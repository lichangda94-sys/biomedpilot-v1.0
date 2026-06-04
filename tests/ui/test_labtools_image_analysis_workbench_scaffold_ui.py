from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture()
def qapp():
    try:
        from PySide6.QtWidgets import QApplication
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PySide6 UI runtime unavailable: {exc}")

    return QApplication.instance() or QApplication([])


def _visible_text(widget) -> str:
    from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit

    parts: list[str] = []
    for label in widget.findChildren(QLabel):
        parts.append(label.text())
    for button in widget.findChildren(QPushButton):
        parts.append(button.text())
    for panel in widget.findChildren(QTextEdit):
        parts.append(panel.toPlainText())
    return "\n".join(part for part in parts if part)


def _fake_executable(tmp_path: Path) -> Path:
    path = tmp_path / "fake_imagej"
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def _successful_imagej_runner(command, **kwargs):
    if "--version" in command:
        return subprocess.CompletedProcess(command, 0, stdout="ImageJ 1.54f\n", stderr="")
    if len(command) >= 2 and "smoke" in str(command[-2]):
        Path(command[-1]).write_text("status=ok\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
    output_path = Path(command[-1])
    output_path.write_text("status=macro_editor_ready\nanalysis=not_started\n", encoding="utf-8")
    return subprocess.CompletedProcess(command, 0, stdout="macro ok\n", stderr="")


def _bridge(tmp_path):
    from app.shared.local_engines import IMAGEJ_FIJI_ENGINE_ID, ImageJFijiBridge, LocalEngineConfigStore

    return ImageJFijiBridge(LocalEngineConfigStore(IMAGEJ_FIJI_ENGINE_ID, tmp_path / "imagej_fiji.json"))


def test_western_blot_result_tab_shows_image_analysis_workbench(qapp) -> None:
    from PySide6.QtWidgets import QTabWidget

    from app.labtools.ui.western_blot_widgets import LabToolsWesternBlotWidget

    widget = LabToolsWesternBlotWidget()
    tabs = widget.findChild(QTabWidget, "westernBlotTabs")
    tabs.setCurrentIndex(tabs.count() - 1)
    text = _visible_text(tabs.currentWidget())

    assert tabs.tabText(tabs.currentIndex()) == "结果与灰度分析"
    assert "Western Blot 结果与灰度分析" in text
    assert "第一步：导入图片" in text
    assert "第二步：预处理设置" in text
    assert "第三步：ROI 设置" in text
    assert "第四步：灰度结果" in text
    assert "第五步：归一化计算" in text
    assert "图像分析引擎未准备好" in text
    assert "运行 ImageJ macro" not in text


def test_cell_experiment_page_has_three_image_analysis_entries(qapp) -> None:
    from PySide6.QtWidgets import QFrame, QPushButton, QTabWidget, QTextEdit

    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_cell_experiments()
    tabs = widget._stack.currentWidget().findChild(QTabWidget, "cellExperimentImageAnalysisTabs")
    text = _visible_text(widget._stack.currentWidget())

    assert [tabs.tabText(index) for index in range(tabs.count())] == [
        "划痕实验图像分析",
        "Transwell 图像分析",
        "荧光 / 染色图像分析",
    ]
    assert "识别划痕区域" in text
    assert "统计细胞数" in text
    assert "测量荧光强度" in text
    assert "ImageJ 本地后端状态" in text
    assert "ImageJ macro 准备区" in text
    for index, analysis_type in enumerate(("scratch_area", "transwell_count", "fluorescence_intensity")):
        page = tabs.widget(index)
        assert page.property("uiPrimitive") == "labtools_c2_gated_workbench"
        assert page.property("connectionStatus") == "connected"
        assert page.property("formalActionEnabled") is False
        assert page.property("analysisType") == analysis_type
        assert page.findChild(QFrame, "imageWorkbenchHeader") is not None
        assert page.findChild(QTextEdit, "cellImageJMacroEditor") is not None
        primary = page.findChild(QPushButton, "imageWorkbenchPrimaryActionButton")
        assert primary is not None
        assert primary.property("buttonBehavior") == "creates_image_analysis_run_request_without_running_engine"
        export = page.findChild(QPushButton, "imageWorkbenchExportPlaceholderButton")
        assert export is not None
        assert not export.isEnabled()
        assert export.property("buttonBehavior") == "disabled_missing_real_image_analysis_result"
        assert "尚未产生真实图像分析结果" in export.property("disabledReason")


def test_workbench_generates_run_request_without_running_engine(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QPushButton

    from app.labtools.image_analysis import ImageAnalysisTaskStore
    from app.labtools.ui.image_analysis_widgets import ImageAnalysisWorkbenchWidget

    image_path = tmp_path / "cells.png"
    image_path.write_bytes(b"image")
    widget = ImageAnalysisWorkbenchWidget(
        experiment_module="cell_experiment",
        analysis_type="transwell_count",
        title="Transwell 图像分析",
        primary_actions=("识别细胞区域", "统计细胞数", "生成分析任务"),
        parameter_defaults={"分组": "A", "输出格式": "CSV"},
        task_store=ImageAnalysisTaskStore(tmp_path / "tasks"),
    )

    assert widget.property("uiPrimitive") == "labtools_c2_gated_workbench"
    assert widget.property("analysisType") == "transwell_count"
    assert widget.findChild(QPushButton, "imageWorkbenchExportPlaceholderButton") is None
    widget.set_image_paths_for_testing((str(image_path),))
    action_button = widget.findChildren(QPushButton, "imageWorkbenchPrimaryActionButton")[0]
    assert action_button.property("buttonBehavior") == "creates_image_analysis_run_request_without_running_engine"
    action_button.click()
    workspace = widget.latest_workspace()

    assert workspace is not None
    assert workspace.run_request_path.exists()
    action_manifest = workspace.task_dir / "review" / "image_action_manifest.json"
    assert action_manifest.exists()
    action_payload = json.loads(action_manifest.read_text(encoding="utf-8"))
    assert action_payload["requested_action"] == "识别细胞区域"
    assert action_payload["external_engine_execution_enabled"] is False
    assert workspace.task.status == "run_request_created"
    text = _visible_text(widget)
    assert "RunRequest 已生成" in text
    assert "尚未生成真实图像分析结果" in text
    assert "运行 ImageJ macro" not in text


def test_cell_workbench_writes_and_runs_macro_draft_through_configured_imagej(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QPushButton, QTextEdit

    from app.labtools.image_analysis import ImageAnalysisTaskStore
    from app.labtools.ui.image_analysis_widgets import ImageAnalysisWorkbenchWidget

    bridge = _bridge(tmp_path)
    bridge.configure_path(_fake_executable(tmp_path))
    image_path = tmp_path / "cells.png"
    image_path.write_bytes(b"image")
    widget = ImageAnalysisWorkbenchWidget(
        experiment_module="cell_experiment",
        analysis_type="transwell_count",
        title="Transwell 图像分析",
        primary_actions=("识别细胞区域", "统计细胞数", "生成分析任务"),
        parameter_defaults={"分组": "A", "输出格式": "CSV"},
        task_store=ImageAnalysisTaskStore(tmp_path / "tasks"),
        imagej_bridge=bridge,
        imagej_runner=_successful_imagej_runner,
    )
    widget.set_image_paths_for_testing((str(image_path),))

    editor = widget.findChild(QTextEdit, "cellImageJMacroEditor")
    assert editor is not None
    assert "not a formal cell-recognition macro" in editor.toPlainText()
    write_button = widget.findChild(QPushButton, "cellImageJWriteMacroDraftButton")
    run_button = widget.findChild(QPushButton, "cellImageJRunMacroDraftButton")
    write_button.click()
    workspace = widget.latest_workspace()

    assert workspace is not None
    draft_path = workspace.task_dir / "macros" / "user_macro_draft.ijm"
    manifest_path = workspace.task_dir / "review" / "macro_editor_manifest.json"
    assert draft_path.exists()
    assert manifest_path.exists()
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["formal_analysis_macro_ready"] is False

    run_button.click()
    result_text = widget.findChild(QTextEdit, "imageWorkbenchResultPanel").toPlainText()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert "ImageJ macro 调用完成" in result_text
    assert "status=macro_editor_ready" in result_text
    assert payload["external_engine_execution_enabled"] is True
    assert payload["execution_result"]["succeeded"] is True
