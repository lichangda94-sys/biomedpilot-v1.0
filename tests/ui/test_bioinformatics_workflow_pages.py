from __future__ import annotations

import os
import json
import gzip
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from xml.sax.saxutils import escape

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QCheckBox, QHeaderView, QLabel, QPlainTextEdit, QPushButton, QFrame, QScrollArea, QTableWidget, QTextEdit

    from app.bioinformatics.comparison_config import ComparisonSampleAssignment, build_comparison_config_text, comparison_config_path
    from app.bioinformatics.deg_engine.confirmation import CONFIRMATION_PATH, CONFIRMATION_SCHEMA_VERSION
    from app.bioinformatics.plots import create_formal_deg_plot_artifact
    from app.bioinformatics.project_workspace import create_bioinformatics_project
    from app.bioinformatics.results.models import ResultIndexEntry
    from app.bioinformatics.results.project_results import write_result_index
    from app.bioinformatics.results.registry import register_result
    import app.bioinformatics.project_recognition as project_recognition
    import app.bioinformatics.workflow_pages as workflow_pages
    from app.bioinformatics.workflow_pages import (
        BioinformaticsAcquisitionStatusWidget,
        BioinformaticsAnalysisTaskCenterWidget,
        BioinformaticsChineseDatasetSearchWidget,
        BioinformaticsDataSourceWidget,
        BioinformaticsDegConfigWidget,
        GseaGeneSetResourceManagerDialog,
        BioinformaticsImportedDegBrowserWidget,
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
    QPlainTextEdit = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


def _table_text(table: QTableWidget) -> str:
    values: list[str] = []
    for row in range(table.rowCount()):
        for column in range(table.columnCount()):
            item = table.item(row, column)
            if item is not None:
                values.append(item.text())
    return "\n".join(values)


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


def _write_gmt(path: Path) -> Path:
    path.write_text(
        "CUSTOM_ALPHA\tna\tTP53\tBAX\tCASP3\nCUSTOM_BETA\tna\tSTAT1\tIRF1\n",
        encoding="utf-8",
    )
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


def _write_geo_candidate_manifest(root: Path, accession: str = "GSE33630") -> Path:
    geo_dir = root / "raw_data" / "geo" / accession
    geo_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "biomedpilot.geo_asset_manifest.v1",
        "accession": accession,
        "assets": [
            {
                "asset_type": "family_soft",
                "role": "metadata_container",
                "file_name": f"{accession}_family.soft.gz",
                "status": "downloaded",
                "local_path": str(geo_dir / f"{accession}_family.soft.gz"),
                "remote_url": f"https://example.org/{accession}_family.soft.gz",
            },
            {
                "asset_type": "series_matrix",
                "role": "expression_matrix_candidate",
                "file_name": f"{accession}-GPL570_series_matrix.txt.gz",
                "status": "remote_discovered",
                "remote_url": f"https://example.org/{accession}-GPL570_series_matrix.txt.gz",
            },
            {
                "asset_type": "supplementary_file",
                "role": "supplementary_expression_candidate",
                "file_name": f"{accession}_counts.tsv.gz",
                "status": "remote_discovered",
                "remote_url": f"https://example.org/{accession}_counts.tsv.gz",
            },
            {
                "asset_type": "supplementary_file",
                "role": "supplementary_annotation_candidate",
                "file_name": "GPL570_probe_annotation.txt.gz",
                "status": "remote_discovered",
                "remote_url": "https://example.org/GPL570_probe_annotation.txt.gz",
            },
            {
                "asset_type": "supplementary_file",
                "role": "supplementary_file",
                "file_name": f"{accession}_DEG_results.xlsx",
                "status": "remote_discovered",
                "remote_url": f"https://example.org/{accession}_DEG_results.xlsx",
            },
            {
                "asset_type": "supplementary_file",
                "role": "supplementary_file",
                "file_name": f"{accession}_RAW.tar",
                "status": "remote_discovered",
                "remote_url": f"https://example.org/{accession}_RAW.tar",
                "size_bytes": 2_000_000_000,
            },
        ],
        "summary": {"metadata_downloaded": True, "series_matrix_discovered": True, "supplementary_files_discovered": True},
    }
    path = geo_dir / f"{accession}_asset_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return path


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
        BioinformaticsDegConfigWidget(),
        BioinformaticsImportedDegBrowserWidget(),
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
        "bioinformaticsDegConfigPage",
        "bioinformaticsImportedDegBrowserPage",
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


def test_data_source_page_shows_four_primary_source_entries(qt_app) -> None:
    widget = BioinformaticsDataSourceWidget()
    card_titles = [
        label.text()
        for label in widget.findChildren(QLabel, "bioProjectCardTitle")
        if label.text() not in {"GEO 数据集详情", "下载列表 / 待处理数据来源", "当前数据选择状态", "历史缓存数据", "数据详情"}
    ]
    button_texts = [button.text() for button in widget.findChildren(QPushButton)]
    inputs = widget.findChildren(workflow_pages.QLineEdit)
    visible_text = " ".join(
        [label.text() for label in widget.findChildren(QLabel)]
        + [button.text() for button in widget.findChildren(QPushButton)]
        + [input_box.placeholderText() for input_box in inputs]
    )

    assert "选择数据来源" in card_titles
    assert "GEO 数据库" in card_titles
    assert "TCGA 数据库" in card_titles
    assert "GTEx 数据库" in card_titles
    assert "本地数据导入" in card_titles
    assert "按 GSE 编号检索/下载" in card_titles
    assert "按中文研究问题检索 GEO 数据集" in card_titles
    assert "GEO Series Matrix 文件" not in card_titles
    assert "TCGA 本地数据" not in card_titles
    assert "GTEx 本地数据" not in card_titles
    assert "TCGA + GTEx 联合数据" not in card_titles
    assert "本地 AI 检索助手" not in card_titles
    assert {"GEO 数据库", "TCGA 数据库", "GTEx 数据库", "本地数据导入"} <= set(card_titles)
    assert {"进入", "预览可下载数据", "生成下载计划草案"} <= set(button_texts)
    assert "选择本地文件或文件夹" in button_texts
    assert "选择本地数据" not in button_texts
    assert "选择本地文件夹" not in button_texts
    assert "检索" in button_texts
    assert "检索数据集" not in button_texts
    assert "进入中文主题检索" in button_texts
    assert any(input_box.placeholderText() == "请输入 GSE 编号，例如 GSE60235" for input_box in inputs)
    assert any(input_box.placeholderText() == "请输入研究方向，例如：甲状腺癌与肥胖相关基因表达数据" for input_box in inputs)
    assert "选择文件" not in button_texts
    assert "选择文件夹" not in button_texts
    assert "登记为数据源" not in button_texts
    assert "PubMed" not in visible_text
    assert widget.findChild(QLabel, "dataSelectionSavedCount").text() == "已保存数据来源：0 个"
    assert widget.findChild(QLabel, "dataSelectionDownloadCount").text() == "下载列表 / 待处理：0 个"
    assert widget.findChild(QLabel, "dataSelectionReadyCount").text() == "可进入数据检查：0 个"
    assert "下一步" in widget.findChild(QLabel, "dataSelectionNextStep").text()


def test_data_source_tcga_workflow_initial_state_shows_five_steps_and_only_preview(qt_app, project_summary) -> None:
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    table = widget.findChild(QTableWidget, "tcgaWorkflowStepsTable")
    text = _table_text(table)

    assert table.rowCount() == 5
    assert "1. 预览可下载数据" in text
    assert "2. 下载 TCGA 原始文件" in text
    assert "3. 构建 TCGA 表达矩阵" in text
    assert "4. 获取 TCGA 临床信息" in text
    assert "5. 进入数据检查与准备" in text
    assert widget.findChild(QPushButton, "previewTcgaDownloadableDataButton").isEnabled()
    assert widget.findChild(QPushButton, "downloadTcgaRawFilesButton").isEnabled() is False
    assert widget.findChild(QPushButton, "buildTcgaExpressionMatrixButton").isEnabled() is False
    assert widget.findChild(QPushButton, "fetchTcgaClinicalMetadataButton").isEnabled() is False
    assert widget.findChild(QPushButton, "enterTcgaDataCheckButton").isEnabled() is False
    assert widget.findChild(QPlainTextEdit, "tcgaMetadataPreviewDeveloperDiagnostics").isVisible() is False
    main_text = widget.findChild(QPlainTextEdit, "tcgaWorkflowSummary").toPlainText()
    assert "file uuid" not in main_text.lower()
    assert "raw path" not in main_text.lower()
    assert "GDC filter" not in main_text


def test_data_source_tcga_request_is_pending_not_ready(qt_app, project_summary) -> None:
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    summary = widget.create_tcga_source_request()

    assert summary is not None
    assert summary.source_type == "tcga_project"
    assert summary.strategy == "plan_only"
    assert summary.source_files == ()
    assert "不会执行虚假下载" in widget.status_message()
    request_index = project_summary.project_root / "manifests" / "data_source_requests.json"
    payload = json.loads(request_index.read_text(encoding="utf-8"))
    assert payload["requests"][-1]["source_type"] == "TCGA"
    assert payload["requests"][-1]["actual_assets"] == []
    assert workflow_pages._ready_registered_source_count(project_summary.project_root) == 0
    entries = workflow_pages._current_project_dataset_entries(project_summary.project_root)
    assert entries[0].source == "TCGA 数据库"
    assert entries[0].status == "等待下载与构建"
    assert entries[0].ready_for_recognition is False


def test_data_source_tcga_metadata_preview_and_plan_draft(qt_app, project_summary, monkeypatch) -> None:
    class FakeTcgaPreviewService:
        def build_preview(self, request):
            from app.bioinformatics.data_sources.tcga_preview import TCGAPreviewSummary

            return TCGAPreviewSummary(
                request=request,
                status="ready",
                case_count=2,
                sample_count=2,
                file_count=2,
                estimated_size_bytes=3 * 1024 * 1024,
                size_has_unknown=False,
                sample_type_counts={"Primary Tumor": 2},
                access_counts={"open": 2},
                workflow_type_counts={"STAR - Counts": 2},
                data_format_counts={"TSV": 2},
                warnings=("本阶段仅预览可下载数据。",),
                is_download_plan_available=True,
                gdc_filters={"op": "and", "content": []},
                case_filters={"op": "and", "content": []},
                selected_file_ids_preview=("file-1", "file-2"),
                files_fetched=2,
                cases_fetched=2,
                files_total=2,
                cases_total=2,
                file_manifest_entries=(
                    {"file_id": "file-1", "file_name": "file-1.tsv", "file_size": 8, "access": "open", "data_type": "Gene Expression Quantification", "data_format": "TSV"},
                    {"file_id": "file-2", "file_name": "file-2.tsv", "file_size": 8, "access": "open", "data_type": "Gene Expression Quantification", "data_format": "TSV"},
                ),
            )

    widget = BioinformaticsDataSourceWidget()
    widget._tcga_preview_service = FakeTcgaPreviewService()
    widget.refresh_project(project_summary)

    summary = widget.preview_tcga_downloadable_data()
    acquisition = widget.create_tcga_download_plan_draft()

    assert summary is not None
    assert acquisition is not None
    assert acquisition.strategy == "plan_only"
    assert acquisition.source_files == ()
    assert "未写 source_files" in widget.status_message()
    assert widget.findChild(QPushButton, "createTcgaDownloadPlanDraftButton").isEnabled()
    assert "case 数：2" in widget.findChild(QPlainTextEdit, "tcgaMetadataPreviewSummary").toPlainText()
    assert "STAR - Counts 2" in widget.findChild(QPlainTextEdit, "tcgaMetadataPreviewSummary").toPlainText()
    assert widget.findChild(QPlainTextEdit, "tcgaMetadataPreviewDeveloperDiagnostics").isVisible() is False
    workflow_text = _table_text(widget.findChild(QTableWidget, "tcgaWorkflowStepsTable"))
    assert "1. 预览可下载数据" in workflow_text
    assert "已完成" in workflow_text
    assert "下载 TCGA 原始文件" in workflow_text
    assert widget.findChild(QPushButton, "downloadTcgaRawFilesButton").isEnabled()
    request_index = project_summary.project_root / "manifests" / "data_source_requests.json"
    payload = json.loads(request_index.read_text(encoding="utf-8"))
    assert payload["requests"][-1]["status"] == "download_plan_draft"
    assert payload["requests"][-1]["actual_assets"] == []
    plan_path = Path(payload["requests"][-1]["internal_selection"]["download_plan_draft_path"])
    assert plan_path.is_file()
    plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan_payload["status"] == "draft_only"
    assert len(plan_payload["file_manifest_entries"]) == 2
    assert plan_payload["constraints"]["writes_source_files"] is False
    assert "source_files" not in plan_payload
    assert workflow_pages._ready_registered_source_count(project_summary.project_root) == 0
    entries = workflow_pages._current_project_dataset_entries(project_summary.project_root)
    assert entries[0].source == "TCGA 数据库"
    assert entries[0].status == "等待下载与构建"
    assert entries[0].available_content == "下载计划草案"
    assert entries[0].ready_for_recognition is False


