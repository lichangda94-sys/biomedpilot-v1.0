from __future__ import annotations

from pathlib import Path

from app.bioinformatics.clinical_analysis import build_survival_package
from app.bioinformatics.survival_clinical import build_cox_univariate_parameter_manifest, confirm_cox_univariate_parameters, validate_cox_univariate_confirmation


def test_cox_confirmation_requires_matching_manifest(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("sample_id\tOS_time\tOS_event\tarm\nS1\t1\t1\tA\nS2\t2\t1\tA\nS3\t3\t1\tB\nS4\t4\t1\tB\n", encoding="utf-8")
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    manifest = build_cox_univariate_parameter_manifest(package, outcome_gate={"status": "passed", "blockers": []}, covariate="arm", dependency_snapshot={"status": "passed", "python_lifelines": {"available": True}})

    confirmation = confirm_cox_univariate_parameters(tmp_path, manifest)

    assert confirmation["status"] == "confirmed"
    assert validate_cox_univariate_confirmation(confirmation, manifest)["status"] == "passed"
    changed = dict(manifest)
    changed["covariate"] = "age"
    assert "cox_univariate_confirmation_manifest_mismatch" in validate_cox_univariate_confirmation(confirmation, changed)["blockers"]
