from __future__ import annotations

import os
import json
import gzip
import zipfile
from pathlib import Path
from types import SimpleNamespace
from xml.sax.saxutils import escape

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QCheckBox, QHeaderView, QLabel, QPushButton, QFrame, QScrollArea, QTableWidget, QTextEdit

    from app.bioinformatics.project_workspace import create_bioinformatics_project
    from app.bioinformatics.results.project_results import write_result_index
    import app.bioinformatics.workflow_pages as workflow_pages
    from app.bioinformatics.workflow_pages import (
        BioinformaticsAcquisitionStatusWidget,
        BioinformaticsAnalysisTaskCenterWidget,
        BioinformaticsChineseDatasetSearchWidget,
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


def _write_xlsx_count_matrix(path: Path) -> Path:
    rows = [
        ["gene_id", "A1_count", "A2_count", "B1_count"],
        ["ENSMUSG00000026193", 195458, 215969, 197661],
        ["ENSMUSG00000064351", 160365, 142505, 129666],
    ]
    sheet_rows: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells: list[str] = []
        for column_index, value in enumerate(row):
            reference = f"{chr(ord('A') + column_index)}{row_index}"
            if isinstance(value, (int, float)):
                cells.append(f'<c r="{reference}"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{reference}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    worksheet_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        "</worksheet>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", worksheet_xml)
    return path


def _geo_candidate(*, query_used: str = '("glioma" OR "glioblastoma") AND "RNA-seq" AND GSE[ETYP]') -> workflow_pages.UnifiedDatasetCandidate:
    return workflow_pages.UnifiedDatasetCandidate(
        source="geo",
        accession_or_project="GSE33630",
        display_title="Glioma RNA-seq expression profile",
        organism="Homo sapiens",
        disease="glioma",
        tissue="brain",
        data_modality="RNA-seq",
        sample_count=45,
        has_expression_matrix=True,
        has_sample_metadata=True,
        has_clinical_metadata=False,
        has_platform_annotation=True,
        recommended_analyses=("data_recognition",),
        download_plan_available=True,
        score=80,
        warnings=(),
        source_specific_metadata={
            "match_reason": "title contains glioma",
            "title_en": "Glioma RNA-seq expression profile",
            "summary_en": "Expression profiling of glioma tumor and normal brain control samples.",
            "overall_design_en": "Tumor versus normal control samples were analyzed.",
            "platform_accessions": ["GPL11154"],
            "geo_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE33630",
            "query_used": query_used,
            "search_time": "2026-05-04T00:00:00+00:00",
        },
    )


def _source_card_text(widget: BioinformaticsChineseDatasetSearchWidget, source: str) -> str:
    container = widget._source_recommendation_widgets[source]
    texts = [label.text() for label in container.findChildren(QLabel)]
    texts.extend(button.text() for button in container.findChildren(QPushButton))
    return " ".join(texts)


class _FakeGeoDownloader:
    def download(self, accession: str, target_dir: Path) -> dict[str, object]:
        path = target_dir / f"{accession}_family.soft"
        path.write_text(
            "\n".join(
                [
                    "^DATABASE = Gene Expression Omnibus",
                    f"^SERIES = {accession}",
                    "!Series_sample_id = GSM1",
                    "^SAMPLE = GSM1",
                    "!Sample_title = tumor sample",
                    "!Sample_characteristics_ch1 = tissue: tumor",
                    "#ID_REF = ID_REF",
                    "#VALUE = RMA expression estimate",
                    "!sample_table_begin",
                    "ID_REF\tVALUE",
                    "1007_s_at\t1.0",
                    "!sample_table_end",
                    "^PLATFORM = GPL570",
                    "!platform_table_begin",
                    "ID\tGene Symbol",
                    "1007_s_at\tDDR1",
                    "!platform_table_end",
                ]
            ),
            encoding="utf-8",
        )
        return {"status": "success", "accession": accession, "family_soft_path": str(path)}


class _FakeGeoAssetDiscoverer:
    def discover(self, accession: str, target_dir: Path, download_result: dict[str, object]) -> dict[str, object]:
        family_path = Path(str(download_result["family_soft_path"]))
        return {
            "schema_version": "biomedpilot.geo_asset_manifest.v1",
            "accession": accession,
            "assets": [
                {
                    "asset_type": "family_soft",
                    "role": "metadata_container",
                    "file_name": family_path.name,
                    "status": "downloaded",
                    "local_path": str(family_path),
                    "remote_url": f"https://example.org/{family_path.name}",
                    "input_eligible": True,
                    "needs_download": False,
                },
                {
                    "asset_type": "series_matrix",
                    "role": "expression_matrix_candidate",
                    "file_name": f"{accession}-GPL570_series_matrix.txt.gz",
                    "status": "remote_discovered",
                    "local_path": "",
                    "remote_url": f"https://example.org/{accession}-GPL570_series_matrix.txt.gz",
                    "input_eligible": False,
                    "needs_download": True,
                },
                {
                    "asset_type": "supplementary_file",
                    "role": "supplementary_expression_candidate",
                    "file_name": f"{accession}_counts.tsv.gz",
                    "status": "remote_discovered",
                    "local_path": "",
                    "remote_url": f"https://example.org/{accession}_counts.tsv.gz",
                    "input_eligible": False,
                    "needs_download": True,
                },
            ],
            "summary": {
                "metadata_downloaded": True,
                "series_matrix_discovered": True,
                "supplementary_files_discovered": True,
                "expression_matrix_status": "remote_discovered",
                "recognition_ready": True,
            },
            "ui_status_parts": ["元数据已下载", "表达矩阵待下载", "已发现补充文件", "可进入识别"],
            "warnings": [],
        }


class _FakeGeoRemoteAssetDownloader:
    def download_asset(self, asset: dict[str, object], target_dir: Path) -> dict[str, object]:
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / Path(str(asset["file_name"])).name
        if str(asset.get("asset_type")) == "series_matrix":
            content = "\n".join(
                [
                    "!Series_title = demo",
                    "!Series_geo_accession = GSE33630",
                    "!Series_platform_id = GPL570",
                    "!Sample_title = tumor",
                    "!Sample_geo_accession = GSM1",
                    "!Sample_characteristics_ch1 = tissue: tumor",
                    "!series_matrix_table_begin",
                    "ID_REF\tGSM1\tGSM2",
                    "1007_s_at\t1.0\t2.0",
                    "!series_matrix_table_end",
                ]
            )
            if path.name.endswith(".gz"):
                with gzip.open(path, "wt", encoding="utf-8") as handle:
                    handle.write(content)
            else:
                path.write_text(content, encoding="utf-8")
        else:
            content = "gene\tGSM1\tGSM2\nTP53\t1\t2\nEGFR\t3\t4\n"
            if path.name.endswith(".gz"):
                with gzip.open(path, "wt", encoding="utf-8") as handle:
                    handle.write(content)
            else:
                path.write_text(content, encoding="utf-8")
        return {"status": "success", "local_path": str(path), "bytes_downloaded": path.stat().st_size}


def test_ui_04_to_ui_13_pages_instantiate_offscreen(qt_app) -> None:
    pages = [
        BioinformaticsDataSourceWidget(),
        BioinformaticsChineseDatasetSearchWidget(),
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
        "bioinformaticsChineseDatasetSearchPage",
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
    assert events == []
    assert "实际数据文件" in widget.status_message()
    assert widget.objectName() == "bioinformaticsDataSourcePage"


def test_gse_preview_preserves_geo_organism_for_detail_profile(qt_app) -> None:
    metadata_text = "\n".join(
        [
            "当前 GSE 编号：GSE5078",
            "数据集标题：Hippocampal transcript profile in young and middle-aged mice",
            "样本数：23",
            "平台信息：GPL1261",
            "物种：Mus musculus",
        ]
    )

    preview = workflow_pages._gse_preview_from_metadata("GSE5078", metadata_text)
    candidate = workflow_pages._geo_candidate_from_gse_preview(preview)
    rows = workflow_pages._geo_detail_basic_rows(candidate)
    profile = workflow_pages._build_geo_detail_profile(None, candidate)
    row_map = {str(row[0]): str(row[1]) for row in rows}

    assert preview.organism == "Mus musculus"
    assert candidate.organism == "Mus musculus"
    assert row_map["物种"] == "Mus musculus"
    assert profile.organism == "Mus musculus"
    assert profile.species_group == "mouse"
    assert "人类或疑似人类" not in profile.analysis_potential_reason


def test_data_source_page_shows_only_three_primary_modules(qt_app) -> None:
    widget = BioinformaticsDataSourceWidget()
    card_titles = [
        label.text()
        for label in widget.findChildren(QLabel, "bioProjectCardTitle")
        if label.text() not in {"GEO 数据集详情", "待处理数据集", "历史缓存数据", "数据详情"}
    ]
    button_texts = [button.text() for button in widget.findChildren(QPushButton)]
    inputs = widget.findChildren(workflow_pages.QLineEdit)

    assert "本地数据导入" in card_titles
    assert "GSE 编号检索" in card_titles
    assert "中文研究问题检索" in card_titles
    assert "GEO Series Matrix 文件" not in card_titles
    assert "TCGA 本地数据" not in card_titles
    assert "GTEx 本地数据" not in card_titles
    assert "TCGA + GTEx 联合数据" not in card_titles
    assert "本地 AI 检索助手" not in card_titles
    assert card_titles[:3] == ["本地数据导入", "GSE 编号检索", "中文研究问题检索"]
    assert "选择本地数据" in button_texts
    assert "选择本地文件夹" in button_texts
    assert "进入检索界面" in button_texts
    assert any(input_box.placeholderText() == "请输入研究方向，例如：甲状腺癌与肥胖相关基因表达数据" for input_box in inputs)
    assert "选择文件" not in button_texts
    assert "选择文件夹" not in button_texts
    assert "登记为数据源" not in button_texts


def test_local_import_strategy_copy_uses_user_friendly_copy(qt_app) -> None:
    widget = BioinformaticsDataSourceWidget()
    combo = widget._local_strategy_combo
    hint = widget.findChild(QLabel, "localImportStrategyHint")

    assert combo.currentText() == "复制到项目文件夹（推荐）"
    assert combo.itemText(0) == "复制到项目文件夹（推荐）"
    assert combo.itemText(1) == "使用原文件位置"
    assert hint is not None
    assert hint.text() == "把数据文件复制到当前项目，便于后续复用、迁移和归档。"
    all_text = "\n".join(
        [hint.text(), combo.itemText(0), combo.itemText(1), *[label.text() for label in widget.findChildren(QLabel)]]
    )
    assert "仅记录路径" not in all_text


def test_local_import_strategy_reference_updates_hint(qt_app) -> None:
    widget = BioinformaticsDataSourceWidget()
    combo = widget._local_strategy_combo
    hint = widget.findChild(QLabel, "localImportStrategyHint")

    combo.setCurrentText("使用原文件位置")

    assert hint is not None
    assert "不复制文件" in hint.text()
    assert "后续分析将从原位置读取" in hint.text()
    assert "请勿移动或删除" in hint.text()
    assert "项目可能无法继续读取该数据" in hint.text()


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
    progress_messages: list[str] = []
    real_register_acquisition = workflow_pages.register_acquisition

    def capture_progress(*args, **kwargs):
        progress_messages.append(widget.source_summary_text("local_import"))
        return real_register_acquisition(*args, **kwargs)

    monkeypatch.setattr(workflow_pages.QDesktopServices, "openUrl", lambda url: opened.append(url.toLocalFile()) or True)
    monkeypatch.setattr(workflow_pages, "register_acquisition", capture_progress)
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    summary = widget.register_local_paths([source], strategy="reference", selected_kind="file", summary_key="local_import")

    text = widget.source_summary_text("local_import")
    assert summary is not None
    assert progress_messages == ["正在添加本地数据，请稍候。"]
    assert text == "已选择本地数据：expression_matrix.csv"
    assert str(source.resolve()) not in text
    assert "数据获取计划" not in text
    assert "数据记录" not in text
    detail = widget.source_summary_tooltip("local_import")
    assert str(source.resolve()) in detail
    assert "引用原始位置" in detail
    assert "数据记录：已生成" in detail
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

    assert widget.source_summary_text("local_import") == "已选择本地数据：copy_expression.csv"
    assert "已复制到项目文件夹" in widget.source_summary_tooltip("local_import")


def test_data_source_shows_local_folder_source_summary(qt_app, project_summary, tmp_path: Path) -> None:
    folder = tmp_path / "local_matrix_folder"
    folder.mkdir()
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    widget.register_local_paths([folder], strategy="reference", selected_kind="folder", summary_key="local_import")

    text = widget.source_summary_text("local_import")
    assert text == "已选择本地数据：local_matrix_folder"
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
    assert widget.source_summary_text("local_import") == "已选择本地数据：GSE60024_series_matrix.txt"
    assert "GEO Series Matrix" in widget.source_summary_tooltip("local_import")
    assert str(series.resolve()) in widget.source_summary_tooltip("local_import")

    widget.register_local_paths([tcga], strategy="reference", selected_kind="folder", summary_key="local_import")
    assert widget.source_summary_text("local_import") == "已选择本地数据：TCGA_GDC_folder"
    assert "TCGA 本地数据" in widget.source_summary_tooltip("local_import")
    assert str(tcga.resolve()) in widget.source_summary_tooltip("local_import")

    widget.register_local_paths([gtex], strategy="reference", selected_kind="folder", summary_key="local_import")
    assert widget.source_summary_text("local_import") == "已选择本地数据：GTEx_folder"
    assert "GTEx 本地数据" in widget.source_summary_tooltip("local_import")
    assert str(gtex.resolve()) in widget.source_summary_tooltip("local_import")

    widget.register_local_paths([expression], strategy="reference", selected_kind="file", summary_key="local_import")
    assert widget.source_summary_text("local_import") == "已选择本地数据：expression_matrix.csv"
    assert "本地表达矩阵" in widget.source_summary_tooltip("local_import")
    assert str(expression.resolve()) in widget.source_summary_tooltip("local_import")

    workbook = _write_xlsx_count_matrix(tmp_path / "GSE236866_Processed_data_tau_with_inhibitors.xlsx")
    widget.register_local_paths([workbook], strategy="reference", selected_kind="file", summary_key="local_import")
    assert widget.source_summary_text("local_import") == "已选择本地数据：GSE236866_Processed_data_tau_with_inhibitors.xlsx"
    assert "原始计数矩阵" in widget.source_summary_tooltip("local_import")


def test_data_source_gse_search_normalizes_accession_and_hides_developer_terms(qt_app, project_summary, monkeypatch) -> None:
    monkeypatch.setattr(workflow_pages, "_fetch_geo_accession_metadata", lambda gse_id: f"当前 GSE 编号：{gse_id}\n处理状态：已添加到项目。")
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)
    widget.set_gse_input("gse60024")

    preview = widget.search_gse_dataset()
    assert preview is not None
    assert not widget._register_gse_button.isHidden()
    assert isinstance(widget._gse_geo_detail_panel, workflow_pages.GeoDatasetDetailPanel)
    assert not widget._gse_geo_detail_panel.isHidden()
    assert "GSE60024" in widget._gse_geo_detail_panel._title.text()
    assert widget._gse_geo_detail_panel._save_button.text() == "添加到项目"
    summary = widget.register_gse_dataset()

    text = widget.source_summary_text("geo_gse")
    assert summary is not None
    assert text == "已添加 GSE 数据集：GSE60024"
    assert widget._dataset_list_panel._table.rowCount() == 1
    assert widget._dataset_list_panel._table.item(0, 2).text() == "GSE60024"
    assert widget._dataset_list_panel._table.item(0, 3).text() == "未下载"
    assert widget.register_gse_dataset() is None
    assert widget._dataset_list_panel._table.rowCount() == 1
    assert "数据获取计划" not in text
    assert "数据记录" not in text
    assert widget._gse_status_label.text() == "已添加 GSE 数据集：GSE60024"
    assert "已添加编号，等待数据获取" in widget.source_summary_tooltip("geo_gse")
    assert "数据获取计划：已生成" in widget.source_summary_tooltip("geo_gse")
    assert "数据记录：已生成" in widget.source_summary_tooltip("geo_gse")
    assert "下一步交接清单：已生成" in widget.source_summary_tooltip("geo_gse")
    assert str(summary.plan_path) in widget._technical_details.toPlainText()
    assert widget._technical_details.isHidden()
    assert widget.status_message() == "先添加数据，下一步进入数据识别。"
    assert "plan_only" not in text
    assert "acquisition" not in text.lower()
    assert not widget._next_button.isEnabled()


def test_data_source_geo_detail_generates_summary_inside_detail(qt_app, project_summary, monkeypatch) -> None:
    monkeypatch.setattr(workflow_pages, "_fetch_geo_accession_metadata", lambda gse_id: f"当前 GSE 编号：{gse_id}\n数据集标题：Glioma expression profile\n样本数：12\n平台信息：GPL570")
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)
    widget.set_gse_input("GSE33630")
    widget.search_gse_dataset()

    class _FakeSummaryService:
        def summarize(self, text):
            return SimpleNamespace(
                status="completed",
                to_dict=lambda: {
                    "status": "completed",
                    "title_zh": "胶质瘤表达谱",
                    "summary_zh": "胶质瘤样本摘要。",
                    "overall_design_zh": "肿瘤和对照。",
                    "brief_zh": "该数据集比较胶质瘤和对照样本。",
                    "error_message": "",
                },
            )

    widget._text_summary_service = _FakeSummaryService()
    candidate = widget._gse_geo_detail_panel.current_candidate()
    assert candidate is not None
    assert "分析潜力" in widget._gse_geo_detail_panel._profile_text.toPlainText()
    payload = widget._generate_gse_geo_summary(candidate)

    assert payload is not None
    text = widget._gse_geo_detail_panel._translation_text.toPlainText()
    assert "该数据集比较胶质瘤和对照样本。" in text
    assert "AI 草稿：中文翻译与提炼，需人工确认。" in text
    assert "与检索主题匹配：" not in text
    assert "推荐等级：" not in text
    assert "医学实体一致性状态" not in text


def test_data_source_chinese_search_is_entry_only(qt_app) -> None:
    events: list[str] = []
    widget = BioinformaticsDataSourceWidget()
    widget.chinese_search_requested.connect(lambda: events.append("open"))

    result = widget.search_research_topic()
    card_titles = [label.text() for label in widget.findChildren(QLabel, "bioProjectCardTitle")]

    assert result == "中文研究问题检索已移动到独立页面。"
    assert events == ["open"]
    assert "GEO 检索关键词" not in " ".join(label.text() for label in widget.findChildren(QLabel))
    assert "本地 AI 检索助手" not in card_titles


def test_workspace_chinese_entry_opens_search_page_with_prefilled_topic(qt_app, project_summary) -> None:
    widget = BioinformaticsWorkspaceWidget()
    widget.show_data_source(project_summary)
    widget._data_source_page._chinese_query_input.setText("甲状腺癌与肥胖相关基因表达数据")

    widget._data_source_page.open_chinese_search()

    assert widget.current_page_object_name() == "bioinformaticsChineseDatasetSearchPage"
    assert widget._chinese_search_page._query_input.text() == "甲状腺癌与肥胖相关基因表达数据"


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


def test_data_source_registered_summary_and_next_button_states(qt_app, project_summary, tmp_path: Path) -> None:
    source = tmp_path / "expression_matrix.tsv"
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    assert widget._dataset_list_panel._table.rowCount() == 0
    assert not widget._dataset_list_panel._empty.isHidden()
    assert not widget._next_button.isEnabled()
    assert not widget.findChild(QPushButton, "local_importOpenSourceButton").isVisible()
    assert not widget.findChild(QPushButton, "local_importCopyPathButton").isVisible()
    assert not widget._dataset_list_panel._download_selected_button.isEnabled()
    assert not widget._dataset_list_panel._delete_selected_button.isEnabled()
    assert not widget._dataset_list_panel._continue_selected_button.isEnabled()

    widget.register_local_paths([source], strategy="reference", selected_kind="file", summary_key="local_import")

    table = widget._dataset_list_panel._table
    assert table.rowCount() == 1
    assert table.columnCount() == 8
    assert table.horizontalHeaderItem(0).text() == "选择"
    assert table.horizontalHeaderItem(1).text() == "来源"
    assert table.horizontalHeaderItem(2).text() == "数据集 / 文件名"
    assert table.horizontalHeaderItem(3).text() == "数据状态"
    assert table.horizontalHeaderItem(4).text() == "可用内容"
    assert table.horizontalHeaderItem(5).text() == "需要补充"
    assert table.horizontalHeaderItem(6).text() == "备注"
    assert table.horizontalHeaderItem(7).text() == "操作"
    assert table.item(0, 1).text() == "本地导入"
    assert "expression_matrix.tsv" in table.item(0, 2).text()
    assert table.item(0, 3).text() == "已导入"
    assert [button.text() for button in table.cellWidget(0, 7).findChildren(QPushButton)] == ["查看详情"]
    checkbox = table.cellWidget(0, 0)
    assert isinstance(checkbox, QCheckBox)
    checkbox.setChecked(True)
    assert not widget._dataset_list_panel._download_selected_button.isEnabled()
    assert widget._dataset_list_panel._delete_selected_button.isEnabled()
    assert widget._dataset_list_panel._continue_selected_button.isEnabled()
    assert widget._next_button.isEnabled()


def test_data_source_dataset_detail_prefers_summary_and_saves_user_note(qt_app, project_summary, tmp_path: Path) -> None:
    source = tmp_path / "expression_matrix.tsv"
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)
    widget.register_local_paths([source], strategy="reference", selected_kind="file", summary_key="local_import")

    key = next(iter(widget._dataset_entries))
    widget._show_dataset_detail(key)

    assert not widget._dataset_detail_panel.isHidden()
    assert "数据集编号或文件名：expression_matrix.tsv" in widget._dataset_detail_panel._summary.toPlainText()
    assert "摘要：暂无摘要" in widget._dataset_detail_panel._summary.toPlainText()
    assert widget._dataset_detail_panel._technical.isHidden()
    widget._dataset_detail_panel._note_edit.setPlainText("优先用于差异分析")
    widget._dataset_detail_panel._save_note()

    notes_path = project_summary.project_root / "manifests" / "user_dataset_notes.json"
    payload = json.loads(notes_path.read_text(encoding="utf-8"))
    assert payload["notes"][key]["note"] == "优先用于差异分析"
    assert "user_notes" not in json.loads(project_summary.manifest_path.read_text(encoding="utf-8"))
    assert widget._dataset_list_panel._table.item(0, 6).text() == "优先用于差异分析"


