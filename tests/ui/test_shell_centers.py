from __future__ import annotations

import json
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton, QScrollArea, QStackedWidget, QTabBar

    from app.shell.centers_page import build_centers_page
    from app.shell.main_window import MainWindow
    from app.shared.data_center.service import DataCenter
    from app.shared.project_center.service import ProjectCenter
    from app.shared.semantic_keys import NavKey
    from app.shared.task_center.service import TaskCenter
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def _button(widget, object_name: str):
    button = widget.findChild(QPushButton, object_name)
    assert button is not None, object_name
    assert button.property("buttonBehavior") is not None
    assert button.property("formalActionEnabled") is False
    if not button.isEnabled():
        assert button.property("disabledReason") is not None
    return button


def test_shell_centers_page_exposes_six_center_tabs(qt_app, tmp_path) -> None:
    project_center = ProjectCenter(tmp_path / "projects" / "projects.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    page = build_centers_page(project_center=project_center, data_center=data_center, task_center=task_center)
    nav = page.findChild(QTabBar, "centersSecondaryNav")
    stack = page.findChild(QStackedWidget, "centersContentStack")

    assert page.objectName() == "centersPage"
    assert page.property("navKey") == NavKey.CENTERS.value
    assert page.accessibleName() == "Shell centers page"
    assert nav is not None
    assert [nav.tabData(index) for index in range(nav.count())] == ["project", "data", "task", "report", "environment", "packaging"]
    assert stack is not None
    assert [stack.widget(index).property("centerKey") for index in range(stack.count())] == ["project", "data", "task", "report", "environment", "packaging"]


def test_shell_centers_buttons_click_services_or_write_artifacts(qt_app, tmp_path) -> None:
    project_center = ProjectCenter(tmp_path / "projects" / "projects.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center.register_asset(project_id="project-1", module="bioinformatics", data_type="expression_matrix", source_path="source.tsv", output_path="output.tsv")
    page = build_centers_page(project_center=project_center, data_center=data_center, task_center=task_center)

    _button(page, "centersCreateProjectRecordButton").click()
    assert project_center.storage_path.exists()
    assert project_center.list_projects(limit=None)
    _button(page, "centersOpenRecentProjectButton").click()
    recent_review = tmp_path / "centers" / "project_center_recent_project_review.json"
    assert recent_review.exists()
    assert json.loads(recent_review.read_text(encoding="utf-8"))["status"] == "opened_record_summary"

    _button(page, "centersExportDataIndexButton").click()
    data_index = tmp_path / "centers" / "data_center_index_summary.json"
    assert data_index.exists()
    assert json.loads(data_index.read_text(encoding="utf-8"))["asset_count"] == 1

    _button(page, "centersCreateTaskButton").click()
    assert task_center.storage_path.exists()
    assert task_center.list_tasks(limit=None)

    _button(page, "centersBuildReportIndexButton").click()
    report_index = tmp_path / "centers" / "report_center_index.json"
    assert report_index.exists()
    report_payload = json.loads(report_index.read_text(encoding="utf-8"))
    assert report_payload["formal_report_ready"] is False

    _button(page, "centersRunEnvironmentCheckButton").click()
    environment_status = tmp_path / "centers" / "environment_status.json"
    assert environment_status.exists()
    assert "python_version" in json.loads(environment_status.read_text(encoding="utf-8"))

    _button(page, "centersBuildPackagingPreflightButton").click()
    packaging_preflight = tmp_path / "centers" / "packaging_preflight.json"
    assert packaging_preflight.exists()
    packaging_payload = json.loads(packaging_preflight.read_text(encoding="utf-8"))
    assert packaging_payload["release_build_allowed"] is False

    build_button = _button(page, "centersRunReleaseBuildButton")
    assert not build_button.isEnabled()
    assert build_button.property("disabledReason") == "release_build_execution_not_allowed_from_centers_preview"


def test_main_window_sidebar_reaches_centers_shell(qt_app) -> None:
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        centers_button = next(button for button in window._sidebar.findChildren(QPushButton) if button.property("pageKey") == "centers")

        assert centers_button.property("semanticKey") == NavKey.CENTERS.value
        assert centers_button.property("buttonBehavior") == "navigates_to_shell_route_centers"

        centers_button.click()

        assert window.current_workspace_key() == "centers"
        assert window.findChild(QScrollArea, "centersPage") is not None
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
