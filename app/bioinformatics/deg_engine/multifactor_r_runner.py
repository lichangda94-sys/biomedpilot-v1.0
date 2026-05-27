from __future__ import annotations

import csv
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result

from .models import REQUIRED_DEG_RESULT_COLUMNS
from .multifactor_confirmation import build_multifactor_deg_parameter_manifest, save_multifactor_deg_parameter_confirmation, validate_multifactor_deg_parameter_confirmation
from .multifactor_schema import build_multifactor_deg_result_schema_gate, validate_multifactor_deg_result_bundle, validate_multifactor_deg_result_index_entry


MULTIFACTOR_DEG_RUN_SCHEMA_VERSION = "biomedpilot.multifactor_deg_controlled_run.v1"
MULTIFACTOR_DEG_FIXTURE_SCHEMA_VERSION = "biomedpilot.multifactor_deg_fixture.v1"
SUPPORTED_MULTIFACTOR_R_METHODS = {"limma": "limma", "DESeq2": "DESeq2", "edgeR": "edgeR"}


def check_multifactor_r_backend(method: str) -> dict[str, Any]:
    package = SUPPORTED_MULTIFACTOR_R_METHODS.get(method)
    blockers: list[str] = []
    rscript = shutil.which("Rscript")
    if not rscript:
        blockers.append("missing_rscript")
    package_status = {"available": False, "version": "", "missing_reason": ""}
    r_version = ""
    if rscript:
        r_version = _run_version_command([rscript, "--version"])
    if not package:
        blockers.append(f"unsupported_multifactor_r_method:{method}")
    elif rscript:
        package_status = _detect_r_package(rscript, package)
        if not package_status["available"]:
            blockers.append(f"missing_r_package:{package}")
    return {
        "schema_version": "biomedpilot.multifactor_deg_r_dependency_snapshot.v1",
        "status": "blocked" if blockers else "passed",
        "engine_candidate": f"r_{method}_multifactor",
        "dependency_policy": "detect_first_external_rscript_and_bioconductor_package",
        "rscript": {"available": bool(rscript), "path": rscript or "", "version": r_version, "packaging_impact": "external_runtime_not_bundled"},
        "r_backend": {"packages": {"R": {"available": bool(rscript), "version": r_version}, str(package or method): package_status}},
        "blockers": blockers,
        "warnings": ["r_backend_detect_first_no_auto_install"],
        "install_action": "none_detect_first_only",
        "packaging_impact": "Rscript_and_Bioconductor_packages_must_be_available_on_user_system",
    }


