from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import REPO_ROOT


RESOURCE_MANIFEST_PATH = REPO_ROOT / "analysis" / "resources" / "manifest.json"
ENVIRONMENT_REGISTRY_PATH = REPO_ROOT / "analysis" / "registry" / "analysis_environments.json"
MODULE_REGISTRY_PATH = REPO_ROOT / "analysis" / "registry" / "analysis_modules.json"
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


def _is_placeholder_resource_value(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text.lower() in PLACEHOLDER_RESOURCE_VALUES


def _blocked_resource_has_partial_final_lock(item: dict[str, Any]) -> bool:
    return any(not _is_placeholder_resource_value(item.get(field)) for field in FINAL_LOCK_REQUIRED_FIELDS)


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
    if policy.get("environment") != environment_id:
        blockers.append(f"analysis_environment_renv_lock_environment_mismatch:{environment_id}")
    if policy.get("runtime_package_install") != "forbidden":
        blockers.append(f"analysis_environment_renv_lock_runtime_install_policy_invalid:{environment_id}")
    status = str(policy.get("status") or "missing")
    if status not in RESTORED_LOCK_STATUSES:
        blockers.append(f"analysis_environment_renv_lock_not_restored:{environment_id}:{status}")
    return blockers
