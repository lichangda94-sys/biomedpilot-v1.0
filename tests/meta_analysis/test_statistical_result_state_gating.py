from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.meta_analysis.models.analysis_dataset import AnalysisReadyDataset, StudyAnalysisRow, now_utc
from app.meta_analysis.models.analysis_result import analysis_result_to_dict
from app.meta_analysis.models.statistical_result_state import (
    STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN,
    STATISTICAL_RESULT_STATE_FAILED_VALIDATION,
    STATISTICAL_RESULT_STATE_REPORT_READY,
    STATISTICAL_RESULT_STATE_TESTING_LEVEL,
    STATISTICAL_RESULT_STATES,
    blocks_formal_report_claim,
    can_enter_computed_state,
    can_enter_report_ready_state,
    failed_validation_result_metadata,
    is_formal_computed_result,
    is_report_ready_result,
    requires_user_review,
    validate_statistical_result_state,
)
from app.meta_analysis.pages.analysis_page import analysis_setup_state_from_project
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.services.analysis_run_service import AnalysisRunService
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder


def test_m10_statistical_result_states_and_invalid_state() -> None:
    assert set(STATISTICAL_RESULT_STATES) == {
        "not_run",
        "configured_not_run",
        "testing_level",
        "failed_validation",
        "computed",
        "user_reviewed",
        "report_ready",
    }
    assert validate_statistical_result_state(STATISTICAL_RESULT_STATE_TESTING_LEVEL) == STATISTICAL_RESULT_STATE_TESTING_LEVEL
    with pytest.raises(ValueError, match="invalid_statistical_result_state"):
        validate_statistical_result_state("formal_final")


def test_m10_testing_level_and_configured_not_run_are_not_formal_results() -> None:
    testing = {"result_state": "testing_level", "testing_level": True, "formal_computed": False}
    configured = {"result_state": STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN}

    assert not is_formal_computed_result(testing)
    assert blocks_formal_report_claim(testing)
    assert blocks_formal_report_claim(configured)
    assert not is_report_ready_result(configured)


def test_m10_computed_requires_user_review_before_report_ready() -> None:
    computed = {"result_state": "computed", "testing_level": False, "formal_computed": True, "user_reviewed": False}
    reviewed = {**computed, "user_reviewed": True}
    report_ready = {**reviewed, "result_state": STATISTICAL_RESULT_STATE_REPORT_READY, "report_ready": True}

    assert is_formal_computed_result(computed)
    assert requires_user_review(computed)
    assert not can_enter_report_ready_state(computed).allowed
    assert can_enter_report_ready_state(reviewed).allowed
    assert is_report_ready_result(report_ready)


def test_m10_computed_gate_requires_confirmed_inputs_and_metadata() -> None:
    blocked = can_enter_computed_state({"confirmed_analysis_plan": True}, warnings=["quality_assessment_incomplete"])

    assert not blocked.allowed
    assert blocked.target_state == STATISTICAL_RESULT_STATE_FAILED_VALIDATION
    assert "confirmed_extraction_rows_required_for_computed_state" in blocked.errors
    assert blocked.warnings == ("quality_assessment_incomplete",)

    allowed = can_enter_computed_state(
        {
            "confirmed_analysis_plan": True,
            "confirmed_extraction_rows": True,
            "effect_measure_consistent": True,
            "numeric_fields_valid": True,
            "enough_included_studies": True,
            "reproducibility_metadata_present": True,
        }
    )

    assert allowed.allowed
    assert allowed.target_state == "computed"


def test_m10_failed_validation_metadata_carries_errors_and_warnings() -> None:
    payload = failed_validation_result_metadata(["effect_measure_mixed"], ["quality_assessment_incomplete"])

    assert payload["result_state"] == STATISTICAL_RESULT_STATE_FAILED_VALIDATION
    assert payload["validation_errors"] == ["effect_measure_mixed"]
    assert payload["result_state_warnings"] == ["quality_assessment_incomplete"]
    assert blocks_formal_report_claim(payload)


