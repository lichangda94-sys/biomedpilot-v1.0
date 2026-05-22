from __future__ import annotations

from app.bioinformatics.survival_clinical import validate_cox_multivariate_result_index_entry, validate_cox_multivariate_result_table


def test_cox_multivariate_result_table_requires_adjusted_rows_and_forbids_risk_score() -> None:
    row = {
        "covariate": "age",
        "covariate_label": "age",
        "covariate_type": "continuous_variable",
        "hazard_ratio": 1.1,
        "ci_lower": 0.9,
        "ci_upper": 1.4,
        "p_value": 0.2,
        "z_statistic": 1.1,
        "sample_count": 24,
        "event_count": 20,
        "non_missing_count": 24,
        "missing_count": 0,
        "adjusted_for": "marker",
        "method": "multivariate_cox_partial_likelihood_breslow_ties",
        "warnings": "not_clinical_conclusion",
    }

    assert validate_cox_multivariate_result_table([row])["status"] == "passed"
    blocked = validate_cox_multivariate_result_table([{**row, "risk_score": "x"}])
    assert "cox_multivariate_row_0:forbidden_field:risk_score" in blocked["blockers"]


def test_cox_multivariate_result_index_keeps_task_type_and_report_boundary() -> None:
    entry = {
        "result_id": "r",
        "task_run_id": "t",
        "task_type": "cox_multivariate",
        "result_semantics": "formal_computed_result",
        "input_package_id": "surv",
        "source_dataset_id": "surv",
        "source_repository_manifest": "B12",
        "parameters_manifest": {"status": "passed"},
        "engine_name": "engine",
        "engine_version": "1",
        "dependency_snapshot": {"status": "passed"},
        "output_artifacts": [{"artifact_type": "cox_multivariate_result_table"}],
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
        "survival_clinical_input_id": "surv",
        "survival_outcome_gate_id": "outcome",
    }

    assert validate_cox_multivariate_result_index_entry(entry)["status"] == "passed"
    blocked = validate_cox_multivariate_result_index_entry({**entry, "report_ready_eligible": True})
    assert "cox_multivariate_report_ready_forbidden_in_b20" in blocked["blockers"]
    wrong_task = validate_cox_multivariate_result_index_entry({**entry, "task_type": "cox_univariate"})
    assert "task_type_must_be_cox_multivariate" in wrong_task["blockers"]
