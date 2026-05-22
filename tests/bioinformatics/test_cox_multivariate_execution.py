from __future__ import annotations

from pathlib import Path

from app.bioinformatics.clinical_analysis import build_clinical_association_preflight, build_survival_package
from app.bioinformatics.survival_clinical import build_cox_multivariate_parameter_manifest, confirm_cox_multivariate_parameters, run_controlled_cox_multivariate


def test_controlled_cox_multivariate_registers_formal_result_without_risk_score(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    confirmation = confirm_cox_multivariate_parameters(tmp_path, manifest)

    result = run_controlled_cox_multivariate(tmp_path, manifest, confirmation)

    assert result["status"] == "passed"
    table = Path(result["cox_result_table"]).read_text(encoding="utf-8")
    assert "hazard_ratio" in table
    assert "ci_lower" in table
    assert "p_value" in table
    assert "adjusted_for" in table
    assert "risk_score" not in table
    index = (tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8")
    assert "formal_computed_result" in index
    assert "cox_multivariate" in index
    assert '"plot_artifacts": []' in index
    assert '"report_artifacts": []' in index
    assert '"report_ready_eligible": false' in index
    assert "clinical_risk_group" not in index
    assert "treatment_recommendation" not in index


def test_controlled_cox_multivariate_blocks_missing_confirmation_without_result_index(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)

    result = run_controlled_cox_multivariate(tmp_path, manifest, {})

    assert result["status"] == "blocked"
    assert "cox_multivariate_parameter_confirmation_missing" in result["blockers"]
    assert Path(result["task_run_log_path"]).is_file()
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def _manifest(tmp_path: Path) -> dict[str, object]:
    clinical = tmp_path / "clinical.tsv"
    lines = ["sample_id\tOS_time\tOS_event\tage\tmarker"]
    for index in range(24):
        event = "0" if index in {3, 8, 15, 22} else "1"
        marker = str(index % 2)
        lines.append(f"S{index + 1}\t{5 + index}\t{event}\t{40 + index}\t{marker}")
    clinical.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rows = [dict(zip(lines[0].split("\t"), line.split("\t"), strict=False)) for line in lines[1:]]
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    audit = build_clinical_association_preflight(rows)
    return build_cox_multivariate_parameter_manifest(
        package,
        outcome_gate={"status": "passed", "survival_outcome_gate_id": "outcome-1", "blockers": []},
        clinical_variable_audit=audit,
        selected_covariates=["age", "marker"],
        dependency_snapshot={"status": "passed", "python_lifelines": {"available": True, "version": "test"}},
    )
