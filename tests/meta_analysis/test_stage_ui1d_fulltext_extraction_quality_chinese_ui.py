from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.attachment_page import attachment_state_from_project, initial_attachment_state
from app.meta_analysis.pages.extraction_page import initial_extraction_state, simplified_extraction_state_from_project
from app.meta_analysis.pages.fulltext_eligibility_page import fulltext_eligibility_state_from_project, initial_fulltext_eligibility_state
from app.meta_analysis.pages.quality_page import initial_quality_state, quality_state_from_project


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def seed_title_abstract_decisions(project_dir: Path) -> None:
    write_json(
        project_dir / "screening" / "title_abstract_decisions.json",
        {
            "records": [
                {"record_id": "rec-1", "title": "Trial A", "decision": "included"},
                {"record_id": "rec-2", "title": "Trial B", "decision": "maybe"},
            ]
        },
    )


def seed_final_included(project_dir: Path) -> None:
    write_json(
        project_dir / "fulltext" / "final_included_studies.json",
        {
            "included_studies": [
                {"record_id": "rec-1", "study_id": "study-1", "title": "Trial A", "year": "2025", "study_design": "randomized trial"},
            ]
        },
    )


def test_ui1d_attachment_state_has_chinese_status_and_mode_labels(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"

    initial = initial_attachment_state()
    state = attachment_state_from_project(project_dir)

    assert initial.title_zh == "全文 / 附件管理"
    assert "0.1.0-internal-beta" in state.status_label_zh
    assert "不自动下载 PDF" in state.description_zh
    assert {"忽略附件", "链接现有文件", "复制到项目库"} <= set(state.mode_option_labels_zh)
    assert state.attachment_registry_missing is True
    assert state.attachment_validation_status_zh == "无附件"
    assert state.missing_fulltext_report_status_zh == "未生成"


def test_ui1d_fulltext_eligibility_state_has_chinese_status_options(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_title_abstract_decisions(project_dir)

    initial = initial_fulltext_eligibility_state(project_dir)
    state = fulltext_eligibility_state_from_project(project_dir)

    assert initial.title_zh == "全文筛选"
    assert "0.1.0-internal-beta" in state.status_label_zh
    assert "已链接本地 PDF" in state.status_option_labels_zh
    assert "纳入数据提取" in state.status_option_labels_zh
    assert state.candidate_count == 2
    assert state.decision_count_labels_zh["total"] == "总数"


def test_ui1d_extraction_state_has_chinese_field_labels_and_export_copy(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_final_included(project_dir)

    initial = initial_extraction_state()
    state = simplified_extraction_state_from_project(project_dir)

    assert initial.title_zh == "数据提取"
    assert "0.1.0-internal-beta" in state.status_label_zh
    assert state.field_labels_zh is not None
    assert state.field_labels_zh["record_id"] == "文献记录 ID"
    assert state.field_labels_zh["outcome_name"] == "结局名称"
    assert state.outcome_type_labels_zh is not None
    assert state.outcome_type_labels_zh["binary"] == "二分类结局"
    assert state.export_ready_zh in {"可以导出", "需要补齐后再导出"}
    assert state.study_rows[0].status == "needs_extraction"


def test_ui1d_quality_state_has_chinese_form_copy_and_suggestion_labels(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    seed_final_included(project_dir)

    initial = initial_quality_state()
    state = quality_state_from_project(project_dir)

    assert initial.title_zh == "质量评价"
    assert "0.1.0-internal-beta" in state.status_label_zh
    assert {"选择研究", "选择评价工具", "领域判断", "领域备注", "总体判断", "评价人备注"} <= set(initial.form_section_labels_zh)
    assert state.tool_label_zh == "质量评价工具"
    assert state.domain_note_label_zh == "领域备注"
    assert state.overall_suggestion_label_zh == "总体判断建议"
    assert state.completeness_label_zh == "质量评价完整性"
    assert state.study_rows[0].recommended_tool == "RoB2 simplified"
