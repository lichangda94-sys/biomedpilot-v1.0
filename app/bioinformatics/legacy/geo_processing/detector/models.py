"""Typed models for GEO dataset detection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AccessionType(str, Enum):
    GSE = "GSE"
    GSM = "GSM"
    GPL = "GPL"
    GDS = "GDS"
    UNKNOWN = "UNKNOWN"


class ContainerType(str, Enum):
    SERIES_MATRIX = "series_matrix"
    FAMILY_SOFT = "family_soft"
    MINIML = "miniml"
    SUPPLEMENTARY = "supplementary"
    PLATFORM_ANNOTATION = "platform_annotation"
    RAW_FILE = "raw_file"
    UNKNOWN = "unknown"


class DataRole(str, Enum):
    METADATA = "metadata"
    PROCESSED = "processed"
    RAW = "raw"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class TechnologyType(str, Enum):
    MICROARRAY = "microarray"
    BULK_RNASEQ = "bulk_rnaseq"
    BULK_RNASEQ_RAW_LINKED = "bulk_rnaseq_raw_linked"
    SINGLE_CELL = "single_cell"
    SPATIAL = "spatial"
    MULTIOMICS = "multiomics"
    UNKNOWN = "unknown"


class MatrixLevel(str, Enum):
    PROBE = "probe"
    GENE = "gene"
    TRANSCRIPT = "transcript"
    PEAK = "peak"
    DIFF_RESULT = "diff_result"
    NON_MATRIX = "non_matrix"
    UNKNOWN = "unknown"


class ValueSemantic(str, Enum):
    RAW_COUNTS = "raw_counts"
    NORMALIZED_COUNTS = "normalized_counts"
    LOG2_EXPRESSION = "log2_expression"
    INTENSITY = "intensity"
    RATIO = "ratio"
    UNKNOWN = "unknown"


class RecommendedStrategy(str, Enum):
    SERIES_MATRIX_FIRST = "SERIES_MATRIX_FIRST"
    SUPPLEMENTARY_MATRIX_FIRST = "SUPPLEMENTARY_MATRIX_FIRST"
    SOFT_METADATA_PLUS_SUPP_MATRIX = "SOFT_METADATA_PLUS_SUPP_MATRIX"
    PROBE_TO_GENE_WITH_GPL = "PROBE_TO_GENE_WITH_GPL"
    RAW_MICROARRAY_EXTERNAL_PREPROCESS = "RAW_MICROARRAY_EXTERNAL_PREPROCESS"
    RAW_RNASEQ_EXTERNAL_PREPROCESS = "RAW_RNASEQ_EXTERNAL_PREPROCESS"
    METADATA_ONLY = "METADATA_ONLY"
    UNSUPPORTED_SINGLE_CELL = "UNSUPPORTED_SINGLE_CELL"
    UNSUPPORTED_SPATIAL = "UNSUPPORTED_SPATIAL"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


@dataclass
class DatasetDetectionResult:
    accession: str
    accession_type: str
    scan_root: str

    container_types: List[str] = field(default_factory=list)
    data_roles: List[str] = field(default_factory=list)

    technology_type: str = "unknown"
    matrix_level: str = "unknown"
    value_semantic: str = "unknown"

    has_series_matrix: bool = False
    has_family_soft: bool = False
    has_miniml: bool = False
    has_supplementary: bool = False
    has_platform_annotation: bool = False
    has_expression_payload: bool = False
    has_sample_annotation: bool = False
    has_clinical_annotation: bool = False
    payload_type: str = "none"

    candidate_expression_files: List[str] = field(default_factory=list)
    candidate_metadata_files: List[str] = field(default_factory=list)
    candidate_clinical_files: List[str] = field(default_factory=list)
    candidate_annotation_files: List[str] = field(default_factory=list)
    raw_files: List[str] = field(default_factory=list)
    platform_annotation_files: List[str] = field(default_factory=list)
    supporting_files: List[str] = field(default_factory=list)
    archive_files: List[str] = field(default_factory=list)
    external_sources: List[str] = field(default_factory=list)
    ignored_files: List[str] = field(default_factory=list)

    recommended_strategy: str = "MANUAL_REVIEW_REQUIRED"
    confidence: float = 0.0

    warnings: List[str] = field(default_factory=list)
    failure_stage: Optional[str] = None
    failure_reason: Optional[str] = None
    next_action: Optional[str] = None
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    classification_debug: Dict[str, Any] = field(default_factory=dict)
    top_problem_summary: Optional[str] = None
    suggested_next_fix: Optional[str] = None

    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FileScanRecord:
    path: str
    relative_path: str
    name: str
    extension: str
    is_gzip: bool
    size_bytes: int
    initial_container_guess: str = ContainerType.UNKNOWN.value

    container_type: str = ContainerType.UNKNOWN.value
    data_role: str = DataRole.UNKNOWN.value
    technology_type: str = TechnologyType.UNKNOWN.value
    matrix_level: str = MatrixLevel.UNKNOWN.value
    value_semantic: str = ValueSemantic.UNKNOWN.value

    expression_score: float = 0.0
    metadata_score: float = 0.0
    annotation_score: float = 0.0

    preview_lines: List[str] = field(default_factory=list)
    preview_rows: List[List[str]] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    decision_trace: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)
