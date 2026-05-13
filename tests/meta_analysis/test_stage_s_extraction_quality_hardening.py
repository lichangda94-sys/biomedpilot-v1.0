from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.extraction_page import initial_extraction_state
from app.meta_analysis.pages.quality_page import initial_quality_state
from app.meta_analysis.services.extraction_form_service import ExtractionFormService
from app.meta_analysis.services.quality_service import QualityAssessmentService
from app.meta_analysis.services.quality_service import (
    NOS_DOMAINS,
    QUALITY_M6_GOVERNANCE_STATES,
    QUALITY_RATING_LABELS_ZH,
)


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


def test_m6_nos_quality_model_validation_and_domain_handling(tmp_path: Path) -> None:
    service = QualityAssessmentService()

    validation = service.validate_quality_assessment_model(
        tool_name="NOS",
        domains={"selection": "低风险/较好", "comparability": "不明确", "outcome_or_exposure": "高风险/较差"},
        overall_rating="不明确",
        state="draft",
    )
    invalid = service.validate_quality_assessment_model(
        tool_name="NOS",
        domains={"selection": "invalid", "unknown": "low_risk_or_good"},
        overall_rating="invalid",
        state="confirmed",
    )
    draft = service.create_nos_assessment_draft(
        tmp_path,
        study_id="study-1",
        record_id="rec-1",
        domains={"selection": "low_risk_or_good", "comparability": "unclear", "outcome_or_exposure": "high_risk_or_poor"},
        domain_notes={"selection": "Representative cohort."},
        reviewer_id="reviewer",
    )

    assert validation["validation_status"] == "valid"
    assert invalid["validation_status"] == "invalid"
    assert "unsupported_quality_domain:unknown" in invalid["errors"]
    assert set(NOS_DOMAINS) == {"selection", "comparability", "outcome_or_exposure"}
    assert QUALITY_RATING_LABELS_ZH["low_risk_or_good"] == "低风险/较好"
    assert draft.record["tool_name"] == "NOS"
    assert draft.record["domains"]["selection"] == "low_risk_or_good"
    assert draft.record["domain_notes"]["selection"].startswith("Representative")


def test_m6_quality_governance_suggested_is_not_confirmed_and_summary_counts(tmp_path: Path) -> None:
    service = QualityAssessmentService()
    _seed_confirmed_extraction_row(tmp_path)

    suggested = service.create_nos_assessment_draft(
        tmp_path,
        study_id="study-1",
        record_id="rec-1",
        domains={"selection": "low_risk_or_good", "comparability": "unclear", "outcome_or_exposure": "not_assessed"},
        overall_rating="unclear",
        reviewer_id="model",
        actor="model",
        assessment_state="suggested",
    )
    summary_before = service.quality_m6_summary(tmp_path)
    accepted = service.change_quality_assessment_state(tmp_path, assessment_id=suggested.assessment_id, state="user_accepted", actor="reviewer")
    confirmed = service.confirm_quality_assessment_by_user(tmp_path, assessment_id=suggested.assessment_id, actor="reviewer")
    summary_after = service.quality_m6_summary(tmp_path)

    assert suggested.success
    assert suggested.record["status"] == "suggested"
    assert summary_before["studies_with_confirmed_quality"] == 0
    assert accepted.record["status"] == "user_accepted"
    assert confirmed.record["status"] == "confirmed"
    assert summary_after["studies_pending_quality"] == 0
    assert summary_after["studies_with_confirmed_quality"] == 1
    assert summary_after["unclear"] == 1
    assert "confirmed" in QUALITY_M6_GOVERNANCE_STATES


def test_m6_quality_summary_counts_rating_buckets(tmp_path: Path) -> None:
    service = QualityAssessmentService()
    for index, rating in enumerate(("low_risk_or_good", "unclear", "high_risk_or_poor"), start=1):
        result = service.create_nos_assessment_draft(
            tmp_path,
            study_id=f"study-{index}",
            record_id=f"rec-{index}",
            domains={"selection": rating, "comparability": rating, "outcome_or_exposure": rating},
            overall_rating=rating,
            reviewer_id="reviewer",
        )
        service.confirm_quality_assessment_by_user(tmp_path, assessment_id=result.assessment_id, actor="reviewer")

    summary = service.quality_m6_summary(tmp_path, expected_study_ids=["study-1", "study-2", "study-3", "study-4"])

    assert summary == {
        "studies_pending_quality": 1,
        "studies_with_draft_quality": 0,
        "studies_with_confirmed_quality": 3,
        "low_risk_or_good": 1,
        "unclear": 1,
        "high_risk_or_poor": 1,
    }


def _seed_confirmed_extraction_row(project_dir: Path) -> None:
    path = project_dir / "extraction" / "extraction_effect_rows.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "effect_rows": [
                    {
                        "effect_row_id": "effect-internal-1",
                        "record_id": "rec-1",
                        "study_unit_id": "unit-1",
                        "study_unit_label": "Study One",
                        "extraction_status": "completed_by_user",
                        "evidence_state": "confirmed",
                        "m5_structured_fields": {
                            "study_id": "study-1",
                            "title": "Confirmed extracted study",
                            "first_author": "Zhang",
                            "year": "2025",
                            "study_design": "observational cohort",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
