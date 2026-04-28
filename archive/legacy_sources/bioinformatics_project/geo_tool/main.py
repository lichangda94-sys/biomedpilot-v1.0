"""PySide6 GUI for Chinese-driven GEO search and bilingual study preview."""

from __future__ import annotations

import csv
import html
import json
import importlib.util
import os
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _bootstrap_qt_environment() -> None:
    """Set Qt plugin paths explicitly before importing PySide6."""

    if sys.platform != "darwin":
        return

    plugins_dir: Path | None = None

    spec = importlib.util.find_spec("PySide6")
    if spec and spec.submodule_search_locations:
        package_dir = Path(list(spec.submodule_search_locations)[0])
        candidate = package_dir / "Qt" / "plugins"
        if candidate.exists():
            plugins_dir = candidate

    if plugins_dir is None:
        project_root = Path(__file__).resolve().parent
        candidates = sorted(project_root.glob(".venv/lib/python*/site-packages/PySide6/Qt/plugins"))
        if candidates:
            plugins_dir = candidates[-1]

    if plugins_dir is None:
        return

    platforms_dir = plugins_dir / "platforms"
    if not platforms_dir.exists():
        return

    lib_dir = plugins_dir.parent / "lib"
    os.environ["QT_PLUGIN_PATH"] = str(plugins_dir)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms_dir)
    if lib_dir.exists():
        os.environ["DYLD_FRAMEWORK_PATH"] = str(lib_dir)
        os.environ["DYLD_LIBRARY_PATH"] = str(lib_dir)
    os.environ.setdefault("QT_QPA_PLATFORM", "cocoa")


_bootstrap_qt_environment()

from PySide6.QtCore import QSettings, QThread, Qt, Signal
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from geo_info_fetcher import GeoInfoFetcher, GeoSearchResult, GeoSeriesInfo
from geo_processing import read_selected_results
from geo_text_processor import GeoTextProcessor, OllamaAPIError
from geo_workflow import WorkflowConfig, run_download_and_process_workflow
from mesh_query_builder import MeshQueryBuilder, QueryBundle
from tcga_gtex import resolve_tcga_gtex_files, search_tcga_gtex
from tcga_gtex.mainline_bridge import (
    build_mainline_summary,
    build_runtime_message,
    build_runtime_action_state,
    first_runtime_candidate,
    records_by_study,
    response_results,
    run_minimal_runtime,
)
from ui.module3_sandbox import Module3SandboxWindow, open_module3_sandbox, workflow_result_dataset_dir
from ui.module3_sandbox_formatters import build_workflow_result_text


@dataclass
class AppState:
    query_bundle: Optional[QueryBundle] = None
    results: List[GeoSeriesInfo] = field(default_factory=list)
    total_count: int = 0
    fetched_all: bool = False
    current_page: int = 1
    selected_gse_ids: set[str] = field(default_factory=set)
    current_fetch_limit: int | None = None
    current_search_strategy: str = "完整检索"


class QueryInputTextEdit(QTextEdit):
    submit_requested = Signal()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (
            event.modifiers() & (Qt.ShiftModifier | Qt.ControlModifier | Qt.AltModifier)
        ):
            event.accept()
            self.submit_requested.emit()
            return
        super().keyPressEvent(event)


SETTINGS_ORG = "Codex"
SETTINGS_APP = "GeoTool"


def app_settings() -> QSettings:
    return QSettings(SETTINGS_ORG, SETTINGS_APP)


def app_stylesheet() -> str:
    return """
        QMainWindow, QWidget {
            background: #f3f6fb;
            color: #243041;
            font-size: 14px;
            font-family: "SF Pro Text", "PingFang SC", "Microsoft YaHei", sans-serif;
        }
        QFrame#headerCard, QFrame#sectionCard, QFrame#primarySectionCard {
            background: #ffffff;
            border: 1px solid #d9e2f0;
            border-radius: 14px;
        }
        QFrame#primarySectionCard {
            border: 1px solid #cfdced;
            background: #ffffff;
        }
        QFrame#headerCard {
            background: #fcfdff;
        }
        QLabel#appTitle {
            font-size: 28px;
            font-weight: 700;
            color: #111827;
            letter-spacing: 0.2px;
        }
        QLabel#appSubtitle {
            color: #4b5563;
            font-size: 13px;
            line-height: 1.4;
        }
        QLabel#sectionTitle {
            font-size: 25px;
            font-weight: 700;
            color: #1f2937;
            padding-bottom: 2px;
        }
        QLabel#sectionDescription {
            color: #6b7280;
            font-size: 14px;
            line-height: 1.45;
        }
        QLabel#resultStatus {
            color: #2b3445;
            font-weight: 600;
            font-size: 15px;
            padding: 4px 0;
        }
        QLabel#detailSummary {
            background: #edf3fa;
            color: #243041;
            border: 1px solid #d6e0ee;
            border-radius: 12px;
            padding: 12px 14px;
            font-weight: 600;
            font-size: 14px;
        }
        QLabel#detailState {
            color: #5b6472;
            font-size: 14px;
            font-weight: 500;
            padding: 2px 0 6px 0;
        }
        QLabel#fieldLabel {
            color: #2b3445;
            font-size: 14px;
            font-weight: 600;
        }
        QLabel#drawerStatus {
            color: #5b6472;
            font-size: 14px;
            font-weight: 500;
        }
        QLabel {
            color: #4b5563;
            font-size: 14px;
        }
        QLabel:disabled {
            color: #a0aec0;
        }
        QLineEdit, QTextEdit, QPlainTextEdit {
            background: #ffffff;
            color: #374151;
            border: 1px solid #d7dfeb;
            border-radius: 10px;
            padding: 7px 9px;
            selection-background-color: #d9e7fb;
            selection-color: #111827;
            font-size: 14px;
            line-height: 1.45;
        }
        QPlainTextEdit#detailCompactBox {
            font-size: 13px;
            padding: 8px 10px;
        }
        QTableWidget {
            background: #ffffff;
            color: #374151;
            alternate-background-color: #f8fbff;
            border: 1px solid #d7dfeb;
            border-radius: 12px;
            padding: 4px;
            gridline-color: #e3eaf4;
            selection-background-color: #dbe7f7;
            selection-color: #111827;
            font-size: 14px;
        }
        QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus, QTableWidget:focus {
            border: 1px solid #4f78b8;
            background: #ffffff;
        }
        QLineEdit[readOnly="true"], QTextEdit[readOnly="true"], QPlainTextEdit[readOnly="true"] {
            background: #fbfcfe;
        }
        QLineEdit::placeholder, QTextEdit::placeholder {
            color: #9ca3af;
        }
        QPlainTextEdit, QTextEdit {
            border-radius: 12px;
        }
        QPushButton, QToolButton {
            background: #ecf2f8;
            color: #243041;
            border: 1px solid #d3deec;
            border-radius: 10px;
            padding: 8px 12px;
            font-weight: 500;
            font-size: 13px;
            min-height: 16px;
        }
        QPushButton:hover, QToolButton:hover {
            background: #e4edf7;
            border: 1px solid #c7d5e7;
        }
        QPushButton:disabled, QToolButton:disabled {
            background: #dde3ec;
            color: #a0aec0;
            border: 1px solid #d5dce6;
        }
        QPushButton#primaryButton {
            background: #315f9e;
            color: white;
            border: 1px solid #315f9e;
            font-size: 14px;
            font-weight: 600;
        }
        QPushButton#primaryButton:hover {
            background: #294f84;
            border: 1px solid #294f84;
        }
        QPushButton#primaryButton:disabled {
            background: #c9d4e4;
            color: #f7f9fc;
            border: 1px solid #c9d4e4;
        }
        QPushButton#secondaryAction {
            background: #edf2f7;
            color: #243041;
            border: 1px solid #d5e0ec;
            font-size: 14px;
            font-weight: 500;
        }
        QPushButton#secondaryAction:hover {
            background: #e6edf5;
        }
        QPushButton#quietButton {
            background: #f5f7fb;
            color: #4b5563;
            border: 1px solid #d9e2f0;
            font-size: 14px;
            font-weight: 500;
        }
        QToolButton#drawerToggle {
            background: #eef3f9;
            color: #243041;
            border: 1px solid #d7e0eb;
            border-radius: 10px;
            padding: 8px 12px;
            font-size: 13px;
            font-weight: 600;
            text-align: left;
        }
        QToolButton#drawerToggle:checked {
            background: #e2ebf6;
            border: 1px solid #c9d8ea;
        }
        QTabWidget::pane {
            border: 1px solid #d9e2f0;
            border-radius: 12px;
            background: #ffffff;
            top: -1px;
        }
        QTabBar::tab {
            background: #eaf0f7;
            color: #4b5563;
            padding: 11px 18px;
            margin-right: 6px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            font-size: 14px;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            color: #1f2937;
            font-weight: 700;
        }
        QHeaderView::section {
            background: #eef3f9;
            color: #243041;
            border: 0;
            border-bottom: 1px solid #d9e2f0;
            padding: 6px 8px;
            font-weight: 600;
            font-size: 14px;
        }
        QTableWidget::item:selected {
            background: #e3edf9;
            color: #111827;
        }
        QTableCornerButton::section {
            background: #eef3f9;
            border: 0;
            border-bottom: 1px solid #d9e2f0;
            border-right: 1px solid #d9e2f0;
        }
        QProgressBar {
            background: #eef2f7;
            color: #4b5563;
            border: 1px solid #d9e2f0;
            border-radius: 9px;
            text-align: center;
            min-height: 18px;
            font-size: 13px;
        }
        QProgressBar::chunk {
            background: #5f86bf;
            border-radius: 8px;
        }
        QSplitter::handle {
            background: #e7edf5;
        }
        QSplitter#resultDetailSplitter::handle {
            background: #dfe7f1;
            width: 7px;
        }
        QScrollBar:vertical {
            background: #f5f7fa;
            width: 10px;
            margin: 4px 0 4px 0;
        }
        QScrollBar::handle:vertical {
            background: #c9d4e4;
            min-height: 28px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
            border: none;
        }
        QStatusBar {
            background: #fcfdff;
            border-top: 1px solid #d9e2f0;
            color: #6b7280;
            font-size: 13px;
        }
    """


