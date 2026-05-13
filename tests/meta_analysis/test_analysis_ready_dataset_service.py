from __future__ import annotations

from pathlib import Path

from app.meta_analysis.extraction.schema_registry import PROGNOSTIC_FACTOR_META, TREATMENT_EFFECT_META
from app.meta_analysis.models.extraction import (
    BinaryOutcomeData,
    ContinuousOutcomeData,
    ExtractedOutcome,
    ExtractionRecord,
    GenericEffectOutcomeData,
    OutcomeDataType,
    StudyCharacteristics,
)
from app.meta_analysis.pages.analysis_page import initial_analysis_state
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.services.extraction_record_storage_service import ExtractionRecordStorageService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def make_service(tmp_path: Path) -> tuple[AnalysisDatasetService, ExtractionRecordStorageService, TaskCenter, DataCenter, Path]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    extraction_storage = ExtractionRecordStorageService(task_center=task_center, data_center=data_center)
    service = AnalysisDatasetService(
        extraction_storage=extraction_storage,
        task_center=task_center,
        data_center=data_center,
    )
    project_dir = tmp_path / "project"
    return service, extraction_storage, task_center, data_center, project_dir


def test_builds_analysis_ready_dataset_from_binary_extraction_records(tmp_path: Path) -> None:
    service, extraction_storage, task_center, data_center, project_dir = make_service(tmp_path)
    extraction_storage.save_extraction_records(
        project_dir,
        [
            binary_record("extr-1", "rec-1", "Study 1", 10, 100, 12, 100),
            binary_record("extr-2", "rec-2", "Study 2", 7, 80, 11, 78),
        ],
    )

    available = service.list_available_outcomes(project_dir)
    dataset = service.build_analysis_ready_dataset(project_dir, TREATMENT_EFFECT_META, "Mortality", "OR")
    output_path = service.save_analysis_ready_dataset(project_dir, dataset)

    assert available[0]["outcome_name"] == "Mortality"
    assert available[0]["record_count"] == 2
    assert dataset.outcome_data_type == OutcomeDataType.BINARY.value
    assert dataset.included_extraction_ids == ["extr-1", "extr-2"]
    assert dataset.excluded_extraction_ids == []
    assert dataset.validation_errors == []
    assert dataset.study_rows[0].normalized_data["experimental_non_events"] == 90
    assert output_path == project_dir / "analysis" / "analysis_ready_datasets.json"
    assert task_center.list_tasks()[0].task_type is TaskType.ANALYSIS_DATASET_BUILD
    assert any(asset.data_type == "analysis_ready_dataset" for asset in data_center.list_assets("meta-test"))


def test_builds_analysis_ready_dataset_from_continuous_extraction_records(tmp_path: Path) -> None:
    service, extraction_storage, _task_center, _data_center, project_dir = make_service(tmp_path)
    extraction_storage.save_extraction_records(
        project_dir,
        [continuous_record("extr-1", "rec-1", "Study 1")],
    )

    dataset = service.build_analysis_ready_dataset(project_dir, TREATMENT_EFFECT_META, "Pain score", "MD")

    assert dataset.outcome_data_type == OutcomeDataType.CONTINUOUS.value
    assert dataset.included_extraction_ids == ["extr-1"]
    assert dataset.study_rows[0].normalized_data["experimental_sd"] == 1.2
    assert "fewer_than_two_included_studies" in dataset.validation_warnings


def test_builds_analysis_ready_dataset_from_generic_effect_records(tmp_path: Path) -> None:
    service, extraction_storage, _task_center, _data_center, project_dir = make_service(tmp_path)
    extraction_storage.save_extraction_records(
        project_dir,
        [generic_record("extr-1", "rec-1", "Study 1", effect=1.8, ci_lower=1.1, ci_upper=2.6)],
    )

    dataset = service.build_analysis_ready_dataset(project_dir, PROGNOSTIC_FACTOR_META, "Overall survival", "HR")

    assert dataset.outcome_data_type == OutcomeDataType.GENERIC_EFFECT.value
    assert dataset.included_extraction_ids == ["extr-1"]
    assert dataset.study_rows[0].normalized_data["effect"] == 1.8
    assert dataset.study_rows[0].normalized_data["ci_upper"] == 2.6


def test_build_dataset_reports_missing_extraction_records(tmp_path: Path) -> None:
    service, _extraction_storage, task_center, _data_center, project_dir = make_service(tmp_path)

    dataset = service.build_analysis_ready_dataset(project_dir, TREATMENT_EFFECT_META, "Mortality", "OR")

    assert "extraction_records_missing" in dataset.validation_errors
    assert "analysis_ready_dataset_has_no_included_studies" in dataset.validation_errors
    assert dataset.included_extraction_ids == []
    assert task_center.list_tasks()[0].task_type is TaskType.ANALYSIS_DATASET_BUILD


def test_build_dataset_reports_outcome_mismatch(tmp_path: Path) -> None:
    service, extraction_storage, _task_center, _data_center, project_dir = make_service(tmp_path)
    extraction_storage.save_extraction_records(project_dir, [binary_record("extr-1", "rec-1", "Study 1", 1, 10, 2, 10)])

    dataset = service.build_analysis_ready_dataset(project_dir, TREATMENT_EFFECT_META, "Hospitalization", "OR")

    assert "matching_outcome_missing" in dataset.validation_errors
    assert dataset.study_rows == []


