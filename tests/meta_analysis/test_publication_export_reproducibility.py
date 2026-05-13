from __future__ import annotations

import json
import zipfile
from pathlib import Path

from app.meta_analysis.pages.reporting_page import initial_reporting_state
from app.meta_analysis.services.publication_export_service import PublicationExportService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def test_html_and_word_testing_reports_are_exported(tmp_path: Path) -> None:
    project_dir = seed_publication_project(tmp_path)
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = PublicationExportService(task_center=task_center, data_center=data_center)

    html_result = service.export_html_report(project_dir)
    word_result = service.export_word_report(project_dir)

    html_path = Path(html_result.output_path)
    word_path = Path(word_result.output_path)
    assert html_path.exists()
    assert "testing / developer preview" in html_path.read_text(encoding="utf-8")
    assert word_path.exists()
    assert zipfile.is_zipfile(word_path)
    with zipfile.ZipFile(word_path) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
    assert "Analysis summary" in document_xml
    data_types = {asset.data_type for asset in data_center.list_assets(project_dir.name)}
    assert {"formal_html_report", "formal_word_report"} <= data_types
    task_types = {task.task_type for task in task_center.list_tasks()}
    assert TaskType.HTML_REPORT_EXPORT in task_types
    assert TaskType.WORD_REPORT_EXPORT in task_types


def test_supplementary_exports_and_figure_package_are_generated(tmp_path: Path) -> None:
    project_dir = seed_publication_project(tmp_path)
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = PublicationExportService(task_center=task_center, data_center=data_center)

    supplementary = service.export_supplementary_exports(project_dir)
    figure_package = service.export_figure_package(project_dir)

    supplementary_dir = Path(supplementary.output_path)
    assert (supplementary_dir / "literature_records.csv").exists()
    assert (supplementary_dir / "extraction_records.csv").exists()
    assert "wrong outcome" in (supplementary_dir / "full_text_exclusion_report.csv").read_text(encoding="utf-8")
    package_path = Path(figure_package.output_path)
    assert package_path.exists()
    assert package_path.stat().st_size > 0
    with zipfile.ZipFile(package_path) as archive:
        names = set(archive.namelist())
    assert "figures/forest_plot_ares-test.png" in names
    assert "exports/analysis_result_table_ares-test.csv" in names
    data_types = {asset.data_type for asset in data_center.list_assets(project_dir.name)}
    assert {"supplementary_exports", "figure_package"} <= data_types
    task_types = {task.task_type for task in task_center.list_tasks()}
    assert TaskType.SUPPLEMENTARY_EXPORT in task_types
    assert TaskType.FIGURE_PACKAGE_EXPORT in task_types


def test_snapshot_reproducibility_package_and_artifact_lock(tmp_path: Path) -> None:
    project_dir = seed_publication_project(tmp_path)
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = PublicationExportService(task_center=task_center, data_center=data_center)

    first_html = service.export_html_report(project_dir)
    snapshot = service.create_project_snapshot(project_dir)
    snapshot_path = service.save_project_snapshot(project_dir, snapshot)
    repro_package = service.export_reproducibility_package(project_dir)
    lock = service.lock_formal_report(project_dir)
    second_html = service.export_html_report(project_dir)

    assert snapshot_path.exists()
    assert service.list_project_snapshots(project_dir)[0].snapshot_id == snapshot.snapshot_id
    assert snapshot.software_version.endswith("testing")
    repro_path = Path(repro_package.output_path)
    assert repro_path.exists()
    with zipfile.ZipFile(repro_path) as archive:
        names = set(archive.namelist())
    assert "project.json" in names
    assert "software_version.json" in names
    assert lock.artifact_type == "formal_report"
    assert Path(second_html.output_path) != Path(first_html.output_path)
    assert "formal_report_locked_new_version_created" in second_html.warnings
    assert Path(first_html.output_path).exists()
    data_types = {asset.data_type for asset in data_center.list_assets(project_dir.name)}
    assert {"project_snapshot", "reproducibility_package", "formal_html_report"} <= data_types
    task_types = {task.task_type for task in task_center.list_tasks()}
    assert TaskType.PROJECT_SNAPSHOT_CREATE in task_types
    assert TaskType.REPRODUCIBILITY_PACKAGE_EXPORT in task_types
    assert TaskType.ARTIFACT_LOCK in task_types