def test_data_source_tcga_raw_download_ui_registers_files_but_not_ready(qt_app, project_summary) -> None:
    from app.bioinformatics.data_sources.tcga_download_executor import TCGADownloadPlanExecutor

    class FakeTcgaPreviewService:
        def build_preview(self, request):
            from app.bioinformatics.data_sources.tcga_preview import TCGAPreviewSummary

            return TCGAPreviewSummary(
                request=request,
                status="ready",
                case_count=1,
                sample_count=1,
                file_count=1,
                estimated_size_bytes=8,
                size_has_unknown=False,
                sample_type_counts={"Primary Tumor": 1},
                access_counts={"open": 1},
                workflow_type_counts={"STAR - Counts": 1},
                data_format_counts={"TSV": 1},
                warnings=(),
                is_download_plan_available=True,
                gdc_filters={"op": "and", "content": []},
                case_filters={"op": "and", "content": []},
                selected_file_ids_preview=("file-1",),
                files_fetched=1,
                cases_fetched=1,
                files_total=1,
                cases_total=1,
                file_manifest_entries=(
                    {"file_id": "file-1", "file_name": "file-1.tsv", "file_size": 8, "access": "open", "data_type": "Gene Expression Quantification", "data_format": "TSV"},
                ),
            )

    class FakeGdcDownloader:
        def download_file(self, entry, target_dir):
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / str(entry["file_name"])
            target.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
            return {
                "status": "success",
                "cache_hit": False,
                "local_path": str(target),
                "bytes_downloaded": target.stat().st_size,
                "source_url": f"https://api.gdc.cancer.gov/data/{entry['file_id']}",
                "sha256": "fake",
            }

    widget = BioinformaticsDataSourceWidget()
    widget._tcga_preview_service = FakeTcgaPreviewService()
    widget._tcga_download_executor = TCGADownloadPlanExecutor(downloader=FakeGdcDownloader())
    widget.refresh_project(project_summary)

    assert widget.findChild(QPushButton, "downloadTcgaRawFilesButton").isEnabled() is False
    assert widget.download_tcga_raw_files() is None
    assert "未找到 TCGA 下载计划草案" in widget.findChild(QPlainTextEdit, "tcgaRawDownloadStatus").toPlainText()

    widget.preview_tcga_downloadable_data()
    widget.create_tcga_download_plan_draft()
    assert widget.findChild(QPushButton, "downloadTcgaRawFilesButton").isEnabled() is True
    result = widget.download_tcga_raw_files()

    assert result is not None
    assert result.status == "tcga_gdc_raw_files_acquired"
    status_text = widget.findChild(QPlainTextEdit, "tcgaRawDownloadStatus").toPlainText()
    assert "成功：1" in status_text
    assert "本地缓存路径" in status_text
    assert "receipt" in status_text
    workflow_text = _table_text(widget.findChild(QTableWidget, "tcgaWorkflowStepsTable"))
    assert "3. 构建 TCGA 表达矩阵" in workflow_text
    assert widget.findChild(QPushButton, "buildTcgaExpressionMatrixButton").isEnabled()
    assert workflow_pages._ready_registered_source_count(project_summary.project_root) == 0
    entries = workflow_pages._current_project_dataset_entries(project_summary.project_root)
    assert entries[0].source == "TCGA 数据库"
    assert entries[0].status == "TCGA 原始文件已获取，等待 B6.4 构建表达矩阵"
    assert entries[0].available_content == "TCGA 原始文件：1 个"
    assert entries[0].missing_content == "B6.4 表达矩阵构建"
    assert entries[0].ready_for_recognition is False
    assert widget.findChild(QLabel, "dataSelectionReadyCount").text() == "可进入数据检查：0 个"


def test_data_source_tcga_expression_build_ui_waits_for_data_check(qt_app, project_summary) -> None:
    from app.bioinformatics.data_sources.tcga_download_executor import TCGADownloadPlanExecutor

    class FakeTcgaPreviewService:
        def build_preview(self, request):
            from app.bioinformatics.data_sources.tcga_preview import TCGAPreviewSummary

            return TCGAPreviewSummary(
                request=request,
                status="ready",
                case_count=1,
                sample_count=1,
                file_count=1,
                estimated_size_bytes=8,
                size_has_unknown=False,
                sample_type_counts={"Primary Tumor": 1},
                access_counts={"open": 1},
                workflow_type_counts={"STAR - Counts": 1},
                data_format_counts={"TSV": 1},
                warnings=(),
                is_download_plan_available=True,
                gdc_filters={"op": "and", "content": []},
                case_filters={"op": "and", "content": []},
                selected_file_ids_preview=("file-1",),
                files_fetched=1,
                cases_fetched=1,
                files_total=1,
                cases_total=1,
                file_manifest_entries=(
                    {
                        "file_id": "file-1",
                        "file_name": "file-1.tsv",
                        "file_size": 8,
                        "access": "open",
                        "data_type": "Gene Expression Quantification",
                        "data_format": "TSV",
                        "workflow_type": "STAR - Counts",
                        "case_ids": ["case-1"],
                        "case_submitter_ids": ["TCGA-AA-0001"],
                        "sample_ids": ["sample-1"],
                        "sample_submitter_ids": ["TCGA-AA-0001-01A"],
                        "sample_types": ["Primary Tumor"],
                    },
                ),
            )

    class FakeGdcDownloader:
        def download_file(self, entry, target_dir):
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / str(entry["file_name"])
            target.write_text(
                "\n".join(
                    [
                        "gene_id\tgene_name\tgene_type\tunstranded\ttpm_unstranded\tfpkm_unstranded\tfpkm_uq_unstranded",
                        "ENSG00000141510.18\tTP53\tprotein_coding\t42\t3.4\t1.2\t1.8",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            return {
                "status": "success",
                "cache_hit": False,
                "local_path": str(target),
                "bytes_downloaded": target.stat().st_size,
                "source_url": f"https://api.gdc.cancer.gov/data/{entry['file_id']}",
                "sha256": "fake",
            }

    widget = BioinformaticsDataSourceWidget()
    widget._tcga_preview_service = FakeTcgaPreviewService()
    widget._tcga_download_executor = TCGADownloadPlanExecutor(downloader=FakeGdcDownloader())
    widget.refresh_project(project_summary)

    assert widget.findChild(QPushButton, "buildTcgaExpressionMatrixButton").isEnabled() is False
    widget.preview_tcga_downloadable_data()
    widget.create_tcga_download_plan_draft()
    widget.download_tcga_raw_files()
    assert widget.findChild(QPushButton, "buildTcgaExpressionMatrixButton").isEnabled() is True
    result = widget.build_tcga_expression_matrix()

    assert result is not None
    assert result.sample_count == 1
    assert result.gene_count == 1
    status_text = widget.findChild(QPlainTextEdit, "tcgaExpressionBuildStatus").toPlainText()
    assert "样本：1；基因：1" in status_text
    assert "build manifest" in status_text
    workflow_text = _table_text(widget.findChild(QTableWidget, "tcgaWorkflowStepsTable"))
    assert "4. 获取 TCGA 临床信息" in workflow_text
    assert widget.findChild(QPushButton, "fetchTcgaClinicalMetadataButton").isEnabled()
    assert widget.findChild(QPushButton, "enterTcgaDataCheckButton").isEnabled()
    entries = workflow_pages._current_project_dataset_entries(project_summary.project_root)
    assert entries[0].status == "TCGA 表达矩阵已构建，等待数据检查与准备"
    assert entries[0].missing_content == "统一数据检查与准备"
    assert entries[0].ready_for_recognition is True
    assert widget.findChild(QLabel, "dataSelectionReadyCount").text() == "可进入数据检查：1 个"


def test_data_source_tcga_clinical_metadata_ui_runs_after_expression_build(qt_app, project_summary, monkeypatch, tmp_path: Path) -> None:
    from app.bioinformatics.data_sources.tcga_clinical_builder import TCGAClinicalBuildResult

    manifest = project_summary.project_root / "standardized_data" / "tcga" / "tcga-thca" / "build" / "data_prepared" / "tcga" / "tcga_expression_build_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("{}", encoding="utf-8")
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="tcga_project",
        source_label="TCGA-THCA",
        strategy="reference",
        selected_paths=[manifest],
        metadata={
            "source": "tcga_gdc",
            "project_id": "TCGA-THCA",
            "download_status": "tcga_expression_matrix_built",
            "ready_for_recognition": "pending_data_check",
            "analysis_gate_status": "pending_data_check",
            "tcga_expression_build_manifest_path": str(manifest),
        },
    )
    raw_cases = tmp_path / "tcga_clinical_raw_cases.json"
    case_table = tmp_path / "tcga_clinical_case_table.tsv"
    diagnosis_table = tmp_path / "tcga_clinical_diagnosis_table.tsv"
    followup_table = tmp_path / "tcga_clinical_followup_table.tsv"
    survival_table = tmp_path / "tcga_clinical_survival_table.tsv"
    mapping_table = tmp_path / "tcga_clinical_mapping_table.tsv"
    clinical_manifest = tmp_path / "tcga_clinical_build_manifest.json"
    receipt = tmp_path / "tcga_clinical_receipt.json"
    for path in (raw_cases, case_table, diagnosis_table, followup_table, survival_table, mapping_table, clinical_manifest, receipt):
        path.write_text("", encoding="utf-8")

    class FakeClinicalBuilder:
        def build_for_latest_expression_build(self, project_root, **kwargs):
            return TCGAClinicalBuildResult(
                success=True,
                status="tcga_clinical_metadata_built",
                message="TCGA clinical metadata 已获取：2 个 case；匹配表达 case 2 个，基础 OS 可用 1 个 case；等待数据检查与准备。",
                project_id="TCGA-THCA",
                clinical_build_id="tcga-b66-test",
                mode="expression_matched_cases",
                case_count=2,
                matched_case_count=2,
                matched_sample_count=3,
                survival_case_count=1,
                death_event_count=1,
                raw_cases_path=raw_cases,
                case_table_path=case_table,
                diagnosis_table_path=diagnosis_table,
                followup_table_path=followup_table,
                survival_table_path=survival_table,
                mapping_table_path=mapping_table,
                clinical_manifest_path=clinical_manifest,
                clinical_receipt_path=receipt,
                warnings=("death_event_count_below_warning_threshold_5",),
            )

    monkeypatch.setattr(workflow_pages, "latest_tcga_expression_build_manifest_path", lambda project_root, **kwargs: manifest)
    widget = BioinformaticsDataSourceWidget()
    widget._tcga_project_combo.setCurrentIndex(widget._tcga_project_combo.findData("TCGA-THCA"))
    widget._tcga_clinical_builder = FakeClinicalBuilder()
    widget.refresh_project(project_summary)

    button = widget.findChild(QPushButton, "fetchTcgaClinicalMetadataButton")
    assert button.isEnabled()
    result = widget.fetch_tcga_clinical_metadata()

    assert result is not None
    assert result.mode == "expression_matched_cases"
    status_text = widget.findChild(QPlainTextEdit, "tcgaClinicalBuildStatus").toPlainText()
    assert "case：2；匹配 case：2；匹配 sample：3" in status_text
    assert "基础 OS 可用 case：1；死亡事件：1" in status_text
    assert "不会执行 KM/Cox/log-rank" in status_text


def test_data_source_tcga_clinical_metadata_ui_allows_project_preview_without_expression_build(qt_app, project_summary, monkeypatch, tmp_path: Path) -> None:
    from app.bioinformatics.data_sources.tcga_clinical_builder import TCGAClinicalBuildResult

    paths = [tmp_path / name for name in (
        "tcga_clinical_raw_cases.json",
        "tcga_clinical_case_table.tsv",
        "tcga_clinical_diagnosis_table.tsv",
        "tcga_clinical_followup_table.tsv",
        "tcga_clinical_survival_table.tsv",
        "tcga_clinical_mapping_table.tsv",
        "tcga_clinical_build_manifest.json",
        "tcga_clinical_receipt.json",
    )]
    for path in paths:
        path.write_text("", encoding="utf-8")

    class FakeClinicalBuilder:
        def build_for_project(self, project_root, project_id):
            return TCGAClinicalBuildResult(
                success=True,
                status="tcga_clinical_metadata_built",
                message="TCGA clinical 概况已获取：1 个 case；无 B6.4 表达矩阵，不能做表达-临床映射。",
                project_id=project_id,
                clinical_build_id="tcga-b66-preview",
                mode="project_clinical_preview_only",
                case_count=1,
                matched_case_count=0,
                matched_sample_count=0,
                survival_case_count=1,
                death_event_count=0,
                raw_cases_path=paths[0],
                case_table_path=paths[1],
                diagnosis_table_path=paths[2],
                followup_table_path=paths[3],
                survival_table_path=paths[4],
                mapping_table_path=paths[5],
                clinical_manifest_path=paths[6],
                clinical_receipt_path=paths[7],
                warnings=("project_clinical_preview_only_no_expression_mapping",),
            )

    monkeypatch.setattr(workflow_pages, "latest_tcga_expression_build_manifest_path", lambda project_root, **kwargs: None)
    widget = BioinformaticsDataSourceWidget()
    widget._tcga_clinical_builder = FakeClinicalBuilder()
    widget.refresh_project(project_summary)

    assert widget.findChild(QPushButton, "fetchTcgaClinicalMetadataButton").isEnabled() is False
    result = widget.fetch_tcga_clinical_metadata()

    assert result is not None
    assert result.mode == "project_clinical_preview_only"
    status_text = widget.findChild(QPlainTextEdit, "tcgaClinicalBuildStatus").toPlainText()
    assert "项目 clinical 概况预览" in status_text
    assert "匹配 case：0；匹配 sample：0" in status_text


def test_data_source_tcga_workflow_restores_existing_clinical_manifest(qt_app, project_summary) -> None:
    expression_manifest = project_summary.project_root / "standardized_data" / "tcga" / "tcga-thca" / "build" / "data_prepared" / "tcga" / "tcga_expression_build_manifest.json"
    clinical_manifest = expression_manifest.parent / "clinical" / "tcga_clinical_build_manifest.json"
    expression_manifest.parent.mkdir(parents=True, exist_ok=True)
    clinical_manifest.parent.mkdir(parents=True, exist_ok=True)
    expression_manifest.write_text(json.dumps({"project_id": "TCGA-THCA", "sample_count": 2, "gene_count": 1}), encoding="utf-8")
    clinical_manifest.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.tcga_clinical_build_manifest.v1",
                "project_id": "TCGA-THCA",
                "clinical_build_id": "clinical",
                "mode": "expression_matched_cases",
                "summary": {
                    "case_count": 2,
                    "matched_case_count": 2,
                    "matched_sample_count": 2,
                    "survival_case_count": 1,
                    "death_event_count": 1,
                    "clinical_gate_status": "clinical_ready",
                    "survival_gate_status": "survival_ready_basic",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="tcga_project",
        source_label="TCGA-THCA",
        strategy="reference",
        selected_paths=[expression_manifest],
        metadata={"source": "tcga_gdc", "project_id": "TCGA-THCA", "download_status": "tcga_expression_matrix_built", "tcga_expression_build_manifest_path": str(expression_manifest)},
    )
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="tcga_project",
        source_label="TCGA-THCA",
        strategy="reference",
        selected_paths=[clinical_manifest],
        metadata={
            "source": "tcga_gdc",
            "project_id": "TCGA-THCA",
            "download_status": "tcga_clinical_metadata_built",
            "tcga_clinical_build_manifest_path": str(clinical_manifest),
            "tcga_clinical_summary": {"case_count": 2, "matched_case_count": 2, "survival_case_count": 1, "death_event_count": 1},
        },
    )

    widget = BioinformaticsDataSourceWidget()
    widget._tcga_project_combo.setCurrentIndex(widget._tcga_project_combo.findData("TCGA-THCA"))
    widget.refresh_project(project_summary)

    workflow_text = _table_text(widget.findChild(QTableWidget, "tcgaWorkflowStepsTable"))
    assert "4. 获取 TCGA 临床信息" in workflow_text
    assert "clinical 已获取：2 case" in workflow_text
    assert "基础 OS 1 case" in workflow_text


def test_data_source_tcga_workflow_buttons_are_project_scoped(qt_app, project_summary) -> None:
    manifest = project_summary.project_root / "standardized_data" / "tcga" / "tcga-luad" / "build" / "data_prepared" / "tcga" / "tcga_expression_build_manifest.json"
    matrix = manifest.parent / "expression" / "tcga_expression_matrix.csv"
    sample = manifest.parent / "sample_metadata" / "tcga_sample_metadata.csv"
    gene = manifest.parent / "expression" / "tcga_gene_annotation.csv"
    matrix.parent.mkdir(parents=True, exist_ok=True)
    sample.parent.mkdir(parents=True, exist_ok=True)
    matrix.write_text("gene_id,TCGA-LU-0001-01A\nTP53,1\n", encoding="utf-8")
    sample.write_text("sample_id\nTCGA-LU-0001-01A\n", encoding="utf-8")
    gene.write_text("gene_id,gene_name\nTP53,TP53\n", encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.tcga_expression_build_manifest.v1",
                "project_id": "TCGA-LUAD",
                "sample_count": 1,
                "gene_count": 1,
                "metric_matrix_paths": {"raw_counts": str(matrix)},
                "sample_metadata_path": str(sample),
                "gene_annotation_path": str(gene),
            }
        ),
        encoding="utf-8",
    )
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="tcga_project",
        source_label="TCGA-LUAD",
        strategy="reference",
        selected_paths=[matrix, sample, gene, manifest],
        metadata={
            "source": "tcga_gdc",
            "project_id": "TCGA-LUAD",
            "download_status": "tcga_expression_matrix_built",
            "ready_for_recognition": "pending_data_check",
            "analysis_gate_status": "pending_data_check",
            "tcga_expression_build_manifest_path": str(manifest),
            "tcga_expression_build_summary": {"sample_count": 1, "gene_count": 1},
        },
    )

    widget = BioinformaticsDataSourceWidget()
    widget._tcga_project_combo.setCurrentIndex(widget._tcga_project_combo.findData("TCGA-THCA"))
    widget.refresh_project(project_summary)
    assert widget.findChild(QPushButton, "fetchTcgaClinicalMetadataButton").isEnabled() is False
    assert "需要先构建表达矩阵" in widget.findChild(QPlainTextEdit, "tcgaClinicalBuildStatus").toPlainText()

    widget._tcga_project_combo.setCurrentIndex(widget._tcga_project_combo.findData("TCGA-LUAD"))
    widget._refresh_tcga_workflow_state()
    widget._refresh_tcga_clinical_build_state()
    assert widget.findChild(QPushButton, "fetchTcgaClinicalMetadataButton").isEnabled() is True
    assert "表达矩阵已构建" in _table_text(widget.findChild(QTableWidget, "tcgaWorkflowStepsTable"))