def test_data_source_keeps_history_cache_separate_until_user_adds(qt_app, project_summary) -> None:
    cache_dir = project_summary.project_root / "raw_data" / "geo" / "GSE99999"
    cache_dir.mkdir(parents=True)
    (cache_dir / "GSE99999_family.soft").write_text("^SERIES = GSE99999\n", encoding="utf-8")
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    assert widget._dataset_list_panel._table.rowCount() == 0
    assert not widget._history_cache_card.isHidden()
    assert "发现 1 个历史下载数据集" in widget._history_cache_hint.text()
    assert widget._history_cache_table.item(0, 0).text() == "GSE99999"
    assert widget._history_cache_table.horizontalHeader().sectionResizeMode(1) == QHeaderView.Stretch

    summary = widget._add_history_cache_to_project({"name": "GSE99999", "path": str(cache_dir)})

    assert summary is not None
    assert widget._dataset_list_panel._table.rowCount() == 1
    assert widget._dataset_list_panel._table.item(0, 1).text() == "本地导入"
    assert widget._history_cache_table.isHidden()
    assert widget._history_cache_hint.text() == "暂无历史缓存数据。"
    assert widget.status_message() == "已加入当前项目"


def test_history_cache_delete_button_confirms_before_deleting(qt_app, project_summary, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_dir = project_summary.project_root / "raw_data" / "geo" / "GSE88888"
    cache_dir.mkdir(parents=True)
    (cache_dir / "GSE88888_family.soft").write_text("^SERIES = GSE88888\n", encoding="utf-8")
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)
    delete_button = [button for button in widget._history_cache_table.cellWidget(0, 2).findChildren(QPushButton) if button.text() == "删除缓存"][0]

    monkeypatch.setattr(workflow_pages.QMessageBox, "question", lambda *args, **kwargs: workflow_pages.QMessageBox.Cancel)
    delete_button.click()

    assert cache_dir.exists()
    assert widget._history_cache_table.rowCount() == 1
    assert widget.status_message() == "已取消删除缓存。"


