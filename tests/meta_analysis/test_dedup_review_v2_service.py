from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.duplicate_review_page import duplicate_review_v2_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.dedup_review_v2_service import (
    DEDUPLICATED_SET_SCHEMA_VERSION,
    DEDUP_DECISION_LOG_SCHEMA_VERSION,
    DUPLICATE_REVIEW_QUEUE_SCHEMA_VERSION,
    DECISION_MARK_NOT_DUPLICATE,
    DECISION_MERGE,
    RISK_GRAY,
    RISK_RED,
    DedupReviewV2Service,
)
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def test_dedup_review_v2_builds_duplicate_groups_with_risk_levels(tmp_path: Path) -> None:
    _seed_library(tmp_path)

    result = DedupReviewV2Service().build_review_queue(tmp_path, project_id="meta-dedup")
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    groups = {group["duplicate_rule"]: group for group in payload["duplicate_groups"]}

    assert payload["schema_version"] == DUPLICATE_REVIEW_QUEUE_SCHEMA_VERSION
    assert payload["auto_deleted"] is False
    assert payload["auto_merged"] is False
    assert result.group_count >= 4
    assert groups["pmid_exact"]["risk_level"] == RISK_RED
    assert groups["doi_exact_or_variant"]["risk_level"] == RISK_RED
    assert groups["title_normalized_exact"]["risk_level"] == RISK_RED
    assert groups["title_fuzzy_journal_author"]["risk_level"] == RISK_GRAY
    assert groups["pmid_exact"]["merge_preview"]["auto_merged"] is False
    assert groups["pmid_exact"]["retain_candidate_id"]
    assert groups["pmid_exact"]["field_differences"]


def test_dedup_review_v2_merge_decision_writes_audit_without_changing_library(tmp_path: Path) -> None:
    _seed_library(tmp_path)
    service = DedupReviewV2Service()
    result = service.build_review_queue(tmp_path, project_id="meta-dedup")
    group = next(item for item in result.groups if item.duplicate_rule == "pmid_exact")
    before_records = LiteratureLibraryService().list_records(tmp_path)

    preview = service.preview_merge(tmp_path, group_id=group.group_id)
    decision = service.save_decision(
        tmp_path,
        group_id=group.group_id,
        decision=DECISION_MERGE,
        actor="reviewer",
        merged_record=preview,
        note="Reviewer confirmed same PMID duplicate.",
    )
    after_records = LiteratureLibraryService().list_records(tmp_path)
    decisions_payload = json.loads(service.decisions_path(tmp_path).read_text(encoding="utf-8"))
    governance_events = MetaResearchGovernanceService().list_events(tmp_path)
    audit_events = MetaAuditLogService().list_events(tmp_path)

    assert decision.decision == DECISION_MERGE
    assert decisions_payload["schema_version"] == DEDUP_DECISION_LOG_SCHEMA_VERSION
    assert decisions_payload["auto_deleted"] is False
    assert decisions_payload["auto_merged"] is False
    assert len(after_records) == len(before_records)
    assert [record["record_id"] for record in after_records] == [record["record_id"] for record in before_records]
    assert any(event.target_type == "dedup_merge" and event.status == "confirmed" for event in governance_events)
    assert any(event.event_type == "duplicate_decision" and event.target_id == group.group_id for event in audit_events)


def test_dedup_review_v2_can_mark_not_duplicate_and_generate_separate_deduplicated_set(tmp_path: Path) -> None:
    _seed_library(tmp_path)
    service = DedupReviewV2Service()
    result = service.build_review_queue(tmp_path, project_id="meta-dedup")
    fuzzy_group = next(item for item in result.groups if item.duplicate_rule == "title_fuzzy_journal_author")

    service.save_decision(
        tmp_path,
        group_id=fuzzy_group.group_id,
        decision=DECISION_MARK_NOT_DUPLICATE,
        actor="reviewer",
        note="Similar title but reviewer keeps both.",
    )
    deduplicated = service.generate_deduplicated_set(tmp_path, project_id="meta-dedup")

    assert deduplicated["schema_version"] == DEDUPLICATED_SET_SCHEMA_VERSION
    assert deduplicated["auto_deleted"] is False
    assert deduplicated["auto_merged"] is False
    assert deduplicated["screening_status"] == "not_started"
    assert fuzzy_group.group_id not in deduplicated["unresolved_group_ids"]
    assert LiteratureLibraryService().get_record(tmp_path, "lit-pmid-111") is not None


