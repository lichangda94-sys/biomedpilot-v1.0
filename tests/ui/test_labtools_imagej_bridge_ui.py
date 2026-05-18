from __future__ import annotations

import os
from dataclasses import replace

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


def _bridge(tmp_path, status=None):
    from app.shared.local_engines import IMAGEJ_FIJI_ENGINE_ID, ImageJFijiBridge, LocalEngineConfig, LocalEngineConfigStore

    store = LocalEngineConfigStore(IMAGEJ_FIJI_ENGINE_ID, tmp_path / "imagej_fiji.json")
    bridge = ImageJFijiBridge(store)
    if status is not None:
        store.save(
            LocalEngineConfig(
                engine_id=IMAGEJ_FIJI_ENGINE_ID,
                configured_path_or_endpoint=status.configured_path_or_endpoint,
                last_status=status,
            )
        )
    return bridge


def test_image_related_entry_shows_missing_imagej_setup_prompt_without_crash(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QPushButton

    from app.labtools.ui.image_analysis_widgets import LabToolsImageAnalysisWidget

    widget = LabToolsImageAnalysisWidget(imagej_bridge=_bridge(tmp_path))
    text = _visible_text(widget)

    assert "ImageJ 本地后端状态" in text
    assert "未配置" in text
    assert "需要本机 ImageJ" in text
    assert "Fiji 仅作为增强引擎保留" in text
    assert "BioMedPilot 不会静默下载" in text
    assert widget.findChild(QPushButton, "imageJFijiAutoDetectButton") is not None
    assert widget.findChild(QPushButton, "imageJFijiChoosePathButton") is not None
    assert widget.findChild(QPushButton, "imageJFijiDownloadRuntimeButton") is not None
    assert widget.findChild(QPushButton, "imageJFijiInstallGuideButton") is not None


def test_available_imagej_status_is_displayed_in_image_area(qapp, tmp_path) -> None:
    from app.labtools.ui.image_analysis_widgets import LabToolsImageAnalysisWidget
    from app.shared.local_engines import ENGINE_STATUS_AVAILABLE, default_imagej_fiji_status

    status = replace(
        default_imagej_fiji_status(ENGINE_STATUS_AVAILABLE, configured_path="/Applications/Fiji.app"),
        detected_version="2.14.0",
        smoke_test_result="status=ok",
    )
    widget = LabToolsImageAnalysisWidget(imagej_bridge=_bridge(tmp_path, status))
    text = _visible_text(widget)

    assert "可用" in text
    assert "2.14.0" in text
    assert "不表示任何具体图像分析算法已经实现" in text


def test_failed_imagej_validation_shows_safe_error_state(qapp, tmp_path) -> None:
    from app.labtools.ui.image_analysis_widgets import LabToolsImageAnalysisWidget
    from app.shared.local_engines import ENGINE_STATUS_FAILED, default_imagej_fiji_status

    status = default_imagej_fiji_status(
        ENGINE_STATUS_FAILED,
        configured_path="/bad/path",
        last_error="Fiji/ImageJ 路径无效或不可执行",
    )
    widget = LabToolsImageAnalysisWidget(imagej_bridge=_bridge(tmp_path, status))
    text = _visible_text(widget)

    assert "验证失败" in text
    assert "路径无效" in text
    assert "Traceback" not in text


def test_existing_manual_roi_tools_remain_accessible(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QPushButton

    from app.labtools.ui.image_analysis_widgets import LabToolsImageAnalysisWidget

    widget = LabToolsImageAnalysisWidget(imagej_bridge=_bridge(tmp_path))
    text = _visible_text(widget)

    assert "荧光强度 ROI 分析 MVP" in text
    assert "划痕实验面积分析 MVP" in text
    assert "manual ROI" in text
    assert widget.findChild(QPushButton, "secondaryButton") is not None
    assert "正式报告" not in text
    assert "无需人工复核" not in text


def test_western_blot_grayscale_area_is_placeholder_not_imagej_status(qapp, tmp_path) -> None:
    from app.labtools.ui.western_blot_widgets import LabToolsWesternBlotWidget

    widget = LabToolsWesternBlotWidget(imagej_bridge=_bridge(tmp_path))
    text = _visible_text(widget)

    assert "结果与灰度分析" in text
    assert "ImageJ 本地后端状态" not in text
    assert "Western Blot 灰度分析 workflow" not in text
    assert "需要本机 ImageJ" not in text
    assert "自动条带识别" in text
    assert "WB 灰度分析已完成" not in text
    assert "自动 ROI 已完成" not in text
    assert "细胞计数已完成" not in text


def test_non_image_labtools_workspace_is_not_blocked_by_missing_imagej(qapp) -> None:
    from PySide6.QtWidgets import QTabWidget

    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()

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
    widget.show_general_calculators()
    tabs = widget.findChild(QTabWidget, "labToolsCalculatorTabs")

    assert tabs is not None
    assert [tabs.tabText(index) for index in range(tabs.count())] == ["快速计算", "试剂制备"]
    quick_tabs = widget.findChild(QTabWidget, "labToolsQuickCalculatorTabs")
    assert quick_tabs is not None
    assert quick_tabs.tabText(0) == "浓度换算"
    assert "ImageJ 本地后端状态" not in _visible_text(widget._stack.currentWidget())


def test_labtools_home_is_workbench_not_imagej_only_page(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    text = _visible_text(widget._stack.currentWidget())

    for entry in (
        "通用试剂制备",
        "Western Blot 工具",
        "PCR/qPCR 工具",
        "ELISA/吸光度工具",
        "细胞实验工具",
    ):
        assert entry in text
    assert "ImageJ 本地引擎" not in text
    assert "图像能力边界" not in text
    assert "本地引擎状态摘要" not in text
    assert "ImageJ 本地后端状态" not in text


def test_labtools_home_opens_calculator_and_header_opens_imagej_config_pages(qapp) -> None:
    from PySide6.QtWidgets import QFrame, QPushButton, QTabWidget

    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()

    calculator_entry = widget.findChild(QFrame, "labToolsGeneralCalculatorEntry")
    assert calculator_entry is not None
    calculator_entry.findChild(QPushButton).click()
    assert widget.current_page_key() == "general_calculators"
    tabs = widget.findChild(QTabWidget, "labToolsCalculatorTabs")
    assert tabs is not None
    assert [tabs.tabText(index) for index in range(tabs.count())] == ["快速计算", "试剂制备"]
    quick_tabs = widget.findChild(QTabWidget, "labToolsQuickCalculatorTabs")
    assert quick_tabs is not None
    assert quick_tabs.tabText(0) == "浓度换算"

    widget.show_home()
    imagej_entry = widget.findChild(QFrame, "labToolsImageJFijiEntry")
    assert imagej_entry is None
    widget.findChild(QPushButton, "labToolsExternalEngineSettingsButton").click()
    assert widget.current_page_key() == "imagej_fiji"
    text = _visible_text(widget._stack.currentWidget())
    assert "ImageJ 本地引擎配置" in text
    assert "ImageJ 本地后端状态" in text
    assert "Fiji 增强路径" in text
    assert widget.findChild(QPushButton, "imageJFijiAutoDetectButton") is not None


def test_labtools_copy_uses_imagej_fiji_spelling_and_no_enabled_algorithm_claims(qapp) -> None:
    from app.labtools.workspace import LabToolsWorkspaceWidget

    widget = LabToolsWorkspaceWidget()
    text = _visible_text(widget)

    for forbidden in (
        "ImageG",
        "Fuji",
        "已启用 WB/gel 真实分析",
        "自动 ROI 已启用",
        "细胞计数已启用",
    ):
        assert forbidden not in text
