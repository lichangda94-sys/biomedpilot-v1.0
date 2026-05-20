from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.bioinformatics.deg_engine.confirmation import CONFIRMATION_PATH, CONFIRMATION_SCHEMA_VERSION
from app.bioinformatics.plots import create_formal_deg_plot_artifact
from app.bioinformatics.reports.formal_deg import create_formal_deg_report_ready_package, evaluate_formal_deg_report_ready_gate
from app.bioinformatics.reports.readiness import evaluate_report_ready_gate
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import load_registry, register_result


def test_formal_deg_report_ready_package_requires_formal_plot_and_updates_result_index(tmp_path: Path) -> None:
    table = _write_deg_table(tmp_path)
    parameters = _parameters()
    dependency = _dependency()
    _register_formal(tmp_path, table, parameters=parameters, dependency=dependency)
    _write_confirmation(tmp_path, parameters=parameters, dependency=dependency)
    plot = create_formal_deg_plot_artifact(tmp_path, result_id="formal-report", plot_type="volcano_plot")

    gate = evaluate_formal_deg_report_ready_gate(tmp_path, result_id="formal-report")
    manifest = create_formal_deg_report_ready_package(tmp_path, result_id="formal-report")

    assert plot["status"] == "passed"
    assert gate["status"] == "eligible_for_formal_deg_report_ready"
    assert manifest["status"] == "formal_deg_report_ready_package_created"
    assert manifest["section_scope"] == "formal_deg_only"
    assert manifest["gsea_enabled"] is False
    assert manifest["survival_enabled"] is False
    assert manifest["clinical_conclusion_enabled"] is False
    package = Path(str(manifest["package_path"]))
    report = (package / "formal_deg_report.md").read_text(encoding="utf-8")
    assert "Formal DEG Report-Ready Section" in report
    assert "does not include GSEA" in report
    assert "clinical conclusions" in report
    assert (package / "manifests" / "formal_deg_parameter_confirmation.json").is_file()
    assert (package / "manifests" / "plot_artifacts.json").is_file()
    entry = load_registry(tmp_path)["results"][0]
    assert entry["report_ready_eligible"] is True
    assert entry["report_artifacts"][0]["artifact_type"] == "formal_deg_report_ready_package"
    assert evaluate_report_ready_gate(tmp_path)["status"] == "eligible_for_internal_report"


def test_formal_deg_report_ready_blocks_without_plot_unless_table_only_mode_is_explicit(tmp_path: Path) -> None:
    table = _write_deg_table(tmp_path)
    parameters = _parameters()
    dependency = _dependency()
    _register_formal(tmp_path, table, parameters=parameters, dependency=dependency)
    _write_confirmation(tmp_path, parameters=parameters, dependency=dependency)

    blocked = evaluate_formal_deg_report_ready_gate(tmp_path, result_id="formal-report")
    table_only = create_formal_deg_report_ready_package(tmp_path, result_id="formal-report", allow_table_only_report=True)

    assert blocked["status"] == "blocked"
    assert "formal_deg_report_ready_requires_formal_plot_artifact_or_table_only_mode" in blocked["blockers"]
    assert table_only["status"] == "formal_deg_report_ready_package_created"
    assert table_only["allow_table_only_report"] is True
    assert "formal_deg_table_only_report_mode_no_plot_artifact" in table_only["gate"]["warnings"]


def test_formal_deg_report_ready_blocks_imported_testing_and_preflight_results(tmp_path: Path) -> None:
    for result_id, semantics in (
        ("imported", "imported_external_result"),
        ("testing", "testing_level"),
        ("preflight", "preflight_only"),
    ):
        register_result(
            tmp_path,
            ResultIndexEntry(result_id=result_id, task_run_id=f"task-{result_id}", task_type="deg", result_semantics=semantics, validation_status="passed"),
        )

    for result_id in ("imported", "testing", "preflight"):
        gate = evaluate_formal_deg_report_ready_gate(tmp_path, result_id=result_id, allow_table_only_report=True)
        assert gate["status"] == "blocked"
        assert "formal_deg_report_ready_requires_formal_computed_deg_result" in gate["blockers"]


