from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.extraction.schema_registry import TREATMENT_EFFECT_META
from app.meta_analysis.models.extraction import (
    BinaryOutcomeData,
    ExtractedOutcome,
    ExtractionRecord,
    OutcomeDataType,
    StudyCharacteristics,
)
from app.meta_analysis.pages.analysis_page import analysis_setup_state_from_project
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.services.analysis_run_service import AnalysisRunService
from app.meta_analysis.services.analysis_setup_service import AnalysisSetupService
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.extraction_record_storage_service import ExtractionRecordStorageService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter


def make_setup(tmp_path: Path) -> tuple[AnalysisSetupService, ExtractionRecordStorageService, DataCenter, Path]:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    audit_log = MetaAuditLogService()
    extraction_storage = ExtractionRecordStorageService(task_center=task_center, data_center=data_center)
    dataset_service = AnalysisDatasetService(extraction_storage=extraction_storage, task_center=task_center, data_center=data_center)
    run_service = AnalysisRunService(dataset_service=dataset_service, task_center=task_center, data_center=data_center, audit_log=audit_log)
    contract = MetaProjectContractService(data_center=data_center, task_center=task_center)
    setup = AnalysisSetupService(
        dataset_service=dataset_service,
        run_service=run_service,
        audit_log=audit_log,
        data_center=data_center,
        project_contract=contract,
    )
    return setup, extraction_storage, data_center, tmp_path / "project"


def test_empty_project_analysis_setup_state_does_not_crash(tmp_path: Path) -> None:
    state = analysis_setup_state_from_project(tmp_path / "empty")

    assert state.status_label == "测试中 / Developer Preview"
    assert state.preflight_summary["status"] == "missing"
    assert "analysis_plan_missing" in state.warnings
    assert state.advanced_method_status["network_meta"] == "network_meta_analysis_not_implemented"


def test_analysis_plan_preflight_writes_dataset_alias_and_warnings(tmp_path: Path) -> None:
    setup, extraction_storage, data_center, project_dir = make_setup(tmp_path)
    extraction_storage.save_extraction_records(
        project_dir,
        [
            binary_record("extr-1", "rec-1", "Study 1", 10, 100, 20, 100),
            binary_record("extr-2", "rec-2", "Study 2", 15, 110, 18, 105),
        ],
    )
    plan = setup.create_plan(
        project_dir,
        profile_type=TREATMENT_EFFECT_META,
        outcome_name="Mortality",
        effect_measure="OR",
        model="random",
        zero_event_correction="continuity_0.5",
        subgroup_variable="subgroup",
    )

    summary = setup.run_preflight(project_dir, plan)

    assert summary.success is True
    assert (project_dir / "analysis" / "analysis_plan.json").exists()
    assert (project_dir / "analysis" / "analysis_ready_dataset.json").exists()
    assert (project_dir / "analysis" / "applicability_warnings.json").exists()
    assert (project_dir / "project.json").exists()
    alias_payload = json.loads((project_dir / "analysis" / "analysis_ready_dataset.json").read_text(encoding="utf-8"))
    assert alias_payload["dataset"]["outcome_name"] == "Mortality"
    warning_payload = json.loads((project_dir / "analysis" / "applicability_warnings.json").read_text(encoding="utf-8"))
    assert "random_effects_tau_squared_unstable_with_fewer_than_three_studies" in warning_payload["warnings"]
    assert any(asset.data_type == "analysis_plan" for asset in data_center.list_assets(project_dir.name))


