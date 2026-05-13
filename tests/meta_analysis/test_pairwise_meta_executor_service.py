from __future__ import annotations

import math
from pathlib import Path

import pytest

from app.meta_analysis.models.effect_size_normalization import NORMALIZATION_STATUS_INCOMPLETE, NORMALIZATION_STATUS_READY, NormalizedEffectSizeInput
from app.meta_analysis.models.pairwise_meta_executor import PairwiseMetaExecutorConfig
from app.meta_analysis.models.statistical_result_state import (
    STATISTICAL_RESULT_STATE_COMPUTED,
    STATISTICAL_RESULT_STATE_FAILED_VALIDATION,
    STATISTICAL_RESULT_STATE_REPORT_READY,
    blocks_formal_report_claim,
    can_enter_report_ready_state,
    is_report_ready_result,
    requires_user_review,
)
from app.meta_analysis.pages.analysis_page import analysis_setup_state_from_project
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder
from app.meta_analysis.services.pairwise_meta_executor_service import PairwiseMetaExecutorService


def test_m12_missing_confirmed_plan_fails_validation() -> None:
    result = PairwiseMetaExecutorService().execute_from_inputs(confirmed_plan={}, normalized_records=[_effect("A", 0.2, 0.04), _effect("B", 0.5, 0.01)])

    assert result.result_state == STATISTICAL_RESULT_STATE_FAILED_VALIDATION
    assert result.pooled_effect is None
    assert "confirmed_analysis_plan_required" in result.validation_errors
    assert blocks_formal_report_claim(result)


def test_m12_fewer_than_two_ready_studies_fails_validation() -> None:
    result = PairwiseMetaExecutorService().execute_from_inputs(confirmed_plan=_plan("OR"), normalized_records=[_effect("A", 0.2, 0.04)])

    assert result.result_state == STATISTICAL_RESULT_STATE_FAILED_VALIDATION
    assert "at_least_two_ready_normalized_studies_required" in result.validation_errors
    assert result.pooled_effect is None


def test_m12_inconsistent_effect_type_fails_validation() -> None:
    records = [_effect("A", 0.2, 0.04, measure="OR"), _effect("B", 0.5, 0.01, measure="RR")]

    result = PairwiseMetaExecutorService().execute_from_inputs(confirmed_plan=_plan("OR"), normalized_records=records)

    assert result.result_state == STATISTICAL_RESULT_STATE_FAILED_VALIDATION
    assert "normalized_effect_type_must_match_confirmed_plan" in result.validation_errors or "consistent_effect_measure_type_required" in result.validation_errors


def test_m12_missing_variance_or_standard_error_fails_validation() -> None:
    records = [
        _effect("A", 0.2, 0.04),
        NormalizedEffectSizeInput(study_label="B", effect_measure_type="OR", log_estimate=0.5, standard_error=None, variance=None, source_state="confirmed", normalization_status=NORMALIZATION_STATUS_READY),
    ]

    result = PairwiseMetaExecutorService().execute_from_inputs(confirmed_plan=_plan("OR"), normalized_records=records)

    assert result.result_state == STATISTICAL_RESULT_STATE_FAILED_VALIDATION
    assert "finite_numeric_estimate_se_variance_required" in result.validation_errors


def test_m12_draft_or_suggested_records_are_excluded_and_not_enough_ready_fails() -> None:
    records = [
        _effect("A", 0.2, 0.04),
        _effect("B", 0.5, 0.01, source_state="suggested"),
        NormalizedEffectSizeInput(study_label="C", effect_measure_type="OR", source_state="confirmed", normalization_status=NORMALIZATION_STATUS_INCOMPLETE),
    ]

    result = PairwiseMetaExecutorService().execute_from_inputs(confirmed_plan=_plan("OR"), normalized_records=records)

    assert result.result_state == STATISTICAL_RESULT_STATE_FAILED_VALIDATION
    assert "at_least_two_ready_normalized_studies_required" in result.validation_errors
    assert {item["reason"] for item in result.excluded_studies} >= {"source_row_not_confirmed", "normalization_status:incomplete"}


