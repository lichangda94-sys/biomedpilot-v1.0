from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.bioinformatics.results.registry import load_registry

from .registry import build_result_index_task_type_module_map, get_analysis_module
from .standard_package import validate_standard_result_package


def build_standard_analysis_package_catalog(project_root: str | Path) -> dict[str, Any]:
    """Build a read-only catalog of standard analysis result packages.

    The catalog is intentionally derived from the current result index and the
    standard package contract. It does not scan arbitrary folders, execute
    workers, or infer formal readiness from module-specific payloads.
    """

    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    rows: list[dict[str, Any]] = []
    for entry in [item for item in registry.get("results", []) if isinstance(item, dict)]:
        for artifact in _standard_package_artifacts(entry):
            package_dir = _resolve_artifact_path(root, artifact.get("path"))
            expected_module_id = _module_id_from_entry(entry)
            payload_schemas = _payload_schemas_for_module(expected_module_id)
            result_index_module_blockers = _result_index_module_resolution_blockers(entry, expected_module_id)
            if not _is_relative_to(package_dir, root):
                rows.append(
                    _blocked_catalog_row(
                        root=root,
                        entry=entry,
                        package_dir=package_dir,
                        expected_module_id=expected_module_id,
                        payload_schemas=payload_schemas,
                        blockers=[
                            "standard_result_package_path_outside_project_root",
                            *result_index_module_blockers,
                        ],
                    )
                )
                continue
            validation = validate_standard_result_package(
                package_dir,
                expected_module_id=expected_module_id,
                expected_task_id=str(entry.get("task_run_id") or ""),
                expected_mode=str((entry.get("dependency_snapshot") or {}).get("mode") or ""),
            )
            result_payload = _read_json(package_dir / "result.json")
            provenance_payload = _read_json(package_dir / "provenance.json")
            invocation_payload = _read_json(package_dir / "logs" / "worker_invocation.json")
            result_index_log_blockers = _result_index_worker_invocation_blockers(entry, root, package_dir)
            task_system_blockers = _catalog_task_system_boundary_blockers(invocation_payload, provenance_payload)
            detail = build_standard_analysis_package_detail(
                package_dir,
                project_root=root,
                validation=validation,
                result_payload=result_payload,
                provenance_payload=provenance_payload,
                invocation_payload=invocation_payload,
            )
            provenance_boundary = provenance_payload.get("worker_boundary") if isinstance(provenance_payload.get("worker_boundary"), dict) else {}
            invocation_boundary = invocation_payload.get("worker_boundary") if isinstance(invocation_payload.get("worker_boundary"), dict) else {}
            worker_boundary = invocation_boundary or provenance_boundary
            package_manifest = detail["package_manifest"]
            input_manifest = detail["input_manifest"]
            rows.append(
                {
                    "schema_version": "biomedpilot.analysis.standard_package_catalog_row.v1",
                    "result_id": str(entry.get("result_id") or ""),
                    "task_run_id": str(entry.get("task_run_id") or ""),
                    "task_type": str(entry.get("task_type") or ""),
                    "result_semantics": str(entry.get("result_semantics") or ""),
                    "package_path": str(package_dir),
                    "package_path_relative": _relative_or_absolute(root, package_dir),
                    "module_id": str(result_payload.get("module_id") or _module_id_from_entry(entry)),
                    "mode": str(result_payload.get("mode") or (entry.get("dependency_snapshot") or {}).get("mode") or ""),
                    "status": str(result_payload.get("status") or validation.get("result_status") or ""),
                    "validation_status": str(validation.get("status") or "blocked"),
                    "result_package_schema": str(validation.get("result_package_schema") or ""),
                    "package_manifest": package_manifest,
                    "package_manifest_validation_status": str(package_manifest.get("validation_status") or ""),
                    "payload_schemas": payload_schemas,
                    "result_payload_schema": payload_schemas.get("result.json", ""),
                    "provenance_payload_schema": payload_schemas.get("provenance.json", ""),
                    "engine_name": str((provenance_payload.get("engine") or {}).get("name") or entry.get("engine_name") or ""),
                    "engine_version": str((provenance_payload.get("engine") or {}).get("version") or entry.get("engine_version") or ""),
                    "runtime": provenance_payload.get("runtime") if isinstance(provenance_payload.get("runtime"), dict) else {},
                    "analysis_environment": provenance_payload.get("analysis_environment") if isinstance(provenance_payload.get("analysis_environment"), dict) else {},
                    "worker_invocation": invocation_payload,
                    "input_manifest": input_manifest,
                    "input_manifest_path_relative": str(input_manifest.get("path_relative") or ""),
                    "input_manifest_validation_status": str(input_manifest.get("validation_status") or ""),
                    "worker_backend": str(invocation_payload.get("worker_backend") or ""),
                    "worker_invocation_status": str(invocation_payload.get("invocation_status") or ""),
                    "worker_boundary": worker_boundary,
                    "worker_boundary_type": str(worker_boundary.get("boundary_type") or _default_worker_boundary_type(provenance_payload)),
                    "worker_migration_status": str(worker_boundary.get("migration_status") or ""),
                    "command": str(provenance_payload.get("command") or ""),
                    "input_hash": str(provenance_payload.get("input_hash") or ""),
                    "parameter_hash": str(provenance_payload.get("parameter_hash") or ""),
                    "random_seed": "" if provenance_payload.get("random_seed") is None else str(provenance_payload.get("random_seed")),
                    "artifact_counts": {
                        "tables": len(result_payload.get("tables") or []),
                        "plots": len(result_payload.get("plots") or []),
                        "reports": len(result_payload.get("reports") or []),
                        "logs": len(detail["artifact_manifest"]["logs"]),
                    },
                    "artifact_manifest": detail["artifact_manifest"],
                    "blockers": list(
                        dict.fromkeys(
                            [
                                *validation.get("blockers", []),
                                *result_payload.get("blockers", []),
                                *result_index_log_blockers,
                                *result_index_module_blockers,
                                *task_system_blockers,
                            ]
                        )
                    ),
                    "warnings": list(dict.fromkeys([*validation.get("warnings", []), *result_payload.get("warnings", [])])),
                }
            )
    blockers = [f"standard_analysis_package_invalid:{row['result_id']}:{item}" for row in rows for item in row["blockers"]]
    return {
        "schema_version": "biomedpilot.analysis.standard_package_catalog.v1",
        "status": "blocked" if blockers else "passed",
        "project_root": str(root),
        "source_policy": "result_index_standard_result_package_artifacts_only",
        "package_count": len(rows),
        "rows": rows,
        "blockers": blockers,
        "warnings": [item for row in rows for item in row["warnings"]],
    }


