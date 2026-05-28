from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

    import app.shell.main_window as main_window_module
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


def _open_primary(window: MainWindow, semantic_key: str) -> None:
    window.show_labtools()
    window._show_labtools_home()
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("semanticKey") == semantic_key
    )
    button.click()


def _open_experiment_page(window: MainWindow, page_key: str) -> None:
    _open_primary(window, PageKey.LABTOOLS_EXPERIMENT_MODULES.value)
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == page_key
    )
    button.click()


def test_reagent_export_buttons_record_file_picker_contract(qt_app) -> None:
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        _open_primary(window, PageKey.LABTOOLS_REAGENT_PREPARATION.value)
        markdown = window.findChild(QPushButton, "labtoolsReagentExportMarkdownButton")
        csv = window.findChild(QPushButton, "labtoolsReagentExportCsvButton")

        assert markdown.property("exportRequiresFilePicker") is True
        assert markdown.property("exportFormat") == "markdown"
        assert csv.property("exportRequiresFilePicker") is True
        assert csv.property("exportFormat") == "csv"
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_wb_export_buttons_record_file_picker_contract(qt_app) -> None:
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        _open_experiment_page(window, "wb_loading")
        markdown = window.findChild(QPushButton, "labtoolsWbExportMarkdownButton")
        csv = window.findChild(QPushButton, "labtoolsWbExportCsvButton")

        assert markdown.property("exportRequiresFilePicker") is True
        assert markdown.property("exportFormat") == "markdown"
        assert csv.property("exportRequiresFilePicker") is True
        assert csv.property("exportFormat") == "csv"
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_reagent_file_picker_cancel_reports_no_write(qt_app, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main_window_module.QFileDialog, "getSaveFileName", lambda *_args, **_kwargs: ("", ""))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        _open_primary(window, PageKey.LABTOOLS_REAGENT_PREPARATION.value)
        window.findChild(QPushButton, "labtoolsReagentExportMarkdownButton").click()

        issue = window.findChild(QLabel, "labtoolsReagentIssueRows")
        assert "导出已取消" in issue.text()
        assert "未写入任何文件" in issue.text()
        assert issue.property("hasError") is False
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_wb_file_picker_cancel_reports_no_write(qt_app, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main_window_module.QFileDialog, "getSaveFileName", lambda *_args, **_kwargs: ("", ""))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        _open_experiment_page(window, "wb_loading")
        window.findChild(QPushButton, "labtoolsWbExportCsvButton").click()

        issue = window.findChild(QLabel, "labtoolsWbIssueRows")
        assert "导出已取消" in issue.text()
        assert "未写入任何文件" in issue.text()
        assert issue.property("hasError") is False
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_file_picker_suffix_hardening_appends_expected_suffix(qt_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target_without_suffix = tmp_path / "picked" / "reagent_export"
    monkeypatch.setattr(main_window_module.QFileDialog, "getSaveFileName", lambda *_args, **_kwargs: (str(target_without_suffix), ""))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        _open_primary(window, PageKey.LABTOOLS_REAGENT_PREPARATION.value)
        window.findChild(QPushButton, "labtoolsReagentExportMarkdownButton").click()

        expected = target_without_suffix.with_suffix(".md")
        assert expected.exists()
        assert not target_without_suffix.exists()
        assert "BioMedPilot LabTools Reagent Preparation" in expected.read_text(encoding="utf-8")
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_home_labtools_export_rejection_reaches_ui_error_row(qt_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    blocked_path = home / ".labtools" / "blocked.csv"
    monkeypatch.setattr(main_window_module.QFileDialog, "getSaveFileName", lambda *_args, **_kwargs: (str(blocked_path), ""))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        _open_experiment_page(window, "wb_loading")
        window.findChild(QPushButton, "labtoolsWbExportCsvButton").click()

        issue = window.findChild(QLabel, "labtoolsWbIssueRows")
        assert "拒绝写入 ~/.labtools" in issue.text()
        assert issue.property("hasError") is True
        assert not blocked_path.exists()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
