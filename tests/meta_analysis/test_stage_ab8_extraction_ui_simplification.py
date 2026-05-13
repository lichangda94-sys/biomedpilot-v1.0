from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.extraction.schema_registry import TREATMENT_EFFECT_META
from app.meta_analysis.models.extraction import OutcomeDataType
from app.meta_analysis.pages.extraction_page import simplified_extraction_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.extraction_form_service import ExtractionFormService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter


def valid_binary_form(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "record_id": "rec-1",
        "study_id": "study-1",
        "reviewer_id": "rev-1",
        "profile_type": TREATMENT_EFFECT_META,
        "outcome_data_type": OutcomeDataType.BINARY.value,
        "first_author": "Smith",
        "year": "2025",
        "population": "Adults with condition",
        "sample_size": "120",
        "intervention_or_exposure": "Drug A",
        "comparator": "Placebo",
        "outcome_name": "Response",
        "effect_measure": "OR",
        "experimental_events": "20",
        "experimental_total": "60",
        "control_events": "10",
        "control_total": "60",
        "source_location": "Table 2",
    }
    payload.update(overrides)
    return payload


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_ab8_manual_edit_log_records_before_after_source_and_audit(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    audit_log = MetaAuditLogService()
    service = ExtractionFormService(data_center=data_center, audit_log=audit_log)

    log_path = service.record_manual_edit(
        project_dir,
        extraction_id="extr-1",
        record_id="rec-1",
        field_name="experimental_events",
        before_value="18",
        after_value="20",
        reviewer_id="rev-1",
        note="Corrected from full-text table.",
        source_location="Table 2, page 4",
        used_for_formal_analysis=True,
    )

    assert log_path == project_dir / "extraction" / "manual_edits_log.jsonl"
    edits = service.load_manual_edits(project_dir)
    assert edits[0].field_name == "experimental_events"
    assert edits[0].before_value == "18"
    assert edits[0].after_value == "20"
    assert edits[0].source_location == "Table 2, page 4"
    assert edits[0].used_for_formal_analysis is True
    assert "extraction_manual_edits_log" in {asset.data_type for asset in data_center.list_assets(project_dir.name)}
    assert any(event.event_type == "extraction_updated" for event in audit_log.list_events(project_dir))


def test_ab8_simplified_state_uses_final_included_studies_when_no_records(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    write_json(
        project_dir / "fulltext" / "final_included_studies.json",
        {
            "included_studies": [
                {"record_id": "rec-1", "study_id": "study-1", "title": "Trial A", "year": "2025"},
                {"record_id": "rec-2", "title": "Trial B"},
            ]
        },
    )

    state = simplified_extraction_state_from_project(project_dir)

    assert state.status_label == "Testing / Developer Preview"
    assert state.saved_record_count == 0
    assert [row.record_id for row in state.study_rows] == ["rec-1", "rec-2"]
    assert state.study_rows[0].status == "needs_extraction"
    assert state.manual_edits_log_path.endswith("extraction/manual_edits_log.jsonl")
    assert state.export_ready is True
    assert "manual_supplement" in state.field_help_text
    assert state.required_field_markers["record_id"] is True


def test_ab8_simplified_state_reads_saved_records_completeness_and_drafts(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = ExtractionFormService(task_center=task_center, data_center=data_center)
    record = service.build_extraction_record(project_id=project_dir.name, form_data=valid_binary_form())
    save_result = service.save_extraction_record(project_dir=project_dir, record=record)
    assert save_result.success is True
    service.save_draft(project_dir, project_id=project_dir.name, record_id="rec-2", form_data=valid_binary_form(record_id="rec-2"))

    state = simplified_extraction_state_from_project(project_dir, service=service)

    assert state.saved_record_count == 1
    assert state.draft_count == 1
    assert state.copy_previous_available is True
    assert state.study_rows[0].completeness_score == 1.0
    assert state.completeness_summary["ready_for_export"] is True
    assert state.extraction_records_csv_path.endswith("exports/extraction_records.csv")


def test_ab8_outcome_row_templates_and_multi_outcome_compatibility(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    service = ExtractionFormService()
    record = service.build_extraction_record_with_outcomes(
        project_id=project_dir.name,
        form_data=valid_binary_form(),
        outcome_rows=[
            valid_binary_form(outcome_name="Response", experimental_events="20", control_events="10"),
            valid_binary_form(outcome_name="Mortality", experimental_events="5", control_events="8"),
        ],
    )

    state = simplified_extraction_state_from_project(project_dir, service=service)

    assert len(record.outcomes) == 2
    assert {template.outcome_data_type for template in state.outcome_row_templates} >= {"binary", "continuous", "generic_effect"}
    binary_template = next(template for template in state.outcome_row_templates if template.outcome_data_type == "binary")
    assert "experimental_events" in binary_template.fields
    assert "outcome_name" in binary_template.required_fields
