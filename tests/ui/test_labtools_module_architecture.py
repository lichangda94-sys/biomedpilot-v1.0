from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


MODULE_DESCRIPTIONS = {
    "通用试剂制备": "用于常用试剂快速计算、模板管理和本次制备清单生成。",
    "Western Blot 工具": "Western Blot 流程工作台可用，覆盖样品准备、BCA、上样计算、配胶与 Lane 布局及关键流程记录。",
    "PCR/qPCR 工具": "PCR mix、qPCR 结果整理 workflow 占位。",
    "ELISA/吸光度工具": "标准曲线、OD 数据整理 workflow 占位。",
    "细胞实验工具": "细胞接种、处理分组、实验记录 workflow 占位。",
}

ENTRY_OBJECTS = {
    "通用试剂制备": "labToolsGeneralCalculatorEntry",
    "Western Blot 工具": "labToolsWesternBlotEntry",
    "PCR/qPCR 工具": "labToolsPcrQpcrEntry",
    "ELISA/吸光度工具": "labToolsElisaAbsorbanceEntry",
    "细胞实验工具": "labToolsCellExperimentEntry",
}


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


def test_labtools_home_exposes_five_top_level_module_entries(qapp) -> None:
    from PySide6.QtWidgets import QFrame

    from app.labtools.labtools_home import LabToolsHomeWidget
    from app.labtools.labtools_tool_registry import labtools_tool_registry

    widget = LabToolsHomeWidget()
    text = _visible_text(widget)

    for tool in labtools_tool_registry():
        assert tool.chinese_name in text
        assert tool.english_name in text
        assert widget.findChild(QFrame, tool.object_name) is not None
    assert len(labtools_tool_registry()) == 5


def test_labtools_home_module_descriptions_match_architecture_copy(qapp) -> None:
    from app.labtools.labtools_home import LabToolsHomeWidget

    text = _visible_text(LabToolsHomeWidget())

    for description in MODULE_DESCRIPTIONS.values():
        assert description in text


def test_specialized_module_entries_keep_status_boundaries(qapp) -> None:
    from PySide6.QtWidgets import QFrame

    from app.labtools.labtools_home import LabToolsHomeWidget

    widget = LabToolsHomeWidget()
    forbidden = ("已完成算法", "算法已完成", "自动分析已开放", "正式报告", "临床诊断", "无需人工复核")
    for title in ("PCR/qPCR 工具", "ELISA/吸光度工具", "细胞实验工具"):
        frame = widget.findChild(QFrame, ENTRY_OBJECTS[title])
        assert frame is not None
        text = _visible_text(frame)
        assert "planned / 未启用" in text
        assert "已开放" not in text
        for term in forbidden:
            assert term not in text
    western_frame = widget.findChild(QFrame, ENTRY_OBJECTS["Western Blot 工具"])
    assert western_frame is not None
    western_text = _visible_text(western_frame)
    assert "available / 可用" in western_text
    assert "不启用 WB 图像分析" in western_text
    for term in forbidden:
        assert term not in western_text


def test_general_calculator_is_not_described_as_all_experiment_calculation(qapp) -> None:
    from PySide6.QtWidgets import QFrame

    from app.labtools.labtools_home import LabToolsHomeWidget

    widget = LabToolsHomeWidget()
    frame = widget.findChild(QFrame, "labToolsGeneralCalculatorEntry")
    assert frame is not None
    text = _visible_text(frame)

    assert "通用试剂制备" in text
    assert "进入通用试剂制备" in text
    assert "打开计算器" not in text
    assert "全部实验计算" not in text
    assert "承载全部实验" not in text


def test_planned_tool_detail_pages_keep_logic_card_and_boundaries(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_cell_experiments()
    cell_text = _visible_text(widget._stack.currentWidget())
    assert widget.current_page_key() == "cell_experiments"
    assert "细胞实验工具" in cell_text
    assert "划痕实验图像分析" in cell_text
    assert "Transwell 图像分析" in cell_text
    assert "荧光图像分析" in cell_text
    assert "本阶段只生成任务、Macro 模板映射和 RunRequest" in cell_text

    planned_routes = (
        (widget.show_pcr_qpcr, "pcr_qpcr", "PCR/qPCR 工具"),
        (widget.show_elisa_absorbance, "elisa_absorbance", "ELISA/吸光度工具"),
    )

    for show_page, key, title in planned_routes:
        show_page()
        assert widget.current_page_key() == key
        text = _visible_text(widget._stack.currentWidget())
        assert title in text
        assert "当前状态：planned / 未启用" in text
        assert "可做内容：未来将支持什么" in text
        assert "当前不可做内容" in text
        assert "后续开发前需要 Tool Logic Card" in text
        assert "不替代人工判断" in text or "不替代人工复核" in text or "不替代试剂盒说明书" in text


def test_western_blot_available_page_keeps_image_analysis_disabled(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    text = _visible_text(widget._stack.currentWidget())

    assert widget.current_page_key() == "western_blot"
    assert "Western Blot 流程工作台：available / 可用" in text
    assert "结果与灰度分析：placeholder / 未启用" in text
    assert "不启用 WB 图像分析、条带识别、灰度定量、自动 ROI" in text


def test_main_window_can_instantiate_labtools_workspace_offscreen(qapp) -> None:
    from PySide6.QtWidgets import QPushButton

    from app.shell.main_window import MainWindow

    window = MainWindow()
    try:
        window._login_page.set_credentials("researcher", "local-password")
        window._login_page.attempt_login()
        labtools_button = window._dashboard_page.findChild(QPushButton, "labToolsModuleButton")
        labtools_button.click()

        assert window.current_workspace_key() == "labtools"
        assert window._labtools_page.page_keys() == (
            "home",
            "general_calculators",
            "imagej_fiji",
            "reagent_records",
            "cell_experiments",
            "western_blot",
            "pcr_qpcr",
            "elisa_absorbance",
        )
    finally:
        window.close()
        window.deleteLater()
        qapp.processEvents()
