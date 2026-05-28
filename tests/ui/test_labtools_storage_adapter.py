from __future__ import annotations

import os
from pathlib import Path

import pytest

from app import labtools_runtime
from app.labtools_storage_adapter import BioMedPilotLabToolsStorageAdapter

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton

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


def test_adapter_resolves_project_storage_labtools_paths(tmp_path: Path) -> None:
    adapter = BioMedPilotLabToolsStorageAdapter.from_project_root(tmp_path)
    paths = adapter.resolve_paths()

    assert paths.project_root == tmp_path.resolve()
    assert paths.project_storage_root == tmp_path / "project_storage"
    assert paths.labtools_root == tmp_path / "project_storage" / "labtools"
    assert paths.templates == tmp_path / "project_storage" / "labtools" / "templates"
    assert paths.records == tmp_path / "project_storage" / "labtools" / "records"
    assert paths.exports == tmp_path / "project_storage" / "labtools" / "exports"
    assert paths.attachments == tmp_path / "project_storage" / "labtools" / "attachments"
    assert paths.diagnostics == tmp_path / "project_storage" / "labtools" / "diagnostics"


def test_diagnose_does_not_create_project_storage(tmp_path: Path) -> None:
    adapter = BioMedPilotLabToolsStorageAdapter.from_project_root(tmp_path)
    state = adapter.diagnose()

    assert state.status == "missing_project_storage"
    assert not (tmp_path / "project_storage").exists()
    assert not state.save_enabled
    assert not state.export_enabled
    assert not state.history_enabled


def test_ensure_readiness_without_create_missing_does_not_create_directories(tmp_path: Path) -> None:
    adapter = BioMedPilotLabToolsStorageAdapter.from_project_root(tmp_path)
    state = adapter.ensure_readiness(create_missing=False)

    assert state.status == "missing_project_storage"
    assert not (tmp_path / "project_storage").exists()
    assert state.created_paths == ()


def test_ensure_readiness_with_create_missing_creates_only_project_storage_layout(tmp_path: Path) -> None:
    adapter = BioMedPilotLabToolsStorageAdapter.from_project_root(tmp_path)
    state = adapter.ensure_readiness(create_missing=True)
    paths = adapter.resolve_paths()

    assert state.status == "ready_read_only"
    assert state.created_paths
    for directory in paths.required_directories:
        assert directory.is_dir()
        directory.relative_to(tmp_path)
    assert not state.save_enabled
    assert not state.export_enabled
    assert not state.history_enabled


def test_adapter_does_not_use_home_labtools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    monkeypatch.setenv("HOME", str(home))

    adapter = BioMedPilotLabToolsStorageAdapter.from_project_root(project)
    adapter.ensure_readiness(create_missing=True)

    assert not (home / ".labtools").exists()
    assert not any(".labtools" in str(path) for path in adapter.resolve_paths().required_directories)


def test_runtime_status_without_project_context_keeps_persistence_disabled() -> None:
    state = labtools_runtime.get_labtools_storage_adapter_status(None)

    assert state.status == "missing_project_context"
    assert state.paths is None
    assert not state.save_enabled
    assert not state.export_enabled
    assert not state.history_enabled


def test_runtime_status_with_project_context_is_read_only_and_non_creating(tmp_path: Path) -> None:
    state = labtools_runtime.get_labtools_storage_adapter_status(tmp_path)

    assert state.status == "missing_project_storage"
    assert not (tmp_path / "project_storage").exists()
    assert not state.save_enabled
    assert not state.export_enabled
    assert not state.history_enabled


def test_labtools_ui_save_export_history_buttons_remain_disabled(qt_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        window.show_labtools()
        button = next(
            item
            for item in window.findChildren(QPushButton, "labtoolsEntryButton")
            if item.property("semanticKey") == PageKey.LABTOOLS_GENERAL_CALCULATORS.value
        )
        button.click()

        save_buttons = window.findChildren(QPushButton, "labtoolsSaveHistoryButton")
        export_buttons = window.findChildren(QPushButton, "labtoolsExportResultButton")

        assert save_buttons
        assert export_buttons
        assert all(not button.isEnabled() for button in save_buttons)
        assert all(not button.isEnabled() for button in export_buttons)
        assert all(button.property("disabledState") in {"disabled_missing_storage_adapter", "future"} for button in save_buttons + export_buttons)
        assert not (tmp_path / ".labtools").exists()
        assert not (tmp_path / "project_storage").exists()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
