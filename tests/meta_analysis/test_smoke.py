from __future__ import annotations

from app.meta_analysis.workspace import meta_analysis_features, meta_analysis_step_features
from app.shared.feature_status import FeatureStatus


def test_meta_analysis_feature_statuses_are_explicit() -> None:
    features = meta_analysis_features()
    assert any(feature.name == "文献导入" for feature in features)
    assert {feature.status for feature in features} <= set(FeatureStatus)
    assert all(feature.description for feature in features)


def test_meta_analysis_workspace_steps_are_visible() -> None:
    steps = meta_analysis_step_features()
    step_names = [step.feature_name for step in steps]
    assert step_names == [
        "文献导入",
        "去重准备",
        "Duplicate Review",
        "Screening",
        "Extraction",
        "Analysis",
        "Reporting",
    ]
    assert all(step.next_step for step in steps)


def test_meta_workspace_includes_literature_import_step() -> None:
    steps = meta_analysis_step_features()
    literature_import = [step for step in steps if step.feature_id == "meta-literature-import"]
    assert literature_import
    assert literature_import[0].status.value == "testing"
