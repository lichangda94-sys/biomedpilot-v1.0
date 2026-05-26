from __future__ import annotations

from app.bioinformatics.survival_clinical import (
    build_risk_score_result_schema_gate,
    validate_risk_score_result_index_entry,
    validate_risk_score_result_table,
)


def test_risk_score_result_schema_gate_is_blocked_without_future_bundle() -> None:
    gate = build_risk_score_result_schema_gate(None, confirmation_gate={"status": "passed", "blockers": []})

    assert gate["status"] == "blocked"
    assert gate["formal_execution_enabled"] is False
    assert gate["writes_result_index"] is False
    assert gate["report_ready_eligible"] is False
    assert "risk_score_result_bundle_missing" in gate["blockers"]


def test_risk_score_result_schema_gate_requires_parameter_confirmation() -> None:
    gate = build_risk_score_result_schema_gate(_valid_entry(), confirmation_gate={"status": "blocked", "blockers": ["risk_score_parameter_confirmation_missing"]})

    assert gate["status"] == "blocked"
    assert "risk_score_parameter_confirmation_missing" in gate["blockers"]
    assert "risk_score_parameter_confirmation_gate_not_passed" in gate["blockers"]


def test_risk_score_result_table_requires_numeric_scores_and_forbids_groups() -> None:
    row = {
        "sample_id": "S1",
        "case_id": "C1",
        "risk_score": 1.25,
        "source_cox_multivariate_result_id": "cox-mv-1",
        "model_formula": "beta_age * age + beta_marker * marker",
        "coefficient_source": "cox-mv-1",
        "missingness_policy": "block_missing_required_variables",
        "scaling_policy": "use_training_cohort_parameters",
        "warnings": "statistical_result_only",
    }

    assert validate_risk_score_result_table([row])["status"] == "passed"
    blocked = validate_risk_score_result_table([{**row, "risk_score": "not numeric", "risk_group": "high"}])
    assert "risk_score_row_0:non_numeric:risk_score" in blocked["blockers"]
    assert "risk_score_row_0:forbidden_field:risk_group" in blocked["blockers"]


def test_risk_score_result_index_schema_allows_only_formal_statistical_result_without_report_ready() -> None:
    assert validate_risk_score_result_index_entry(_valid_entry())["status"] == "passed"
    assert validate_risk_score_result_index_entry({**_valid_entry(), "plot_artifacts": [_valid_plot_artifact()]})["status"] == "passed"

    imported = validate_risk_score_result_index_entry({**_valid_entry(), "result_semantics": "imported_external_result"})
    assert "non_formal_semantics:imported_external_result" in imported["blockers"]

    report_ready = validate_risk_score_result_index_entry({**_valid_entry(), "report_ready_eligible": True})
    assert "risk_score_report_ready_not_enabled" in report_ready["blockers"]

    clinical = validate_risk_score_result_index_entry({**_valid_entry(), "clinical_conclusion": "poor prognosis"})
    assert "forbidden_clinical_field:clinical_conclusion" in clinical["blockers"]

    nomogram = validate_risk_score_result_index_entry({**_valid_entry(), "plot_artifacts": [_valid_plot_artifact("risk_score_nomogram")]})
    assert nomogram["status"] == "passed"

    calibration = validate_risk_score_result_index_entry({**_valid_entry(), "plot_artifacts": [_valid_plot_artifact("risk_score_calibration_curve")]})
    assert calibration["status"] == "passed"

    decision = validate_risk_score_result_index_entry({**_valid_entry(), "plot_artifacts": [_valid_plot_artifact("risk_score_decision_curve")]})
    assert decision["status"] == "passed"


def _valid_entry() -> dict[str, object]:
    return {
        "result_id": "risk-1",
        "task_run_id": "task-risk-1",
        "task_type": "risk_score",
        "result_semantics": "formal_computed_result",
        "input_package_id": "surv",
        "source_dataset_id": "surv",
        "source_repository_manifest": "B12",
        "parameters_manifest": {"status": "passed"},
        "risk_score_parameter_confirmation": {"status": "confirmed"},
        "source_cox_multivariate_result_id": "cox-mv-1",
        "engine_name": "biomedpilot-risk-score",
        "engine_version": "0.0.0-schema-only",
        "dependency_snapshot": {"status": "passed"},
        "output_artifacts": [{"artifact_type": "risk_score_result_table", "path": "results/tables/risk.tsv"}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": [],
        "blockers": [],
        "log_artifacts": [{"artifact_type": "task_run_log", "path": "analysis/risk/log.json"}],
        "failure_reason": "",
        "created_at": "now",
        "updated_at": "now",
        "schema_version": "biomedpilot.result_index_entry.v1",
        "report_ready_eligible": False,
        "migration_status": "native_v2",
    }


def _valid_plot_artifact(plot_type: str = "risk_score_distribution_plot") -> dict[str, object]:
    return {
        "plot_id": "plot-risk-score-1",
        "plot_type": plot_type,
        "source_result_id": "risk-1",
        "source_result_semantics": "formal_computed_result",
        "source_task_type": "risk_score",
        "plot_semantics": "formal_computed_result",
        "plot_artifact_scope": "formal_risk_score_plot_artifact",
        "image_artifacts": [{"artifact_type": f"{plot_type}_svg", "path": "results/plots/risk.svg", "format": "svg"}],
        "table_artifacts": [{"artifact_type": "risk_score_result_table", "path": "results/tables/risk.tsv"}],
    }
