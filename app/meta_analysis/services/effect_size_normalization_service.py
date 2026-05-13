from __future__ import annotations

import math
from typing import Any

from app.meta_analysis.models.effect_size_normalization import (
    EFFECT_MEASURE_OTHER,
    EFFECT_SIZE_CONTINUOUS_MEASURES,
    EFFECT_SIZE_NORMALIZATION_STATUSES,
    EFFECT_SIZE_RATIO_MEASURES,
    EFFECT_SIZE_SUPPORTED_MEASURES,
    NORMALIZATION_STATUS_INCOMPLETE,
    NORMALIZATION_STATUS_INVALID_CI,
    NORMALIZATION_STATUS_INVALID_NUMERIC,
    NORMALIZATION_STATUS_NEEDS_USER_REVIEW,
    NORMALIZATION_STATUS_READY,
    NORMALIZATION_STATUS_UNSUPPORTED_EFFECT_TYPE,
    EffectSizeNormalizationSummary,
    NormalizedEffectSizeInput,
)
from app.meta_analysis.services.manual_extraction_effect_row_service import ManualExtractionEffectRowService


class EffectSizeNormalizationService:
    def __init__(self, *, manual_extraction: ManualExtractionEffectRowService | None = None) -> None:
        self._manual_extraction = manual_extraction or ManualExtractionEffectRowService()

    def normalize_extraction_rows(self, project_dir: Any) -> list[NormalizedEffectSizeInput]:
        rows = self._manual_extraction.load_effect_rows(project_dir)
        return [self.normalize_single_effect(row) for row in rows]

    def normalize_single_effect(self, row: dict[str, Any]) -> NormalizedEffectSizeInput:
        fields = _row_fields(row)
        source_state = _source_state(row)
        measure = _normalize_measure(fields.get("effect_measure_type") or fields.get("effect_measure") or _reported(row).get("effect_measure"))
        base = {
            "study_ref": _safe_study_ref(fields, row),
            "study_label": _safe_study_label(fields, row),
            "effect_measure_type": measure,
            "estimate": _number(_first_available(fields.get("effect_estimate"), _reported(row).get("effect_value"))),
            "ci_lower": _number(_first_available(fields.get("ci_lower"), _reported(row).get("ci_low"))),
            "ci_upper": _number(_first_available(fields.get("ci_upper"), _reported(row).get("ci_high"))),
            "standard_error": _number(fields.get("standard_error")),
            "events_case": _number(_first_available(fields.get("events_case"), _raw(row).get("group_1_events"))),
            "total_case": _number(_first_available(fields.get("total_case"), _raw(row).get("group_1_n"))),
            "events_control": _number(_first_available(fields.get("events_control"), _raw(row).get("group_2_events"))),
            "total_control": _number(_first_available(fields.get("total_control"), _raw(row).get("group_2_n"))),
            "mean_case": _number(_first_available(fields.get("mean_case"), _raw(row).get("group_1_mean"))),
            "sd_case": _number(_first_available(fields.get("sd_case"), _raw(row).get("group_1_sd"))),
            "n_case": _number(_first_available(fields.get("n_case"), fields.get("sample_size_case"), _raw(row).get("group_1_n"))),
            "mean_control": _number(_first_available(fields.get("mean_control"), _raw(row).get("group_2_mean"))),
            "sd_control": _number(_first_available(fields.get("sd_control"), _raw(row).get("group_2_sd"))),
            "n_control": _number(_first_available(fields.get("n_control"), fields.get("sample_size_control"), _raw(row).get("group_2_n"))),
            "correlation_coefficient": _number(_first_available(fields.get("correlation_coefficient"), _raw(row).get("r"))),
            "diagnostic_tp": _number(_first_available(fields.get("diagnostic_tp"), _raw(row).get("tp"))),
            "diagnostic_fp": _number(_first_available(fields.get("diagnostic_fp"), _raw(row).get("fp"))),
            "diagnostic_fn": _number(_first_available(fields.get("diagnostic_fn"), _raw(row).get("fn"))),
            "diagnostic_tn": _number(_first_available(fields.get("diagnostic_tn"), _raw(row).get("tn"))),
            "source_state": source_state,
        }
        numeric_warnings = _numeric_warnings(fields, row)
        warnings = _dedupe([*_source_warnings(row), *numeric_warnings])
        if not _is_confirmed_source(row):
            return NormalizedEffectSizeInput(
                **base,
                normalization_status=NORMALIZATION_STATUS_NEEDS_USER_REVIEW,
                warnings=_dedupe([*warnings, "source_row_not_confirmed"]),
                source_field_completeness=_field_completeness(base),
            )
        if measure not in EFFECT_SIZE_SUPPORTED_MEASURES:
            return NormalizedEffectSizeInput(
                **base,
                normalization_status=NORMALIZATION_STATUS_UNSUPPORTED_EFFECT_TYPE,
                warnings=_dedupe([*warnings, "unsupported_effect_measure_type"]),
                source_field_completeness=_field_completeness(base),
            )
        numeric_status = NORMALIZATION_STATUS_INVALID_NUMERIC if numeric_warnings else _invalid_numeric_status(base)
        if numeric_status:
            return NormalizedEffectSizeInput(
                **base,
                normalization_status=numeric_status,
                warnings=_dedupe([*warnings, numeric_status]),
                source_field_completeness=_field_completeness(base),
            )
        normalized = self.validate_effect_input(NormalizedEffectSizeInput(**base, warnings=warnings, source_field_completeness=_field_completeness(base)))
        return normalized

    def validate_effect_input(self, effect: NormalizedEffectSizeInput) -> NormalizedEffectSizeInput:
        warnings = list(effect.warnings)
        status = effect.normalization_status
        standard_error = effect.standard_error
        variance = effect.variance
        log_estimate = effect.log_estimate
        log_ci_lower = effect.log_ci_lower
        log_ci_upper = effect.log_ci_upper
        if effect.effect_measure_type == EFFECT_MEASURE_OTHER:
            return _replace(effect, normalization_status=NORMALIZATION_STATUS_INCOMPLETE, warnings=_dedupe([*warnings, "other_effect_type_requires_user_mapping"]))
        if effect.ci_lower is not None and effect.ci_upper is not None and effect.ci_lower > effect.ci_upper:
            return _replace(effect, normalization_status=NORMALIZATION_STATUS_INVALID_CI, warnings=_dedupe([*warnings, "ci_lower_exceeds_ci_upper"]))
        if effect.effect_measure_type in EFFECT_SIZE_RATIO_MEASURES:
            if effect.estimate is None or effect.ci_lower is None or effect.ci_upper is None:
                return _replace(effect, normalization_status=NORMALIZATION_STATUS_INCOMPLETE, warnings=_dedupe([*warnings, "ratio_measure_requires_estimate_and_ci"]))
            if effect.estimate <= 0 or effect.ci_lower <= 0 or effect.ci_upper <= 0:
                return _replace(effect, normalization_status=NORMALIZATION_STATUS_INVALID_NUMERIC, warnings=_dedupe([*warnings, "ratio_measure_requires_positive_estimate_and_ci"]))
            log_estimate = math.log(effect.estimate)
            log_ci_lower = math.log(effect.ci_lower)
            log_ci_upper = math.log(effect.ci_upper)
            standard_error = standard_error if standard_error is not None else (log_ci_upper - log_ci_lower) / 3.92
            variance = standard_error**2 if standard_error is not None else None
            status = NORMALIZATION_STATUS_READY
        elif effect.effect_measure_type in EFFECT_SIZE_CONTINUOUS_MEASURES:
            if effect.estimate is None or effect.ci_lower is None or effect.ci_upper is None:
                return _replace(effect, normalization_status=NORMALIZATION_STATUS_INCOMPLETE, warnings=_dedupe([*warnings, "continuous_measure_requires_estimate_and_ci"]))
            standard_error = standard_error if standard_error is not None else (effect.ci_upper - effect.ci_lower) / 3.92
            variance = standard_error**2 if standard_error is not None else None
            status = NORMALIZATION_STATUS_READY
        elif effect.effect_measure_type in {"proportion", "correlation", "diagnostic_accuracy"}:
            return _replace(effect, normalization_status=NORMALIZATION_STATUS_INCOMPLETE, warnings=_dedupe([*warnings, f"{effect.effect_measure_type}_normalization_requires_future_executor_mapping"]))
        else:
            return _replace(effect, normalization_status=NORMALIZATION_STATUS_UNSUPPORTED_EFFECT_TYPE, warnings=_dedupe([*warnings, "unsupported_effect_measure_type"]))
        if standard_error is None or variance is None or standard_error < 0 or variance < 0:
            return _replace(effect, normalization_status=NORMALIZATION_STATUS_INVALID_NUMERIC, warnings=_dedupe([*warnings, "standard_error_or_variance_invalid"]))
        return _replace(
            effect,
            standard_error=standard_error,
            variance=variance,
            log_estimate=log_estimate,
            log_ci_lower=log_ci_lower,
            log_ci_upper=log_ci_upper,
            normalization_status=status,
            warnings=_dedupe(warnings),
        )

    def summarize_normalization(self, effects: list[NormalizedEffectSizeInput]) -> EffectSizeNormalizationSummary:
        warnings = _dedupe([warning for effect in effects for warning in effect.warnings])
        return EffectSizeNormalizationSummary(
            total_rows=len(effects),
            confirmed_rows=sum(1 for effect in effects if effect.source_state == "confirmed"),
            normalized_ready=sum(1 for effect in effects if effect.normalization_status == NORMALIZATION_STATUS_READY),
            incomplete=sum(1 for effect in effects if effect.normalization_status == NORMALIZATION_STATUS_INCOMPLETE),
            invalid=sum(1 for effect in effects if effect.normalization_status in {NORMALIZATION_STATUS_INVALID_NUMERIC, NORMALIZATION_STATUS_INVALID_CI}),
            needs_user_review=sum(1 for effect in effects if effect.normalization_status == NORMALIZATION_STATUS_NEEDS_USER_REVIEW),
            unsupported_effect_type=sum(1 for effect in effects if effect.normalization_status == NORMALIZATION_STATUS_UNSUPPORTED_EFFECT_TYPE),
            warnings=warnings,
        )


