from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.bioinformatics.plots import create_gsea_plot_artifact
from app.bioinformatics.reports.gsea import create_gsea_report_ready_package, evaluate_gsea_report_ready_gate
from app.bioinformatics.results.models import RESULT_INDEX_SCHEMA_VERSION, ResultIndexEntry
from app.bioinformatics.results.registry import load_registry


def test_formal_gsea_with_plot_artifact_creates_report_ready_package(tmp_path: Path) -> None:
    complete_gsea_fixture(tmp_path, with_plot=True)

    gate = evaluate_gsea_report_ready_gate(tmp_path, result_id="gsea-formal")
    package = create_gsea_report_ready_package(tmp_path, result_id="gsea-formal")

    assert gate["status"] == "eligible_for_gsea_report_ready"
    assert package["status"] == "gsea_report_ready_package_created"
    package_path = Path(str(package["package_path"]))
    assert (package_path / "gsea_report.md").is_file()
    assert (package_path / "tables" / "gsea_result_table.tsv").is_file()
    assert (package_path / "plots" / "gsea_plot_artifact.json").is_file()
    assert (package_path / "manifests" / "gsea_result_index_snapshot.json").is_file()
    assert (package_path / "manifests" / "source_deg_result_snapshot.json").is_file()
    assert (package_path / "manifests" / "gsea_parameters_manifest.json").is_file()
    assert (package_path / "manifests" / "gene_set_resource_manifest.json").is_file()
    assert (package_path / "manifests" / "dependency_snapshot.json").is_file()
    assert (package_path / "manifests" / "gate_snapshot.json").is_file()
    assert (package_path / "manifests" / "package_inventory.json").is_file()
    assert (package_path / "logs" / "task_run_log.json").is_file()
    report = (package_path / "gsea_report.md").read_text(encoding="utf-8")
    assert "Controlled preranked GSEA" in report
    assert "not phenotype permutation GSEA" in report
    assert "not survival analysis" in report
    assert "not clinical interpretation" in report
    entry = next(item for item in load_registry(tmp_path)["results"] if item["result_id"] == "gsea-formal")
    assert entry["report_ready_eligible"] is True
    assert entry["report_artifacts"][0]["artifact_type"] == "gsea_report_ready_package"


def test_formal_gsea_table_only_mode_is_explicit_and_non_misleading(tmp_path: Path) -> None:
    complete_gsea_fixture(tmp_path, with_plot=False)

    blocked = evaluate_gsea_report_ready_gate(tmp_path, result_id="gsea-formal")
    table_only = create_gsea_report_ready_package(tmp_path, result_id="gsea-formal", allow_table_only_report=True)

    assert blocked["status"] == "blocked"
    assert "gsea_report_ready_requires_gsea_plot_artifact_or_table_only_mode" in blocked["blockers"]
    assert table_only["status"] == "gsea_report_ready_package_created"
    text = (Path(str(table_only["package_path"])) / "gsea_report.md").read_text(encoding="utf-8")
    text += (Path(str(table_only["package_path"])) / "README_limitations.md").read_text(encoding="utf-8")
    assert "No-plot GSEA report" in text
    assert "does not mean plot generation failed" in text
    assert "must not imply that GSEA enrichment curve, NES barplot, volcano, heatmap, ORA, or survival figures were generated" in text


def test_gsea_report_gate_blocks_invalid_table_missing_gene_set_and_dependency(tmp_path: Path) -> None:
    complete_gsea_fixture(tmp_path / "invalid_table", with_plot=False, table_valid=False)
    invalid = evaluate_gsea_report_ready_gate(tmp_path / "invalid_table", result_id="gsea-formal", allow_table_only_report=True)
    assert any("gsea_table:" in item for item in invalid["blockers"])

    complete_gsea_fixture(tmp_path / "missing_gene_set", with_plot=False, gene_set_manifest=False)
    missing_gene_set = evaluate_gsea_report_ready_gate(tmp_path / "missing_gene_set", result_id="gsea-formal", allow_table_only_report=True)
    assert any("gene_set:" in item for item in missing_gene_set["blockers"])

    complete_gsea_fixture(tmp_path / "missing_dependency", with_plot=False, dependency_passed=False)
    missing_dependency = evaluate_gsea_report_ready_gate(tmp_path / "missing_dependency", result_id="gsea-formal", allow_table_only_report=True)
    assert "gsea_report_dependency_snapshot_not_passed" in missing_dependency["blockers"]