def test_data_source_tcga_metadata_preview_network_failure(qt_app, project_summary) -> None:
    class FailingTcgaPreviewService:
        def build_preview(self, request):
            from app.bioinformatics.data_sources.tcga_preview import TCGAPreviewSummary

            return TCGAPreviewSummary(
                request=request,
                status="failed",
                case_count=0,
                sample_count=0,
                file_count=0,
                estimated_size_bytes=0,
                size_has_unknown=False,
                sample_type_counts={},
                access_counts={},
                workflow_type_counts={},
                data_format_counts={},
                warnings=("GDC metadata 预览失败：timeout",),
                is_download_plan_available=False,
                gdc_filters={"op": "and", "content": []},
                case_filters={"op": "and", "content": []},
                selected_file_ids_preview=(),
                files_fetched=0,
                cases_fetched=0,
                files_total=None,
                cases_total=None,
                error_message="timeout",
            )

    widget = BioinformaticsDataSourceWidget()
    widget._tcga_preview_service = FailingTcgaPreviewService()
    widget.refresh_project(project_summary)

    summary = widget.preview_tcga_downloadable_data()

    assert summary is not None
    assert summary.status == "failed"
    assert "预览失败" in widget.findChild(QPlainTextEdit, "tcgaMetadataPreviewWarnings").toPlainText()
    assert widget.findChild(QPushButton, "createTcgaDownloadPlanDraftButton").isEnabled() is False
    assert widget.create_tcga_download_plan_draft() is None


def test_data_source_gtex_request_is_pending_and_not_tcga_control(qt_app, project_summary) -> None:
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    summary = widget.create_gtex_source_request()

    assert summary is not None
    assert summary.source_type == "gtex_tissue"
    assert summary.strategy == "plan_only"
    assert summary.source_files == ()
    assert "不会作为 TCGA 自动对照" in widget.status_message()
    request_index = project_summary.project_root / "manifests" / "data_source_requests.json"
    payload = json.loads(request_index.read_text(encoding="utf-8"))
    assert payload["requests"][-1]["source_type"] == "GTEx"
    assert payload["requests"][-1]["internal_selection"]["not_tcga_auto_control"] is True
    assert workflow_pages._ready_registered_source_count(project_summary.project_root) == 0
    entries = workflow_pages._current_project_dataset_entries(project_summary.project_root)
    assert entries[0].source == "GTEx 数据库"
    assert entries[0].status == "等待下载与构建"
    assert entries[0].ready_for_recognition is False


def test_data_source_gtex_g6_preview_download_build_flow(qt_app, project_summary) -> None:
    class FakeDownloader:
        def download_file(self, entry: dict[str, object], target_dir: Path) -> dict[str, object]:
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / str(entry.get("file_name") or "gtex_expression.tsv")
            target.write_text(
                "gene_id\tGTEX-1111-0001-SM-A\tGTEX-2222-0001-SM-B\n"
                "TP53\t1.2\t2.4\n"
                "PTEN\t0.5\t0.8\n",
                encoding="utf-8",
            )
            return {
                "status": "success",
                "cache_hit": False,
                "local_path": str(target),
                "bytes_downloaded": target.stat().st_size,
                "source_url": str(entry.get("url") or ""),
            }

    def fake_fetcher(url, params, timeout):
        return {
            "data": [
                {
                    "tissueSiteDetailId": "Thyroid",
                    "tissueSiteDetail": "Thyroid",
                    "rnaSeqSampleCount": 2,
                    "donorCount": 2,
                    "datasetId": "GTEx_v8",
                    "file_manifest_entries": [
                        {
                            "file_id": "gtex-thyroid",
                            "file_name": "gtex_thyroid_tpm.tsv",
                            "file_size": 10,
                            "url": "https://example.org/gtex_thyroid_tpm.tsv",
                            "value_type": "TPM",
                        }
                    ],
                }
            ]
        }

    widget = BioinformaticsDataSourceWidget()
    widget._gtex_preview_service = workflow_pages.GTExMetadataPreviewService(fake_fetcher)
    widget._gtex_download_executor = workflow_pages.GTExDownloadPlanExecutor(downloader=FakeDownloader())
    widget.refresh_project(project_summary)

    button_texts = [button.text() for button in widget.findChildren(QPushButton)]
    assert "获取 TCGA 临床信息" in button_texts
    assert "预览 GTEx 可下载数据" in button_texts
    assert "下载 GTEx 原始文件" in button_texts
    assert "构建 GTEx 表达矩阵" in button_texts
    assert widget.findChild(QPushButton, "createGtexDownloadPlanDraftButton").isEnabled() is False

    preview = widget.preview_gtex_downloadable_data()
    assert preview is not None
    assert preview.file_count == 1
    assert widget.findChild(QPushButton, "createGtexDownloadPlanDraftButton").isEnabled() is True

    plan = widget.create_gtex_download_plan_draft()
    assert plan is not None
    assert widget.findChild(QPushButton, "downloadGtexRawFilesButton").isEnabled() is True

    download = widget.download_gtex_raw_files()
    assert download is not None
    assert download.success_count == 1
    assert widget.findChild(QPushButton, "buildGtexExpressionMatrixButton").isEnabled() is True

    build = widget.build_gtex_expression_matrix()
    assert build is not None
    assert build.sample_count == 2
    assert build.donor_count == 2
    assert widget.findChild(QPushButton, "enterGtexDataCheckButton").isEnabled() is True
    status = widget.findChild(QPlainTextEdit, "gtexWorkflowStatus").toPlainText()
    assert "GTEx 不自动作为 TCGA normal control" in status
    workflow_text = _table_text(widget.findChild(QTableWidget, "gtexWorkflowStepsTable"))
    assert "4. 进入数据检查与准备" in workflow_text
    assert "GTEx 构建产物可进入数据检查" in workflow_text
    assert workflow_pages._ready_registered_source_count(project_summary.project_root) == 1
    readiness = workflow_pages.run_project_readiness(project_summary.project_root)
    joint_row = next(row for row in readiness["capability_matrix"]["rows"] if row["analysis_type"] == "tcga_gtex_joint")
    assert joint_row["can_run"] is False
    assert any("不会自动作为 TCGA normal control" in warning for warning in joint_row["warnings"])


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


def test_data_source_multifile_local_batch_display_detail_and_recognition_handoff(qt_app, project_summary, tmp_path: Path) -> None:
    files = {
        "GSE6004_family.soft": "^SERIES = GSE6004\n!Series_title = demo\n",
        "expression_matrix.tsv": "gene\tcase_1\tcontrol_1\nTP53\t2\t1\n",
        "sample_metadata.tsv": "sample\tgroup\ncase_1\tcase\ncontrol_1\tcontrol\n",
        "clinical.tsv": "sample\tstage\ncase_1\tII\ncontrol_1\tNA\n",
    }
    sources = []
    for name, content in files.items():
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        sources.append(path)
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)

    summary = widget.register_local_paths(sources, strategy="reference", selected_kind="file", summary_key="local_import")

    expected_paths = [str(path.resolve()) for path in sources]
    assert summary is not None
    assert list(summary.source_files) == expected_paths
    assert list(summary.referenced_paths) == expected_paths
    assert widget.source_summary_text("local_import") == "已选择本地数据：本地导入批次：4 个文件"
    assert str(sources[0].resolve()) not in widget.source_summary_text("local_import")
    assert "另有 1 个文件" in widget.source_summary_tooltip("local_import")
    raw_import_root = project_summary.project_root / "raw_data" / "local_import"
    assert not any(path.is_file() for path in raw_import_root.rglob("*"))

    table = widget._dataset_list_panel._table
    assert table.rowCount() == 4
    table_names = {table.item(row, 2).text() for row in range(table.rowCount())}
    assert table_names == set(files)
    for row in range(table.rowCount()):
        assert table.item(row, 3).text() == "已导入"
        assert table.item(row, 4).text() == "待识别：1 个文件"
        assert table.item(row, 6).text() == ""
    batch_summary = widget._dataset_list_panel._batch_summary.text()
    assert "本地导入批次摘要" in batch_summary
    assert "文件总数：4 个" in batch_summary
    assert "保存方式：引用原始位置" in batch_summary
    assert "包含 GSE6004_family.soft 等 4 个文件" in batch_summary
    visible_table_text = "\n".join(
        table.item(row, col).text()
        for row in range(table.rowCount())
        for col in range(table.columnCount())
        if table.item(row, col) is not None
    )
    assert str(sources[0].resolve()) not in visible_table_text
    assert "包含 GSE6004_family.soft 等 4 个文件" not in visible_table_text

    key = next(entry.key for entry in widget._dataset_entries.values() if entry.name == "GSE6004_family.soft")
    widget._show_dataset_detail(key)
    detail_text = widget._dataset_detail_panel._summary.toPlainText()
    assert "当前查看文件：GSE6004_family.soft" in detail_text
    assert "文件总数：4 个" in detail_text
    assert "保存方式：引用原始位置" in detail_text
    for source in sources:
        assert source.name in detail_text
    assert widget._dataset_detail_panel._note_edit.toPlainText() == ""
    assert widget._dataset_detail_panel._note_edit.placeholderText() == "可记录筛选理由、疑问或后续处理计划，备注只作为笔记保存"
    widget._dataset_detail_panel._note_edit.setPlainText("优先检查 SOFT 元数据")
    widget._dataset_detail_panel._save_note()
    notes_path = project_summary.project_root / "manifests" / "user_dataset_notes.json"
    notes_payload = json.loads(notes_path.read_text(encoding="utf-8"))
    assert notes_payload["notes"][key]["note"] == "优先检查 SOFT 元数据"

    row_by_name = {table.item(row, 2).text(): row for row in range(table.rowCount())}
    assert table.item(row_by_name["GSE6004_family.soft"], 6).text() == "优先检查 SOFT 元数据"
    assert table.item(row_by_name["expression_matrix.tsv"], 6).text() == ""
    checkbox = table.cellWidget(row_by_name["GSE6004_family.soft"], 0)
    assert isinstance(checkbox, QCheckBox)
    checkbox.setChecked(True)
    widget.continue_to_recognition()
    pending = json.loads((project_summary.project_root / "manifests" / "pending_recognition_selection.json").read_text(encoding="utf-8"))
    assert pending["selected_sources"][0]["display_name"] == "本地导入批次：4 个文件"
    assert pending["selected_sources"][0]["source_files"] == expected_paths
    assert pending["selected_sources"][0]["source_file_count"] == 4

    recognition = BioinformaticsRecognitionWidget()
    recognition.refresh_project(project_summary)
    pre_table = recognition.findChild(QTableWidget, "preRecognitionInputList")
    assert pre_table.rowCount() == 1
    assert pre_table.item(0, 2).text() == "本地导入批次：4 个文件"
    assert pre_table.item(0, 3).text() == "4 个文件"
    report = recognition.run_recognition()

    assert report is not None
    assert report["selected_input_count"] == 4
    assert set(report["selected_inputs"]) == set(expected_paths)


