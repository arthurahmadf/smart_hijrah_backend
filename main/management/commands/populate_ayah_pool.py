from django.core.management.base import BaseCommand
from main.models_tilawah import TilawahAyahPool
from main.utils_tilawah.quran_data import get_all_ayahs
from main.utils_tilawah.tajwid_classifier import classify_level

# Surah yang di-whitelist sebagai basic (surah pendek & populer)
BASIC_WHITELIST_SURAHS = [1, 108, 110, 112, 113, 114]

# Surah yang di-whitelist sebagai intermediate (surah menengah & populer)
INTERMEDIATE_WHITELIST_SURAHS = [36, 55, 67, 78, 103, 104, 105, 106, 107, 109, 111]


class Command(BaseCommand):
    help = 'Populate TilawahAyahPool dari quran_uthmani.json'

    def handle(self, *args, **kwargs):
        self.stdout.write('Memulai populate ayah pool...')

        all_ayahs = get_all_ayahs()
        created = 0
        updated = 0
        skipped = 0

        for ayah in all_ayahs:
            if ayah['total_words'] < 2:
                skipped += 1
                continue

            # Cek whitelist dulu sebelum classifier
            if ayah['surah_number'] in BASIC_WHITELIST_SURAHS:
                level = 'basic'
            elif ayah['surah_number'] in INTERMEDIATE_WHITELIST_SURAHS:
                level = 'intermediate'
            else:
                level = classify_level(ayah['ayah_text'], ayah['total_words'])

            audio_url = (
                f"https://cdn.islamic.network/quran/audio/128/ar.alafasy/"
                f"{self._get_global_ayah_number(ayah['surah_number'], ayah['ayah_number'])}.mp3"
            )

            obj, is_created = TilawahAyahPool.objects.update_or_create(
                surah_number=ayah['surah_number'],
                ayah_number=ayah['ayah_number'],
                defaults={
                    'surah_name': ayah['surah_name'],
                    'ayah_text': ayah['ayah_text'],
                    'level': level,
                    'audio_url': audio_url,
                }
            )

            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Selesai! {created} ayat baru, {updated} diupdate, {skipped} dilewati. '
            f'Total diproses: {created + updated + skipped}'
        ))

    def _get_global_ayah_number(self, surah_number, ayah_number):
        from main.utils_tilawah.quran_data import get_quran_data
        quran = get_quran_data()
        total = 0
        for surah in quran:
            if surah['id'] == surah_number:
                return total + ayah_number
            total += surah['total_verses']
        return total