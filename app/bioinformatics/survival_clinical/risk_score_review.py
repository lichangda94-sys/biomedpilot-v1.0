from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry

from ._io import read_table
from .risk_score_result_schema import RISK_SCORE_RESULT_COLUMNS


RISK_SCORE_REVIEW_SCHEMA_VERSION = "biomedpilot.risk_score_result_review.v1"
RISK_SCORE_EXPORT_DIR = Path("results") / "exports" / "risk_score_review"
RISK_SCORE_GUARD_COPY = (
    "Risk score review shows a statistical model score only. "
    "It is not a clinical prognosis conclusion, diagnosis, treatment recommendation, or validated clinical risk stratification. "
    "No high/low-risk group, nomogram, calibration curve, decision curve, plot artifact, or report-ready package is generated."
)


def build_risk_score_result_review(
    project_root: str | Path,
    result_id: str | None = None,
    *,
    sort_by: str = "risk_score",
    filter_mode: str = "all",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) or [] if isinstance(entry, dict)]
    formal_entries = [_risk_score_entry(entry) for entry in entries]
    formal_entries = [entry for entry in formal_entries if entry is not None]
    excluded = [_excluded_entry(entry) for entry in entries if _risk_score_entry(entry) is None]
    selected = _select_entry(formal_entries, result_id)
    if selected is None:
        return {
            "schema_version": RISK_SCORE_REVIEW_SCHEMA_VERSION,
            "status": "blocked",
            "result_options": _result_options(formal_entries),
            "selected_result_id": result_id or "",
            "summary": _empty_summary(),
            "rows": [],
            "provenance": {},
            "guard_copy": RISK_SCORE_GUARD_COPY,
            "disabled_downstream": _disabled_downstream(),
            "excluded_results": excluded,
            "blockers": ["formal_risk_score_result_not_found"],
            "warnings": [],
        }
    table_path = _result_table_path(root, selected)
    rows = _read_risk_score_rows(table_path)
    filtered_rows = _filter_rows(rows, filter_mode)
    sorted_rows = _sort_rows(filtered_rows, sort_by)
    confirmation = selected.get("risk_score_parameter_confirmation") if isinstance(selected.get("risk_score_parameter_confirmation"), dict) else {}
    return {
        "schema_version": RISK_SCORE_REVIEW_SCHEMA_VERSION,
        "status": "passed" if rows else "blocked",
        "result_options": _result_options(formal_entries),
        "selected_result_id": str(selected.get("result_id") or ""),
        "summary": _summary(rows, selected, confirmation),
        "rows": sorted_rows,
        "provenance": _provenance(selected, table_path, confirmation),
        "guard_copy": RISK_SCORE_GUARD_COPY,
        "disabled_downstream": _disabled_downstream(),
        "excluded_results": excluded,
        "blockers": [] if rows else ["missing_risk_score_result_table"],
        "warnings": list(dict.fromkeys([*list(selected.get("warnings", []) or []), "table_only_not_report_ready", "no_clinical_interpretation"])),
    }


def export_risk_score_review_table(
    project_root: str | Path,
    result_id: str | None = None,
    *,
    file_format: str = "tsv",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    review = build_risk_score_result_review(root, result_id=result_id, sort_by="input_order", filter_mode="all")
    if review.get("status") != "passed":
        return {"status": "blocked", "blockers": list(review.get("blockers", []) or []), "warnings": []}
    selected_result_id = str(review.get("selected_result_id") or "risk_score")
    normalized_format = "csv" if str(file_format).lower() == "csv" else "tsv"
    delimiter = "," if normalized_format == "csv" else "\t"
    export_path = root / RISK_SCORE_EXPORT_DIR / f"{selected_result_id}_review.{normalized_format}"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    with export_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(RISK_SCORE_RESULT_COLUMNS), delimiter=delimiter)
        writer.writeheader()
        for row in review.get("rows", []) or []:
            if isinstance(row, dict):
                writer.writerow({column: row.get(column, "") for column in RISK_SCORE_RESULT_COLUMNS})
    return {
        "status": "passed",
        "export_path": str(export_path),
        "file_format": normalized_format,
        "result_id": selected_result_id,
        "row_count": len(review.get("rows", []) or []),
        "report_ready_eligible": False,
        "plot_artifacts": [],
        "report_artifacts": [],
        "blockers": [],
        "warnings": ["risk_score_export_table_only_not_report_ready", "no_risk_group_or_nomogram_export"],
    }


def _risk_score_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    if normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") != "formal_computed_result":
        return None
    if str(entry.get("task_type") or "").lower() != "risk_score":
        return None
    artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    if not any(isinstance(item, dict) and item.get("artifact_type") == "risk_score_result_table" for item in artifacts):
        return None
    if entry.get("plot_artifacts") or entry.get("report_artifacts") or entry.get("report_ready_eligible") is True:
        return None
    return entry


def _excluded_entry(entry: dict[str, Any]) -> dict[str, str]:
    return {
        "result_id": str(entry.get("result_id") or entry.get("result_name") or ""),
        "result_semantics": str(entry.get("result_semantics") or ""),
        "task_type": str(entry.get("task_type") or ""),
        "reason": "not_formal_table_only_risk_score_result",
    }