def test_m10_old_analysis_run_service_outputs_testing_level_not_formal(tmp_path: Path) -> None:
    dataset_service = AnalysisDatasetService()
    run_service = AnalysisRunService(dataset_service=dataset_service)
    project_dir = tmp_path / "project"
    dataset = _analysis_dataset()
    dataset_service.save_analysis_ready_dataset(project_dir, dataset)

    result = run_service.run_meta_analysis(project_dir, dataset.dataset_id, "fixed")
    output_path = run_service.save_analysis_result(project_dir, result)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    reloaded = run_service.load_analysis_result(project_dir, result.result_id)

    assert result.result_state == STATISTICAL_RESULT_STATE_TESTING_LEVEL
    assert result.testing_level is True
    assert not is_formal_computed_result(result)
    assert blocks_formal_report_claim(result)
    assert payload["result_state"] == STATISTICAL_RESULT_STATE_TESTING_LEVEL
    assert reloaded is not None
    assert reloaded.result_state == STATISTICAL_RESULT_STATE_TESTING_LEVEL
    assert not is_report_ready_result(reloaded)


def test_m10_report_gates_testing_level_and_not_run_outputs(tmp_path: Path) -> None:
    missing_project = tmp_path / "missing"
    missing_project.mkdir()
    missing_report = FormalMarkdownReportBuilder().build_draft_markdown_report(missing_project).read_text(encoding="utf-8")
    assert "结果状态：尚未运行正式统计分析（not_run）" in missing_report
    assert "尚未运行正式统计分析" in missing_report
    assert "pooled effect、p value、forest plot、funnel plot" in missing_report

    project_dir = tmp_path / "testing"
    dataset_service = AnalysisDatasetService()
    run_service = AnalysisRunService(dataset_service=dataset_service)
    dataset = _analysis_dataset()
    dataset_service.save_analysis_ready_dataset(project_dir, dataset)
    result = run_service.run_meta_analysis(project_dir, dataset.dataset_id, "fixed")
    run_service.save_analysis_result(project_dir, result)

    report = FormalMarkdownReportBuilder().build_draft_markdown_report(project_dir).read_text(encoding="utf-8")
    assert "结果状态：测试级结果（testing_level）" in report
    assert "formal claim blocked：是" in report
    assert "测试级结果不能作为正式 computed 结果" in report


def test_m10_analysis_setup_ui_state_labels_old_output_as_testing(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    dataset_service = AnalysisDatasetService()
    run_service = AnalysisRunService(dataset_service=dataset_service)
    dataset = _analysis_dataset()
    dataset_service.save_analysis_ready_dataset(project_dir, dataset)
    result = run_service.run_meta_analysis(project_dir, dataset.dataset_id, "fixed")
    run_service.save_analysis_result(project_dir, result)
    (project_dir / "analysis" / "analysis_result.json").write_text(
        json.dumps({"result": analysis_result_to_dict(result), "result_state": result.result_state}, ensure_ascii=False),
        encoding="utf-8",
    )

    state = analysis_setup_state_from_project(project_dir)

    assert state.result_state_summary["state"] == STATISTICAL_RESULT_STATE_TESTING_LEVEL
    assert state.result_state_summary["label_zh"] == "测试级结果"
    assert state.result_state_summary["blocks_formal_report_claim"] is True


def _analysis_dataset() -> AnalysisReadyDataset:
    rows = [
        _binary_row(10, 100, 20, 100, "study-1", "rec-1"),
        _binary_row(15, 110, 18, 105, "study-2", "rec-2"),
    ]
    return AnalysisReadyDataset(
        dataset_id="ards-test",
        project_id="meta-test",
        profile_type="TREATMENT_EFFECT_META",
        outcome_name="Mortality",
        effect_measure="OR",
        outcome_data_type="binary",
        included_extraction_ids=["extr-1", "extr-2"],
        excluded_extraction_ids=[],
        study_rows=rows,
        validation_errors=[],
        validation_warnings=[],
        created_at=now_utc(),
    )


def _binary_row(events_1: int, total_1: int, events_0: int, total_0: int, study_id: str, record_id: str) -> StudyAnalysisRow:
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
            "experimental_events": events_1,
            "experimental_non_events": total_1 - events_1,
            "experimental_total": total_1,
            "control_events": events_0,
            "control_non_events": total_0 - events_0,
            "control_total": total_0,
            "effect_measure": "OR",
        },
        analysis_status="included",
    )
