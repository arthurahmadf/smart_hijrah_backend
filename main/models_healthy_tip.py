from django.conf import settings
from django.db import models


class HealthyTip(models.Model):
    class Section(models.TextChoices):
        TIPS_BARU = "tips_baru", "Tips Baru"
        SEMINAR_SEHAT = "seminar_sehat", "Seminar Sehat"
        GENERAL = "general", "General"

    title = models.CharField(max_length=255)
    banner = models.ImageField(upload_to="healthy_tips/", blank=True, null=True)
    description_short = models.TextField()
    category = models.CharField(max_length=100)
    article = models.TextField(help_text="Isi artikel dalam format Markdown.")

    section = models.CharField(
        max_length=30,
        choices=Section.choices,
        default=Section.GENERAL,
        db_index=True,
    )

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="healthy_tips",
    )

    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "healthy_tips"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["section", "-created_at"]),
            models.Index(fields=["is_published", "-created_at"]),
        ]

    def __str__(self):
        return self.title