from __future__ import annotations

import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from main.models_tilawah import (
    TilawahAyahPool,
    TilawahAyahTajwidAnnotation,
    TilawahAyahTajwidAnnotationSet,
    TilawahTajwidRule,
)
from main.utils_tilawah.tajwid_rule_catalog import TAJWID_RULE_CATALOG


class SyncTajwidRuleCatalogCommandTests(TestCase):
    def test_sync_is_idempotent(self):
        call_command("sync_tajwid_rule_catalog", verbosity=0)
        first_count = TilawahTajwidRule.objects.count()

        call_command("sync_tajwid_rule_catalog", verbosity=0)
        second_count = TilawahTajwidRule.objects.count()

        self.assertEqual(first_count, len(TAJWID_RULE_CATALOG))
        self.assertEqual(second_count, first_count)

    def test_dry_run_does_not_write_database(self):
        call_command("sync_tajwid_rule_catalog", "--dry-run", verbosity=0)
        self.assertEqual(TilawahTajwidRule.objects.count(), 0)


class AuditTajwidEngineCommandTests(TestCase):
    def setUp(self):
        self.ayah = TilawahAyahPool.objects.create(
            surah_number=1,
            surah_name="Al-Fatihah",
            surah_name_id="Pembukaan",
            ayah_number=1,
            ayah_text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            level="basic",
        )

    def test_audit_is_read_only_and_writes_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            call_command(
                "audit_tajwid_engine",
                "--surah",
                "1",
                "--ayah",
                "1",
                "--output-dir",
                directory,
                verbosity=0,
            )

            summary_path = Path(directory) / "tajwid_engine_audit.json"
            self.assertTrue(summary_path.exists())

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["counters"]["total_ayah"], 1)
            self.assertFalse(summary["database_write_performed"])

            self.assertEqual(
                TilawahAyahTajwidAnnotationSet.objects.count(),
                0,
            )
            self.assertEqual(
                TilawahAyahTajwidAnnotation.objects.count(),
                0,
            )
