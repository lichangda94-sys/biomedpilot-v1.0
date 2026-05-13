from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from PIL import Image

from app.labtools.image_analysis.export_package import (
    LABTOOLS_ROI_EXPORT_SCHEMA_VERSION,
    build_export_basename,
    export_fluorescence_analysis_package,
    export_wound_healing_analysis_package,
    sanitize_filename_component,
)
from app.labtools.image_analysis.fluorescence import (
    FluorescenceAnalysisParameters,
    FluorescenceROI,
    analyze_fluorescence_roi,
)
from app.labtools.image_analysis.image_models import ImageAnalysisError
from app.labtools.image_analysis.wound_healing import (
    WoundHealingParameters,
    WoundHealingROI,
    analyze_wound_healing_area,
)


def _fluorescence_result(tmp_path):
    image_path = tmp_path / "fluorescence-source.png"
    image = Image.new("L", (6, 3))
    image.putdata([20, 20, 20, 2, 2, 2, 20, 20, 20, 2, 2, 2, 20, 20, 20, 2, 2, 2])
    image.save(image_path)
    return analyze_fluorescence_roi(
        FluorescenceAnalysisParameters(
            image_path=str(image_path),
            signal_roi=FluorescenceROI("signal", 0, 0, 3, 3, "signal"),
            background_roi=FluorescenceROI("background", 3, 0, 3, 3, "background"),
        ),
        task_id="task-export",
    )


def _wound_result(tmp_path):
    image_path = tmp_path / "wound-source.png"
    image = Image.new("L", (10, 10))
    image.putdata([250] * 25 + [20] * 75)
    image.save(image_path)
    return analyze_wound_healing_area(
        WoundHealingParameters(str(image_path), WoundHealingROI("analysis ROI", 0, 0, 10, 10), 200, "bright"),
        task_id="task-export",
    )


def test_export_basename_and_filename_component_are_sanitized() -> None:
    created_at = datetime(2026, 5, 13, 4, 5, 6, tzinfo=timezone.utc)

    sanitized = sanitize_filename_component("bad name/with:unsafe，chars")
    basename = build_export_basename("fluorescence manual/roi", created_at, "token:with/slash")

    assert sanitized == "bad_name_with_unsafe_chars"
    assert basename == "fluorescence_manual_roi_20260513T040506Z_token_with_s"
    assert "/" not in basename
    assert ":" not in basename
    assert " " not in basename
    assert len(basename) < 150


def test_fluorescence_export_package_does_not_overwrite_existing_files(tmp_path, monkeypatch) -> None:
    import app.labtools.image_analysis.export_package as export_package

    fixed_now = datetime(2026, 5, 13, 4, 5, 6, tzinfo=timezone.utc)
    monkeypatch.setattr(export_package, "_utc_now", lambda: fixed_now)
    result = _fluorescence_result(tmp_path)
    export_dir = tmp_path / "exports"

    first = export_fluorescence_analysis_package(result, export_dir)
    first_manifest_text = Path(first.manifest_path).read_text(encoding="utf-8")
    second = export_fluorescence_analysis_package(result, export_dir)

    assert first.manifest_path != second.manifest_path
    assert first.csv_path != second.csv_path
    assert first.markdown_path != second.markdown_path
    assert first.overlay_path != second.overlay_path
    assert Path(first.manifest_path).read_text(encoding="utf-8") == first_manifest_text
    assert Path(second.manifest_path).exists()
    assert Path(second.manifest_path).name.endswith("_001_manifest.json")


def test_wound_export_manifest_output_files_match_actual_files(tmp_path) -> None:
    result = _wound_result(tmp_path)
    package = export_wound_healing_analysis_package(result, tmp_path / "exports")
    manifest = json.loads(Path(package.manifest_path).read_text(encoding="utf-8"))

    assert manifest["schema_version"] == LABTOOLS_ROI_EXPORT_SCHEMA_VERSION
    assert manifest["tool_slug"] == "wound_manual_roi_threshold"
    assert manifest["parameters"]["manual_roi"] is True
    assert manifest["parameters"]["threshold_value"] == 200
    assert manifest["result_summary"]["scratch_area_pixels"] == 25
    assert manifest["output_files"]["manifest_json"]["filename"] == Path(package.manifest_path).name
    assert manifest["output_files"]["summary_csv"]["filename"] == Path(package.csv_path).name
    assert manifest["output_files"]["markdown_fragment"]["filename"] == Path(package.markdown_path).name
    assert manifest["output_files"]["roi_overlay_png"]["filename"] == Path(package.overlay_path).name
    for path in (package.manifest_path, package.csv_path, package.markdown_path, package.overlay_path):
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0


@pytest.mark.parametrize("bad_output_dir", [None, ""])
def test_export_package_rejects_missing_output_dir(tmp_path, bad_output_dir) -> None:
    result = _fluorescence_result(tmp_path)

    with pytest.raises(ImageAnalysisError, match="请选择 ROI 结果导出目录"):
        export_fluorescence_analysis_package(result, bad_output_dir)


def test_export_package_rejects_output_dir_that_is_file(tmp_path) -> None:
    result = _fluorescence_result(tmp_path)
    output_file = tmp_path / "not-a-directory.txt"
    output_file.write_text("existing user file", encoding="utf-8")

    with pytest.raises(ImageAnalysisError, match="导出位置必须是文件夹"):
        export_fluorescence_analysis_package(result, output_file)

    assert output_file.read_text(encoding="utf-8") == "existing user file"


def test_markdown_fragment_has_review_semantics_and_no_raw_path(tmp_path) -> None:
    result = _wound_result(tmp_path)
    package = export_wound_healing_analysis_package(result, tmp_path / "exports")
    markdown_text = Path(package.markdown_path).read_text(encoding="utf-8")

    assert "LabTools 手动 ROI 辅助分析导出片段" in markdown_text
    assert "人工复核" in markdown_text
    assert "Developer Preview / testing" in markdown_text
    assert str(tmp_path) not in markdown_text
    forbidden = ["正式结论", "自动识别证明", "临床诊断", "无需人工复核", "production-grade"]
    assert not any(term in markdown_text for term in forbidden)


def test_export_package_source_result_is_not_mutated(tmp_path) -> None:
    result = _fluorescence_result(tmp_path)
    before = result.to_dict()

    export_fluorescence_analysis_package(result, tmp_path / "exports")

    assert result.to_dict() == before


def test_export_package_module_does_not_import_disallowed_image_libraries() -> None:
    source = Path("app/labtools/image_analysis/export_package.py").read_text(encoding="utf-8")

    assert "cv2" not in source
    assert "skimage" not in source
    assert "imagej" not in source.lower()
