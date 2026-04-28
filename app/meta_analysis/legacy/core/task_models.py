from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from core.task_status import TaskState


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskResultState(StrEnum):
    AVAILABLE = "available"
    FAILED = "failed"


class TaskResultArtifactStatus(StrEnum):
    PRESENT = "present"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"


class TaskPlanState(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class TaskPlanMaterializationReason(StrEnum):
    READY = "ready"
    NOT_READY = "not_ready"
    DISABLED = "disabled"
    ARCHIVED = "archived"
    MISSING_REQUIRED_CONTEXT = "missing_required_context"


class TaskExecutionOutcomeStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    FAILED_CONTRACT_VALIDATION = "failed_contract_validation"


class TaskExecutionContractReason(StrEnum):
    READY = "ready"
    MISSING_TASK = "missing_task"
    MISSING_TASK_ID = "missing_task_id"
    MISSING_TASK_TYPE = "missing_task_type"
    VALIDATION_FAILED = "validation_failed"


@dataclass(slots=True)
class TaskRecord:
    task_id: str
    task_type: str
    title: str
    state: TaskState = TaskState.PENDING
    message: str = ""
    project_id: str | None = None
    source_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def transition(self, state: TaskState, message: str = "") -> None:
        self.state = state
        self.message = message
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "title": self.title,
            "state": self.state.value,
            "message": self.message,
            "project_id": self.project_id,
            "source_id": self.source_id,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskRecord":
        return cls(
            task_id=str(payload["task_id"]),
            task_type=str(payload["task_type"]),
            title=str(payload["title"]),
            state=TaskState(str(payload.get("state", TaskState.PENDING.value))),
            message=str(payload.get("message", "")),
            project_id=(
                str(payload["project_id"])
                if payload.get("project_id") is not None
                else None
            ),
            source_id=(
                str(payload["source_id"])
                if payload.get("source_id") is not None
                else None
            ),
            metadata=dict(payload.get("metadata", {})),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )


@dataclass(slots=True)
class TaskResultRecord:
    result_id: str
    task_id: str
    result_type: str
    state: TaskResultState = TaskResultState.AVAILABLE
    title: str = ""
    artifact_path: str = ""
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "task_id": self.task_id,
            "result_type": self.result_type,
            "state": self.state.value,
            "title": self.title,
            "artifact_path": self.artifact_path,
            "summary": self.summary,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskResultRecord":
        return cls(
            result_id=str(payload["result_id"]),
            task_id=str(payload["task_id"]),
            result_type=str(payload["result_type"]),
            state=TaskResultState(str(payload.get("state", TaskResultState.AVAILABLE.value))),
            title=str(payload.get("title", "")),
            artifact_path=str(payload.get("artifact_path", "")),
            summary=str(payload.get("summary", "")),
            metadata=dict(payload.get("metadata", {})),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
        )


@dataclass(slots=True)
class TaskResultArtifactDiagnostic:
    result_id: str
    result_type: str
    state: TaskResultState
    artifact_path: str
    artifact_status: TaskResultArtifactStatus

    def to_dict(self) -> dict[str, str]:
        return {
            "result_id": self.result_id,
            "result_type": self.result_type,
            "state": self.state.value,
            "artifact_path": self.artifact_path,
            "artifact_status": self.artifact_status.value,
        }


@dataclass(slots=True)
class ArtifactPreviewRecord:
    artifact_path: str
    exists: bool
    file_name: str = ""
    file_extension: str = ""
    size_bytes: int = 0
    preview_available: bool = False
    preview_text: str = ""
    message: str = ""
    error_code: str = ""

    def to_dict(self) -> dict[str, str | int | bool]:
        return {
            "artifact_path": self.artifact_path,
            "exists": self.exists,
            "file_name": self.file_name,
            "file_extension": self.file_extension,
            "size_bytes": self.size_bytes,
            "preview_available": self.preview_available,
            "preview_text": self.preview_text,
            "message": self.message,
            "error_code": self.error_code,
        }


@dataclass(slots=True)
class TaskResultDetailRecord:
    result_id: str
    result_type: str
    state: TaskResultState | None
    title: str = ""
    task_id: str = ""
    source_task_id: str = ""
    analysis_id: str = ""
    analysis_profile_id: str = ""
    project_id: str = ""
    artifact_path: str = ""
    artifact_status: TaskResultArtifactStatus = TaskResultArtifactStatus.NOT_APPLICABLE
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    message: str = ""
    error_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "result_type": self.result_type,
            "state": self.state.value if self.state is not None else "",
            "title": self.title,
            "task_id": self.task_id,
            "source_task_id": self.source_task_id,
            "analysis_id": self.analysis_id,
            "analysis_profile_id": self.analysis_profile_id,
            "project_id": self.project_id,
            "artifact_path": self.artifact_path,
            "artifact_status": self.artifact_status.value,
            "summary": self.summary,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
            "message": self.message,
            "error_code": self.error_code,
        }