def test_b5_16_data_check_page_expands_three_local_files(qt_app, project_summary, tmp_path: Path) -> None:
    sources = []
    for name, content in {
        "expression_matrix.tsv": "gene\tcase_1\tcontrol_1\nTP53\t2\t1\n",
        "sample_metadata.tsv": "sample_id\tgroup\ncase_1\tcase\ncontrol_1\tcontrol\n",
        "imported_deg.tsv": "gene\tlogFC\tP.Value\tadj.P.Val\nTP53\t1.2\t0.01\t0.03\n",
    }.items():
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        sources.append(path)
    widget = BioinformaticsDataSourceWidget()
    widget.refresh_project(project_summary)
    widget.register_local_paths(sources, strategy="reference", selected_kind="file", summary_key="local_import")

    pending_table = widget._dataset_list_panel._table
    assert pending_table.rowCount() == 3
    assert {pending_table.item(row, 2).text() for row in range(3)} == {path.name for path in sources}

    for row in range(pending_table.rowCount()):
        checkbox = pending_table.cellWidget(row, 0)
        assert isinstance(checkbox, QCheckBox)
        checkbox.setChecked(True)
    widget.continue_to_recognition()

    readiness = BioinformaticsReadinessDashboardWidget()
    readiness.refresh_project(project_summary)
    pending_check_table = readiness.findChild(QTableWidget, "dataCheckFileStatusTable")
    assert pending_check_table.rowCount() == 3
    assert {pending_check_table.item(row, 3).text() for row in range(3)} == {"灰色：未检查"}

    readiness.save_and_rerun_readiness()
    checked_table = readiness.findChild(QTableWidget, "dataCheckFileStatusTable")
    assert checked_table.rowCount() == 3
    status_text = " ".join(
        checked_table.item(row, col).text()
        for row in range(checked_table.rowCount())
        for col in range(checked_table.columnCount())
        if checked_table.item(row, col)
    )
    assert "expression_matrix.tsv" in status_text
    assert "sample_metadata.tsv" in status_text
    assert "imported_deg.tsv" in status_text
    assert "绿色：检查通过" in status_text
    assert "黄色：需要用户确认或补充" in status_text or "黄色：后续 GSEA 资源候选" in status_text
    dataset_table = readiness.findChild(QTableWidget, "datasetReadinessSummaryTable")
    dataset_text = " ".join(
        dataset_table.item(row, col).text()
        for row in range(dataset_table.rowCount())
        for col in range(dataset_table.columnCount())
        if dataset_table.item(row, col)
    )
    assert "可用 expression matrix" in dataset_text
    assert "sample metadata" in dataset_text
    assert "imported DEG" in dataset_text


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
    assert widget._gse_geo_detail_panel._save_button.text() == "保存"
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
    assert widget.status_message() == "已在下载列表 / 待处理数据来源中：GSE60024"
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

    assert result == "中文研究主题检索已移动到独立页面。"
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
    events: list[Path] = []
    widget = BioinformaticsDataSourceWidget(on_continue=events.append)
    widget.refresh_project(project_summary)

    assert widget._dataset_list_panel._table.rowCount() == 0
    assert not widget._dataset_list_panel._empty.isHidden()
    assert not widget._next_button.isEnabled()
    assert not widget.findChild(QPushButton, "local_importOpenSourceButton").isVisible()
    assert not widget.findChild(QPushButton, "local_importCopyPathButton").isVisible()
    assert not widget._dataset_list_panel._download_selected_button.isEnabled()
    assert not widget._dataset_list_panel._delete_selected_button.isEnabled()
    check_buttons = [button.text() for button in widget.findChildren(QPushButton) if "数据检查" in button.text()]
    assert check_buttons == ["下一步：数据检查与准备"]
    assert widget.findChild(QLabel, "dataSelectionSavedCount").text() == "已保存数据来源：0 个"
    assert widget.findChild(QLabel, "dataSelectionDownloadCount").text() == "下载列表 / 待处理：0 个"
    assert widget.findChild(QLabel, "dataSelectionReadyCount").text() == "可进入数据检查：0 个"

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
    assert widget._next_button.isEnabled()
    check_buttons = [button.text() for button in widget.findChildren(QPushButton) if "数据检查" in button.text()]
    assert check_buttons == ["下一步：数据检查与准备"]
    assert widget._registered_count_label.text() == "已保存数据来源：1 个；待处理：0 个；可识别：1 个"
    assert widget.findChild(QLabel, "dataSelectionSavedCount").text() == "已保存数据来源：1 个"
    assert widget.findChild(QLabel, "dataSelectionDownloadCount").text() == "下载列表 / 待处理：0 个"
    assert widget.findChild(QLabel, "dataSelectionReadyCount").text() == "可进入数据检查：1 个"
    assert widget.findChild(QLabel, "dataSelectionNextStep").text() == "下一步：可以进入数据检查与准备。"
    widget._next_button.click()
    assert events == [project_summary.project_root]


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
    assert widget._query_input.placeholderText() == "例如：甲状腺癌 脂质代谢 免疫浸润"
    assert widget.findChild(QFrame, "chineseQueryDraftOverviewCard") is not None
    assert widget.findChild(QFrame, "chineseSearchStatusSummaryCard") is not None
    assert widget._draft_overview_status.text() == "草稿状态：尚未生成"
    assert widget._chinese_draft_status_label.text() == "Query draft：未生成"
    assert widget._chinese_partition_status_label.text() == "分区候选：GEO 0 个，TCGA 0 个，GTEx 0 个"
    assert widget._chinese_saved_count_label.text() == "已保存候选：0 个"
    assert widget._chinese_download_count_label.text() == "加入下载列表：0 个"
    assert widget._geo_query_box.toPlainText() == "暂无 GEO/GSE 检索草稿"
    assert widget._geo_query_box.isHidden()
    assert widget._tcga_query_box.toPlainText() == "暂无 TCGA/GDC 项目草稿"
    assert widget._gtex_query_box.toPlainText() == "暂无 GTEx 组织草稿"
    assert not widget._geo_empty_label.isHidden()
    assert not widget._tcga_empty_label.isHidden()
    assert not widget._gtex_empty_label.isHidden()
    assert widget._mapping_log.isHidden()
    button_texts = [button.text() for button in widget.findChildren(QPushButton)]
    assert button_texts.count("确认草稿") == 4
    assert "展开分区草稿" in button_texts
    assert "在线检索 GEO/GSE" in button_texts
    assert "在线检查 TCGA/GDC" in button_texts
    assert "在线检查 GTEx" in button_texts
    assert "查看完整检索词" in button_texts
    assert "检索候选数据集" not in button_texts
    assert "GEO/GSE" == widget._tabs.tabText(0)
    assert "TCGA/GDC" == widget._tabs.tabText(1)
    assert "GTEx" == widget._tabs.tabText(2)
    assert widget._continue_button.text() == "下一步：数据检查与准备"

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
    assert "保存" in tcga_card
    assert "查看详情" in tcga_card
    assert "忽略" in tcga_card
    assert "加入下载列表" in tcga_card
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
    assert "保存" in gtex_card
    assert "查看详情" in gtex_card
    assert "忽略" in gtex_card
    assert "加入下载列表" in gtex_card
    assert "待创建下载任务" in gtex_card
    assert widget._draft_overview_status.text() == "草稿状态：已生成，待用户确认"
    assert "thyroid cancer" in widget._draft_overview_geo.text()
    assert "TCGA-THCA" in widget._draft_overview_tcga.text()
    assert "Thyroid" in widget._draft_overview_gtex.text()
    assert widget._chinese_draft_status_label.text() == "Query draft：已生成，待确认"
    assert widget._chinese_partition_status_label.text() == "分区候选：GEO 0 个，TCGA 1 个，GTEx 1 个"
    assert widget._chinese_next_step_label.text() == "下一步：查看候选详情，保存或加入下载列表。"
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
    assert widget._geo_table.columnWidth(0) >= 250
    buttons = widget._geo_table.cellWidget(0, 0).findChildren(QPushButton)
    assert [button.text() for button in buttons] == ["查看详情", "保存", "忽略", "加入下载列表"]
    buttons[0].click()
    assert not widget._geo_dataset_detail_panel.isHidden()
    assert "GSE33630" in widget._geo_dataset_detail_panel._title.text()
    assert widget._geo_dataset_detail_panel._save_button.text() == "保存"
    assert widget._geo_dataset_detail_panel._download_list_button.text() == "加入下载列表"
    assert widget._geo_dataset_detail_panel._ignore_button.text() == "忽略"
    assert widget._geo_dataset_detail_panel._translation_text.toPlainText() == "尚未生成中文翻译。"
    profile_text = widget._geo_dataset_detail_panel._profile_text.toPlainText()
    assert "样本结构预览" in profile_text
    assert "候选比较组" in profile_text
    assert "需用户确认" in profile_text


def test_chinese_dataset_search_ignore_hides_candidate_without_project_write(qt_app, project_summary) -> None:
    widget = BioinformaticsChineseDatasetSearchWidget()
    widget.refresh_project(project_summary)
    widget.set_query_text("甲状腺癌")
    widget.generate_terms()

    assert "TCGA-THCA" in _source_card_text(widget, "tcga_gdc")
    assert widget.ignore_candidate("tcga_gdc", "TCGA-THCA") is True

    assert "TCGA-THCA" not in _source_card_text(widget, "tcga_gdc")
    assert widget.status_message() == "已忽略：TCGA-THCA。仅从当前候选展示中移除。"
    records = [path for path in (project_summary.project_root / "acquisition" / "records").glob("*.json") if path.name != "latest_acquisition_record.json"]
    assert records == []


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
    assert widget._registered_count_label.text() == "已选 GEO 1 个，TCGA 0 个，GTEx 0 个；1 个可进入数据检查。 当前状态：可进入数据检查。"
    assert widget._continue_button.isEnabled()
    check_buttons = [button.text() for button in widget.findChildren(QPushButton) if "数据检查" in button.text()]
    assert check_buttons == ["下一步：数据检查与准备"]
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
    assert widget._geo_download_list_panel._delete_selected_button.isEnabled()
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


def test_geo_detail_panel_shows_and_saves_download_candidate_selection(qt_app, project_summary) -> None:
    _write_geo_candidate_manifest(project_summary.project_root)
    panel = workflow_pages.GeoDatasetDetailPanel()
    candidate = _geo_candidate()

    panel.show_candidate(candidate, project_root=project_summary.project_root, saved=True)

    table = panel._download_candidate_table
    assert table.rowCount() == 6
    table_text = " ".join(
        table.item(row, col).text()
        for row in range(table.rowCount())
        for col in range(1, table.columnCount())
        if table.item(row, col) is not None
    )
    assert "GSE33630-GPL570_series_matrix.txt.gz" in table_text
    assert "GSE33630_counts.tsv.gz" in table_text
    assert "RAW/heavy 风险文件" in table_text
    assert "外部 DEG 结果候选；不是软件计算结果" in table_text
    assert str(project_summary.project_root) not in table_text

    checkboxes = {
        table.item(row, 1).text(): table.cellWidget(row, 0)
        for row in range(table.rowCount())
    }
    assert isinstance(checkboxes["GSE33630-GPL570_series_matrix.txt.gz"], QCheckBox)
    assert checkboxes["GSE33630-GPL570_series_matrix.txt.gz"].isChecked()
    assert checkboxes["GSE33630_counts.tsv.gz"].isChecked()
    assert not checkboxes["GSE33630_RAW.tar"].isChecked()
    assert not checkboxes["GSE33630_DEG_results.xlsx"].isChecked()

    checkboxes["GSE33630_counts.tsv.gz"].setChecked(False)
    panel._save_download_candidates_button.click()

    selection_path = project_summary.project_root / "acquisition" / "gse_file_download_candidates" / "GSE33630_download_candidates.json"
    saved = json.loads(selection_path.read_text(encoding="utf-8"))
    selected_files = [row["file_name"] for row in saved["candidates"] if row["selected"]]
    assert selected_files == ["GSE33630-GPL570_series_matrix.txt.gz"]
    assert panel._download_candidate_status.text() == "已保存下载候选选择：1 个文件。"


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
    assert widget._geo_registered_table.item(0, 4).text() == "可识别"
    pending_entries = workflow_pages._current_project_dataset_entries(project_summary.project_root, expand_geo_files=True)
    geo_file_entries = [entry for entry in pending_entries if entry.source_type_key == "geo_accession"]
    assert [entry.name for entry in geo_file_entries] == ["GSE33630-GPL570_series_matrix.txt.gz", "GSE33630_counts.tsv.gz"]
    assert all(len(entry.source_files) == 2 for entry in geo_file_entries)
    assert "GEO 下载批次摘要" in workflow_pages._dataset_batch_summary_text(pending_entries)
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
    assert widget._registered_count_label.text() == "已选 GEO 0 个，TCGA 1 个，GTEx 0 个；0 个可进入数据检查。 当前建议操作：先补全表达矩阵。"
    assert not widget._continue_button.isEnabled()
    assert widget._continue_button.text() == "下一步：数据检查与准备"
    check_buttons = [button.text() for button in widget.findChildren(QPushButton) if "数据检查" in button.text()]
    assert check_buttons == ["下一步：数据检查与准备"]
    assert widget.status_message() == "已选择候选来源，待下载数据文件。"
    assert "已选择，待创建下载任务" in _source_card_text(widget, "tcga_gdc")
    download_result = widget.generate_candidate_download_task("tcga_gdc", "TCGA-THCA")
    assert download_result is not None
    assert download_result.status == "tcga_gdc_download_manifest_pending_file_selection"
    assert "GDC 下载任务清单" in widget.status_message()
    assert "下载清单已创建" in _source_card_text(widget, "tcga_gdc")
    registered_button = widget.findChild(QPushButton, "registerCandidateButton_tcga_gdc_TCGA-THCA")
    assert registered_button.text() == "已保存"
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
    check_buttons = [button.text() for button in widget._chinese_search_page.findChildren(QPushButton) if "数据检查" in button.text()]
    assert check_buttons == ["下一步：数据检查与准备"]
    widget._chinese_search_page._continue_button.click()

    assert widget.current_page_object_name() == "bioinformaticsReadinessDashboardPage"
    table = widget._readiness_page.findChild(QTableWidget, "dataCheckFileStatusTable")
    assert table.rowCount() == 1
    assert "GSE33630" in table.item(0, 0).text()


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
    assert "标准化数据" in standardization.status_message()


def test_standardization_page_userized_surface_hides_technical_fields(qt_app, project_summary) -> None:
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
    workflow_pages.run_project_recognition(project_summary.project_root)
    workflow_pages.run_project_readiness(project_summary.project_root)

    widget = BioinformaticsStandardizedAssetsWidget()
    widget.refresh_project(project_summary)
    widget.generate_assets()

    button_texts = {button.text() for button in widget.findChildren(QPushButton)}
    assert {"生成标准化数据", "确认分组与比较设计", "继续到分析任务中心"}.issubset(button_texts)
    assert widget.findChild(QLabel, "standardizationExpressionStatus") is not None
    assert "表达矩阵" in widget.findChild(QLabel, "standardizationExpressionStatus").text()
    assert "样本信息" in widget.findChild(QLabel, "standardizationSampleStatus").text()
    assert "分组与比较设计" in widget.findChild(QLabel, "standardizationGroupStatus").text()
    assert "下一步建议" in widget.findChild(QLabel, "standardizationNextStep").text()

    table = widget.findChild(QTableWidget, "standardizationUserAssetTable")
    assert table is not None
    headers = [table.horizontalHeaderItem(index).text() for index in range(table.columnCount())]
    assert headers == ["数据内容", "当前状态", "用于后续分析", "说明"]
    visible_table_text = "\n".join(
        table.item(row, col).text()
        for row in range(table.rowCount())
        for col in range(table.columnCount())
        if table.item(row, col) is not None
    )
    assert str(raw_file) not in visible_table_text
    assert "materialize" not in visible_table_text
    assert "validation_status" not in visible_table_text
    assert "analysis-ready" not in visible_table_text
    assert "manifest" not in visible_table_text.lower()
    assert "schema" not in visible_table_text.lower()

    diagnostics = widget.findChild(QPlainTextEdit, "standardizationDeveloperDiagnostics")
    assert diagnostics is not None
    assert not diagnostics.isVisible()
    diagnostics_text = diagnostics.toPlainText()
    assert "standardized_assets_registry" in diagnostics_text
    assert "analysis_ready_manifest" in diagnostics_text
    assert str(raw_file) in diagnostics_text


