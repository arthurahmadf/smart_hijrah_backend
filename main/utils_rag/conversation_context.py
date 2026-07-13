# main/utils_rag/conversation_context.py

from __future__ import annotations

from typing import Any

from main.models_ai import ChatMessage
from main.utils_rag.topic_classifier import (
    FOLLOW_UP_DALIL,
    FOLLOW_UP_EXPLANATION,
    FOLLOW_UP_HADITH,
    FOLLOW_UP_MUI,
    FOLLOW_UP_NONE,
    FOLLOW_UP_QURAN,
    FOLLOW_UP_DOA,
    RELATION_AMBIGUOUS,
    RELATION_FOLLOW_UP,
    RELATION_NEW_TOPIC,
    RELATION_TOPIC_REFINEMENT,
    TopicRepresentation,
    build_topic_representation,
    classify_topic_relation,
    detect_explicit_follow_up,
)
from main.utils_rag.topic_llm_classifier import (
    classify_ambiguous_topic_with_llm,
)


def _normalize_comparison(text: str) -> str:
    return " ".join(
        (text or "").strip().lower().split()
    )


def _get_previous_messages(
    conversation_id: int | None,
    current_user_message: str,
    limit: int = 20,
) -> list[ChatMessage]:
    if not conversation_id:
        return []

    messages_desc = list(
        ChatMessage.objects.filter(
            conversation_id=conversation_id,
        )
        .order_by("-created_at", "-id")[:limit]
    )

    current_normalized = _normalize_comparison(
        current_user_message
    )

    if (
        messages_desc
        and messages_desc[0].role == "user"
        and _normalize_comparison(
            messages_desc[0].text
        )
        == current_normalized
    ):
        messages_desc = messages_desc[1:]

    return list(reversed(messages_desc))


def _find_previous_substantive_user_message(
    messages: list[ChatMessage],
) -> ChatMessage | None:
    for message in reversed(messages):
        if message.role != "user":
            continue

        normalized = _normalize_comparison(message.text)

        if len(normalized.split()) < 2:
            continue

        return message

    return None


def _resolve_follow_up_query(
    original_query: str,
    follow_up_type: str,
    active_topic: TopicRepresentation,
) -> str:
    topic = active_topic.summary or active_topic.label

    if follow_up_type == FOLLOW_UP_HADITH:
        return f"Hadis tentang {topic}"

    if follow_up_type == FOLLOW_UP_QURAN:
        return f"Ayat Al-Qur'an tentang {topic}"

    if follow_up_type == FOLLOW_UP_DALIL:
        return (
            f"Dalil Al-Qur'an dan hadis tentang {topic}"
        )

    if follow_up_type == FOLLOW_UP_MUI:
        return (
            f"Apa fatwa atau pandangan MUI tentang "
            f"{topic}?"
        )

    if follow_up_type == FOLLOW_UP_EXPLANATION:
        return (
            f"Jelaskan lebih lanjut tentang {topic}. "
            f"Pertanyaan pengguna: {original_query}"
        )
    if follow_up_type == FOLLOW_UP_DOA:
        return f"Doa yang relevan untuk {topic}"
    return (
        f"Terkait topik {topic}, jawab pertanyaan "
        f"lanjutan berikut: {original_query}"
    )

def _merge_topic_refinement(
    previous_topic: TopicRepresentation,
    refinement_topic: TopicRepresentation,
) -> TopicRepresentation:
    """
    Gabungkan topik utama dengan detail refinement tanpa kehilangan
    inti topik sebelumnya.
    """
    previous_summary = (
        previous_topic.summary
        or previous_topic.label
    ).strip()

    refinement_summary = (
        refinement_topic.summary
        or refinement_topic.label
    ).strip()

    summaries = [previous_summary]

    if (
        refinement_summary
        and refinement_summary.lower()
        not in previous_summary.lower()
    ):
        summaries.append(
            f"detail lanjutan: {refinement_summary}"
        )

    entities = list(
        dict.fromkeys(
            previous_topic.entities
            + refinement_topic.entities
        )
    )[:15]

    return TopicRepresentation(
        # Label utama tidak diganti oleh kalimat refinement.
        label=previous_topic.label,
        summary="; ".join(summaries)[:300],
        entities=entities,
        action=(
            refinement_topic.action
            or previous_topic.action
        ),
        original_text=previous_topic.original_text,
    )

