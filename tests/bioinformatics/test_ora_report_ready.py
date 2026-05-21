from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.bioinformatics.plots import create_ora_plot_artifact
from app.bioinformatics.reports.ora import create_ora_report_ready_package, evaluate_ora_report_ready_gate
from app.bioinformatics.results.models import RESULT_INDEX_SCHEMA_VERSION, ResultIndexEntry
from app.bioinformatics.results.registry import load_registry


def test_formal_ora_with_plot_artifact_creates_report_ready_package(tmp_path: Path) -> None:
    _complete_fixture(tmp_path, with_plot=True)

    gate = evaluate_ora_report_ready_gate(tmp_path, result_id="ora-formal")
    package = create_ora_report_ready_package(tmp_path, result_id="ora-formal")

    assert gate["status"] == "eligible_for_ora_report_ready"
    assert package["status"] == "ora_report_ready_package_created"
    package_path = Path(str(package["package_path"]))
    assert (package_path / "ora_report.md").is_file()
    assert (package_path / "tables" / "ora_result_table.tsv").is_file()
    assert (package_path / "plots" / "ora_plot_artifact.json").is_file()
    assert (package_path / "manifests" / "ora_result_index_snapshot.json").is_file()
    assert (package_path / "manifests" / "source_deg_result_snapshot.json").is_file()
    assert (package_path / "manifests" / "ora_parameters_manifest.json").is_file()
    assert (package_path / "manifests" / "gene_set_resource_manifest.json").is_file()
    assert (package_path / "manifests" / "dependency_snapshot.json").is_file()
    assert (package_path / "manifests" / "gate_snapshot.json").is_file()
    assert (package_path / "manifests" / "package_inventory.json").is_file()
    assert (package_path / "logs" / "task_run_log.json").is_file()
    report = (package_path / "ora_report.md").read_text(encoding="utf-8")
    assert "ORA identifies over-represented gene sets" in report
    assert "It is not GSEA" in report
    assert "It is not survival analysis" in report
    assert "not clinical interpretation" in report
    entry = next(item for item in load_registry(tmp_path)["results"] if item["result_id"] == "ora-formal")
    assert entry["report_ready_eligible"] is True
    assert entry["report_artifacts"][0]["artifact_type"] == "ora_report_ready_package"


def test_formal_ora_table_only_mode_creates_non_misleading_package(tmp_path: Path) -> None:
    _complete_fixture(tmp_path, with_plot=False)

    blocked = evaluate_ora_report_ready_gate(tmp_path, result_id="ora-formal")
    table_only = create_ora_report_ready_package(tmp_path, result_id="ora-formal", allow_table_only_report=True)

    assert blocked["status"] == "blocked"
    assert "ora_report_ready_requires_ora_plot_artifact_or_table_only_mode" in blocked["blockers"]
    assert table_only["status"] == "ora_report_ready_package_created"
    package_path = Path(str(table_only["package_path"]))
    text = (package_path / "ora_report.md").read_text(encoding="utf-8") + (package_path / "README_limitations.md").read_text(encoding="utf-8")
    assert "No-plot ORA report" in text
    assert "does not mean plot generation failed" in text
    assert "must not imply that ORA barplot, ORA dotplot, GSEA plot, volcano, or heatmap figures were generated" in text


def test_ora_report_gate_blocks_invalid_table_missing_gene_set_and_dependency(tmp_path: Path) -> None:
    _complete_fixture(tmp_path / "invalid_table", with_plot=False, table_valid=False)
    invalid = evaluate_ora_report_ready_gate(tmp_path / "invalid_table", result_id="ora-formal", allow_table_only_report=True)
    assert any("ora_table:" in item for item in invalid["blockers"])

    _complete_fixture(tmp_path / "missing_gene_set", with_plot=False, gene_set_manifest=False)
    missing_gene_set = evaluate_ora_report_ready_gate(tmp_path / "missing_gene_set", result_id="ora-formal", allow_table_only_report=True)
    assert any("gene_set:" in item for item in missing_gene_set["blockers"])

    _complete_fixture(tmp_path / "missing_dependency", with_plot=False, dependency_passed=False)
    missing_dependency = evaluate_ora_report_ready_gate(tmp_path / "missing_dependency", result_id="ora-formal", allow_table_only_report=True)
    assert "ora_report_dependency_snapshot_not_passed" in missing_dependency["blockers"]


def test_imported_derived_ora_package_keeps_imported_policy_and_not_formal_report_ready(tmp_path: Path) -> None:
    _complete_fixture(tmp_path, with_plot=True, result_semantics="imported_external_result", source_result_semantics="imported_external_result")

    gate = evaluate_ora_report_ready_gate(tmp_path, result_id="ora-formal")
    package = create_ora_report_ready_package(tmp_path, result_id="ora-formal")

    assert gate["status"] == "eligible_for_imported_derived_ora_report_package"
    assert "imported_derived_ora_report_not_biomedpilot_formal_recomputed_ora" in gate["warnings"]
    assert package["status"] == "imported_derived_ora_report_package_created"
    assert package["section_scope"] == "imported_derived_ora_only"
    entry = next(item for item in load_registry(tmp_path)["results"] if item["result_id"] == "ora-formal")
    assert entry["report_ready_eligible"] is False
    assert entry["report_artifacts"][0]["artifact_type"] == "imported_derived_ora_report_package"


