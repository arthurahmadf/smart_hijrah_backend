from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from main.models_tilawah import TilawahAyahPool
from main.utils_tilawah.tajwid_annotation_engine import (
    ANNOTATION_ENGINE_VERSION,
    analyze_tajwid_annotations,
    validate_render_segments,
)
from main.utils_tilawah.tajwid_rule_catalog import TAJWID_RULE_CATALOG


class Command(BaseCommand):
    help = (
        "Audit Expected Tajwid Annotation Engine secara read-only. "
        "Command ini tidak membuat annotation set dan tidak mengubah level ayat."
    )

    def add_arguments(self, parser):
        scope = parser.add_mutually_exclusive_group(required=True)
        scope.add_argument(
            "--all",
            action="store_true",
            help="Audit seluruh ayat pada TilawahAyahPool.",
        )
        scope.add_argument(
            "--surah",
            type=int,
            help="Audit satu surah. Gunakan --ayah untuk mempersempit.",
        )
        parser.add_argument(
            "--ayah",
            type=int,
            help="Nomor ayat; hanya valid bersama --surah.",
        )
        parser.add_argument(
            "--reading-mode",
            choices=("ayah", "wasl", "waqf"),
            default="ayah",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Batasi jumlah ayat untuk smoke test.",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=250,
            help="Ukuran iterator queryset. Default 250.",
        )
        parser.add_argument(
            "--low-confidence",
            type=float,
            default=0.75,
            help="Batas locator confidence yang ditandai rendah.",
        )
        parser.add_argument(
            "--max-annotations",
            type=int,
            default=40,
            help="Jumlah anotasi per ayat yang dianggap abnormal.",
        )
        parser.add_argument(
            "--output-dir",
            default="reports/tilawah",
            help="Folder report; relatif terhadap BASE_DIR atau path absolut.",
        )
        parser.add_argument(
            "--fail-on-errors",
            action="store_true",
            help="Return error bila ditemukan structural error/exception.",
        )

    def handle(self, *args: Any, **options: Any):
        self._validate_options(options)

        reading_mode: str = options["reading_mode"]
        low_confidence_threshold: float = options["low_confidence"]
        max_annotations: int = options["max_annotations"]
        chunk_size: int = options["chunk_size"]

        queryset = TilawahAyahPool.objects.only(
            "id",
            "surah_number",
            "ayah_number",
            "ayah_text",
        ).order_by("surah_number", "ayah_number")

        if options["surah"] is not None:
            queryset = queryset.filter(surah_number=options["surah"])
            if options["ayah"] is not None:
                queryset = queryset.filter(ayah_number=options["ayah"])

        if options["limit"] is not None:
            queryset = queryset[: options["limit"]]

        selected_count = queryset.count()
        if selected_count == 0:
            raise CommandError("Tidak ada ayat yang cocok dengan filter audit.")

        output_dir = self._resolve_output_dir(options["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        counters: Counter[str] = Counter()
        issue_type_counts: Counter[str] = Counter()
        issue_severity_counts: Counter[str] = Counter()
        rule_counts: Counter[str] = Counter()
        rule_ayahs: dict[str, set[int]] = defaultdict(set)
        rule_low_confidence: Counter[str] = Counter()
        locator_method_counts: dict[str, Counter[str]] = defaultdict(Counter)

        issue_rows: list[dict[str, Any]] = []
        ayah_rows: list[dict[str, Any]] = []

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Audit Tajwid Engine {ANNOTATION_ENGINE_VERSION}"
            )
        )
        self.stdout.write(f"Ayat dipilih : {selected_count}")
        self.stdout.write(f"Reading mode : {reading_mode}")
        self.stdout.write("Database write: TIDAK")

        for position, ayah in enumerate(
            queryset.iterator(chunk_size=chunk_size),
            start=1,
        ):
            counters["total_ayah"] += 1
            ayah_key = f"{ayah.surah_number}:{ayah.ayah_number}"
            annotations: list[dict[str, Any]] = []
            issues: list[dict[str, Any]] = []
            safe = False
            exception_message = ""

            try:
                result = analyze_tajwid_annotations(
                    ayah.ayah_text,
                    user_level=None,
                    reading_mode=reading_mode,
                    strict=False,
                )
                annotations = result["annotations"]
                issues = result["issues"]
                safe = bool(result["is_safe_to_persist"])
                validate_render_segments(
                    ayah.ayah_text,
                    result["render_segments"],
                )
                counters["render_reconstruction_ok"] += 1
            except Exception as exc:  # audit harus lanjut ke ayat berikutnya
                counters["exceptions"] += 1
                exception_message = f"{type(exc).__name__}: {exc}"
                issues = [
                    {
                        "type": "audit_exception",
                        "severity": "error",
                        "detail": exception_message,
                    }
                ]

            if not annotations:
                counters["ayah_without_annotations"] += 1

            if len(annotations) > max_annotations:
                counters["abnormal_annotation_count"] += 1
                issues.append(
                    {
                        "type": "abnormal_annotation_count",
                        "severity": "warning",
                        "detail": (
                            f"annotation_count={len(annotations)} melebihi "
                            f"threshold={max_annotations}"
                        ),
                    }
                )

            ayah_low_confidence = 0
            emitted_codes: list[str] = []
            for annotation in annotations:
                code = str(annotation["rule_code"])
                emitted_codes.append(code)
                rule_counts[code] += 1
                rule_ayahs[code].add(ayah.id)
                locator_method_counts[code][
                    str(annotation.get("locator_method", ""))
                ] += 1

                confidence = float(annotation.get("locator_confidence", 0.0))
                if confidence < low_confidence_threshold:
                    counters["low_confidence_annotations"] += 1
                    rule_low_confidence[code] += 1
                    ayah_low_confidence += 1

                if code not in TAJWID_RULE_CATALOG:
                    counters["unregistered_rule_annotations"] += 1
                    issues.append(
                        {
                            "type": "unregistered_rule_annotation",
                            "severity": "error",
                            "rule_code": code,
                        }
                    )

            if ayah_low_confidence:
                counters["ayah_with_low_confidence"] += 1

            if any(issue.get("severity") == "error" for issue in issues):
                safe = False

            if safe:
                counters["safe_ayah"] += 1
            else:
                counters["unsafe_ayah"] += 1

            for issue in issues:
                issue_type = str(issue.get("type", "unknown"))
                severity = str(issue.get("severity", "unknown"))
                issue_type_counts[issue_type] += 1
                issue_severity_counts[severity] += 1
                counters["total_issues"] += 1
                if severity == "error":
                    counters["structural_errors"] += 1
                elif severity == "warning":
                    counters["warnings"] += 1

                issue_rows.append(
                    {
                        "ayah_id": ayah.id,
                        "surah_number": ayah.surah_number,
                        "ayah_number": ayah.ayah_number,
                        "ayah_key": ayah_key,
                        "issue_type": issue_type,
                        "severity": severity,
                        "rule_code": issue.get("rule_code", ""),
                        "word_index": issue.get("word_index", ""),
                        "word": issue.get("word", ""),
                        "reason": issue.get("reason", ""),
                        "detail": issue.get("detail", ""),
                        "raw_issue": json.dumps(
                            issue,
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    }
                )

            counters["total_annotations"] += len(annotations)
            ayah_rows.append(
                {
                    "ayah_id": ayah.id,
                    "surah_number": ayah.surah_number,
                    "ayah_number": ayah.ayah_number,
                    "ayah_key": ayah_key,
                    "safe_to_persist": safe,
                    "annotation_count": len(annotations),
                    "issue_count": len(issues),
                    "low_confidence_count": ayah_low_confidence,
                    "emitted_rule_codes": "|".join(sorted(set(emitted_codes))),
                    "exception": exception_message,
                }
            )

            if position % 250 == 0 or position == selected_count:
                self.stdout.write(
                    f"Processed {position}/{selected_count} | "
                    f"safe={counters['safe_ayah']} | "
                    f"unsafe={counters['unsafe_ayah']} | "
                    f"errors={counters['structural_errors']}"
                )

        missing_catalog_rules = sorted(set(TAJWID_RULE_CATALOG) - set(rule_counts))
        generated_at = timezone.now().isoformat()

        summary = {
            "generated_at": generated_at,
            "engine_version": ANNOTATION_ENGINE_VERSION,
            "reading_mode": reading_mode,
            "scope": {
                "all": bool(options["all"]),
                "surah": options["surah"],
                "ayah": options["ayah"],
                "limit": options["limit"],
            },
            "thresholds": {
                "low_confidence": low_confidence_threshold,
                "max_annotations": max_annotations,
            },
            "database_write_performed": False,
            "counters": dict(sorted(counters.items())),
            "issue_type_counts": dict(sorted(issue_type_counts.items())),
            "issue_severity_counts": dict(
                sorted(issue_severity_counts.items())
            ),
            "catalog_rule_count": len(TAJWID_RULE_CATALOG),
            "emitted_rule_count": len(rule_counts),
            "missing_catalog_rules_in_scope": missing_catalog_rules,
        }

        summary_path = output_dir / "tajwid_engine_audit.json"
        issues_path = output_dir / "tajwid_engine_issues.csv"
        distribution_path = output_dir / "tajwid_rule_distribution.csv"
        ayahs_path = output_dir / "tajwid_ayah_audit.csv"

        self._write_json(summary_path, summary)
        self._write_csv(
            issues_path,
            issue_rows,
            fieldnames=[
                "ayah_id",
                "surah_number",
                "ayah_number",
                "ayah_key",
                "issue_type",
                "severity",
                "rule_code",
                "word_index",
                "word",
                "reason",
                "detail",
                "raw_issue",
            ],
        )
        self._write_csv(
            ayahs_path,
            ayah_rows,
            fieldnames=[
                "ayah_id",
                "surah_number",
                "ayah_number",
                "ayah_key",
                "safe_to_persist",
                "annotation_count",
                "issue_count",
                "low_confidence_count",
                "emitted_rule_codes",
                "exception",
            ],
        )

        distribution_rows = []
        for code in sorted(TAJWID_RULE_CATALOG):
            definition = TAJWID_RULE_CATALOG[code]
            distribution_rows.append(
                {
                    "rule_code": code,
                    "rule_name": definition.name,
                    "display_group": definition.display_group.value,
                    "annotation_count": rule_counts[code],
                    "ayah_count": len(rule_ayahs[code]),
                    "low_confidence_count": rule_low_confidence[code],
                    "locator_methods": json.dumps(
                        dict(sorted(locator_method_counts[code].items())),
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                }
            )
        self._write_csv(
            distribution_path,
            distribution_rows,
            fieldnames=[
                "rule_code",
                "rule_name",
                "display_group",
                "annotation_count",
                "ayah_count",
                "low_confidence_count",
                "locator_methods",
            ],
        )

        self.stdout.write(self.style.SUCCESS("Audit selesai."))
        self.stdout.write(f"Summary      : {summary_path}")
        self.stdout.write(f"Issues       : {issues_path}")
        self.stdout.write(f"Per ayat     : {ayahs_path}")
        self.stdout.write(f"Distribution : {distribution_path}")
        self.stdout.write(
            "Tidak ada TilawahAyahTajwidAnnotationSet atau annotation "
            "yang dibuat."
        )

        if options["fail_on_errors"] and counters["structural_errors"] > 0:
            raise CommandError(
                "Audit menemukan structural error. Periksa report sebelum seed."
            )

    @staticmethod
    def _validate_options(options: dict[str, Any]) -> None:
        surah = options["surah"]
        ayah = options["ayah"]
        if ayah is not None and surah is None:
            raise CommandError("--ayah hanya boleh digunakan bersama --surah.")
        if surah is not None and not (1 <= surah <= 114):
            raise CommandError("--surah harus berada pada rentang 1-114.")
        if ayah is not None and ayah < 1:
            raise CommandError("--ayah minimal 1.")
        if options["limit"] is not None and options["limit"] < 1:
            raise CommandError("--limit minimal 1.")
        if options["chunk_size"] < 1:
            raise CommandError("--chunk-size minimal 1.")
        if not (0 <= options["low_confidence"] <= 1):
            raise CommandError("--low-confidence harus berada pada rentang 0-1.")
        if options["max_annotations"] < 1:
            raise CommandError("--max-annotations minimal 1.")

    @staticmethod
    def _resolve_output_dir(raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = Path(settings.BASE_DIR) / path
        return path.resolve()

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(
                payload,
                file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            file.write("\n")

    @staticmethod
    def _write_csv(
        path: Path,
        rows: list[dict[str, Any]],
        *,
        fieldnames: list[str],
    ) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(rows)
