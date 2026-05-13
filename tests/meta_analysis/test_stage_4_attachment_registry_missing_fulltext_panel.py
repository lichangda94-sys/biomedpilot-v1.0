from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.attachment_page import attachment_state_from_project, initial_attachment_state
from app.meta_analysis.services.attachment_service import AttachmentService


def test_attachment_state_summarizes_registry_pdf_modes_and_missing_report(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    external_pdf = tmp_path / "external.pdf"
    external_pdf.write_bytes(b"%PDF-1.4 external")
    copy_pdf = tmp_path / "copy.pdf"
    copy_pdf.write_bytes(b"%PDF-1.4 copy")
    supplement = tmp_path / "supplement.txt"
    supplement.write_text("supplement", encoding="utf-8")
    service = AttachmentService()

    linked = service.add_attachment(
        project_dir,
        record_id="rec-1",
        source_file_path=str(external_pdf),
        attachment_type="pdf",
        mode="link_existing_files",
    )
    copied = service.add_attachment(
        project_dir,
        record_id="rec-2",
        source_file_path=str(copy_pdf),
        attachment_type="pdf",
        mode="copy_to_project_library",
    )
    service.add_attachment(
        project_dir,
        record_id="rec-3",
        source_file_path=str(supplement),
        attachment_type="supplement",
        mode="copy_to_project_library",
    )
    missing_report = service.export_missing_fulltext_report(project_dir, record_ids=["rec-1", "rec-2", "rec-3", "rec-4"])

    state = attachment_state_from_project(project_dir, service=service)
    rows = {row.record_id: row for row in state.attachment_rows}

    assert linked is not None and copied is not None
    assert state.status_label == "测试中"
    assert state.attachment_count == 3
    assert state.pdf_attachment_count == 2
    assert state.link_attachment_count == 1
    assert state.copy_attachment_count == 2
    assert state.ignore_attachment_count == 0
    assert state.broken_path_count == 0
    assert state.missing_fulltext_report_status == "available"
    assert state.missing_fulltext_count == 2
    assert state.missing_fulltext_report_path == str(missing_report)
    assert rows["rec-1"].file_name == external_pdf.name
    assert rows["rec-1"].attachment_type == "pdf"
    assert rows["rec-1"].file_exists is True
    assert rows["rec-1"].storage_mode == "link_existing_files"
    assert rows["rec-2"].storage_mode == "copy_to_project_library"


def test_attachment_state_handles_broken_paths_without_crashing(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    registry_path = project_dir / "attachments" / "attachment_registry.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "project_id": "meta-project",
                "attachments": [
                    {
                        "attachment_id": "att-broken",
                        "record_id": "rec-1",
                        "attachment_type": "pdf",
                        "file_path": str(tmp_path / "missing.pdf"),
                        "file_name": "missing.pdf",
                        "file_exists": True,
                        "file_size": 123,
                        "checksum": "old",
                        "added_at": "2026-01-01T00:00:00+00:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    state = attachment_state_from_project(project_dir, service=AttachmentService())

    assert state.attachment_count == 1
    assert state.pdf_attachment_count == 1
    assert state.broken_path_count == 1
    assert state.attachment_rows[0].record_id == "rec-1"
    assert state.attachment_rows[0].file_name == "missing.pdf"
    assert state.attachment_rows[0].attachment_type == "pdf"
    assert state.attachment_rows[0].file_exists is False
    assert "rec-1:pdf:missing:missing.pdf" in state.file_status_summary


def test_attachment_state_missing_fulltext_report_absent_is_empty_state(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    project_dir.mkdir()

    state = attachment_state_from_project(project_dir, service=AttachmentService())

    assert state.attachment_count == 0
    assert state.pdf_attachment_count == 0
    assert state.link_attachment_count == 0
    assert state.copy_attachment_count == 0
    assert state.ignore_attachment_count == 0
    assert state.broken_path_count == 0
    assert state.missing_fulltext_report_status == "not_generated"
    assert state.missing_fulltext_count == 0
    assert state.attachment_rows == ()
    assert state.file_status_summary == ()
    assert state.missing_fulltext_report_path.endswith("missing_fulltext_report.csv")


def test_attachment_state_keeps_supported_modes_visible_and_no_download_claims() -> None:
    state = initial_attachment_state()

    assert state.mode_options == ("ignore_attachments", "link_existing_files", "copy_to_project_library")
    assert "不自动下载 PDF" in state.description
    assert "测试中" == state.status_label