def test_history_cache_delete_removes_allowed_cache_and_refreshes(qt_app, project_summary, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_dir = project_summary.project_root / "raw_data" / "geo" / "GSE77777"
    cache_dir.mkdir(parents=True)
    (cache_dir / "GSE77777_family.soft").write_text("^SERIES = GSE77777\n", encoding="utf-8")
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)
    monkeypatch.setattr(workflow_pages.QMessageBox, "question", lambda *args, **kwargs: workflow_pages.QMessageBox.Yes)

    ok = widget._delete_history_cache_entry({"name": "GSE77777", "path": str(cache_dir)})

    assert ok is True
    assert not cache_dir.exists()
    assert widget._history_cache_table.isHidden()
    assert widget._history_cache_hint.text() == "暂无历史缓存数据。"
    assert widget.status_message() == "缓存已删除。"


def test_history_cache_delete_cleans_missing_cache_from_list(qt_app, project_summary, monkeypatch: pytest.MonkeyPatch) -> None:
    missing = project_summary.project_root / "raw_data" / "geo" / "GSE40404"
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)
    monkeypatch.setattr(workflow_pages.QMessageBox, "question", lambda *args, **kwargs: workflow_pages.QMessageBox.Yes)

    ok = widget._delete_history_cache_entry({"name": "GSE40404", "path": str(missing)})

    assert ok is True
    assert widget.status_message() == "缓存文件已不存在，已从列表移除。"


def test_history_cache_delete_refuses_project_bound_cache(qt_app, project_summary, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_dir = project_summary.project_root / "raw_data" / "geo" / "GSE66666"
    cache_dir.mkdir(parents=True)
    (cache_dir / "GSE66666_family.soft").write_text("^SERIES = GSE66666\n", encoding="utf-8")
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)
    summary = widget._add_history_cache_to_project({"name": "GSE66666", "path": str(cache_dir)})
    monkeypatch.setattr(workflow_pages.QMessageBox, "question", lambda *args, **kwargs: workflow_pages.QMessageBox.Yes)

    ok = widget._delete_history_cache_entry({"name": "GSE66666", "path": str(cache_dir)})

    assert summary is not None
    assert ok is False
    assert cache_dir.exists()
    assert "该数据已加入当前项目" in widget.status_message()


def test_history_cache_delete_refuses_external_or_traversal_paths(qt_app, project_summary, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    external = tmp_path / "manual_import.tsv"
    external.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    traversal = project_summary.project_root / "raw_data" / "geo" / ".." / "local_import"
    traversal.mkdir(parents=True, exist_ok=True)
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)
    monkeypatch.setattr(workflow_pages.QMessageBox, "question", lambda *args, **kwargs: workflow_pages.QMessageBox.Yes)

    external_ok = widget._delete_history_cache_entry({"name": "manual_import.tsv", "path": str(external)})
    traversal_ok = widget._delete_history_cache_entry({"name": "local_import", "path": str(traversal)})

    assert external_ok is False
    assert traversal_ok is False
    assert external.exists()
    assert traversal.exists()
    assert "路径不在允许删除的缓存目录内" in widget.status_message()


def test_chinese_dataset_search_page_empty_state_and_terms(qt_app) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()

    assert widget.objectName() == "bioinformaticsChineseDatasetSearchPage"
    assert not widget._continue_button.isEnabled()
    assert widget._registered_count_label.text() == "已选 GEO 0 个，TCGA 0 个，GTEx 0 个；0 个可进入识别。"
    assert widget._geo_query_box.toPlainText() == "暂无 GEO/GSE 检索草稿"
    assert widget._geo_query_box.isHidden()
    assert widget._tcga_query_box.toPlainText() == "暂无 TCGA/GDC 项目草稿"
    assert widget._gtex_query_box.toPlainText() == "暂无 GTEx 组织草稿"
    assert not widget._geo_empty_label.isHidden()
    assert not widget._tcga_empty_label.isHidden()
    assert not widget._gtex_empty_label.isHidden()
    assert widget._mapping_log.isHidden()
    button_texts = [button.text() for button in widget.findChildren(QPushButton)]
    assert button_texts.count("确认草稿") == 3
    assert "在线检索 GEO/GSE" in button_texts
    assert "在线检查 TCGA/GDC" in button_texts
    assert "在线检查 GTEx" in button_texts
    assert "查看完整检索词" in button_texts
    assert "检索候选数据集" not in button_texts
    assert "GEO/GSE" == widget._tabs.tabText(0)
    assert "TCGA/GDC" == widget._tabs.tabText(1)
    assert "GTEx" == widget._tabs.tabText(2)
    assert widget._continue_button.text() == "下一步：进入数据识别"

    widget.set_query_text("甲状腺癌")
    result = widget.generate_terms()

    assert result is not None
    assert widget.status_message() == "已生成检索草稿。确认前不会执行真实数据库检索。"
    assert "thyroid cancer" in widget._geo_query_box.toPlainText()
    assert "thyroid cancer" in widget._geo_draft_summary.text()
    assert "TCGA-THCA" in widget._tcga_query_box.toPlainText()
    assert "Thyroid" in widget._gtex_query_box.toPlainText()
    assert not widget._continue_button.isEnabled()
    assert widget._geo_empty_label.text() == "已生成 GEO/GSE 检索草稿，尚未执行在线检索。"
    assert "暂无候选结果" not in widget._geo_empty_label.text()
    assert widget._tcga_empty_label.isHidden()
    assert widget._gtex_empty_label.isHidden()
    assert widget._tcga_table.isHidden()
    assert widget._gtex_table.isHidden()
    tcga_card = _source_card_text(widget, "tcga_gdc")
    gtex_card = _source_card_text(widget, "gtex")
    assert "项目代码：" in tcga_card
    assert "TCGA-THCA" in tcga_card
    assert "中文名称：" in tcga_card
    assert "甲状腺癌队列" in tcga_card
    assert "英文名称：" in tcga_card
    assert "Thyroid Carcinoma" in tcga_card
    assert "数据库：" in tcga_card
    assert "TCGA/GDC" in tcga_card
    assert "可用数据：" in tcga_card
    assert "RNA-seq 表达、临床信息、突变数据" in tcga_card
    assert "适用说明：" in tcga_card
    assert "适合肿瘤样本分析" in tcga_card
    assert "选择项目" in tcga_card
    assert "查看说明" in tcga_card
    assert "创建下载清单" in tcga_card
    assert "待创建下载任务" in tcga_card
    assert "组织名称：" in gtex_card
    assert "Thyroid" in gtex_card
    assert "中文名称：" in gtex_card
    assert "甲状腺组织" in gtex_card
    assert "数据库：" in gtex_card
    assert "GTEx" in gtex_card
    assert "可用数据：" in gtex_card
    assert "正常组织 RNA 表达" in gtex_card
    assert "适用说明：" in gtex_card
    assert "GTEx 是正常组织表达参考，不是肿瘤样本数据库" in gtex_card
    assert "选择组织" in gtex_card
    assert "查看说明" in gtex_card
    assert "创建下载清单" in gtex_card
    assert "待创建下载任务" in gtex_card
    assert widget._mapping_log.isHidden()
    visible_text = " ".join(
        [label.text() for label in widget.findChildren(QLabel)]
        + [button.text() for button in widget.findChildren(QPushButton)]
        + [widget.status_message()]
    )
    for forbidden in ("fallback_registry_only", "configurable_not_called", "Ollama", "Translator", "Media", "rejected_terms", "batch effect", "PubMed", "PICO", "literature search", "Meta Analysis"):
        assert forbidden not in visible_text


def test_glioma_tcga_gtex_candidates_displayed(qt_app) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.set_query_text("脑胶质瘤")
    result = widget.generate_terms()

    assert result is not None
    assert "glioma" in widget._geo_query_box.toPlainText().lower()
    assert "glioblastoma" in widget._geo_query_box.toPlainText().lower()
    tcga_card = _source_card_text(widget, "tcga_gdc")
    assert "TCGA-GBM" in tcga_card
    assert "胶质母细胞瘤队列" in tcga_card
    assert "TCGA-LGG" in tcga_card
    assert "低级别胶质瘤队列" in tcga_card
    gtex_card = _source_card_text(widget, "gtex")
    assert "Brain" in gtex_card
    assert "脑组织" in gtex_card
    assert "正常组织 RNA 表达" in gtex_card


