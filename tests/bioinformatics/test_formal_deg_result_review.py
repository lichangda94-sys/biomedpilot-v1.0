from __future__ import annotations

from pathlib import Path

from app.bioinformatics.deg_engine.result_review import build_formal_deg_result_review, export_formal_deg_review_table
from app.bioinformatics.deg_engine.standard_package import write_formal_deg_standard_result_package
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


def test_formal_deg_result_review_summarizes_and_filters_only_formal_deg(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "formal.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "feature_id\tgene_symbol\tbase_mean_or_mean_expression\tcase_mean\tcontrol_mean\tlog2_fold_change\tstatistic\tp_value\tadjusted_p_value\tsignificance_label\twarnings\n"
        "g1\tTP53\t10\t12\t4\t1.5\t3.0\t0.001\t0.003\tup\t\n"
        "g2\tEGFR\t10\t3\t9\t-1.4\t-2.9\t0.002\t0.004\tdown\t\n"
        "g3\tGAPDH\t8\t8\t7\t0.1\t0.1\t0.8\t0.9\tnot_significant\t\n",
        encoding="utf-8",
    )
    _register_formal(tmp_path, table)
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="imported",
            task_run_id="task-imported",
            task_type="deg",
            result_semantics="imported_external_result",
            validation_status="passed",
        ),
    )

    review = build_formal_deg_result_review(tmp_path, sort_by="adjusted_p_value", significance_filter="significant")

    assert review["status"] == "passed"
    assert review["summary"]["total_gene_count"] == 3
    assert review["summary"]["significant_up_count"] == 1
    assert review["summary"]["significant_down_count"] == 1
    assert review["summary"]["method"] == "welch_t_test"
    assert review["summary"]["dependency_versions"]["scipy"] == "1.17.1"
    assert [row["gene_symbol"] for row in review["rows"]] == ["TP53", "EGFR"]
    assert review["provenance"]["input_package_id"] == "pkg-1"
    assert review["provenance"]["parameter_confirmation"] == "manifests/formal_deg_parameter_confirmation.json"
    assert review["provenance"]["standard_package_source_policy"] == "result_index_registered_standard_result_package_artifacts_only"
    assert review["provenance"]["standard_package_validation_status"] == "passed"
    assert review["provenance"]["standard_package_table_path"] == "tables/formal.tsv"
    assert review["provenance"]["plot_artifacts"] == []
    assert review["provenance"]["report_artifacts"] == []
    assert review["provenance"]["report_ready_eligible"] is False
    assert review["excluded_results"][0]["result_id"] == "imported"
    assert "not a clinical conclusion" in review["guard_copy"]


def test_formal_deg_review_export_is_table_only_not_report_ready(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "formal.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "feature_id\tgene_symbol\tlog2_fold_change\tp_value\tadjusted_p_value\tsignificance_label\n"
        "g1\tTP53\t1.5\t0.001\t0.003\tup\n",
        encoding="utf-8",
    )
    _register_formal(tmp_path, table)

    exported = export_formal_deg_review_table(tmp_path, file_format="csv")

    assert exported["status"] == "passed"
    assert exported["file_format"] == "csv"
    assert exported["report_ready_eligible"] is False
    assert exported["plot_artifacts"] == []
    assert exported["report_artifacts"] == []
    export_path = Path(str(exported["export_path"]))
    assert export_path.is_file()
    assert "feature_id,gene_symbol,log2_fold_change,p_value,adjusted_p_value,significance_label" in export_path.read_text(encoding="utf-8")


def test_formal_deg_review_blocks_when_only_non_formal_results_exist(tmp_path: Path) -> None:
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="testing",
            task_run_id="task-testing",
            task_type="deg",
            result_semantics="testing_level",
            validation_status="passed",
        ),
    )

    review = build_formal_deg_result_review(tmp_path)

    assert review["status"] == "blocked"
    assert "formal_deg_result_not_found" in review["blockers"]
    assert review["rows"] == []
    assert review["excluded_results"][0]["result_semantics"] == "testing_level"


def test_formal_deg_review_blocks_formal_result_without_standard_package(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "legacy_formal.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "feature_id\tgene_symbol\tlog2_fold_change\tp_value\tadjusted_p_value\tsignificance_label\n"
        "g1\tTP53\t1.5\t0.001\t0.003\tup\n",
        encoding="utf-8",
    )
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="legacy-formal",
            task_run_id="task-legacy-formal",
            task_type="deg",
            result_semantics="formal_computed_result",
            validation_status="passed",
            output_artifacts=({"artifact_type": "deg_result_table", "path": str(table.relative_to(tmp_path)), "schema": "biomedpilot.deg_result_table.v1"},),
        ),
    )

    review = build_formal_deg_result_review(tmp_path)

    assert review["status"] == "blocked"
    assert review["selected_result_id"] == "legacy-formal"
    assert review["blockers"] == ["formal_deg_standard_result_package_missing"]
    assert review["rows"] == []
    assert review["provenance"]["standard_package_source_policy"] == "result_index_registered_standard_result_package_artifacts_only"


def _register_formal(root: Path, table: Path) -> None:
    log_path = root / "analysis" / "formal_deg" / "formal-1_run_log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text('{"status":"passed"}\n', encoding="utf-8")
    parameter_manifest = {
        "method": "welch_t_test",
        "log2fc_threshold": 1.0,
        "p_value_threshold": 0.05,
        "fdr_threshold": 0.05,
        "case_samples": ["case1", "case2"],
        "control_samples": ["ctrl1", "ctrl2"],
    }
    dependency_snapshot = {
        "packages": {
            "numpy": {"version": "2.4.6"},
            "pandas": {"version": "3.0.3"},
            "scipy": {"version": "1.17.1"},
            "statsmodels": {"version": "0.14.6"},
        }
    }
    standard_package = write_formal_deg_standard_result_package(
        root,
        result_id="formal-1",
        task_run_id="task-formal-1",
        result_table_path=table,
        log_path=log_path,
        parameter_manifest=parameter_manifest,
        dependency_snapshot=dependency_snapshot,
        engine_name="python_scipy_statsmodels_deg_mvp",
        engine_version="0.1",
    )
    register_result(
        root,
        ResultIndexEntry(
            result_id="formal-1",
            task_run_id="task-formal-1",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="pkg-1",
            source_dataset_id="dataset-1",
            source_repository_manifest="standardized_data/repositories/repository_manifest.json",
            parameters_manifest=parameter_manifest,
            engine_name="python_scipy_statsmodels_deg_mvp",
            engine_version="0.1",
            dependency_snapshot=dependency_snapshot,
            output_artifacts=(
                {"artifact_type": "deg_result_table", "path": str(table.relative_to(root)), "schema": "biomedpilot.deg_result_table.v1"},
                {"artifact_type": "standard_result_package", "path": str(standard_package.relative_to(root)), "schema": "biomedpilot.analysis.result_package.v1"},
            ),
            plot_artifacts=(),
            report_artifacts=(),
            validation_status="passed",
            log_artifacts=(
                {"artifact_type": "formal_deg_run_log", "path": str(log_path.relative_to(root))},
                {"artifact_type": "analysis_worker_invocation_manifest", "path": str((standard_package / "logs" / "worker_invocation.json").relative_to(root)), "schema": "biomedpilot.analysis.worker_invocation.v1"},
            ),
            report_ready_eligible=False,
        ),
    )
