from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from ..annotations import TajwidAnnotationV3, make_text_span
from ..grapheme_parser import CanonicalGrapheme, GraphemeKind, HAMZAT_WASL, MarkTag
from ..rule_specs import get_rule_spec
from ..specification import AppliesWhen, ReadingMode
from ..token_stream import CanonicalTokenStream, WordToken
from .base import DetectorIssue, DetectorOutput


DETECTOR_ID = "ra_detector_v3.0.0-alpha.1"
SUPPORTED_RULE_CODES = frozenset({
    "ra_tafkhim",
    "ra_tarqiq",
    "ra_both_permitted",
})

ISTILA_LETTERS = frozenset({"خ", "ص", "ض", "غ", "ط", "ق", "ظ"})

# Hafs 'an 'Asim through al-Shatibiyyah: the ra in فِرْقٍ allows both
# faces in wasl. Waqf on the word follows tafkhim.
BOTH_IN_WASL_REGISTRY = frozenset({("26:63", "فرق")})

# At waqf, these lexical loci allow both faces. The verse key is required so
# an unrelated spelling cannot silently inherit a profile exception.
BOTH_IN_WAQF_REGISTRY = frozenset({
    ("12:21", "مصر"),
    ("12:99", "مصر"),
    ("43:51", "مصر"),
    ("34:12", "القطر"),
})


@dataclass(frozen=True, slots=True)
class _Decision:
    rule_code: str
    reason: str
    context_start: int
    context_end: int
    confidence: float = 1.0
    evidence: dict[str, object] | None = None


def _has(item: CanonicalGrapheme, *tags: MarkTag) -> bool:
    return any(tag in item.mark_tags for tag in tags)


def _vowel_class(item: CanonicalGrapheme) -> Optional[str]:
    if _has(item, MarkTag.KASRA, MarkTag.KASRATAN):
        return "kasra"
    if _has(item, MarkTag.FATHA, MarkTag.FATHATAN):
        return "fatha"
    if _has(item, MarkTag.DAMMA, MarkTag.DAMMATAN):
        return "damma"
    return None


def _is_sakin(item: CanonicalGrapheme) -> bool:
    return item.has_sukun


def _word_letters(stream: CanonicalTokenStream, word: WordToken) -> tuple[CanonicalGrapheme, ...]:
    return tuple(stream.grapheme(index) for index in word.letter_indices)


def _word_key(stream: CanonicalTokenStream, word: WordToken) -> str:
    return "".join(
        item.folded_base or item.base_letter or ""
        for item in _word_letters(stream, word)
        if item.kind == GraphemeKind.LETTER
    )


def _same_word_previous(
    stream: CanonicalTokenStream,
    item: CanonicalGrapheme,
) -> Optional[CanonicalGrapheme]:
    return stream.previous_letter(item.index, same_word_only=True)


def _same_word_next(
    stream: CanonicalTokenStream,
    item: CanonicalGrapheme,
) -> Optional[CanonicalGrapheme]:
    return stream.next_letter(item.index, same_word_only=True)


def _last_letter(stream: CanonicalTokenStream) -> Optional[CanonicalGrapheme]:
    for item in reversed(stream.graphemes):
        if item.kind == GraphemeKind.LETTER:
            return item
    return None


def _is_actual_waqf_locus(
    stream: CanonicalTokenStream,
    item: CanonicalGrapheme,
    reading_mode: ReadingMode,
) -> bool:
    if reading_mode not in {ReadingMode.AYAH_STOP, ReadingMode.WAQF}:
        return False
    last = _last_letter(stream)
    return last is not None and last.index == item.index


