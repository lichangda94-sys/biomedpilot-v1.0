from __future__ import annotations

from pathlib import Path

from app.bioinformatics.enrichment_e2e_audit import audit_enrichment_layer_acceptance
from app.bioinformatics.enrichment_plot_report import create_enrichment_plot_artifact, create_enrichment_section_report_package
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


def test_enrichment_e2e_audit_passes_for_formal_section_package_and_excludes_imported(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    register_result(tmp_path, _entry("ora-formal", "formal_computed_result", table))
    register_result(tmp_path, _entry("ora-imported", "imported_external_result", table))
    plot = create_enrichment_plot_artifact(tmp_path, result_id="ora-formal", plot_type="ora_dotplot")
    assert plot["status"] == "passed"
    package = create_enrichment_section_report_package(tmp_path, result_id="ora-formal")
    assert package["status"] == "enrichment_section_report_package_created"

    audit = audit_enrichment_layer_acceptance(tmp_path, result_id="ora-formal")

    assert audit["status"] == "passed"
    assert audit["checks"]["review_excludes_non_formal"] is True
    assert audit["checks"]["section_report_gate_is_section_only"] is True
    assert audit["checks"]["non_formal_outputs_not_promoted"] is True
    assert audit["capability_matrix"]["reactomepa_msigdbr_policy"] == "blocked_until_external_detector_and_resource_gates_pass"


def test_enrichment_e2e_audit_blocks_without_formal_result(tmp_path: Path) -> None:
    audit = audit_enrichment_layer_acceptance(tmp_path)

    assert audit["status"] == "blocked"
    assert "formal_enrichment_result_selected" in audit["blockers"]


def _write_ora_table(tmp_path: Path) -> Path:
    path = tmp_path / "ora.tsv"
    path.write_text(
        "ID\tDescription\tGeneRatio\tBgRatio\tpvalue\tp.adjust\tqvalue\tgeneID\tCount\n"
        "DNA_DAMAGE\tDNA damage response\t3/3\t3/5\t0.01\t0.02\t0.02\tTP53/CDKN1A/EGFR\t3\n",
        encoding="utf-8",
    )
    return path


def _entry(result_id: str, semantics: str, table: Path) -> ResultIndexEntry:
    return ResultIndexEntry(
        result_id=result_id,
        task_run_id=f"task-{result_id}",
        task_type="ora",
        result_semantics=semantics,
        input_package_id=f"input-{result_id}",
        source_dataset_id="controlled_enrichment_fixture",
        source_repository_manifest="controlled_fixture://enrichment/test",
        parameters_manifest={"analysis_type": "ora", "p_value_cutoff": 0.05, "fdr_cutoff": 0.05},
        engine_name="r_clusterProfiler_enricher",
        engine_version="1",
        dependency_snapshot={"status": "passed"},
        output_artifacts=({"artifact_type": "ora_result_table", "path": str(table)},),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        report_ready_eligible=False,
    )
