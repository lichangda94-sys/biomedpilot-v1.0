from __future__ import annotations

import csv
import json

import pytest

from app.labtools.western_blot import (
    CoordinateMapper,
    WBMeasurement,
    WBRectangleROI,
    WBROIAnalysisError,
    WBROICollection,
    background_corrected_density,
    calculate_wb_normalization,
    create_wb_roi_run_request_workspace,
    export_wb_roi_csv,
    read_wb_measurement_csv,
)


def test_wb_roi_model_serializes_and_round_trips() -> None:
    roi = WBRectangleROI("img_001", "wb.png", "target_band", 120, 240, 35, 18, label="Target Lane 1", lane_index=1, sample_name="Sample A", linked_background_roi_id="bg")

    restored = WBRectangleROI.from_dict(roi.to_dict())

    assert restored.roi_type == "target_band"
    assert restored.csv_row()["linked_background_roi_id"] == "bg"


def test_coordinate_mapper_converts_display_and_image_coordinates() -> None:
    mapper = CoordinateMapper(image_width=1000, image_height=500, display_width=500, display_height=500)

    display = mapper.image_to_display_rect(100, 50, 200, 100)
    image = mapper.display_to_image_rect(*display)

    assert display == pytest.approx((50, 150, 100, 50))
    assert image == pytest.approx((100, 50, 200, 100))


def test_fixed_roi_size_and_copy_to_lanes() -> None:
    collection = WBROICollection()
    roi = collection.add_roi(WBRectangleROI("img", "wb.png", "target_band", 10, 20, 30, 12, lane_index=1))

    size = collection.set_fixed_size_from_roi(roi.roi_id)
    copied = collection.copy_to_next_lane(roi.roi_id)
    collection.add_roi(WBRectangleROI("img", "wb.png", "control_band", 10, 80, 99, 99, lane_index=1))
    collection.unify_size()
    all_lane_copies = collection.copy_to_all_lanes(roi.roi_id, 4, x_step=40)

    assert size.width == 30
    assert copied.lane_index == 2
    assert collection.rois[-1].width == 30
    assert {item.lane_index for item in all_lane_copies} == {2, 3, 4}


def test_roi_csv_export(tmp_path) -> None:
    roi = WBRectangleROI("img", "wb.png", "background", 1, 2, 3, 4, label="BG", lane_index=1)

    path = export_wb_roi_csv((roi,), tmp_path / "wb_rois.csv")

    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    assert rows[0]["roi_id"] == roi.roi_id
    assert rows[0]["roi_type"] == "background"


def test_macro_registry_contains_wb_preprocess_and_fixed_rectangle_roi_measure() -> None:
    from app.labtools.image_analysis import builtin_macro_registry, default_macro_for_analysis

    templates = {template.macro_id: template for template in builtin_macro_registry()}

    assert templates["wb_batch_preprocess"].path.exists()
    assert templates["wb_fixed_rectangle_roi_measure"].path.exists()
    assert default_macro_for_analysis("western_blot", "wb_preprocess").macro_id == "wb_batch_preprocess"
    assert default_macro_for_analysis("western_blot", "wb_fixed_rectangle_roi_measure").macro_id == "wb_fixed_rectangle_roi_measure"


def test_wb_roi_run_request_workspace_writes_roi_files(tmp_path) -> None:
    from app.labtools.image_analysis import ImageAnalysisTaskStore

    image_path = tmp_path / "wb.png"
    image_path.write_bytes(b"image")
    roi = WBRectangleROI("img", str(image_path), "target_band", 1, 2, 3, 4)

    workspace = create_wb_roi_run_request_workspace(image_path=str(image_path), rois=(roi,), parameters={"invert_mode": "自动判断"}, task_store=ImageAnalysisTaskStore(tmp_path / "tasks"))

    assert workspace.task.status == "run_request_created"
    assert (workspace.task_dir / "rois" / "wb_rois.csv").exists()
    assert (workspace.task_dir / "rois" / "wb_rois.json").exists()
    request = json.loads(workspace.run_request_path.read_text(encoding="utf-8"))
    assert request["macro_id"] == "wb_fixed_rectangle_roi_measure"


def test_measurement_csv_background_correction_and_ratios(tmp_path) -> None:
    path = tmp_path / "measurements.csv"
    path.write_text(
        "\n".join(
            (
                "roi_id,image_id,image_path,roi_type,label,lane_index,sample_name,x,y,width,height,area,mean_gray_value,integrated_density,raw_integrated_density,background_roi_id,notes",
                "target,img,wb.png,target_band,T,1,S1,0,0,10,10,100,50,5000,6000,bg,",
                "control,img,wb.png,control_band,C,1,S1,0,20,10,10,100,20,2000,3000,bg,",
                "total,img,wb.png,total_protein_lane,Total,1,S1,0,40,10,20,200,15,3000,5000,bg,",
                "bg,img,wb.png,background,BG,1,S1,0,80,10,10,100,10,1000,1000,,",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    measurements = read_wb_measurement_csv(path)
    results = calculate_wb_normalization(measurements)

    assert background_corrected_density(measurements[0], measurements[3]) == pytest.approx(5000)
    assert results[0].target_control_ratio == pytest.approx(2.5)
    assert results[0].target_total_protein_ratio == pytest.approx(5 / 3)


def test_wb_normalization_returns_error_when_control_missing_or_zero() -> None:
    target = WBMeasurement("target", "img", "wb.png", "target_band", "T", 1, "S1", 0, 0, 1, 1, 100, 10, 1000, 1000)
    zero_control = WBMeasurement("control", "img", "wb.png", "control_band", "C", 1, "S1", 0, 0, 1, 1, 100, 0, 0, 0)

    missing = calculate_wb_normalization((target,))
    zero = calculate_wb_normalization((target, zero_control))

    assert "缺少内参蛋白 ROI" in missing[0].error
    assert "为 0" in zero[0].error


def test_roi_rejects_unsupported_type() -> None:
    with pytest.raises(WBROIAnalysisError):
        WBRectangleROI("img", "wb.png", "ellipse", 0, 0, 1, 1)
