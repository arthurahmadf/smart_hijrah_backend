import requests
from django.core.management.base import BaseCommand
from main.models_tilawah import TilawahAyahPool

class Command(BaseCommand):
    help = 'Import transliteration and translation from Alquran.cloud API'

    def handle(self, *args, **options):
        # API yang menyediakan 3 edition sekaligus: teks Utsmani, transliterasi, dan terjemahan Indonesia
        url = "https://api.alquran.cloud/v1/quran/editions/quran-uthmani,en.transliteration,id.kemenag"
        
        self.stdout.write("Downloading data from Alquran.cloud...")
        response = requests.get(url)
        
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f"Failed to download data: {response.status_code}"))
            return
        
        data = response.json()
        
        # Data tersedia dalam bentuk list of editions
        # edition 1: quran-uthmani, edition 2: en.transliteration, edition 3: id.kemenag
        editions = data['data']
        
        uthmani_verses = editions[0]['verses']
        translit_verses = editions[1]['verses']
        trans_verses = editions[2]['verses']
        
        updated = 0
        not_found = 0
        
        for uthmani, translit, trans in zip(uthmani_verses, translit_verses, trans_verses):
            surah_number = uthmani['chapterId']
            ayah_number = uthmani['verseNumber']
            uthmani_text = uthmani['text']
            translit_text = translit['text']
            trans_text = trans['text']
            
            # Cari dan update record yang sudah ada
            result = TilawahAyahPool.objects.filter(
                surah_number=surah_number,
                ayah_number=ayah_number
            ).update(
                ayah_text=uthmani_text,
                ayah_transliteration=translit_text,
                ayah_translation=trans_text
            )
            
            if result:
                updated += 1
            else:
                not_found += 1
            
            if updated % 100 == 0:
                self.stdout.write(f"Processed {updated} verses...")
        
        self.stdout.write(self.style.SUCCESS(f"Done! Updated: {updated}, Not found: {not_found}"))