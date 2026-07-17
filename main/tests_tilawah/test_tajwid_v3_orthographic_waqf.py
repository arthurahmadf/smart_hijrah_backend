from __future__ import annotations

import unittest
from pathlib import Path

from main.utils_tilawah.tajwid_v3.detectors.orthographic_waqf import (
    OrthographicWaqfDetector,
    SUPPORTED_RULE_CODES,
)
from main.utils_tilawah.tajwid_v3.engine import analyze_tajwid_v3
from main.utils_tilawah.tajwid_v3.evaluation import evaluate_gold_cases, relevant_gold_cases
from main.utils_tilawah.tajwid_v3.gold_loader import load_gold_dataset


class OrthographicWaqfDetectorV3Tests(unittest.TestCase):
    def result_for(
        self,
        text: str,
        *,
        mode: str = "wasl",
        verse_key: str | None = None,
        boundary_to_verse_key: str | None = None,
        isolated: bool = True,
    ):
        detector = OrthographicWaqfDetector(
            verse_key=verse_key,
            boundary_to_verse_key=boundary_to_verse_key,
        )
        result = analyze_tajwid_v3(
            text,
            reading_mode=mode,
            detectors=(detector,) if isolated else None,
            verse_key=verse_key,
            boundary_to_verse_key=boundary_to_verse_key,
        )
        self.assertFalse(result.has_errors, result.to_dict())
        return result

    def find_one(self, text: str, code: str, **kwargs):
        result = self.result_for(text, **kwargs)
        matches = [item for item in result.annotations if item.rule_code == code]
        self.assertEqual(1, len(matches), result.to_dict())
        return matches[0]

    def test_hamzat_wasl_at_ibtida_article_uses_fatha(self):
        item = self.find_one("ٱلْحَمْدُ", "hamzat_wasl")
        self.assertEqual("ٱ", item.display_span.text)
        self.assertEqual("pronounced_at_ibtida", item.expected_features["pronunciation_status"])
        self.assertEqual("fatha", item.expected_features["initial_vowel"])

    def test_hamzat_wasl_in_connected_reading_is_dropped(self):
        item = self.find_one("قَالَ ٱللَّهُ", "hamzat_wasl")
        self.assertEqual("dropped_in_wasl", item.expected_features["pronunciation_status"])
        self.assertIsNone(item.expected_features["initial_vowel"])

    def test_hamzat_wasl_noun_and_verb_start_vowels(self):
        samples = (
            ("ٱسْمُ", "kasra"),
            ("ٱدْخُلُوا", "damma"),
            ("ٱهْدِنَا", "kasra"),
        )
        for text, expected in samples:
            with self.subTest(text=text):
                item = self.find_one(text, "hamzat_wasl")
                self.assertEqual(expected, item.expected_features["initial_vowel"])

    def test_explicit_hamzah_is_not_hamzat_wasl(self):
        result = self.result_for("أَحْمَدُ")
        self.assertNotIn("hamzat_wasl", {item.rule_code for item in result.annotations})

    def test_rounded_zero_is_always_silent(self):
        item = self.find_one("قَالُوا۟", "silent_letter")
        self.assertEqual("ا۟", item.display_span.text)
        self.assertEqual("both", item.expected_features["silent_when"])

    def test_rectangular_zero_is_silent_only_in_wasl(self):
        item = self.find_one("أَنَا۠", "silent_letter", mode="wasl")
        self.assertEqual("wasl", item.expected_features["silent_when"])
        stopped = self.result_for("أَنَا۠", mode="ayah_stop")
        self.assertNotIn("silent_letter", {a.rule_code for a in stopped.annotations})

    def test_mandatory_saktah_cross_ayah_exact_span(self):
        item = self.find_one(
            "عِوَجَاۜ قَيِّمًا",
            "saktah_wajibah",
            verse_key="18:1",
            boundary_to_verse_key="18:2",
        )
        self.assertEqual("اۜ", item.trigger_span.text)
        self.assertEqual("جَاۜ قَ", item.context_span.text)
        self.assertEqual("اۜ", item.display_span.text)

    def test_mandatory_saktah_suppresses_cross_boundary_idgham(self):
        for text, key, forbidden in (
            ("مَنْۜ رَاقٍ", "75:27", "idgham_bilaghunnah"),
            ("بَلْۜ رَانَ", "83:14", "idgham_mutaqaribain"),
        ):
            with self.subTest(text=text):
                result = self.result_for(
                    text,
                    verse_key=key,
                    isolated=False,
                )
                codes = {item.rule_code for item in result.annotations}
                self.assertIn("saktah_wajibah", codes)
                self.assertNotIn(forbidden, codes)

    def test_cross_ayah_saktah_not_active_in_ayah_stop_mode(self):
        result = self.result_for(
            "عِوَجَاۜ قَيِّمًا",
            mode="ayah_stop",
            verse_key="18:1",
            boundary_to_verse_key="18:2",
        )
        self.assertNotIn("saktah_wajibah", {item.rule_code for item in result.annotations})

    def test_optional_haa_saktah_has_two_faces_and_no_deferred_warning(self):
        result = self.result_for(
            "مَالِيَهْۜ هَلَكَ",
            verse_key="69:28",
            boundary_to_verse_key="69:29",
            isolated=False,
        )
        item = next(a for a in result.annotations if a.rule_code == "saktah_jaizah")
        self.assertEqual(
            ["saktah", "connected_alternative"],
            item.expected_features["allowed_faces"],
        )
        self.assertNotIn(
            "haa_sakt_idgham_deferred",
            {issue.issue_type for issue in result.issues},
        )

    def test_optional_anfaal_tawbah_boundary_uses_last_word(self):
        item = self.find_one(
            "عَلِيمٌۜ بَرَاءَةٌ",
            "saktah_jaizah",
            verse_key="8:75",
            boundary_to_verse_key="9:1",
        )
        self.assertEqual("مٌۜ", item.trigger_span.text)
        self.assertEqual("مٌۜ بَ", item.context_span.text)

    def test_unregistered_saktah_mark_warns_without_false_rule(self):
        result = self.result_for("كِتَابٌۜ جَدِيدٌ")
        self.assertNotIn(
            "saktah_wajibah",
            {item.rule_code for item in result.annotations},
        )
        self.assertIn(
            "unregistered_saktah_mark",
            {issue.issue_type for issue in result.issues},
        )

    def test_waqf_sign_hints_are_metadata_not_rule_codes(self):
        result = self.result_for("عَلِيمٌۖ حَكِيمٌۚ")
        kinds = {item.kind.value for item in result.waqf_hints}
        self.assertIn("continue_preferred", kinds)
        self.assertIn("permissible_stop", kinds)
        codes = {item.rule_code for item in result.annotations}
        self.assertFalse(codes.intersection({"continue_preferred", "permissible_stop"}))

    def test_goldset_exact_match(self):
        base_dir = Path(__file__).resolve().parents[2]
        dataset = load_gold_dataset(
            base_dir / "main/data/tilawah/tajwid_v3_gold_cases.v1.json"
        )
        cases = relevant_gold_cases(dataset, SUPPORTED_RULE_CODES)
        report = evaluate_gold_cases(
            cases,
            supported_rule_codes=SUPPORTED_RULE_CODES,
        )
        self.assertGreaterEqual(report.total_cases, 25)
        self.assertTrue(report.success, report.to_dict())


if __name__ == "__main__":
    unittest.main()
