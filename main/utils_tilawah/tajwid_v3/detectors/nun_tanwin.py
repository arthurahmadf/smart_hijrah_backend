from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

from ..annotations import TajwidAnnotationV3, make_text_span
from ..grapheme_parser import CanonicalGrapheme, HAMZAT_WASL, MarkTag
from ..rule_specs import get_rule_spec
from ..specification import AppliesWhen, ReadingMode
from ..token_stream import CanonicalTokenStream
from .base import DetectorIssue, DetectorOutput


DETECTOR_ID = "nun_tanwin_detector_v3.0.0-alpha.1"

HALQI_BASES = frozenset({"ه", "ع", "ح", "غ", "خ"})
HAMZA_BASES = frozenset({"ء", "أ", "إ", "آ", "ؤ", "ئ"})
IDGHAM_GHUNNAH = frozenset({"ي", "ن", "م", "و"})
IDGHAM_BILA_GHUNNAH = frozenset({"ل", "ر"})
IKHFA_HAQIQI = frozenset(
    {"ت", "ث", "ج", "د", "ذ", "ز", "س", "ش", "ص", "ض", "ط", "ظ", "ف", "ق", "ك"}
)
IQLAB_TARGET = "ب"

# Four lexical families conventionally treated as izhar mutlaq in Hafs.
IZHAR_MUTLAQ_LEXEMES = frozenset({"الدنيا", "بنيان", "صنوان", "قنوان"})
PROCLITIC_PREFIXES = frozenset({"و", "ف", "ب", "ك", "ل"})

SUPPORTED_RULE_CODES = frozenset(
    {
        "izhar_halqi",
        "izhar_mutlaq",
        "idgham_bighunnah",
        "idgham_bilaghunnah",
        "iqlab",
        "ikhfa_haqiqi",
    }
)


@dataclass(frozen=True, slots=True)
class Trigger:
    grapheme: CanonicalGrapheme
    trigger_type: str


def _word_letters(stream: CanonicalTokenStream, word_index: int) -> str:
    word = stream.word(word_index)
    return "".join(
        stream.grapheme(index).folded_base or ""
        for index in word.letter_indices
    )


def _lexeme_candidates(word_letters: str) -> Tuple[str, ...]:
    candidates = {word_letters}
    frontier = {word_letters}
    for _ in range(2):
        next_frontier = set()
        for candidate in frontier:
            if candidate and candidate[0] in PROCLITIC_PREFIXES:
                stripped = candidate[1:]
                if stripped:
                    candidates.add(stripped)
                    next_frontier.add(stripped)
        frontier = next_frontier
    return tuple(sorted(candidates))


def _is_izhar_mutlaq_lexeme(stream: CanonicalTokenStream, word_index: int) -> bool:
    letters = _word_letters(stream, word_index)
    return bool(IZHAR_MUTLAQ_LEXEMES.intersection(_lexeme_candidates(letters)))


def _iter_triggers(stream: CanonicalTokenStream) -> Iterable[Trigger]:
    for item in stream.iter_letters():
        if item.folded_base == "ن" and (
            item.has_sukun or MarkTag.IQLAB in item.mark_tags
        ):
            yield Trigger(item, "nun_sakinah")
        elif item.has_tanwin or MarkTag.IQLAB in item.mark_tags:
            yield Trigger(item, "tanwin_or_iqlab_sign")


def _rule_for_target(
    trigger: Trigger,
    target: CanonicalGrapheme,
    *,
    same_word: bool,
    stream: CanonicalTokenStream,
) -> tuple[Optional[str], Optional[str]]:
    actual = target.base_letter or ""
    folded = target.folded_base or actual

    if same_word and folded in {"ي", "و"}:
        if trigger.trigger_type == "nun_sakinah" and _is_izhar_mutlaq_lexeme(
            stream, trigger.grapheme.word_index
        ):
            return "izhar_mutlaq", None
        return None, "same_word_nun_before_yaw_waw_not_in_verified_lexicon"

    if actual in HAMZA_BASES or folded in HALQI_BASES:
        return "izhar_halqi", None
    if folded == IQLAB_TARGET:
        return "iqlab", None
    if folded in IKHFA_HAQIQI:
        return "ikhfa_haqiqi", None
    if folded in IDGHAM_BILA_GHUNNAH:
        if same_word:
            return None, "same_word_idgham_bila_not_supported"
        return "idgham_bilaghunnah", None
    if folded in IDGHAM_GHUNNAH:
        if same_word:
            return None, "same_word_idgham_ghunnah_not_supported"
        return "idgham_bighunnah", None
    return None, "following_letter_outside_nun_tanwin_taxonomy"


