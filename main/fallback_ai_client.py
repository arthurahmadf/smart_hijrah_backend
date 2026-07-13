# main/fallback_ai_client.py

from __future__ import annotations

import logging
import re
import time
from typing import Any

from django.conf import settings
from groq import Groq

from main.models_ai import ChatMessage
from main.utils_rag.prompts import get_metode7_system_prompt


logger = logging.getLogger(__name__)


# ============================================================
# GROQ CLIENT
# ============================================================

groq_client = Groq(
    api_key=settings.GROQ_API_KEY,
)


# ============================================================
# MODEL CHAIN
# ============================================================

MODEL_CHAIN = [
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
]

REASONING_MODELS_PREFIXES = (
    "openai/gpt-oss",
    "qwen/",
)


# ============================================================
# WARIS CONFIGURATION
# ============================================================

WARIS_KEYWORDS = [
    "waris",
    "warisan",
    "faraid",
    "ahli waris",
    "pusaka",
    "harta peninggalan",
    "tirkah",
    "mirats",
    "bagian warisan",
    "pembagian harta warisan",
    "hitung waris",
    "perhitungan waris",
    "hukum waris",
    "cara waris",
    "pembagian harta",
]

KALKULATOR_WARIS_MESSAGE = (
    "\n\n💡 *Tips:* Untuk perhitungan waris yang lebih akurat "
    "dan sesuai dengan kasus spesifik Anda, saya sarankan "
    "menggunakan fitur **Kalkulator Waris** yang tersedia di "
    "aplikasi Smart Hijrah. Fitur ini akan membantu Anda "
    "menghitung pembagian waris secara otomatis dan presisi."
)


# ============================================================
# BASE INSTRUCTION
# ============================================================

BASE_INSTRUCTION = (
    "Anda adalah 'Smart Hijrah Assistant', seorang pakar dan "
    "agamawan Islam yang berwawasan luas, santun, bijaksana, "
    "dan objektif. Jawablah setiap pertanyaan pengguna dalam "
    "Bahasa Indonesia yang formal, sejuk, dan penuh hormat.\n\n"

    "Aturan Penulisan Jawaban:\n"

    "1. Sertakan referensi dalil yang sahih jika tersedia dalam "
    "evidence, yaitu nama surah dan nomor ayat untuk Al-Qur'an, "
    "atau perawi dan identitas hadis jika tersedia.\n"

    "2. Jangan mengarang ayat, nomor hadis, sanad, derajat hadis, "
    "nama ulama, fatwa, atau rujukan yang tidak tersedia dalam "
    "evidence.\n"

    "3. Jika terdapat perbedaan pandangan fiqih yang relevan dan "
    "didukung evidence, jelaskan secara netral dan proporsional.\n"

    "4. Hindari menghakimi pengguna atau mengeluarkan fatwa mutlak "
    "tanpa dasar dan rincian kasus yang memadai.\n"

    "5. Jika pertanyaan tidak terkait Islam, ibadah, akhlak, "
    "spiritualitas, atau kehidupan Muslim, jawab secara singkat "
    "bahwa Smart Hijrah berfokus pada pertanyaan seputar Islam.\n"

    "6. Jika pengguna bertanya tentang hukum Islam atas objek "
    "modern seperti teknologi, hiburan, finansial, atau media, "
    "tetap analisis dari sisi hukum dan adab Islam. Jangan langsung "
    "menganggapnya di luar domain.\n"

    "7. Jangan membantu mencari, merekomendasikan, atau "
    "mendeskripsikan konten maksiat atau eksplisit."
)


# ============================================================
# HISTORY HELPERS
# ============================================================

def _normalize_history_text(
    text: str | None,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        (text or "").strip().lower(),
    )


def _get_previous_user_questions(
    conversation_id: int | None,
    current_db_message: str | None = None,
    limit: int = 3,
) -> list[ChatMessage]:
    """
    Mengambil pesan user sebelumnya secara kronologis.

    current_db_message dikecualikan karena chat_views biasanya
    sudah menyimpan pesan user terbaru sebelum Smart AI pipeline
    dijalankan.
    """
    if not conversation_id:
        return []

    questions_desc = list(
        ChatMessage.objects.filter(
            conversation_id=conversation_id,
            role="user",
        )
        .order_by("-created_at", "-id")[: limit + 1]
    )

    if current_db_message and questions_desc:
        current_normalized = _normalize_history_text(
            current_db_message
        )

        newest_question = questions_desc[0]

        if (
            _normalize_history_text(newest_question.text)
            == current_normalized
        ):
            questions_desc = questions_desc[1:]

    questions_desc = questions_desc[:limit]

    return list(
        reversed(questions_desc)
    )


