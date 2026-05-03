from __future__ import annotations

import csv
from pathlib import Path

from app.bioinformatics.standard_assets.tcga_assets import (
    TCGA_CLINICAL_LINKAGE_SUMMARY,
    TCGA_CLINICAL_TABLE,
    TCGA_EXPRESSION_MATRIX,
    TCGA_PREPARE_MANIFEST,
    TCGA_SAMPLE_METADATA,
)
from app.bioinformatics.tcga.prepared_package import (
    load_tcga_clinical_linkage_summary,
    load_tcga_clinical_table,
    load_tcga_expression_matrix,
    load_tcga_prepared_manifest,
    load_tcga_sample_metadata,
    prepare_tcga_local_package,
    validate_tcga_prepared_package,
)


def _write_expression_fixture(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "gene_id,TCGA-AB-1234-01A,TCGA-AB-1234-11A",
                "ENSG000001234.5,1.0,2.0",
                "TP53,3.0,4.0",
            ]
        ),
        encoding="utf-8",
    )


def _write_clinical_fixture(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "bcr_patient_barcode,days_to_death,days_to_last_follow_up,vital_status,age_at_diagnosis,gender,ajcc_pathologic_stage",
                "TCGA-AB-1234,100,,Dead,21915,Female,Stage II",
                "TCGA-CD-5678,,200,Alive,50,Male,Stage I",
            ]
        ),
        encoding="utf-8",
    )


def test_prepare_tcga_local_package_builds_complete_package(tmp_path) -> None:
    expression_path = tmp_path / "expression.csv"
    clinical_path = tmp_path / "clinical.csv"
    _write_expression_fixture(expression_path)
    _write_clinical_fixture(clinical_path)

    summary = prepare_tcga_local_package(
        expression_path,
        clinical_path,
        tmp_path / "out",
        "TCGA-THCA",
        "batch-1",
        normalization="TPM",
        log_transform=False,
        parameters={"expression": {"fixture": "expr"}, "clinical": {"fixture": "clin"}},
    )

    assert summary["project_id"] == "TCGA-THCA"
    assert summary["batch_id"] == "batch-1"
    assert summary["gene_count"] == 2
    assert summary["sample_count"] == 2
    assert summary["clinical_patient_count"] == 2
    assert summary["matched_patient_count"] == 1
    assert Path(summary["manifest_path"]).exists()
    assert Path(summary["expression_matrix_path"]).exists()
    assert Path(summary["sample_metadata_path"]).exists()
    assert Path(summary["clinical_table_path"]).exists()
    assert Path(summary["clinical_linkage_summary_path"]).exists()

    manifest = summary["manifest"]
    assert TCGA_PREPARE_MANIFEST in manifest["asset_paths"]
    assert TCGA_EXPRESSION_MATRIX in manifest["asset_paths"]
    assert TCGA_SAMPLE_METADATA in manifest["asset_paths"]
    assert TCGA_CLINICAL_TABLE in manifest["asset_paths"]
    assert TCGA_CLINICAL_LINKAGE_SUMMARY in manifest["asset_paths"]
    assert manifest["normalization"] == "TPM"
    assert manifest["parameters"]["fixture"] == "expr"
    assert manifest["parameters"]["clinical_import"]["fixture"] == "clin"


def test_prepared_package_loaders_read_all_standard_assets(tmp_path) -> None:
    expression_path = tmp_path / "expression.csv"
    clinical_path = tmp_path / "clinical.csv"
    _write_expression_fixture(expression_path)
    _write_clinical_fixture(clinical_path)
    summary = prepare_tcga_local_package(expression_path, clinical_path, tmp_path / "out", "TCGA-THCA", "batch-2")

    manifest = load_tcga_prepared_manifest(summary["manifest_path"])
    expression_rows = load_tcga_expression_matrix(manifest)
    sample_rows = load_tcga_sample_metadata(summary["manifest_path"])
    clinical_rows = load_tcga_clinical_table(manifest)
    linkage = load_tcga_clinical_linkage_summary(summary["manifest_path"])

    assert expression_rows[0]["gene_id"] == "ENSG000001234"
    assert sample_rows[0]["tcga_barcode"] == "TCGA-AB-1234-01A"
    assert clinical_rows[0]["patient_barcode"] == "TCGA-AB-1234"
    assert linkage["matched_patient_count"] == 1


def test_validator_accepts_complete_package(tmp_path) -> None:
    expression_path = tmp_path / "expression.csv"
    clinical_path = tmp_path / "clinical.csv"
    _write_expression_fixture(expression_path)
    _write_clinical_fixture(clinical_path)
    summary = prepare_tcga_local_package(expression_path, clinical_path, tmp_path / "out", "TCGA-THCA", "batch-3")

    validation = validate_tcga_prepared_package(summary["manifest_path"])

    assert validation["is_valid"]
    assert validation["errors"] == []
    assert validation["sample_count"] == 2
    assert validation["gene_count"] == 2
    assert validation["clinical_patient_count"] == 2
    assert validation["matched_patient_count"] == 1


def test_validator_reports_missing_clinical_table(tmp_path) -> None:
    expression_path = tmp_path / "expression.csv"
    clinical_path = tmp_path / "clinical.csv"
    _write_expression_fixture(expression_path)
    _write_clinical_fixture(clinical_path)
    summary = prepare_tcga_local_package(expression_path, clinical_path, tmp_path / "out", "TCGA-THCA", "batch-4")

    Path(summary["clinical_table_path"]).unlink()
    validation = validate_tcga_prepared_package(summary["manifest_path"])

    assert not validation["is_valid"]
    assert any(error.startswith(f"asset_unreadable:{TCGA_CLINICAL_TABLE}") for error in validation["errors"])


def test_validator_warns_when_expression_columns_and_sample_metadata_disagree(tmp_path) -> None:
    expression_path = tmp_path / "expression.csv"
    clinical_path = tmp_path / "clinical.csv"
    _write_expression_fixture(expression_path)
    _write_clinical_fixture(clinical_path)
    summary = prepare_tcga_local_package(expression_path, clinical_path, tmp_path / "out", "TCGA-THCA", "batch-5")

    sample_metadata_path = Path(summary["sample_metadata_path"])
    with sample_metadata_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    with sample_metadata_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(rows[0])
        writer.writerow(rows[1])

    validation = validate_tcga_prepared_package(summary["manifest_path"])

    assert validation["is_valid"]
    assert any(
        warning.startswith("expression_sample_columns_mismatch_sample_metadata")
        for warning in validation["warnings"]
    )


def test_validator_reports_missing_manifest_path(tmp_path) -> None:
    validation = validate_tcga_prepared_package(tmp_path / "missing_manifest.json")

    assert not validation["is_valid"]
    assert validation["errors"][0].startswith("manifest_missing:")

