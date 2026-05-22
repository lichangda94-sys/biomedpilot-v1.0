from __future__ import annotations

from pathlib import Path

from app.bioinformatics.clinical_analysis import build_clinical_association_preflight, build_survival_package
from app.bioinformatics.survival_clinical import audit_risk_score_design


def test_risk_score_design_audit_ready_but_never_executable(tmp_path: Path) -> None:
    package, audit = _package_and_audit(tmp_path)
    design = audit_risk_score_design(package, audit, model_spec=_complete_model_spec())

    assert design["status"] == "design_audit_ready"
    assert design["formal_execution_enabled"] is False
    assert design["writes_result_index"] is False
    assert design["result_semantics"] == "design_audit_only"
    assert design["report_ready_eligible"] is False
    assert "risk_score_result" in design["forbidden_outputs"]
    assert design["interpretation_boundary"]["clinical_conclusion_forbidden"] is True


def test_risk_score_design_blocks_missing_prerequisites(tmp_path: Path) -> None:
    package, audit = _package_and_audit(tmp_path)
    design = audit_risk_score_design(package, audit, model_spec={"variables": ["age"]})

    assert design["status"] == "blocked"
    for blocker in (
        "training_validation_plan_missing",
        "model_formula_missing",
        "coefficient_source_missing",
        "cutoff_strategy_missing",
        "overfitting_protection_missing",
        "risk_score_validation_plan_missing",
    ):
        assert blocker in design["blockers"]


def test_risk_score_design_blocks_unknown_variable_and_non_cox_source(tmp_path: Path) -> None:
    package, audit = _package_and_audit(tmp_path)
    spec = _complete_model_spec()
    spec["variables"] = ["age", "missing_marker"]

    design = audit_risk_score_design(package, audit, model_spec=spec, source_cox_result={"task_type": "cox_univariate", "result_semantics": "formal_computed_result"})

    assert "risk_score_variable_not_in_clinical_audit:missing_marker" in design["blockers"]
    assert "source_result_must_be_cox_multivariate" in design["blockers"]


def test_risk_score_design_audit_has_no_result_index_side_effect(tmp_path: Path) -> None:
    package, audit = _package_and_audit(tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    design = audit_risk_score_design(package, audit, model_spec=_complete_model_spec())

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert design["writes_result_index"] is False
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
        "overfitting_protection": {"cross_validation": "5-fold", "external_validation": ""},
        "validation_plan": {"cross_validation": "5-fold", "external_validation": ""},
    }
