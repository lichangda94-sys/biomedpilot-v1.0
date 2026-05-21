from __future__ import annotations

from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.validation import validate_result_entry


COX_RESULT_COLUMNS = (
    "covariate",
    "covariate_label",
    "covariate_type",
    "hazard_ratio",
    "ci_lower",
    "ci_upper",
    "p_value",
    "z_statistic",
    "sample_count",
    "event_count",
    "non_missing_count",
    "missing_count",
    "method",
    "warnings",
)


def validate_cox_result_table(rows: list[dict[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    if not rows:
        blockers.append("missing_cox_result_table")
    for index, row in enumerate(rows):
        blockers.extend(f"cox_row_{index}:missing_column:{column}" for column in COX_RESULT_COLUMNS if column not in row)
        for numeric in ("hazard_ratio", "ci_lower", "ci_upper", "p_value", "z_statistic"):
            if numeric in row:
                try:
                    float(row[numeric])
                except (TypeError, ValueError):
                    blockers.append(f"cox_row_{index}:non_numeric:{numeric}")
        for forbidden in ("multivariate_adjusted_hr", "risk_score", "clinical_risk_group", "treatment_recommendation"):
            if forbidden in row:
                blockers.append(f"cox_row_{index}:forbidden_field:{forbidden}")
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": []}


def validate_cox_result_index_entry(entry: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    if semantics != "formal_computed_result":
        blockers.append(f"non_formal_semantics:{semantics}")
    if entry.get("task_type") != "cox_univariate":
        blockers.append("task_type_must_be_cox_univariate")
    if not entry.get("survival_clinical_input_id"):
        blockers.append("missing_survival_clinical_input_id")
    if not entry.get("survival_outcome_gate_id"):
        blockers.append("missing_survival_outcome_gate_id")
    if not entry.get("parameters_manifest"):
        blockers.append("missing_parameters_manifest")
    if not entry.get("dependency_snapshot") or entry.get("dependency_snapshot", {}).get("status") != "passed":
        blockers.append("dependency_snapshot_not_passed")
    if entry.get("validation_status") not in {"passed", "warning"}:
        blockers.append("validation_status_failed_or_blocked")
    if entry.get("blockers"):
        blockers.append("formal_cox_result_has_blockers")
    if entry.get("report_ready_eligible") is True:
        blockers.append("cox_report_ready_forbidden_in_b14")
    artifact_types = {str(item.get("artifact_type") or "") for item in entry.get("output_artifacts", []) or [] if isinstance(item, dict)}
    if "cox_result_table" not in artifact_types:
        blockers.append("missing_cox_result_table_artifact")
    if entry.get("report_artifacts"):
        blockers.append("cox_report_artifacts_forbidden_in_b14")
    text = str(entry)
    for forbidden in ("multivariate_adjusted_hr", "risk_score", "clinical_risk_group", "treatment_recommendation"):
        if forbidden in text:
            blockers.append(f"forbidden_multivariate_or_clinical_field:{forbidden}")
    base = validate_result_entry(entry)
    blockers.extend(str(item) for item in base.get("blockers", []) or [])
    warnings.extend(str(item) for item in base.get("warnings", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}
