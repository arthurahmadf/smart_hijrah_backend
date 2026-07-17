from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

from ..annotations import TajwidAnnotationV3, make_text_span
from ..grapheme_parser import CanonicalGrapheme, HAMZAT_WASL, MarkTag
from ..rule_specs import get_rule_spec
from ..specification import AppliesWhen, ReadingMode
from ..token_stream import CanonicalTokenStream, WordToken
from .base import DetectorIssue, DetectorOutput


DETECTOR_ID = "alif_lam_detector_v3.0.0-alpha.1"
SUPPORTED_RULE_CODES = frozenset(
    {
        "alif_lam_qamariyyah",
        "alif_lam_shamsiyyah",
        "lam_jalalah_tafkhim",
        "lam_jalalah_tarqiq",
    }
)

SUN_LETTERS = frozenset({"ت", "ث", "د", "ذ", "ر", "ز", "س", "ش", "ص", "ض", "ط", "ظ", "ل", "ن"})
MOON_LETTERS = frozenset({"ا", "ب", "ج", "ح", "خ", "ع", "غ", "ف", "ق", "ك", "م", "ه", "و", "ي"})
EXPLICIT_ARTICLE_PREFIXES = frozenset({"و", "ف", "ب", "ك"})
CONTRACTED_ARTICLE_LEADING_PREFIXES = frozenset({"و", "ف"})


@dataclass(frozen=True, slots=True)
class _ArticleCandidate:
    word: WordToken
    article_start: CanonicalGrapheme
    article_lam: CanonicalGrapheme
    target: CanonicalGrapheme
    contracted: bool


@dataclass(frozen=True, slots=True)
class _JalalahCandidate:
    word: WordToken
    principal_lam: CanonicalGrapheme
    core_start: CanonicalGrapheme
    predecessor: Optional[CanonicalGrapheme]


def _word_letters(stream: CanonicalTokenStream, word: WordToken) -> Tuple[CanonicalGrapheme, ...]:
    return tuple(stream.grapheme(index) for index in word.letter_indices)


def _has(item: CanonicalGrapheme, tag: MarkTag) -> bool:
    return tag in item.mark_tags


def _valid_explicit_prefix(items: Sequence[CanonicalGrapheme]) -> bool:
    """Validate attached proclitics before explicit alif/hamzat-wasl.

    Supported forms cover the common Quranic combinations:
    ``الـ``, ``والـ``, ``فالـ``, ``بالـ``, ``كالـ``, ``وبالـ``, etc.
    Interrogative hamza is intentionally excluded because forms such as Mad
    Farq require a dedicated lexical/profile resolver.
    """

    if not items:
        return True
    folded = tuple(item.folded_base for item in items)
    if any(base not in EXPLICIT_ARTICLE_PREFIXES for base in folded):
        return False
    if len(folded) == 1:
        return True
    if len(folded) == 2:
        return folded[0] in {"و", "ف"} and folded[1] in {"ب", "ك"}
    return False


def _valid_contracted_prefix(items: Sequence[CanonicalGrapheme]) -> bool:
    if not items:
        return True
    folded = tuple(item.folded_base for item in items)
    return len(folded) == 1 and folded[0] in CONTRACTED_ARTICLE_LEADING_PREFIXES


def _jalalah_candidate(stream: CanonicalTokenStream, word: WordToken) -> Optional[_JalalahCandidate]:
    letters = _word_letters(stream, word)
    for position, item in enumerate(letters):
        if item.folded_base != "ل" or not item.has_shadda:
            continue
        if position + 1 >= len(letters) or letters[position + 1].folded_base != "ه":
            continue

        previous = letters[position - 1] if position > 0 else None
        previous_previous = letters[position - 2] if position > 1 else None

        # Explicit Allah orthography: ا/ٱ + ل + لّ + ه
        if (
            previous is not None
            and previous.folded_base == "ل"
            and previous_previous is not None
            and previous_previous.folded_base == "ا"
            and previous_previous.base_letter in {"ا", HAMZAT_WASL}
        ):
            predecessor = (
                stream.previous_letter(previous_previous.index)
                if previous_previous.index > 0
                else None
            )
            return _JalalahCandidate(
                word=word,
                principal_lam=item,
                core_start=previous_previous,
                predecessor=predecessor,
            )

        # Contracted li-llah forms: لِ + لّ + ه, optionally preceded by و/ف.
        if previous is not None and previous.folded_base == "ل" and _has(previous, MarkTag.KASRA):
            before_prefix = letters[position - 2] if position > 1 else None
            if before_prefix is None or before_prefix.folded_base in CONTRACTED_ARTICLE_LEADING_PREFIXES:
                return _JalalahCandidate(
                    word=word,
                    principal_lam=item,
                    core_start=item,
                    predecessor=previous,
                )
    return None


