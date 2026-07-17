from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from main.models_tilawah import TilawahTajwidRule
from main.utils_tilawah.tajwid_rule_catalog import (
    TAJWID_RULE_CATALOG,
    validate_rule_catalog,
)


SYNC_FIELDS = (
    "name",
    "display_group",
    "description",
    "color",
    "priority",
    "default_applies_when",
    "assessment_family",
    "supported_levels",
    "expected_features",
    "is_active",
)


class Command(BaseCommand):
    help = (
        "Sinkronkan katalog hukum tajwid Python ke tabel TilawahTajwidRule. "
        "Command ini tidak membuat anotasi ayat."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Tampilkan perubahan tanpa menulis database.",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help=(
                "Periksa drift katalog dan keluar dengan error bila database "
                "belum sinkron. Tidak menulis database."
            ),
        )
        parser.add_argument(
            "--deactivate-missing",
            action="store_true",
            help=(
                "Nonaktifkan rule database yang tidak lagi terdapat dalam "
                "katalog Python. Tidak menghapus record."
            ),
        )

    def handle(self, *args: Any, **options: Any):
        validate_rule_catalog()

        dry_run = bool(options["dry_run"])
        check_only = bool(options["check"])
        deactivate_missing = bool(options["deactivate_missing"])

        if dry_run and check_only:
            raise CommandError("Gunakan salah satu dari --dry-run atau --check.")

        existing_by_code = {
            item.code: item
            for item in TilawahTajwidRule.objects.all()
        }

        create_rows: list[dict[str, Any]] = []
        update_rows: list[tuple[TilawahTajwidRule, dict[str, Any], list[str]]] = []
        unchanged_codes: list[str] = []

        for code, definition in sorted(TAJWID_RULE_CATALOG.items()):
            payload = definition.to_dict()
            payload["is_active"] = True
            payload.pop("code", None)

            existing = existing_by_code.get(code)
            if existing is None:
                create_rows.append({"code": code, **payload})
                continue

            changed_fields = [
                field
                for field in SYNC_FIELDS
                if getattr(existing, field) != payload[field]
            ]
            if changed_fields:
                update_rows.append((existing, payload, changed_fields))
            else:
                unchanged_codes.append(code)

        catalog_codes = set(TAJWID_RULE_CATALOG)
        missing_from_catalog = [
            item
            for code, item in existing_by_code.items()
            if code not in catalog_codes
        ]
        active_missing = [item for item in missing_from_catalog if item.is_active]

        self.stdout.write(
            self.style.MIGRATE_HEADING("Ringkasan sinkronisasi katalog tajwid")
        )
        self.stdout.write(f"Catalog rules      : {len(TAJWID_RULE_CATALOG)}")
        self.stdout.write(f"Akan dibuat        : {len(create_rows)}")
        self.stdout.write(f"Akan diperbarui    : {len(update_rows)}")
        self.stdout.write(f"Sudah sinkron      : {len(unchanged_codes)}")
        self.stdout.write(f"Tidak ada di katalog: {len(missing_from_catalog)}")

        for row in create_rows:
            self.stdout.write(f"  CREATE {row['code']}")
        for obj, _payload, fields in update_rows:
            self.stdout.write(
                f"  UPDATE {obj.code}: {', '.join(sorted(fields))}"
            )
        for obj in missing_from_catalog:
            state = "active" if obj.is_active else "inactive"
            self.stdout.write(f"  EXTRA  {obj.code} ({state})")

        has_drift = bool(create_rows or update_rows or active_missing)

        if check_only:
            if has_drift:
                raise CommandError(
                    "Katalog database belum sinkron. Jalankan "
                    "sync_tajwid_rule_catalog."
                )
            self.stdout.write(self.style.SUCCESS("Katalog database sinkron."))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Dry-run selesai. Database tidak diubah.")
            )
            return

        with transaction.atomic():
            for row in create_rows:
                obj = TilawahTajwidRule(**row)
                obj.full_clean()
                obj.save(force_insert=True)

            for obj, payload, changed_fields in update_rows:
                for field in changed_fields:
                    setattr(obj, field, payload[field])
                obj.full_clean()
                obj.save(update_fields=[*changed_fields, "updated_at"])

            deactivated_count = 0
            if deactivate_missing and active_missing:
                deactivated_count = TilawahTajwidRule.objects.filter(
                    pk__in=[obj.pk for obj in active_missing]
                ).update(is_active=False)
            elif active_missing:
                self.stdout.write(
                    self.style.WARNING(
                        "Ada rule aktif yang tidak terdapat di katalog. "
                        "Rule tidak diubah karena --deactivate-missing tidak "
                        "diberikan."
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Sinkronisasi selesai: "
                f"created={len(create_rows)}, "
                f"updated={len(update_rows)}, "
                f"deactivated={deactivated_count}."
            )
        )
