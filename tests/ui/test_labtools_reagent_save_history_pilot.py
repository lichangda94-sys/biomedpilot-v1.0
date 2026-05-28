from __future__ import annotations

import json
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


def _open_reagent(window: MainWindow) -> None:
    window.show_labtools()
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("semanticKey") == PageKey.LABTOOLS_REAGENT_PREPARATION.value
    )
    button.click()


def test_reagent_pilot_saves_template_and_preparation_record(qt_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    project_root = tmp_path / "project"
    home.mkdir()
    project_root.mkdir()
    monkeypatch.setenv("HOME", str(home))

    window = MainWindow()
    try:
        window.set_labtools_project_root(project_root)
        window._welcome_page.enter_workspace()
        _open_reagent(window)

        save_template = window.findChild(QPushButton, "labtoolsReagentSaveTemplateButton")
        save_record = window.findChild(QPushButton, "labtoolsReagentSaveRecordButton")
        history_list = window.findChild(QListWidget, "labtoolsReagentHistoryList")
        status = window.findChild(QLabel, "labtoolsReagentHistoryStatus")

        assert save_template.isEnabled()
        assert save_record.isEnabled()
        assert save_template.property("disabledState") == ""
        assert save_record.property("disabledState") == ""

        save_template.click()
        window.findChild(QPushButton, "labtoolsReagentCalculateButton").click()
        save_record.click()

        templates_file = project_root / "project_storage" / "labtools" / "templates" / "reagent_templates.json"
        legacy_records_file = project_root / "project_storage" / "labtools" / "records" / "reagent_preparations.json"
        record_index_file = project_root / "project_storage" / "labtools" / "labtools_record_index.json"
        assert templates_file.exists()
        assert record_index_file.exists()
        assert str(templates_file.resolve()).startswith(str((project_root / "project_storage" / "labtools").resolve()))
        assert str(record_index_file.resolve()).startswith(str((project_root / "project_storage" / "labtools").resolve()))
        assert not legacy_records_file.exists()
        assert not (home / ".labtools").exists()

        templates_payload = json.loads(templates_file.read_text(encoding="utf-8"))
        records = labtools_runtime.list_local_record_summaries(project_root, record_type="reagent_preparation")
        assert templates_payload["templates"]
        assert records

        assert history_list.count() >= 1
        assert "本地实验记录摘要" in status.text()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_reagent_pilot_missing_project_context_keeps_save_disabled(qt_app) -> None:
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        _open_reagent(window)
        save_template = window.findChild(QPushButton, "labtoolsReagentSaveTemplateButton")
        save_record = window.findChild(QPushButton, "labtoolsReagentSaveRecordButton")

        assert not save_template.isEnabled()
        assert not save_record.isEnabled()
        assert save_template.property("disabledState") == "disabled_missing_storage_adapter"
        assert save_record.property("disabledState") == "disabled_missing_storage_adapter"
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_reagent_pilot_legacy_corrupted_history_json_is_ignored_after_record_index_migration(qt_app, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    records_dir = project_root / "project_storage" / "labtools" / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    (records_dir / "reagent_preparations.json").write_text("{bad-json", encoding="utf-8")

    window = MainWindow()
    try:
        window.set_labtools_project_root(project_root)
        window._welcome_page.enter_workspace()
        _open_reagent(window)

        status = window.findChild(QLabel, "labtoolsReagentHistoryStatus")
        assert "JSON" not in status.text()
        assert "暂无本地配制记录摘要" in status.text()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