def _underlying_vowel_before_carrier(
    stream: CanonicalTokenStream,
    carrier: CanonicalGrapheme,
) -> tuple[Optional[str], Optional[CanonicalGrapheme]]:
    before = _same_word_previous(stream, carrier)
    if before is None:
        return None, None
    if carrier.folded_base == "ي" and _vowel_class(before) == "kasra":
        return "kasra", before
    if carrier.folded_base == "و" and _vowel_class(before) == "damma":
        return "damma", before
    if carrier.folded_base == "ا" and _vowel_class(before) == "fatha":
        return "fatha", before
    return None, before


def _decision_direct_vowel(item: CanonicalGrapheme) -> Optional[_Decision]:
    vowel = _vowel_class(item)
    if vowel == "kasra":
        return _Decision(
            rule_code="ra_tarqiq",
            reason="ra_with_kasra",
            context_start=item.index,
            context_end=item.index + 1,
            evidence={"ra_vowel": vowel, "ra_has_shadda": item.has_shadda},
        )
    if vowel in {"fatha", "damma"}:
        return _Decision(
            rule_code="ra_tafkhim",
            reason="ra_with_fatha_or_damma",
            context_start=item.index,
            context_end=item.index + 1,
            evidence={"ra_vowel": vowel, "ra_has_shadda": item.has_shadda},
        )
    return None


