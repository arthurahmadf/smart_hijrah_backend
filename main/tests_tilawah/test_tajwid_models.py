from django.core.exceptions import ValidationError
from django.test import TestCase

from main.models_tilawah import (
    TajwidAnnotationSetStatus,
    TajwidAppliesWhen,
    TajwidAssessmentFamily,
    TajwidDefaultAppliesWhen,
    TajwidDisplayGroup,
    TilawahAyahPool,
    TilawahAyahTajwidAnnotation,
    TilawahAyahTajwidAnnotationSet,
    TilawahTajwidRule,
    calculate_ayah_text_hash,
)


class TilawahTajwidModelTests(TestCase):
    def setUp(self):
        self.ayah = TilawahAyahPool.objects.create(
            surah_number=1,
            surah_name="Al-Fatihah",
            surah_name_id="Pembukaan",
            ayah_number=1,
            ayah_text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            level="basic",
        )
        self.rule = TilawahTajwidRule.objects.create(
            code="mad_asli",
            name="Mad Asli",
            display_group=TajwidDisplayGroup.MAD,
            description="Huruf mad dibaca sepanjang 2 harakat.",
            color="0xFF256E99",
            priority=90,
            default_applies_when=TajwidDefaultAppliesWhen.BOTH,
            assessment_family=TajwidAssessmentFamily.DURATION,
            supported_levels=["basic", "intermediate", "expert"],
            expected_features={"nominal_harakat": 2},
        )
        self.annotation_set = TilawahAyahTajwidAnnotationSet.objects.create(
            ayah=self.ayah,
            engine_version="2.0.0",
            source_text_hash=calculate_ayah_text_hash(self.ayah.ayah_text),
            is_safe_to_persist=True,
            status=TajwidAnnotationSetStatus.VALIDATED,
        )

    def test_rule_rejects_invalid_supported_level(self):
        self.rule.supported_levels = ["basic", "invalid"]
        with self.assertRaises(ValidationError):
            self.rule.full_clean()

    def test_active_annotation_set_must_be_published(self):
        self.annotation_set.is_active = True
        with self.assertRaises(ValidationError):
            self.annotation_set.full_clean()

    def test_annotation_segment_must_match_source_text(self):
        annotation = TilawahAyahTajwidAnnotation(
            annotation_set=self.annotation_set,
            rule=self.rule,
            word_index=0,
            start_grapheme=0,
            end_grapheme=1,
            start_codepoint=0,
            end_codepoint=2,
            arabic_segment="SALAH",
            applies_when=TajwidAppliesWhen.BOTH,
            locator_confidence=1,
            locator_method="test",
        )
        with self.assertRaises(ValidationError):
            annotation.full_clean()

    def test_source_hash_detects_stale_annotation_set(self):
        self.assertFalse(self.annotation_set.is_stale)
        self.ayah.ayah_text = self.ayah.ayah_text + " "
        self.ayah.save(update_fields=["ayah_text"])
        self.annotation_set.refresh_from_db()
        self.assertTrue(self.annotation_set.is_stale)
