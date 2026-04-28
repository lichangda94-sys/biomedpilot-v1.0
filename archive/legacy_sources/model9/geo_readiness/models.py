from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GeoRemoteAssetCandidate:
    candidate_type: str
    name: str
    url: str = ""
    size_hint: str = ""
    confidence: float = 0.0
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_type": self.candidate_type,
            "name": self.name,
            "url": self.url,
            "size_hint": self.size_hint,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class GeoAccessionInventory:
    gse_id: str
    title: str = ""
    summary: str = ""
    organism: str = ""
    sample_count: int = 0
    platform_ids: list[str] = field(default_factory=list)
    series_matrix_candidates: list[GeoRemoteAssetCandidate] = field(default_factory=list)
    supplementary_candidates: list[GeoRemoteAssetCandidate] = field(default_factory=list)
    sample_metadata_candidates: list[GeoRemoteAssetCandidate] = field(default_factory=list)
    expression_candidates: list[GeoRemoteAssetCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.expression_candidates:
            self.warnings.append("no_expression_candidate")

    def to_dict(self) -> dict[str, Any]:
        return {
            "gse_id": self.gse_id,
            "title": self.title,
            "summary": self.summary,
            "organism": self.organism,
            "sample_count": self.sample_count,
            "platform_ids": list(self.platform_ids),
            "series_matrix_candidates": [
                candidate.to_dict() for candidate in self.series_matrix_candidates
            ],
            "supplementary_candidates": [
                candidate.to_dict() for candidate in self.supplementary_candidates
            ],
            "sample_metadata_candidates": [
                candidate.to_dict() for candidate in self.sample_metadata_candidates
            ],
            "expression_candidates": [
                candidate.to_dict() for candidate in self.expression_candidates
            ],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass(slots=True)
class SeriesMatrixMetadataReport:
    gse_id: str = ""
    platform_ids: list[str] = field(default_factory=list)
    sample_ids: list[str] = field(default_factory=list)
    sample_count: int = 0
    sample_metadata_columns: list[str] = field(default_factory=list)
    sample_metadata_rows: list[dict[str, str]] = field(default_factory=list)
    group_hints: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gse_id": self.gse_id,
            "platform_ids": list(self.platform_ids),
            "sample_ids": list(self.sample_ids),
            "sample_count": self.sample_count,
            "sample_metadata_columns": list(self.sample_metadata_columns),
            "sample_metadata_rows": [dict(row) for row in self.sample_metadata_rows],
            "group_hints": list(self.group_hints),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass(slots=True)
class SeriesMatrixExpressionReport:
    feature_count: int = 0
    sample_count: int = 0
    feature_id_column: str = ""
    matrix_sample_ids: list[str] = field(default_factory=list)
    numeric_value_status: str = "not_checked"
    missing_value_count: int = 0
    negative_value_count: int = 0
    sample_id_match_status: str = "not_checked"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_count": self.feature_count,
            "sample_count": self.sample_count,
            "feature_id_column": self.feature_id_column,
            "matrix_sample_ids": list(self.matrix_sample_ids),
            "numeric_value_status": self.numeric_value_status,
            "missing_value_count": self.missing_value_count,
            "negative_value_count": self.negative_value_count,
            "sample_id_match_status": self.sample_id_match_status,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass(slots=True)
class PlatformAnnotationMappingReport:
    platform_id: str = ""
    probe_count: int = 0
    mapped_probe_count: int = 0
    unmapped_probe_count: int = 0
    duplicated_symbol_count: int = 0
    mapping_success_rate: float = 0.0
    acceptable: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform_id": self.platform_id,
            "probe_count": self.probe_count,
            "mapped_probe_count": self.mapped_probe_count,
            "unmapped_probe_count": self.unmapped_probe_count,
            "duplicated_symbol_count": self.duplicated_symbol_count,
            "mapping_success_rate": self.mapping_success_rate,
            "acceptable": self.acceptable,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }
