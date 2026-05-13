from __future__ import annotations

from pathlib import Path

from app.meta_analysis.models.analysis_dataset import AnalysisReadyDataset, StudyAnalysisRow, now_utc
from app.meta_analysis.models.analysis_result import AnalysisResult, StudyMetaAnalysisResult
from app.meta_analysis.pages.analysis_page import initial_analysis_state
from app.meta_analysis.services.advanced_analysis_service import AdvancedAnalysisService, SMALL_STUDY_BIAS_WARNING
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.services.analysis_run_service import AnalysisRunService
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def make_services(tmp_path: Path) -> tuple[AdvancedAnalysisService, AnalysisDatasetService, AnalysisRunService, TaskCenter, DataCenter, Path]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    dataset_service = AnalysisDatasetService(task_center=task_center, data_center=data_center)
    run_service = AnalysisRunService(dataset_service=dataset_service, task_center=task_center, data_center=data_center)
    service = AdvancedAnalysisService(
        dataset_service=dataset_service,
        analysis_run_service=run_service,
        task_center=task_center,
        data_center=data_center,
    )
    return service, dataset_service, run_service, task_center, data_center, tmp_path / "project"


def test_subgroup_analysis_groups_by_subgroup_field(tmp_path: Path) -> None:
    service, dataset_service, _run_service, task_center, data_center, project_dir = make_services(tmp_path)
    dataset = analysis_dataset(
        [
            binary_row("study-1", "rec-1", 10, 100, 20, 100, subgroup="A"),
            binary_row("study-2", "rec-2", 12, 100, 18, 100, subgroup="A"),
            binary_row("study-3", "rec-3", 20, 100, 18, 100, subgroup="B"),
        ]
    )
    dataset_service.save_analysis_ready_dataset(project_dir, dataset)

    result = service.run_subgroup_analysis(project_dir, dataset.dataset_id, "subgroup", "fixed")
    output_path = service.save_subgroup_result(project_dir, result)

    assert {item["subgroup_value"] for item in result.subgroup_results} == {"A", "B"}
    assert result.between_group_heterogeneity["df"] == 1
    assert output_path.exists()
    assert service.load_subgroup_result(project_dir, result.subgroup_result_id).subgroup_result_id == result.subgroup_result_id  # type: ignore[union-attr]
    assert TaskType.SUBGROUP_ANALYSIS_RUN in {task.task_type for task in task_center.list_tasks()}
    assert "subgroup_analysis_result" in {asset.data_type for asset in data_center.list_assets("meta-test")}


def test_leave_one_out_generates_omitted_results_and_warning(tmp_path: Path) -> None:
    service, _dataset_service, run_service, task_center, data_center, project_dir = make_services(tmp_path)
    result = analysis_result()
    run_service.save_analysis_result(project_dir, result)

    leave_one_out = service.run_leave_one_out(project_dir, result.result_id)
    output_path = service.save_leave_one_out_result(project_dir, leave_one_out)

    assert len(leave_one_out.omitted_study_results) == len(result.study_results)
    assert output_path.exists()
    assert TaskType.LEAVE_ONE_OUT_RUN in {task.task_type for task in task_center.list_tasks()}
    assert "leave_one_out_result" in {asset.data_type for asset in data_center.list_assets("meta-test")}


def test_publication_bias_egger_and_small_study_warning(tmp_path: Path) -> None:
    service, _dataset_service, run_service, task_center, data_center, project_dir = make_services(tmp_path)
    result = analysis_result(study_count=5)
    run_service.save_analysis_result(project_dir, result)

    bias = service.run_publication_bias_test(project_dir, result.result_id)
    output_path = service.save_publication_bias_result(project_dir, bias)

    assert bias.egger_test["implemented"] is True
    assert bias.egger_test["study_count"] == 5
    assert bias.begg_test["implemented"] is False
    assert SMALL_STUDY_BIAS_WARNING in bias.warnings
    assert output_path.exists()
    assert service.load_publication_bias_result(project_dir, bias.bias_result_id).bias_result_id == bias.bias_result_id  # type: ignore[union-attr]
    assert TaskType.PUBLICATION_BIAS_TEST in {task.task_type for task in task_center.list_tasks()}
    assert "publication_bias_result" in {asset.data_type for asset in data_center.list_assets("meta-test")}


