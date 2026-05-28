from __future__ import annotations

from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.validation import validate_result_entry


KM_CURVE_COLUMNS = ("time", "survival_probability", "group", "at_risk", "events", "censored", "time_unit", "warnings")
LOGRANK_COLUMNS = ("group_a", "group_b", "test_statistic", "p_value", "method", "event_count_group_a", "event_count_group_b", "sample_count_group_a", "sample_count_group_b", "warnings")


def validate_km_result_tables(km_curve_rows: list[dict[str, Any]], logrank_rows: list[dict[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if not km_curve_rows:
        blockers.append("missing_km_curve_table")
    if not logrank_rows:
        blockers.append("missing_logrank_result_table")
    for index, row in enumerate(km_curve_rows):
        blockers.extend(f"km_curve_row_{index}:missing_column:{column}" for column in KM_CURVE_COLUMNS if column not in row)
        if any(column in row for column in ("hazard_ratio", "ci_lower", "ci_upper", "cox_p_value")):
            blockers.append(f"km_curve_row_{index}:cox_or_hr_field_forbidden")
    for index, row in enumerate(logrank_rows):
        blockers.extend(f"logrank_row_{index}:missing_column:{column}" for column in LOGRANK_COLUMNS if column not in row)
        for numeric in ("test_statistic", "p_value"):
            if numeric in row:
                try:
                    float(row[numeric])
                except (TypeError, ValueError):
                    blockers.append(f"logrank_row_{index}:non_numeric:{numeric}")
        if any(column in row for column in ("hazard_ratio", "ci_lower", "ci_upper", "cox_p_value")):
            blockers.append(f"logrank_row_{index}:cox_or_hr_field_forbidden")
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": warnings}


def validate_km_result_index_entry(entry: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    if semantics != "formal_computed_result":
        blockers.append(f"non_formal_semantics:{semantics}")
    if entry.get("task_type") != "survival_km_logrank":
        blockers.append("task_type_must_be_survival_km_logrank")
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
        blockers.append("formal_survival_result_has_blockers")
    if entry.get("report_ready_eligible") is True:
        blockers.append("survival_report_ready_forbidden_in_b13")
    output_artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    artifact_types = {str(item.get("artifact_type") or "") for item in output_artifacts if isinstance(item, dict)}
    if "km_curve_table" not in artifact_types:
        blockers.append("missing_km_curve_table_artifact")
    if "logrank_result_table" not in artifact_types:
        blockers.append("missing_logrank_result_table_artifact")
    if entry.get("report_artifacts"):
        blockers.append("survival_report_artifacts_forbidden_in_b13")
    text = str(entry)
    for forbidden in ("hazard_ratio", "ci_lower", "ci_upper", "cox_p_value"):
        if forbidden in text:
            blockers.append(f"forbidden_cox_or_hr_field:{forbidden}")
    base = validate_result_entry(entry)
    blockers.extend(str(item) for item in base.get("blockers", []) or [])
    warnings.extend(str(item) for item in base.get("warnings", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}
