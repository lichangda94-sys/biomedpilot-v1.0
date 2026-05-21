from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.enrichment.e2e_audit import audit_ora_e2e_acceptance
from app.bioinformatics.plots import create_ora_plot_artifact
from app.bioinformatics.reports.ora import create_ora_report_ready_package
from app.bioinformatics.results.models import RESULT_INDEX_SCHEMA_VERSION, ResultIndexEntry


def test_ora_e2e_acceptance_passes_for_complete_plot_package(tmp_path: Path) -> None:
    _fixture(tmp_path, with_plot=True)
    package = create_ora_report_ready_package(tmp_path, result_id="ora-e2e")

    audit = audit_ora_e2e_acceptance(tmp_path, result_id="ora-e2e", package_manifest_path=Path(str(package["package_path"])) / "ora_report_package_manifest.json")

    assert audit["status"] == "passed"
    assert audit["checklist"]["source_deg_traces_to_ora_result"] is True
    assert audit["checklist"]["ora_review_matches_result_table"] is True
    assert audit["checklist"]["plot_artifact_registered_and_packaged"] is True
    assert audit["checklist"]["package_independently_reviewable"] is True
    assert audit["traceability"]["source_deg_result_id"] == "deg-source"
    assert audit["traceability"]["ora_result_id"] == "ora-e2e"


def test_ora_e2e_acceptance_passes_for_explicit_table_only_package(tmp_path: Path) -> None:
    _fixture(tmp_path, with_plot=False)
    package = create_ora_report_ready_package(tmp_path, result_id="ora-e2e", allow_table_only_report=True)

    audit = audit_ora_e2e_acceptance(tmp_path, result_id="ora-e2e", package_manifest_path=Path(str(package["package_path"])) / "ora_report_package_manifest.json", allow_table_only_report=True)

    assert audit["status"] == "passed"
    assert audit["checklist"]["table_only_mode_not_misleading"] is True
    assert audit["checklist"]["plot_artifact_registered_and_packaged"] is True


def test_ora_e2e_acceptance_fails_for_missing_dependency_invalid_table_and_missing_plot(tmp_path: Path) -> None:
    _fixture(tmp_path / "missing_dependency", with_plot=False, dependency_passed=False)
    dep = audit_ora_e2e_acceptance(tmp_path / "missing_dependency", result_id="ora-e2e", allow_table_only_report=True)
    assert dep["status"] == "blocked"
    assert dep["checklist"]["dependency_missing_invalid_table_missing_plot_blockers_visible"] is True
    assert any("dependency_snapshot" in item for item in dep["failure_diagnostics"]["report_gate_blockers"])

    _fixture(tmp_path / "invalid_table", with_plot=False, table_valid=False)
    invalid = audit_ora_e2e_acceptance(tmp_path / "invalid_table", result_id="ora-e2e", allow_table_only_report=True)
    assert invalid["status"] == "blocked"
    assert any("ora_table:" in item for item in invalid["failure_diagnostics"]["report_gate_blockers"])

    _fixture(tmp_path / "missing_plot", with_plot=False)
    missing_plot = audit_ora_e2e_acceptance(tmp_path / "missing_plot", result_id="ora-e2e")
    assert missing_plot["status"] == "blocked"
    assert any("plot_artifact" in item or "plot_artifact_or_table_only_mode" in item for item in missing_plot["failure_diagnostics"]["report_gate_blockers"])


def _fixture(root: Path, *, with_plot: bool, dependency_passed: bool = True, table_valid: bool = True) -> None:
    root.mkdir(parents=True, exist_ok=True)
    table = root / "results" / "tables" / "ora.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    if table_valid:
        table.write_text(
            "term_id\tterm_name\tgene_set_size\toverlap_count\toverlap_genes\tbackground_size\tselected_gene_count\tp_value\tadjusted_p_value\tenrichment_ratio\tsource_gene_list\twarnings\n"
            "TERM_A\tApoptosis\t2\t2\tTP53;BRCA1\t100\t10\t0.001\t0.003\t10\tselected\t\n",
            encoding="utf-8",
        )
    else:
        table.write_text("term_id\tterm_name\tp_value\nTERM_A\tApoptosis\tbad\n", encoding="utf-8")
    _write_gene_set_registry(root)
    task_log = root / "analysis_runs" / "ora" / "run-ora" / "task_run.json"
    task_log.parent.mkdir(parents=True, exist_ok=True)
    task_log.write_text(json.dumps({"task_run_id": "run-ora", "status": "completed"}), encoding="utf-8")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    deg = ResultIndexEntry(result_id="deg-source", task_run_id="deg-run", task_type="deg", result_semantics="formal_computed_result", validation_status="passed").to_dict()
    ora = {
        "result_id": "ora-e2e",
        "task_run_id": "run-ora",
        "task_type": "ora_enrichment",
        "result_semantics": "formal_computed_result",
        "input_package_id": "ora-input-1",
        "ora_input_id": "ora-input-1",
        "source_dataset_id": "dataset-1",
        "source_repository_manifest": "standardized_data/repositories/repository_manifest.json",
        "source_deg_result_id": "deg-source",
        "source_result_semantics": "formal_computed_result",
        "gene_set_resource_id": "sets",
        "parameters_manifest": {"ora_parameter_id": "params-1", "gene_set_resource_id": "sets", "test_method": "hypergeometric", "fdr_threshold": 0.05, "selected_gene_rule": "adjusted_p_value_and_abs_log2fc", "background_universe_rule": "source_deg_detected_genes"},
        "engine_name": "python_scipy_statsmodels_ora_mvp",
        "engine_version": "0.1.0",
        "dependency_snapshot": {"status": "passed" if dependency_passed else "blocked", "packages": {"scipy": {"version": "fake-scipy"}, "statsmodels": {"version": "fake-statsmodels"}}, "blockers": [] if dependency_passed else ["missing_python_package:statsmodels"]},
        "output_artifacts": [{"artifact_type": "ora_result_table", "path": "results/tables/ora.tsv"}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": [],
        "blockers": [],
        "log_artifacts": [{"artifact_type": "controlled_ora_task_run_log", "path": "analysis_runs/ora/run-ora/task_run.json"}],
        "failure_reason": "",
        "created_at": now,
        "updated_at": now,
        "schema_version": "biomedpilot.result_index_entry.v1",
        "report_ready_eligible": False,
        "migration_status": "native_v2",
    }
    _write_result_index(root, [deg, ora])
    if with_plot:
        plot = create_ora_plot_artifact(root, result_id="ora-e2e")
        assert plot["status"] == "passed"


def _write_gene_set_registry(root: Path) -> None:
    gmt = root / "user_data" / "bioinformatics" / "gene_sets" / "custom" / "sets.gmt"
    gmt.parent.mkdir(parents=True, exist_ok=True)
    gmt.write_text("TERM_A\tApoptosis\tTP53\tBRCA1\n", encoding="utf-8")
    registry = root / "user_data" / "bioinformatics" / "gene_sets" / "gene_set_registry.json"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.gene_set_registry.v1",
                "resources": [
                    {
                        "resource_id": "sets",
                        "name": "sets",
                        "collection_type": "Custom",
                        "species": "unknown",
                        "gene_id_type": "symbol",
                        "status": "available",
                        "local_path": str(gmt.relative_to(root)),
                        "source": "user_import",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_result_index(root: Path, entries: list[dict[str, object]]) -> None:
    path = root / "results" / "summaries" / "result_index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": RESULT_INDEX_SCHEMA_VERSION, "results": entries}), encoding="utf-8")
