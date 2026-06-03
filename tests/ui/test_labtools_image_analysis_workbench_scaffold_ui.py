from __future__ import annotations

import json
import os

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
    from PySide6.QtWidgets import QFrame, QPushButton, QTabWidget

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
    assert "ImageJ/Fiji 本地后端状态" not in text
    for index, analysis_type in enumerate(("scratch_area", "transwell_count", "fluorescence_intensity")):
        page = tabs.widget(index)
        assert page.property("uiPrimitive") == "labtools_c2_gated_workbench"
        assert page.property("connectionStatus") == "connected"
        assert page.property("formalActionEnabled") is False
        assert page.property("analysisType") == analysis_type
        assert page.findChild(QFrame, "imageWorkbenchHeader") is not None
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
