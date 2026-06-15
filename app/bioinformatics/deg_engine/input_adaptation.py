from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


DEG_INPUT_ADAPTATION_SCHEMA_VERSION = "biomedpilot.deg_real_project_input_adaptation_gate.v1"

COUNT_VALUE_TYPES = {"count", "raw_count", "raw_counts", "count_like_candidate"}
DISPLAY_VALUE_TYPES = {"TPM", "FPKM", "FPKM-UQ", "CPM", "normalized", "normalized_expression", "normalized_or_log_expression", "log_expression", "log2_transformed"}
PROBE_GENE_ID_TYPES = {"probe", "probe_id", "ID_REF", "id_ref", "unknown"}
GENE_LEVEL_TYPES = {"symbol", "gene_symbol", "ensembl", "ensembl_gene_id"}


def build_deg_input_adaptation_gate(
    input_package: dict[str, Any] | None,
    deg_ready_package: dict[str, Any] | None = None,
    *,
    requested_method_family: str = "",
) -> dict[str, Any]:
    package = input_package if isinstance(input_package, dict) else {}
    ready = deg_ready_package if isinstance(deg_ready_package, dict) else {}
    blockers = [str(item) for item in package.get("blockers", []) or []]
    warnings = [str(item) for item in package.get("warnings", []) or []]
    repair_guidance: list[str] = []
    if not package:
        blockers.append("missing_deg_recompute_input_package")
        repair_guidance.append("Create a standardized DEG recompute input package through resolver.")
    elif str(package.get("package_type") or "") != "deg_recompute":
        blockers.append("input_package_is_not_deg_recompute")
        repair_guidance.append("Select a resolver package with package_type=deg_recompute.")

    value_type = str(package.get("value_type") or ready.get("value_type") or "unknown")
    gene_id_type = str(package.get("gene_id_type") or ready.get("gene_id_type") or "unknown")
    alignment = ready.get("sample_alignment_status") if isinstance(ready.get("sample_alignment_status"), dict) else {}
    gene_mapping = ready.get("gene_mapping_status") if isinstance(ready.get("gene_mapping_status"), dict) else {}
    blockers.extend(str(item) for item in ready.get("blockers", []) or [])
    warnings.extend(str(item) for item in ready.get("warnings", []) or [])

    if value_type in {"", "unknown"}:
        blockers.append("unknown_value_type_blocks_formal_deg")
        repair_guidance.append("Annotate expression value type during standardization.")
    elif value_type in DISPLAY_VALUE_TYPES:
        warnings.append("display_value_type_blocks_count_model_methods")
        if requested_method_family in {"deseq2", "edger", "count_model"}:
            blockers.append("tpm_fpkm_or_log_expression_not_allowed_for_count_model_deg")
    elif value_type not in COUNT_VALUE_TYPES:
        blockers.append("unsupported_value_type_for_deg_real_project")
        repair_guidance.append("Normalize value type to raw counts, TPM, FPKM, FPKM-UQ, CPM, or log expression.")

    if gene_id_type in PROBE_GENE_ID_TYPES and gene_mapping.get("status") != "passed":
        blockers.append("geo_probe_or_id_ref_requires_platform_mapping")
        repair_guidance.append("Attach validated platform probe-to-gene mapping before formal DEG.")
    elif gene_id_type not in GENE_LEVEL_TYPES and gene_id_type not in PROBE_GENE_ID_TYPES:
        warnings.append("non_standard_gene_id_type_requires_review")

    if alignment.get("status") == "blocked":
        repair_guidance.append("Repair sample/group alignment before DEG.")
    if "expression_metadata_sample_partial_overlap" in alignment.get("warnings", []):
        warnings.append("sample_group_partial_overlap_requires_review")
        repair_guidance.append("Review unmatched expression and metadata samples before confirmation.")

    method_recommendations = _method_recommendations(value_type=value_type, gene_id_type=gene_id_type, blockers=blockers)
    allowed_methods = [item["method"] for item in method_recommendations if item["state"] in {"recommended", "available"}]
    unique_blockers = _dedupe(blockers)
    unique_warnings = _dedupe(warnings)
    return {
        "schema_version": DEG_INPUT_ADAPTATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if unique_blockers else "passed",
        "input_package_id": str(package.get("input_package_id") or ""),
        "deg_ready_package_id": str(ready.get("deg_ready_package_id") or ""),
        "value_type": value_type,
        "gene_id_type": gene_id_type,
        "sample_alignment_status": str(alignment.get("status") or "missing"),
        "gene_mapping_status": str(gene_mapping.get("status") or "missing"),
        "allowed_methods": allowed_methods,
        "method_recommendations": method_recommendations,
        "blockers": unique_blockers,
        "warnings": unique_warnings,
        "repair_guidance": _dedupe(repair_guidance),
        "diagnostics": {
            "sample_alignment": alignment,
            "gene_mapping": gene_mapping,
            "source_policy": "standardized repository / registry / analysis_input_repository only",
        },
    }


def _method_recommendations(*, value_type: str, gene_id_type: str, blockers: list[str]) -> list[dict[str, Any]]:
    hard_blocked = bool(blockers)
    count_value = value_type in COUNT_VALUE_TYPES
    display_value = value_type in DISPLAY_VALUE_TYPES
    gene_level = gene_id_type in GENE_LEVEL_TYPES
    return [
        _method("deseq2", "recommended" if count_value and not hard_blocked else "disabled", "raw integer count model only" if count_value else "requires raw integer counts"),
        _method("edger", "recommended" if count_value and not hard_blocked else "disabled", "raw integer count model only" if count_value else "requires raw integer counts"),
        _method("limma", "recommended" if display_value and gene_level and not hard_blocked else ("available" if count_value and not hard_blocked else "disabled"), "recommended for log/microarray/normalized expression; limma-voom may be considered for counts"),
        _method("python_welch_or_mann_whitney", "available" if (count_value or display_value) and gene_level and not hard_blocked else "disabled", "controlled two-group fallback with statistical limitations"),
    ]


def _method(method: str, state: str, reason: str) -> dict[str, str]:
    return {"method": method, "state": state, "reason": reason}


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
