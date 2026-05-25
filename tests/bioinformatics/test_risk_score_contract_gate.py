from __future__ import annotations

from pathlib import Path

from app.bioinformatics.clinical_analysis import build_clinical_association_preflight, build_survival_package
from app.bioinformatics.survival_clinical import build_risk_score_nomogram_contract_gate


def test_risk_score_contract_gate_ready_for_confirmation_but_non_executing(tmp_path: Path) -> None:
    package, audit = _package_and_audit(tmp_path)
    gate = build_risk_score_nomogram_contract_gate(
        package,
        audit,
        model_spec=_complete_model_spec(),
        source_cox_result=_source_cox_result(),
    )

    assert gate["status"] == "ready_for_parameter_confirmation"
    assert gate["schema_version"] == "biomedpilot.risk_score_nomogram_contract_gate.v1"
    assert gate["source_cox_multivariate_result_id"] == "cox-mv-1"
    assert gate["candidate_variables"] == ["age", "marker"]
    assert gate["formal_execution_enabled"] is False
    assert gate["writes_result_index"] is False
    assert gate["result_semantics"] == "contract_gate_only"
    assert gate["report_ready_eligible"] is False
    assert "risk_score_result" in gate["forbidden_outputs"]
    assert "nomogram" in gate["forbidden_outputs"]
    assert gate["checks"]["no_execution"] is True
    assert gate["checks"]["no_result_index_write"] is True


def test_risk_score_contract_gate_blocks_wrong_or_unready_source(tmp_path: Path) -> None:
    package, audit = _package_and_audit(tmp_path)
    source = {
        **_source_cox_result(),
        "task_type": "cox_univariate",
        "result_semantics": "imported_external_result",
        "dependency_snapshot": {"status": "blocked"},
        "parameters_manifest": {},
        "log_artifacts": [],
        "output_artifacts": [],
    }

    gate = build_risk_score_nomogram_contract_gate(package, audit, model_spec=_complete_model_spec(), source_cox_result=source)

    for blocker in (
        "source_result_must_be_cox_multivariate",
        "source_result_must_be_formal_computed_result",
        "source_dependency_snapshot_not_passed",
        "source_parameters_manifest_missing",
        "source_task_run_log_missing",
        "source_cox_multivariate_result_table_missing",
    ):
        assert blocker in gate["blockers"]
    assert gate["status"] == "blocked"


def test_risk_score_contract_gate_blocks_missing_policies_and_forbidden_outputs(tmp_path: Path) -> None:
    package, audit = _package_and_audit(tmp_path)
    spec = _complete_model_spec()
    for key in ("missingness_policy", "scaling_policy", "calibration_plan", "nomogram_policy"):
        spec.pop(key)
    spec["cutoff_strategy"] = {"policy": "optimal_cutpoint"}
    spec["treatment_recommendation"] = "recommend treatment"

    gate = build_risk_score_nomogram_contract_gate(package, audit, model_spec=spec, source_cox_result=_source_cox_result())

    for blocker in (
        "missingness_policy_missing",
        "scaling_policy_missing",
        "calibration_plan_missing",
        "nomogram_policy_missing",
        "cutoff_policy_data_leakage_risk",
        "forbidden_clinical_output_requested:treatment_recommendation",
    ):
        assert blocker in gate["blockers"]


def test_risk_score_contract_gate_has_no_file_side_effect(tmp_path: Path) -> None:
    package, audit = _package_and_audit(tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    gate = build_risk_score_nomogram_contract_gate(package, audit, model_spec=_complete_model_spec(), source_cox_result=_source_cox_result())

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert gate["writes_result_index"] is False
    assert before == after
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def _package_and_audit(tmp_path: Path) -> tuple[dict[str, object], dict[str, object]]:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tOS_time\tOS_event\tage\tmarker\n"
        "S1\t5\t1\t50\t0\nS2\t8\t0\t55\t1\nS3\t12\t1\t60\t0\nS4\t6\t1\t65\t1\n",
        encoding="utf-8",
    )
    rows = [
        {"sample_id": "S1", "OS_time": "5", "OS_event": "1", "age": "50", "marker": "0"},
        {"sample_id": "S2", "OS_time": "8", "OS_event": "0", "age": "55", "marker": "1"},
        {"sample_id": "S3", "OS_time": "12", "OS_event": "1", "age": "60", "marker": "0"},
        {"sample_id": "S4", "OS_time": "6", "OS_event": "1", "age": "65", "marker": "1"},
    ]
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    return package.to_dict(), build_clinical_association_preflight(rows)


def _complete_model_spec() -> dict[str, object]:
    return {
        "variables": ["age", "marker"],
        "training_validation": {"training_set": "training cohort", "validation_set": "holdout cohort"},
        "model_formula": "risk_score = beta_age * age + beta_marker * marker",
        "coefficient_source": {"source_result_id": "cox-mv-1", "source_manifest_path": "results/summaries/result_index.json"},
        "cutoff_strategy": {"policy": "predeclared_cutoff", "value": 0.5},
        "overfitting_protection": {"cross_validation": "5-fold", "external_validation": "holdout cohort"},
        "validation_plan": {"cross_validation": "5-fold", "external_validation": "holdout cohort", "external_validation_required": True},
        "missingness_policy": {"policy": "block_missing_required_variables"},
        "scaling_policy": {"policy": "use_training_cohort_parameters"},
        "calibration_plan": {"policy": "calibration_curve_on_validation_cohort"},
        "nomogram_policy": {"policy": "disabled_until_renderer_gate"},
    }


def _source_cox_result() -> dict[str, object]:
    return {
        "result_id": "cox-mv-1",
        "task_type": "cox_multivariate",
        "result_semantics": "formal_computed_result",
        "validation_status": "passed",
        "blockers": [],
        "dependency_snapshot": {"status": "passed", "python_lifelines": {"available": True}},
        "parameters_manifest": {"selected_covariates": ["age", "marker"], "survival_clinical_input_id": "pkg"},
        "log_artifacts": [{"artifact_type": "task_run_log", "path": "analysis/cox_mv/log.json"}],
        "output_artifacts": [{"artifact_type": "cox_multivariate_result_table", "path": "results/tables/cox_mv.tsv"}],
    }
