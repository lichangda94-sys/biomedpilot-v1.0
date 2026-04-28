from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
import re

from geo_readiness.models import PlatformAnnotationMappingReport


_PROBE_COLUMNS = (
    "id",
    "id_ref",
    "probe set id",
    "probe_id",
    "probe id",
)
_SYMBOL_COLUMNS = (
    "gene symbol",
    "gene_symbol",
    "symbol",
    "gene symbols",
)
_EMPTY_SYMBOLS = {"", "---", "na", "n/a", "null", "none", "nan"}


def parse_platform_annotation_mapping_report(
    path_or_text: str | Path,
    *,
    platform_id: str = "GPL570",
    minimum_success_rate: float = 0.8,
) -> PlatformAnnotationMappingReport:
    try:
        text = _read_path_or_text(path_or_text)
    except OSError as exc:
        return PlatformAnnotationMappingReport(
            platform_id=platform_id,
            errors=["platform_annotation_read_failed"],
            warnings=[str(exc)],
        )

    if not text.strip():
        return PlatformAnnotationMappingReport(
            platform_id=platform_id,
            errors=["platform_annotation_empty"],
        )

    table_text, delimiter = _extract_table_text(text)
    if not table_text:
        return PlatformAnnotationMappingReport(
            platform_id=platform_id,
            errors=["platform_annotation_header_missing"],
        )

    rows = list(csv.DictReader(StringIO(table_text), delimiter=delimiter))
    if not rows:
        return PlatformAnnotationMappingReport(
            platform_id=platform_id,
            errors=["platform_annotation_rows_missing"],
        )

    fieldnames = rows[0].keys()
    probe_column = _find_column(fieldnames, _PROBE_COLUMNS)
    symbol_column = _find_column(fieldnames, _SYMBOL_COLUMNS)
    if not probe_column or not symbol_column:
        errors = []
        if not probe_column:
            errors.append("probe_id_column_missing")
        if not symbol_column:
            errors.append("gene_symbol_column_missing")
        return PlatformAnnotationMappingReport(platform_id=platform_id, errors=errors)

    probe_count = 0
    mapped_symbols: list[str] = []
    unmapped_probe_count = 0
    multi_symbol_cells = 0
    for row in rows:
        probe_id = str(row.get(probe_column, "")).strip()
        if not probe_id:
            continue
        probe_count += 1
        symbol, had_multiple = _normalize_symbol(str(row.get(symbol_column, "")))
        if had_multiple:
            multi_symbol_cells += 1
        if symbol:
            mapped_symbols.append(symbol)
        else:
            unmapped_probe_count += 1

    mapped_probe_count = len(mapped_symbols)
    success_rate = (mapped_probe_count / probe_count) if probe_count else 0.0
    duplicated_symbol_count = _duplicated_count(mapped_symbols)
    warnings: list[str] = []
    errors: list[str] = []
    if multi_symbol_cells:
        warnings.append("multi_symbol_cells_collapsed_to_first")
    if duplicated_symbol_count:
        warnings.append("duplicated_symbols_detected")
    if not probe_count:
        errors.append("probe_rows_missing")
    if success_rate < minimum_success_rate:
        errors.append("mapping_success_rate_too_low")

    return PlatformAnnotationMappingReport(
        platform_id=platform_id,
        probe_count=probe_count,
        mapped_probe_count=mapped_probe_count,
        unmapped_probe_count=unmapped_probe_count,
        duplicated_symbol_count=duplicated_symbol_count,
        mapping_success_rate=round(success_rate, 4),
        acceptable=not errors,
        warnings=warnings,
        errors=errors,
    )


def _read_path_or_text(path_or_text: str | Path) -> str:
    if isinstance(path_or_text, Path):
        return path_or_text.read_text(encoding="utf-8", errors="replace")
    if "\n" not in path_or_text:
        candidate = Path(path_or_text)
        if candidate.exists():
            return candidate.read_text(encoding="utf-8", errors="replace")
    return path_or_text


def _extract_table_text(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        delimiter = _detect_delimiter(line)
        columns = next(csv.reader([line], delimiter=delimiter), [])
        if _find_column(columns, _PROBE_COLUMNS) and _find_column(columns, _SYMBOL_COLUMNS):
            table_lines = [
                candidate
                for candidate in lines[index:]
                if candidate.strip() and not candidate.lstrip().startswith("#")
            ]
            return "\n".join(table_lines), delimiter
    return "", ","


def _detect_delimiter(line: str) -> str:
    return "\t" if line.count("\t") >= line.count(",") else ","


def _find_column(columns, aliases: tuple[str, ...]) -> str:
    normalized_aliases = {_normalize_header(alias) for alias in aliases}
    for column in columns:
        if _normalize_header(str(column)) in normalized_aliases:
            return str(column)
    return ""


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _normalize_symbol(value: str) -> tuple[str, bool]:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] == '"':
        cleaned = cleaned[1:-1].strip()
    if cleaned.lower() in _EMPTY_SYMBOLS:
        return "", False
    parts = [part.strip() for part in re.split(r"///|//|;|,", cleaned) if part.strip()]
    if not parts:
        return "", False
    first = parts[0]
    if first.lower() in _EMPTY_SYMBOLS:
        return "", len(parts) > 1
    return first, len(parts) > 1


def _duplicated_count(values: list[str]) -> int:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)