def test_dedup_review_v2_ui_state_summarizes_groups_and_does_not_enable_auto_actions(tmp_path: Path) -> None:
    _seed_library(tmp_path)

    state = duplicate_review_v2_state_from_project(tmp_path)

    assert state.duplicate_group_count >= 4
    assert state.v2_schema_version == DUPLICATE_REVIEW_QUEUE_SCHEMA_VERSION
    assert state.auto_delete_enabled is False
    assert state.auto_merge_enabled is False
    assert state.risk_level_counts[RISK_RED] >= 3
    assert "merge" in state.interactive_decision_options
    assert "不自动删除" in state.output_summary


def test_dedup_review_v2_does_not_create_screening_or_advance_prisma(tmp_path: Path) -> None:
    _seed_library(tmp_path)

    DedupReviewV2Service().build_review_queue(tmp_path, project_id="meta-dedup")
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)

    assert not (tmp_path / "screening").exists()
    assert prisma.records_screened == 0
    assert prisma.records_excluded_title_abstract == 0
    assert prisma.full_text_reports_assessed == 0
    assert prisma.studies_included == 0


def _seed_library(project_dir: Path) -> None:
    LiteratureLibraryService().import_records(
        project_dir,
        project_id="meta-dedup",
        source_type="test_fixture",
        source_name="Test Fixture",
        raw_records=[
            {
                "record_id": "lit-pmid-111",
                "title": "PMID duplicate alpha",
                "abstract": "Short abstract.",
                "authors": ["Alice Adams"],
                "first_author": "Alice Adams",
                "journal": "Journal A",
                "year": "2024",
                "pmid": "111",
            },
            {
                "record_id": "lit-pmid-111-b",
                "title": "PMID duplicate alpha extended title",
                "abstract": "Longer abstract for the same PMID.",
                "authors": ["Alice Adams", "Ben Baker"],
                "first_author": "Alice Adams",
                "journal": "Journal A",
                "year": "2024",
                "pmid": "111",
            },
            {
                "record_id": "lit-doi-a",
                "title": "DOI duplicate trial A",
                "authors": ["Carol Chen"],
                "first_author": "Carol Chen",
                "journal": "Journal B",
                "year": "2022",
                "doi": "https://doi.org/10.1000/demo.001",
            },
            {
                "record_id": "lit-doi-b",
                "title": "DOI duplicate trial B",
                "authors": ["Carol Chen"],
                "first_author": "Carol Chen",
                "journal": "Journal B",
                "year": "2022",
                "doi": "doi:10.1000/demo.001",
            },
            {
                "record_id": "lit-title-a",
                "title": "Exact Normalized Duplicate Title",
                "authors": ["Dana Doe"],
                "first_author": "Dana Doe",
                "journal": "Journal C",
                "year": "2021",
            },
            {
                "record_id": "lit-title-b",
                "title": "Exact normalized duplicate title!",
                "authors": ["Different Author"],
                "first_author": "Different Author",
                "journal": "Journal D",
                "year": "2020",
            },
            {
                "record_id": "lit-fuzzy-a",
                "title": "Obesity and thyroid cancer risk in adults",
                "authors": ["Eva Evans"],
                "first_author": "Eva Evans",
                "journal": "Journal E",
                "year": "2019",
            },
            {
                "record_id": "lit-fuzzy-b",
                "title": "Obesity thyroid cancer risks among adults",
                "authors": ["Eva Evans"],
                "first_author": "Eva Evans",
                "journal": "Journal E",
                "year": "2020",
            },
        ],
    )
