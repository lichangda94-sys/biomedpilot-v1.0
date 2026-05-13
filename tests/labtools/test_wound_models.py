from __future__ import annotations

import pytest

from app.labtools.image_analysis.image_models import ImageAnalysisError
from app.labtools.image_analysis.wound_healing import (
    WOUND_FORMULA,
    WOUND_REVIEW_NOTICE,
    WoundHealingMetrics,
    WoundHealingParameters,
    WoundHealingROI,
    WoundHealingResult,
)


def test_wound_roi_exports_json_compatible_dict() -> None:
    roi = WoundHealingROI(label="scratch ROI", x=1, y=2, width=3, height=4, notes="manual")

    payload = roi.to_dict()

    assert payload["label"] == "scratch ROI"
    assert payload["x"] == 1
    assert payload["width"] == 3
    assert roi.area_pixels == 12


def test_wound_roi_rejects_zero_size_and_negative_coordinates() -> None:
    with pytest.raises(ImageAnalysisError, match="不能为负数"):
        WoundHealingROI(label="bad", x=-1, y=0, width=1, height=1)

    with pytest.raises(ImageAnalysisError, match="必须大于 0"):
        WoundHealingROI(label="bad", x=0, y=0, width=0, height=1)


def test_wound_parameters_validate_threshold_and_mode() -> None:
    roi = WoundHealingROI(label="roi", x=0, y=0, width=10, height=10)

    params = WoundHealingParameters("image.png", roi, 128, "bright")

    assert params.to_dict()["threshold"] == 128
    with pytest.raises(ImageAnalysisError, match="0-255"):
        WoundHealingParameters("image.png", roi, -1, "bright")
    with pytest.raises(ImageAnalysisError, match="bright 或 dark"):
        WoundHealingParameters("image.png", roi, 128, "auto")


def test_wound_result_exports_metrics_and_review_notice() -> None:
    roi = WoundHealingROI(label="roi", x=0, y=0, width=10, height=10)
    parameters = WoundHealingParameters("image.png", roi, 128, "bright")
    metrics = WoundHealingMetrics(100, 25, 0.25, 75, 0.75, 128, "bright")
    result = WoundHealingResult(task_id="task-1", parameters=parameters, metrics=metrics, image_width=10, image_height=10)

    payload = result.to_dict()

    assert payload["image_dimensions"] == {"width": 10, "height": 10, "unit": "pixels"}
    assert payload["metrics"]["scratch_area_fraction"] == 0.25
    assert payload["formula"] == WOUND_FORMULA
    assert payload["review_notice"] == WOUND_REVIEW_NOTICE
