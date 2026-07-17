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
from main.utils_tilawah.tajwid_v3.detectors.qalqalah import (
    QalqalahDetector,
    SUPPORTED_RULE_CODES as QALQALAH_RULE_CODES,
)
from main.utils_tilawah.tajwid_v3.engine import ENGINE_VERSION, analyze_tajwid_v3
from main.utils_tilawah.tajwid_v3.rule_specs import get_rule_spec


AUDITED_RULE_CODES = QALQALAH_RULE_CODES


class Command(BaseCommand):
    help = (
        "Audit corpus read-only untuk detector Qalqalah v3. Tidak membuat annotation set atau mengubah level ayat."
    )

    def add_arguments(self, parser):
        scope = parser.add_mutually_exclusive_group(required=True)
        scope.add_argument("--all", action="store_true")
        scope.add_argument("--surah", type=int)
        parser.add_argument("--ayah", type=int)
        parser.add_argument(
            "--reading-mode",
            choices=("ayah_stop", "wasl", "waqf"),
            default="ayah_stop",
        )
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--chunk-size", type=int, default=250)
        parser.add_argument(
            "--output-dir",
            default="reports/tilawah/v3_qalqalah_corpus",
        )
        parser.add_argument("--fail-on-errors", action="store_true")

    def handle(self, *args: Any, **options: Any):
        if options["ayah"] is not None and options["surah"] is None:
            raise CommandError("--ayah hanya dapat digunakan bersama --surah.")
        if options["limit"] is not None and options["limit"] < 1:
            raise CommandError("--limit harus lebih besar dari 0.")
        if options["chunk_size"] < 1:
            raise CommandError("--chunk-size harus lebih besar dari 0.")

        queryset = TilawahAyahPool.objects.only(
            "id", "surah_number", "ayah_number", "ayah_text"
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

        output_dir = Path(options["output_dir"])
        if not output_dir.is_absolute():
            output_dir = Path(settings.BASE_DIR) / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        counters: Counter[str] = Counter()
        issue_counts: Counter[str] = Counter()
        rule_counts: Counter[str] = Counter()
        rule_ayahs: dict[str, set[int]] = defaultdict(set)
        issue_rows: list[dict[str, Any]] = []
        ayah_rows: list[dict[str, Any]] = []

        self.stdout.write(f"Tajwid v3 corpus audit — Engine {ENGINE_VERSION}")
        self.stdout.write(f"Ayat dipilih : {selected_count}")
        self.stdout.write(f"Reading mode : {options['reading_mode']}")
        self.stdout.write("Database write: TIDAK")

        for position, ayah in enumerate(
            queryset.iterator(chunk_size=options["chunk_size"]),
            start=1,
        ):
            counters["total_ayah"] += 1
            relevant = []
            issues = []
            exception_message = ""
            try:
                result = analyze_tajwid_v3(
                    ayah.ayah_text,
                    reading_mode=options["reading_mode"],
                    detectors=(QalqalahDetector(),),
                )
                relevant = [
                    item for item in result.annotations
                    if item.rule_code in AUDITED_RULE_CODES
                ]
                issues = list(result.issues)
            except Exception as exc:  # audit harus tetap melanjutkan corpus
                counters["exceptions"] += 1
                exception_message = f"{type(exc).__name__}: {exc}"
                issues = []

            if relevant:
                counters["ayah_with_annotations"] += 1
            else:
                counters["ayah_without_annotations"] += 1

            emitted_codes = []
            for annotation in relevant:
                emitted_codes.append(annotation.rule_code)
                rule_counts[annotation.rule_code] += 1
                rule_ayahs[annotation.rule_code].add(ayah.id)
                counters["total_annotations"] += 1

            if exception_message:
                issue_rows.append(
                    {
                        "ayah_id": ayah.id,
                        "surah_number": ayah.surah_number,
                        "ayah_number": ayah.ayah_number,
                        "issue_type": "audit_exception",
                        "severity": "error",
                        "detail": exception_message,
                        "evidence": "",
                    }
                )
                counters["errors"] += 1
                issue_counts["audit_exception"] += 1

            for issue in issues:
                issue_counts[issue.issue_type] += 1
                counters[f"{issue.severity}s"] += 1
                issue_rows.append(
                    {
                        "ayah_id": ayah.id,
                        "surah_number": ayah.surah_number,
                        "ayah_number": ayah.ayah_number,
                        "issue_type": issue.issue_type,
                        "severity": issue.severity,
                        "detail": issue.detail,
                        "evidence": json.dumps(
                            issue.evidence,
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    }
                )

            ayah_rows.append(
                {
                    "ayah_id": ayah.id,
                    "surah_number": ayah.surah_number,
                    "ayah_number": ayah.ayah_number,
                    "annotation_count": len(relevant),
                    "emitted_rule_codes": "|".join(sorted(set(emitted_codes))),
                    "issue_count": len(issues) + (1 if exception_message else 0),
                    "exception": exception_message,
                }
            )

            if position % 250 == 0 or position == selected_count:
                self.stdout.write(
                    f"Processed {position}/{selected_count} | "
                    f"annotations={counters['total_annotations']} | "
                    f"errors={counters['errors']}"
                )

        summary = {
            "generated_at": timezone.now().isoformat(),
            "engine_version": ENGINE_VERSION,
            "reading_mode": options["reading_mode"],
            "database_write_performed": False,
            "scope": {
                "all": bool(options["all"]),
                "surah": options["surah"],
                "ayah": options["ayah"],
                "limit": options["limit"],
            },
            "audited_rule_codes": sorted(AUDITED_RULE_CODES),
            "counters": dict(sorted(counters.items())),
            "issue_type_counts": dict(sorted(issue_counts.items())),
        }

        summary_path = output_dir / "tajwid_v3_qalqalah_corpus_summary.json"
        issue_path = output_dir / "tajwid_v3_qalqalah_corpus_issues.csv"
        ayah_path = output_dir / "tajwid_v3_qalqalah_corpus_ayahs.csv"
        distribution_path = output_dir / "tajwid_v3_qalqalah_distribution.csv"

        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._write_csv(
            issue_path,
            issue_rows,
            [
                "ayah_id", "surah_number", "ayah_number", "issue_type",
                "severity", "detail", "evidence",
            ],
        )
        self._write_csv(
            ayah_path,
            ayah_rows,
            [
                "ayah_id", "surah_number", "ayah_number", "annotation_count",
                "emitted_rule_codes", "issue_count", "exception",
            ],
        )
        distribution_rows = []
        for code in sorted(AUDITED_RULE_CODES):
            spec = get_rule_spec(code)
            distribution_rows.append(
                {
                    "rule_code": code,
                    "rule_name": spec.name,
                    "annotation_count": rule_counts[code],
                    "ayah_count": len(rule_ayahs[code]),
                }
            )
        self._write_csv(
            distribution_path,
            distribution_rows,
            ["rule_code", "rule_name", "annotation_count", "ayah_count"],
        )

        self.stdout.write("Audit selesai.")
        self.stdout.write(f"Summary     : {summary_path}")
        self.stdout.write(f"Issues      : {issue_path}")
        self.stdout.write(f"Per ayat    : {ayah_path}")
        self.stdout.write(f"Distribution: {distribution_path}")
        self.stdout.write("Tidak ada annotation set atau annotation yang dibuat.")

        if options["fail_on_errors"] and (
            counters["errors"] > 0 or counters["exceptions"] > 0
        ):
            raise CommandError("Audit menemukan structural error/exception.")

    @staticmethod
    def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
