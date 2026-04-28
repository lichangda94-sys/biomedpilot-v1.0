from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.reporting_page import initial_reporting_state
from app.meta_analysis.services.reporting_service import ReportingService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[ReportingService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = ReportingService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_analysis_preflight(tmp_path: Path, *, runnable: bool = False) -> Path:
    path = tmp_path / "analysis_preflight.json"
    payload = {
        "project_id": "meta-test",
        "batch_id": "batch-reporting",
        "source_path": "extraction_pool.json",
        "statistical_analysis_executed": False,
        "preflight": {
            "extraction_records": 1,
            "outcome_records": 0 if not runnable else 2,
            "valid_outcome_records": 0 if not runnable else 2,
            "outcome_type_counts": {} if not runnable else {"binary": 2},
            "runnable": runnable,
            "blocking_errors": ["outcome_records_missing"] if not runnable else [],
            "warnings": ["manual_extraction_form_not_open"],
            "recommended_action": "enter_outcome_data" if not runnable else "review_warnings_before_analysis",
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_reporting_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.export_preflight_report(project_id="meta-test", analysis_preflight_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_reporting_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.export_preflight_report(project_id="meta-test", analysis_preflight_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.REPORT_EXPORT


def test_reporting_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "report.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.export_preflight_report(project_id="meta-test", analysis_preflight_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_reporting_exports_markdown_preflight_summary(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_analysis_preflight(tmp_path)
    result = service.export_preflight_report(project_id="meta-test", analysis_preflight_path=str(source))
    assert result.success
    assert result.report_type == "analysis_preflight_markdown"
    report_text = Path(result.report_path).read_text(encoding="utf-8")
    assert "BioMedPilot Meta Analysis Preflight Report" in report_text
    assert "no pooled meta-analysis was executed" in report_text
    assert "outcome_records_missing" in report_text
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.REPORT_EXPORT
    assert any(asset.data_type == "meta_analysis_report" for asset in data_center.list_assets("meta-test"))


def test_reporting_feature_status_and_page_state() -> None:
    feature = get_feature("meta-reporting")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "Markdown" in feature.description
    state = initial_reporting_state()
    assert state.title == "Reporting / 报告导出"
    assert state.status_label == "测试中"
