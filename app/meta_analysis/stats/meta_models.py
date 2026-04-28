from __future__ import annotations

import math
from dataclasses import dataclass

from app.meta_analysis.stats.heterogeneity import calculate_heterogeneity
from app.meta_analysis.stats.meta_effects import StudyEffectEstimate, report_effect_values


@dataclass(frozen=True)
class PooledEffectEstimate:
    model: str
    pooled_effect: float
    ci_lower: float
    ci_upper: float
    p_value: float
    q_statistic: float
    i_squared: float
    tau_squared: float
    weights: list[float]


def pool_effects(effects: list[StudyEffectEstimate], *, effect_measure: str, model: str) -> PooledEffectEstimate:
    normalized_model = model.strip().lower()
    if normalized_model not in {"fixed", "random"}:
        raise ValueError("model must be fixed or random")
    if not effects:
        raise ValueError("meta analysis requires at least one study effect")

    heterogeneity = calculate_heterogeneity(effects)
    if normalized_model == "random":
        weights = [1 / (effect.variance + heterogeneity.tau_squared) for effect in effects]
    else:
        weights = [1 / effect.variance for effect in effects]
    pooled_theta = sum(
        weight * effect.transformed_effect
        for weight, effect in zip(weights, effects, strict=True)
    ) / sum(weights)
    pooled_variance = 1 / sum(weights)
    pooled_se = math.sqrt(pooled_variance)
    pooled_effect, ci_lower, ci_upper = report_effect_values(effect_measure, pooled_theta, pooled_se)
    z_value = pooled_theta / pooled_se if pooled_se > 0 else 0.0
    p_value = math.erfc(abs(z_value) / math.sqrt(2))
    return PooledEffectEstimate(
        model=normalized_model,
        pooled_effect=pooled_effect,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        p_value=p_value,
        q_statistic=heterogeneity.q_statistic,
        i_squared=heterogeneity.i_squared,
        tau_squared=heterogeneity.tau_squared,
        weights=weights,
    )
