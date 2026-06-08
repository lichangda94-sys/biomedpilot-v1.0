from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from app.analysis_runtime.package_catalog import build_standard_analysis_package_catalog
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.project_results import load_result_index


REVIEW_SCHEMA_VERSION = "biomedpilot.formal_deg_result_review.v1"
REVIEW_COLUMNS = ("feature_id", "gene_symbol", "log2_fold_change", "p_value", "adjusted_p_value", "significance_label")
EXPORT_DIR = Path("results") / "exports" / "formal_deg_review"


def build_formal_deg_result_review(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    sort_by: str = "adjusted_p_value",
    significance_filter: str = "all",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    index = load_result_index(root)
    formal_entries = [_formal_deg_entry(entry) for entry in index.get("entries", []) or [] if isinstance(entry, dict)]
    formal_entries = [entry for entry in formal_entries if entry is not None]
    excluded = [_excluded_entry(entry) for entry in index.get("entries", []) or [] if isinstance(entry, dict) and _formal_deg_entry(entry) is None]
    selected = _select_entry(formal_entries, result_id)
    if selected is None:
        return {
            "schema_version": REVIEW_SCHEMA_VERSION,
            "status": "blocked",
            "result_options": _result_options(formal_entries),
            "selected_result_id": result_id or "",
            "summary": _empty_summary(),
            "rows": [],
            "provenance": {},
            "guard_copy": _guard_copy(),
            "disabled_downstream": _disabled_downstream(),
            "excluded_results": excluded,
            "blockers": ["formal_deg_result_not_found"],
            "warnings": [],
        }
    standard_package = _standard_package_for_result(root, selected)
    if standard_package.get("status") != "passed":
        blocker = str(standard_package.get("blocker") or "formal_deg_standard_result_package_missing")
        return {
            "schema_version": REVIEW_SCHEMA_VERSION,
            "status": "blocked",
            "result_options": _result_options(formal_entries),
            "selected_result_id": str(selected.get("result_id") or result_id or ""),
            "summary": _empty_summary(),
            "rows": [],
            "provenance": _blocked_provenance(selected, standard_package),
            "guard_copy": _guard_copy(),
            "disabled_downstream": _disabled_downstream(),
            "excluded_results": excluded,
            "blockers": [blocker],
            "warnings": [],
        }
    table_path = Path(str(standard_package.get("table_path") or ""))
    rows = _read_deg_rows(table_path)
    filtered_rows = _filter_rows(rows, significance_filter)
    sorted_rows = _sort_rows(filtered_rows, sort_by)
    parameter_manifest = selected.get("parameters_manifest") if isinstance(selected.get("parameters_manifest"), dict) else {}
    dependency_snapshot = selected.get("dependency_snapshot") if isinstance(selected.get("dependency_snapshot"), dict) else {}
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "status": "passed",
        "result_options": _result_options(formal_entries),
        "selected_result_id": str(selected.get("result_id") or ""),
        "summary": _summary(rows, parameter_manifest, dependency_snapshot),
        "rows": sorted_rows,
        "provenance": _provenance(selected, table_path, standard_package=standard_package),
        "guard_copy": _guard_copy(),
        "disabled_downstream": _disabled_downstream(),
        "excluded_results": excluded,
        "blockers": [],
        "warnings": [],
    }


def export_formal_deg_review_table(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    file_format: str = "tsv",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    review = build_formal_deg_result_review(root, result_id=result_id, sort_by="input_order", significance_filter="all")
    if review.get("status") != "passed":
        return {"status": "blocked", "blockers": list(review.get("blockers", []) or []), "warnings": []}
    selected_result_id = str(review.get("selected_result_id") or "formal_deg")
    normalized_format = "csv" if str(file_format).lower() == "csv" else "tsv"
    delimiter = "," if normalized_format == "csv" else "\t"
    export_path = root / EXPORT_DIR / f"{selected_result_id}_review.{normalized_format}"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    with export_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(REVIEW_COLUMNS), delimiter=delimiter)
        writer.writeheader()
        for row in review.get("rows", []) or []:
            if isinstance(row, dict):
                writer.writerow({column: row.get(column, "") for column in REVIEW_COLUMNS})
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
        "warnings": ["export_table_only_not_report_ready"],
    }


