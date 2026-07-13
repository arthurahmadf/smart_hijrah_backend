# main/utils_rag/topic_classifier.py

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Callable

from main.utils_rag.topic_embedding import (
    TopicEmbeddingError,
    compare_topic_texts,
)


RELATION_NEW_TOPIC = "NEW_TOPIC"
RELATION_FOLLOW_UP = "FOLLOW_UP"
RELATION_TOPIC_REFINEMENT = "TOPIC_REFINEMENT"
RELATION_AMBIGUOUS = "AMBIGUOUS"


FOLLOW_UP_NONE = "NONE"
FOLLOW_UP_HADITH = "HADITH"
FOLLOW_UP_QURAN = "QURAN"
FOLLOW_UP_DALIL = "DALIL"
FOLLOW_UP_MUI = "MUI"
FOLLOW_UP_EXPLANATION = "EXPLANATION"
FOLLOW_UP_CONTEXTUAL = "CONTEXTUAL"
FOLLOW_UP_DOA = "DOA"

HIGH_SIMILARITY_THRESHOLD = 0.74
LOW_SIMILARITY_THRESHOLD = 0.46


TOPIC_STOPWORDS = {
    "apa",
    "apakah",
    "bagaimana",
    "berapa",
    "kenapa",
    "mengapa",
    "hukum",
    "hukumnya",
    "bolehkah",
    "boleh",
    "tidak",
    "dalam",
    "menurut",
    "pandangan",
    "islam",
    "islami",
    "syariat",
    "syariah",
    "tentang",
    "mengenai",
    "seputar",
    "dalil",
    "ayat",
    "ayah",
    "quran",
    "alquran",
    "hadis",
    "hadits",
    "riwayat",
    "sebutkan",
    "tampilkan",
    "berikan",
    "carikan",
    "tolong",
    "aku",
    "saya",
    "kami",
    "yang",
    "dan",
    "atau",
    "itu",
    "ini",
    "ya",
    "nya",
}


@dataclass
class TopicRepresentation:
    label: str
    summary: str
    entities: list[str]
    action: str | None
    original_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TopicRelationResult:
    relation: str
    confidence: float
    similarity: float | None
    previous_topic: TopicRepresentation | None
    current_topic: TopicRepresentation
    follow_up_type: str
    used_llm_fallback: bool
    reasoning_code: str

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)

        return result


INFORMAL_NORMALIZATION = {
    "klo": "kalau",
    "klw": "kalau",
    "kalo": "kalau",
    "mnrt": "menurut",
    "menurt": "menurut",
    "gmn": "bagaimana",
    "gimana": "bagaimana",
    "knp": "kenapa",
    "krn": "karena",
    "ga": "tidak",
    "gak": "tidak",
    "nggak": "tidak",
    "hadisny": "hadisnya",
    "haditsny": "hadisnya",
    "ayatny": "ayatnya",
    "dalilny": "dalilnya",
    "doany": "doanya",
}


