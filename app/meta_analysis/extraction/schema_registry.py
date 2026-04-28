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
    description: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


TREATMENT_EFFECT_META = "TREATMENT_EFFECT_META"
BIOMARKER_PREVALENCE_ASSOCIATION_META = "BIOMARKER_PREVALENCE_ASSOCIATION_META"
PROGNOSTIC_FACTOR_META = "PROGNOSTIC_FACTOR_META"


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
    ),
    BIOMARKER_PREVALENCE_ASSOCIATION_META: ExtractionSchemaProfile(
        profile_type=BIOMARKER_PREVALENCE_ASSOCIATION_META,
        description="Biomarker prevalence or biomarker-disease association meta-analysis.",
        allowed_outcome_data_types=(OutcomeDataType.BINARY.value, OutcomeDataType.GENERIC_EFFECT.value),
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
        },
        validation_rules=COMMON_VALIDATION_RULES
        + ("events_cannot_exceed_total", "total_must_be_positive", "ci_lower_cannot_exceed_ci_upper"),
        recommended_quality_tools=("NOS", "JBI checklist placeholder", "GRADE placeholder"),
        downstream_analysis_hint="Build association or prevalence-ready extraction datasets before analysis.",
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
    ),
}


def list_extraction_schema_profiles() -> list[ExtractionSchemaProfile]:
    return list(EXTRACTION_SCHEMA_REGISTRY.values())


def get_extraction_schema_profile(profile_type: str) -> ExtractionSchemaProfile | None:
    return EXTRACTION_SCHEMA_REGISTRY.get(profile_type)
