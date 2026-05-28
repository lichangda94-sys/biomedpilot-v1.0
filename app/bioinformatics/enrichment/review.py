from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.project_results import load_result_index

from .models import REQUIRED_ORA_TABLE_COLUMNS


ORA_REVIEW_SCHEMA_VERSION = "biomedpilot.ora_result_review.v1"
ORA_REVIEW_COLUMNS = (
    "term_id",
    "term_name",
    "overlap_count",
    "gene_set_size",
    "selected_gene_count",
    "enrichment_ratio",
    "p_value",
    "adjusted_p_value",
    "overlap_genes",
    "significance_label",
)


def build_ora_result_review(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    sort_by: str = "adjusted_p_value",
    significance_filter: str = "all",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    index = load_result_index(root)
    ora_entries = [_ora_entry(entry) for entry in index.get("entries", []) or [] if isinstance(entry, dict)]
    ora_entries = [entry for entry in ora_entries if entry is not None]
    excluded = [_excluded_entry(entry) for entry in index.get("entries", []) or [] if isinstance(entry, dict) and _ora_entry(entry) is None]
    selected = _select_entry(ora_entries, result_id)
    if selected is None:
        return {
            "schema_version": ORA_REVIEW_SCHEMA_VERSION,
            "status": "blocked",
            "result_options": _result_options(ora_entries),
            "selected_result_id": result_id or "",
            "summary": _empty_summary(),
            "rows": [],
            "provenance": {},
            "guard_copy": _guard_copy(),
            "disabled_downstream": _disabled_downstream(),
            "excluded_results": excluded,
            "blockers": ["ora_result_not_found"],
            "warnings": [],
        }
    table_path = _result_table_path(root, selected)
    all_rows = _read_ora_rows(table_path, _fdr_threshold(selected))
    filtered = _filter_rows(all_rows, significance_filter)
    sorted_rows = _sort_rows(filtered, sort_by)
    warnings = [str(item) for item in selected.get("warnings", []) or []]
    if normalize_result_semantics(selected.get("result_semantics"), default="") == "imported_external_result":
        warnings.append("imported_deg_derived_ora_not_biomedpilot_recomputed_deg_formal_ora")
    return {
        "schema_version": ORA_REVIEW_SCHEMA_VERSION,
        "status": "passed",
        "result_options": _result_options(ora_entries),
        "selected_result_id": str(selected.get("result_id") or ""),
        "summary": _summary(all_rows, selected),
        "rows": sorted_rows,
        "provenance": _provenance(selected, table_path),
        "guard_copy": _guard_copy(),
        "disabled_downstream": _disabled_downstream(),
        "excluded_results": excluded,
        "blockers": [],
        "warnings": list(dict.fromkeys(warnings)),
    }


def _ora_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    if str(entry.get("task_type") or "") != "ora_enrichment":
        return None
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    if semantics not in {"formal_computed_result", "imported_external_result"}:
        return None
    artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    if not any(isinstance(item, dict) and item.get("artifact_type") == "ora_result_table" for item in artifacts):
        return None
    return entry


def _excluded_entry(entry: dict[str, Any]) -> dict[str, str]:
    return {
        "result_id": str(entry.get("result_id") or entry.get("result_name") or ""),
        "result_semantics": str(entry.get("result_semantics") or ""),
        "task_type": str(entry.get("task_type") or ""),
        "reason": "not_controlled_ora_result",
    }


def _select_entry(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    return entries[-1] if entries else None


def _result_options(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{"result_id": str(entry.get("result_id") or ""), "task_run_id": str(entry.get("task_run_id") or ""), "created_at": str(entry.get("created_at") or "")} for entry in entries]


def _result_table_path(root: Path, entry: dict[str, Any]) -> Path:
    artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "ora_result_table"), {})
    path = Path(str(artifact.get("path") or ""))
    return path if path.is_absolute() else root / path


def _read_ora_rows(path: Path, fdr_threshold: float) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        reader = csv.DictReader([first, *handle.readlines()], delimiter=delimiter)
        rows: list[dict[str, Any]] = []
        for index, raw in enumerate(reader):
            row = {column: raw.get(column, "") for column in REQUIRED_ORA_TABLE_COLUMNS}
            row["_input_order"] = index
            row["significance_label"] = "significant" if _float(row.get("adjusted_p_value"), default=1.0) <= fdr_threshold and int(_float(row.get("overlap_count"), default=0)) > 0 else "not_significant"
            rows.append(row)
        return rows


