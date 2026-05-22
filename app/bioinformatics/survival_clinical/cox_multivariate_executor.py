from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result

from ._io import event_observed, parse_float, read_table, sample_id, write_table
from .cox_multivariate_confirmation import validate_cox_multivariate_confirmation
from .cox_multivariate_result_schema import COX_MULTIVARIATE_RESULT_COLUMNS, validate_cox_multivariate_result_index_entry, validate_cox_multivariate_result_table


ENGINE_NAME = "biomedpilot_controlled_cox_multivariate"
ENGINE_VERSION = "0.1.0"


def run_controlled_cox_multivariate(project_root: str | Path, parameter_manifest: dict[str, Any], confirmation: dict[str, Any]) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    blockers: list[str] = []
    warnings = list(dict.fromkeys([*(parameter_manifest.get("warnings", []) or []), "proportional_hazards_assumption_not_formally_tested", "not_clinical_conclusion"]))
    if parameter_manifest.get("status") != "passed":
        blockers.extend(str(item) for item in parameter_manifest.get("blockers", []) or ["cox_multivariate_parameter_manifest_not_passed"])
    confirmation_gate = validate_cox_multivariate_confirmation(confirmation, parameter_manifest)
    if confirmation_gate.get("status") != "passed":
        blockers.extend(str(item) for item in confirmation_gate.get("blockers", []) or [])
    dependency = parameter_manifest.get("dependency_snapshot") if isinstance(parameter_manifest.get("dependency_snapshot"), dict) else {}
    if dependency.get("status") != "passed":
        blockers.append("dependency_snapshot_not_passed")
    output_plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
    task_run_id = str(output_plan.get("task_run_id") or f"task-run-cox-mv-{_now_compact()}")
    result_id = str(output_plan.get("result_id") or f"cox-mv-{_now_compact()}")
    log_path = root / str(output_plan.get("task_run_log_path") or f"analysis/survival_cox/{result_id}_run_log.json")
    table_path = root / str(output_plan.get("cox_result_table_path") or f"results/tables/survival/{result_id}_cox_multivariate.tsv")
    if blockers:
        _write_json(log_path, _task_log(task_run_id, parameter_manifest, dependency, "blocked", "", "", warnings, blockers, "cox_multivariate_gates_not_passed"))
        return {"status": "blocked", "result_id": "", "task_run_id": task_run_id, "warnings": warnings, "blockers": list(dict.fromkeys(blockers)), "failure_reason": "cox_multivariate_gates_not_passed", "task_run_log_path": str(log_path)}

    rows = read_table(str(parameter_manifest.get("provenance", {}).get("clinical_asset_path") or ""))
    observations = _observations(rows, parameter_manifest)
    if len(observations) < int(parameter_manifest.get("minimum_sample_count") or 12):
        blockers.append("minimum_sample_count_not_met")
    if sum(1 for item in observations if item["event"]) < int(parameter_manifest.get("minimum_event_count") or 10):
        blockers.append("minimum_event_count_not_met")
    fit = _fit_multivariate_cox(observations, len(parameter_manifest.get("selected_covariates", []) or [])) if not blockers else {"blockers": blockers}
    blockers.extend(str(item) for item in fit.get("blockers", []) or [])
    cox_rows = _cox_rows(fit, observations, parameter_manifest) if not blockers else []
    validation = validate_cox_multivariate_result_table(cox_rows)
    blockers.extend(str(item) for item in validation.get("blockers", []) or [])
    if blockers:
        _write_json(log_path, _task_log(task_run_id, parameter_manifest, dependency, "failed", str(table_path), "", warnings, blockers, "cox_multivariate_runtime_validation_failed"))
        return {"status": "blocked", "result_id": "", "task_run_id": task_run_id, "warnings": warnings, "blockers": list(dict.fromkeys(blockers)), "failure_reason": "cox_multivariate_runtime_validation_failed", "task_run_log_path": str(log_path)}

    write_table(table_path, cox_rows, list(COX_MULTIVARIATE_RESULT_COLUMNS))
    _write_json(log_path, _task_log(task_run_id, parameter_manifest, dependency, "succeeded", str(table_path), "results/summaries/result_index.json", warnings, [], ""))
    entry = ResultIndexEntry(
        result_id=result_id,
        task_run_id=task_run_id,
        task_type="cox_multivariate",
        result_semantics="formal_computed_result",
        input_package_id=str(parameter_manifest.get("survival_clinical_input_id") or ""),
        source_dataset_id=str(parameter_manifest.get("survival_clinical_input_id") or ""),
        source_repository_manifest="B12 survival input package",
        parameters_manifest=dict(parameter_manifest),
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        dependency_snapshot=dict(dependency),
        output_artifacts=({"artifact_type": "cox_multivariate_result_table", "path": str(table_path), "required_columns": list(COX_MULTIVARIATE_RESULT_COLUMNS)},),
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
    schema_gate = validate_cox_multivariate_result_index_entry(entry)
    if schema_gate.get("status") != "passed":
        entry["validation_status"] = "blocked"
        entry["blockers"] = list(schema_gate.get("blockers", []) or [])
    registered = register_result(root, entry)
    return {"status": "passed" if not registered.get("blockers") else "blocked", "result_id": result_id, "task_run_id": task_run_id, "cox_result_table": str(table_path), "task_run_log_path": str(log_path), "result": registered, "warnings": warnings, "blockers": list(registered.get("blockers", []) or [])}


def _observations(rows: list[dict[str, str]], parameter_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    covariates = [str(item) for item in parameter_manifest.get("selected_covariates", []) or []]
    specs = parameter_manifest.get("covariate_specs") if isinstance(parameter_manifest.get("covariate_specs"), dict) else {}
    references = _category_references(rows, covariates)
    time_field = str(parameter_manifest.get("time_field") or "")
    event_field = str(parameter_manifest.get("event_field") or "")
    event_coding = parameter_manifest.get("event_coding") if isinstance(parameter_manifest.get("event_coding"), dict) else {}
    observations: list[dict[str, Any]] = []
    for row in rows:
        sid = sample_id(row)
        time = parse_float(row.get(time_field))
        event = event_observed(row.get(event_field), event_coding)
        values: list[float] = []
        if not sid or time is None or event is None:
            continue
        valid = True
        for name in covariates:
            raw = str(row.get(name) or "").strip()
            spec = specs.get(name) if isinstance(specs, dict) else {}
            variable_type = str((spec or {}).get("variable_type") or "")
            if raw == "":
                valid = False
                break
            if variable_type in {"binary_variable", "categorical_variable", "ordinal_variable"}:
                values.append(0.0 if raw == references.get(name, raw) else 1.0)
            else:
                parsed = parse_float(raw)
                if parsed is None:
                    valid = False
                    break
                values.append(parsed)
        if valid:
            observations.append({"sample_id": sid, "time": float(time), "event": bool(event), "x": values})
    return observations


def _fit_multivariate_cox(observations: list[dict[str, Any]], variable_count: int) -> dict[str, Any]:
    if variable_count <= 0:
        return {"blockers": ["missing_selected_covariates"]}
    beta = [0.0] * variable_count
    for _ in range(50):
        score, info = _score_info(observations, beta)
        step = _solve_linear(_regularized_info(info), score)
        if step is None:
            return {"blockers": ["cox_multivariate_model_singular"]}
        step = [max(min(value, 1.0), -1.0) for value in step]
        beta = [b + s for b, s in zip(beta, step, strict=False)]
        if max(abs(value) for value in step) < 1e-7:
            break
    _, info = _score_info(observations, beta)
    covariance = _invert_matrix(_regularized_info(info))
    if covariance is None:
        return {"blockers": ["cox_multivariate_model_singular"]}
    se = [(max(covariance[index][index], 1e-12)) ** 0.5 for index in range(variable_count)]
    z_values = [beta[index] / se[index] if se[index] else 0.0 for index in range(variable_count)]
    p_values = [math.erfc(abs(z) / math.sqrt(2.0)) for z in z_values]
    return {"beta": beta, "se": se, "z_values": z_values, "p_values": p_values, "blockers": []}


def _score_info(observations: list[dict[str, Any]], beta: list[float]) -> tuple[list[float], list[list[float]]]:
    p = len(beta)
    score = [0.0] * p
    info = [[0.0 for _ in range(p)] for _ in range(p)]
    for time in sorted({item["time"] for item in observations if item["event"]}):
        events = [item for item in observations if item["time"] == time and item["event"]]
        risk = [item for item in observations if item["time"] >= time]
        weights = [math.exp(sum(beta[index] * item["x"][index] for index in range(p))) for item in risk]
        total = sum(weights)
        if not total:
            continue
        means = [sum(weight * item["x"][index] for weight, item in zip(weights, risk, strict=False)) / total for index in range(p)]
        second = [
            [
                sum(weight * item["x"][i] * item["x"][j] for weight, item in zip(weights, risk, strict=False)) / total
                for j in range(p)
            ]
            for i in range(p)
        ]
        for event in events:
            for index in range(p):
                score[index] += event["x"][index] - means[index]
        for i in range(p):
            for j in range(p):
                info[i][j] += len(events) * max(second[i][j] - means[i] * means[j], 0.0 if i == j else -1e12)
    return score, info


def _cox_rows(fit: dict[str, Any], observations: list[dict[str, Any]], parameter_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    covariates = [str(item) for item in parameter_manifest.get("selected_covariates", []) or []]
    specs = parameter_manifest.get("covariate_specs") if isinstance(parameter_manifest.get("covariate_specs"), dict) else {}
    rows: list[dict[str, Any]] = []
    for index, covariate in enumerate(covariates):
        beta = fit["beta"][index]
        se = fit["se"][index]
        adjusted_for = [item for item in covariates if item != covariate]
        rows.append(
            {
                "covariate": covariate,
                "covariate_label": covariate,
                "covariate_type": str((specs.get(covariate) or {}).get("variable_type") or ""),
                "hazard_ratio": _safe_exp(beta),
                "ci_lower": _safe_exp(beta - 1.96 * se),
                "ci_upper": _safe_exp(beta + 1.96 * se),
                "p_value": fit["p_values"][index],
                "z_statistic": fit["z_values"][index],
                "sample_count": len(observations),
                "event_count": sum(1 for item in observations if item["event"]),
                "non_missing_count": len(observations),
                "missing_count": int(parameter_manifest.get("missing_count") or 0),
                "adjusted_for": ";".join(adjusted_for),
                "method": "multivariate_cox_partial_likelihood_breslow_ties",
                "warnings": "proportional_hazards_assumption_not_formally_tested; not_clinical_conclusion",
            }
        )
    return rows


def _category_references(rows: list[dict[str, str]], covariates: list[str]) -> dict[str, str]:
    references: dict[str, str] = {}
    for name in covariates:
        values = sorted({str(row.get(name) or "").strip() for row in rows if str(row.get(name) or "").strip()})
        if values:
            references[name] = values[0]
    return references


def _safe_exp(value: float) -> float:
    return math.exp(max(min(value, 700.0), -700.0))


def _solve_linear(matrix: list[list[float]], vector: list[float]) -> list[float] | None:
    n = len(vector)
    aug = [list(matrix[row]) + [vector[row]] for row in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(aug[row][col]))
        if abs(aug[pivot][col]) < 1e-10:
            return None
        aug[col], aug[pivot] = aug[pivot], aug[col]
        pivot_value = aug[col][col]
        aug[col] = [value / pivot_value for value in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [value - factor * aug[col][idx] for idx, value in enumerate(aug[row])]
    return [aug[row][-1] for row in range(n)]


def _regularized_info(matrix: list[list[float]]) -> list[list[float]]:
    return [
        [value + (1e-6 if row == col else 0.0) for col, value in enumerate(values)]
        for row, values in enumerate(matrix)
    ]


def _invert_matrix(matrix: list[list[float]]) -> list[list[float]] | None:
    n = len(matrix)
    inverse: list[list[float]] = []
    for col in range(n):
        unit = [0.0] * n
        unit[col] = 1.0
        solved = _solve_linear(matrix, unit)
        if solved is None:
            return None
        inverse.append(solved)
    return [[inverse[col][row] for col in range(n)] for row in range(n)]


def _task_log(task_run_id: str, parameter_manifest: dict[str, Any], dependency: dict[str, Any], status: str, table_path: str, index_path: str, warnings: list[str], blockers: list[str], failure_reason: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "schema_version": "biomedpilot.cox_multivariate_task_run_log.v1",
        "task_run_id": task_run_id,
        "survival_clinical_input_id": parameter_manifest.get("survival_clinical_input_id", ""),
        "survival_outcome_gate_id": parameter_manifest.get("survival_outcome_gate_id", ""),
        "cox_multivariate_parameter_id": parameter_manifest.get("cox_multivariate_parameter_id", ""),
        "dependency_snapshot": dependency,
        "status": status,
        "started_at": now,
        "finished_at": now,
        "cox_multivariate_result_table": table_path,
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
