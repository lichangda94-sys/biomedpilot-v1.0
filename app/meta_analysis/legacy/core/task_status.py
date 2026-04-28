from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class TaskState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class TaskStatus:
    task_id: str
    state: TaskState = TaskState.PENDING
    message: str = ""
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def transition(self, state: TaskState, message: str = "") -> None:
        self.state = state
        self.message = message
        self.updated_at = datetime.now(timezone.utc)
