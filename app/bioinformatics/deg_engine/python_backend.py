from __future__ import annotations

import csv
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dependency_check import check_deg_backend_dependencies
from .models import DEG_ENGINE_NAME, DEG_ENGINE_VERSION, DEG_RESULT_BUNDLE_SCHEMA_VERSION, DEG_RESULT_SCHEMA_VERSION


def run_controlled_deg(
    deg_ready_package: dict[str, Any],
    *,
    case_samples: list[str],
    control_samples: list[str],
    method: str = "welch_t_test",
    dependency_snapshot: dict[str, Any] | None = None,
    log2fc_threshold: float = 1.0,
    adjusted_p_threshold: float = 0.05,
    pseudocount: float = 1e-9,
) -> dict[str, Any]:
    snapshot = dependency_snapshot or check_deg_backend_dependencies()
    if snapshot.get("status") != "passed":
        return _blocked_bundle(deg_ready_package, snapshot, ["deg_dependencies_missing_no_p_values_computed"])
    scipy_stats, multipletests = _import_backends()
    if scipy_stats is None or multipletests is None:
        return _blocked_bundle(deg_ready_package, snapshot, ["deg_backend_import_failed_no_p_values_computed"])
    blockers = [str(item) for item in deg_ready_package.get("blockers", []) or []]
    value_type = str(deg_ready_package.get("value_type") or "")
    gene_mapping = deg_ready_package.get("gene_mapping_status") if isinstance(deg_ready_package.get("gene_mapping_status"), dict) else {}
    if value_type in {"TPM", "FPKM", "FPKM-UQ"} and method in {"count_model", "deseq2", "edger"}:
        blockers.append("display_value_type_not_allowed_for_count_model_deg")
    if gene_mapping.get("status") == "blocked":
        blockers.append("gene_mapping_blocked")
    if blockers:
        return _blocked_bundle(deg_ready_package, snapshot, blockers)
    matrix_asset = deg_ready_package.get("matrix_asset") if isinstance(deg_ready_package.get("matrix_asset"), dict) else {}
    matrix_path = Path(str(matrix_asset.get("path") or matrix_asset.get("file_path") or "")).expanduser()
    header, rows = _read_matrix(matrix_path)
    column_index = {name: index for index, name in enumerate(header)}
    case_indices = [column_index[name] for name in case_samples if name in column_index]
    control_indices = [column_index[name] for name in control_samples if name in column_index]
    if not case_indices or not control_indices:
        return _blocked_bundle(deg_ready_package, snapshot, ["case_control_samples_not_found_in_matrix"])
    result_rows: list[dict[str, Any]] = []
    p_values: list[float] = []
    for row in rows:
        feature_id = str(row[0]).strip()
        case_values = [_float_at(row, index) for index in case_indices]
        control_values = [_float_at(row, index) for index in control_indices]
        case_numeric = [value for value in case_values if value is not None]
        control_numeric = [value for value in control_values if value is not None]
        if len(case_numeric) < 1 or len(control_numeric) < 1:
            continue
        if method == "mann_whitney":
            test = scipy_stats.mannwhitneyu(case_numeric, control_numeric, alternative="two-sided")
        else:
            test = scipy_stats.ttest_ind(case_numeric, control_numeric, equal_var=False, nan_policy="omit")
        p_value = float(test.pvalue)
        p_values.append(p_value)
        case_mean = sum(case_numeric) / len(case_numeric)
        control_mean = sum(control_numeric) / len(control_numeric)
        base_mean = (sum(case_numeric) + sum(control_numeric)) / (len(case_numeric) + len(control_numeric))
        ratio = (case_mean + pseudocount) / (control_mean + pseudocount)
        result_rows.append(
            {
                "feature_id": feature_id,
                "gene_symbol": feature_id,
                "base_mean_or_mean_expression": base_mean,
                "case_mean": case_mean,
                "control_mean": control_mean,
                "log2_fold_change": math.log2(ratio) if ratio > 0 else None,
                "statistic": float(test.statistic),
                "p_value": p_value,
                "adjusted_p_value": None,
                "significance_label": "not_tested",
                "warnings": [],
            }
        )
    adjusted = multipletests(p_values, method="fdr_bh")[1] if p_values else []
    for row, adjusted_p in zip(result_rows, adjusted, strict=False):
        row["adjusted_p_value"] = float(adjusted_p)
        row["significance_label"] = _significance_label(float(row["log2_fold_change"] or 0.0), float(adjusted_p), log2fc_threshold, adjusted_p_threshold)
    return {
        "schema_version": DEG_RESULT_BUNDLE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "passed",
        "result_semantics": "formal_computed_result",
        "engine_name": DEG_ENGINE_NAME,
        "engine_version": DEG_ENGINE_VERSION,
        "method": method,
        "input_package_id": deg_ready_package.get("source_input_package_id") or "",
        "deg_ready_package_id": deg_ready_package.get("deg_ready_package_id") or "",
        "parameters_manifest": {
            "case_samples": case_samples,
            "control_samples": control_samples,
            "method": method,
            "log2fc_threshold": log2fc_threshold,
            "adjusted_p_threshold": adjusted_p_threshold,
            "pseudocount": pseudocount,
        },
        "dependency_snapshot": snapshot,
        "result_table_schema": DEG_RESULT_SCHEMA_VERSION,
        "rows": result_rows,
        "warnings": [],
        "blockers": [],
    }


def _blocked_bundle(deg_ready_package: dict[str, Any], dependency_snapshot: dict[str, Any], blockers: list[str]) -> dict[str, Any]:
    return {
        "schema_version": DEG_RESULT_BUNDLE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked",
        "result_semantics": "blocked",
        "engine_name": DEG_ENGINE_NAME,
        "engine_version": DEG_ENGINE_VERSION,
        "input_package_id": deg_ready_package.get("source_input_package_id") or "",
        "deg_ready_package_id": deg_ready_package.get("deg_ready_package_id") or "",
        "parameters_manifest": {},
        "dependency_snapshot": dependency_snapshot,
        "rows": [],
        "warnings": [],
        "blockers": list(dict.fromkeys(blockers)),
    }


def _import_backends() -> tuple[Any | None, Any | None]:
    try:
        from scipy import stats as scipy_stats  # type: ignore[import-not-found]
        from statsmodels.stats.multitest import multipletests  # type: ignore[import-not-found]
    except Exception:
        return None, None
    return scipy_stats, multipletests


def _read_matrix(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        header = next(csv.reader([first], delimiter=delimiter))
        rows = [[str(cell).strip() for cell in row] for row in csv.reader(handle, delimiter=delimiter) if row]
    return [str(cell).strip() for cell in header], rows


def _float_at(row: list[str], index: int) -> float | None:
    try:
        return float(row[index])
    except (ValueError, IndexError):
        return None


def _significance_label(log2fc: float, adjusted_p: float, log2fc_threshold: float, adjusted_p_threshold: float) -> str:
    if adjusted_p > adjusted_p_threshold or abs(log2fc) < log2fc_threshold:
        return "not_significant"
    return "up" if log2fc > 0 else "down"
