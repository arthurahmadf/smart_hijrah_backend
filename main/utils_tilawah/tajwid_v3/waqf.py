from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from .annotations import TextSpan, make_text_span
from .grapheme_parser import CanonicalGrapheme
from .token_stream import CanonicalTokenStream


WAQF_ANALYZER_VERSION = "3.0.0-alpha.1"


class WaqfSignKind(str, Enum):
    CONTINUE_PREFERRED = "continue_preferred"
    STOP_PREFERRED = "stop_preferred"
    MANDATORY_STOP = "mandatory_stop"
    DO_NOT_STOP = "do_not_stop"
    PERMISSIBLE_STOP = "permissible_stop"
    PAIRED_STOP = "paired_stop"
    SAKTAH = "saktah"


# Unicode Quranic signs used by QPC/Uthmani-compatible text. These are
# semantic rendering hints, not additional Tajwid rule codes.
WAQF_SIGN_MAP = {
    "\u06d6": WaqfSignKind.CONTINUE_PREFERRED,  # صلى
    "\u06d7": WaqfSignKind.STOP_PREFERRED,      # قلى
    "\u06d8": WaqfSignKind.MANDATORY_STOP,      # م
    "\u06d9": WaqfSignKind.DO_NOT_STOP,         # لا
    "\u06da": WaqfSignKind.PERMISSIBLE_STOP,    # ج
    "\u06db": WaqfSignKind.PAIRED_STOP,         # تعانق الوقف
    "\u06dc": WaqfSignKind.SAKTAH,              # س
}


@dataclass(frozen=True, slots=True)
class WaqfSignHint:
    sign: str
    kind: WaqfSignKind
    span: TextSpan
    word_index: int | None
    paired: bool
    analyzer_version: str = WAQF_ANALYZER_VERSION

    def to_dict(self) -> dict:
        return {
            "sign": self.sign,
            "kind": self.kind.value,
            "span": self.span.to_dict(),
            "word_index": self.word_index,
            "paired": self.paired,
            "analyzer_version": self.analyzer_version,
        }


def _word_index_for_mark(
    stream: CanonicalTokenStream,
    grapheme: CanonicalGrapheme,
) -> int | None:
    if grapheme.word_index is not None:
        return grapheme.word_index
    previous = stream.previous_letter(grapheme.index)
    return previous.word_index if previous is not None else None


def extract_waqf_sign_hints(
    stream: CanonicalTokenStream,
) -> Tuple[WaqfSignHint, ...]:
    hints: list[WaqfSignHint] = []
    for grapheme in stream.graphemes:
        for sign, kind in WAQF_SIGN_MAP.items():
            if sign not in grapheme.text:
                continue
            hints.append(
                WaqfSignHint(
                    sign=sign,
                    kind=kind,
                    span=make_text_span(stream, grapheme.index, grapheme.index + 1),
                    word_index=_word_index_for_mark(stream, grapheme),
                    paired=kind == WaqfSignKind.PAIRED_STOP,
                )
            )
    return tuple(hints)
