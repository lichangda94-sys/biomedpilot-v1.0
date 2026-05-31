from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_labtools_tool_registry_lists_available_and_planned_tools() -> None:
    from app.labtools.labtools_tool_registry import labtools_primary_entries, labtools_secondary_entries

    assert [entry.tool_id for entry in labtools_primary_entries()] == [
        "general_calculators",
        "reagent_preparation",
        "experiment_modules",
    ]
    assert [entry.tool_id for entry in labtools_secondary_entries()] == [
        "cell_experiments",
        "protein_experiments",
        "nucleic_acid_experiments",
        "immuno_absorbance",
        "ihc",
    ]
    assert all(entry.semantic_key.startswith("labtools.page.") for entry in labtools_primary_entries())
    assert all(entry.disabled_reason for entry in labtools_secondary_entries())


def test_labtools_module_exports_features() -> None:
    from app.labtools.workspace import labtools_features
    from app.shared.feature_status import FeatureStatus

    features = labtools_features()

    assert [feature.name for feature in features] == [
        "图像能力边界",
        "通用计算器",
        "试剂制备",
        "实验模块",
    ]
    assert features[0].status is FeatureStatus.TESTING
    assert features[3].status is FeatureStatus.TESTING
    assert all(features[index].status is FeatureStatus.UNAVAILABLE for index in (1, 2))
    assert all(feature.module == "labtools" for feature in features)

    descriptions = {feature.name: feature.description for feature in features}
    assert "常用科学计算" in descriptions["通用计算器"]
    assert "试剂配制" in descriptions["试剂制备"]
    assert "细胞实验" in descriptions["实验模块"]
    assert "图像能力边界" in descriptions

    from app.labtools.experiment_templates import LABTOOLS_EXPERIMENT_RECORD_DRAFT_STORE_SCHEMA_VERSION

    assert LABTOOLS_EXPERIMENT_RECORD_DRAFT_STORE_SCHEMA_VERSION == "labtools_experiment_record_draft_store.v1"


def test_labtools_workspace_instantiates_when_qt_available() -> None:
    try:
        from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTabWidget

        from app.labtools.workspace import LabToolsWorkspaceWidget
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PySide6 UI runtime unavailable: {exc}")

    app = QApplication.instance() or QApplication([])
    widget = LabToolsWorkspaceWidget()

    assert app is not None
    assert widget.objectName() == "labToolsWorkspace"
    assert widget.page_keys() == (
        "home",
        "general_calculators",
        "reagent_preparation",
        "experiment_modules",
        "cell_experiments",
        "protein_experiments",
        "nucleic_acid_experiments",
        "immuno_absorbance",
        "ihc",
    )
    assert widget.current_page_key() == "home"
    assert widget.findChild(QPushButton, "labtoolsEntryButton") is not None
    widget.show_general_calculators()
    assert widget.current_page_key() == "general_calculators"
    tabs = widget.findChild(QTabWidget, "labToolsCalculatorTabs")
    assert tabs is not None
    assert [tabs.tabText(index) for index in range(tabs.count())] == ["快速计算", "试剂制备"]
    quick_tabs = widget.findChild(QTabWidget, "labToolsQuickCalculatorTabs")
    assert quick_tabs is not None
    assert [quick_tabs.tabText(index) for index in range(quick_tabs.count())] == ["浓度换算", "稀释计算", "溶液配制"]
    calculator_labels = "\n".join(label.text() for label in widget._stack.currentWidget().findChildren(QLabel))
    assert "通用试剂制备" in calculator_labels
    assert "本地通用试剂制备工作台" in calculator_labels
    assert "我的试剂模板" in calculator_labels
    assert "本次制备" in calculator_labels
    assert "不替代实验 SOP" in calculator_labels
    assert "溶液稀释" in calculator_labels or "C1V1 = C2V2 稀释计算" in calculator_labels
    assert "摩尔浓度" in calculator_labels
    assert "细胞接种" not in calculator_labels
    assert "qPCR 配液" not in calculator_labels
    assert "WB / SDS-PAGE 上样计算" not in calculator_labels
    assert "WB 上样" not in calculator_labels
    assert "人工复核" in calculator_labels or "结果仅供实验前核对" in calculator_labels
    widget.show_reagent_preparation()
    assert widget.current_page_key() == "reagent_preparation"
    widget.show_western_blot()
    assert widget.current_page_key() == "protein_experiments"
    western_text = "\n".join(label.text() for label in widget._stack.currentWidget().findChildren(QLabel))
    assert "Western Blot 流程工作台：available / 可用" in western_text
    assert "结果与灰度分析：placeholder / 未启用" in western_text
    widget.show_cell_experiments()
    assert widget.current_page_key() == "cell_experiments"


