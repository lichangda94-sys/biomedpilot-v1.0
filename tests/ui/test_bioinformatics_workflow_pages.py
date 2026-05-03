from __future__ import annotations

import os
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QFrame, QScrollArea, QTableWidget

    from app.bioinformatics.project_workspace import create_bioinformatics_project
    from app.bioinformatics.results.project_results import write_result_index
    import app.bioinformatics.workflow_pages as workflow_pages
    from app.bioinformatics.workflow_pages import (
        BioinformaticsAcquisitionStatusWidget,
        BioinformaticsAnalysisTaskCenterWidget,
        BioinformaticsDataSourceWidget,
        BioinformaticsRecognitionWidget,
        BioinformaticsReadinessDashboardWidget,
        BioinformaticsReportViewerWidget,
        BioinformaticsResultsBrowserWidget,
        BioinformaticsSettingsAndLocalAIWidget,
        BioinformaticsStandardizedAssetsWidget,
        BioinformaticsWorkflowStatusWidget,
    )
    from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QScrollArea = None  # type: ignore[assignment]
    QFrame = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def project_summary(tmp_path: Path):
    return create_bioinformatics_project("UI Workflow Project", tmp_path)


def test_ui_04_to_ui_13_pages_instantiate_offscreen(qt_app) -> None:
    pages = [
        BioinformaticsDataSourceWidget(),
        BioinformaticsAcquisitionStatusWidget(),
        BioinformaticsRecognitionWidget(),
        BioinformaticsReadinessDashboardWidget(),
        BioinformaticsStandardizedAssetsWidget(),
        BioinformaticsWorkflowStatusWidget(),
        BioinformaticsAnalysisTaskCenterWidget(),
        BioinformaticsResultsBrowserWidget(),
        BioinformaticsReportViewerWidget(),
        BioinformaticsSettingsAndLocalAIWidget(),
    ]

    assert [page.objectName() for page in pages] == [
        "bioinformaticsDataSourcePage",
        "bioinformaticsAcquisitionStatusPage",
        "bioinformaticsRecognitionPage",
        "bioinformaticsReadinessDashboardPage",
        "bioinformaticsStandardizedAssetsPage",
        "bioinformaticsWorkflowStatusPage",
        "bioinformaticsAnalysisTaskCenterPage",
        "bioinformaticsResultsBrowserPage",
        "bioinformaticsReportViewerPage",
        "bioinformaticsSettingsLocalAIPage",
    ]
    assert all(page.findChild(QScrollArea) is not None for page in pages)


def test_data_source_requires_project_and_generates_gse_plan(qt_app, project_summary, monkeypatch) -> None:
    monkeypatch.setattr(workflow_pages, "_fetch_geo_accession_metadata", lambda gse_id: f"当前 GSE 编号：{gse_id}")
    events: list[Path] = []
    widget = BioinformaticsDataSourceWidget(on_continue=events.append)

    assert widget.generate_gse_plan() is None
    assert "请先创建或打开生信分析项目" in widget.status_message()

    widget.refresh_project(project_summary)
    widget.set_gse_input("GSE33630")
    summary = widget.generate_gse_plan()
    widget.continue_to_recognition()

    assert summary is not None
    assert summary.strategy == "plan_only"
    assert events == [project_summary.project_root]
    assert widget.objectName() == "bioinformaticsDataSourcePage"


def test_data_source_page_shows_only_three_primary_modules(qt_app) -> None:
    widget = BioinformaticsDataSourceWidget()
    card_titles = [label.text() for label in widget.findChildren(QLabel, "bioProjectCardTitle")]
    button_texts = [button.text() for button in widget.findChildren(QPushButton)]

    assert "本地数据导入" in card_titles
    assert "GSE 编号检索" in card_titles
    assert "中文研究主题检索" in card_titles
    assert "GEO Series Matrix 文件" not in card_titles
    assert "TCGA 本地数据" not in card_titles
    assert "GTEx 本地数据" not in card_titles
    assert "TCGA + GTEx 联合数据" not in card_titles
    assert "本地 AI 检索助手" not in card_titles
    assert "选择本地数据" in button_texts
    assert "选择文件" not in button_texts
    assert "选择文件夹" not in button_texts