def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("’", "'")

    text = re.sub(r"[^\w\s'-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = text.split()

    normalized_tokens = [
        INFORMAL_NORMALIZATION.get(token, token)
        for token in tokens
    ]

    return " ".join(normalized_tokens)  


def detect_explicit_follow_up(text: str) -> str:
    normalized = normalize_text(text)

    patterns = {
        FOLLOW_UP_HADITH: [
            r"^(kalau\s+)?hadis(nya)?(\s+juga)?$",
            r"^(kalau\s+)?hadits(nya)?(\s+juga)?$",
            r"^ada\s+hadis(nya)?$",
            r"^ada\s+hadits(nya)?$",
            r"^hadis\s+pendukung(nya)?$",
        ],
        FOLLOW_UP_QURAN: [
            r"^(kalau\s+)?ayat(nya)?(\s+juga)?$",
            r"^(kalau\s+)?quran(nya)?(\s+juga)?$",
            r"^ada\s+ayat(nya)?$",
            r"^ayat\s+pendukung(nya)?$",
        ],
        FOLLOW_UP_DALIL: [
            r"^(kalau\s+)?dalil(nya)?(\s+juga)?$",
            r"^ada\s+dalil(nya)?$",
            r"^apa\s+dalil(nya)?$",
            r"^mana\s+dalil(nya)?$",
            r"^rujukan(nya)?\s+apa$",
        ],
        FOLLOW_UP_MUI: [
            r"^(kalau\s+)?menurut\s+mui$",
            r"^(kalau\s+)?fatwa\s+mui(nya)?$",
            r"^bagaimana\s+menurut\s+mui$",
            r"^mui\s+bilang\s+apa$",
        ],
        FOLLOW_UP_EXPLANATION: [
            r"^jelaskan\s+lagi$",
            r"^jelaskan\s+lebih\s+lanjut$",
            r"^maksudnya\s+apa$",
            r"^apa\s+maksudnya$",
            r"^kenapa$",
            r"^mengapa$",
            r"^kok\s+bisa$",
        ],
        FOLLOW_UP_CONTEXTUAL: [
            r"^kalau\s+begitu$",
            r"^terus$",
            r"^lalu$",
            r"^bagaimana$",
            r"^contohnya$",
            r"^yang\s+tadi$",
            r"^yang\s+itu$",
            r"^bagaimana\s+dengan\s+itu$",
        ],
        FOLLOW_UP_DOA: [
            r"^ada\s+doa(nya)?(\s+yang\s+bisa\s+(kubaca|dibaca))?$",
            r"^doa(nya)?\s+apa$",
            r"^doa\s+apa\s+yang\s+bisa\s+(kubaca|dibaca)$",
            r"^apa\s+ada\s+doa(nya)?$",
            r"^bisa\s+kasih\s+doa(nya)?$",
        ],
    }

    for follow_up_type, type_patterns in patterns.items():
        if any(
            re.fullmatch(pattern, normalized)
            for pattern in type_patterns
        ):
            return follow_up_type

    contextual_signals = [
        r"^kalau\s+begitu\b",
        r"^kalau\s+yang\s+tadi\b",
        r"^kalau\s+hal\s+itu\b",
        r"^kalau\s+masalah\s+itu\b",
        r"\byang\s+tadi\b",
        r"\byang\s+tersebut\b",
        r"\bhal\s+tersebut\b",
        r"\bmasalah\s+itu\b",
    ]

    if any(
        re.search(pattern, normalized)
        for pattern in contextual_signals
    ):
        return FOLLOW_UP_CONTEXTUAL

    return FOLLOW_UP_NONE


def build_topic_representation(
    text: str,
) -> TopicRepresentation:
    """
    Representasi deterministik awal.

    Ini bukan kamus domain besar. Tujuannya hanya membersihkan
    kalimat agar embedding lebih fokus pada topik dan tindakan.
    """
    normalized = normalize_text(text)

    action_patterns = [
        (
            r"\b(dapat|mendapat|menerima)\s+waris(an)?\b",
            "menerima pembagian waris",
        ),
        (
            r"\b(membagi|pembagian)\s+waris(an)?\b",
            "pembagian waris",
        ),
        (
            r"\b(mencari|menghasilkan|mendapatkan)\s+"
            r"(harta|uang|penghasilan)\b",
            "mencari penghasilan sendiri",
        ),
        (
            r"\b(bekerja|kerja|berkarier|karier)\b",
            "bekerja atau berkarier",
        ),
        (
            r"\b(bertaubat|taubat)\b",
            "bertaubat",
        ),
        (
            r"\b(meninggalkan|melalaikan)\s+"
            r"(shalat|sholat)\b",
            "meninggalkan shalat",
        ),
        (
            r"\b(investasi|berinvestasi|trading)\b",
            "investasi",
        ),
        (
            r"\b(paylater|pinjaman online|pinjol)\b",
            "pembiayaan atau utang digital",
        ),
        (
        r"\b(waris|warisan|ahli waris|bagian waris)\b",
            "pembagian waris",
        ),
        (
            r"\b(nafkah|menafkahi|dinafkahi)\b",
            "kewajiban nafkah",
        ),
        (
            r"\b(menggunakan|memakai|mengambil)\s+uang\s+orang\s+tua\b",
            "menggunakan harta orang tua",
        ),
        (
            r"\b(menggunakan|memakai|mengambil)\s+uang\s+kas\b",
            "menggunakan dana amanah",
        ),
        (
            r"\b(zakat|dizakati|menzakati)\b",
            "kewajiban zakat",
        ),
        (
            r"\b(mencari|mengumpulkan)\s+harta\b",
            "mencari kekayaan",
        ),

    ]

    detected_action = None

    for pattern, action in action_patterns:
        if re.search(pattern, normalized):
            detected_action = action
            break

    cleaned = normalized

    prefix_patterns = [
        r"^(apa|bagaimana)\s+hukum\s+",
        r"^hukumnya\s+",
        r"^bolehkah\s+",
        r"^apa\s+boleh\s+",
        r"^(apa|sebutkan|carikan|tampilkan|berikan)\s+"
        r"(dalil|ayat|ayah|hadis|hadits|riwayat)\s+"
        r"(tentang|mengenai)?\s*",
        r"^(dalil|ayat|ayah|hadis|hadits|riwayat)\s+"
        r"(tentang|mengenai)\s+",
    ]

    for pattern in prefix_patterns:
        cleaned = re.sub(pattern, "", cleaned).strip()

    entity_candidates = [
        token
        for token in cleaned.split()
        if token not in TOPIC_STOPWORDS
        and len(token) > 2
    ]

    # N-gram singkat lebih berguna daripada hanya token.
    entities: list[str] = []

    if len(entity_candidates) >= 2:
        entities.append(
            " ".join(entity_candidates[:2])
        )

    entities.extend(entity_candidates[:5])

    # Hilangkan duplikat dengan urutan tetap.
    entities = list(dict.fromkeys(entities))

    summary_parts = []

    if detected_action:
        summary_parts.append(detected_action)

    summary_parts.extend(entity_candidates[:8])

    summary = " ".join(
        dict.fromkeys(summary_parts)
    ).strip()

    if not summary:
        summary = normalized

    label = detected_action or " ".join(
        entity_candidates[:4]
    )

    if not label:
        label = normalized[:80]

    return TopicRepresentation(
        label=label,
        summary=summary[:240],
        entities=entities,
        action=detected_action,
        original_text=text,
    )


def build_comparison_text(
    topic: TopicRepresentation,
) -> str:
    parts = [
        f"topik {topic.label}",
        f"ringkasan {topic.summary}",
    ]

    if topic.action:
        parts.append(f"tindakan {topic.action}")

    if topic.entities:
        parts.append(
            f"entitas {' '.join(topic.entities)}"
        )

    return ". ".join(parts)


def classify_topic_relation(
    previous_topic: TopicRepresentation | None,
    current_message: str,
    llm_fallback: Callable[
        [
            TopicRepresentation,
            TopicRepresentation,
            float,
        ],
        dict[str, Any],
    ]
    | None = None,
) -> TopicRelationResult:
    current_topic = build_topic_representation(
        current_message
    )

    follow_up_type = detect_explicit_follow_up(
        current_message
    )

    if previous_topic is None:
        return TopicRelationResult(
            relation=RELATION_NEW_TOPIC,
            confidence=1.0,
            similarity=None,
            previous_topic=None,
            current_topic=current_topic,
            follow_up_type=follow_up_type,
            used_llm_fallback=False,
            reasoning_code="NO_PREVIOUS_TOPIC",
        )

    if follow_up_type != FOLLOW_UP_NONE:
        return TopicRelationResult(
            relation=RELATION_FOLLOW_UP,
            confidence=0.96,
            similarity=None,
            previous_topic=previous_topic,
            current_topic=current_topic,
            follow_up_type=follow_up_type,
            used_llm_fallback=False,
            reasoning_code="EXPLICIT_FOLLOW_UP_RULE",
        )

    if detect_explicit_new_topic(current_message):
        return TopicRelationResult(
            relation=RELATION_NEW_TOPIC,
            confidence=0.94,
            similarity=None,
            previous_topic=previous_topic,
            current_topic=current_topic,
            follow_up_type=FOLLOW_UP_NONE,
            used_llm_fallback=False,
            reasoning_code="EXPLICIT_SELF_CONTAINED_NEW_TOPIC",
        )


    previous_comparison = build_comparison_text(
        previous_topic
    )
    current_comparison = build_comparison_text(
        current_topic
    )

    try:
        similarity = compare_topic_texts(
            previous_comparison,
            current_comparison,
        )
    except TopicEmbeddingError:
        similarity = None

    if similarity is not None:
        if similarity >= HIGH_SIMILARITY_THRESHOLD:
            return TopicRelationResult(
                relation=RELATION_TOPIC_REFINEMENT,
                confidence=min(0.97, similarity),
                similarity=similarity,
                previous_topic=previous_topic,
                current_topic=current_topic,
                follow_up_type=FOLLOW_UP_NONE,
                used_llm_fallback=False,
                reasoning_code="HIGH_SEMANTIC_SIMILARITY",
            )

        if (
            similarity <= LOW_SIMILARITY_THRESHOLD
            and not is_short_context_dependent_message(
                current_message
            )
        ):
            return TopicRelationResult(
                relation=RELATION_NEW_TOPIC,
                confidence=min(
                    0.97,
                    1.0 - similarity,
                ),
                similarity=similarity,
                previous_topic=previous_topic,
                current_topic=current_topic,
                follow_up_type=FOLLOW_UP_NONE,
                used_llm_fallback=False,
                reasoning_code="LOW_SEMANTIC_SIMILARITY",
            )

    # Zona abu-abu atau embedding gagal.
    if llm_fallback is not None:
        try:
            llm_result = llm_fallback(
                previous_topic,
                current_topic,
                similarity if similarity is not None else 0.5,
            )

            relation = llm_result.get(
                "relation",
                RELATION_AMBIGUOUS,
            )

            # Validasi hasil LLM terlebih dahulu sebelum menjalankan
            # deterministic guardrails.
            if relation not in {
                RELATION_NEW_TOPIC,
                RELATION_FOLLOW_UP,
                RELATION_TOPIC_REFINEMENT,
                RELATION_AMBIGUOUS,
            }:
                relation = RELATION_AMBIGUOUS

            contextual_refinement = (
                is_contextual_condition_refinement(
                    previous_topic,
                    current_topic,
                )
            )

            action_conflict = actions_are_conflicting(
                previous_topic,
                current_topic,
            )

            # Guardrail 1:
            # Pesan bersyarat seperti "kalau...", "jika...", atau
            # "bagaimana jika..." yang masih berkaitan dengan entitas
            # lama lebih tepat dianggap TOPIC_REFINEMENT.
            if (
                relation == RELATION_NEW_TOPIC
                and contextual_refinement
            ):
                relation = RELATION_TOPIC_REFINEMENT

            # Guardrail 2:
            # Pesan lengkap dan mandiri tidak boleh dianggap FOLLOW_UP
            # hanya karena meminta dalil, hukum, atau penjelasan.
            if (
                relation == RELATION_FOLLOW_UP
                and is_self_contained_topic_query(
                    current_topic.original_text
                )
            ):
                previous_action = normalize_text(
                    previous_topic.action or ""
                )
                current_action = normalize_text(
                    current_topic.action or ""
                )

                same_action = bool(
                    previous_action
                    and current_action
                    and previous_action == current_action
                )

                # Jangan ubah menjadi NEW_TOPIC bila pesan tersebut
                # sebenarnya merupakan kondisi lanjutan terhadap
                # masalah sebelumnya.
                if (
                    not same_action
                    and not contextual_refinement
                ):
                    relation = RELATION_NEW_TOPIC

            # Guardrail 3:
            # Action yang benar-benar berbeda biasanya menandakan
            # topik baru, kecuali action baru hanya menjadi kondisi
            # dalam analisis topik lama.
            if (
                relation
                in {
                    RELATION_FOLLOW_UP,
                    RELATION_TOPIC_REFINEMENT,
                }
                and action_conflict
                and not contextual_refinement
            ):
                relation = RELATION_NEW_TOPIC

            try:
                confidence = float(
                    llm_result.get("confidence", 0.7)
                )
            except (TypeError, ValueError):
                confidence = 0.7

            confidence = max(
                0.0,
                min(1.0, confidence),
            )

            return TopicRelationResult(
                relation=relation,
                confidence=confidence,
                similarity=similarity,
                previous_topic=previous_topic,
                current_topic=current_topic,
                follow_up_type=FOLLOW_UP_NONE,
                used_llm_fallback=True,
                reasoning_code="LLM_AMBIGUOUS_ZONE",
            )

        except Exception as exc:
            print(
                "[TOPIC CLASSIFIER] "
                f"LLM fallback gagal: {type(exc).__name__}: {exc}"
            )
    return TopicRelationResult(
        relation=RELATION_AMBIGUOUS,
        confidence=0.5,
        similarity=similarity,
        previous_topic=previous_topic,
        current_topic=current_topic,
        follow_up_type=FOLLOW_UP_NONE,
        used_llm_fallback=False,
        reasoning_code="AMBIGUOUS_WITHOUT_LLM_RESULT",
    )


def is_self_contained_topic_query(text: str) -> bool:
    """
    True jika pesan menyebut topik/objek baru secara cukup lengkap
    dan dapat dipahami tanpa context sebelumnya.
    """
    normalized = normalize_text(text)

    patterns = [
        r"^apa\s+(dalil|ayat|hadis|hadits)\s+tentang\s+.+",
        r"^dalil\s+tentang\s+.+",
        r"^ayat\s+tentang\s+.+",
        r"^hadis\s+tentang\s+.+",
        r"^hadits\s+tentang\s+.+",
        r"^pemimpin\s+.+",
        r"^hukum\s+.+",
        r"^apa\s+hukum\s+.+",
        r"^bolehkah\s+.+",
        r"^kalau\s+tentang\s+.+",
    ]

    if any(
        re.search(pattern, normalized)
        for pattern in patterns
    ):
        return True

    # Kalimat cukup panjang dan memiliki topik substantif.
    tokens = [
        token
        for token in normalized.split()
        if token not in TOPIC_STOPWORDS
    ]

    return len(tokens) >= 4


def detect_explicit_new_topic(text: str) -> bool:
    normalized = normalize_text(text)

    patterns = [
        r"^apa\s+(dalil|ayat|hadis|hadits)\s+tentang\s+.+",
        r"^(dalil|ayat|hadis|hadits)\s+tentang\s+.+",
        r"^kalau\s+tentang\s+.+",
        r"^pemimpin\s+.+",
        r"^hukum\s+.+",
        r"^apa\s+hukum\s+.+",
    ]

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )

def _normalize_action(action: str | None) -> str:
    return normalize_text(action or "")


def actions_are_conflicting(
    previous_topic: TopicRepresentation,
    current_topic: TopicRepresentation,
) -> bool:
    previous_action = _normalize_action(
        previous_topic.action
    )
    current_action = _normalize_action(
        current_topic.action
    )

    if not previous_action or not current_action:
        return False

    return previous_action != current_action

def has_distinct_ownership_context(
    previous_topic: TopicRepresentation,
    current_topic: TopicRepresentation,
) -> bool:
    previous_text = normalize_text(
        previous_topic.original_text
    )
    current_text = normalize_text(
        current_topic.original_text
    )

    ownership_groups = [
        {
            "orang tua",
            "ayah",
            "ibu",
            "keluarga",
        },
        {
            "kas masjid",
            "uang kas",
            "dana masjid",
            "pengurus masjid",
        },
        {
            "uang suami",
            "harta suami",
        },
        {
            "uang perusahaan",
            "dana perusahaan",
        },
    ]

    previous_group = None
    current_group = None

    for index, group in enumerate(ownership_groups):
        if any(term in previous_text for term in group):
            previous_group = index

        if any(term in current_text for term in group):
            current_group = index

    return (
        previous_group is not None
        and current_group is not None
        and previous_group != current_group
    )


