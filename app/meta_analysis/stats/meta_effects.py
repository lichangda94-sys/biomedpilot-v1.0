from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.meta_analysis.models.analysis_dataset import StudyAnalysisRow


LOG_SCALE_EFFECT_MEASURES = {"OR", "RR", "HR", "PLR", "NLR", "DOR"}
LOGIT_SCALE_EFFECT_MEASURES = {"PREVALENCE", "INCIDENCE", "PROPORTION", "SINGLE_ARM", "SENSITIVITY", "SPECIFICITY"}
CORRELATION_EFFECT_MEASURES = {"CORRELATION", "PEARSON_R", "SPEARMAN_R"}


@dataclass(frozen=True)
class StudyEffectEstimate:
    study_id: str
    record_id: str
    first_author: str
    year: int | None
    effect_measure: str
    effect: float
    ci_lower: float
    ci_upper: float
    standard_error: float
    variance: float
    transformed_effect: float
    adjusted: bool = False
    covariates: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def study_effect_from_row(row: StudyAnalysisRow) -> StudyEffectEstimate:
    if row.outcome_data_type == "binary":
        return binary_study_effect(row)
    if row.outcome_data_type == "continuous":
        return continuous_study_effect(row)
    if row.outcome_data_type == "generic_effect":
        return generic_inverse_variance_effect(row)
    if row.outcome_data_type == "proportion":
        return proportion_study_effect(row)
    if row.outcome_data_type == "correlation":
        return correlation_study_effect(row)
    if row.outcome_data_type == "diagnostic_accuracy":
        return diagnostic_accuracy_study_effect(row)
    raise ValueError(f"Unsupported outcome data type: {row.outcome_data_type}")


def binary_study_effect(row: StudyAnalysisRow) -> StudyEffectEstimate:
    data = row.normalized_data
    measure = str(data["effect_measure"])
    a = float(data["experimental_events"])
    b = float(data["experimental_non_events"])
    n1 = float(data["experimental_total"])
    c = float(data["control_events"])
    d = float(data["control_non_events"])
    n0 = float(data["control_total"])
    warnings = list(row.warnings)
    if min(a, b, c, d) < 0 or n1 <= 0 or n0 <= 0:
        raise ValueError(f"Invalid binary data for record {row.record_id}.")
    if measure in {"OR", "RR"} and min(a, b, c, d) == 0:
        a += 0.5
        b += 0.5
        c += 0.5
        d += 0.5
        n1 = a + b
        n0 = c + d
        warnings.append("zero_event_correction_applied")
    if measure == "OR":
        theta = math.log((a * d) / (b * c))
        variance = (1 / a) + (1 / b) + (1 / c) + (1 / d)
    elif measure == "RR":
        theta = math.log((a / n1) / (c / n0))
        variance = (1 / a) - (1 / n1) + (1 / c) - (1 / n0)
    elif measure == "RD":
        p1 = a / n1
        p0 = c / n0
        theta = p1 - p0
        variance = (p1 * (1 - p1) / n1) + (p0 * (1 - p0) / n0)
        if variance <= 0:
            variance = 1 / (n1 + n0)
            warnings.append("risk_difference_zero_variance_continuity_warning")
    else:
        raise ValueError(f"Unsupported binary effect measure: {measure}")
    return _make_effect(row, measure, theta, variance, warnings=warnings)


def continuous_study_effect(row: StudyAnalysisRow) -> StudyEffectEstimate:
    data = row.normalized_data
    measure = str(data["effect_measure"])
    n1 = float(data["experimental_total"])
    n0 = float(data["control_total"])
    mean1 = float(data["experimental_mean"])
    mean0 = float(data["control_mean"])
    sd1 = float(data["experimental_sd"])
    sd0 = float(data["control_sd"])
    if n1 <= 1 or n0 <= 1 or sd1 < 0 or sd0 < 0:
        raise ValueError(f"Invalid continuous data for record {row.record_id}.")
    mean_diff = mean1 - mean0
    if measure == "MD":
        theta = mean_diff
        variance = (sd1**2 / n1) + (sd0**2 / n0)
    elif measure == "SMD":
        pooled_sd_den = n1 + n0 - 2
        pooled_sd = math.sqrt((((n1 - 1) * sd1**2) + ((n0 - 1) * sd0**2)) / pooled_sd_den)
        if pooled_sd <= 0:
            raise ValueError(f"Continuous data produced zero pooled SD for record {row.record_id}.")
        cohen_d = mean_diff / pooled_sd
        hedges_correction = 1 - (3 / (4 * (n1 + n0) - 9))
        theta = hedges_correction * cohen_d
        variance = ((n1 + n0) / (n1 * n0)) + ((theta**2) / (2 * (n1 + n0 - 2)))
    else:
        raise ValueError(f"Unsupported continuous effect measure: {measure}")
    return _make_effect(row, measure, theta, variance, warnings=list(row.warnings))


