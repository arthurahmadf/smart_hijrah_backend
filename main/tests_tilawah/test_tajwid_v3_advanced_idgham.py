from __future__ import annotations

import unittest
from pathlib import Path

from main.utils_tilawah.tajwid_v3.detectors.advanced_idgham import (
    AdvancedIdghamDetector,
    SUPPORTED_RULE_CODES,
)
from main.utils_tilawah.tajwid_v3.engine import analyze_tajwid_v3
from main.utils_tilawah.tajwid_v3.evaluation import evaluate_gold_cases, relevant_gold_cases
from main.utils_tilawah.tajwid_v3.gold_loader import load_gold_dataset


class AdvancedIdghamDetectorV3Tests(unittest.TestCase):
    def annotations_for(
        self,
        text: str,
        *,
        mode: str = "wasl",
        verse_key: str | None = None,
    ):
        result = analyze_tajwid_v3(
            text,
            reading_mode=mode,
            detectors=(AdvancedIdghamDetector(verse_key=verse_key),),
            verse_key=verse_key,
        )
        self.assertFalse(result.has_errors, result.to_dict())
        return list(result.annotations), list(result.issues)

    def find_one(
        self,
        text: str,
        code: str,
        *,
        mode: str = "wasl",
        verse_key: str | None = None,
    ):
        annotations, _ = self.annotations_for(
            text,
            mode=mode,
            verse_key=verse_key,
        )
        matches = [item for item in annotations if item.rule_code == code]
        self.assertEqual(
            1,
            len(matches),
            (text, code, [item.to_dict() for item in annotations]),
        )
        return matches[0]

    def test_mutamathilain_cross_word_exact_span(self):
        item = self.find_one("قُلْ لَّكُمْ", "idgham_mutamathilain")
        self.assertEqual("لْ", item.trigger_span.text)
        self.assertEqual("لْ لَّ", item.context_span.text)
        self.assertEqual("لْ لَّ", item.display_span.text)
        self.assertEqual(1, item.next_word_index)

    def test_mutamathilain_same_word(self):
        item = self.find_one("مَنَاسِكْكُّمْ", "idgham_mutamathilain")
        self.assertEqual("كْكُّ", item.display_span.text)
        self.assertEqual("both", item.applies_when.value)
        self.assertIsNone(item.next_word_index)

    def test_madd_waw_and_ya_are_not_swallowed(self):
        for text in ("قُوْ وُعِدَ", "قِيْ يَقِينًا"):
            annotations, _ = self.annotations_for(text)
            self.assertNotIn(
                "idgham_mutamathilain",
                {item.rule_code for item in annotations},
            )

    def test_mim_and_nun_identical_pairs_are_left_to_specialised_detectors(self):
        for text in ("هُمْ مُّؤْمِنُونَ", "مِنْ نِّعْمَةٍ"):
            annotations, _ = self.annotations_for(text)
            self.assertEqual([], annotations)

    def test_mutajanisain_exact_pair_table(self):
        samples = (
            ("قَدْ تَّبَيَّنَ", "دْ تَّ"),
            ("أُجِيبَتْ دَّعْوَتُكُمَا", "تْ دَّ"),
            ("هَمَّتْ طَّائِفَةٌ", "تْ طَّ"),
            ("يَلْهَثْ ذَّلِكَ", "ثْ ذَّ"),
            ("إِذْ ظَّلَمُوا", "ذْ ظَّ"),
            ("ارْكَبْ مَّعَنَا", "بْ مَّ"),
        )
        for text, display in samples:
            with self.subTest(text=text):
                item = self.find_one(text, "idgham_mutajanisain")
                self.assertEqual(display, item.display_span.text)

    def test_ta_into_ta_emphatic_is_incomplete(self):
        item = self.find_one(
            "بَسَطْتَ",
            "idgham_mutajanisain",
            verse_key="5:28",
        )
        self.assertEqual("incomplete", item.evidence["assimilation_completeness"])
        self.assertEqual("itbaq_istila", item.expected_features["retained_feature"])

    def test_ba_into_mim_carries_nasalisation_metadata(self):
        item = self.find_one(
            "ارْكَبْ مَّعَنَا",
            "idgham_mutajanisain",
            verse_key="11:42",
        )
        self.assertTrue(item.expected_features["nasalization"])
        self.assertEqual(2, item.expected_features["nominal_harakat"])

    def test_mutaqaribain_lam_ra(self):
        item = self.find_one("وَقُلْ رَّبِّ", "idgham_mutaqaribain")
        self.assertEqual("لْ رَّ", item.display_span.text)
        self.assertEqual(["ل", "ر"], item.evidence["pair"])

    def test_qaf_kaf_preserves_two_acoustic_faces(self):
        item = self.find_one(
            "نَخْلُقْكُّمْ",
            "idgham_mutaqaribain",
            verse_key="77:20",
        )
        self.assertEqual("قْكُّ", item.display_span.text)
        self.assertEqual(
            ["complete", "incomplete"],
            item.expected_features["allowed_assimilation_faces"],
        )
        self.assertEqual("complete", item.expected_features["preferred_face"])
        self.assertLess(item.confidence, 1.0)

    def test_non_whitelisted_pairs_do_not_emit(self):
        for text in ("قَدْ ذَهَبَ", "قُلْ نَعَمْ", "مِنْ خَيْرٍ"):
            annotations, _ = self.annotations_for(text)
            self.assertEqual([], annotations)

    def test_cross_word_pair_does_not_apply_in_explicit_waqf_mode(self):
        for text in ("قُلْ لَّكُمْ", "قَدْ تَّبَيَّنَ", "قُلْ رَّبِّ"):
            annotations, _ = self.annotations_for(text, mode="waqf")
            self.assertEqual([], annotations)

    def test_haa_sakt_boundary_is_deferred(self):
        annotations, issues = self.annotations_for(
            "مَالِيَهْ هَلَكَ",
            verse_key="69:28",
        )
        self.assertEqual([], annotations)
        self.assertIn("haa_sakt_idgham_deferred", {item.issue_type for item in issues})


    def test_full_engine_suppresses_qalqalah_on_assimilated_trigger(self):
        samples = (
            ("قَدْ تَّبَيَّنَ", "idgham_mutajanisain"),
            ("ارْكَبْ مَّعَنَا", "idgham_mutajanisain"),
            ("نَخْلُقْكُّمْ", "idgham_mutaqaribain"),
        )
        for text, expected_code in samples:
            with self.subTest(text=text):
                result = analyze_tajwid_v3(
                    text,
                    reading_mode="wasl",
                    verse_key="77:20" if "نَخْلُق" in text else None,
                )
                codes = {item.rule_code for item in result.annotations}
                self.assertIn(expected_code, codes)
                self.assertNotIn("qalqalah_sughra", codes)

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
        self.assertGreaterEqual(report.total_cases, 23)
        self.assertTrue(report.success, report.to_dict())


if __name__ == "__main__":
    unittest.main()
