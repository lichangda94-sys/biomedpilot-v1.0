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
    from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QPushButton, QFrame, QScrollArea, QTableWidget

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
    payload = widget._generate_gse_geo_summary(candidate)

    assert payload is not None
    text = widget._gse_geo_detail_panel._translation_text.toPlainText()
    assert "该数据集比较胶质瘤和对照样本。" in text
    assert "与检索主题匹配：是" in text
    assert "推荐等级：" in text
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

    summary = widget._add_history_cache_to_project({"name": "GSE99999", "path": str(cache_dir)})

    assert summary is not None
    assert widget._dataset_list_panel._table.rowCount() == 1
    assert widget._dataset_list_panel._table.item(0, 1).text() == "本地导入"


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
    assert "检索 GEO/GSE 候选数据集" in button_texts
    assert "检索 TCGA/GDC 项目" in button_texts
    assert "检索 GTEx 组织" in button_texts
    assert "查看完整检索词" in button_texts
    assert "检索候选数据集" not in button_texts
    assert "GEO/GSE" == widget._tabs.tabText(0)
    assert "TCGA/GDC" == widget._tabs.tabText(1)
    assert "GTEx" == widget._tabs.tabText(2)
    assert widget._continue_button.text() == "下一步：进入数据识别"

    widget.set_query_text("甲状腺癌")
    result = widget.generate_terms()

    assert result is not None
    assert widget.status_message() == "已生成检索草稿。请确认后检索候选数据集。"
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
    assert "创建下载任务" in tcga_card
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
    assert "创建下载任务" in gtex_card
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
    record = json.loads(summary.record_path.read_text(encoding="utf-8"))
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
    assert widget.status_message() == "已生成下载任务，等待下载数据文件。"
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
    assert widget.status_message() == "已生成中文翻译与一句话简介。"
    assert widget._mapping_log.isHidden()
    assert not widget._geo_dataset_detail_panel.isHidden()
    text = widget._geo_dataset_detail_panel._translation_text.toPlainText()
    assert "该数据集比较胶质瘤和对照样本。" in text
    assert "与检索主题匹配：是" in text
    assert "推荐等级：" in text
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

    assert "与检索主题匹配：可能相关" in text
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
    assert table.item(0, 0).text() == "GEO/GSE 数据来源"
    assert table.item(0, 1).text() == "GSE33630"
    assert table.item(0, 2).text() == "GEO"
    assert table.item(0, 3).text() == "待下载"


def test_geo_source_registration_does_not_auto_download_or_analyze(qt_app, project_summary) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    candidate = _geo_candidate()
    widget._candidates = {("geo", "GSE33630"): candidate}
    summary = widget.register_candidate("geo", "GSE33630")

    assert summary is not None
    assert not (project_summary.project_root / "raw_data" / "geo" / "GSE33630").exists()
    assert list((project_summary.project_root / "analysis").glob("**/*")) == []
    record = json.loads(summary.record_path.read_text(encoding="utf-8"))
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
    assert table.item(0, 0).text() == "TCGA/GDC 项目"
    assert table.item(0, 1).text() == "TCGA-THCA"
    record = json.loads(summary.record_path.read_text(encoding="utf-8"))
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
    assert not widget._continue_button.isEnabled()
    assert not (project_summary.project_root / "raw_data" / "gtex" / "GTEX-THYROID").exists()

    record = json.loads(summary.record_path.read_text(encoding="utf-8"))
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
    assert table.item(0, 1).text() == "GSE33630"


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
    assert not readiness._comparison_file_button.isHidden()
    assert not readiness._comparison_manual_button.isHidden()
    assert not readiness._comparison_template_button.isHidden()
    assert readiness._expression_file_button.isHidden()

    template = readiness.create_missing_info_template("sample_metadata")
    assert template is not None
    assert template.exists()
    assert "sample_id" in template.read_text(encoding="utf-8")
    comparison_template = readiness.create_missing_info_template("comparison_config")
    assert comparison_template is not None
    assert "case_group" in comparison_template.read_text(encoding="utf-8")


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
    table = widget.findChild(QTableWidget)

    assert table.horizontalHeaderItem(3).text() == "识别可信度"
    assert "不是数据质量评分" in table.horizontalHeaderItem(3).toolTip()
    assert table.item(0, 3).text() == "70%"
    assert table.item(0, 4).text() == "5.5 MB"
    assert table.item(0, 1).text().startswith("...")
    assert table.item(0, 1).toolTip() == str(long_path)
    assert table.item(0, 2).text() == "GEO SOFT 容器（含：表达矩阵、样本注释）"
    assert "可用角色：表达矩阵、样本注释" in table.item(0, 2).toolTip()
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
    assert "已重新扫描当前项目数据和已选择的外部引用文件" in widget.status_message()


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
