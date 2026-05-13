from __future__ import annotations

import csv
import json
from io import StringIO

from PIL import Image

from app.labtools.image_analysis import export_wound_healing_analysis_package
from app.labtools.image_analysis.wound_healing import (
    WoundHealingParameters,
    WoundHealingROI,
    analyze_wound_healing_area,
    wound_csv_rows,
    wound_csv_text,
    wound_result_to_json_dict,
)


def _write_image(path) -> None:
    image = Image.new("L", (10, 10))
    image.putdata([250] * 25 + [20] * 75)
    image.save(path)


def _result(tmp_path):
    image_path = tmp_path / "wound-export.png"
    _write_image(image_path)
    return analyze_wound_healing_area(
        WoundHealingParameters(str(image_path), WoundHealingROI("analysis ROI", 0, 0, 10, 10), 200, "bright"),
        task_id="task-export",
    )


def test_wound_json_dict_contains_review_export_fields(tmp_path) -> None:
    result = _result(tmp_path)

    payload = wound_result_to_json_dict(result)
    encoded = json.dumps(payload, ensure_ascii=False)

    assert payload["result_id"] == result.result_id
    assert payload["task_id"] == "task-export"
    assert payload["image_filename"] == "wound-export.png"
    assert payload["source_path_summary"] == "wound-export.png"
    assert payload["image_dimensions"] == {"width": 10, "height": 10, "unit": "pixels"}
    assert payload["roi"]["width"] == 10
    assert payload["threshold"] == 200
    assert payload["scratch_mode"] == "bright"
    assert payload["metrics"]["scratch_area_pixels"] == 25
    assert payload["metrics"]["scratch_area_fraction"] == 0.25
    assert "基于用户 ROI 和阈值" in payload["review_notice"]
    assert "scratch_area_fraction" in encoded


def test_wound_csv_rows_and_text_are_stable(tmp_path) -> None:
    result = _result(tmp_path)

    rows = wound_csv_rows(result)
    text = wound_csv_text(result)
    parsed = list(csv.DictReader(StringIO(text)))

    assert set(rows[0]) == {"metric", "value", "unit", "note"}
    assert rows[0] == {"metric": "roi_area_pixels", "value": "100", "unit": "pixels", "note": "manual ROI area"}
    assert rows[2]["metric"] == "scratch_area_fraction"
    assert rows[2]["value"] == "0.25"
    assert text.startswith("metric,value,unit,note\n")
    assert parsed == rows


def test_wound_exports_do_not_write_result_files(tmp_path) -> None:
    result = _result(tmp_path)
    before = {path.name for path in tmp_path.iterdir()}

    wound_result_to_json_dict(result)
    wound_csv_rows(result)
    wound_csv_text(result)

    assert {path.name for path in tmp_path.iterdir()} == before


def test_wound_export_package_writes_manifest_csv_markdown_and_overlay(tmp_path) -> None:
    result = _result(tmp_path)
    export_dir = tmp_path / "confirmed-export"

    package = export_wound_healing_analysis_package(result, export_dir)

    manifest = json.loads((export_dir / f"{result.result_id}_manifest.json").read_text(encoding="utf-8"))
    assert package.analysis_type == "wound_healing"
    assert set(package.files) == {
        package.manifest_path,
        package.csv_path,
        package.markdown_path,
        package.overlay_path,
    }
    assert manifest["schema_version"] == "labtools_image_analysis_export_package_v1"
    assert manifest["manual_review_required"] is True
    assert manifest["semi_quantitative"] is True
    assert manifest["algorithm"]["name"] == "manual_roi_threshold_wound_healing_v1"
    assert "semi-quantitative area estimation" in manifest["result_semantics"]
    assert manifest["result"]["threshold"] == 200
    assert manifest["result"]["scratch_mode"] == "bright"
    assert "基于用户 ROI 和阈值" in manifest["result"]["review_notice"]
    assert "不自动保存、不上传、不联网" in manifest["persistence_note"]
    assert (export_dir / f"{result.result_id}_summary.csv").read_text(encoding="utf-8").startswith(
        "metric,value,unit,note\n"
    )
    assert "## 划痕实验面积分析片段" in (
        export_dir / f"{result.result_id}_report.md"
    ).read_text(encoding="utf-8")
    with Image.open(export_dir / f"{result.result_id}_roi_overlay.png") as overlay:
        assert overlay.size == (10, 10)
        assert overlay.convert("RGB").getpixel((0, 0)) == (251, 140, 0)
