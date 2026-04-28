from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DeliveryFileType(StrEnum):
    RAW_COUNT_MATRIX = "raw_count_matrix"
    TPM_MATRIX = "tpm_matrix"
    FPKM_MATRIX = "fpkm_matrix"
    NORMALIZED_EXPRESSION_MATRIX = "normalized_expression_matrix"
    SAMPLE_METADATA = "sample_metadata"
    GENE_ANNOTATION = "gene_annotation"
    DIFFERENTIAL_EXPRESSION_RESULT = "differential_expression_result"
    QC_REPORT = "qc_report"
    RAW_FASTQ = "raw_fastq"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class DeliveryFileCandidate:
    file_path: str
    file_name: str
    file_size: int
    detected_type: DeliveryFileType
    confidence: float
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "detected_type": self.detected_type.value,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class DeliveryScanReport:
    root_dir: str
    candidates: list[DeliveryFileCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_dir": self.root_dir,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class SelectedImportPlan:
    dataset_slug: str
    selected_expression_matrix: str | None
    expression_data_type: str | None
    selected_sample_metadata: str | None = None
    selected_gene_annotation: str | None = None
    selected_qc_reports: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    valid: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_slug": self.dataset_slug,
            "selected_expression_matrix": self.selected_expression_matrix,
            "expression_data_type": self.expression_data_type,
            "selected_sample_metadata": self.selected_sample_metadata,
            "selected_gene_annotation": self.selected_gene_annotation,
            "selected_qc_reports": list(self.selected_qc_reports),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "valid": self.valid,
        }


@dataclass(slots=True)
class LocalDatasetManifest:
    dataset_slug: str
    source_type: str
    detected_files: list[str]
    selected_expression_matrix: str
    selected_sample_metadata: str | None
    selected_gene_annotation: str | None
    expression_data_type: str
    sample_count: int
    gene_count: int
    created_at: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_slug": self.dataset_slug,
            "source_type": self.source_type,
            "detected_files": list(self.detected_files),
            "selected_expression_matrix": self.selected_expression_matrix,
            "selected_sample_metadata": self.selected_sample_metadata,
            "selected_gene_annotation": self.selected_gene_annotation,
            "expression_data_type": self.expression_data_type,
            "sample_count": self.sample_count,
            "gene_count": self.gene_count,
            "created_at": self.created_at,
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class LocalDatasetValidationReport:
    sample_id_match_status: str
    missing_value_count: int
    duplicated_gene_count: int
    group_count: int
    group_size_summary: dict[str, int]
    expression_value_type: str
    count_based_compatible: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id_match_status": self.sample_id_match_status,
            "missing_value_count": self.missing_value_count,
            "duplicated_gene_count": self.duplicated_gene_count,
            "group_count": self.group_count,
            "group_size_summary": dict(self.group_size_summary),
            "expression_value_type": self.expression_value_type,
            "count_based_compatible": self.count_based_compatible,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }
