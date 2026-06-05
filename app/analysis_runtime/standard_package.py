from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULT_PACKAGE_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "result_package.schema.json"
MODULE_INPUT_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "input" / "module_input.schema.json"
RESULT_PAYLOAD_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "result.schema.json"
PROVENANCE_PAYLOAD_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "provenance.schema.json"
REQUIRED_FILES = ("result.json", "provenance.json")
REQUIRED_DIRECTORIES = ("tables", "plots", "reports", "logs")
TASK_BRIDGE_ENGINES = {"biomedpilot_analysis_task_bridge", "biomedpilot_standard_r_worker"}
WORKER_INVOCATION_STATUSES = {
    "fixture_copy_completed",
    "fixture_copy_blocked",
    "blocked_validation_gate",
    "not_invoked_mode_gate",
    "blocked_before_process",
    "completed",
    "sidecar_recorded",
}
WORKER_BACKENDS = {"python_fixture", "rscript", "legacy_service_adapter"}
TASK_SYSTEM_INVOCATIONS = {"task_center_registered", "standard_worker_direct_cli", "legacy_service_adapter_direct_call"}


def write_legacy_service_adapter_invocation_manifest(
    package_dir: str | Path,
    *,
    module_id: str,
    mode: str,
    task_id: str,
    subprocess_owner: str,
    command: str | list[Any],
    created_at: str,
    returncode: int | None = 0,
    stdout: str = "",
    stderr: str = "",
    blockers: list[str] | tuple[str, ...] | None = None,
) -> Path:
    """Write a worker invocation manifest for transitional sidecar packages.

    This keeps catalog diagnostics consistent while explicitly preserving that
    the package came from a legacy service adapter, not the isolated standard
    worker or task bridge.
    """

    root = Path(package_dir)
    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    command_vector = command if isinstance(command, list) else [command]
    manifest = {
        "schema_version": "biomedpilot.analysis.worker_invocation.v1",
        "created_at": created_at,
        "module_id": module_id,
        "mode": mode,
        "task_id": task_id,
        "worker_backend": "legacy_service_adapter",
        "invocation_status": "sidecar_recorded",
        "standard_worker_entrypoint": "not_used",
        "input_manifest": "service_adapter_payload",
        "output_contract": "standard_result_package",
        "runtime_install_policy": "forbidden",
        "resource_download_policy": "forbidden",
        "returncode": returncode,
        "command": [str(item) for item in command_vector],
        "stdout": stdout,
        "stderr": stderr,
        "blockers": list(blockers or []),
        "worker_boundary": {
            "boundary_type": "legacy_service_adapter_sidecar",
            "task_system_invocation": "legacy_service_adapter_direct_call",
            "migration_status": "sidecar_only_not_isolated_standard_worker",
            "subprocess_owner": subprocess_owner,
        },
    }
    path = logs_dir / "worker_invocation.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def validate_standard_result_package(
    package_dir: str | Path,
    *,
    expected_module_id: str = "",
    expected_task_id: str = "",
    expected_mode: str = "",
) -> dict[str, Any]:
    root = Path(package_dir).expanduser().resolve()
    blockers: list[str] = []
    warnings: list[str] = []
    for filename in REQUIRED_FILES:
        if not (root / filename).is_file():
            blockers.append(f"missing_required_file:{filename}")
    for dirname in REQUIRED_DIRECTORIES:
        if not (root / dirname).is_dir():
            blockers.append(f"missing_required_directory:{dirname}")

    result = _load_json(root / "result.json") if (root / "result.json").is_file() else {}
    provenance = _load_json(root / "provenance.json") if (root / "provenance.json").is_file() else {}
    package_manifest = _standard_result_package_manifest(root, result)
    invocation_path = root / "logs" / "worker_invocation.json"
    invocation = _load_json(invocation_path) if invocation_path.is_file() else {}
    if package_manifest.get("schema_version") != "biomedpilot.analysis.result_package.v1":
        blockers.append("result_package_schema_version_mismatch")
    if result.get("schema_version") != "biomedpilot.analysis.result.v1":
        blockers.append("result_schema_version_mismatch")
    if provenance.get("schema_version") != "biomedpilot.analysis.provenance.v1":
        blockers.append("provenance_schema_version_mismatch")
    blockers.extend(_payload_required_field_blockers("result_package", package_manifest, RESULT_PACKAGE_SCHEMA_PATH))
    blockers.extend(_payload_schema_shape_blockers("result_package", package_manifest, RESULT_PACKAGE_SCHEMA_PATH))
    blockers.extend(_payload_required_field_blockers("result", result, RESULT_PAYLOAD_SCHEMA_PATH))
    blockers.extend(_payload_required_field_blockers("provenance", provenance, PROVENANCE_PAYLOAD_SCHEMA_PATH))
    blockers.extend(_payload_schema_shape_blockers("result", result, RESULT_PAYLOAD_SCHEMA_PATH))
    blockers.extend(_payload_schema_shape_blockers("provenance", provenance, PROVENANCE_PAYLOAD_SCHEMA_PATH))
    for payload_name, payload in (("result", result), ("provenance", provenance)):
        if expected_module_id and payload.get("module_id") != expected_module_id:
            blockers.append(f"{payload_name}_module_id_mismatch")
        if expected_task_id and payload.get("task_id") != expected_task_id:
            blockers.append(f"{payload_name}_task_id_mismatch")
        if expected_mode and payload.get("mode") != expected_mode:
            blockers.append(f"{payload_name}_mode_mismatch")
    if result.get("status") not in {"passed", "blocked", "failed"}:
        blockers.append("result_status_invalid_or_missing")
    if not provenance.get("input_hash"):
        warnings.append("provenance_input_hash_missing")
    if not provenance.get("parameter_hash"):
        warnings.append("provenance_parameter_hash_missing")
    if not provenance.get("command"):
        warnings.append("provenance_command_missing")
    blockers.extend(_declared_artifact_blockers(root, result))
    blockers.extend(_passed_package_provenance_blockers(result, provenance))
    formal_blockers = _formal_package_provenance_blockers(result, provenance, expected_mode=expected_mode)
    blockers.extend(formal_blockers)
    blockers.extend(_analysis_environment_blockers(result, provenance, expected_mode=expected_mode))
    blockers.extend(
        _worker_invocation_blockers(
            root,
            invocation,
            provenance,
            expected_module_id=expected_module_id,
            expected_task_id=expected_task_id,
            expected_mode=expected_mode,
        )
    )
    return {
        "schema_version": "biomedpilot.analysis.result_package_validation.v1",
        "status": "blocked" if blockers else "passed",
        "package_dir": str(root),
        "result_status": str(result.get("status") or ""),
        "result_package_schema": str(RESULT_PACKAGE_SCHEMA_PATH.relative_to(REPO_ROOT)),
        "package_manifest": package_manifest,
        "blockers": blockers,
        "warnings": warnings,
        "required_files": list(REQUIRED_FILES),
        "required_directories": list(REQUIRED_DIRECTORIES),
    }


