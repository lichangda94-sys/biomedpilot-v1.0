"""Local TCGA expression matrix import and standardization shell."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from app.bioinformatics.standard_assets.tcga_assets import (
    TCGA_EXPRESSION_MATRIX,
    TCGA_PREPARE_MANIFEST,
    TCGA_SAMPLE_METADATA,
    build_tcga_asset_paths,
    write_tcga_prepare_manifest,
)

from .barcode import parse_tcga_barcode, validate_tcga_sample_barcodes
from .sample_metadata import build_tcga_sample_metadata


SUPPORTED_ORIENTATIONS = {"auto", "gene_by_sample", "sample_by_gene"}
_ENSEMBL_VERSION_RE = re.compile(r"^(ENSG[0-9]+)\.[0-9]+$", re.IGNORECASE)


def _detect_delimiter(input_path: Path) -> str:
    first_line = input_path.read_text(encoding="utf-8-sig").splitlines()[0]
    if first_line.count("\t") > first_line.count(","):
        return "\t"
    return ","


def _read_matrix(input_path: Path) -> list[list[str]]:
    delimiter = _detect_delimiter(input_path)
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [list(row) for row in csv.reader(handle, delimiter=delimiter)]


def _write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _write_matrix(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _clean_gene_id(value: str) -> str:
    stripped = str(value).strip()
    match = _ENSEMBL_VERSION_RE.match(stripped)
    if match:
        return match.group(1).upper()
    return stripped


def _is_tcga_barcode(value: str) -> bool:
    try:
        parse_tcga_barcode(value)
    except ValueError:
        return False
    return True


def _normalize_sample_name(value: str) -> str:
    try:
        return parse_tcga_barcode(value)["barcode"]
    except ValueError:
        return str(value).strip()


def _infer_orientation(header: list[str], body: list[list[str]], warnings: list[str]) -> str:
    header_barcode_count = sum(1 for value in header[1:] if _is_tcga_barcode(value))
    first_column_barcode_count = sum(1 for row in body if row and _is_tcga_barcode(row[0]))

    if header_barcode_count > first_column_barcode_count:
        return "gene_by_sample"
    if first_column_barcode_count > header_barcode_count:
        return "sample_by_gene"

    warnings.append(
        "matrix_orientation_auto_ambiguous:"
        f"header_tcga_count={header_barcode_count},first_column_tcga_count={first_column_barcode_count};"
        "defaulted_to_gene_by_sample"
    )
    return "gene_by_sample"


def _rectangularize(rows: list[list[str]]) -> list[list[str]]:
    width = max((len(row) for row in rows), default=0)
    return [row + [""] * (width - len(row)) for row in rows]


def _standardize_gene_rows(
    sample_names: list[str],
    raw_gene_rows: list[list[str]],
    warnings: list[str],
) -> tuple[list[str], list[list[str]]]:
    seen_gene_ids: set[str] = set()
    output_rows: list[list[str]] = []
    empty_gene_count = 0
    duplicate_gene_ids: list[str] = []

    for raw_row in raw_gene_rows:
        gene_id = _clean_gene_id(raw_row[0] if raw_row else "")
        if not gene_id:
            empty_gene_count += 1
            continue
        if gene_id in seen_gene_ids:
            duplicate_gene_ids.append(gene_id)
            continue
        seen_gene_ids.add(gene_id)
        values = raw_row[1 : len(sample_names) + 1]
        values = values + [""] * (len(sample_names) - len(values))
        output_rows.append([gene_id] + values)

    if empty_gene_count:
        warnings.append(f"empty_gene_id_rows_removed:{empty_gene_count}")
    if duplicate_gene_ids:
        unique_duplicates = sorted(set(duplicate_gene_ids))
        warnings.append(f"duplicate_gene_id_rows_removed:{len(duplicate_gene_ids)}:{','.join(unique_duplicates)}")

    return sample_names, output_rows


def _transpose_sample_rows(header: list[str], body: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    sample_names = [_normalize_sample_name(row[0]) for row in body if row]
    gene_rows: list[list[str]] = []
    for gene_index, gene_name in enumerate(header[1:], start=1):
        values = []
        for row in body:
            values.append(row[gene_index] if len(row) > gene_index else "")
        gene_rows.append([gene_name] + values)
    return sample_names, gene_rows


def _valid_sample_barcodes(sample_names: list[str], warnings: list[str]) -> list[str]:
    validation = validate_tcga_sample_barcodes(sample_names)
    for invalid in validation["invalid_barcodes"]:
        warnings.append(f"invalid_sample_barcode:{invalid['barcode']}")
    if validation["duplicate_count"]:
        warnings.append(f"duplicate_sample_barcodes:{','.join(validation['duplicates'])}")
    valid = [record["barcode"] for record in validation["valid_barcodes"]]
    if not valid:
        warnings.append("no_valid_tcga_sample_barcodes")
    return valid


def import_tcga_expression_matrix(
    input_path: str | Path,
    output_dir: str | Path,
    project_id: str,
    batch_id: str,
    normalization: str = "unknown",
    matrix_orientation: str = "auto",
    log_transform: bool | None = None,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Import a local TCGA expression matrix into standard prepared assets."""
    if matrix_orientation not in SUPPORTED_ORIENTATIONS:
        raise ValueError(f"Unsupported matrix_orientation: {matrix_orientation}")

    source_path = Path(input_path).expanduser().resolve()
    rows = _rectangularize(_read_matrix(source_path))
    if not rows:
        raise ValueError("Input expression matrix is empty.")
    if len(rows[0]) < 2:
        raise ValueError("Input expression matrix must contain at least one sample or gene column.")

    warnings: list[str] = []
    header = rows[0]
    body = rows[1:]
    resolved_orientation = (
        _infer_orientation(header, body, warnings) if matrix_orientation == "auto" else matrix_orientation
    )

    if resolved_orientation == "gene_by_sample":
        sample_names = [_normalize_sample_name(value) for value in header[1:]]
        raw_gene_rows = body
    else:
        sample_names, raw_gene_rows = _transpose_sample_rows(header, body)

    sample_names, expression_rows = _standardize_gene_rows(sample_names, raw_gene_rows, warnings)
    valid_sample_barcodes = _valid_sample_barcodes(sample_names, warnings)
    sample_metadata_rows = build_tcga_sample_metadata(valid_sample_barcodes)

    asset_paths = build_tcga_asset_paths(output_dir, project_id, batch_id, layout="data_prepared")
    expression_path = asset_paths[TCGA_EXPRESSION_MATRIX]
    sample_metadata_path = asset_paths[TCGA_SAMPLE_METADATA]
    manifest_path = asset_paths[TCGA_PREPARE_MANIFEST]

    _write_matrix(expression_path, ["gene_id"] + sample_names, expression_rows)
    sample_metadata_fields = [
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
    _write_rows(sample_metadata_path, sample_metadata_rows, sample_metadata_fields)

    manifest_parameters = dict(parameters or {})
    manifest_parameters.update(
        {
            "input_path": str(source_path),
            "requested_matrix_orientation": matrix_orientation,
            "matrix_orientation": resolved_orientation,
            "log_transform": log_transform,
        }
    )
    manifest = write_tcga_prepare_manifest(
        manifest_path,
        project_id=project_id,
        batch_id=batch_id,
        source=str(source_path),
        asset_paths=asset_paths,
        sample_count=len(valid_sample_barcodes),
        gene_count=len(expression_rows),
        normalization=normalization,
        warnings=warnings,
        parameters=manifest_parameters,
        matrix_orientation=resolved_orientation,
        log_transform=log_transform,
    )

    return {
        "status": "success",
        "project_id": project_id,
        "batch_id": batch_id,
        "matrix_orientation": resolved_orientation,
        "gene_count": len(expression_rows),
        "sample_count": len(valid_sample_barcodes),
        "warnings": warnings,
        "asset_paths": {key: str(value) for key, value in asset_paths.items()},
        "manifest": manifest,
    }


__all__ = ["import_tcga_expression_matrix"]