def test_labtools_calculator_workbench_saves_template_and_generates_preparation(tmp_path) -> None:
    try:
        from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QLineEdit, QPushButton, QTabWidget, QTextEdit

        from app.labtools.reagent_templates import ReagentTemplateStore
        from app.labtools.ui.calculator_widgets import LabToolsCalculatorWidget
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PySide6 UI runtime unavailable: {exc}")

    app = QApplication.instance() or QApplication([])
    store = ReagentTemplateStore(tmp_path / "reagent_templates.json")
    widget = LabToolsCalculatorWidget(reagent_template_store=store)

    assert app is not None
    tabs = widget.findChild(QTabWidget, "labToolsCalculatorTabs")
    assert tabs is not None
    assert [tabs.tabText(index) for index in range(tabs.count())] == ["快速计算", "试剂制备"]

    tabs.setCurrentIndex(1)
    widget.findChild(QLineEdit, "reagentTemplateNameField").setText("试剂 A")
    widget.findChild(QLineEdit, "reagentTemplateDefaultVolumeField").setText("100")
    widget.findChild(QLineEdit, "reagentTemplateDefaultStrengthField").setText("1X")

    widget.findChild(QLineEdit, "reagentComponentNameField").setText("B")
    widget.findChild(QLineEdit, "reagentComponentAmountField").setText("10")
    widget.findChild(QCheckBox, "reagentComponentContributesVolumeCheck").setChecked(True)
    widget.findChild(QPushButton, "reagentTemplateAddComponentButton").click()

    widget.findChild(QLineEdit, "reagentComponentNameField").setText("水")
    widget.findChild(QComboBox, "reagentComponentTypeCombo").setCurrentText("solvent")
    widget.findChild(QLineEdit, "reagentComponentAmountField").setText("0")
    widget.findChild(QCheckBox, "reagentComponentContributesVolumeCheck").setChecked(False)
    widget.findChild(QCheckBox, "reagentComponentAutoFillCheck").setChecked(True)
    widget.findChild(QComboBox, "reagentSolventInitialModeCombo").setCurrentText("percent_of_final")
    widget.findChild(QLineEdit, "reagentSolventInitialPercentField").setText("80")
    widget.findChild(QPushButton, "reagentTemplateAddComponentButton").click()
    widget.findChild(QCheckBox, "reagentPhRecordEnabledCheck").setChecked(True)
    widget.findChild(QLineEdit, "reagentPhTargetField").setText("7.4")
    widget.findChild(QLineEdit, "reagentPhAdjustmentNoteField").setText("使用 HCl 或 NaOH 调整，需 pH meter 实测")
    widget.findChild(QPushButton, "reagentTemplateSaveButton").click()

    saved = store.load()
    assert len(saved) == 1
    assert saved[0].name == "试剂 A"
    assert len(saved[0].components) == 2
    assert saved[0].ph_record is not None
    assert saved[0].ph_record.target_ph == "7.4"

    tabs.setCurrentIndex(1)
    widget.findChild(QPushButton, "preparationReloadTemplatesButton").click()
    widget.findChild(QLineEdit, "preparationTargetVolumeField").setText("75")
    widget.findChild(QLineEdit, "preparationOverageField").setText("10")
    widget.findChild(QPushButton, "preparationCalculateButton").click()

    result_text = widget.findChild(QTextEdit, "preparationResultPanel").toPlainText()
    assert "试剂 A 本次制备清单" in result_text
    assert "目标最终体积：75 mL" in result_text
    assert "建议配制体积：82.5 mL" in result_text
    assert "- B: 8.25 mL" in result_text
    assert "- 水（溶剂补足）: 74.25 mL" in result_text
    assert "pH / 调节记录" in result_text
    assert "目标 pH: 7.4" in result_text
    assert "7.4 mL" not in result_text
    assert "初始加入约 66 mL" in result_text
    assert "调节或记录 pH 至目标 pH 7.4" in result_text
    assert "人工复核提示" in result_text