def test_chinese_dataset_search_online_buttons_execute_explicit_search(qt_app, monkeypatch) -> None:
    calls: list[tuple[str, bool]] = []

    def geo_search(self, query, *, online_enabled=False, limit=20, **kwargs):
        calls.append(("geo", online_enabled))
        return workflow_pages.SourceSearchResult(
            source="geo",
            search_status="completed",
            executed_query=query.geo_query_candidates[0],
            total_found=1,
            returned_count=1,
            displayed_count=1,
            candidates=(_geo_candidate(),),
            warnings=(),
            database_source="NCBI GEO",
        )

    def tcga_search(self, query, *, online_enabled=False, limit=20, **kwargs):
        calls.append(("tcga_gdc", online_enabled))
        return workflow_pages.SourceSearchResult(
            source="tcga_gdc",
            search_status="completed",
            executed_query="TCGA-THCA",
            total_found=1,
            returned_count=1,
            displayed_count=1,
            candidates=(workflow_pages.UnifiedDatasetCandidate("tcga_gdc", "TCGA-THCA", "Thyroid Carcinoma", "Homo sapiens", "thyroid cancer", "thyroid", "RNA-seq", 500, True, True, True, False, ("survival",), True, 95, (), {}),),
            warnings=(),
            database_source="GDC",
        )

    def gtex_search(self, query, *, online_enabled=False, limit=20, **kwargs):
        calls.append(("gtex", online_enabled))
        return workflow_pages.SourceSearchResult(
            source="gtex",
            search_status="completed",
            executed_query="Thyroid",
            total_found=1,
            returned_count=1,
            displayed_count=1,
            candidates=(workflow_pages.UnifiedDatasetCandidate("gtex", "GTEX-THYROID", "Thyroid", "Homo sapiens", "normal reference", "Thyroid", "TPM", 653, True, True, False, False, ("reference",), True, 85, (), {}),),
            warnings=(),
            database_source="GTEx",
        )

    monkeypatch.setattr(workflow_pages.GeoSearchAdapter, "search", geo_search)
    monkeypatch.setattr(workflow_pages.TcgaGdcSearchAdapter, "search", tcga_search)
    monkeypatch.setattr(workflow_pages.GtexSearchAdapter, "search", gtex_search)

    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.set_query_text("甲状腺癌")
    widget.generate_terms()
    calls.clear()

    widget.search_geo_candidates()
    widget.search_tcga_candidates()
    widget.search_gtex_candidates()

    assert calls == [("geo", True), ("tcga_gdc", True), ("gtex", True)]
    assert "已完成 GTEx 在线检查" in widget.status_message()


def test_chinese_dataset_search_confirm_draft_does_not_run_real_search(qt_app, project_summary, monkeypatch) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    widget.set_query_text("甲状腺癌")
    widget.generate_terms()

    def fail_search(*args, **kwargs):
        raise AssertionError("confirm draft must not execute database search")

    monkeypatch.setattr(workflow_pages.GeoSearchAdapter, "search", fail_search)
    monkeypatch.setattr(workflow_pages.TcgaGdcSearchAdapter, "search", fail_search)
    monkeypatch.setattr(workflow_pages.GtexSearchAdapter, "search", fail_search)

    record = widget.confirm_query_draft()

    assert record is not None
    assert record.status == "confirmed"
    assert widget.status_message() == "已确认检索草稿。确认本身不联网；如需联网请点击在线检索/在线检查。"
    saved = list((project_summary.project_root / "ai_drafts").glob("*bio_generate_dataset_query_draft.json"))
    assert saved
    payload = json.loads(saved[0].read_text(encoding="utf-8"))
    assert payload["status"] == "confirmed"
    assert payload["summary"]["search_executed"] is False
    assert "raw_prompt" not in payload
    assert "raw_response" not in payload
    dumped = json.dumps(payload, ensure_ascii=False)
    assert "PubMed" not in dumped
    assert "Embase" not in dumped
    assert "WOS" not in dumped
    assert "CNKI" not in dumped


def test_no_generic_tcga_mapping_label(qt_app) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.set_query_text("脑胶质瘤")
    widget.generate_terms()

    rendered = _source_card_text(widget, "tcga_gdc")
    assert "TCGA/GDC 项目映射：TCGA" not in rendered
    assert "本地词库映射" not in rendered


def test_chinese_dataset_search_broad_query_guard_does_not_create_candidates(qt_app) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.set_query_text("表达谱")
    result = widget.generate_terms()

    assert result is not None
    assert result.query.broad_query_guard is True
    assert result.query.geo_query_candidates == ()
    assert result.query.tcga_project_ids == ()
    assert result.query.gtex_tissues == ()
    assert result.candidates == ()
    assert widget.status_message() == "请补充明确疾病或组织主题后再检索候选数据集。"
    assert widget._geo_query_box.toPlainText() == "暂无 GEO/GSE 检索草稿"
    assert widget._tcga_empty_label.text() == "未生成 TCGA/GDC 项目候选。"
    assert widget._gtex_empty_label.text() == "未生成 GTEx 组织候选。"
    assert not widget._continue_button.isEnabled()


def test_chinese_dataset_search_geo_candidate_has_registration_button(qt_app) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    candidate = _geo_candidate()

    widget._fill_geo_candidates([candidate])

    assert not widget._geo_table.isHidden()
    assert widget._geo_table.horizontalHeaderItem(0).text() == "操作"
    assert widget._geo_table.columnWidth(0) >= 120
    buttons = widget._geo_table.cellWidget(0, 0).findChildren(QPushButton)
    assert [button.text() for button in buttons] == ["查看详情"]
    buttons[0].click()
    assert not widget._geo_dataset_detail_panel.isHidden()
    assert "GSE33630" in widget._geo_dataset_detail_panel._title.text()
    assert widget._geo_dataset_detail_panel._save_button.text() == "添加到项目"
    assert widget._geo_dataset_detail_panel._translation_text.toPlainText() == "尚未生成中文翻译。"
    profile_text = widget._geo_dataset_detail_panel._profile_text.toPlainText()
    assert "样本结构预览" in profile_text
    assert "候选比较组" in profile_text
    assert "需用户确认" in profile_text


def test_register_geo_requires_open_project(qt_app) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    candidate = _geo_candidate()
    widget._candidates = {("geo", "GSE33630"): candidate}

    assert widget.register_candidate("geo", "GSE33630") is None
    assert widget.status_message() == "请先创建或打开生信分析项目。"


def test_register_geo_search_result_as_source(qt_app, project_summary) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    candidate = _geo_candidate()
    widget._candidates = {("geo", "GSE33630"): candidate}
    widget.set_query_text("脑胶质瘤")

    summary = widget.register_candidate("geo", "GSE33630")

    assert summary is not None
    assert summary.source_type == "geo_accession"
    assert summary.status == "planned"
    assert summary.registered_files == ()
    assert widget.status_message() == "已选择候选来源，待下载数据文件。"
    record_path = project_summary.project_root / "acquisition" / "records" / f"{summary.acquisition_id}.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["source_type"] == "geo_accession"
    assert record["strategy"] == "plan_only"
    assert record["registered_files"] == []
    metadata = record["metadata"]
    assert metadata["accession"] == "GSE33630"
    assert metadata["title"] == "Glioma RNA-seq expression profile"
    assert metadata["organism"] == "Homo sapiens"
    assert metadata["sample_count"] == 45
    assert metadata["platform_accessions"] == ["GPL11154"]
    assert metadata["source_database"] == "NCBI GEO"
    assert metadata["download_plan_available"] is True
    assert metadata["ready_for_recognition"] == "pending"
    assert metadata["audit"]["event_type"] == "geo_source_registered"


def test_register_geo_result_preserves_query_used(qt_app, project_summary) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    candidate = _geo_candidate(query_used='("glioma" OR "glioblastoma") AND "RNA-seq" AND GSE[ETYP]')
    widget._candidates = {("geo", "GSE33630"): candidate}

    summary = widget.register_candidate("geo", "GSE33630")

    assert summary is not None
    metadata = json.loads(summary.record_path.read_text(encoding="utf-8"))["metadata"]
    assert metadata["query_used"] == '("glioma" OR "glioblastoma") AND "RNA-seq" AND GSE[ETYP]'
    assert metadata["audit"]["query_used"] == metadata["query_used"]


def test_chinese_dataset_search_generates_download_task_without_fake_download(qt_app, project_summary) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    candidate = _geo_candidate()
    widget._candidates = {("geo", "GSE33630"): candidate}
    widget.set_query_text("脑胶质瘤")

    result = widget.generate_candidate_download_task("geo", "GSE33630")

    assert result is not None
    assert widget.status_message() == "已生成 GEO 下载任务：GSE33630。尚未下载数据文件。"
    assert not widget._continue_button.isEnabled()
    assert not (project_summary.project_root / "raw_data" / "geo" / "GSE33630" / "GSE33630_family.soft.gz").exists()
    records = [path for path in (project_summary.project_root / "acquisition" / "records").glob("*.json") if path.name != "latest_acquisition_record.json"]
    assert len(records) == 1
    record = json.loads(records[0].read_text(encoding="utf-8"))
    assert record["source_type"] == "geo_accession"
    assert record["strategy"] == "plan_only"
    assert record["metadata"]["download_status"] == "registered_pending_geo_download"
    assert record["metadata"]["download_executed"] is False
    assert Path(record["metadata"]["download_request_path"]).exists()
    assert Path(record["metadata"]["download_receipt_path"]).exists()


