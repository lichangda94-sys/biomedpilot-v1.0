from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


MODULE_DESCRIPTIONS = {
    "通用试剂计算器": "浓度、质量、体积、摩尔量、稀释快速计算，以及用户自定义试剂模板、本次配制换算和子模板展开。",
    "ImageJ/Fiji 本地引擎": "用于图像 workflow 的本地 ImageJ/Fiji 检测与路径配置。",
    "Western Blot 工具": "WB 上样计算、条带定量 workflow 占位。",
    "PCR/qPCR 工具": "PCR mix、qPCR 结果整理 workflow 占位。",
    "ELISA/吸光度工具": "标准曲线、OD 数据整理 workflow 占位。",
    "细胞实验工具": "细胞接种、处理分组、实验记录 workflow 占位。",
}

ENTRY_OBJECTS = {
    "通用试剂计算器": "labToolsGeneralCalculatorEntry",
    "ImageJ/Fiji 本地引擎": "labToolsImageJFijiEntry",
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


def test_labtools_home_exposes_six_top_level_module_entries(qapp) -> None:
    from PySide6.QtWidgets import QFrame

    from app.labtools.labtools_home import LabToolsHomeWidget
    from app.labtools.labtools_tool_registry import labtools_tool_registry

    widget = LabToolsHomeWidget()
    text = _visible_text(widget)

    for tool in labtools_tool_registry():
        assert tool.chinese_name in text
        assert tool.english_name in text
        assert widget.findChild(QFrame, tool.object_name) is not None
    assert len(labtools_tool_registry()) == 6


def test_labtools_home_module_descriptions_match_architecture_copy(qapp) -> None:
    from app.labtools.labtools_home import LabToolsHomeWidget

    text = _visible_text(LabToolsHomeWidget())

    for description in MODULE_DESCRIPTIONS.values():
        assert description in text


def test_specialized_module_entries_are_planned_not_completed_algorithms(qapp) -> None:
    from PySide6.QtWidgets import QFrame

    from app.labtools.labtools_home import LabToolsHomeWidget

    widget = LabToolsHomeWidget()
    forbidden = ("已完成算法", "算法已完成", "自动分析已开放", "正式报告", "临床诊断", "无需人工复核")
    for title in ("Western Blot 工具", "PCR/qPCR 工具", "ELISA/吸光度工具", "细胞实验工具"):
        frame = widget.findChild(QFrame, ENTRY_OBJECTS[title])
        assert frame is not None
        text = _visible_text(frame)
        assert "planned / 未启用" in text
        assert "已开放" not in text
        for term in forbidden:
            assert term not in text


def test_general_calculator_is_not_described_as_all_experiment_calculation(qapp) -> None:
    from PySide6.QtWidgets import QFrame

    from app.labtools.labtools_home import LabToolsHomeWidget

    widget = LabToolsHomeWidget()
    frame = widget.findChild(QFrame, "labToolsGeneralCalculatorEntry")
    assert frame is not None
    text = _visible_text(frame)

    assert "通用试剂计算器" in text
    assert "全部实验计算" not in text
    assert "承载全部实验" not in text


def test_planned_tool_detail_pages_keep_logic_card_and_boundaries(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    planned_routes = (
        (widget.show_cell_experiments, "cell_experiments", "细胞实验工具"),
        (widget.show_western_blot, "western_blot", "Western Blot 工具"),
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
