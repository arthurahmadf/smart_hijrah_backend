from __future__ import annotations

import csv
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from main.models_tilawah import TilawahAyahPool
from main.utils_tilawah.tajwid_v3.gold_loader import load_default_gold_dataset
from main.utils_tilawah.tajwid_v3.parser_audit import audit_texts


class Command(BaseCommand):
    help = "Audit parser/token stream Tajwid v3 tanpa menulis database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--goldset",
            action="store_true",
            help="Audit seluruh text pada bootstrap goldset.",
        )
        parser.add_argument(
            "--corpus",
            action="store_true",
            help="Audit TilawahAyahPool secara read-only.",
        )
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument(
            "--fail-on-errors",
            action="store_true",
        )
        parser.add_argument(
            "--output-dir",
            default="reports/tilawah/v3_parser",
        )

    def handle(self, *args, **options):
        use_goldset = options["goldset"]
        use_corpus = options["corpus"]
        if not use_goldset and not use_corpus:
            use_goldset = True

        items = []
        if use_goldset:
            dataset = load_default_gold_dataset(Path(settings.BASE_DIR))
            items.extend((f"gold:{case.case_id}", case.text) for case in dataset.cases)

        if use_corpus:
            queryset = TilawahAyahPool.objects.order_by(
                "surah_number",
                "ayah_number",
            ).values_list("surah_number", "ayah_number", "ayah_text")
            if options["limit"] is not None:
                if options["limit"] <= 0:
                    raise CommandError("--limit harus > 0.")
                queryset = queryset[: options["limit"]]
            items.extend((f"ayah:{s}:{a}", text) for s, a, text in queryset)

        report = audit_texts(items)
        output_dir = Path(settings.BASE_DIR) / options["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)

        summary_path = output_dir / "tajwid_v3_parser_audit.json"
        issues_path = output_dir / "tajwid_v3_parser_issues.csv"
        summary_path.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        with issues_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["key", "issue_type", "detail"],
            )
            writer.writeheader()
            for issue in report.issues:
                writer.writerow(
                    {
                        "key": issue.key,
                        "issue_type": issue.issue_type,
                        "detail": issue.detail,
                    }
                )

        self.stdout.write(f"Texts      : {report.total_texts}")
        self.stdout.write(f"Passed     : {report.passed_texts}")
        self.stdout.write(f"Failed     : {report.failed_texts}")
        self.stdout.write(f"Graphemes  : {report.total_graphemes}")
        self.stdout.write(f"Words      : {report.total_words}")
        self.stdout.write("Database write: TIDAK")
        self.stdout.write(f"Summary    : {summary_path}")
        self.stdout.write(f"Issues     : {issues_path}")

        if options["fail_on_errors"] and not report.success:
            raise CommandError("Parser audit menemukan error.")
