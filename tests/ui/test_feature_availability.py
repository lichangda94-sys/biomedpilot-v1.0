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
    open_registry_names = {
        item.feature_name
        for item in list_features()
        if item.status is FeatureAvailabilityStatus.OPEN
    }
    assert unavailable_registry_names.isdisjoint(open_registry_names)


def test_feature_registry_exposes_key_statuses() -> None:
    geo_import = get_feature("bio-data-import")
    geo_download = get_feature("bio-download")
    geo_asset_detection = get_feature("bio-asset-detection")
    geo_cleaning = get_feature("bio-cleaning")
    sample_grouping = get_feature("bio-sample-groups")
    deg = get_feature("bio-deg")
    enrichment = get_feature("bio-enrichment")
    correlation = get_feature("bio-correlation")
    survival = get_feature("bio-survival")
    meta_import = get_feature("meta-literature-import")
    prepare = get_feature("meta-dedup-prep")
    duplicate_review = get_feature("meta-duplicate-review")
    screening = get_feature("meta-screening")
    extraction = get_feature("meta-extraction")
    analysis = get_feature("meta-analysis")
    reporting = get_feature("meta-reporting")
    project_center = get_feature("shared-project-center")
    assert geo_import is not None
    assert geo_import.status is FeatureAvailabilityStatus.TESTING
    assert "GEO 查询计划" in geo_import.description
    assert geo_download is not None
    assert geo_download.status is FeatureAvailabilityStatus.TESTING
    assert "下载计划" in geo_download.description
    assert geo_asset_detection is not None
    assert geo_asset_detection.status is FeatureAvailabilityStatus.TESTING
    assert "不联网" in geo_asset_detection.description
    assert geo_cleaning is not None
    assert geo_cleaning.status is FeatureAvailabilityStatus.TESTING
    assert "清洗预检计划" in geo_cleaning.description
    assert sample_grouping is not None
    assert sample_grouping.status is FeatureAvailabilityStatus.TESTING
    assert "样本分组预检" in sample_grouping.description
    assert deg is not None
    assert deg.status is FeatureAvailabilityStatus.TESTING
    assert "不运行正式差异统计" in deg.description
    assert enrichment is not None
    assert enrichment.status is FeatureAvailabilityStatus.TESTING
    assert "不下载数据库" in enrichment.description
    assert correlation is not None
    assert correlation.status is FeatureAvailabilityStatus.TESTING
    assert "不计算相关系数" in correlation.description
    assert survival is not None
    assert survival.status is FeatureAvailabilityStatus.TESTING
    assert "不计算 Kaplan-Meier" in survival.description
    assert meta_import is not None
    assert meta_import.legacy_source
    assert prepare is not None
    assert prepare.status is FeatureAvailabilityStatus.TESTING
    assert duplicate_review is not None
    assert duplicate_review.status is FeatureAvailabilityStatus.TESTING
    assert screening is not None
    assert screening.status is FeatureAvailabilityStatus.TESTING
    assert "include/exclude/maybe" in screening.description
    assert extraction is not None
    assert extraction.status is FeatureAvailabilityStatus.TESTING
    assert "提取池" in extraction.description
    assert analysis is not None
    assert analysis.status is FeatureAvailabilityStatus.TESTING
    assert "预检" in analysis.description
    assert reporting is not None
    assert reporting.status is FeatureAvailabilityStatus.TESTING
    assert "Markdown" in reporting.description
    assert project_center is not None
    assert project_center.status is FeatureAvailabilityStatus.OPEN
    assert list_features("bioinformatics")
