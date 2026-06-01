from __future__ import annotations

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
    from PySide6.QtWidgets import QLabel, QPushButton

    parts = [label.text() for label in widget.findChildren(QLabel)]
    parts.extend(button.text() for button in widget.findChildren(QPushButton))
    return "\n".join(part for part in parts if part)


def test_western_blot_roi_page_contains_five_workflow_sections_and_review_notice(qapp) -> None:
    from PySide6.QtWidgets import QComboBox, QFrame, QPushButton, QTabWidget

    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    tabs = widget._stack.currentWidget().findChild(QTabWidget, "westernBlotTabs")
    tabs.setCurrentIndex(tabs.count() - 1)
    page = tabs.currentWidget()
    text = _visible_text(page)

    assert tabs.tabText(tabs.currentIndex()) == "结果与灰度分析"
    assert page.property("uiPrimitive") == "labtools_c2_gated_workbench"
    assert page.property("connectionStatus") == "connected"
    assert page.property("formalActionEnabled") is False
    assert page.findChild(QFrame, "wbRoiHeader") is not None
    for object_name in ("wbImageImportSection", "wbPreprocessSection", "wbRoiEditorSection", "wbMeasurementResultSection", "wbNormalizationSection"):
        assert page.findChild(QFrame, object_name) is not None
    assert "自动预处理和灰度测量结果仅用于辅助分析" in text
    assert "图像分析引擎未准备好" in text
    combo = page.findChild(QComboBox, "wbRoiTypeCombo")
    assert [combo.itemText(index) for index in range(combo.count())] == ["目标蛋白", "内参蛋白", "总蛋白 / Lane", "背景"]
    preprocess = page.findChild(QPushButton, "wbPreprocessButton")
    assert preprocess is not None
    assert not preprocess.isEnabled()
    assert preprocess.property("buttonBehavior") == "disabled_external_engine_missing"
    assert "图像分析引擎未准备好" in preprocess.property("disabledReason")
    measure = page.findChild(QPushButton, "wbMeasureRoiButton")
    assert measure is not None
    assert measure.property("buttonBehavior") == "creates_wb_roi_run_request_without_running_engine"
    save = page.findChild(QPushButton, "wbSaveRoiButton")
    assert save is not None
    assert save.property("buttonBehavior") == "exports_manual_roi_csv_and_json"
    assert "运行 ImageJ macro" not in text


def test_western_blot_roi_page_can_generate_run_request_without_engine(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QPushButton, QTableWidget

    from app.labtools.image_analysis import ImageAnalysisTaskStore
    from app.labtools.ui.western_blot_roi_widgets import WesternBlotROIAnalysisWidget
    from app.labtools.western_blot import WBRectangleROI

    image_path = tmp_path / "wb.png"
    image_path.write_bytes(b"image")
    widget = WesternBlotROIAnalysisWidget(task_store=ImageAnalysisTaskStore(tmp_path / "tasks"))
    widget.set_image_path_for_testing(str(image_path))
    widget.add_roi_for_testing(WBRectangleROI("img", str(image_path), "target_band", 10, 20, 30, 12, label="Target Lane 1"))
    widget.findChild(QPushButton, "wbMeasureRoiButton").click()

    workspace = widget.latest_workspace()
    assert widget.findChild(QTableWidget, "wbRoiTable").rowCount() == 1
    assert workspace is not None
    assert workspace.run_request_path.exists()
    assert (workspace.task_dir / "rois" / "wb_rois.csv").exists()
