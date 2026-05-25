from django.db import models
from django.conf import settings

class MasjidReview(models.Model):
    """Review dan rating untuk masjid dari user Smart Hijrah"""
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='masjid_reviews')
    place_id = models.CharField(max_length=255, db_index=True)  # ID dari Geoapify
    rating = models.IntegerField()  # 1-5
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'masjid_review'
        # Satu user hanya bisa satu review per masjid
        unique_together = ('user', 'place_id')
        indexes = [
            models.Index(fields=['place_id']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.place_id} - {self.rating}⭐"

class MasjidReviewPhoto(models.Model):
    """Foto yang diupload user saat review masjid"""
    review = models.ForeignKey(MasjidReview, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='masjid_reviews/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'masjid_review_photo'
    
    def __str__(self):
        return f"Photo for review {self.review.id}"