def _decision_sakin_wasl(
    stream: CanonicalTokenStream,
    item: CanonicalGrapheme,
    *,
    word: WordToken,
    verse_key: str | None,
    reading_mode: ReadingMode,
) -> tuple[Optional[_Decision], tuple[DetectorIssue, ...]]:
    issues: list[DetectorIssue] = []
    word_key = _word_key(stream, word)

    if (verse_key, word_key) in BOTH_IN_WASL_REGISTRY:
        previous = _same_word_previous(stream, item)
        following = _same_word_next(stream, item)
        start = previous.index if previous is not None else item.index
        end = following.index + 1 if following is not None else item.index + 1
        stopping_on_this_word = (
            reading_mode in {ReadingMode.AYAH_STOP, ReadingMode.WAQF}
            and word.index == len(stream.words) - 1
        )
        if stopping_on_this_word:
            return (
                _Decision(
                    rule_code="ra_tafkhim",
                    reason="profile_lexical_exception_firq_waqf",
                    context_start=start,
                    context_end=end,
                    confidence=0.95,
                    evidence={
                        "word_key": word_key,
                        "verse_key": verse_key,
                        "waqf": True,
                    },
                ),
                tuple(issues),
            )
        return (
            _Decision(
                rule_code="ra_both_permitted",
                reason="profile_lexical_exception_firq_wasl",
                context_start=start,
                context_end=end,
                confidence=0.95,
                evidence={
                    "word_key": word_key,
                    "verse_key": verse_key,
                    "preferred_face": "tarqiq",
                    "allowed_faces": ["tafkhim", "tarqiq"],
                },
            ),
            tuple(issues),
        )

    previous = _same_word_previous(stream, item)
    if previous is None:
        issues.append(
            DetectorIssue(
                issue_type="ra_sakin_without_same_word_predecessor",
                severity="warning",
                grapheme_index=item.index,
                word_index=word.index,
                detail="Ra sakinah tidak memiliki predecessor dalam kata yang sama.",
                evidence={"word": word.text, "verse_key": verse_key},
            )
        )
        return None, tuple(issues)

    if previous.base_letter == HAMZAT_WASL:
        return (
            _Decision(
                rule_code="ra_tafkhim",
                reason="ra_sakin_after_temporary_kasra_of_hamzat_wasl",
                context_start=previous.index,
                context_end=item.index + 1,
                confidence=0.95,
                evidence={
                    "preceding_type": "hamzat_wasl",
                    "kasra_type": "temporary",
                },
            ),
            tuple(issues),
        )

    # A sakin ya immediately before Ra gives tarqiq.
    if previous.folded_base == "ي" and (_is_sakin(previous) or _vowel_class(previous) is None):
        before_ya = _same_word_previous(stream, previous)
        context_start = (
            before_ya.index
            if before_ya is not None and _vowel_class(before_ya) == "kasra" and not _is_sakin(previous)
            else previous.index
        )
        return (
            _Decision(
                rule_code="ra_tarqiq",
                reason="ra_sakin_after_ya_sakinah",
                context_start=context_start,
                context_end=item.index + 1,
                evidence={"preceding_letter": previous.base_letter},
            ),
            tuple(issues),
        )

    previous_vowel = _vowel_class(previous)
    if previous_vowel in {"fatha", "damma"}:
        return (
            _Decision(
                rule_code="ra_tafkhim",
                reason="ra_sakin_after_fatha_or_damma",
                context_start=previous.index,
                context_end=item.index + 1,
                evidence={"preceding_vowel": previous_vowel},
            ),
            tuple(issues),
        )

    if previous_vowel == "kasra":
        following = _same_word_next(stream, item)
        if following is not None and (following.folded_base or following.base_letter) in ISTILA_LETTERS:
            following_vowel = _vowel_class(following)
            return (
                _Decision(
                    rule_code="ra_tafkhim",
                    reason="ra_sakin_after_kasra_before_istila_letter",
                    context_start=previous.index,
                    context_end=following.index + 1,
                    evidence={
                        "preceding_vowel": "kasra",
                        "following_istila_letter": following.base_letter,
                        "following_vowel": following_vowel,
                    },
                ),
                tuple(issues),
            )
        return (
            _Decision(
                rule_code="ra_tarqiq",
                reason="ra_sakin_after_original_kasra_same_word",
                context_start=previous.index,
                context_end=item.index + 1,
                evidence={"preceding_vowel": "kasra", "same_word": True},
            ),
            tuple(issues),
        )

    carrier_vowel, carrier_source = _underlying_vowel_before_carrier(stream, previous)
    if carrier_vowel == "kasra":
        return (
            _Decision(
                rule_code="ra_tarqiq",
                reason="ra_after_ya_maddiyyah",
                context_start=(carrier_source.index if carrier_source else previous.index),
                context_end=item.index + 1,
                evidence={"preceding_vowel": "kasra", "carrier": previous.base_letter},
            ),
            tuple(issues),
        )
    if carrier_vowel in {"fatha", "damma"}:
        return (
            _Decision(
                rule_code="ra_tafkhim",
                reason="ra_after_long_vowel_carrier",
                context_start=(carrier_source.index if carrier_source else previous.index),
                context_end=item.index + 1,
                evidence={"preceding_vowel": carrier_vowel, "carrier": previous.base_letter},
            ),
            tuple(issues),
        )

    issues.append(
        DetectorIssue(
            issue_type="ra_sakin_context_unresolved",
            severity="warning",
            grapheme_index=item.index,
            word_index=word.index,
            detail="Konteks Ra sakinah tidak dapat diputuskan secara aman.",
            evidence={
                "word": word.text,
                "previous": previous.text,
                "verse_key": verse_key,
            },
        )
    )
    return None, tuple(issues)


