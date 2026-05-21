from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.gse_file_download_candidates import (
    build_gse_file_download_candidates,
    save_gse_file_download_candidate_selection,
)


def _asset_manifest(accession: str = "GSE33630") -> dict[str, object]:
    return {
        "schema_version": "biomedpilot.geo_asset_manifest.v1",
        "accession": accession,
        "assets": [
            {
                "asset_type": "family_soft",
                "role": "metadata_container",
                "file_name": f"{accession}_family.soft.gz",
                "status": "downloaded",
                "local_path": f"/internal/project/raw_data/geo/{accession}/{accession}_family.soft.gz",
                "remote_url": f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:5]}nnn/{accession}/soft/{accession}_family.soft.gz",
            },
            {
                "asset_type": "series_matrix",
                "role": "expression_matrix_candidate",
                "file_name": f"{accession}-GPL570_series_matrix.txt.gz",
                "status": "remote_discovered",
                "remote_url": f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:5]}nnn/{accession}/matrix/{accession}-GPL570_series_matrix.txt.gz",
            },
            {
                "asset_type": "supplementary_file",
                "role": "supplementary_expression_candidate",
                "file_name": f"{accession}_counts.tsv.gz",
                "status": "remote_discovered",
                "remote_url": f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:5]}nnn/{accession}/suppl/{accession}_counts.tsv.gz",
            },
            {
                "asset_type": "supplementary_file",
                "role": "supplementary_annotation_candidate",
                "file_name": "GPL570_probe_annotation.txt.gz",
                "status": "remote_discovered",
                "remote_url": f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:5]}nnn/{accession}/suppl/GPL570_probe_annotation.txt.gz",
            },
            {
                "asset_type": "supplementary_file",
                "role": "supplementary_file",
                "file_name": f"{accession}_DEG_results.xlsx",
                "status": "remote_discovered",
                "remote_url": f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:5]}nnn/{accession}/suppl/{accession}_DEG_results.xlsx",
            },
            {
                "asset_type": "supplementary_file",
                "role": "supplementary_file",
                "file_name": f"{accession}_RAW.tar",
                "status": "remote_discovered",
                "remote_url": f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:5]}nnn/{accession}/suppl/{accession}_RAW.tar",
                "size_bytes": 2_000_000_000,
            },
        ],
    }


def test_gse_asset_manifest_builds_download_candidate_rows(tmp_path: Path) -> None:
    manifest = build_gse_file_download_candidates(
        project_root=tmp_path,
        accession="GSE33630",
        asset_manifest=_asset_manifest(),
    )

    rows = {row["file_name"]: row for row in manifest["candidates"]}
    assert rows["GSE33630-GPL570_series_matrix.txt.gz"]["selected"] is True
    assert rows["GSE33630-GPL570_series_matrix.txt.gz"]["suggested_for_download"] is True
    assert rows["GSE33630-GPL570_series_matrix.txt.gz"]["recognition_use"] == "expression_matrix_candidate"
    assert rows["GSE33630_counts.tsv.gz"]["selected"] is True
    assert rows["GSE33630_counts.tsv.gz"]["recognition_use"] == "expression_matrix_candidate"
    assert rows["GSE33630_RAW.tar"]["selected"] is False
    assert rows["GSE33630_RAW.tar"]["recognition_use"] == "raw_heavy_risk_file"
    assert "RAW/heavy" in rows["GSE33630_RAW.tar"]["risk_warning"]
    assert rows["GSE33630_DEG_results.xlsx"]["selected"] is False
    assert rows["GSE33630_DEG_results.xlsx"]["recognition_use"] == "imported_deg_candidate"
    assert rows["GSE33630_DEG_results.xlsx"]["requires_recognition"] is False
    assert rows["GPL570_probe_annotation.txt.gz"]["recognition_use"] == "platform_annotation_candidate"
    assert "不代表已完成 ID 映射" in rows["GPL570_probe_annotation.txt.gz"]["risk_warning"]
    assert "PubMed" not in json.dumps(manifest, ensure_ascii=False)


def test_gse_download_candidate_selection_manifest_persists_selected_ids(tmp_path: Path) -> None:
    draft = build_gse_file_download_candidates(
        project_root=tmp_path,
        accession="GSE33630",
        asset_manifest=_asset_manifest(),
    )
    series_id = next(row["candidate_id"] for row in draft["candidates"] if row["file_name"].endswith("series_matrix.txt.gz"))

    path = save_gse_file_download_candidate_selection(
        project_root=tmp_path,
        accession="GSE33630",
        asset_manifest=_asset_manifest(),
        selected_candidate_ids=(series_id,),
    )

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["schema_version"] == "biomedpilot.gse_download_candidates.v1"
    assert saved["selected_count"] == 1
    selected = [row for row in saved["candidates"] if row["selected"]]
    assert [row["file_name"] for row in selected] == ["GSE33630-GPL570_series_matrix.txt.gz"]
    assert saved["notes"]
