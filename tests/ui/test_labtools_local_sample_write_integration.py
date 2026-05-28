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


def _open_bca(window: MainWindow) -> None:
    _open_experiment_modules(window)
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == "bca_od_mvp"
    )
    button.click()


def _window(qt_app, project_root: Path) -> MainWindow:
    window = MainWindow()
    window.set_labtools_project_root(project_root)
    window._welcome_page.enter_workspace()
    window.show_labtools()
    return window


def _sample_field(window: MainWindow, field_id: str) -> QLineEdit:
    return [item for item in window.findChildren(QLineEdit, "labtoolsLocalSampleInput") if item.property("fieldId") == field_id][-1]


def _bca_field(window: MainWindow, field_id: str) -> QLineEdit:
    return [item for item in window.findChildren(QLineEdit, "labtoolsBcaProposalInput") if item.property("fieldId") == field_id][-1]


def _sample_rows(window: MainWindow) -> list[QPushButton]:
    return window.findChildren(QPushButton, "labtoolsLocalWbSampleRow")


def _sample_write_status(window: MainWindow) -> QLabel:
    return window.findChildren(QLabel, "labtoolsLocalSampleWriteStatus")[-1]


def _load_store(project_root: Path):
    labtools_runtime._ensure_labtools_importable()
    from labtools.local_data import LocalLabToolsDataStore

    return LocalLabToolsDataStore(project_root / "project_storage" / "labtools")


def _seed_sample(project_root: Path):
    store = _load_store(project_root)
    store.initialize_store()
    return store.create_sample(
        {
            "sample_name": "Tumor lysate",
            "sample_type": "protein_lysate",
            "concentration": "2.0",
            "concentration_unit": "mg/mL",
            "volume": "25",
            "volume_unit": "µL",
            "storage_location": "-80C / Rack 1",
        }
    )


def test_sample_ui_creates_updates_and_archives_local_sample(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    window = _window(qt_app, project)
    try:
        _open_wb(window)
        _sample_field(window, "sample_name").setText("Tumor lysate")
        _sample_field(window, "sample_type").setText("protein_lysate")
        _sample_field(window, "concentration").setText("2.0")
        _sample_field(window, "concentration_unit").setText("mg/mL")
        _sample_field(window, "volume").setText("25")
        _sample_field(window, "volume_unit").setText("µL")
        _sample_field(window, "storage_location").setText("-80C / Rack 1")
        window.findChild(QPushButton, "labtoolsLocalSampleCreateButton").click()
        qt_app.processEvents()

        row = _sample_rows(window)[-1]
        status = _sample_write_status(window)
        assert row.property("sampleName") == "Tumor lysate"
        assert row.property("sampleType") == "protein_lysate"
        assert row.property("version") == 1
        assert "已保存到本地 LabTools 数据库" in status.text()

        row.click()
        _sample_field(window, "concentration").setText("2.5")
        window.findChild(QPushButton, "labtoolsLocalSampleUpdateButton").click()
        qt_app.processEvents()
        updated_row = _sample_rows(window)[-1]
        assert updated_row.property("version") == 2
        assert "2.5 mg/mL" in updated_row.text()

        updated_row.click()
        window.findChild(QPushButton, "labtoolsLocalSampleArchiveButton").click()
        qt_app.processEvents()
        assert _load_store(project).list_samples() == ()
        assert any("暂无本地 sample" in label.text() for label in window.findChildren(QLabel))

        snapshot = _load_store(project).load_store()
        assert snapshot.samples[0].status == "archived"
        assert snapshot.samples[0].volume == "25"
        assert [entry.action for entry in snapshot.audit_log] == ["create", "update", "archive"]
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_sample_ui_blocks_stale_version_and_does_not_deduct_volume(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    _seed_sample(project)
    window = _window(qt_app, project)
    try:
        _open_wb(window)
        row = _sample_rows(window)[-1]
        row.click()
        before = _load_store(project).load_store().samples[0]
        _load_store(project).update_sample(row.property("sampleId"), {"concentration": "2.2"}, expected_version=1)

        _sample_field(window, "concentration").setText("2.5")
        window.findChild(QPushButton, "labtoolsLocalSampleUpdateButton").click()
        qt_app.processEvents()

        after = _load_store(project).load_store().samples[0]
        status = _sample_write_status(window)
        assert status.property("status") == "blocked_version_conflict"
        assert "version_conflict" in status.text()
        assert before.volume == after.volume == "25"
        assert after.status == "available"
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_wb_loading_reads_sample_concentration_without_volume_or_status_write(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    _seed_sample(project)
    window = _window(qt_app, project)
    try:
        _open_wb(window)
        window.findChild(QPushButton, "labtoolsWbCalculateButton").click()
        qt_app.processEvents()

        sample = _load_store(project).load_store().samples[0]
        result_rows = "\n".join(label.text() for label in window.findChildren(QLabel, "labtoolsWbSampleRow"))
        assert "Tumor lysate" in result_rows
        assert sample.concentration == "2.0"
        assert sample.volume == "25"
        assert sample.status == "available"
        assert sample.version == 1
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_bca_proposal_writes_only_after_user_confirmation(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    _seed_sample(project)
    window = _window(qt_app, project)
    try:
        _open_bca(window)
        _bca_field(window, "concentration").setText("3.0")
        window.findChild(QPushButton, "labtoolsBcaProposalButton").click()
        qt_app.processEvents()

        proposal_status = window.findChild(QLabel, "labtoolsBcaProposalStatus")
        confirm = window.findChild(QPushButton, "labtoolsBcaConfirmProposalButton")
        after_proposal = _load_store(project).load_store().samples[0]
        assert proposal_status.property("status") == "proposal_ready"
        assert confirm.isEnabled()
        assert after_proposal.concentration == "2.0"
        assert after_proposal.version == 1

        confirm.click()
        qt_app.processEvents()
        after_confirm = _load_store(project).load_store().samples[0]
        assert proposal_status.property("status") == "updated"
        assert after_confirm.concentration == "3.0"
        assert after_confirm.volume == "25"
        assert after_confirm.version == 2
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_sample_write_ui_does_not_import_store_directly_and_future_adapters_disabled() -> None:
    source = Path("app/shell/main_window.py").read_text(encoding="utf-8")
    lan = labtools_runtime.get_labtools_local_data_status(Path("/tmp/nonexistent-labtools-project"), data_source_mode="future_lan")
    cloud = labtools_runtime.get_labtools_local_data_status(Path("/tmp/nonexistent-labtools-project"), data_source_mode="future_cloud")

    assert "LocalLabToolsDataStore" not in source
    assert "labtools.local_data" not in source
    assert lan.status == "disabled_future_option"
    assert cloud.status == "disabled_future_option"
