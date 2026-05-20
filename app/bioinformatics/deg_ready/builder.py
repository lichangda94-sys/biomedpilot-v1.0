from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from app.bioinformatics.analysis_inputs.models import AnalysisInputPackage

from .models import DegReadyPackage


COUNT_VALUE_TYPES = {"count", "raw_count", "raw_counts", "count_like_candidate"}
DISPLAY_VALUE_TYPES = {"TPM", "FPKM", "FPKM-UQ", "normalized", "normalized_expression", "normalized_or_log_expression", "log_expression", "log2_transformed"}
GENE_LEVEL_TYPES = {"symbol", "gene_symbol", "ensembl", "ensembl_gene_id"}
PROBE_TYPES = {"probe", "probe_id", "ID_REF", "id_ref", "unknown"}


def build_deg_ready_package(input_package: AnalysisInputPackage | dict[str, Any]) -> DegReadyPackage:
    package = input_package.to_dict() if isinstance(input_package, AnalysisInputPackage) else dict(input_package)
    blockers = [str(item) for item in package.get("blockers", []) or []]
    warnings = [str(item) for item in package.get("warnings", []) or []]
    if str(package.get("package_type") or "") != "deg_recompute":
        blockers.append("input_package_is_not_deg_recompute")
    matrix_asset = _asset(package, "expression_asset")
    sample_asset = _asset(package, "sample_metadata_asset")
    group_asset = _asset(package, "group_design_asset")
    feature_asset = _asset(package, "feature_annotation_asset")
    matrix_samples = _matrix_sample_columns(_asset_path(matrix_asset))
    sample_groups = _sample_groups(_asset_path(sample_asset), _asset_path(group_asset))
    alignment = _sample_alignment(matrix_samples, sample_groups)
    gene_mapping = _gene_mapping_status(str(package.get("gene_id_type") or "unknown"), feature_asset)
    blockers.extend(str(item) for item in alignment.get("blockers", []) or [])
    blockers.extend(str(item) for item in gene_mapping.get("blockers", []) or [])
    warnings.extend(str(item) for item in alignment.get("warnings", []) or [])
    warnings.extend(str(item) for item in gene_mapping.get("warnings", []) or [])
    value_type = str(package.get("value_type") or "unknown")
    allowed_methods: list[str] = []
    if not blockers and value_type in COUNT_VALUE_TYPES and not gene_mapping.get("requires_mapping"):
        allowed_methods.append("count_model_preflight")
    if not blockers and value_type in DISPLAY_VALUE_TYPES and str(package.get("gene_id_type") or "") in GENE_LEVEL_TYPES:
        allowed_methods.append("exploratory_welch_or_mann_whitney_preflight")
    if value_type in {"unknown", ""}:
        blockers.append("unknown_value_type_blocks_formal_deg")
    return DegReadyPackage(
        deg_ready_package_id=_deg_ready_id(str(package.get("input_package_id") or "")),
        source_input_package_id=str(package.get("input_package_id") or ""),
        matrix_asset=matrix_asset,
        sample_metadata_asset=sample_asset,
        group_design_asset=group_asset,
        feature_annotation_asset=feature_asset,
        value_type=value_type,
        gene_id_type=str(package.get("gene_id_type") or "unknown"),
        sample_alignment_status=alignment,
        gene_mapping_status=gene_mapping,
        allowed_deg_methods=tuple(allowed_methods),
        blockers=tuple(_dedupe(blockers)),
        warnings=tuple(_dedupe(warnings)),
    )


def _asset(package: dict[str, Any], key: str) -> dict[str, Any] | None:
    value = package.get(key)
    return value if isinstance(value, dict) else None


def _asset_path(asset: dict[str, Any] | None) -> Path | None:
    if not isinstance(asset, dict):
        return None
    value = str(asset.get("path") or asset.get("file_path") or "")
    if not value:
        return None
    return Path(value).expanduser()


def _matrix_sample_columns(path: Path | None) -> list[str]:
    if path is None or not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            first = handle.readline()
    except OSError:
        return []
    if not first:
        return []
    delimiter = "," if first.count(",") > first.count("\t") else "\t"
    row = next(csv.reader([first], delimiter=delimiter), [])
    return [str(cell).strip() for cell in row[1:] if str(cell).strip()]


