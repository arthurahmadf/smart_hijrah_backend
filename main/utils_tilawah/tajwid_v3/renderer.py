from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from .annotations import TajwidAnnotationV3
from .display import REGULAR_DISPLAY, RuleDisplayDefinition, get_rule_display
from .engine import TajwidEngineV3Result
from .token_stream import CanonicalTokenStream


RENDERER_VERSION = "3.0.0-alpha.1"


@dataclass(frozen=True, slots=True)
class TajwidRenderSegment:
    arabic: str
    grapheme_start: int
    grapheme_end: int
    codepoint_start: int
    codepoint_end: int
    primary_rule_code: str
    active_rule_codes: Tuple[str, ...]
    active_rule_titles: Tuple[str, ...]
    color: str
    rule_name: str
    rule_description: str
    confidence: float
    reading_mode: str
    is_verified: bool = False
    source: str = "engine"

    @property
    def is_regular(self) -> bool:
        return self.primary_rule_code == "regular"

    def to_frontend_dict(self) -> Dict[str, str]:
        """Kontrak minimal yang sudah disepakati dengan frontend."""
        return {
            "rule_name": self.rule_name,
            "color": self.color,
            "rule_description": self.rule_description,
            "arabic": self.arabic,
        }

    def to_extended_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = self.to_frontend_dict()
        payload.update(
            {
                "primary_rule_code": self.primary_rule_code,
                "rule_codes": list(self.active_rule_codes),
                "rule_titles": list(self.active_rule_titles),
                "grapheme_start": self.grapheme_start,
                "grapheme_end": self.grapheme_end,
                "codepoint_start": self.codepoint_start,
                "codepoint_end": self.codepoint_end,
                "confidence": self.confidence,
                "reading_mode": self.reading_mode,
                "is_verified": self.is_verified,
                "source": self.source,
                "renderer_version": RENDERER_VERSION,
            }
        )
        return payload


@dataclass(frozen=True, slots=True)
class TajwidRenderResult:
    source_text: str
    reading_mode: str
    segments: Tuple[TajwidRenderSegment, ...]
    renderer_version: str = RENDERER_VERSION

    def reconstruct(self) -> str:
        return "".join(item.arabic for item in self.segments)

    @property
    def is_valid(self) -> bool:
        return self.reconstruct() == self.source_text and all(
            item.arabic for item in self.segments
        )

    def to_frontend_rules(self) -> List[Dict[str, str]]:
        return [item.to_frontend_dict() for item in self.segments]

    def to_extended_dict(self) -> Dict[str, object]:
        return {
            "renderer_version": self.renderer_version,
            "reading_mode": self.reading_mode,
            "source_text": self.source_text,
            "is_valid": self.is_valid,
            "segments": [item.to_extended_dict() for item in self.segments],
        }


def _primary_annotation(
    annotations: Sequence[TajwidAnnotationV3],
) -> TajwidAnnotationV3:
    return min(
        annotations,
        key=lambda item: (
            get_rule_display(item.rule_code).priority,
            item.display_span.grapheme_end - item.display_span.grapheme_start,
            -item.confidence,
            item.rule_code,
        ),
    )


def _active_annotations(
    annotations: Sequence[TajwidAnnotationV3],
    start: int,
    end: int,
) -> Tuple[TajwidAnnotationV3, ...]:
    return tuple(
        item
        for item in annotations
        if item.display_span.grapheme_start <= start
        and item.display_span.grapheme_end >= end
    )


def _same_render_signature(
    left: TajwidRenderSegment,
    right: TajwidRenderSegment,
) -> bool:
    return (
        left.grapheme_end == right.grapheme_start
        and left.codepoint_end == right.codepoint_start
        and left.primary_rule_code == right.primary_rule_code
        and left.active_rule_codes == right.active_rule_codes
        and left.rule_description == right.rule_description
        and left.color == right.color
        and left.reading_mode == right.reading_mode
        and left.is_verified == right.is_verified
        and left.source == right.source
    )


