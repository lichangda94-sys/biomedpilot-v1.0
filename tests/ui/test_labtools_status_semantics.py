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


def test_labtools_feature_descriptions_keep_testing_and_draft_boundaries() -> None:
    from app.labtools.workspace import labtools_features
    from app.shared.feature_status import FeatureStatus

    features = {feature.name: feature for feature in labtools_features()}

    assert set(features) == {
        "通用试剂计算器",
        "ImageJ/Fiji 本地引擎",
        "Western Blot 工具",
        "PCR/qPCR 工具",
        "ELISA/吸光度工具",
        "细胞实验工具",
    }
    assert features["通用试剂计算器"].status is FeatureStatus.TESTING
    assert features["ImageJ/Fiji 本地引擎"].status is FeatureStatus.TESTING
    assert all(features[name].status is FeatureStatus.UNAVAILABLE for name in ("Western Blot 工具", "PCR/qPCR 工具", "ELISA/吸光度工具", "细胞实验工具"))
    assert "浓度、质量、体积、摩尔量、稀释" in features["通用试剂计算器"].description
    assert "不替代实验 SOP" in features["通用试剂计算器"].description
    assert "ImageJ/Fiji 检测与路径配置" in features["ImageJ/Fiji 本地引擎"].description
    assert "不是图像分析结果工具" in features["ImageJ/Fiji 本地引擎"].description
    for name in ("Western Blot 工具", "PCR/qPCR 工具", "ELISA/吸光度工具", "细胞实验工具"):
        assert "占位" in features[name].description or "workflow" in features[name].description


def test_labtools_home_status_cards_are_specific_not_broad_production_claims(qapp) -> None:
    from app.labtools.labtools_home import LabToolsHomeWidget

    widget = LabToolsHomeWidget()
    text = _visible_text(widget)

    for title in ("通用试剂计算器", "ImageJ/Fiji 本地引擎", "Western Blot 工具", "PCR/qPCR 工具", "ELISA/吸光度工具", "细胞实验工具"):
        assert title in text
    assert "available / 已接入" in text
    assert text.count("planned / 未启用") == 4
    assert "浓度、质量、体积、摩尔量、稀释等基础实验计算。" in text
    assert "图像能力边界" in text
    assert "本地引擎状态摘要" in text
    assert "未启用 WB/gel 真实分析" in text
    for forbidden in ("production-grade", "正式报告", "临床诊断", "无需人工复核", "算法已完成"):
        assert forbidden not in text


def test_image_analysis_status_preserves_manual_roi_and_placeholders(qapp) -> None:
    from app.labtools.ui.image_analysis_widgets import LabToolsImageAnalysisWidget

    widget = LabToolsImageAnalysisWidget()
    text = _visible_text(widget)

    assert "MVP 可用：manual ROI grayscale 指标；需人工复核" in text
    assert "MVP 可用：manual ROI + user threshold 面积估算；semi-quantitative" in text
    assert text.count("占位：algorithm_not_available，未生成定量结果") >= 2
    assert "不会自动识别细胞、划痕或条带" in text
    assert "用户阈值" in text
    assert "人工复核" in text
    for forbidden in ("自动细胞计数可用", "自动 ROI 可用", "WB/凝胶灰度可用", "无需人工复核"):
        assert forbidden not in text


def test_roi_export_success_text_is_auxiliary_not_formal_report(qapp, tmp_path, monkeypatch) -> None:
    from PIL import Image

    from app.labtools.image_analysis.fluorescence import (
        FluorescenceAnalysisParameters,
        FluorescenceROI,
        analyze_fluorescence_roi,
    )
    from app.labtools.ui.image_analysis_widgets import LabToolsImageAnalysisWidget

    image_path = tmp_path / "status-fluorescence.png"
    image = Image.new("L", (6, 3))
    image.putdata([20, 20, 20, 2, 2, 2, 20, 20, 20, 2, 2, 2, 20, 20, 20, 2, 2, 2])
    image.save(image_path)
    result = analyze_fluorescence_roi(
        FluorescenceAnalysisParameters(
            image_path=str(image_path),
            signal_roi=FluorescenceROI("signal", 0, 0, 3, 3, "signal"),
            background_roi=FluorescenceROI("background", 3, 0, 3, 3, "background"),
        ),
        task_id="status-ui-export",
    )
    widget = LabToolsImageAnalysisWidget()
    widget.set_export_result_for_testing("fluorescence_intensity", result)
    monkeypatch.setattr(widget, "_select_export_directory", lambda: str(tmp_path / "exports"))

    widget._handle_export_current_result()

    text = widget._task_summary.toPlainText()
    assert "导出成功" in text
    assert "manual ROI auxiliary analysis" in text
    assert "manual-review / semi-quantitative 辅助结果" in text
    assert "人工复核提示" in text
    for forbidden in ("正式报告", "正式结论", "临床诊断", "无需人工复核", "production-grade"):
        assert forbidden not in text


def test_recipe_and_experiment_draft_ui_keep_draft_non_eln_semantics(qapp) -> None:
    from app.labtools.ui.recipe_widgets import LabToolsRecipeWidget
    from app.labtools.ui.template_widgets import LabToolsTemplateWidget

    recipe_widget = LabToolsRecipeWidget()
    recipe_text = _visible_text(recipe_widget)
    assert "本地配方草稿持久化" in recipe_text
    assert "不会自动写盘" in recipe_text
    assert "人工核对" in recipe_text
    assert "SOP" in recipe_text
    assert "SDS" in recipe_text

    template_widget = LabToolsTemplateWidget()
    template_text = _visible_text(template_widget)
    assert "结构化记录草稿" in template_text
    assert "不自动保存" in template_text
    assert "不生成正式 ELN" in template_text
    assert "复核提示" in template_text

    combined = recipe_text + "\n" + template_text
    for forbidden in ("production-grade", "无需人工复核", "临床诊断结论", "完整 ELN 已生成"):
        assert forbidden not in combined


def test_unimplemented_labtools_surfaces_remain_placeholder_or_not_implemented(qapp) -> None:
    from app.labtools.ui.image_analysis_widgets import LabToolsImageAnalysisWidget
    from app.labtools.ui.template_widgets import LabToolsTemplateWidget

    image_text = _visible_text(LabToolsImageAnalysisWidget())
    template_widget = LabToolsTemplateWidget()
    for row in range(template_widget._template_list.count()):
        if "Western blot" in template_widget._template_list.item(row).text():
            template_widget._template_list.setCurrentRow(row)
            break
    template_text = _visible_text(template_widget)
    combined = image_text + "\n" + template_text

    assert "细胞计数" in combined
    assert "灰度 / 墨值" in combined
    assert "algorithm_not_available" in combined
    assert "不做 WB/凝胶灰度或条带自动分析" in combined
    for forbidden in (
        "automatic cell counting completed",
        "automatic ROI completed",
        "grayscale / ink-value completed",
        "WB / gel grayscale completed",
        "自动细胞计数已完成",
        "灰度 / 墨值已完成",
        "WB/凝胶灰度已完成",
        "批量图像处理已完成",
    ):
        assert forbidden not in combined