def test_chinese_dataset_search_downloads_geo_and_runs_recognition(qt_app, project_summary) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    widget._download_service = workflow_pages.DatasetDownloadService(
        geo_downloader=_FakeGeoDownloader(),
        geo_asset_discoverer=_FakeGeoAssetDiscoverer(),
        geo_asset_downloader=_FakeGeoRemoteAssetDownloader(),
    )
    candidate = _geo_candidate()
    widget._candidates = {("geo", "GSE33630"): candidate}
    widget._fill_geo_candidates([candidate])
    widget.set_query_text("脑胶质瘤")

    result = widget.download_geo_candidate("GSE33630")

    assert result is not None
    assert result.status == "geo_metadata_downloaded"
    assert result.download_executed is True
    assert len(result.downloaded_files) == 1
    assert Path(result.downloaded_files[0]).exists()
    assert "元数据已下载" in widget.status_message()
    assert "表达矩阵待下载" in widget.status_message()
    assert widget._registered_count_label.text() == "已选 GEO 1 个，TCGA 0 个，GTEx 0 个；1 个可进入识别。 当前建议操作：进入数据识别。"
    assert widget._continue_button.isEnabled()
    assert widget._geo_table.item(0, 6).text() == "元数据已下载 / 表达矩阵待下载 / 已发现补充文件 / 可进入识别"
    widget._show_candidate_detail(candidate)
    assert "元数据已下载" in widget._geo_dataset_detail_panel._asset_text.toPlainText()
    assert "表达矩阵：待下载" in widget._geo_dataset_detail_panel._asset_text.toPlainText()
    assert "建议下载文件" in widget._geo_dataset_detail_panel._profile_text.toPlainText()
    assert "GSE33630_counts.tsv.gz" in widget._geo_dataset_detail_panel._profile_text.toPlainText()
    assert not widget._geo_dataset_detail_panel._download_assets_button.isHidden()
    assert widget._geo_dataset_detail_panel._download_assets_button.isEnabled()
    assert widget._geo_download_list_panel._table.item(0, 3).text() == "元数据已下载"
    assert "表达矩阵" not in widget._geo_download_list_panel._table.item(0, 4).text()
    assert "表达矩阵" in widget._geo_download_list_panel._table.item(0, 5).text()
    widget._geo_download_list_panel._checks["geo:GSE33630"].setChecked(True)
    assert widget._geo_download_list_panel._download_selected_button.text() == "下载补充文件"
    assert widget._geo_download_list_panel._download_selected_button.isEnabled()
    manifest_path = Path(str(result.details["asset_manifest_path"]))
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert {item["asset_type"] for item in manifest["assets"]} == {"family_soft", "series_matrix", "supplementary_file"}
    report = workflow_pages.load_recognition_report(project_summary.project_root)
    assert report is not None
    files = report.get("files", [])
    assert files
    assert files[0]["recognized_type"] == "geo_soft_container"
    assert "expression_matrix" in files[0]["recognized_roles"]


def test_chinese_dataset_search_downloads_geo_supplementary_assets_and_refreshes_processing(qt_app, project_summary) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    widget._download_service = workflow_pages.DatasetDownloadService(
        geo_downloader=_FakeGeoDownloader(),
        geo_asset_discoverer=_FakeGeoAssetDiscoverer(),
        geo_asset_downloader=_FakeGeoRemoteAssetDownloader(),
    )
    candidate = _geo_candidate()
    widget._candidates = {("geo", "GSE33630"): candidate}
    widget._fill_geo_candidates([candidate])
    widget.set_query_text("脑胶质瘤")

    metadata_result = widget.download_geo_candidate("GSE33630")
    supplement_result = widget.download_geo_candidate("GSE33630")

    assert metadata_result is not None
    assert supplement_result is not None
    assert supplement_result.status == "geo_assets_downloaded"
    assert "补充/Matrix 资产" in widget.status_message()
    assert "数据处理任务" in widget.status_message()
    assert widget._geo_table.item(0, 6).text() == "元数据已下载 / 表达矩阵已下载 / 补充文件已下载 / 可进入识别"
    assert widget._geo_registered_table.rowCount() == 1
    assert widget._geo_registered_table.item(0, 0).text() == "GSE33630"
    assert "表达矩阵" in widget._geo_registered_table.item(0, 2).text()
    assert widget._geo_registered_table.item(0, 4).text() == "进入数据识别"
    widget._show_candidate_detail(candidate)
    assert "补充文件" in widget._geo_dataset_detail_panel._asset_text.toPlainText()
    assert widget._geo_dataset_detail_panel._download_assets_button.isHidden()
    report = workflow_pages.load_recognition_report(project_summary.project_root)
    assert report is not None
    recognized_types = {file["recognized_type"] for file in report.get("files", [])}
    assert "geo_series_matrix_container" in recognized_types
    standardization = workflow_pages.load_standardization_artifacts(project_summary.project_root)
    task_plan = standardization["data_processing_task_plan"]
    assert task_plan is not None
    task_types = {task["task_type"] for task in task_plan["tasks"]}
    assert {"expression_matrix_cleaning", "gene_annotation_mapping", "sample_annotation_review"} <= task_types


def test_chinese_dataset_search_geo_brief_uses_summary_service(qt_app) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    candidate = _geo_candidate()
    widget._candidates = {("geo", "GSE33630"): candidate}

    class _FakeSummaryService:
        def summarize(self, text):
            return SimpleNamespace(
                status="completed",
                to_dict=lambda: {
                    "status": "completed",
                    "title_zh": "胶质瘤表达谱",
                    "summary_zh": "胶质瘤样本摘要。",
                    "overall_design_zh": "肿瘤和对照。",
                    "brief_zh": "该数据集比较胶质瘤和对照样本。",
                    "error_message": "",
                },
            )

    widget._text_summary_service = _FakeSummaryService()
    payload = widget.generate_geo_chinese_brief("GSE33630")

    assert payload is not None
    assert widget.status_message() == "已生成中文翻译与提炼草稿。"
    assert widget._mapping_log.isHidden()
    assert not widget._geo_dataset_detail_panel.isHidden()
    text = widget._geo_dataset_detail_panel._translation_text.toPlainText()
    assert "该数据集比较胶质瘤和对照样本。" in text
    assert "AI 草稿：中文翻译与提炼，需人工确认。" in text
    assert "与检索主题匹配：" not in text
    assert "推荐等级：" not in text
    assert "医学实体一致性状态" not in text


def test_geo_brief_topic_match_label_maps_consistency_status(qt_app) -> None:
    candidate = _geo_candidate()
    text = workflow_pages._geo_text_summary_user_display(
        candidate,
        {
            "status": "completed",
            "title_zh": "胶质瘤表达谱",
            "summary_zh": "胶质瘤样本摘要。",
            "brief_zh": "该数据集可能与检索主题相关。",
            "entity_consistency_status": "partial",
        },
    )

    assert "AI 草稿：中文翻译与提炼，需人工确认。" in text
    assert "一句话介绍：该数据集可能与检索主题相关。" in text
    assert "与检索主题匹配：" not in text
    assert "医学实体一致性状态" not in text


def test_chinese_dataset_search_geo_brief_retries_after_fallback(qt_app) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    candidate = _geo_candidate()
    widget._candidates = {("geo", "GSE33630"): candidate}

    class _RetrySummaryService:
        def __init__(self) -> None:
            self.calls = 0

        def summarize(self, text):
            self.calls += 1
            status = "failed" if self.calls == 1 else "completed"
            brief = "英文摘要待人工确认。" if self.calls == 1 else "第二次生成了可靠中文简介。"
            return SimpleNamespace(
                status=status,
                to_dict=lambda: {
                    "status": status,
                    "title_zh": "胶质瘤表达谱",
                    "summary_zh": "胶质瘤样本摘要。",
                    "overall_design_zh": "肿瘤和对照。",
                    "brief_zh": brief,
                    "error_message": "timeout" if status == "failed" else "",
                    "quality_warnings": ["需人工确认"] if status == "failed" else [],
                },
            )

    service = _RetrySummaryService()
    widget._text_summary_service = service

    first = widget.generate_geo_chinese_brief("GSE33630")
    second = widget.generate_geo_chinese_brief("GSE33630")

    assert first is not None
    assert first["status"] == "failed"
    assert second is not None
    assert second["status"] == "completed"
    assert service.calls == 2
    assert "第二次生成了可靠中文简介。" in widget._geo_dataset_detail_panel._translation_text.toPlainText()


def test_register_geo_result_deduplicates_existing_source(qt_app, project_summary) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    candidate = _geo_candidate()
    widget._candidates = {("geo", "GSE33630"): candidate}

    first = widget.register_candidate("geo", "GSE33630")
    duplicate = widget.register_candidate("geo", "GSE33630")

    assert first is not None
    assert duplicate is None
    records = [path for path in (project_summary.project_root / "acquisition" / "records").glob("*.json") if path.name != "latest_acquisition_record.json"]
    assert len(records) == 1
    assert widget.status_message() == "已选择数据：GSE33630"


def test_registered_geo_source_appears_in_pre_recognition_input_list(qt_app, project_summary) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    candidate = _geo_candidate()
    widget._candidates = {("geo", "GSE33630"): candidate}
    summary = widget.register_candidate("geo", "GSE33630")

    recognition = BioinformaticsRecognitionWidget()
    recognition.refresh_project(project_summary)
    table = recognition.findChild(QTableWidget, "preRecognitionInputList")

    assert summary is not None
    assert table.rowCount() == 1
    assert table.cellWidget(0, 0) is not None
    assert table.item(0, 1).text() == "GEO/GSE 数据来源"
    assert table.item(0, 2).text() == "GSE33630"
    assert table.item(0, 3).text() == "GEO"
    assert table.item(0, 4).text() == "待下载"


def test_geo_source_registration_does_not_auto_download_or_analyze(qt_app, project_summary) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    candidate = _geo_candidate()
    widget._candidates = {("geo", "GSE33630"): candidate}
    summary = widget.register_candidate("geo", "GSE33630")

    assert summary is not None
    assert not (project_summary.project_root / "raw_data" / "geo" / "GSE33630").exists()
    assert list((project_summary.project_root / "analysis").glob("**/*")) == []
    record_path = project_summary.project_root / "acquisition" / "records" / f"{summary.acquisition_id}.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["status"] == "planned"
    assert record["metadata"]["registration_handoff"] == "data_recognition_pending_source_acquisition"


def test_chinese_dataset_search_registers_candidate_and_recognition_pre_input(qt_app, project_summary) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    widget.set_query_text("甲状腺癌")
    widget.generate_terms()

    summary = widget.register_candidate("tcga_gdc", "TCGA-THCA")

    assert summary is not None
    assert summary.source_type == "tcga_project"
    assert widget._tcga_registered_table.rowCount() == 1
    assert widget._tcga_registered_table.item(0, 0).text() == "TCGA-THCA"
    assert widget._registered_count_label.text() == "已选 GEO 0 个，TCGA 1 个，GTEx 0 个；0 个可进入识别。 当前建议操作：先补全表达矩阵。"
    assert not widget._continue_button.isEnabled()
    assert widget._continue_button.text() == "下一步：进入数据识别"
    assert widget.status_message() == "已选择候选来源，待下载数据文件。"
    assert "已选择，待创建下载任务" in _source_card_text(widget, "tcga_gdc")
    download_result = widget.generate_candidate_download_task("tcga_gdc", "TCGA-THCA")
    assert download_result is not None
    assert download_result.status == "tcga_gdc_download_manifest_pending_file_selection"
    assert "GDC 下载任务清单" in widget.status_message()
    assert "下载清单已创建" in _source_card_text(widget, "tcga_gdc")
    registered_button = widget.findChild(QPushButton, "registerCandidateButton_tcga_gdc_TCGA-THCA")
    assert registered_button.text() == "已选择"
    assert not registered_button.isEnabled()
    duplicate = widget.register_candidate("tcga_gdc", "TCGA-THCA")
    assert duplicate is None
    assert widget._tcga_registered_table.rowCount() == 1

    recognition = BioinformaticsRecognitionWidget()
    recognition.refresh_project(project_summary)
    table = recognition.findChild(QTableWidget, "preRecognitionInputList")
    assert table.rowCount() == 1
    assert table.cellWidget(0, 0) is not None
    assert table.item(0, 1).text() == "TCGA/GDC 项目"
    assert table.item(0, 2).text() == "TCGA-THCA"
    record_path = project_summary.project_root / "acquisition" / "records" / f"{summary.acquisition_id}.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["source_type"] == "tcga_project"
    assert record["strategy"] == "plan_only"
    assert record["status"] == "planned"
    assert record["registered_files"] == []
    assert record["metadata"]["query_source"] == "chinese_topic_search"
    assert record["metadata"]["original_chinese_topic"] == "甲状腺癌"
    assert record["metadata"]["project_id"] == "TCGA-THCA"
    assert record["metadata"]["project_name"] == "Thyroid Carcinoma"
    assert record["metadata"]["source_origin"] == "local_mapping"
    assert record["metadata"]["registration_status"] == "registered_as_planned_source"


