from django.db import models
from django.contrib.auth.models import AbstractUser
from .models_feed import *
from .models_fest import *
from .models_klinik import *
from .models_ngaji import *
from .models_kisah_nabi import *
from .models_ai import *
from .models_tilawah import *
from .models_gamification import *
from .models_hadis import *

from .models_tuntunan_shalat import (
    TuntunanShalat,
    TuntunanShalatPage,
    TuntunanShalatImage,
)

from .models_doa import (
    DoaCategory,
    Doa,
    DoaContent,
    DoaBookmark,
)

class User(AbstractUser):
    nama = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    alamat = models.CharField(max_length=200, null=True, blank=True)
    telepon = models.CharField(max_length=20, null=True, blank=True)
    fcm_token = models.TextField(null=True, blank=True)
    foto_profil = models.ImageField(upload_to='foto_profil', null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    token_created_at = models.DateTimeField(blank=True, null=True)
    jenis_kelamin = models.CharField(
        max_length=10,
        choices=[('L', 'Laki-laki'), ('P', 'Perempuan')],
        null=True,
        blank=True
    )

    banner = models.ImageField(
        upload_to='user_banners/',
        null=True,
        blank=True,
        help_text="User profile banner with 12:5 aspect ratio (landscape)"
    )

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'user'
        

class PrayerMonthDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=100)
    year = models.IntegerField()
    month = models.IntegerField()
    timezone = models.CharField(max_length=50, default="Asia/Jakarta")
    source_hash = models.CharField(max_length=64)
    last_updated = models.DateTimeField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField()

    class Meta:
        db_table = 'jadwal_shalat_data'
        unique_together = ("user", "year", "month")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["year", "month"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.year}-{self.month}"
    
class UserPrayerPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    subuh = models.BooleanField(default=True)
    dzuhur = models.BooleanField(default=True)
    ashar = models.BooleanField(default=True)
    maghrib = models.BooleanField(default=True)
    isya = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preference'
    
class PrayerNotificationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    prayer_name = models.CharField(max_length=20)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notification_log'
        unique_together = ("user", "date", "prayer_name")


