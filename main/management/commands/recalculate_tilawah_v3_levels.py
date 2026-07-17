from __future__ import annotations

import csv
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Prefetch
from django.utils import timezone

from main.models_tilawah import (
    TilawahAyahPool,
    TilawahAyahTajwidAnnotation,
    TilawahAyahTajwidAnnotationSet,
    TilawahLevelSource,
)
from main.utils_tilawah.tajwid_v3.difficulty import (
    DIFFICULTY_VERSION,
    calculate_raw_difficulty,
    level_from_percentile,
    percentile_rank,
)
from main.utils_tilawah.tajwid_v3.engine import ENGINE_VERSION


class Command(BaseCommand):
    help = (
        "Hitung kandidat level dari annotation aktif. Default report-only; "
        "gunakan --commit setelah distribusi diperiksa."
    )

    def add_arguments(self, parser):
        parser.add_argument("--commit", action="store_true")
        parser.add_argument("--intermediate-from", type=float, default=55.0)
        parser.add_argument("--expert-from", type=float, default=88.0)
        parser.add_argument(
            "--output-dir", default="reports/tilawah/v3_level_candidates"
        )

    def handle(self, *args, **options):
        intermediate_from = options["intermediate_from"]
        expert_from = options["expert_from"]
        if not 0 < intermediate_from < expert_from < 100:
            raise CommandError(
                "Threshold harus 0 < intermediate < expert < 100."
            )

        annotations = TilawahAyahTajwidAnnotation.objects.select_related("rule")
        active_sets = TilawahAyahTajwidAnnotationSet.objects.filter(
            is_active=True,
            reading_mode="ayah",
        ).prefetch_related(Prefetch("annotations", queryset=annotations))
        ayahs = list(
            TilawahAyahPool.objects.prefetch_related(
                Prefetch(
                    "tajwid_annotation_sets",
                    queryset=active_sets,
                    to_attr="_level_active_sets",
                )
            ).order_by("surah_number", "ayah_number")
        )
        if not ayahs:
            raise CommandError("TilawahAyahPool kosong.")

        calculated = []
        raw_values = []
        for ayah in ayahs:
            annotation_set = ayah._level_active_sets[0] if ayah._level_active_sets else None
            if annotation_set is None:
                continue
            metrics = calculate_raw_difficulty(
                ayah.ayah_text,
                annotation_set.annotations.all(),
            )
            raw_values.append(metrics.raw_score)
            calculated.append((ayah, annotation_set, metrics))

        if not calculated:
            raise CommandError("Belum ada annotation set aktif mode ayah.")
        sorted_values = sorted(raw_values)
        rows = []
        updates = []
        distribution = {"basic": 0, "intermediate": 0, "expert": 0}

        for ayah, annotation_set, metrics in calculated:
            percentile = percentile_rank(sorted_values, metrics.raw_score)
            level = level_from_percentile(
                percentile,
                intermediate_from=intermediate_from,
                expert_from=expert_from,
            )
            distribution[level] += 1
            metric_payload = metrics.to_dict()
            metric_payload.update({
                "percentile": round(percentile, 4),
                "intermediate_from": intermediate_from,
                "expert_from": expert_from,
                "annotation_set_id": annotation_set.pk,
                "annotation_engine_version": annotation_set.engine_version,
            })
            rows.append({
                "ayah_id": ayah.pk,
                "verse_key": f"{ayah.surah_number}:{ayah.ayah_number}",
                "old_level": ayah.level,
                "candidate_level": level,
                "raw_score": round(metrics.raw_score, 6),
                "percentile": round(percentile, 4),
                "annotation_count": metrics.annotation_count,
                "unique_rule_count": metrics.unique_rule_count,
                "overlap_count": metrics.overlap_count,
            })
            if options["commit"]:
                ayah.level = level
                ayah.level_source = TilawahLevelSource.ENGINE
                ayah.level_score = round(percentile, 2)
                ayah.level_engine_version = ENGINE_VERSION
                ayah.level_metrics = metric_payload
                ayah.level_is_verified = False
                ayah.level_updated_at = timezone.now()
                updates.append(ayah)

        if options["commit"]:
            TilawahAyahPool.objects.bulk_update(
                updates,
                [
                    "level",
                    "level_source",
                    "level_score",
                    "level_engine_version",
                    "level_metrics",
                    "level_is_verified",
                    "level_updated_at",
                ],
                batch_size=500,
            )

        output_dir = Path(options["output_dir"])
        if not output_dir.is_absolute():
            output_dir = Path(settings.BASE_DIR) / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "generated_at": timezone.now().isoformat(),
            "difficulty_version": DIFFICULTY_VERSION,
            "engine_version": ENGINE_VERSION,
            "commit": bool(options["commit"]),
            "thresholds": {
                "intermediate_from": intermediate_from,
                "expert_from": expert_from,
            },
            "distribution": distribution,
            "evaluated_ayah": len(rows),
            "missing_active_set": len(ayahs) - len(rows),
        }
        (output_dir / "tajwid_v3_level_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        with (output_dir / "tajwid_v3_level_candidates.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        self.stdout.write(self.style.SUCCESS("Kandidat level selesai dihitung."))
        self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2))
        if not options["commit"]:
            self.stdout.write(
                self.style.WARNING(
                    "Database belum diubah. Periksa distribusi sebelum --commit."
                )
            )
