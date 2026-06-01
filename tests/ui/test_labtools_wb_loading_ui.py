from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QScrollArea, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit

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
    return QApplication.instance() or QApplication([])


@pytest.fixture
def labtools_wb_window(qt_app):
    window = MainWindow()
    window._welcome_page.enter_workspace()
    window.show_labtools()
    _open_wb_workspace(window)
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


def _open_wb_workspace(window: MainWindow) -> None:
    _open_experiment_modules(window)
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == "protein_experiments"
    )
    button.click()


def _content(window: MainWindow):
    return window.findChild(QScrollArea, "labToolsWesternBlotScroll").widget()


def test_wb_workspace_opens_from_current_figma_second_level_list(labtools_wb_window) -> None:
    content = _content(labtools_wb_window)
    tabs = labtools_wb_window.findChild(QTabWidget, "westernBlotTabs")
    labels = "\n".join(label.text() for label in content.findChildren(QLabel))

    assert labtools_wb_window._labtools_page.current_page_key() == "protein_experiments"
    assert labtools_wb_window._labtools_page.property("semanticKey") == PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value
    assert content.objectName() == "labToolsWesternBlotContent"
    assert tabs is not None
    assert tabs.count() >= 5
    assert [tabs.tabText(index) for index in range(5)] == [
        "流程工作台",
        "蛋白样品准备",
        "BCA 蛋白浓度测定",
        "蛋白上样计算",
        "配胶与 Lane 布局",
    ]
    assert "Western Blot" in labels
    assert "当前不启用 WB 图像分析的自动 lane/band 识别" in labels


def test_wb_workspace_buttons_have_current_release_contracts(labtools_wb_window) -> None:
    gaps: list[str] = []
    for button in _content(labtools_wb_window).findChildren(QPushButton):
        if button.property("buttonBehavior") is None:
            gaps.append(f"{button.objectName()}:{button.text()}:missing-buttonBehavior")
        if not button.isEnabled() and button.property("disabledReason") is None:
            gaps.append(f"{button.objectName()}:{button.text()}:missing-disabledReason")

    assert gaps == []


def test_wb_protein_loading_calculation_generates_lane_layout(labtools_wb_window) -> None:
    tabs = labtools_wb_window.findChild(QTabWidget, "westernBlotTabs")
    tabs.setCurrentIndex(next(index for index in range(tabs.count()) if tabs.tabText(index) == "蛋白上样计算"))
    table = labtools_wb_window.findChild(QTableWidget, "proteinLoadingSampleTable")
    table.setItem(0, 0, QTableWidgetItem("S1"))
    table.setItem(0, 1, QTableWidgetItem("2"))

    labtools_wb_window.findChild(QPushButton, "proteinLoadingCalculateButton").click()

    result_text = labtools_wb_window.findChild(QTextEdit, "proteinLoadingResultPanel").toPlainText()
    lane_text = labtools_wb_window.findChild(QTextEdit, "wbLoadingLaneLayoutPanel").toPlainText()
    assert "Western Blot 上样体系辅助计算草稿" in result_text
    assert "Lane 1" in lane_text
    assert "Protein Marker" in lane_text
    assert "S1" in lane_text


def test_wb_result_analysis_tab_is_gated_not_auto_image_analysis(labtools_wb_window) -> None:
    tabs = labtools_wb_window.findChild(QTabWidget, "westernBlotTabs")
    tabs.setCurrentIndex(tabs.count() - 1)
    text = "\n".join(
        [label.text() for label in tabs.currentWidget().findChildren(QLabel)]
        + [panel.toPlainText() for panel in tabs.currentWidget().findChildren(QTextEdit)]
    )

    assert tabs.tabText(tabs.currentIndex()) == "结果与灰度分析"
    assert "图像分析引擎未准备好" in text
    assert "运行 ImageJ macro" not in text


def test_wb_calculation_does_not_create_labtools_storage(qt_app, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        window.show_labtools()
        _open_wb_workspace(window)
        window.findChild(QPushButton, "proteinLoadingCalculateButton").click()

        assert not (Path(tmp_path) / ".labtools").exists()
        assert list(Path(tmp_path).iterdir()) == []
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