def _blocked_catalog_row(
    *,
    root: Path,
    entry: dict[str, Any],
    package_dir: Path,
    expected_module_id: str,
    payload_schemas: dict[str, str],
    blockers: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.analysis.standard_package_catalog_row.v1",
        "result_id": str(entry.get("result_id") or ""),
        "task_run_id": str(entry.get("task_run_id") or ""),
        "task_type": str(entry.get("task_type") or ""),
        "result_semantics": str(entry.get("result_semantics") or ""),
        "package_path": str(package_dir),
        "package_path_relative": _relative_or_absolute(root, package_dir),
        "module_id": expected_module_id,
        "mode": str((entry.get("dependency_snapshot") or {}).get("mode") or ""),
        "status": "blocked",
        "validation_status": "blocked",
        "result_package_schema": "analysis/schemas/output/result_package.schema.json",
        "package_manifest": {
            "schema_version": "biomedpilot.analysis.standard_package_manifest_detail.v1",
            "source_policy": "result_index_declared_standard_package_not_read",
            "validation_status": "blocked",
            "blockers": blockers,
        },
        "package_manifest_validation_status": "blocked",
        "payload_schemas": payload_schemas,
        "result_payload_schema": payload_schemas.get("result.json", ""),
        "provenance_payload_schema": payload_schemas.get("provenance.json", ""),
        "engine_name": str(entry.get("engine_name") or ""),
        "engine_version": str(entry.get("engine_version") or ""),
        "runtime": {},
        "analysis_environment": {},
        "worker_invocation": {},
        "input_manifest": {
            "schema_version": "biomedpilot.analysis.standard_package_input_manifest.v1",
            "validation_status": "blocked",
            "source_policy": "standard_result_package_not_read",
            "blockers": blockers,
        },
        "input_manifest_path_relative": "",
        "input_manifest_validation_status": "blocked",
        "worker_backend": "",
        "worker_invocation_status": "",
        "worker_boundary": {},
        "worker_boundary_type": "",
        "worker_migration_status": "",
        "command": "",
        "input_hash": "",
        "parameter_hash": "",
        "random_seed": "",
        "artifact_counts": {"tables": 0, "plots": 0, "reports": 0, "logs": 0},
        "artifact_manifest": {
            "schema_version": "biomedpilot.analysis.standard_package_artifact_manifest.v1",
            "source_policy": "standard_result_package_not_read",
            "tables": [],
            "plots": [],
            "reports": [],
            "logs": [],
        },
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": [],
    }


