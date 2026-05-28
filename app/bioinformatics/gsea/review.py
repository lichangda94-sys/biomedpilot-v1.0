from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.project_results import load_result_index

from .models import GSEA_TASK_TYPE, REQUIRED_GSEA_RESULT_TABLE_COLUMNS


GSEA_REVIEW_SCHEMA_VERSION = "biomedpilot.gsea_result_review.v1"
GSEA_REVIEW_COLUMNS = (
    "term_id",
    "term_name",
    "set_size",
    "overlap_size",
    "enrichment_score",
    "normalized_enrichment_score",
    "p_value",
    "adjusted_p_value",
    "leading_edge_genes",
    "rank_metric",
    "significance_label",
    "warnings",
)


def build_gsea_result_review(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    sort_by: str = "adjusted_p_value",
    significance_filter: str = "all",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    index = load_result_index(root)
    gsea_entries = [_gsea_entry(entry) for entry in index.get("entries", []) or [] if isinstance(entry, dict)]
    gsea_entries = [entry for entry in gsea_entries if entry is not None]
    excluded = [_excluded_entry(entry) for entry in index.get("entries", []) or [] if isinstance(entry, dict) and _gsea_entry(entry) is None]
    selected = _select_entry(gsea_entries, result_id)
    if selected is None:
        return {
            "schema_version": GSEA_REVIEW_SCHEMA_VERSION,
            "status": "blocked",
            "result_options": _result_options(gsea_entries),
            "selected_result_id": result_id or "",
            "summary": _empty_summary(),
            "rows": [],
            "provenance": {},
            "guard_copy": _guard_copy(),
            "disabled_downstream": _disabled_downstream(),
            "excluded_results": excluded,
            "blockers": ["gsea_result_not_found"],
            "warnings": [],
        }
    table_path = _result_table_path(root, selected)
    all_rows = _read_gsea_rows(table_path, _fdr_threshold(selected))
    filtered = _filter_rows(all_rows, significance_filter)
    sorted_rows = _sort_rows(filtered, sort_by)
    warnings = [str(item) for item in selected.get("warnings", []) or []]
    if normalize_result_semantics(selected.get("result_semantics"), default="") == "imported_external_result":
        warnings.append("imported_deg_derived_gsea_not_biomedpilot_recomputed_deg_formal_gsea")
    return {
        "schema_version": GSEA_REVIEW_SCHEMA_VERSION,
        "status": "passed",
        "result_options": _result_options(gsea_entries),
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


def _gsea_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    if str(entry.get("task_type") or "") != GSEA_TASK_TYPE:
        return None
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    if semantics not in {"formal_computed_result", "imported_external_result"}:
        return None
    artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    if not any(isinstance(item, dict) and item.get("artifact_type") == "gsea_result_table" for item in artifacts):
        return None
    return entry


def _excluded_entry(entry: dict[str, Any]) -> dict[str, str]:
    return {
        "result_id": str(entry.get("result_id") or entry.get("result_name") or ""),
        "result_semantics": str(entry.get("result_semantics") or ""),
        "task_type": str(entry.get("task_type") or ""),
        "reason": "not_controlled_preranked_gsea_result",
    }


def _select_entry(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    return entries[-1] if entries else None


def _result_options(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{"result_id": str(entry.get("result_id") or ""), "task_run_id": str(entry.get("task_run_id") or ""), "created_at": str(entry.get("created_at") or "")} for entry in entries]


def _result_table_path(root: Path, entry: dict[str, Any]) -> Path:
    artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "gsea_result_table"), {})
    path = Path(str(artifact.get("path") or ""))
    return path if path.is_absolute() else root / path


def _read_gsea_rows(path: Path, fdr_threshold: float) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        reader = csv.DictReader([first, *handle.readlines()], delimiter=delimiter)
        rows: list[dict[str, Any]] = []
        for index, raw in enumerate(reader):
            row = {column: raw.get(column, "") for column in REQUIRED_GSEA_RESULT_TABLE_COLUMNS}
            row["_input_order"] = index
            fdr = _float(row.get("adjusted_p_value"), default=1.0)
            nes = _float(row.get("normalized_enrichment_score"), default=0.0)
            if fdr <= fdr_threshold and nes > 0:
                label = "significant_positive"
            elif fdr <= fdr_threshold and nes < 0:
                label = "significant_negative"
            elif fdr <= fdr_threshold:
                label = "significant"
            else:
                label = "not_significant"
            row["significance_label"] = label
            rows.append(row)
        return rows


def _filter_rows(rows: list[dict[str, Any]], significance_filter: str) -> list[dict[str, Any]]:
    selected = str(significance_filter or "all")
    if selected == "all":
        return list(rows)
    if selected == "significant":
        return [row for row in rows if str(row.get("significance_label") or "").startswith("significant")]
    if selected in {"positive", "significant_positive"}:
        return [row for row in rows if str(row.get("significance_label") or "") == "significant_positive"]
    if selected in {"negative", "significant_negative"}:
        return [row for row in rows if str(row.get("significance_label") or "") == "significant_negative"]
    return [row for row in rows if str(row.get("significance_label") or "") == selected]


def _sort_rows(rows: list[dict[str, Any]], sort_by: str) -> list[dict[str, Any]]:
    key = str(sort_by or "adjusted_p_value")
    if key == "input_order":
        return sorted(rows, key=lambda row: int(row.get("_input_order") or 0))
    if key == "significance_label":
        return sorted(rows, key=lambda row: str(row.get("significance_label") or ""))
    numeric = {"adjusted_p_value", "p_value", "enrichment_score", "normalized_enrichment_score", "set_size", "overlap_size"}
    if key in numeric:
        reverse = key in {"enrichment_score", "normalized_enrichment_score", "set_size", "overlap_size"}
        return sorted(rows, key=lambda row: _float(row.get(key), default=float("inf")), reverse=reverse)
    return list(rows)


def _summary(rows: list[dict[str, Any]], entry: dict[str, Any]) -> dict[str, Any]:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    dependency = entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {}
    packages = dependency.get("packages") if isinstance(dependency.get("packages"), dict) else {}
    significant = [row for row in rows if str(row.get("significance_label") or "").startswith("significant")]
    top_positive = next((item for item in sorted(rows, key=lambda row: _float(row.get("normalized_enrichment_score"), default=-float("inf")), reverse=True) if _float(item.get("normalized_enrichment_score"), default=0.0) > 0), {})
    top_negative = next((item for item in sorted(rows, key=lambda row: _float(row.get("normalized_enrichment_score"), default=float("inf"))) if _float(item.get("normalized_enrichment_score"), default=0.0) < 0), {})
    return {
        "term_total": len(rows),
        "significant_term_count": len(significant),
        "top_positive_nes_term": top_positive.get("term_name", ""),
        "top_negative_nes_term": top_negative.get("term_name", ""),
        "source_deg_result_id": str(entry.get("source_deg_result_id") or ""),
        "source_result_semantics": str(entry.get("source_result_semantics") or entry.get("result_semantics") or ""),
        "rank_metric": str(parameters.get("rank_metric") or ""),
        "gene_set_resource": str(entry.get("gene_set_resource_id") or ""),
        "method": str(parameters.get("permutation_type") or "gene_set"),
        "permutation_count": int(_float(parameters.get("permutation_count"), default=0)),
        "random_seed": parameters.get("random_seed", ""),
        "dependency_versions": {name: str(status.get("version") or "") for name, status in packages.items() if isinstance(status, dict)},
    }


def _provenance(entry: dict[str, Any], table_path: Path) -> dict[str, Any]:
    return {
        "result_id": str(entry.get("result_id") or ""),
        "task_run_id": str(entry.get("task_run_id") or ""),
        "gsea_input_id": str(entry.get("gsea_input_id") or entry.get("input_package_id") or ""),
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
    return _float(parameters.get("fdr_threshold"), default=0.25)


def _empty_summary() -> dict[str, Any]:
    return {
        "term_total": 0,
        "significant_term_count": 0,
        "top_positive_nes_term": "",
        "top_negative_nes_term": "",
        "source_deg_result_id": "",
        "rank_metric": "",
        "gene_set_resource": "",
        "method": "",
        "permutation_count": 0,
        "random_seed": "",
        "dependency_versions": {},
    }


def _guard_copy() -> str:
    return "Preranked GSEA is a statistical enrichment result from a confirmed DEG-derived rank metric and local gene-set resource. It is not pathway activation proof, clinical interpretation, or treatment recommendation."


def _disabled_downstream() -> dict[str, str]:
    return {
        "plot": "GSEA plot artifact waits for B11.3 and is disabled here.",
        "report_ready": "GSEA is not report-ready in B11.2.",
        "survival": "Survival/KM/Cox/log-rank remain disabled.",
        "clinical": "No clinical or treatment conclusion is generated.",
    }


def _float(value: object, *, default: float) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default
