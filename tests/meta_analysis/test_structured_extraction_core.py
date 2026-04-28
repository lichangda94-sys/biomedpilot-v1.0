from __future__ import annotations

from pathlib import Path

from app.meta_analysis.extraction.schema_registry import (
    BIOMARKER_PREVALENCE_ASSOCIATION_META,
    PROGNOSTIC_FACTOR_META,
    TREATMENT_EFFECT_META,
    get_extraction_schema_profile,
    list_extraction_schema_profiles,
)
from app.meta_analysis.models.extraction import (
    BinaryOutcomeData,
    ContinuousOutcomeData,
    ExtractedOutcome,
    ExtractionRecord,
    ExtractionValidationStatus,
    GenericEffectOutcomeData,
    OutcomeDataType,
    StudyCharacteristics,
)
from app.meta_analysis.services.extraction_record_storage_service import ExtractionRecordStorageService
from app.meta_analysis.services.extraction_service import ExtractionService
from app.meta_analysis.services.extraction_validation_service import ExtractionValidationService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType
from tests.meta_analysis.test_extraction_service import write_screening_queue


def study_characteristics() -> StudyCharacteristics:
    return StudyCharacteristics(
        first_author="Smith",
        year=2024,
        country="China",
        study_design="RCT",
        population="Adults with condition",
        sample_size=200,
        intervention_or_exposure="Treatment A",
        comparator="Control",
        follow_up="12 weeks",
    )


def binary_outcome() -> BinaryOutcomeData:
    return BinaryOutcomeData(
        outcome_name="Mortality",
        effect_measure="OR",
        experimental_events=10,
        experimental_total=100,
        control_events=20,
        control_total=100,
        timepoint="12 weeks",
    )


def continuous_outcome() -> ContinuousOutcomeData:
    return ContinuousOutcomeData(
        outcome_name="Symptom score",
        effect_measure="MD",
        experimental_mean=2.1,
        experimental_sd=0.8,
        experimental_total=80,
        control_mean=3.0,
        control_sd=1.1,
        control_total=75,
        unit="points",
    )


def generic_effect_outcome() -> GenericEffectOutcomeData:
    return GenericEffectOutcomeData(
        outcome_name="Overall survival",
        effect_measure="HR",
        effect=0.72,
        ci_lower=0.55,
        ci_upper=0.94,
        standard_error=0.14,
        adjusted=True,
        covariates=["age", "stage"],
    )


def extraction_record(*, extraction_id: str = "extr-1", record_id: str = "rec-1", study_id: str = "study-1") -> ExtractionRecord:
    return ExtractionRecord(
        extraction_id=extraction_id,
        project_id="meta-test",
        record_id=record_id,
        study_id=study_id,
        reviewer_id="reviewer-1",
        profile_type=TREATMENT_EFFECT_META,
        study_characteristics=study_characteristics(),
        outcomes=[
            ExtractedOutcome(
                outcome_id="out-1",
                outcome_data_type=OutcomeDataType.BINARY.value,
                data=binary_outcome(),
            )
        ],
        notes="structured extraction core fixture",
        source_location="Table 1",
        validation_status=ExtractionValidationStatus.VALID.value,
        created_at="2026-04-28T00:00:00+00:00",
        updated_at="2026-04-28T00:00:00+00:00",
    )


def test_structured_extraction_models_can_be_created() -> None:
    assert study_characteristics().sample_size == 200
    assert binary_outcome().experimental_total == 100
    assert continuous_outcome().experimental_sd == 0.8
    assert generic_effect_outcome().adjusted is True
    record = extraction_record()
    assert record.profile_type == TREATMENT_EFFECT_META
    assert record.outcomes[0].outcome_data_type == "binary"


def test_extraction_schema_registry_exposes_three_profiles() -> None:
    profiles = {profile.profile_type: profile for profile in list_extraction_schema_profiles()}
    assert set(profiles) == {
        TREATMENT_EFFECT_META,
        BIOMARKER_PREVALENCE_ASSOCIATION_META,
        PROGNOSTIC_FACTOR_META,
    }
    assert OutcomeDataType.BINARY.value in profiles[TREATMENT_EFFECT_META].allowed_outcome_data_types
    assert "HR" in profiles[PROGNOSTIC_FACTOR_META].supported_effect_measures
    assert get_extraction_schema_profile("missing") is None


