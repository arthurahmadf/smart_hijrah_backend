from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple

import regex


PARSER_VERSION = "3.0.0-alpha.1"


class GraphemeKind(str, Enum):
    LETTER = "letter"
    WHITESPACE = "whitespace"
    QURANIC_MARK = "quranic_mark"
    VERSE_MARKER = "verse_marker"
    ORNAMENT = "ornament"
    DIGIT = "digit"
    PUNCTUATION = "punctuation"
    UNKNOWN = "unknown"


class PronunciationState(str, Enum):
    PRONOUNCED_CANDIDATE = "pronounced_candidate"
    CONTEXTUAL = "contextual"
    NON_PRONOUNCED = "non_pronounced"


class MarkTag(str, Enum):
    FATHA = "fatha"
    DAMMA = "damma"
    KASRA = "kasra"
    FATHATAN = "fathatan"
    DAMMATAN = "dammatan"
    KASRATAN = "kasratan"
    SHADDA = "shadda"
    SUKUN = "sukun"
    SUKUN_UTHMANI = "sukun_uthmani"
    DAGGER_ALEF = "dagger_alef"
    MADDAH = "maddah"
    HAMZA_ABOVE = "hamza_above"
    HAMZA_BELOW = "hamza_below"
    IQLAB = "iqlab"
    WAQF = "waqf"
    SMALL_LETTER = "small_letter"
    ORTHOGRAPHIC = "orthographic"
    OTHER_COMBINING = "other_combining"


MARK_TAGS: Mapping[str, MarkTag] = MappingProxyType(
    {
        "\u064e": MarkTag.FATHA,
        "\u064f": MarkTag.DAMMA,
        "\u0650": MarkTag.KASRA,
        "\u064b": MarkTag.FATHATAN,
        "\u064c": MarkTag.DAMMATAN,
        "\u064d": MarkTag.KASRATAN,
        "\u0651": MarkTag.SHADDA,
        "\u0652": MarkTag.SUKUN,
        "\u06e1": MarkTag.SUKUN_UTHMANI,
        "\u0670": MarkTag.DAGGER_ALEF,
        "\u0653": MarkTag.MADDAH,
        "\u0654": MarkTag.HAMZA_ABOVE,
        "\u0655": MarkTag.HAMZA_BELOW,
        "\u06e2": MarkTag.IQLAB,
    }
)

# Quranic annotation marks. Some are pause/stop marks, while others are
# orthographic signs. We preserve every codepoint and classify conservatively.
WAQF_MARK_CODEPOINTS = frozenset(
    {
        "\u06d6",  # small high ligature sad with lam with alef maqsura
        "\u06d7",  # small high ligature qaf with lam with alef maqsura
        "\u06d8",  # small high meem initial form
        "\u06d9",  # small high lam alef
        "\u06da",  # small high jeem
        "\u06db",  # small high three dots
        "\u06dc",  # small high seen
        "\u06de",  # rub el hizb (also ornament; classified separately alone)
    }
)

SMALL_LETTER_CODEPOINTS = frozenset(
    {
        "\u06e5",  # small waw
        "\u06e6",  # small ya
    }
)

ORTHOGRAPHIC_MARK_RANGES = (
    (0x0610, 0x061A),
    (0x06DF, 0x06E0),
    (0x06E3, 0x06E4),
    (0x06E7, 0x06E8),
    (0x06EA, 0x06ED),
)

VERSE_MARKER_CODEPOINTS = frozenset({"\u06dd"})
ORNAMENT_CODEPOINTS = frozenset({"\u06de", "\u06e9"})
HAMZAT_WASL = "\u0671"


ALEF_FOLD = frozenset({"ا", "أ", "إ", "آ", "ٱ", "ٲ", "ٳ"})
YEH_FOLD = frozenset({"ي", "ى", "ی"})
WAW_FOLD = frozenset({"و", "ؤ"})


def _is_in_ranges(char: str, ranges: Sequence[Tuple[int, int]]) -> bool:
    value = ord(char)
    return any(start <= value <= end for start, end in ranges)


def is_arabic_letter(char: str) -> bool:
    if not char:
        return False
    category = unicodedata.category(char)
    name = unicodedata.name(char, "")
    return category.startswith("L") and "ARABIC" in name


