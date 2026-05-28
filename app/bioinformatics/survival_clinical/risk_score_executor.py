from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result

from ._io import parse_float, read_table, sample_id, write_table
from .risk_score_confirmation import validate_risk_score_parameter_confirmation
from .risk_score_result_schema import RISK_SCORE_RESULT_COLUMNS, validate_risk_score_result_index_entry, validate_risk_score_result_table


ENGINE_NAME = "biomedpilot_controlled_risk_score"
ENGINE_VERSION = "0.1.0"


def run_controlled_risk_score(project_root: str | Path, contract_gate: dict[str, Any], confirmation: dict[str, Any]) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    contract = dict(contract_gate or {})
    confirmed = dict(confirmation or {})
    warnings = list(dict.fromkeys([*(contract.get("warnings") or []), *(confirmed.get("warnings") or []), "risk_score_statistical_result_only", "no_group_labels_or_clinical_advice"]))
    blockers: list[str] = []
    if contract.get("status") != "ready_for_parameter_confirmation":
        blockers.append("risk_score_contract_gate_not_ready")
    confirmation_gate = validate_risk_score_parameter_confirmation(confirmed, contract)
    if confirmation_gate.get("status") != "passed":
        blockers.extend(str(item) for item in confirmation_gate.get("blockers", []) or [])
    source_dependency = confirmed.get("source_dependency_snapshot") if isinstance(confirmed.get("source_dependency_snapshot"), dict) else {}
    if source_dependency.get("status") != "passed":
        blockers.append("source_dependency_snapshot_not_passed")

    output_plan = confirmed.get("output_plan") if isinstance(confirmed.get("output_plan"), dict) else {}
    task_run_id = str(output_plan.get("task_run_id") or f"task-run-risk-score-{_now_compact()}")
    result_id = str(output_plan.get("result_id") or f"risk-score-{_now_compact()}")
    log_path = root / str(output_plan.get("task_run_log_path") or f"analysis/survival_risk_score/{result_id}_run_log.json")
    table_path = root / str(output_plan.get("risk_score_result_table_path") or f"results/tables/survival/{result_id}_risk_score.tsv")

    clinical_path = str((confirmed.get("source_parameters_manifest") or {}).get("provenance", {}).get("clinical_asset_path") or "")
    cox_table_path = _source_cox_result_table_path(root, contract)
    if not clinical_path:
        blockers.append("risk_score_clinical_asset_path_missing")
    if not cox_table_path:
        blockers.append("source_cox_multivariate_result_table_missing")
    if blockers:
        _write_json(log_path, _task_log(task_run_id, contract, confirmed, source_dependency, "blocked", "", "", warnings, blockers, "risk_score_gates_not_passed"))
        return {"status": "blocked", "result_id": "", "task_run_id": task_run_id, "warnings": warnings, "blockers": list(dict.fromkeys(blockers)), "failure_reason": "risk_score_gates_not_passed", "task_run_log_path": str(log_path)}

    coefficients = _coefficients_from_cox_table(cox_table_path)
    variables = [str(item) for item in confirmed.get("candidate_variables", []) or [] if str(item)]
    missing_coefficients = [name for name in variables if name not in coefficients]
    if missing_coefficients:
        blockers.extend(f"missing_cox_coefficient:{name}" for name in missing_coefficients)
    clinical_rows = read_table(clinical_path)
    if not clinical_rows:
        blockers.append("risk_score_clinical_table_missing_or_empty")
    risk_rows = _risk_score_rows(clinical_rows, variables, coefficients, confirmed, contract) if not blockers else []
    validation = validate_risk_score_result_table(risk_rows)
    blockers.extend(str(item) for item in validation.get("blockers", []) or [])
    if blockers:
        _write_json(log_path, _task_log(task_run_id, contract, confirmed, source_dependency, "failed", str(table_path), "", warnings, blockers, "risk_score_runtime_validation_failed"))
        return {"status": "blocked", "result_id": "", "task_run_id": task_run_id, "warnings": warnings, "blockers": list(dict.fromkeys(blockers)), "failure_reason": "risk_score_runtime_validation_failed", "task_run_log_path": str(log_path)}

    write_table(table_path, risk_rows, list(RISK_SCORE_RESULT_COLUMNS))
    _write_json(log_path, _task_log(task_run_id, contract, confirmed, source_dependency, "succeeded", str(table_path), "results/summaries/result_index.json", warnings, [], ""))
    entry = ResultIndexEntry(
        result_id=result_id,
        task_run_id=task_run_id,
        task_type="risk_score",
        result_semantics="formal_computed_result",
        input_package_id=str(confirmed.get("source_survival_package_id") or contract.get("source_survival_package_id") or ""),
        source_dataset_id=str(confirmed.get("source_survival_package_id") or contract.get("source_survival_package_id") or ""),
        source_repository_manifest="B12 survival input package / B32 risk score contract gate",
        parameters_manifest=dict(confirmed.get("risk_score_contract_gate") or contract),
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        dependency_snapshot=dict(source_dependency),
        output_artifacts=({"artifact_type": "risk_score_result_table", "path": str(table_path), "required_columns": list(RISK_SCORE_RESULT_COLUMNS)},),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=tuple(warnings),
        blockers=(),
        log_artifacts=({"artifact_type": "task_run_log", "path": str(log_path)},),
        report_ready_eligible=False,
    ).to_dict()
    entry["risk_score_parameter_confirmation"] = confirmed
    entry["source_cox_multivariate_result_id"] = str(confirmed.get("source_cox_multivariate_result_id") or contract.get("source_cox_multivariate_result_id") or "")
    schema_gate = validate_risk_score_result_index_entry(entry)
    if schema_gate.get("status") != "passed":
        entry["validation_status"] = "blocked"
        entry["blockers"] = list(schema_gate.get("blockers", []) or [])
    registered = register_result(root, entry)
    return {
        "status": "passed" if not registered.get("blockers") else "blocked",
        "result_id": result_id,
        "task_run_id": task_run_id,
        "risk_score_result_table": str(table_path),
        "task_run_log_path": str(log_path),
        "result": registered,
        "warnings": warnings,
        "blockers": list(registered.get("blockers", []) or []),
    }


