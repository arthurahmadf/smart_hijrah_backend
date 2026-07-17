from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Optional, Sequence, Tuple

from .grapheme_parser import (
    CanonicalGrapheme,
    GraphemeKind,
    ParsedGraphemes,
    PronunciationState,
    parse_graphemes,
)


TOKEN_STREAM_VERSION = "3.0.0-alpha.1"


@dataclass(frozen=True, slots=True)
class WordToken:
    index: int
    lexical_index: int
    text: str
    grapheme_start: int
    grapheme_end: int
    codepoint_start: int
    codepoint_end: int
    letter_indices: Tuple[int, ...]

    def __post_init__(self) -> None:
        if self.index < 0 or self.lexical_index < 0:
            raise ValueError("Word index tidak boleh negatif.")
        if self.grapheme_end <= self.grapheme_start:
            raise ValueError("Word grapheme span tidak valid.")
        if self.codepoint_end <= self.codepoint_start:
            raise ValueError("Word codepoint span tidak valid.")
        if not self.letter_indices:
            raise ValueError("WordToken wajib memiliki minimal satu huruf.")


@dataclass(frozen=True, slots=True)
class WordBoundary:
    left_word_index: int
    right_word_index: int
    separator_grapheme_start: int
    separator_grapheme_end: int
    separator_text: str


@dataclass(frozen=True, slots=True)
class CanonicalTokenStream:
    source_text: str
    graphemes: Tuple[CanonicalGrapheme, ...]
    words: Tuple[WordToken, ...]
    boundaries: Tuple[WordBoundary, ...]
    parser_version: str
    stream_version: str = TOKEN_STREAM_VERSION

    def reconstruct(self) -> str:
        return "".join(item.text for item in self.graphemes)

    def grapheme(self, index: int) -> CanonicalGrapheme:
        try:
            return self.graphemes[index]
        except IndexError as exc:
            raise IndexError(f"Grapheme index {index} di luar stream.") from exc

    def word(self, index: int) -> WordToken:
        try:
            return self.words[index]
        except IndexError as exc:
            raise IndexError(f"Word index {index} di luar stream.") from exc

    def grapheme_text(self, start: int, end: int) -> str:
        self._validate_grapheme_range(start, end)
        return "".join(item.text for item in self.graphemes[start:end])

    def codepoint_span_for_graphemes(self, start: int, end: int) -> Tuple[int, int]:
        self._validate_grapheme_range(start, end)
        return (
            self.graphemes[start].codepoint_start,
            self.graphemes[end - 1].codepoint_end,
        )

    def _validate_grapheme_range(self, start: int, end: int) -> None:
        if start < 0 or end <= start or end > len(self.graphemes):
            raise ValueError(
                f"Grapheme range [{start}, {end}) tidak valid untuk "
                f"panjang {len(self.graphemes)}."
            )

    def iter_letters(self) -> Iterator[CanonicalGrapheme]:
        return (
            item for item in self.graphemes if item.kind == GraphemeKind.LETTER
        )

    def next_letter(
        self,
        index: int,
        *,
        include_contextual: bool = True,
        same_word_only: bool = False,
    ) -> Optional[CanonicalGrapheme]:
        origin = self.grapheme(index)
        for candidate in self.graphemes[index + 1:]:
            if same_word_only and candidate.word_index != origin.word_index:
                return None
            if candidate.kind != GraphemeKind.LETTER:
                continue
            if (
                not include_contextual
                and candidate.pronunciation_state == PronunciationState.CONTEXTUAL
            ):
                continue
            return candidate
        return None

    def previous_letter(
        self,
        index: int,
        *,
        include_contextual: bool = True,
        same_word_only: bool = False,
    ) -> Optional[CanonicalGrapheme]:
        origin = self.grapheme(index)
        for candidate in reversed(self.graphemes[:index]):
            if same_word_only and candidate.word_index != origin.word_index:
                return None
            if candidate.kind != GraphemeKind.LETTER:
                continue
            if (
                not include_contextual
                and candidate.pronunciation_state == PronunciationState.CONTEXTUAL
            ):
                continue
            return candidate
        return None

    def next_pronounced_candidate(
        self,
        index: int,
        *,
        same_word_only: bool = False,
    ) -> Optional[CanonicalGrapheme]:
        origin = self.grapheme(index)
        for candidate in self.graphemes[index + 1:]:
            if same_word_only and candidate.word_index != origin.word_index:
                return None
            if candidate.is_pronounced_candidate:
                return candidate
        return None

    def previous_pronounced_candidate(
        self,
        index: int,
        *,
        same_word_only: bool = False,
    ) -> Optional[CanonicalGrapheme]:
        origin = self.grapheme(index)
        for candidate in reversed(self.graphemes[:index]):
            if same_word_only and candidate.word_index != origin.word_index:
                return None
            if candidate.is_pronounced_candidate:
                return candidate
        return None

    def validate_integrity(self) -> Tuple[str, ...]:
        issues = []
        if self.reconstruct() != self.source_text:
            issues.append("reconstruction_mismatch")
        for expected, word in enumerate(self.words):
            if word.index != expected:
                issues.append(f"non_contiguous_word_index:{expected}")
            if self.source_text[word.codepoint_start:word.codepoint_end] != word.text:
                issues.append(f"word_text_mismatch:{expected}")
            for letter_index in word.letter_indices:
                item = self.grapheme(letter_index)
                if item.word_index != word.index:
                    issues.append(f"word_mapping_mismatch:{letter_index}")
        for expected, boundary in enumerate(self.boundaries):
            if boundary.left_word_index + 1 != boundary.right_word_index:
                issues.append(f"invalid_boundary_words:{expected}")
            separator = self.grapheme_text(
                boundary.separator_grapheme_start,
                boundary.separator_grapheme_end,
            )
            if separator != boundary.separator_text:
                issues.append(f"boundary_text_mismatch:{expected}")
        return tuple(issues)


