from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from main.models_tilawah import TilawahAyahPool
from main.utils_tilawah.tajwid_v3.engine import ENGINE_VERSION
from main.utils_tilawah.tajwid_v3.persistence import (
    boundary_destination_for_verse,
    destination_text_map,
    load_rule_map,
    persist_prepared_ayah_mode,
    prepare_ayah_mode,
    supported_db_modes,
    sync_v3_rule_catalog,
)


class Command(BaseCommand):
    help = (
        "Generate candidate annotation Tajwid v3. Default dry-run; gunakan "
        "--commit untuk menulis DB dan --publish-beta agar aktif di frontend."
    )

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true")
        parser.add_argument("--surah", type=int)
        parser.add_argument("--ayah", type=int)
        parser.add_argument("--limit", type=int)
        parser.add_argument(
            "--modes",
            choices=("ayah", "wasl", "waqf", "both"),
            default="both",
        )
        parser.add_argument("--chunk-size", type=int, default=100)
        parser.add_argument("--commit", action="store_true")
        parser.add_argument("--publish-beta", action="store_true")
        parser.add_argument("--fail-on-errors", action="store_true")
        parser.add_argument(
            "--output-dir",
            default="reports/tilawah/v3_seed",
        )

    def handle(self, *args, **options):
        if not options["all"] and options["surah"] is None:
            raise CommandError("Gunakan --all atau --surah.")
        if options["ayah"] is not None and options["surah"] is None:
            raise CommandError("--ayah harus digunakan bersama --surah.")
        if options["publish_beta"] and not options["commit"]:
            raise CommandError("--publish-beta memerlukan --commit.")
        if options["chunk_size"] < 1:
            raise CommandError("--chunk-size minimal 1.")

        modes = supported_db_modes(options["modes"])
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

        selected = queryset.count()
        if selected == 0:
            raise CommandError("Tidak ada ayat yang cocok.")

        rule_map = None
        if options["commit"]:
            sync_v3_rule_catalog(deactivate_unknown=True)
            rule_map = load_rule_map()

        destination_map = destination_text_map()
        counters: Counter[str] = Counter()
        rows: list[dict] = []

        self.stdout.write(
            f"Tajwid v3 seed — engine={ENGINE_VERSION} ayat={selected} "
            f"modes={','.join(modes)}"
        )
        self.stdout.write(
            "Database write: " + ("YA" if options["commit"] else "TIDAK (dry-run)")
        )
        self.stdout.write(
            "Frontend beta : " + ("AKTIF" if options["publish_beta"] else "TIDAK")
        )

        for position, ayah in enumerate(
            queryset.iterator(chunk_size=options["chunk_size"]),
            start=1,
        ):
            verse_key = f"{ayah.surah_number}:{ayah.ayah_number}"
            counters["ayah_processed"] += 1
            for mode in modes:
                try:
                    prepared = prepare_ayah_mode(
                        ayah,
                        db_reading_mode=mode,
                        destination_text=destination_map.get(
                            boundary_destination_for_verse(verse_key)
                        ),
                        rule_map=rule_map,
                    )
                    counters["mode_processed"] += 1
                    counters["annotations_generated"] += len(prepared.annotations)
                    error_count = sum(
                        1 for issue in prepared.issues
                        if issue.get("severity") == "error"
                    )
                    warning_count = sum(
                        1 for issue in prepared.issues
                        if issue.get("severity") == "warning"
                    )
                    counters["engine_errors"] += error_count
                    counters["warnings"] += warning_count

                    action = "dry_run_safe" if prepared.safe_to_persist else "dry_run_failed"
                    set_id = None
                    published = False
                    protected_set_id = None
                    if options["commit"]:
                        outcome = persist_prepared_ayah_mode(
                            prepared,
                            publish_beta=options["publish_beta"],
                            rule_map=rule_map,
                        )
                        action = outcome.action
                        set_id = outcome.annotation_set_id
                        published = outcome.published
                        protected_set_id = outcome.protected_active_set_id
                        counters[action] += 1
                        if published:
                            counters["published_sets"] += 1
                        if protected_set_id:
                            counters["protected_sets"] += 1
                    else:
                        counters[action] += 1

                    rows.append({
                        "ayah_id": ayah.pk,
                        "verse_key": verse_key,
                        "mode": mode,
                        "annotation_set_id": set_id or "",
                        "annotation_count": len(prepared.annotations),
                        "safe_to_persist": prepared.safe_to_persist,
                        "error_count": error_count,
                        "warning_count": warning_count,
                        "action": action,
                        "published": published,
                        "protected_active_set_id": protected_set_id or "",
                    })
                except Exception as exc:
                    counters["exceptions"] += 1
                    rows.append({
                        "ayah_id": ayah.pk,
                        "verse_key": verse_key,
                        "mode": mode,
                        "annotation_set_id": "",
                        "annotation_count": 0,
                        "safe_to_persist": False,
                        "error_count": 1,
                        "warning_count": 0,
                        "action": "exception",
                        "published": False,
                        "protected_active_set_id": "",
                        "exception": f"{type(exc).__name__}: {exc}",
                    })

            if position % 100 == 0 or position == selected:
                self.stdout.write(
                    f"Processed {position}/{selected} | "
                    f"annotations={counters['annotations_generated']} | "
                    f"errors={counters['engine_errors'] + counters['exceptions']}"
                )

        output_dir = self._write_report(options["output_dir"], options, counters, rows)
        self.stdout.write(self.style.SUCCESS("Seed Tajwid v3 selesai."))
        self.stdout.write(f"Report: {output_dir}")

        if options["fail_on_errors"] and (
            counters["engine_errors"] > 0 or counters["exceptions"] > 0
        ):
            raise CommandError("Seed menemukan error. Periksa report.")

    def _write_report(self, configured, options, counters, rows):
        output_dir = Path(configured)
        if not output_dir.is_absolute():
            output_dir = Path(settings.BASE_DIR) / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        summary = {
            "generated_at": timezone.now().isoformat(),
            "engine_version": ENGINE_VERSION,
            "commit": bool(options["commit"]),
            "publish_beta": bool(options["publish_beta"]),
            "modes": list(supported_db_modes(options["modes"])),
            "counters": dict(sorted(counters.items())),
        }
        (output_dir / "tajwid_v3_seed_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        fieldnames = sorted({key for row in rows for key in row})
        with (output_dir / "tajwid_v3_seed_rows.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return output_dir
