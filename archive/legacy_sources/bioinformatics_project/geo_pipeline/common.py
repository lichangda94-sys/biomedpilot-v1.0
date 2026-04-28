"""Shared helpers for GEO download and processing modules."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def save_json(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def normalize_accession(accession: str) -> str:
    accession = accession.strip().upper()
    if not accession.startswith("GSE"):
        raise ValueError(f"Only GSE accessions are supported, got: {accession}")
    return accession


def is_gse_like(obj: Any) -> bool:
    return (
        obj is not None
        and getattr(obj, "__class__", type(None)).__name__ == "GSE"
        and hasattr(obj, "gsms")
    )


def standardize_column_name(name: Any) -> str:
    text = str(name).strip().lower()
    text = re.sub(r"[^0-9a-zA-Z]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unnamed"


def build_gse_summary(gse: Any) -> dict[str, Any]:
    metadata = getattr(gse, "metadata", {}) or {}
    metadata_keys = list(metadata.keys())[:20]
    name = None
    if "title" in metadata and metadata["title"]:
        name = metadata["title"][0]
    elif hasattr(gse, "name"):
        name = getattr(gse, "name")

    return {
        "geo_type": getattr(gse, "__class__", type(None)).__name__,
        "name": name,
        "n_samples": len(getattr(gse, "gsms", {}) or {}),
        "n_platforms": len(getattr(gse, "gpls", {}) or {}),
        "metadata_keys": metadata_keys,
    }
