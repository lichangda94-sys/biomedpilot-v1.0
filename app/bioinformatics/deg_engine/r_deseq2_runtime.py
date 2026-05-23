"""Controlled DESeq2 Rscript execution adapter.

B25.9 can run a fixture-scale, audited DESeq2 adapter from a caller that already
holds the B25 gates. The Analysis UI still does not expose a user-facing DESeq2
run button in this stage.
"""

from __future__ import annotations

import csv
import json
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from app.bioinformatics.deg_engine.models import REQUIRED_DEG_RESULT_COLUMNS
from app.bioinformatics.deg_engine.r_adapter_contract import build_r_deg_runtime_gate, validate_r_deg_output_schema, validate_r_deg_result_registration_bundle
from app.bioinformatics.deg_engine.result_schema import validate_deg_result_bundle, validate_formal_deg_result_index_entry
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result

from .r_deseq2_planning import validate_r_deseq2_count_fixture
from .rscript_adapter import resolve_rscript_path


R_DESEQ2_RSCRIPT_ADAPTER_SCHEMA_VERSION = "biomedpilot.r_deseq2_rscript_adapter.v1"
R_DESEQ2_RSCRIPT_ENGINE_NAME = "r_deseq2_rscript_adapter"
R_DESEQ2_RSCRIPT_ENGINE_VERSION = "0.1.0"


