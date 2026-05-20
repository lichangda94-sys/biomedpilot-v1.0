from __future__ import annotations

from app.bioinformatics.reports.readiness import evaluate_report_ready_gate
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


def test_report_gate_blocks_testing_level_result_without_test_mode(tmp_path) -> None:
    register_result(tmp_path, ResultIndexEntry(result_id="test", task_run_id="task", task_type="deg", result_semantics="testing_level"))

    gate = evaluate_report_ready_gate(tmp_path)

    assert gate["status"] == "blocked"
    assert "unverified_testing_exploratory_or_imported_results_present" in gate["blockers"]


def test_report_gate_blocks_legacy_testing_semantics_even_with_complete_fields(tmp_path) -> None:
    from app.bioinformatics.results.registry import save_registry

    save_registry(
        tmp_path,
        [
            {
                "result_id": "legacy-testing",
                "task_run_id": "task",
                "task_type": "deg",
                "result_semantics": "testing-level",
                "input_package_id": "pkg",
                "source_dataset_id": "dataset",
                "source_repository_manifest": "manifest",
                "parameters_manifest": {"method": "preview"},
                "engine_name": "legacy",
                "engine_version": "1",
                "dependency_snapshot": {"deps": "recorded"},
                "output_artifacts": [],
                "plot_artifacts": [],
                "report_artifacts": [],
                "validation_status": "passed",
                "warnings": [],
                "blockers": [],
                "log_artifacts": [],
                "failure_reason": "",
                "created_at": "now",
                "updated_at": "now",
                "schema_version": "biomedpilot.result_index_entry.v1",
                "report_ready_eligible": False,
                "migration_status": "native_v2",
            }
        ],
    )

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
