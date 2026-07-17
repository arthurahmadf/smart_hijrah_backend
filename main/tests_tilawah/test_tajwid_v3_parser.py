from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from main.utils_tilawah.tajwid_v3.annotations import (
    TajwidAnnotationV3,
    make_text_span,
    validate_annotation_against_stream,
)
from main.utils_tilawah.tajwid_v3.context import build_grapheme_context
from main.utils_tilawah.tajwid_v3.gold_loader import load_default_gold_dataset
from main.utils_tilawah.tajwid_v3.grapheme_parser import (
    GraphemeKind,
    MarkTag,
    PronunciationState,
    parse_graphemes,
)
from main.utils_tilawah.tajwid_v3.parser_audit import audit_texts
from main.utils_tilawah.tajwid_v3.specification import AppliesWhen
from main.utils_tilawah.tajwid_v3.token_stream import build_token_stream


class TajwidV3ParserTests(SimpleTestCase):
    databases = set()

    def test_grapheme_parser_round_trip(self):
        text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        parsed = parse_graphemes(text)
        self.assertEqual(parsed.reconstruct(), text)
        self.assertEqual(parsed.validate_integrity(), ())

    def test_combining_marks_stay_with_base_letter(self):
        parsed = parse_graphemes("رَّ")
        self.assertEqual(len(parsed.graphemes), 1)
        item = parsed.graphemes[0]
        self.assertEqual(item.base_letter, "ر")
        self.assertTrue(item.has_shadda)
        self.assertIn(MarkTag.FATHA, item.mark_tags)

    def test_leading_quranic_mark_does_not_become_word(self):
        stream = build_token_stream("ۙاِنَّمَا")
        self.assertEqual(len(stream.words), 1)
        self.assertEqual(stream.words[0].text, "اِنَّمَا")
        self.assertEqual(stream.graphemes[0].kind, GraphemeKind.QURANIC_MARK)
        self.assertIsNone(stream.graphemes[0].word_index)

    def test_attached_waqf_mark_preserved_without_word_drift(self):
        stream = build_token_stream("يُوْقِنُوْنَۗ")
        self.assertEqual(len(stream.words), 1)
        self.assertEqual(stream.words[0].text, "يُوْقِنُوْنَۗ")
        self.assertTrue(stream.graphemes[-1].has_waqf_mark)

    def test_word_indices_remain_contiguous(self):
        stream = build_token_stream("هُمُ الْمُفْلِحُوْنَ ۙاِنَّمَا")
        self.assertEqual([word.index for word in stream.words], [0, 1, 2])
        self.assertEqual(stream.words[2].text, "اِنَّمَا")

    def test_navigation_skips_whitespace_and_quranic_marks(self):
        stream = build_token_stream("مِنْ ۙشَرِّ")
        noon = next(item for item in stream.graphemes if item.base_letter == "ن")
        next_letter = stream.next_letter(noon.index)
        self.assertIsNotNone(next_letter)
        self.assertEqual(next_letter.base_letter, "ش")
        self.assertEqual(next_letter.word_index, 1)

    def test_hamzat_wasl_is_contextual_candidate(self):
        stream = build_token_stream("ٱلْحَمْدُ")
        first = next(stream.iter_letters())
        self.assertEqual(first.base_letter, "ٱ")
        self.assertEqual(first.pronunciation_state, PronunciationState.CONTEXTUAL)

    def test_context_exposes_adjacent_words_and_letters(self):
        stream = build_token_stream("مِنْ شَرِّ")
        noon = next(item for item in stream.graphemes if item.base_letter == "ن")
        context = build_grapheme_context(stream, noon.index)
        self.assertEqual(context.word.index, 0)
        self.assertEqual(context.next_word.index, 1)
        self.assertEqual(context.next_letter.base_letter, "ش")

    def test_annotation_contract_uses_exact_grapheme_spans(self):
        stream = build_token_stream("مِنْ شَرِّ")
        noon = next(item for item in stream.graphemes if item.base_letter == "ن")
        sheen = stream.next_letter(noon.index)
        trigger = make_text_span(stream, noon.index, noon.index + 1)
        context = make_text_span(stream, noon.index, sheen.index + 1)
        annotation = TajwidAnnotationV3(
            rule_code="ikhfa_haqiqi",
            trigger_span=trigger,
            context_span=context,
            display_span=context,
            word_index=0,
            next_word_index=1,
            applies_when=AppliesWhen.WASL,
            evidence={"trigger": "nun_sakinah", "following_letter": "ش"},
            confidence=1.0,
            detector_id="test_detector",
        )
        self.assertEqual(validate_annotation_against_stream(annotation, stream), ())
        self.assertEqual(annotation.trigger_span.text, "نْ")
        self.assertEqual(annotation.context_span.text, "نْ شَ")

    def test_invalid_span_is_rejected(self):
        stream = build_token_stream("رَّ")
        with self.assertRaises(ValueError):
            make_text_span(stream, 0, 2)

    def test_all_bootstrap_gold_texts_parse_without_structural_error(self):
        dataset = load_default_gold_dataset(Path(settings.BASE_DIR))
        report = audit_texts((case.case_id, case.text) for case in dataset.cases)
        self.assertTrue(report.success)
        self.assertEqual(report.failed_texts, 0)
        self.assertEqual(report.passed_texts, len(dataset.cases))
