from __future__ import annotations

import json


def test_builtin_macro_registry_loads_expected_templates_and_paths() -> None:
    from app.labtools.image_analysis import builtin_macro_registry, default_macro_for_analysis

    templates = {template.macro_id: template for template in builtin_macro_registry()}

    assert set(templates) == {
        "wb_grayscale_basic",
        "wb_lane_band_measurement",
        "scratch_area_basic",
        "transwell_count_basic",
        "fluorescence_intensity_basic",
        "convert_to_8bit",
        "batch_preprocess",
    }
    assert all(template.path.exists() for template in templates.values())
    assert default_macro_for_analysis("western_blot", "wb_grayscale").macro_id == "wb_grayscale_basic"
    assert default_macro_for_analysis("cell_experiment", "scratch_area").macro_id == "scratch_area_basic"
    assert default_macro_for_analysis("cell_experiment", "transwell_count").macro_id == "transwell_count_basic"
    assert default_macro_for_analysis("cell_experiment", "fluorescence_intensity").macro_id == "fluorescence_intensity_basic"


def test_image_analysis_task_store_reference_mode_creates_manifest_macro_and_run_request(tmp_path) -> None:
    from app.labtools.image_analysis import ImageAnalysisTaskStore

    image_path = tmp_path / "wb.png"
    image_path.write_bytes(b"image")
    store = ImageAnalysisTaskStore(tmp_path / "tasks")

    workspace = store.create_workspace(
        task_name="WB test",
        experiment_module="western_blot",
        analysis_type="wb_grayscale",
        image_paths=(str(image_path),),
        import_mode="reference_original_path",
        parameters={"lane 数量": "10"},
    )
    workspace = store.create_run_request(workspace)

    assert workspace.task.status == "run_request_created"
    assert workspace.task_manifest_path.exists()
    assert workspace.image_manifest_path.exists()
    assert workspace.selected_macro_path.exists()
    assert workspace.generated_parameters_path.exists()
    assert workspace.run_request_path.exists()
    manifest = json.loads(workspace.image_manifest_path.read_text(encoding="utf-8"))
    assert manifest["images"][0]["original_path"] == str(image_path)
    assert manifest["images"][0]["task_path"] == ""
    request = json.loads(workspace.run_request_path.read_text(encoding="utf-8"))
    assert request["engine_key"] == "imagej"
    assert request["minimum_engine_requirement"] == "imagej"
    assert request["macro_id"] == "wb_grayscale_basic"
    assert request["input_images"] == [str(image_path)]


def test_builtin_macro_registry_marks_first_wave_macros_as_imagej() -> None:
    from app.labtools.image_analysis import builtin_macro_registry

    templates = {template.macro_id: template for template in builtin_macro_registry()}

    for macro_id in (
        "wb_grayscale_basic",
        "wb_lane_band_measurement",
        "scratch_area_basic",
        "transwell_count_basic",
        "fluorescence_intensity_basic",
    ):
        assert templates[macro_id].minimum_engine_requirement == "imagej"
        assert templates[macro_id].to_dict()["minimum_engine_requirement"] == "imagej"


def test_image_analysis_task_store_copy_mode_copies_input_image(tmp_path) -> None:
    from app.labtools.image_analysis import ImageAnalysisTaskStore

    image_path = tmp_path / "scratch.tif"
    image_path.write_bytes(b"image")
    store = ImageAnalysisTaskStore(tmp_path / "tasks")

    workspace = store.create_workspace(
        task_name="Scratch test",
        experiment_module="cell_experiment",
        analysis_type="scratch_area",
        image_paths=(str(image_path),),
        import_mode="copy_to_task_workspace",
    )

    copied = workspace.image_manifest_entries[0].task_path
    assert copied
    assert copied != str(image_path)
    assert copied.endswith("scratch.tif")
    assert json.loads(workspace.generated_parameters_path.read_text(encoding="utf-8")) == {}
