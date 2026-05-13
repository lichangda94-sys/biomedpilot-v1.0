from __future__ import annotations

import pytest

from app.labtools.image_analysis.fluorescence import (
    FLUORESCENCE_FORMULA,
    FLUORESCENCE_REVIEW_NOTICE,
    FluorescenceAnalysisMetrics,
    FluorescenceAnalysisParameters,
    FluorescenceAnalysisResult,
    FluorescenceROI,
)
from app.labtools.image_analysis.image_models import ImageAnalysisError


def test_fluorescence_roi_exports_json_compatible_dict() -> None:
    roi = FluorescenceROI(label="signal", x=1, y=2, width=3, height=4, roi_type="signal", notes="manual")

    payload = roi.to_dict()

    assert payload["roi_type"] == "signal"
    assert payload["width"] == 3
    assert roi.area_pixels == 12


def test_fluorescence_roi_rejects_bad_type_and_zero_size() -> None:
    with pytest.raises(ImageAnalysisError, match="signal 或 background"):
        FluorescenceROI(label="bad", x=0, y=0, width=1, height=1, roi_type="auto")

    with pytest.raises(ImageAnalysisError, match="必须大于 0"):
        FluorescenceROI(label="signal", x=0, y=0, width=0, height=1, roi_type="signal")


def test_fluorescence_result_exports_metrics_and_review_notice() -> None:
    signal = FluorescenceROI(label="signal", x=0, y=0, width=2, height=2, roi_type="signal")
    background = FluorescenceROI(label="background", x=2, y=0, width=1, height=2, roi_type="background")
    parameters = FluorescenceAnalysisParameters("image.png", signal, background)
    metrics = FluorescenceAnalysisMetrics(4, 10.0, 40.0, 2.0, 32.0, 5.0, 15.0)
    result = FluorescenceAnalysisResult(task_id="task-1", parameters=parameters, metrics=metrics)

    payload = result.to_dict()

    assert payload["status"] == "completed"
    assert payload["metrics"]["corrected_total_fluorescence"] == 32.0
    assert payload["formula"] == FLUORESCENCE_FORMULA
    assert payload["review_notice"] == FLUORESCENCE_REVIEW_NOTICE
