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


def _western_blot_page():
    from app.labtools.ui.western_blot_widgets import LabToolsWesternBlotWidget

    page = LabToolsWesternBlotWidget()
    return page, page


def _visible_text(widget) -> str:
    from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit

    parts: list[str] = []
    for label in widget.findChildren(QLabel):
        parts.append(label.text())
    for button in widget.findChildren(QPushButton):
        parts.append(button.text())
    for panel in widget.findChildren(QTextEdit):
        parts.append(panel.toPlainText())
    return "\n".join(part for part in parts if part)


def _matrix_text() -> str:
    values = [[0.10 for _ in range(12)] for _ in range(8)]
    values[0][0] = 0.10
    values[0][1] = 0.10
    values[0][2] = 0.30
    values[0][3] = 0.30
    values[0][4] = 0.50
    values[0][5] = 0.50
    values[0][6] = 0.40
    values[0][7] = 0.40
    return "\n".join("\t".join(f"{value:.3f}" for value in row) for row in values)


def test_western_blot_page_can_enter_protein_loading_and_bca_tools(qapp) -> None:
    from PySide6.QtWidgets import QPushButton, QTabWidget

    _, page = _western_blot_page()
    tabs = page.findChild(QTabWidget, "westernBlotTabs")

    page.findChild(QPushButton, "openProteinLoadingToolButton").click()
    assert tabs.currentIndex() == 2
    assert tabs.tabText(2) == "蛋白上样体系"

    page.findChild(QPushButton, "openBcaAssayToolButton").click()
    assert tabs.currentIndex() == 3
    assert tabs.tabText(3) == "BCA 蛋白浓度测定"


def test_protein_loading_ui_supports_multi_sample_rows_and_reducer_notice(qapp) -> None:
    from PySide6.QtWidgets import QPushButton, QTableWidget

    _, page = _western_blot_page()
    table = page.findChild(QTableWidget, "proteinLoadingSampleTable")
    add_button = page.findChild(QPushButton, "proteinLoadingAddSampleRowButton")
    before = table.rowCount()

    add_button.click()

    assert table.rowCount() == before + 1
    assert "请确认所用 loading buffer 是否已包含 DTT、β-ME 或其他还原剂" in _visible_text(page)


def test_protein_loading_calculation_enables_copy_and_shows_totals(qapp) -> None:
    from PySide6.QtWidgets import QPushButton, QTableWidget, QTableWidgetItem, QTextEdit

    _, page = _western_blot_page()
    table = page.findChild(QTableWidget, "proteinLoadingSampleTable")
    table.setItem(0, 0, QTableWidgetItem("S1"))
    table.setItem(0, 1, QTableWidgetItem("2"))
    copy_button = page.findChild(QPushButton, "proteinLoadingCopyResultButton")

    assert not copy_button.isEnabled()
    page.findChild(QPushButton, "proteinLoadingCalculateButton").click()

    result_text = page.findChild(QTextEdit, "proteinLoadingResultPanel").toPlainText()
    assert copy_button.isEnabled()
    assert "总 loading buffer 体积" in result_text
    assert "Western Blot 上样体系辅助计算草稿" in result_text
    assert "横向 lane layout" in result_text
    assert "Lane 1" in result_text
    assert "Protein Marker" in result_text


def test_bca_ui_displays_plate_matrix_annotation_and_result_entries(qapp) -> None:
    from PySide6.QtWidgets import QComboBox, QPushButton, QTableWidget, QTextEdit

    _, page = _western_blot_page()
    table = page.findChild(QTableWidget, "bcaPlateTable")

    assert table.rowCount() == 8
    assert table.columnCount() == 12
    assert table.verticalHeaderItem(0).text() == "A"
    assert table.horizontalHeaderItem(11).text() == "12"
    assert page.findChild(QTextEdit, "bcaOdMatrixPasteArea") is not None
    assert [page.findChild(QComboBox, "bcaWellTypeCombo").itemText(index) for index in range(4)] == [
        "Blank",
        "Standard",
        "Sample",
        "Unused",
    ]
    assert page.findChild(QPushButton, "bcaApplyBatchAnnotationButton") is not None
    assert page.findChild(QPushButton, "bcaCopyResultButton") is not None
    assert not page.findChild(QPushButton, "bcaCopyResultButton").isEnabled()


