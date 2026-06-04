from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_formal_deg_standard_result_package(
    root: Path,
    *,
    result_id: str,
    task_run_id: str,
    result_table_path: Path,
    log_path: Path,
    parameter_manifest: dict[str, Any],
    dependency_snapshot: dict[str, Any],
    engine_name: str,
    engine_version: str,
) -> Path:
    package_dir = root / "analysis" / "standard_packages" / result_id
    for dirname in ("tables", "plots", "reports", "logs"):
        (package_dir / dirname).mkdir(parents=True, exist_ok=True)

    table_name = result_table_path.name
    (package_dir / "tables" / table_name).write_text(result_table_path.read_text(encoding="utf-8"), encoding="utf-8")
    (package_dir / "logs" / log_path.name).write_text(log_path.read_text(encoding="utf-8"), encoding="utf-8")
    (package_dir / "reports" / "README_limitations.md").write_text(
        "\n".join(
            [
                "# Controlled formal DEG standard package",
                "",
                "This standard result package mirrors the controlled two-group formal DEG result table for package-contract validation.",
                "It does not create plot artifacts, report-ready output, clinical interpretation, diagnosis, prognosis, or treatment recommendations.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result_payload = {
        "schema_version": "biomedpilot.analysis.result.v1",
        "module_id": "deg",
        "mode": "full",
        "task_id": task_run_id,
        "status": "passed",
        "result_semantics": "formal_computed_result",
        "summary": {
            "message": "Controlled two-group formal DEG result mirrored into a standard result package.",
            "clinical_conclusion_status": "not_generated",
            "analysis_type": "controlled_two_group_deg",
            "method": str(parameter_manifest.get("method") or ""),
            "source_result_id": result_id,
            "worker_boundary_status": "sidecar_only_not_isolated_standard_worker",
        },
        "tables": [{"artifact_type": "deg_result_table", "path": f"tables/{table_name}"}],
        "plots": [],
        "reports": [{"artifact_type": "standard_package_limitations_report", "path": "reports/README_limitations.md"}],
        "blockers": [],
        "warnings": [
            "standard_package_sidecar_for_existing_controlled_formal_deg_runner",
            "report_ready_not_enabled_by_standard_package",
            "clinical_conclusion_not_generated",
        ],
        "created_at": now,
    }
    provenance_payload = {
        "schema_version": "biomedpilot.analysis.provenance.v1",
        "module_id": "deg",
        "mode": "full",
        "task_id": task_run_id,
        "created_at": now,
        "input_path": "parameter_manifest_embedded_in_result_index",
        "input_hash": _sha256_json(
            {
                "input_package_id": parameter_manifest.get("input_package_id", ""),
                "deg_ready_package_id": parameter_manifest.get("deg_ready_package_id", ""),
                "case_samples": parameter_manifest.get("case_samples", []),
                "control_samples": parameter_manifest.get("control_samples", []),
            }
        ),
        "parameter_hash": _sha256_json(parameter_manifest),
        "random_seed": None,
        "engine": {"name": engine_name, "version": engine_version},
        "runtime": {
            "r_version": "not_used_python_controlled_executor",
            "bioconductor_version": "not_used_python_controlled_executor",
            "package_versions": _package_versions(dependency_snapshot),
            "external_tool_versions": {},
        },
        "command": "app.bioinformatics.deg_engine.formal_runner.run_formal_controlled_deg",
        "worker_boundary": {
            "boundary_type": "legacy_service_adapter_sidecar",
            "standard_worker_entrypoint": "not_used",
            "subprocess_owner": "app.bioinformatics.deg_engine.formal_runner",
            "migration_status": "sidecar_only_not_isolated_standard_worker",
            "task_system_invocation": "not_yet_migrated",
        },
        "source_result_id": result_id,
        "source_result_table_hash": _sha256_file(result_table_path),
    }
    (package_dir / "result.json").write_text(json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_dir / "provenance.json").write_text(json.dumps(provenance_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return package_dir


def _package_versions(snapshot: dict[str, Any]) -> dict[str, str]:
    packages = snapshot.get("packages") if isinstance(snapshot.get("packages"), dict) else {}
    versions: dict[str, str] = {}
    for name, payload in packages.items():
        if isinstance(payload, dict):
            version = str(payload.get("version") or "")
            if version:
                versions[str(name)] = version
        elif payload:
            versions[str(name)] = str(payload)
    return versions


def _sha256_json(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