def generic_inverse_variance_effect(row: StudyAnalysisRow) -> StudyEffectEstimate:
    data = row.normalized_data
    measure = str(data["effect_measure"])
    effect = float(data["effect"])
    ci_lower = _optional_float(data.get("ci_lower"))
    ci_upper = _optional_float(data.get("ci_upper"))
    standard_error = _optional_float(data.get("standard_error"))
    if measure in LOG_SCALE_EFFECT_MEASURES:
        if effect <= 0:
            raise ValueError(f"Generic ratio effect must be positive for record {row.record_id}.")
        theta = math.log(effect)
        if standard_error is None:
            if ci_lower is None or ci_upper is None or ci_lower <= 0 or ci_upper <= 0:
                raise ValueError(f"Generic ratio effect requires positive CI or SE for record {row.record_id}.")
            standard_error = ci_to_standard_error(ci_lower, ci_upper, log_scale=True)
    else:
        theta = effect
        if standard_error is None:
            if ci_lower is None or ci_upper is None:
                raise ValueError(f"Generic inverse variance effect requires CI or SE for record {row.record_id}.")
            standard_error = ci_to_standard_error(ci_lower, ci_upper, log_scale=False)
    variance = standard_error**2
    if variance <= 0:
        raise ValueError(f"Generic inverse variance effect produced non-positive variance for record {row.record_id}.")
    reported_effect, reported_low, reported_high = report_effect_values(measure, theta, standard_error)
    return StudyEffectEstimate(
        study_id=row.study_id,
        record_id=row.record_id,
        first_author=row.first_author,
        year=row.year,
        effect_measure=measure,
        effect=reported_effect,
        ci_lower=reported_low,
        ci_upper=reported_high,
        standard_error=standard_error,
        variance=variance,
        transformed_effect=theta,
        adjusted=bool(data.get("adjusted", False)),
        covariates=[str(item) for item in data.get("covariates", [])],
        warnings=list(row.warnings),
    )


def proportion_study_effect(row: StudyAnalysisRow) -> StudyEffectEstimate:
    data = row.normalized_data
    measure = str(data["effect_measure"])
    events = float(data["events"])
    total = float(data["total"])
    warnings = list(row.warnings)
    theta, variance, warnings = proportion_effect(events, total, measure=measure, warnings=warnings)
    return _make_effect(row, measure, theta, variance, warnings=warnings)


def correlation_study_effect(row: StudyAnalysisRow) -> StudyEffectEstimate:
    data = row.normalized_data
    measure = str(data["effect_measure"])
    r = float(data["r"])
    sample_size = float(data["sample_size"])
    theta, variance = fisher_z_effect(r, sample_size)
    return _make_effect(row, measure, theta, variance, warnings=list(row.warnings))


def diagnostic_accuracy_study_effect(row: StudyAnalysisRow) -> StudyEffectEstimate:
    data = row.normalized_data
    metrics = diagnostic_accuracy_metrics(
        tp=float(data["tp"]),
        fp=float(data["fp"]),
        fn=float(data["fn"]),
        tn=float(data["tn"]),
    )
    measure = str(data["effect_measure"])
    warnings = list(row.warnings)
    if measure == "SENSITIVITY":
        theta, variance, warnings = proportion_effect(float(data["tp"]), float(data["tp"]) + float(data["fn"]), measure=measure, warnings=warnings)
    elif measure == "SPECIFICITY":
        theta, variance, warnings = proportion_effect(float(data["tn"]), float(data["tn"]) + float(data["fp"]), measure=measure, warnings=warnings)
    elif measure in {"PLR", "NLR", "DOR"}:
        effect = getattr(metrics, measure.lower())
        if effect <= 0:
            raise ValueError(f"Diagnostic {measure} must be positive for record {row.record_id}.")
        theta = math.log(effect)
        variance = diagnostic_ratio_variance(
            tp=float(data["tp"]),
            fp=float(data["fp"]),
            fn=float(data["fn"]),
            tn=float(data["tn"]),
            measure=measure,
        )
    else:
        raise ValueError(f"Unsupported diagnostic effect measure: {measure}")
    return _make_effect(row, measure, theta, variance, warnings=warnings)


@dataclass(frozen=True)
class DiagnosticAccuracyMetrics:
    sensitivity: float
    specificity: float
    plr: float
    nlr: float
    dor: float


def proportion_effect(events: float, total: float, *, measure: str = "PREVALENCE", warnings: list[str] | None = None) -> tuple[float, float, list[str]]:
    warnings = list(warnings or [])
    if total <= 0:
        raise ValueError("Proportion total must be positive.")
    if events < 0 or events > total:
        raise ValueError("Proportion events must be between 0 and total.")
    non_events = total - events
    corrected_events = events
    corrected_non_events = non_events
    corrected_total = total
    if events == 0 or non_events == 0:
        corrected_events = events + 0.5
        corrected_non_events = non_events + 0.5
        corrected_total = total + 1.0
        warnings.append("single_arm_continuity_correction_applied")
    proportion = corrected_events / corrected_total
    normalized_measure = measure.upper()
    if normalized_measure in LOGIT_SCALE_EFFECT_MEASURES:
        theta = math.log(proportion / (1 - proportion))
        variance = (1 / corrected_events) + (1 / corrected_non_events)
        return theta, variance, warnings
    theta = events / total
    variance = theta * (1 - theta) / total
    if variance <= 0:
        variance = 1 / (total + 1)
        warnings.append("proportion_zero_variance_warning")
    return theta, variance, warnings


