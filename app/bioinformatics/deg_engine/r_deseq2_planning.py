from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from .multifactor_gate import COUNT_VALUE_TYPES, DISPLAY_VALUE_TYPES
from .parameter_gate import REQUIRED_PARAMETER_FIELDS
from .r_adapter_contract import build_r_deg_adapter_contract, validate_r_deg_output_schema, validate_r_deg_result_registration_bundle
from .result_schema import validate_formal_deg_result_index_entry
from app.bioinformatics.results.models import ResultIndexEntry


R_DESEQ2_PARAMETER_SCHEMA_VERSION = "biomedpilot.r_deseq2_parameter_manifest.v1"
R_DESEQ2_CONFIRMATION_SCHEMA_VERSION = "biomedpilot.r_deseq2_parameter_confirmation.v1"
R_DESEQ2_ADAPTER_PLAN_SCHEMA_VERSION = "biomedpilot.r_deseq2_rscript_adapter_plan.v1"
R_DESEQ2_DRY_RUN_ACCEPTANCE_SCHEMA_VERSION = "biomedpilot.r_deseq2_dry_run_acceptance_gate.v1"
R_DESEQ2_CONFIRMATION_PATH = Path("manifests") / "r_deseq2_parameter_confirmation.json"


def load_r_deseq2_parameter_confirmation(project_root: str | Path) -> dict[str, Any]:
    path = Path(project_root).expanduser().resolve() / R_DESEQ2_CONFIRMATION_PATH
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def save_r_deseq2_parameter_confirmation(
    project_root: str | Path,
    *,
    deg_ready_package: Mapping[str, Any],
    multi_factor_preflight: Mapping[str, Any],
    dependency_snapshot: Mapping[str, Any],
    log2fc_threshold: float = 1.0,
    p_value_threshold: float = 0.05,
    fdr_threshold: float = 0.05,
    minimum_count_filter: int = 10,
    size_factor_policy: str = "median_ratio",
    dispersion_fit_type: str = "parametric",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    parameter_manifest = build_r_deseq2_parameter_manifest(
        deg_ready_package,
        multi_factor_preflight=multi_factor_preflight,
        dependency_snapshot=dependency_snapshot,
        log2fc_threshold=log2fc_threshold,
        p_value_threshold=p_value_threshold,
        fdr_threshold=fdr_threshold,
        minimum_count_filter=minimum_count_filter,
        size_factor_policy=size_factor_policy,
        dispersion_fit_type=dispersion_fit_type,
    )
    result_id = f"r-deseq2-{uuid4().hex[:10]}"
    task_run_id = f"task-r-deseq2-{uuid4().hex[:10]}"
    output_plan = {
        "task_run_id": task_run_id,
        "result_id": result_id,
        "result_table_path": f"results/tables/{result_id}.tsv",
        "method_result_table_path": f"results/tables/r_deseq2/{result_id}_deseq2.tsv",
        "task_run_log_path": f"analysis/r_deg/deseq2/{result_id}_run_log.json",
        "command_log_path": f"analysis/r_deg/deseq2_rscript/{task_run_id}/command_log.json",
        "result_index_registry_path": "results/summaries/result_index.json",
    }
    blockers = list(parameter_manifest.get("blockers", []) or [])
    confirmation = {
        "schema_version": R_DESEQ2_CONFIRMATION_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "confirmed",
        "confirmation_semantics": "user_confirmed_r_deseq2_parameters_not_execution",
        "confirmed_by_user": not blockers,
        "parameter_manifest": parameter_manifest,
        "dependency_snapshot": dict(dependency_snapshot),
        "output_plan": output_plan,
        "user_confirmation_summary": build_r_deseq2_confirmation_summary(parameter_manifest, dependency_snapshot, output_plan),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(parameter_manifest.get("warnings", []) or []),
    }
    path = root / R_DESEQ2_CONFIRMATION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(confirmation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return confirmation


def build_r_deseq2_parameter_manifest(
    deg_ready_package: Mapping[str, Any],
    *,
    multi_factor_preflight: Mapping[str, Any],
    dependency_snapshot: Mapping[str, Any],
    log2fc_threshold: float = 1.0,
    p_value_threshold: float = 0.05,
    fdr_threshold: float = 0.05,
    minimum_count_filter: int = 10,
    size_factor_policy: str = "median_ratio",
    dispersion_fit_type: str = "parametric",
) -> dict[str, Any]:
    ready = dict(deg_ready_package)
    preflight = dict(multi_factor_preflight)
    dependency = dict(dependency_snapshot)
    contrast = preflight.get("contrast") if isinstance(preflight.get("contrast"), dict) else {}
    matrix_asset = ready.get("matrix_asset") if isinstance(ready.get("matrix_asset"), dict) else {}
    gene_mapping = ready.get("gene_mapping_status") if isinstance(ready.get("gene_mapping_status"), dict) else {}
    alignment = ready.get("sample_alignment_status") if isinstance(ready.get("sample_alignment_status"), dict) else {}
    manifest = {
        "schema_version": R_DESEQ2_PARAMETER_SCHEMA_VERSION,
        "created_at": _now(),
        "input_package_id": str(preflight.get("input_package_id") or ready.get("source_input_package_id") or ready.get("input_package_id") or ""),
        "deg_ready_package_id": str(preflight.get("deg_ready_package_id") or ready.get("deg_ready_package_id") or ""),
        "comparison_id": str(contrast.get("contrast_id") or "case_vs_control"),
        "case_group": str(contrast.get("case_level") or ""),
        "control_group": str(contrast.get("control_level") or ""),
        "case_samples": list(contrast.get("case_samples", []) or []),
        "control_samples": list(contrast.get("control_samples", []) or []),
        "group_design_source": "manifests/r_limma_design_config.json or manifests/deg_multifactor_design_config.json",
        "method": "deseq2",
        "method_family": str(preflight.get("method_family") or "deseq2_count_model"),
        "value_type": str(preflight.get("value_type") or ready.get("value_type") or "unknown"),
        "value_type_policy": str(preflight.get("value_type_policy") or "deseq2_requires_raw_integer_counts"),
        "gene_id_type": str(preflight.get("gene_id_type") or ready.get("gene_id_type") or "unknown"),
        "gene_mapping_policy": "passed" if gene_mapping.get("status") == "passed" else f"blocked_{gene_mapping.get('status') or 'unknown'}",
        "sample_alignment_policy": "passed" if alignment.get("status") == "passed" else f"blocked_{alignment.get('status') or 'unknown'}",
        "log2fc_threshold": log2fc_threshold,
        "p_value_threshold": p_value_threshold,
        "fdr_threshold": fdr_threshold,
        "fdr_policy": "benjamini_hochberg",
        "pseudocount": 0.0,
        "pseudocount_policy": "not_used_by_deseq2_count_model",
        "minimum_group_size": 2,
        "minimum_count_filter": minimum_count_filter,
        "size_factor_policy": size_factor_policy,
        "dispersion_fit_type": dispersion_fit_type,
        "independent_filtering_policy": "deseq2_default_enabled",
        "cooks_cutoff_policy": "deseq2_default",
        "count_integer_policy": "raw_integer_counts_required_no_tpm_fpkm_or_log_values",
        "missing_value_policy": "count_matrix_must_be_numeric_integer_complete_or_adapter_fails",
        "multiple_testing_policy": "benjamini_hochberg",
        "engine_candidate": "r_deseq2_rscript_adapter_planned",
        "dependency_snapshot": dependency,
        "expression_table_path": str(matrix_asset.get("path") or matrix_asset.get("file_path") or ""),
        "sample_group_map": _sample_group_map(preflight),
        "warnings": list(dict.fromkeys([str(item) for item in preflight.get("warnings", []) or []])),
        "blockers": list(dict.fromkeys([str(item) for item in preflight.get("blockers", []) or []])),
    }
    validation = validate_r_deseq2_parameter_manifest(manifest)
    manifest["blockers"] = list(dict.fromkeys([*manifest["blockers"], *validation["blockers"]]))
    manifest["warnings"] = list(dict.fromkeys([*manifest["warnings"], *validation["warnings"]]))
    manifest["status"] = "blocked" if manifest["blockers"] else "passed"
    manifest["semantic_boundary"] = "r_deseq2_parameter_gate_only_not_execution"
    return manifest


def validate_r_deseq2_parameter_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(manifest)
    blockers = [f"missing_field:{field_name}" for field_name in REQUIRED_PARAMETER_FIELDS if field_name not in payload]
    warnings: list[str] = []
    if payload.get("method") != "deseq2":
        blockers.append("r_deseq2_parameter_method_not_deseq2")
    if payload.get("method_family") != "deseq2_count_model":
        blockers.append("r_deseq2_method_family_not_count_model")
    if not payload.get("expression_table_path"):
        blockers.append("r_deseq2_count_table_path_missing")
    if not payload.get("sample_group_map"):
        blockers.append("r_deseq2_sample_group_map_missing")
    if payload.get("dependency_snapshot", {}).get("status") != "passed":
        blockers.append("r_deseq2_dependency_snapshot_not_passed")
    value_type = str(payload.get("value_type") or "")
    if value_type in DISPLAY_VALUE_TYPES:
        blockers.append("r_deseq2_display_value_type_not_allowed")
    if value_type not in COUNT_VALUE_TYPES:
        blockers.append("r_deseq2_raw_integer_counts_required")
    if not payload.get("case_samples"):
        blockers.append("r_deseq2_case_samples_missing")
    if not payload.get("control_samples"):
        blockers.append("r_deseq2_control_samples_missing")
    if payload.get("case_group") == payload.get("control_group"):
        blockers.append("r_deseq2_case_control_groups_same")
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
    if payload.get("size_factor_policy") not in {"median_ratio", "poscounts", "iterate"}:
        blockers.append("invalid_deseq2_size_factor_policy")
    if payload.get("dispersion_fit_type") not in {"parametric", "local", "mean"}:
        blockers.append("invalid_deseq2_dispersion_fit_type")
    blockers.extend(str(item) for item in payload.get("blockers", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": warnings}


def validate_r_deseq2_parameter_confirmation(
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
        return _gate(["r_deseq2_parameter_confirmation_missing"], warnings)
    if payload.get("schema_version") != R_DESEQ2_CONFIRMATION_SCHEMA_VERSION:
        blockers.append("r_deseq2_parameter_confirmation_schema_mismatch")
    if payload.get("status") != "confirmed" or payload.get("confirmed_by_user") is not True:
        blockers.append("r_deseq2_parameters_not_user_confirmed")
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
        "size_factor_policy",
        "dispersion_fit_type",
        "expression_table_path",
        "sample_group_map",
    ):
        if confirmed_parameters.get(field_name) != current_parameters.get(field_name):
            blockers.append(f"r_deseq2_confirmation_mismatch:{field_name}")
    if confirmed_parameters.get("status") != "passed":
        blockers.append("r_deseq2_confirmation_parameter_manifest_not_passed")
    if confirmed_dependency.get("status") != "passed":
        blockers.append("r_deseq2_confirmation_dependency_not_passed")
    if current_dependency.get("status") != "passed":
        blockers.append("r_deseq2_current_dependency_not_passed")
    for package_name in ("R", "BiocManager", "DESeq2"):
        if _dependency_version(current_dependency, package_name) != _dependency_version(confirmed_dependency, package_name):
            blockers.append(f"r_deseq2_dependency_version_mismatch:{package_name}")
    output_plan = payload.get("output_plan") if isinstance(payload.get("output_plan"), dict) else {}
    for field_name in ("task_run_id", "result_id", "result_table_path", "method_result_table_path", "command_log_path", "result_index_registry_path"):
        if not output_plan.get(field_name):
            blockers.append(f"r_deseq2_confirmation_missing_output_plan:{field_name}")
    return _gate(blockers, warnings)


def build_r_deseq2_rscript_adapter_plan(
    *,
    parameter_manifest: Mapping[str, Any],
    runtime_gate: Mapping[str, Any],
    confirmation_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = build_r_deg_adapter_contract("deseq2")
    parameter = dict(parameter_manifest)
    runtime = dict(runtime_gate)
    confirmation = dict(confirmation_gate or {})
    blockers: list[str] = []
    if parameter.get("status") != "passed":
        blockers.extend(parameter.get("blockers", []) or ["r_deseq2_parameter_manifest_not_passed"])
    if runtime.get("status") != "ready_for_external_runtime_execution":
        blockers.extend(runtime.get("blockers", []) or ["r_deseq2_runtime_gate_not_ready"])
    if confirmation and confirmation.get("status") != "passed":
        blockers.extend(confirmation.get("blockers", []) or ["r_deseq2_confirmation_gate_not_passed"])
    can_execute = not blockers
    return {
        "schema_version": R_DESEQ2_ADAPTER_PLAN_SCHEMA_VERSION,
        "created_at": _now(),
        "method": "deseq2",
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
        "warnings": ["B25.11 allows DESeq2 UI execution only after resolver, raw count design preflight, runtime detection, user confirmation and result-index gates pass."],
    }


def build_r_deseq2_dry_run_acceptance_gate(
    *,
    parameter_manifest: Mapping[str, Any],
    dependency_snapshot: Mapping[str, Any],
    output_rows: list[Mapping[str, Any]] | None = None,
    count_fixture: Mapping[str, Any] | None = None,
    result_id: str = "r-deseq2-dry-run-candidate",
    task_run_id: str = "task-r-deseq2-dry-run-candidate",
    source_dataset_id: str = "deseq2-count-fixture",
    source_repository_manifest: str = "standardized_data/repositories/repository_manifest.json",
) -> dict[str, Any]:
    parameter = dict(parameter_manifest)
    dependency = dict(dependency_snapshot)
    rows = [dict(row) for row in (output_rows or []) if isinstance(row, Mapping)]
    blockers: list[str] = ["b25_8_deseq2_dry_run_only_no_result_index_write"]
    warnings: list[str] = []
    fixture_gate = validate_r_deseq2_count_fixture(count_fixture or {})
    if count_fixture and fixture_gate["status"] != "passed":
        blockers.extend(fixture_gate["blockers"])
    if parameter.get("status") != "passed":
        blockers.extend(parameter.get("blockers", []) or ["r_deseq2_parameter_manifest_not_passed"])
    if dependency.get("status") != "passed":
        blockers.extend(dependency.get("blockers", []) or ["r_deseq2_dependency_snapshot_not_passed"])
    if not rows:
        output_schema_gate = validate_r_deg_output_schema("deseq2", [])
        blockers.append("r_deseq2_dry_run_output_rows_missing")
    else:
        output_schema_gate = validate_r_deg_output_schema("deseq2", list(rows[0].keys()))
    blockers.extend(output_schema_gate.get("blockers", []) or [])

    candidate_entry = _deseq2_candidate_result_index_entry(
        parameter_manifest=parameter,
        dependency_snapshot=dependency,
        result_id=result_id,
        task_run_id=task_run_id,
        source_dataset_id=source_dataset_id,
        source_repository_manifest=source_repository_manifest,
    )
    registration_gate = validate_r_deg_result_registration_bundle(
        method="deseq2",
        execution_status="succeeded" if rows else "dry_run_no_execution",
        output_columns=list(rows[0].keys()) if rows else [],
        result_entry=candidate_entry,
        dependency_snapshot=dependency,
    )
    result_index_gate = validate_formal_deg_result_index_entry(candidate_entry)
    if rows:
        blockers.extend(registration_gate.get("blockers", []) or [])
        blockers.extend(result_index_gate.get("blockers", []) or [])
    dry_run_blockers = list(dict.fromkeys(str(item) for item in blockers if str(item)))
    contract_blockers = [item for item in dry_run_blockers if item != "b25_8_deseq2_dry_run_only_no_result_index_write"]
    return {
        "schema_version": R_DESEQ2_DRY_RUN_ACCEPTANCE_SCHEMA_VERSION,
        "created_at": _now(),
        "method": "deseq2",
        "status": "planned_not_enabled",
        "dry_run_validation_status": "passed" if rows and not contract_blockers else "blocked",
        "formal_execution_enabled": False,
        "can_execute": False,
        "can_register_formal_result": False,
        "writes_result_index": False,
        "result_semantics": "not_executed",
        "count_fixture_gate": fixture_gate,
        "output_schema_gate": output_schema_gate,
        "result_registration_gate": registration_gate,
        "result_index_gate": result_index_gate,
        "candidate_result_index_entry": candidate_entry,
        "blockers": dry_run_blockers,
        "warnings": list(dict.fromkeys(["Dry-run acceptance validates contracts only and must not be registered as a formal DEG result.", *warnings])),
    }


def validate_r_deseq2_count_fixture(fixture: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(fixture or {})
    blockers: list[str] = []
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    sample_ids = [str(item) for item in payload.get("sample_ids", []) or [] if str(item)]
    if not rows:
        blockers.append("r_deseq2_count_fixture_rows_missing")
    if len(sample_ids) < 4:
        blockers.append("r_deseq2_count_fixture_requires_at_least_four_samples")
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            blockers.append(f"count_fixture_row_{index}:not_a_dict")
            continue
        if not row.get("feature_id"):
            blockers.append(f"count_fixture_row_{index}:feature_id_missing")
        for sample_id in sample_ids:
            value = row.get(sample_id)
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                blockers.append(f"count_fixture_row_{index}:non_numeric_count:{sample_id}")
                continue
            if numeric < 0 or numeric != int(numeric):
                blockers.append(f"count_fixture_row_{index}:non_integer_count:{sample_id}")
    return {"status": "passed" if not blockers else "blocked", "blockers": list(dict.fromkeys(blockers)), "warnings": []}


def build_r_deseq2_confirmation_summary(
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
        "method": "deseq2",
        "thresholds": {
            "log2fc_threshold": parameter_manifest.get("log2fc_threshold"),
            "p_value_threshold": parameter_manifest.get("p_value_threshold"),
            "fdr_threshold": parameter_manifest.get("fdr_threshold"),
            "minimum_count_filter": parameter_manifest.get("minimum_count_filter"),
        },
        "count_model_policy": {
            "value_type": parameter_manifest.get("value_type", ""),
            "count_integer_policy": parameter_manifest.get("count_integer_policy", ""),
            "size_factor_policy": parameter_manifest.get("size_factor_policy", ""),
            "dispersion_fit_type": parameter_manifest.get("dispersion_fit_type", ""),
        },
        "dependency_versions": {name: str(status.get("version") or "") for name, status in dependencies.items() if isinstance(status, dict)},
        "output_plan": dict(output_plan),
    }


def _sample_group_map(preflight: Mapping[str, Any]) -> dict[str, str]:
    contrast = preflight.get("contrast") if isinstance(preflight.get("contrast"), dict) else {}
    case_group = str(contrast.get("case_level") or "")
    control_group = str(contrast.get("control_level") or "")
    sample_map: dict[str, str] = {}
    for sample in contrast.get("case_samples", []) or []:
        sample_map[str(sample)] = case_group
    for sample in contrast.get("control_samples", []) or []:
        sample_map[str(sample)] = control_group
    return sample_map


def _deseq2_candidate_result_index_entry(
    *,
    parameter_manifest: Mapping[str, Any],
    dependency_snapshot: Mapping[str, Any],
    result_id: str,
    task_run_id: str,
    source_dataset_id: str,
    source_repository_manifest: str,
) -> dict[str, Any]:
    created_at = _now()
    entry = ResultIndexEntry(
        result_id=result_id,
        task_run_id=task_run_id,
        task_type="deg",
        result_semantics="formal_computed_result",
        input_package_id=str(parameter_manifest.get("input_package_id") or ""),
        source_dataset_id=source_dataset_id,
        source_repository_manifest=source_repository_manifest,
        parameters_manifest=dict(parameter_manifest),
        engine_name="r_deseq2_rscript_adapter",
        engine_version="planned-0.1.0",
        dependency_snapshot=dict(dependency_snapshot),
        output_artifacts=(
            {
                "artifact_id": f"{result_id}-canonical-table",
                "artifact_type": "deg_result_table",
                "path": f"results/tables/{result_id}.tsv",
                "format": "tsv",
                "validation_status": "passed",
            },
            {
                "artifact_id": f"{result_id}-deseq2-table",
                "artifact_type": "deseq2_result_table",
                "path": f"results/tables/r_deseq2/{result_id}_deseq2.tsv",
                "format": "tsv",
                "validation_status": "passed",
            },
        ),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=("r_deseq2_dry_run_candidate_not_registered",),
        blockers=(),
        log_artifacts=(
            {"artifact_type": "r_deseq2_dry_run_acceptance_log", "path": f"analysis/r_deg/deseq2/{result_id}_dry_run_acceptance.json"},
        ),
        failure_reason="",
        created_at=created_at,
        updated_at=created_at,
        schema_version="2.0.0",
        report_ready_eligible=False,
        migration_status="native_v2",
    )
    return entry.to_dict()


def _dependency_version(snapshot: Mapping[str, Any], name: str) -> str:
    dependencies = snapshot.get("dependencies") if isinstance(snapshot.get("dependencies"), dict) else {}
    status = dependencies.get(name) if isinstance(dependencies.get(name), dict) else {}
    return str(status.get("version") or "")


def _gate(blockers: list[str], warnings: list[str]) -> dict[str, Any]:
    return {"status": "passed" if not blockers else "blocked", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
