from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QFrame, QLineEdit, QPlainTextEdit, QPushButton, QScrollArea, QSplitter, QWidget

    from app import labtools_runtime
    from app.shell.main_window import MainWindow
    from app.shared.semantic_keys import PageKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    MainWindow = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    if not labtools_runtime.runtime_status().available:
        pytest.skip(labtools_runtime.runtime_status().message)
    return QApplication.instance() or QApplication([])


@pytest.fixture
def labtools_wb_window(qt_app):
    window = MainWindow()
    window._welcome_page.enter_workspace()
    window.show_labtools()
    _open_wb_loading(window)
    yield window
    window.close()
    window.deleteLater()
    qt_app.processEvents()


def _open_experiment_modules(window: MainWindow) -> None:
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("semanticKey") == PageKey.LABTOOLS_EXPERIMENT_MODULES.value
    )
    button.click()


def _open_wb_loading(window: MainWindow) -> None:
    _open_experiment_modules(window)
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == "wb_loading"
    )
    button.click()


def _content(window: MainWindow):
    return window.findChild(QScrollArea, "labtoolsShellPage").widget()


def test_wb_loading_page_opens_with_focused_structure(labtools_wb_window) -> None:
    content = _content(labtools_wb_window)
    labels = "\n".join(label.text() for label in content.findChildren(QLabel))
    substeps = content.findChildren(QLabel, "labtoolsWbSubstepTitle")
    left_column = content.findChild(QWidget, "labtoolsWbLeftColumn")
    workbench = content.findChild(QSplitter, "labtoolsWbWorkbenchColumns")
    preview = content.findChild(QFrame, "labtoolsWbLanePreviewPanel")

    assert content.property("pageKey") == "wb_loading"
    assert content.property("semanticKey") == PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value
    assert workbench is not None
    assert workbench.property("uiPrimitive") == "three_column_workbench"
    assert workbench.property("rightPanelMinWidth") == 280
    assert workbench.property("rightPanelMaxWidth") == 360
    assert workbench.count() == 3
    assert preview is not None
    assert preview.property("uiPrimitive") == "preview_card"
    assert preview.property("requiresNonFormalStatusChip") is True
    assert preview.property("formalResult") is False
    assert preview.property("fakeGelBands") is False
    assert preview.property("imageAnalysisEnabled") is False
    assert left_column is not None
    assert left_column.property("uiPrimitive") == "workbench_secondary_column"
    assert left_column.property("layoutPolishNoOverlap") is True
    assert content.findChild(QLabel, "labtoolsWbIssueRows") is not None
    assert [step.text() for step in substeps][:3] == ["1. 蛋白定量", "2. WB 上样计算", "3. SDS-PAGE 配胶"]
    assert "当前步骤" in labels
    assert "SDS-PAGE 配胶、图像分析、自动条带识别、抗体推荐" in labels


def test_wb_config_sample_table_and_result_rows_are_rendered(labtools_wb_window) -> None:
    content = _content(labtools_wb_window)
    inputs = {field.property("fieldId"): field.text() for field in content.findChildren(QLineEdit, "labtoolsWbInput")}
    sample_rows = content.findChildren(QLabel, "labtoolsWbSampleRow")
    result_rows = content.findChildren(QLabel, "labtoolsWbResultRow")
    detail = content.findChild(QPlainTextEdit, "labtoolsWbDetailText").toPlainText()

    assert inputs["target_protein_ug"] == "20"
    assert inputs["loading_buffer_factor"] == "4"
    assert inputs["final_volume_ul"] == "20"
    assert any("S1" in row.text() and "2" in row.text() and "control" in row.text() for row in sample_rows)
    assert any("S2" in row.text() and "1.5" in row.text() and "treatment low" in row.text() for row in sample_rows)
    assert any("S3" in row.text() and "0.8" in row.text() and "treatment high" in row.text() for row in sample_rows)
    assert any("S1" in row.text() and "sample 10.0 µL" in row.text() and "water 5.0 µL" in row.text() for row in result_rows)
    assert any("S2" in row.text() and "sample 13.3 µL" in row.text() and "water 1.7 µL" in row.text() for row in result_rows)
    assert "Western Blot 上样体系辅助计算草稿" in detail


def test_wb_s3_warning_is_visible_without_hiding_result_table(labtools_wb_window) -> None:
    warning_rows = labtools_wb_window.findChildren(QLabel, "labtoolsWbWarningRow")
    result_rows = labtools_wb_window.findChildren(QLabel, "labtoolsWbResultRow")
    issue = labtools_wb_window.findChild(QLabel, "labtoolsWbIssueRows")

    assert any(row.property("sampleId") == "S3" and "样本浓度不足" in row.text() for row in warning_rows)
    assert any(row.property("sampleId") == "S3" and "sample 25.0 µL" in row.text() and "water -10.0 µL" in row.text() for row in result_rows)
    assert issue.property("hasError") is True
    assert "上样计算结果需由实验人员复核后用于台面操作" in issue.text()


def test_wb_lane_preview_shows_samples_and_empty_lanes(labtools_wb_window) -> None:
    lane_cards = labtools_wb_window.findChildren(QLabel, "labtoolsWbLaneSample")
    lane_volumes = labtools_wb_window.findChildren(QLabel, "labtoolsWbLaneVolume")

    assert any(label.property("laneNumber") == 2 and label.text() == "S1" for label in lane_cards)
    assert any(label.property("laneNumber") == 3 and label.text() == "S2" for label in lane_cards)
    assert any(label.property("laneNumber") == 4 and label.text() == "S3" for label in lane_cards)
    assert any(label.property("laneNumber") == 2 and label.text() == "10.0 µL" for label in lane_volumes)
    assert any(label.property("laneNumber") == 4 and label.text() == "25.0 µL" for label in lane_volumes)
    assert any("Empty / 空白" in label.text() for label in lane_cards)
    assert any("Empty / 空白" in label.text() for label in lane_volumes)


def test_wb_actions_are_gated_and_forbidden_surfaces_absent(labtools_wb_window) -> None:
    labels = "\n".join(label.text() for label in labtools_wb_window.findChildren(QLabel))
    copy = labtools_wb_window.findChild(QPushButton, "labtoolsWbCopyTableButton")
    save = labtools_wb_window.findChild(QPushButton, "labtoolsWbSaveRecordButton")
    export = labtools_wb_window.findChild(QPushButton, "labtoolsWbExportButton")
    export_md = labtools_wb_window.findChild(QPushButton, "labtoolsWbExportMarkdownButton")
    export_csv = labtools_wb_window.findChild(QPushButton, "labtoolsWbExportCsvButton")
    history = labtools_wb_window.findChild(QPushButton, "labtoolsWbHistoryButton")

    assert copy.isEnabled()
    assert not save.isEnabled()
    assert not export.isEnabled()
    assert export_md.isEnabled()
    assert export_csv.isEnabled()
    assert not history.isEnabled()
    assert save.property("disabledState") == "disabled_missing_storage_adapter"
    assert export.property("disabledState") == "future"
    assert "SDS-PAGE 配胶结果表" not in labels
    assert "fake gel bands" not in labels
    assert "image analysis" not in labels
    assert "antibody recommendation" not in labels


def test_wb_loading_does_not_create_labtools_storage(qt_app, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        window.show_labtools()
        _open_wb_loading(window)
        window.findChild(QPushButton, "labtoolsWbCalculateButton").click()

        assert not (Path(tmp_path) / ".labtools").exists()
        assert list(Path(tmp_path).iterdir()) == []
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
