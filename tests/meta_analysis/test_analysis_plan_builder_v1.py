from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.meta_analysis.pages.analysis_page import analysis_plan_builder_state_from_project
from app.meta_analysis.services.analysis_plan_service import (
    ANALYSIS_PLAN_DRAFT_SCHEMA_VERSION,
    ANALYSIS_PLAN_MANIFEST_SCHEMA_VERSION,
    CONFIRMED_ANALYSIS_PLAN_SCHEMA_VERSION,
    AnalysisPlanService,
)
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.manual_extraction_effect_row_service import ManualExtractionEffectRowService
from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService
from app.meta_analysis.services.quality_service import QualityAssessmentService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def seed_confirmed_protocol(project_dir: Path, *, meta_type: str = "treatment_comparative_meta") -> None:
    pico = PICOWorkspaceService()
    pico.generate_draft(project_dir, "成人肺炎患者使用糖皮质激素能否降低死亡率", pico_mode="pico")
    pico.confirm_protocol(project_dir, actor="reviewer", confirmed_meta_type=meta_type)


def seed_effect_rows(project_dir: Path) -> tuple[ManualExtractionEffectRowService, dict[str, object], dict[str, object], dict[str, object]]:
    manual = ManualExtractionEffectRowService()
    unit = manual.create_study_unit(project_dir, record_id="rec-1", study_unit_label="Study A", study_design="randomized trial").payload
    primary = manual.create_effect_row(
        project_dir,
        study_unit_id=str(unit["study_unit_id"]),
        schema_meta_type="binary_outcome_meta",
        outcome_name="Mortality",
        timepoint="28 days",
        data_fields={"group_1_n": 60, "group_1_events": 20, "group_2_n": 60, "group_2_events": 10, "effect_measure": "OR"},
        analysis_role="primary_effect_candidate",
        analysis_eligibility="candidate",
    ).payload
    second_primary = manual.create_effect_row(
        project_dir,
        study_unit_id=str(unit["study_unit_id"]),
        schema_meta_type="binary_outcome_meta",
        outcome_name="Mortality",
        timepoint="28 days",
        data_fields={"group_1_n": 55, "group_1_events": 18, "group_2_n": 55, "group_2_events": 12, "effect_measure": "RR"},
        analysis_role="primary_effect_candidate",
        analysis_eligibility="candidate",
    ).payload
    missing = manual.create_effect_row(
        project_dir,
        study_unit_id=str(unit["study_unit_id"]),
        schema_meta_type="binary_outcome_meta",
        outcome_name="ICU stay",
        data_fields={"group_1_n": 40},
        analysis_role="secondary_effect_candidate",
        analysis_eligibility="candidate",
    ).payload
    return manual, primary, second_primary, missing


def test_analysis_plan_requires_confirmed_protocol(tmp_path: Path) -> None:
    service = AnalysisPlanService()

    with pytest.raises(ValueError, match="confirmed_protocol_required_for_analysis_plan"):
        service.generate_draft(tmp_path)

    assert not (tmp_path / "analysis" / "analysis_plan_draft_v1.json").exists()


def test_generates_analysis_plan_draft_from_effect_rows_and_quality_summary(tmp_path: Path) -> None:
    seed_confirmed_protocol(tmp_path)
    _, primary, second_primary, missing = seed_effect_rows(tmp_path)
    quality = QualityAssessmentService()
    qa = quality.create_quality_assessment_draft(
        tmp_path,
        study_id="study-1",
        record_id="rec-1",
        tool_name="ROB2",
        domains={"randomization": "low"},
        overall_rating="low",
        reviewer_id="rev-1",
    )
    quality.complete_quality_assessment_by_user(tmp_path, assessment_id=qa.assessment_id, actor="reviewer")

    result = AnalysisPlanService().generate_draft(tmp_path, actor="system")
    payload = read_json(tmp_path / "analysis" / "analysis_plan_draft_v1.json")
    manifest = read_json(tmp_path / "analysis" / "analysis_plan_manifest_v1.json")

    assert result.success is True
    assert payload["schema_version"] == ANALYSIS_PLAN_DRAFT_SCHEMA_VERSION
    assert payload["status"] == "draft"
    assert payload["source_confirmed_protocol_id"]
    assert payload["meta_type"] == "treatment_comparative_meta"
    assert payload["model_default"] == "random_effects"
    assert payload["analysis_run_status"] == "not_started"
    assert payload["analysis_ready_dataset_created"] is False
    assert payload["final_analysis_result_created"] is False
    assert payload["prisma_advanced"] is False
    assert {item["effect_row_id"] for item in payload["included_effect_row_candidates"]} == {primary["effect_row_id"], second_primary["effect_row_id"]}
    assert {item["effect_row_id"] for item in payload["excluded_effect_row_candidates"]} == {missing["effect_row_id"]}
    assert "multiple_primary_effect_candidates:" + str(primary["study_unit_id"]) in payload["warnings"]
    assert "effect_measure_mixed" in payload["warnings"]
    assert any(str(item).startswith("effect_row_missing_required_fields:") for item in payload["warnings"])
    assert manifest["schema_version"] == ANALYSIS_PLAN_MANIFEST_SCHEMA_VERSION
    assert manifest["analysis_run_status"] == "not_started"
    assert manifest["analysis_ready_dataset_created"] is False
    assert (tmp_path / "quality" / "quality_assessment_summary_v1.json").exists()
    assert not (tmp_path / "analysis" / "analysis_ready_datasets.json").exists()
    assert not (tmp_path / "analysis" / "analysis_results.json").exists()


