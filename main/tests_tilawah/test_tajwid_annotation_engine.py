import unicodedata
from unittest import TestCase

from main.utils_tilawah.tajwid_annotation_engine import (
    TajwidAnnotationError,
    analyze_tajwid_annotations,
    build_render_segments,
    split_graphemes,
    validate_render_segments,
)


class TajwidAnnotationEngineTests(TestCase):
    def test_bismillah_reconstructs_exactly_and_resolves_lam_jalalah(self):
        ayah = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"

        result = analyze_tajwid_annotations(
            ayah,
            user_level="expert",
        )

        validate_render_segments(ayah, result["render_segments"])
        self.assertTrue(result["is_safe_to_persist"])
        self.assertEqual(
            "".join(item["arabic"] for item in result["render_segments"]),
            ayah,
        )

        rule_codes = [item["rule_code"] for item in result["annotations"]]
        self.assertIn("tarqiq_lam_jalalah", rule_codes)
        self.assertNotIn("tafkhim_lam_jalalah", rule_codes)
        self.assertNotIn("mad_silah_qasirah", rule_codes)

        warning_codes = {
            issue.get("rule_code")
            for issue in result["issues"]
            if issue.get("severity") == "warning"
        }
        self.assertIn("mad_silah_qasirah", warning_codes)

    def test_cross_word_ikhfa_is_annotated_for_ayah_display(self):
        ayah = "مِنْ تَحْتِهَا"

        result = analyze_tajwid_annotations(
            ayah,
            user_level="expert",
        )

        ikhfa = next(
            item
            for item in result["annotations"]
            if item["rule_code"] == "ikhfa_haqiqi"
        )
        self.assertEqual(ikhfa["arabic_segment"], "نْ")
        self.assertEqual(ikhfa["applies_when"], "wasl")

        rendered_groups = {
            item["rule_name"] for item in result["render_segments"]
        }
        self.assertIn("nun_tanwin", rendered_groups)

    def test_specific_reading_modes_filter_contextual_rules(self):
        ayah = "مَنْ يَقُولُ"
        result = analyze_tajwid_annotations(
            ayah,
            user_level="expert",
        )

        wasl_segments = build_render_segments(
            ayah,
            result["annotations"],
            reading_mode="wasl",
        )
        waqf_segments = build_render_segments(
            ayah,
            result["annotations"],
            reading_mode="waqf",
        )

        self.assertIn(
            "idgham",
            {segment["rule_name"] for segment in wasl_segments},
        )
        self.assertNotIn(
            "mad",
            {segment["rule_name"] for segment in wasl_segments},
        )

        self.assertNotIn(
            "idgham",
            {segment["rule_name"] for segment in waqf_segments},
        )
        self.assertIn(
            "mad",
            {segment["rule_name"] for segment in waqf_segments},
        )

    def test_render_segments_never_begin_with_detached_combining_mark(self):
        ayah = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        result = analyze_tajwid_annotations(ayah, user_level="expert")

        for segment in result["render_segments"]:
            first_non_space = next(
                (char for char in segment["arabic"] if not char.isspace()),
                "",
            )
            if first_non_space:
                self.assertFalse(
                    unicodedata.category(first_non_space).startswith("M")
                )

    def test_annotation_ranges_match_exact_grapheme_slices(self):
        ayah = "مِنْ بَعْدِ"
        result = analyze_tajwid_annotations(ayah, user_level="expert")
        graphemes = split_graphemes(ayah)

        for annotation in result["annotations"]:
            sliced = "".join(
                grapheme.text
                for grapheme in graphemes[
                    annotation["start_grapheme"]:
                    annotation["end_grapheme"]
                ]
            )
            self.assertEqual(sliced, annotation["arabic_segment"])

    def test_lower_priority_number_wins_overlapping_render_range(self):
        ayah = "مَٰ"
        annotations = [
            {
                "rule_code": "mad_asli",
                "display_group": "mad",
                "color": "0xFF256E99",
                "rule_description": "Mad asli",
                "priority": 90,
                "start_grapheme": 0,
                "end_grapheme": 1,
                "applies_when": "both",
            },
            {
                "rule_code": "mad_lazim_mutsaqqal",
                "display_group": "mad",
                "color": "0xFF256E99",
                "rule_description": "Mad lazim",
                "priority": 12,
                "start_grapheme": 0,
                "end_grapheme": 1,
                "applies_when": "both",
            },
        ]

        segments = build_render_segments(ayah, annotations)

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["rule_description"], "Mad lazim")
        self.assertEqual(segments[0]["arabic"], ayah)

    def test_strict_mode_rejects_any_engine_issue(self):
        ayah = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"

        with self.assertRaises(TajwidAnnotationError):
            analyze_tajwid_annotations(
                ayah,
                user_level="expert",
                strict=True,
            )

    def test_invalid_reading_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze_tajwid_annotations(
                "مِنْ بَعْدِ",
                reading_mode="invalid",
            )