def fisher_z_transform(r: float) -> float:
    if not -1 < r < 1:
        raise ValueError("Correlation r must be between -1 and 1.")
    return 0.5 * math.log((1 + r) / (1 - r))


def fisher_z_back_transform(z_value: float) -> float:
    numerator = math.exp(2 * z_value) - 1
    denominator = math.exp(2 * z_value) + 1
    return numerator / denominator


def fisher_z_effect(r: float, sample_size: float) -> tuple[float, float]:
    if sample_size <= 3:
        raise ValueError("Correlation sample size must exceed 3.")
    return fisher_z_transform(r), 1 / (sample_size - 3)


def diagnostic_accuracy_metrics(*, tp: float, fp: float, fn: float, tn: float) -> DiagnosticAccuracyMetrics:
    if min(tp, fp, fn, tn) < 0:
        raise ValueError("Diagnostic counts cannot be negative.")
    sensitivity_denominator = tp + fn
    specificity_denominator = tn + fp
    if sensitivity_denominator <= 0 or specificity_denominator <= 0:
        raise ValueError("Diagnostic sensitivity and specificity denominators must be positive.")
    sensitivity = tp / sensitivity_denominator
    specificity = tn / specificity_denominator
    if specificity >= 1 or specificity <= 0 or sensitivity >= 1 or sensitivity <= 0:
        tp += 0.5
        fp += 0.5
        fn += 0.5
        tn += 0.5
        sensitivity = tp / (tp + fn)
        specificity = tn / (tn + fp)
    plr = sensitivity / (1 - specificity)
    nlr = (1 - sensitivity) / specificity
    dor = plr / nlr
    return DiagnosticAccuracyMetrics(sensitivity=sensitivity, specificity=specificity, plr=plr, nlr=nlr, dor=dor)


def diagnostic_ratio_variance(*, tp: float, fp: float, fn: float, tn: float, measure: str) -> float:
    if min(tp, fp, fn, tn) == 0:
        tp += 0.5
        fp += 0.5
        fn += 0.5
        tn += 0.5
    if measure == "DOR":
        return (1 / tp) + (1 / fp) + (1 / fn) + (1 / tn)
    if measure == "PLR":
        return (1 / tp) - (1 / (tp + fn)) + (1 / fp) - (1 / (fp + tn))
    if measure == "NLR":
        return (1 / fn) - (1 / (tp + fn)) + (1 / tn) - (1 / (fp + tn))
    raise ValueError(f"Unsupported diagnostic ratio measure: {measure}")


def ci_to_standard_error(ci_lower: float, ci_upper: float, *, log_scale: bool) -> float:
    if ci_lower > ci_upper:
        raise ValueError("CI lower cannot exceed CI upper.")
    if log_scale:
        if ci_lower <= 0 or ci_upper <= 0:
            raise ValueError("Log-scale CI bounds must be positive.")
        return (math.log(ci_upper) - math.log(ci_lower)) / (2 * 1.96)
    return (ci_upper - ci_lower) / (2 * 1.96)


def report_effect_values(effect_measure: str, theta: float, standard_error: float) -> tuple[float, float, float]:
    ci_low_theta = theta - (1.96 * standard_error)
    ci_high_theta = theta + (1.96 * standard_error)
    if effect_measure in LOG_SCALE_EFFECT_MEASURES:
        return math.exp(theta), math.exp(ci_low_theta), math.exp(ci_high_theta)
    if effect_measure in LOGIT_SCALE_EFFECT_MEASURES:
        return _inverse_logit(theta), _inverse_logit(ci_low_theta), _inverse_logit(ci_high_theta)
    if effect_measure in CORRELATION_EFFECT_MEASURES:
        return fisher_z_back_transform(theta), fisher_z_back_transform(ci_low_theta), fisher_z_back_transform(ci_high_theta)
    return theta, ci_low_theta, ci_high_theta


def _make_effect(
    row: StudyAnalysisRow,
    effect_measure: str,
    theta: float,
    variance: float,
    *,
    warnings: list[str],
) -> StudyEffectEstimate:
    if variance <= 0:
        raise ValueError(f"Study effect produced non-positive variance for record {row.record_id}.")
    standard_error = math.sqrt(variance)
    effect, ci_lower, ci_upper = report_effect_values(effect_measure, theta, standard_error)
    return StudyEffectEstimate(
        study_id=row.study_id,
        record_id=row.record_id,
        first_author=row.first_author,
        year=row.year,
        effect_measure=effect_measure,
        effect=effect,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        standard_error=standard_error,
        variance=variance,
        transformed_effect=theta,
        warnings=warnings,
    )


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _inverse_logit(value: float) -> float:
    return 1 / (1 + math.exp(-value))
