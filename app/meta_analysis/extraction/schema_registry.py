from __future__ import annotations

from dataclasses import dataclass, field

from app.meta_analysis.models.extraction import OutcomeDataType


@dataclass(frozen=True)
class ExtractionSchemaProfile:
    profile_type: str
    allowed_outcome_data_types: tuple[str, ...]
    supported_effect_measures: tuple[str, ...]
    required_study_fields: tuple[str, ...]
    required_outcome_fields: dict[str, tuple[str, ...]]
    validation_rules: tuple[str, ...]
    recommended_quality_tools: tuple[str, ...]
    downstream_analysis_hint: str
    recommended_figures: tuple[str, ...] = ()
    report_sections: tuple[str, ...] = ()
    description: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


TREATMENT_EFFECT_META = "TREATMENT_EFFECT_META"
BIOMARKER_PREVALENCE_ASSOCIATION_META = "BIOMARKER_PREVALENCE_ASSOCIATION_META"
PROGNOSTIC_FACTOR_META = "PROGNOSTIC_FACTOR_META"
DIAGNOSTIC_ACCURACY_META = "DIAGNOSTIC_ACCURACY_META"
PREVALENCE_INCIDENCE_META = "PREVALENCE_INCIDENCE_META"
CORRELATION_META = "CORRELATION_META"
SINGLE_ARM_OUTCOME_META = "SINGLE_ARM_OUTCOME_META"
CONTINUOUS_BIOMARKER_DIFFERENCE_META = "CONTINUOUS_BIOMARKER_DIFFERENCE_META"
EXPOSURE_DISEASE_RISK_META = "EXPOSURE_DISEASE_RISK_META"
NETWORK_META_ANALYSIS = "NETWORK_META_ANALYSIS"


COMMON_STUDY_FIELDS = (
    "first_author",
    "year",
    "population",
    "sample_size",
)

COMMON_VALIDATION_RULES = (
    "sample_size_must_be_positive",
    "outcome_name_required",
    "effect_measure_must_be_supported_by_profile",
)


