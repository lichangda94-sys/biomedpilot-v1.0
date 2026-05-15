from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.meta_analysis.pages.screening_page import title_abstract_screening_v2_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.dedup_review_v2_service import DEDUPLICATED_SET_SCHEMA_VERSION, DedupReviewV2Service
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService
from app.meta_analysis.services.title_abstract_screening_v2_service import (
    DECISION_EXCLUDE,
    DECISION_INCLUDE,
    DECISION_NEED_FULL_TEXT,
    DECISION_NOT_SCREENED,
    DECISION_UNCERTAIN,
    EXCLUSION_REASON_LABELS_ZH,
    TITLE_ABSTRACT_SCREENING_DECISION_LOG_SCHEMA_VERSION,
    TITLE_ABSTRACT_SCREENING_QUEUE_SCHEMA_VERSION,
    TitleAbstractScreeningV2Service,
)


def test_screening_v2_builds_queue_from_deduplicated_set_without_decisions_or_prisma(tmp_path: Path) -> None:
    _seed_library(tmp_path)
    deduplicated_path = DedupReviewV2Service().deduplicated_set_path(tmp_path)
    deduplicated_path.parent.mkdir(parents=True, exist_ok=True)
    deduplicated_path.write_text(
        json.dumps(
            {
                "schema_version": DEDUPLICATED_SET_SCHEMA_VERSION,
                "project_id": "meta-screening-v2",
                "records": [
                    {"record_id": "lit-1", "title": "Eligible trial", "abstract": "Adult study", "authors": ["Alice"], "journal": "J A", "year": "2024", "pmid": "111"},
                    {"record_id": "lit-2", "title": "Animal study", "abstract": "Mouse study", "authors": ["Ben"], "journal": "J B", "year": "2023"},
                ],
                "screening_status": "not_started",
            }
        ),
        encoding="utf-8",
    )

    result = TitleAbstractScreeningV2Service().build_queue(tmp_path, project_id="meta-screening-v2")
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)

    assert result.success
    assert result.source_type == "deduplicated_literature_v2"
    assert payload["schema_version"] == TITLE_ABSTRACT_SCREENING_QUEUE_SCHEMA_VERSION
    assert payload["status"] == "preview_needs_reviewer_decision"
    assert payload["auto_screening_enabled"] is False
    assert payload["auto_prisma_update"] is False
    assert payload["queue_records"][0]["decision"] == "not_screened"
    assert "screening_records" not in payload
    assert not (tmp_path / "screening" / "screening_decisions.json").exists()
    assert prisma.records_screened == 0
    assert prisma.records_excluded_title_abstract == 0
    assert prisma.studies_included == 0


def test_screening_v2_falls_back_to_literature_library_and_ui_state(tmp_path: Path) -> None:
    _seed_library(tmp_path)

    result = TitleAbstractScreeningV2Service().build_queue(tmp_path, project_id="meta-screening-v2")
    state = title_abstract_screening_v2_state_from_project(tmp_path)

    assert result.source_type == "literature_library_v2"
    assert "deduplicated_set_missing_using_literature_library" in result.warnings
    assert state.schema_version == TITLE_ABSTRACT_SCREENING_QUEUE_SCHEMA_VERSION
    assert state.total_records == 3
    assert state.decision_counts["not_screened"] == 3
    assert state.decision_option_labels_zh == ("未筛选", "纳入", "排除", "不确定", "需要全文", "重置为未筛选")
    assert {"研究对象不符合", "干预/暴露不符合", "结局不符合", "全文不可获取", "其他"} <= set(state.exclusion_reason_options)
    assert state.prisma_summary_lines_zh[0] == "导入文献数：3"
    assert state.next_step == "下一步：全文管理"
    assert "生成队列不是筛选决定" in state.testing_limitations[0]


