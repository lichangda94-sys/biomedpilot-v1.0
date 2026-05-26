from __future__ import annotations

from pathlib import Path

from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result
from app.bioinformatics.survival_clinical import build_risk_score_plot_nomogram_gate


def test_risk_score_plot_nomogram_gate_is_planning_only_for_valid_formal_source(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    gate = build_risk_score_plot_nomogram_gate(tmp_path)

    assert gate["schema_version"] == "biomedpilot.risk_score_plot_nomogram_gate.v1"
    assert gate["status"] == "blocked_planning_only"
    assert gate["selected_result_id"] == "risk-1"
    assert "b37_risk_score_renderer_activation_required" in gate["blockers"]
    assert gate["formal_execution_enabled"] is False
    assert gate["writes_result_index"] is False
    assert gate["creates_plot_artifact"] is False
    assert gate["creates_report_artifact"] is False
    assert gate["report_ready_eligible"] is False
    artifact_types = {item["artifact_type"] for item in gate["planned_artifacts"]}
    assert {"risk_score_distribution_plot", "risk_score_nomogram", "risk_score_calibration_curve", "risk_score_decision_curve"} <= artifact_types
    assert "clinical_conclusion" in gate["forbidden_outputs"]
    assert not (tmp_path / "results" / "summaries" / "result_index.json.lock").exists()


def test_risk_score_plot_nomogram_gate_blocks_missing_or_invalid_source(tmp_path: Path) -> None:
    missing = build_risk_score_plot_nomogram_gate(tmp_path)
    assert "formal_risk_score_result_not_found" in missing["blockers"]

    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text("sample_id\tcase_id\trisk_score\nS1\tC1\t1.0\n", encoding="utf-8")
    _register_risk_score(tmp_path, table, dependency_status="blocked", report_ready=True)

    gate = build_risk_score_plot_nomogram_gate(tmp_path)

    assert "dependency_snapshot_not_passed" in gate["blockers"]
    assert "risk_score_source_must_not_be_report_ready" in gate["blockers"]
    assert "b37_risk_score_renderer_activation_required" in gate["blockers"]


def _register_risk_score(root: Path, table: Path, *, dependency_status: str = "passed", report_ready: bool = False) -> None:
    entry = ResultIndexEntry(
        result_id="risk-1",
        task_run_id="task-risk-1",
        task_type="risk_score",
        result_semantics="formal_computed_result",
        input_package_id="surv-1",
        source_dataset_id="surv-1",
        source_repository_manifest="B12 survival input package / B32 risk score contract gate",
        parameters_manifest={"status": "ready_for_parameter_confirmation"},
        engine_name="biomedpilot_controlled_risk_score",
        engine_version="0.1.0",
        dependency_snapshot={"status": dependency_status},
        output_artifacts=({"artifact_type": "risk_score_result_table", "path": str(table.relative_to(root))},),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=("risk_score_statistical_result_only",),
        log_artifacts=({"artifact_type": "task_run_log", "path": "analysis/risk/log.json"},),
        report_ready_eligible=report_ready,
    ).to_dict()
    entry["source_cox_multivariate_result_id"] = "cox-mv-1"
    entry["risk_score_parameter_confirmation"] = {"schema_version": "biomedpilot.risk_score_parameter_confirmation.v1"}
    register_result(root, entry)
