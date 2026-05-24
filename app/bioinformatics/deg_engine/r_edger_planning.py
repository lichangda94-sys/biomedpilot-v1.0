from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from .multifactor_gate import COUNT_VALUE_TYPES, DISPLAY_VALUE_TYPES
from .parameter_gate import REQUIRED_PARAMETER_FIELDS
from .r_adapter_contract import build_r_deg_adapter_contract


R_EDGER_PARAMETER_SCHEMA_VERSION = "biomedpilot.r_edger_parameter_manifest.v1"
R_EDGER_ADAPTER_PLAN_SCHEMA_VERSION = "biomedpilot.r_edger_rscript_adapter_plan.v1"
R_EDGER_CONFIRMATION_PATH = Path("manifests") / "r_edger_parameter_confirmation.json"


def load_r_edger_parameter_confirmation(project_root: str | Path) -> dict[str, Any]:
    path = Path(project_root).expanduser().resolve() / R_EDGER_CONFIRMATION_PATH
    if not path.is_file():
        return {}
    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def build_r_edger_parameter_manifest(
    deg_ready_package: Mapping[str, Any],
    *,
    multi_factor_preflight: Mapping[str, Any],
    dependency_snapshot: Mapping[str, Any],
    log2fc_threshold: float = 1.0,
    p_value_threshold: float = 0.05,
    fdr_threshold: float = 0.05,
    minimum_count_filter: int = 10,
    normalization_method: str = "TMM",
    dispersion_policy: str = "estimate_common_trended_tagwise",
    test_method: str = "exact_test",
) -> dict[str, Any]:
    ready = dict(deg_ready_package)
    preflight = dict(multi_factor_preflight)
    dependency = dict(dependency_snapshot)
    contrast = preflight.get("contrast") if isinstance(preflight.get("contrast"), dict) else {}
    matrix_asset = ready.get("matrix_asset") if isinstance(ready.get("matrix_asset"), dict) else {}
    gene_mapping = ready.get("gene_mapping_status") if isinstance(ready.get("gene_mapping_status"), dict) else {}
    alignment = ready.get("sample_alignment_status") if isinstance(ready.get("sample_alignment_status"), dict) else {}
    manifest = {
        "schema_version": R_EDGER_PARAMETER_SCHEMA_VERSION,
        "created_at": _now(),
        "input_package_id": str(preflight.get("input_package_id") or ready.get("source_input_package_id") or ready.get("input_package_id") or ""),
        "deg_ready_package_id": str(preflight.get("deg_ready_package_id") or ready.get("deg_ready_package_id") or ""),
        "comparison_id": str(contrast.get("contrast_id") or "case_vs_control"),
        "case_group": str(contrast.get("case_level") or ""),
        "control_group": str(contrast.get("control_level") or ""),
        "case_samples": list(contrast.get("case_samples", []) or []),
        "control_samples": list(contrast.get("control_samples", []) or []),
        "group_design_source": "manifests/r_limma_design_config.json or manifests/deg_multifactor_design_config.json",
        "method": "edger",
        "method_family": str(preflight.get("method_family") or "edger_count_model"),
        "value_type": str(preflight.get("value_type") or ready.get("value_type") or "unknown"),
        "value_type_policy": str(preflight.get("value_type_policy") or "edger_requires_raw_integer_counts"),
        "gene_id_type": str(preflight.get("gene_id_type") or ready.get("gene_id_type") or "unknown"),
        "gene_mapping_policy": "passed" if gene_mapping.get("status") == "passed" else f"blocked_{gene_mapping.get('status') or 'unknown'}",
        "sample_alignment_policy": "passed" if alignment.get("status") == "passed" else f"blocked_{alignment.get('status') or 'unknown'}",
        "log2fc_threshold": log2fc_threshold,
        "p_value_threshold": p_value_threshold,
        "fdr_threshold": fdr_threshold,
        "fdr_policy": "benjamini_hochberg",
        "pseudocount": 0.0,
        "pseudocount_policy": "not_used_by_edger_count_model",
        "minimum_group_size": 2,
        "minimum_count_filter": minimum_count_filter,
        "normalization_method": normalization_method,
        "dispersion_policy": dispersion_policy,
        "test_method": test_method,
        "count_integer_policy": "raw_integer_counts_required_no_tpm_fpkm_or_log_values",
        "missing_value_policy": "count_matrix_must_be_numeric_integer_complete_or_adapter_fails",
        "multiple_testing_policy": "benjamini_hochberg",
        "engine_candidate": "r_edger_rscript_adapter_planned",
        "dependency_snapshot": dependency,
        "expression_table_path": str(matrix_asset.get("path") or matrix_asset.get("file_path") or ""),
        "sample_group_map": _sample_group_map(preflight),
        "warnings": list(dict.fromkeys([str(item) for item in preflight.get("warnings", []) or []])),
        "blockers": list(dict.fromkeys([str(item) for item in preflight.get("blockers", []) or []])),
    }
    validation = validate_r_edger_parameter_manifest(manifest)
    manifest["blockers"] = list(dict.fromkeys([*manifest["blockers"], *validation["blockers"]]))
    manifest["warnings"] = list(dict.fromkeys([*manifest["warnings"], *validation["warnings"]]))
    manifest["status"] = "blocked" if manifest["blockers"] else "passed"
    manifest["semantic_boundary"] = "r_edger_parameter_gate_only_not_execution"
    return manifest