def _source_cox_result_table_path(root: Path, contract: dict[str, Any]) -> str:
    artifacts = contract.get("source_result_output_artifacts") if isinstance(contract.get("source_result_output_artifacts"), list) else []
    for artifact in artifacts:
        if not isinstance(artifact, dict) or artifact.get("artifact_type") != "cox_multivariate_result_table":
            continue
        path = Path(str(artifact.get("path") or ""))
        candidate = path if path.is_absolute() else root / path
        if candidate.is_file():
            return str(candidate)
    return ""


def _coefficients_from_cox_table(path: str) -> dict[str, float]:
    coefficients: dict[str, float] = {}
    for row in read_table(path):
        covariate = str(row.get("covariate") or "").strip()
        hazard_ratio = parse_float(row.get("hazard_ratio"))
        if covariate and hazard_ratio is not None and hazard_ratio > 0:
            coefficients[covariate] = math.log(hazard_ratio)
    return coefficients


def _risk_score_rows(
    clinical_rows: list[dict[str, str]],
    variables: list[str],
    coefficients: dict[str, float],
    confirmation: dict[str, Any],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    source_parameters = confirmation.get("source_parameters_manifest") if isinstance(confirmation.get("source_parameters_manifest"), dict) else {}
    specs = source_parameters.get("covariate_specs") if isinstance(source_parameters.get("covariate_specs"), dict) else {}
    references = _category_references(clinical_rows, variables)
    rows: list[dict[str, Any]] = []
    for row in clinical_rows:
        sid = sample_id(row)
        if not sid:
            continue
        score = 0.0
        valid = True
        for variable in variables:
            encoded = _encoded_value(row, variable, specs.get(variable) if isinstance(specs, dict) else {}, references)
            if encoded is None:
                valid = False
                break
            score += float(coefficients[variable]) * encoded
        if not valid:
            continue
        rows.append(
            {
                "sample_id": sid,
                "case_id": str(row.get("case_id") or row.get("patient_id") or row.get("participant_id") or sid),
                "risk_score": score,
                "source_cox_multivariate_result_id": str(confirmation.get("source_cox_multivariate_result_id") or contract.get("source_cox_multivariate_result_id") or ""),
                "model_formula": _model_formula(variables),
                "coefficient_source": str((confirmation.get("coefficient_source") or {}).get("source_result_id") or contract.get("source_cox_multivariate_result_id") or ""),
                "missingness_policy": json.dumps(confirmation.get("missingness_policy") or {}, ensure_ascii=False, sort_keys=True),
                "scaling_policy": json.dumps(confirmation.get("scaling_policy") or {}, ensure_ascii=False, sort_keys=True),
                "warnings": "statistical_result_only; no_group_labels_or_clinical_advice",
            }
        )
    return rows


def _encoded_value(row: dict[str, str], variable: str, spec: Any, references: dict[str, str]) -> float | None:
    raw = str(row.get(variable) or "").strip()
    if raw == "":
        return None
    variable_type = str((spec or {}).get("variable_type") or "")
    if variable_type in {"binary_variable", "categorical_variable", "ordinal_variable"}:
        return 0.0 if raw == references.get(variable, raw) else 1.0
    return parse_float(raw)


def _category_references(rows: list[dict[str, str]], variables: list[str]) -> dict[str, str]:
    references: dict[str, str] = {}
    for name in variables:
        values = sorted({str(row.get(name) or "").strip() for row in rows if str(row.get(name) or "").strip()})
        if values:
            references[name] = values[0]
    return references


def _model_formula(variables: list[str]) -> str:
    return "risk_score = " + " + ".join(f"beta_{name} * {name}" for name in variables)


def _task_log(
    task_run_id: str,
    contract: dict[str, Any],
    confirmation: dict[str, Any],
    dependency: dict[str, Any],
    status: str,
    table_path: str,
    index_path: str,
    warnings: list[str],
    blockers: list[str],
    failure_reason: str,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "schema_version": "biomedpilot.risk_score_task_run_log.v1",
        "task_run_id": task_run_id,
        "source_survival_package_id": confirmation.get("source_survival_package_id") or contract.get("source_survival_package_id", ""),
        "source_cox_multivariate_result_id": confirmation.get("source_cox_multivariate_result_id") or contract.get("source_cox_multivariate_result_id", ""),
        "dependency_snapshot": dependency,
        "status": status,
        "started_at": now,
        "finished_at": now,
        "risk_score_result_table": table_path,
        "result_index_path": index_path,
        "plot_artifacts": [],
        "report_artifacts": [],
        "report_ready_eligible": False,
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
        "failure_reason": failure_reason,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
