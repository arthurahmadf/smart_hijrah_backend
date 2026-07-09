from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from .models_book_author import BookAuthor
from .models_book_category import BookCategory

from main.utils_epustaka.file_validator import validate_pdf_size
class IslamicBook(models.Model):
    title = models.CharField(
        max_length=255,
        db_index=True,
    )

    cover = models.ImageField(
        upload_to="e_pustaka/covers/",
        blank=True,
        null=True,
    )

    category = models.ForeignKey(
        BookCategory,
        on_delete=models.PROTECT,
        related_name="books",
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    publish_year = models.PositiveIntegerField(
        db_index=True,
    )

    author = models.ForeignKey(
        BookAuthor,
        on_delete=models.PROTECT,
        related_name="books",
    )

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_books",
    )

    sold_count = models.BigIntegerField(
        default=0,
        db_index=True,
    )

    synopsis = models.TextField()

    pdf = models.FileField(
        upload_to="e_pustaka/books/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"]
            ),
            validate_pdf_size,
        ],
    )

    is_recommended = models.BooleanField(
        default=False,
        db_index=True,
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
        db_table = "islamic_books"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_published", "-created_at"]),
            models.Index(fields=["category", "-created_at"]),
            models.Index(fields=["author"]),
            models.Index(fields=["is_recommended"]),
            models.Index(fields=["sold_count"]),
        ]

    def __str__(self):
        return self.title
    
    def clean(self):
        if self.discount > self.price:
            raise ValidationError(
                "Discount tidak boleh lebih besar dari harga."
            )