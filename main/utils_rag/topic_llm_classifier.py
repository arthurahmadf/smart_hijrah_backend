# main/utils_rag/topic_llm_classifier.py

from __future__ import annotations

import json
import os
import re
from typing import Any

from groq import Groq

from main.utils_rag.topic_classifier import (
    RELATION_AMBIGUOUS,
    RELATION_FOLLOW_UP,
    RELATION_NEW_TOPIC,
    RELATION_TOPIC_REFINEMENT,
    TopicRepresentation,
)


ALLOWED_RELATIONS = {
    RELATION_NEW_TOPIC,
    RELATION_FOLLOW_UP,
    RELATION_TOPIC_REFINEMENT,
    RELATION_AMBIGUOUS,
}


TOPIC_CLASSIFIER_MODELS = (
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
)


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = (text or "").strip()

    cleaned = re.sub(
        r"^```(?:json)?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        result = json.loads(cleaned)

        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    match = re.search(
        r"\{.*\}",
        cleaned,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError(
            "LLM topic classifier tidak mengembalikan JSON."
        )

    result = json.loads(match.group(0))

    if not isinstance(result, dict):
        raise ValueError(
            "Hasil topic classifier bukan JSON object."
        )

    return result


def classify_ambiguous_topic_with_llm(
    previous_topic: TopicRepresentation,
    current_topic: TopicRepresentation,
    similarity: float,
) -> dict[str, Any]:
    """
    Hanya klasifikasi hubungan topik.

    Tidak meminta fatwa, jawaban agama, atau chain-of-thought.
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY tidak tersedia untuk "
            "topic classifier."
        )

    client = Groq(api_key=api_key)

    prompt = f"""
        Anda adalah pengklasifikasi hubungan topik dalam percakapan.

        Tugas Anda hanya menentukan hubungan antara pesan pengguna saat ini
        dan topik sebelumnya.

        Pilih tepat satu label berikut:

        1. FOLLOW_UP
        Pesan hanya meminta tambahan langsung dari jawaban sebelumnya,
        seperti dalil, hadis, ayat, alasan, penjelasan ulang, sumber,
        atau pendapat lembaga tertentu.

        FOLLOW_UP tidak menambahkan kasus hukum baru, kondisi baru,
        jumlah baru, pihak baru, atau skenario baru yang perlu dianalisis.

        Contoh:
        - "Ada hadisnya?"
        - "Kenapa?"
        - "Kalau menurut MUI?"
        - "Jelaskan lagi."
        - "Sumbernya apa?"

        2. TOPIC_REFINEMENT
        Pesan masih membahas masalah utama yang sama, tetapi menambahkan
        rincian kasus yang mengubah atau mempersempit analisis.

        Refinement dapat berupa:
        - jumlah
        - kondisi
        - pihak
        - waktu
        - objek
        - pengecualian
        - skenario baru dalam masalah yang sama

        Walaupun pesan bergantung pada konteks sebelumnya, pilih
        TOPIC_REFINEMENT jika ada detail kasus baru yang harus dianalisis.

        Contoh:
        - Topik sebelumnya: pembagian waris anak perempuan
        - Pesan: "Kalau anak perempuannya dua bagaimana?"
        - Hasil: TOPIC_REFINEMENT

        Contoh:
        - Topik sebelumnya: hukum paylater
        - Pesan: "Kalau tidak ada bunga tetapi ada biaya admin?"
        - Hasil: TOPIC_REFINEMENT

        3. NEW_TOPIC
        Pesan membahas masalah utama atau tindakan yang berbeda dari topik
        sebelumnya.

        Kesamaan subjek, orang, atau beberapa kata tidak otomatis berarti
        topiknya sama.

        Contoh:
        - Topik sebelumnya: anak perempuan menerima warisan
        - Pesan: "Hukum anak perempuan mencari penghasilan sendiri"
        - Hasil: NEW_TOPIC

        Contoh:
        - Topik sebelumnya: sedekah
        - Pesan: "Kalau tentang riba ada ayatnya?"
        - Hasil: NEW_TOPIC

        4. AMBIGUOUS
        Informasi tidak cukup untuk menentukan hubungan topiknya.

        Topik sebelumnya:
        - label: {previous_topic.label}
        - summary: {previous_topic.summary}
        - action: {previous_topic.action}
        - entities: {previous_topic.entities}

        Pesan saat ini:
        - original: {current_topic.original_text}
        - label: {current_topic.label}
        - summary: {current_topic.summary}
        - action: {current_topic.action}
        - entities: {current_topic.entities}

        Semantic similarity awal: {similarity:.4f}

        Aturan keputusan:
        - Jangan memilih FOLLOW_UP hanya karena pesan bergantung pada konteks.
        - Jika pesan menambahkan detail kasus baru, pilih TOPIC_REFINEMENT.
        - Jika pesan hanya meminta sumber, alasan, ayat, hadis, penjelasan,
        atau pendapat lembaga, pilih FOLLOW_UP.
        - Kata "kalau" tidak otomatis berarti FOLLOW_UP.
        - Jika pesan dapat dipahami sendiri dan menyebut masalah baru secara
        lengkap, pilih NEW_TOPIC.
        - Jika masalah utamanya tetap sama tetapi kondisi kasus berubah,
        pilih TOPIC_REFINEMENT.
        - Kesamaan entitas tidak cukup untuk menyatakan topik yang sama.
        - Semantic similarity hanya sinyal tambahan, bukan keputusan final.
        - Gunakan AMBIGUOUS hanya jika benar-benar tidak cukup informasi.
        - Jangan menjawab pertanyaan agama pengguna.
        - Jangan memberikan penjelasan di luar JSON.

        Aturan topic_label:
        - FOLLOW_UP: pertahankan topik sebelumnya.
        - TOPIC_REFINEMENT: gabungkan topik lama dengan detail kasus baru.
        - NEW_TOPIC: gunakan label masalah baru.
        - AMBIGUOUS: gunakan label netral dari pesan saat ini.

        Kembalikan tepat satu JSON valid:
        {{
        "relation": "FOLLOW_UP",
        "confidence": 0.90,
        "topic_label": "label singkat topik saat ini"
        }}

        Nilai relation hanya boleh:
        "FOLLOW_UP", "TOPIC_REFINEMENT", "NEW_TOPIC", atau "AMBIGUOUS".

        Nilai confidence harus antara 0.0 dan 1.0.
        """.strip()
    last_error: Exception | None = None

    for model in TOPIC_CLASSIFIER_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Keluarkan JSON valid saja. "
                            "Jangan memberikan penjelasan tambahan."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0,
                max_tokens=120,
            )

            content = (
                response.choices[0].message.content
                or ""
            )

            result = _extract_json_object(content)

            relation = result.get(
                "relation",
                RELATION_AMBIGUOUS,
            )

            if relation not in ALLOWED_RELATIONS:
                relation = RELATION_AMBIGUOUS

            try:
                confidence = float(
                    result.get("confidence", 0.65)
                )
            except (TypeError, ValueError):
                confidence = 0.65

            confidence = max(
                0.0,
                min(1.0, confidence),
            )

            return {
                "relation": relation,
                "confidence": confidence,
                "topic_label": result.get(
                    "topic_label"
                ),
                "model": model,
            }

        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        "Semua model topic classifier gagal."
    ) from last_error