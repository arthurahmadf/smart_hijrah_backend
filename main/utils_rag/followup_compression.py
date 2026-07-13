# main/utils_rag/followup_compression.py

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Any

from main.utils_rag.answer_strategy import (
    AnswerStrategy,
    STRATEGY_FATWA,
)


ASPECT_GENERAL = "GENERAL"
ASPECT_HADITH = "HADITH"
ASPECT_QURAN = "QURAN"
ASPECT_DALIL = "DALIL"
ASPECT_REASON = "REASON"
ASPECT_EXAMPLE = "EXAMPLE"
ASPECT_PRACTICAL = "PRACTICAL"
ASPECT_DOA = "DOA"
ASPECT_MUI = "MUI"
ASPECT_SUMMARY = "SUMMARY"
ASPECT_RULING = "RULING"
ASPECT_CONTINUATION = "CONTINUATION"

FOLLOW_UP_RELATIONS = {
    "FOLLOW_UP",
    "TOPIC_REFINEMENT",
    "AMBIGUOUS",
}

INFORMAL_REPLACEMENTS = {
    "klo": "kalau",
    "kalo": "kalau",
    "klw": "kalau",
    "mnrt": "menurut",
    "gmn": "bagaimana",
    "gimana": "bagaimana",
    "knp": "kenapa",
    "hadisny": "hadisnya",
    "haditsny": "hadisnya",
    "ayatny": "ayatnya",
    "dalilny": "dalilnya",
    "doany": "doanya",
}


@dataclass(frozen=True)
class FollowUpPolicy:
    """
    Aturan presentation untuk jawaban lanjutan.

    Policy ini tidak menentukan hukum atau substansi agama. Ia hanya
    mengendalikan fokus, panjang, section, dan pengulangan jawaban.
    """

    enabled: bool
    relation: str
    requested_aspect: str

    max_paragraphs: int
    max_list_items: int
    max_chars: int

    include_references: bool
    include_practical_steps: bool
    include_doa: bool
    include_caution: bool
    include_context_reference: bool
    preserve_headings: bool

    reasoning_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["reasoning_codes"] = list(
            self.reasoning_codes
        )
        return result


def normalize_followup_text(
    text: str | None,
) -> str:
    normalized = (text or "").lower().strip()
    normalized = normalized.replace("’", "'")
    normalized = re.sub(
        r"[^\w\s'-]",
        " ",
        normalized,
    )
    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()

    tokens = normalized.split()

    return " ".join(
        INFORMAL_REPLACEMENTS.get(token, token)
        for token in tokens
    )


def detect_requested_aspect(
    user_message: str | None,
) -> str:
    text = normalize_followup_text(
        user_message
    )

    if not text:
        return ASPECT_GENERAL

    if re.search(
        r"\b(mui|dsn mui|dsn-mui|fatwa mui)\b",
        text,
    ):
        return ASPECT_MUI

    if re.search(
        (
            r"\b(?:hadis|hadits)(?:nya)?\b"
            r"|\briwayat(?:nya)?\b"
            r"|\bsabda\s+nabi\b"
        ),
        text,
    ):
        return ASPECT_HADITH

    if re.search(
        (
            r"\bayat(?:nya)?\b"
            r"|\bquran\b"
            r"|\bal\s+quran\b"
            r"|\balquran\b"
            r"|\bsurah\b"
            r"|\bsurat\b"
        ),
        text,
    ):
        return ASPECT_QURAN

    if re.search(
        r"\b(dalil|rujukan|sumber)\b",
        text,
    ):
        return ASPECT_DALIL

    if re.search(
        r"\b(doa|doanya|doakan)\b",
        text,
    ):
        return ASPECT_DOA

    if re.search(
        r"\b(kenapa|mengapa|alasannya|alasan|sebab|dasarnya)\b",
        text,
    ):
        return ASPECT_REASON

    if re.search(
        r"\b(contoh|contohnya|misalnya|ilustrasi)\b",
        text,
    ):
        return ASPECT_EXAMPLE

    if re.search(
        r"\b(caranya|cara|langkah|tips|praktiknya|praktis)\b",
        text,
    ):
        return ASPECT_PRACTICAL

    if re.search(
        (
            r"\bringkas(?:nya)?\b"
            r"|\bsingkat(?:nya)?\b"
            r"|\bkesimpulan(?:nya)?\b"
            r"|\bintinya\b"
            r"|\bsimpulkan\b"
        ),
        text,
    ):
        return ASPECT_SUMMARY

    if re.search(
        r"\b(hukum|hukumnya|boleh|haram|halal|wajib|sunnah|makruh)\b",
        text,
    ):
        return ASPECT_RULING

    if text in {
        "terus",
        "lanjut",
        "lalu",
        "bagaimana",
        "terus bagaimana",
        "lanjutkan",
    }:
        return ASPECT_CONTINUATION

    return ASPECT_GENERAL


