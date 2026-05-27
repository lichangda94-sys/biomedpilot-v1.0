from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


DEG_INPUT_ADAPTATION_SCHEMA_VERSION = "biomedpilot.deg_real_project_input_adaptation_gate.v1"

COUNT_VALUE_TYPES = {"count", "raw_count", "raw_counts", "count_like_candidate"}
DISPLAY_VALUE_TYPES = {
    "TPM",
    "FPKM",
    "FPKM-UQ",
    "CPM",
    "normalized",
    "normalized_expression",
    "normalized_or_log_expression",
    "log_expression",
    "log2_transformed",
}
COUNT_MODEL_METHOD_FAMILIES = {"count_model", "deseq2", "edger"}
GENE_LEVEL_TYPES = {"symbol", "gene_symbol", "ensembl", "ensembl_gene_id"}
PROBE_GENE_ID_TYPES = {"probe", "probe_id", "ID_REF", "id_ref"}


def build_deg_input_adaptation_gate(
    input_package: dict[str, Any] | None,
    deg_ready_package: dict[str, Any] | None = None,
    *,
    requested_method_family: str = "",
) -> dict[str, Any]:
    package = input_package or {}
    ready = deg_ready_package or {}
    blockers: list[str] = []
    warnings: list[str] = []
    repair: list[str] = []

    if not package:
        blockers.append("missing_deg_recompute_input_package")
        repair.append("Create a standardized DEG recompute input package from the repository/registry before configuring DEG.")
    elif str(package.get("package_type") or "") != "deg_recompute":
        blockers.append("input_package_is_not_deg_recompute")
        repair.append("Select or generate a DEG recompute package; imported/preflight packages cannot be formal DEG input.")

    value_type = str(ready.get("value_type") or package.get("value_type") or "unknown")
    gene_id_type = str(ready.get("gene_id_type") or package.get("gene_id_type") or "unknown")
    alignment = ready.get("sample_alignment_status") if isinstance(ready.get("sample_alignment_status"), dict) else {}
    mapping = ready.get("gene_mapping_status") if isinstance(ready.get("gene_mapping_status"), dict) else {}

    if value_type in {"", "unknown"}:
        blockers.append("unknown_value_type_blocks_formal_deg")
        repair.append("Annotate the standardized expression asset with count, TPM, FPKM, log expression, or another supported value type.")
    elif value_type not in COUNT_VALUE_TYPES | DISPLAY_VALUE_TYPES:
        blockers.append("unsupported_value_type_for_deg_real_project")
        repair.append("Normalize value type metadata in the standardized repository before formal DEG.")

    requested_family = requested_method_family.strip().lower()
    if value_type in DISPLAY_VALUE_TYPES:
        warnings.append("display_value_type_requires_non_count_model_method")
        if requested_family in COUNT_MODEL_METHOD_FAMILIES:
            blockers.append("tpm_fpkm_or_log_expression_not_allowed_for_count_model_deg")
            repair.append("Use limma/Python two-group methods for display/log values, or regenerate a raw-count package for DESeq2/edgeR.")

    if alignment.get("status") == "blocked":
        blockers.extend(str(item) for item in alignment.get("blockers", []) or [])
        repair.append("Repair sample/group alignment in standardized sample metadata and rebuild the input package.")
    elif alignment.get("status") == "warning":
        warnings.extend(str(item) for item in alignment.get("warnings", []) or [])
        repair.append("Review partial sample/group overlap before formal DEG; rebuild standardized inputs if the mismatch is unintended.")

    if gene_id_type in PROBE_GENE_ID_TYPES or mapping.get("requires_mapping"):
        if mapping.get("status") != "passed":
            blockers.append("geo_probe_or_id_ref_requires_platform_mapping")
            repair.append("Attach a platform probe-to-gene mapping feature annotation and rebuild the standardized input package.")
    elif gene_id_type not in GENE_LEVEL_TYPES and "transcript" not in gene_id_type.lower():
        warnings.append("non_standard_gene_id_type_requires_review")
        repair.append("Confirm feature identifiers are gene-level or provide a reviewed mapping policy.")

    ready_blockers = [str(item) for item in ready.get("blockers", []) or []]
    ready_warnings = [str(item) for item in ready.get("warnings", []) or []]
    blockers.extend(item for item in ready_blockers if item not in {"probe_or_id_ref_mapping_missing"})
    warnings.extend(ready_warnings)

    blockers = _dedupe(blockers)
    warnings = _dedupe(warnings)
    allowed_methods = _allowed_methods(value_type, gene_id_type, blockers)
    return {
        "schema_version": DEG_INPUT_ADAPTATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "passed",
        "input_package_id": str(package.get("input_package_id") or ready.get("source_input_package_id") or ""),
        "deg_ready_package_id": str(ready.get("deg_ready_package_id") or ""),
        "value_type": value_type,
        "gene_id_type": gene_id_type,
        "sample_alignment_status": str(alignment.get("status") or ("blocked" if not package else "unknown")),
        "gene_mapping_status": str(mapping.get("status") or "unknown"),
        "allowed_methods": allowed_methods,
        "method_recommendations": _method_recommendations(value_type, gene_id_type, blockers),
        "blockers": blockers,
        "warnings": warnings,
        "repair_guidance": _dedupe(repair),
        "source_policy": "standardized repository / registry / analysis_input_repository only",
        "formal_execution_enabled": False,
        "semantic_boundary": "input_adaptation_gate_only_not_execution",
    }


def _allowed_methods(value_type: str, gene_id_type: str, blockers: list[str]) -> list[str]:
    if blockers:
        return []
    if value_type in COUNT_VALUE_TYPES and gene_id_type in GENE_LEVEL_TYPES:
        return ["deseq2", "edger", "limma_voom", "welch_t_test", "mann_whitney"]
    if value_type in DISPLAY_VALUE_TYPES and gene_id_type in GENE_LEVEL_TYPES:
        return ["limma", "welch_t_test", "mann_whitney"]
    return []


def _method_recommendations(value_type: str, gene_id_type: str, blockers: list[str]) -> list[dict[str, str]]:
    count_ready = value_type in COUNT_VALUE_TYPES and gene_id_type in GENE_LEVEL_TYPES and not blockers
    display_ready = value_type in DISPLAY_VALUE_TYPES and gene_id_type in GENE_LEVEL_TYPES and not blockers
    rows = [
        ("deseq2", count_ready, "recommended for raw count two-group designs", "requires raw counts and passed dependencies"),
        ("edger", count_ready, "available for raw count two-group designs", "requires raw counts and passed dependencies"),
        ("limma", count_ready or display_ready, "recommended for log/microarray values; limma-voom candidate for counts", "requires compatible gene-level values"),
        ("python_welch_or_mann_whitney", count_ready or display_ready, "available controlled two-group statistical fallback", "requires compatible numeric matrix"),
    ]
    result: list[dict[str, str]] = []
    for method, enabled, enabled_reason, disabled_reason in rows:
        state = "recommended" if enabled and method in {"deseq2", "limma"} else ("available" if enabled else "disabled")
        result.append({"method": method, "state": state, "reason": enabled_reason if enabled else disabled_reason})
    return result


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
