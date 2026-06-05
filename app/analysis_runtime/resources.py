from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import REPO_ROOT


RESOURCE_MANIFEST_PATH = REPO_ROOT / "analysis" / "resources" / "manifest.json"
ENVIRONMENT_REGISTRY_PATH = REPO_ROOT / "analysis" / "registry" / "analysis_environments.json"
MODULE_REGISTRY_PATH = REPO_ROOT / "analysis" / "registry" / "analysis_modules.json"
RESOURCE_LOCK_EVIDENCE_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "resource_lock_evidence.schema.json"
REQUIRED_RESOURCE_FIELDS = (
    "resource_id",
    "title",
    "version",
    "source",
    "hash",
    "license",
    "cache_path",
    "status",
    "required_for_modules",
)
REQUIRED_ENVIRONMENT_FIELDS = (
    "environment_id",
    "title",
    "purpose",
    "dockerfile",
    "renv_lock",
    "r_runtime",
    "allows_heavy_analysis_dependencies",
    "resource_lock_required",
    "external_tool_lock_required",
    "allowed_module_ids",
)
PLACEHOLDER_RESOURCE_VALUES = {
    "required_before_full_mode",
    "required_before_lite_mode",
    "pending",
    "todo",
    "tbd",
    "",
}
FINAL_LOCK_REQUIRED_FIELDS = ("version", "source", "hash", "license", "cache_path")
BLOCKED_RESOURCE_STATUSES = {
    "blocked_until_resource_lock",
    "blocked_until_tool_lock",
    "blocked_until_reference_lock",
}
RESTORED_LOCK_STATUSES = {"restored", "locked", "active"}


def load_analysis_resource_manifest(path: str | Path | None = None) -> dict[str, Any]:
    manifest_path = Path(path).expanduser().resolve() if path else RESOURCE_MANIFEST_PATH
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def load_analysis_environment_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = Path(path).expanduser().resolve() if path else ENVIRONMENT_REGISTRY_PATH
    return json.loads(registry_path.read_text(encoding="utf-8"))