def test_imported_derived_gsea_package_keeps_imported_policy_and_not_formal_report_ready(tmp_path: Path) -> None:
    complete_gsea_fixture(tmp_path, with_plot=True, result_semantics="imported_external_result", source_result_semantics="imported_external_result")

    gate = evaluate_gsea_report_ready_gate(tmp_path, result_id="gsea-formal")
    package = create_gsea_report_ready_package(tmp_path, result_id="gsea-formal")

    assert gate["status"] == "eligible_for_imported_derived_gsea_report_package"
    assert "imported_derived_gsea_report_not_biomedpilot_formal_recomputed_gsea" in gate["warnings"]
    assert package["status"] == "imported_derived_gsea_report_package_created"
    assert package["section_scope"] == "imported_derived_gsea_only"
    entry = next(item for item in load_registry(tmp_path)["results"] if item["result_id"] == "gsea-formal")
    assert entry["report_ready_eligible"] is False
    assert entry["report_artifacts"][0]["artifact_type"] == "imported_derived_gsea_report_package"


@pytest.mark.parametrize("semantics", ["testing_level", "exploratory", "preflight_only"])
def test_gsea_report_gate_blocks_testing_exploratory_and_preflight(tmp_path: Path, semantics: str) -> None:
    complete_gsea_fixture(tmp_path, with_plot=False, result_semantics=semantics, source_result_semantics=semantics)

    gate = evaluate_gsea_report_ready_gate(tmp_path, result_id="gsea-formal", allow_table_only_report=True)

    assert gate["status"] == "blocked"
    assert f"gsea_report_source_semantics_not_allowed:{semantics}" in gate["blockers"]


def test_gsea_report_package_path_is_timestamped_and_non_overwriting(tmp_path: Path) -> None:
    complete_gsea_fixture(tmp_path, with_plot=True)

    first = create_gsea_report_ready_package(tmp_path, result_id="gsea-formal")
    second = create_gsea_report_ready_package(tmp_path, result_id="gsea-formal")

    assert first["status"] == "gsea_report_ready_package_created"
    assert second["status"] == "gsea_report_ready_package_created"
    assert first["package_path"] != second["package_path"]
    assert second["package_inventory"]["required_directories"]["tables"] is True
    assert second["package_inventory"]["required_files"]["manifests/package_inventory.json"] is True


