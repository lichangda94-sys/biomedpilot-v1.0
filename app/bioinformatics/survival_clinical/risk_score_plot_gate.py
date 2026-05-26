from __future__ import annotations

from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry


RISK_SCORE_PLOT_NOMOGRAM_GATE_SCHEMA_VERSION = "biomedpilot.risk_score_plot_nomogram_gate.v1"


def build_risk_score_plot_nomogram_gate(project_root: str | Path, result_id: str | None = None) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) or [] if isinstance(entry, dict)]
    candidates = [_risk_score_entry(entry) for entry in entries]
    candidates = [entry for entry in candidates if entry is not None]
    source = _select_entry(candidates, result_id)
    blockers: list[str] = []
    warnings = [
        "risk_score_plot_nomogram_planning_only",
        "no_plot_artifact_created",
        "no_nomogram_generated",
        "no_report_ready_unlock",
        "no_clinical_interpretation",
    ]
    if source is None:
        blockers.append("formal_risk_score_result_not_found")
    else:
        blockers.extend(_source_blockers(source))
    blockers.append("b37_risk_score_renderer_activation_required")
    return {
        "schema_version": RISK_SCORE_PLOT_NOMOGRAM_GATE_SCHEMA_VERSION,
        "status": "blocked_planning_only",
        "selected_result_id": str((source or {}).get("result_id") or result_id or ""),
        "source_result_semantics": normalize_result_semantics((source or {}).get("result_semantics"), default="blocked"),
        "source_task_type": str((source or {}).get("task_type") or ""),
        "planned_artifacts": _planned_artifacts(source or {}),
        "minimum_conditions": {
            "source_formal_risk_score_table_only": "required",
            "source_validation_passed": "required",
            "risk_score_table_present": "required",
            "parameter_confirmation_present": "required",
            "dependency_snapshot_passed": "required",
            "plot_schema_defined": "required_before_activation",
            "renderer_dependency_passed": "required_before_activation",
            "user_visualization_confirmation": "required_before_activation",
        },
        "formal_execution_enabled": False,
        "writes_result_index": False,
        "creates_plot_artifact": False,
        "creates_report_artifact": False,
        "report_ready_eligible": False,
        "forbidden_outputs": [
            "high_risk_group",
            "low_risk_group",
            "clinical_risk_group",
            "prognosis_label",
            "diagnosis",
            "treatment_recommendation",
            "clinical_conclusion",
            "report_ready_package",
        ],
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _risk_score_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    if normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") != "formal_computed_result":
        return None
    if str(entry.get("task_type") or "").lower() != "risk_score":
        return None
    return entry


def _select_entry(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    return entries[-1] if entries else None


def _source_blockers(entry: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if entry.get("validation_status") not in {"passed", "warning"}:
        blockers.append("risk_score_source_validation_not_passed")
    if entry.get("blockers"):
        blockers.append("risk_score_source_has_blockers")
    if entry.get("plot_artifacts"):
        blockers.append("risk_score_source_already_has_plot_artifacts")
    if entry.get("report_artifacts"):
        blockers.append("risk_score_source_already_has_report_artifacts")
    if entry.get("report_ready_eligible") is True:
        blockers.append("risk_score_source_must_not_be_report_ready")
    if not entry.get("risk_score_parameter_confirmation"):
        blockers.append("risk_score_parameter_confirmation_missing")
    dependency = entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {}
    if dependency.get("status") != "passed":
        blockers.append("dependency_snapshot_not_passed")
    artifact_types = {str(item.get("artifact_type") or "") for item in entry.get("output_artifacts", []) or [] if isinstance(item, dict)}
    if "risk_score_result_table" not in artifact_types:
        blockers.append("risk_score_result_table_missing")
    return blockers


def _planned_artifacts(entry: dict[str, Any]) -> list[dict[str, Any]]:
    source_result_id = str(entry.get("result_id") or "")
    return [
        {
            "artifact_type": "risk_score_distribution_plot",
            "source_result_id": source_result_id,
            "activation_status": "planned_disabled",
            "renderer": "future_svg_or_matplotlib_renderer",
            "creates_risk_groups": False,
        },
        {
            "artifact_type": "risk_score_nomogram",
            "source_result_id": source_result_id,
            "activation_status": "planned_disabled",
            "renderer": "future_nomogram_renderer_not_selected",
            "creates_clinical_interpretation": False,
        },
        {
            "artifact_type": "risk_score_calibration_curve",
            "source_result_id": source_result_id,
            "activation_status": "planned_disabled",
            "renderer": "future_calibration_renderer_not_selected",
            "requires_validation_cohort": True,
        },
        {
            "artifact_type": "risk_score_decision_curve",
            "source_result_id": source_result_id,
            "activation_status": "planned_disabled",
            "renderer": "future_decision_curve_renderer_not_selected",
            "clinical_decision_recommendation_forbidden": True,
        },
    ]
