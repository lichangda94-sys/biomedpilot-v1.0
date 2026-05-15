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
    assert "WB 上样计算、条带定量 workflow 占位。" in text
    assert "planned / 未启用" in text


def test_western_blot_entry_opens_planned_detail_page(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    text = _visible_text(widget._stack.currentWidget())

    assert widget.current_page_key() == "western_blot"
    assert "当前状态：planned / 未启用" in text
    assert "可做内容：未来将支持什么" in text
    assert "当前不可做内容" in text
    assert "后续开发前需要 Tool Logic Card" in text
    assert "ImageJ/Fiji 本地引擎状态" in text


def test_western_blot_planned_detail_keeps_algorithm_boundaries(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    text = _visible_text(widget._stack.currentWidget())

    assert "WB 上样体系计算和实验记录入口" in text
    assert "条带定量 workflow 的人工复核式整理" in text
    assert "不启用 WB/gel 真实分析" in text
    assert "不做条带自动识别或自动 ROI" in text
    assert "不替代人工判断、试剂盒说明书或实验室 SOP" in text


def test_sds_page_and_wb_grayscale_are_planned_not_completed(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    widget.show_western_blot()
    text = _visible_text(widget._stack.currentWidget())

    assert "planned / 未启用" in text
    assert "不启用 WB/gel 真实分析" in text
    assert "当前不会运行真实图像分析" in text
    for forbidden in (
        "蛋白上样体系计算: 已实现 / 辅助计算草稿",
        "SDS-PAGE 配胶模板与批量配制: 已实现 / 用户模板换算",
        "BCA 蛋白浓度测定: 已实现 / 辅助计算草稿",
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
