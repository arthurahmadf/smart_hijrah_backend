from django.core.management.base import BaseCommand
from main.models_tuntunan_shalat import TuntunanShalat


class Command(BaseCommand):
    help = "Seed dummy data for Tuntunan Shalat"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Tuntunan Shalat data...")

        TuntunanShalat.objects.all().delete()

        TuntunanShalat.objects.create(
            order=1,
            title="Adzan dan Iqomah",
            excerpt="Panduan singkat tentang adzan dan iqomah.",
            content=(
                "Adzan adalah panggilan untuk memberitahukan masuknya waktu shalat fardhu.\n\n"
                "Iqomah dikumandangkan sebagai tanda bahwa shalat berjamaah akan segera dimulai.\n\n"
                "Umat Islam dianjurkan untuk menjawab lafaz adzan dan mempersiapkan diri menuju shalat."
            ),
            is_active=True,
        )

        TuntunanShalat.objects.create(
            order=2,
            title="Shalat Subuh",
            excerpt="Panduan singkat pelaksanaan shalat Subuh.",
            content=(
                "Shalat Subuh terdiri dari dua rakaat dan dikerjakan sejak terbit fajar hingga sebelum terbit matahari.\n\n"
                "Niat shalat Subuh dilakukan di dalam hati ketika hendak memulai shalat.\n\n"
                "Setelah takbiratul ihram, shalat dilanjutkan dengan membaca doa iftitah, Al-Fatihah, surah pendek, rukuk, i'tidal, sujud, duduk di antara dua sujud, dan seterusnya hingga salam."
            ),
            is_active=True,
        )

        self.stdout.write(self.style.SUCCESS("Tuntunan Shalat data seeded successfully."))