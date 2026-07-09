# main/models_hadis.py
from django.db import models
from django.contrib.postgres.search import SearchVectorField

from pgvector.django import VectorField

class KitabHadis(models.Model):
    """Master kitab hadis (Bukhari, Muslim, dll)"""
    nama_file = models.CharField(max_length=50, unique=True)  # 'abu-daud'
    nama_indonesia = models.CharField(max_length=100)         # 'Sunan Abu Daud'
    jumlah_hadis = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'hadis_kitab'
        ordering = ['nama_indonesia']
    
    def __str__(self):
        return self.nama_indonesia


class Hadis(models.Model):
    """Model untuk menyimpan hadis"""
    kitab = models.ForeignKey(KitabHadis, on_delete=models.CASCADE, related_name='hadis')
    nomor = models.IntegerField()
    embedding = VectorField(dimensions=1024, null=True, blank=True)
    # Teks asli (dengan sanad) - untuk display
    teks_arab = models.TextField()
    terjemahan = models.TextField()
    
    # Teks bersih (tanpa sanad) - untuk search
    teks_hadis = models.TextField()      # Arab tanpa sanad
    isi_hadis = models.TextField()       # Indonesia tanpa sanad
    
    # Untuk full-text search (PostgreSQL)
    search_vector = SearchVectorField(null=True, blank=True)
    
    class Meta:
        db_table = 'hadis'
        unique_together = ('kitab', 'nomor')
        indexes = [
            models.Index(fields=['kitab', 'nomor']),
        ]
        ordering = ['kitab', 'nomor']
    
    def __str__(self):
        return f"{self.kitab.nama_indonesia} No. {self.nomor}"