def test_m12_non_finite_numeric_values_are_rejected() -> None:
    result = PairwiseMetaExecutorService().execute_from_inputs(
        confirmed_plan=_plan("OR"),
        normalized_records=[_effect("A", 0.2, 0.04), _effect("B", math.inf, 0.01)],
    )

    assert result.result_state == STATISTICAL_RESULT_STATE_FAILED_VALIDATION
    assert "finite_numeric_estimate_se_variance_required" in result.validation_errors


def test_m12_fixed_effect_inverse_variance_pooling_and_counts() -> None:
    result = PairwiseMetaExecutorService().execute_from_inputs(
        confirmed_plan=_plan("MD"),
        normalized_records=[
            _effect("A", 0.2, 0.04, measure="MD"),
            _effect("B", 0.5, 0.01, measure="MD"),
            NormalizedEffectSizeInput(study_label="C", effect_measure_type="MD", source_state="confirmed", normalization_status=NORMALIZATION_STATUS_INCOMPLETE),
        ],
    )

    pooled = ((1 / 0.04) * 0.2 + (1 / 0.01) * 0.5) / ((1 / 0.04) + (1 / 0.01))
    se = math.sqrt(1 / ((1 / 0.04) + (1 / 0.01)))

    assert result.result_state == STATISTICAL_RESULT_STATE_COMPUTED
    assert result.model_used == "fixed_effect"
    assert result.pooled_effect == pytest.approx(pooled)
    assert result.pooled_standard_error == pytest.approx(se)
    assert result.pooled_ci_lower == pytest.approx(pooled - 1.96 * se)
    assert result.pooled_ci_upper == pytest.approx(pooled + 1.96 * se)
    assert result.z_value == pytest.approx(pooled / se)
    assert result.p_value is not None and 0 <= result.p_value <= 1
    assert len(result.included_studies) == 2
    assert len(result.excluded_studies) == 1
    assert result.formal_computed is True
    assert result.report_ready is False


def test_m12_ratio_measures_preserve_log_scale_and_back_transform() -> None:
    result = PairwiseMetaExecutorService().execute_from_inputs(
        confirmed_plan=_plan("OR"),
        normalized_records=[_ratio_effect("A", 1.5, 0.04), _ratio_effect("B", 2.0, 0.01)],
    )

    assert result.result_state == STATISTICAL_RESULT_STATE_COMPUTED
    assert result.effect_scale == "log"
    assert result.pooled_effect is not None
    assert result.back_transformed_effect == pytest.approx(math.exp(result.pooled_effect))
    assert result.back_transformed_ci_lower == pytest.approx(math.exp(result.pooled_ci_lower))
    assert result.back_transformed_ci_upper == pytest.approx(math.exp(result.pooled_ci_upper))


def test_m12_heterogeneity_q_df_i2_and_zero_q_safe() -> None:
    result = PairwiseMetaExecutorService().execute_from_inputs(
        confirmed_plan=_plan("MD"),
        normalized_records=[_effect("A", 0.2, 0.04, measure="MD"), _effect("B", 0.5, 0.01, measure="MD")],
    )
    identical = PairwiseMetaExecutorService().execute_from_inputs(
        confirmed_plan=_plan("MD"),
        normalized_records=[_effect("A", 0.2, 0.04, measure="MD"), _effect("B", 0.2, 0.01, measure="MD")],
    )

    assert result.heterogeneity_summary["q"] >= 0
    assert result.heterogeneity_summary["df"] == 1
    assert 0 <= result.heterogeneity_summary["i_squared"] <= 100
    assert identical.heterogeneity_summary["q"] == pytest.approx(0)
    assert identical.heterogeneity_summary["i_squared"] == 0


