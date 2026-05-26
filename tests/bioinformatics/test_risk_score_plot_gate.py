from __future__ import annotations

from pathlib import Path

from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result
from app.bioinformatics.survival_clinical import (
    build_risk_score_advanced_visualization_artifact_gate,
    build_risk_score_advanced_visualization_planning_gate,
    build_risk_score_advanced_visualization_preflight_gate,
    build_risk_score_advanced_visualization_runtime_plan,
    build_risk_score_calibration_decision_curve_input_gate,
    build_risk_score_calibration_decision_curve_plot_artifact_gate,
    build_risk_score_calibration_decision_curve_statistics_gate,
    build_risk_score_plot_artifact_activation_gate,
    build_risk_score_plot_artifact_schema_candidate,
    build_risk_score_plot_nomogram_gate,
    check_risk_score_plot_renderer_dependencies,
    create_risk_score_advanced_visualization_artifact,
    create_risk_score_calibration_decision_curve_plot_artifact,
    create_risk_score_plot_artifact,
    run_risk_score_calibration_decision_curve_statistics,
    validate_risk_score_plot_artifact_schema,
)


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


def test_risk_score_plot_artifact_schema_gate_passes_for_builtin_distribution_source(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    gate = build_risk_score_plot_artifact_activation_gate(tmp_path)

    assert gate["schema_version"] == "biomedpilot.risk_score_plot_artifact_activation_gate.v1"
    assert gate["status"] == "passed"
    assert gate["source_ready_for_future_activation"] is True
    assert gate["selected_result_id"] == "risk-1"
    assert gate["artifact_schema_validation"]["status"] == "passed"
    assert gate["renderer_dependency_snapshot"]["status"] == "passed"
    assert gate["blockers"] == []
    assert gate["creates_plot_artifact"] is True
    assert gate["writes_result_index"] is True
    assert gate["report_ready_eligible"] is False


def test_risk_score_plot_artifact_execution_writes_svg_and_registers_plot_only(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n"
        "S2\tC2\t-0.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    output = create_risk_score_plot_artifact(tmp_path)

    assert output["status"] == "passed"
    assert output["report_ready_eligible"] is False
    artifact = output["plot_artifact"]
    assert artifact["plot_type"] == "risk_score_distribution_plot"
    assert artifact["plot_semantics"] == "formal_computed_result"
    assert artifact["plot_artifact_scope"] == "formal_risk_score_plot_artifact"
    assert artifact["image_artifacts"][0]["format"] == "svg"
    svg_path = Path(artifact["image_artifacts"][0]["path"])
    assert svg_path.is_file()
    svg = svg_path.read_text(encoding="utf-8")
    assert svg.startswith("<svg")
    assert "no risk group" in svg
    registry_text = (tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8")
    assert "risk_score_distribution_plot" in registry_text
    assert '"report_ready_eligible": false' in registry_text
    assert '"clinical_conclusion":' not in registry_text


def test_risk_score_plot_execution_blocks_nomogram_until_later_stage(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    output = create_risk_score_plot_artifact(tmp_path, plot_type="risk_score_nomogram")

    assert output["status"] == "blocked"
    assert "risk_score_plot_type_not_enabled_in_b38:risk_score_nomogram" in output["blockers"]
    assert output["plot_artifact"]["image_artifacts"] == []


def test_risk_score_advanced_visualization_gate_is_planning_only(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    gate = build_risk_score_advanced_visualization_planning_gate(tmp_path)

    assert gate["schema_version"] == "biomedpilot.risk_score_advanced_visualization_planning_gate.v1"
    assert gate["status"] == "blocked_planning_only"
    assert gate["selected_result_id"] == "risk-1"
    assert "b40_risk_score_advanced_visualization_activation_required" in gate["blockers"]
    assert gate["formal_execution_enabled"] is False
    assert gate["writes_result_index"] is False
    assert gate["creates_plot_artifact"] is False
    assert gate["creates_report_artifact"] is False
    assert gate["report_ready_eligible"] is False
    planned = {item["artifact_type"] for item in gate["planned_artifacts"]}
    assert planned == {"risk_score_nomogram", "risk_score_calibration_curve", "risk_score_decision_curve"}
    assert "decision_recommendation_forbidden" in gate["planned_artifacts"][2]["minimum_conditions"]


def test_risk_score_advanced_visualization_gate_blocks_missing_source(tmp_path: Path) -> None:
    gate = build_risk_score_advanced_visualization_planning_gate(tmp_path)

    assert gate["status"] == "blocked_planning_only"
    assert "formal_risk_score_result_not_found" in gate["blockers"]
    assert "b40_risk_score_advanced_visualization_activation_required" in gate["blockers"]


def test_risk_score_advanced_visualization_runtime_plan_is_non_executing(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    plan = build_risk_score_advanced_visualization_runtime_plan(tmp_path)

    assert plan["schema_version"] == "biomedpilot.risk_score_advanced_visualization_runtime_plan.v1"
    assert plan["status"] == "blocked_runtime_planning_only"
    assert plan["selected_result_id"] == "risk-1"
    assert plan["runtime_policy"]["renderer_detection"] == "detect_first_no_install_no_download"
    assert plan["validation_gates"]["low_event_count"] == "must_block_before_calibration_or_decision_curve"
    assert "b41_risk_score_advanced_visualization_execution_required" in plan["blockers"]
    assert plan["formal_execution_enabled"] is False
    assert plan["writes_result_index"] is False
    assert plan["creates_plot_artifact"] is False
    assert plan["report_ready_eligible"] is False
    plans = {item["artifact_type"]: item for item in plan["artifact_runtime_plans"]}
    assert plans["risk_score_nomogram"]["renderer_candidates"][0]["renderer"] == "r_rms_nomogram"
    assert "clinical_decision_recommendation_forbidden" in plans["risk_score_decision_curve"]["required_runtime_inputs"]


def test_risk_score_advanced_visualization_runtime_plan_blocks_missing_source(tmp_path: Path) -> None:
    plan = build_risk_score_advanced_visualization_runtime_plan(tmp_path)

    assert plan["status"] == "blocked_runtime_planning_only"
    assert "formal_risk_score_result_not_found" in plan["blockers"]
    assert "b41_risk_score_advanced_visualization_execution_required" in plan["blockers"]


def test_risk_score_advanced_visualization_preflight_passes_without_execution(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    gate = build_risk_score_advanced_visualization_preflight_gate(
        tmp_path,
        preflight_config={
            "time_horizon_days": 365,
            "outcome_mapping": {"time_field": "OS_time", "event_field": "OS_event", "event_positive_value": "1"},
            "event_count": 12,
            "minimum_event_count": 10,
            "threshold_probability_grid": [0.1, 0.2, 0.3],
            "clinical_boundary_acknowledged": True,
        },
    )

    assert gate["schema_version"] == "biomedpilot.risk_score_advanced_visualization_preflight_gate.v1"
    assert gate["status"] == "passed_preflight_only"
    assert gate["checks"]["time_horizon_present"] is True
    assert gate["checks"]["outcome_mapping_present"] is True
    assert gate["checks"]["minimum_event_count_met"] is True
    assert gate["checks"]["threshold_grid_valid"] is True
    assert gate["checks"]["clinical_boundary_acknowledged"] is True
    assert gate["formal_execution_enabled"] is False
    assert gate["writes_result_index"] is False
    assert gate["creates_plot_artifact"] is False
    assert gate["report_ready_eligible"] is False


def test_risk_score_advanced_visualization_preflight_blocks_invalid_inputs(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    gate = build_risk_score_advanced_visualization_preflight_gate(
        tmp_path,
        preflight_config={
            "time_horizon_days": 0,
            "outcome_mapping": {"time_field": "", "event_field": ""},
            "event_count": 2,
            "minimum_event_count": 10,
            "threshold_probability_grid": [0.5, 0.2, 1.1],
            "clinical_boundary_acknowledged": False,
        },
    )

    assert gate["status"] == "blocked"
    assert "time_horizon_invalid" in gate["blockers"]
    assert "outcome_time_field_missing" in gate["blockers"]
    assert "outcome_event_field_missing" in gate["blockers"]
    assert "minimum_event_count_not_met_for_advanced_visualization" in gate["blockers"]
    assert "threshold_probability_grid_invalid" in gate["blockers"]
    assert "clinical_boundary_acknowledgement_missing" in gate["blockers"]


def test_risk_score_advanced_visualization_artifact_gate_allows_nomogram_only_after_preflight(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n"
        "S2\tC2\t-0.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    config = _advanced_preflight_config()
    gate = build_risk_score_advanced_visualization_artifact_gate(tmp_path, preflight_config=config)

    assert gate["schema_version"] == "biomedpilot.risk_score_advanced_visualization_artifact_gate.v1"
    assert gate["status"] == "passed"
    assert gate["plot_type"] == "risk_score_nomogram"
    assert gate["creates_plot_artifact"] is True
    assert gate["writes_result_index"] is True
    assert gate["report_ready_eligible"] is False
    assert gate["blocked_future_plot_types"] == ["risk_score_calibration_curve", "risk_score_decision_curve"]

    blocked = build_risk_score_advanced_visualization_artifact_gate(tmp_path, plot_type="risk_score_calibration_curve", preflight_config=config)
    assert blocked["status"] == "blocked"
    assert "risk_score_advanced_plot_type_not_enabled_in_b42:risk_score_calibration_curve" in blocked["blockers"]


def test_risk_score_advanced_visualization_artifact_execution_registers_nomogram_svg_only(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n"
        "S2\tC2\t-0.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    output = create_risk_score_advanced_visualization_artifact(tmp_path, preflight_config=_advanced_preflight_config())

    assert output["status"] == "passed"
    assert output["report_ready_eligible"] is False
    artifact = output["plot_artifact"]
    assert artifact["plot_type"] == "risk_score_nomogram"
    assert artifact["plot_semantics"] == "formal_computed_result"
    assert artifact["plot_artifact_scope"] == "formal_risk_score_plot_artifact"
    svg_path = Path(artifact["image_artifacts"][0]["path"])
    assert svg_path.is_file()
    svg = svg_path.read_text(encoding="utf-8")
    assert svg.startswith("<svg")
    assert "nomogram scale audit" in svg
    assert "No high/low-risk group" in svg
    registry_text = (tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8")
    assert "risk_score_nomogram" in registry_text
    assert '"report_ready_eligible": false' in registry_text
    assert '"clinical_conclusion":' not in registry_text


def test_risk_score_calibration_decision_curve_input_gate_is_review_only_when_inputs_ready(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n"
        "S2\tC2\t-0.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    gate = build_risk_score_calibration_decision_curve_input_gate(tmp_path, planning_config=_calibration_decision_curve_config())

    assert gate["schema_version"] == "biomedpilot.risk_score_calibration_decision_curve_input_gate.v1"
    assert gate["status"] == "ready_for_future_artifact_gate"
    assert gate["checks"]["calibration_inputs_ready"] is True
    assert gate["checks"]["decision_curve_inputs_ready"] is True
    assert gate["future_artifact_types"] == ["risk_score_calibration_curve", "risk_score_decision_curve"]
    assert gate["formal_execution_enabled"] is False
    assert gate["writes_result_index"] is False
    assert gate["creates_plot_artifact"] is False
    assert gate["report_ready_eligible"] is False
    assert not (tmp_path / "results" / "plots" / "risk_score" / "advanced").exists()


def test_risk_score_calibration_decision_curve_input_gate_blocks_fake_or_missing_inputs(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    gate = build_risk_score_calibration_decision_curve_input_gate(
        tmp_path,
        planning_config={
            **_advanced_preflight_config(),
            "validation_cohort_id": "",
            "validation_strategy": "",
            "predicted_probability": {"source": "", "column": "", "scale": "percent"},
            "observed_outcome_mapping": {"time_field": "", "event_field": ""},
            "calibration_method": "",
            "calibration_bins": 1,
            "bootstrap_or_resampling_policy": "",
            "net_benefit_formula_policy": "",
            "treat_all_none_baselines": False,
            "clinical_decision_boundary_acknowledged": False,
        },
    )

    assert gate["status"] == "blocked_planning_only"
    assert "validation_cohort_missing" in gate["blockers"]
    assert "calibration_validation_strategy_missing" in gate["blockers"]
    assert "predicted_probability_source_missing" in gate["blockers"]
    assert "predicted_probability_column_missing" in gate["blockers"]
    assert "predicted_probability_scale_invalid" in gate["blockers"]
    assert "observed_outcome_mapping_missing" in gate["blockers"]
    assert "calibration_method_missing" in gate["blockers"]
    assert "calibration_bins_invalid" in gate["blockers"]
    assert "calibration_resampling_policy_missing" in gate["blockers"]
    assert "net_benefit_formula_policy_missing" in gate["blockers"]
    assert "decision_curve_treat_all_none_baselines_missing" in gate["blockers"]
    assert "clinical_decision_boundary_acknowledgement_missing" in gate["blockers"]


def test_risk_score_calibration_decision_curve_statistics_gate_blocks_missing_probability_table(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    gate = build_risk_score_calibration_decision_curve_statistics_gate(tmp_path, planning_config=_calibration_decision_curve_config())

    assert gate["schema_version"] == "biomedpilot.risk_score_calibration_decision_curve_statistics_gate.v1"
    assert gate["status"] == "blocked"
    assert "validation_probability_table_missing_or_empty" in gate["blockers"]
    assert gate["creates_plot_artifact"] is False
    assert gate["report_ready_eligible"] is False


def test_risk_score_calibration_decision_curve_statistics_execution_writes_tables_only(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n"
        "S2\tC2\t-0.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    validation = tmp_path / "results" / "tables" / "validation_probability.tsv"
    validation.write_text(
        "sample_id\tpredicted_probability\tOS_time\tOS_event\n"
        "S1\t0.80\t300\t1\n"
        "S2\t0.70\t310\t1\n"
        "S3\t0.20\t500\t0\n"
        "S4\t0.10\t620\t0\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    output = run_risk_score_calibration_decision_curve_statistics(
        tmp_path,
        planning_config={**_calibration_decision_curve_config(), "predicted_probability": {"source": str(validation.relative_to(tmp_path)), "column": "predicted_probability", "scale": "0_to_1"}, "calibration_bins": 2, "minimum_event_count": 2},
    )

    assert output["status"] == "passed"
    assert output["report_ready_eligible"] is False
    artifact_types = {artifact["artifact_type"] for artifact in output["statistics_artifacts"]}
    assert "risk_score_calibration_statistics_table" in artifact_types
    assert "risk_score_decision_curve_statistics_table" in artifact_types
    assert output["calibration_rows"][0]["n"] == 2
    assert output["decision_curve_rows"][0]["threshold_probability"] == "0.1"
    registry_text = (tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8")
    assert "risk_score_calibration_statistics_table" in registry_text
    assert "risk_score_decision_curve_statistics_table" in registry_text
    assert "risk_score_calibration_curve_svg" not in registry_text
    assert '"report_ready_eligible": false' in registry_text


def test_risk_score_calibration_decision_curve_plot_gate_requires_b44_statistics_tables(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)

    gate = build_risk_score_calibration_decision_curve_plot_artifact_gate(tmp_path)

    assert gate["schema_version"] == "biomedpilot.risk_score_calibration_decision_curve_plot_gate.v1"
    assert gate["status"] == "blocked"
    assert "risk_score_calibration_statistics_table_missing" in gate["blockers"]
    assert "risk_score_decision_curve_statistics_table_missing" in gate["blockers"]
    assert gate["creates_plot_artifact"] is False
    assert gate["report_ready_eligible"] is False


def test_risk_score_calibration_decision_curve_plot_artifacts_register_from_b44_tables_only(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "risk.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "sample_id\tcase_id\trisk_score\tsource_cox_multivariate_result_id\tmodel_formula\tcoefficient_source\tmissingness_policy\tscaling_policy\twarnings\n"
        "S1\tC1\t1.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n"
        "S2\tC2\t-0.5\tcox-mv-1\tformula\tcox-mv-1\tblock\tas_is\tstatistical_result_only\n",
        encoding="utf-8",
    )
    validation = tmp_path / "results" / "tables" / "validation_probability.tsv"
    validation.write_text(
        "sample_id\tpredicted_probability\tOS_time\tOS_event\n"
        "S1\t0.80\t300\t1\n"
        "S2\t0.70\t310\t1\n"
        "S3\t0.20\t500\t0\n"
        "S4\t0.10\t620\t0\n",
        encoding="utf-8",
    )
    _register_risk_score(tmp_path, table)
    config = {**_calibration_decision_curve_config(), "predicted_probability": {"source": str(validation.relative_to(tmp_path)), "column": "predicted_probability", "scale": "0_to_1"}, "calibration_bins": 2, "minimum_event_count": 2}
    stats = run_risk_score_calibration_decision_curve_statistics(tmp_path, planning_config=config)
    assert stats["status"] == "passed"

    calibration = create_risk_score_calibration_decision_curve_plot_artifact(tmp_path, plot_type="risk_score_calibration_curve")
    decision = create_risk_score_calibration_decision_curve_plot_artifact(tmp_path, plot_type="risk_score_decision_curve")

    assert calibration["status"] == "passed"
    assert decision["status"] == "passed"
    assert calibration["report_ready_eligible"] is False
    assert decision["report_ready_eligible"] is False
    assert calibration["plot_artifact"]["plot_type"] == "risk_score_calibration_curve"
    assert decision["plot_artifact"]["plot_type"] == "risk_score_decision_curve"
    assert calibration["plot_artifact"]["plot_semantics"] == "formal_computed_result"
    assert decision["plot_artifact"]["plot_semantics"] == "formal_computed_result"
    assert Path(calibration["plot_artifact"]["image_artifacts"][0]["path"]).read_text(encoding="utf-8").startswith("<svg")
    assert Path(decision["plot_artifact"]["image_artifacts"][0]["path"]).read_text(encoding="utf-8").startswith("<svg")
    registry_text = (tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8")
    assert "risk_score_calibration_curve" in registry_text
    assert "risk_score_decision_curve" in registry_text
    assert "source_statistics_stage" in registry_text
    assert '"report_ready_eligible": false' in registry_text
    assert '"clinical_conclusion":' not in registry_text


def test_risk_score_plot_artifact_schema_blocks_nonformal_and_clinical_fields(tmp_path: Path) -> None:
    dependency = check_risk_score_plot_renderer_dependencies()
    artifact = build_risk_score_plot_artifact_schema_candidate(
        {
            "result_id": "risk-2",
            "task_type": "risk_score",
            "result_semantics": "imported_external_result",
            "input_package_id": "pkg",
            "task_run_id": "task",
            "parameters_manifest": {"status": "confirmed"},
            "output_artifacts": [{"artifact_type": "risk_score_result_table", "path": "results/tables/risk.tsv"}],
        },
        plot_type="risk_score_distribution_plot",
        renderer="builtin_svg",
        dependency_snapshot=dependency,
    )
    artifact["plot_parameters"]["clinical_conclusion"] = "poor prognosis"

    validation = validate_risk_score_plot_artifact_schema(artifact)

    assert validation["status"] == "blocked"
    assert "risk_score_plot_requires_formal_computed_result_source" in validation["blockers"]
    assert "forbidden_risk_score_plot_field:plot_parameters.clinical_conclusion" in validation["blockers"]


def test_risk_score_plot_renderer_detection_is_detect_first(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.bioinformatics.survival_clinical.risk_score_plot_schema.importlib.util.find_spec", lambda name: None if name == "matplotlib" else object())

    dependency = check_risk_score_plot_renderer_dependencies(renderer="matplotlib_png")
    missing = build_risk_score_plot_artifact_activation_gate(tmp_path, renderer="matplotlib_png")

    assert dependency["status"] == "blocked"
    assert dependency["install_action"] == "none_detect_first_only"
    assert "matplotlib_missing_for_risk_score_plot_renderer" in dependency["blockers"]
    assert "matplotlib_missing_for_risk_score_plot_renderer" in missing["blockers"]


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


def _advanced_preflight_config() -> dict[str, object]:
    return {
        "time_horizon_days": 365,
        "outcome_mapping": {"time_field": "OS_time", "event_field": "OS_event", "event_positive_value": "1"},
        "event_count": 12,
        "minimum_event_count": 10,
        "threshold_probability_grid": [0.1, 0.2, 0.3],
        "clinical_boundary_acknowledged": True,
    }


def _calibration_decision_curve_config() -> dict[str, object]:
    return {
        **_advanced_preflight_config(),
        "validation_cohort_id": "validation-cohort-1",
        "validation_strategy": "held_out_validation",
        "predicted_probability": {"source": "risk_score_probability_table", "column": "predicted_probability", "scale": "0_to_1"},
        "observed_outcome_mapping": {"time_field": "OS_time", "event_field": "OS_event", "event_positive_value": "1"},
        "calibration_method": "grouped_observed_vs_predicted",
        "calibration_bins": 4,
        "bootstrap_or_resampling_policy": "none_controlled_fixture",
        "net_benefit_formula_policy": "standard_binary_outcome_net_benefit",
        "treat_all_none_baselines": True,
        "clinical_decision_boundary_acknowledged": True,
    }
