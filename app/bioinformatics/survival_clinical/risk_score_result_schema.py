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


def build_risk_score_result_schema_gate(
    candidate_result: dict[str, Any] | None = None,
    *,
    confirmation_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = ["risk_score_result_schema_only_no_execution"]
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
    if entry.get("plot_artifacts"):
        blockers.append("risk_score_plot_artifacts_not_enabled")
    if entry.get("report_artifacts"):
        blockers.append("risk_score_report_artifacts_not_enabled")
    if entry.get("report_ready_eligible") is True:
        blockers.append("risk_score_report_ready_not_enabled")
    for forbidden in ("clinical_conclusion", "diagnosis", "prognosis_label", "treatment_recommendation", "clinical_risk_group", "nomogram"):
        if entry.get(forbidden):
            blockers.append(f"forbidden_clinical_field:{forbidden}")
    base = validate_result_entry(entry)
    blockers.extend(str(item) for item in base.get("blockers", []) or [])
    warnings.extend(str(item) for item in base.get("warnings", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}
