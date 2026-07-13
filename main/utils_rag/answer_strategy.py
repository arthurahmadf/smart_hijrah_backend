# main/utils_rag/answer_strategy.py

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


# ============================================================
# STRATEGY NAMES
# ============================================================

STRATEGY_DIRECT_LOOKUP = "DIRECT_LOOKUP"
STRATEGY_THEMATIC_DALIL = "THEMATIC_DALIL"
STRATEGY_FIQH = "FIQH"
STRATEGY_FATWA = "FATWA"
STRATEGY_SPIRITUAL = "SPIRITUAL"
STRATEGY_GENERAL_ISLAMIC = "GENERAL_ISLAMIC"
STRATEGY_OUT_OF_DOMAIN = "OUT_OF_DOMAIN"


# ============================================================
# ANSWER DEPTH
# ============================================================

DEPTH_CONCISE = "CONCISE"
DEPTH_STANDARD = "STANDARD"
DEPTH_DETAILED = "DETAILED"


# ============================================================
# CONVERSATION MODES
# ============================================================

CONVERSATION_NEW_TOPIC = "NEW_TOPIC"
CONVERSATION_FOLLOW_UP = "FOLLOW_UP"
CONVERSATION_TOPIC_REFINEMENT = "TOPIC_REFINEMENT"
CONVERSATION_AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class AnswerSection:
    """
    Satu bagian dalam struktur jawaban.

    key:
        Identifier internal yang stabil.

    title:
        Judul default yang dapat dipakai composer.

    required:
        Apakah section wajib muncul.

    max_items:
        Maksimal jumlah evidence/item yang ditampilkan.

    condition:
        Kondisi opsional yang nanti dapat dibaca composer.
    """

    key: str
    title: str
    required: bool = False
    max_items: int | None = None
    condition: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnswerStrategy:
    """
    Blueprint jawaban yang dipilih berdasarkan intent dan context.

    Strategy tidak menyusun teks akhir. Strategy hanya memberi aturan
    kepada composer mengenai struktur, panjang, tone, dan evidence.
    """

    name: str
    intent: str
    depth: str

    sections: list[AnswerSection] = field(default_factory=list)

    # Presentation behavior
    show_opening: bool = True
    show_identity_intro: bool = False
    show_summary_first: bool = True
    show_conclusion: bool = True
    show_caution_note: bool = False
    show_practical_steps: bool = False
    show_empathy: bool = False
    show_doa: bool = False
    show_external_sources: bool = True
    show_unverified_sources: bool = True

    # Evidence limits
    max_quran: int = 2
    max_hadith: int = 2
    max_external: int = 2
    max_unverified: int = 2

    # Conversation behavior
    is_follow_up: bool = False
    avoid_repeating_previous_answer: bool = False
    answer_only_requested_aspect: bool = False
    reference_previous_context_briefly: bool = False

    # Safety and epistemic behavior
    require_verified_evidence: bool = False
    allow_general_principles_without_specific_evidence: bool = True
    require_fatwa_disclaimer: bool = False
    require_scholarly_difference_note: bool = False
    prohibit_hadith_grading_claim: bool = True

    # Length guidance
    max_summary_paragraphs: int = 2
    max_practical_steps: int = 5
    max_total_sections: int = 8

    # Debug / observability
    reasoning_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["sections"] = [
            section.to_dict()
            for section in self.sections
        ]
        return result


def _normalize_intent(intent: Any) -> str:
    """
    Mendukung:
    - Enum dengan .value
    - string
    - dictionary intent dari router
    """
    if isinstance(intent, dict):
        intent = intent.get("intent")

    if hasattr(intent, "value"):
        intent = intent.value

    return str(intent or "").strip().upper()


def _get_context_relation(
    conversation_context: dict[str, Any] | None,
) -> str:
    if not conversation_context:
        return CONVERSATION_NEW_TOPIC

    relation = conversation_context.get(
        "conversation_relation",
        CONVERSATION_NEW_TOPIC,
    )

    return str(relation or "").strip().upper()


