from __future__ import annotations

import unittest
from pathlib import Path

from main.utils_tilawah.tajwid_v3.detectors.qalqalah import (
    QALQALAH_LETTERS,
    SUPPORTED_RULE_CODES,
)
from main.utils_tilawah.tajwid_v3.engine import analyze_tajwid_v3
from main.utils_tilawah.tajwid_v3.evaluation import (
    evaluate_gold_cases,
    relevant_gold_cases,
)
from main.utils_tilawah.tajwid_v3.gold_loader import load_gold_dataset
from main.utils_tilawah.tajwid_v3.specification import AppliesWhen


class QalqalahDetectorTests(unittest.TestCase):
    def annotations_for(self, text: str, reading_mode: str = "wasl"):
        result = analyze_tajwid_v3(text, reading_mode=reading_mode)
        self.assertFalse(result.has_errors, result.to_dict())
        return [
            item for item in result.annotations
            if item.rule_code in SUPPORTED_RULE_CODES
        ]

    def assert_single_rule(self, text, rule_code, reading_mode="wasl"):
        matches = [
            item for item in self.annotations_for(text, reading_mode)
            if item.rule_code == rule_code
        ]
        self.assertEqual(1, len(matches), (text, [m.to_dict() for m in matches]))
        return matches[0]

    def test_qalqalah_letter_inventory(self):
        self.assertEqual({"ق", "ط", "ب", "ج", "د"}, set(QALQALAH_LETTERS))

    def test_sughra_detects_all_five_letters_with_explicit_sukun(self):
        examples = {
            "يَقْطَعُونَ": "قْ",
            "أَطْعَمَ": "طْ",
            "أَبْتَرُ": "بْ",
            "يَجْعَلُ": "جْ",
            "قَدْ أَفْلَحَ": "دْ",
        }
        for text, trigger in examples.items():
            with self.subTest(text=text):
                annotation = self.assert_single_rule(text, "qalqalah_sughra")
                self.assertEqual(trigger, annotation.trigger_span.text)
                self.assertEqual(trigger, annotation.display_span.text)
                self.assertEqual(AppliesWhen.BOTH, annotation.applies_when)
                self.assertEqual(
                    "light",
                    annotation.expected_features["release_strength"],
                )

    def test_moving_qalqalah_letter_has_no_sughra(self):
        annotations = self.annotations_for("قَالَ", "wasl")
        self.assertFalse(annotations)

    def test_kubra_is_emitted_at_ayah_stop(self):
        annotation = self.assert_single_rule(
            "الْفَلَقِ",
            "qalqalah_kubra",
            reading_mode="ayah_stop",
        )
        self.assertEqual("قِ", annotation.trigger_span.text)
        self.assertEqual(AppliesWhen.WAQF, annotation.applies_when)
        self.assertEqual("strong", annotation.expected_features["release_strength"])
        self.assertEqual(
            "acquired_sukun_by_waqf",
            annotation.evidence["stop_origin"],
        )

    def test_kubra_is_not_emitted_during_wasl(self):
        annotations = self.annotations_for("الْفَلَقِ", "wasl")
        self.assertFalse(
            any(item.rule_code == "qalqalah_kubra" for item in annotations)
        )

    def test_original_sukun_at_final_stop_becomes_kubra_not_sughra(self):
        annotations = self.annotations_for("أَحَدْ", "ayah_stop")
        emitted = {item.rule_code for item in annotations}
        self.assertEqual({"qalqalah_kubra"}, emitted)
        annotation = annotations[0]
        self.assertEqual("original_sukun_at_waqf", annotation.evidence["stop_origin"])

    def test_akbar_requires_final_shadda_and_actual_stop(self):
        annotation = self.assert_single_rule(
            "الْحَقُّ",
            "qalqalah_akbar",
            reading_mode="waqf",
        )
        self.assertEqual("قُّ", annotation.trigger_span.text)
        self.assertEqual(AppliesWhen.WAQF, annotation.applies_when)
        self.assertEqual(
            "strongest",
            annotation.expected_features["release_strength"],
        )
        self.assertLess(annotation.confidence, 1.0)

        annotations = self.annotations_for("الْحَقُّ", "wasl")
        self.assertFalse(
            any(item.rule_code == "qalqalah_akbar" for item in annotations)
        )

    def test_internal_mushaddad_is_conservatively_not_coloured(self):
        annotations = self.annotations_for("حَقَّقَ", "wasl")
        self.assertFalse(annotations)

    def test_sughra_and_kubra_can_coexist_in_one_ayah(self):
        annotations = self.annotations_for(
            "يَقْطَعُ الْفَلَقِ",
            "ayah_stop",
        )
        pairs = {(item.rule_code, item.trigger_span.text) for item in annotations}
        self.assertIn(("qalqalah_sughra", "قْ"), pairs)
        self.assertIn(("qalqalah_kubra", "قِ"), pairs)

    def test_non_qalqalah_final_letter_has_no_stop_rule(self):
        annotations = self.annotations_for("الْعَالَمِينَ", "ayah_stop")
        self.assertFalse(annotations)

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
