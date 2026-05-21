from __future__ import annotations

from app.bioinformatics.survival_clinical.cox_result_schema import validate_cox_result_index_entry, validate_cox_result_table


def test_cox_result_table_requires_columns_and_forbids_risk_score() -> None:
    row = {
        "covariate": "arm",
        "covariate_label": "arm",
        "covariate_type": "binary_variable",
        "hazard_ratio": 1.2,
        "ci_lower": 0.5,
        "ci_upper": 3.0,
        "p_value": 0.8,
        "z_statistic": 0.2,
        "sample_count": 6,
        "event_count": 4,
        "non_missing_count": 6,
        "missing_count": 0,
        "method": "single_variable_cox_partial_likelihood_breslow_ties",
        "warnings": "",
    }
    assert validate_cox_result_table([row])["status"] == "passed"
    blocked = validate_cox_result_table([{**row, "risk_score": "x"}])
    assert "cox_row_0:forbidden_field:risk_score" in blocked["blockers"]


def test_cox_result_index_blocks_non_formal_or_report_ready() -> None:
    entry = {
        "result_id": "r",
        "task_run_id": "t",
        "task_type": "cox_univariate",
        "result_semantics": "testing_level",
        "input_package_id": "surv",
        "source_dataset_id": "surv",
        "source_repository_manifest": "B12",
        "parameters_manifest": {"status": "passed"},
        "engine_name": "engine",
        "engine_version": "1",
        "dependency_snapshot": {"status": "passed"},
        "output_artifacts": [{"artifact_type": "cox_result_table"}],
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
    validation = validate_cox_result_index_entry(entry)
    assert "non_formal_semantics:testing_level" in validation["blockers"]
    assert "cox_report_ready_forbidden_in_b14" in validation["blockers"]
