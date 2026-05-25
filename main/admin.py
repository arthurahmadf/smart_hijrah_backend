# main/admin.py
from django.contrib import admin
from .models_fest import Fest

@admin.register(Fest)
class FestAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'date', 'is_headline', 'is_recommendation']
    list_filter = ['category', 'is_headline', 'is_recommendation']
    search_fields = ['title', 'description']
    readonly_fields = ['banner_preview']
    
    def banner_preview(self, obj):
        if obj.banner:
            from django.utils.html import mark_safe
            return mark_safe(f'<img src="{obj.banner.url}" width="300" height="130" style="object-fit:cover;" />')
        return "No image"
    banner_preview.short_description = 'Banner Preview'