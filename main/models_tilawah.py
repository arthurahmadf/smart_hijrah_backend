# models_tilawah.py

from django.db import models
from django.conf import settings  # ganti import User
from pgvector.django import VectorField

LEVEL_CHOICES = [
    ('basic', 'Basic'),
    ('intermediate', 'Intermediate'),
    ('expert', 'Expert'),
]

class TilawahSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # pakai string
    surah_number = models.IntegerField()
    surah_name = models.CharField(max_length=100)
    ayah_number = models.IntegerField()
    ayah_text = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    tajwid_score = models.FloatField(null=True, blank=True)
    word_accuracy = models.FloatField(null=True, blank=True)
    audio_file = models.FileField(upload_to='tilawah_audio/', null=True, blank=True)
    transcript = models.TextField(null=True, blank=True)
    feedback_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.surah_name}:{self.ayah_number}"



class TilawahAyahPool(models.Model):
    surah_number = models.IntegerField()
    surah_name = models.CharField(max_length=100)
    surah_name_id = models.CharField(max_length=100, blank=True, null=True)  # Nama surah dalam Bahasa Indonesia
    ayah_number = models.IntegerField()
    ayah_text = models.TextField()
    ayah_transliteration = models.TextField(blank=True, null=True)
    ayah_translation = models.TextField(blank=True, null=True)
    juz = models.IntegerField(blank=True, null=True)  # Nomor juz (1-30)

    embedding = VectorField(dimensions=1024, null=True, blank=True)
    level = models.CharField(max_length=20, choices=[
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert')
    ], default='basic')
    audio_url = models.URLField(blank=True, null=True)
    
    class Meta:
        db_table = 'tilawah_ayah_pool'
        ordering = ['surah_number', 'ayah_number']
        unique_together = ('surah_number', 'ayah_number')

    def __str__(self):
        return f"{self.surah_name}:{self.ayah_number} ({self.level})"