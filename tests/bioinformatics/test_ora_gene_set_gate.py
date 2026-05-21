from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.enrichment.gene_set_gate import build_ora_gene_set_resource_gate


def test_valid_local_gmt_passes_gene_set_gate(tmp_path: Path) -> None:
    gmt = _write_gmt(tmp_path / "sets.gmt")

    gate = build_ora_gene_set_resource_gate(tmp_path, resource_path=gmt)

    assert gate["status"] == "passed"
    assert gate["term_count"] == 2
    assert gate["gene_count"] == 3
    assert gate["resource_format"] == "GMT"


def test_invalid_gmt_is_blocked(tmp_path: Path) -> None:
    gmt = tmp_path / "bad.gmt"
    gmt.write_text("term_without_genes\tdescription\n", encoding="utf-8")

    gate = build_ora_gene_set_resource_gate(tmp_path, resource_path=gmt)

    assert gate["status"] == "blocked"
    assert any("expected_name_description_and_gene" in item for item in gate["blockers"])


def test_species_and_gene_id_mismatch_are_blocked_when_known(tmp_path: Path) -> None:
    gmt = _write_gmt(tmp_path / "sets.gmt")
    _write_registry(tmp_path, gmt, species="mouse", gene_id_type="entrez")

    gate = build_ora_gene_set_resource_gate(tmp_path, resource_id="custom_sets", expected_species="human", expected_gene_id_type="symbol")

    assert "ora_gene_set_species_mismatch:mouse!=human" in gate["blockers"]
    assert "ora_gene_set_gene_id_mismatch:entrez!=symbol" in gate["blockers"]


def test_msigdb_without_manual_license_or_source_is_blocked(tmp_path: Path) -> None:
    gmt = _write_gmt(tmp_path / "msigdb.gmt")
    _write_registry(tmp_path, gmt, resource_id="msigdb_hallmark", name="MSigDB Hallmark", source_name="", license_note="")

    gate = build_ora_gene_set_resource_gate(tmp_path, resource_id="msigdb_hallmark")

    assert "msigdb_manual_license_or_source_missing" in gate["blockers"]


def _write_gmt(path: Path) -> Path:
    path.write_text("TERM_A\tdesc\tTP53\tBRCA1\nTERM_B\tdesc\tEGFR\n", encoding="utf-8")
    return path


def _write_registry(
    root: Path,
    gmt: Path,
    *,
    resource_id: str = "custom_sets",
    name: str = "Custom sets",
    species: str = "human",
    gene_id_type: str = "symbol",
    source_name: str = "User import",
    license_note: str = "User confirmed local GMT source.",
) -> None:
    path = root / "user_data" / "bioinformatics" / "gene_sets" / "gene_set_registry.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.gene_set_registry.v1",
                "resources": [
                    {
                        "resource_id": resource_id,
                        "name": name,
                        "collection_type": "Custom",
                        "species": species,
                        "gene_id_type": gene_id_type,
                        "source_type": "user_import",
                        "source_name": source_name,
                        "license_note": license_note,
                        "local_path": str(gmt),
                        "status": "available",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
