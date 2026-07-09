from django.db import models
from django.core.exceptions import ValidationError
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
    """
    Legacy validator kept for old migrations.
    Do not remove unless old migrations are squashed.
    """
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

from django.db import models


class TuntunanShalat(models.Model):
    order = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=255)
    excerpt = models.TextField(blank=True, null=True)
    hero_image = models.ImageField(
        upload_to="tuntunan_shalat/hero_images/",
        blank=True,
        null=True
    )
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Tuntunan Shalat"
        verbose_name_plural = "Tuntunan Shalat"

    def __str__(self):
        return self.title