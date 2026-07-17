from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Tuple

from .annotations import TajwidAnnotationV3
from .detectors.base import DetectorIssue
from .rule_specs import RULE_SPECS


ADVANCED_MAD_CODES = frozenset(
    {
        "mad_tamkin",
        "mad_silah_qasirah",
        "mad_silah_tawilah",
        "mad_lazim_harfi_muthaqqal",
        "mad_lazim_harfi_mukhaffaf",
        "mad_harfi_tabii",
        "mad_ayn_muqattaah",
        "mad_farq",
    }
)
CORE_MAD_CODES = frozenset(
    {
        "mad_tabii",
        "mad_badl",
        "mad_iwad",
        "mad_wajib_muttasil",
        "mad_jaiz_munfasil",
        "mad_lazim_kalimi_muthaqqal",
        "mad_lazim_kalimi_mukhaffaf",
        "mad_arid_lissukun",
        "mad_lin",
    }
)

ADVANCED_IDGHAM_CODES = frozenset(
    {
        "idgham_mutamathilain",
        "idgham_mutajanisain",
        "idgham_mutaqaribain",
    }
)
QALQALAH_CODES = frozenset(
    {
        "qalqalah_sughra",
        "qalqalah_kubra",
        "qalqalah_akbar",
    }
)

SAKTAH_CODES = frozenset({"saktah_wajibah", "saktah_jaizah"})
CROSS_BOUNDARY_RULE_CODES = frozenset(
    {
        "izhar_halqi",
        "idgham_bighunnah",
        "idgham_bilaghunnah",
        "iqlab",
        "ikhfa_haqiqi",
        "izhar_shafawi",
        "ikhfa_shafawi",
        "idgham_mimi",
        "idgham_mutamathilain",
        "idgham_mutajanisain",
        "idgham_mutaqaribain",
    }
)

# Rule dalam satu group tidak boleh aktif bersamaan pada trigger span identik.
# Angka lebih kecil menang. Resolver tetap mengeluarkan warning agar konflik
# detector dapat ditelusuri pada audit corpus.
_EXCLUSIVE_PRECEDENCE = {
    "ra_both_permitted": 1,
    "ra_tafkhim": 2,
    "ra_tarqiq": 3,
    "qalqalah_akbar": 1,
    "qalqalah_kubra": 2,
    "qalqalah_sughra": 3,
    "lam_jalalah_tafkhim": 1,
    "lam_jalalah_tarqiq": 2,
    "alif_lam_shamsiyyah": 1,
    "alif_lam_qamariyyah": 2,
}
_EXCLUSIVE_GROUPS = (
    frozenset({"ra_tafkhim", "ra_tarqiq", "ra_both_permitted"}),
    QALQALAH_CODES,
    frozenset({"lam_jalalah_tafkhim", "lam_jalalah_tarqiq"}),
    frozenset({"alif_lam_qamariyyah", "alif_lam_shamsiyyah"}),
)


def _contains(outer, inner) -> bool:
    return (
        outer.grapheme_start <= inner.grapheme_start
        and outer.grapheme_end >= inner.grapheme_end
    )


def _trigger_key(item: TajwidAnnotationV3) -> tuple[int, int]:
    return (
        item.trigger_span.grapheme_start,
        item.trigger_span.grapheme_end,
    )


def _resolve_exclusive_groups(
    items: list[TajwidAnnotationV3],
    issues: list[DetectorIssue],
) -> list[TajwidAnnotationV3]:
    suppressed_ids = set()
    for group in _EXCLUSIVE_GROUPS:
        by_trigger: dict[tuple[int, int], list[TajwidAnnotationV3]] = defaultdict(list)
        for item in items:
            if item.rule_code in group:
                by_trigger[_trigger_key(item)].append(item)
        for trigger, candidates in by_trigger.items():
            codes = {item.rule_code for item in candidates}
            if len(codes) <= 1:
                continue
            winner = min(
                candidates,
                key=lambda item: (
                    _EXCLUSIVE_PRECEDENCE.get(item.rule_code, 999),
                    -item.confidence,
                    item.rule_code,
                ),
            )
            for item in candidates:
                if item is not winner:
                    suppressed_ids.add(id(item))
            issues.append(
                DetectorIssue(
                    issue_type="resolved_mutually_exclusive_rules",
                    severity="warning",
                    grapheme_index=trigger[0],
                    word_index=winner.word_index,
                    detail=(
                        "Beberapa rule mutually-exclusive muncul pada trigger "
                        "yang sama; global resolver memilih satu rule."
                    ),
                    evidence={
                        "candidate_rule_codes": sorted(codes),
                        "selected_rule_code": winner.rule_code,
                        "trigger_grapheme_start": trigger[0],
                        "trigger_grapheme_end": trigger[1],
                    },
                )
            )
    return [item for item in items if id(item) not in suppressed_ids]


