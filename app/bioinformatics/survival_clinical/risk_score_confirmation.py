from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RISK_SCORE_CONFIRMATION_SCHEMA_VERSION = "biomedpilot.risk_score_parameter_confirmation.v1"
RISK_SCORE_CONFIRMATION_GATE_SCHEMA_VERSION = "biomedpilot.risk_score_parameter_confirmation_gate.v1"
RISK_SCORE_CONFIRMATION_PATH = Path("manifests") / "risk_score_parameter_confirmation.json"


def confirm_risk_score_parameters(
    project_root: str | Path,
    contract_gate: dict[str, Any],
    *,
    confirmed_by_user: bool = True,
    reviewer_id: str = "",
) -> dict[str, Any]:
    contract = dict(contract_gate or {})
    digest = _contract_digest(contract)
    source_result_id = str(contract.get("source_cox_multivariate_result_id") or "")
    result_id = f"risk-score-{digest[:10]}"
    output_plan = {
        "task_run_id": f"task-run-risk-score-{digest[:10]}",
        "result_id": result_id,
        "risk_score_result_table_path": f"results/tables/survival/{result_id}_risk_score.tsv",
        "task_run_log_path": f"analysis/survival_risk_score/{result_id}_run_log.json",
        "result_index_registry_path": "results/summaries/result_index.json",
    }
    blockers: list[str] = []
    if contract.get("status") != "ready_for_parameter_confirmation":
        blockers.append("risk_score_contract_gate_not_ready")
    if not confirmed_by_user:
        blockers.append("risk_score_parameters_not_user_confirmed")
    blockers.extend(_required_contract_field_blockers(contract))
    if not _boundary_acknowledged(contract):
        blockers.append("risk_score_clinical_boundary_not_acknowledged")

    payload = {
        "schema_version": RISK_SCORE_CONFIRMATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "confirmed",
        "confirmation_semantics": "user_confirmed_risk_score_parameters_schema_only_no_execution",
        "confirmed_by_user": confirmed_by_user and not blockers,
        "reviewer_id": str(reviewer_id or ""),
        "risk_score_contract_gate_digest": digest,
        "risk_score_contract_gate": contract,
        "source_survival_package_id": str(contract.get("source_survival_package_id") or ""),
        "source_clinical_variable_audit_id": str(contract.get("source_clinical_variable_audit_id") or ""),
        "source_cox_multivariate_result_id": source_result_id,
        "candidate_variables": list(contract.get("candidate_variables") or []),
        "coefficient_source": dict(contract.get("coefficient_source") or {}),
        "cutoff_policy": dict(contract.get("cutoff_policy") or {}),
        "missingness_policy": dict(contract.get("missingness_policy") or {}),
        "scaling_policy": dict(contract.get("scaling_policy") or {}),
        "calibration_plan": dict(contract.get("calibration_plan") or {}),
        "nomogram_policy": dict(contract.get("nomogram_policy") or {}),
        "training_validation_plan": dict(contract.get("training_validation_plan") or {}),
        "validation_plan": dict(contract.get("validation_plan") or {}),
        "source_dependency_snapshot": dict(contract.get("source_result_dependency_snapshot") or {}),
        "source_parameters_manifest": dict(contract.get("source_result_parameters_manifest") or {}),
        "interpretation_boundary_acknowledged": _boundary_acknowledged(contract),
        "output_plan": output_plan,
        "formal_execution_enabled": False,
        "writes_result_index": False,
        "result_semantics": "parameter_confirmation_only",
        "report_ready_eligible": False,
        "forbidden_outputs": list(contract.get("forbidden_outputs") or []),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys([*(contract.get("warnings") or []), "risk_score_confirmation_schema_only_no_execution"])),
    }
    path = Path(project_root).expanduser().resolve() / RISK_SCORE_CONFIRMATION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def load_risk_score_parameter_confirmation(project_root: str | Path) -> dict[str, Any]:
    path = Path(project_root).expanduser().resolve() / RISK_SCORE_CONFIRMATION_PATH
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def validate_risk_score_parameter_confirmation(
    confirmation: dict[str, Any] | None,
    contract_gate: dict[str, Any],
) -> dict[str, Any]:
    payload = dict(confirmation or {})
    contract = dict(contract_gate or {})
    blockers: list[str] = []
    warnings: list[str] = []
    if not payload:
        blockers.append("risk_score_parameter_confirmation_missing")
        return _gate(blockers, warnings)
    if payload.get("schema_version") != RISK_SCORE_CONFIRMATION_SCHEMA_VERSION:
        blockers.append("risk_score_confirmation_schema_mismatch")
    if payload.get("status") != "confirmed" or payload.get("confirmed_by_user") is not True:
        blockers.append("risk_score_parameters_not_user_confirmed")
    if payload.get("risk_score_contract_gate_digest") != _contract_digest(contract):
        blockers.append("risk_score_confirmation_contract_mismatch")
    if contract.get("status") != "ready_for_parameter_confirmation":
        blockers.append("risk_score_contract_gate_not_ready")
    blockers.extend(_required_contract_field_blockers(contract))
    if payload.get("interpretation_boundary_acknowledged") is not True:
        blockers.append("risk_score_clinical_boundary_not_acknowledged")
    if payload.get("formal_execution_enabled") is not False:
        blockers.append("risk_score_confirmation_must_not_enable_execution")
    if payload.get("writes_result_index") is not False:
        blockers.append("risk_score_confirmation_must_not_write_result_index")
    if payload.get("report_ready_eligible") is not False:
        blockers.append("risk_score_confirmation_must_not_be_report_ready")
    output_plan = payload.get("output_plan") if isinstance(payload.get("output_plan"), dict) else {}
    for field_name in ("task_run_id", "result_id", "risk_score_result_table_path", "task_run_log_path", "result_index_registry_path"):
        if not output_plan.get(field_name):
            blockers.append(f"risk_score_confirmation_missing_output_plan:{field_name}")
    warnings.extend(str(item) for item in payload.get("warnings", []) or [])
    return _gate(blockers, warnings)