def test_formal_deg_report_ready_blocks_expired_confirmation_dependency_and_invalid_table(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "formal.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text("feature_id\tgene_symbol\tp_value\nf1\tTP53\t0.01\n", encoding="utf-8")
    parameters = _parameters()
    dependency = _dependency(status="blocked")
    _register_formal(tmp_path, table, parameters=parameters, dependency=dependency)
    _write_confirmation(tmp_path, parameters=parameters, dependency=dependency, created_at=datetime.now(timezone.utc) - timedelta(days=8))

    gate = evaluate_formal_deg_report_ready_gate(tmp_path, result_id="formal-report", allow_table_only_report=True)

    assert gate["status"] == "blocked"
    assert "formal_deg_parameter_confirmation_expired" in gate["blockers"]
    assert "formal_deg_dependency_snapshot_not_passed" in gate["blockers"]
    assert "deg_table:missing_column:adjusted_p_value" in gate["blockers"]


def _write_deg_table(root: Path) -> Path:
    table = root / "results" / "tables" / "formal.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "feature_id\tgene_symbol\tbase_mean_or_mean_expression\tcase_mean\tcontrol_mean\tlog2_fold_change\tstatistic\tp_value\tadjusted_p_value\tsignificance_label\twarnings\n"
        "f1\tTP53\t10\t12\t4\t1.4\t3.0\t0.01\t0.02\tup\t\n",
        encoding="utf-8",
    )
    return table


def _register_formal(root: Path, table: Path, *, parameters: dict[str, object], dependency: dict[str, object]) -> None:
    register_result(
        root,
        ResultIndexEntry(
            result_id="formal-report",
            task_run_id="task-formal-report",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="pkg-1",
            source_dataset_id="dataset-1",
            source_repository_manifest="standardized_data/repositories/repository_manifest.json",
            parameters_manifest=parameters,
            engine_name="python_scipy_statsmodels_deg_mvp",
            engine_version="0.1.0",
            dependency_snapshot=dependency,
            output_artifacts=({"artifact_type": "deg_result_table", "path": str(table.relative_to(root)), "schema": "biomedpilot.deg_result_table.v1"},),
            plot_artifacts=(),
            report_artifacts=(),
            validation_status="passed",
            warnings=("low_sample_size_warning_included",),
            log_artifacts=({"artifact_type": "formal_deg_run_log", "path": "analysis/formal_deg/formal-report_run_log.json"},),
            report_ready_eligible=False,
        ),
    )


def _write_confirmation(root: Path, *, parameters: dict[str, object], dependency: dict[str, object], created_at: datetime | None = None) -> None:
    path = root / CONFIRMATION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": CONFIRMATION_SCHEMA_VERSION,
        "created_at": (created_at or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
        "status": "confirmed",
        "confirmed_by_user": True,
        "parameter_manifest": parameters,
        "dependency_snapshot": dependency,
        "output_plan": {
            "task_run_id": "task-formal-report",
            "result_id": "formal-report",
            "result_table_path": "results/tables/formal-report.tsv",
            "task_run_log_path": "analysis/formal_deg/formal-report_run_log.json",
            "result_index_registry_path": "results/summaries/result_index.json",
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _parameters() -> dict[str, object]:
    return {
        "status": "passed",
        "method": "welch_t_test",
        "log2fc_threshold": 1.0,
        "p_value_threshold": 0.05,
        "fdr_threshold": 0.05,
        "case_samples": ["case1", "case2"],
        "control_samples": ["ctrl1", "ctrl2"],
    }


def _dependency(*, status: str = "passed") -> dict[str, object]:
    return {
        "status": status,
        "packages": {
            "numpy": {"version": "2.4.6"},
            "pandas": {"version": "3.0.3"},
            "scipy": {"version": "1.17.1"},
            "statsmodels": {"version": "0.14.6"},
        },
    }
