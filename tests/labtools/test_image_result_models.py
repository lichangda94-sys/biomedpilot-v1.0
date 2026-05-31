from __future__ import annotations

import pytest

from app.labtools.image_analysis.result_models import ImageAnalysisResult, placeholder_result


def test_placeholder_result_has_no_quantitative_metrics() -> None:
    result = placeholder_result("task-1", "fluorescence_intensity")
    payload = result.to_dict()

    assert result.status == "algorithm_not_available"
    assert payload["metrics"] == {}
    assert "算法开发中" in payload["warnings"][0]
    assert "请勿将占位状态作为实验结果" in payload["review_notice"]


def test_result_model_rejects_completed_or_metric_payloads() -> None:
    with pytest.raises(ValueError, match="不允许创建 completed"):
        ImageAnalysisResult(task_id="task-1", result_type="cell_counting", status="completed")

    with pytest.raises(ValueError, match="不允许生成面积"):
        ImageAnalysisResult(task_id="task-1", result_type="cell_counting", metrics={"cell_count": 10})
