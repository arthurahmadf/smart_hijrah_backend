from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import regex

from .tajwid_engine import analyze_tajwid, strip_harakat
from .tajwid_rule_catalog import (
    REGULAR_RENDER_RULE,
    TajwidAppliesWhen,
    TajwidRuleDefinition,
    get_rule_definition,
)


ANNOTATION_ENGINE_VERSION = "2.0.0"

# Unicode marks used by the locator. A grapheme cluster keeps these marks
# attached to its base letter, so the frontend never receives a detached
# harakat segment.
FATHAH = "\u064e"
DAMMAH = "\u064f"
KASRAH = "\u0650"
SHADDA = "\u0651"
SUKUN_MARKS = {"\u0652", "\u06e1"}
TANWIN_MARKS = {"\u064b", "\u064c", "\u064d", "\u0656", "\u0657", "\u065e"}
DAGGER_ALEF = "\u0670"
IQLAB_SIGN = "\u06e2"
SAKTAH = "\u06db"

ALEF_VARIANTS = {"ا", "أ", "إ", "آ", "ٱ"}
HAMZAH_VARIANTS = {"ء", "أ", "إ", "آ", "ئ", "ؤ"}
QALQALAH_LETTERS = {"ق", "ط", "ب", "ج", "د"}
MAD_LETTERS = ALEF_VARIANTS | {"و", "ي", "ى"}

NUN_TANWIN_RULES = {
    "izhar_halqi",
    "idgham_bighunnah",
    "idgham_bilaghunnah",
    "iqlab",
    "ikhfa_haqiqi",
}
MIM_SAKINAH_RULES = {
    "idgham_mimi",
    "ikhfa_syafawi",
    "izhar_syafawi",
}
MAD_RULES = {
    "mad_asli",
    "mad_wajib_muttasil",
    "mad_jaiz_munfasil",
    "mad_lazim_mutsaqqal",
    "mad_lazim_mukhaffaf",
    "mad_aridh_lissukun",
    "mad_lin",
    "mad_iwad",
    "mad_silah_qasirah",
    "mad_silah_thawilah",
}
IDGHAM_RULES = {
    "idgham_mutamatsilain",
    "idgham_mutajanisain",
    "idgham_mutaqaribain",
}
RA_RULES = {"tafkhim_ra", "tarqiq_ra"}
LAM_JALALAH_RULES = {"tafkhim_lam_jalalah", "tarqiq_lam_jalalah"}
WAQF_ONLY_RULES = {
    "qalqalah_kubra",
    "mad_aridh_lissukun",
    "mad_lin",
    "mad_iwad",
}


@dataclass(frozen=True, slots=True)
class Grapheme:
    text: str
    index: int
    codepoint_start: int
    codepoint_end: int

    @property
    def is_whitespace(self) -> bool:
        return self.text.isspace()

    @property
    def base(self) -> str:
        """Return the first non-mark character in the grapheme cluster."""

        for char in self.text:
            if not unicodedata.category(char).startswith("M"):
                return char
        return ""

    def has_any(self, marks: Iterable[str]) -> bool:
        return any(mark in self.text for mark in marks)


@dataclass(frozen=True, slots=True)
class WordSpan:
    word_index: int
    text: str
    start_grapheme: int
    end_grapheme: int  # exclusive
    start_codepoint: int
    end_codepoint: int  # exclusive


@dataclass(frozen=True, slots=True)
class LocatedSpan:
    start_grapheme: int
    end_grapheme: int  # exclusive
    next_word_index: Optional[int] = None
    locator_confidence: float = 1.0
    locator_method: str = "exact"


class TajwidAnnotationError(ValueError):
    """Raised when strict annotation generation cannot produce safe output."""


def split_graphemes(text: str) -> Tuple[Grapheme, ...]:
    """Split Unicode text with UAX #29 extended grapheme boundaries."""

    return tuple(
        Grapheme(
            text=match.group(0),
            index=index,
            codepoint_start=match.start(),
            codepoint_end=match.end(),
        )
        for index, match in enumerate(regex.finditer(r"\X", text))
    )


