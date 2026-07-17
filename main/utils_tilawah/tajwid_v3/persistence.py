from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping, Sequence

from django.db import transaction
from django.utils import timezone

from main.models_tilawah import (
    LEVEL_CHOICES,
    TajwidAnnotationSetStatus,
    TajwidAssessmentFamily,
    TajwidDefaultAppliesWhen,
    TajwidReadingMode,
    TilawahAyahPool,
    TilawahAyahTajwidAnnotation,
    TilawahAyahTajwidAnnotationSet,
    TilawahTajwidRule,
    calculate_ayah_text_hash,
)

from .db_renderer import DatabaseRenderAnnotation, render_database_annotations
from .display import RULE_DISPLAY_CATALOG, get_rule_display
from .engine import ENGINE_VERSION, TajwidEngineV3Result, analyze_tajwid_v3
from .rule_specs import RULE_SPECS
from .specification import (
    SPECIFICATION_VERSION,
    AppliesWhen,
    ReadingMode,
    get_recitation_profile,
)


PERSISTENCE_VERSION = "3.0.0-alpha.1"

_ENGINE_TO_DB_MODE = {
    ReadingMode.AYAH_STOP: TajwidReadingMode.AYAH,
    ReadingMode.WASL: TajwidReadingMode.WASL,
    ReadingMode.WAQF: TajwidReadingMode.WAQF,
}
_DB_TO_ENGINE_MODE = {
    TajwidReadingMode.AYAH: ReadingMode.AYAH_STOP,
    TajwidReadingMode.WASL: ReadingMode.WASL,
    TajwidReadingMode.WAQF: ReadingMode.WAQF,
}

_ASSESSMENT_FAMILY_MAP = {
    "duration": TajwidAssessmentFamily.DURATION,
    "nasalization_model": TajwidAssessmentFamily.NASALIZATION,
    "release_model": TajwidAssessmentFamily.RELEASE,
    "assimilation_model": TajwidAssessmentFamily.ASSIMILATION,
    "resonance_model": TajwidAssessmentFamily.RESONANCE,
    "articulation_model": TajwidAssessmentFamily.ARTICULATION,
    "pause": TajwidAssessmentFamily.PAUSE,
    "render_only": TajwidAssessmentFamily.RENDER_ONLY,
    "deferred": TajwidAssessmentFamily.RENDER_ONLY,
}


@dataclass(frozen=True, slots=True)
class CatalogSyncSummary:
    created: int
    updated: int
    unchanged: int
    deactivated: int


@dataclass(frozen=True, slots=True)
class PreparedAyahMode:
    ayah: TilawahAyahPool
    db_reading_mode: str
    engine_reading_mode: ReadingMode
    result: TajwidEngineV3Result
    annotations: tuple
    issues: tuple[dict, ...]
    source_text_hash: str
    safe_to_persist: bool


@dataclass(frozen=True, slots=True)
class PersistOutcome:
    ayah_id: int
    verse_key: str
    reading_mode: str
    annotation_set_id: int | None
    annotation_count: int
    action: str
    published: bool
    protected_active_set_id: int | None = None


def _default_applies_when(spec_value: str) -> str:
    if spec_value == AppliesWhen.PROFILE_DEPENDENT.value:
        return TajwidDefaultAppliesWhen.CONTEXTUAL
    return spec_value