def test_labtools_template_ui_clears_reference_after_self_prepared_component(tmp_path) -> None:
    try:
        from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QLineEdit, QPushButton, QTabWidget

        from app.labtools.reagent_templates import ReagentTemplateStore
        from app.labtools.ui.calculator_widgets import LabToolsCalculatorWidget
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PySide6 UI runtime unavailable: {exc}")

    app = QApplication.instance() or QApplication([])
    store = ReagentTemplateStore(tmp_path / "reagent_templates.json")
    widget = LabToolsCalculatorWidget(reagent_template_store=store)
    tabs = widget.findChild(QTabWidget, "labToolsCalculatorTabs")
    assert app is not None
    assert tabs is not None
    tabs.setCurrentIndex(1)

    widget.findChild(QLineEdit, "reagentTemplateNameField").setText("10X PBS stock")
    widget.findChild(QLineEdit, "reagentTemplateDefaultVolumeField").setText("1000")
    widget.findChild(QLineEdit, "reagentComponentNameField").setText("NaCl")
    widget.findChild(QLineEdit, "reagentComponentAmountField").setText("80")
    widget.findChild(QPushButton, "reagentTemplateAddComponentButton").click()
    widget.findChild(QPushButton, "reagentTemplateSaveButton").click()
    stock = store.load()[0]

    widget.findChild(QPushButton, "reagentTemplateNewButton").click()
    widget.findChild(QLineEdit, "reagentTemplateNameField").setText("1X PBS from stock")
    widget.findChild(QLineEdit, "reagentTemplateDefaultVolumeField").setText("100")
    widget.findChild(QComboBox, "reagentComponentTypeCombo").setCurrentText("self_prepared_template")
    reference_combo = widget.findChild(QComboBox, "reagentComponentReferenceTemplateCombo")
    reference_combo.setCurrentIndex(reference_combo.findData(stock.template_id))
    widget.findChild(QLineEdit, "reagentComponentNameField").setText("10X PBS stock")
    widget.findChild(QLineEdit, "reagentComponentAmountField").setText("10")
    widget.findChild(QCheckBox, "reagentComponentContributesVolumeCheck").setChecked(True)
    widget.findChild(QPushButton, "reagentTemplateAddComponentButton").click()

    assert widget.findChild(QComboBox, "reagentComponentTypeCombo").currentText() == "liquid"
    assert widget.findChild(QComboBox, "reagentComponentReferenceTemplateCombo").currentData() == ""
    assert widget.findChild(QComboBox, "reagentComponentReferenceTemplateCombo").isEnabled() is False

    widget.findChild(QComboBox, "reagentComponentTypeCombo").setCurrentText("solvent")
    widget.findChild(QLineEdit, "reagentComponentNameField").setText("ddH2O")
    widget.findChild(QLineEdit, "reagentComponentAmountField").setText("0")
    widget.findChild(QCheckBox, "reagentComponentContributesVolumeCheck").setChecked(True)
    widget.findChild(QCheckBox, "reagentComponentAutoFillCheck").setChecked(True)
    widget.findChild(QPushButton, "reagentTemplateAddComponentButton").click()
    widget.findChild(QPushButton, "reagentTemplateSaveButton").click()

    working = next(template for template in store.load() if template.name == "1X PBS from stock")
    components = {component.name: component for component in working.components}
    assert components["10X PBS stock"].referenced_template_id == stock.template_id
    assert components["ddH2O"].referenced_template_id == ""