def run_controlled_multifactor_limma_fixture(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    dependency = check_multifactor_r_backend("limma")
    deg_ready = _fixture_deg_ready_package(value_type="log_expression")
    design = _fixture_design_manifest()
    parameter_manifest = build_multifactor_deg_parameter_manifest(deg_ready, design_manifest=design, method="limma", dependency_snapshot=dependency)
    confirmation = save_multifactor_deg_parameter_confirmation(root, deg_ready_package=deg_ready, design_manifest=design, method="limma", dependency_snapshot=dependency)
    confirmation_gate = validate_multifactor_deg_parameter_confirmation(confirmation, parameter_manifest=parameter_manifest, dependency_snapshot=dependency)
    schema_gate = build_multifactor_deg_result_schema_gate(parameter_manifest=parameter_manifest, dependency_snapshot=dependency)
    blockers = [
        *[str(item) for item in dependency.get("blockers", []) or []],
        *[str(item) for item in parameter_manifest.get("blockers", []) or []],
        *[str(item) for item in confirmation_gate.get("blockers", []) or []],
        *[str(item) for item in schema_gate.get("blockers", []) or []],
    ]
    if blockers:
        return _blocked(*blockers, parameter_manifest=parameter_manifest, dependency_snapshot=dependency, confirmation_gate=confirmation_gate, result_schema_gate=schema_gate)

    result_id = str(confirmation["output_plan"]["result_id"])
    task_run_id = str(confirmation["output_plan"]["task_run_id"])
    with tempfile.TemporaryDirectory(prefix="biomedpilot_multifactor_limma_") as workdir:
        work = Path(workdir)
        matrix_path = _write_fixture_matrix(work)
        metadata_path = _write_fixture_metadata(work)
        raw_output = work / "limma_output.tsv"
        run_log = _run_limma_rscript(dependency["rscript"]["path"], matrix_path, metadata_path, raw_output)
        if run_log["status"] != "passed":
            return _blocked(*[str(item) for item in run_log.get("blockers", []) or []], parameter_manifest=parameter_manifest, dependency_snapshot=dependency, rscript_log=run_log)
        rows = _read_limma_rows(raw_output, _fixture_group_means(matrix_path))

    bundle = {
        "schema_version": MULTIFACTOR_DEG_FIXTURE_SCHEMA_VERSION,
        "status": "passed",
        "result_semantics": "formal_computed_result",
        "engine_name": "r_limma_multifactor",
        "engine_version": _package_version(dependency, "limma"),
        "input_package_id": str(parameter_manifest.get("input_package_id") or ""),
        "deg_ready_package_id": str(parameter_manifest.get("deg_ready_package_id") or ""),
        "parameters_manifest": parameter_manifest,
        "dependency_snapshot": dependency,
        "rows": rows,
        "warnings": [],
        "blockers": [],
    }
    bundle_validation = validate_multifactor_deg_result_bundle(bundle)
    if bundle_validation["status"] != "passed":
        return _blocked(*[str(item) for item in bundle_validation.get("blockers", []) or []], parameter_manifest=parameter_manifest, dependency_snapshot=dependency, result_bundle=bundle)

    output_path = _write_deg_table(root, result_id, rows)
    log_path = _write_run_log(root, result_id, task_run_id, bundle, run_log)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = ResultIndexEntry(
        result_id=result_id,
        task_run_id=task_run_id,
        task_type="deg",
        result_semantics="formal_computed_result",
        input_package_id=str(parameter_manifest.get("input_package_id") or ""),
        source_dataset_id="controlled_multifactor_fixture",
        source_repository_manifest="controlled_fixture://multifactor_deg/limma/v1",
        parameters_manifest=parameter_manifest,
        engine_name="r_limma_multifactor",
        engine_version=_package_version(dependency, "limma"),
        dependency_snapshot=dependency,
        output_artifacts=({"artifact_type": "deg_result_table", "path": str(output_path.relative_to(root)), "schema": "biomedpilot.deg_result_table.v1"},),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=tuple(str(item) for item in bundle.get("warnings", []) or []),
        blockers=(),
        log_artifacts=({"artifact_type": "multifactor_deg_run_log", "path": str(log_path.relative_to(root))},),
        failure_reason="",
        created_at=now,
        updated_at=now,
        report_ready_eligible=False,
    ).to_dict()
    entry_validation = validate_multifactor_deg_result_index_entry(entry)
    if entry_validation["status"] != "passed":
        return _blocked(*[str(item) for item in entry_validation.get("blockers", []) or []], parameter_manifest=parameter_manifest, dependency_snapshot=dependency, result_bundle=bundle, result_entry=entry)
    registered = register_result(root, entry)
    return {
        "schema_version": MULTIFACTOR_DEG_RUN_SCHEMA_VERSION,
        "status": "passed",
        "method": "limma",
        "result_id": result_id,
        "task_run_id": task_run_id,
        "result_entry": registered,
        "result_table_path": str(output_path),
        "task_run_log_path": str(log_path),
        "parameter_manifest": parameter_manifest,
        "dependency_snapshot": dependency,
        "warnings": list(registered.get("warnings", []) or []),
        "blockers": [],
    }


def run_controlled_multifactor_deseq2_fixture(project_root: str | Path, *, value_type: str = "count") -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    dependency = check_multifactor_r_backend("DESeq2")
    deg_ready = _fixture_deg_ready_package(value_type=value_type)
    design = _fixture_design_manifest()
    parameter_manifest = build_multifactor_deg_parameter_manifest(deg_ready, design_manifest=design, method="DESeq2", dependency_snapshot=dependency)
    confirmation = save_multifactor_deg_parameter_confirmation(root, deg_ready_package=deg_ready, design_manifest=design, method="DESeq2", dependency_snapshot=dependency)
    confirmation_gate = validate_multifactor_deg_parameter_confirmation(confirmation, parameter_manifest=parameter_manifest, dependency_snapshot=dependency)
    schema_gate = build_multifactor_deg_result_schema_gate(parameter_manifest=parameter_manifest, dependency_snapshot=dependency)
    blockers = [
        *[str(item) for item in dependency.get("blockers", []) or []],
        *[str(item) for item in parameter_manifest.get("blockers", []) or []],
        *[str(item) for item in confirmation_gate.get("blockers", []) or []],
        *[str(item) for item in schema_gate.get("blockers", []) or []],
    ]
    if blockers:
        return _blocked(*blockers, parameter_manifest=parameter_manifest, dependency_snapshot=dependency, confirmation_gate=confirmation_gate, result_schema_gate=schema_gate)

    result_id = str(confirmation["output_plan"]["result_id"])
    task_run_id = str(confirmation["output_plan"]["task_run_id"])
    with tempfile.TemporaryDirectory(prefix="biomedpilot_multifactor_deseq2_") as workdir:
        work = Path(workdir)
        matrix_path = _write_count_fixture_matrix(work)
        metadata_path = _write_fixture_metadata(work)
        raw_output = work / "deseq2_output.tsv"
        run_log = _run_deseq2_rscript(dependency["rscript"]["path"], matrix_path, metadata_path, raw_output)
        if run_log["status"] != "passed":
            return _blocked(*[str(item) for item in run_log.get("blockers", []) or []], parameter_manifest=parameter_manifest, dependency_snapshot=dependency, rscript_log=run_log)
        rows = _read_deseq2_rows(raw_output, _fixture_group_means(matrix_path))

    bundle = {
        "schema_version": MULTIFACTOR_DEG_FIXTURE_SCHEMA_VERSION,
        "status": "passed",
        "result_semantics": "formal_computed_result",
        "engine_name": "r_deseq2_multifactor",
        "engine_version": _package_version(dependency, "DESeq2"),
        "input_package_id": str(parameter_manifest.get("input_package_id") or ""),
        "deg_ready_package_id": str(parameter_manifest.get("deg_ready_package_id") or ""),
        "parameters_manifest": parameter_manifest,
        "dependency_snapshot": dependency,
        "rows": rows,
        "warnings": [],
        "blockers": [],
    }
    bundle_validation = validate_multifactor_deg_result_bundle(bundle)
    if bundle_validation["status"] != "passed":
        return _blocked(*[str(item) for item in bundle_validation.get("blockers", []) or []], parameter_manifest=parameter_manifest, dependency_snapshot=dependency, result_bundle=bundle)

    output_path = _write_deg_table(root, result_id, rows)
    log_path = _write_run_log(root, result_id, task_run_id, bundle, run_log)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = ResultIndexEntry(
        result_id=result_id,
        task_run_id=task_run_id,
        task_type="deg",
        result_semantics="formal_computed_result",
        input_package_id=str(parameter_manifest.get("input_package_id") or ""),
        source_dataset_id="controlled_multifactor_fixture",
        source_repository_manifest="controlled_fixture://multifactor_deg/deseq2/v1",
        parameters_manifest=parameter_manifest,
        engine_name="r_deseq2_multifactor",
        engine_version=_package_version(dependency, "DESeq2"),
        dependency_snapshot=dependency,
        output_artifacts=({"artifact_type": "deg_result_table", "path": str(output_path.relative_to(root)), "schema": "biomedpilot.deg_result_table.v1"},),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=tuple(str(item) for item in bundle.get("warnings", []) or []),
        blockers=(),
        log_artifacts=({"artifact_type": "multifactor_deg_run_log", "path": str(log_path.relative_to(root))},),
        failure_reason="",
        created_at=now,
        updated_at=now,
        report_ready_eligible=False,
    ).to_dict()
    entry_validation = validate_multifactor_deg_result_index_entry(entry)
    if entry_validation["status"] != "passed":
        return _blocked(*[str(item) for item in entry_validation.get("blockers", []) or []], parameter_manifest=parameter_manifest, dependency_snapshot=dependency, result_bundle=bundle, result_entry=entry)
    registered = register_result(root, entry)
    return {
        "schema_version": MULTIFACTOR_DEG_RUN_SCHEMA_VERSION,
        "status": "passed",
        "method": "DESeq2",
        "result_id": result_id,
        "task_run_id": task_run_id,
        "result_entry": registered,
        "result_table_path": str(output_path),
        "task_run_log_path": str(log_path),
        "parameter_manifest": parameter_manifest,
        "dependency_snapshot": dependency,
        "warnings": list(registered.get("warnings", []) or []),
        "blockers": [],
    }


def run_controlled_multifactor_edger_fixture(project_root: str | Path, *, value_type: str = "count") -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    dependency = check_multifactor_r_backend("edgeR")
    deg_ready = _fixture_deg_ready_package(value_type=value_type)
    design = _fixture_design_manifest()
    parameter_manifest = build_multifactor_deg_parameter_manifest(deg_ready, design_manifest=design, method="edgeR", dependency_snapshot=dependency)
    confirmation = save_multifactor_deg_parameter_confirmation(root, deg_ready_package=deg_ready, design_manifest=design, method="edgeR", dependency_snapshot=dependency)
    confirmation_gate = validate_multifactor_deg_parameter_confirmation(confirmation, parameter_manifest=parameter_manifest, dependency_snapshot=dependency)
    schema_gate = build_multifactor_deg_result_schema_gate(parameter_manifest=parameter_manifest, dependency_snapshot=dependency)
    blockers = [
        *[str(item) for item in dependency.get("blockers", []) or []],
        *[str(item) for item in parameter_manifest.get("blockers", []) or []],
        *[str(item) for item in confirmation_gate.get("blockers", []) or []],
        *[str(item) for item in schema_gate.get("blockers", []) or []],
    ]
    if blockers:
        return _blocked(*blockers, parameter_manifest=parameter_manifest, dependency_snapshot=dependency, confirmation_gate=confirmation_gate, result_schema_gate=schema_gate)

    result_id = str(confirmation["output_plan"]["result_id"])
    task_run_id = str(confirmation["output_plan"]["task_run_id"])
    with tempfile.TemporaryDirectory(prefix="biomedpilot_multifactor_edger_") as workdir:
        work = Path(workdir)
        matrix_path = _write_count_fixture_matrix(work)
        metadata_path = _write_fixture_metadata(work)
        raw_output = work / "edger_output.tsv"
        run_log = _run_edger_rscript(dependency["rscript"]["path"], matrix_path, metadata_path, raw_output)
        if run_log["status"] != "passed":
            return _blocked(*[str(item) for item in run_log.get("blockers", []) or []], parameter_manifest=parameter_manifest, dependency_snapshot=dependency, rscript_log=run_log)
        rows = _read_edger_rows(raw_output, _fixture_group_means(matrix_path))

    bundle = {
        "schema_version": MULTIFACTOR_DEG_FIXTURE_SCHEMA_VERSION,
        "status": "passed",
        "result_semantics": "formal_computed_result",
        "engine_name": "r_edger_multifactor",
        "engine_version": _package_version(dependency, "edgeR"),
        "input_package_id": str(parameter_manifest.get("input_package_id") or ""),
        "deg_ready_package_id": str(parameter_manifest.get("deg_ready_package_id") or ""),
        "parameters_manifest": parameter_manifest,
        "dependency_snapshot": dependency,
        "rows": rows,
        "warnings": [],
        "blockers": [],
    }
    bundle_validation = validate_multifactor_deg_result_bundle(bundle)
    if bundle_validation["status"] != "passed":
        return _blocked(*[str(item) for item in bundle_validation.get("blockers", []) or []], parameter_manifest=parameter_manifest, dependency_snapshot=dependency, result_bundle=bundle)

    output_path = _write_deg_table(root, result_id, rows)
    log_path = _write_run_log(root, result_id, task_run_id, bundle, run_log)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = ResultIndexEntry(
        result_id=result_id,
        task_run_id=task_run_id,
        task_type="deg",
        result_semantics="formal_computed_result",
        input_package_id=str(parameter_manifest.get("input_package_id") or ""),
        source_dataset_id="controlled_multifactor_fixture",
        source_repository_manifest="controlled_fixture://multifactor_deg/edger/v1",
        parameters_manifest=parameter_manifest,
        engine_name="r_edger_multifactor",
        engine_version=_package_version(dependency, "edgeR"),
        dependency_snapshot=dependency,
        output_artifacts=({"artifact_type": "deg_result_table", "path": str(output_path.relative_to(root)), "schema": "biomedpilot.deg_result_table.v1"},),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=tuple(str(item) for item in bundle.get("warnings", []) or []),
        blockers=(),
        log_artifacts=({"artifact_type": "multifactor_deg_run_log", "path": str(log_path.relative_to(root))},),
        failure_reason="",
        created_at=now,
        updated_at=now,
        report_ready_eligible=False,
    ).to_dict()
    entry_validation = validate_multifactor_deg_result_index_entry(entry)
    if entry_validation["status"] != "passed":
        return _blocked(*[str(item) for item in entry_validation.get("blockers", []) or []], parameter_manifest=parameter_manifest, dependency_snapshot=dependency, result_bundle=bundle, result_entry=entry)
    registered = register_result(root, entry)
    return {
        "schema_version": MULTIFACTOR_DEG_RUN_SCHEMA_VERSION,
        "status": "passed",
        "method": "edgeR",
        "result_id": result_id,
        "task_run_id": task_run_id,
        "result_entry": registered,
        "result_table_path": str(output_path),
        "task_run_log_path": str(log_path),
        "parameter_manifest": parameter_manifest,
        "dependency_snapshot": dependency,
        "warnings": list(registered.get("warnings", []) or []),
        "blockers": [],
    }


def _run_limma_rscript(rscript: str, matrix_path: Path, metadata_path: Path, output_path: Path) -> dict[str, Any]:
    script = """
suppressPackageStartupMessages(library(limma))
args <- commandArgs(trailingOnly=TRUE)
matrix_path <- args[[1]]
metadata_path <- args[[2]]
output_path <- args[[3]]
expr <- read.table(matrix_path, header=TRUE, row.names=1, sep="\\t", check.names=FALSE)
meta <- read.table(metadata_path, header=TRUE, sep="\\t", stringsAsFactors=TRUE)
meta <- meta[match(colnames(expr), meta$sample_id), ]
meta$group <- relevel(factor(meta$group), ref="control")
meta$batch <- factor(meta$batch)
design <- model.matrix(~ batch + group, data=meta)
fit <- lmFit(as.matrix(expr), design)
fit <- eBayes(fit)
result <- topTable(fit, coef="groupcase", number=Inf, sort.by="none")
result$feature_id <- rownames(result)
write.table(result, file=output_path, sep="\\t", quote=FALSE, row.names=FALSE)
"""
    proc = subprocess.run([rscript, "--vanilla", "-e", script, str(matrix_path), str(metadata_path), str(output_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=60)
    blockers = [] if proc.returncode == 0 and output_path.is_file() else [f"limma_rscript_failed:{proc.returncode}"]
    return {"status": "blocked" if blockers else "passed", "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "blockers": blockers}


def _run_deseq2_rscript(rscript: str, matrix_path: Path, metadata_path: Path, output_path: Path) -> dict[str, Any]:
    script = """
suppressPackageStartupMessages(library(DESeq2))
args <- commandArgs(trailingOnly=TRUE)
matrix_path <- args[[1]]
metadata_path <- args[[2]]
output_path <- args[[3]]
counts <- read.table(matrix_path, header=TRUE, row.names=1, sep="\\t", check.names=FALSE)
meta <- read.table(metadata_path, header=TRUE, sep="\\t", stringsAsFactors=TRUE)
meta <- meta[match(colnames(counts), meta$sample_id), ]
meta$group <- relevel(factor(meta$group), ref="control")
meta$batch <- factor(meta$batch)
dds <- DESeqDataSetFromMatrix(countData=round(as.matrix(counts)), colData=meta, design=~ batch + group)
dds <- estimateSizeFactors(dds)
dds <- estimateDispersionsGeneEst(dds)
dispersions(dds) <- mcols(dds)$dispGeneEst
dds <- nbinomWaldTest(dds)
result <- as.data.frame(results(dds, name="group_case_vs_control"))
result$feature_id <- rownames(result)
write.table(result, file=output_path, sep="\\t", quote=FALSE, row.names=FALSE)
"""
    proc = subprocess.run([rscript, "--vanilla", "-e", script, str(matrix_path), str(metadata_path), str(output_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=120)
    blockers = [] if proc.returncode == 0 and output_path.is_file() else [f"deseq2_rscript_failed:{proc.returncode}"]
    return {"status": "blocked" if blockers else "passed", "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "blockers": blockers}


def _run_edger_rscript(rscript: str, matrix_path: Path, metadata_path: Path, output_path: Path) -> dict[str, Any]:
    script = """
suppressPackageStartupMessages(library(edgeR))
args <- commandArgs(trailingOnly=TRUE)
matrix_path <- args[[1]]
metadata_path <- args[[2]]
output_path <- args[[3]]
counts <- read.table(matrix_path, header=TRUE, row.names=1, sep="\\t", check.names=FALSE)
meta <- read.table(metadata_path, header=TRUE, sep="\\t", stringsAsFactors=TRUE)
meta <- meta[match(colnames(counts), meta$sample_id), ]
meta$group <- relevel(factor(meta$group), ref="control")
meta$batch <- factor(meta$batch)
design <- model.matrix(~ batch + group, data=meta)
y <- DGEList(counts=round(as.matrix(counts)))
y <- calcNormFactors(y)
y <- estimateDisp(y, design)
fit <- glmQLFit(y, design)
test <- glmQLFTest(fit, coef="groupcase")
result <- topTags(test, n=Inf, sort.by="none")$table
result$feature_id <- rownames(result)
write.table(result, file=output_path, sep="\\t", quote=FALSE, row.names=FALSE)
"""
    proc = subprocess.run([rscript, "--vanilla", "-e", script, str(matrix_path), str(metadata_path), str(output_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=120)
    blockers = [] if proc.returncode == 0 and output_path.is_file() else [f"edger_rscript_failed:{proc.returncode}"]
    return {"status": "blocked" if blockers else "passed", "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "blockers": blockers}


def _detect_r_package(rscript: str, package: str) -> dict[str, Any]:
    script = f"suppressPackageStartupMessages(library({package})); cat(as.character(packageVersion('{package}')))"
    proc = subprocess.run([rscript, "--vanilla", "-e", script], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)
    available = proc.returncode == 0
    return {"available": available, "installed": available, "importable": available, "version": proc.stdout.strip() if available else "", "missing_reason": "" if available else proc.stderr.strip()}


def _run_version_command(command: list[str]) -> str:
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=10)
    return (proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr).strip() else ""


def _fixture_deg_ready_package(value_type: str) -> dict[str, Any]:
    return {"source_input_package_id": "controlled-multifactor-fixture-input", "deg_ready_package_id": "controlled-multifactor-fixture-ready", "value_type": value_type}


def _fixture_design_manifest() -> dict[str, Any]:
    return {
        "design_formula": "~ batch + group",
        "contrast": {"contrast_id": "group_case_vs_control", "case_group": "case", "control_group": "control", "coefficient": "groupcase"},
        "covariates": [],
        "batch_variables": ["batch"],
        "batch_assignments": {"batch": {"CTRL_1": "B1", "CTRL_2": "B2", "CTRL_3": "B1", "CASE_1": "B2", "CASE_2": "B1", "CASE_3": "B2"}},
        "design_rank": 3,
        "residual_degrees_of_freedom": 3,
        "contrast_estimability": "estimable",
    }


def _write_fixture_matrix(root: Path) -> Path:
    path = root / "matrix.tsv"
    rows = [
        ["feature_id", "CTRL_1", "CTRL_2", "CTRL_3", "CASE_1", "CASE_2", "CASE_3"],
        ["GENE_A", "5.0", "5.2", "5.1", "8.2", "8.1", "8.3"],
        ["GENE_B", "7.1", "7.0", "7.2", "4.3", "4.2", "4.1"],
        ["GENE_C", "6.0", "6.1", "5.9", "6.1", "6.0", "6.2"],
        ["GENE_D", "4.2", "4.1", "4.3", "4.4", "4.2", "4.3"],
    ]
    _write_rows(path, rows)
    return path


def _write_count_fixture_matrix(root: Path) -> Path:
    path = root / "count_matrix.tsv"
    rows = [
        ["feature_id", "CTRL_1", "CTRL_2", "CTRL_3", "CASE_1", "CASE_2", "CASE_3"],
        ["GENE_A", "82", "88", "85", "420", "445", "430"],
        ["GENE_B", "460", "440", "455", "92", "88", "95"],
        ["GENE_C", "260", "255", "270", "275", "265", "280"],
        ["GENE_D", "120", "125", "118", "130", "127", "126"],
        ["GENE_E", "40", "45", "44", "42", "48", "43"],
        ["GENE_F", "690", "705", "710", "680", "700", "695"],
        ["GENE_G", "18", "22", "20", "125", "118", "130"],
        ["GENE_H", "150", "155", "148", "145", "152", "151"],
    ]
    _write_rows(path, rows)
    return path


def _write_fixture_metadata(root: Path) -> Path:
    path = root / "metadata.tsv"
    rows = [
        ["sample_id", "group", "batch"],
        ["CTRL_1", "control", "B1"],
        ["CTRL_2", "control", "B2"],
        ["CTRL_3", "control", "B1"],
        ["CASE_1", "case", "B2"],
        ["CASE_2", "case", "B1"],
        ["CASE_3", "case", "B2"],
    ]
    _write_rows(path, rows)
    return path


def _write_rows(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerows(rows)


def _fixture_group_means(matrix_path: Path) -> dict[str, dict[str, float]]:
    control_samples = {"CTRL_1", "CTRL_2", "CTRL_3"}
    case_samples = {"CASE_1", "CASE_2", "CASE_3"}
    means: dict[str, dict[str, float]] = {}
    with matrix_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        samples = reader.fieldnames or []
        for row in reader:
            feature_id = str(row.get("feature_id") or "")
            control_values = [_safe_float(row.get(sample)) for sample in samples if sample in control_samples]
            case_values = [_safe_float(row.get(sample)) for sample in samples if sample in case_samples]
            means[feature_id] = {
                "control": sum(control_values) / len(control_values) if control_values else 0.0,
                "case": sum(case_values) / len(case_values) if case_values else 0.0,
            }
    return means


def _read_limma_rows(path: Path, group_means: dict[str, dict[str, float]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for raw in reader:
            logfc = float(raw.get("logFC") or 0.0)
            p_value = float(raw.get("P.Value") or 1.0)
            fdr = float(raw.get("adj.P.Val") or 1.0)
            rows.append(
                {
                    "feature_id": str(raw.get("feature_id") or ""),
                    "gene_symbol": str(raw.get("feature_id") or ""),
                    "base_mean_or_mean_expression": str(raw.get("AveExpr") or ""),
                    "case_mean": f"{group_means.get(str(raw.get('feature_id') or ''), {}).get('case', 0.0):.8g}",
                    "control_mean": f"{group_means.get(str(raw.get('feature_id') or ''), {}).get('control', 0.0):.8g}",
                    "log2_fold_change": f"{logfc:.8g}",
                    "statistic": str(raw.get("t") or ""),
                    "p_value": f"{p_value:.8g}",
                    "adjusted_p_value": f"{fdr:.8g}",
                    "significance_label": _significance(logfc, fdr),
                    "warnings": "",
                }
            )
    return rows


def _read_deseq2_rows(path: Path, group_means: dict[str, dict[str, float]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for raw in reader:
            logfc = _safe_float(raw.get("log2FoldChange"))
            p_value = _safe_float(raw.get("pvalue"), default=1.0)
            fdr = _safe_float(raw.get("padj"), default=1.0)
            rows.append(
                {
                    "feature_id": str(raw.get("feature_id") or ""),
                    "gene_symbol": str(raw.get("feature_id") or ""),
                    "base_mean_or_mean_expression": str(raw.get("baseMean") or ""),
                    "case_mean": f"{group_means.get(str(raw.get('feature_id') or ''), {}).get('case', 0.0):.8g}",
                    "control_mean": f"{group_means.get(str(raw.get('feature_id') or ''), {}).get('control', 0.0):.8g}",
                    "log2_fold_change": f"{logfc:.8g}",
                    "statistic": str(raw.get("stat") or ""),
                    "p_value": f"{p_value:.8g}",
                    "adjusted_p_value": f"{fdr:.8g}",
                    "significance_label": _significance(logfc, fdr),
                    "warnings": "" if str(raw.get("padj") or "").upper() != "NA" else "adjusted_p_value_na_replaced_for_schema",
                }
            )
    return rows


def _read_edger_rows(path: Path, group_means: dict[str, dict[str, float]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for raw in reader:
            logfc = _safe_float(raw.get("logFC"))
            p_value = _safe_float(raw.get("PValue"), default=1.0)
            fdr = _safe_float(raw.get("FDR"), default=1.0)
            rows.append(
                {
                    "feature_id": str(raw.get("feature_id") or ""),
                    "gene_symbol": str(raw.get("feature_id") or ""),
                    "base_mean_or_mean_expression": str(raw.get("logCPM") or ""),
                    "case_mean": f"{group_means.get(str(raw.get('feature_id') or ''), {}).get('case', 0.0):.8g}",
                    "control_mean": f"{group_means.get(str(raw.get('feature_id') or ''), {}).get('control', 0.0):.8g}",
                    "log2_fold_change": f"{logfc:.8g}",
                    "statistic": str(raw.get("F") or ""),
                    "p_value": f"{p_value:.8g}",
                    "adjusted_p_value": f"{fdr:.8g}",
                    "significance_label": _significance(logfc, fdr),
                    "warnings": "",
                }
            )
    return rows


def _write_deg_table(root: Path, result_id: str, rows: list[dict[str, str]]) -> Path:
    path = root / "results" / "tables" / f"{result_id}.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(REQUIRED_DEG_RESULT_COLUMNS), delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def _write_run_log(root: Path, result_id: str, task_run_id: str, bundle: dict[str, Any], rscript_log: dict[str, Any]) -> Path:
    path = root / "analysis" / "formal_deg" / f"{result_id}_run_log.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "biomedpilot.multifactor_deg_run_log.v1",
        "result_id": result_id,
        "task_run_id": task_run_id,
        "method": (bundle.get("parameters_manifest", {}) if isinstance(bundle.get("parameters_manifest"), dict) else {}).get("backend_method", ""),
        "bundle_status": bundle.get("status"),
        "row_count": len(bundle.get("rows", []) or []),
        "parameter_manifest": bundle.get("parameters_manifest", {}),
        "dependency_snapshot": bundle.get("dependency_snapshot", {}),
        "rscript": {"returncode": rscript_log.get("returncode"), "stdout": rscript_log.get("stdout", ""), "stderr": rscript_log.get("stderr", "")},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _significance(logfc: float, fdr: float) -> str:
    if fdr <= 0.05 and logfc >= 1.0:
        return "up"
    if fdr <= 0.05 and logfc <= -1.0:
        return "down"
    return "not_significant"


def _safe_float(value: object, *, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text.upper() == "NA" or not text:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _package_version(dependency: dict[str, Any], package: str) -> str:
    packages = dependency.get("r_backend", {}).get("packages", {}) if isinstance(dependency.get("r_backend"), dict) else {}
    status = packages.get(package, {}) if isinstance(packages, dict) else {}
    return str(status.get("version") or "unknown") if isinstance(status, dict) else "unknown"


def _blocked(*blockers: str, **payload: Any) -> dict[str, Any]:
    return {
        "schema_version": MULTIFACTOR_DEG_RUN_SCHEMA_VERSION,
        "status": "blocked",
        "result_semantics": "blocked",
        "warnings": [],
        "blockers": list(dict.fromkeys(blocker for blocker in blockers if blocker)),
        **payload,
    }
