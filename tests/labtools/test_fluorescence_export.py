from __future__ import annotations

import csv
import json
from io import StringIO

from PIL import Image

from app.labtools.image_analysis.fluorescence import (
    FluorescenceAnalysisParameters,
    FluorescenceROI,
    analyze_fluorescence_roi,
    fluorescence_csv_rows,
    fluorescence_csv_text,
    fluorescence_result_to_json_dict,
)


def _write_image(path) -> None:
    image = Image.new("L", (6, 3))
    image.putdata([20, 20, 20, 2, 2, 2, 20, 20, 20, 2, 2, 2, 20, 20, 20, 2, 2, 2])
    image.save(path)


def _result(tmp_path):
    image_path = tmp_path / "fluorescence-export.png"
    _write_image(image_path)
    return analyze_fluorescence_roi(
        FluorescenceAnalysisParameters(
            image_path=str(image_path),
            signal_roi=FluorescenceROI("signal", 0, 0, 3, 3, "signal"),
            background_roi=FluorescenceROI("background", 3, 0, 3, 3, "background"),
        ),
        task_id="task-export",
    )


def test_fluorescence_json_dict_contains_review_export_fields(tmp_path) -> None:
    result = _result(tmp_path)

    payload = fluorescence_result_to_json_dict(result)
    encoded = json.dumps(payload, ensure_ascii=False)

    assert payload["result_id"] == result.result_id
    assert payload["task_id"] == "task-export"
    assert payload["image_filename"] == "fluorescence-export.png"
    assert payload["source_path_summary"] == "fluorescence-export.png"
    assert payload["image_dimensions"] == {"width": 6, "height": 3, "unit": "pixels"}
    assert payload["signal_roi"]["roi_type"] == "signal"
    assert payload["background_roi"]["roi_type"] == "background"
    assert payload["metrics"]["corrected_total_fluorescence"] == 162.0
    assert payload["formula"].startswith("CTF = Integrated Density")
    assert payload["warnings"] == []
    assert "请人工复核 ROI" in payload["review_notice"]
    assert payload["generated_at"]
    assert "corrected_total_fluorescence" in encoded


def test_fluorescence_csv_rows_and_text_are_stable(tmp_path) -> None:
    result = _result(tmp_path)

    rows = fluorescence_csv_rows(result)
    text = fluorescence_csv_text(result)
    parsed = list(csv.DictReader(StringIO(text)))

    assert set(rows[0]) == {"metric", "value", "unit", "note"}
    assert rows[0] == {"metric": "roi_area_pixels", "value": "9", "unit": "pixels", "note": "signal ROI area"}
    assert rows[4]["metric"] == "corrected_total_fluorescence"
    assert rows[4]["value"] == "162"
    assert text.startswith("metric,value,unit,note\n")
    assert parsed == rows


def test_fluorescence_exports_do_not_write_result_files(tmp_path) -> None:
    result = _result(tmp_path)
    before = {path.name for path in tmp_path.iterdir()}

    fluorescence_result_to_json_dict(result)
    fluorescence_csv_rows(result)
    fluorescence_csv_text(result)

    assert {path.name for path in tmp_path.iterdir()} == before