def sync_v3_rule_catalog(*, deactivate_unknown: bool = True) -> CatalogSyncSummary:
    """Sinkronkan 44 rule v3 tanpa menghapus historical rule lama."""

    created = updated = unchanged = deactivated = 0
    supported_levels = [value for value, _label in LEVEL_CHOICES]

    with transaction.atomic():
        for code, spec in RULE_SPECS.items():
            display = get_rule_display(code)
            assessment_family = _ASSESSMENT_FAMILY_MAP[
                spec.acoustic_assessment.value
            ]
            expected_features = dict(spec.expected_features)
            expected_features.update(
                {
                    "detection_maturity": spec.detection_maturity.value,
                    "verification_state": spec.verification_state.value,
                    "display_span_policy": spec.display_span_policy.value,
                    "requires_profile": spec.requires_profile,
                    "source_ids": list(spec.source_ids),
                    "spec_applies_when": spec.applies_when.value,
                    "specification_version": SPECIFICATION_VERSION,
                }
            )
            defaults = {
                "name": spec.name,
                "display_group": spec.display_group.value,
                "description": display.description,
                "color": display.color,
                "priority": display.priority,
                "default_applies_when": _default_applies_when(
                    spec.applies_when.value
                ),
                "assessment_family": assessment_family,
                "supported_levels": supported_levels,
                "expected_features": expected_features,
                "is_active": True,
            }
            obj, was_created = TilawahTajwidRule.objects.get_or_create(
                code=code,
                defaults=defaults,
            )
            if was_created:
                created += 1
                continue

            dirty = False
            for field, value in defaults.items():
                if getattr(obj, field) != value:
                    setattr(obj, field, value)
                    dirty = True
            if dirty:
                obj.full_clean()
                obj.save(update_fields=[*defaults.keys(), "updated_at"])
                updated += 1
            else:
                unchanged += 1

        if deactivate_unknown:
            deactivated = TilawahTajwidRule.objects.exclude(
                code__in=RULE_SPECS.keys()
            ).filter(is_active=True).update(is_active=False)

    return CatalogSyncSummary(
        created=created,
        updated=updated,
        unchanged=unchanged,
        deactivated=deactivated,
    )


def boundary_map() -> dict[str, str]:
    profile = get_recitation_profile()
    return {
        item.start_verse_key: item.end_verse_key
        for item in (*profile.mandatory_saktah, *profile.optional_saktah)
        if item.start_verse_key != item.end_verse_key
    }


def _issue_to_dict(issue) -> dict:
    return {
        "issue_type": issue.issue_type,
        "severity": issue.severity,
        "grapheme_index": issue.grapheme_index,
        "word_index": issue.word_index,
        "detail": issue.detail,
        "evidence": dict(issue.evidence),
    }


def _filter_source_issues(result: TajwidEngineV3Result, source_cutoff: int) -> tuple[dict, ...]:
    rows = []
    for issue in result.issues:
        if issue.grapheme_index is not None:
            grapheme = result.stream.grapheme(issue.grapheme_index)
            if grapheme.codepoint_start >= source_cutoff:
                continue
        rows.append(_issue_to_dict(issue))
    return tuple(rows)


def _validate_prepared_render(
    source_text: str,
    annotations: Sequence,
    rule_map: Mapping[str, TilawahTajwidRule],
) -> bool:
    render_items = []
    for item in annotations:
        rule = rule_map[item.rule_code]
        render_items.append(
            DatabaseRenderAnnotation(
                start_grapheme=item.display_span.grapheme_start,
                end_grapheme=item.display_span.grapheme_end,
                rule_code=item.rule_code,
                rule_name=rule.display_group,
                color=rule.color,
                description=rule.description,
                priority=rule.priority,
                confidence=item.confidence,
                is_verified=False,
            )
        )
    rendered = render_database_annotations(source_text, render_items)
    return "".join(item["arabic"] for item in rendered) == source_text


def prepare_ayah_mode(
    ayah: TilawahAyahPool,
    *,
    db_reading_mode: str,
    destination_text: str | None = None,
    rule_map: Mapping[str, TilawahTajwidRule] | None = None,
) -> PreparedAyahMode:
    engine_mode = _DB_TO_ENGINE_MODE[db_reading_mode]
    verse_key = f"{ayah.surah_number}:{ayah.ayah_number}"
    input_text = ayah.ayah_text
    boundary_to = None
    source_cutoff = len(ayah.ayah_text)

    if db_reading_mode == TajwidReadingMode.WASL:
        boundary_to = boundary_map().get(verse_key)
        if boundary_to and destination_text:
            input_text = f"{ayah.ayah_text} {destination_text}"

    result = analyze_tajwid_v3(
        input_text,
        reading_mode=engine_mode,
        verse_key=verse_key,
        boundary_to_verse_key=boundary_to,
    )
    annotations = tuple(
        item
        for item in result.annotations
        if item.trigger_span.codepoint_start < source_cutoff
        and item.display_span.codepoint_end <= source_cutoff
    )
    issues = _filter_source_issues(result, source_cutoff)
    has_error = any(item.get("severity") == "error" for item in issues)

    safe = not has_error
    if safe and rule_map is not None:
        try:
            safe = _validate_prepared_render(ayah.ayah_text, annotations, rule_map)
        except Exception:
            safe = False
            issues = (*issues, {
                "issue_type": "database_render_validation_failed",
                "severity": "error",
                "grapheme_index": None,
                "word_index": None,
                "detail": "Candidate gagal direkonstruksi sebelum persist.",
                "evidence": {},
            })

    return PreparedAyahMode(
        ayah=ayah,
        db_reading_mode=db_reading_mode,
        engine_reading_mode=engine_mode,
        result=result,
        annotations=annotations,
        issues=tuple(issues),
        source_text_hash=calculate_ayah_text_hash(ayah.ayah_text),
        safe_to_persist=safe,
    )