def _merge_adjacent(
    segments: Iterable[TajwidRenderSegment],
) -> Tuple[TajwidRenderSegment, ...]:
    merged: List[TajwidRenderSegment] = []
    for item in segments:
        if merged and _same_render_signature(merged[-1], item):
            previous = merged[-1]
            merged[-1] = TajwidRenderSegment(
                arabic=previous.arabic + item.arabic,
                grapheme_start=previous.grapheme_start,
                grapheme_end=item.grapheme_end,
                codepoint_start=previous.codepoint_start,
                codepoint_end=item.codepoint_end,
                primary_rule_code=previous.primary_rule_code,
                active_rule_codes=previous.active_rule_codes,
                active_rule_titles=previous.active_rule_titles,
                color=previous.color,
                rule_name=previous.rule_name,
                rule_description=previous.rule_description,
                confidence=min(previous.confidence, item.confidence),
                reading_mode=previous.reading_mode,
                is_verified=previous.is_verified,
                source=previous.source,
            )
        else:
            merged.append(item)
    return tuple(merged)


def render_annotations(
    stream: CanonicalTokenStream,
    annotations: Iterable[TajwidAnnotationV3],
    *,
    reading_mode: str,
    is_verified: bool = False,
    source: str = "engine",
) -> TajwidRenderResult:
    if not stream.source_text:
        raise ValueError("Renderer tidak menerima source_text kosong.")

    annotation_items = tuple(annotations)
    boundaries = {0, len(stream.graphemes)}
    for item in annotation_items:
        boundaries.add(item.display_span.grapheme_start)
        boundaries.add(item.display_span.grapheme_end)
    ordered = sorted(boundaries)

    raw_segments: List[TajwidRenderSegment] = []
    for start, end in zip(ordered, ordered[1:]):
        if end <= start:
            continue
        arabic = stream.grapheme_text(start, end)
        if not arabic:
            raise ValueError(f"Renderer menghasilkan segment kosong [{start}, {end}).")
        codepoint_start, codepoint_end = stream.codepoint_span_for_graphemes(
            start,
            end,
        )
        active = _active_annotations(annotation_items, start, end)
        if active:
            primary = _primary_annotation(active)
            definition = get_rule_display(primary.rule_code)
            ordered_active = tuple(
                sorted(
                    active,
                    key=lambda item: (
                        get_rule_display(item.rule_code).priority,
                        item.rule_code,
                    ),
                )
            )
            rule_codes = tuple(item.rule_code for item in ordered_active)
            rule_titles = tuple(
                get_rule_display(item.rule_code).rule_title
                for item in ordered_active
            )
            confidence = min(item.confidence for item in active)
            primary_code = primary.rule_code
        else:
            definition = REGULAR_DISPLAY
            rule_codes = ()
            rule_titles = ()
            confidence = 1.0
            primary_code = "regular"

        raw_segments.append(
            TajwidRenderSegment(
                arabic=arabic,
                grapheme_start=start,
                grapheme_end=end,
                codepoint_start=codepoint_start,
                codepoint_end=codepoint_end,
                primary_rule_code=primary_code,
                active_rule_codes=rule_codes,
                active_rule_titles=rule_titles,
                color=definition.color,
                rule_name=definition.rule_name,
                rule_description=definition.description,
                confidence=confidence,
                reading_mode=reading_mode,
                is_verified=is_verified,
                source=source,
            )
        )

    result = TajwidRenderResult(
        source_text=stream.source_text,
        reading_mode=reading_mode,
        segments=_merge_adjacent(raw_segments),
    )
    if not result.is_valid:
        raise ValueError("Tajwid renderer gagal merekonstruksi source text secara identik.")
    return result


def render_engine_result(
    result: TajwidEngineV3Result,
    *,
    is_verified: bool = False,
    source: str = "engine",
) -> TajwidRenderResult:
    return render_annotations(
        result.stream,
        result.annotations,
        reading_mode=result.reading_mode.value,
        is_verified=is_verified,
        source=source,
    )


def frontend_rules_from_result(
    result: TajwidEngineV3Result,
    *,
    is_verified: bool = False,
) -> List[Dict[str, str]]:
    return render_engine_result(
        result,
        is_verified=is_verified,
    ).to_frontend_rules()