@dataclass(slots=True)
class TaskPlanMaterializationDiagnostic:
    plan_id: str
    plan_type: str
    state: TaskPlanState
    can_materialize: bool
    reason_code: TaskPlanMaterializationReason
    reason: str

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "plan_id": self.plan_id,
            "plan_type": self.plan_type,
            "state": self.state.value,
            "can_materialize": self.can_materialize,
            "reason_code": self.reason_code.value,
            "reason": self.reason,
        }


@dataclass(slots=True)
class TaskExecutionRequest:
    task_id: str
    task_type: str
    source_plan_id: str | None = None
    analysis_id: str | None = None
    analysis_profile_id: str | None = None
    project_id: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    requested_by: str = ""
    dry_run: bool = True
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "source_plan_id": self.source_plan_id,
            "analysis_id": self.analysis_id,
            "analysis_profile_id": self.analysis_profile_id,
            "project_id": self.project_id,
            "parameters": dict(self.parameters),
            "requested_by": self.requested_by,
            "dry_run": self.dry_run,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(slots=True)
class TaskExecutionOutcome:
    task_id: str
    accepted: bool
    status: TaskExecutionOutcomeStatus
    message: str = ""
    result_id: str | None = None
    error_code: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "accepted": self.accepted,
            "status": self.status.value,
            "message": self.message,
            "result_id": self.result_id,
            "error_code": self.error_code,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class TaskExecutionLogRecord:
    log_id: str
    task_id: str
    source_plan_id: str | None = None
    runner_type: str = ""
    task_type: str = ""
    dry_run: bool = True
    outcome_status: str = ""
    message: str = ""
    error_code: str = ""
    result_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "log_id": self.log_id,
            "task_id": self.task_id,
            "source_plan_id": self.source_plan_id,
            "runner_type": self.runner_type,
            "task_type": self.task_type,
            "dry_run": self.dry_run,
            "outcome_status": self.outcome_status,
            "message": self.message,
            "error_code": self.error_code,
            "result_id": self.result_id,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskExecutionLogRecord":
        return cls(
            log_id=str(payload["log_id"]),
            task_id=str(payload["task_id"]),
            source_plan_id=(
                str(payload["source_plan_id"])
                if payload.get("source_plan_id") is not None
                else None
            ),
            runner_type=str(payload.get("runner_type", "")),
            task_type=str(payload.get("task_type", "")),
            dry_run=bool(payload.get("dry_run", True)),
            outcome_status=str(payload.get("outcome_status", "")),
            message=str(payload.get("message", "")),
            error_code=str(payload.get("error_code", "")),
            result_id=(
                str(payload["result_id"])
                if payload.get("result_id") is not None
                else None
            ),
            metadata=dict(payload.get("metadata", {})),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
        )


@dataclass(slots=True)
class TaskExecutionContractDiagnostic:
    task_id: str
    task_type: str
    can_build_request: bool
    contract_valid: bool
    reason_code: TaskExecutionContractReason
    reason: str

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "can_build_request": self.can_build_request,
            "contract_valid": self.contract_valid,
            "reason_code": self.reason_code.value,
            "reason": self.reason,
        }


@dataclass(slots=True)
class TaskPlanRecord:
    plan_id: str
    title: str
    plan_type: str
    state: TaskPlanState = TaskPlanState.DRAFT
    analysis_id: str | None = None
    analysis_profile_id: str | None = None
    project_id: str | None = None
    requested_by: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def transition(self, state: TaskPlanState) -> None:
        self.state = state
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "plan_type": self.plan_type,
            "state": self.state.value,
            "analysis_id": self.analysis_id,
            "analysis_profile_id": self.analysis_profile_id,
            "project_id": self.project_id,
            "requested_by": self.requested_by,
            "parameters": dict(self.parameters),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskPlanRecord":
        return cls(
            plan_id=str(payload["plan_id"]),
            title=str(payload["title"]),
            plan_type=str(payload["plan_type"]),
            state=TaskPlanState(str(payload.get("state", TaskPlanState.DRAFT.value))),
            analysis_id=(
                str(payload["analysis_id"])
                if payload.get("analysis_id") is not None
                else None
            ),
            analysis_profile_id=(
                str(payload["analysis_profile_id"])
                if payload.get("analysis_profile_id") is not None
                else None
            ),
            project_id=(
                str(payload["project_id"])
                if payload.get("project_id") is not None
                else None
            ),
            requested_by=str(payload.get("requested_by", "")),
            parameters=dict(payload.get("parameters", {})),
            notes=str(payload.get("notes", "")),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )
