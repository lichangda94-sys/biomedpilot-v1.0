from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton

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


def _patch_save_file(monkeypatch: pytest.MonkeyPatch, target: Path) -> None:
    monkeypatch.setattr(main_window_module.QFileDialog, "getSaveFileName", lambda *_args, **_kwargs: (str(target), ""))


def test_reagent_preparation_exports_markdown_and_csv_via_file_picker(qt_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        _open_primary(window, PageKey.LABTOOLS_REAGENT_PREPARATION.value)

        markdown_path = tmp_path / "picked" / "reagent.md"
        _patch_save_file(monkeypatch, markdown_path)
        window.findChild(QPushButton, "labtoolsReagentExportMarkdownButton").click()
        assert markdown_path.exists()
        assert "BioMedPilot LabTools Reagent Preparation" in markdown_path.read_text(encoding="utf-8")

        csv_path = tmp_path / "picked" / "reagent.csv"
        _patch_save_file(monkeypatch, csv_path)
        window.findChild(QPushButton, "labtoolsReagentExportCsvButton").click()
        assert csv_path.exists()
        assert "review_notice" in csv_path.read_text(encoding="utf-8")

        assert not (home / ".labtools").exists()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_wb_loading_exports_markdown_and_csv_via_file_picker(qt_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        _open_experiment_page(window, "wb_loading")

        markdown_path = tmp_path / "exports" / "wb.md"
        _patch_save_file(monkeypatch, markdown_path)
        window.findChild(QPushButton, "labtoolsWbExportMarkdownButton").click()
        assert markdown_path.exists()
        assert "BioMedPilot LabTools WB Loading" in markdown_path.read_text(encoding="utf-8")

        csv_path = tmp_path / "exports" / "wb.csv"
        _patch_save_file(monkeypatch, csv_path)
        window.findChild(QPushButton, "labtoolsWbExportCsvButton").click()
        assert csv_path.exists()
        assert "sample_id" in csv_path.read_text(encoding="utf-8")

        assert not (home / ".labtools").exists()
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_file_picker_export_rejects_home_labtools_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    result = labtools_runtime.calculate_reagent_preparation(
        template_id="demo_pbs_1x",
        target_volume="500",
        target_volume_unit="mL",
        operator_name="Researcher",
        measured_ph="7.4",
        adjustment_note="reviewed",
    )

    blocked = labtools_runtime.export_reagent_preparation_markdown(home / ".labtools" / "blocked.md", result)
    assert not blocked.ok
    assert not (home / ".labtools" / "blocked.md").exists()


def test_non_pilot_labtools_exports_remain_disabled(qt_app) -> None:
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        _open_primary(window, PageKey.LABTOOLS_GENERAL_CALCULATORS.value)
        quick_exports = window.findChildren(QPushButton, "labtoolsExportResultButton")
        assert quick_exports
        assert all(not button.isEnabled() for button in quick_exports)

        for page_key in ("bca_od_mvp", "cell_experiment_workspace", "elisa_boundary", "image_processing_boundary"):
            _open_experiment_page(window, page_key)
            actions = window.findChildren(QPushButton, "labtoolsBoundaryActionButton")
            export_actions = [button for button in actions if "导出" in button.text()]
            assert export_actions
            assert all(not button.isEnabled() for button in export_actions)

        assert not window.findChildren(QPushButton, "labtoolsPdfExportButton")
        assert not window.findChildren(QPushButton, "labtoolsDocxExportButton")
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
