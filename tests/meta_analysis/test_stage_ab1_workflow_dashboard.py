from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.workflow_dashboard_page import (
    RELEASE_STATUS_DEVELOPER_PREVIEW,
    WORKFLOW_STATUS_COMPLETED,
    WORKFLOW_STATUS_IN_PROGRESS,
    WORKFLOW_STATUS_NEEDS_REVIEW,
    WORKFLOW_STATUS_NOT_STARTED,
    WORKFLOW_STATUS_READY,
    initial_workflow_dashboard_state,
    workflow_dashboard_state_from_project,
)
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def test_ab1_workflow_dashboard_empty_project_no_crash(tmp_path: Path) -> None:
    project_dir = tmp_path / "empty-meta-project"

    state = workflow_dashboard_state_from_project(project_dir)
    step_by_id = {step.step_id: step for step in state.steps}

    assert state.status_label == RELEASE_STATUS_DEVELOPER_PREVIEW
    assert state.overall_status == WORKFLOW_STATUS_NOT_STARTED
    assert state.not_started_count == len(state.steps)
    assert state.manifest_status == WORKFLOW_STATUS_NEEDS_REVIEW
    assert state.manifest_warnings
    assert step_by_id["project_setup"].workflow_status == WORKFLOW_STATUS_NOT_STARTED
    assert step_by_id["literature_import"].entrypoint_page == "Literature Import page"
    assert all(step.release_status == RELEASE_STATUS_DEVELOPER_PREVIEW for step in state.steps)


def test_ab1_workflow_dashboard_infers_completed_ready_and_needs_review(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    (project_dir / "literature" / "import_diagnostics").mkdir(parents=True)
    (project_dir / "deduplication").mkdir(parents=True)
    (project_dir / "reports").mkdir(parents=True)
    (project_dir / "project.json").write_text(json.dumps({"project_id": "meta-project"}), encoding="utf-8")
    (project_dir / "literature" / "literature_records.json").write_text(
        json.dumps({"records": [{"record_id": "rec-1"}]}),
        encoding="utf-8",
    )
    (project_dir / "literature" / "import_diagnostics" / "batch_import_diagnostics.json").write_text(
        json.dumps({"warning_count": 2, "missing_title_count": 1}),
        encoding="utf-8",
    )
    (project_dir / "deduplication" / "batch_duplicate_groups.json").write_text(
        json.dumps({"duplicate_groups": [{"group_id": "dup-1", "record_ids": ["rec-1", "rec-2"]}]}),
        encoding="utf-8",
    )
    (project_dir / "reports" / "missing_fulltext_report.csv").write_text(
        "record_id,missing_fulltext\nrec-1,true\n",
        encoding="utf-8",
    )

    audit = MetaAuditLogService()
    audit.record_event(project_dir, event_type="import_batch_created", target_type="import_batch", target_id="batch", summary="import")
    audit.record_event(project_dir, event_type="diagnostics_generated", target_type="diagnostics", target_id="batch", summary="diagnostics")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    data_center.register_asset(
        project_id="meta-project",
        module="meta_analysis",
        data_type="literature_records",
        source_path="source.csv",
        output_path=str(project_dir / "literature" / "literature_records.json"),
    )

    state = workflow_dashboard_state_from_project(project_dir, data_center=data_center, audit_log=audit)
    step_by_id = {step.step_id: step for step in state.steps}

    assert step_by_id["project_setup"].workflow_status == WORKFLOW_STATUS_NEEDS_REVIEW
    assert step_by_id["literature_import"].workflow_status == WORKFLOW_STATUS_COMPLETED
    assert step_by_id["literature_import"].data_asset_count == 1
    assert step_by_id["literature_import"].audit_event_count == 1
    assert step_by_id["import_diagnostics"].workflow_status == WORKFLOW_STATUS_NEEDS_REVIEW
    assert any("missing_title_count" in warning for warning in step_by_id["import_diagnostics"].warnings)
    assert step_by_id["duplicate_review"].workflow_status == WORKFLOW_STATUS_NEEDS_REVIEW
    assert any("duplicate_groups_need_review" in warning for warning in step_by_id["duplicate_review"].warnings)
    assert step_by_id["criteria_builder"].workflow_status == WORKFLOW_STATUS_NOT_STARTED
    assert step_by_id["title_abstract_screening"].workflow_status == WORKFLOW_STATUS_READY
    assert state.needs_review_count >= 3


def test_ab1_workflow_dashboard_uses_task_center_for_in_progress(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    project_dir.mkdir()
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    task_center.register_task(
        task_id="task-analysis",
        task_type=TaskType.META_ANALYSIS_RUN,
        module="meta_analysis",
        title="Meta Analysis Run",
        project_id="meta-project",
        status=TaskStatus.RUNNING,
    )

    state = workflow_dashboard_state_from_project(project_dir, task_center=task_center)
    step_by_id = {step.step_id: step for step in state.steps}

    assert step_by_id["meta_analysis_run"].workflow_status == WORKFLOW_STATUS_IN_PROGRESS
    assert step_by_id["meta_analysis_run"].task_count == 1
    assert state.overall_status == WORKFLOW_STATUS_IN_PROGRESS


def test_ab1_initial_state_and_step_copy_are_tester_readable(tmp_path: Path) -> None:
    state = initial_workflow_dashboard_state(tmp_path)

    assert state.title == "Meta Project Workflow Dashboard"
    assert state.status_label == RELEASE_STATUS_DEVELOPER_PREVIEW
    assert "Not started / Ready / Needs review / Completed" in state.empty_state
