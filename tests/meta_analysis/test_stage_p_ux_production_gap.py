from __future__ import annotations

from app.meta_analysis.pages.ai_suggestions_page import initial_ai_suggestions_state
from app.meta_analysis.pages.analysis_page import initial_analysis_state
from app.meta_analysis.pages.duplicate_review_page import initial_duplicate_review_state
from app.meta_analysis.pages.extraction_page import initial_extraction_state
from app.meta_analysis.pages.literature_import_page import initial_literature_import_state
from app.meta_analysis.pages.prepare_screening_page import initial_prepare_screening_state
from app.meta_analysis.pages.reporting_page import initial_reporting_state
from app.meta_analysis.pages.screening_page import initial_screening_state
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature


def test_every_meta_page_state_declares_testing_inputs_outputs_next_steps_and_empty_states() -> None:
    states = [
        initial_literature_import_state(),
        initial_prepare_screening_state(),
        initial_duplicate_review_state(),
        initial_screening_state(),
        initial_extraction_state(),
        initial_analysis_state(),
        initial_reporting_state(),
        initial_ai_suggestions_state(),
    ]

    for state in states:
        assert state.status_label == "测试中", state.title
        assert "输入" in state.input_summary, state.title
        assert "输出" in state.output_summary, state.title
        assert "下一步" in state.next_step, state.title
        assert state.empty_state, state.title
        assert any(token in state.warning_summary.lower() for token in ("warning", "错误", "not implemented", "pdf", "suggestion")), state.title


def test_analysis_page_distinguishes_preflight_dataset_run_result_and_advanced_analysis() -> None:
    state = initial_analysis_state()

    assert "preflight" in state.input_summary.lower() or "预检" in state.title
    assert "analysis_ready_dataset" in state.output_summary
    assert "analysis_result" in state.output_summary
    assert "advanced analysis" in state.warning_summary
    assert "network meta" in state.warning_summary.lower()
    assert "not implemented" in state.description


def test_reporting_page_distinguishes_test_summary_formal_markdown_and_testing_exports() -> None:
    state = initial_reporting_state()

    assert "test summary" in state.output_summary
    assert "formal Markdown" in state.warning_summary
    assert "HTML/DOCX testing report" in state.warning_summary
    assert "PDF 正式报告仍未开放" in state.description
    assert "missing / not generated" in state.empty_state


def test_ai_page_marks_suggestions_as_human_confirmed_only() -> None:
    state = initial_ai_suggestions_state()

    assert "候选建议" in state.description
    assert "人工" in state.next_step
    assert "不会直接改正式数据" in state.output_summary
    assert "pending_suggestion_cannot_enter_formal_data" in state.safety_rules
    assert "accepted_suggestion_requires_explicit_apply" in state.safety_rules


def test_no_meta_feature_is_marked_open_or_production_for_internal_beta_candidate() -> None:
    feature_ids = [
        "meta-literature-import",
        "meta-dedup-prep",
        "meta-duplicate-review",
        "meta-screening",
        "meta-extraction",
        "meta-analysis",
        "meta-reporting",
        "meta-ai-assisted-review",
    ]

    for feature_id in feature_ids:
        feature = get_feature(feature_id)
        assert feature is not None
        assert feature.status is FeatureAvailabilityStatus.TESTING
        assert "production" not in feature.description.lower()
