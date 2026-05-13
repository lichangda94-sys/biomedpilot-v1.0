from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.models.dedup import DuplicateGroup
from app.meta_analysis.pages.criteria_page import criteria_page_state_from_project, initial_criteria_page_state
from app.meta_analysis.pages.duplicate_review_page import duplicate_review_state_from_groups, initial_duplicate_review_state
from app.meta_analysis.pages.screening_page import initial_screening_state, title_abstract_screening_state_from_queue
from app.meta_analysis.services.criteria_service import CriteriaBuilderService


def test_ui1c_duplicate_review_state_has_chinese_copy_and_keeps_english_decisions() -> None:
    state = initial_duplicate_review_state()

    assert state.title == "文献去重"
    assert state.title_zh == "去重审核"
    assert "0.1.0-internal-beta" in state.status_label_zh
    assert "合并预览" in state.description_zh
    assert {"keep_both", "mark_not_duplicate", "exclude_duplicate", "merge"} <= set(state.interactive_decision_options)
    assert {"都保留", "标记为非重复", "排除重复记录", "合并记录"} <= set(state.decision_option_labels_zh)


def test_ui1c_duplicate_review_conflicts_have_chinese_field_names() -> None:
    group = DuplicateGroup(
        group_id="dup-1",
        records=[
            {"record_id": "rec-1", "title": "Short title", "authors": ["Smith J"], "year": "2024", "journal": "Journal A", "doi": "10.1000/a"},
            {"record_id": "rec-2", "title": "Longer title", "authors": ["Wang M"], "year": "2025", "journal": "Journal B", "doi": "10.1000/a"},
        ],
        match_reason="doi_exact,title_author_year_journal_suspected",
        confidence=0.91,
        status="pending",
    )

    state = duplicate_review_state_from_groups(groups=[group], original_record_count=2)

    assert state.group_summaries[0].duplicate_type_zh in {"精确重复", "疑似重复"}
    field_names = {item.field_name: item.field_name_zh for item in state.field_conflict_summary}
    assert field_names["title"] == "题名"
    assert field_names["authors"] == "作者"
    assert field_names["year/date"] == "年份 / 日期"
    assert field_names["journal/publication_title"] == "期刊 / 出版物名称"
    assert state.warning_summary_zh


def test_ui1c_criteria_state_has_chinese_sections_and_readiness(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"

    initial = initial_criteria_page_state(project_dir)
    assert initial.title_zh == "纳入与排除标准"
    assert initial.inclusion_title_zh == "纳入标准"
    assert initial.exclusion_title_zh == "排除标准"
    assert initial.readiness_status_zh == "未开始"

    (project_dir / "protocol").mkdir(parents=True)
    (project_dir / "protocol" / "review_protocol.json").write_text("{}", encoding="utf-8")
    service = CriteriaBuilderService()
    service.save_criteria(project_dir, inclusion_labels=["human studies"], exclusion_labels=["wrong population"])

    state = criteria_page_state_from_project(project_dir, service=service)

    assert state.title == "Criteria Builder"
    assert state.title_zh == "纳入与排除标准"
    assert state.readiness_status == "ready"
    assert state.readiness_status_zh == "已就绪"
    assert state.next_step_zh == "下一步：使用标准开展标题摘要筛选。"


def test_ui1c_screening_state_has_chinese_decisions_filters_and_progress(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    queue_path = project_dir / "screening" / "queue.json"
    queue_path.parent.mkdir(parents=True)
    queue_path.write_text(
        json.dumps(
            {
                "screening_records": [
                    {
                        "screening_record_id": "screen-1",
                        "record_id": "rec-1",
                        "title": "Trial A",
                        "abstract": "Abstract A",
                        "doi": "10.1000/a",
                        "pmid": "123456",
                        "decision": "maybe",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    base = initial_screening_state()
    state = title_abstract_screening_state_from_queue(queue_path, project_dir=project_dir)

    assert base.title_zh == "标题摘要筛选"
    assert "0.1.0-internal-beta" in state.status_label_zh
    assert state.current_record is not None
    assert state.current_record.decision == "maybe"
    assert state.current_record.decision_zh == "可能纳入"
    assert state.current_record.source_link_labels_zh == ("打开 DOI", "打开 PubMed")
    assert {"纳入", "排除", "可能纳入", "需要复核", "待筛选"} <= set(state.decision_option_labels_zh)
    assert {"全部", "待筛选", "纳入", "排除", "可能纳入", "需要复核"} <= set(state.filter_view_labels_zh)
    assert state.progress_labels_zh["total"] == "总数"
    assert state.progress_summary["needs_review"] == 1


def test_ui1c_missing_screening_queue_has_chinese_empty_state(tmp_path: Path) -> None:
    state = title_abstract_screening_state_from_queue(tmp_path / "project" / "screening" / "missing.json", project_dir=tmp_path / "project")

    assert "missing_screening_queue" in state.warnings
    assert state.empty_state_zh == "没有可筛选记录。请先生成 screening queue。"
    assert "缺少 queue" in state.warning_summary_zh
