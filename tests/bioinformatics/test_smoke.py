from __future__ import annotations

from app.bioinformatics.workspace import bioinformatics_features, bioinformatics_step_features
from app.shared.feature_status import FeatureStatus


def test_bioinformatics_feature_statuses_are_explicit() -> None:
    features = bioinformatics_features()
    assert any(feature.name == "数据检索 / 导入" for feature in features)
    assert {feature.status for feature in features} <= set(FeatureStatus)
    assert all(feature.description for feature in features)


def test_bioinformatics_workspace_steps_are_visible() -> None:
    steps = bioinformatics_step_features()
    step_names = [step.feature_name for step in steps]
    assert step_names == ["数据检索 / 导入", "数据下载", "数据资产识别", "数据清洗", "样本分组"]
    assert all(step.next_step for step in steps)


def test_bioinformatics_workspace_includes_geo_import_step() -> None:
    steps = bioinformatics_step_features()
    geo_import = [step for step in steps if step.feature_id == "bio-data-import"]
    assert geo_import
    assert geo_import[0].status.value == "testing"
    assert "GEO 查询计划" in geo_import[0].description
