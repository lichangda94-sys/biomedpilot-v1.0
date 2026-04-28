from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from analysis.models import AnalysisMetric, AnalysisModelType
from analysis_profiles.models import (
    AnalysisProfile,
    AnalysisProfileStatus,
    AnalysisProfileValidationResult,
    ComparisonEffectDirection,
    ComparisonRule,
    EngineReadyAnalysisConfig,
    GenePanel,
    KeywordMatchMode,
    KeywordRuleSet,
    ThresholdProfile,
)
from analysis_profiles.store import AnalysisProfileStore
from extraction.models import OutcomeType


class AnalysisProfileService:
    def __init__(self, store: AnalysisProfileStore) -> None:
        self._store = store

    @classmethod
    def from_root_dir(cls, root_dir: Path) -> "AnalysisProfileService":
        return cls(AnalysisProfileStore(root_dir))

    def create_gene_panel(
        self,
        project_id: str,
        name: str,
        genes: list[str],
        *,
        description: str = "",
    ) -> GenePanel:
        self._require(project_id.strip(), "project_id is required.")
        self._require(name.strip(), "Gene panel name is required.")
        normalized_genes = _normalize_unique(genes)
        self._require(normalized_genes, "Gene panel requires at least one gene.")
        return self._store.save_gene_panel(
            GenePanel(
                gene_panel_id=f"gpanel-{uuid4().hex[:12]}",
                project_id=project_id.strip(),
                name=name.strip(),
                genes=normalized_genes,
                description=description.strip(),
            )
        )

    def create_comparison_rule(
        self,
        project_id: str,
        name: str,
        group_a_label: str,
        group_b_label: str,
        *,
        effect_direction: ComparisonEffectDirection = ComparisonEffectDirection.GROUP_A_OVER_B,
        description: str = "",
    ) -> ComparisonRule:
        self._require(project_id.strip(), "project_id is required.")
        self._require(name.strip(), "Comparison rule name is required.")
        self._require(group_a_label.strip(), "group_a_label is required.")
        self._require(group_b_label.strip(), "group_b_label is required.")
        self._require(group_a_label.strip() != group_b_label.strip(), "Comparison groups must differ.")
        return self._store.save_comparison_rule(
            ComparisonRule(
                comparison_rule_id=f"compr-{uuid4().hex[:12]}",
                project_id=project_id.strip(),
                name=name.strip(),
                group_a_label=group_a_label.strip(),
                group_b_label=group_b_label.strip(),
                effect_direction=effect_direction,
                description=description.strip(),
            )
        )

    def create_keyword_rule_set(
        self,
        project_id: str,
        name: str,
        keywords: list[str],
        *,
        match_mode: KeywordMatchMode = KeywordMatchMode.ANY,
        description: str = "",
    ) -> KeywordRuleSet:
        self._require(project_id.strip(), "project_id is required.")
        self._require(name.strip(), "Keyword rule set name is required.")
        normalized_keywords = _normalize_unique(keywords)
        self._require(normalized_keywords, "Keyword rule set requires at least one keyword.")
        return self._store.save_keyword_rule_set(
            KeywordRuleSet(
                keyword_rule_set_id=f"kset-{uuid4().hex[:12]}",
                project_id=project_id.strip(),
                name=name.strip(),
                keywords=normalized_keywords,
                match_mode=match_mode,
                description=description.strip(),
            )
        )

    def create_threshold_profile(
        self,
        project_id: str,
        name: str,
        *,
        min_study_count: int | None = None,
        max_i2: float | None = None,
        alpha: float | None = None,
        description: str = "",
    ) -> ThresholdProfile:
        self._require(project_id.strip(), "project_id is required.")
        self._require(name.strip(), "Threshold profile name is required.")
        self._validate_threshold_values(min_study_count=min_study_count, max_i2=max_i2, alpha=alpha)
        return self._store.save_threshold_profile(
            ThresholdProfile(
                threshold_profile_id=f"thr-{uuid4().hex[:12]}",
                project_id=project_id.strip(),
                name=name.strip(),
                min_study_count=min_study_count,
                max_i2=max_i2,
                alpha=alpha,
                description=description.strip(),
            )
        )

    def create_analysis_profile(
        self,
        project_id: str,
        name: str,
        *,
        outcome_type: OutcomeType,
        metric: AnalysisMetric,
        model_type: AnalysisModelType,
        comparison_rule_id: str,
        threshold_profile_id: str,
        gene_panel_id: str | None = None,
        keyword_rule_set_id: str | None = None,
        description: str = "",
    ) -> AnalysisProfile:
        self._require(project_id.strip(), "project_id is required.")
        self._require(name.strip(), "Analysis profile name is required.")
        profile = AnalysisProfile(
            analysis_profile_id=f"aprof-{uuid4().hex[:12]}",
            project_id=project_id.strip(),
            name=name.strip(),
            outcome_type=outcome_type,
            metric=metric,
            model_type=model_type,
            comparison_rule_id=comparison_rule_id,
            threshold_profile_id=threshold_profile_id,
            gene_panel_id=gene_panel_id,
            keyword_rule_set_id=keyword_rule_set_id,
            description=description.strip(),
        )
        result = self.validate_analysis_profile(profile)
        if result.errors:
            raise ValueError("; ".join(result.errors))
        return self._store.save_analysis_profile(profile)

    def validate_analysis_profile(
        self,
        profile: AnalysisProfile,
    ) -> AnalysisProfileValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        if not self._metric_supported(profile.outcome_type, profile.metric):
            errors.append(f"Metric {profile.metric.value} is not supported for {profile.outcome_type.value}.")
        comparison = self._store.get_comparison_rule(profile.comparison_rule_id)
        if comparison is None:
            errors.append(f"Comparison rule does not exist: {profile.comparison_rule_id}")
        elif comparison.project_id != profile.project_id:
            errors.append("Comparison rule belongs to a different project.")
        threshold = self._store.get_threshold_profile(profile.threshold_profile_id)
        if threshold is None:
            errors.append(f"Threshold profile does not exist: {profile.threshold_profile_id}")
        elif threshold.project_id != profile.project_id:
            errors.append("Threshold profile belongs to a different project.")
        if profile.gene_panel_id:
            gene_panel = self._store.get_gene_panel(profile.gene_panel_id)
            if gene_panel is None:
                errors.append(f"Gene panel does not exist: {profile.gene_panel_id}")
            elif gene_panel.project_id != profile.project_id:
                errors.append("Gene panel belongs to a different project.")
        else:
            warnings.append("No gene panel attached.")
        if profile.keyword_rule_set_id:
            keyword_set = self._store.get_keyword_rule_set(profile.keyword_rule_set_id)
            if keyword_set is None:
                errors.append(f"Keyword rule set does not exist: {profile.keyword_rule_set_id}")
            elif keyword_set.project_id != profile.project_id:
                errors.append("Keyword rule set belongs to a different project.")
        else:
            warnings.append("No keyword rule set attached.")
        return AnalysisProfileValidationResult(valid=not errors, errors=errors, warnings=warnings)

    def mark_ready(self, analysis_profile_id: str) -> AnalysisProfile:
        profile = self._require_analysis_profile(analysis_profile_id)
        validation = self.validate_analysis_profile(profile)
        if validation.errors:
            raise ValueError("; ".join(validation.errors))
        profile.status = AnalysisProfileStatus.READY
        profile.touch()
        return self._store.save_analysis_profile(profile)

    def export_engine_config(self, analysis_profile_id: str) -> EngineReadyAnalysisConfig:
        profile = self._require_analysis_profile(analysis_profile_id)
        validation = self.validate_analysis_profile(profile)
        if validation.errors:
            raise ValueError("; ".join(validation.errors))
        comparison = self._require_comparison_rule(profile.comparison_rule_id)
        threshold = self._require_threshold_profile(profile.threshold_profile_id)
        gene_panel = self._store.get_gene_panel(profile.gene_panel_id) if profile.gene_panel_id else None
        keyword_set = self._store.get_keyword_rule_set(profile.keyword_rule_set_id) if profile.keyword_rule_set_id else None
        return EngineReadyAnalysisConfig(
            analysis_profile_id=profile.analysis_profile_id,
            project_id=profile.project_id,
            outcome_type=profile.outcome_type,
            metric=profile.metric,
            model_type=profile.model_type,
            comparison=comparison,
            thresholds=threshold,
            gene_panel=gene_panel,
            keyword_rule_set=keyword_set,
        )

    def list_analysis_profiles(self, project_id: str) -> list[AnalysisProfile]:
        return self._store.list_analysis_profiles(project_id=project_id)

    def list_gene_panels(self, project_id: str) -> list[GenePanel]:
        return self._store.list_gene_panels(project_id=project_id)

    def list_comparison_rules(self, project_id: str) -> list[ComparisonRule]:
        return self._store.list_comparison_rules(project_id=project_id)

    def list_keyword_rule_sets(self, project_id: str) -> list[KeywordRuleSet]:
        return self._store.list_keyword_rule_sets(project_id=project_id)

    def list_threshold_profiles(self, project_id: str) -> list[ThresholdProfile]:
        return self._store.list_threshold_profiles(project_id=project_id)

    def _require_analysis_profile(self, analysis_profile_id: str) -> AnalysisProfile:
        profile = self._store.get_analysis_profile(analysis_profile_id)
        if profile is None:
            raise ValueError(f"Analysis profile does not exist: {analysis_profile_id}")
        return profile

    def _require_comparison_rule(self, comparison_rule_id: str) -> ComparisonRule:
        record = self._store.get_comparison_rule(comparison_rule_id)
        if record is None:
            raise ValueError(f"Comparison rule does not exist: {comparison_rule_id}")
        return record

    def _require_threshold_profile(self, threshold_profile_id: str) -> ThresholdProfile:
        record = self._store.get_threshold_profile(threshold_profile_id)
        if record is None:
            raise ValueError(f"Threshold profile does not exist: {threshold_profile_id}")
        return record

    def _validate_threshold_values(
        self,
        *,
        min_study_count: int | None,
        max_i2: float | None,
        alpha: float | None,
    ) -> None:
        if min_study_count is not None and min_study_count < 1:
            raise ValueError("min_study_count must be >= 1.")
        if max_i2 is not None and not (0 <= max_i2 <= 100):
            raise ValueError("max_i2 must be between 0 and 100.")
        if alpha is not None and not (0 < alpha < 1):
            raise ValueError("alpha must be between 0 and 1.")

    def _metric_supported(self, outcome_type: OutcomeType, metric: AnalysisMetric) -> bool:
        supported = {
            OutcomeType.BINARY: {AnalysisMetric.OR, AnalysisMetric.RR},
            OutcomeType.CONTINUOUS: {AnalysisMetric.MD, AnalysisMetric.SMD},
            OutcomeType.TIME_TO_EVENT: {AnalysisMetric.HR},
        }
        return metric in supported[outcome_type]

    def _require(self, condition: object, message: str) -> None:
        if not condition:
            raise ValueError(message)


AnalysisRuleService = AnalysisProfileService


def _normalize_unique(values: list[str]) -> list[str]:
    normalized = []
    seen = set()
    for value in values:
        item = value.strip()
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        normalized.append(item)
        seen.add(key)
    return normalized
