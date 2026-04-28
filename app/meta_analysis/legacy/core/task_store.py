from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path

from core.task_models import (
    TaskExecutionLogRecord,
    TaskPlanRecord,
    TaskPlanState,
    TaskRecord,
    TaskResultRecord,
)
from core.task_status import TaskState, TaskStatus


class TaskStatusStore:
    def __init__(self, state_dir: Path) -> None:
        self._state_dir = state_dir
        self._state_file = state_dir / "task_status.json"

    @property
    def state_file(self) -> Path:
        return self._state_file

    def save(self, status: TaskStatus) -> Path:
        self._state_dir.mkdir(parents=True, exist_ok=True)
        payload = asdict(status)
        payload["state"] = status.state.value
        payload["updated_at"] = status.updated_at.isoformat()
        self._state_file.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        return self._state_file

    def load(self) -> TaskStatus | None:
        if not self._state_file.exists():
            return None

        payload = json.loads(self._state_file.read_text(encoding="utf-8"))
        return TaskStatus(
            task_id=payload["task_id"],
            state=TaskState(payload["state"]),
            message=payload.get("message", ""),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
            metadata=payload.get("metadata", {}),
        )


class TaskRecordStore:
    def __init__(self, state_dir: Path) -> None:
        self._state_dir = state_dir
        self._tasks_file = state_dir / "tasks.json"
        self._results_file = state_dir / "task_results.json"
        self._plans_file = state_dir / "task_plans.json"
        self._execution_logs_file = state_dir / "task_execution_logs.json"

    @property
    def tasks_file(self) -> Path:
        return self._tasks_file

    @property
    def results_file(self) -> Path:
        return self._results_file

    @property
    def plans_file(self) -> Path:
        return self._plans_file

    @property
    def execution_logs_file(self) -> Path:
        return self._execution_logs_file

    def list_tasks(
        self,
        *,
        project_id: str | None = None,
        state: TaskState | None = None,
    ) -> list[TaskRecord]:
        records = [TaskRecord.from_dict(item) for item in self._read_json(self._tasks_file)]
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        if state is not None:
            records = [record for record in records if record.state == state]
        return records

    def get_task(self, task_id: str) -> TaskRecord | None:
        for task in self.list_tasks():
            if task.task_id == task_id:
                return task
        return None

    def save_task(self, task: TaskRecord) -> TaskRecord:
        records = self.list_tasks()
        self._write_records(
            self._tasks_file,
            self._upsert_by_key(records, task, "task_id"),
        )
        return task

    def list_results(
        self,
        *,
        task_id: str | None = None,
        result_type: str | None = None,
    ) -> list[TaskResultRecord]:
        records = [
            TaskResultRecord.from_dict(item)
            for item in self._read_json(self._results_file)
        ]
        if task_id is not None:
            records = [record for record in records if record.task_id == task_id]
        if result_type is not None:
            records = [record for record in records if record.result_type == result_type]
        return records

    def save_result(self, result: TaskResultRecord) -> TaskResultRecord:
        records = self.list_results()
        self._write_records(
            self._results_file,
            self._upsert_by_key(records, result, "result_id"),
        )
        return result

    def list_plans(
        self,
        *,
        project_id: str | None = None,
        state: TaskPlanState | None = None,
    ) -> list[TaskPlanRecord]:
        records = [TaskPlanRecord.from_dict(item) for item in self._read_json(self._plans_file)]
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        if state is not None:
            records = [record for record in records if record.state == state]
        return records

    def get_plan(self, plan_id: str) -> TaskPlanRecord | None:
        for plan in self.list_plans():
            if plan.plan_id == plan_id:
                return plan
        return None

    def save_plan(self, plan: TaskPlanRecord) -> TaskPlanRecord:
        records = self.list_plans()
        self._write_records(
            self._plans_file,
            self._upsert_by_key(records, plan, "plan_id"),
        )
        return plan

    def list_execution_logs(
        self,
        *,
        task_id: str | None = None,
    ) -> list[TaskExecutionLogRecord]:
        records = [
            TaskExecutionLogRecord.from_dict(item)
            for item in self._read_json(self._execution_logs_file)
        ]
        if task_id is not None:
            records = [record for record in records if record.task_id == task_id]
        return records

    def save_execution_log(
        self,
        log: TaskExecutionLogRecord,
    ) -> TaskExecutionLogRecord:
        records = self.list_execution_logs()
        self._write_records(
            self._execution_logs_file,
            self._upsert_by_key(records, log, "log_id"),
        )
        return log

    def _read_json(self, file_path: Path) -> list[dict]:
        if not file_path.exists():
            return []
        return json.loads(file_path.read_text(encoding="utf-8"))

    def _write_records(
        self,
        file_path: Path,
        records: (
            list[TaskRecord]
            | list[TaskResultRecord]
            | list[TaskPlanRecord]
            | list[TaskExecutionLogRecord]
        ),
    ) -> None:
        self._state_dir.mkdir(parents=True, exist_ok=True)
        payload = [record.to_dict() for record in records]
        file_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def _upsert_by_key(
        self,
        records: list,
        record: object,
        key: str,
    ) -> list:
        record_key = getattr(record, key)
        updated = []
        replaced = False
        for item in records:
            if getattr(item, key) == record_key:
                updated.append(record)
                replaced = True
            else:
                updated.append(item)
        if not replaced:
            updated.append(record)
        return updated
