from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.meta_analysis.pages.analysis_page import meta_statistics_engine_state_from_project
from app.meta_analysis.services.analysis_plan_service import AnalysisPlanService
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.manual_extraction_effect_row_service import ManualExtractionEffectRowService
from app.meta_analysis.services.meta_statistics_engine_service import (
    META_STATISTICS_ANALYSIS_MANIFEST_SCHEMA_VERSION,
    META_STATISTICS_ANALYSIS_RUN_SCHEMA_VERSION,
    META_STATISTICS_STANDARDIZED_RESULT_SCHEMA_VERSION,
    MetaStatisticsEngineService,
)
from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def seed_protocol(project_dir: Path, meta_type: str) -> None:
    pico = PICOWorkspaceService()
    pico.generate_draft(project_dir, "成人肺炎患者使用糖皮质激素能否降低死亡率", pico_mode="pico")
    pico.confirm_protocol(project_dir, actor="reviewer", confirmed_meta_type=meta_type)


def add_unit(manual: ManualExtractionEffectRowService, project_dir: Path, index: int, *, study_design: str = "trial") -> dict[str, object]:
    return manual.create_study_unit(
        project_dir,
        record_id=f"rec-{index}",
        study_unit_label=f"Study {index}",
        study_design=study_design,
    ).payload


def seed_binary_plan(project_dir: Path, *, effect_measure: str = "OR") -> tuple[AnalysisPlanService, list[str]]:
    seed_protocol(project_dir, "treatment_comparative_meta")
    manual = ManualExtractionEffectRowService()
    ids: list[str] = []
    rows = [
        (24, 80, 15, 80),
        (18, 76, 20, 75),
        (11, 60, 21, 62),
    ]
    for index, (e1, n1, e0, n0) in enumerate(rows, start=1):
        unit = add_unit(manual, project_dir, index)
        row = manual.create_effect_row(
            project_dir,
            study_unit_id=str(unit["study_unit_id"]),
            schema_meta_type="binary_outcome_meta",
            outcome_name="Mortality",
            timepoint="28 days",
            subgroup_label="severe" if index < 3 else "non-severe",
            data_fields={"group_1_n": n1, "group_1_events": e1, "group_2_n": n0, "group_2_events": e0},
            analysis_role="primary_effect_candidate",
            analysis_eligibility="candidate",
        ).payload
        ids.append(str(row["effect_row_id"]))
    plan = AnalysisPlanService()
    plan.generate_draft(project_dir)
    plan.confirm_plan(project_dir, actor="reviewer", confirmed_model="random_effects", confirmed_effect_measure=effect_measure, primary_effect_row_ids=ids)
    return plan, ids


def seed_continuous_plan(project_dir: Path, *, effect_measure: str = "MD") -> None:
    seed_protocol(project_dir, "continuous_outcome_meta")
    manual = ManualExtractionEffectRowService()
    ids: list[str] = []
    for index, offset in enumerate((0.0, 0.4, -0.2), start=1):
        unit = add_unit(manual, project_dir, index)
        row = manual.create_effect_row(
            project_dir,
            study_unit_id=str(unit["study_unit_id"]),
            schema_meta_type="continuous_outcome_meta",
            outcome_name="Score",
            data_fields={
                "group_1_n": 35 + index,
                "group_1_mean": 12.0 + offset,
                "group_1_sd": 2.2,
                "group_2_n": 34 + index,
                "group_2_mean": 10.0,
                "group_2_sd": 2.0,
            },
            analysis_eligibility="candidate",
        ).payload
        ids.append(str(row["effect_row_id"]))
    plan = AnalysisPlanService()
    plan.generate_draft(project_dir)
    plan.confirm_plan(project_dir, actor="reviewer", confirmed_effect_measure=effect_measure, primary_effect_row_ids=ids)


