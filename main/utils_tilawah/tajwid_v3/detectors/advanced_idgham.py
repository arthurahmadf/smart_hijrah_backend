from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..annotations import TajwidAnnotationV3, make_text_span
from ..grapheme_parser import CanonicalGrapheme, HAMZAT_WASL, MarkTag
from ..rule_specs import get_rule_spec
from ..specification import AppliesWhen, ReadingMode
from ..token_stream import CanonicalTokenStream
from .base import DetectorIssue, DetectorOutput


DETECTOR_ID = "advanced_idgham_detector_v3.0.0-alpha.1"
SUPPORTED_RULE_CODES = frozenset(
    {
        "idgham_mutamathilain",
        "idgham_mutajanisain",
        "idgham_mutaqaribain",
    }
)

# Exact-pair tables for Hafs 'an 'Asim through al-Shatibiyyah. These are
# deliberately conservative: proximity of articulation alone is not enough.
MUTAJANISAIN_PAIRS = frozenset(
    {
        ("ت", "د"),
        ("د", "ت"),
        ("ت", "ط"),
        ("ط", "ت"),
        ("ث", "ذ"),
        ("ذ", "ظ"),
        ("ب", "م"),
    }
)

MUTAQARIBAIN_PAIRS = frozenset(
    {
        ("ل", "ر"),
        ("ق", "ك"),
    }
)

# These specialised families are already handled by dedicated detectors and
# must not be duplicated as generic mutamathilain.
SPECIALISED_IDENTICAL_PAIRS = frozenset({("م", "م"), ("ن", "ن")})

# Haa as-sakt at the Al-Haaqqah boundary has profile-specific choices and will
# be resolved together with saktah/waqf in Stage 5L.
HAA_SAKT_WORD_KEYS = frozenset({"ماليه", "سلطانيه"})


@dataclass(frozen=True, slots=True)
class _PairDecision:
    rule_code: str
    confidence: float
    evidence: dict[str, object]
    expected_features: dict[str, object]


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


def _word_key(stream: CanonicalTokenStream, word_index: int) -> str:
    word = stream.word(word_index)
    return "".join(
        stream.grapheme(index).folded_base
        or stream.grapheme(index).base_letter
        or ""
        for index in word.letter_indices
    )


def _is_madd_letter_trigger(
    stream: CanonicalTokenStream,
    trigger: CanonicalGrapheme,
) -> bool:
    """Return True when waw/ya is a madd carrier, not an idgham consonant.

    A waw sakin after dammah and ya sakin after kasrah retain their madd and
    must not be swallowed by the generic identical-letter rule. Waw/ya leen
    after fathah are not excluded here because classical descriptions permit
    idgham for the leen consonant relation.
    """

    folded = trigger.folded_base or trigger.base_letter or ""
    if folded == "ا":
        return True
    if folded not in {"و", "ي"}:
        return False
    previous = stream.previous_letter(trigger.index, same_word_only=True)
    if previous is None:
        return False
    previous_vowel = _vowel_class(previous)
    return (folded == "و" and previous_vowel == "damma") or (
        folded == "ي" and previous_vowel == "kasra"
    )


def _target_is_vocalised(target: CanonicalGrapheme) -> bool:
    return target.has_short_vowel or target.has_tanwin or target.has_shadda


def _classify_pair(
    stream: CanonicalTokenStream,
    trigger: CanonicalGrapheme,
    target: CanonicalGrapheme,
    *,
    verse_key: str | None,
) -> _PairDecision | None:
    left = trigger.folded_base or trigger.base_letter or ""
    right = target.folded_base or target.base_letter or ""
    pair = (left, right)

    if pair in SPECIALISED_IDENTICAL_PAIRS:
        return None

    if left == right:
        if _is_madd_letter_trigger(stream, trigger):
            return None
        features = dict(get_rule_spec("idgham_mutamathilain").expected_features)
        if left in {"و", "ي"}:
            features.update(
                {
                    "assimilation_completeness": "complete",
                    "trigger_type": "leen_consonant",
                }
            )
        return _PairDecision(
            rule_code="idgham_mutamathilain",
            confidence=1.0,
            evidence={
                "pair": [left, right],
                "relationship": "same_letter",
                "verse_key": verse_key,
            },
            expected_features=features,
        )

    if pair in MUTAJANISAIN_PAIRS:
        features = dict(get_rule_spec("idgham_mutajanisain").expected_features)
        completeness = "complete"
        confidence = 0.97
        if pair == ("ط", "ت"):
            # The articulation of ط is merged while its itbaq/isti'la quality is
            # retained. This is traditionally taught as incomplete idgham.
            completeness = "incomplete"
            confidence = 0.95
            features.update(
                {
                    "retained_feature": "itbaq_istila",
                    "assimilation_completeness": completeness,
                }
            )
        elif pair == ("ب", "م"):
            features.update(
                {
                    "nasalization": True,
                    "nominal_harakat": 2,
                    "assimilation_completeness": completeness,
                }
            )
        else:
            features["assimilation_completeness"] = completeness
        return _PairDecision(
            rule_code="idgham_mutajanisain",
            confidence=confidence,
            evidence={
                "pair": [left, right],
                "relationship": "same_makhraj_different_sifat",
                "assimilation_completeness": completeness,
                "verse_key": verse_key,
            },
            expected_features=features,
        )

    if pair in MUTAQARIBAIN_PAIRS:
        features = dict(get_rule_spec("idgham_mutaqaribain").expected_features)
        confidence = 0.97
        evidence: dict[str, object] = {
            "pair": [left, right],
            "relationship": "close_makhraj_or_sifat",
            "verse_key": verse_key,
        }
        if pair == ("ق", "ك"):
            # In أَلَمْ نَخْلُقكُّم the performance tradition records complete
            # and incomplete faces. The engine stores both rather than falsely
            # forcing a single acoustic target before expert calibration.
            confidence = 0.92
            evidence.update(
                {
                    "allowed_assimilation_faces": ["complete", "incomplete"],
                    "preferred_face": "complete",
                    "retained_feature_for_incomplete_face": "istila",
                }
            )
            features.update(
                {
                    "allowed_assimilation_faces": ["complete", "incomplete"],
                    "preferred_face": "complete",
                }
            )
        else:
            features["assimilation_completeness"] = "complete"
        return _PairDecision(
            rule_code="idgham_mutaqaribain",
            confidence=confidence,
            evidence=evidence,
            expected_features=features,
        )

    return None


