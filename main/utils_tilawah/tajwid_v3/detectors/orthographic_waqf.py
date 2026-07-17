from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Iterable, Optional

from ..annotations import TajwidAnnotationV3, make_text_span
from ..grapheme_parser import CanonicalGrapheme, HAMZAT_WASL, MarkTag, fold_base_letter
from ..rule_specs import get_rule_spec
from ..specification import (
    AppliesWhen,
    BoundaryLocation,
    ReadingMode,
    get_recitation_profile,
)
from ..token_stream import CanonicalTokenStream
from .base import DetectorIssue, DetectorOutput


DETECTOR_ID = "orthographic_waqf_detector_v3.0.0-alpha.1"
SUPPORTED_RULE_CODES = frozenset(
    {
        "hamzat_wasl",
        "silent_letter",
        "saktah_wajibah",
        "saktah_jaizah",
    }
)

ROUNDED_ZERO = "\u06df"
RECTANGULAR_ZERO = "\u06e0"
SAKTAH_MARK = "\u06dc"
TATWEEL = "\u0640"

# The well-known سماعية nouns are deliberately explicit. The list concerns
# the orthographic/ibtida aid only; it is not used as a morphology engine.
HAMZAT_WASL_NOUNS = frozenset(
    {
        "اسم",
        "ابن",
        "ابنة",
        "امرؤ",
        "امرأ",
        "اثنان",
        "اثنتان",
    }
)


@dataclass(frozen=True, slots=True)
class _SaktahMatch:
    rule_code: str
    location: BoundaryLocation
    start_word_index: int
    end_word_index: int | None
    trigger: CanonicalGrapheme
    target: CanonicalGrapheme | None
    marker_present: bool


def _has(item: CanonicalGrapheme, *tags: MarkTag) -> bool:
    return any(tag in item.mark_tags for tag in tags)


def _short_vowel(item: CanonicalGrapheme) -> str | None:
    if _has(item, MarkTag.FATHA, MarkTag.FATHATAN):
        return "fatha"
    if _has(item, MarkTag.DAMMA, MarkTag.DAMMATAN):
        return "damma"
    if _has(item, MarkTag.KASRA, MarkTag.KASRATAN):
        return "kasra"
    return None


def _normalise_word(text: str) -> str:
    chars: list[str] = []
    for char in unicodedata.normalize("NFD", text):
        if char == TATWEEL or unicodedata.combining(char):
            continue
        if char in {ROUNDED_ZERO, RECTANGULAR_ZERO, SAKTAH_MARK}:
            continue
        if not unicodedata.category(char).startswith("L"):
            continue
        folded = fold_base_letter(char)
        chars.append(folded or char)
    return "".join(chars)


def _same_word_letters(
    stream: CanonicalTokenStream,
    grapheme: CanonicalGrapheme,
) -> tuple[CanonicalGrapheme, ...]:
    if grapheme.word_index is None:
        return ()
    return tuple(stream.grapheme(i) for i in stream.word(grapheme.word_index).letter_indices)


def _infer_hamzat_wasl_ibtida_vowel(
    stream: CanonicalTokenStream,
    hamzah: CanonicalGrapheme,
) -> tuple[str | None, str]:
    letters = _same_word_letters(stream, hamzah)
    if not letters:
        return None, "word_unavailable"
    try:
        position = letters.index(hamzah)
    except ValueError:
        return None, "word_mapping_unavailable"

    following = letters[position + 1 :]
    if following and (following[0].folded_base or following[0].base_letter) == "ل":
        return "fatha", "definite_article"

    word_key = _normalise_word(stream.word(hamzah.word_index).text)
    without_initial_alef = word_key[1:] if word_key.startswith("ا") else word_key
    if any(without_initial_alef.startswith(item[1:]) for item in HAMZAT_WASL_NOUNS):
        return "kasra", "lexical_noun_registry"

    # For imperative/past verbal forms, the third written consonant after the
    # hamzah determines the conventional starting vowel: dammah if explicitly
    # dammed, otherwise kasrah. This remains metadata, not a separate scored rule.
    if len(following) >= 2:
        third_letter = following[1]
        if _short_vowel(third_letter) == "damma":
            return "damma", "verb_third_letter_damma"
        if _short_vowel(third_letter) in {"fatha", "kasra"}:
            return "kasra", "verb_third_letter_non_damma"
    return None, "unresolved_without_morphology"


