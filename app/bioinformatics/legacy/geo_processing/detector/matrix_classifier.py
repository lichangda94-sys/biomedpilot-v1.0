"""Heuristics for distinguishing expression matrices from other tables."""

from __future__ import annotations

import logging
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List

from .models import MatrixLevel, ValueSemantic
from .rules import (
    DIFF_RESULT_COLUMNS,
    EXPRESSION_HINTS,
    EXPRESSION_NEGATIVE_HINTS,
    GENE_PREFIXES,
    MATRIX_PRIORITY_ORDER,
    METADATA_COLUMNS,
    PROBE_PATTERNS,
    TABULAR_EXTENSIONS,
    TRANSCRIPT_PREFIXES,
)
from .utils import normalize_extension, preview_delimited_rows, preview_xlsx_rows, read_text_head

LOGGER = logging.getLogger(__name__)


def looks_like_probe_id(text: str) -> bool:
    """Return True when the identifier resembles a probe/reporter id."""
    value = str(text).strip()
    if not value:
        return False
    upper_value = value.upper()
    return any(pattern.upper() in upper_value for pattern in PROBE_PATTERNS)


def looks_like_ensembl_id(text: str) -> bool:
    """Return True when the identifier looks like an Ensembl gene or transcript id."""
    value = str(text).strip().upper()
    return value.startswith(GENE_PREFIXES) or value.startswith(TRANSCRIPT_PREFIXES)


GENE_SYMBOL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9\-_.]{1,14}$")


def looks_like_gene_symbol(text: str) -> bool:
    """Return True when the identifier resembles a gene symbol."""
    value = str(text).strip()
    if not value or len(value) > 15 or " " in value:
        return False
    if value.upper().startswith(("GSM", "GSE", "GPL")):
        return False
    return bool(GENE_SYMBOL_RE.match(value))


def looks_like_diff_result_columns(columns: list[str]) -> bool:
    """Return True when columns are dominated by differential result markers."""
    lowered = {column.strip().lower() for column in columns}
    return len(lowered & DIFF_RESULT_COLUMNS) >= 2


def _is_numeric(value: str) -> bool:
    try:
        float(str(value).strip())
        return True
    except (TypeError, ValueError):
        return False


def _numeric_values(preview_rows: list[list[str]]) -> list[float]:
    numbers: list[float] = []
    for row in preview_rows[1:]:
        for cell in row[1:]:
            if _is_numeric(cell):
                numbers.append(float(cell))
    return numbers


def infer_value_semantic_from_preview(preview_rows: list[list[str]]) -> ValueSemantic:
    """Infer whether preview values behave like counts, log values, or ratios."""
    values = _numeric_values(preview_rows)
    if len(values) < 6:
        return ValueSemantic.UNKNOWN

    finite_values = [value for value in values if math.isfinite(value)]
    if len(finite_values) < 6:
        return ValueSemantic.UNKNOWN

    min_value = min(finite_values)
    max_value = max(finite_values)
    integer_ratio = sum(float(value).is_integer() for value in finite_values) / len(finite_values)
    non_negative_ratio = sum(value >= 0 for value in finite_values) / len(finite_values)
    in_log_window_ratio = sum(-3 <= value <= 20 for value in finite_values) / len(finite_values)
    near_ratio_window = sum(-5 <= value <= 5 for value in finite_values) / len(finite_values)

    if integer_ratio >= 0.85 and non_negative_ratio >= 0.98 and max_value >= 20:
        return ValueSemantic.RAW_COUNTS
    if integer_ratio < 0.5 and non_negative_ratio >= 0.95 and max_value >= 500 and (max_value / max(min_value, 1e-6)) > 100:
        return ValueSemantic.INTENSITY
    if in_log_window_ratio >= 0.8 and max_value <= 25:
        return ValueSemantic.LOG2_EXPRESSION
    if near_ratio_window >= 0.8 and min_value < 0:
        return ValueSemantic.RATIO
    if non_negative_ratio >= 0.98 and max_value <= 1_000_000 and integer_ratio < 0.8:
        return ValueSemantic.NORMALIZED_COUNTS
    return ValueSemantic.UNKNOWN


def _load_preview_rows(file_path: str) -> list[list[str]]:
    extension = normalize_extension(file_path)
    if extension not in TABULAR_EXTENSIONS:
        return []
    if extension in {".xls", ".xlsx"}:
        return preview_xlsx_rows(file_path)
    return preview_delimited_rows(read_text_head(file_path))


def _normalize_matrix_rows(preview_rows: list[list[str]]) -> list[list[str]]:
    """Trim non-tabular preamble and keep the densest table-like region."""
    if not preview_rows:
        return []

    header_index, header_width = max(
        ((index, len(row)) for index, row in enumerate(preview_rows)),
        key=lambda item: item[1],
    )
    if header_width < 2:
        return preview_rows

    normalized: list[list[str]] = []
    for row in preview_rows[header_index:]:
        if len(row) >= max(2, header_width - 1):
            padded = row + [""] * (header_width - len(row))
            normalized.append(padded[:header_width])
        elif normalized:
            break
    return normalized or preview_rows


