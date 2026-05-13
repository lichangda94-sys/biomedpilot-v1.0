from __future__ import annotations

import pytest
from PIL import Image

from app.labtools.image_analysis.fluorescence import (
    FluorescenceAnalysisParameters,
    FluorescenceROI,
    analyze_fluorescence_roi,
    create_fluorescence_audit_records,
    validate_roi_bounds,
)
from app.labtools.image_analysis.image_models import ImageAnalysisError


def _write_test_image(path) -> None:
    image = Image.new("L", (4, 4))
    image.putdata(
        [
            1,
            2,
            3,
            4,
            5,
            10,
            20,
            8,
            9,
            30,
            40,
            12,
            13,
            14,
            15,
            16,
        ]
    )
    image.save(path)


def test_fluorescence_analyzer_calculates_manual_roi_metrics(tmp_path) -> None:
    image_path = tmp_path / "fluorescence.png"
    _write_test_image(image_path)
    parameters = FluorescenceAnalysisParameters(
        image_path=str(image_path),
        signal_roi=FluorescenceROI("signal", 1, 1, 2, 2, "signal"),
        background_roi=FluorescenceROI("background", 0, 0, 2, 1, "background"),
    )

    result = analyze_fluorescence_roi(parameters, task_id="task-1")

    assert result.metrics.roi_area_pixels == 4
    assert result.metrics.integrated_density == pytest.approx(100.0)
    assert result.metrics.mean_intensity == pytest.approx(25.0)
    assert result.metrics.background_mean_intensity == pytest.approx(1.5)
    assert result.metrics.corrected_total_fluorescence == pytest.approx(94.0)
    assert result.metrics.min_intensity == pytest.approx(10.0)
    assert result.metrics.max_intensity == pytest.approx(40.0)
    assert result.warnings == ()


def test_fluorescence_analyzer_warns_when_corrected_total_is_negative(tmp_path) -> None:
    image_path = tmp_path / "negative.png"
    _write_test_image(image_path)
    parameters = FluorescenceAnalysisParameters(
        image_path=str(image_path),
        signal_roi=FluorescenceROI("signal", 0, 0, 2, 1, "signal"),
        background_roi=FluorescenceROI("background", 1, 1, 2, 2, "background"),
    )

    result = analyze_fluorescence_roi(parameters)

    assert result.metrics.corrected_total_fluorescence < 0
    assert "背景可能过高" in result.warnings[0]


def test_fluorescence_analyzer_rejects_out_of_bounds_roi(tmp_path) -> None:
    image_path = tmp_path / "bounds.png"
    _write_test_image(image_path)
    parameters = FluorescenceAnalysisParameters(
        image_path=str(image_path),
        signal_roi=FluorescenceROI("signal", 3, 3, 2, 1, "signal"),
        background_roi=FluorescenceROI("background", 0, 0, 1, 1, "background"),
    )

    with pytest.raises(ImageAnalysisError, match="超出图片边界"):
        analyze_fluorescence_roi(parameters)


def test_fluorescence_analyzer_rejects_missing_image() -> None:
    parameters = FluorescenceAnalysisParameters(
        image_path="/tmp/biomedpilot-missing-fluorescence.png",
        signal_roi=FluorescenceROI("signal", 0, 0, 1, 1, "signal"),
        background_roi=FluorescenceROI("background", 0, 0, 1, 1, "background"),
    )

    with pytest.raises(ImageAnalysisError, match="图片路径不存在"):
        analyze_fluorescence_roi(parameters)


def test_validate_roi_bounds_uses_image_dimensions() -> None:
    roi = FluorescenceROI("signal", 0, 0, 2, 2, "signal")

    validate_roi_bounds(roi, 2, 2)

    with pytest.raises(ImageAnalysisError, match="超出图片边界"):
        validate_roi_bounds(FluorescenceROI("signal", 1, 1, 2, 2, "signal"), 2, 2)


def test_fluorescence_audit_record_includes_algorithm_details(tmp_path) -> None:
    image_path = tmp_path / "audit.png"
    _write_test_image(image_path)
    parameters = FluorescenceAnalysisParameters(
        image_path=str(image_path),
        signal_roi=FluorescenceROI("signal", 1, 1, 2, 2, "signal"),
        background_roi=FluorescenceROI("background", 0, 0, 1, 1, "background"),
    )
    result = analyze_fluorescence_roi(parameters, task_id="task-1")

    audit = create_fluorescence_audit_records(result, source_path=image_path)[0].to_dict()

    assert audit["event_type"] == "fluorescence_analysis_completed"
    assert audit["details"]["algorithm_name"] == "manual_roi_grayscale_fluorescence_v1"
    assert audit["details"]["manual_roi_required"] is True
