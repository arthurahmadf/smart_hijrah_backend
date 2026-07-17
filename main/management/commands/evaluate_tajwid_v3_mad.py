from __future__ import annotations

import csv
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from main.utils_tilawah.tajwid_v3.detectors.mad import SUPPORTED_RULE_CODES
from main.utils_tilawah.tajwid_v3.evaluation import (
    evaluate_gold_cases,
    relevant_gold_cases,
)
from main.utils_tilawah.tajwid_v3.gold_loader import load_default_gold_dataset


class Command(BaseCommand):
    help = "Evaluasi exact-span Mad Detector v3 terhadap goldset Stage 5G."

    def add_arguments(self, parser):
        parser.add_argument("--fail-on-errors", action="store_true")
        parser.add_argument(
            "--output-dir",
            default="reports/tilawah/v3_mad",
        )

    def handle(self, *args, **options):
        dataset = load_default_gold_dataset(Path(settings.BASE_DIR))
        cases = relevant_gold_cases(dataset, SUPPORTED_RULE_CODES)
        report = evaluate_gold_cases(
            cases,
            supported_rule_codes=SUPPORTED_RULE_CODES,
        )

        output_dir = Path(settings.BASE_DIR) / options["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = output_dir / "tajwid_v3_mad_summary.json"
        mismatch_path = output_dir / "tajwid_v3_mad_mismatches.csv"

        summary_path.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        with mismatch_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["case_id", "mismatch_type", "rule_code", "detail"],
            )
            writer.writeheader()
            for mismatch in report.mismatches:
                writer.writerow(mismatch.to_dict())

        self.stdout.write("Tajwid v3 — Mad Evaluation")
        self.stdout.write(f"Cases     : {report.total_cases}")
        self.stdout.write(f"Passed    : {report.passed_cases}")
        self.stdout.write(f"Failed    : {report.failed_cases}")
        self.stdout.write("DB write  : TIDAK")
        self.stdout.write(f"Summary   : {summary_path}")
        self.stdout.write(f"Mismatches: {mismatch_path}")

        if options["fail_on_errors"] and not report.success:
            raise CommandError("Mad Detector v3 belum lulus goldset.")
