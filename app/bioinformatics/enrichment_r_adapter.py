from __future__ import annotations

import csv
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from app.bioinformatics.enrichment_backend import build_enrichment_backend_gate
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


CONTROLLED_ENRICHMENT_R_RUN_SCHEMA_VERSION = "biomedpilot.controlled_enrichment_r_run.v1"
CONTROLLED_ORA_COLUMNS = ("ID", "Description", "GeneRatio", "BgRatio", "pvalue", "p.adjust", "qvalue", "geneID", "Count")
CONTROLLED_GSEA_COLUMNS = ("pathway", "ES", "NES", "pval", "padj", "leadingEdge", "size")
SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


def run_controlled_ora_r_fixture(
    project_root: str | Path,
    *,
    detection_path: str | Path | None = None,
    runner: SubprocessRunner = subprocess.run,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = build_enrichment_backend_gate(root, analysis_type="ora", detection_path=detection_path)
    if gate.get("status") != "passed":
        return _blocked("ora", *[str(item) for item in gate.get("blockers", []) or []], dependency_snapshot=gate)
    result_id = f"controlled-ora-r-{uuid4().hex[:10]}"
    task_run_id = f"task-run-{uuid4().hex[:10]}"
    parameter_manifest = _parameter_manifest("ora", result_id=result_id, task_run_id=task_run_id, dependency_snapshot=gate)
    with tempfile.TemporaryDirectory(prefix="biomedpilot_controlled_ora_r_") as tmpdir:
        work = Path(tmpdir)
        genes_path, term2gene_path, term2name_path = _write_ora_fixture_inputs(work)
        raw_output = work / "ora_result.tsv"
        run_log = _run_rscript(
            gate["rscript"]["path"],
            _ora_r_script(),
            [genes_path, term2gene_path, term2name_path, raw_output],
            runner=runner,
        )
        if run_log["status"] != "passed":
            return _blocked("ora", *[str(item) for item in run_log.get("blockers", []) or []], dependency_snapshot=gate, parameter_manifest=parameter_manifest, rscript_log=run_log)
        validation = _validate_tsv(raw_output, CONTROLLED_ORA_COLUMNS)
        if validation["status"] != "passed":
            return _blocked("ora", *[str(item) for item in validation.get("blockers", []) or []], dependency_snapshot=gate, parameter_manifest=parameter_manifest, rscript_log=run_log)
        result_path = _copy_result_table(root, result_id, raw_output)
    log_path = _write_run_log(root, result_id, task_run_id, "ora", parameter_manifest, gate, run_log)
    manifest_path = _write_parameter_manifest(root, result_id, parameter_manifest)
    return _register_enrichment_result(
        root,
        result_id=result_id,
        task_run_id=task_run_id,
        task_type="ora",
        parameter_manifest=parameter_manifest,
        parameter_manifest_path=manifest_path,
        dependency_snapshot=gate,
        result_path=result_path,
        log_path=log_path,
        engine_name="r_clusterProfiler_enricher",
        engine_version=_package_version(gate, "clusterProfiler"),
        artifact_type="ora_result_table",
    )


def run_controlled_gsea_preranked_r_fixture(
    project_root: str | Path,
    *,
    detection_path: str | Path | None = None,
    runner: SubprocessRunner = subprocess.run,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = build_enrichment_backend_gate(root, analysis_type="gsea_preranked", detection_path=detection_path)
    if gate.get("status") != "passed":
        return _blocked("gsea_preranked", *[str(item) for item in gate.get("blockers", []) or []], dependency_snapshot=gate)
    result_id = f"controlled-gsea-r-{uuid4().hex[:10]}"
    task_run_id = f"task-run-{uuid4().hex[:10]}"
    parameter_manifest = _parameter_manifest("gsea_preranked", result_id=result_id, task_run_id=task_run_id, dependency_snapshot=gate)
    with tempfile.TemporaryDirectory(prefix="biomedpilot_controlled_gsea_r_") as tmpdir:
        work = Path(tmpdir)
        stats_path, pathways_path = _write_gsea_fixture_inputs(work)
        raw_output = work / "gsea_result.tsv"
        run_log = _run_rscript(
            gate["rscript"]["path"],
            _gsea_r_script(),
            [stats_path, pathways_path, raw_output],
            runner=runner,
        )
        if run_log["status"] != "passed":
            return _blocked("gsea_preranked", *[str(item) for item in run_log.get("blockers", []) or []], dependency_snapshot=gate, parameter_manifest=parameter_manifest, rscript_log=run_log)
        validation = _validate_tsv(raw_output, CONTROLLED_GSEA_COLUMNS)
        if validation["status"] != "passed":
            return _blocked("gsea_preranked", *[str(item) for item in validation.get("blockers", []) or []], dependency_snapshot=gate, parameter_manifest=parameter_manifest, rscript_log=run_log)
        result_path = _copy_result_table(root, result_id, raw_output)
    log_path = _write_run_log(root, result_id, task_run_id, "gsea_preranked", parameter_manifest, gate, run_log)
    manifest_path = _write_parameter_manifest(root, result_id, parameter_manifest)
    return _register_enrichment_result(
        root,
        result_id=result_id,
        task_run_id=task_run_id,
        task_type="gsea_preranked",
        parameter_manifest=parameter_manifest,
        parameter_manifest_path=manifest_path,
        dependency_snapshot=gate,
        result_path=result_path,
        log_path=log_path,
        engine_name="r_fgsea_preranked",
        engine_version=_package_version(gate, "fgsea"),
        artifact_type="gsea_preranked_result_table",
    )


def _register_enrichment_result(
    root: Path,
    *,
    result_id: str,
    task_run_id: str,
    task_type: str,
    parameter_manifest: dict[str, Any],
    parameter_manifest_path: Path,
    dependency_snapshot: dict[str, Any],
    result_path: Path,
    log_path: Path,
    engine_name: str,
    engine_version: str,
    artifact_type: str,
) -> dict[str, Any]:
    now = _now()
    entry = ResultIndexEntry(
        result_id=result_id,
        task_run_id=task_run_id,
        task_type=task_type,
        result_semantics="formal_computed_result",
        input_package_id=str(parameter_manifest.get("input_package_id") or ""),
        source_dataset_id="controlled_enrichment_fixture",
        source_repository_manifest=f"controlled_fixture://enrichment/{task_type}/r/v1",
        parameters_manifest=parameter_manifest,
        engine_name=engine_name,
        engine_version=engine_version,
        dependency_snapshot=dependency_snapshot,
        output_artifacts=(
            {"artifact_type": artifact_type, "path": str(result_path.relative_to(root)), "schema": f"biomedpilot.{artifact_type}.v1"},
            {"artifact_type": "enrichment_parameter_manifest", "path": str(parameter_manifest_path.relative_to(root)), "schema": "biomedpilot.enrichment_parameter_manifest.v1"},
        ),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=tuple(str(item) for item in dependency_snapshot.get("warnings", []) or []),
        blockers=(),
        log_artifacts=({"artifact_type": "controlled_enrichment_r_run_log", "path": str(log_path.relative_to(root))},),
        failure_reason="",
        created_at=now,
        updated_at=now,
        report_ready_eligible=False,
    ).to_dict()
    registered = register_result(root, entry)
    return {
        "schema_version": CONTROLLED_ENRICHMENT_R_RUN_SCHEMA_VERSION,
        "status": "passed",
        "analysis_type": task_type,
        "result_id": result_id,
        "task_run_id": task_run_id,
        "result_entry": registered,
        "result_table_path": str(result_path),
        "parameter_manifest_path": str(parameter_manifest_path),
        "dependency_snapshot": dependency_snapshot,
        "plot_artifacts": [],
        "report_artifacts": [],
        "report_ready_eligible": False,
        "warnings": list(registered.get("warnings", []) or []),
        "blockers": [],
    }


def _run_rscript(rscript_path: str, script: str, args: list[Path], *, runner: SubprocessRunner) -> dict[str, Any]:
    command = [rscript_path, "--vanilla", "-e", script, *[str(arg) for arg in args]]
    try:
        result = runner(command, check=False, capture_output=True, text=True, timeout=90)
    except Exception as exc:  # pragma: no cover - defensive boundary around external runtime
        return {"status": "blocked", "command": command, "stdout": "", "stderr": str(exc), "blockers": ["r_enrichment_rscript_execution_failed"]}
    stdout = str(getattr(result, "stdout", "") or "")
    stderr = str(getattr(result, "stderr", "") or "")
    returncode = int(getattr(result, "returncode", 1) or 0)
    return {
        "status": "passed" if returncode == 0 else "blocked",
        "command": command,
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
        "blockers": [] if returncode == 0 else ["r_enrichment_rscript_execution_failed"],
    }


def _write_ora_fixture_inputs(work: Path) -> tuple[Path, Path, Path]:
    genes = work / "ora_genes.txt"
    term2gene = work / "term2gene.tsv"
    term2name = work / "term2name.tsv"
    genes.write_text("TP53\nCDKN1A\nEGFR\n", encoding="utf-8")
    term2gene.write_text(
        "term\tgene\nDNA_DAMAGE\tTP53\nDNA_DAMAGE\tCDKN1A\nDNA_DAMAGE\tEGFR\nHOUSEKEEPING\tGAPDH\nHOUSEKEEPING\tACTB\n",
        encoding="utf-8",
    )
    term2name.write_text("term\tname\nDNA_DAMAGE\tDNA damage response\nHOUSEKEEPING\tHousekeeping genes\n", encoding="utf-8")
    return genes, term2gene, term2name


def _write_gsea_fixture_inputs(work: Path) -> tuple[Path, Path]:
    stats = work / "ranked_stats.tsv"
    pathways = work / "pathways.tsv"
    stats.write_text("gene\tstat\nTP53\t4.2\nCDKN1A\t3.1\nEGFR\t2.7\nGAPDH\t-1.2\nACTB\t-2.5\nBAX\t1.8\n", encoding="utf-8")
    pathways.write_text("pathway\tgene\nDNA_DAMAGE\tTP53\nDNA_DAMAGE\tCDKN1A\nDNA_DAMAGE\tBAX\nHOUSEKEEPING\tGAPDH\nHOUSEKEEPING\tACTB\n", encoding="utf-8")
    return stats, pathways


def _ora_r_script() -> str:
    return r"""
args <- commandArgs(trailingOnly=TRUE)
genes <- readLines(args[[1]], warn=FALSE)
term2gene <- read.delim(args[[2]], stringsAsFactors=FALSE)
term2name <- read.delim(args[[3]], stringsAsFactors=FALSE)
output <- args[[4]]
suppressPackageStartupMessages(library(clusterProfiler))
res <- clusterProfiler::enricher(
  gene=genes,
  universe=unique(term2gene$gene),
  TERM2GENE=term2gene,
  TERM2NAME=term2name,
  pAdjustMethod="BH",
  pvalueCutoff=1,
  qvalueCutoff=1,
  minGSSize=1,
  maxGSSize=500
)
cols <- c("ID", "Description", "GeneRatio", "BgRatio", "pvalue", "p.adjust", "qvalue", "geneID", "Count")
df <- if (is.null(res)) data.frame(matrix(ncol=length(cols), nrow=0)) else as.data.frame(res)
if (nrow(df) == 0) {
  df <- data.frame(matrix(ncol=length(cols), nrow=0))
  colnames(df) <- cols
} else {
  df <- df[, cols, drop=FALSE]
}
write.table(df, file=output, sep="\t", quote=FALSE, row.names=FALSE)
"""


def _gsea_r_script() -> str:
    return r"""
args <- commandArgs(trailingOnly=TRUE)
stats_df <- read.delim(args[[1]], stringsAsFactors=FALSE)
pathway_df <- read.delim(args[[2]], stringsAsFactors=FALSE)
output <- args[[3]]
suppressPackageStartupMessages(library(fgsea))
stats <- stats_df$stat
names(stats) <- stats_df$gene
stats <- sort(stats, decreasing=TRUE)
pathways <- split(pathway_df$gene, pathway_df$pathway)
res <- fgsea::fgsea(pathways=pathways, stats=stats, minSize=1, maxSize=500)
df <- as.data.frame(res)
if (!"leadingEdge" %in% colnames(df)) {
  df$leadingEdge <- ""
} else {
  df$leadingEdge <- vapply(df$leadingEdge, function(x) paste(x, collapse="/"), character(1))
}
cols <- c("pathway", "ES", "NES", "pval", "padj", "leadingEdge", "size")
if (nrow(df) == 0) {
  df <- data.frame(matrix(ncol=length(cols), nrow=0))
  colnames(df) <- cols
} else {
  df <- df[, cols, drop=FALSE]
}
write.table(df, file=output, sep="\t", quote=FALSE, row.names=FALSE)
"""


def _validate_tsv(path: Path, columns: tuple[str, ...]) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "blocked", "blockers": ["r_enrichment_output_missing"], "warnings": []}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        found = list(reader.fieldnames or [])
        missing = [column for column in columns if column not in found]
        rows = list(reader)
    blockers = [f"r_enrichment_output_missing_column:{column}" for column in missing]
    if not rows:
        blockers.append("r_enrichment_output_empty")
    return {"status": "blocked" if blockers else "passed", "columns": found, "row_count": len(rows), "blockers": blockers, "warnings": []}


def _copy_result_table(root: Path, result_id: str, source: Path) -> Path:
    target = root / "results" / "tables" / f"{result_id}.tsv"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _write_parameter_manifest(root: Path, result_id: str, manifest: dict[str, Any]) -> Path:
    path = root / "manifests" / "enrichment" / f"{result_id}_parameters.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_run_log(root: Path, result_id: str, task_run_id: str, analysis_type: str, parameter_manifest: dict[str, Any], dependency_snapshot: dict[str, Any], rscript_log: dict[str, Any]) -> Path:
    path = root / "analysis" / "enrichment" / f"{result_id}_run_log.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "biomedpilot.controlled_enrichment_r_run_log.v1",
        "result_id": result_id,
        "task_run_id": task_run_id,
        "analysis_type": analysis_type,
        "parameter_manifest": parameter_manifest,
        "dependency_snapshot": dependency_snapshot,
        "rscript_log": rscript_log,
        "report_ready_eligible": False,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _parameter_manifest(analysis_type: str, *, result_id: str, task_run_id: str, dependency_snapshot: dict[str, Any]) -> dict[str, Any]:
    capability = "ora_enricher" if analysis_type == "ora" else "gsea_preranked_fgsea"
    return {
        "schema_version": "biomedpilot.enrichment_parameter_manifest.v1",
        "created_at": _now(),
        "analysis_type": analysis_type,
        "result_id": result_id,
        "task_run_id": task_run_id,
        "input_package_id": f"controlled_{analysis_type}_fixture_package",
        "resource_policy": "controlled_fixture_no_download",
        "required_capabilities": [capability],
        "dependency_snapshot_id": dependency_snapshot.get("detection_path", ""),
        "dependency_snapshot": dependency_snapshot,
        "engine_candidate": "r_clusterProfiler_enricher" if analysis_type == "ora" else "r_fgsea_preranked",
        "plot_artifacts": [],
        "report_artifacts": [],
        "report_ready_eligible": False,
        "warnings": [],
        "blockers": [],
    }


def _package_version(gate: dict[str, Any], package: str) -> str:
    packages = gate.get("packages") if isinstance(gate.get("packages"), dict) else {}
    status = packages.get(package) if isinstance(packages.get(package), dict) else {}
    return str(status.get("version") or "unknown")


def _blocked(analysis_type: str, *blockers: str, **payload: Any) -> dict[str, Any]:
    return {
        "schema_version": CONTROLLED_ENRICHMENT_R_RUN_SCHEMA_VERSION,
        "status": "blocked",
        "analysis_type": analysis_type,
        "result_semantics": "blocked",
        "plot_artifacts": [],
        "report_artifacts": [],
        "report_ready_eligible": False,
        "warnings": [],
        "blockers": list(dict.fromkeys(blocker for blocker in blockers if blocker)),
        **payload,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
