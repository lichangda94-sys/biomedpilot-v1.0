from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QScrollArea

    from app.bioinformatics.project_home import BioinformaticsProjectHomeWidget
    from app.bioinformatics.project_workspace import create_bioinformatics_project
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    BioinformaticsProjectHomeWidget = None  # type: ignore[assignment]
    create_bioinformatics_project = None  # type: ignore[assignment]
    QScrollArea = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def test_bioinformatics_project_home_instantiates_with_empty_state(qt_app) -> None:
    widget = BioinformaticsProjectHomeWidget()

    assert widget.objectName() == "bioinformaticsProjectHomePage"
    assert widget.current_summary() is None
    assert "尚未选择项目" in widget.status_message()
    assert widget.findChild(QScrollArea, "bioProjectHomeScrollArea") is not None


def test_project_home_uses_ui03_icons(qt_app) -> None:
    widget = BioinformaticsProjectHomeWidget()

    icons = widget.findChildren(QLabel, "bioProjectIcon")
    icon_count = sum(1 for icon in icons if not icon.isHidden() and icon.pixmap() is not None and not icon.pixmap().isNull())
    project_name = widget.findChild(QLineEdit, "projectNameInput")
    save_location = widget.findChild(QLineEdit, "saveLocationInput")
    create_button = widget.findChild(QPushButton, "primaryButton")

    assert icon_count >= 5
    assert project_name is not None and project_name.actions()
    assert save_location is not None and save_location.actions()
    assert create_button is not None and not create_button.icon().isNull()


def test_project_home_create_project_generates_summary(qt_app, tmp_path) -> None:
    events = []
    widget = BioinformaticsProjectHomeWidget(on_continue=events.append)
    widget.set_new_project_inputs("UI Project", tmp_path)

    summary = widget.create_project_from_inputs()

    assert summary is not None
    assert widget.current_summary() == summary
    assert summary.project_name == "UI Project"
    assert summary.manifest_path.exists()
    assert summary.config_path.exists()
    assert "正在进入数据来源与登记" in widget.status_message()
    assert events == [summary]


def test_project_home_opens_valid_project(qt_app, tmp_path) -> None:
    created = create_bioinformatics_project("Openable Project", tmp_path)
    events = []
    widget = BioinformaticsProjectHomeWidget(on_continue=events.append)
    widget.set_existing_project_path(created.project_root)

    summary = widget.open_selected_project()

    assert summary is not None
    assert summary.project_name == "Openable Project"
    assert summary.project_root == created.project_root
    assert summary.current_stage == "project_created"
    assert summary.readiness_status == "ready_for_data_source_selection"
    assert "项目验证通过" in widget.status_message()
    assert events == [summary]


def test_project_home_invalid_folder_shows_chinese_error(qt_app, tmp_path) -> None:
    invalid_dir = tmp_path / "invalid"
    invalid_dir.mkdir()
    events = []
    widget = BioinformaticsProjectHomeWidget(on_continue=events.append)
    widget.set_existing_project_path(invalid_dir)

    assert widget.open_selected_project() is None
    assert "该文件夹不是有效的生信分析项目" in widget.status_message()
    assert events == []


def test_project_home_continue_triggers_callback(qt_app, tmp_path) -> None:
    events = []
    widget = BioinformaticsProjectHomeWidget(on_continue=events.append)
    widget.set_new_project_inputs("Continue Project", tmp_path)
    summary = widget.create_project_from_inputs()

    assert events == [summary]


def test_project_home_removes_summary_action_buttons_and_updates_open_copy(qt_app) -> None:
    widget = BioinformaticsProjectHomeWidget()
    button_texts = [button.text() for button in widget.findChildren(QPushButton)]
    label_text = "\n".join(label.text() for label in widget.findChildren(QLabel))

    assert "继续：数据来源选择" not in button_texts
    assert "打开项目文件夹" not in button_texts
    assert "打开项目" not in button_texts
    assert "确认并继续" in button_texts
    assert "创建项目并继续" in button_texts
    assert "raw_data/" not in label_text
    assert "project_manifest.json" not in label_text
    assert "每个项目会自动保存原始数据、分析结果、报告和日志" in label_text


def test_project_home_back_triggers_callback(qt_app) -> None:
    events: list[str] = []
    widget = BioinformaticsProjectHomeWidget(on_back=lambda: events.append("back"))

    widget.back_requested.emit()

    assert events == ["back"]
