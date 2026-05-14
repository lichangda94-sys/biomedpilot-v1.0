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


def test_western_blot_module_entry_exists(qapp) -> None:
    from PySide6.QtWidgets import QFrame

    from app.labtools.labtools_home import LabToolsHomeWidget

    widget = LabToolsHomeWidget()
    text = _visible_text(widget)

    assert widget.findChild(QFrame, "labToolsWesternBlotEntry") is not None
    assert "Western Blot" in text
    assert "查看 Western Blot 规划" in text


def test_western_blot_page_contains_five_placeholder_sections(qapp) -> None:
    from PySide6.QtWidgets import QFrame

    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    page = widget._stack.currentWidget()
    text = _visible_text(page)

    assert widget.current_page_key() == "western_blot"
    assert len(page.findChildren(QFrame, "labToolsWesternBlotSectionCard")) == 5
    for section in (
        "蛋白样品准备",
        "蛋白浓度测定",
        "上样与胶",
        "电泳 / 转膜 / 抗体孵育流程",
        "结果与灰度分析",
    ):
        assert section in text
    assert text.count("待确认使用逻辑 / 规划中 / 暂未开放") >= 5


def test_western_blot_section_descriptions_are_scaffold_only(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    text = _visible_text(widget._stack.currentWidget())

    assert "用于记录蛋白提取、裂解液/抑制剂草稿、样本分组和实验室自定义流程。当前为流程模板入口，不自动生成唯一实验方案。" in text
    assert "提供 BCA、Bradford、NanoDrop 等蛋白浓度测定入口；底层逻辑后续与吸光度/标准曲线能力复用。" in text
    assert "用于蛋白上样体系计算、loading buffer、还原剂、SDS-PAGE 配胶模板和批量配制计算。" in text
    assert "用于记录电泳参数、电转参数、封闭、一抗、二抗和洗膜步骤模板。用户可录入试剂盒说明书或实验室成熟流程。" in text
    assert "用于后续 WB/gel grayscale、条带 ROI、背景扣除、target/loading control ratio 和结果导出。开发前需单独确认图像分析逻辑。" in text


def test_sds_page_and_wb_grayscale_are_planned_not_completed(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    text = _visible_text(widget._stack.currentWidget())

    assert "蛋白上样体系计算: 待确认使用逻辑 / 规划中 / 暂未开放" in text
    assert "SDS-PAGE 配胶模板与批量配制: 待确认使用逻辑 / 规划中 / 暂未开放" in text
    assert "WB/gel grayscale" in text
    assert "开发前需单独确认图像分析逻辑" in text
    for forbidden in (
        "SDS-PAGE 配胶已完成",
        "胶浓度自动推导已完成",
        "WB 灰度分析已完成",
        "WB/gel grayscale completed",
        "自动配方推荐已完成",
    ):
        assert forbidden not in text


def test_western_blot_scaffold_avoids_misleading_result_or_sop_claims(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    text = _visible_text(widget._stack.currentWidget())

    for forbidden in ("正式 SOP", "自动诊断", "无需人工复核", "production-grade"):
        assert forbidden not in text