def _is_protected(annotation_set: TilawahAyahTajwidAnnotationSet) -> bool:
    return annotation_set.has_expert_review


def _decimal_confidence(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _annotation_model(
    annotation_set: TilawahAyahTajwidAnnotationSet,
    item,
    rule: TilawahTajwidRule,
    source_text: str,
) -> TilawahAyahTajwidAnnotation:
    display = item.display_span
    metadata = {
        "trigger_span": item.trigger_span.to_dict(),
        "context_span": item.context_span.to_dict(),
        "evidence": dict(item.evidence),
        "detector_id": item.detector_id,
        "profile_id": item.profile_id,
        "specification_version": item.specification_version,
        "annotation_schema_version": item.annotation_schema_version,
        "notes": item.notes,
        "persistence_version": PERSISTENCE_VERSION,
        "source": "tajwid_v3_engine",
    }
    return TilawahAyahTajwidAnnotation(
        annotation_set=annotation_set,
        rule=rule,
        word_index=item.word_index,
        next_word_index=item.next_word_index,
        start_grapheme=display.grapheme_start,
        end_grapheme=display.grapheme_end,
        start_codepoint=display.codepoint_start,
        end_codepoint=display.codepoint_end,
        arabic_segment=source_text[display.codepoint_start:display.codepoint_end],
        applies_when=item.applies_when.value,
        expected_features=dict(item.expected_features),
        locator_confidence=_decimal_confidence(item.confidence),
        locator_method=item.detector_id[:64],
        metadata=metadata,
        is_verified=False,
    )


@transaction.atomic
def persist_prepared_ayah_mode(
    prepared: PreparedAyahMode,
    *,
    publish_beta: bool,
    rule_map: Mapping[str, TilawahTajwidRule],
) -> PersistOutcome:
    ayah = prepared.ayah
    verse_key = f"{ayah.surah_number}:{ayah.ayah_number}"

    annotation_set, _created = (
        TilawahAyahTajwidAnnotationSet.objects.select_for_update().get_or_create(
            ayah=ayah,
            engine_version=ENGINE_VERSION,
            source_text_hash=prepared.source_text_hash,
            reading_mode=prepared.db_reading_mode,
            defaults={
                "status": TajwidAnnotationSetStatus.GENERATED,
                "is_active": False,
            },
        )
    )

    if _is_protected(annotation_set):
        return PersistOutcome(
            ayah_id=ayah.pk,
            verse_key=verse_key,
            reading_mode=prepared.db_reading_mode,
            annotation_set_id=annotation_set.pk,
            annotation_count=annotation_set.annotation_count,
            action="skipped_current_set_expert_protected",
            published=annotation_set.is_active,
            protected_active_set_id=annotation_set.pk,
        )

    if not prepared.safe_to_persist:
        annotation_set.status = TajwidAnnotationSetStatus.FAILED
        annotation_set.is_active = False
        annotation_set.is_safe_to_persist = False
        annotation_set.annotation_count = 0
        annotation_set.issues = list(prepared.issues)
        annotation_set.validated_at = None
        annotation_set.save()
        return PersistOutcome(
            ayah_id=ayah.pk,
            verse_key=verse_key,
            reading_mode=prepared.db_reading_mode,
            annotation_set_id=annotation_set.pk,
            annotation_count=0,
            action="failed_validation",
            published=False,
        )

    annotation_set.annotations.all().delete()
    rows = [
        _annotation_model(
            annotation_set,
            item,
            rule_map[item.rule_code],
            ayah.ayah_text,
        )
        for item in prepared.annotations
    ]
    TilawahAyahTajwidAnnotation.objects.bulk_create(rows, batch_size=1000)

    now = timezone.now()
    annotation_set.status = TajwidAnnotationSetStatus.VALIDATED
    annotation_set.is_active = False
    annotation_set.is_safe_to_persist = True
    annotation_set.annotation_count = len(rows)
    annotation_set.issues = list(prepared.issues)
    annotation_set.validated_at = now
    annotation_set.verified_at = None
    annotation_set.reviewed_by = None
    annotation_set.published_at = None
    annotation_set.save()

    if not publish_beta:
        return PersistOutcome(
            ayah_id=ayah.pk,
            verse_key=verse_key,
            reading_mode=prepared.db_reading_mode,
            annotation_set_id=annotation_set.pk,
            annotation_count=len(rows),
            action="seeded_validated_inactive",
            published=False,
        )

    active_sets = list(
        TilawahAyahTajwidAnnotationSet.objects.select_for_update()
        .filter(
            ayah=ayah,
            reading_mode=prepared.db_reading_mode,
            is_active=True,
        )
        .exclude(pk=annotation_set.pk)
    )
    protected = next((item for item in active_sets if _is_protected(item)), None)
    if protected is not None:
        return PersistOutcome(
            ayah_id=ayah.pk,
            verse_key=verse_key,
            reading_mode=prepared.db_reading_mode,
            annotation_set_id=annotation_set.pk,
            annotation_count=len(rows),
            action="seeded_inactive_active_expert_set_protected",
            published=False,
            protected_active_set_id=protected.pk,
        )

    if active_sets:
        TilawahAyahTajwidAnnotationSet.objects.filter(
            pk__in=[item.pk for item in active_sets]
        ).update(is_active=False)

    annotation_set.status = TajwidAnnotationSetStatus.PUBLISHED
    annotation_set.is_active = True
    annotation_set.published_at = now
    annotation_set.save(
        update_fields=[
            "status",
            "is_active",
            "published_at",
            "updated_at",
        ]
    )
    return PersistOutcome(
        ayah_id=ayah.pk,
        verse_key=verse_key,
        reading_mode=prepared.db_reading_mode,
        annotation_set_id=annotation_set.pk,
        annotation_count=len(rows),
        action="published_beta_candidate",
        published=True,
    )


def load_rule_map() -> dict[str, TilawahTajwidRule]:
    rules = TilawahTajwidRule.objects.filter(
        code__in=RULE_SPECS.keys(),
        is_active=True,
    )
    result = {item.code: item for item in rules}
    missing = sorted(set(RULE_SPECS) - set(result))
    if missing:
        raise RuntimeError(
            "Rule catalog v3 belum sinkron. Missing: " + ", ".join(missing)
        )
    return result


def boundary_destination_for_verse(verse_key: str) -> str | None:
    return boundary_map().get(verse_key)


def destination_text_map() -> dict[str, str]:
    keys = set(boundary_map().values())
    if not keys:
        return {}
    surahs = {int(item.split(":", 1)[0]) for item in keys}
    rows = TilawahAyahPool.objects.filter(surah_number__in=surahs).only(
        "surah_number", "ayah_number", "ayah_text"
    )
    return {
        f"{item.surah_number}:{item.ayah_number}": item.ayah_text
        for item in rows
        if f"{item.surah_number}:{item.ayah_number}" in keys
    }


def supported_db_modes(value: str) -> tuple[str, ...]:
    if value == "both":
        return (TajwidReadingMode.AYAH, TajwidReadingMode.WASL)
    if value in {
        TajwidReadingMode.AYAH,
        TajwidReadingMode.WASL,
        TajwidReadingMode.WAQF,
    }:
        return (value,)
    raise ValueError(f"Mode seed tidak valid: {value}")
