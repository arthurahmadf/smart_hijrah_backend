from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .gold_schema import GoldDataset, default_gold_dataset_path


def load_gold_dataset(path: Path | str) -> GoldDataset:
    resolved_path = Path(path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Gold dataset tidak ditemukan: {resolved_path}")

    with resolved_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    return GoldDataset.from_dict(payload)


def load_default_gold_dataset(base_dir: Optional[Path] = None) -> GoldDataset:
    if base_dir is None:
        try:
            from django.conf import settings

            base_dir = Path(settings.BASE_DIR)
        except Exception as exc:  # pragma: no cover - fallback non-Django
            raise RuntimeError(
                "base_dir wajib diberikan ketika Django settings belum aktif."
            ) from exc

    return load_gold_dataset(default_gold_dataset_path(Path(base_dir)))
