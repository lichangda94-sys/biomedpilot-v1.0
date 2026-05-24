from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

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


def _window(qt_app, project_root: Path) -> MainWindow:
    window = MainWindow()
    window.set_labtools_project_root(project_root)
    window._welcome_page.enter_workspace()
    window.show_labtools()
    return window


def _open_primary(window: MainWindow, semantic_key: str) -> None:
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("semanticKey") == semantic_key
    )
    button.click()


def _open_wb(window: MainWindow) -> None:
    _open_primary(window, PageKey.LABTOOLS_EXPERIMENT_MODULES.value)
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == "wb_loading"
    )
    button.click()


def _load_store(project_root: Path):
    labtools_runtime._ensure_labtools_importable()
    from labtools.local_data import LocalLabToolsDataStore

    return LocalLabToolsDataStore(project_root / "project_storage" / "labtools")


def _seed_local_entities(project_root: Path) -> tuple[str, str]:
    store = _load_store(project_root)
    store.initialize_store()
    reagent = store.create_reagent({"name": "Tris-HCl", "concentration": "1 M"})
    sample = store.create_sample(
        {
            "sample_name": "Tumor lysate",
            "sample_type": "protein_lysate",
            "concentration": "2.0",
            "concentration_unit": "mg/mL",
            "volume": "25",
            "volume_unit": "µL",
        }
    )
    return reagent.id, sample.id


def _assert_no_formal_or_pdf_docx(project_root: Path) -> None:
    created_files = [path for path in project_root.rglob("*") if path.is_file()]
    assert all(path.suffix.lower() not in {".pdf", ".docx"} for path in created_files)
    assert all(record.status != "formal_report" for record in _load_store(project_root).load_store().records)


def test_reagent_preparation_saves_local_record_summary_with_reagent_link(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    reagent_id, sample_id = _seed_local_entities(project)
    before_sample = _load_store(project).load_store().samples[0]
    window = _window(qt_app, project)
    try:
        _open_primary(window, PageKey.LABTOOLS_REAGENT_PREPARATION.value)
        window.findChildren(QPushButton, "labtoolsLocalReagentRow")[-1].click()
        window.findChild(QPushButton, "labtoolsReagentSaveRecordButton").click()
        qt_app.processEvents()

        snapshot = _load_store(project).load_store()
        record = snapshot.records[-1]
        after_sample = snapshot.samples[0]
        issue = window.findChild(QLabel, "labtoolsReagentIssueRows")

        assert record.record_type == "reagent_preparation"
        assert record.version == 1
        assert record.status == "draft"
        assert record.linked_reagents == (reagent_id,)
        assert sample_id not in record.linked_samples
        assert "local-summary-only" in record.artifact_refs[-1]
        assert "不是正式报告" in issue.text()
        assert after_sample.volume == before_sample.volume == "25"
        assert after_sample.status == before_sample.status
        assert [(entry.entity_type, entry.action) for entry in snapshot.audit_log][-1] == ("record", "create")
        _assert_no_formal_or_pdf_docx(project)
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_wb_loading_saves_local_record_summary_with_sample_link_without_deduction(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    _reagent_id, sample_id = _seed_local_entities(project)
    before_sample = _load_store(project).load_store().samples[0]
    window = _window(qt_app, project)
    try:
        _open_wb(window)
        window.findChild(QPushButton, "labtoolsWbSaveRecordButton").click()
        qt_app.processEvents()

        snapshot = _load_store(project).load_store()
        record = snapshot.records[-1]
        after_sample = snapshot.samples[0]
        issue = window.findChild(QLabel, "labtoolsWbIssueRows")

        assert record.record_type == "wb_loading"
        assert record.version == 1
        assert record.status == "draft"
        assert record.linked_samples == (sample_id,)
        assert "WB 上样计算预览" in record.record_summary
        assert "不是正式报告" in issue.text()
        assert after_sample.volume == before_sample.volume == "25"
        assert after_sample.status == before_sample.status
        _assert_no_formal_or_pdf_docx(project)
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_general_calculator_saves_quick_and_formula_record_summaries(qt_app, tmp_path: Path) -> None:
    project = tmp_path / "project"
    window = _window(qt_app, project)
    try:
        _open_primary(window, PageKey.LABTOOLS_GENERAL_CALCULATORS.value)
        window.findChild(QPushButton, "labtoolsQuickCalculateButton").click()
        quick_save = next(
            item for item in window.findChildren(QPushButton, "labtoolsSaveHistoryButton") if item.property("pageKey") == "quick_calculator"
        )
        assert quick_save.isEnabled()
        quick_save.click()
        qt_app.processEvents()

        formula_mode = next(
            item for item in window.findChildren(QPushButton, "labtoolsGeneralModeButton") if item.property("modeKey") == "formula_solver"
        )
        formula_mode.click()
        window.findChild(QPushButton, "labtoolsFormulaCalculateButton").click()
        formula_save = next(
            item for item in window.findChildren(QPushButton, "labtoolsSaveHistoryButton") if item.property("pageKey") == "formula_solver"
        )
        formula_save.click()
        qt_app.processEvents()

        records = _load_store(project).load_store().records
        quick = [record for record in records if record.record_type == "quick_calculation"][-1]
        formula = [record for record in records if record.record_type == "formula_solver"][-1]

        assert quick.version == 1
        assert formula.version == 1
        assert quick.status == "draft"
        assert formula.status == "draft"
        assert quick.record_summary
        assert formula.record_summary
        assert "local-summary-only" in quick.artifact_refs[-1]
        assert "local-summary-only" in formula.artifact_refs[-1]
        _assert_no_formal_or_pdf_docx(project)
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_record_index_save_ui_does_not_import_store_directly_and_future_adapters_disabled() -> None:
    source = Path("app/shell/main_window.py").read_text(encoding="utf-8")
    lan = labtools_runtime.get_labtools_local_data_status(Path("/tmp/nonexistent-labtools-project"), data_source_mode="future_lan")
    cloud = labtools_runtime.get_labtools_local_data_status(Path("/tmp/nonexistent-labtools-project"), data_source_mode="future_cloud")

    assert "LocalLabToolsDataStore" not in source
    assert "labtools.local_data" not in source
    assert lan.status == "disabled_future_option"
    assert cloud.status == "disabled_future_option"