def _count_verified_sources(
    verified_sources: list[dict[str, Any]] | None,
) -> dict[str, int]:
    counts = {
        "quran": 0,
        "hadith": 0,
        "external": 0,
        "unverified": 0,
        "total_verified": 0,
    }

    for source in verified_sources or []:
        source_type = str(
            source.get("type", "")
        ).upper()

        is_verified = bool(
            source.get(
                "is_verified",
                source.get("verified", False),
            )
        )

        if source_type == "QURAN":
            counts["quran"] += 1
        elif source_type in {"HADIS", "HADITH"}:
            counts["hadith"] += 1
        elif source_type == "EKSTERNAL":
            counts["external"] += 1

        if is_verified:
            counts["total_verified"] += 1
        else:
            counts["unverified"] += 1

    return counts


def _direct_lookup_strategy(
    intent: str,
) -> AnswerStrategy:
    return AnswerStrategy(
        name=STRATEGY_DIRECT_LOOKUP,
        intent=intent,
        depth=DEPTH_CONCISE,
        sections=[
            AnswerSection(
                key="reference",
                title="Rujukan",
                required=True,
                max_items=1,
            ),
            AnswerSection(
                key="arabic_text",
                title="Teks Arab",
                required=False,
                max_items=1,
            ),
            AnswerSection(
                key="translation",
                title="Terjemahan",
                required=True,
                max_items=1,
            ),
            AnswerSection(
                key="verification",
                title="Status Verifikasi",
                required=True,
                max_items=1,
            ),
        ],
        show_opening=True,
        show_identity_intro=False,
        show_summary_first=False,
        show_conclusion=False,
        show_caution_note=False,
        show_practical_steps=False,
        show_empathy=False,
        show_doa=False,
        show_external_sources=False,
        show_unverified_sources=True,
        max_quran=1,
        max_hadith=1,
        max_external=0,
        max_unverified=1,
        require_verified_evidence=True,
        allow_general_principles_without_specific_evidence=False,
        max_summary_paragraphs=0,
        max_total_sections=4,
        reasoning_codes=[
            "DIRECT_REFERENCE_REQUEST",
            "NO_LLM_NARRATIVE_REQUIRED",
        ],
    )


def _thematic_strategy(
    intent: str,
) -> AnswerStrategy:
    return AnswerStrategy(
        name=STRATEGY_THEMATIC_DALIL,
        intent=intent,
        depth=DEPTH_STANDARD,
        sections=[
            AnswerSection(
                key="theme_summary",
                title="Ringkasan Tema",
                required=True,
            ),
            AnswerSection(
                key="quran",
                title="Dalil Al-Qur’an",
                max_items=3,
                condition="WHEN_QURAN_AVAILABLE",
            ),
            AnswerSection(
                key="hadith",
                title="Hadis",
                max_items=3,
                condition="WHEN_HADITH_AVAILABLE",
            ),
            AnswerSection(
                key="evidence_relationship",
                title="Keterkaitan Dalil",
                required=False,
            ),
            AnswerSection(
                key="coverage_note",
                title="Catatan",
                required=True,
            ),
        ],
        show_opening=True,
        show_identity_intro=False,
        show_summary_first=True,
        show_conclusion=False,
        show_caution_note=False,
        show_practical_steps=False,
        show_external_sources=False,
        show_unverified_sources=False,
        max_quran=3,
        max_hadith=3,
        max_external=0,
        max_unverified=0,
        require_verified_evidence=True,
        allow_general_principles_without_specific_evidence=False,
        max_summary_paragraphs=1,
        max_total_sections=5,
        reasoning_codes=[
            "RETRIEVAL_FIRST",
            "THEMATIC_EVIDENCE_ONLY",
        ],
    )


