from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple

from ..annotations import TajwidAnnotationV3, make_text_span
from ..grapheme_parser import CanonicalGrapheme, HAMZAT_WASL, MarkTag
from ..rule_specs import get_rule_spec
from ..specification import AppliesWhen, ReadingMode
from ..token_stream import CanonicalTokenStream
from .base import DetectorIssue, DetectorOutput


DETECTOR_ID = "advanced_mad_detector_v3.0.0-alpha.1"
SUPPORTED_RULE_CODES = frozenset(
    {
        "mad_tamkin",
        "mad_silah_qasirah",
        "mad_silah_tawilah",
        "mad_lazim_harfi_muthaqqal",
        "mad_lazim_harfi_mukhaffaf",
        "mad_harfi_tabii",
        "mad_ayn_muqattaah",
        "mad_farq",
    }
)

HAMZA_LETTERS = frozenset({"ء", "أ", "إ", "ؤ", "ئ", "آ"})
MUQATTAAH_TABII = frozenset({"ح", "ي", "ط", "ه", "ر"})
MUQATTAAH_LAZIM = frozenset({"ن", "ق", "ص", "س", "ل", "ك", "م"})
MUQATTAAH_ALL = MUQATTAAH_TABII | MUQATTAAH_LAZIM | {"ا", "ع"}
MUQATTAAH_VERSE_KEYS = frozenset(
    {
        "2:1", "3:1", "7:1", "10:1", "11:1", "12:1", "13:1", "14:1",
        "15:1", "19:1", "20:1", "26:1", "27:1", "28:1", "29:1", "30:1",
        "31:1", "32:1", "36:1", "38:1", "40:1", "41:1", "42:1", "42:2",
        "43:1", "44:1", "45:1", "46:1", "50:1", "68:1",
    }
)
MAD_FARQ_VERSE_KEYS = frozenset({"6:143", "6:144", "10:51", "10:59", "10:91", "27:59"})

# Hafs lexical exception: the pronominal ha in يرضه is read without silah.
SILAH_EXCLUDED_WORDS = frozenset({"يرضه"})
# Conservative exclusions for lexical/root-final ha that can resemble ha dhamir.
ORIGINAL_HA_EXCLUSIONS = frozenset(
    {
        "فواكه", "وجه", "ينته", "تنته", "شفاه", "اشباه", "نفقه",
    }
)


@dataclass(frozen=True, slots=True)
class _MuqattaahLetter:
    item: CanonicalGrapheme
    base: str
    next_base: Optional[str]


def _has(item: CanonicalGrapheme, tag: MarkTag) -> bool:
    return tag in item.mark_tags


def _make_annotation(
    stream: CanonicalTokenStream,
    *,
    rule_code: str,
    trigger_start: int,
    trigger_end: int,
    context_start: Optional[int] = None,
    context_end: Optional[int] = None,
    display_start: Optional[int] = None,
    display_end: Optional[int] = None,
    word_index: int,
    next_word_index: Optional[int],
    applies_when: AppliesWhen,
    evidence: dict,
    confidence: float,
    notes: str = "",
) -> TajwidAnnotationV3:
    spec = get_rule_spec(rule_code)
    context_start = trigger_start if context_start is None else context_start
    context_end = trigger_end if context_end is None else context_end
    display_start = context_start if display_start is None else display_start
    display_end = context_end if display_end is None else display_end
    return TajwidAnnotationV3(
        rule_code=rule_code,
        trigger_span=make_text_span(stream, trigger_start, trigger_end),
        context_span=make_text_span(stream, context_start, context_end),
        display_span=make_text_span(stream, display_start, display_end),
        word_index=word_index,
        next_word_index=next_word_index,
        applies_when=applies_when,
        evidence=evidence,
        expected_features=dict(spec.expected_features),
        confidence=confidence,
        detector_id=DETECTOR_ID,
        notes=notes,
    )


def _normalize_word(text: str) -> str:
    text = re.sub(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]", "", text)
    text = text.replace("ـ", "")
    text = re.sub(r"[أإآٱٲٳ]", "ا", text)
    text = text.replace("ى", "ي")
    return text


def _is_stop_mode(mode: ReadingMode) -> bool:
    return mode in {ReadingMode.WAQF, ReadingMode.AYAH_STOP}


def _has_explicit_short_vowel(item: CanonicalGrapheme) -> bool:
    return item.has_short_vowel or item.has_tanwin


def _is_allah_form(normalized: str) -> bool:
    return normalized.endswith("الله") or normalized in {"لله", "بالله", "والله", "فالله", "تالله", "كالله"}


