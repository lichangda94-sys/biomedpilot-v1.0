from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QPushButton

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
    return QApplication.instance() or QApplication([])


def _open_wb(window: MainWindow) -> None:
    window.show_labtools()
    module_button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("semanticKey") == PageKey.LABTOOLS_EXPERIMENT_MODULES.value
    )
    module_button.click()
    wb_button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == "wb_loading"
    )
    wb_button.click()


def test_wb_pilot_saves_record_in_project_storage(qt_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    project_root = tmp_path / "project"
    home.mkdir()
    project_root.mkdir()
    monkeypatch.setenv("HOME", str(home))

    window = MainWindow()
    try:
        window.set_labtools_project_root(project_root)
        window._welcome_page.enter_workspace()
        _open_wb(window)

        save = window.findChild(QPushButton, "labtoolsWbSaveRecordButton")
        export = window.findChild(QPushButton, "labtoolsWbExportButton")
        history_button = window.findChild(QPushButton, "labtoolsWbHistoryButton")
        history_list = window.findChild(QListWidget, "labtoolsWbHistoryList")
        history_status = window.findChild(QLabel, "labtoolsWbHistoryStatus")

        assert save.isEnabled()
        assert history_button.isEnabled()
        assert not export.isEnabled()

        save.click()
        history_button.click()

        legacy_records_file = project_root / "project_storage" / "labtools" / "records" / "wb_loading_records.json"
        record_index_file = project_root / "project_storage" / "labtools" / "labtools_record_index.json"
        assert record_index_file.exists()
        assert str(record_index_file.resolve()).startswith(str((project_root / "project_storage" / "labtools").resolve()))
        assert not legacy_records_file.exists()
        assert not (home / ".labtools").exists()

        records = labtools_runtime.list_local_record_summaries(project_root, record_type="wb_loading")
        assert records
        assert history_list.count() >= 1
        assert "本地实验记录摘要" in history_status.text()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_wb_pilot_missing_project_context_keeps_save_history_disabled(qt_app) -> None:
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        _open_wb(window)

        save = window.findChild(QPushButton, "labtoolsWbSaveRecordButton")
        history = window.findChild(QPushButton, "labtoolsWbHistoryButton")
        assert not save.isEnabled()
        assert not history.isEnabled()
        assert save.property("disabledState") == "disabled_missing_storage_adapter"
        assert history.property("disabledState") == "disabled_missing_storage_adapter"
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_wb_pilot_legacy_corrupted_json_is_ignored_after_record_index_migration(qt_app, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    records_dir = project_root / "project_storage" / "labtools" / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    (records_dir / "wb_loading_records.json").write_text("{bad-json", encoding="utf-8")

    window = MainWindow()
    try:
        window.set_labtools_project_root(project_root)
        window._welcome_page.enter_workspace()
        _open_wb(window)

        status = window.findChild(QLabel, "labtoolsWbHistoryStatus")
        assert "JSON" not in status.text()
        assert "暂无 WB 本地记录摘要" in status.text()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
