from __future__ import annotations

import math
from pathlib import Path

from app.meta_analysis.models.effect_size_normalization import NORMALIZATION_STATUS_READY, NormalizedEffectSizeInput
from app.meta_analysis.models.pairwise_meta_executor import PairwiseMetaExecutorResult
from app.meta_analysis.models.result_review import (
    REVIEW_STATE_ACCEPTED_FOR_REPORT,
    REVIEW_STATE_IN_REVIEW,
    REVIEW_STATE_NEEDS_REVISION,
    REVIEW_STATE_NOT_REVIEWED,
    REVIEW_STATE_REJECTED_FOR_REPORT,
    result_review_label_zh,
)
from app.meta_analysis.models.statistical_result_state import (
    STATISTICAL_RESULT_STATE_COMPUTED,
    STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN,
    STATISTICAL_RESULT_STATE_FAILED_VALIDATION,
    STATISTICAL_RESULT_STATE_REPORT_READY,
    STATISTICAL_RESULT_STATE_TESTING_LEVEL,
    STATISTICAL_RESULT_STATE_USER_REVIEWED,
    is_report_ready_result,
)
from app.meta_analysis.pages.analysis_page import analysis_setup_state_from_project
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder
from app.meta_analysis.services.pairwise_meta_executor_service import PairwiseMetaExecutorService
from app.meta_analysis.services.result_review_service import StatisticalResultReviewService


def test_m13_default_computed_result_is_not_reviewed() -> None:
    result = _computed_result()
    review = StatisticalResultReviewService().default_review(result)

    assert result.result_state == STATISTICAL_RESULT_STATE_COMPUTED
    assert result.review_state == REVIEW_STATE_NOT_REVIEWED
    assert review.review_state == REVIEW_STATE_NOT_REVIEWED
    assert result_review_label_zh(review.review_state) == "尚未审核"


def test_m13_computed_result_can_enter_in_review(tmp_path: Path) -> None:
    service = StatisticalResultReviewService()
    result = _computed_result()

    transition = service.start_review(tmp_path, result, reviewer_role="reviewer", review_notes="checking inputs")

    assert transition.success is True
    assert transition.review.review_state == REVIEW_STATE_IN_REVIEW
    assert service.load_review(tmp_path).review_state == REVIEW_STATE_IN_REVIEW


def test_m13_computed_result_can_be_accepted_for_report_with_acknowledged_warnings(tmp_path: Path) -> None:
    service = StatisticalResultReviewService()
    result = _computed_result()

    transition = service.accept_for_report(tmp_path, result, reviewer_role="reviewer", review_notes="accepted for draft", warnings_acknowledged=True)
    latest = PairwiseMetaExecutorService().load_latest_result(tmp_path)

    assert transition.success is True
    assert transition.review.review_state == REVIEW_STATE_ACCEPTED_FOR_REPORT
    assert transition.review.review_warnings_acknowledged is True
    assert transition.review.warnings_visible == result.warnings
    assert latest is not None
    assert latest.result_state == STATISTICAL_RESULT_STATE_USER_REVIEWED
    assert latest.report_ready is False


def test_m13_computed_result_can_be_marked_needs_revision_or_rejected(tmp_path: Path) -> None:
    service = StatisticalResultReviewService()
    result = _computed_result()

    needs_revision = service.mark_needs_revision(tmp_path / "needs", result, reviewer_role="reviewer", review_notes="missing input check")
    rejected = service.reject_for_report(tmp_path / "rejected", result, reviewer_role="reviewer", review_notes="do not use")

    assert needs_revision.review.review_state == REVIEW_STATE_NEEDS_REVISION
    assert "review_state:needs_revision" in needs_revision.blockers
    assert rejected.review.review_state == REVIEW_STATE_REJECTED_FOR_REPORT
    assert "review_state:rejected_for_report" in rejected.blockers


def test_m13_computed_without_review_cannot_become_report_ready(tmp_path: Path) -> None:
    result = _computed_result()
    PairwiseMetaExecutorService().save_result(tmp_path, result)

    transition = StatisticalResultReviewService().grant_report_ready(tmp_path, result, reviewer_role="reviewer")

    assert transition.success is False
    assert "user_reviewed_result_required:computed" in transition.blockers
    assert "accepted_for_report_review_required:not_reviewed" in transition.blockers


