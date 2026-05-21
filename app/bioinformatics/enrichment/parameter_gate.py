from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .models import ALLOWED_ORA_TEST_METHODS, ORA_PARAMETER_SCHEMA_VERSION


def build_ora_parameter_manifest(
    ora_input: dict[str, Any] | None,
    gene_set_resource: dict[str, Any] | None,
    *,
    selected_gene_rule: str = "adjusted_p_value_and_abs_log2fc",
    background_universe_rule: str = "source_deg_detected_genes",
    min_gene_set_size: int = 10,
    max_gene_set_size: int = 500,
    p_value_threshold: float = 0.05,
    fdr_threshold: float = 0.05,
    multiple_testing_policy: str = "BH",
    test_method: str = "hypergeometric",
    gene_id_policy: str = "require_matching_gene_id_or_mapping",
    species_policy: str = "require_match_when_known",
) -> dict[str, Any]:
    manifest = {
        "schema_version": ORA_PARAMETER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ora_parameter_id": f"ora_parameters_{uuid4().hex[:12]}",
        "ora_input_id": str((ora_input or {}).get("ora_input_id") or ""),
        "gene_set_resource_id": str((gene_set_resource or {}).get("gene_set_resource_id") or ""),
        "source_result_id": str((ora_input or {}).get("source_result_id") or ""),
        "source_result_semantics": str((ora_input or {}).get("source_result_semantics") or ""),
        "selected_gene_rule": selected_gene_rule,
        "background_universe_rule": background_universe_rule,
        "min_gene_set_size": min_gene_set_size,
        "max_gene_set_size": max_gene_set_size,
        "p_value_threshold": p_value_threshold,
        "fdr_threshold": fdr_threshold,
        "multiple_testing_policy": multiple_testing_policy,
        "test_method": test_method,
        "gene_id_policy": gene_id_policy,
        "species_policy": species_policy,
        "warnings": [],
        "blockers": [],
    }
    validation = validate_ora_parameter_manifest(manifest, ora_input=ora_input, gene_set_resource=gene_set_resource)
    manifest["warnings"] = validation["warnings"]
    manifest["blockers"] = validation["blockers"]
    manifest["status"] = validation["status"]
    return manifest


def validate_ora_parameter_manifest(
    manifest: dict[str, Any],
    *,
    ora_input: dict[str, Any] | None = None,
    gene_set_resource: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    ora_input = ora_input or {}
    gene_set_resource = gene_set_resource or {}
    if not manifest.get("source_result_id"):
        blockers.append("ora_parameter_missing_source_result")
    if str(ora_input.get("source_task_type") or "") != "deg":
        blockers.append("ora_parameter_source_result_not_deg")
    if str(ora_input.get("source_result_semantics") or "") not in {"formal_computed_result", "imported_external_result"}:
        blockers.append("ora_parameter_source_semantics_not_allowed")
    if ora_input.get("status") != "passed":
        blockers.extend(str(item) for item in ora_input.get("blockers", []) or [])
        if not ora_input:
            blockers.append("ora_input_gate_missing")
    if not manifest.get("gene_set_resource_id"):
        blockers.append("ora_parameter_missing_gene_set_resource")
    if gene_set_resource.get("status") != "passed" and gene_set_resource.get("validation_status") != "passed":
        blockers.extend(str(item) for item in gene_set_resource.get("blockers", []) or [])
        if not gene_set_resource:
            blockers.append("ora_gene_set_gate_missing")
    if int(ora_input.get("gene_list_count") or 0) <= 0:
        blockers.append("ora_selected_gene_list_empty")
    if int(ora_input.get("background_universe_count") or 0) <= 0:
        blockers.append("ora_background_universe_empty")
    blockers.extend(_threshold_blockers("p_value_threshold", manifest.get("p_value_threshold")))
    blockers.extend(_threshold_blockers("fdr_threshold", manifest.get("fdr_threshold")))
    if int(manifest.get("min_gene_set_size") or 0) <= 0:
        blockers.append("ora_min_gene_set_size_invalid")
    if int(manifest.get("max_gene_set_size") or 0) <= 0:
        blockers.append("ora_max_gene_set_size_invalid")
    if int(manifest.get("min_gene_set_size") or 0) > int(manifest.get("max_gene_set_size") or 0):
        blockers.append("ora_gene_set_size_bounds_invalid")
    if not str(manifest.get("multiple_testing_policy") or "").strip():
        blockers.append("ora_missing_multiple_testing_policy")
    if str(manifest.get("test_method") or "") not in ALLOWED_ORA_TEST_METHODS:
        blockers.append("ora_test_method_not_allowed")
    gene_mismatch = [str(item) for item in gene_set_resource.get("blockers", []) or [] if "gene_id_mismatch" in str(item)]
    if gene_mismatch:
        blockers.extend(gene_mismatch)
    warnings.extend(str(item) for item in ora_input.get("warnings", []) or [])
    warnings.extend(str(item) for item in gene_set_resource.get("warnings", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}


def _threshold_blockers(name: str, value: object) -> list[str]:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return [f"ora_{name}_invalid"]
    if number < 0 or number > 1:
        return [f"ora_{name}_invalid"]
    return []