def _formal_deg_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    if normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") != "formal_computed_result":
        return None
    if str(entry.get("task_type") or "").lower() != "deg":
        return None
    return entry


def _excluded_entry(entry: dict[str, Any]) -> dict[str, str]:
    return {
        "result_id": str(entry.get("result_id") or entry.get("result_name") or ""),
        "result_semantics": str(entry.get("result_semantics") or ""),
        "task_type": str(entry.get("task_type") or ""),
        "reason": "not_formal_computed_deg_result",
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


def _standard_package_for_result(root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    result_id = str(entry.get("result_id") or "")
    catalog = build_standard_analysis_package_catalog(root)
    package = next(
        (
            row
            for row in catalog.get("rows", []) or []
            if isinstance(row, dict) and str(row.get("result_id") or "") == result_id
        ),
        {},
    )
    if not package:
        return {"status": "blocked", "blocker": "formal_deg_standard_result_package_missing"}
    if str(package.get("validation_status") or "") != "passed":
        return {"status": "blocked", "blocker": "formal_deg_standard_result_package_invalid", "package": package}
    if str(package.get("module_id") or "") != "deg":
        return {"status": "blocked", "blocker": "formal_deg_standard_result_package_module_mismatch", "package": package}
    if normalize_result_semantics(package.get("result_semantics"), default="") != "formal_computed_result":
        return {"status": "blocked", "blocker": "formal_deg_standard_result_package_semantics_invalid", "package": package}
    artifact_manifest = package.get("artifact_manifest") if isinstance(package.get("artifact_manifest"), dict) else {}
    table = next(
        (
            item
            for item in artifact_manifest.get("tables", []) or []
            if isinstance(item, dict) and item.get("artifact_type") == "deg_result_table"
        ),
        {},
    )
    if not table:
        return {"status": "blocked", "blocker": "formal_deg_standard_package_deg_table_missing", "package": package}
    if not bool(table.get("exists")):
        return {"status": "blocked", "blocker": "formal_deg_standard_package_deg_table_file_missing", "package": package}
    if table.get("within_standard_package") is not True:
        return {"status": "blocked", "blocker": "formal_deg_standard_package_deg_table_outside_package", "package": package}
    return {
        "status": "passed",
        "table_path": str(table.get("path") or ""),
        "package_path": str(package.get("package_path") or ""),
        "package_path_relative": str(package.get("package_path_relative") or ""),
        "table_package_relative_path": str(table.get("package_relative_path") or ""),
        "package_validation_status": str(package.get("validation_status") or ""),
        "worker_boundary_type": str(package.get("worker_boundary_type") or ""),
        "worker_migration_status": str(package.get("worker_migration_status") or ""),
    }


def _read_deg_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        reader = csv.DictReader([first, *handle.readlines()], delimiter=delimiter)
        rows = []
        for index, row in enumerate(reader):
            normalized = {column: row.get(column, "") for column in REVIEW_COLUMNS}
            normalized["_input_order"] = index
            rows.append(normalized)
        return rows


def _filter_rows(rows: list[dict[str, Any]], significance_filter: str) -> list[dict[str, Any]]:
    selected = str(significance_filter or "all")
    if selected == "all":
        return list(rows)
    if selected == "significant":
        return [row for row in rows if str(row.get("significance_label") or "") in {"up", "down"}]
    return [row for row in rows if str(row.get("significance_label") or "") == selected]


def _sort_rows(rows: list[dict[str, Any]], sort_by: str) -> list[dict[str, Any]]:
    key = str(sort_by or "adjusted_p_value")
    if key == "input_order":
        return sorted(rows, key=lambda row: int(row.get("_input_order") or 0))
    if key == "significance_label":
        return sorted(rows, key=lambda row: str(row.get("significance_label") or ""))
    numeric_key = {
        "adjusted_p_value": "adjusted_p_value",
        "p_value": "p_value",
        "log2_fold_change": "log2_fold_change",
    }.get(key, "adjusted_p_value")
    reverse = numeric_key == "log2_fold_change"
    return sorted(rows, key=lambda row: _float(row.get(numeric_key), default=float("inf")), reverse=reverse)


def _summary(rows: list[dict[str, Any]], parameter_manifest: dict[str, Any], dependency_snapshot: dict[str, Any]) -> dict[str, Any]:
    packages = dependency_snapshot.get("packages") if isinstance(dependency_snapshot.get("packages"), dict) else {}
    return {
        "total_gene_count": len(rows),
        "significant_up_count": sum(1 for row in rows if str(row.get("significance_label") or "") == "up"),
        "significant_down_count": sum(1 for row in rows if str(row.get("significance_label") or "") == "down"),
        "method": str(parameter_manifest.get("method") or ""),
        "thresholds": {
            "log2fc_threshold": parameter_manifest.get("log2fc_threshold", ""),
            "p_value_threshold": parameter_manifest.get("p_value_threshold", ""),
            "fdr_threshold": parameter_manifest.get("fdr_threshold", ""),
        },
        "sample_counts": {
            "case": len(parameter_manifest.get("case_samples", []) or []),
            "control": len(parameter_manifest.get("control_samples", []) or []),
        },
        "dependency_versions": {
            name: str(status.get("version") or "") for name, status in packages.items() if isinstance(status, dict) and name in {"numpy", "pandas", "scipy", "statsmodels"}
        },
    }


def _provenance(entry: dict[str, Any], table_path: Path, *, standard_package: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_id": str(entry.get("result_id") or ""),
        "task_run_id": str(entry.get("task_run_id") or ""),
        "input_package_id": str(entry.get("input_package_id") or ""),
        "source_repository_manifest": str(entry.get("source_repository_manifest") or ""),
        "parameter_confirmation": "manifests/formal_deg_parameter_confirmation.json",
        "parameters_manifest_present": bool(entry.get("parameters_manifest")),
        "dependency_snapshot_present": bool(entry.get("dependency_snapshot")),
        "task_run_log": entry.get("log_artifacts", []),
        "result_table_path": str(table_path),
        "standard_result_package": str(standard_package.get("package_path_relative") or standard_package.get("package_path") or ""),
        "standard_package_validation_status": str(standard_package.get("package_validation_status") or ""),
        "standard_package_table_path": str(standard_package.get("table_package_relative_path") or ""),
        "standard_package_source_policy": "result_index_registered_standard_result_package_artifacts_only",
        "worker_boundary_type": str(standard_package.get("worker_boundary_type") or ""),
        "worker_migration_status": str(standard_package.get("worker_migration_status") or ""),
        "result_index_path": "results/summaries/result_index.json",
        "plot_artifacts": entry.get("plot_artifacts", []),
        "report_artifacts": entry.get("report_artifacts", []),
        "report_ready_eligible": bool(entry.get("report_ready_eligible")),
    }


def _blocked_provenance(entry: dict[str, Any], standard_package: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_id": str(entry.get("result_id") or ""),
        "task_run_id": str(entry.get("task_run_id") or ""),
        "standard_result_package": str(standard_package.get("package_path_relative") or ""),
        "standard_package_validation_status": str(standard_package.get("package_validation_status") or "missing"),
        "standard_package_source_policy": "result_index_registered_standard_result_package_artifacts_only",
        "result_index_path": "results/summaries/result_index.json",
    }


def _empty_summary() -> dict[str, Any]:
    return {
        "total_gene_count": 0,
        "significant_up_count": 0,
        "significant_down_count": 0,
        "method": "",
        "thresholds": {},
        "sample_counts": {"case": 0, "control": 0},
        "dependency_versions": {},
    }


def _guard_copy() -> str:
    return "Formal DEG review shows statistical analysis results only. It is not a clinical conclusion or treatment recommendation."


def _disabled_downstream() -> dict[str, str]:
    return {
        "plot": "B9.6 plot artifact gate can register formal DEG plot artifacts only from this formal_computed_result source.",
        "report_ready": "Waiting for B9.7 report-ready gate; export table is not report-ready.",
        "gsea": "GSEA is not entered from B9.5.",
        "survival": "Survival/KM/Cox/log-rank are not entered from B9.5.",
    }


def _float(value: object, *, default: float) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default