def test_recognition_requires_selected_inputs(qt_app, project_summary) -> None:
    source = project_summary.project_root / "raw_data" / "local_import" / "expression.tsv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    workflow_pages.register_acquisition(project_summary.project_root, source_type="local_import", source_label="expression.tsv", strategy="reference", selected_paths=[source])

    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)

    assert widget.run_recognition() is None
    assert widget.status_message() == "请先选择需要识别的数据。"


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


def test_recognition_main_buttons_are_simplified_and_summary_read_only(qt_app, project_summary) -> None:
    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)
    button_texts = [button.text() for button in widget.findChildren(QPushButton)]

    assert "开始识别" in button_texts
    assert "刷新" in button_texts
    assert widget.findChild(QFrame, "recognitionTechnicalOperations").isHidden()
    assert widget._counts.isReadOnly()


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
    assert readiness.findChild(QFrame, "readinessTodo_gmt_gene_set") is None
    assert readiness.findChild(QLabel, "gseaGeneSetStatus").text() == "GSEA 基因集：未选择"
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


def test_gsea_gene_set_resource_manager_displays_and_selects_local_resource(qt_app, project_summary, tmp_path: Path) -> None:
    gmt = _write_gmt(tmp_path / "custom_signatures.gmt")
    dialog = GseaGeneSetResourceManagerDialog(project_summary.project_root)

    result = dialog.import_local_gmt(
        gmt,
        {
            "name": "Custom signatures",
            "collection_type": "Custom",
            "species": "human",
            "gene_id_type": "symbol",
            "source_name": "unit test",
        },
    )

    assert result is not None
    table = dialog.findChild(QTableWidget, "gseaGeneSetResourceTable")
    assert table is not None
    assert table.rowCount() == 1
    assert table.item(0, 0).text() == "Custom signatures"
    assert table.item(0, 6).text() == "available"
    assert table.item(0, 7).text() == "2"

    dialog.select_current_resource()
    assert table.item(0, 8).text() == "是"
    detail = dialog.show_current_resource_detail()
    assert detail is not None
    assert detail["gene_id_type"] == "symbol"


def test_gene_set_resource_manager_shows_downloadable_resources_and_refreshes_after_download(qt_app, project_summary, tmp_path: Path, monkeypatch) -> None:
    dialog = GseaGeneSetResourceManagerDialog(project_summary.project_root)
    future_table = dialog.findChild(QTableWidget, "gseaGeneSetFutureResourcesTable")
    assert future_table is not None
    future_text = "\n".join(future_table.item(row, col).text() for row in range(future_table.rowCount()) for col in range(future_table.columnCount()) if future_table.item(row, col))
    assert "Reactome pathways" in future_text
    assert "GO Biological Process" in future_text
    assert "KEGG human pathways" in future_text
    assert "请导入用户已下载的 MSigDB GMT" in future_text

    def fake_download(project_root: Path, resource_id: str, **_kwargs):
        return workflow_pages.import_gmt_file(
            project_root,
            _write_gmt(tmp_path / f"{resource_id}.gmt"),
            {"resource_id": resource_id, "name": "Downloaded Reactome", "collection_type": "Reactome", "species": "all_species", "gene_id_type": "symbol"},
        ) | {"cached": False}

    monkeypatch.setattr(workflow_pages, "download_gene_set_resource", fake_download)
    dialog.download_selected_common_resource()

    local_table = dialog.findChild(QTableWidget, "gseaGeneSetResourceTable")
    assert local_table is not None
    assert local_table.item(0, 0).text() == "Downloaded Reactome"
    assert local_table.item(0, 6).text() == "available"


def test_readiness_gene_set_button_opens_manager_and_status_updates(qt_app, project_summary, tmp_path: Path) -> None:
    readiness = BioinformaticsReadinessDashboardWidget()
    readiness.refresh_project(project_summary)

    opened = readiness.open_gene_set_resource_manager()

    assert opened is not None
    dialog = opened["dialog"]
    assert isinstance(dialog, GseaGeneSetResourceManagerDialog)
    table = dialog.findChild(QTableWidget, "gseaGeneSetResourceTable")
    assert table is not None
    assert table.rowCount() == 1
    assert table.item(0, 0).text() == "暂无本地 GSEA 基因集资源。"

    dialog.import_local_gmt(
        _write_gmt(tmp_path / "selected.gmt"),
        {"name": "Selected gene set", "collection_type": "Custom", "species": "human", "gene_id_type": "symbol"},
    )
    dialog.select_current_resource()

    assert readiness.findChild(QLabel, "gseaGeneSetStatus").text() == "GSEA 基因集：已选择 Selected gene set"


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

    assert "运行数据检查" in button_texts
    assert "重新检查" not in button_texts
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

    assert preview is not None
    text = preview.toPlainText()
    assert "样本数：4" in text
    assert "识别到的候选分组：condition" in text
    assert "分组数量：2 组" in text
    assert "control 2" in text
    assert "treated 2" in text
    assert "正式比较组需由你确认" in text


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
    assert "已重新运行数据检查" in readiness.status_message()


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
    assert any(item["result_semantics"] == "testing-level" for item in entries)
    assert "测试级 GEO 差异分析结果" in task_center.status_message()
    assert "不等于正式 DEG 分析" in task_center.status_message()


def test_analysis_task_center_userized_main_surface_and_diagnostics(qt_app, project_summary, tmp_path: Path) -> None:
    expression_file = tmp_path / "expression_matrix.tsv"
    expression_file.write_text("gene\ts1\ts2\nTP53\t1\t2\n", encoding="utf-8")
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="local_import",
        source_label="expression",
        strategy="reference",
        selected_paths=[expression_file],
    )
    workflow_pages.run_project_recognition(project_summary.project_root)
    workflow_pages.run_project_readiness(project_summary.project_root)
    workflow_pages.generate_standardized_assets(project_summary.project_root)

    widget = BioinformaticsAnalysisTaskCenterWidget()
    widget.refresh_project(project_summary)

    buttons = {button.text() for button in widget.findChildren(QPushButton)}
    assert {"刷新任务状态", "确认分组与比较设计", "进入差异分析配置", "确认 formal DEG 参数", "查看已导入差异分析结果", "继续：结果浏览"}.issubset(buttons)
    assert widget.findChild(QLabel, "analysisTaskInputSummary") is not None
    assert "核心输入" in widget.findChild(QLabel, "analysisTaskInputSummary").text()
    assert "下一步建议" in widget.findChild(QLabel, "analysisTaskNextStep").text()

    table = widget.findChild(QTableWidget, "analysisTaskUserTable")
    assert table is not None
    headers = [table.horizontalHeaderItem(index).text() for index in range(table.columnCount())]
    assert headers == ["分析任务", "当前状态", "需要输入", "当前缺少", "下一步"]
    table_text = "\n".join(
        table.item(row, col).text()
        for row in range(table.rowCount())
        for col in range(table.columnCount())
        if table.item(row, col) is not None
    )
    assert "差异表达分析" in table_text
    assert "differential_expression" not in table_text
    assert "analysis_capability_matrix" not in table_text
    assert "manifest" not in table_text.lower()
    assert "task_id" not in table_text
    assert str(expression_file) not in table_text

    diagnostics = widget.findChild(QPlainTextEdit, "analysisTaskDeveloperDiagnostics")
    assert diagnostics is not None
    assert not diagnostics.isVisible()
    diagnostics_text = diagnostics.toPlainText()
    assert "analysis_task_center" in diagnostics_text
    assert "differential_expression" in diagnostics_text
    assert "analysis_center_state" in diagnostics_text

    package_table = widget.findChild(QTableWidget, "analysisPackageTable")
    assert package_table is not None
    package_text = _table_text(package_table)
    assert "DEG recompute input" in package_text
    assert "Blockers" not in package_text
    assert "sample metadata" in package_text or "Return to" in package_text or "raw count matrix" in package_text

    action_table = widget.findChild(QTableWidget, "analysisActionGateTable")
    assert action_table is not None
    action_text = _table_text(action_table)
    assert "Confirm formal DEG parameters" in action_text
    assert "Run controlled two-group DEG" in action_text
    assert "Review GSEA preranked readiness" in action_text
    assert "Run controlled preranked GSEA" in action_text
    assert "gsea_source_result_missing" in action_text or "gsea_input_gate_not_passed" in action_text
    assert "disabled" in action_text
    assert "Run formal GSEA" not in action_text
    assert "KM/Cox/log-rank" not in action_text
    assert "Export report-ready package" in action_text
    assert "blocked_report_ready_gate" in action_text

    dependency_table = widget.findChild(QTableWidget, "analysisDependencyTable")
    assert dependency_table is not None
    dependency_text = _table_text(dependency_table)
    assert "scipy" in dependency_text
    assert "statsmodels" in dependency_text
    assert "Detect only" in dependency_text
    assert "required_in_packaged_app_for_formal_deg" in dependency_text
    assert "安装" not in dependency_text

    formal_deg_gate = widget.findChild(QTableWidget, "analysisFormalDegGateTable")
    assert formal_deg_gate is not None
    formal_deg_gate_text = _table_text(formal_deg_gate)
    assert "Parameter manifest" in formal_deg_gate_text
    assert "User parameter confirmation" in formal_deg_gate_text
    assert "Result schema gate" in formal_deg_gate_text
    assert "B9.2 controlled activation" in formal_deg_gate_text

    confirmation_table = widget.findChild(QTableWidget, "analysisFormalDegConfirmationTable")
    assert confirmation_table is not None
    confirmation_text = _table_text(confirmation_table)
    assert "Comparison" in confirmation_text
    assert "Method" in confirmation_text
    assert "Thresholds" in confirmation_text
    assert "Dependency snapshot" in confirmation_text
    assert "Output plan" in confirmation_text

    gate_table = widget.findChild(QTableWidget, "analysisGatePreviewTable")
    assert gate_table is not None
    gate_text = _table_text(gate_table)
    assert "Report-ready export" in gate_text
    assert "GSEA source DEG result" in gate_text
    assert "GSEA rank metric" in gate_text
    assert "B11.2 controlled GSEA execution" in gate_text
    assert "blocked_report_ready_gate" in gate_text

    survival_table = widget.findChild(QTableWidget, "analysisSurvivalClinicalTable")
    assert survival_table is not None
    survival_text = _table_text(survival_table)
    assert "Survival design preflight" in survival_text
    assert "KM/Cox/log-rank/HR" in survival_text
    assert "disabled" in survival_text


def test_analysis_task_center_imported_deg_is_not_presented_as_computed(qt_app, project_summary, tmp_path: Path) -> None:
    imported_deg = tmp_path / "diffexpr-results.csv"
    imported_deg.write_text("gene,logFC,P.Value,adj.P.Val\nTP53,1.2,0.01,0.05\n", encoding="utf-8")
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="local_import",
        source_label="imported DEG",
        strategy="reference",
        selected_paths=[imported_deg],
    )
    workflow_pages.run_project_recognition(project_summary.project_root)
    workflow_pages.run_project_readiness(project_summary.project_root)

    widget = BioinformaticsAnalysisTaskCenterWidget()
    widget.refresh_project(project_summary)
    table = widget.findChild(QTableWidget, "analysisTaskUserTable")
    assert table is not None
    table_text = "\n".join(
        table.item(row, col).text()
        for row in range(table.rowCount())
        for col in range(table.columnCount())
        if table.item(row, col) is not None
    )
    assert "已有导入结果" in table_text
    assert "导入表格中的已有差异分析结果，不是本软件重新计算" in table_text
    assert "真实 DEG" not in table_text


def test_imported_deg_browser_user_page_and_report_candidate(qt_app, project_summary, tmp_path: Path) -> None:
    imported_deg = tmp_path / "deg_results.csv"
    imported_deg.write_text(
        "gene,logFC,P.Value,adj.P.Val\n"
        "TP53,1.2,0.01,0.02\n"
        "EGFR,-1.5,0.02,0.03\n"
        "ACTB,0.1,0.8,0.9\n",
        encoding="utf-8",
    )
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="local_import",
        source_label="imported DEG",
        strategy="reference",
        selected_paths=[imported_deg],
    )
    workflow_pages.run_project_recognition(project_summary.project_root)

    widget = BioinformaticsImportedDegBrowserWidget()
    widget.refresh_project(project_summary)

    assert "导入结果浏览" in widget.status_message()
    assert "这是用户导入的外部差异分析结果，不是 BioMedPilot 重新计算得到的结果" in widget.findChild(QLabel, "importedDegBoundary").text()
    table = widget.findChild(QTableWidget, "importedDegUserTable")
    assert table is not None
    headers = [table.horizontalHeaderItem(index).text() for index in range(table.columnCount())]
    assert headers == ["结果名称", "来源说明", "状态", "可用于报告", "主要列识别", "上调 / 下调 / 不显著", "查看详情"]
    table_text = "\n".join(
        table.item(row, col).text()
        for row in range(table.rowCount())
        for col in range(table.columnCount())
        if table.item(row, col) is not None
    )
    assert "用户导入 / 外部分析结果" in table_text
    assert "可浏览" in table_text
    assert "上调 1；下调 1；不显著 1" in table_text
    assert str(imported_deg) not in table_text
    assert "manifest" not in table_text.lower()
    assert "schema_version" not in table_text

    detail_text = widget.findChild(QLabel, "importedDegDetailSummary").text()
    assert "阈值草稿" in detail_text
    assert "Top up genes" in detail_text
    assert "报告可用性" in detail_text
    assert "本软件计算发现" not in detail_text
    preview = widget.findChild(QTableWidget, "importedDegPreviewTable")
    assert preview is not None
    assert preview.rowCount() == 3
    assert preview.columnCount() == 4

    entries = widget.mark_report_candidates()
    assert entries
    assert entries[0]["result_semantics"] == "imported result"
    assert entries[0]["result_type"] == "导入结果"
    assert (project_summary.project_root / str(entries[0]["manifest_ref"])).is_file()
    assert "不是 BioMedPilot 重新计算" in entries[0]["warning"]
    assert not (project_summary.project_root / "results" / "tables").exists()
    assert not (project_summary.project_root / "results" / "figures").exists()

    diagnostics = widget.findChild(QPlainTextEdit, "importedDegDeveloperDiagnostics")
    assert diagnostics is not None
    assert not diagnostics.isVisible()
    diagnostics_text = diagnostics.toPlainText()
    assert str(imported_deg) in diagnostics_text
    assert "semantic_boundary" in diagnostics_text


