# main/utils_rag/thematic_retrieval.py

import re
from typing import Any

from main.utils_hadis.semantic_search import (
    semantic_search_quran,
    semantic_search_hadis,
)
from main.utils_hadis.search import search_hadis_by_keyword


THEMATIC_STOPWORDS = {
    "apa",
    "apakah",
    "mana",
    "yang",
    "tentang",
    "mengenai",
    "seputar",
    "dalil",
    "ayat",
    "ayah",
    "quran",
    "alquran",
    "al-quran",
    "al",
    "hadis",
    "hadits",
    "riwayat",
    "sebutkan",
    "tampilkan",
    "berikan",
    "carikan",
    "cari",
    "tolong",
    "untuk",
    "dalam",
    "islam",
    "islami",
    "dari",
    "di",
    "ke",
    "dan",
    "atau",
    "itu",
    "ini",
}


def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("’", "'")
    text = re.sub(r"[^\w\s'-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_theme_query(user_query: str) -> str:
    """
    Ubah:
    - "Apa dalil tentang sabar?" -> "sabar"
    - "Sebutkan hadis tentang niat" -> "niat"
    - "Ayat tentang sedekah" -> "sedekah"
    """
    normalized = _normalize(user_query)

    tokens = [
        token
        for token in normalized.split()
        if token not in THEMATIC_STOPWORDS and len(token) > 1
    ]

    result = " ".join(tokens).strip()

    # Fallback agar semantic search tetap menerima query.
    return result or normalized


def detect_source_preference(user_query: str) -> str:
    """
    Return:
    - quran
    - hadis
    - both
    """
    text = _normalize(user_query)

    quran_signals = [
        "ayat",
        "ayah",
        "quran",
        "al quran",
        "alquran",
        "surah",
        "surat",
    ]

    hadith_signals = [
        "hadis",
        "hadits",
        "riwayat",
        "sabda nabi",
        "sabda rasul",
    ]

    has_quran = any(signal in text for signal in quran_signals)
    has_hadith = any(signal in text for signal in hadith_signals)

    if has_quran and not has_hadith:
        return "quran"

    if has_hadith and not has_quran:
        return "hadis"

    return "both"


def _tokenize(text: str) -> set[str]:
    normalized = _normalize(text)

    return {
        token
        for token in normalized.split()
        if token not in THEMATIC_STOPWORDS and len(token) > 2
    }


def _calculate_keyword_overlap(theme: str, candidate_text: str) -> float:
    theme_tokens = _tokenize(theme)
    candidate_tokens = _tokenize(candidate_text)

    if not theme_tokens:
        return 0.0

    overlap = theme_tokens.intersection(candidate_tokens)

    return len(overlap) / len(theme_tokens)


def _get_similarity(item: Any) -> float:
    try:
        return float(getattr(item, "similarity", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _quran_candidate_text(item: Any) -> str:
    return " ".join([
        str(getattr(item, "surah_name", "") or ""),
        str(getattr(item, "ayah_translation", "") or ""),
        str(getattr(item, "ayah_transliteration", "") or ""),
    ])


def _hadith_candidate_text(item: Any) -> str:
    return " ".join([
        str(getattr(item, "isi_hadis", "") or ""),
        str(getattr(item, "terjemahan", "") or ""),
        str(getattr(item, "teks_hadis", "") or ""),
    ])


def _score_candidate(
    theme: str,
    candidate_text: str,
    semantic_similarity: float,
) -> float:
    """
    Gabungkan semantic similarity dan keyword overlap.

    Semantic lebih dominan karena istilah user dapat berbeda
    dengan terjemahan database.
    """
    keyword_overlap = _calculate_keyword_overlap(
        theme,
        candidate_text,
    )

    return (
        semantic_similarity * 0.75
        + keyword_overlap * 0.25
    )


def _deduplicate_quran(items):
    seen = set()
    output = []

    for item in items:
        key = (
            getattr(item, "surah_number", None),
            getattr(item, "ayah_number", None),
        )

        if key in seen:
            continue

        seen.add(key)
        output.append(item)

    return output


def _deduplicate_hadith(items):
    seen = set()
    output = []

    for item in items:
        kitab = getattr(item, "kitab", None)
        kitab_id = getattr(kitab, "id", None)

        key = (
            kitab_id,
            getattr(item, "nomor", None),
        )

        if key in seen:
            continue

        seen.add(key)
        output.append(item)

    return output


def _rank_quran_results(theme: str, items, limit: int):
    ranked = []

    for item in items:
        similarity = _get_similarity(item)
        candidate_text = _quran_candidate_text(item)

        score = _score_candidate(
            theme=theme,
            candidate_text=candidate_text,
            semantic_similarity=similarity,
        )

        # Simpan untuk debugging/benchmark.
        item.retrieval_score = score
        ranked.append(item)

    ranked.sort(
        key=lambda item: getattr(item, "retrieval_score", 0),
        reverse=True,
    )

    return _deduplicate_quran(ranked)[:limit]


def _rank_hadith_results(theme: str, items, limit: int):
    ranked = []

    for item in items:
        similarity = _get_similarity(item)
        candidate_text = _hadith_candidate_text(item)

        score = _score_candidate(
            theme=theme,
            candidate_text=candidate_text,
            semantic_similarity=similarity,
        )

        item.retrieval_score = score
        ranked.append(item)

    ranked.sort(
        key=lambda item: getattr(item, "retrieval_score", 0),
        reverse=True,
    )

    return _deduplicate_hadith(ranked)[:limit]


def _quran_to_source(item):
    similarity = _get_similarity(item)
    retrieval_score = float(
        getattr(item, "retrieval_score", similarity) or 0
    )

    return {
        "type": "QURAN",
        "label": "Ditemukan melalui Pencarian Tematik ✅",
        "reference": (
            f"QS. {item.surah_name} "
            f"({item.surah_number}) : {item.ayah_number}"
        ),
        "arabic_text": item.ayah_text or "",
        "translation_text": item.ayah_translation or "",
        "transliteration_text": (
            item.ayah_transliteration or ""
        ),
        "is_verified": True,
        "surah_number": item.surah_number,
        "ayah_number": item.ayah_number,
        "semantic_similarity": similarity,
        "retrieval_score": retrieval_score,
        "retrieval_mode": "THEMATIC_RETRIEVAL",
    }


def _hadith_to_source(item):
    similarity = _get_similarity(item)
    retrieval_score = float(
        getattr(item, "retrieval_score", similarity) or 0
    )

    kitab = item.kitab

    return {
        "type": "HADIS",
        "label": (
            "Ditemukan melalui Pencarian Tematik ✅ "
            "(Derajat hadis belum ditampilkan)"
        ),
        "reference": (
            f"{kitab.nama_indonesia} No. {item.nomor}"
        ),
        "arabic_text": item.teks_arab or item.teks_hadis or "",
        "translation_text": (
            item.terjemahan or item.isi_hadis or ""
        ),
        "is_verified": True,
        "book_slug": kitab.nama_file,
        "number": item.nomor,
        "semantic_similarity": similarity,
        "retrieval_score": retrieval_score,
        "retrieval_mode": "THEMATIC_RETRIEVAL",
    }


def retrieve_thematic_evidence(
    user_query: str,
    quran_limit: int = 3,
    hadith_limit: int = 3,
):
    """
    Retrieval-first untuk pencarian dalil tematik.

    Tidak menggunakan LLM untuk memilih referensi.
    """
    theme = extract_theme_query(user_query)
    preference = detect_source_preference(user_query)

    quran_results = []
    hadith_results = []

    # Ambil kandidat lebih banyak daripada output akhir agar bisa diranking.
    candidate_multiplier = 4

    if preference in {"quran", "both"}:
        quran_candidates = semantic_search_quran(
            theme,
            limit=quran_limit * candidate_multiplier,
            threshold=0.42,
        )

        quran_results = _rank_quran_results(
            theme=theme,
            items=quran_candidates or [],
            limit=quran_limit,
        )

    if preference in {"hadis", "both"}:
        hadith_candidates = semantic_search_hadis(
            theme,
            limit=hadith_limit * candidate_multiplier,
            threshold=0.42,
        )

        # Keyword fallback berguna untuk tema pendek seperti "niat".
        keyword_candidates = search_hadis_by_keyword(
            theme,
            limit=hadith_limit * 2,
        )

        for candidate in keyword_candidates or []:
            if not hasattr(candidate, "similarity"):
                candidate.similarity = 0.55

        combined_hadith = list(hadith_candidates or [])
        combined_hadith.extend(keyword_candidates or [])

        hadith_results = _rank_hadith_results(
            theme=theme,
            items=combined_hadith,
            limit=hadith_limit,
        )

    sources = []

    for item in quran_results:
        sources.append(_quran_to_source(item))

    for item in hadith_results:
        sources.append(_hadith_to_source(item))

    # Buang kandidat yang terlalu rendah setelah combined ranking.
    sources = [
        source
        for source in sources
        if source.get("retrieval_score", 0) >= 0.34
    ]

    sources.sort(
        key=lambda source: source.get(
            "retrieval_score",
            0,
        ),
        reverse=True,
    )

    return {
        "theme": theme,
        "source_preference": preference,
        "verified_sources": sources,
        "quran_count": sum(
            1 for source in sources
            if source.get("type") == "QURAN"
        ),
        "hadith_count": sum(
            1 for source in sources
            if source.get("type") == "HADIS"
        ),
    }