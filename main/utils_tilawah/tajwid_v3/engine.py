from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .annotations import TajwidAnnotationV3, validate_annotation_against_stream
from .detectors import (
    AdvancedIdghamDetector,
    AdvancedMadDetector,
    AlifLamDetector,
    DetectorIssue,
    GhunnahMushaddadahDetector,
    MadDetector,
    MimSakinahDetector,
    NunTanwinDetector,
    OrthographicWaqfDetector,
    QalqalahDetector,
    RaDetector,
    TajwidDetector,
)
from .conflict_resolver import (
    resolve_annotation_conflicts,
    validate_resolved_annotation_set,
)
from .specification import ReadingMode
from .token_stream import CanonicalTokenStream, build_token_stream
from .waqf import WaqfSignHint, extract_waqf_sign_hints


ENGINE_VERSION = "3.0.0-alpha.10"


@dataclass(frozen=True, slots=True)
class TajwidEngineV3Result:
    source_text: str
    reading_mode: ReadingMode
    stream: CanonicalTokenStream
    annotations: Tuple[TajwidAnnotationV3, ...]
    issues: Tuple[DetectorIssue, ...]
    waqf_hints: Tuple[WaqfSignHint, ...]
    engine_version: str = ENGINE_VERSION

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    def to_dict(self) -> dict:
        return {
            "engine_version": self.engine_version,
            "reading_mode": self.reading_mode.value,
            "source_text": self.source_text,
            "annotations": [item.to_dict() for item in self.annotations],
            "issues": [item.to_dict() for item in self.issues],
            "waqf_hints": [item.to_dict() for item in self.waqf_hints],
            "has_errors": self.has_errors,
        }


def _annotation_sort_key(item: TajwidAnnotationV3) -> tuple:
    return (
        item.display_span.grapheme_start,
        item.display_span.grapheme_end,
        item.rule_code,
    )


def analyze_tajwid_v3(
    text: str,
    *,
    reading_mode: ReadingMode | str = ReadingMode.AYAH_STOP,
    detectors: Iterable[TajwidDetector] | None = None,
    verse_key: str | None = None,
    boundary_to_verse_key: str | None = None,
) -> TajwidEngineV3Result:
    resolved_mode = (
        reading_mode if isinstance(reading_mode, ReadingMode) else ReadingMode(reading_mode)
    )
    stream = build_token_stream(text)
    detector_list = tuple(
        detectors
        or (
            NunTanwinDetector(),
            MimSakinahDetector(),
            GhunnahMushaddadahDetector(),
            QalqalahDetector(),
            MadDetector(),
            AdvancedMadDetector(verse_key=verse_key),
            AlifLamDetector(),
            RaDetector(verse_key=verse_key),
            AdvancedIdghamDetector(verse_key=verse_key),
            OrthographicWaqfDetector(
                verse_key=verse_key,
                boundary_to_verse_key=boundary_to_verse_key,
            ),
        )
    )

    annotations = []
    issues = []
    seen = set()

    for detector in detector_list:
        output = detector.detect(stream, reading_mode=resolved_mode)
        issues.extend(output.issues)
        for annotation in output.annotations:
            structural_issues = validate_annotation_against_stream(annotation, stream)
            if structural_issues:
                issues.append(
                    DetectorIssue(
                        issue_type="invalid_annotation_contract",
                        severity="error",
                        grapheme_index=annotation.trigger_span.grapheme_start,
                        word_index=annotation.word_index,
                        detail=",".join(structural_issues),
                        evidence={
                            "rule_code": annotation.rule_code,
                            "detector_id": annotation.detector_id,
                        },
                    )
                )
                continue
            key = (
                annotation.rule_code,
                annotation.trigger_span.grapheme_start,
                annotation.trigger_span.grapheme_end,
                annotation.context_span.grapheme_start,
                annotation.context_span.grapheme_end,
            )
            if key in seen:
                continue
            seen.add(key)
            annotations.append(annotation)

    annotations, issues = resolve_annotation_conflicts(annotations, issues)
    annotations = list(annotations)
    issues = list(issues)
    global_contract_issues = validate_resolved_annotation_set(annotations)
    for detail in global_contract_issues:
        issues.append(
            DetectorIssue(
                issue_type="invalid_global_annotation_set",
                severity="error",
                grapheme_index=None,
                word_index=None,
                detail=detail,
                evidence={"engine_version": ENGINE_VERSION},
            )
        )
    annotations.sort(key=_annotation_sort_key)
    return TajwidEngineV3Result(
        source_text=text,
        reading_mode=resolved_mode,
        stream=stream,
        annotations=tuple(annotations),
        issues=tuple(issues),
        waqf_hints=extract_waqf_sign_hints(stream),
    )