def _conversation_relation(
    conversation_context: dict[str, Any] | None,
) -> str:
    if not conversation_context:
        return "NEW_TOPIC"

    return str(
        conversation_context.get(
            "conversation_relation",
            "NEW_TOPIC",
        )
        or "NEW_TOPIC"
    ).upper()


def build_followup_policy(
    user_message: str,
    strategy: AnswerStrategy,
    conversation_context: dict[str, Any] | None,
) -> FollowUpPolicy:
    relation = _conversation_relation(
        conversation_context
    )
    requested_aspect = detect_requested_aspect(
        user_message
    )

    enabled = bool(
        strategy.is_follow_up
        or relation in FOLLOW_UP_RELATIONS
    )

    if not enabled:
        return FollowUpPolicy(
            enabled=False,
            relation=relation,
            requested_aspect=requested_aspect,
            max_paragraphs=max(
                1,
                strategy.max_summary_paragraphs,
            ),
            max_list_items=max(
                1,
                strategy.max_practical_steps,
            ),
            max_chars=5000,
            # Policy follow-up sedang nonaktif. Flag section harus
            # netral agar tidak dianggap sebagai instruksi kompresi.
            include_references=True,
            include_practical_steps=False,
            include_doa=False,
            include_caution=False,
            include_context_reference=False,
            preserve_headings=True,
            reasoning_codes=(
                "FOLLOWUP_COMPRESSION_DISABLED",
            ),
        )

    reasoning_codes = [
        "FOLLOWUP_COMPRESSION_ENABLED",
        f"ASPECT_{requested_aspect}",
    ]

    is_refinement = (
        relation == "TOPIC_REFINEMENT"
    )

    max_paragraphs = 3 if is_refinement else 2
    max_list_items = 3
    max_chars = 1800 if is_refinement else 1300

    include_references = False
    include_practical_steps = False
    include_doa = False
    include_caution = False
    include_context_reference = is_refinement
    preserve_headings = False

    if requested_aspect in {
        ASPECT_HADITH,
        ASPECT_QURAN,
        ASPECT_DALIL,
        ASPECT_MUI,
    }:
        include_references = True
        max_paragraphs = 1
        max_chars = 1100
        reasoning_codes.append(
            "SOURCE_FOCUSED_FOLLOWUP"
        )

    elif requested_aspect == ASPECT_REASON:
        max_paragraphs = 2
        max_chars = 1200
        reasoning_codes.append(
            "REASON_ONLY_FOLLOWUP"
        )

    elif requested_aspect == ASPECT_EXAMPLE:
        max_paragraphs = 2
        max_list_items = 2
        max_chars = 1100
        reasoning_codes.append(
            "EXAMPLE_ONLY_FOLLOWUP"
        )

    elif requested_aspect == ASPECT_PRACTICAL:
        include_practical_steps = True
        max_paragraphs = 1
        max_list_items = 4
        max_chars = 1200
        reasoning_codes.append(
            "PRACTICAL_ONLY_FOLLOWUP"
        )

    elif requested_aspect == ASPECT_DOA:
        include_doa = True
        max_paragraphs = 1
        max_chars = 900
        reasoning_codes.append(
            "DOA_ONLY_FOLLOWUP"
        )

    elif requested_aspect == ASPECT_SUMMARY:
        max_paragraphs = 1
        max_list_items = 2
        max_chars = 700
        reasoning_codes.append(
            "SUMMARY_ONLY_FOLLOWUP"
        )

    elif requested_aspect == ASPECT_RULING:
        include_references = is_refinement
        include_caution = (
            strategy.name == STRATEGY_FATWA
            and is_refinement
        )
        max_paragraphs = 2
        max_chars = 1300
        reasoning_codes.append(
            "RULING_FOLLOWUP"
        )

    elif requested_aspect == ASPECT_CONTINUATION:
        max_paragraphs = 2
        max_chars = 1100
        reasoning_codes.append(
            "CONTINUATION_FOLLOWUP"
        )

    else:
        include_references = is_refinement
        max_paragraphs = 2
        max_chars = 1300
        reasoning_codes.append(
            "GENERAL_FOLLOWUP"
        )

    return FollowUpPolicy(
        enabled=True,
        relation=relation,
        requested_aspect=requested_aspect,
        max_paragraphs=max_paragraphs,
        max_list_items=max_list_items,
        max_chars=max_chars,
        include_references=include_references,
        include_practical_steps=(
            include_practical_steps
        ),
        include_doa=include_doa,
        include_caution=include_caution,
        include_context_reference=(
            include_context_reference
        ),
        preserve_headings=preserve_headings,
        reasoning_codes=tuple(
            reasoning_codes
        ),
    )


