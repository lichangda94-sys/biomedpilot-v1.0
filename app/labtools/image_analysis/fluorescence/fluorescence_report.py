from __future__ import annotations

from app.labtools.calculators.unit_conversion import format_number
from app.labtools.image_analysis.fluorescence.fluorescence_export import fluorescence_csv_rows
from app.labtools.image_analysis.fluorescence.fluorescence_models import FluorescenceAnalysisResult


def fluorescence_parameter_summary(result: FluorescenceAnalysisResult) -> str:
    dimensions = result.image_dimensions_dict()
    signal = result.parameters.signal_roi
    background = result.parameters.background_roi
    return "\n".join(
        [
            "参数摘要",
            f"图片：{result.to_dict()['image_filename']}",
            f"图片尺寸：{dimensions['width']} x {dimensions['height']} px",
            f"通道模式：{result.parameters.channel_mode}",
            f"背景校正：{'启用' if result.parameters.background_correction_enabled else '未启用'}",
            f"signal ROI：x={signal.x}, y={signal.y}, w={signal.width}, h={signal.height}, area={signal.area_pixels} px",
            f"background ROI：x={background.x}, y={background.y}, w={background.width}, h={background.height}, "
            f"area={background.area_pixels} px",
        ]
    )


def fluorescence_metrics_table_rows(result: FluorescenceAnalysisResult) -> list[dict[str, str]]:
    return fluorescence_csv_rows(result)


def fluorescence_metrics_table_text(result: FluorescenceAnalysisResult) -> str:
    rows = fluorescence_metrics_table_rows(result)
    lines = ["指标表", "metric | value | unit | note"]
    lines.extend(f"{row['metric']} | {row['value']} | {row['unit']} | {row['note']}" for row in rows)
    return "\n".join(lines)


def fluorescence_result_summary(result: FluorescenceAnalysisResult) -> str:
    metrics = result.metrics
    lines = [
        "荧光强度 ROI 分析结果",
        f"状态：{result.status}",
        f"ROI 面积：{metrics.roi_area_pixels} px",
        f"Mean intensity：{format_number(metrics.mean_intensity)}",
        f"Integrated density：{format_number(metrics.integrated_density)}",
        f"Background mean：{format_number(metrics.background_mean_intensity)}",
        f"Corrected total fluorescence：{format_number(metrics.corrected_total_fluorescence)}",
        f"Signal min / max：{format_number(metrics.min_intensity)} / {format_number(metrics.max_intensity)}",
        "",
        "公式",
        result.formula,
        "",
        fluorescence_parameter_summary(result),
    ]
    if result.warnings:
        lines.extend(["", "Warning", *result.warnings])
    lines.extend(["", "复核提示", result.review_notice])
    return "\n".join(lines)


def fluorescence_markdown_report_fragment(result: FluorescenceAnalysisResult) -> str:
    signal = result.parameters.signal_roi
    background = result.parameters.background_roi
    dimensions = result.image_dimensions_dict()
    warnings = list(result.warnings) or ["无"]
    rows = fluorescence_metrics_table_rows(result)
    lines = [
        "## 荧光强度 ROI 分析片段",
        "",
        "### 图片摘要",
        f"- 图片文件：{result.to_dict()['image_filename']}",
        f"- 图片尺寸：{dimensions['width']} x {dimensions['height']} px",
        f"- 分析状态：{result.status}",
        "",
        "### ROI 参数",
        f"- signal ROI：x={signal.x}, y={signal.y}, width={signal.width}, height={signal.height}, "
        f"area={signal.area_pixels} pixels",
        f"- background ROI：x={background.x}, y={background.y}, width={background.width}, "
        f"height={background.height}, area={background.area_pixels} pixels",
        f"- 通道模式：{result.parameters.channel_mode}",
        "",
        "### 计算公式",
        f"`{result.formula}`",
        "",
        "### 主要指标",
        "| metric | value | unit | note |",
        "| --- | ---: | --- | --- |",
    ]
    lines.extend(f"| {row['metric']} | {row['value']} | {row['unit']} | {row['note']} |" for row in rows)
    lines.extend(
        [
            "",
            "### Warnings",
            *[f"- {warning}" for warning in warnings],
            "",
            "### 人工复核提示",
            result.review_notice,
        ]
    )
    return "\n".join(lines)
