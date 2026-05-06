from __future__ import annotations

import csv
import json
from pathlib import Path

from app.meta_analysis.pages.quality_page import quality_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.quality_service import (
    GRADE_PLACEHOLDER_SCHEMA_VERSION,
    QUALITY_ASSESSMENT_RECORDS_V1_SCHEMA_VERSION,
    QUALITY_ASSESSMENT_RECORD_V1_SCHEMA_VERSION,
    QUALITY_ASSESSMENT_SUMMARY_V1_SCHEMA_VERSION,
    QUALITY_TOOL_REGISTRY_V1_SCHEMA_VERSION,
    QualityAssessmentService,
)
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def service_stack() -> tuple[QualityAssessmentService, MetaAuditLogService, MetaResearchGovernanceService]:
    audit = MetaAuditLogService()
    governance = MetaResearchGovernanceService(audit_log=audit)
    return QualityAssessmentService(audit_log=audit, research_governance=governance), audit, governance


def test_quality_tool_registry_v1_contains_required_tools_and_is_suggestion_only() -> None:
    service = QualityAssessmentService()
    registry = service.tool_registry_v1()
    tool_names = {tool["tool_name"] for tool in registry["tools"]}

    assert registry["schema_version"] == QUALITY_TOOL_REGISTRY_V1_SCHEMA_VERSION
    assert {
        "ROB2",
        "ROBINS-I",
        "Newcastle-Ottawa Scale",
        "QUADAS-2",
        "JBI prevalence checklist",
        "AHRQ cross-sectional checklist",
        "Cochrane RoB generic",
        "GRADE summary placeholder",
    } <= tool_names
    assert all(tool["recommendation_status"] == "suggestion_only" for tool in registry["tools"])
    assert all(tool["auto_scores_final_quality"] is False for tool in registry["tools"])


def test_recommends_quality_tools_by_meta_type_and_study_design() -> None:
    service = QualityAssessmentService()

    diagnostic = service.recommend_quality_tools(meta_type="diagnostic_accuracy_meta", study_design="")
    randomized = service.recommend_quality_tools(meta_type="", study_design="randomized controlled trial")
    observational = service.recommend_quality_tools(meta_type="", study_design="observational cohort study")
    prevalence = service.recommend_quality_tools(meta_type="", study_design="cross-sectional prevalence study")

    assert diagnostic[0]["tool_name"] == "QUADAS-2"
    assert any(item["tool_name"] == "ROB2" and item["status"] == "suggested" for item in randomized)
    assert any(item["tool_name"] == "Newcastle-Ottawa Scale" for item in observational)
    assert any(item["tool_name"] == "ROBINS-I" for item in observational)
    assert any(item["tool_name"] == "JBI prevalence checklist" for item in prevalence)
    assert all(item["requires_human_confirmation"] is True for item in diagnostic + randomized + observational + prevalence)


def test_manual_quality_assessment_draft_and_completion_write_audit_and_governance(tmp_path: Path) -> None:
    service, audit, governance = service_stack()

    draft = service.create_quality_assessment_draft(
        tmp_path,
        study_id="study-1",
        record_id="rec-1",
        tool_name="ROB2",
        domains={"randomization": "low", "missing_outcome_data": "some_concerns"},
        domain_notes={"missing_outcome_data": "Attrition reported by reviewer."},
        overall_rating="some_concerns",
        reviewer_id="rev-1",
        notes="Manual draft.",
        meta_type="treatment_comparative_meta",
        study_design="randomized controlled trial",
        actor="reviewer",
    )
    completed = service.complete_quality_assessment_by_user(tmp_path, assessment_id=draft.assessment_id, actor="reviewer")

    records_payload = read_json(tmp_path / "quality" / "quality_assessment_records_v1.json")
    records = records_payload["quality_assessment_records"]
    governance_events = governance.list_events(tmp_path)
    audit_events = audit.list_events(tmp_path)

    assert records_payload["schema_version"] == QUALITY_ASSESSMENT_RECORDS_V1_SCHEMA_VERSION
    assert records_payload["record_schema_version"] == QUALITY_ASSESSMENT_RECORD_V1_SCHEMA_VERSION
    assert len(records) == 1
    assert records[0]["status"] == "completed_by_user"
    assert records[0]["analysis_ready_dataset_created"] is False
    assert records[0]["statistics_run"] is False
    assert records[0]["prisma_advanced"] is False
    assert records[0]["grade_placeholder"]["schema_version"] == GRADE_PLACEHOLDER_SCHEMA_VERSION
    assert records[0]["grade_placeholder"]["auto_grade_generated"] is False
    assert draft.record["status"] == "draft"
    assert completed.record["status"] == "completed_by_user"
    assert any(event.action == "draft_created" and event.target_type == "quality_assessment_score" for event in governance_events)
    assert any(event.action == "confirm" and event.status == "confirmed" for event in governance_events)
    assert any(event.event_type == "record_saved" and event.target_type == "quality_assessment" for event in audit_events)
    assert any(event.event_type == "research_governance_event" for event in audit_events)