def _required_contract_field_blockers(contract: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not contract.get("source_survival_package_id"):
        blockers.append("missing_source_survival_package_id")
    if not contract.get("source_clinical_variable_audit_id"):
        blockers.append("missing_source_clinical_variable_audit_id")
    if not contract.get("source_cox_multivariate_result_id"):
        blockers.append("missing_source_cox_multivariate_result_id")
    if not contract.get("candidate_variables"):
        blockers.append("missing_candidate_variables")
    for field_name in (
        "coefficient_source",
        "cutoff_policy",
        "missingness_policy",
        "scaling_policy",
        "calibration_plan",
        "nomogram_policy",
        "training_validation_plan",
        "validation_plan",
    ):
        if not isinstance(contract.get(field_name), dict) or not contract.get(field_name):
            blockers.append(f"missing_{field_name}")
    if (contract.get("source_result_dependency_snapshot") or {}).get("status") != "passed":
        blockers.append("source_dependency_snapshot_not_passed")
    if not isinstance(contract.get("source_result_parameters_manifest"), dict) or not contract.get("source_result_parameters_manifest"):
        blockers.append("source_parameters_manifest_missing")
    return blockers


def _boundary_acknowledged(contract: dict[str, Any]) -> bool:
    boundary = contract.get("interpretation_boundary") if isinstance(contract.get("interpretation_boundary"), dict) else {}
    return (
        boundary.get("statistical_model_contract_only") is True
        and boundary.get("clinical_conclusion_forbidden") is True
        and boundary.get("prognosis_label_forbidden") is True
        and boundary.get("treatment_recommendation_forbidden") is True
        and boundary.get("ordinary_user_execution_enabled") is False
    )


def _contract_digest(contract_gate: dict[str, Any]) -> str:
    stable_contract = _strip_volatile_fields(contract_gate)
    stable = json.dumps(stable_contract, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(stable.encode("utf-8")).hexdigest()


def _strip_volatile_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _strip_volatile_fields(item) for key, item in value.items() if key not in {"created_at", "updated_at"}}
    if isinstance(value, list):
        return [_strip_volatile_fields(item) for item in value]
    return value


def _gate(blockers: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "schema_version": RISK_SCORE_CONFIRMATION_GATE_SCHEMA_VERSION,
        "status": "blocked" if blockers else "passed",
        "gate_semantics": "risk_score_user_parameter_confirmation_required_but_execution_disabled",
        "formal_execution_enabled": False,
        "writes_result_index": False,
        "report_ready_eligible": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }
