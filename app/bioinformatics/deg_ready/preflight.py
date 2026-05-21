from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import DEG_PREFLIGHT_SCHEMA_VERSION, DegReadyPackage


COUNT_VALUE_TYPES = {"count", "raw_count", "raw_counts", "count_like_candidate"}
DISPLAY_VALUE_TYPES = {"TPM", "FPKM", "FPKM-UQ", "normalized", "normalized_expression", "normalized_or_log_expression", "log_expression", "log2_transformed"}


def build_deg_formal_preflight(
    deg_ready_package: DegReadyPackage | dict[str, Any],
    *,
    comparison_id: str = "case_vs_control",
    case_group: str = "case",
    control_group: str = "control",
    method_candidate: str = "backend_decision_pending",
    engine_candidate: str = "not_configured_until_B8_3",
) -> dict[str, Any]:
    package = deg_ready_package.to_dict() if isinstance(deg_ready_package, DegReadyPackage) else dict(deg_ready_package)
    blockers = [str(item) for item in package.get("blockers", []) or []]
    warnings = [str(item) for item in package.get("warnings", []) or []]
    value_type = str(package.get("value_type") or "unknown")
    if not case_group or not control_group or case_group == control_group:
        blockers.append("case_control_groups_invalid")
    if value_type in COUNT_VALUE_TYPES:
        method_policy = "count_model_preflight_allowed"
        if method_candidate not in {"backend_decision_pending", "count_model", "deseq2_external_design", "edger_external_design"}:
            blockers.append("count_matrix_requires_count_model_backend")
    elif value_type in DISPLAY_VALUE_TYPES:
        method_policy = "non_count_model_preflight_only"
        if method_candidate in {"count_model", "deseq2_external_design", "edger_external_design"}:
            blockers.append("tpm_fpkm_or_log_expression_not_allowed_for_count_model_deg")
    else:
        method_policy = "blocked_unknown_value_type"
        blockers.append("unknown_value_type_blocks_formal_deg")
    parameter_manifest = {
        "comparison_id": comparison_id,
        "case_group": case_group,
        "control_group": control_group,
        "method_candidate": method_candidate,
        "value_type": value_type,
        "pseudocount_policy": "required_for_log2fc_only_when_non_count_backend_selected",
        "fold_change_policy": "log2(case_mean/control_mean); no values computed in preflight",
        "p_value_policy": "not_computed_until_B8_3_backend",
        "fdr_policy": "not_computed_until_B8_3_backend",
        "engine_candidate": engine_candidate,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }
    return {
        "schema_version": DEG_PREFLIGHT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "passed",
        "semantic_boundary": "formal_deg_preflight_only_not_result",
        "source_input_package_id": str(package.get("source_input_package_id") or ""),
        "deg_ready_package_id": str(package.get("deg_ready_package_id") or ""),
        "sample_alignment_status": package.get("sample_alignment_status") or {},
        "gene_mapping_status": package.get("gene_mapping_status") or {},
        "value_type_policy": method_policy,
        "parameter_manifest": parameter_manifest,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
        "forbidden_outputs": ["p_value", "adjusted_p_value", "DEG result table", "volcano plot", "report-ready conclusion"],
    }
