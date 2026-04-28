from __future__ import annotations

from pathlib import Path

import pytest

from app.meta_analysis.extraction.schema_registry import (
    CORRELATION_META,
    DIAGNOSTIC_ACCURACY_META,
    NETWORK_META_ANALYSIS,
    PREVALENCE_INCIDENCE_META,
    get_extraction_schema_profile,
)
from app.meta_analysis.models.analysis_dataset import StudyAnalysisRow
from app.meta_analysis.models.extraction import (
    CorrelationOutcomeData,
    DiagnosticAccuracyOutcomeData,
    ExtractedOutcome,
    ExtractionRecord,
    ExtractionValidationStatus,
    OutcomeDataType,
    ProportionOutcomeData,
    StudyCharacteristics,
)
from app.meta_analysis.pages.analysis_page import initial_analysis_state
from app.meta_analysis.pages.extraction_page import initial_extraction_state
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.services.extraction_record_storage_service import ExtractionRecordStorageService
from app.meta_analysis.services.extraction_validation_service import ExtractionValidationService
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder
from app.meta_analysis.stats.meta_effects import (
    correlation_study_effect,
    diagnostic_accuracy_metrics,
    fisher_z_back_transform,
    fisher_z_transform,
    proportion_study_effect,
)


def test_advanced_profile_registry_can_read_new_profiles() -> None:
    diagnostic = get_extraction_schema_profile(DIAGNOSTIC_ACCURACY_META)
    prevalence = get_extraction_schema_profile(PREVALENCE_INCIDENCE_META)
    correlation = get_extraction_schema_profile(CORRELATION_META)
    network = get_extraction_schema_profile(NETWORK_META_ANALYSIS)

    assert diagnostic is not None
    assert OutcomeDataType.DIAGNOSTIC_ACCURACY.value in diagnostic.allowed_outcome_data_types
    assert "DOR" in diagnostic.supported_effect_measures
    assert prevalence is not None
    assert OutcomeDataType.PROPORTION.value in prevalence.allowed_outcome_data_types
    assert correlation is not None
    assert OutcomeDataType.CORRELATION.value in correlation.allowed_outcome_data_types
    assert network is not None
    assert network.metadata["status"] == "not_implemented"


def test_advanced_outcome_validation() -> None:
    service = ExtractionValidationService()

    diagnostic = service.validate_diagnostic_accuracy_outcome(
        DiagnosticAccuracyOutcomeData(outcome_name="Index test positive", tp=80, fp=10, fn=20, tn=90),
        profile_type=DIAGNOSTIC_ACCURACY_META,
    )
    proportion = service.validate_proportion_outcome(
        ProportionOutcomeData(outcome_name="Prevalence", events=25, total=100),
        profile_type=PREVALENCE_INCIDENCE_META,
    )
    correlation = service.validate_correlation_outcome(
        CorrelationOutcomeData(outcome_name="Marker correlation", r=0.42, sample_size=64),
        profile_type=CORRELATION_META,
    )

    assert diagnostic.status == ExtractionValidationStatus.VALID.value
    assert proportion.status == ExtractionValidationStatus.VALID.value
    assert correlation.status == ExtractionValidationStatus.VALID.value
    invalid = service.validate_correlation_outcome(
        CorrelationOutcomeData(outcome_name="Invalid", r=1.0, sample_size=3),
        profile_type=CORRELATION_META,
    )
    assert "correlation_must_be_between_minus_one_and_one" in invalid.errors
    assert "sample_size_must_exceed_three" in invalid.errors


def test_proportion_and_correlation_effect_calculations() -> None:
    prevalence = proportion_study_effect(
        study_row(
            outcome_data_type=OutcomeDataType.PROPORTION.value,
            effect_measure="PREVALENCE",
            normalized_data={"events": 25, "non_events": 75, "total": 100, "effect_measure": "PREVALENCE"},
        )
    )
    z_value = fisher_z_transform(0.5)
    correlation = correlation_study_effect(
        study_row(
            outcome_data_type=OutcomeDataType.CORRELATION.value,
            effect_measure="CORRELATION",
            normalized_data={"r": 0.5, "sample_size": 40, "effect_measure": "CORRELATION"},
        )
    )

    assert prevalence.effect == pytest.approx(0.25)
    assert prevalence.standard_error > 0
    assert fisher_z_back_transform(z_value) == pytest.approx(0.5)
    assert correlation.effect == pytest.approx(0.5)
    assert correlation.standard_error == pytest.approx((1 / 37) ** 0.5)


def test_diagnostic_basic_metrics() -> None:
    metrics = diagnostic_accuracy_metrics(tp=80, fp=10, fn=20, tn=90)

    assert metrics.sensitivity == pytest.approx(0.8)
    assert metrics.specificity == pytest.approx(0.9)
    assert metrics.plr == pytest.approx(8.0)
    assert metrics.nlr == pytest.approx(2 / 9)
    assert metrics.dor == pytest.approx(36.0)


