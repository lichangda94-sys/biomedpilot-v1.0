"""Typed models for downloaded GEO dataset validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FileScoreResult:
    """Multi-dimensional score result for one downloaded file."""

    path: str
    relative_path: str
    size_bytes: int

    excluded: bool = False
    excluded_reason: Optional[str] = None

    expression_score: float = 0.0
    sample_annotation_score: float = 0.0
    clinical_score: float = 0.0
    raw_data_score: float = 0.0
    platform_annotation_score: float = 0.0
    junk_score: float = 0.0

    primary_label: str = "unknown"
    secondary_labels: List[str] = field(default_factory=list)
    accepted_as_candidate_matrix: bool = False
    accepted_as_payload: bool = False
    organized_targets: List[str] = field(default_factory=list)
    source_level: str = "downloaded"
    source_path: str = ""
    source_scope: str = "downloaded"
    confidence: float = 0.0

    reasons: List[str] = field(default_factory=list)
    decision_trace: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    preview_lines: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        return asdict(self)


@dataclass
class DownloadValidationResult:
    """Validation summary for a downloaded GEO dataset directory."""

    gse_id: str
    download_dir: str

    status: str
    download_success: bool

    file_count: int
    nonempty_file_count: int

    has_series_matrix: bool = False
    has_family_soft: bool = False
    has_miniml: bool = False
    has_supplementary: bool = False
    has_raw_files: bool = False
    has_platform_hint: bool = False

    has_expression_payload: bool = False
    has_sample_annotation: bool = False
    has_clinical_annotation: bool = False
    payload_type: str = "none"
    external_raw_source: Optional[str] = None

    detected_gsm_count: Optional[int] = None
    candidate_matrix_count: int = 0
    candidate_metadata_count: int = 0
    candidate_clinical_count: int = 0

    candidate_matrix_files: List[str] = field(default_factory=list)
    candidate_metadata_files: List[str] = field(default_factory=list)
    candidate_clinical_files: List[str] = field(default_factory=list)
    raw_files: List[str] = field(default_factory=list)
    expression_sources: List[str] = field(default_factory=list)
    sample_annotation_sources: List[str] = field(default_factory=list)
    clinical_sources: List[str] = field(default_factory=list)
    archive_files: List[str] = field(default_factory=list)
    supporting_files: List[str] = field(default_factory=list)
    external_sources: List[str] = field(default_factory=list)
    broken_files: List[str] = field(default_factory=list)
    ignored_files: List[str] = field(default_factory=list)
    platform_annotation_files: List[str] = field(default_factory=list)

    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    failure_stage: Optional[str] = None
    next_action: Optional[str] = None
    failure_reason: Optional[str] = None
    top_problem_summary: Optional[str] = None
    suggested_next_fix: Optional[str] = None
    recommended_strategy: Optional[str] = None
    organized_paths: Dict[str, List[str]] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        return asdict(self)
