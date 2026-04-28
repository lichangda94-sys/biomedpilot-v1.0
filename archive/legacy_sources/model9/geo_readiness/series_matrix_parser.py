from __future__ import annotations

import gzip
from pathlib import Path
import re
from typing import Iterable

from geo_readiness.models import SeriesMatrixExpressionReport, SeriesMatrixMetadataReport


_METADATA_FIELDS = {
    "!Sample_title": "title",
    "!Sample_source_name_ch1": "source_name_ch1",
    "!Sample_characteristics_ch1": "characteristics_ch1",
}


def parse_series_matrix_metadata(path_or_text: str | Path) -> SeriesMatrixMetadataReport:
    try:
        text = _read_path_or_text(path_or_text)
    except OSError as exc:
        return SeriesMatrixMetadataReport(errors=["series_matrix_read_failed"], warnings=[str(exc)])

    lines = [line.rstrip("\n\r") for line in text.splitlines()]
    if not any(line.startswith("!Series_") or line.startswith("!Sample_") for line in lines):
        return SeriesMatrixMetadataReport(errors=["series_matrix_metadata_not_found"])

    report = SeriesMatrixMetadataReport()
    metadata_values: dict[str, list[list[str]]] = {}

    for line in lines:
        if line.startswith("!series_matrix_table_begin"):
            break
        key, values = _parse_series_matrix_line(line)
        if not key:
            continue
        if key == "!Series_geo_accession" and values:
            report.gse_id = values[0]
        elif key in {"!Series_platform_id", "!Series_platform_taxid"}:
            report.platform_ids.extend(_unique_platform_values(values))
        elif key == "!Sample_platform_id":
            report.platform_ids.extend(_unique_platform_values(values))
        elif key == "!Sample_geo_accession":
            report.sample_ids = values
        elif key in _METADATA_FIELDS:
            metadata_values.setdefault(_METADATA_FIELDS[key], []).append(values)

    report.platform_ids = _dedupe(report.platform_ids)
    report.sample_count = len(report.sample_ids)
    report.sample_metadata_columns = _metadata_columns(metadata_values)
    report.sample_metadata_rows = _build_sample_metadata_rows(report.sample_ids, metadata_values)
    report.group_hints = _group_hints(report.sample_metadata_rows)

    if not report.gse_id:
        report.warnings.append("series_geo_accession_missing")
    if not report.sample_ids:
        report.errors.append("sample_geo_accession_missing")
    if not report.platform_ids:
        report.warnings.append("platform_id_missing")
    if not report.sample_metadata_rows:
        report.warnings.append("sample_metadata_missing")

    return report


def parse_series_matrix_expression_report(
    path_or_text: str | Path,
    *,
    metadata_sample_ids: list[str] | None = None,
) -> SeriesMatrixExpressionReport:
    try:
        text = _read_path_or_text(path_or_text)
    except OSError as exc:
        return SeriesMatrixExpressionReport(
            errors=["series_matrix_read_failed"],
            warnings=[str(exc)],
        )

    table_lines = _extract_matrix_table_lines(text)
    if not table_lines:
        return SeriesMatrixExpressionReport(
            errors=["series_matrix_table_not_found"],
            numeric_value_status="not_checked",
        )

    header = table_lines[0].split("\t")
    if len(header) < 2:
        return SeriesMatrixExpressionReport(
            errors=["series_matrix_table_header_malformed"],
            numeric_value_status="not_checked",
        )

    feature_id_column = _clean_value(header[0])
    matrix_sample_ids = [_clean_value(value) for value in header[1:] if _clean_value(value)]
    missing_value_count = 0
    negative_value_count = 0
    non_numeric_count = 0
    feature_count = 0

    for line in table_lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        if not parts or not _clean_value(parts[0]):
            continue
        feature_count += 1
        values = parts[1:]
        if len(values) < len(matrix_sample_ids):
            missing_value_count += len(matrix_sample_ids) - len(values)
        for value in values[: len(matrix_sample_ids)]:
            cleaned = _clean_value(value)
            if cleaned == "":
                missing_value_count += 1
                continue
            try:
                numeric = float(cleaned)
            except ValueError:
                non_numeric_count += 1
                continue
            if numeric < 0:
                negative_value_count += 1

    errors: list[str] = []
    warnings: list[str] = []
    if not feature_count:
        errors.append("expression_feature_rows_missing")
    if not matrix_sample_ids:
        errors.append("expression_sample_columns_missing")
    if non_numeric_count:
        errors.append("non_numeric_expression_values")
    if missing_value_count:
        warnings.append("missing_expression_values")
    if negative_value_count:
        warnings.append("negative_expression_values")

    sample_id_match_status = _sample_id_match_status(matrix_sample_ids, metadata_sample_ids)
    if sample_id_match_status == "mismatch":
        errors.append("matrix_metadata_sample_id_mismatch")
    elif sample_id_match_status == "not_checked":
        warnings.append("metadata_sample_ids_not_provided")

    if non_numeric_count:
        numeric_value_status = "non_numeric"
    elif missing_value_count:
        numeric_value_status = "numeric_with_missing"
    else:
        numeric_value_status = "numeric"

    return SeriesMatrixExpressionReport(
        feature_count=feature_count,
        sample_count=len(matrix_sample_ids),
        feature_id_column=feature_id_column,
        matrix_sample_ids=matrix_sample_ids,
        numeric_value_status=numeric_value_status,
        missing_value_count=missing_value_count,
        negative_value_count=negative_value_count,
        sample_id_match_status=sample_id_match_status,
        warnings=warnings,
        errors=errors,
    )


