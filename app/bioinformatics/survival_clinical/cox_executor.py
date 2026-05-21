from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result

from ._io import asset_path, event_observed, parse_float, read_table, sample_id, write_table
from .cox_confirmation import validate_cox_univariate_confirmation
from .cox_result_schema import COX_RESULT_COLUMNS, validate_cox_result_index_entry, validate_cox_result_table


ENGINE_NAME = "biomedpilot_controlled_cox_univariate"
ENGINE_VERSION = "0.1.0"


def run_controlled_cox_univariate(project_root: str | Path, parameter_manifest: dict[str, Any], confirmation: dict[str, Any]) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    blockers: list[str] = []
    warnings = list(dict.fromkeys([*(parameter_manifest.get("warnings", []) or []), "proportional_hazards_assumption_not_formally_tested"]))
    if parameter_manifest.get("status") != "passed":
        blockers.extend(str(item) for item in parameter_manifest.get("blockers", []) or ["cox_parameter_manifest_not_passed"])
    confirmation_gate = validate_cox_univariate_confirmation(confirmation, parameter_manifest)
    if confirmation_gate.get("status") != "passed":
        blockers.extend(str(item) for item in confirmation_gate.get("blockers", []) or [])
    dependency = parameter_manifest.get("dependency_snapshot") if isinstance(parameter_manifest.get("dependency_snapshot"), dict) else {}
    if dependency.get("status") != "passed":
        blockers.append("dependency_snapshot_not_passed")
    output_plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
    task_run_id = str(output_plan.get("task_run_id") or f"task-run-cox-{_now_compact()}")
    result_id = str(output_plan.get("result_id") or f"cox-uni-{_now_compact()}")
    log_path = root / str(output_plan.get("task_run_log_path") or f"analysis/survival_cox/{result_id}_run_log.json")
    table_path = root / str(output_plan.get("cox_result_table_path") or f"results/tables/survival/{result_id}_cox.tsv")
    if blockers:
        _write_json(log_path, _task_log(task_run_id, parameter_manifest, dependency, "blocked", "", "", warnings, blockers, "cox_univariate_gates_not_passed"))
        return {"status": "blocked", "result_id": "", "task_run_id": task_run_id, "warnings": warnings, "blockers": list(dict.fromkeys(blockers)), "failure_reason": "cox_univariate_gates_not_passed", "task_run_log_path": str(log_path)}

    rows = read_table(str(parameter_manifest.get("provenance", {}).get("clinical_asset_path") or ""))
    observations = _observations(rows, parameter_manifest)
    if len(observations) < int(parameter_manifest.get("minimum_non_missing_count") or 4):
        blockers.append("too_few_non_missing_values")
    if sum(1 for item in observations if item["event"]) < int(parameter_manifest.get("minimum_event_count") or 3):
        blockers.append("minimum_event_count_not_met")
    cox_row = _cox_row(observations, parameter_manifest) if not blockers else {}
    validation = validate_cox_result_table([cox_row] if cox_row else [])
    blockers.extend(str(item) for item in validation.get("blockers", []) or [])
    if blockers:
        _write_json(log_path, _task_log(task_run_id, parameter_manifest, dependency, "failed", str(table_path), "", warnings, blockers, "cox_univariate_runtime_validation_failed"))
        return {"status": "blocked", "result_id": "", "task_run_id": task_run_id, "warnings": warnings, "blockers": list(dict.fromkeys(blockers)), "failure_reason": "cox_univariate_runtime_validation_failed", "task_run_log_path": str(log_path)}

    write_table(table_path, [cox_row], list(COX_RESULT_COLUMNS))
    _write_json(log_path, _task_log(task_run_id, parameter_manifest, dependency, "succeeded", str(table_path), "results/summaries/result_index.json", warnings, [], ""))
    entry = ResultIndexEntry(
        result_id=result_id,
        task_run_id=task_run_id,
        task_type="cox_univariate",
        result_semantics="formal_computed_result",
        input_package_id=str(parameter_manifest.get("survival_clinical_input_id") or ""),
        source_dataset_id=str(parameter_manifest.get("survival_clinical_input_id") or ""),
        source_repository_manifest="B12 survival input package",
        parameters_manifest=dict(parameter_manifest),
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        dependency_snapshot=dict(dependency),
        output_artifacts=({"artifact_type": "cox_result_table", "path": str(table_path), "required_columns": list(COX_RESULT_COLUMNS)},),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=tuple(warnings),
        blockers=(),
        log_artifacts=({"artifact_type": "task_run_log", "path": str(log_path)},),
        report_ready_eligible=False,
    ).to_dict()
    entry["survival_clinical_input_id"] = str(parameter_manifest.get("survival_clinical_input_id") or "")
    entry["survival_outcome_gate_id"] = str(parameter_manifest.get("survival_outcome_gate_id") or "")
    schema_gate = validate_cox_result_index_entry(entry)
    if schema_gate.get("status") != "passed":
        entry["validation_status"] = "blocked"
        entry["blockers"] = list(schema_gate.get("blockers", []) or [])
    registered = register_result(root, entry)
    return {"status": "passed" if not registered.get("blockers") else "blocked", "result_id": result_id, "task_run_id": task_run_id, "cox_result_table": str(table_path), "task_run_log_path": str(log_path), "result": registered, "warnings": warnings, "blockers": list(registered.get("blockers", []) or [])}


