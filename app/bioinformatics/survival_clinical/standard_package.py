from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.analysis_runtime.standard_package import write_legacy_service_adapter_invocation_manifest


def write_survival_standard_result_package(
    root: Path,
    *,
    result_id: str,
    task_run_id: str,
    analysis_type: str,
    table_artifacts: tuple[dict[str, Any], ...],
    log_path: Path,
    parameter_manifest: dict[str, Any],
    dependency_snapshot: dict[str, Any],
    engine_name: str,
    engine_version: str,
    source_owner: str,
) -> Path:
    package_dir = root / "analysis" / "standard_packages" / result_id
    for dirname in ("tables", "plots", "reports", "logs"):
        (package_dir / dirname).mkdir(parents=True, exist_ok=True)

    package_tables: list[dict[str, str]] = []
    for artifact in table_artifacts:
        source = _artifact_source_path(root, artifact)
        table_name = source.name
        (package_dir / "tables" / table_name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        package_tables.append({"artifact_type": str(artifact.get("artifact_type") or "survival_result_table"), "path": f"tables/{table_name}"})

    (package_dir / "logs" / log_path.name).write_text(log_path.read_text(encoding="utf-8"), encoding="utf-8")
    (package_dir / "reports" / "README_limitations.md").write_text(
        "\n".join(
            [
                "# Controlled survival/clinical standard package",
                "",
                "This standard result package mirrors a controlled survival/clinical result for package-contract validation.",
                "It does not create plot artifacts, report-ready output, clinical interpretation, diagnosis, prognosis, risk grouping, or treatment recommendations.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result_payload = {
        "schema_version": "biomedpilot.analysis.result.v1",
        "module_id": "survival",
        "mode": "full",
        "task_id": task_run_id,
        "status": "passed",
        "result_semantics": "formal_computed_result",
        "summary": {
            "message": f"Controlled {analysis_type} result mirrored into a standard result package.",
            "clinical_conclusion_status": "not_generated",
            "analysis_type": analysis_type,
            "source_result_id": result_id,
            "worker_boundary_status": "sidecar_only_not_isolated_standard_worker",
        },
        "tables": package_tables,
        "plots": [],
        "reports": [{"artifact_type": "standard_package_limitations_report", "path": "reports/README_limitations.md"}],
        "blockers": [],
        "warnings": [
            "standard_package_sidecar_for_existing_controlled_survival_adapter",
            "report_ready_not_enabled_by_standard_package",
            "clinical_conclusion_not_generated",
        ],
        "created_at": now,
    }
    provenance_payload = {
        "schema_version": "biomedpilot.analysis.provenance.v1",
        "module_id": "survival",
        "mode": "full",
        "task_id": task_run_id,
        "created_at": now,
        "input_path": "parameter_manifest_embedded_in_result_index",
        "input_hash": _sha256_json(parameter_manifest.get("provenance", {}) if isinstance(parameter_manifest.get("provenance"), dict) else parameter_manifest),
        "parameter_hash": _sha256_json(parameter_manifest),
        "random_seed": None,
        "engine": {"name": engine_name, "version": engine_version},
        "runtime": {
            "r_version": "not_used_python_controlled_executor",
            "bioconductor_version": "not_used_python_controlled_executor",
            "package_versions": _package_versions(dependency_snapshot),
            "external_tool_versions": {},
        },
        "command": f"{source_owner}.{analysis_type}",
        "worker_boundary": {
            "boundary_type": "legacy_service_adapter_sidecar",
            "standard_worker_entrypoint": "not_used",
            "subprocess_owner": source_owner,
            "migration_status": "sidecar_only_not_isolated_standard_worker",
            "task_system_invocation": "not_yet_migrated",
        },
        "source_result_id": result_id,
        "source_result_table_hashes": {
            str(artifact.get("artifact_type") or ""): _sha256_file(_artifact_source_path(root, artifact))
            for artifact in table_artifacts
        },
    }
    (package_dir / "result.json").write_text(json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_dir / "provenance.json").write_text(json.dumps(provenance_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_legacy_service_adapter_invocation_manifest(
        package_dir,
        module_id="survival",
        mode="full",
        task_id=task_run_id,
        subprocess_owner=source_owner,
        command=f"{source_owner}.{analysis_type}",
        created_at=now,
    )
    return package_dir


def _package_versions(snapshot: dict[str, Any]) -> dict[str, str]:
    lifelines = snapshot.get("python_lifelines") if isinstance(snapshot.get("python_lifelines"), dict) else {}
    version = str(lifelines.get("version") or "")
    return {"python_lifelines": version} if version else {}


def _artifact_source_path(root: Path, artifact: dict[str, Any]) -> Path:
    path = Path(str(artifact.get("path") or "")).expanduser()
    return path if path.is_absolute() else root / path


def _sha256_json(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
