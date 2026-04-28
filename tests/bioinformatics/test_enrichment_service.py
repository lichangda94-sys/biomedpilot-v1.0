from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.pages.enrichment_page import initial_enrichment_state
from app.bioinformatics.services.enrichment_service import EnrichmentService
from app.shared.data_center.service import DataCenter
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


def make_service(tmp_path) -> tuple[EnrichmentService, TaskCenter, DataCenter]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = EnrichmentService(
        task_center=task_center,
        data_center=data_center,
        storage_root=tmp_path,
    )
    return service, task_center, data_center


def write_deg_preflight(
    tmp_path: Path,
    *,
    deg_result_files: list[str] | None = None,
    upregulated_gene_count: int = 0,
    downregulated_gene_count: int = 0,
) -> Path:
    path = tmp_path / "geo_differential_expression_preflight.json"
    payload = {
        "project_id": "bio-test",
        "formal_deg_executed": False,
        "network_used": False,
        "preflight_items": [
            {
                "accession": "GSE1001",
                "deg_result_files": deg_result_files or [],
                "upregulated_gene_count": upregulated_gene_count,
                "downregulated_gene_count": downregulated_gene_count,
                "status": "ready_for_deg_runner",
                "next_action": "Review parameters and choose a statistical engine before running formal DEG.",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_enrichment_rejects_empty_path(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    result = service.create_preflight(project_id="bio-test", differential_expression_path="")
    assert not result.success
    assert "请选择" in result.message
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED
    assert data_center.list_assets() == []


def test_enrichment_rejects_missing_file(tmp_path) -> None:
    service, task_center, _data_center = make_service(tmp_path)
    result = service.create_preflight(project_id="bio-test", differential_expression_path=str(tmp_path / "missing.json"))
    assert not result.success
    assert "不存在" in result.message
    assert task_center.list_tasks()[0].task_type is TaskType.ANALYSIS


def test_enrichment_rejects_non_json(tmp_path) -> None:
    source = tmp_path / "deg.txt"
    source.write_text("not json", encoding="utf-8")
    service, _task_center, _data_center = make_service(tmp_path)
    result = service.create_preflight(project_id="bio-test", differential_expression_path=str(source))
    assert not result.success
    assert "JSON" in result.message


def test_enrichment_blocks_without_deg_results(tmp_path) -> None:
    service, task_center, data_center = make_service(tmp_path)
    source = write_deg_preflight(tmp_path)
    result = service.create_preflight(project_id="bio-test", differential_expression_path=str(source))
    assert result.success
    assert result.ready_for_enrichment_count == 0
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["enrichment_executed"] is False
    assert payload["database_download_executed"] is False
    assert payload["preflight_items"][0]["status"] == "blocked_no_deg_results"
    task = task_center.list_tasks()[0]
    assert task.status is TaskStatus.COMPLETED
    assert task.task_type is TaskType.ANALYSIS
    assert any(asset.data_type == "geo_enrichment_preflight" for asset in data_center.list_assets("bio-test"))


def test_enrichment_marks_ready_with_gene_lists(tmp_path) -> None:
    service, _task_center, _data_center = make_service(tmp_path)
    source = write_deg_preflight(tmp_path, deg_result_files=["deg.csv"], upregulated_gene_count=12, downregulated_gene_count=8)
    result = service.create_preflight(project_id="bio-test", differential_expression_path=str(source))
    assert result.success
    assert result.ready_for_enrichment_count == 1
    assert result.details["enrichment_executed"] is False
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["network_used"] is False
    assert payload["preflight_items"][0]["status"] == "ready_for_enrichment_runner"


def test_enrichment_feature_status_and_page_state() -> None:
    feature = get_feature("bio-enrichment")
    assert feature is not None
    assert feature.status is FeatureAvailabilityStatus.TESTING
    assert "不下载数据库" in feature.description
    state = initial_enrichment_state()
    assert state.title == "富集分析"
    assert state.status_label == "测试中"
