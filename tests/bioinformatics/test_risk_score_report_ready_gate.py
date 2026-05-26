from __future__ import annotations

from pathlib import Path

from app.bioinformatics.reports.survival_clinical import create_risk_score_report_ready_package, evaluate_risk_score_report_ready_gate
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import load_registry, register_result
from app.bioinformatics.survival_clinical import (
    create_risk_score_advanced_visualization_artifact,
    create_risk_score_calibration_decision_curve_plot_artifact,
    run_risk_score_calibration_decision_curve_statistics,
)


def test_risk_score_report_ready_gate_passes_after_b42_b44_b45_artifacts(tmp_path: Path) -> None:
    _register_risk_score(tmp_path)
    _create_b42_b44_b45_artifacts(tmp_path)

    gate = evaluate_risk_score_report_ready_gate(tmp_path, result_id="risk-1")

    assert gate["schema_version"] == "biomedpilot.risk_score_report_ready_gate.v1"
    assert gate["status"] == "eligible_for_risk_score_report_ready"
    assert gate["section_scope"] == "risk_score_validation_only"
    assert gate["package_creation_enabled"] is True
    assert gate["report_ready_eligible"] is False
    assert gate["clinical_boundary"].startswith("Statistical research section only")
    assert gate["diagnostics"]["risk_score_row_count"] == 2
    assert "risk_score_calibration_statistics_table" in gate["diagnostics"]["statistics_artifact_types"]
    assert "risk_score_decision_curve" in gate["diagnostics"]["plot_artifact_types"]

    package = create_risk_score_report_ready_package(tmp_path, result_id="risk-1")

    assert package["status"] == "risk_score_validation_only_report_ready_package_created"
    assert package["section_scope"] == "risk_score_validation_only"
    assert package["clinical_conclusion_enabled"] is False
    assert package["full_integrated_report_enabled"] is False
    package_path = Path(package["package_path"])
    assert (package_path / "risk_score_validation_report.md").is_file()
    assert (package_path / "README_limitations.md").is_file()
    assert (package_path / "tables" / "risk.tsv").is_file()
    assert (package_path / "manifests" / "gate_snapshot.json").is_file()
    assert (package_path / "manifests" / "plot_artifacts.json").is_file()
    assert (package_path / "provenance" / "provenance.json").is_file()
    markdown = (package_path / "risk_score_validation_report.md").read_text(encoding="utf-8")
    assert "not clinical advice" in markdown
    assert "No new risk score model" in markdown
    entry = load_registry(tmp_path)["results"][0]
    assert entry["report_ready_eligible"] is True
    assert entry["report_artifacts"][0]["artifact_type"] == "risk_score_report_ready_package"
    assert entry["report_artifacts"][0]["section_scope"] == "risk_score_validation_only"


def test_risk_score_report_ready_gate_blocks_missing_required_artifacts(tmp_path: Path) -> None:
    _register_risk_score(tmp_path)

    gate = evaluate_risk_score_report_ready_gate(tmp_path, result_id="risk-1")

    assert gate["status"] == "blocked"
    assert "missing_output_artifact:risk_score_calibration_statistics_table" in gate["blockers"]
    assert "missing_output_artifact:risk_score_decision_curve_statistics_table" in gate["blockers"]
    assert "risk_score_report_ready_requires_b42_nomogram_plot_artifact" in gate["blockers"]
    assert "risk_score_report_ready_requires_b45_calibration_plot_artifact_or_explicit_table_only_mode" in gate["blockers"]
    assert "risk_score_report_ready_requires_b45_decision_curve_plot_artifact_or_explicit_table_only_mode" in gate["blockers"]


def test_risk_score_report_ready_gate_table_only_still_requires_nomogram_and_statistics(tmp_path: Path) -> None:
    _register_risk_score(tmp_path)
    output = create_risk_score_advanced_visualization_artifact(tmp_path, preflight_config=_advanced_preflight_config())
    assert output["status"] == "passed"
    stats = run_risk_score_calibration_decision_curve_statistics(tmp_path, planning_config=_calibration_config(tmp_path))
    assert stats["status"] == "passed"

    gate = evaluate_risk_score_report_ready_gate(tmp_path, result_id="risk-1", allow_table_only_report=True)

    assert gate["status"] == "eligible_for_risk_score_report_ready"
    assert gate["allow_table_only_report"] is True
    assert "risk_score_report_ready_requires_b45_calibration_plot_artifact_or_explicit_table_only_mode" not in gate["blockers"]
    assert "risk_score_report_ready_requires_b45_decision_curve_plot_artifact_or_explicit_table_only_mode" not in gate["blockers"]


