# main/management/commands/generate_hadis_embeddings.py
import time
from django.core.management.base import BaseCommand
from main.models_hadis import Hadis
from main.utils_embedding.embedder import batch_get_embeddings

class Command(BaseCommand):
    help = 'Generate embedding vectors for all hadis'

    def handle(self, *args, **options):
        self.stdout.write('Generating embeddings for hadis...')
        
        # Ambil semua hadis yang belum punya embedding
        hadis_list = list(Hadis.objects.filter(embedding__isnull=True))
        total = len(hadis_list)
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Semua hadis sudah memiliki embedding!'))
            return
        
        self.stdout.write(f'Total hadis tanpa embedding: {total}')
        
        batch_size = 32
        updated = 0
        
        for i in range(0, total, batch_size):
            batch = hadis_list[i:i+batch_size]
            
            # Gabungkan teks untuk embedding (isi_hadis + teks_hadis)
            texts = []
            for h in batch:
                # Kombinasi terjemahan + teks Arab (untuk makna yang lebih kaya)
                text = f"{h.isi_hadis[:500]} {h.teks_hadis[:200]}"
                texts.append(text)
            
            # Generate embeddings
            embeddings = batch_get_embeddings(texts)
            
            # Simpan ke database
            for hadis, emb in zip(batch, embeddings):
                hadis.embedding = emb
                hadis.save(update_fields=['embedding'])
                updated += 1
            
            if updated % 100 == 0:
                self.stdout.write(f'  → {updated}/{total} hadis diproses')
            
            # Jeda kecil agar tidak overload
            time.sleep(0.1)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Selesai! {updated} hadis berhasil di-embedding.'))