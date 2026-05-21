from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.plots import build_ora_plot_gate, create_ora_plot_artifact
from app.bioinformatics.results.models import RESULT_INDEX_SCHEMA_VERSION, ResultIndexEntry
from app.bioinformatics.results.registry import load_registry


def test_formal_ora_barplot_artifact_registers_spec_only_and_keeps_report_disabled(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    _write_result_index(tmp_path, [_ora_entry(table)])

    gate = build_ora_plot_gate(tmp_path, result_id="ora-formal", plot_type="ora_barplot")
    result = create_ora_plot_artifact(tmp_path, result_id="ora-formal", plot_type="ora_barplot")

    assert gate["status"] == "passed"
    assert result["status"] == "passed"
    artifact = result["plot_artifact"]
    assert artifact["plot_type"] == "ora_barplot"
    assert artifact["source_task_type"] == "ora_enrichment"
    assert artifact["source_result_semantics"] == "formal_computed_result"
    assert artifact["plot_semantics"] == "formal_computed_result"
    assert artifact["image_artifacts"] == []
    assert artifact["plot_spec_artifact"]["rendering"] == "spec_only_no_image_dependency"
    assert artifact["plot_spec_artifact"]["source_result_id"] == "ora-formal"
    assert result["report_artifacts"] == []
    assert result["report_ready_eligible"] is False
    entry = load_registry(tmp_path)["results"][0]
    assert entry["plot_artifacts"][0]["plot_id"] == "ora-formal-ora_barplot-artifact"
    assert entry["report_ready_eligible"] is False
    assert entry["report_artifacts"] == []


def test_formal_ora_dotplot_artifact_uses_dotplot_spec(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    _write_result_index(tmp_path, [_ora_entry(table)])

    result = create_ora_plot_artifact(tmp_path, result_id="ora-formal", plot_type="ora_dotplot")

    assert result["status"] == "passed"
    assert result["plot_artifact"]["plot_type"] == "ora_dotplot"
    assert result["plot_artifact"]["plot_spec_artifact"]["size_field"] == "overlap_count"


def test_imported_derived_ora_plot_keeps_imported_warning_and_semantics(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    entry = _ora_entry(table, result_id="ora-imported", result_semantics="imported_external_result", source_result_semantics="imported_external_result")
    entry["warnings"] = ["imported_deg_derived_ora_not_biomedpilot_recomputed_deg_formal_ora"]
    _write_result_index(tmp_path, [entry])

    result = create_ora_plot_artifact(tmp_path, result_id="ora-imported", plot_type="ora_barplot")

    assert result["status"] == "passed"
    artifact = result["plot_artifact"]
    assert artifact["plot_semantics"] == "imported_external_result"
    assert artifact["source_result_semantics"] == "imported_external_result"
    assert "imported_ora_derived_plot_not_biomedpilot_recomputed_formal_plot" in artifact["warnings"]
    assert "plot_source_is_imported_external_result" in artifact["warnings"]


def test_ora_plot_blocks_preflight_testing_exploratory_sources(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    _write_result_index(
        tmp_path,
        [
            _ora_entry(table, result_id="preflight", result_semantics="preflight_only"),
            _ora_entry(table, result_id="testing", result_semantics="testing_level"),
            _ora_entry(table, result_id="exploratory", result_semantics="exploratory"),
        ],
    )

    for result_id, semantics in (("preflight", "preflight_only"), ("testing", "testing_level"), ("exploratory", "exploratory")):
        result = create_ora_plot_artifact(tmp_path, result_id=result_id, plot_type="ora_barplot")
        assert result["status"] == "blocked"
        assert f"ora_plot_source_semantics_not_allowed:{semantics}" in result["blockers"]


def test_ora_plot_blocks_deg_result_without_ora_result(tmp_path: Path) -> None:
    _write_result_index(tmp_path, [_deg_entry()])

    result = create_ora_plot_artifact(tmp_path, result_id="deg-only", plot_type="ora_barplot")

    assert result["status"] == "blocked"
    assert "ora_plot_requires_ora_enrichment_task_type" in result["blockers"]


def test_ora_plot_blocks_missing_invalid_and_nonnumeric_tables(tmp_path: Path) -> None:
    _write_result_index(tmp_path / "missing", [_ora_entry(tmp_path / "missing" / "missing.tsv")])
    missing = create_ora_plot_artifact(tmp_path / "missing", result_id="ora-formal", plot_type="ora_barplot")
    assert "ora_plot_source_table_missing" in missing["blockers"]

    invalid_table = tmp_path / "invalid" / "ora.tsv"
    invalid_table.parent.mkdir(parents=True, exist_ok=True)
    invalid_table.write_text("term_id\tterm_name\tp_value\nT1\tTerm\t0.01\n", encoding="utf-8")
    _write_result_index(tmp_path / "invalid", [_ora_entry(invalid_table)])
    invalid = create_ora_plot_artifact(tmp_path / "invalid", result_id="ora-formal", plot_type="ora_barplot")
    assert any("ora_plot_missing_table_column:adjusted_p_value" in item for item in invalid["blockers"])

    nonnumeric = tmp_path / "nonnumeric" / "ora.tsv"
    _write_ora_table(nonnumeric, p_value="not_numeric", adjusted_p_value="bad", enrichment_ratio="bad")
    _write_result_index(tmp_path / "nonnumeric", [_ora_entry(nonnumeric)])
    bad = create_ora_plot_artifact(tmp_path / "nonnumeric", result_id="ora-formal", plot_type="ora_barplot")
    assert any("non_numeric:p_value" in item for item in bad["blockers"])
    assert any("non_numeric:adjusted_p_value" in item for item in bad["blockers"])
    assert any("non_numeric:enrichment_ratio" in item for item in bad["blockers"])


def test_ora_plot_blocks_invalid_plot_parameters_and_type(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    _write_result_index(tmp_path, [_ora_entry(table)])

    unsupported = create_ora_plot_artifact(tmp_path, result_id="ora-formal", plot_type="gsea_plot")
    assert "unsupported_ora_plot_type:gsea_plot" in unsupported["blockers"]

    invalid = create_ora_plot_artifact(tmp_path, result_id="ora-formal", plot_type="ora_barplot", parameters={"top_n": 0, "sort_by": "rank_metric", "fdr_threshold": 2})
    assert "ora_plot_invalid_top_n" in invalid["blockers"]
    assert "ora_plot_invalid_sort_by" in invalid["blockers"]
    assert "ora_plot_invalid_fdr_threshold" in invalid["blockers"]


def _write_ora_table(path_or_root: Path, *, p_value: str = "0.001", adjusted_p_value: str = "0.003", enrichment_ratio: str = "10") -> Path:
    path = path_or_root if path_or_root.suffix else path_or_root / "ora.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "term_id\tterm_name\tgene_set_size\toverlap_count\toverlap_genes\tbackground_size\tselected_gene_count\tp_value\tadjusted_p_value\tenrichment_ratio\tsource_gene_list\twarnings\n"
        f"TERM_A\tApoptosis\t2\t2\tTP53;BRCA1\t100\t10\t{p_value}\t{adjusted_p_value}\t{enrichment_ratio}\tselected\t\n",
        encoding="utf-8",
    )
    return path


def _ora_entry(table: Path, *, result_id: str = "ora-formal", result_semantics: str = "formal_computed_result", source_result_semantics: str = "formal_computed_result") -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "result_id": result_id,
        "task_run_id": f"{result_id}-run",
        "task_type": "ora_enrichment",
        "result_semantics": result_semantics,
        "input_package_id": "ora-input-1",
        "ora_input_id": "ora-input-1",
        "source_dataset_id": "dataset-1",
        "source_repository_manifest": "standardized_data/repositories/repository_manifest.json",
        "source_deg_result_id": "deg-1",
        "source_result_semantics": source_result_semantics,
        "gene_set_resource_id": "sets",
        "parameters_manifest": {"test_method": "hypergeometric", "fdr_threshold": 0.05},
        "engine_name": "python_scipy_statsmodels_ora_mvp",
        "engine_version": "0.1.0",
        "dependency_snapshot": {"status": "passed", "packages": {"scipy": {"version": "fake"}, "statsmodels": {"version": "fake"}}},
        "output_artifacts": [{"artifact_type": "ora_result_table", "path": str(table)}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": [],
        "blockers": [],
        "log_artifacts": [{"artifact_type": "controlled_ora_task_run_log", "path": "analysis_runs/ora/run/task_run.json"}],
        "failure_reason": "",
        "created_at": now,
        "updated_at": now,
        "schema_version": "biomedpilot.result_index_entry.v1",
        "report_ready_eligible": False,
        "migration_status": "native_v2",
    }


def _deg_entry() -> dict[str, object]:
    return ResultIndexEntry(result_id="deg-only", task_run_id="deg-run", task_type="deg", result_semantics="formal_computed_result", validation_status="passed").to_dict()


def _write_result_index(root: Path, entries: list[dict[str, object]]) -> None:
    path = root / "results" / "summaries" / "result_index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": RESULT_INDEX_SCHEMA_VERSION, "results": entries}), encoding="utf-8")
