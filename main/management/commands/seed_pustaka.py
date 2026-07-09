from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from main.models_book_author import BookAuthor
from main.models_book_category import BookCategory
from main.models_islamic_book import IslamicBook


class Command(BaseCommand):
    help = "Seed E-Pustaka"

    def handle(self, *args, **kwargs):

        User = get_user_model()

        admin = User.objects.filter(is_superuser=True).first()

        if not admin:
            self.stdout.write(
                self.style.ERROR(
                    "Superuser tidak ditemukan."
                )
            )
            return

        categories = [
            "Al-Qur'an & Tafsir",
            "Hadits & Sunnah",
            "Hukum Islam",
            "Aqidah & Tauhid",
            "Akhlak & Adab",
            "Sejarah Peradaban Islam",
            "Pernikahan",
            "Keluarga Islami",
            "Parenting Islami",
        ]

        category_map = {}

        for name in categories:

            category, _ = BookCategory.objects.get_or_create(
                name=name
            )

            category_map[name] = category

        author, _ = BookAuthor.objects.get_or_create(
            name="Istannia Widayati Hidayati"
        )

        IslamicBook.objects.get_or_create(
            title="Nalar Tasawuf",
            defaults={
                "category": category_map["Aqidah & Tauhid"],
                "price": 2500.56,
                "discount": 500.56,
                "publish_year": 2026,
                "author": author,
                "uploader": admin,
                "sold_count": 56334,
                "synopsis": (
                    "Buku ini membahas konsep tasawuf "
                    "dalam kehidupan modern."
                ),
                "is_recommended": True,
                "is_published": True,
            },
        )

        IslamicBook.objects.get_or_create(
            title="Keluarga Islami Bahagia",
            defaults={
                "category": category_map["Keluarga Islami"],
                "price": 0,
                "discount": 0,
                "publish_year": 2025,
                "author": author,
                "uploader": admin,
                "sold_count": 1200,
                "synopsis": (
                    "Panduan membangun keluarga "
                    "yang sakinah mawaddah warahmah."
                ),
                "is_recommended": False,
                "is_published": True,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed E-Pustaka berhasil."
            )
        )


        IslamicBook.objects.get_or_create(
            title="Nalar Tasawuf",
            defaults={
                "category": category_map["Aqidah & Tauhid"],
                "price": 2500.56,
                "discount": 500.56,
                "publish_year": 2026,
                "author": author,
                "uploader": admin,
                "sold_count": 56334,
                "synopsis": (
                    "Buku ini membahas konsep tasawuf dari perspektif Islam klasik "
                    "dan implementasinya dalam kehidupan modern. Pembaca diajak "
                    "memahami bagaimana penyucian hati, akhlak, dan kedekatan kepada "
                    "Allah dapat diterapkan dalam kehidupan sehari-hari tanpa "
                    "meninggalkan aktivitas dunia."
                ),
                "is_recommended": True,
                "is_published": True,
            },
        )

        IslamicBook.objects.get_or_create(
            title="Keluarga Islami Bahagia",
            defaults={
                "category": category_map["Keluarga Islami"],
                "price": 0,
                "discount": 0,
                "publish_year": 2025,
                "author": author,
                "uploader": admin,
                "sold_count": 12420,
                "synopsis": (
                    "Panduan membangun keluarga yang sakinah, mawaddah, wa rahmah "
                    "berdasarkan Al-Qur'an dan Sunnah. Buku ini memberikan contoh "
                    "praktis dalam menghadapi berbagai tantangan rumah tangga modern."
                ),
                "is_recommended": False,
                "is_published": True,
            },
        )

        IslamicBook.objects.get_or_create(
            title="Tafsir Al-Fatihah Modern",
            defaults={
                "category": category_map["Al-Qur'an & Tafsir"],
                "price": 45000,
                "discount": 0,
                "publish_year": 2024,
                "author": author,
                "uploader": admin,
                "sold_count": 42150,
                "synopsis": (
                    "Pembahasan mendalam mengenai kandungan Surat Al-Fatihah dengan "
                    "bahasa yang mudah dipahami serta dikaitkan dengan berbagai "
                    "permasalahan kehidupan masyarakat modern."
                ),
                "is_recommended": True,
                "is_published": True,
            },
        )

        IslamicBook.objects.get_or_create(
            title="Fiqih Muamalah Praktis",
            defaults={
                "category": category_map["Hukum Islam"],
                "price": 85000,
                "discount": 20000,
                "publish_year": 2025,
                "author": author,
                "uploader": admin,
                "sold_count": 27840,
                "synopsis": (
                    "Panduan lengkap mengenai fiqih muamalah mulai dari jual beli, "
                    "hutang piutang, akad, hingga transaksi digital berdasarkan "
                    "fatwa ulama dan dalil yang kuat."
                ),
                "is_recommended": False,
                "is_published": True,
            },
        )

        IslamicBook.objects.get_or_create(
            title="Parenting Islami di Era Digital",
            defaults={
                "category": category_map["Parenting Islami"],
                "price": 65000,
                "discount": 0,
                "publish_year": 2026,
                "author": author,
                "uploader": admin,
                "sold_count": 38720,
                "synopsis": (
                    "Buku ini membahas bagaimana orang tua dapat mendidik anak di era "
                    "digital dengan tetap menjadikan Al-Qur'an dan Sunnah sebagai "
                    "landasan utama dalam pembentukan karakter."
                ),
                "is_recommended": True,
                "is_published": True,
            },
        )

        IslamicBook.objects.get_or_create(
            title="40 Hadits Pilihan",
            defaults={
                "category": category_map["Hadits & Sunnah"],
                "price": 0,
                "discount": 0,
                "publish_year": 2023,
                "author": author,
                "uploader": admin,
                "sold_count": 18950,
                "synopsis": (
                    "Kumpulan empat puluh hadits pilihan beserta penjelasan ringkas "
                    "yang mudah dipahami untuk membantu pembaca mengamalkan sunnah "
                    "Rasulullah ﷺ dalam kehidupan sehari-hari."
                ),
                "is_recommended": False,
                "is_published": True,
            },
        )