def _read_path_or_text(path_or_text: str | Path) -> str:
    if isinstance(path_or_text, Path):
        return _read_path(path_or_text)
    candidate = Path(path_or_text)
    if "\n" not in path_or_text and candidate.exists():
        return _read_path(candidate)
    return path_or_text


def _read_path(path: Path) -> str:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_matrix_table_lines(text: str) -> list[str]:
    lines: list[str] = []
    in_table = False
    for line in text.splitlines():
        stripped = line.rstrip("\n\r")
        if stripped.startswith("!series_matrix_table_begin"):
            in_table = True
            continue
        if stripped.startswith("!series_matrix_table_end"):
            break
        if in_table:
            lines.append(stripped)
    return lines


def _parse_series_matrix_line(line: str) -> tuple[str, list[str]]:
    if not line.startswith("!"):
        return "", []
    parts = line.split("\t")
    key = parts[0].strip()
    values = [_clean_value(value) for value in parts[1:]]
    values = [value for value in values if value]
    return key, values


def _clean_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        value = value[1:-1]
    return value.strip()


def _unique_platform_values(values: Iterable[str]) -> list[str]:
    platforms: list[str] = []
    for value in values:
        matches = re.findall(r"\bGPL\d+\b", value, flags=re.IGNORECASE)
        platforms.extend(match.upper() for match in matches)
    return platforms


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _metadata_columns(metadata_values: dict[str, list[list[str]]]) -> list[str]:
    columns = ["sample_id"]
    for column in ("title", "source_name_ch1", "characteristics_ch1"):
        if column in metadata_values:
            columns.append(column)
    return columns


def _build_sample_metadata_rows(
    sample_ids: list[str],
    metadata_values: dict[str, list[list[str]]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, sample_id in enumerate(sample_ids):
        row = {"sample_id": sample_id}
        for column, value_sets in metadata_values.items():
            values_for_sample = [
                values[index] for values in value_sets if index < len(values)
            ]
            if values_for_sample:
                row[column] = "; ".join(values_for_sample)
        rows.append(row)
    return rows


def _group_hints(rows: list[dict[str, str]]) -> list[str]:
    hints: list[str] = []
    for row in rows:
        combined = " ".join(
            value for key, value in row.items() if key != "sample_id"
        ).lower()
        if "papillary thyroid carcinoma" in combined or "ptc" in combined:
            hints.append("papillary_thyroid_carcinoma")
        if "normal thyroid" in combined or re.search(r"\bnormal\b", combined):
            hints.append("normal")
        if "anaplastic thyroid carcinoma" in combined or "atc" in combined:
            hints.append("anaplastic_thyroid_carcinoma")
    return _dedupe(hints)


def _sample_id_match_status(
    matrix_sample_ids: list[str],
    metadata_sample_ids: list[str] | None,
) -> str:
    if metadata_sample_ids is None:
        return "not_checked"
    matrix_set = set(matrix_sample_ids)
    metadata_set = set(metadata_sample_ids)
    if matrix_set == metadata_set and len(matrix_sample_ids) == len(metadata_sample_ids):
        return "match"
    return "mismatch"
