from __future__ import annotations

from pathlib import Path

import pytest

from app.meta_analysis.models.analysis_dataset import AnalysisReadyDataset, StudyAnalysisRow
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.services.analysis_run_service import AnalysisRunService
from app.meta_analysis.services.statistical_applicability_service import StatisticalApplicabilityService


def smd_dataset(project_id: str, sd: float) -> AnalysisReadyDataset:
    return AnalysisReadyDataset(
        dataset_id="ards-smd",
        project_id=project_id,
        profile_type="TREATMENT_EFFECT_META",
        outcome_name="Change",
        effect_measure="SMD",
        outcome_data_type="continuous",
        included_extraction_ids=["extr-1"],
        excluded_extraction_ids=[],
        study_rows=[
            StudyAnalysisRow(
                study_id="study-1",
                record_id="rec-1",
                first_author="Adams",
                year=2024,
                outcome_name="Change",
                effect_measure="SMD",
                outcome_data_type="continuous",
                raw_data={},
                normalized_data={
                    "experimental_mean": 1.0,
                    "experimental_sd": sd,
                    "experimental_total": 50,
                    "control_mean": 0.5,
                    "control_sd": sd,
                    "control_total": 50,
                    "effect_measure": "SMD",
                },
                analysis_status="included",
            )
        ],
        validation_errors=[],
        validation_warnings=[],
        created_at="now",
    )


def test_applicability_service_flags_key_method_warnings_and_errors() -> None:
    service = StatisticalApplicabilityService()
    dataset = smd_dataset("project", 0.0)

    result = service.evaluate_dataset_for_meta_analysis(dataset, "random")

    assert "smd_sd_must_be_positive:rec-1" in result.errors
    assert "random_effects_tau_squared_unstable_with_fewer_than_three_studies" in result.warnings
    assert "network_meta_analysis_not_implemented" in service.evaluate_advanced_method("network_meta", 5).errors
    assert "publication_bias_and_funnel_plot_unreliable_with_fewer_than_ten_studies" in service.evaluate_advanced_method("egger", 3).warnings


def test_analysis_run_blocks_applicability_errors(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    dataset_service = AnalysisDatasetService()
    dataset_service.save_analysis_ready_dataset(project_dir, smd_dataset("project", 0.0))
    run_service = AnalysisRunService(dataset_service=dataset_service)

    with pytest.raises(ValueError, match="smd_sd_must_be_positive"):
        run_service.run_meta_analysis(project_dir, "ards-smd", "random")


def test_analysis_result_saves_applicability_warnings(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    dataset_service = AnalysisDatasetService()
    dataset_service.save_analysis_ready_dataset(project_dir, smd_dataset("project", 1.0))
    run_service = AnalysisRunService(dataset_service=dataset_service)

    result = run_service.run_meta_analysis(project_dir, "ards-smd", "random")

    assert "random_effects_tau_squared_unstable_with_fewer_than_three_studies" in result.warnings