def seed_reported_plan(project_dir: Path, *, meta_type: str, effect_measure: str, values: tuple[float, ...]) -> None:
    seed_protocol(project_dir, meta_type)
    manual = ManualExtractionEffectRowService()
    ids: list[str] = []
    for index, value in enumerate(values, start=1):
        unit = add_unit(manual, project_dir, index, study_design="cohort")
        row = manual.create_effect_row(
            project_dir,
            study_unit_id=str(unit["study_unit_id"]),
            schema_meta_type=meta_type,
            data_input_mode="reported_effect_size",
            outcome_name="Overall survival" if effect_measure == "HR" else "Correlation",
            data_fields={"effect_measure": effect_measure, "effect_value": value, "ci_low": max(0.01, value * 0.75), "ci_high": value * 1.25},
            analysis_eligibility="candidate",
        ).payload
        ids.append(str(row["effect_row_id"]))
    plan = AnalysisPlanService()
    plan.generate_draft(project_dir)
    plan.confirm_plan(project_dir, actor="reviewer", confirmed_effect_measure=effect_measure, primary_effect_row_ids=ids)


def seed_diagnostic_plan(project_dir: Path) -> None:
    seed_protocol(project_dir, "diagnostic_accuracy_meta")
    manual = ManualExtractionEffectRowService()
    ids: list[str] = []
    for index, counts in enumerate(((42, 5, 8, 45), (55, 8, 10, 50), (36, 7, 9, 48)), start=1):
        unit = add_unit(manual, project_dir, index, study_design="diagnostic accuracy")
        row = manual.create_effect_row(
            project_dir,
            study_unit_id=str(unit["study_unit_id"]),
            schema_meta_type="diagnostic_accuracy_meta",
            outcome_name="Diagnosis",
            data_fields={"tp": counts[0], "fp": counts[1], "fn": counts[2], "tn": counts[3]},
            analysis_eligibility="candidate",
        ).payload
        ids.append(str(row["effect_row_id"]))
    plan = AnalysisPlanService()
    plan.generate_draft(project_dir)
    plan.confirm_plan(project_dir, actor="reviewer", confirmed_effect_measure="DOR", primary_effect_row_ids=ids)


def test_statistics_engine_requires_confirmed_analysis_plan(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="confirmed_analysis_plan_required"):
        MetaStatisticsEngineService().run_statistics(tmp_path)

    assert not (tmp_path / "analysis" / "runs").exists()
    assert not (tmp_path / "analysis" / "results").exists()


def test_binary_or_and_rr_run_from_confirmed_plan_only(tmp_path: Path) -> None:
    seed_binary_plan(tmp_path / "or", effect_measure="OR")
    seed_binary_plan(tmp_path / "rr", effect_measure="RR")

    or_result = MetaStatisticsEngineService().run_statistics(tmp_path / "or", actor="reviewer")
    rr_result = MetaStatisticsEngineService().run_statistics(tmp_path / "rr", actor="reviewer")

    assert or_result.analysis_run["schema_version"] == META_STATISTICS_ANALYSIS_RUN_SCHEMA_VERSION
    assert or_result.standardized_result["schema_version"] == META_STATISTICS_STANDARDIZED_RESULT_SCHEMA_VERSION
    assert or_result.standardized_result["effect_measure"] == "OR"
    assert rr_result.standardized_result["effect_measure"] == "RR"
    assert or_result.standardized_result["pooled_effect"] > 0
    assert rr_result.standardized_result["pooled_effect"] > 0
    assert or_result.standardized_result["heterogeneity_q"] >= 0
    assert or_result.standardized_result["i_squared"] >= 0
    assert or_result.standardized_result["tau_squared"] >= 0
    assert len(or_result.standardized_result["sensitivity_results"]) == 3
    assert or_result.standardized_result["publication_bias_results"]["funnel_data"]


def test_continuous_md_smd_survival_hr_and_correlation_run(tmp_path: Path) -> None:
    seed_continuous_plan(tmp_path / "md", effect_measure="MD")
    seed_continuous_plan(tmp_path / "smd", effect_measure="SMD")
    seed_reported_plan(tmp_path / "hr", meta_type="survival_outcome_meta", effect_measure="HR", values=(0.72, 0.81, 0.69))
    seed_reported_plan(tmp_path / "corr", meta_type="correlation_meta", effect_measure="CORRELATION", values=(0.24, 0.32, 0.28))

    md = MetaStatisticsEngineService().run_statistics(tmp_path / "md").standardized_result
    smd = MetaStatisticsEngineService().run_statistics(tmp_path / "smd").standardized_result
    hr = MetaStatisticsEngineService().run_statistics(tmp_path / "hr").standardized_result
    corr = MetaStatisticsEngineService().run_statistics(tmp_path / "corr").standardized_result

    assert md["effect_measure"] == "MD"
    assert smd["effect_measure"] == "SMD"
    assert hr["effect_measure"] == "HR"
    assert corr["effect_measure"] == "CORRELATION"
    assert all(result["testing_level_notice"].startswith("Developer Preview") for result in (md, smd, hr, corr))


