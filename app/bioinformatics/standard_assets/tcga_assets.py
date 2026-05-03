"""Minimal TCGA standard asset contract helpers.

The helpers in this module intentionally do not download, parse, or normalize
TCGA data. They only define stable asset roles, deterministic project paths,
and a small JSON manifest shape for future TCGA runners.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "tcga_standard_assets_v0"
PREPARE_MANIFEST_FILENAME = "tcga_prepare_manifest.json"

TCGA_EXPRESSION_MATRIX = "tcga_expression_matrix"
TCGA_CLINICAL_TABLE = "tcga_clinical_table"
TCGA_CLINICAL_LINKAGE_SUMMARY = "tcga_clinical_linkage_summary"
TCGA_SAMPLE_METADATA = "tcga_sample_metadata"
TCGA_PREPARE_MANIFEST = "tcga_prepare_manifest"
TCGA_MUTATION_MATRIX = "tcga_mutation_matrix"
TCGA_CNV_MATRIX = "tcga_cnv_matrix"
TCGA_METHYLATION_MATRIX = "tcga_methylation_matrix"

TCGA_ASSET_TYPES = (
    TCGA_EXPRESSION_MATRIX,
    TCGA_CLINICAL_TABLE,
    TCGA_CLINICAL_LINKAGE_SUMMARY,
    TCGA_SAMPLE_METADATA,
    TCGA_PREPARE_MANIFEST,
    TCGA_MUTATION_MATRIX,
    TCGA_CNV_MATRIX,
    TCGA_METHYLATION_MATRIX,
)


@dataclass(frozen=True)
class TcgaAssetPaths:
    """Resolved standard TCGA asset paths for one project batch."""

    project_root: Path
    tcga_expression_matrix: Path
    tcga_clinical_table: Path
    tcga_clinical_linkage_summary: Path
    tcga_sample_metadata: Path
    tcga_prepare_manifest: Path
    tcga_mutation_matrix: Path
    tcga_cnv_matrix: Path
    tcga_methylation_matrix: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            TCGA_EXPRESSION_MATRIX: self.tcga_expression_matrix,
            TCGA_CLINICAL_TABLE: self.tcga_clinical_table,
            TCGA_CLINICAL_LINKAGE_SUMMARY: self.tcga_clinical_linkage_summary,
            TCGA_SAMPLE_METADATA: self.tcga_sample_metadata,
            TCGA_PREPARE_MANIFEST: self.tcga_prepare_manifest,
            TCGA_MUTATION_MATRIX: self.tcga_mutation_matrix,
            TCGA_CNV_MATRIX: self.tcga_cnv_matrix,
            TCGA_METHYLATION_MATRIX: self.tcga_methylation_matrix,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in value.strip())
    return "_".join(part for part in cleaned.split("_") if part) or "unknown"


def build_tcga_asset_paths(
    project_dir: str | Path,
    project_id: str,
    batch_id: str,
    layout: str = "organized",
) -> dict[str, Path]:
    """Build deterministic standard asset paths for a TCGA project batch."""
    root = Path(project_dir).expanduser().resolve() / "tcga" / _slug(project_id) / _slug(batch_id)
    if layout == "organized":
        base = root / "organized" / "tcga"
        paths = TcgaAssetPaths(
            project_root=root,
            tcga_expression_matrix=base / "expression" / "tcga_expression_matrix.tsv.gz",
            tcga_clinical_table=base / "clinical" / "tcga_clinical_table.tsv",
            tcga_clinical_linkage_summary=base / "clinical" / "tcga_clinical_linkage_summary.json",
            tcga_sample_metadata=base / "metadata" / "tcga_sample_metadata.tsv",
            tcga_prepare_manifest=base / PREPARE_MANIFEST_FILENAME,
            tcga_mutation_matrix=base / "mutation" / "tcga_mutation_matrix.tsv.gz",
            tcga_cnv_matrix=base / "cnv" / "tcga_cnv_matrix.tsv.gz",
            tcga_methylation_matrix=base / "methylation" / "tcga_methylation_matrix.tsv.gz",
        )
    elif layout == "data_prepared":
        base = root / "data_prepared" / "tcga"
        paths = TcgaAssetPaths(
            project_root=root,
            tcga_expression_matrix=base / "expression" / "tcga_expression_matrix.csv",
            tcga_clinical_table=base / "clinical" / "tcga_clinical_table.csv",
            tcga_clinical_linkage_summary=base / "clinical" / "tcga_clinical_linkage_summary.json",
            tcga_sample_metadata=base / "sample_metadata" / "tcga_sample_metadata.csv",
            tcga_prepare_manifest=base / PREPARE_MANIFEST_FILENAME,
            tcga_mutation_matrix=base / "mutation" / "tcga_mutation_matrix.csv",
            tcga_cnv_matrix=base / "cnv" / "tcga_cnv_matrix.csv",
            tcga_methylation_matrix=base / "methylation" / "tcga_methylation_matrix.csv",
        )
    else:
        raise ValueError(f"Unsupported TCGA asset layout: {layout}")
    return paths.as_dict()


def _stringify_paths(asset_paths: dict[str, str | Path]) -> dict[str, str]:
    return {key: str(value) for key, value in asset_paths.items()}


def write_tcga_prepare_manifest(
    manifest_path: str | Path,
    *,
    project_id: str,
    batch_id: str,
    source: str,
    asset_paths: dict[str, str | Path],
    sample_count: int = 0,
    gene_count: int = 0,
    normalization: str = "",
    warnings: list[str] | None = None,
    parameters: dict[str, Any] | None = None,
    created_at: str | None = None,
    matrix_orientation: str | None = None,
    log_transform: bool | None = None,
) -> dict[str, Any]:
    """Write a minimal TCGA prepare manifest and return its payload."""
    payload_parameters = dict(parameters or {})
    if matrix_orientation is not None:
        payload_parameters.setdefault("matrix_orientation", matrix_orientation)
    if log_transform is not None:
        payload_parameters.setdefault("log_transform", log_transform)
    payload = {
        "contract_version": CONTRACT_VERSION,
        "manifest_role": TCGA_PREPARE_MANIFEST,
        "project_id": project_id,
        "batch_id": batch_id,
        "created_at": created_at or _now_iso(),
        "source": source,
        "asset_paths": _stringify_paths(asset_paths),
        "sample_count": int(sample_count),
        "gene_count": int(gene_count),
        "normalization": normalization,
        "matrix_orientation": matrix_orientation,
        "log_transform": log_transform,
        "warnings": list(warnings or []),
        "parameters": payload_parameters,
    }

    target = Path(manifest_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def read_tcga_prepare_manifest(manifest_path: str | Path) -> dict[str, Any]:
    """Read a TCGA prepare manifest from JSON."""
    path = Path(manifest_path).expanduser().resolve()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_tcga_prepare_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate the minimal TCGA prepare manifest shape.

    Returns a structured validation result instead of raising so callers can
    surface actionable warnings in a workflow state panel.
    """
    errors: list[str] = []
    warnings: list[str] = []

    required_fields = (
        "project_id",
        "batch_id",
        "created_at",
        "source",
        "asset_paths",
        "sample_count",
        "gene_count",
        "normalization",
        "warnings",
        "parameters",
    )
    for field in required_fields:
        if field not in manifest:
            errors.append(f"missing_required_field:{field}")

    if manifest.get("manifest_role") not in (None, TCGA_PREPARE_MANIFEST):
        errors.append("invalid_manifest_role")

    asset_paths = manifest.get("asset_paths")
    if not isinstance(asset_paths, dict):
        errors.append("asset_paths_must_be_object")
    else:
        missing_assets = [asset_type for asset_type in TCGA_ASSET_TYPES if asset_type not in asset_paths]
        for asset_type in missing_assets:
            warnings.append(f"asset_path_missing:{asset_type}")
        if TCGA_PREPARE_MANIFEST in asset_paths and not str(asset_paths[TCGA_PREPARE_MANIFEST]).endswith(".json"):
            errors.append("tcga_prepare_manifest_path_must_be_json")

    for numeric_field in ("sample_count", "gene_count"):
        value = manifest.get(numeric_field)
        if not isinstance(value, int) or value < 0:
            errors.append(f"{numeric_field}_must_be_non_negative_integer")

    if not isinstance(manifest.get("warnings", []), list):
        errors.append("warnings_must_be_list")
    if not isinstance(manifest.get("parameters", {}), dict):
        errors.append("parameters_must_be_object")

    return {
        "is_valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }


__all__ = [
    "CONTRACT_VERSION",
    "PREPARE_MANIFEST_FILENAME",
    "TCGA_ASSET_TYPES",
    "TCGA_EXPRESSION_MATRIX",
    "TCGA_CLINICAL_TABLE",
    "TCGA_CLINICAL_LINKAGE_SUMMARY",
    "TCGA_SAMPLE_METADATA",
    "TCGA_PREPARE_MANIFEST",
    "TCGA_MUTATION_MATRIX",
    "TCGA_CNV_MATRIX",
    "TCGA_METHYLATION_MATRIX",
    "build_tcga_asset_paths",
    "write_tcga_prepare_manifest",
    "read_tcga_prepare_manifest",
    "validate_tcga_prepare_manifest",
]