def test_deg_config_page_userized_preflight_blocks_missing_group(qt_app, project_summary, tmp_path: Path) -> None:
    expression_file = tmp_path / "counts_matrix.tsv"
    expression_file.write_text("gene\tcase_1\tcontrol_1\nTP53\t10\t2\n", encoding="utf-8")
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="local_import",
        source_label="counts",
        strategy="reference",
        selected_paths=[expression_file],
    )
    workflow_pages.run_project_recognition(project_summary.project_root)
    workflow_pages.generate_standardized_assets(project_summary.project_root)

    widget = BioinformaticsDegConfigWidget()
    widget.refresh_project(project_summary)

    assert "DEG 配置页" in widget.status_message()
    assert "仅配置 / 仅校验 / 未运行真实差异分析" in widget.findChild(QLabel, "degConfigBoundary").text()
    assert "raw path" not in widget.findChild(QLabel, "degInputSummary").text().lower()
    assert "manifest" not in widget.findChild(QLabel, "degInputSummary").text().lower()
    buttons = {button.text() for button in widget.findChildren(QPushButton)}
    assert {"生成 preflight 输入校验", "刷新状态", "返回分析任务中心"}.issubset(buttons)

    manifest = widget.run_preflight_check()

    assert manifest is not None
    assert manifest["status"] == "blocked"
    assert "输入校验记录，不是 DEG 结果" in widget.status_message()
    table = widget.findChild(QTableWidget, "degPreflightCheckTable")
    assert table is not None
    table_text = "\n".join(
        table.item(row, col).text()
        for row in range(table.rowCount())
        for col in range(table.columnCount())
        if table.item(row, col) is not None
    )
    assert "分组设计" in table_text
    assert "阻塞" in table_text
    assert "真实差异分析" not in table_text
    diagnostics = widget.findChild(QPlainTextEdit, "degPreflightDeveloperDiagnostics")
    assert diagnostics is not None
    assert not diagnostics.isVisible()
    assert "preflight_manifest" in diagnostics.toPlainText()
    assert str(expression_file) in diagnostics.toPlainText()


def test_deg_config_preflight_passed_is_not_real_analysis_and_imported_deg_is_excluded(qt_app, project_summary, tmp_path: Path) -> None:
    expression_file = tmp_path / "counts_matrix.tsv"
    expression_file.write_text(
        "gene\tcase_1\tcase_2\tcontrol_1\tcontrol_2\n"
        "TP53\t10\t12\t2\t3\n"
        "EGFR\t4\t5\t9\t10\n",
        encoding="utf-8",
    )
    imported_deg = tmp_path / "diffexpr-results.csv"
    imported_deg.write_text("gene,logFC,P.Value,adj.P.Val\nTP53,1.2,0.01,0.05\n", encoding="utf-8")
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="local_import",
        source_label="counts",
        strategy="reference",
        selected_paths=[expression_file, imported_deg],
    )
    config_path = comparison_config_path(project_summary.project_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        build_comparison_config_text(
            comparison_id="case_vs_control",
            group_column="group",
            case_group="case",
            control_group="control",
            assignments=(
                ComparisonSampleAssignment("case_1", "case"),
                ComparisonSampleAssignment("case_2", "case"),
                ComparisonSampleAssignment("control_1", "control"),
                ComparisonSampleAssignment("control_2", "control"),
            ),
        ),
        encoding="utf-8",
    )
    workflow_pages.run_project_recognition(project_summary.project_root)
    workflow_pages.generate_standardized_assets(project_summary.project_root)

    widget = BioinformaticsDegConfigWidget()
    widget.refresh_project(project_summary)
    assert "imported DEG" in widget.findChild(QLabel, "degInputSummary").text()
    manifest = widget.run_preflight_check()

    assert manifest is not None
    assert manifest["status"] == "passed"
    assert "不是 DEG 结果" in widget.status_message()
    assert not (project_summary.project_root / "results" / "tables").exists()
    table = widget.findChild(QTableWidget, "degPreflightCheckTable")
    assert table is not None
    table_text = "\n".join(
        table.item(row, col).text()
        for row in range(table.rowCount())
        for col in range(table.columnCount())
        if table.item(row, col) is not None
    )
    assert "通过" in table_text
    assert "real computed result" not in table_text


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
    input_paths = [Path(str(item.get("original_path"))) for item in files if item.get("original_path")]
    input_fingerprint = project_recognition._build_input_fingerprint(input_paths)
    payload = {
        "schema_version": project_recognition.RECOGNITION_REPORT_SCHEMA_VERSION,
        "recognition_engine_version": project_recognition.RECOGNITION_ENGINE_VERSION,
        "recognition_run_id": "test-recognition-run",
        "input_fingerprint": input_fingerprint,
        "report_status": "current",
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
                "parser_depth": "table_parsed",
                "sample_count": 2,
                "platform_count": 1,
                "expression_table_presence": True,
                "warnings": [],
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
    table = widget.findChild(QTableWidget, "recognitionResultTable")

    assert table.horizontalHeaderItem(3).text() == "识别可信度"
    assert "不是数据质量评分" in table.horizontalHeaderItem(3).toolTip()
    assert table.item(0, 3).text() == "70%"
    assert table.item(0, 4).text() == "5.5 MB"
    assert table.item(0, 1).text().startswith("...")
    assert table.horizontalHeaderItem(1).text() == "当前位置"
    assert table.item(0, 1).toolTip() == str(project_summary.project_root / "recognized_data/expression_matrix/GSE54350_series_matrix.txt")
    assert table.item(0, 2).text() == "GEO SOFT 容器（已解析表格结构；含：表达矩阵、样本注释）"
    assert "SOFT 解析深度：已解析表格结构" in table.item(0, 2).toolTip()
    assert "表达表格：检测为候选输入" in table.item(0, 2).toolTip()
    assert "可用角色：表达矩阵、样本注释" in table.item(0, 2).toolTip()
    assert "原始 bytes：5763709" in table.item(0, 4).toolTip()


def test_geo_soft_metadata_ui_does_not_claim_full_expression_parse(qt_app, project_summary, tmp_path: Path) -> None:
    source = tmp_path / "GSE6005_family.soft"
    source.write_text("^SERIES = GSE6005\n^SAMPLE = GSM1\n!Sample_title = untreated\n", encoding="utf-8")
    _write_mock_recognition_report(
        project_summary.project_root,
        [
            {
                "file_name": source.name,
                "original_path": str(source),
                "recognized_type": "geo_soft_container",
                "recognized_type_zh": "GEO SOFT 容器",
                "recognized_roles": ["sample_metadata", "platform_annotation"],
                "parser_depth": "metadata_parsed",
                "sample_count": 1,
                "platform_count": 1,
                "expression_table_presence": False,
                "warnings": ["Parsed sample/platform metadata, but no clear ID_REF/VALUE expression table was confirmed."],
                "detected_assets": [
                    {"asset_type": "sample_metadata", "label_zh": "样本注释", "input_eligible": True, "reason": "已解析 SOFT SAMPLE 块。"},
                    {"asset_type": "platform_annotation", "label_zh": "平台注释", "input_eligible": True, "reason": "已解析 SOFT PLATFORM 块。"},
                ],
                "confidence": 0.86,
                "file_size": 128,
                "reason": "GEO family SOFT 容器，已解析样本/平台元数据；尚未确认表达矩阵。",
                "warning": "",
                "route_path": str(source),
            }
        ],
    )

    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)
    table = widget.findChild(QTableWidget, "recognitionResultTable")
    text = table.item(0, 2).text()
    tooltip = table.item(0, 2).toolTip()

    assert "已解析样本/平台元数据" in text
    assert "表达表格：尚未确认表达矩阵" in tooltip
    assert "完整解析" not in text
    assert "完整表达矩阵" not in tooltip


def test_geo_series_matrix_ui_shows_candidate_confirmation_not_confirmed_group(qt_app, project_summary, tmp_path: Path) -> None:
    source = tmp_path / "GSE99999_series_matrix.txt.gz"
    source.write_text("placeholder", encoding="utf-8")
    _write_mock_recognition_report(
        project_summary.project_root,
        [
            {
                "file_name": source.name,
                "original_path": str(source),
                "recognized_type": "geo_series_matrix_container",
                "recognized_type_zh": "GEO Series Matrix 容器",
                "recognized_roles": ["expression_matrix", "sample_metadata", "phenotype_metadata", "platform_reference_hint"],
                "parser_depth": "matrix_previewed",
                "sample_count": 2,
                "platform_accessions": ["GPL96"],
                "expression_matrix_presence": True,
                "expression_matrix_dimensions": {"rows": 2, "columns": 3, "sample_columns": 2},
                "expression_value_type_candidate": "unknown",
                "gene_id_type_candidate": "probe_id",
                "sample_metadata_fields": ["geo_accession", "title", "characteristics_ch1", "disease"],
                "phenotype_candidate_fields": ["disease"],
                "warnings": ["Expression value type is unknown and must be confirmed during standardization."],
                "detected_assets": [
                    {"asset_type": "expression_matrix", "label_zh": "表达矩阵", "input_eligible": True, "reason": "已检测到 GEO Series Matrix 表达矩阵区域，可进入标准化阶段进一步确认。"},
                    {"asset_type": "sample_metadata", "label_zh": "样本注释", "input_eligible": True, "reason": "已解析样本 metadata。"},
                    {"asset_type": "phenotype_metadata", "label_zh": "表型信息", "input_eligible": True, "reason": "样本分组为候选推断，需用户确认后才能进行 DEG 分析。"},
                    {"asset_type": "platform_reference_hint", "label_zh": "平台参考提示", "input_eligible": False, "reason": "GEO Series Matrix 提供 GPL 平台编号。"},
                ],
                "confidence": 0.9,
                "file_size": 1024,
                "reason": "GEO Series Matrix 已解析；表达值类型、ID_REF 映射和候选分组需用户确认。",
                "warning": "",
                "route_path": str(source),
            }
        ],
    )

    widget = BioinformaticsRecognitionWidget()
    widget.refresh_project(project_summary)
    table = widget.findChild(QTableWidget, "recognitionResultTable")
    text = table.item(0, 2).text()
    tooltip = table.item(0, 2).toolTip()

    assert "已解析表达矩阵结构预览" in text
    assert "表达值类型候选：unknown" in tooltip
    assert "ID 类型候选：probe_id" in tooltip
    assert "需用户确认后才能进行 DEG 分析" in tooltip
    assert "已确认分组" not in tooltip
    assert "已完成差异分析" not in tooltip
    assert "表达矩阵已标准化" not in tooltip


def test_standardization_confirmation_page_shows_series_matrix_candidates_without_raw_paths(qt_app, project_summary) -> None:
    source = project_summary.project_root / "raw_data" / "local_import" / "GSE99999_series_matrix.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "\n".join(
            [
                "!Series_geo_accession\tGSE99999",
                "!Series_platform_id\tGPL96",
                "!Sample_title\tcase sample\tcontrol sample",
                "!Sample_geo_accession\tGSM900001\tGSM900002",
                "!Sample_organism_ch1\tHomo sapiens\tHomo sapiens",
                "!Sample_characteristics_ch1\tdisease: asthma\tdisease: control",
                "!series_matrix_table_begin",
                "ID_REF\tGSM900001\tGSM900002",
                "1007_s_at\t10\t12",
                "!series_matrix_table_end",
            ]
        ),
        encoding="utf-8",
    )
    workflow_pages.run_project_recognition(project_summary.project_root)

    widget = BioinformaticsStandardizedAssetsWidget()
    widget.refresh_project(project_summary)
    table = widget.findChild(QTableWidget, "standardizationConfirmationCandidateTable")
    table_text = " ".join(table.item(row, col).text() for row in range(table.rowCount()) for col in range(table.columnCount()) if table.item(row, col))

    assert "表达矩阵候选" in table_text
    assert "GSE99999_series_matrix.txt" in table_text
    assert "geo_series_matrix" in table_text
    assert "Sample_organism_ch1" in table_text
    assert str(project_summary.project_root) not in table_text
    assert "已确认分组" not in table_text
    assert "已完成差异分析" not in table_text
    assert "可直接做 DEG" not in table_text
    assert "表达矩阵已标准化" not in table_text
    assert "当前不会运行真实差异分析" in widget.findChild(QLabel, "standardizationConfirmationSummary").text()


def test_standardization_confirmation_page_writes_manifest_and_preflight_readiness(qt_app, project_summary) -> None:
    source = project_summary.project_root / "raw_data" / "local_import" / "GSE99999_series_matrix.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "\n".join(
            [
                "!Series_geo_accession\tGSE99999",
                "!Series_platform_id\tGPL96",
                "!Sample_geo_accession\tGSM900001\tGSM900002",
                "!Sample_organism_ch1\tHomo sapiens\tHomo sapiens",
                "!Sample_characteristics_ch1\tdisease: asthma\tdisease: control",
                "!series_matrix_table_begin",
                "ID_REF\tGSM900001\tGSM900002",
                "1007_s_at\t10\t12",
                "!series_matrix_table_end",
            ]
        ),
        encoding="utf-8",
    )
    workflow_pages.run_project_recognition(project_summary.project_root)

    widget = BioinformaticsStandardizedAssetsWidget()
    widget.refresh_project(project_summary)
    manifest = widget.confirm_expression_candidate(value_type_confirmed=False)

    assert manifest is not None
    assert manifest["readiness"]["deg_preflight_ready"] is False
    manifest = widget.confirm_expression_candidate(value_type="count_like_candidate", value_type_confirmed=True)
    assert manifest is not None
    assert manifest["readiness"]["deg_preflight_ready"] is False
    widget.confirm_species_candidate()
    widget.confirm_gene_id_type("probe_id")
    manifest = widget.confirm_group_candidate()

    assert manifest is not None
    assert manifest["confirmed_group_design"]["group_confirmed"] is True
    assert manifest["readiness"]["deg_preflight_ready"] is True
    assert (project_summary.project_root / "manifests" / "standardization_confirmation.json").exists()


def test_standardization_confirmation_page_filters_soft_metadata_and_lists_xlsx(qt_app, project_summary) -> None:
    soft = project_summary.project_root / "raw_data" / "local_import" / "GSE6005_family.soft"
    xlsx = project_summary.project_root / "raw_data" / "local_import" / "counts.xlsx"
    soft.parent.mkdir(parents=True, exist_ok=True)
    soft.write_text(
        "\n".join(
            [
                "^DATABASE = GeoMiame",
                "^SERIES = GSE6005",
                "!Series_sample_id = GSM1",
                "^PLATFORM = GPL570",
                "!Platform_title = demo",
                "^SAMPLE = GSM1",
                "!Sample_title = metadata only",
                "!Sample_characteristics_ch1 = treatment: untreated",
            ]
        ),
        encoding="utf-8",
    )
    _write_xlsx_count_matrix(xlsx)
    workflow_pages.run_project_recognition(project_summary.project_root)

    widget = BioinformaticsStandardizedAssetsWidget()
    widget.refresh_project(project_summary)
    table = widget.findChild(QTableWidget, "standardizationConfirmationCandidateTable")
    expression_rows = [
        [table.item(row, col).text() for col in range(table.columnCount()) if table.item(row, col)]
        for row in range(table.rowCount())
        if table.item(row, 0) and table.item(row, 0).text() == "表达矩阵候选"
    ]
    expression_text = " ".join(" ".join(row) for row in expression_rows)

    assert "counts.xlsx" in expression_text
    assert "xlsx" in expression_text
    assert "GSE6005_family.soft" not in expression_text


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
    assert "不重新扫描文件" in widget.status_message()

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


