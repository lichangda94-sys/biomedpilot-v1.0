from __future__ import annotations

from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry

from ._io import read_table, write_table


COX_GUARD_COPY = (
    "This is a single-variable Cox statistical result. "
    "It is not a clinical prognosis conclusion. "
    "It is not a treatment recommendation. "
    "It is not a validated risk score. "
    "Multivariate Cox is not performed in this stage."
)
COX_MULTIVARIATE_GUARD_COPY = (
    "This is a multivariate Cox statistical result adjusted for selected covariates. "
    "It is not a clinical prognosis conclusion. "
    "It is not a treatment recommendation. "
    "It is not a validated risk score or nomogram. "
    "Automatic variable selection is not performed."
)


def build_cox_result_review(project_root: str | Path, result_id: str, *, sort_by: str = "p_value", filter_mode: str = "all") -> dict[str, Any]:
    source = _load_result(project_root, result_id)
    if not source:
        return {"status": "blocked", "blockers": ["missing_cox_univariate_result"], "warnings": [], "guard_copy": COX_GUARD_COPY}
    if normalize_result_semantics(source.get("result_semantics")) != "formal_computed_result" or source.get("task_type") != "cox_univariate":
        return {"status": "blocked", "blockers": ["cox_review_requires_formal_cox_univariate_result"], "warnings": [], "guard_copy": COX_GUARD_COPY}
    paths = _artifact_paths(source)
    rows = read_table(paths.get("cox_result_table"))
    rows = _filter_rows(rows, filter_mode)
    rows = sorted(rows, key=lambda row: _float(row.get(sort_by), default=0.0))
    first = rows[0] if rows else {}
    params = source.get("parameters_manifest") if isinstance(source.get("parameters_manifest"), dict) else {}
    return {
        "schema_version": "biomedpilot.cox_univariate_result_review.v1",
        "status": "passed" if rows else "blocked",
        "result_id": result_id,
        "covariate": first.get("covariate", params.get("covariate", "")),
        "covariate_type": first.get("covariate_type", params.get("covariate_type", "")),
        "hazard_ratio": _float(first.get("hazard_ratio")),
        "ci_lower": _float(first.get("ci_lower")),
        "ci_upper": _float(first.get("ci_upper")),
        "p_value": _float(first.get("p_value")),
        "sample_count": int(_float(first.get("sample_count"), default=0)),
        "event_count": int(_float(first.get("event_count"), default=0)),
        "missing_count": int(_float(first.get("missing_count"), default=0)),
        "missing_rate": params.get("missing_rate", 0.0),
        "method": first.get("method", ""),
        "engine": {"name": source.get("engine_name", ""), "version": source.get("engine_version", "")},
        "dependency_snapshot": source.get("dependency_snapshot") if isinstance(source.get("dependency_snapshot"), dict) else {},
        "cox_result_preview": rows[:20],
        "warnings": list(source.get("warnings", []) or []),
        "blockers": [] if rows else ["missing_cox_result_table"],
        "guard_copy": COX_GUARD_COPY,
        "report_ready_eligible": False,
    }


def export_cox_review_table(project_root: str | Path, result_id: str, output_path: str | Path) -> dict[str, Any]:
    review = build_cox_result_review(project_root, result_id)
    if review.get("status") != "passed":
        return {"status": "blocked", "path": "", "blockers": list(review.get("blockers", []) or [])}
    path = write_table(output_path, review.get("cox_result_preview", []), ["covariate", "covariate_label", "covariate_type", "hazard_ratio", "ci_lower", "ci_upper", "p_value", "z_statistic", "sample_count", "event_count", "non_missing_count", "missing_count", "method", "warnings"])
    return {"status": "passed", "path": str(path), "blockers": []}


