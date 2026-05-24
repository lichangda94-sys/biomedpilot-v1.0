from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QScrollArea

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
def labtools_reagent_window(qt_app):
    window = MainWindow()
    window._welcome_page.enter_workspace()
    window.show_labtools()
    _open_reagent_preparation(window)
    yield window
    window.close()
    window.deleteLater()
    qt_app.processEvents()


def _open_reagent_preparation(window: MainWindow) -> None:
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("semanticKey") == PageKey.LABTOOLS_REAGENT_PREPARATION.value
    )
    button.click()


def _content(window: MainWindow):
    return window.findChild(QScrollArea, "labtoolsShellPage").widget()


def _input(window: MainWindow, field_id: str) -> QLineEdit:
    return next(item for item in window.findChildren(QLineEdit, "labtoolsReagentInput") if item.property("fieldId") == field_id)


def test_reagent_preparation_renders_three_panel_safe_ui(labtools_reagent_window) -> None:
    content = _content(labtools_reagent_window)
    labels = "\n".join(label.text() for label in content.findChildren(QLabel))

    assert content.property("pageKey") == "reagent_preparation"
    assert content.property("semanticKey") == PageKey.LABTOOLS_REAGENT_PREPARATION.value
    assert content.findChild(QLabel, "labtoolsReagentResultPrimary") is not None
    assert content.findChild(QPushButton, "labtoolsReagentTemplateRow") is not None
    assert content.findChild(QLineEdit, "labtoolsReagentSearchInput") is not None
    assert "试剂模板列表" in labels
    assert "本次配制计算预览" in labels
    assert "模板详情 / 编辑侧栏" in labels
    assert "不默认写入 ~/.labtools" in labels


def test_pbs_template_detail_and_validation_are_visible(labtools_reagent_window) -> None:
    content = _content(labtools_reagent_window)
    labels = "\n".join(label.text() for label in content.findChildren(QLabel))
    component_rows = content.findChildren(QLabel, "labtoolsReagentComponentRow")
    validation_rows = content.findChildren(QLabel, "labtoolsReagentValidationRow")

    assert "PBS 1x 示例模板" in labels
    assert "缓冲液 / buffer" in labels
    assert "pH 目标：7.4" in labels
    assert any("NaCl" in row.text() for row in component_rows)
    assert any("Na2HPO4" in row.text() for row in component_rows)
    assert any("水合物形式需人工确认" in row.text() for row in validation_rows)
    assert "云模板库" not in labels
    assert "共享模板库" not in labels
    assert "库存扣减" not in labels
    assert "生产批次放行" not in labels
    assert "多用户同步" not in labels


def test_reagent_preparation_calculates_preview_and_keeps_review_notice(labtools_reagent_window) -> None:
    _input(labtools_reagent_window, "target_volume").setText("500")
    labtools_reagent_window.findChild(QPushButton, "labtoolsReagentCalculateButton").click()

    result_text = labtools_reagent_window.findChild(QPlainTextEdit, "labtoolsReagentResultText").toPlainText()
    primary = labtools_reagent_window.findChild(QLabel, "labtoolsReagentResultPrimary").text()
    issue = labtools_reagent_window.findChild(QLabel, "labtoolsReagentIssueRows")
    result_rows = labtools_reagent_window.findChildren(QLabel, "labtoolsReagentResultRow")

    assert "PBS 1x 示例模板" in primary
    assert "500 mL" in primary
    assert "本次制备摘要" in result_text
    assert "NaCl: 4 g" in result_text
    assert any("ddH2O" in row.text() and "500 mL" in row.text() for row in result_rows)
    assert "实验计算结果需由用户复核后使用" in issue.text()
    assert "不会写入 ~/.labtools" in issue.text()
    assert issue.property("hasError") in (False, None)


def test_reagent_actions_preserve_adapter_gates(labtools_reagent_window) -> None:
    copy = labtools_reagent_window.findChild(QPushButton, "labtoolsReagentCopySummaryButton")
    save_template = labtools_reagent_window.findChild(QPushButton, "labtoolsReagentSaveTemplateButton")
    save_record = labtools_reagent_window.findChild(QPushButton, "labtoolsReagentSaveRecordButton")
    export = labtools_reagent_window.findChild(QPushButton, "labtoolsReagentExportButton")
    export_md = labtools_reagent_window.findChild(QPushButton, "labtoolsReagentExportMarkdownButton")
    export_csv = labtools_reagent_window.findChild(QPushButton, "labtoolsReagentExportCsvButton")

    assert copy.isEnabled()
    assert not save_template.isEnabled()
    assert not save_record.isEnabled()
    assert not export.isEnabled()
    assert export_md.isEnabled()
    assert export_csv.isEnabled()
    assert save_template.property("disabledState") == "disabled_missing_storage_adapter"
    assert save_record.property("disabledState") == "disabled_missing_storage_adapter"
    assert export.property("disabledState") == "future"


def test_reagent_invalid_input_shows_error_without_saved_record(labtools_reagent_window) -> None:
    _input(labtools_reagent_window, "target_volume").setText("bad-value")
    labtools_reagent_window.findChild(QPushButton, "labtoolsReagentCalculateButton").click()

    issue = labtools_reagent_window.findChild(QLabel, "labtoolsReagentIssueRows")
    result = labtools_reagent_window.findChild(QPlainTextEdit, "labtoolsReagentResultText").toPlainText()

    assert issue.property("hasError") is True
    assert "bad-value" in issue.text() or "could not convert" in issue.text()
    assert "历史记录 ID" not in result


def test_reagent_page_does_not_create_labtools_storage(qt_app, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        window.show_labtools()
        _open_reagent_preparation(window)
        window.findChild(QPushButton, "labtoolsReagentCalculateButton").click()

        assert not (Path(tmp_path) / ".labtools").exists()
        assert list(Path(tmp_path).iterdir()) == []
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
