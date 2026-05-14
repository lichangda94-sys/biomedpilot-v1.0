from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_labtools_module_exports_features() -> None:
    from app.labtools.workspace import labtools_features
    from app.shared.feature_status import FeatureStatus

    features = labtools_features()

    assert [feature.name for feature in features] == [
        "通用试剂计算器",
        "ImageJ/Fiji 本地引擎",
        "试剂与实验记录",
        "细胞实验",
        "Western Blot",
        "PCR / qPCR",
        "ELISA / 吸光度与标准曲线",
    ]
    assert features[0].status is FeatureStatus.TESTING
    assert features[1].status is FeatureStatus.TESTING
    assert features[2].status is FeatureStatus.TESTING
    assert all(features[index].status is FeatureStatus.UNAVAILABLE for index in (3, 4, 5, 6))
    assert all(feature.module == "labtools" for feature in features)

    descriptions = {feature.name: feature.description for feature in features}
    assert "浓度、质量、体积、摩尔量、稀释" in descriptions["通用试剂计算器"]
    assert "不长期承载全部实验特异性计算" in descriptions["通用试剂计算器"]
    assert "承载全部实验计算" not in descriptions["通用试剂计算器"]
    assert "ImageJ/Fiji 检测与路径配置" in descriptions["ImageJ/Fiji 本地引擎"]
    assert "不启用真实图像分析算法" in descriptions["ImageJ/Fiji 本地引擎"]
    assert "本地 recipe 草稿" in descriptions["试剂与实验记录"]
    assert "不等同于完整 ELN" in descriptions["试剂与实验记录"]

    for name in ("细胞实验", "Western Blot", "PCR / qPCR", "ELISA / 吸光度与标准曲线"):
        assert "规划中" in descriptions[name]
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
    assert [tabs.tabText(index) for index in range(tabs.count())] == ["浓度换算", "稀释计算", "溶液配制"]
    calculator_labels = "\n".join(label.text() for label in widget._stack.currentWidget().findChildren(QLabel))
    assert "通用试剂计算器" in calculator_labels
    assert "本地基础实验计算：浓度换算、摩尔量/质量/体积换算、C1V1 稀释和溶液配制" in calculator_labels
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
    assert "ImageJ/Fiji 本地引擎配置" in image_labels
    assert "manual-review workflow 准备" in image_labels
    widget.show_templates()
    assert widget.current_page_key() == "reagent_records"
    widget.show_western_blot()
    assert widget.current_page_key() == "western_blot"
    widget.show_pcr_qpcr()
    assert widget.current_page_key() == "pcr_qpcr"
    widget.show_elisa_absorbance()
    assert widget.current_page_key() == "elisa_absorbance"
