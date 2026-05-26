from django.db import models
from django.conf import settings

class KlinikReview(models.Model):
    """Review dan rating untuk klinik dari user Smart Hijrah"""
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='klinik_reviews')
    place_id = models.TextField(db_index=True)  # Ubah dari 255 ke 500
    rating = models.IntegerField()
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'klinik_review'
        unique_together = ('user', 'place_id')
        indexes = [
            models.Index(fields=['place_id']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.place_id[:50]} - {self.rating}⭐"

class KlinikReviewPhoto(models.Model):
    """Foto yang diupload user saat review klinik"""
    review = models.ForeignKey(KlinikReview, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='klinik_reviews/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'klinik_review_photo'
    
    def __str__(self):
        return f"Photo for review {self.review.id}"