def _decision_at_waqf(
    stream: CanonicalTokenStream,
    item: CanonicalGrapheme,
    *,
    word: WordToken,
    verse_key: str | None,
) -> tuple[Optional[_Decision], tuple[DetectorIssue, ...]]:
    issues: list[DetectorIssue] = []
    word_key = _word_key(stream, word)

    if (verse_key, word_key) in BOTH_IN_WAQF_REGISTRY:
        previous = _same_word_previous(stream, item)
        start = previous.index if previous is not None else item.index
        return (
            _Decision(
                rule_code="ra_both_permitted",
                reason="profile_lexical_exception_waqf",
                context_start=start,
                context_end=item.index + 1,
                confidence=0.95,
                evidence={
                    "word_key": word_key,
                    "verse_key": verse_key,
                    "allowed_faces": ["tafkhim", "tarqiq"],
                    "preferred_face": "tafkhim",
                },
            ),
            tuple(issues),
        )

    # A mushaddad Ra follows the vowel carried by the shadda grapheme itself.
    if item.has_shadda:
        direct = _decision_direct_vowel(item)
        if direct is not None:
            return (
                _Decision(
                    rule_code=direct.rule_code,
                    reason=f"waqf_on_mushaddad_{direct.reason}",
                    context_start=direct.context_start,
                    context_end=direct.context_end,
                    confidence=direct.confidence,
                    evidence={**(direct.evidence or {}), "waqf": True},
                ),
                tuple(issues),
            )

    previous = _same_word_previous(stream, item)
    if previous is None:
        issues.append(
            DetectorIssue(
                issue_type="ra_waqf_without_same_word_predecessor",
                severity="warning",
                grapheme_index=item.index,
                word_index=word.index,
                detail="Ra pada waqf tidak memiliki predecessor dalam kata yang sama.",
                evidence={"word": word.text, "verse_key": verse_key},
            )
        )
        return None, tuple(issues)

    # Ya sakinah before the stopped Ra always gives tarqiq.
    if previous.folded_base == "ي" and (_is_sakin(previous) or _vowel_class(previous) is None):
        before_ya = _same_word_previous(stream, previous)
        context_start = (
            before_ya.index
            if before_ya is not None and _vowel_class(before_ya) == "kasra" and not _is_sakin(previous)
            else previous.index
        )
        return (
            _Decision(
                rule_code="ra_tarqiq",
                reason="waqf_ra_after_ya_sakinah",
                context_start=context_start,
                context_end=item.index + 1,
                evidence={"waqf": True, "preceding_letter": previous.base_letter},
            ),
            tuple(issues),
        )

    previous_vowel = _vowel_class(previous)
    if previous_vowel == "kasra":
        return (
            _Decision(
                rule_code="ra_tarqiq",
                reason="waqf_ra_after_kasra",
                context_start=previous.index,
                context_end=item.index + 1,
                evidence={"waqf": True, "preceding_vowel": "kasra"},
            ),
            tuple(issues),
        )
    if previous_vowel in {"fatha", "damma"}:
        return (
            _Decision(
                rule_code="ra_tafkhim",
                reason="waqf_ra_after_fatha_or_damma",
                context_start=previous.index,
                context_end=item.index + 1,
                evidence={"waqf": True, "preceding_vowel": previous_vowel},
            ),
            tuple(issues),
        )

    carrier_vowel, carrier_source = _underlying_vowel_before_carrier(stream, previous)
    if carrier_vowel == "kasra":
        return (
            _Decision(
                rule_code="ra_tarqiq",
                reason="waqf_ra_after_ya_maddiyyah",
                context_start=(carrier_source.index if carrier_source else previous.index),
                context_end=item.index + 1,
                evidence={"waqf": True, "preceding_vowel": "kasra", "carrier": previous.base_letter},
            ),
            tuple(issues),
        )
    if carrier_vowel in {"fatha", "damma"}:
        return (
            _Decision(
                rule_code="ra_tafkhim",
                reason="waqf_ra_after_long_vowel_carrier",
                context_start=(carrier_source.index if carrier_source else previous.index),
                context_end=item.index + 1,
                evidence={"waqf": True, "preceding_vowel": carrier_vowel, "carrier": previous.base_letter},
            ),
            tuple(issues),
        )

    # If a consonant before the stopped Ra is sakin, inspect the vowel before it.
    if _is_sakin(previous) or _vowel_class(previous) is None:
        before_previous = _same_word_previous(stream, previous)
        if before_previous is not None:
            before_vowel = _vowel_class(before_previous)
            if before_vowel == "kasra":
                return (
                    _Decision(
                        rule_code="ra_tarqiq",
                        reason="waqf_ra_after_sakin_preceded_by_kasra",
                        context_start=before_previous.index,
                        context_end=item.index + 1,
                        evidence={
                            "waqf": True,
                            "intervening_sakin": previous.base_letter,
                            "preceding_vowel": "kasra",
                        },
                    ),
                    tuple(issues),
                )
            if before_vowel in {"fatha", "damma"}:
                return (
                    _Decision(
                        rule_code="ra_tafkhim",
                        reason="waqf_ra_after_sakin_preceded_by_fatha_or_damma",
                        context_start=before_previous.index,
                        context_end=item.index + 1,
                        evidence={
                            "waqf": True,
                            "intervening_sakin": previous.base_letter,
                            "preceding_vowel": before_vowel,
                        },
                    ),
                    tuple(issues),
                )

    issues.append(
        DetectorIssue(
            issue_type="ra_waqf_context_unresolved",
            severity="warning",
            grapheme_index=item.index,
            word_index=word.index,
            detail="Konteks Ra ketika waqf tidak dapat diputuskan secara aman.",
            evidence={
                "word": word.text,
                "previous": previous.text,
                "verse_key": verse_key,
            },
        )
    )
    return None, tuple(issues)


