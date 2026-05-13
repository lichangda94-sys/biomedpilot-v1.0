from __future__ import annotations

import math
from pathlib import Path

import pytest

from app.meta_analysis.models.effect_size_normalization import (
    NORMALIZATION_STATUS_INCOMPLETE,
    NORMALIZATION_STATUS_INVALID_CI,
    NORMALIZATION_STATUS_INVALID_NUMERIC,
    NORMALIZATION_STATUS_NEEDS_USER_REVIEW,
    NORMALIZATION_STATUS_READY,
    NORMALIZATION_STATUS_UNSUPPORTED_EFFECT_TYPE,
)
from app.meta_analysis.models.statistical_result_state import can_enter_computed_state
from app.meta_analysis.pages.analysis_page import analysis_setup_state_from_project
from app.meta_analysis.services.effect_size_normalization_service import EffectSizeNormalizationService
from app.meta_analysis.services.manual_extraction_effect_row_service import ManualExtractionEffectRowService


def test_m11_or_rr_hr_estimate_ci_produce_log_fields_and_se() -> None:
    service = EffectSizeNormalizationService()
    for measure, estimate, low, high in (("OR", 1.8, 1.1, 2.9), ("RR", 1.2, 1.0, 1.5), ("HR", 0.72, 0.55, 0.95)):
        normalized = service.normalize_single_effect(_row(measure, estimate=estimate, ci_lower=low, ci_upper=high, evidence_state="confirmed"))

        assert normalized.normalization_status == NORMALIZATION_STATUS_READY
        assert normalized.log_estimate == pytest.approx(math.log(estimate))
        assert normalized.log_ci_lower == pytest.approx(math.log(low))
        assert normalized.log_ci_upper == pytest.approx(math.log(high))
        assert normalized.standard_error == pytest.approx((math.log(high) - math.log(low)) / 3.92)
        assert normalized.variance == pytest.approx(normalized.standard_error**2)


def test_m11_md_smd_estimate_ci_derives_se_original_scale() -> None:
    service = EffectSizeNormalizationService()
    for measure in ("MD", "SMD"):
        normalized = service.normalize_single_effect(_row(measure, estimate=2.4, ci_lower=1.2, ci_upper=3.6, evidence_state="confirmed"))

        assert normalized.normalization_status == NORMALIZATION_STATUS_READY
        assert normalized.log_estimate is None
        assert normalized.standard_error == pytest.approx((3.6 - 1.2) / 3.92)
        assert normalized.variance == pytest.approx(normalized.standard_error**2)


def test_m11_invalid_ci_and_non_positive_ratio_are_rejected() -> None:
    service = EffectSizeNormalizationService()

    invalid_ci = service.normalize_single_effect(_row("OR", estimate=1.4, ci_lower=2.0, ci_upper=1.0, evidence_state="confirmed"))
    non_positive = service.normalize_single_effect(_row("RR", estimate=0.0, ci_lower=0.8, ci_upper=1.2, evidence_state="confirmed"))

    assert invalid_ci.normalization_status == NORMALIZATION_STATUS_INVALID_CI
    assert "ci_lower_exceeds_ci_upper" in invalid_ci.warnings or "invalid_ci" in invalid_ci.warnings
    assert non_positive.normalization_status == NORMALIZATION_STATUS_INVALID_NUMERIC
    assert "ratio_measure_requires_positive_estimate_and_ci" in non_positive.warnings


def test_m11_missing_ci_is_incomplete_and_preserves_warning() -> None:
    normalized = EffectSizeNormalizationService().normalize_single_effect(
        _row("HR", estimate=1.1, ci_lower="", ci_upper="", evidence_state="confirmed", warnings=["source_note"])
    )

    assert normalized.normalization_status == NORMALIZATION_STATUS_INCOMPLETE
    assert "ratio_measure_requires_estimate_and_ci" in normalized.warnings
    assert "source_note" in normalized.warnings


def test_m11_suggested_and_draft_rows_are_not_executor_ready() -> None:
    service = EffectSizeNormalizationService()
    suggested = service.normalize_single_effect(_row("OR", estimate=1.3, ci_lower=1.0, ci_upper=1.7, evidence_state="suggested"))
    draft = service.normalize_single_effect(_row("OR", estimate=1.3, ci_lower=1.0, ci_upper=1.7, evidence_state="draft"))

    assert suggested.normalization_status == NORMALIZATION_STATUS_NEEDS_USER_REVIEW
    assert draft.normalization_status == NORMALIZATION_STATUS_NEEDS_USER_REVIEW
    assert "source_row_not_confirmed" in suggested.warnings


