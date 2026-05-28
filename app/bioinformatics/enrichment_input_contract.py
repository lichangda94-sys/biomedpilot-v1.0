from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.enrichment_resources import build_enrichment_resource_lock
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry


ENRICHMENT_BACKGROUND_UNIVERSE_SCHEMA_VERSION = "biomedpilot.enrichment_background_universe.v1"
ENRICHMENT_IDENTIFIER_COMPATIBILITY_SCHEMA_VERSION = "biomedpilot.enrichment_identifier_compatibility_gate.v1"
ENRICHMENT_SOURCE_DERIVATION_SCHEMA_VERSION = "biomedpilot.enrichment_source_derivation_manifest.v1"
ENRICHMENT_INPUT_CONTRACT_GATE_SCHEMA_VERSION = "biomedpilot.enrichment_input_contract_gate.v1"
SUPPORTED_ANALYSIS_TYPES = {"ora", "gsea_preranked"}
RANKING_METRIC_COLUMNS = {"statistic", "log2_fold_change", "p_value", "adjusted_p_value"}


def build_enrichment_input_contract_gate(
    project_root: str | Path,
    *,
    analysis_type: str,
    source_result_id: str,
    resource_id: str = "",
    required_species: str = "human",
    required_gene_id_type: str = "symbol",
    log2fc_threshold: float = 1.0,
    fdr_cutoff: float = 0.25,
    ranking_metric: str = "statistic",
    background_strategy: str = "formal_deg_result_table_all_features",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    source_entry = _source_entry(root, source_result_id)
    source_gate = _validate_source_entry(source_entry, source_result_id)
    table_path = _deg_table_path(root, source_entry) if source_gate["status"] != "blocked" else None
    rows = _read_deg_rows(table_path) if table_path else []
    background = build_enrichment_background_universe(
        rows=rows,
        source_result_id=source_result_id,
        source_gene_id_type=_source_gene_id_type(source_entry, required_gene_id_type),
        background_strategy=background_strategy,
    )
    derivation = build_enrichment_source_derivation_manifest(
        rows=rows,
        analysis_type=analysis_type,
        source_result_id=source_result_id,
        log2fc_threshold=log2fc_threshold,
        fdr_cutoff=fdr_cutoff,
        ranking_metric=ranking_metric,
    )
    resource_lock = build_enrichment_resource_lock(
        root,
        analysis_type=analysis_type,
        required_species=required_species,
        required_gene_id_type=required_gene_id_type,
        resource_id=resource_id,
    )
    compatibility = build_enrichment_identifier_compatibility_gate(
        source_gene_id_type=_source_gene_id_type(source_entry, required_gene_id_type),
        resource_lock=resource_lock,
        required_gene_id_type=required_gene_id_type,
    )
    blockers = [
        *_list(source_gate.get("blockers")),
        *_list(background.get("blockers")),
        *_list(derivation.get("blockers")),
        *_list(resource_lock.get("blockers")),
        *_list(compatibility.get("blockers")),
    ]
    warnings = [
        *_list(source_gate.get("warnings")),
        *_list(background.get("warnings")),
        *_list(derivation.get("warnings")),
        *_list(resource_lock.get("warnings")),
        *_list(compatibility.get("warnings")),
    ]
    if analysis_type not in SUPPORTED_ANALYSIS_TYPES:
        blockers.append(f"unsupported_enrichment_analysis_type:{analysis_type}")
    return {
        "schema_version": ENRICHMENT_INPUT_CONTRACT_GATE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "analysis_type": analysis_type,
        "source_result_id": source_result_id,
        "source_result_gate": source_gate,
        "source_table_path": str(table_path or ""),
        "background_universe": background,
        "source_derivation_manifest": derivation,
        "resource_lock": resource_lock,
        "identifier_compatibility_gate": compatibility,
        "semantic_boundary": "input_contract_only_not_enrichment_execution",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_enrichment_background_universe(
    *,
    rows: list[dict[str, str]],
    source_result_id: str,
    source_gene_id_type: str,
    background_strategy: str = "formal_deg_result_table_all_features",
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if background_strategy != "formal_deg_result_table_all_features":
        blockers.append(f"unsupported_background_strategy:{background_strategy or 'missing'}")
    genes = _dedupe(_gene_id(row) for row in rows)
    if not genes:
        blockers.append("background_universe_empty")
    if source_gene_id_type in {"", "unknown"}:
        blockers.append("background_gene_id_type_unknown")
    return {
        "schema_version": ENRICHMENT_BACKGROUND_UNIVERSE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "source_result_id": source_result_id,
        "background_strategy": background_strategy,
        "gene_id_type": source_gene_id_type,
        "gene_count": len(genes),
        "genes_preview": genes[:12],
        "selection_policy": "all_features_from_formal_deg_result_table",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": warnings,
    }


def build_enrichment_source_derivation_manifest(
    *,
    rows: list[dict[str, str]],
    analysis_type: str,
    source_result_id: str,
    log2fc_threshold: float = 1.0,
    fdr_cutoff: float = 0.25,
    ranking_metric: str = "statistic",
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if analysis_type == "ora":
        selected = [
            _gene_id(row)
            for row in rows
            if _abs_float(row.get("log2_fold_change")) >= log2fc_threshold and _float(row.get("adjusted_p_value"), default=1.0) <= fdr_cutoff
        ]
        selected = _dedupe(selected)
        if not selected:
            blockers.append("ora_selected_gene_set_empty")
        return {
            "schema_version": ENRICHMENT_SOURCE_DERIVATION_SCHEMA_VERSION,
            "created_at": _now(),
            "status": "blocked" if blockers else "passed",
            "analysis_type": analysis_type,
            "source_result_id": source_result_id,
            "derivation_policy": "deg_significant_genes_by_abs_log2fc_and_fdr",
            "log2fc_threshold": log2fc_threshold,
            "fdr_cutoff": fdr_cutoff,
            "selected_gene_count": len(selected),
            "selected_genes_preview": selected[:12],
            "blockers": list(dict.fromkeys(blockers)),
            "warnings": warnings,
        }
    if analysis_type == "gsea_preranked":
        if ranking_metric not in RANKING_METRIC_COLUMNS:
            blockers.append(f"unsupported_gsea_ranking_metric:{ranking_metric or 'missing'}")
        ranked: list[dict[str, Any]] = []
        for row in rows:
            gene = _gene_id(row)
            value = _float(row.get(ranking_metric), default=None)
            if gene and value is not None:
                ranked.append({"gene_id": gene, "score": value})
        if not ranked:
            blockers.append("gsea_ranking_metric_empty")
        return {
            "schema_version": ENRICHMENT_SOURCE_DERIVATION_SCHEMA_VERSION,
            "created_at": _now(),
            "status": "blocked" if blockers else "passed",
            "analysis_type": analysis_type,
            "source_result_id": source_result_id,
            "derivation_policy": "deg_result_table_preranked_metric",
            "ranking_metric": ranking_metric,
            "ranked_gene_count": len(ranked),
            "ranked_genes_preview": ranked[:12],
            "blockers": list(dict.fromkeys(blockers)),
            "warnings": warnings,
        }
    blockers.append(f"unsupported_enrichment_analysis_type:{analysis_type}")
    return {
        "schema_version": ENRICHMENT_SOURCE_DERIVATION_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked",
        "analysis_type": analysis_type,
        "source_result_id": source_result_id,
        "blockers": blockers,
        "warnings": warnings,
    }


def build_enrichment_identifier_compatibility_gate(
    *,
    source_gene_id_type: str,
    resource_lock: dict[str, Any],
    required_gene_id_type: str = "symbol",
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    resource_gene_id_type = str(resource_lock.get("gene_id_type") or "unknown")
    if source_gene_id_type in {"", "unknown"}:
        blockers.append("source_gene_id_type_unknown")
    if resource_gene_id_type in {"", "unknown"}:
        blockers.append("resource_gene_id_type_unknown")
    if required_gene_id_type and source_gene_id_type != required_gene_id_type:
        blockers.append(f"source_gene_id_type_mismatch:{source_gene_id_type}!={required_gene_id_type}")
    if source_gene_id_type and resource_gene_id_type and source_gene_id_type != resource_gene_id_type:
        blockers.append(f"source_resource_gene_id_type_mismatch:{source_gene_id_type}!={resource_gene_id_type}")
    if resource_lock.get("status") != "passed":
        warnings.append("resource_lock_not_passed_identifier_check_is_preliminary")
    return {
        "schema_version": ENRICHMENT_IDENTIFIER_COMPATIBILITY_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "source_gene_id_type": source_gene_id_type,
        "resource_gene_id_type": resource_gene_id_type,
        "required_gene_id_type": required_gene_id_type,
        "mapping_policy": "no_automatic_identifier_mapping_without_audited_mapping_manifest",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": warnings,
    }


def _source_entry(root: Path, result_id: str) -> dict[str, Any]:
    if not result_id:
        return {}
    registry = load_registry(root)
    return next((entry for entry in registry.get("results", []) if isinstance(entry, dict) and str(entry.get("result_id") or "") == result_id), {})


def _validate_source_entry(entry: dict[str, Any], result_id: str) -> dict[str, Any]:
    blockers: list[str] = []
    if not result_id:
        blockers.append("enrichment_source_result_id_missing")
    if not entry:
        blockers.append("enrichment_source_result_not_found")
    elif normalize_result_semantics(entry.get("result_semantics"), default="") != "formal_computed_result":
        blockers.append(f"enrichment_source_result_not_formal:{entry.get('result_semantics') or 'missing'}")
    if entry and str(entry.get("task_type") or "").lower() != "deg":
        blockers.append(f"enrichment_source_result_not_deg:{entry.get('task_type') or 'missing'}")
    if entry and not _output_artifact(entry, "deg_result_table"):
        blockers.append("enrichment_source_deg_table_missing")
    return {
        "schema_version": "biomedpilot.enrichment_source_result_gate.v1",
        "status": "blocked" if blockers else "passed",
        "source_result_id": result_id,
        "source_result_semantics": str(entry.get("result_semantics") or ""),
        "task_type": str(entry.get("task_type") or ""),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": [],
    }


def _deg_table_path(root: Path, entry: dict[str, Any]) -> Path | None:
    artifact = _output_artifact(entry, "deg_result_table")
    if not artifact:
        return None
    value = str(artifact.get("path") or "")
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def _output_artifact(entry: dict[str, Any], artifact_type: str) -> dict[str, Any]:
    for artifact in entry.get("output_artifacts", []) or []:
        if isinstance(artifact, dict) and artifact.get("artifact_type") == artifact_type:
            return artifact
    return {}


def _read_deg_rows(path: Path | None) -> list[dict[str, str]]:
    if not path or not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter="\t")]


def _source_gene_id_type(entry: dict[str, Any], default: str) -> str:
    manifest = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    return str(manifest.get("gene_id_type") or manifest.get("source_gene_id_type") or default or "unknown")


def _gene_id(row: dict[str, str]) -> str:
    return str(row.get("gene_symbol") or row.get("feature_id") or row.get("gene_id") or "").strip()


def _float(value: object, *, default: float | None = 0.0) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _abs_float(value: object) -> float:
    parsed = _float(value, default=0.0)
    return abs(float(parsed or 0.0))


def _dedupe(values: Any) -> list[str]:
    rows: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in rows:
            rows.append(text)
    return rows


def _list(value: object) -> list[str]:
    if isinstance(value, list | tuple):
        return [str(item) for item in value if str(item)]
    return []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