def _make_annotation(
    stream: CanonicalTokenStream,
    trigger: CanonicalGrapheme,
    target: CanonicalGrapheme,
    decision: _PairDecision,
) -> TajwidAnnotationV3:
    same_word = trigger.word_index == target.word_index
    trigger_span = make_text_span(stream, trigger.index, trigger.index + 1)
    relation_span = make_text_span(stream, trigger.index, target.index + 1)
    return TajwidAnnotationV3(
        rule_code=decision.rule_code,
        trigger_span=trigger_span,
        context_span=relation_span,
        display_span=relation_span,
        word_index=trigger.word_index,
        next_word_index=(target.word_index if not same_word else None),
        applies_when=AppliesWhen.BOTH if same_word else AppliesWhen.WASL,
        evidence={
            **decision.evidence,
            "trigger_letter": trigger.base_letter,
            "target_letter": target.base_letter,
            "same_word": same_word,
            "trigger_has_sukun": trigger.has_sukun,
            "target_has_shadda": target.has_shadda,
            "trigger_grapheme_index": trigger.index,
            "target_grapheme_index": target.index,
        },
        expected_features=decision.expected_features,
        confidence=decision.confidence,
        detector_id=DETECTOR_ID,
    )


class AdvancedIdghamDetector:
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

        for trigger in stream.iter_letters():
            if not trigger.has_sukun:
                continue
            if trigger.word_index is None:
                issues.append(
                    DetectorIssue(
                        issue_type="advanced_idgham_trigger_without_word",
                        severity="error",
                        grapheme_index=trigger.index,
                        word_index=None,
                        detail="Trigger idgham tidak terpetakan ke WordToken.",
                        evidence={"trigger": trigger.text},
                    )
                )
                continue
            if trigger.has_shadda:
                issues.append(
                    DetectorIssue(
                        issue_type="advanced_idgham_conflicting_sukun_shadda",
                        severity="error",
                        grapheme_index=trigger.index,
                        word_index=trigger.word_index,
                        detail="Trigger memiliki sukun dan shadda sekaligus.",
                        evidence={"trigger": trigger.text},
                    )
                )
                continue

            target = stream.next_letter(trigger.index)
            if target is None or target.word_index is None:
                continue

            same_word = trigger.word_index == target.word_index
            if not same_word and reading_mode == ReadingMode.WAQF:
                continue

            if target.base_letter == HAMZAT_WASL:
                continue

            left = trigger.folded_base or trigger.base_letter or ""
            right = target.folded_base or target.base_letter or ""
            pair = (left, right)
            potential_pair = (
                (left == right and pair not in SPECIALISED_IDENTICAL_PAIRS)
                or pair in MUTAJANISAIN_PAIRS
                or pair in MUTAQARIBAIN_PAIRS
            )
            if not potential_pair:
                continue

            if not _target_is_vocalised(target):
                # A fully vocalised Quran corpus should expose a vowel or
                # shadda on the second letter. Warn only for an actual exact
                # pair, not for every arbitrary letter after a sukun.
                issues.append(
                    DetectorIssue(
                        issue_type="advanced_idgham_target_unvocalised",
                        severity="warning",
                        grapheme_index=target.index,
                        word_index=target.word_index,
                        detail="Target pasangan idgham tidak memiliki vokal/shadda eksplisit.",
                        evidence={
                            "pair": [left, right],
                            "trigger": trigger.text,
                            "target": target.text,
                            "verse_key": self.verse_key,
                        },
                    )
                )
                continue

            if (
                left == "ه"
                and right == "ه"
                and _word_key(stream, trigger.word_index) in HAA_SAKT_WORD_KEYS
            ):
                issues.append(
                    DetectorIssue(
                        issue_type="haa_sakt_idgham_deferred",
                        severity="warning",
                        grapheme_index=trigger.index,
                        word_index=trigger.word_index,
                        detail=(
                            "Hubungan Haa as-sakt ditunda ke Stage 5L agar pilihan saktah/idgham "
                            "tidak diputuskan tanpa boundary profile."
                        ),
                        evidence={
                            "word_key": _word_key(stream, trigger.word_index),
                            "verse_key": self.verse_key,
                        },
                    )
                )
                continue

            decision = _classify_pair(
                stream,
                trigger,
                target,
                verse_key=self.verse_key,
            )
            if decision is None:
                continue
            annotations.append(_make_annotation(stream, trigger, target, decision))

        return DetectorOutput(
            annotations=tuple(annotations),
            issues=tuple(issues),
        )
