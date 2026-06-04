from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result

from ._io import asset_path, event_observed, parse_float, read_table, sample_id, write_table
from .km_confirmation import validate_km_logrank_confirmation
from .km_result_schema import KM_CURVE_COLUMNS, LOGRANK_COLUMNS, validate_km_result_index_entry, validate_km_result_tables
from .standard_package import write_survival_standard_result_package


ENGINE_NAME = "biomedpilot_controlled_km_logrank"
ENGINE_VERSION = "0.1.0"


def run_controlled_km_logrank(project_root: str | Path, parameter_manifest: dict[str, Any], confirmation: dict[str, Any]) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    blockers: list[str] = []
    warnings = list(parameter_manifest.get("warnings", []) or [])
    if parameter_manifest.get("status") != "passed":
        blockers.extend(str(item) for item in parameter_manifest.get("blockers", []) or ["km_parameter_manifest_not_passed"])
    confirmation_gate = validate_km_logrank_confirmation(confirmation, parameter_manifest)
    if confirmation_gate.get("status") != "passed":
        blockers.extend(str(item) for item in confirmation_gate.get("blockers", []) or [])
    dependency = parameter_manifest.get("dependency_snapshot") if isinstance(parameter_manifest.get("dependency_snapshot"), dict) else {}
    if dependency.get("status") != "passed":
        blockers.append("dependency_snapshot_not_passed")
    output_plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
    task_run_id = str(output_plan.get("task_run_id") or f"task-run-km-{_now_compact()}")
    result_id = str(output_plan.get("result_id") or f"survival-km-{_now_compact()}")
    log_path = root / str(output_plan.get("task_run_log_path") or f"analysis/survival_km/{result_id}_run_log.json")

    if blockers:
        log_payload = _task_log(task_run_id, parameter_manifest, dependency, "blocked", "", "", "", warnings, blockers, "km_logrank_gates_not_passed")
        _write_json(log_path, log_payload)
        return {"status": "blocked", "result_id": "", "task_run_id": task_run_id, "warnings": warnings, "blockers": list(dict.fromkeys(blockers)), "failure_reason": "km_logrank_gates_not_passed", "task_run_log_path": str(log_path)}

    rows = read_table(asset_path(parameter_manifest.get("provenance", {}).get("clinical_asset") if isinstance(parameter_manifest.get("provenance"), dict) else None))
    if not rows:
        rows = read_table(str(parameter_manifest.get("provenance", {}).get("clinical_asset_path") or ""))
    observations = _observations(rows, parameter_manifest)
    if not observations:
        blockers.append("no_valid_survival_observations")
    km_rows = _km_curve_rows(observations, parameter_manifest)
    logrank_rows = [_logrank_row(observations, parameter_manifest)]
    table_validation = validate_km_result_tables(km_rows, logrank_rows)
    blockers.extend(str(item) for item in table_validation.get("blockers", []) or [])
    warnings.extend(str(item) for item in table_validation.get("warnings", []) or [])
    km_path = root / str(output_plan.get("km_curve_table_path") or f"results/tables/survival/{result_id}_curve.tsv")
    logrank_path = root / str(output_plan.get("logrank_result_table_path") or f"results/tables/survival/{result_id}_logrank.tsv")

    if blockers:
        log_payload = _task_log(task_run_id, parameter_manifest, dependency, "failed", str(km_path), str(logrank_path), "", warnings, blockers, "km_logrank_runtime_validation_failed")
        _write_json(log_path, log_payload)
        return {"status": "blocked", "result_id": "", "task_run_id": task_run_id, "warnings": list(dict.fromkeys(warnings)), "blockers": list(dict.fromkeys(blockers)), "failure_reason": "km_logrank_runtime_validation_failed", "task_run_log_path": str(log_path)}

    write_table(km_path, km_rows, list(KM_CURVE_COLUMNS))
    write_table(logrank_path, logrank_rows, list(LOGRANK_COLUMNS))
    log_payload = _task_log(task_run_id, parameter_manifest, dependency, "succeeded", str(km_path), str(logrank_path), "results/summaries/result_index.json", warnings, [], "")
    _write_json(log_path, log_payload)
    output_artifacts = (
        {"artifact_type": "km_curve_table", "path": str(km_path), "required_columns": list(KM_CURVE_COLUMNS)},
        {"artifact_type": "logrank_result_table", "path": str(logrank_path), "required_columns": list(LOGRANK_COLUMNS)},
    )
    standard_package_dir = write_survival_standard_result_package(
        root,
        result_id=result_id,
        task_run_id=task_run_id,
        analysis_type="survival_km_logrank",
        table_artifacts=output_artifacts,
        log_path=log_path,
        parameter_manifest=parameter_manifest,
        dependency_snapshot=dependency,
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        source_owner="app.bioinformatics.survival_clinical.km_executor",
    )
    entry = ResultIndexEntry(
        result_id=result_id,
        task_run_id=task_run_id,
        task_type="survival_km_logrank",
        result_semantics="formal_computed_result",
        input_package_id=str(parameter_manifest.get("survival_clinical_input_id") or ""),
        source_dataset_id=str(parameter_manifest.get("survival_clinical_input_id") or ""),
        source_repository_manifest="B12 survival input package",
        parameters_manifest=dict(parameter_manifest),
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        dependency_snapshot=dict(dependency),
        output_artifacts=(
            *output_artifacts,
            {"artifact_type": "standard_result_package", "path": str(standard_package_dir.relative_to(root)), "schema": "biomedpilot.analysis.result_package.v1"},
        ),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=tuple(dict.fromkeys(warnings)),
        blockers=(),
        log_artifacts=({"artifact_type": "task_run_log", "path": str(log_path)},),
        report_ready_eligible=False,
    ).to_dict()
    entry["survival_clinical_input_id"] = str(parameter_manifest.get("survival_clinical_input_id") or "")
    entry["survival_outcome_gate_id"] = str(parameter_manifest.get("survival_outcome_gate_id") or "")
    schema_gate = validate_km_result_index_entry(entry)
    if schema_gate.get("status") != "passed":
        entry["validation_status"] = "blocked"
        entry["blockers"] = list(schema_gate.get("blockers", []) or [])
    registered = register_result(root, entry)
    return {"status": "passed" if not registered.get("blockers") else "blocked", "result_id": result_id, "task_run_id": task_run_id, "result": registered, "km_curve_table": str(km_path), "logrank_result_table": str(logrank_path), "task_run_log_path": str(log_path), "standard_result_package_dir": str(standard_package_dir), "warnings": warnings, "blockers": list(registered.get("blockers", []) or [])}


