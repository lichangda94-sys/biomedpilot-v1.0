from __future__ import annotations

from pathlib import Path

import pytest

from app.meta_analysis.extraction.schema_registry import PROGNOSTIC_FACTOR_META, TREATMENT_EFFECT_META
from app.meta_analysis.models.analysis_dataset import AnalysisReadyDataset, StudyAnalysisRow, now_utc
from app.meta_analysis.pages.analysis_page import initial_analysis_state
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.services.analysis_run_service import AnalysisRunService
from app.meta_analysis.stats.heterogeneity import calculate_heterogeneity
from app.meta_analysis.stats.meta_effects import (
    binary_study_effect,
    ci_to_standard_error,
    continuous_study_effect,
    generic_inverse_variance_effect,
)
from app.meta_analysis.stats.meta_models import pool_effects
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def test_or_rr_and_rd_study_effects() -> None:
    row = binary_row(10, 100, 20, 100, "OR")

    odds_ratio = binary_study_effect(row)
    risk_ratio = binary_study_effect(binary_row(10, 100, 20, 100, "RR"))
    risk_difference = binary_study_effect(binary_row(10, 100, 20, 100, "RD"))

    assert odds_ratio.effect == pytest.approx(0.444444, rel=1e-5)
    assert risk_ratio.effect == pytest.approx(0.5)
    assert risk_difference.effect == pytest.approx(-0.1)
    assert odds_ratio.standard_error > 0


def test_zero_event_correction_is_applied_for_ratio_binary_effects() -> None:
    effect = binary_study_effect(binary_row(0, 40, 5, 42, "OR"))

    assert effect.effect > 0
    assert "zero_event_correction_applied" in effect.warnings


def test_md_and_smd_study_effects() -> None:
    md = continuous_study_effect(continuous_row("MD"))
    smd = continuous_study_effect(continuous_row("SMD"))

    assert md.effect == pytest.approx(-0.7)
    assert md.standard_error > 0
    assert smd.effect < 0
    assert smd.standard_error > 0


def test_generic_hr_inverse_variance_uses_ci_to_se() -> None:
    row = generic_row(effect=2.0, ci_lower=1.0, ci_upper=4.0)

    effect = generic_inverse_variance_effect(row)

    assert effect.effect == pytest.approx(2.0)
    assert effect.standard_error == pytest.approx(ci_to_standard_error(1.0, 4.0, log_scale=True))
    assert effect.adjusted is True
    assert effect.covariates == ["age", "stage"]


def test_ci_to_standard_error_for_non_log_scale() -> None:
    assert ci_to_standard_error(1.0, 3.0, log_scale=False) == pytest.approx(2.0 / 3.92)


def test_fixed_and_random_pooling_and_heterogeneity() -> None:
    effects = [
        binary_study_effect(binary_row(10, 100, 20, 100, "OR")),
        binary_study_effect(binary_row(15, 110, 18, 105, "OR", study_id="study-2", record_id="rec-2")),
    ]

    fixed = pool_effects(effects, effect_measure="OR", model="fixed")
    random = pool_effects(effects, effect_measure="OR", model="random")
    heterogeneity = calculate_heterogeneity(effects)

    assert fixed.pooled_effect > 0
    assert random.pooled_effect > 0
    assert heterogeneity.q_statistic >= 0
    assert heterogeneity.i_squared >= 0
    assert heterogeneity.tau_squared >= 0
    assert len(random.weights) == 2


def test_analysis_run_service_saves_result_and_registers_task_and_data(tmp_path: Path) -> None:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    dataset_service = AnalysisDatasetService(task_center=task_center, data_center=data_center)
    run_service = AnalysisRunService(dataset_service=dataset_service, task_center=task_center, data_center=data_center)
    project_dir = tmp_path / "project"
    dataset = analysis_dataset(
        rows=[
            binary_row(10, 100, 20, 100, "OR"),
            binary_row(15, 110, 18, 105, "OR", study_id="study-2", record_id="rec-2"),
        ]
    )
    dataset_service.save_analysis_ready_dataset(project_dir, dataset)

    result = run_service.run_meta_analysis(project_dir, dataset.dataset_id, "random")
    output_path = run_service.save_analysis_result(project_dir, result)

    assert result.model == "random"
    assert result.pooled_effect > 0
    assert result.q_statistic >= 0
    assert result.i_squared >= 0
    assert result.tau_squared >= 0
    assert output_path == project_dir / "analysis" / "analysis_results.json"
    assert run_service.load_analysis_result(project_dir, result.result_id).result_id == result.result_id  # type: ignore[union-attr]
    assert task_center.list_tasks()[0].task_type is TaskType.META_ANALYSIS_RUN
    assert any(asset.data_type == "analysis_result" for asset in data_center.list_assets("meta-test"))


