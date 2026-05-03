"""TCGA prepared package service helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from app.bioinformatics.standard_assets.tcga_assets import (
    TCGA_CLINICAL_LINKAGE_SUMMARY,
    TCGA_CLINICAL_TABLE,
    TCGA_EXPRESSION_MATRIX,
    TCGA_PREPARE_MANIFEST,
    TCGA_SAMPLE_METADATA,
)

from .clinical_importer import import_tcga_clinical_table
from .expression_importer import import_tcga_expression_matrix


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"TCGA prepared asset does not exist: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"TCGA prepared asset does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_from_dict_or_path(manifest_or_path: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(manifest_or_path, dict):
        return manifest_or_path
    return load_tcga_prepared_manifest(manifest_or_path)


def _asset_path(manifest_or_path: dict[str, Any] | str | Path, asset_role: str) -> Path:
    manifest = _manifest_from_dict_or_path(manifest_or_path)
    asset_paths = manifest.get("asset_paths")
    if not isinstance(asset_paths, dict):
        raise KeyError("TCGA prepared manifest is missing asset_paths.")
    value = asset_paths.get(asset_role)
    if not value:
        raise KeyError(f"TCGA prepared manifest is missing asset path: {asset_role}")
    return Path(value).expanduser().resolve()


def prepare_tcga_local_package(
    expression_path: str | Path,
    clinical_path: str | Path,
    output_dir: str | Path,
    project_id: str,
    batch_id: str,
    normalization: str = "unknown",
    matrix_orientation: str = "auto",
    log_transform: bool | None = None,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare a local TCGA package from expression and clinical files."""
    package_parameters = dict(parameters or {})
    expression_result = import_tcga_expression_matrix(
        expression_path,
        output_dir,
        project_id,
        batch_id,
        normalization=normalization,
        matrix_orientation=matrix_orientation,
        log_transform=log_transform,
        parameters=package_parameters.get("expression"),
    )
    clinical_result = import_tcga_clinical_table(
        clinical_path,
        output_dir,
        project_id,
        batch_id,
        sample_metadata_path=expression_result["asset_paths"][TCGA_SAMPLE_METADATA],
        parameters=package_parameters.get("clinical"),
    )

    manifest = clinical_result["manifest"]
    asset_paths = manifest["asset_paths"]
    warnings = []
    for warning in expression_result.get("warnings", []) + clinical_result.get("warnings", []):
        if warning not in warnings:
            warnings.append(warning)

    return {
        "status": "success",
        "project_id": project_id,
        "batch_id": batch_id,
        "manifest_path": asset_paths[TCGA_PREPARE_MANIFEST],
        "expression_matrix_path": asset_paths[TCGA_EXPRESSION_MATRIX],
        "sample_metadata_path": asset_paths[TCGA_SAMPLE_METADATA],
        "clinical_table_path": asset_paths[TCGA_CLINICAL_TABLE],
        "clinical_linkage_summary_path": asset_paths[TCGA_CLINICAL_LINKAGE_SUMMARY],
        "gene_count": manifest.get("gene_count", 0),
        "sample_count": manifest.get("sample_count", 0),
        "clinical_patient_count": manifest.get("clinical_patient_count", 0),
        "matched_patient_count": manifest.get("matched_patient_count", 0),
        "warnings": warnings,
        "manifest": manifest,
    }


def load_tcga_prepared_manifest(manifest_path: str | Path) -> dict[str, Any]:
    """Load a TCGA prepared package manifest."""
    return _read_json(Path(manifest_path).expanduser().resolve())


def load_tcga_expression_matrix(manifest_or_path: dict[str, Any] | str | Path) -> list[dict[str, str]]:
    """Load the prepared TCGA expression matrix as CSV rows."""
    return _read_csv_rows(_asset_path(manifest_or_path, TCGA_EXPRESSION_MATRIX))


def load_tcga_sample_metadata(manifest_or_path: dict[str, Any] | str | Path) -> list[dict[str, str]]:
    """Load the prepared TCGA sample metadata table."""
    return _read_csv_rows(_asset_path(manifest_or_path, TCGA_SAMPLE_METADATA))