def _sample_groups(sample_path: Path | None, group_path: Path | None) -> dict[str, str]:
    groups: dict[str, str] = {}
    if sample_path is not None and sample_path.is_file():
        groups.update(_sample_groups_from_tsv(sample_path))
    if group_path is not None and group_path.is_file() and group_path.suffix.lower() == ".json":
        try:
            payload = json.loads(group_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        group = payload.get("group_design") if isinstance(payload.get("group_design"), dict) else {}
        assignments = group.get("sample_group_assignments") if isinstance(group.get("sample_group_assignments"), dict) else {}
        groups.update({str(sample): str(value) for sample, value in assignments.items() if str(sample)})
    return groups


def _sample_groups_from_tsv(path: Path) -> dict[str, str]:
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            rows = list(reader)
    except OSError:
        return {}
    groups: dict[str, str] = {}
    for row in rows:
        sample = str(row.get("sample_id") or row.get("sample") or row.get("barcode") or "").strip()
        group = str(row.get("group") or row.get("sample_group") or row.get("condition") or "").strip()
        if sample:
            groups[sample] = group
    return groups


def _sample_alignment(matrix_samples: list[str], sample_groups: dict[str, str]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    duplicates = sorted(_duplicates(matrix_samples))
    if not matrix_samples:
        blockers.append("expression_matrix_has_no_sample_columns")
    if not sample_groups:
        blockers.append("missing_sample_group_assignments")
    if duplicates:
        blockers.append("duplicate_expression_sample_ids")
    expression_set = set(matrix_samples)
    metadata_set = set(sample_groups)
    missing_in_metadata = sorted(expression_set - metadata_set)
    missing_in_matrix = sorted(metadata_set - expression_set)
    matched = sorted(expression_set & metadata_set)
    if expression_set and metadata_set and not matched:
        blockers.append("expression_and_metadata_samples_do_not_overlap")
    elif missing_in_metadata or missing_in_matrix:
        warnings.append("expression_metadata_sample_partial_overlap")
    group_counts: dict[str, int] = {}
    matched_assignments: dict[str, str] = {}
    for sample in matched:
        group = sample_groups.get(sample, "")
        if group:
            group_counts[group] = group_counts.get(group, 0) + 1
            matched_assignments[sample] = group
    non_empty_groups = [group for group, count in group_counts.items() if count > 0]
    if len(non_empty_groups) < 2:
        blockers.append("case_control_groups_not_confirmed_or_empty")
    return {
        "status": "blocked" if blockers else ("warning" if warnings else "passed"),
        "matrix_sample_count": len(matrix_samples),
        "metadata_sample_count": len(sample_groups),
        "matched_sample_count": len(matched),
        "missing_in_metadata": missing_in_metadata,
        "missing_in_matrix": missing_in_matrix,
        "duplicate_samples": duplicates,
        "group_counts": group_counts,
        "sample_group_assignments": matched_assignments,
        "blockers": blockers,
        "warnings": warnings,
    }


def _gene_mapping_status(gene_id_type: str, feature_asset: dict[str, Any] | None) -> dict[str, Any]:
    normalized = gene_id_type or "unknown"
    blockers: list[str] = []
    warnings: list[str] = []
    requires_mapping = normalized in PROBE_TYPES
    if normalized in GENE_LEVEL_TYPES:
        status = "passed"
    elif requires_mapping:
        if not _mapping_confirmed(feature_asset):
            blockers.append("probe_or_id_ref_mapping_missing")
            status = "blocked"
        else:
            status = "passed"
    elif "transcript" in normalized.lower():
        warnings.append("transcript_level_matrix_not_collapsed_to_gene_level")
        status = "warning"
    else:
        blockers.append("unknown_feature_id_type")
        status = "blocked"
    return {"status": status, "gene_id_type": normalized, "requires_mapping": requires_mapping, "blockers": blockers, "warnings": warnings}


def _mapping_confirmed(feature_asset: dict[str, Any] | None) -> bool:
    if not isinstance(feature_asset, dict):
        return False
    return str(feature_asset.get("validation_status") or "") != "blocked" and bool(feature_asset.get("asset_id"))


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _deg_ready_id(input_package_id: str) -> str:
    return f"deg-ready-{hashlib.sha1(input_package_id.encode('utf-8')).hexdigest()[:12]}"


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
