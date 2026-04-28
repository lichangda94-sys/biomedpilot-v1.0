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


def test_meta_workspace_includes_prepare_screening_step() -> None:
    steps = meta_analysis_step_features()
    prepare = [step for step in steps if step.feature_id == "meta-dedup-prep"]
    assert prepare
    assert prepare[0].feature_name == "去重准备"
    assert prepare[0].status.value == "testing"


def test_meta_workspace_includes_duplicate_review_step() -> None:
    steps = meta_analysis_step_features()
    duplicate_review = [step for step in steps if step.feature_id == "meta-duplicate-review"]
    assert duplicate_review
    assert duplicate_review[0].feature_name == "Duplicate Review"
    assert duplicate_review[0].status.value == "testing"


def test_meta_workspace_includes_screening_step() -> None:
    steps = meta_analysis_step_features()
    screening = [step for step in steps if step.feature_id == "meta-screening"]
    assert screening
    assert screening[0].feature_name == "Screening"
    assert screening[0].status.value == "testing"


def test_meta_workspace_includes_extraction_step() -> None:
    steps = meta_analysis_step_features()
    extraction = [step for step in steps if step.feature_id == "meta-extraction"]
    assert extraction
    assert extraction[0].feature_name == "Extraction"
    assert extraction[0].status.value == "testing"


def test_meta_workspace_includes_analysis_step() -> None:
    steps = meta_analysis_step_features()
    analysis = [step for step in steps if step.feature_id == "meta-analysis"]
    assert analysis
    assert analysis[0].feature_name == "Analysis"
    assert analysis[0].status.value == "testing"


def test_meta_workspace_includes_reporting_step() -> None:
    steps = meta_analysis_step_features()
    reporting = [step for step in steps if step.feature_id == "meta-reporting"]
    assert reporting
    assert reporting[0].feature_name == "Reporting"
    assert reporting[0].status.value == "testing"