def restore_window_geometry(window: QMainWindow, key: str, default_size: tuple[int, int]) -> None:
    settings = app_settings()
    geometry = settings.value(f"{key}/geometry")
    if geometry:
        window.restoreGeometry(geometry)
    else:
        window.resize(*default_size)


def save_window_geometry(window: QMainWindow, key: str) -> None:
    settings = app_settings()
    settings.setValue(f"{key}/geometry", window.saveGeometry())


def compact_text(text: str, limit: int = 30) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return f"{text[:limit - 1]}…"


def experiment_type_zh(text: str) -> str:
    lowered = (text or "").lower()
    mapping = [
        ("expression profiling by array", "芯片表达谱"),
        ("expression profiling by high throughput sequencing", "高通量表达谱"),
        ("non coding rna profiling", "非编码 RNA"),
        ("methylation profiling", "甲基化"),
        ("genome variation profiling", "基因组变异"),
        ("snp genotyping", "SNP 分型"),
        ("other", "其他"),
    ]
    for key, value in mapping:
        if key in lowered:
            return value
    return text or "未注明"


class QueryWorker(QThread):
    finished_signal = Signal(object)
    error_signal = Signal(str)
    progress_signal = Signal(int, str)

    def __init__(self, chinese_query: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.chinese_query = chinese_query

    def run(self) -> None:
        try:
            self.progress_signal.emit(15, "正在分析中文问题并生成检索词")
            builder = MeshQueryBuilder()
            bundle = builder.build_query_bundle(self.chinese_query)
            self.progress_signal.emit(100, "检索词生成完成")
            self.finished_signal.emit(bundle)
        except Exception as exc:
            self.error_signal.emit(f"检索词生成失败：{exc}")


class SearchWorker(QThread):
    finished_signal = Signal(object)
    error_signal = Signal(str)
    progress_signal = Signal(int, str)
    debug_signal = Signal(str)
    pause_state_signal = Signal(bool)

    def __init__(
        self,
        search_queries: list[tuple[str, str]],
        max_results: int | None,
        page_size: int,
        start_offset: int = 0,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.search_queries = search_queries
        self.max_results = max_results
        self.page_size = page_size
        self.start_offset = start_offset
        self._pause_event = threading.Event()
        self._pause_event.set()

    def set_paused(self, paused: bool) -> None:
        if paused:
            self._pause_event.clear()
        else:
            self._pause_event.set()
        self.pause_state_signal.emit(paused)

    def _wait_if_paused(self) -> None:
        self._pause_event.wait()

    def _emit_fetch_progress(self, fetched_count: int, target_count: int) -> None:
        if target_count <= 0:
            return
        progress = min(95, 20 + int(fetched_count * 70 / max(target_count, 1)))
        self.progress_signal.emit(progress, f"正在抓取与解析 GEO 结果（{fetched_count}/{target_count}）")

    def run(self) -> None:
        try:
            self.progress_signal.emit(10, "正在向 GEO 发起检索")
            self.debug_signal.emit(f"[UI] SearchWorker 收到 query 数量: {len(self.search_queries)}")
            fetcher = GeoInfoFetcher(debug_callback=self.debug_signal.emit)
            results = None
            for index, (strategy_label, query_text) in enumerate(self.search_queries, start=1):
                self._wait_if_paused()
                self.progress_signal.emit(
                    min(20 + index * 20, 90),
                    f"正在尝试{strategy_label}",
                )
                self.debug_signal.emit(f"[UI] 尝试 {strategy_label}: {query_text}")
                candidate = fetcher.search_series(
                    query_text,
                    max_results=self.max_results,
                    page_size=self.page_size,
                    start=self.start_offset,
                    pause_callback=self._wait_if_paused,
                    progress_callback=self._emit_fetch_progress,
                )
                candidate.strategy_label = strategy_label
                self.debug_signal.emit(
                    f"[UI] {strategy_label} 完成: total_count={candidate.total_count}, results={len(candidate.results)}"
                )
                results = candidate
                if candidate.total_count > 0 or candidate.results:
                    break
            if results is None:
                raise RuntimeError("未生成任何检索结果对象")
            self.progress_signal.emit(100, "GEO 检索完成")
            self.finished_signal.emit(results)
        except Exception as exc:
            detail = str(exc)
            if any(token in detail for token in ["NameResolutionError", "Failed to resolve", "ConnectionError", "Max retries exceeded"]):
                detail = (
                    "无法连接 NCBI GEO。请检查当前网络、VPN/代理设置，"
                    "如果你是从桌面 GEO Tool.app 启动，可能是 Finder 启动的 GUI 没有继承终端里的代理环境。"
                    f"\n原始错误：{exc}"
                )
            self.error_signal.emit(f"GEO 检索失败：{detail}")


class TextProcessWorker(QThread):
    finished_signal = Signal(object)
    error_signal = Signal(str)
    progress_signal = Signal(int, str)
    pause_state_signal = Signal(bool)

    def __init__(self, series_list: List[GeoSeriesInfo], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.series_list = series_list
        self._pause_event = threading.Event()
        self._pause_event.set()

    def set_paused(self, paused: bool) -> None:
        if paused:
            self._pause_event.clear()
        else:
            self._pause_event.set()
        self.pause_state_signal.emit(paused)

    def run(self) -> None:
        try:
            processor = GeoTextProcessor()
            enriched_list = []
            total = max(len(self.series_list), 1)
            for index, series_info in enumerate(self.series_list, start=1):
                self._pause_event.wait()
                self.progress_signal.emit(
                    int((index - 1) * 100 / total),
                    f"正在翻译与提炼 {series_info.gse_id}（{index}/{total}）",
                )
                enriched_list.append(processor.enrich_series_info(series_info))
                self.progress_signal.emit(
                    int(index * 100 / total),
                    f"已完成 {series_info.gse_id}（{index}/{total}）",
                )
            self.finished_signal.emit(enriched_list)
        except OllamaAPIError as exc:
            self.error_signal.emit(f"Ollama 处理失败：{exc}")
        except Exception as exc:
            self.error_signal.emit(f"中文处理失败：{exc}")


class DownloadProcessWorker(QThread):
    finished_signal = Signal(object)
    error_signal = Signal(str)
    progress_signal = Signal(int, str)
    pause_state_signal = Signal(bool)

    def __init__(
        self,
        selected_items: List[GeoSeriesInfo],
        base_dir: str,
        gpl_gene_col: str,
        query_text: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.selected_items = selected_items
        self.base_dir = base_dir
        self.gpl_gene_col = gpl_gene_col
        self.query_text = query_text
        self._pause_event = threading.Event()
        self._pause_event.set()

    def set_paused(self, paused: bool) -> None:
        if paused:
            self._pause_event.clear()
        else:
            self._pause_event.set()
        self.pause_state_signal.emit(paused)

    def run(self) -> None:
        try:
            batch_dir = build_batch_output_dir(self.base_dir, self.query_text)
            metadata_json, metadata_csv = save_selected_results_metadata(self.selected_items, batch_dir)
            workflow_results = []
            normalized_items = [GeoSeriesInfo.from_search_payload(item) for item in read_selected_results(metadata_json)]
            deduped_items: list[GeoSeriesInfo] = []
            seen_accessions: set[str] = set()
            for item in normalized_items:
                accession = item.gse_id.upper()
                if accession in seen_accessions:
                    continue
                seen_accessions.add(accession)
                deduped_items.append(item)

            total = max(len(deduped_items), 1)
            for index, item in enumerate(deduped_items, start=1):
                self._pause_event.wait()
                self.progress_signal.emit(
                    int((index - 1) * 100 / total),
                    f"正在下载并处理 {item.gse_id}（{index}/{total}）",
                )
                workflow_results.append(
                    run_download_and_process_workflow(
                        WorkflowConfig(
                            accession=item.gse_id,
                            base_dir=str(batch_dir),
                            gpl_gene_col=self.gpl_gene_col,
                        )
                    )
                )
                self.progress_signal.emit(
                    int(index * 100 / total),
                    f"已完成 {item.gse_id}（{index}/{total}）",
                )
            overall_status = "success"
            if any(item.get("status") == "partial_success" for item in workflow_results):
                overall_status = "partial_success"
            self.finished_signal.emit(
                {
                    "status": overall_status,
                    "batch_dir": str(batch_dir),
                    "metadata_json": str(metadata_json),
                    "metadata_csv": str(metadata_csv),
                    "workflow_results": workflow_results,
                    "download_success_count": sum(1 for item in workflow_results if item.get("download_success")),
                    "metadata_parse_success_count": sum(
                        1 for item in workflow_results if item.get("metadata_parse_success")
                    ),
                    "expression_matrix_success_count": sum(
                        1 for item in workflow_results if item.get("expression_matrix_success")
                    ),
                }
            )
        except Exception as exc:
            self.error_signal.emit(f"GSE 下载/处理失败：{exc}")


class TaskWindow(QMainWindow):
    results_updated = Signal(object)

    def __init__(self, selected_items: List[GeoSeriesInfo], query_text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("GEO 翻译与处理任务")
        icon_path = Path(__file__).resolve().parent / "app" / "geo_tool_icon.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(980, 700)
        restore_window_geometry(self, "task_window", (1180, 820))

        self.selected_items = list(selected_items)
        self.query_text = query_text
        self.text_worker: Optional[TextProcessWorker] = None
        self.workflow_worker: Optional[DownloadProcessWorker] = None
        self.workflow_batch_result: Optional[dict] = None
        self.workflow_results_by_accession: dict[str, dict] = {}
        self.workflow_sandbox_window: Optional[Module3SandboxWindow] = None
        self._current_pause_target: Optional[object] = None
        self._task_paused = False

        self._build_ui()
        self._populate_selected_table()

    def closeEvent(self, event) -> None:
        save_window_geometry(self, "task_window")
        super().closeEvent(event)

    def _create_section(self, title: str, description: str = "") -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("sectionCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)
        if description:
            desc = QLabel(description)
            desc.setObjectName("sectionDescription")
            desc.setWordWrap(True)
            layout.addWidget(desc)
        return frame, layout

    def _build_ui(self) -> None:
        self.setStyleSheet(app_stylesheet())
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(10)

        header = QFrame()
        header.setObjectName("headerCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 10, 14, 10)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title = QLabel("翻译与处理任务页")
        title.setObjectName("appTitle")
        subtitle = QLabel("查看、翻译并批量处理已选 GSE。")
        subtitle.setObjectName("appSubtitle")
        subtitle.setWordWrap(True)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout, 1)
        root_layout.addWidget(header)

        progress_section, progress_layout = self._create_section("任务进度", "翻译和下载处理支持暂停与继续。")
        progress_row = QHBoxLayout()
        self.task_status_label = QLabel("当前无任务")
        self.task_status_label.setObjectName("resultStatus")
        self.task_progress_bar = QProgressBar()
        self.task_progress_bar.setRange(0, 100)
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setObjectName("secondaryAction")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause_current_task)
        progress_row.addWidget(self.task_status_label, 1)
        progress_row.addWidget(self.task_progress_bar, 1)
        progress_row.addWidget(self.pause_btn)
        progress_layout.addLayout(progress_row)
        root_layout.addWidget(progress_section)

        content_splitter = QSplitter(Qt.Horizontal)

        left_section, left_layout = self._create_section("任务列表")
        self.selected_table = QTableWidget(0, 4)
        self.selected_table.setHorizontalHeaderLabels(["GSE", "中文类型", "样本数", "中文标题简写"])
        self.selected_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.selected_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.selected_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.selected_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.selected_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.selected_table.verticalHeader().setVisible(False)
        self.selected_table.itemSelectionChanged.connect(self.on_selected_row_changed)
        left_layout.addWidget(self.selected_table)

        action_row = QHBoxLayout()
        self.translate_btn = QPushButton("开始翻译")
        self.translate_btn.setObjectName("primaryButton")
        self.translate_btn.clicked.connect(self.start_text_processing)
        action_row.addWidget(self.translate_btn)
        left_layout.addLayout(action_row)

        right_tabs = QTabWidget()
        detail_page = QWidget()
        detail_layout = QVBoxLayout(detail_page)
        self.detail_summary_label = QLabel("选择一条任务查看详情。")
        self.detail_summary_label.setObjectName("detailSummary")
        self.detail_summary_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_summary_label)
        detail_grid = QGridLayout()
        self.title_en_box = QPlainTextEdit()
        self.title_zh_box = QPlainTextEdit()
        self.summary_en_box = QPlainTextEdit()
        self.summary_zh_box = QPlainTextEdit()
        self.design_en_box = QPlainTextEdit()
        self.design_zh_box = QPlainTextEdit()
        self.brief_box = QPlainTextEdit()
        self.meta_box = QPlainTextEdit()
        for widget in [
            self.title_en_box,
            self.title_zh_box,
            self.summary_en_box,
            self.summary_zh_box,
            self.design_en_box,
            self.design_zh_box,
            self.brief_box,
            self.meta_box,
        ]:
            widget.setReadOnly(True)
        detail_grid.addWidget(QLabel("英文标题"), 0, 0)
        detail_grid.addWidget(QLabel("中文标题"), 0, 1)
        detail_grid.addWidget(self.title_en_box, 1, 0)
        detail_grid.addWidget(self.title_zh_box, 1, 1)
        detail_grid.addWidget(QLabel("英文摘要"), 2, 0)
        detail_grid.addWidget(QLabel("中文摘要"), 2, 1)
        detail_grid.addWidget(self.summary_en_box, 3, 0)
        detail_grid.addWidget(self.summary_zh_box, 3, 1)
        detail_grid.addWidget(QLabel("实验设计英文"), 4, 0)
        detail_grid.addWidget(QLabel("实验设计中文"), 4, 1)
        detail_grid.addWidget(self.design_en_box, 5, 0)
        detail_grid.addWidget(self.design_zh_box, 5, 1)
        detail_grid.addWidget(QLabel("中文简写"), 6, 0)
        detail_grid.addWidget(QLabel("元信息"), 6, 1)
        detail_grid.addWidget(self.brief_box, 7, 0)
        detail_grid.addWidget(self.meta_box, 7, 1)
        detail_layout.addLayout(detail_grid)

        workflow_page = QWidget()
        workflow_layout = QGridLayout(workflow_page)
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("选择下载与处理输出目录")
        self.gpl_gene_col_input = QLineEdit()
        self.gpl_gene_col_input.setPlaceholderText("高级选项：自动识别失败时再手动填写")
        self.choose_output_dir_btn = QPushButton("选择输出目录")
        self.choose_output_dir_btn.setObjectName("secondaryAction")
        self.choose_output_dir_btn.clicked.connect(self.choose_output_dir)
        self.run_workflow_btn = QPushButton("开始下载与处理")
        self.run_workflow_btn.setObjectName("primaryButton")
        self.run_workflow_btn.clicked.connect(self.start_download_process_workflow)
        self.open_module3_action_btn = QPushButton("进入当前 GSE 的模块3工作台")
        self.open_module3_action_btn.setObjectName("secondaryAction")
        self.open_module3_action_btn.setEnabled(False)
        self.open_module3_action_btn.clicked.connect(self.open_current_result_in_module3)
        self.workflow_result_box = QPlainTextEdit()
        self.workflow_result_box.setReadOnly(True)
        workflow_layout.addWidget(QLabel("GPL gene 列（高级/兜底）"), 0, 0)
        workflow_layout.addWidget(self.gpl_gene_col_input, 0, 1)
        workflow_layout.addWidget(QLabel("输出目录"), 1, 0)
        workflow_layout.addWidget(self.output_dir_input, 1, 1)
        workflow_layout.addWidget(self.choose_output_dir_btn, 1, 2)
        workflow_layout.addWidget(self.run_workflow_btn, 2, 0, 1, 3)
        workflow_layout.addWidget(self.workflow_result_box, 3, 0, 1, 3)
        workflow_layout.addWidget(self.open_module3_action_btn, 4, 0, 1, 3)

        log_page = QWidget()
        log_layout = QVBoxLayout(log_page)
        self.status_box = QPlainTextEdit()
        self.status_box.setReadOnly(True)
        log_layout.addWidget(self.status_box)

        right_tabs.addTab(detail_page, "详情")
        right_tabs.addTab(workflow_page, "下载处理")
        right_tabs.addTab(log_page, "日志")

        content_splitter.addWidget(left_section)
        content_splitter.addWidget(right_tabs)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 3)
        content_splitter.setSizes([320, 860])
        root_layout.addWidget(content_splitter)

        self.setCentralWidget(root)
        self.statusBar().showMessage("任务页就绪")

    def log(self, message: str) -> None:
        if hasattr(self, "status_box"):
            self.status_box.appendPlainText(message)
        self.statusBar().showMessage(message, 5000)

    def _set_task_progress(self, task_name: str, value: int, message: str, pause_target: Optional[object] = None) -> None:
        self._current_pause_target = pause_target
        self.task_progress_bar.setValue(max(0, min(100, value)))
        self.task_status_label.setText(f"{task_name}：{message}")
        self.pause_btn.setEnabled(pause_target is not None)
        self.pause_btn.setText("继续" if self._task_paused else "暂停")

    def _finish_task(self, task_name: str, message: str) -> None:
        self.task_progress_bar.setValue(100)
        self.task_status_label.setText(f"{task_name}：{message}")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("暂停")
        self._current_pause_target = None
        self._task_paused = False

    def _reset_task_progress(self, message: str = "当前无任务") -> None:
        self.task_progress_bar.setValue(0)
        self.task_status_label.setText(message)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("暂停")
        self._current_pause_target = None
        self._task_paused = False

    def toggle_pause_current_task(self) -> None:
        if not self._current_pause_target or not hasattr(self._current_pause_target, "set_paused"):
            return
        self._task_paused = not self._task_paused
        self._current_pause_target.set_paused(self._task_paused)
        self.pause_btn.setText("继续" if self._task_paused else "暂停")
        self.task_status_label.setText("任务已暂停，可继续" if self._task_paused else "任务继续执行中")

    def _populate_selected_table(self) -> None:
        self.selected_table.setRowCount(len(self.selected_items))
        for row, item in enumerate(self.selected_items):
            values = [
                item.gse_id,
                experiment_type_zh(item.experiment_type),
                str(item.sample_count),
                compact_text(item.brief_zh or item.title_zh or "待翻译"),
            ]
            for column, value in enumerate(values):
                self.selected_table.setItem(row, column, QTableWidgetItem(value))
        if self.selected_items:
            self.selected_table.selectRow(0)

    def _current_result(self) -> Optional[GeoSeriesInfo]:
        row = self.selected_table.currentRow()
        if row < 0 or row >= len(self.selected_items):
            return None
        return self.selected_items[row]

    def on_selected_row_changed(self) -> None:
        info = self._current_result()
        if not info:
            self._refresh_module3_action_state()
            return
        self.detail_summary_label.setText(
            f"{info.gse_id} | {experiment_type_zh(info.experiment_type)} | {info.sample_count} 样本"
        )
        self.title_en_box.setPlainText(info.title_en)
        self.title_zh_box.setPlainText(info.title_zh or "尚未翻译")
        self.summary_en_box.setPlainText(info.summary_en)
        self.summary_zh_box.setPlainText(info.summary_zh or "尚未翻译")
        self.design_en_box.setPlainText(info.overall_design_en)
        self.design_zh_box.setPlainText(info.overall_design_zh or "尚未翻译")
        self.brief_box.setPlainText(info.brief_zh or "尚未提炼")
        self.meta_box.setPlainText(
            "\n".join(
                [
                    f"GSE: {info.gse_id}",
                    f"类型: {experiment_type_zh(info.experiment_type)}",
                    f"样本数: {info.sample_count}",
                    f"平台: {info.platform}",
                    f"物种: {info.organism}",
                    f"URL: {info.geo_url}",
                ]
            )
        )
        self._refresh_module3_action_state()

    def _current_workflow_result(self) -> Optional[dict]:
        info = self._current_result()
        if info is None:
            return None
        return self.workflow_results_by_accession.get(info.gse_id.upper())

    def _refresh_module3_action_state(self) -> None:
        info = self._current_result()
        workflow_result = self._current_workflow_result()
        dataset_dir = workflow_result_dataset_dir(workflow_result)

        if info is None or workflow_result is None or not dataset_dir:
            self.open_module3_action_btn.setEnabled(False)
            self.open_module3_action_btn.setText("进入当前 GSE 的模块3工作台")
            return

        self.open_module3_action_btn.setEnabled(True)
        self.open_module3_action_btn.setText(f"进入 {info.gse_id} 的模块3工作台")

    def open_current_result_in_module3(self) -> None:
        workflow_result = self._current_workflow_result()
        dataset_dir = workflow_result_dataset_dir(workflow_result)
        if not dataset_dir:
            QMessageBox.information(self, "提示", "当前结果还没有可交给模块3的工作目录。")
            return

        self.workflow_sandbox_window = open_module3_sandbox(initial_dir=dataset_dir)
        self.workflow_sandbox_window.raise_()
        self.workflow_sandbox_window.activateWindow()
        accession = workflow_result.get("accession") if isinstance(workflow_result, dict) else ""
        self.log(f"已从 workflow 结果进入模块3工作台：{accession or dataset_dir}")

    def start_text_processing(self) -> None:
        if not self.selected_items:
            QMessageBox.information(self, "提示", "当前没有可翻译的 GSE。")
            return
        self.text_worker = TextProcessWorker(self.selected_items, self)
        self.text_worker.finished_signal.connect(self.on_text_processed)
        self.text_worker.error_signal.connect(self.on_worker_error)
        self.text_worker.progress_signal.connect(
            lambda value, message: self._set_task_progress("中文翻译与提炼", value, message, pause_target=self.text_worker)
        )
        self._task_paused = False
        self.text_worker.start()
        self._set_task_progress("中文翻译与提炼", 0, "任务已启动", pause_target=self.text_worker)
        self.log(f"开始中文翻译与提炼，共 {len(self.selected_items)} 条。")

    def on_text_processed(self, enriched_list: List[GeoSeriesInfo]) -> None:
        self.selected_items = enriched_list
        self._populate_selected_table()
        self.on_selected_row_changed()
        self.results_updated.emit(enriched_list)
        self._finish_task("中文翻译与提炼", f"共处理 {len(enriched_list)} 条")
        self.log(f"中文翻译与提炼完成，共处理 {len(enriched_list)} 条。")

    def choose_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择工作流输出目录")
        if folder:
            self.output_dir_input.setText(folder)
            self.log(f"已选择工作流输出目录：{folder}")

    def start_download_process_workflow(self) -> None:
        if not self.selected_items:
            QMessageBox.information(self, "提示", "当前没有可处理的 GSE。")
            return
        output_dir = self.output_dir_input.text().strip()
        if not output_dir:
            QMessageBox.information(self, "提示", "请先选择输出目录。")
            return
        self.workflow_batch_result = None
        self.workflow_results_by_accession = {}
        self._refresh_module3_action_state()
        self.workflow_worker = DownloadProcessWorker(
            selected_items=self.selected_items,
            base_dir=output_dir,
            gpl_gene_col=self.gpl_gene_col_input.text().strip() or "",
            query_text=self.query_text or "geo_query",
            parent=self,
        )
        self.workflow_worker.finished_signal.connect(self.on_workflow_finished)
        self.workflow_worker.error_signal.connect(self.on_worker_error)
        self.workflow_worker.progress_signal.connect(
            lambda value, message: self._set_task_progress("下载与处理", value, message, pause_target=self.workflow_worker)
        )
        self._task_paused = False
        self.workflow_worker.start()
        self._set_task_progress("下载与处理", 0, "任务已启动", pause_target=self.workflow_worker)
        self.log(f"开始执行下载与处理工作流，共 {len(self.selected_items)} 条。")

    def on_workflow_finished(self, result: dict) -> None:
        self.workflow_batch_result = result
        self.workflow_results_by_accession = {
            workflow_result.get("accession", "").upper(): workflow_result
            for workflow_result in result.get("workflow_results", [])
            if workflow_result.get("accession")
        }
        self.workflow_result_box.setPlainText(build_workflow_result_text(result))
        self._refresh_module3_action_state()
        self._finish_task("下载与处理", f"共处理 {len(result.get('workflow_results', []))} 条")
        self.log(f"下载与处理工作流完成，共处理 {len(result.get('workflow_results', []))} 条。")

    def on_worker_error(self, message: str) -> None:
        self._reset_task_progress(f"任务失败：{message}")
        QMessageBox.warning(self, "错误", message)
        self.log(message)

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("中文驱动 GEO 数据集检索与预筛选工具")
        icon_path = Path(__file__).resolve().parent / "app" / "geo_tool_icon.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(1180, 760)
        restore_window_geometry(self, "main_window", (1360, 860))
        self.state = AppState()
        self.query_worker: Optional[QueryWorker] = None
        self.search_worker: Optional[SearchWorker] = None
        self.task_window: Optional[TaskWindow] = None
        self.sandbox_window: Optional[Module3SandboxWindow] = None
        self._updating_table = False
        self._current_task_name: str | None = None
        self._current_pause_target: Optional[object] = None
        self._task_paused = False
        self.module4_search_result: dict | None = None
        self.module4_resolve_result: dict | None = None
        self.module4_records_by_study: dict[str, list[dict]] = {}
        self.module4_runtime_result: dict | None = None
        self._build_ui()

    def closeEvent(self, event) -> None:
        save_window_geometry(self, "main_window")
        super().closeEvent(event)

    def _create_section(self, title: str, description: str = "") -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("sectionCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)

        if description:
            description_label = QLabel(description)
            description_label.setObjectName("sectionDescription")
            description_label.setWordWrap(True)
            layout.addWidget(description_label)

        return frame, layout

    def _apply_styles(self) -> None:
        self.setStyleSheet(app_stylesheet())

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(10)
        self._apply_styles()

        header = QFrame()
        header.setObjectName("headerCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(12)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title_label = QLabel("GEO 智能检索工作台")
        title_label.setObjectName("appTitle")
        subtitle_label = QLabel("输入问题，生成检索词并筛选 GEO 数据集。")
        subtitle_label.setObjectName("appSubtitle")
        subtitle_label.setWordWrap(True)
        title_block.addWidget(title_label)
        title_block.addWidget(subtitle_label)

        header_layout.addLayout(title_block, 1)
        root_layout.addWidget(header)

        progress_card, progress_layout = self._create_section("任务进度")
        progress_row = QHBoxLayout()
        progress_row.setSpacing(12)
        self.task_status_label = QLabel("当前无任务")
        self.task_status_label.setObjectName("resultStatus")
        self.task_progress_bar = QProgressBar()
        self.task_progress_bar.setRange(0, 100)
        self.task_progress_bar.setValue(0)
        self.task_progress_bar.setTextVisible(True)
        self.search_btn = QPushButton("检索 GEO")
        self.search_btn.setObjectName("primaryButton")
        self.search_btn.setEnabled(False)
        self.module4_search_btn = QPushButton("检索 TCGA/GTEx")
        self.module4_search_btn.setObjectName("secondaryAction")
        self.translate_btn = QPushButton("进入翻译与处理页面")
        self.translate_btn.setObjectName("secondaryAction")
        self.translate_btn.setEnabled(False)
        self.sandbox_btn = QPushButton("打开模块3测试台")
        self.sandbox_btn.setObjectName("secondaryAction")
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setObjectName("secondaryAction")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause_current_task)
        progress_row.addWidget(self.task_status_label, 1)
        progress_row.addWidget(self.task_progress_bar, 1)
        progress_row.addWidget(self.search_btn)
        progress_row.addWidget(self.module4_search_btn)
        progress_row.addWidget(self.translate_btn)
        progress_row.addWidget(self.sandbox_btn)
        progress_row.addWidget(self.pause_btn)
        progress_layout.addLayout(progress_row)

        search_config_row = QGridLayout()
        self.max_results_input = QLineEdit("1000")
        self.max_results_input.setPlaceholderText("1000 或 all")
        self.max_results_input.setMaximumWidth(68)
        self.page_size_input = QLineEdit("20")
        self.page_size_input.setPlaceholderText("每页 20")
        self.page_size_input.setMaximumWidth(54)
        search_config_row.addWidget(QLabel("结果数"), 0, 0)
        search_config_row.addWidget(self.max_results_input, 0, 1)
        search_config_row.addWidget(QLabel("每页"), 0, 2)
        search_config_row.addWidget(self.page_size_input, 0, 3)
        search_config_row.setHorizontalSpacing(10)
        search_config_row.setVerticalSpacing(10)

        input_section, input_layout = self._create_section("1. 研究问题")
        self.query_input = QueryInputTextEdit()
        self.query_input.setMaximumHeight(64)
        self.query_input.setPlaceholderText("例如：甲状腺嗜酸细胞性肿瘤的转录组比较，重点看人群和肥胖相关研究")
        input_layout.addWidget(self.query_input)
        input_layout.addLayout(search_config_row)
        input_action_row = QHBoxLayout()
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setObjectName("quietButton")
        self.build_query_btn = QPushButton("生成检索词")
        self.build_query_btn.setObjectName("primaryButton")
        input_action_row.addWidget(self.clear_btn)
        input_action_row.addStretch(1)
        input_action_row.addWidget(self.build_query_btn)
        input_layout.addLayout(input_action_row)

        query_section, query_layout = self._create_section("2. 检索式与命中主题")
        self.query_drawer_status = QLabel("尚未生成。")
        self.query_drawer_status.setObjectName("drawerStatus")
        query_layout.addWidget(self.query_drawer_status)
        self.query_drawer_toggle = QToolButton()
        self.query_drawer_toggle.setObjectName("drawerToggle")
        self.query_drawer_toggle.setText("查看检索词")
        self.query_drawer_toggle.setCheckable(True)
        self.query_drawer_toggle.setEnabled(False)
        self.query_drawer_toggle.toggled.connect(self._toggle_query_drawer)
        query_layout.addWidget(self.query_drawer_toggle)

        self.query_drawer_container = QWidget()
        query_drawer_layout = QVBoxLayout(self.query_drawer_container)
        query_drawer_layout.setContentsMargins(0, 0, 0, 0)
        query_drawer_layout.setSpacing(10)
        self.full_query_label = QLabel("完整 GEO 检索式")
        self.full_query_label.setObjectName("fieldLabel")
        self.full_query_box = QPlainTextEdit()
        self.full_query_box.setReadOnly(True)
        self.match_label = QLabel("主题命中")
        self.match_label.setObjectName("fieldLabel")
        self.match_box = QPlainTextEdit()
        self.match_box.setReadOnly(True)
        self.search_query_label = QLabel("英文核心检索")
        self.search_query_label.setObjectName("fieldLabel")
        self.search_query_box = QPlainTextEdit()
        self.search_query_box.setReadOnly(True)
        query_drawer_layout.addWidget(self.full_query_label)
        query_drawer_layout.addWidget(self.full_query_box)
        query_drawer_layout.addWidget(self.match_label)
        query_drawer_layout.addWidget(self.match_box)
        query_drawer_layout.addWidget(self.search_query_label)
        query_drawer_layout.addWidget(self.search_query_box)
        self.query_drawer_container.setVisible(False)
        query_layout.addWidget(self.query_drawer_container)

        module4_section, module4_layout = self._create_section(
            "TCGA/GTEx 分流",
            "可选查询 TCGA/GTEx 候选；只走 main.py 分流，不进入 GEO workflow。",
        )
        self.module4_result_box = QPlainTextEdit()
        self.module4_result_box.setReadOnly(True)
        self.module4_result_box.setMaximumHeight(220)
        self.module4_result_box.setPlainText("尚未执行 TCGA/GTEx 查询。")
        self.module4_runtime_btn = QPushButton("运行 TCGA/GTEx 最小 runtime")
        self.module4_runtime_btn.setObjectName("secondaryAction")
        self.module4_runtime_btn.setEnabled(False)
        self.module4_runtime_btn.setToolTip("先执行 TCGA/GTEx 查询分流。")
        module4_layout.addWidget(self.module4_result_box)
        module4_layout.addWidget(self.module4_runtime_btn)

        result_section, result_layout = self._create_section("3. GEO 结果列表")
        result_section.setObjectName("primarySectionCard")
        result_toolbar = QHBoxLayout()
        self.result_status_label = QLabel("总命中: 0 | 已抓取: 0 | 是否抓完整: 否")
        self.result_status_label.setObjectName("resultStatus")
        self.prev_page_btn = QPushButton("上一页")
        self.next_page_btn = QPushButton("下一页")
        self.fetch_more_btn = QPushButton("继续抓取更多")
        self.fetch_all_btn = QPushButton("抓取全部")
        self.select_page_btn = QPushButton("勾选当前页")
        self.clear_selection_btn = QPushButton("清空勾选")
        self.prev_page_btn.setObjectName("secondaryAction")
        self.next_page_btn.setObjectName("secondaryAction")
        self.fetch_more_btn.setObjectName("secondaryAction")
        self.fetch_all_btn.setObjectName("secondaryAction")
        self.select_page_btn.setObjectName("secondaryAction")
        self.clear_selection_btn.setObjectName("quietButton")
        result_toolbar.addWidget(self.result_status_label)
        result_toolbar.addStretch(1)
        result_toolbar.addWidget(self.prev_page_btn)
        result_toolbar.addWidget(self.next_page_btn)
        result_toolbar.addWidget(self.fetch_more_btn)
        result_toolbar.addWidget(self.fetch_all_btn)
        result_toolbar.addWidget(self.select_page_btn)
        result_toolbar.addWidget(self.clear_selection_btn)
        result_layout.addLayout(result_toolbar)

        self.result_table = QTableWidget(0, 5)
        self.result_table.setHorizontalHeaderLabels(["选择", "GSE编号", "中文类型", "样本数", "中文标题简写"])
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result_table.setMouseTracking(True)
        self.result_table.viewport().setMouseTracking(True)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setWordWrap(False)
        self.result_table.setAlternatingRowColors(True)
        compact_font = self.result_table.font()
        compact_font.setPointSize(max(compact_font.pointSize() - 1, 10))
        self.result_table.setFont(compact_font)
        self.result_table.verticalHeader().setDefaultSectionSize(28)
        result_layout.addWidget(self.result_table)

        detail_page = QWidget()
        detail_page.setObjectName("sectionCard")
        detail_layout = QVBoxLayout(detail_page)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(12)
        detail_header = QHBoxLayout()
        detail_title = QLabel("详情查看")
        detail_title.setObjectName("sectionTitle")
        self.close_detail_btn = QPushButton("收起详情")
        self.close_detail_btn.setObjectName("quietButton")
        self.close_detail_btn.clicked.connect(self._hide_detail_drawer)
        detail_header.addWidget(detail_title)
        detail_header.addStretch(1)
        detail_header.addWidget(self.close_detail_btn)
        detail_layout.addLayout(detail_header)
        self.detail_summary_label = QLabel("点击某条 GSE 后，这里会显示完整详情。")
        self.detail_summary_label.setObjectName("detailSummary")
        self.detail_summary_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_summary_label)
        self.detail_state_label = QLabel("当前未打开详情。")
        self.detail_state_label.setObjectName("detailState")
        self.detail_state_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_state_label)

        detail_grid = QGridLayout()
        detail_grid.setHorizontalSpacing(12)
        detail_grid.setVerticalSpacing(10)
        self.title_en_box = QPlainTextEdit()
        self.title_zh_box = QPlainTextEdit()
        self.summary_en_box = QPlainTextEdit()
        self.summary_zh_box = QPlainTextEdit()
        self.design_en_box = QPlainTextEdit()
        self.design_zh_box = QPlainTextEdit()
        self.brief_en_box = QPlainTextEdit()
        self.brief_zh_box = QPlainTextEdit()
        for widget in [
            self.title_en_box,
            self.title_zh_box,
            self.summary_en_box,
            self.summary_zh_box,
            self.design_en_box,
            self.design_zh_box,
            self.brief_en_box,
            self.brief_zh_box,
        ]:
            widget.setReadOnly(True)
            widget.setObjectName("detailCompactBox")
        for widget in [self.title_en_box, self.title_zh_box, self.brief_en_box, self.brief_zh_box]:
            widget.setMaximumHeight(92)
        for widget in [self.summary_en_box, self.summary_zh_box, self.design_en_box, self.design_zh_box]:
            widget.setMinimumHeight(132)
        self.title_en_label = QLabel("英文标题")
        self.title_zh_label = QLabel("中文标题")
        self.summary_en_label = QLabel("英文摘要")
        self.summary_zh_label = QLabel("中文摘要")
        self.design_en_label = QLabel("英文 overall design")
        self.design_zh_label = QLabel("中文 overall design")
        self.brief_en_label = QLabel("英文一句话提炼")
        self.brief_zh_label = QLabel("中文一句话提炼")
        for label in [
            self.title_en_label,
            self.title_zh_label,
            self.summary_en_label,
            self.summary_zh_label,
            self.design_en_label,
            self.design_zh_label,
            self.brief_en_label,
            self.brief_zh_label,
        ]:
            label.setObjectName("fieldLabel")
        detail_grid.addWidget(self.title_en_label, 0, 0)
        detail_grid.addWidget(self.title_zh_label, 0, 1)
        detail_grid.addWidget(self.title_en_box, 1, 0)
        detail_grid.addWidget(self.title_zh_box, 1, 1)
        detail_grid.addWidget(self.summary_en_label, 2, 0)
        detail_grid.addWidget(self.summary_zh_label, 2, 1)
        detail_grid.addWidget(self.summary_en_box, 3, 0)
        detail_grid.addWidget(self.summary_zh_box, 3, 1)
        detail_grid.addWidget(self.design_en_label, 4, 0)
        detail_grid.addWidget(self.design_zh_label, 4, 1)
        detail_grid.addWidget(self.design_en_box, 5, 0)
        detail_grid.addWidget(self.design_zh_box, 5, 1)
        detail_grid.addWidget(self.brief_en_label, 6, 0)
        detail_grid.addWidget(self.brief_zh_label, 6, 1)
        detail_grid.addWidget(self.brief_en_box, 7, 0)
        detail_grid.addWidget(self.brief_zh_box, 7, 1)
        detail_layout.addLayout(detail_grid)
        detail_page.setVisible(False)
        self.detail_page = detail_page

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)
        left_layout.addWidget(input_section)
        left_layout.addWidget(query_section)
        left_layout.addWidget(module4_section)
        left_layout.addWidget(progress_card)
        left_layout.addStretch(1)

        result_detail_splitter = QSplitter(Qt.Horizontal)
        result_detail_splitter.setObjectName("resultDetailSplitter")
        result_detail_splitter.addWidget(result_section)
        result_detail_splitter.addWidget(detail_page)
        result_detail_splitter.setStretchFactor(0, 5)
        result_detail_splitter.setStretchFactor(1, 0)
        result_detail_splitter.setSizes([1120, 0])
        self.result_detail_splitter = result_detail_splitter

        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(result_detail_splitter)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 3)
        content_splitter.setSizes([360, 1000])

        root_layout.addWidget(content_splitter)
        self.setCentralWidget(root)
        self.statusBar().showMessage("就绪")

        self.build_query_btn.clicked.connect(self.start_query_build)
        self.search_btn.clicked.connect(self.start_search)
        self.module4_search_btn.clicked.connect(self.start_module4_search)
        self.module4_runtime_btn.clicked.connect(self.run_module4_runtime_action)
        self.translate_btn.clicked.connect(self.open_task_window)
        self.sandbox_btn.clicked.connect(self.open_module3_sandbox)
        self.clear_btn.clicked.connect(self.clear_all)
        self.query_input.submit_requested.connect(self.start_query_build)
        self.result_table.itemSelectionChanged.connect(self.on_result_selected)
        self.result_table.itemChanged.connect(self.on_table_item_changed)
        self.result_table.cellEntered.connect(self.on_result_hovered)
        self.prev_page_btn.clicked.connect(self.show_previous_page)
        self.next_page_btn.clicked.connect(self.show_next_page)
        self.fetch_more_btn.clicked.connect(self.start_fetch_more)
        self.fetch_all_btn.clicked.connect(self.start_fetch_all)
        self.select_page_btn.clicked.connect(self.select_current_page)
        self.clear_selection_btn.clicked.connect(self.clear_checked_results)

        self.status_box = QPlainTextEdit()
        self.status_box.setReadOnly(True)

        processor = GeoTextProcessor()
        if not processor.is_available():
            self.log("未检测到 Ollama API。你仍可先完成 GEO 检索，翻译按钮将在模型可用时使用。")

        self._update_result_status()

    def log(self, message: str) -> None:
        self.status_box.appendPlainText(message)
        self.statusBar().showMessage(message, 5000)

    def _toggle_query_drawer(self, checked: bool) -> None:
        self.query_drawer_container.setVisible(checked)
        self.query_drawer_toggle.setText("收起检索词" if checked else "查看检索词")

    @staticmethod
    def _match_terms_to_query(matches: tuple) -> str:
        groups = []
        for match in matches:
            joined = " OR ".join(f'"{term}"' for term in match.english_terms)
            groups.append(f"({joined})")
        return " AND ".join(groups)

    def _build_search_strategies(self, bundle: QueryBundle) -> list[tuple[str, str]]:
        strategies: list[tuple[str, str]] = []
        if bundle.full_geo_query:
            strategies.append(("完整检索", bundle.full_geo_query))

        disease_query = self._match_terms_to_query(bundle.disease_matches)
        population_query = self._match_terms_to_query(bundle.population_matches)
        exposure_query = self._match_terms_to_query(bundle.exposure_matches)
        treatment_query = self._match_terms_to_query(bundle.treatment_matches)
        molecular_query = self._match_terms_to_query(bundle.molecular_matches)

        relaxed_parts = [part for part in [disease_query, molecular_query] if part]
        relaxed_query = " AND ".join(relaxed_parts)
        if not relaxed_query:
            relaxed_query = disease_query or molecular_query
        if relaxed_query:
            relaxed_full = f"({relaxed_query}) AND GSE[ETYP] AND (Homo sapiens[Organism] OR Mus musculus[Organism] OR Rattus norvegicus[Organism])"
            if relaxed_full not in {query for _, query in strategies}:
                strategies.append(("放宽检索", relaxed_full))

        if disease_query:
            disease_only = f"({disease_query}) AND GSE[ETYP] AND (Homo sapiens[Organism] OR Mus musculus[Organism] OR Rattus norvegicus[Organism])"
            if disease_only not in {query for _, query in strategies}:
                strategies.append(("疾病兜底检索", disease_only))

        if not strategies and bundle.search_query_en:
            strategies.append(("完整检索", bundle.search_query_en))
        return strategies

    def _set_task_progress(
        self,
        task_name: str,
        value: int,
        message: str,
        *,
        pausable: bool = False,
        pause_target: Optional[object] = None,
    ) -> None:
        self._current_task_name = task_name
        self._current_pause_target = pause_target if pausable else None
        self.task_progress_bar.setValue(max(0, min(100, value)))
        self.task_status_label.setText(f"{task_name}：{message}")
        self.pause_btn.setEnabled(pausable)
        self.pause_btn.setText("继续" if self._task_paused else "暂停")

    def _reset_task_progress(self, message: str = "当前无任务") -> None:
        self._current_task_name = None
        self._current_pause_target = None
        self._task_paused = False
        self.task_progress_bar.setValue(0)
        self.task_status_label.setText(message)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("暂停")

    def _mark_task_complete(self, task_name: str, message: str) -> None:
        self.task_progress_bar.setValue(100)
        self.task_status_label.setText(f"{task_name}：{message}")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("暂停")
        self._current_task_name = None
        self._current_pause_target = None
        self._task_paused = False

    def toggle_pause_current_task(self) -> None:
        if not self._current_pause_target or not hasattr(self._current_pause_target, "set_paused"):
            return
        self._task_paused = not self._task_paused
        self._current_pause_target.set_paused(self._task_paused)
        if self._current_task_name:
            suffix = "已暂停，可继续" if self._task_paused else "继续执行中"
            self.task_status_label.setText(f"{self._current_task_name}：{suffix}")
        self.pause_btn.setText("继续" if self._task_paused else "暂停")

    def clear_all(self) -> None:
        self.query_input.clear()
        self.search_query_box.clear()
        self.full_query_box.clear()
        self.match_box.clear()
        self.query_drawer_status.setText("尚未生成。")
        self.query_drawer_toggle.setChecked(False)
        self.query_drawer_toggle.setEnabled(False)
        self.query_drawer_container.setVisible(False)
        self.result_table.setRowCount(0)
        if hasattr(self, "status_box"):
            self.status_box.clear()
        self.state = AppState()
        self.search_btn.setEnabled(False)
        self.translate_btn.setEnabled(False)
        self._clear_detail()
        self._update_result_status()
        self._reset_task_progress()
        self.statusBar().showMessage("已清空当前会话", 5000)

        self.module4_search_result = None
        self.module4_resolve_result = None
        self.module4_records_by_study = {}
        self.module4_runtime_result = None
        self.module4_result_box.setPlainText("尚未执行 TCGA/GTEx 查询。")
        self.module4_runtime_btn.setEnabled(False)
        self.module4_runtime_btn.setText("运行 TCGA/GTEx 最小 runtime")
        self.module4_runtime_btn.setToolTip("先执行 TCGA/GTEx 查询分流。")

    def open_module3_sandbox(self) -> None:
        self.sandbox_window = Module3SandboxWindow()
        self.sandbox_window.show()
        self.sandbox_window.raise_()
        self.sandbox_window.activateWindow()
        self.log("已打开模块3测试台。")

    def _parse_max_results(self) -> int | None:
        raw = self.max_results_input.text().strip().lower()
        if not raw:
            return 1000
        if raw == "all":
            return None
        value = int(raw)
        if value <= 0:
            raise ValueError("max_results 必须是正整数或 all")
        return value

    def _parse_page_size(self) -> int:
        raw = self.page_size_input.text().strip()
        value = int(raw or "20")
        if value <= 0:
            raise ValueError("page_size 必须是正整数")
        return value

    def start_module4_search(self) -> None:
        query_text = self.query_input.toPlainText().strip()
        if not query_text and self.state.query_bundle:
            query_text = self.state.query_bundle.search_query_en.strip()
        if not query_text:
            QMessageBox.information(self, "提示", "请先输入研究问题。")
            return

        self._set_task_progress("TCGA/GTEx 分流", 10, "查询与文件候选解析中")
        self.log(f"[Module4] 开始 TCGA/GTEx 查询分流: {query_text}")
        try:
            search_result = search_tcga_gtex(query_text)
            resolve_result = resolve_tcga_gtex_files(query_text)
        except Exception as exc:
            message = f"TCGA/GTEx 查询分流失败：{exc}"
            self.module4_search_result = None
            self.module4_resolve_result = None
            self.module4_records_by_study = {}
            self.module4_runtime_btn.setEnabled(False)
            self.module4_result_box.setPlainText(message)
            self._reset_task_progress(message)
            QMessageBox.warning(self, "TCGA/GTEx 分流失败", message)
            self.log(f"[Module4] {message}")
            return

        records = response_results(resolve_result)
        self.module4_search_result = search_result
        self.module4_resolve_result = resolve_result
        self.module4_records_by_study = records_by_study(records)
        self.module4_runtime_result = None
        self.module4_result_box.setPlainText(build_mainline_summary(search_result, resolve_result))
        runtime_state = build_runtime_action_state(self.module4_records_by_study)
        self.module4_runtime_btn.setEnabled(bool(runtime_state["enabled"]))
        self.module4_runtime_btn.setText(runtime_state["button_text"])
        self.module4_runtime_btn.setToolTip(runtime_state["help_text"])
        self._mark_task_complete("TCGA/GTEx 分流", f"解析到 {len(records)} 个文件候选")
        self.log(
            "[Module4] 查询分流完成："
            f"study_groups={len(self.module4_records_by_study)}, file_candidates={len(records)}, "
            f"runtime_hint={runtime_state['help_text']}"
        )

    def run_module4_runtime_action(self) -> None:
        candidate = first_runtime_candidate(self.module4_records_by_study)
        if candidate is None:
            QMessageBox.information(self, "提示", "当前没有可用于 TCGA/GTEx runtime 的文件候选。")
            return
        study_id, records = candidate
        output_dir = QFileDialog.getExistingDirectory(self, "选择 TCGA/GTEx runtime 输出目录")
        if not output_dir:
            return

        self._set_task_progress("TCGA/GTEx runtime", 25, f"处理 {study_id}")
        self.log(f"[Module4] 启动最小 runtime：study_id={study_id}, output_dir={output_dir}")
        result = run_minimal_runtime(study_id, output_dir, records)
        self.module4_runtime_result = result
        current_text = self.module4_result_box.toPlainText().rstrip()
        runtime_message = build_runtime_message(result)
        self.module4_result_box.setPlainText(f"{current_text}\n{runtime_message}".strip())

        if result.get("status") == "success":
            self._mark_task_complete("TCGA/GTEx runtime", "完成")
            QMessageBox.information(self, "TCGA/GTEx runtime", runtime_message)
        else:
            self._reset_task_progress(f"TCGA/GTEx runtime 失败：{result.get('stage', 'unknown')}")
            QMessageBox.warning(self, "TCGA/GTEx runtime 失败", runtime_message)
        self.log(f"[Module4] runtime 结果：status={result.get('status')}, stage={result.get('stage')}")

    def start_query_build(self) -> None:
        chinese_query = self.query_input.toPlainText().strip()
        if not chinese_query:
            QMessageBox.information(self, "提示", "请先输入中文问题。")
            return

        self.query_worker = QueryWorker(chinese_query, self)
        self.query_worker.finished_signal.connect(self.on_query_built)
        self.query_worker.error_signal.connect(self.on_worker_error)
        self.query_worker.progress_signal.connect(
            lambda value, message: self._set_task_progress("检索词生成", value, message)
        )
        self.query_worker.start()
        self._set_task_progress("检索词生成", 5, "任务已启动")
        self.log("开始生成检索词。")

    def on_query_built(self, bundle: QueryBundle) -> None:
        self.state.query_bundle = bundle
        self.search_query_box.setPlainText(bundle.search_query_en)
        self.full_query_box.setPlainText(bundle.full_geo_query)
        self.match_box.setPlainText(self._format_matches(bundle))
        self.query_drawer_status.setText("检索词已生成。点击下方按钮按需展开查看。")
        self.query_drawer_toggle.setEnabled(True)
        self.query_drawer_toggle.setChecked(False)
        self.search_btn.setEnabled(bool(bundle.full_geo_query))
        self._mark_task_complete("检索词生成", "检索词生成完成")
        self.log("检索词生成完成。")
        self.log(f"[检索词] 研究问题: {self.query_input.toPlainText().strip()}")
        self.log(f"[检索词] 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"[检索词] GEO 检索式: {bundle.full_geo_query}")
        self.log(f"[检索词] 命中主题摘要: {self._format_matches(bundle).replace(chr(10), ' | ')}")

    def start_search(self) -> None:
        bundle = self.state.query_bundle
        if not bundle or not bundle.full_geo_query:
            QMessageBox.information(self, "提示", "请先生成检索词。")
            return
        try:
            max_results = self._parse_max_results()
            page_size = self._parse_page_size()
        except ValueError as exc:
            QMessageBox.warning(self, "参数错误", str(exc))
            return

        self.log("[UI] 点击“步骤2：搜索 GEO”")
        strategies = self._build_search_strategies(bundle)
        for strategy_label, query in strategies:
            self.log(f"[UI] {strategy_label}: {query}")
        self.search_worker = SearchWorker(strategies, max_results, page_size, 0, self)
        self.search_worker.finished_signal.connect(self.on_search_finished)
        self.search_worker.error_signal.connect(self.on_worker_error)
        self.search_worker.debug_signal.connect(self.log)
        self.search_worker.progress_signal.connect(
            lambda value, message: self._set_task_progress(
                "GEO 检索",
                value,
                message,
                pausable=True,
                pause_target=self.search_worker,
            )
        )
        self.search_worker.start()
        self._set_task_progress("GEO 检索", 5, "任务已启动", pausable=True, pause_target=self.search_worker)
        limit_label = "all" if max_results is None else str(max_results)
        self.log(f"开始检索 GEO。max_results={limit_label}, page_size={page_size}")

    def start_fetch_more(self) -> None:
        bundle = self.state.query_bundle
        if not bundle or not bundle.full_geo_query:
            QMessageBox.information(self, "提示", "请先生成检索词并执行检索。")
            return
        if self.state.fetched_all:
            QMessageBox.information(self, "提示", "当前结果已经抓取完整。")
            return
        try:
            page_size = self._parse_page_size()
        except ValueError as exc:
            QMessageBox.warning(self, "参数错误", str(exc))
            return

        next_limit = len(self.state.results) + page_size
        strategies = self._build_search_strategies(bundle)
        for strategy_label, query in strategies:
            self.log(f"[UI] 继续抓取 {strategy_label}: {query}")
        self.search_worker = SearchWorker(strategies, next_limit, page_size, 0, self)
        self.search_worker.finished_signal.connect(self.on_search_finished)
        self.search_worker.error_signal.connect(self.on_worker_error)
        self.search_worker.debug_signal.connect(self.log)
        self.search_worker.progress_signal.connect(
            lambda value, message: self._set_task_progress(
                "继续抓取",
                value,
                message,
                pausable=True,
                pause_target=self.search_worker,
            )
        )
        self.search_worker.start()
        self._set_task_progress("继续抓取", 5, "任务已启动", pausable=True, pause_target=self.search_worker)
        self.log(f"继续抓取更多结果，目标累计条数：{next_limit}")

    def start_fetch_all(self) -> None:
        bundle = self.state.query_bundle
        if not bundle or not bundle.full_geo_query:
            QMessageBox.information(self, "提示", "请先生成检索词并执行检索。")
            return
        if self.state.fetched_all:
            QMessageBox.information(self, "提示", "当前结果已经抓取完整。")
            return
        if QMessageBox.question(self, "确认", "抓取全部结果可能较慢，是否继续？") != QMessageBox.Yes:
            return
        try:
            page_size = self._parse_page_size()
        except ValueError as exc:
            QMessageBox.warning(self, "参数错误", str(exc))
            return

        strategies = self._build_search_strategies(bundle)
        for strategy_label, query in strategies:
            self.log(f"[UI] 抓取全部 {strategy_label}: {query}")
        self.search_worker = SearchWorker(strategies, None, page_size, 0, self)
        self.search_worker.finished_signal.connect(self.on_search_finished)
        self.search_worker.error_signal.connect(self.on_worker_error)
        self.search_worker.debug_signal.connect(self.log)
        self.search_worker.progress_signal.connect(
            lambda value, message: self._set_task_progress(
                "抓取全部",
                value,
                message,
                pausable=True,
                pause_target=self.search_worker,
            )
        )
        self.search_worker.start()
        self._set_task_progress("抓取全部", 5, "任务已启动", pausable=True, pause_target=self.search_worker)
        self.log("开始抓取全部 GEO 结果。")

    def on_search_finished(self, response: GeoSearchResult) -> None:
        previous_map = {item.gse_id: item for item in self.state.results}
        merged_results = []
        for item in response.results:
            old = previous_map.get(item.gse_id)
            if old:
                item.title_zh = old.title_zh
                item.summary_zh = old.summary_zh
                item.overall_design_zh = old.overall_design_zh
                item.brief_zh = old.brief_zh
            merged_results.append(item)

        self.state.results = merged_results
        self.state.total_count = response.total_count
        self.state.fetched_all = response.fetched_all
        self.state.current_fetch_limit = response.requested_max
        self.state.current_search_strategy = response.strategy_label
        self.state.current_page = 1
        self.log(f"[UI] 响应 total_count={response.total_count}, results={len(response.results)}")
        self._populate_table()
        self.translate_btn.setEnabled(bool(self.state.selected_gse_ids or self._current_result()))
        fetched = len(self.state.results)
        self._mark_task_complete("GEO 检索", f"已抓取 {fetched} 条")
        self.log(f"GEO 检索完成，已抓取 {fetched} 条 / 总命中 {response.total_count} 条。")

    def on_result_selected(self) -> None:
        info = self._current_result()
        if not info:
            self._clear_detail()
            return
        self._show_detail_drawer()
        self._render_detail(info)
        self.translate_btn.setEnabled(bool(self.state.selected_gse_ids or info))

    def on_result_hovered(self, row: int, _column: int) -> None:
        page_results = self._current_page_results()
        if row < 0 or row >= len(page_results):
            return
        info = page_results[row]
        QToolTip.showText(QCursor.pos(), self._build_hover_preview(info), self.result_table)

    def on_table_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating_table or item.column() != 0:
            return
        gse_item = self.result_table.item(item.row(), 1)
        if not gse_item:
            return
        accession = gse_item.text()
        if item.checkState() == Qt.Checked:
            self.state.selected_gse_ids.add(accession)
        else:
            self.state.selected_gse_ids.discard(accession)
        self.translate_btn.setEnabled(bool(self.state.selected_gse_ids or self._current_result()))
        self._update_result_status()

    def _selected_results(self) -> List[GeoSeriesInfo]:
        if self.state.selected_gse_ids:
            return [item for item in self.state.results if item.gse_id in self.state.selected_gse_ids]
        current = self._current_result()
        return [current] if current else []

    def open_task_window(self) -> None:
        selected = self._selected_results()
        if not selected:
            QMessageBox.information(self, "提示", "请先勾选至少一条 GSE 结果，或选中当前行。")
            return
        query_text = self.query_input.toPlainText().strip() or (
            self.state.query_bundle.search_query_en if self.state.query_bundle else "geo_query"
        )
        self.task_window = TaskWindow(selected, query_text, self)
        self.task_window.results_updated.connect(self.on_task_results_updated)
        self.task_window.show()
        self.task_window.raise_()
        self.task_window.activateWindow()

    def on_task_results_updated(self, enriched_list: List[GeoSeriesInfo]) -> None:
        enriched_map = {item.gse_id: item for item in enriched_list}
        self.state.results = [enriched_map.get(item.gse_id, item) for item in self.state.results]
        current_gse = self._current_result().gse_id if self._current_result() else None
        self._populate_table(current_gse=current_gse)
        current = self._current_result()
        if current:
            self._render_detail(current)
        self.log(f"已同步任务页翻译结果，共 {len(enriched_list)} 条。")

    def on_worker_error(self, message: str) -> None:
        self._reset_task_progress(f"任务失败：{message}")
        QMessageBox.warning(self, "错误", message)
        self.log(message)

    def _current_page_results(self) -> List[GeoSeriesInfo]:
        page_size = max(self._safe_page_size_for_display(), 1)
        start = (self.state.current_page - 1) * page_size
        end = min(start + page_size, len(self.state.results))
        return self.state.results[start:end]

    def _safe_page_size_for_display(self) -> int:
        try:
            return self._parse_page_size()
        except Exception:
            return 20

    def _total_pages(self) -> int:
        if not self.state.results:
            return 0
        page_size = max(self._safe_page_size_for_display(), 1)
        return (len(self.state.results) + page_size - 1) // page_size

    def _populate_table(self, current_gse: Optional[str] = None) -> None:
        page_results = self._current_page_results()
        self._updating_table = True
        self.result_table.blockSignals(True)
        self.result_table.clearSelection()
        self.result_table.setRowCount(len(page_results))
        for row, item in enumerate(page_results):
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
            checkbox.setCheckState(Qt.Checked if item.gse_id in self.state.selected_gse_ids else Qt.Unchecked)
            self.result_table.setItem(row, 0, checkbox)

            cells = [
                item.gse_id,
                experiment_type_zh(item.experiment_type),
                str(item.sample_count),
                compact_text(item.brief_zh or item.title_zh or "待翻译"),
            ]
            for column, value in enumerate(cells, start=1):
                self.result_table.setItem(row, column, QTableWidgetItem(value))
            self.result_table.setRowHeight(row, 28)

        self.result_table.blockSignals(False)
        self._updating_table = False

        if current_gse:
            target_row = None
            for row, item in enumerate(page_results):
                if item.gse_id == current_gse:
                    target_row = row
                    break
            if target_row is not None:
                self.result_table.selectRow(target_row)
            else:
                self._clear_detail()
        else:
            self._clear_detail()
        self.log(f"[UI] 写入表格数量: {len(page_results)}（当前页） / {len(self.state.results)}（累计）")
        self._update_result_status()

    def _current_result(self) -> Optional[GeoSeriesInfo]:
        row = self.result_table.currentRow()
        page_results = self._current_page_results()
        if row < 0 or row >= len(page_results):
            return None
        return page_results[row]

    def _render_detail(self, info: GeoSeriesInfo) -> None:
        translated = self._has_translated_content(info)
        self.detail_summary_label.setText(
            f"{info.gse_id} | {experiment_type_zh(info.experiment_type)} | {info.sample_count} 样本 | {info.organism}"
        )
        self.detail_state_label.setText(
            "当前状态：已生成中文翻译与提炼，可查看完整双语详情。"
            if translated
            else "当前状态：仅有 GEO 原始英文信息。中文标题、中文摘要、中文 overall design 和一句话提炼将在“进入翻译与处理页面”后生成。"
        )
        self.title_en_box.setPlainText(info.title_en)
        self.title_zh_box.setPlainText(info.title_zh or "尚未生成中文翻译")
        self.summary_en_box.setPlainText(info.summary_en)
        self.summary_zh_box.setPlainText(info.summary_zh or "尚未生成中文翻译")
        self.design_en_box.setPlainText(info.overall_design_en)
        self.design_zh_box.setPlainText(info.overall_design_zh or "尚未生成中文翻译")
        self.brief_en_box.setPlainText("尚未生成英文一句话提炼")
        self.brief_zh_box.setPlainText(info.brief_zh or "尚未生成中文一句话提炼")
        self.title_zh_label.setText("中文标题" if info.title_zh else "中文标题（待生成）")
        self.summary_zh_label.setText("中文摘要" if info.summary_zh else "中文摘要（待生成）")
        self.design_zh_label.setText(
            "中文 overall design" if info.overall_design_zh else "中文 overall design（待生成）"
        )
        self.brief_en_label.setText("英文一句话提炼（待生成）")
        self.brief_zh_label.setText("中文一句话提炼" if info.brief_zh else "中文一句话提炼（待生成）")

    def _clear_detail(self) -> None:
        self._hide_detail_drawer()
        self.detail_summary_label.setText("点击某条 GSE 后，这里会显示完整详情。")
        self.detail_state_label.setText("当前未打开详情。")
        self.title_zh_label.setText("中文标题")
        self.summary_zh_label.setText("中文摘要")
        self.design_zh_label.setText("中文 overall design")
        self.brief_en_label.setText("英文一句话提炼")
        self.brief_zh_label.setText("中文一句话提炼")
        for widget in [
            self.title_en_box,
            self.title_zh_box,
            self.summary_en_box,
            self.summary_zh_box,
            self.design_en_box,
            self.design_zh_box,
            self.brief_en_box,
            self.brief_zh_box,
        ]:
            widget.clear()

    @staticmethod
    def _has_translated_content(info: GeoSeriesInfo) -> bool:
        return any(
            [
                bool((info.title_zh or "").strip()),
                bool((info.summary_zh or "").strip()),
                bool((info.overall_design_zh or "").strip()),
                bool((info.brief_zh or "").strip()),
            ]
        )

    def _build_hover_preview(self, info: GeoSeriesInfo) -> str:
        title_en = html.escape(compact_text(info.title_en or "无英文标题", 140))
        title_zh = html.escape(compact_text(info.title_zh or "尚未生成中文翻译", 140))
        preview_text = info.summary_zh or info.summary_en or info.overall_design_en or "暂无摘要信息"
        preview_text = html.escape(compact_text(preview_text, 220))
        return (
            f"<b>{html.escape(info.gse_id)}</b> | {html.escape(experiment_type_zh(info.experiment_type))} | "
            f"{info.sample_count} 样本<br>"
            f"<span style='color:#243041;'><b>英文标题：</b>{title_en}</span><br>"
            f"<span style='color:#4b5563;'><b>中文标题：</b>{title_zh}</span><br>"
            f"<span style='color:#5b6472;'><b>摘要预览：</b>{preview_text}</span><br>"
            f"<span style='color:#6b7280;'><b>物种：</b>{html.escape(info.organism or '未注明')} | "
            f"<b>平台：</b>{html.escape(info.platform or '未注明')}</span>"
        )

    def _show_detail_drawer(self) -> None:
        self.detail_page.setVisible(True)
        self.result_detail_splitter.setSizes([860, 420])

    def _hide_detail_drawer(self) -> None:
        self.detail_page.setVisible(False)
        self.result_detail_splitter.setSizes([1280, 0])

    def _update_result_status(self) -> None:
        total_pages = self._total_pages()
        fetched_all = "是" if self.state.fetched_all else "否"
        limit_label = "all" if self.state.current_fetch_limit is None else str(self.state.current_fetch_limit or 0)
        self.result_status_label.setText(
            f"检索模式: {self.state.current_search_strategy} | 总命中: {self.state.total_count} | 已抓取: {len(self.state.results)} | 抓取上限: {limit_label} | 是否抓完整: {fetched_all} | 当前页: {self.state.current_page}/{max(total_pages, 1)} | 已勾选: {len(self.state.selected_gse_ids)}"
        )

    def show_previous_page(self) -> None:
        if self.state.current_page <= 1:
            return
        self.state.current_page -= 1
        self._populate_table()

    def show_next_page(self) -> None:
        if self.state.current_page >= self._total_pages():
            return
        self.state.current_page += 1
        self._populate_table()

    def select_current_page(self) -> None:
        for item in self._current_page_results():
            self.state.selected_gse_ids.add(item.gse_id)
        self._populate_table(current_gse=self._current_result().gse_id if self._current_result() else None)
        self.translate_btn.setEnabled(bool(self.state.selected_gse_ids or self._current_result()))

    def clear_checked_results(self) -> None:
        self.state.selected_gse_ids.clear()
        self._populate_table(current_gse=self._current_result().gse_id if self._current_result() else None)
        self.translate_btn.setEnabled(bool(self._current_result()))

    @staticmethod
    def _format_matches(bundle: QueryBundle) -> str:
        sections = []
        for label, matches in [
            ("疾病组", bundle.disease_matches),
            ("暴露组", bundle.exposure_matches),
            ("治疗组", bundle.treatment_matches),
            ("分子组", bundle.molecular_matches),
            ("人群组", bundle.population_matches),
        ]:
            if not matches:
                sections.append(f"{label}: 未命中")
                continue
            lines = [f"{label}:"]
            for match in matches:
                lines.append(
                    f"- {match.canonical} <- {match.matched_alias} -> {', '.join(match.english_terms)}"
                )
            sections.append("\n".join(lines))
        return "\n\n".join(sections)


def sanitize_folder_name(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in text.strip())
    return cleaned.strip("_") or "geo_query"


def build_batch_output_dir(base_dir: str, query_text: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = Path(base_dir).expanduser().resolve() / f"{sanitize_folder_name(query_text)[:80]}_{timestamp}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    return batch_dir


def save_selected_results_metadata(selected_items: List[GeoSeriesInfo], batch_dir: Path) -> tuple[Path, Path]:
    payload = [
        {
            **item.to_search_payload(),
            "gse_id": item.gse_id,
            "organism": item.organism,
            "experiment_type": item.experiment_type,
            "sample_count": item.sample_count,
            "platform": item.platform,
            "title_en": item.title_en,
            "title_zh": item.title_zh,
            "summary_en": item.summary_en,
            "summary_zh": item.summary_zh,
            "overall_design_en": item.overall_design_en,
            "overall_design_zh": item.overall_design_zh,
            "pubmed_id": item.pubmed_id,
            "geo_url": item.geo_url,
            "brief_zh": item.brief_zh,
        }
        for item in selected_items
    ]

    json_path = batch_dir / "selected_results.json"
    csv_path = batch_dir / "selected_results.csv"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "gse_id",
                "organism",
                "experiment_type",
                "sample_count",
                "platform",
                "title_en",
                "title_zh",
                "summary_en",
                "summary_zh",
                "overall_design_en",
                "overall_design_zh",
                "pubmed_id",
                "geo_url",
                "brief_zh",
            ],
        )
        writer.writeheader()
        for row in payload:
            writer.writerow(row)
    return json_path, csv_path


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
