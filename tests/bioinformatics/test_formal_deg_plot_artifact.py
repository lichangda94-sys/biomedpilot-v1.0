from __future__ import annotations

from pathlib import Path

from app.bioinformatics.plots import build_formal_deg_plot_gate, build_formal_deg_plot_production_gate, create_formal_deg_plot_artifact
from app.bioinformatics.reports.readiness import evaluate_report_ready_gate
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import load_registry, register_result


def test_formal_deg_plot_artifact_registers_to_result_index_and_keeps_report_disabled(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "formal.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text("feature_id\tgene_symbol\tlog2_fold_change\tp_value\tadjusted_p_value\tsignificance_label\nf1\tTP53\t1.4\t0.01\t0.02\tup\n", encoding="utf-8")
    _register_formal(tmp_path, table)

    gate = build_formal_deg_plot_gate(tmp_path, result_id="formal-plot", plot_type="volcano_plot")
    result = create_formal_deg_plot_artifact(tmp_path, result_id="formal-plot", plot_type="volcano_plot")

    assert gate["status"] == "passed"
    assert result["status"] == "passed"
    assert result["report_ready_eligible"] is False
    assert result["report_artifacts"] == []
    artifact = result["plot_artifact"]
    assert artifact["plot_artifact_scope"] == "formal_deg_plot"
    assert artifact["source_result_semantics"] == "formal_computed_result"
    assert artifact["plot_semantics"] == "formal_computed_result"
    assert artifact["plot_spec_artifact"]["data_source"] == "result_index_output_artifacts"
    assert artifact["image_artifacts"][0]["format"] == "svg"
    assert artifact["image_artifacts"][0]["sha256"]
    svg_path = tmp_path / artifact["image_artifacts"][0]["path"]
    assert svg_path.is_file()
    assert "Formal DEG Volcano Plot" in svg_path.read_text(encoding="utf-8")
    assert "clinical diagnosis" in svg_path.read_text(encoding="utf-8")
    assert (tmp_path / artifact["renderer_log_artifact"]["path"]).is_file()
    assert "clinical conclusions" in result["guard_copy"]

    entry = load_registry(tmp_path)["results"][0]
    assert entry["plot_artifacts"][0]["plot_id"] == "formal-plot-volcano_plot-artifact"
    assert entry["report_ready_eligible"] is False
    report_gate = evaluate_report_ready_gate(tmp_path)
    assert report_gate["status"] == "blocked"
    assert "included_results_marked_report_ready_eligible" in report_gate["blockers"]


def test_formal_deg_plot_blocks_imported_testing_and_preflight_sources(tmp_path: Path) -> None:
    for result_id, semantics in (
        ("imported", "imported_external_result"),
        ("testing", "testing_level"),
        ("preflight", "preflight_only"),
    ):
        register_result(
            tmp_path,
            ResultIndexEntry(
                result_id=result_id,
                task_run_id=f"task-{result_id}",
                task_type="deg",
                result_semantics=semantics,
                validation_status="passed",
            ),
        )

    for result_id in ("imported", "testing", "preflight"):
        result = create_formal_deg_plot_artifact(tmp_path, result_id=result_id, plot_type="volcano_plot")
        assert result["status"] == "blocked"
        assert any("formal_deg_plot_requires_formal_computed_result_source" in blocker for blocker in result["blockers"])


def test_formal_deg_plot_blocks_non_deg_and_missing_deg_table(tmp_path: Path) -> None:
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="formal-no-table",
            task_run_id="task",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="pkg",
            source_dataset_id="dataset",
            source_repository_manifest="manifest",
            parameters_manifest={"method": "welch_t_test"},
            engine_name="engine",
            engine_version="1",
            dependency_snapshot={"packages": {"scipy": {"available": True}}},
            validation_status="passed",
            report_ready_eligible=False,
        ),
    )

    result = create_formal_deg_plot_artifact(tmp_path, result_id="formal-no-table", plot_type="volcano_plot")

    assert result["status"] == "blocked"
    assert "formal_deg_plot_requires_deg_result_table" in result["blockers"]


def test_formal_deg_plot_production_gate_passes_for_builtin_volcano_renderer(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "formal.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text("feature_id\tgene_symbol\tlog2_fold_change\tp_value\tadjusted_p_value\tsignificance_label\nf1\tTP53\t1.4\t0.01\t0.02\tup\n", encoding="utf-8")
    _register_formal(tmp_path, table)

    passed = build_formal_deg_plot_production_gate(tmp_path, result_id="formal-plot")
    blocked = build_formal_deg_plot_production_gate(tmp_path, result_id="formal-plot", renderer_capability={"status": "blocked", "renderer": "external", "blockers": ["renderer_missing"]})

    assert blocked["status"] == "blocked"
    assert "renderer_missing" in blocked["blockers"]
    assert passed["status"] == "passed"
    assert passed["renderer_capability"]["renderer"] == "biomedpilot_builtin_svg_volcano"
    assert passed["inherits_source_semantics"] is True
    assert passed["report_ready_eligible_changed"] is False
    assert passed["clinical_conclusion_enabled"] is False


def _register_formal(root: Path, table: Path) -> None:
    register_result(
        root,
        ResultIndexEntry(
            result_id="formal-plot",
            task_run_id="task-formal-plot",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="pkg-1",
            source_dataset_id="dataset-1",
            source_repository_manifest="standardized_data/repositories/repository_manifest.json",
            parameters_manifest={"method": "welch_t_test", "case_samples": ["case1", "case2"], "control_samples": ["ctrl1", "ctrl2"]},
            engine_name="python_scipy_statsmodels_deg_mvp",
            engine_version="0.1",
            dependency_snapshot={"packages": {"scipy": {"version": "1.17.1"}, "statsmodels": {"version": "0.14.6"}}},
            output_artifacts=({"artifact_type": "deg_result_table", "path": str(table.relative_to(root)), "schema": "biomedpilot.deg_result_table.v1"},),
            plot_artifacts=(),
            report_artifacts=(),
            validation_status="passed",
            log_artifacts=({"artifact_type": "formal_deg_run_log", "path": "analysis/formal_deg/formal-plot_run_log.json"},),
            report_ready_eligible=False,
        ),
    )