def split_word_spans(
    text: str,
    graphemes: Optional[Sequence[Grapheme]] = None,
) -> Tuple[WordSpan, ...]:
    """Return exact word boundaries without normalising the Quran text."""

    graphemes = tuple(graphemes or split_graphemes(text))
    words: List[WordSpan] = []
    start: Optional[int] = None

    def flush(end: int) -> None:
        nonlocal start
        if start is None:
            return
        first = graphemes[start]
        last = graphemes[end - 1]
        words.append(
            WordSpan(
                word_index=len(words),
                text=text[first.codepoint_start:last.codepoint_end],
                start_grapheme=start,
                end_grapheme=end,
                start_codepoint=first.codepoint_start,
                end_codepoint=last.codepoint_end,
            )
        )
        start = None

    for index, grapheme in enumerate(graphemes):
        if grapheme.is_whitespace:
            flush(index)
        elif start is None:
            start = index

    flush(len(graphemes))
    return tuple(words)


def _word_graphemes(
    word: WordSpan,
    graphemes: Sequence[Grapheme],
) -> Sequence[Grapheme]:
    return graphemes[word.start_grapheme:word.end_grapheme]


def _first_letter_index(
    word: WordSpan,
    graphemes: Sequence[Grapheme],
) -> Optional[int]:
    for grapheme in _word_graphemes(word, graphemes):
        if grapheme.base and not grapheme.base.isspace():
            return grapheme.index
    return None


def _last_letter_index(
    word: WordSpan,
    graphemes: Sequence[Grapheme],
) -> Optional[int]:
    for grapheme in reversed(_word_graphemes(word, graphemes)):
        if grapheme.base and not grapheme.base.isspace():
            return grapheme.index
    return None


def _find_indices_by_base(
    word: WordSpan,
    graphemes: Sequence[Grapheme],
    bases: Iterable[str],
) -> List[int]:
    wanted = set(bases)
    return [
        grapheme.index
        for grapheme in _word_graphemes(word, graphemes)
        if grapheme.base in wanted
    ]


def _span_from_indices(
    indices: Sequence[int],
    *,
    next_word_index: Optional[int] = None,
    confidence: float = 1.0,
    method: str = "exact",
) -> Optional[LocatedSpan]:
    if not indices:
        return None
    return LocatedSpan(
        start_grapheme=min(indices),
        end_grapheme=max(indices) + 1,
        next_word_index=next_word_index,
        locator_confidence=confidence,
        locator_method=method,
    )


def _locate_nun_or_tanwin(
    word: WordSpan,
    next_word: Optional[WordSpan],
    graphemes: Sequence[Grapheme],
) -> Optional[LocatedSpan]:
    candidates: List[int] = []
    for grapheme in _word_graphemes(word, graphemes):
        if grapheme.base == "ن" and (
            grapheme.has_any(SUKUN_MARKS) or IQLAB_SIGN in grapheme.text
        ):
            candidates.append(grapheme.index)
        elif grapheme.has_any(TANWIN_MARKS):
            candidates.append(grapheme.index)

    # Some Uthmani sources omit an explicit sukun. Only use a conservative
    # end-of-word fallback and mark the locator confidence lower.
    if not candidates:
        last_index = _last_letter_index(word, graphemes)
        if last_index is not None and graphemes[last_index].base == "ن":
            return _span_from_indices(
                [last_index],
                next_word_index=next_word.word_index if next_word else None,
                confidence=0.7,
                method="implicit_final_nun",
            )
        return None

    return _span_from_indices(
        [candidates[-1]],
        next_word_index=next_word.word_index if next_word else None,
    )


def _locate_mim_sakinah(
    word: WordSpan,
    next_word: Optional[WordSpan],
    graphemes: Sequence[Grapheme],
) -> Optional[LocatedSpan]:
    for grapheme in reversed(_word_graphemes(word, graphemes)):
        if grapheme.base == "م" and grapheme.has_any(SUKUN_MARKS):
            return _span_from_indices(
                [grapheme.index],
                next_word_index=next_word.word_index if next_word else None,
            )
    return None


def _locate_qalqalah(
    word: WordSpan,
    graphemes: Sequence[Grapheme],
    *,
    kubra: bool,
) -> Optional[LocatedSpan]:
    candidates = [
        grapheme.index
        for grapheme in _word_graphemes(word, graphemes)
        if grapheme.base in QALQALAH_LETTERS
        and grapheme.has_any(SUKUN_MARKS)
    ]

    if kubra:
        last_index = _last_letter_index(word, graphemes)
        if last_index is not None and graphemes[last_index].base in QALQALAH_LETTERS:
            return _span_from_indices([last_index], method="waqf_final_letter")

    if candidates:
        return _span_from_indices([candidates[-1]])
    return None


