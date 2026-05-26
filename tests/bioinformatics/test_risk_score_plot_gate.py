from __future__ import annotations

from pathlib import Path

from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result
from app.bioinformatics.survival_clinical import (
    build_risk_score_advanced_visualization_planning_gate,
    build_risk_score_plot_artifact_activation_gate,
    build_risk_score_plot_artifact_schema_candidate,
    build_risk_score_plot_nomogram_gate,
    check_risk_score_plot_renderer_dependencies,
    create_risk_score_plot_artifact,
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