def test_no_expression_matrix_keeps_standardization_gate_blocked(qt_app, project_summary) -> None:
    source = project_summary.project_root / "raw_data" / "local_import" / "samples.tsv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("sample_id\tgroup\nS1\tcase\nS2\tcontrol\n", encoding="utf-8")
    _write_mock_recognition_report(
        project_summary.project_root,
        [
            {
                "file_name": source.name,
                "original_path": str(source),
                "recognized_type": "sample_metadata",
                "recognized_type_zh": "样本注释",
                "recognized_roles": ["sample_metadata"],
                "route_path": str(source),
            }
        ],
    )

    events: list[Path] = []
    recognition = BioinformaticsRecognitionWidget(on_continue=events.append)
    recognition.refresh_project(project_summary)
    recognition.continue_to_readiness()

    assert events == []
    assert "不能继续：未识别到表达矩阵或原始计数矩阵" in recognition.status_message()
    assert "未识别到表达矩阵或原始计数矩阵" in recognition._counts.toPlainText()

    readiness = BioinformaticsReadinessDashboardWidget(on_continue=events.append)
    readiness.refresh_project(project_summary)
    artifacts = readiness.run_readiness_check()
    assert artifacts is not None
    assert artifacts["readiness_report"]["standardization_ready"] is False  # type: ignore[index]
    assert artifacts["readiness_report"]["deg_ready"] is False  # type: ignore[index]
    assert "补充表达矩阵" in readiness.findChild(QLabel, "readinessNextStep").text()


def test_mixed_expression_detection_separates_standardization_and_deg_readiness(qt_app, project_summary) -> None:
    source = project_summary.project_root / "raw_data" / "local_import" / "GSE236866_Processed_data_tau_with_inhibitors.xlsx"
    source.parent.mkdir(parents=True, exist_ok=True)
    _write_xlsx_count_matrix(source)
    _write_mock_recognition_report(
        project_summary.project_root,
        [
            {
                "file_name": source.name,
                "original_path": str(source),
                "recognized_type": "tabular_text_file",
                "recognized_type_zh": "RNA-seq 综合表达结果表",
                "recognized_roles": [],
                "detected_assets": [
                    {"asset_type": "raw_count_matrix", "label_zh": "count 矩阵", "input_eligible": True},
                    {"asset_type": "normalized_expression_matrix", "label_zh": "FPKM 矩阵", "input_eligible": True},
                    {"asset_type": "differential_result_table", "label_zh": "差异分析结果", "input_eligible": False},
                    {"asset_type": "gene_annotation", "label_zh": "基因注释", "input_eligible": True},
                ],
                "route_path": str(source),
            }
        ],
    )

    events: list[Path] = []
    recognition = BioinformaticsRecognitionWidget(on_continue=events.append)
    recognition.refresh_project(project_summary)
    recognition.continue_to_readiness()

    assert events == [project_summary.project_root]
    assert "不能继续" not in recognition.status_message()
    assert "可以继续进入数据准备与标准化" in recognition.status_message()
    assert "可以继续进入数据准备与标准化" in recognition._counts.toPlainText()
    assert "确认分组后才能进行 DEG 分析" in recognition._counts.toPlainText()
    assert "未识别到表达矩阵" not in recognition.status_message()
    assert "未识别到表达矩阵" not in recognition._counts.toPlainText()

    readiness = BioinformaticsReadinessDashboardWidget(on_continue=events.append)
    readiness.refresh_project(project_summary)
    artifacts = readiness.run_readiness_check()
    assert artifacts is not None
    report = artifacts["readiness_report"]  # type: ignore[index]
    assert report["standardization_ready"] is True
    assert report["deg_ready"] is False
    assert "可以继续进入数据准备与标准化" in readiness.findChild(QLabel, "readinessStatusBadge").text()
    assert "已识别到的数据：表达矩阵" in readiness.findChild(QLabel, "readinessRecognizedInputs").text()
    assert "仍需补充的数据" in readiness.findChild(QLabel, "readinessMissingInputs").text()
    assert "可以继续进入数据准备与标准化" in readiness.findChild(QLabel, "readinessNextStep").text()
    assert "未识别到表达矩阵" not in readiness.findChild(QLabel, "readinessNextStep").text()
    readiness.continue_to_standardization()
    assert events[-1] == project_summary.project_root
    assert "不能继续" not in readiness.status_message()

    standardization = BioinformaticsStandardizedAssetsWidget(on_continue=events.append)
    standardization.refresh_project(project_summary)
    generated = standardization.generate_assets()
    assert generated is not None
    assert "表达矩阵：已整理为 BioMedPilot 内部标准格式" in standardization.findChild(QLabel, "standardizationExpressionStatus").text()
    assert "未执行生物学 normalization" in standardization.findChild(QLabel, "standardizationExpressionStatus").text()
    assert "尚未检测到明确分组" in standardization.findChild(QLabel, "standardizationGroupStatus").text()
    standardization.continue_to_workflow()
    assert events[-1] == project_summary.project_root
    assert "不能继续" not in standardization.status_message()


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
    assert "报告草稿" in report.status_message()

    settings = BioinformaticsSettingsAndLocalAIWidget()
    settings._question_input.setText("甲状腺癌淋巴结转移")
    terms = settings.generate_placeholder_terms()
    assert "GEO query draft" in terms
    assert "本地 AI" in settings.status_message()


def test_results_browser_userized_result_semantics_and_diagnostics(qt_app, project_summary) -> None:
    imported_path = project_summary.project_root / "results" / "tables" / "imported_deg.csv"
    testing_path = project_summary.project_root / "results" / "tables" / "testing_deg.csv"
    imported_path.parent.mkdir(parents=True, exist_ok=True)
    imported_path.write_text("gene,logFC,P.Value\nTP53,1.2,0.01\n", encoding="utf-8")
    testing_path.write_text("gene,logFC,P.Value\nEGFR,-1.1,0.02\n", encoding="utf-8")
    record_dir = project_summary.project_root / "analysis" / "task_records"
    record_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / "task-demo.json").write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.analysis_task_record.v1",
                "task_id": "task-demo",
                "task_type": "differential_expression",
                "label": "差异表达分析",
                "status": "created",
                "execution": "not_run",
                "note": "当前只创建任务记录，不运行正式统计分析。",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    write_result_index(
        project_summary.project_root,
        [
            {
                "result_name": "Imported DEG table",
                "analysis_type": "differential_expression",
                "file_type": "csv",
                "path": str(imported_path),
                "status": "imported",
                "result_semantics": "imported result",
            },
            {
                "result_name": "Testing DEG preview",
                "analysis_type": "differential_expression",
                "file_type": "csv",
                "path": str(testing_path),
                "status": "testing-level",
                "result_semantics": "testing-level",
            },
            {
                "result_name": "Dry run record",
                "analysis_type": "differential_expression",
                "file_type": "json",
                "status": "dry-run",
                "result_semantics": "dry-run",
            },
        ],
    )

    widget = BioinformaticsResultsBrowserWidget()
    widget.refresh_project(project_summary)

    assert "结果浏览" in widget.status_message()
    assert "导入结果浏览" in {button.text() for button in widget.findChildren(QPushButton)}
    assert "导入结果" in widget.findChild(QLabel, "resultsSourceSummary").text()
    assert "测试级结果" in widget.findChild(QLabel, "resultsSourceSummary").text()
    table = widget.findChild(QTableWidget, "resultsUserTable")
    assert table is not None
    headers = [table.horizontalHeaderItem(index).text() for index in range(table.columnCount())]
    assert headers == ["结果名称", "结果类型", "来源", "状态", "可用于报告", "生成时间", "简短说明", "查看详情"]
    table_text = "\n".join(
        table.item(row, col).text()
        for row in range(table.rowCount())
        for col in range(table.columnCount())
        if table.item(row, col) is not None
    )
    assert "导入表格中的已有差异分析结果，不是本软件重新计算" in table_text
    assert "测试级 / 开发者预览结果" in table_text
    assert "流程记录 / dry-run，未执行真实分析" in table_text
    assert "已配置，尚未运行" in table_text
    assert "查看详情" in table_text
    assert "真实计算结果" not in table_text
    assert str(imported_path) not in table_text
    assert "differential_expression" not in table_text
    assert "schema_version" not in table_text
    assert "task-demo" not in table_text

    diagnostics = widget.findChild(QPlainTextEdit, "resultsDeveloperDiagnostics")
    assert diagnostics is not None
    assert not diagnostics.isVisible()
    diagnostics_text = diagnostics.toPlainText()
    assert "result_index" in diagnostics_text
    assert "schema_version" in diagnostics_text
    assert str(imported_path) in diagnostics_text
    assert "analysis_center_state" in diagnostics_text

    gate = widget.findChild(QTableWidget, "resultsGatePreviewTable")
    assert gate is not None
    gate_text = _table_text(gate)
    assert "Report-ready export" in gate_text
    assert "blocked_report_ready_gate" in gate_text
    assert "Testing/imported/exploratory entries keep their semantics" in gate_text

    formal_review = widget.findChild(QTableWidget, "formalDegReviewTable")
    assert formal_review is not None
    assert formal_review.rowCount() == 0
    guard = widget.findChild(QLabel, "formalDegReviewGuard")
    assert guard is not None
    assert "not a clinical conclusion" in guard.text()


def test_results_browser_formal_deg_review_table_summary_and_exports(qt_app, project_summary) -> None:
    table_path = project_summary.project_root / "results" / "tables" / "formal_deg.tsv"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text(
        "feature_id\tgene_symbol\tbase_mean_or_mean_expression\tcase_mean\tcontrol_mean\tlog2_fold_change\tstatistic\tp_value\tadjusted_p_value\tsignificance_label\twarnings\n"
        "g1\tTP53\t10\t12\t4\t1.5\t3.0\t0.001\t0.003\tup\t\n"
        "g2\tEGFR\t10\t3\t9\t-1.4\t-2.9\t0.002\t0.004\tdown\t\n",
        encoding="utf-8",
    )
    register_result(
        project_summary.project_root,
        ResultIndexEntry(
            result_id="formal-ui",
            task_run_id="task-formal-ui",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="pkg-ui",
            source_dataset_id="dataset-ui",
            source_repository_manifest="standardized_data/repositories/repository_manifest.json",
            parameters_manifest={
                "method": "welch_t_test",
                "log2fc_threshold": 1.0,
                "p_value_threshold": 0.05,
                "fdr_threshold": 0.05,
                "case_samples": ["case1", "case2"],
                "control_samples": ["ctrl1", "ctrl2"],
            },
            engine_name="python_scipy_statsmodels_deg_mvp",
            engine_version="0.1",
            dependency_snapshot={
                "packages": {
                    "numpy": {"version": "2.4.6"},
                    "pandas": {"version": "3.0.3"},
                    "scipy": {"version": "1.17.1"},
                    "statsmodels": {"version": "0.14.6"},
                }
            },
            output_artifacts=({"artifact_type": "deg_result_table", "path": str(table_path.relative_to(project_summary.project_root)), "schema": "biomedpilot.deg_result_table.v1"},),
            plot_artifacts=(),
            report_artifacts=(),
            validation_status="passed",
            log_artifacts=({"artifact_type": "formal_deg_run_log", "path": "analysis/formal_deg/formal-ui_run_log.json"},),
            report_ready_eligible=False,
        ),
    )
    register_result(
        project_summary.project_root,
        ResultIndexEntry(result_id="testing-ui", task_run_id="task-testing-ui", task_type="deg", result_semantics="testing_level", validation_status="passed"),
    )

    widget = BioinformaticsResultsBrowserWidget()
    widget.refresh_project(project_summary)

    summary = widget.findChild(QLabel, "formalDegReviewSummary")
    assert summary is not None
    assert "genes=2" in summary.text()
    assert "up=1" in summary.text()
    assert "down=1" in summary.text()
    assert "scipy=1.17.1" in summary.text()
    review_table = widget.findChild(QTableWidget, "formalDegReviewTable")
    assert review_table is not None
    review_text = _table_text(review_table)
    assert "TP53" in review_text
    assert "EGFR" in review_text
    provenance = widget.findChild(QTableWidget, "formalDegReviewProvenanceTable")
    assert provenance is not None
    provenance_text = _table_text(provenance)
    assert "pkg-ui" in provenance_text
    assert "manifests/formal_deg_parameter_confirmation.json" in provenance_text
    assert "results/summaries/result_index.json" in provenance_text
    assert "False" in provenance_text
    downstream = widget.findChild(QLabel, "formalDegReviewDownstream")
    assert downstream is not None
    assert "B9.6 plot artifact" in downstream.text()
    assert "B9.7 report-ready gate" in downstream.text()
    plot_status = widget.findChild(QLabel, "formalDegPlotStatus")
    assert plot_status is not None
    assert "Formal DEG plot gate passed" in plot_status.text()
    plot_button = widget.findChild(QPushButton, "formalDegPlotButton")
    assert plot_button is not None
    assert plot_button.isEnabled()

    exported = widget.export_formal_deg_review_csv()

    assert exported is not None
    assert exported["status"] == "passed"
    assert exported["report_ready_eligible"] is False
    assert Path(str(exported["export_path"])).is_file()
    assert "未生成 report-ready" in widget.status_message()
    plot_result = widget.generate_formal_deg_plot_artifact()
    assert plot_result is not None
    assert plot_result["status"] == "passed"
    assert plot_result["report_ready_eligible"] is False
    assert plot_result["plot_artifact"]["source_result_semantics"] == "formal_computed_result"
    assert "未生成 report-ready" in widget.status_message()


