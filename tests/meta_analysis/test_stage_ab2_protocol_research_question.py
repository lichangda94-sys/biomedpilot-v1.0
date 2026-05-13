from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.protocol_page import initial_protocol_page_state, protocol_page_state_from_project
from app.meta_analysis.pages.workflow_dashboard_page import (
    WORKFLOW_STATUS_COMPLETED,
    WORKFLOW_STATUS_NEEDS_REVIEW,
    WORKFLOW_STATUS_NOT_STARTED,
    WORKFLOW_STATUS_READY,
    workflow_dashboard_state_from_project,
)
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.protocol_service import ProjectProtocolService
from app.shared.data_center.service import DataCenter


def complete_protocol_values() -> dict[str, object]:
    return {
        "project_title": "Corticosteroids for adult severe pneumonia",
        "review_question": "Do systemic corticosteroids reduce mortality in adults with severe pneumonia?",
        "background": "Severe pneumonia remains associated with high mortality.",
        "objective": "Estimate comparative treatment effect using binary outcomes.",
        "meta_analysis_type": "TREATMENT_EFFECT_META",
        "method_profile_id": "TREATMENT_EFFECT_META",
        "population": "adults with severe pneumonia",
        "intervention_or_exposure": "systemic corticosteroids OR hydrocortisone",
        "comparator": "placebo OR usual care",
        "outcomes": ["mortality", "clinical cure"],
        "study_design": "randomized controlled trial",
        "primary_outcome": "mortality",
        "secondary_outcomes": ["clinical cure"],
        "eligible_study_designs": ["randomized controlled trial"],
        "planned_databases": ["PubMed", "Web of Science", "CNKI", "WanFang"],
        "search_date": "2026-04-29",
        "language_restriction": "none",
        "date_range_restriction": "none",
    }


def make_service(tmp_path: Path) -> tuple[ProjectProtocolService, DataCenter, MetaAuditLogService]:
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    audit_log = MetaAuditLogService()
    return ProjectProtocolService(data_center=data_center, audit_log=audit_log), data_center, audit_log


def test_ab2_empty_project_protocol_page_state_no_crash(tmp_path: Path) -> None:
    project_dir = tmp_path / "empty-meta-project"

    state = protocol_page_state_from_project(project_dir)
    initial = initial_protocol_page_state(project_dir)

    assert state.status_label == "Testing / Developer Preview"
    assert state.readiness_status == "not_started"
    assert "missing_protocol_artifact" in state.warnings
    assert state.output_paths["review_protocol"].endswith("protocol/review_protocol.json")
    assert "review_protocol.json" in initial.output_summary

    dashboard = workflow_dashboard_state_from_project(project_dir)
    protocol_step = {step.step_id: step for step in dashboard.steps}["protocol"]
    assert protocol_step.workflow_status == WORKFLOW_STATUS_NOT_STARTED


def test_ab2_save_complete_protocol_generates_artifacts_manifest_and_audit(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    service, data_center, audit_log = make_service(tmp_path)

    result = service.save_protocol(project_dir, complete_protocol_values(), confirmed=False)

    assert result.success is True
    assert result.protocol.readiness_status == "ready"
    assert not result.warnings
    for path in (
        result.artifact_paths.review_protocol,
        result.artifact_paths.search_terms_draft,
        result.artifact_paths.search_strategy_preview,
        result.artifact_paths.protocol_summary,
    ):
        assert Path(path).exists()

    protocol_payload = json.loads((project_dir / "protocol" / "review_protocol.json").read_text(encoding="utf-8"))
    assert protocol_payload["pico"]["population"] == "adults with severe pneumonia"
    assert protocol_payload["primary_outcome"] == "mortality"

    artifact_manifest = json.loads((project_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    relative_paths = {item["relative_path"] for item in artifact_manifest["artifacts"]}
    assert "protocol/review_protocol.json" in relative_paths
    assert "protocol/search_strategy_preview.md" in relative_paths

    data_types = {asset.data_type for asset in data_center.list_assets("meta-project")}
    assert {"review_protocol", "search_terms_draft", "search_strategy_preview", "protocol_summary"}.issubset(data_types)

    events = audit_log.list_events(project_dir)
    assert any(event.event_type == "record_saved" and event.target_type == "review_protocol" for event in events)


def test_ab2_missing_core_fields_generate_warnings_without_crash(tmp_path: Path) -> None:
    project_dir = tmp_path / "partial-project"
    service, _, _ = make_service(tmp_path)

    result = service.save_protocol(
        project_dir,
        {
            "project_title": "Partial protocol",
            "review_question": "A partial question",
            "planned_databases": ["PubMed"],
        },
    )

    assert result.protocol.readiness_status == "needs_review"
    assert "missing_population" in result.warnings
    assert "missing_outcomes" in result.warnings
    assert "missing_meta_analysis_type" in result.warnings
    assert Path(result.artifact_paths.search_strategy_preview).exists()

    state = protocol_page_state_from_project(project_dir, service=service)
    assert state.readiness_status == "needs_review"
    assert "Missing core fields" in state.completeness_summary

    dashboard = workflow_dashboard_state_from_project(project_dir)
    protocol_step = {step.step_id: step for step in dashboard.steps}["protocol"]
    assert protocol_step.workflow_status == WORKFLOW_STATUS_NEEDS_REVIEW
    assert any("missing_population" in warning for warning in protocol_step.warnings)


def test_ab2_search_strategy_drafts_for_required_databases(tmp_path: Path) -> None:
    project_dir = tmp_path / "strategy-project"
    service, _, _ = make_service(tmp_path)

    result = service.save_protocol(project_dir, complete_protocol_values())
    terms = json.loads(Path(result.artifact_paths.search_terms_draft).read_text(encoding="utf-8"))
    preview = Path(result.artifact_paths.search_strategy_preview).read_text(encoding="utf-8")

    assert terms["term_groups"]["population"]["free_text_terms"] == ["adults with severe pneumonia"]
    assert terms["term_groups"]["population"]["mesh_placeholder"]
    assert terms["term_groups"]["population"]["chinese_terms_placeholder"]
    assert "## PubMed draft" in preview
    assert "## Web of Science draft" in preview
    assert "## CNKI draft" in preview
    assert "## WanFang draft" in preview
    assert '"systemic corticosteroids"[Title/Abstract]' in preview
    assert "draft / needs reviewer validation" in preview


def test_ab2_workflow_dashboard_protocol_ready_and_completed_status(tmp_path: Path) -> None:
    project_dir = tmp_path / "workflow-project"
    service, data_center, audit_log = make_service(tmp_path)

    service.save_protocol(project_dir, complete_protocol_values(), confirmed=False)
    ready_state = workflow_dashboard_state_from_project(project_dir, data_center=data_center, audit_log=audit_log)
    ready_step = {step.step_id: step for step in ready_state.steps}["protocol"]
    assert ready_step.workflow_status == WORKFLOW_STATUS_READY
    assert ready_step.data_asset_count == 4

    service.save_protocol(project_dir, complete_protocol_values(), confirmed=True)
    completed_state = workflow_dashboard_state_from_project(project_dir, data_center=data_center, audit_log=audit_log)
    completed_step = {step.step_id: step for step in completed_state.steps}["protocol"]
    assert completed_step.workflow_status == WORKFLOW_STATUS_COMPLETED
    assert completed_step.audit_event_count >= 1
