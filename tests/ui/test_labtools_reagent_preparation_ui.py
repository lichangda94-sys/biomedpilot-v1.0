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


@pytest.fixture()
def reagent_workflow(qapp, tmp_path):
    from app.labtools.reagent_templates import ReagentTemplateStore
    from app.labtools.ui.calculator_widgets import ReagentPreparationWorkflowWidget

    store = ReagentTemplateStore(tmp_path / "reagent_templates.json")
    widget = ReagentPreparationWorkflowWidget(store)
    widget.show()
    qapp.processEvents()
    yield widget, store
    widget.close()
    widget.deleteLater()
    qapp.processEvents()


def _child(widget, cls, object_name: str):
    item = widget.findChild(cls, object_name)
    assert item is not None, object_name
    return item


def _save_basic_template(widget) -> None:
    from PySide6.QtWidgets import QCheckBox, QLineEdit, QPushButton

    _child(widget, QLineEdit, "reagentTemplateNameField").setText("PBS 1x")
    _child(widget, QLineEdit, "reagentTemplateDefaultVolumeField").setText("100")
    _child(widget, QLineEdit, "reagentTemplateDefaultStrengthField").setText("1X")
    _child(widget, QLineEdit, "reagentComponentNameField").setText("NaCl")
    _child(widget, QLineEdit, "reagentComponentAmountField").setText("0.8")
    _child(widget, QCheckBox, "reagentComponentScaleVolumeCheck").setChecked(True)
    _child(widget, QCheckBox, "reagentComponentContributesVolumeCheck").setChecked(False)
    _child(widget, QPushButton, "reagentTemplateAddComponentButton").click()
    _child(widget, QPushButton, "reagentTemplateSaveButton").click()


def test_reagent_preparation_workflow_exposes_connected_c2_surface(reagent_workflow) -> None:
    from PySide6.QtWidgets import QPushButton, QWidget

    widget, _store = reagent_workflow
    template_manager = _child(widget, QWidget, "labToolsReagentTemplateManager")
    preparation = _child(widget, QWidget, "labToolsReagentPreparationWorkspace")

    assert widget.objectName() == "labToolsReagentPreparationFlow"
    assert widget.property("uiPrimitive") == "labtools_c2_reagent_workflow"
    assert widget.property("connectionStatus") == "connected"
    assert widget.property("formalActionEnabled") is False
    assert template_manager.property("uiPrimitive") == "labtools_c2_reagent_template_manager"
    assert preparation.property("uiPrimitive") == "labtools_c2_reagent_preparation"
    assert _child(widget, QPushButton, "reagentTemplateSaveButton").property("buttonBehavior") == "upserts_reagent_template_local_json"
    assert _child(widget, QPushButton, "preparationCalculateButton").property("buttonBehavior") == "generates_reagent_preparation_preview_without_record_write"


def test_reagent_template_save_writes_local_json_artifact(reagent_workflow) -> None:
    from PySide6.QtWidgets import QTextEdit

    widget, store = reagent_workflow
    _save_basic_template(widget)

    templates = store.load()
    status = _child(widget, QTextEdit, "reagentTemplateStatusPanel").toPlainText()

    assert store.resolved_path().exists()
    assert len(templates) == 1
    assert templates[0].name == "PBS 1x"
    assert templates[0].components[0].name == "NaCl"
    assert "模板已保存" in status
    assert str(store.resolved_path()) in status


def test_reagent_preparation_generates_preview_artifact_without_record_write(reagent_workflow) -> None:
    from PySide6.QtWidgets import QLineEdit, QPushButton, QTextEdit

    widget, store = reagent_workflow
    _save_basic_template(widget)
    _child(widget, QPushButton, "preparationReloadTemplatesButton").click()
    _child(widget, QLineEdit, "preparationTargetVolumeField").setText("500")
    _child(widget, QLineEdit, "preparationOverageField").setText("10")
    _child(widget, QPushButton, "preparationCalculateButton").click()

    result = _child(widget, QTextEdit, "preparationResultPanel").toPlainText()

    assert "PBS 1x" in result
    assert "500" in result
    assert "NaCl" in result
    assert store.resolved_path().exists()
    assert not (store.resolved_path().parent / "preparation_records.json").exists()


def test_reagent_preparation_invalid_input_reports_disabled_reason(reagent_workflow) -> None:
    from PySide6.QtWidgets import QLineEdit, QPushButton, QTextEdit

    widget, _store = reagent_workflow
    _save_basic_template(widget)
    _child(widget, QPushButton, "preparationReloadTemplatesButton").click()
    _child(widget, QLineEdit, "preparationTargetVolumeField").setText("bad-value")
    _child(widget, QPushButton, "preparationCalculateButton").click()

    result = _child(widget, QTextEdit, "preparationResultPanel").toPlainText()

    assert "输入需要调整" in result
    assert "目标体积和损耗系数必须是有效数字" in result