def _row_fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = dict(row.get("m5_structured_fields", {}) if isinstance(row.get("m5_structured_fields"), dict) else {})
    reported = _reported(row)
    if not fields and reported:
        fields = {
            "effect_measure_type": reported.get("effect_measure", ""),
            "effect_estimate": reported.get("effect_value", ""),
            "ci_lower": reported.get("ci_low", ""),
            "ci_upper": reported.get("ci_high", ""),
            "outcome": row.get("outcome_name", ""),
        }
    return fields


def _reported(row: dict[str, Any]) -> dict[str, Any]:
    return dict(row.get("reported_effect_size", {}) if isinstance(row.get("reported_effect_size"), dict) else {})


def _raw(row: dict[str, Any]) -> dict[str, Any]:
    return dict(row.get("raw_group_data", {}) if isinstance(row.get("raw_group_data"), dict) else {})


def _source_state(row: dict[str, Any]) -> str:
    if str(row.get("evidence_state", "")).strip():
        return str(row.get("evidence_state", "")).strip()
    if str(row.get("extraction_status", "")) == "completed_by_user":
        return "confirmed"
    return str(row.get("extraction_status", "") or "draft")


def _is_confirmed_source(row: dict[str, Any]) -> bool:
    return str(row.get("evidence_state", "")) == "confirmed" or str(row.get("extraction_status", "")) == "completed_by_user"


