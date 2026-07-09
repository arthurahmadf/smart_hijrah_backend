# main/management/commands/seed_tuntunan_shalat.py

from django.core.management.base import BaseCommand

from main.models_tuntunan_shalat import TuntunanShalat, TuntunanShalatPage


class Command(BaseCommand):
    help = "Seed dummy data for Tuntunan Shalat"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Tuntunan Shalat data...")

        TuntunanShalatPage.objects.all().delete()
        TuntunanShalat.objects.all().delete()

        data = [
            {
                "order": 1,
                "title": "Adzan dan Iqomah",
                "pages": [
                    {
                        "page_number": 1,
                        "page_title": "Adzan dan Iqomah",
                        "blocks": [
                            {
                                "type": "heading",
                                "text": "Adzan dan Iqomah"
                            },
                            {
                                "type": "paragraph",
                                "text": "Adzan adalah panggilan untuk memberitahukan masuknya waktu shalat fardhu."
                            },
                            {
                                "type": "arabic",
                                "text": "اللّٰهُ أَكْبَرُ اللّٰهُ أَكْبَرُ"
                            },
                            {
                                "type": "transliteration",
                                "text": "Allaahu akbar, Allaahu akbar"
                            },
                            {
                                "type": "translation",
                                "text": "Allah Maha Besar, Allah Maha Besar"
                            }
                        ]
                    },
                    {
                        "page_number": 2,
                        "page_title": "Iqomah",
                        "blocks": [
                            {
                                "type": "heading",
                                "text": "Iqomah"
                            },
                            {
                                "type": "paragraph",
                                "text": "Iqomah dikumandangkan sebagai tanda bahwa shalat berjamaah akan segera dimulai."
                            }
                        ]
                    }
                ]
            },
            {
                "order": 2,
                "title": "Shalat Subuh",
                "pages": [
                    {
                        "page_number": 1,
                        "page_title": "Niat Shalat Subuh",
                        "blocks": [
                            {
                                "type": "heading",
                                "text": "Niat Shalat Subuh"
                            },
                            {
                                "type": "paragraph",
                                "text": "Shalat Subuh terdiri dari dua rakaat dan dikerjakan sejak terbit fajar hingga sebelum terbit matahari."
                            },
                            {
                                "type": "arabic",
                                "text": "أُصَلِّي فَرْضَ الصُّبْحِ رَكْعَتَيْنِ لِلّٰهِ تَعَالَى"
                            },
                            {
                                "type": "transliteration",
                                "text": "Ushallii fardhash-shubhi rak'ataini lillaahi ta'aalaa"
                            },
                            {
                                "type": "translation",
                                "text": "Aku niat melaksanakan shalat fardhu Subuh dua rakaat karena Allah Ta'ala."
                            }
                        ]
                    },
                    {
                        "page_number": 2,
                        "page_title": "Tata Cara Shalat Subuh",
                        "blocks": [
                            {
                                "type": "heading",
                                "text": "Tata Cara Shalat Subuh"
                            },
                            {
                                "type": "step",
                                "number": 1,
                                "text": "Berdiri tegak menghadap kiblat.",
                                "image_url": None
                            },
                            {
                                "type": "step",
                                "number": 2,
                                "text": "Melakukan takbiratul ihram.",
                                "image_url": None
                            },
                            {
                                "type": "step",
                                "number": 3,
                                "text": "Membaca doa iftitah, surah Al-Fatihah, dan surah pendek.",
                                "image_url": None
                            },
                            {
                                "type": "surah",
                                "name": "Al-Fatihah",
                                "description": "Pembukaan",
                                "ayah_count": 7,
                                "arabic_header": "الْفَاتِحَةُ"
                            }
                        ]
                    }
                ]
            }
        ]

        for item in data:
            tuntunan = TuntunanShalat.objects.create(
                order=item["order"],
                title=item["title"],
                is_active=True,
            )

            for page in item["pages"]:
                TuntunanShalatPage.objects.create(
                    tuntunan=tuntunan,
                    page_number=page["page_number"],
                    page_title=page["page_title"],
                    blocks=page["blocks"],
                )

        self.stdout.write(self.style.SUCCESS("Tuntunan Shalat data seeded successfully."))