def _filter_rows(rows: list[dict[str, Any]], significance_filter: str) -> list[dict[str, Any]]:
    selected = str(significance_filter or "all")
    if selected == "all":
        return list(rows)
    return [row for row in rows if str(row.get("significance_label") or "") == selected]


def _sort_rows(rows: list[dict[str, Any]], sort_by: str) -> list[dict[str, Any]]:
    key = str(sort_by or "adjusted_p_value")
    if key == "input_order":
        return sorted(rows, key=lambda row: int(row.get("_input_order") or 0))
    if key == "significance_label":
        return sorted(rows, key=lambda row: str(row.get("significance_label") or ""))
    numeric = {"adjusted_p_value", "p_value", "enrichment_ratio", "overlap_count"}
    if key in numeric:
        reverse = key in {"enrichment_ratio", "overlap_count"}
        return sorted(rows, key=lambda row: _float(row.get(key), default=float("inf")), reverse=reverse)
    return list(rows)


def _summary(rows: list[dict[str, Any]], entry: dict[str, Any]) -> dict[str, Any]:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    dependency = entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {}
    packages = dependency.get("packages") if isinstance(dependency.get("packages"), dict) else {}
    significant = [row for row in rows if str(row.get("significance_label") or "") == "significant"]
    top = significant[0] if significant else (rows[0] if rows else {})
    return {
        "term_total": len(rows),
        "significant_term_count": len(significant),
        "top_term_by_fdr": top.get("term_name", ""),
        "source_deg_result_id": str(entry.get("source_deg_result_id") or ""),
        "source_result_semantics": str(entry.get("source_result_semantics") or entry.get("result_semantics") or ""),
        "gene_set_resource": str(entry.get("gene_set_resource_id") or ""),
        "method": str(parameters.get("test_method") or ""),
        "dependency_versions": {name: str(status.get("version") or "") for name, status in packages.items() if isinstance(status, dict)},
        "selected_gene_count": int(_float(rows[0].get("selected_gene_count"), default=0)) if rows else 0,
        "background_size": int(_float(rows[0].get("background_size"), default=0)) if rows else 0,
    }


def _provenance(entry: dict[str, Any], table_path: Path) -> dict[str, Any]:
    return {
        "result_id": str(entry.get("result_id") or ""),
        "task_run_id": str(entry.get("task_run_id") or ""),
        "ora_input_id": str(entry.get("ora_input_id") or entry.get("input_package_id") or ""),
        "source_deg_result_id": str(entry.get("source_deg_result_id") or ""),
        "source_result_semantics": str(entry.get("source_result_semantics") or entry.get("result_semantics") or ""),
        "gene_set_resource_id": str(entry.get("gene_set_resource_id") or ""),
        "parameters_manifest_present": bool(entry.get("parameters_manifest")),
        "dependency_snapshot_present": bool(entry.get("dependency_snapshot")),
        "task_run_log": entry.get("log_artifacts", []),
        "result_table_path": str(table_path),
        "result_index_path": "results/summaries/result_index.json",
        "plot_artifacts": entry.get("plot_artifacts", []),
        "report_artifacts": entry.get("report_artifacts", []),
        "report_ready_eligible": bool(entry.get("report_ready_eligible")),
    }


def _fdr_threshold(entry: dict[str, Any]) -> float:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    return _float(parameters.get("fdr_threshold"), default=0.05)


def _empty_summary() -> dict[str, Any]:
    return {
        "term_total": 0,
        "significant_term_count": 0,
        "top_term_by_fdr": "",
        "source_deg_result_id": "",
        "gene_set_resource": "",
        "method": "",
        "dependency_versions": {},
        "selected_gene_count": 0,
        "background_size": 0,
    }


def _guard_copy() -> str:
    return "ORA is pathway over-representation analysis based on selected DEG genes. It does not prove pathway activation or inhibition. It is not clinical interpretation or treatment recommendation."


def _disabled_downstream() -> dict[str, str]:
    return {
        "plot": "ORA plot artifact waits for B10.3/B15 and is disabled here.",
        "report_ready": "ORA is not automatically added to formal DEG report-ready packages in B10.2.",
        "gsea": "GSEA remains disabled; ORA does not enter ranked enrichment.",
        "survival": "Survival/KM/Cox/log-rank remain disabled.",
    }


def _float(value: object, *, default: float) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default
