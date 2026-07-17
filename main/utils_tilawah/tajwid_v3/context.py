from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .grapheme_parser import CanonicalGrapheme
from .token_stream import CanonicalTokenStream, WordToken


@dataclass(frozen=True, slots=True)
class GraphemeContext:
    current: CanonicalGrapheme
    previous_letter: Optional[CanonicalGrapheme]
    next_letter: Optional[CanonicalGrapheme]
    previous_pronounced_candidate: Optional[CanonicalGrapheme]
    next_pronounced_candidate: Optional[CanonicalGrapheme]
    word: Optional[WordToken]
    previous_word: Optional[WordToken]
    next_word: Optional[WordToken]


def build_grapheme_context(
    stream: CanonicalTokenStream,
    grapheme_index: int,
) -> GraphemeContext:
    current = stream.grapheme(grapheme_index)
    word = (
        stream.word(current.word_index)
        if current.word_index is not None
        else None
    )
    previous_word = None
    next_word = None
    if word is not None:
        if word.index > 0:
            previous_word = stream.word(word.index - 1)
        if word.index + 1 < len(stream.words):
            next_word = stream.word(word.index + 1)

    return GraphemeContext(
        current=current,
        previous_letter=stream.previous_letter(grapheme_index),
        next_letter=stream.next_letter(grapheme_index),
        previous_pronounced_candidate=stream.previous_pronounced_candidate(
            grapheme_index
        ),
        next_pronounced_candidate=stream.next_pronounced_candidate(
            grapheme_index
        ),
        word=word,
        previous_word=previous_word,
        next_word=next_word,
    )
