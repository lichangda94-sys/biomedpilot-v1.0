from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.meta_analysis.pages.workflow_integration_page import meta_workflow_integration_state_from_project
from app.meta_analysis.project_workspace import META_PROJECT_DIRECTORIES, create_meta_analysis_project
from app.meta_analysis.workspace import meta_workspace_layout_state

try:
    from PySide6.QtWidgets import QApplication, QComboBox, QFrame, QLabel, QLineEdit, QListWidget, QPlainTextEdit, QPushButton
except Exception as exc:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def _visible_text(widget) -> str:
    texts: list[str] = []
    for child in [*widget.findChildren(QLabel), *widget.findChildren(QPushButton)]:
        if child.isVisibleTo(widget):
            value = child.text()
            if value:
                texts.append(value)
    for child in widget.findChildren(QListWidget):
        if child.isVisibleTo(widget):
            for index in range(child.count()):
                texts.append(child.item(index).text())
    return "\n".join(texts)


def _current_step_widget(widget):
    scroll = widget._page_stack.currentWidget()
    return scroll.widget()


def test_meta_workspace_layout_state_uses_eight_user_facing_stages() -> None:
    state = meta_workspace_layout_state()

    assert "0.1.0-internal-beta" in state.status_label
    assert state.title == "Meta 分析模块"
    assert state.default_page_key == "workflow_home"
    assert [item.page_key for item in state.navigation_items] == [
        "workflow_home",
        "pico_workspace",
        "search_strategy",
        "literature_import",
        "screening_review",
        "manual_extraction",
        "statistics_analysis",
        "report_export",
    ]
    assert [item.label for item in state.navigation_items] == [
        "项目首页",
        "研究问题与 PICO",
        "检索策略",
        "文献库与导入",
        "去重与筛选",
        "数据提取与质量评价",
        "统计分析",
        "报告导出",
    ]
    assert "不能作为正式临床" in state.testing_notice


