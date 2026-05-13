from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.attachment_page import attachment_state_from_project
from app.meta_analysis.pages.criteria_page import criteria_page_state_from_project, initial_criteria_page_state
from app.meta_analysis.pages.screening_page import screening_state_with_criteria
from app.meta_analysis.pages.workflow_dashboard_page import WORKFLOW_STATUS_COMPLETED, WORKFLOW_STATUS_READY, workflow_dashboard_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.criteria_service import CriteriaBuilderService
from app.shared.data_center.service import DataCenter


def write_protocol(project_dir: Path) -> None:
    path = project_dir / "protocol" / "review_protocol.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"project_id": project_dir.name, "protocol_id": "protocol-1"}), encoding="utf-8")


def make_service(tmp_path: Path) -> tuple[CriteriaBuilderService, DataCenter, MetaAuditLogService]:
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    audit_log = MetaAuditLogService()
    return CriteriaBuilderService(data_center=data_center, audit_log=audit_log), data_center, audit_log


def test_ab5_criteria_empty_state_no_crash(tmp_path: Path) -> None:
    project_dir = tmp_path / "empty-project"

    initial = initial_criteria_page_state(project_dir)
    state = criteria_page_state_from_project(project_dir)

    assert initial.status_label == "Testing / Developer Preview"
    assert state.readiness_status == "not_started"
    assert "missing_criteria_artifacts" in state.warnings
    assert state.output_paths["criteria_summary"].endswith("criteria/criteria_summary.md")


def test_ab5_save_default_criteria_writes_artifacts_manifest_data_and_audit(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    write_protocol(project_dir)
    service, data_center, audit_log = make_service(tmp_path)

    criteria = service.save_criteria(project_dir)

    assert criteria.readiness_status == "ready"
    assert not criteria.warnings
    assert (project_dir / "criteria" / "inclusion_criteria.json").exists()
    assert (project_dir / "criteria" / "exclusion_criteria.json").exists()
    assert (project_dir / "criteria" / "criteria_summary.md").exists()
    summary = (project_dir / "criteria" / "criteria_summary.md").read_text(encoding="utf-8")
    assert "human studies" in summary
    assert "wrong population" in summary

    artifact_manifest = json.loads((project_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    relative_paths = {item["relative_path"] for item in artifact_manifest["artifacts"]}
    assert "criteria/inclusion_criteria.json" in relative_paths
    assert "criteria/criteria_summary.md" in relative_paths

    data_types = {asset.data_type for asset in data_center.list_assets("meta-project")}
    assert {"inclusion_criteria", "exclusion_criteria", "criteria_summary"} <= data_types
    assert any(event.event_type == "record_saved" and event.target_type == "criteria_builder" for event in audit_log.list_events(project_dir))


def test_ab5_missing_protocol_reference_generates_warning_but_writes_draft(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    service, _, _ = make_service(tmp_path)

    criteria = service.save_criteria(project_dir, inclusion_labels=["human studies"], exclusion_labels=["animal study"])
    state = criteria_page_state_from_project(project_dir, service=service)

    assert "missing_protocol_reference" in criteria.warnings
    assert state.readiness_status == "needs_review"
    assert "Exclude if: animal study" in state.screening_hints
    assert (project_dir / "criteria" / "criteria_summary.md").exists()


def test_ab5_criteria_hints_surface_in_screening_and_fulltext_states(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    write_protocol(project_dir)
    service, _, _ = make_service(tmp_path)
    service.save_criteria(
        project_dir,
        inclusion_labels=["target population", "eligible outcome"],
        exclusion_labels=["wrong population", "wrong outcome"],
    )

    screening_state = screening_state_with_criteria(project_dir, criteria_service=service)
    attachment_state = attachment_state_from_project(project_dir, criteria_service=service)

    assert screening_state.criteria_summary_path.endswith("criteria/criteria_summary.md")
    assert "Include if: target population" in screening_state.criteria_hints
    assert "Exclude if: wrong outcome" in screening_state.criteria_hints
    assert attachment_state.criteria_summary_path.endswith("criteria/criteria_summary.md")
    assert "Exclude if: wrong population" in attachment_state.criteria_hints


def test_ab5_workflow_dashboard_criteria_status(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    write_protocol(project_dir)
    service, data_center, audit_log = make_service(tmp_path)

    missing_state = workflow_dashboard_state_from_project(project_dir, data_center=data_center, audit_log=audit_log)
    missing_step = {step.step_id: step for step in missing_state.steps}["criteria_builder"]
    assert missing_step.workflow_status == WORKFLOW_STATUS_READY

    service.save_criteria(project_dir)
    state = workflow_dashboard_state_from_project(project_dir, data_center=data_center, audit_log=audit_log)
    step = {step.step_id: step for step in state.steps}["criteria_builder"]
    assert step.workflow_status == WORKFLOW_STATUS_COMPLETED
    assert step.data_asset_count == 3
