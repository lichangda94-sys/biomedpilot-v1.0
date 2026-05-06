from __future__ import annotations

import subprocess
from pathlib import Path

from app.meta_analysis.pages.workflow_dashboard_page import WORKFLOW_STEP_DEFINITIONS, workflow_dashboard_state_from_project
from app.meta_analysis.ui_text import (
    USER_MISSING_ARTIFACT_WARNING_ZH,
    WORKFLOW_STEP_TEXT,
    WORKFLOW_STATUS_ZH,
    warning_summary_zh,
    workflow_status_zh,
)
from app.meta_analysis.workspace import meta_workspace_layout_state
from app.shell.dashboard import build_dashboard_model


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ui1a_test_inputs_is_explicitly_ignored() -> None:
    completed = subprocess.run(
        ["git", "check-ignore", "-v", "test_inputs/demo_expression_matrix.csv"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert ".gitignore" in completed.stdout
    assert "test_inputs/" in completed.stdout


def test_ui1a_workflow_status_chinese_mapping() -> None:
    assert WORKFLOW_STATUS_ZH == {
        "Not started": "未开始",
        "In progress": "进行中",
        "Needs review": "需要复核",
        "Ready": "已就绪",
        "Completed": "已完成",
        "Developer Preview": "内部测试",
    }
    assert workflow_status_zh("Not started") == "未开始"
    assert workflow_status_zh("Needs review") == "需要复核"


def test_ui1a_all_workflow_steps_have_chinese_names_and_english_subtitles() -> None:
    step_ids = [str(item["step_id"]) for item in WORKFLOW_STEP_DEFINITIONS]

    assert len(step_ids) == 15
    assert set(step_ids) == set(WORKFLOW_STEP_TEXT)
    assert WORKFLOW_STEP_TEXT["literature_import"].title_zh == "文献导入"
    assert WORKFLOW_STEP_TEXT["duplicate_review"].subtitle_en == "Duplicate Review"
    assert WORKFLOW_STEP_TEXT["meta_analysis_run"].title_zh == "Meta 分析运行"


def test_ui1a_empty_project_dashboard_has_chinese_warning_state(tmp_path: Path) -> None:
    state = workflow_dashboard_state_from_project(tmp_path / "empty-meta-project")
    step_by_id = {step.step_id: step for step in state.steps}

    assert state.display_title_zh == "Meta 分析流程总控"
    assert state.overall_status_zh == "未开始"
    assert state.manifest_status_zh == "需要复核"
    assert state.empty_state_zh.startswith("选择或创建 Meta 项目")
    assert step_by_id["project_setup"].display_title_zh == "项目设置"
    assert step_by_id["project_setup"].workflow_status_zh == "未开始"
    assert step_by_id["project_setup"].release_status_zh == "内部测试"
    assert step_by_id["project_setup"].warning_summary_zh == USER_MISSING_ARTIFACT_WARNING_ZH
    assert warning_summary_zh(step_by_id["project_setup"].warnings) == USER_MISSING_ARTIFACT_WARNING_ZH


def test_ui1a_meta_workspace_entry_is_chinese_friendly() -> None:
    state = meta_workspace_layout_state()
    labels = [item.label for item in state.navigation_items]

    assert state.title == "Meta 分析模块"
    assert "0.1.0-internal-beta" in state.status_label
    assert "内部测试版 / Developer Preview / testing" in state.status_label
    assert labels[0] == "Meta 项目首页"
    assert "PubMed 检索结果确认 / 文献导入" in labels
    assert "质量评价" in labels
    assert "报告导出" in labels
    assert "不能作为正式临床" in state.testing_notice


def test_ui1a_app_dashboard_keeps_version_and_internal_beta_copy() -> None:
    dashboard = build_dashboard_model()

    assert "0.1.0-internal-beta" in dashboard.product_subtitle
    assert "内部测试版 / Developer Preview / testing" in dashboard.product_subtitle


def test_ui1a_source_smoke_reports_version_git_head_and_app_root() -> None:
    completed = subprocess.run(
        ["python3", "-m", "app.main", "--smoke-test"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "app_version=0.1.0-internal-beta" in completed.stdout
    assert "git_head=" in completed.stdout
    assert f"app_root={REPO_ROOT}" in completed.stdout
