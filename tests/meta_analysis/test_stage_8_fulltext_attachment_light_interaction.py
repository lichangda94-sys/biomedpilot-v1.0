from __future__ import annotations

from pathlib import Path

from app.meta_analysis.pages.attachment_page import attachment_state_from_project, initial_attachment_state
from app.meta_analysis.services.attachment_service import AttachmentService
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.fulltext_service import FullTextService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def test_link_pdf_updates_attachment_fulltext_state_and_audit(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    source_pdf = tmp_path / "linked.pdf"
    source_pdf.write_bytes(b"%PDF-1.4 linked")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    audit = MetaAuditLogService()
    attachment_service = AttachmentService(task_center=task_center, data_center=data_center, audit_log=audit)
    fulltext_service = FullTextService(task_center=task_center, data_center=data_center, attachment_service=attachment_service, audit_log=audit)

    fulltext = fulltext_service.attach_pdf(project_dir, "rec-1", str(source_pdf), mode="link_existing_files")
    state = attachment_state_from_project(project_dir, service=attachment_service)
    events = audit.list_events(project_dir)

    assert fulltext.record_id == "rec-1"
    assert fulltext.pdf_path == str(source_pdf.resolve())
    assert state.attachment_count == 1
    assert state.pdf_attachment_count == 1
    assert state.link_attachment_count == 1
    assert state.copy_attachment_count == 0
    assert state.fulltext_record_count == 1
    assert state.attachment_validation_status == "valid"
    assert state.attachment_rows[0].record_id == "rec-1"
    assert state.attachment_rows[0].file_name == "linked.pdf"
    assert state.attachment_rows[0].attachment_type == "pdf"
    assert state.attachment_rows[0].file_exists is True
    assert any(event.event_type == "fulltext_status_changed" and event.target_type == "fulltext" for event in events)
    assert any(event.details.get("mode") == "link_existing_files" for event in events)


def test_copy_pdf_to_project_library_and_missing_report_export(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    source_pdf = tmp_path / "copied.pdf"
    source_pdf.write_bytes(b"%PDF-1.4 copied")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    audit = MetaAuditLogService()
    attachment_service = AttachmentService(task_center=task_center, data_center=data_center, audit_log=audit)
    fulltext_service = FullTextService(task_center=task_center, data_center=data_center, attachment_service=attachment_service, audit_log=audit)

    fulltext = fulltext_service.attach_pdf(project_dir, "rec-2", str(source_pdf), mode="copy_to_project_library")
    missing_path = attachment_service.export_missing_fulltext_report(project_dir, record_ids=["rec-1", "rec-2"])
    state = attachment_state_from_project(project_dir, service=attachment_service)

    assert Path(fulltext.pdf_path).exists()
    assert str(project_dir / "fulltext") in fulltext.pdf_path
    assert state.copy_attachment_count == 1
    assert state.link_attachment_count == 0
    assert state.missing_fulltext_report_status == "available"
    assert state.missing_fulltext_count == 1
    assert state.missing_fulltext_rows[0].record_id == "rec-1"
    assert state.missing_fulltext_rows[0].missing_fulltext is True
    assert state.missing_fulltext_rows[1].record_id == "rec-2"
    assert state.missing_fulltext_rows[1].missing_fulltext is False
    assert state.missing_fulltext_report_path == str(missing_path)
    assert {task.task_type for task in task_center.list_tasks()} >= {
        TaskType.FULLTEXT_ATTACH,
        TaskType.ATTACHMENT_COPY,
        TaskType.MISSING_FULLTEXT_REPORT_EXPORT,
    }
    assert any(event.event_type == "report_exported" and event.target_type == "missing_fulltext_report" for event in audit.list_events(project_dir))


def test_attachment_validation_detects_broken_link_without_crashing(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    source_pdf = tmp_path / "will_break.pdf"
    source_pdf.write_bytes(b"%PDF-1.4 linked")
    audit = MetaAuditLogService()
    attachment_service = AttachmentService(audit_log=audit)
    fulltext_service = FullTextService(attachment_service=attachment_service, audit_log=audit)
    fulltext_service.attach_pdf(project_dir, "rec-3", str(source_pdf), mode="link_existing_files")
    source_pdf.unlink()

    refreshed = attachment_service.validate_attachments(project_dir)
    state = attachment_state_from_project(project_dir, service=attachment_service)

    assert refreshed[0].file_exists is False
    assert state.broken_path_count == 1
    assert state.attachment_validation_status == "broken_paths_detected"
    assert "路径失效" in state.attachment_validation_message
    assert state.attachment_rows[0].file_exists is False
    assert any(event.event_type == "record_saved" and event.target_type == "attachment_registry" for event in audit.list_events(project_dir))


def test_ignore_mode_marks_fulltext_not_required_without_creating_pdf_attachment(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    attachment_service = AttachmentService()
    fulltext_service = FullTextService(attachment_service=attachment_service)

    fulltext = fulltext_service.attach_pdf(project_dir, "rec-4", "", mode="ignore_attachments")
    state = attachment_state_from_project(project_dir, service=attachment_service)

    assert fulltext.availability_status == "not_required"
    assert state.attachment_count == 0
    assert state.fulltext_record_count == 1
    assert state.ignore_attachment_count == 0


def test_attachment_page_state_keeps_forbidden_capabilities_out_of_scope() -> None:
    state = initial_attachment_state()

    forbidden = "自动下载 PDF OCR 网页抓取 机构代理登录 Zotero 双向同步"
    assert "不自动下载 PDF" in state.description
    assert "不执行自动 PDF 下载" in state.warning_summary
    assert "测试中" == state.status_label
    assert "OCR" not in state.description
    assert forbidden
