from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture()
def qapp():
    try:
        from PySide6.QtWidgets import QApplication
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PySide6 UI runtime unavailable: {exc}")
    return QApplication.instance() or QApplication([])


def _tab_labels(tabs):
    return [tabs.tabText(index) for index in range(tabs.count())]


def test_cell_experiment_page_shows_record_and_image_analysis_areas(qapp) -> None:
    from PySide6.QtWidgets import QTabWidget

    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_cell_experiments()
    page = widget._stack.currentWidget()
    top_tabs = page.findChild(QTabWidget, "cellExperimentTopTabs")
    record_tabs = page.findChild(QTabWidget, "cellExperimentRecordTabs")
    image_tabs = page.findChild(QTabWidget, "cellExperimentImageAnalysisTabs")

    assert _tab_labels(top_tabs) == ["细胞实验记录", "细胞图像分析"]
    assert _tab_labels(record_tabs) == [
        "细胞档案",
        "细胞复苏记录",
        "细胞传代记录",
        "细胞接种 / 铺板记录",
        "细胞冻存记录",
        "给药 / 处理记录",
        "转染记录",
        "其他处理记录",
    ]
    assert _tab_labels(image_tabs) == ["划痕实验图像分析", "Transwell 图像分析", "荧光 / 染色图像分析"]


def test_cell_profile_page_can_save_profile_and_create_inventory(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QLineEdit, QPushButton, QTableWidget

    from app.labtools.cell_experiments import CellExperimentRecordStore, CellProfileStore, FreezingInventoryStore
    from app.labtools.ui.cell_experiment_widgets import LabToolsCellExperimentPage

    profile_store = CellProfileStore(tmp_path / "profiles.json")
    inventory_store = FreezingInventoryStore(tmp_path / "inventory.json")
    record_store = CellExperimentRecordStore(tmp_path / "records.json", profile_store=profile_store, inventory_store=inventory_store)
    page = LabToolsCellExperimentPage(profile_store=profile_store, inventory_store=inventory_store, record_store=record_store)

    page.findChild(QLineEdit, "cellProfileField_cell_name").setText("A549")
    page.findChild(QLineEdit, "cellProfileField_current_passage").setText("P8")
    save_profile = page.findChild(QPushButton, "cellProfileSaveButton")
    create_batch = page.findChild(QPushButton, "freezingBatchCreateButton")
    update_cryovial = page.findChild(QPushButton, "cryovialUpdateButton")

    assert save_profile.property("buttonBehavior") == "upserts_cell_profile_store"
    assert create_batch.property("buttonBehavior") == "creates_freezing_batch_and_cryovial_inventory"
    assert update_cryovial.property("buttonBehavior") == "updates_cryovial_location_and_status"

    save_profile.click()
    page.findChild(QLineEdit, "freezingBatchCodeInput").setText("A549-FZ")
    page.findChild(QLineEdit, "cryovialTankInput").setText("LN2-1")
    create_batch.click()

    profile_table = page.findChild(QTableWidget, "cellProfileTable")
    vial_table = page.findChild(QTableWidget, "cellProfileCryovialTable")

    assert profile_table.rowCount() == 1
    assert profile_table.item(0, 0).text() == "A549"
    assert vial_table.rowCount() == 2
    assert vial_table.item(0, 3).text() == "可用"


def test_record_templates_have_from_last_export_and_seeding_calculation(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QLabel, QPushButton

    from app.labtools.cell_experiments import CellExperimentRecordStore, CellProfile, CellProfileStore, FreezingInventoryStore
    from app.labtools.ui.cell_experiment_widgets import LabToolsCellExperimentPage

    profile_store = CellProfileStore(tmp_path / "profiles.json")
    inventory_store = FreezingInventoryStore(tmp_path / "inventory.json")
    record_store = CellExperimentRecordStore(tmp_path / "records.json", profile_store=profile_store, inventory_store=inventory_store)
    profile_store.save_profile(CellProfile(cell_name="HeLa", current_passage="P3"))
    page = LabToolsCellExperimentPage(profile_store=profile_store, inventory_store=inventory_store, record_store=record_store)

    from_last = page.findChild(QPushButton, "cellRecordFromLastButton_seeding")
    export = page.findChild(QPushButton, "cellRecordExportButton_seeding")
    save = page.findChild(QPushButton, "cellRecordSaveButton_seeding")
    calculate = page.findChild(QPushButton, "seedingCalculationButton")

    assert from_last.text() == "从上次记录创建"
    assert from_last.property("buttonBehavior") == "creates_draft_from_last_cell_record"
    assert export.text() == "导出 TXT"
    assert export.property("buttonBehavior") == "exports_cell_experiment_record_txt"
    assert save.property("buttonBehavior") == "saves_cell_experiment_record"
    assert calculate.property("buttonBehavior") == "calculates_cell_seeding_preparation_preview"

    calculate.click()

    result = page.findChild(QLabel, "seedingCalculationResult").text()
    assert "需要细胞悬液体积" in result
    assert "需要培养基体积" in result


def test_saved_cell_profiles_refresh_record_selectors(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QComboBox, QLineEdit, QPushButton

    from app.labtools.cell_experiments import CellExperimentRecordStore, CellProfileStore, FreezingInventoryStore
    from app.labtools.ui.cell_experiment_widgets import LabToolsCellExperimentPage

    profile_store = CellProfileStore(tmp_path / "profiles.json")
    inventory_store = FreezingInventoryStore(tmp_path / "inventory.json")
    record_store = CellExperimentRecordStore(tmp_path / "records.json", profile_store=profile_store, inventory_store=inventory_store)
    page = LabToolsCellExperimentPage(profile_store=profile_store, inventory_store=inventory_store, record_store=record_store)

    selector = page.findChild(QComboBox, "cellRecordProfileSelector_passage")
    assert selector is not None
    assert selector.count() == 0

    page.findChild(QLineEdit, "cellProfileField_cell_name").setText("BCPAP")
    page.findChild(QLineEdit, "cellProfileField_current_passage").setText("P3")
    page.findChild(QPushButton, "cellProfileSaveButton").click()
    qapp.processEvents()

    assert selector.count() == 1
    assert "BCPAP" in selector.itemText(0)


def test_cell_image_analysis_previews_image_and_generates_run_request(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QPushButton, QTextEdit

    from app.labtools.ui.image_analysis_widgets import scratch_area_workbench_widget

    image_path = tmp_path / "scratch.png"
    image_path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?"
        b"\x00\x05\xfe\x02\xfeA\xe2!\xbc\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    widget = scratch_area_workbench_widget()
    widget.set_image_paths_for_testing((str(image_path),))

    preview = widget.findChild(QTextEdit, "imageWorkbenchPreviewPanel")
    assert preview is not None
    assert "scratch.png" in preview.toHtml()
    assert "<img" in preview.toHtml()

    generate = next(button for button in widget.findChildren(QPushButton, "imageWorkbenchPrimaryActionButton") if button.text() == "生成分析任务")
    generate.click()
    qapp.processEvents()

    assert widget.latest_workspace() is not None
    result = widget.findChild(QTextEdit, "imageWorkbenchResultPanel")
    assert "RunRequest 已生成" in result.toPlainText()
