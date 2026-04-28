from __future__ import annotations

import gzip
from pathlib import Path
import re
from typing import Iterable

from geo_readiness.models import (
    PlatformAnnotationMappingReport,
    SeriesMatrixExpressionReport,
    SeriesMatrixMetadataReport,
)
from geo_readiness.platform_annotation_parser import parse_platform_annotation_mapping_report


def parse_geo_soft_metadata(path_or_text: str | Path) -> SeriesMatrixMetadataReport:
    try:
        text = _read_path_or_text(path_or_text)
    except OSError as exc:
        return SeriesMatrixMetadataReport(errors=["geo_soft_read_failed"], warnings=[str(exc)])

    lines = [line.rstrip("\n\r") for line in text.splitlines()]
    if not any(line.startswith("^SERIES") or line.startswith("^SAMPLE") for line in lines):
        return SeriesMatrixMetadataReport(errors=["geo_soft_metadata_not_found"])

    report = SeriesMatrixMetadataReport()
    sample_rows: list[dict[str, str]] = []
    current_sample: dict[str, str] | None = None
    current_characteristics: list[str] = []
    in_sample_table = False
    series_sample_ids: list[str] = []

    for line in lines:
        if line.startswith("^SAMPLE"):
            _finalize_sample(sample_rows, current_sample, current_characteristics)
            current_sample = {"sample_id": _value_after_equals(line)}
            current_characteristics = []
            in_sample_table = False
            continue
        if line.startswith("^") and not line.startswith("^SAMPLE"):
            _finalize_sample(sample_rows, current_sample, current_characteristics)
            current_sample = None
            current_characteristics = []
            in_sample_table = False

        if line.startswith("!sample_table_begin"):
            in_sample_table = True
            continue
        if line.startswith("!sample_table_end"):
            in_sample_table = False
            continue
        if in_sample_table:
            continue

        key, value = _parse_soft_line(line)
        if not key:
            continue
        if key == "!Series_geo_accession":
            report.gse_id = value
        elif key == "!Series_platform_id":
            report.platform_ids.extend(_unique_platform_values([value]))
        elif key == "!Series_sample_id":
            series_sample_ids.append(value)
        elif key == "!Sample_geo_accession" and current_sample is not None:
            current_sample["sample_id"] = value
        elif key == "!Sample_title" and current_sample is not None:
            current_sample["title"] = value
        elif key == "!Sample_source_name_ch1" and current_sample is not None:
            current_sample["source_name_ch1"] = value
        elif key == "!Sample_characteristics_ch1" and current_sample is not None:
            current_characteristics.append(value)
        elif key == "!Sample_platform_id" and current_sample is not None:
            report.platform_ids.extend(_unique_platform_values([value]))

    _finalize_sample(sample_rows, current_sample, current_characteristics)

    report.platform_ids = _dedupe(report.platform_ids)
    report.sample_metadata_rows = sample_rows
    report.sample_ids = [
        row.get("sample_id", "") for row in sample_rows if row.get("sample_id")
    ] or series_sample_ids
    report.sample_count = len(report.sample_ids)
    report.sample_metadata_columns = _metadata_columns(sample_rows)
    report.group_hints = _group_hints(sample_rows)

    if not report.gse_id:
        report.warnings.append("series_geo_accession_missing")
    if not report.sample_ids:
        report.errors.append("sample_geo_accession_missing")
    if not report.platform_ids:
        report.warnings.append("platform_id_missing")
    if not report.sample_metadata_rows:
        report.warnings.append("sample_metadata_missing")
    elif series_sample_ids and len(series_sample_ids) != len(report.sample_metadata_rows):
        report.warnings.append("series_sample_id_count_mismatch")

    return report