def _observations(rows: list[dict[str, str]], parameter_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    covariate = str(parameter_manifest.get("covariate") or "")
    cov_type = str(parameter_manifest.get("covariate_type") or "")
    values = [str(row.get(covariate) or "").strip() for row in rows if str(row.get(covariate) or "").strip()]
    categories = sorted(set(values))
    reference = categories[0] if categories else ""
    time_field = str(parameter_manifest.get("time_field") or "")
    event_field = str(parameter_manifest.get("event_field") or "")
    event_coding = parameter_manifest.get("event_coding") if isinstance(parameter_manifest.get("event_coding"), dict) else {}
    observations: list[dict[str, Any]] = []
    for row in rows:
        sid = sample_id(row)
        time = parse_float(row.get(time_field))
        event = event_observed(row.get(event_field), event_coding)
        raw_value = str(row.get(covariate) or "").strip()
        if not sid or time is None or event is None or raw_value == "":
            continue
        if cov_type in {"binary_variable", "categorical_variable"}:
            encoded = 0.0 if raw_value == reference else 1.0
        else:
            parsed = parse_float(raw_value)
            if parsed is None:
                continue
            encoded = parsed
        observations.append({"sample_id": sid, "time": float(time), "event": bool(event), "x": float(encoded)})
    return observations


def _cox_row(observations: list[dict[str, Any]], parameter_manifest: dict[str, Any]) -> dict[str, Any]:
    beta, se, z_value, p_value = _fit_univariate_cox(observations)
    hazard_ratio = math.exp(beta)
    ci_lower = math.exp(beta - 1.96 * se)
    ci_upper = math.exp(beta + 1.96 * se)
    return {
        "covariate": parameter_manifest.get("covariate", ""),
        "covariate_label": parameter_manifest.get("covariate_label", ""),
        "covariate_type": parameter_manifest.get("covariate_type", ""),
        "hazard_ratio": hazard_ratio,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "p_value": p_value,
        "z_statistic": z_value,
        "sample_count": len(observations),
        "event_count": sum(1 for item in observations if item["event"]),
        "non_missing_count": len(observations),
        "missing_count": parameter_manifest.get("missing_count", 0),
        "method": "single_variable_cox_partial_likelihood_breslow_ties",
        "warnings": "proportional_hazards_assumption_not_formally_tested; not_clinical_conclusion",
    }


def _fit_univariate_cox(observations: list[dict[str, Any]]) -> tuple[float, float, float, float]:
    beta = 0.0
    for _ in range(40):
        score, info = _score_info(observations, beta)
        if info <= 1e-12:
            break
        step = max(min(score / info, 1.0), -1.0)
        beta += step
        if abs(step) < 1e-8:
            break
    _, info = _score_info(observations, beta)
    se = (1.0 / info) ** 0.5 if info > 1e-12 else 1e6
    z_value = beta / se if se else 0.0
    p_value = math.erfc(abs(z_value) / math.sqrt(2.0))
    return beta, se, z_value, p_value


def _score_info(observations: list[dict[str, Any]], beta: float) -> tuple[float, float]:
    score = 0.0
    info = 0.0
    for time in sorted({item["time"] for item in observations if item["event"]}):
        events = [item for item in observations if item["time"] == time and item["event"]]
        risk = [item for item in observations if item["time"] >= time]
        weights = [math.exp(beta * item["x"]) for item in risk]
        total = sum(weights)
        if not total:
            continue
        mean_x = sum(weight * item["x"] for weight, item in zip(weights, risk)) / total
        mean_x2 = sum(weight * item["x"] * item["x"] for weight, item in zip(weights, risk)) / total
        variance = max(mean_x2 - mean_x * mean_x, 0.0)
        score += sum(item["x"] for item in events) - len(events) * mean_x
        info += len(events) * variance
    return score, info


def _task_log(task_run_id: str, parameter_manifest: dict[str, Any], dependency: dict[str, Any], status: str, table_path: str, index_path: str, warnings: list[str], blockers: list[str], failure_reason: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "schema_version": "biomedpilot.cox_univariate_task_run_log.v1",
        "task_run_id": task_run_id,
        "survival_clinical_input_id": parameter_manifest.get("survival_clinical_input_id", ""),
        "survival_outcome_gate_id": parameter_manifest.get("survival_outcome_gate_id", ""),
        "cox_parameter_id": parameter_manifest.get("cox_parameter_id", ""),
        "dependency_snapshot": dependency,
        "status": status,
        "started_at": now,
        "finished_at": now,
        "cox_result_table": table_path,
        "result_index_path": index_path,
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
        "failure_reason": failure_reason,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
