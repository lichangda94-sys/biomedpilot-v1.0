from __future__ import annotations

from app.bioinformatics.standard_assets.tcga_assets import (
    TCGA_ASSET_TYPES,
    TCGA_CLINICAL_LINKAGE_SUMMARY,
    TCGA_EXPRESSION_MATRIX,
    TCGA_PREPARE_MANIFEST,
    build_tcga_asset_paths,
    read_tcga_prepare_manifest,
    validate_tcga_prepare_manifest,
    write_tcga_prepare_manifest,
)


def test_tcga_asset_paths_include_all_standard_roles(tmp_path) -> None:
    paths = build_tcga_asset_paths(tmp_path, "TCGA-THCA", "batch-1")

    assert set(TCGA_ASSET_TYPES) == set(paths)
    assert paths[TCGA_EXPRESSION_MATRIX].name == "tcga_expression_matrix.tsv.gz"
    assert paths[TCGA_PREPARE_MANIFEST].name == "tcga_prepare_manifest.json"
    assert "tcga_thca" in paths[TCGA_PREPARE_MANIFEST].as_posix()


def test_tcga_asset_paths_support_data_prepared_layout(tmp_path) -> None:
    paths = build_tcga_asset_paths(tmp_path, "TCGA-THCA", "batch-1", layout="data_prepared")

    assert set(TCGA_ASSET_TYPES) == set(paths)
    assert paths[TCGA_EXPRESSION_MATRIX].as_posix().endswith(
        "data_prepared/tcga/expression/tcga_expression_matrix.csv"
    )
    assert paths[TCGA_PREPARE_MANIFEST].as_posix().endswith("data_prepared/tcga/tcga_prepare_manifest.json")
    assert paths[TCGA_CLINICAL_LINKAGE_SUMMARY].as_posix().endswith(
        "data_prepared/tcga/clinical/tcga_clinical_linkage_summary.json"
    )


def test_tcga_manifest_writer_reader_and_validator(tmp_path) -> None:
    paths = build_tcga_asset_paths(tmp_path, "TCGA-THCA", "batch-1")

    payload = write_tcga_prepare_manifest(
        paths[TCGA_PREPARE_MANIFEST],
        project_id="TCGA-THCA",
        batch_id="batch-1",
        source="fixture",
        asset_paths=paths,
        sample_count=2,
        gene_count=3,
        normalization="TPM",
        warnings=["fixture_only"],
        parameters={"tissue_filter": "all"},
        created_at="2026-04-29T00:00:00+00:00",
        matrix_orientation="gene_by_sample",
        log_transform=False,
    )

    loaded = read_tcga_prepare_manifest(paths[TCGA_PREPARE_MANIFEST])
    validation = validate_tcga_prepare_manifest(loaded)

    assert loaded == payload
    assert loaded["project_id"] == "TCGA-THCA"
    assert loaded["sample_count"] == 2
    assert loaded["gene_count"] == 3
    assert loaded["normalization"] == "TPM"
    assert loaded["matrix_orientation"] == "gene_by_sample"
    assert loaded["log_transform"] is False
    assert loaded["parameters"]["tissue_filter"] == "all"
    assert validation["is_valid"]
    assert validation["errors"] == []


def test_tcga_manifest_validator_reports_missing_required_fields() -> None:
    validation = validate_tcga_prepare_manifest({"project_id": "TCGA-THCA"})

    assert not validation["is_valid"]
    assert "missing_required_field:batch_id" in validation["errors"]
    assert "asset_paths_must_be_object" in validation["errors"]
