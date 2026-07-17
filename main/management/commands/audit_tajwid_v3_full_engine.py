from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from main.models_tilawah import TilawahAyahPool
from main.utils_tilawah.tajwid_v3.display import RULE_DISPLAY_CATALOG
from main.utils_tilawah.tajwid_v3.engine import ENGINE_VERSION, analyze_tajwid_v3
from main.utils_tilawah.tajwid_v3.renderer import RENDERER_VERSION, render_engine_result
from main.utils_tilawah.tajwid_v3.rule_specs import RULE_SPECS
from main.utils_tilawah.tajwid_v3.specification import get_recitation_profile


class Command(BaseCommand):
    help = (
        "Audit read-only Stage 5M untuk full Tajwid Engine v3, global conflict "
        "resolver, multi-mode wasl/ayah_stop, dan frontend renderer."
    )

    def add_arguments(self, parser):
        scope = parser.add_mutually_exclusive_group(required=True)
        scope.add_argument("--all", action="store_true")
        scope.add_argument("--surah", type=int)
        parser.add_argument("--ayah", type=int)
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--chunk-size", type=int, default=250)
        parser.add_argument(
            "--modes",
            choices=("both", "ayah_stop", "wasl"),
            default="both",
        )
        parser.add_argument(
            "--output-dir",
            default="reports/tilawah/v3_full_engine",
        )
        parser.add_argument("--fail-on-errors", action="store_true")

    def handle(self, *args: Any, **options: Any):
        if options["ayah"] is not None and options["surah"] is None:
            raise CommandError("--ayah hanya dapat digunakan bersama --surah.")
        if options["limit"] is not None and options["limit"] < 1:
            raise CommandError("--limit harus lebih besar dari 0.")
        if options["chunk_size"] < 1:
            raise CommandError("--chunk-size harus lebih besar dari 0.")

        queryset = TilawahAyahPool.objects.only(
            "id", "surah_number", "ayah_number", "ayah_text"
        ).order_by("surah_number", "ayah_number")
        if options["surah"] is not None:
            queryset = queryset.filter(surah_number=options["surah"])
            if options["ayah"] is not None:
                queryset = queryset.filter(ayah_number=options["ayah"])
        if options["limit"] is not None:
            queryset = queryset[: options["limit"]]

        selected_count = queryset.count()
        if selected_count == 0:
            raise CommandError("Tidak ada ayat yang cocok dengan filter audit.")

        output_dir = Path(options["output_dir"])
        if not output_dir.is_absolute():
            output_dir = Path(settings.BASE_DIR) / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        profile = get_recitation_profile()
        boundary_map = {
            location.start_verse_key: location.end_verse_key
            for location in (*profile.mandatory_saktah, *profile.optional_saktah)
            if location.start_verse_key != location.end_verse_key
        }
        destination_keys = set(boundary_map.values())
        destination_text = self._load_destination_text(destination_keys)

        modes = (
            ("ayah_stop", "wasl")
            if options["modes"] == "both"
            else (options["modes"],)
        )
        counters: Counter[str] = Counter()
        issue_counts: Counter[str] = Counter()
        rule_counts: dict[str, Counter[str]] = {
            mode: Counter() for mode in modes
        }
        rule_ayahs: dict[str, dict[str, set[int]]] = {
            mode: defaultdict(set) for mode in modes
        }
        primary_rule_counts: Counter[str] = Counter()
        overlap_counts: Counter[str] = Counter()
        issue_rows: list[dict[str, Any]] = []
        ayah_rows: list[dict[str, Any]] = []
        mode_difference_rows: list[dict[str, Any]] = []

        self.stdout.write(
            f"Tajwid v3 full-engine audit — Engine {ENGINE_VERSION} / "
            f"Renderer {RENDERER_VERSION}"
        )
        self.stdout.write(f"Ayat dipilih : {selected_count}")
        self.stdout.write(f"Modes        : {','.join(modes)}")
        self.stdout.write("Database write: TIDAK")

        for position, ayah in enumerate(
            queryset.iterator(chunk_size=options["chunk_size"]),
            start=1,
        ):
            counters["total_ayah"] += 1
            verse_key = f"{ayah.surah_number}:{ayah.ayah_number}"
            mode_outputs: dict[str, dict[str, Any]] = {}

            for mode in modes:
                input_text = ayah.ayah_text
                boundary_to = None
                source_cutoff = len(ayah.ayah_text)
                if mode == "wasl" and verse_key in boundary_map:
                    boundary_to = boundary_map[verse_key]
                    next_text = destination_text.get(boundary_to)
                    if next_text:
                        input_text = f"{ayah.ayah_text} {next_text}"
                        counters["cross_ayah_inputs"] += 1
                    else:
                        counters["missing_boundary_destination"] += 1

                output = self._analyze_one_mode(
                    ayah_id=ayah.id,
                    surah_number=ayah.surah_number,
                    ayah_number=ayah.ayah_number,
                    verse_key=verse_key,
                    input_text=input_text,
                    source_cutoff=source_cutoff,
                    mode=mode,
                    boundary_to=boundary_to,
                )
                mode_outputs[mode] = output

                counters[f"{mode}_annotations"] += output["annotation_count"]
                counters[f"{mode}_segments"] += output["segment_count"]
                counters[f"{mode}_overlap_segments"] += output["overlap_segment_count"]
                if output["has_error"]:
                    counters["ayah_mode_errors"] += 1
                if output["exception"]:
                    counters["exceptions"] += 1

                for code in output["rule_codes"]:
                    rule_counts[mode][code] += 1
                    rule_ayahs[mode][code].add(ayah.id)
                for code in output["primary_rule_codes"]:
                    primary_rule_counts[code] += 1
                for signature in output["overlap_signatures"]:
                    overlap_counts[signature] += 1
                for issue in output["issues"]:
                    issue_counts[issue["issue_type"]] += 1
                    counters[f"{issue['severity']}s"] += 1
                    issue_rows.append(issue)
                if output["exception"]:
                    issue_counts["audit_exception"] += 1
                    counters["errors"] += 1
                    issue_rows.append(
                        {
                            "ayah_id": ayah.id,
                            "surah_number": ayah.surah_number,
                            "ayah_number": ayah.ayah_number,
                            "mode": mode,
                            "issue_type": "audit_exception",
                            "severity": "error",
                            "detail": output["exception"],
                            "evidence": "",
                        }
                    )

            if "ayah_stop" in mode_outputs and "wasl" in mode_outputs:
                stop_signatures = set(mode_outputs["ayah_stop"]["annotation_signatures"])
                wasl_signatures = set(mode_outputs["wasl"]["annotation_signatures"])
                only_stop = sorted(stop_signatures - wasl_signatures)
                only_wasl = sorted(wasl_signatures - stop_signatures)
                if only_stop or only_wasl:
                    counters["ayah_with_mode_differences"] += 1
                    mode_difference_rows.append(
                        {
                            "ayah_id": ayah.id,
                            "surah_number": ayah.surah_number,
                            "ayah_number": ayah.ayah_number,
                            "only_ayah_stop": "|".join(only_stop),
                            "only_wasl": "|".join(only_wasl),
                        }
                    )

            ayah_rows.append(
                {
                    "ayah_id": ayah.id,
                    "surah_number": ayah.surah_number,
                    "ayah_number": ayah.ayah_number,
                    "ayah_stop_annotations": mode_outputs.get("ayah_stop", {}).get(
                        "annotation_count", 0
                    ),
                    "wasl_annotations": mode_outputs.get("wasl", {}).get(
                        "annotation_count", 0
                    ),
                    "ayah_stop_segments": mode_outputs.get("ayah_stop", {}).get(
                        "segment_count", 0
                    ),
                    "wasl_segments": mode_outputs.get("wasl", {}).get(
                        "segment_count", 0
                    ),
                    "issue_count": sum(
                        len(item["issues"]) + (1 if item["exception"] else 0)
                        for item in mode_outputs.values()
                    ),
                    "has_error": any(
                        item["has_error"] or bool(item["exception"])
                        for item in mode_outputs.values()
                    ),
                }
            )

            if position % 250 == 0 or position == selected_count:
                total_annotations = sum(
                    counters[f"{mode}_annotations"] for mode in modes
                )
                self.stdout.write(
                    f"Processed {position}/{selected_count} | "
                    f"annotations={total_annotations} | "
                    f"errors={counters['errors'] + counters['exceptions']}"
                )

        distribution_rows = []
        for mode in modes:
            for code in sorted(RULE_SPECS):
                distribution_rows.append(
                    {
                        "mode": mode,
                        "rule_code": code,
                        "annotation_count": rule_counts[mode][code],
                        "ayah_count": len(rule_ayahs[mode][code]),
                        "primary_segment_count": primary_rule_counts[code],
                    }
                )

        missing_display = sorted(set(RULE_SPECS) - set(RULE_DISPLAY_CATALOG))
        if missing_display:
            counters["errors"] += len(missing_display)
            for code in missing_display:
                issue_rows.append(
                    {
                        "ayah_id": "",
                        "surah_number": "",
                        "ayah_number": "",
                        "mode": "global",
                        "issue_type": "missing_display_definition",
                        "severity": "error",
                        "detail": code,
                        "evidence": "",
                    }
                )

        summary = {
            "generated_at": timezone.now().isoformat(),
            "engine_version": ENGINE_VERSION,
            "renderer_version": RENDERER_VERSION,
            "database_write_performed": False,
            "modes": list(modes),
            "scope": {
                "all": bool(options["all"]),
                "surah": options["surah"],
                "ayah": options["ayah"],
                "limit": options["limit"],
            },
            "rule_count": len(RULE_SPECS),
            "display_rule_count": len(RULE_DISPLAY_CATALOG),
            "counters": dict(sorted(counters.items())),
            "issue_type_counts": dict(sorted(issue_counts.items())),
            "overlap_signatures": dict(overlap_counts.most_common()),
        }

        self._write_outputs(
            output_dir=output_dir,
            summary=summary,
            issue_rows=issue_rows,
            ayah_rows=ayah_rows,
            distribution_rows=distribution_rows,
            mode_difference_rows=mode_difference_rows,
        )

        self.stdout.write(self.style.SUCCESS("Full-engine audit selesai."))
        self.stdout.write(f"Report: {output_dir}")
        if options["fail_on_errors"] and (
            counters["errors"] > 0 or counters["exceptions"] > 0
        ):
            raise CommandError(
                "Full-engine audit menemukan error/exception. Periksa report."
            )

    def _load_destination_text(self, destination_keys: set[str]) -> dict[str, str]:
        if not destination_keys:
            return {}
        surah_numbers = {int(key.split(":")[0]) for key in destination_keys}
        rows = TilawahAyahPool.objects.filter(
            surah_number__in=surah_numbers
        ).only("surah_number", "ayah_number", "ayah_text")
        return {
            f"{row.surah_number}:{row.ayah_number}": row.ayah_text
            for row in rows
            if f"{row.surah_number}:{row.ayah_number}" in destination_keys
        }

    def _analyze_one_mode(
        self,
        *,
        ayah_id: int,
        surah_number: int,
        ayah_number: int,
        verse_key: str,
        input_text: str,
        source_cutoff: int,
        mode: str,
        boundary_to: str | None,
    ) -> dict[str, Any]:
        try:
            result = analyze_tajwid_v3(
                input_text,
                reading_mode=mode,
                verse_key=verse_key,
                boundary_to_verse_key=boundary_to,
            )
            rendered = render_engine_result(result, is_verified=False)
            if rendered.reconstruct() != input_text:
                raise ValueError("render_reconstruction_mismatch")
            if result.stream.reconstruct() != input_text:
                raise ValueError("stream_reconstruction_mismatch")

            annotations = [
                item
                for item in result.annotations
                if item.trigger_span.codepoint_start < source_cutoff
            ]
            issues = []
            for issue in result.issues:
                if issue.grapheme_index is not None:
                    grapheme = result.stream.grapheme(issue.grapheme_index)
                    if grapheme.codepoint_start >= source_cutoff:
                        continue
                issues.append(
                    {
                        "ayah_id": ayah_id,
                        "surah_number": surah_number,
                        "ayah_number": ayah_number,
                        "mode": mode,
                        "issue_type": issue.issue_type,
                        "severity": issue.severity,
                        "detail": issue.detail,
                        "evidence": json.dumps(
                            issue.evidence,
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    }
                )

            primary_codes = []
            overlaps = []
            for segment in rendered.segments:
                if segment.codepoint_start >= source_cutoff:
                    continue
                if segment.primary_rule_code != "regular":
                    primary_codes.append(segment.primary_rule_code)
                if len(segment.active_rule_codes) > 1:
                    overlaps.append("+".join(segment.active_rule_codes))

            signatures = [
                f"{item.rule_code}@{item.trigger_span.grapheme_start}:"
                f"{item.trigger_span.grapheme_end}"
                for item in annotations
            ]
            return {
                "annotation_count": len(annotations),
                "segment_count": len(
                    [
                        item
                        for item in rendered.segments
                        if item.codepoint_start < source_cutoff
                    ]
                ),
                "overlap_segment_count": len(overlaps),
                "rule_codes": [item.rule_code for item in annotations],
                "primary_rule_codes": primary_codes,
                "overlap_signatures": overlaps,
                "annotation_signatures": signatures,
                "issues": issues,
                "has_error": result.has_errors,
                "exception": "",
            }
        except Exception as exc:
            return {
                "annotation_count": 0,
                "segment_count": 0,
                "overlap_segment_count": 0,
                "rule_codes": [],
                "primary_rule_codes": [],
                "overlap_signatures": [],
                "annotation_signatures": [],
                "issues": [],
                "has_error": True,
                "exception": f"{type(exc).__name__}: {exc}",
            }

    def _write_outputs(
        self,
        *,
        output_dir: Path,
        summary: dict[str, Any],
        issue_rows: list[dict[str, Any]],
        ayah_rows: list[dict[str, Any]],
        distribution_rows: list[dict[str, Any]],
        mode_difference_rows: list[dict[str, Any]],
    ) -> None:
        (output_dir / "tajwid_v3_full_engine_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._write_csv(
            output_dir / "tajwid_v3_full_engine_issues.csv",
            issue_rows,
            [
                "ayah_id",
                "surah_number",
                "ayah_number",
                "mode",
                "issue_type",
                "severity",
                "detail",
                "evidence",
            ],
        )
        self._write_csv(
            output_dir / "tajwid_v3_full_engine_ayahs.csv",
            ayah_rows,
            [
                "ayah_id",
                "surah_number",
                "ayah_number",
                "ayah_stop_annotations",
                "wasl_annotations",
                "ayah_stop_segments",
                "wasl_segments",
                "issue_count",
                "has_error",
            ],
        )
        self._write_csv(
            output_dir / "tajwid_v3_full_engine_distribution.csv",
            distribution_rows,
            [
                "mode",
                "rule_code",
                "annotation_count",
                "ayah_count",
                "primary_segment_count",
            ],
        )
        self._write_csv(
            output_dir / "tajwid_v3_full_engine_mode_differences.csv",
            mode_difference_rows,
            [
                "ayah_id",
                "surah_number",
                "ayah_number",
                "only_ayah_stop",
                "only_wasl",
            ],
        )

    @staticmethod
    def _write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
