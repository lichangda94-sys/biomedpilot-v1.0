from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry


ENRICHMENT_STATISTICAL_POLICY_SCHEMA_VERSION = "biomedpilot.enrichment_statistical_policy.v1"
ENRICHMENT_RESULT_SCHEMA_GATE_VERSION = "biomedpilot.enrichment_result_schema_gate.v1"
ENRICHMENT_TASK_TYPES = {"ora", "gsea_preranked"}
ORA_COLUMNS = ("ID", "Description", "GeneRatio", "BgRatio", "pvalue", "p.adjust", "qvalue", "geneID", "Count")
GSEA_COLUMNS = ("pathway", "ES", "NES", "pval", "padj", "leadingEdge", "size")
MULTIPLE_TESTING_METHODS = {"BH", "fdr_bh", "Benjamini-Hochberg"}


def build_enrichment_statistical_policy(
    *,
    analysis_type: str,
    p_value_cutoff: float = 0.05,
    fdr_cutoff: float = 0.25,
    min_gene_set_size: int = 1,
    max_gene_set_size: int = 500,
    p_adjust_method: str = "BH",
    q_value_policy: str = "qvalue_column_optional_but_validated_when_present",
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if analysis_type not in ENRICHMENT_TASK_TYPES:
        blockers.append(f"unsupported_enrichment_analysis_type:{analysis_type}")
    if p_adjust_method not in MULTIPLE_TESTING_METHODS:
        blockers.append(f"unsupported_multiple_testing_method:{p_adjust_method or 'missing'}")
    if not 0 < float(p_value_cutoff) <= 1:
        blockers.append("invalid_enrichment_p_value_cutoff")
    if not 0 < float(fdr_cutoff) <= 1:
        blockers.append("invalid_enrichment_fdr_cutoff")
    if min_gene_set_size < 1:
        blockers.append("invalid_min_gene_set_size")
    if max_gene_set_size < min_gene_set_size:
        blockers.append("invalid_max_gene_set_size")
    return {
        "schema_version": ENRICHMENT_STATISTICAL_POLICY_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "analysis_type": analysis_type,
        "p_value_cutoff": p_value_cutoff,
        "fdr_cutoff": fdr_cutoff,
        "min_gene_set_size": min_gene_set_size,
        "max_gene_set_size": max_gene_set_size,
        "p_adjust_method": p_adjust_method,
        "multiple_testing_policy": "Benjamini-Hochberg FDR adjustment required for formal enrichment",
        "q_value_policy": q_value_policy,
        "interpretation_boundary": "statistical_research_only_no_biological_or_clinical_conclusion",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": warnings,
    }


def validate_enrichment_result_schema_gate(project_root: str | Path, *, result_id: str) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    entry = _result_entry(root, result_id)
    blockers: list[str] = []
    warnings: list[str] = []
    if not entry:
        blockers.append("formal_enrichment_result_not_found")
    else:
        blockers.extend(_entry_blockers(entry))
    table_path = _table_path(root, entry) if entry else None
    table_validation = _validate_table(table_path, str(entry.get("task_type") or "") if entry else "")
    blockers.extend(_list(table_validation.get("blockers")))
    warnings.extend(_list(table_validation.get("warnings")))
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    statistical_policy = parameters.get("statistical_policy") if isinstance(parameters.get("statistical_policy"), dict) else {}
    if not statistical_policy:
        blockers.append("enrichment_statistical_policy_missing")
    elif statistical_policy.get("status") != "passed":
        blockers.extend(_list(statistical_policy.get("blockers")) or ["enrichment_statistical_policy_not_passed"])
    for field_name in ("input_contract_gate", "background_universe", "identifier_compatibility_gate", "resource_lock"):
        if not isinstance(parameters.get(field_name), dict) or not parameters.get(field_name):
            blockers.append(f"enrichment_parameters_missing:{field_name}")
    return {
        "schema_version": ENRICHMENT_RESULT_SCHEMA_GATE_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "selected_result_id": result_id,
        "task_type": str(entry.get("task_type") or "") if entry else "",
        "required_result_index_fields": [
            "result_id",
            "task_run_id",
            "task_type",
            "result_semantics",
            "input_package_id",
            "parameters_manifest",
            "engine_name",
            "engine_version",
            "dependency_snapshot",
            "output_artifacts",
            "validation_status",
        ],
        "required_parameter_snapshots": ["statistical_policy", "input_contract_gate", "background_universe", "identifier_compatibility_gate", "resource_lock"],
        "table_validation": table_validation,
        "statistical_policy": statistical_policy,
        "semantic_boundary": "result_schema_gate_only_not_interpretation_or_report_ready",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _entry_blockers(entry: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    if semantics != "formal_computed_result":
        blockers.append(f"enrichment_result_not_formal:{entry.get('result_semantics') or 'missing'}")
    if str(entry.get("task_type") or "") not in ENRICHMENT_TASK_TYPES:
        blockers.append(f"unsupported_enrichment_result_task_type:{entry.get('task_type') or 'missing'}")
    for field_name in ("result_id", "task_run_id", "input_package_id", "parameters_manifest", "engine_name", "engine_version", "dependency_snapshot", "output_artifacts"):
        if not entry.get(field_name):
            blockers.append(f"enrichment_result_missing:{field_name}")
    dependency = entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {}
    if dependency.get("status") != "passed":
        blockers.append("enrichment_dependency_snapshot_not_passed")
    if entry.get("validation_status") not in {"passed", "warning"}:
        blockers.append("enrichment_result_validation_not_passed")
    if entry.get("blockers"):
        blockers.append("enrichment_result_has_blockers")
    return blockers


def _validate_table(path: Path | None, task_type: str) -> dict[str, Any]:
    if not path or not path.is_file():
        return {"status": "blocked", "path": str(path or ""), "row_count": 0, "blockers": ["enrichment_result_table_missing"], "warnings": []}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        columns = list(reader.fieldnames or [])
        rows = list(reader)
    required = ORA_COLUMNS if task_type == "ora" else GSEA_COLUMNS if task_type == "gsea_preranked" else ()
    blockers = [f"enrichment_result_table_missing_column:{column}" for column in required if column not in columns]
    for row_index, row in enumerate(rows, start=1):
        if task_type == "ora":
            blockers.extend(_probability_blockers(row, row_index, ("pvalue", "p.adjust", "qvalue")))
            if _integer(row.get("Count")) is None:
                blockers.append(f"ora_result_invalid_count:row_{row_index}")
        elif task_type == "gsea_preranked":
            blockers.extend(_probability_blockers(row, row_index, ("pval", "padj")))
            for field_name in ("ES", "NES"):
                if _float(row.get(field_name)) is None:
                    blockers.append(f"gsea_result_invalid_numeric:{field_name}:row_{row_index}")
            if _integer(row.get("size")) is None:
                blockers.append(f"gsea_result_invalid_size:row_{row_index}")
    if not rows:
        blockers.append("enrichment_result_table_empty")
    return {"status": "blocked" if blockers else "passed", "path": str(path), "columns": columns, "row_count": len(rows), "blockers": list(dict.fromkeys(blockers)), "warnings": []}


def _probability_blockers(row: dict[str, str], row_index: int, fields: tuple[str, ...]) -> list[str]:
    blockers: list[str] = []
    for field_name in fields:
        if field_name not in row or row.get(field_name) in {"", None}:
            if field_name == "qvalue":
                continue
            blockers.append(f"enrichment_result_missing_probability:{field_name}:row_{row_index}")
            continue
        value = _float(row.get(field_name))
        if value is None or not 0 <= value <= 1:
            blockers.append(f"enrichment_result_invalid_probability:{field_name}:row_{row_index}")
    return blockers


def _result_entry(root: Path, result_id: str) -> dict[str, Any]:
    return next((entry for entry in load_registry(root).get("results", []) if isinstance(entry, dict) and str(entry.get("result_id") or "") == result_id), {})


def _table_path(root: Path, entry: dict[str, Any]) -> Path | None:
    expected = {"ora_result_table", "gsea_preranked_result_table"}
    for artifact in entry.get("output_artifacts", []) or []:
        if isinstance(artifact, dict) and artifact.get("artifact_type") in expected:
            path = Path(str(artifact.get("path") or ""))
            return path if path.is_absolute() else root / path
    return None


def _float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _integer(value: object) -> int | None:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _list(value: object) -> list[str]:
    if isinstance(value, list | tuple):
        return [str(item) for item in value if str(item)]
    return []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
