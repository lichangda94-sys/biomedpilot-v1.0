from __future__ import annotations

from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry

from ._io import read_table, write_table


KM_GUARD_COPY = (
    "This is a statistical survival analysis result. "
    "It is not a clinical prognosis conclusion. "
    "It is not a treatment recommendation. "
    "No Cox hazard ratio is produced in this stage."
)


def build_km_result_review(project_root: str | Path, result_id: str) -> dict[str, Any]:
    source = _load_result(project_root, result_id)
    if not source:
        return {"status": "blocked", "blockers": ["missing_km_logrank_result"], "warnings": [], "guard_copy": KM_GUARD_COPY}
    if normalize_result_semantics(source.get("result_semantics")) != "formal_computed_result" or source.get("task_type") != "survival_km_logrank":
        return {"status": "blocked", "blockers": ["km_review_requires_formal_survival_km_logrank_result"], "warnings": [], "guard_copy": KM_GUARD_COPY}
    artifacts = _artifact_paths(source)
    km_rows = read_table(artifacts.get("km_curve_table"))
    logrank_rows = read_table(artifacts.get("logrank_result_table"))
    logrank = logrank_rows[0] if logrank_rows else {}
    params = source.get("parameters_manifest") if isinstance(source.get("parameters_manifest"), dict) else {}
    dependency = source.get("dependency_snapshot") if isinstance(source.get("dependency_snapshot"), dict) else {}
    review = {
        "schema_version": "biomedpilot.km_logrank_result_review.v1",
        "status": "passed" if km_rows and logrank_rows else "blocked",
        "result_id": result_id,
        "group_names": [params.get("group_a", ""), params.get("group_b", "")],
        "group_sample_counts": {
            str(params.get("group_a") or ""): int(float(logrank.get("sample_count_group_a") or 0)),
            str(params.get("group_b") or ""): int(float(logrank.get("sample_count_group_b") or 0)),
        },
        "group_event_counts": {
            str(params.get("group_a") or ""): int(float(logrank.get("event_count_group_a") or 0)),
            str(params.get("group_b") or ""): int(float(logrank.get("event_count_group_b") or 0)),
        },
        "median_survival": _median_survival(km_rows),
        "logrank_p_value": float(logrank.get("p_value") or 0.0) if logrank else None,
        "time_unit": params.get("time_unit", ""),
        "censoring_policy": params.get("censoring_policy", ""),
        "missingness_summary": params.get("missingness_policy", ""),
        "engine": {"name": source.get("engine_name", ""), "version": source.get("engine_version", "")},
        "dependency_snapshot": dependency,
        "km_curve_preview": km_rows[:20],
        "logrank_result_preview": logrank_rows[:5],
        "warnings": list(source.get("warnings", []) or []),
        "blockers": [] if km_rows and logrank_rows else ["missing_review_source_table"],
        "guard_copy": KM_GUARD_COPY,
        "report_ready_eligible": False,
    }
    return review


def export_km_review_table(project_root: str | Path, result_id: str, output_path: str | Path) -> dict[str, Any]:
    review = build_km_result_review(project_root, result_id)
    if review.get("status") != "passed":
        return {"status": "blocked", "path": "", "blockers": list(review.get("blockers", []) or [])}
    rows = [
        {
            "result_id": review["result_id"],
            "group": group,
            "sample_count": review["group_sample_counts"].get(group, 0),
            "event_count": review["group_event_counts"].get(group, 0),
            "median_survival": review["median_survival"].get(group, ""),
            "logrank_p_value": review["logrank_p_value"],
            "time_unit": review["time_unit"],
        }
        for group in review.get("group_names", [])
    ]
    path = write_table(output_path, rows, ["result_id", "group", "sample_count", "event_count", "median_survival", "logrank_p_value", "time_unit"])
    return {"status": "passed", "path": str(path), "blockers": []}


def _load_result(project_root: str | Path, result_id: str) -> dict[str, Any]:
    registry = load_registry(project_root)
    return next((entry for entry in registry.get("results", []) if isinstance(entry, dict) and entry.get("result_id") == result_id), {})


def _artifact_paths(entry: dict[str, Any]) -> dict[str, str]:
    paths: dict[str, str] = {}
    for artifact in entry.get("output_artifacts", []) or []:
        if isinstance(artifact, dict):
            paths[str(artifact.get("artifact_type") or "")] = str(artifact.get("path") or "")
    return paths


def _median_survival(km_rows: list[dict[str, str]]) -> dict[str, float | str]:
    medians: dict[str, float | str] = {}
    for row in km_rows:
        group = str(row.get("group") or "")
        if group in medians:
            continue
        try:
            survival = float(row.get("survival_probability") or 1.0)
            time = float(row.get("time") or 0.0)
        except ValueError:
            continue
        if survival <= 0.5:
            medians[group] = time
    for row in km_rows:
        group = str(row.get("group") or "")
        medians.setdefault(group, "not_reached")
    return medians
