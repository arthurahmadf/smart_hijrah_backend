from __future__ import annotations

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from main.models_tilawah import (
    TajwidAnnotationSetStatus,
    TajwidReadingMode,
    TilawahAyahPool,
    TilawahAyahTajwidAnnotation,
    TilawahAyahTajwidAnnotationSet,
    TilawahTajwidRule,
)


@admin.register(TilawahTajwidRule)
class TilawahTajwidRuleAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "display_group",
        "color",
        "priority",
        "assessment_family",
        "is_active",
    )
    list_filter = ("display_group", "assessment_family", "is_active")
    search_fields = ("code", "name", "description")
    ordering = ("priority", "code")
    readonly_fields = ("created_at", "updated_at")


class TilawahTajwidAnnotationInline(admin.TabularInline):
    model = TilawahAyahTajwidAnnotation
    extra = 0
    autocomplete_fields = ("rule",)
    fields = (
        "rule",
        "arabic_segment",
        "start_grapheme",
        "end_grapheme",
        "applies_when",
        "locator_confidence",
        "is_verified",
        "verification_note",
    )
    readonly_fields = (
        "arabic_segment",
        "start_grapheme",
        "end_grapheme",
        "applies_when",
        "locator_confidence",
    )
    ordering = ("start_grapheme", "end_grapheme", "rule__priority")
    show_change_link = True


@admin.register(TilawahAyahTajwidAnnotationSet)
class TilawahAyahTajwidAnnotationSetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "verse_key",
        "reading_mode",
        "engine_version",
        "status",
        "is_active",
        "annotation_count",
        "verification_state_display",
        "generated_at",
    )
    list_filter = (
        "reading_mode",
        "status",
        "is_active",
        "engine_version",
        "generated_at",
    )
    search_fields = (
        "ayah__surah_name",
        "ayah__surah_number",
        "ayah__ayah_number",
        "engine_version",
        "notes",
    )
    autocomplete_fields = ("ayah", "reviewed_by")
    readonly_fields = (
        "source_text_hash",
        "annotation_count",
        "issues",
        "generated_at",
        "validated_at",
        "verified_at",
        "published_at",
        "updated_at",
        "verification_state_display",
        "is_stale_display",
    )
    inlines = (TilawahTajwidAnnotationInline,)
    actions = (
        "mark_as_expert_reviewed",
        "publish_as_beta_candidate",
        "deactivate_selected",
    )
    list_select_related = ("ayah", "reviewed_by")

    @admin.display(description="Ayat", ordering="ayah__surah_number")
    def verse_key(self, obj):
        return f"{obj.ayah.surah_number}:{obj.ayah.ayah_number}"

    @admin.display(description="Verifikasi")
    def verification_state_display(self, obj):
        return obj.verification_state

    @admin.display(description="Teks berubah?", boolean=True)
    def is_stale_display(self, obj):
        return obj.is_stale

    @admin.action(description="Tandai seluruh anotasi sebagai terverifikasi ahli")
    def mark_as_expert_reviewed(self, request, queryset):
        reviewed = 0
        rejected = 0
        for pk in queryset.values_list("pk", flat=True):
            with transaction.atomic():
                obj = (
                    TilawahAyahTajwidAnnotationSet.objects
                    .select_for_update()
                    .get(pk=pk)
                )
                if obj.is_stale or not obj.is_safe_to_persist:
                    rejected += 1
                    continue
                obj.annotations.update(is_verified=True, updated_at=timezone.now())
                obj.reviewed_by = request.user
                obj.verified_at = timezone.now()
                if not obj.is_active:
                    obj.status = TajwidAnnotationSetStatus.VERIFIED
                obj.save(
                    update_fields=[
                        "reviewed_by",
                        "verified_at",
                        "status",
                        "updated_at",
                    ]
                )
                reviewed += 1
        self.message_user(
            request,
            f"{reviewed} set ditandai terverifikasi; {rejected} ditolak.",
            level=messages.SUCCESS if reviewed else messages.WARNING,
        )

    @admin.action(description="Publish/aktifkan sebagai candidate beta")
    def publish_as_beta_candidate(self, request, queryset):
        published = 0
        protected = 0
        rejected = 0
        for pk in queryset.values_list("pk", flat=True):
            try:
                with transaction.atomic():
                    obj = (
                        TilawahAyahTajwidAnnotationSet.objects
                        .select_for_update()
                        .select_related("ayah")
                        .get(pk=pk)
                    )
                    if obj.is_stale or not obj.is_safe_to_persist:
                        raise ValidationError("Set stale atau belum aman.")

                    active_sets = list(
                        TilawahAyahTajwidAnnotationSet.objects
                        .select_for_update()
                        .filter(
                            ayah=obj.ayah,
                            reading_mode=obj.reading_mode,
                            is_active=True,
                        )
                        .exclude(pk=obj.pk)
                    )
                    if any(item.has_expert_review for item in active_sets):
                        protected += 1
                        continue
                    if active_sets:
                        TilawahAyahTajwidAnnotationSet.objects.filter(
                            pk__in=[item.pk for item in active_sets]
                        ).update(is_active=False)

                    obj.status = TajwidAnnotationSetStatus.PUBLISHED
                    obj.is_active = True
                    obj.published_at = timezone.now()
                    obj.save(
                        update_fields=[
                            "status",
                            "is_active",
                            "published_at",
                            "updated_at",
                        ]
                    )
                    published += 1
            except ValidationError:
                rejected += 1

        self.message_user(
            request,
            (
                f"{published} set dipublish; {protected} dilindungi hasil ahli; "
                f"{rejected} ditolak."
            ),
            level=messages.SUCCESS if published else messages.WARNING,
        )

    @admin.action(description="Nonaktifkan dari frontend")
    def deactivate_selected(self, request, queryset):
        count = queryset.filter(is_active=True).update(is_active=False)
        self.message_user(request, f"{count} set dinonaktifkan.")


