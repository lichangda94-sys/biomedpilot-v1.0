from __future__ import annotations

import csv
from pathlib import Path

from app.meta_analysis.models.extraction import OutcomeDataType
from app.meta_analysis.pages.extraction_page import initial_extraction_state
from app.meta_analysis.services.extraction_form_service import ExtractionFormService
from app.meta_analysis.services.extraction_record_storage_service import ExtractionRecordStorageService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def make_form_service(tmp_path) -> tuple[ExtractionFormService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = ExtractionFormService(task_center=task_center, data_center=data_center)
    return service, task_center, data_center


def binary_form_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "record_id": "rec-1",
        "study_id": "study-1",
        "reviewer_id": "reviewer-1",
        "profile_type": "TREATMENT_EFFECT_META",
        "outcome_data_type": OutcomeDataType.BINARY.value,
        "first_author": "Smith",
        "year": "2024",
        "country": "China",
        "study_design": "RCT",
        "population": "Adults",
        "sample_size": "200",
        "intervention_or_exposure": "Treatment",
        "comparator": "Control",
        "follow_up": "12 weeks",
        "outcome_name": "Mortality",
        "effect_measure": "OR",
        "experimental_events": "10",
        "experimental_total": "100",
        "control_events": "20",
        "control_total": "100",
        "timepoint": "12 weeks",
        "subgroup": "",
        "notes": "form integration fixture",
        "source_location": "Table 1",
    }
    data.update(overrides)
    return data


def test_extraction_page_state_exposes_testing_form_fields() -> None:
    state = initial_extraction_state()
    assert state.status_label == "测试中"
    assert "ExtractionRecord 表单" in state.description
    assert "TREATMENT_EFFECT_META" in state.profile_options
    assert OutcomeDataType.BINARY.value in state.outcome_type_options
    assert "first_author" in state.study_characteristics_fields
    assert "experimental_events" in state.binary_outcome_fields
    assert "experimental_mean" in state.continuous_outcome_fields
    assert "ci_lower" in state.generic_effect_outcome_fields
    assert state.export_path == "project_dir/exports/extraction_records.csv"


def test_load_candidate_records_empty_state_is_safe(tmp_path) -> None:
    service, _task_center, _data_center = make_form_service(tmp_path)
    assert service.load_candidate_records("") == []
    assert service.load_candidate_records(str(tmp_path / "missing.json")) == []


def test_valid_binary_extraction_record_can_be_saved(tmp_path) -> None:
    service, task_center, data_center = make_form_service(tmp_path)
    project_dir = tmp_path / "project"
    result = service.save_extraction_record_from_form(
        project_dir=project_dir,
        project_id="meta-test",
        form_data=binary_form_data(),
    )
    assert result.success
    assert result.output_path == str(project_dir / "extraction" / "extraction_records.json")
    assert result.validation.errors == []
    stored = ExtractionRecordStorageService().load_extraction_records(project_dir)
    assert stored[0].record_id == "rec-1"
    assert stored[0].validation_status == "valid"
    assert any(asset.data_type == "extraction_records" for asset in data_center.list_assets("meta-test"))
    assert task_center.list_tasks()[0].task_type is TaskType.EXTRACTION_RECORD_SAVE


def test_invalid_binary_extraction_record_blocks_save(tmp_path) -> None:
    service, _task_center, data_center = make_form_service(tmp_path)
    project_dir = tmp_path / "project"
    result = service.save_extraction_record_from_form(
        project_dir=project_dir,
        project_id="meta-test",
        form_data=binary_form_data(experimental_events="101"),
    )
    assert not result.success
    assert "experimental_events_cannot_exceed_total" in result.validation.errors
    assert not (project_dir / "extraction" / "extraction_records.json").exists()
    assert data_center.list_assets("meta-test") == []


def test_extraction_records_csv_can_be_exported(tmp_path) -> None:
    service, task_center, data_center = make_form_service(tmp_path)
    project_dir = tmp_path / "project"
    save_result = service.save_extraction_record_from_form(
        project_dir=project_dir,
        project_id="meta-test",
        form_data=binary_form_data(),
    )
    assert save_result.success
    export = service.export_extraction_records_csv(project_dir=project_dir, project_id="meta-test")
    assert export.success
    assert export.output_path == str(project_dir / "exports" / "extraction_records.csv")
    with Path(export.output_path).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["record_id"] == "rec-1"
    assert rows[0]["outcome_name"] == "Mortality"
    assert any(asset.data_type == "extraction_records_export" for asset in data_center.list_assets("meta-test"))
    assert task_center.list_tasks()[0].task_type is TaskType.EXTRACTION_EXPORT