def test_analysis_ready_dataset_supports_advanced_outcome_types(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    storage = ExtractionRecordStorageService()
    service = AnalysisDatasetService(extraction_storage=storage)
    storage.save_extraction_records(
        project_dir,
        [
            extraction_record(
                "extr-prev",
                PREVALENCE_INCIDENCE_META,
                ExtractedOutcome(
                    outcome_id="out-prev",
                    outcome_data_type=OutcomeDataType.PROPORTION.value,
                    data=ProportionOutcomeData(outcome_name="Prevalence", events=25, total=100),
                ),
            ),
            extraction_record(
                "extr-corr",
                CORRELATION_META,
                ExtractedOutcome(
                    outcome_id="out-corr",
                    outcome_data_type=OutcomeDataType.CORRELATION.value,
                    data=CorrelationOutcomeData(outcome_name="Marker correlation", r=0.42, sample_size=64),
                ),
            ),
            extraction_record(
                "extr-dx",
                DIAGNOSTIC_ACCURACY_META,
                ExtractedOutcome(
                    outcome_id="out-dx",
                    outcome_data_type=OutcomeDataType.DIAGNOSTIC_ACCURACY.value,
                    data=DiagnosticAccuracyOutcomeData(outcome_name="Index test positive", tp=80, fp=10, fn=20, tn=90),
                ),
            ),
        ],
    )

    prevalence = service.build_analysis_ready_dataset(project_dir, PREVALENCE_INCIDENCE_META, "Prevalence", "PREVALENCE")
    correlation = service.build_analysis_ready_dataset(project_dir, CORRELATION_META, "Marker correlation", "CORRELATION")
    diagnostic = service.build_analysis_ready_dataset(project_dir, DIAGNOSTIC_ACCURACY_META, "Index test positive", "DOR")

    assert prevalence.outcome_data_type == OutcomeDataType.PROPORTION.value
    assert prevalence.study_rows[0].normalized_data["proportion"] == 0.25
    assert correlation.outcome_data_type == OutcomeDataType.CORRELATION.value
    assert correlation.study_rows[0].normalized_data["r"] == 0.42
    assert diagnostic.outcome_data_type == OutcomeDataType.DIAGNOSTIC_ACCURACY.value
    assert diagnostic.study_rows[0].normalized_data["dor"] == pytest.approx(36.0)
    assert not prevalence.validation_errors
    assert not correlation.validation_errors
    assert not diagnostic.validation_errors


def test_network_meta_placeholder_returns_not_implemented(tmp_path: Path) -> None:
    dataset = AnalysisDatasetService().build_analysis_ready_dataset(
        tmp_path / "project",
        NETWORK_META_ANALYSIS,
        "Network outcome",
        "OR",
    )

    assert "network_meta_analysis_not_implemented" in dataset.validation_errors
    assert "analysis_ready_dataset_has_no_included_studies" in dataset.validation_errors


def test_page_states_and_formal_report_list_advanced_methods(tmp_path: Path) -> None:
    extraction_state = initial_extraction_state()
    analysis_state = initial_analysis_state()
    project_dir = tmp_path / "project"

    report_path = FormalMarkdownReportBuilder().build_formal_markdown_report(project_dir)
    report_text = report_path.read_text(encoding="utf-8")

    assert OutcomeDataType.PROPORTION.value in extraction_state.outcome_type_options
    assert "diagnostic_accuracy" in extraction_state.outcome_type_options
    assert "network meta 显示 not implemented" in analysis_state.description
    assert "Advanced method summary" in report_text
    assert "Network meta-analysis" in report_text


def study_row(*, outcome_data_type: str, effect_measure: str, normalized_data: dict[str, object]) -> StudyAnalysisRow:
    return StudyAnalysisRow(
        study_id="study-1",
        record_id="rec-1",
        first_author="Author",
        year=2024,
        outcome_name="Advanced outcome",
        effect_measure=effect_measure,
        outcome_data_type=outcome_data_type,
        raw_data={},
        normalized_data=normalized_data,
        analysis_status="included",
    )


def extraction_record(extraction_id: str, profile_type: str, outcome: ExtractedOutcome) -> ExtractionRecord:
    return ExtractionRecord(
        extraction_id=extraction_id,
        project_id="meta-test",
        record_id=f"rec-{extraction_id}",
        study_id=f"study-{extraction_id}",
        reviewer_id="reviewer-1",
        profile_type=profile_type,
        study_characteristics=StudyCharacteristics(
            first_author="Advanced",
            year=2024,
            country="CN",
            study_design="Observational",
            population="Adults",
            sample_size=120,
        ),
        outcomes=[outcome],
        validation_status=ExtractionValidationStatus.VALID.value,
        created_at="2026-04-28T00:00:00+00:00",
        updated_at="2026-04-28T00:00:00+00:00",
    )
