from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

from .gold_schema import (
    CaseKind,
    GOLD_DATASET_SCHEMA_VERSION,
    GoldCase,
    GoldDataset,
    ReviewStatus,
    resolve_text_span,
)
from .rule_specs import RULE_SPECS
from .specification import (
    DEFAULT_RECITATION_PROFILE_ID,
    DetectionMaturity,
    SOURCE_REFERENCES,
    SPECIFICATION_VERSION,
    TajwidRuleSpec,
)


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class GoldValidationIssue:
    severity: IssueSeverity
    issue_type: str
    message: str
    case_id: str = ""
    rule_code: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "severity": self.severity.value,
            "issue_type": self.issue_type,
            "message": self.message,
            "case_id": self.case_id,
            "rule_code": self.rule_code,
        }


@dataclass(frozen=True, slots=True)
class RuleCoverage:
    rule_code: str
    maturity: str
    positive: int
    negative: int
    exception: int
    boundary: int
    candidate: int
    reference: int
    expert_verified: int
    verified_positive: int
    verified_negative: int
    verified_exception: int
    verified_candidate_or_reference: int
    structural_gate_passed: bool
    production_gate_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_code": self.rule_code,
            "maturity": self.maturity,
            "positive": self.positive,
            "negative": self.negative,
            "exception": self.exception,
            "boundary": self.boundary,
            "candidate": self.candidate,
            "reference": self.reference,
            "expert_verified": self.expert_verified,
            "verified_positive": self.verified_positive,
            "verified_negative": self.verified_negative,
            "verified_exception": self.verified_exception,
            "verified_candidate_or_reference": self.verified_candidate_or_reference,
            "structural_gate_passed": self.structural_gate_passed,
            "production_gate_passed": self.production_gate_passed,
        }


@dataclass(frozen=True, slots=True)
class GoldValidationReport:
    dataset_version: str
    total_cases: int
    error_count: int
    warning_count: int
    expert_verified_cases: int
    structural_ready: bool
    detector_development_ready: bool
    production_ready: bool
    issues: Tuple[GoldValidationIssue, ...]
    coverage: Tuple[RuleCoverage, ...]
    resolved_cases: Tuple[Dict[str, Any], ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_version": self.dataset_version,
            "total_cases": self.total_cases,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "expert_verified_cases": self.expert_verified_cases,
            "structural_ready": self.structural_ready,
            "detector_development_ready": self.detector_development_ready,
            "production_ready": self.production_ready,
            "issues": [issue.to_dict() for issue in self.issues],
            "coverage": [item.to_dict() for item in self.coverage],
        }


def _case_semantic_issues(case: GoldCase) -> List[GoldValidationIssue]:
    issues: List[GoldValidationIssue] = []
    expected_codes = {item.rule_code for item in case.expected}
    forbidden = set(case.forbidden_rules)

    if expected_codes & forbidden:
        issues.append(
            GoldValidationIssue(
                IssueSeverity.ERROR,
                "expected_forbidden_conflict",
                f"Rule muncul di expected dan forbidden: {sorted(expected_codes & forbidden)}",
                case.case_id,
                case.rule_under_test,
            )
        )

    if case.kind in {CaseKind.POSITIVE, CaseKind.BOUNDARY, CaseKind.REFERENCE}:
        if case.rule_under_test not in expected_codes:
            issues.append(
                GoldValidationIssue(
                    IssueSeverity.ERROR,
                    "positive_missing_expected_rule",
                    "rule_under_test harus muncul di expected.",
                    case.case_id,
                    case.rule_under_test,
                )
            )

    if case.kind == CaseKind.NEGATIVE:
        if case.rule_under_test not in forbidden:
            issues.append(
                GoldValidationIssue(
                    IssueSeverity.ERROR,
                    "negative_missing_forbidden_rule",
                    "Negative case harus melarang rule_under_test.",
                    case.case_id,
                    case.rule_under_test,
                )
            )

    if case.kind == CaseKind.EXCEPTION:
        if (
            case.rule_under_test not in expected_codes
            and case.rule_under_test not in forbidden
        ):
            issues.append(
                GoldValidationIssue(
                    IssueSeverity.ERROR,
                    "exception_has_no_rule_decision",
                    "Exception case harus menetapkan rule sebagai expected atau forbidden.",
                    case.case_id,
                    case.rule_under_test,
                )
            )

    if case.kind == CaseKind.CANDIDATE:
        if case.review_status not in {
            ReviewStatus.EXPERT_REQUIRED,
            ReviewStatus.EXPERT_VERIFIED,
        }:
            issues.append(
                GoldValidationIssue(
                    IssueSeverity.ERROR,
                    "candidate_review_status_invalid",
                    "Candidate case wajib expert_required atau expert_verified.",
                    case.case_id,
                    case.rule_under_test,
                )
            )

    if not case.source_ids:
        issues.append(
            GoldValidationIssue(
                IssueSeverity.WARNING,
                "missing_sources",
                "Case belum memiliki source_ids.",
                case.case_id,
                case.rule_under_test,
            )
        )

    return issues


