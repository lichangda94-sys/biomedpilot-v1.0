from __future__ import annotations

from app.bioinformatics.clinical_analysis import build_survival_package
from app.bioinformatics.plots import create_km_plot_artifact
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result
from app.bioinformatics.survival_clinical import build_km_logrank_parameter_manifest, confirm_km_logrank_parameters, run_controlled_km_logrank


def test_km_plot_artifact_is_spec_only_and_registered(tmp_path) -> None:
    result = _run(tmp_path)

    plot = create_km_plot_artifact(str(tmp_path), result["result_id"])

    assert plot["plot_type"] == "km_curve"
    assert plot["source_result_semantics"] == "formal_computed_result"
    assert plot["image_artifacts"] == []
    assert plot["plot_spec_artifact"]["rendering"] == "spec_only_no_image_dependency"
    index_text = (tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8")
    assert plot["plot_id"] in index_text
    assert '"report_ready_eligible": false' in index_text


def test_km_plot_blocks_preflight_testing_source(tmp_path) -> None:
    register_result(tmp_path, ResultIndexEntry(result_id="preflight", task_run_id="t", task_type="survival_km_logrank", result_semantics="preflight_only", validation_status="passed"))

    plot = create_km_plot_artifact(str(tmp_path), "preflight")

    assert "km_plot_requires_formal_computed_result_source" in plot["blockers"]


def _run(tmp_path):
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tOS_time\tOS_event\tarm\n"
        "S1\t5\t1\tA\nS2\t8\t0\tA\nS3\t12\t1\tA\n"
        "S4\t6\t1\tB\nS5\t9\t0\tB\nS6\t15\t1\tB\n",
        encoding="utf-8",
    )
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    manifest = build_km_logrank_parameter_manifest(package, outcome_gate={"status": "passed", "survival_outcome_gate_id": "outcome-1", "blockers": []}, grouping_variable="arm", group_a="A", group_b="B", dependency_snapshot={"status": "passed", "python_lifelines": {"available": True, "version": "test"}})
    return run_controlled_km_logrank(tmp_path, manifest, confirm_km_logrank_parameters(tmp_path, manifest), allow_legacy_sidecar_execution=True)