def test_bca_calculation_enables_copy_and_shows_results(qapp) -> None:
    from PySide6.QtWidgets import QComboBox, QLineEdit, QPushButton, QTextEdit

    _, page = _western_blot_page()
    page.findChild(QTextEdit, "bcaOdMatrixPasteArea").setText(_matrix_text())
    page.findChild(QPushButton, "bcaParseOdMatrixButton").click()

    type_combo = page.findChild(QComboBox, "bcaWellTypeCombo")
    start = page.findChild(QLineEdit, "bcaBatchStartWellField")
    end = page.findChild(QLineEdit, "bcaBatchEndWellField")
    name = page.findChild(QLineEdit, "bcaAnnotationNameField")
    concentration = page.findChild(QLineEdit, "bcaStandardConcentrationField")
    dilution = page.findChild(QLineEdit, "bcaDilutionFactorField")
    apply_button = page.findChild(QPushButton, "bcaApplyBatchAnnotationButton")

    for start_well, end_well, conc in (("A1", "A2", "0"), ("A3", "A4", "100"), ("A5", "A6", "200")):
        type_combo.setCurrentText("Standard")
        start.setText(start_well)
        end.setText(end_well)
        name.setText("BSA")
        concentration.setText(conc)
        dilution.setText("1")
        apply_button.click()
    type_combo.setCurrentText("Sample")
    start.setText("A7")
    end.setText("A8")
    name.setText("Sample 1")
    concentration.setText("")
    dilution.setText("2")
    apply_button.click()

    copy_button = page.findChild(QPushButton, "bcaCopyResultButton")
    assert not copy_button.isEnabled()
    page.findChild(QPushButton, "bcaCalculateButton").click()

    assert copy_button.isEnabled()
    assert "slope" in page.findChild(QTextEdit, "bcaStandardCurvePanel").toPlainText()
    assert "Sample 1" in page.findChild(QTextEdit, "bcaSampleResultsPanel").toPlainText()
    assert "BCA 蛋白浓度测定辅助计算草稿" in page.findChild(QTextEdit, "bcaSampleResultsPanel").toPlainText()


def test_wb_loading_ui_generates_lane_layout_and_marker_variants(qapp) -> None:
    from PySide6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit

    _, page = _western_blot_page()
    table = page.findChild(QTableWidget, "proteinLoadingSampleTable")
    table.setItem(0, 0, QTableWidgetItem("S1"))
    table.setItem(0, 1, QTableWidgetItem("2"))
    table.setItem(1, 0, QTableWidgetItem("S2"))
    table.setItem(1, 1, QTableWidgetItem("4"))

    page.findChild(QPushButton, "proteinLoadingCalculateButton").click()
    lane_text = page.findChild(QTextEdit, "wbLoadingLaneLayoutPanel").toPlainText()
    assert "Lane 1" in lane_text
    assert "Protein Marker" in lane_text
    assert "S1" in lane_text

    page.findChild(QCheckBox, "wbLoadingMarkerEnabledCheck").setChecked(False)
    page.findChild(QPushButton, "proteinLoadingCalculateButton").click()
    lane_text = page.findChild(QTextEdit, "wbLoadingLaneLayoutPanel").toPlainText()
    assert "样本\tS1\tS2" in lane_text

    page.findChild(QCheckBox, "wbLoadingMarkerEnabledCheck").setChecked(True)
    page.findChild(QComboBox, "wbLoadingLaneModeCombo").setCurrentText("fixed")
    page.findChild(QComboBox, "wbLoadingFixedLaneCountCombo").setCurrentText("10")
    page.findChild(QPushButton, "proteinLoadingCalculateButton").click()
    lane_text = page.findChild(QTextEdit, "wbLoadingLaneLayoutPanel").toPlainText()
    assert "Lane 10" in lane_text
    assert "Empty" in lane_text

    page.findChild(QComboBox, "wbLoadingReducingModeCombo").setCurrentText("percent_of_final")
    page.findChild(QLineEdit, "wbLoadingReducingNameField").setText("β-ME")
    page.findChild(QLineEdit, "wbLoadingReducingPercentField").setText("5")
    page.findChild(QPushButton, "proteinLoadingCalculateButton").click()
    assert "β-ME" in page.findChild(QTextEdit, "wbLoadingLaneLayoutPanel").toPlainText()


def test_wb_loading_ui_saves_record_and_updates_history(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QPushButton, QTableWidget, QTableWidgetItem, QTextEdit

    from app.labtools.western_blot.store import WBLoadingRecordStore
    from app.labtools.western_blot.widgets import WesternBlotLoadingCalculatorWidget

    page = WesternBlotLoadingCalculatorWidget(record_store=WBLoadingRecordStore(tmp_path / "loading_records.json"))
    table = page.findChild(QTableWidget, "proteinLoadingSampleTable")
    table.setItem(0, 0, QTableWidgetItem("S1"))
    table.setItem(0, 1, QTableWidgetItem("2"))

    save_button = page.findChild(QPushButton, "wbLoadingSaveRecordButton")
    copy_markdown = page.findChild(QPushButton, "wbLoadingCopyMarkdownButton")
    assert not save_button.isEnabled()
    assert not copy_markdown.isEnabled()

    page.findChild(QPushButton, "proteinLoadingCalculateButton").click()

    assert save_button.isEnabled()
    assert copy_markdown.isEnabled()
    save_button.click()

    history = page.findChild(QTableWidget, "wbLoadingRecordHistoryTable")
    assert history.rowCount() == 1
    assert history.item(0, 0).text() == "WB loading"
    assert history.item(0, 4).text() == "OK"
    assert "已保存本次上样记录" in page.findChild(QTextEdit, "proteinLoadingResultPanel").toPlainText() or history.item(0, 5).text().startswith("wb_loading_")


def test_loading_and_bca_ui_avoid_misleading_claims(qapp) -> None:
    _, page = _western_blot_page()
    text = _visible_text(page)

    for forbidden in ("正式报告", "无需人工复核", "clinical diagnosis", "production-grade"):
        assert forbidden not in text