def test_data_source_registers_local_reference_strategy(qt_app, project_summary, tmp_path: Path) -> None:
    source = tmp_path / "sample_metadata.tsv"
    source.write_text("sample\tgroup\ns1\tcase\n", encoding="utf-8")
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    summary = widget.register_local_paths([source], strategy="reference")

    assert summary is not None
    assert summary.strategy == "reference"
    assert str(source.resolve()) in summary.referenced_paths


def test_data_source_shows_local_file_source_summary_and_copy_open(qt_app, project_summary, tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "expression_matrix.csv"
    source.write_text("gene,s1\nTP53,1\n", encoding="utf-8")
    opened: list[str] = []
    monkeypatch.setattr(workflow_pages.QDesktopServices, "openUrl", lambda url: opened.append(url.toLocalFile()) or True)
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    summary = widget.register_local_paths([source], strategy="reference", selected_kind="file", summary_key="local_import")

    text = widget.source_summary_text("local_import")
    assert summary is not None
    assert "expression_matrix.csv" in text
    assert str(source.resolve()) in widget.source_summary_tooltip("local_import")
    assert "引用原始位置" in text
    assert "数据登记记录：已生成" in text
    assert widget.copy_selected_source_path("local_import") is True
    assert QApplication.clipboard().text() == str(source.resolve())
    assert widget.open_selected_source_location("local_import") is True
    assert opened == [str(source.resolve().parent)]


def test_data_source_copy_strategy_displays_chinese_policy(qt_app, project_summary, tmp_path: Path) -> None:
    source = tmp_path / "copy_expression.csv"
    source.write_text("gene,s1\nTP53,1\n", encoding="utf-8")
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    widget.register_local_paths([source], strategy="copy", selected_kind="file", summary_key="local_import")

    assert "已复制到项目文件夹" in widget.source_summary_text("local_import")


def test_data_source_shows_local_folder_source_summary(qt_app, project_summary, tmp_path: Path) -> None:
    folder = tmp_path / "local_matrix_folder"
    folder.mkdir()
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    widget.register_local_paths([folder], strategy="reference", selected_kind="folder", summary_key="local_import")

    text = widget.source_summary_text("local_import")
    assert "已选择文件夹：local_matrix_folder" in text
    assert str(folder.resolve()) in widget.source_summary_tooltip("local_import")


def test_data_source_infers_local_data_types_in_single_import_card(qt_app, project_summary, tmp_path: Path) -> None:
    series = tmp_path / "GSE60024_series_matrix.txt"
    series.write_text("!Series_title = demo\n", encoding="utf-8")
    tcga = tmp_path / "TCGA_GDC_folder"
    gtex = tmp_path / "GTEx_folder"
    expression = tmp_path / "expression_matrix.csv"
    expression.write_text("gene,s1\nTP53,1\n", encoding="utf-8")
    for folder in (tcga, gtex):
        folder.mkdir()
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    widget.register_local_paths([series], strategy="reference", selected_kind="file", summary_key="local_import")
    assert "GEO Series Matrix" in widget.source_summary_text("local_import")
    assert str(series.resolve()) in widget.source_summary_tooltip("local_import")

    widget.register_local_paths([tcga], strategy="reference", selected_kind="folder", summary_key="local_import")
    assert "TCGA 本地数据" in widget.source_summary_text("local_import")
    assert str(tcga.resolve()) in widget.source_summary_tooltip("local_import")

    widget.register_local_paths([gtex], strategy="reference", selected_kind="folder", summary_key="local_import")
    assert "GTEx 本地数据" in widget.source_summary_text("local_import")
    assert str(gtex.resolve()) in widget.source_summary_tooltip("local_import")

    widget.register_local_paths([expression], strategy="reference", selected_kind="file", summary_key="local_import")
    assert "本地表达矩阵" in widget.source_summary_text("local_import")
    assert str(expression.resolve()) in widget.source_summary_tooltip("local_import")


def test_data_source_gse_search_normalizes_accession_and_hides_developer_terms(qt_app, project_summary, monkeypatch) -> None:
    monkeypatch.setattr(workflow_pages, "_fetch_geo_accession_metadata", lambda gse_id: f"当前 GSE 编号：{gse_id}\n处理状态：已登记到项目。")
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)
    widget.set_gse_input("gse60024")

    summary = widget.search_gse_dataset()

    text = widget.source_summary_text("geo_gse")
    assert summary is not None
    assert "GSE60024" in text
    assert "已登记编号，等待数据获取" in text
    assert "数据获取计划：已生成" in text
    assert "数据登记记录：已生成" in text
    assert "下一步交接清单：已生成" in text
    assert str(summary.plan_path) in widget._technical_details.toPlainText()
    assert widget._technical_details.isHidden()
    assert "最近登记的数据来源：GSE 编号检索" in widget.status_message()
    assert "plan_only" not in text
    assert "acquisition" not in text.lower()


