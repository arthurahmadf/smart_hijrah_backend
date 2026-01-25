from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    nama = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    alamat = models.CharField(max_length=200, null=True, blank=True)
    telepon = models.CharField(max_length=20, null=True, blank=True)
    fcm_token = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'user'