@admin.register(TilawahAyahTajwidAnnotation)
class TilawahAyahTajwidAnnotationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "verse_key",
        "rule",
        "arabic_segment",
        "applies_when",
        "locator_confidence",
        "is_verified",
    )
    list_filter = (
        "is_verified",
        "applies_when",
        "rule__display_group",
        "annotation_set__reading_mode",
    )
    search_fields = (
        "annotation_set__ayah__surah_name",
        "annotation_set__ayah__surah_number",
        "annotation_set__ayah__ayah_number",
        "rule__code",
        "rule__name",
        "arabic_segment",
        "verification_note",
    )
    autocomplete_fields = ("annotation_set", "rule")
    list_select_related = ("annotation_set__ayah", "rule")
    readonly_fields = (
        "word_index",
        "next_word_index",
        "start_grapheme",
        "end_grapheme",
        "start_codepoint",
        "end_codepoint",
        "arabic_segment",
        "applies_when",
        "expected_features",
        "locator_confidence",
        "locator_method",
        "metadata",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Ayat")
    def verse_key(self, obj):
        ayah = obj.annotation_set.ayah
        return f"{ayah.surah_number}:{ayah.ayah_number}"


@admin.register(TilawahAyahPool)
class TilawahAyahPoolAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "verse_key",
        "surah_name",
        "level",
        "active_tajwid_sets",
    )
    list_filter = ("surah_number", "level", "level_source")
    search_fields = ("surah_name", "surah_name_id", "ayah_text")
    ordering = ("surah_number", "ayah_number")
    readonly_fields = (
        "surah_number",
        "ayah_number",
        "ayah_text",
        "ayah_transliteration",
        "ayah_translation",
    )

    @admin.display(description="Ayat", ordering="surah_number")
    def verse_key(self, obj):
        return f"{obj.surah_number}:{obj.ayah_number}"

    @admin.display(description="Set tajwid aktif")
    def active_tajwid_sets(self, obj):
        return obj.tajwid_annotation_sets.filter(is_active=True).count()
