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
    assert step_names == ["数据检索 / 导入", "数据下载", "数据资产识别", "数据清洗", "样本分组", "差异表达分析", "富集分析"]
    assert all(step.next_step for step in steps)


def test_bioinformatics_workspace_includes_geo_import_step() -> None:
    steps = bioinformatics_step_features()
    geo_import = [step for step in steps if step.feature_id == "bio-data-import"]
    assert geo_import
    assert geo_import[0].status.value == "testing"
    assert "GEO 查询计划" in geo_import[0].description


def test_bioinformatics_workspace_includes_geo_download_step() -> None:
    steps = bioinformatics_step_features()
    download = [step for step in steps if step.feature_id == "bio-download"]
    assert download
    assert download[0].status.value == "testing"
    assert "下载计划" in download[0].description


def test_bioinformatics_workspace_includes_geo_asset_detection_step() -> None:
    steps = bioinformatics_step_features()
    asset_detection = [step for step in steps if step.feature_id == "bio-asset-detection"]
    assert asset_detection
    assert asset_detection[0].status.value == "testing"
    assert "不联网" in asset_detection[0].description


def test_bioinformatics_workspace_includes_geo_cleaning_step() -> None:
    steps = bioinformatics_step_features()
    cleaning = [step for step in steps if step.feature_id == "bio-cleaning"]
    assert cleaning
    assert cleaning[0].status.value == "testing"
    assert "清洗预检计划" in cleaning[0].description


def test_bioinformatics_workspace_includes_sample_grouping_step() -> None:
    steps = bioinformatics_step_features()
    grouping = [step for step in steps if step.feature_id == "bio-sample-groups"]
    assert grouping
    assert grouping[0].status.value == "testing"
    assert "样本分组预检" in grouping[0].description


def test_bioinformatics_workspace_includes_differential_expression_step() -> None:
    steps = bioinformatics_step_features()
    deg = [step for step in steps if step.feature_id == "bio-deg"]
    assert deg
    assert deg[0].status.value == "testing"
    assert "不运行正式差异统计" in deg[0].description


def test_bioinformatics_workspace_includes_enrichment_step() -> None:
    steps = bioinformatics_step_features()
    enrichment = [step for step in steps if step.feature_id == "bio-enrichment"]
    assert enrichment
    assert enrichment[0].status.value == "testing"
    assert "不下载数据库" in enrichment[0].description
