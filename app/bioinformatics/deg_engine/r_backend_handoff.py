"""Controlled external R DEG backend handoff gates.

B25 intentionally does not invoke R or install Bioconductor packages. It accepts
audited external runtime output only after the R adapter contract, runtime gate,
output schema gate, and result-index gate all pass.
"""

from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from app.bioinformatics.deg_engine.models import REQUIRED_DEG_RESULT_COLUMNS
from app.bioinformatics.deg_engine.r_adapter_contract import (
    build_r_deg_runtime_gate,
    validate_r_deg_output_schema,
    validate_r_deg_result_registration_bundle,
)
from app.bioinformatics.deg_engine.result_schema import (
    validate_deg_result_bundle,
    validate_formal_deg_result_index_entry,
)
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result

R_DEG_EXTERNAL_HANDOFF_SCHEMA_VERSION = "biomedpilot.r_deg_external_handoff.v1"
R_LIMMA_EXTERNAL_ENGINE_NAME = "r_limma_external_handoff"
R_LIMMA_EXTERNAL_ENGINE_VERSION = "0.1.0"
DEFERRED_B25_R_DEG_METHODS = frozenset({"deseq2", "edger"})


def build_r_deg_external_handoff_plan(method: str) -> dict[str, Any]:
    """Return the B25 availability plan for an R DEG method."""

    method_key = _normalise_method(method)
    if method_key == "limma":
        return {
            "schema_version": R_DEG_EXTERNAL_HANDOFF_SCHEMA_VERSION,
            "method": "limma",
            "status": "available_after_runtime_schema_and_result_gates",
            "can_register_formal_result": False,
            "required_gates": [
                "B18 multi-factor design preflight passed",
                "B19 R runtime capability gate passed",
                "limma output schema passed",
                "formal DEG result index v2 gate passed",
            ],
            "warnings": [
                "BioMedPilot does not invoke R in B25; only audited external limma output can be registered."
            ],
            "blockers": [],
        }
    if method_key in DEFERRED_B25_R_DEG_METHODS:
        return {
            "schema_version": R_DEG_EXTERNAL_HANDOFF_SCHEMA_VERSION,
            "method": method_key,
            "status": "planned_not_enabled",
            "can_register_formal_result": False,
            "required_gates": [
                "method-specific R output schema",
                "method-specific parameter contract",
                "method-specific result-index validation",
            ],
            "warnings": [],
            "blockers": [f"b25_deferred_until_after_limma_acceptance:{method_key}"],
        }
    return {
        "schema_version": R_DEG_EXTERNAL_HANDOFF_SCHEMA_VERSION,
        "method": method_key,
        "status": "unsupported",
        "can_register_formal_result": False,
        "warnings": [],
        "blockers": [f"unsupported_r_deg_method:{method_key}"],
    }