def _is_lafz_jalalah(stream: CanonicalTokenStream, word: WordToken) -> bool:
    return _jalalah_candidate(stream, word) is not None


def _iter_article_candidates(stream: CanonicalTokenStream) -> Iterable[_ArticleCandidate]:
    for word in stream.words:
        if _is_lafz_jalalah(stream, word):
            continue
        letters = _word_letters(stream, word)

        # Explicit article: [prefixes] + ا/ٱ + ل + target.
        for position, alif in enumerate(letters):
            if alif.base_letter not in {"ا", HAMZAT_WASL}:
                continue
            if position + 2 >= len(letters):
                continue
            article_lam = letters[position + 1]
            target = letters[position + 2]
            if article_lam.folded_base != "ل":
                continue
            if not _valid_explicit_prefix(letters[:position]):
                continue
            yield _ArticleCandidate(
                word=word,
                article_start=alif,
                article_lam=article_lam,
                target=target,
                contracted=False,
            )
            break

        # Contracted li-l article: [و/ف]? + لِ + ل + target.
        for position, prefix_lam in enumerate(letters):
            if prefix_lam.folded_base != "ل" or not _has(prefix_lam, MarkTag.KASRA):
                continue
            if position + 2 >= len(letters):
                continue
            if not _valid_contracted_prefix(letters[:position]):
                continue
            article_lam = letters[position + 1]
            target = letters[position + 2]
            if article_lam.folded_base != "ل":
                continue
            yield _ArticleCandidate(
                word=word,
                article_start=article_lam,
                article_lam=article_lam,
                target=target,
                contracted=True,
            )
            break


def _classify_article(candidate: _ArticleCandidate) -> Optional[str]:
    target_base = candidate.target.folded_base or candidate.target.base_letter
    if target_base in SUN_LETTERS:
        return "alif_lam_shamsiyyah"
    if target_base in MOON_LETTERS:
        return "alif_lam_qamariyyah"
    return None


def _make_article_annotation(
    stream: CanonicalTokenStream,
    candidate: _ArticleCandidate,
    rule_code: str,
    *,
    confidence: float,
) -> TajwidAnnotationV3:
    spec = get_rule_spec(rule_code)
    # For Lam Ta'rif the rule locus is the complete article-target sequence.
    # This gives frontend a contiguous colored segment and remains exact-span.
    span = make_text_span(stream, candidate.article_start.index, candidate.target.index + 1)
    return TajwidAnnotationV3(
        rule_code=rule_code,
        trigger_span=span,
        context_span=span,
        display_span=span,
        word_index=candidate.word.index,
        next_word_index=None,
        applies_when=AppliesWhen.BOTH,
        evidence={
            "trigger_type": "lam_tarif",
            "article_lam": candidate.article_lam.text,
            "target_letter": candidate.target.base_letter,
            "target_folded_letter": candidate.target.folded_base,
            "target_has_shadda": candidate.target.has_shadda,
            "article_lam_has_sukun": candidate.article_lam.has_sukun,
            "contracted_li_l_article": candidate.contracted,
        },
        expected_features=dict(spec.expected_features),
        confidence=confidence,
        detector_id=DETECTOR_ID,
    )


def _preceding_vowel(
    stream: CanonicalTokenStream,
    predecessor: Optional[CanonicalGrapheme],
) -> tuple[Optional[str], str, Optional[CanonicalGrapheme]]:
    if predecessor is None:
        return "fatha", "ibtida_default_tafkhim", None

    if _has(predecessor, MarkTag.KASRA) or _has(predecessor, MarkTag.KASRATAN):
        return "kasra", "explicit_preceding_vowel", predecessor
    if _has(predecessor, MarkTag.FATHA) or _has(predecessor, MarkTag.FATHATAN):
        return "fatha", "explicit_preceding_vowel", predecessor
    if _has(predecessor, MarkTag.DAMMA) or _has(predecessor, MarkTag.DAMMATAN):
        return "damma", "explicit_preceding_vowel", predecessor

    # Resolve a long-vowel carrier from the vowel on its preceding consonant.
    before = stream.previous_letter(predecessor.index) if predecessor.index > 0 else None
    if before is not None and before.word_index == predecessor.word_index:
        if predecessor.folded_base == "ي" and _has(before, MarkTag.KASRA):
            return "kasra", "long_vowel_carrier", before
        if predecessor.folded_base == "و" and _has(before, MarkTag.DAMMA):
            return "damma", "long_vowel_carrier", before
        if predecessor.folded_base == "ا" and _has(before, MarkTag.FATHA):
            return "fatha", "long_vowel_carrier", before

    return None, "unresolved_preceding_vowel", predecessor


