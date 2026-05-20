from __future__ import annotations

from app.bioinformatics.results.validation import validate_result_entry


def test_imported_result_cannot_be_labeled_recomputed() -> None:
    entry = {
        "result_id": "imported",
        "task_run_id": "task",
        "task_type": "recomputed_deg",
        "result_semantics": "imported_external_result",
        "input_package_id": "pkg",
        "source_dataset_id": "dataset",
        "source_repository_manifest": "manifest",
        "parameters_manifest": {},
        "engine_name": "",
        "engine_version": "",
        "dependency_snapshot": {},
        "output_artifacts": [],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "not_validated",
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

    validation = validate_result_entry(entry)

    assert "imported_result_must_not_be_labeled_recomputed" in validation["blockers"]
