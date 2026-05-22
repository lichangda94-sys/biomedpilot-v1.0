"""Audited limma Rscript execution adapter.

B25.2 can invoke a user/system-provided Rscript, but it still cannot install R
packages, bundle R into the app, or bypass the B25 result handoff gate.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from app.bioinformatics.deg_engine.r_adapter_contract import build_r_deg_runtime_gate
from app.bioinformatics.deg_engine.r_backend_handoff import register_r_limma_external_handoff_result

R_LIMMA_RSCRIPT_ADAPTER_SCHEMA_VERSION = "biomedpilot.r_limma_rscript_adapter.v1"
R_LIMMA_RSCRIPT_ENGINE_NAME = "r_limma_rscript_adapter"
R_LIMMA_RSCRIPT_ENGINE_VERSION = "0.1.0"


def detect_r_limma_runtime_capabilities(
    rscript_path: str = "Rscript",
    *,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    """Detect R/Bioconductor/limma without installing anything."""

    script = (
        "cat('R=', R.version$version.string, '\\n', sep='')\n"
        "cat('platform=', R.version$platform, '\\n', sep='')\n"
        "for (pkg in c('BiocManager','limma')) {\n"
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
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        return _runtime_detection_blocked(
            resolved_rscript_path,
            ["rscript_not_found"],
            str(exc),
            command=command,
        )
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
    if parsed.get("limma") in {None, "", "MISSING"}:
        blockers.append("limma_missing")

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
        "package.r.limma.available": {
            "available": parsed.get("limma") not in {None, "", "MISSING"},
            "version": parsed.get("limma", ""),
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
            "limma": capabilities["package.r.limma.available"],
        },
        "blockers": blockers,
    }
    return {
        "schema_version": "biomedpilot.r_limma_runtime_detection.v1",
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


def resolve_rscript_path(rscript_path: str = "Rscript") -> str:
    if rscript_path and rscript_path != "Rscript":
        return rscript_path
    discovered = shutil.which("Rscript")
    if discovered:
        return discovered
    for candidate in ("/usr/local/bin/Rscript", "/opt/homebrew/bin/Rscript"):
        if Path(candidate).is_file():
            return candidate
    return rscript_path or "Rscript"


def run_r_limma_rscript_execution(
    project_root: str | Path,
    *,
    expression_table_path: str | Path,
    sample_group_map: Mapping[str, str],
    case_group: str,
    control_group: str,
    multi_factor_preflight: Mapping[str, Any],
    parameters_manifest: Mapping[str, Any],
    rscript_path: str = "Rscript",
    external_capabilities: Mapping[str, Any] | None = None,
    dependency_snapshot: Mapping[str, Any] | None = None,
    timeout_seconds: int = 60,
    result_id: str | None = None,
    task_run_id: str | None = None,
    input_package_id: str = "",
    source_dataset_id: str = "",
    source_repository_manifest: str = "",
) -> dict[str, Any]:
    """Run limma through Rscript, then register through the B25 handoff gate."""

    root = Path(project_root).expanduser().resolve()
    expression_path = Path(expression_table_path).expanduser().resolve()
    if not expression_path.is_file():
        return _blocked(["expression_table_missing"], expression_table_path=str(expression_path))
    if not sample_group_map:
        return _blocked(["sample_group_map_missing"], expression_table_path=str(expression_path))
    if not case_group or not control_group or case_group == control_group:
        return _blocked(["invalid_case_control_groups"], expression_table_path=str(expression_path))

    header_gate = _validate_expression_header(expression_path, sample_group_map)
    if header_gate["status"] != "passed":
        return _blocked(header_gate["blockers"], expression_header_gate=header_gate)

    runtime_detection = None
    capabilities = dict(external_capabilities or {})
    dependency = dict(dependency_snapshot or {})
    if not capabilities or not dependency:
        runtime_detection = detect_r_limma_runtime_capabilities(rscript_path, timeout_seconds=min(timeout_seconds, 10))
        if runtime_detection["status"] != "passed":
            return _blocked(
                runtime_detection["blockers"],
                runtime_detection=runtime_detection,
                expression_header_gate=header_gate,
            )
        capabilities = dict(runtime_detection["external_capabilities"])
        dependency = dict(runtime_detection["dependency_snapshot"])

    runtime_gate = build_r_deg_runtime_gate(
        method="limma",
        multi_factor_preflight=dict(multi_factor_preflight),
        external_capabilities=capabilities,
        dependency_snapshot=dependency,
    )
    if runtime_gate["status"] != "ready_for_external_runtime_execution":
        return _blocked(
            list(runtime_gate.get("blockers") or ["r_limma_runtime_gate_not_ready"]),
            runtime_detection=runtime_detection,
            runtime_gate=runtime_gate,
            expression_header_gate=header_gate,
        )

    resolved_result_id = result_id or f"r-limma-run-{uuid.uuid4().hex[:12]}"
    resolved_task_run_id = task_run_id or f"task-r-limma-run-{uuid.uuid4().hex[:12]}"
    run_dir = root / "analysis" / "r_deg" / "limma_rscript" / resolved_task_run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    design_path = run_dir / "design.tsv"
    output_path = run_dir / "limma_output.tsv"
    script_path = run_dir / "run_limma.R"
    command_manifest_path = run_dir / "command_manifest.json"
    command_log_path = run_dir / "command_log.json"
    _write_design_table(design_path, header_gate["sample_columns"], sample_group_map)
    script_path.write_text(_limma_r_script(), encoding="utf-8")

    contrast = f"{_r_make_names(case_group)}-{_r_make_names(control_group)}"
    command = [
        rscript_path,
        str(script_path),
        str(expression_path),
        str(design_path),
        str(output_path),
        contrast,
    ]
    command_manifest = {
        "schema_version": "biomedpilot.r_limma_command_manifest.v1",
        "created_at": _now(),
        "method": "limma",
        "shell": False,
        "command": command,
        "rscript_path": rscript_path,
        "script_path": str(script_path),
        "expression_table_path": str(expression_path),
        "design_table_path": str(design_path),
        "output_path": str(output_path),
        "contrast": contrast,
        "timeout_seconds": timeout_seconds,
        "result_id": resolved_result_id,
        "task_run_id": resolved_task_run_id,
    }
    _write_json(command_manifest_path, command_manifest)

    started_at = _now()
    try:
        completed = subprocess.run(
            command,
            cwd=str(run_dir),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        command_log = {
            "schema_version": "biomedpilot.r_limma_command_log.v1",
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
            "schema_version": "biomedpilot.r_limma_command_log.v1",
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
        return _blocked(
            ["r_limma_rscript_timeout"],
            runtime_detection=runtime_detection,
            runtime_gate=runtime_gate,
            expression_header_gate=header_gate,
            command_manifest_path=str(command_manifest_path),
            command_log_path=str(command_log_path),
        )
    except FileNotFoundError as exc:
        command_log = {
            "schema_version": "biomedpilot.r_limma_command_log.v1",
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
        return _blocked(
            ["rscript_not_found"],
            runtime_detection=runtime_detection,
            runtime_gate=runtime_gate,
            expression_header_gate=header_gate,
            command_manifest_path=str(command_manifest_path),
            command_log_path=str(command_log_path),
        )

    _write_json(command_log_path, command_log)
    if command_log["status"] != "succeeded":
        return _blocked(
            [f"r_limma_rscript_exit_code:{command_log['returncode']}"],
            runtime_detection=runtime_detection,
            runtime_gate=runtime_gate,
            expression_header_gate=header_gate,
            command_manifest_path=str(command_manifest_path),
            command_log_path=str(command_log_path),
        )
    if not output_path.is_file():
        return _blocked(
            ["r_limma_output_missing"],
            runtime_detection=runtime_detection,
            runtime_gate=runtime_gate,
            expression_header_gate=header_gate,
            command_manifest_path=str(command_manifest_path),
            command_log_path=str(command_log_path),
        )

    output_rows = _read_tsv(output_path)
    handoff = register_r_limma_external_handoff_result(
        root,
        multi_factor_preflight=multi_factor_preflight,
        external_capabilities=capabilities,
        dependency_snapshot=dependency,
        execution_status="succeeded",
        output_rows=output_rows,
        parameters_manifest={
            **dict(parameters_manifest),
            "rscript_command_manifest_path": str(command_manifest_path),
            "rscript_command_log_path": str(command_log_path),
        },
        method="limma",
        result_id=resolved_result_id,
        task_run_id=resolved_task_run_id,
        input_package_id=input_package_id,
        source_dataset_id=source_dataset_id,
        source_repository_manifest=source_repository_manifest,
        engine_name=R_LIMMA_RSCRIPT_ENGINE_NAME,
        engine_version=R_LIMMA_RSCRIPT_ENGINE_VERSION,
        additional_log_artifacts=(
            {"artifact_type": "r_limma_rscript_command_manifest", "path": str(command_manifest_path)},
            {"artifact_type": "r_limma_rscript_command_log", "path": str(command_log_path)},
        ),
        execution_provenance={
            "adapter_schema_version": R_LIMMA_RSCRIPT_ADAPTER_SCHEMA_VERSION,
            "rscript_path": rscript_path,
            "command_manifest_path": str(command_manifest_path),
            "command_log_path": str(command_log_path),
            "limma_output_path": str(output_path),
            "runtime_detection": runtime_detection,
        },
    )
    if handoff["status"] != "passed":
        return {
            "schema_version": R_LIMMA_RSCRIPT_ADAPTER_SCHEMA_VERSION,
            "status": "blocked",
            "result_semantics": "",
            "runtime_detection": runtime_detection,
            "runtime_gate": runtime_gate,
            "expression_header_gate": header_gate,
            "command_manifest_path": str(command_manifest_path),
            "command_log_path": str(command_log_path),
            "handoff": handoff,
            "warnings": [],
            "blockers": list(handoff.get("blockers") or ["r_limma_handoff_blocked"]),
        }
    return {
        "schema_version": R_LIMMA_RSCRIPT_ADAPTER_SCHEMA_VERSION,
        "status": "passed",
        "method": "limma",
        "result_semantics": "formal_computed_result",
        "result_id": handoff["result_id"],
        "task_run_id": handoff["task_run_id"],
        "runtime_detection": runtime_detection,
        "runtime_gate": runtime_gate,
        "expression_header_gate": header_gate,
        "command_manifest_path": str(command_manifest_path),
        "command_log_path": str(command_log_path),
        "limma_output_path": str(output_path),
        "handoff": handoff,
        "result_index_entry": handoff["result_index_entry"],
        "report_ready_eligible": False,
        "plot_artifacts": [],
        "report_artifacts": [],
        "warnings": handoff.get("warnings", []),
        "blockers": [],
    }


def _runtime_detection_blocked(
    rscript_path: str,
    blockers: Sequence[str],
    message: str,
    **payload: Any,
) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.r_limma_runtime_detection.v1",
        "status": "blocked",
        "rscript_path": rscript_path,
        "message": message,
        "external_capabilities": {},
        "dependency_snapshot": {"status": "blocked", "blockers": list(blockers)},
        "warnings": [],
        "blockers": list(blockers),
        **payload,
    }


def _blocked(blockers: Sequence[str], **payload: Any) -> dict[str, Any]:
    return {
        "schema_version": R_LIMMA_RSCRIPT_ADAPTER_SCHEMA_VERSION,
        "status": "blocked",
        "result_semantics": "",
        "report_ready_eligible": False,
        "plot_artifacts": [],
        "report_artifacts": [],
        "warnings": [],
        "blockers": list(dict.fromkeys(str(item) for item in blockers if item)),
        **payload,
    }


def _parse_key_values(text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def _validate_expression_header(path: Path, sample_group_map: Mapping[str, str]) -> dict[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader, [])
    blockers: list[str] = []
    if "feature_id" not in header:
        blockers.append("expression_table_missing_feature_id")
    sample_columns = [column for column in header if column not in {"feature_id", "gene_symbol"}]
    missing_groups = [sample for sample in sample_columns if sample not in sample_group_map]
    extra_groups = [sample for sample in sample_group_map if sample not in sample_columns]
    blockers.extend(f"sample_missing_group:{sample}" for sample in missing_groups)
    blockers.extend(f"group_sample_missing_expression:{sample}" for sample in extra_groups)
    return {
        "status": "passed" if not blockers else "blocked",
        "sample_columns": sample_columns,
        "blockers": blockers,
        "warnings": [],
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


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _r_make_names(value: str) -> str:
    cleaned = []
    for index, char in enumerate(str(value)):
        if char.isalnum() or char == "_":
            cleaned.append(char)
        else:
            cleaned.append(".")
        if index == 0 and char.isdigit():
            cleaned.insert(0, "X")
    text = "".join(cleaned).strip(".")
    return text or "group"


def _limma_r_script() -> str:
    return r"""
