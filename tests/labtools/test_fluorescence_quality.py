from __future__ import annotations

from PIL import Image

from app.labtools.image_analysis.fluorescence import (
    FluorescenceAnalysisParameters,
    FluorescenceROI,
    analyze_fluorescence_roi,
)


def _write_constant_image(path, size: tuple[int, int], value: int) -> None:
    image = Image.new("L", size, color=value)
    image.save(path)


def _write_half_image(path, *, signal_value: int, background_value: int) -> None:
    image = Image.new("L", (6, 3))
    image.putdata([signal_value] * 9 + [background_value] * 9)
    image.save(path)


def test_fluorescence_quality_warns_for_negative_ctf_and_high_background(tmp_path) -> None:
    image_path = tmp_path / "negative-high-background.png"
    _write_half_image(image_path, signal_value=10, background_value=20)

    result = analyze_fluorescence_roi(
        FluorescenceAnalysisParameters(
            image_path=str(image_path),
            signal_roi=FluorescenceROI("signal", 0, 0, 3, 3, "signal"),
            background_roi=FluorescenceROI("background", 3, 0, 3, 3, "background"),
        )
    )

    assert result.metrics.corrected_total_fluorescence < 0
    assert any("CTF 为负值" in warning for warning in result.warnings)
    assert any("背景 ROI 平均强度不低于 signal ROI" in warning for warning in result.warnings)


def test_fluorescence_quality_warns_for_too_small_signal_roi(tmp_path) -> None:
    image_path = tmp_path / "small-roi.png"
    _write_constant_image(image_path, (6, 6), 30)

    result = analyze_fluorescence_roi(
        FluorescenceAnalysisParameters(
            image_path=str(image_path),
            signal_roi=FluorescenceROI("signal", 0, 0, 2, 2, "signal"),
            background_roi=FluorescenceROI("background", 3, 3, 3, 3, "background"),
        )
    )

    assert any("signal ROI 面积小于 9 pixels" in warning for warning in result.warnings)


def test_fluorescence_quality_warns_for_too_small_background_roi(tmp_path) -> None:
    image_path = tmp_path / "small-background.png"
    _write_constant_image(image_path, (6, 6), 30)

    result = analyze_fluorescence_roi(
        FluorescenceAnalysisParameters(
            image_path=str(image_path),
            signal_roi=FluorescenceROI("signal", 0, 0, 3, 3, "signal"),
            background_roi=FluorescenceROI("background", 4, 4, 2, 2, "background"),
        )
    )

    assert any("background ROI 面积小于 9 pixels" in warning for warning in result.warnings)


def test_fluorescence_quality_warns_for_large_roi_area_difference(tmp_path) -> None:
    image_path = tmp_path / "area-difference.png"
    _write_constant_image(image_path, (12, 12), 40)

    result = analyze_fluorescence_roi(
        FluorescenceAnalysisParameters(
            image_path=str(image_path),
            signal_roi=FluorescenceROI("signal", 0, 0, 3, 3, "signal"),
            background_roi=FluorescenceROI("background", 3, 3, 9, 9, "background"),
        )
    )

    assert any("面积差异较大" in warning for warning in result.warnings)
