from __future__ import annotations

from app.labtools.calculators.unit_conversion import format_number
from app.labtools.image_analysis.wound_healing.wound_export import wound_csv_rows
from app.labtools.image_analysis.wound_healing.wound_models import WoundHealingResult


def wound_parameter_summary(result: WoundHealingResult) -> str:
    dimensions = result.image_dimensions_dict()
    roi = result.parameters.roi
    return "\n".join(
        [
            "参数摘要",
            f"图片：{result.to_dict()['image_filename']}",
            f"图片尺寸：{dimensions['width']} x {dimensions['height']} px",
            f"ROI：x={roi.x}, y={roi.y}, w={roi.width}, h={roi.height}, area={roi.area_pixels} px",
            f"阈值：{result.parameters.threshold}",
            f"划痕模式：{result.parameters.scratch_mode}",
            f"通道模式：{result.parameters.channel_mode}",
        ]
    )


def wound_metrics_table_rows(result: WoundHealingResult) -> list[dict[str, str]]:
    return wound_csv_rows(result)


def wound_metrics_table_text(result: WoundHealingResult) -> str:
    rows = wound_metrics_table_rows(result)
    lines = ["指标表", "metric | value | unit | note"]
    lines.extend(f"{row['metric']} | {row['value']} | {row['unit']} | {row['note']}" for row in rows)
    return "\n".join(lines)


def wound_result_summary(result: WoundHealingResult) -> str:
    metrics = result.metrics
    lines = [
        "划痕实验面积分析结果",
        f"状态：{result.status}",
        f"ROI 面积：{metrics.roi_area_pixels} px",
        f"Scratch area：{metrics.scratch_area_pixels} px",
        f"Scratch area fraction：{format_number(metrics.scratch_area_fraction)}",
        f"Covered / migrated fraction（基于阈值的估算）：{format_number(metrics.non_scratch_area_fraction)}",
        "",
        "公式",
        result.formula,
        "",
        wound_parameter_summary(result),
    ]
    if result.warnings:
        lines.extend(["", "Warning", *result.warnings])
    lines.extend(["", "复核提示", result.review_notice])
    return "\n".join(lines)


def wound_markdown_report_fragment(result: WoundHealingResult) -> str:
    roi = result.parameters.roi
    dimensions = result.image_dimensions_dict()
    warnings = list(result.warnings) or ["无"]
    rows = wound_metrics_table_rows(result)
    lines = [
        "## 划痕实验面积分析片段",
        "",
        "### 图片摘要",
        f"- 图片文件：{result.to_dict()['image_filename']}",
        f"- 图片尺寸：{dimensions['width']} x {dimensions['height']} px",
        f"- 分析状态：{result.status}",
        "",
        "### ROI 参数",
        f"- ROI：x={roi.x}, y={roi.y}, width={roi.width}, height={roi.height}, area={roi.area_pixels} pixels",
        "",
        "### 阈值和模式",
        f"- 阈值：{result.parameters.threshold}",
        f"- 划痕模式：{result.parameters.scratch_mode}",
        "- bright 模式：pixel >= threshold 视为 scratch candidate",
        "- dark 模式：pixel <= threshold 视为 scratch candidate",
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