def test_analysis_plan_warns_when_quality_is_not_completed_and_study_count_too_small(tmp_path: Path) -> None:
    seed_confirmed_protocol(tmp_path)
    seed_effect_rows(tmp_path)

    draft = AnalysisPlanService().generate_draft(tmp_path).payload

    assert "quality_assessment_not_completed" in draft["warnings"]
    assert "study_count_less_than_10_publication_bias_not_recommended" in draft["warnings"]
    assert draft["publication_bias_plan"]["egger"] == "planned_if_study_count_at_least_10"


def test_analysis_plan_defaults_for_meta_types(tmp_path: Path) -> None:
    cases = {
        "continuous_outcome_meta": ("MD", "not_applicable"),
        "survival_outcome_meta": ("HR", "log"),
        "prevalence_incidence_meta": ("PREVALENCE", "logit"),
        "diagnostic_accuracy_meta": ("DOR", "diagnostic_2x2"),
        "correlation_meta": ("Fisher z", "fisher_z"),
        "dose_response_meta": ("dose_response_slope", "dose_response_placeholder"),
    }
    for meta_type, expected in cases.items():
        project_dir = tmp_path / meta_type
        seed_confirmed_protocol(project_dir, meta_type=meta_type)
        draft = AnalysisPlanService().generate_draft(project_dir).payload
        rendered = json.dumps(draft, ensure_ascii=False).lower()

        assert draft["effect_measure"] == expected[0]
        assert expected[1] in rendered
        assert draft["status"] == "draft"
        assert draft["analysis_run_status"] == "not_started"


def test_confirmed_analysis_plan_requires_explicit_call_and_does_not_run_statistics_or_prisma(tmp_path: Path) -> None:
    audit = MetaAuditLogService()
    governance = MetaResearchGovernanceService(audit_log=audit)
    seed_confirmed_protocol(tmp_path)
    _, primary, _, _ = seed_effect_rows(tmp_path)
    service = AnalysisPlanService(audit_log=audit, research_governance=governance)

    draft = service.generate_draft(tmp_path, actor="system")
    assert not service.confirmed_path(tmp_path).exists()

    confirmed = service.confirm_plan(
        tmp_path,
        actor="reviewer",
        confirmed_model="random_effects",
        primary_effect_row_ids=(str(primary["effect_row_id"]),),
    )
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)
    governance_events = governance.list_events(tmp_path)
    audit_events = audit.list_events(tmp_path)

    assert confirmed.payload["schema_version"] == CONFIRMED_ANALYSIS_PLAN_SCHEMA_VERSION
    assert confirmed.payload["source_draft_id"] == draft.plan_id
    assert confirmed.payload["locked_for_analysis_run"] is True
    assert confirmed.payload["analysis_run_status"] == "not_started"
    assert confirmed.payload["analysis_ready_dataset_created"] is False
    assert confirmed.payload["final_analysis_result_created"] is False
    assert confirmed.payload["prisma_advanced"] is False
    assert not (tmp_path / "analysis" / "analysis_ready_datasets.json").exists()
    assert not (tmp_path / "analysis" / "analysis_results.json").exists()
    assert prisma.records_screened == 0
    assert prisma.studies_included == 0
    assert any(event.action == "draft_created" and event.target_type == "analysis_plan" for event in governance_events)
    assert any(event.action == "confirm" and event.status == "confirmed" and event.target_type == "analysis_plan" for event in governance_events)
    assert any(event.target_type == "effect_row_candidate" and event.metadata.get("analysis_plan_candidate_action") == "candidate_selected" for event in governance_events)
    assert any(event.event_type == "record_saved" and event.target_type == "analysis_plan" for event in audit_events)


def test_analysis_plan_page_state_exposes_draft_first_boundaries(tmp_path: Path) -> None:
    seed_confirmed_protocol(tmp_path)
    seed_effect_rows(tmp_path)
    service = AnalysisPlanService()
    service.generate_draft(tmp_path)

    state = analysis_plan_builder_state_from_project(tmp_path, service=service)

    assert state.draft_schema_version == ANALYSIS_PLAN_DRAFT_SCHEMA_VERSION
    assert state.confirmed_schema_version == CONFIRMED_ANALYSIS_PLAN_SCHEMA_VERSION
    assert state.confirmed_protocol_status == "confirmed"
    assert state.draft_status == "draft"
    assert state.confirmed_status == "not_confirmed"
    assert state.included_candidate_count == 2
    assert state.excluded_candidate_count == 1
    assert state.primary_actions == ("生成分析计划草稿", "查看候选效应量", "确认分析计划", "暂不运行统计")
    assert state.safety_flags == {
        "auto_confirms_analysis_plan": False,
        "creates_analysis_ready_dataset": False,
        "runs_statistics": False,
        "creates_final_analysis_result": False,
        "advances_prisma": False,
        "generates_medical_interpretation": False,
    }
