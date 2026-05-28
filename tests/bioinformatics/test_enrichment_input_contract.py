from __future__ import annotations

from pathlib import Path

from app.bioinformatics.enrichment_input_contract import (
    build_enrichment_background_universe,
    build_enrichment_identifier_compatibility_gate,
    build_enrichment_input_contract_gate,
    build_enrichment_source_derivation_manifest,
)
from app.bioinformatics.gene_set_resources import import_gmt_file, select_gene_set
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


def test_enrichment_input_contract_passes_for_formal_deg_ora_source(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path)
    select_gene_set(tmp_path, str(resource["resource_id"]))
    _register_deg_source(tmp_path, "deg-ora")

    gate = build_enrichment_input_contract_gate(tmp_path, analysis_type="ora", source_result_id="deg-ora", resource_id=str(resource["resource_id"]))

    assert gate["schema_version"] == "biomedpilot.enrichment_input_contract_gate.v1"
    assert gate["status"] == "passed"
    assert gate["background_universe"]["gene_count"] == 4
    assert gate["source_derivation_manifest"]["selected_gene_count"] == 2
    assert gate["identifier_compatibility_gate"]["status"] == "passed"
    assert gate["resource_lock"]["status"] == "passed"
    assert gate["semantic_boundary"] == "input_contract_only_not_enrichment_execution"


def test_enrichment_input_contract_passes_for_preranked_gsea_metric(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path)
    select_gene_set(tmp_path, str(resource["resource_id"]))
    _register_deg_source(tmp_path, "deg-gsea")

    gate = build_enrichment_input_contract_gate(tmp_path, analysis_type="gsea_preranked", source_result_id="deg-gsea", resource_id=str(resource["resource_id"]), ranking_metric="statistic")

    assert gate["status"] == "passed"
    assert gate["source_derivation_manifest"]["ranked_gene_count"] == 4
    assert gate["source_derivation_manifest"]["ranking_metric"] == "statistic"


def test_enrichment_input_contract_blocks_imported_or_preflight_source(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path)
    select_gene_set(tmp_path, str(resource["resource_id"]))
    _register_deg_source(tmp_path, "imported", semantics="imported_external_result")

    gate = build_enrichment_input_contract_gate(tmp_path, analysis_type="ora", source_result_id="imported", resource_id=str(resource["resource_id"]))

    assert gate["status"] == "blocked"
    assert "enrichment_source_result_not_formal:imported_external_result" in gate["blockers"]


def test_enrichment_input_contract_blocks_identifier_mismatch(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path, gene_id_type="entrez")
    select_gene_set(tmp_path, str(resource["resource_id"]))
    _register_deg_source(tmp_path, "deg-symbol", gene_id_type="symbol")

    gate = build_enrichment_input_contract_gate(tmp_path, analysis_type="ora", source_result_id="deg-symbol", resource_id=str(resource["resource_id"]), required_gene_id_type="symbol")

    assert gate["status"] == "blocked"
    assert "resource_gene_id_type_mismatch:entrez!=symbol" in gate["blockers"]
    assert "source_resource_gene_id_type_mismatch:symbol!=entrez" in gate["blockers"]
    assert gate["identifier_compatibility_gate"]["mapping_policy"] == "no_automatic_identifier_mapping_without_audited_mapping_manifest"


def test_background_universe_blocks_unsupported_strategy_and_empty_rows() -> None:
    manifest = build_enrichment_background_universe(rows=[], source_result_id="deg-1", source_gene_id_type="symbol", background_strategy="implicit_visible_rows")

    assert manifest["status"] == "blocked"
    assert "unsupported_background_strategy:implicit_visible_rows" in manifest["blockers"]
    assert "background_universe_empty" in manifest["blockers"]


def test_source_derivation_blocks_empty_ora_and_bad_gsea_metric() -> None:
    rows = [{"feature_id": "f1", "gene_symbol": "TP53", "log2_fold_change": "0.1", "adjusted_p_value": "0.9", "statistic": "1"}]

    ora = build_enrichment_source_derivation_manifest(rows=rows, analysis_type="ora", source_result_id="deg", log2fc_threshold=1.0, fdr_cutoff=0.05)
    gsea = build_enrichment_source_derivation_manifest(rows=rows, analysis_type="gsea_preranked", source_result_id="deg", ranking_metric="unsupported")

    assert "ora_selected_gene_set_empty" in ora["blockers"]
    assert "unsupported_gsea_ranking_metric:unsupported" in gsea["blockers"]
    assert "gsea_ranking_metric_empty" in gsea["blockers"]


def test_identifier_compatibility_blocks_unknown_without_mapping_manifest() -> None:
    gate = build_enrichment_identifier_compatibility_gate(source_gene_id_type="unknown", resource_lock={"gene_id_type": "symbol", "status": "passed"}, required_gene_id_type="symbol")

    assert gate["status"] == "blocked"
    assert "source_gene_id_type_unknown" in gate["blockers"]
    assert "source_gene_id_type_mismatch:unknown!=symbol" in gate["blockers"]


def _import_resource(tmp_path: Path, *, gene_id_type: str = "symbol") -> dict[str, object]:
    gmt = tmp_path / f"resource_{gene_id_type}.gmt"
    gmt.write_text("DNA_DAMAGE\tcurated\tTP53\tBAX\tCDKN1A\nINTERFERON\tcurated\tSTAT1\tIRF1\n", encoding="utf-8")
    return import_gmt_file(
        tmp_path,
        gmt,
        {
            "name": "Curated pathways",
            "collection_type": "Custom",
            "species": "human",
            "gene_id_type": gene_id_type,
            "source_name": "unit-test-curation",
            "source_url": "https://example.test/gmt",
            "license_note": "test-only user supplied resource",
            "version": "2026-test",
        },
    )["resource"]


def _register_deg_source(tmp_path: Path, result_id: str, *, gene_id_type: str = "symbol", semantics: str = "formal_computed_result") -> None:
    table = tmp_path / "results" / "tables" / f"{result_id}.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "feature_id\tgene_symbol\tlog2_fold_change\tstatistic\tp_value\tadjusted_p_value\tsignificance_label\n"
        "f1\tTP53\t1.5\t3.0\t0.01\t0.02\tup\n"
        "f2\tBAX\t-1.3\t-2.2\t0.02\t0.04\tdown\n"
        "f3\tSTAT1\t0.6\t1.1\t0.2\t0.4\tnot_significant\n"
        "f4\tGAPDH\t0.1\t0.1\t0.9\t0.95\tnot_significant\n",
        encoding="utf-8",
    )
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id=result_id,
            task_run_id=f"{result_id}-task",
            task_type="deg",
            result_semantics=semantics,
            input_package_id="deg-ready",
            parameters_manifest={"gene_id_type": gene_id_type},
            engine_name="test_deg",
            engine_version="1",
            dependency_snapshot={"status": "passed"},
            output_artifacts=({"artifact_type": "deg_result_table", "path": str(table.relative_to(tmp_path)), "schema": "biomedpilot.deg_result_table.v1"},),
            validation_status="passed",
        ),
    )