def _locate_ghunnah(
    word: WordSpan,
    graphemes: Sequence[Grapheme],
) -> Optional[LocatedSpan]:
    for grapheme in _word_graphemes(word, graphemes):
        if grapheme.base in {"ن", "م"} and SHADDA in grapheme.text:
            return _span_from_indices([grapheme.index])
    return None


def _locate_alif_lam(
    word: WordSpan,
    graphemes: Sequence[Grapheme],
) -> Optional[LocatedSpan]:
    local = list(_word_graphemes(word, graphemes))
    bases = [grapheme.base for grapheme in local]

    for offset in (0, 1):
        if offset + 2 >= len(local):
            continue
        if bases[offset] in ALEF_VARIANTS and bases[offset + 1] == "ل":
            return _span_from_indices(
                [
                    local[offset].index,
                    local[offset + 1].index,
                    local[offset + 2].index,
                ]
            )
    return None


def _mad_candidates(
    word: WordSpan,
    graphemes: Sequence[Grapheme],
) -> List[Tuple[int, int, str]]:
    """Return (start, end-exclusive, method) for plausible mad spans."""

    local = list(_word_graphemes(word, graphemes))
    candidates: List[Tuple[int, int, str]] = []

    for pos, grapheme in enumerate(local):
        # Dagger alif is a combining mark inside the preceding grapheme.
        if DAGGER_ALEF in grapheme.text:
            candidates.append(
                (grapheme.index, grapheme.index + 1, "dagger_alef")
            )

        if grapheme.base == "آ":
            candidates.append(
                (grapheme.index, grapheme.index + 1, "alef_madda")
            )

        if pos == 0:
            continue

        previous = local[pos - 1]
        if grapheme.base in ALEF_VARIANTS and FATHAH in previous.text:
            candidates.append(
                (previous.index, grapheme.index + 1, "fathah_alef")
            )
        elif grapheme.base == "و" and DAMMAH in previous.text:
            candidates.append(
                (previous.index, grapheme.index + 1, "dammah_waw")
            )
        elif grapheme.base in {"ي", "ى"} and KASRAH in previous.text:
            candidates.append(
                (previous.index, grapheme.index + 1, "kasrah_ya")
            )

    # Stable de-duplication.
    seen = set()
    unique: List[Tuple[int, int, str]] = []
    for candidate in candidates:
        key = candidate[:2]
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _locate_mad(
    rule_code: str,
    word: WordSpan,
    graphemes: Sequence[Grapheme],
) -> Optional[LocatedSpan]:
    local = list(_word_graphemes(word, graphemes))

    if rule_code in {"mad_silah_qasirah", "mad_silah_thawilah"}:
        for grapheme in reversed(local):
            if grapheme.base == "ه" and (
                FATHAH in grapheme.text
                or DAMMAH in grapheme.text
                or KASRAH in grapheme.text
            ):
                return _span_from_indices([grapheme.index], method="ha_dhamir")
        return None

    if rule_code == "mad_iwad":
        for grapheme in reversed(local):
            if "\u064b" in grapheme.text or "\u0657" in grapheme.text:
                return _span_from_indices([grapheme.index], method="tanwin_fath")
        return None

    if rule_code == "mad_lin":
        for pos, grapheme in enumerate(local):
            if pos == 0 or grapheme.base not in {"و", "ي", "ى"}:
                continue
            if FATHAH in local[pos - 1].text and (
                grapheme.has_any(SUKUN_MARKS) or len(grapheme.text) == 1
            ):
                return _span_from_indices(
                    [local[pos - 1].index, grapheme.index],
                    method="fathah_lin_letter",
                )
        return None

    candidates = _mad_candidates(word, graphemes)
    if not candidates:
        return None

    # Waqf rules normally concern the final eligible mad span in the word.
    chosen = candidates[-1] if rule_code == "mad_aridh_lissukun" else candidates[0]
    return LocatedSpan(
        start_grapheme=chosen[0],
        end_grapheme=chosen[1],
        locator_method=chosen[2],
    )


def _locate_idgham_pair(
    word: WordSpan,
    next_word: Optional[WordSpan],
    graphemes: Sequence[Grapheme],
) -> Optional[LocatedSpan]:
    last_index = _last_letter_index(word, graphemes)
    if last_index is None:
        return None

    # Never annotate a madd letter as an idgham consonant. This guardrail
    # suppresses a known false positive in the legacy engine.
    if graphemes[last_index].base in MAD_LETTERS:
        return None

    return _span_from_indices(
        [last_index],
        next_word_index=next_word.word_index if next_word else None,
        confidence=0.9,
        method="final_consonant",
    )