@pytest.mark.parametrize("semantics", ["testing_level", "exploratory", "preflight_only"])
def test_ora_report_gate_blocks_testing_exploratory_and_preflight(tmp_path: Path, semantics: str) -> None:
    _complete_fixture(tmp_path, with_plot=False, result_semantics=semantics, source_result_semantics=semantics)

    gate = evaluate_ora_report_ready_gate(tmp_path, result_id="ora-formal", allow_table_only_report=True)

    assert gate["status"] == "blocked"
    assert f"ora_report_source_semantics_not_allowed:{semantics}" in gate["blockers"]


def test_ora_report_package_path_is_timestamped_and_non_overwriting(tmp_path: Path) -> None:
    _complete_fixture(tmp_path, with_plot=True)

    first = create_ora_report_ready_package(tmp_path, result_id="ora-formal")
    second = create_ora_report_ready_package(tmp_path, result_id="ora-formal")

    assert first["status"] == "ora_report_ready_package_created"
    assert second["status"] == "ora_report_ready_package_created"
    assert first["package_path"] != second["package_path"]
    inventory = second["package_inventory"]
    assert inventory["required_directories"]["tables"] is True
    assert inventory["required_files"]["manifests/package_inventory.json"] is True


def _complete_fixture(
    root: Path,
    *,
    with_plot: bool,
    result_semantics: str = "formal_computed_result",
    source_result_semantics: str = "formal_computed_result",
    table_valid: bool = True,
    gene_set_manifest: bool = True,
    dependency_passed: bool = True,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    table = _write_ora_table(root, valid=table_valid)
    gmt = _write_gene_set_registry(root) if gene_set_manifest else _write_gmt(root / "sets.gmt")
    task_log = root / "analysis_runs" / "ora" / "run-ora" / "task_run.json"
    task_log.parent.mkdir(parents=True, exist_ok=True)
    task_log.write_text(json.dumps({"task_run_id": "run-ora", "status": "completed"}), encoding="utf-8")
    source = _source_deg_entry(result_semantics=source_result_semantics)
    ora = _ora_entry(
        table,
        result_semantics=result_semantics,
        source_result_semantics=source_result_semantics,
        dependency_status="passed" if dependency_passed else "blocked",
    )
    if not gene_set_manifest:
        ora["parameters_manifest"]["gene_set_resource_id"] = gmt.stem
    _write_result_index(root, [source, ora])
    if with_plot:
        plot = create_ora_plot_artifact(root, result_id="ora-formal", plot_type="ora_barplot")
        assert plot["status"] == "passed"


def _write_ora_table(root: Path, *, valid: bool = True) -> Path:
    path = root / "results" / "tables" / "ora.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    if valid:
        path.write_text(
            "term_id\tterm_name\tgene_set_size\toverlap_count\toverlap_genes\tbackground_size\tselected_gene_count\tp_value\tadjusted_p_value\tenrichment_ratio\tsource_gene_list\twarnings\n"
            "TERM_A\tApoptosis\t2\t2\tTP53;BRCA1\t100\t10\t0.001\t0.003\t10\tselected\t\n",
            encoding="utf-8",
        )
    else:
        path.write_text("term_id\tterm_name\tp_value\nTERM_A\tApoptosis\tbad\n", encoding="utf-8")
    return path


def _write_gene_set_registry(root: Path) -> Path:
    gmt = _write_gmt(root / "user_data" / "bioinformatics" / "gene_sets" / "custom" / "sets.gmt")
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
    return gmt


def _write_gmt(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("TERM_A\tApoptosis\tTP53\tBRCA1\n", encoding="utf-8")
    return path


def _source_deg_entry(*, result_semantics: str) -> dict[str, object]:
    return ResultIndexEntry(result_id="deg-source", task_run_id="deg-run", task_type="deg", result_semantics=result_semantics, validation_status="passed").to_dict()


def _ora_entry(table: Path, *, result_semantics: str, source_result_semantics: str, dependency_status: str) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "result_id": "ora-formal",
        "task_run_id": "run-ora",
        "task_type": "ora_enrichment",
        "result_semantics": result_semantics,
        "input_package_id": "ora-input-1",
        "ora_input_id": "ora-input-1",
        "source_dataset_id": "dataset-1",
        "source_repository_manifest": "standardized_data/repositories/repository_manifest.json",
        "source_deg_result_id": "deg-source",
        "source_result_semantics": source_result_semantics,
        "gene_set_resource_id": "sets",
        "parameters_manifest": {"ora_parameter_id": "params-1", "gene_set_resource_id": "sets", "test_method": "hypergeometric", "fdr_threshold": 0.05, "selected_gene_rule": "adjusted_p_value_and_abs_log2fc", "background_universe_rule": "source_deg_detected_genes"},
        "engine_name": "python_scipy_statsmodels_ora_mvp",
        "engine_version": "0.1.0",
        "dependency_snapshot": {"status": dependency_status, "packages": {"scipy": {"version": "fake-scipy"}, "statsmodels": {"version": "fake-statsmodels"}}, "blockers": [] if dependency_status == "passed" else ["missing_python_package:statsmodels"]},
        "output_artifacts": [{"artifact_type": "ora_result_table", "path": str(table.relative_to(table.parents[2])) if "results" in table.parts else str(table)}],
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


def _write_result_index(root: Path, entries: list[dict[str, object]]) -> None:
    path = root / "results" / "summaries" / "result_index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": RESULT_INDEX_SCHEMA_VERSION, "results": entries}), encoding="utf-8")