def _detect_tamkin(stream: CanonicalTokenStream) -> Tuple[TajwidAnnotationV3, ...]:
    annotations = []
    for first in stream.iter_letters():
        if first.folded_base != "ي" or not first.has_shadda or not _has(first, MarkTag.KASRA):
            continue
        second = stream.next_letter(first.index, same_word_only=True)
        if second is None:
            continue
        explicit_second_ya = second.folded_base == "ي" and (
            second.has_sukun or not second.has_short_vowel
        )
        small_ya = "\u06e6" in second.text or "\u06e7" in second.text
        if not (explicit_second_ya or small_ya):
            continue
        annotations.append(
            _make_annotation(
                stream,
                rule_code="mad_tamkin",
                trigger_start=first.index,
                trigger_end=second.index + 1,
                word_index=first.word_index,
                next_word_index=None,
                applies_when=AppliesWhen.BOTH,
                confidence=0.95,
                notes="Candidate morphology-sensitive; menunggu cross-check ahli.",
                evidence={
                    "trigger_type": "ya_mushaddadah_kasrah_followed_by_ya",
                    "first_ya_index": first.index,
                    "second_ya_index": second.index,
                    "small_ya_encoding": small_ya,
                },
            )
        )
    return tuple(annotations)


def _detect_silah(
    stream: CanonicalTokenStream,
    reading_mode: ReadingMode,
) -> Tuple[Tuple[TajwidAnnotationV3, ...], Tuple[DetectorIssue, ...]]:
    if reading_mode == ReadingMode.WAQF:
        return (), ()

    annotations = []
    issues = []
    final_word_index = len(stream.words) - 1

    for ha in stream.iter_letters():
        if ha.base_letter != "ه" or ha.word_index is None or not ha.is_word_end:
            continue
        if ha.has_sukun or ha.has_shadda or ha.has_tanwin:
            continue
        if not (_has(ha, MarkTag.DAMMA) or _has(ha, MarkTag.KASRA)):
            continue
        if reading_mode == ReadingMode.AYAH_STOP and ha.word_index == final_word_index:
            continue

        word = stream.word(ha.word_index)
        normalized = _normalize_word(word.text)
        if _is_allah_form(normalized):
            continue
        if normalized in SILAH_EXCLUDED_WORDS or normalized in ORIGINAL_HA_EXCLUSIONS:
            continue

        previous = stream.previous_letter(ha.index, same_word_only=True)
        if previous is None or not _has_explicit_short_vowel(previous):
            continue

        target = stream.next_letter(ha.index)
        if target is None or target.word_index == ha.word_index:
            continue
        if target.base_letter == HAMZAT_WASL:
            issues.append(
                DetectorIssue(
                    issue_type="silah_hamzat_wasl_deferred",
                    severity="warning",
                    grapheme_index=target.index,
                    word_index=target.word_index,
                    detail="Target sesudah ha dhamir adalah hamzat wasl; pronunciation resolver diperlukan.",
                    evidence={"word": word.text, "target": target.text},
                )
            )
            continue
        if not (_has_explicit_short_vowel(target) or target.base_letter in HAMZA_LETTERS):
            continue

        is_tawilah = target.base_letter in HAMZA_LETTERS
        rule_code = "mad_silah_tawilah" if is_tawilah else "mad_silah_qasirah"
        context_end = target.index + 1 if is_tawilah else ha.index + 1
        annotations.append(
            _make_annotation(
                stream,
                rule_code=rule_code,
                trigger_start=ha.index,
                trigger_end=ha.index + 1,
                context_start=ha.index,
                context_end=context_end,
                display_start=ha.index,
                display_end=context_end,
                word_index=ha.word_index,
                next_word_index=target.word_index,
                applies_when=AppliesWhen.WASL,
                confidence=0.88 if is_tawilah else 0.85,
                notes=(
                    "Candidate ha dhamir berbasis orthography. Morphology adapter dan review ahli tetap diperlukan."
                ),
                evidence={
                    "trigger_type": "candidate_ha_damir",
                    "word_normalized": normalized,
                    "previous_letter": previous.base_letter,
                    "following_letter": target.base_letter,
                    "following_is_hamza": is_tawilah,
                    "resolver": "conservative_orthographic_suffix_v1",
                },
            )
        )
    return tuple(annotations), tuple(issues)


