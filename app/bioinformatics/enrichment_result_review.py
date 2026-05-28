from __future__ import annotations

import csv
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.project_results import load_result_index


ENRICHMENT_REVIEW_SCHEMA_VERSION = "biomedpilot.enrichment_result_review.v1"
ENRICHMENT_EXPORT_DIR = Path("results") / "exports" / "enrichment_review"
ENRICHMENT_TASK_TYPES = {"ora", "gsea_preranked"}


def build_enrichment_result_review(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    sort_by: str = "adjusted_p_value",
    significance_filter: str = "all",
    top_n: int = 50,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    index = load_result_index(root)
    entries = [item for item in index.get("entries", []) or [] if isinstance(item, dict)]
    formal_entries = [_formal_enrichment_entry(root, entry) for entry in entries]
    formal_entries = [entry for entry in formal_entries if entry is not None]
    excluded_entries = [_excluded_entry(entry) for entry in entries if _formal_enrichment_entry(root, entry) is None]
    selected = _select_entry(formal_entries, result_id)
    if selected is None:
        return {
            "schema_version": ENRICHMENT_REVIEW_SCHEMA_VERSION,
            "status": "blocked",
            "result_options": _result_options(formal_entries),
            "selected_result_id": result_id or "",
            "summary": {},
            "rows": [],
            "excluded_results": excluded_entries,
            "guard_copy": _guard_copy(),
            "blockers": ["formal_enrichment_result_not_found"],
            "warnings": [],
        }
    rows = _read_rows(Path(selected["table_path"]), selected["task_type"])
    rows = _filter_rows(rows, significance_filter)
    rows = _sort_rows(rows, sort_by)
    if top_n > 0:
        rows = rows[:top_n]
    return {
        "schema_version": ENRICHMENT_REVIEW_SCHEMA_VERSION,
        "status": "passed",
        "result_options": _result_options(formal_entries),
        "selected_result_id": selected["result_id"],
        "task_type": selected["task_type"],
        "summary": _summary(selected, rows),
        "rows": rows,
        "excluded_results": excluded_entries,
        "provenance": _provenance(selected),
        "guard_copy": _guard_copy(),
        "plot_status": "disabled_until_enrichment_plot_gate",
        "report_status": "disabled_until_enrichment_section_report_gate",
        "blockers": [],
        "warnings": list(selected.get("warnings", []) or []),
    }


def export_enrichment_review_table(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    file_format: str = "tsv",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    review = build_enrichment_result_review(root, result_id=result_id, sort_by="input_order", significance_filter="all", top_n=0)
    if review.get("status") != "passed":
        return {"status": "blocked", "blockers": list(review.get("blockers", []) or []), "warnings": []}
    fmt = file_format.lower()
    if fmt not in {"tsv", "csv"}:
        return {"status": "blocked", "blockers": [f"unsupported_enrichment_export_format:{file_format}"], "warnings": []}
    selected_result_id = str(review.get("selected_result_id") or "enrichment")
    source = _selected_table(root, selected_result_id)
    if source is None:
        return {"status": "blocked", "blockers": ["enrichment_result_table_missing"], "warnings": []}
    target = root / ENRICHMENT_EXPORT_DIR / f"{_safe_name(selected_result_id)}.{fmt}"
    target.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "tsv":
        shutil.copyfile(source, target)
    else:
        _convert_tsv_to_csv(source, target)
    return {
        "schema_version": "biomedpilot.enrichment_review_export.v1",
        "status": "exported",
        "result_id": selected_result_id,
        "file_format": fmt,
        "export_path": str(target),
        "report_ready_eligible": False,
        "plot_artifacts": [],
        "report_artifacts": [],
        "guard_copy": _guard_copy(),
        "blockers": [],
        "warnings": [],
    }


def _formal_enrichment_entry(root: Path, entry: dict[str, Any]) -> dict[str, Any] | None:
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    task_type = str(entry.get("task_type") or "")
    if semantics != "formal_computed_result" or task_type not in ENRICHMENT_TASK_TYPES:
        return None
    table_path = _result_table_path(root, entry)
    if table_path is None:
        return None
    payload = dict(entry)
    payload["table_path"] = str(table_path)
    return payload


def _result_table_path(root: Path, entry: dict[str, Any]) -> Path | None:
    for artifact in entry.get("output_artifacts", []) or []:
        if not isinstance(artifact, dict):
            continue
        artifact_type = str(artifact.get("artifact_type") or "")
        if artifact_type not in {"ora_result_table", "gsea_preranked_result_table"}:
            continue
        path = Path(str(artifact.get("path") or ""))
        resolved = path if path.is_absolute() else root / path
        if resolved.is_file():
            return resolved
    return None


def _read_rows(path: Path, task_type: str) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = []
        for index, row in enumerate(reader):
            normalized = {str(key): str(value) for key, value in row.items() if key is not None}
            normalized["input_order"] = index
            normalized["analysis_type"] = task_type
            normalized["term_id"] = normalized.get("ID") or normalized.get("pathway") or ""
            normalized["description"] = normalized.get("Description") or normalized.get("pathway") or ""
            normalized["p_value"] = _numeric(normalized.get("pvalue") or normalized.get("pval"))
            normalized["adjusted_p_value"] = _numeric(normalized.get("p.adjust") or normalized.get("padj"))
            normalized["significance_label"] = _significance_label(normalized)
            rows.append(normalized)
        return rows


def _filter_rows(rows: list[dict[str, Any]], significance_filter: str) -> list[dict[str, Any]]:
    if significance_filter == "all":
        return rows
    if significance_filter == "significant":
        return [row for row in rows if row.get("significance_label") == "significant"]
    if significance_filter == "not_significant":
        return [row for row in rows if row.get("significance_label") == "not_significant"]
    if significance_filter == "positive_enrichment":
        return [row for row in rows if _numeric(row.get("NES")) is not None and (_numeric(row.get("NES")) or 0) > 0]
    if significance_filter == "negative_enrichment":
        return [row for row in rows if _numeric(row.get("NES")) is not None and (_numeric(row.get("NES")) or 0) < 0]
    return rows


def _sort_rows(rows: list[dict[str, Any]], sort_by: str) -> list[dict[str, Any]]:
    if sort_by == "input_order":
        return sorted(rows, key=lambda row: int(row.get("input_order") or 0))
    if sort_by in {"p_value", "adjusted_p_value", "NES", "ES", "Count", "size"}:
        return sorted(rows, key=lambda row: (_numeric(row.get(sort_by)) is None, _numeric(row.get(sort_by)) or 0))
    if sort_by == "term_id":
        return sorted(rows, key=lambda row: str(row.get("term_id") or ""))
    return sorted(rows, key=lambda row: (_numeric(row.get("adjusted_p_value")) is None, _numeric(row.get("adjusted_p_value")) or 1.0))


def _summary(entry: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    significant = [row for row in rows if row.get("significance_label") == "significant"]
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    dependency = entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {}
    return {
        "result_id": str(entry.get("result_id") or ""),
        "task_type": str(entry.get("task_type") or ""),
        "term_count": len(rows),
        "significant_term_count": len(significant),
        "fdr_cutoff": parameters.get("fdr_cutoff", ""),
        "p_value_cutoff": parameters.get("p_value_cutoff", ""),
        "engine": str(entry.get("engine_name") or ""),
        "engine_version": str(entry.get("engine_version") or ""),
        "dependency_status": str(dependency.get("status") or ""),
        "created_at": str(entry.get("created_at") or ""),
    }


def _provenance(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_id": str(entry.get("result_id") or ""),
        "task_run_id": str(entry.get("task_run_id") or ""),
        "input_package_id": str(entry.get("input_package_id") or ""),
        "source_dataset_id": str(entry.get("source_dataset_id") or ""),
        "source_repository_manifest": str(entry.get("source_repository_manifest") or ""),
        "parameters_manifest": entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {},
        "dependency_snapshot": entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {},
        "log_artifacts": [dict(item) for item in entry.get("log_artifacts", []) or [] if isinstance(item, dict)],
    }


def _selected_table(root: Path, result_id: str) -> Path | None:
    review = build_enrichment_result_review(root, result_id=result_id, top_n=0)
    if review.get("status") != "passed":
        return None
    for entry in load_result_index(root).get("entries", []) or []:
        if isinstance(entry, dict) and str(entry.get("result_id") or "") == result_id:
            return _result_table_path(root, entry)
    return None


def _select_entry(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    return entries[0] if entries else None


def _excluded_entry(entry: dict[str, Any]) -> dict[str, str]:
    return {
        "result_id": str(entry.get("result_id") or ""),
        "task_type": str(entry.get("task_type") or ""),
        "result_semantics": str(entry.get("result_semantics") or ""),
        "reason": "not_formal_computed_enrichment_result",
    }


def _result_options(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{"result_id": str(entry.get("result_id") or ""), "task_type": str(entry.get("task_type") or ""), "engine": str(entry.get("engine_name") or "")} for entry in entries]


def _significance_label(row: dict[str, Any]) -> str:
    adjusted = _numeric(row.get("adjusted_p_value"))
    return "significant" if adjusted is not None and adjusted <= 0.05 else "not_significant"


def _numeric(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _convert_tsv_to_csv(source: Path, target: Path) -> None:
    with source.open(encoding="utf-8", newline="") as src, target.open("w", encoding="utf-8", newline="") as dst:
        reader = csv.reader(src, delimiter="\t")
        writer = csv.writer(dst)
        writer.writerows(reader)


def _guard_copy() -> str:
    return "Enrichment review is a statistical research result review only; it is not a clinical conclusion, prognosis, diagnosis, or treatment recommendation."


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value) or f"enrichment-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
