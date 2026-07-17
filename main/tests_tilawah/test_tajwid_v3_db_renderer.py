from unittest import TestCase

from main.utils_tilawah.tajwid_v3.db_renderer import (
    DatabaseRenderAnnotation,
    render_database_annotations,
)
from main.utils_tilawah.tajwid_v3.difficulty import (
    level_from_percentile,
    percentile_rank,
)
from main.utils_tilawah.tajwid_v3.token_stream import build_token_stream


class DatabaseRendererTests(TestCase):
    def test_regular_only_reconstructs_source(self):
        text = "الْحَمْدُ لِلَّهِ"
        rules = render_database_annotations(text, [])
        self.assertEqual("".join(item["arabic"] for item in rules), text)
        self.assertEqual(rules[0]["rule_name"], "regular")

    def test_lower_priority_number_wins_overlap(self):
        text = "مِنْ"
        stream = build_token_stream(text)
        end = len(stream.graphemes)
        annotations = [
            DatabaseRenderAnnotation(
                0, end, "slow", "mad", "0xFF256E99", "slow", 70, 1.0, False
            ),
            DatabaseRenderAnnotation(
                0, end, "primary", "idgham", "0xFF4F46A5", "primary", 20, 0.9, False
            ),
        ]
        rules = render_database_annotations(text, annotations)
        self.assertEqual(rules[0]["rule_name"], "idgham")
        self.assertEqual("".join(item["arabic"] for item in rules), text)

    def test_adjacent_segments_with_same_signature_are_merged(self):
        text = "اب"
        annotations = [
            DatabaseRenderAnnotation(
                0, 1, "a", "mad", "0xFF256E99", "x", 10, 1.0, False
            ),
            DatabaseRenderAnnotation(
                1, 2, "b", "mad", "0xFF256E99", "x", 10, 1.0, False
            ),
        ]
        rules = render_database_annotations(text, annotations)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["arabic"], text)

    def test_invalid_span_is_rejected(self):
        text = "مِنْ"
        with self.assertRaises(ValueError):
            render_database_annotations(
                text,
                [
                    DatabaseRenderAnnotation(
                        0, 999, "x", "mad", "0xFF256E99", "x", 10, 1.0, False
                    )
                ],
            )


class DifficultyCalibrationTests(TestCase):
    def test_percentile_rank_is_stable_for_ties(self):
        values = [1.0, 2.0, 2.0, 4.0]
        self.assertAlmostEqual(percentile_rank(values, 2.0), 50.0)

    def test_level_thresholds(self):
        self.assertEqual(level_from_percentile(20), "basic")
        self.assertEqual(level_from_percentile(55), "intermediate")
        self.assertEqual(level_from_percentile(88), "expert")
