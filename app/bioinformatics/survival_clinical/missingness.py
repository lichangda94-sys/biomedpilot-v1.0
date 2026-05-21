from __future__ import annotations

from typing import Any


def missingness(values: list[object]) -> dict[str, Any]:
    total = len(values)
    missing_count = sum(1 for value in values if str(value or "").strip() == "")
    non_missing = total - missing_count
    return {
        "missing_count": missing_count,
        "missing_rate": missing_count / total if total else 0.0,
        "non_missing_count": non_missing,
    }
