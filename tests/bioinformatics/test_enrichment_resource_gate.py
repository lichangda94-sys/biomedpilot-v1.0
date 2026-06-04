from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.enrichment_resources import (
    build_enrichment_library_policy,
    build_enrichment_resource_gate,
    build_enrichment_resource_lock,
    build_enrichment_resource_registry,
    write_enrichment_resource_lock_manifest,
)
from app.bioinformatics.gene_set_resources import GENE_SET_REGISTRY, RUNTIME_GENE_SET_DOWNLOAD_POLICY, import_gmt_file, select_gene_set


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
    assert catalog["reactome_pathways"]["policy"] == RUNTIME_GENE_SET_DOWNLOAD_POLICY
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


def test_enrichment_library_policy_records_supported_libraries_without_execution(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path, collection_type="GO_BP")
    select_gene_set(tmp_path, str(resource["resource_id"]))

    policy = build_enrichment_library_policy(tmp_path, analysis_type="ora")

    assert policy["schema_version"] == "biomedpilot.enrichment_library_policy.v1"
    assert policy["status"] == "passed"
    assert policy["policy_boundary"] == "library_policy_only_no_download_no_execution"
    assert policy["network_downloads"] is False
    assert policy["auto_install"] is False
    rows = {item["collection_type"]: item for item in policy["library_policies"]}
    assert rows["GO_BP"]["backend_capabilities"]["ora"] == ["ora_go"]
    assert rows["GO_BP"]["acquisition_policy"] == "import_or_prelocked_resource_required"
    assert rows["GO_BP"]["download_policy"] == RUNTIME_GENE_SET_DOWNLOAD_POLICY
    assert rows["Reactome"]["backend_capabilities"]["ora"] == ["ora_reactome"]
    assert rows["Hallmark"]["acquisition_policy"] == "user_provided_licensed_gmt_only"
    assert rows["Hallmark"]["requires_user_import"] is True


def test_enrichment_resource_lock_passes_for_immutable_selected_resource(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path, collection_type="GO_BP")
    select_gene_set(tmp_path, str(resource["resource_id"]))
    before = _file_set(tmp_path)

    lock = build_enrichment_resource_lock(tmp_path, analysis_type="ora", required_species="human", required_gene_id_type="symbol")

    assert lock["schema_version"] == "biomedpilot.enrichment_resource_lock.v1"
    assert lock["status"] == "passed"
    assert lock["resource_id"] == resource["resource_id"]
    assert lock["collection_type"] == "GO_BP"
    assert lock["library_family"] == "Gene Ontology"
    assert lock["source_version"] == "2026-test"
    assert lock["checksum"]
    assert lock["lock_id"].startswith(f"ora:{resource['resource_id']}:")
    assert lock["backend_capability_requirements"] == ["ora_go"]
    assert "checksum" in lock["immutable_fields"]
    assert lock["semantic_boundary"] == "resource_lock_only_not_enrichment_execution"
    assert lock["network_downloads"] is False
    assert lock["auto_install"] is False
    assert _file_set(tmp_path) == before


def test_enrichment_resource_lock_blocks_missing_version_license_and_checksum(tmp_path: Path) -> None:
    source = _write_gmt(tmp_path / "minimal.gmt")
    resource = import_gmt_file(tmp_path, source, {"species": "human", "gene_id_type": "symbol"})["resource"]
    select_gene_set(tmp_path, str(resource["resource_id"]))

    lock = build_enrichment_resource_lock(tmp_path, analysis_type="ora", required_species="human", required_gene_id_type="symbol")

    assert lock["status"] == "blocked"
    assert "resource_license_note_missing" in lock["blockers"]
    assert "resource_version_missing" in lock["blockers"]
    assert "resource_license_policy_not_recorded" in lock["blockers"]
    assert "resource_source_version_unknown" in lock["blockers"]


def test_enrichment_resource_lock_blocks_msigdb_without_user_import(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path, collection_type="Hallmark")
    resource["source_type"] = "configured"
    _write_registry_resource(tmp_path, resource)
    select_gene_set(tmp_path, str(resource["resource_id"]))

    lock = build_enrichment_resource_lock(tmp_path, analysis_type="gsea_preranked", required_species="human", required_gene_id_type="symbol")

    assert lock["status"] == "blocked"
    assert "resource_requires_user_import:Hallmark" in lock["blockers"]
    assert lock["acquisition_policy"] == "user_provided_licensed_gmt_only"


def test_write_enrichment_resource_lock_manifest_is_explicit(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path)
    select_gene_set(tmp_path, str(resource["resource_id"]))

    lock = write_enrichment_resource_lock_manifest(tmp_path, analysis_type="ora")

    manifest_path = Path(str(lock["manifest_path"]))
    assert manifest_path.is_file()
    assert manifest_path.name == f"ora_{resource['resource_id']}_resource_lock.json"
    assert "manifests/enrichment" in str(manifest_path)


def _import_resource(tmp_path: Path, *, gene_id_type: str = "symbol", collection_type: str = "Custom") -> dict[str, object]:
    source = _write_gmt(tmp_path / f"resource_{gene_id_type}.gmt")
    return import_gmt_file(
        tmp_path,
        source,
        {
            "name": "Curated pathways",
            "collection_type": collection_type,
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


def _file_set(root: Path) -> set[str]:
    return {str(item.relative_to(root)) for item in root.rglob("*") if item.is_file()}


def _write_registry_resource(tmp_path: Path, resource: dict[str, object]) -> None:
    registry_path = tmp_path / GENE_SET_REGISTRY
    payload = {
        "schema_version": "biomedpilot.gene_set_registry.v1",
        "project_root": str(tmp_path),
        "resources": [resource],
    }
    registry_path.write_text(json.dumps(payload), encoding="utf-8")