def is_arabic_digit(char: str) -> bool:
    return char.isdigit() and "ARABIC" in unicodedata.name(char, "")


def fold_base_letter(char: Optional[str]) -> Optional[str]:
    if char is None:
        return None
    if char in ALEF_FOLD:
        return "ا"
    if char in YEH_FOLD:
        return "ي"
    if char in WAW_FOLD:
        return "و"
    return char


def classify_mark(char: str) -> Optional[MarkTag]:
    direct = MARK_TAGS.get(char)
    if direct is not None:
        return direct
    if char in WAQF_MARK_CODEPOINTS:
        return MarkTag.WAQF
    if char in SMALL_LETTER_CODEPOINTS:
        return MarkTag.SMALL_LETTER
    if _is_in_ranges(char, ORTHOGRAPHIC_MARK_RANGES):
        return MarkTag.ORTHOGRAPHIC
    if unicodedata.combining(char):
        return MarkTag.OTHER_COMBINING
    return None


def _find_base_letter(grapheme: str) -> Optional[str]:
    for char in grapheme:
        if is_arabic_letter(char):
            return char
    return None


def _classify_grapheme(grapheme: str, base_letter: Optional[str]) -> GraphemeKind:
    if grapheme.isspace():
        return GraphemeKind.WHITESPACE
    if grapheme in ORNAMENT_CODEPOINTS:
        return GraphemeKind.ORNAMENT
    if any(char in VERSE_MARKER_CODEPOINTS for char in grapheme):
        return GraphemeKind.VERSE_MARKER
    if base_letter is not None:
        return GraphemeKind.LETTER
    if all(is_arabic_digit(char) for char in grapheme):
        return GraphemeKind.DIGIT
    if any(classify_mark(char) is not None for char in grapheme):
        return GraphemeKind.QURANIC_MARK
    if all(unicodedata.category(char).startswith("P") for char in grapheme):
        return GraphemeKind.PUNCTUATION
    return GraphemeKind.UNKNOWN


def _pronunciation_state(
    kind: GraphemeKind,
    base_letter: Optional[str],
) -> PronunciationState:
    if kind != GraphemeKind.LETTER or base_letter is None:
        return PronunciationState.NON_PRONOUNCED
    if base_letter == HAMZAT_WASL:
        return PronunciationState.CONTEXTUAL
    return PronunciationState.PRONOUNCED_CANDIDATE


@dataclass(frozen=True, slots=True)
class CanonicalGrapheme:
    index: int
    text: str
    codepoint_start: int
    codepoint_end: int
    kind: GraphemeKind
    base_letter: Optional[str]
    folded_base: Optional[str]
    marks: Tuple[str, ...]
    mark_tags: Tuple[MarkTag, ...]
    pronunciation_state: PronunciationState
    word_index: Optional[int] = None
    lexical_word_index: Optional[int] = None
    is_word_start: bool = False
    is_word_end: bool = False

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("Grapheme index tidak boleh negatif.")
        if not self.text:
            raise ValueError("CanonicalGrapheme.text tidak boleh kosong.")
        if self.codepoint_start < 0 or self.codepoint_end <= self.codepoint_start:
            raise ValueError("Codepoint span grapheme tidak valid.")
        if self.base_letter is None and self.folded_base is not None:
            raise ValueError("folded_base tidak boleh ada tanpa base_letter.")

    @property
    def is_letter(self) -> bool:
        return self.kind == GraphemeKind.LETTER

    @property
    def is_pronounced_candidate(self) -> bool:
        return self.pronunciation_state in {
            PronunciationState.PRONOUNCED_CANDIDATE,
            PronunciationState.CONTEXTUAL,
        }

    @property
    def has_shadda(self) -> bool:
        return MarkTag.SHADDA in self.mark_tags

    @property
    def has_sukun(self) -> bool:
        return bool(
            {MarkTag.SUKUN, MarkTag.SUKUN_UTHMANI}.intersection(self.mark_tags)
        )

    @property
    def has_tanwin(self) -> bool:
        return bool(
            {
                MarkTag.FATHATAN,
                MarkTag.DAMMATAN,
                MarkTag.KASRATAN,
            }.intersection(self.mark_tags)
        )

    @property
    def has_short_vowel(self) -> bool:
        return bool(
            {MarkTag.FATHA, MarkTag.DAMMA, MarkTag.KASRA}.intersection(
                self.mark_tags
            )
        )

    @property
    def has_waqf_mark(self) -> bool:
        return MarkTag.WAQF in self.mark_tags

    def with_word_context(
        self,
        *,
        word_index: Optional[int],
        lexical_word_index: Optional[int],
        is_word_start: bool,
        is_word_end: bool,
    ) -> "CanonicalGrapheme":
        return CanonicalGrapheme(
            index=self.index,
            text=self.text,
            codepoint_start=self.codepoint_start,
            codepoint_end=self.codepoint_end,
            kind=self.kind,
            base_letter=self.base_letter,
            folded_base=self.folded_base,
            marks=self.marks,
            mark_tags=self.mark_tags,
            pronunciation_state=self.pronunciation_state,
            word_index=word_index,
            lexical_word_index=lexical_word_index,
            is_word_start=is_word_start,
            is_word_end=is_word_end,
        )