def _word_runs(parsed: ParsedGraphemes) -> Tuple[Tuple[int, int], ...]:
    """Return grapheme spans containing at least one Arabic letter.

    Quranic marks before/after a word do not become words. A whitespace run is
    the primary separator. Non-letter ornaments and verse markers are excluded
    from word spans, preventing the legacy word-index drift.
    """

    runs = []
    run_start: Optional[int] = None
    run_has_letter = False

    for item in parsed.graphemes:
        hard_separator = item.kind in {
            GraphemeKind.WHITESPACE,
            GraphemeKind.VERSE_MARKER,
            GraphemeKind.ORNAMENT,
            GraphemeKind.DIGIT,
            GraphemeKind.PUNCTUATION,
            GraphemeKind.UNKNOWN,
        }
        if hard_separator:
            if run_start is not None and run_has_letter:
                runs.append((run_start, item.index))
            run_start = None
            run_has_letter = False
            continue

        if item.kind == GraphemeKind.QURANIC_MARK and run_start is None:
            # Leading standalone mark (e.g. ۙ) is metadata, not a word.
            continue

        if run_start is None:
            run_start = item.index
        if item.kind == GraphemeKind.LETTER:
            run_has_letter = True

    if run_start is not None and run_has_letter:
        runs.append((run_start, len(parsed.graphemes)))
    return tuple(runs)


def build_token_stream(text: str) -> CanonicalTokenStream:
    parsed = parse_graphemes(text)
    word_runs = _word_runs(parsed)

    words = []
    word_by_grapheme = {}
    for word_index, (start, end) in enumerate(word_runs):
        items = parsed.graphemes[start:end]
        letter_indices = tuple(
            item.index for item in items if item.kind == GraphemeKind.LETTER
        )
        if not letter_indices:
            continue
        codepoint_start = items[0].codepoint_start
        codepoint_end = items[-1].codepoint_end
        word_text = text[codepoint_start:codepoint_end]
        words.append(
            WordToken(
                index=word_index,
                lexical_index=word_index,
                text=word_text,
                grapheme_start=start,
                grapheme_end=end,
                codepoint_start=codepoint_start,
                codepoint_end=codepoint_end,
                letter_indices=letter_indices,
            )
        )
        for grapheme_index in range(start, end):
            if parsed.graphemes[grapheme_index].kind == GraphemeKind.LETTER:
                word_by_grapheme[grapheme_index] = word_index

    contextual_graphemes = []
    for item in parsed.graphemes:
        word_index = word_by_grapheme.get(item.index)
        if word_index is None:
            contextual_graphemes.append(item)
            continue
        word = words[word_index]
        contextual_graphemes.append(
            item.with_word_context(
                word_index=word_index,
                lexical_word_index=word.lexical_index,
                is_word_start=item.index == word.letter_indices[0],
                is_word_end=item.index == word.letter_indices[-1],
            )
        )

    boundaries = []
    for left, right in zip(words, words[1:]):
        separator_start = left.grapheme_end
        separator_end = right.grapheme_start
        if separator_end <= separator_start:
            # Adjacent words without explicit whitespace are unsupported until
            # prefix/lexeme segmentation is introduced; do not invent a span.
            continue
        separator_text = "".join(
            item.text for item in contextual_graphemes[separator_start:separator_end]
        )
        boundaries.append(
            WordBoundary(
                left_word_index=left.index,
                right_word_index=right.index,
                separator_grapheme_start=separator_start,
                separator_grapheme_end=separator_end,
                separator_text=separator_text,
            )
        )

    stream = CanonicalTokenStream(
        source_text=text,
        graphemes=tuple(contextual_graphemes),
        words=tuple(words),
        boundaries=tuple(boundaries),
        parser_version=parsed.parser_version,
    )
    issues = stream.validate_integrity()
    if issues:
        raise ValueError(f"Token stream integrity gagal: {issues}")
    return stream
