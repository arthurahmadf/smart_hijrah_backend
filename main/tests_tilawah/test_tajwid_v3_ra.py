from __future__ import annotations

import unittest
from pathlib import Path

from main.utils_tilawah.tajwid_v3.detectors.ra import SUPPORTED_RULE_CODES
from main.utils_tilawah.tajwid_v3.engine import analyze_tajwid_v3
from main.utils_tilawah.tajwid_v3.evaluation import evaluate_gold_cases, relevant_gold_cases
from main.utils_tilawah.tajwid_v3.gold_loader import load_gold_dataset


class RaDetectorV3Tests(unittest.TestCase):
    def annotations_for(self, text: str, *, mode: str = "wasl", verse_key: str | None = None):
        result = analyze_tajwid_v3(text, reading_mode=mode, verse_key=verse_key)
        self.assertFalse(result.has_errors, result.to_dict())
        return [item for item in result.annotations if item.rule_code in SUPPORTED_RULE_CODES]

    def find_one(self, text: str, code: str, *, mode: str = "wasl", verse_key: str | None = None):
        matches = [
            item for item in self.annotations_for(text, mode=mode, verse_key=verse_key)
            if item.rule_code == code
        ]
        self.assertEqual(1, len(matches), (text, code, [item.to_dict() for item in matches]))
        return matches[0]

    def test_direct_vowels(self):
        self.assertEqual("رَ", self.find_one("رَبِّ", "ra_tafkhim").trigger_span.text)
        self.assertEqual("رُ", self.find_one("رُسُلٌ", "ra_tafkhim").trigger_span.text)
        self.assertEqual("رِ", self.find_one("رِزْقًا", "ra_tarqiq").trigger_span.text)

    def test_shadda_uses_its_own_vowel(self):
        self.assertEqual("ra_tafkhim", self.find_one("مَرَّ", "ra_tafkhim").rule_code)
        self.assertEqual("ra_tarqiq", self.find_one("مَرِّ", "ra_tarqiq").rule_code)

    def test_ra_sakin_after_fatha_and_damma_is_tafkhim(self):
        self.assertEqual("مَرْ", self.find_one("مَرْيَمَ", "ra_tafkhim").context_span.text)
        self.assertEqual("قُرْ", self.find_one("قُرْآنٌ", "ra_tafkhim").context_span.text)

    def test_ra_sakin_after_original_kasra_is_tarqiq(self):
        item = self.find_one("مِرْيَةٍ", "ra_tarqiq")
        self.assertEqual("مِرْ", item.context_span.text)
        self.assertEqual("light", item.expected_features["resonance"])

    def test_istila_after_ra_overrides_kasra(self):
        item = self.find_one("مِرْصَادًا", "ra_tafkhim")
        self.assertEqual("مِرْصَ", item.context_span.text)
        self.assertEqual("ص", item.evidence["following_istila_letter"])

    def test_temporary_kasra_from_hamzat_wasl_is_tafkhim(self):
        item = self.find_one("ٱرْجِعُوا", "ra_tafkhim")
        self.assertEqual("ٱرْ", item.context_span.text)
        self.assertEqual("temporary", item.evidence["kasra_type"])
        self.assertLess(item.confidence, 1.0)

    def test_waqf_after_ya_is_tarqiq(self):
        self.assertEqual("بِيرٍ", self.find_one("خَبِيرٍ", "ra_tarqiq", mode="ayah_stop").context_span.text)
        self.assertEqual("يْرٍ", self.find_one("خَيْرٍ", "ra_tarqiq", mode="ayah_stop").context_span.text)

    def test_waqf_after_sakin_uses_vowel_before_it(self):
        self.assertEqual("ra_tarqiq", self.find_one("سِحْرٌ", "ra_tarqiq", mode="ayah_stop").rule_code)
        self.assertEqual("ra_tafkhim", self.find_one("نَهْرٌ", "ra_tafkhim", mode="ayah_stop").rule_code)

    def test_firq_allows_both_in_wasl_but_tafkhim_in_waqf(self):
        both = self.find_one(
            "فِرْقٍ فَكَانَ",
            "ra_both_permitted",
            mode="ayah_stop",
            verse_key="26:63",
        )
        self.assertEqual(["tafkhim", "tarqiq"], both.evidence["allowed_faces"])
        stopped = self.find_one("فِرْقٍ", "ra_tafkhim", mode="waqf", verse_key="26:63")
        self.assertEqual("profile_lexical_exception_firq_waqf", stopped.evidence["decision_reason"])

    def test_misr_and_qitr_allow_both_only_at_registered_waqf(self):
        misr = self.find_one("مِصْرَ", "ra_both_permitted", mode="waqf", verse_key="12:21")
        qitr = self.find_one("الْقِطْرِ", "ra_both_permitted", mode="waqf", verse_key="34:12")
        self.assertEqual("profile_dependent", misr.applies_when.value)
        self.assertEqual("profile_dependent", qitr.applies_when.value)
        wasl = self.find_one("مِصْرَ كَانَ", "ra_tafkhim", mode="wasl", verse_key="12:21")
        self.assertEqual("ra_with_fatha_or_damma", wasl.evidence["decision_reason"])

    def test_non_ra_text_emits_no_ra_rule(self):
        items = self.annotations_for("قَالَ")
        self.assertEqual([], items)

    def test_goldset_exact_match(self):
        base_dir = Path(__file__).resolve().parents[2]
        dataset = load_gold_dataset(base_dir / "main/data/tilawah/tajwid_v3_gold_cases.v1.json")
        cases = relevant_gold_cases(dataset, SUPPORTED_RULE_CODES)
        report = evaluate_gold_cases(cases, supported_rule_codes=SUPPORTED_RULE_CODES)
        self.assertGreaterEqual(report.total_cases, 25)
        self.assertTrue(report.success, report.to_dict())


if __name__ == "__main__":
    unittest.main()