def is_short_context_dependent_message(
    text: str,
) -> bool:
    normalized = normalize_text(text)
    tokens = normalized.split()

    contextual_terms = {
        "menurut",
        "mui",
        "kenapa",
        "bagaimana",
        "doa",
        "dalil",
        "hadis",
        "ayat",
        "sumber",
    }

    return (
        len(tokens) <= 5
        and any(
            token in contextual_terms
            for token in tokens
        )
    )

def is_contextual_condition_refinement(
    previous_topic: TopicRepresentation,
    current_topic: TopicRepresentation,
) -> bool:
    """
    True jika pesan baru menambahkan kondisi terhadap topik lama,
    bukan mengganti masalah utama.

    Contoh:
    - nafkah anak perempuan
      -> kalau anak perempuannya sudah bekerja sendiri?
    - hukum paylater
      -> kalau tidak ada bunga?
    - waris anak perempuan
      -> kalau anak perempuannya dua?
    """
    current_text = normalize_text(
        current_topic.original_text
    )

    previous_text = normalize_text(
        " ".join([
            previous_topic.label or "",
            previous_topic.summary or "",
            previous_topic.original_text or "",
        ])
    )

    contextual_prefixes = [
        "kalau ",
        "jika ",
        "apabila ",
        "bagaimana jika ",
        "bagaimana kalau ",
    ]

    starts_contextually = any(
        current_text.startswith(prefix)
        for prefix in contextual_prefixes
    )

    if not starts_contextually:
        return False

    previous_entities = {
        entity
        for entity in previous_topic.entities
        if len(normalize_text(entity)) >= 3
    }

    current_entities = {
        entity
        for entity in current_topic.entities
        if len(normalize_text(entity)) >= 3
    }

    entity_overlap = False

    for previous_entity in previous_entities:
        previous_normalized = normalize_text(
            previous_entity
        )

        for current_entity in current_entities:
            current_normalized = normalize_text(
                current_entity
            )

            if (
                previous_normalized in current_normalized
                or current_normalized in previous_normalized
            ):
                entity_overlap = True
                break

        if entity_overlap:
            break

    # Fallback lexical overlap pada kata substantif.
    previous_tokens = {
        token
        for token in previous_text.split()
        if token not in TOPIC_STOPWORDS
        and len(token) > 2
    }

    current_tokens = {
        token
        for token in current_text.split()
        if token not in TOPIC_STOPWORDS
        and len(token) > 2
    }

    token_overlap = previous_tokens & current_tokens

    return entity_overlap or len(token_overlap) >= 1