def _locate_ra(
    word: WordSpan,
    graphemes: Sequence[Grapheme],
) -> Optional[LocatedSpan]:
    indices = _find_indices_by_base(word, graphemes, {"ر"})
    return _span_from_indices([indices[0]]) if indices else None


def _locate_lam_jalalah(
    word: WordSpan,
    graphemes: Sequence[Grapheme],
) -> Optional[LocatedSpan]:
    stripped = strip_harakat(word.text).replace("ٱ", "ا")
    if "الله" not in stripped and not stripped.endswith("لله"):
        return None

    lam_indices = _find_indices_by_base(word, graphemes, {"ل"})
    if not lam_indices:
        return None

    # The second lam is normally the pronounced lam of lafzul jalalah.
    target = lam_indices[1] if len(lam_indices) > 1 else lam_indices[0]
    return _span_from_indices([target], method="lafzul_jalalah_lam")


def _locate_saktah(
    word: WordSpan,
    graphemes: Sequence[Grapheme],
) -> Optional[LocatedSpan]:
    for grapheme in _word_graphemes(word, graphemes):
        if SAKTAH in grapheme.text:
            return _span_from_indices([grapheme.index])
    return None


def _resolve_applies_when(
    definition: TajwidRuleDefinition,
    *,
    rule_code: str,
    span: LocatedSpan,
    word: WordSpan,
    words: Sequence[WordSpan],
) -> str:
    if rule_code in WAQF_ONLY_RULES:
        return TajwidAppliesWhen.WAQF.value

    if rule_code in {
        "idgham_bighunnah",
        "idgham_bilaghunnah",
        "mad_jaiz_munfasil",
        *IDGHAM_RULES,
    }:
        return TajwidAppliesWhen.WASL.value

    if definition.default_applies_when != TajwidAppliesWhen.CONTEXTUAL:
        return definition.default_applies_when.value

    # Contextual nun/mim rules at a word boundary are only active when the
    # reciter joins the words. Rules located inside a word remain active in
    # both reading modes.
    if span.next_word_index is not None and word.word_index < len(words) - 1:
        return TajwidAppliesWhen.WASL.value

    return TajwidAppliesWhen.BOTH.value


def _legacy_rule_is_plausible(
    rule_code: str,
    word: WordSpan,
    words: Sequence[WordSpan],
    graphemes: Sequence[Grapheme],
) -> Tuple[bool, Optional[str]]:
    """Guardrails for known unsafe outputs from the legacy rule detector."""

    is_last_word = word.word_index == len(words) - 1
    stripped = strip_harakat(word.text).replace("ٱ", "ا")

    if rule_code == "qalqalah_kubra" and not is_last_word:
        return False, "qalqalah_kubra_requires_final_waqf"

    if rule_code in {"mad_aridh_lissukun", "mad_lin", "mad_iwad"} and not is_last_word:
        return False, "waqf_rule_requires_final_word"

    if rule_code in {"mad_silah_qasirah", "mad_silah_thawilah"}:
        if "الله" in stripped or stripped.endswith("لله"):
            return False, "ha_in_lafzul_jalalah_is_not_ha_dhamir"

    if rule_code in IDGHAM_RULES and is_last_word:
        return False, "cross_word_idgham_requires_next_word"

    if rule_code in IDGHAM_RULES:
        last_index = _last_letter_index(word, graphemes)
        if last_index is not None and graphemes[last_index].base in MAD_LETTERS:
            return False, "mad_letter_cannot_be_idgham_trigger"

    return True, None


