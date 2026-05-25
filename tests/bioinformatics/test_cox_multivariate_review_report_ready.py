from __future__ import annotations

from pathlib import Path

from app.bioinformatics.reports.integrated import evaluate_full_integrated_report_gate
from app.bioinformatics.reports.survival_clinical import create_cox_report_ready_package, evaluate_cox_report_ready_gate
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import load_registry, save_registry
from app.bioinformatics.survival_clinical import build_cox_multivariate_result_review, export_cox_multivariate_review_table


def test_cox_multivariate_review_summarizes_adjusted_covariates_and_exports_table(tmp_path: Path) -> None:
    save_registry(tmp_path, [_cox_multivariate_entry(tmp_path)])

    review = build_cox_multivariate_result_review(tmp_path, "cox-mv-ready")
    exported = export_cox_multivariate_review_table(tmp_path, "cox-mv-ready", tmp_path / "exports" / "cox_mv.tsv")

    assert review["status"] == "passed"
    assert review["covariate_count"] == 2
    assert review["significant_covariate_count"] == 1
    assert "not a clinical" in review["guard_copy"]
    assert "risk_score_not_generated" in review["warnings"]
    assert exported["status"] == "passed"
    assert Path(exported["path"]).is_file()
    assert "risk_score" not in Path(exported["path"]).read_text(encoding="utf-8")


def test_cox_multivariate_report_ready_gate_and_package_are_section_only(tmp_path: Path) -> None:
    save_registry(tmp_path, [_cox_multivariate_entry(tmp_path)])

    gate = evaluate_cox_report_ready_gate(tmp_path, result_id="cox-mv-ready")
    package = create_cox_report_ready_package(tmp_path, result_id="cox-mv-ready")

    assert gate["status"] == "eligible_for_cox_report_ready"
    assert gate["schema_version"] == "biomedpilot.cox_multivariate_report_ready_gate.v1"
    assert gate["section_scope"] == "cox_multivariate_only"
    assert gate["diagnostics"]["covariate_count"] == 2
    assert package["status"] == "cox_multivariate_only_report_ready_package_created"
    assert package["section_scope"] == "cox_multivariate_only"
    package_path = Path(package["package_path"])
    assert (package_path / "cox_multivariate_report.md").is_file()
    assert (package_path / "tables" / "cox_mv.tsv").is_file()
    assert (package_path / "manifests" / "gate_snapshot.json").is_file()
    assert package["clinical_conclusion_enabled"] is False
    assert package["full_integrated_report_enabled"] is False
    assert "risk score" in (package_path / "cox_multivariate_report.md").read_text(encoding="utf-8")
    entry = load_registry(tmp_path)["results"][0]
    assert entry["report_ready_eligible"] is True
    assert entry["report_artifacts"][0]["section_scope"] == "cox_multivariate_only"
    assert entry["report_artifacts"][0]["artifact_type"] == "cox_multivariate_report_ready_package"

    full = evaluate_full_integrated_report_gate(tmp_path, section_result_ids={"cox": "cox-mv-ready"}, include_sections=["cox"])
    assert full["status"] == "blocked"
    assert full["prerequisite_summary"]["section_only_package_sufficient"] is True
    assert "full_integrated_required_sections_not_complete" in full["blockers"]


def test_cox_multivariate_report_ready_blocks_without_plot_unless_table_only(tmp_path: Path) -> None:
    save_registry(tmp_path, [_cox_multivariate_entry(tmp_path, plot=False)])

    blocked = evaluate_cox_report_ready_gate(tmp_path, result_id="cox-mv-ready")
    allowed = evaluate_cox_report_ready_gate(tmp_path, result_id="cox-mv-ready", allow_table_only_report=True)

    assert blocked["status"] == "blocked"
    assert "cox_multivariate_report_ready_requires_formal_cox_plot_artifact_or_explicit_table_only_mode" in blocked["blockers"]
    assert allowed["status"] == "eligible_for_cox_report_ready"


def _cox_multivariate_entry(root: Path, *, plot: bool = True) -> dict:
    table = root / "results" / "tables" / "cox_mv.tsv"
    log = root / "analysis" / "cox_mv_log.json"
    _write(
        table,
        "covariate\tcovariate_label\tcovariate_type\thazard_ratio\tci_lower\tci_upper\tp_value\tz_statistic\tsample_count\tevent_count\tnon_missing_count\tmissing_count\tadjusted_for\tmethod\twarnings\n"
        "age\tAge\tcontinuous_variable\t1.20\t1.05\t1.40\t0.01\t2.3\t24\t20\t24\t0\tmarker\tmultivariate_cox_partial_likelihood_breslow_ties\tstatistical_only\n"
        "marker\tMarker\tbinary_variable\t0.85\t0.50\t1.20\t0.32\t0.5\t24\t20\t24\t0\tage\tmultivariate_cox_partial_likelihood_breslow_ties\tstatistical_only\n",
    )
    _write(log, "{}\n")
    entry = ResultIndexEntry(
        result_id="cox-mv-ready",
        task_run_id="run-cox-mv",
        task_type="cox_multivariate",
        result_semantics="formal_computed_result",
        input_package_id="surv-input",
        source_dataset_id="surv-input",
        source_repository_manifest="B12 survival input package",
        parameters_manifest={
            "survival_clinical_input_id": "surv-input",
            "survival_outcome_gate_id": "outcome",
            "time_field": "OS_time",
            "event_field": "OS_event",
            "selected_covariates": ["age", "marker"],
            "missingness_policy": "drop_missing",
            "minimum_event_count": 10,
        },
        engine_name="biomedpilot_controlled_cox_multivariate",
        engine_version="0.1.0",
        dependency_snapshot={"status": "passed", "python_lifelines": {"available": True}},
        output_artifacts=({"artifact_type": "cox_multivariate_result_table", "path": str(table)},),
        plot_artifacts=(_plot("plot-cox-mv", "cox_forest_plot", "cox-mv-ready"),) if plot else (),
        validation_status="passed",
        log_artifacts=({"artifact_type": "task_run_log", "path": str(log)},),
    ).to_dict()
    entry["survival_clinical_input_id"] = "surv-input"
    entry["survival_outcome_gate_id"] = "outcome"
    return entry


def _plot(plot_id: str, plot_type: str, source_result_id: str) -> dict:
    return {"plot_id": plot_id, "plot_type": plot_type, "source_result_id": source_result_id, "plot_semantics": "formal_computed_result", "source_result_semantics": "formal_computed_result", "blockers": []}


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
