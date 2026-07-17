from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import regex

from .specification import AppliesWhen, ReadingMode


GOLD_DATASET_SCHEMA_VERSION = "1.0.0"
DEFAULT_GOLD_DATASET_VERSION = "1.0.0-alpha.1"


class CaseKind(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    EXCEPTION = "exception"
    BOUNDARY = "boundary"
    CANDIDATE = "candidate"
    REFERENCE = "reference"


class TextOrigin(str, Enum):
    SYNTHETIC_MINIMAL = "synthetic_minimal"
    QURAN_EXCERPT = "quran_excerpt"
    QURAN_BOUNDARY = "quran_boundary"
    EXTERNAL_REFERENCE = "external_reference"


class ReviewStatus(str, Enum):
    SPEC_DERIVED = "spec_derived"
    REFERENCE_CHECKED = "reference_checked"
    EXPERT_REQUIRED = "expert_required"
    EXPERT_VERIFIED = "expert_verified"


@dataclass(frozen=True, slots=True)
class GoldExpectation:
    rule_code: str
    trigger: str
    trigger_occurrence: int = 1
    context: Optional[str] = None
    context_occurrence: int = 1
    display: Optional[str] = None
    display_occurrence: int = 1
    applies_when: Optional[AppliesWhen] = None
    expected_features: Mapping[str, Any] = field(default_factory=dict)
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.rule_code.strip():
            raise ValueError("GoldExpectation.rule_code wajib diisi.")
        if not self.trigger:
            raise ValueError(
                f"GoldExpectation '{self.rule_code}' wajib memiliki trigger."
            )
        for name, value in (
            ("trigger_occurrence", self.trigger_occurrence),
            ("context_occurrence", self.context_occurrence),
            ("display_occurrence", self.display_occurrence),
        ):
            if value < 1:
                raise ValueError(f"{name} harus >= 1.")
        object.__setattr__(
            self,
            "expected_features",
            MappingProxyType(dict(self.expected_features)),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GoldExpectation":
        applies_when = payload.get("applies_when")
        return cls(
            rule_code=str(payload["rule_code"]),
            trigger=str(payload["trigger"]),
            trigger_occurrence=int(payload.get("trigger_occurrence", 1)),
            context=(
                str(payload["context"])
                if payload.get("context") is not None
                else None
            ),
            context_occurrence=int(payload.get("context_occurrence", 1)),
            display=(
                str(payload["display"])
                if payload.get("display") is not None
                else None
            ),
            display_occurrence=int(payload.get("display_occurrence", 1)),
            applies_when=(
                AppliesWhen(applies_when) if applies_when is not None else None
            ),
            expected_features=dict(payload.get("expected_features", {})),
            notes=str(payload.get("notes", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_code": self.rule_code,
            "trigger": self.trigger,
            "trigger_occurrence": self.trigger_occurrence,
            "context": self.context,
            "context_occurrence": self.context_occurrence,
            "display": self.display,
            "display_occurrence": self.display_occurrence,
            "applies_when": (
                self.applies_when.value if self.applies_when is not None else None
            ),
            "expected_features": dict(self.expected_features),
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class GoldCase:
    case_id: str
    rule_under_test: str
    kind: CaseKind
    text: str
    text_origin: TextOrigin
    reading_mode: ReadingMode
    review_status: ReviewStatus
    expected: Tuple[GoldExpectation, ...] = ()
    forbidden_rules: Tuple[str, ...] = ()
    source_ids: Tuple[str, ...] = ()
    verse_key: Optional[str] = None
    boundary_to_verse_key: Optional[str] = None
    source_note: str = ""
    notes: str = ""
    tags: Tuple[str, ...] = ()
    reviewer: Optional[str] = None
    reviewed_at: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id wajib diisi.")
        if not self.rule_under_test.strip():
            raise ValueError(f"Case '{self.case_id}' wajib memiliki rule_under_test.")
        if not self.text:
            raise ValueError(f"Case '{self.case_id}' memiliki text kosong.")
        if self.review_status == ReviewStatus.EXPERT_VERIFIED:
            if not self.reviewer or not self.reviewed_at:
                raise ValueError(
                    f"Case '{self.case_id}' expert_verified wajib memiliki "
                    "reviewer dan reviewed_at."
                )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GoldCase":
        return cls(
            case_id=str(payload["case_id"]),
            rule_under_test=str(payload["rule_under_test"]),
            kind=CaseKind(payload["kind"]),
            text=str(payload["text"]),
            text_origin=TextOrigin(payload["text_origin"]),
            reading_mode=ReadingMode(payload["reading_mode"]),
            review_status=ReviewStatus(payload["review_status"]),
            expected=tuple(
                GoldExpectation.from_dict(item)
                for item in payload.get("expected", [])
            ),
            forbidden_rules=tuple(payload.get("forbidden_rules", [])),
            source_ids=tuple(payload.get("source_ids", [])),
            verse_key=payload.get("verse_key"),
            boundary_to_verse_key=payload.get("boundary_to_verse_key"),
            source_note=str(payload.get("source_note", "")),
            notes=str(payload.get("notes", "")),
            tags=tuple(payload.get("tags", [])),
            reviewer=payload.get("reviewer"),
            reviewed_at=payload.get("reviewed_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "rule_under_test": self.rule_under_test,
            "kind": self.kind.value,
            "text": self.text,
            "text_origin": self.text_origin.value,
            "reading_mode": self.reading_mode.value,
            "review_status": self.review_status.value,
            "expected": [item.to_dict() for item in self.expected],
            "forbidden_rules": list(self.forbidden_rules),
            "source_ids": list(self.source_ids),
            "verse_key": self.verse_key,
            "boundary_to_verse_key": self.boundary_to_verse_key,
            "source_note": self.source_note,
            "notes": self.notes,
            "tags": list(self.tags),
            "reviewer": self.reviewer,
            "reviewed_at": self.reviewed_at,
        }


@dataclass(frozen=True, slots=True)
class GoldDataset:
    schema_version: str
    dataset_version: str
    specification_version: str
    profile_id: str
    status: str
    description: str
    cases: Tuple[GoldCase, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GoldDataset":
        return cls(
            schema_version=str(payload["schema_version"]),
            dataset_version=str(payload["dataset_version"]),
            specification_version=str(payload["specification_version"]),
            profile_id=str(payload["profile_id"]),
            status=str(payload["status"]),
            description=str(payload.get("description", "")),
            cases=tuple(GoldCase.from_dict(item) for item in payload["cases"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dataset_version": self.dataset_version,
            "specification_version": self.specification_version,
            "profile_id": self.profile_id,
            "status": self.status,
            "description": self.description,
            "cases": [case.to_dict() for case in self.cases],
        }


@dataclass(frozen=True, slots=True)
class ResolvedSpan:
    text: str
    occurrence: int
    codepoint_start: int
    codepoint_end: int
    grapheme_start: int
    grapheme_end: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "occurrence": self.occurrence,
            "codepoint_start": self.codepoint_start,
            "codepoint_end": self.codepoint_end,
            "grapheme_start": self.grapheme_start,
            "grapheme_end": self.grapheme_end,
        }


def split_graphemes(text: str) -> Tuple[str, ...]:
    return tuple(regex.findall(r"\X", text))


def _codepoint_to_grapheme_boundaries(text: str) -> Dict[int, int]:
    boundaries: Dict[int, int] = {0: 0}
    codepoint_index = 0
    for grapheme_index, grapheme in enumerate(split_graphemes(text), start=1):
        codepoint_index += len(grapheme)
        boundaries[codepoint_index] = grapheme_index
    return boundaries


def resolve_text_span(text: str, anchor: str, occurrence: int = 1) -> ResolvedSpan:
    if occurrence < 1:
        raise ValueError("occurrence harus >= 1.")
    if not anchor:
        raise ValueError("anchor tidak boleh kosong.")

    start = -1
    cursor = 0
    for _ in range(occurrence):
        start = text.find(anchor, cursor)
        if start < 0:
            raise ValueError(
                f"Anchor {anchor!r} occurrence={occurrence} tidak ditemukan "
                f"di text {text!r}."
            )
        cursor = start + 1

    end = start + len(anchor)
    boundaries = _codepoint_to_grapheme_boundaries(text)
    if start not in boundaries or end not in boundaries:
        raise ValueError(
            f"Anchor {anchor!r} memotong combining mark atau bukan batas "
            "grapheme yang valid."
        )

    return ResolvedSpan(
        text=anchor,
        occurrence=occurrence,
        codepoint_start=start,
        codepoint_end=end,
        grapheme_start=boundaries[start],
        grapheme_end=boundaries[end],
    )


def default_gold_dataset_path(base_dir: Path) -> Path:
    return base_dir / "main" / "data" / "tilawah" / "tajwid_v3_gold_cases.v1.json"
