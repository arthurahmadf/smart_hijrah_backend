from django.conf import settings
from django.db import models


class DoaCategory(models.Model):
    order = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Doa Category"
        verbose_name_plural = "Doa Categories"

    def __str__(self):
        return self.title


class Doa(models.Model):
    category = models.ForeignKey(
        DoaCategory,
        related_name="doas",
        on_delete=models.CASCADE
    )
    order = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=255)
    page_title = models.CharField(max_length=255)
    hero_image = models.ImageField(
        upload_to="doa/hero_images/",
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Doa"
        verbose_name_plural = "Doa"

    def __str__(self):
        return self.title


class DoaContent(models.Model):
    doa = models.ForeignKey(
        Doa,
        related_name="contents",
        on_delete=models.CASCADE
    )
    order = models.PositiveIntegerField(default=0)
    sub_title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    arabic_text = models.TextField()
    transliteration = models.TextField(blank=True, null=True)
    translation = models.TextField()
    reference = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Doa Content"
        verbose_name_plural = "Doa Contents"

    def __str__(self):
        return f"{self.doa.title} - {self.sub_title}"


class DoaBookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="doa_bookmarks",
        on_delete=models.CASCADE
    )
    doa = models.ForeignKey(
        Doa,
        related_name="bookmarks",
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "doa")
        verbose_name = "Doa Bookmark"
        verbose_name_plural = "Doa Bookmarks"

    def __str__(self):
        return f"{self.user} - {self.doa.title}"