def build_standard_analysis_package_detail(
    package_dir: str | Path,
    *,
    project_root: str | Path | None = None,
    validation: dict[str, Any] | None = None,
    result_payload: dict[str, Any] | None = None,
    provenance_payload: dict[str, Any] | None = None,
    invocation_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read a standard package as a UI-safe artifact manifest.

    The detail view is constrained to the standard result package directory. It
    does not inspect module-private output folders or infer artifacts from R
    package-specific naming conventions.
    """

    package = Path(package_dir).expanduser().resolve()
    root = Path(project_root).expanduser().resolve() if project_root else package
    result = result_payload if result_payload is not None else _read_json(package / "result.json")
    provenance = provenance_payload if provenance_payload is not None else _read_json(package / "provenance.json")
    invocation = invocation_payload if invocation_payload is not None else _read_json(package / "logs" / "worker_invocation.json")
    package_validation = validation or validate_standard_result_package(package)
    payload_schemas = _payload_schemas_for_module(str(result.get("module_id") or ""))
    artifact_manifest = {
        "schema_version": "biomedpilot.analysis.standard_package_artifact_manifest.v1",
        "source_policy": "standard_result_package_declared_artifacts_and_logs_only",
        "tables": _declared_artifacts(package, root, result, "tables"),
        "plots": _declared_artifacts(package, root, result, "plots"),
        "reports": _declared_artifacts(package, root, result, "reports"),
        "logs": _log_artifacts(package, root),
    }
    package_manifest = _package_manifest_detail(package_validation)
    input_manifest = _input_manifest_detail(package, root, invocation, package_validation)
    return {
        "schema_version": "biomedpilot.analysis.standard_package_detail.v1",
        "package_path": str(package),
        "package_path_relative": _relative_or_absolute(root, package),
        "validation_status": str(package_validation.get("status") or "blocked"),
        "result_package_schema": str(package_validation.get("result_package_schema") or ""),
        "package_manifest": package_manifest,
        "payload_schemas": payload_schemas,
        "result_payload_schema": payload_schemas.get("result.json", ""),
        "provenance_payload_schema": payload_schemas.get("provenance.json", ""),
        "result": {
            "schema_version": str(result.get("schema_version") or ""),
            "module_id": str(result.get("module_id") or ""),
            "mode": str(result.get("mode") or ""),
            "task_id": str(result.get("task_id") or ""),
            "status": str(result.get("status") or ""),
            "result_semantics": str(result.get("result_semantics") or ""),
            "summary": result.get("summary") if isinstance(result.get("summary"), dict) else {},
            "warnings": _list(result.get("warnings")),
            "blockers": _list(result.get("blockers")),
        },
        "provenance": {
            "schema_version": str(provenance.get("schema_version") or ""),
            "engine": provenance.get("engine") if isinstance(provenance.get("engine"), dict) else {},
            "runtime": provenance.get("runtime") if isinstance(provenance.get("runtime"), dict) else {},
            "analysis_environment": provenance.get("analysis_environment") if isinstance(provenance.get("analysis_environment"), dict) else {},
            "input_hash": str(provenance.get("input_hash") or ""),
            "parameter_hash": str(provenance.get("parameter_hash") or ""),
            "command": str(provenance.get("command") or ""),
        },
        "worker_invocation": invocation,
        "input_manifest": input_manifest,
        "artifact_manifest": artifact_manifest,
        "blockers": list(package_validation.get("blockers", [])),
        "warnings": list(package_validation.get("warnings", [])),
    }


def _standard_package_artifacts(entry: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = entry.get("output_artifacts")
    if not isinstance(artifacts, list | tuple):
        return []
    return [item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "standard_result_package" and item.get("path")]


def _result_index_worker_invocation_blockers(entry: dict[str, Any], root: Path, package_dir: Path) -> list[str]:
    invocation_path = package_dir / "logs" / "worker_invocation.json"
    if not invocation_path.is_file():
        return []
    log_artifacts = entry.get("log_artifacts")
    if not isinstance(log_artifacts, list | tuple):
        return ["result_index_log_artifacts_invalid"]
    invocation_artifacts = [
        item
        for item in log_artifacts
        if isinstance(item, dict) and item.get("artifact_type") == "analysis_worker_invocation_manifest"
    ]
    if not invocation_artifacts:
        return ["result_index_worker_invocation_manifest_missing"]
    blockers: list[str] = []
    for artifact in invocation_artifacts:
        if artifact.get("schema") != "biomedpilot.analysis.worker_invocation.v1":
            blockers.append("result_index_worker_invocation_manifest_schema_invalid")
        declared = _resolve_artifact_path(root, artifact.get("path"))
        if declared != invocation_path.resolve():
            blockers.append("result_index_worker_invocation_manifest_path_mismatch")
        if not declared.is_file():
            blockers.append("result_index_worker_invocation_manifest_file_missing")
    return list(dict.fromkeys(blockers))


def _catalog_task_system_boundary_blockers(invocation: dict[str, Any], provenance: dict[str, Any]) -> list[str]:
    invocation_boundary = invocation.get("worker_boundary") if isinstance(invocation.get("worker_boundary"), dict) else {}
    provenance_boundary = provenance.get("worker_boundary") if isinstance(provenance.get("worker_boundary"), dict) else {}
    boundary = invocation_boundary or provenance_boundary
    if boundary.get("boundary_type") != "standard_r_worker":
        return []
    task_system_invocation = str(boundary.get("task_system_invocation") or "")
    if task_system_invocation == "task_center_registered":
        return []
    return [f"standard_r_worker_package_not_task_center_registered:{task_system_invocation or 'missing'}"]


def _resolve_artifact_path(root: Path, value: object) -> Path:
    path = Path(str(value or "")).expanduser()
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _module_id_from_entry(entry: dict[str, Any]) -> str:
    task_type = str(entry.get("task_type") or "")
    task_type_map = build_result_index_task_type_module_map()
    if task_type.startswith("analysis:"):
        module_id = task_type.split(":", 1)[1].lower()
        return task_type_map.get(module_id, "")
    task_type_normalized = task_type.lower()
    return task_type_map.get(task_type_normalized, "")


def _result_index_module_resolution_blockers(entry: dict[str, Any], module_id: str) -> list[str]:
    if module_id:
        return []
    task_type = str(entry.get("task_type") or "missing")
    return [f"result_index_task_type_not_registered:{task_type}"]


def _payload_schemas_for_module(module_id: str) -> dict[str, str]:
    if not module_id:
        return {}
    try:
        module = get_analysis_module(module_id)
    except ValueError:
        return {}
    return {
        "result.json": str(module.get("result_payload_schema") or ""),
        "provenance.json": str(module.get("provenance_payload_schema") or ""),
    }


def _default_worker_boundary_type(provenance: dict[str, Any]) -> str:
    engine = provenance.get("engine") if isinstance(provenance.get("engine"), dict) else {}
    if engine.get("name") == "biomedpilot_standard_r_worker":
        return "standard_r_worker"
    return ""


def _relative_or_absolute(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _declared_artifacts(package: Path, root: Path, result: dict[str, Any], group: str) -> list[dict[str, Any]]:
    artifacts = result.get(group)
    if not isinstance(artifacts, list | tuple):
        return []
    rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        rows.append(_artifact_row(package, root, artifact, group=group))
    return rows


def _log_artifacts(package: Path, root: Path) -> list[dict[str, Any]]:
    logs_dir = package / "logs"
    if not logs_dir.is_dir():
        return []
    rows = []
    for path in sorted(item for item in logs_dir.iterdir() if item.is_file()):
        rows.append(
            _artifact_row(
                package,
                root,
                {"artifact_type": _log_artifact_type(path.name), "path": f"logs/{path.name}"},
                group="logs",
            )
        )
    return rows


def _package_manifest_detail(validation: dict[str, Any]) -> dict[str, Any]:
    manifest = validation.get("package_manifest")
    manifest_payload = manifest if isinstance(manifest, dict) else {}
    blockers = [
        str(item)
        for item in validation.get("blockers", [])
        if str(item).startswith("result_package_schema_") or str(item).startswith("missing_required_")
    ]
    return {
        "schema_version": "biomedpilot.analysis.standard_package_manifest_detail.v1",
        "source_policy": "synthesized_from_standard_package_filesystem_and_result_json",
        "schema": str(validation.get("result_package_schema") or ""),
        "validation_status": "blocked" if blockers else str(validation.get("status") or "blocked"),
        "package_schema_version": str(manifest_payload.get("schema_version") or ""),
        "module_id": str(manifest_payload.get("module_id") or ""),
        "mode": str(manifest_payload.get("mode") or ""),
        "task_id": str(manifest_payload.get("task_id") or ""),
        "status": str(manifest_payload.get("status") or ""),
        "result_json": str(manifest_payload.get("result_json") or ""),
        "provenance_json": str(manifest_payload.get("provenance_json") or ""),
        "directories": [str(item) for item in manifest_payload.get("directories", [])] if isinstance(manifest_payload.get("directories"), list | tuple) else [],
        "blockers": blockers,
    }


def _input_manifest_detail(package: Path, root: Path, invocation: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    declared_path = str(invocation.get("input_manifest") or "")
    path = (package / declared_path).resolve() if declared_path else package / ""
    inside_package = bool(declared_path) and _is_relative_to(path, package)
    payload = _read_json(path) if inside_package else {}
    blocker_prefixes = (
        "worker_invocation_input_manifest_",
        "module_input_manifest_",
    )
    blockers = [
        str(item)
        for item in validation.get("blockers", [])
        if any(str(item).startswith(prefix) for prefix in blocker_prefixes)
    ]
    if not declared_path:
        validation_status = "blocked"
    elif blockers:
        validation_status = "blocked"
    elif declared_path == "module_input.json" and path.is_file():
        validation_status = "passed"
    elif declared_path == "service_adapter_payload":
        validation_status = "external_service_adapter_reference"
    else:
        validation_status = "external_or_unvalidated_reference"
    return {
        "schema_version": "biomedpilot.analysis.standard_package_input_manifest.v1",
        "declared_path": declared_path,
        "path": str(path) if declared_path else "",
        "path_relative": _relative_or_absolute(root, path) if declared_path and inside_package else declared_path,
        "package_relative_path": _relative_or_absolute(package, path) if declared_path and inside_package else declared_path,
        "exists": path.is_file() if declared_path and inside_package else False,
        "within_standard_package": inside_package,
        "schema": "analysis/schemas/input/module_input.schema.json" if declared_path == "module_input.json" else "",
        "validation_status": validation_status,
        "source_policy": "package_local_module_input_manifest" if declared_path == "module_input.json" else "worker_invocation_declared_reference",
        "module_id": str(payload.get("module_id") or ""),
        "mode": str(payload.get("mode") or ""),
        "task_id": str(payload.get("task_id") or ""),
        "project_id": str(payload.get("project_id") or ""),
        "input_keys": sorted(str(key) for key in payload.get("inputs", {}).keys()) if isinstance(payload.get("inputs"), dict) else [],
        "parameter_keys": sorted(str(key) for key in payload.get("parameters", {}).keys()) if isinstance(payload.get("parameters"), dict) else [],
        "blockers": blockers,
    }


def _artifact_row(package: Path, root: Path, artifact: dict[str, Any], *, group: str) -> dict[str, Any]:
    declared_path = str(artifact.get("path") or "")
    path = (package / declared_path).resolve()
    inside_package = _is_relative_to(path, package)
    return {
        "artifact_type": str(artifact.get("artifact_type") or artifact.get("type") or ""),
        "group": group,
        "declared_path": declared_path,
        "path": str(path),
        "path_relative": _relative_or_absolute(root, path),
        "package_relative_path": _relative_or_absolute(package, path) if inside_package else declared_path,
        "exists": path.is_file() if inside_package else False,
        "size_bytes": path.stat().st_size if inside_package and path.is_file() else 0,
        "within_standard_package": inside_package,
        "source_policy": "standard_result_package_only",
    }


def _log_artifact_type(filename: str) -> str:
    if filename == "worker_invocation.json":
        return "analysis_worker_invocation_manifest"
    if filename == "worker.log":
        return "analysis_worker_log"
    return "analysis_log"


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list | tuple) else []


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
