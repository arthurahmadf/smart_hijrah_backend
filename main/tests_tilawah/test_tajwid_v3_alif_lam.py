from __future__ import annotations

import unittest
from pathlib import Path

from main.utils_tilawah.tajwid_v3.detectors.alif_lam import SUPPORTED_RULE_CODES
from main.utils_tilawah.tajwid_v3.engine import analyze_tajwid_v3
from main.utils_tilawah.tajwid_v3.evaluation import evaluate_gold_cases, relevant_gold_cases
from main.utils_tilawah.tajwid_v3.gold_loader import load_gold_dataset


class AlifLamDetectorV3Tests(unittest.TestCase):
    def annotations_for(self, text: str, *, mode: str = "wasl"):
        result = analyze_tajwid_v3(text, reading_mode=mode)
        self.assertFalse(result.has_errors, result.to_dict())
        return [item for item in result.annotations if item.rule_code in SUPPORTED_RULE_CODES]

    def find_one(self, text: str, code: str, *, mode: str = "wasl"):
        matches = [item for item in self.annotations_for(text, mode=mode) if item.rule_code == code]
        self.assertEqual(1, len(matches), (text, code, [item.to_dict() for item in matches]))
        return matches[0]

    def test_qamariyyah_exact_span(self):
        item = self.find_one("ٱلْقَمَرُ", "alif_lam_qamariyyah")
        self.assertEqual("ٱلْقَ", item.trigger_span.text)
        self.assertEqual(item.trigger_span, item.context_span)
        self.assertEqual(item.trigger_span, item.display_span)

    def test_shamsiyyah_exact_span(self):
        item = self.find_one("ٱلشَّمْسُ", "alif_lam_shamsiyyah")
        self.assertEqual("ٱلشَّ", item.display_span.text)
        self.assertTrue(item.evidence["target_has_shadda"])

    def test_attached_prefixes_are_not_colored_as_article(self):
        qam = self.find_one("وَالْكِتَابِ", "alif_lam_qamariyyah")
        shams = self.find_one("فَالصَّافَّاتِ", "alif_lam_shamsiyyah")
        self.assertEqual("الْكِ", qam.display_span.text)
        self.assertEqual("الصَّ", shams.display_span.text)

    def test_contracted_li_l_article(self):
        qam = self.find_one("لِلْمُتَّقِينَ", "alif_lam_qamariyyah")
        shams = self.find_one("لِلنَّاسِ", "alif_lam_shamsiyyah")
        self.assertEqual("لْمُ", qam.display_span.text)
        self.assertEqual("لنَّ", shams.display_span.text)
        self.assertTrue(qam.evidence["contracted_li_l_article"])

    def test_hamzated_root_is_not_definite_article(self):
        codes = {item.rule_code for item in self.annotations_for("أَلْهَاكُمُ")}
        self.assertNotIn("alif_lam_qamariyyah", codes)
        self.assertNotIn("alif_lam_shamsiyyah", codes)

    def test_lafz_allah_is_not_alif_lam_rule(self):
        items = self.annotations_for("ٱللَّهُ")
        codes = {item.rule_code for item in items}
        self.assertIn("lam_jalalah_tafkhim", codes)
        self.assertNotIn("alif_lam_qamariyyah", codes)
        self.assertNotIn("alif_lam_shamsiyyah", codes)

    def test_lam_jalalah_tafkhim_after_fatha_and_damma(self):
        for text in ("قَالَ ٱللَّهُ", "عَبْدُ ٱللَّهِ", "وَاللَّهُ"):
            with self.subTest(text=text):
                item = self.find_one(text, "lam_jalalah_tafkhim")
                self.assertEqual("لَّ", item.trigger_span.text)
                self.assertEqual("emphatic", item.expected_features["resonance"])

    def test_lam_jalalah_tafkhim_at_ibtida(self):
        item = self.find_one("ٱللَّهُ", "lam_jalalah_tafkhim")
        self.assertEqual("ibtida_default_tafkhim", item.evidence["vowel_resolution"])

    def test_lam_jalalah_tarqiq_after_kasra(self):
        for text in ("بِسْمِ ٱللَّهِ", "بِاللَّهِ", "لِلَّهِ"):
            with self.subTest(text=text):
                item = self.find_one(text, "lam_jalalah_tarqiq")
                self.assertEqual("kasra", item.evidence["preceding_vowel"])
                self.assertEqual("light", item.expected_features["resonance"])

    def test_lam_jalalah_resolves_long_ya_vowel(self):
        item = self.find_one("فِي ٱللَّهِ", "lam_jalalah_tarqiq")
        self.assertEqual("long_vowel_carrier", item.evidence["vowel_resolution"])

    def test_shamsiyyah_without_shadda_is_provisional_warning(self):
        result = analyze_tajwid_v3("الشَمْسُ", reading_mode="wasl")
        items = [item for item in result.annotations if item.rule_code == "alif_lam_shamsiyyah"]
        self.assertEqual(1, len(items))
        self.assertLess(items[0].confidence, 1.0)
        self.assertIn("shamsiyyah_target_without_shadda", {item.issue_type for item in result.issues})

    def test_goldset_exact_match(self):
        base_dir = Path(__file__).resolve().parents[2]
        dataset = load_gold_dataset(base_dir / "main/data/tilawah/tajwid_v3_gold_cases.v1.json")
        cases = relevant_gold_cases(dataset, SUPPORTED_RULE_CODES)
        report = evaluate_gold_cases(cases, supported_rule_codes=SUPPORTED_RULE_CODES)
        self.assertGreaterEqual(report.total_cases, 30)
        self.assertTrue(report.success, report.to_dict())


if __name__ == "__main__":
    unittest.main()
