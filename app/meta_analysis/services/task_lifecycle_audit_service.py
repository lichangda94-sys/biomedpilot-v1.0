from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.shared.task_center.service import TaskRecord


@dataclass(frozen=True)
class TaskLifecycleAuditEvent:
    event_id: str
    task_id: str
    project_id: str
    task_type: str
    from_status: str
    to_status: str
    actor: str
    reason: str
    created_at: str
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskLifecycleAuditSummary:
    project_id: str
    event_count: int
    task_count: int
    status_transition_counts: dict[str, int]
    latest_event: TaskLifecycleAuditEvent | None = None


class TaskLifecycleAuditService:
    def __init__(self, *, audit_log: MetaAuditLogService | None = None) -> None:
        self._audit_log = audit_log or MetaAuditLogService()

    def audit_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "audit" / "task_lifecycle_log.jsonl"

    def record_transition(
        self,
        project_dir: Path,
        *,
        before: TaskRecord | None,
        after: TaskRecord,
        actor: str = "system",
        reason: str = "",
        details: dict[str, object] | None = None,
    ) -> TaskLifecycleAuditEvent:
        project_dir = project_dir.expanduser().resolve()
        path = self.audit_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        event = TaskLifecycleAuditEvent(
            event_id=f"tlife-{uuid4().hex[:12]}",
            task_id=after.task_id,
            project_id=after.project_id or project_dir.name,
            task_type=after.task_type.value,
            from_status=before.status.value if before is not None else "",
            to_status=after.status.value,
            actor=actor,
            reason=reason,
            details=dict(details or {}),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")
        self._audit_log.record_event(
            project_dir,
            event_type="task_lifecycle_changed",
            project_id=event.project_id,
            actor=actor,
            target_type="task",
            target_id=after.task_id,
            summary=f"Task lifecycle changed: {event.from_status or 'new'} -> {event.to_status}.",
            details={
                "task_type": event.task_type,
                "from_status": event.from_status,
                "to_status": event.to_status,
                "reason": reason,
                **dict(details or {}),
            },
        )
        return event

    def list_events(self, project_dir: Path) -> list[TaskLifecycleAuditEvent]:
        path = self.audit_path(project_dir)
        if not path.exists():
            return []
        events: list[TaskLifecycleAuditEvent] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            events.append(
                TaskLifecycleAuditEvent(
                    event_id=str(payload.get("event_id", "")),
                    task_id=str(payload.get("task_id", "")),
                    project_id=str(payload.get("project_id", "")),
                    task_type=str(payload.get("task_type", "")),
                    from_status=str(payload.get("from_status", "")),
                    to_status=str(payload.get("to_status", "")),
                    actor=str(payload.get("actor", "")),
                    reason=str(payload.get("reason", "")),
                    created_at=str(payload.get("created_at", "")),
                    details=dict(payload.get("details", {})),
                )
            )
        return events

    def summarize(self, project_dir: Path) -> TaskLifecycleAuditSummary:
        events = self.list_events(project_dir)
        transition_counts: dict[str, int] = {}
        task_ids: set[str] = set()
        for event in events:
            task_ids.add(event.task_id)
            key = f"{event.from_status or 'new'}->{event.to_status}"
            transition_counts[key] = transition_counts.get(key, 0) + 1
        return TaskLifecycleAuditSummary(
            project_id=project_dir.expanduser().resolve().name,
            event_count=len(events),
            task_count=len(task_ids),
            status_transition_counts=transition_counts,
            latest_event=events[-1] if events else None,
        )
