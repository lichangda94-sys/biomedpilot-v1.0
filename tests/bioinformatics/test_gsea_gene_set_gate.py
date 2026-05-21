from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.gsea import build_gsea_gene_set_resource_gate


def test_valid_gmt_with_ranked_gene_overlap_passes(tmp_path: Path) -> None:
    ranked = _write_ranked(tmp_path)
    gmt = _write_gmt(tmp_path / "sets.gmt", genes=("GENE1", "GENE2", "GENE3"))
    gsea_input = _gsea_input(ranked)

    gate = build_gsea_gene_set_resource_gate(tmp_path, gsea_input=gsea_input, resource_path=gmt, min_gene_set_size=2, max_gene_set_size=20)

    assert gate["status"] == "passed"
    assert gate["overlapping_term_count"] == 1
    assert gate["max_overlap_count"] == 3


def test_gmt_without_overlap_blocks(tmp_path: Path) -> None:
    ranked = _write_ranked(tmp_path)
    gmt = _write_gmt(tmp_path / "sets.gmt", genes=("NOPE1", "NOPE2"))

    gate = build_gsea_gene_set_resource_gate(tmp_path, gsea_input=_gsea_input(ranked), resource_path=gmt, min_gene_set_size=2, max_gene_set_size=20)

    assert "gsea_gene_set_no_overlap_with_ranked_genes" in gate["blockers"]


def test_invalid_size_bounds_block(tmp_path: Path) -> None:
    ranked = _write_ranked(tmp_path)
    gmt = _write_gmt(tmp_path / "sets.gmt", genes=("GENE1", "GENE2"))

    gate = build_gsea_gene_set_resource_gate(tmp_path, gsea_input=_gsea_input(ranked), resource_path=gmt, min_gene_set_size=20, max_gene_set_size=2)

    assert "gsea_gene_set_size_bounds_invalid" in gate["blockers"]


def test_registry_resource_and_msigdb_license_warning(tmp_path: Path) -> None:
    ranked = _write_ranked(tmp_path)
    gmt = _write_gmt(tmp_path / "user_data" / "bioinformatics" / "gene_sets" / "custom" / "msigdb.gmt", genes=("GENE1", "GENE2"))
    registry = tmp_path / "user_data" / "bioinformatics" / "gene_sets" / "gene_set_registry.json"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.gene_set_registry.v1",
                "resources": [
                    {
                        "resource_id": "msigdb_hallmark",
                        "name": "MSigDB Hallmark",
                        "collection_type": "Hallmark",
                        "species": "unknown",
                        "gene_id_type": "symbol",
                        "status": "available",
                        "local_path": str(gmt.relative_to(tmp_path)),
                        "source": "msigdb",
                        "license_note": "manual import",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    blocked = build_gsea_gene_set_resource_gate(tmp_path, gsea_input=_gsea_input(ranked), resource_id="msigdb_hallmark", min_gene_set_size=2, max_gene_set_size=20)
    passed = build_gsea_gene_set_resource_gate(tmp_path, gsea_input=_gsea_input(ranked), resource_id="msigdb_hallmark", min_gene_set_size=2, max_gene_set_size=20, msigdb_license_acknowledged=True)

    assert "gsea_msigdb_license_or_source_unacknowledged" in blocked["blockers"]
    assert "gsea_msigdb_resource_requires_manual_license_acknowledgement" in blocked["warnings"]
    assert passed["status"] == "passed"


def _write_ranked(root: Path) -> Path:
    path = root / "ranked.rnk"
    path.write_text("\n".join(f"GENE{i}\t{10 - i}" for i in range(1, 13)) + "\n", encoding="utf-8")
    return path


def _write_gmt(path: Path, *, genes: tuple[str, ...]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("TERM_A\tTerm A\t" + "\t".join(genes) + "\n", encoding="utf-8")
    return path


def _gsea_input(ranked: Path) -> dict[str, object]:
    return {"status": "passed", "ranked_gene_list_path": str(ranked), "source_gene_id_type": "symbol", "blockers": [], "warnings": []}
