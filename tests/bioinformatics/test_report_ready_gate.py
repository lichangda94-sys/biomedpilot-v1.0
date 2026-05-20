from __future__ import annotations

from app.bioinformatics.reports.readiness import evaluate_report_ready_gate
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


def test_report_gate_blocks_testing_level_result_without_test_mode(tmp_path) -> None:
    register_result(tmp_path, ResultIndexEntry(result_id="test", task_run_id="task", task_type="deg", result_semantics="testing_level"))

    gate = evaluate_report_ready_gate(tmp_path)

    assert gate["status"] == "blocked"
    assert "unverified_testing_exploratory_or_imported_results_present" in gate["blockers"]


def test_report_gate_passes_complete_formal_result(tmp_path) -> None:
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="formal",
            task_run_id="task",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="pkg",
            source_dataset_id="dataset",
            source_repository_manifest="manifest",
            parameters_manifest={"method": "welch"},
            engine_name="python",
            engine_version="1",
            dependency_snapshot={"scipy": {"available": True}},
            validation_status="passed",
        ),
    )

    gate = evaluate_report_ready_gate(tmp_path)

    assert gate["status"] == "eligible_for_internal_report"
