# main/utils_rag/evidence_composer.py

from __future__ import annotations

import re
from typing import Any

from main.utils_rag.answer_strategy import (
    AnswerStrategy,
    STRATEGY_FATWA,
    STRATEGY_FIQH,
    STRATEGY_GENERAL_ISLAMIC,
    STRATEGY_SPIRITUAL,
    select_answer_strategy,
)

from main.utils_rag.followup_compression import (
    ASPECT_DALIL,
    ASPECT_DOA,
    ASPECT_EXAMPLE,
    ASPECT_HADITH,
    ASPECT_MUI,
    ASPECT_PRACTICAL,
    ASPECT_QURAN,
    ASPECT_REASON,
    ASPECT_SUMMARY,
    FollowUpPolicy,
    build_followup_policy,
    compress_followup_draft,
    select_display_sources,
)


# ============================================================
# STRATEGY HELPERS
# ============================================================

def _resolve_strategy(
    intent_result: Any,
    conversation_context: dict[str, Any] | None,
    verified_sources: list[dict[str, Any]] | None,
    strategy: AnswerStrategy | None = None,
) -> AnswerStrategy:
    """
    Gunakan strategy dari integration.py jika tersedia.

    Fallback ke select_answer_strategy() dipertahankan agar composer
    tetap aman ketika dipanggil langsung dari management command,
    unit test, atau modul lama.
    """
    if strategy is not None:
        return strategy

    return select_answer_strategy(
        intent=intent_result,
        conversation_context=conversation_context,
        verified_sources=verified_sources,
    )


def _strategy_opening(
    strategy: AnswerStrategy,
    is_first_message: bool,
) -> str:
    """
    Salam hanya boleh muncul pada pesan pertama dan ketika strategy
    memang mengizinkan opening.

    Pesan lanjutan, refinement, maupun NEW_TOPIC di conversation yang
    sama tidak mengulang salam.
    """
    if not strategy.show_opening:
        return ""

    if not is_first_message:
        return ""

    return "Assalamu’alaikum warahmatullahi wabarakatuh."


def _join_non_empty_blocks(
    blocks: list[str | None],
) -> str:
    return "\n\n".join(
        block.strip()
        for block in blocks
        if block and block.strip()
    )


def _build_context_reference(
    strategy: AnswerStrategy,
    conversation_context: dict[str, Any] | None,
    followup_policy: FollowUpPolicy | None = None,
) -> str:
    """
    Tampilkan referensi konteks secara singkat tanpa membocorkan
    resolved_query atau metadata internal.
    """
    if followup_policy and followup_policy.enabled:
        if not followup_policy.include_context_reference:
            return ""

    if not strategy.reference_previous_context_briefly:
        return ""

    if not conversation_context:
        return ""

    previous_topic = (
        conversation_context.get("previous_topic")
        or {}
    )

    summary = str(
        previous_topic.get("summary")
        or previous_topic.get("label")
        or ""
    ).strip()

    if not summary:
        return ""

    return (
        "Terkait pembahasan sebelumnya tentang "
        f"**{summary}**:"
    )


# ============================================================
# DRAFT SANITIZER
# ============================================================

def _sanitize_draft_text(
    draft_text: str | None,
) -> str:
    """
    Bersihkan pembukaan yang mungkin masih dibuat oleh LLM.

    Composer memiliki opening sendiri. Tanpa sanitizer, pesan pertama
    dapat memperoleh salam atau perkenalan dua kali.
    """
    text = (draft_text or "").strip()

    if not text:
        return ""

    text = re.sub(
        (
            r"^\s*assalamu[’']?alaikum"
            r"(?:\s+warahmatullahi\s+wabarakatuh)?"
            r"[\s,.:;!\-–—]*"
        ),
        "",
        text,
        flags=re.IGNORECASE,
    ).lstrip()

    lines = text.splitlines()

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

        is_identity_line = (
            "smart hijrah assistant" in normalized
            and (
                normalized.startswith("saya ")
                or normalized.startswith("saya adalah")
                or normalized.startswith("perkenalkan")
            )
        )

        if is_separator or is_identity_line:
            lines.pop(0)

            while lines and not lines[0].strip():
                lines.pop(0)

            continue

        break

    return "\n".join(lines).strip()


# ============================================================
# SOURCE HELPERS
# ============================================================

