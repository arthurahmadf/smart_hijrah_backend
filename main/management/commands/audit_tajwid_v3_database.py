from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Prefetch
from django.utils import timezone

from main.models_tilawah import (
    TajwidAnnotationSetStatus,
    TilawahAyahPool,
    TilawahAyahTajwidAnnotation,
    TilawahAyahTajwidAnnotationSet,
    TilawahTajwidRule,
)
from main.utils_tilawah.tajwid_v3.db_renderer import (
    _annotation_from_model,
    render_database_annotations,
)
from main.utils_tilawah.tajwid_v3.rule_specs import RULE_SPECS


class Command(BaseCommand):
    help = "Audit integritas annotation Tajwid v3 yang sudah disimpan di database."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true")
        parser.add_argument("--surah", type=int)
        parser.add_argument("--ayah", type=int)
        parser.add_argument("--limit", type=int)
        parser.add_argument(
            "--modes", choices=("ayah", "wasl", "waqf", "both"), default="both"
        )
        parser.add_argument("--require-complete", action="store_true")
        parser.add_argument("--fail-on-errors", action="store_true")
        parser.add_argument(
            "--output-dir", default="reports/tilawah/v3_database"
        )

    def handle(self, *args, **options):
        if not options["all"] and options["surah"] is None:
            raise CommandError("Gunakan --all atau --surah.")
        if options["ayah"] is not None and options["surah"] is None:
            raise CommandError("--ayah harus digunakan bersama --surah.")

        modes = (
            ("ayah", "wasl") if options["modes"] == "both"
            else (options["modes"],)
        )
        annotation_qs = TilawahAyahTajwidAnnotation.objects.select_related(
            "rule"
        ).order_by("start_grapheme", "end_grapheme", "rule__priority")
        set_qs = TilawahAyahTajwidAnnotationSet.objects.filter(
            is_active=True,
            reading_mode__in=modes,
        ).prefetch_related(Prefetch("annotations", queryset=annotation_qs))

        queryset = TilawahAyahPool.objects.only(
            "id", "surah_number", "ayah_number", "ayah_text"
        ).prefetch_related(
            Prefetch(
                "tajwid_annotation_sets",
                queryset=set_qs,
                to_attr="_audit_active_sets",
            )
        ).order_by("surah_number", "ayah_number")
        if options["surah"] is not None:
            queryset = queryset.filter(surah_number=options["surah"])
        if options["ayah"] is not None:
            queryset = queryset.filter(ayah_number=options["ayah"])
        if options["limit"] is not None:
            queryset = queryset[: options["limit"]]

        selected = queryset.count()
        if selected == 0:
            raise CommandError("Tidak ada ayat yang cocok.")

        counters: Counter[str] = Counter()
        issue_rows: list[dict] = []
        ayah_rows: list[dict] = []

        active_catalog_count = TilawahTajwidRule.objects.filter(
            code__in=RULE_SPECS.keys(), is_active=True
        ).count()
        if active_catalog_count != len(RULE_SPECS):
            counters["errors"] += 1
            issue_rows.append({
                "verse_key": "",
                "mode": "global",
                "issue_type": "rule_catalog_not_44_active",
                "detail": f"active={active_catalog_count} expected={len(RULE_SPECS)}",
            })

        for position, ayah in enumerate(queryset.iterator(chunk_size=100), start=1):
            counters["ayah_processed"] += 1
            by_mode = {item.reading_mode: item for item in ayah._audit_active_sets}
            verse_key = f"{ayah.surah_number}:{ayah.ayah_number}"

            for mode in modes:
                annotation_set = by_mode.get(mode)
                if annotation_set is None:
                    counters["missing_active_sets"] += 1
                    if options["require_complete"]:
                        counters["errors"] += 1
                        issue_rows.append({
                            "verse_key": verse_key,
                            "mode": mode,
                            "issue_type": "missing_active_set",
                            "detail": "",
                        })
                    continue

                counters["active_sets"] += 1
                annotations = list(annotation_set.annotations.all())
                counters["annotations"] += len(annotations)
                if annotation_set.status != TajwidAnnotationSetStatus.PUBLISHED:
                    counters["errors"] += 1
                    issue_rows.append({
                        "verse_key": verse_key,
                        "mode": mode,
                        "issue_type": "active_set_not_published",
                        "detail": annotation_set.status,
                    })
                if annotation_set.is_stale:
                    counters["errors"] += 1
                    issue_rows.append({
                        "verse_key": verse_key,
                        "mode": mode,
                        "issue_type": "stale_source_text_hash",
                        "detail": "",
                    })
                if annotation_set.annotation_count != len(annotations):
                    counters["errors"] += 1
                    issue_rows.append({
                        "verse_key": verse_key,
                        "mode": mode,
                        "issue_type": "annotation_count_mismatch",
                        "detail": (
                            f"stored={annotation_set.annotation_count} "
                            f"actual={len(annotations)}"
                        ),
                    })

                try:
                    rules = render_database_annotations(
                        ayah.ayah_text,
                        (_annotation_from_model(item) for item in annotations),
                    )
                    if "".join(item["arabic"] for item in rules) != ayah.ayah_text:
                        raise ValueError("reconstruction_mismatch")
                    counters["rendered_sets"] += 1
                except Exception as exc:
                    counters["errors"] += 1
                    issue_rows.append({
                        "verse_key": verse_key,
                        "mode": mode,
                        "issue_type": "database_render_failure",
                        "detail": f"{type(exc).__name__}: {exc}",
                    })

                verified_count = sum(1 for item in annotations if item.is_verified)
                if annotation_set.has_expert_review:
                    counters["expert_protected_sets"] += 1
                if verified_count:
                    counters["verified_annotations"] += verified_count

                ayah_rows.append({
                    "ayah_id": ayah.pk,
                    "verse_key": verse_key,
                    "mode": mode,
                    "annotation_set_id": annotation_set.pk,
                    "engine_version": annotation_set.engine_version,
                    "annotation_count": len(annotations),
                    "verified_annotation_count": verified_count,
                    "verification_state": annotation_set.verification_state,
                    "issue_count": len(annotation_set.issues or []),
                })

            if position % 250 == 0 or position == selected:
                self.stdout.write(
                    f"Processed {position}/{selected} | "
                    f"sets={counters['active_sets']} | "
                    f"annotations={counters['annotations']} | "
                    f"errors={counters['errors']}"
                )

        output_dir = self._write_report(options, counters, issue_rows, ayah_rows)
        self.stdout.write(self.style.SUCCESS("Audit database Tajwid v3 selesai."))
        self.stdout.write(f"Report: {output_dir}")
        if options["fail_on_errors"] and counters["errors"]:
            raise CommandError("Audit database menemukan error.")

    def _write_report(self, options, counters, issues, ayahs):
        output_dir = Path(options["output_dir"])
        if not output_dir.is_absolute():
            output_dir = Path(settings.BASE_DIR) / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "generated_at": timezone.now().isoformat(),
            "modes": options["modes"],
            "require_complete": bool(options["require_complete"]),
            "counters": dict(sorted(counters.items())),
        }
        (output_dir / "tajwid_v3_database_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._write_csv(output_dir / "tajwid_v3_database_issues.csv", issues)
        self._write_csv(output_dir / "tajwid_v3_database_ayahs.csv", ayahs)
        return output_dir

    @staticmethod
    def _write_csv(path, rows):
        fieldnames = sorted({key for row in rows for key in row}) or ["empty"]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            if rows:
                writer.writerows(rows)
