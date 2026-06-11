from __future__ import annotations

from pathlib import Path

from app.bioinformatics.clinical_analysis import build_survival_package
from app.bioinformatics.survival_clinical import build_cox_result_review, build_cox_univariate_parameter_manifest, confirm_cox_univariate_parameters, export_cox_review_table, run_controlled_cox_univariate


def test_cox_result_review_exports_table_and_guard_copy(tmp_path: Path) -> None:
    result = _run(tmp_path)

    review = build_cox_result_review(tmp_path, result["result_id"])

    assert review["status"] == "passed"
    assert review["hazard_ratio"] is not None
    assert "not a clinical prognosis conclusion" in review["guard_copy"]
    assert "Multivariate Cox is not performed" in review["guard_copy"]
    export = export_cox_review_table(tmp_path, result["result_id"], tmp_path / "cox_review.tsv")
    assert export["status"] == "passed"
    assert Path(export["path"]).read_text(encoding="utf-8").startswith("covariate\t")


def _run(tmp_path: Path) -> dict[str, object]:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tOS_time\tOS_event\tarm\n"
        "S1\t5\t1\tA\nS2\t8\t0\tA\nS3\t12\t1\tA\n"
        "S4\t6\t1\tB\nS5\t9\t0\tB\nS6\t15\t1\tB\n",
        encoding="utf-8",
    )
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    manifest = build_cox_univariate_parameter_manifest(package, outcome_gate={"status": "passed", "survival_outcome_gate_id": "outcome-1", "blockers": []}, covariate="arm", dependency_snapshot={"status": "passed", "python_lifelines": {"available": True, "version": "test"}})
    return run_controlled_cox_univariate(tmp_path, manifest, confirm_cox_univariate_parameters(tmp_path, manifest), allow_legacy_sidecar_execution=True)
