"""Core infrastructure shared across the desktop application."""

from core.task_management import TaskManagementService
from core.task_models import (
    TaskPlanRecord,
    TaskPlanState,
    TaskRecord,
    TaskResultArtifactDiagnostic,
    TaskResultArtifactStatus,
    TaskResultRecord,
    TaskResultState,
)
from core.task_status import TaskState, TaskStatus
from core.task_store import TaskRecordStore, TaskStatusStore

__all__ = [
    "TaskManagementService",
    "TaskPlanRecord",
    "TaskPlanState",
    "TaskRecord",
    "TaskRecordStore",
    "TaskResultArtifactDiagnostic",
    "TaskResultArtifactStatus",
    "TaskResultRecord",
    "TaskResultState",
    "TaskState",
    "TaskStatus",
    "TaskStatusStore",
]
