from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


MODULE_DESCRIPTIONS = {
    "通用计算器": "用于浓度、分子量、质量、体积、稀释、称量和后续 pH/酸碱度等通用试剂计算。",
    "试剂与实验记录": "用于本地 recipe 草稿、实验记录草稿、模板保存和 JSON 导入导出；不等同于完整 ELN。",
    "细胞实验": "用于细胞接种、活率、Transwell、wound healing、增殖率、台盼蓝、Alamar Blue 等细胞实验工具。",
    "Western Blot": "用于蛋白样品准备、蛋白浓度测定入口、上样体系、SDS-PAGE 配胶、电泳/转膜参数、抗体孵育流程和后续灰度分析。",
    "PCR / qPCR": "用于 PCR/qPCR 体系计算、运行参数、plate layout、Ct / ΔCt / ΔΔCt 结果分析。",
    "ELISA / 吸光度与标准曲线": "用于 OD 值、标准曲线、BCA、Bradford、NanoDrop、ELISA 样本浓度反推等。",
}

ENTRY_OBJECTS = {
    "通用计算器": "labToolsGeneralCalculatorEntry",
    "试剂与实验记录": "labToolsReagentRecordsEntry",
    "细胞实验": "labToolsCellExperimentEntry",
    "Western Blot": "labToolsWesternBlotEntry",
    "PCR / qPCR": "labToolsPcrQpcrEntry",
    "ELISA / 吸光度与标准曲线": "labToolsElisaAbsorbanceEntry",
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

    widget = LabToolsHomeWidget()
    text = _visible_text(widget)

    for title, object_name in ENTRY_OBJECTS.items():
        assert title in text
        assert widget.findChild(QFrame, object_name) is not None
    assert len(ENTRY_OBJECTS) == 6


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
    for title in ("细胞实验", "Western Blot", "PCR / qPCR", "ELISA / 吸光度与标准曲线"):
        frame = widget.findChild(QFrame, ENTRY_OBJECTS[title])
        assert frame is not None
        text = _visible_text(frame)
        assert "规划中 / 待确认使用逻辑 / 暂未开放" in text
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

    assert "通用试剂计算" in text
    assert "全部实验计算" not in text
    assert "承载全部实验" not in text


def test_module_placeholder_pages_keep_logic_confirmation_boundary(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    planned_routes = (
        (widget.show_cell_experiments, "cell_experiments", "细胞实验"),
        (widget.show_western_blot, "western_blot", "Western Blot"),
        (widget.show_pcr_qpcr, "pcr_qpcr", "PCR / qPCR"),
        (widget.show_elisa_absorbance, "elisa_absorbance", "ELISA / 吸光度与标准曲线"),
    )

    for show_page, key, title in planned_routes:
        show_page()
        assert widget.current_page_key() == key
        text = _visible_text(widget._stack.currentWidget())
        assert title in text
        assert "待确认使用逻辑" in text
        assert "暂未开放" in text
        if key == "western_blot":
            assert "基于用户录入的试剂盒/实验室模板进行批量换算" in text
            assert "不进行自动配方推荐" in text
        else:
            assert "不新增算法、公式、图像处理、schema 或导出格式" in text


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
            "reagent_records",
            "cell_experiments",
            "western_blot",
            "pcr_qpcr",
            "elisa_absorbance",
            "imagej_fiji_bridge",
        )
    finally:
        window.close()
        window.deleteLater()
        qapp.processEvents()
