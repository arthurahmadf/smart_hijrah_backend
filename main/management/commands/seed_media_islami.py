from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from main.models_artikel_islami import ArtikelIslami
from main.models_media_category import MediaCategory
from main.models_short_islami import ShortIslami


class Command(BaseCommand):
    help = "Seed Media Islami"

    def handle(self, *args, **kwargs):

        User = get_user_model()

        admin = User.objects.filter(is_superuser=True).first()

        if not admin:
            self.stdout.write(
                self.style.ERROR("Superuser tidak ditemukan.")
            )
            return

        categories = [
            "Tips & Trick",
            "Pola Makan",
            "Olahraga",
            "Tidur",
            "Ibadah",
            "Aqidah",
        ]

        category_map = {}

        for name in categories:

            category, _ = MediaCategory.objects.get_or_create(
                name=name
            )

            category_map[name] = category

        ArtikelIslami.objects.get_or_create(
            title="Luangkan Waktu untuk Berdzikir",
            defaults={
                "description": "Dzikir pagi dan petang menjaga hati tetap tenang.",
                "category": category_map["Ibadah"],
                "article": "# Dzikir\n\nPerbanyak dzikir setiap hari...",
                "uploader": admin,
                "is_published": True,
            },
        )

        ArtikelIslami.objects.get_or_create(
            title="Tidur Lebih Awal",
            defaults={
                "description": "Tidur cukup membantu kualitas ibadah.",
                "category": category_map["Tidur"],
                "article": "# Tidur\n\nIslam menganjurkan tidur lebih awal...",
                "uploader": admin,
                "is_published": True,
            },
        )

        ShortIslami.objects.get_or_create(
            title="Awali Hari dengan Bismillah",
            defaults={
                "description": "Kebiasaan sederhana namun penuh keberkahan.",
                "category": category_map["Tips & Trick"],
                "uploader": admin,
                "is_published": True,
            },
        )

        ShortIslami.objects.get_or_create(
            title="Olahraga Setelah Subuh",
            defaults={
                "description": "Tubuh sehat untuk ibadah yang lebih baik.",
                "category": category_map["Olahraga"],
                "uploader": admin,
                "is_published": True,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed Media Islami berhasil."
            )
        )