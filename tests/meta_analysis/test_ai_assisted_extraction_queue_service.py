from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.models.ai_suggestion import AISuggestionStatus
from app.meta_analysis.pages.ai_suggestions_page import ai_extraction_suggestion_queue_state_from_project
from app.meta_analysis.services.ai_assisted_extraction_queue_service import (
    AI_EXTRACTION_QUEUE_SCHEMA_VERSION,
    AIAssistedExtractionQueueService,
)
from app.meta_analysis.services.extraction_schema_registry_v1_service import (
    BINARY_OUTCOME_META,
    DIAGNOSTIC_ACCURACY_META_V1,
    SURVIVAL_OUTCOME_META,
)
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.fulltext_parsing_service import FullTextParsingService
from app.meta_analysis.services.manual_extraction_effect_row_service import ManualExtractionEffectRowService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def test_ai_extraction_suggestion_created_as_pending_with_validation_and_disease_guard(tmp_path: Path) -> None:
    service = AIAssistedExtractionQueueService()

    result = service.create_suggestion_from_text(
        tmp_path,
        project_id="meta-ai-extraction",
        record_id="rec-1",
        text="Obesity thyroid cancer response 60 20 60 10 table 2",
        schema_meta_type=BINARY_OUTCOME_META,
        research_question="肥胖与甲状腺癌风险",
    )
    suggestion = service.list_extraction_suggestions(tmp_path)[0]
    queue = json.loads(service.queue_path(tmp_path).read_text(encoding="utf-8"))
    validation = json.loads(service.validation_path(tmp_path).read_text(encoding="utf-8"))

    assert result.success is True
    assert suggestion.status == AISuggestionStatus.PENDING.value
    assert suggestion.target_type == "extraction_effect_row"
    assert suggestion.suggestion_type == "extraction_effect_row_suggestion"
    assert queue["schema_version"] == AI_EXTRACTION_QUEUE_SCHEMA_VERSION
    assert queue["pending_count"] == 1
    assert validation["validations"][0]["validation"]["status"] == "valid"
    assert result.diagnostics["disease_guard"]["target_context"] == "meta_analysis"
    assert not (tmp_path / "extraction" / "extraction_effect_rows.json").exists()


def test_ai_extraction_pending_rejected_and_edited_suggestions_do_not_write_extraction(tmp_path: Path) -> None:
    service = AIAssistedExtractionQueueService()
    pending = service.create_suggestion_from_text(
        tmp_path,
        record_id="rec-1",
        text="Response 60 20 60 10",
        schema_meta_type=BINARY_OUTCOME_META,
    ).suggestion
    assert pending is not None

    pending_apply = service.apply_accepted_suggestion_as_draft(tmp_path, suggestion_id=pending.suggestion_id)
    rejected = service.reject_suggestion(tmp_path, pending.suggestion_id)
    rejected_apply = service.apply_accepted_suggestion_as_draft(tmp_path, suggestion_id=pending.suggestion_id)
    edited_seed = service.create_suggestion_from_text(
        tmp_path,
        record_id="rec-2",
        text="Overall survival 0.72 0.55 0.94",
        schema_meta_type=SURVIVAL_OUTCOME_META,
    ).suggestion
    assert edited_seed is not None
    edited = service.edit_suggestion(
        tmp_path,
        edited_seed.suggestion_id,
        edited_effect_row_draft={
            "record_id": "rec-2",
            "schema_meta_type": SURVIVAL_OUTCOME_META,
            "data_input_mode": "reported_effect_size",
            "outcome_name": "Overall survival",
            "data_fields": {"effect_measure": "HR", "effect_value": 0.7, "ci_low": 0.5, "ci_high": 0.9},
        },
    )
    edited_apply = service.apply_accepted_suggestion_as_draft(tmp_path, suggestion_id=edited_seed.suggestion_id)

    assert pending_apply.success is False
    assert rejected.success is True
    assert rejected_apply.success is False
    assert edited.status == AISuggestionStatus.EDITED.value
    assert edited_apply.success is False
    assert not (tmp_path / "extraction" / "extraction_effect_rows.json").exists()