def test_m12_result_state_requires_user_review_before_report_ready() -> None:
    service = PairwiseMetaExecutorService()
    result = service.execute_from_inputs(confirmed_plan=_plan("MD"), normalized_records=[_effect("A", 0.2, 0.04, measure="MD"), _effect("B", 0.5, 0.01, measure="MD")])

    assert result.result_state == STATISTICAL_RESULT_STATE_COMPUTED
    assert requires_user_review(result)
    assert not can_enter_report_ready_state(result).allowed
    reviewed = service.mark_user_reviewed({**result.to_dict(), "review_decision": "accepted_for_report", "review_warnings_acknowledged": True}, actor="reviewer")
    report_ready = service.mark_report_ready({**reviewed.to_dict(), "report_ready_requested": True}, actor="reviewer")
    failed = service.execute_from_inputs(confirmed_plan={}, normalized_records=[])

    assert reviewed.result_state == "user_reviewed"
    assert report_ready.result_state == STATISTICAL_RESULT_STATE_REPORT_READY
    assert is_report_ready_result(report_ready)
    assert not is_report_ready_result(failed)


def test_m12_random_effects_are_not_supported_in_mvp() -> None:
    result = PairwiseMetaExecutorService().execute_from_inputs(
        confirmed_plan=_plan("MD"),
        normalized_records=[_effect("A", 0.2, 0.04, measure="MD"), _effect("B", 0.5, 0.01, measure="MD")],
        config=PairwiseMetaExecutorConfig(model="random_effect"),
    )

    assert result.result_state == STATISTICAL_RESULT_STATE_FAILED_VALIDATION
    assert "random_effects_not_supported_in_m12" in result.validation_errors


def test_m12_report_and_ui_show_testing_labels_without_raw_internals(tmp_path: Path) -> None:
    service = PairwiseMetaExecutorService()
    result = service.execute_from_inputs(confirmed_plan=_plan("MD"), normalized_records=[_effect("A", 0.2, 0.04, measure="MD"), _effect("B", 0.5, 0.01, measure="MD")], project_name="safe-project")
    service.save_result(tmp_path, result)

    report_text = FormalMarkdownReportBuilder().build_draft_markdown_report(tmp_path).read_text(encoding="utf-8")
    state = analysis_setup_state_from_project(tmp_path)
    rendered_summary = str(state.pairwise_executor_summary)

    assert "M12 pairwise executor：Developer Preview / testing MVP" in report_text
    assert "统计结果已计算但尚未完成用户审核，不能作为正式报告结论。" in report_text
    assert "report_ready：否" in report_text
    assert "统计执行状态" in rendered_summary
    assert "合并效应量" in rendered_summary
    assert "测试阶段提示" in rendered_summary
    assert "pairwise-result-" not in report_text
    assert str(tmp_path) not in report_text
    assert "raw JSON" not in rendered_summary


def _plan(effect: str) -> dict[str, object]:
    return {
        "plan_state": "confirmed",
        "confirmed_analysis_plan_id": "safe-plan",
        "confirmed_effect_measure": effect,
        "effect_measure_type": effect,
        "confirmed_model": "fixed_effect",
    }


def _effect(label: str, estimate: float, variance: float, *, measure: str = "OR", source_state: str = "confirmed") -> NormalizedEffectSizeInput:
    return NormalizedEffectSizeInput(
        study_label=label,
        effect_measure_type=measure,
        estimate=estimate,
        standard_error=math.sqrt(variance),
        variance=variance,
        log_estimate=estimate if measure in {"OR", "RR", "HR"} else None,
        source_state=source_state,
        normalization_status=NORMALIZATION_STATUS_READY,
    )


def _ratio_effect(label: str, ratio: float, variance: float) -> NormalizedEffectSizeInput:
    log_value = math.log(ratio)
    se = math.sqrt(variance)
    return NormalizedEffectSizeInput(
        study_label=label,
        effect_measure_type="OR",
        estimate=ratio,
        ci_lower=math.exp(log_value - 1.96 * se),
        ci_upper=math.exp(log_value + 1.96 * se),
        standard_error=se,
        variance=variance,
        log_estimate=log_value,
        log_ci_lower=log_value - 1.96 * se,
        log_ci_upper=log_value + 1.96 * se,
        source_state="confirmed",
        normalization_status=NORMALIZATION_STATUS_READY,
    )