def test_results_browser_ora_review_table_summary_and_exports(qt_app, project_summary) -> None:
    table_path = project_summary.project_root / "results" / "tables" / "ora_ui.tsv"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text(
        "term_id\tterm_name\tgene_set_size\toverlap_count\toverlap_genes\tbackground_size\tselected_gene_count\tp_value\tadjusted_p_value\tenrichment_ratio\tsource_gene_list\twarnings\n"
        "TERM_A\tApoptosis\t2\t2\tTP53;BRCA1\t100\t10\t0.001\t0.003\t10\tselected\t\n",
        encoding="utf-8",
    )
    gene_set_path = project_summary.project_root / "user_data" / "bioinformatics" / "gene_sets" / "custom" / "sets-ui.gmt"
    gene_set_path.parent.mkdir(parents=True, exist_ok=True)
    gene_set_path.write_text("TERM_A\tApoptosis\tTP53\tBRCA1\n", encoding="utf-8")
    gene_set_registry = project_summary.project_root / "user_data" / "bioinformatics" / "gene_sets" / "gene_set_registry.json"
    gene_set_registry.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.gene_set_registry.v1",
                "resources": [
                    {
                        "resource_id": "sets-ui",
                        "name": "sets-ui",
                        "collection_type": "Custom",
                        "species": "unknown",
                        "gene_id_type": "symbol",
                        "status": "available",
                        "local_path": str(gene_set_path.relative_to(project_summary.project_root)),
                        "source": "user_import",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    task_log = project_summary.project_root / "analysis_runs" / "ora" / "ora-run-ui" / "task_run.json"
    task_log.parent.mkdir(parents=True, exist_ok=True)
    task_log.write_text(json.dumps({"task_run_id": "ora-run-ui", "status": "completed"}), encoding="utf-8")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    register_result(
        project_summary.project_root,
        ResultIndexEntry(result_id="formal-ui", task_run_id="formal-ui-run", task_type="deg", result_semantics="formal_computed_result", validation_status="passed"),
    )
    register_result(
        project_summary.project_root,
        {
            "result_id": "ora-ui",
            "task_run_id": "ora-run-ui",
            "task_type": "ora_enrichment",
            "result_semantics": "formal_computed_result",
            "input_package_id": "ora-input-ui",
            "ora_input_id": "ora-input-ui",
            "source_dataset_id": "dataset-ui",
            "source_repository_manifest": "standardized_data/repositories/repository_manifest.json",
            "source_deg_result_id": "formal-ui",
            "source_result_semantics": "formal_computed_result",
            "gene_set_resource_id": "sets-ui",
            "parameters_manifest": {"ora_parameter_id": "ora-ui-params", "test_method": "hypergeometric", "fdr_threshold": 0.05, "selected_gene_rule": "adjusted_p_value_and_abs_log2fc", "background_universe_rule": "source_deg_detected_genes"},
            "engine_name": "python_scipy_statsmodels_ora_mvp",
            "engine_version": "0.1",
            "dependency_snapshot": {"status": "passed", "packages": {"scipy": {"version": "1.17.1"}, "statsmodels": {"version": "0.14.6"}}},
            "output_artifacts": [{"artifact_type": "ora_result_table", "path": str(table_path.relative_to(project_summary.project_root))}],
            "plot_artifacts": [],
            "report_artifacts": [],
            "validation_status": "passed",
            "warnings": [],
            "blockers": [],
            "log_artifacts": [{"artifact_type": "controlled_ora_task_run_log", "path": "analysis_runs/ora/ora-run-ui/task_run.json"}],
            "failure_reason": "",
            "created_at": now,
            "updated_at": now,
            "schema_version": "biomedpilot.result_index_entry.v1",
            "report_ready_eligible": False,
            "migration_status": "native_v2",
        },
    )

    widget = BioinformaticsResultsBrowserWidget()
    widget.refresh_project(project_summary)

    summary = widget.findChild(QLabel, "oraReviewSummary")
    assert summary is not None
    assert "terms=1" in summary.text()
    assert "source=formal-ui" in summary.text()
    assert "scipy=1.17.1" in summary.text()
    table = widget.findChild(QTableWidget, "oraReviewTable")
    assert table is not None
    assert "Apoptosis" in _table_text(table)
    downstream = widget.findChild(QLabel, "oraReviewDownstream")
    assert downstream is not None
    assert "GSEA remains disabled" in downstream.text()
    plot_status = widget.findChild(QLabel, "oraPlotStatus")
    assert plot_status is not None
    assert "ORA plot gate passed" in plot_status.text()
    plot_button = widget.findChild(QPushButton, "oraPlotButton")
    assert plot_button is not None
    assert plot_button.isEnabled()

    exported = widget.export_ora_review_csv()

    assert exported is not None
    assert exported["status"] == "passed"
    assert exported["report_ready_eligible"] is False
    assert Path(str(exported["export_path"])).is_file()
    assert "未生成 report-ready" in widget.status_message()
    plot_result = widget.generate_ora_plot_artifact()
    assert plot_result is not None
    assert plot_result["status"] == "passed"
    assert plot_result["report_ready_eligible"] is False
    assert plot_result["plot_artifact"]["image_artifacts"] == []
    assert plot_result["plot_artifact"]["plot_spec_artifact"]["rendering"] == "spec_only_no_image_dependency"
    assert "未生成 PNG/SVG/PDF" in widget.status_message()
    report_status = widget.findChild(QLabel, "oraReportReadyStatus")
    assert report_status is not None
    assert "ORA report-ready gate passed" in report_status.text()
    report_button = widget.findChild(QPushButton, "oraReportReadyButton")
    assert report_button is not None
    assert report_button.isEnabled()
    report_package = widget.generate_ora_report_ready_package()
    assert report_package is not None
    assert report_package["status"] == "ora_report_ready_package_created"
    assert Path(str(report_package["package_path"])).is_dir()
    assert "未生成 GSEA、survival、完整综合报告或临床结论" in widget.status_message()


def test_results_browser_formal_deg_report_ready_package_gate(qt_app, project_summary) -> None:
    table_path = project_summary.project_root / "results" / "tables" / "formal_deg_report.tsv"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text(
        "feature_id\tgene_symbol\tbase_mean_or_mean_expression\tcase_mean\tcontrol_mean\tlog2_fold_change\tstatistic\tp_value\tadjusted_p_value\tsignificance_label\twarnings\n"
        "g1\tTP53\t10\t12\t4\t1.5\t3.0\t0.001\t0.003\tup\t\n",
        encoding="utf-8",
    )
    parameters = {
        "status": "passed",
        "method": "welch_t_test",
        "log2fc_threshold": 1.0,
        "p_value_threshold": 0.05,
        "fdr_threshold": 0.05,
        "case_samples": ["case1", "case2"],
        "control_samples": ["ctrl1", "ctrl2"],
    }
    dependency = {
        "status": "passed",
        "packages": {
            "numpy": {"version": "2.4.6"},
            "pandas": {"version": "3.0.3"},
            "scipy": {"version": "1.17.1"},
            "statsmodels": {"version": "0.14.6"},
        },
    }
    register_result(
        project_summary.project_root,
        ResultIndexEntry(
            result_id="formal-ui-report",
            task_run_id="task-formal-ui-report",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="pkg-ui-report",
            source_dataset_id="dataset-ui",
            source_repository_manifest="standardized_data/repositories/repository_manifest.json",
            parameters_manifest=parameters,
            engine_name="python_scipy_statsmodels_deg_mvp",
            engine_version="0.1.0",
            dependency_snapshot=dependency,
            output_artifacts=({"artifact_type": "deg_result_table", "path": str(table_path.relative_to(project_summary.project_root)), "schema": "biomedpilot.deg_result_table.v1"},),
            plot_artifacts=(),
            report_artifacts=(),
            validation_status="passed",
            log_artifacts=({"artifact_type": "formal_deg_run_log", "path": "analysis/formal_deg/formal-ui-report_run_log.json"},),
            report_ready_eligible=False,
        ),
    )
    confirmation_path = project_summary.project_root / CONFIRMATION_PATH
    confirmation_path.parent.mkdir(parents=True, exist_ok=True)
    confirmation_path.write_text(
        json.dumps(
            {
                "schema_version": CONFIRMATION_SCHEMA_VERSION,
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "status": "confirmed",
                "confirmed_by_user": True,
                "parameter_manifest": parameters,
                "dependency_snapshot": dependency,
                "output_plan": {
                    "task_run_id": "task-formal-ui-report",
                    "result_id": "formal-ui-report",
                    "result_table_path": "results/tables/formal-ui-report.tsv",
                    "task_run_log_path": "analysis/formal_deg/formal-ui-report_run_log.json",
                    "result_index_registry_path": "results/summaries/result_index.json",
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    plot = create_formal_deg_plot_artifact(project_summary.project_root, result_id="formal-ui-report")
    assert plot["status"] == "passed"

    widget = BioinformaticsResultsBrowserWidget()
    widget.refresh_project(project_summary)

    status = widget.findChild(QLabel, "formalDegReportReadyStatus")
    assert status is not None
    assert "Formal DEG report-ready gate passed" in status.text()
    button = widget.findChild(QPushButton, "formalDegReportReadyButton")
    assert button is not None
    assert button.isEnabled()
    manifest = widget.generate_formal_deg_report_ready_package()

    assert manifest is not None
    assert manifest["status"] == "formal_deg_report_ready_package_created"
    assert manifest["section_scope"] == "formal_deg_only"
    assert manifest["gsea_enabled"] is False
    assert manifest["survival_enabled"] is False
    assert "user_visible_package_path" in manifest
    assert Path(str(manifest["user_visible_package_path"])).is_dir()
    assert "输出位置：" in widget.status_message()
    assert "仅包含 formal DEG section" in widget.status_message()


def test_report_viewer_userized_draft_semantics_and_diagnostics(qt_app, project_summary) -> None:
    imported_path = project_summary.project_root / "results" / "tables" / "imported_deg.csv"
    testing_path = project_summary.project_root / "results" / "tables" / "testing_deg.csv"
    imported_path.parent.mkdir(parents=True, exist_ok=True)
    imported_path.write_text("gene,logFC,P.Value\nTP53,1.2,0.01\n", encoding="utf-8")
    testing_path.write_text("gene,logFC,P.Value\nEGFR,-1.1,0.02\n", encoding="utf-8")
    record_dir = project_summary.project_root / "analysis" / "task_records"
    record_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / "task-draft.json").write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.analysis_task_record.v1",
                "task_id": "task-draft",
                "task_type": "differential_expression",
                "label": "差异表达分析",
                "status": "created",
                "execution": "not_run",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    write_result_index(
        project_summary.project_root,
        [
            {
                "result_name": "Imported DEG table",
                "analysis_type": "differential_expression",
                "file_type": "csv",
                "path": str(imported_path),
                "status": "imported",
                "result_semantics": "imported result",
            },
            {
                "result_name": "Testing DEG preview",
                "analysis_type": "differential_expression",
                "file_type": "csv",
                "path": str(testing_path),
                "status": "testing-level",
                "result_semantics": "testing-level",
            },
        ],
    )

    widget = BioinformaticsReportViewerWidget()
    widget.refresh_project(project_summary)
    generated = widget.generate_report()

    assert generated is not None
    assert "报告草稿" in widget.status_message()
    assert "导入结果" in widget.findChild(QLabel, "reportResultSemantics").text()
    assert "测试级结果" in widget.findChild(QLabel, "reportResultSemantics").text()
    table = widget.findChild(QTableWidget, "reportDraftSectionsTable")
    assert table is not None
    table_text = "\n".join(
        table.item(row, col).text()
        for row in range(table.rowCount())
        for col in range(table.columnCount())
        if table.item(row, col) is not None
    )
    assert "报告草稿" in table_text
    assert "导入和测试级结果必须在报告中保留标签" in table_text
    assert "配置草稿或 dry-run 不等于真实结果" in table_text
    assert str(imported_path) not in table_text
    assert "manifest" not in table_text.lower()
    assert "schema_version" not in table_text
    assert "task-draft" not in table_text

    preview = widget.findChild(QPlainTextEdit, "reportDraftUserPreview")
    assert preview is not None
    preview_text = preview.toPlainText()
    assert "导入结果必须写明来自外部表格" in preview_text
    assert "测试级结果只能作为 Developer Preview" in preview_text
    assert "配置草稿或 dry-run 记录不应写成真实分析结论" in preview_text
    assert str(imported_path) not in preview_text

    diagnostics = widget.findChild(QPlainTextEdit, "reportDeveloperDiagnostics")
    assert diagnostics is not None
    assert not diagnostics.isVisible()
    diagnostics_text = diagnostics.toPlainText()
    assert "report_manifest" in diagnostics_text
    assert "schema_version" in diagnostics_text
    assert str(imported_path) in diagnostics_text
    assert "analysis_center_state" in diagnostics_text

    gate = widget.findChild(QTableWidget, "reportReadyGateTable")
    assert gate is not None
    gate_text = _table_text(gate)
    assert "Report-ready export" in gate_text
    assert "blocked_report_ready_gate" in gate_text
    assert "unverified_testing_exploratory_or_imported_results_present" in gate_text


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
    dep_table = settings.findChild(QTableWidget, "analysisDependencyStatusTable")
    assert dep_table is not None
    dep_text = _table_text(dep_table)
    assert "scipy" in dep_text
    assert "statsmodels" in dep_text
    assert "lifelines" in dep_text
    assert "Detect only" in dep_text
    assert "required_in_packaged_app_for_formal_deg" in dep_text
    assert "安装" not in dep_text


def test_workspace_navigation_reaches_full_stack(qt_app, project_summary) -> None:
    widget = BioinformaticsWorkspaceWidget()

    widget.show_data_source(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsDataSourcePage"
    source = project_summary.project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    widget._data_source_page.register_local_paths([source], strategy="reference", selected_kind="file", summary_key="local_import")
    widget._data_source_page.continue_to_recognition()
    assert widget.current_page_object_name() == "bioinformaticsReadinessDashboardPage"
    widget.show_standardization(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsStandardizedAssetsPage"
    widget.show_workflow_status(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsWorkflowStatusPage"
    widget.show_analysis_tasks(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsAnalysisTaskCenterPage"
    widget.show_deg_config(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsDegConfigPage"
    widget.show_imported_deg_browser(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsImportedDegBrowserPage"
    widget.show_results_browser(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsResultsBrowserPage"
    widget.show_report_viewer(project_summary)
    assert widget.current_page_object_name() == "bioinformaticsReportViewerPage"


def test_standardization_continue_opens_analysis_task_center(qt_app, project_summary) -> None:
    widget = BioinformaticsWorkspaceWidget()
    source = project_summary.project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    workflow_pages.register_acquisition(
        project_summary.project_root,
        source_type="local_import",
        source_label="expression_matrix.tsv",
        strategy="reference",
        selected_paths=[source],
    )
    workflow_pages.run_project_recognition(project_summary.project_root)
    workflow_pages.run_project_readiness(project_summary.project_root)
    workflow_pages.generate_standardized_assets(project_summary.project_root)

    widget.show_standardization(project_summary)
    widget._standardized_assets_page.continue_to_workflow()

    assert widget.current_page_object_name() == "bioinformaticsAnalysisTaskCenterPage"
