# main/management/commands/import_hadis.py
import json
import os
from django.core.management.base import BaseCommand
from main.models_hadis import KitabHadis, Hadis
from main.utils_hadis.clean_sanad import clean_sanad_arab, clean_sanad_indonesian

class Command(BaseCommand):
    help = 'Import hadis dari file JSON ke database'

    def handle(self, *args, **options):
        # Mapping nama file → nama kitab
        KITAB_MAPPING = {
            'abu-daud': 'Sunan Abu Daud',
            'bukhari': 'Shahih Bukhari',
            'muslim': 'Shahih Muslim',
            'tirmidzi': 'Sunan Tirmidzi',
            'nasai': 'Sunan Nasa\'i',
            'ibnu-majah': 'Sunan Ibnu Majah',
            'malik': 'Muwaththa\' Malik',
            'ahmad': 'Musnad Ahmad',
            'darimi': 'Sunan Darimi',
        }
        
        # Folder tempat file JSON
        data_dir = os.path.join(os.getcwd(), 'data', 'hadis')
        
        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f'Folder tidak ditemukan: {data_dir}'))
            return
        
        total_imported = 0
        
        for filename, kitab_name in KITAB_MAPPING.items():
            filepath = os.path.join(data_dir, f'{filename}.json')
            
            if not os.path.exists(filepath):
                self.stdout.write(self.style.WARNING(f'File tidak ditemukan: {filepath}'))
                continue
            
            self.stdout.write(f'Memproses {kitab_name}...')
            
            # Baca file JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Buat atau dapatkan kitab
            kitab, created = KitabHadis.objects.get_or_create(
                nama_file=filename,
                defaults={'nama_indonesia': kitab_name}
            )
            
            count = 0
            for item in data:
                nomor = item.get('number')
                teks_arab = item.get('arab', '')
                terjemahan = item.get('id', '')
                
                if not nomor or not teks_arab:
                    continue
                
                # Bersihkan sanad
                teks_hadis = clean_sanad_arab(teks_arab)
                isi_hadis = clean_sanad_indonesian(terjemahan)
                
                # Simpan ke database
                hadis, created = Hadis.objects.get_or_create(
                    kitab=kitab,
                    nomor=nomor,
                    defaults={
                        'teks_arab': teks_arab,
                        'terjemahan': terjemahan,
                        'teks_hadis': teks_hadis,
                        'isi_hadis': isi_hadis,
                    }
                )
                
                # Update jika sudah ada
                if not created:
                    hadis.teks_arab = teks_arab
                    hadis.terjemahan = terjemahan
                    hadis.teks_hadis = teks_hadis
                    hadis.isi_hadis = isi_hadis
                    hadis.save()
                
                count += 1
            
            # Update jumlah hadis di kitab
            kitab.jumlah_hadis = count
            kitab.save()
            
            total_imported += count
            self.stdout.write(self.style.SUCCESS(f'  ✅ {kitab_name}: {count} hadis'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ TOTAL: {total_imported} hadis berhasil diimport!'))