from __future__ import annotations

from dataclasses import dataclass, field

from app.meta_analysis.models.analysis_dataset import AnalysisReadyDataset, StudyAnalysisRow
from app.meta_analysis.models.analysis_result import AnalysisResult


@dataclass(frozen=True)
class ApplicabilityResult:
    method: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def can_run(self) -> bool:
        return not self.errors


class StatisticalApplicabilityService:
    def evaluate_dataset_for_meta_analysis(self, dataset: AnalysisReadyDataset, model: str) -> ApplicabilityResult:
        warnings = list(dataset.validation_warnings)
        errors = list(dataset.validation_errors)
        rows = [row for row in dataset.study_rows if row.analysis_status == "included"]
        method = f"{dataset.effect_measure}:{model}"
        if dataset.profile_type == "NETWORK_META_ANALYSIS":
            errors.append("network_meta_analysis_not_implemented")
        if model.strip().lower() == "random" and len(rows) < 3:
            warnings.append("random_effects_tau_squared_unstable_with_fewer_than_three_studies")
        if dataset.effect_measure == "SMD":
            for row in rows:
                sd_values = (row.normalized_data.get("experimental_sd"), row.normalized_data.get("control_sd"))
                if any(value in (None, "") for value in sd_values):
                    errors.append(f"smd_sd_missing:{row.record_id}")
                elif any(float(value) <= 0 for value in sd_values):
                    errors.append(f"smd_sd_must_be_positive:{row.record_id}")
        if dataset.effect_measure in {"OR", "RR"}:
            warnings.append("or_rr_zero_event_continuity_correction_will_be_reported_when_applied")
        if dataset.effect_measure == "HR":
            warnings.append("hr_generic_inverse_variance_uses_log_scale_and_ci_to_se_when_needed")
        if dataset.effect_measure in {"PREVALENCE", "INCIDENCE", "PROPORTION", "SINGLE_ARM"}:
            warnings.append("single_arm_proportion_uses_logit_transformation_when configured as prevalence/proportion")
        if dataset.outcome_data_type == "diagnostic_accuracy":
            warnings.append("diagnostic_basic_not_bivariate_or_hsroc")
        return ApplicabilityResult(method=method, warnings=_dedupe(warnings), errors=_dedupe(errors))

    def evaluate_analysis_result(self, result: AnalysisResult) -> ApplicabilityResult:
        warnings = list(result.warnings)
        if len(result.study_results) < 10:
            warnings.append("funnel_plot_and_publication_bias_tests_unreliable_with_fewer_than_ten_studies")
        if result.effect_measure in {"OR", "RR", "HR", "PLR", "NLR", "DOR"}:
            warnings.append("ratio_effects_are_analyzed_on_log_scale")
        return ApplicabilityResult(method=result.effect_measure, warnings=_dedupe(warnings), errors=[])

    def evaluate_advanced_method(self, method: str, study_count: int) -> ApplicabilityResult:
        warnings: list[str] = []
        errors: list[str] = []
        normalized = method.lower()
        if normalized in {"egger", "publication_bias", "funnel_plot"} and study_count < 10:
            warnings.append("publication_bias_and_funnel_plot_unreliable_with_fewer_than_ten_studies")
        if normalized == "network_meta":
            errors.append("network_meta_analysis_not_implemented")
        return ApplicabilityResult(method=method, warnings=warnings, errors=errors)


def applicability_warnings_for_row(row: StudyAnalysisRow) -> list[str]:
    warnings = []
    if row.effect_measure in {"OR", "RR"} and "zero_event_correction_applied" in row.warnings:
        warnings.append(f"zero_event_correction_applied:{row.record_id}")
    if row.effect_measure == "HR":
        warnings.append(f"hr_log_scale_ci_to_se_review_required:{row.record_id}")
    return warnings


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result

