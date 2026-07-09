# main/admin.py
from django.contrib import admin
from .models import User, PrayerMonthDocument, UserPrayerPreference, PrayerNotificationLog
from .models_fest import Fest
from .models_masjid import MasjidReview, MasjidReviewPhoto
from .models_klinik import KlinikReview, KlinikReviewPhoto
from .models_ngaji import (
    KelasTahfidz, KelasSchedule, KelasEnrollment,
    Pelajaran, DetailPelajaran, MateriPelajaran
)
from .models_kisah_nabi import KisahNabi, KisahNabiEpisode, KisahNabiReadLog


from .models_tuntunan_shalat import TuntunanShalat

from .models_doa import (
    DoaCategory,
    Doa,
    DoaContent,
    DoaBookmark,
)

from main.models_healthy_tip import HealthyTip



# User
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'nama', 'email', 'telepon']
    search_fields = ['username', 'nama', 'email']

# Masjid Review
@admin.register(MasjidReview)
class MasjidReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'place_id', 'rating', 'created_at']
    list_filter = ['rating']

@admin.register(MasjidReviewPhoto)
class MasjidReviewPhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'review', 'created_at']

# Klinik Review
@admin.register(KlinikReview)
class KlinikReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'place_id', 'rating', 'created_at']
    list_filter = ['rating']

@admin.register(KlinikReviewPhoto)
class KlinikReviewPhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'review', 'created_at']

# Ngaji - Kelas Tahfidz
@admin.register(KelasTahfidz)
class KelasTahfidzAdmin(admin.ModelAdmin):
    list_display = ['title', 'lecturer_name', 'price', 'is_dewasa', 'enroll_count']
    list_filter = ['is_dewasa']
    search_fields = ['title', 'lecturer_name']

@admin.register(KelasSchedule)
class KelasScheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'kelas', 'start_time', 'end_time', 'enrolled_students']


@admin.register(KelasEnrollment)
class KelasEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'kelas', 'nama_lengkap', 'enrollment_status', 'is_dewasa', 'enrolled_at']
    list_filter = ['enrollment_status', 'is_dewasa', 'is_private', 'ngaji_level']
    search_fields = ['user__username', 'user__email', 'nama_lengkap', 'parent_name', 'parent_phone']
    readonly_fields = ['user', 'kelas', 'enrolled_at', 'updated_at']
    
    fieldsets = (
        ('Informasi Pendaftaran', {
            'fields': ('user', 'kelas', 'selected_schedule', 'enrollment_status')
        }),
        ('Data Peserta', {
            'fields': ('nama_lengkap', 'jenis_kelamin', 'usia_in_tahun', 'address', 'ngaji_level')
        }),
        ('Status', {
            'fields': ('is_dewasa', 'is_private')
        }),
        ('Data Orang Tua (jika peserta anak-anak)', {
            'fields': ('parent_name', 'parent_phone'),
            'classes': ('collapse',)
        }),
        ('Waktu', {
            'fields': ('enrolled_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
# Ngaji - Pelajaran
@admin.register(Pelajaran)
class PelajaranAdmin(admin.ModelAdmin):
    list_display = ['name', 'step', 'course_total', 'course_finished']

@admin.register(DetailPelajaran)
class DetailPelajaranAdmin(admin.ModelAdmin):
    list_display = ['pelajaran', 'name', 'step', 'is_finished']
    list_filter = ['is_finished']

@admin.register(MateriPelajaran)
class MateriPelajaranAdmin(admin.ModelAdmin):
    list_display = ['detail_pelajaran', 'title', 'arabic', 'latin', 'order']

# Kisah Nabi
@admin.register(KisahNabi)
class KisahNabiAdmin(admin.ModelAdmin):
    list_display = ['id', 'prophet_name', 'total_read_count', 'created_at']
    list_filter = ['prophet_name']
    search_fields = ['prophet_name', 'description']
    readonly_fields = ['total_read_count']

@admin.register(KisahNabiEpisode)
class KisahNabiEpisodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'kisah_nabi', 'title', 'order', 'created_at']
    list_filter = ['kisah_nabi']
    search_fields = ['title', 'description']

@admin.register(KisahNabiReadLog)
class KisahNabiReadLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'kisah_nabi', 'episode', 'read_at']
    list_filter = ['kisah_nabi', 'read_at']
    search_fields = ['user__username', 'kisah_nabi__prophet_name']
    readonly_fields = ['user', 'kisah_nabi', 'episode', 'read_at']
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


@admin.register(TuntunanShalat)
class TuntunanShalatAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "title", "is_active", "updated_at")
    list_display_links = ("id", "title")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "excerpt", "content")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Informasi Artikel", {
            "fields": ("order", "title", "excerpt", "hero_image", "is_active")
        }),
        ("Konten", {
            "fields": ("content",)
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at")
        }),
    )

class DoaContentInline(admin.TabularInline):
    model = DoaContent
    extra = 1


@admin.register(DoaCategory)
class DoaCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "title", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title",)


@admin.register(Doa)
class DoaAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "order", "category", "is_active", "hero_image")
    list_display_links = ("id", "title")
    list_editable = ("order", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("title", "page_title")
    inlines = [DoaContentInline]


@admin.register(DoaContent)
class DoaContentAdmin(admin.ModelAdmin):
    list_display = ("id", "doa", "order", "sub_title")
    list_filter = ("doa",)
    search_fields = ("sub_title", "arabic_text", "translation")


@admin.register(DoaBookmark)
class DoaBookmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "doa", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "user__email", "doa__title")


@admin.register(HealthyTip)
class HealthyTipAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "section",
        "uploader",
        "is_published",
        "created_at",
    )

    list_filter = (
        "section",
        "category",
        "is_published",
        "created_at",
    )

    search_fields = (
        "title",
        "description_short",
        "category",
        "article",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Konten", {
            "fields": (
                "title",
                "banner",
                "description_short",
                "category",
                "article",
            )
        }),
        ("Pengelompokan", {
            "fields": (
                "section",
                "is_published",
            )
        }),
        ("Uploader", {
            "fields": (
                "uploader",
            )
        }),
        ("Tanggal", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.uploader:
            obj.uploader = request.user
        super().save_model(request, obj, form, change)