def _is_source_verified(
    source: dict[str, Any],
) -> bool:
    return bool(
        source.get(
            "is_verified",
            source.get("verified", False),
        )
    )


def _normalize_source_type(
    source: dict[str, Any],
) -> str:
    source_type = str(
        source.get("type", "")
    ).strip().upper()

    if source_type == "HADITH":
        return "HADIS"

    return source_type


def _limit_sources_by_strategy(
    sources: list[dict[str, Any]] | None,
    strategy: AnswerStrategy,
) -> list[dict[str, Any]]:
    """
    Batasi evidence berdasarkan strategy.

    Aturan visibility tetap diterapkan pada sumber eksternal meskipun
    sumber tersebut belum terverifikasi. Ini mencegah external source
    masuk melalui jalur UNVERIFIED ketika strategy melarang external.
    """
    result: list[dict[str, Any]] = []

    counters = {
        "QURAN": 0,
        "HADIS": 0,
        "EKSTERNAL": 0,
        "UNVERIFIED": 0,
    }

    type_limits = {
        "QURAN": max(0, strategy.max_quran),
        "HADIS": max(0, strategy.max_hadith),
        "EKSTERNAL": max(0, strategy.max_external),
    }

    for source in sources or []:
        source_type = _normalize_source_type(source)
        is_verified = _is_source_verified(source)

        if source_type == "EKSTERNAL":
            if not strategy.show_external_sources:
                continue

        if source_type in type_limits:
            if (
                counters[source_type]
                >= type_limits[source_type]
            ):
                continue
        else:
            # Jenis sumber tak dikenal diperlakukan secara hati-hati
            # sebagai sumber belum terverifikasi.
            is_verified = False

        if not is_verified:
            if not strategy.show_unverified_sources:
                continue

            if (
                counters["UNVERIFIED"]
                >= max(0, strategy.max_unverified)
            ):
                continue

        result.append(source)

        if source_type in counters:
            counters[source_type] += 1

        if not is_verified:
            counters["UNVERIFIED"] += 1

    return result


