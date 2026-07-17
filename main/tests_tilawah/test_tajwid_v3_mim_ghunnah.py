from __future__ import annotations

import unittest
from pathlib import Path

from main.utils_tilawah.tajwid_v3.detectors.ghunnah import (
    SUPPORTED_RULE_CODES as GHUNNAH_RULE_CODES,
)
from main.utils_tilawah.tajwid_v3.detectors.mim_sakinah import (
    SUPPORTED_RULE_CODES as MIM_RULE_CODES,
)
from main.utils_tilawah.tajwid_v3.engine import analyze_tajwid_v3
from main.utils_tilawah.tajwid_v3.evaluation import (
    evaluate_gold_cases,
    relevant_gold_cases,
)
from main.utils_tilawah.tajwid_v3.gold_loader import load_gold_dataset
from main.utils_tilawah.tajwid_v3.specification import AppliesWhen


class MimSakinahAndGhunnahDetectorTests(unittest.TestCase):
    def assert_single_rule(self, text, rule_code, reading_mode="wasl"):
        result = analyze_tajwid_v3(text, reading_mode=reading_mode)
        matches = [item for item in result.annotations if item.rule_code == rule_code]
        self.assertEqual(1, len(matches), result.to_dict())
        self.assertFalse(result.has_errors, result.to_dict())
        return matches[0]

    def test_mim_sakinah_three_way_classification(self):
        examples = {
            "هُمْ فِيهَا": "izhar_shafawi",
            "هُمْ بِهَا": "ikhfa_shafawi",
            "لَهُمْ مَّا": "idgham_mimi",
        }
        for text, rule_code in examples.items():
            with self.subTest(text=text):
                annotation = self.assert_single_rule(text, rule_code)
                self.assertEqual(AppliesWhen.WASL, annotation.applies_when)

    def test_same_word_izhar_applies_in_both_modes(self):
        annotation = self.assert_single_rule("أَمْسَكْنَا", "izhar_shafawi")
        self.assertEqual(AppliesWhen.BOTH, annotation.applies_when)
        self.assertEqual("مْ", annotation.trigger_span.text)
        self.assertEqual("مْسَ", annotation.context_span.text)
        self.assertEqual("مْ", annotation.display_span.text)

    def test_explicit_waqf_suppresses_cross_word_mim_rule(self):
        result = analyze_tajwid_v3("هُمْ بِهَا", reading_mode="waqf")
        emitted = {item.rule_code for item in result.annotations}
        self.assertFalse(MIM_RULE_CODES.intersection(emitted), result.to_dict())

    def test_final_mim_sakinah_without_target_emits_nothing(self):
        result = analyze_tajwid_v3("عَلَيْهِمْ", reading_mode="ayah_stop")
        emitted = {item.rule_code for item in result.annotations}
        self.assertFalse(MIM_RULE_CODES.intersection(emitted), result.to_dict())

    def test_ghunnah_detects_nun_and_mim_mushaddadah(self):
        for text, trigger in (("إِنَّا", "نَّ"), ("ثُمَّ", "مَّ")):
            with self.subTest(text=text):
                annotation = self.assert_single_rule(
                    text,
                    "ghunnah_mushaddadah",
                    reading_mode="ayah_stop",
                )
                self.assertEqual(trigger, annotation.trigger_span.text)
                self.assertEqual(trigger, annotation.display_span.text)
                self.assertEqual(AppliesWhen.BOTH, annotation.applies_when)
                self.assertEqual(2, annotation.expected_features["nominal_harakat"])

    def test_ghunnah_requires_explicit_shadda(self):
        for text in ("إِنَا", "ثُمَا"):
            with self.subTest(text=text):
                result = analyze_tajwid_v3(text, reading_mode="wasl")
                emitted = {item.rule_code for item in result.annotations}
                self.assertNotIn("ghunnah_mushaddadah", emitted, result.to_dict())

    def test_idgham_mimi_and_ghunnah_can_coexist(self):
        result = analyze_tajwid_v3("لَهُمْ مَّا", reading_mode="wasl")
        emitted = {item.rule_code for item in result.annotations}
        self.assertIn("idgham_mimi", emitted, result.to_dict())
        self.assertIn("ghunnah_mushaddadah", emitted, result.to_dict())
        self.assertFalse(result.has_errors, result.to_dict())

    def test_hamzat_wasl_is_deferred_not_guessed(self):
        result = analyze_tajwid_v3("هُمْ ٱلْفَائِزُونَ", reading_mode="wasl")
        emitted = {item.rule_code for item in result.annotations}
        self.assertFalse(MIM_RULE_CODES.intersection(emitted), result.to_dict())
        self.assertTrue(
            any(issue.issue_type == "hamzat_wasl_target_deferred" for issue in result.issues),
            result.to_dict(),
        )

    def test_goldset_subset_exact_match(self):
        base_dir = Path(__file__).resolve().parents[2]
        dataset = load_gold_dataset(
            base_dir / "main/data/tilawah/tajwid_v3_gold_cases.v1.json"
        )
        cases = relevant_gold_cases(
            dataset,
            MIM_RULE_CODES | GHUNNAH_RULE_CODES,
        )
        report = evaluate_gold_cases(cases)
        self.assertGreaterEqual(report.total_cases, 20)
        self.assertTrue(report.success, report.to_dict())


if __name__ == "__main__":
    unittest.main()
