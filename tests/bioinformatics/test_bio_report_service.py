from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.pages.bio_report_page import initial_bio_report_state
from app.bioinformatics.services.bio_report_service import BioReportService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[BioReportService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = BioReportService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_preflight(tmp_path: Path) -> Path:
    path = tmp_path / "geo_differential_expression_preflight.json"
    payload = {
        "project_id": "bio-test",
        "formal_deg_executed": False,
        "preflight_items": [
            {
                "accession": "GSE1001",
                "status": "blocked_no_group_assignment",
                "next_action": "Assign case/control groups.",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_bio_report_rejects_empty_sources(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.export_summary_report(project_id="bio-test", source_paths=[])
    assert not result.success
    assert "至少选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_bio_report_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.export_summary_report(project_id="bio-test", source_paths=[str(tmp_path / "missing.json")])
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.REPORT_EXPORT


def test_bio_report_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "preflight.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.export_summary_report(project_id="bio-test", source_paths=[str(source)])
    assert not result.success
    assert "JSON" in result.message


def test_bio_report_exports_testing_summary(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_preflight(tmp_path)
    result = service.export_summary_report(project_id="bio-test", source_paths=[str(source)])
    assert result.success
    assert result.source_count == 1
    assert result.details["formal_report_executed"] is False
    report = Path(result.output_path).read_text(encoding="utf-8")
    assert "Bioinformatics Test Summary" in report
    assert "formal differential expression" in report
    assert "geo_differential_expression_preflight" in report
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.REPORT_EXPORT
    assert any(asset.data_type == "bioinformatics_report_summary" for asset in data_center.list_assets("bio-test"))


def test_bio_report_feature_status_and_page_state() -> None:
    feature = get_feature("bio-reporting")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "测试摘要" in feature.description
    state = initial_bio_report_state()
    assert state.title == "报告导出"
    assert state.status_label == "测试中"