def test_meta_workspace_widget_mounts_project_sidebar_and_home(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("Mounted Pages", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)

    assert widget.meta_workspace_layout_state()["workflow_nav"] == "metaWorkflowNav"
    assert widget.meta_workspace_layout_state()["current_step_workspace"] == "metaCurrentStepWorkspace"
    assert widget.page_keys() == (
        "workflow_home",
        "pico_workspace",
        "search_strategy",
        "literature_import",
        "screening_review",
        "manual_extraction",
        "statistics_analysis",
        "report_export",
    )
    mounted_pages = {frame.objectName() for frame in widget.findChildren(QFrame)}
    assert {
        "metaProjectHomePage",
        "metaPicoPage",
        "metaSearchStrategyPage",
        "metaLiteratureAcquisitionPage",
        "metaTitleAbstractScreeningPage",
        "metaManualExtractionPage",
        "metaStatisticsAnalysisPage",
        "metaReportExportPage",
    } <= mounted_pages


def test_meta_screening_workspace_renders_chinese_user_controls_without_raw_paths(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
    from app.meta_analysis.services.title_abstract_screening_v2_service import TitleAbstractScreeningV2Service
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("Screening Workspace", tmp_path)
    LiteratureLibraryService().import_records(
        summary.project_root,
        project_id="screening-workspace",
        source_type="nbib",
        source_name="PubMed",
        raw_records=[
            {
                "record_id": "lit-screen-1",
                "title": "Trial of treatment for hypertension",
                "abstract": "Adults with hypertension were randomized to treatment or usual care.",
                "authors": ["Zhang Wei", "Li Ming"],
                "journal": "Journal A",
                "year": "2024",
                "database_source": "PubMed",
            }
        ],
    )
    TitleAbstractScreeningV2Service().build_queue(summary.project_root, project_id="screening-workspace")

    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)
    widget.show_step("screening_review")
    widget.show()
    qt_app.processEvents()
    current = _current_step_widget(widget)
    visible = _visible_text(current)
    combos = {
        child.objectName(): [child.itemText(index) for index in range(child.count())]
        for child in current.findChildren(QComboBox)
    }

    assert "文献筛选" in visible
    assert "标题摘要筛选" in visible
    assert "当前文献库" in visible
    assert "当前 PRISMA 计数" in visible
    assert "排除原因" in visible
    assert "下一步：全文管理" in visible
    assert {"未筛选", "纳入", "排除", "不确定", "需要全文", "重置为未筛选"} <= set(combos["metaScreeningWorkspaceDecisionSelector"])
    assert {"研究对象不符合", "干预/暴露不符合", "对照不符合", "结局不符合", "研究类型不符合", "重复文献", "非原始研究", "全文不可获取", "语言或获取限制", "其他"} <= set(combos["metaScreeningWorkspaceReasonSelector"])
    assert str(summary.project_root) not in visible
    assert "title_abstract_queue_v2.json" not in visible
    assert "manifest" not in visible
    assert "raw JSON" not in visible


def test_meta_fulltext_management_workspace_renders_chinese_user_controls_without_raw_paths(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.services.fulltext_management_service import FullTextManagementService
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("全文管理 Meta", tmp_path, research_topic="降压治疗")
    screening_path = summary.project_root / "screening" / "screening_decisions.json"
    screening_path.parent.mkdir(parents=True, exist_ok=True)
    screening_path.write_text(
        json.dumps(
            {
                "screening_records": [
                    {
                        "record_id": "ft-rec-1",
                        "decision": "need_full_text",
                        "title": "Full text needed trial",
                        "authors": ["Zhang Wei"],
                        "journal": "Journal A",
                        "year": "2025",
                        "database_source": "PubMed",
                    },
                    {
                        "record_id": "ft-rec-2",
                        "decision": "include",
                        "title": "Included trial",
                        "authors": ["Li Ming"],
                        "journal": "Journal B",
                        "year": "2024",
                        "database_source": "Embase",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    pdf = summary.project_root / "uploaded.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%test\n")
    service = FullTextManagementService()
    service.build_registry_from_screening(summary.project_root, project_id="fulltext-workspace")
    service.attach_pdf(summary.project_root, record_id="ft-rec-1", source_file_path=str(pdf), actor="reviewer")

    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)
    widget.show_step("screening_review")
    widget.show()
    qt_app.processEvents()
    current = _current_step_widget(widget)
    visible = _visible_text(current)
    combos = {
        child.objectName(): [child.itemText(index) for index in range(child.count())]
        for child in current.findChildren(QComboBox)
    }

    assert "全文管理" in visible
    assert "全文筛选" in visible
    assert "全文状态" in visible
    assert "上传全文" in visible
    assert "标记无法获取" in visible
    assert "全文确认" in visible
    assert "下一步：数据提取" in visible
    assert "已登记全文文件" in visible
    assert {"暂不需要全文", "需要全文", "已上传全文", "全文待检查", "全文已确认", "全文不可获取", "全文已排除"} <= set(combos["metaFulltextStatusSelector"])
    assert {"全文不可获取", "研究对象不符合", "干预/暴露不符合", "对照不符合", "结局不符合", "研究类型不符合", "全文阶段发现重复", "数据不足", "其他"} <= set(combos["metaFulltextReasonSelector"])
    assert str(summary.project_root) not in visible
    assert "fulltext_management_registry_v1.json" not in visible
    assert "manifest" not in visible
    assert "raw JSON" not in visible
    assert "ft-rec-1" not in visible


def test_meta_extraction_workspace_renders_structured_table_without_raw_internals(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("数据提取 Meta", tmp_path, research_topic="降压治疗")
    registry_path = summary.project_root / "fulltext" / "fulltext_management_registry_v1.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": "meta_fulltext_management_registry.v1",
                "records": [
                    {
                        "record_id": "extract-rec-1",
                        "title": "Confirmed extraction trial",
                        "authors": "Zhang Wei",
                        "year": "2025",
                        "journal": "Journal A",
                        "fulltext_status": "full_text_confirmed",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)
    widget.show_step("manual_extraction")
    widget.show()
    qt_app.processEvents()
    current = _current_step_widget(widget)
    visible = _visible_text(current)
    combos = {
        child.objectName(): [child.itemText(index) for index in range(child.count())]
        for child in current.findChildren(QComboBox)
    }

    assert "数据提取" in visible
    assert "研究基本信息" in visible
    assert "PICO/PECO" in visible
    assert "效应量数据" in visible
    assert "统计字段" in visible
    assert "提取状态" in visible
    assert "用户确认" in visible
    assert "下一步：质量评价" in visible
    assert "Confirmed extraction trial" in visible
    assert {"OR", "RR", "HR", "MD", "SMD", "proportion", "correlation", "diagnostic_accuracy", "other"} <= set(combos["metaExtractionEffectMeasureSelector"])
    assert {"空", "草稿", "建议", "用户接受", "用户编辑", "已确认", "已拒绝"} <= set(combos["metaExtractionEvidenceStateSelector"])
    assert str(summary.project_root) not in visible
    assert "extraction_manifest.json" not in visible
    assert "raw JSON" not in visible
    assert "extract-rec-1" not in visible


def test_meta_quality_workspace_renders_chinese_nos_controls_without_raw_internals(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("质量评价 Meta", tmp_path, research_topic="队列研究")
    extraction_path = summary.project_root / "extraction" / "extraction_effect_rows.json"
    extraction_path.parent.mkdir(parents=True, exist_ok=True)
    extraction_path.write_text(
        json.dumps(
            {
                "effect_rows": [
                    {
                        "effect_row_id": "effect-internal-1",
                        "record_id": "quality-rec-1",
                        "study_unit_id": "unit-internal-1",
                        "study_unit_label": "Study One",
                        "extraction_status": "completed_by_user",
                        "evidence_state": "confirmed",
                        "m5_structured_fields": {
                            "study_id": "study-quality-1",
                            "title": "Quality cohort study",
                            "first_author": "Zhang",
                            "year": "2025",
                            "study_design": "observational cohort",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)
    widget.show_step("manual_extraction")
    widget.show()
    qt_app.processEvents()
    current = _current_step_widget(widget)
    visible = _visible_text(current)
    combos = {
        child.objectName(): [child.itemText(index) for index in range(child.count())]
        for child in current.findChildren(QComboBox)
    }

    assert "质量评价" in visible
    assert "偏倚风险" in visible
    assert "评价工具" in visible
    assert "评价维度" in visible
    assert "评价理由" in visible
    assert "总体判断" in visible
    assert "已确认" in visible
    assert "下一步：分析计划" in visible
    assert "Quality cohort study" in visible
    assert any(item.startswith("NOS") for item in combos["metaQualityToolSelector"])
    assert {"未评价", "低风险/较好", "不明确", "高风险/较差"} <= set(combos["metaQualityOverallSelector"])
    assert {"草稿", "建议", "用户接受", "用户编辑", "已确认", "已拒绝"} <= set(combos["metaQualityStateSelector"])
    assert str(summary.project_root) not in visible
    assert "quality_assessment_records_v1.json" not in visible
    assert "raw JSON" not in visible
    assert "quality-rec-1" not in visible
    assert "effect-internal-1" not in visible


def test_meta_workspace_blocks_pico_entry_until_project_exists(qt_app) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    widget = MetaAnalysisWorkspaceWidget()
    widget.show()
    qt_app.processEvents()

    buttons = [button for button in widget.findChildren(QPushButton) if button.text() == "继续：研究问题 / PICO"]
    assert buttons
    assert all(not button.isEnabled() for button in buttons)
    assert "请先新建或打开 Meta 项目" in _visible_text(widget)


def test_meta_workspace_creates_meta_project_from_home_form(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    widget = MetaAnalysisWorkspaceWidget()
    widget.set_new_project_form(project_name="高血压 Meta", research_topic="降压治疗", save_location=tmp_path)

    summary = widget.create_meta_project_from_form()

    assert summary is not None
    assert widget.current_project_dir() == summary.project_root
    for directory in META_PROJECT_DIRECTORIES:
        assert (summary.project_root / directory).is_dir()
    manifest = json.loads((summary.project_root / "meta_project_manifest.json").read_text(encoding="utf-8"))
    config = json.loads((summary.project_root / "meta_project_config.json").read_text(encoding="utf-8"))
    assert manifest["project_type"] == "meta_analysis"
    assert manifest["project_name"] == "高血压 Meta"
    assert manifest["workflow_stage"] == "project_home"
    assert config["ui"]["current_page"] == "workflow_home"


def test_meta_workspace_opens_existing_project_and_rejects_invalid_folder(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("Existing Meta", tmp_path)
    invalid = tmp_path / "plain-folder"
    invalid.mkdir()
    widget = MetaAnalysisWorkspaceWidget()

    assert widget.open_meta_project_folder(summary.project_root) is True
    assert widget.current_project_dir() == summary.project_root
    assert widget.open_meta_project_folder(invalid) is False
    assert widget.current_project_dir() == summary.project_root


def test_meta_home_collapses_repeated_status_and_developer_terms(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("Clean Home", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)
    widget.show()
    qt_app.processEvents()

    visible = _visible_text(widget)
    assert "当前项目状态" not in visible
    assert "项目概览" not in visible
    assert "最近 warnings" not in visible
    assert "project_home" not in visible
    assert "manifest" not in visible
    assert "config" not in visible
    assert "workflow_state" not in visible
    assert visible.count("Developer Preview / 本地测试版") == 1
    assert "下一步：填写研究问题 / PICO" in visible
    assert "继续：研究问题 / PICO" in visible


def test_meta_workspace_pico_protocol_round_trip_updates_status(qt_app, tmp_path: Path) -> None:
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

    summary = create_meta_analysis_project("PICO Round Trip", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)
    widget.show_step("pico_workspace")

    before = {step.step_id: step.status for step in meta_workflow_integration_state_from_project(summary.project_root).steps}
    assert before["pico_workspace"] == "未开始"

    question = widget.findChild(QPlainTextEdit, "metaPicoQuestionInput")
    assert question is not None
    question.setPlainText("高血压患者降压药与常规治疗相比对卒中风险的影响")
    mode = widget.findChild(QComboBox, "metaPicoModeSelector")
    assert mode is not None
    mode.setCurrentIndex(mode.findData("pico"))
    current = _current_step_widget(widget)
    generate = next(button for button in current.findChildren(QPushButton) if button.text() == "生成 PICO 草稿")
    generate.click()
    qt_app.processEvents()

    draft_state = {step.step_id: step.status for step in meta_workflow_integration_state_from_project(summary.project_root).steps}
    assert draft_state["pico_workspace"] == "草稿"
    assert (summary.project_root / "protocol" / "pico_workspace_draft.json").exists()

    widget.show_step("pico_workspace")
    current = _current_step_widget(widget)
    primary = current.findChild(QLineEdit, "metaPicoPrimaryOutcomesInput")
    effect = current.findChild(QLineEdit, "metaPicoEffectMeasureInput")
    assert primary is not None
    assert effect is not None
    primary.setText("卒中发生率")
    effect.setText("RR")
    save = next(button for button in current.findChildren(QPushButton) if button.text() == "保存草稿编辑")
    save.click()
    qt_app.processEvents()

    widget.show_step("pico_workspace")
    current = _current_step_widget(widget)
    confirm = next(button for button in current.findChildren(QPushButton) if button.text() == "确认研究问题")
    confirm.click()
    qt_app.processEvents()

    confirmed_path = summary.project_root / "protocol" / "pico_workspace_confirmed.json"
    protocol_manifest = summary.project_root / "protocol" / "pico_workspace_manifest.json"
    assert confirmed_path.exists()
    assert protocol_manifest.exists()
    confirmed = json.loads(confirmed_path.read_text(encoding="utf-8"))
    manifest = json.loads(protocol_manifest.read_text(encoding="utf-8"))
    assert confirmed["confirmed_pico_mode"] == "pico"
    assert "卒中发生率" in confirmed["confirmed_outcomes"]
    assert "推荐效应量类型：RR" in confirmed["user_notes"]
    assert manifest["confirmed_status"] == "confirmed"

    complete_state = {step.step_id: step.status for step in meta_workflow_integration_state_from_project(summary.project_root).steps}
    assert complete_state["pico_workspace"] == "已完成"

    widget.show_step("search_strategy")
    visible = _visible_text(widget)
    assert "下一阶段将基于该方案生成检索策略" in visible
