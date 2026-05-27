from __future__ import annotations

from typing import Any

from .result_schema import validate_formal_deg_result_index_entry


MULTIFACTOR_DEG_RESULT_SCHEMA_GATE_VERSION = "biomedpilot.multifactor_deg_result_schema_gate.v1"

REQUIRED_MULTIFACTOR_PROVENANCE_FIELDS = (
    "design_formula",
    "contrast",
    "covariates",
    "batch_variables",
    "design_rank",
    "residual_degrees_of_freedom",
    "contrast_estimability",
    "backend_method",
)


def validate_multifactor_deg_parameters_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    blockers = [f"missing_multifactor_field:{field}" for field in REQUIRED_MULTIFACTOR_PROVENANCE_FIELDS if field not in manifest]
    if manifest.get("backend_method") not in {"limma", "DESeq2", "edgeR"}:
        blockers.append("unsupported_multifactor_backend_method")
    if not str(manifest.get("design_formula") or ""):
        blockers.append("missing_design_formula")
    contrast = manifest.get("contrast") if isinstance(manifest.get("contrast"), dict) else {}
    if not contrast:
        blockers.append("missing_contrast_manifest")
    elif not str(contrast.get("contrast_id") or ""):
        blockers.append("missing_contrast_id")
    if str(manifest.get("contrast_estimability") or "") not in {"estimable", "passed"}:
        blockers.append("contrast_not_estimable")
    if _to_int(manifest.get("design_rank")) <= 0:
        blockers.append("invalid_design_rank")
    if _to_int(manifest.get("residual_degrees_of_freedom")) <= 0:
        blockers.append("insufficient_degrees_of_freedom")
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": []}


def validate_multifactor_deg_result_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if bundle.get("result_semantics") != "formal_computed_result":
        blockers.append("multifactor_deg_requires_formal_computed_result_semantics")
    parameters = bundle.get("parameters_manifest") if isinstance(bundle.get("parameters_manifest"), dict) else {}
    parameter_validation = validate_multifactor_deg_parameters_manifest(parameters)
    blockers.extend(str(item) for item in parameter_validation.get("blockers", []) or [])
    for field in ("engine_name", "engine_version", "dependency_snapshot", "rows"):
        if field not in bundle:
            blockers.append(f"missing_field:{field}")
    if not bundle.get("rows"):
        warnings.append("multifactor_deg_result_has_no_rows")
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": warnings}


def validate_multifactor_deg_result_index_entry(entry: dict[str, Any]) -> dict[str, Any]:
    base = validate_formal_deg_result_index_entry(entry)
    blockers = [str(item) for item in base.get("blockers", []) or []]
    warnings = [str(item) for item in base.get("warnings", []) or []]
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    parameter_validation = validate_multifactor_deg_parameters_manifest(parameters)
    blockers.extend(str(item) for item in parameter_validation.get("blockers", []) or [])
    if str(entry.get("task_type") or "") != "deg":
        blockers.append("multifactor_deg_result_requires_deg_task_type")
    if entry.get("report_ready_eligible") is True:
        blockers.append("multifactor_deg_result_must_not_start_report_ready")
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}


def build_multifactor_deg_result_schema_gate(
    *,
    parameter_manifest: dict[str, Any] | None = None,
    dependency_snapshot: dict[str, Any] | None = None,
    result_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    parameters = parameter_manifest or {}
    parameter_validation = validate_multifactor_deg_parameters_manifest(parameters)
    blockers.extend(str(item) for item in parameter_validation.get("blockers", []) or [])
    dependency = dependency_snapshot or {}
    if dependency.get("status") != "passed":
        blockers.extend(str(item) for item in dependency.get("blockers", []) or ["dependency_snapshot_not_passed"])
    if result_entry is not None:
        entry_validation = validate_multifactor_deg_result_index_entry(result_entry)
        blockers.extend(str(item) for item in entry_validation.get("blockers", []) or [])
        warnings.extend(str(item) for item in entry_validation.get("warnings", []) or [])
    return {
        "schema_version": MULTIFACTOR_DEG_RESULT_SCHEMA_GATE_VERSION,
        "status": "blocked" if blockers else "passed",
        "gate_semantics": "multifactor_deg_result_index_v2_acceptance_gate",
        "required_multifactor_provenance_fields": list(REQUIRED_MULTIFACTOR_PROVENANCE_FIELDS),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _to_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
