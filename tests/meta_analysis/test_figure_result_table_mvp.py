from __future__ import annotations

from pathlib import Path

from app.meta_analysis.models.analysis_result import AnalysisResult, StudyMetaAnalysisResult, now_utc
from app.meta_analysis.pages.analysis_page import initial_analysis_state
from app.meta_analysis.services.analysis_run_service import AnalysisRunService
from app.meta_analysis.services.figure_result_service import FigureResultService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def test_forest_plot_png_and_result_table_are_exported(tmp_path: Path) -> None:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    run_service = AnalysisRunService(task_center=task_center, data_center=data_center)
    figure_service = FigureResultService(
        analysis_run_service=run_service,
        task_center=task_center,
        data_center=data_center,
    )
    project_dir = tmp_path / "project"
    result = mock_analysis_result()
    run_service.save_analysis_result(project_dir, result)

    artifact = figure_service.generate_forest_plot(project_dir, result.result_id)
    table_path = figure_service.export_result_table_csv(project_dir, result.result_id)

    assert artifact.figure_type == "forest_plot"
    assert artifact.format == "png"
    assert Path(artifact.file_path).exists()
    assert Path(artifact.file_path).stat().st_size > 0
    assert table_path.exists()
    assert "pooled" in table_path.read_text(encoding="utf-8")
    assert figure_service.list_figure_artifacts(project_dir)[0].figure_id == artifact.figure_id
    data_types = {asset.data_type for asset in data_center.list_assets("meta-test")}
    assert {"forest_plot", "analysis_result_table"} <= data_types
    task_types = {task.task_type for task in task_center.list_tasks()}
    assert TaskType.FOREST_PLOT_EXPORT in task_types
    assert TaskType.ANALYSIS_RESULT_TABLE_EXPORT in task_types


def test_analysis_page_state_exposes_figure_artifact_fields() -> None:
    state = initial_analysis_state()

    assert "forest_plot_path" in state.figure_artifact_fields
    assert "result_table_path" in state.figure_artifact_fields


def mock_analysis_result() -> AnalysisResult:
    return AnalysisResult(
        result_id="ares-test",
        dataset_id="ards-test",
        project_id="meta-test",
        profile_type="TREATMENT_EFFECT_META",
        outcome_name="Mortality",
        effect_measure="OR",
        model="fixed",
        pooled_effect=0.72,
        ci_lower=0.51,
        ci_upper=1.02,
        p_value=0.06,
        q_statistic=1.2,
        i_squared=12.5,
        tau_squared=0.01,
        study_results=[
            StudyMetaAnalysisResult(
                study_id="study-1",
                record_id="rec-1",
                first_author="Alpha",
                year=2022,
                effect=0.6,
                ci_lower=0.31,
                ci_upper=1.1,
                standard_error=0.23,
                variance=0.0529,
                weight=18.9,
                transformed_effect=-0.51,
            ),
            StudyMetaAnalysisResult(
                study_id="study-2",
                record_id="rec-2",
                first_author="Beta",
                year=2024,
                effect=0.82,
                ci_lower=0.52,
                ci_upper=1.29,
                standard_error=0.19,
                variance=0.0361,
                weight=27.7,
                transformed_effect=-0.2,
            ),
        ],
        warnings=[],
        created_at=now_utc(),
    )
