from django.core.exceptions import ValidationError
from django.db import models


ALLOWED_TUNTUNAN_BLOCK_TYPES = {
    "heading",
    "paragraph",
    "arabic",
    "transliteration",
    "translation",
    "step",
    "surah",
    "image",
}


def validate_tuntunan_blocks(blocks):
    if not isinstance(blocks, list):
        raise ValidationError("Blocks must be a list.")

    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise ValidationError(f"Block at index {index} must be an object.")

        block_type = block.get("type")
        if block_type not in ALLOWED_TUNTUNAN_BLOCK_TYPES:
            raise ValidationError(
                f"Invalid block type at index {index}: {block_type}"
            )


class TuntunanShalat(models.Model):
    order = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Tuntunan Shalat"
        verbose_name_plural = "Tuntunan Shalat"

    def __str__(self):
        return self.title


class TuntunanShalatPage(models.Model):
    tuntunan = models.ForeignKey(
        TuntunanShalat,
        related_name="pages",
        on_delete=models.CASCADE
    )
    page_number = models.PositiveIntegerField()
    page_title = models.CharField(max_length=255)
    blocks = models.JSONField(
        default=list,
        validators=[validate_tuntunan_blocks],
        help_text="Array of content blocks: heading, paragraph, arabic, transliteration, translation, step, surah, image."
    )

    class Meta:
        ordering = ["page_number", "id"]
        unique_together = ("tuntunan", "page_number")
        verbose_name = "Tuntunan Shalat Page"
        verbose_name_plural = "Tuntunan Shalat Pages"

    def __str__(self):
        return f"{self.tuntunan.title} - Page {self.page_number}"


class TuntunanShalatImage(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="tuntunan_shalat/images/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]
        verbose_name = "Tuntunan Shalat Image"
        verbose_name_plural = "Tuntunan Shalat Images"

    def __str__(self):
        return self.title