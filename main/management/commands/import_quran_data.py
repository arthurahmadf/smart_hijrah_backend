import requests
from django.core.management.base import BaseCommand
from main.models_tilawah import TilawahAyahPool

class Command(BaseCommand):
    help = 'Update transliteration and translation'

    def handle(self, *args, **options):
        print("Downloading data...")
        trans_url = "https://cdn.jsdelivr.net/npm/quran-json@3.1.2/dist/quran_transliteration.json"
        trans_data = requests.get(trans_url).json()
        
        id_url = "https://cdn.jsdelivr.net/npm/quran-json@3.1.2/dist/quran_id.json"
        id_data = requests.get(id_url).json()
        
        updated = 0
        
        for surah_idx in range(114):
            surah_trans = trans_data[surah_idx]
            surah_id = id_data[surah_idx]
            
            surah_number = surah_idx + 1
            
            verses_trans = surah_trans.get('verses', [])
            verses_id = surah_id.get('verses', [])
            
            for i in range(len(verses_trans)):
                ayah_number = i + 1
                transliteration = verses_trans[i].get('text', '')
                translation = verses_id[i].get('text', '') if i < len(verses_id) else ''
                
                # Update berdasarkan surah_number dan ayah_number
                result = TilawahAyahPool.objects.filter(
                    surah_number=surah_number,
                    ayah_number=ayah_number
                ).update(
                    ayah_transliteration=transliteration,
                    ayah_translation=translation
                )
                
                if result:
                    updated += 1
            
            print(f"Processed surah {surah_number}")
        
        print(f"Done! Updated {updated} verses.")