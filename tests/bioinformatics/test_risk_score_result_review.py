from __future__ import annotations

from pathlib import Path

from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result
from app.bioinformatics.survival_clinical import build_risk_score_result_review, export_risk_score_review_table


def test_risk_score_result_review_summarizes_formal_table_only_result(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n"
        "S2\tC2\t-0.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="testing-risk",
            task_run_id="task-testing",
            task_type="risk_score",
            result_semantics="testing_level",
            validation_status="passed",
        ),
    )

    review = build_risk_score_result_review(tmp_path, sort_by="risk_score", filter_mode="positive_score")

    assert review["status"] == "passed"
    assert review["summary"]["sample_count"] == 2
    assert review["summary"]["max_risk_score"] == 1.5
    assert review["summary"]["source_cox_multivariate_result_id"] == "cox-mv-1"
    assert review["rows"][0]["sample_id"] == "S1"
    assert review["provenance"]["source_cox_multivariate_result_id"] == "cox-mv-1"
    assert review["provenance"]["plot_artifacts"] == []
    assert review["provenance"]["report_artifacts"] == []
    assert review["provenance"]["report_ready_eligible"] is False
    assert review["excluded_results"][0]["result_id"] == "testing-risk"
    assert "not a clinical prognosis conclusion" in review["guard_copy"]
    assert "Risk group/cutpoint labels remain disabled" in review["disabled_downstream"]["risk_group"]


def test_risk_score_review_export_is_table_only_not_report_ready(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    exported = export_risk_score_review_table(tmp_path, file_format="csv")

    assert exported["status"] == "passed"
    assert exported["file_format"] == "csv"
    assert exported["report_ready_eligible"] is False
    assert exported["plot_artifacts"] == []
    assert exported["report_artifacts"] == []
    export_path = Path(str(exported["export_path"]))
    assert export_path.is_file()
    assert "sample_id,case_id,risk_score" in export_path.read_text(encoding="utf-8")


def test_risk_score_review_blocks_non_formal_or_report_ready_sources(tmp_path: Path) -> None:
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="imported-risk",
            task_run_id="task-imported",
            task_type="risk_score",
            result_semantics="imported_external_result",
            validation_status="passed",
        ),
    )

    review = build_risk_score_result_review(tmp_path)

    assert review["status"] == "blocked"
    assert "formal_risk_score_result_not_found" in review["blockers"]
    assert review["rows"] == []
    assert review["excluded_results"][0]["result_semantics"] == "imported_external_result"


def _register_risk_score(root: Path, table: Path) -> None:
    register_result(
        root,
        ResultIndexEntry(
            result_id="risk-1",
            task_run_id="task-risk-1",
            task_type="risk_score",
            result_semantics="formal_computed_result",
            input_package_id="surv-1",
            source_dataset_id="surv-1",
            source_repository_manifest="B12 survival input package / B32 risk score contract gate",
            parameters_manifest={"status": "ready_for_parameter_confirmation"},
            engine_name="biomedpilot_controlled_risk_score",
            engine_version="0.1.0",
            dependency_snapshot={"status": "passed"},
            output_artifacts=({"artifact_type": "risk_score_result_table", "path": str(table.relative_to(root))},),
            plot_artifacts=(),
            report_artifacts=(),
            validation_status="passed",
            warnings=("risk_score_statistical_result_only",),
            log_artifacts=({"artifact_type": "task_run_log", "path": "analysis/risk/log.json"},),
            report_ready_eligible=False,
        ).to_dict()
        | {
            "source_cox_multivariate_result_id": "cox-mv-1",
            "risk_score_parameter_confirmation": {
                "schema_version": "biomedpilot.risk_score_parameter_confirmation.v1",
                "created_at": "now",
                "candidate_variables": ["age", "marker"],
                "source_cox_multivariate_result_id": "cox-mv-1",
                "cutoff_policy": {"policy": "predeclared_cutoff"},
                "scaling_policy": {"policy": "as_is"},
            },
        },
    )
