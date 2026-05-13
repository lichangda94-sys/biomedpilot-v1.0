from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.analysis_page import analysis_setup_state_from_project, initial_analysis_state
from app.meta_analysis.pages.reporting_page import initial_reporting_state, reporting_prisma_trace_state_from_project


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def seed_reporting_sources(project_dir: Path) -> None:
    write_json(project_dir / "literature" / "literature_records.json", {"records": [{"record_id": "rec-1"}]})
    write_json(project_dir / "deduplication" / "deduplicated_literature.json", {"deduplicated_records": [{"record_id": "rec-1"}]})
    write_json(project_dir / "screening" / "screening_decisions.json", {"screening_records": [{"record_id": "rec-1", "decision": "included"}]})


def test_ui1e_analysis_state_has_chinese_sections_models_and_blocked_methods(tmp_path: Path) -> None:
    initial = initial_analysis_state()
    state = analysis_setup_state_from_project(tmp_path / "empty")

    assert initial.title_zh == "统计分析"
    assert "0.1.0-internal-beta" in state.status_label_zh
    assert state.section_labels_zh is not None
    assert state.section_labels_zh["preflight"] == "分析预检"
    assert state.section_labels_zh["figures_tables"] == "图表与结果表"
    assert state.model_option_labels_zh == ("固定效应", "随机效应")
    assert state.advanced_method_status["network_meta"] == "network_meta_analysis_not_implemented"
    assert state.advanced_method_status_zh is not None
    assert state.advanced_method_status_zh["network_meta"] == "Network Meta 未实现"
    assert "analysis_plan_missing" in state.warnings


def test_ui1e_reporting_state_has_chinese_sections_and_pdf_placeholder_copy() -> None:
    state = initial_reporting_state()

    assert state.title_zh == "PRISMA / 报告导出"
    assert "0.1.0-internal-beta" in state.status_label_zh
    assert state.section_labels_zh is not None
    assert state.section_labels_zh["formal_markdown"] == "正式报告雏形 Markdown"
    assert state.section_labels_zh["pdf_placeholder"] == "PDF placeholder"
    assert "正式 PDF 未开放" in state.warning_summary_zh
    assert any("正式 PDF report 未开放" in item for item in state.testing_limitations)


def test_ui1e_prisma_trace_state_has_chinese_labels_and_missing_warnings(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_reporting_sources(project_dir)

    trace = reporting_prisma_trace_state_from_project(project_dir)

    assert trace.title_zh == "PRISMA 来源追溯"
    assert trace.source_references_label_zh == "来源引用"
    assert trace.source_reference_warnings_label_zh == "来源 warning"
    assert trace.audit_reference_warnings_label_zh == "审计 warning"
    assert trace.workflow_event_counts_label_zh == "流程事件数量"
    assert trace.review_log_jsonl_path.endswith("reports/review_log.jsonl")
    assert trace.source_references
    assert {row.status_zh for row in trace.source_references} <= {"可用", "缺失", "available", "missing"}
    assert trace.audit_reference_warnings