def _fiqh_strategy(
    intent: str,
) -> AnswerStrategy:
    return AnswerStrategy(
        name=STRATEGY_FIQH,
        intent=intent,
        depth=DEPTH_STANDARD,
        sections=[
            AnswerSection(
                key="legal_summary",
                title="Jawaban Ringkas",
                required=True,
            ),
            AnswerSection(
                key="conditions",
                title="Syarat dan Rincian Hukum",
                required=False,
            ),
            AnswerSection(
                key="quran",
                title="Dalil Al-Qur’an",
                max_items=2,
                condition="WHEN_QURAN_AVAILABLE",
            ),
            AnswerSection(
                key="hadith",
                title="Hadis",
                max_items=2,
                condition="WHEN_HADITH_AVAILABLE",
            ),
            AnswerSection(
                key="general_principles",
                title="Prinsip Umum Syariat",
                required=False,
            ),
            AnswerSection(
                key="scholarly_difference",
                title="Perbedaan Pendapat",
                required=False,
                condition="WHEN_DIFFERENCE_EXISTS",
            ),
            AnswerSection(
                key="conclusion",
                title="Kesimpulan",
                required=True,
            ),
        ],
        show_opening=True,
        show_identity_intro=False,
        show_summary_first=True,
        show_conclusion=True,
        show_caution_note=True,
        show_practical_steps=False,
        show_external_sources=True,
        show_unverified_sources=True,
        max_quran=2,
        max_hadith=2,
        max_external=2,
        max_unverified=1,
        require_verified_evidence=False,
        allow_general_principles_without_specific_evidence=True,
        require_scholarly_difference_note=False,
        max_summary_paragraphs=2,
        max_total_sections=7,
        reasoning_codes=[
            "FIQH_LEGAL_ANALYSIS",
            "SUMMARY_BEFORE_EVIDENCE",
        ],
    )


def _fatwa_strategy(
    intent: str,
) -> AnswerStrategy:
    return AnswerStrategy(
        name=STRATEGY_FATWA,
        intent=intent,
        depth=DEPTH_DETAILED,
        sections=[
            AnswerSection(
                key="case_definition",
                title="Gambaran Masalah",
                required=True,
            ),
            AnswerSection(
                key="legal_summary",
                title="Jawaban Ringkas",
                required=True,
            ),
            AnswerSection(
                key="quran",
                title="Dalil Umum Al-Qur’an",
                max_items=2,
                condition="WHEN_QURAN_AVAILABLE",
            ),
            AnswerSection(
                key="hadith",
                title="Hadis dan Prinsip Umum",
                max_items=2,
                condition="WHEN_HADITH_AVAILABLE",
            ),
            AnswerSection(
                key="legal_reasoning",
                title="Analisis Fiqih",
                required=True,
            ),
            AnswerSection(
                key="external_fatwa",
                title="Fatwa atau Pendapat Lembaga",
                required=False,
                max_items=3,
                condition="WHEN_EXTERNAL_SOURCE_AVAILABLE",
            ),
            AnswerSection(
                key="practical_checklist",
                title="Hal yang Perlu Diperiksa",
                required=False,
            ),
            AnswerSection(
                key="conclusion",
                title="Kesimpulan",
                required=True,
            ),
        ],
        show_opening=True,
        show_identity_intro=False,
        show_summary_first=True,
        show_conclusion=True,
        show_caution_note=True,
        show_practical_steps=True,
        show_external_sources=True,
        show_unverified_sources=True,
        max_quran=2,
        max_hadith=2,
        max_external=3,
        max_unverified=1,
        require_verified_evidence=False,
        allow_general_principles_without_specific_evidence=True,
        require_fatwa_disclaimer=True,
        require_scholarly_difference_note=True,
        max_summary_paragraphs=2,
        max_practical_steps=5,
        max_total_sections=8,
        reasoning_codes=[
            "CONTEMPORARY_FATWA_CASE",
            "DETAIL_DEPENDENT_LEGAL_RULING",
            "REQUIRE_CONDITIONAL_CONCLUSION",
        ],
    )