def complete_gsea_fixture(
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
    deg_table = _write_deg_table(root)
    gsea_table = _write_gsea_table(root, valid=table_valid)
    if gene_set_manifest:
        _write_gene_set_registry(root)
    task_log = root / "analysis_runs" / "gsea" / "run-gsea" / "task_run.json"
    task_log.parent.mkdir(parents=True, exist_ok=True)
    task_log.write_text(json.dumps({"task_run_id": "run-gsea", "status": "completed"}), encoding="utf-8")
    _write_result_index(
        root,
        [
            _source_deg_entry(deg_table, result_semantics=source_result_semantics),
            _gsea_entry(gsea_table, result_semantics=result_semantics, source_result_semantics=source_result_semantics, dependency_status="passed" if dependency_passed else "blocked"),
        ],
    )
    if with_plot:
        plot = create_gsea_plot_artifact(root, result_id="gsea-formal", plot_type="gsea_enrichment_curve_spec")
        assert plot["status"] == "passed"


def _write_deg_table(root: Path) -> Path:
    path = root / "results" / "tables" / "deg.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [f"GENE{i}\tGENE{i}\t{2.0 if i <= 6 else -1.5}\t0.01\t0.02" for i in range(1, 13)]
    path.write_text("feature_id\tgene_symbol\tlog2_fold_change\tp_value\tadjusted_p_value\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def _write_gsea_table(root: Path, *, valid: bool = True) -> Path:
    path = root / "results" / "tables" / "gsea.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    if valid:
        path.write_text(
            "term_id\tterm_name\tset_size\toverlap_size\tenrichment_score\tnormalized_enrichment_score\tp_value\tadjusted_p_value\tleading_edge_genes\trank_metric\twarnings\n"
            "TERM_POS\tPositive\t10\t4\t0.8\t1.6\t0.01\t0.02\tGENE1;GENE2\tsigned_log10_fdr_by_log2fc\t\n"
            "TERM_NEG\tNegative\t10\t4\t-0.7\t-1.4\t0.03\t0.2\tGENE8;GENE9\tsigned_log10_fdr_by_log2fc\t\n",
            encoding="utf-8",
        )
    else:
        path.write_text("term_id\tterm_name\tp_value\nTERM_POS\tPositive\tbad\n", encoding="utf-8")
    return path


def _write_gene_set_registry(root: Path) -> Path:
    gmt = root / "user_data" / "bioinformatics" / "gene_sets" / "custom" / "sets.gmt"
    gmt.parent.mkdir(parents=True, exist_ok=True)
    gmt.write_text("TERM_POS\tPositive\tGENE1\tGENE2\tGENE3\tGENE4\nTERM_NEG\tNegative\tGENE8\tGENE9\tGENE10\tGENE11\n", encoding="utf-8")
    registry = root / "user_data" / "bioinformatics" / "gene_sets" / "gene_set_registry.json"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.gene_set_registry.v1",
                "resources": [{"resource_id": "sets", "name": "sets", "collection_type": "Custom", "species": "unknown", "gene_id_type": "symbol", "status": "available", "local_path": str(gmt.relative_to(root)), "source": "user_import"}],
            }
        ),
        encoding="utf-8",
    )
    return gmt


def _source_deg_entry(table: Path, *, result_semantics: str) -> dict[str, object]:
    return ResultIndexEntry(
        result_id="deg-source",
        task_run_id="deg-run",
        task_type="deg",
        result_semantics=result_semantics,
        parameters_manifest={"gene_id_type": "symbol"},
        output_artifacts=({"artifact_type": "deg_result_table", "path": str(table.relative_to(table.parents[2])) if "results" in table.parts else str(table)},),
        validation_status="passed",
    ).to_dict()


def _gsea_entry(table: Path, *, result_semantics: str, source_result_semantics: str, dependency_status: str) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "result_id": "gsea-formal",
        "task_run_id": "run-gsea",
        "task_type": "gsea_preranked",
        "result_semantics": result_semantics,
        "input_package_id": "gsea-input-1",
        "gsea_input_id": "gsea-input-1",
        "source_dataset_id": "dataset-1",
        "source_repository_manifest": "standardized_data/repositories/repository_manifest.json",
        "source_deg_result_id": "deg-source",
        "source_result_semantics": source_result_semantics,
        "gene_set_resource_id": "sets",
        "parameters_manifest": {"gsea_parameter_id": "params-1", "gene_set_resource_id": "sets", "rank_metric": "signed_log10_fdr_by_log2fc", "permutation_type": "gene_set", "permutation_count": 100, "random_seed": 1, "fdr_threshold": 0.25},
        "engine_name": "python_preranked_gsea_mvp",
        "engine_version": "0.1.0",
        "dependency_snapshot": {"status": dependency_status, "packages": {"numpy": {"version": "n"}, "pandas": {"version": "p"}, "scipy": {"version": "s"}, "statsmodels": {"version": "sm"}}, "blockers": [] if dependency_status == "passed" else ["missing_python_package:statsmodels"]},
        "output_artifacts": [{"artifact_type": "gsea_result_table", "path": str(table.relative_to(table.parents[2])) if "results" in table.parts else str(table)}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": [],
        "blockers": [],
        "log_artifacts": [{"artifact_type": "controlled_gsea_task_run_log", "path": "analysis_runs/gsea/run-gsea/task_run.json"}],
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
