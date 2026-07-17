from __future__ import annotations

import unittest
from pathlib import Path

from main.utils_tilawah.tajwid_v3 import (
    RULE_DISPLAY_CATALOG,
    RULE_SPECS,
    analyze_tajwid_v3,
    analyze_tajwid_v3_modes,
    frontend_rules_from_result,
    get_rule_display,
    render_engine_result,
    validate_display_catalog,
)
from main.utils_tilawah.tajwid_v3.annotations import TajwidAnnotationV3, make_text_span
from main.utils_tilawah.tajwid_v3.conflict_resolver import (
    resolve_annotation_conflicts,
    validate_resolved_annotation_set,
)
from main.utils_tilawah.tajwid_v3.gold_loader import load_gold_dataset
from main.utils_tilawah.tajwid_v3.specification import AppliesWhen
from main.utils_tilawah.tajwid_v3.token_stream import build_token_stream


class TajwidRendererV3Tests(unittest.TestCase):
    def test_display_catalog_covers_all_44_rules(self):
        self.assertEqual(44, len(RULE_SPECS))
        self.assertEqual(set(RULE_SPECS), set(RULE_DISPLAY_CATALOG))
        self.assertEqual((), validate_display_catalog())

    def test_all_display_colors_use_flutter_argb_format(self):
        for code in RULE_SPECS:
            with self.subTest(code=code):
                item = get_rule_display(code)
                self.assertRegex(item.color, r"^0xFF[0-9A-F]{6}$")
                self.assertGreaterEqual(item.priority, 1)

    def test_renderer_reconstructs_bismillah_exactly(self):
        text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        result = analyze_tajwid_v3(text, reading_mode="ayah_stop", verse_key="1:1")
        rendered = render_engine_result(result)
        self.assertFalse(result.has_errors, result.to_dict())
        self.assertTrue(rendered.is_valid)
        self.assertEqual(text, rendered.reconstruct())
        self.assertEqual(text, "".join(item.arabic for item in rendered.segments))

    def test_regular_gaps_are_preserved(self):
        result = analyze_tajwid_v3("مِنْ شَرِّ", reading_mode="wasl")
        rendered = render_engine_result(result)
        regular_text = "".join(
            item.arabic for item in rendered.segments if item.is_regular
        )
        self.assertIn("مِ", regular_text)
        self.assertTrue(regular_text)
        self.assertEqual(result.source_text, rendered.reconstruct())

    def test_overlapping_rules_keep_all_codes_but_choose_one_primary(self):
        text = "ٱلرَّحْمَٰنِ"
        result = analyze_tajwid_v3(text, reading_mode="ayah_stop")
        rendered = render_engine_result(result)
        overlap = next(
            item
            for item in rendered.segments
            if "alif_lam_shamsiyyah" in item.active_rule_codes
            and "ra_tafkhim" in item.active_rule_codes
        )
        self.assertEqual("ra_tafkhim", overlap.primary_rule_code)
        self.assertEqual(
            {"alif_lam_shamsiyyah", "ra_tafkhim"},
            set(overlap.active_rule_codes),
        )

    def test_frontend_contract_has_exact_minimal_keys(self):
        result = analyze_tajwid_v3("الْعَالَمِينَ", reading_mode="ayah_stop", verse_key="1:2")
        rules = frontend_rules_from_result(result)
        self.assertTrue(rules)
        for item in rules:
            self.assertEqual(
                {"rule_name", "color", "rule_description", "arabic"},
                set(item),
            )
        self.assertEqual(result.source_text, "".join(item["arabic"] for item in rules))

    def test_extended_segments_expose_beta_verification_status(self):
        result = analyze_tajwid_v3("مِنْ شَرِّ", reading_mode="wasl")
        rendered = render_engine_result(result, is_verified=False)
        extended = rendered.segments[0].to_extended_dict()
        self.assertFalse(extended["is_verified"])
        self.assertEqual("engine", extended["source"])
        self.assertIn("rule_codes", extended)
        self.assertIn("primary_rule_code", extended)

    def test_segments_are_contiguous_and_non_empty(self):
        result = analyze_tajwid_v3("مَنْۜ رَاقٍ", reading_mode="wasl", verse_key="75:27")
        rendered = render_engine_result(result)
        self.assertTrue(all(item.arabic for item in rendered.segments))
        for left, right in zip(rendered.segments, rendered.segments[1:]):
            self.assertEqual(left.grapheme_end, right.grapheme_start)
            self.assertEqual(left.codepoint_end, right.codepoint_start)

    def test_saktah_has_visual_priority_at_mark(self):
        result = analyze_tajwid_v3("مَنْۜ رَاقٍ", reading_mode="wasl", verse_key="75:27")
        rendered = render_engine_result(result)
        segment = next(
            item for item in rendered.segments if "saktah_wajibah" in item.active_rule_codes
        )
        self.assertEqual("saktah_wajibah", segment.primary_rule_code)
        self.assertEqual("waqf", segment.rule_name)

    def test_multi_mode_merge_distinguishes_end_of_ayah_mad(self):
        multi = analyze_tajwid_v3_modes("الْعَالَمِينَ", verse_key="1:2")
        wasl_codes = {item.rule_code for item in multi.wasl.annotations}
        stop_codes = {item.rule_code for item in multi.ayah_stop.annotations}
        self.assertIn("mad_tabii", wasl_codes)
        self.assertIn("mad_arid_lissukun", stop_codes)
        end_mad = [
            item
            for item in multi.merged_annotations
            if item.rule_code in {"mad_tabii", "mad_arid_lissukun"}
            and item.display_grapheme_start >= 5
        ]
        by_code = {item.rule_code: item.modes for item in end_mad}
        self.assertEqual(("wasl",), by_code["mad_tabii"])
        self.assertEqual(("ayah_stop",), by_code["mad_arid_lissukun"])

    def test_multi_mode_render_is_exact_in_both_modes(self):
        text = "الْعَالَمِينَ"
        multi = analyze_tajwid_v3_modes(text, verse_key="1:2")
        self.assertEqual(text, multi.render_for_mode("wasl").reconstruct())
        self.assertEqual(text, multi.render_for_mode("ayah_stop").reconstruct())

    def test_exclusive_ra_conflict_is_resolved_deterministically(self):
        stream = build_token_stream("رَ")
        span = make_text_span(stream, 0, 1)
        common = {
            "trigger_span": span,
            "context_span": span,
            "display_span": span,
            "word_index": 0,
            "next_word_index": None,
            "applies_when": AppliesWhen.BOTH,
            "evidence": {},
            "confidence": 1.0,
            "detector_id": "test",
        }
        annotations = (
            TajwidAnnotationV3(rule_code="ra_tafkhim", **common),
            TajwidAnnotationV3(rule_code="ra_tarqiq", **common),
        )
        kept, issues = resolve_annotation_conflicts(annotations, ())
        self.assertEqual(["ra_tafkhim"], [item.rule_code for item in kept])
        self.assertIn(
            "resolved_mutually_exclusive_rules",
            {item.issue_type for item in issues},
        )
        self.assertEqual((), validate_resolved_annotation_set(kept))

    def test_renderer_rejects_empty_text(self):
        stream = build_token_stream("")
        with self.assertRaises(ValueError):
            from main.utils_tilawah.tajwid_v3.renderer import render_annotations

            render_annotations(stream, (), reading_mode="ayah_stop")

    def test_all_goldset_texts_render_without_loss(self):
        base_dir = Path(__file__).resolve().parents[2]
        dataset = load_gold_dataset(
            base_dir / "main/data/tilawah/tajwid_v3_gold_cases.v1.json"
        )
        self.assertGreaterEqual(len(dataset.cases), 240)
        for case in dataset.cases:
            with self.subTest(case_id=case.case_id):
                result = analyze_tajwid_v3(
                    case.text,
                    reading_mode=case.reading_mode,
                    verse_key=case.verse_key,
                    boundary_to_verse_key=case.boundary_to_verse_key,
                )
                rendered = render_engine_result(result)
                self.assertFalse(result.has_errors, result.to_dict())
                self.assertEqual(case.text, rendered.reconstruct())


if __name__ == "__main__":
    unittest.main()
