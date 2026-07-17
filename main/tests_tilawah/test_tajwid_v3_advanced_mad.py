from __future__ import annotations

import unittest
from pathlib import Path

from main.utils_tilawah.tajwid_v3.detectors.advanced_mad import SUPPORTED_RULE_CODES
from main.utils_tilawah.tajwid_v3.engine import analyze_tajwid_v3
from main.utils_tilawah.tajwid_v3.evaluation import evaluate_gold_cases, relevant_gold_cases
from main.utils_tilawah.tajwid_v3.gold_loader import load_gold_dataset


class AdvancedMadDetectorV3Tests(unittest.TestCase):
    def annotations_for(self, text: str, *, mode: str = "wasl", verse_key: str | None = None):
        result = analyze_tajwid_v3(text, reading_mode=mode, verse_key=verse_key)
        self.assertFalse(result.has_errors, result.to_dict())
        return [item for item in result.annotations if item.rule_code in SUPPORTED_RULE_CODES]

    def find_one(self, text: str, code: str, *, mode: str = "wasl", verse_key: str | None = None):
        matches = [item for item in self.annotations_for(text, mode=mode, verse_key=verse_key) if item.rule_code == code]
        self.assertEqual(1, len(matches), (text, code, [item.to_dict() for item in matches]))
        return matches[0]

    def test_tamkin_requires_two_ya_pattern(self):
        item = self.find_one("النَّبِيِّينَ", "mad_tamkin")
        self.assertEqual("يِّي", item.trigger_span.text)
        self.assertLess(item.confidence, 1.0)
        emitted = {item.rule_code for item in self.annotations_for("يَدَيْنِ")}
        self.assertNotIn("mad_tamkin", emitted)

    def test_silah_qasirah_candidate(self):
        item = self.find_one("إِنَّهُ كَانَ", "mad_silah_qasirah")
        self.assertEqual("هُ", item.trigger_span.text)
        self.assertEqual("هُ", item.display_span.text)
        self.assertLess(item.confidence, 1.0)

    def test_silah_tawilah_includes_hamza_target(self):
        item = self.find_one("مَالَهُ أَخْلَدَهُ", "mad_silah_tawilah", verse_key="104:3")
        self.assertEqual("هُ", item.trigger_span.text)
        self.assertEqual("هُ أَ", item.context_span.text)
        self.assertEqual("هُ أَ", item.display_span.text)

    def test_silah_excludes_original_ha_and_hafs_exception(self):
        for text, key in (("وَجْهُ رَبِّكَ", None), ("يَرْضَهُ لَكُمْ", "39:7")):
            with self.subTest(text=text):
                emitted = {item.rule_code for item in self.annotations_for(text, verse_key=key)}
                self.assertNotIn("mad_silah_qasirah", emitted)
                self.assertNotIn("mad_silah_tawilah", emitted)

    def test_silah_is_suppressed_at_actual_stop(self):
        emitted = {item.rule_code for item in self.annotations_for("إِنَّهُ", mode="ayah_stop")}
        self.assertNotIn("mad_silah_qasirah", emitted)
        self.assertNotIn("mad_silah_tawilah", emitted)

    def test_muqattaah_alm_classification(self):
        items = self.annotations_for("الٓمٓ", verse_key="2:1")
        pairs = {(item.rule_code, item.trigger_span.text) for item in items}
        self.assertIn(("mad_lazim_harfi_muthaqqal", "لٓ"), pairs)
        self.assertIn(("mad_lazim_harfi_mukhaffaf", "مٓ"), pairs)

    def test_muqattaah_mixed_sequence(self):
        items = self.annotations_for("كٓهيعٓصٓ", verse_key="19:1")
        pairs = {(item.rule_code, item.trigger_span.text) for item in items}
        self.assertIn(("mad_lazim_harfi_mukhaffaf", "كٓ"), pairs)
        self.assertIn(("mad_harfi_tabii", "ه"), pairs)
        self.assertIn(("mad_harfi_tabii", "ي"), pairs)
        self.assertIn(("mad_ayn_muqattaah", "عٓ"), pairs)
        self.assertIn(("mad_lazim_harfi_mukhaffaf", "صٓ"), pairs)

    def test_ordinary_word_is_not_muqattaah(self):
        emitted = {item.rule_code for item in self.annotations_for("طَهُرَ")}
        self.assertFalse(emitted.intersection({
            "mad_harfi_tabii", "mad_lazim_harfi_muthaqqal",
            "mad_lazim_harfi_mukhaffaf", "mad_ayn_muqattaah",
        }))

    def test_farq_requires_verified_verse_registry(self):
        item = self.find_one("ءَآللَّهُ", "mad_farq", verse_key="10:59")
        self.assertEqual("ءَآ", item.trigger_span.text)
        self.assertEqual([6], item.expected_features["allowed_harakat"])
        emitted = {item.rule_code for item in self.annotations_for("ءَآللَّهُ")}
        self.assertNotIn("mad_farq", emitted)

    def test_farq_supersedes_core_mad_at_same_locus(self):
        result = analyze_tajwid_v3("ءَآلْـَٰٔنَ", reading_mode="wasl", verse_key="10:51")
        codes = {item.rule_code for item in result.annotations}
        self.assertIn("mad_farq", codes)
        self.assertNotIn("mad_lazim_kalimi_mukhaffaf", codes)

    def test_goldset_exact_match(self):
        base_dir = Path(__file__).resolve().parents[2]
        dataset = load_gold_dataset(base_dir / "main/data/tilawah/tajwid_v3_gold_cases.v1.json")
        cases = relevant_gold_cases(dataset, SUPPORTED_RULE_CODES)
        report = evaluate_gold_cases(cases, supported_rule_codes=SUPPORTED_RULE_CODES)
        self.assertGreaterEqual(report.total_cases, 25)
        self.assertTrue(report.success, report.to_dict())


if __name__ == "__main__":
    unittest.main()
