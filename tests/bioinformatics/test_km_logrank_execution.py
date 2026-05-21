from __future__ import annotations

from pathlib import Path

from app.bioinformatics.clinical_analysis import build_survival_package
from app.bioinformatics.survival_clinical import build_km_logrank_parameter_manifest, confirm_km_logrank_parameters, run_controlled_km_logrank


def test_controlled_km_logrank_registers_formal_result_without_hr_or_report(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    confirmation = confirm_km_logrank_parameters(tmp_path, manifest)

    result = run_controlled_km_logrank(tmp_path, manifest, confirmation)

    assert result["status"] == "passed"
    assert Path(result["km_curve_table"]).is_file()
    assert Path(result["logrank_result_table"]).is_file()
    table = Path(result["logrank_result_table"]).read_text(encoding="utf-8")
    assert "p_value" in table
    assert "hazard_ratio" not in table
    index = (tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8")
    assert "formal_computed_result" in index
    assert "survival_km_logrank" in index
    assert '"plot_artifacts": []' in index
    assert '"report_artifacts": []' in index
    assert '"report_ready_eligible": false' in index


def test_controlled_km_logrank_blocks_missing_confirmation_without_traceback(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    result = run_controlled_km_logrank(tmp_path, manifest, {})

    assert result["status"] == "blocked"
    assert "km_logrank_parameter_confirmation_missing" in result["blockers"]
    assert Path(result["task_run_log_path"]).is_file()


def _manifest(tmp_path: Path) -> dict[str, object]:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tOS_time\tOS_event\tarm\n"
        "S1\t5\t1\tA\nS2\t8\t0\tA\nS3\t12\t1\tA\n"
        "S4\t6\t1\tB\nS5\t9\t0\tB\nS6\t15\t1\tB\n",
        encoding="utf-8",
    )
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    return build_km_logrank_parameter_manifest(package, outcome_gate={"status": "passed", "survival_outcome_gate_id": "outcome-1", "blockers": []}, grouping_variable="arm", group_a="A", group_b="B", dependency_snapshot={"status": "passed", "python_lifelines": {"available": True, "version": "test"}})