def test_m13_accepted_with_acknowledged_warnings_can_become_report_ready(tmp_path: Path) -> None:
    service = StatisticalResultReviewService()
    result = _computed_result()

    accepted = service.accept_for_report(tmp_path, result, reviewer_role="reviewer", review_notes="accepted", warnings_acknowledged=True)
    requested = service.request_report_ready(tmp_path, accepted.result_payload, reviewer_role="reviewer")
    granted = service.grant_report_ready(tmp_path, requested.result_payload, reviewer_role="reviewer")
    latest = PairwiseMetaExecutorService().load_latest_result(tmp_path)

    assert accepted.success is True
    assert requested.success is True
    assert granted.success is True
    assert granted.review.report_ready_granted is True
    assert latest is not None
    assert latest.result_state == STATISTICAL_RESULT_STATE_REPORT_READY
    assert is_report_ready_result(latest)


def test_m13_unresolved_critical_warnings_block_report_ready(tmp_path: Path) -> None:
    service = StatisticalResultReviewService()
    result = _computed_result(warnings=["developer_preview_testing_only", "critical_warning:input_assumption_unresolved"])

    accepted = service.accept_for_report(tmp_path, result, reviewer_role="reviewer", review_notes="accepted", warnings_acknowledged=True)
    grant = service.grant_report_ready(tmp_path, accepted.result_payload, reviewer_role="reviewer")

    assert accepted.success is False
    assert "critical_warnings_block_report_ready" in accepted.blockers
    assert grant.success is False
    assert "critical_warnings_block_report_ready" in grant.blockers


def test_m13_failed_testing_configured_rejected_and_revision_states_cannot_be_report_ready(tmp_path: Path) -> None:
    service = StatisticalResultReviewService()
    for index, state in enumerate((STATISTICAL_RESULT_STATE_FAILED_VALIDATION, STATISTICAL_RESULT_STATE_TESTING_LEVEL, STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN)):
        payload = {"result_state": state, "testing_level": state == STATISTICAL_RESULT_STATE_TESTING_LEVEL}
        transition = service.grant_report_ready(tmp_path / f"state-{index}", payload, reviewer_role="reviewer")
        assert transition.success is False
        assert transition.blockers

    result = _computed_result()
    rejected = service.reject_for_report(tmp_path / "rejected", result, reviewer_role="reviewer")
    reject_grant = service.grant_report_ready(tmp_path / "rejected", rejected.result_payload, reviewer_role="reviewer")
    revision = service.mark_needs_revision(tmp_path / "revision", result, reviewer_role="reviewer")
    revision_grant = service.grant_report_ready(tmp_path / "revision", revision.result_payload, reviewer_role="reviewer")

    assert reject_grant.success is False
    assert "accepted_for_report_review_required:rejected_for_report" in reject_grant.blockers
    assert revision_grant.success is False
    assert "accepted_for_report_review_required:needs_revision" in revision_grant.blockers


def test_m13_warning_acknowledgement_keeps_warnings_visible(tmp_path: Path) -> None:
    service = StatisticalResultReviewService()
    result = _computed_result(warnings=["developer_preview_testing_only", "fixed_effect_inverse_variance_mvp"])

    blocked = service.accept_for_report(tmp_path / "blocked", result, reviewer_role="reviewer", review_notes="accepted", warnings_acknowledged=False)
    accepted = service.accept_for_report(tmp_path / "accepted", result, reviewer_role="reviewer", review_notes="accepted", warnings_acknowledged=True)

    assert blocked.success is False
    assert "warnings_must_be_acknowledged" in blocked.blockers
    assert accepted.review.review_warnings_acknowledged is True
    assert accepted.review.warnings_visible == result.warnings