def _resolve_lam_jalalah_rule_code(
    rule_code: str,
    word: WordSpan,
    previous_word: Optional[WordSpan],
    graphemes: Sequence[Grapheme],
) -> str:
    """
    Resolve tafkhim/tarqiq across a word boundary. The legacy engine only
    inspects lafzul jalalah itself and therefore defaults to tafkhim for
    expressions such as "بِسْمِ اللَّهِ".
    """

    if rule_code not in LAM_JALALAH_RULES:
        return rule_code

    local = list(_word_graphemes(word, graphemes))
    lam_indices = [index for index, g in enumerate(local) if g.base == "ل"]
    target_local = lam_indices[1] if len(lam_indices) > 1 else (lam_indices[0] if lam_indices else None)

    # First inspect any pronounced vowel inside the same token before the
    # jalalah lam, e.g. بِاللَّهِ.
    if target_local is not None:
        for grapheme in reversed(local[:target_local]):
            if KASRAH in grapheme.text:
                return "tarqiq_lam_jalalah"
            if FATHAH in grapheme.text or DAMMAH in grapheme.text:
                return "tafkhim_lam_jalalah"

    # For a standalone اللَّه token, inspect the previous Quran word.
    if previous_word is not None:
        for grapheme in reversed(_word_graphemes(previous_word, graphemes)):
            if KASRAH in grapheme.text:
                return "tarqiq_lam_jalalah"
            if FATHAH in grapheme.text or DAMMAH in grapheme.text:
                return "tafkhim_lam_jalalah"

    return "tafkhim_lam_jalalah"


def _locate_rule(
    rule_code: str,
    word: WordSpan,
    next_word: Optional[WordSpan],
    graphemes: Sequence[Grapheme],
) -> Optional[LocatedSpan]:
    if rule_code in NUN_TANWIN_RULES:
        return _locate_nun_or_tanwin(word, next_word, graphemes)
    if rule_code in MIM_SAKINAH_RULES:
        return _locate_mim_sakinah(word, next_word, graphemes)
    if rule_code == "qalqalah_sugra":
        return _locate_qalqalah(word, graphemes, kubra=False)
    if rule_code == "qalqalah_kubra":
        return _locate_qalqalah(word, graphemes, kubra=True)
    if rule_code == "ghunnah":
        return _locate_ghunnah(word, graphemes)
    if rule_code in {"alif_lam_syamsiah", "alif_lam_qamariah"}:
        return _locate_alif_lam(word, graphemes)
    if rule_code in MAD_RULES:
        return _locate_mad(rule_code, word, graphemes)
    if rule_code in IDGHAM_RULES:
        return _locate_idgham_pair(word, next_word, graphemes)
    if rule_code in RA_RULES:
        return _locate_ra(word, graphemes)
    if rule_code in LAM_JALALAH_RULES:
        return _locate_lam_jalalah(word, graphemes)
    if rule_code == "saktah":
        return _locate_saktah(word, graphemes)
    return None


def _annotation_key(annotation: Mapping[str, Any]) -> Tuple[Any, ...]:
    return (
        annotation["rule_code"],
        annotation["start_grapheme"],
        annotation["end_grapheme"],
        annotation["applies_when"],
    )


def _validate_annotation_bounds(
    text: str,
    graphemes: Sequence[Grapheme],
    annotations: Sequence[Mapping[str, Any]],
) -> None:
    for annotation in annotations:
        start = annotation["start_grapheme"]
        end = annotation["end_grapheme"]
        if not (0 <= start < end <= len(graphemes)):
            raise TajwidAnnotationError(
                f"Invalid grapheme range {start}:{end} for "
                f"{annotation['rule_code']}."
            )
        reconstructed = "".join(g.text for g in graphemes[start:end])
        if reconstructed != annotation["arabic_segment"]:
            raise TajwidAnnotationError(
                f"Arabic segment mismatch for {annotation['rule_code']}: "
                f"{reconstructed!r} != {annotation['arabic_segment']!r}."
            )
        codepoint_start = graphemes[start].codepoint_start
        codepoint_end = graphemes[end - 1].codepoint_end
        if text[codepoint_start:codepoint_end] != annotation["arabic_segment"]:
            raise TajwidAnnotationError(
                f"Codepoint range mismatch for {annotation['rule_code']}."
            )


def _mode_allows(annotation: Mapping[str, Any], reading_mode: str) -> bool:
    # Mode ayah adalah mode display default: bacaan disambung di dalam ayat
    # dan berhenti pada akhir ayat, sehingga anotasi wasl dan waqf sama-sama
    # perlu ditampilkan. Mode wasl/waqf yang lebih sempit disediakan untuk
    # assessment atau preview khusus.
    if reading_mode == "ayah":
        return True
    applies_when = annotation["applies_when"]
    return applies_when == "both" or applies_when == reading_mode


