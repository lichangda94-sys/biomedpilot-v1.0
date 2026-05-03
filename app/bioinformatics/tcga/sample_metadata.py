"""Build minimal TCGA sample metadata tables from barcodes."""

from __future__ import annotations

from typing import Any

from .barcode import parse_tcga_barcode, validate_tcga_sample_barcodes


def build_tcga_sample_metadata(sample_barcodes: list[str]) -> list[dict[str, Any]]:
    """Build one metadata row per valid TCGA sample barcode."""
    rows: list[dict[str, Any]] = []
    for barcode in sample_barcodes:
        parsed = parse_tcga_barcode(barcode)
        rows.append(
            {
                "sample_id": parsed["barcode"],
                "barcode": parsed["barcode"],
                "tcga_barcode": parsed["barcode"],
                "patient_barcode": parsed["patient_barcode"],
                "participant_barcode": parsed["patient_barcode"],
                "project_prefix": parsed["project_prefix"],
                "sample_type_code": parsed["sample_type_code"],
                "sample_type_label": parsed["sample_type_label"],
                "is_tumor": parsed["is_tumor"],
                "is_normal": parsed["is_normal"],
            }
        )
    return rows


__all__ = ["build_tcga_sample_metadata", "validate_tcga_sample_barcodes"]