def test_chinese_dataset_search_registers_gtex_tissue_as_planned_source(qt_app, project_summary) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    widget.set_query_text("甲状腺癌")
    widget.generate_terms()

    summary = widget.register_candidate("gtex", "GTEX-THYROID")

    assert summary is not None
    assert summary.source_type == "gtex_tissue"
    assert widget._gtex_registered_table.rowCount() == 1
    assert widget._gtex_registered_table.item(0, 0).text() == "Thyroid"
    assert "已选择，待创建下载任务" in _source_card_text(widget, "gtex")
    download_result = widget.generate_candidate_download_task("gtex", "GTEX-THYROID")
    assert download_result is not None
    assert download_result.status == "gtex_download_manifest_created"
    assert "GTEx 组织下载清单" in widget.status_message()
    assert "下载清单已创建" in _source_card_text(widget, "gtex")
    assert not widget._continue_button.isEnabled()
    assert not (project_summary.project_root / "raw_data" / "gtex" / "GTEX-THYROID").exists()

    record_path = project_summary.project_root / "acquisition" / "records" / f"{summary.acquisition_id}.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["source_type"] == "gtex_tissue"
    assert record["status"] == "planned"
    assert record["registered_files"] == []
    assert record["metadata"]["query_source"] == "chinese_topic_search"
    assert record["metadata"]["tissue_name"] == "Thyroid"
    assert record["metadata"]["source_origin"] == "local_mapping"
    assert record["metadata"]["registration_status"] == "registered_as_planned_source"


def test_chinese_dataset_search_continue_enters_recognition(qt_app, project_summary) -> None:
    widget = BioinformaticsWorkspaceWidget()

    widget.show_chinese_search(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsChineseDatasetSearchPage"
    widget._chinese_search_page.set_query_text("脑胶质瘤")
    widget._chinese_search_page._download_service = workflow_pages.DatasetDownloadService(
        geo_downloader=_FakeGeoDownloader(),
        geo_asset_discoverer=_FakeGeoAssetDiscoverer(),
    )
    widget._chinese_search_page._candidates = {("geo", "GSE33630"): _geo_candidate()}
    widget._chinese_search_page.download_geo_candidate("GSE33630")
    widget._chinese_search_page.continue_to_recognition()

    assert widget.current_page_object_name() == "bioinformaticsRecognitionPage"
    table = widget._recognition_page.findChild(QTableWidget, "preRecognitionInputList")
    assert table.rowCount() == 1
    assert table.item(0, 2).text() == "GSE33630"


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
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="local_import",
        source_label="expression_matrix.tsv",
        strategy="reference",
        selected_paths=[raw_file],
    )

    recognition = BioinformaticsRecognitionWidget()
    recognition.refresh_project(project_summary)
    checkbox = recognition.findChild(QCheckBox)
    assert checkbox is not None
    checkbox.setChecked(True)
    report = recognition.run_recognition()
    assert report is not None
    assert "已读取识别报告" in recognition.status_message()

    readiness = BioinformaticsReadinessDashboardWidget()
    readiness.refresh_project(project_summary)
    artifacts = readiness.run_readiness_check()
    assert artifacts is not None
    assert "继续" in readiness.status_message()

    standardization = BioinformaticsStandardizedAssetsWidget()
    standardization.refresh_project(project_summary)
    generated = standardization.generate_assets()
    assert generated is not None
    assert "标准化资产" in standardization.status_message()


def test_recognition_requires_selected_inputs(qt_app, project_summary) -> None:
    source = project_summary.project_root / "raw_data" / "local_import" / "expression.tsv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    workflow_pages.register_acquisition(project_summary.project_root, source_type="local_import", source_label="expression.tsv", strategy="reference", selected_paths=[source])

    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)

    assert widget.run_recognition() is None
    assert widget.status_message() == "请先选择需要识别的数据源。"


def test_recognition_only_scans_checked_sources(qt_app, project_summary) -> None:
    selected = project_summary.project_root / "raw_data" / "local_import" / "selected_expression.tsv"
    skipped = project_summary.project_root / "raw_data" / "local_import" / "skipped_expression.tsv"
    selected.parent.mkdir(parents=True, exist_ok=True)
    selected.write_text("gene\tcase_1\tcontrol_1\nTP53\t2\t1\n", encoding="utf-8")
    skipped.write_text("gene\tcase_1\tcontrol_1\nEGFR\t3\t1\n", encoding="utf-8")
    workflow_pages.register_acquisition(project_summary.project_root, source_type="local_import", source_label="selected", strategy="reference", selected_paths=[selected])
    workflow_pages.register_acquisition(project_summary.project_root, source_type="local_import", source_label="skipped", strategy="reference", selected_paths=[skipped])

    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)
    table = widget.findChild(QTableWidget, "preRecognitionInputList")
    assert table.rowCount() == 2
    selected_row = next(row for row in range(table.rowCount()) if table.item(row, 2).text() == "selected_expression.tsv")
    table.cellWidget(selected_row, 0).setChecked(True)

    report = widget.run_recognition()

    assert report is not None
    assert report["selected_input_count"] == 1
    assert report["skipped_unselected_count"] == 1
    file_names = [item["file_name"] for item in report["files"]]
    assert file_names == [Path(report["selected_inputs"][0]).name]
    assert "skipped_expression.tsv" not in file_names
    current = json.loads((project_summary.project_root / "recognized_data" / "current.json").read_text(encoding="utf-8"))
    run_id = current["run_id"]
    run_dir = project_summary.project_root / "recognized_data" / "runs" / run_id
    assert run_dir.is_dir()
    assert (run_dir / "input_manifest.json").exists()
    assert (run_dir / "recognized_files.json").exists()
    assert (run_dir / "recognition_report.json").exists()
    assert (run_dir / "warnings.json").exists()
    history = widget.findChild(QTableWidget, "recognitionHistoryTable")
    assert history is not None
    assert history.rowCount() == 1
    assert history.item(0, 1).text() == "本次识别"


def test_recognition_main_buttons_are_simplified_and_summary_read_only(qt_app, project_summary) -> None:
    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)
    button_texts = [button.text() for button in widget.findChildren(QPushButton)]

    assert "开始识别" in button_texts
    assert "刷新" in button_texts
    assert widget.findChild(QFrame, "recognitionTechnicalOperations").isHidden()
    assert widget._counts.isReadOnly()


def test_recognition_opening_old_project_keeps_legacy_report_in_history(qt_app, project_summary, tmp_path: Path) -> None:
    source = tmp_path / "legacy_expression.tsv"
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    _write_mock_recognition_report(
        project_summary.project_root,
        [
            {
                "file_name": source.name,
                "original_path": str(source),
                "recognized_type": "expression_matrix",
                "confidence": 0.9,
                "file_size": source.stat().st_size,
                "reason": "legacy",
                "route_path": str(project_summary.project_root / "recognized_data/expression_matrix" / source.name),
            }
        ],
    )

    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)
    current_table = widget.findChild(QTableWidget, "recognitionResultTable")
    history = widget.findChild(QTableWidget, "recognitionHistoryTable")

    assert current_table is not None
    assert current_table.rowCount() == 0
    assert "尚未开始本次识别" in widget._counts.toPlainText()
    assert history is not None
    assert history.rowCount() == 1
    assert history.item(0, 1).text() == "旧版识别记录"
    assert history.item(0, 3).text() == "1"
    assert not (project_summary.project_root / "recognized_data" / "current.json").exists()


def test_recognition_filters_system_files_from_report(qt_app, project_summary) -> None:
    raw_dir = project_summary.project_root / "raw_data" / "local_import"
    raw_dir.mkdir(parents=True, exist_ok=True)
    expression = raw_dir / "expression.tsv"
    expression.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    (raw_dir / ".DS_Store").write_text("system", encoding="utf-8")
    (raw_dir / "._expression.tsv").write_text("system", encoding="utf-8")
    macosx = raw_dir / "__MACOSX"
    macosx.mkdir()
    (macosx / "expression.tsv").write_text("system", encoding="utf-8")

    report = workflow_pages.run_project_recognition(project_summary.project_root)

    names = [str(item.get("file_name")) for item in report["files"]]
    assert names == ["expression.tsv"]
    assert ".DS_Store" not in names
    assert "._expression.tsv" not in names


def test_recognition_delete_selected_removes_binding_not_file(qt_app, project_summary) -> None:
    source = project_summary.project_root / "raw_data" / "local_import" / "expression.tsv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    workflow_pages.register_acquisition(project_summary.project_root, source_type="local_import", source_label="expression.tsv", strategy="reference", selected_paths=[source])
    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)
    table = widget.findChild(QTableWidget, "preRecognitionInputList")
    table.cellWidget(0, 0).setChecked(True)

    widget._delete_selected_pre_recognition_sources()

    assert source.exists()
    assert table.rowCount() == 0
    assert "未删除原始文件" in widget.status_message()


def test_readiness_page_uses_compact_status_and_warning_chips(qt_app, project_summary) -> None:
    raw_file = project_summary.project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    BioinformaticsRecognitionWidget().refresh_project(project_summary)
    workflow_pages.run_project_recognition(project_summary.project_root)

    readiness = BioinformaticsReadinessDashboardWidget()
    readiness.refresh_project(project_summary)
    readiness.run_readiness_check()

    assert readiness.findChild(QFrame, "readinessStatusCard") is not None
    chips = readiness.findChild(QLabel, "readinessWarningChips")
    assert chips is not None
    assert "待办项" in chips.text() or "提示" in chips.text()
    assert "已识别到的数据：表达矩阵" in readiness.findChild(QLabel, "readinessRecognizedInputs").text()
    assert "比较分组" in readiness.findChild(QLabel, "readinessMissingInputs").text()
    assert "下一步建议" in readiness.findChild(QLabel, "readinessNextStep").text()
    table = readiness.findChild(QTableWidget, "readinessCapabilityTable")
    assert [table.horizontalHeaderItem(index).text() for index in range(table.columnCount())] == ["分析项目", "当前状态", "还需要什么", "建议操作"]
    assert table.minimumHeight() >= 360
    assert readiness._details.isHidden()