def _count_numeric_cells(rows: list[list[str]]) -> tuple[int, int]:
    total = 0
    numeric = 0
    for row in rows[1:]:
        for cell in row[1:]:
            if str(cell).strip():
                total += 1
                if _is_numeric(cell):
                    numeric += 1
    return numeric, total


def _sample_column_count(columns: list[str]) -> int:
    metadata_exact = {value.lower() for value in METADATA_COLUMNS}
    diff_exact = {value.lower() for value in DIFF_RESULT_COLUMNS}
    return sum(
        1
        for column in columns[1:]
        if column
        and column.strip().lower() not in metadata_exact
        and column.strip().lower() not in diff_exact
        and not column.strip().lower().endswith("_id")
    )


def _infer_matrix_level(columns: list[str], preview_rows: list[list[str]]) -> MatrixLevel:
    if looks_like_diff_result_columns(columns):
        return MatrixLevel.DIFF_RESULT
    if len(preview_rows) < 2 or len(columns) < 3:
        return MatrixLevel.NON_MATRIX

    id_samples = [row[0] for row in preview_rows[1:8] if row]
    if any(looks_like_probe_id(sample) for sample in id_samples):
        return MatrixLevel.PROBE
    if any(str(sample).strip().upper().startswith(TRANSCRIPT_PREFIXES) for sample in id_samples):
        return MatrixLevel.TRANSCRIPT
    if any(str(sample).strip().upper().startswith(GENE_PREFIXES) for sample in id_samples):
        return MatrixLevel.GENE
    if any(looks_like_gene_symbol(sample) for sample in id_samples):
        return MatrixLevel.GENE
    if any("transcript" in column.lower() for column in columns[:3]):
        return MatrixLevel.TRANSCRIPT
    if any(token in " ".join(columns[:5]).lower() for token in ("probe", "reporter", "feature id")):
        return MatrixLevel.PROBE
    return MatrixLevel.UNKNOWN


def score_expression_candidate(file_info: dict) -> float:
    """Score how likely a file is to be a processed expression matrix."""
    score = 0.0
    name = Path(str(file_info.get("file_path", ""))).name.lower()
    columns = [str(column) for column in file_info.get("columns", [])]
    preview_rows = file_info.get("preview_rows", [])
    matrix_level = str(file_info.get("matrix_level", MatrixLevel.UNKNOWN.value))
    numeric_cells, total_cells = _count_numeric_cells(preview_rows)
    numeric_ratio = (numeric_cells / total_cells) if total_cells else 0.0
    sample_columns = _sample_column_count(columns)

    if "series_matrix" in name:
        score += 0.45
    if any(token in name for token in EXPRESSION_HINTS):
        score += 0.25
    if sample_columns >= 3:
        score += min(0.2, sample_columns * 0.02)
    if numeric_ratio >= 0.6:
        score += 0.2
    if matrix_level in MATRIX_PRIORITY_ORDER:
        score += 0.15
    if any(token in name for token in EXPRESSION_NEGATIVE_HINTS):
        score -= 0.4
    if looks_like_diff_result_columns(columns):
        score -= 0.5
    if sample_columns <= 1:
        score -= 0.2
    return max(0.0, min(1.0, score))


def classify_tabular_matrix(file_path: str) -> Dict[str, object]:
    """Classify whether a tabular file is a matrix, diff table, or metadata-like table."""
    extension = normalize_extension(file_path)
    result: Dict[str, object] = {
        "file_path": file_path,
        "is_expression_matrix": False,
        "matrix_level": MatrixLevel.UNKNOWN.value,
        "value_semantic": ValueSemantic.UNKNOWN.value,
        "columns": [],
        "preview_rows": [],
        "warnings": [],
        "expression_score": 0.0,
    }
    if extension not in TABULAR_EXTENSIONS:
        return result

    preview_rows = _normalize_matrix_rows(_load_preview_rows(file_path))
    columns = preview_rows[0] if preview_rows else []
    result["preview_rows"] = preview_rows
    result["columns"] = columns
    if not preview_rows or len(columns) < 2:
        result["matrix_level"] = MatrixLevel.NON_MATRIX.value
        result["warnings"].append("table preview is too small to classify")
        return result

    matrix_level = _infer_matrix_level(columns, preview_rows)
    sample_columns = _sample_column_count(columns)
    numeric_cells, total_cells = _count_numeric_cells(preview_rows)
    numeric_ratio = (numeric_cells / total_cells) if total_cells else 0.0

    if matrix_level == MatrixLevel.DIFF_RESULT:
        result["matrix_level"] = MatrixLevel.DIFF_RESULT.value
        result["value_semantic"] = ValueSemantic.UNKNOWN.value
    elif sample_columns >= 2 and numeric_ratio >= 0.5:
        result["matrix_level"] = (matrix_level if matrix_level != MatrixLevel.UNKNOWN else MatrixLevel.GENE).value
        result["value_semantic"] = infer_value_semantic_from_preview(preview_rows).value
        result["is_expression_matrix"] = result["matrix_level"] in MATRIX_PRIORITY_ORDER
    else:
        result["matrix_level"] = MatrixLevel.NON_MATRIX.value

    result["expression_score"] = score_expression_candidate(
        {
            "file_path": file_path,
            "columns": columns,
            "preview_rows": preview_rows,
            "matrix_level": result["matrix_level"],
        }
    )
    return result