def test_screening_v2_saves_reviewer_decisions_with_governance_and_compatible_prisma_source(tmp_path: Path) -> None:
    _seed_library(tmp_path)
    service = TitleAbstractScreeningV2Service()
    service.build_queue(tmp_path, project_id="meta-screening-v2")

    include_result = service.save_decision(
        tmp_path,
        record_id="lit-1",
        decision=DECISION_INCLUDE,
        actor="reviewer-a",
        notes="Relevant adult study.",
    )
    exclude_result = service.save_decision(
        tmp_path,
        record_id="lit-2",
        decision=DECISION_EXCLUDE,
        actor="reviewer-a",
        exclusion_reason_code="population_mismatch",
        exclusion_reason_text="Animal study.",
    )
    uncertain_result = service.save_decision(
        tmp_path,
        record_id="lit-3",
        decision=DECISION_NEED_FULL_TEXT,
        actor="reviewer-a",
    )
    decisions_payload = json.loads(Path(include_result.decisions_path).read_text(encoding="utf-8"))
    compatible = json.loads(Path(include_result.compatible_decisions_path).read_text(encoding="utf-8"))
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)
    summary = service.screening_summary(tmp_path)
    governance_events = MetaResearchGovernanceService().list_events(tmp_path)
    audit_events = MetaAuditLogService().list_events(tmp_path)

    assert include_result.success
    assert exclude_result.success
    assert uncertain_result.success
    assert decisions_payload["schema_version"] == TITLE_ABSTRACT_SCREENING_DECISION_LOG_SCHEMA_VERSION
    assert decisions_payload["decision_counts"]["include"] == 1
    assert decisions_payload["decision_counts"]["exclude"] == 1
    assert decisions_payload["decision_counts"]["need_full_text"] == 1
    assert decisions_payload["screening_records"][1]["exclusion_reason_text"] == "研究对象不符合"
    assert decisions_payload["screening_records"][0]["evidence_state"] == "confirmed"
    assert compatible["screening_records"][0]["decision"] == "included"
    assert compatible["screening_records"][1]["decision"] == "excluded"
    assert compatible["screening_records"][2]["decision"] == "maybe"
    assert prisma.records_screened == 3
    assert prisma.records_excluded_title_abstract == 1
    assert prisma.full_text_reports_sought == 2
    assert prisma.studies_included == 1
    assert summary.imported_total == 3
    assert summary.after_dedup_total == 3
    assert summary.title_abstract_included == 1
    assert summary.title_abstract_excluded == 1
    assert summary.full_text_needed == 2
    assert any(event.target_type == "title_abstract_screening" and event.status == "confirmed" for event in governance_events)
    assert any(event.event_type == "screening_decision" and event.target_type == "title_abstract_screening" for event in audit_events)


def test_screening_v2_exclude_requires_reason_and_missing_actor_fails(tmp_path: Path) -> None:
    _seed_library(tmp_path)
    service = TitleAbstractScreeningV2Service()
    service.build_queue(tmp_path, project_id="meta-screening-v2")

    no_reason = service.save_decision(tmp_path, record_id="lit-1", decision=DECISION_EXCLUDE, actor="reviewer-a")
    bad_reason = service.save_decision(tmp_path, record_id="lit-1", decision=DECISION_EXCLUDE, actor="reviewer-a", exclusion_reason_code="unsupported_reason")
    no_actor = service.save_decision(tmp_path, record_id="lit-1", decision=DECISION_INCLUDE, actor="")

    assert not no_reason.success
    assert "exclusion reason" in no_reason.message
    assert not bad_reason.success
    assert "unsupported exclusion reason" in bad_reason.message
    assert not no_actor.success
    assert "actor" in no_actor.message
    assert not (tmp_path / "screening" / "screening_decisions.json").exists()


def test_screening_v2_ai_suggestion_does_not_write_final_decision_or_prisma(tmp_path: Path) -> None:
    _seed_library(tmp_path)
    service = TitleAbstractScreeningV2Service()
    service.build_queue(tmp_path, project_id="meta-screening-v2")

    suggestion = service.create_screening_suggestion(
        tmp_path,
        record_id="lit-1",
        suggested_decision=DECISION_INCLUDE,
        rationale="The abstract appears relevant.",
        confidence=0.75,
    )
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)
    governance = MetaResearchGovernanceService().list_events(tmp_path)

    assert suggestion["status"] == "suggested_include"
    assert suggestion["evidence_state"] == "suggested"
    assert suggestion["writes_final_decision"] is False
    assert (tmp_path / "ai" / "ai_suggestions.json").exists()
    assert (tmp_path / "screening" / "title_abstract_ai_suggestions_v2.json").exists()
    assert not (tmp_path / "screening" / "screening_decisions.json").exists()
    assert prisma.records_screened == 0
    assert any(event.action == "suggestion_created" and event.target_type == "screening_decision" for event in governance)
    assert not MetaResearchGovernanceService().can_consume_confirmed(tmp_path, target_type="screening_decision", target_id="lit-1")