def test_accepted_ai_extraction_suggestion_applies_only_as_manual_draft(tmp_path: Path) -> None:
    governance = MetaResearchGovernanceService()
    manual = ManualExtractionEffectRowService(research_governance=governance)
    service = AIAssistedExtractionQueueService(manual_extraction=manual, research_governance=governance)
    suggestion = service.create_suggestion_from_text(
        tmp_path,
        record_id="rec-1",
        text="Response 60 20 60 10",
        schema_meta_type=BINARY_OUTCOME_META,
    ).suggestion
    assert suggestion is not None

    service.accept_suggestion(tmp_path, suggestion.suggestion_id)
    applied = service.apply_accepted_suggestion_as_draft(tmp_path, suggestion_id=suggestion.suggestion_id, actor="reviewer")
    effect_rows = manual.load_effect_rows(tmp_path)
    applications = json.loads(service.application_path(tmp_path).read_text(encoding="utf-8"))["applications"]
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)
    governance_events = governance.list_events(tmp_path)

    assert applied.success is True
    assert len(effect_rows) == 1
    assert effect_rows[0]["effect_row_id"] == applied.effect_row_id
    assert effect_rows[0]["extraction_status"] == "draft"
    assert effect_rows[0]["analysis_ready"] is False
    assert effect_rows[0]["source_suggestion_id"] == suggestion.suggestion_id
    assert applications[0]["analysis_ready_dataset_created"] is False
    assert not (tmp_path / "analysis" / "analysis_ready_datasets.json").exists()
    assert not (tmp_path / "analysis" / "analysis_results.json").exists()
    assert prisma.records_screened == 0
    assert prisma.studies_included == 0
    assert any(event.source_suggestion_id == suggestion.suggestion_id and event.target_type == "extraction_effect_row" for event in governance_events)


def test_ai_extraction_suggestion_supports_diagnostic_2x2_schema(tmp_path: Path) -> None:
    service = AIAssistedExtractionQueueService()

    result = service.create_suggestion_from_text(
        tmp_path,
        record_id="rec-dx",
        text="Diagnostic accuracy sensitivity specificity 42 5 8 45",
        schema_meta_type=DIAGNOSTIC_ACCURACY_META_V1,
    )
    value = result.suggestion.suggested_value if result.suggestion is not None else {}
    draft = value["effect_row_draft"]

    assert result.diagnostics["schema_validation"]["status"] == "valid"
    assert draft["data_fields"] == {"tp": 42, "fp": 5, "fn": 8, "tn": 45}


def test_ai_extraction_can_create_suggestion_from_parsed_fulltext_text(tmp_path: Path) -> None:
    parser = FullTextParsingService()
    parser.extracted_text_dir(tmp_path).mkdir(parents=True)
    text_path = parser.extracted_text_dir(tmp_path) / "rec-1.txt"
    text_path.write_text("Response 60 20 60 10", encoding="utf-8")
    parser.result_path(tmp_path, "rec-1").parent.mkdir(parents=True)
    parser.result_path(tmp_path, "rec-1").write_text(
        json.dumps({"record_id": "rec-1", "extracted_text_path": "fulltext/extracted_text/rec-1.txt"}),
        encoding="utf-8",
    )
    service = AIAssistedExtractionQueueService(fulltext_parsing=parser)

    result = service.create_suggestion_from_parsed_fulltext(tmp_path, record_id="rec-1", schema_meta_type=BINARY_OUTCOME_META)

    assert result.success is True
    assert result.suggestion_id


def test_ai_extraction_queue_page_state_exposes_review_actions(tmp_path: Path) -> None:
    service = AIAssistedExtractionQueueService()
    service.create_suggestion_from_text(
        tmp_path,
        record_id="rec-1",
        text="Response 60 20 60 10",
        schema_meta_type=BINARY_OUTCOME_META,
    )

    state = ai_extraction_suggestion_queue_state_from_project(tmp_path, service=service)

    assert state.queue_schema_version == AI_EXTRACTION_QUEUE_SCHEMA_VERSION
    assert state.suggestion_count == 1
    assert state.pending_count == 1
    assert "apply_accepted_as_manual_draft" in state.review_actions
    assert any("No analysis-ready dataset" in rule for rule in state.safety_rules)
