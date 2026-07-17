from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import sqrt
from typing import Iterable


DIFFICULTY_VERSION = "3.0.0-alpha.1"

_GROUP_WEIGHTS = {
    "orthographic": 0.30,
    "alif_lam": 0.45,
    "mad": 0.85,
    "nun_tanwin": 1.00,
    "mim_sakinah": 1.00,
    "ghunnah": 1.05,
    "qalqalah": 1.15,
    "tafkhim_tarqiq": 1.30,
    "idgham": 1.45,
    "waqf": 1.80,
}

_ADVANCED_RULE_BONUS = {
    "izhar_mutlaq": 0.7,
    "mad_farq": 1.5,
    "mad_tamkin": 0.8,
    "mad_silah_qasirah": 0.7,
    "mad_silah_tawilah": 1.0,
    "mad_lazim_harfi_muthaqqal": 1.3,
    "mad_lazim_harfi_mukhaffaf": 1.2,
    "mad_ayn_muqattaah": 1.2,
    "ra_both_permitted": 1.4,
    "idgham_mutajanisain": 1.0,
    "idgham_mutaqaribain": 1.1,
    "idgham_mutamathilain": 0.8,
    "saktah_wajibah": 1.5,
    "saktah_jaizah": 1.4,
}


@dataclass(frozen=True, slots=True)
class DifficultyMetrics:
    raw_score: float
    word_count: int
    annotation_count: int
    unique_rule_count: int
    overlap_count: int
    advanced_rule_count: int
    group_counts: dict[str, int]

    def to_dict(self) -> dict:
        return {
            "difficulty_version": DIFFICULTY_VERSION,
            "raw_score": round(self.raw_score, 6),
            "word_count": self.word_count,
            "annotation_count": self.annotation_count,
            "unique_rule_count": self.unique_rule_count,
            "overlap_count": self.overlap_count,
            "advanced_rule_count": self.advanced_rule_count,
            "group_counts": dict(self.group_counts),
        }


def calculate_raw_difficulty(ayah_text: str, annotations: Iterable) -> DifficultyMetrics:
    items = tuple(annotations)
    word_count = max(1, len((ayah_text or "").split()))
    group_counts: Counter[str] = Counter()
    rule_codes = set()
    span_counts: Counter[tuple[int, int]] = Counter()
    weighted = 0.0
    advanced_count = 0

    for item in items:
        rule = item.rule
        code = str(rule.code)
        group = str(rule.display_group)
        group_counts[group] += 1
        rule_codes.add(code)
        span_counts[(int(item.start_grapheme), int(item.end_grapheme))] += 1
        weighted += _GROUP_WEIGHTS.get(group, 1.0)
        bonus = _ADVANCED_RULE_BONUS.get(code, 0.0)
        weighted += bonus
        if bonus:
            advanced_count += 1

    overlap_count = sum(value - 1 for value in span_counts.values() if value > 1)
    raw_score = (
        weighted / sqrt(word_count)
        + len(rule_codes) * 0.30
        + overlap_count * 0.45
        + advanced_count * 0.20
    )
    return DifficultyMetrics(
        raw_score=raw_score,
        word_count=word_count,
        annotation_count=len(items),
        unique_rule_count=len(rule_codes),
        overlap_count=overlap_count,
        advanced_rule_count=advanced_count,
        group_counts=dict(sorted(group_counts.items())),
    )


def percentile_rank(sorted_values: list[float], value: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return 0.0
    # Mid-rank untuk nilai yang sama agar hasil stabil.
    left = 0
    while left < len(sorted_values) and sorted_values[left] < value:
        left += 1
    right = left
    while right < len(sorted_values) and sorted_values[right] == value:
        right += 1
    rank = (left + max(left, right - 1)) / 2
    return rank / (len(sorted_values) - 1) * 100.0


def level_from_percentile(
    percentile: float,
    *,
    intermediate_from: float = 55.0,
    expert_from: float = 88.0,
) -> str:
    if percentile >= expert_from:
        return "expert"
    if percentile >= intermediate_from:
        return "intermediate"
    return "basic"
