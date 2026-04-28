"""Content-level signature inspection for GEO dataset files."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict

from .models import ContainerType, DataRole
from .rules import DIFF_RESULT_COLUMNS, RAW_EXTENSIONS
from .utils import normalize_extension, preview_delimited_rows, preview_xlsx_rows, read_text_head

LOGGER = logging.getLogger(__name__)


SOFT_PATTERNS = (
    re.compile(r"^SERIES\b", re.IGNORECASE),
    re.compile(r"^SAMPLE\b", re.IGNORECASE),
    re.compile(r"^!Series_", re.IGNORECASE),
    re.compile(r"^!Sample_", re.IGNORECASE),
    re.compile(r"^!sample_table_begin", re.IGNORECASE),
    re.compile(r"^!sample_table_end", re.IGNORECASE),
)


def _contains_soft_signature(lines: list[str]) -> bool:
    return any(pattern.search(line) for pattern in SOFT_PATTERNS for line in lines)


def _contains_series_matrix_signature(name: str, lines: list[str], rows: list[list[str]]) -> bool:
    has_series_name = "series_matrix" in name.lower()
    has_soft_markers = any(line.startswith("!Series_") or line.startswith("!Sample_") for line in lines)
    has_table = any(len(row) >= 4 for row in rows)
    return has_series_name and has_soft_markers and has_table


def _contains_miniml_signature(extension: str, lines: list[str]) -> bool:
    joined = "\n".join(lines[:10])
    return extension == ".xml" and "<?xml" in joined and "MINiML" in joined


def inspect_file_signature(file_path: str) -> Dict[str, object]:
    """Inspect a file and infer coarse container type, data role, and preview."""
    path = Path(file_path)
    extension = normalize_extension(file_path)
    name = path.name.lower()
    result: Dict[str, object] = {
        "file_path": file_path,
        "extension": extension,
        "container_type": ContainerType.UNKNOWN.value,
        "data_role": DataRole.UNKNOWN.value,
        "preview_lines": [],
        "preview_rows": [],
        "columns": [],
        "is_diff_result_hint": False,
        "warnings": [],
    }

    if extension in RAW_EXTENSIONS:
        result["container_type"] = ContainerType.RAW_FILE.value
        result["data_role"] = DataRole.RAW.value
        return result

    preview_rows: list[list[str]] = []
    preview_lines = preview_xlsx_rows(file_path) if extension in {".xls", ".xlsx"} else read_text_head(file_path)
    if extension in {".xls", ".xlsx"}:
        preview_rows = preview_lines
        preview_lines = ["\t".join(row) for row in preview_rows[:20]]
    else:
        preview_rows = preview_delimited_rows(preview_lines)

    columns = preview_rows[0] if preview_rows else []
    result["preview_lines"] = preview_lines
    result["preview_rows"] = preview_rows
    result["columns"] = columns

    if _contains_series_matrix_signature(path.name, preview_lines, preview_rows):
        result["container_type"] = ContainerType.SERIES_MATRIX.value
        result["data_role"] = DataRole.MIXED.value
    elif _contains_soft_signature(preview_lines):
        result["container_type"] = ContainerType.FAMILY_SOFT.value
        result["data_role"] = DataRole.METADATA.value
    elif _contains_miniml_signature(extension, preview_lines):
        result["container_type"] = ContainerType.MINIML.value
        result["data_role"] = DataRole.METADATA.value
    elif any(token in name for token in ("gpl", "platform", "annot")):
        result["container_type"] = ContainerType.PLATFORM_ANNOTATION.value
        result["data_role"] = DataRole.METADATA.value
    elif extension in {".txt", ".tsv", ".csv", ".xls", ".xlsx"}:
        result["container_type"] = ContainerType.SUPPLEMENTARY.value
        result["data_role"] = DataRole.PROCESSED.value
    else:
        result["container_type"] = ContainerType.UNKNOWN.value

    lowered_columns = {column.strip().lower() for column in columns}
    if len(lowered_columns & DIFF_RESULT_COLUMNS) >= 2:
        result["is_diff_result_hint"] = True

    return result