def _coverage_gate(rule: TajwidRuleSpec, counts: Counter) -> Tuple[bool, bool]:
    if rule.detection_maturity == DetectionMaturity.CORE_DETERMINISTIC:
        structural = counts[CaseKind.POSITIVE] >= 1 and counts[CaseKind.NEGATIVE] >= 1
        production = (
            structural
            and counts[("verified", CaseKind.POSITIVE)] >= 1
            and counts[("verified", CaseKind.NEGATIVE)] >= 1
        )
    elif rule.detection_maturity == DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS:
        structural = (
            counts[CaseKind.POSITIVE] >= 1
            and counts[CaseKind.NEGATIVE] >= 1
            and counts[CaseKind.EXCEPTION] >= 1
        )
        production = (
            structural
            and counts[("verified", CaseKind.POSITIVE)] >= 1
            and counts[("verified", CaseKind.NEGATIVE)] >= 1
            and counts[("verified", CaseKind.EXCEPTION)] >= 1
        )
    else:
        structural = (
            counts[CaseKind.CANDIDATE] >= 1
            or counts[CaseKind.REFERENCE] >= 1
            or counts[CaseKind.POSITIVE] >= 1
        )
        production = structural and counts["expert_verified"] >= 1
    return structural, production


def validate_gold_dataset(
    dataset: GoldDataset,
    *,
    rules: Mapping[str, TajwidRuleSpec] = RULE_SPECS,
) -> GoldValidationReport:
    issues: List[GoldValidationIssue] = []
    resolved_cases: List[Dict[str, Any]] = []

    if dataset.schema_version != GOLD_DATASET_SCHEMA_VERSION:
        issues.append(
            GoldValidationIssue(
                IssueSeverity.ERROR,
                "schema_version_mismatch",
                f"Expected {GOLD_DATASET_SCHEMA_VERSION}, got {dataset.schema_version}.",
            )
        )
    if dataset.specification_version != SPECIFICATION_VERSION:
        issues.append(
            GoldValidationIssue(
                IssueSeverity.ERROR,
                "specification_version_mismatch",
                f"Expected {SPECIFICATION_VERSION}, got {dataset.specification_version}.",
            )
        )
    if dataset.profile_id != DEFAULT_RECITATION_PROFILE_ID:
        issues.append(
            GoldValidationIssue(
                IssueSeverity.ERROR,
                "profile_mismatch",
                f"Expected profile {DEFAULT_RECITATION_PROFILE_ID}.",
            )
        )

    seen_case_ids = set()
    coverage_counts: MutableMapping[str, Counter] = defaultdict(Counter)

    for case in dataset.cases:
        if case.case_id in seen_case_ids:
            issues.append(
                GoldValidationIssue(
                    IssueSeverity.ERROR,
                    "duplicate_case_id",
                    f"Duplicate case_id: {case.case_id}",
                    case.case_id,
                    case.rule_under_test,
                )
            )
        seen_case_ids.add(case.case_id)

        if case.rule_under_test not in rules:
            issues.append(
                GoldValidationIssue(
                    IssueSeverity.ERROR,
                    "unknown_rule_under_test",
                    "rule_under_test tidak terdaftar pada RULE_SPECS.",
                    case.case_id,
                    case.rule_under_test,
                )
            )
            continue

        unknown_sources = set(case.source_ids) - set(SOURCE_REFERENCES)
        if unknown_sources:
            issues.append(
                GoldValidationIssue(
                    IssueSeverity.ERROR,
                    "unknown_source_id",
                    f"Source tidak dikenal: {sorted(unknown_sources)}",
                    case.case_id,
                    case.rule_under_test,
                )
            )

        issues.extend(_case_semantic_issues(case))
        coverage_counts[case.rule_under_test][case.kind] += 1
        if case.review_status == ReviewStatus.EXPERT_VERIFIED:
            coverage_counts[case.rule_under_test]["expert_verified"] += 1
            coverage_counts[case.rule_under_test][("verified", case.kind)] += 1

        resolved_expectations = []
        for expectation in case.expected:
            if expectation.rule_code not in rules:
                issues.append(
                    GoldValidationIssue(
                        IssueSeverity.ERROR,
                        "unknown_expected_rule",
                        "Expected rule tidak terdaftar.",
                        case.case_id,
                        expectation.rule_code,
                    )
                )
                continue

            try:
                trigger = resolve_text_span(
                    case.text,
                    expectation.trigger,
                    expectation.trigger_occurrence,
                )
                context = (
                    resolve_text_span(
                        case.text,
                        expectation.context,
                        expectation.context_occurrence,
                    )
                    if expectation.context
                    else None
                )
                display = (
                    resolve_text_span(
                        case.text,
                        expectation.display,
                        expectation.display_occurrence,
                    )
                    if expectation.display
                    else None
                )
            except ValueError as exc:
                issues.append(
                    GoldValidationIssue(
                        IssueSeverity.ERROR,
                        "invalid_anchor",
                        str(exc),
                        case.case_id,
                        expectation.rule_code,
                    )
                )
                continue

            resolved_expectations.append(
                {
                    "rule_code": expectation.rule_code,
                    "trigger": trigger.to_dict(),
                    "context": context.to_dict() if context else None,
                    "display": display.to_dict() if display else None,
                    "applies_when": (
                        expectation.applies_when.value
                        if expectation.applies_when is not None
                        else None
                    ),
                    "expected_features": dict(expectation.expected_features),
                }
            )

        resolved_cases.append(
            {
                "case_id": case.case_id,
                "rule_under_test": case.rule_under_test,
                "kind": case.kind.value,
                "review_status": case.review_status.value,
                "text": case.text,
                "expected": resolved_expectations,
                "forbidden_rules": list(case.forbidden_rules),
            }
        )

    coverage: List[RuleCoverage] = []
    for code, rule in rules.items():
        counts = coverage_counts[code]
        structural, production = _coverage_gate(rule, counts)
        coverage.append(
            RuleCoverage(
                rule_code=code,
                maturity=rule.detection_maturity.value,
                positive=counts[CaseKind.POSITIVE],
                negative=counts[CaseKind.NEGATIVE],
                exception=counts[CaseKind.EXCEPTION],
                boundary=counts[CaseKind.BOUNDARY],
                candidate=counts[CaseKind.CANDIDATE],
                reference=counts[CaseKind.REFERENCE],
                expert_verified=counts["expert_verified"],
                verified_positive=counts[("verified", CaseKind.POSITIVE)],
                verified_negative=counts[("verified", CaseKind.NEGATIVE)],
                verified_exception=counts[("verified", CaseKind.EXCEPTION)],
                verified_candidate_or_reference=(
                    counts[("verified", CaseKind.CANDIDATE)]
                    + counts[("verified", CaseKind.REFERENCE)]
                ),
                structural_gate_passed=structural,
                production_gate_passed=production,
            )
        )
        if not structural:
            issues.append(
                GoldValidationIssue(
                    IssueSeverity.ERROR,
                    "rule_coverage_incomplete",
                    "Coverage minimum belum terpenuhi sesuai detection maturity.",
                    rule_code=code,
                )
            )

    error_count = sum(1 for issue in issues if issue.severity == IssueSeverity.ERROR)
    warning_count = sum(
        1 for issue in issues if issue.severity == IssueSeverity.WARNING
    )
    expert_verified_cases = sum(
        1 for case in dataset.cases if case.review_status == ReviewStatus.EXPERT_VERIFIED
    )

    structural_ready = error_count == 0
    detector_development_ready = structural_ready and all(
        item.structural_gate_passed for item in coverage
    )
    production_ready = detector_development_ready and all(
        item.production_gate_passed for item in coverage
    )

    if detector_development_ready and not production_ready:
        issues.append(
            GoldValidationIssue(
                IssueSeverity.WARNING,
                "expert_verification_incomplete",
                "Goldset siap untuk development detector, tetapi belum boleh "
                "menjadi oracle production sebelum review ahli selesai.",
            )
        )
        warning_count += 1

    return GoldValidationReport(
        dataset_version=dataset.dataset_version,
        total_cases=len(dataset.cases),
        error_count=error_count,
        warning_count=warning_count,
        expert_verified_cases=expert_verified_cases,
        structural_ready=structural_ready,
        detector_development_ready=detector_development_ready,
        production_ready=production_ready,
        issues=tuple(issues),
        coverage=tuple(coverage),
        resolved_cases=tuple(resolved_cases),
    )


