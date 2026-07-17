from django.core.management.base import BaseCommand

from main.utils_tilawah.tajwid_v3.persistence import sync_v3_rule_catalog


class Command(BaseCommand):
    help = "Sinkronkan 44 rule Tajwid Engine v3 ke katalog database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-legacy-active",
            action="store_true",
            help="Jangan nonaktifkan rule lama yang tidak termasuk taxonomy v3.",
        )

    def handle(self, *args, **options):
        summary = sync_v3_rule_catalog(
            deactivate_unknown=not options["keep_legacy_active"]
        )
        self.stdout.write(self.style.SUCCESS("Katalog Tajwid v3 tersinkron."))
        self.stdout.write(f"Created     : {summary.created}")
        self.stdout.write(f"Updated     : {summary.updated}")
        self.stdout.write(f"Unchanged   : {summary.unchanged}")
        self.stdout.write(f"Deactivated : {summary.deactivated}")
        self.stdout.write("Target v3   : 44 rule aktif")