def build_render_segments(
    ayah_text: str,
    annotations: Sequence[Mapping[str, Any]],
    *,
    reading_mode: str = "ayah",
) -> List[Dict[str, str]]:
    """
    Convert possibly-overlapping annotations into non-overlapping frontend
    segments. The rule with the lowest priority number wins each grapheme.
    """

    if reading_mode not in {"ayah", "wasl", "waqf"}:
        raise ValueError("reading_mode harus 'ayah', 'wasl', atau 'waqf'.")

    graphemes = split_graphemes(ayah_text)
    coverage: List[List[Mapping[str, Any]]] = [[] for _ in graphemes]

    for annotation in annotations:
        if not _mode_allows(annotation, reading_mode):
            continue
        for index in range(
            annotation["start_grapheme"],
            annotation["end_grapheme"],
        ):
            coverage[index].append(annotation)

    labels: List[Optional[Mapping[str, Any]]] = []
    for candidates in coverage:
        if not candidates:
            labels.append(None)
            continue
        labels.append(
            min(
                candidates,
                key=lambda item: (
                    item["priority"],
                    item["rule_code"],
                ),
            )
        )

    raw_segments: List[Dict[str, str]] = []
    segment_start = 0

    def label_key(label: Optional[Mapping[str, Any]]) -> Tuple[Any, ...]:
        if label is None:
            return ("regular",)
        return (
            label["rule_code"],
            label["display_group"],
            label["color"],
            label["rule_description"],
        )

    for index in range(1, len(graphemes) + 1):
        previous_label = labels[index - 1]
        next_label = labels[index] if index < len(graphemes) else object()
        if index < len(graphemes) and label_key(previous_label) == label_key(next_label):
            continue

        arabic = "".join(g.text for g in graphemes[segment_start:index])
        if previous_label is None:
            segment = {
                **dict(REGULAR_RENDER_RULE),
                "arabic": arabic,
            }
        else:
            segment = {
                "rule_name": previous_label["display_group"],
                "color": previous_label["color"],
                "rule_description": previous_label["rule_description"],
                "arabic": arabic,
            }
        raw_segments.append(segment)
        segment_start = index

    # Avoid standalone whitespace segments. Appending whitespace to the
    # preceding visible segment preserves exact reconstruction and produces a
    # cleaner Flutter RichText span list.
    segments: List[Dict[str, str]] = []
    for segment in raw_segments:
        if segment["arabic"].isspace() and segments:
            segments[-1]["arabic"] += segment["arabic"]
        else:
            segments.append(segment)

    reconstructed = "".join(segment["arabic"] for segment in segments)
    if reconstructed != ayah_text:
        raise TajwidAnnotationError(
            "Render segments tidak dapat merekonstruksi ayat secara identik."
        )

    return segments