def validate_r_edger_parameter_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(manifest)
    blockers = [f"missing_field:{field_name}" for field_name in REQUIRED_PARAMETER_FIELDS if field_name not in payload]
    warnings: list[str] = []
    if payload.get("method") != "edger":
        blockers.append("r_edger_parameter_method_not_edger")
    if payload.get("method_family") != "edger_count_model":
        blockers.append("r_edger_method_family_not_count_model")
    if not payload.get("expression_table_path"):
        blockers.append("r_edger_count_table_path_missing")
    if not payload.get("sample_group_map"):
        blockers.append("r_edger_sample_group_map_missing")
    if payload.get("dependency_snapshot", {}).get("status") != "passed":
        blockers.append("r_edger_dependency_snapshot_not_passed")
    value_type = str(payload.get("value_type") or "")
    if value_type in DISPLAY_VALUE_TYPES:
        blockers.append("r_edger_display_value_type_not_allowed")
    if value_type not in COUNT_VALUE_TYPES:
        blockers.append("r_edger_raw_integer_counts_required")
    if not payload.get("case_samples"):
        blockers.append("r_edger_case_samples_missing")
    if not payload.get("control_samples"):
        blockers.append("r_edger_control_samples_missing")
    if payload.get("case_group") == payload.get("control_group"):
        blockers.append("r_edger_case_control_groups_same")
    for field_name in ("log2fc_threshold", "p_value_threshold", "fdr_threshold"):
        try:
            value = float(payload.get(field_name))
        except (TypeError, ValueError):
            blockers.append(f"invalid_threshold:{field_name}")
            continue
        if field_name in {"p_value_threshold", "fdr_threshold"} and not 0 <= value <= 1:
            blockers.append(f"invalid_threshold:{field_name}")
        if field_name == "log2fc_threshold" and value < 0:
            blockers.append(f"invalid_threshold:{field_name}")
    try:
        minimum_count_filter = int(payload.get("minimum_count_filter"))
    except (TypeError, ValueError):
        blockers.append("invalid_minimum_count_filter")
    else:
        if minimum_count_filter < 0:
            blockers.append("invalid_minimum_count_filter")
    if payload.get("normalization_method") not in {"TMM", "RLE", "upperquartile", "none"}:
        blockers.append("invalid_edger_normalization_method")
    if payload.get("dispersion_policy") not in {"estimate_common_trended_tagwise", "common", "trended", "tagwise", "qlf_planned"}:
        blockers.append("invalid_edger_dispersion_policy")
    if payload.get("test_method") not in {"exact_test", "glm_lrt_planned", "glm_qlf_planned"}:
        blockers.append("invalid_edger_test_method")
    blockers.extend(str(item) for item in payload.get("blockers", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": warnings}


def validate_r_edger_parameter_confirmation(
    confirmation: Mapping[str, Any] | None,
    *,
    parameter_manifest: Mapping[str, Any],
    dependency_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = ["b25_12_edger_parameter_confirmation_planning_only"]
    if not confirmation:
        blockers.append("r_edger_parameter_confirmation_missing")
    if parameter_manifest.get("status") != "passed":
        blockers.extend(str(item) for item in parameter_manifest.get("blockers", []) or ["r_edger_parameter_manifest_not_passed"])
    if dependency_snapshot.get("status") != "passed":
        blockers.extend(str(item) for item in dependency_snapshot.get("blockers", []) or ["r_edger_dependency_snapshot_not_passed"])
    return {"status": "blocked", "blockers": list(dict.fromkeys(blockers)), "warnings": []}


def build_r_edger_rscript_adapter_plan(
    *,
    parameter_manifest: Mapping[str, Any],
    runtime_gate: Mapping[str, Any],
    confirmation_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = build_r_deg_adapter_contract("edger")
    blockers = [
        "b25_14_edger_ui_activation_required",
    ]
    if parameter_manifest.get("status") != "passed":
        blockers.extend(parameter_manifest.get("blockers", []) or ["r_edger_parameter_manifest_not_passed"])
    if runtime_gate.get("status") != "ready_for_external_runtime_execution":
        blockers.extend(runtime_gate.get("blockers", []) or ["r_edger_runtime_gate_not_ready"])
    if confirmation_gate and confirmation_gate.get("status") != "passed":
        blockers.extend(confirmation_gate.get("blockers", []) or ["r_edger_confirmation_gate_not_passed"])
    return {
        "schema_version": R_EDGER_ADAPTER_PLAN_SCHEMA_VERSION,
        "created_at": _now(),
        "method": "edger",
        "status": "adapter_available_ui_activation_blocked",
        "adapter_semantics": "controlled_rscript_adapter_available_no_user_ui_execution",
        "formal_execution_enabled": False,
        "can_execute": False,
        "can_register_formal_result": True,
        "writes_result_index": True,
        "result_semantics": "not_executed",
        "command_manifest_contract": {
            "shell": False,
            "required_inputs": ["raw_count_table", "design_table", "contrast", "parameter_manifest", "dependency_snapshot"],
            "required_logs": ["command_manifest", "command_log", "stderr", "stdout"],
            "timeout_policy": "explicit_timeout_required",
        },
        "output_schema": contract["output_schema"],
        "result_index_contract": contract["result_index_contract"],
        "blockers": list(dict.fromkeys(str(item) for item in blockers if str(item))),
        "warnings": ["B25.13 validates the controlled edgeR adapter/runtime path, but user-facing UI activation remains blocked until B25.14."],
    }


def _sample_group_map(preflight: Mapping[str, Any]) -> dict[str, str]:
    contrast = preflight.get("contrast") if isinstance(preflight.get("contrast"), dict) else {}
    assignments: dict[str, str] = {}
    for sample in contrast.get("case_samples", []) or []:
        assignments[str(sample)] = str(contrast.get("case_level") or "")
    for sample in contrast.get("control_samples", []) or []:
        assignments[str(sample)] = str(contrast.get("control_level") or "")
    return assignments


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