def detect_r_deseq2_runtime_capabilities(
    rscript_path: str = "Rscript",
    *,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    script = (
        "cat('R=', R.version$version.string, '\\n', sep='')\n"
        "cat('platform=', R.version$platform, '\\n', sep='')\n"
        "for (pkg in c('BiocManager','DESeq2')) {\n"
        "  if (requireNamespace(pkg, quietly=TRUE)) {\n"
        "    cat(pkg, '=', as.character(utils::packageVersion(pkg)), '\\n', sep='')\n"
        "  } else {\n"
        "    cat(pkg, '=MISSING\\n', sep='')\n"
        "  }\n"
        "}\n"
    )
    resolved_rscript_path = resolve_rscript_path(rscript_path)
    command = [resolved_rscript_path, "-e", script]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except FileNotFoundError as exc:
        return _runtime_detection_blocked(resolved_rscript_path, ["rscript_not_found"], str(exc), command=command)
    except subprocess.TimeoutExpired as exc:
        return _runtime_detection_blocked(
            resolved_rscript_path,
            ["rscript_detection_timeout"],
            str(exc),
            command=command,
            stdout=_text(exc.stdout),
            stderr=_text(exc.stderr),
        )

    parsed = _parse_key_values(completed.stdout)
    blockers: list[str] = []
    if completed.returncode != 0:
        blockers.append(f"rscript_detection_exit_code:{completed.returncode}")
    if not parsed.get("R"):
        blockers.append("r_version_missing")
    if parsed.get("BiocManager") in {None, "", "MISSING"}:
        blockers.append("biocmanager_missing")
    if parsed.get("DESeq2") in {None, "", "MISSING"}:
        blockers.append("deseq2_missing")
    available = not blockers
    capabilities = {
        "runtime.r.available": {
            "available": completed.returncode == 0 and bool(parsed.get("R")),
            "path": resolved_rscript_path,
            "version": parsed.get("R", ""),
            "platform": parsed.get("platform", ""),
        },
        "runtime.bioconductor.available": {
            "available": parsed.get("BiocManager") not in {None, "", "MISSING"},
            "version": parsed.get("BiocManager", ""),
        },
        "package.r.deseq2.available": {
            "available": parsed.get("DESeq2") not in {None, "", "MISSING"},
            "version": parsed.get("DESeq2", ""),
        },
    }
    dependency_snapshot = {
        "status": "passed" if available else "blocked",
        "runtime": "system_rscript",
        "rscript_path": resolved_rscript_path,
        "platform": parsed.get("platform", ""),
        "dependencies": {
            "R": capabilities["runtime.r.available"],
            "BiocManager": capabilities["runtime.bioconductor.available"],
            "DESeq2": capabilities["package.r.deseq2.available"],
        },
        "blockers": blockers,
    }
    return {
        "schema_version": "biomedpilot.r_deseq2_runtime_detection.v1",
        "status": "passed" if available else "blocked",
        "rscript_path": resolved_rscript_path,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "external_capabilities": capabilities,
        "dependency_snapshot": dependency_snapshot,
        "warnings": [],
        "blockers": blockers,
    }


def run_r_deseq2_rscript_execution(
    project_root: str | Path,
    *,
    count_table_path: str | Path,
    sample_group_map: Mapping[str, str],
    case_group: str,
    control_group: str,
    multi_factor_preflight: Mapping[str, Any],
    parameters_manifest: Mapping[str, Any],
    rscript_path: str = "Rscript",
    external_capabilities: Mapping[str, Any] | None = None,
    dependency_snapshot: Mapping[str, Any] | None = None,
    timeout_seconds: int = 120,
    result_id: str | None = None,
    task_run_id: str | None = None,
    input_package_id: str = "",
    source_dataset_id: str = "",
    source_repository_manifest: str = "",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    count_path = Path(count_table_path).expanduser().resolve()
    if not count_path.is_file():
        return _blocked(["r_deseq2_count_table_missing"], count_table_path=str(count_path))
    if not sample_group_map:
        return _blocked(["r_deseq2_sample_group_map_missing"], count_table_path=str(count_path))
    if not case_group or not control_group or case_group == control_group:
        return _blocked(["r_deseq2_invalid_case_control_groups"], count_table_path=str(count_path))

    header_gate = _validate_count_table(count_path, sample_group_map)
    if header_gate["status"] != "passed":
        return _blocked(header_gate["blockers"], count_table_gate=header_gate)

    runtime_detection = None
    capabilities = dict(external_capabilities or {})
    dependency = dict(dependency_snapshot or {})
    if not capabilities or not dependency:
        runtime_detection = detect_r_deseq2_runtime_capabilities(rscript_path, timeout_seconds=min(timeout_seconds, 20))
        if runtime_detection["status"] != "passed":
            return _blocked(runtime_detection["blockers"], runtime_detection=runtime_detection, count_table_gate=header_gate)
        capabilities = dict(runtime_detection["external_capabilities"])
        dependency = dict(runtime_detection["dependency_snapshot"])

    runtime_gate = build_r_deg_runtime_gate(
        method="deseq2",
        multi_factor_preflight=dict(multi_factor_preflight),
        external_capabilities=capabilities,
        dependency_snapshot=dependency,
    )
    if runtime_gate["status"] != "ready_for_external_runtime_execution":
        return _blocked(list(runtime_gate.get("blockers") or ["r_deseq2_runtime_gate_not_ready"]), runtime_gate=runtime_gate, count_table_gate=header_gate)

    resolved_result_id = result_id or f"r-deseq2-run-{uuid.uuid4().hex[:12]}"
    resolved_task_run_id = task_run_id or f"task-r-deseq2-run-{uuid.uuid4().hex[:12]}"
    run_dir = root / "analysis" / "r_deg" / "deseq2_rscript" / resolved_task_run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    design_path = run_dir / "design.tsv"
    output_path = run_dir / "deseq2_output.tsv"
    script_path = run_dir / "run_deseq2.R"
    command_manifest_path = run_dir / "command_manifest.json"
    command_log_path = run_dir / "command_log.json"
    _write_design_table(design_path, header_gate["sample_columns"], sample_group_map)
    script_path.write_text(_deseq2_r_script(), encoding="utf-8")

    command = [
        rscript_path,
        str(script_path),
        str(count_path),
        str(design_path),
        str(output_path),
        case_group,
        control_group,
        str(parameters_manifest.get("dispersion_fit_type") or "mean"),
    ]
    command_manifest = {
        "schema_version": "biomedpilot.r_deseq2_command_manifest.v1",
        "created_at": _now(),
        "method": "deseq2",
        "shell": False,
        "command": command,
        "rscript_path": rscript_path,
        "script_path": str(script_path),
        "count_table_path": str(count_path),
        "design_table_path": str(design_path),
        "output_path": str(output_path),
        "case_group": case_group,
        "control_group": control_group,
        "dispersion_fit_type": str(parameters_manifest.get("dispersion_fit_type") or "mean"),
        "dispersion_fallback_policy": "if_DESeq_dispersion_fit_fails_use_gene_wise_dispersion_then_nbinomWaldTest",
        "timeout_seconds": timeout_seconds,
        "result_id": resolved_result_id,
        "task_run_id": resolved_task_run_id,
    }
    _write_json(command_manifest_path, command_manifest)

    started_at = _now()
    try:
        completed = subprocess.run(command, cwd=str(run_dir), capture_output=True, text=True, timeout=timeout_seconds, check=False)
        command_log = {
            "schema_version": "biomedpilot.r_deseq2_command_log.v1",
            "status": "succeeded" if completed.returncode == 0 else "failed",
            "started_at": started_at,
            "finished_at": _now(),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "command_manifest_path": str(command_manifest_path),
            "output_path": str(output_path),
        }
    except subprocess.TimeoutExpired as exc:
        command_log = {
            "schema_version": "biomedpilot.r_deseq2_command_log.v1",
            "status": "timeout",
            "started_at": started_at,
            "finished_at": _now(),
            "returncode": None,
            "stdout": _text(exc.stdout),
            "stderr": _text(exc.stderr),
            "command_manifest_path": str(command_manifest_path),
            "output_path": str(output_path),
            "failure_reason": str(exc),
        }
        _write_json(command_log_path, command_log)
        return _blocked(["r_deseq2_rscript_timeout"], runtime_gate=runtime_gate, count_table_gate=header_gate, command_log_path=str(command_log_path))
    except FileNotFoundError as exc:
        command_log = {
            "schema_version": "biomedpilot.r_deseq2_command_log.v1",
            "status": "failed",
            "started_at": started_at,
            "finished_at": _now(),
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "command_manifest_path": str(command_manifest_path),
            "output_path": str(output_path),
            "failure_reason": "rscript_not_found",
        }
        _write_json(command_log_path, command_log)
        return _blocked(["rscript_not_found"], runtime_gate=runtime_gate, count_table_gate=header_gate, command_log_path=str(command_log_path))

    _write_json(command_log_path, command_log)
    if command_log["status"] != "succeeded":
        return _blocked([f"r_deseq2_rscript_exit_code:{command_log['returncode']}"], runtime_gate=runtime_gate, count_table_gate=header_gate, command_log_path=str(command_log_path))
    if not output_path.is_file():
        return _blocked(["r_deseq2_output_missing"], runtime_gate=runtime_gate, count_table_gate=header_gate, command_log_path=str(command_log_path))

    output_rows = _read_tsv(output_path)
    return _register_deseq2_result(
        root,
        output_rows=output_rows,
        parameters_manifest={**dict(parameters_manifest), "rscript_command_manifest_path": str(command_manifest_path), "rscript_command_log_path": str(command_log_path)},
        dependency_snapshot=dependency,
        runtime_gate=runtime_gate,
        result_id=resolved_result_id,
        task_run_id=resolved_task_run_id,
        input_package_id=input_package_id,
        source_dataset_id=source_dataset_id,
        source_repository_manifest=source_repository_manifest,
        command_manifest_path=command_manifest_path,
        command_log_path=command_log_path,
        output_path=output_path,
    )


def _register_deseq2_result(
    project_root: Path,
    *,
    output_rows: Sequence[Mapping[str, Any]],
    parameters_manifest: Mapping[str, Any],
    dependency_snapshot: Mapping[str, Any],
    runtime_gate: Mapping[str, Any],
    result_id: str,
    task_run_id: str,
    input_package_id: str,
    source_dataset_id: str,
    source_repository_manifest: str,
    command_manifest_path: Path,
    command_log_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    output_schema_gate = validate_r_deg_output_schema("deseq2", _row_columns(output_rows))
    if output_schema_gate["status"] != "passed":
        return _blocked(list(output_schema_gate.get("blockers") or ["r_deseq2_output_schema_failed"]), output_schema_gate=output_schema_gate)
    numeric_blockers = _numeric_blockers(output_rows, ("baseMean", "log2FoldChange", "lfcSE", "stat", "pvalue", "padj"))
    if numeric_blockers:
        return _blocked(numeric_blockers, output_schema_gate=output_schema_gate)

    canonical_rows = [_canonical_deg_row(row, parameters_manifest) for row in output_rows]
    result_table_path = project_root / "results" / "tables" / f"{result_id}.tsv"
    deseq2_table_path = project_root / "results" / "tables" / "r_deseq2" / f"{result_id}_deseq2.tsv"
    log_path = project_root / "analysis" / "r_deg" / "deseq2" / f"{result_id}_run_log.json"
    created_at = _now()
    entry = ResultIndexEntry(
        result_id=result_id,
        task_run_id=task_run_id,
        task_type="deg",
        result_semantics="formal_computed_result",
        input_package_id=input_package_id,
        source_dataset_id=source_dataset_id,
        source_repository_manifest=source_repository_manifest,
        parameters_manifest={**dict(parameters_manifest), "method": "deseq2", "method_family": "deseq2_count_model"},
        engine_name=R_DESEQ2_RSCRIPT_ENGINE_NAME,
        engine_version=R_DESEQ2_RSCRIPT_ENGINE_VERSION,
        dependency_snapshot=dict(dependency_snapshot),
        output_artifacts=(
            {"artifact_id": f"{result_id}-canonical-table", "artifact_type": "deg_result_table", "path": str(result_table_path), "format": "tsv", "validation_status": "passed"},
            {"artifact_id": f"{result_id}-deseq2-table", "artifact_type": "deseq2_result_table", "path": str(deseq2_table_path), "format": "tsv", "validation_status": "passed"},
        ),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=("r_deseq2_rscript_no_report_ready_activation",),
        blockers=(),
        log_artifacts=(
            {"artifact_type": "r_deseq2_rscript_command_manifest", "path": str(command_manifest_path)},
            {"artifact_type": "r_deseq2_rscript_command_log", "path": str(command_log_path)},
            {"artifact_type": "r_deseq2_rscript_run_log", "path": str(log_path)},
        ),
        failure_reason="",
        created_at=created_at,
        updated_at=created_at,
        schema_version="2.0.0",
        report_ready_eligible=False,
        migration_status="native_v2",
    )
    result_bundle_gate = validate_deg_result_bundle(
        {
            "result_semantics": "formal_computed_result",
            "engine_name": R_DESEQ2_RSCRIPT_ENGINE_NAME,
            "engine_version": R_DESEQ2_RSCRIPT_ENGINE_VERSION,
            "input_package_id": input_package_id,
            "deg_ready_package_id": parameters_manifest.get("deg_ready_package_id", ""),
            "parameters_manifest": dict(parameters_manifest),
            "dependency_snapshot": dict(dependency_snapshot),
            "rows": canonical_rows,
            "blockers": [],
        }
    )
    if result_bundle_gate["status"] != "passed":
        return _blocked(list(result_bundle_gate.get("blockers") or ["r_deseq2_result_bundle_failed"]), output_schema_gate=output_schema_gate, result_bundle_gate=result_bundle_gate)
    registration_gate = validate_r_deg_result_registration_bundle(
        method="deseq2",
        execution_status="succeeded",
        output_columns=_row_columns(output_rows),
        result_entry=entry.to_dict(),
        dependency_snapshot=dict(dependency_snapshot),
    )
    if registration_gate["status"] != "passed":
        return _blocked(list(registration_gate.get("blockers") or ["r_deseq2_registration_gate_failed"]), output_schema_gate=output_schema_gate, result_bundle_gate=result_bundle_gate, registration_gate=registration_gate)
    result_index_gate = validate_formal_deg_result_index_entry(entry.to_dict())
    if result_index_gate["status"] != "passed":
        return _blocked(list(result_index_gate.get("blockers") or ["r_deseq2_result_index_gate_failed"]), output_schema_gate=output_schema_gate, result_bundle_gate=result_bundle_gate, registration_gate=registration_gate, result_index_gate=result_index_gate)

    _write_tsv(result_table_path, REQUIRED_DEG_RESULT_COLUMNS, canonical_rows)
    _write_tsv(deseq2_table_path, _deseq2_output_columns(output_rows), output_rows)
    _write_json(
        log_path,
        {
            "schema_version": R_DESEQ2_RSCRIPT_ADAPTER_SCHEMA_VERSION,
            "result_id": result_id,
            "task_run_id": task_run_id,
            "method": "deseq2",
            "runtime_gate": dict(runtime_gate),
            "output_schema_gate": output_schema_gate,
            "result_bundle_gate": result_bundle_gate,
            "registration_gate": registration_gate,
            "result_index_gate": result_index_gate,
            "created_at": created_at,
            "warnings": list(entry.warnings),
            "blockers": [],
        },
    )
    registered_entry = register_result(project_root, entry)
    return {
        "schema_version": R_DESEQ2_RSCRIPT_ADAPTER_SCHEMA_VERSION,
        "method": "deseq2",
        "status": "passed",
        "result_semantics": "formal_computed_result",
        "result_id": result_id,
        "task_run_id": task_run_id,
        "report_ready_eligible": False,
        "plot_artifacts": [],
        "report_artifacts": [],
        "canonical_table_path": str(result_table_path),
        "deseq2_table_path": str(deseq2_table_path),
        "log_path": str(log_path),
        "result_index_entry": registered_entry,
        "runtime_gate": dict(runtime_gate),
        "output_schema_gate": output_schema_gate,
        "result_bundle_gate": result_bundle_gate,
        "registration_gate": registration_gate,
        "result_index_gate": result_index_gate,
        "warnings": list(entry.warnings),
        "blockers": [],
    }


def _validate_count_table(path: Path, sample_group_map: Mapping[str, str]) -> dict[str, Any]:
    rows = _read_tsv(path)
    sample_columns = list(rows[0].keys()) if rows else []
    sample_columns = [column for column in sample_columns if column not in {"feature_id", "gene_symbol"}]
    fixture_gate = validate_r_deseq2_count_fixture({"sample_ids": sample_columns, "rows": rows})
    missing_groups = [sample for sample in sample_columns if sample not in sample_group_map]
    extra_groups = [sample for sample in sample_group_map if sample not in sample_columns]
    blockers = [*fixture_gate["blockers"]]
    blockers.extend(f"sample_missing_group:{sample}" for sample in missing_groups)
    blockers.extend(f"group_sample_missing_count_table:{sample}" for sample in extra_groups)
    return {"status": "passed" if not blockers else "blocked", "sample_columns": sample_columns, "blockers": list(dict.fromkeys(blockers)), "warnings": []}


def _blocked(blockers: Sequence[str], **payload: Any) -> dict[str, Any]:
    return {
        "schema_version": R_DESEQ2_RSCRIPT_ADAPTER_SCHEMA_VERSION,
        "status": "blocked",
        "result_semantics": "",
        "report_ready_eligible": False,
        "plot_artifacts": [],
        "report_artifacts": [],
        "warnings": [],
        "blockers": list(dict.fromkeys(str(item) for item in blockers if item)),
        **payload,
    }


def _runtime_detection_blocked(rscript_path: str, blockers: Sequence[str], message: str, **payload: Any) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.r_deseq2_runtime_detection.v1",
        "status": "blocked",
        "rscript_path": rscript_path,
        "message": message,
        "external_capabilities": {},
        "dependency_snapshot": {"status": "blocked", "blockers": list(blockers)},
        "warnings": [],
        "blockers": list(blockers),
        **payload,
    }


def _write_design_table(path: Path, sample_columns: Sequence[str], sample_group_map: Mapping[str, str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample", "group"], delimiter="\t")
        writer.writeheader()
        for sample in sample_columns:
            writer.writerow({"sample": sample, "group": sample_group_map[sample]})


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter="\t")]


def _write_tsv(path: Path, fieldnames: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_key_values(text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def _row_columns(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for column in row:
            if column not in seen:
                seen.add(column)
                columns.append(column)
    return columns


def _numeric_blockers(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> list[str]:
    blockers: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        if not str(row.get("feature_id", "")).strip():
            blockers.append(f"row_{row_index}:missing_feature_id")
        for column in columns:
            try:
                float(row[column])
            except (TypeError, ValueError, KeyError):
                blockers.append(f"row_{row_index}:non_numeric:{column}")
    return blockers


def _deseq2_output_columns(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    preferred = ["feature_id", "gene_symbol", "baseMean", "log2FoldChange", "lfcSE", "stat", "pvalue", "padj"]
    row_columns = _row_columns(rows)
    return [column for column in preferred if column in row_columns] + [column for column in row_columns if column not in preferred]


def _canonical_deg_row(row: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
    log2fc = float(row["log2FoldChange"])
    adjusted_p_value = float(row["padj"])
    log2fc_threshold = float(params.get("log2fc_threshold", 1.0))
    fdr_threshold = float(params.get("fdr_threshold", 0.05))
    if abs(log2fc) >= log2fc_threshold and adjusted_p_value <= fdr_threshold:
        significance_label = "upregulated" if log2fc > 0 else "downregulated"
    else:
        significance_label = "not_significant"
    return {
        "feature_id": str(row["feature_id"]),
        "gene_symbol": str(row.get("gene_symbol") or ""),
        "base_mean_or_mean_expression": float(row["baseMean"]),
        "case_mean": None,
        "control_mean": None,
        "log2_fold_change": log2fc,
        "statistic": float(row["stat"]),
        "p_value": float(row["pvalue"]),
        "adjusted_p_value": adjusted_p_value,
        "significance_label": significance_label,
        "warnings": "r_deseq2_rscript_no_group_means",
    }


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _deseq2_r_script() -> str:
    return r"""
args <- commandArgs(trailingOnly=TRUE)
if (length(args) < 6) {
  stop("expected count_table design_table output_table case_group control_group dispersion_fit_type")
}
count_path <- args[[1]]
design_path <- args[[2]]
output_path <- args[[3]]
case_group <- args[[4]]
control_group <- args[[5]]
dispersion_fit_type <- args[[6]]
if (!requireNamespace("DESeq2", quietly=TRUE)) {
  stop("DESeq2 package is not available")
}
suppressPackageStartupMessages(library(DESeq2))
counts <- utils::read.delim(count_path, check.names=FALSE, stringsAsFactors=FALSE)
design_df <- utils::read.delim(design_path, check.names=FALSE, stringsAsFactors=FALSE)
if (!("feature_id" %in% colnames(counts))) {
  colnames(counts)[[1]] <- "feature_id"
}
feature_id <- as.character(counts$feature_id)
gene_symbol <- if ("gene_symbol" %in% colnames(counts)) as.character(counts$gene_symbol) else feature_id
sample_columns <- setdiff(colnames(counts), c("feature_id", "gene_symbol"))
if (length(sample_columns) < 4) {
  stop("DESeq2 controlled fixture requires at least four sample columns")
}
if (!all(c("sample", "group") %in% colnames(design_df))) {
  stop("design table must contain sample and group")
}
design_df <- design_df[match(sample_columns, design_df$sample), , drop=FALSE]
if (any(is.na(design_df$sample))) {
  stop("design table does not cover all count samples")
}
mat <- as.matrix(counts[, sample_columns, drop=FALSE])
storage.mode(mat) <- "numeric"
if (any(is.na(mat)) || any(mat < 0) || any(mat != round(mat))) {
  stop("DESeq2 input must be non-negative integer counts")
}
storage.mode(mat) <- "integer"
rownames(mat) <- feature_id
level_order <- unique(c(control_group, case_group, as.character(design_df$group)))
coldata <- data.frame(row.names=sample_columns, group=factor(design_df$group, levels=level_order))
dds <- DESeq2::DESeqDataSetFromMatrix(countData=mat, colData=coldata, design=~group)
dds <- tryCatch(
  DESeq2::DESeq(dds, fitType=dispersion_fit_type, quiet=TRUE),
  error=function(e) {
    message("DESeq2 dispersion fit failed; using gene-wise dispersion fallback for controlled fixture: ", conditionMessage(e))
    dds2 <- DESeq2::estimateSizeFactors(dds)
    dds2 <- DESeq2::estimateDispersionsGeneEst(dds2)
    dispersions(dds2) <- mcols(dds2)$dispGeneEst
    DESeq2::nbinomWaldTest(dds2)
  }
)
res <- DESeq2::results(dds, contrast=c("group", case_group, control_group), independentFiltering=TRUE)
out <- data.frame(
  feature_id=rownames(res),
  gene_symbol=gene_symbol[match(rownames(res), feature_id)],
  baseMean=res$baseMean,
  log2FoldChange=res$log2FoldChange,
  lfcSE=res$lfcSE,
  stat=res$stat,
  pvalue=res$pvalue,
  padj=res$padj,
  check.names=FALSE
)
utils::write.table(out, file=output_path, sep="\t", quote=FALSE, row.names=FALSE, na="")
"""
