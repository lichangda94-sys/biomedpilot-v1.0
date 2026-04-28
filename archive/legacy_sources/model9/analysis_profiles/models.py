from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from analysis.models import AnalysisMetric, AnalysisModelType
from extraction.models import OutcomeType
from literature.models import utc_now


class ComparisonEffectDirection(StrEnum):
    GROUP_A_OVER_B = "group_a_over_b"
    GROUP_B_OVER_A = "group_b_over_a"


class KeywordMatchMode(StrEnum):
    ANY = "any"
    ALL = "all"


class AnalysisProfileStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    ARCHIVED = "archived"


@dataclass(slots=True)
class GenePanel:
    gene_panel_id: str
    project_id: str
    name: str
    genes: list[str] = field(default_factory=list)
    description: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "gene_panel_id": self.gene_panel_id,
            "project_id": self.project_id,
            "name": self.name,
            "genes": list(self.genes),
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GenePanel":
        return cls(
            gene_panel_id=str(payload["gene_panel_id"]),
            project_id=str(payload["project_id"]),
            name=str(payload["name"]),
            genes=list(payload.get("genes", [])),
            description=str(payload.get("description", "")),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )


@dataclass(slots=True)
class ComparisonRule:
    comparison_rule_id: str
    project_id: str
    name: str
    group_a_label: str
    group_b_label: str
    effect_direction: ComparisonEffectDirection = ComparisonEffectDirection.GROUP_A_OVER_B
    description: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparison_rule_id": self.comparison_rule_id,
            "project_id": self.project_id,
            "name": self.name,
            "group_a_label": self.group_a_label,
            "group_b_label": self.group_b_label,
            "effect_direction": self.effect_direction.value,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ComparisonRule":
        return cls(
            comparison_rule_id=str(payload["comparison_rule_id"]),
            project_id=str(payload["project_id"]),
            name=str(payload["name"]),
            group_a_label=str(payload["group_a_label"]),
            group_b_label=str(payload["group_b_label"]),
            effect_direction=ComparisonEffectDirection(str(payload.get("effect_direction", ComparisonEffectDirection.GROUP_A_OVER_B.value))),
            description=str(payload.get("description", "")),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )


@dataclass(slots=True)
class KeywordRuleSet:
    keyword_rule_set_id: str
    project_id: str
    name: str
    keywords: list[str] = field(default_factory=list)
    match_mode: KeywordMatchMode = KeywordMatchMode.ANY
    description: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "keyword_rule_set_id": self.keyword_rule_set_id,
            "project_id": self.project_id,
            "name": self.name,
            "keywords": list(self.keywords),
            "match_mode": self.match_mode.value,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KeywordRuleSet":
        return cls(
            keyword_rule_set_id=str(payload["keyword_rule_set_id"]),
            project_id=str(payload["project_id"]),
            name=str(payload["name"]),
            keywords=list(payload.get("keywords", [])),
            match_mode=KeywordMatchMode(str(payload.get("match_mode", KeywordMatchMode.ANY.value))),
            description=str(payload.get("description", "")),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )


@dataclass(slots=True)
class ThresholdProfile:
    threshold_profile_id: str
    project_id: str
    name: str
    min_study_count: int | None = None
    max_i2: float | None = None
    alpha: float | None = None
    description: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "threshold_profile_id": self.threshold_profile_id,
            "project_id": self.project_id,
            "name": self.name,
            "min_study_count": self.min_study_count,
            "max_i2": self.max_i2,
            "alpha": self.alpha,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ThresholdProfile":
        return cls(
            threshold_profile_id=str(payload["threshold_profile_id"]),
            project_id=str(payload["project_id"]),
            name=str(payload["name"]),
            min_study_count=payload.get("min_study_count"),  # type: ignore[arg-type]
            max_i2=payload.get("max_i2"),  # type: ignore[arg-type]
            alpha=payload.get("alpha"),  # type: ignore[arg-type]
            description=str(payload.get("description", "")),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )


@dataclass(slots=True)
class AnalysisProfile:
    analysis_profile_id: str
    project_id: str
    name: str
    outcome_type: OutcomeType
    metric: AnalysisMetric
    model_type: AnalysisModelType
    comparison_rule_id: str
    threshold_profile_id: str
    gene_panel_id: str | None = None
    keyword_rule_set_id: str | None = None
    status: AnalysisProfileStatus = AnalysisProfileStatus.DRAFT
    description: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_profile_id": self.analysis_profile_id,
            "project_id": self.project_id,
            "name": self.name,
            "outcome_type": self.outcome_type.value,
            "metric": self.metric.value,
            "model_type": self.model_type.value,
            "comparison_rule_id": self.comparison_rule_id,
            "threshold_profile_id": self.threshold_profile_id,
            "gene_panel_id": self.gene_panel_id,
            "keyword_rule_set_id": self.keyword_rule_set_id,
            "status": self.status.value,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AnalysisProfile":
        return cls(
            analysis_profile_id=str(payload["analysis_profile_id"]),
            project_id=str(payload["project_id"]),
            name=str(payload["name"]),
            outcome_type=OutcomeType(str(payload["outcome_type"])),
            metric=AnalysisMetric(str(payload["metric"])),
            model_type=AnalysisModelType(str(payload["model_type"])),
            comparison_rule_id=str(payload["comparison_rule_id"]),
            threshold_profile_id=str(payload["threshold_profile_id"]),
            gene_panel_id=payload.get("gene_panel_id"),  # type: ignore[arg-type]
            keyword_rule_set_id=payload.get("keyword_rule_set_id"),  # type: ignore[arg-type]
            status=AnalysisProfileStatus(str(payload.get("status", AnalysisProfileStatus.DRAFT.value))),
            description=str(payload.get("description", "")),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )


@dataclass(slots=True)
class AnalysisProfileValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class EngineReadyAnalysisConfig:
    analysis_profile_id: str
    project_id: str
    outcome_type: OutcomeType
    metric: AnalysisMetric
    model_type: AnalysisModelType
    comparison: ComparisonRule
    thresholds: ThresholdProfile
    gene_panel: GenePanel | None = None
    keyword_rule_set: KeywordRuleSet | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_profile_id": self.analysis_profile_id,
            "project_id": self.project_id,
            "outcome_type": self.outcome_type.value,
            "metric": self.metric.value,
            "model_type": self.model_type.value,
            "comparison": self.comparison.to_dict(),
            "thresholds": self.thresholds.to_dict(),
            "gene_panel": self.gene_panel.to_dict() if self.gene_panel else None,
            "keyword_rule_set": self.keyword_rule_set.to_dict() if self.keyword_rule_set else None,
        }
