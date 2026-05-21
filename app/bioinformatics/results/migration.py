from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import ResultIndexEntry, normalize_result_semantics


def migrate_legacy_result_entry(entry: dict[str, Any]) -> dict[str, Any]:
    result_id = str(entry.get("result_id") or entry.get("id") or entry.get("name") or f"legacy-result-{abs(hash(str(entry))) % 10**8}")
    task_type = str(entry.get("task_type") or entry.get("analysis_type") or "legacy_result")
    semantics = _legacy_semantics(entry)
    legacy_semantics = str(entry.get("result_semantics") or "")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    migrated = ResultIndexEntry(
        result_id=result_id,
        task_run_id=str(entry.get("task_run_id") or ""),
        task_type=task_type,
        result_semantics=legacy_semantics or semantics,
        input_package_id=str(entry.get("input_package_id") or ""),
        source_dataset_id=str(entry.get("source_dataset_id") or ""),
        source_repository_manifest=str(entry.get("source_repository_manifest") or ""),
        parameters_manifest=entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {},
        engine_name=str(entry.get("engine_name") or entry.get("statistical_engine") or ""),
        engine_version=str(entry.get("engine_version") or ""),
        dependency_snapshot=entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {},
        output_artifacts=_artifact_tuple(entry),
        validation_status=str(entry.get("validation_status") or "not_validated"),
        warnings=tuple(str(item) for item in entry.get("warnings", []) or []),
        blockers=tuple(str(item) for item in entry.get("blockers", []) or []),
        failure_reason=str(entry.get("failure_reason") or ""),
        created_at=str(entry.get("created_at") or entry.get("generated_at") or now),
        updated_at=str(entry.get("updated_at") or now),
        report_ready_eligible=False,
        migration_status="legacy_unverified" if semantics in {"testing_level", "imported_external_result"} else "migrated_conservative",
    )
    payload = {**entry, **migrated.to_dict()}
    for key, value in entry.items():
        if key not in payload or key in {"analysis_type", "result_name", "name", "path", "file_path", "file_type", "status", "report_candidate", "report_usage_label", "warning", "manifest_ref"}:
            payload[key] = value
    if legacy_semantics:
        payload["result_semantics"] = legacy_semantics
    payload["canonical_result_semantics"] = semantics
    return payload


def migrate_result_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [entry if entry.get("schema_version") == "biomedpilot.result_index_entry.v1" else migrate_legacy_result_entry(entry) for entry in entries]


def _legacy_semantics(entry: dict[str, Any]) -> str:
    raw = entry.get("result_semantics") or entry.get("semantics") or ""
    normalized = normalize_result_semantics(raw, default="")
    if normalized:
        return normalized
    task_type = str(entry.get("task_type") or entry.get("analysis_type") or "").lower()
    if "import" in task_type:
        return "imported_external_result"
    if entry.get("formal_deg_executed") is True and entry.get("dependency_snapshot") and entry.get("input_package_id"):
        return "formal_computed_result"
    if entry.get("status") in {"failed", "error"}:
        return "failed"
    return "testing_level"


def _artifact_tuple(entry: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    artifacts = entry.get("output_artifacts")
    if isinstance(artifacts, list):
        return tuple(dict(item) for item in artifacts if isinstance(item, dict))
    path = str(entry.get("path") or entry.get("file_path") or "")
    if path:
        return ({"artifact_type": "legacy_output", "path": path},)
    return ()
