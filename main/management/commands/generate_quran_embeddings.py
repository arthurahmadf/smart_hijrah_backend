# main/management/commands/generate_quran_embeddings.py
import time
from django.core.management.base import BaseCommand
from main.models_tilawah import TilawahAyahPool
from main.utils_embedding.embedder import batch_get_embeddings

class Command(BaseCommand):
    help = 'Generate embedding vectors for all Quran verses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regenerate all embeddings (reset first)',
        )

    def handle(self, *args, **options):
        if options['force']:
            self.stdout.write('Resetting all Quran embeddings...')
            TilawahAyahPool.objects.all().update(embedding=None)
            self.stdout.write('Done reset!')

        self.stdout.write('Generating embeddings for Quran verses...')
        
        # Ambil semua ayat yang belum punya embedding
        ayahs = list(TilawahAyahPool.objects.filter(embedding__isnull=True))
        total = len(ayahs)
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Semua ayat sudah memiliki embedding!'))
            return
        
        self.stdout.write(f'Total ayat tanpa embedding: {total}')
        
        batch_size = 8
        updated = 0
        
        for i in range(0, total, batch_size):
            batch = ayahs[i:i+batch_size]
            
            # Gabungkan teks untuk embedding
            texts = []
            for a in batch:
                # Kombinasi teks Arab + terjemahan (untuk makna lebih kaya)
                text = f"{a.ayah_text} {a.ayah_translation or ''} {a.ayah_transliteration or ''}"
                texts.append(text)
            
            # Generate embeddings
            embeddings = batch_get_embeddings(texts)
            
            # Simpan ke database
            for ayah, emb in zip(batch, embeddings):
                ayah.embedding = emb
                ayah.save(update_fields=['embedding'])
                updated += 1
            
            if updated % 100 == 0:
                self.stdout.write(f'  → {updated}/{total} ayat diproses')
            
            # Jeda kecil agar tidak overload
            time.sleep(0.1)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Selesai! {updated} ayat berhasil di-embedding.'))