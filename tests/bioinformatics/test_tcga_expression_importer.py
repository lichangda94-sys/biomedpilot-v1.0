from __future__ import annotations

import csv
from pathlib import Path

from app.bioinformatics.standard_assets.tcga_assets import (
    TCGA_EXPRESSION_MATRIX,
    TCGA_PREPARE_MANIFEST,
    TCGA_SAMPLE_METADATA,
)
from app.bioinformatics.tcga.expression_importer import import_tcga_expression_matrix


def _read_csv(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


def test_gene_by_sample_csv_import_outputs_standard_assets(tmp_path) -> None:
    input_path = tmp_path / "input_gene_by_sample.csv"
    input_path.write_text(
        "\n".join(
            [
                "gene_id,TCGA-AB-1234-01A,TCGA-AB-1234-11A",
                "ENSG000001234.5,1.0,2.0",
                "TP53,3.0,4.0",
            ]
        ),
        encoding="utf-8",
    )

    result = import_tcga_expression_matrix(
        input_path,
        tmp_path / "out",
        "TCGA-THCA",
        "batch-1",
        normalization="TPM",
        log_transform=False,
        parameters={"fixture": "gene_by_sample"},
    )

    expression_path = result["asset_paths"][TCGA_EXPRESSION_MATRIX]
    sample_metadata_path = result["asset_paths"][TCGA_SAMPLE_METADATA]
    manifest = result["manifest"]
    matrix_rows = _read_csv(Path(expression_path))
    metadata_rows = _read_csv(Path(sample_metadata_path))

    assert result["matrix_orientation"] == "gene_by_sample"
    assert matrix_rows == [
        ["gene_id", "TCGA-AB-1234-01A", "TCGA-AB-1234-11A"],
        ["ENSG000001234", "1.0", "2.0"],
        ["TP53", "3.0", "4.0"],
    ]
    assert metadata_rows[0] == [
        "sample_id",
        "barcode",
        "tcga_barcode",
        "patient_barcode",
        "participant_barcode",
        "project_prefix",
        "sample_type_code",
        "sample_type_label",
        "is_tumor",
        "is_normal",
    ]
    assert metadata_rows[1][0] == "TCGA-AB-1234-01A"
    assert metadata_rows[1][7] == "Primary Tumor"
    assert metadata_rows[2][0] == "TCGA-AB-1234-11A"
    assert metadata_rows[2][7] == "Solid Tissue Normal"
    assert manifest["project_id"] == "TCGA-THCA"
    assert manifest["batch_id"] == "batch-1"
    assert manifest["source"] == str(input_path.resolve())
    assert manifest["gene_count"] == 2
    assert manifest["sample_count"] == 2
    assert manifest["normalization"] == "TPM"
    assert manifest["matrix_orientation"] == "gene_by_sample"
    assert manifest["log_transform"] is False
    assert manifest["parameters"]["fixture"] == "gene_by_sample"
    assert TCGA_EXPRESSION_MATRIX in manifest["asset_paths"]
    assert TCGA_PREPARE_MANIFEST in manifest["asset_paths"]


def test_sample_by_gene_tsv_import_auto_transposes(tmp_path) -> None:
    input_path = tmp_path / "input_sample_by_gene.tsv"
    input_path.write_text(
        "\n".join(
            [
                "barcode\tENSG000001234.5\tTP53",
                "TCGA-AB-1234-01A\t1.0\t3.0",
                "TCGA-AB-1234-11A\t2.0\t4.0",
            ]
        ),
        encoding="utf-8",
    )

    result = import_tcga_expression_matrix(input_path, tmp_path / "out", "TCGA-THCA", "batch-2")

    matrix_rows = _read_csv(Path(result["asset_paths"][TCGA_EXPRESSION_MATRIX]))
    assert result["matrix_orientation"] == "sample_by_gene"
    assert matrix_rows == [
        ["gene_id", "TCGA-AB-1234-01A", "TCGA-AB-1234-11A"],
        ["ENSG000001234", "1.0", "2.0"],
        ["TP53", "3.0", "4.0"],
    ]
    assert result["manifest"]["gene_count"] == 2
    assert result["manifest"]["sample_count"] == 2


def test_duplicate_gene_and_invalid_sample_barcode_are_warnings(tmp_path) -> None:
    input_path = tmp_path / "input_with_warnings.csv"
    input_path.write_text(
        "\n".join(
            [
                "gene_symbol,TCGA-AB-1234-01A,INVALID-SAMPLE",
                "TP53,1.0,2.0",
                "TP53,3.0,4.0",
                ",5.0,6.0",
            ]
        ),
        encoding="utf-8",
    )

    result = import_tcga_expression_matrix(input_path, tmp_path / "out", "TCGA-THCA", "batch-3")

    matrix_rows = _read_csv(Path(result["asset_paths"][TCGA_EXPRESSION_MATRIX]))
    warnings = result["warnings"]
    assert matrix_rows == [["gene_id", "TCGA-AB-1234-01A", "INVALID-SAMPLE"], ["TP53", "1.0", "2.0"]]
    assert result["gene_count"] == 1
    assert result["sample_count"] == 1
    assert any(warning.startswith("duplicate_gene_id_rows_removed:1:TP53") for warning in warnings)
    assert "empty_gene_id_rows_removed:1" in warnings
    assert "invalid_sample_barcode:INVALID-SAMPLE" in warnings
    assert "invalid_sample_barcode:INVALID-SAMPLE" in result["manifest"]["warnings"]


def test_import_without_valid_tcga_sample_barcodes_still_writes_manifest(tmp_path) -> None:
    input_path = tmp_path / "input_no_valid_samples.csv"
    input_path.write_text("gene_id,sample_a\nTP53,1.0\n", encoding="utf-8")

    result = import_tcga_expression_matrix(
        input_path,
        tmp_path / "out",
        "TCGA-THCA",
        "batch-4",
        matrix_orientation="gene_by_sample",
    )

    assert result["sample_count"] == 0
    assert "no_valid_tcga_sample_barcodes" in result["warnings"]
    assert Path(result["asset_paths"][TCGA_PREPARE_MANIFEST]).exists()
