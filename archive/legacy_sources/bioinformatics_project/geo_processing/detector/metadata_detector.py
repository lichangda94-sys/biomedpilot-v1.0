"""Metadata source detection and ranking."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from .models import ContainerType, DataRole, FileScanRecord
from .rules import METADATA_COLUMNS, METADATA_HINTS


def score_metadata_candidate(file_info: dict) -> float:
    """Score how likely a file is to be a metadata source."""
    score = 0.0
    name = Path(str(file_info.get("file_path", ""))).name.lower()
    columns = [str(column).lower() for column in file_info.get("columns", [])]
    container_type = str(file_info.get("container_type", ""))

    if container_type == ContainerType.FAMILY_SOFT.value:
        score += 0.65
    if container_type == ContainerType.MINIML.value:
        score += 0.55
    if any(token in name for token in METADATA_HINTS):
        score += 0.2
    if len(set(columns) & METADATA_COLUMNS) >= 2:
        score += 0.25
    if container_type == ContainerType.SERIES_MATRIX.value:
        score += 0.2
    if "annotation" in name and "gpl" not in name:
        score += 0.1
    return max(0.0, min(1.0, score))


def detect_metadata_sources(scan_records: list[FileScanRecord]) -> Dict[str, object]:
    """Return sorted metadata candidates and preferred source."""
    candidates = []
    for record in scan_records:
        info = {
            "file_path": record.relative_path,
            "columns": record.columns,
            "container_type": record.container_type,
        }
        record.metadata_score = max(record.metadata_score, score_metadata_candidate(info))
        if record.data_role in {DataRole.METADATA.value, DataRole.MIXED.value} or record.metadata_score >= 0.3:
            candidates.append(record)

    candidates.sort(key=lambda item: item.metadata_score, reverse=True)
    return {
        "metadata_files": [record.relative_path for record in candidates],
        "preferred_metadata_source": candidates[0].relative_path if candidates else None,
        "scores": {record.relative_path: round(record.metadata_score, 3) for record in candidates},
    }
