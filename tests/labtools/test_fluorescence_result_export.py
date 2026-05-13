from __future__ import annotations

import json

from PIL import Image

from app.labtools.image_analysis.fluorescence import (
    FluorescenceAnalysisParameters,
    FluorescenceROI,
    analyze_fluorescence_roi,
    fluorescence_result_summary,
)


def test_fluorescence_result_is_json_compatible_and_not_fake(tmp_path) -> None:
    image_path = tmp_path / "export.png"
    image = Image.new("L", (2, 2))
    image.putdata([10, 20, 30, 40])
    image.save(image_path)
    result = analyze_fluorescence_roi(
        FluorescenceAnalysisParameters(
            image_path=str(image_path),
            signal_roi=FluorescenceROI("signal", 0, 0, 1, 2, "signal"),
            background_roi=FluorescenceROI("background", 1, 0, 1, 2, "background"),
        ),
        task_id="task-export",
    )

    payload = result.to_dict()
    encoded = json.dumps(payload, ensure_ascii=False)
    summary = fluorescence_result_summary(result)

    assert "corrected_total_fluorescence" in encoded
    assert payload["metrics"]["integrated_density"] == 40.0
    assert payload["metrics"]["background_mean_intensity"] == 30.0
    assert payload["metrics"]["corrected_total_fluorescence"] == -20.0
    assert "背景可能过高" in payload["warnings"][0]
    assert "Corrected total fluorescence" in summary
    assert "请人工复核 ROI" in summary
