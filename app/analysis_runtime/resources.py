from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .registry import REPO_ROOT


RESOURCE_MANIFEST_PATH = REPO_ROOT / "analysis" / "resources" / "manifest.json"
RESOURCE_LOCK_EVIDENCE_REGISTRY_PATH = REPO_ROOT / "analysis" / "registry" / "resource_lock_evidence.json"
ENVIRONMENT_REGISTRY_PATH = REPO_ROOT / "analysis" / "registry" / "analysis_environments.json"
ENVIRONMENT_LOCK_EVIDENCE_REGISTRY_PATH = REPO_ROOT / "analysis" / "registry" / "environment_lock_evidence.json"
MODULE_REGISTRY_PATH = REPO_ROOT / "analysis" / "registry" / "analysis_modules.json"
RESOURCE_LOCK_EVIDENCE_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "resource_lock_evidence.schema.json"
RESOURCE_LOCK_EVIDENCE_REGISTRY_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "resource_lock_evidence_registry.schema.json"
ENVIRONMENT_LOCK_EVIDENCE_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "environment_lock_evidence.schema.json"
ENVIRONMENT_LOCK_EVIDENCE_REGISTRY_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "environment_lock_evidence_registry.schema.json"
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
MOCK_FIXTURE_RESOURCE_ID = "mock_fixture_builtin_v1"
BLOCKED_RESOURCE_STATUSES = {
    "blocked_until_resource_lock",
    "blocked_until_tool_lock",
    "blocked_until_reference_lock",
}
RESTORED_LOCK_STATUSES = {"restored", "locked", "active"}


def load_analysis_resource_manifest(path: str | Path | None = None) -> dict[str, Any]:
    manifest_path = Path(path).expanduser().resolve() if path else RESOURCE_MANIFEST_PATH
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def load_analysis_resource_lock_evidence_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = Path(path).expanduser().resolve() if path else RESOURCE_LOCK_EVIDENCE_REGISTRY_PATH
    return json.loads(registry_path.read_text(encoding="utf-8"))


def load_analysis_environment_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = Path(path).expanduser().resolve() if path else ENVIRONMENT_REGISTRY_PATH
    return json.loads(registry_path.read_text(encoding="utf-8"))


def load_analysis_environment_lock_evidence_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = Path(path).expanduser().resolve() if path else ENVIRONMENT_LOCK_EVIDENCE_REGISTRY_PATH
    return json.loads(registry_path.read_text(encoding="utf-8"))


