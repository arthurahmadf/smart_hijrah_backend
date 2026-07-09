from django.db import models


class BookCategory(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "book_categories"
        ordering = ["name"]
        verbose_name = "Book Category"
        verbose_name_plural = "Book Categories"

    def __str__(self):
        return self.name