def _find_active_topic_from_history(
    messages: list[ChatMessage],
) -> tuple[TopicRepresentation | None, int | None]:
    """
    Bangun active topic dengan memutar ulang pesan user secara
    kronologis.

    Aturan:
    - NEW_TOPIC mengganti active topic.
    - TOPIC_REFINEMENT memperkaya active topic lama.
    - FOLLOW_UP tidak mengganti active topic.
    - AMBIGUOUS mempertahankan active topic lama.
    """
    user_messages = [
        message
        for message in messages
        if message.role == "user"
    ]

    if not user_messages:
        return None, None

    active_topic: TopicRepresentation | None = None
    topic_source_message_id: int | None = None

    for message in user_messages:
        current_topic = build_topic_representation(
            message.text
        )

        if active_topic is None:
            active_topic = current_topic
            topic_source_message_id = message.id
            continue

        follow_up_type = detect_explicit_follow_up(
            message.text
        )

        # Follow-up eksplisit tidak boleh mengganti atau
        # mengurangi active topic.
        if follow_up_type != FOLLOW_UP_NONE:
            continue

        relation_result = classify_topic_relation(
            previous_topic=active_topic,
            current_message=message.text,
            llm_fallback=classify_ambiguous_topic_with_llm,
        )

        relation = relation_result.relation

        if relation == RELATION_NEW_TOPIC:
            active_topic = current_topic
            topic_source_message_id = message.id
            continue

        if relation == RELATION_TOPIC_REFINEMENT:
            active_topic = _merge_topic_refinement(
                previous_topic=active_topic,
                refinement_topic=current_topic,
            )
            continue

        # FOLLOW_UP atau AMBIGUOUS:
        # pertahankan active topic sebelumnya.
        if relation in {
            RELATION_FOLLOW_UP,
            RELATION_AMBIGUOUS,
        }:
            continue

    return active_topic, topic_source_message_id

def _resolve_refinement_query(
    original_query: str,
    previous_topic: TopicRepresentation,
) -> str:
    return (
        f"Terkait pembahasan sebelumnya tentang "
        f"{previous_topic.summary}, jawab detail lanjutan: "
        f"{original_query}"
    )


def resolve_conversation_context(
    user_message: str,
    conversation_id: int | None = None,
    is_first_message: bool = True,
) -> dict[str, Any]:
    current_topic = build_topic_representation(
        user_message
    )

    base_result = {
        "original_query": user_message,
        "resolved_query": user_message,
        "conversation_relation": RELATION_NEW_TOPIC,
        "is_follow_up": False,
        "topic_changed": False,
        "should_include_history": False,
        "previous_topic": None,
        "active_topic": current_topic.to_dict(),
        "topic_similarity": None,
        "context_confidence": 1.0,
        "follow_up_type": "NONE",
        "used_llm_topic_classifier": False,
        "reasoning_code": "FIRST_MESSAGE",
        "history_message_count": 0,
        "topic_source_message_id": None,
    }

    if is_first_message or not conversation_id:
        return base_result

    messages = _get_previous_messages(
        conversation_id=conversation_id,
        current_user_message=user_message,
    )

    base_result["history_message_count"] = len(
        messages
    )

    previous_topic, topic_source_message_id = (
        _find_active_topic_from_history(messages)
    )

    if previous_topic is None:
        base_result["reasoning_code"] = (
            "NO_PREVIOUS_ACTIVE_TOPIC"
        )
        return base_result

    

    relation_result = classify_topic_relation(
        previous_topic=previous_topic,
        current_message=user_message,
        llm_fallback=classify_ambiguous_topic_with_llm,
    )

    relation = relation_result.relation
    resolved_query = user_message
    active_topic = relation_result.current_topic

    if relation == RELATION_FOLLOW_UP:
        resolved_query = _resolve_follow_up_query(
            original_query=user_message,
            follow_up_type=relation_result.follow_up_type,
            active_topic=previous_topic,
        )

        # Follow-up pendek tetap berada pada topik lama.
        active_topic = previous_topic

    elif relation == RELATION_TOPIC_REFINEMENT:
        resolved_query = _resolve_refinement_query(
            original_query=user_message,
            previous_topic=previous_topic,
        )

        # Gabungkan ringkasan lama dan detail baru.
        active_topic = TopicRepresentation(
            label=current_topic.label,
            summary=(
                f"{previous_topic.summary}; "
                f"detail lanjutan: {current_topic.summary}"
            )[:240],
            entities=list(
                dict.fromkeys(
                    previous_topic.entities
                    + current_topic.entities
                )
            )[:12],
            action=(
                current_topic.action
                or previous_topic.action
            ),
            original_text=user_message,
        )

    should_include_history = relation in {
        RELATION_FOLLOW_UP,
        RELATION_TOPIC_REFINEMENT,
        RELATION_AMBIGUOUS,
    }

    topic_changed = (
        relation == RELATION_NEW_TOPIC
        and previous_topic is not None
    )

    return {
        "original_query": user_message,
        "resolved_query": resolved_query,
        "conversation_relation": relation,
        "is_follow_up": relation
        in {
            RELATION_FOLLOW_UP,
            RELATION_TOPIC_REFINEMENT,
            RELATION_AMBIGUOUS,
        },
        "topic_changed": topic_changed,
        "should_include_history": (
            should_include_history
        ),
        "previous_topic": previous_topic.to_dict(),
        "active_topic": active_topic.to_dict(),
        "topic_similarity": (
            relation_result.similarity
        ),
        "context_confidence": (
            relation_result.confidence
        ),
        "follow_up_type": (
            relation_result.follow_up_type
        ),
        "used_llm_topic_classifier": (
            relation_result.used_llm_fallback
        ),
        "reasoning_code": (
            relation_result.reasoning_code
        ),
        "history_message_count": len(messages),
        "topic_source_message_id": topic_source_message_id,
    }