from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.models.extraction import (
    ExtractionRecord,
    extraction_record_from_dict,
    extraction_record_to_dict,
)
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


class ExtractionRecordStorageService:
    def __init__(
        self,
        *,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        audit_log: MetaAuditLogService | None = None,
    ) -> None:
        self._task_center = task_center
        self._data_center = data_center
        self._audit_log = audit_log or MetaAuditLogService()

    def save_extraction_records(self, project_dir: Path, records: list[ExtractionRecord]) -> Path:
        project_dir = project_dir.expanduser().resolve()
        project_id = _project_id(project_dir, records)
        task = self._start_task(project_id=project_id, summary=f"Saving {len(records)} extraction records")
        output_path = self._records_path(project_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "project_id": project_id,
            "data_type": "extraction_records",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "records": [extraction_record_to_dict(record) for record in records],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._register_asset(project_id=project_id, source_path=str(project_dir), output_path=str(output_path))
        for record in records:
            self._audit_log.record_event(
                project_dir,
                event_type="extraction_updated",
                project_id=project_id,
                target_type="extraction_record",
                target_id=record.extraction_id,
                source_path=str(project_dir),
                output_path=str(output_path),
                summary=f"Extraction record saved for {record.record_id}",
            )
        self._finish_task(task, success=True, summary=f"Saved {len(records)} extraction records")
        return output_path

    def load_extraction_records(self, project_dir: Path) -> list[ExtractionRecord]:
        path = self._records_path(project_dir.expanduser().resolve())
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [extraction_record_from_dict(item) for item in payload.get("records", [])]

    def append_or_update_extraction_record(self, project_dir: Path, record: ExtractionRecord) -> Path:
        records = [existing for existing in self.load_extraction_records(project_dir) if existing.extraction_id != record.extraction_id]
        records.append(record)
        return self.save_extraction_records(project_dir, records)

    def get_extraction_records_by_record_id(self, project_dir: Path, record_id: str) -> list[ExtractionRecord]:
        return [record for record in self.load_extraction_records(project_dir) if record.record_id == record_id]

    def get_extraction_records_by_study_id(self, project_dir: Path, study_id: str) -> list[ExtractionRecord]:
        return [record for record in self.load_extraction_records(project_dir) if record.study_id == study_id]

    def list_extraction_outcomes(self, project_dir: Path) -> list[dict[str, str]]:
        outcomes: list[dict[str, str]] = []
        for record in self.load_extraction_records(project_dir):
            for outcome in record.outcomes:
                outcomes.append(
                    {
                        "extraction_id": record.extraction_id,
                        "record_id": record.record_id,
                        "study_id": record.study_id,
                        "profile_type": record.profile_type,
                        "outcome_id": outcome.outcome_id,
                        "outcome_data_type": outcome.outcome_data_type,
                        "outcome_name": outcome.data.outcome_name,
                        "effect_measure": outcome.data.effect_measure,
                    }
                )
        return outcomes

    def _records_path(self, project_dir: Path) -> Path:
        return project_dir / "extraction" / "extraction_records.json"

    def _register_asset(self, *, project_id: str, source_path: str, output_path: str) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(
            project_id=project_id,
            module="meta_analysis",
            data_type="extraction_records",
            source_path=source_path,
            output_path=output_path,
            status="available",
        )

    def _start_task(self, *, project_id: str, summary: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        if self._task_center is None:
            return TaskRecord(
                task_id=f"task-{uuid4().hex[:12]}",
                task_type=TaskType.EXTRACTION_RECORD_SAVE,
                status=TaskStatus.RUNNING,
                module="meta_analysis",
                title="Extraction Record Save",
                created_at=now,
                updated_at=now,
                project_id=project_id,
                started_at=now,
                summary=summary,
            )
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.EXTRACTION_RECORD_SAVE,
            module="meta_analysis",
            title="Extraction Record Save",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=summary,
        )

    def _finish_task(self, task: TaskRecord, *, success: bool, summary: str) -> None:
        if self._task_center is None:
            return
        now = datetime.now(timezone.utc).isoformat()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=summary,
                error_message="" if success else summary,
            )
        )


def _project_id(project_dir: Path, records: list[ExtractionRecord]) -> str:
    if records:
        return records[0].project_id
    return project_dir.name