def test_analysis_run_warns_when_study_count_is_insufficient(tmp_path: Path) -> None:
    dataset_service = AnalysisDatasetService()
    run_service = AnalysisRunService(dataset_service=dataset_service)
    project_dir = tmp_path / "project"
    dataset = analysis_dataset(rows=[binary_row(10, 100, 20, 100, "OR")])
    dataset_service.save_analysis_ready_dataset(project_dir, dataset)

    result = run_service.run_meta_analysis(project_dir, dataset.dataset_id, "fixed")

    assert "insufficient_studies_warning" in result.warnings


def test_analysis_result_page_state_exposes_result_summary() -> None:
    state = initial_analysis_state()

    assert "pooled_effect" in state.result_summary_fields
    assert "fixed" in state.model_options
    assert "random" in state.model_options


def binary_row(
    experimental_events: int,
    experimental_total: int,
    control_events: int,
    control_total: int,
    effect_measure: str,
    *,
    study_id: str = "study-1",
    record_id: str = "rec-1",
) -> StudyAnalysisRow:
    return StudyAnalysisRow(
        study_id=study_id,
        record_id=record_id,
        first_author="Author",
        year=2024,
        outcome_name="Mortality",
        effect_measure=effect_measure,
        outcome_data_type="binary",
        raw_data={},
        normalized_data={
            "experimental_events": experimental_events,
            "experimental_non_events": experimental_total - experimental_events,
            "experimental_total": experimental_total,
            "control_events": control_events,
            "control_non_events": control_total - control_events,
            "control_total": control_total,
            "effect_measure": effect_measure,
        },
        analysis_status="included",
    )


def continuous_row(effect_measure: str) -> StudyAnalysisRow:
    return StudyAnalysisRow(
        study_id="study-cont",
        record_id="rec-cont",
        first_author="Continuous",
        year=2024,
        outcome_name="Pain score",
        effect_measure=effect_measure,
        outcome_data_type="continuous",
        raw_data={},
        normalized_data={
            "experimental_mean": 3.4,
            "experimental_sd": 1.2,
            "experimental_total": 40,
            "control_mean": 4.1,
            "control_sd": 1.4,
            "control_total": 42,
            "effect_measure": effect_measure,
        },
        analysis_status="included",
    )


def generic_row(effect: float, ci_lower: float, ci_upper: float) -> StudyAnalysisRow:
    return StudyAnalysisRow(
        study_id="study-hr",
        record_id="rec-hr",
        first_author="Generic",
        year=2024,
        outcome_name="Overall survival",
        effect_measure="HR",
        outcome_data_type="generic_effect",
        raw_data={},
        normalized_data={
            "effect": effect,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "standard_error": None,
            "p_value": None,
            "adjusted": True,
            "covariates": ["age", "stage"],
            "effect_measure": "HR",
        },
        analysis_status="included",
    )


def analysis_dataset(rows: list[StudyAnalysisRow]) -> AnalysisReadyDataset:
    return AnalysisReadyDataset(
        dataset_id="ards-test",
        project_id="meta-test",
        profile_type=PROGNOSTIC_FACTOR_META if rows and rows[0].outcome_data_type == "generic_effect" else TREATMENT_EFFECT_META,
        outcome_name=rows[0].outcome_name if rows else "Mortality",
        effect_measure=rows[0].effect_measure if rows else "OR",
        outcome_data_type=rows[0].outcome_data_type if rows else "binary",
        included_extraction_ids=[f"extr-{index}" for index, _row in enumerate(rows, start=1)],
        excluded_extraction_ids=[],
        study_rows=rows,
        validation_errors=[],
        validation_warnings=[],
        created_at=now_utc(),
    )