args <- commandArgs(trailingOnly=TRUE)
if (length(args) < 4) {
  stop("expected expression_table design_table output_table contrast")
}
expression_path <- args[[1]]
design_path <- args[[2]]
output_path <- args[[3]]
contrast_expression <- args[[4]]
if (!requireNamespace("limma", quietly=TRUE)) {
  stop("limma package is not available")
}
expr <- utils::read.delim(expression_path, check.names=FALSE, stringsAsFactors=FALSE)
design_df <- utils::read.delim(design_path, check.names=FALSE, stringsAsFactors=FALSE)
if (!("feature_id" %in% colnames(expr))) {
  stop("expression table missing feature_id")
}
feature_id <- as.character(expr$feature_id)
gene_symbol <- if ("gene_symbol" %in% colnames(expr)) as.character(expr$gene_symbol) else rep("", length(feature_id))
sample_columns <- setdiff(colnames(expr), c("feature_id", "gene_symbol"))
if (length(sample_columns) < 2) {
  stop("limma requires at least two sample columns")
}
if (!all(c("sample", "group") %in% colnames(design_df))) {
  stop("design table must contain sample and group")
}
design_df <- design_df[match(sample_columns, design_df$sample), , drop=FALSE]
if (any(is.na(design_df$sample))) {
  stop("design table does not cover all expression samples")
}
group <- factor(design_df$group)
design <- stats::model.matrix(~0 + group)
colnames(design) <- make.names(levels(group))
mat <- as.matrix(expr[, sample_columns, drop=FALSE])
storage.mode(mat) <- "numeric"
rownames(mat) <- feature_id
fit <- limma::lmFit(mat, design)
contrast <- limma::makeContrasts(contrasts=contrast_expression, levels=design)
fit2 <- limma::eBayes(limma::contrasts.fit(fit, contrast))
table <- limma::topTable(fit2, number=Inf, sort.by="none")
table$feature_id <- rownames(table)
gene_map <- stats::setNames(gene_symbol, feature_id)
table$gene_symbol <- unname(gene_map[table$feature_id])
out <- table[, c("feature_id", "gene_symbol", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val", "B")]
utils::write.table(out, file=output_path, sep="\t", quote=FALSE, row.names=FALSE, na="")
"""
