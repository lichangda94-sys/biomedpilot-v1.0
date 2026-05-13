from __future__ import annotations

import pytest

from app.labtools.image_analysis.analysis_task import TASK_TYPES, ImageAnalysisTask, create_analysis_task
from app.labtools.image_analysis.image_io import create_image_record
from app.labtools.image_analysis.image_models import ImageAnalysisError


def test_create_analysis_task_defaults_to_draft_without_image() -> None:
    task = create_analysis_task("wound_healing")

    payload = task.to_dict()

    assert task.status == "draft"
    assert payload["task_label"] == TASK_TYPES["wound_healing"]
    assert payload["result_records"][0]["status"] == "algorithm_not_available"
    assert payload["result_records"][0]["metrics"] == {}
    assert payload["roi_records"][0]["roi_type"] == "not_configured"


def test_create_analysis_task_with_image_is_pending_configuration(tmp_path) -> None:
    image_path = tmp_path / "cells.png"
    image_path.write_bytes(b"image")
    record = create_image_record(image_path)

    task = create_analysis_task("cell_counting", (record,))

    assert task.status == "pending_configuration"
    assert task.image_records == (record,)
    assert task.result_records[0].status == "algorithm_not_available"


def test_image_analysis_task_rejects_completed_status() -> None:
    with pytest.raises(ImageAnalysisError, match="不允许创建 completed"):
        ImageAnalysisTask(task_type="densitometry", status="completed")


def test_image_analysis_task_rejects_unknown_type() -> None:
    with pytest.raises(ImageAnalysisError, match="暂不支持该图像分析任务类型"):
        create_analysis_task("unknown")