def validate_analysis_resource_manifest(
    manifest: dict[str, Any] | None = None,
    *,
    resource_lock_evidence_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = manifest or load_analysis_resource_manifest()
    evidence_registry = (
        resource_lock_evidence_registry
        if isinstance(resource_lock_evidence_registry, dict)
        else load_analysis_resource_lock_evidence_registry()
    )
    blockers: list[str] = []
    warnings: list[str] = []
    resources = payload.get("resources")
    evidence_registry_validation = validate_analysis_resource_lock_evidence_registry(
        evidence_registry,
        manifest=payload,
    )
    blockers.extend(
        f"analysis_resource_lock_evidence_registry:{blocker}"
        for blocker in evidence_registry_validation.get("blockers", [])
    )
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
                lock_evidence_path = _resource_lock_evidence_path_from_registry(resource_id, evidence_registry)
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
        "resource_lock_evidence_templates": _resource_lock_evidence_templates(resources),
        "evidence_registry_status": evidence_registry_validation.get("status"),
        "evidence_registry_entry_count": evidence_registry_validation.get("entry_count"),
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
    hash_algorithm = ""
    hash_value = ""
    if not isinstance(hash_payload, dict):
        blockers.append("analysis_resource_lock_evidence_hash_invalid")
    else:
        hash_algorithm = str(hash_payload.get("algorithm") or "")
        hash_value = str(hash_payload.get("value") or "")
        if not hash_algorithm:
            blockers.append("analysis_resource_lock_evidence_hash_algorithm_missing")
        elif not _resource_hash_algorithm_allowed(resource_key, hash_algorithm):
            blockers.append("analysis_resource_lock_evidence_hash_algorithm_not_allowed")
        if _is_placeholder_resource_value(hash_value):
            blockers.append("analysis_resource_lock_evidence_hash_value_missing")
        elif hash_algorithm == "sha256" and not _is_sha256_hex(hash_value):
            blockers.append("analysis_resource_lock_evidence_hash_value_not_sha256")
        elif hash_algorithm == "repository_fixture" and resource_key != MOCK_FIXTURE_RESOURCE_ID:
            blockers.append("analysis_resource_lock_evidence_repository_fixture_hash_for_full_resource")

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
    elif cache_path and hash_algorithm == "sha256" and _is_sha256_hex(hash_value):
        actual_hash = _sha256_path(REPO_ROOT / cache_path)
        if actual_hash != hash_value.lower():
            blockers.append("analysis_resource_lock_evidence_hash_mismatch")

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


def validate_analysis_resource_lock_evidence_registry(
    registry: dict[str, Any] | None = None,
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the authoritative registry for resource lock evidence."""

    payload = registry if isinstance(registry, dict) else load_analysis_resource_lock_evidence_registry()
    manifest_payload = manifest or load_analysis_resource_manifest()
    blockers: list[str] = []
    warnings: list[str] = []
    blockers.extend(_resource_lock_evidence_registry_schema_blockers(payload))
    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    if not policy:
        blockers.append("analysis_resource_lock_evidence_registry_policy_missing")
    else:
        if policy.get("registry_is_authoritative") is not True:
            blockers.append("analysis_resource_lock_evidence_registry_authoritative_policy_invalid")
        if policy.get("locked_resource_requires_schema_valid_evidence") is not True:
            blockers.append("analysis_resource_lock_evidence_registry_locked_policy_invalid")
        if policy.get("runtime_download_allowed") is not False:
            blockers.append("analysis_resource_lock_evidence_registry_runtime_download_policy_invalid")

    entries = payload.get("evidence_entries")
    if not isinstance(entries, list):
        blockers.append("analysis_resource_lock_evidence_registry_entries_invalid")
        entries = []
    seen: set[str] = set()
    registered_resource_ids: list[str] = []
    for item in entries:
        if not isinstance(item, dict):
            blockers.append("analysis_resource_lock_evidence_registry_entry_invalid")
            continue
        resource_id = str(item.get("resource_id") or "")
        evidence_path = str(item.get("evidence_path") or "")
        if not resource_id:
            blockers.append("analysis_resource_lock_evidence_registry_resource_id_missing")
            continue
        if resource_id in seen:
            blockers.append(f"analysis_resource_lock_evidence_registry_duplicate:{resource_id}")
        seen.add(resource_id)
        registered_resource_ids.append(resource_id)
        if not evidence_path:
            blockers.append(f"analysis_resource_lock_evidence_registry_evidence_path_missing:{resource_id}")
            continue
        full_path = REPO_ROOT / evidence_path
        if not full_path.is_file():
            blockers.append(f"analysis_resource_lock_evidence_registry_evidence_not_found:{resource_id}:{evidence_path}")
            continue
        try:
            evidence = json.loads(full_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            blockers.append(f"analysis_resource_lock_evidence_registry_evidence_invalid_json:{resource_id}:{evidence_path}")
            continue
        validation = validate_analysis_resource_lock_evidence(resource_id, evidence, manifest=manifest_payload)
        blockers.extend(
            f"analysis_resource_lock_evidence_registry:{resource_id}:{blocker}"
            for blocker in validation.get("blockers", [])
        )
        warnings.extend(
            f"analysis_resource_lock_evidence_registry:{resource_id}:{warning}"
            for warning in validation.get("warnings", [])
        )

    return {
        "schema_version": "biomedpilot.analysis.resource_lock_evidence_registry_validation.v1",
        "status": "blocked" if blockers else "passed",
        "entry_count": len(entries),
        "registered_resource_ids": registered_resource_ids,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def validate_analysis_environment_lock_evidence(
    environment_id: str,
    evidence: dict[str, Any],
    *,
    environment_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate evidence before an isolated analysis environment can be restored."""

    payload = environment_registry or load_analysis_environment_registry()
    environments = {
        str(item.get("environment_id") or ""): item
        for item in payload.get("environments", [])
        if isinstance(item, dict) and item.get("environment_id")
    }
    blockers: list[str] = []
    warnings: list[str] = []
    blockers.extend(_environment_lock_evidence_schema_blockers(evidence))
    environment_key = str(environment_id or evidence.get("environment_id") or "")
    environment = environments.get(environment_key)
    if environment is None:
        blockers.append(f"analysis_environment_lock_evidence_environment_unregistered:{environment_key}")
    if str(evidence.get("environment_id") or environment_key) != environment_key:
        blockers.append("analysis_environment_lock_evidence_environment_id_mismatch")

    status = str(evidence.get("status") or "")
    if status not in RESTORED_LOCK_STATUSES:
        blockers.append("analysis_environment_lock_evidence_status_not_restored")
    if evidence.get("runtime_package_install") != "forbidden":
        blockers.append("analysis_environment_lock_evidence_runtime_install_not_forbidden")
    if evidence.get("runtime_resource_download") != "forbidden":
        blockers.append("analysis_environment_lock_evidence_runtime_download_not_forbidden")

    package_hash = evidence.get("package_lock_hash")
    package_hash_algorithm = ""
    package_hash_value = ""
    if not isinstance(package_hash, dict):
        blockers.append("analysis_environment_lock_evidence_package_lock_hash_invalid")
    else:
        package_hash_algorithm = str(package_hash.get("algorithm") or "")
        package_hash_value = str(package_hash.get("value") or "")
        if not package_hash_algorithm:
            blockers.append("analysis_environment_lock_evidence_package_lock_hash_algorithm_missing")
        elif package_hash_algorithm != "sha256":
            blockers.append("analysis_environment_lock_evidence_package_lock_hash_algorithm_not_sha256")
        if _is_placeholder_resource_value(package_hash_value):
            blockers.append("analysis_environment_lock_evidence_package_lock_hash_value_missing")
        elif package_hash_algorithm == "sha256" and not _is_sha256_hex(package_hash_value):
            blockers.append("analysis_environment_lock_evidence_package_lock_hash_value_not_sha256")

    for field in ("r_version", "bioconductor_version", "dockerfile", "renv_lock"):
        if _is_placeholder_resource_value(evidence.get(field)):
            blockers.append(f"analysis_environment_lock_evidence_placeholder_field:{field}")

    dockerfile = str(evidence.get("dockerfile") or "")
    renv_lock = str(evidence.get("renv_lock") or "")
    if dockerfile and not (REPO_ROOT / dockerfile).is_file():
        blockers.append(f"analysis_environment_lock_evidence_dockerfile_not_found:{dockerfile}")
    if renv_lock and not (REPO_ROOT / renv_lock).is_file():
        blockers.append(f"analysis_environment_lock_evidence_renv_lock_not_found:{renv_lock}")
    elif renv_lock and package_hash_algorithm == "sha256" and _is_sha256_hex(package_hash_value):
        actual_hash = _sha256_file(REPO_ROOT / renv_lock)
        if actual_hash != package_hash_value.lower():
            blockers.append("analysis_environment_lock_evidence_package_lock_hash_mismatch")

    evidence_files = evidence.get("evidence_files")
    if not isinstance(evidence_files, list) or not evidence_files:
        blockers.append("analysis_environment_lock_evidence_files_missing")
    else:
        for item in evidence_files:
            evidence_file = str(item or "")
            if not evidence_file:
                blockers.append("analysis_environment_lock_evidence_file_invalid")
            elif not (REPO_ROOT / evidence_file).is_file():
                blockers.append(f"analysis_environment_lock_evidence_file_not_found:{evidence_file}")

    allowed_modules = evidence.get("allowed_module_ids")
    allowed = {str(item) for item in allowed_modules if item is not None} if isinstance(allowed_modules, list) else set()
    if environment_key != "app-dev" and not allowed:
        blockers.append("analysis_environment_lock_evidence_allowed_modules_missing")
    if environment is not None:
        expected_allowed = {
            str(item)
            for item in environment.get("allowed_module_ids", [])
            if item is not None
        }
        if allowed != expected_allowed:
            blockers.append("analysis_environment_lock_evidence_allowed_modules_mismatch")
        for field in ("dockerfile", "renv_lock"):
            if str(evidence.get(field) or "") != str(environment.get(field) or ""):
                blockers.append(f"analysis_environment_lock_evidence_registry_field_mismatch:{field}")
        r_runtime = str(environment.get("r_runtime") or "")
        if r_runtime != "not_required" and str(evidence.get("r_version") or "") != r_runtime:
            blockers.append("analysis_environment_lock_evidence_registry_field_mismatch:r_version")

    return {
        "schema_version": "biomedpilot.analysis.environment_lock_evidence_validation.v1",
        "status": "blocked" if blockers else "passed",
        "environment_id": environment_key,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": warnings,
    }


def validate_analysis_environment_lock_evidence_registry(
    registry: dict[str, Any] | None = None,
    *,
    environment_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the authoritative registry for restored full environment evidence."""

    payload = registry if isinstance(registry, dict) else load_analysis_environment_lock_evidence_registry()
    environment_payload = environment_registry or load_analysis_environment_registry()
    blockers: list[str] = []
    warnings: list[str] = []
    blockers.extend(_environment_lock_evidence_registry_schema_blockers(payload))
    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    if not policy:
        blockers.append("analysis_environment_lock_evidence_registry_policy_missing")
    else:
        if policy.get("registry_is_authoritative") is not True:
            blockers.append("analysis_environment_lock_evidence_registry_authoritative_policy_invalid")
        if policy.get("restored_full_environment_requires_schema_valid_evidence") is not True:
            blockers.append("analysis_environment_lock_evidence_registry_restored_policy_invalid")
        if policy.get("runtime_package_install") != "forbidden":
            blockers.append("analysis_environment_lock_evidence_registry_runtime_install_policy_invalid")
        if policy.get("runtime_resource_download") != "forbidden":
            blockers.append("analysis_environment_lock_evidence_registry_runtime_download_policy_invalid")

    entries = payload.get("evidence_entries")
    if not isinstance(entries, list):
        blockers.append("analysis_environment_lock_evidence_registry_entries_invalid")
        entries = []
    seen: set[str] = set()
    registered_environment_ids: list[str] = []
    for item in entries:
        if not isinstance(item, dict):
            blockers.append("analysis_environment_lock_evidence_registry_entry_invalid")
            continue
        environment_id = str(item.get("environment_id") or "")
        evidence_path = str(item.get("evidence_path") or "")
        if not environment_id:
            blockers.append("analysis_environment_lock_evidence_registry_environment_id_missing")
            continue
        if environment_id in seen:
            blockers.append(f"analysis_environment_lock_evidence_registry_duplicate:{environment_id}")
        seen.add(environment_id)
        registered_environment_ids.append(environment_id)
        if not evidence_path:
            blockers.append(f"analysis_environment_lock_evidence_registry_evidence_path_missing:{environment_id}")
            continue
        full_path = REPO_ROOT / evidence_path
        if not full_path.is_file():
            blockers.append(f"analysis_environment_lock_evidence_registry_evidence_not_found:{environment_id}:{evidence_path}")
            continue
        try:
            evidence = json.loads(full_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            blockers.append(f"analysis_environment_lock_evidence_registry_evidence_invalid_json:{environment_id}:{evidence_path}")
            continue
        validation = validate_analysis_environment_lock_evidence(
            environment_id,
            evidence,
            environment_registry=environment_payload,
        )
        blockers.extend(
            f"analysis_environment_lock_evidence_registry:{environment_id}:{blocker}"
            for blocker in validation.get("blockers", [])
        )
        warnings.extend(
            f"analysis_environment_lock_evidence_registry:{environment_id}:{warning}"
            for warning in validation.get("warnings", [])
        )

    return {
        "schema_version": "biomedpilot.analysis.environment_lock_evidence_registry_validation.v1",
        "status": "blocked" if blockers else "passed",
        "entry_count": len(entries),
        "registered_environment_ids": registered_environment_ids,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def validate_analysis_environment_registry(
    environment_registry: dict[str, Any] | None = None,
    *,
    module_registry: dict[str, Any] | None = None,
    environment_lock_evidence_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the environment split without claiming full readiness.

    Structural blockers mean the registry cannot be trusted. Readiness blockers
    mean the registry is structurally usable but full analysis must remain
    disabled until the isolated environment locks are restored.
    """

    environment_payload = environment_registry or load_analysis_environment_registry()
    evidence_registry = (
        environment_lock_evidence_registry
        if isinstance(environment_lock_evidence_registry, dict)
        else load_analysis_environment_lock_evidence_registry()
    )
    module_payload = module_registry or json.loads(MODULE_REGISTRY_PATH.read_text(encoding="utf-8"))
    blockers: list[str] = []
    readiness_blockers: list[str] = []
    warnings: list[str] = []
    evidence_registry_validation = validate_analysis_environment_lock_evidence_registry(
        evidence_registry,
        environment_registry=environment_payload,
    )
    blockers.extend(
        f"analysis_environment_lock_evidence_registry:{blocker}"
        for blocker in evidence_registry_validation.get("blockers", [])
    )
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
        blockers.extend(_environment_file_policy_blockers(item, environment_id, evidence_registry=evidence_registry, environment_registry=environment_payload))
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
        "environment_lock_evidence_templates": _environment_lock_evidence_templates(environments),
        "evidence_registry_status": evidence_registry_validation.get("status"),
        "evidence_registry_entry_count": evidence_registry_validation.get("entry_count"),
        "blockers": list(dict.fromkeys(blockers)),
        "readiness_blockers": list(dict.fromkeys(readiness_blockers)),
        "warnings": warnings,
    }


def _is_placeholder_resource_value(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text.lower() in PLACEHOLDER_RESOURCE_VALUES


def _resource_hash_algorithm_allowed(resource_id: str, algorithm: str) -> bool:
    if resource_id == MOCK_FIXTURE_RESOURCE_ID:
        return algorithm in {"repository_fixture", "sha256"}
    return algorithm == "sha256"


def _is_sha256_hex(value: str) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(char in "0123456789abcdefABCDEF" for char in text)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_path(path: Path) -> str:
    if path.is_file():
        return _sha256_file(path)
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        relative = child.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with child.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def _blocked_resource_has_partial_final_lock(item: dict[str, Any]) -> bool:
    return any(not _is_placeholder_resource_value(item.get(field)) for field in FINAL_LOCK_REQUIRED_FIELDS)


def _resource_lock_evidence_templates(resources: list[Any]) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    for item in resources:
        if not isinstance(item, dict):
            continue
        resource_id = str(item.get("resource_id") or "")
        if not resource_id or str(item.get("status") or "") == "locked":
            continue
        templates.append(
            {
                "schema_version": "biomedpilot.analysis.resource_lock_evidence.v1",
                "resource_id": resource_id,
                "status": "locked",
                "version": str(item.get("version") or "<version>"),
                "source": str(item.get("source") or "<source>"),
                "hash": {
                    "algorithm": "sha256",
                    "value": str(item.get("hash") or "<sha256>"),
                },
                "license": str(item.get("license") or "<license>"),
                "cache_path": str(item.get("cache_path") or "external_analysis_resources/cache/<resource_id>"),
                "runtime_download_allowed": False,
                "approved_for_modules": [str(value) for value in item.get("required_for_modules", []) if value is not None],
                "evidence_files": [
                    "external_analysis_resources/evidence/<resource_id>.json",
                    "external_analysis_resources/logs/<resource_id>.log",
                ],
                "registry_entry": {
                    "resource_id": resource_id,
                    "evidence_path": "analysis/resources/locks/<resource_id>.lock.json",
                },
                "forbidden_evidence_sources": [
                    "runtime_download",
                    "user_request_download",
                    "placeholder_hash",
                    "unlicensed_cache",
                ],
            }
        )
    return templates


def _environment_lock_evidence_templates(environments: list[Any]) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    for item in environments:
        if not isinstance(item, dict):
            continue
        environment_id = str(item.get("environment_id") or "")
        if environment_id in {"", "app-dev", "r-bio-core"}:
            continue
        templates.append(
            {
                "schema_version": "biomedpilot.analysis.environment_lock_evidence.v1",
                "environment_id": environment_id,
                "status": "restored",
                "r_version": str(item.get("r_runtime") or "<R version>"),
                "bioconductor_version": "<Bioconductor version>",
                "package_lock_hash": {
                    "algorithm": "sha256",
                    "value": "<renv lock sha256>",
                },
                "dockerfile": str(item.get("dockerfile") or "docker/Dockerfile.<environment>"),
                "renv_lock": str(item.get("renv_lock") or "renv/renv.<environment>.lock"),
                "runtime_package_install": "forbidden",
                "runtime_resource_download": "forbidden",
                "allowed_module_ids": [str(value) for value in item.get("allowed_module_ids", []) if value is not None],
                "evidence_files": [
                    "external_analysis_environments/evidence/<environment_id>.json",
                    "external_analysis_environments/logs/<environment_id>.log",
                ],
                "registry_entry": {
                    "environment_id": environment_id,
                    "evidence_path": "external_analysis_environments/evidence/<environment_id>.json",
                },
                "forbidden_evidence_sources": [
                    "default_app_dev_environment",
                    "runtime_package_install",
                    "runtime_resource_download",
                    "scaffold_only_lockfile",
                ],
            }
        )
    return templates


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


def _resource_lock_evidence_registry_schema_blockers(payload: dict[str, Any]) -> list[str]:
    schema = _read_json(RESOURCE_LOCK_EVIDENCE_REGISTRY_SCHEMA_PATH)
    blockers: list[str] = []
    required = schema.get("required") if isinstance(schema.get("required"), list) else []
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for field in required:
        if isinstance(field, str) and field not in payload:
            blockers.append(f"analysis_resource_lock_evidence_registry_required_field_missing:{field}")
    for field, field_schema in properties.items():
        if not isinstance(field, str) or field not in payload or not isinstance(field_schema, dict):
            continue
        value = payload[field]
        if "const" in field_schema and value != field_schema["const"]:
            blockers.append(f"analysis_resource_lock_evidence_registry_const_mismatch:{field}")
        expected_type = field_schema.get("type")
        if isinstance(expected_type, str) and not _schema_type_matches(value, expected_type):
            blockers.append(f"analysis_resource_lock_evidence_registry_type_invalid:{field}")
    return blockers


def _environment_lock_evidence_schema_blockers(evidence: dict[str, Any]) -> list[str]:
    schema = _read_json(ENVIRONMENT_LOCK_EVIDENCE_SCHEMA_PATH)
    blockers: list[str] = []
    required = schema.get("required") if isinstance(schema.get("required"), list) else []
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for field in required:
        if isinstance(field, str) and field not in evidence:
            blockers.append(f"analysis_environment_lock_evidence_required_field_missing:{field}")
    for field, field_schema in properties.items():
        if not isinstance(field, str) or field not in evidence or not isinstance(field_schema, dict):
            continue
        value = evidence[field]
        if "const" in field_schema and value != field_schema["const"]:
            blockers.append(f"analysis_environment_lock_evidence_const_mismatch:{field}")
        expected_type = field_schema.get("type")
        if isinstance(expected_type, str) and not _schema_type_matches(value, expected_type):
            blockers.append(f"analysis_environment_lock_evidence_type_invalid:{field}")
            continue
        min_length = field_schema.get("minLength")
        if isinstance(min_length, int) and isinstance(value, str) and len(value) < min_length:
            blockers.append(f"analysis_environment_lock_evidence_min_length_invalid:{field}")
    return blockers


def _environment_lock_evidence_registry_schema_blockers(payload: dict[str, Any]) -> list[str]:
    schema = _read_json(ENVIRONMENT_LOCK_EVIDENCE_REGISTRY_SCHEMA_PATH)
    blockers: list[str] = []
    required = schema.get("required") if isinstance(schema.get("required"), list) else []
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for field in required:
        if isinstance(field, str) and field not in payload:
            blockers.append(f"analysis_environment_lock_evidence_registry_required_field_missing:{field}")
    for field, field_schema in properties.items():
        if not isinstance(field, str) or field not in payload or not isinstance(field_schema, dict):
            continue
        value = payload[field]
        if "const" in field_schema and value != field_schema["const"]:
            blockers.append(f"analysis_environment_lock_evidence_registry_const_mismatch:{field}")
        expected_type = field_schema.get("type")
        if isinstance(expected_type, str) and not _schema_type_matches(value, expected_type):
            blockers.append(f"analysis_environment_lock_evidence_registry_type_invalid:{field}")
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


def _environment_file_policy_blockers(
    environment: dict[str, Any],
    environment_id: str,
    *,
    evidence_registry: dict[str, Any] | None = None,
    environment_registry: dict[str, Any] | None = None,
) -> list[str]:
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
            blockers.extend(
                _environment_lock_evidence_blockers(
                    environment_id,
                    policy,
                    environment_registry=environment_registry,
                    evidence_registry=evidence_registry,
                )
            )
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


def _resource_lock_evidence_path_from_registry(resource_id: str, evidence_registry: dict[str, Any]) -> str:
    entries = evidence_registry.get("evidence_entries") if isinstance(evidence_registry, dict) else []
    if not isinstance(entries, list):
        return ""
    for item in entries:
        if isinstance(item, dict) and str(item.get("resource_id") or "") == resource_id:
            return str(item.get("evidence_path") or "")
    return ""


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
    environment_lock_evidence_registry: dict[str, Any] | None = None,
) -> list[str]:
    """Return blockers proving full mode is isolated and lock-restored.

    Full analysis must not become runnable merely because resources are locked.
    The module must also target an isolated registered environment with an
    existing Dockerfile and a restored renv/tool lock.
    """

    module_payload = module_registry or json.loads(MODULE_REGISTRY_PATH.read_text(encoding="utf-8"))
    environment_payload = environment_registry or load_analysis_environment_registry()
    evidence_registry = (
        environment_lock_evidence_registry
        if isinstance(environment_lock_evidence_registry, dict)
        else load_analysis_environment_lock_evidence_registry()
    )
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
    blockers.extend(
        _renv_lock_environment_blockers(
            environment_id,
            lockfile,
            evidence_registry=evidence_registry,
            environment_registry=environment_payload,
        )
    )
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


def _renv_lock_environment_blockers(
    environment_id: str,
    lockfile: str,
    *,
    evidence_registry: dict[str, Any] | None = None,
    environment_registry: dict[str, Any] | None = None,
) -> list[str]:
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
    blockers.extend(
        _environment_lock_evidence_blockers(
            environment_id,
            policy,
            environment_registry=environment_registry,
            evidence_registry=evidence_registry,
        )
    )
    return blockers


def _environment_lock_evidence_blockers(
    environment_id: str,
    policy: dict[str, Any],
    *,
    environment_registry: dict[str, Any] | None,
    evidence_registry: dict[str, Any] | None = None,
) -> list[str]:
    status = str(policy.get("status") or "missing")
    if status not in RESTORED_LOCK_STATUSES:
        return []
    evidence_path = str(policy.get("lock_evidence") or "")
    if not evidence_path and isinstance(evidence_registry, dict):
        entries = evidence_registry.get("evidence_entries")
        if isinstance(entries, list):
            for item in entries:
                if isinstance(item, dict) and str(item.get("environment_id") or "") == environment_id:
                    evidence_path = str(item.get("evidence_path") or "")
                    break
    if not evidence_path:
        return [f"analysis_environment_lock_evidence_missing:{environment_id}"]
    full_path = REPO_ROOT / evidence_path
    if not full_path.is_file():
        return [f"analysis_environment_lock_evidence_not_found:{environment_id}:{evidence_path}"]
    try:
        evidence = json.loads(full_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [f"analysis_environment_lock_evidence_invalid_json:{environment_id}:{evidence_path}"]
    validation = validate_analysis_environment_lock_evidence(environment_id, evidence, environment_registry=environment_registry)
    return [
        f"analysis_environment_lock_evidence:{environment_id}:{blocker}"
        for blocker in validation.get("blockers", [])
    ]