def build_followup_prompt_instruction(
    policy: FollowUpPolicy,
) -> str:
    if not policy.enabled:
        return ""

    lines = [
        "ATURAN NATURAL FOLLOW-UP:",
        "- Jawab langsung aspek baru yang diminta.",
        "- Jangan mengulang salam atau perkenalan.",
        "- Jangan mengulang seluruh jawaban sebelumnya.",
        (
            f"- Fokus jawaban: "
            f"{policy.requested_aspect}."
        ),
        (
            f"- Maksimal sekitar "
            f"{policy.max_paragraphs} paragraf."
        ),
        (
            f"- Maksimal sekitar "
            f"{policy.max_list_items} item daftar."
        ),
    ]

    if not policy.include_references:
        lines.append(
            "- Jangan mengulang daftar rujukan lama kecuali "
            "diperlukan untuk menjawab aspek baru."
        )

    if policy.requested_aspect == ASPECT_REASON:
        lines.append(
            "- Fokus pada alasan atau prinsip yang mendasari "
            "jawaban sebelumnya."
        )

    elif policy.requested_aspect == ASPECT_EXAMPLE:
        lines.append(
            "- Berikan contoh yang konkret dan singkat."
        )

    elif policy.requested_aspect == ASPECT_SUMMARY:
        lines.append(
            "- Berikan inti jawaban dalam bentuk sangat ringkas."
        )

    elif policy.requested_aspect in {
        ASPECT_HADITH,
        ASPECT_QURAN,
        ASPECT_DALIL,
        ASPECT_MUI,
    }:
        lines.append(
            "- Fokus hanya pada sumber yang diminta pengguna."
        )

    return "\n".join(
        lines
    )


def select_display_sources(
    sources: list[dict[str, Any]] | None,
    policy: FollowUpPolicy,
) -> list[dict[str, Any]]:
    """
    Pilih source yang dirender di teks jawaban.

    verified_sources utama tetap dapat dipertahankan untuk final
    checker. Fungsi ini hanya mengontrol source yang ditampilkan.
    """
    if not policy.enabled:
        return list(
            sources or []
        )

    if not policy.include_references:
        return []

    result: list[dict[str, Any]] = []

    for source in sources or []:
        source_type = str(
            source.get("type", "")
        ).upper()

        if source_type == "HADITH":
            source_type = "HADIS"

        if (
            policy.requested_aspect == ASPECT_HADITH
            and source_type != "HADIS"
        ):
            continue

        if (
            policy.requested_aspect == ASPECT_QURAN
            and source_type != "QURAN"
        ):
            continue

        if (
            policy.requested_aspect == ASPECT_DALIL
            and source_type
            not in {"QURAN", "HADIS"}
        ):
            continue

        if (
            policy.requested_aspect == ASPECT_MUI
            and source_type != "EKSTERNAL"
        ):
            continue

        result.append(
            source
        )

    return result


def _normalize_sentence(
    sentence: str,
) -> str:
    normalized = sentence.lower()
    normalized = re.sub(
        r"[*_`>#]",
        " ",
        normalized,
    )
    normalized = re.sub(
        r"[^\w\s]",
        " ",
        normalized,
    )
    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )
    return normalized.strip()


def _sentence_is_duplicate(
    sentence: str,
    previous_sentences: list[str],
) -> bool:
    normalized = _normalize_sentence(
        sentence
    )

    tokens = set(
        normalized.split()
    )

    if len(tokens) < 6:
        return False

    for previous in previous_sentences:
        previous_normalized = _normalize_sentence(
            previous
        )

        if normalized == previous_normalized:
            return True

        ratio = SequenceMatcher(
            None,
            normalized,
            previous_normalized,
        ).ratio()

        if ratio >= 0.90:
            return True

        previous_tokens = set(
            previous_normalized.split()
        )

        if not previous_tokens:
            continue

        union = tokens | previous_tokens

        if not union:
            continue

        jaccard = len(
            tokens & previous_tokens
        ) / len(union)

        if jaccard >= 0.88:
            return True

    return False


def _split_sentences(
    text: str,
) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+",
            text,
        )
        if sentence.strip()
    ]


