from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics

from .risk_score_design import audit_risk_score_design


RISK_SCORE_NOMOGRAM_CONTRACT_GATE_SCHEMA_VERSION = "biomedpilot.risk_score_nomogram_contract_gate.v1"


def build_risk_score_nomogram_contract_gate(
    survival_package: dict[str, Any] | Any | None,
    clinical_variable_audit: dict[str, Any] | None,
    *,
    model_spec: dict[str, Any] | None = None,
    source_cox_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    package = survival_package.to_dict() if hasattr(survival_package, "to_dict") else dict(survival_package or {})
    audit = clinical_variable_audit if isinstance(clinical_variable_audit, dict) else {}
    spec = model_spec if isinstance(model_spec, dict) else {}
    source = source_cox_result if isinstance(source_cox_result, dict) else {}
    design = audit_risk_score_design(package, audit, model_spec=spec, source_cox_result=source)
    blockers = [str(item) for item in design.get("blockers", []) or []]
    warnings = [
        "risk_score_contract_gate_only",
        "no_risk_score_execution",
        "no_nomogram_output",
        "no_clinical_prognosis_or_treatment_advice",
        *[str(item) for item in design.get("warnings", []) or []],
    ]

    blockers.extend(_source_result_blockers(source))
    blockers.extend(_model_policy_blockers(spec))
    if not package:
        blockers.append("missing_survival_clinical_input")
    if not audit:
        blockers.append("missing_clinical_variable_audit")

    blockers = list(dict.fromkeys(blockers))
    warnings = list(dict.fromkeys(warnings))
    status = "ready_for_parameter_confirmation" if not blockers else "blocked"
    variables = [str(item) for item in spec.get("variables", []) or [] if str(item)]
    coefficient_source = spec.get("coefficient_source") if isinstance(spec.get("coefficient_source"), dict) else {}
    validation_plan = spec.get("validation_plan") if isinstance(spec.get("validation_plan"), dict) else {}

    return {
        "schema_version": RISK_SCORE_NOMOGRAM_CONTRACT_GATE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "source_survival_package_id": str(package.get("survival_package_id") or package.get("survival_clinical_input_id") or ""),
        "source_clinical_variable_audit_id": str(audit.get("clinical_variable_audit_id") or audit.get("schema_version") or ""),
        "source_cox_multivariate_result_id": str(source.get("result_id") or coefficient_source.get("source_result_id") or ""),
        "source_result_semantics": normalize_result_semantics(source.get("canonical_result_semantics") or source.get("result_semantics"), default="missing"),
        "source_result_validation_status": str(source.get("validation_status") or ""),
        "source_result_dependency_snapshot": source.get("dependency_snapshot") if isinstance(source.get("dependency_snapshot"), dict) else {},
        "source_result_parameters_manifest": source.get("parameters_manifest") if isinstance(source.get("parameters_manifest"), dict) else {},
        "candidate_variables": variables,
        "coefficient_source": coefficient_source,
        "training_validation_plan": spec.get("training_validation") if isinstance(spec.get("training_validation"), dict) else {},
        "cutoff_policy": spec.get("cutoff_strategy") if isinstance(spec.get("cutoff_strategy"), dict) else {},
        "overfitting_protection_plan": spec.get("overfitting_protection") if isinstance(spec.get("overfitting_protection"), dict) else {},
        "external_validation_plan": validation_plan.get("external_validation", ""),
        "validation_plan": validation_plan,
        "missingness_policy": spec.get("missingness_policy") if isinstance(spec.get("missingness_policy"), dict) else {},
        "scaling_policy": spec.get("scaling_policy") if isinstance(spec.get("scaling_policy"), dict) else {},
        "calibration_plan": spec.get("calibration_plan") if isinstance(spec.get("calibration_plan"), dict) else {},
        "nomogram_policy": spec.get("nomogram_policy") if isinstance(spec.get("nomogram_policy"), dict) else {},
        "interpretation_boundary": {
            "statistical_model_contract_only": True,
            "clinical_conclusion_forbidden": True,
            "prognosis_label_forbidden": True,
            "treatment_recommendation_forbidden": True,
            "ordinary_user_execution_enabled": False,
        },
        "formal_execution_enabled": False,
        "writes_result_index": False,
        "result_semantics": "contract_gate_only",
        "report_ready_eligible": False,
        "forbidden_outputs": [
            "risk_score_result",
            "high_risk_group",
            "low_risk_group",
            "nomogram",
            "calibration_curve",
            "decision_curve",
            "clinical_prognosis",
            "treatment_recommendation",
        ],
        "checks": {
            "source_is_formal_cox_multivariate": not any(item in blockers for item in ("missing_formal_cox_multivariate_result", "source_result_must_be_cox_multivariate", "source_result_must_be_formal_computed_result")),
            "source_dependency_snapshot_passed": "source_dependency_snapshot_not_passed" not in blockers,
            "source_parameters_manifest_present": "source_parameters_manifest_missing" not in blockers,
            "clinical_variables_mapped": not any(item.startswith("risk_score_variable_not_in_clinical_audit:") for item in blockers),
            "training_validation_declared": "training_validation_plan_missing" not in blockers,
            "cutoff_policy_declared": "cutoff_strategy_missing" not in blockers and "cutoff_policy_missing" not in blockers,
            "missingness_policy_declared": "missingness_policy_missing" not in blockers,
            "scaling_policy_declared": "scaling_policy_missing" not in blockers,
            "calibration_plan_declared": "calibration_plan_missing" not in blockers,
            "nomogram_policy_declared": "nomogram_policy_missing" not in blockers,
            "no_execution": True,
            "no_result_index_write": True,
        },
        "design_audit": design,
        "blockers": blockers,
        "warnings": warnings,
    }


def _source_result_blockers(source: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not source:
        return ["missing_formal_cox_multivariate_result"]
    semantics = normalize_result_semantics(source.get("canonical_result_semantics") or source.get("result_semantics"), default="")
    if source.get("task_type") != "cox_multivariate":
        blockers.append("source_result_must_be_cox_multivariate")
    if semantics != "formal_computed_result":
        blockers.append("source_result_must_be_formal_computed_result")
    if source.get("validation_status") not in {"passed", "warning"}:
        blockers.append("source_result_validation_not_passed")
    if source.get("blockers"):
        blockers.append("source_result_has_blockers")
    dependency = source.get("dependency_snapshot") if isinstance(source.get("dependency_snapshot"), dict) else {}
    if dependency.get("status") != "passed":
        blockers.append("source_dependency_snapshot_not_passed")
    if not isinstance(source.get("parameters_manifest"), dict) or not source.get("parameters_manifest"):
        blockers.append("source_parameters_manifest_missing")
    if not source.get("log_artifacts"):
        blockers.append("source_task_run_log_missing")
    artifact_types = {
        str(item.get("artifact_type") or "")
        for item in source.get("output_artifacts", []) or []
        if isinstance(item, dict)
    }
    if "cox_multivariate_result_table" not in artifact_types:
        blockers.append("source_cox_multivariate_result_table_missing")
    return blockers


def _model_policy_blockers(spec: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(spec.get("missingness_policy"), dict) or not spec.get("missingness_policy"):
        blockers.append("missingness_policy_missing")
    if not isinstance(spec.get("scaling_policy"), dict) or not spec.get("scaling_policy"):
        blockers.append("scaling_policy_missing")
    if not isinstance(spec.get("calibration_plan"), dict) or not spec.get("calibration_plan"):
        blockers.append("calibration_plan_missing")
    if not isinstance(spec.get("nomogram_policy"), dict) or not spec.get("nomogram_policy"):
        blockers.append("nomogram_policy_missing")
    cutoff = spec.get("cutoff_strategy") if isinstance(spec.get("cutoff_strategy"), dict) else {}
    cutoff_policy = str(cutoff.get("policy") or "").lower()
    if cutoff_policy in {"optimal_cutpoint", "data_driven_cutpoint", "median_from_all_data", "maxstat"}:
        blockers.append("cutoff_policy_data_leakage_risk")
    validation = spec.get("validation_plan") if isinstance(spec.get("validation_plan"), dict) else {}
    if validation.get("external_validation_required") and not validation.get("external_validation"):
        blockers.append("external_validation_required_but_missing")
    for key in ("clinical_conclusion", "prognosis_label", "treatment_recommendation", "diagnosis", "clinical_risk_group"):
        if spec.get(key):
            blockers.append(f"forbidden_clinical_output_requested:{key}")
    return blockers
