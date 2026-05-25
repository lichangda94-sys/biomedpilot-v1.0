from __future__ import annotations

from pathlib import Path

from app.bioinformatics.survival_clinical import (
    RISK_SCORE_CONFIRMATION_PATH,
    confirm_risk_score_parameters,
    load_risk_score_parameter_confirmation,
    validate_risk_score_parameter_confirmation,
)


def test_risk_score_confirmation_writes_manifest_but_keeps_execution_disabled(tmp_path: Path) -> None:
    contract = _ready_contract()

    confirmation = confirm_risk_score_parameters(tmp_path, contract, reviewer_id="reviewer")
    gate = validate_risk_score_parameter_confirmation(confirmation, {**contract, "created_at": "later"})

    assert confirmation["status"] == "confirmed"
    assert confirmation["confirmed_by_user"] is True
    assert confirmation["reviewer_id"] == "reviewer"
    assert confirmation["formal_execution_enabled"] is False
    assert confirmation["writes_result_index"] is False
    assert confirmation["result_semantics"] == "parameter_confirmation_only"
    assert confirmation["report_ready_eligible"] is False
    assert confirmation["output_plan"]["risk_score_result_table_path"].endswith("_risk_score.tsv")
    assert gate["status"] == "passed"
    assert gate["formal_execution_enabled"] is False
    assert (tmp_path / RISK_SCORE_CONFIRMATION_PATH).is_file()
    assert load_risk_score_parameter_confirmation(tmp_path)["schema_version"] == "biomedpilot.risk_score_parameter_confirmation.v1"
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def test_risk_score_confirmation_blocks_unready_contract_and_missing_user_confirmation(tmp_path: Path) -> None:
    contract = {**_ready_contract(), "status": "blocked", "source_result_dependency_snapshot": {"status": "blocked"}}

    confirmation = confirm_risk_score_parameters(tmp_path, contract, confirmed_by_user=False)
    gate = validate_risk_score_parameter_confirmation(confirmation, contract)

    assert confirmation["status"] == "blocked"
    assert "risk_score_contract_gate_not_ready" in gate["blockers"]
    assert "risk_score_parameters_not_user_confirmed" in gate["blockers"]
    assert "source_dependency_snapshot_not_passed" in gate["blockers"]


def test_risk_score_confirmation_requires_clinical_boundary_acknowledgement(tmp_path: Path) -> None:
    contract = _ready_contract()
    contract["interpretation_boundary"] = {"clinical_conclusion_forbidden": False}

    confirmation = confirm_risk_score_parameters(tmp_path, contract)
    gate = validate_risk_score_parameter_confirmation(confirmation, contract)

    assert "risk_score_clinical_boundary_not_acknowledged" in gate["blockers"]


def test_missing_risk_score_confirmation_is_blocked(tmp_path: Path) -> None:
    gate = validate_risk_score_parameter_confirmation(load_risk_score_parameter_confirmation(tmp_path), _ready_contract())

    assert gate["status"] == "blocked"
    assert "risk_score_parameter_confirmation_missing" in gate["blockers"]


def _ready_contract() -> dict[str, object]:
    return {
        "schema_version": "biomedpilot.risk_score_nomogram_contract_gate.v1",
        "created_at": "now",
        "status": "ready_for_parameter_confirmation",
        "source_survival_package_id": "surv-1",
        "source_clinical_variable_audit_id": "clinical-audit-1",
        "source_cox_multivariate_result_id": "cox-mv-1",
        "candidate_variables": ["age", "marker"],
        "coefficient_source": {"source_result_id": "cox-mv-1", "source_manifest_path": "results/summaries/result_index.json"},
        "training_validation_plan": {"training_set": "training cohort", "validation_set": "holdout cohort"},
        "cutoff_policy": {"policy": "predeclared_cutoff", "value": 0.5},
        "missingness_policy": {"policy": "block_missing_required_variables"},
        "scaling_policy": {"policy": "use_training_cohort_parameters"},
        "calibration_plan": {"policy": "calibration_curve_on_validation_cohort"},
        "nomogram_policy": {"policy": "disabled_until_renderer_gate"},
        "validation_plan": {"cross_validation": "5-fold", "external_validation": "holdout cohort"},
        "source_result_dependency_snapshot": {"status": "passed", "python_lifelines": {"available": True}},
        "source_result_parameters_manifest": {"status": "passed", "selected_covariates": ["age", "marker"]},
        "interpretation_boundary": {
            "statistical_model_contract_only": True,
            "clinical_conclusion_forbidden": True,
            "prognosis_label_forbidden": True,
            "treatment_recommendation_forbidden": True,
            "ordinary_user_execution_enabled": False,
        },
        "formal_execution_enabled": False,
        "writes_result_index": False,
        "result_semantics": "contract_gate_only",
        "report_ready_eligible": False,
        "forbidden_outputs": ["risk_score_result", "nomogram", "clinical_prognosis", "treatment_recommendation"],
        "blockers": [],
        "warnings": ["risk_score_contract_gate_only"],
    }
