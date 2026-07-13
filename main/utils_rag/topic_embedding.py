# main/utils_rag/topic_embedding.py

from __future__ import annotations

import importlib
import math
from collections.abc import Iterable
from typing import Any


class TopicEmbeddingError(RuntimeError):
    pass


_EMBEDDER_MODULE = "main.utils_embedding.embedder"

_CANDIDATE_FUNCTIONS = (
    "generate_embedding",
    "get_embedding",
    "embed_text",
    "create_embedding",
    "encode_text",
    "encode",
)


def _to_float_list(value: Any) -> list[float]:
    """
    Normalisasi output embedding dari:
    - list
    - tuple
    - numpy array
    - torch tensor
    - dict dengan key embedding/vector
    """
    if value is None:
        raise TopicEmbeddingError("Embedding engine mengembalikan None.")

    if isinstance(value, dict):
        for key in ("embedding", "vector", "data"):
            if key in value:
                value = value[key]
                break

    if hasattr(value, "detach"):
        value = value.detach()

    if hasattr(value, "cpu"):
        value = value.cpu()

    if hasattr(value, "numpy"):
        value = value.numpy()

    if hasattr(value, "tolist"):
        value = value.tolist()

    # Beberapa model mengembalikan [[...]].
    if (
        isinstance(value, list)
        and len(value) == 1
        and isinstance(value[0], (list, tuple))
    ):
        value = value[0]

    if not isinstance(value, Iterable) or isinstance(
        value,
        (str, bytes),
    ):
        raise TopicEmbeddingError(
            "Format hasil embedding tidak dikenali."
        )

    try:
        vector = [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise TopicEmbeddingError(
            "Embedding mengandung nilai non-numerik."
        ) from exc

    if not vector:
        raise TopicEmbeddingError("Embedding kosong.")

    return vector


def _resolve_embedder():
    try:
        module = importlib.import_module(_EMBEDDER_MODULE)
    except ImportError as exc:
        raise TopicEmbeddingError(
            f"Tidak dapat mengimpor {_EMBEDDER_MODULE}."
        ) from exc

    for function_name in _CANDIDATE_FUNCTIONS:
        function = getattr(module, function_name, None)

        if callable(function):
            return function

    raise TopicEmbeddingError(
        "Tidak menemukan fungsi embedding yang didukung di "
        f"{_EMBEDDER_MODULE}. Nama yang dicoba: "
        f"{', '.join(_CANDIDATE_FUNCTIONS)}."
    )


def embed_topic_text(text: str) -> list[float]:
    normalized = " ".join((text or "").strip().split())

    if not normalized:
        raise TopicEmbeddingError(
            "Teks topik tidak boleh kosong."
        )

    embedder = _resolve_embedder()

    try:
        result = embedder(normalized)
    except TypeError:
        # Beberapa embedder menggunakan keyword argument.
        result = embedder(text=normalized)

    return _to_float_list(result)


def cosine_similarity(
    first: list[float],
    second: list[float],
) -> float:
    if not first or not second:
        return 0.0

    if len(first) != len(second):
        raise TopicEmbeddingError(
            "Dimensi embedding topik tidak sama: "
            f"{len(first)} != {len(second)}."
        )

    dot_product = sum(
        left * right
        for left, right in zip(first, second)
    )

    first_norm = math.sqrt(
        sum(value * value for value in first)
    )
    second_norm = math.sqrt(
        sum(value * value for value in second)
    )

    if first_norm == 0 or second_norm == 0:
        return 0.0

    similarity = dot_product / (
        first_norm * second_norm
    )

    # Perlindungan terhadap floating-point overflow kecil.
    return max(-1.0, min(1.0, similarity))


def compare_topic_texts(
    previous_topic: str,
    current_topic: str,
) -> float:
    previous_embedding = embed_topic_text(previous_topic)
    current_embedding = embed_topic_text(current_topic)

    return cosine_similarity(
        previous_embedding,
        current_embedding,
    )