def test_funnel_plot_png_is_generated(tmp_path: Path) -> None:
    service, _dataset_service, run_service, task_center, data_center, project_dir = make_services(tmp_path)
    result = analysis_result(study_count=4)
    run_service.save_analysis_result(project_dir, result)

    artifact = service.generate_funnel_plot(project_dir, result.result_id)

    path = Path(artifact.file_path)
    assert artifact.figure_type == "funnel_plot"
    assert path.exists()
    assert path.stat().st_size > 0
    assert TaskType.FUNNEL_PLOT_EXPORT in {task.task_type for task in task_center.list_tasks()}
    assert "funnel_plot" in {asset.data_type for asset in data_center.list_assets("meta-test")}


def test_analysis_page_and_formal_report_reference_advanced_addons(tmp_path: Path) -> None:
    state = initial_analysis_state()
    project_dir = tmp_path / "project"
    (project_dir / "analysis").mkdir(parents=True)
    (project_dir / "figures").mkdir(parents=True)
    (project_dir / "analysis" / "subgroup_analysis_results.json").write_text('{"subgroup_results":[]}', encoding="utf-8")
    (project_dir / "analysis" / "leave_one_out_results.json").write_text('{"leave_one_out_results":[]}', encoding="utf-8")
    (project_dir / "analysis" / "publication_bias_results.json").write_text('{"publication_bias_results":[]}', encoding="utf-8")
    (project_dir / "figures" / "funnel_plot_ares-test.png").write_bytes(b"png")

    report_path = FormalMarkdownReportBuilder().build_formal_markdown_report(project_dir)
    report_text = report_path.read_text(encoding="utf-8")

    assert "subgroup_result_id" in state.advanced_analysis_fields
    assert "funnel_plot_path" in state.advanced_analysis_fields
    assert "publication bias basic" in state.description
    assert "Advanced analysis add-ons summary" in report_text
    assert "funnel_plot_ares-test.png" in report_text


def binary_row(
    study_id: str,
    record_id: str,
    experimental_events: int,
    experimental_total: int,
    control_events: int,
    control_total: int,
    *,
    subgroup: str,
) -> StudyAnalysisRow:
    return StudyAnalysisRow(
        study_id=study_id,
        record_id=record_id,
        first_author=study_id,
        year=2024,
        outcome_name="Mortality",
        effect_measure="OR",
        outcome_data_type="binary",
        raw_data={},
        normalized_data={
            "experimental_events": experimental_events,
            "experimental_non_events": experimental_total - experimental_events,
            "experimental_total": experimental_total,
            "control_events": control_events,
            "control_non_events": control_total - control_events,
            "control_total": control_total,
            "effect_measure": "OR",
            "subgroup": subgroup,
        },
        analysis_status="included",
    )


def analysis_dataset(rows: list[StudyAnalysisRow]) -> AnalysisReadyDataset:
    return AnalysisReadyDataset(
        dataset_id="ards-test",
        project_id="meta-test",
        profile_type="TREATMENT_EFFECT_META",
        outcome_name="Mortality",
        effect_measure="OR",
        outcome_data_type="binary",
        included_extraction_ids=[f"extr-{index}" for index, _row in enumerate(rows, start=1)],
        excluded_extraction_ids=[],
        study_rows=rows,
        validation_errors=[],
        validation_warnings=[],
        created_at=now_utc(),
    )


def analysis_result(*, study_count: int = 3) -> AnalysisResult:
    study_results = [
        StudyMetaAnalysisResult(
            study_id=f"study-{index}",
            record_id=f"rec-{index}",
            first_author=f"Author {index}",
            year=2024,
            effect=0.55 + (index * 0.05),
            ci_lower=0.3 + (index * 0.03),
            ci_upper=1.0 + (index * 0.08),
            standard_error=0.18 + (index * 0.02),
            variance=(0.18 + (index * 0.02)) ** 2,
            weight=1 / ((0.18 + (index * 0.02)) ** 2),
            transformed_effect=-0.6 + (index * 0.08),
        )
        for index in range(1, study_count + 1)
    ]
    return AnalysisResult(
        result_id="ares-test",
        dataset_id="ards-test",
        project_id="meta-test",
        profile_type="TREATMENT_EFFECT_META",
        outcome_name="Mortality",
        effect_measure="OR",
        model="fixed",
        pooled_effect=0.72,
        ci_lower=0.5,
        ci_upper=1.1,
        p_value=0.08,
        q_statistic=1.4,
        i_squared=15.0,
        tau_squared=0.02,
        study_results=study_results,
        warnings=[],
        created_at=now_utc(),
    )