def test_diagnostic_2x2_runs_with_testing_warning(tmp_path: Path) -> None:
    seed_diagnostic_plan(tmp_path)

    result = MetaStatisticsEngineService().run_statistics(tmp_path).standardized_result

    assert result["effect_measure"] == "DOR"
    assert result["pooled_effect"] > 0
    assert any("diagnostic_2x2_testing_basic" in warning for row in result["study_results"] for warning in row["warnings"])


def test_statistics_outputs_manifest_audit_governance_and_does_not_advance_prisma_or_conclusion(tmp_path: Path) -> None:
    audit = MetaAuditLogService()
    governance = MetaResearchGovernanceService(audit_log=audit)
    seed_binary_plan(tmp_path, effect_measure="OR")
    service = MetaStatisticsEngineService(audit_log=audit, research_governance=governance)

    result = service.run_statistics(tmp_path, actor="reviewer")
    manifest = read_json(tmp_path / "analysis" / "analysis_manifest.json")
    run_payload = read_json(Path(result.run_path))
    standardized = read_json(Path(result.result_path))
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)
    gov_events = governance.list_events(tmp_path)
    audit_events = audit.list_events(tmp_path)

    assert manifest["schema_version"] == META_STATISTICS_ANALYSIS_MANIFEST_SCHEMA_VERSION
    assert manifest["latest_analysis_run_id"] == result.analysis_run_id
    assert manifest["testing_level"] is True
    assert run_payload["source_confirmed_analysis_plan_id"]
    assert run_payload["result_status"] == "testing_result_generated"
    assert standardized["medical_conclusion_status"] == "not_generated"
    assert standardized["production_grade"] is False
    assert not (tmp_path / "analysis" / "analysis_results.json").exists()
    assert not (tmp_path / "reports" / "prisma_flow_summary.json").exists()
    assert prisma.records_screened == 0
    assert prisma.studies_included == 0
    assert any(event.target_type == "analysis_run" and event.metadata.get("workflow_action") == "analysis_run requested" for event in gov_events)
    assert any(event.target_type == "analysis_run" and event.metadata.get("workflow_action") == "analysis_run executed" for event in gov_events)
    assert any(event.target_type == "analysis_result" and event.metadata.get("workflow_action") == "analysis_result generated" for event in gov_events)
    assert any(event.event_type == "analysis_run_completed" and event.target_type == "analysis_result" for event in audit_events)
    assert (tmp_path / "logs" / "analysis" / "analysis_audit.jsonl").exists()


def test_statistics_page_state_exposes_confirmed_plan_guardrails(tmp_path: Path) -> None:
    seed_binary_plan(tmp_path, effect_measure="OR")
    service = MetaStatisticsEngineService()
    service.run_statistics(tmp_path)

    state = meta_statistics_engine_state_from_project(tmp_path, service=service)

    assert state.run_schema_version == META_STATISTICS_ANALYSIS_RUN_SCHEMA_VERSION
    assert state.result_schema_version == META_STATISTICS_STANDARDIZED_RESULT_SCHEMA_VERSION
    assert state.manifest_schema_version == META_STATISTICS_ANALYSIS_MANIFEST_SCHEMA_VERSION
    assert state.confirmed_plan_status == "confirmed"
    assert state.latest_run_id
    assert state.latest_result_id
    assert state.primary_actions == ("运行统计分析", "查看分析计划", "查看输入校验", "查看统计结果", "生成 canonical result artifacts")
    assert state.safety_flags == {
        "requires_confirmed_analysis_plan": True,
        "modifies_extraction_records": False,
        "modifies_quality_assessment": False,
        "advances_prisma": False,
        "generates_medical_conclusion": False,
        "production_grade": False,
    }