def test_data_source_research_topic_uses_rule_fallback_without_ai_card(qt_app, monkeypatch) -> None:
    monkeypatch.setattr(workflow_pages, "_geo_fetcher_class", lambda: None)
    widget = BioinformaticsDataSourceWidget()
    widget._research_goal_input.setText("甲状腺癌淋巴结转移")

    result = widget.search_research_topic()
    card_titles = [label.text() for label in widget.findChildren(QLabel, "bioProjectCardTitle")]

    assert "thyroid cancer" in result
    assert "lymph node metastasis" in result
    assert "当前为检索词生成模式" in result
    assert "不参与统计分析" in result
    assert "本地 AI 检索助手" not in card_titles


def test_data_source_long_path_does_not_break_summary(qt_app, project_summary, tmp_path: Path) -> None:
    nested = tmp_path / ("very_long_folder_name_" * 4) / ("another_long_folder_name_" * 4)
    nested.mkdir(parents=True)
    source = nested / ("expression_" + "x" * 80 + ".csv")
    source.write_text("gene,s1\nTP53,1\n", encoding="utf-8")
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    widget.register_local_paths([source], strategy="reference", selected_kind="file", summary_key="local_import")

    assert "..." in widget.source_summary_text("local_import")
    assert str(source.resolve()) in widget.source_summary_tooltip("local_import")


def test_data_source_technical_details_are_folded_by_default(qt_app) -> None:
    widget = BioinformaticsDataSourceWidget()

    assert widget._technical_details.isHidden()


def test_acquisition_status_empty_and_continue_signal(qt_app, project_summary) -> None:
    events: list[Path] = []
    widget = BioinformaticsAcquisitionStatusWidget(on_continue=events.append)
    widget.refresh_project(project_summary)

    assert "尚未生成数据获取记录" in widget.status_message()
    widget.continue_to_recognition()
    assert events == []
    assert "不能继续" in widget.status_message()


def test_plan_only_acquisition_cannot_continue_to_recognition(qt_app, project_summary, monkeypatch) -> None:
    monkeypatch.setattr(workflow_pages, "_fetch_geo_accession_metadata", lambda gse_id: f"当前 GSE 编号：{gse_id}")
    events: list[Path] = []
    source = BioinformaticsDataSourceWidget()
    source.refresh_project(project_summary)
    source.set_gse_input("GSE33630")
    source.generate_gse_plan()

    widget = BioinformaticsAcquisitionStatusWidget(on_continue=events.append)
    widget.refresh_project(project_summary)
    widget.continue_to_recognition()

    assert events == []
    assert "plan_only" in widget.status_message()