def _split_sources(
    sources: list[dict[str, Any]] | None,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    quran_sources: list[dict[str, Any]] = []
    hadith_sources: list[dict[str, Any]] = []
    external_sources: list[dict[str, Any]] = []
    unverified_sources: list[dict[str, Any]] = []

    for source in sources or []:
        source_type = _normalize_source_type(source)
        is_verified = _is_source_verified(source)

        if not is_verified:
            unverified_sources.append(source)
            continue

        if source_type == "QURAN":
            quran_sources.append(source)
        elif source_type == "HADIS":
            hadith_sources.append(source)
        elif source_type == "EKSTERNAL":
            external_sources.append(source)
        else:
            # Jangan hilangkan source tak dikenal secara diam-diam.
            unverified_sources.append(source)

    return (
        quran_sources,
        hadith_sources,
        external_sources,
        unverified_sources,
    )


def _format_references(
    quran_sources: list[dict[str, Any]],
    hadith_sources: list[dict[str, Any]],
    external_sources: list[dict[str, Any]],
    unverified_sources: list[dict[str, Any]],
) -> str:
    lines: list[str] = []

    if quran_sources:
        lines.append(
            "**Dalil Al-Qur’an yang terverifikasi:**"
        )

        for index, source in enumerate(
            quran_sources,
            start=1,
        ):
            reference = source.get(
                "reference",
                "Rujukan Al-Qur’an",
            )
            translation = source.get(
                "translation_text",
                "",
            )

            lines.append(
                f"{index}. **{reference}**"
            )

            if translation:
                lines.append(
                    f"   > {translation}"
                )

    if hadith_sources:
        if lines:
            lines.append("")

        lines.append(
            "**Hadis yang ditemukan dalam database:**"
        )

        for index, source in enumerate(
            hadith_sources,
            start=1,
        ):
            reference = source.get(
                "reference",
                "Rujukan Hadis",
            )
            translation = source.get(
                "translation_text",
                "",
            )

            lines.append(
                f"{index}. **{reference}**"
            )

            if translation:
                lines.append(
                    f"   > {translation}"
                )

    if external_sources:
        if lines:
            lines.append("")

        lines.append(
            "**Rujukan eksternal/kajian ulama:**"
        )

        for index, source in enumerate(
            external_sources,
            start=1,
        ):
            reference = source.get(
                "reference",
                "Rujukan eksternal",
            )

            lines.append(
                f"{index}. {reference}"
            )

    if unverified_sources:
        if lines:
            lines.append("")

        lines.append(
            "**Rujukan yang belum terverifikasi:**"
        )

        for index, source in enumerate(
            unverified_sources,
            start=1,
        ):
            reference = source.get(
                "reference",
                "Rujukan tidak ditemukan",
            )

            lines.append(
                f"{index}. {reference}"
            )

    if not lines:
        return (
            "**Rujukan:**\n"
            "⚠️ Belum ada rujukan spesifik yang berhasil "
            "diverifikasi dari database Smart Hijrah."
        )

    return "\n".join(lines)


# ============================================================
# STRATEGY-AWARE ANSWER BODY
# ============================================================

def _build_strategy_answer_body(
    user_query: str,
    intent_result: Any,
    strategy: AnswerStrategy,
    draft_text: str,
    has_verified_sources: bool,
    followup_policy: FollowUpPolicy,
    previous_assistant_text: str | None = None,
) -> str:
    """
    Strategy menentukan bentuk jawaban, sedangkan draft LLM tetap
    menjadi substansi utama selama tersedia.

    Untuk follow-up, draft dikompres secara deterministik agar tidak
    mengulang jawaban sebelumnya.
    """
    del intent_result  # Dipertahankan untuk kompatibilitas signature.

    clean_draft = _sanitize_draft_text(
        draft_text
    )

    if followup_policy.enabled:
        clean_draft = compress_followup_draft(
            draft_text=clean_draft,
            previous_assistant_text=(
                previous_assistant_text
            ),
            policy=followup_policy,
        )

    if followup_policy.enabled:
        aspect = followup_policy.requested_aspect

        if aspect == ASPECT_MUI:
            if clean_draft:
                return _join_non_empty_blocks([
                    "**Menurut sumber yang tersedia:**",
                    clean_draft,
                ])

            return (
                "**Menurut sumber yang tersedia:**\n"
                "Dokumen resmi MUI yang relevan belum tersedia "
                "dalam knowledge base Smart Hijrah, sehingga saya "
                "tidak akan mengatasnamakan MUI secara pasti."
            )

        if aspect in {
            ASPECT_HADITH,
            ASPECT_QURAN,
            ASPECT_DALIL,
        }:
            if clean_draft:
                return _join_non_empty_blocks([
                    "**Rujukan yang diminta:**",
                    clean_draft,
                ])

            return (
                "**Rujukan yang diminta:**\n"
                "Berikut dalil yang berhasil ditemukan dan "
                "diverifikasi untuk topik tersebut."
            )

        if aspect == ASPECT_REASON:
            if clean_draft:
                return _join_non_empty_blocks([
                    "**Alasannya:**",
                    clean_draft,
                ])

        elif aspect == ASPECT_EXAMPLE:
            if clean_draft:
                return _join_non_empty_blocks([
                    "**Contohnya:**",
                    clean_draft,
                ])

        elif aspect == ASPECT_SUMMARY:
            if clean_draft:
                return clean_draft

        elif aspect in {
            ASPECT_PRACTICAL,
            ASPECT_DOA,
        }:
            if clean_draft:
                return clean_draft

        elif clean_draft:
            return clean_draft

    if strategy.name == STRATEGY_SPIRITUAL:
        if clean_draft:
            return _join_non_empty_blocks([
                "**Untukmu saat ini:**",
                clean_draft,
            ])

        return (
            "**Untukmu saat ini:**\n"
            "Pintu kembali kepada Allah tetap terbuka. "
            "Mulailah kembali dari langkah kecil dan jangan "
            "menyerah."
        )

    if strategy.name == STRATEGY_FATWA:
        if clean_draft:
            return _join_non_empty_blocks([
                "**Jawaban ringkas:**",
                clean_draft,
            ])

        return (
            "**Jawaban ringkas:**\n"
            "Hukum kasus ini bergantung pada rincian akad, "
            "mekanisme, tujuan, dan unsur yang menyertainya."
        )

    if strategy.name == STRATEGY_FIQH:
        if clean_draft:
            return _join_non_empty_blocks([
                "**Jawaban ringkas:**",
                clean_draft,
            ])

        return (
            "**Jawaban ringkas:**\n"
            "Masalah ini perlu dinilai berdasarkan rincian "
            "perbuatan, syarat, dampak, dan prinsip umum "
            "syariat."
        )

    if strategy.name == STRATEGY_GENERAL_ISLAMIC:
        if clean_draft:
            return _join_non_empty_blocks([
                "**Jawaban ringkas:**",
                clean_draft,
            ])

        return (
            "**Jawaban ringkas:**\n"
            "Berikut penjelasan berdasarkan prinsip Islam dan "
            "rujukan yang berhasil diverifikasi."
        )

    if clean_draft:
        return clean_draft

    if has_verified_sources:
        return (
            "**Jawaban ringkas:**\n"
            "Berikut jawaban berdasarkan rujukan yang berhasil "
            "diverifikasi."
        )

    return (
        "**Jawaban ringkas:**\n"
        "Belum ada rujukan spesifik yang berhasil diverifikasi. "
        "Jawaban perlu dipahami sebagai penjelasan umum."
    )


# ============================================================
# OPTIONAL SECTIONS
# ============================================================

def _build_practical_block(
    strategy: AnswerStrategy,
    followup_policy: FollowUpPolicy,
) -> str:
    if followup_policy.enabled:
        if not followup_policy.include_practical_steps:
            return ""
    elif not strategy.show_practical_steps:
        return ""

    if strategy.name == STRATEGY_SPIRITUAL:
        return (
            "**Langkah praktis:**\n"
            "1. Mulai kembali dari satu amal kecil yang konsisten.\n"
            "2. Jauhi pemicu yang membuatmu kembali jatuh.\n"
            "3. Jaga shalat dan perbanyak istighfar.\n"
            "4. Cari lingkungan atau teman yang membantu kebaikan."
        )

    if strategy.name == STRATEGY_FATWA:
        return (
            "**Hal yang perlu diperiksa:**\n"
            "1. Akad atau bentuk transaksinya.\n"
            "2. Adanya bunga, denda, gharar, atau spekulasi.\n"
            "3. Objek usaha atau penggunaan dananya.\n"
            "4. Transparansi biaya, risiko, dan kewajiban."
        )

    return ""


def _build_doa_block(
    user_query: str,
    strategy: AnswerStrategy,
    followup_policy: FollowUpPolicy,
) -> str:
    del user_query  # Fokus doa sudah ditentukan oleh policy.

    if followup_policy.enabled:
        if not followup_policy.include_doa:
            return ""
    elif (
        not strategy.show_doa
        or strategy.name != STRATEGY_SPIRITUAL
    ):
        return ""

    if strategy.name != STRATEGY_SPIRITUAL:
        return ""

    return (
        "**Doa singkat:**\n"
        "Ya Allah, teguhkan hatiku di atas ketaatan, ampuni "
        "kesalahanku, dan mudahkan aku untuk terus kembali "
        "kepada-Mu."
    )


def _build_caution_block(
    strategy: AnswerStrategy,
    status_global: str,
    limited_sources: list[dict[str, Any]],
    unverified_sources: list[dict[str, Any]],
    followup_policy: FollowUpPolicy,
) -> str:
    if (
        followup_policy.enabled
        and not followup_policy.include_caution
    ):
        return ""

    blocks: list[str] = []

    if strategy.require_fatwa_disclaimer:
        blocks.append(
            "**Catatan fatwa:**\n"
            "Kasus kontemporer sering bergantung pada rincian "
            "akad, syarat, dan praktik sebenarnya. Jawaban ini "
            "merupakan panduan umum, bukan fatwa personal yang "
            "menggantikan pemeriksaan ahli syariah."
        )

    should_show_verification_caution = (
        strategy.show_caution_note
        or status_global != "HIGH_CONFIDENCE"
    )

    if should_show_verification_caution:
        if not limited_sources:
            blocks.append(
                "**Catatan kehati-hatian:**\n"
                "Belum ada rujukan spesifik yang berhasil "
                "diverifikasi. Jawaban ini menggunakan prinsip "
                "umum dan tidak boleh dipahami sebagai penetapan "
                "hukum final."
            )

        elif unverified_sources:
            blocks.append(
                "**Catatan kehati-hatian:**\n"
                "Sebagian rujukan belum berhasil diverifikasi "
                "sepenuhnya."
            )

        elif status_global != "HIGH_CONFIDENCE":
            blocks.append(
                "**Catatan kehati-hatian:**\n"
                "Tingkat verifikasi jawaban ini belum mencapai "
                "keyakinan tinggi sehingga masih perlu dipahami "
                "secara hati-hati."
            )

    return _join_non_empty_blocks(
        blocks
    )


# ============================================================
# EVIDENCE-GROUNDED COMPOSER
# ============================================================

def compose_evidence_grounded_answer(
    user_query,
    intent_result,
    draft_text,
    verified_sources,
    status_global,
    is_first_message=True,
    conversation_context=None,
    strategy=None,
    followup_policy=None,
    previous_assistant_text=None,
):
    """
    Menyusun final answer dari:
    1. strategy,
    2. draft LLM yang sudah dibersihkan,
    3. evidence hasil verifier,
    4. conversation context,
    5. natural follow-up policy.
    """
    strategy = _resolve_strategy(
        intent_result=intent_result,
        conversation_context=conversation_context,
        verified_sources=verified_sources,
        strategy=strategy,
    )

    if followup_policy is None:
        followup_policy = build_followup_policy(
            user_message=user_query,
            strategy=strategy,
            conversation_context=conversation_context,
        )

    limited_sources = _limit_sources_by_strategy(
        sources=verified_sources,
        strategy=strategy,
    )

    display_sources = select_display_sources(
        sources=limited_sources,
        policy=followup_policy,
    )

    (
        quran_sources,
        hadith_sources,
        external_sources,
        unverified_display_sources,
    ) = _split_sources(
        display_sources
    )

    (
        _all_quran_sources,
        _all_hadith_sources,
        _all_external_sources,
        all_unverified_sources,
    ) = _split_sources(
        limited_sources
    )

    opening = _strategy_opening(
        strategy=strategy,
        is_first_message=is_first_message,
    )

    context_reference = _build_context_reference(
        strategy=strategy,
        conversation_context=conversation_context,
        followup_policy=followup_policy,
    )

    answer_body = _build_strategy_answer_body(
        user_query=user_query,
        intent_result=intent_result,
        strategy=strategy,
        draft_text=draft_text,
        has_verified_sources=bool(
            limited_sources
        ),
        followup_policy=followup_policy,
        previous_assistant_text=(
            previous_assistant_text
        ),
    )

    references_block = ""

    if (
        not followup_policy.enabled
        or followup_policy.include_references
    ):
        references_block = _format_references(
            quran_sources=quran_sources,
            hadith_sources=hadith_sources,
            external_sources=external_sources,
            unverified_sources=(
                unverified_display_sources
            ),
        )

    practical_block = _build_practical_block(
        strategy=strategy,
        followup_policy=followup_policy,
    )

    doa_block = _build_doa_block(
        user_query=user_query,
        strategy=strategy,
        followup_policy=followup_policy,
    )

    caution_block = _build_caution_block(
        strategy=strategy,
        status_global=status_global,
        limited_sources=limited_sources,
        unverified_sources=(
            all_unverified_sources
        ),
        followup_policy=followup_policy,
    )

    reply = _join_non_empty_blocks([
        opening,
        context_reference,
        answer_body,
        references_block,
        practical_block,
        doa_block,
        caution_block,
    ])

    narrative_text = _join_non_empty_blocks([
        context_reference,
        answer_body,
        practical_block,
        doa_block,
        caution_block,
    ])

    return {
        "reply": reply,
        "narrative_text": narrative_text,
        "verification_status": status_global,
        "verified_sources": limited_sources,
        "displayed_sources": display_sources,
        "composer": "NATURAL_FOLLOWUP_COMPOSER_V1",
        "strategy": strategy.to_dict(),
        "followup_policy": followup_policy.to_dict(),
    }


# ============================================================
# THEMATIC RETRIEVAL COMPOSER
# ============================================================

def compose_thematic_retrieval_answer(
    user_query,
    intent_result,
    retrieval_result,
    is_first_message=True,
    conversation_context=None,
    strategy=None,
    followup_policy=None,
    previous_assistant_text=None,
):
    del previous_assistant_text  # Thematic route tidak memakai draft LLM.

    verified_sources = retrieval_result.get(
        "verified_sources",
        [],
    )

    strategy = _resolve_strategy(
        intent_result=intent_result,
        conversation_context=conversation_context,
        verified_sources=verified_sources,
        strategy=strategy,
    )

    if followup_policy is None:
        followup_policy = build_followup_policy(
            user_message=user_query,
            strategy=strategy,
            conversation_context=conversation_context,
        )

    limited_sources = _limit_sources_by_strategy(
        sources=verified_sources,
        strategy=strategy,
    )

    display_sources = select_display_sources(
        sources=limited_sources,
        policy=followup_policy,
    )

    (
        quran_sources,
        hadith_sources,
        external_sources,
        unverified_sources,
    ) = _split_sources(
        display_sources
    )

    opening = _strategy_opening(
        strategy=strategy,
        is_first_message=is_first_message,
    )

    context_reference = _build_context_reference(
        strategy=strategy,
        conversation_context=conversation_context,
        followup_policy=followup_policy,
    )

    theme = (
        retrieval_result.get("theme")
        or user_query
    )

    preference = retrieval_result.get(
        "source_preference",
        "both",
    )

    if followup_policy.enabled:
        if followup_policy.requested_aspect == ASPECT_QURAN:
            preference = "quran"
        elif followup_policy.requested_aspect == ASPECT_HADITH:
            preference = "hadis"

    has_verified_primary_source = any(
        _is_source_verified(source)
        and _normalize_source_type(source)
        in {"QURAN", "HADIS"}
        for source in display_sources
    )

    if has_verified_primary_source:
        if preference == "quran":
            introduction = (
                "Berikut ayat Al-Qur’an yang paling relevan "
                f"dengan tema **{theme}**."
            )

        elif preference == "hadis":
            introduction = (
                "Berikut hadis yang paling relevan "
                f"dengan tema **{theme}**."
            )

        else:
            introduction = (
                "Berikut dalil Al-Qur’an dan hadis yang paling "
                f"relevan dengan tema **{theme}**."
            )

        references_block = _format_references(
            quran_sources=quran_sources,
            hadith_sources=hadith_sources,
            external_sources=external_sources,
            unverified_sources=unverified_sources,
        )

        coverage_note = ""

        if not followup_policy.enabled:
            coverage_note = (
                "**Catatan:**\n"
                "Hasil ini merupakan rujukan paling relevan yang "
                "ditemukan, bukan daftar lengkap seluruh dalil "
                "mengenai tema tersebut."
            )

        heading = (
            "**Rujukan yang diminta:**"
            if followup_policy.enabled
            else "**Hasil pencarian dalil tematik:**"
        )

        reply = _join_non_empty_blocks([
            opening,
            context_reference,
            heading,
            introduction,
            references_block,
            coverage_note,
        ])

        narrative_text = _join_non_empty_blocks([
            context_reference,
            introduction,
            coverage_note,
        ])

        return {
            "reply": reply,
            "narrative_text": narrative_text,
            "verification_status": "HIGH_CONFIDENCE",
            "verified_sources": limited_sources,
            "displayed_sources": display_sources,
            "composer": "THEMATIC_NATURAL_FOLLOWUP_V1",
            "strategy": strategy.to_dict(),
            "followup_policy": followup_policy.to_dict(),
        }

    if followup_policy.enabled:
        if followup_policy.requested_aspect == ASPECT_HADITH:
            source_label = "hadis"
        elif followup_policy.requested_aspect == ASPECT_QURAN:
            source_label = "ayat Al-Qur’an"
        else:
            source_label = "ayat atau hadis"

        no_result_message = (
            f"Saya belum menemukan {source_label} dengan "
            f"relevansi yang cukup kuat untuk tema **{theme}**."
        )
    else:
        no_result_message = (
            "Saya belum menemukan ayat atau hadis dengan "
            f"relevansi yang cukup kuat untuk tema **{theme}**."
        )

    suggestion = (
        "Saya tidak akan memaksakan rujukan yang kurang sesuai. "
        "Coba gunakan kata kunci yang lebih spesifik."
    )

    reply = _join_non_empty_blocks([
        opening,
        context_reference,
        (
            "**Rujukan yang diminta:**"
            if followup_policy.enabled
            else "**Hasil pencarian dalil tematik:**"
        ),
        no_result_message,
        suggestion,
    ])

    narrative_text = _join_non_empty_blocks([
        context_reference,
        no_result_message,
        suggestion,
    ])

    return {
        "reply": reply,
        "narrative_text": narrative_text,
        "verification_status": "NEEDS_REVIEW",
        "verified_sources": limited_sources,
        "displayed_sources": [],
        "composer": "THEMATIC_NATURAL_FOLLOWUP_V1",
        "strategy": strategy.to_dict(),
        "followup_policy": followup_policy.to_dict(),
    }