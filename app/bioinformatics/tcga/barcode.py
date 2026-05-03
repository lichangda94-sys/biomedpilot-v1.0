"""TCGA barcode parsing helpers."""

from __future__ import annotations

import re
from typing import Any


SAMPLE_TYPE_LABELS = {
    "01": "Primary Tumor",
    "06": "Metastatic",
    "10": "Blood Derived Normal",
    "11": "Solid Tissue Normal",
}

TUMOR_SAMPLE_TYPE_CODES = {"01", "06"}
NORMAL_SAMPLE_TYPE_CODES = {"10", "11"}

_TCGA_BARCODE_RE = re.compile(
    r"^(?P<project>TCGA)-(?P<tss>[A-Z0-9]{2})-(?P<participant>[A-Z0-9]{4})"
    r"(?:-(?P<sample_type>[0-9]{2})(?P<vial>[A-Z])?)?.*$",
    re.IGNORECASE,
)


def parse_tcga_barcode(barcode: str) -> dict[str, Any]:
    """Parse a TCGA barcode into stable sample metadata fields."""
    if not isinstance(barcode, str) or not barcode.strip():
        raise ValueError("TCGA barcode must be a non-empty string.")

    normalized = barcode.strip().upper()
    match = _TCGA_BARCODE_RE.match(normalized)
    if match is None:
        raise ValueError(f"Invalid TCGA barcode: {barcode}")

    sample_type_code = match.group("sample_type") or ""
    sample_type_label = SAMPLE_TYPE_LABELS.get(sample_type_code, "Unknown" if sample_type_code else "")
    patient_barcode = "-".join(
        [match.group("project").upper(), match.group("tss").upper(), match.group("participant").upper()]
    )

    return {
        "barcode": normalized,
        "patient_barcode": patient_barcode,
        "project_prefix": match.group("project").upper(),
        "sample_type_code": sample_type_code,
        "sample_type_label": sample_type_label,
        "is_tumor": sample_type_code in TUMOR_SAMPLE_TYPE_CODES,
        "is_normal": sample_type_code in NORMAL_SAMPLE_TYPE_CODES,
    }


def infer_tcga_sample_type(barcode: str) -> dict[str, Any]:
    """Infer TCGA sample type fields from a barcode."""
    parsed = parse_tcga_barcode(barcode)
    return {
        "sample_type_code": parsed["sample_type_code"],
        "sample_type_label": parsed["sample_type_label"],
        "is_tumor": parsed["is_tumor"],
        "is_normal": parsed["is_normal"],
    }


def validate_tcga_sample_barcodes(sample_barcodes: list[str]) -> dict[str, Any]:
    """Validate a list of TCGA sample barcodes without raising."""
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, str]] = []
    seen: set[str] = set()
    duplicates: list[str] = []

    for barcode in sample_barcodes:
        try:
            parsed = parse_tcga_barcode(barcode)
        except ValueError as exc:
            invalid.append({"barcode": str(barcode), "error": str(exc)})
            continue
        if parsed["barcode"] in seen and parsed["barcode"] not in duplicates:
            duplicates.append(parsed["barcode"])
        seen.add(parsed["barcode"])
        valid.append(parsed)

    return {
        "is_valid": not invalid,
        "valid_count": len(valid),
        "invalid_count": len(invalid),
        "duplicate_count": len(duplicates),
        "valid_barcodes": valid,
        "invalid_barcodes": invalid,
        "duplicates": duplicates,
    }


__all__ = [
    "SAMPLE_TYPE_LABELS",
    "parse_tcga_barcode",
    "infer_tcga_sample_type",
    "validate_tcga_sample_barcodes",
]

