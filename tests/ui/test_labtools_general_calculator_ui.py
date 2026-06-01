from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QTabWidget, QTextEdit

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
def labtools_general_window(qt_app):
    window = MainWindow()
    window._welcome_page.enter_workspace()
    window.show_labtools()
    _open_general_calculator(window)
    yield window
    window.close()
    window.deleteLater()
    qt_app.processEvents()


def _open_general_calculator(window: MainWindow) -> None:
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("semanticKey") == PageKey.LABTOOLS_GENERAL_CALCULATORS.value
    )
    button.click()


def _calculator_page(window: MainWindow):
    return window._labtools_page.current_page_widget()


def _quick_tabs(window: MainWindow) -> QTabWidget:
    tabs = window.findChild(QTabWidget, "labToolsQuickCalculatorTabs")
    assert tabs is not None
    return tabs


def _current_quick_tab(window: MainWindow):
    return _quick_tabs(window).currentWidget()


def _result_text(widget) -> str:
    result = widget.findChild(QTextEdit, "labToolsResultPanel")
    assert result is not None
    return result.toPlainText()


def test_general_calculator_current_workspace_is_rendered(labtools_general_window) -> None:
    page = _calculator_page(labtools_general_window)
    title = labtools_general_window.findChild(QLabel, "labToolsCalculatorTitle")
    calculator_tabs = labtools_general_window.findChild(QTabWidget, "labToolsCalculatorTabs")
    quick_tabs = _quick_tabs(labtools_general_window)

    assert labtools_general_window._labtools_page.current_page_key() == "general_calculators"
    assert labtools_general_window._labtools_page.property("semanticKey") == PageKey.LABTOOLS_GENERAL_CALCULATORS.value
    assert page.objectName() == "labToolsCalculatorWorkspace"
    assert page.property("connectionStatus") == "connected"
    assert title.text() == "通用计算器"
    assert [calculator_tabs.tabText(index) for index in range(calculator_tabs.count())] == ["快速计算", "试剂制备"]
    assert [quick_tabs.tabText(index) for index in range(quick_tabs.count())] == ["浓度换算", "稀释计算", "溶液配制"]


def test_general_calculator_buttons_have_current_release_contracts(labtools_general_window) -> None:
    gaps: list[str] = []
    for button in _calculator_page(labtools_general_window).findChildren(QPushButton):
        if button.property("buttonBehavior") is None:
            gaps.append(f"{button.objectName()}:{button.text()}:missing-buttonBehavior")
        if not button.isEnabled() and button.property("disabledReason") is None:
            gaps.append(f"{button.objectName()}:{button.text()}:missing-disabledReason")

    assert gaps == []


def test_dilution_calculator_generates_result_and_enables_copy(labtools_general_window) -> None:
    quick_tabs = _quick_tabs(labtools_general_window)
    quick_tabs.setCurrentIndex(next(index for index in range(quick_tabs.count()) if quick_tabs.tabText(index) == "稀释计算"))
    tab = _current_quick_tab(labtools_general_window)
    fields = tab.findChildren(QLineEdit)
    fields[0].setText("10")
    fields[1].setText("100")
    fields[2].setText("1")
    copy_button = next(button for button in tab.findChildren(QPushButton) if button.text() == "复制结果")

    assert not copy_button.isEnabled()
    tab.findChild(QPushButton, "primaryButton").click()

    result = _result_text(tab)
    assert "所需 stock 体积" in result
    assert "人工核对提示" in result
    assert "使用前需人工核对" in result
    assert copy_button.isEnabled()


def test_dilution_invalid_input_shows_error_without_fake_result(labtools_general_window) -> None:
    quick_tabs = _quick_tabs(labtools_general_window)
    quick_tabs.setCurrentIndex(next(index for index in range(quick_tabs.count()) if quick_tabs.tabText(index) == "稀释计算"))
    tab = _current_quick_tab(labtools_general_window)
    tab.findChildren(QLineEdit)[0].setText("bad-value")

    tab.findChild(QPushButton, "primaryButton").click()

    result = _result_text(tab)
    assert "输入需要调整" in result
    assert "stock 浓度必须是有效数字" in result
    assert "所需 stock 体积" not in result


def test_solution_preparation_calculator_generates_reviewable_result(labtools_general_window) -> None:
    quick_tabs = _quick_tabs(labtools_general_window)
    quick_tabs.setCurrentIndex(next(index for index in range(quick_tabs.count()) if quick_tabs.tabText(index) == "溶液配制"))
    tab = _current_quick_tab(labtools_general_window)
    fields = tab.findChildren(QLineEdit)
    fields[0].setText("1")
    fields[1].setText("10")
    fields[2].setText("")

    tab.findChild(QPushButton, "primaryButton").click()

    result = _result_text(tab)
    assert "输入摘要" in result
    assert "需要称量质量" in result
    assert "请人工复核计算结果后再用于实验" in result


def test_general_calculator_calculation_does_not_create_labtools_storage(qt_app, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        window.show_labtools()
        _open_general_calculator(window)
        quick_tabs = _quick_tabs(window)
        quick_tabs.setCurrentIndex(next(index for index in range(quick_tabs.count()) if quick_tabs.tabText(index) == "稀释计算"))
        _current_quick_tab(window).findChild(QPushButton, "primaryButton").click()

        assert not (Path(tmp_path) / ".labtools").exists()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
