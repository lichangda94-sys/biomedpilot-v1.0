from __future__ import annotations

from pathlib import Path

from app.bioinformatics.enrichment_resources import build_enrichment_resource_gate, build_enrichment_resource_registry
from app.bioinformatics.gene_set_resources import import_gmt_file, select_gene_set


def test_enrichment_resource_registry_records_provenance_checksum_and_scope(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path)
    select_gene_set(tmp_path, str(resource["resource_id"]))

    registry = build_enrichment_resource_registry(tmp_path)

    assert registry["schema_version"] == "biomedpilot.enrichment_resource_registry.v1"
    assert registry["network_downloads"] is False
    assert registry["auto_install"] is False
    row = registry["resources"][0]
    catalog = {item["resource_id"]: item for item in registry["known_resource_catalog"]}
    assert {"reactome_pathways", "go_bp_human", "go_cc_human", "go_mf_human", "kegg_hsa_pathways", "msigdb_hallmark_user_import", "custom_gmt_import"} <= set(catalog)
    assert catalog["msigdb_hallmark_user_import"]["downloadable"] is False
    assert catalog["reactome_pathways"]["policy"] == "user_triggered_only_no_silent_download"
    assert row["resource_id"] == resource["resource_id"]
    assert row["species"] == "human"
    assert row["gene_id_type"] == "symbol"
    assert row["source_name"] == "unit-test-curation"
    assert row["license_note"] == "test-only user supplied resource"
    assert row["version"] == "2026-test"
    assert row["checksum"]
    assert row["checksum_algorithm"] == "sha256"
    assert row["allowed_analysis_types"] == ["ora", "gsea_preranked"]
    assert row["resource_semantics"] == "enrichment_gene_set_resource_not_analysis_result"


def test_enrichment_resource_gate_passes_for_selected_matching_resource(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path)
    select_gene_set(tmp_path, str(resource["resource_id"]))

    gate = build_enrichment_resource_gate(tmp_path, analysis_type="ora", required_species="human", required_gene_id_type="symbol")

    assert gate["schema_version"] == "biomedpilot.enrichment_resource_gate.v1"
    assert gate["status"] == "passed"
    assert gate["selected_resource_id"] == resource["resource_id"]
    assert gate["semantic_boundary"] == "resource_gate_only_not_enrichment_execution"
    assert gate["network_downloads"] is False
    assert gate["auto_install"] is False


def test_enrichment_resource_gate_blocks_missing_selection_and_mismatches(tmp_path: Path) -> None:
    gate = build_enrichment_resource_gate(tmp_path, analysis_type="gsea_preranked", required_species="human", required_gene_id_type="symbol")

    assert gate["status"] == "blocked"
    assert "enrichment_resource_not_selected" in gate["blockers"]

    resource = _import_resource(tmp_path, gene_id_type="entrez")
    select_gene_set(tmp_path, str(resource["resource_id"]))
    mismatch = build_enrichment_resource_gate(tmp_path, analysis_type="gsea_preranked", required_species="human", required_gene_id_type="symbol")

    assert mismatch["status"] == "blocked"
    assert "resource_gene_id_type_mismatch:entrez!=symbol" in mismatch["blockers"]


def test_enrichment_resource_gate_blocks_missing_license_version_and_source(tmp_path: Path) -> None:
    source = _write_gmt(tmp_path / "minimal.gmt")
    resource = import_gmt_file(tmp_path, source, {"species": "human", "gene_id_type": "symbol"})["resource"]
    select_gene_set(tmp_path, str(resource["resource_id"]))

    gate = build_enrichment_resource_gate(tmp_path, analysis_type="ora", required_species="human", required_gene_id_type="symbol")

    assert gate["status"] == "blocked"
    assert "resource_license_note_missing" in gate["blockers"]
    assert "resource_version_missing" in gate["blockers"]


def _import_resource(tmp_path: Path, *, gene_id_type: str = "symbol") -> dict[str, object]:
    source = _write_gmt(tmp_path / f"resource_{gene_id_type}.gmt")
    return import_gmt_file(
        tmp_path,
        source,
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


def _write_gmt(path: Path) -> Path:
    path.write_text("DNA_DAMAGE\tcurated\tTP53\tBAX\tCDKN1A\nINTERFERON\tcurated\tSTAT1\tIRF1\n", encoding="utf-8")
    return path
