from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any


MULTIFACTOR_DEG_SCHEMA_VERSION = "biomedpilot.deg_multifactor_preflight.v1"
DESIGN_CONFIG_SCHEMA_VERSION = "biomedpilot.deg_multifactor_design_config.v1"

COUNT_VALUE_TYPES = {"count", "raw_count", "raw_counts", "integer_count", "count_like_candidate"}
DISPLAY_VALUE_TYPES = {
    "TPM",
    "FPKM",
    "FPKM-UQ",
    "normalized",
    "normalized_expression",
    "normalized_or_log_expression",
    "log_expression",
    "log2_transformed",
}
COUNT_MODEL_METHODS = {"deseq2", "edger", "edgeR"}


def build_multifactor_deg_preflight_manifest(
    deg_ready_package: dict[str, Any] | None,
    *,
    design_config: dict[str, Any] | None = None,
    method: str = "limma",
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ready = deg_ready_package if isinstance(deg_ready_package, dict) else {}
    config = design_config if isinstance(design_config, dict) else {}
    method_key = _method_key(method)
    value_type = str(ready.get("value_type") or config.get("value_type") or "unknown")
    blockers = _list(ready.get("blockers"))
    warnings = _list(ready.get("warnings"))

    method_family, value_type_policy = _method_policy(method_key, value_type)
    blockers.extend(_value_type_blockers(method_key, value_type, ready))

    design_state = _build_design_state(config)
    blockers.extend(design_state["blockers"])
    warnings.extend(design_state["warnings"])

    dep_snapshot = dependency_snapshot if isinstance(dependency_snapshot, dict) else {}
    if dep_snapshot and str(dep_snapshot.get("status") or "") not in {"passed", "preflight_only", "not_required_for_preflight"}:
        warnings.append("dependency_snapshot_not_passed_but_not_required_for_preflight")

    blockers = _dedupe(blockers)
    warnings = _dedupe(warnings)
    status = "design_ready" if not blockers else "blocked"
    return {
        "schema_version": MULTIFACTOR_DEG_SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "status": status,
        "gate_semantics": "multi_factor_deg_preflight_only_not_execution",
        "result_semantics": "preflight_only",
        "formal_execution_enabled": False,
        "writes_result_index": False,
        "report_ready_eligible": False,
        "input_package_id": str(ready.get("source_input_package_id") or ready.get("input_package_id") or ""),
        "deg_ready_package_id": str(ready.get("deg_ready_package_id") or ""),
        "method": method_key,
        "method_family": method_family,
        "value_type": value_type,
        "value_type_policy": value_type_policy,
        "gene_id_type": str(ready.get("gene_id_type") or config.get("gene_id_type") or "unknown"),
        "design_config": _public_design_config(config),
        "design_matrix": design_state["design_matrix"],
        "contrast": design_state["contrast"],
        "sample_count": design_state["sample_count"],
        "factor_levels": design_state["factor_levels"],
        "rank": design_state["rank"],
        "column_count": design_state["column_count"],
        "dependency_snapshot": dep_snapshot,
        "blockers": blockers,
        "warnings": warnings,
        "next_required_stage": "B19 R adapter or audited external engine contract before any formal multi-factor DEG execution.",
    }


def validate_multifactor_deg_preflight_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    payload = manifest if isinstance(manifest, dict) else {}
    blockers: list[str] = []
    warnings: list[str] = []
    if payload.get("schema_version") != MULTIFACTOR_DEG_SCHEMA_VERSION:
        blockers.append("invalid_multifactor_deg_preflight_schema")
    if payload.get("result_semantics") != "preflight_only":
        blockers.append("multi_factor_preflight_must_not_use_formal_result_semantics")
    if payload.get("formal_execution_enabled") is True:
        blockers.append("multi_factor_preflight_must_not_enable_formal_execution")
    if payload.get("writes_result_index") is True:
        blockers.append("multi_factor_preflight_must_not_write_result_index")
    blockers.extend(_list(payload.get("blockers")))
    if str(payload.get("status") or "") == "design_ready" and blockers:
        blockers.append("design_ready_manifest_contains_blockers")
    if str(payload.get("status") or "") not in {"design_ready", "blocked"}:
        blockers.append("invalid_multifactor_preflight_status")
    return {"status": "passed" if not blockers else "blocked", "blockers": _dedupe(blockers), "warnings": _dedupe(warnings)}


def _build_design_state(config: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if not config:
        return {
            "design_matrix": {"columns": [], "rows": []},
            "contrast": {},
            "sample_count": 0,
            "factor_levels": {},
            "rank": 0,
            "column_count": 0,
            "blockers": ["multi_factor_design_config_missing"],
            "warnings": [],
        }

    rows = config.get("sample_table") if isinstance(config.get("sample_table"), list) else []
    rows = [row for row in rows if isinstance(row, dict)]
    sample_ids = [str(row.get("sample_id") or "").strip() for row in rows]
    sample_count = len([sample for sample in sample_ids if sample])
    if not rows:
        blockers.append("missing_sample_table")
    if sample_count != len(rows) or len(set(sample_ids)) != len(sample_ids):
        blockers.append("invalid_or_duplicate_sample_ids")

    primary_factor = str(config.get("primary_factor") or "group")
    case_group = str(config.get("case_group") or "").strip()
    control_group = str(config.get("control_group") or "").strip()
    if not primary_factor:
        blockers.append("primary_factor_missing")
    if not case_group or not control_group:
        blockers.append("contrast_levels_missing")
    if case_group and control_group and case_group == control_group:
        blockers.append("case_control_groups_must_differ")

    groups = [str(row.get(primary_factor) or "").strip() for row in rows]
    case_samples = [sample for sample, group in zip(sample_ids, groups, strict=False) if sample and group == case_group]
    control_samples = [sample for sample, group in zip(sample_ids, groups, strict=False) if sample and group == control_group]
    if case_group and not case_samples:
        blockers.append("case_group_empty")
    if control_group and not control_samples:
        blockers.append("control_group_empty")

    contrast = config.get("contrast") if isinstance(config.get("contrast"), dict) else {}
    if not contrast:
        blockers.append("contrast_missing")
    elif str(contrast.get("factor") or primary_factor) != primary_factor:
        blockers.append("contrast_factor_mismatch")
    elif str(contrast.get("case_level") or "") != case_group or str(contrast.get("control_level") or "") != control_group:
        blockers.append("contrast_levels_mismatch")

    covariates = _covariates(config)
    matrix, matrix_blockers, matrix_warnings, factor_levels = _design_matrix(rows, primary_factor, covariates)
    blockers.extend(matrix_blockers)
    warnings.extend(matrix_warnings)
    rank = _matrix_rank(matrix["numeric_rows"])
    column_count = len(matrix["columns"])
    if sample_count < max(4, column_count):
        blockers.append("sample_count_insufficient_for_multifactor_design")
    if column_count and rank < column_count:
        blockers.append("design_matrix_not_full_rank")

    return {
        "design_matrix": {"columns": matrix["columns"], "rows": matrix["display_rows"]},
        "contrast": {
            "contrast_id": str(contrast.get("contrast_id") or f"{case_group}_vs_{control_group}"),
            "factor": primary_factor,
            "case_level": case_group,
            "control_level": control_group,
            "case_samples": case_samples,
            "control_samples": control_samples,
        },
        "sample_count": sample_count,
        "factor_levels": factor_levels,
        "rank": rank,
        "column_count": column_count,
        "blockers": blockers,
        "warnings": warnings,
    }


def _design_matrix(rows: list[dict[str, Any]], primary_factor: str, covariates: list[dict[str, str]]) -> tuple[dict[str, Any], list[str], list[str], dict[str, list[str]]]:
    blockers: list[str] = []
    warnings: list[str] = []
    terms = [{"name": primary_factor, "variable_type": "categorical", "role": "primary_factor"}, *covariates]
    columns = ["intercept"]
    encoders: list[tuple[str, str, str | None]] = []
    factor_levels: dict[str, list[str]] = {}

    for term in terms:
        name = term["name"]
        variable_type = term["variable_type"]
        values = [row.get(name) for row in rows]
        if any(value is None or str(value).strip() == "" for value in values):
            blockers.append(f"variable_missing:{name}")
        if variable_type == "categorical":
            levels = sorted({str(value).strip() for value in values if str(value).strip()})
            factor_levels[name] = levels
            if len(levels) < 2:
                blockers.append(f"categorical_variable_has_single_level:{name}")
            for level in levels[1:]:
                columns.append(f"{name}={level}")
                encoders.append((name, "categorical", level))
        elif variable_type == "continuous":
            if not _all_numeric(values):
                blockers.append(f"continuous_variable_non_numeric:{name}")
            columns.append(name)
            encoders.append((name, "continuous", None))
        else:
            blockers.append(f"unsupported_variable_type:{name}:{variable_type}")

    numeric_rows: list[list[float]] = []
    display_rows: list[dict[str, Any]] = []
    for row in rows:
        numeric = [1.0]
        display = {"sample_id": str(row.get("sample_id") or ""), "intercept": 1}
        for name, variable_type, level in encoders:
            if variable_type == "categorical":
                value = 1.0 if str(row.get(name) or "").strip() == level else 0.0
                column = f"{name}={level}"
            else:
                value = _to_float(row.get(name))
                column = name
            numeric.append(value)
            display[column] = int(value) if value in {0.0, 1.0} else value
        numeric_rows.append(numeric)
        display_rows.append(display)
    return {"columns": columns, "numeric_rows": numeric_rows, "display_rows": display_rows}, blockers, warnings, factor_levels


def _covariates(config: dict[str, Any]) -> list[dict[str, str]]:
    values = config.get("covariates") if isinstance(config.get("covariates"), list) else []
    covariates: list[dict[str, str]] = []
    for item in values:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        variable_type = str(item.get("variable_type") or item.get("type") or "categorical").strip().lower()
        if variable_type in {"numeric", "number", "float", "integer"}:
            variable_type = "continuous"
        elif variable_type not in {"categorical", "continuous"}:
            variable_type = "unsupported"
        covariates.append({"name": name, "variable_type": variable_type, "role": str(item.get("role") or "covariate")})
    return covariates


def _method_policy(method_key: str, value_type: str) -> tuple[str, str]:
    if method_key == "limma_voom":
        return "limma_voom_count_model", "limma_voom_requires_raw_integer_counts"
    if method_key == "limma":
        return "limma_normalized_expression", "limma_normalized_expression_requires_logged_or_normalized_values"
    if method_key in {"deseq2", "edger"}:
        return f"{method_key}_count_model", f"{method_key}_requires_raw_integer_counts"
    return "unsupported", f"unsupported_method_for_value_type:{value_type}"


def _value_type_blockers(method_key: str, value_type: str, ready: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if value_type in {"", "unknown"}:
        blockers.append("unknown_value_type_blocks_multifactor_deg")
    count_model_requested = method_key in {"deseq2", "edger", "limma_voom"}
    if count_model_requested and value_type in DISPLAY_VALUE_TYPES:
        blockers.append("count_model_requested_for_display_value_type")
    if count_model_requested and value_type not in COUNT_VALUE_TYPES:
        blockers.append("count_model_requires_count_value_type")
    if method_key in {"deseq2", "edger"} and not _has_count_matrix(ready):
        blockers.append("count_matrix_missing_for_deseq2_or_edger")
    if method_key == "limma_voom" and not _has_count_matrix(ready):
        blockers.append("count_matrix_missing_for_limma_voom")
    if method_key == "limma" and value_type in COUNT_VALUE_TYPES:
        blockers.append("limma_normalized_expression_requires_normalized_or_log_values")
    if method_key == "unsupported":
        blockers.append("unsupported_multifactor_deg_method")
    gene_mapping = ready.get("gene_mapping_status") if isinstance(ready.get("gene_mapping_status"), dict) else {}
    if str(gene_mapping.get("status") or "") == "blocked":
        blockers.append("gene_mapping_not_ready_for_multifactor_deg")
    return blockers


def _has_count_matrix(ready: dict[str, Any]) -> bool:
    matrix = ready.get("matrix_asset") if isinstance(ready.get("matrix_asset"), dict) else {}
    asset_type = str(matrix.get("asset_type") or "").lower()
    path = str(matrix.get("path") or matrix.get("file_path") or "")
    return bool(path) and any(token in asset_type for token in ("count", "raw_count"))


def _public_design_config(config: dict[str, Any]) -> dict[str, Any]:
    if not config:
        return {}
    return {
        "schema_version": str(config.get("schema_version") or DESIGN_CONFIG_SCHEMA_VERSION),
        "primary_factor": str(config.get("primary_factor") or "group"),
        "case_group": str(config.get("case_group") or ""),
        "control_group": str(config.get("control_group") or ""),
        "covariates": _covariates(config),
        "contrast": config.get("contrast") if isinstance(config.get("contrast"), dict) else {},
    }


def _matrix_rank(matrix: list[list[float]]) -> int:
    if not matrix:
        return 0
    work = [list(row) for row in matrix]
    rows = len(work)
    cols = max((len(row) for row in work), default=0)
    rank = 0
    for col in range(cols):
        pivot = None
        for row in range(rank, rows):
            if col < len(work[row]) and abs(work[row][col]) > 1e-10:
                pivot = row
                break
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        pivot_value = work[rank][col]
        work[rank] = [value / pivot_value for value in work[rank]]
        for row in range(rows):
            if row == rank or col >= len(work[row]):
                continue
            factor = work[row][col]
            if abs(factor) <= 1e-10:
                continue
            work[row] = [value - factor * work[rank][idx] for idx, value in enumerate(work[row])]
        rank += 1
        if rank == rows:
            break
    return rank


def _method_key(method: str) -> str:
    value = str(method or "").strip().lower().replace("-", "_")
    if value == "edgeR".lower():
        return "edger"
    return value or "limma"


def _all_numeric(values: list[Any]) -> bool:
    return all(math.isfinite(_to_float(value)) for value in values if value is not None and str(value).strip() != "")


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _list(values: object) -> list[str]:
    if isinstance(values, (list, tuple, set)):
        return [str(item) for item in values if str(item)]
    if values:
        return [str(values)]
    return []


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
