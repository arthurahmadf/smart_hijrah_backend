from django.db import models


class BookAuthor(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "book_authors"
        ordering = ["name"]
        verbose_name = "Book Author"
        verbose_name_plural = "Book Authors"

    def __str__(self):
        return self.name