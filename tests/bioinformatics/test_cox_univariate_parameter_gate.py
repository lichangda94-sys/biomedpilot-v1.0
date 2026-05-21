from __future__ import annotations

from pathlib import Path

from app.bioinformatics.clinical_analysis import build_clinical_association_preflight, build_survival_package
from app.bioinformatics.survival_clinical import build_cox_univariate_parameter_manifest


def test_cox_parameter_gate_passes_valid_binary_covariate(tmp_path: Path) -> None:
    clinical = _clinical_fixture(tmp_path)
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    audit = build_clinical_association_preflight(_rows())

    manifest = build_cox_univariate_parameter_manifest(package, outcome_gate=_outcome_gate(), clinical_variable_audit=audit, covariate="arm", dependency_snapshot=_dependency_passed())

    assert manifest["status"] == "passed"
    assert manifest["covariate"] == "arm"
    assert manifest["covariate_type"] == "categorical_variable"
    assert manifest["event_count"] == 4
    assert manifest["non_missing_count"] == 6
    assert "single_variable_model_only" in manifest["warnings"]
    assert manifest["provenance"]["raw_recognition_report_used"] is False


def test_cox_parameter_gate_blocks_identifier_constant_and_missing_dependency(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("sample_id\tOS_time\tOS_event\tcase_id\nS1\t1\t1\tC1\nS2\t2\t1\tC2\nS3\t3\t0\tC3\nS4\t4\t1\tC4\n", encoding="utf-8")
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})

    manifest = build_cox_univariate_parameter_manifest(package, outcome_gate=_outcome_gate(), covariate="case_id", dependency_snapshot={"status": "preflight_only"})

    assert "identifier_not_allowed_as_covariate" in manifest["blockers"]
    assert "dependency_snapshot_not_passed" in manifest["blockers"]


def test_cox_parameter_gate_blocks_too_many_categories_and_low_events(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("sample_id\tOS_time\tOS_event\tstage\nS1\t1\t1\tI\nS2\t2\t0\tII\nS3\t3\t0\tIII\nS4\t4\t0\tIV\n", encoding="utf-8")
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    audit = build_clinical_association_preflight([
        {"stage": "I"}, {"stage": "II"}, {"stage": "III"}, {"stage": "IV"}
    ])

    manifest = build_cox_univariate_parameter_manifest(package, outcome_gate=_outcome_gate(), clinical_variable_audit=audit, covariate="stage", dependency_snapshot=_dependency_passed())

    assert "minimum_event_count_not_met" in manifest["blockers"]
    assert "too_many_categories" in manifest["blockers"]


def _clinical_fixture(tmp_path: Path) -> Path:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tOS_time\tOS_event\tarm\tage\n"
        "S1\t5\t1\tA\t50\nS2\t8\t0\tA\t55\nS3\t12\t1\tA\t60\n"
        "S4\t6\t1\tB\t65\nS5\t9\t0\tB\t70\nS6\t15\t1\tB\t75\n",
        encoding="utf-8",
    )
    return clinical


def _rows() -> list[dict[str, str]]:
    return [{"arm": "A", "age": "50"}, {"arm": "B", "age": "60"}]


def _outcome_gate() -> dict[str, object]:
    return {"status": "passed", "survival_outcome_gate_id": "outcome-1", "blockers": [], "warnings": []}


def _dependency_passed() -> dict[str, object]:
    return {"status": "passed", "python_lifelines": {"available": True, "version": "test"}, "blockers": [], "warnings": []}
