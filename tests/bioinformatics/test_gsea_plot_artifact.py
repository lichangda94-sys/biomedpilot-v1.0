from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.bioinformatics.plots import create_gsea_plot_artifact
from app.bioinformatics.results.models import RESULT_INDEX_SCHEMA_VERSION, ResultIndexEntry
from app.bioinformatics.results.registry import load_registry


def test_formal_gsea_creates_spec_only_plot_artifact(tmp_path: Path) -> None:
    _complete_fixture(tmp_path)

    result = create_gsea_plot_artifact(tmp_path, result_id="gsea-formal", plot_type="gsea_enrichment_curve_spec")

    assert result["status"] == "passed"
    artifact = result["plot_artifact"]
    assert artifact["source_task_type"] == "gsea_preranked"
    assert artifact["source_result_semantics"] == "formal_computed_result"
    assert artifact["plot_semantics"] == "formal_computed_result"
    assert artifact["image_artifacts"] == []
    assert artifact["plot_spec_artifact"]["rendering"] == "spec_only_no_image_dependency"
    entry = next(item for item in load_registry(tmp_path)["results"] if item["result_id"] == "gsea-formal")
    assert entry["report_ready_eligible"] is False
    assert entry["plot_artifacts"][0]["plot_type"] == "gsea_enrichment_curve_spec"


def test_imported_derived_gsea_plot_keeps_imported_warning(tmp_path: Path) -> None:
    _complete_fixture(tmp_path, result_semantics="imported_external_result", source_result_semantics="imported_external_result")

    result = create_gsea_plot_artifact(tmp_path, result_id="gsea-formal", plot_type="gsea_nes_barplot_spec")

    assert result["status"] == "passed"
    assert result["plot_artifact"]["plot_semantics"] == "imported_external_result"
    assert "imported_gsea_derived_plot_not_biomedpilot_recomputed_formal_plot" in result["warnings"]


@pytest.mark.parametrize("semantics", ["testing_level", "exploratory", "preflight_only"])
def test_gsea_plot_blocks_testing_exploratory_preflight(tmp_path: Path, semantics: str) -> None:
    _complete_fixture(tmp_path, result_semantics=semantics, source_result_semantics=semantics)

    result = create_gsea_plot_artifact(tmp_path, result_id="gsea-formal")

    assert result["status"] == "blocked"
    assert f"gsea_plot_source_semantics_not_allowed:{semantics}" in result["blockers"]


def _complete_fixture(root: Path, *, result_semantics: str = "formal_computed_result", source_result_semantics: str = "formal_computed_result") -> None:
    root.mkdir(parents=True, exist_ok=True)
    table = _write_gsea_table(root)
    task_log = root / "analysis_runs" / "gsea" / "run-gsea" / "task_run.json"
    task_log.parent.mkdir(parents=True, exist_ok=True)
    task_log.write_text(json.dumps({"task_run_id": "run-gsea", "status": "completed"}), encoding="utf-8")
    _write_result_index(root, [_source_deg_entry(result_semantics=source_result_semantics), _gsea_entry(table, result_semantics=result_semantics, source_result_semantics=source_result_semantics)])


def _write_gsea_table(root: Path) -> Path:
    path = root / "results" / "tables" / "gsea.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "term_id\tterm_name\tset_size\toverlap_size\tenrichment_score\tnormalized_enrichment_score\tp_value\tadjusted_p_value\tleading_edge_genes\trank_metric\twarnings\n"
        "TERM_POS\tPositive\t10\t4\t0.8\t1.6\t0.01\t0.02\tGENE1;GENE2\tsigned_log10_fdr_by_log2fc\t\n",
        encoding="utf-8",
    )
    return path


def _source_deg_entry(*, result_semantics: str) -> dict[str, object]:
    return ResultIndexEntry(result_id="deg-source", task_run_id="deg-run", task_type="deg", result_semantics=result_semantics, validation_status="passed").to_dict()


def _gsea_entry(table: Path, *, result_semantics: str, source_result_semantics: str) -> dict[str, object]:
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
        "dependency_snapshot": {"status": "passed", "packages": {"numpy": {"version": "n"}, "pandas": {"version": "p"}, "scipy": {"version": "s"}, "statsmodels": {"version": "sm"}}, "blockers": []},
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
