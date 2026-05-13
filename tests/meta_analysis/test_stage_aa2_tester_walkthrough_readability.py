from __future__ import annotations

from pathlib import Path

from app.meta_analysis.pages.attachment_page import attachment_state_from_project, initial_attachment_state
from app.meta_analysis.pages.audit_log_page import audit_log_state_from_project, initial_audit_log_state
from app.meta_analysis.pages.duplicate_review_page import duplicate_review_state_from_groups, initial_duplicate_review_state
from app.meta_analysis.pages.literature_import_page import import_diagnostics_visual_summary, initial_literature_import_state
from app.meta_analysis.pages.reporting_page import initial_reporting_state, reporting_prisma_trace_state_from_project
from app.meta_analysis.pages.warning_severity import classify_warning_severity


def test_aa2_page_states_include_help_next_step_and_testing_limits(tmp_path: Path) -> None:
    import_state = initial_literature_import_state()
    duplicate_state = initial_duplicate_review_state()
    attachment_state = initial_attachment_state()
    reporting_state = initial_reporting_state()
    audit_state = initial_audit_log_state()

    states = (import_state, duplicate_state, attachment_state, reporting_state, audit_state)
    for state in states:
        assert state.status_label in {"测试中", "Testing / Developer Preview"}
        assert state.input_summary
        assert state.output_summary
        assert state.next_step
        assert state.warning_summary
        assert state.panel_help
        assert state.testing_limitations

    assert "Diagnostics" in " ".join(import_state.panel_help) or "diagnostics" in " ".join(import_state.panel_help)
    assert "merge preview" in " ".join(duplicate_state.panel_help)
    assert "不自动下载 PDF" in " ".join(attachment_state.testing_limitations)
    assert "PRISMA" in " ".join(reporting_state.panel_help)
    assert "review_log.csv" in " ".join(audit_state.panel_help)


def test_aa2_warning_severity_helper_classifies_typical_cases() -> None:
    assert classify_warning_severity(context="import_diagnostics", key="missing_title_count") == "blocker"
    assert classify_warning_severity(context="import_diagnostics", key="missing_author_count") == "major"
    assert classify_warning_severity(context="import_diagnostics", key="missing_doi_count") == "minor"
    assert classify_warning_severity(context="attachment", key="attachment_registry_missing") == "major"
    assert classify_warning_severity(context="attachment", key="missing_fulltext_count") == "minor"
    assert classify_warning_severity(context="merge_preview", key="merge_preview_no_records") == "blocker"
    assert classify_warning_severity(context="merge_preview", key="field_conflict") == "major"
    assert classify_warning_severity(context="prisma_trace", key="missing_source_reference") == "major"
    assert classify_warning_severity(context="prisma_trace", key="missing_audit_events") == "minor"
    assert classify_warning_severity(context="prisma_trace", key="formal_prisma_diagram_not_implemented") == "info"


def test_aa2_missing_diagnostics_attachment_audit_prisma_do_not_crash(tmp_path: Path) -> None:
    diagnostics = import_diagnostics_visual_summary(str(tmp_path / "missing_import_diagnostics.json"))
    attachment = attachment_state_from_project(tmp_path / "empty-project")
    audit = audit_log_state_from_project(tmp_path / "empty-project")
    prisma = reporting_prisma_trace_state_from_project(tmp_path / "empty-project")
    duplicate = duplicate_review_state_from_groups(groups=[])

    assert diagnostics.missing_diagnostics is True
    assert diagnostics.warning_severity_counts is not None
    assert attachment.attachment_registry_missing is True
    assert attachment.warning_severity_counts is not None
    assert audit.event_count == 0
    assert prisma.audit_reference_warnings
    assert prisma.warning_severity_counts is not None
    assert duplicate.duplicate_group_count == 0


def test_aa2_docs_exist_and_contain_key_headings() -> None:
    root = Path(__file__).resolve().parents[2]
    walkthrough = root / "docs" / "user_testing" / "meta_literature_workspace_walkthrough.md"
    checklist = root / "docs" / "user_testing" / "meta_literature_workspace_checklist.md"
    limitations = root / "docs" / "user_testing" / "known_limitations.md"

    walkthrough_text = walkthrough.read_text(encoding="utf-8")
    checklist_text = checklist.read_text(encoding="utf-8")
    limitations_text = limitations.read_text(encoding="utf-8")

    assert "Meta Literature Workspace Walkthrough" in walkthrough_text
    assert "查看 Import diagnostics" in walkthrough_text
    assert "查看 Duplicate Merge Preview" in walkthrough_text
    assert "导出 Review Log" in walkthrough_text
    assert "Meta Literature Workspace Checklist" in checklist_text
    assert "| 测试项 | 操作步骤 | 预期结果 | 失败时记录内容 | 严重程度建议 |" in checklist_text
    assert "formal PRISMA diagram" in limitations_text or "正式 PRISMA diagram" in limitations_text
    assert "does not download PDFs" in limitations_text or "不自动下载 PDF" in limitations_text
