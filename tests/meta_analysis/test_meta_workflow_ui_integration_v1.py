from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.workflow_integration_page import meta_workflow_integration_state_from_project
from app.meta_analysis.search.search_strategy_builder_service import SearchStrategyBuilderService
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def step_by_id(project_dir: Path) -> dict[str, object]:
    state = meta_workflow_integration_state_from_project(project_dir)
    return {step.step_id: step for step in state.steps}


def test_meta_workflow_integration_state_has_fourteen_chinese_steps(tmp_path: Path) -> None:
    state = meta_workflow_integration_state_from_project(tmp_path)

    assert state.step_count == 14
    assert [step.title_zh for step in state.steps] == [
        "Meta 项目首页",
        "中文研究问题 / PICO",
        "检索策略",
        "PubMed 检索结果确认 / 文献导入",
        "文献库",
        "去重复核",
        "全文管理",
        "数据提取",
        "AI 辅助提取",
        "质量评价",
        "分析计划",
        "统计分析",
        "图表结果",
        "报告导出",
    ]
    for step in state.steps:
        assert step.status
        assert step.artifact_count >= 0
        assert step.artifact_summary
        assert step.warning_count == len(step.warnings)
        assert step.primary_action_zh
        assert step.next_action_zh
    assert state.safety_flags["auto_runs_statistics"] is False
    assert state.safety_flags["advances_prisma"] is False


def test_pico_and_search_steps_show_draft_and_confirmed_states(tmp_path: Path) -> None:
    pico = PICOWorkspaceService()
    pico.generate_draft(tmp_path, "高血压患者降压药对卒中风险的影响", pico_mode="pico")
    draft_steps = step_by_id(tmp_path)
    assert draft_steps["pico_workspace"].status == "草稿待确认"

    pico.confirm_protocol(tmp_path, actor="reviewer", confirmed_meta_type="treatment_comparative_meta")
    SearchStrategyBuilderService().generate_from_confirmed_protocol(tmp_path)
    confirmed_steps = step_by_id(tmp_path)

    assert confirmed_steps["pico_workspace"].status == "已确认"
    assert confirmed_steps["search_strategy"].status == "草稿待确认"
    assert "drafts=7" in confirmed_steps["search_strategy"].artifact_summary


def test_literature_pubmed_dedup_extraction_quality_and_analysis_plan_summaries(tmp_path: Path) -> None:
    write_json(
        tmp_path / "protocol" / "pubmed_candidates" / "preview-1_candidates_preview.json",
        {"schema_version": "meta_pubmed_candidate_preview.v1", "candidates": [{"candidate_id": "c1"}], "created_at": "2026-01-01T00:00:00Z"},
    )
    write_json(
        tmp_path / "protocol" / "pubmed_candidates" / "preview-1_candidate_selection.json",
        {"schema_version": "meta_pubmed_candidate_selection.v1", "candidates": [{"candidate_id": "c1", "decision": "selected"}]},
    )
    LiteratureLibraryService().import_records(
        tmp_path,
        raw_records=[{"title": "Trial A", "authors": ["Chen L"], "year": "2024", "pmid": "1"}],
        source_type="pubmed_confirmed_candidates",
    )
    write_json(
        tmp_path / "deduplication" / "duplicate_groups_v2.json",
        {"schema_version": "meta_duplicate_review_queue.v2", "duplicate_groups": [{"group_id": "g1", "risk_level": "red"}]},
    )
    write_json(
        tmp_path / "fulltext" / "fulltext_management_registry_v1.json",
        {"schema_version": "meta_fulltext_management_registry.v1", "records": [{"record_id": "r1", "fulltext_status": "pdf_attached"}]},
    )
    write_json(
        tmp_path / "extraction" / "extraction_study_units.json",
        {"schema_version": "collection", "study_units": [{"study_unit_id": "su1", "record_id": "r1"}]},
    )
    write_json(
        tmp_path / "extraction" / "extraction_effect_rows.json",
        {"schema_version": "collection", "effect_rows": [{"effect_row_id": "er1", "study_unit_id": "su1"}]},
    )
    write_json(tmp_path / "extraction" / "extraction_validation_report.json", {"missing_required_fields_count": 1})
    write_json(
        tmp_path / "extraction" / "extraction_ai_suggestion_queue.json",
        {"schema_version": "meta_ai_extraction_queue.v1", "suggestions": [{"suggestion_id": "s1", "status": "pending"}]},
    )
    write_json(
        tmp_path / "quality" / "quality_assessment_records_v1.json",
        {"schema_version": "meta_quality_assessment_records.v1", "quality_assessment_records": [{"assessment_id": "qa1", "status": "completed_by_user"}]},
    )
    write_json(tmp_path / "analysis" / "analysis_plan_draft_v1.json", {"analysis_plan_id": "draft-1", "status": "draft", "warnings": []})
    write_json(tmp_path / "analysis" / "analysis_plan_confirmed_v1.json", {"confirmed_analysis_plan_id": "confirmed-1"})

    steps = step_by_id(tmp_path)

    assert "previews=1" in steps["pubmed_handoff"].artifact_summary
    assert "selected=1" in steps["pubmed_handoff"].artifact_summary
    assert "records=1" in steps["literature_library"].artifact_summary
    assert "duplicate_groups=1" in steps["dedup_review"].artifact_summary
    assert "fulltext_records=1" in steps["fulltext_management"].artifact_summary
    assert "effect_rows=1" in steps["manual_extraction"].artifact_summary
    assert steps["manual_extraction"].warning_count == 1
    assert "suggestions=1" in steps["ai_extraction"].artifact_summary
    assert "completed=1" in steps["quality_assessment"].artifact_summary
    assert steps["analysis_plan"].status == "已确认"


def test_placeholder_pages_do_not_generate_statistics_figures_reports_or_prisma(tmp_path: Path) -> None:
    write_json(tmp_path / "analysis" / "analysis_plan_confirmed_v1.json", {"confirmed_analysis_plan_id": "confirmed-1"})
    before_prisma = PRISMAService().collect_prisma_numbers(tmp_path)

    steps = step_by_id(tmp_path)

    assert steps["statistics_analysis"].placeholder is True
    assert steps["statistics_analysis"].safety_flags["runs_statistics"] is False
    assert "不自动运行统计" in steps["statistics_analysis"].artifact_summary
    assert steps["figure_results"].placeholder is True
    assert steps["report_export"].placeholder is True
    assert not (tmp_path / "analysis" / "runs").exists()
    assert not (tmp_path / "analysis" / "results").exists()
    assert not (tmp_path / "figures").exists()
    assert not (tmp_path / "reports" / "formal_meta_report.md").exists()
    after_prisma = PRISMAService().collect_prisma_numbers(tmp_path)
    assert before_prisma.records_screened == after_prisma.records_screened == 0
    assert before_prisma.full_text_reports_assessed == after_prisma.full_text_reports_assessed == 0
    assert before_prisma.studies_included == after_prisma.studies_included == 0


def test_meta_workflow_integration_does_not_import_dataset_module() -> None:
    files = [
        Path("app/meta_analysis/pages/workflow_integration_page.py"),
        Path("app/meta_analysis/workspace.py"),
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "app.bioinformatics" not in text