def _make_hamzat_wasl_annotation(
    stream: CanonicalTokenStream,
    hamzah: CanonicalGrapheme,
) -> TajwidAnnotationV3:
    previous = stream.previous_letter(hamzah.index)
    pronounced_at_ibtida = previous is None
    initial_vowel, vowel_reason = (
        _infer_hamzat_wasl_ibtida_vowel(stream, hamzah)
        if pronounced_at_ibtida
        else (None, "dropped_in_connected_reading")
    )
    span = make_text_span(stream, hamzah.index, hamzah.index + 1)
    expected = dict(get_rule_spec("hamzat_wasl").expected_features)
    expected.update(
        {
            "render_only": True,
            "pronunciation_status": (
                "pronounced_at_ibtida" if pronounced_at_ibtida else "dropped_in_wasl"
            ),
            "initial_vowel": initial_vowel,
        }
    )
    return TajwidAnnotationV3(
        rule_code="hamzat_wasl",
        trigger_span=span,
        context_span=span,
        display_span=span,
        word_index=hamzah.word_index,
        next_word_index=None,
        applies_when=AppliesWhen.CONTEXTUAL,
        evidence={
            "base_letter": hamzah.base_letter,
            "word_is_first_input_word": hamzah.word_index == 0,
            "has_previous_pronounced_letter": previous is not None,
            "pronunciation_status": expected["pronunciation_status"],
            "initial_vowel_reason": vowel_reason,
        },
        expected_features=expected,
        confidence=1.0 if initial_vowel is not None or not pronounced_at_ibtida else 0.95,
        detector_id=DETECTOR_ID,
    )


def _is_actual_stop_on(
    stream: CanonicalTokenStream,
    item: CanonicalGrapheme,
    reading_mode: ReadingMode,
) -> bool:
    if reading_mode not in {ReadingMode.AYAH_STOP, ReadingMode.WAQF}:
        return False
    return stream.next_letter(item.index) is None


def _make_silent_annotation(
    stream: CanonicalTokenStream,
    item: CanonicalGrapheme,
    *,
    mark: str,
    reading_mode: ReadingMode,
) -> TajwidAnnotationV3 | None:
    if mark == RECTANGULAR_ZERO and _is_actual_stop_on(stream, item, reading_mode):
        return None
    span = make_text_span(stream, item.index, item.index + 1)
    always_silent = mark == ROUNDED_ZERO
    expected = dict(get_rule_spec("silent_letter").expected_features)
    expected.update(
        {
            "render_only": True,
            "silent": True,
            "silent_when": "both" if always_silent else "wasl",
            "pronounced_when": None if always_silent else "waqf",
            "orthographic_mark": (
                "small_high_rounded_zero"
                if always_silent
                else "small_high_upright_rectangular_zero"
            ),
        }
    )
    return TajwidAnnotationV3(
        rule_code="silent_letter",
        trigger_span=span,
        context_span=span,
        display_span=span,
        word_index=item.word_index,
        next_word_index=None,
        applies_when=AppliesWhen.CONTEXTUAL,
        evidence={
            "base_letter": item.base_letter,
            "mark": mark,
            "mark_codepoint": f"U+{ord(mark):04X}",
            "reading_mode": reading_mode.value,
            "actual_stop_on_letter": _is_actual_stop_on(stream, item, reading_mode),
        },
        expected_features=expected,
        confidence=1.0,
        detector_id=DETECTOR_ID,
    )


