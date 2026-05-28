from __future__ import annotations

from pathlib import Path

from app.bioinformatics.enrichment_result_review import build_enrichment_result_review, export_enrichment_review_table
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


def test_enrichment_result_review_only_includes_formal_ora_and_excludes_imported(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    register_result(tmp_path, _entry("ora-formal", "ora", "formal_computed_result", table, "ora_result_table"))
    register_result(tmp_path, _entry("ora-imported", "ora", "imported_external_result", table, "ora_result_table"))

    review = build_enrichment_result_review(tmp_path, result_id="ora-formal")

    assert review["status"] == "passed"
    assert review["summary"]["term_count"] == 2
    assert review["summary"]["significant_term_count"] == 1
    assert review["rows"][0]["term_id"] == "DNA_DAMAGE"
    assert review["plot_status"] == "disabled_until_enrichment_plot_gate"
    assert review["report_status"] == "disabled_until_enrichment_section_report_gate"
    assert "clinical conclusion" in review["guard_copy"]
    excluded = {item["result_id"]: item for item in review["excluded_results"]}
    assert excluded["ora-imported"]["reason"] == "not_formal_computed_enrichment_result"


def test_enrichment_result_review_supports_gsea_filters_and_sort(tmp_path: Path) -> None:
    table = _write_gsea_table(tmp_path)
    register_result(tmp_path, _entry("gsea-formal", "gsea_preranked", "formal_computed_result", table, "gsea_preranked_result_table"))

    review = build_enrichment_result_review(tmp_path, result_id="gsea-formal", significance_filter="positive_enrichment", sort_by="NES")

    assert review["status"] == "passed"
    assert [row["term_id"] for row in review["rows"]] == ["DNA_DAMAGE"]
    assert review["summary"]["engine"] == "r_fgsea_preranked"


def test_enrichment_review_export_tsv_and_csv_without_report_ready(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    register_result(tmp_path, _entry("ora-formal", "ora", "formal_computed_result", table, "ora_result_table"))

    tsv = export_enrichment_review_table(tmp_path, result_id="ora-formal", file_format="tsv")
    csv = export_enrichment_review_table(tmp_path, result_id="ora-formal", file_format="csv")

    assert tsv["status"] == "exported"
    assert csv["status"] == "exported"
    assert Path(tsv["export_path"]).is_file()
    assert Path(csv["export_path"]).read_text(encoding="utf-8").startswith("ID,Description")
    assert csv["report_ready_eligible"] is False
    assert csv["plot_artifacts"] == []
    assert csv["report_artifacts"] == []


def test_enrichment_review_blocks_missing_formal_result(tmp_path: Path) -> None:
    review = build_enrichment_result_review(tmp_path, result_id="missing")

    assert review["status"] == "blocked"
    assert "formal_enrichment_result_not_found" in review["blockers"]


def _write_ora_table(tmp_path: Path) -> Path:
    path = tmp_path / "ora.tsv"
    path.write_text(
        "ID\tDescription\tGeneRatio\tBgRatio\tpvalue\tp.adjust\tqvalue\tgeneID\tCount\n"
        "DNA_DAMAGE\tDNA damage response\t3/3\t3/5\t0.01\t0.02\t0.02\tTP53/CDKN1A/EGFR\t3\n"
        "HOUSEKEEPING\tHousekeeping genes\t1/3\t2/5\t0.5\t0.8\t0.8\tGAPDH\t1\n",
        encoding="utf-8",
    )
    return path


def _write_gsea_table(tmp_path: Path) -> Path:
    path = tmp_path / "gsea.tsv"
    path.write_text(
        "pathway\tES\tNES\tpval\tpadj\tleadingEdge\tsize\n"
        "DNA_DAMAGE\t0.8\t1.7\t0.01\t0.03\tTP53/CDKN1A\t3\n"
        "HOUSEKEEPING\t-0.5\t-1.2\t0.2\t0.4\tGAPDH/ACTB\t2\n",
        encoding="utf-8",
    )
    return path


def _entry(result_id: str, task_type: str, semantics: str, table: Path, artifact_type: str) -> ResultIndexEntry:
    engine_name = "r_fgsea_preranked" if task_type == "gsea_preranked" else "r_clusterProfiler_enricher"
    return ResultIndexEntry(
        result_id=result_id,
        task_run_id=f"task-{result_id}",
        task_type=task_type,
        result_semantics=semantics,
        input_package_id=f"input-{result_id}",
        source_dataset_id="controlled_enrichment_fixture",
        source_repository_manifest="controlled_fixture://enrichment/test",
        parameters_manifest={"analysis_type": task_type, "p_value_cutoff": 0.05, "fdr_cutoff": 0.05},
        engine_name=engine_name,
        engine_version="1",
        dependency_snapshot={"status": "passed"},
        output_artifacts=({"artifact_type": artifact_type, "path": str(table)},),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        report_ready_eligible=False,
    )
