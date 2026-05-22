from __future__ import annotations

from pathlib import Path

from app.bioinformatics.reports.integrated import evaluate_full_integrated_report_gate
from app.bioinformatics.reports.survival_clinical import create_cox_report_ready_package, create_km_logrank_report_ready_package, evaluate_cox_report_ready_gate, evaluate_km_logrank_report_ready_gate
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import load_registry, save_registry


def test_km_report_ready_gate_passes_formal_result_with_plot_and_provenance(tmp_path: Path) -> None:
    entry = _km_entry(tmp_path)
    save_registry(tmp_path, [entry])

    gate = evaluate_km_logrank_report_ready_gate(tmp_path, result_id="km-ready")

    assert gate["status"] == "eligible_for_km_logrank_report_ready"
    assert gate["package_creation_enabled"] is True
    assert gate["report_ready_eligible"] is False
    assert gate["diagnostics"]["km_curve_row_count"] == 2
    assert gate["diagnostics"]["logrank_row_count"] == 1
    assert not (tmp_path / "survival_clinical_report_package").exists()


def test_km_report_ready_gate_blocks_preflight_and_missing_plot_without_table_only(tmp_path: Path) -> None:
    entry = _km_entry(tmp_path, result_semantics="preflight_only", plot=False)
    save_registry(tmp_path, [entry])

    gate = evaluate_km_logrank_report_ready_gate(tmp_path, result_id="km-ready")

    assert gate["status"] == "blocked"
    assert "km_report_ready_requires_formal_computed_result" in gate["blockers"]
    assert "km_report_ready_requires_formal_km_plot_artifact_or_explicit_table_only_mode" in gate["blockers"]


def test_km_report_ready_gate_allows_explicit_table_only_mode(tmp_path: Path) -> None:
    entry = _km_entry(tmp_path, plot=False)
    save_registry(tmp_path, [entry])

    gate = evaluate_km_logrank_report_ready_gate(tmp_path, result_id="km-ready", allow_table_only_report=True)

    assert gate["status"] == "eligible_for_km_logrank_report_ready"
    assert gate["allow_table_only_report"] is True


def test_cox_report_ready_gate_passes_formal_univariate_result_with_plot(tmp_path: Path) -> None:
    entry = _cox_entry(tmp_path)
    save_registry(tmp_path, [entry])

    gate = evaluate_cox_report_ready_gate(tmp_path, result_id="cox-ready")

    assert gate["status"] == "eligible_for_cox_report_ready"
    assert gate["package_creation_enabled"] is True
    assert gate["report_ready_eligible"] is False
    assert gate["diagnostics"]["cox_row_count"] == 1


def test_cox_report_ready_gate_blocks_multivariate_and_clinical_conclusion(tmp_path: Path) -> None:
    entry = _cox_entry(tmp_path)
    entry["task_type"] = "cox_multivariate"
    entry["parameters_manifest"]["clinical_conclusion"] = "forbidden"
    save_registry(tmp_path, [entry])

    gate = evaluate_cox_report_ready_gate(tmp_path, result_id="cox-ready")

    assert gate["status"] == "blocked"
    assert "cox_report_ready_requires_cox_univariate_task" in gate["blockers"]
    assert "clinical_conclusion_text_forbidden" in gate["blockers"]


def test_full_integrated_gate_consumes_km_and_cox_report_ready_gates_but_stays_blocked(tmp_path: Path) -> None:
    entries = [_section_entry(tmp_path, "deg-ready", "deg", "deg_result_table"), _section_entry(tmp_path, "ora-ready", "ora_enrichment", "ora_result_table"), _section_entry(tmp_path, "gsea-ready", "gsea_preranked", "gsea_result_table"), _km_entry(tmp_path), _cox_entry(tmp_path)]
    save_registry(tmp_path, entries)

    gate = evaluate_full_integrated_report_gate(tmp_path, section_result_ids={"formal_deg": "deg-ready", "ora_enrichment": "ora-ready", "gsea_preranked": "gsea-ready", "survival_km_logrank": "km-ready", "cox": "cox-ready"})

    sections = {row["section_id"]: row for row in gate["section_rows"]}
    assert sections["survival_km_logrank"]["section_report_ready_gate_schema"] == "biomedpilot.km_logrank_report_ready_gate.v1"
    assert sections["survival_km_logrank"]["section_report_ready_status"] == "passed"
    assert sections["cox"]["section_report_ready_gate_schema"] == "biomedpilot.cox_univariate_report_ready_gate.v1"
    assert sections["cox"]["section_report_ready_status"] == "passed"
    assert gate["status"] == "blocked"
    assert "survival_clinical_report_ready_not_implemented" in gate["blockers"]
    assert "full_integrated_report_export_not_enabled_in_b23_1" in gate["blockers"]


