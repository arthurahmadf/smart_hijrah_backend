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
        # Crop image to 300x130 aspect ratio (30:13)
        if self.banner:
            img = Image.open(self.banner)
            
            # Target aspect ratio 300:130 = 30:13 = 2.307
            target_ratio = 300 / 130  # ≈ 2.307
            current_ratio = img.width / img.height
            
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
            
            # Resize to exact 300x130
            img = img.resize((300, 130), Image.Resampling.LANCZOS)
            
            # Save to BytesIO
            buffer = BytesIO()
            img_format = 'PNG' if self.banner.name.endswith('.png') else 'JPEG'
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