def _word_matches(stream: CanonicalTokenStream, word_index: int, expected: str) -> bool:
    return _normalise_word(stream.word(word_index).text) == _normalise_word(expected)


def _last_letter(stream: CanonicalTokenStream, word_index: int) -> CanonicalGrapheme:
    return stream.grapheme(stream.word(word_index).letter_indices[-1])


def _first_letter(stream: CanonicalTokenStream, word_index: int) -> CanonicalGrapheme:
    return stream.grapheme(stream.word(word_index).letter_indices[0])


def _iter_profile_locations(rule_code: str) -> Iterable[BoundaryLocation]:
    profile = get_recitation_profile()
    if rule_code == "saktah_wajibah":
        return profile.mandatory_saktah
    return profile.optional_saktah


def _find_saktah_matches(
    stream: CanonicalTokenStream,
    *,
    verse_key: str | None,
    boundary_to_verse_key: str | None,
) -> tuple[_SaktahMatch, ...]:
    matches: list[_SaktahMatch] = []
    effective_to_key = boundary_to_verse_key or verse_key
    for rule_code in ("saktah_wajibah", "saktah_jaizah"):
        for location in _iter_profile_locations(rule_code):
            if verse_key != location.start_verse_key:
                continue
            if effective_to_key is not None and effective_to_key != location.end_verse_key:
                # Same-ayah locations remain valid without an explicit destination.
                if location.start_verse_key != location.end_verse_key:
                    continue
            for word in stream.words:
                if not _word_matches(stream, word.index, location.start_word):
                    continue
                trigger = _last_letter(stream, word.index)
                target_word_index: int | None = None
                target: CanonicalGrapheme | None = None
                for candidate in stream.words[word.index + 1 :]:
                    if _word_matches(stream, candidate.index, location.end_word):
                        target_word_index = candidate.index
                        target = _first_letter(stream, candidate.index)
                        break
                matches.append(
                    _SaktahMatch(
                        rule_code=rule_code,
                        location=location,
                        start_word_index=word.index,
                        end_word_index=target_word_index,
                        trigger=trigger,
                        target=target,
                        marker_present=SAKTAH_MARK in trigger.text,
                    )
                )
    return tuple(matches)


def _saktah_active_in_mode(
    match: _SaktahMatch,
    reading_mode: ReadingMode,
) -> bool:
    if reading_mode == ReadingMode.WAQF:
        return False
    cross_verse = match.location.start_verse_key != match.location.end_verse_key
    if reading_mode == ReadingMode.AYAH_STOP and cross_verse:
        return False
    return True


def _make_saktah_annotation(
    stream: CanonicalTokenStream,
    match: _SaktahMatch,
) -> TajwidAnnotationV3:
    trigger = match.trigger
    trigger_span = make_text_span(stream, trigger.index, trigger.index + 1)
    context_start = trigger.index
    previous = stream.previous_letter(trigger.index, same_word_only=True)
    if (trigger.folded_base or trigger.base_letter) == "ا" and previous is not None:
        context_start = previous.index
    context_end = trigger.index + 1
    if match.target is not None:
        context_end = match.target.index + 1
    context_span = make_text_span(stream, context_start, context_end)
    spec = get_rule_spec(match.rule_code)
    expected = dict(spec.expected_features)
    expected.update(
        {
            "marker_present": match.marker_present,
            "boundary_start_verse": match.location.start_verse_key,
            "boundary_end_verse": match.location.end_verse_key,
        }
    )
    if match.rule_code == "saktah_jaizah":
        expected.update(
            {
                "allowed_faces": ["saktah", "connected_alternative"],
                "selected_face": None,
            }
        )
    return TajwidAnnotationV3(
        rule_code=match.rule_code,
        trigger_span=trigger_span,
        context_span=context_span,
        display_span=trigger_span,
        word_index=match.start_word_index,
        next_word_index=match.end_word_index,
        applies_when=AppliesWhen.PROFILE_DEPENDENT,
        evidence={
            "verse_key": match.location.start_verse_key,
            "boundary_to_verse_key": match.location.end_verse_key,
            "start_word": match.location.start_word,
            "end_word": match.location.end_word,
            "marker_present": match.marker_present,
            "target_available_in_input": match.target is not None,
            "profile_notes": match.location.notes,
        },
        expected_features=expected,
        confidence=(
            1.0
            if match.marker_present and match.rule_code == "saktah_wajibah"
            else 0.97
            if match.marker_present
            else 0.95
        ),
        detector_id=DETECTOR_ID,
    )


