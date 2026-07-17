from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

from ..annotations import TajwidAnnotationV3, make_text_span
from ..grapheme_parser import CanonicalGrapheme, HAMZAT_WASL, MarkTag
from ..rule_specs import get_rule_spec
from ..specification import AppliesWhen, ReadingMode
from ..token_stream import CanonicalTokenStream
from .base import DetectorIssue, DetectorOutput


DETECTOR_ID = "mad_detector_v3.0.0-alpha.1"
SUPPORTED_RULE_CODES = frozenset(
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

HAMZA_LETTERS = frozenset({"ء", "أ", "إ", "ؤ", "ئ", "آ"})
PLAIN_ALEF = "ا"
TA_MARBUTA = "ة"


@dataclass(frozen=True, slots=True)
class MaddNucleus:
    onset: CanonicalGrapheme
    carrier: CanonicalGrapheme
    kind: str
    badl_origin: bool = False

    @property
    def word_index(self) -> int:
        if self.carrier.word_index is None:
            raise ValueError("Madd carrier tidak memiliki word_index.")
        return self.carrier.word_index

    @property
    def pronunciation_start(self) -> int:
        return self.onset.index

    @property
    def pronunciation_end(self) -> int:
        return self.carrier.index + 1


@dataclass(frozen=True, slots=True)
class LinNucleus:
    onset: CanonicalGrapheme
    carrier: CanonicalGrapheme


def _has(item: CanonicalGrapheme, tag: MarkTag) -> bool:
    return tag in item.mark_tags


def _has_fatha(item: CanonicalGrapheme) -> bool:
    return _has(item, MarkTag.FATHA)


def _has_damma(item: CanonicalGrapheme) -> bool:
    return _has(item, MarkTag.DAMMA)


def _has_kasra(item: CanonicalGrapheme) -> bool:
    return _has(item, MarkTag.KASRA)


def _is_hamza(item: Optional[CanonicalGrapheme]) -> bool:
    return bool(item is not None and item.base_letter in HAMZA_LETTERS)


def _is_unvowelled_carrier(item: CanonicalGrapheme) -> bool:
    return not (
        item.has_short_vowel
        or item.has_tanwin
        or item.has_shadda
    )


def _is_waw_or_ya_sakin(item: CanonicalGrapheme) -> bool:
    return bool(
        item.folded_base in {"و", "ي"}
        and (item.has_sukun or _is_unvowelled_carrier(item))
    )


def _same_word_previous_letter(
    stream: CanonicalTokenStream,
    item: CanonicalGrapheme,
) -> Optional[CanonicalGrapheme]:
    return stream.previous_letter(item.index, same_word_only=True)


def _same_word_next_letter(
    stream: CanonicalTokenStream,
    item: CanonicalGrapheme,
) -> Optional[CanonicalGrapheme]:
    return stream.next_letter(item.index, same_word_only=True)


def _is_support_alef_after_plural_waw(
    previous: CanonicalGrapheme,
    candidate: CanonicalGrapheme,
) -> bool:
    return bool(
        previous.folded_base == "و"
        and candidate.base_letter == PLAIN_ALEF
        and candidate.word_index == previous.word_index
        and candidate.is_word_end
        and not candidate.marks
    )


def _next_effective_letter(
    stream: CanonicalTokenStream,
    nucleus: MaddNucleus,
) -> Optional[CanonicalGrapheme]:
    candidate = stream.next_letter(nucleus.carrier.index)
    if candidate is None:
        return None

    if _is_support_alef_after_plural_waw(nucleus.carrier, candidate):
        return stream.next_letter(candidate.index)
    return candidate


def _last_effective_letter(
    stream: CanonicalTokenStream,
) -> Optional[CanonicalGrapheme]:
    letters = list(stream.iter_letters())
    if not letters:
        return None
    final = letters[-1]
    if len(letters) >= 2 and _is_support_alef_after_plural_waw(letters[-2], final):
        return letters[-2]
    return final


def _iter_madd_nuclei(stream: CanonicalTokenStream) -> Iterable[MaddNucleus]:
    for item in stream.iter_letters():
        if item.word_index is None:
            continue

        # Some QPC/Uthmani text encodes dagger alif on a tatweel extender
        # separated from its consonantal onset (for example مَـٰ).
        if item.base_letter == "ـ":
            if _has(item, MarkTag.DAGGER_ALEF):
                previous = _same_word_previous_letter(stream, item)
                if previous is not None and _has_fatha(previous):
                    yield MaddNucleus(previous, item, "tatweel_dagger_alif")
            continue

        # Dagger alif may also be attached directly to its consonantal onset.
        if _has(item, MarkTag.DAGGER_ALEF):
            yield MaddNucleus(item, item, "dagger_alif")
            continue

        # Alif madda encodes a hamza followed by a long alif in one grapheme.
        if item.base_letter == "آ":
            yield MaddNucleus(item, item, "alif_madda", badl_origin=True)
            continue

        previous = _same_word_previous_letter(stream, item)
        if previous is None:
            continue

        if item.base_letter == PLAIN_ALEF and _has_fatha(previous):
            yield MaddNucleus(
                previous,
                item,
                "alif",
                badl_origin=_is_hamza(previous),
            )
            continue

        if (
            item.folded_base == "و"
            and _is_waw_or_ya_sakin(item)
            and _has_damma(previous)
        ):
            yield MaddNucleus(
                previous,
                item,
                "waw",
                badl_origin=_is_hamza(previous),
            )
            continue

        if (
            item.folded_base == "ي"
            and _is_waw_or_ya_sakin(item)
            and _has_kasra(previous)
        ):
            yield MaddNucleus(
                previous,
                item,
                "ya",
                badl_origin=_is_hamza(previous),
            )


def _iter_lin_nuclei(stream: CanonicalTokenStream) -> Iterable[LinNucleus]:
    for carrier in stream.iter_letters():
        if carrier.word_index is None or not _is_waw_or_ya_sakin(carrier):
            continue
        onset = _same_word_previous_letter(stream, carrier)
        if onset is not None and _has_fatha(onset):
            yield LinNucleus(onset=onset, carrier=carrier)


def _make_annotation(
    stream: CanonicalTokenStream,
    *,
    rule_code: str,
    trigger_start: int,
    trigger_end: int,
    context_start: int,
    context_end: int,
    display_start: int,
    display_end: int,
    word_index: int,
    next_word_index: Optional[int],
    applies_when: AppliesWhen,
    evidence: dict,
    confidence: float = 1.0,
    notes: str = "",
) -> TajwidAnnotationV3:
    rule_spec = get_rule_spec(rule_code)
    return TajwidAnnotationV3(
        rule_code=rule_code,
        trigger_span=make_text_span(stream, trigger_start, trigger_end),
        context_span=make_text_span(stream, context_start, context_end),
        display_span=make_text_span(stream, display_start, display_end),
        word_index=word_index,
        next_word_index=next_word_index,
        applies_when=applies_when,
        evidence=evidence,
        expected_features=dict(rule_spec.expected_features),
        confidence=confidence,
        detector_id=DETECTOR_ID,
        notes=notes,
    )


def _make_nucleus_annotation(
    stream: CanonicalTokenStream,
    nucleus: MaddNucleus,
    rule_code: str,
    *,
    target: Optional[CanonicalGrapheme] = None,
    confidence: float = 1.0,
    notes: str = "",
) -> TajwidAnnotationV3:
    trigger_start = nucleus.pronunciation_start
    trigger_end = nucleus.pronunciation_end
    context_end = target.index + 1 if target is not None else trigger_end
    next_word_index = None
    if target is not None and target.word_index != nucleus.word_index:
        next_word_index = target.word_index

    if rule_code == "mad_jaiz_munfasil":
        applies_when = AppliesWhen.WASL
    else:
        applies_when = AppliesWhen.BOTH

    display_end = (
        context_end
        if rule_code
        in {
            "mad_wajib_muttasil",
            "mad_jaiz_munfasil",
            "mad_lazim_kalimi_muthaqqal",
            "mad_lazim_kalimi_mukhaffaf",
        }
        else trigger_end
    )

    return _make_annotation(
        stream,
        rule_code=rule_code,
        trigger_start=trigger_start,
        trigger_end=trigger_end,
        context_start=trigger_start,
        context_end=context_end,
        display_start=trigger_start,
        display_end=display_end,
        word_index=nucleus.word_index,
        next_word_index=next_word_index,
        applies_when=applies_when,
        confidence=confidence,
        notes=notes,
        evidence={
            "trigger_type": "madd_nucleus",
            "nucleus_kind": nucleus.kind,
            "onset_letter": nucleus.onset.base_letter,
            "carrier_letter": nucleus.carrier.base_letter,
            "carrier_grapheme_index": nucleus.carrier.index,
            "target_letter": target.base_letter if target else None,
            "target_grapheme_index": target.index if target else None,
            "same_word_target": (
                target.word_index == nucleus.word_index if target else None
            ),
            "badl_origin": nucleus.badl_origin,
        },
    )


def _stop_mode(reading_mode: ReadingMode) -> bool:
    return reading_mode in {ReadingMode.AYAH_STOP, ReadingMode.WAQF}


def _detect_iwad(
    stream: CanonicalTokenStream,
    reading_mode: ReadingMode,
) -> Tuple[TajwidAnnotationV3, ...]:
    if not _stop_mode(reading_mode) or not stream.words:
        return ()

    final_word = stream.words[-1]
    letters = [stream.grapheme(index) for index in final_word.letter_indices]
    if not letters:
        return ()

    trigger: Optional[CanonicalGrapheme] = None
    support_alef: Optional[CanonicalGrapheme] = None

    if (
        len(letters) >= 2
        and letters[-1].base_letter == PLAIN_ALEF
        and not letters[-1].marks
        and _has(letters[-2], MarkTag.FATHATAN)
    ):
        trigger = letters[-2]
        support_alef = letters[-1]
    elif _has(letters[-1], MarkTag.FATHATAN):
        trigger = letters[-1]

    if trigger is None or trigger.base_letter == TA_MARBUTA:
        return ()

    end = (support_alef.index + 1) if support_alef is not None else trigger.index + 1
    annotation = _make_annotation(
        stream,
        rule_code="mad_iwad",
        trigger_start=trigger.index,
        trigger_end=end,
        context_start=trigger.index,
        context_end=end,
        display_start=trigger.index,
        display_end=end,
        word_index=trigger.word_index,
        next_word_index=None,
        applies_when=AppliesWhen.WAQF,
        confidence=(1.0 if support_alef is not None else 0.95),
        notes=(
            "Tanwin fathah tanpa alif penyangga eksplisit ditandai provisional."
            if support_alef is None
            else ""
        ),
        evidence={
            "trigger_type": "fathatan_at_actual_stop",
            "trigger_letter": trigger.base_letter,
            "has_support_alef": support_alef is not None,
            "support_alef_index": support_alef.index if support_alef else None,
            "ta_marbuta_excluded": False,
        },
    )
    return (annotation,)


def _detect_stop_mad(
    stream: CanonicalTokenStream,
    reading_mode: ReadingMode,
    nuclei_by_carrier: dict[int, MaddNucleus],
    lin_by_carrier: dict[int, LinNucleus],
) -> Tuple[Tuple[TajwidAnnotationV3, ...], frozenset[int]]:
    if not _stop_mode(reading_mode):
        return (), frozenset()

    final = _last_effective_letter(stream)
    if final is None or final.word_index is None:
        return (), frozenset()
    if final.has_sukun or final.has_shadda:
        return (), frozenset()

    previous = stream.previous_letter(final.index, same_word_only=True)
    if previous is None:
        return (), frozenset()

    nucleus = nuclei_by_carrier.get(previous.index)
    if nucleus is not None:
        annotation = _make_annotation(
            stream,
            rule_code="mad_arid_lissukun",
            trigger_start=nucleus.pronunciation_start,
            trigger_end=nucleus.pronunciation_end,
            context_start=nucleus.pronunciation_start,
            context_end=final.index + 1,
            display_start=nucleus.pronunciation_start,
            display_end=final.index + 1,
            word_index=nucleus.word_index,
            next_word_index=None,
            applies_when=AppliesWhen.WAQF,
            evidence={
                "trigger_type": "madd_before_acquired_final_sukun",
                "nucleus_kind": nucleus.kind,
                "final_letter": final.base_letter,
                "final_grapheme_index": final.index,
                "stop_origin": "acquired_sukun_by_waqf",
            },
        )
        return (annotation,), frozenset({nucleus.carrier.index})

    lin = lin_by_carrier.get(previous.index)
    if lin is not None:
        annotation = _make_annotation(
            stream,
            rule_code="mad_lin",
            trigger_start=lin.onset.index,
            trigger_end=lin.carrier.index + 1,
            context_start=lin.onset.index,
            context_end=final.index + 1,
            display_start=lin.onset.index,
            display_end=final.index + 1,
            word_index=lin.carrier.word_index,
            next_word_index=None,
            applies_when=AppliesWhen.WAQF,
            evidence={
                "trigger_type": "lin_before_acquired_final_sukun",
                "carrier_letter": lin.carrier.base_letter,
                "final_letter": final.base_letter,
                "final_grapheme_index": final.index,
            },
        )
        return (annotation,), frozenset({lin.carrier.index})

    return (), frozenset()


class MadDetector:
    detector_id = DETECTOR_ID
    supported_rule_codes = SUPPORTED_RULE_CODES

    def detect(
        self,
        stream: CanonicalTokenStream,
        *,
        reading_mode: ReadingMode,
    ) -> DetectorOutput:
        annotations = []
        issues = []

        nuclei = tuple(_iter_madd_nuclei(stream))
        nuclei_by_carrier = {item.carrier.index: item for item in nuclei}
        lin_nuclei = tuple(_iter_lin_nuclei(stream))
        lin_by_carrier = {item.carrier.index: item for item in lin_nuclei}

        iwad_annotations = _detect_iwad(stream, reading_mode)
        annotations.extend(iwad_annotations)

        stop_annotations, consumed_carriers = _detect_stop_mad(
            stream,
            reading_mode,
            nuclei_by_carrier,
            lin_by_carrier,
        )
        annotations.extend(stop_annotations)

        for nucleus in nuclei:
            if nucleus.carrier.index in consumed_carriers:
                continue

            target = _next_effective_letter(stream, nucleus)
            same_word_target = bool(
                target is not None and target.word_index == nucleus.word_index
            )

            if same_word_target and _is_hamza(target):
                annotations.append(
                    _make_nucleus_annotation(
                        stream,
                        nucleus,
                        "mad_wajib_muttasil",
                        target=target,
                    )
                )
                continue

            if same_word_target and target is not None and target.has_shadda:
                annotations.append(
                    _make_nucleus_annotation(
                        stream,
                        nucleus,
                        "mad_lazim_kalimi_muthaqqal",
                        target=target,
                    )
                )
                continue

            if same_word_target and target is not None and target.has_sukun:
                annotations.append(
                    _make_nucleus_annotation(
                        stream,
                        nucleus,
                        "mad_lazim_kalimi_mukhaffaf",
                        target=target,
                        confidence=0.95,
                        notes=(
                            "Mad lazim kalimi mukhaffaf memiliki corpus sangat "
                            "terbatas; anotasi tetap memerlukan review ahli."
                        ),
                    )
                )
                continue

            if (
                target is not None
                and target.word_index != nucleus.word_index
                and _is_hamza(target)
                and target.base_letter != HAMZAT_WASL
                and reading_mode in {ReadingMode.WASL, ReadingMode.AYAH_STOP}
            ):
                annotations.append(
                    _make_nucleus_annotation(
                        stream,
                        nucleus,
                        "mad_jaiz_munfasil",
                        target=target,
                    )
                )
                continue

            if nucleus.badl_origin:
                annotations.append(
                    _make_nucleus_annotation(
                        stream,
                        nucleus,
                        "mad_badl",
                        confidence=0.98,
                        notes=(
                            "Mad badl ditandai dari pola ortografis; lexical "
                            "exception registry tetap diperlukan sebelum status ahli."
                        ),
                    )
                )
                continue

            annotations.append(
                _make_nucleus_annotation(
                    stream,
                    nucleus,
                    "mad_tabii",
                )
            )

        # Preserve unresolved maddah signs as warnings rather than inventing a
        # rule. This keeps corpus audit honest while remaining non-blocking for beta.
        known_carriers = {item.carrier.index for item in nuclei}
        for item in stream.iter_letters():
            if _has(item, MarkTag.MADDAH) and item.index not in known_carriers:
                issues.append(
                    DetectorIssue(
                        issue_type="unresolved_maddah_sign",
                        severity="warning",
                        grapheme_index=item.index,
                        word_index=item.word_index,
                        detail=(
                            "Tanda maddah tidak dapat dipetakan ke nucleus mad core; "
                            "kemungkinan termasuk mad harfi, farq, atau rasm khusus."
                        ),
                        evidence={"text": item.text, "base_letter": item.base_letter},
                    )
                )

        return DetectorOutput(
            annotations=tuple(annotations),
            issues=tuple(issues),
        )
