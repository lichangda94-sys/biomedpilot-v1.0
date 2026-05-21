from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.gsea import build_gsea_result_review, export_gsea_review_table
from app.bioinformatics.results.registry import register_result


def test_gsea_result_review_summarizes_filters_and_exports_table_only(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "gsea.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "term_id\tterm_name\tset_size\toverlap_size\tenrichment_score\tnormalized_enrichment_score\tp_value\tadjusted_p_value\tleading_edge_genes\trank_metric\twarnings\n"
        "T1\tPositive\t10\t4\t0.8\t1.6\t0.01\t0.02\tGENE1;GENE2\tsigned_log10_fdr_by_log2fc\t\n"
        "T2\tNegative\t10\t4\t-0.7\t-1.4\t0.03\t0.2\tGENE8;GENE9\tsigned_log10_fdr_by_log2fc\t\n",
        encoding="utf-8",
    )
    register_result(tmp_path, _gsea_entry(table))

    review = build_gsea_result_review(tmp_path, sort_by="normalized_enrichment_score", significance_filter="significant")

    assert review["status"] == "passed"
    assert review["summary"]["term_total"] == 2
    assert review["summary"]["significant_term_count"] == 1
    assert review["summary"]["top_positive_nes_term"] == "Positive"
    assert review["rows"][0]["significance_label"] == "significant_positive"
    assert "clinical interpretation" in review["guard_copy"]
    assert review["disabled_downstream"]["plot"].startswith("GSEA plot artifact waits")

    exported = export_gsea_review_table(tmp_path, result_id="gsea-1", file_format="csv")
    assert exported["status"] == "passed"
    assert exported["report_ready_eligible"] is False
    assert Path(str(exported["export_path"])).is_file()


def test_gsea_result_review_excludes_ora_and_preflight_results(tmp_path: Path) -> None:
    register_result(
        tmp_path,
        {
            **_gsea_entry(tmp_path / "missing.tsv"),
            "result_id": "preflight",
            "result_semantics": "preflight_only",
            "output_artifacts": [{"artifact_type": "gsea_result_table", "path": "missing.tsv"}],
        },
    )
    register_result(
        tmp_path,
        {
            **_gsea_entry(tmp_path / "missing.tsv"),
            "result_id": "ora",
            "task_type": "ora_enrichment",
            "output_artifacts": [{"artifact_type": "ora_result_table", "path": "missing.tsv"}],
        },
    )

    review = build_gsea_result_review(tmp_path)

    assert review["status"] == "blocked"
    assert "gsea_result_not_found" in review["blockers"]
    assert {item["reason"] for item in review["excluded_results"]} == {"not_controlled_preranked_gsea_result"}


def _gsea_entry(table: Path) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "result_id": "gsea-1",
        "task_run_id": "gsea-run-1",
        "task_type": "gsea_preranked",
        "result_semantics": "formal_computed_result",
        "input_package_id": "gsea-input-1",
        "gsea_input_id": "gsea-input-1",
        "source_dataset_id": "dataset-1",
        "source_repository_manifest": "standardized_data/repositories/repository_manifest.json",
        "source_deg_result_id": "deg-1",
        "source_result_semantics": "formal_computed_result",
        "gene_set_resource_id": "sets",
        "parameters_manifest": {"rank_metric": "signed_log10_fdr_by_log2fc", "fdr_threshold": 0.05, "permutation_type": "gene_set", "permutation_count": 100, "random_seed": 1},
        "engine_name": "python_preranked_gsea_mvp",
        "engine_version": "0.1.0",
        "dependency_snapshot": {"status": "passed", "packages": {"numpy": {"version": "n"}, "pandas": {"version": "p"}, "scipy": {"version": "s"}, "statsmodels": {"version": "sm"}}},
        "output_artifacts": [{"artifact_type": "gsea_result_table", "path": str(table.relative_to(table.parents[2])) if "results" in table.parts else str(table)}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": [],
        "blockers": [],
        "log_artifacts": [{"artifact_type": "controlled_gsea_task_run_log", "path": "analysis_runs/gsea/run/task_run.json"}],
        "failure_reason": "",
        "created_at": now,
        "updated_at": now,
        "schema_version": "biomedpilot.result_index_entry.v1",
        "report_ready_eligible": False,
        "migration_status": "native_v2",
    }