def test_km_report_ready_package_writes_section_only_layout_and_updates_source_result(tmp_path: Path) -> None:
    save_registry(tmp_path, [_km_entry(tmp_path)])

    package = create_km_logrank_report_ready_package(tmp_path, result_id="km-ready")

    assert package["status"] == "survival_km_logrank_only_report_ready_package_created"
    assert package["section_scope"] == "survival_km_logrank_only"
    package_path = Path(package["package_path"])
    assert (package_path / "km_logrank_report.md").is_file()
    assert (package_path / "README_limitations.md").is_file()
    assert (package_path / "tables" / "km_curve.tsv").is_file()
    assert (package_path / "tables" / "logrank.tsv").is_file()
    assert (package_path / "manifests" / "gate_snapshot.json").is_file()
    assert (package_path / "provenance" / "provenance.json").is_file()
    assert package["clinical_conclusion_enabled"] is False
    assert package["full_integrated_report_enabled"] is False
    entry = load_registry(tmp_path)["results"][0]
    assert entry["report_ready_eligible"] is True
    assert entry["report_artifacts"][0]["section_scope"] == "survival_km_logrank_only"
    assert "clinical advice" in (package_path / "km_logrank_report.md").read_text(encoding="utf-8")
    full = evaluate_full_integrated_report_gate(tmp_path, section_result_ids={"survival_km_logrank": "km-ready"})
    assert full["status"] == "blocked"
    assert "full_integrated_prerequisite_forbids_section_package_as_full_report:survival_km_logrank" in full["blockers"]


def test_cox_report_ready_package_writes_section_only_layout_and_updates_source_result(tmp_path: Path) -> None:
    save_registry(tmp_path, [_cox_entry(tmp_path)])

    package = create_cox_report_ready_package(tmp_path, result_id="cox-ready")

    assert package["status"] == "cox_univariate_only_report_ready_package_created"
    assert package["section_scope"] == "cox_univariate_only"
    package_path = Path(package["package_path"])
    assert (package_path / "cox_univariate_report.md").is_file()
    assert (package_path / "tables" / "cox.tsv").is_file()
    assert (package_path / "manifests" / "dependency_snapshot.json").is_file()
    assert (package_path / "manifests" / "package_inventory.json").is_file()
    assert package["clinical_conclusion_enabled"] is False
    assert package["full_integrated_report_enabled"] is False
    entry = load_registry(tmp_path)["results"][0]
    assert entry["report_ready_eligible"] is True
    assert entry["report_artifacts"][0]["section_scope"] == "cox_univariate_only"


def test_survival_clinical_report_ready_package_blocks_without_gate_pass_and_writes_nothing(tmp_path: Path) -> None:
    save_registry(tmp_path, [_km_entry(tmp_path, result_semantics="preflight_only", plot=False)])

    package = create_km_logrank_report_ready_package(tmp_path, result_id="km-ready")

    assert package["status"] == "blocked"
    assert "km_report_ready_requires_formal_computed_result" in package["blockers"]
    assert not (tmp_path / "survival_clinical_report_package").exists()


