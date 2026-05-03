from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .term_index_models import ChineseTermOverride


def default_zh_overrides_path() -> Path:
    return Path(__file__).resolve().parents[4] / "data" / "medical_terms" / "zh_term_overrides.json"


@lru_cache(maxsize=4)
def load_zh_overrides(path: str | None = None) -> tuple[ChineseTermOverride, ...]:
    resolved = Path(path) if path else default_zh_overrides_path()
    if not resolved.exists():
        return ()
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except Exception:
        return ()
    if not isinstance(payload, list):
        return ()
    return tuple(ChineseTermOverride.from_dict(item) for item in payload if isinstance(item, dict))