def build_cox_multivariate_result_review(project_root: str | Path, result_id: str, *, sort_by: str = "p_value", filter_mode: str = "all") -> dict[str, Any]:
    source = _load_result(project_root, result_id)
    if not source:
        return {"status": "blocked", "blockers": ["missing_cox_multivariate_result"], "warnings": [], "guard_copy": COX_MULTIVARIATE_GUARD_COPY}
    if normalize_result_semantics(source.get("result_semantics")) != "formal_computed_result" or source.get("task_type") != "cox_multivariate":
        return {"status": "blocked", "blockers": ["cox_multivariate_review_requires_formal_cox_multivariate_result"], "warnings": [], "guard_copy": COX_MULTIVARIATE_GUARD_COPY}
    paths = _artifact_paths(source)
    rows = read_table(paths.get("cox_multivariate_result_table"))
    rows = _filter_rows(rows, filter_mode)
    rows = sorted(rows, key=lambda row: _float(row.get(sort_by), default=0.0))
    params = source.get("parameters_manifest") if isinstance(source.get("parameters_manifest"), dict) else {}
    covariates = [str(item) for item in params.get("selected_covariates", []) or []]
    significant = [row for row in rows if _float(row.get("p_value"), default=1.0) is not None and (_float(row.get("p_value"), default=1.0) or 1.0) < 0.05]
    return {
        "schema_version": "biomedpilot.cox_multivariate_result_review.v1",
        "status": "passed" if rows else "blocked",
        "result_id": result_id,
        "covariates": covariates,
        "covariate_count": len(covariates) or len(rows),
        "sample_count": int(_float((rows[0] if rows else {}).get("sample_count"), default=0)),
        "event_count": int(_float((rows[0] if rows else {}).get("event_count"), default=0)),
        "significant_covariate_count": len(significant),
        "method": (rows[0] if rows else {}).get("method", ""),
        "adjustment_policy": "selected covariates only; no automatic variable selection",
        "engine": {"name": source.get("engine_name", ""), "version": source.get("engine_version", "")},
        "dependency_snapshot": source.get("dependency_snapshot") if isinstance(source.get("dependency_snapshot"), dict) else {},
        "cox_multivariate_result_preview": rows[:50],
        "warnings": list(dict.fromkeys([*list(source.get("warnings", []) or []), "not_clinical_conclusion", "risk_score_not_generated"])),
        "blockers": [] if rows else ["missing_cox_multivariate_result_table"],
        "guard_copy": COX_MULTIVARIATE_GUARD_COPY,
        "report_ready_eligible": False,
    }


def export_cox_multivariate_review_table(project_root: str | Path, result_id: str, output_path: str | Path) -> dict[str, Any]:
    review = build_cox_multivariate_result_review(project_root, result_id)
    if review.get("status") != "passed":
        return {"status": "blocked", "path": "", "blockers": list(review.get("blockers", []) or [])}
    path = write_table(
        output_path,
        review.get("cox_multivariate_result_preview", []),
        ["covariate", "covariate_label", "covariate_type", "hazard_ratio", "ci_lower", "ci_upper", "p_value", "z_statistic", "sample_count", "event_count", "non_missing_count", "missing_count", "adjusted_for", "method", "warnings"],
    )
    return {"status": "passed", "path": str(path), "blockers": [], "report_ready_eligible": False}


def _load_result(project_root: str | Path, result_id: str) -> dict[str, Any]:
    registry = load_registry(project_root)
    return next((entry for entry in registry.get("results", []) if isinstance(entry, dict) and entry.get("result_id") == result_id), {})


def _artifact_paths(entry: dict[str, Any]) -> dict[str, str]:
    return {str(item.get("artifact_type") or ""): str(item.get("path") or "") for item in entry.get("output_artifacts", []) or [] if isinstance(item, dict)}


def _filter_rows(rows: list[dict[str, str]], filter_mode: str) -> list[dict[str, str]]:
    if filter_mode == "significant":
        return [row for row in rows if _float(row.get("p_value"), default=1.0) < 0.05]
    if filter_mode == "not_significant":
        return [row for row in rows if _float(row.get("p_value"), default=1.0) >= 0.05]
    return rows


def _float(value: object, *, default: float | None = None) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default
