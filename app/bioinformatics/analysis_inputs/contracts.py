from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


TASK_RUN_SCHEMA_VERSION = "biomedpilot.analysis_task_run.v1"
ALLOWED_TASK_RUN_STATUSES = {"not_run", "config_only", "preflight_only", "blocked"}
FORBIDDEN_B8_1_OUTPUT_SEMANTICS = {"formal_computed_result", "report_ready_result"}


@dataclass(frozen=True)
class AnalysisTaskRunManifest:
    task_run_id: str
    task_type: str
    input_package_id: str
    task_semantics: str = "config_only"
    parameters: dict[str, Any] = field(default_factory=dict)
    dependency_snapshot: dict[str, Any] = field(default_factory=dict)
    status: str = "not_run"
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    output_artifacts: tuple[dict[str, Any], ...] = ()
    result_index_entry: dict[str, Any] | None = None
    logs: tuple[dict[str, Any], ...] = ()
    failure_reason: str = ""
    schema_version: str = TASK_RUN_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["output_artifacts"] = [dict(item) for item in self.output_artifacts]
        payload["logs"] = [dict(item) for item in self.logs]
        return payload


def create_task_run_manifest(
    *,
    task_type: str,
    input_package_id: str,
    task_semantics: str = "config_only",
    parameters: dict[str, Any] | None = None,
    dependency_snapshot: dict[str, Any] | None = None,
    status: str = "not_run",
    blockers: list[str] | tuple[str, ...] | None = None,
    warnings: list[str] | tuple[str, ...] | None = None,
    task_run_id: str | None = None,
) -> AnalysisTaskRunManifest:
    normalized_blockers = tuple(str(item) for item in (blockers or ()) if str(item))
    normalized_status = "blocked" if normalized_blockers else status
    if normalized_status not in ALLOWED_TASK_RUN_STATUSES:
        normalized_status = "not_run"
    return AnalysisTaskRunManifest(
        task_run_id=task_run_id or f"task-run-{uuid4().hex[:12]}",
        task_type=task_type,
        input_package_id=input_package_id,
        task_semantics=task_semantics,
        parameters=parameters or {},
        dependency_snapshot=dependency_snapshot or {},
        status=normalized_status,
        blockers=normalized_blockers,
        warnings=tuple(str(item) for item in (warnings or ()) if str(item)),
    )


def validate_task_run_manifest(manifest: AnalysisTaskRunManifest | dict[str, Any]) -> dict[str, Any]:
    payload = manifest.to_dict() if isinstance(manifest, AnalysisTaskRunManifest) else dict(manifest)
    blockers: list[str] = []
    warnings: list[str] = []
    for field_name in (
        "task_run_id",
        "task_type",
        "input_package_id",
        "task_semantics",
        "parameters",
        "dependency_snapshot",
        "status",
        "blockers",
        "warnings",
        "created_at",
        "updated_at",
        "output_artifacts",
        "result_index_entry",
        "logs",
        "failure_reason",
        "schema_version",
    ):
        if field_name not in payload:
            blockers.append(f"missing_field:{field_name}")
    status = str(payload.get("status") or "")
    if status not in ALLOWED_TASK_RUN_STATUSES:
        blockers.append(f"invalid_status:{status}")
    semantics = str(payload.get("task_semantics") or "")
    if semantics in FORBIDDEN_B8_1_OUTPUT_SEMANTICS:
        blockers.append(f"forbidden_b8_1_semantics:{semantics}")
    if payload.get("output_artifacts"):
        warnings.append("b8_1_task_run_should_not_materialize_formal_outputs")
    return {"status": "blocked" if blockers else "passed", "blockers": blockers, "warnings": warnings}
