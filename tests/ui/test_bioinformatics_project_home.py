from __future__ import annotations

import json
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QScrollArea

    from app.bioinformatics.project_home import BioinformaticsProjectHomeWidget
    from app.bioinformatics.project_workspace import create_bioinformatics_project, open_bioinformatics_project
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

    assert "打开项目" not in button_texts
    assert "确认并继续" in button_texts
    assert "创建项目并继续" in button_texts
    assert widget._summary_content.isHidden()
    assert "raw_data/" not in label_text
    assert "project_manifest.json" not in label_text
    assert "每个项目会自动保存原始数据、分析结果、报告和日志" in label_text


def test_project_summary_uses_user_friendly_status_card(qt_app, tmp_path) -> None:
    events = []
    widget = BioinformaticsProjectHomeWidget(on_continue=events.append)
    widget.set_new_project_inputs("Readable Project", tmp_path)
    summary = widget.create_project_from_inputs()

    label_text = "\n".join(label.text() for label in widget.findChildren(QLabel))
    button_texts = [button.text() for button in widget.findChildren(QPushButton)]

    assert summary is not None
    assert "project_created" not in label_text
    assert "ready_for_data_source_selection" not in label_text
    assert "项目名称：Readable Project" in label_text
    assert "当前状态：项目已创建，等待选择数据来源" in label_text
    assert "项目结构正常" in label_text
    assert "暂无警告" in label_text
    assert "当前：选择数据来源" in label_text
    assert "数据来源\n未选择" in label_text
    assert "样本识别\n未开始" in label_text
    assert "分析结果\n暂无" in label_text
    assert "项目报告\n未生成" in label_text
    assert "继续：选择数据来源" in button_texts
    assert "打开项目文件夹" in button_texts
    assert "查看项目结构" in button_texts
    assert str(summary.project_root) not in label_text
    assert widget._project_path_line.toolTip() == str(summary.project_root)


def test_project_summary_technical_details_are_collapsed_by_default(qt_app, tmp_path) -> None:
    widget = BioinformaticsProjectHomeWidget()
    widget.set_new_project_inputs("Tech Project", tmp_path)
    summary = widget.create_project_from_inputs()
    details = widget.findChild(QPlainTextEdit, "bioProjectTechnicalDetails")

    assert summary is not None
    assert details is not None
    assert details.isHidden()
    assert "project_stage: project_created" in details.toPlainText()
    assert "readiness: ready_for_data_source_selection" in details.toPlainText()
    widget._technical_toggle.setChecked(True)
    assert not details.isHidden()


def test_project_summary_reads_status_blocks_and_warning_card(qt_app, tmp_path) -> None:
    created = create_bioinformatics_project("Warned Project", tmp_path)
    manifest = json.loads(created.manifest_path.read_text(encoding="utf-8"))
    manifest["readiness"]["warning_count"] = 1
    manifest["readiness"]["warnings"] = ["缺少标准化表达矩阵"]
    created.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    records_dir = created.project_root / "acquisition" / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    (records_dir / "bio-test.json").write_text("{}", encoding="utf-8")
    recognition = created.project_root / "logs" / "recognition" / "recognition_report.json"
    recognition.parent.mkdir(parents=True, exist_ok=True)
    recognition.write_text(json.dumps({"files": [{"recognized_type": "sample_metadata"}]}), encoding="utf-8")
    result_index = created.project_root / "results" / "summaries" / "result_index.json"
    result_index.parent.mkdir(parents=True, exist_ok=True)
    result_index.write_text(json.dumps({"results": [{"path": "results/a.tsv"}]}), encoding="utf-8")
    report = created.project_root / "reports" / "project_analysis_report.md"
    report.write_text("# report\n", encoding="utf-8")
    summary = open_bioinformatics_project(created.project_root).summary

    widget = BioinformaticsProjectHomeWidget()
    widget._render_summary(summary)
    label_text = "\n".join(label.text() for label in widget.findChildren(QLabel))

    assert "存在 1 条项目警告" in label_text
    assert "缺少标准化表达矩阵" in label_text
    assert "数据来源\n已选择" in label_text
    assert "样本识别\n已识别" in label_text
    assert "分析结果\n已有 1 项" in label_text
    assert "项目报告\n已生成" in label_text


def test_project_home_back_triggers_callback(qt_app) -> None:
    events: list[str] = []
    widget = BioinformaticsProjectHomeWidget(on_back=lambda: events.append("back"))

    widget.back_requested.emit()

    assert events == ["back"]
