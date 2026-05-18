from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_labtools_tool_registry_lists_available_and_planned_tools() -> None:
    from app.labtools.labtools_tool_registry import labtools_tool_registry

    tools = labtools_tool_registry()
    tool_ids = [tool.tool_id for tool in tools]

    assert tool_ids == [
        "general_reagent_calculator",
        "western_blot",
        "pcr_qpcr",
        "elisa_absorbance",
        "cell_experiments",
    ]
    assert tools[0].is_available is True
    assert tools[0].is_planned_only is False
    assert tools[1].is_available is True
    assert tools[1].requires_imagej_fiji is False
    assert tools[1].is_planned_only is False
    assert tools[1].status == "available / 可用"
    assert all(tool.is_planned_only for tool in tools[2:])
    assert all(tool.status == "planned / 未启用" for tool in tools[2:])
    assert all(tool.boundary_statement for tool in tools)
    assert tools[1].requires_imagej_fiji is False


def test_labtools_module_exports_features() -> None:
    from app.labtools.workspace import labtools_features
    from app.shared.feature_status import FeatureStatus

    features = labtools_features()

    assert [feature.name for feature in features] == [
        "通用试剂制备",
        "Western Blot 工具",
        "PCR/qPCR 工具",
        "ELISA/吸光度工具",
        "细胞实验工具",
    ]
    assert features[0].status is FeatureStatus.TESTING
    assert features[1].status is FeatureStatus.TESTING
    assert all(features[index].status is FeatureStatus.UNAVAILABLE for index in (2, 3, 4))
    assert all(feature.module == "labtools" for feature in features)

    descriptions = {feature.name: feature.description for feature in features}
    assert "常用试剂快速计算" in descriptions["通用试剂制备"]
    assert "模板管理" in descriptions["通用试剂制备"]
    assert "承载全部实验计算" not in descriptions["通用试剂制备"]
    assert "流程工作台可用" in descriptions["Western Blot 工具"]
    assert "不启用 WB 图像分析" in descriptions["Western Blot 工具"]

    for name in ("PCR/qPCR 工具", "ELISA/吸光度工具", "细胞实验工具"):
        assert "占位" in descriptions[name] or "workflow" in descriptions[name]
        assert "算法已完成" not in descriptions[name]

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
        "imagej_fiji",
        "reagent_records",
        "cell_experiments",
        "western_blot",
        "pcr_qpcr",
        "elisa_absorbance",
    )
    assert widget.current_page_key() == "home"
    assert widget.findChild(QPushButton, "primaryButton") is not None
    widget.show_calculators()
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
    widget.show_recipes()
    assert widget.current_page_key() == "reagent_records"
    placeholder_labels = "\n".join(label.text() for label in widget.findChildren(QLabel))
    assert "试剂与实验记录" in placeholder_labels
    assert "recipe draft store 与 recipe import/export 现有能力后续归入本模块" in placeholder_labels
    assert "experiment template draft 与 experiment record draft JSON persistence 后续归入本模块" in placeholder_labels
    assert "不等同于完整 ELN" in placeholder_labels
    widget.show_image_analysis()
    assert widget.current_page_key() == "imagej_fiji"
    image_labels = "\n".join(label.text() for label in widget.findChildren(QLabel))
    assert "ImageJ 本地引擎配置" in image_labels
    assert "Fiji 增强路径" in image_labels
    assert "manual-review workflow 准备" in image_labels
    widget.show_templates()
    assert widget.current_page_key() == "reagent_records"
    widget.show_western_blot()
    assert widget.current_page_key() == "western_blot"
    western_text = "\n".join(label.text() for label in widget._stack.currentWidget().findChildren(QLabel))
    assert "Western Blot 流程工作台：available / 可用" in western_text
    assert "结果与灰度分析：placeholder / 未启用" in western_text
    widget.show_pcr_qpcr()
    assert widget.current_page_key() == "pcr_qpcr"
    widget.show_elisa_absorbance()
    assert widget.current_page_key() == "elisa_absorbance"


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