def _strip_opening_and_identity(
    text: str,
) -> str:
    cleaned = (text or "").strip()

    cleaned = re.sub(
        (
            r"^\s*assalamu[’']?alaikum"
            r"(?:\s+warahmatullahi\s+wabarakatuh)?"
            r"[\s,.:;!\-–—]*"
        ),
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).lstrip()

    lines = cleaned.splitlines()

    while lines and not lines[0].strip():
        lines.pop(0)

    while lines:
        first_line = lines[0].strip()
        normalized = first_line.lower()

        is_separator = normalized in {
            "---",
            "***",
            "___",
        }

        is_identity = (
            "smart hijrah assistant" in normalized
            and (
                normalized.startswith("saya")
                or normalized.startswith(
                    "perkenalkan"
                )
            )
        )

        if is_separator or is_identity:
            lines.pop(0)

            while lines and not lines[0].strip():
                lines.pop(0)

            continue

        break

    return "\n".join(
        lines
    ).strip()


def _strip_leading_heading(
    text: str,
) -> str:
    cleaned = text.strip()

    patterns = [
        r"^\s*#{1,6}\s+.+?\n+",
        r"^\s*\*\*(?:jawaban ringkas|jawaban lanjutan|kesimpulan|penjelasan lanjutan|rujukan yang diminta|untukmu saat ini|menurut sumber yang tersedia)\s*:\*\*\s*",
        r"^\s*(?:jawaban ringkas|jawaban lanjutan|kesimpulan|penjelasan lanjutan)\s*:\s*",
    ]

    changed = True

    while changed:
        changed = False

        for pattern in patterns:
            updated = re.sub(
                pattern,
                "",
                cleaned,
                count=1,
                flags=re.IGNORECASE,
            ).lstrip()

            if updated != cleaned:
                cleaned = updated
                changed = True

    return cleaned


def _limit_list_items(
    block: str,
    max_items: int,
) -> str:
    lines = block.splitlines()
    output: list[str] = []
    list_count = 0

    for line in lines:
        stripped = line.strip()

        is_list_item = bool(
            re.match(
                r"^(?:[-*+]|\d+[.)])\s+",
                stripped,
            )
        )

        if is_list_item:
            list_count += 1

            if list_count > max_items:
                continue

        output.append(
            line
        )

    return "\n".join(
        output
    ).strip()


def _truncate_at_boundary(
    text: str,
    max_chars: int,
) -> str:
    if len(text) <= max_chars:
        return text

    candidate = text[:max_chars].rstrip()

    boundary = max(
        candidate.rfind(". "),
        candidate.rfind("! "),
        candidate.rfind("? "),
        candidate.rfind("\n"),
    )

    if boundary >= int(
        max_chars * 0.60
    ):
        candidate = candidate[
            : boundary + 1
        ].rstrip()

    return candidate.rstrip(
        " ,;:-"
    ) + "…"


def compress_followup_draft(
    draft_text: str | None,
    previous_assistant_text: str | None,
    policy: FollowUpPolicy,
) -> str:
    """
    Bersihkan dan kompres draft follow-up secara deterministik.

    Tidak menggunakan LLM tambahan sehingga tidak menambah latency
    atau biaya.
    """
    text = _strip_opening_and_identity(
        draft_text or ""
    )

    if not text:
        return ""

    if not policy.enabled:
        return text

    if not policy.preserve_headings:
        text = _strip_leading_heading(
            text
        )

    previous_sentences = _split_sentences(
        previous_assistant_text or ""
    )

    blocks = [
        block.strip()
        for block in re.split(
            r"\n\s*\n",
            text,
        )
        if block.strip()
    ]

    compressed_blocks: list[str] = []

    for block in blocks:
        block = _limit_list_items(
            block=block,
            max_items=policy.max_list_items,
        )

        if not block:
            continue

        is_list_block = any(
            re.match(
                r"^(?:[-*+]|\d+[.)])\s+",
                line.strip(),
            )
            for line in block.splitlines()
        )

        if is_list_block:
            compressed_blocks.append(
                block
            )
        else:
            unique_sentences = [
                sentence
                for sentence in _split_sentences(
                    block
                )
                if not _sentence_is_duplicate(
                    sentence,
                    previous_sentences,
                )
            ]

            unique_block = " ".join(
                unique_sentences
            ).strip()

            if unique_block:
                compressed_blocks.append(
                    unique_block
                )

        if (
            len(compressed_blocks)
            >= policy.max_paragraphs
        ):
            break

    if not compressed_blocks:
        # Hindari jawaban kosong ketika seluruh draft sangat mirip
        # dengan jawaban sebelumnya. Tetap berikan blok pertama yang
        # sudah dibersihkan sebagai fallback.
        first_block = blocks[0] if blocks else text

        compressed_blocks = [
            _limit_list_items(
                block=first_block,
                max_items=policy.max_list_items,
            )
        ]

    result = "\n\n".join(
        compressed_blocks[
            : policy.max_paragraphs
        ]
    ).strip()

    return _truncate_at_boundary(
        text=result,
        max_chars=policy.max_chars,
    )