from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


BIOINFORMATICS_ALLOWED_SOURCES = ("geo", "tcga_gdc", "gtex")


@dataclass(frozen=True)
class StructuredBioinformaticsQuery:
    original_query_zh: str
    disease_terms_zh: tuple[str, ...]
    disease_terms_en: tuple[str, ...]
    synonyms: tuple[str, ...]
    abbreviations: tuple[str, ...]
    tissue_terms: tuple[str, ...]
    species: tuple[str, ...]
    data_modalities: tuple[str, ...]
    analysis_intent: str
    allowed_sources: tuple[str, ...] = BIOINFORMATICS_ALLOWED_SOURCES
    geo_query_candidates: tuple[str, ...] = ()
    tcga_project_ids: tuple[str, ...] = ()
    gtex_tissues: tuple[str, ...] = ()
    search_execution_status: str = "draft_only"
    broad_query_guard: bool = False
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UnifiedDatasetCandidate:
    source: str
    accession_or_project: str
    display_title: str
    organism: str
    disease: str
    tissue: str
    data_modality: str
    sample_count: int | str
    has_expression_matrix: bool
    has_sample_metadata: bool
    has_clinical_metadata: bool
    has_platform_annotation: bool
    recommended_analyses: tuple[str, ...]
    download_plan_available: bool
    score: int
    warnings: tuple[str, ...]
    source_specific_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceSearchResult:
    source: str
    search_status: str
    executed_query: str
    total_found: int | None
    returned_count: int
    displayed_count: int
    candidates: tuple[UnifiedDatasetCandidate, ...]
    warnings: tuple[str, ...]
    error_message: str = ""
    database_source: str = ""
    search_time: str = ""
    start: int = 0
    next_start: int | None = None
    fetched_all: bool = True
    query_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BioinformaticsSearchCenterResult:
    query: StructuredBioinformaticsQuery
    source_results: dict[str, SourceSearchResult]
    candidates: tuple[UnifiedDatasetCandidate, ...]
    online_enabled: bool
    search_time: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query.to_dict(),
            "source_results": {source: result.to_dict() for source, result in self.source_results.items()},
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "online_enabled": self.online_enabled,
            "search_time": self.search_time,
            "warnings": list(self.warnings),
        }