def test_recognition_readiness_standardization_pages(qt_app, project_summary) -> None:
    raw_file = project_summary.project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")

    recognition = BioinformaticsRecognitionWidget()
    recognition.refresh_project(project_summary)
    report = recognition.run_recognition()
    assert report is not None
    assert "已读取识别报告" in recognition.status_message()

    readiness = BioinformaticsReadinessDashboardWidget()
    readiness.refresh_project(project_summary)
    artifacts = readiness.run_readiness_check()
    assert artifacts is not None
    assert "当前 Ready 状态" in readiness.status_message()

    standardization = BioinformaticsStandardizedAssetsWidget()
    standardization.refresh_project(project_summary)
    generated = standardization.generate_assets()
    assert generated is not None
    assert "标准化资产" in standardization.status_message()


def test_readiness_page_uses_compact_status_and_warning_chips(qt_app, project_summary) -> None:
    raw_file = project_summary.project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    BioinformaticsRecognitionWidget().refresh_project(project_summary)
    workflow_pages.run_project_recognition(project_summary.project_root)

    readiness = BioinformaticsReadinessDashboardWidget()
    readiness.refresh_project(project_summary)
    readiness.run_readiness_check()

    assert readiness.findChild(QFrame, "readinessCompactStatusBar") is not None
    chips = readiness.findChild(QLabel, "readinessWarningChips")
    assert chips is not None
    assert "缺少样本信息" in chips.text()
    assert "缺少临床信息" in chips.text()
    assert readiness.findChild(QTableWidget, "readinessCapabilityTable").horizontalHeaderItem(4).text() == "警告"
    assert readiness._details.isHidden()


def test_readiness_missing_info_entry_and_templates(qt_app, project_summary) -> None:
    raw_file = project_summary.project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    workflow_pages.run_project_recognition(project_summary.project_root)

    readiness = BioinformaticsReadinessDashboardWidget()
    readiness.refresh_project(project_summary)
    readiness.run_readiness_check()

    assert "补充缺失信息" in readiness.findChild(QFrame, "readinessSupplementCard").findChild(QLabel).text()
    assert not readiness._sample_file_button.isHidden()
    assert not readiness._sample_manual_button.isHidden()
    assert not readiness._clinical_file_button.isHidden()
    assert not readiness._clinical_manual_button.isHidden()
    assert readiness._expression_file_button.isHidden()

    template = readiness.create_missing_info_template("sample_metadata")
    assert template is not None
    assert template.exists()
    assert "sample_id" in template.read_text(encoding="utf-8")


def test_readiness_supplement_manual_and_file_then_rerun(qt_app, project_summary, tmp_path: Path) -> None:
    expression_file = tmp_path / "expression_matrix.tsv"
    expression_file.write_text("gene\ts1\ts2\nTP53\t1\t2\n", encoding="utf-8")
    clinical_file = tmp_path / "clinical_metadata.tsv"
    clinical_file.write_text("sample_id\tsurvival_time\tsurvival_status\ns1\t10\t1\n", encoding="utf-8")

    readiness = BioinformaticsReadinessDashboardWidget()
    readiness.refresh_project(project_summary)

    assert readiness.supplement_missing_info("expression_matrix", mode="file", path=expression_file) is True
    assert readiness.supplement_missing_info("sample_metadata", mode="manual", manual_text="sample_id\tgroup\ns1\tcase\ns2\tcontrol\n") is True
    assert readiness.supplement_missing_info("clinical_metadata", mode="file", path=clinical_file) is True

    manual_file = project_summary.project_root / "raw_data" / "local_import" / "manual_supplements" / "sample_metadata_manual.tsv"
    assert manual_file.exists()
    artifacts = readiness.save_and_rerun_readiness()
    assert artifacts is not None
    report = artifacts["readiness_report"]
    assert isinstance(report, dict)
    assert report["has_core_input"] is True
    assert "已重新检查" in readiness.status_message()


