from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path

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

    manifest = json.loads(Path(package.manifest_path).read_text(encoding="utf-8"))
    csv_text = Path(package.csv_path).read_text(encoding="utf-8")
    markdown_text = Path(package.markdown_path).read_text(encoding="utf-8")
    assert package.analysis_type == "wound_healing"
    assert package.success is True
    assert set(package.files) == {"manifest_json", "summary_csv", "markdown_fragment", "roi_overlay_png"}
    assert manifest["schema_version"] == "labtools_roi_export_manifest.v1"
    assert manifest["export_type"] == "labtools_image_roi_export_package"
    assert manifest["tool_slug"] == "wound_manual_roi_threshold"
    assert manifest["analysis_mode"] == "manual_roi_threshold_area_estimation"
    assert manifest["review_status"] == "manual_review_required"
    assert manifest["manual_review_required"] is True
    assert manifest["semi_quantitative"] is True
    assert manifest["algorithm"]["name"] == "manual_roi_threshold_wound_healing_v1"
    assert "semi-quantitative area estimation" in manifest["interpretation_note"]
    assert "人工复核" in manifest["safety_note"]
    assert manifest["generated_files_count"] == 4
    assert set(manifest["output_files"]) == {"manifest_json", "summary_csv", "markdown_fragment", "roi_overlay_png"}
    assert manifest["result"]["threshold"] == 200
    assert manifest["result"]["scratch_mode"] == "bright"
    assert "基于用户 ROI 和阈值" in manifest["result"]["review_notice"]
    assert "不自动保存、不上传、不联网" in manifest["persistence_note"]
    assert csv_text.startswith(
        "export_schema_version,tool_slug,review_status,measurement_id,roi_id,measurement_name,value,unit,note,"
    )
    assert "threshold_value" in csv_text
    assert "manual_review_required" in csv_text
    assert "## LabTools 手动 ROI 辅助分析导出片段" in markdown_text
    assert str(tmp_path) not in markdown_text
    assert "人工复核" in markdown_text
    assert "临床诊断" not in markdown_text
    assert "无需人工复核" not in markdown_text
    assert manifest["output_files"]["roi_overlay_png"]["filename"] == Path(package.overlay_path).name
    with Image.open(package.overlay_path) as overlay:
        assert overlay.size == (10, 10)
        assert overlay.convert("RGB").getpixel((0, 0)) == (251, 140, 0)