def _make_annotation(
    stream: CanonicalTokenStream,
    item: CanonicalGrapheme,
    word: WordToken,
    decision: _Decision,
) -> TajwidAnnotationV3:
    spec = get_rule_spec(decision.rule_code)
    trigger = make_text_span(stream, item.index, item.index + 1)
    context = make_text_span(stream, decision.context_start, decision.context_end)
    evidence = {
        "trigger_type": "letter_ra",
        "decision_reason": decision.reason,
        **(decision.evidence or {}),
    }
    return TajwidAnnotationV3(
        rule_code=decision.rule_code,
        trigger_span=trigger,
        context_span=context,
        display_span=trigger,
        word_index=word.index,
        next_word_index=None,
        applies_when=(
            AppliesWhen.PROFILE_DEPENDENT
            if decision.rule_code == "ra_both_permitted"
            else AppliesWhen.CONTEXTUAL
        ),
        evidence=evidence,
        confidence=decision.confidence,
        detector_id=DETECTOR_ID,
        expected_features=dict(spec.expected_features),
    )


class RaDetector:
    detector_id = DETECTOR_ID
    supported_rule_codes = SUPPORTED_RULE_CODES

    def __init__(self, *, verse_key: str | None = None) -> None:
        self.verse_key = verse_key

    def detect(
        self,
        stream: CanonicalTokenStream,
        *,
        reading_mode: ReadingMode,
    ) -> DetectorOutput:
        annotations: list[TajwidAnnotationV3] = []
        issues: list[DetectorIssue] = []

        for item in stream.iter_letters():
            if (item.folded_base or item.base_letter) != "ر":
                continue
            if item.word_index is None:
                continue
            word = stream.word(item.word_index)

            if _is_actual_waqf_locus(stream, item, reading_mode):
                decision, item_issues = _decision_at_waqf(
                    stream,
                    item,
                    word=word,
                    verse_key=self.verse_key,
                )
            else:
                decision = _decision_direct_vowel(item)
                item_issues = ()
                if decision is None and item.has_sukun:
                    decision, item_issues = _decision_sakin_wasl(
                        stream,
                        item,
                        word=word,
                        verse_key=self.verse_key,
                        reading_mode=reading_mode,
                    )
                elif decision is None:
                    issues.append(
                        DetectorIssue(
                            issue_type="ra_without_resolvable_vowel_or_sukun",
                            severity="warning",
                            grapheme_index=item.index,
                            word_index=word.index,
                            detail="Ra tidak memiliki vokal atau sukun eksplisit yang dapat diputuskan.",
                            evidence={"word": word.text, "verse_key": self.verse_key},
                        )
                    )

            issues.extend(item_issues)
            if decision is not None:
                annotations.append(_make_annotation(stream, item, word, decision))

        return DetectorOutput(
            annotations=tuple(annotations),
            issues=tuple(issues),
        )
