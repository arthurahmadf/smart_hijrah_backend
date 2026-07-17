from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, Tuple

from .engine import analyze_tajwid_v3
from .gold_schema import GoldCase, GoldDataset, GoldExpectation, resolve_text_span


@dataclass(frozen=True, slots=True)
class GoldMismatch:
    case_id: str
    mismatch_type: str
    rule_code: str
    detail: str

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "mismatch_type": self.mismatch_type,
            "rule_code": self.rule_code,
            "detail": self.detail,
        }


@dataclass(slots=True)
class GoldEvaluationReport:
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    mismatches: List[GoldMismatch] = field(default_factory=list)
    emitted_rule_counts: Counter = field(default_factory=Counter)

    @property
    def success(self) -> bool:
        return self.failed_cases == 0

    def to_dict(self) -> dict:
        return {
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "success": self.success,
            "emitted_rule_counts": dict(self.emitted_rule_counts),
            "mismatches": [item.to_dict() for item in self.mismatches],
        }


def _span_matches(annotation_span, resolved) -> bool:
    return (
        annotation_span.codepoint_start == resolved.codepoint_start
        and annotation_span.codepoint_end == resolved.codepoint_end
        and annotation_span.text == resolved.text
    )


def _expectation_matches(case: GoldCase, expected: GoldExpectation, annotations) -> bool:
    trigger = resolve_text_span(case.text, expected.trigger, expected.trigger_occurrence)
    context = (
        trigger
        if expected.context is None
        else resolve_text_span(
            case.text,
            expected.context,
            expected.context_occurrence,
        )
    )
    if expected.display is None:
        display = context
    else:
        display = resolve_text_span(
            case.text,
            expected.display,
            expected.display_occurrence,
        )
    for annotation in annotations:
        if annotation.rule_code != expected.rule_code:
            continue
        if not _span_matches(annotation.trigger_span, trigger):
            continue
        if not _span_matches(annotation.context_span, context):
            continue
        if not _span_matches(annotation.display_span, display):
            continue
        if expected.applies_when and annotation.applies_when != expected.applies_when:
            continue
        return True
    return False


def relevant_gold_cases(
    dataset: GoldDataset,
    supported_rule_codes: Iterable[str],
) -> Tuple[GoldCase, ...]:
    supported = frozenset(supported_rule_codes)
    cases = []
    for case in dataset.cases:
        mentioned = {case.rule_under_test, *case.forbidden_rules}
        mentioned.update(item.rule_code for item in case.expected)
        if mentioned.intersection(supported):
            cases.append(case)
    return tuple(cases)


def evaluate_gold_cases(
    cases: Sequence[GoldCase],
    *,
    supported_rule_codes: Iterable[str] | None = None,
) -> GoldEvaluationReport:
    report = GoldEvaluationReport()
    supported = (
        frozenset(supported_rule_codes)
        if supported_rule_codes is not None
        else None
    )
    for case in cases:
        report.total_cases += 1
        result = analyze_tajwid_v3(
            case.text,
            reading_mode=case.reading_mode,
            verse_key=case.verse_key,
            boundary_to_verse_key=case.boundary_to_verse_key,
        )
        emitted = tuple(result.annotations)
        report.emitted_rule_counts.update(item.rule_code for item in emitted)
        case_mismatches = []

        if result.has_errors:
            case_mismatches.append(
                GoldMismatch(
                    case_id=case.case_id,
                    mismatch_type="engine_error",
                    rule_code=case.rule_under_test,
                    detail=str([issue.to_dict() for issue in result.issues if issue.severity == "error"]),
                )
            )

        expected_items = (
            tuple(
                item for item in case.expected
                if supported is None or item.rule_code in supported
            )
        )
        for expected in expected_items:
            if not _expectation_matches(case, expected, emitted):
                case_mismatches.append(
                    GoldMismatch(
                        case_id=case.case_id,
                        mismatch_type="missing_or_span_mismatch",
                        rule_code=expected.rule_code,
                        detail="Expected exact trigger/context/display span tidak ditemukan.",
                    )
                )

        emitted_codes = {item.rule_code for item in emitted}
        for forbidden in case.forbidden_rules:
            if supported is not None and forbidden not in supported:
                continue
            if forbidden in emitted_codes:
                case_mismatches.append(
                    GoldMismatch(
                        case_id=case.case_id,
                        mismatch_type="forbidden_rule_emitted",
                        rule_code=forbidden,
                        detail="Rule yang dilarang oleh gold case terdeteksi.",
                    )
                )

        if case_mismatches:
            report.failed_cases += 1
            report.mismatches.extend(case_mismatches)
        else:
            report.passed_cases += 1
    return report
