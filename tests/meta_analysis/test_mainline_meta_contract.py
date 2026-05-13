from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.meta_analysis.project_workspace import create_meta_analysis_project, open_meta_analysis_project
from app.meta_analysis.workspace import meta_workspace_layout_state
from app.shared.ui import BioMedPilotColors, button_qss, page_title_qss, status_badge_qss

try:
    from PySide6.QtWidgets import QApplication, QFrame, QLabel, QPushButton
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
    assert [item.page_key for item in state.navigation_items] == ["workflow_home", "project_contract", "dev_branch"]
    assert "独立开发线" in state.testing_notice


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

    assert widget.page_keys() == ("workflow_home", "project_contract", "dev_branch")
    assert widget.current_project_dir() == project.project_root
    assert "Meta UI" in widget._status_label.text()
    assert str(project.project_root) not in widget._status_label.text()
    assert "meta_project_manifest.json" not in widget._status_label.text()
    assert "草稿" in widget._status_label.text()
    assert status_badge_qss("draft") == widget._status_label.styleSheet()
    assert widget._diagnostic_card.isHidden()
    assert str(project.project_root) in widget._diagnostic_text.text()
    assert "manifest_path:" in widget._diagnostic_text.text()


def test_mainline_meta_workspace_uses_shared_ui_styles(qt_app) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    widget = MetaAnalysisWorkspaceWidget(on_back=lambda: None)

    title = widget.findChild(QLabel, "metaWorkspaceTitle")
    assert title is not None
    assert title.styleSheet() == page_title_qss()

    header = widget.findChild(QFrame, "metaMainlineHeader")
    assert header is not None
    assert BioMedPilotColors.SURFACE_WHITE in header.styleSheet()
    assert BioMedPilotColors.BORDER_MEDIUM in header.styleSheet()

    back = widget.findChild(QPushButton, "metaBackButton")
    assert back is not None
    assert back.property("buttonRole") == "navigation_back"
    assert back.styleSheet() == button_qss("navigation_back")

    toggle = widget.findChild(QPushButton, "metaDeveloperDiagnosticsToggle")
    assert toggle is not None
    assert toggle.property("buttonRole") == "secondary"
    assert widget._diagnostic_card.isHidden()
    toggle.click()
    assert not widget._diagnostic_card.isHidden()
    assert toggle.text() == "收起开发者诊断"