def _register_risk_score(root: Path) -> None:
    table = root / "results" / "tables" / "risk.tsv"
    log = root / "analysis" / "risk" / "log.json"
    _write(
        table,
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n"
        "S2\tC2\t-0.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
    )
    _write(log, "{}\n")
    entry = ResultIndexEntry(
        result_id="risk-1",
        task_run_id="task-risk-1",
        task_type="risk_score",
        result_semantics="formal_computed_result",
        input_package_id="surv-1",
        source_dataset_id="surv-1",
        source_repository_manifest="B12 survival input package / B32 risk score contract gate",
        parameters_manifest={"status": "passed"},
        engine_name="biomedpilot_controlled_risk_score",
        engine_version="0.1.0",
        dependency_snapshot={"status": "passed"},
        output_artifacts=({"artifact_type": "risk_score_result_table", "path": str(table.relative_to(root))},),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=("risk_score_statistical_result_only",),
        log_artifacts=({"artifact_type": "task_run_log", "path": str(log.relative_to(root))},),
        report_ready_eligible=False,
    ).to_dict()
    entry["source_cox_multivariate_result_id"] = "cox-mv-1"
    entry["risk_score_parameter_confirmation"] = {"schema_version": "biomedpilot.risk_score_parameter_confirmation.v1"}
    register_result(root, entry)


def _create_b42_b44_b45_artifacts(root: Path) -> None:
    nomogram = create_risk_score_advanced_visualization_artifact(root, preflight_config=_advanced_preflight_config())
    assert nomogram["status"] == "passed"
    stats = run_risk_score_calibration_decision_curve_statistics(root, planning_config=_calibration_config(root))
    assert stats["status"] == "passed"
    calibration = create_risk_score_calibration_decision_curve_plot_artifact(root, plot_type="risk_score_calibration_curve")
    decision = create_risk_score_calibration_decision_curve_plot_artifact(root, plot_type="risk_score_decision_curve")
    assert calibration["status"] == "passed"
    assert decision["status"] == "passed"


def _advanced_preflight_config() -> dict[str, object]:
    return {
        "time_horizon_days": 365,
        "outcome_mapping": {"time_field": "OS_time", "event_field": "OS_event", "event_positive_value": "1"},
        "event_count": 12,
        "minimum_event_count": 10,
        "threshold_probability_grid": [0.1, 0.2, 0.3],
        "clinical_boundary_acknowledged": True,
    }


def _calibration_config(root: Path) -> dict[str, object]:
    validation = root / "results" / "tables" / "validation_probability.tsv"
    _write(
        validation,
        "sample_id\tpredicted_probability\tOS_time\tOS_event\n"
        "S1\t0.80\t300\t1\n"
        "S2\t0.70\t310\t1\n"
        "S3\t0.20\t500\t0\n"
        "S4\t0.10\t620\t0\n",
    )
    return {
        **_advanced_preflight_config(),
        "validation_cohort_id": "validation-cohort-1",
        "validation_strategy": "held_out_validation",
        "predicted_probability": {"source": str(validation.relative_to(root)), "column": "predicted_probability", "scale": "0_to_1"},
        "observed_outcome_mapping": {"time_field": "OS_time", "event_field": "OS_event", "event_positive_value": "1"},
        "calibration_method": "grouped_observed_vs_predicted",
        "calibration_bins": 2,
        "bootstrap_or_resampling_policy": "none_controlled_fixture",
        "net_benefit_formula_policy": "standard_binary_outcome_net_benefit",
        "treat_all_none_baselines": True,
        "clinical_decision_boundary_acknowledged": True,
        "minimum_event_count": 2,
    }


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
