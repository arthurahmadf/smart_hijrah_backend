from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Protocol, Tuple

from ..annotations import TajwidAnnotationV3
from ..specification import ReadingMode
from ..token_stream import CanonicalTokenStream


@dataclass(frozen=True, slots=True)
class DetectorIssue:
    issue_type: str
    severity: str
    grapheme_index: int | None
    word_index: int | None
    detail: str
    evidence: Dict[str, object]

    def to_dict(self) -> dict:
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "grapheme_index": self.grapheme_index,
            "word_index": self.word_index,
            "detail": self.detail,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class DetectorOutput:
    annotations: Tuple[TajwidAnnotationV3, ...] = ()
    issues: Tuple[DetectorIssue, ...] = ()


class TajwidDetector(Protocol):
    detector_id: str
    supported_rule_codes: frozenset[str]

    def detect(
        self,
        stream: CanonicalTokenStream,
        *,
        reading_mode: ReadingMode,
    ) -> DetectorOutput:
        ...
