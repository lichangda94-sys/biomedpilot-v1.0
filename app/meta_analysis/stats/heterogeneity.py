from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.stats.meta_effects import StudyEffectEstimate


@dataclass(frozen=True)
class HeterogeneityStats:
    q_statistic: float
    i_squared: float
    tau_squared: float


def calculate_heterogeneity(effects: list[StudyEffectEstimate]) -> HeterogeneityStats:
    if not effects:
        return HeterogeneityStats(q_statistic=0.0, i_squared=0.0, tau_squared=0.0)
    fixed_weights = [1 / effect.variance for effect in effects]
    sum_fixed = sum(fixed_weights)
    pooled_fixed = sum(
        weight * effect.transformed_effect
        for weight, effect in zip(fixed_weights, effects, strict=True)
    ) / sum_fixed
    q_statistic = sum(
        weight * ((effect.transformed_effect - pooled_fixed) ** 2)
        for weight, effect in zip(fixed_weights, effects, strict=True)
    )
    df = len(effects) - 1
    if df <= 0:
        return HeterogeneityStats(q_statistic=q_statistic, i_squared=0.0, tau_squared=0.0)
    c_value = sum_fixed - (sum(weight**2 for weight in fixed_weights) / sum_fixed)
    tau_squared = max(0.0, (q_statistic - df) / c_value) if c_value > 0 else 0.0
    i_squared = max(0.0, ((q_statistic - df) / q_statistic) * 100) if q_statistic > 0 else 0.0
    return HeterogeneityStats(q_statistic=q_statistic, i_squared=i_squared, tau_squared=tau_squared)