def _make_annotation(
    stream: CanonicalTokenStream,
    trigger: Trigger,
    target: CanonicalGrapheme,
    rule_code: str,
    support_letter: Optional[CanonicalGrapheme] = None,
) -> TajwidAnnotationV3:
    trigger_item = trigger.grapheme
    same_word = trigger_item.word_index == target.word_index
    applies_when = AppliesWhen.BOTH if same_word else AppliesWhen.WASL
    rule_spec = get_rule_spec(rule_code)

    trigger_span = make_text_span(stream, trigger_item.index, trigger_item.index + 1)
    context_span = make_text_span(stream, trigger_item.index, target.index + 1)
    display_span = context_span

    return TajwidAnnotationV3(
        rule_code=rule_code,
        trigger_span=trigger_span,
        context_span=context_span,
        display_span=display_span,
        word_index=trigger_item.word_index,
        next_word_index=(target.word_index if not same_word else None),
        applies_when=applies_when,
        evidence={
            "trigger_type": trigger.trigger_type,
            "trigger_letter": trigger_item.base_letter,
            "following_letter": target.base_letter,
            "following_folded_letter": target.folded_base,
            "same_word": same_word,
            "trigger_grapheme_index": trigger_item.index,
            "target_grapheme_index": target.index,
            "target_has_shadda": target.has_shadda,
            "orthographic_support_letter": (
                support_letter.text if support_letter is not None else None
            ),
        },
        expected_features=dict(rule_spec.expected_features),
        confidence=(0.99 if rule_code == "izhar_mutlaq" else 1.0),
        detector_id=DETECTOR_ID,
    )


def _resolve_following_letter(
    stream: CanonicalTokenStream,
    trigger: Trigger,
) -> tuple[Optional[CanonicalGrapheme], Optional[CanonicalGrapheme]]:
    """Resolve the pronounced target after nun/tanwin.

    Fathatan may be followed by an orthographic support alif or alif maqsura
    in the same word (for example ``خَيْرًا``). That letter is preserved in
    the context/display span but is not the phonological target of the rule.
    """

    first = stream.next_letter(trigger.grapheme.index)
    if first is None:
        return None, None

    has_fathatan = MarkTag.FATHATAN in trigger.grapheme.mark_tags
    is_support_letter = (
        has_fathatan
        and first.word_index == trigger.grapheme.word_index
        and first.is_word_end
        and first.base_letter in {"ا", "ى"}
    )
    if not is_support_letter:
        return first, None
    return stream.next_letter(first.index), first


class NunTanwinDetector:
    detector_id = DETECTOR_ID
    supported_rule_codes = SUPPORTED_RULE_CODES

    def detect(
        self,
        stream: CanonicalTokenStream,
        *,
        reading_mode: ReadingMode,
    ) -> DetectorOutput:
        annotations = []
        issues = []

        for trigger in _iter_triggers(stream):
            item = trigger.grapheme
            if item.word_index is None:
                issues.append(
                    DetectorIssue(
                        issue_type="trigger_without_word",
                        severity="error",
                        grapheme_index=item.index,
                        word_index=None,
                        detail="Trigger nun/tanwin tidak terpetakan ke WordToken.",
                        evidence={"text": item.text},
                    )
                )
                continue

            target, support_letter = _resolve_following_letter(stream, trigger)
            if target is None:
                # Tanwin/nun at the end of the supplied text is governed by
                # waqf, so no cross-word nun/tanwin rule is emitted.
                continue

            if target.base_letter == HAMZAT_WASL:
                issues.append(
                    DetectorIssue(
                        issue_type="hamzat_wasl_target_deferred",
                        severity="warning",
                        grapheme_index=item.index,
                        word_index=item.word_index,
                        detail=(
                            "Target berikutnya hamzat wasl. Klasifikasi ditunda "
                            "sampai pronunciation resolver v3 tersedia."
                        ),
                        evidence={
                            "trigger": item.text,
                            "target": target.text,
                            "reading_mode": reading_mode.value,
                            "support_letter": (support_letter.text if support_letter else None),
                        },
                    )
                )
                continue

            same_word = item.word_index == target.word_index
            if trigger.trigger_type == "tanwin_or_iqlab_sign" and same_word:
                issues.append(
                    DetectorIssue(
                        issue_type="tanwin_not_at_word_boundary",
                        severity="warning",
                        grapheme_index=item.index,
                        word_index=item.word_index,
                        detail="Tanwin ditemukan sebelum huruf lain dalam WordToken yang sama.",
                        evidence={"trigger": item.text, "target": target.text},
                    )
                )
                continue

            rule_code, deferred_reason = _rule_for_target(
                trigger,
                target,
                same_word=same_word,
                stream=stream,
            )
            if rule_code is None:
                if deferred_reason and deferred_reason != "following_letter_outside_nun_tanwin_taxonomy":
                    issues.append(
                        DetectorIssue(
                            issue_type="nun_tanwin_classification_deferred",
                            severity="warning",
                            grapheme_index=item.index,
                            word_index=item.word_index,
                            detail=deferred_reason,
                            evidence={
                                "trigger": item.text,
                                "target": target.text,
                                "same_word": same_word,
                            },
                        )
                    )
                continue

            annotations.append(
                _make_annotation(
                    stream, trigger, target, rule_code, support_letter=support_letter
                )
            )

        return DetectorOutput(
            annotations=tuple(annotations),
            issues=tuple(issues),
        )