def test_invalid_extraction_is_excluded_with_reason(tmp_path: Path) -> None:
    service, extraction_storage, _task_center, _data_center, project_dir = make_service(tmp_path)
    extraction_storage.save_extraction_records(
        project_dir,
        [binary_record("extr-1", "rec-1", "Study 1", 15, 10, 2, 10, validation_status="invalid")],
    )

    dataset = service.build_analysis_ready_dataset(project_dir, TREATMENT_EFFECT_META, "Mortality", "OR")

    assert dataset.included_extraction_ids == []
    assert dataset.excluded_extraction_ids == ["extr-1"]
    assert dataset.study_rows[0].analysis_status == "excluded"
    assert "experimental_events_cannot_exceed_total" in dataset.study_rows[0].exclusion_reason
    assert dataset.study_rows[0].exclusion_reason


def test_analysis_ready_dataset_save_load_and_list(tmp_path: Path) -> None:
    service, extraction_storage, _task_center, _data_center, project_dir = make_service(tmp_path)
    extraction_storage.save_extraction_records(project_dir, [binary_record("extr-1", "rec-1", "Study 1", 1, 10, 2, 10)])
    dataset = service.build_analysis_ready_dataset(project_dir, TREATMENT_EFFECT_META, "Mortality", "OR")

    service.save_analysis_ready_dataset(project_dir, dataset)
    loaded = service.load_analysis_ready_dataset(project_dir, dataset.dataset_id)

    assert loaded is not None
    assert loaded.dataset_id == dataset.dataset_id
    assert service.list_analysis_ready_datasets(project_dir)[0].dataset_id == dataset.dataset_id


def test_available_outcomes_and_analysis_page_state_include_dataset_builder() -> None:
    state = initial_analysis_state()

    assert "analysis-ready dataset" in state.description
    assert TREATMENT_EFFECT_META in state.profile_options
    assert "outcome_name" in state.available_outcome_columns
    assert "included_study_count" in state.dataset_summary_fields


def binary_record(
    extraction_id: str,
    record_id: str,
    first_author: str,
    experimental_events: int,
    experimental_total: int,
    control_events: int,
    control_total: int,
    *,
    validation_status: str = "valid",
) -> ExtractionRecord:
    return extraction_record(
        extraction_id,
        record_id,
        first_author,
        TREATMENT_EFFECT_META,
        ExtractedOutcome(
            outcome_id=f"out-{extraction_id}",
            outcome_data_type=OutcomeDataType.BINARY.value,
            data=BinaryOutcomeData(
                outcome_name="Mortality",
                effect_measure="OR",
                experimental_events=experimental_events,
                experimental_total=experimental_total,
                control_events=control_events,
                control_total=control_total,
            ),
        ),
        validation_status=validation_status,
    )


def continuous_record(extraction_id: str, record_id: str, first_author: str) -> ExtractionRecord:
    return extraction_record(
        extraction_id,
        record_id,
        first_author,
        TREATMENT_EFFECT_META,
        ExtractedOutcome(
            outcome_id=f"out-{extraction_id}",
            outcome_data_type=OutcomeDataType.CONTINUOUS.value,
            data=ContinuousOutcomeData(
                outcome_name="Pain score",
                effect_measure="MD",
                experimental_mean=3.4,
                experimental_sd=1.2,
                experimental_total=40,
                control_mean=4.1,
                control_sd=1.4,
                control_total=42,
            ),
        ),
    )


def generic_record(
    extraction_id: str,
    record_id: str,
    first_author: str,
    *,
    effect: float,
    ci_lower: float,
    ci_upper: float,
) -> ExtractionRecord:
    return extraction_record(
        extraction_id,
        record_id,
        first_author,
        PROGNOSTIC_FACTOR_META,
        ExtractedOutcome(
            outcome_id=f"out-{extraction_id}",
            outcome_data_type=OutcomeDataType.GENERIC_EFFECT.value,
            data=GenericEffectOutcomeData(
                outcome_name="Overall survival",
                effect_measure="HR",
                effect=effect,
                ci_lower=ci_lower,
                ci_upper=ci_upper,
                adjusted=True,
                covariates=["age", "stage"],
            ),
        ),
    )


def extraction_record(
    extraction_id: str,
    record_id: str,
    first_author: str,
    profile_type: str,
    outcome: ExtractedOutcome,
    *,
    validation_status: str = "valid",
) -> ExtractionRecord:
    return ExtractionRecord(
        extraction_id=extraction_id,
        project_id="meta-test",
        record_id=record_id,
        study_id=f"study-{record_id}",
        reviewer_id="reviewer-1",
        profile_type=profile_type,
        study_characteristics=StudyCharacteristics(
            first_author=first_author,
            year=2024,
            country="CN",
            study_design="RCT",
            population="Adults",
            sample_size=120,
        ),
        outcomes=[outcome],
        validation_status=validation_status,
        created_at="2026-04-28T00:00:00+00:00",
        updated_at="2026-04-28T00:00:00+00:00",
    )