def test_screening_v2_accepts_suggestion_only_after_user_action_and_can_reset(tmp_path: Path) -> None:
    _seed_library(tmp_path)
    service = TitleAbstractScreeningV2Service()
    service.build_queue(tmp_path, project_id="meta-screening-v2")
    suggestion = service.create_screening_suggestion(
        tmp_path,
        record_id="lit-1",
        suggested_decision=DECISION_NEED_FULL_TEXT,
        rationale="Needs the full paper to decide.",
        confidence=0.62,
    )

    accepted = service.save_decision(
        tmp_path,
        record_id="lit-1",
        decision=DECISION_NEED_FULL_TEXT,
        actor="reviewer-a",
        source_suggestion_id=suggestion["suggestion_id"],
    )
    payload = json.loads(Path(accepted.decisions_path).read_text(encoding="utf-8"))
    governance = MetaResearchGovernanceService().latest_event(tmp_path, target_type="title_abstract_screening", target_id="lit-1")

    assert suggestion["status"] == "suggested_need_full_text"
    assert accepted.success
    assert payload["screening_records"][0]["decision"] == DECISION_NEED_FULL_TEXT
    assert payload["screening_records"][0]["evidence_state"] == "user_accepted"
    assert governance is not None
    assert governance.status == "user_accepted"
    assert service.screening_summary(tmp_path).full_text_needed == 1

    reset = service.save_decision(tmp_path, record_id="lit-1", decision=DECISION_NOT_SCREENED, actor="reviewer-a")
    reset_payload = json.loads(Path(reset.decisions_path).read_text(encoding="utf-8"))

    assert reset.success
    assert reset_payload["screening_records"] == []
    assert service.screening_summary(tmp_path).title_abstract_unscreened == 3


def test_screening_v2_required_exclusion_reason_labels_are_available() -> None:
    assert EXCLUSION_REASON_LABELS_ZH == {
        "population_mismatch": "研究对象不符合",
        "intervention_or_exposure_mismatch": "干预/暴露不符合",
        "comparator_mismatch": "对照不符合",
        "outcome_mismatch": "结局不符合",
        "study_type_mismatch": "研究类型不符合",
        "duplicate": "重复文献",
        "non_original_research": "非原始研究",
        "full_text_unavailable": "全文不可获取",
        "language_or_access_issue": "语言或获取限制",
        "other": "其他",
    }


def test_screening_v2_rejects_unknown_decision(tmp_path: Path) -> None:
    _seed_library(tmp_path)
    service = TitleAbstractScreeningV2Service()
    service.build_queue(tmp_path, project_id="meta-screening-v2")

    with pytest.raises(ValueError, match="unsupported_title_abstract_screening_decision"):
        service.save_decision(tmp_path, record_id="lit-1", decision="auto_include", actor="reviewer")


def _seed_library(project_dir: Path) -> None:
    LiteratureLibraryService().import_records(
        project_dir,
        project_id="meta-screening-v2",
        source_type="test_fixture",
        source_name="Test Fixture",
        raw_records=[
            {
                "record_id": "lit-1",
                "title": "Eligible trial",
                "abstract": "Adult participants with the target disease.",
                "authors": ["Alice Adams"],
                "journal": "Journal A",
                "year": "2024",
                "pmid": "111",
            },
            {
                "record_id": "lit-2",
                "title": "Animal study",
                "abstract": "Mouse model only.",
                "authors": ["Ben Baker"],
                "journal": "Journal B",
                "year": "2023",
                "doi": "10.1000/animal",
            },
            {
                "record_id": "lit-3",
                "title": "Unclear abstract",
                "abstract": "Eligibility unclear from abstract.",
                "authors": ["Carol Chen"],
                "journal": "Journal C",
                "year": "2022",
            },
        ],
    )
