from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


RESULT_INDEX_SCHEMA_VERSION = "biomedpilot.result_index.v2"
RESULT_ENTRY_SCHEMA_VERSION = "biomedpilot.result_index_entry.v1"
RESULT_SEMANTICS = {
    "preflight_only",
    "testing_level",
    "exploratory",
    "formal_computed_result",
    "imported_external_result",
    "configured_not_run",
    "failed",
    "blocked",
}


@dataclass(frozen=True)
class ResultIndexEntry:
    result_id: str
    task_run_id: str
    task_type: str
    result_semantics: str
    input_package_id: str = ""
    source_dataset_id: str = ""
    source_repository_manifest: str = ""
    parameters_manifest: dict[str, Any] = field(default_factory=dict)
    engine_name: str = ""
    engine_version: str = ""
    dependency_snapshot: dict[str, Any] = field(default_factory=dict)
    output_artifacts: tuple[dict[str, Any], ...] = ()
    plot_artifacts: tuple[dict[str, Any], ...] = ()
    report_artifacts: tuple[dict[str, Any], ...] = ()
    validation_status: str = "not_validated"
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    log_artifacts: tuple[dict[str, Any], ...] = ()
    failure_reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    schema_version: str = RESULT_ENTRY_SCHEMA_VERSION
    report_ready_eligible: bool = False
    migration_status: str = "native_v2"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["output_artifacts"] = [dict(item) for item in self.output_artifacts]
        payload["plot_artifacts"] = [dict(item) for item in self.plot_artifacts]
        payload["report_artifacts"] = [dict(item) for item in self.report_artifacts]
        payload["warnings"] = list(self.warnings)
        payload["blockers"] = list(self.blockers)
        payload["log_artifacts"] = [dict(item) for item in self.log_artifacts]
        return payload


def normalize_result_semantics(value: object, *, default: str = "testing_level") -> str:
    text = str(value or "").strip()
    aliases = {
        "imported": "imported_external_result",
        "imported result": "imported_external_result",
        "dry-run": "configured_not_run",
        "dry_run": "configured_not_run",
        "real computed result": "formal_computed_result",
        "formal": "formal_computed_result",
        "preflight-only": "preflight_only",
    }
    normalized = aliases.get(text, text)
    if normalized in RESULT_SEMANTICS:
        return normalized
    return default
