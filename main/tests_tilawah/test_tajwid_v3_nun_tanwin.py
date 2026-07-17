from __future__ import annotations

import unittest
from pathlib import Path

from main.utils_tilawah.tajwid_v3.detectors.nun_tanwin import (
    SUPPORTED_RULE_CODES,
)
from main.utils_tilawah.tajwid_v3.engine import analyze_tajwid_v3
from main.utils_tilawah.tajwid_v3.evaluation import (
    evaluate_gold_cases,
    relevant_gold_cases,
)
from main.utils_tilawah.tajwid_v3.gold_loader import load_gold_dataset
from main.utils_tilawah.tajwid_v3.specification import AppliesWhen


class NunTanwinDetectorTests(unittest.TestCase):
    def assert_single_rule(self, text, rule_code, applies_when=None):
        result = analyze_tajwid_v3(text, reading_mode="wasl")
        matches = [item for item in result.annotations if item.rule_code == rule_code]
        self.assertEqual(1, len(matches), result.to_dict())
        if applies_when is not None:
            self.assertEqual(applies_when, matches[0].applies_when)
        self.assertFalse(result.has_errors, result.to_dict())
        return matches[0]

    def test_cross_word_nun_sakinah_rules(self):
        examples = {
            "مِنْ هَادٍ": "izhar_halqi",
            "مِنْ مَالٍ": "idgham_bighunnah",
            "مِنْ رَبِّهِمْ": "idgham_bilaghunnah",
            "مِنْ بَعْدِ": "iqlab",
            "مِنْ شَرِّ": "ikhfa_haqiqi",
        }
        for text, rule in examples.items():
            with self.subTest(text=text):
                self.assert_single_rule(text, rule, AppliesWhen.WASL)

    def test_tanwin_rules(self):
        examples = {
            "عَلِيمٌ حَكِيمٌ": "izhar_halqi",
            "خَيْرًا يَرَهُ": "idgham_bighunnah",
            "غَفُورٌ رَحِيمٌ": "idgham_bilaghunnah",
            "سَمِيعٌۢ بَصِيرٌ": "iqlab",
            "قَوْلًا سَدِيدًا": "ikhfa_haqiqi",
        }
        for text, rule in examples.items():
            with self.subTest(text=text):
                self.assert_single_rule(text, rule, AppliesWhen.WASL)

    def test_same_word_rules_apply_in_both_modes(self):
        examples = {
            "يَنْهَوْنَ": "izhar_halqi",
            "أَنْفُسَكُمْ": "ikhfa_haqiqi",
            "أَنْبِئْهُمْ": "iqlab",
            "الدُّنْيَا": "izhar_mutlaq",
            "وَالدُّنْيَا": "izhar_mutlaq",
        }
        for text, rule in examples.items():
            with self.subTest(text=text):
                self.assert_single_rule(text, rule, AppliesWhen.BOTH)

    def test_final_tanwin_does_not_emit_cross_word_rule(self):
        result = analyze_tajwid_v3("عَلِيمٌ", reading_mode="ayah_stop")
        self.assertFalse(
            SUPPORTED_RULE_CODES.intersection(
                item.rule_code for item in result.annotations
            )
        )

    def test_exact_span_includes_trigger_separator_and_target(self):
        annotation = self.assert_single_rule("مِنْ شَرِّ", "ikhfa_haqiqi")
        self.assertEqual("نْ", annotation.trigger_span.text)
        self.assertEqual("نْ شَ", annotation.context_span.text)
        self.assertEqual("نْ شَ", annotation.display_span.text)

    def test_goldset_subset_exact_match(self):
        base_dir = Path(__file__).resolve().parents[2]
        dataset = load_gold_dataset(
            base_dir / "main/data/tilawah/tajwid_v3_gold_cases.v1.json"
        )
        cases = relevant_gold_cases(dataset, SUPPORTED_RULE_CODES)
        report = evaluate_gold_cases(cases)
        self.assertGreaterEqual(report.total_cases, 20)
        self.assertTrue(report.success, report.to_dict())


if __name__ == "__main__":
    unittest.main()
