from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DatasetAssetStatus(StrEnum):
    PRESENT = "present"
    MISSING = "missing"
    PARTIAL = "partial"
    SUSPICIOUS = "suspicious"
    NOT_APPLICABLE = "not_applicable"


@dataclass(slots=True)
class DatasetAssetReadinessReport:
    dataset_id: str
    expression_matrix_status: DatasetAssetStatus
    sample_annotation_status: DatasetAssetStatus
    platform_annotation_status: DatasetAssetStatus
    gene_annotation_status: DatasetAssetStatus
    clinical_annotation_status: DatasetAssetStatus
    runnable: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    recommended_action: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "expression_matrix_status": self.expression_matrix_status.value,
            "sample_annotation_status": self.sample_annotation_status.value,
            "platform_annotation_status": self.platform_annotation_status.value,
            "gene_annotation_status": self.gene_annotation_status.value,
            "clinical_annotation_status": self.clinical_annotation_status.value,
            "runnable": self.runnable,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "recommended_action": self.recommended_action,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class GeneMappingReadinessReport:
    input_id_type: str
    target_id_type: str
    total_features: int
    mapped_features: int
    unmapped_features: int
    duplicated_targets: int
    mapping_success_rate: float
    collapse_strategy: str
    acceptable: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_id_type": self.input_id_type,
            "target_id_type": self.target_id_type,
            "total_features": self.total_features,
            "mapped_features": self.mapped_features,
            "unmapped_features": self.unmapped_features,
            "duplicated_targets": self.duplicated_targets,
            "mapping_success_rate": self.mapping_success_rate,
            "collapse_strategy": self.collapse_strategy,
            "acceptable": self.acceptable,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass(slots=True)
class SampleMappingReadinessReport:
    matrix_sample_count: int
    metadata_sample_count: int
    matched_sample_count: int
    unmatched_matrix_samples: list[str]
    unmatched_metadata_samples: list[str]
    duplicate_sample_ids: list[str]
    match_rate: float
    acceptable: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matrix_sample_count": self.matrix_sample_count,
            "metadata_sample_count": self.metadata_sample_count,
            "matched_sample_count": self.matched_sample_count,
            "unmatched_matrix_samples": list(self.unmatched_matrix_samples),
            "unmatched_metadata_samples": list(self.unmatched_metadata_samples),
            "duplicate_sample_ids": list(self.duplicate_sample_ids),
            "match_rate": self.match_rate,
            "acceptable": self.acceptable,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


def build_dataset_asset_readiness_report(
    dataset_id: str,
    assets: dict[str, Any] | None,
) -> DatasetAssetReadinessReport:
    asset_payload = assets or {}
    expression_status = _asset_status(asset_payload.get("expression_matrix"))
    sample_status = _asset_status(asset_payload.get("sample_annotation"))
    platform_status = _asset_status(
        asset_payload.get("platform_annotation"),
        default=DatasetAssetStatus.NOT_APPLICABLE,
    )
    gene_status = _asset_status(asset_payload.get("gene_annotation"))
    clinical_status = _asset_status(
        asset_payload.get("clinical_annotation"),
        default=DatasetAssetStatus.NOT_APPLICABLE,
    )

    warnings: list[str] = []
    errors: list[str] = []

    if expression_status == DatasetAssetStatus.MISSING:
        errors.append("expression_matrix_missing")
    elif expression_status in {
        DatasetAssetStatus.PARTIAL,
        DatasetAssetStatus.SUSPICIOUS,
    }:
        warnings.append(f"expression_matrix_{expression_status.value}")

    if sample_status == DatasetAssetStatus.MISSING:
        warnings.append("sample_annotation_missing")
    elif sample_status in {DatasetAssetStatus.PARTIAL, DatasetAssetStatus.SUSPICIOUS}:
        warnings.append(f"sample_annotation_{sample_status.value}")

    if platform_status in {DatasetAssetStatus.PARTIAL, DatasetAssetStatus.SUSPICIOUS}:
        warnings.append(f"platform_annotation_{platform_status.value}")

    if gene_status == DatasetAssetStatus.MISSING:
        warnings.append("gene_annotation_missing")
    elif gene_status in {DatasetAssetStatus.PARTIAL, DatasetAssetStatus.SUSPICIOUS}:
        warnings.append(f"gene_annotation_{gene_status.value}")

    if clinical_status in {DatasetAssetStatus.PARTIAL, DatasetAssetStatus.SUSPICIOUS}:
        warnings.append(f"clinical_annotation_{clinical_status.value}")

    runnable = not errors
    return DatasetAssetReadinessReport(
        dataset_id=dataset_id,
        expression_matrix_status=expression_status,
        sample_annotation_status=sample_status,
        platform_annotation_status=platform_status,
        gene_annotation_status=gene_status,
        clinical_annotation_status=clinical_status,
        runnable=runnable,
        warnings=warnings,
        errors=errors,
        recommended_action=_dataset_asset_recommended_action(runnable, warnings, errors),
        metadata=dict(asset_payload.get("metadata", {})),
    )