def _make_jalalah_annotation(
    stream: CanonicalTokenStream,
    candidate: _JalalahCandidate,
    rule_code: str,
    *,
    vowel: str,
    vowel_source: str,
    vowel_grapheme: Optional[CanonicalGrapheme],
) -> TajwidAnnotationV3:
    spec = get_rule_spec(rule_code)
    trigger = make_text_span(
        stream,
        candidate.principal_lam.index,
        candidate.principal_lam.index + 1,
    )
    context = make_text_span(
        stream,
        candidate.core_start.index,
        candidate.principal_lam.index + 1,
    )
    return TajwidAnnotationV3(
        rule_code=rule_code,
        trigger_span=trigger,
        context_span=context,
        display_span=trigger,
        word_index=candidate.word.index,
        next_word_index=None,
        applies_when=AppliesWhen.CONTEXTUAL,
        evidence={
            "trigger_type": "lam_lafz_al_jalalah",
            "preceding_vowel": vowel,
            "vowel_resolution": vowel_source,
            "vowel_grapheme": vowel_grapheme.text if vowel_grapheme else None,
            "principal_lam_has_shadda": candidate.principal_lam.has_shadda,
        },
        expected_features=dict(spec.expected_features),
        confidence=1.0,
        detector_id=DETECTOR_ID,
    )


class AlifLamDetector:
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

        for candidate in _iter_article_candidates(stream):
            rule_code = _classify_article(candidate)
            if rule_code is None:
                continue
            confidence = 1.0
            if rule_code == "alif_lam_qamariyyah" and not candidate.article_lam.has_sukun:
                confidence = 0.95
                issues.append(
                    DetectorIssue(
                        issue_type="qamariyyah_lam_without_explicit_sukun",
                        severity="warning",
                        grapheme_index=candidate.article_lam.index,
                        word_index=candidate.word.index,
                        detail="Target qamariyyah terdeteksi tetapi lam ta'rif tidak memiliki sukun eksplisit.",
                        evidence={"word": candidate.word.text, "target": candidate.target.text},
                    )
                )
            if rule_code == "alif_lam_shamsiyyah" and not candidate.target.has_shadda:
                confidence = 0.95
                issues.append(
                    DetectorIssue(
                        issue_type="shamsiyyah_target_without_shadda",
                        severity="warning",
                        grapheme_index=candidate.target.index,
                        word_index=candidate.word.index,
                        detail="Huruf syamsiyyah terdeteksi tanpa shadda eksplisit pada teks.",
                        evidence={"word": candidate.word.text, "target": candidate.target.text},
                    )
                )
            annotations.append(
                _make_article_annotation(
                    stream,
                    candidate,
                    rule_code,
                    confidence=confidence,
                )
            )

        for word in stream.words:
            candidate = _jalalah_candidate(stream, word)
            if candidate is None:
                continue
            vowel, vowel_source, vowel_grapheme = _preceding_vowel(
                stream,
                candidate.predecessor,
            )
            if vowel is None:
                issues.append(
                    DetectorIssue(
                        issue_type="lam_jalalah_preceding_vowel_unresolved",
                        severity="warning",
                        grapheme_index=candidate.principal_lam.index,
                        word_index=word.index,
                        detail="Vokal terucap sebelum lafz Allah tidak dapat ditentukan secara aman.",
                        evidence={
                            "word": word.text,
                            "predecessor": candidate.predecessor.text if candidate.predecessor else None,
                            "reading_mode": reading_mode.value,
                        },
                    )
                )
                continue
            rule_code = (
                "lam_jalalah_tarqiq" if vowel == "kasra" else "lam_jalalah_tafkhim"
            )
            annotations.append(
                _make_jalalah_annotation(
                    stream,
                    candidate,
                    rule_code,
                    vowel=vowel,
                    vowel_source=vowel_source,
                    vowel_grapheme=vowel_grapheme,
                )
            )

        return DetectorOutput(
            annotations=tuple(annotations),
            issues=tuple(issues),
        )
