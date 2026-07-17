from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from .grapheme_parser import GraphemeKind
from .token_stream import build_token_stream


@dataclass(frozen=True, slots=True)
class ParserAuditIssue:
    key: str
    issue_type: str
    detail: str


@dataclass(slots=True)
class ParserAuditReport:
    total_texts: int = 0
    passed_texts: int = 0
    failed_texts: int = 0
    total_graphemes: int = 0
    total_words: int = 0
    kind_counts: Counter = field(default_factory=Counter)
    issues: List[ParserAuditIssue] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.failed_texts == 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "total_texts": self.total_texts,
            "passed_texts": self.passed_texts,
            "failed_texts": self.failed_texts,
            "total_graphemes": self.total_graphemes,
            "total_words": self.total_words,
            "kind_counts": dict(sorted(self.kind_counts.items())),
            "issues": [
                {
                    "key": item.key,
                    "issue_type": item.issue_type,
                    "detail": item.detail,
                }
                for item in self.issues
            ],
            "success": self.success,
        }


def audit_texts(items: Iterable[Tuple[str, str]]) -> ParserAuditReport:
    report = ParserAuditReport()
    for key, text in items:
        report.total_texts += 1
        try:
            stream = build_token_stream(text)
            issues = stream.validate_integrity()
            if issues:
                raise ValueError(",".join(issues))
            report.passed_texts += 1
            report.total_graphemes += len(stream.graphemes)
            report.total_words += len(stream.words)
            for item in stream.graphemes:
                report.kind_counts[item.kind.value] += 1
        except Exception as exc:
            report.failed_texts += 1
            report.issues.append(
                ParserAuditIssue(
                    key=key,
                    issue_type="parser_exception",
                    detail=str(exc),
                )
            )
    return report
