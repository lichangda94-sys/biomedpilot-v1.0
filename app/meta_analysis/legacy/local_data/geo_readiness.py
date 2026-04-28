from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class GeoSubmissionReadinessLevel(StrEnum):
    INSUFFICIENT = "insufficient"
    PARTIAL = "partial"
    LIKELY_READY_FOR_MANUAL_GEO_SUBMISSION = "likely_ready_for_manual_geo_submission"


@dataclass(slots=True)
class GeoSubmissionReadinessReport:
    has_raw_fastq: bool
    has_processed_count_matrix: bool
    has_normalized_expression_matrix: bool
    has_sample_metadata: bool
    has_gene_annotation: bool
    has_sample_to_raw_file_mapping: bool
    has_reference_genome_info: bool
    has_annotation_version_info: bool
    has_processing_software_info: bool
    has_human_subject_privacy_warning: bool
    readiness_level: GeoSubmissionReadinessLevel
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_raw_fastq": self.has_raw_fastq,
            "has_processed_count_matrix": self.has_processed_count_matrix,
            "has_normalized_expression_matrix": self.has_normalized_expression_matrix,
            "has_sample_metadata": self.has_sample_metadata,
            "has_gene_annotation": self.has_gene_annotation,
            "has_sample_to_raw_file_mapping": self.has_sample_to_raw_file_mapping,
            "has_reference_genome_info": self.has_reference_genome_info,
            "has_annotation_version_info": self.has_annotation_version_info,
            "has_processing_software_info": self.has_processing_software_info,
            "has_human_subject_privacy_warning": self.has_human_subject_privacy_warning,
            "readiness_level": self.readiness_level.value,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


def build_geo_submission_readiness_report(
    *,
    has_raw_fastq: bool = False,
    has_processed_count_matrix: bool = False,
    has_normalized_expression_matrix: bool = False,
    has_sample_metadata: bool = False,
    has_gene_annotation: bool = False,
    has_sample_to_raw_file_mapping: bool = False,
    has_reference_genome_info: bool = False,
    has_annotation_version_info: bool = False,
    has_processing_software_info: bool = False,
    expression_samples: list[str] | None = None,
    metadata_samples: list[str] | None = None,
    is_human_subject_data: bool = False,
) -> GeoSubmissionReadinessReport:
    warnings: list[str] = []
    errors: list[str] = []

    has_processed_expression = has_processed_count_matrix or has_normalized_expression_matrix
    if not has_processed_expression:
        errors.append("processed_expression_matrix_missing")
    if not has_sample_metadata:
        errors.append("sample_metadata_missing")

    if has_processed_expression and has_sample_metadata:
        if not _samples_match(expression_samples or [], metadata_samples or []):
            errors.append("expression_metadata_sample_mismatch")

    if not has_raw_fastq:
        warnings.append("raw_fastq_missing")
    if has_raw_fastq and not has_sample_to_raw_file_mapping:
        warnings.append("sample_to_raw_file_mapping_missing")
    if not has_gene_annotation:
        warnings.append("gene_annotation_missing")
    if not has_reference_genome_info:
        warnings.append("reference_genome_info_missing")
    if not has_annotation_version_info:
        warnings.append("annotation_version_info_missing")
    if not has_processing_software_info:
        warnings.append("processing_software_info_missing")

    has_human_subject_privacy_warning = is_human_subject_data
    if has_human_subject_privacy_warning:
        warnings.append("human_subject_privacy_review_required")

    readiness_level = _readiness_level(errors, warnings)
    return GeoSubmissionReadinessReport(
        has_raw_fastq=has_raw_fastq,
        has_processed_count_matrix=has_processed_count_matrix,
        has_normalized_expression_matrix=has_normalized_expression_matrix,
        has_sample_metadata=has_sample_metadata,
        has_gene_annotation=has_gene_annotation,
        has_sample_to_raw_file_mapping=has_sample_to_raw_file_mapping,
        has_reference_genome_info=has_reference_genome_info,
        has_annotation_version_info=has_annotation_version_info,
        has_processing_software_info=has_processing_software_info,
        has_human_subject_privacy_warning=has_human_subject_privacy_warning,
        readiness_level=readiness_level,
        warnings=_dedupe_preserve_order(warnings),
        errors=_dedupe_preserve_order(errors),
    )


def _samples_match(expression_samples: list[str], metadata_samples: list[str]) -> bool:
    if not expression_samples or not metadata_samples:
        return False
    return set(expression_samples) == set(metadata_samples)


def _readiness_level(
    errors: list[str],
    warnings: list[str],
) -> GeoSubmissionReadinessLevel:
    if errors:
        return GeoSubmissionReadinessLevel.INSUFFICIENT
    if warnings:
        return GeoSubmissionReadinessLevel.PARTIAL
    return GeoSubmissionReadinessLevel.LIKELY_READY_FOR_MANUAL_GEO_SUBMISSION


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
