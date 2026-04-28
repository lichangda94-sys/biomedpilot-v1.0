from __future__ import annotations

from pathlib import Path

from app.meta_analysis.pages.extraction_page import initial_extraction_state
from app.meta_analysis.pages.quality_page import initial_quality_state
from app.meta_analysis.services.extraction_form_service import ExtractionFormService
from app.meta_analysis.services.quality_service import QualityAssessmentService


def valid_form_data() -> dict[str, object]:
    return {
        "record_id": "rec-1",
        "study_id": "study-1",
        "reviewer_id": "reviewer-a",
        "profile_type": "TREATMENT_EFFECT_META",
        "first_author": "Adams",
        "year": "2024",
        "sample_size": "200",
        "outcome_data_type": "binary",
        "outcome_name": "Mortality",
        "effect_measure": "OR",
        "experimental_events": "10",
        "experimental_total": "100",
        "control_events": "20",
        "control_total": "100",
    }


def test_extraction_draft_lifecycle_copy_previous_multi_outcome_and_completeness(tmp_path: Path) -> None:
    service = ExtractionFormService()
    project_dir = tmp_path / "project"
    form = valid_form_data()

    draft_path = service.save_draft(project_dir, project_id="project", record_id="rec-1", form_data=form)
    drafts = service.load_drafts(project_dir)
    record = service.build_extraction_record_with_outcomes(
        project_id="project",
        form_data=form,
        outcome_rows=[
            form,
            {**form, "outcome_name": "Hospitalization", "experimental_events": "12", "control_events": "18"},
        ],
    )
    save_result = service.save_extraction_record(project_dir=project_dir, record=record)

    assert draft_path.exists()
    assert drafts[0].record_id == "rec-1"
    assert len(record.outcomes) == 2
    assert save_result.success
    assert service.copy_previous_study_characteristics(project_dir)["first_author"] == "Adams"
    assert service.extraction_completeness_score(record) == 1.0
    assert service.pre_export_completeness_check(project_dir)["ready_for_export"] is True
    assert service.delete_draft(project_dir, drafts[0].draft_id) is True


def test_extraction_field_level_validation_and_page_state() -> None:
    service = ExtractionFormService()
    form = valid_form_data()
    form.pop("outcome_name")
    record = service.build_extraction_record(project_id="project", form_data=form)
    summary = service.field_validation_summary(record)
    state = initial_extraction_state()

    assert "outcome_name" in summary.errors_by_field
    assert "outcome_common" in state.required_fields
    assert "add_outcome_row" in state.outcome_row_controls
    assert state.export_readiness_warning


def test_quality_domain_notes_suggestion_completeness_and_page_state(tmp_path: Path) -> None:
    service = QualityAssessmentService()
    project_dir = tmp_path / "project"

    assessment = service.create_quality_assessment(
        project_id="project",
        study_id="study-1",
        record_id="rec-1",
        tool_name="RoB2 simplified",
        domains={"randomization": "low risk", "deviations": "some concerns"},
        domain_notes={"deviations": "Protocol deviations were partially reported."},
        overall_judgement=service.suggest_overall_judgement("RoB2 simplified", {"randomization": "low risk", "deviations": "some concerns"}),
        reviewer_id="reviewer-a",
    )
    service.save_quality_assessment(project_dir, assessment)
    summary = service.quality_completeness_summary(project_dir, expected_study_ids=["study-1", "study-2"])
    state = initial_quality_state(service)

    assert assessment.domain_notes["deviations"].startswith("Protocol")
    assert assessment.overall_judgement == "some concerns"
    assert summary["missing_study_ids"] == ["study-2"]
    assert summary["completeness_score"] == 0.5
    assert state.domain_note_support is True
    assert "QUADAS-2" in state.tool_options