def test_readiness_missing_info_entry_and_templates(qt_app, project_summary) -> None:
    raw_file = project_summary.project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    workflow_pages.run_project_recognition(project_summary.project_root)

    readiness = BioinformaticsReadinessDashboardWidget()
    readiness.refresh_project(project_summary)
    readiness.run_readiness_check()

    todo_card = readiness.findChild(QFrame, "readinessTodoCard")
    assert todo_card is not None
    assert not readiness.findChild(QFrame, "readinessTodo_sample_metadata").isHidden()
    assert not readiness.findChild(QFrame, "readinessTodo_comparison_config").isHidden()
    assert not readiness.findChild(QFrame, "readinessTodo_gmt_gene_set").isHidden()
    assert not readiness._sample_file_button.isHidden()
    assert not readiness._sample_manual_button.isHidden()
    assert not readiness._comparison_file_button.isHidden()
    assert not readiness._comparison_manual_button.isHidden()
    assert not readiness._comparison_template_button.isHidden()
    assert readiness.findChild(QFrame, "readinessTodo_expression_matrix").isHidden()

    template = readiness.create_missing_info_template("sample_metadata")
    assert template is not None
    assert template.exists()
    assert "sample_id" in template.read_text(encoding="utf-8")
    comparison_template = readiness.create_missing_info_template("comparison_config")
    assert comparison_template is not None
    assert "case_group" in comparison_template.read_text(encoding="utf-8")


def test_readiness_default_view_hides_technical_warnings(qt_app, project_summary) -> None:
    readiness = BioinformaticsReadinessDashboardWidget()
    readiness.refresh_project(project_summary)
    readiness._render(
        {
            "readiness_report": {
                "overall_status": "partially_ready",
                "has_core_input": True,
                "available_inputs": ["expression_matrix", "sample_metadata"],
                "warnings": [
                    "numeric density is too low for expression payload: asset_manifest.json",
                    "sample-like columns are insufficient for expression payload",
                ],
            },
            "capability_matrix": {
                "rows": [
                    {
                        "analysis_type": "differential_expression",
                        "label": "差异表达分析",
                        "can_run": False,
                        "available_inputs": ["expression_matrix", "sample_metadata"],
                        "missing_inputs": ["comparison_config"],
                        "warnings": [],
                        "next_step": "请补充缺失输入或返回前序页面。",
                    }
                ]
            },
            "readiness_path": str(project_summary.project_root / "logs/readiness/readiness_report.json"),
            "matrix_path": str(project_summary.project_root / "manifests/analysis_capability_matrix.json"),
        }
    )

    default_text = "\n".join(label.text() for label in readiness.findChildren(QLabel))
    assert "numeric density" not in default_text
    assert "sample-like columns" not in default_text
    assert "asset_manifest.json" not in default_text
    assert "比较分组" in default_text
    assert readiness._details.isHidden()
    readiness._details.setVisible(True)
    assert "numeric density" in readiness._details.toPlainText()


def test_readiness_main_buttons_are_simplified(qt_app, project_summary) -> None:
    readiness = BioinformaticsReadinessDashboardWidget()
    readiness.refresh_project(project_summary)
    button_texts = [button.text() for button in readiness.findChildren(QPushButton)]

    assert "重新检查" in button_texts
    assert "继续：标准化数据" in button_texts
    assert "运行 Ready 检查" not in button_texts
    assert "刷新状态" not in button_texts
    assert "保存并重新检查" not in button_texts
    assert "继续：标准化资产" not in button_texts


def test_recognition_page_shows_group_preview(qt_app, project_summary) -> None:
    expression = project_summary.project_root / "raw_data" / "local_import" / "expression.tsv"
    samples = project_summary.project_root / "raw_data" / "local_import" / "sample_metadata.tsv"
    expression.parent.mkdir(parents=True, exist_ok=True)
    expression.write_text("gene\tGSM1\tGSM2\tGSM3\tGSM4\nTP53\t1\t2\t3\t4\n", encoding="utf-8")
    samples.write_text("sample_id\tcondition\nGSM1\tcontrol\nGSM2\tcontrol\nGSM3\ttreated\nGSM4\ttreated\n", encoding="utf-8")
    workflow_pages.run_project_recognition(project_summary.project_root)

    recognition = BioinformaticsRecognitionWidget()
    recognition.refresh_project(project_summary)
    preview = recognition.findChild(QTextEdit, "recognitionGroupPreviewReport")
    history = recognition.findChild(QTableWidget, "recognitionHistoryTable")

    assert preview is not None
    assert preview.toPlainText() == ""
    assert "尚未开始本次识别" in recognition._counts.toPlainText()
    assert history is not None
    assert history.rowCount() >= 1


def test_readiness_confirms_group_preview_before_comparison_config(qt_app, project_summary) -> None:
    expression = project_summary.project_root / "raw_data" / "local_import" / "expression.tsv"
    samples = project_summary.project_root / "raw_data" / "local_import" / "sample_metadata.tsv"
    expression.parent.mkdir(parents=True, exist_ok=True)
    expression.write_text("gene\tGSM1\tGSM2\tGSM3\tGSM4\nTP53\t1\t2\t3\t4\n", encoding="utf-8")
    samples.write_text("sample_id\tcondition\nGSM1\tcontrol\nGSM2\tcontrol\nGSM3\ttreated\nGSM4\ttreated\n", encoding="utf-8")
    workflow_pages.run_project_recognition(project_summary.project_root)
    workflow_pages.run_project_readiness(project_summary.project_root)

    readiness = BioinformaticsReadinessDashboardWidget()
    readiness.refresh_project(project_summary)
    table = readiness.findChild(QTableWidget, "readinessCapabilityTable")
    row_text = " ".join(table.item(0, column).text() for column in range(table.columnCount()))
    assert "候选分组待确认" in row_text
    assert not readiness.findChild(QFrame, "readinessTodo_comparison_config").isHidden()

    assert readiness.confirm_group_preview_as_comparison(skip_dialog=True) is True

    comparison_file = project_summary.project_root / "raw_data" / "local_import" / "manual_supplements" / "comparison_config_manual.tsv"
    audit_log = project_summary.project_root / "logs" / "readiness" / "comparison_group_confirmation_log.jsonl"
    artifacts = workflow_pages.load_readiness_artifacts(project_summary.project_root)
    assert comparison_file.exists()
    assert audit_log.exists()
    assert "condition" in comparison_file.read_text(encoding="utf-8")
    assert "comparison_config" in artifacts["readiness_report"]["available_inputs"]
    assert "已确认候选分组" in readiness.status_message()


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
    assert readiness.supplement_missing_info("comparison_config", mode="manual", manual_text="comparison_id\tgroup_column\tcase_group\tcontrol_group\ncase_vs_control\tgroup\tcase\tcontrol\n") is True

    manual_file = project_summary.project_root / "raw_data" / "local_import" / "manual_supplements" / "sample_metadata_manual.tsv"
    comparison_file = project_summary.project_root / "raw_data" / "local_import" / "manual_supplements" / "comparison_config_manual.tsv"
    assert manual_file.exists()
    assert comparison_file.exists()
    artifacts = readiness.save_and_rerun_readiness()
    assert artifacts is not None
    report = artifacts["readiness_report"]
    assert isinstance(report, dict)
    assert report["has_core_input"] is True
    assert "comparison_config" in report["available_inputs"]
    assert "已重新检查" in readiness.status_message()


def test_analysis_task_center_can_save_comparison_groups(qt_app, project_summary, tmp_path: Path) -> None:
    expression_file = tmp_path / "expression_matrix.tsv"
    expression_file.write_text("gene\ts1\ts2\nTP53\t1\t2\n", encoding="utf-8")
    sample_file = tmp_path / "sample_metadata.tsv"
    sample_file.write_text("sample_id\tgroup\ns1\tcase\ns2\tcontrol\n", encoding="utf-8")
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="local_import",
        source_label="expression",
        strategy="copy",
        selected_paths=[expression_file, sample_file],
    )
    workflow_pages.run_project_recognition(project_summary.project_root)
    workflow_pages.run_project_readiness(project_summary.project_root)

    task_center = BioinformaticsAnalysisTaskCenterWidget()
    task_center.refresh_project(project_summary)

    assert task_center.configure_comparison_groups(
        "comparison_id\tgroup_column\tcase_group\tcontrol_group\ncase_vs_control\tgroup\tcase\tcontrol\n"
    ) is True
    assert "已保存比较组设置" in task_center.status_message()
    artifacts = workflow_pages.load_readiness_artifacts(project_summary.project_root)
    report = artifacts["readiness_report"]
    assert isinstance(report, dict)
    assert "comparison_config" in report["available_inputs"]


def test_analysis_task_center_runs_geo_differential_expression_and_indexes_results(qt_app, project_summary, tmp_path: Path) -> None:
    expression_file = tmp_path / "GSETEST_expression_matrix.tsv"
    expression_file.write_text(
        "gene\tcase_1\tcase_2\tcontrol_1\tcontrol_2\n"
        "TP53\t10\t12\t2\t3\n"
        "EGFR\t4\t5\t9\t10\n",
        encoding="utf-8",
    )
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="geo_accession",
        source_label="GSETEST",
        strategy="reference",
        selected_paths=[expression_file],
        metadata={"source": "geo", "accession_or_project": "GSETEST", "ready_for_recognition": "ready"},
    )
    workflow_pages.run_project_recognition(project_summary.project_root)
    workflow_pages.run_project_readiness(project_summary.project_root)
    workflow_pages.generate_standardized_assets(project_summary.project_root)

    task_center = BioinformaticsAnalysisTaskCenterWidget()
    task_center.refresh_project(project_summary)
    result = task_center.run_geo_differential_expression_task()

    assert result is not None
    assert result["summaries"]
    index = workflow_pages.load_result_index(project_summary.project_root)
    entries = index["entries"]
    assert any(item["analysis_type"] == "differential_expression" for item in entries)
    assert "已运行 GEO 差异分析" in task_center.status_message()


