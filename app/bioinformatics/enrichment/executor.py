from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.bioinformatics.analysis_task_runs import task_run_path
from app.bioinformatics.results.registry import RESULT_INDEX, register_result

from .dependency_check import check_ora_backend_dependencies
from .gene_set_gate import build_ora_gene_set_resource_gate
from .input_gate import build_ora_input_gate
from .models import (
    ADJUSTED_P_COLUMN_ALIASES,
    CONTROLLED_ORA_ENGINE_NAME,
    CONTROLLED_ORA_ENGINE_VERSION,
    GENE_COLUMN_ALIASES,
    LOG2FC_COLUMN_ALIASES,
    ORA_RESULT_TASK_TYPE,
    REQUIRED_ORA_TABLE_COLUMNS,
    SIGNIFICANCE_COLUMN_ALIASES,
)
from .parameter_gate import build_ora_parameter_manifest
from .result_schema import build_ora_result_schema_gate, validate_ora_result_index_entry, validate_ora_result_table_row


CONTROLLED_ORA_RUN_SCHEMA_VERSION = "biomedpilot.controlled_ora_run.v1"


def run_controlled_ora(
    project_root: str | Path,
    *,
    result_id: str = "",
    gene_set_resource_id: str = "",
    gene_set_resource_path: str | Path | None = None,
    test_method: str = "hypergeometric",
    min_gene_set_size: int = 1,
    max_gene_set_size: int = 500,
    p_value_threshold: float = 0.05,
    fdr_threshold: float = 0.05,
    log2fc_threshold: float = 1.0,
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    task_run_id = _unique_run_id(root)
    run_dir = task_run_path(root, "ora", task_run_id)
    run_dir.mkdir(parents=True, exist_ok=False)
    started_at = _now()

    ora_input = build_ora_input_gate(root, result_id=result_id, adjusted_p_value_threshold=fdr_threshold, log2fc_threshold=log2fc_threshold)
    gene_set = build_ora_gene_set_resource_gate(
        root,
        resource_id=gene_set_resource_id,
        resource_path=gene_set_resource_path,
        expected_gene_id_type=str(ora_input.get("source_gene_id_type") or "unknown"),
    )
    parameters = build_ora_parameter_manifest(
        ora_input,
        gene_set,
        min_gene_set_size=min_gene_set_size,
        max_gene_set_size=max_gene_set_size,
        p_value_threshold=p_value_threshold,
        fdr_threshold=fdr_threshold,
        test_method=test_method,
    )
    dependency = dependency_snapshot or check_ora_backend_dependencies()
    schema_gate = build_ora_result_schema_gate(parameter_manifest=parameters)
    blockers = _gate_blockers(ora_input, gene_set, parameters, schema_gate)
    if dependency.get("status") != "passed":
        blockers.extend(str(item) for item in dependency.get("blockers", []) or [])
        blockers.append("ora_dependency_snapshot_not_passed")
        return _blocked(root, run_dir, task_run_id, started_at, ora_input, gene_set, parameters, dependency, blockers, failure_reason="controlled_ora_missing_dependency")

    if blockers:
        return _blocked(root, run_dir, task_run_id, started_at, ora_input, gene_set, parameters, dependency, blockers, failure_reason="controlled_ora_gate_not_passed")

    try:
        from scipy.stats import fisher_exact, hypergeom
        from statsmodels.stats.multitest import multipletests
    except Exception as exc:  # pragma: no cover - depends on broken native installs.
        return _blocked(root, run_dir, task_run_id, started_at, ora_input, gene_set, parameters, dependency, ["ora_dependency_import_failed"], failure_reason=f"{exc.__class__.__name__}: {exc}")

    deg_rows = _read_table(Path(str(ora_input.get("source_deg_table") or "")))
    selected_genes, background_genes = _selected_and_background_genes(deg_rows, fdr_threshold=fdr_threshold, log2fc_threshold=log2fc_threshold)
    if not selected_genes:
        return _blocked(root, run_dir, task_run_id, started_at, ora_input, gene_set, parameters, dependency, ["ora_selected_gene_list_empty"], failure_reason="controlled_ora_empty_selected_gene_list")
    if not background_genes:
        return _blocked(root, run_dir, task_run_id, started_at, ora_input, gene_set, parameters, dependency, ["ora_background_universe_empty"], failure_reason="controlled_ora_empty_background_universe")

    gene_sets = _read_gmt(Path(str(gene_set.get("resource_path") or "")))
    rows: list[dict[str, Any]] = []
    skipped_terms = 0
    for term_id, description, genes in gene_sets:
        term_background = sorted(set(genes) & background_genes)
        gene_set_size = len(term_background)
        if gene_set_size < min_gene_set_size or gene_set_size > max_gene_set_size:
            skipped_terms += 1
            continue
        overlap = sorted(set(term_background) & selected_genes)
        p_value = _p_value(
            method=test_method,
            hypergeom=hypergeom,
            fisher_exact=fisher_exact,
            background_size=len(background_genes),
            gene_set_size=gene_set_size,
            selected_gene_count=len(selected_genes),
            overlap_count=len(overlap),
        )
        rows.append(
            {
                "term_id": term_id,
                "term_name": description or term_id,
                "gene_set_size": gene_set_size,
                "overlap_count": len(overlap),
                "overlap_genes": ";".join(overlap),
                "background_size": len(background_genes),
                "selected_gene_count": len(selected_genes),
                "p_value": p_value,
                "adjusted_p_value": "",
                "enrichment_ratio": _enrichment_ratio(len(overlap), len(selected_genes), gene_set_size, len(background_genes)),
                "source_gene_list": str(parameters.get("selected_gene_rule") or "adjusted_p_value_and_abs_log2fc"),
                "warnings": "",
            }
        )
    if rows:
        adjusted = multipletests([float(row["p_value"]) for row in rows], method="fdr_bh")[1]
        for row, value in zip(rows, adjusted, strict=False):
            row["adjusted_p_value"] = float(value)
    warnings = list(dict.fromkeys([str(item) for item in parameters.get("warnings", []) or []]))
    if not rows:
        warnings.append("ora_no_gene_sets_tested_after_size_filter")
    elif not any(int(row.get("overlap_count") or 0) > 0 for row in rows):
        warnings.append("ora_no_overlap_terms_detected")
    if skipped_terms:
        warnings.append(f"ora_gene_sets_skipped_by_size_filter:{skipped_terms}")
    rows.sort(key=lambda row: (float(row.get("adjusted_p_value") or 1.0), float(row.get("p_value") or 1.0), str(row.get("term_id") or "")))

    result_id_value = f"ora-{uuid4().hex[:10]}"
    table_path = _write_ora_table(root, result_id_value, rows)
    _write_task_run_files(
        root,
        run_dir,
        task_run_id,
        started_at,
        status="completed",
        ora_input=ora_input,
        gene_set=gene_set,
        parameters=parameters,
        dependency=dependency,
        output_table=table_path,
        result_id=result_id_value,
        warnings=warnings,
        blockers=[],
        failure_reason="",
    )
    now = _now()
    source_semantics = str(ora_input.get("source_result_semantics") or "")
    result_semantics = "formal_computed_result" if source_semantics == "formal_computed_result" else "imported_external_result"
    if result_semantics == "imported_external_result":
        warnings.append("imported_deg_derived_ora_not_biomedpilot_recomputed_deg_formal_ora")
    entry = {
        "result_id": result_id_value,
        "task_run_id": task_run_id,
        "task_type": ORA_RESULT_TASK_TYPE,
        "result_semantics": result_semantics,
        "input_package_id": str(ora_input.get("ora_input_id") or ""),
        "ora_input_id": str(ora_input.get("ora_input_id") or ""),
        "source_dataset_id": "",
        "source_repository_manifest": str((ora_input.get("provenance") or {}).get("source_repository_manifest") if isinstance(ora_input.get("provenance"), dict) else ""),
        "source_deg_result_id": str(ora_input.get("source_result_id") or ""),
        "source_result_semantics": source_semantics,
        "gene_set_resource_id": str(gene_set.get("gene_set_resource_id") or ""),
        "parameters_manifest": parameters,
        "engine_name": CONTROLLED_ORA_ENGINE_NAME,
        "engine_version": CONTROLLED_ORA_ENGINE_VERSION,
        "dependency_snapshot": dependency,
        "output_artifacts": [{"artifact_type": "ora_result_table", "path": str(table_path.relative_to(root)), "schema": "biomedpilot.ora_result_table.v1"}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": [],
        "log_artifacts": [{"artifact_type": "controlled_ora_task_run_log", "path": str((run_dir / "task_run.json").relative_to(root))}],
        "failure_reason": "",
        "created_at": now,
        "updated_at": now,
        "schema_version": "biomedpilot.result_index_entry.v1",
        "report_ready_eligible": False,
        "migration_status": "native_v2",
    }
    validation = validate_ora_result_index_entry(entry)
    if validation.get("status") != "passed":
        return _blocked(root, run_dir, task_run_id, started_at, ora_input, gene_set, parameters, dependency, [str(item) for item in validation.get("blockers", []) or []], failure_reason="controlled_ora_result_schema_failed")
    registered = register_result(root, entry)
    return {
        "schema_version": CONTROLLED_ORA_RUN_SCHEMA_VERSION,
        "status": "passed",
        "result_id": result_id_value,
        "task_run_id": task_run_id,
        "result_entry": registered,
        "result_table_path": str(table_path),
        "result_index_path": str(root / RESULT_INDEX),
        "task_run_path": str(run_dir / "task_run.json"),
        "ora_input": ora_input,
        "gene_set_resource": gene_set,
        "parameter_manifest": parameters,
        "dependency_snapshot": dependency,
        "warnings": list(registered.get("warnings", []) or []),
        "blockers": [],
        "plot_artifacts": [],
        "report_artifacts": [],
        "report_ready_eligible": False,
    }


def _blocked(
    root: Path,
    run_dir: Path,
    task_run_id: str,
    started_at: str,
    ora_input: dict[str, Any],
    gene_set: dict[str, Any],
    parameters: dict[str, Any],
    dependency: dict[str, Any],
    blockers: list[str],
    *,
    failure_reason: str,
) -> dict[str, Any]:
    unique_blockers = list(dict.fromkeys(blocker for blocker in blockers if blocker))
    _write_task_run_files(
        root,
        run_dir,
        task_run_id,
        started_at,
        status="failed",
        ora_input=ora_input,
        gene_set=gene_set,
        parameters=parameters,
        dependency=dependency,
        output_table=None,
        result_id="",
        warnings=[],
        blockers=unique_blockers,
        failure_reason=failure_reason,
    )
    status = "blocked_missing_dependency" if any("missing_python_package" in item or "dependency" in item for item in unique_blockers) else "blocked"
    return {
        "schema_version": CONTROLLED_ORA_RUN_SCHEMA_VERSION,
        "status": status,
        "result_semantics": "blocked",
        "task_run_id": task_run_id,
        "task_run_path": str(run_dir / "task_run.json"),
        "ora_input": ora_input,
        "gene_set_resource": gene_set,
        "parameter_manifest": parameters,
        "dependency_snapshot": dependency,
        "warnings": [],
        "blockers": unique_blockers,
        "failure_reason": failure_reason,
        "plot_artifacts": [],
        "report_artifacts": [],
        "report_ready_eligible": False,
    }


def _write_task_run_files(
    root: Path,
    run_dir: Path,
    task_run_id: str,
    started_at: str,
    *,
    status: str,
    ora_input: dict[str, Any],
    gene_set: dict[str, Any],
    parameters: dict[str, Any],
    dependency: dict[str, Any],
    output_table: Path | None,
    result_id: str,
    warnings: list[str],
    blockers: list[str],
    failure_reason: str,
) -> None:
    finished_at = _now()
    output_table_text = str(output_table.relative_to(root)) if output_table is not None else ""
    payload = {
        "schema_version": "bioinformatics_analysis_task_run.v1",
        "run_id": task_run_id,
        "task_run_id": task_run_id,
        "task_type": ORA_RESULT_TASK_TYPE,
        "task_family": "ora",
        "status": status,
        "execution_mode": "controlled_ora_mvp",
        "ora_input_id": ora_input.get("ora_input_id", ""),
        "source_result_id": ora_input.get("source_result_id", ""),
        "gene_set_resource_id": gene_set.get("gene_set_resource_id", ""),
        "parameters_manifest": parameters,
        "dependency_snapshot": dependency,
        "outputs": [{"artifact_type": "ora_result_table", "path": output_table_text}] if output_table_text else [],
        "output_table": output_table_text,
        "result_id": result_id,
        "result_index_path": str(RESULT_INDEX),
        "warnings": warnings,
        "blockers": blockers,
        "failure_reason": failure_reason,
        "error": failure_reason or None,
        "created_at": started_at,
        "updated_at": finished_at,
        "started_at": started_at,
        "finished_at": finished_at,
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / "task_run.json", payload)
    _write_json(run_dir / "parameters.json", parameters)
    _write_json(run_dir / "dependency_snapshot.json", dependency)
    _write_json(run_dir / "outputs_manifest.json", {"schema_version": "bioinformatics_analysis_task_run_outputs.v1", "outputs": payload["outputs"]})
    (run_dir / "logs" / "task.log").write_text(f"controlled ORA {status}: {failure_reason or result_id}\n", encoding="utf-8")


def _gate_blockers(*gates: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for gate in gates:
        if gate.get("status") != "passed" and gate.get("validation_status") != "passed":
            blockers.extend(str(item) for item in gate.get("blockers", []) or [])
    return list(dict.fromkeys(blockers))


def _read_table(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    delimiter = "\t" if path.suffix.lower() in {".tsv", ".txt"} else ","
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(2048)
        handle.seek(0)
        if "\t" in sample and sample.count("\t") >= sample.count(","):
            delimiter = "\t"
        return [dict(row) for row in csv.DictReader(handle, delimiter=delimiter)]


def _read_gmt(path: Path) -> list[tuple[str, str, list[str]]]:
    gene_sets: list[tuple[str, str, list[str]]] = []
    if not path.is_file():
        return gene_sets
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        parts = [part.strip() for part in line.split("\t")]
        if len(parts) >= 3:
            genes = [gene for gene in parts[2:] if gene]
            if genes:
                gene_sets.append((parts[0], parts[1], genes))
    return gene_sets


def _selected_and_background_genes(rows: list[dict[str, str]], *, fdr_threshold: float, log2fc_threshold: float) -> tuple[set[str], set[str]]:
    header = set(rows[0].keys()) if rows else set()
    gene_column = _first_present(header, GENE_COLUMN_ALIASES)
    fdr_column = _first_present(header, ADJUSTED_P_COLUMN_ALIASES)
    log2fc_column = _first_present(header, LOG2FC_COLUMN_ALIASES)
    significance_column = _first_present(header, SIGNIFICANCE_COLUMN_ALIASES)
    selected: set[str] = set()
    background: set[str] = set()
    for row in rows:
        gene = str(row.get(gene_column) or "").strip() if gene_column else ""
        if not gene:
            continue
        background.add(gene)
        fdr = _float_or_none(row.get(fdr_column)) if fdr_column else None
        log2fc = _float_or_none(row.get(log2fc_column)) if log2fc_column else None
        label = str(row.get(significance_column) or "").strip().lower() if significance_column else ""
        if fdr is not None and log2fc is not None and fdr <= fdr_threshold and abs(log2fc) >= log2fc_threshold:
            selected.add(gene)
        elif label and label not in {"not_significant", "not significant", "ns", "none"}:
            selected.add(gene)
    return selected, background


def _first_present(header: set[str], aliases: tuple[str, ...]) -> str:
    lookup = {name.lower(): name for name in header}
    for alias in aliases:
        if alias in header:
            return alias
        if alias.lower() in lookup:
            return lookup[alias.lower()]
    return ""


def _p_value(*, method: str, hypergeom: Any, fisher_exact: Any, background_size: int, gene_set_size: int, selected_gene_count: int, overlap_count: int) -> float:
    if background_size <= 0 or gene_set_size <= 0 or selected_gene_count <= 0:
        return 1.0
    if method == "fisher_exact":
        table = [
            [overlap_count, max(0, selected_gene_count - overlap_count)],
            [max(0, gene_set_size - overlap_count), max(0, background_size - gene_set_size - selected_gene_count + overlap_count)],
        ]
        return float(fisher_exact(table, alternative="greater").pvalue)
    return float(hypergeom.sf(max(0, overlap_count - 1), background_size, gene_set_size, selected_gene_count))


def _enrichment_ratio(overlap_count: int, selected_gene_count: int, gene_set_size: int, background_size: int) -> float:
    if overlap_count <= 0 or selected_gene_count <= 0 or gene_set_size <= 0 or background_size <= 0:
        return 0.0
    return (overlap_count / selected_gene_count) / (gene_set_size / background_size)


def _write_ora_table(root: Path, result_id: str, rows: list[dict[str, Any]]) -> Path:
    path = root / "results" / "tables" / f"{result_id}_ora.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(REQUIRED_ORA_TABLE_COLUMNS), delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            validation = validate_ora_result_table_row(row)
            if validation.get("status") != "passed":
                row = {**row, "warnings": ";".join(str(item) for item in validation.get("blockers", []) or [])}
            writer.writerow({column: _format(row.get(column, "")) for column in REQUIRED_ORA_TABLE_COLUMNS})
    return path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _format(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"
    return "" if value is None else str(value)


def _float_or_none(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _unique_run_id(root: Path) -> str:
    for _ in range(20):
        candidate = f"ora_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
        if not task_run_path(root, "ora", candidate).exists():
            return candidate
    raise RuntimeError("Unable to create unique ORA run id.")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
