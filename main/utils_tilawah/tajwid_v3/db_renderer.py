from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Sequence

from .display import REGULAR_DISPLAY
from .token_stream import build_token_stream

logger = logging.getLogger(__name__)

ACTIVE_TAJWID_PREFETCH_ATTR = "_active_tajwid_annotation_sets"
DEFAULT_FRONTEND_READING_MODE = "ayah"


@dataclass(frozen=True, slots=True)
class DatabaseRenderAnnotation:
    start_grapheme: int
    end_grapheme: int
    rule_code: str
    rule_name: str
    color: str
    description: str
    priority: int
    confidence: float
    is_verified: bool


def _annotation_from_model(item) -> DatabaseRenderAnnotation:
    rule = item.rule
    return DatabaseRenderAnnotation(
        start_grapheme=int(item.start_grapheme),
        end_grapheme=int(item.end_grapheme),
        rule_code=str(rule.code),
        rule_name=str(rule.display_group),
        color=str(rule.color),
        description=str(rule.description),
        priority=int(rule.priority),
        confidence=float(item.locator_confidence or Decimal("1")),
        is_verified=bool(item.is_verified),
    )


def _regular_rule(arabic: str) -> dict[str, str]:
    return REGULAR_DISPLAY.to_frontend_dict(arabic)


def _same_signature(left: dict, right: dict) -> bool:
    return all(
        left.get(key) == right.get(key)
        for key in ("rule_name", "color", "rule_description")
    )


def render_database_annotations(
    source_text: str,
    annotations: Iterable[DatabaseRenderAnnotation],
) -> list[dict[str, str]]:
    """Render annotation database menjadi segment frontend yang lossless."""

    if not source_text:
        return []

    stream = build_token_stream(source_text)
    items = tuple(annotations)
    boundaries = {0, len(stream.graphemes)}

    for item in items:
        if (
            item.start_grapheme < 0
            or item.end_grapheme <= item.start_grapheme
            or item.end_grapheme > len(stream.graphemes)
        ):
            raise ValueError(
                f"Rentang annotation database tidak valid: "
                f"{item.rule_code}@{item.start_grapheme}:{item.end_grapheme}"
            )
        boundaries.add(item.start_grapheme)
        boundaries.add(item.end_grapheme)

    raw_segments: list[dict[str, str]] = []
    ordered = sorted(boundaries)
    for start, end in zip(ordered, ordered[1:]):
        if end <= start:
            continue
        arabic = stream.grapheme_text(start, end)
        active = [
            item
            for item in items
            if item.start_grapheme <= start and item.end_grapheme >= end
        ]
        if active:
            primary = min(
                active,
                key=lambda item: (
                    item.priority,
                    item.end_grapheme - item.start_grapheme,
                    -item.confidence,
                    item.rule_code,
                ),
            )
            payload = {
                "rule_name": primary.rule_name,
                "color": primary.color,
                "rule_description": primary.description,
                "arabic": arabic,
            }
        else:
            payload = _regular_rule(arabic)

        if raw_segments and _same_signature(raw_segments[-1], payload):
            raw_segments[-1]["arabic"] += payload["arabic"]
        else:
            raw_segments.append(payload)

    if "".join(item["arabic"] for item in raw_segments) != source_text:
        raise ValueError("Database renderer gagal merekonstruksi ayat.")
    return raw_segments


def _active_set_from_ayah(ayah):
    prefetched = getattr(ayah, ACTIVE_TAJWID_PREFETCH_ATTR, None)
    if prefetched is not None:
        return prefetched[0] if prefetched else None

    return (
        ayah.tajwid_annotation_sets.filter(
            is_active=True,
            reading_mode=DEFAULT_FRONTEND_READING_MODE,
        )
        .prefetch_related("annotations__rule")
        .first()
    )


def frontend_rules_from_ayah(ayah) -> list[dict[str, str]]:
    """Ambil rules aktif; bila belum seed atau data rusak, tampilkan regular."""

    source_text = ayah.ayah_text or ""
    if not source_text:
        return []

    annotation_set = _active_set_from_ayah(ayah)
    if annotation_set is None or annotation_set.is_stale:
        return [_regular_rule(source_text)]

    try:
        annotations = (
            annotation_set.annotations.all()
            if hasattr(annotation_set.annotations, "all")
            else annotation_set.annotations
        )
        return render_database_annotations(
            source_text,
            (_annotation_from_model(item) for item in annotations),
        )
    except Exception:
        logger.exception(
            "Gagal render tajwid DB untuk ayah_id=%s set_id=%s",
            getattr(ayah, "pk", None),
            getattr(annotation_set, "pk", None),
        )
        return [_regular_rule(source_text)]


def active_tajwid_prefetch():
    """Prefetch object reusable untuk mencegah N+1 pada list ayat."""

    from django.db.models import Prefetch
    from main.models_tilawah import (
        TilawahAyahTajwidAnnotation,
        TilawahAyahTajwidAnnotationSet,
    )

    annotation_queryset = TilawahAyahTajwidAnnotation.objects.select_related(
        "rule"
    ).order_by("start_grapheme", "end_grapheme", "rule__priority", "rule__code")

    set_queryset = (
        TilawahAyahTajwidAnnotationSet.objects.filter(
            is_active=True,
            reading_mode=DEFAULT_FRONTEND_READING_MODE,
        )
        .prefetch_related(
            Prefetch("annotations", queryset=annotation_queryset)
        )
        .order_by("-published_at", "-generated_at")
    )
    return Prefetch(
        "tajwid_annotation_sets",
        queryset=set_queryset,
        to_attr=ACTIVE_TAJWID_PREFETCH_ATTR,
    )
