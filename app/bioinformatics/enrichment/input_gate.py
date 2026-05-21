from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.bioinformatics.deg_engine.result_schema import validate_formal_deg_result_index_entry
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.project_results import RESULT_INDEX, load_result_index

from .models import (
    ADJUSTED_P_COLUMN_ALIASES,
    GENE_COLUMN_ALIASES,
    LOG2FC_COLUMN_ALIASES,
    ORA_INPUT_SCHEMA_VERSION,
    SIGNIFICANCE_COLUMN_ALIASES,
)


def build_ora_input_gate(
    project_root: str | Path,
    *,
    result_id: str = "",
    adjusted_p_value_threshold: float = 0.05,
    log2fc_threshold: float = 1.0,
    selected_gene_policy: str = "adjusted_p_value_and_abs_log2fc",
    source_gene_universe_policy: str = "source_deg_detected_genes",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    entries = [item for item in load_result_index(root, persist_generated=False).get("entries", []) or [] if isinstance(item, dict)]
    entry = _select_deg_entry(entries, result_id=result_id)
    blockers: list[str] = []
    warnings: list[str] = []
    if entry is None:
        blockers.append("ora_source_deg_result_missing")
        return _payload(root, {}, blockers=blockers, warnings=warnings, selected_gene_policy=selected_gene_policy, source_gene_universe_policy=source_gene_universe_policy)

    source_result_id = str(entry.get("result_id") or entry.get("item_id") or entry.get("result_name") or "")
    task_type = _task_type(entry)
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    if task_type != "deg":
        blockers.append(f"ora_input_requires_deg_result:{task_type or 'missing'}")
    if semantics not in {"formal_computed_result", "imported_external_result"}:
        blockers.append(f"ora_input_semantics_not_allowed:{semantics or 'unknown'}")
    source_type = "formal_deg" if semantics == "formal_computed_result" else "imported_deg" if semantics == "imported_external_result" else "blocked"
    if source_type == "formal_deg":
        validation = validate_formal_deg_result_index_entry(entry)
        if validation.get("status") != "passed":
            blockers.extend(f"formal_deg_result_index:{item}" for item in validation.get("blockers", []) or [])
            warnings.extend(str(item) for item in validation.get("warnings", []) or [])
    if source_type == "imported_deg":
        warnings.append("imported_deg_source_is_external_not_biomedpilot_recomputed")
        if not _has_imported_provenance(entry):
            blockers.append("imported_deg_missing_source_provenance")
        if not _has_confirmed_column_mapping(entry):
            blockers.append("imported_deg_column_mapping_not_confirmed")

    table_path = _deg_table_path(root, entry)
    rows: list[dict[str, str]] = []
    if not table_path:
        blockers.append("ora_source_deg_table_missing")
    elif not table_path.is_file():
        blockers.append("ora_source_deg_table_file_missing")
    else:
        rows = _read_table(table_path)
        if not rows:
            blockers.append("ora_source_deg_table_empty")

    header = set(rows[0].keys()) if rows else set()
    gene_column = _first_present(header, GENE_COLUMN_ALIASES)
    log2fc_column = _first_present(header, LOG2FC_COLUMN_ALIASES)
    adjusted_p_column = _first_present(header, ADJUSTED_P_COLUMN_ALIASES)
    significance_column = _first_present(header, SIGNIFICANCE_COLUMN_ALIASES)
    if rows and not gene_column:
        blockers.append("ora_source_deg_table_missing_gene_column")
    if rows and not adjusted_p_column:
        blockers.append("ora_source_deg_table_missing_adjusted_p_value")
    if rows and not log2fc_column:
        blockers.append("ora_source_deg_table_missing_log2fc")
    if rows and not significance_column and source_type == "imported_deg":
        blockers.append("imported_deg_missing_significance_field")

    background_genes = _unique_genes(rows, gene_column)
    selected_genes = _selected_genes(rows, gene_column, adjusted_p_column, log2fc_column, significance_column, adjusted_p_value_threshold, log2fc_threshold)
    if rows and not background_genes:
        blockers.append("ora_background_universe_empty")
    if rows and not selected_genes:
        blockers.append("ora_selected_gene_list_empty")

    payload = _payload(root, entry, blockers=blockers, warnings=warnings, selected_gene_policy=selected_gene_policy, source_gene_universe_policy=source_gene_universe_policy)
    payload.update(
        {
            "source": source_type,
            "source_result_id": source_result_id,
            "source_result_semantics": semantics or "unknown",
            "source_task_type": task_type or "unknown",
            "source_result_index_path": str(root / RESULT_INDEX),
            "source_deg_table": str(table_path or ""),
            "source_gene_id_type": _gene_id_type(entry),
            "significance_filter_policy": f"adjusted_p_value <= {adjusted_p_value_threshold}",
            "log2fc_filter_policy": f"abs(log2_fold_change) >= {log2fc_threshold}",
            "adjusted_p_value_filter_policy": "requires adjusted_p_value/FDR column",
            "gene_list_count": len(selected_genes),
            "background_universe_count": len(background_genes),
            "allowed_downstream_tasks": ["ora_preflight", "ora_resource_review"] if not blockers else [],
            "provenance": _provenance(entry),
            "selected_genes_preview": selected_genes[:20],
            "background_genes_preview": background_genes[:20],
            "column_mapping": {
                "gene": gene_column,
                "log2_fold_change": log2fc_column,
                "adjusted_p_value": adjusted_p_column,
                "significance": significance_column,
            },
        }
    )
    payload["status"] = "blocked" if blockers else "passed"
    return payload


def _payload(
    root: Path,
    entry: dict[str, Any],
    *,
    blockers: list[str],
    warnings: list[str],
    selected_gene_policy: str,
    source_gene_universe_policy: str,
) -> dict[str, Any]:
    return {
        "schema_version": ORA_INPUT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ora_input_id": f"ora_input_{uuid4().hex[:12]}",
        "source_result_id": str(entry.get("result_id") or entry.get("item_id") or ""),
        "source_result_semantics": normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="unknown") if entry else "missing",
        "source_task_type": _task_type(entry) if entry else "missing",
        "source_result_index_path": str(root / RESULT_INDEX),
        "source_deg_table": "",
        "source_gene_id_type": _gene_id_type(entry) if entry else "unknown",
        "source_gene_universe_policy": source_gene_universe_policy,
        "selected_gene_policy": selected_gene_policy,
        "significance_filter_policy": "",
        "log2fc_filter_policy": "",
        "adjusted_p_value_filter_policy": "",
        "gene_list_count": 0,
        "background_universe_count": 0,
        "allowed_downstream_tasks": [],
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
        "provenance": _provenance(entry) if entry else {},
        "status": "blocked" if blockers else "passed",
    }


