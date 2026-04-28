from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.analysis_page import initial_analysis_state
from app.meta_analysis.services.analysis_service import AnalysisPreflightService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[AnalysisPreflightService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = AnalysisPreflightService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_extraction_pool(
    tmp_path: Path,
    *,
    extraction_count: int = 1,
    outcome_records: list[dict[str, object]] | None = None,
) -> Path:
    path = tmp_path / "extraction_pool.json"
    payload = {
        "project_id": "meta-test",
        "batch_id": "batch-analysis",
        "manual_data_entry_enabled": False,
        "extraction_records": [
            {
                "extraction_record_id": f"extr-{index}",
                "project_id": "meta-test",
                "screening_record_id": f"screen-{index}",
                "normalized_record_id": f"rec-{index}",
                "study_title": f"Study {index}",
            }
            for index in range(1, extraction_count + 1)
        ],
        "outcome_records": outcome_records or [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def binary_outcome(outcome_id: str) -> dict[str, object]:
    return {
        "outcome_record_id": outcome_id,
        "extraction_record_id": "extr-1",
        "outcome_name": "Mortality",
        "outcome_type": "binary",
        "group_a_n": 100,
        "group_b_n": 100,
        "events_a": 10,
        "events_b": 15,
    }


def test_analysis_preflight_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.run_preflight(project_id="meta-test", extraction_pool_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_analysis_preflight_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.run_preflight(project_id="meta-test", extraction_pool_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.ANALYSIS


def test_analysis_preflight_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "analysis.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.run_preflight(project_id="meta-test", extraction_pool_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_analysis_preflight_blocks_without_outcomes(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_extraction_pool(tmp_path, extraction_count=1)
    result = service.run_preflight(project_id="meta-test", extraction_pool_path=str(source))
    assert result.success
    assert not result.runnable
    assert result.extraction_records == 1
    assert result.outcome_records == 0
    assert "outcome_records_missing" in result.blocking_errors
    assert result.recommended_action == "enter_outcome_data"
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["statistical_analysis_executed"] is False
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.ANALYSIS
    assert any(asset.data_type == "analysis_preflight" for asset in data_center.list_assets("meta-test"))


def test_analysis_preflight_blocks_without_extraction_records(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    source = write_extraction_pool(tmp_path, extraction_count=0)
    result = service.run_preflight(project_id="meta-test", extraction_pool_path=str(source))
    assert result.success
    assert not result.runnable
    assert "extraction_records_missing" in result.blocking_errors


def test_analysis_preflight_passes_with_two_valid_binary_outcomes(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    source = write_extraction_pool(
        tmp_path,
        extraction_count=2,
        outcome_records=[binary_outcome("out-1"), binary_outcome("out-2")],
    )
    result = service.run_preflight(project_id="meta-test", extraction_pool_path=str(source))
    assert result.success
    assert result.runnable
    assert result.valid_outcome_records == 2
    assert result.blocking_errors == []
    assert result.recommended_action in {"ready_for_statistical_analysis", "review_warnings_before_analysis"}


def test_analysis_preflight_blocks_invalid_outcome_fields(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    invalid = binary_outcome("out-bad")
    invalid.pop("events_b")
    source = write_extraction_pool(tmp_path, extraction_count=1, outcome_records=[invalid])
    result = service.run_preflight(project_id="meta-test", extraction_pool_path=str(source))
    assert result.success
    assert not result.runnable
    assert any("missing_events_b" in error for error in result.blocking_errors)


def test_analysis_feature_status_and_page_state() -> None:
    feature = get_feature("meta-analysis")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "预检" in feature.description
    state = initial_analysis_state()
    assert state.title == "Analysis / Meta 统计分析预检"
    assert state.status_label == "测试中"