def _get_assistant_answer_after_question(
    conversation_id: int,
    question: ChatMessage,
) -> ChatMessage | None:
    """
    Mengambil jawaban assistant pertama setelah pesan user.

    Urutan menggunakan created_at dan id agar deterministik.
    """
    return (
        ChatMessage.objects.filter(
            conversation_id=conversation_id,
            role="assistant",
            created_at__gte=question.created_at,
        )
        .order_by("created_at", "id")
        .first()
    )


def _build_conversation_history(
    conversation_id: int | None,
    current_db_message: str | None = None,
    limit: int = 3,
    max_answer_chars: int = 1000,
) -> str:
    """
    Membentuk selective history untuk prompt.

    Fungsi ini hanya dipanggil jika
    include_conversation_history=True.
    """
    if not conversation_id:
        return ""

    previous_questions = _get_previous_user_questions(
        conversation_id=conversation_id,
        current_db_message=current_db_message,
        limit=limit,
    )

    if not previous_questions:
        return ""

    history_parts: list[str] = []

    for index, question in enumerate(
        previous_questions,
        start=1,
    ):
        history_parts.append(
            f"{index}. User: {question.text}"
        )

        assistant_answer = (
            _get_assistant_answer_after_question(
                conversation_id=conversation_id,
                question=question,
            )
        )

        if assistant_answer:
            answer_text = (
                assistant_answer.text or ""
            ).strip()

            if len(answer_text) > max_answer_chars:
                answer_text = (
                    answer_text[:max_answer_chars]
                    + "... (dipotong)"
                )

            history_parts.append(
                f"   Assistant: {answer_text}"
            )

    return "\n".join(history_parts)


# ============================================================
# GROQ FALLBACK
# ============================================================

def chat_with_fallback(
    messages: list[dict[str, str]],
    max_retries: int = 2,
) -> tuple[str, str]:
    """
    Kirim chat dengan fallback otomatis ke model Groq lain.

    Returns:
        tuple(response_text, model_name)
    """
    last_error: Exception | None = None

    for model_name in MODEL_CHAIN:
        for attempt in range(max_retries):
            try:
                logger.info(
                    "[FALLBACK] Trying model=%s attempt=%s/%s",
                    model_name,
                    attempt + 1,
                    max_retries,
                )

                extra_kwargs: dict[str, Any] = {}

                if model_name.startswith(
                    REASONING_MODELS_PREFIXES
                ):
                    extra_kwargs[
                        "reasoning_effort"
                    ] = "low"

                    extra_kwargs[
                        "include_reasoning"
                    ] = False

                response = (
                    groq_client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=0.4,
                        max_tokens=2048,
                        **extra_kwargs,
                    )
                )

                choice = response.choices[0]
                result = choice.message.content
                finish_reason = getattr(
                    choice,
                    "finish_reason",
                    None,
                )

                logger.info(
                    (
                        "[FALLBACK] model=%s "
                        "finish_reason=%s "
                        "response_length=%s"
                    ),
                    model_name,
                    finish_reason,
                    len(result) if result else 0,
                )

                if not result or not result.strip():
                    last_error = RuntimeError(
                        (
                            f"Empty content from "
                            f"{model_name}; "
                            f"finish_reason="
                            f"{finish_reason}"
                        )
                    )

                    time.sleep(1)
                    continue

                return result.strip(), model_name

            except Exception as exc:
                last_error = exc
                error_message = str(exc)

                logger.warning(
                    "[FALLBACK] model=%s error=%s",
                    model_name,
                    error_message[:300],
                )

                if (
                    "429" in error_message
                    or "rate" in error_message.lower()
                ):
                    time.sleep(5)

                elif "413" in error_message:
                    break

                else:
                    time.sleep(1)

        logger.warning(
            "[FALLBACK] Model failed, switching: %s",
            model_name,
        )

    safe_error = (
        str(last_error)[:150]
        if last_error
        else "unknown error"
    )

    return (
        (
            "Maaf, layanan AI sedang sibuk. "
            "Silakan coba kembali beberapa saat lagi. "
            f"Kode teknis: {safe_error}"
        ),
        "none",
    )


# ============================================================
# DOMAIN HELPERS
# ============================================================

def is_waris_question(
    text: str,
) -> bool:
    normalized_text = (
        text or ""
    ).lower()

    return any(
        keyword in normalized_text
        for keyword in WARIS_KEYWORDS
    )


# ============================================================
# MAIN SMART AI WRAPPER
# ============================================================