@dataclass(frozen=True, slots=True)
class ParsedGraphemes:
    source_text: str
    graphemes: Tuple[CanonicalGrapheme, ...]
    parser_version: str = PARSER_VERSION

    def reconstruct(self) -> str:
        return "".join(item.text for item in self.graphemes)

    def validate_integrity(self) -> Tuple[str, ...]:
        issues = []
        if self.reconstruct() != self.source_text:
            issues.append("reconstruction_mismatch")
        expected_start = 0
        for expected_index, item in enumerate(self.graphemes):
            if item.index != expected_index:
                issues.append(f"non_contiguous_index:{expected_index}")
            if item.codepoint_start != expected_start:
                issues.append(f"codepoint_gap:{expected_index}")
            if self.source_text[item.codepoint_start:item.codepoint_end] != item.text:
                issues.append(f"codepoint_text_mismatch:{expected_index}")
            expected_start = item.codepoint_end
        if expected_start != len(self.source_text):
            issues.append("codepoint_end_mismatch")
        return tuple(issues)




def _iter_semantic_graphemes(text: str):
    """Yield semantic grapheme spans while preserving every codepoint.

    Unicode ``\\X`` legitimately joins a leading combining Quranic mark to
    preceding whitespace (for example ``" \u06d9"``). For Tajwid word
    boundaries that cluster must be split into a whitespace token and a
    standalone Quranic-mark token. Letter + harakat clusters remain intact.
    """

    for match in regex.finditer(r"\X", text):
        cluster = match.group(0)
        start = match.start()
        if cluster and cluster[0].isspace() and len(cluster) > 1:
            cursor = start
            prefix_length = 0
            for char in cluster:
                if not char.isspace():
                    break
                prefix_length += 1
                yield char, cursor, cursor + 1
                cursor += 1
            remainder = cluster[prefix_length:]
            if remainder:
                yield remainder, cursor, match.end()
            continue
        yield cluster, start, match.end()


def parse_graphemes(text: str) -> ParsedGraphemes:
    if not isinstance(text, str):
        raise TypeError("text harus berupa str.")
    if not text:
        return ParsedGraphemes(source_text=text, graphemes=())

    graphemes = []
    codepoint_cursor = 0
    for index, (grapheme, start, end) in enumerate(
        _iter_semantic_graphemes(text)
    ):
        if start != codepoint_cursor:
            raise ValueError(
                f"Grapheme parser menemukan gap codepoint di posisi {start}."
            )
        codepoint_cursor = end

        base_letter = _find_base_letter(grapheme)
        marks = tuple(char for char in grapheme if char != base_letter)
        mark_tags = tuple(
            tag
            for char in marks
            for tag in (classify_mark(char),)
            if tag is not None
        )
        kind = _classify_grapheme(grapheme, base_letter)

        graphemes.append(
            CanonicalGrapheme(
                index=index,
                text=grapheme,
                codepoint_start=start,
                codepoint_end=end,
                kind=kind,
                base_letter=base_letter,
                folded_base=fold_base_letter(base_letter),
                marks=marks,
                mark_tags=mark_tags,
                pronunciation_state=_pronunciation_state(kind, base_letter),
            )
        )

    parsed = ParsedGraphemes(source_text=text, graphemes=tuple(graphemes))
    issues = parsed.validate_integrity()
    if issues:
        raise ValueError(f"Grapheme integrity gagal: {issues}")
    return parsed
