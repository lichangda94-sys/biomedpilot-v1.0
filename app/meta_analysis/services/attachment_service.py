from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.models.attachments import (
    ATTACHMENT_MODES,
    ATTACHMENT_TYPES,
    AttachmentRecord,
    attachment_from_dict,
    attachment_to_dict,
    new_attachment_id,
    now_utc,
)
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


class AttachmentService:
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

    def add_attachment(
        self,
        project_dir: Path,
        *,
        record_id: str,
        source_file_path: str,
        attachment_type: str = "other",
        mode: str = "copy_to_project_library",
        added_by: str = "system",
        notes: str = "",
    ) -> AttachmentRecord | None:
        if mode not in ATTACHMENT_MODES:
            raise ValueError("unsupported_attachment_mode")
        if mode == "ignore_attachments":
            return None
        if attachment_type not in ATTACHMENT_TYPES:
            raise ValueError("unsupported_attachment_type")
        project_dir = project_dir.expanduser().resolve()
        source = Path(source_file_path).expanduser().resolve()
        if not source.exists() or not source.is_file():
            raise ValueError("attachment_source_file_missing")
        task_type = TaskType.ATTACHMENT_COPY if mode == "copy_to_project_library" else TaskType.ATTACHMENT_LINK
        task = self._start_task(project_dir.name, task_type, "Attachment")
        target = source
        if mode == "copy_to_project_library":
            library = project_dir / "fulltext" if attachment_type == "pdf" else project_dir / "attachments" / record_id
            library.mkdir(parents=True, exist_ok=True)
            target = library / (f"{record_id}_{source.name}" if attachment_type == "pdf" else source.name)
            shutil.copy2(source, target)
        record = self._build_record(record_id, target, attachment_type, added_by=added_by, notes=notes)
        records = [existing for existing in self.list_attachments(project_dir) if existing.attachment_id != record.attachment_id]
        records.append(record)
        self.save_attachment_registry(project_dir, records)
        self._register_asset(project_dir.name, "attachment_registry", str(source), str(self._registry_path(project_dir)))
        self._audit_log.record_event(
            project_dir,
            event_type="fulltext_status_changed" if attachment_type == "pdf" else "record_saved",
            project_id=project_dir.name,
            target_type="attachment",
            target_id=record.attachment_id,
            source_path=str(source),
            output_path=str(target),
            summary=f"Attachment {mode}: {record.file_name}",
            details={"record_id": record_id, "attachment_type": attachment_type, "mode": mode},
        )
        self._finish_task(task, True, f"Attachment saved for {record_id}")
        return record

    def list_attachments(self, project_dir: Path) -> list[AttachmentRecord]:
        path = self._registry_path(project_dir.expanduser().resolve())
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [attachment_from_dict(item) for item in payload.get("attachments", [])]

    def get_attachments_for_record(self, project_dir: Path, record_id: str) -> list[AttachmentRecord]:
        return [record for record in self.list_attachments(project_dir) if record.record_id == record_id]

    def validate_attachments(self, project_dir: Path) -> list[AttachmentRecord]:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(project_dir.name, TaskType.ATTACHMENT_VALIDATE, "Attachment Validate")
        refreshed = [
            self._build_record(record.record_id, Path(record.file_path), record.attachment_type, attachment_id=record.attachment_id, added_by=record.added_by, notes=record.notes, added_at=record.added_at)
            for record in self.list_attachments(project_dir)
        ]
        self.save_attachment_registry(project_dir, refreshed)
        self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=project_dir.name,
            target_type="attachment_registry",
            target_id="attachment_registry",
            output_path=str(self._registry_path(project_dir)),
            summary="Attachment registry validated.",
            details={"attachment_count": len(refreshed), "broken_path_count": len([record for record in refreshed if not record.file_exists])},
        )
        self._finish_task(task, True, f"Validated {len(refreshed)} attachments")
        return refreshed

    def save_attachment_registry(self, project_dir: Path, records: list[AttachmentRecord]) -> Path:
        project_dir = project_dir.expanduser().resolve()
        path = self._registry_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"project_id": project_dir.name, "attachments": [attachment_to_dict(record) for record in records]}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def export_missing_fulltext_report(self, project_dir: Path, *, record_ids: list[str] | None = None) -> Path:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(project_dir.name, TaskType.MISSING_FULLTEXT_REPORT_EXPORT, "Missing Full-text Report")
        output_path = project_dir / "reports" / "missing_fulltext_report.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        attachment_by_record = {
            record.record_id: record
            for record in self.list_attachments(project_dir)
            if record.attachment_type == "pdf" and record.file_exists
        }
        if record_ids is None:
            record_ids = sorted({record.record_id for record in self.list_attachments(project_dir)})
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["record_id", "missing_fulltext"])
            writer.writeheader()
            for record_id in record_ids:
                writer.writerow({"record_id": record_id, "missing_fulltext": str(record_id not in attachment_by_record).lower()})
        self._register_asset(project_dir.name, "missing_fulltext_report", str(self._registry_path(project_dir)), str(output_path))
        self._audit_log.record_event(
            project_dir,
            event_type="report_exported",
            project_id=project_dir.name,
            target_type="missing_fulltext_report",
            target_id="missing_fulltext_report.csv",
            source_path=str(self._registry_path(project_dir)),
            output_path=str(output_path),
            summary="Missing full-text report exported.",
            details={"record_count": len(record_ids)},
        )
        self._finish_task(task, True, f"Missing full-text report exported: {output_path}")
        return output_path

    def _build_record(
        self,
        record_id: str,
        file_path: Path,
        attachment_type: str,
        *,
        attachment_id: str | None = None,
        added_by: str = "system",
        notes: str = "",
        added_at: str | None = None,
    ) -> AttachmentRecord:
        exists = file_path.exists() and file_path.is_file()
        return AttachmentRecord(
            attachment_id=attachment_id or new_attachment_id(),
            record_id=record_id,
            attachment_type=attachment_type,
            file_path=str(file_path),
            file_name=file_path.name,
            file_exists=exists,
            file_size=file_path.stat().st_size if exists else 0,
            checksum=_sha256(file_path) if exists else "",
            added_at=added_at or now_utc(),
            added_by=added_by,
            notes=notes,
        )

    def _registry_path(self, project_dir: Path) -> Path:
        return project_dir / "attachments" / "attachment_registry.json"

    def _register_asset(self, project_id: str, data_type: str, source_path: str, output_path: str) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(project_id=project_id, module="meta_analysis", data_type=data_type, source_path=source_path, output_path=output_path, status="available")

    def _start_task(self, project_id: str, task_type: TaskType, title: str) -> TaskRecord:
        now = now_utc()
        if self._task_center is None:
            return TaskRecord(task_id=f"task-{uuid4().hex[:12]}", task_type=task_type, status=TaskStatus.RUNNING, module="meta_analysis", title=title, created_at=now, updated_at=now, project_id=project_id, started_at=now)
        return self._task_center.register_task(task_id=f"task-{uuid4().hex[:12]}", task_type=task_type, module="meta_analysis", title=title, project_id=project_id, status=TaskStatus.RUNNING, started_at=now)

    def _finish_task(self, task: TaskRecord, success: bool, summary: str) -> None:
        if self._task_center is None:
            return
        now = now_utc()
        self._task_center.save_task(TaskRecord(task_id=task.task_id, task_type=task.task_type, status=TaskStatus.COMPLETED if success else TaskStatus.FAILED, module=task.module, title=task.title, created_at=task.created_at, updated_at=now, project_id=task.project_id, started_at=task.started_at, finished_at=now, summary=summary, error_message="" if success else summary))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()