def test_valid_binary_outcome_passes_validation() -> None:
    result = ExtractionValidationService().validate_binary_outcome(binary_outcome(), profile_type=TREATMENT_EFFECT_META)
    assert result.status == ExtractionValidationStatus.VALID.value
    assert result.errors == []


def test_binary_outcome_events_greater_than_total_is_error() -> None:
    outcome = BinaryOutcomeData(
        outcome_name="Mortality",
        effect_measure="OR",
        experimental_events=101,
        experimental_total=100,
        control_events=20,
        control_total=100,
    )
    result = ExtractionValidationService().validate_binary_outcome(outcome, profile_type=TREATMENT_EFFECT_META)
    assert "experimental_events_cannot_exceed_total" in result.errors


def test_generic_effect_ci_lower_greater_than_upper_is_error() -> None:
    outcome = GenericEffectOutcomeData(
        outcome_name="Overall survival",
        effect_measure="HR",
        effect=0.8,
        ci_lower=1.2,
        ci_upper=0.7,
    )
    result = ExtractionValidationService().validate_generic_effect_outcome(outcome, profile_type=PROGNOSTIC_FACTOR_META)
    assert "ci_lower_cannot_exceed_ci_upper" in result.errors


def test_ratio_effect_less_than_or_equal_to_zero_is_error() -> None:
    outcome = GenericEffectOutcomeData(outcome_name="Overall survival", effect_measure="HR", effect=0.0)
    result = ExtractionValidationService().validate_generic_effect_outcome(outcome, profile_type=PROGNOSTIC_FACTOR_META)
    assert "ratio_effect_must_be_positive" in result.errors


def test_validate_extraction_record_registers_validation_task(tmp_path) -> None:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    result = ExtractionValidationService(task_center=task_center).validate_extraction_record_task(
        project_id="meta-test",
        record=extraction_record(),
    )
    assert result.status == ExtractionValidationStatus.VALID.value
    assert task_center.list_tasks()[0].task_type is TaskType.EXTRACTION_RECORD_VALIDATION


def test_extraction_records_save_load_and_register_data_center(tmp_path) -> None:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    project_dir = tmp_path / "project"
    service = ExtractionRecordStorageService(task_center=task_center, data_center=data_center)
    output_path = service.save_extraction_records(project_dir, [extraction_record()])
    assert output_path == project_dir / "extraction" / "extraction_records.json"
    loaded = service.load_extraction_records(project_dir)
    assert loaded[0].extraction_id == "extr-1"
    assert loaded[0].outcomes[0].data.outcome_name == "Mortality"
    assert data_center.list_assets("meta-test")[0].data_type == "extraction_records"
    assert task_center.list_tasks()[0].task_type is TaskType.EXTRACTION_RECORD_SAVE


def test_get_extraction_records_by_record_and_study_id(tmp_path) -> None:
    project_dir = tmp_path / "project"
    service = ExtractionRecordStorageService()
    service.save_extraction_records(
        project_dir,
        [
            extraction_record(extraction_id="extr-1", record_id="rec-1", study_id="study-1"),
            extraction_record(extraction_id="extr-2", record_id="rec-2", study_id="study-1"),
        ],
    )
    assert len(service.get_extraction_records_by_record_id(project_dir, "rec-1")) == 1
    assert len(service.get_extraction_records_by_study_id(project_dir, "study-1")) == 2
    outcomes = service.list_extraction_outcomes(project_dir)
    assert {item["outcome_name"] for item in outcomes} == {"Mortality"}


def test_append_or_update_extraction_record_updates_existing_id(tmp_path) -> None:
    project_dir = tmp_path / "project"
    service = ExtractionRecordStorageService()
    service.save_extraction_records(project_dir, [extraction_record()])
    service.append_or_update_extraction_record(project_dir, extraction_record(record_id="rec-updated"))
    records = service.load_extraction_records(project_dir)
    assert len(records) == 1
    assert records[0].record_id == "rec-updated"


def test_existing_extraction_pool_functionality_still_works(tmp_path) -> None:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = ExtractionService(task_center=task_center, data_center=data_center, storage_root=tmp_path)
    source = write_screening_queue(Path(tmp_path), decisions=["included", "excluded"])
    result = service.create_pool(project_id="meta-test", screening_queue_path=str(source))
    assert result.success
    assert result.extraction_records == 1
    assert any(asset.data_type == "extraction_pool" for asset in data_center.list_assets("meta-test"))
