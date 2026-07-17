from __future__ import annotations

import unittest
from pathlib import Path

from main.utils_tilawah.tajwid_v3.detectors.mad import SUPPORTED_RULE_CODES
from main.utils_tilawah.tajwid_v3.engine import analyze_tajwid_v3
from main.utils_tilawah.tajwid_v3.evaluation import (
    evaluate_gold_cases,
    relevant_gold_cases,
)
from main.utils_tilawah.tajwid_v3.gold_loader import load_gold_dataset
from main.utils_tilawah.tajwid_v3.specification import AppliesWhen


class MadDetectorV3Tests(unittest.TestCase):
    def annotations_for(self, text: str, reading_mode: str = "wasl"):
        result = analyze_tajwid_v3(text, reading_mode=reading_mode)
        self.assertFalse(result.has_errors, result.to_dict())
        return [
            item for item in result.annotations
            if item.rule_code in SUPPORTED_RULE_CODES
        ]

    def find_rule(self, text: str, rule_code: str, reading_mode: str = "wasl"):
        matches = [
            item for item in self.annotations_for(text, reading_mode)
            if item.rule_code == rule_code
        ]
        self.assertEqual(1, len(matches), (text, [m.to_dict() for m in matches]))
        return matches[0]

    def test_tabii_supports_alif_waw_ya_and_dagger_alif(self):
        examples = {
            "قَالَ": "قَا",
            "يَقُوْلُ": "قُوْ",
            "قِيْلَ": "قِيْ",
            "الرَّحْمَٰنِ": "مَٰ",
            "الرَّحْمَـٰنِ": "مَـٰ",
        }
        for text, trigger in examples.items():
            with self.subTest(text=text):
                item = self.find_rule(text, "mad_tabii")
                self.assertEqual(trigger, item.trigger_span.text)
                self.assertEqual((2,), tuple(item.expected_features["allowed_harakat"]))

    def test_lin_carrier_is_not_mad_tabii(self):
        emitted = {item.rule_code for item in self.annotations_for("خَوْفٌ")}
        self.assertNotIn("mad_tabii", emitted)
        self.assertNotIn("mad_lin", emitted)

    def test_badl_supports_separate_hamza_and_alif_madda(self):
        examples = {"ءَامَنُوا": "ءَا", "إِيمَانًا": "إِي", "آمَنُوا": "آ"}
        for text, trigger in examples.items():
            with self.subTest(text=text):
                item = self.find_rule(text, "mad_badl")
                self.assertEqual(trigger, item.trigger_span.text)
                self.assertLess(item.confidence, 1.0)

    def test_wajib_muttasil_for_alif_waw_and_ya(self):
        examples = {
            "جَاءَ": ("جَا", "جَاءَ"),
            "سُوْءٌ": ("سُوْ", "سُوْءٌ"),
            "جِيْءَ": ("جِيْ", "جِيْءَ"),
        }
        for text, spans in examples.items():
            with self.subTest(text=text):
                item = self.find_rule(text, "mad_wajib_muttasil")
                self.assertEqual(spans[0], item.trigger_span.text)
                self.assertEqual(spans[1], item.context_span.text)

    def test_jaiz_munfasil_and_plural_waw_support_alef(self):
        item = self.find_rule("فِي أَنْفُسِكُمْ", "mad_jaiz_munfasil")
        self.assertEqual("فِي", item.trigger_span.text)
        self.assertEqual("فِي أَ", item.context_span.text)
        self.assertEqual(AppliesWhen.WASL, item.applies_when)

        item = self.find_rule("قَالُوْا آمَنَّا", "mad_jaiz_munfasil")
        self.assertEqual("لُوْ", item.trigger_span.text)
        self.assertEqual("لُوْا آ", item.context_span.text)

    def test_munfasil_is_suppressed_in_explicit_waqf(self):
        emitted = {
            item.rule_code
            for item in self.annotations_for("فِي أَنْفُسِكُمْ", "waqf")
        }
        self.assertNotIn("mad_jaiz_munfasil", emitted)

    def test_hamzat_wasl_is_not_treated_as_munfasil_hamza(self):
        emitted = {
            item.rule_code for item in self.annotations_for("فِي ٱلْبَيْتِ")
        }
        self.assertNotIn("mad_jaiz_munfasil", emitted)

    def test_lazim_kalimi_muthaqqal(self):
        item = self.find_rule("الضَّالِّينَ", "mad_lazim_kalimi_muthaqqal")
        self.assertEqual("ضَّا", item.trigger_span.text)
        self.assertEqual("ضَّالِّ", item.context_span.text)
        self.assertEqual([6], item.expected_features["allowed_harakat"])

    def test_lazim_kalimi_mukhaffaf_is_provisional(self):
        item = self.find_rule("ءَآلْـَٰٔنَ", "mad_lazim_kalimi_mukhaffaf")
        self.assertEqual("ءَآ", item.trigger_span.text)
        self.assertEqual("ءَآلْ", item.context_span.text)
        self.assertLess(item.confidence, 1.0)

    def test_iwad_requires_actual_stop_and_excludes_ta_marbuta(self):
        item = self.find_rule("عَلِيمًا", "mad_iwad", "ayah_stop")
        self.assertEqual("مًا", item.display_span.text)
        self.assertEqual(AppliesWhen.WAQF, item.applies_when)

        emitted = {
            item.rule_code for item in self.annotations_for("عَلِيمًا", "wasl")
        }
        self.assertNotIn("mad_iwad", emitted)
        emitted = {
            item.rule_code for item in self.annotations_for("رَحْمَةً", "ayah_stop")
        }
        self.assertNotIn("mad_iwad", emitted)

    def test_arid_replaces_tabii_at_final_locus_only_during_stop(self):
        item = self.find_rule("الْعَالَمِينَ", "mad_arid_lissukun", "ayah_stop")
        self.assertEqual("مِي", item.trigger_span.text)
        self.assertEqual("مِينَ", item.context_span.text)
        self.assertEqual([2, 4, 6], item.expected_features["allowed_harakat"])

        emitted = self.annotations_for("الْعَالَمِينَ", "wasl")
        pairs = {(item.rule_code, item.trigger_span.text) for item in emitted}
        self.assertIn(("mad_tabii", "مِي"), pairs)
        self.assertNotIn(("mad_arid_lissukun", "مِي"), pairs)

    def test_lin_requires_actual_stop(self):
        item = self.find_rule("خَوْفٍ", "mad_lin", "ayah_stop")
        self.assertEqual("خَوْ", item.trigger_span.text)
        self.assertEqual("خَوْفٍ", item.display_span.text)

        emitted = {
            item.rule_code for item in self.annotations_for("خَوْفٍ", "wasl")
        }
        self.assertNotIn("mad_lin", emitted)

    def test_lazim_and_arid_can_coexist_in_al_fatihah_ending(self):
        annotations = self.annotations_for("الضَّالِّينَ", "ayah_stop")
        emitted = {item.rule_code for item in annotations}
        self.assertIn("mad_lazim_kalimi_muthaqqal", emitted)
        self.assertIn("mad_arid_lissukun", emitted)

    def test_goldset_subset_exact_match(self):
        base_dir = Path(__file__).resolve().parents[2]
        dataset = load_gold_dataset(
            base_dir / "main/data/tilawah/tajwid_v3_gold_cases.v1.json"
        )
        cases = relevant_gold_cases(dataset, SUPPORTED_RULE_CODES)
        report = evaluate_gold_cases(
            cases,
            supported_rule_codes=SUPPORTED_RULE_CODES,
        )
        self.assertGreaterEqual(report.total_cases, 40)
        self.assertTrue(report.success, report.to_dict())


if __name__ == "__main__":
    unittest.main()