def test_m11_confirmed_structured_rows_can_become_ready_from_project_state(tmp_path: Path) -> None:
    manual = ManualExtractionEffectRowService()
    created = manual.create_structured_extraction_row(
        tmp_path,
        fields={"study_id": "study-1", "first_author": "Zhang", "year": "2025", "outcome": "Mortality", "effect_measure_type": "OR", "effect_estimate": "1.8", "ci_lower": "1.1", "ci_upper": "2.9"},
        actor="reviewer",
    )
    manual.confirm_structured_extraction_row(tmp_path, effect_row_id=created.payload["effect_row_id"], actor="reviewer")

    effects = EffectSizeNormalizationService().normalize_extraction_rows(tmp_path)
    summary = EffectSizeNormalizationService().summarize_normalization(effects)

    assert effects[0].normalization_status == NORMALIZATION_STATUS_READY
    assert effects[0].study_label == "Zhang 2025"
    assert summary.total_rows == 1
    assert summary.confirmed_rows == 1
    assert summary.normalized_ready == 1
    assert summary.creates_computed_result is False
    assert summary.result_state == "configured_not_run"


def test_m11_unsupported_and_other_effects_are_handled_safely() -> None:
    service = EffectSizeNormalizationService()
    unsupported = service.normalize_single_effect(_row("BAD", estimate=1.0, ci_lower=0.8, ci_upper=1.2, evidence_state="confirmed"))
    other = service.normalize_single_effect(_row("other", estimate=1.0, ci_lower=0.8, ci_upper=1.2, evidence_state="confirmed"))

    assert unsupported.normalization_status == NORMALIZATION_STATUS_UNSUPPORTED_EFFECT_TYPE
    assert other.normalization_status == NORMALIZATION_STATUS_INCOMPLETE
    assert "other_effect_type_requires_user_mapping" in other.warnings


def test_m11_summary_counts_ready_incomplete_invalid_and_review_states() -> None:
    service = EffectSizeNormalizationService()
    effects = [
        service.normalize_single_effect(_row("OR", estimate=1.8, ci_lower=1.1, ci_upper=2.9, evidence_state="confirmed")),
        service.normalize_single_effect(_row("HR", estimate=1.1, ci_lower="", ci_upper="", evidence_state="confirmed")),
        service.normalize_single_effect(_row("RR", estimate=0, ci_lower=0.8, ci_upper=1.2, evidence_state="confirmed")),
        service.normalize_single_effect(_row("OR", estimate=1.8, ci_lower=1.1, ci_upper=2.9, evidence_state="suggested")),
        service.normalize_single_effect(_row("BAD", estimate=1.8, ci_lower=1.1, ci_upper=2.9, evidence_state="confirmed")),
    ]

    summary = service.summarize_normalization(effects)

    assert summary.total_rows == 5
    assert summary.confirmed_rows == 4
    assert summary.normalized_ready == 1
    assert summary.incomplete == 1
    assert summary.invalid == 1
    assert summary.needs_user_review == 1
    assert summary.unsupported_effect_type == 1
    assert summary.warnings


def test_m11_normalized_ready_inputs_do_not_create_computed_result() -> None:
    summary = EffectSizeNormalizationService().summarize_normalization(
        [EffectSizeNormalizationService().normalize_single_effect(_row("OR", estimate=1.8, ci_lower=1.1, ci_upper=2.9, evidence_state="confirmed"))]
    )
    gate = can_enter_computed_state(
        {
            "confirmed_analysis_plan": True,
            "confirmed_extraction_rows": summary.confirmed_rows > 0,
            "effect_measure_consistent": True,
            "numeric_fields_valid": summary.invalid == 0,
            "enough_included_studies": summary.normalized_ready >= 2,
            "reproducibility_metadata_present": False,
        }
    )

    assert summary.creates_computed_result is False
    assert summary.result_state == "configured_not_run"
    assert not gate.allowed
    assert "enough_included_studies_required_for_computed_state" in gate.errors
    assert "reproducibility_metadata_present_required_for_computed_state" in gate.errors


def test_m11_analysis_page_state_exposes_chinese_preview_without_paths_or_ids(tmp_path: Path) -> None:
    manual = ManualExtractionEffectRowService()
    created = manual.create_structured_extraction_row(
        tmp_path,
        fields={"study_id": "internal-study-1", "first_author": "Li", "year": "2026", "outcome": "Response", "effect_measure_type": "OR", "effect_estimate": "1.4", "ci_lower": "1.1", "ci_upper": "1.8"},
        actor="reviewer",
    )
    manual.confirm_structured_extraction_row(tmp_path, effect_row_id=created.payload["effect_row_id"], actor="reviewer")

    state = analysis_setup_state_from_project(tmp_path)
    rendered = str(state.effect_size_normalization_summary)

    assert "效应量标准化预检查" in rendered
    assert state.effect_size_normalization_summary["normalized_ready"] == 1
    assert "effectrow-" not in rendered
    assert str(tmp_path) not in rendered
    assert "raw JSON" not in rendered


def _row(
    effect_measure_type: str,
    *,
    estimate: object,
    ci_lower: object,
    ci_upper: object,
    evidence_state: str,
    warnings: list[str] | None = None,
) -> dict[str, object]:
    return {
        "study_unit_label": "Study A",
        "evidence_state": evidence_state,
        "extraction_status": "completed_by_user" if evidence_state == "confirmed" else "draft",
        "m5_structured_fields": {
            "study_id": "study-a",
            "first_author": "Alpha",
            "year": "2025",
            "outcome": "Mortality",
            "effect_measure_type": effect_measure_type,
            "effect_estimate": estimate,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
        },
        "warnings": warnings or [],
    }
