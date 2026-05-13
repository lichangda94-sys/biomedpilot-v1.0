from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_labtools_module_exports_features() -> None:
    from app.labtools.workspace import labtools_features

    features = labtools_features()

    assert [feature.name for feature in features] == ["实验计算器", "试剂与配方", "图像定量", "实验模板"]
    assert features[0].status.value == "测试中"
    assert features[1].status.value == "测试中"
    assert features[2].status.value == "测试中"
    assert features[3].status.value == "测试中"
    assert all(feature.module == "labtools" for feature in features)
    assert "WB/SDS-PAGE 上样计算" in features[0].description

    image_feature = features[2]
    assert "荧光 manual ROI grayscale" in image_feature.description
    assert "scratch/wound manual ROI + threshold" in image_feature.description
    assert "细胞计数、灰度/墨值仍为占位" in image_feature.description
    assert "算法开发中" not in image_feature.description
    assert "algorithm in development" not in image_feature.description.lower()

    template_feature = features[3]
    assert "qPCR" in template_feature.description
    assert "结构化草稿" in template_feature.description


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
    assert widget.page_keys() == ("home", "calculators", "recipes", "image_analysis", "templates")
    assert widget.current_page_key() == "home"
    assert widget.findChild(QPushButton, "primaryButton") is not None
    widget.show_calculators()
    tabs = widget.findChild(QTabWidget, "labToolsCalculatorTabs")
    assert tabs is not None
    assert [tabs.tabText(index) for index in range(tabs.count())] == ["浓度换算", "稀释计算", "溶液配制", "细胞接种", "qPCR 配液", "WB 上样"]
    calculator_labels = "\n".join(label.text() for label in widget.findChildren(QLabel))
    assert "实验计算器中心" in calculator_labels
    assert "本地辅助计算：稀释、摩尔浓度换算、细胞接种" in calculator_labels
    assert "不替代实验 SOP" in calculator_labels
    assert "溶液稀释" in calculator_labels or "C1V1 = C2V2 稀释计算" in calculator_labels
    assert "摩尔浓度" in calculator_labels
    assert "细胞接种" in calculator_labels
    assert "WB / SDS-PAGE 上样计算" in calculator_labels
    assert "不做 WB/凝胶灰度或条带分析" in calculator_labels
    assert "人工复核" in calculator_labels or "结果仅供实验前核对" in calculator_labels
    widget.show_recipes()
    assert widget.current_page_key() == "recipes"
    recipe_tabs = widget.findChild(QTabWidget, "recipeWorkspaceTabs")
    assert recipe_tabs is not None
    assert [recipe_tabs.tabText(index) for index in range(recipe_tabs.count())] == ["本地配方库", "用户配方", "外部来源草稿"]
    recipe_labels = "\n".join(label.text() for label in widget.findChildren(QLabel))
    recipe_buttons = [button.text() for button in widget.findChildren(QPushButton)]
    assert "本地配方草稿持久化" in recipe_labels
    assert "不自动保存、不联网、不调用 AI" in recipe_labels
    assert "保存用户配方 JSON" in recipe_buttons
    assert "载入用户配方 JSON" in recipe_buttons
    widget.show_image_analysis()
    assert widget.current_page_key() == "image_analysis"
    image_labels = "\n".join(label.text() for label in widget.findChildren(QLabel))
    image_buttons = [button.text() for button in widget.findChildren(QPushButton)]
    assert "MVP 可用：manual ROI grayscale 指标；需人工复核" in image_labels
    assert "MVP 可用：manual ROI + user threshold 面积估算；semi-quantitative" in image_labels
    assert image_labels.count("占位：algorithm_not_available，未生成定量结果") == 2
    assert "未启用自动 ROI、细胞计数或灰度/墨值算法" in image_labels
    assert "JSON manifest、CSV summary、Markdown 片段和 ROI overlay PNG" in image_labels
    assert "导出当前 ROI 结果" in image_buttons
    widget.show_templates()
    assert widget.current_page_key() == "templates"
    template_labels = "\n".join(label.text() for label in widget.findChildren(QLabel))
    template_buttons = [button.text() for button in widget.findChildren(QPushButton)]
    assert "实验模板" in template_labels
    assert "不构成完整 ELN" in template_labels
    assert "生成记录草稿" in template_buttons
