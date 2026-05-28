from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from .multifactor_gate import COUNT_VALUE_TYPES, DISPLAY_VALUE_TYPES
from .parameter_gate import REQUIRED_PARAMETER_FIELDS
from .r_adapter_contract import build_r_deg_adapter_contract


R_EDGER_PARAMETER_SCHEMA_VERSION = "biomedpilot.r_edger_parameter_manifest.v1"
R_EDGER_CONFIRMATION_SCHEMA_VERSION = "biomedpilot.r_edger_parameter_confirmation.v1"
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


def save_r_edger_parameter_confirmation(
    project_root: str | Path,
    *,
    deg_ready_package: Mapping[str, Any],
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
    root = Path(project_root).expanduser().resolve()
    parameter_manifest = build_r_edger_parameter_manifest(
        deg_ready_package,
        multi_factor_preflight=multi_factor_preflight,
        dependency_snapshot=dependency_snapshot,
        log2fc_threshold=log2fc_threshold,
        p_value_threshold=p_value_threshold,
        fdr_threshold=fdr_threshold,
        minimum_count_filter=minimum_count_filter,
        normalization_method=normalization_method,
        dispersion_policy=dispersion_policy,
        test_method=test_method,
    )
    result_id = f"r-edger-{uuid4().hex[:10]}"
    task_run_id = f"task-r-edger-{uuid4().hex[:10]}"
    output_plan = {
        "task_run_id": task_run_id,
        "result_id": result_id,
        "result_table_path": f"results/tables/{result_id}.tsv",
        "method_result_table_path": f"results/tables/r_edger/{result_id}_edger.tsv",
        "task_run_log_path": f"analysis/r_deg/edger/{result_id}_run_log.json",
        "command_log_path": f"analysis/r_deg/edger_rscript/{task_run_id}/command_log.json",
        "result_index_registry_path": "results/summaries/result_index.json",
    }
    blockers = list(parameter_manifest.get("blockers", []) or [])
    confirmation = {
        "schema_version": R_EDGER_CONFIRMATION_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "confirmed",
        "confirmation_semantics": "user_confirmed_r_edger_parameters_not_execution",
        "confirmed_by_user": not blockers,
        "parameter_manifest": parameter_manifest,
        "dependency_snapshot": dict(dependency_snapshot),
        "output_plan": output_plan,
        "user_confirmation_summary": build_r_edger_confirmation_summary(parameter_manifest, dependency_snapshot, output_plan),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(parameter_manifest.get("warnings", []) or []),
    }
    path = root / R_EDGER_CONFIRMATION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(confirmation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return confirmation


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
    resolved_test_method = "glm_lrt" if test_method == "exact_test" and _has_covariates(preflight) else test_method
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
        "test_method": resolved_test_method,
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
    if payload.get("test_method") not in {"exact_test", "glm_lrt", "glm_lrt_planned", "glm_qlf_planned"}:
        blockers.append("invalid_edger_test_method")
    blockers.extend(str(item) for item in payload.get("blockers", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": warnings}


def validate_r_edger_parameter_confirmation(
    confirmation: Mapping[str, Any] | None,
    *,
    parameter_manifest: Mapping[str, Any],
    dependency_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(confirmation or {})
    current_parameters = dict(parameter_manifest)
    current_dependency = dict(dependency_snapshot)
    blockers: list[str] = []
    warnings: list[str] = []
    if not payload:
        return _gate(["r_edger_parameter_confirmation_missing"], warnings)
    if payload.get("schema_version") != R_EDGER_CONFIRMATION_SCHEMA_VERSION:
        blockers.append("r_edger_parameter_confirmation_schema_mismatch")
    if payload.get("status") != "confirmed" or payload.get("confirmed_by_user") is not True:
        blockers.append("r_edger_parameters_not_user_confirmed")
    confirmed_parameters = payload.get("parameter_manifest") if isinstance(payload.get("parameter_manifest"), dict) else {}
    confirmed_dependency = payload.get("dependency_snapshot") if isinstance(payload.get("dependency_snapshot"), dict) else {}
    for field_name in (
        "input_package_id",
        "deg_ready_package_id",
        "comparison_id",
        "case_group",
        "control_group",
        "case_samples",
        "control_samples",
        "method",
        "method_family",
        "value_type",
        "value_type_policy",
        "gene_id_type",
        "gene_mapping_policy",
        "sample_alignment_policy",
        "log2fc_threshold",
        "p_value_threshold",
        "fdr_threshold",
        "fdr_policy",
        "multiple_testing_policy",
        "minimum_count_filter",
        "normalization_method",
        "dispersion_policy",
        "test_method",
        "expression_table_path",
        "sample_group_map",
    ):
        if confirmed_parameters.get(field_name) != current_parameters.get(field_name):
            blockers.append(f"r_edger_confirmation_mismatch:{field_name}")
    if confirmed_parameters.get("status") != "passed":
        blockers.append("r_edger_confirmation_parameter_manifest_not_passed")
    if confirmed_dependency.get("status") != "passed":
        blockers.append("r_edger_confirmation_dependency_not_passed")
    if parameter_manifest.get("status") != "passed":
        blockers.extend(str(item) for item in parameter_manifest.get("blockers", []) or ["r_edger_parameter_manifest_not_passed"])
    if dependency_snapshot.get("status") != "passed":
        blockers.extend(str(item) for item in dependency_snapshot.get("blockers", []) or ["r_edger_dependency_snapshot_not_passed"])
    for package_name in ("R", "BiocManager", "edgeR"):
        if _dependency_version(current_dependency, package_name) != _dependency_version(confirmed_dependency, package_name):
            blockers.append(f"r_edger_dependency_version_mismatch:{package_name}")
    output_plan = payload.get("output_plan") if isinstance(payload.get("output_plan"), dict) else {}
    for field_name in ("task_run_id", "result_id", "result_table_path", "method_result_table_path", "command_log_path", "result_index_registry_path"):
        if not output_plan.get(field_name):
            blockers.append(f"r_edger_confirmation_missing_output_plan:{field_name}")
    return _gate(blockers, warnings)


def build_r_edger_rscript_adapter_plan(
    *,
    parameter_manifest: Mapping[str, Any],
    runtime_gate: Mapping[str, Any],
    confirmation_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = build_r_deg_adapter_contract("edger")
    blockers: list[Any] = []
    if parameter_manifest.get("status") != "passed":
        blockers.extend(parameter_manifest.get("blockers", []) or ["r_edger_parameter_manifest_not_passed"])
    if runtime_gate.get("status") != "ready_for_external_runtime_execution":
        blockers.extend(runtime_gate.get("blockers", []) or ["r_edger_runtime_gate_not_ready"])
    if confirmation_gate and confirmation_gate.get("status") != "passed":
        blockers.extend(confirmation_gate.get("blockers", []) or ["r_edger_confirmation_gate_not_passed"])
    can_execute = not blockers
    return {
        "schema_version": R_EDGER_ADAPTER_PLAN_SCHEMA_VERSION,
        "created_at": _now(),
        "method": "edger",
        "status": "ready_for_ui_execution" if can_execute else "blocked",
        "adapter_semantics": "controlled_rscript_adapter_available_gated_ui_execution",
        "formal_execution_enabled": can_execute,
        "can_execute": can_execute,
        "can_register_formal_result": can_execute,
        "writes_result_index": can_execute,
        "result_semantics": "formal_computed_result_when_run" if can_execute else "not_executed",
        "command_manifest_contract": {
            "shell": False,
            "required_inputs": ["raw_count_table", "design_table", "contrast", "parameter_manifest", "dependency_snapshot"],
            "required_logs": ["command_manifest", "command_log", "stderr", "stdout"],
            "timeout_policy": "explicit_timeout_required",
        },
        "output_schema": contract["output_schema"],
        "result_index_contract": contract["result_index_contract"],
        "blockers": list(dict.fromkeys(str(item) for item in blockers if str(item))),
        "warnings": ["B25.14 allows edgeR UI execution only after resolver, raw count design preflight, runtime detection, user confirmation and result-index gates pass."],
    }


def build_r_edger_confirmation_summary(
    parameter_manifest: Mapping[str, Any],
    dependency_snapshot: Mapping[str, Any],
    output_plan: Mapping[str, Any],
) -> dict[str, Any]:
    dependencies = dependency_snapshot.get("dependencies") if isinstance(dependency_snapshot.get("dependencies"), dict) else {}
    return {
        "comparison": {
            "comparison_id": parameter_manifest.get("comparison_id", ""),
            "case_group": parameter_manifest.get("case_group", ""),
            "control_group": parameter_manifest.get("control_group", ""),
            "case_sample_count": len(parameter_manifest.get("case_samples", []) or []),
            "control_sample_count": len(parameter_manifest.get("control_samples", []) or []),
            "case_samples": list(parameter_manifest.get("case_samples", []) or []),
            "control_samples": list(parameter_manifest.get("control_samples", []) or []),
        },
        "method": "edger",
        "thresholds": {
            "log2fc_threshold": parameter_manifest.get("log2fc_threshold"),
            "p_value_threshold": parameter_manifest.get("p_value_threshold"),
            "fdr_threshold": parameter_manifest.get("fdr_threshold"),
            "minimum_count_filter": parameter_manifest.get("minimum_count_filter"),
        },
        "count_model_policy": {
            "value_type": parameter_manifest.get("value_type", ""),
            "count_integer_policy": parameter_manifest.get("count_integer_policy", ""),
            "normalization_method": parameter_manifest.get("normalization_method", ""),
            "dispersion_policy": parameter_manifest.get("dispersion_policy", ""),
            "test_method": parameter_manifest.get("test_method", ""),
        },
        "dependency_versions": {name: str(status.get("version") or "") for name, status in dependencies.items() if isinstance(status, dict)},
        "output_plan": dict(output_plan),
    }


def _sample_group_map(preflight: Mapping[str, Any]) -> dict[str, str]:
    contrast = preflight.get("contrast") if isinstance(preflight.get("contrast"), dict) else {}
    assignments: dict[str, str] = {}
    for sample in contrast.get("case_samples", []) or []:
        assignments[str(sample)] = str(contrast.get("case_level") or "")
    for sample in contrast.get("control_samples", []) or []:
        assignments[str(sample)] = str(contrast.get("control_level") or "")
    return assignments


def _has_covariates(preflight: Mapping[str, Any]) -> bool:
    design_config = preflight.get("design_config") if isinstance(preflight.get("design_config"), dict) else {}
    return bool(design_config.get("covariates"))


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _dependency_version(snapshot: Mapping[str, Any], name: str) -> str:
    dependencies = snapshot.get("dependencies") if isinstance(snapshot.get("dependencies"), dict) else {}
    status = dependencies.get(name) if isinstance(dependencies.get(name), dict) else {}
    return str(status.get("version") or "")


def _gate(blockers: list[str], warnings: list[str]) -> dict[str, Any]:
    return {"status": "passed" if not blockers else "blocked", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}