def validate_analysis_resource_manifest(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = manifest or load_analysis_resource_manifest()
    blockers: list[str] = []
    warnings: list[str] = []
    resources = payload.get("resources")
    if payload.get("schema_version") != "biomedpilot.analysis_resources.v1":
        blockers.append("analysis_resource_manifest_schema_version_mismatch")
    if not isinstance(resources, list) or not resources:
        blockers.append("analysis_resource_manifest_resources_missing")
        resources = []

    seen: set[str] = set()
    locked_resource_ids: list[str] = []
    blocked_resource_ids: list[str] = []
    for item in resources:
        if not isinstance(item, dict):
            blockers.append("analysis_resource_manifest_resource_invalid")
            continue
        resource_id = str(item.get("resource_id") or "")
        if not resource_id:
            blockers.append("analysis_resource_id_missing")
        elif resource_id in seen:
            blockers.append(f"analysis_resource_id_duplicate:{resource_id}")
        seen.add(resource_id)
        missing_fields = [field for field in REQUIRED_RESOURCE_FIELDS if not item.get(field)]
        if missing_fields:
            blockers.append(f"analysis_resource_required_fields_missing:{resource_id or 'unknown'}:{','.join(missing_fields)}")
        status = str(item.get("status") or "")
        if status == "locked":
            locked_resource_ids.append(resource_id)
            placeholder_fields = [
                field
                for field in FINAL_LOCK_REQUIRED_FIELDS
                if _is_placeholder_resource_value(item.get(field))
            ]
            if placeholder_fields:
                blockers.append(
                    f"analysis_resource_locked_with_placeholder_fields:{resource_id or 'unknown'}:{','.join(placeholder_fields)}"
                )
            lock_evidence_path = str(item.get("lock_evidence") or "")
            if not lock_evidence_path:
                blockers.append(f"analysis_resource_lock_evidence_missing:{resource_id or 'unknown'}")
            else:
                evidence_path = REPO_ROOT / lock_evidence_path
                if not evidence_path.is_file():
                    blockers.append(f"analysis_resource_lock_evidence_not_found:{resource_id or 'unknown'}:{lock_evidence_path}")
                else:
                    try:
                        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
                    except json.JSONDecodeError:
                        blockers.append(f"analysis_resource_lock_evidence_invalid_json:{resource_id or 'unknown'}:{lock_evidence_path}")
                    else:
                        evidence_validation = validate_analysis_resource_lock_evidence(resource_id, evidence, manifest=payload)
                        blockers.extend(
                            f"analysis_resource_lock_evidence:{resource_id or 'unknown'}:{blocker}"
                            for blocker in evidence_validation.get("blockers", [])
                        )
        elif status in BLOCKED_RESOURCE_STATUSES:
            blocked_resource_ids.append(resource_id)
            if _blocked_resource_has_partial_final_lock(item):
                warnings.append(f"blocked_resource_has_partial_final_lock:{resource_id}")
        else:
            blockers.append(f"analysis_resource_status_invalid:{resource_id or 'unknown'}:{status or 'missing'}")
        if item.get("runtime_download_allowed") is not False:
            blockers.append(f"analysis_resource_runtime_download_not_forbidden:{resource_id or 'unknown'}")

    return {
        "schema_version": "biomedpilot.analysis_resource_manifest_validation.v1",
        "status": "blocked" if blockers else "passed",
        "full_mode_ready": not blockers and len(blocked_resource_ids) == 0,
        "resource_count": len(resources),
        "locked_resource_ids": locked_resource_ids,
        "blocked_resource_ids": blocked_resource_ids,
        "blockers": blockers,
        "warnings": warnings,
    }


def validate_analysis_resource_lock_evidence(
    resource_id: str,
    evidence: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a resource lock evidence payload before a resource can be locked."""

    payload = manifest or load_analysis_resource_manifest()
    resources = {
        str(item.get("resource_id") or ""): item
        for item in payload.get("resources", [])
        if isinstance(item, dict) and item.get("resource_id")
    }
    blockers: list[str] = []
    warnings: list[str] = []
    blockers.extend(_resource_lock_evidence_schema_blockers(evidence))
    resource_key = str(resource_id or evidence.get("resource_id") or "")
    resource = resources.get(resource_key)
    if resource is None:
        blockers.append(f"analysis_resource_lock_evidence_resource_unregistered:{resource_key}")
    if str(evidence.get("resource_id") or resource_key) != resource_key:
        blockers.append("analysis_resource_lock_evidence_resource_id_mismatch")

    status = str(evidence.get("status") or "")
    if status != "locked":
        blockers.append("analysis_resource_lock_evidence_status_not_locked")
    if evidence.get("runtime_download_allowed") is not False:
        blockers.append("analysis_resource_lock_evidence_runtime_download_not_forbidden")

    hash_payload = evidence.get("hash")
    if not isinstance(hash_payload, dict):
        blockers.append("analysis_resource_lock_evidence_hash_invalid")
    else:
        algorithm = str(hash_payload.get("algorithm") or "")
        value = str(hash_payload.get("value") or "")
        if not algorithm:
            blockers.append("analysis_resource_lock_evidence_hash_algorithm_missing")
        if _is_placeholder_resource_value(value):
            blockers.append("analysis_resource_lock_evidence_hash_value_missing")

    for field in FINAL_LOCK_REQUIRED_FIELDS:
        value: Any
        if field == "hash":
            value = hash_payload.get("value") if isinstance(hash_payload, dict) else None
        else:
            value = evidence.get(field)
        if _is_placeholder_resource_value(value):
            blockers.append(f"analysis_resource_lock_evidence_placeholder_field:{field}")

    cache_path = str(evidence.get("cache_path") or "")
    if cache_path and not (REPO_ROOT / cache_path).exists():
        blockers.append(f"analysis_resource_lock_evidence_cache_path_not_found:{cache_path}")

    evidence_files = evidence.get("evidence_files")
    if not isinstance(evidence_files, list) or not evidence_files:
        blockers.append("analysis_resource_lock_evidence_files_missing")
    else:
        for item in evidence_files:
            evidence_file = str(item or "")
            if not evidence_file:
                blockers.append("analysis_resource_lock_evidence_file_invalid")
            elif not (REPO_ROOT / evidence_file).is_file():
                blockers.append(f"analysis_resource_lock_evidence_file_not_found:{evidence_file}")

    approved_modules = evidence.get("approved_for_modules")
    approved = {str(item) for item in approved_modules if item is not None} if isinstance(approved_modules, list) else set()
    if not approved:
        blockers.append("analysis_resource_lock_evidence_approved_modules_missing")
    if resource is not None:
        required = {
            str(item)
            for item in resource.get("required_for_modules", [])
            if item is not None
        }
        if approved != required:
            blockers.append("analysis_resource_lock_evidence_approved_modules_mismatch")
        for field in ("version", "source", "license", "cache_path"):
            if str(evidence.get(field) or "") != str(resource.get(field) or ""):
                blockers.append(f"analysis_resource_lock_evidence_manifest_field_mismatch:{field}")
        manifest_hash = str(resource.get("hash") or "")
        evidence_hash = str(hash_payload.get("value") or "") if isinstance(hash_payload, dict) else ""
        if manifest_hash != evidence_hash:
            blockers.append("analysis_resource_lock_evidence_manifest_field_mismatch:hash")

    return {
        "schema_version": "biomedpilot.analysis.resource_lock_evidence_validation.v1",
        "status": "blocked" if blockers else "passed",
        "resource_id": resource_key,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": warnings,
    }


def validate_analysis_environment_registry(
    environment_registry: dict[str, Any] | None = None,
    *,
    module_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the environment split without claiming full readiness.

    Structural blockers mean the registry cannot be trusted. Readiness blockers
    mean the registry is structurally usable but full analysis must remain
    disabled until the isolated environment locks are restored.
    """

    environment_payload = environment_registry or load_analysis_environment_registry()
    module_payload = module_registry or json.loads(MODULE_REGISTRY_PATH.read_text(encoding="utf-8"))
    blockers: list[str] = []
    readiness_blockers: list[str] = []
    warnings: list[str] = []
    environments = environment_payload.get("environments")
    modules = module_payload.get("modules")
    if environment_payload.get("schema_version") != "biomedpilot.analysis_environments.v1":
        blockers.append("analysis_environment_registry_schema_version_mismatch")
    policy = environment_payload.get("policy") if isinstance(environment_payload.get("policy"), dict) else {}
    if not policy:
        blockers.append("analysis_environment_registry_policy_missing")
    else:
        if policy.get("default_app_dependency") is not False:
            blockers.append("analysis_environment_registry_default_app_dependency_policy_invalid")
        if policy.get("runtime_package_install") != "forbidden":
            blockers.append("analysis_environment_registry_runtime_package_install_policy_invalid")
        if policy.get("runtime_resource_download") != "forbidden":
            blockers.append("analysis_environment_registry_runtime_resource_download_policy_invalid")
        if policy.get("full_mode_requires_isolated_environment") is not True:
            blockers.append("analysis_environment_registry_full_mode_isolation_policy_invalid")
        if policy.get("environment_registry_is_authoritative") is not True:
            blockers.append("analysis_environment_registry_authoritative_policy_invalid")
    if not isinstance(environments, list) or not environments:
        blockers.append("analysis_environment_registry_environments_missing")
        environments = []
    if not isinstance(modules, list):
        blockers.append("analysis_module_registry_modules_missing")
        modules = []

    registered_modules = {
        str(item.get("module_id") or ""): item
        for item in modules
        if isinstance(item, dict)
    }
    seen: set[str] = set()
    environment_ids: list[str] = []
    for item in environments:
        if not isinstance(item, dict):
            blockers.append("analysis_environment_registry_environment_invalid")
            continue
        environment_id = str(item.get("environment_id") or "")
        if not environment_id:
            blockers.append("analysis_environment_id_missing")
        elif environment_id in seen:
            blockers.append(f"analysis_environment_id_duplicate:{environment_id}")
        seen.add(environment_id)
        if environment_id:
            environment_ids.append(environment_id)
        missing_fields = [field for field in REQUIRED_ENVIRONMENT_FIELDS if field not in item]
        if missing_fields:
            blockers.append(f"analysis_environment_required_fields_missing:{environment_id or 'unknown'}:{','.join(missing_fields)}")
        allowed_modules = item.get("allowed_module_ids")
        if not isinstance(allowed_modules, list):
            blockers.append(f"analysis_environment_allowed_module_ids_invalid:{environment_id or 'unknown'}")
            allowed_modules = []
        for module_id in {str(value) for value in allowed_modules if value is not None}:
            if module_id not in registered_modules:
                blockers.append(f"analysis_environment_allowed_module_unregistered:{environment_id}:{module_id}")
        blockers.extend(_environment_file_policy_blockers(item, environment_id))
        readiness_blockers.extend(_environment_readiness_blockers(item, environment_id))
        if environment_id == "app-dev":
            if allowed_modules:
                blockers.append("analysis_environment_app_dev_allows_analysis_modules")
            if item.get("r_runtime") != "not_required":
                blockers.append("analysis_environment_app_dev_r_runtime_required")
            if item.get("allows_heavy_analysis_dependencies") is not False:
                blockers.append("analysis_environment_app_dev_heavy_dependency_policy_invalid")
        if environment_id == "r-bio-core" and item.get("allows_heavy_analysis_dependencies") is not False:
            blockers.append("analysis_environment_bio_core_heavy_dependency_policy_invalid")
        if environment_id not in {"app-dev", "r-bio-core"} and item.get("allows_heavy_analysis_dependencies") is not True:
            blockers.append(f"analysis_environment_full_heavy_dependency_policy_invalid:{environment_id}")

    required_environment_ids = {
        "app-dev",
        "r-bio-core",
        "r-bio-full",
        "r-spatial-full",
        "r-chem-full",
        "r-chem-gpu",
    }
    missing_required = sorted(required_environment_ids - set(environment_ids))
    for environment_id in missing_required:
        blockers.append(f"analysis_environment_required_environment_missing:{environment_id}")

    for module_id, module in registered_modules.items():
        full_environment_id = str(module.get("full_environment") or "")
        analysis_environment_id = str(module.get("analysis_environment") or "")
        if full_environment_id and full_environment_id not in seen:
            blockers.append(f"analysis_module_full_environment_unregistered:{module_id}:{full_environment_id}")
        if analysis_environment_id and analysis_environment_id not in seen:
            blockers.append(f"analysis_module_lite_environment_unregistered:{module_id}:{analysis_environment_id}")

    return {
        "schema_version": "biomedpilot.analysis_environment_registry_validation.v1",
        "status": "blocked" if blockers else "passed",
        "full_mode_ready": not blockers and not readiness_blockers,
        "environment_count": len(environments),
        "environment_ids": environment_ids,
        "blocked_environment_ids": _blocked_environment_ids_from_readiness(readiness_blockers),
        "blockers": list(dict.fromkeys(blockers)),
        "readiness_blockers": list(dict.fromkeys(readiness_blockers)),
        "warnings": warnings,
    }


def _is_placeholder_resource_value(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text.lower() in PLACEHOLDER_RESOURCE_VALUES


def _blocked_resource_has_partial_final_lock(item: dict[str, Any]) -> bool:
    return any(not _is_placeholder_resource_value(item.get(field)) for field in FINAL_LOCK_REQUIRED_FIELDS)


def _resource_lock_evidence_schema_blockers(evidence: dict[str, Any]) -> list[str]:
    schema = _read_json(RESOURCE_LOCK_EVIDENCE_SCHEMA_PATH)
    blockers: list[str] = []
    required = schema.get("required") if isinstance(schema.get("required"), list) else []
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for field in required:
        if isinstance(field, str) and field not in evidence:
            blockers.append(f"analysis_resource_lock_evidence_required_field_missing:{field}")
    for field, field_schema in properties.items():
        if not isinstance(field, str) or field not in evidence or not isinstance(field_schema, dict):
            continue
        value = evidence[field]
        if "const" in field_schema and value != field_schema["const"]:
            blockers.append(f"analysis_resource_lock_evidence_const_mismatch:{field}")
        expected_type = field_schema.get("type")
        if isinstance(expected_type, str) and not _schema_type_matches(value, expected_type):
            blockers.append(f"analysis_resource_lock_evidence_type_invalid:{field}")
            continue
        min_length = field_schema.get("minLength")
        if isinstance(min_length, int) and isinstance(value, str) and len(value) < min_length:
            blockers.append(f"analysis_resource_lock_evidence_min_length_invalid:{field}")
    return blockers


def _schema_type_matches(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "null":
        return value is None
    return True


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _environment_file_policy_blockers(environment: dict[str, Any], environment_id: str) -> list[str]:
    blockers: list[str] = []
    blockers.extend(_dockerfile_environment_blockers(environment_id, str(environment.get("dockerfile") or "")))
    lockfile = str(environment.get("renv_lock") or "")
    if not lockfile:
        blockers.append(f"analysis_environment_renv_lock_missing:{environment_id}")
    elif not (REPO_ROOT / lockfile).is_file():
        blockers.append(f"analysis_environment_renv_lock_not_found:{environment_id}:{lockfile}")
    else:
        try:
            lock = json.loads((REPO_ROOT / lockfile).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            blockers.append(f"analysis_environment_renv_lock_invalid_json:{environment_id}:{lockfile}")
        else:
            policy = lock.get("BioMedPilotPolicy") if isinstance(lock.get("BioMedPilotPolicy"), dict) else {}
            policy_environment = str(policy.get("environment") or "")
            if not _renv_lock_environment_matches(environment_id, policy_environment):
                blockers.append(f"analysis_environment_renv_lock_environment_mismatch:{environment_id}")
            if policy.get("runtime_package_install") != "forbidden":
                blockers.append(f"analysis_environment_renv_lock_runtime_install_policy_invalid:{environment_id}")
    return blockers


def _environment_readiness_blockers(environment: dict[str, Any], environment_id: str) -> list[str]:
    if environment_id in {"app-dev", "r-bio-core"}:
        return []
    lockfile = str(environment.get("renv_lock") or "")
    if not lockfile or not (REPO_ROOT / lockfile).is_file():
        return []
    try:
        lock = json.loads((REPO_ROOT / lockfile).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    policy = lock.get("BioMedPilotPolicy") if isinstance(lock.get("BioMedPilotPolicy"), dict) else {}
    status = str(policy.get("status") or "missing")
    if status not in RESTORED_LOCK_STATUSES:
        return [f"analysis_environment_renv_lock_not_restored:{environment_id}:{status}"]
    return []


def _renv_lock_environment_matches(environment_id: str, policy_environment: str) -> bool:
    if policy_environment == environment_id:
        return True
    return environment_id == "r-chem-gpu" and policy_environment == "r-chem-full"


def _blocked_environment_ids_from_readiness(readiness_blockers: list[str]) -> list[str]:
    ids: list[str] = []
    for blocker in readiness_blockers:
        parts = blocker.split(":")
        if len(parts) >= 2:
            ids.append(parts[1])
    return list(dict.fromkeys(ids))


def full_mode_resource_blockers(module_id: str, manifest: dict[str, Any] | None = None) -> list[str]:
    payload = manifest or load_analysis_resource_manifest()
    validation = validate_analysis_resource_manifest(payload)
    blockers = list(validation.get("blockers", []))
    resources = payload.get("resources") if isinstance(payload.get("resources"), list) else []
    for item in resources:
        if not isinstance(item, dict):
            continue
        modules = item.get("required_for_modules")
        if not isinstance(modules, list) or module_id not in {str(value) for value in modules}:
            continue
        status = str(item.get("status") or "")
        if status in BLOCKED_RESOURCE_STATUSES:
            blockers.append(f"analysis_resource_not_locked:{item.get('resource_id')}")
    return list(dict.fromkeys(blockers))


def full_mode_environment_blockers(
    module_id: str,
    *,
    module_registry: dict[str, Any] | None = None,
    environment_registry: dict[str, Any] | None = None,
) -> list[str]:
    """Return blockers proving full mode is isolated and lock-restored.

    Full analysis must not become runnable merely because resources are locked.
    The module must also target an isolated registered environment with an
    existing Dockerfile and a restored renv/tool lock.
    """

    module_payload = module_registry or json.loads(MODULE_REGISTRY_PATH.read_text(encoding="utf-8"))
    environment_payload = environment_registry or load_analysis_environment_registry()
    modules = {
        str(item.get("module_id") or ""): item
        for item in module_payload.get("modules", [])
        if isinstance(item, dict)
    }
    environments = {
        str(item.get("environment_id") or ""): item
        for item in environment_payload.get("environments", [])
        if isinstance(item, dict)
    }
    blockers: list[str] = []
    module = modules.get(module_id)
    if not module:
        return [f"analysis_module_not_registered:{module_id}"]
    policy = environment_payload.get("policy") if isinstance(environment_payload.get("policy"), dict) else {}
    if policy.get("full_mode_requires_isolated_environment") is not True:
        blockers.append("analysis_environment_full_mode_isolation_policy_invalid")
    if policy.get("runtime_package_install") != "forbidden":
        blockers.append("analysis_environment_runtime_package_install_policy_invalid")
    if policy.get("runtime_resource_download") != "forbidden":
        blockers.append("analysis_environment_runtime_resource_download_policy_invalid")

    environment_id = str(module.get("full_environment") or "")
    if not environment_id:
        return list(dict.fromkeys([*blockers, f"analysis_full_environment_missing:{module_id}"]))
    environment = environments.get(environment_id)
    if not environment:
        return list(dict.fromkeys([*blockers, f"analysis_environment_missing:{environment_id}"]))
    allowed_module_ids = {
        str(item)
        for item in environment.get("allowed_module_ids", [])
        if item is not None
    }
    if module_id not in allowed_module_ids:
        blockers.append(f"analysis_environment_module_not_allowed:{environment_id}:{module_id}")
    if environment.get("allows_heavy_analysis_dependencies") is not True:
        blockers.append(f"analysis_environment_full_heavy_dependency_policy_invalid:{environment_id}")

    dockerfile = str(environment.get("dockerfile") or "")
    lockfile = str(environment.get("renv_lock") or "")
    blockers.extend(_dockerfile_environment_blockers(environment_id, dockerfile))
    blockers.extend(_renv_lock_environment_blockers(environment_id, lockfile))
    return list(dict.fromkeys(blockers))


def _dockerfile_environment_blockers(environment_id: str, dockerfile: str) -> list[str]:
    if not dockerfile:
        return [f"analysis_environment_dockerfile_missing:{environment_id}"]
    docker_path = REPO_ROOT / dockerfile
    if not docker_path.is_file():
        return [f"analysis_environment_dockerfile_not_found:{environment_id}:{dockerfile}"]
    text = docker_path.read_text(encoding="utf-8", errors="ignore")
    blockers: list[str] = []
    if f'org.biomedpilot.environment="{environment_id}"' not in text:
        blockers.append(f"analysis_environment_dockerfile_label_mismatch:{environment_id}")
    if 'runtime-package-install="forbidden"' not in text:
        blockers.append(f"analysis_environment_dockerfile_runtime_install_policy_invalid:{environment_id}")
    return blockers


def _renv_lock_environment_blockers(environment_id: str, lockfile: str) -> list[str]:
    if not lockfile:
        return [f"analysis_environment_renv_lock_missing:{environment_id}"]
    lock_path = REPO_ROOT / lockfile
    if not lock_path.is_file():
        return [f"analysis_environment_renv_lock_not_found:{environment_id}:{lockfile}"]
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [f"analysis_environment_renv_lock_invalid_json:{environment_id}:{lockfile}"]
    policy = lock.get("BioMedPilotPolicy") if isinstance(lock.get("BioMedPilotPolicy"), dict) else {}
    blockers: list[str] = []
    policy_environment = str(policy.get("environment") or "")
    if not _renv_lock_environment_matches(environment_id, policy_environment):
        blockers.append(f"analysis_environment_renv_lock_environment_mismatch:{environment_id}")
    if policy.get("runtime_package_install") != "forbidden":
        blockers.append(f"analysis_environment_renv_lock_runtime_install_policy_invalid:{environment_id}")
    status = str(policy.get("status") or "missing")
    if status not in RESTORED_LOCK_STATUSES:
        blockers.append(f"analysis_environment_renv_lock_not_restored:{environment_id}:{status}")
    return blockers
