from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.workflow_integration_page import meta_workflow_integration_state_from_project
from app.meta_analysis.services.dedup_review_v2_service import DECISION_MARK_NOT_DUPLICATE, DECISION_MERGE, DedupReviewV2Service
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
from app.meta_analysis.services.multisource_literature_import_service import MultiSourceLiteratureImportService
from app.meta_analysis.services.title_abstract_screening_v2_service import TitleAbstractScreeningV2Service


def test_stage_m3_import_diagnostics_include_missing_fields_and_title_warnings(tmp_path: Path) -> None:
    source = tmp_path / "records.csv"
    source.write_text("title,authors,doi,abstract,year,journal\n??????,,,,,\nComplete,Alice,10.1000/m3,Abstract,2024,\n", encoding="utf-8")

    result = MultiSourceLiteratureImportService().import_file(tmp_path / "project", source_path=source, source_format="csv")
    diagnostics = json.loads(Path(result.diagnostics_path).read_text(encoding="utf-8"))

    assert result.success
    assert diagnostics["source_file_name"] == "records.csv"
    assert diagnostics["failed_record_count"] == 0
    assert diagnostics["warning_counts"]["缺少 DOI"] == 1
    assert diagnostics["warning_counts"]["缺少 PMID"] == 2
    assert diagnostics["warning_counts"]["缺少摘要"] == 1
    assert diagnostics["warning_counts"]["缺少年份"] == 1
    assert diagnostics["warning_counts"]["缺少期刊"] == 2
    assert diagnostics["title_abnormality_count"] == 1
    assert "field_mapping_warnings" in diagnostics


def test_stage_m3_dedup_merge_preserves_provenance_and_updates_prisma(tmp_path: Path) -> None:
    _seed_stage_m3_library(tmp_path)
    service = DedupReviewV2Service()
    queue = service.build_review_queue(tmp_path, project_id="stage-m3")
    group = next(item for item in queue.groups if item.duplicate_rule == "pmid_exact")

    service.save_decision(
        tmp_path,
        group_id=group.group_id,
        decision=DECISION_MERGE,
        actor="reviewer",
        selected_record_id="lit-a",
        merged_record=service.preview_merge(tmp_path, group_id=group.group_id, selected_record_id="lit-a"),
        note="same PMID",
    )
    deduplicated = service.generate_deduplicated_set(tmp_path, project_id="stage-m3")
    original_library = LiteratureLibraryService().list_records(tmp_path)
    manifest = LiteratureLibraryService().read_manifest(tmp_path)
    prisma = PRISMAService().collect_literature_acquisition_summary(tmp_path)

    assert len(original_library) == 3
    assert deduplicated["original_count"] == 3
    assert deduplicated["active_record_count"] == 2
    assert deduplicated["duplicate_records_removed"] == 1
    merged = next(record for record in deduplicated["records"] if record["record_id"].startswith("merged-"))
    assert merged["merged_from"] == list(group.record_ids)
    assert merged["user_decision"]["actor"] == "reviewer"
    assert manifest["deduplication"]["active_record_count"] == 2
    assert manifest["deduplication"]["original_records_retained"] is True
    assert prisma["records_identified_from_pubmed"] == 2
    assert prisma["records_identified_from_local_imports"] == 1
    assert prisma["total_records_before_deduplication"] == 3
    assert prisma["duplicate_records_removed"] == 1
    assert prisma["records_after_deduplication"] == 2
    assert prisma["deduplication_status"] == "completed"


def test_stage_m3_nonduplicate_decision_and_screening_queue_status(tmp_path: Path) -> None:
    _seed_stage_m3_library(tmp_path)
    service = DedupReviewV2Service()
    queue = service.build_review_queue(tmp_path, project_id="stage-m3")
    group = next(item for item in queue.groups if item.duplicate_rule == "pmid_exact")

    decision = service.save_decision(
        tmp_path,
        group_id=group.group_id,
        decision=DECISION_MARK_NOT_DUPLICATE,
        actor="reviewer",
        note="same PMID but reviewer keeps both in test fixture",
    )
    deduplicated = service.generate_deduplicated_set(tmp_path, project_id="stage-m3")
    queue_result = TitleAbstractScreeningV2Service().build_queue(tmp_path, project_id="stage-m3")
    statuses = {step.step_id: step for step in meta_workflow_integration_state_from_project(tmp_path).steps}
    prisma = PRISMAService().collect_literature_acquisition_summary(tmp_path)

    assert decision.decision == DECISION_MARK_NOT_DUPLICATE
    assert deduplicated["active_record_count"] == 3
    assert queue_result.record_count == 3
    assert prisma["records_ready_for_title_abstract_screening"] == 3
    assert statuses["screening"].status == "待筛选"
    assert "screening_queue=3" in statuses["screening"].artifact_summary


def _seed_stage_m3_library(project_dir: Path) -> None:
    LiteratureLibraryService().import_records(
        project_dir,
        project_id="stage-m3",
        source_type="pubmed_confirmed_candidates",
        source_name="PubMed",
        raw_records=[
            {
                "record_id": "lit-a",
                "title": "Obesity and thyroid cancer risk",
                "abstract": "Abstract A.",
                "authors": ["Alice Adams"],
                "journal": "Journal A",
                "year": "2024",
                "pmid": "111",
                "doi": "10.1000/a",
            },
            {
                "record_id": "lit-b",
                "title": "Obesity and thyroid cancer risk extended",
                "abstract": "Abstract B is longer.",
                "authors": ["Alice Adams", "Ben Baker"],
                "journal": "Journal A",
                "year": "2024",
                "pmid": "111",
                "doi": "10.1000/b",
            },
        ],
    )
    LiteratureLibraryService().import_records(
        project_dir,
        project_id="stage-m3",
        source_type="csv",
        source_name="CSV",
        raw_records=[
            {
                "record_id": "lit-c",
                "title": "Independent local import",
                "abstract": "Local abstract.",
                "authors": ["Carol Chen"],
                "journal": "Journal C",
                "year": "2023",
            }
        ],
    )