def _write_mock_recognition_report(project_root: Path, files: list[dict[str, object]]) -> Path:
    path = project_root / "logs" / "recognition" / "recognition_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "biomedpilot.recognition_report.v1",
        "files": files,
        "type_counts": {"expression_matrix": sum(1 for item in files if item.get("recognized_type") == "expression_matrix")},
        "warnings": [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_recognition_table_formats_confidence_size_and_path_tooltip(qt_app, project_summary, tmp_path: Path) -> None:
    long_path = tmp_path / ("long_path_" * 8) / "GSE54350_series_matrix.txt"
    long_path.parent.mkdir(parents=True)
    long_path.write_text("x", encoding="utf-8")
    _write_mock_recognition_report(
        project_summary.project_root,
        [
            {
                "file_name": long_path.name,
                "original_path": str(long_path),
                "recognized_type": "expression_matrix",
                "recognized_type_zh": "表达矩阵",
                "confidence": 0.7,
                "file_size": 5763709,
                "reason": "文件名包含表达矩阵提示。",
                "warning": "",
                "route_path": str(project_summary.project_root / "recognized_data/expression_matrix/GSE54350_series_matrix.txt"),
            }
        ],
    )
    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)
    table = widget.findChild(QTableWidget)

    assert table.horizontalHeaderItem(3).text() == "识别可信度"
    assert "不是数据质量评分" in table.horizontalHeaderItem(3).toolTip()
    assert table.item(0, 3).text() == "70%"
    assert table.item(0, 4).text() == "5.5 MB"
    assert table.item(0, 1).text().startswith("...")
    assert table.item(0, 1).toolTip() == str(long_path)
    assert "原始 bytes：5763709" in table.item(0, 4).toolTip()


def test_recognition_refresh_does_not_call_backend_but_rerun_does(qt_app, project_summary, monkeypatch) -> None:
    _write_mock_recognition_report(project_summary.project_root, [])
    calls: list[str] = []
    monkeypatch.setattr(workflow_pages, "run_project_recognition", lambda root: calls.append(str(root)) or {"files": [], "warnings": [], "type_counts": {}})
    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)

    widget.refresh_report()
    assert calls == []
    assert "不重新扫描文件" in widget.status_message()

    widget.run_recognition()
    assert calls == [str(project_summary.project_root)]
    assert "重新识别已重新扫描" in widget.status_message()


def test_recognition_clean_old_results_keeps_raw_data(qt_app, project_summary) -> None:
    raw_file = project_summary.project_root / "raw_data" / "local_import" / "acq-old" / "expression_matrix.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    report_path = _write_mock_recognition_report(project_summary.project_root, [])
    routed = project_summary.project_root / "recognized_data" / "expression_matrix" / "expression_matrix.tsv"
    routed.parent.mkdir(parents=True, exist_ok=True)
    routed.write_text("copy", encoding="utf-8")
    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)

    assert widget.clean_old_recognition_results(skip_confirmation=True) is True

    assert raw_file.exists()
    assert not report_path.exists()
    assert not routed.exists()
    assert "原始数据文件未删除" in widget.status_message()


def test_recognition_duplicate_filter_marks_and_hides_duplicates(qt_app, project_summary) -> None:
    root = project_summary.project_root
    first = root / "raw_data" / "GSE54350_series_matrix.txt"
    duplicate = root / "raw_data" / "local_import" / "acq-123" / "GSE54350_series_matrix.txt"
    for path in (first, duplicate):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("same", encoding="utf-8")
    files = [
        {
            "file_name": path.name,
            "original_path": str(path),
            "recognized_type": "expression_matrix",
            "recognized_type_zh": "表达矩阵",
            "confidence": 1.0,
            "file_size": path.stat().st_size,
            "reason": "文件名包含表达矩阵提示。",
            "warning": "",
            "route_path": str(root / "recognized_data/expression_matrix" / path.name),
        }
        for path in (first, duplicate)
    ]
    _write_mock_recognition_report(root, files)
    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)
    table = widget.findChild(QTableWidget)

    assert table.rowCount() == 2
    warnings = [table.item(row, 6).text() for row in range(table.rowCount())]
    assert any("检测到可能重复导入的文件" in warning for warning in warnings)
    assert "疑似重复文件：1 个" in widget._counts.toPlainText()

    widget._duplicate_filter.setCurrentText("隐藏疑似重复文件")
    assert table.rowCount() == 1
    assert widget._technical_details.isHidden()