def validate_resolved_annotation_set(
    annotations: Iterable[TajwidAnnotationV3],
) -> Tuple[str, ...]:
    """Global invariants setelah seluruh detector dan resolver dijalankan."""
    items = tuple(annotations)
    issues = []
    seen = set()
    for item in items:
        if item.rule_code not in RULE_SPECS:
            issues.append(f"unknown_rule_code:{item.rule_code}")
        key = (
            item.rule_code,
            item.trigger_span.grapheme_start,
            item.trigger_span.grapheme_end,
            item.context_span.grapheme_start,
            item.context_span.grapheme_end,
            item.display_span.grapheme_start,
            item.display_span.grapheme_end,
        )
        if key in seen:
            issues.append(f"duplicate_annotation:{item.rule_code}:{key[1]}:{key[2]}")
        seen.add(key)

    for group in _EXCLUSIVE_GROUPS:
        by_trigger: dict[tuple[int, int], set[str]] = defaultdict(set)
        for item in items:
            if item.rule_code in group:
                by_trigger[_trigger_key(item)].add(item.rule_code)
        for trigger, codes in by_trigger.items():
            if len(codes) > 1:
                issues.append(
                    "unresolved_exclusive_conflict:"
                    f"{trigger[0]}:{trigger[1]}:{','.join(sorted(codes))}"
                )
    return tuple(issues)


def resolve_annotation_conflicts(
    annotations: Iterable[TajwidAnnotationV3],
    issues: Iterable[DetectorIssue],
) -> Tuple[Tuple[TajwidAnnotationV3, ...], Tuple[DetectorIssue, ...]]:
    items = list(annotations)
    issue_items = list(issues)
    advanced = [item for item in items if item.rule_code in ADVANCED_MAD_CODES]
    assimilations = [
        item for item in items if item.rule_code in ADVANCED_IDGHAM_CODES
    ]
    saktaat = [item for item in items if item.rule_code in SAKTAH_CODES]
    kept = []
    for item in items:
        if item.rule_code in CORE_MAD_CODES:
            superseded = any(
                candidate.word_index == item.word_index
                and _contains(candidate.trigger_span, item.trigger_span)
                for candidate in advanced
            )
            if superseded:
                continue
        if (
            item.rule_code in CROSS_BOUNDARY_RULE_CODES
            and item.next_word_index is not None
            and any(
                _contains(saktah.trigger_span, item.trigger_span)
                for saktah in saktaat
            )
        ):
            # Saktah prevents the adjacent letters from meeting; suppress a
            # cross-boundary assimilation/ikhfa/izhar generated at the same
            # trigger, while preserving unrelated rules elsewhere.
            continue
        if item.rule_code in QALQALAH_CODES:
            # A qalqalah letter that is actively merged into the following
            # consonant is not released as qalqalah. Suppress only when the
            # exact trigger grapheme is covered by an Advanced Idgham locus.
            assimilated = any(
                candidate.word_index == item.word_index
                and _contains(candidate.trigger_span, item.trigger_span)
                for candidate in assimilations
            )
            if assimilated:
                continue
        kept.append(item)

    kept = _resolve_exclusive_groups(kept, issue_items)

    covered_saktah_graphemes = set()
    for item in saktaat:
        covered_saktah_graphemes.update(
            range(item.trigger_span.grapheme_start, item.trigger_span.grapheme_end)
        )

    covered_graphemes = set()
    for item in advanced:
        covered_graphemes.update(
            range(item.trigger_span.grapheme_start, item.trigger_span.grapheme_end)
        )
    kept_issues = []
    for issue in issue_items:
        if (
            issue.issue_type == "unresolved_maddah_sign"
            and issue.grapheme_index in covered_graphemes
        ):
            continue
        if (
            issue.issue_type == "haa_sakt_idgham_deferred"
            and issue.grapheme_index in covered_saktah_graphemes
        ):
            continue
        kept_issues.append(issue)
    return tuple(kept), tuple(kept_issues)
