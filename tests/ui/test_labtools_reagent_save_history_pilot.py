from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QPushButton

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
        records_file = project_root / "project_storage" / "labtools" / "records" / "reagent_preparations.json"
        assert templates_file.exists()
        assert records_file.exists()
        assert str(templates_file.resolve()).startswith(str((project_root / "project_storage" / "labtools").resolve()))
        assert str(records_file.resolve()).startswith(str((project_root / "project_storage" / "labtools").resolve()))
        assert not (home / ".labtools").exists()

        templates_payload = json.loads(templates_file.read_text(encoding="utf-8"))
        records_payload = json.loads(records_file.read_text(encoding="utf-8"))
        assert templates_payload["templates"]
        assert records_payload["records"]

        assert history_list.count() >= 1
        assert "Saved to project storage" in status.text() or "已保存到项目存储" in status.text()
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


def test_reagent_pilot_corrupted_history_json_shows_error_state(qt_app, tmp_path: Path) -> None:
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
        assert "JSON" in status.text() or "读取失败" in status.text()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
