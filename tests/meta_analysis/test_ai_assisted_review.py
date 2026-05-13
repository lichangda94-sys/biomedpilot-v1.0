from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.models.ai_suggestion import AISuggestionStatus
from app.meta_analysis.pages.ai_suggestions_page import initial_ai_suggestions_state
from app.meta_analysis.services.ai_suggestion_service import AISuggestionService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def make_service(tmp_path: Path) -> tuple[AISuggestionService, TaskCenter, DataCenter, Path]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = AISuggestionService(task_center=task_center, data_center=data_center)
    return service, task_center, data_center, tmp_path / "project"


def test_suggestion_creation_defaults_to_pending_and_registers_data_task(tmp_path: Path) -> None:
    service, task_center, data_center, project_dir = make_service(tmp_path)

    suggestion = service.create_ai_suggestion(
        project_dir,
        project_id="meta-test",
        target_type="screening_decision",
        target_id="screen-1",
        suggestion_type="relevance_screening",
        suggested_value={"decision": "include"},
        rationale="Title appears relevant.",
        confidence=0.7,
    )

    assert suggestion.status == AISuggestionStatus.PENDING.value
    assert service.list_ai_suggestions(project_dir)[0].suggestion_id == suggestion.suggestion_id
    assert "ai_suggestions" in {asset.data_type for asset in data_center.list_assets("meta-test")}
    assert TaskType.AI_SUGGESTION_CREATE in {task.task_type for task in task_center.list_tasks()}


def test_pending_rejected_and_edited_suggestions_do_not_apply(tmp_path: Path) -> None:
    service, task_center, _data_center, project_dir = make_service(tmp_path)
    pending = create_screening_suggestion(service, project_dir)

    pending_apply = service.apply_accepted_suggestion(project_dir, pending.suggestion_id)
    rejected = service.reject_ai_suggestion(project_dir, pending.suggestion_id)
    rejected_apply = service.apply_accepted_suggestion(project_dir, pending.suggestion_id)
    edited_suggestion = create_screening_suggestion(service, project_dir)
    edited = service.edit_ai_suggestion(project_dir, edited_suggestion.suggestion_id, suggested_value={"decision": "maybe"})
    edited_apply = service.apply_accepted_suggestion(project_dir, edited_suggestion.suggestion_id)

    assert not pending_apply.success
    assert rejected.success
    assert not rejected_apply.success
    assert edited.status == AISuggestionStatus.EDITED.value
    assert not edited_apply.success
    assert not (project_dir / "ai" / "applied_suggestions.json").exists()
    assert TaskType.AI_SUGGESTION_REJECT in {task.task_type for task in task_center.list_tasks()}
    assert TaskType.AI_SUGGESTION_EDIT in {task.task_type for task in task_center.list_tasks()}


def test_accepted_but_not_applied_does_not_enter_target_until_apply(tmp_path: Path) -> None:
    service, task_center, _data_center, project_dir = make_service(tmp_path)
    seed_formal_artifacts(project_dir)
    original_extraction = (project_dir / "extraction" / "extraction_records.json").read_text(encoding="utf-8")
    suggestion = create_screening_suggestion(service, project_dir)

    accepted = service.accept_ai_suggestion(project_dir, suggestion.suggestion_id)

    assert accepted.success
    assert not (project_dir / "ai" / "applied_suggestions.json").exists()
    assert (project_dir / "extraction" / "extraction_records.json").read_text(encoding="utf-8") == original_extraction
    applied = service.apply_accepted_suggestion(project_dir, suggestion.suggestion_id)
    applications = json.loads(Path(applied.output_path).read_text(encoding="utf-8"))["applications"]
    assert applied.success
    assert applications[0]["suggestion_id"] == suggestion.suggestion_id
    assert "formal screening/extraction/analysis artifacts are not overwritten" in applications[0]["safety_note"]
    assert (project_dir / "extraction" / "extraction_records.json").read_text(encoding="utf-8") == original_extraction
    assert TaskType.AI_SUGGESTION_ACCEPT in {task.task_type for task in task_center.list_tasks()}
    assert TaskType.AI_SUGGESTION_APPLY in {task.task_type for task in task_center.list_tasks()}


def test_ai_suggestion_queue_page_state_is_testing_and_human_confirmed() -> None:
    state = initial_ai_suggestions_state()

    assert state.status_label == "测试中"
    assert "suggestion_type" in state.queue_columns
    assert "accept" in state.allowed_actions
    assert "ai_never_overwrites_screening_extraction_analysis_results" in state.safety_rules
    assert "AI 不会直接覆盖" in state.description


def test_mock_provider_creates_local_pending_suggestion(tmp_path: Path) -> None:
    service, _task_center, _data_center, project_dir = make_service(tmp_path)

    suggestion = service.create_mock_suggestion(
        project_dir,
        project_id="meta-test",
        target_type="report_text",
        target_id="section-analysis-summary",
        suggestion_type="report_draft_suggestion",
    )

    assert suggestion.status == AISuggestionStatus.PENDING.value
    assert suggestion.suggested_value["mock"] is True


def create_screening_suggestion(service: AISuggestionService, project_dir: Path):
    return service.create_ai_suggestion(
        project_dir,
        project_id="meta-test",
        target_type="screening_decision",
        target_id="screen-1",
        suggestion_type="relevance_screening",
        suggested_value={"decision": "include"},
        rationale="Abstract contains the target population and intervention.",
        confidence=0.82,
    )


def seed_formal_artifacts(project_dir: Path) -> None:
    (project_dir / "screening").mkdir(parents=True)
    (project_dir / "extraction").mkdir(parents=True)
    (project_dir / "analysis").mkdir(parents=True)
    (project_dir / "screening" / "screening_queue.json").write_text(
        json.dumps({"screening_records": [{"screening_record_id": "screen-1", "decision": "pending"}]}),
        encoding="utf-8",
    )
    (project_dir / "extraction" / "extraction_records.json").write_text(
        json.dumps({"records": [{"extraction_id": "extr-1", "record_id": "rec-1"}]}),
        encoding="utf-8",
    )
    (project_dir / "analysis" / "analysis_results.json").write_text(
        json.dumps({"results": [{"result_id": "ares-1"}]}),
        encoding="utf-8",
    )
