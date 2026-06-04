from __future__ import annotations

import json


def test_builtin_macro_registry_loads_expected_templates_and_paths() -> None:
    from app.labtools.image_analysis import builtin_macro_registry, default_macro_for_analysis

    templates = {template.macro_id: template for template in builtin_macro_registry()}

    assert set(templates) == {
        "wb_grayscale_basic",
        "wb_lane_band_measurement",
        "wb_batch_preprocess",
        "wb_fixed_rectangle_roi_measure",
        "scratch_area_basic",
        "transwell_count_basic",
        "fluorescence_intensity_basic",
        "ihc_dab_area_basic",
        "convert_to_8bit",
        "batch_preprocess",
    }
    assert all(template.path.exists() for template in templates.values())
    assert default_macro_for_analysis("western_blot", "wb_grayscale").macro_id == "wb_grayscale_basic"
    assert default_macro_for_analysis("western_blot", "wb_fixed_rectangle_roi_measure").macro_id == "wb_fixed_rectangle_roi_measure"
    assert default_macro_for_analysis("cell_experiment", "scratch_area").macro_id == "scratch_area_basic"
    assert default_macro_for_analysis("cell_experiment", "transwell_count").macro_id == "transwell_count_basic"
    assert default_macro_for_analysis("cell_experiment", "fluorescence_intensity").macro_id == "fluorescence_intensity_basic"
    assert default_macro_for_analysis("cell_experiment", "immunohistochemistry").macro_id == "ihc_dab_area_basic"


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


def test_cell_imagej_workflows_from_latest_labtools_commit_are_registered(tmp_path) -> None:
    from app.labtools.image_analysis import (
        get_cell_imagej_experiment,
        list_cell_imagej_experiments,
        render_cell_imagej_macro,
    )

    experiment_ids = {spec.experiment_id for spec in list_cell_imagej_experiments()}

    assert experiment_ids == {"wound_scratch", "transwell", "immunohistochemistry"}
    assert get_cell_imagej_experiment("划痕实验").analysis_type == "scratch_area"
    assert get_cell_imagej_experiment("ihc").analysis_type == "immunohistochemistry"

    scratch = render_cell_imagej_macro(
        "scratch_area",
        tmp_path / "images",
        tmp_path / "out",
        parameters={"threshold_method": "Otsu", "min_gap_area_px": 1200},
    )
    transwell = render_cell_imagej_macro("transwell_count", tmp_path / "images", tmp_path / "out")
    ihc = render_cell_imagej_macro("immunohistochemistry", tmp_path / "images", tmp_path / "out")

    assert scratch.output_csv_path == tmp_path / "out" / "wound_scratch_results.csv"
    assert 'File.saveString("image,gap_area_px,total_area_px,gap_fraction' in scratch.macro_text
    assert 'threshold_method = "Otsu";' in scratch.macro_text
    assert "min_gap_area_px = 1200;" in scratch.macro_text
    assert "particle_count,total_particle_area_px" in transwell.macro_text
    assert 'run("Watershed")' in transwell.macro_text
    assert "positive_area_px,total_area_px,positive_fraction" in ihc.macro_text
    assert "mean_gray" in ihc.macro_text


def test_cell_image_task_store_renders_real_imagej_macro_not_placeholder(tmp_path) -> None:
    from app.labtools.image_analysis import ImageAnalysisTaskStore

    image_path = tmp_path / "scratch.png"
    image_path.write_bytes(b"image")
    store = ImageAnalysisTaskStore(tmp_path / "tasks")

    workspace = store.create_workspace(
        task_name="Scratch image workflow",
        experiment_module="cell_experiment",
        analysis_type="scratch_area",
        image_paths=(str(image_path),),
        import_mode="reference_original_path",
        parameters={"threshold_method": "Otsu", "min_gap_area_px": "1500"},
    )
    macro_text = workspace.selected_macro_path.read_text(encoding="utf-8")

    assert "Placeholder macro" not in macro_text
    assert "dev/labtools@0bd04b2 cell ImageJ workflows" in macro_text
    assert 'inputDir = "' in macro_text
    assert str(tmp_path) in macro_text
    assert 'outputCsv = outputDir + "wound_scratch_results.csv";' in macro_text
    assert 'threshold_method = "Otsu";' in macro_text
    assert "min_gap_area_px = 1500;" in macro_text


def test_builtin_macro_registry_marks_first_wave_macros_as_imagej() -> None:
    from app.labtools.image_analysis import builtin_macro_registry

    templates = {template.macro_id: template for template in builtin_macro_registry()}

    for macro_id in (
        "wb_grayscale_basic",
        "wb_lane_band_measurement",
        "wb_batch_preprocess",
        "wb_fixed_rectangle_roi_measure",
        "scratch_area_basic",
        "transwell_count_basic",
        "fluorescence_intensity_basic",
        "ihc_dab_area_basic",
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
