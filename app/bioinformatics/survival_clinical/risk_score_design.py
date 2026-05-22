from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


RISK_SCORE_DESIGN_SCHEMA_VERSION = "biomedpilot.risk_score_design_audit.v1"


def audit_risk_score_design(
    survival_package: dict[str, Any] | Any | None,
    clinical_variable_audit: dict[str, Any] | None,
    *,
    model_spec: dict[str, Any] | None = None,
    source_cox_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    package = survival_package.to_dict() if hasattr(survival_package, "to_dict") else dict(survival_package or {})
    audit = clinical_variable_audit if isinstance(clinical_variable_audit, dict) else {}
    spec = model_spec if isinstance(model_spec, dict) else {}
    cox_result = source_cox_result if isinstance(source_cox_result, dict) else {}
    variable_mapping = audit.get("variable_mapping") if isinstance(audit.get("variable_mapping"), dict) else {}
    variables = [str(item) for item in spec.get("variables", []) or [] if str(item)]
    blockers: list[str] = []
    warnings: list[str] = ["risk_score_design_audit_only", "no_high_low_risk_grouping", "no_clinical_prognosis_or_treatment_advice"]

    if not package:
        blockers.append("missing_survival_input")
    if package.get("blockers"):
        blockers.extend(str(item) for item in package.get("blockers", []) or [])
    if not variables:
        blockers.append("risk_score_variables_missing")
    for variable in variables:
        if variable not in variable_mapping:
            blockers.append(f"risk_score_variable_not_in_clinical_audit:{variable}")
    training_validation = spec.get("training_validation") if isinstance(spec.get("training_validation"), dict) else {}
    if not training_validation:
        blockers.append("training_validation_plan_missing")
    else:
        if not training_validation.get("training_set"):
            blockers.append("training_set_missing")
        if not training_validation.get("validation_set"):
            blockers.append("validation_set_missing")
    if not spec.get("model_formula"):
        blockers.append("model_formula_missing")
    coefficient_source = spec.get("coefficient_source") if isinstance(spec.get("coefficient_source"), dict) else {}
    if not coefficient_source:
        blockers.append("coefficient_source_missing")
    elif not coefficient_source.get("source_result_id") and not coefficient_source.get("source_manifest_path"):
        blockers.append("coefficient_source_provenance_missing")
    cutoff_strategy = spec.get("cutoff_strategy") if isinstance(spec.get("cutoff_strategy"), dict) else {}
    if not cutoff_strategy:
        blockers.append("cutoff_strategy_missing")
    elif not cutoff_strategy.get("policy"):
        blockers.append("cutoff_policy_missing")
    overfitting = spec.get("overfitting_protection") if isinstance(spec.get("overfitting_protection"), dict) else {}
    if not overfitting:
        blockers.append("overfitting_protection_missing")
    elif not (overfitting.get("cross_validation") or overfitting.get("external_validation")):
        blockers.append("cross_validation_or_external_validation_missing")
    validation_plan = spec.get("validation_plan") if isinstance(spec.get("validation_plan"), dict) else {}
    if not validation_plan:
        blockers.append("risk_score_validation_plan_missing")
    elif not (validation_plan.get("cross_validation") or validation_plan.get("external_validation")):
        blockers.append("risk_score_validation_not_declared")
    if cox_result:
        if str(cox_result.get("task_type") or "") != "cox_multivariate":
            blockers.append("source_result_must_be_cox_multivariate")
        if str(cox_result.get("result_semantics") or "") != "formal_computed_result":
            blockers.append("source_result_must_be_formal_computed_result")
        if cox_result.get("report_ready_eligible") is True:
            warnings.append("source_result_report_ready_does_not_make_risk_score_report_ready")

    blockers = list(dict.fromkeys(blockers))
    return {
        "schema_version": RISK_SCORE_DESIGN_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "design_audit_ready",
        "risk_score_design_id": _design_id(package, variables, spec),
        "survival_clinical_input_id": str(package.get("survival_package_id") or package.get("survival_clinical_input_id") or ""),
        "variables": variables,
        "variable_source": {
            "source": "B12 clinical variable audit / B20 Cox multivariate result provenance",
            "clinical_variable_audit_schema": str(audit.get("schema_version") or ""),
            "source_result_id": str(cox_result.get("result_id") or coefficient_source.get("source_result_id") or ""),
        },
        "model_formula": str(spec.get("model_formula") or ""),
        "coefficient_source": coefficient_source,
        "cutoff_strategy": cutoff_strategy,
        "training_validation": training_validation,
        "overfitting_protection": overfitting,
        "validation_plan": validation_plan,
        "formal_execution_enabled": False,
        "writes_result_index": False,
        "result_semantics": "design_audit_only",
        "report_ready_eligible": False,
        "forbidden_outputs": ["risk_score_result", "high_risk_group", "low_risk_group", "nomogram", "clinical_prognosis", "treatment_recommendation"],
        "interpretation_boundary": {
            "statistical_design_only": True,
            "clinical_conclusion_forbidden": True,
            "prognosis_label_forbidden": True,
            "treatment_recommendation_forbidden": True,
        },
        "provenance": {
            "raw_recognition_report_used": False,
            "ui_temp_table_used": False,
            "automatic_variable_selection": False,
            "risk_score_generated": False,
            "nomogram_generated": False,
            "clinical_risk_group_generated": False,
        },
        "blockers": blockers,
        "warnings": list(dict.fromkeys(warnings)),
    }


def _design_id(package: dict[str, Any], variables: list[str], spec: dict[str, Any]) -> str:
    seed = "|".join([str(package.get("survival_package_id") or ""), *variables, str(spec.get("model_formula") or "")])
    return f"risk-score-design-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"
