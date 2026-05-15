from __future__ import annotations

from app.meta_analysis.models.systematic_review import QualityToolDefinition


QUALITY_TOOL_REGISTRY: dict[str, QualityToolDefinition] = {
    "ROB2": QualityToolDefinition(
        tool_name="ROB2",
        domains=("randomization", "deviations_from_intended_interventions", "missing_outcome_data", "outcome_measurement", "selection_of_reported_result"),
        judgement_options=("low", "some_concerns", "high", "unclear", "not_applicable"),
        recommended_profiles=("TREATMENT_EFFECT_META", "binary_outcome_meta", "continuous_outcome_meta"),
        output_summary_fields=("overall_rating", "randomization", "deviations_from_intended_interventions", "missing_outcome_data"),
    ),
    "ROBINS-I": QualityToolDefinition(
        tool_name="ROBINS-I",
        domains=("confounding", "selection", "classification_of_interventions", "deviations", "missing_data", "outcome_measurement", "reported_result"),
        judgement_options=("low", "some_concerns", "high", "unclear", "not_applicable"),
        recommended_profiles=("EXPOSURE_DISEASE_RISK_META", "PROGNOSTIC_FACTOR_META", "exposure_disease_risk_meta", "prognostic_factor_meta"),
        output_summary_fields=("overall_rating", "confounding", "selection", "outcome_measurement"),
    ),
    "Newcastle-Ottawa Scale": QualityToolDefinition(
        tool_name="Newcastle-Ottawa Scale",
        domains=("selection", "comparability", "outcome_or_exposure"),
        judgement_options=("low", "some_concerns", "high", "unclear", "not_applicable"),
        recommended_profiles=("BIOMARKER_PREVALENCE_ASSOCIATION_META", "PROGNOSTIC_FACTOR_META", "EXPOSURE_DISEASE_RISK_META", "prognostic_factor_meta", "exposure_disease_risk_meta"),
        output_summary_fields=("overall_rating", "selection", "comparability", "outcome_or_exposure"),
    ),
    "NOS": QualityToolDefinition(
        tool_name="NOS",
        domains=("selection", "comparability", "outcome_or_exposure"),
        judgement_options=("low_risk_or_good", "unclear", "high_risk_or_poor", "not_assessed"),
        recommended_profiles=("BIOMARKER_PREVALENCE_ASSOCIATION_META", "PROGNOSTIC_FACTOR_META"),
        output_summary_fields=("overall_judgement", "selection", "comparability", "outcome_or_exposure"),
    ),
    "QUADAS-2": QualityToolDefinition(
        tool_name="QUADAS-2",
        domains=("patient_selection", "index_test", "reference_standard", "flow_and_timing"),
        judgement_options=("low", "high", "unclear"),
        recommended_profiles=("DIAGNOSTIC_ACCURACY_META",),
        output_summary_fields=("overall_judgement", "patient_selection", "index_test", "reference_standard", "flow_and_timing"),
    ),
    "JBI prevalence checklist": QualityToolDefinition(
        tool_name="JBI prevalence checklist",
        domains=("sample_frame", "sampling_method", "sample_size", "measurement", "coverage", "analysis"),
        judgement_options=("low", "some_concerns", "high", "unclear", "not_applicable"),
        recommended_profiles=("PREVALENCE_INCIDENCE_META", "prevalence_incidence_meta"),
        output_summary_fields=("overall_rating", "sample_frame", "sampling_method", "measurement"),
    ),
    "AHRQ cross-sectional checklist": QualityToolDefinition(
        tool_name="AHRQ cross-sectional checklist",
        domains=("source_population", "eligibility_criteria", "time_period", "consecutive_subjects", "subjective_components", "quality_assurance", "confounding"),
        judgement_options=("low", "some_concerns", "high", "unclear", "not_applicable"),
        recommended_profiles=("BIOMARKER_PREVALENCE_ASSOCIATION_META", "CONTINUOUS_BIOMARKER_DIFFERENCE_META", "biomarker_expression_difference_meta"),
        output_summary_fields=("overall_rating", "source_population", "eligibility_criteria", "confounding"),
    ),
    "Cochrane RoB generic": QualityToolDefinition(
        tool_name="Cochrane RoB generic",
        domains=("sequence_generation", "allocation_concealment", "blinding", "incomplete_outcome_data", "selective_reporting", "other_bias"),
        judgement_options=("low", "some_concerns", "high", "unclear", "not_applicable"),
        recommended_profiles=("TREATMENT_EFFECT_META", "binary_outcome_meta", "continuous_outcome_meta"),
        output_summary_fields=("overall_rating", "sequence_generation", "allocation_concealment", "selective_reporting"),
    ),
    "GRADE summary placeholder": QualityToolDefinition(
        tool_name="GRADE summary placeholder",
        domains=("risk_of_bias", "inconsistency", "indirectness", "imprecision", "publication_bias"),
        judgement_options=("not_assessed", "draft_note_only", "not_applicable"),
        recommended_profiles=("TREATMENT_EFFECT_META", "PROGNOSTIC_FACTOR_META", "DIAGNOSTIC_ACCURACY_META"),
        output_summary_fields=("grade_status", "risk_of_bias", "inconsistency", "imprecision"),
    ),
    "RoB2 simplified": QualityToolDefinition(
        tool_name="RoB2 simplified",
        domains=("randomization", "deviations", "missing_outcome_data", "outcome_measurement", "reported_result"),
        judgement_options=("low risk", "some concerns", "high risk", "unclear"),
        recommended_profiles=("TREATMENT_EFFECT_META",),
        output_summary_fields=("overall_judgement", "randomization", "deviations", "missing_outcome_data"),
    ),
    "JBI checklist placeholder": QualityToolDefinition(
        tool_name="JBI checklist placeholder",
        domains=("sample_frame", "sampling", "measurement", "analysis"),
        judgement_options=("yes", "no", "unclear", "not applicable"),
        recommended_profiles=("BIOMARKER_PREVALENCE_ASSOCIATION_META", "PREVALENCE_INCIDENCE_META"),
        output_summary_fields=("overall_judgement", "sample_frame", "sampling", "measurement"),
    ),
    "GRADE placeholder": QualityToolDefinition(
        tool_name="GRADE placeholder",
        domains=("risk_of_bias", "inconsistency", "indirectness", "imprecision", "publication_bias"),
        judgement_options=("not assessed", "not serious", "serious", "very serious"),
        recommended_profiles=("TREATMENT_EFFECT_META", "PROGNOSTIC_FACTOR_META"),
        output_summary_fields=("overall_judgement", "risk_of_bias", "inconsistency", "imprecision"),
    ),
}


def list_quality_tools() -> list[QualityToolDefinition]:
    return list(QUALITY_TOOL_REGISTRY.values())


def get_quality_tool(tool_name: str) -> QualityToolDefinition | None:
    aliases = {
        "RoB2 simplified": "RoB2 simplified",
        "ROB 2": "ROB2",
        "ROB2": "ROB2",
        "Newcastle-Ottawa Scale / NOS": "Newcastle-Ottawa Scale",
        "NOS": "NOS",
        "JBI checklist placeholder": "JBI checklist placeholder",
        "JBI prevalence checklist": "JBI prevalence checklist",
        "AHRQ cross-sectional": "AHRQ cross-sectional checklist",
        "GRADE placeholder": "GRADE placeholder",
        "GRADE summary placeholder": "GRADE summary placeholder",
    }
    return QUALITY_TOOL_REGISTRY.get(aliases.get(tool_name, tool_name))