def _normalize_measure(value: Any) -> str:
    text = str(value or "").strip()
    upper = text.upper()
    if upper in {"OR", "RR", "HR", "MD", "SMD"}:
        return upper
    lower = text.lower()
    aliases = {
        "proportion": "proportion",
        "prevalence": "proportion",
        "incidence": "proportion",
        "correlation": "correlation",
        "pearson_r": "correlation",
        "spearman_r": "correlation",
        "diagnostic_accuracy": "diagnostic_accuracy",
        "diagnostic": "diagnostic_accuracy",
        "other": "other",
    }
    return aliases.get(lower, text)


def _safe_study_ref(fields: dict[str, Any], row: dict[str, Any]) -> str:
    return str(fields.get("study_id") or fields.get("first_author") or row.get("study_unit_label") or fields.get("title") or "study").strip()


def _safe_study_label(fields: dict[str, Any], row: dict[str, Any]) -> str:
    author = str(fields.get("first_author") or row.get("study_unit_label") or fields.get("study_id") or "Study").strip()
    year = str(fields.get("year") or "").strip()
    return f"{author} {year}".strip()


def _number(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_available(*values: Any) -> Any:
    for value in values:
        if value not in ("", None):
            return value
    return None


def _numeric_warnings(fields: dict[str, Any], row: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for name, value in {**fields, **_reported(row), **_raw(row)}.items():
        if value in ("", None):
            continue
        if name in {
            "effect_estimate",
            "effect_value",
            "ci_lower",
            "ci_upper",
            "ci_low",
            "ci_high",
            "standard_error",
            "events_case",
            "total_case",
            "events_control",
            "total_control",
            "sample_size_total",
            "sample_size_case",
            "sample_size_control",
            "group_1_n",
            "group_1_events",
            "group_2_n",
            "group_2_events",
            "mean_case",
            "sd_case",
            "mean_control",
            "sd_control",
            "correlation_coefficient",
            "diagnostic_tp",
            "diagnostic_fp",
            "diagnostic_fn",
            "diagnostic_tn",
            "tp",
            "fp",
            "fn",
            "tn",
        } and _number(value) is None:
            warnings.append(f"invalid_numeric_field:{name}")
    return warnings


def _invalid_numeric_status(values: dict[str, Any]) -> str:
    non_negative = (
        "events_case",
        "total_case",
        "events_control",
        "total_control",
        "n_case",
        "n_control",
        "diagnostic_tp",
        "diagnostic_fp",
        "diagnostic_fn",
        "diagnostic_tn",
    )
    if any(values.get(field) is not None and float(values[field]) < 0 for field in non_negative):
        return NORMALIZATION_STATUS_INVALID_NUMERIC
    if values.get("ci_lower") is not None and values.get("ci_upper") is not None and float(values["ci_lower"]) > float(values["ci_upper"]):
        return NORMALIZATION_STATUS_INVALID_CI
    return ""


def _source_warnings(row: dict[str, Any]) -> list[str]:
    warnings = list(row.get("warnings", [])) if isinstance(row.get("warnings"), list) else []
    diagnostics = list(row.get("diagnostics", [])) if isinstance(row.get("diagnostics"), list) else []
    return [str(item) for item in [*warnings, *diagnostics] if str(item)]


def _field_completeness(values: dict[str, Any]) -> dict[str, bool]:
    return {
        "study_label": bool(values.get("study_label")),
        "effect_measure_type": bool(values.get("effect_measure_type")),
        "estimate": values.get("estimate") is not None,
        "ci_lower": values.get("ci_lower") is not None,
        "ci_upper": values.get("ci_upper") is not None,
        "standard_error": values.get("standard_error") is not None,
    }


def _replace(effect: NormalizedEffectSizeInput, **updates: Any) -> NormalizedEffectSizeInput:
    payload = effect.to_dict()
    payload.update(updates)
    status = str(payload.get("normalization_status", ""))
    if status not in EFFECT_SIZE_NORMALIZATION_STATUSES:
        payload["normalization_status"] = NORMALIZATION_STATUS_INCOMPLETE
    return NormalizedEffectSizeInput(**payload)


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