def _observations(rows: list[dict[str, str]], parameter_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    time_field = str(parameter_manifest.get("time_field") or "")
    event_field = str(parameter_manifest.get("event_field") or "")
    group_field = str(parameter_manifest.get("grouping_variable") or "")
    event_coding = parameter_manifest.get("event_coding") if isinstance(parameter_manifest.get("event_coding"), dict) else {}
    groups = {str(parameter_manifest.get("group_a") or ""), str(parameter_manifest.get("group_b") or "")}
    observations: list[dict[str, Any]] = []
    for row in rows:
        group = str(row.get(group_field) or "").strip()
        time = parse_float(row.get(time_field))
        event = event_observed(row.get(event_field), event_coding)
        sid = sample_id(row)
        if sid and group in groups and time is not None and event is not None:
            observations.append({"sample_id": sid, "group": group, "time": float(time), "event": bool(event)})
    return observations


def _km_curve_rows(observations: list[dict[str, Any]], parameter_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    time_unit = str(parameter_manifest.get("time_unit") or "")
    for group in (str(parameter_manifest.get("group_a") or ""), str(parameter_manifest.get("group_b") or "")):
        group_obs = [item for item in observations if item["group"] == group]
        survival = 1.0
        for time in sorted({item["time"] for item in group_obs}):
            at_risk = sum(1 for item in group_obs if item["time"] >= time)
            events = sum(1 for item in group_obs if item["time"] == time and item["event"])
            censored = sum(1 for item in group_obs if item["time"] == time and not item["event"])
            if at_risk > 0 and events:
                survival *= 1.0 - (events / at_risk)
            rows.append({"time": time, "survival_probability": survival, "group": group, "at_risk": at_risk, "events": events, "censored": censored, "time_unit": time_unit, "warnings": ""})
    return rows


def _logrank_row(observations: list[dict[str, Any]], parameter_manifest: dict[str, Any]) -> dict[str, Any]:
    group_a = str(parameter_manifest.get("group_a") or "")
    group_b = str(parameter_manifest.get("group_b") or "")
    event_times = sorted({item["time"] for item in observations if item["event"]})
    observed_a = expected_a = variance_a = 0.0
    for time in event_times:
        a_at_risk = sum(1 for item in observations if item["group"] == group_a and item["time"] >= time)
        b_at_risk = sum(1 for item in observations if item["group"] == group_b and item["time"] >= time)
        a_events = sum(1 for item in observations if item["group"] == group_a and item["time"] == time and item["event"])
        b_events = sum(1 for item in observations if item["group"] == group_b and item["time"] == time and item["event"])
        n = a_at_risk + b_at_risk
        d = a_events + b_events
        if n <= 0 or d <= 0:
            continue
        observed_a += a_events
        expected_a += d * (a_at_risk / n)
        if n > 1:
            variance_a += (a_at_risk * b_at_risk * d * (n - d)) / (n * n * (n - 1))
    statistic = ((observed_a - expected_a) ** 2 / variance_a) if variance_a > 0 else 0.0
    p_value = math.erfc(math.sqrt(statistic / 2.0))
    return {
        "group_a": group_a,
        "group_b": group_b,
        "test_statistic": statistic,
        "p_value": p_value,
        "method": "two_group_logrank_chi_square_df1",
        "event_count_group_a": sum(1 for item in observations if item["group"] == group_a and item["event"]),
        "event_count_group_b": sum(1 for item in observations if item["group"] == group_b and item["event"]),
        "sample_count_group_a": sum(1 for item in observations if item["group"] == group_a),
        "sample_count_group_b": sum(1 for item in observations if item["group"] == group_b),
        "warnings": "",
    }


def _task_log(task_run_id: str, parameter_manifest: dict[str, Any], dependency: dict[str, Any], status: str, km_path: str, logrank_path: str, index_path: str, warnings: list[str], blockers: list[str], failure_reason: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "schema_version": "biomedpilot.survival_km_task_run_log.v1",
        "task_run_id": task_run_id,
        "survival_clinical_input_id": parameter_manifest.get("survival_clinical_input_id", ""),
        "survival_outcome_gate_id": parameter_manifest.get("survival_outcome_gate_id", ""),
        "km_parameter_id": parameter_manifest.get("km_parameter_id", ""),
        "dependency_snapshot": dependency,
        "status": status,
        "started_at": now,
        "finished_at": now,
        "km_curve_table": km_path,
        "logrank_result_table": logrank_path,
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
