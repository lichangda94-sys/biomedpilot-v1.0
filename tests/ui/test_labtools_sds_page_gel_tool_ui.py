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


def _western_blot_page():
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    return widget, widget._stack.currentWidget()


def _fill_valid_template(page) -> None:
    from PySide6.QtWidgets import QComboBox, QLineEdit

    page.findChild(QLineEdit, "sdsPageTemplateNameField").setText("UI 10% 胶模板")
    page.findChild(QLineEdit, "sdsPageGelConcentrationField").setText("10%")
    page.findChild(QComboBox, "sdsPageGelThicknessCombo").setCurrentText("1.0 mm")
    page.findChild(QComboBox, "sdsPageWellCountCombo").setCurrentText("10 wells")
    page.findChild(QLineEdit, "sdsPageGelCountField").setText("10")
    page.findChild(QLineEdit, "sdsPageOveragePercentField").setText("3")
    page.findChild(QLineEdit, "sdsPageResolvingComponentNameField").setText("Acrylamide mix")
    page.findChild(QLineEdit, "sdsPageResolvingAmountField").setText("2.5")
    page.findChild(QComboBox, "sdsPageResolvingUnitCombo").setCurrentText("mL")
    page.findChild(QLineEdit, "sdsPageResolvingComponentNoteField").setText("最后加入前检查有效期")
    page.findChild(QLineEdit, "sdsPageStackingComponentNameField").setText("Stacking buffer")
    page.findChild(QLineEdit, "sdsPageStackingAmountField").setText("1")
    page.findChild(QComboBox, "sdsPageStackingUnitCombo").setCurrentText("mL")
    page.findChild(QLineEdit, "sdsPageStackingComponentNoteField").setText("用户自定义备注")


def test_western_blot_page_can_enter_sds_page_gel_tool(qapp) -> None:
    from PySide6.QtWidgets import QPushButton, QTabWidget

    widget, page = _western_blot_page()
    button = page.findChild(QPushButton, "openSdsPageGelToolButton")

    assert widget.current_page_key() == "western_blot"
    assert button is not None
    button.click()
    tabs = page.findChild(QTabWidget, "westernBlotTabs")
    assert tabs.currentIndex() == 1
    assert "SDS-PAGE 配胶模板与批量配制" in _visible_text(page)


def test_sds_page_template_form_contains_required_fields_and_combos(qapp) -> None:
    from PySide6.QtWidgets import QComboBox, QLineEdit

    _, page = _western_blot_page()
    text = _visible_text(page)
    thickness = page.findChild(QComboBox, "sdsPageGelThicknessCombo")
    wells = page.findChild(QComboBox, "sdsPageWellCountCombo")

    assert "胶浓度" in text
    assert "胶厚度" in text
    assert "孔数" in text
    assert "分离胶" in text
    assert "浓缩胶" in text
    assert [thickness.itemText(index) for index in range(thickness.count())] == ["0.75 mm", "1.0 mm", "1.5 mm"]
    assert [wells.itemText(index) for index in range(wells.count())] == ["10 wells", "12 wells", "15 wells"]
    assert page.findChild(QLineEdit, "sdsPageResolvingComponentNoteField") is not None
    assert page.findChild(QLineEdit, "sdsPageStackingComponentNoteField") is not None


def test_sds_page_overage_defaults_to_three_percent_and_button_states(qapp) -> None:
    from PySide6.QtWidgets import QLineEdit, QPushButton

    _, page = _western_blot_page()

    assert page.findChild(QLineEdit, "sdsPageOveragePercentField").text() == "3"
    assert not page.findChild(QPushButton, "sdsPageTemplateJsonExportButton").isEnabled()
    assert not page.findChild(QPushButton, "sdsPageXlsxExportButton").isEnabled()
    assert page.findChild(QPushButton, "sdsPageTemplateJsonImportButton").isEnabled()


def test_sds_page_calculation_shows_total_amount_with_overage(qapp) -> None:
    from PySide6.QtWidgets import QPushButton, QTextEdit

    _, page = _western_blot_page()
    _fill_valid_template(page)

    page.findChild(QPushButton, "primaryButton").click()

    result_text = page.findChild(QTextEdit, "sdsPageGelResultPanel").toPlainText()
    assert "总量含余量" in result_text
    assert "25.75 mL" in result_text
    assert "10.3 mL" in result_text
    assert "结果为实验辅助计算草稿，使用前请按试剂盒说明书和实验室 SOP 人工核对" in result_text
    assert page.findChild(QPushButton, "sdsPageTemplateJsonExportButton").isEnabled()
    assert page.findChild(QPushButton, "sdsPageXlsxExportButton").isEnabled()


def test_sds_page_json_and_xlsx_export_entries_exist(qapp) -> None:
    from PySide6.QtWidgets import QPushButton

    _, page = _western_blot_page()
    text = _visible_text(page)

    assert page.findChild(QPushButton, "sdsPageTemplateJsonImportButton") is not None
    assert page.findChild(QPushButton, "sdsPageTemplateJsonExportButton") is not None
    assert page.findChild(QPushButton, "sdsPageXlsxExportButton") is not None
    assert "导入模板 JSON" in text
    assert "导出模板 JSON" in text
    assert "导出本次计算 XLSX" in text


def test_sds_page_tool_does_not_claim_auto_recommendation_or_formal_output(qapp) -> None:
    _, page = _western_blot_page()
    text = _visible_text(page)

    assert "基于用户录入的试剂盒/实验室模板进行批量换算" in text
    for forbidden in ("自动推荐最佳配方", "通用正确配方", "无需人工复核", "正式 SOP"):
        assert forbidden not in text