def test_analysis_setup_run_writes_result_alias_and_audit(tmp_path: Path) -> None:
    setup, extraction_storage, data_center, project_dir = make_setup(tmp_path)
    extraction_storage.save_extraction_records(
        project_dir,
        [
            binary_record("extr-1", "rec-1", "Study 1", 10, 100, 20, 100),
            binary_record("extr-2", "rec-2", "Study 2", 15, 110, 18, 105),
        ],
    )
    plan = setup.create_plan(project_dir, profile_type=TREATMENT_EFFECT_META, outcome_name="Mortality", effect_measure="OR", model="fixed")

    summary = setup.run_analysis_from_plan(project_dir, plan)

    assert summary.success is True
    assert summary.result is not None
    assert (project_dir / "analysis" / "analysis_result.json").exists()
    result_payload = json.loads((project_dir / "analysis" / "analysis_result.json").read_text(encoding="utf-8"))
    assert result_payload["result"]["effect_measure"] == "OR"
    audit_lines = (project_dir / "audit" / "audit_log.jsonl").read_text(encoding="utf-8").splitlines()
    assert any("analysis_run_completed" in line for line in audit_lines)
    assert any(asset.data_type == "analysis_result_alias" for asset in data_center.list_assets("meta-test"))


def test_analysis_setup_blocks_not_implemented_methods(tmp_path: Path) -> None:
    setup, _extraction_storage, _data_center, project_dir = make_setup(tmp_path)

    plan = setup.create_plan(
        project_dir,
        profile_type=TREATMENT_EFFECT_META,
        outcome_name="Mortality",
        effect_measure="OR",
        requested_method="network_meta",
    )
    summary = setup.run_preflight(project_dir, plan)

    assert summary.success is False
    assert "network_meta_analysis_not_implemented" in summary.errors
    warnings_payload = json.loads((project_dir / "analysis" / "applicability_warnings.json").read_text(encoding="utf-8"))
    assert warnings_payload["blocked_methods"]["network_meta"] == "network_meta_analysis_not_implemented"


def test_analysis_setup_page_state_distinguishes_plan_dataset_result_and_advanced_methods(tmp_path: Path) -> None:
    setup, extraction_storage, _data_center, project_dir = make_setup(tmp_path)
    extraction_storage.save_extraction_records(
        project_dir,
        [
            binary_record("extr-1", "rec-1", "Study 1", 10, 100, 20, 100),
            binary_record("extr-2", "rec-2", "Study 2", 15, 110, 18, 105),
        ],
    )
    plan = setup.create_plan(project_dir, profile_type=TREATMENT_EFFECT_META, outcome_name="Mortality", effect_measure="OR", model="fixed")
    setup.run_analysis_from_plan(project_dir, plan)

    state = analysis_setup_state_from_project(project_dir, service=setup)

    assert "profile_type" in state.setup_inputs
    assert state.preflight_summary["status"] == "available"
    assert state.run_result_summary["status"] == "available"
    assert state.run_result_summary["model"] == "fixed"
    assert state.advanced_method_status["hsroc"] == "diagnostic_hsroc_not_implemented"
    assert "Developer Preview" in state.status_label


def binary_record(
    extraction_id: str,
    record_id: str,
    first_author: str,
    experimental_events: int,
    experimental_total: int,
    control_events: int,
    control_total: int,
) -> ExtractionRecord:
    return ExtractionRecord(
        extraction_id=extraction_id,
        project_id="meta-test",
        record_id=record_id,
        study_id=f"study-{record_id}",
        reviewer_id="reviewer-1",
        profile_type=TREATMENT_EFFECT_META,
        study_characteristics=StudyCharacteristics(
            first_author=first_author,
            year=2024,
            country="CN",
            study_design="RCT",
            population="Adults",
            sample_size=120,
        ),
        outcomes=[
            ExtractedOutcome(
                outcome_id=f"out-{extraction_id}",
                outcome_data_type=OutcomeDataType.BINARY.value,
                data=BinaryOutcomeData(
                    outcome_name="Mortality",
                    effect_measure="OR",
                    experimental_events=experimental_events,
                    experimental_total=experimental_total,
                    control_events=control_events,
                    control_total=control_total,
                ),
            )
        ],
        validation_status="valid",
        created_at="2026-04-28T00:00:00+00:00",
        updated_at="2026-04-28T00:00:00+00:00",
    )