def _muqattaah_sequence(stream: CanonicalTokenStream, verse_key: Optional[str]) -> Optional[Tuple[_MuqattaahLetter, ...]]:
    letters = list(stream.iter_letters())
    if not letters or len(stream.words) != 1 or len(letters) > 5:
        return None
    bases = [item.folded_base or item.base_letter for item in letters]
    if not all(base in MUQATTAAH_ALL for base in bases):
        return None
    if verse_key not in MUQATTAAH_VERSE_KEYS:
        # Allow standalone gold/bootstrap forms only when they look like disjoint
        # letters: no ordinary short-vowel morphology on the written letters.
        if any(item.has_short_vowel or item.has_tanwin or item.has_shadda or item.has_sukun for item in letters):
            return None
    result = []
    for index, item in enumerate(letters):
        result.append(
            _MuqattaahLetter(
                item=item,
                base=bases[index],
                next_base=bases[index + 1] if index + 1 < len(bases) else None,
            )
        )
    return tuple(result)


def _detect_muqattaah(
    stream: CanonicalTokenStream,
    verse_key: Optional[str],
) -> Tuple[TajwidAnnotationV3, ...]:
    sequence = _muqattaah_sequence(stream, verse_key)
    if sequence is None:
        return ()
    confidence = 1.0 if verse_key in MUQATTAAH_VERSE_KEYS else 0.90
    annotations = []
    for token in sequence:
        base = token.base
        if base == "ا":
            continue
        if base in MUQATTAAH_TABII:
            rule_code = "mad_harfi_tabii"
        elif base == "ع":
            rule_code = "mad_ayn_muqattaah"
        elif base in MUQATTAAH_LAZIM:
            is_heavy = (base, token.next_base) in {("ل", "م"), ("س", "م")}
            rule_code = (
                "mad_lazim_harfi_muthaqqal"
                if is_heavy
                else "mad_lazim_harfi_mukhaffaf"
            )
        else:
            continue
        annotations.append(
            _make_annotation(
                stream,
                rule_code=rule_code,
                trigger_start=token.item.index,
                trigger_end=token.item.index + 1,
                word_index=token.item.word_index,
                next_word_index=None,
                applies_when=AppliesWhen.PROFILE_DEPENDENT,
                confidence=confidence if rule_code != "mad_ayn_muqattaah" else min(confidence, 0.95),
                notes="Huruf muqatta'ah mengikuti registry Hafs al-Shatibiyyah; review ahli tetap dicatat.",
                evidence={
                    "trigger_type": "muqattaah_letter_registry",
                    "letter": base,
                    "next_letter": token.next_base,
                    "verse_key": verse_key,
                    "sequence": "".join(item.base for item in sequence),
                },
            )
        )
    return tuple(annotations)


def _detect_farq(
    stream: CanonicalTokenStream,
    verse_key: Optional[str],
) -> Tuple[TajwidAnnotationV3, ...]:
    letters = list(stream.iter_letters())
    if not letters:
        return ()

    start = None
    end = None
    first = letters[0]
    if first.base_letter == "آ":
        start, end = first.index, first.index + 1
    elif len(letters) >= 2 and first.base_letter == "ء":
        second = letters[1]
        if second.folded_base == "ا" and (_has(second, MarkTag.MADDAH) or "ٓ" in second.text):
            start, end = first.index, second.index + 1
    if start is None:
        return ()

    normalized = _normalize_word(stream.words[0].text) if stream.words else ""
    if verse_key not in MAD_FARQ_VERSE_KEYS:
        return ()

    return (
        _make_annotation(
            stream,
            rule_code="mad_farq",
            trigger_start=start,
            trigger_end=end,
            word_index=0,
            next_word_index=None,
            applies_when=AppliesWhen.PROFILE_DEPENDENT,
            confidence=1.0,
            notes="Mad Farq dibatasi registry enam lokasi Hafs; lexical fallback bersifat provisional.",
            evidence={
                "trigger_type": "interrogative_hamza_plus_hamzat_wasl",
                "verse_key": verse_key,
                "normalized_word": normalized,
                "registry_match": True,
            },
        ),
    )


class AdvancedMadDetector:
    detector_id = DETECTOR_ID
    supported_rule_codes = SUPPORTED_RULE_CODES

    def __init__(self, *, verse_key: Optional[str] = None):
        self.verse_key = verse_key

    def detect(self, stream: CanonicalTokenStream, *, reading_mode: ReadingMode) -> DetectorOutput:
        annotations = []
        issues = []
        annotations.extend(_detect_tamkin(stream))
        silah_annotations, silah_issues = _detect_silah(stream, reading_mode)
        annotations.extend(silah_annotations)
        issues.extend(silah_issues)
        annotations.extend(_detect_muqattaah(stream, self.verse_key))
        annotations.extend(_detect_farq(stream, self.verse_key))
        return DetectorOutput(annotations=tuple(annotations), issues=tuple(issues))
