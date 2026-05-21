from __future__ import annotations

from app.bioinformatics.survival_clinical.km_result_schema import validate_km_result_index_entry, validate_km_result_tables


def test_km_result_tables_require_columns_and_forbid_hr_fields() -> None:
    validation = validate_km_result_tables(
        [{"time": 1, "survival_probability": 1.0, "group": "A", "at_risk": 2, "events": 1, "censored": 0, "time_unit": "days", "warnings": ""}],
        [{"group_a": "A", "group_b": "B", "test_statistic": 1.2, "p_value": 0.2, "method": "two_group_logrank_chi_square_df1", "event_count_group_a": 1, "event_count_group_b": 1, "sample_count_group_a": 2, "sample_count_group_b": 2, "warnings": ""}],
    )

    assert validation["status"] == "passed"
    blocked = validate_km_result_tables([], [{"hazard_ratio": 2.0}])
    assert "missing_km_curve_table" in blocked["blockers"]
    assert any("cox_or_hr_field_forbidden" in item for item in blocked["blockers"])


def test_km_result_index_blocks_non_formal_or_report_ready() -> None:
    entry = {
        "result_id": "r",
        "task_run_id": "t",
        "task_type": "survival_km_logrank",
        "result_semantics": "testing_level",
        "input_package_id": "surv",
        "source_dataset_id": "surv",
        "source_repository_manifest": "B12",
        "parameters_manifest": {"status": "passed"},
        "engine_name": "engine",
        "engine_version": "1",
        "dependency_snapshot": {"status": "passed"},
        "output_artifacts": [{"artifact_type": "km_curve_table"}, {"artifact_type": "logrank_result_table"}],
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
        "report_ready_eligible": True,
        "migration_status": "native_v2",
        "survival_clinical_input_id": "surv",
        "survival_outcome_gate_id": "outcome",
    }

    validation = validate_km_result_index_entry(entry)

    assert "non_formal_semantics:testing_level" in validation["blockers"]
    assert "survival_report_ready_forbidden_in_b13" in validation["blockers"]