def test_reporting_page_state_exposes_publication_export_fields() -> None:
    state = initial_reporting_state()

    assert "html_report_path" in state.publication_export_fields
    assert "word_report_path" in state.publication_export_fields
    assert "reproducibility_package_path" in state.publication_export_fields
    assert "PDF 正式报告仍未开放" in state.description


def seed_publication_project(tmp_path: Path) -> Path:
    project_dir = tmp_path / "meta-project"
    (project_dir / "literature").mkdir(parents=True)
    (project_dir / "deduplication").mkdir(parents=True)
    (project_dir / "screening").mkdir(parents=True)
    (project_dir / "extraction").mkdir(parents=True)
    (project_dir / "analysis").mkdir(parents=True)
    (project_dir / "figures").mkdir(parents=True)
    (project_dir / "exports").mkdir(parents=True)
    (project_dir / "reports").mkdir(parents=True)
    (project_dir / "quality").mkdir(parents=True)

    (project_dir / "project.json").write_text(json.dumps({"project_id": "meta-project"}), encoding="utf-8")
    write_json(project_dir / "literature" / "batch_literature_records.json", {"records": [{"record_id": "rec-1", "title": "Trial 1"}]})
    write_json(project_dir / "deduplication" / "batch_deduplicated_literature.json", {"deduplicated_records": [{"record_id": "rec-1"}]})
    write_json(project_dir / "screening" / "batch_screening_queue.json", {"screening_records": [{"record_id": "rec-1", "decision": "included"}]})
    write_json(project_dir / "extraction" / "extraction_records.json", {"records": [{"extraction_id": "extr-1", "record_id": "rec-1", "study_id": "study-1"}]})
    write_json(
        project_dir / "analysis" / "analysis_ready_datasets.json",
        {
            "datasets": [
                {
                    "dataset_id": "ards-test",
                    "study_rows": [
                        {
                            "study_id": "study-1",
                            "record_id": "rec-1",
                            "outcome_name": "Mortality",
                            "analysis_status": "included",
                        }
                    ],
                }
            ]
        },
    )
    write_json(project_dir / "analysis" / "analysis_results.json", {"results": [{"result_id": "ares-test"}]})
    (project_dir / "reports" / "full_text_exclusion_report.csv").write_text(
        "record_id,decision,exclusion_reason\nrec-2,exclude,wrong outcome\n",
        encoding="utf-8",
    )
    (project_dir / "quality" / "quality_assessments.json").write_text(json.dumps({"quality_assessments": []}), encoding="utf-8")
    (project_dir / "exports" / "quality_assessment_table.csv").write_text("assessment_id,overall_judgement\nqa-1,low risk\n", encoding="utf-8")
    (project_dir / "exports" / "analysis_result_table_ares-test.csv").write_text("row_type,study_id\npooled,pooled\n", encoding="utf-8")
    (project_dir / "figures" / "forest_plot_ares-test.png").write_bytes(b"png")
    (project_dir / "reports" / "formal_meta_report.md").write_text(
        "\n".join(
            [
                "# Formal Meta Analysis Report Draft",
                "",
                "## Project summary",
                "- Current software status: testing / developer preview",
                "",
                "## Analysis summary",
                "- Pooled result: testing.",
                "",
                "## Forest plot artifact path",
                "- figures/forest_plot_ares-test.png",
                "",
                "## Result table artifact path",
                "- exports/analysis_result_table_ares-test.csv",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return project_dir


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")
