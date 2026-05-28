from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


R_DEG_ADAPTER_CONTRACT_SCHEMA_VERSION = "biomedpilot.r_deg_adapter_contract.v1"
R_DEG_RUNTIME_GATE_SCHEMA_VERSION = "biomedpilot.r_deg_runtime_gate.v1"

R_RUNTIME_KEY = "runtime.r.available"
BIOCONDUCTOR_KEY = "runtime.bioconductor.available"
METHOD_PACKAGE_KEYS = {
    "limma": "package.r.limma.available",
    "limma_voom": "package.r.limma.available",
    "deseq2": "package.r.deseq2.available",
    "edger": "package.r.edger.available",
}

METHOD_OUTPUT_SCHEMAS = {
    "limma": {
        "required_columns": ("feature_id", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val"),
        "optional_columns": ("gene_symbol", "B"),
        "p_value_column": "P.Value",
        "fdr_column": "adj.P.Val",
    },
    "limma_voom": {
        "required_columns": ("feature_id", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val"),
        "optional_columns": ("gene_symbol", "B"),
        "p_value_column": "P.Value",
        "fdr_column": "adj.P.Val",
    },
    "deseq2": {
        "required_columns": ("feature_id", "baseMean", "log2FoldChange", "lfcSE", "stat", "pvalue", "padj"),
        "optional_columns": ("gene_symbol",),
        "p_value_column": "pvalue",
        "fdr_column": "padj",
    },
    "edger": {
        "required_columns": ("feature_id", "logFC", "logCPM", "PValue", "FDR"),
        "optional_columns": ("gene_symbol", "LR"),
        "p_value_column": "PValue",
        "fdr_column": "FDR",
    },
}


def build_r_deg_adapter_contract(method: str) -> dict[str, Any]:
    method_key = _method_key(method)
    output_schema = METHOD_OUTPUT_SCHEMAS.get(method_key, {})
    return {
        "schema_version": R_DEG_ADAPTER_CONTRACT_SCHEMA_VERSION,
        "adapter_id": f"r_deg_{method_key}",
        "method": method_key,
        "adapter_semantics": "contract_only_no_r_invocation",
        "method_parameters": _method_parameters(method_key),
        "input_policy": _input_policy(method_key),
        "output_schema": output_schema,
        "dependency_capability_keys": [R_RUNTIME_KEY, BIOCONDUCTOR_KEY, METHOD_PACKAGE_KEYS.get(method_key, "")],
        "dependency_snapshot_required": True,
        "task_run_contract": {
            "must_record": ["manifest", "status", "parameters", "dependency_snapshot", "logs"],
            "must_not_bypass": ["B8 resolver", "B18 multi-factor preflight", "result schema gate"],
        },
        "result_index_contract": {
            "schema": "result_index_v2",
            "required_fields": [
                "result_id",
                "task_run_id",
                "task_type",
                "result_semantics",
                "input_package_id",
                "parameters_manifest",
                "engine_name",
                "engine_version",
                "dependency_snapshot",
                "output_artifacts",
                "validation_status",
                "warnings",
                "blockers",
            ],
            "formal_semantics_policy": "formal_computed_result is allowed only after runtime execution succeeds, output schema validates, dependency snapshot is passed and result index v2 registration succeeds.",
        },
        "result_review_contract": {
            "table_columns_remain_method_specific": True,
            "clinical_interpretation_forbidden": True,
            "plot_or_report_ready_activation": False,
        },
        "graceful_failure_state": {
            "on_missing_runtime": "blocked_no_traceback",
            "on_execution_error": "failed_no_formal_result",
            "on_output_schema_mismatch": "blocked_no_formal_result",
        },
    }


def build_r_deg_runtime_gate(
    *,
    method: str,
    multi_factor_preflight: dict[str, Any] | None,
    external_capabilities: dict[str, Any] | None = None,
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    method_key = _method_key(method)
    contract = build_r_deg_adapter_contract(method_key)
    preflight = multi_factor_preflight if isinstance(multi_factor_preflight, dict) else {}
    capabilities = external_capabilities if isinstance(external_capabilities, dict) else {}
    dep_snapshot = dependency_snapshot if isinstance(dependency_snapshot, dict) else _dependency_snapshot_from_capabilities(capabilities)
    blockers: list[str] = []
    warnings: list[str] = []

    if not capabilities:
        blockers.append("external_engine_capability_registry_missing")
    for key in contract["dependency_capability_keys"]:
        if not key:
            blockers.append(f"unsupported_r_deg_method:{method_key}")
            continue
        capability = capabilities.get(key)
        if _capability_available(capability) is not True:
            blockers.append(f"external_capability_not_available:{key}")

    if preflight.get("status") != "design_ready":
        blockers.extend(_list(preflight.get("blockers")) or ["multi_factor_deg_preflight_not_design_ready"])
    if method_key != str(preflight.get("method") or method_key):
        expected_family = _expected_preflight_family(method_key)
        actual_family = str(preflight.get("method_family") or "")
        if actual_family and actual_family != expected_family:
            blockers.append("r_adapter_method_mismatch_with_preflight")

    if dep_snapshot and str(dep_snapshot.get("status") or "") not in {"passed", "available"}:
        blockers.append("external_dependency_snapshot_not_passed")
    elif not dep_snapshot:
        blockers.append("external_dependency_snapshot_missing")

    blockers = _dedupe(blockers)
    status = "ready_for_external_runtime_execution" if not blockers else "blocked"
    return {
        "schema_version": R_DEG_RUNTIME_GATE_SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "status": status,
        "method": method_key,
        "contract": contract,
        "dependency_snapshot": dep_snapshot,
        "external_capabilities": capabilities,
        "input_preflight_status": str(preflight.get("status") or "missing"),
        "formal_execution_enabled": status == "ready_for_external_runtime_execution",
        "button_activation_policy": "external runtime execution can be shown only when this gate, user confirmation and result schema gate all pass; B19 does not invoke R directly.",
        "writes_result_index": False,
        "result_semantics": "not_executed",
        "blockers": blockers,
        "warnings": warnings,
    }


def build_r_deg_runtime_gate_matrix(
    multi_factor_preflight: dict[str, Any] | None,
    *,
    external_capabilities: dict[str, Any] | None = None,
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gates = {
        method: build_r_deg_runtime_gate(
            method=method,
            multi_factor_preflight=multi_factor_preflight,
            external_capabilities=external_capabilities,
            dependency_snapshot=dependency_snapshot,
        )
        for method in ("limma", "limma_voom", "deseq2", "edger")
    }
    blockers = _dedupe([item for gate in gates.values() for item in gate.get("blockers", []) or []])
    return {
        "schema_version": "biomedpilot.r_deg_runtime_gate_matrix.v1",
        "status": "ready_for_external_runtime_execution" if any(gate["status"] == "ready_for_external_runtime_execution" for gate in gates.values()) else "blocked",
        "gates": gates,
        "blockers": blockers,
        "warnings": [],
    }


def validate_r_deg_output_schema(method: str, columns: list[str] | tuple[str, ...]) -> dict[str, Any]:
    method_key = _method_key(method)
    schema = METHOD_OUTPUT_SCHEMAS.get(method_key)
    blockers: list[str] = []
    if schema is None:
        blockers.append(f"unsupported_r_deg_method:{method_key}")
        return {"status": "blocked", "method": method_key, "blockers": blockers, "warnings": []}
    column_set = {str(column) for column in columns}
    missing = [column for column in schema["required_columns"] if column not in column_set]
    blockers.extend(f"missing_output_column:{column}" for column in missing)
    return {
        "status": "passed" if not blockers else "blocked",
        "method": method_key,
        "required_columns": list(schema["required_columns"]),
        "optional_columns": list(schema["optional_columns"]),
        "p_value_column": schema["p_value_column"],
        "fdr_column": schema["fdr_column"],
        "blockers": blockers,
        "warnings": [],
    }


def validate_r_deg_result_registration_bundle(
    *,
    method: str,
    execution_status: str,
    output_columns: list[str] | tuple[str, ...],
    result_entry: dict[str, Any] | None,
    dependency_snapshot: dict[str, Any] | None,
) -> dict[str, Any]:
    schema_gate = validate_r_deg_output_schema(method, output_columns)
    result = result_entry if isinstance(result_entry, dict) else {}
    dep_snapshot = dependency_snapshot if isinstance(dependency_snapshot, dict) else {}
    blockers = _list(schema_gate.get("blockers"))
    if execution_status != "succeeded":
        blockers.append("r_deg_execution_not_succeeded")
        if result.get("result_semantics") == "formal_computed_result":
            blockers.append("failed_execution_must_not_create_formal_result")
    if not dep_snapshot:
        blockers.append("dependency_snapshot_missing_from_result_provenance")
    elif str(dep_snapshot.get("status") or "") not in {"passed", "available"}:
        blockers.append("dependency_snapshot_not_passed")
    if execution_status == "succeeded":
        if result.get("result_semantics") != "formal_computed_result":
            blockers.append("successful_execution_requires_formal_computed_result_semantics")
        if not result.get("input_package_id"):
            blockers.append("result_index_missing_input_package_id")
        if not result.get("parameters_manifest"):
            blockers.append("result_index_missing_parameters_manifest")
        if not result.get("dependency_snapshot"):
            blockers.append("result_index_missing_dependency_snapshot")
        if str(result.get("validation_status") or "") != "passed":
            blockers.append("result_index_validation_status_not_passed")
    return {
        "status": "passed" if not blockers else "blocked",
        "method": _method_key(method),
        "output_schema_gate": schema_gate,
        "result_semantics_allowed": execution_status == "succeeded" and not blockers,
        "blockers": _dedupe(blockers),
        "warnings": [],
    }


def _method_parameters(method: str) -> dict[str, Any]:
    common = {
        "contrast": "required",
        "design_matrix": "required",
        "fdr_policy": "required",
        "log2fc_threshold": "required",
        "p_value_threshold": "required",
    }
    if method == "deseq2":
        return {**common, "size_factor_estimation": "DESeq2_default", "count_integer_policy": "raw_integer_counts_required"}
    if method == "edger":
        return {**common, "dispersion_policy": "edgeR_default_or_declared", "count_integer_policy": "raw_integer_counts_required"}
    if method == "limma_voom":
        return {**common, "voom_policy": "raw_counts_to_voom_weights", "count_integer_policy": "raw_integer_counts_required"}
    return {**common, "expression_scale_policy": "logged_or_normalized_expression_required"}


def _input_policy(method: str) -> dict[str, Any]:
    if method in {"deseq2", "edger", "limma_voom"}:
        return {
            "accepted_value_types": ["count", "raw_count", "raw_counts", "integer_count"],
            "blocked_value_types": ["TPM", "FPKM", "FPKM-UQ", "normalized", "log_expression"],
            "requires_design_matrix_full_rank": True,
            "requires_gene_level_or_mapped_features": True,
        }
    return {
        "accepted_value_types": ["TPM", "FPKM", "FPKM-UQ", "normalized", "normalized_expression", "log_expression", "log2_transformed"],
        "blocked_value_types": ["unknown", "unmapped_probe_or_ID_REF"],
        "requires_design_matrix_full_rank": True,
        "requires_gene_level_or_mapped_features": True,
    }


def _dependency_snapshot_from_capabilities(capabilities: dict[str, Any]) -> dict[str, Any]:
    if not capabilities:
        return {}
    blockers = [f"external_capability_not_available:{key}" for key, value in capabilities.items() if _capability_available(value) is not True]
    return {
        "schema_version": "biomedpilot.external_engine_dependency_snapshot.v1",
        "status": "blocked" if blockers else "passed",
        "capabilities": capabilities,
        "blockers": blockers,
        "warnings": [],
    }


def _capability_available(value: Any) -> bool | None:
    if isinstance(value, dict):
        if "available" in value:
            return bool(value.get("available"))
        status = str(value.get("status") or "").lower()
        if status in {"available", "passed", "ok", "true"}:
            return True
        if status in {"missing", "blocked", "failed", "not_configured", "false"}:
            return False
    if isinstance(value, bool):
        return value
    return None


def _expected_preflight_family(method: str) -> str:
    if method == "limma":
        return "limma_normalized_expression"
    if method == "limma_voom":
        return "limma_voom_count_model"
    return f"{method}_count_model"


def _method_key(method: str) -> str:
    value = str(method or "").strip().lower().replace("-", "_")
    if value == "edger":
        return "edger"
    return value or "limma"


def _list(values: object) -> list[str]:
    if isinstance(values, (list, tuple, set)):
        return [str(item) for item in values if str(item)]
    if values:
        return [str(values)]
    return []


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
