from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.services.formal_report_service import DRAFT_REPORT_M8_SCHEMA_VERSION, FormalMarkdownReportBuilder


def test_m8_draft_report_generation_with_complete_mock_project(tmp_path: Path) -> None:
    project_dir = _seed_m8_project(tmp_path / "complete")

    report_path = FormalMarkdownReportBuilder().build_draft_markdown_report(project_dir)
    report_text = report_path.read_text(encoding="utf-8")

    assert report_path == project_dir / "reports" / "formal_meta_report.md"
    assert DRAFT_REPORT_M8_SCHEMA_VERSION in report_text
    for heading in (
        "报告标题",
        "研究问题",
        "检索与导入概况",
        "去重结果",
        "PRISMA 流程摘要",
        "标题摘要筛选结果",
        "全文筛选结果",
        "纳入研究基本特征",
        "数据提取表摘要",
        "质量评价摘要",
        "分析计划",
        "统计分析状态",
        "局限性",
        "下一步建议",
        "开发者预览声明",
    ):
        assert heading in report_text
    assert "用户确认内容" in report_text
    assert "草稿内容" in report_text
    assert "建议内容" in report_text
    assert "testing-level output" in report_text
    assert "未来正式统计结果占位" in report_text
    assert "title_abstract_included：1" in report_text
    assert "full_text_confirmed：1" in report_text
    assert "Zhang 2025" in report_text
    assert "NOS" in report_text
    assert "随机效应" in report_text


def test_m8_draft_report_generation_with_missing_sections(tmp_path: Path) -> None:
    project_dir = tmp_path / "missing"
    project_dir.mkdir()

    report_path = FormalMarkdownReportBuilder().build_draft_markdown_report(project_dir)
    report_text = report_path.read_text(encoding="utf-8")

    assert "Missing artifact warnings" in report_text
    assert "structured_extraction_rows: missing / not generated" in report_text
    assert "confirmed_analysis_plan: missing / not generated" in report_text
    assert "统计分析结果尚未作为正式可发表结论生成" in report_text


def test_m8_report_does_not_expose_raw_paths_json_or_internal_ids(tmp_path: Path) -> None:
    project_dir = _seed_m8_project(tmp_path / "safe")

    report_text = FormalMarkdownReportBuilder().build_draft_markdown_report(project_dir).read_text(encoding="utf-8")

    assert str(project_dir) not in report_text
    assert "raw JSON" not in report_text
    assert "manifest_path" not in report_text
    assert "effect-internal-1" not in report_text
    assert "record-internal-1" not in report_text
    assert "unit-internal-1" not in report_text
    assert "analysis_plan_confirmed_v1.json" not in report_text


def _seed_m8_project(project_dir: Path) -> Path:
    for name in ("protocol", "literature", "deduplication", "screening", "fulltext", "extraction", "quality", "analysis", "reports"):
        (project_dir / name).mkdir(parents=True, exist_ok=True)
    _write_json(
        project_dir / "protocol" / "pico_workspace_confirmed.json",
        {
            "confirmed_population": "成人肺炎患者",
            "confirmed_intervention_or_exposure": "糖皮质激素",
            "confirmed_comparator": "常规治疗",
            "confirmed_outcomes": ["死亡率"],
            "confirmed_study_design": "randomized trial",
        },
    )
    _write_json(
        project_dir / "literature" / "literature_records.json",
        {
            "records": [
                {"record_id": "record-internal-1", "title": "Trial A", "source_database": "PubMed"},
                {"record_id": "record-internal-2", "title": "Trial B", "source_database": "RIS"},
            ]
        },
    )
    _write_json(
        project_dir / "deduplication" / "deduplicated_literature_v2.json",
        {"original_count": 2, "deduplicated_count": 2, "active_record_count": 2, "pending_duplicate_group_count": 0},
    )
    _write_json(
        project_dir / "screening" / "title_abstract_queue_v2.json",
        {"queue_records": [{"record_id": "record-internal-1"}, {"record_id": "record-internal-2"}]},
    )
    _write_json(
        project_dir / "screening" / "title_abstract_decisions_v2.json",
        {
            "screening_records": [
                {"record_id": "record-internal-1", "decision": "include", "evidence_state": "confirmed"},
                {"record_id": "record-internal-2", "decision": "exclude", "evidence_state": "user_edited"},
            ]
        },
    )
    _write_json(
        project_dir / "fulltext" / "fulltext_management_registry_v1.json",
        {"records": [{"record_id": "record-internal-1", "title": "Trial A", "fulltext_status": "full_text_confirmed"}]},
    )
    _write_json(
        project_dir / "extraction" / "extraction_effect_rows.json",
        {
            "effect_rows": [
                {
                    "effect_row_id": "effect-internal-1",
                    "record_id": "record-internal-1",
                    "study_unit_id": "unit-internal-1",
                    "study_unit_label": "Study A",
                    "evidence_state": "confirmed",
                    "extraction_status": "completed_by_user",
                    "m5_structured_fields": {
                        "study_id": "study-safe-1",
                        "first_author": "Zhang",
                        "year": "2025",
                        "study_design": "randomized trial",
                        "population": "成人肺炎患者",
                        "outcome": "死亡率",
                        "effect_measure_type": "OR",
                        "effect_estimate": "1.4",
                        "ci_lower": "1.1",
                        "ci_upper": "1.8",
                    },
                }
            ]
        },
    )
    _write_json(
        project_dir / "quality" / "quality_assessment_records_v1.json",
        {
            "quality_assessment_records": [
                {
                    "assessment_id": "qa-internal-1",
                    "study_id": "study-safe-1",
                    "tool_name": "NOS",
                    "status": "confirmed",
                    "overall_rating": "low_risk_or_good",
                }
            ]
        },
    )
    _write_json(
        project_dir / "analysis" / "analysis_plan_confirmed_v1.json",
        {
            "plan_state": "confirmed",
            "effect_measure_type": "OR",
            "model_preference": "random_effect",
            "heterogeneity_metrics": ["I2", "tau2", "Q"],
            "subgroup_plan": {"user_plan": "按疾病严重程度分层"},
            "sensitivity_plan": {"user_plan": "排除高风险研究"},
            "m7_warning_labels_zh": {"too_few_studies_for_pooled_analysis": "当前纳入研究数量可能不足"},
        },
    )
    return project_dir


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
