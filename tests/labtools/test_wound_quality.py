from __future__ import annotations

from PIL import Image

from app.labtools.image_analysis.wound_healing import (
    WoundHealingParameters,
    WoundHealingROI,
    analyze_wound_healing_area,
)


def _write_constant_image(path, size: tuple[int, int], value: int) -> None:
    image = Image.new("L", size, color=value)
    image.save(path)


def test_wound_quality_warns_for_small_roi_and_extreme_threshold(tmp_path) -> None:
    image_path = tmp_path / "small-extreme.png"
    _write_constant_image(image_path, (10, 10), 100)

    result = analyze_wound_healing_area(
        WoundHealingParameters(str(image_path), WoundHealingROI("analysis ROI", 0, 0, 5, 5), 2, "bright")
    )

    assert any("分析 ROI 面积小于 100 pixels" in warning for warning in result.warnings)
    assert any("阈值接近 0 或 255" in warning for warning in result.warnings)


def test_wound_quality_warns_for_zero_scratch_area(tmp_path) -> None:
    image_path = tmp_path / "zero.png"
    _write_constant_image(image_path, (10, 10), 10)

    result = analyze_wound_healing_area(
        WoundHealingParameters(str(image_path), WoundHealingROI("analysis ROI", 0, 0, 10, 10), 200, "bright")
    )

    assert result.metrics.scratch_area_pixels == 0
    assert any("scratch area 为 0" in warning for warning in result.warnings)
    assert any("小于 ROI 的 1%" in warning for warning in result.warnings)


def test_wound_quality_warns_when_scratch_area_nearly_all_roi(tmp_path) -> None:
    image_path = tmp_path / "full.png"
    _write_constant_image(image_path, (10, 10), 240)

    result = analyze_wound_healing_area(
        WoundHealingParameters(str(image_path), WoundHealingROI("analysis ROI", 0, 0, 10, 10), 200, "bright")
    )

    assert result.metrics.scratch_area_fraction == 1.0
    assert any("划痕区域接近 ROI 全部" in warning for warning in result.warnings)


def test_wound_quality_warns_when_scratch_area_below_one_percent(tmp_path) -> None:
    image_path = tmp_path / "tiny.png"
    image = Image.new("L", (20, 20), color=10)
    pixels = [10] * 400
    pixels[0] = 255
    image.putdata(pixels)
    image.save(image_path)

    result = analyze_wound_healing_area(
        WoundHealingParameters(str(image_path), WoundHealingROI("analysis ROI", 0, 0, 20, 20), 200, "bright")
    )

    assert result.metrics.scratch_area_fraction == 0.0025
    assert any("小于 ROI 的 1%" in warning for warning in result.warnings)
