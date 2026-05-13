from __future__ import annotations

from app.labtools.image_analysis.fluorescence.fluorescence_models import FluorescenceAnalysisResult


MIN_REVIEWABLE_ROI_AREA_PIXELS = 9
ROI_AREA_RATIO_WARNING_THRESHOLD = 4.0


def evaluate_fluorescence_quality(
    result: FluorescenceAnalysisResult,
    *,
    min_roi_area_pixels: int = MIN_REVIEWABLE_ROI_AREA_PIXELS,
    area_ratio_threshold: float = ROI_AREA_RATIO_WARNING_THRESHOLD,
) -> tuple[str, ...]:
    """Return user-facing review warnings without blocking the calculation."""
    warnings: list[str] = []
    metrics = result.metrics
    signal_roi = result.parameters.signal_roi
    background_roi = result.parameters.background_roi

    if metrics.corrected_total_fluorescence < 0:
        warnings.append("校正总荧光 CTF 为负值，背景可能过高或 ROI 设置需要复核。")
    if metrics.background_mean_intensity >= metrics.mean_intensity:
        warnings.append("背景 ROI 平均强度不低于 signal ROI 平均强度，请复核背景区域、曝光条件和 ROI 位置。")
    if signal_roi.area_pixels < min_roi_area_pixels:
        warnings.append(f"signal ROI 面积小于 {min_roi_area_pixels} pixels，结果可能对单个像素变化过于敏感。")
    if background_roi.area_pixels < min_roi_area_pixels:
        warnings.append(f"background ROI 面积小于 {min_roi_area_pixels} pixels，背景估计可能不稳定。")

    smaller_area = min(signal_roi.area_pixels, background_roi.area_pixels)
    larger_area = max(signal_roi.area_pixels, background_roi.area_pixels)
    if smaller_area > 0 and larger_area / smaller_area >= area_ratio_threshold:
        warnings.append(
            "signal ROI 与 background ROI 面积差异较大，请确认背景扣除是否仍可代表当前图片。"
        )
    return tuple(warnings)
