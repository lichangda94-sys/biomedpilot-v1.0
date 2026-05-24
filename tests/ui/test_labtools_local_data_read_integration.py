from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QScrollArea

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


def _seed_local_data(project_root: Path) -> None:
    labtools_runtime._ensure_labtools_importable()
    from labtools.local_data import LocalLabToolsDataStore

    store = LocalLabToolsDataStore(project_root / "project_storage" / "labtools")
    store.initialize_store()
    reagent = store.create_reagent(
        {
            "name": "Tris-HCl",
            "category": "buffer",
            "concentration": "1 M",
            "storage_location": "4C fridge / Box A",
        }
    )
    sample = store.create_sample(
        {
            "sample_name": "Tumor lysate",
            "sample_type": "protein_lysate",
            "concentration": "2.0",
            "concentration_unit": "mg/mL",
            "storage_location": "-80C / Rack 1",
        }
    )
    cell = store.create_cell({"cell_name": "TPC-1", "passage": 12, "species": "human"})
    batch = store.create_freeze_batch({"cell_id": cell.id, "batch_name": "TPC-1_P12", "vial_count": 2})
    store.create_freeze_vial({"freeze_batch_id": batch.id, "vial_label": "TPC-1 P12 #01", "location": "LN2 A1"})
    store.create_record_index_entry(
        {
            "record_type": "wb_loading",
            "title": "WB loading draft",
            "linked_reagents": [reagent.id],
            "linked_samples": [sample.id],
            "linked_cells": [cell.id],
        }
    )


def _window(qt_app, project_root: Path | None = None) -> MainWindow:
    window = MainWindow()
    if project_root is not None:
        window.set_labtools_project_root(project_root)
    window._welcome_page.enter_workspace()
    window.show_labtools()
    window._show_labtools_home()
    return window


def _content(window: MainWindow):
    return window.findChild(QScrollArea, "labtoolsShellPage").widget()


def _labels(window: MainWindow) -> str:
    return "\n".join(label.text() for label in _content(window).findChildren(QLabel))


def _open_reagent(window: MainWindow) -> None:
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("semanticKey") == PageKey.LABTOOLS_REAGENT_PREPARATION.value
    )
    button.click()


def _open_experiment_modules(window: MainWindow) -> None:
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("semanticKey") == PageKey.LABTOOLS_EXPERIMENT_MODULES.value
    )
    button.click()


def _open_wb(window: MainWindow) -> None:
    _open_experiment_modules(window)
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == "wb_loading"
    )
    button.click()


def _open_cell_workspace(window: MainWindow) -> None:
    _open_experiment_modules(window)
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == "cell_experiment_workspace"
    )
    button.click()


def test_home_gracefully_shows_missing_local_data_store(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    window = _window(qt_app, project)
    try:
        status = window.findChild(QLabel, "labtoolsLocalDataStatusText")
        counts = window.findChild(QLabel, "labtoolsLocalDataCountRow")

        assert status is not None
        assert status.property("status") == "blocked"
        assert "not been initialized" in status.text()
        assert counts.property("reagentCount") == 0
        assert not (project / "project_storage").exists()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_home_shows_initialized_local_data_counts(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    _seed_local_data(project)
    window = _window(qt_app, project)
    try:
        counts = window.findChild(QLabel, "labtoolsLocalDataCountRow")
        labels = _labels(window)

        assert counts.property("reagentCount") == 1
        assert counts.property("sampleCount") == 1
        assert counts.property("cellCount") == 1
        assert counts.property("recordCount") == 1
        assert "数据源：本地模式" in labels
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_reagent_preparation_reads_local_reagent_summary(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    _seed_local_data(project)
    window = _window(qt_app, project)
    try:
        _open_reagent(window)
        row = window.findChild(QPushButton, "labtoolsLocalReagentRow")
        reference = window.findChild(QLabel, "labtoolsLocalReagentReference")

        assert row is not None
        assert row.property("reagentName") == "Tris-HCl"
        assert "4C fridge" in row.text()
        row.click()
        assert reference.property("reagentId") == row.property("reagentId")
        assert "已引用本地试剂：Tris-HCl" in reference.text()
        assert "不会扣减库存" in _labels(window)
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_wb_loading_reads_local_sample_summary_without_deduction(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    _seed_local_data(project)
    window = _window(qt_app, project)
    try:
        _open_wb(window)
        local_row = window.findChild(QPushButton, "labtoolsLocalWbSampleRow")
        sample_rows = window.findChildren(QLabel, "labtoolsWbSampleRow")

        assert local_row is not None
        assert local_row.property("sampleType") == "protein_lysate"
        assert "Tumor lysate" in local_row.text()
        assert any("Tumor lysate" in row.text() and "2" in row.text() for row in sample_rows)
        assert "不会扣减样本体积" in _labels(window)
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_cell_workspace_reads_cell_and_freeze_vial_summary(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    _seed_local_data(project)
    window = _window(qt_app, project)
    try:
        _open_cell_workspace(window)
        labels = _labels(window)

        assert "local cell profiles: 1" in labels
        assert "Local cell: TPC-1 P12" in labels
        assert "freeze vial overview: available: 1" in labels
        assert "Local vial: TPC-1 P12 #01" in labels
        actions = [button.text() for button in window.findChildren(QPushButton, "labtoolsBoundaryActionButton")]
        assert "保存细胞记录 - 后端未完成" in actions
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_shell_ui_does_not_import_local_data_store_directly() -> None:
    main_window_source = Path("app/shell/main_window.py").read_text(encoding="utf-8")

    assert "LocalLabToolsDataStore" not in main_window_source
    assert "labtools.local_data" not in main_window_source
