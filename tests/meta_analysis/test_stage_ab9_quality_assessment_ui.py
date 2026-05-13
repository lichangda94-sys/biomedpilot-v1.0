from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.extraction.schema_registry import DIAGNOSTIC_ACCURACY_META, TREATMENT_EFFECT_META
from app.meta_analysis.pages.quality_page import quality_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
from app.meta_analysis.services.quality_service import QualityAssessmentService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def seed_final_included(project_dir: Path) -> None:
    write_json(
        project_dir / "fulltext" / "final_included_studies.json",
        {
            "included_studies": [
                {"record_id": "rec-1", "study_id": "study-1", "title": "Randomized trial", "study_design": "randomized trial"},
                {"record_id": "rec-2", "study_id": "study-2", "title": "Diagnostic accuracy study", "study_design": "diagnostic accuracy"},
            ]
        },
    )


def service_stack(tmp_path: Path) -> tuple[QualityAssessmentService, DataCenter, TaskCenter, MetaAuditLogService]:
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    audit = MetaAuditLogService()
    contract = MetaProjectContractService(data_center=data_center, task_center=task_center)
    return QualityAssessmentService(task_center=task_center, data_center=data_center, audit_log=audit, project_contract=contract), data_center, task_center, audit


def test_ab9_quality_state_recommends_tools_and_handles_empty_project(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"

    empty = quality_state_from_project(project_dir)
    assert empty.status_label == "Testing / Developer Preview"
    assert "no_included_studies_for_quality_assessment" in empty.warnings
    assert "quality_summary" in empty.output_paths

    seed_final_included(project_dir)
    state = quality_state_from_project(project_dir, profile_type=TREATMENT_EFFECT_META)

    assert [row.study_id for row in state.study_rows] == ["study-1", "study-2"]
    assert state.study_rows[0].recommended_tool == "RoB2 simplified"
    assert state.selected_tool == "RoB2 simplified"
    assert "randomization" in state.domain_fields
    assert "randomization_note" in state.domain_note_fields
    assert "overall judgement" in state.description.lower()


def test_ab9_quality_state_supports_diagnostic_profile_metadata(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_final_included(project_dir)

    state = quality_state_from_project(project_dir, selected_tool="QUADAS-2", profile_type=DIAGNOSTIC_ACCURACY_META)

    assert state.selected_tool == "QUADAS-2"
    assert "patient_selection" in state.domain_fields
    assert "low" in state.judgement_options
    assert state.study_rows[0].recommended_tool == "QUADAS-2"


def test_ab9_save_quality_assessment_audit_manifest_and_exports(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_final_included(project_dir)
    service, data_center, task_center, audit = service_stack(tmp_path)
    assessment = service.create_quality_assessment(
        project_id=project_dir.name,
        study_id="study-1",
        record_id="rec-1",
        tool_name="RoB2 simplified",
        domains={"randomization": "low risk", "deviations": "some concerns"},
        domain_notes={"deviations": "Some protocol deviations."},
        overall_judgement=service.suggest_overall_judgement("RoB2 simplified", {"randomization": "low risk", "deviations": "some concerns"}),
        reviewer_id="rev-1",
        notes="Testing quality assessment.",
    )

    service.save_quality_assessment(project_dir, assessment)
    outputs = service.export_quality_beta_outputs(project_dir, expected_study_ids=["study-1", "study-2"])

    assert Path(outputs["quality_assessment"]).exists()
    assert Path(outputs["quality_table"]).exists()
    assert Path(outputs["quality_summary"]).exists()
    assert "Completeness score" in Path(outputs["quality_summary"]).read_text(encoding="utf-8")
    assert "quality_summary" in {asset.data_type for asset in data_center.list_assets(project_dir.name)}
    assert {TaskType.QUALITY_ASSESSMENT_SAVE, TaskType.QUALITY_ASSESSMENT_EXPORT} <= {task.task_type for task in task_center.list_tasks()}
    assert any(event.target_type == "quality_assessment" for event in audit.list_events(project_dir))
    assert (project_dir / "artifact_manifest.json").exists()


def test_ab9_quality_page_state_marks_missing_assessments(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_final_included(project_dir)
    service, _, _, _ = service_stack(tmp_path)
    assessment = service.create_quality_assessment(
        project_id=project_dir.name,
        study_id="study-1",
        record_id="rec-1",
        tool_name="NOS",
        domains={"selection": "low risk"},
        overall_judgement="low risk",
        reviewer_id="rev-1",
    )
    service.save_quality_assessment(project_dir, assessment)

    state = quality_state_from_project(project_dir, service=service)

    assert state.study_rows[0].assessment_status == "assessed"
    assert state.study_rows[1].assessment_status == "needs_assessment"
    assert state.completeness_summary["missing_study_ids"] == ["study-2"]
    assert "quality_assessment_missing:1" in state.warnings