def write_gold_validation_reports(
    report: GoldValidationReport,
    dataset: GoldDataset,
    output_dir: Path | str,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with (output_path / "tajwid_v3_goldset_summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(report.to_dict(), handle, ensure_ascii=False, indent=2)

    with (output_path / "tajwid_v3_goldset_resolved_cases.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(
            {
                "dataset_version": dataset.dataset_version,
                "cases": list(report.resolved_cases),
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )

    with (output_path / "tajwid_v3_goldset_coverage.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fieldnames = list(report.coverage[0].to_dict()) if report.coverage else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in report.coverage:
            writer.writerow(item.to_dict())

    with (output_path / "tajwid_v3_goldset_issues.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fieldnames = ["severity", "issue_type", "message", "case_id", "rule_code"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for issue in report.issues:
            writer.writerow(issue.to_dict())

    with (output_path / "tajwid_v3_expert_review_queue.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fieldnames = [
            "case_id",
            "rule_under_test",
            "kind",
            "text",
            "reading_mode",
            "verse_key",
            "boundary_to_verse_key",
            "review_status",
            "expected_rules",
            "forbidden_rules",
            "source_ids",
            "notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in dataset.cases:
            if case.review_status == ReviewStatus.EXPERT_VERIFIED:
                continue
            writer.writerow(
                {
                    "case_id": case.case_id,
                    "rule_under_test": case.rule_under_test,
                    "kind": case.kind.value,
                    "text": case.text,
                    "reading_mode": case.reading_mode.value,
                    "verse_key": case.verse_key or "",
                    "boundary_to_verse_key": case.boundary_to_verse_key or "",
                    "review_status": case.review_status.value,
                    "expected_rules": ",".join(item.rule_code for item in case.expected),
                    "forbidden_rules": ",".join(case.forbidden_rules),
                    "source_ids": ",".join(case.source_ids),
                    "notes": case.notes,
                }
            )
