from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry

from .models import ALLOWED_GSEA_SOURCE_SEMANTICS, GSEA_INPUT_SCHEMA_VERSION
from .rank_metric_gate import build_gsea_rank_metric_gate


def build_gsea_preranked_input_gate(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    rank_metric: str = "signed_log10_fdr_by_log2fc",
    custom_rank_column: str = "",
    duplicate_gene_policy: str = "keep_max_abs_rank",
    minimum_ranked_gene_count: int = 10,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected = _select_source(entries, result_id)
    blockers: list[str] = []
    warnings: list[str] = []
    rank_gate: dict[str, Any] = {
        "status": "blocked",
        "ranked_gene_count": 0,
        "ranked_gene_list_path": "",
        "blockers": ["gsea_source_result_missing"],
        "warnings": [],
    }
    source_table = Path()
    source_gene_id_type = "unknown"
    if selected is None:
        blockers.append("gsea_source_result_missing")
    else:
        semantics = _semantics(selected)
        task_type = str(selected.get("task_type") or "")
        if task_type != "deg":
            blockers.append(f"gsea_input_requires_deg_result:{task_type or 'unknown'}")
        if semantics not in ALLOWED_GSEA_SOURCE_SEMANTICS:
            blockers.append(f"gsea_input_semantics_not_allowed:{semantics or 'unknown'}")
        if selected.get("validation_status") in {"blocked", "failed"}:
            blockers.append("gsea_input_source_validation_status_blocked")
        if selected.get("blockers"):
            blockers.append("gsea_input_source_result_has_blockers")
        source_table = _deg_table_path(root, selected)
        if not source_table.is_file():
            blockers.append("gsea_source_deg_table_missing")
        source_gene_id_type = _source_gene_id_type(selected)
        if semantics == "imported_external_result":
            warnings.append("imported_deg_gsea_preranked_input_requires_external_provenance_label")
            if not _imported_mapping_confirmed(selected):
                blockers.append("gsea_imported_deg_column_mapping_not_confirmed")
            if not _imported_source_present(selected):
                blockers.append("gsea_imported_deg_source_provenance_missing")
        if not blockers:
            rank_gate = build_gsea_rank_metric_gate(
                root,
                source_result_id=str(selected.get("result_id") or ""),
                source_deg_table=source_table,
                source_gene_id_type=source_gene_id_type,
                rank_metric=rank_metric,
                custom_rank_column=custom_rank_column,
                duplicate_gene_policy=duplicate_gene_policy,
                minimum_ranked_gene_count=minimum_ranked_gene_count,
            )
            blockers.extend(str(item) for item in rank_gate.get("blockers", []) or [])
            warnings.extend(str(item) for item in rank_gate.get("warnings", []) or [])
    return {
        "schema_version": GSEA_INPUT_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "gsea_input_id": f"gsea_input_{uuid4().hex[:12]}" if not blockers else "",
        "source_result_id": str((selected or {}).get("result_id") or result_id or ""),
        "source_result_semantics": _semantics(selected or {}),
        "source_task_type": str((selected or {}).get("task_type") or ""),
        "source_result_index_path": str(root / RESULT_INDEX),
        "source_deg_table": str(source_table) if source_table else "",
        "source_gene_id_type": source_gene_id_type,
        "rank_metric": rank_metric,
        "rank_metric_policy": "gsea_preranked_metric_gate_only_no_execution",
        "ranked_gene_list_path": str(rank_gate.get("ranked_gene_list_path") or ""),
        "ranked_gene_count": int(rank_gate.get("ranked_gene_count") or 0),
        "duplicate_gene_policy": duplicate_gene_policy,
        "missing_gene_policy": str(rank_gate.get("missing_gene_policy") or "drop_missing_gene_id"),
        "allowed_downstream_tasks": ["gsea_preranked_preflight"],
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
        "rank_metric_gate": rank_gate,
        "provenance": {
            "source_policy": "result_index_v2_deg_result_only",
            "source_result_id": str((selected or {}).get("result_id") or ""),
            "source_result_semantics": _semantics(selected or {}),
            "source_repository_manifest": str((selected or {}).get("source_repository_manifest") or ""),
            "output_artifacts": list((selected or {}).get("output_artifacts", []) or []),
        },
    }


def _select_source(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    candidates = [entry for entry in entries if str(entry.get("task_type") or "") == "deg" and _semantics(entry) in ALLOWED_GSEA_SOURCE_SEMANTICS]
    return candidates[-1] if candidates else None


def _deg_table_path(root: Path, entry: dict[str, Any]) -> Path:
    artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "deg_result_table"), {})
    path = Path(str(artifact.get("path") or ""))
    return path if path.is_absolute() else root / path


def _source_gene_id_type(entry: dict[str, Any]) -> str:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    return str(parameters.get("gene_id_type") or parameters.get("source_gene_id_type") or parameters.get("gene_id_policy") or "unknown")


def _imported_mapping_confirmed(entry: dict[str, Any]) -> bool:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    return bool(parameters.get("column_mapping_confirmed") or parameters.get("imported_column_mapping_confirmed"))


def _imported_source_present(entry: dict[str, Any]) -> bool:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    return bool(entry.get("source") or entry.get("source_file") or parameters.get("source_file") or parameters.get("external_source"))


def _semantics(entry: dict[str, Any]) -> str:
    return normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
