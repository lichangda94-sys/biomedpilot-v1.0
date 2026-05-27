from __future__ import annotations

import csv
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


DEG_DATA_QUALITY_SCHEMA_VERSION = "biomedpilot.deg_data_quality_gate.v1"
COUNT_VALUE_TYPES = {"count", "raw_count", "raw_counts", "count_like_candidate"}


def build_deg_data_quality_gate(
    deg_ready_package: dict[str, Any] | None,
    *,
    aggregation_policy: str = "",
) -> dict[str, Any]:
    ready = deg_ready_package or {}
    matrix_asset = ready.get("matrix_asset") if isinstance(ready.get("matrix_asset"), dict) else {}
    matrix_path = _asset_path(matrix_asset)
    blockers: list[str] = []
    warnings: list[str] = []
    repair: list[str] = []

    if not ready:
        blockers.append("missing_deg_ready_package")
    if ready.get("blockers"):
        blockers.extend(str(item) for item in ready.get("blockers", []) or [])
    if matrix_path is None or not matrix_path.is_file():
        blockers.append("expression_matrix_missing")
        repair.append("Rebuild the standardized expression matrix asset before formal DEG.")
        rows: list[dict[str, Any]] = []
        sample_ids: list[str] = []
    else:
        sample_ids, rows, read_blockers = _read_matrix(matrix_path)
        blockers.extend(read_blockers)

    duplicated_samples = _duplicates(sample_ids)
    if duplicated_samples:
        blockers.append("duplicated_sample_id")
        repair.append("Rename or remove duplicated sample columns and regenerate the standardized input package.")

    feature_ids = [str(row.get("feature_id") or "") for row in rows]
    duplicated_features = _duplicates(feature_ids)
    if duplicated_features and not aggregation_policy:
        blockers.append("duplicated_gene_id_without_aggregation_policy")
        repair.append("Define a reviewed aggregation policy upstream, then regenerate the standardized input package.")
    elif duplicated_features:
        warnings.append("duplicated_gene_id_aggregation_policy_declared")

    value_type = str(ready.get("value_type") or "")
    numeric_values: list[float] = []
    all_zero_features = 0
    zero_variance_features = 0
    low_count_features = 0
    negative_count_features = 0
    missing_value_count = 0
    non_numeric_count = 0
    for row in rows:
        values = row.get("values") if isinstance(row.get("values"), list) else []
        numeric_row: list[float] = []
        row_has_negative = False
        for value in values:
            if value == "":
                missing_value_count += 1
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                non_numeric_count += 1
                continue
            if not math.isfinite(numeric):
                non_numeric_count += 1
                continue
            if numeric < 0:
                row_has_negative = True
            numeric_values.append(numeric)
            numeric_row.append(numeric)
        if numeric_row and all(item == 0 for item in numeric_row):
            all_zero_features += 1
        if len(set(numeric_row)) <= 1 and numeric_row:
            zero_variance_features += 1
        if value_type in COUNT_VALUE_TYPES and numeric_row and sum(numeric_row) < 10:
            low_count_features += 1
        if row_has_negative:
            negative_count_features += 1

    if missing_value_count:
        blockers.append("missing_values_in_expression_matrix")
        repair.append("Handle missing expression values upstream and regenerate the standardized matrix.")
    if non_numeric_count:
        blockers.append("non_numeric_expression_values")
        repair.append("Remove annotation text from numeric expression columns and rebuild the standardized matrix.")
    if negative_count_features and value_type in COUNT_VALUE_TYPES:
        blockers.append("negative_counts_block_count_model")
        repair.append("Counts must be non-negative for DESeq2/edgeR/limma-voom; repair upstream and rebuild the package.")
    elif negative_count_features:
        warnings.append("negative_expression_values_require_review")
    if all_zero_features:
        warnings.append("all_zero_features_present")
    if low_count_features:
        warnings.append("low_count_features_present")
    if zero_variance_features:
        warnings.append("zero_variance_features_present")
    outlier_status = _outlier_status(numeric_values)
    if outlier_status:
        warnings.append(outlier_status)
        repair.append("Review extreme expression outliers before formal DEG; do not mutate formal input in place.")
    mixed_identifier_status = _mixed_identifier_status(feature_ids)
    if mixed_identifier_status:
        warnings.append(mixed_identifier_status)
        repair.append("Normalize mixed feature identifiers upstream before formal DEG if they reflect inconsistent annotation sources.")

    blockers = _dedupe(blockers)
    warnings = _dedupe(warnings)
    return {
        "schema_version": DEG_DATA_QUALITY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "passed",
        "input_package_id": str(ready.get("source_input_package_id") or ready.get("input_package_id") or ""),
        "deg_ready_package_id": str(ready.get("deg_ready_package_id") or ""),
        "matrix_path": str(matrix_path or ""),
        "feature_count": len(rows),
        "sample_count": len(sample_ids),
        "duplicated_gene_ids": duplicated_features[:20],
        "duplicated_sample_ids": duplicated_samples[:20],
        "missing_value_count": missing_value_count,
        "non_numeric_value_count": non_numeric_count,
        "negative_count_feature_count": negative_count_features,
        "all_zero_feature_count": all_zero_features,
        "low_count_feature_count": low_count_features,
        "zero_variance_feature_count": zero_variance_features,
        "blockers": blockers,
        "warnings": warnings,
        "repair_guidance": _dedupe(repair),
        "auto_repaired": False,
        "formal_execution_enabled": False,
        "semantic_boundary": "data_quality_gate_only_not_execution",
    }


def _read_matrix(path: Path) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    try:
        first = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return [], [], ["expression_matrix_empty_or_unreadable"]
    delimiter = "," if first.count(",") > first.count("\t") else "\t"
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        header = next(reader, [])
        sample_ids = [str(cell).strip() for cell in header[1:] if str(cell).strip()]
        for raw in reader:
            if not raw:
                continue
            rows.append({"feature_id": str(raw[0]).strip(), "values": [str(cell).strip() for cell in raw[1:]]})
    return sample_ids, rows, []


def _asset_path(asset: dict[str, Any]) -> Path | None:
    value = str(asset.get("path") or asset.get("file_path") or "")
    return Path(value).expanduser() if value else None


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates


def _outlier_status(values: list[float]) -> str:
    if len(values) < 4:
        return ""
    midpoint = median(values)
    deviations = [abs(value - midpoint) for value in values]
    mad = median(deviations)
    if mad == 0:
        return ""
    return "extreme_expression_outliers_present" if any(abs(value - midpoint) / mad > 20 for value in values) else ""


def _mixed_identifier_status(feature_ids: list[str]) -> str:
    if not feature_ids:
        return ""
    ensembl = sum(1 for item in feature_ids if item.startswith("ENSG"))
    symbols = sum(1 for item in feature_ids if item.isupper() and not item.startswith("ENSG"))
    return "mixed_feature_identifier_patterns_present" if ensembl and symbols else ""


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
