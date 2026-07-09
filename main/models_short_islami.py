from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from main.utils_media_islami.file_validator import validate_video_size
from .models_media_category import MediaCategory


class ShortIslami(models.Model):
    title = models.CharField(
        max_length=255,
        db_index=True,
    )

    thumbnail = models.ImageField(
        upload_to="media_islami/shorts/thumbnails/",
        blank=True,
        null=True,
    )

    video = models.FileField(
        upload_to="media_islami/shorts/videos/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "mp4",
                    "mov",
                    "webm",
                ]
            ),
            validate_video_size,
        ],
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    category = models.ForeignKey(
        MediaCategory,
        on_delete=models.PROTECT,
        related_name="shorts",
    )

    view_count = models.BigIntegerField(
        default=0,
        db_index=True,
    )

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_shorts_islami",
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
        db_table = "short_islami"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_published", "-created_at"]),
            models.Index(fields=["category", "-created_at"]),
            models.Index(fields=["view_count"]),
        ]

    def __str__(self):
        return self.title