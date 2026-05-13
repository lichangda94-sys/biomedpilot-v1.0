from __future__ import annotations

import csv
import json
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.models.systematic_review import (
    FULLTEXT_AVAILABILITY_STATUSES,
    FULLTEXT_EXCLUSION_REASONS,
    FullTextFile,
    FullTextScreeningDecision,
    fulltext_decision_from_dict,
    fulltext_decision_to_dict,
    fulltext_file_from_dict,
    fulltext_file_to_dict,
    new_fulltext_decision_id,
    new_fulltext_id,
    now_utc,
)
from app.meta_analysis.models.attachments import ATTACHMENT_MODES
from app.meta_analysis.services.attachment_service import AttachmentService
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


class FullTextService:
    def __init__(
        self,
        *,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        attachment_service: AttachmentService | None = None,
        audit_log: MetaAuditLogService | None = None,
    ) -> None:
        self._task_center = task_center
        self._data_center = data_center
        self._audit_log = audit_log or MetaAuditLogService()
        self._attachment_service = attachment_service or AttachmentService(task_center=task_center, data_center=data_center, audit_log=self._audit_log)

    def attach_fulltext(self, project_dir: Path, record_id: str, source_file_path: str, *, notes: str = "") -> FullTextFile:
        return self.attach_pdf(project_dir, record_id, source_file_path, mode="copy_to_project_library", notes=notes)

    def attach_pdf(
        self,
        project_dir: Path,
        record_id: str,
        source_file_path: str,
        *,
        mode: str = "copy_to_project_library",
        notes: str = "",
    ) -> FullTextFile:
        if mode not in ATTACHMENT_MODES:
            raise ValueError("unsupported_attachment_mode")
        if mode == "ignore_attachments":
            return self.update_fulltext_availability(project_dir, record_id, "not_required")
        project_dir = project_dir.expanduser().resolve()
        source = Path(source_file_path).expanduser().resolve()
        if not source.exists() or not source.is_file():
            raise ValueError("fulltext_source_file_missing")
        task = self._start_task(project_id=project_dir.name, task_type=TaskType.FULLTEXT_ATTACH, title="Full-text Attach")
        attachment = self._attachment_service.add_attachment(
            project_dir,
            record_id=record_id,
            source_file_path=str(source),
            attachment_type="pdf",
            mode=mode,
            notes=notes,
        )
        if attachment is None:
            raise ValueError("fulltext_attachment_not_created")
        target = Path(attachment.file_path)
        output_dir = project_dir / "fulltext"
        output_dir.mkdir(parents=True, exist_ok=True)
        record = FullTextFile(
            fulltext_id=new_fulltext_id(),
            project_id=project_dir.name,
            record_id=record_id,
            pdf_path=str(target),
            supplementary_paths=[],
            availability_status="available",
            uploaded_at=now_utc(),
            notes=notes,
        )
        records = [existing for existing in self.list_fulltext_files(project_dir) if existing.record_id != record_id]
        records.append(record)
        self.save_fulltext_registry(project_dir, records)
        self._register_asset(project_id=project_dir.name, data_type="fulltext_registry", source_path=str(source), output_path=str(self._registry_path(project_dir)))
        self._audit_log.record_event(
            project_dir,
            event_type="fulltext_status_changed",
            project_id=project_dir.name,
            target_type="fulltext",
            target_id=record.fulltext_id,
            source_path=str(source),
            output_path=str(self._registry_path(project_dir)),
            summary=f"Full-text attached for {record_id}",
            details={"attachment_id": attachment.attachment_id, "mode": mode},
        )
        self._finish_task(task, success=True, summary=f"Full-text attached for {record_id}")
        return record

    def list_fulltext_files(self, project_dir: Path) -> list[FullTextFile]:
        path = self._registry_path(project_dir.expanduser().resolve())
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [fulltext_file_from_dict(item) for item in payload.get("fulltext_files", [])]

    def get_fulltext_by_record_id(self, project_dir: Path, record_id: str) -> FullTextFile | None:
        for record in self.list_fulltext_files(project_dir):
            if record.record_id == record_id:
                return record
        return None

    def update_fulltext_availability(self, project_dir: Path, record_id: str, status: str) -> FullTextFile:
        if status not in FULLTEXT_AVAILABILITY_STATUSES:
            raise ValueError("unsupported_fulltext_availability_status")
        records = self.list_fulltext_files(project_dir)
        updated: FullTextFile | None = None
        replacement: list[FullTextFile] = []
        for record in records:
            if record.record_id == record_id:
                updated = FullTextFile(
                    fulltext_id=record.fulltext_id,
                    project_id=record.project_id,
                    record_id=record.record_id,
                    pdf_path=record.pdf_path,
                    supplementary_paths=record.supplementary_paths,
                    availability_status=status,
                    uploaded_at=record.uploaded_at,
                    notes=record.notes,
                )
                replacement.append(updated)
            else:
                replacement.append(record)
        if updated is None:
            updated = FullTextFile(
                fulltext_id=new_fulltext_id(),
                project_id=project_dir.name,
                record_id=record_id,
                pdf_path="",
                supplementary_paths=[],
                availability_status=status,
                uploaded_at=now_utc(),
            )
            replacement.append(updated)
        self.save_fulltext_registry(project_dir, replacement)
        self._audit_log.record_event(
            project_dir,
            event_type="fulltext_status_changed",
            project_id=project_dir.name,
            target_type="fulltext",
            target_id=updated.fulltext_id,
            output_path=str(self._registry_path(project_dir)),
            summary=f"Full-text status changed to {status} for {record_id}",
        )
        return updated

    def save_fulltext_registry(self, project_dir: Path, records: list[FullTextFile]) -> Path:
        project_dir = project_dir.expanduser().resolve()
        path = self._registry_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"project_id": project_dir.name, "fulltext_files": [fulltext_file_to_dict(record) for record in records]}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load_fulltext_registry(self, project_dir: Path) -> list[FullTextFile]:
        return self.list_fulltext_files(project_dir)

    def save_fulltext_decision(
        self,
        project_dir: Path,
        *,
        record_id: str,
        reviewer_id: str,
        decision: str,
        exclusion_reason: str = "",
        notes: str = "",
    ) -> FullTextScreeningDecision:
        normalized_decision = decision.strip().lower()
        if normalized_decision not in {"include", "exclude", "maybe"}:
            raise ValueError("unsupported_fulltext_screening_decision")
        if normalized_decision == "exclude" and exclusion_reason not in FULLTEXT_EXCLUSION_REASONS:
            raise ValueError("unsupported_fulltext_exclusion_reason")
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(project_id=project_dir.name, task_type=TaskType.FULLTEXT_SCREENING_DECISION, title="Full-text Screening Decision")
        decision_record = FullTextScreeningDecision(
            decision_id=new_fulltext_decision_id(),
            project_id=project_dir.name,
            record_id=record_id,
            reviewer_id=reviewer_id,
            decision=normalized_decision,
            exclusion_reason=exclusion_reason if normalized_decision == "exclude" else "",
            notes=notes,
            created_at=now_utc(),
        )
        decisions = [existing for existing in self.load_fulltext_decisions(project_dir) if existing.record_id != record_id]
        decisions.append(decision_record)
        self._write_decisions(project_dir, decisions)
        self._register_asset(project_id=project_dir.name, data_type="fulltext_screening_decisions", source_path=str(project_dir), output_path=str(self._decisions_path(project_dir)))
        self._finish_task(task, success=True, summary=f"Full-text decision saved for {record_id}")
        return decision_record

    def load_fulltext_decisions(self, project_dir: Path) -> list[FullTextScreeningDecision]:
        path = self._decisions_path(project_dir.expanduser().resolve())
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [fulltext_decision_from_dict(item) for item in payload.get("decisions", [])]

    def export_full_text_exclusion_report(self, project_dir: Path) -> Path:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(project_id=project_dir.name, task_type=TaskType.FULLTEXT_EXCLUSION_EXPORT, title="Full-text Exclusion Export")
        output_path = project_dir / "reports" / "full_text_exclusion_report.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["record_id", "decision", "exclusion_reason", "reviewer_id", "notes", "created_at"])
            writer.writeheader()
            for decision in self.load_fulltext_decisions(project_dir):
                if decision.decision == "exclude":
                    writer.writerow(
                        {
                            "record_id": decision.record_id,
                            "decision": decision.decision,
                            "exclusion_reason": decision.exclusion_reason,
                            "reviewer_id": decision.reviewer_id,
                            "notes": decision.notes,
                            "created_at": decision.created_at,
                        }
                    )
        self._register_asset(project_id=project_dir.name, data_type="full_text_exclusion_report", source_path=str(self._decisions_path(project_dir)), output_path=str(output_path))
        self._finish_task(task, success=True, summary=f"Full-text exclusion report exported: {output_path}")
        return output_path

    def exclusion_reasons(self) -> tuple[str, ...]:
        return FULLTEXT_EXCLUSION_REASONS

    def _registry_path(self, project_dir: Path) -> Path:
        return project_dir / "fulltext" / "fulltext_registry.json"

    def _decisions_path(self, project_dir: Path) -> Path:
        return project_dir / "fulltext" / "fulltext_screening_decisions.json"

    def _write_decisions(self, project_dir: Path, decisions: list[FullTextScreeningDecision]) -> Path:
        path = self._decisions_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"project_id": project_dir.name, "decisions": [fulltext_decision_to_dict(decision) for decision in decisions]}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _register_asset(self, *, project_id: str, data_type: str, source_path: str, output_path: str) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(project_id=project_id, module="meta_analysis", data_type=data_type, source_path=source_path, output_path=output_path, status="available")

    def _start_task(self, *, project_id: str, task_type: TaskType, title: str) -> TaskRecord:
        now = now_utc()
        if self._task_center is None:
            return TaskRecord(task_id=f"task-{uuid4().hex[:12]}", task_type=task_type, status=TaskStatus.RUNNING, module="meta_analysis", title=title, created_at=now, updated_at=now, project_id=project_id, started_at=now)
        return self._task_center.register_task(task_id=f"task-{uuid4().hex[:12]}", task_type=task_type, module="meta_analysis", title=title, project_id=project_id, status=TaskStatus.RUNNING, started_at=now)

    def _finish_task(self, task: TaskRecord, *, success: bool, summary: str) -> None:
        if self._task_center is None:
            return
        now = now_utc()
        self._task_center.save_task(TaskRecord(task_id=task.task_id, task_type=task.task_type, status=TaskStatus.COMPLETED if success else TaskStatus.FAILED, module=task.module, title=task.title, created_at=task.created_at, updated_at=now, project_id=task.project_id, started_at=task.started_at, finished_at=now, summary=summary, error_message="" if success else summary))