def parse_geo_soft_expression_report(
    path_or_text: str | Path,
    *,
    metadata_sample_ids: list[str] | None = None,
) -> SeriesMatrixExpressionReport:
    try:
        text = _read_path_or_text(path_or_text)
    except OSError as exc:
        return SeriesMatrixExpressionReport(
            errors=["geo_soft_read_failed"],
            warnings=[str(exc)],
            numeric_value_status="not_checked",
        )

    current_sample_id = ""
    in_sample_table = False
    header: list[str] = []
    feature_column_index = -1
    value_column_index = -1
    current_feature_ids: list[str] = []
    first_feature_ids: list[str] | None = None
    matrix_sample_ids: list[str] = []
    feature_id_column = ""
    missing_value_count = 0
    negative_value_count = 0
    non_numeric_count = 0
    malformed_table_count = 0
    feature_mismatch_count = 0

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n\r")
        if line.startswith("^SAMPLE"):
            current_sample_id = _value_after_equals(line)
            continue
        key, value = _parse_soft_line(line)
        if key == "!Sample_geo_accession":
            current_sample_id = value
            continue
        if line.startswith("!sample_table_begin"):
            in_sample_table = True
            header = []
            feature_column_index = -1
            value_column_index = -1
            current_feature_ids = []
            continue
        if line.startswith("!sample_table_end"):
            in_sample_table = False
            if feature_column_index < 0 or value_column_index < 0:
                malformed_table_count += 1
                continue
            if current_sample_id:
                matrix_sample_ids.append(current_sample_id)
            if first_feature_ids is None:
                first_feature_ids = list(current_feature_ids)
            elif set(first_feature_ids) != set(current_feature_ids):
                feature_mismatch_count += 1
            continue
        if not in_sample_table:
            continue
        if not header:
            header = line.split("\t")
            feature_column_index = _find_column_index(header, ("id_ref", "id", "probe_id"))
            value_column_index = _find_column_index(header, ("value", "signal", "expression"))
            if feature_column_index >= 0:
                feature_id_column = header[feature_column_index].strip()
            continue

        parts = line.split("\t")
        if feature_column_index >= len(parts):
            missing_value_count += 1
            continue
        feature_id = parts[feature_column_index].strip().strip('"')
        if not feature_id:
            continue
        current_feature_ids.append(feature_id)
        if value_column_index >= len(parts):
            missing_value_count += 1
            continue
        cleaned_value = parts[value_column_index].strip().strip('"')
        if cleaned_value == "":
            missing_value_count += 1
            continue
        try:
            numeric_value = float(cleaned_value)
        except ValueError:
            non_numeric_count += 1
            continue
        if numeric_value < 0:
            negative_value_count += 1

    errors: list[str] = []
    warnings: list[str] = []
    if not matrix_sample_ids:
        errors.append("geo_soft_sample_table_not_found")
    if malformed_table_count:
        errors.append("geo_soft_sample_table_header_malformed")
    if feature_mismatch_count:
        errors.append("geo_soft_sample_table_feature_mismatch")
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
    elif matrix_sample_ids:
        numeric_value_status = "numeric"
    else:
        numeric_value_status = "not_checked"

    return SeriesMatrixExpressionReport(
        feature_count=len(first_feature_ids or []),
        sample_count=len(matrix_sample_ids),
        feature_id_column=feature_id_column,
        matrix_sample_ids=matrix_sample_ids,
        numeric_value_status=numeric_value_status,
        missing_value_count=missing_value_count,
        negative_value_count=negative_value_count,
        sample_id_match_status=sample_id_match_status,
        warnings=warnings,
        errors=_dedupe(errors),
    )


def parse_geo_soft_platform_mapping_report(
    path_or_text: str | Path,
    *,
    platform_id: str = "",
    minimum_success_rate: float = 0.8,
) -> PlatformAnnotationMappingReport:
    try:
        text = _read_path_or_text(path_or_text)
    except OSError as exc:
        return PlatformAnnotationMappingReport(
            platform_id=platform_id,
            errors=["geo_soft_read_failed"],
            warnings=[str(exc)],
        )

    table_text = _extract_platform_table_text(text)
    if not table_text:
        return PlatformAnnotationMappingReport(
            platform_id=platform_id,
            errors=["geo_soft_platform_table_not_found"],
        )
    resolved_platform_id = platform_id or _extract_platform_id(text)
    return parse_platform_annotation_mapping_report(
        table_text,
        platform_id=resolved_platform_id,
        minimum_success_rate=minimum_success_rate,
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


def _extract_platform_table_text(text: str) -> str:
    lines: list[str] = []
    in_table = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n\r")
        if line.startswith("!platform_table_begin"):
            in_table = True
            continue
        if line.startswith("!platform_table_end"):
            break
        if in_table:
            lines.append(line)
    return "\n".join(lines)


def _extract_platform_id(text: str) -> str:
    for line in text.splitlines():
        key, value = _parse_soft_line(line.rstrip("\n\r"))
        if key in {"!Platform_geo_accession", "!Series_platform_id", "!Sample_platform_id"}:
            platforms = _unique_platform_values([value])
            if platforms:
                return platforms[0]
    return ""


def _parse_soft_line(line: str) -> tuple[str, str]:
    if not line.startswith("!") or "=" not in line:
        return "", ""
    key, value = line.split("=", 1)
    return key.strip(), value.strip()


def _value_after_equals(line: str) -> str:
    if "=" not in line:
        return ""
    return line.split("=", 1)[1].strip()


def _finalize_sample(
    rows: list[dict[str, str]],
    current_sample: dict[str, str] | None,
    characteristics: list[str],
) -> None:
    if current_sample is None:
        return
    if characteristics:
        current_sample["characteristics_ch1"] = "; ".join(characteristics)
    if current_sample.get("sample_id"):
        rows.append(dict(current_sample))


def _metadata_columns(rows: list[dict[str, str]]) -> list[str]:
    columns = ["sample_id"]
    for column in ("title", "source_name_ch1", "characteristics_ch1"):
        if any(row.get(column) for row in rows):
            columns.append(column)
    return columns


def _find_column_index(columns: list[str], aliases: tuple[str, ...]) -> int:
    normalized_aliases = {_normalize_header(alias) for alias in aliases}
    for index, column in enumerate(columns):
        if _normalize_header(column) in normalized_aliases:
            return index
    return -1


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _unique_platform_values(values: Iterable[str]) -> list[str]:
    platforms: list[str] = []
    for value in values:
        platforms.extend(
            match.upper()
            for match in re.findall(r"\bGPL\d+\b", value, flags=re.IGNORECASE)
        )
    return platforms


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


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
        if "follicular thyroid carcinoma" in combined:
            hints.append("follicular_thyroid_carcinoma")
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
