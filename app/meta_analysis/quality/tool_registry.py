from __future__ import annotations

from app.meta_analysis.models.systematic_review import QualityToolDefinition


QUALITY_TOOL_REGISTRY: dict[str, QualityToolDefinition] = {
    "NOS": QualityToolDefinition(
        tool_name="NOS",
        domains=("selection", "comparability", "outcome_or_exposure"),
        judgement_options=("low risk", "moderate risk", "high risk", "unclear"),
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
    return QUALITY_TOOL_REGISTRY.get(tool_name)