def _select_deg_entry(entries: list[dict[str, Any]], *, result_id: str) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or entry.get("item_id") or "") == result_id), None)
    candidates = [entry for entry in entries if _task_type(entry) == "deg"]
    formal = [entry for entry in candidates if normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") == "formal_computed_result"]
    imported = [entry for entry in candidates if normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") == "imported_external_result"]
    return (formal or imported or candidates or entries or [None])[0]


def _task_type(entry: dict[str, Any]) -> str:
    raw = str(entry.get("task_type") or entry.get("analysis_type") or "")
    if raw in {"imported_deg_result", "differential_expression", "differential_expression_deg"}:
        return "deg"
    return raw.lower()


def _deg_table_path(root: Path, entry: dict[str, Any]) -> Path | None:
    for artifact in entry.get("output_artifacts", []) or []:
        if not isinstance(artifact, dict):
            continue
        artifact_type = str(artifact.get("artifact_type") or "")
        if artifact_type and artifact_type != "deg_result_table":
            continue
        raw = str(artifact.get("path") or artifact.get("file_path") or artifact.get("source_path") or "")
        if raw:
            path = Path(raw).expanduser()
            return path if path.is_absolute() else root / path
    raw_path = str(entry.get("path") or entry.get("file_path") or "")
    if raw_path:
        path = Path(raw_path).expanduser()
        return path if path.is_absolute() else root / path
    return None


def _read_table(path: Path) -> list[dict[str, str]]:
    delimiter = "\t" if path.suffix.lower() in {".tsv", ".txt"} else ","
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(2048)
        handle.seek(0)
        if "\t" in sample and sample.count("\t") >= sample.count(","):
            delimiter = "\t"
        return [dict(row) for row in csv.DictReader(handle, delimiter=delimiter)]


def _first_present(header: set[str], aliases: tuple[str, ...]) -> str:
    lookup = {name.lower(): name for name in header}
    for alias in aliases:
        if alias in header:
            return alias
        if alias.lower() in lookup:
            return lookup[alias.lower()]
    return ""


def _unique_genes(rows: list[dict[str, str]], gene_column: str) -> list[str]:
    if not gene_column:
        return []
    return sorted({str(row.get(gene_column) or "").strip() for row in rows if str(row.get(gene_column) or "").strip()})


def _selected_genes(
    rows: list[dict[str, str]],
    gene_column: str,
    adjusted_p_column: str,
    log2fc_column: str,
    significance_column: str,
    adjusted_p_value_threshold: float,
    log2fc_threshold: float,
) -> list[str]:
    if not gene_column:
        return []
    selected: set[str] = set()
    for row in rows:
        gene = str(row.get(gene_column) or "").strip()
        if not gene:
            continue
        padj = _float_or_none(row.get(adjusted_p_column)) if adjusted_p_column else None
        log2fc = _float_or_none(row.get(log2fc_column)) if log2fc_column else None
        label = str(row.get(significance_column) or "").strip().lower() if significance_column else ""
        if padj is not None and log2fc is not None and padj <= adjusted_p_value_threshold and abs(log2fc) >= log2fc_threshold:
            selected.add(gene)
        elif label and label not in {"not_significant", "not significant", "ns", "none"}:
            selected.add(gene)
    return sorted(selected)


def _float_or_none(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _gene_id_type(entry: dict[str, Any]) -> str:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    return str(entry.get("gene_id_type") or parameters.get("gene_id_type") or parameters.get("source_gene_id_type") or "unknown")


def _has_imported_provenance(entry: dict[str, Any]) -> bool:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    return bool(entry.get("provenance") or entry.get("source_provenance") or entry.get("source") or parameters.get("source_file") or entry.get("path"))


def _has_confirmed_column_mapping(entry: dict[str, Any]) -> bool:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    return bool(entry.get("column_mapping_confirmed") or parameters.get("column_mapping_confirmed") or parameters.get("column_mapping"))


def _provenance(entry: dict[str, Any]) -> dict[str, Any]:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    return {
        "result_id": entry.get("result_id") or entry.get("item_id") or "",
        "source": entry.get("source") or parameters.get("source") or "",
        "source_file": entry.get("path") or parameters.get("source_file") or "",
        "task_run_id": entry.get("task_run_id") or "",
        "source_repository_manifest": entry.get("source_repository_manifest") or "",
    }