def _standard_result_package_manifest(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    artifacts = {
        "tables": result.get("tables") if isinstance(result.get("tables"), list) else [],
        "plots": result.get("plots") if isinstance(result.get("plots"), list) else [],
        "reports": result.get("reports") if isinstance(result.get("reports"), list) else [],
        "logs": [
            {"artifact_type": "analysis_worker_log", "path": "logs/worker.log"}
        ]
        if (root / "logs" / "worker.log").is_file()
        else [],
    }
    if (root / "logs" / "worker_invocation.json").is_file():
        artifacts["logs"].append({"artifact_type": "analysis_worker_invocation_manifest", "path": "logs/worker_invocation.json"})
    return {
        "schema_version": "biomedpilot.analysis.result_package.v1",
        "module_id": str(result.get("module_id") or ""),
        "mode": str(result.get("mode") or ""),
        "task_id": str(result.get("task_id") or ""),
        "status": str(result.get("status") or ""),
        "result_json": "result.json" if (root / "result.json").is_file() else "",
        "provenance_json": "provenance.json" if (root / "provenance.json").is_file() else "",
        "directories": [dirname for dirname in REQUIRED_DIRECTORIES if (root / dirname).is_dir()],
        "artifacts": artifacts,
    }


def _passed_package_provenance_blockers(result: dict[str, Any], provenance: dict[str, Any]) -> list[str]:
    if result.get("status") != "passed":
        return []

    blockers: list[str] = []
    engine = provenance.get("engine") if isinstance(provenance.get("engine"), dict) else {}
    runtime = provenance.get("runtime") if isinstance(provenance.get("runtime"), dict) else {}

    for field in ("input_hash", "parameter_hash", "command"):
        if not provenance.get(field):
            blockers.append(f"passed_provenance_{field}_missing")
    if "random_seed" not in provenance:
        blockers.append("passed_provenance_random_seed_missing")
    for field in ("name", "version"):
        if not engine.get(field):
            blockers.append(f"passed_provenance_engine_{field}_missing")
    for field in ("r_version", "bioconductor_version", "package_versions", "external_tool_versions"):
        if field not in runtime:
            blockers.append(f"passed_provenance_runtime_{field}_missing")
    if not isinstance(runtime.get("package_versions"), dict):
        blockers.append("passed_provenance_runtime_package_versions_invalid")
    if not isinstance(runtime.get("external_tool_versions"), dict):
        blockers.append("passed_provenance_runtime_external_tool_versions_invalid")
    return blockers


def _payload_required_field_blockers(payload_name: str, payload: dict[str, Any], schema_path: Path) -> list[str]:
    schema = _load_schema(schema_path)
    required = schema.get("required")
    if not isinstance(required, list):
        return [f"{payload_name}_payload_schema_required_fields_missing"]
    blockers: list[str] = []
    for field in required:
        if not isinstance(field, str):
            continue
        if field not in payload:
            blockers.append(f"{payload_name}_schema_required_field_missing:{field}")
    return blockers


def _payload_schema_shape_blockers(payload_name: str, payload: dict[str, Any], schema_path: Path) -> list[str]:
    schema = _load_schema(schema_path)
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return [f"{payload_name}_payload_schema_properties_missing"]
    blockers: list[str] = []
    for field, field_schema in properties.items():
        if not isinstance(field, str) or field not in payload or not isinstance(field_schema, dict):
            continue
        blockers.extend(_schema_value_blockers(payload_name, field, payload[field], field_schema))
    return blockers


def _schema_value_blockers(payload_name: str, field_path: str, value: Any, schema: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if "const" in schema and value != schema["const"]:
        blockers.append(f"{payload_name}_schema_field_const_mismatch:{field_path}")
    enum = schema.get("enum")
    if isinstance(enum, list) and value not in enum:
        blockers.append(f"{payload_name}_schema_field_enum_invalid:{field_path}")
    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _value_matches_schema_type(value, expected_type):
        blockers.append(f"{payload_name}_schema_field_type_invalid:{field_path}")
        return blockers
    if isinstance(expected_type, list) and not any(isinstance(item, str) and _value_matches_schema_type(value, item) for item in expected_type):
        blockers.append(f"{payload_name}_schema_field_type_invalid:{field_path}")
        return blockers
    min_length = schema.get("minLength")
    if isinstance(min_length, int) and isinstance(value, str) and len(value) < min_length:
        blockers.append(f"{payload_name}_schema_field_min_length_invalid:{field_path}")
    if _schema_allows_type(expected_type, "array") and isinstance(value, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            blockers.extend(_array_item_blockers(payload_name, field_path, value, item_schema))
        contains_schema = schema.get("contains")
        if isinstance(contains_schema, dict) and not any(_schema_contains_match(item, contains_schema) for item in value):
            blockers.append(f"{payload_name}_schema_array_contains_missing:{field_path}")
    if _schema_allows_type(expected_type, "object") and isinstance(value, dict):
        blockers.extend(_object_nested_blockers(payload_name, field_path, value, schema))
    return blockers


def _object_nested_blockers(payload_name: str, field_path: str, value: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    required = schema.get("required")
    if isinstance(required, list):
        for item in required:
            if isinstance(item, str) and item not in value:
                blockers.append(f"{payload_name}_schema_required_field_missing:{field_path}.{item}")
    properties = schema.get("properties")
    if isinstance(properties, dict):
        for field, field_schema in properties.items():
            if isinstance(field, str) and field in value and isinstance(field_schema, dict):
                blockers.extend(_schema_value_blockers(payload_name, f"{field_path}.{field}", value[field], field_schema))
    return blockers


def _array_item_blockers(payload_name: str, field_path: str, values: list[Any], item_schema: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for index, item in enumerate(values):
        item_path = f"{field_path}[{index}]"
        blockers.extend(_schema_value_blockers(payload_name, item_path, item, item_schema))
    return blockers


def _schema_allows_type(expected_type: object, type_name: str) -> bool:
    if expected_type == type_name:
        return True
    return isinstance(expected_type, list) and type_name in expected_type


def _schema_contains_match(value: Any, schema: dict[str, Any]) -> bool:
    if "const" in schema and value != schema["const"]:
        return False
    enum = schema.get("enum")
    if isinstance(enum, list) and value not in enum:
        return False
    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _value_matches_schema_type(value, expected_type):
        return False
    return True


def _value_matches_schema_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected_type == "null":
        return value is None
    return True


def _load_schema(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _formal_package_provenance_blockers(result: dict[str, Any], provenance: dict[str, Any], *, expected_mode: str) -> list[str]:
    status = str(result.get("status") or "")
    mode = str(result.get("mode") or provenance.get("mode") or expected_mode or "")
    semantics = str(result.get("result_semantics") or "")
    if status != "passed" or (mode != "full" and semantics != "formal_computed_result"):
        return []

    blockers: list[str] = []
    engine = provenance.get("engine") if isinstance(provenance.get("engine"), dict) else {}
    runtime = provenance.get("runtime") if isinstance(provenance.get("runtime"), dict) else {}
    worker_boundary = provenance.get("worker_boundary") if isinstance(provenance.get("worker_boundary"), dict) else {}

    for field in ("input_hash", "parameter_hash", "command"):
        if not provenance.get(field):
            blockers.append(f"formal_provenance_{field}_missing")
    if "random_seed" not in provenance:
        blockers.append("formal_provenance_random_seed_missing")
    for field in ("name", "version"):
        if not engine.get(field):
            blockers.append(f"formal_provenance_engine_{field}_missing")
    for field in ("r_version", "bioconductor_version", "package_versions", "external_tool_versions"):
        if field not in runtime:
            blockers.append(f"formal_provenance_runtime_{field}_missing")
    if not isinstance(runtime.get("package_versions"), dict):
        blockers.append("formal_provenance_runtime_package_versions_invalid")
    if not isinstance(runtime.get("external_tool_versions"), dict):
        blockers.append("formal_provenance_runtime_external_tool_versions_invalid")

    engine_name = str(engine.get("name") or "")
    if engine_name != "biomedpilot_standard_r_worker" and not worker_boundary.get("boundary_type"):
        blockers.append("formal_provenance_worker_boundary_missing")
    return blockers


def _declared_artifact_blockers(root: Path, result: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for group in ("tables", "plots", "reports"):
        artifacts = result.get(group)
        if artifacts is None:
            continue
        if not isinstance(artifacts, list):
            blockers.append(f"declared_artifacts_{group}_invalid")
            continue
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                blockers.append(f"declared_artifact_{group}_{index}_invalid")
                continue
            declared_path = artifact.get("path")
            if not isinstance(declared_path, str) or not declared_path.strip():
                blockers.append(f"declared_artifact_{group}_{index}_path_missing")
                continue
            path = Path(declared_path)
            if path.is_absolute():
                blockers.append(f"declared_artifact_{group}_{index}_path_absolute")
                continue
            resolved = (root / path).resolve()
            group_root = (root / group).resolve()
            if not _is_relative_to(resolved, group_root):
                blockers.append(f"declared_artifact_{group}_{index}_path_outside_standard_group")
                continue
            if not resolved.is_file():
                blockers.append(f"declared_artifact_{group}_{index}_file_missing")
    return blockers


def _analysis_environment_blockers(result: dict[str, Any], provenance: dict[str, Any], *, expected_mode: str) -> list[str]:
    mode = str(result.get("mode") or provenance.get("mode") or expected_mode or "")
    environment = provenance.get("analysis_environment")
    worker_boundary = provenance.get("worker_boundary") if isinstance(provenance.get("worker_boundary"), dict) else {}
    if worker_boundary.get("boundary_type") == "legacy_service_adapter_sidecar":
        return []
    if mode != "full" and environment is None:
        return []
    if not isinstance(environment, dict):
        return ["analysis_environment_snapshot_missing_or_invalid"]

    blockers: list[str] = []
    required_fields = (
        "schema_version",
        "status",
        "mode",
        "module_id",
        "environment_id",
        "dockerfile",
        "renv_lock",
        "allows_heavy_analysis_dependencies",
        "resource_lock_required",
        "external_tool_lock_required",
        "full_mode_requires_isolated_environment",
        "environment_registry_is_authoritative",
        "runtime_package_install",
        "runtime_resource_download",
        "module_manifest",
        "environment_lock_status",
        "resource_lock_status",
    )
    missing = [field for field in required_fields if field not in environment]
    if missing:
        blockers.append(f"analysis_environment_required_fields_missing:{','.join(missing)}")
    if environment.get("schema_version") != "biomedpilot.analysis_environment_snapshot.v1":
        blockers.append("analysis_environment_schema_version_mismatch")
    if environment.get("mode") != mode:
        blockers.append("analysis_environment_mode_mismatch")
    if result.get("module_id") and environment.get("module_id") != result.get("module_id"):
        blockers.append("analysis_environment_module_id_mismatch")
    if mode == "full":
        for field in ("environment_id", "dockerfile", "renv_lock", "module_manifest"):
            if not environment.get(field):
                blockers.append(f"analysis_environment_{field}_missing")
        if environment.get("full_mode_requires_isolated_environment") is not True:
            blockers.append("analysis_environment_full_mode_isolation_policy_invalid")
        if environment.get("environment_registry_is_authoritative") is not True:
            blockers.append("analysis_environment_registry_policy_invalid")
    if environment.get("runtime_package_install") != "forbidden":
        blockers.append("analysis_environment_runtime_package_install_policy_invalid")
    if environment.get("runtime_resource_download") != "forbidden":
        blockers.append("analysis_environment_runtime_resource_download_policy_invalid")
    environment_lock_status = environment.get("environment_lock_status")
    if not isinstance(environment_lock_status, dict):
        blockers.append("analysis_environment_lock_status_invalid")
    else:
        if "ready" not in environment_lock_status:
            blockers.append("analysis_environment_lock_status_ready_missing")
        if not isinstance(environment_lock_status.get("blockers"), list):
            blockers.append("analysis_environment_lock_status_blockers_invalid")
        status = str(environment.get("status") or "")
        if status == "blocked_full_mode_environment_lock" and not environment_lock_status.get("blockers"):
            blockers.append("analysis_environment_lock_blockers_missing")
    resource_lock_status = environment.get("resource_lock_status")
    if not isinstance(resource_lock_status, dict):
        blockers.append("analysis_environment_resource_lock_status_invalid")
    else:
        if "full_mode_ready" not in resource_lock_status:
            blockers.append("analysis_environment_resource_lock_status_full_mode_ready_missing")
        for field in ("required_resource_ids", "blocked_resource_ids", "blockers", "warnings"):
            if not isinstance(resource_lock_status.get(field), list):
                blockers.append(f"analysis_environment_resource_lock_status_{field}_invalid")
        status = str(environment.get("status") or "")
        if status == "blocked_full_mode_resource_or_tool_lock" and not resource_lock_status.get("blockers"):
            blockers.append("analysis_environment_resource_lock_blockers_missing")
    return blockers


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _worker_invocation_blockers(
    root: Path,
    invocation: dict[str, Any],
    provenance: dict[str, Any],
    *,
    expected_module_id: str,
    expected_task_id: str,
    expected_mode: str,
) -> list[str]:
    engine = provenance.get("engine") if isinstance(provenance.get("engine"), dict) else {}
    worker_boundary = provenance.get("worker_boundary") if isinstance(provenance.get("worker_boundary"), dict) else {}
    engine_name = str(engine.get("name") or "")
    invocation_required = engine_name in TASK_BRIDGE_ENGINES or worker_boundary.get("boundary_type") == "legacy_service_adapter_sidecar"
    if not invocation:
        return ["worker_invocation_manifest_missing"] if invocation_required else []

    blockers: list[str] = []
    required_fields = (
        "schema_version",
        "created_at",
        "module_id",
        "mode",
        "task_id",
        "worker_backend",
        "invocation_status",
        "standard_worker_entrypoint",
        "input_manifest",
        "output_contract",
        "runtime_install_policy",
        "resource_download_policy",
        "returncode",
        "command",
        "stdout",
        "stderr",
        "blockers",
        "worker_boundary",
    )
    missing = [field for field in required_fields if field not in invocation]
    if missing:
        blockers.append(f"worker_invocation_required_fields_missing:{','.join(missing)}")
    if invocation.get("schema_version") != "biomedpilot.analysis.worker_invocation.v1":
        blockers.append("worker_invocation_schema_version_mismatch")
    if expected_module_id and invocation.get("module_id") != expected_module_id:
        blockers.append("worker_invocation_module_id_mismatch")
    if expected_task_id and invocation.get("task_id") != expected_task_id:
        blockers.append("worker_invocation_task_id_mismatch")
    if expected_mode and invocation.get("mode") != expected_mode:
        blockers.append("worker_invocation_mode_mismatch")
    if invocation.get("worker_backend") not in WORKER_BACKENDS:
        blockers.append("worker_invocation_worker_backend_invalid")
    if invocation.get("invocation_status") not in WORKER_INVOCATION_STATUSES:
        blockers.append("worker_invocation_status_invalid")
    if invocation.get("output_contract") != "standard_result_package":
        blockers.append("worker_invocation_output_contract_invalid")
    if invocation.get("runtime_install_policy") != "forbidden":
        blockers.append("worker_invocation_runtime_install_policy_invalid")
    if invocation.get("resource_download_policy") != "forbidden":
        blockers.append("worker_invocation_resource_download_policy_invalid")
    if not isinstance(invocation.get("command"), list):
        blockers.append("worker_invocation_command_invalid")
    if not isinstance(invocation.get("blockers"), list):
        blockers.append("worker_invocation_blockers_invalid")
    boundary = invocation.get("worker_boundary")
    if not isinstance(boundary, dict):
        blockers.append("worker_invocation_worker_boundary_invalid")
    else:
        for field in ("boundary_type", "task_system_invocation", "migration_status"):
            if not boundary.get(field):
                blockers.append(f"worker_invocation_worker_boundary_{field}_missing")
        if boundary.get("task_system_invocation") not in TASK_SYSTEM_INVOCATIONS:
            blockers.append("worker_invocation_task_system_invocation_invalid")
        blockers.extend(
            _worker_input_manifest_blockers(
                root,
                invocation,
                boundary,
                expected_module_id=expected_module_id,
                expected_task_id=expected_task_id,
                expected_mode=expected_mode,
            )
        )
    return blockers


def _worker_input_manifest_blockers(
    root: Path,
    invocation: dict[str, Any],
    boundary: dict[str, Any],
    *,
    expected_module_id: str,
    expected_task_id: str,
    expected_mode: str,
) -> list[str]:
    input_manifest = invocation.get("input_manifest")
    if not isinstance(input_manifest, str) or not input_manifest.strip():
        return ["worker_invocation_input_manifest_invalid"]
    task_system_invocation = str(boundary.get("task_system_invocation") or "")
    if task_system_invocation == "task_center_registered" and input_manifest != "module_input.json":
        return ["worker_invocation_input_manifest_not_materialized_for_task_center"]
    if input_manifest != "module_input.json":
        return []

    path = root / input_manifest
    if not path.is_file():
        return [f"worker_invocation_input_manifest_missing:{input_manifest}"]
    payload = _safe_load_json(path)
    if not payload:
        return [f"worker_invocation_input_manifest_invalid_json:{input_manifest}"]

    blockers = []
    blockers.extend(_payload_required_field_blockers("module_input_manifest", payload, MODULE_INPUT_SCHEMA_PATH))
    blockers.extend(_payload_schema_shape_blockers("module_input_manifest", payload, MODULE_INPUT_SCHEMA_PATH))
    if expected_module_id and payload.get("module_id") != expected_module_id:
        blockers.append("module_input_manifest_module_id_mismatch")
    if expected_task_id and payload.get("task_id") != expected_task_id:
        blockers.append("module_input_manifest_task_id_mismatch")
    if expected_mode and payload.get("mode") != expected_mode:
        blockers.append("module_input_manifest_mode_mismatch")
    return blockers


def _safe_load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
