from __future__ import annotations

from pathlib import Path

from app.labtools.experiment_templates import (
    EXPERIMENT_TEMPLATE_SCHEMA_VERSION,
    LABTOOLS_EXPERIMENT_RECORD_DRAFT_STORE_SCHEMA_VERSION,
)
from app.labtools.image_analysis.export_package import LABTOOLS_ROI_EXPORT_SCHEMA_VERSION
from app.labtools.recipes import LABTOOLS_RECIPE_DRAFT_STORE_SCHEMA_VERSION


def test_labtools_schema_index_lists_current_schema_versions_and_boundaries() -> None:
    text = Path("docs/labtools_schema_index.md").read_text(encoding="utf-8")

    for schema in (
        LABTOOLS_ROI_EXPORT_SCHEMA_VERSION,
        LABTOOLS_RECIPE_DRAFT_STORE_SCHEMA_VERSION,
        EXPERIMENT_TEMPLATE_SCHEMA_VERSION,
        LABTOOLS_EXPERIMENT_RECORD_DRAFT_STORE_SCHEMA_VERSION,
        "CalculationRecord",
        "RecipeDraft",
    ):
        assert schema in text

    for phrase in (
        "是否可公开分享",
        "是否包含本地路径",
        "不自动保存",
        "no silent overwrite",
        "manual-review",
        "不构成自动图像算法结论",
        "不是完整 ELN",
        "不是正式 SOP",
        "不是生产级",
        "不替代实验室 SOP",
    ):
        assert phrase in text


def test_labtools_schema_index_marks_public_sharing_and_local_path_risk() -> None:
    text = Path("docs/labtools_schema_index.md").read_text(encoding="utf-8")

    assert "不建议直接作为公开报告分享" in text
    assert "不建议公开" in text
    assert "Markdown fragment 不应包含 raw absolute source path" in text
    assert "用户填写的 `output_files` 可能包含本地文件名或路径片段" in text