def test_m13_report_builder_describes_computed_reviewed_and_report_ready_states(tmp_path: Path) -> None:
    pairwise = PairwiseMetaExecutorService()
    review = StatisticalResultReviewService()
    computed_dir = tmp_path / "computed"
    reviewed_dir = tmp_path / "reviewed"
    ready_dir = tmp_path / "ready"

    pairwise.save_result(computed_dir, _computed_result())
    computed_report = FormalMarkdownReportBuilder().build_draft_markdown_report(computed_dir).read_text(encoding="utf-8")

    accepted = review.accept_for_report(reviewed_dir, _computed_result(), reviewer_role="reviewer", review_notes="accepted", warnings_acknowledged=True)
    reviewed_report = FormalMarkdownReportBuilder().build_draft_markdown_report(reviewed_dir).read_text(encoding="utf-8")

    ready_accepted = review.accept_for_report(ready_dir, _computed_result(), reviewer_role="reviewer", review_notes="accepted", warnings_acknowledged=True)
    requested = review.request_report_ready(ready_dir, ready_accepted.result_payload, reviewer_role="reviewer")
    granted = review.grant_report_ready(ready_dir, requested.result_payload, reviewer_role="reviewer")
    ready_report = FormalMarkdownReportBuilder().build_draft_markdown_report(ready_dir).read_text(encoding="utf-8")

    assert "统计结果已计算但尚未完成用户审核，不能作为正式报告结论。" in computed_report
    assert "统计结果已完成用户审核，但尚未标记为报告就绪。" in reviewed_report
    assert granted.success is True
    assert "报告就绪统计结果（Developer Preview / testing）" in ready_report
    assert "production-ready" not in ready_report
    assert "pairwise-result-" not in ready_report
    assert str(tmp_path) not in ready_report


def test_m13_failed_and_testing_reports_never_emit_formal_conclusion(tmp_path: Path) -> None:
    pairwise = PairwiseMetaExecutorService()
    failed = PairwiseMetaExecutorResult(result_state=STATISTICAL_RESULT_STATE_FAILED_VALIDATION, validation_errors=["confirmed_analysis_plan_required"])
    testing = PairwiseMetaExecutorResult(result_state=STATISTICAL_RESULT_STATE_TESTING_LEVEL, testing_level=True, formal_computed=False)
    pairwise.save_result(tmp_path / "failed", failed)
    pairwise.save_result(tmp_path / "testing", testing)

    failed_report = FormalMarkdownReportBuilder().build_draft_markdown_report(tmp_path / "failed").read_text(encoding="utf-8")
    testing_report = FormalMarkdownReportBuilder().build_draft_markdown_report(tmp_path / "testing").read_text(encoding="utf-8")

    assert "输入校验失败" in failed_report
    assert "仅展示错误摘要" in failed_report
    assert "测试级结果" in testing_report
    assert "不能作为正式结论" in testing_report
    assert "正式发表结论" not in failed_report


def test_m13_analysis_page_state_exposes_review_labels_without_raw_internals(tmp_path: Path) -> None:
    review = StatisticalResultReviewService()
    accepted = review.accept_for_report(tmp_path, _computed_result(), reviewer_role="reviewer", review_notes="accepted", warnings_acknowledged=True)
    review.request_report_ready(tmp_path, accepted.result_payload, reviewer_role="reviewer")

    state = analysis_setup_state_from_project(tmp_path)
    rendered = str(state.result_review_summary)

    assert "统计结果审核" in rendered
    assert "接受进入报告草稿" in rendered
    assert "阻止进入报告的原因" in rendered
    assert "pairwise-result-" not in rendered
    assert str(tmp_path) not in rendered
    assert "raw JSON" not in rendered


def _computed_result(*, warnings: list[str] | None = None) -> PairwiseMetaExecutorResult:
    result = PairwiseMetaExecutorService().execute_from_inputs(
        confirmed_plan={
            "plan_state": "confirmed",
            "confirmed_analysis_plan_id": "safe-plan",
            "confirmed_effect_measure": "MD",
            "effect_measure_type": "MD",
            "confirmed_model": "fixed_effect",
        },
        normalized_records=[_effect("Study A", 0.2, 0.04), _effect("Study B", 0.5, 0.01)],
        project_name="safe-project",
    )
    if warnings is None:
        return result
    return PairwiseMetaExecutorResult(**{**result.to_dict(), "warnings": warnings})


def _effect(label: str, estimate: float, variance: float) -> NormalizedEffectSizeInput:
    return NormalizedEffectSizeInput(
        study_label=label,
        effect_measure_type="MD",
        estimate=estimate,
        standard_error=math.sqrt(variance),
        variance=variance,
        source_state="confirmed",
        normalization_status=NORMALIZATION_STATUS_READY,
    )
