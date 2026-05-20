from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.bioinformatics.analysis_inputs import resolve_analysis_inputs
from app.bioinformatics.deg_ready.builder import build_deg_ready_package
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result

from . import python_backend
from .dependency_check import check_deg_backend_dependencies
from .models import DEG_ENGINE_NAME, DEG_ENGINE_VERSION, REQUIRED_DEG_RESULT_COLUMNS
from .parameter_gate import build_deg_parameter_manifest
from .result_schema import build_formal_deg_result_schema_gate, validate_deg_result_bundle, validate_formal_deg_result_index_entry


FORMAL_DEG_RUN_SCHEMA_VERSION = "biomedpilot.formal_deg_controlled_run.v1"


def run_formal_controlled_deg(
    project_root: str | Path,
    *,
    method: str = "welch_t_test",
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    resolver = resolve_analysis_inputs(root).to_dict()
    package = next((item for item in resolver.get("packages", []) or [] if isinstance(item, dict) and item.get("package_type") == "deg_recompute"), None)
    if package is None:
        return _blocked("missing_deg_recompute_input_package")
    if package.get("blockers"):
        return _blocked(*[str(item) for item in package.get("blockers", []) or []])

    deg_ready = build_deg_ready_package(package).to_dict()
    if deg_ready.get("blockers"):
        return _blocked(*[str(item) for item in deg_ready.get("blockers", []) or []], deg_ready_package=deg_ready)

    dependency = dependency_snapshot or check_deg_backend_dependencies()
    parameter_manifest = build_deg_parameter_manifest(deg_ready, method=method, dependency_snapshot=dependency)
    if parameter_manifest.get("blockers"):
        return _blocked(*[str(item) for item in parameter_manifest.get("blockers", []) or []], deg_ready_package=deg_ready, parameter_manifest=parameter_manifest, dependency_snapshot=dependency)

    schema_gate = build_formal_deg_result_schema_gate(parameter_manifest=parameter_manifest, dependency_snapshot=dependency)
    if schema_gate.get("status") != "passed":
        return _blocked(*[str(item) for item in schema_gate.get("blockers", []) or []], deg_ready_package=deg_ready, parameter_manifest=parameter_manifest, dependency_snapshot=dependency, result_schema_gate=schema_gate)

    bundle = python_backend.run_controlled_deg(
        deg_ready,
        case_samples=[str(item) for item in parameter_manifest.get("case_samples", []) or []],
        control_samples=[str(item) for item in parameter_manifest.get("control_samples", []) or []],
        method=method,
        dependency_snapshot=dependency,
        log2fc_threshold=float(parameter_manifest.get("log2fc_threshold") or 1.0),
        adjusted_p_threshold=float(parameter_manifest.get("fdr_threshold") or 0.05),
        pseudocount=float(parameter_manifest.get("pseudocount") or 1e-9),
    )
    if bundle.get("status") != "passed":
        return _blocked(*[str(item) for item in bundle.get("blockers", []) or []], deg_ready_package=deg_ready, parameter_manifest=parameter_manifest, dependency_snapshot=dependency, result_bundle=bundle)

    bundle_validation = validate_deg_result_bundle(bundle)
    if bundle_validation.get("status") != "passed":
        return _blocked(*[str(item) for item in bundle_validation.get("blockers", []) or []], deg_ready_package=deg_ready, parameter_manifest=parameter_manifest, dependency_snapshot=dependency, result_bundle=bundle)

    result_id = f"formal-deg-{uuid4().hex[:10]}"
    task_run_id = f"task-run-{uuid4().hex[:10]}"
    output_path = _write_deg_table(root, result_id, bundle.get("rows", []) or [])
    log_path = _write_run_log(root, result_id, bundle, parameter_manifest)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = ResultIndexEntry(
        result_id=result_id,
        task_run_id=task_run_id,
        task_type="deg",
        result_semantics="formal_computed_result",
        input_package_id=str(parameter_manifest.get("input_package_id") or ""),
        source_dataset_id=str(package.get("source_dataset_id") or ""),
        source_repository_manifest=str(package.get("source_repository_manifest") or ""),
        parameters_manifest=parameter_manifest,
        engine_name=DEG_ENGINE_NAME,
        engine_version=DEG_ENGINE_VERSION,
        dependency_snapshot=dependency,
        output_artifacts=({"artifact_type": "deg_result_table", "path": str(output_path.relative_to(root)), "schema": "biomedpilot.deg_result_table.v1"},),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=tuple(str(item) for item in bundle.get("warnings", []) or []),
        blockers=(),
        log_artifacts=({"artifact_type": "formal_deg_run_log", "path": str(log_path.relative_to(root))},),
        failure_reason="",
        created_at=now,
        updated_at=now,
        report_ready_eligible=False,
    ).to_dict()
    entry_validation = validate_formal_deg_result_index_entry(entry)
    if entry_validation.get("status") != "passed":
        return _blocked(*[str(item) for item in entry_validation.get("blockers", []) or []], deg_ready_package=deg_ready, parameter_manifest=parameter_manifest, dependency_snapshot=dependency, result_bundle=bundle, result_entry=entry)

    registered = register_result(root, entry)
    return {
        "schema_version": FORMAL_DEG_RUN_SCHEMA_VERSION,
        "status": "passed",
        "result_id": result_id,
        "task_run_id": task_run_id,
        "result_entry": registered,
        "result_table_path": str(output_path),
        "parameter_manifest": parameter_manifest,
        "dependency_snapshot": dependency,
        "warnings": list(registered.get("warnings", []) or []),
        "blockers": [],
    }


def _write_deg_table(root: Path, result_id: str, rows: list[object]) -> Path:
    path = root / "results" / "tables" / f"{result_id}.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(REQUIRED_DEG_RESULT_COLUMNS), delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            if isinstance(row, dict):
                writer.writerow({column: row.get(column, "") for column in REQUIRED_DEG_RESULT_COLUMNS})
    return path


def _write_run_log(root: Path, result_id: str, bundle: dict[str, Any], parameter_manifest: dict[str, Any]) -> Path:
    import json

    path = root / "analysis" / "formal_deg" / f"{result_id}_run_log.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "biomedpilot.formal_deg_run_log.v1",
        "result_id": result_id,
        "bundle_status": bundle.get("status"),
        "row_count": len(bundle.get("rows", []) or []),
        "parameter_manifest": parameter_manifest,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _blocked(*blockers: str, **payload: Any) -> dict[str, Any]:
    return {
        "schema_version": FORMAL_DEG_RUN_SCHEMA_VERSION,
        "status": "blocked",
        "result_semantics": "blocked",
        "warnings": [],
        "blockers": list(dict.fromkeys(blocker for blocker in blockers if blocker)),
        **payload,
    }
