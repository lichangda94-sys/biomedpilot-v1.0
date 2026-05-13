from __future__ import annotations

import pytest
from PIL import Image

from app.labtools.image_analysis.image_models import ImageAnalysisError
from app.labtools.image_analysis.wound_healing import (
    WoundHealingParameters,
    WoundHealingROI,
    analyze_wound_healing_area,
    create_wound_healing_audit_records,
    validate_wound_roi_bounds,
)


def _write_grid(path) -> None:
    image = Image.new("L", (4, 4))
    image.putdata(
        [
            0,
            10,
            200,
            220,
            5,
            20,
            180,
            240,
            30,
            40,
            100,
            110,
            130,
            140,
            150,
            160,
        ]
    )
    image.save(path)


def test_wound_analyzer_calculates_bright_threshold_area(tmp_path) -> None:
    image_path = tmp_path / "bright.png"
    _write_grid(image_path)
    parameters = WoundHealingParameters(
        image_path=str(image_path),
        roi=WoundHealingROI("analysis ROI", 0, 0, 4, 4),
        threshold=128,
        scratch_mode="bright",
    )

    result = analyze_wound_healing_area(parameters, task_id="task-bright")

    assert result.metrics.roi_area_pixels == 16
    assert result.metrics.scratch_area_pixels == 8
    assert result.metrics.scratch_area_fraction == pytest.approx(0.5)
    assert result.metrics.non_scratch_area_pixels == 8
    assert result.metrics.non_scratch_area_fraction == pytest.approx(0.5)
    assert result.image_dimensions_dict()["width"] == 4


def test_wound_analyzer_calculates_dark_threshold_area(tmp_path) -> None:
    image_path = tmp_path / "dark.png"
    _write_grid(image_path)
    parameters = WoundHealingParameters(
        image_path=str(image_path),
        roi=WoundHealingROI("analysis ROI", 0, 0, 4, 4),
        threshold=40,
        scratch_mode="dark",
    )

    result = analyze_wound_healing_area(parameters)

    assert result.metrics.scratch_area_pixels == 6
    assert result.metrics.scratch_area_fraction == pytest.approx(0.375)
    assert result.metrics.non_scratch_area_fraction == pytest.approx(0.625)


def test_wound_analyzer_rejects_out_of_bounds_roi(tmp_path) -> None:
    image_path = tmp_path / "bounds.png"
    _write_grid(image_path)
    parameters = WoundHealingParameters(
        image_path=str(image_path),
        roi=WoundHealingROI("analysis ROI", 3, 3, 2, 1),
        threshold=128,
        scratch_mode="bright",
    )

    with pytest.raises(ImageAnalysisError, match="超出图片边界"):
        analyze_wound_healing_area(parameters)


def test_wound_analyzer_rejects_missing_image() -> None:
    parameters = WoundHealingParameters(
        image_path="/tmp/biomedpilot-missing-wound.png",
        roi=WoundHealingROI("analysis ROI", 0, 0, 10, 10),
        threshold=128,
        scratch_mode="bright",
    )

    with pytest.raises(ImageAnalysisError, match="图片路径不存在"):
        analyze_wound_healing_area(parameters)


def test_validate_wound_roi_bounds_uses_image_dimensions() -> None:
    validate_wound_roi_bounds(WoundHealingROI("analysis ROI", 0, 0, 2, 2), 2, 2)

    with pytest.raises(ImageAnalysisError, match="超出图片边界"):
        validate_wound_roi_bounds(WoundHealingROI("analysis ROI", 1, 1, 2, 2), 2, 2)


def test_wound_audit_record_includes_algorithm_details(tmp_path) -> None:
    image_path = tmp_path / "audit.png"
    _write_grid(image_path)
    result = analyze_wound_healing_area(
        WoundHealingParameters(str(image_path), WoundHealingROI("analysis ROI", 0, 0, 4, 4), 128, "bright"),
        task_id="task-audit",
    )

    audit = create_wound_healing_audit_records(result, source_path=image_path)[0].to_dict()

    assert audit["event_type"] == "wound_healing_analysis_completed"
    assert audit["details"]["algorithm_name"] == "manual_roi_threshold_wound_healing_v1"
    assert audit["details"]["threshold"] == 128
    assert audit["details"]["manual_roi_required"] is True
