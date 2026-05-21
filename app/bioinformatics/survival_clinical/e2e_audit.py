from __future__ import annotations

from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry

from .km_confirmation import validate_km_logrank_confirmation
from .km_result_schema import validate_km_result_index_entry, validate_km_result_tables
from .km_review import build_km_result_review
from ._io import read_table


def audit_survival_km_e2e_acceptance(project_root: str | Path, result_id: str, *, confirmation: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = load_registry(project_root)
    entry = next((item for item in registry.get("results", []) if isinstance(item, dict) and item.get("result_id") == result_id), {})
    blockers: list[str] = []
    warnings: list[str] = []
    if not entry:
        blockers.append("missing_result_index_entry")
        return _audit(blockers, warnings, {})
    if normalize_result_semantics(entry.get("result_semantics")) != "formal_computed_result":
        blockers.append("preflight_testing_or_imported_source_blocked")
    parameter_manifest = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    if parameter_manifest.get("status") != "passed":
        blockers.append("km_parameter_gate_not_passed")
    if confirmation is not None:
        confirmation_gate = validate_km_logrank_confirmation(confirmation, parameter_manifest)
        blockers.extend(str(item) for item in confirmation_gate.get("blockers", []) or [])
    if (entry.get("dependency_snapshot") or {}).get("status") != "passed":
        blockers.append("missing_dependency")
    schema_gate = validate_km_result_index_entry(entry)
    blockers.extend(str(item) for item in schema_gate.get("blockers", []) or [])
    paths = {str(item.get("artifact_type") or ""): str(item.get("path") or "") for item in entry.get("output_artifacts", []) or [] if isinstance(item, dict)}
    km_rows = read_table(paths.get("km_curve_table"))
    logrank_rows = read_table(paths.get("logrank_result_table"))
    table_gate = validate_km_result_tables(km_rows, logrank_rows)
    blockers.extend(str(item) for item in table_gate.get("blockers", []) or [])
    review = build_km_result_review(project_root, result_id)
    if review.get("status") != "passed":
        blockers.append("km_review_failed")
    plot_artifacts = [item for item in entry.get("plot_artifacts", []) or [] if isinstance(item, dict)]
    if plot_artifacts:
        latest = plot_artifacts[-1]
        if latest.get("source_result_id") != result_id:
            blockers.append("plot_artifact_source_mismatch")
        if latest.get("image_artifacts"):
            blockers.append("km_plot_image_artifacts_forbidden_in_b13")
    if entry.get("report_ready_eligible") is True or entry.get("report_artifacts"):
        blockers.append("survival_report_ready_must_remain_disabled")
    text = str(entry)
    for forbidden in ("hazard_ratio", "ci_lower", "ci_upper", "cox_p_value"):
        if forbidden in text:
            blockers.append(f"forbidden_cox_or_hr_field:{forbidden}")
    traceability = {
        "survival_input_id": entry.get("survival_clinical_input_id", ""),
        "outcome_gate_id": entry.get("survival_outcome_gate_id", ""),
        "parameter_manifest_id": parameter_manifest.get("km_parameter_id", ""),
        "dependency_snapshot": bool(entry.get("dependency_snapshot")),
        "task_run_log": bool(entry.get("log_artifacts")),
        "result_id": entry.get("result_id", ""),
        "plot_artifact_id": plot_artifacts[-1].get("plot_id", "") if plot_artifacts else "",
    }
    return _audit(blockers, warnings, traceability)


def _audit(blockers: list[str], warnings: list[str], traceability: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.survival_km_e2e_acceptance_audit.v1",
        "status": "blocked" if blockers else "passed",
        "traceability": traceability,
        "report_ready_eligible": False,
        "survival_report_ready": {"status": "disabled", "reason": "survival_report_gate_not_implemented"},
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }
