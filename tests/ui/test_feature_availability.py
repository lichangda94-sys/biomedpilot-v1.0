from __future__ import annotations

from app.bioinformatics.workspace import bioinformatics_features
from app.meta_analysis.workspace import meta_analysis_features
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature, list_features
from app.shared.feature_status import FeatureStatus


def test_unavailable_features_are_not_marked_open() -> None:
    features = bioinformatics_features() + meta_analysis_features()
    assert all(item.status.value in {"已开放", "测试中", "待接入", "暂未开放"} for item in features)
    unavailable_registry_names = {
        item.feature_name
        for item in list_features()
        if item.status is FeatureAvailabilityStatus.UNAVAILABLE
    }
    assert "富集分析" in unavailable_registry_names


def test_feature_registry_exposes_key_statuses() -> None:
    geo_import = get_feature("bio-data-import")
    meta_import = get_feature("meta-literature-import")
    prepare = get_feature("meta-dedup-prep")
    duplicate_review = get_feature("meta-duplicate-review")
    screening = get_feature("meta-screening")
    project_center = get_feature("shared-project-center")
    assert geo_import is not None
    assert geo_import.status is FeatureAvailabilityStatus.TESTING
    assert meta_import is not None
    assert meta_import.legacy_source
    assert prepare is not None
    assert prepare.status is FeatureAvailabilityStatus.TESTING
    assert duplicate_review is not None
    assert duplicate_review.status is FeatureAvailabilityStatus.TESTING
    assert screening is not None
    assert screening.status is FeatureAvailabilityStatus.TESTING
    assert "pending" in screening.description
    assert project_center is not None
    assert project_center.status is FeatureAvailabilityStatus.OPEN
    assert list_features("bioinformatics")
