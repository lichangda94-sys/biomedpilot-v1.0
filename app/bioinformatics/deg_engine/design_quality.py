from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


DEG_DESIGN_QUALITY_SCHEMA_VERSION = "biomedpilot.deg_design_quality_gate.v1"


def build_deg_design_quality_gate(
    deg_ready_package: dict[str, Any] | None,
    *,
    design_manifest: dict[str, Any] | None = None,
    method_family: str = "",
    minimum_group_size: int = 1,
) -> dict[str, Any]:
    ready = deg_ready_package or {}
    design = design_manifest or {}
    alignment = ready.get("sample_alignment_status") if isinstance(ready.get("sample_alignment_status"), dict) else {}
    assignments = alignment.get("sample_group_assignments") if isinstance(alignment.get("sample_group_assignments"), dict) else {}
    group_counts = alignment.get("group_counts") if isinstance(alignment.get("group_counts"), dict) else {}
    sample_count = len(assignments)
    blockers: list[str] = []
    warnings: list[str] = []
    repair: list[str] = []

    if not ready:
        blockers.append("missing_deg_ready_package")
    if ready.get("blockers"):
        blockers.extend(str(item) for item in ready.get("blockers", []) or [])
    if len([group for group, count in group_counts.items() if int(count or 0) > 0]) < 2:
        blockers.append("case_control_groups_not_confirmed_or_empty")
        repair.append("Confirm at least two non-empty groups in standardized sample metadata.")
    if any(int(count or 0) < minimum_group_size for count in group_counts.values()):
        blockers.append("minimum_group_size_not_met")
        repair.append("Increase group size or revise comparison before formal DEG.")

    covariates = _covariates(design)
    batches = _batch_assignments(design)
    if not design:
        warnings.append("batch_covariate_manifest_missing")
        repair.append("Add a reviewed batch/covariate manifest when the study design contains known batches or covariates.")
    for name, values in {**covariates, **batches}.items():
        scoped_values = {sample: str(values.get(sample) or "") for sample in assignments}
        non_empty = {value for value in scoped_values.values() if value}
        if len(non_empty) <= 1:
            blockers.append(f"covariate_single_value:{name}")
            repair.append(f"Remove or repair covariate '{name}' because it has no usable variation.")
        if _fully_confounded(assignments, scoped_values):
            blockers.append(f"group_covariate_fully_confounded:{name}")
            repair.append(f"Resolve full confounding between group and '{name}' before formal DEG.")

    if bool(design.get("rank_deficient")):
        blockers.append("design_matrix_rank_deficient")
        repair.append("Revise the design formula/covariates; rank-deficient design matrices cannot be used for formal DEG.")
    if design.get("contrast_estimable") is False:
        blockers.append("contrast_not_estimable")
        repair.append("Revise the contrast or design formula so the requested comparison is estimable.")

    parameter_count = 1 + max(1, len(group_counts) - 1) + len(covariates) + len(batches)
    degrees_of_freedom = sample_count - parameter_count
    if sample_count and degrees_of_freedom <= 0:
        blockers.append("insufficient_degrees_of_freedom")
        repair.append("Reduce covariates or add samples; the design has no residual degrees of freedom.")

    blockers = _dedupe(blockers)
    warnings = _dedupe(warnings)
    return {
        "schema_version": DEG_DESIGN_QUALITY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "passed",
        "input_package_id": str(ready.get("source_input_package_id") or ready.get("input_package_id") or ""),
        "deg_ready_package_id": str(ready.get("deg_ready_package_id") or ""),
        "method_family": method_family or "unspecified",
        "sample_count": sample_count,
        "group_counts": dict(group_counts),
        "covariate_names": sorted(covariates),
        "batch_names": sorted(batches),
        "design_matrix_rank_status": "blocked" if "design_matrix_rank_deficient" in blockers else "not_rank_deficient",
        "contrast_estimability_status": "blocked" if "contrast_not_estimable" in blockers else "estimable_or_not_requested",
        "degrees_of_freedom": degrees_of_freedom if sample_count else 0,
        "supported_engines": ["python", "limma", "deseq2", "edger"],
        "blockers": blockers,
        "warnings": warnings,
        "repair_guidance": _dedupe(repair),
        "formal_execution_enabled": False,
        "semantic_boundary": "design_quality_gate_only_not_execution",
    }


def _covariates(design: dict[str, Any]) -> dict[str, dict[str, str]]:
    value = design.get("covariates")
    if isinstance(value, dict):
        return {str(name): _string_map(mapping) for name, mapping in value.items() if isinstance(mapping, dict)}
    rows = {}
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("assignments"), dict):
                rows[str(item.get("name") or "covariate")] = _string_map(item["assignments"])
    return rows


def _batch_assignments(design: dict[str, Any]) -> dict[str, dict[str, str]]:
    value = design.get("batch_assignments")
    if isinstance(value, dict):
        if all(not isinstance(item, dict) for item in value.values()):
            return {"batch": _string_map(value)}
        return {str(name): _string_map(mapping) for name, mapping in value.items() if isinstance(mapping, dict)}
    return {}


def _fully_confounded(groups: dict[str, str], covariate: dict[str, str]) -> bool:
    pairs = [(str(groups.get(sample) or ""), str(covariate.get(sample) or "")) for sample in groups if covariate.get(sample)]
    if not pairs:
        return False
    by_group: dict[str, set[str]] = {}
    by_covariate: dict[str, set[str]] = {}
    for group, value in pairs:
        by_group.setdefault(group, set()).add(value)
        by_covariate.setdefault(value, set()).add(group)
    return all(len(values) == 1 for values in by_group.values()) and all(len(groups_) == 1 for groups_ in by_covariate.values())


def _string_map(value: dict[Any, Any]) -> dict[str, str]:
    return {str(key): str(item) for key, item in value.items() if str(key)}


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