def _km_entry(root: Path, *, result_semantics: str = "formal_computed_result", plot: bool = True) -> dict:
    km_table = root / "results" / "tables" / "km_curve.tsv"
    logrank_table = root / "results" / "tables" / "logrank.tsv"
    log = root / "analysis" / "km_log.json"
    _write(km_table, "time\tsurvival_probability\tgroup\tat_risk\tevents\tcensored\ttime_unit\twarnings\n1\t0.5\tA\t2\t1\t0\tmonth\t\n1\t0.5\tB\t2\t1\t0\tmonth\t\n")
    _write(logrank_table, "group_a\tgroup_b\ttest_statistic\tp_value\tmethod\tevent_count_group_a\tevent_count_group_b\tsample_count_group_a\tsample_count_group_b\twarnings\nA\tB\t1.2\t0.27\tlogrank\t1\t1\t2\t2\t\n")
    _write(log, "{}\n")
    entry = ResultIndexEntry(
        result_id="km-ready",
        task_run_id="run-km",
        task_type="survival_km_logrank",
        result_semantics=result_semantics,
        input_package_id="surv-input",
        source_dataset_id="surv-input",
        source_repository_manifest="B12 survival input package",
        parameters_manifest={
            "survival_clinical_input_id": "surv-input",
            "survival_outcome_gate_id": "outcome",
            "time_field": "OS_time",
            "event_field": "OS_event",
            "grouping_variable": "arm",
            "group_a": "A",
            "group_b": "B",
            "censoring_policy": "right_censored",
            "missingness_policy": "drop_missing",
        },
        engine_name="engine",
        engine_version="1",
        dependency_snapshot={"status": "passed", "python_lifelines": {"available": True}},
        output_artifacts=({"artifact_type": "km_curve_table", "path": str(km_table)}, {"artifact_type": "logrank_result_table", "path": str(logrank_table)}),
        plot_artifacts=(_plot("plot-km", "km_curve", "km-ready"),) if plot else (),
        validation_status="passed",
        log_artifacts=({"artifact_type": "task_run_log", "path": str(log)},),
    ).to_dict()
    entry["survival_clinical_input_id"] = "surv-input"
    entry["survival_outcome_gate_id"] = "outcome"
    return entry


def _cox_entry(root: Path, *, plot: bool = True) -> dict:
    table = root / "results" / "tables" / "cox.tsv"
    log = root / "analysis" / "cox_log.json"
    _write(table, "covariate\tcovariate_label\tcovariate_type\thazard_ratio\tci_lower\tci_upper\tp_value\tz_statistic\tsample_count\tevent_count\tnon_missing_count\tmissing_count\tmethod\twarnings\narm\tArm\tbinary_variable\t1.4\t0.8\t2.1\t0.2\t1.1\t6\t3\t6\t0\tcox\tstatistical_only\n")
    _write(log, "{}\n")
    entry = ResultIndexEntry(
        result_id="cox-ready",
        task_run_id="run-cox",
        task_type="cox_univariate",
        result_semantics="formal_computed_result",
        input_package_id="surv-input",
        source_dataset_id="surv-input",
        source_repository_manifest="B12 survival input package",
        parameters_manifest={
            "survival_clinical_input_id": "surv-input",
            "survival_outcome_gate_id": "outcome",
            "time_field": "OS_time",
            "event_field": "OS_event",
            "covariate": "arm",
            "covariate_type": "binary_variable",
            "missing_value_policy": "drop_missing",
            "minimum_event_count": 3,
        },
        engine_name="engine",
        engine_version="1",
        dependency_snapshot={"status": "passed", "python_lifelines": {"available": True}},
        output_artifacts=({"artifact_type": "cox_result_table", "path": str(table)},),
        plot_artifacts=(_plot("plot-cox", "cox_forest_plot", "cox-ready"),) if plot else (),
        validation_status="passed",
        log_artifacts=({"artifact_type": "task_run_log", "path": str(log)},),
    ).to_dict()
    entry["survival_clinical_input_id"] = "surv-input"
    entry["survival_outcome_gate_id"] = "outcome"
    return entry


def _section_entry(root: Path, result_id: str, task_type: str, artifact_type: str) -> dict:
    table = root / "results" / "tables" / f"{result_id}.tsv"
    log = root / "analysis" / f"{result_id}.json"
    _write(table, f"{artifact_type}\nvalue\n")
    _write(log, "{}\n")
    return ResultIndexEntry(
        result_id=result_id,
        task_run_id=f"run-{result_id}",
        task_type=task_type,
        result_semantics="formal_computed_result",
        input_package_id="input",
        source_dataset_id="dataset",
        source_repository_manifest="manifest",
        parameters_manifest={"section": task_type},
        engine_name="engine",
        engine_version="1",
        dependency_snapshot={"status": "passed"},
        output_artifacts=({"artifact_type": artifact_type, "path": str(table)},),
        plot_artifacts=(_plot(f"plot-{result_id}", "section_plot", result_id),),
        validation_status="passed",
        log_artifacts=({"artifact_type": "task_run_log", "path": str(log)},),
    ).to_dict()


def _plot(plot_id: str, plot_type: str, source_result_id: str) -> dict:
    return {"plot_id": plot_id, "plot_type": plot_type, "source_result_id": source_result_id, "plot_semantics": "formal_computed_result", "source_result_semantics": "formal_computed_result", "blockers": []}


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