def get_islamic_response(
    user_message: str,
    conversation_id: int | None = None,
    is_first_message: bool = True,
    use_metode7: bool = False,
    current_db_message: str | None = None,
    include_conversation_history: bool = True,
    answer_strategy_prompt: str | None = None,
    evidence_context: str | None = None,
) -> str:
    """
    Wrapper utama Smart AI.

    Parameters:
        user_message:
            Query efektif yang dikirim ke LLM.

        conversation_id:
            ID conversation aktif.

        is_first_message:
            Menentukan apakah opening boleh digunakan.

        use_metode7:
            Mengaktifkan system prompt Metode 7.

        current_db_message:
            Pesan user terbaru yang sudah tersimpan di DB dan perlu
            dikecualikan dari history.

        include_conversation_history:
            Selective history dari Conversation Context Engine.
            False berarti history tidak boleh dikirim sama sekali.

        answer_strategy_prompt:
            Instruksi dari Phase 5A Answer Strategy Prompt Builder.

        evidence_context:
            Evidence terstruktur yang boleh dipakai LLM jika tersedia.
    """
    logger.info(
        (
            "[FALLBACK] New request "
            "conversation_id=%s "
            "is_first=%s "
            "include_history=%s "
            "prompt_length=%s"
        ),
        conversation_id,
        is_first_message,
        include_conversation_history,
        len(user_message or ""),
    )

    total_start_time = time.time()

    try:
        conversation_history = ""

        if (
            conversation_id
            and not is_first_message
            and include_conversation_history
        ):
            conversation_history = (
                _build_conversation_history(
                    conversation_id=conversation_id,
                    current_db_message=current_db_message,
                    limit=3,
                    max_answer_chars=1000,
                )
            )

        # Urutan prompt:
        # 1. Base/system instruction
        # 2. Answer strategy
        # 3. Evidence
        # 4. Selective history
        # 5. Conversation behavior
        # 6. Current user query
        prompt_parts: list[str] = []

        if use_metode7:
            prompt_parts.append(
                get_metode7_system_prompt()
            )
        else:
            prompt_parts.append(
                BASE_INSTRUCTION
            )

        if (
            answer_strategy_prompt
            and answer_strategy_prompt.strip()
        ):
            prompt_parts.extend([
                "",
                answer_strategy_prompt.strip(),
            ])

        if evidence_context and evidence_context.strip():
            prompt_parts.extend([
                "",
                "EVIDENCE YANG BOLEH DIGUNAKAN:",
                evidence_context.strip(),
            ])

        if conversation_history:
            prompt_parts.extend([
                "",
                "RIWAYAT PERCAKAPAN YANG RELEVAN:",
                conversation_history,
                (
                    "Gunakan riwayat hanya untuk memahami konteks. "
                    "Jangan mengulang seluruh jawaban sebelumnya."
                ),
            ])

        if is_first_message:
            prompt_parts.extend([
                "",
                (
                    "Untuk pesan pertama, awali dengan salam "
                    "Assalamu’alaikum secara singkat apabila "
                    "answer strategy mengizinkan opening. "
                    "Jangan membuat perkenalan panjang."
                ),
            ])

        else:
            prompt_parts.extend([
                "",
                (
                    "Ini adalah kelanjutan percakapan. "
                    "Jangan mengulang salam atau memperkenalkan diri. "
                    "Langsung jawab pertanyaan."
                ),
            ])

        prompt_parts.extend([
            "",
            "PERTANYAAN PENGGUNA SAAT INI:",
            user_message,
        ])

        final_prompt = "\n".join(
            part
            for part in prompt_parts
            if part is not None
        ).strip()

        messages = [
            {
                "role": "system",
                "content": (
                    "Anda adalah Smart Hijrah Assistant, "
                    "asisten Islam yang santun, objektif, "
                    "berhati-hati, dan berbasis evidence."
                ),
            },
            {
                "role": "user",
                "content": final_prompt,
            },
        ]

        logger.info(
            (
                "[FALLBACK] Calling Groq "
                "messages=%s final_prompt_length=%s"
            ),
            len(messages),
            len(final_prompt),
        )

        api_start_time = time.time()

        response_text, used_model = (
            chat_with_fallback(messages)
        )

        logger.info(
            "[FALLBACK] Used model=%s",
            used_model,
        )

        if (
            used_model != "none"
            and is_waris_question(user_message)
        ):
            response_text += (
                KALKULATOR_WARIS_MESSAGE
            )

        logger.info(
            (
                "[FALLBACK] API duration=%.4fs "
                "total_duration=%.4fs"
            ),
            time.time() - api_start_time,
            time.time() - total_start_time,
        )

        return response_text

    except Exception as exc:
        logger.exception(
            "[FALLBACK] get_islamic_response failed"
        )

        return (
            "Maaf, saya mengalami masalah teknis saat "
            "menyusun jawaban. Silakan coba kembali."
        )