from __future__ import annotations

import math
from pathlib import Path

from app.bioinformatics.survival_clinical import confirm_risk_score_parameters, run_controlled_risk_score


def test_controlled_risk_score_registers_formal_table_only_result(tmp_path: Path) -> None:
    contract = _ready_contract(tmp_path)
    confirmation = confirm_risk_score_parameters(tmp_path, contract)

    result = run_controlled_risk_score(tmp_path, contract, confirmation)

    assert result["status"] == "passed"
    table = Path(result["risk_score_result_table"]).read_text(encoding="utf-8")
    assert "risk_score" in table
    assert "risk_group" not in table
    assert "clinical_conclusion" not in table
    assert "treatment_recommendation" not in table
    first_score = float(table.splitlines()[1].split("\t")[2])
    assert math.isclose(first_score, math.log(1.1) * 50 + math.log(2.0) * 0, rel_tol=1e-6)
    index = (tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8")
    assert "formal_computed_result" in index
    assert '"task_type": "risk_score"' in index
    assert '"plot_artifacts": []' in index
    assert '"report_artifacts": []' in index
    assert '"report_ready_eligible": false' in index
    assert '"artifact_type": "nomogram"' not in index
    assert '"clinical_risk_group":' not in index


def test_controlled_risk_score_blocks_missing_confirmation_without_result_index(tmp_path: Path) -> None:
    contract = _ready_contract(tmp_path)

    result = run_controlled_risk_score(tmp_path, contract, {})

    assert result["status"] == "blocked"
    assert "risk_score_parameter_confirmation_missing" in result["blockers"]
    assert Path(result["task_run_log_path"]).is_file()
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def test_controlled_risk_score_blocks_missing_source_coefficient(tmp_path: Path) -> None:
    contract = _ready_contract(tmp_path)
    cox_table = tmp_path / "results" / "tables" / "cox_mv.tsv"
    cox_table.write_text("covariate\thazard_ratio\nage\t1.1\n", encoding="utf-8")
    confirmation = confirm_risk_score_parameters(tmp_path, contract)

    result = run_controlled_risk_score(tmp_path, contract, confirmation)

    assert result["status"] == "blocked"
    assert "missing_cox_coefficient:marker" in result["blockers"]


def _ready_contract(tmp_path: Path) -> dict[str, object]:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tcase_id\tOS_time\tOS_event\tage\tmarker\n"
        "S1\tC1\t5\t1\t50\t0\n"
        "S2\tC2\t8\t0\t55\t1\n"
        "S3\tC3\t12\t1\t60\t0\n",
        encoding="utf-8",
    )
    cox_table = tmp_path / "results" / "tables" / "cox_mv.tsv"
    cox_table.parent.mkdir(parents=True)
    cox_table.write_text(
        "covariate\thazard_ratio\tp_value\n"
        "age\t1.1\t0.02\n"
        "marker\t2.0\t0.03\n",
        encoding="utf-8",
    )
    source_parameters = {
        "status": "passed",
        "selected_covariates": ["age", "marker"],
        "covariate_specs": {
            "age": {"variable_type": "continuous_variable"},
            "marker": {"variable_type": "binary_variable"},
        },
        "provenance": {"clinical_asset_path": str(clinical)},
    }
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
        "scaling_policy": {"policy": "use_cox_model_original_covariate_encoding"},
        "calibration_plan": {"policy": "calibration_curve_on_validation_cohort"},
        "nomogram_policy": {"policy": "disabled_until_renderer_gate"},
        "validation_plan": {"cross_validation": "5-fold", "external_validation": "holdout cohort"},
        "source_result_dependency_snapshot": {"status": "passed", "python_lifelines": {"available": True}},
        "source_result_parameters_manifest": source_parameters,
        "source_result_output_artifacts": [{"artifact_type": "cox_multivariate_result_table", "path": str(cox_table)}],
        "source_result_log_artifacts": [{"artifact_type": "task_run_log", "path": "analysis/cox/log.json"}],
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
