# main/management/commands/seed_doa.py

from django.core.management.base import BaseCommand

from main.models_doa import DoaCategory, Doa, DoaContent, DoaBookmark


class Command(BaseCommand):
    help = "Seed dummy data for Doa"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Doa data...")

        DoaBookmark.objects.all().delete()
        DoaContent.objects.all().delete()
        Doa.objects.all().delete()
        DoaCategory.objects.all().delete()

        category = DoaCategory.objects.create(
            order=1,
            title="Doa Keseharian",
            is_active=True,
        )

        doa = Doa.objects.create(
            category=category,
            order=1,
            title="Doa Sebelum & Bangun Tidur",
            page_title="Doa Sebelum & Bangun Tidur",
            # hero_image_url="https://url-to-image.jpg/",
            is_active=True,
        )

        DoaContent.objects.create(
            doa=doa,
            order=1,
            sub_title="Doa Sebelum Tidur",
            description="Membaca doa sebelum tidur sebagai bentuk mengingat Allah sebelum beristirahat.",
            arabic_text="بِاسْمِكَ اللّٰهُمَّ أَحْيَا وَأَمُوتُ",
            transliteration="Bismika Allahumma ahyaa wa amuut",
            translation="Dengan nama-Mu ya Allah aku hidup dan aku mati.",
            reference="HR. Bukhari",
        )

        DoaContent.objects.create(
            doa=doa,
            order=2,
            sub_title="Doa Bangun Tidur",
            description="Doa yang dibaca ketika bangun dari tidur.",
            arabic_text="الْحَمْدُ لِلّٰهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا وَإِلَيْهِ النُّشُورُ",
            transliteration="Alhamdulillaahil-ladzii ahyaanaa ba'da maa amaatanaa wa ilaihin-nusyuur",
            translation="Segala puji bagi Allah yang telah menghidupkan kami setelah mematikan kami, dan kepada-Nya kami dibangkitkan.",
            reference="HR. Bukhari",
        )

        self.stdout.write(self.style.SUCCESS("Doa data seeded successfully."))