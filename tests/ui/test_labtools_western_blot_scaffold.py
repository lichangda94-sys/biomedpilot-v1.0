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
    assert "Western Blot 工具" in text
    assert "Western Blot 流程工作台可用" in text
    assert "available / 可用" in text


def test_western_blot_entry_opens_available_tool_page(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    text = _visible_text(widget._stack.currentWidget())

    assert widget.current_page_key() == "western_blot"
    assert "Western Blot 流程工作台：available / 可用" in text
    assert "结果与灰度分析：placeholder / 未启用" in text
    assert "配胶与 Lane 布局" in text


def test_western_blot_tabs_follow_flow_workbench_order(qapp) -> None:
    from PySide6.QtWidgets import QTabWidget

    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    tabs = widget._stack.currentWidget().findChild(QTabWidget, "westernBlotTabs")

    assert [tabs.tabText(index) for index in range(tabs.count())] == [
        "流程工作台",
        "蛋白样品准备",
        "BCA 蛋白浓度测定",
        "蛋白上样计算",
        "配胶与 Lane 布局",
        "电泳记录",
        "电转记录",
        "封闭记录",
        "一抗孵育记录",
        "一抗后洗膜记录",
        "二抗孵育记录",
        "二抗后洗膜记录",
        "显影/成像记录",
        "结果与灰度分析",
    ]


def test_western_blot_page_keeps_algorithm_boundaries(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    text = _visible_text(widget._stack.currentWidget())

    assert "Western Blot 上样计算器" in text
    assert "不启用 WB 图像分析" in text
    assert "条带识别" in text
    assert "自动 ROI" in text
    assert "本工具不判断实验设计合理性" in text


def test_wb_grayscale_is_planned_not_completed(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    text = _visible_text(widget._stack.currentWidget())

    assert "placeholder / 未启用" in text
    assert "不启用 WB 图像分析" in text
    assert "结果解释" in text
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
