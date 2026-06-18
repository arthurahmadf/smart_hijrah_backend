# main/management/commands/import_quran_final.py

import json
import requests
from django.core.management.base import BaseCommand
from main.models_tilawah import TilawahAyahPool

class Command(BaseCommand):
    help = 'Import Quran data from brianadi/Al-Quran-ID-Json repository'

    def handle(self, *args, **options):
        url = "https://raw.githubusercontent.com/brianadi/Al-Quran-ID-Json/refs/heads/main/al-quran.json"
        
        self.stdout.write("Mengunduh data Quran...")
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Gagal mengunduh data: {str(e)}"))
            return
        
        self.stdout.write("Data berhasil diunduh. Memulai impor...")
        
        total_ayat = 0
        created_count = 0
        updated_count = 0
        
        for surah in data['features']:
            surah_number = surah['quranNumber']
            surah_name = surah['name']
            surah_name_id = surah.get('translationId', '')
            
            self.stdout.write(f"Memproses Surah {surah_number}: {surah_name}")
            
            for ayat in surah['text']:
                ayah_number = ayat['verseId']
                ayah_text = ayat['ayahText']
                ayah_transliteration = ayat.get('readText', '')
                ayah_translation = ayat.get('indoText', '')
                juz = ayat.get('juz', None)
                
                obj, created = TilawahAyahPool.objects.update_or_create(
                    surah_number=surah_number,
                    ayah_number=ayah_number,
                    defaults={
                        'surah_name': surah_name,
                        'surah_name_id': surah_name_id,
                        'ayah_text': ayah_text,
                        'ayah_transliteration': ayah_transliteration,
                        'ayah_translation': ayah_translation,
                        'juz': juz,
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                
                total_ayat += 1
                
                if total_ayat % 500 == 0:
                    self.stdout.write(f"  → {total_ayat} ayat telah diproses...")
        
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ IMPOR SELESAI!\n"
            f"   Total ayat: {total_ayat}\n"
            f"   Baru dibuat: {created_count}\n"
            f"   Diperbarui: {updated_count}"
        ))