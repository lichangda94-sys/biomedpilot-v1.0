from __future__ import annotations

import os
from typing import Any


def light_validation_enabled() -> bool:
    return str(os.environ.get("BIOINF_LIGHT_VALIDATION_MODE") or "").strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int = 0) -> int:
    try:
        value = int(str(os.environ.get(name, default)).strip())
    except (TypeError, ValueError):
        return default
    return max(value, 0)


def tcga_download_limit_files() -> int:
    return env_int("BIOINF_TCGA_DOWNLOAD_LIMIT_FILES", 0)


def gtex_download_limit_files() -> int:
    return env_int("BIOINF_GTEX_DOWNLOAD_LIMIT_FILES", 0)


def gtex_limit_samples() -> int:
    return env_int("BIOINF_GTEX_LIMIT_SAMPLES", 0)


def gtex_limit_genes() -> int:
    return env_int("BIOINF_GTEX_LIMIT_GENES", 0)


def validation_settings() -> dict[str, Any]:
    return {
        "validation_limited": light_validation_enabled(),
        "BIOINF_LIGHT_VALIDATION_MODE": os.environ.get("BIOINF_LIGHT_VALIDATION_MODE", ""),
        "BIOINF_TCGA_DOWNLOAD_LIMIT_FILES": tcga_download_limit_files(),
        "BIOINF_GTEX_DOWNLOAD_LIMIT_FILES": gtex_download_limit_files(),
        "BIOINF_GTEX_LIMIT_SAMPLES": gtex_limit_samples(),
        "BIOINF_GTEX_LIMIT_GENES": gtex_limit_genes(),
    }


def validation_warning() -> str:
    return "轻量联网验收数据，不可用于正式分析、DEG/GSEA/KM/Cox/log-rank 或报告生成。"


def apply_limit(entries: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return entries
    return entries[:limit]


__all__ = [
    "apply_limit",
    "env_int",
    "gtex_download_limit_files",
    "gtex_limit_genes",
    "gtex_limit_samples",
    "light_validation_enabled",
    "tcga_download_limit_files",
    "validation_settings",
    "validation_warning",
]
