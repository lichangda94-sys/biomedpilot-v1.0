from __future__ import annotations

from app.meta_analysis.pages.analysis_page import initial_analysis_state
from app.meta_analysis.pages.duplicate_review_page import initial_duplicate_review_state
from app.meta_analysis.pages.extraction_page import initial_extraction_state
from app.meta_analysis.pages.literature_import_page import initial_literature_import_state
from app.meta_analysis.pages.prepare_screening_page import initial_prepare_screening_state
from app.meta_analysis.pages.reporting_page import initial_reporting_state
from app.meta_analysis.pages.screening_page import initial_screening_state
from app.meta_analysis.workspace import meta_analysis_step_features
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from app.shared.task_center.service import TaskType


EXPECTED_META_STEP_IDS = (
    "meta-literature-import",
    "meta-dedup-prep",
    "meta-duplicate-review",
    "meta-screening",
    "meta-extraction",
    "meta-analysis",
    "meta-reporting",
)

EXPECTED_DATA_CENTER_TYPES = {
    "literature_records",
    "screening_ready_records",
    "duplicate_candidate_groups",
    "deduplicated_literature",
    "screening_queue",
    "screening_decisions",
    "extraction_pool",
    "analysis_preflight",
    "meta_analysis_report",
}

EXPECTED_TASK_TYPES = {
    "literature_import",
    "prepare_screening",
    "duplicate_review",
    "dedup_decision",
    "screening",
    "screening_decision",
    "extraction",
    "analysis",
    "report_export",
}


def test_meta_developer_preview_chain_has_seven_testing_steps() -> None:
    steps = meta_analysis_step_features()
    assert tuple(step.feature_id for step in steps) == EXPECTED_META_STEP_IDS
    assert {step.status for step in steps} == {FeatureAvailabilityStatus.TESTING}
    assert not any(step.status is FeatureAvailabilityStatus.OPEN for step in steps)


def test_meta_page_states_are_testing_and_developer_preview_scoped() -> None:
    states = [
        initial_literature_import_state(),
        initial_prepare_screening_state(),
        initial_duplicate_review_state(),
        initial_screening_state(),
        initial_extraction_state(),
        initial_analysis_state(),
        initial_reporting_state(),
    ]
    assert all(state.title for state in states)
    assert all(state.description for state in states)
    assert all(state.status_label == "测试中" for state in states)
    assert "预检" in initial_analysis_state().title
    assert "testing pooled effect" in initial_analysis_state().description
    assert "测试版 Markdown 摘要" in initial_reporting_state().description
    assert "不导出正式论文报告" in initial_reporting_state().description


def test_meta_feature_availability_matches_current_testing_scope() -> None:
    for feature_id in EXPECTED_META_STEP_IDS:
        feature = get_feature(feature_id)
        assert feature is not None
        assert feature.module == "meta_analysis"
        assert feature.status is FeatureAvailabilityStatus.TESTING
        assert feature.next_step


def test_meta_data_center_types_remain_documented_in_services() -> None:
    service_modules = (
        "app.meta_analysis.services.literature_import_service",
        "app.meta_analysis.services.prepare_screening_service",
        "app.meta_analysis.services.duplicate_review_service",
        "app.meta_analysis.services.dedup_decision_service",
        "app.meta_analysis.services.screening_service",
        "app.meta_analysis.services.extraction_service",
        "app.meta_analysis.services.analysis_service",
        "app.meta_analysis.services.reporting_service",
    )
    module_text = "\n".join(_module_source(module_name) for module_name in service_modules)
    for data_type in EXPECTED_DATA_CENTER_TYPES:
        assert data_type in module_text


def test_meta_task_center_types_remain_available() -> None:
    assert EXPECTED_TASK_TYPES <= {task_type.value for task_type in TaskType}


def test_meta_analysis_and_reporting_are_not_formal_outputs() -> None:
    analysis = get_feature("meta-analysis")
    reporting = get_feature("meta-reporting")
    assert analysis is not None
    assert reporting is not None
    assert "testing pooled effect" in analysis.description
    assert "不是生产级正式 Meta 统计" in analysis.description
    assert "测试版 Markdown 摘要" in reporting.description
    assert "正式报告和图表包尚未开放" in reporting.description


def _module_source(module_name: str) -> str:
    module = __import__(module_name, fromlist=["__file__"])
    path = module.__file__
    assert path is not None
    with open(path, encoding="utf-8") as handle:
        return handle.read()