def _spiritual_strategy(
    intent: str,
) -> AnswerStrategy:
    return AnswerStrategy(
        name=STRATEGY_SPIRITUAL,
        intent=intent,
        depth=DEPTH_STANDARD,
        sections=[
            AnswerSection(
                key="empathy",
                title="Respons Empatik",
                required=True,
            ),
            AnswerSection(
                key="hope",
                title="Harapan dan Penguatan",
                required=True,
            ),
            AnswerSection(
                key="quran",
                title="Dalil Al-Qur’an",
                max_items=2,
                condition="WHEN_QURAN_AVAILABLE",
            ),
            AnswerSection(
                key="hadith",
                title="Hadis",
                max_items=2,
                condition="WHEN_HADITH_AVAILABLE",
            ),
            AnswerSection(
                key="practical_steps",
                title="Langkah Praktis",
                required=True,
                max_items=5,
            ),
            AnswerSection(
                key="doa",
                title="Doa",
                required=False,
                condition="WHEN_DOA_RELEVANT",
            ),
        ],
        show_opening=True,
        show_identity_intro=False,
        show_summary_first=False,
        show_conclusion=False,
        show_caution_note=False,
        show_practical_steps=True,
        show_empathy=True,
        show_doa=True,
        show_external_sources=False,
        show_unverified_sources=False,
        max_quran=2,
        max_hadith=2,
        max_external=0,
        max_unverified=0,
        require_verified_evidence=False,
        allow_general_principles_without_specific_evidence=True,
        max_summary_paragraphs=2,
        max_practical_steps=5,
        max_total_sections=6,
        reasoning_codes=[
            "SPIRITUAL_SUPPORT",
            "EMPATHY_BEFORE_EVIDENCE",
            "PRACTICAL_SMALL_STEPS",
        ],
    )


def _general_strategy(
    intent: str,
) -> AnswerStrategy:
    return AnswerStrategy(
        name=STRATEGY_GENERAL_ISLAMIC,
        intent=intent,
        depth=DEPTH_STANDARD,
        sections=[
            AnswerSection(
                key="summary",
                title="Jawaban Ringkas",
                required=True,
            ),
            AnswerSection(
                key="explanation",
                title="Penjelasan",
                required=True,
            ),
            AnswerSection(
                key="quran",
                title="Dalil Al-Qur’an",
                max_items=2,
                condition="WHEN_QURAN_AVAILABLE",
            ),
            AnswerSection(
                key="hadith",
                title="Hadis",
                max_items=2,
                condition="WHEN_HADITH_AVAILABLE",
            ),
            AnswerSection(
                key="conclusion",
                title="Kesimpulan",
                required=False,
            ),
        ],
        show_opening=True,
        show_identity_intro=False,
        show_summary_first=True,
        show_conclusion=True,
        show_caution_note=False,
        show_practical_steps=False,
        show_external_sources=True,
        show_unverified_sources=True,
        max_quran=2,
        max_hadith=2,
        max_external=2,
        max_unverified=1,
        require_verified_evidence=False,
        allow_general_principles_without_specific_evidence=True,
        max_summary_paragraphs=2,
        max_total_sections=5,
        reasoning_codes=[
            "GENERAL_ISLAMIC_EXPLANATION",
        ],
    )


def _out_of_domain_strategy(
    intent: str,
) -> AnswerStrategy:
    return AnswerStrategy(
        name=STRATEGY_OUT_OF_DOMAIN,
        intent=intent,
        depth=DEPTH_CONCISE,
        sections=[
            AnswerSection(
                key="scope_notice",
                title="Batas Lingkup",
                required=True,
            ),
        ],
        show_opening=False,
        show_identity_intro=False,
        show_summary_first=False,
        show_conclusion=False,
        show_caution_note=False,
        show_practical_steps=False,
        show_empathy=False,
        show_doa=False,
        show_external_sources=False,
        show_unverified_sources=False,
        max_quran=0,
        max_hadith=0,
        max_external=0,
        max_unverified=0,
        require_verified_evidence=False,
        allow_general_principles_without_specific_evidence=False,
        max_summary_paragraphs=1,
        max_total_sections=1,
        reasoning_codes=[
            "OUT_OF_DOMAIN",
        ],
    )


