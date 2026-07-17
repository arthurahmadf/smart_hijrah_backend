from __future__ import annotations

from typing import Iterable, Optional

from ..annotations import TajwidAnnotationV3, make_text_span
from ..grapheme_parser import CanonicalGrapheme, HAMZAT_WASL
from ..rule_specs import get_rule_spec
from ..specification import AppliesWhen, ReadingMode
from ..token_stream import CanonicalTokenStream
from .base import DetectorIssue, DetectorOutput


DETECTOR_ID = "mim_sakinah_detector_v3.0.0-alpha.1"

SUPPORTED_RULE_CODES = frozenset(
    {
        "izhar_shafawi",
        "ikhfa_shafawi",
        "idgham_mimi",
    }
)


def _iter_mim_sakinah(stream: CanonicalTokenStream) -> Iterable[CanonicalGrapheme]:
    """Yield only explicit meem-sakinah graphemes.

    Bare meem at a word boundary is deliberately not inferred as sakin. This
    conservative rule avoids false positives across different Uthmani text
    encodings. Script-specific inference may be added later through a verified
    pronunciation resolver.
    """

    for item in stream.iter_letters():
        if item.folded_base == "م" and item.has_sukun:
            yield item


def _classify_target(target: CanonicalGrapheme) -> str:
    folded = target.folded_base or target.base_letter or ""
    if folded == "ب":
        return "ikhfa_shafawi"
    if folded == "م":
        return "idgham_mimi"
    return "izhar_shafawi"


def _make_annotation(
    stream: CanonicalTokenStream,
    trigger: CanonicalGrapheme,
    target: CanonicalGrapheme,
    rule_code: str,
) -> TajwidAnnotationV3:
    same_word = trigger.word_index == target.word_index
    applies_when = AppliesWhen.BOTH if same_word else AppliesWhen.WASL
    rule_spec = get_rule_spec(rule_code)

    trigger_span = make_text_span(stream, trigger.index, trigger.index + 1)
    context_span = make_text_span(stream, trigger.index, target.index + 1)
    if rule_code == "izhar_shafawi":
        # The target proves the classification, while the visibly highlighted
        # locus is the clear meem-sakinah itself.
        display_span = trigger_span
    else:
        display_span = context_span

    return TajwidAnnotationV3(
        rule_code=rule_code,
        trigger_span=trigger_span,
        context_span=context_span,
        display_span=display_span,
        word_index=trigger.word_index,
        next_word_index=(target.word_index if not same_word else None),
        applies_when=applies_when,
        evidence={
            "trigger_type": "mim_sakinah",
            "trigger_letter": trigger.base_letter,
            "following_letter": target.base_letter,
            "following_folded_letter": target.folded_base,
            "same_word": same_word,
            "trigger_grapheme_index": trigger.index,
            "target_grapheme_index": target.index,
            "target_has_shadda": target.has_shadda,
            "labial_caution": (
                "waw_or_fa_after_mim_sakinah"
                if rule_code == "izhar_shafawi"
                and (target.folded_base or target.base_letter) in {"و", "ف"}
                else None
            ),
        },
        expected_features=dict(rule_spec.expected_features),
        confidence=1.0,
        detector_id=DETECTOR_ID,
    )


class MimSakinahDetector:
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

        for trigger in _iter_mim_sakinah(stream):
            if trigger.word_index is None:
                issues.append(
                    DetectorIssue(
                        issue_type="trigger_without_word",
                        severity="error",
                        grapheme_index=trigger.index,
                        word_index=None,
                        detail="Mim sakinah tidak terpetakan ke WordToken.",
                        evidence={"text": trigger.text},
                    )
                )
                continue

            if trigger.has_shadda:
                issues.append(
                    DetectorIssue(
                        issue_type="conflicting_sukun_shadda",
                        severity="error",
                        grapheme_index=trigger.index,
                        word_index=trigger.word_index,
                        detail=(
                            "Grapheme mim memiliki sukun dan shadda sekaligus; "
                            "teks perlu diperiksa sebelum klasifikasi."
                        ),
                        evidence={"text": trigger.text},
                    )
                )
                continue

            target = stream.next_letter(trigger.index)
            if target is None:
                # Mim sakinah at the end of supplied input has no following
                # target, so no contextual meem rule is emitted.
                continue

            same_word = trigger.word_index == target.word_index
            if not same_word and reading_mode == ReadingMode.WAQF:
                # Explicit WAQF means the cross-word relation is not realised.
                continue

            if target.base_letter == HAMZAT_WASL:
                issues.append(
                    DetectorIssue(
                        issue_type="hamzat_wasl_target_deferred",
                        severity="warning",
                        grapheme_index=trigger.index,
                        word_index=trigger.word_index,
                        detail=(
                            "Target setelah mim sakinah adalah hamzat wasl. "
                            "Klasifikasi ditunda sampai pronunciation resolver "
                            "menentukan huruf terucap sesudahnya."
                        ),
                        evidence={
                            "trigger": trigger.text,
                            "target": target.text,
                            "reading_mode": reading_mode.value,
                        },
                    )
                )
                continue

            rule_code = _classify_target(target)
            annotations.append(
                _make_annotation(stream, trigger, target, rule_code)
            )

        return DetectorOutput(
            annotations=tuple(annotations),
            issues=tuple(issues),
        )
