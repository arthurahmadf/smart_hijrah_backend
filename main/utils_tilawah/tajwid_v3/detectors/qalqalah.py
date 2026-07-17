from __future__ import annotations

from typing import Optional

from ..annotations import TajwidAnnotationV3, make_text_span
from ..grapheme_parser import CanonicalGrapheme
from ..rule_specs import get_rule_spec
from ..specification import AppliesWhen, ReadingMode
from ..token_stream import CanonicalTokenStream
from .base import DetectorIssue, DetectorOutput


DETECTOR_ID = "qalqalah_detector_v3.0.0-alpha.1"
SUPPORTED_RULE_CODES = frozenset(
    {
        "qalqalah_sughra",
        "qalqalah_kubra",
        "qalqalah_akbar",
    }
)
QALQALAH_LETTERS = frozenset({"ق", "ط", "ب", "ج", "د"})


def _last_letter(stream: CanonicalTokenStream) -> Optional[CanonicalGrapheme]:
    for item in reversed(stream.graphemes):
        if item.is_letter:
            return item
    return None


def _is_actual_stop_position(
    item: CanonicalGrapheme,
    final_letter: Optional[CanonicalGrapheme],
    reading_mode: ReadingMode,
) -> bool:
    return bool(
        final_letter is not None
        and item.index == final_letter.index
        and reading_mode in {ReadingMode.AYAH_STOP, ReadingMode.WAQF}
    )


def _make_annotation(
    stream: CanonicalTokenStream,
    trigger: CanonicalGrapheme,
    rule_code: str,
    *,
    stop_origin: str,
) -> TajwidAnnotationV3:
    rule_spec = get_rule_spec(rule_code)
    span = make_text_span(stream, trigger.index, trigger.index + 1)
    applies_when = (
        AppliesWhen.WAQF
        if rule_code in {"qalqalah_kubra", "qalqalah_akbar"}
        else AppliesWhen.BOTH
    )
    strength = {
        "qalqalah_sughra": "light",
        "qalqalah_kubra": "strong",
        "qalqalah_akbar": "strongest",
    }[rule_code]
    return TajwidAnnotationV3(
        rule_code=rule_code,
        trigger_span=span,
        context_span=span,
        display_span=span,
        word_index=trigger.word_index,
        next_word_index=None,
        applies_when=applies_when,
        evidence={
            "trigger_type": "qalqalah_letter",
            "trigger_letter": trigger.base_letter,
            "trigger_folded_letter": trigger.folded_base,
            "trigger_grapheme_index": trigger.index,
            "has_explicit_sukun": trigger.has_sukun,
            "has_shadda": trigger.has_shadda,
            "is_word_end": trigger.is_word_end,
            "stop_origin": stop_origin,
            "release_strength": strength,
            "taxonomy_status": (
                "provisional_expert_review"
                if rule_code == "qalqalah_akbar"
                else "deterministic_text_condition"
            ),
        },
        expected_features=dict(rule_spec.expected_features),
        confidence=(0.95 if rule_code == "qalqalah_akbar" else 1.0),
        detector_id=DETECTOR_ID,
        notes=(
            "Label qalqalah_akbar tetap provisional sampai review ahli, "
            "meskipun posisi huruf dan shadda terdeteksi deterministik."
            if rule_code == "qalqalah_akbar"
            else ""
        ),
    )


class QalqalahDetector:
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
        final_letter = _last_letter(stream)

        for trigger in stream.iter_letters():
            if trigger.folded_base not in QALQALAH_LETTERS:
                continue

            if trigger.word_index is None:
                issues.append(
                    DetectorIssue(
                        issue_type="trigger_without_word",
                        severity="error",
                        grapheme_index=trigger.index,
                        word_index=None,
                        detail="Huruf qalqalah tidak terpetakan ke WordToken.",
                        evidence={"text": trigger.text},
                    )
                )
                continue

            if trigger.has_sukun and trigger.has_shadda:
                issues.append(
                    DetectorIssue(
                        issue_type="conflicting_sukun_shadda",
                        severity="error",
                        grapheme_index=trigger.index,
                        word_index=trigger.word_index,
                        detail=(
                            "Huruf qalqalah memiliki sukun dan shadda eksplisit "
                            "sekaligus; teks perlu diperiksa."
                        ),
                        evidence={"text": trigger.text},
                    )
                )
                continue

            is_stop = _is_actual_stop_position(
                trigger,
                final_letter,
                reading_mode,
            )

            if is_stop:
                if trigger.has_shadda:
                    annotations.append(
                        _make_annotation(
                            stream,
                            trigger,
                            "qalqalah_akbar",
                            stop_origin="waqf_on_mushaddad_final",
                        )
                    )
                else:
                    annotations.append(
                        _make_annotation(
                            stream,
                            trigger,
                            "qalqalah_kubra",
                            stop_origin=(
                                "original_sukun_at_waqf"
                                if trigger.has_sukun
                                else "acquired_sukun_by_waqf"
                            ),
                        )
                    )
                # Waqf classification replaces sughra at the same locus.
                continue

            # Conservative v3 policy: only explicit original sukun is emitted
            # as sughra. A mushaddad qalqalah letter during wasl is not coloured
            # until the expert-reviewed phonological policy is finalised.
            if trigger.has_sukun and not trigger.has_shadda:
                annotations.append(
                    _make_annotation(
                        stream,
                        trigger,
                        "qalqalah_sughra",
                        stop_origin="original_sukun_continued",
                    )
                )

        return DetectorOutput(
            annotations=tuple(annotations),
            issues=tuple(issues),
        )