def register_r_limma_external_handoff_result(
    project_root: str | Path,
    *,
    multi_factor_preflight: Mapping[str, Any],
    external_capabilities: Mapping[str, Any],
    dependency_snapshot: Mapping[str, Any] | None = None,
    execution_status: str = "succeeded",
    output_rows: Sequence[Mapping[str, Any]] | None = None,
    parameters_manifest: Mapping[str, Any] | None = None,
    method: str = "limma",
    result_id: str | None = None,
    task_run_id: str | None = None,
    input_package_id: str = "",
    source_dataset_id: str = "",
    source_repository_manifest: str = "",
    engine_name: str = R_LIMMA_EXTERNAL_ENGINE_NAME,
    engine_version: str = R_LIMMA_EXTERNAL_ENGINE_VERSION,
    additional_log_artifacts: Sequence[Mapping[str, Any]] | None = None,
    execution_provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Register a formal DEG result from audited external limma output."""

    method_key = _normalise_method(method)
    if method_key != "limma":
        return _blocked(
            method_key,
            [f"b25_limma_only_deferred_method:{method_key}"],
            "B25 only accepts limma handoff results.",
        )

    rows = [dict(row) for row in (output_rows or [])]
    if not rows:
        return _blocked("limma", ["limma_output_rows_missing"], "No limma rows were provided.")

    runtime_gate = build_r_deg_runtime_gate(
        method="limma",
        multi_factor_preflight=multi_factor_preflight,
        external_capabilities=external_capabilities,
        dependency_snapshot=dependency_snapshot,
    )
    if runtime_gate.get("status") != "ready_for_external_runtime_execution":
        return _blocked(
            "limma",
            list(runtime_gate.get("blockers") or ["r_deg_runtime_gate_not_ready"]),
            "R DEG runtime gate did not pass.",
            runtime_gate=runtime_gate,
        )

    if execution_status != "succeeded":
        return _blocked(
            "limma",
            [f"r_deg_execution_not_succeeded:{execution_status}"],
            "External limma execution did not report success.",
            runtime_gate=runtime_gate,
        )

    columns = _row_columns(rows)
    schema_gate = validate_r_deg_output_schema("limma", columns)
    if schema_gate.get("status") != "passed":
        return _blocked(
            "limma",
            list(schema_gate.get("blockers") or ["limma_output_schema_failed"]),
            "limma output schema gate did not pass.",
            runtime_gate=runtime_gate,
            output_schema_gate=schema_gate,
        )

    numeric_blockers = _numeric_blockers(rows, ("logFC", "AveExpr", "t", "P.Value", "adj.P.Val"))
    if numeric_blockers:
        return _blocked(
            "limma",
            numeric_blockers,
            "limma output contained non-numeric statistical fields.",
            runtime_gate=runtime_gate,
            output_schema_gate=schema_gate,
        )

    params = dict(parameters_manifest or {})
    resolved_input_package_id = (
        input_package_id
        or str(params.get("input_package_id") or "")
        or str(multi_factor_preflight.get("input_package_id") or "")
    )
    if not resolved_input_package_id:
        return _blocked(
            "limma",
            ["missing_input_package_id_for_r_limma_handoff"],
            "Formal limma handoff requires an input_package_id.",
            runtime_gate=runtime_gate,
            output_schema_gate=schema_gate,
        )

    created_at = _utc_now()
    resolved_result_id = result_id or f"r-limma-{uuid.uuid4().hex[:12]}"
    resolved_task_run_id = task_run_id or f"task-r-limma-{uuid.uuid4().hex[:12]}"
    effective_dependency_snapshot = dict(runtime_gate.get("dependency_snapshot") or dependency_snapshot or {})
    deg_ready_package_id = str(
        params.get("deg_ready_package_id")
        or multi_factor_preflight.get("deg_ready_package_id")
        or multi_factor_preflight.get("design_id")
        or f"{resolved_input_package_id}:r_limma_design_ready"
    )
    canonical_rows = [_canonical_deg_row(row, params) for row in rows]
    bundle_gate = validate_deg_result_bundle(
        {
            "schema_version": "biomedpilot.deg_result_bundle.v1",
            "result_id": resolved_result_id,
            "result_semantics": "formal_computed_result",
            "engine_name": engine_name,
            "engine_version": engine_version,
            "input_package_id": resolved_input_package_id,
            "deg_ready_package_id": deg_ready_package_id,
            "parameters_manifest": params,
            "dependency_snapshot": effective_dependency_snapshot,
            "rows": canonical_rows,
            "warnings": ["r_limma_external_handoff_no_biomedpilot_r_invocation"],
            "blockers": [],
        }
    )
    if bundle_gate.get("status") != "passed":
        return _blocked(
            "limma",
            list(bundle_gate.get("blockers") or ["deg_result_bundle_validation_failed"]),
            "Canonical DEG result bundle validation failed.",
            runtime_gate=runtime_gate,
            output_schema_gate=schema_gate,
            result_bundle_gate=bundle_gate,
        )

    project_root_path = Path(project_root)
    canonical_table_path = project_root_path / "results" / "tables" / f"{resolved_result_id}.tsv"
    limma_table_path = project_root_path / "results" / "tables" / "r_limma" / f"{resolved_result_id}_limma.tsv"
    log_path = project_root_path / "analysis" / "r_deg" / "limma" / f"{resolved_result_id}_run_log.json"

    effective_parameters = {
        **params,
        "schema_version": params.get("schema_version", "biomedpilot.r_limma_external_parameters.v1"),
        "input_package_id": resolved_input_package_id,
        "deg_ready_package_id": deg_ready_package_id,
        "method": "limma",
        "method_family": "r_linear_model",
        "external_runtime_handoff": True,
        "execution_provenance": dict(execution_provenance or {}),
        "result_id": resolved_result_id,
        "task_run_id": resolved_task_run_id,
    }

    entry = ResultIndexEntry(
        result_id=resolved_result_id,
        task_run_id=resolved_task_run_id,
        task_type="deg",
        result_semantics="formal_computed_result",
        input_package_id=resolved_input_package_id,
        source_dataset_id=source_dataset_id,
        source_repository_manifest=source_repository_manifest,
        parameters_manifest=effective_parameters,
        engine_name=engine_name,
        engine_version=engine_version,
        dependency_snapshot=effective_dependency_snapshot,
        output_artifacts=(
            {
                "artifact_id": f"{resolved_result_id}-canonical-table",
                "artifact_type": "deg_result_table",
                "path": str(canonical_table_path),
                "format": "tsv",
                "validation_status": "passed",
            },
            {
                "artifact_id": f"{resolved_result_id}-limma-table",
                "artifact_type": "limma_result_table",
                "path": str(limma_table_path),
                "format": "tsv",
                "validation_status": "passed",
            },
        ),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=(
            "r_limma_external_handoff_no_biomedpilot_r_invocation",
            "r_limma_external_handoff_no_report_ready_activation",
        ),
        blockers=(),
        log_artifacts=(
            {"artifact_type": "r_limma_external_handoff_log", "path": str(log_path)},
            *tuple(dict(item) for item in (additional_log_artifacts or ())),
        ),
        failure_reason="",
        created_at=created_at,
        updated_at=created_at,
        schema_version="2.0.0",
        report_ready_eligible=False,
        migration_status="native_v2",
    )

    registration_gate = validate_r_deg_result_registration_bundle(
        method="limma",
        execution_status=execution_status,
        output_columns=columns,
        result_entry=entry.to_dict(),
        dependency_snapshot=effective_dependency_snapshot,
    )
    if registration_gate.get("status") != "passed":
        return _blocked(
            "limma",
            list(registration_gate.get("blockers") or ["r_deg_result_registration_gate_failed"]),
            "R DEG result registration gate did not pass.",
            runtime_gate=runtime_gate,
            output_schema_gate=schema_gate,
            result_bundle_gate=bundle_gate,
            registration_gate=registration_gate,
        )

    result_index_gate = validate_formal_deg_result_index_entry(entry.to_dict())
    if result_index_gate.get("status") != "passed":
        return _blocked(
            "limma",
            list(result_index_gate.get("blockers") or ["formal_deg_result_index_gate_failed"]),
            "Formal DEG result-index gate did not pass.",
            runtime_gate=runtime_gate,
            output_schema_gate=schema_gate,
            result_bundle_gate=bundle_gate,
            registration_gate=registration_gate,
            result_index_gate=result_index_gate,
        )

    _write_tsv(canonical_table_path, REQUIRED_DEG_RESULT_COLUMNS, canonical_rows)
    _write_tsv(limma_table_path, _limma_output_columns(rows), rows)
    _write_json(
        log_path,
        {
            "schema_version": R_DEG_EXTERNAL_HANDOFF_SCHEMA_VERSION,
            "result_id": resolved_result_id,
            "task_run_id": resolved_task_run_id,
            "method": "limma",
            "execution_status": execution_status,
            "runtime_gate": runtime_gate,
            "output_schema_gate": schema_gate,
            "result_bundle_gate": bundle_gate,
            "registration_gate": registration_gate,
            "result_index_gate": result_index_gate,
            "execution_provenance": dict(execution_provenance or {}),
            "created_at": created_at,
            "warnings": list(entry.warnings),
            "blockers": [],
        },
    )
    registered_entry = register_result(project_root_path, entry)

    return {
        "schema_version": R_DEG_EXTERNAL_HANDOFF_SCHEMA_VERSION,
        "method": "limma",
        "status": "passed",
        "result_id": resolved_result_id,
        "task_run_id": resolved_task_run_id,
        "result_semantics": "formal_computed_result",
        "report_ready_eligible": False,
        "plot_artifacts": [],
        "report_artifacts": [],
        "canonical_table_path": str(canonical_table_path),
        "limma_table_path": str(limma_table_path),
        "log_path": str(log_path),
        "result_index_entry": registered_entry,
        "runtime_gate": runtime_gate,
        "output_schema_gate": schema_gate,
        "result_bundle_gate": bundle_gate,
        "registration_gate": registration_gate,
        "result_index_gate": result_index_gate,
        "warnings": list(entry.warnings),
        "blockers": [],
    }


def _blocked(method: str, blockers: Sequence[str], message: str, **gates: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": R_DEG_EXTERNAL_HANDOFF_SCHEMA_VERSION,
        "method": method,
        "status": "blocked",
        "message": message,
        "result_semantics": "",
        "report_ready_eligible": False,
        "plot_artifacts": [],
        "report_artifacts": [],
        "warnings": [],
        "blockers": list(blockers),
    }
    payload.update(gates)
    return payload


def _normalise_method(method: str) -> str:
    method_key = (method or "").strip().lower().replace("-", "_")
    if method_key in {"edger", "edge_r"}:
        return "edger"
    return method_key


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_columns(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for column in row.keys():
            if column not in seen:
                seen.add(column)
                columns.append(column)
    return columns


def _limma_output_columns(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    preferred = ["feature_id", "gene_symbol", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val", "B"]
    row_columns = _row_columns(rows)
    return [column for column in preferred if column in row_columns] + [
        column for column in row_columns if column not in preferred
    ]


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


def _canonical_deg_row(row: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
    log2fc = float(row["logFC"])
    adjusted_p_value = float(row["adj.P.Val"])
    log2fc_threshold = float(params.get("log2fc_threshold", 1.0))
    fdr_threshold = float(params.get("fdr_threshold", 0.05))
    if abs(log2fc) >= log2fc_threshold and adjusted_p_value <= fdr_threshold:
        significance_label = "upregulated" if log2fc > 0 else "downregulated"
    else:
        significance_label = "not_significant"

    return {
        "feature_id": str(row["feature_id"]),
        "gene_symbol": str(row.get("gene_symbol") or ""),
        "base_mean_or_mean_expression": float(row["AveExpr"]),
        "case_mean": None,
        "control_mean": None,
        "log2_fold_change": log2fc,
        "statistic": float(row["t"]),
        "p_value": float(row["P.Value"]),
        "adjusted_p_value": adjusted_p_value,
        "significance_label": significance_label,
        "warnings": "r_limma_external_handoff_no_group_means",
    }


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