def build_gene_mapping_readiness_report(
    input_ids: list[str],
    mapping_results: dict[str, str | None] | None = None,
    *,
    input_id_type: str,
    target_id_type: str = "gene_symbol",
    collapse_strategy: str = "first",
    minimum_success_rate: float = 0.8,
) -> GeneMappingReadinessReport:
    normalized_input_ids, stripped_versions = _normalize_feature_ids(
        input_ids,
        input_id_type=input_id_type,
    )
    total_features = len(normalized_input_ids)
    mapping_payload = mapping_results or {}

    mapped_targets: list[str] = []
    for original_id, normalized_id in zip(input_ids, normalized_input_ids, strict=True):
        target = mapping_payload.get(normalized_id)
        if target is None:
            target = mapping_payload.get(str(original_id))
        if target is None and input_id_type == target_id_type:
            target = normalized_id
        if target:
            mapped_targets.append(str(target))

    mapped_features = len(mapped_targets)
    unmapped_features = total_features - mapped_features
    duplicated_targets = _count_duplicate_targets(mapped_targets)
    success_rate = (mapped_features / total_features) if total_features else 0.0

    warnings: list[str] = []
    errors: list[str] = []
    if stripped_versions:
        warnings.append("ensembl_versions_stripped")
    if "probe" in input_id_type.lower():
        warnings.append("probe_identifier_mapping_required")
    if duplicated_targets:
        warnings.append("duplicated_targets_detected")
    if success_rate < minimum_success_rate:
        errors.append("mapping_success_rate_too_low")
    if total_features == 0:
        errors.append("no_input_features")

    return GeneMappingReadinessReport(
        input_id_type=input_id_type,
        target_id_type=target_id_type,
        total_features=total_features,
        mapped_features=mapped_features,
        unmapped_features=unmapped_features,
        duplicated_targets=duplicated_targets,
        mapping_success_rate=round(success_rate, 4),
        collapse_strategy=collapse_strategy,
        acceptable=not errors,
        warnings=warnings,
        errors=errors,
    )


def build_sample_mapping_readiness_report(
    matrix_samples: list[str],
    metadata_samples: list[str],
    *,
    minimum_match_rate: float = 0.9,
) -> SampleMappingReadinessReport:
    matrix_ids = [str(item).strip() for item in matrix_samples if str(item).strip()]
    metadata_ids = [str(item).strip() for item in metadata_samples if str(item).strip()]
    matrix_set = set(matrix_ids)
    metadata_set = set(metadata_ids)
    matched = sorted(matrix_set & metadata_set)
    unmatched_matrix = sorted(matrix_set - metadata_set)
    unmatched_metadata = sorted(metadata_set - matrix_set)
    duplicate_ids = sorted(
        set(_duplicate_values(matrix_ids)) | set(_duplicate_values(metadata_ids))
    )
    match_rate = (len(matched) / len(matrix_set)) if matrix_set else 0.0

    warnings: list[str] = []
    errors: list[str] = []
    if duplicate_ids:
        warnings.append("duplicate_sample_ids_detected")
    if unmatched_matrix:
        warnings.append("unmatched_matrix_samples")
    if unmatched_metadata:
        warnings.append("unmatched_metadata_samples")
    if not matrix_set:
        errors.append("no_matrix_samples")
    if not metadata_set:
        errors.append("no_metadata_samples")
    if match_rate < minimum_match_rate:
        errors.append("sample_match_rate_too_low")

    return SampleMappingReadinessReport(
        matrix_sample_count=len(matrix_set),
        metadata_sample_count=len(metadata_set),
        matched_sample_count=len(matched),
        unmatched_matrix_samples=unmatched_matrix,
        unmatched_metadata_samples=unmatched_metadata,
        duplicate_sample_ids=duplicate_ids,
        match_rate=round(match_rate, 4),
        acceptable=not errors,
        warnings=warnings,
        errors=errors,
    )


def _asset_status(
    value: Any,
    *,
    default: DatasetAssetStatus = DatasetAssetStatus.MISSING,
) -> DatasetAssetStatus:
    if value is None:
        return default
    if isinstance(value, DatasetAssetStatus):
        return value
    if isinstance(value, bool):
        return DatasetAssetStatus.PRESENT if value else DatasetAssetStatus.MISSING
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return default
        return DatasetAssetStatus(normalized)
    if isinstance(value, dict):
        if "status" in value:
            return _asset_status(value.get("status"), default=default)
        if "present" in value:
            return _asset_status(bool(value.get("present")), default=default)
    return DatasetAssetStatus.PRESENT


def _dataset_asset_recommended_action(
    runnable: bool,
    warnings: list[str],
    errors: list[str],
) -> str:
    if "expression_matrix_missing" in errors:
        return "provide_expression_matrix"
    if not runnable:
        return "resolve_blocking_errors"
    if warnings:
        return "review_warnings_before_analysis"
    return "ready_for_preflight"


def _normalize_feature_ids(
    input_ids: list[str],
    *,
    input_id_type: str,
) -> tuple[list[str], bool]:
    strip_ensembl_versions = input_id_type.lower() in {
        "ensembl",
        "ensembl_id",
        "ensembl_gene_id",
    }
    normalized: list[str] = []
    stripped_versions = False
    for item in input_ids:
        value = str(item).strip()
        if strip_ensembl_versions and "." in value:
            value = value.split(".", 1)[0]
            stripped_versions = True
        normalized.append(value)
    return normalized, stripped_versions


def _count_duplicate_targets(mapped_targets: list[str]) -> int:
    counts: dict[str, int] = {}
    for target in mapped_targets:
        counts[target] = counts.get(target, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _duplicate_values(values: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return [value for value, count in counts.items() if count > 1]