def _select_entry(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    return entries[-1] if entries else None


def _result_options(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "result_id": str(entry.get("result_id") or ""),
            "task_run_id": str(entry.get("task_run_id") or ""),
            "created_at": str(entry.get("created_at") or ""),
        }
        for entry in entries
    ]


def _result_table_path(root: Path, entry: dict[str, Any]) -> Path:
    artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "risk_score_result_table"), {})
    path = Path(str(artifact.get("path") or ""))
    return path if path.is_absolute() else root / path


def _read_risk_score_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(read_table(path)):
        normalized = {column: row.get(column, "") for column in RISK_SCORE_RESULT_COLUMNS}
        normalized["_input_order"] = index
        rows.append(normalized)
    return rows


def _filter_rows(rows: list[dict[str, Any]], filter_mode: str) -> list[dict[str, Any]]:
    selected = str(filter_mode or "all")
    if selected == "all":
        return list(rows)
    if selected == "positive_score":
        return [row for row in rows if _float(row.get("risk_score"), default=0.0) > 0.0]
    if selected == "negative_score":
        return [row for row in rows if _float(row.get("risk_score"), default=0.0) < 0.0]
    return rows


def _sort_rows(rows: list[dict[str, Any]], sort_by: str) -> list[dict[str, Any]]:
    key = str(sort_by or "risk_score")
    if key == "input_order":
        return sorted(rows, key=lambda row: int(row.get("_input_order") or 0))
    if key == "sample_id":
        return sorted(rows, key=lambda row: str(row.get("sample_id") or ""))
    return sorted(rows, key=lambda row: _float(row.get("risk_score"), default=0.0), reverse=True)


def _summary(rows: list[dict[str, Any]], entry: dict[str, Any], confirmation: dict[str, Any]) -> dict[str, Any]:
    scores = [_float(row.get("risk_score"), default=0.0) for row in rows]
    variables = [str(item) for item in confirmation.get("candidate_variables", []) or []]
    dependency = entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {}
    return {
        "sample_count": len(rows),
        "covariate_count": len(variables),
        "candidate_variables": variables,
        "min_risk_score": min(scores) if scores else 0.0,
        "max_risk_score": max(scores) if scores else 0.0,
        "mean_risk_score": (sum(scores) / len(scores)) if scores else 0.0,
        "source_cox_multivariate_result_id": str(entry.get("source_cox_multivariate_result_id") or confirmation.get("source_cox_multivariate_result_id") or ""),
        "engine": {"name": entry.get("engine_name", ""), "version": entry.get("engine_version", "")},
        "dependency_status": dependency.get("status", ""),
        "dependency_snapshot": dependency,
        "cutoff_policy": confirmation.get("cutoff_policy") if isinstance(confirmation.get("cutoff_policy"), dict) else {},
        "scaling_policy": confirmation.get("scaling_policy") if isinstance(confirmation.get("scaling_policy"), dict) else {},
    }


def _provenance(entry: dict[str, Any], table_path: Path, confirmation: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_id": str(entry.get("result_id") or ""),
        "task_run_id": str(entry.get("task_run_id") or ""),
        "input_package_id": str(entry.get("input_package_id") or ""),
        "source_repository_manifest": str(entry.get("source_repository_manifest") or ""),
        "source_cox_multivariate_result_id": str(entry.get("source_cox_multivariate_result_id") or ""),
        "parameter_confirmation_schema": str(confirmation.get("schema_version") or ""),
        "parameter_confirmation_created_at": str(confirmation.get("created_at") or ""),
        "parameters_manifest_present": bool(entry.get("parameters_manifest")),
        "dependency_snapshot_present": bool(entry.get("dependency_snapshot")),
        "task_run_log": entry.get("log_artifacts", []),
        "result_table_path": str(table_path),
        "result_index_path": "results/summaries/result_index.json",
        "plot_artifacts": entry.get("plot_artifacts", []),
        "report_artifacts": entry.get("report_artifacts", []),
        "report_ready_eligible": bool(entry.get("report_ready_eligible")),
    }


def _empty_summary() -> dict[str, Any]:
    return {
        "sample_count": 0,
        "covariate_count": 0,
        "candidate_variables": [],
        "min_risk_score": 0.0,
        "max_risk_score": 0.0,
        "mean_risk_score": 0.0,
        "source_cox_multivariate_result_id": "",
        "engine": {},
        "dependency_status": "",
    }


def _disabled_downstream() -> dict[str, str]:
    return {
        "risk_group": "Risk group/cutpoint labels remain disabled after B35.",
        "nomogram": "Nomogram/calibration/decision-curve rendering is not generated by B35.",
        "plot": "Risk score plot artifacts are not enabled by B35.",
        "report_ready": "Risk score review/export is table-only and not report-ready.",
        "clinical_interpretation": "No clinical prognosis, diagnosis, treatment recommendation, or validated stratification is produced.",
    }


def _float(value: object, *, default: float) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default
