from __future__ import annotations

from pathlib import Path

from app.bioinformatics.plots import create_formal_deg_plot_artifact, evaluate_plot_export_quality_gate
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


def test_plot_export_quality_passes_for_formal_deg_svg(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "formal.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text("feature_id\tgene_symbol\tlog2_fold_change\tp_value\tadjusted_p_value\tsignificance_label\nf1\tTP53\t1.4\t0.01\t0.02\tup\n", encoding="utf-8")
    _register_formal(tmp_path, table)
    result = create_formal_deg_plot_artifact(tmp_path, result_id="formal-qc", plot_type="volcano_plot")

    gate = evaluate_plot_export_quality_gate(tmp_path, result["plot_artifact"])

    assert gate["status"] == "passed"
    assert gate["image_checks"][0]["status"] == "passed"
    assert gate["report_ready_eligible_changed"] is False
    assert gate["clinical_conclusion_enabled"] is False


def test_plot_export_quality_blocks_missing_image_and_semantics_mismatch(tmp_path: Path) -> None:
    gate = evaluate_plot_export_quality_gate(
        tmp_path,
        {
            "plot_id": "bad",
            "plot_type": "volcano_plot",
            "source_result_id": "testing",
            "source_result_semantics": "testing_level",
            "plot_semantics": "formal_computed_result",
            "plot_artifact_scope": "formal_deg_plot",
            "image_artifacts": [{"path": "missing.svg", "format": "svg", "sha256": "bad"}],
            "report_ready_eligible": False,
        },
    )

    assert gate["status"] == "blocked"
    assert "formal_plot_qc_requires_formal_computed_source" in gate["blockers"]
    assert "plot_qc_semantics_must_inherit_source" in gate["blockers"]
    assert "plot_image_file_missing" in gate["blockers"]


def _register_formal(root: Path, table: Path) -> None:
    register_result(
        root,
        ResultIndexEntry(
            result_id="formal-qc",
            task_run_id="task-formal-qc",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="pkg-1",
            source_dataset_id="dataset-1",
            source_repository_manifest="standardized_data/repositories/repository_manifest.json",
            parameters_manifest={"method": "welch_t_test"},
            engine_name="python_scipy_statsmodels_deg_mvp",
            engine_version="0.1",
            dependency_snapshot={"status": "passed", "packages": {"scipy": {"version": "1.17.1"}}},
            output_artifacts=({"artifact_type": "deg_result_table", "path": str(table.relative_to(root)), "schema": "biomedpilot.deg_result_table.v1"},),
            validation_status="passed",
            log_artifacts=({"artifact_type": "formal_deg_run_log", "path": "analysis/formal_deg/formal-qc_run_log.json"},),
            report_ready_eligible=False,
        ),
    )
