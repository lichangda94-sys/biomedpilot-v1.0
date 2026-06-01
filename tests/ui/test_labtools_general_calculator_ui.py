from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QRadioButton, QScrollArea

    from app import labtools_runtime
    from app.shell.main_window import MainWindow
    from app.shared.semantic_keys import PageKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QComboBox = None  # type: ignore[assignment]
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


def _content(window: MainWindow):
    return window.findChild(QScrollArea, "labtoolsShellPage").widget()


def _field(window: MainWindow, object_name: str, field_id: str) -> QLineEdit:
    return next(item for item in window.findChildren(QLineEdit, object_name) if item.property("fieldId") == field_id)


def _result_text(window: MainWindow, page_key: str) -> QPlainTextEdit:
    return next(item for item in window.findChildren(QPlainTextEdit, "labtoolsResultText") if item.property("pageKey") == page_key)


def _issue_label(window: MainWindow, page_key: str) -> QLabel:
    return next(item for item in window.findChildren(QLabel, "labtoolsIssueRows") if item.property("pageKey") == page_key)


def test_quick_calculator_task_list_is_rendered_from_backend_specs(labtools_general_window) -> None:
    combo = labtools_general_window.findChild(QComboBox, "labtoolsQuickTaskCombo")
    title = labtools_general_window.findChild(QLabel, "labToolsCalculatorTitle")
    backend_tasks = labtools_runtime.list_quick_tasks()
    task_ids = [combo.itemData(index) for index in range(combo.count())]
    labels = "\n".join(combo.itemText(index) for index in range(combo.count()))

    assert title.text() == "通用计算器"
    assert task_ids == [task.task_id for task in backend_tasks]
    assert "quick_dilution" in task_ids
    assert "quick_mass_molarity" in task_ids
    assert "quick_qpcr_mix" in task_ids
    assert "quick_cell_seeding" in task_ids
    assert "quick_wb_loading" in task_ids
    assert "BCA" not in labels
    assert "ELISA" not in labels
    assert "细胞实验记录" not in labels


def test_quick_dilution_form_calculates_result_and_keeps_save_export_disabled(labtools_general_window) -> None:
    combo = labtools_general_window.findChild(QComboBox, "labtoolsQuickTaskCombo")
    combo.setCurrentIndex(combo.findData("quick_dilution"))
    _field(labtools_general_window, "labtoolsQuickInput", "stock_concentration").setText("100")
    _field(labtools_general_window, "labtoolsQuickInput", "target_concentration").setText("10")
    _field(labtools_general_window, "labtoolsQuickInput", "final_volume").setText("1")

    labtools_general_window.findChild(QPushButton, "labtoolsQuickCalculateButton").click()

    result = _result_text(labtools_general_window, "quick_calculator").toPlainText()
    issue = _issue_label(labtools_general_window, "quick_calculator").text()
    copy_button = next(button for button in labtools_general_window.findChildren(QPushButton, "labtoolsCopyResultButton") if button.property("pageKey") == "quick_calculator")
    save_button = next(button for button in labtools_general_window.findChildren(QPushButton, "labtoolsSaveHistoryButton") if button.property("pageKey") == "quick_calculator")
    export_button = next(button for button in labtools_general_window.findChildren(QPushButton, "labtoolsExportResultButton") if button.property("pageKey") == "quick_calculator")

    assert "所需 stock 体积" in result
    assert "0.1 mL" in result
    assert "实验计算结果需由用户复核后使用" in issue
    assert copy_button.isEnabled()
    assert not save_button.isEnabled()
    assert not export_button.isEnabled()
    assert save_button.property("disabledState") == "disabled_missing_storage_adapter"
    assert export_button.property("disabledState") == "future"


def test_quick_invalid_input_shows_error_row_without_fake_result(labtools_general_window) -> None:
    combo = labtools_general_window.findChild(QComboBox, "labtoolsQuickTaskCombo")
    combo.setCurrentIndex(combo.findData("quick_dilution"))
    _field(labtools_general_window, "labtoolsQuickInput", "stock_concentration").setText("abc")

    labtools_general_window.findChild(QPushButton, "labtoolsQuickCalculateButton").click()

    primary = next(label for label in labtools_general_window.findChildren(QLabel, "labtoolsResultPrimary") if label.property("pageKey") == "quick_calculator")
    issue = _issue_label(labtools_general_window, "quick_calculator")
    result = _result_text(labtools_general_window, "quick_calculator").toPlainText()

    assert "未生成结果" in primary.text() or primary.text() == "输入需要调整"
    assert issue.property("hasError") is True
    assert "abc" in issue.text() or "stock" in issue.text()
    assert "所需 stock 体积" not in result


def test_formula_solver_renders_formula_list_solve_target_and_calculates(labtools_general_window) -> None:
    formula_mode = next(button for button in labtools_general_window.findChildren(QPushButton, "labtoolsGeneralModeButton") if button.property("modeKey") == "formula_solver")
    formula_mode.click()
    combo = labtools_general_window.findChild(QComboBox, "labtoolsFormulaSpecCombo")
    backend_specs = labtools_runtime.list_formula_specs()
    target_buttons = labtools_general_window.findChildren(QRadioButton, "labtoolsFormulaSolveTarget")

    assert [combo.itemData(index) for index in range(combo.count())] == [spec.spec_id for spec in backend_specs]
    assert target_buttons
    assert any(button.property("targetId") == "molar_concentration" for button in target_buttons)
    assert labtools_general_window.findChild(QLabel, "labtoolsFormulaExpression").text().startswith("公式：")

    labtools_general_window.findChild(QPushButton, "labtoolsFormulaCalculateButton").click()

    result = _result_text(labtools_general_window, "formula_solver").toPlainText()
    issue = _issue_label(labtools_general_window, "formula_solver").text()
    save_button = next(button for button in labtools_general_window.findChildren(QPushButton, "labtoolsSaveHistoryButton") if button.property("pageKey") == "formula_solver")
    export_button = next(button for button in labtools_general_window.findChildren(QPushButton, "labtoolsExportResultButton") if button.property("pageKey") == "formula_solver")

    assert "输入摘要" in result
    assert "摩尔浓度" in result
    assert "复核提示" in result
    assert "实验计算结果需由用户复核后使用" in issue
    assert not save_button.isEnabled()
    assert not export_button.isEnabled()


def test_formula_solver_invalid_input_shows_error(labtools_general_window) -> None:
    formula_mode = next(button for button in labtools_general_window.findChildren(QPushButton, "labtoolsGeneralModeButton") if button.property("modeKey") == "formula_solver")
    formula_mode.click()
    _field(labtools_general_window, "labtoolsFormulaInput", "mass_concentration").setText("bad-value")

    labtools_general_window.findChild(QPushButton, "labtoolsFormulaCalculateButton").click()

    issue = _issue_label(labtools_general_window, "formula_solver")
    result = _result_text(labtools_general_window, "formula_solver").toPlainText()

    assert issue.property("hasError") is True
    assert "bad-value" in issue.text() or "质量浓度" in issue.text()
    assert "计算公式" not in result


def test_general_calculator_does_not_create_labtools_storage(qt_app, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        window.show_labtools()
        _open_general_calculator(window)
        window.findChild(QPushButton, "labtoolsQuickCalculateButton").click()

        assert not (Path(tmp_path) / ".labtools").exists()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
