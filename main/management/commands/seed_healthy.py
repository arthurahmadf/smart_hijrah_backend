from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from main.models_healthy_tip import HealthyTip


class Command(BaseCommand):
    help = "Seed healthy tips data"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()

        data = [
            {
                "title": "Awali Hari dengan Shalat Subuh dan Air Putih",
                "description_short": "Kebiasaan sederhana untuk memulai hari dengan lebih sehat dan berkah.",
                "category": "Tips & Trick",
                "section": HealthyTip.Section.TIPS_BARU,
                "article": "# Awali Hari dengan Shalat Subuh dan Air Putih\n\nMemulai hari dengan shalat Subuh membantu menata hati, pikiran, dan aktivitas harian.\n\nSetelah itu, minum air putih dapat membantu tubuh kembali terhidrasi setelah tidur malam.",
            },
            {
                "title": "Pola Makan Sehat dalam Islam",
                "description_short": "Materi singkat tentang menjaga pola makan secara seimbang.",
                "category": "Pola Makan",
                "section": HealthyTip.Section.SEMINAR_SEHAT,
                "article": "# Pola Makan Sehat dalam Islam\n\nIslam mengajarkan keseimbangan dalam makan dan minum.\n\nHindari berlebihan, pilih makanan halal dan thayyib, serta biasakan makan secukupnya.",
            },
            {
                "title": "Olahraga Ringan Setelah Subuh",
                "description_short": "Aktivitas ringan untuk menjaga tubuh tetap bugar.",
                "category": "Olahraga",
                "section": HealthyTip.Section.GENERAL,
                "article": "# Olahraga Ringan Setelah Subuh\n\nJalan kaki ringan setelah Subuh dapat membantu tubuh lebih segar dan meningkatkan mood di pagi hari.",
            },
        ]

        created_count = 0

        for item in data:
            _, created = HealthyTip.objects.get_or_create(
                title=item["title"],
                defaults={
                    **item,
                    "uploader": admin_user,
                    "is_published": True,
                }
            )

            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Seed healthy tips selesai. Created: {created_count}")
        )