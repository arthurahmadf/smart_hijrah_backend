# models_tilawah.py

from django.db import models
from django.conf import settings  # ganti import User

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
    ayah_number = models.IntegerField()
    ayah_text = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    audio_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        unique_together = ['surah_number', 'ayah_number']

    def __str__(self):
        return f"{self.surah_name}:{self.ayah_number} ({self.level})"