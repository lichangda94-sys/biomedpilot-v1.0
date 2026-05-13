from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.meta_analysis.pages.protocol_page import (
    write_pubmed_search_execution_artifacts,
    write_protocol_search_strategy_artifacts,
)
from app.meta_analysis.search.pubmed_search_service import PubMedSearchExecution, PubMedSearchResult
from app.meta_analysis.search.search_strategy_models import MetaSearchStrategyDraft, QueryDraft
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.ai_suggestion_service import AISuggestionService
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.research_governance_service import (
    AUTONOMOUS_ENGINEERING_SCOPES,
    HUMAN_CONFIRMATION_TARGETS,
    MetaResearchGovernanceService,
    ResearchDecisionStatus,
    is_autonomous_engineering_scope,
    requires_human_confirmation,
)


def test_draft_and_suggestion_events_cannot_be_consumed_as_confirmed(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    service = MetaResearchGovernanceService()

    draft = service.record_draft_created(
        project_dir,
        target_type="final_pico",
        target_id="protocol-1",
        after={"population": "adult patients"},
    )
    suggestion = service.record_suggestion_created(
        project_dir,
        target_type="title_abstract_screening",
        target_id="screen-1",
        source_suggestion_id="aisug-1",
        after={"decision": "include"},
    )

    assert draft.status == ResearchDecisionStatus.DRAFT.value
    assert suggestion.status == ResearchDecisionStatus.SUGGESTED.value
    assert not service.can_consume_confirmed(project_dir, target_type="final_pico", target_id="protocol-1")
    with pytest.raises(ValueError, match="research_decision_not_confirmed"):
        service.assert_can_consume_confirmed(project_dir, target_type="title_abstract_screening", target_id="screen-1")


def test_user_confirmations_write_before_after_source_suggestion_and_meta_audit(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    service = MetaResearchGovernanceService()

    event = service.record_user_confirmation(
        project_dir,
        action="confirm",
        actor="reviewer-a",
        target_type="final_search_strategy",
        target_id="pubmed-query",
        before={"query": "draft query"},
        after={"query": '"Obesity"[Mesh] AND "Cancer"[tiab]'},
        source_suggestion_id="aisug-search-1",
    )

    assert event.status == ResearchDecisionStatus.CONFIRMED.value
    assert event.actor == "reviewer-a"
    assert event.before["query"] == "draft query"
    assert event.after["query"].startswith('"Obesity"')
    assert event.source_suggestion_id == "aisug-search-1"
    assert event.created_at
    assert service.can_consume_confirmed(project_dir, target_type="final_search_strategy", target_id="pubmed-query")

    audit_events = MetaAuditLogService().list_events(project_dir)
    assert audit_events[-1].event_type == "research_governance_event"
    assert audit_events[-1].details["action"] == "confirm"
    assert audit_events[-1].details["status"] == "confirmed"


def test_accept_reject_edit_are_user_review_events_not_final_confirmation(tmp_path: Path) -> None:
    service = MetaResearchGovernanceService()
    project_dir = tmp_path / "project"

    accepted = service.record_user_confirmation(
        project_dir,
        action="accept",
        actor="reviewer",
        target_type="data_extraction_final",
        target_id="extract-1",
        before={"value": "suggested"},
        after={"value": "accepted"},
        source_suggestion_id="aisug-extract-1",
    )
    rejected = service.record_user_confirmation(
        project_dir,
        action="reject",
        actor="reviewer",
        target_type="quality_assessment_score",
        target_id="quality-1",
        before={"score": "low"},
        after={"score": ""},
        source_suggestion_id="aisug-quality-1",
    )
    edited = service.record_user_confirmation(
        project_dir,
        action="edit",
        actor="reviewer",
        target_type="discussion_conclusion",
        target_id="discussion-draft",
        before={"text": "overstated"},
        after={"text": "draft limitation wording"},
        source_suggestion_id="aisug-report-1",
    )

    assert accepted.status == ResearchDecisionStatus.USER_ACCEPTED.value
    assert rejected.status == ResearchDecisionStatus.USER_REJECTED.value
    assert edited.status == ResearchDecisionStatus.USER_EDITED.value
    assert not service.can_consume_confirmed(project_dir, target_type="data_extraction_final", target_id="extract-1")
    assert not service.can_consume_confirmed(project_dir, target_type="discussion_conclusion", target_id="discussion-draft")


def test_ai_suggestion_service_records_suggestion_and_reviewer_audit(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    ai_service = AISuggestionService()
    governance = MetaResearchGovernanceService()

    suggestion = ai_service.create_ai_suggestion(
        project_dir,
        project_id="meta-test",
        target_type="screening_decision",
        target_id="screen-1",
        suggestion_type="relevance_screening",
        suggested_value={"decision": "include"},
        rationale="Abstract appears relevant.",
        confidence=0.8,
    )
    ai_service.accept_ai_suggestion(project_dir, suggestion.suggestion_id)

    events = governance.list_events(project_dir)
    assert [event.action for event in events] == ["suggestion_created", "accept"]
    assert events[0].status == ResearchDecisionStatus.SUGGESTED.value
    assert events[1].status == ResearchDecisionStatus.USER_ACCEPTED.value
    assert events[1].source_suggestion_id == suggestion.suggestion_id
    assert events[1].before["status"] == "pending"
    assert events[1].after["status"] == "accepted"
    assert not governance.can_consume_confirmed(project_dir, target_type="screening_decision", target_id="screen-1")


def test_policy_lists_required_human_targets_and_autonomous_engineering_scopes() -> None:
    expected_targets = {
        "final_pico",
        "final_picos",
        "final_peco",
        "final_search_strategy",
        "literature_inclusion",
        "dedup_merge",
        "title_abstract_screening",
        "fulltext_screening",
        "data_extraction_final",
        "quality_assessment_score",
        "analysis_plan",
        "medical_interpretation",
        "discussion_conclusion",
    }
    expected_scopes = {
        "schema",
        "service",
        "adapter",
        "manifest",
        "audit",
        "ui_skeleton",
        "preview",
        "validation",
        "report_draft",
        "figure_output",
        "reproducibility_package",
        "boundary_tests",
    }

    assert expected_targets <= set(HUMAN_CONFIRMATION_TARGETS)
    assert expected_scopes <= set(AUTONOMOUS_ENGINEERING_SCOPES)
    assert all(requires_human_confirmation(target) for target in expected_targets)
    assert all(is_autonomous_engineering_scope(scope) for scope in expected_scopes)


def test_search_strategy_draft_writes_governance_draft_not_confirmed(tmp_path: Path) -> None:
    draft = MetaSearchStrategyDraft(
        original_question="肥胖是否增加甲状腺癌风险",
        target_context="meta_analysis",
        review_framework="PECO",
        review_or_analysis_intent="evidence_synthesis",
        concept_groups=(),
        query_drafts=(QueryDraft(database="pubmed", query='"Obesity"[Mesh]'),),
        local_model_status="not_available",
    )

    write_protocol_search_strategy_artifacts(tmp_path, draft)

    service = MetaResearchGovernanceService()
    latest = service.latest_event(
        tmp_path,
        target_type="final_search_strategy",
        target_id="multi_database_search_strategy",
    )
    assert latest is not None
    assert latest.status == "draft"
    assert not service.can_consume_confirmed(
        tmp_path,
        target_type="final_search_strategy",
        target_id="multi_database_search_strategy",
    )


def test_pubmed_execution_candidates_do_not_auto_import_screen_or_prisma(tmp_path: Path) -> None:
    execution = PubMedSearchExecution(
        success=True,
        query_used='"Obesity"[Mesh]',
        executed_at="2026-05-06T00:00:00+00:00",
        result_count=1,
        returned_count=1,
        records=(
            PubMedSearchResult(
                pmid="111",
                title="Candidate only",
                journal="Journal",
                year="2026",
                authors=("Reviewer",),
                abstract="Candidate abstract.",
                snippet="Candidate abstract.",
                url="https://pubmed.ncbi.nlm.nih.gov/111/",
                query_used='"Obesity"[Mesh]',
            ),
        ),
    )

    paths = write_pubmed_search_execution_artifacts(tmp_path, '"Obesity"[Mesh]', execution)
    report = json.loads(Path(paths["search_execution_report"]).read_text(encoding="utf-8"))
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)
    governance = MetaResearchGovernanceService()

    assert report["literature_import_status"] == "not_imported"
    assert report["screening_status"] == "not_started"
    assert report["auto_imported"] is False
    assert report["auto_screened"] is False
    assert not (tmp_path / "literature").exists()
    assert not (tmp_path / "screening").exists()
    assert prisma.records_identified == 0
    assert prisma.records_screened == 0
    assert prisma.studies_included == 0
    assert governance.can_consume_confirmed(tmp_path, target_type="final_search_strategy", target_id="pubmed_query")
