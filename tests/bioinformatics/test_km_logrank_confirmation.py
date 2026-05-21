from __future__ import annotations

from pathlib import Path

from app.bioinformatics.clinical_analysis import build_survival_package
from app.bioinformatics.survival_clinical import build_km_logrank_parameter_manifest, confirm_km_logrank_parameters, validate_km_logrank_confirmation


def test_km_parameter_confirmation_requires_matching_manifest(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("sample_id\tOS_time\tOS_event\tarm\nS1\t1\t1\tA\nS2\t2\t1\tA\nS3\t3\t1\tB\nS4\t4\t1\tB\n", encoding="utf-8")
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    manifest = build_km_logrank_parameter_manifest(package, outcome_gate={"status": "passed", "blockers": []}, grouping_variable="arm", group_a="A", group_b="B", dependency_snapshot={"status": "passed", "python_lifelines": {"available": True}})

    confirmation = confirm_km_logrank_parameters(tmp_path, manifest)

    assert confirmation["status"] == "confirmed"
    assert validate_km_logrank_confirmation(confirmation, manifest)["status"] == "passed"
    changed = dict(manifest)
    changed["group_b"] = "C"
    assert "km_logrank_confirmation_manifest_mismatch" in validate_km_logrank_confirmation(confirmation, changed)["blockers"]
