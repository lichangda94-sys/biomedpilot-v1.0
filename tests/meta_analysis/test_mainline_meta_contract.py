from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.meta_analysis.project_workspace import create_meta_analysis_project, open_meta_analysis_project
from app.meta_analysis.workspace import meta_workspace_layout_state

try:
    from PySide6.QtWidgets import QApplication
except Exception as exc:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def test_mainline_meta_layout_is_shell_contract() -> None:
    state = meta_workspace_layout_state()

    assert state.default_page_key == "workflow_home"
    assert [item.page_key for item in state.navigation_items] == [
        "workflow_home",
        "pico_workspace",
        "search_strategy",
        "literature_import",
        "screening_review",
        "manual_extraction",
        "statistics_analysis",
        "report_export",
    ]
    assert "内部测试版" in state.testing_notice


def test_meta_project_contract_can_create_and_open_project(tmp_path) -> None:
    summary = create_meta_analysis_project("Meta Contract", tmp_path, research_topic="test topic")
    validation = open_meta_analysis_project(summary.project_root)

    assert validation.is_valid is True
    assert validation.summary is not None
    assert validation.summary.project_name == "Meta Contract"
    assert (summary.project_root / "meta_project_manifest.json").exists()


def test_mainline_meta_workspace_binds_project_record(qt_app, tmp_path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
    from app.shared.project_center.service import ProjectRecord

    project = create_meta_analysis_project("Meta UI", tmp_path)
    record = ProjectRecord(
        project_id="meta-ui",
        project_name="Meta UI",
        project_type="meta_analysis",
        created_at="2026-05-11T00:00:00+08:00",
        updated_at="2026-05-11T00:00:00+08:00",
        project_dir=str(project.project_root),
        current_stage="created",
        status="active",
    )
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_record(record)

    assert widget.page_keys() == (
        "workflow_home",
        "pico_workspace",
        "search_strategy",
        "literature_import",
        "screening_review",
        "manual_extraction",
        "statistics_analysis",
        "report_export",
    )
    assert widget.current_project_dir() == project.project_root
    assert "Meta UI" in widget._project_summary_label.text()