class OrthographicWaqfDetector:
    detector_id = DETECTOR_ID
    supported_rule_codes = SUPPORTED_RULE_CODES

    def __init__(
        self,
        *,
        verse_key: str | None = None,
        boundary_to_verse_key: str | None = None,
    ) -> None:
        self.verse_key = verse_key
        self.boundary_to_verse_key = boundary_to_verse_key

    def detect(
        self,
        stream: CanonicalTokenStream,
        *,
        reading_mode: ReadingMode,
    ) -> DetectorOutput:
        annotations: list[TajwidAnnotationV3] = []
        issues: list[DetectorIssue] = []
        registered_saktah_graphemes: set[int] = set()

        for item in stream.iter_letters():
            if item.word_index is None:
                issues.append(
                    DetectorIssue(
                        issue_type="orthographic_letter_without_word",
                        severity="error",
                        grapheme_index=item.index,
                        word_index=None,
                        detail="Huruf ortografis tidak terpetakan ke WordToken.",
                        evidence={"text": item.text},
                    )
                )
                continue
            if item.base_letter == HAMZAT_WASL:
                annotations.append(_make_hamzat_wasl_annotation(stream, item))
            for mark in (ROUNDED_ZERO, RECTANGULAR_ZERO):
                if mark not in item.text:
                    continue
                annotation = _make_silent_annotation(
                    stream,
                    item,
                    mark=mark,
                    reading_mode=reading_mode,
                )
                if annotation is not None:
                    annotations.append(annotation)

        for match in _find_saktah_matches(
            stream,
            verse_key=self.verse_key,
            boundary_to_verse_key=self.boundary_to_verse_key,
        ):
            registered_saktah_graphemes.add(match.trigger.index)
            if not _saktah_active_in_mode(match, reading_mode):
                continue
            if match.target is None:
                issues.append(
                    DetectorIssue(
                        issue_type="saktah_boundary_target_not_in_input",
                        severity="warning",
                        grapheme_index=match.trigger.index,
                        word_index=match.start_word_index,
                        detail=(
                            "Lokasi saktah terdaftar tetapi kata tujuan tidak tersedia dalam input; "
                            "annotation trigger-only tetap dapat dipakai untuk rendering ayat."
                        ),
                        evidence={
                            "verse_key": self.verse_key,
                            "boundary_to_verse_key": self.boundary_to_verse_key,
                            "start_word": match.location.start_word,
                            "end_word": match.location.end_word,
                        },
                    )
                )
            annotations.append(_make_saktah_annotation(stream, match))

        for grapheme in stream.graphemes:
            if SAKTAH_MARK not in grapheme.text:
                continue
            if grapheme.index in registered_saktah_graphemes:
                continue
            issues.append(
                DetectorIssue(
                    issue_type="unregistered_saktah_mark",
                    severity="warning",
                    grapheme_index=grapheme.index,
                    word_index=grapheme.word_index,
                    detail="Tanda saktah ditemukan di luar boundary registry profil.",
                    evidence={
                        "text": grapheme.text,
                        "verse_key": self.verse_key,
                        "boundary_to_verse_key": self.boundary_to_verse_key,
                    },
                )
            )

        return DetectorOutput(
            annotations=tuple(annotations),
            issues=tuple(issues),
        )
