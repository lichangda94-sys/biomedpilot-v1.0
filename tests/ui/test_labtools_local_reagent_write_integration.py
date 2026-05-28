from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton

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


def _open_reagent(window: MainWindow) -> None:
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("semanticKey") == PageKey.LABTOOLS_REAGENT_PREPARATION.value
    )
    button.click()


def _window(qt_app, project_root: Path) -> MainWindow:
    window = MainWindow()
    window.set_labtools_project_root(project_root)
    window._welcome_page.enter_workspace()
    window.show_labtools()
    _open_reagent(window)
    return window


def _field(window: MainWindow, field_id: str) -> QLineEdit:
    return [item for item in window.findChildren(QLineEdit, "labtoolsLocalReagentInput") if item.property("fieldId") == field_id][-1]


def _write_status(window: MainWindow) -> QLabel:
    return window.findChildren(QLabel, "labtoolsLocalReagentWriteStatus")[-1]


def _reagent_rows(window: MainWindow) -> list[QPushButton]:
    return window.findChildren(QPushButton, "labtoolsLocalReagentRow")


def _load_store(project_root: Path):
    labtools_runtime._ensure_labtools_importable()
    from labtools.local_data import LocalLabToolsDataStore

    return LocalLabToolsDataStore(project_root / "project_storage" / "labtools")


def test_reagent_ui_creates_updates_and_archives_local_reagent(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    window = _window(qt_app, project)
    try:
        _field(window, "name").setText("Tris-HCl")
        _field(window, "category").setText("buffer")
        _field(window, "concentration").setText("1 M")
        _field(window, "storage_location").setText("4C fridge / Box A")
        window.findChild(QPushButton, "labtoolsLocalReagentCreateButton").click()
        qt_app.processEvents()

        row = _reagent_rows(window)[-1]
        status = _write_status(window)
        assert row is not None
        assert row.property("reagentName") == "Tris-HCl"
        assert row.property("version") == 1
        assert "已保存到本地 LabTools 数据库" in status.text()

        row.click()
        _field(window, "concentration").setText("2 M")
        window.findChild(QPushButton, "labtoolsLocalReagentUpdateButton").click()
        qt_app.processEvents()
        updated_row = _reagent_rows(window)[-1]
        assert updated_row.property("version") == 2
        assert "2 M" in updated_row.text()

        updated_row.click()
        window.findChild(QPushButton, "labtoolsLocalReagentArchiveButton").click()
        qt_app.processEvents()
        assert _load_store(project).list_reagents() == ()

        snapshot = _load_store(project).load_store()
        assert snapshot.reagents[0].status == "archived"
        assert [entry.action for entry in snapshot.audit_log] == ["create", "update", "archive"]
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_reagent_ui_blocks_stale_version_and_keeps_preparation_template(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    window = _window(qt_app, project)
    try:
        _field(window, "name").setText("Tris-HCl")
        window.findChild(QPushButton, "labtoolsLocalReagentCreateButton").click()
        qt_app.processEvents()
        row = _reagent_rows(window)[-1]
        row.click()

        _load_store(project).update_reagent(row.property("reagentId"), {"concentration": "1 M"}, expected_version=1)
        _field(window, "category").setText("buffer")
        window.findChild(QPushButton, "labtoolsLocalReagentUpdateButton").click()
        qt_app.processEvents()

        status = _write_status(window)
        labels = "\n".join(label.text() for label in window.findChildren(QLabel))
        assert status.property("status") == "blocked_version_conflict"
        assert "version_conflict" in status.text()
        assert "PBS 1x 示例模板" in labels
        assert "不会扣减库存" in labels
        assert not (project / "project_storage" / "labtools" / "templates" / "reagent_templates.json").exists()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_reagent_write_ui_does_not_import_store_directly_and_future_adapters_disabled() -> None:
    source = Path("app/shell/main_window.py").read_text(encoding="utf-8")
    lan = labtools_runtime.get_labtools_local_data_status(Path("/tmp/nonexistent-labtools-project"), data_source_mode="future_lan")
    cloud = labtools_runtime.get_labtools_local_data_status(Path("/tmp/nonexistent-labtools-project"), data_source_mode="future_cloud")

    assert "LocalLabToolsDataStore" not in source
    assert "labtools.local_data" not in source
    assert lan.status == "disabled_future_option"
    assert cloud.status == "disabled_future_option"
