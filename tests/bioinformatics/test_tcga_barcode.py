from __future__ import annotations

import pytest

from app.bioinformatics.tcga.barcode import (
    infer_tcga_sample_type,
    parse_tcga_barcode,
    validate_tcga_sample_barcodes,
)
from app.bioinformatics.tcga.sample_metadata import build_tcga_sample_metadata


def test_parse_primary_tumor_barcode() -> None:
    parsed = parse_tcga_barcode("TCGA-AB-1234-01A-01R-5678-07")

    assert parsed["barcode"] == "TCGA-AB-1234-01A-01R-5678-07"
    assert parsed["patient_barcode"] == "TCGA-AB-1234"
    assert parsed["project_prefix"] == "TCGA"
    assert parsed["sample_type_code"] == "01"
    assert parsed["sample_type_label"] == "Primary Tumor"
    assert parsed["is_tumor"] is True
    assert parsed["is_normal"] is False


def test_parse_solid_tissue_normal_barcode() -> None:
    parsed = parse_tcga_barcode("TCGA-AB-1234-11A")

    assert parsed["sample_type_code"] == "11"
    assert parsed["sample_type_label"] == "Solid Tissue Normal"
    assert parsed["is_tumor"] is False
    assert parsed["is_normal"] is True


def test_infer_blood_derived_normal_sample_type() -> None:
    inferred = infer_tcga_sample_type("TCGA-AB-1234-10A")

    assert inferred == {
        "sample_type_code": "10",
        "sample_type_label": "Blood Derived Normal",
        "is_tumor": False,
        "is_normal": True,
    }


def test_invalid_tcga_barcode_raises_and_validator_reports_it() -> None:
    with pytest.raises(ValueError):
        parse_tcga_barcode("not-a-tcga-barcode")

    validation = validate_tcga_sample_barcodes(["TCGA-AB-1234-01A", "not-a-tcga-barcode"])
    assert not validation["is_valid"]
    assert validation["valid_count"] == 1
    assert validation["invalid_count"] == 1
    assert validation["invalid_barcodes"][0]["barcode"] == "not-a-tcga-barcode"


def test_build_tcga_sample_metadata_fields() -> None:
    rows = build_tcga_sample_metadata(["TCGA-AB-1234-01A", "TCGA-AB-1234-11A"])

    assert len(rows) == 2
    assert rows[0]["sample_id"] == "TCGA-AB-1234-01A"
    assert rows[0]["tcga_barcode"] == "TCGA-AB-1234-01A"
    assert rows[0]["participant_barcode"] == "TCGA-AB-1234"
    assert rows[0]["sample_type_label"] == "Primary Tumor"
    assert rows[0]["is_tumor"] is True
    assert rows[1]["sample_type_label"] == "Solid Tissue Normal"
    assert rows[1]["is_normal"] is True

