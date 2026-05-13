from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.reporting_page import initial_reporting_state
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder, PRISMAService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def test_prisma_numbers_collect_from_mock_project(tmp_path: Path) -> None:
    project_dir = seed_mock_project(tmp_path)
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = PRISMAService(task_center=task_center, data_center=data_center)

    summary = service.collect_prisma_numbers(project_dir)
    json_path = service.save_prisma_flow_summary(project_dir, summary)
    md_path = service.export_prisma_flow_markdown(project_dir, summary)

    assert summary.records_identified == 3
    assert summary.records_after_deduplication == 2
    assert summary.records_screened == 3
    assert summary.records_excluded_title_abstract == 1
    assert summary.studies_included == 1
    assert any("full-text workflow incomplete" in note for note in summary.notes)
    assert json_path.exists()
    assert "Full-text reports sought" in md_path.read_text(encoding="utf-8")
    assert task_center.list_tasks()[0].task_type is TaskType.PRISMA_COLLECT
    assert any(asset.data_type == "prisma_flow_summary" for asset in data_center.list_assets(project_dir.name))


def test_formal_markdown_report_contains_analysis_and_artifact_paths(tmp_path: Path) -> None:
    project_dir = seed_mock_project(tmp_path)
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    prisma_service = PRISMAService(task_center=task_center, data_center=data_center)
    builder = FormalMarkdownReportBuilder(
        prisma_service=prisma_service,
        task_center=task_center,
        data_center=data_center,
    )

    report_path = builder.build_formal_markdown_report(project_dir)
    report_text = report_path.read_text(encoding="utf-8")

    assert "Analysis summary" in report_text
    assert "forest_plot_ares-test.png" in report_text
    assert "analysis_result_table_ares-test.csv" in report_text
    assert "full-text workflow incomplete" in report_text.lower()
    assert "missing / not generated" in report_text
    assert task_center.list_tasks()[0].task_type is TaskType.FORMAL_REPORT_EXPORT
    assert any(asset.data_type == "formal_meta_report" for asset in data_center.list_assets(project_dir.name))


def test_reporting_page_state_exposes_prisma_and_formal_report_fields() -> None:
    state = initial_reporting_state()

    assert "records_identified" in state.prisma_summary_fields
    assert "formal_report_path" in state.formal_report_fields
    assert "PRISMA" in state.description


def seed_mock_project(tmp_path: Path) -> Path:
    project_dir = tmp_path / "meta-project"
    (project_dir / "literature").mkdir(parents=True)
    (project_dir / "deduplication").mkdir(parents=True)
    (project_dir / "screening").mkdir(parents=True)
    (project_dir / "extraction").mkdir(parents=True)
    (project_dir / "analysis").mkdir(parents=True)
    (project_dir / "figures").mkdir(parents=True)
    (project_dir / "exports").mkdir(parents=True)

    write_json(project_dir / "literature" / "batch_literature_records.json", {"records": [{"id": 1}, {"id": 2}, {"id": 3}]})
    write_json(project_dir / "deduplication" / "batch_deduplicated_literature.json", {"deduplicated_records": [{"id": 1}, {"id": 2}]})
    write_json(
        project_dir / "screening" / "batch_screening_queue.json",
        {
            "screening_records": [
                {"record_id": "rec-1", "decision": "included"},
                {"record_id": "rec-2", "decision": "excluded"},
                {"record_id": "rec-3", "decision": "maybe"},
            ]
        },
    )
    write_json(project_dir / "extraction" / "extraction_records.json", {"records": [{"extraction_id": "extr-1"}]})
    write_json(project_dir / "analysis" / "analysis_ready_datasets.json", {"datasets": [{"dataset_id": "ards-test"}]})
    write_json(project_dir / "analysis" / "analysis_results.json", {"results": [{"result_id": "ares-test"}]})
    write_json(project_dir / "figures" / "figure_artifacts.json", {"artifacts": [{"file_path": "forest_plot_ares-test.png"}]})
    (project_dir / "figures" / "forest_plot_ares-test.png").write_bytes(b"png")
    (project_dir / "exports" / "analysis_result_table_ares-test.csv").write_text("row_type,study_id\npooled,pooled\n", encoding="utf-8")
    return project_dir


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")