def test_quality_completion_does_not_trigger_analysis_dataset_statistics_or_prisma(tmp_path: Path) -> None:
    service = QualityAssessmentService()
    draft = service.create_quality_assessment_draft(
        tmp_path,
        study_id="study-1",
        record_id="rec-1",
        tool_name="QUADAS-2",
        domains={"patient_selection": "low", "index_test": "unclear"},
        overall_rating="unclear",
        reviewer_id="rev-1",
    )

    service.complete_quality_assessment_by_user(tmp_path, assessment_id=draft.assessment_id, actor="reviewer")
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)

    assert not (tmp_path / "analysis" / "analysis_ready_datasets.json").exists()
    assert not (tmp_path / "analysis" / "analysis_results.json").exists()
    assert not (tmp_path / "reports" / "prisma_flow_summary.json").exists()
    assert prisma.records_screened == 0
    assert prisma.full_text_reports_assessed == 0
    assert prisma.studies_included == 0


def test_grade_placeholder_and_quality_report_summary_do_not_auto_judge_grade(tmp_path: Path) -> None:
    service = QualityAssessmentService()
    placeholder = service.grade_summary_placeholder(tmp_path, outcome_id="mortality", actor="system")
    service.create_quality_assessment_draft(
        tmp_path,
        study_id="study-1",
        record_id="rec-1",
        tool_name="Newcastle-Ottawa Scale",
        domains={"selection": "low", "comparability": "some_concerns"},
        overall_rating="some_concerns",
        reviewer_id="rev-1",
    )

    summary = service.quality_summary_for_report(tmp_path)

    assert placeholder["schema_version"] == GRADE_PLACEHOLDER_SCHEMA_VERSION
    assert placeholder["certainty"] == "not_assessed"
    assert placeholder["auto_grade_generated"] is False
    assert summary["schema_version"] == QUALITY_ASSESSMENT_SUMMARY_V1_SCHEMA_VERSION
    assert summary["grade_status"] == "placeholder_only_no_auto_grade"
    assert summary["assessment_count"] == 1
    assert summary["analysis_ready_dataset_created"] is False
    assert summary["statistics_run"] is False
    assert summary["prisma_advanced"] is False
    assert summary["reporting_status"] == "draft_testing"


def test_quality_export_csv_json_and_page_state_surface_m15_boundaries(tmp_path: Path) -> None:
    service = QualityAssessmentService()
    draft = service.create_quality_assessment_draft(
        tmp_path,
        study_id="study-1",
        record_id="rec-1",
        tool_name="AHRQ cross-sectional checklist",
        domains={"source_population": "low"},
        overall_rating="low",
        reviewer_id="rev-1",
    )

    json_path = service.export_quality_assessments_v1_json(tmp_path)
    csv_path = service.export_quality_assessments_v1_csv(tmp_path)
    state = quality_state_from_project(tmp_path, service=service, selected_tool="AHRQ cross-sectional checklist")

    assert read_json(json_path)["quality_assessment_records"][0]["assessment_id"] == draft.assessment_id
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["assessment_id"] == draft.assessment_id
    assert rows[0]["source_population"] == "low"
    assert state.record_schema_version == QUALITY_ASSESSMENT_RECORD_V1_SCHEMA_VERSION
    assert state.summary_schema_version == QUALITY_ASSESSMENT_SUMMARY_V1_SCHEMA_VERSION
    assert state.tool_registry_schema_version == QUALITY_TOOL_REGISTRY_V1_SCHEMA_VERSION
    assert state.grade_placeholder_status == "placeholder_only_no_auto_grade"
    assert state.safety_flags == {
        "auto_quality_scoring": False,
        "auto_grade_conclusion": False,
        "creates_analysis_ready_dataset": False,
        "runs_statistics": False,
        "advances_prisma": False,
    }
    assert "quality_assessment_records_v1" in state.output_paths