EXTRACTION_SCHEMA_REGISTRY: dict[str, ExtractionSchemaProfile] = {
    TREATMENT_EFFECT_META: ExtractionSchemaProfile(
        profile_type=TREATMENT_EFFECT_META,
        description="Treatment or exposure comparative effect meta-analysis.",
        allowed_outcome_data_types=(
            OutcomeDataType.BINARY.value,
            OutcomeDataType.CONTINUOUS.value,
            OutcomeDataType.GENERIC_EFFECT.value,
        ),
        supported_effect_measures=("OR", "RR", "RD", "MD", "SMD", "HR"),
        required_study_fields=COMMON_STUDY_FIELDS,
        required_outcome_fields={
            OutcomeDataType.BINARY.value: (
                "outcome_name",
                "effect_measure",
                "experimental_events",
                "experimental_total",
                "control_events",
                "control_total",
            ),
            OutcomeDataType.CONTINUOUS.value: (
                "outcome_name",
                "effect_measure",
                "experimental_mean",
                "experimental_sd",
                "experimental_total",
                "control_mean",
                "control_sd",
                "control_total",
            ),
            OutcomeDataType.GENERIC_EFFECT.value: ("outcome_name", "effect_measure", "effect"),
        },
        validation_rules=COMMON_VALIDATION_RULES
        + (
            "events_cannot_exceed_total",
            "total_must_be_positive",
            "sd_cannot_be_negative",
            "ci_lower_cannot_exceed_ci_upper",
            "ratio_effect_must_be_positive",
        ),
        recommended_quality_tools=("RoB2 simplified", "JBI checklist placeholder", "GRADE placeholder"),
        downstream_analysis_hint="Build comparative binary, continuous, or generic inverse-variance datasets.",
        recommended_figures=("forest_plot", "result_table"),
        report_sections=("study_characteristics", "effect_summary", "heterogeneity"),
    ),
    BIOMARKER_PREVALENCE_ASSOCIATION_META: ExtractionSchemaProfile(
        profile_type=BIOMARKER_PREVALENCE_ASSOCIATION_META,
        description="Biomarker prevalence or biomarker-disease association meta-analysis.",
        allowed_outcome_data_types=(
            OutcomeDataType.BINARY.value,
            OutcomeDataType.GENERIC_EFFECT.value,
            OutcomeDataType.PROPORTION.value,
            OutcomeDataType.CORRELATION.value,
        ),
        supported_effect_measures=("OR", "RR", "PREVALENCE", "CORRELATION"),
        required_study_fields=COMMON_STUDY_FIELDS,
        required_outcome_fields={
            OutcomeDataType.BINARY.value: (
                "outcome_name",
                "effect_measure",
                "experimental_events",
                "experimental_total",
                "control_events",
                "control_total",
            ),
            OutcomeDataType.GENERIC_EFFECT.value: ("outcome_name", "effect_measure", "effect"),
            OutcomeDataType.PROPORTION.value: ("outcome_name", "events", "total"),
            OutcomeDataType.CORRELATION.value: ("outcome_name", "r", "sample_size"),
        },
        validation_rules=COMMON_VALIDATION_RULES
        + (
            "events_cannot_exceed_total",
            "total_must_be_positive",
            "correlation_must_be_between_minus_one_and_one",
            "ci_lower_cannot_exceed_ci_upper",
        ),
        recommended_quality_tools=("NOS", "JBI checklist placeholder", "GRADE placeholder"),
        downstream_analysis_hint="Build association or prevalence-ready extraction datasets before analysis.",
        recommended_figures=("forest_plot", "result_table"),
        report_sections=("biomarker_definition", "prevalence_or_association_summary"),
    ),
    PROGNOSTIC_FACTOR_META: ExtractionSchemaProfile(
        profile_type=PROGNOSTIC_FACTOR_META,
        description="Prognostic factor meta-analysis with reported hazard or risk effects.",
        allowed_outcome_data_types=(OutcomeDataType.GENERIC_EFFECT.value,),
        supported_effect_measures=("HR", "OR", "RR"),
        required_study_fields=COMMON_STUDY_FIELDS,
        required_outcome_fields={
            OutcomeDataType.GENERIC_EFFECT.value: ("outcome_name", "effect_measure", "effect"),
        },
        validation_rules=COMMON_VALIDATION_RULES
        + ("ci_lower_cannot_exceed_ci_upper", "ratio_effect_must_be_positive"),
        recommended_quality_tools=("NOS", "QUADAS-2", "GRADE placeholder"),
        downstream_analysis_hint="Build generic inverse-variance datasets for reported prognostic effects.",
        recommended_figures=("forest_plot", "result_table"),
        report_sections=("prognostic_factor_definition", "adjustment_summary", "effect_summary"),
    ),
    DIAGNOSTIC_ACCURACY_META: ExtractionSchemaProfile(
        profile_type=DIAGNOSTIC_ACCURACY_META,
        description="Diagnostic test accuracy meta-analysis using 2x2 TP/FP/FN/TN data.",
        allowed_outcome_data_types=(OutcomeDataType.DIAGNOSTIC_ACCURACY.value,),
        supported_effect_measures=("SENSITIVITY", "SPECIFICITY", "PLR", "NLR", "DOR"),
        required_study_fields=COMMON_STUDY_FIELDS,
        required_outcome_fields={
            OutcomeDataType.DIAGNOSTIC_ACCURACY.value: ("outcome_name", "tp", "fp", "fn", "tn"),
        },
        validation_rules=COMMON_VALIDATION_RULES
        + (
            "diagnostic_counts_cannot_be_negative",
            "sensitivity_denominator_must_be_positive",
            "specificity_denominator_must_be_positive",
        ),
        recommended_quality_tools=("QUADAS-2", "GRADE placeholder"),
        downstream_analysis_hint="Build diagnostic basic result rows; bivariate model and HSROC are not implemented.",
        recommended_figures=("diagnostic_result_table",),
        report_sections=("index_test", "reference_standard", "diagnostic_basic_summary"),
        metadata={"advanced_model_status": "bivariate_and_hsroc_not_implemented"},
    ),
    PREVALENCE_INCIDENCE_META: ExtractionSchemaProfile(
        profile_type=PREVALENCE_INCIDENCE_META,
        description="Prevalence or incidence meta-analysis using single-arm event counts.",
        allowed_outcome_data_types=(OutcomeDataType.PROPORTION.value,),
        supported_effect_measures=("PREVALENCE", "INCIDENCE", "PROPORTION"),
        required_study_fields=COMMON_STUDY_FIELDS,
        required_outcome_fields={
            OutcomeDataType.PROPORTION.value: ("outcome_name", "events", "total"),
        },
        validation_rules=COMMON_VALIDATION_RULES + ("events_cannot_exceed_total", "total_must_be_positive"),
        recommended_quality_tools=("JBI checklist placeholder", "GRADE placeholder"),
        downstream_analysis_hint="Build logit proportion datasets for fixed/random pooling.",
        recommended_figures=("forest_plot", "result_table"),
        report_sections=("case_definition", "population_source", "prevalence_summary"),
    ),
    CORRELATION_META: ExtractionSchemaProfile(
        profile_type=CORRELATION_META,
        description="Correlation meta-analysis using r and sample size.",
        allowed_outcome_data_types=(OutcomeDataType.CORRELATION.value,),
        supported_effect_measures=("CORRELATION", "PEARSON_R", "SPEARMAN_R"),
        required_study_fields=COMMON_STUDY_FIELDS,
        required_outcome_fields={
            OutcomeDataType.CORRELATION.value: ("outcome_name", "r", "sample_size"),
        },
        validation_rules=COMMON_VALIDATION_RULES + ("correlation_must_be_between_minus_one_and_one", "sample_size_must_exceed_three"),
        recommended_quality_tools=("NOS", "JBI checklist placeholder"),
        downstream_analysis_hint="Build Fisher z transformed correlation datasets for pooling.",
        recommended_figures=("forest_plot", "result_table"),
        report_sections=("variable_definitions", "correlation_summary"),
    ),
    SINGLE_ARM_OUTCOME_META: ExtractionSchemaProfile(
        profile_type=SINGLE_ARM_OUTCOME_META,
        description="Single-arm outcome meta-analysis using event counts.",
        allowed_outcome_data_types=(OutcomeDataType.PROPORTION.value,),
        supported_effect_measures=("SINGLE_ARM", "PROPORTION"),
        required_study_fields=COMMON_STUDY_FIELDS,
        required_outcome_fields={
            OutcomeDataType.PROPORTION.value: ("outcome_name", "events", "total"),
        },
        validation_rules=COMMON_VALIDATION_RULES + ("events_cannot_exceed_total", "total_must_be_positive"),
        recommended_quality_tools=("JBI checklist placeholder", "GRADE placeholder"),
        downstream_analysis_hint="Build single-arm logit proportion datasets.",
        recommended_figures=("forest_plot", "result_table"),
        report_sections=("population_source", "single_arm_summary"),
    ),
    CONTINUOUS_BIOMARKER_DIFFERENCE_META: ExtractionSchemaProfile(
        profile_type=CONTINUOUS_BIOMARKER_DIFFERENCE_META,
        description="Continuous biomarker difference meta-analysis.",
        allowed_outcome_data_types=(OutcomeDataType.CONTINUOUS.value,),
        supported_effect_measures=("MD", "SMD"),
        required_study_fields=COMMON_STUDY_FIELDS,
        required_outcome_fields={
            OutcomeDataType.CONTINUOUS.value: (
                "outcome_name",
                "effect_measure",
                "experimental_mean",
                "experimental_sd",
                "experimental_total",
                "control_mean",
                "control_sd",
                "control_total",
            ),
        },
        validation_rules=COMMON_VALIDATION_RULES + ("sd_cannot_be_negative", "total_must_be_positive"),
        recommended_quality_tools=("NOS", "JBI checklist placeholder"),
        downstream_analysis_hint="Build MD/SMD analysis-ready datasets for biomarker differences.",
        recommended_figures=("forest_plot", "result_table"),
        report_sections=("biomarker_definition", "group_difference_summary"),
    ),
    EXPOSURE_DISEASE_RISK_META: ExtractionSchemaProfile(
        profile_type=EXPOSURE_DISEASE_RISK_META,
        description="Exposure-disease risk meta-analysis using 2x2 or reported association effects.",
        allowed_outcome_data_types=(OutcomeDataType.BINARY.value, OutcomeDataType.GENERIC_EFFECT.value),
        supported_effect_measures=("OR", "RR", "HR"),
        required_study_fields=COMMON_STUDY_FIELDS,
        required_outcome_fields={
            OutcomeDataType.BINARY.value: (
                "outcome_name",
                "effect_measure",
                "experimental_events",
                "experimental_total",
                "control_events",
                "control_total",
            ),
            OutcomeDataType.GENERIC_EFFECT.value: ("outcome_name", "effect_measure", "effect"),
        },
        validation_rules=COMMON_VALIDATION_RULES
        + ("events_cannot_exceed_total", "total_must_be_positive", "ratio_effect_must_be_positive"),
        recommended_quality_tools=("NOS", "GRADE placeholder"),
        downstream_analysis_hint="Build association effect datasets for exposure-disease risk.",
        recommended_figures=("forest_plot", "result_table"),
        report_sections=("exposure_definition", "risk_summary"),
    ),
    NETWORK_META_ANALYSIS: ExtractionSchemaProfile(
        profile_type=NETWORK_META_ANALYSIS,
        description="Network meta-analysis placeholder. Data structures only; statistical models are not implemented.",
        allowed_outcome_data_types=(),
        supported_effect_measures=(),
        required_study_fields=COMMON_STUDY_FIELDS,
        required_outcome_fields={},
        validation_rules=("network_meta_analysis_not_implemented",),
        recommended_quality_tools=("RoB2 simplified", "GRADE placeholder"),
        downstream_analysis_hint="Not implemented in current testing version.",
        recommended_figures=(),
        report_sections=("not_implemented_method_note",),
        metadata={"status": "not_implemented"},
    ),
}


def list_extraction_schema_profiles() -> list[ExtractionSchemaProfile]:
    return list(EXTRACTION_SCHEMA_REGISTRY.values())


def get_extraction_schema_profile(profile_type: str) -> ExtractionSchemaProfile | None:
    return EXTRACTION_SCHEMA_REGISTRY.get(profile_type)
