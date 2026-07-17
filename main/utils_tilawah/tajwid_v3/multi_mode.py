from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Dict, Mapping, Tuple

from .annotations import TajwidAnnotationV3
from .engine import TajwidEngineV3Result, analyze_tajwid_v3
from .renderer import TajwidRenderResult, render_engine_result
from .specification import ReadingMode


MULTI_MODE_SCHEMA_VERSION = "3.0.0-alpha.1"


@dataclass(frozen=True, slots=True)
class MergedModeAnnotation:
    rule_code: str
    trigger_grapheme_start: int
    trigger_grapheme_end: int
    display_grapheme_start: int
    display_grapheme_end: int
    modes: Tuple[str, ...]
    annotations_by_mode: Mapping[str, TajwidAnnotationV3]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "annotations_by_mode",
            MappingProxyType(dict(self.annotations_by_mode)),
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "rule_code": self.rule_code,
            "trigger_grapheme_start": self.trigger_grapheme_start,
            "trigger_grapheme_end": self.trigger_grapheme_end,
            "display_grapheme_start": self.display_grapheme_start,
            "display_grapheme_end": self.display_grapheme_end,
            "modes": list(self.modes),
            "annotations_by_mode": {
                mode: item.to_dict()
                for mode, item in self.annotations_by_mode.items()
            },
        }


@dataclass(frozen=True, slots=True)
class MultiModeTajwidResult:
    source_text: str
    wasl: TajwidEngineV3Result
    ayah_stop: TajwidEngineV3Result
    merged_annotations: Tuple[MergedModeAnnotation, ...]
    schema_version: str = MULTI_MODE_SCHEMA_VERSION

    def result_for_mode(self, mode: ReadingMode | str) -> TajwidEngineV3Result:
        resolved = mode if isinstance(mode, ReadingMode) else ReadingMode(mode)
        if resolved == ReadingMode.WASL:
            return self.wasl
        if resolved in {ReadingMode.AYAH_STOP, ReadingMode.WAQF}:
            return self.ayah_stop
        raise ValueError(f"Reading mode tidak didukung: {resolved.value}")

    def render_for_mode(
        self,
        mode: ReadingMode | str,
        *,
        is_verified: bool = False,
    ) -> TajwidRenderResult:
        return render_engine_result(
            self.result_for_mode(mode),
            is_verified=is_verified,
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_text": self.source_text,
            "wasl": self.wasl.to_dict(),
            "ayah_stop": self.ayah_stop.to_dict(),
            "merged_annotations": [
                item.to_dict() for item in self.merged_annotations
            ],
        }


def _identity(annotation: TajwidAnnotationV3) -> tuple:
    return (
        annotation.rule_code,
        annotation.trigger_span.grapheme_start,
        annotation.trigger_span.grapheme_end,
        annotation.display_span.grapheme_start,
        annotation.display_span.grapheme_end,
    )


def _merge_mode_annotations(
    wasl: TajwidEngineV3Result,
    ayah_stop: TajwidEngineV3Result,
) -> Tuple[MergedModeAnnotation, ...]:
    grouped: Dict[tuple, Dict[str, TajwidAnnotationV3]] = {}
    for mode, result in (
        (ReadingMode.WASL.value, wasl),
        (ReadingMode.AYAH_STOP.value, ayah_stop),
    ):
        for annotation in result.annotations:
            grouped.setdefault(_identity(annotation), {})[mode] = annotation

    merged = []
    for key, by_mode in grouped.items():
        rule_code, trigger_start, trigger_end, display_start, display_end = key
        modes = tuple(
            mode
            for mode in (ReadingMode.WASL.value, ReadingMode.AYAH_STOP.value)
            if mode in by_mode
        )
        merged.append(
            MergedModeAnnotation(
                rule_code=rule_code,
                trigger_grapheme_start=trigger_start,
                trigger_grapheme_end=trigger_end,
                display_grapheme_start=display_start,
                display_grapheme_end=display_end,
                modes=modes,
                annotations_by_mode=by_mode,
            )
        )
    return tuple(
        sorted(
            merged,
            key=lambda item: (
                item.display_grapheme_start,
                item.display_grapheme_end,
                item.rule_code,
            ),
        )
    )


def analyze_tajwid_v3_modes(
    text: str,
    *,
    verse_key: str | None = None,
) -> MultiModeTajwidResult:
    wasl = analyze_tajwid_v3(
        text,
        reading_mode=ReadingMode.WASL,
        verse_key=verse_key,
    )
    ayah_stop = analyze_tajwid_v3(
        text,
        reading_mode=ReadingMode.AYAH_STOP,
        verse_key=verse_key,
    )
    if wasl.source_text != ayah_stop.source_text:
        raise ValueError("Multi-mode analysis membutuhkan source text identik.")
    return MultiModeTajwidResult(
        source_text=text,
        wasl=wasl,
        ayah_stop=ayah_stop,
        merged_annotations=_merge_mode_annotations(wasl, ayah_stop),
    )
