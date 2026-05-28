from __future__ import annotations

from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.validation import validate_result_entry


COX_MULTIVARIATE_RESULT_COLUMNS = (
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
    "adjusted_for",
    "method",
    "warnings",
)


def validate_cox_multivariate_result_table(rows: list[dict[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    if not rows:
        blockers.append("missing_cox_multivariate_result_table")
    for index, row in enumerate(rows):
        blockers.extend(f"cox_multivariate_row_{index}:missing_column:{column}" for column in COX_MULTIVARIATE_RESULT_COLUMNS if column not in row)
        for numeric in ("hazard_ratio", "ci_lower", "ci_upper", "p_value", "z_statistic"):
            if numeric in row:
                try:
                    float(row[numeric])
                except (TypeError, ValueError):
                    blockers.append(f"cox_multivariate_row_{index}:non_numeric:{numeric}")
        for forbidden in ("risk_score", "clinical_risk_group", "prognosis_label", "treatment_recommendation", "clinical_conclusion"):
            if forbidden in row:
                blockers.append(f"cox_multivariate_row_{index}:forbidden_field:{forbidden}")
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": []}


def validate_cox_multivariate_result_index_entry(entry: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    if semantics != "formal_computed_result":
        blockers.append(f"non_formal_semantics:{semantics}")
    if entry.get("task_type") != "cox_multivariate":
        blockers.append("task_type_must_be_cox_multivariate")
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
        blockers.append("formal_cox_multivariate_result_has_blockers")
    if entry.get("report_ready_eligible") is True and not _has_b28_report_artifact(entry):
        blockers.append("cox_multivariate_report_ready_requires_b28_section_package")
    artifact_types = {str(item.get("artifact_type") or "") for item in entry.get("output_artifacts", []) or [] if isinstance(item, dict)}
    if "cox_multivariate_result_table" not in artifact_types:
        blockers.append("missing_cox_multivariate_result_table_artifact")
    if entry.get("report_artifacts") and not _has_b28_report_artifact(entry):
        blockers.append("cox_multivariate_report_artifacts_must_be_b28_section_package")
    base = validate_result_entry(entry)
    blockers.extend(str(item) for item in base.get("blockers", []) or [])
    warnings.extend(str(item) for item in base.get("warnings", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}


def _has_b28_report_artifact(entry: dict[str, Any]) -> bool:
    for artifact in entry.get("report_artifacts", []) or []:
        if not isinstance(artifact, dict):
            continue
        if artifact.get("artifact_type") == "cox_multivariate_report_ready_package" and artifact.get("section_scope") == "cox_multivariate_only":
            return True
    return False
