from django.conf import settings
from django.db import models

from .models_media_category import MediaCategory


class ArtikelIslami(models.Model):
    title = models.CharField(
        max_length=255,
        db_index=True,
    )

    banner = models.ImageField(
        upload_to="media_islami/articles/banners/",
        blank=True,
        null=True,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    category = models.ForeignKey(
        MediaCategory,
        on_delete=models.PROTECT,
        related_name="artikel_islami",
    )

    article = models.TextField(
        help_text="Isi artikel dalam format Markdown."
    )

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_artikel_islami",
    )

    is_published = models.BooleanField(
        default=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "artikel_islami"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_published", "-created_at"]),
            models.Index(fields=["category", "-created_at"]),
        ]

    def __str__(self):
        return self.title