def test_recognition_readiness_and_standardization_continue_gates(qt_app, project_summary) -> None:
    events: list[Path] = []

    recognition = BioinformaticsRecognitionWidget(on_continue=events.append)
    recognition.refresh_project(project_summary)
    recognition.continue_to_readiness()
    assert events == []
    assert "不能继续" in recognition.status_message()

    readiness = BioinformaticsReadinessDashboardWidget(on_continue=events.append)
    readiness.refresh_project(project_summary)
    readiness.run_readiness_check()
    readiness.continue_to_standardization()
    assert events == []
    assert "不能继续" in readiness.status_message()

    standardization = BioinformaticsStandardizedAssetsWidget(on_continue=events.append)
    standardization.refresh_project(project_summary)
    standardization.generate_assets()
    standardization.continue_to_workflow()
    assert events == []
    assert "不能继续" in standardization.status_message()


def test_workflow_task_results_report_and_settings_pages(qt_app, project_summary) -> None:
    workflow = BioinformaticsWorkflowStatusWidget()
    workflow.refresh_project(project_summary)
    assert workflow.run_single_stage("recognition") is not None
    assert "Developer Preview" in workflow.status_message()

    tasks = BioinformaticsAnalysisTaskCenterWidget()
    tasks.refresh_project(project_summary)
    assert tasks.refresh_task_center() is not None
    assert "分析任务中心" in tasks.status_message()

    results = BioinformaticsResultsBrowserWidget()
    results.refresh_project(project_summary)
    assert "暂无结果" in results.status_message()

    report = BioinformaticsReportViewerWidget()
    report.refresh_project(project_summary)
    write_result_index(
        project_summary.project_root,
        [
            {
                "result_name": "Preview result",
                "analysis_type": "preview",
                "file_type": "tsv",
                "path": str(project_summary.project_root / "results" / "tables" / "preview.tsv"),
                "status": "created",
            }
        ],
    )
    generated = report.generate_report()
    assert generated is not None
    assert "PDF 当前" in report.status_message()

    settings = BioinformaticsSettingsAndLocalAIWidget()
    settings._question_input.setText("甲状腺癌淋巴结转移")
    terms = settings.generate_placeholder_terms()
    assert "placeholder" in terms
    assert "本地 AI" in settings.status_message()


def test_settings_page_runs_geo_legacy_environment_check(qt_app, monkeypatch) -> None:
    monkeypatch.setattr(workflow_pages, "geo_check_command", lambda: ["python", "run_geo_tool.py", "--check"])
    monkeypatch.setattr(
        workflow_pages,
        "run_geo_environment_check",
        lambda: SimpleNamespace(returncode=0, stdout="legacy check ok", stderr=""),
    )
    settings = BioinformaticsSettingsAndLocalAIWidget()

    result = settings.run_geo_legacy_environment_check()

    assert "GEO legacy 环境检查" in result
    assert "legacy check ok" in result
    assert "不下载数据" in result
    assert "已完成" in settings._geo_check_status.text()


def test_workspace_navigation_reaches_full_stack(qt_app, project_summary) -> None:
    widget = BioinformaticsWorkspaceWidget()

    widget.show_data_source(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsDataSourcePage"
    source = project_summary.project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    widget._data_source_page.register_local_paths([source], strategy="reference", selected_kind="file", summary_key="local_import")
    widget._data_source_page.continue_to_recognition()
    assert widget.current_page_object_name() == "bioinformaticsRecognitionPage"
    widget.show_readiness(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsReadinessDashboardPage"
    widget.show_standardization(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsStandardizedAssetsPage"
    widget.show_workflow_status(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsWorkflowStatusPage"
    widget.show_analysis_tasks(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsAnalysisTaskCenterPage"
    widget.show_results_browser(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsResultsBrowserPage"
    widget.show_report_viewer(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsReportViewerPage"
