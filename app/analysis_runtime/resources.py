from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import REPO_ROOT


RESOURCE_MANIFEST_PATH = REPO_ROOT / "analysis" / "resources" / "manifest.json"
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


def load_analysis_resource_manifest(path: str | Path | None = None) -> dict[str, Any]:
    manifest_path = Path(path).expanduser().resolve() if path else RESOURCE_MANIFEST_PATH
    return json.loads(manifest_path.read_text(encoding="utf-8"))


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
