from __future__ import annotations

from app.labtools.calculators.unit_conversion import format_number
from app.labtools.image_analysis.fluorescence.fluorescence_models import FluorescenceAnalysisResult


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
        "参数",
        f"signal ROI：x={result.parameters.signal_roi.x}, y={result.parameters.signal_roi.y}, "
        f"w={result.parameters.signal_roi.width}, h={result.parameters.signal_roi.height}",
        f"background ROI：x={result.parameters.background_roi.x}, y={result.parameters.background_roi.y}, "
        f"w={result.parameters.background_roi.width}, h={result.parameters.background_roi.height}",
        "channel：grayscale",
    ]
    if result.warnings:
        lines.extend(["", "Warning", *result.warnings])
    lines.extend(["", "复核提示", result.review_notice])
    return "\n".join(lines)
