from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

class Fest(models.Model):
    banner = models.ImageField(upload_to='fest_banners/', max_length=500)  # Ganti ke ImageField
    title = models.CharField(max_length=255)
    date = models.DateField()
    address = models.CharField(max_length=500)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    category = models.CharField(max_length=100)
    description = models.TextField()
    
    is_headline = models.BooleanField(default=False)
    is_recommendation = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lifestyle_fest'
        ordering = ['date']
    
    def save(self, *args, **kwargs):
        # Crop image to 120:59 aspect ratio (without resizing)
        if self.banner:
            img = Image.open(self.banner)
            
            # Target aspect ratio 120:59 ≈ 2.0339
            target_ratio = 120 / 59
            current_ratio = img.width / img.height
            
            if abs(current_ratio - target_ratio) > 0.01:
                if current_ratio > target_ratio:
                    # Image too wide, crop width
                    new_width = int(img.height * target_ratio)
                    offset = (img.width - new_width) // 2
                    img = img.crop((offset, 0, offset + new_width, img.height))
                elif current_ratio < target_ratio:
                    # Image too tall, crop height
                    new_height = int(img.width / target_ratio)
                    offset = (img.height - new_height) // 2
                    img = img.crop((0, offset, img.width, offset + new_height))
            
            # Save to BytesIO (without resizing to small dimensions)
            buffer = BytesIO()
            img_format = 'PNG' if self.banner.name.lower().endswith('.png') else 'JPEG'
            img.save(buffer, format=img_format)
            
            # Replace file
            self.banner.save(
                os.path.basename(self.banner.name),
                ContentFile(buffer.getvalue()),
                save=False
            )
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title