from __future__ import annotations

from pathlib import Path

from app.bioinformatics.enrichment_plot_report import (
    build_enrichment_plot_gate,
    create_enrichment_plot_artifact,
    create_enrichment_section_report_package,
    evaluate_enrichment_section_report_ready_gate,
)
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import load_registry, register_result


def test_enrichment_plot_artifact_requires_formal_enrichment_source(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    register_result(tmp_path, _entry("imported", "ora", "imported_external_result", table, "ora_result_table"))

    gate = build_enrichment_plot_gate(tmp_path, result_id="imported", plot_type="ora_dotplot")

    assert gate["status"] == "blocked"
    assert "enrichment_plot_requires_formal_computed_enrichment_result" in gate["blockers"]


def test_enrichment_plot_artifact_registers_svg_without_report_ready(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    register_result(tmp_path, _entry("ora-formal", "ora", "formal_computed_result", table, "ora_result_table"))

    result = create_enrichment_plot_artifact(tmp_path, result_id="ora-formal", plot_type="ora_dotplot")

    assert result["status"] == "passed"
    artifact = result["plot_artifact"]
    assert artifact["plot_artifact_scope"] == "formal_enrichment_plot"
    assert artifact["source_result_semantics"] == "formal_computed_result"
    svg = tmp_path / artifact["image_artifacts"][0]["path"]
    assert svg.is_file()
    assert "No clinical conclusion" in svg.read_text(encoding="utf-8")
    entry = load_registry(tmp_path)["results"][0]
    assert entry["plot_artifacts"]
    assert entry["report_ready_eligible"] is False


def test_enrichment_section_report_gate_requires_plot_or_table_only_mode(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    register_result(tmp_path, _entry("ora-formal", "ora", "formal_computed_result", table, "ora_result_table"))

    blocked = evaluate_enrichment_section_report_ready_gate(tmp_path, result_id="ora-formal")
    table_only = evaluate_enrichment_section_report_ready_gate(tmp_path, result_id="ora-formal", allow_table_only_report=True)

    assert blocked["status"] == "blocked"
    assert "enrichment_report_ready_requires_plot_artifact_or_table_only_mode" in blocked["blockers"]
    assert table_only["status"] == "eligible_for_enrichment_section_report_ready"
    assert "enrichment_table_only_report_mode_no_plot_artifact" in table_only["warnings"]


def test_enrichment_section_report_package_is_section_only_and_registers_artifact(tmp_path: Path) -> None:
    table = _write_gsea_table(tmp_path)
    register_result(tmp_path, _entry("gsea-formal", "gsea_preranked", "formal_computed_result", table, "gsea_preranked_result_table"))
    plot = create_enrichment_plot_artifact(tmp_path, result_id="gsea-formal", plot_type="gsea_preranked_plot")
    assert plot["status"] == "passed"

    package = create_enrichment_section_report_package(tmp_path, result_id="gsea-formal")

    assert package["status"] == "enrichment_section_report_package_created"
    assert package["section_scope"] == "formal_enrichment_only"
    assert package["full_integrated_report_enabled"] is False
    assert package["clinical_interpretation_enabled"] is False
    package_path = Path(package["package_path"])
    assert (package_path / "enrichment_section_report.md").is_file()
    assert (package_path / "README_limitations.md").is_file()
    assert (package_path / "manifests" / "gate_snapshot.json").is_file()
    entry = load_registry(tmp_path)["results"][0]
    assert entry["report_ready_eligible"] is True
    assert entry["report_artifacts"][0]["section_scope"] == "formal_enrichment_only"


def _write_ora_table(tmp_path: Path) -> Path:
    path = tmp_path / "ora.tsv"
    path.write_text(
        "ID\tDescription\tGeneRatio\tBgRatio\tpvalue\tp.adjust\tqvalue\tgeneID\tCount\n"
        "DNA_DAMAGE\tDNA damage response\t3/3\t3/5\t0.01\t0.02\t0.02\tTP53/CDKN1A/EGFR\t3\n",
        encoding="utf-8",
    )
    return path


def _write_gsea_table(tmp_path: Path) -> Path:
    path = tmp_path / "gsea.tsv"
    path.write_text(
        "pathway\tES\tNES\tpval\tpadj\tleadingEdge\tsize\n"
        "DNA_DAMAGE\t0.8\t1.7\t0.01\t0.03\tTP53/CDKN1A\t3\n",
        encoding="utf-8",
    )
    return path


def _entry(result_id: str, task_type: str, semantics: str, table: Path, artifact_type: str) -> ResultIndexEntry:
    return ResultIndexEntry(
        result_id=result_id,
        task_run_id=f"task-{result_id}",
        task_type=task_type,
        result_semantics=semantics,
        input_package_id=f"input-{result_id}",
        source_dataset_id="controlled_enrichment_fixture",
        source_repository_manifest="controlled_fixture://enrichment/test",
        parameters_manifest={"analysis_type": task_type, "p_value_cutoff": 0.05, "fdr_cutoff": 0.05},
        engine_name="r_fgsea_preranked" if task_type == "gsea_preranked" else "r_clusterProfiler_enricher",
        engine_version="1",
        dependency_snapshot={"status": "passed"},
        output_artifacts=({"artifact_type": artifact_type, "path": str(table)},),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        report_ready_eligible=False,
    )
