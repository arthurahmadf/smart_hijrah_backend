from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Tuple

from .specification import (
    AppliesWhen,
    DEFAULT_RECITATION_PROFILE_ID,
    SPECIFICATION_VERSION,
)
from .token_stream import CanonicalTokenStream


ANNOTATION_SCHEMA_VERSION = "3.0.0-alpha.1"


@dataclass(frozen=True, slots=True)
class TextSpan:
    grapheme_start: int
    grapheme_end: int
    codepoint_start: int
    codepoint_end: int
    text: str

    def __post_init__(self) -> None:
        if self.grapheme_start < 0 or self.grapheme_end <= self.grapheme_start:
            raise ValueError("TextSpan grapheme range tidak valid.")
        if self.codepoint_start < 0 or self.codepoint_end <= self.codepoint_start:
            raise ValueError("TextSpan codepoint range tidak valid.")
        if not self.text:
            raise ValueError("TextSpan.text tidak boleh kosong.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "grapheme_start": self.grapheme_start,
            "grapheme_end": self.grapheme_end,
            "codepoint_start": self.codepoint_start,
            "codepoint_end": self.codepoint_end,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class TajwidAnnotationV3:
    rule_code: str
    trigger_span: TextSpan
    context_span: TextSpan
    display_span: TextSpan
    word_index: int
    next_word_index: Optional[int]
    applies_when: AppliesWhen
    evidence: Mapping[str, Any]
    confidence: float
    detector_id: str
    profile_id: str = DEFAULT_RECITATION_PROFILE_ID
    specification_version: str = SPECIFICATION_VERSION
    annotation_schema_version: str = ANNOTATION_SCHEMA_VERSION
    expected_features: Mapping[str, Any] = field(default_factory=dict)
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.rule_code.strip():
            raise ValueError("rule_code wajib diisi.")
        if self.word_index < 0:
            raise ValueError("word_index tidak boleh negatif.")
        if self.next_word_index is not None:
            if self.next_word_index <= self.word_index:
                raise ValueError("next_word_index harus lebih besar dari word_index.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence harus berada pada rentang 0..1.")
        if not self.detector_id.strip():
            raise ValueError("detector_id wajib diisi.")
        object.__setattr__(self, "evidence", MappingProxyType(dict(self.evidence)))
        object.__setattr__(
            self,
            "expected_features",
            MappingProxyType(dict(self.expected_features)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_code": self.rule_code,
            "trigger_span": self.trigger_span.to_dict(),
            "context_span": self.context_span.to_dict(),
            "display_span": self.display_span.to_dict(),
            "word_index": self.word_index,
            "next_word_index": self.next_word_index,
            "applies_when": self.applies_when.value,
            "evidence": dict(self.evidence),
            "confidence": self.confidence,
            "detector_id": self.detector_id,
            "profile_id": self.profile_id,
            "specification_version": self.specification_version,
            "annotation_schema_version": self.annotation_schema_version,
            "expected_features": dict(self.expected_features),
            "notes": self.notes,
        }


def make_text_span(
    stream: CanonicalTokenStream,
    grapheme_start: int,
    grapheme_end: int,
) -> TextSpan:
    codepoint_start, codepoint_end = stream.codepoint_span_for_graphemes(
        grapheme_start,
        grapheme_end,
    )
    text = stream.grapheme_text(grapheme_start, grapheme_end)
    if stream.source_text[codepoint_start:codepoint_end] != text:
        raise ValueError("TextSpan tidak cocok dengan source text.")
    return TextSpan(
        grapheme_start=grapheme_start,
        grapheme_end=grapheme_end,
        codepoint_start=codepoint_start,
        codepoint_end=codepoint_end,
        text=text,
    )


def validate_annotation_against_stream(
    annotation: TajwidAnnotationV3,
    stream: CanonicalTokenStream,
) -> Tuple[str, ...]:
    issues = []
    for name, span in (
        ("trigger", annotation.trigger_span),
        ("context", annotation.context_span),
        ("display", annotation.display_span),
    ):
        try:
            expected = make_text_span(
                stream,
                span.grapheme_start,
                span.grapheme_end,
            )
        except (IndexError, ValueError):
            issues.append(f"{name}_span_out_of_range")
            continue
        if expected != span:
            issues.append(f"{name}_span_mismatch")

    if annotation.word_index >= len(stream.words):
        issues.append("word_index_out_of_range")
    if (
        annotation.next_word_index is not None
        and annotation.next_word_index >= len(stream.words)
    ):
        issues.append("next_word_index_out_of_range")
    return tuple(issues)