def test_geo_profile_display_uses_user_facing_comparison_and_download_categories(qt_app) -> None:
    from app.bioinformatics.services.geo_metadata_profile_service import (
        GeoCandidateComparison,
        GeoMetadataProfile,
        GeoSampleGroupAssignment,
        GeoSupplementaryFile,
    )

    profile = GeoMetadataProfile(
        accession="GSETEST",
        analysis_potential_level="高",
        analysis_potential_reason="sample-level metadata supports tumor/normal grouping",
        geo_sample_count=4,
        metadata_sample_count=4,
        sample_structure_preview={"sample_types": {"tumor": 2, "normal": 2}},
        candidate_comparisons=(
            GeoCandidateComparison(
                comparison_id="pathological_diagnostic:tumor_vs_normal",
                label="tumor vs normal",
                control_group="normal",
                case_group="tumor",
                group_sizes={"normal": 2, "tumor": 2},
                sample_assignments=(
                    GeoSampleGroupAssignment("GSM1", "normal", "pathological_diagnostic", "diagnosis: normal", "high"),
                    GeoSampleGroupAssignment("GSM2", "tumor", "pathological_diagnostic", "diagnosis: tumor", "high"),
                ),
                confidence="high",
            ),
        ),
        supplementary_file_preview=(
            GeoSupplementaryFile("GSETEST_family.soft.gz", predicted_type="metadata_container", asset_type="family_soft", recommendation="元数据容器，用于读取标题、样本和平台信息。"),
            GeoSupplementaryFile("GSETEST_series_matrix.txt.gz", predicted_type="expression_matrix", asset_type="series_matrix", recommendation="建议优先查看，可能包含表达矩阵。"),
            GeoSupplementaryFile("GSETEST_RAW.tar", predicted_type="raw_data", risk_level="高", recommendation="文件较大，建议确认后下载。"),
        ),
    )

    text = workflow_pages._geo_profile_user_display(profile)

    assert "候选比较组：肿瘤组 vs 正常/对照组" in text
    assert "样本数：正常/对照组 2 个，肿瘤组 2 个" in text
    assert "判断依据：样本注释中的病理诊断信息" in text
    assert "推荐下载：元数据/样本注释" in text
    assert "可能用于分析：表达矩阵或标准化表达文件" in text
    assert "可能包含表达矩阵或样本注释，需下载后确认" in text
    assert "不建议默认下载：raw/CEL/大文件/SRA 原始数据" in text


def test_geo_profile_confirmation_writes_formal_comparison_and_audit(qt_app, project_summary, monkeypatch) -> None:
    from app.bioinformatics.services.geo_metadata_profile_service import (
        GeoCandidateComparison,
        GeoMetadataProfile,
        GeoSampleGroupAssignment,
    )

    profile = GeoMetadataProfile(
        accession="GSETEST",
        candidate_comparisons=(
            GeoCandidateComparison(
                comparison_id="pathological_diagnostic:tumor_vs_normal",
                label="tumor vs normal",
                control_group="normal",
                case_group="tumor",
                group_sizes={"normal": 2, "tumor": 2},
                sample_assignments=(
                    GeoSampleGroupAssignment("GSM1", "normal", "pathological_diagnostic", "diagnosis: normal", "high"),
                    GeoSampleGroupAssignment("GSM2", "normal", "pathological_diagnostic", "diagnosis: normal", "high"),
                    GeoSampleGroupAssignment("GSM3", "tumor", "pathological_diagnostic", "diagnosis: tumor", "high"),
                    GeoSampleGroupAssignment("GSM4", "tumor", "pathological_diagnostic", "diagnosis: tumor", "high"),
                ),
                confidence="high",
            ),
        ),
    )
    monkeypatch.setattr(workflow_pages, "_build_geo_detail_profile", lambda *args, **kwargs: profile)
    candidate = SimpleNamespace(accession_or_project="GSETEST")

    ok, message = workflow_pages._save_geo_profile_comparison_with_confirmation(
        BioinformaticsDataSourceWidget(),
        project_summary.project_root,
        candidate,
        None,
        included_sample_ids=["GSM1", "GSM3", "GSM4"],
        assignment_overrides={"GSM4": "normal"},
        skip_dialog=True,
    )

    comparison_file = project_summary.project_root / "raw_data" / "local_import" / "manual_supplements" / "comparison_config_manual.tsv"
    audit_log = project_summary.project_root / "logs" / "readiness" / "comparison_group_confirmation_log.jsonl"
    text = comparison_file.read_text(encoding="utf-8")

    assert ok is True
    assert "正式比较组" in message
    assert comparison_file.exists()
    assert audit_log.exists()
    assert "sample_accession\tassigned_group\tinclude" in text
    assert "GSM2\tnormal\tno" in text
    assert "GSM4\tnormal\tyes" in text


def test_readiness_reports_confirmed_comparison_and_sample_match(qt_app, project_summary) -> None:
    expression = project_summary.project_root / "raw_data" / "local_import" / "expression.tsv"
    expression.parent.mkdir(parents=True, exist_ok=True)
    expression.write_text("gene\tGSM1\tGSM2\tGSM3\tGSM4\nTP53\t1\t2\t8\t9\n", encoding="utf-8")
    workflow_pages._save_manual_supplement(
        project_summary.project_root,
        "comparison_config",
        "comparison_id\tgroup_column\tcase_group\tcontrol_group\tcase_label_zh\tcontrol_label_zh\n"
        "tumor_vs_normal\tpathological_diagnostic\ttumor\tnormal\t肿瘤组\t正常/对照组\n\n"
        "sample_accession\tassigned_group\tinclude\tevidence_field\tevidence_text\tconfidence\n"
        "GSM1\tnormal\tyes\tpathological_diagnostic\tdiagnosis: normal\thigh\n"
        "GSM2\tnormal\tyes\tpathological_diagnostic\tdiagnosis: normal\thigh\n"
        "GSM3\ttumor\tyes\tpathological_diagnostic\tdiagnosis: tumor\thigh\n"
        "GSM4\ttumor\tyes\tpathological_diagnostic\tdiagnosis: tumor\thigh\n",
    )
    workflow_pages.run_project_recognition(project_summary.project_root)
    artifacts = workflow_pages.run_project_readiness(project_summary.project_root)
    readiness = BioinformaticsReadinessDashboardWidget()
    readiness._render(artifacts)

    labels = "\n".join(label.text() for label in readiness.findChildren(QLabel))
    table = readiness.findChild(QTableWidget, "readinessCapabilityTable")
    row_text = " ".join(table.item(0, column).text() for column in range(table.columnCount()))

    assert "比较组已确认：肿瘤组 2 个 vs 正常/对照组 2 个" in labels
    assert "可继续" in row_text


def test_analysis_task_center_uses_confirmed_geo_assignments(qt_app, project_summary, tmp_path: Path) -> None:
    expression_file = tmp_path / "GSETEST_expression_matrix.tsv"
    expression_file.write_text(
        "gene\tGSM1\tGSM2\tGSM3\tGSM4\n"
        "TP53\t2\t3\t10\t12\n"
        "EGFR\t9\t10\t4\t5\n",
        encoding="utf-8",
    )
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="geo_accession",
        source_label="GSETEST",
        strategy="reference",
        selected_paths=[expression_file],
        metadata={"source": "geo", "accession_or_project": "GSETEST", "ready_for_recognition": "ready"},
    )
    workflow_pages._save_manual_supplement(
        project_summary.project_root,
        "comparison_config",
        "comparison_id\tgroup_column\tcase_group\tcontrol_group\tcase_label_zh\tcontrol_label_zh\n"
        "tumor_vs_normal\tpathological_diagnostic\ttumor\tnormal\t肿瘤组\t正常/对照组\n\n"
        "sample_accession\tassigned_group\tinclude\tevidence_field\tevidence_text\tconfidence\n"
        "GSM1\tnormal\tyes\tpathological_diagnostic\tdiagnosis: normal\thigh\n"
        "GSM2\tnormal\tyes\tpathological_diagnostic\tdiagnosis: normal\thigh\n"
        "GSM3\ttumor\tyes\tpathological_diagnostic\tdiagnosis: tumor\thigh\n"
        "GSM4\ttumor\tyes\tpathological_diagnostic\tdiagnosis: tumor\thigh\n",
    )
    workflow_pages.run_project_recognition(project_summary.project_root)
    workflow_pages.run_project_readiness(project_summary.project_root)
    workflow_pages.generate_standardized_assets(project_summary.project_root)

    task_center = BioinformaticsAnalysisTaskCenterWidget()
    task_center.refresh_project(project_summary)
    result = task_center.run_geo_differential_expression_task()

    assert result is not None
    summary = result["summaries"][0]
    assert summary["parameters"]["explicit_group_assignments_used"] is True
    assert summary["case_label"] == "tumor"
    assert summary["control_label"] == "normal"


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
                "recognized_type": "geo_soft_container",
                "recognized_type_zh": "GEO SOFT 容器",
                "recognized_roles": ["expression_matrix", "sample_metadata"],
                "detected_assets": [
                    {"asset_type": "expression_matrix", "label_zh": "表达矩阵", "reason": "SOFT sample table 包含表达值。"},
                    {"asset_type": "sample_metadata", "label_zh": "样本注释", "reason": "SOFT 包含 SAMPLE 块。"},
                ],
                "confidence": 0.7,
                "file_size": 5763709,
                "reason": "GEO family SOFT 容器，检测到表达矩阵和样本注释。",
                "warning": "",
                "route_path": str(project_summary.project_root / "recognized_data/expression_matrix/GSE54350_series_matrix.txt"),
            }
        ],
    )
    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)
    report = json.loads((project_summary.project_root / "logs" / "recognition" / "recognition_report.json").read_text(encoding="utf-8"))
    widget._render_report(report)
    table = widget.findChild(QTableWidget, "recognitionResultTable")

    assert table.horizontalHeaderItem(3).text() == "识别可信度"
    assert "不是数据质量评分" in table.horizontalHeaderItem(3).toolTip()
    assert table.item(0, 3).text() == "70%"
    assert table.item(0, 4).text() == "5.5 MB"
    assert table.item(0, 1).text().startswith("...")
    assert table.horizontalHeaderItem(1).text() == "当前位置"
    assert table.item(0, 1).toolTip() == str(project_summary.project_root / "recognized_data/expression_matrix/GSE54350_series_matrix.txt")
    assert table.item(0, 2).text() == "GEO SOFT 容器（含：表达矩阵、样本注释）"
    assert "可用角色：表达矩阵、样本注释" in table.item(0, 2).toolTip()
    assert "原始 bytes：5763709" in table.item(0, 4).toolTip()


def test_recognition_refresh_does_not_call_backend_but_rerun_does(qt_app, project_summary, monkeypatch) -> None:
    source = project_summary.project_root / "raw_data" / "local_import" / "expression.tsv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="local_import",
        source_label="expression.tsv",
        strategy="reference",
        selected_paths=[source],
    )
    _write_mock_recognition_report(project_summary.project_root, [])
    calls: list[str] = []
    monkeypatch.setattr(
        workflow_pages,
        "run_project_recognition_for_paths",
        lambda root, paths, skipped_unselected_count=0: calls.append((str(root), tuple(paths), skipped_unselected_count))
        or {"files": [], "warnings": [], "type_counts": {}, "selected_inputs": list(paths), "selected_input_count": len(paths), "skipped_unselected_count": skipped_unselected_count},
    )
    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)

    widget.refresh_report()
    assert calls == []
    assert "尚未开始本次识别" in widget.status_message()

    table = widget.findChild(QTableWidget, "preRecognitionInputList")
    checkbox = table.cellWidget(0, 0)
    assert checkbox is not None
    checkbox.setChecked(True)
    widget.run_recognition()
    assert calls == [(str(project_summary.project_root), (str(source),), 0)]
    assert "本次只识别已勾选的数据" in widget.status_message()


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
    report = json.loads((root / "logs" / "recognition" / "recognition_report.json").read_text(encoding="utf-8"))
    widget._render_report(report)
    table = widget.findChild(QTableWidget, "recognitionResultTable")

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
    assert "GEO query draft" in terms
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
