from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.enrichment.export import export_ora_review_table
from app.bioinformatics.enrichment.review import build_ora_result_review
from app.bioinformatics.results.models import RESULT_INDEX_SCHEMA_VERSION


def test_ora_result_review_summarizes_sorts_filters_and_preserves_boundaries(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    _write_result_index(tmp_path, [_ora_entry(table)])

    review = build_ora_result_review(tmp_path, sort_by="adjusted_p_value", significance_filter="significant")

    assert review["status"] == "passed"
    assert review["summary"]["term_total"] == 3
    assert review["summary"]["significant_term_count"] == 1
    assert review["summary"]["top_term_by_fdr"] == "Apoptosis"
    assert review["summary"]["source_deg_result_id"] == "deg-1"
    assert review["summary"]["dependency_versions"]["scipy"] == "fake-scipy"
    assert [row["term_id"] for row in review["rows"]] == ["TERM_A"]
    assert review["provenance"]["plot_artifacts"] == []
    assert review["provenance"]["report_artifacts"] == []
    assert review["provenance"]["report_ready_eligible"] is False
    assert "does not prove pathway activation" in review["guard_copy"]


def test_ora_review_export_is_table_only_not_report_ready(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    _write_result_index(tmp_path, [_ora_entry(table)])

    exported = export_ora_review_table(tmp_path, file_format="csv")

    assert exported["status"] == "passed"
    assert exported["report_ready_eligible"] is False
    assert exported["plot_artifacts"] == []
    assert exported["report_artifacts"] == []
    export_path = Path(str(exported["export_path"]))
    assert export_path.is_file()
    assert "term_id,term_name,overlap_count" in export_path.read_text(encoding="utf-8")


def test_ora_review_blocks_when_only_non_ora_results_exist(tmp_path: Path) -> None:
    _write_result_index(tmp_path, [{"result_id": "testing", "task_type": "deg", "result_semantics": "testing_level"}])

    review = build_ora_result_review(tmp_path)

    assert review["status"] == "blocked"
    assert "ora_result_not_found" in review["blockers"]
    assert review["rows"] == []
    assert review["excluded_results"][0]["result_semantics"] == "testing_level"


def _write_ora_table(root: Path) -> Path:
    path = root / "results" / "tables" / "ora.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "term_id\tterm_name\tgene_set_size\toverlap_count\toverlap_genes\tbackground_size\tselected_gene_count\tp_value\tadjusted_p_value\tenrichment_ratio\tsource_gene_list\twarnings\n"
        "TERM_A\tApoptosis\t2\t2\tTP53;BRCA1\t100\t10\t0.001\t0.003\t10\tselected\t\n"
        "TERM_B\tGrowth\t5\t1\tEGFR\t100\t10\t0.2\t0.3\t2\tselected\t\n"
        "TERM_C\tNo hit\t3\t0\t\t100\t10\t1\t1\t0\tselected\t\n",
        encoding="utf-8",
    )
    return path


def _ora_entry(table: Path) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "result_id": "ora-1",
        "task_run_id": "ora-run-1",
        "task_type": "ora_enrichment",
        "result_semantics": "formal_computed_result",
        "input_package_id": "ora-input-1",
        "ora_input_id": "ora-input-1",
        "source_dataset_id": "dataset-1",
        "source_repository_manifest": "standardized_data/repositories/repository_manifest.json",
        "source_deg_result_id": "deg-1",
        "source_result_semantics": "formal_computed_result",
        "gene_set_resource_id": "sets",
        "parameters_manifest": {"test_method": "hypergeometric", "fdr_threshold": 0.05},
        "engine_name": "python_scipy_statsmodels_ora_mvp",
        "engine_version": "0.1.0",
        "dependency_snapshot": {"status": "passed", "packages": {"scipy": {"version": "fake-scipy"}, "statsmodels": {"version": "fake-statsmodels"}}},
        "output_artifacts": [{"artifact_type": "ora_result_table", "path": str(table)}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": [],
        "blockers": [],
        "log_artifacts": [{"artifact_type": "controlled_ora_task_run_log", "path": "analysis_runs/ora/ora-run-1/task_run.json"}],
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
