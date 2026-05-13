from __future__ import annotations

import json

from app.meta_analysis.extraction.schema_registry import NETWORK_META_ANALYSIS, TREATMENT_EFFECT_META
from app.meta_analysis.services.analysis_profile_config_service import AnalysisProfileConfigService
from app.meta_analysis.services.artifact_review_service import ArtifactReviewService
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.literature_edge_case_audit_service import LiteratureEdgeCaseAuditService
from app.meta_analysis.services.task_lifecycle_audit_service import TaskLifecycleAuditService
from app.shared.task_center.service import TaskRecord, TaskStatus, TaskType


def test_artifact_preview_reads_bounded_project_text_and_blocks_outside_paths(tmp_path) -> None:
    project_dir = tmp_path / "project"
    artifact = project_dir / "reports" / "formal_meta_report.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# Report\n\n" + ("result line\n" * 50), encoding="utf-8")

    service = ArtifactReviewService()
    preview = service.preview_project_artifact(project_dir, "reports/formal_meta_report.md", max_chars=32)
    outside = service.preview_project_artifact(project_dir, tmp_path / "outside.txt")

    assert preview.exists is True
    assert preview.relative_path == "reports/formal_meta_report.md"
    assert preview.preview_text.startswith("# Report")
    assert preview.truncated is True
    assert "artifact_preview_truncated" in preview.warnings
    assert outside.exists is False
    assert "artifact_path_outside_project" in outside.warnings


def test_result_detail_links_analysis_result_to_artifact_previews(tmp_path) -> None:
    project_dir = tmp_path / "project"
    (project_dir / "analysis").mkdir(parents=True)
    (project_dir / "exports").mkdir()
    table = project_dir / "exports" / "analysis_result_table_ares-1.csv"
    table.write_text("study,effect\nA,1.2\n", encoding="utf-8")
    (project_dir / "analysis" / "analysis_results.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "result_id": "ares-1",
                        "dataset_id": "ards-1",
                        "profile_type": "TREATMENT_EFFECT_META",
                        "outcome_name": "Mortality",
                        "effect_measure": "OR",
                        "model": "random",
                        "pooled_effect": 0.72,
                        "ci_lower": 0.55,
                        "ci_upper": 0.91,
                        "p_value": 0.02,
                        "study_results": [{"record_id": "rec-1"}, {"record_id": "rec-2"}],
                        "warnings": ["testing_result"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    detail = ArtifactReviewService().get_analysis_result_detail(project_dir, "ares-1")

    assert detail.warnings == ()
    assert detail.summary["study_count"] == 2
    assert detail.summary["effect_measure"] == "OR"
    assert any(item.relative_path == "exports/analysis_result_table_ares-1.csv" for item in detail.linked_artifacts)


def test_task_lifecycle_audit_records_transition_jsonl_and_meta_audit_event(tmp_path) -> None:
    project_dir = tmp_path / "project"
    before = _task("task-1", TaskStatus.RUNNING)
    after = _task("task-1", TaskStatus.COMPLETED)

    service = TaskLifecycleAuditService(audit_log=MetaAuditLogService())
    event = service.record_transition(project_dir, before=before, after=after, reason="batch_import_completed")
    summary = service.summarize(project_dir)
    audit_events = MetaAuditLogService().list_events(project_dir)

    assert event.from_status == "running"
    assert event.to_status == "completed"
    assert summary.event_count == 1
    assert summary.status_transition_counts["running->completed"] == 1
    assert any(item.event_type == "task_lifecycle_changed" and item.target_id == "task-1" for item in audit_events)


def test_analysis_profile_config_saves_reusable_pico_extraction_analysis_snapshot(tmp_path) -> None:
    project_dir = tmp_path / "project"
    service = AnalysisProfileConfigService(audit_log=MetaAuditLogService())
    config = service.build_config(
        project_dir,
        profile_type=TREATMENT_EFFECT_META,
        review_question="Does obesity increase thyroid cancer risk?",
        pico_mode="PECO",
        population="thyroid cancer population",
        intervention_or_exposure="obesity",
        comparator="non-obesity",
        outcomes=("incidence risk",),
        study_design="observational studies",
    )

    path = service.save_config(project_dir, config)
    loaded = service.list_configs(project_dir)
    audit_events = MetaAuditLogService().list_events(project_dir)

    assert path.exists()
    assert loaded[0].config_id == config.config_id
    assert loaded[0].pico_mode == "PECO"
    assert "OR" in loaded[0].effect_measures
    assert loaded[0].analysis_plan_defaults["model"] == "random"
    assert loaded[0].validation_errors == ()
    assert any(item.event_type == "analysis_profile_config_saved" for item in audit_events)


def test_analysis_profile_config_blocks_not_implemented_profile(tmp_path) -> None:
    config = AnalysisProfileConfigService().build_config(
        tmp_path / "project",
        profile_type=NETWORK_META_ANALYSIS,
        review_question="Network comparison?",
        outcomes=("response",),
    )

    assert "profile_type_not_implemented" in config.validation_errors
    assert config.effect_measures == ()


def test_literature_edge_case_audit_lists_test_driven_replacement_candidates(tmp_path) -> None:
    service = LiteratureEdgeCaseAuditService()
    items = service.build_audit()
    path = service.write_audit(tmp_path / "project")

    assert path.exists()
    assert {item.area for item in items} == {"literature_import", "literature_dedup"}
    assert any(item.capability == "CSV header aliases" for item in items)
    assert all("legacy" not in " ".join(item.active_files) for item in items)
    assert all(item.proposed_test for item in items)
    assert "active_runtime_no_legacy_bridge" in path.read_text(encoding="utf-8")


def _task(task_id: str, status: TaskStatus) -> TaskRecord:
    return TaskRecord(
        task_id=task_id,
        task_type=TaskType.LITERATURE_IMPORT,
        status=status,
        module="meta_analysis",
        title="Literature Import",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
        project_id="project",
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:00:01+00:00" if status is TaskStatus.COMPLETED else "",
        summary="testing task",
    )