def _apply_conversation_behavior(
    strategy: AnswerStrategy,
    conversation_context: dict[str, Any] | None,
) -> AnswerStrategy:
    """
    Modifikasi strategy berdasarkan hubungan percakapan.

    FOLLOW_UP:
    - Jangan membuka dengan salam/identitas berulang.
    - Fokus hanya pada aspek yang diminta.
    - Hindari mengulang seluruh jawaban sebelumnya.

    TOPIC_REFINEMENT:
    - Tidak perlu opening lengkap.
    - Jawab detail kondisi baru.
    - Boleh merujuk konteks lama secara singkat.

    NEW_TOPIC:
    - Gunakan struktur lengkap sesuai intent.
    """
    relation = _get_context_relation(
        conversation_context
    )

    if relation == CONVERSATION_FOLLOW_UP:
        strategy.is_follow_up = True
        strategy.show_opening = False
        strategy.show_identity_intro = False
        strategy.avoid_repeating_previous_answer = True
        strategy.answer_only_requested_aspect = True
        strategy.reference_previous_context_briefly = True
        strategy.max_summary_paragraphs = 1
        strategy.max_total_sections = min(
            strategy.max_total_sections,
            4,
        )
        strategy.reasoning_codes.append(
            "CONVERSATION_FOLLOW_UP"
        )

    elif relation == CONVERSATION_TOPIC_REFINEMENT:
        strategy.is_follow_up = True
        strategy.show_opening = False
        strategy.show_identity_intro = False
        strategy.avoid_repeating_previous_answer = True
        strategy.answer_only_requested_aspect = False
        strategy.reference_previous_context_briefly = True
        strategy.max_summary_paragraphs = 1
        strategy.reasoning_codes.append(
            "CONVERSATION_TOPIC_REFINEMENT"
        )

    elif relation == CONVERSATION_AMBIGUOUS:
        strategy.is_follow_up = True
        strategy.show_opening = False
        strategy.avoid_repeating_previous_answer = True
        strategy.reference_previous_context_briefly = True
        strategy.reasoning_codes.append(
            "CONVERSATION_AMBIGUOUS"
        )

    else:
        strategy.reasoning_codes.append(
            "CONVERSATION_NEW_TOPIC"
        )

    return strategy


def _apply_evidence_behavior(
    strategy: AnswerStrategy,
    verified_sources: list[dict[str, Any]] | None,
) -> AnswerStrategy:
    counts = _count_verified_sources(
        verified_sources
    )

    if counts["quran"] == 0:
        strategy.reasoning_codes.append(
            "NO_QURAN_SOURCE"
        )

    if counts["hadith"] == 0:
        strategy.reasoning_codes.append(
            "NO_HADITH_SOURCE"
        )

    if counts["total_verified"] == 0:
        strategy.reasoning_codes.append(
            "NO_VERIFIED_SOURCE"
        )

        if strategy.require_verified_evidence:
            strategy.show_caution_note = True

    if counts["external"] == 0:
        strategy.show_external_sources = False

    if counts["unverified"] == 0:
        strategy.show_unverified_sources = False

    return strategy


def select_answer_strategy(
    intent: Any,
    conversation_context: dict[str, Any] | None = None,
    verified_sources: list[dict[str, Any]] | None = None,
) -> AnswerStrategy:
    """
    Public API Phase 5A.

    Contoh:

        strategy = select_answer_strategy(
            intent=intent_result,
            conversation_context=conversation_context,
            verified_sources=verified_sources,
        )
    """
    normalized_intent = _normalize_intent(intent)

    if normalized_intent in {
        "DIRECT_HADITH_LOOKUP",
        "DIRECT_QURAN_LOOKUP",
    }:
        strategy = _direct_lookup_strategy(
            normalized_intent
        )

    elif normalized_intent == "THEMATIC_DALIL_SEARCH":
        strategy = _thematic_strategy(
            normalized_intent
        )

    elif normalized_intent == "FIQH_QA":
        strategy = _fiqh_strategy(
            normalized_intent
        )

    elif normalized_intent == "FATWA_QA":
        strategy = _fatwa_strategy(
            normalized_intent
        )

    elif normalized_intent == "SPIRITUAL_ADVICE":
        strategy = _spiritual_strategy(
            normalized_intent
        )

    elif normalized_intent == "OUT_OF_DOMAIN":
        strategy = _out_of_domain_strategy(
            normalized_intent
        )

    else:
        strategy = _general_strategy(
            normalized_intent
            or "GENERAL_ISLAMIC_QA"
        )

    strategy = _apply_conversation_behavior(
        strategy=strategy,
        conversation_context=conversation_context,
    )

    strategy = _apply_evidence_behavior(
        strategy=strategy,
        verified_sources=verified_sources,
    )

    return strategy