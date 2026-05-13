from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.fulltext_eligibility_page import fulltext_eligibility_state_from_project
from app.meta_analysis.pages.workflow_dashboard_page import workflow_dashboard_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.fulltext_eligibility_service import FullTextEligibilityService
from app.meta_analysis.services.fulltext_service import FullTextService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def seed_title_abstract_decisions(project_dir: Path) -> None:
    write_json(
        project_dir / "screening" / "title_abstract_decisions.json",
        {
            "records": [
                {
                    "screening_record_id": "screen-1",
                    "record_id": "rec-1",
                    "title": "Included randomized trial",
                    "authors": ["Smith J"],
                    "journal": "Journal A",
                    "year": "2025",
                    "doi": "10.1000/a",
                    "pmid": "111",
                    "decision": "included",
                },
                {
                    "screening_record_id": "screen-2",
                    "record_id": "rec-2",
                    "title": "Maybe trial",
                    "authors_text": "Lee K",
                    "decision": "maybe",
                },
                {
                    "screening_record_id": "screen-3",
                    "record_id": "rec-3",
                    "title": "Excluded review",
                    "decision": "excluded",
                },
            ],
            "decision_counts": {"included": 1, "maybe": 1, "excluded": 1},
        },
    )
    write_json(project_dir / "screening" / "screening_decisions.json", {"records": []})


def service_stack(tmp_path: Path) -> tuple[FullTextEligibilityService, DataCenter, TaskCenter, MetaAuditLogService]:
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    audit = MetaAuditLogService()
    fulltext_service = FullTextService(task_center=task_center, data_center=data_center, audit_log=audit)
    return FullTextEligibilityService(fulltext_service=fulltext_service, data_center=data_center, audit_log=audit), data_center, task_center, audit


def test_ab7_build_candidates_from_included_and_maybe_screening_decisions(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_title_abstract_decisions(project_dir)
    service, _, _, _ = service_stack(tmp_path)

    candidates = service.build_candidates_from_screening(project_dir)

    assert [candidate.record_id for candidate in candidates] == ["rec-1", "rec-2"]
    assert candidates[0].recommended_action == "link_or_copy_pdf"
    assert candidates[1].screening_decision == "maybe"


def test_ab7_save_decision_writes_eligibility_and_compatible_fulltext_decisions(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_title_abstract_decisions(project_dir)
    service, data_center, task_center, audit = service_stack(tmp_path)

    result = service.save_eligibility_decision(
        project_dir,
        record_id="rec-1",
        eligibility_status="included_for_extraction",
        reviewer_id="rev-1",
        notes="Full text assessed.",
        source_screening_decision="included",
    )

    assert result.success is True
    assert Path(result.output_path).exists()
    assert Path(result.compatible_decisions_path).exists()
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["developer_preview"] is True
    compatible = json.loads(Path(result.compatible_decisions_path).read_text(encoding="utf-8"))
    assert compatible["decisions"][0]["decision"] == "include"
    assert TaskType.FULLTEXT_SCREENING_DECISION in {task.task_type for task in task_center.list_tasks()}
    data_types = {asset.data_type for asset in data_center.list_assets(project_dir.name)}
    assert "fulltext_eligibility_decisions" in data_types
    assert any(event.target_type == "fulltext_eligibility_decision" for event in audit.list_events(project_dir))


def test_ab7_excluded_decision_requires_reason_and_exports_reports(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_title_abstract_decisions(project_dir)
    service, data_center, _, _ = service_stack(tmp_path)

    blocked = service.save_eligibility_decision(project_dir, record_id="rec-2", eligibility_status="excluded_after_full_text_review")
    assert blocked.success is False
    assert "error:missing_fulltext_exclusion_reason" in blocked.warnings

    saved = service.save_eligibility_decision(
        project_dir,
        record_id="rec-2",
        eligibility_status="excluded_after_full_text_review",
        exclusion_reason="wrong outcome",
        reviewer_id="rev-1",
    )
    assert saved.success is True
    report_path = service.export_fulltext_exclusion_report(project_dir)

    assert report_path == project_dir / "fulltext" / "fulltext_exclusion_report.csv"
    assert "wrong outcome" in report_path.read_text(encoding="utf-8")
    assert (project_dir / "reports" / "full_text_exclusion_report.csv").exists()
    data_types = {asset.data_type for asset in data_center.list_assets(project_dir.name)}
    assert {"fulltext_eligibility_exclusion_report", "full_text_exclusion_report"} <= data_types


def test_ab7_final_included_studies_uses_include_like_statuses(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_title_abstract_decisions(project_dir)
    service, data_center, _, _ = service_stack(tmp_path)
    service.save_eligibility_decision(project_dir, record_id="rec-1", eligibility_status="included_for_extraction")
    service.save_eligibility_decision(project_dir, record_id="rec-2", eligibility_status="missing_full_text", exclusion_reason="no full text")

    output_path = service.export_final_included_studies(project_dir)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert [item["record_id"] for item in payload["included_studies"]] == ["rec-1"]
    data_types = {asset.data_type for asset in data_center.list_assets(project_dir.name)}
    assert "final_included_studies" in data_types


def test_ab7_attach_pdf_for_candidate_link_and_copy_modes(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_title_abstract_decisions(project_dir)
    source_pdf = tmp_path / "trial.pdf"
    source_pdf.write_bytes(b"%PDF-1.4 trial")
    service, _, _, _ = service_stack(tmp_path)

    linked = service.attach_pdf_for_candidate(project_dir, record_id="rec-1", source_file_path=str(source_pdf), mode="link_existing_files")
    copied = service.attach_pdf_for_candidate(project_dir, record_id="rec-2", source_file_path=str(source_pdf), mode="copy_to_project_library")

    assert linked.success is True
    assert linked.decision is not None and linked.decision.eligibility_status == "local_pdf_linked"
    assert copied.success is True
    assert copied.decision is not None and copied.decision.eligibility_status == "local_pdf_copied"
    assert (project_dir / "fulltext" / f"rec-2_{source_pdf.name}").exists()


def test_ab7_page_state_handles_empty_and_populated_project(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"

    empty = fulltext_eligibility_state_from_project(project_dir)
    assert empty.candidate_count == 0
    assert "missing_screening_decisions" in empty.warnings
    assert "fulltext_eligibility_decisions" in empty.output_paths

    seed_title_abstract_decisions(project_dir)
    state = fulltext_eligibility_state_from_project(project_dir)
    assert state.status_label == "Testing / Developer Preview"
    assert state.candidate_count == 2
    assert "included_for_extraction" in state.status_options
    assert "wrong outcome" in state.exclusion_reason_options
    assert state.output_paths["final_included_studies"].endswith("fulltext/final_included_studies.json")


def test_ab7_workflow_dashboard_reads_final_included_studies(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_title_abstract_decisions(project_dir)
    (project_dir / "project.json").write_text("{}", encoding="utf-8")
    service, data_center, task_center, audit = service_stack(tmp_path)
    service.save_eligibility_decision(project_dir, record_id="rec-1", eligibility_status="included_for_extraction")
    service.export_final_included_studies(project_dir)

    state = workflow_dashboard_state_from_project(project_dir, data_center=data_center, task_center=task_center, audit_log=audit)
    fulltext_step = next(step for step in state.steps if step.step_id == "fulltext_attachment")

    assert "fulltext/fulltext_eligibility_decisions.json" in fulltext_step.existing_artifacts
    assert "fulltext/final_included_studies.json" in fulltext_step.existing_artifacts
    assert fulltext_step.release_status == "Developer Preview"
