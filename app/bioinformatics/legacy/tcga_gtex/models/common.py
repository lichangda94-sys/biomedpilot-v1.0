"""Common data objects for the unified TCGA/GTEx module."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class QueryMapping:
    """Normalized bilingual query object shared by adapters."""

    raw_query: str
    normalized_query: str = ""
    concept_ids: list[str] = field(default_factory=list)
    concept_categories: list[str] = field(default_factory=list)
    matched_terms_zh: list[str] = field(default_factory=list)
    query_terms_en: list[str] = field(default_factory=list)
    query_terms_zh: list[str] = field(default_factory=list)
    disease_terms: list[str] = field(default_factory=list)
    tissue_terms: list[str] = field(default_factory=list)
    sample_type_terms: list[str] = field(default_factory=list)
    data_type_terms: list[str] = field(default_factory=list)
    abbreviation_terms: list[str] = field(default_factory=list)
    source_hints: list[str] = field(default_factory=lambda: ["tcga_gdc", "gtex", "geo"])
    notes_zh: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StudyRecord:
    """Unified study-level record for TCGA/GTEx search results."""

    source: str
    study_id: str
    title_en: str = ""
    title_zh: str = ""
    summary_en: str = ""
    summary_zh: str = ""
    disease: str = ""
    tissue: str = ""
    access_level: str = "open"
    available_data_types: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FileRecord:
    """Unified file-level record for downloadable TCGA/GTEx assets."""

    source: str
    study_id: str
    file_id: str
    file_name: str
    file_type: str = ""
    guessed_role: str = ""
    download_url: str = ""
    local_path: str = ""
    size_hint: Optional[int] = None
    content_type: str = ""
    access_level: str = "open"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DownloadResult:
    """Unified download result shape for future GEO-compatible integration."""

    source: str
    study_id: str
    download_success: bool
    local_path: str
    metadata_path: str = ""
    error_message: str = ""
    parser_status: str = "not_started"
    status: str = "failed"
    message: str = ""
    output_dir: str = ""
    bundle_path: str = ""
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisBundle:
    """Minimal bundle summary object for analysis-ready outputs."""

    source: str
    study_id: str
    bundle_dir: str
    matrix_kind: str = "unknown"
    normalization_method: str = ""
    unit: str = ""
    is_log: Optional[bool] = None
    source_mode: str = "official"
    analysis_compatible: list[str] = field(default_factory=list)
    cross_source_safe: bool = False
    warning_messages: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ApiResponse:
    """Stable outward response shape for the module facade."""

    status: str
    message: str
    output_dir: str | None = None
    bundle_path: str | None = None
    warnings: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


@dataclass
class ConceptRecord:
    """Database-agnostic concept used across TCGA/GDC, GTEx, and future GEO."""

    concept_id: str
    concept_en: str
    concept_category: str
    parent_concept_id: str = ""
    synonyms_en: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SourceAdaptationRule:
    """Source-specific mapping rule derived from the shared concept layer."""

    concept_id: str
    source: str
    rule_kind: str
    target_field: str = ""
    target_value: str = ""
    target_term_id: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
