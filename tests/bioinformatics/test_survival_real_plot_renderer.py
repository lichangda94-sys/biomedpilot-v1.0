from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.plots import survival_real
from app.bioinformatics.clinical_analysis import build_survival_package
from app.bioinformatics.plots import build_survival_real_plot_gate, check_survival_plot_renderer_dependencies, create_survival_real_plot_artifact
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import load_registry, register_result
from app.bioinformatics.survival_clinical import (
    build_cox_univariate_parameter_manifest,
    build_km_logrank_parameter_manifest,
    confirm_cox_univariate_parameters,
    confirm_km_logrank_parameters,
    run_controlled_cox_univariate,
    run_controlled_km_logrank,
)


def test_real_km_plot_generates_svg_artifact_and_preserves_source_result(tmp_path: Path) -> None:
    result = _run_km(tmp_path)

    output = create_survival_real_plot_artifact(tmp_path, result["result_id"])

    assert output["status"] == "passed"
    artifact = output["plot_artifact"]
    assert artifact["plot_type"] == "km_curve"
    assert artifact["source_result_semantics"] == "formal_computed_result"
    assert artifact["plot_semantics"] == "formal_computed_result"
    assert artifact["image_artifacts"][0]["format"] == "svg"
    assert Path(artifact["image_artifacts"][0]["path"]).is_file()
    assert output["report_ready_eligible"] is False
    manifest = json.loads(Path(output["plot_manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["report_ready_eligible"] is False
    registry = load_registry(tmp_path)
    source = next(entry for entry in registry["results"] if entry["result_id"] == result["result_id"])
    assert source["result_semantics"] == "formal_computed_result"
    assert source["report_ready_eligible"] is False
    assert source["plot_artifacts"][0]["image_artifacts"][0]["source_result_id"] == result["result_id"]


def test_real_cox_plot_generates_svg_artifact_from_formal_cox_only(tmp_path: Path) -> None:
    result = _run_cox(tmp_path)

    output = create_survival_real_plot_artifact(tmp_path, result["result_id"])

    assert output["status"] == "passed"
    artifact = output["plot_artifact"]
    assert artifact["plot_type"] == "cox_forest_plot"
    assert artifact["source_task_type"] == "cox_univariate"
    assert artifact["image_artifacts"][0]["format"] == "svg"
    assert Path(artifact["image_artifacts"][0]["path"]).read_text(encoding="utf-8").startswith("<svg")
    assert output["report_ready_eligible"] is False


def test_real_plot_blocks_preflight_and_does_not_register_image_artifact(tmp_path: Path) -> None:
    register_result(tmp_path, ResultIndexEntry(result_id="preflight", task_run_id="t", task_type="survival_km_logrank", result_semantics="preflight_only", validation_status="passed"))

    output = create_survival_real_plot_artifact(tmp_path, "preflight")

    assert output["status"] == "blocked"
    assert "survival_real_plot_requires_formal_computed_result_source" in output["blockers"]
    assert output["plot_artifact"]["image_artifacts"] == []
    registry = load_registry(tmp_path)
    source = next(entry for entry in registry["results"] if entry["result_id"] == "preflight")
    assert source.get("plot_artifacts", []) == []


def test_missing_matplotlib_renderer_blocks_gracefully(tmp_path: Path, monkeypatch) -> None:
    result = _run_km(tmp_path)
    monkeypatch.setattr(survival_real.importlib.util, "find_spec", lambda name: None if name == "matplotlib" else object())

    dependency = check_survival_plot_renderer_dependencies(renderer="matplotlib_png")
    gate = build_survival_real_plot_gate(tmp_path, result["result_id"], renderer="matplotlib_png")
    output = create_survival_real_plot_artifact(tmp_path, result["result_id"], renderer="matplotlib_png")

    assert dependency["status"] == "blocked"
    assert "matplotlib_missing_for_survival_plot_renderer" in dependency["blockers"]
    assert gate["status"] == "blocked"
    assert output["status"] == "blocked"
    assert output["plot_artifact"]["image_artifacts"] == []


def _run_km(tmp_path: Path) -> dict:
    package = _package(tmp_path)
    manifest = build_km_logrank_parameter_manifest(
        package,
        outcome_gate={"status": "passed", "survival_outcome_gate_id": "outcome-1", "blockers": []},
        grouping_variable="arm",
        group_a="A",
        group_b="B",
        dependency_snapshot={"status": "passed", "python_lifelines": {"available": True, "version": "test"}},
    )
    return run_controlled_km_logrank(tmp_path, manifest, confirm_km_logrank_parameters(tmp_path, manifest))


def _run_cox(tmp_path: Path) -> dict:
    package = _package(tmp_path)
    manifest = build_cox_univariate_parameter_manifest(
        package,
        outcome_gate={"status": "passed", "survival_outcome_gate_id": "outcome-1", "blockers": []},
        covariate="arm",
        dependency_snapshot={"status": "passed", "python_lifelines": {"available": True, "version": "test"}},
    )
    return run_controlled_cox_univariate(tmp_path, manifest, confirm_cox_univariate_parameters(tmp_path, manifest))


def _package(tmp_path: Path) -> dict:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tOS_time\tOS_event\tarm\n"
        "S1\t5\t1\tA\nS2\t8\t0\tA\nS3\t12\t1\tA\nS7\t16\t0\tA\n"
        "S4\t6\t1\tB\nS5\t9\t0\tB\nS6\t15\t1\tB\nS8\t18\t0\tB\n",
        encoding="utf-8",
    )
    return build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