def analyze_tajwid_annotations(
    ayah_text: str,
    *,
    user_level: Optional[str] = None,
    reading_mode: str = "ayah",
    strict: bool = False,
) -> Dict[str, Any]:
    """
    Generate safe, grapheme-aligned expected tajwid annotations.

    This function deliberately does not mutate or replace legacy
    `analyze_tajwid()`. It converts its rule findings into deterministic spans,
    applies guardrails, records every suppression/unlocatable rule, and then
    builds the frontend render segments.
    """

    if not isinstance(ayah_text, str) or not ayah_text.strip():
        raise ValueError("ayah_text wajib berupa teks Arab yang tidak kosong.")
    if reading_mode not in {"ayah", "wasl", "waqf"}:
        raise ValueError("reading_mode harus 'ayah', 'wasl', atau 'waqf'.")

    graphemes = split_graphemes(ayah_text)
    words = split_word_spans(ayah_text, graphemes)
    legacy_results = analyze_tajwid(ayah_text, user_level=user_level)

    annotations: List[Dict[str, Any]] = []
    issues: List[Dict[str, Any]] = []

    for word_result in legacy_results:
        word_index = word_result.get("word_index")
        if not isinstance(word_index, int) or not (0 <= word_index < len(words)):
            issues.append(
                {
                    "type": "invalid_word_index",
                    "severity": "error",
                    "word_index": word_index,
                    "word": word_result.get("word"),
                }
            )
            continue

        word = words[word_index]
        previous_word = words[word_index - 1] if word_index > 0 else None
        next_word = words[word_index + 1] if word_index + 1 < len(words) else None

        for legacy_rule in word_result.get("rules", []):
            rule_code = legacy_rule.get("rule")
            rule_code = _resolve_lam_jalalah_rule_code(
                rule_code,
                word,
                previous_word,
                graphemes,
            )
            try:
                definition = get_rule_definition(rule_code)
            except KeyError as exc:
                issue = {
                    "type": "unregistered_rule",
                    "severity": "error",
                    "rule_code": rule_code,
                    "word_index": word_index,
                    "word": word.text,
                    "detail": str(exc),
                }
                issues.append(issue)
                if strict:
                    raise TajwidAnnotationError(str(issue)) from exc
                continue

            plausible, reason = _legacy_rule_is_plausible(
                rule_code,
                word,
                words,
                graphemes,
            )
            if not plausible:
                issues.append(
                    {
                        "type": "suppressed_legacy_false_positive",
                        "severity": "warning",
                        "rule_code": rule_code,
                        "word_index": word_index,
                        "word": word.text,
                        "reason": reason,
                    }
                )
                continue

            span = _locate_rule(
                rule_code,
                word,
                next_word,
                graphemes,
            )
            if span is None:
                issue = {
                    "type": "unlocatable_rule",
                    "severity": "error",
                    "rule_code": rule_code,
                    "word_index": word_index,
                    "word": word.text,
                }
                issues.append(issue)
                if strict:
                    raise TajwidAnnotationError(str(issue))
                continue

            applies_when = _resolve_applies_when(
                definition,
                rule_code=rule_code,
                span=span,
                word=word,
                words=words,
            )
            codepoint_start = graphemes[span.start_grapheme].codepoint_start
            codepoint_end = graphemes[span.end_grapheme - 1].codepoint_end
            arabic_segment = ayah_text[codepoint_start:codepoint_end]

            annotations.append(
                {
                    "rule_code": definition.code,
                    "rule_name": definition.name,
                    "display_group": definition.display_group.value,
                    "color": definition.color,
                    "rule_description": definition.description,
                    "priority": definition.priority,
                    "assessment_family": definition.assessment_family.value,
                    "word_index": word_index,
                    "next_word_index": span.next_word_index,
                    "start_grapheme": span.start_grapheme,
                    "end_grapheme": span.end_grapheme,
                    "start_codepoint": codepoint_start,
                    "end_codepoint": codepoint_end,
                    "arabic_segment": arabic_segment,
                    "applies_when": applies_when,
                    "expected_features": dict(definition.expected_features),
                    "engine_version": ANNOTATION_ENGINE_VERSION,
                    "locator_confidence": span.locator_confidence,
                    "locator_method": span.locator_method,
                    "is_verified": False,
                }
            )

    # Stable de-duplication after all locators have run.
    unique: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
    for annotation in annotations:
        key = _annotation_key(annotation)
        current = unique.get(key)
        if current is None or annotation["priority"] < current["priority"]:
            unique[key] = annotation

    annotations = sorted(
        unique.values(),
        key=lambda item: (
            item["start_grapheme"],
            item["end_grapheme"],
            item["priority"],
            item["rule_code"],
        ),
    )

    _validate_annotation_bounds(ayah_text, graphemes, annotations)
    render_segments = build_render_segments(
        ayah_text,
        annotations,
        reading_mode=reading_mode,
    )

    result = {
        "engine_version": ANNOTATION_ENGINE_VERSION,
        "reading_mode": reading_mode,
        "ayah_text": ayah_text,
        "grapheme_count": len(graphemes),
        "word_count": len(words),
        "annotations": annotations,
        "issues": issues,
        "render_segments": render_segments,
        "is_safe_to_persist": not any(
            issue.get("severity") == "error" for issue in issues
        ),
    }

    if strict and issues:
        raise TajwidAnnotationError(
            f"Annotation generation menghasilkan {len(issues)} issue(s)."
        )

    return result


def validate_render_segments(
    ayah_text: str,
    segments: Sequence[Mapping[str, Any]],
) -> None:
    """Public validation helper used by tests and future backfill commands."""

    reconstructed = "".join(str(segment.get("arabic", "")) for segment in segments)
    if reconstructed != ayah_text:
        raise TajwidAnnotationError(
            "Gabungan arabic pada render segments tidak identik dengan ayat."
        )

    for index, segment in enumerate(segments):
        arabic = str(segment.get("arabic", ""))
        if not arabic:
            raise TajwidAnnotationError(f"Render segment index {index} kosong.")
        first_non_space = next((char for char in arabic if not char.isspace()), "")
        if first_non_space and unicodedata.category(first_non_space).startswith("M"):
            raise TajwidAnnotationError(
                f"Render segment index {index} dimulai dengan combining mark."
            )
