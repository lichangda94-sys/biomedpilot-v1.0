from __future__ import annotations

from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.validation import validate_result_entry


RISK_SCORE_RESULT_SCHEMA_GATE_VERSION = "biomedpilot.risk_score_result_schema_gate.v1"
RISK_SCORE_RESULT_COLUMNS = (
    "sample_id",
    "case_id",
    "risk_score",
    "source_cox_multivariate_result_id",
    "model_formula",
    "coefficient_source",
    "missingness_policy",
    "scaling_policy",
    "warnings",
)
FORBIDDEN_RISK_SCORE_FIELDS = (
    "risk_group",
    "high_risk_group",
    "low_risk_group",
    "prognosis_label",
    "clinical_conclusion",
    "diagnosis",
    "treatment_recommendation",
    "nomogram_score",
)
ALLOWED_RISK_SCORE_PLOT_TYPES = {
    "risk_score_distribution_plot",
    "risk_score_nomogram",
    "risk_score_calibration_curve",
    "risk_score_decision_curve",
}


def build_risk_score_result_schema_gate(
    candidate_result: dict[str, Any] | None = None,
    *,
    confirmation_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = ["risk_score_result_schema_validation_required"]
    confirmation = confirmation_gate if isinstance(confirmation_gate, dict) else {}
    if confirmation.get("status") != "passed":
        blockers.extend(str(item) for item in confirmation.get("blockers", []) or [])
        blockers.append("risk_score_parameter_confirmation_gate_not_passed")
    if not candidate_result:
        blockers.append("risk_score_result_bundle_missing")
    else:
        schema_gate = validate_risk_score_result_index_entry(candidate_result)
        blockers.extend(str(item) for item in schema_gate.get("blockers", []) or [])
        warnings.extend(str(item) for item in schema_gate.get("warnings", []) or [])
    return {
        "schema_version": RISK_SCORE_RESULT_SCHEMA_GATE_VERSION,
        "status": "passed_future_schema_only" if not blockers else "blocked",
        "gate_semantics": "risk_score_result_index_v2_schema_gate_no_execution",
        "formal_execution_enabled": False,
        "writes_result_index": False,
        "report_ready_eligible": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def validate_risk_score_result_table(rows: list[dict[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    if not rows:
        blockers.append("missing_risk_score_result_table")
    for index, row in enumerate(rows):
        blockers.extend(f"risk_score_row_{index}:missing_column:{column}" for column in RISK_SCORE_RESULT_COLUMNS if column not in row)
        if "risk_score" in row:
            try:
                float(row["risk_score"])
            except (TypeError, ValueError):
                blockers.append(f"risk_score_row_{index}:non_numeric:risk_score")
        for forbidden in FORBIDDEN_RISK_SCORE_FIELDS:
            if forbidden in row:
                blockers.append(f"risk_score_row_{index}:forbidden_field:{forbidden}")
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": []}


def validate_risk_score_result_index_entry(entry: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    if semantics != "formal_computed_result":
        blockers.append(f"non_formal_semantics:{semantics}")
    if entry.get("task_type") != "risk_score":
        blockers.append("task_type_must_be_risk_score")
    if not entry.get("source_cox_multivariate_result_id"):
        blockers.append("missing_source_cox_multivariate_result_id")
    if not entry.get("risk_score_parameter_confirmation"):
        blockers.append("missing_risk_score_parameter_confirmation")
    if not entry.get("parameters_manifest"):
        blockers.append("missing_parameters_manifest")
    if not entry.get("dependency_snapshot") or entry.get("dependency_snapshot", {}).get("status") != "passed":
        blockers.append("dependency_snapshot_not_passed")
    if entry.get("validation_status") not in {"passed", "warning"}:
        blockers.append("validation_status_failed_or_blocked")
    if entry.get("blockers"):
        blockers.append("formal_risk_score_result_has_blockers")
    artifact_types = {str(item.get("artifact_type") or "") for item in entry.get("output_artifacts", []) or [] if isinstance(item, dict)}
    if "risk_score_result_table" not in artifact_types:
        blockers.append("missing_risk_score_result_table_artifact")
    blockers.extend(_validate_plot_artifacts(entry))
    if entry.get("report_artifacts"):
        _validate_report_artifacts(entry, blockers)
    if entry.get("report_ready_eligible") is True and not _has_risk_score_report_ready_artifact(entry):
        blockers.append("risk_score_report_ready_requires_b46_report_package")
    for forbidden in ("clinical_conclusion", "diagnosis", "prognosis_label", "treatment_recommendation", "clinical_risk_group", "nomogram"):
        if entry.get(forbidden):
            blockers.append(f"forbidden_clinical_field:{forbidden}")
    base = validate_result_entry(entry)
    blockers.extend(str(item) for item in base.get("blockers", []) or [])
    warnings.extend(str(item) for item in base.get("warnings", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}


def _validate_plot_artifacts(entry: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    artifacts = entry.get("plot_artifacts") if isinstance(entry.get("plot_artifacts"), list) else []
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            blockers.append(f"risk_score_plot_artifact_{index}:invalid")
            continue
        if artifact.get("plot_artifact_scope") != "formal_risk_score_plot_artifact":
            blockers.append(f"risk_score_plot_artifact_{index}:invalid_scope")
        if artifact.get("plot_type") not in ALLOWED_RISK_SCORE_PLOT_TYPES:
            blockers.append(f"risk_score_plot_artifact_{index}:unsupported_plot_type:{artifact.get('plot_type')}")
        semantics = normalize_result_semantics(artifact.get("plot_semantics") or artifact.get("source_result_semantics"), default="")
        if semantics != "formal_computed_result":
            blockers.append(f"risk_score_plot_artifact_{index}:non_formal_semantics:{semantics}")
        if artifact.get("source_result_id") and artifact.get("source_result_id") != entry.get("result_id"):
            blockers.append(f"risk_score_plot_artifact_{index}:source_result_mismatch")
        if artifact.get("report_ready_eligible") is True:
            blockers.append(f"risk_score_plot_artifact_{index}:report_ready_not_allowed")
        for forbidden in ("risk_group", "high_risk_group", "low_risk_group", "clinical_risk_group", "clinical_conclusion", "diagnosis", "prognosis_label", "treatment_recommendation"):
            if _contains_key(artifact, forbidden):
                blockers.append(f"risk_score_plot_artifact_{index}:forbidden_field:{forbidden}")
    return blockers


def _contains_key(value: Any, key_name: str) -> bool:
    if isinstance(value, dict):
        return any(str(key) == key_name or _contains_key(item, key_name) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_key(item, key_name) for item in value)
    return False


def _validate_report_artifacts(entry: dict[str, Any], blockers: list[str]) -> None:
    for index, artifact in enumerate(entry.get("report_artifacts", []) or []):
        if not isinstance(artifact, dict):
            blockers.append(f"risk_score_report_artifact_{index}:invalid")
            continue
        if artifact.get("artifact_type") != "risk_score_report_ready_package":
            blockers.append(f"risk_score_report_artifact_{index}:unsupported_report_artifact:{artifact.get('artifact_type')}")
        if artifact.get("section_scope") != "risk_score_validation_only":
            blockers.append(f"risk_score_report_artifact_{index}:invalid_section_scope:{artifact.get('section_scope')}")
        if not artifact.get("path"):
            blockers.append(f"risk_score_report_artifact_{index}:missing_path")


def _has_risk_score_report_ready_artifact(entry: dict[str, Any]) -> bool:
    return any(
        isinstance(artifact, dict)
        and artifact.get("artifact_type") == "risk_score_report_ready_package"
        and artifact.get("section_scope") == "risk_score_validation_only"
        and bool(artifact.get("path"))
        for artifact in entry.get("report_artifacts", []) or []
    )
