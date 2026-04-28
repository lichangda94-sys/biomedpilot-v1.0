from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from analysis.models import (
    AnalysisInput,
    AnalysisMetric,
    AnalysisModelType,
    MetaResult,
    StudyEffectResult,
)
from analysis.profile_adapter import build_profile_analysis_input
from analysis.store import AnalysisStore
from analysis_profiles.models import EngineReadyAnalysisConfig
from extraction.models import OutcomeRecord, OutcomeType
from extraction.store import ExtractionStore


LOG_SCALE_METRICS = {
    AnalysisMetric.OR,
    AnalysisMetric.RR,
    AnalysisMetric.HR,
}


class AnalysisService:
    def __init__(
        self,
        extraction_store: ExtractionStore,
        analysis_store: AnalysisStore,
    ) -> None:
        self._extraction_store = extraction_store
        self._analysis_store = analysis_store

    @classmethod
    def from_root_dir(cls, root_dir: Path) -> "AnalysisService":
        return cls(ExtractionStore(root_dir), AnalysisStore(root_dir))

    def create_analysis(
        self,
        project_id: str,
        outcome_record_ids: list[str],
        *,
        outcome_type: OutcomeType,
        metric: AnalysisMetric,
        model_type: AnalysisModelType,
    ) -> AnalysisInput:
        return self._create_analysis(
            project_id,
            outcome_record_ids,
            outcome_type=outcome_type,
            metric=metric,
            model_type=model_type,
        )

    def create_analysis_from_profile_config(
        self,
        config: EngineReadyAnalysisConfig,
        outcome_record_ids: list[str],
    ) -> AnalysisInput:
        profile_input = build_profile_analysis_input(config, outcome_record_ids)
        return self._create_analysis(
            profile_input.project_id,
            profile_input.outcome_record_ids,
            outcome_type=profile_input.outcome_type,
            metric=profile_input.metric,
            model_type=profile_input.model_type,
            analysis_profile_id=profile_input.analysis_profile_id,
        )

    def _create_analysis(
        self,
        project_id: str,
        outcome_record_ids: list[str],
        *,
        outcome_type: OutcomeType,
        metric: AnalysisMetric,
        model_type: AnalysisModelType,
        analysis_profile_id: str | None = None,
    ) -> AnalysisInput:
        if not outcome_record_ids:
            raise ValueError("Analysis requires at least one outcome_record_id.")
        outcomes = [self._require_outcome_record(record_id) for record_id in outcome_record_ids]
        self._validate_metric_support(outcome_type, metric)
        for outcome in outcomes:
            if outcome.outcome_type != outcome_type:
                raise ValueError(
                    f"Outcome {outcome.outcome_record_id} type mismatch: expected {outcome_type.value}, got {outcome.outcome_type.value}."
                )
        analysis = AnalysisInput(
            analysis_id=f"analysis-{uuid4().hex[:12]}",
            project_id=project_id,
            outcome_record_ids=list(outcome_record_ids),
            outcome_type=outcome_type,
            metric=metric,
            model_type=model_type,
            analysis_profile_id=analysis_profile_id,
        )
        return self._analysis_store.save_analysis_input(analysis)

    def calculate_study_effects(self, analysis_id: str) -> list[StudyEffectResult]:
        analysis = self._require_analysis(analysis_id)
        effects = [
            self._compute_study_effect(analysis, self._require_outcome_record(outcome_id))
            for outcome_id in analysis.outcome_record_ids
        ]
        return self._analysis_store.replace_study_effects(analysis.analysis_id, effects)

    def run_analysis(self, analysis_id: str) -> MetaResult:
        analysis = self._require_analysis(analysis_id)
        study_effects = self.calculate_study_effects(analysis.analysis_id)
        result = self._pool_effects(analysis, study_effects)
        return self._analysis_store.save_meta_result(result)

    def list_study_effects(self, analysis_id: str) -> list[StudyEffectResult]:
        return self._analysis_store.list_study_effects(analysis_id=analysis_id)

    def list_meta_results(self, analysis_id: str) -> list[MetaResult]:
        return self._analysis_store.list_meta_results(analysis_id=analysis_id)

    def _compute_study_effect(
        self,
        analysis: AnalysisInput,
        outcome: OutcomeRecord,
    ) -> StudyEffectResult:
        if analysis.outcome_type == OutcomeType.BINARY:
            return self._binary_effect(analysis, outcome)
        if analysis.outcome_type == OutcomeType.CONTINUOUS:
            return self._continuous_effect(analysis, outcome)
        if analysis.outcome_type == OutcomeType.TIME_TO_EVENT:
            return self._time_to_event_effect(analysis, outcome)
        raise ValueError(f"Unsupported outcome type: {analysis.outcome_type.value}")

    def _binary_effect(
        self,
        analysis: AnalysisInput,
        outcome: OutcomeRecord,
    ) -> StudyEffectResult:
        self._require(
            outcome.group_a_n is not None
            and outcome.group_b_n is not None
            and outcome.events_a is not None
            and outcome.events_b is not None,
            f"Outcome {outcome.outcome_record_id} requires 2x2 data for binary analysis.",
        )
        a = float(outcome.events_a)
        c = float(outcome.events_b)
        b = float(outcome.group_a_n - outcome.events_a)
        d = float(outcome.group_b_n - outcome.events_b)
        if min(a, b, c, d) < 0:
            raise ValueError(
                f"Outcome {outcome.outcome_record_id} has invalid binary counts."
            )
        if min(a, b, c, d) == 0:
            a += 0.5
            b += 0.5
            c += 0.5
            d += 0.5

        if analysis.metric == AnalysisMetric.OR:
            theta = math.log((a * d) / (b * c))
            variance = (1 / a) + (1 / b) + (1 / c) + (1 / d)
        elif analysis.metric == AnalysisMetric.RR:
            n1 = a + b
            n0 = c + d
            theta = math.log((a / n1) / (c / n0))
            variance = (1 / a) - (1 / n1) + (1 / c) - (1 / n0)
        else:
            raise ValueError(f"Unsupported binary metric: {analysis.metric.value}")
        return self._make_study_effect(analysis, outcome, theta, variance)

    def _continuous_effect(
        self,
        analysis: AnalysisInput,
        outcome: OutcomeRecord,
    ) -> StudyEffectResult:
        self._require(
            outcome.group_a_n is not None
            and outcome.group_b_n is not None
            and outcome.mean_a is not None
            and outcome.mean_b is not None
            and outcome.sd_a is not None
            and outcome.sd_b is not None,
            f"Outcome {outcome.outcome_record_id} requires n, mean, and sd for continuous analysis.",
        )
        n1 = float(outcome.group_a_n)
        n0 = float(outcome.group_b_n)
        self._require(n1 > 1 and n0 > 1, f"Outcome {outcome.outcome_record_id} requires group sizes > 1.")
        mean_diff = float(outcome.mean_a - outcome.mean_b)
        if analysis.metric == AnalysisMetric.MD:
            variance = (float(outcome.sd_a) ** 2 / n1) + (float(outcome.sd_b) ** 2 / n0)
            theta = mean_diff
        elif analysis.metric == AnalysisMetric.SMD:
            pooled_sd_num = ((n1 - 1) * float(outcome.sd_a) ** 2) + ((n0 - 1) * float(outcome.sd_b) ** 2)
            pooled_sd_den = n1 + n0 - 2
            self._require(pooled_sd_den > 0, f"Outcome {outcome.outcome_record_id} has invalid pooled sd denominator.")
            pooled_sd = math.sqrt(pooled_sd_num / pooled_sd_den)
            self._require(pooled_sd > 0, f"Outcome {outcome.outcome_record_id} has zero pooled sd.")
            d = mean_diff / pooled_sd
            correction = 1 - (3 / (4 * (n1 + n0) - 9))
            theta = correction * d
            variance = ((n1 + n0) / (n1 * n0)) + ((theta ** 2) / (2 * (n1 + n0 - 2)))
        else:
            raise ValueError(f"Unsupported continuous metric: {analysis.metric.value}")
        return self._make_study_effect(analysis, outcome, theta, variance)

    def _time_to_event_effect(
        self,
        analysis: AnalysisInput,
        outcome: OutcomeRecord,
    ) -> StudyEffectResult:
        self._require(
            outcome.hr is not None
            and outcome.ci_lower is not None
            and outcome.ci_upper is not None,
            f"Outcome {outcome.outcome_record_id} requires hr and confidence interval for time-to-event analysis.",
        )
        self._require(
            analysis.metric == AnalysisMetric.HR,
            f"Time-to-event analysis only supports HR, got {analysis.metric.value}.",
        )
        hr = float(outcome.hr)
        ci_lower = float(outcome.ci_lower)
        ci_upper = float(outcome.ci_upper)
        self._require(hr > 0 and ci_lower > 0 and ci_upper > 0, f"Outcome {outcome.outcome_record_id} has non-positive HR inputs.")
        theta = math.log(hr)
        se = (math.log(ci_upper) - math.log(ci_lower)) / (2 * 1.96)
        variance = se ** 2
        return self._make_study_effect(analysis, outcome, theta, variance)

    def _make_study_effect(
        self,
        analysis: AnalysisInput,
        outcome: OutcomeRecord,
        theta: float,
        variance: float,
    ) -> StudyEffectResult:
        self._require(variance > 0, f"Outcome {outcome.outcome_record_id} produced non-positive variance.")
        se = math.sqrt(variance)
        effect_value, ci_lower, ci_upper = self._report_effect_values(
            analysis.metric,
            theta,
            se,
        )
        return StudyEffectResult(
            study_effect_id=f"seff-{uuid4().hex[:12]}",
            analysis_id=analysis.analysis_id,
            outcome_record_id=outcome.outcome_record_id,
            metric=analysis.metric,
            effect_value=effect_value,
            standard_error=se,
            variance=variance,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            weight_fixed=1 / variance,
        )

    def _pool_effects(
        self,
        analysis: AnalysisInput,
        study_effects: list[StudyEffectResult],
    ) -> MetaResult:
        self._require(study_effects, f"Analysis {analysis.analysis_id} has no study effects to pool.")
        transformed_effects = [self._effect_to_analysis_scale(effect) for effect in study_effects]
        fixed_weights = [1 / effect.variance for effect in study_effects]
        sum_fixed = sum(fixed_weights)
        pooled_fixed = sum(weight * theta for weight, theta in zip(fixed_weights, transformed_effects, strict=True)) / sum_fixed
        q_statistic = sum(
            weight * ((theta - pooled_fixed) ** 2)
            for weight, theta in zip(fixed_weights, transformed_effects, strict=True)
        )
        df = max(len(study_effects) - 1, 0)
        if df == 0:
            tau2 = 0.0
            i2 = 0.0
        else:
            c_value = sum_fixed - (sum(weight ** 2 for weight in fixed_weights) / sum_fixed)
            tau2 = max(0.0, (q_statistic - df) / c_value) if c_value > 0 else 0.0
            i2 = max(0.0, ((q_statistic - df) / q_statistic) * 100) if q_statistic > 0 else 0.0

        if analysis.model_type == AnalysisModelType.RANDOM_EFFECT:
            random_weights = [1 / (effect.variance + tau2) for effect in study_effects]
            pooled_theta = sum(
                weight * theta
                for weight, theta in zip(random_weights, transformed_effects, strict=True)
            ) / sum(random_weights)
            pooled_variance = 1 / sum(random_weights)
            for index, effect in enumerate(study_effects):
                study_effects[index] = replace(
                    effect,
                    weight_random=random_weights[index],
                )
            self._analysis_store.replace_study_effects(analysis.analysis_id, study_effects)
        else:
            pooled_theta = pooled_fixed
            pooled_variance = 1 / sum_fixed

        pooled_se = math.sqrt(pooled_variance)
        pooled_effect, ci_lower, ci_upper = self._report_effect_values(
            analysis.metric,
            pooled_theta,
            pooled_se,
        )
        z_value = pooled_theta / pooled_se if pooled_se > 0 else 0.0
        p_value = math.erfc(abs(z_value) / math.sqrt(2))
        return MetaResult(
            meta_result_id=f"meta-{uuid4().hex[:12]}",
            analysis_id=analysis.analysis_id,
            metric=analysis.metric,
            model_type=analysis.model_type,
            pooled_effect=pooled_effect,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            p_value=p_value,
            tau2=tau2,
            q_statistic=q_statistic,
            i2=i2,
            study_count=len(study_effects),
        )

    def _report_effect_values(
        self,
        metric: AnalysisMetric,
        theta: float,
        se: float,
    ) -> tuple[float, float, float]:
        ci_low_theta = theta - (1.96 * se)
        ci_high_theta = theta + (1.96 * se)
        if metric in LOG_SCALE_METRICS:
            return (
                math.exp(theta),
                math.exp(ci_low_theta),
                math.exp(ci_high_theta),
            )
        return (theta, ci_low_theta, ci_high_theta)

    def _effect_to_analysis_scale(self, effect: StudyEffectResult) -> float:
        if effect.metric in LOG_SCALE_METRICS:
            return math.log(effect.effect_value)
        return effect.effect_value

    def _validate_metric_support(
        self,
        outcome_type: OutcomeType,
        metric: AnalysisMetric,
    ) -> None:
        supported = {
            OutcomeType.BINARY: {AnalysisMetric.OR, AnalysisMetric.RR},
            OutcomeType.CONTINUOUS: {AnalysisMetric.MD, AnalysisMetric.SMD},
            OutcomeType.TIME_TO_EVENT: {AnalysisMetric.HR},
        }
        if metric not in supported[outcome_type]:
            raise ValueError(
                f"Metric {metric.value} is not supported for outcome type {outcome_type.value}."
            )

    def _require_analysis(self, analysis_id: str) -> AnalysisInput:
        analysis = self._analysis_store.get_analysis_input(analysis_id)
        if analysis is None:
            raise ValueError(f"Analysis does not exist: {analysis_id}")
        return analysis

    def _require_outcome_record(self, outcome_record_id: str) -> OutcomeRecord:
        record = self._extraction_store.get_outcome_record(outcome_record_id)
        if record is None:
            raise ValueError(f"Outcome record does not exist: {outcome_record_id}")
        return record

    def _require(self, condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)
