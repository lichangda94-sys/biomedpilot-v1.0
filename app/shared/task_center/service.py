from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

from app.shared.storage import default_storage_root


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(StrEnum):
    DOWNLOAD = "download"
    IMPORT = "import"
    LITERATURE_IMPORT = "literature_import"
    PREPARE_SCREENING = "prepare_screening"
    DUPLICATE_REVIEW = "duplicate_review"
    SCREENING = "screening"
    SCREENING_DECISION = "screening_decision"
    EXTRACTION = "extraction"
    PREPROCESS = "preprocess"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    REPORT_EXPORT = "report_export"


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    task_type: TaskType
    status: TaskStatus
    module: str
    title: str
    created_at: str
    updated_at: str
    project_id: str = ""
    started_at: str = ""
    finished_at: str = ""
    summary: str = ""
    error_message: str = ""

    def display_label(self) -> str:
        return f"{self.title} · {self.task_type.value} · {self.status.value}"


class TaskCenter:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def default(cls) -> "TaskCenter":
        return cls(default_storage_root() / "tasks" / "tasks.json")

    def register_task(
        self,
        task_id: str,
        task_type: TaskType,
        module: str,
        title: str,
        *,
        project_id: str = "",
        status: TaskStatus = TaskStatus.PENDING,
        started_at: str = "",
        finished_at: str = "",
        summary: str = "",
        error_message: str = "",
    ) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        record = TaskRecord(
            task_id=task_id,
            task_type=task_type,
            status=status,
            module=module,
            title=title,
            created_at=now,
            updated_at=now,
            project_id=project_id,
            started_at=started_at,
            finished_at=finished_at,
            summary=summary,
            error_message=error_message,
        )
        records = self.list_tasks(limit=None)
        records.insert(0, record)
        self._write(records)
        return record

    def save_task(self, record: TaskRecord) -> TaskRecord:
        records = [existing for existing in self.list_tasks(limit=None) if existing.task_id != record.task_id]
        records.insert(0, record)
        self._write(records)
        return record

    def list_tasks(self, limit: int | None = None) -> list[TaskRecord]:
        if not self.storage_path.exists():
            return []
        payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
        records = [
            TaskRecord(
                task_id=item["task_id"],
                task_type=TaskType(item["task_type"]),
                status=TaskStatus(item["status"]),
                module=item["module"],
                title=item["title"],
                created_at=item["created_at"],
                updated_at=item["updated_at"],
                project_id=item.get("project_id", ""),
                started_at=item.get("started_at", ""),
                finished_at=item.get("finished_at", ""),
                summary=item.get("summary", ""),
                error_message=item.get("error_message", ""),
            )
            for item in payload.get("tasks", [])
        ]
        return records if limit is None else records[:limit]

    def _write(self, records: list[TaskRecord]) -> None:
        payload = {"tasks": [asdict(record) for record in records]}
        self.storage_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
