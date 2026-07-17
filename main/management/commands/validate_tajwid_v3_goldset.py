from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from main.utils_tilawah.tajwid_v3.gold_loader import load_gold_dataset
from main.utils_tilawah.tajwid_v3.gold_schema import default_gold_dataset_path
from main.utils_tilawah.tajwid_v3.gold_validation import (
    validate_gold_dataset,
    write_gold_validation_reports,
)


class Command(BaseCommand):
    help = (
        "Validasi bootstrap goldset Tajwid Engine v3 secara read-only dan "
        "hasilkan coverage/review reports."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset",
            type=str,
            default=None,
            help="Path JSON goldset. Default: main/data/tilawah/tajwid_v3_gold_cases.v1.json",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default=None,
            help="Folder report. Default: reports/tilawah/v3_goldset",
        )
        parser.add_argument(
            "--strict-core",
            action="store_true",
            help="Gagal jika goldset belum siap untuk development detector.",
        )
        parser.add_argument(
            "--strict-production",
            action="store_true",
            help="Gagal jika goldset belum memenuhi expert verification gate.",
        )
        parser.add_argument(
            "--no-write-report",
            action="store_true",
            help="Validasi tanpa membuat file report.",
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        dataset_path = (
            Path(options["dataset"])
            if options["dataset"]
            else default_gold_dataset_path(base_dir)
        )
        output_dir = (
            Path(options["output_dir"])
            if options["output_dir"]
            else base_dir / "reports" / "tilawah" / "v3_goldset"
        )

        try:
            dataset = load_gold_dataset(dataset_path)
            report = validate_gold_dataset(dataset)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise CommandError(f"Gagal memuat/validasi goldset: {exc}") from exc

        self.stdout.write("Tajwid v3 Goldset Validation")
        self.stdout.write(f"Dataset       : {dataset_path}")
        self.stdout.write(f"Version       : {dataset.dataset_version}")
        self.stdout.write(f"Cases         : {report.total_cases}")
        self.stdout.write(f"Errors        : {report.error_count}")
        self.stdout.write(f"Warnings      : {report.warning_count}")
        self.stdout.write(f"Expert verified: {report.expert_verified_cases}")
        self.stdout.write(
            f"Structural ready        : {'YA' if report.structural_ready else 'TIDAK'}"
        )
        self.stdout.write(
            "Detector development ready: "
            f"{'YA' if report.detector_development_ready else 'TIDAK'}"
        )
        self.stdout.write(
            f"Production ready        : {'YA' if report.production_ready else 'TIDAK'}"
        )
        self.stdout.write("Database write          : TIDAK")

        if not options["no_write_report"]:
            write_gold_validation_reports(report, dataset, output_dir)
            self.stdout.write(f"Reports                  : {output_dir}")

        if report.error_count:
            raise CommandError(
                "Goldset memiliki structural/coverage error. Periksa report."
            )
        if options["strict_core"] and not report.detector_development_ready:
            raise CommandError("Goldset belum siap untuk development detector.")
        if options["strict_production"] and not report.production_ready:
            raise CommandError(
                "Goldset belum production-ready: expert verification belum lengkap."
            )

        if report.production_ready:
            self.stdout.write(self.style.SUCCESS("Goldset production gate PASS."))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Goldset detector-development gate PASS, tetapi production "
                    "gate masih tertutup sampai validasi ahli selesai."
                )
            )
