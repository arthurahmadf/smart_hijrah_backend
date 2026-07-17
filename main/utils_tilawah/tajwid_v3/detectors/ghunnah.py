from __future__ import annotations

from typing import Iterable

from ..annotations import TajwidAnnotationV3, make_text_span
from ..grapheme_parser import CanonicalGrapheme
from ..rule_specs import get_rule_spec
from ..specification import AppliesWhen, ReadingMode
from ..token_stream import CanonicalTokenStream
from .base import DetectorIssue, DetectorOutput


DETECTOR_ID = "ghunnah_mushaddadah_detector_v3.0.0-alpha.1"
SUPPORTED_RULE_CODES = frozenset({"ghunnah_mushaddadah"})


def _iter_mushaddad_nun_mim(
    stream: CanonicalTokenStream,
) -> Iterable[CanonicalGrapheme]:
    for item in stream.iter_letters():
        if item.folded_base in {"ن", "م"} and item.has_shadda:
            yield item


def _make_annotation(
    stream: CanonicalTokenStream,
    trigger: CanonicalGrapheme,
) -> TajwidAnnotationV3:
    rule_spec = get_rule_spec("ghunnah_mushaddadah")
    span = make_text_span(stream, trigger.index, trigger.index + 1)
    return TajwidAnnotationV3(
        rule_code="ghunnah_mushaddadah",
        trigger_span=span,
        context_span=span,
        display_span=span,
        word_index=trigger.word_index,
        next_word_index=None,
        applies_when=AppliesWhen.BOTH,
        evidence={
            "trigger_type": "nun_or_mim_mushaddad",
            "trigger_letter": trigger.base_letter,
            "trigger_folded_letter": trigger.folded_base,
            "trigger_grapheme_index": trigger.index,
            "has_shadda": True,
            "same_word_rule": True,
        },
        expected_features=dict(rule_spec.expected_features),
        confidence=1.0,
        detector_id=DETECTOR_ID,
    )


class GhunnahMushaddadahDetector:
    detector_id = DETECTOR_ID
    supported_rule_codes = SUPPORTED_RULE_CODES

    def detect(
        self,
        stream: CanonicalTokenStream,
        *,
        reading_mode: ReadingMode,
    ) -> DetectorOutput:
        del reading_mode  # Rule is valid in both wasl and waqf.
        annotations = []
        issues = []

        for trigger in _iter_mushaddad_nun_mim(stream):
            if trigger.word_index is None:
                issues.append(
                    DetectorIssue(
                        issue_type="trigger_without_word",
                        severity="error",
                        grapheme_index=trigger.index,
                        word_index=None,
                        detail="Nun/mim mushaddad tidak terpetakan ke WordToken.",
                        evidence={"text": trigger.text},
                    )
                )
                continue

            if trigger.has_sukun:
                issues.append(
                    DetectorIssue(
                        issue_type="conflicting_sukun_shadda",
                        severity="error",
                        grapheme_index=trigger.index,
                        word_index=trigger.word_index,
                        detail=(
                            "Grapheme nun/mim memiliki sukun dan shadda "
                            "sekaligus; teks perlu diperiksa."
                        ),
                        evidence={"text": trigger.text},
                    )
                )
                continue

            annotations.append(_make_annotation(stream, trigger))

        return DetectorOutput(
            annotations=tuple(annotations),
            issues=tuple(issues),
        )
