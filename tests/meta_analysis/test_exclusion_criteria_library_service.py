from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.criteria_page import criteria_page_state_from_project
from app.meta_analysis.pages.screening_page import title_abstract_screening_v2_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.exclusion_criteria_library_service import (
    EXCLUSION_CRITERIA_LIBRARY_SCHEMA_VERSION,
    FULL_TEXT_STAGE,
    TITLE_ABSTRACT_STAGE,
    ExclusionCriteriaLibraryService,
)
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def test_exclusion_criteria_library_writes_default_reasons_and_prisma_map(tmp_path: Path) -> None:
    service = ExclusionCriteriaLibraryService()

    library = service.save_library(tmp_path, actor="reviewer", confirm=False)
    payload = json.loads(service.library_path(tmp_path).read_text(encoding="utf-8"))
    prisma_map = json.loads(service.prisma_reason_map_path(tmp_path).read_text(encoding="utf-8"))
    governance = MetaResearchGovernanceService().list_events(tmp_path)

    assert library.schema_version == EXCLUSION_CRITERIA_LIBRARY_SCHEMA_VERSION
    assert library.status == "draft_needs_review"
    assert payload["enabled_reason_count"] >= 20
    assert "wrong_population" in {reason["code"] for reason in payload["reasons"]}
    assert prisma_map["mappings"]["wrong_population"] == "wrong_population"
    assert any(event.action == "draft_created" and event.target_type == "exclusion_criteria_library" for event in governance)


def test_exclusion_criteria_library_can_select_and_confirm_reason_set(tmp_path: Path) -> None:
    service = ExclusionCriteriaLibraryService()

    library = service.save_library(
        tmp_path,
        selected_reason_codes=("wrong_population", "wrong_outcome", "animal_study"),
        actor="reviewer-a",
        confirm=True,
    )
    enabled = {reason.code for reason in service.list_reasons(tmp_path)}
    governance = MetaResearchGovernanceService().list_events(tmp_path)
    audit_events = MetaAuditLogService().list_events(tmp_path)

    assert library.status == "confirmed"
    assert enabled == {"wrong_population", "wrong_outcome", "animal_study"}
    assert any(event.action == "confirm" and event.status == "confirmed" for event in governance)
    assert any(event.event_type == "record_saved" and event.target_type == "exclusion_criteria_library" for event in audit_events)


def test_exclusion_criteria_library_adds_custom_reason_and_validates_stage(tmp_path: Path) -> None:
    service = ExclusionCriteriaLibraryService()
    service.save_library(tmp_path, selected_reason_codes=("wrong_population",), actor="reviewer", confirm=False)

    library = service.add_custom_reason(
        tmp_path,
        english_label="Wrong dose range",
        chinese_label="剂量范围不符",
        prisma_reason="wrong_intervention_or_exposure",
        applies_to_stage=(FULL_TEXT_STAGE,),
        actor="reviewer",
    )
    full_text_ok, full_text_message = service.validate_reason(tmp_path, reason_code="wrong_dose_range", stage=FULL_TEXT_STAGE)
    title_ok, title_message = service.validate_reason(tmp_path, reason_code="wrong_dose_range", stage=TITLE_ABSTRACT_STAGE)

    assert any(reason.custom and reason.code == "wrong_dose_range" for reason in library.reasons)
    assert full_text_ok
    assert full_text_message == ""
    assert not title_ok
    assert title_message == "exclusion_reason_not_available_for_stage"


def test_exclusion_criteria_library_counts_prisma_reasons_from_real_decisions(tmp_path: Path) -> None:
    service = ExclusionCriteriaLibraryService()
    service.save_library(tmp_path, actor="reviewer", confirm=True)

    counts = service.count_prisma_reasons(
        tmp_path,
        [
            {"record_id": "rec-1", "decision": "exclude", "exclusion_reason_code": "wrong_population"},
            {"record_id": "rec-2", "decision": "excluded", "exclusion_reason_text": "Wrong outcome"},
            {"record_id": "rec-3", "decision": "include", "exclusion_reason_code": "animal_study"},
        ],
        stage=TITLE_ABSTRACT_STAGE,
    )

    assert counts == {"wrong_population": 1, "wrong_outcome": 1}


def test_exclusion_criteria_library_surfaces_in_criteria_and_screening_states(tmp_path: Path) -> None:
    service = ExclusionCriteriaLibraryService()
    service.save_library(tmp_path, selected_reason_codes=("wrong_population", "wrong_outcome"), actor="reviewer", confirm=True)
    (tmp_path / "screening").mkdir(parents=True)
    (tmp_path / "screening" / "title_abstract_queue_v2.json").write_text(
        json.dumps(
            {
                "schema_version": "meta_title_abstract_screening_queue.v2",
                "project_id": tmp_path.name,
                "source_type": "fixture",
                "queue_records": [{"record_id": "lit-1", "title": "Study", "decision": "not_screened"}],
            }
        ),
        encoding="utf-8",
    )

    criteria_state = criteria_page_state_from_project(tmp_path, exclusion_library_service=service)
    screening_state = title_abstract_screening_v2_state_from_project(tmp_path, exclusion_library_service=service)

    assert criteria_state.exclusion_library_status == "confirmed"
    assert criteria_state.exclusion_library_enabled_count == 2
    assert criteria_state.prisma_reason_map_path.endswith("criteria/prisma_reason_map_v1.json")
    assert {"研究对象不符合", "结局不符合", "其他"} <= set(screening_state.exclusion_reason_options)
