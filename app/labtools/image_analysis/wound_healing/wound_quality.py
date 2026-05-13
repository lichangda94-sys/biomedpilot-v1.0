from __future__ import annotations

from app.labtools.image_analysis.wound_healing.wound_models import WoundHealingResult


MIN_WOUND_ROI_AREA_PIXELS = 100


def evaluate_wound_healing_quality(
    result: WoundHealingResult,
    *,
    min_roi_area_pixels: int = MIN_WOUND_ROI_AREA_PIXELS,
) -> tuple[str, ...]:
    warnings: list[str] = []
    metrics = result.metrics

    if metrics.roi_area_pixels < min_roi_area_pixels:
        warnings.append(f"分析 ROI 面积小于 {min_roi_area_pixels} pixels，划痕面积估算可能不稳定。")
    if metrics.threshold < 5 or metrics.threshold > 250:
        warnings.append("阈值接近 0 或 255，可能导致划痕区域估算偏差，请人工调整阈值后复核。")
    if metrics.scratch_area_pixels == 0:
        warnings.append("当前阈值下 scratch area 为 0，请检查阈值、亮/暗模式和 ROI 是否正确。")
    if metrics.scratch_area_fraction > 0.95:
        warnings.append("当前阈值下划痕区域接近 ROI 全部，请复核阈值、模式和原图质量。")
    if metrics.scratch_area_fraction < 0.01:
        warnings.append("当前阈值下划痕区域小于 ROI 的 1%，图像可能需要人工调整阈值。")
    return tuple(warnings)