def load_tcga_clinical_table(manifest_or_path: dict[str, Any] | str | Path) -> list[dict[str, str]]:
    """Load the prepared TCGA clinical table."""
    return _read_csv_rows(_asset_path(manifest_or_path, TCGA_CLINICAL_TABLE))


def load_tcga_clinical_linkage_summary(manifest_or_path: dict[str, Any] | str | Path) -> dict[str, Any]:
    """Load the prepared TCGA clinical linkage summary."""
    return _read_json(_asset_path(manifest_or_path, TCGA_CLINICAL_LINKAGE_SUMMARY))


def _validate_manifest_readable(
    manifest_or_path: dict[str, Any] | str | Path,
    errors: list[str],
) -> dict[str, Any] | None:
    if isinstance(manifest_or_path, dict):
        return manifest_or_path
    path = Path(manifest_or_path).expanduser().resolve()
    if not path.exists():
        errors.append(f"manifest_missing:{path}")
        return None
    try:
        return load_tcga_prepared_manifest(path)
    except Exception as exc:
        errors.append(f"manifest_unreadable:{path}:{exc}")
        return None


def _load_required_table(
    manifest: dict[str, Any],
    asset_role: str,
    errors: list[str],
) -> list[dict[str, str]]:
    try:
        return _read_csv_rows(_asset_path(manifest, asset_role))
    except Exception as exc:
        errors.append(f"asset_unreadable:{asset_role}:{exc}")
        return []


def validate_tcga_prepared_package(manifest_or_path: dict[str, Any] | str | Path) -> dict[str, Any]:
    """Validate a minimal prepared TCGA expression plus clinical package."""
    errors: list[str] = []
    warnings: list[str] = []
    manifest = _validate_manifest_readable(manifest_or_path, errors)
    if manifest is None:
        return {
            "is_valid": False,
            "errors": errors,
            "warnings": warnings,
            "sample_count": 0,
            "gene_count": 0,
            "clinical_patient_count": 0,
            "matched_patient_count": 0,
        }

    expression_rows = _load_required_table(manifest, TCGA_EXPRESSION_MATRIX, errors)
    sample_rows = _load_required_table(manifest, TCGA_SAMPLE_METADATA, errors)
    clinical_rows = _load_required_table(manifest, TCGA_CLINICAL_TABLE, errors)

    if expression_rows:
        expression_sample_columns = [key for key in expression_rows[0].keys() if key != "gene_id"]
    else:
        expression_sample_columns = []
    sample_barcodes = [row.get("tcga_barcode") or row.get("sample_id") or row.get("barcode") for row in sample_rows]
    sample_barcodes = [barcode for barcode in sample_barcodes if barcode]

    if expression_rows and sample_rows and len(expression_sample_columns) != len(sample_barcodes):
        warnings.append(
            "expression_sample_columns_mismatch_sample_metadata:"
            f"expression={len(expression_sample_columns)}:sample_metadata={len(sample_barcodes)}"
        )
    if sample_rows and not any(
        str(row.get("is_tumor", "")).lower() == "true" or str(row.get("is_normal", "")).lower() == "true"
        for row in sample_rows
    ):
        warnings.append("no_tumor_or_normal_samples_identified")
    elif not sample_rows:
        warnings.append("no_sample_metadata_rows")

    linkage_summary: dict[str, Any] = {}
    try:
        linkage_summary = load_tcga_clinical_linkage_summary(manifest)
    except Exception as exc:
        warnings.append(f"clinical_linkage_summary_unreadable:{exc}")

    sample_count = len(sample_rows)
    gene_count = len(expression_rows)
    clinical_patient_count = len(clinical_rows)
    matched_patient_count = int(linkage_summary.get("matched_patient_count", manifest.get("matched_patient_count", 0)) or 0)

    return {
        "is_valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "sample_count": sample_count,
        "gene_count": gene_count,
        "clinical_patient_count": clinical_patient_count,
        "matched_patient_count": matched_patient_count,
    }


__all__ = [
    "prepare_tcga_local_package",
    "load_tcga_prepared_manifest",
    "load_tcga_expression_matrix",
    "load_tcga_sample_metadata",
    "load_tcga_clinical_table",
    "load_tcga_clinical_linkage_summary",
    "validate_tcga_prepared_package",
]

