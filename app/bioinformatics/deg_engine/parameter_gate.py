from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


PARAMETER_GATE_SCHEMA_VERSION = "biomedpilot.deg_parameter_gate.v1"

COUNT_VALUE_TYPES = {"count", "raw_count", "raw_counts", "count_like_candidate"}
DISPLAY_VALUE_TYPES = {"TPM", "FPKM", "FPKM-UQ", "normalized", "normalized_expression", "normalized_or_log_expression", "log_expression", "log2_transformed"}
COUNT_MODEL_METHODS = {"count_model", "deseq2", "deseq2_external_design", "edger", "edger_external_design"}
CONTROLLED_TWO_GROUP_METHODS = {"welch_t_test", "mann_whitney"}

REQUIRED_PARAMETER_FIELDS = (
    "schema_version",
    "created_at",
    "input_package_id",
    "deg_ready_package_id",
    "comparison_id",
    "case_group",
    "control_group",
    "case_samples",
    "control_samples",
    "group_design_source",
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
    "pseudocount",
    "pseudocount_policy",
    "minimum_group_size",
    "missing_value_policy",
    "multiple_testing_policy",
    "engine_candidate",
    "dependency_snapshot",
    "warnings",
    "blockers",
)


def build_deg_parameter_manifest(
    deg_ready_package: dict[str, Any],
    *,
    comparison_id: str = "case_vs_control",
    case_group: str = "case",
    control_group: str = "control",
    case_samples: list[str] | None = None,
    control_samples: list[str] | None = None,
    method: str = "welch_t_test",
    log2fc_threshold: float = 1.0,
    p_value_threshold: float = 0.05,
    fdr_threshold: float = 0.05,
    fdr_policy: str = "benjamini_hochberg",
    pseudocount: float = 1e-9,
    minimum_group_size: int = 1,
    missing_value_policy: str = "omit_missing_values_per_feature",
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    package = dict(deg_ready_package)
    dependency = dependency_snapshot or {}
    alignment = package.get("sample_alignment_status") if isinstance(package.get("sample_alignment_status"), dict) else {}
    gene_mapping = package.get("gene_mapping_status") if isinstance(package.get("gene_mapping_status"), dict) else {}
    group_design = package.get("group_design_asset") if isinstance(package.get("group_design_asset"), dict) else {}
    manifest = {
        "schema_version": PARAMETER_GATE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_package_id": str(package.get("source_input_package_id") or package.get("input_package_id") or ""),
        "deg_ready_package_id": str(package.get("deg_ready_package_id") or ""),
        "comparison_id": comparison_id,
        "case_group": case_group,
        "control_group": control_group,
        "case_samples": list(case_samples or _samples_for_group(alignment, case_group)),
        "control_samples": list(control_samples or _samples_for_group(alignment, control_group)),
        "group_design_source": str(group_design.get("path") or group_design.get("file_path") or ""),
        "method": method,
        "method_family": _method_family(method),
        "value_type": str(package.get("value_type") or "unknown"),
        "value_type_policy": _value_type_policy(str(package.get("value_type") or "unknown"), method),
        "gene_id_type": str(package.get("gene_id_type") or "unknown"),
        "gene_mapping_policy": _gene_mapping_policy(gene_mapping),
        "sample_alignment_policy": _sample_alignment_policy(alignment),
        "log2fc_threshold": log2fc_threshold,
        "p_value_threshold": p_value_threshold,
        "fdr_threshold": fdr_threshold,
        "fdr_policy": fdr_policy,
        "pseudocount": pseudocount,
        "pseudocount_policy": "required_non_negative_for_log2fc_ratio",
        "minimum_group_size": minimum_group_size,
        "missing_value_policy": missing_value_policy,
        "multiple_testing_policy": fdr_policy,
        "engine_candidate": str(dependency.get("engine_candidate") or "python_scipy_statsmodels"),
        "dependency_snapshot": dependency,
        "warnings": list(dict.fromkeys([str(item) for item in package.get("warnings", []) or []])),
        "blockers": list(dict.fromkeys([str(item) for item in package.get("blockers", []) or []])),
    }
    validation = validate_deg_parameter_manifest(manifest)
    manifest["blockers"] = list(dict.fromkeys([*manifest["blockers"], *validation["blockers"]]))
    manifest["warnings"] = list(dict.fromkeys([*manifest["warnings"], *validation["warnings"]]))
    manifest["status"] = "blocked" if manifest["blockers"] else "passed"
    manifest["semantic_boundary"] = "formal_deg_parameter_gate_only_not_execution"
    return manifest


def validate_deg_parameter_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    blockers = [f"missing_field:{field_name}" for field_name in REQUIRED_PARAMETER_FIELDS if field_name not in manifest]
    warnings: list[str] = []
    case_group = str(manifest.get("case_group") or "")
    control_group = str(manifest.get("control_group") or "")
    case_samples = _string_list(manifest.get("case_samples"))
    control_samples = _string_list(manifest.get("control_samples"))
    method = str(manifest.get("method") or "")
    value_type = str(manifest.get("value_type") or "unknown")
    dependency = manifest.get("dependency_snapshot") if isinstance(manifest.get("dependency_snapshot"), dict) else {}

    if not case_group or not control_group:
        blockers.append("missing_case_or_control_group")
    elif case_group == control_group:
        blockers.append("same_case_control_group")
    if not case_samples:
        blockers.append("missing_case_samples")
    if not control_samples:
        blockers.append("missing_control_samples")
    if set(case_samples) & set(control_samples):
        blockers.append("case_control_samples_overlap")
    minimum_group_size = _to_int(manifest.get("minimum_group_size"), default=1)
    if len(case_samples) < minimum_group_size or len(control_samples) < minimum_group_size:
        blockers.append("minimum_group_size_not_met")
    sample_policy = str(manifest.get("sample_alignment_policy") or "")
    if sample_policy.startswith("blocked"):
        blockers.append("sample_group_mismatch")
    if method in COUNT_MODEL_METHODS:
        blockers.append("count_model_backend_not_activated_in_b9_2_controlled_mvp")
    if value_type in DISPLAY_VALUE_TYPES and method in COUNT_MODEL_METHODS:
        blockers.append("count_model_requested_for_display_value_type")
    elif value_type in COUNT_VALUE_TYPES | DISPLAY_VALUE_TYPES and method not in CONTROLLED_TWO_GROUP_METHODS | COUNT_MODEL_METHODS:
        blockers.append("method_not_supported_by_controlled_deg_mvp")
    elif value_type in {"", "unknown"}:
        blockers.append("unknown_value_type")
    elif value_type not in COUNT_VALUE_TYPES | DISPLAY_VALUE_TYPES:
        blockers.append("unknown_value_type")
    gene_policy = str(manifest.get("gene_mapping_policy") or "")
    if gene_policy.startswith("blocked"):
        blockers.append("probe_or_id_ref_mapping_missing")
    if _to_float(manifest.get("pseudocount")) is None or float(manifest.get("pseudocount") or 0) < 0:
        blockers.append("invalid_pseudocount")
    if not str(manifest.get("fdr_policy") or ""):
        blockers.append("missing_fdr_policy")
    for field_name in ("log2fc_threshold", "p_value_threshold", "fdr_threshold"):
        value = _to_float(manifest.get(field_name))
        if value is None:
            blockers.append(f"invalid_threshold:{field_name}")
            continue
        if field_name in {"p_value_threshold", "fdr_threshold"} and not 0 <= value <= 1:
            blockers.append(f"invalid_threshold:{field_name}")
        if field_name == "log2fc_threshold" and value < 0:
            blockers.append(f"invalid_threshold:{field_name}")
    if dependency.get("status") != "passed":
        blockers.append("dependency_snapshot_not_passed")
        blockers.extend(str(item) for item in dependency.get("blockers", []) or [])
    package_blockers = _string_list(manifest.get("blockers"))
    for blocker in package_blockers:
        if blocker.startswith("missing_field:"):
            continue
        blockers.append(blocker)
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": warnings}


def _method_family(method: str) -> str:
    if method in COUNT_MODEL_METHODS:
        return "count_model"
    if method in CONTROLLED_TWO_GROUP_METHODS:
        return "controlled_two_group_statistical_test"
    return "unknown"


def _value_type_policy(value_type: str, method: str) -> str:
    if value_type in COUNT_VALUE_TYPES and method in COUNT_MODEL_METHODS:
        return "blocked_count_model_backend_not_activated"
    if value_type in COUNT_VALUE_TYPES and method in CONTROLLED_TWO_GROUP_METHODS:
        return "count_values_controlled_two_group_mvp"
    if value_type in DISPLAY_VALUE_TYPES and method in CONTROLLED_TWO_GROUP_METHODS:
        return "display_values_controlled_two_group_mvp"
    if value_type in DISPLAY_VALUE_TYPES and method in COUNT_MODEL_METHODS:
        return "blocked_display_value_for_count_model"
    return "blocked_unknown_or_incompatible_value_type"


def _gene_mapping_policy(gene_mapping: dict[str, Any]) -> str:
    if gene_mapping.get("status") == "passed":
        return "passed"
    if gene_mapping.get("requires_mapping"):
        return "blocked_probe_or_id_ref_mapping_required"
    return f"blocked_{gene_mapping.get('status') or 'unknown'}"


def _sample_alignment_policy(alignment: dict[str, Any]) -> str:
    status = str(alignment.get("status") or "unknown")
    if status == "passed":
        return "passed"
    if status == "warning":
        return "warning_partial_overlap_review_required"
    return f"blocked_{status}"


def _samples_for_group(alignment: dict[str, Any], group: str) -> list[str]:
    assignments = alignment.get("sample_group_assignments")
    if isinstance(assignments, dict):
        return sorted(str(sample) for sample, value in assignments.items() if str(value) == group)
    return []


def _string_list(value: object) -> list[str]:
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value if str(item)]
    return []


def _to_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: object, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
