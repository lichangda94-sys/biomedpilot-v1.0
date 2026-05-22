from __future__ import annotations

import json
import re
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QInputDialog,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.bioinformatics.analysis_task_runs import create_deg_task_run, list_analysis_task_runs, task_run_status_label
from app.bioinformatics.analysis_ui.labels import label_status
from app.bioinformatics.analysis_ui.state import build_analysis_center_state
from app.bioinformatics.project_analysis_tasks import create_analysis_task, load_analysis_task_center, load_task_records
from app.bioinformatics.deg_executor_preflight import run_deg_executor_preflight
from app.bioinformatics.deg_task_plan import save_deg_task_plan
from app.bioinformatics.group_comparison_design import (
    build_default_comparison_rows,
    build_default_group_rows,
    design_status_summary,
    has_confirmed_group_comparison_design,
    load_group_design_context,
    save_group_comparison_design,
    validate_group_comparison_design,
)
from app.bioinformatics.comparison_config import (
    build_geo_comparison_config_text,
    comparison_summary_text,
    evidence_field_label_zh,
    group_label_zh,
    confirmed_group_assignments,
    load_confirmed_comparison_config,
)
from app.bioinformatics.project_readiness import load_readiness_artifacts, readiness_status_zh, run_project_readiness
from app.bioinformatics.project_recognition import (
    TYPE_LABELS,
    classify_file,
    delete_recognition_run,
    list_recognition_runs,
    load_recognition_report,
    run_project_recognition,
    run_project_recognition_for_paths,
    set_current_recognition_run,
)
from app.bioinformatics.recognition_detail_report import (
    build_recognition_detail_payload,
    export_recognition_report_markdown,
    format_recognition_detail_technical,
    format_recognition_detail_text,
)
from app.bioinformatics.recognition_next_steps import (
    build_recognition_next_steps,
    standardization_current_input_summary,
)
from app.bioinformatics.project_standardization import generate_standardized_assets, load_standardization_artifacts
from app.bioinformatics.standardized_asset_selection import (
    build_asset_selection_context,
    save_standardized_asset_selection,
    selection_status_label,
)
from app.bioinformatics.project_workflow_orchestrator import (
    default_workflow_state,
    load_workflow_state,
    run_project_stage,
    run_project_workflow,
    workflow_status_zh,
)
from app.bioinformatics.project_workspace import BioinformaticsProjectSummary
from app.bioinformatics.project_workspace_binding import (
    AcquisitionStrategy,
    AcquisitionSummary,
    LATEST_HANDOFF,
    LATEST_PLAN,
    LATEST_RECORD,
    generate_gse_acquisition_plan,
    load_latest_acquisition_summary,
    read_acquisition_artifacts,
    register_acquisition,
)
from app.bioinformatics.adapters.legacy_geo import geo_check_command, run_geo_environment_check
from app.bioinformatics.download import DatasetDownloadService, GeoDatasetProfile, GeoDatasetProfileService, GeoStudyTextInput, GeoTextSummaryService
from app.bioinformatics.retrieval.geo_detail_enrichment import GeoDetailEnrichmentService, build_geo_detail_metadata
from app.bioinformatics.reports.project_report_builder import generate_project_report, load_project_report
from app.bioinformatics.results.project_results import build_imported_deg_view, load_imported_deg_comparisons, load_result_index, write_result_index
from app.bioinformatics.search_center import (
    BioinformaticsSearchCenterResult,
    BioinformaticsSourceRouter,
    GeoSearchAdapter,
    GtexSearchAdapter,
    SourceSearchResult,
    TcgaGdcSearchAdapter,
    UnifiedDatasetCandidate,
)
from app.bioinformatics.services.geo_differential_expression_runner import run_geo_differential_expression
from app.bioinformatics.services.organism_display import get_organism_display_name
from app.shared.ai_gateway import (
    create_ai_draft_record,
    desktop_local_ollama_config,
    load_ai_gateway_config,
    mark_ai_draft_status,
    save_ai_draft_record,
    save_ai_gateway_config,
)
from app.shared.ai_gateway.drafts import AIDraftRecord
from app.shared.ai_gateway.models import AIProviderStatus
from app.shared.ai_gateway.providers.ollama_provider import DEFAULT_OLLAMA_BASE_URL, DEFAULT_OLLAMA_MODEL, OllamaProvider
from app.shared.query_intelligence import LocalModelConfig
from app.ui_style_tokens import SPACING, bioinformatics_project_home_stylesheet


@dataclass(frozen=True)
class SelectedSourceSummary:
    source_type: str
    source_label: str
    selected_kind: str
    display_name: str
    absolute_path: str
    storage_policy: str
    acquisition_status: str
    acquisition_plan_path: str
    acquisition_record_path: str
    handoff_path: str
    created_at: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class RegisteredSourceRow:
    acquisition_id: str
    source_type_key: str
    source_type: str
    source_label: str
    location: str
    status: str
    created_at: str
    strategy: str
    location_tooltip: str = ""


@dataclass(frozen=True)
class DatasetListEntry:
    key: str
    source: str
    name: str
    status: str
    available_content: str
    missing_content: str
    note: str
    title: str
    abstract: str
    keywords: str
    technical_info: str
    ready_for_recognition: bool
    downloadable: bool
    removable: bool
    source_type_key: str
    accession: str = ""
    acquisition_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class GseDatasetPreview:
    gse_id: str
    title: str = "未记录"
    organism: str = "未记录"
    platform: str = "未记录"
    sample_count: str = "未记录"
    status: str = "尚未添加"
    detail_metadata: dict[str, object] | None = None


class GeoDatasetDetailPanel(QFrame):
    save_requested = Signal(object)
    ignore_requested = Signal(object)
    remove_requested = Signal(object)
    download_assets_requested = Signal(object)
    translate_requested = Signal(object)
    brief_requested = Signal(object)
    confirm_comparison_requested = Signal(object)
    manual_comparison_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._candidate: UnifiedDatasetCandidate | None = None
        self.setObjectName("geoDatasetDetailView")
        self.setVisible(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        layout.setSpacing(SPACING["sm"])

        self._title = QLabel("GEO 数据集详情")
        self._title.setObjectName("bioProjectCardTitle")
        self._title.setWordWrap(True)
        layout.addWidget(self._title)
        self._saved_status = _status_label("尚未加入待处理数据集。")
        layout.addWidget(self._saved_status)

        layout.addWidget(_muted("基础信息"))
        self._basic_table = _table(["字段", "内容"])
        self._basic_table.setObjectName("geoDatasetBasicInfoTable")
        self._basic_table.setMaximumHeight(230)
        layout.addWidget(self._basic_table)

        layout.addWidget(_muted("英文原始信息"))
        self._english_text = _text_preview(150)
        self._english_text.setObjectName("geoDatasetEnglishMetadata")
        layout.addWidget(self._english_text)

        layout.addWidget(_muted("中文翻译与精炼"))
        translate_actions = QHBoxLayout()
        self._translate_button = _button("中文翻译与提炼", "secondaryButton", lambda: self._emit_translate())
        self._brief_button = self._translate_button
        translate_actions.addWidget(self._translate_button)
        translate_actions.addStretch(1)
        layout.addLayout(translate_actions)
        self._translation_text = _text_preview(150)
        self._translation_text.setObjectName("geoDatasetChineseSummary")
        self._translation_text.setPlainText("尚未生成中文翻译。")
        layout.addWidget(self._translation_text)

        layout.addWidget(_muted("样本结构与下载建议"))
        self._profile_text = _text_preview(150)
        self._profile_text.setObjectName("geoDatasetProfileSummary")
        layout.addWidget(self._profile_text)
        comparison_actions = QHBoxLayout()
        self._confirm_comparison_button = _button("使用该分组创建比较组", "secondaryButton", lambda: self._emit_confirm_comparison())
        self._manual_comparison_button = _button("手动设置比较组", "secondaryButton", lambda: self._emit_manual_comparison())
        self._confirm_comparison_button.setEnabled(False)
        self._manual_comparison_button.setEnabled(False)
        comparison_actions.addWidget(self._confirm_comparison_button)
        comparison_actions.addWidget(self._manual_comparison_button)
        comparison_actions.addStretch(1)
        layout.addLayout(comparison_actions)

        layout.addWidget(_muted("数据资产状态"))
        self._asset_text = _text_preview(120)
        self._asset_text.setObjectName("geoDatasetAssetStatus")
        layout.addWidget(self._asset_text)

        decision_actions = QHBoxLayout()
        self._save_button = _button("添加到项目", "primaryButton", lambda: self._emit_save())
        self._download_assets_button = _button("下载补充文件", "primaryButton", lambda: self._emit_download_assets())
        self._remove_button = _button("从项目列表移除", "secondaryButton", lambda: self._emit_remove())
        self._ignore_button = _button("忽略该数据集", "secondaryButton", lambda: self._emit_ignore())
        self._download_assets_button.setVisible(False)
        self._remove_button.setVisible(False)
        decision_actions.addWidget(self._save_button)
        decision_actions.addWidget(self._download_assets_button)
        decision_actions.addWidget(self._remove_button)
        decision_actions.addWidget(self._ignore_button)
        decision_actions.addStretch(1)
        layout.addLayout(decision_actions)

    def current_candidate(self) -> UnifiedDatasetCandidate | None:
        return self._candidate

    def show_candidate(
        self,
        candidate: UnifiedDatasetCandidate,
        *,
        project_root: Path | None,
        summary_payload: dict[str, object] | None = None,
        saved: bool = False,
    ) -> None:
        self._candidate = candidate
        self.setVisible(True)
        self._title.setText(f"{candidate.accession_or_project} · {candidate.display_title or 'GEO 数据集'}")
        _fill_table(self._basic_table, _geo_detail_basic_rows(candidate))
        self._english_text.setPlainText(_geo_detail_english_text(candidate))
        profile = _build_geo_detail_profile(project_root, candidate, summary_payload)
        self._profile_text.setPlainText(_geo_profile_user_display(profile, candidate))
        self._confirm_comparison_button.setEnabled(bool(profile.candidate_comparisons and project_root is not None))
        self._manual_comparison_button.setEnabled(project_root is not None)
        self._asset_text.setPlainText(_geo_asset_detail_text(project_root, candidate.accession_or_project))
        self.set_saved(saved)
        self.set_pending_assets(saved and _candidate_has_pending_geo_assets(project_root, candidate.accession_or_project))
        if summary_payload:
            self.render_summary(candidate, summary_payload)
        else:
            self._translation_text.setPlainText("尚未生成中文翻译。")

    def set_saved(self, saved: bool) -> None:
        self._saved_status.setText("已在待处理数据集中。" if saved else "尚未加入待处理数据集。")
        self._save_button.setText("已添加" if saved else "添加到项目")
        self._save_button.setEnabled(not saved)
        self._remove_button.setVisible(saved)

    def set_pending_assets(self, pending: bool) -> None:
        self._download_assets_button.setVisible(pending)
        self._download_assets_button.setEnabled(pending)

    def render_summary(self, candidate: UnifiedDatasetCandidate, payload: dict[str, object]) -> None:
        self._translation_text.setPlainText(_geo_text_summary_user_display(candidate, payload))

    def set_busy_text(self, text: str) -> None:
        self._translation_text.setPlainText(text)

    def _emit_save(self) -> None:
        if self._candidate is not None:
            self.save_requested.emit(self._candidate)

    def _emit_ignore(self) -> None:
        if self._candidate is not None:
            self.ignore_requested.emit(self._candidate)

    def _emit_remove(self) -> None:
        if self._candidate is not None:
            self.remove_requested.emit(self._candidate)

    def _emit_download_assets(self) -> None:
        if self._candidate is not None:
            self.download_assets_requested.emit(self._candidate)

    def _emit_translate(self) -> None:
        if self._candidate is not None:
            self.translate_requested.emit(self._candidate)

    def _emit_brief(self) -> None:
        if self._candidate is not None:
            self.brief_requested.emit(self._candidate)

    def _emit_confirm_comparison(self) -> None:
        if self._candidate is not None:
            self.confirm_comparison_requested.emit(self._candidate)

    def _emit_manual_comparison(self) -> None:
        if self._candidate is not None:
            self.manual_comparison_requested.emit(self._candidate)


class GeoDownloadListPanel(QFrame):
    view_requested = Signal(str)
    download_metadata_requested = Signal(str)
    download_assets_requested = Signal(str)
    download_selected_requested = Signal(tuple)
    delete_selected_requested = Signal(tuple)
    continue_requested = Signal()
    remove_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None, *, title: str = "待处理数据集", geo_only: bool = False) -> None:
        super().__init__(parent)
        self._geo_only = geo_only
        self._entries: list[DatasetListEntry] = []
        self._checks: dict[str, QCheckBox] = {}
        self.setObjectName("geoDownloadListPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        layout.setSpacing(SPACING["sm"])
        self._title_label = QLabel(title)
        self._title_label.setObjectName("bioProjectCardTitle")
        layout.addWidget(self._title_label)
        self._empty = _muted("尚未选择数据。")
        layout.addWidget(self._empty)
        self._table = _table(["选择", "来源", "数据集 / 文件名", "数据状态", "可用内容", "需要补充", "备注", "操作"])
        self._table.setObjectName("geoDownloadListTable")
        self._table.setMinimumHeight(180)
        layout.addWidget(self._table)

        batch_row = QHBoxLayout()
        self._download_selected_button = _button("下载所选", "secondaryButton", self._emit_download_selected)
        self._delete_selected_button = _button("删除所选", "secondaryButton", self._emit_delete_selected)
        self._continue_selected_button = _button("进入数据识别", "primaryButton", self._emit_continue_selected)
        self._download_selected_button.setEnabled(False)
        self._delete_selected_button.setEnabled(False)
        self._continue_selected_button.setEnabled(False)
        batch_row.addStretch(1)
        batch_row.addWidget(self._download_selected_button)
        batch_row.addWidget(self._delete_selected_button)
        batch_row.addWidget(self._continue_selected_button)
        layout.addLayout(batch_row)

    def refresh(self, project_root: Path | None) -> None:
        entries = _current_project_dataset_entries(project_root, geo_only=self._geo_only)
        self._entries = entries
        self._checks = {}
        self._empty.setVisible(not entries)
        self._table.setVisible(bool(entries))
        _fill_table(
            self._table,
            [
                [
                    "",
                    entry.source,
                    entry.name,
                    entry.status,
                    entry.available_content,
                    entry.missing_content,
                    _compact_note(entry.note),
                    "",
                ]
                for entry in entries
            ],
        )
        for row_index, entry in enumerate(entries):
            checkbox = QCheckBox()
            checkbox.setObjectName(f"datasetSelectCheck_{entry.key}")
            checkbox.stateChanged.connect(lambda _state=0: self._refresh_batch_buttons())
            self._checks[entry.key] = checkbox
            self._table.setCellWidget(row_index, 0, checkbox)
            self._table.setCellWidget(row_index, 7, self._action_widget(entry))
            for col in range(self._table.columnCount()):
                item = self._table.item(row_index, col)
                if item is not None:
                    item.setToolTip(_dataset_entry_tooltip(entry, col))
        _set_table_widths(self._table, [54, 110, 190, 120, 150, 120, 180, 110])
        self._refresh_batch_buttons()

    def selected_keys(self) -> tuple[str, ...]:
        return tuple(key for key, checkbox in self._checks.items() if checkbox.isChecked())

    def selected_entries(self) -> list[DatasetListEntry]:
        selected = set(self.selected_keys())
        return [entry for entry in self._entries if entry.key in selected]

    def _action_widget(self, entry: DatasetListEntry) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        view_button = QPushButton("查看详情")
        view_button.clicked.connect(lambda checked=False, value=entry.key: self.view_requested.emit(value))
        layout.addWidget(view_button)
        layout.addStretch(1)
        return widget

    def _refresh_batch_buttons(self) -> None:
        entries = self.selected_entries()
        has_selection = bool(entries)
        downloadable = [entry for entry in entries if entry.downloadable]
        self._download_selected_button.setEnabled(bool(downloadable))
        if any("表达矩阵" in entry.missing_content or "补充" in entry.status for entry in downloadable):
            self._download_selected_button.setText("下载补充文件")
        else:
            self._download_selected_button.setText("下载所选")
        self._delete_selected_button.setEnabled(has_selection)
        self._continue_selected_button.setEnabled(any(entry.ready_for_recognition for entry in entries))

    def _emit_download_selected(self) -> None:
        keys = self.selected_keys()
        if keys:
            self.download_selected_requested.emit(keys)

    def _emit_delete_selected(self) -> None:
        keys = self.selected_keys()
        if keys:
            self.delete_selected_requested.emit(keys)

    def _emit_continue_selected(self) -> None:
        if self.selected_entries():
            self.continue_requested.emit()


class DatasetDetailPanel(QFrame):
    save_note_requested = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entry: DatasetListEntry | None = None
        self.setObjectName("datasetDetailPanel")
        self.setVisible(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        layout.setSpacing(SPACING["sm"])

        self._title = QLabel("数据详情")
        self._title.setObjectName("bioProjectCardTitle")
        self._title.setWordWrap(True)
        layout.addWidget(self._title)
        self._summary = _text_preview(120)
        self._summary.setObjectName("datasetDefaultSummary")
        layout.addWidget(self._summary)

        layout.addWidget(_muted("用户备注"))
        self._note_edit = QPlainTextEdit()
        self._note_edit.setObjectName("datasetUserNoteEdit")
        self._note_edit.setPlaceholderText("可记录筛选理由、疑问或后续处理计划。备注只作为笔记保存。")
        self._note_edit.setMinimumHeight(72)
        self._note_edit.setMaximumHeight(120)
        layout.addWidget(self._note_edit)
        note_actions = QHBoxLayout()
        note_actions.addWidget(_button("保存备注", "secondaryButton", self._save_note))
        note_actions.addWidget(_button("清空备注", "secondaryButton", self._clear_note))
        note_actions.addStretch(1)
        layout.addLayout(note_actions)

        self._tech_button = _button("技术信息", "secondaryButton", lambda: _toggle_details(self._technical))
        layout.addWidget(self._tech_button, alignment=Qt.AlignLeft)
        self._technical = _text_preview(140)
        self._technical.setObjectName("datasetTechnicalInfo")
        self._technical.setVisible(False)
        layout.addWidget(self._technical)

    def show_entry(self, entry: DatasetListEntry) -> None:
        self._entry = entry
        self.setVisible(True)
        self._title.setText(f"{entry.name} · {entry.source}")
        self._summary.setPlainText(_dataset_detail_summary(entry))
        self._note_edit.setPlainText(entry.note)
        self._technical.setPlainText(entry.technical_info)
        self._technical.setVisible(False)

    def _save_note(self) -> None:
        if self._entry is None:
            return
        self.save_note_requested.emit(self._entry.key, self._note_edit.toPlainText().strip())

    def _clear_note(self) -> None:
        self._note_edit.setPlainText("")
        self._save_note()


class BioinformaticsDataSourceWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()
    chinese_search_requested = Signal()

    def __init__(
        self,
        *,
        on_continue: Callable[[Path], None] | None = None,
        on_back: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._summary: BioinformaticsProjectSummary | None = None
        self._project_root: Path | None = None
        self._latest_summary: AcquisitionSummary | None = None
        self._source_summaries: dict[str, SelectedSourceSummary] = {}
        self._source_summary_labels: dict[str, QLabel] = {}
        self._source_action_buttons: dict[str, tuple[QPushButton, QPushButton]] = {}
        self._source_detail_edits: dict[str, QPlainTextEdit] = {}
        self._source_detail_buttons: dict[str, QPushButton] = {}
        self._gse_preview: GseDatasetPreview | None = None
        self._geo_candidates: dict[str, UnifiedDatasetCandidate] = {}
        self._geo_brief_cache: dict[str, dict[str, object]] = {}
        self._dataset_entries: dict[str, DatasetListEntry] = {}
        self._pending_chinese_query = ""
        self._download_service = DatasetDownloadService()
        self._text_summary_service = GeoTextSummaryService(timeout=20)
        self.setObjectName("bioinformaticsDataSourcePage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)
        self.refresh_project(None)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._summary = summary if isinstance(summary, BioinformaticsProjectSummary) else None
        self._project_root = _project_root(summary)
        self._project_label.setText(_project_header_text(summary))
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
        else:
            self._set_status("先添加数据，下一步进入数据识别。")
        self._refresh_registered_sources()
        self._refresh_geo_download_list()
        self._render_gated_source_tables(selected_source="")

    def status_message(self) -> str:
        return self._status_label.text()

    def latest_acquisition_summary(self) -> AcquisitionSummary | None:
        return self._latest_summary

    def set_gse_input(self, value: str) -> None:
        self._gse_input.setText(value)

    def generate_gse_plan(self) -> AcquisitionSummary | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        if self.search_gse_dataset() is None:
            return None
        return self.register_gse_dataset()

    def search_gse_dataset(self) -> GseDatasetPreview | None:
        gse_id = _normalize_gse_id(self._gse_input.text())
        if not gse_id:
            self._gse_status_label.setText("请输入 GSE 编号。")
            self._set_status("请输入 GSE 编号。", error=True)
            return None
        self._gse_input.setText(gse_id)
        try:
            metadata_text = _fetch_geo_accession_metadata(gse_id, self._project_root)
        except TypeError:
            metadata_text = _fetch_geo_accession_metadata(gse_id)
        self._gse_preview = _gse_preview_from_metadata(gse_id, metadata_text)
        candidate = _geo_candidate_from_gse_preview(self._gse_preview)
        self._geo_candidates[candidate.accession_or_project] = candidate
        self._render_gse_preview(self._gse_preview)
        self._show_gse_geo_detail(candidate)
        self._set_status("GSE 数据集摘要已生成，请查看详情后添加到项目。")
        return self._gse_preview

    def register_gse_dataset(self) -> AcquisitionSummary | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        preview = self._gse_preview or self.search_gse_dataset()
        if preview is None:
            return None
        candidate = self._geo_candidates.get(preview.gse_id) or _geo_candidate_from_gse_preview(preview)
        summary = self._save_gse_geo_candidate(candidate)
        if summary is None:
            return None
        self._render_acquisition_summary(
            summary,
            summary_key="geo_gse",
            selected_kind="accession",
            display_name=preview.gse_id,
            absolute_path="",
            data_type_label="GSE 编号检索",
        )
        self._gse_preview = GseDatasetPreview(
            gse_id=preview.gse_id,
            title=preview.title,
            organism=preview.organism,
            platform=preview.platform,
            sample_count=preview.sample_count,
            status="已选择",
        )
        self._render_gse_preview(self._gse_preview)
        self._refresh_registered_sources()
        self._refresh_geo_download_list()
        self._set_status(f"{preview.gse_id} 已添加到项目。")
        return summary

    def register_local_paths(
        self,
        selected_paths: list[str | Path],
        *,
        source_type: str = "local_import",
        source_label: str = "本地数据导入",
        strategy: AcquisitionStrategy | None = None,
        metadata: dict[str, object] | None = None,
        selected_kind: str | None = None,
        summary_key: str | None = None,
        data_type_label: str | None = None,
    ) -> AcquisitionSummary | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        resolved_strategy = strategy or _strategy_from_combo(self._local_strategy_combo)
        summary_key_resolved = summary_key or source_type
        progress_text = "正在复制本地数据，请稍候。" if resolved_strategy == "copy" else "正在添加本地数据，请稍候。"
        progress_label = self._source_summary_labels.get(summary_key_resolved)
        if progress_label is not None:
            progress_label.setText(progress_text)
            progress_label.setToolTip(progress_text)
            QApplication.processEvents()
        summary = register_acquisition(
            self._project_root,
            source_type=source_type,
            source_label=source_label,
            strategy=resolved_strategy,
            selected_paths=selected_paths,
            metadata=metadata,
        )
        normalized_paths = [Path(path).expanduser().resolve() for path in selected_paths]
        inferred_kind = selected_kind or _selected_kind_from_paths(normalized_paths)
        self._render_acquisition_summary(
            summary,
            selected_paths=normalized_paths,
            summary_key=summary_key_resolved,
            selected_kind=inferred_kind,
            data_type_label=data_type_label or _infer_local_data_type(normalized_paths, source_type=source_type),
        )
        self._refresh_registered_sources()
        return summary

    def generate_research_terms(self) -> str:
        return self.search_research_topic()

    def search_research_topic(self) -> str:
        self.open_chinese_search()
        return "中文研究问题检索已移动到独立页面。"

    def pending_chinese_query(self) -> str:
        return self._pending_chinese_query

    def open_chinese_search(self) -> None:
        self._pending_chinese_query = self._chinese_query_input.text().strip()
        self.chinese_search_requested.emit()

    def continue_to_recognition(self) -> None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return
        if self._latest_summary is None:
            self._latest_summary = load_latest_acquisition_summary(self._project_root)
        if self._registered_source_count() == 0:
            self._set_status("请先下载或导入至少一个实际数据文件。", error=True)
            return
        selected_entries = [entry for entry in self._dataset_list_panel.selected_entries() if entry.ready_for_recognition]
        _save_pending_recognition_selection(self._project_root, selected_entries)
        self.continue_requested.emit(self._project_root)

    def continue_to_acquisition_status(self) -> None:
        self.continue_to_recognition()

    def _build_ui(self) -> None:
        root = _scroll_root(self, max_width=1040)
        root.addWidget(
            _header(
                "Data Source / 数据来源",
                "选择或配置数据来源；本页只做 gated preview，不下载、不导入、不执行分析。",
                back_text="返回项目首页",
                back_signal=self.back_requested,
            )
        )
        self._project_label = _status_label("请先创建或打开生信分析项目。")
        root.addWidget(self._project_label)
        self._status_label = _status_label("请选择数据来源类型；导入后必须进入 Data Check & Preparation。")
        root.addWidget(self._status_label)
        root.addWidget(self._gated_source_overview())

        self._legacy_local_import_card = self._local_import_card()
        self._legacy_gse_card = self._gse_card()
        self._legacy_research_card = self._research_card()
        for legacy_card in (self._legacy_local_import_card, self._legacy_gse_card, self._legacy_research_card):
            legacy_card.setProperty("developerDiagnostic", True)
            legacy_card.setProperty("normalUserVisible", False)
            legacy_card.setVisible(False)
            root.addWidget(legacy_card)

        self._dataset_list_panel = GeoDownloadListPanel(title="待处理数据集")
        self._dataset_list_panel.view_requested.connect(self._show_dataset_detail)
        self._dataset_list_panel.download_selected_requested.connect(self._download_selected_dataset_entries)
        self._dataset_list_panel.delete_selected_requested.connect(self._delete_selected_dataset_entries)
        self._dataset_list_panel.continue_requested.connect(self.continue_to_recognition)
        root.addWidget(self._dataset_list_panel)

        self._history_cache_card, self._history_cache_layout = _card("历史缓存数据")
        self._history_cache_card.setObjectName("historicalCacheDataCard")
        self._history_cache_hint = _muted("未发现历史缓存数据。")
        self._history_cache_table = _table(["数据集", "位置", "操作"])
        self._history_cache_table.setObjectName("historicalCacheDataTable")
        self._history_cache_table.setMinimumWidth(0)
        self._history_cache_layout.addWidget(self._history_cache_hint)
        self._history_cache_layout.addWidget(self._history_cache_table)
        root.addWidget(self._history_cache_card)

        self._dataset_detail_panel = DatasetDetailPanel()
        self._dataset_detail_panel.save_note_requested.connect(self._save_dataset_note)
        root.addWidget(self._dataset_detail_panel)

        self._technical_details = _text_preview(120)
        self._technical_details.setVisible(False)
        root.addWidget(self._technical_details)

        actions_frame = QFrame()
        actions_frame.setObjectName("dataSourceBottomActionBar")
        actions = QHBoxLayout(actions_frame)
        actions.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        self._registered_count_label = _status_label("已选择的数据：0 个")
        self._next_button = _button("下一步：数据识别", "primaryButton", self.continue_to_recognition)
        self._next_button.setEnabled(False)
        actions.addWidget(self._registered_count_label)
        actions.addStretch(1)
        actions.addWidget(self._next_button)
        root.addWidget(actions_frame)

    def _gated_source_overview(self) -> QFrame:
        card, layout = _card("Source Status Overview / 数据来源状态总览")
        card.setObjectName("bioinformaticsDataSourceGatedOverview")
        card.setProperty("formalActionEnabled", False)
        layout.addWidget(_muted("主数据源入口仅用于选择和配置。GEO、TCGA、GTEx 不在本页下载；Local File 不在本页真实导入。"))
        source_grid = QGridLayout()
        source_grid.setHorizontalSpacing(SPACING["sm"])
        source_grid.setVerticalSpacing(SPACING["sm"])
        sources = (
            ("geo", "GEO", "GEO accession / dataset search", "配置 GEO 数据集编号或候选来源；下载和识别进入后续 gated 流程。"),
            ("tcga", "TCGA", "TCGA project source", "选择 TCGA 项目来源；TCGA+GTEx 不自动合并。"),
            ("gtex", "GTEx", "GTEx tissue source", "选择 GTEx 组织来源；不与 TCGA 默认合并。"),
            ("local_file", "Local File", "本地文件", "选择本地文件类型预览；真实导入需后续文件适配器和 Data Check。"),
        )
        for index, (key, title, subtitle, body) in enumerate(sources):
            source_grid.addWidget(self._gated_source_card(key, title, subtitle, body), index // 2, index % 2)
        layout.addLayout(source_grid)
        self._source_status_table = _table(["source", "status", "allowed action", "blocked action", "next gate"])
        self._source_status_table.setObjectName("bioinformaticsSourceStatusOverviewTable")
        layout.addWidget(self._source_status_table)
        self._recent_imports_table = _table(["source", "name", "state", "gate note"])
        self._recent_imports_table.setObjectName("bioinformaticsRecentImportsPreviewTable")
        layout.addWidget(_muted("Recent Imports / 最近导入状态：仅显示当前项目状态或安全空状态，不代表 formal input readiness。"))
        layout.addWidget(self._recent_imports_table)
        gate_note = _muted("选择或登记来源后仍必须进入 Data Check & Preparation；不得直接进入正式分析。Report / Export 当前 not ready。")
        gate_note.setObjectName("bioinformaticsDataSourceGateNotice")
        gate_note.setProperty("formalActionEnabled", False)
        gate_note.setProperty("exportGate", "disabled_missing_report_ready")
        layout.addWidget(gate_note)
        self._render_gated_source_tables(selected_source="")
        return card

    def _gated_source_card(self, source_key: str, title: str, subtitle: str, body: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("bioinformaticsDataSourceMainCard")
        frame.setProperty("sourceKey", source_key)
        frame.setProperty("formalActionEnabled", False)
        frame.setProperty("downloadEnabled", False)
        frame.setProperty("importEnabled", False)
        frame.setProperty("analysisEnabled", False)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        layout.setSpacing(SPACING["xs"])
        title_label = QLabel(title)
        title_label.setObjectName("bioinformaticsDataSourceMainCardTitle")
        subtitle_label = _muted(subtitle)
        body_label = QLabel(body)
        body_label.setObjectName("bioinformaticsDataSourceMainCardBody")
        body_label.setWordWrap(True)
        button = _button("选择 / 配置预览", "secondaryButton", lambda checked=False, key=source_key: self._select_gated_source_preview(key))
        button.setObjectName("bioinformaticsDataSourceSelectPreviewButton")
        button.setProperty("sourceKey", source_key)
        button.setProperty("buttonBehavior", "enabled_select_preview_only")
        button.setProperty("formalActionEnabled", False)
        button.setToolTip("只更新页面状态预览，不下载、不导入、不写入 acquisition record。")
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addWidget(body_label)
        layout.addWidget(button, alignment=Qt.AlignLeft)
        return frame

    def _select_gated_source_preview(self, source_key: str) -> None:
        label = {"geo": "GEO", "tcga": "TCGA", "gtex": "GTEx", "local_file": "Local File"}.get(source_key, source_key)
        self._set_status(f"已选择 {label} 配置预览；未下载、未导入、未生成结果。")
        self._render_gated_source_tables(selected_source=source_key)

    def _render_gated_source_tables(self, *, selected_source: str) -> None:
        selected = selected_source or "none"
        _fill_table(
            self._source_status_table,
            [
                ["GEO", "configure/select preview" if selected == "geo" else "not selected", "选择 / 配置预览", "download / analysis", "Data Check & Preparation"],
                ["TCGA", "configure/select preview" if selected == "tcga" else "not selected", "选择 / 配置预览", "TCGA+GTEx auto merge", "Data Check & Preparation"],
                ["GTEx", "configure/select preview" if selected == "gtex" else "not selected", "选择 / 配置预览", "TCGA+GTEx auto merge", "Data Check & Preparation"],
                ["Local File", "configure/select preview" if selected == "local_file" else "not selected", "选择 / 配置预览", "real file import", "Data Check & Preparation"],
            ],
        )
        entries = _current_project_dataset_entries(self._project_root)
        rows = [[entry.source, entry.name, entry.status, "current project state preview; not formal input readiness"] for entry in entries[:6]]
        if not rows:
            rows = [["-", "暂无最近导入", "empty-safe", "No fake expression matrix; no fake result."]]
        _fill_table(self._recent_imports_table, rows)

    def _local_import_card(self) -> QFrame:
        card, layout = _card("本地数据导入")
        card.setObjectName("localImportEntryCard")
        card.setProperty("normalUserVisible", False)
        layout.addWidget(_muted("导入本地表达矩阵、GEO Series Matrix、样本信息、临床表或注释文件。"))
        self._local_strategy_combo = QComboBox()
        self._local_strategy_combo.setObjectName("localImportStrategyCombo")
        self._local_strategy_combo.addItems(["复制到项目文件夹（推荐）", "使用原文件位置"])
        self._local_strategy_combo.currentIndexChanged.connect(self._update_local_strategy_hint)
        layout.addWidget(self._local_strategy_combo)
        self._local_strategy_hint = _muted("")
        self._local_strategy_hint.setObjectName("localImportStrategyHint")
        self._local_strategy_hint.setWordWrap(True)
        layout.addWidget(self._local_strategy_hint)
        self._update_local_strategy_hint()
        select_button = _button("选择本地数据", "primaryButton", self._choose_local_files)
        select_button.setMinimumHeight(44)
        folder_button = _button("选择本地文件夹", "secondaryButton", self._choose_local_folder)
        folder_button.setMinimumHeight(44)
        for button in (select_button, folder_button):
            button.setEnabled(False)
            button.setProperty("buttonBehavior", "disabled_import_gated_in_ui_c2c")
            button.setProperty("formalActionEnabled", False)
            button.setToolTip("UI-C2c 不触发真实本地导入；请使用上方 Local File 配置预览。")
        actions = QHBoxLayout()
        actions.addWidget(select_button)
        actions.addWidget(folder_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addWidget(self._source_summary_frame("local_import", "尚未选择本地数据。", detail_button_text="查看导入详情"))
        return card

    def _update_local_strategy_hint(self) -> None:
        if not hasattr(self, "_local_strategy_hint"):
            return
        if _strategy_from_combo(self._local_strategy_combo) == "copy":
            self._local_strategy_hint.setText("把数据文件复制到当前项目，便于后续复用、迁移和归档。")
        else:
            self._local_strategy_hint.setText("不复制文件；后续分析将从原位置读取，请勿移动或删除。原文件移动或删除后，项目可能无法继续读取该数据。")

    def _gse_card(self) -> QFrame:
        card, layout = _card("GSE 编号检索")
        card.setObjectName("gseSearchEntryCard")
        card.setProperty("normalUserVisible", False)
        layout.addWidget(_muted("已知 GEO 数据集编号时使用，例如 GSE33630。"))
        self._gse_input = QLineEdit()
        self._gse_input.setPlaceholderText("请输入 GSE 编号，例如 GSE33630")
        self._gse_input.setMinimumHeight(44)
        layout.addWidget(self._gse_input)
        gse_actions = QHBoxLayout()
        search_button = _button("检索数据集", "primaryButton", self.search_gse_dataset)
        search_button.setMinimumHeight(44)
        search_button.setEnabled(False)
        search_button.setProperty("buttonBehavior", "disabled_geo_download_gated_in_ui_c2c")
        search_button.setProperty("formalActionEnabled", False)
        search_button.setToolTip("UI-C2c 不触发 GEO 检索或下载；请使用上方 GEO 配置预览。")
        self._register_gse_button = _button("添加到项目", "secondaryButton", self.register_gse_dataset)
        self._register_gse_button.setEnabled(False)
        self._register_gse_button.setVisible(False)
        gse_actions.addWidget(search_button)
        gse_actions.addWidget(self._register_gse_button)
        gse_actions.addStretch(1)
        layout.addLayout(gse_actions)
        self._gse_status_label = _status_label("尚未检索 GSE 数据集。")
        layout.addWidget(self._gse_status_label)
        self._gse_summary_table = _table(["GSE 编号", "数据集标题", "物种", "平台", "样本数量", "数据状态"])
        self._gse_summary_table.setObjectName("gseDatasetSummaryTable")
        self._gse_summary_table.setMaximumHeight(120)
        self._gse_summary_table.setVisible(False)
        layout.addWidget(self._gse_summary_table)
        self._gse_search_details = _text_preview(120)
        self._gse_search_details.setVisible(False)
        self._gse_search_detail_button = _button("查看检索详情", "secondaryButton", lambda: _toggle_details(self._gse_search_details))
        self._gse_search_detail_button.setVisible(False)
        layout.addWidget(self._gse_search_detail_button, alignment=Qt.AlignLeft)
        layout.addWidget(self._gse_search_details)
        self._gse_geo_detail_panel = GeoDatasetDetailPanel()
        self._gse_geo_detail_panel.save_requested.connect(self._save_gse_geo_candidate)
        self._gse_geo_detail_panel.ignore_requested.connect(self._ignore_gse_geo_candidate)
        self._gse_geo_detail_panel.remove_requested.connect(self._remove_gse_geo_candidate)
        self._gse_geo_detail_panel.translate_requested.connect(self._generate_gse_geo_summary)
        self._gse_geo_detail_panel.brief_requested.connect(self._generate_gse_geo_summary)
        self._gse_geo_detail_panel.confirm_comparison_requested.connect(self._confirm_gse_geo_profile_comparison)
        self._gse_geo_detail_panel.manual_comparison_requested.connect(self._manual_gse_geo_profile_comparison)
        layout.addWidget(self._gse_geo_detail_panel)
        layout.addWidget(self._source_summary_frame("geo_gse", "尚未检索 GSE 数据集。", detail_button_text="查看检索详情"))
        return card

    def _research_card(self) -> QFrame:
        card, layout = _card("中文研究问题检索")
        card.setObjectName("chineseResearchSearchEntryCard")
        card.setProperty("normalUserVisible", False)
        layout.addWidget(_muted("输入中文研究方向，生成英文检索词并推荐 GEO、TCGA、GTEx 候选数据集。"))
        self._chinese_query_input = QLineEdit()
        self._chinese_query_input.setObjectName("chineseResearchTopicEntry")
        self._chinese_query_input.setPlaceholderText("请输入研究方向，例如：甲状腺癌与肥胖相关基因表达数据")
        self._chinese_query_input.setMinimumHeight(44)
        layout.addWidget(self._chinese_query_input)
        self._chinese_search_status_label = _status_label("尚未进行中文检索。")
        layout.addWidget(self._chinese_search_status_label)
        button = _button("进入检索界面", "primaryButton", self.open_chinese_search)
        button.setMinimumHeight(44)
        button.setEnabled(False)
        button.setProperty("buttonBehavior", "disabled_source_search_gated_in_ui_c2c")
        button.setProperty("formalActionEnabled", False)
        button.setToolTip("UI-C2c 数据来源页只展示四类主数据源；中文检索保留为后续/诊断入口。")
        layout.addWidget(button, alignment=Qt.AlignLeft)
        return card

    def _choose_local_data(self) -> None:
        menu = QMenu(self)
        file_action = menu.addAction("选择文件")
        folder_action = menu.addAction("选择文件夹")
        chosen = menu.exec(self.mapToGlobal(self.rect().center()))
        if chosen == file_action:
            self._choose_local_files()
        elif chosen == folder_action:
            self._choose_local_folder()

    def _choose_local_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "选择本地数据文件")
        if paths:
            self.register_local_paths(paths, source_type="local_import", source_label="本地数据导入", selected_kind="file", summary_key="local_import")

    def _choose_local_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择本地数据文件夹")
        if path:
            self.register_local_paths([path], source_type="local_import", source_label="本地数据文件夹", selected_kind="folder", summary_key="local_import")

    def _render_acquisition_summary(
        self,
        summary: AcquisitionSummary,
        *,
        selected_paths: list[Path] | None = None,
        summary_key: str | None = None,
        selected_kind: str = "file",
        display_name: str | None = None,
        absolute_path: str | None = None,
        data_type_label: str | None = None,
    ) -> None:
        self._latest_summary = summary
        key = summary_key or summary.source_type
        paths = selected_paths or []
        source_path = str(paths[0]) if paths else (absolute_path or "")
        name = display_name or _display_name_for_paths(paths, summary.source_label)
        selected_summary = SelectedSourceSummary(
            source_type=summary.source_type,
            source_label=data_type_label or summary.source_label,
            selected_kind=selected_kind,
            display_name=name,
            absolute_path=source_path,
            storage_policy=summary.strategy,
            acquisition_status=_acquisition_status_text(summary),
            acquisition_plan_path=str(summary.plan_path),
            acquisition_record_path=str(summary.record_path),
            handoff_path=str(summary.handoff_path),
            created_at=summary.created_at,
            warnings=tuple(summary.warnings),
        )
        self._source_summaries[key] = selected_summary
        self._update_source_summary_label(key, selected_summary)
        self._set_status("先添加数据，下一步进入数据识别。")
        self._technical_details.setPlainText(_selected_source_technical_details(selected_summary))

    def source_summary_text(self, key: str) -> str:
        label = self._source_summary_labels.get(key)
        return label.text() if label is not None else ""

    def source_summary_tooltip(self, key: str) -> str:
        label = self._source_summary_labels.get(key)
        return label.toolTip() if label is not None else ""

    def copy_selected_source_path(self, key: str) -> bool:
        summary = self._source_summaries.get(key)
        if summary is None or not summary.absolute_path:
            self._set_status("未记录来源位置。", error=True)
            return False
        QApplication.clipboard().setText(summary.absolute_path)
        self._set_status(f"已复制来源路径：{_compact_path(summary.absolute_path)}")
        return True

    def open_selected_source_location(self, key: str) -> bool:
        summary = self._source_summaries.get(key)
        if summary is None or not summary.absolute_path:
            self._set_status("未记录来源位置。", error=True)
            return False
        path = Path(summary.absolute_path)
        target = path if path.is_dir() else path.parent
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
        self._set_status(f"已请求打开来源位置：{_compact_path(str(target))}")
        return True

    def _source_summary_frame(self, key: str, empty_text: str, *, detail_button_text: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("selectedSourceSummary")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["sm"], SPACING["sm"], SPACING["sm"], SPACING["sm"])
        layout.setSpacing(SPACING["xs"])
        label = _muted(empty_text)
        label.setObjectName(f"{key}SourceSummaryText")
        label.setToolTip(empty_text)
        layout.addWidget(label)
        actions = QHBoxLayout()
        open_button = _button("打开来源位置", "secondaryButton", lambda checked=False, k=key: self.open_selected_source_location(k))
        copy_button = _button("复制路径", "secondaryButton", lambda checked=False, k=key: self.copy_selected_source_path(k))
        open_button.setObjectName(f"{key}OpenSourceButton")
        copy_button.setObjectName(f"{key}CopyPathButton")
        open_button.setEnabled(False)
        copy_button.setEnabled(False)
        open_button.setVisible(False)
        copy_button.setVisible(False)
        details_button = _button(detail_button_text, "secondaryButton", lambda checked=False, k=key: self._toggle_source_detail(k))
        details_button.setVisible(False)
        actions.addWidget(open_button)
        actions.addWidget(copy_button)
        actions.addWidget(details_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        detail_edit = _text_preview(120)
        detail_edit.setVisible(False)
        layout.addWidget(detail_edit)
        self._source_summary_labels[key] = label
        self._source_action_buttons[key] = (open_button, copy_button)
        self._source_detail_buttons[key] = details_button
        self._source_detail_edits[key] = detail_edit
        return frame

    def _update_source_summary_label(self, key: str, summary: SelectedSourceSummary) -> None:
        label = self._source_summary_labels.get(key)
        if label is not None:
            label.setText(_source_card_status_text(summary))
            label.setToolTip(_selected_source_summary_text(summary, compact=False))
        detail = self._source_detail_edits.get(key)
        if detail is not None:
            detail.setPlainText(_selected_source_summary_text(summary, compact=False))
        details_button = self._source_detail_buttons.get(key)
        if details_button is not None:
            details_button.setVisible(True)
        buttons = self._source_action_buttons.get(key)
        if buttons is not None:
            has_path = bool(summary.absolute_path)
            for button in buttons:
                button.setEnabled(has_path)
                button.setVisible(False)

    def _render_gse_preview(self, preview: GseDatasetPreview) -> None:
        self._gse_status_label.setText(f"已添加 GSE 数据集：{preview.gse_id}" if preview.status == "已选择" else f"已检索到：{preview.gse_id}")
        self._gse_summary_table.setVisible(False)
        _fill_table(
            self._gse_summary_table,
            [[preview.gse_id, preview.title, preview.organism, preview.platform, preview.sample_count, preview.status]],
        )
        self._gse_search_details.setPlainText(
            _json(
                {
                    "GSE 编号": preview.gse_id,
                    "数据集标题": preview.title,
                    "物种": preview.organism,
                    "平台": preview.platform,
                    "样本数量": preview.sample_count,
                    "数据状态": preview.status,
                }
            )
        )
        self._gse_search_detail_button.setVisible(True)
        self._register_gse_button.setVisible(preview.status != "已选择")
        self._register_gse_button.setEnabled(preview.status != "已选择")

    def _show_gse_geo_detail(self, candidate: UnifiedDatasetCandidate) -> None:
        self._geo_candidates[candidate.accession_or_project] = candidate
        self._gse_geo_detail_panel.show_candidate(
            candidate,
            project_root=self._project_root,
            summary_payload=self._geo_brief_cache.get(candidate.accession_or_project),
            saved=_is_geo_saved_to_download_list(self._project_root, candidate.accession_or_project),
        )

    def _show_gse_geo_detail_by_accession(self, accession: str) -> None:
        accession = accession.split(":", 1)[1] if accession.startswith("geo:") else accession
        candidate = self._geo_candidates.get(accession) or _geo_candidate_from_download_entry(self._project_root, accession)
        if candidate is None:
            self._set_status(f"未找到 GEO 数据集详情：{accession}", error=True)
            return
        self._show_gse_geo_detail(candidate)
        self._set_status(f"正在查看：{accession}")

    def _save_gse_geo_candidate(self, candidate: UnifiedDatasetCandidate) -> AcquisitionSummary | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        if _is_geo_saved_to_download_list(self._project_root, candidate.accession_or_project):
            self._set_status(f"已在待处理数据集中：{candidate.accession_or_project}")
            self._show_gse_geo_detail(candidate)
            self._refresh_geo_download_list()
            return None
        metadata = _candidate_registration_metadata(candidate, None, "GSE 编号检索")
        metadata.update({"ui_source": "gse_accession_search", "query_source": "gse_accession_search"})
        summary = register_acquisition(
            self._project_root,
            source_type="geo_accession",
            source_label=candidate.accession_or_project,
            strategy="plan_only",
            selected_paths=[],
            metadata=metadata,
        )
        self._latest_summary = summary
        self._refresh_geo_download_list()
        self._show_gse_geo_detail(candidate)
        self._set_status(f"{candidate.accession_or_project} 已添加到待处理数据集。")
        return summary

    def _ignore_gse_geo_candidate(self, candidate: UnifiedDatasetCandidate) -> None:
        self._gse_geo_detail_panel.setVisible(False)
        self._set_status(f"已忽略：{candidate.accession_or_project}")

    def _remove_gse_geo_candidate(self, candidate: UnifiedDatasetCandidate) -> None:
        self._remove_gse_geo_accession(candidate.accession_or_project)

    def _remove_gse_geo_accession(self, accession: str) -> None:
        if _remove_geo_download_entry(self._project_root, accession):
            self._refresh_registered_sources()
            self._refresh_geo_download_list()
            candidate = self._geo_candidates.get(accession)
            if candidate is not None:
                self._show_gse_geo_detail(candidate)
            self._set_status(f"已从待处理数据集中移除：{accession}")
        else:
            self._set_status(f"待处理数据集中未找到：{accession}", error=True)

    def _generate_gse_geo_summary(self, candidate: UnifiedDatasetCandidate) -> dict[str, object] | None:
        cached = self._geo_brief_cache.get(candidate.accession_or_project)
        if cached is not None:
            self._gse_geo_detail_panel.render_summary(candidate, cached)
            self._set_status("已显示中文简介。")
            return cached
        self._gse_geo_detail_panel.set_busy_text("正在生成中文翻译与提炼，请稍候。")
        QApplication.processEvents()
        metadata = candidate.source_specific_metadata
        summary_en = str(metadata.get("summary_en") or "")
        overall_design_en = str(metadata.get("overall_design_en") or "")
        sample_overview_en = str(metadata.get("sample_summary") or _geo_sample_overview_for_summary(metadata))
        if not summary_en.strip() and not overall_design_en.strip():
            payload = {
                "status": "missing_source_metadata",
                "title_zh": "",
                "summary_zh": "",
                "overall_design_zh": "",
                "brief_zh": "未抓取到 GEO Summary / Overall design，无法生成可靠中文提炼。",
                "error_message": "未抓取到 GEO Summary / Overall design，无法翻译。",
                "quality_warnings": ["未抓取到 GEO Summary / Overall design，无法翻译。"],
            }
            self._geo_brief_cache[candidate.accession_or_project] = payload
            self._gse_geo_detail_panel.render_summary(candidate, payload)
            self._set_status("未抓取到 GEO Summary / Overall design，无法翻译。", error=True)
            return payload
        text_input = GeoStudyTextInput(
            accession=candidate.accession_or_project,
            title_en=str(metadata.get("title_en") or candidate.display_title),
            summary_en=summary_en,
            overall_design_en=overall_design_en,
            sample_overview_en=sample_overview_en,
        )
        summary = self._text_summary_service.summarize(text_input)
        payload = summary.to_dict()
        draft_record = _geo_text_summary_draft_record(text_input, payload)
        payload["ai_draft"] = draft_record.to_dict()
        if self._project_root is not None:
            save_ai_draft_record(self._project_root, draft_record, filename_hint=f"bio_translate_dataset_detail_{candidate.accession_or_project}")
        self._geo_brief_cache[candidate.accession_or_project] = payload
        self._gse_geo_detail_panel.render_summary(candidate, payload)
        self._set_status("已生成中文翻译与提炼草稿。" if summary.status == "completed" else "中文提炼草稿需人工确认。")
        return payload

    def _confirm_gse_geo_profile_comparison(self, candidate: UnifiedDatasetCandidate) -> bool:
        ok, message = _save_geo_profile_comparison_with_confirmation(
            self,
            self._project_root,
            candidate,
            self._geo_brief_cache.get(candidate.accession_or_project),
        )
        self._set_status(message, error=not ok)
        self._show_gse_geo_detail(candidate)
        return ok

    def _manual_gse_geo_profile_comparison(self, candidate: UnifiedDatasetCandidate) -> bool:
        text, ok = QInputDialog.getMultiLineText(
            self,
            "手动设置比较组",
            "请按 TSV 格式输入比较组；保存后才会作为正式比较组设置。",
            _template_text_for_missing_input("comparison_config"),
        )
        if not ok:
            self._set_status("已取消手动设置比较组。")
            return False
        saved, message = _save_geo_profile_comparison_with_confirmation(
            self,
            self._project_root,
            candidate,
            self._geo_brief_cache.get(candidate.accession_or_project),
            manual_text=text,
        )
        self._set_status(message, error=not saved)
        self._show_gse_geo_detail(candidate)
        return saved

    def _download_gse_geo_metadata(self, accession: str) -> object | None:
        candidate = self._geo_candidates.get(accession) or _geo_candidate_from_download_entry(self._project_root, accession)
        if candidate is None:
            self._set_status(f"未找到 GEO 数据集：{accession}", error=True)
            return None
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        self._set_status(f"正在下载 GEO 元数据：{accession}，请稍候。")
        QApplication.processEvents()
        result = self._download_service.create_candidate_download_task(
            project_root=self._project_root,
            candidate=candidate,
            search_result=None,
            original_chinese_topic="GSE 编号检索",
            execute_download=True,
        )
        self._refresh_registered_sources()
        self._refresh_geo_download_list()
        self._show_gse_geo_detail(candidate)
        self._set_status(result.message if result.success else (result.message or "GEO 下载未完成，请稍后重试。"), error=not result.success)
        return result

    def _download_gse_geo_assets(self, accession: str) -> object | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        try:
            result = self._download_service.download_geo_manifest_assets(project_root=self._project_root, accession_or_project=accession)
        except Exception as exc:
            self._set_status(f"补充文件下载失败：{exc}", error=True)
            return None
        self._refresh_registered_sources()
        self._refresh_geo_download_list()
        self._show_gse_geo_detail_by_accession(accession)
        self._set_status(result.message if result.success else (result.message or "未下载到补充文件，请检查 manifest。"), error=not result.success)
        return result

    def _refresh_registered_sources(self) -> None:
        rows = _registered_source_rows(self._project_root)
        self._refresh_geo_download_list()
        self._refresh_history_cache()
        count = len(_current_project_dataset_entries(self._project_root))
        ready_count = _ready_registered_source_count(self._project_root)
        self._registered_count_label.setText(f"已选择的数据：{count} 个；可进入识别：{ready_count} 个")
        self._next_button.setEnabled(ready_count > 0 and self._project_root is not None)
        self._chinese_search_status_label.setText(_chinese_search_entry_status(rows))
        self._render_gated_source_tables(selected_source="")

    def _refresh_geo_download_list(self) -> None:
        entries = _current_project_dataset_entries(self._project_root)
        self._dataset_entries = {entry.key: entry for entry in entries}
        panel = getattr(self, "_dataset_list_panel", None)
        if panel is not None:
            panel.refresh(self._project_root)

    def _refresh_history_cache(self) -> None:
        entries = _historical_cache_entries(self._project_root)
        card = getattr(self, "_history_cache_card", None)
        if card is None:
            return
        card.setVisible(True)
        self._history_cache_hint.setText(f"发现 {len(entries)} 个历史下载数据集，尚未加入当前项目。" if entries else "暂无历史缓存数据。")
        self._history_cache_table.setVisible(bool(entries))
        _fill_table(self._history_cache_table, [[entry["name"], _compact_path(entry["path"], max_chars=64), "加入当前项目 / 查看 / 删除缓存"] for entry in entries])
        for row_index, entry in enumerate(entries):
            self._history_cache_table.setCellWidget(row_index, 2, self._history_cache_action_widget(entry))
            item = self._history_cache_table.item(row_index, 1)
            if item is not None:
                item.setToolTip(entry["path"])
        _configure_history_cache_table(self._history_cache_table)

    def _history_cache_action_widget(self, entry: dict[str, str]) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        add_button = QPushButton("加入当前项目")
        view_button = QPushButton("查看")
        delete_button = QPushButton("删除缓存")
        add_button.clicked.connect(lambda checked=False, item=entry: self._add_history_cache_to_project(item))
        view_button.clicked.connect(lambda checked=False, path=entry["path"]: _open_path(Path(path)))
        delete_button.clicked.connect(lambda checked=False, item=entry: self._delete_history_cache_entry(item))
        layout.addWidget(add_button)
        layout.addWidget(view_button)
        layout.addWidget(delete_button)
        layout.addStretch(1)
        return widget

    def _delete_history_cache_entry(self, entry: dict[str, str]) -> bool:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return False
        response = QMessageBox.question(
            self,
            "确认删除缓存？",
            "这将删除该历史缓存数据，并从历史缓存列表中移除。不会删除当前项目已选择的数据，也不会删除你手动导入的原始文件。",
            QMessageBox.Cancel | QMessageBox.Yes,
            QMessageBox.Cancel,
        )
        if response != QMessageBox.Yes:
            self._show_data_source_status("已取消删除缓存。")
            return False
        target = Path(entry.get("path", ""))
        ok, message = _delete_historical_cache_path(self._project_root, target, entry.get("name", ""))
        self._refresh_history_cache()
        self._show_data_source_status(message, error=not ok)
        return ok

    def _add_history_cache_to_project(self, entry: dict[str, str]) -> AcquisitionSummary | None:
        path = Path(entry["path"])
        if not path.exists():
            self._set_status("历史缓存路径不存在。", error=True)
            return None
        summary = self.register_local_paths(
            [path],
            source_type="local_import",
            source_label="历史缓存数据",
            strategy="reference",
            selected_kind="folder" if path.is_dir() else "file",
            summary_key="local_import",
            data_type_label="历史缓存数据",
        )
        if summary is not None:
            self._refresh_registered_sources()
            self._status_label.setText("已加入当前项目")
            self._status_label.setProperty("status", "ok")
            _refresh_style(self._status_label)
        else:
            self._set_status("加入当前项目失败。", error=True)
        return summary

    def _show_dataset_detail(self, key: str) -> None:
        entry = self._dataset_entries.get(key)
        if entry is None:
            self._set_status("未找到数据详情。", error=True)
            return
        self._dataset_detail_panel.show_entry(entry)
        self._set_status(f"正在查看：{entry.name}")

    def _save_dataset_note(self, key: str, note: str) -> None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return
        _save_user_dataset_note(self._project_root, key, note)
        self._refresh_registered_sources()
        entry = self._dataset_entries.get(key)
        if entry is not None:
            self._dataset_detail_panel.show_entry(entry)
        self._set_status("备注已保存。")

    def _download_selected_dataset_entries(self, keys: tuple[str, ...]) -> None:
        for key in keys:
            entry = self._dataset_entries.get(key)
            if entry is None or not entry.downloadable:
                continue
            if entry.accession:
                if _candidate_has_pending_geo_assets(self._project_root, entry.accession):
                    self._download_gse_geo_assets(entry.accession)
                else:
                    self._download_gse_geo_metadata(entry.accession)
        self._refresh_registered_sources()

    def _delete_selected_dataset_entries(self, keys: tuple[str, ...]) -> None:
        if self._project_root is None:
            return
        removed = 0
        for key in keys:
            entry = self._dataset_entries.get(key)
            if entry is None or not entry.removable:
                continue
            if _remove_dataset_project_binding(self._project_root, entry):
                removed += 1
        self._dataset_detail_panel.setVisible(False)
        self._refresh_registered_sources()
        self._set_status(f"已从当前项目列表移除 {removed} 个条目；未删除原始文件。")

    def _registered_source_count(self) -> int:
        return _ready_registered_source_count(self._project_root)

    def _toggle_source_detail(self, key: str) -> None:
        detail = self._source_detail_edits.get(key)
        if detail is not None:
            _toggle_details(detail)

    def _set_status(self, text: str, *, error: bool = False) -> None:
        self._status_label.setText(text)
        self._status_label.setProperty("status", "error" if error else "ok")
        _refresh_style(self._status_label)

    def _show_data_source_status(self, text: str, *, error: bool = False) -> None:
        self._status_label.setText(text)
        self._status_label.setProperty("status", "error" if error else "ok")
        _refresh_style(self._status_label)


class BioinformaticsChineseDatasetSearchWidget(QWidget):
    back_requested = Signal()
    continue_requested = Signal(object)
    source_registered = Signal(object)

    def __init__(
        self,
        *,
        on_back: Callable[[], None] | None = None,
        on_continue: Callable[[Path], None] | None = None,
        on_source_registered: Callable[[object], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self._last_result: BioinformaticsSearchCenterResult | None = None
        self._last_render_searched = False
        self._candidates: dict[tuple[str, str], UnifiedDatasetCandidate] = {}
        self._candidate_register_buttons: dict[tuple[str, str], QPushButton] = {}
        self._candidate_download_buttons: dict[tuple[str, str], QPushButton] = {}
        self._geo_brief_cache: dict[str, dict[str, object]] = {}
        self._selected_candidate: UnifiedDatasetCandidate | None = None
        self._source_detail_titles: dict[str, QLabel] = {}
        self._source_detail_texts: dict[str, QPlainTextEdit] = {}
        self._source_detail_select_buttons: dict[str, QPushButton] = {}
        self._source_detail_download_buttons: dict[str, QPushButton] = {}
        self._source_detail_brief_buttons: dict[str, QPushButton] = {}
        self._source_registered_empty_labels: dict[str, QLabel] = {}
        self._source_registered_tables: dict[str, QTableWidget] = {}
        self._source_recommendation_empty_labels: dict[str, QLabel] = {}
        self._source_recommendation_widgets: dict[str, QWidget] = {}
        self._source_recommendation_layouts: dict[str, QVBoxLayout] = {}
        self._candidate_status_labels: dict[tuple[str, str], QLabel] = {}
        self._query_draft_record: AIDraftRecord | None = None
        self._download_service = DatasetDownloadService()
        self._text_summary_service = GeoTextSummaryService(timeout=20)
        self.setObjectName("bioinformaticsChineseDatasetSearchPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_back is not None:
            self.back_requested.connect(on_back)
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_source_registered is not None:
            self.source_registered.connect(on_source_registered)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self._project_label.setText(_project_header_text(summary))
        self._refresh_registered_sources()
        self._refresh_candidate_registration_buttons()

    def set_query_text(self, text: str) -> None:
        self._query_input.setText(text)

    def status_message(self) -> str:
        return self._status_label.text()

    def generate_terms(self) -> BioinformaticsSearchCenterResult | None:
        query = self._query_input.text().strip()
        if not query:
            self._set_status("请输入中文研究主题。", error=True)
            return None
        local_model_config = _desktop_local_model_config()
        result = BioinformaticsSourceRouter().search(
            query,
            online_enabled=False,
            limit=20,
            use_local_model=local_model_config.enabled,
            local_model_config=local_model_config,
            gateway_module="bioinformatics",
            gateway_task_type="bio_generate_dataset_query_draft",
        )
        self._last_result = result
        self._render_result(result, searched=False)
        self._query_draft_record = self._create_query_draft_record(result, status="suggested")
        if result.query.broad_query_guard:
            self._set_status("请补充明确疾病或组织主题后再检索候选数据集。", error=True)
        else:
            self._set_status("已生成检索草稿。确认前不会执行真实数据库检索。")
        return result

    def search_candidates(self, *, online_enabled: bool = False) -> BioinformaticsSearchCenterResult | None:
        return self.confirm_query_draft() if online_enabled else self.generate_terms()

    def search_geo_candidates(self) -> BioinformaticsSearchCenterResult | None:
        draft = self._ensure_draft_result()
        if draft is None:
            return None
        self._set_status("正在在线检索 GEO/GSE 候选数据集，请稍候。")
        QApplication.processEvents()
        geo_result = GeoSearchAdapter().search(draft.query, online_enabled=True, limit=20)
        result = _merge_source_search_result(draft, "geo", geo_result, online_enabled=True)
        self._last_result = result
        self._render_result(result, searched=True)
        geo_result = result.source_results.get("geo")
        if geo_result is None:
            self._set_status("未生成 GEO/GSE 检索草稿。", error=True)
        elif geo_result.search_status == "search_failed":
            self._set_status("GEO/GSE 在线检索失败，请检查网络或稍后重试。", error=True)
        elif geo_result.displayed_count == 0:
            self._set_status("未检索到符合条件的 GEO/GSE 数据集。")
        else:
            self._set_status("已完成 GEO/GSE 在线检索。")
        return result

    def search_tcga_candidates(self) -> BioinformaticsSearchCenterResult | None:
        draft = self._ensure_draft_result()
        if draft is None:
            return None
        self._set_status("正在在线检查 TCGA/GDC 项目资产，请稍候。")
        QApplication.processEvents()
        tcga_result = TcgaGdcSearchAdapter().search(draft.query, online_enabled=True, limit=20)
        if not tcga_result.candidates and draft.source_results.get("tcga_gdc") is not None:
            tcga_result = draft.source_results["tcga_gdc"]
        result = _merge_source_search_result(draft, "tcga_gdc", tcga_result, online_enabled=True)
        self._last_result = result
        self._render_result(result, searched=False)
        candidates = [candidate for candidate in result.candidates if candidate.source == "tcga_gdc"]
        self._set_status(
            "已完成 TCGA/GDC 在线检查，可创建 GDC 文件清单。"
            if candidates
            else "未生成 TCGA/GDC 项目候选。"
        )
        return result

    def search_gtex_candidates(self) -> BioinformaticsSearchCenterResult | None:
        draft = self._ensure_draft_result()
        if draft is None:
            return None
        self._set_status("正在在线检查 GTEx 组织参考，请稍候。")
        QApplication.processEvents()
        gtex_result = GtexSearchAdapter().search(draft.query, online_enabled=True, limit=20)
        if not gtex_result.candidates and draft.source_results.get("gtex") is not None:
            gtex_result = draft.source_results["gtex"]
        result = _merge_source_search_result(draft, "gtex", gtex_result, online_enabled=True)
        self._last_result = result
        self._render_result(result, searched=False)
        candidates = [candidate for candidate in result.candidates if candidate.source == "gtex"]
        self._set_status(
            "已完成 GTEx 在线检查，可创建组织参考清单。"
            if candidates
            else "未生成 GTEx 组织候选。"
        )
        return result

    def confirm_query_draft(self) -> AIDraftRecord | None:
        draft = self._ensure_draft_result()
        if draft is None:
            return None
        editable_output = "\n".join(
            [
                self._geo_query_box.toPlainText().strip(),
                self._tcga_query_box.toPlainText().strip(),
                self._gtex_query_box.toPlainText().strip(),
            ]
        )
        record = self._query_draft_record or self._create_query_draft_record(draft, status="suggested")
        generated_output = _query_draft_output_text(draft)
        if editable_output and editable_output != generated_output:
            record = mark_ai_draft_status(record, "user_edited", output_text=editable_output, summary=_query_draft_summary(draft, editable_output=editable_output))
        record = mark_ai_draft_status(record, "confirmed", output_text=editable_output or generated_output, summary=_query_draft_summary(draft, editable_output=editable_output))
        self._query_draft_record = record
        if self._project_root is not None:
            save_ai_draft_record(self._project_root, record, filename_hint="bio_generate_dataset_query_draft")
        self._set_status("已确认检索草稿。确认本身不联网；如需联网请点击在线检索/在线检查。")
        return record

    def register_candidate(self, source: str, accession_or_project: str) -> AcquisitionSummary | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        candidate = self._candidates.get((source, accession_or_project))
        if candidate is None:
            self._set_status("候选结果不存在。", error=True)
            return None
        if self._is_candidate_registered(source, accession_or_project):
            self._set_status(f"已选择数据：{accession_or_project}")
            self._refresh_candidate_registration_buttons()
            return None
        summary = register_acquisition(
            self._project_root,
            source_type=_candidate_source_type(candidate),
            source_label=candidate.accession_or_project,
            strategy="plan_only",
            selected_paths=[],
            metadata=_candidate_registration_metadata(candidate, self._last_result, self._query_input.text().strip()),
        )
        self._refresh_registered_sources()
        if self._last_result is not None:
            self._render_candidate_tables(self._last_result, searched=self._last_render_searched)
        else:
            self._refresh_candidate_registration_buttons()
        self.source_registered.emit(summary)
        self._set_status("已选择候选来源，待下载数据文件。")
        return summary

    def generate_candidate_download_task(self, source: str, accession_or_project: str, *, execute_download: bool | None = None) -> object | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        candidate = self._candidates.get((source, accession_or_project))
        if candidate is None:
            self._set_status("候选结果不存在。", error=True)
            return None
        if source != "geo" and _candidate_has_download_manifest(self._project_root, source, accession_or_project):
            self._set_status(_candidate_record_status_text(self._project_root, source, accession_or_project) or f"下载清单已创建：{accession_or_project}")
            self._refresh_candidate_registration_buttons()
            return None
        if source == "geo" and self._is_candidate_ready_for_recognition(source, accession_or_project):
            if source == "geo":
                self._set_status(_candidate_record_status_text(self._project_root, source, accession_or_project) or f"元数据已下载：{accession_or_project}")
            else:
                self._set_status(f"已生成下载任务：{accession_or_project}")
            self._refresh_candidate_registration_buttons()
            return None
        should_execute = source != "geo" if execute_download is None else execute_download
        result = self._download_service.create_candidate_download_task(
            project_root=self._project_root,
            candidate=candidate,
            search_result=self._last_result,
            original_chinese_topic=self._query_input.text().strip(),
            execute_download=should_execute,
        )
        self._refresh_registered_sources()
        if self._last_result is not None:
            self._render_candidate_tables(self._last_result, searched=self._last_render_searched)
        self.source_registered.emit(result.acquisition_summary)
        self._set_status(result.message or "已生成下载任务，等待下载数据文件。")
        return result

    def download_geo_candidate(self, accession_or_project: str) -> object | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        candidate = self._candidates.get(("geo", accession_or_project)) or _geo_candidate_from_download_entry(self._project_root, accession_or_project)
        if candidate is None:
            self._set_status("GEO/GSE 候选结果不存在。", error=True)
            return None
        self._candidates[("geo", candidate.accession_or_project)] = candidate
        if self._is_candidate_ready_for_recognition("geo", accession_or_project):
            if _candidate_has_pending_geo_assets(self._project_root, accession_or_project):
                return self.download_geo_supplementary_assets(accession_or_project)
            self._set_status(_candidate_record_status_text(self._project_root, "geo", accession_or_project) or f"元数据已下载：{accession_or_project}")
            self._refresh_candidate_registration_buttons()
            return None
        self._set_status(f"正在下载 GEO 数据：{accession_or_project}，请稍候。")
        QApplication.processEvents()
        result = self._download_service.create_candidate_download_task(
            project_root=self._project_root,
            candidate=candidate,
            search_result=self._last_result,
            original_chinese_topic=self._query_input.text().strip(),
            execute_download=True,
        )
        self._refresh_registered_sources()
        if self._last_result is not None:
            self._render_candidate_tables(self._last_result, searched=self._last_render_searched)
        else:
            self._refresh_candidate_registration_buttons()
            self._refresh_candidate_status_cells()
        self.source_registered.emit(result.acquisition_summary)
        self._refresh_open_geo_detail(accession_or_project)
        if result.success and result.downloaded_files:
            report = run_project_recognition(self._project_root)
            file_count = len(report.get("files", []) or []) if isinstance(report, dict) else 0
            self._set_status(f"{result.message}（已完成元数据识别：{file_count} 个文件）。")
        else:
            self._set_status(result.message or "GEO 下载未完成，请稍后重试。", error=True)
        return result

    def download_geo_supplementary_assets(self, accession_or_project: str) -> object | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        if not _candidate_has_pending_geo_assets(self._project_root, accession_or_project):
            self._set_status("未发现待下载的 Matrix 或补充文件。")
            self._refresh_candidate_registration_buttons()
            return None
        self._set_status(f"正在下载补充文件：{accession_or_project}，请稍候。")
        QApplication.processEvents()
        try:
            result = self._download_service.download_geo_manifest_assets(
                project_root=self._project_root,
                accession_or_project=accession_or_project,
            )
        except Exception as exc:
            self._set_status(f"补充文件下载失败：{exc}", error=True)
            return None
        self._refresh_registered_sources()
        if self._last_result is not None:
            self._render_candidate_tables(self._last_result, searched=self._last_render_searched)
        else:
            self._refresh_candidate_registration_buttons()
            self._refresh_candidate_status_cells()
        self.source_registered.emit(result.acquisition_summary)
        self._refresh_open_geo_detail(accession_or_project)
        if result.success and result.downloaded_files:
            recognition = run_project_recognition(self._project_root)
            readiness = run_project_readiness(self._project_root)
            standardization = generate_standardized_assets(self._project_root)
            load_analysis_task_center(self._project_root)
            file_count = len(recognition.get("files", []) or []) if isinstance(recognition, dict) else 0
            available = readiness.get("readiness_report", {}).get("available_inputs", []) if isinstance(readiness, dict) else []
            task_count = len(standardization.get("data_processing_task_plan", {}).get("tasks", []) or []) if isinstance(standardization, dict) else 0
            self._set_status(f"{result.message}（已识别 {file_count} 个文件；数据处理任务 {task_count} 项；可用资产：{', '.join(available) or '待确认'}）。")
        else:
            self._set_status(result.message or "未下载到补充文件，请检查 manifest。", error=True)
        return result

    def _refresh_open_geo_detail(self, accession_or_project: str) -> None:
        current = self._geo_dataset_detail_panel.current_candidate()
        if current is None or current.accession_or_project != accession_or_project:
            return
        self._geo_dataset_detail_panel.show_candidate(
            current,
            project_root=self._project_root,
            summary_payload=self._geo_brief_cache.get(accession_or_project),
            saved=_is_geo_saved_to_download_list(self._project_root, accession_or_project),
        )

    def generate_geo_chinese_brief(self, accession_or_project: str) -> dict[str, object] | None:
        candidate = self._candidates.get(("geo", accession_or_project))
        if candidate is None:
            self._set_status("候选结果不存在。", error=True)
            return None
        if self._geo_dataset_detail_panel.current_candidate() is None or self._geo_dataset_detail_panel.current_candidate().accession_or_project != accession_or_project:
            self._show_geo_candidate_detail(candidate)
        cached = self._geo_brief_cache.get(accession_or_project)
        if cached is not None and str(cached.get("status") or "") == "completed":
            self._geo_dataset_detail_panel.render_summary(candidate, cached)
            self._set_status("已显示中文简介。")
            return cached
        busy_text = "正在重新生成中文翻译与提炼，请稍候。" if cached is not None else "正在生成中文翻译与提炼，请稍候。"
        self._geo_dataset_detail_panel.set_busy_text(busy_text)
        QApplication.processEvents()
        metadata = candidate.source_specific_metadata
        text_input = GeoStudyTextInput(
            accession=accession_or_project,
            title_en=str(metadata.get("title_en") or candidate.display_title),
            summary_en=str(metadata.get("summary_en") or ""),
            overall_design_en=str(metadata.get("overall_design_en") or ""),
        )
        summary = self._text_summary_service.summarize(text_input)
        payload = summary.to_dict()
        draft_record = _geo_text_summary_draft_record(text_input, payload)
        payload["ai_draft"] = draft_record.to_dict()
        if self._project_root is not None:
            save_ai_draft_record(self._project_root, draft_record, filename_hint=f"bio_translate_dataset_detail_{accession_or_project}")
        self._geo_brief_cache[accession_or_project] = payload
        self._geo_dataset_detail_panel.render_summary(candidate, payload)
        if summary.status == "completed":
            self._set_status("已生成中文翻译与提炼草稿。")
        else:
            self._set_status("中文提炼草稿需人工确认。")
        return payload

    def _confirm_geo_profile_comparison(self, candidate: UnifiedDatasetCandidate) -> bool:
        ok, message = _save_geo_profile_comparison_with_confirmation(
            self,
            self._project_root,
            candidate,
            self._geo_brief_cache.get(candidate.accession_or_project),
        )
        self._set_status(message, error=not ok)
        self._show_geo_candidate_detail(candidate)
        return ok

    def _manual_geo_profile_comparison(self, candidate: UnifiedDatasetCandidate) -> bool:
        text, ok = QInputDialog.getMultiLineText(
            self,
            "手动设置比较组",
            "请按 TSV 格式输入比较组；保存后才会作为正式比较组设置。",
            _template_text_for_missing_input("comparison_config"),
        )
        if not ok:
            self._set_status("已取消手动设置比较组。")
            return False
        saved, message = _save_geo_profile_comparison_with_confirmation(
            self,
            self._project_root,
            candidate,
            self._geo_brief_cache.get(candidate.accession_or_project),
            manual_text=text,
        )
        self._set_status(message, error=not saved)
        self._show_geo_candidate_detail(candidate)
        return saved

    def continue_to_recognition(self) -> None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return
        if self._registered_source_count() == 0:
            self._set_status("请先选择至少一个数据源。", error=True)
            return
        _save_pending_recognition_selection(self._project_root, [])
        self.continue_requested.emit(self._project_root)

    def copy_query(self, source: str) -> bool:
        edit = {"geo": self._geo_query_box, "tcga": self._tcga_query_box, "gtex": self._gtex_query_box}.get(source)
        if edit is None:
            return False
        QApplication.clipboard().setText(edit.toPlainText())
        self._set_status("已复制草稿。")
        return True

    def _create_query_draft_record(self, result: BioinformaticsSearchCenterResult, *, status: str) -> AIDraftRecord:
        query = result.query
        provider = str(query.metadata.get("local_model_status") or "disabled")
        draft = query.metadata.get("search_translation_draft")
        model = ""
        if draft is not None:
            audit = getattr(draft, "audit", {})
            local_model = audit.get("local_model") if isinstance(audit, dict) else None
            if isinstance(local_model, dict):
                provider = str(local_model.get("provider_name") or provider)
                model = str(local_model.get("model_name") or "")
        return create_ai_draft_record(
            module="bioinformatics",
            task_type="bio_generate_dataset_query_draft",
            provider=provider,
            model=model,
            input_text=query.original_query_zh,
            output_text=_query_draft_output_text(result),
            warnings=query.warnings,
            summary=_query_draft_summary(result),
            status=status,
        )

    def _build_ui(self) -> None:
        root = _scroll_root(self, max_width=1080)
        root.addWidget(_header("中文研究问题检索", "输入中文研究方向，选择 GEO、TCGA/GDC、GTEx 数据源后进入数据识别。", back_text="返回数据来源", back_signal=self.back_requested))
        self._project_label = _status_label("请先创建或打开生信分析项目。")
        root.addWidget(self._project_label)
        input_card, input_layout = _card("研究主题输入")
        self._query_input = QLineEdit()
        self._query_input.setPlaceholderText("例如：甲状腺癌、乳腺癌转移、肺癌免疫治疗耐药")
        self._query_input.setMinimumHeight(44)
        input_layout.addWidget(self._query_input)
        action_row = QHBoxLayout()
        action_row.addWidget(_button("生成草稿", "primaryButton", self.generate_terms))
        action_row.addStretch(1)
        input_layout.addLayout(action_row)
        self._status_label = _status_label("未生成检索词")
        input_layout.addWidget(self._status_label)
        self._topic_summary_label = _status_label("主题识别：尚未开始。")
        input_layout.addWidget(self._topic_summary_label)
        root.addWidget(input_card)

        result_card, result_layout = _card("数据库区")
        self._tabs = QTabWidget()
        self._draft_detail_widgets: list[QWidget] = []
        self._geo_tab_page = self._build_database_tab(
            source_key="geo",
            draft_title="GEO/GSE 检索草稿",
            draft_placeholder="暂无 GEO/GSE 检索草稿",
            copy_source="geo",
            search_text="在线检索 GEO/GSE",
            search_callback=self.search_geo_candidates,
            candidate_headers=["操作", "GSE 编号", "标题", "样本数", "数据类型/平台", "分析潜力", "资产状态"],
            selected_empty="尚未选择 GEO/GSE 数据源。",
        )
        self._tcga_tab_page = self._build_database_tab(
            source_key="tcga_gdc",
            draft_title="TCGA/GDC 项目草稿",
            draft_placeholder="暂无 TCGA/GDC 项目草稿",
            copy_source="tcga",
            search_text="在线检查 TCGA/GDC",
            search_callback=self.search_tcga_candidates,
            candidate_headers=["操作", "项目代码", "癌种/项目名称", "样本类型", "数据类型", "状态"],
            selected_empty="尚未选择 TCGA/GDC 项目。",
            presentation="tcga_cards",
        )
        self._gtex_tab_page = self._build_database_tab(
            source_key="gtex",
            draft_title="GTEx 组织草稿",
            draft_placeholder="暂无 GTEx 组织草稿",
            copy_source="gtex",
            search_text="在线检查 GTEx",
            search_callback=self.search_gtex_candidates,
            candidate_headers=["操作", "组织", "样本数", "表达类型", "状态"],
            selected_empty="尚未选择 GTEx 组织参考。",
            presentation="gtex_cards",
        )
        self._candidate_detail_title = self._source_detail_titles["geo"]
        self._candidate_detail_text = self._source_detail_texts["geo"]
        self._detail_select_button = self._source_detail_select_buttons["geo"]
        self._detail_download_button = self._source_detail_download_buttons["geo"]
        self._detail_brief_button = self._source_detail_brief_buttons["geo"]
        self._registered_table = self._source_registered_tables["geo"]
        self._tabs.addTab(self._geo_tab_page, "GEO/GSE")
        self._tabs.addTab(self._tcga_tab_page, "TCGA/GDC")
        self._tabs.addTab(self._gtex_tab_page, "GTEx")
        result_layout.addWidget(self._tabs)
        root.addWidget(result_card)

        log_card, log_layout = _card("高级信息")
        self._mapping_log = _text_preview(180)
        self._mapping_log.setObjectName("chineseMappingLog")
        self._mapping_log.setVisible(False)
        log_layout.addWidget(_button("查看映射日志", "secondaryButton", lambda: _toggle_details(self._mapping_log)), alignment=Qt.AlignLeft)
        log_layout.addWidget(self._mapping_log)
        root.addWidget(log_card)

        bottom_frame = QFrame()
        bottom_frame.setObjectName("chineseDatasetSearchBottomActionBar")
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        self._registered_count_label = _status_label("已选 GEO 0 个，TCGA 0 个，GTEx 0 个；0 个可进入识别。")
        self._continue_button = _button("下一步：进入数据识别", "primaryButton", self.continue_to_recognition)
        self._continue_button.setEnabled(False)
        bottom_layout.addWidget(self._registered_count_label)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(_button("返回数据来源页", "secondaryButton", self.back_requested.emit))
        bottom_layout.addWidget(self._continue_button)
        root.addWidget(bottom_frame)

    def _query_draft_box(self, text: str) -> QPlainTextEdit:
        box = _text_preview(72)
        box.setPlainText(text)
        box.setMinimumHeight(64)
        box.setMaximumHeight(92)
        return box

    def _build_database_tab(
        self,
        *,
        source_key: str,
        draft_title: str,
        draft_placeholder: str,
        copy_source: str,
        search_text: str,
        search_callback: Callable[[], object],
        candidate_headers: list[str],
        selected_empty: str,
        presentation: str = "table",
    ) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(SPACING["sm"], SPACING["md"], SPACING["sm"], SPACING["sm"])
        layout.setSpacing(SPACING["md"])

        summary = _status_label(f"{draft_title}：尚未生成")
        query_box = self._query_draft_box(draft_placeholder)
        query_box.setVisible(False)
        self._draft_detail_widgets.append(query_box)
        toggle_button = _button("查看完整检索词", "secondaryButton", lambda checked=False, box=query_box: self._toggle_single_draft_box(box))
        draft_frame = QFrame()
        draft_frame.setObjectName("databaseDraftPanel")
        draft_layout = QVBoxLayout(draft_frame)
        draft_layout.setContentsMargins(0, 0, 0, 0)
        draft_layout.addWidget(_muted(draft_title))
        draft_layout.addWidget(summary)
        draft_actions = QHBoxLayout()
        draft_actions.addWidget(toggle_button)
        draft_actions.addWidget(_button("复制", "secondaryButton", lambda checked=False, s=copy_source: self.copy_query(s)))
        draft_actions.addWidget(_button("确认草稿", "secondaryButton", lambda checked=False: self.confirm_query_draft()))
        draft_actions.addWidget(_button(search_text, "secondaryButton", lambda checked=False, callback=search_callback: callback()))
        draft_actions.addStretch(1)
        draft_layout.addLayout(draft_actions)
        draft_layout.addWidget(query_box)
        layout.addWidget(draft_frame)

        result_title = "GEO/GSE 数据集候选" if presentation == "table" else ("TCGA/GDC 推荐项目" if presentation == "tcga_cards" else "GTEx 推荐组织")
        layout.addWidget(_muted(result_title))
        empty = _muted("暂无候选结果。")
        table = _table(candidate_headers)
        table.setWordWrap(True)
        table.setMinimumHeight(220)
        layout.addWidget(empty)
        if presentation == "table":
            layout.addWidget(table)
        else:
            table.setVisible(False)
            table.setParent(page)
            cards_widget = QWidget()
            cards_widget.setObjectName(f"{source_key}RecommendationCards")
            cards_layout = QVBoxLayout(cards_widget)
            cards_layout.setContentsMargins(0, 0, 0, 0)
            cards_layout.setSpacing(SPACING["sm"])
            cards_widget.setVisible(False)
            layout.addWidget(cards_widget)
            self._source_recommendation_empty_labels[source_key] = empty
            self._source_recommendation_widgets[source_key] = cards_widget
            self._source_recommendation_layouts[source_key] = cards_layout

        detail_frame = QFrame()
        detail_frame.setObjectName(f"{source_key}CandidateDetailPanel")
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(0, SPACING["sm"], 0, 0)
        detail_title = _status_label("候选详情")
        detail_text = _text_preview(140)
        detail_text.setObjectName(f"{source_key}CandidateDetailText")
        detail_text.setPlainText("点击候选结果的“详情”查看标题、中文简介、匹配原因、资产状态和下载建议。")
        detail_layout.addWidget(detail_title)
        detail_layout.addWidget(detail_text)
        detail_actions = QHBoxLayout()
        select_button = _button("选择", "secondaryButton", self._select_current_candidate)
        download_button = _button("下载并添加" if source_key == "geo" else "创建下载任务", "secondaryButton", self._download_current_candidate)
        brief_button = _button("生成中文简介", "secondaryButton", self._brief_current_candidate)
        select_button.setEnabled(False)
        download_button.setEnabled(False)
        brief_button.setEnabled(False)
        brief_button.setVisible(source_key == "geo")
        detail_actions.addWidget(select_button)
        detail_actions.addWidget(download_button)
        detail_actions.addWidget(brief_button)
        detail_actions.addStretch(1)
        detail_layout.addLayout(detail_actions)
        layout.addWidget(detail_frame)
        if source_key == "geo":
            detail_frame.setVisible(False)
            self._geo_dataset_detail_panel = GeoDatasetDetailPanel()
            self._geo_dataset_detail_panel.save_requested.connect(self._save_geo_candidate_from_detail)
            self._geo_dataset_detail_panel.ignore_requested.connect(self._ignore_geo_candidate_from_detail)
            self._geo_dataset_detail_panel.remove_requested.connect(self._remove_geo_candidate_from_detail)
            self._geo_dataset_detail_panel.download_assets_requested.connect(lambda candidate: self.download_geo_supplementary_assets(candidate.accession_or_project))
            self._geo_dataset_detail_panel.translate_requested.connect(lambda candidate: self.generate_geo_chinese_brief(candidate.accession_or_project))
            self._geo_dataset_detail_panel.brief_requested.connect(lambda candidate: self.generate_geo_chinese_brief(candidate.accession_or_project))
            self._geo_dataset_detail_panel.confirm_comparison_requested.connect(self._confirm_geo_profile_comparison)
            self._geo_dataset_detail_panel.manual_comparison_requested.connect(self._manual_geo_profile_comparison)
            layout.addWidget(self._geo_dataset_detail_panel)
            self._geo_download_list_panel = GeoDownloadListPanel(title="已选 GEO 数据集", geo_only=True)
            self._geo_download_list_panel.view_requested.connect(self._show_geo_detail_by_accession)
            self._geo_download_list_panel.download_selected_requested.connect(self._download_selected_geo_entries)
            self._geo_download_list_panel.delete_selected_requested.connect(self._delete_selected_geo_entries)
            self._geo_download_list_panel.continue_requested.connect(self.continue_to_recognition)
            layout.addWidget(self._geo_download_list_panel)

        layout.addWidget(_muted("已选本库数据源"))
        registered_empty = _muted(selected_empty)
        registered_table = _table(["数据源", "当前状态", "已有资产", "缺失资产", "下一步", "操作"])
        registered_table.setObjectName(f"{source_key}RegisteredSourceTable")
        layout.addWidget(registered_empty)
        layout.addWidget(registered_table)

        self._source_detail_titles[source_key] = detail_title
        self._source_detail_texts[source_key] = detail_text
        self._source_detail_select_buttons[source_key] = select_button
        self._source_detail_download_buttons[source_key] = download_button
        self._source_detail_brief_buttons[source_key] = brief_button
        self._source_registered_empty_labels[source_key] = registered_empty
        self._source_registered_tables[source_key] = registered_table
        if source_key == "geo":
            self._geo_draft_summary = summary
            self._geo_query_box = query_box
            self._geo_empty_label = empty
            self._geo_table = table
            self._geo_registered_empty_label = registered_empty
            self._geo_registered_table = registered_table
        elif source_key == "tcga_gdc":
            self._tcga_draft_summary = summary
            self._tcga_query_box = query_box
            self._tcga_empty_label = empty
            self._tcga_table = table
            self._tcga_registered_empty_label = registered_empty
            self._tcga_registered_table = registered_table
        elif source_key == "gtex":
            self._gtex_draft_summary = summary
            self._gtex_query_box = query_box
            self._gtex_empty_label = empty
            self._gtex_table = table
            self._gtex_registered_empty_label = registered_empty
            self._gtex_registered_table = registered_table
        return page

    def _toggle_single_draft_box(self, box: QPlainTextEdit) -> None:
        box.setVisible(not box.isVisible())

    def _toggle_full_drafts(self) -> None:
        visible = not self._geo_query_box.isVisible()
        self._set_full_drafts_visible(visible)

    def _set_full_drafts_visible(self, visible: bool) -> None:
        for widget in self._draft_detail_widgets:
            widget.setVisible(visible)

    def _add_draft_section(
        self,
        layout: QVBoxLayout,
        *,
        title: str,
        box: QPlainTextEdit,
        copy_text: str,
        search_text: str,
        copy_source: str,
        search_callback: Callable[[], object],
    ) -> None:
        layout.addWidget(_muted(title))
        layout.addWidget(box)
        row = QHBoxLayout()
        row.addWidget(_button(copy_text, "secondaryButton", lambda checked=False, s=copy_source: self.copy_query(s)))
        row.addWidget(_button(search_text, "secondaryButton", lambda checked=False, callback=search_callback: callback()))
        row.addStretch(1)
        layout.addLayout(row)

    def _candidate_tab(self, headers: list[str]) -> tuple[QWidget, QLabel, QTableWidget]:
        page = QWidget()
        layout = QVBoxLayout(page)
        empty = _muted("暂无候选结果。")
        table = _table(headers)
        table.setWordWrap(True)
        table.setMinimumHeight(220)
        layout.addWidget(empty)
        layout.addWidget(table)
        return page, empty, table

    def _render_result(self, result: BioinformaticsSearchCenterResult, *, searched: bool) -> None:
        self._last_render_searched = searched
        query = result.query
        geo_queries = tuple(query.geo_query_candidates)
        self._geo_query_box.setPlainText("\n".join(geo_queries) if geo_queries else "暂无 GEO/GSE 检索草稿")
        self._tcga_query_box.setPlainText(", ".join(query.tcga_project_ids) if query.tcga_project_ids else "暂无 TCGA/GDC 项目草稿")
        self._gtex_query_box.setPlainText(", ".join(query.gtex_tissues) if query.gtex_tissues else "暂无 GTEx 组织草稿")
        self._topic_summary_label.setText(_topic_summary_text(query))
        self._geo_draft_summary.setText(_geo_draft_summary_text(query))
        self._tcga_draft_summary.setText(f"TCGA：{', '.join(query.tcga_project_ids) if query.tcga_project_ids else '未生成项目草稿'}")
        self._gtex_draft_summary.setText(f"GTEx：{', '.join(query.gtex_tissues) if query.gtex_tissues else '未生成组织草稿'}")
        self._candidates = {(candidate.source, candidate.accession_or_project): candidate for candidate in result.candidates}
        self._candidate_register_buttons.clear()
        self._candidate_download_buttons.clear()
        self._candidate_status_labels.clear()
        self._render_candidate_tables(result, searched=searched)
        self._refresh_candidate_registration_buttons()
        self._mapping_log.setPlainText(_mapping_log_text(result))

    def _render_candidate_tables(self, result: BioinformaticsSearchCenterResult, *, searched: bool) -> None:
        grouped: dict[str, list[UnifiedDatasetCandidate]] = {"geo": [], "tcga_gdc": [], "gtex": []}
        for candidate in result.candidates:
            if candidate.source in grouped:
                grouped[candidate.source].append(candidate)
        self._fill_geo_candidates(grouped["geo"], result.source_results.get("geo"), searched=searched)
        self._fill_tcga_candidates(grouped["tcga_gdc"])
        self._fill_gtex_candidates(grouped["gtex"])

    def _fill_geo_candidates(self, candidates: list[UnifiedDatasetCandidate], source_result: object | None = None, *, searched: bool = False) -> None:
        self._geo_empty_label.setVisible(not candidates)
        self._geo_table.setVisible(bool(candidates))
        if not candidates:
            self._geo_empty_label.setText(_geo_empty_state_text(source_result, searched=searched))
        _fill_table(
            self._geo_table,
            [
                [
                    "",
                    item.accession_or_project,
                    item.display_title,
                    item.sample_count,
                    _candidate_modality_label(item),
                    _geo_candidate_potential_text(self._project_root, item),
                    self._candidate_registration_status(item),
                ]
                for item in candidates
            ],
        )
        self._install_candidate_action_buttons(self._geo_table, candidates)
        _set_table_widths(self._geo_table, [140, 92, 300, 70, 160, 72, 150])

    def _fill_tcga_candidates(self, candidates: list[UnifiedDatasetCandidate]) -> None:
        self._tcga_empty_label.setVisible(not candidates)
        self._tcga_table.setVisible(False)
        self._tcga_empty_label.setText("未生成 TCGA/GDC 项目候选。")
        self._render_recommendation_cards("tcga_gdc", candidates)

    def _fill_gtex_candidates(self, candidates: list[UnifiedDatasetCandidate]) -> None:
        self._gtex_empty_label.setVisible(not candidates)
        self._gtex_table.setVisible(False)
        self._gtex_empty_label.setText("未生成 GTEx 组织候选。")
        self._render_recommendation_cards("gtex", candidates)

    def _render_recommendation_cards(self, source_key: str, candidates: list[UnifiedDatasetCandidate]) -> None:
        cards_widget = self._source_recommendation_widgets[source_key]
        cards_layout = self._source_recommendation_layouts[source_key]
        _clear_layout(cards_layout)
        for key in [key for key in self._candidate_register_buttons if key[0] == source_key]:
            self._candidate_register_buttons.pop(key, None)
        for key in [key for key in self._candidate_download_buttons if key[0] == source_key]:
            self._candidate_download_buttons.pop(key, None)
        for key in [key for key in self._candidate_status_labels if key[0] == source_key]:
            self._candidate_status_labels.pop(key, None)
        cards_widget.setVisible(bool(candidates))
        for candidate in candidates:
            cards_layout.addWidget(self._recommendation_card(candidate))
        cards_layout.addStretch(1)
        self._refresh_candidate_registration_buttons()

    def _recommendation_card(self, candidate: UnifiedDatasetCandidate) -> QFrame:
        frame = QFrame()
        frame.setObjectName("bioProjectSummaryCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
        layout.setSpacing(SPACING["xs"])

        title = QLabel(_recommendation_card_title(candidate))
        title.setObjectName("bioProjectCardTitle")
        title.setWordWrap(True)
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(SPACING["md"])
        grid.setVerticalSpacing(SPACING["xs"])
        fields = _recommendation_card_fields(candidate)
        for row_index, (label_text, value_text) in enumerate(fields):
            label = _muted(f"{label_text}：")
            value = QLabel(value_text)
            value.setWordWrap(True)
            grid.addWidget(label, row_index, 0, alignment=Qt.AlignTop)
            grid.addWidget(value, row_index, 1)
        status_row = len(fields)
        status_label = _status_label(self._candidate_recommendation_status(candidate))
        status_label.setObjectName(f"candidateStatusLabel_{candidate.source}_{candidate.accession_or_project}")
        grid.addWidget(_muted("状态："), status_row, 0, alignment=Qt.AlignTop)
        grid.addWidget(status_label, status_row, 1)
        layout.addLayout(grid)

        actions = QHBoxLayout()
        register_text = "选择项目" if candidate.source == "tcga_gdc" else "选择组织"
        register_button = QPushButton(register_text)
        register_button.setObjectName(f"registerCandidateButton_{candidate.source}_{candidate.accession_or_project}")
        register_button.clicked.connect(lambda checked=False, s=candidate.source, a=candidate.accession_or_project: self.register_candidate(s, a))
        detail_button = QPushButton("查看说明")
        detail_button.setObjectName(f"candidateDetailButton_{candidate.source}_{candidate.accession_or_project}")
        detail_button.clicked.connect(lambda checked=False, item=candidate: self._show_candidate_detail(item))
        download_button = QPushButton("创建下载清单")
        download_button.setObjectName(f"candidateDownloadButton_{candidate.source}_{candidate.accession_or_project}")
        download_button.clicked.connect(lambda checked=False, s=candidate.source, a=candidate.accession_or_project: self.generate_candidate_download_task(s, a))
        actions.addWidget(register_button)
        actions.addWidget(detail_button)
        actions.addWidget(download_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        key = (candidate.source, candidate.accession_or_project)
        self._candidate_register_buttons[key] = register_button
        self._candidate_download_buttons[key] = download_button
        self._candidate_status_labels[key] = status_label
        return frame

    def _refresh_registered_sources(self) -> None:
        rows = self._registered_chinese_rows()
        grouped_rows: dict[str, list[RegisteredSourceRow]] = {"geo": [], "tcga_gdc": [], "gtex": []}
        for row in rows:
            grouped_rows[_registered_source_bucket(row)].append(row)
        for source_key, source_rows in grouped_rows.items():
            empty_label = self._source_registered_empty_labels[source_key]
            table = self._source_registered_tables[source_key]
            empty_label.setVisible(not source_rows)
            display_rows: list[list[object]] = []
            for row in source_rows:
                status = _current_registered_row_status(self._project_root, row)
                display_rows.append(
                    [
                        row.source_label,
                        status,
                        _registered_existing_assets(row, status),
                        _registered_missing_assets(row, status),
                        _registered_next_step(row, status),
                        "",
                    ]
                )
            _fill_table(table, display_rows)
            for row_index, row in enumerate(source_rows):
                table.setCellWidget(row_index, 5, _registered_source_action_widget(row))
        total_count = len(rows)
        ready_count = _ready_chinese_source_count(self._project_root)
        source_counts = {key: len(value) for key, value in grouped_rows.items()}
        prefix = f"已选 GEO {source_counts['geo']} 个，TCGA {source_counts['tcga_gdc']} 个，GTEx {source_counts['gtex']} 个；{ready_count} 个可进入识别。"
        if ready_count:
            self._registered_count_label.setText(f"{prefix} 当前建议操作：进入数据识别。")
        elif total_count:
            self._registered_count_label.setText(f"{prefix} 当前建议操作：先补全表达矩阵。")
        else:
            self._registered_count_label.setText(f"{prefix} 当前建议操作：先选择数据源。")
        can_continue = ready_count > 0 and self._project_root is not None
        self._continue_button.setEnabled(can_continue)
        self._continue_button.setText("下一步：进入数据识别")
        self._refresh_geo_download_list()

    def _refresh_geo_download_list(self) -> None:
        panel = getattr(self, "_geo_download_list_panel", None)
        if panel is not None:
            panel.refresh(self._project_root)

    def _download_selected_geo_entries(self, keys: tuple[str, ...]) -> None:
        for key in keys:
            accession = key.split(":", 1)[1] if key.startswith("geo:") else key
            if _candidate_has_pending_geo_assets(self._project_root, accession):
                self.download_geo_supplementary_assets(accession)
            else:
                self.download_geo_candidate(accession)
        self._refresh_geo_download_list()

    def _delete_selected_geo_entries(self, keys: tuple[str, ...]) -> None:
        removed = 0
        for key in keys:
            accession = key.split(":", 1)[1] if key.startswith("geo:") else key
            if _remove_geo_download_entry(self._project_root, accession):
                removed += 1
        self._refresh_registered_sources()
        self._set_status(f"已移除 {removed} 个 GEO 数据集；未删除原始文件。")

    def _install_candidate_action_buttons(self, table: QTableWidget, candidates: list[UnifiedDatasetCandidate]) -> None:
        action_col = _table_column_index(table, "操作")
        table.setColumnWidth(action_col, 140)
        for row_index, candidate in enumerate(candidates):
            key = (candidate.source, candidate.accession_or_project)
            action_widget = QWidget()
            layout = QHBoxLayout(action_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            detail_button = QPushButton("查看详情")
            detail_button.setObjectName(f"candidateDetailButton_{candidate.source}_{candidate.accession_or_project}")
            detail_button.clicked.connect(lambda checked=False, item=candidate: self._show_candidate_detail(item))
            if candidate.source != "geo":
                register_button = QPushButton("选择")
                register_button.setObjectName(f"registerCandidateButton_{candidate.source}_{candidate.accession_or_project}")
                register_button.clicked.connect(lambda checked=False, s=candidate.source, a=candidate.accession_or_project: self.register_candidate(s, a))
                layout.addWidget(register_button)
                self._candidate_register_buttons[key] = register_button
            layout.addWidget(detail_button)
            layout.addStretch(1)
            table.setCellWidget(row_index, action_col, action_widget)
        self._refresh_candidate_registration_buttons()

    def _show_candidate_detail(self, candidate: UnifiedDatasetCandidate) -> None:
        if candidate.source == "geo":
            self._show_geo_candidate_detail(candidate)
            return
        self._selected_candidate = candidate
        source_key = _candidate_source_bucket(candidate.source)
        self._candidate_detail_title = self._source_detail_titles[source_key]
        self._candidate_detail_text = self._source_detail_texts[source_key]
        self._detail_select_button = self._source_detail_select_buttons[source_key]
        self._detail_download_button = self._source_detail_download_buttons[source_key]
        self._detail_brief_button = self._source_detail_brief_buttons[source_key]
        self._candidate_detail_title.setText(f"候选详情：{candidate.accession_or_project}")
        self._candidate_detail_text.setPlainText(_candidate_detail_text(candidate, self._project_root, self._geo_brief_cache.get(candidate.accession_or_project)))
        self._detail_select_button.setEnabled(not self._is_candidate_registered(candidate.source, candidate.accession_or_project))
        self._detail_download_button.setEnabled(True)
        self._detail_download_button.setVisible(candidate.source == "geo" or candidate.source in {"tcga_gdc", "gtex"})
        self._detail_download_button.setText("下载并添加" if candidate.source == "geo" else "创建下载任务")
        self._detail_brief_button.setVisible(candidate.source == "geo")
        self._detail_brief_button.setEnabled(candidate.source == "geo")
        self._set_status(f"正在查看：{candidate.accession_or_project}")

    def _show_geo_candidate_detail(self, candidate: UnifiedDatasetCandidate) -> None:
        self._selected_candidate = candidate
        self._geo_dataset_detail_panel.show_candidate(
            candidate,
            project_root=self._project_root,
            summary_payload=self._geo_brief_cache.get(candidate.accession_or_project),
            saved=_is_geo_saved_to_download_list(self._project_root, candidate.accession_or_project),
        )
        self._tabs.setCurrentWidget(self._geo_tab_page)
        self._set_status(f"正在查看：{candidate.accession_or_project}")

    def _show_geo_detail_by_accession(self, accession: str) -> None:
        accession = accession.split(":", 1)[1] if accession.startswith("geo:") else accession
        candidate = self._candidates.get(("geo", accession)) or _geo_candidate_from_download_entry(self._project_root, accession)
        if candidate is None:
            self._set_status(f"未找到 GEO 数据集详情：{accession}", error=True)
            return
        self._show_geo_candidate_detail(candidate)

    def _save_geo_candidate_from_detail(self, candidate: UnifiedDatasetCandidate) -> None:
        summary = self.register_candidate(candidate.source, candidate.accession_or_project)
        if summary is not None:
            self._geo_dataset_detail_panel.set_saved(True)
            self._refresh_geo_download_list()

    def _ignore_geo_candidate_from_detail(self, candidate: UnifiedDatasetCandidate) -> None:
        self._geo_dataset_detail_panel.setVisible(False)
        self._set_status(f"已忽略：{candidate.accession_or_project}")

    def _remove_geo_candidate_from_detail(self, candidate: UnifiedDatasetCandidate) -> None:
        self._remove_geo_accession_from_download_list(candidate.accession_or_project)

    def _remove_geo_accession_from_download_list(self, accession: str) -> None:
        if _remove_geo_download_entry(self._project_root, accession):
            self._refresh_registered_sources()
            self._refresh_geo_download_list()
            candidate = self._candidates.get(("geo", accession))
            if candidate is not None:
                self._show_geo_candidate_detail(candidate)
            self._set_status(f"已从待处理数据集中移除：{accession}")
        else:
            self._set_status(f"待处理数据集中未找到：{accession}", error=True)

    def _select_current_candidate(self) -> None:
        if self._selected_candidate is None:
            return
        self.register_candidate(self._selected_candidate.source, self._selected_candidate.accession_or_project)
        self._show_candidate_detail(self._selected_candidate)

    def _download_current_candidate(self) -> None:
        if self._selected_candidate is None:
            return
        candidate = self._selected_candidate
        if candidate.source == "geo":
            self.download_geo_candidate(candidate.accession_or_project)
        else:
            self.generate_candidate_download_task(candidate.source, candidate.accession_or_project)
        self._show_candidate_detail(candidate)

    def _brief_current_candidate(self) -> None:
        if self._selected_candidate is None or self._selected_candidate.source != "geo":
            return
        self.generate_geo_chinese_brief(self._selected_candidate.accession_or_project)
        self._show_candidate_detail(self._selected_candidate)

    def _refresh_candidate_registration_buttons(self) -> None:
        for (source, accession), button in self._candidate_register_buttons.items():
            registered = self._is_candidate_registered(source, accession)
            if registered:
                button.setText("已选择")
            elif source == "tcga_gdc":
                button.setText("选择项目")
            elif source == "gtex":
                button.setText("选择组织")
            else:
                button.setText("选择")
            button.setEnabled(not registered)
        for (source, accession), button in self._candidate_download_buttons.items():
            ready = self._is_candidate_ready_for_recognition(source, accession)
            planned = self._is_candidate_registered(source, accession)
            if source == "geo":
                pending_assets = ready and _candidate_has_pending_geo_assets(self._project_root, accession)
                if pending_assets:
                    button.setText("下载补充文件")
                    button.setEnabled(True)
                else:
                    status_text = _candidate_record_status_text(self._project_root, source, accession)
                    button.setText("补充文件已下载" if "补充文件已下载" in status_text else ("元数据已下载" if ready else "下载并添加"))
                    button.setEnabled(not ready)
            else:
                manifest_created = _candidate_has_download_manifest(self._project_root, source, accession)
                if manifest_created:
                    button.setText("下载清单已创建")
                    button.setEnabled(False)
                else:
                    button.setText("创建下载清单")
                    button.setEnabled(True)

    def _refresh_candidate_status_cells(self) -> None:
        for key, label in self._candidate_status_labels.items():
            candidate = self._candidates.get(key)
            if candidate is not None:
                label.setText(self._candidate_recommendation_status(candidate))
        for source, table in (("geo", self._geo_table), ("tcga_gdc", self._tcga_table), ("gtex", self._gtex_table)):
            status_col = _table_column_index(table, "状态")
            id_col = 1
            for row_index in range(table.rowCount()):
                item = table.item(row_index, id_col)
                if item is None:
                    continue
                if source == "gtex":
                    candidate = next((value for (candidate_source, _key), value in self._candidates.items() if candidate_source == "gtex" and (value.tissue == item.text() or value.accession_or_project == item.text())), None)
                else:
                    candidate = self._candidates.get((source, item.text()))
                if candidate is None:
                    continue
                table.setItem(row_index, status_col, QTableWidgetItem(self._candidate_registration_status(candidate)))

    def _is_candidate_registered(self, source: str, accession_or_project: str) -> bool:
        return (source, accession_or_project) in self._registered_candidate_keys()

    def _registered_candidate_keys(self) -> set[tuple[str, str]]:
        keys: set[tuple[str, str]] = set()
        if self._project_root is None:
            return keys
        records_dir = self._project_root / "acquisition" / "records"
        if not records_dir.exists():
            return keys
        for path in records_dir.glob("*.json"):
            if path.name == LATEST_RECORD:
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            metadata = payload.get("metadata")
            if not isinstance(metadata, dict) or metadata.get("ui_source") != "chinese_research_question_search":
                continue
            keys.add((str(metadata.get("source") or ""), str(metadata.get("accession_or_project") or payload.get("source_label") or "")))
        return keys

    def _is_candidate_ready_for_recognition(self, source: str, accession_or_project: str) -> bool:
        return self._candidate_registration_state(source, accession_or_project) == "ready"

    def _candidate_registration_state(self, source: str, accession_or_project: str) -> str:
        state = ""
        if self._project_root is None:
            return state
        records_dir = self._project_root / "acquisition" / "records"
        if not records_dir.exists():
            return state
        for path in sorted(records_dir.glob("*.json")):
            if path.name == LATEST_RECORD:
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            metadata = payload.get("metadata")
            if not isinstance(metadata, dict) or metadata.get("ui_source") != "chinese_research_question_search":
                continue
            key = (str(metadata.get("source") or ""), str(metadata.get("accession_or_project") or payload.get("source_label") or ""))
            if key != (source, accession_or_project):
                continue
            if metadata.get("ready_for_recognition") == "ready" or payload.get("strategy") != "plan_only":
                state = "ready"
            elif not state:
                state = "planned"
        return state

    def _registered_chinese_rows(self) -> list[RegisteredSourceRow]:
        grouped: dict[tuple[str, str], RegisteredSourceRow] = {}
        for row in _registered_source_rows(self._project_root):
            if not _is_chinese_topic_source_type(row.source_type_key):
                continue
            key = (row.source_type_key, row.source_label)
            previous = grouped.get(key)
            if previous is None or _registered_row_rank(row) >= _registered_row_rank(previous):
                grouped[key] = row
        return sorted(grouped.values(), key=lambda row: row.created_at)

    def _registered_source_count(self) -> int:
        return _ready_chinese_source_count(self._project_root)

    def _candidate_registration_status(self, candidate: UnifiedDatasetCandidate) -> str:
        state = self._candidate_registration_state(candidate.source, candidate.accession_or_project)
        if state == "ready":
            return _candidate_record_status_text(self._project_root, candidate.source, candidate.accession_or_project) or "可进入识别"
        if state == "planned":
            return "待下载"
        return "未选择"

    def _candidate_recommendation_status(self, candidate: UnifiedDatasetCandidate) -> str:
        if candidate.source not in {"tcga_gdc", "gtex"}:
            return self._candidate_registration_status(candidate)
        state = self._candidate_registration_state(candidate.source, candidate.accession_or_project)
        if state == "ready":
            return _candidate_record_status_text(self._project_root, candidate.source, candidate.accession_or_project) or "已生成下载任务"
        if state == "planned":
            return "已选择，待创建下载任务"
        return "待创建下载任务"

    def _ensure_draft_result(self) -> BioinformaticsSearchCenterResult | None:
        if self._last_result is not None:
            return self._last_result
        return self.generate_terms()

    def _set_status(self, text: str, *, error: bool = False) -> None:
        self._status_label.setText(text)
        self._status_label.setProperty("status", "error" if error else "ok")
        _refresh_style(self._status_label)


class BioinformaticsAcquisitionStatusWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()

    def __init__(self, *, on_continue: Callable[[Path], None] | None = None, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self.setObjectName("bioinformaticsAcquisitionStatusPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_status()

    def status_message(self) -> str:
        return self._status_label.text()

    def refresh_status(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            self._summary.setPlainText("")
            self._details.setPlainText("")
            return
        artifacts = read_acquisition_artifacts(self._project_root)
        summary = load_latest_acquisition_summary(self._project_root)
        if summary is None:
            self._status_label.setText("尚未生成数据获取记录。")
        else:
            warning = " plan_only 需要补充文件或后续执行下载。" if summary.strategy == "plan_only" else ""
            self._status_label.setText(f"当前数据来源：{summary.source_type} · {summary.source_label} · {summary.strategy}。{warning}")
        payload = {
            "数据来源摘要": _summary_to_dict(summary),
            "acquisition_plan": artifacts.get("plan") or "不存在",
            "standardization_handoff": artifacts.get("handoff") or "不存在",
            "acquisition_record": artifacts.get("record") or "不存在",
            "原始数据位置": {
                "raw_data/local_import": str(self._project_root / "raw_data/local_import"),
                "raw_data/geo": str(self._project_root / "raw_data/geo"),
                "raw_data/tcga": str(self._project_root / "raw_data/tcga"),
                "raw_data/gtex": str(self._project_root / "raw_data/gtex"),
            },
        }
        self._summary.setPlainText(_acquisition_user_summary(summary, artifacts, self._project_root))
        self._details.setPlainText(_json(payload))

    def continue_to_recognition(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        ok, reason = _can_continue_from_acquisition(self._project_root)
        if not ok:
            self._status_label.setText(f"不能继续：{reason} 请返回数据来源补充文件。")
            return
        self.continue_requested.emit(self._project_root)

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("生信数据获取状态", "Developer Preview / 本地测试版", back_text="返回数据来源选择", back_signal=self.back_requested))
        self._status_label = _status_label("尚未生成数据获取记录。")
        root.addWidget(self._status_label)
        self._summary = _text_preview(180)
        root.addWidget(self._summary)
        self._details = _text_preview(180)
        self._details.setVisible(False)
        root.addWidget(_button("展开技术详情", "secondaryButton", lambda: _toggle_details(self._details)))
        root.addWidget(self._details)
        actions = QHBoxLayout()
        actions.addWidget(_button("刷新状态", "secondaryButton", self.refresh_status))
        actions.addWidget(_button("打开项目文件夹", "secondaryButton", lambda: _open_path(self._project_root)))
        actions.addWidget(_button("打开 raw_data 文件夹", "secondaryButton", lambda: _open_path(self._project_root / "raw_data" if self._project_root else None)))
        actions.addWidget(_button("继续：数据识别", "primaryButton", self.continue_to_recognition))
        actions.addStretch(1)
        root.addLayout(actions)


class BioinformaticsRecognitionWidget(QWidget):
    continue_requested = Signal(object)
    navigate_requested = Signal(str, object)
    back_requested = Signal()

    def __init__(self, *, on_continue: Callable[[Path], None] | None = None, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self._last_report: dict[str, object] | None = None
        self._selected_detail_run: dict[str, object] | None = None
        self._selected_detail_file: dict[str, object] | None = None
        self._selected_detail_payload: dict[str, object] | None = None
        self._active_next_run: dict[str, object] | None = None
        self._active_next_files: list[dict[str, object]] = []
        self._active_next_steps: dict[str, object] | None = None
        self._next_step_actions: list[dict[str, object]] = []
        self._pre_recognition_rows: list[RegisteredSourceRow] = []
        self._pre_recognition_checks: dict[str, QCheckBox] = {}
        self._history_expanded = False
        self.setObjectName("bioinformaticsRecognitionPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self._last_report = None
        self.refresh_report()

    def run_recognition(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。")
            return None
        selected_rows = self._selected_pre_recognition_rows()
        if not selected_rows:
            self._set_status("请先选择需要识别的数据源。")
            return None
        selected_paths = _recognition_paths_for_rows(self._project_root, selected_rows)
        if not selected_paths:
            self._set_status("所选数据没有可识别文件，请返回数据导入与检索页补充数据。")
            return None
        self._set_status("正在识别数据文件，请稍候。大文件可能需要几十秒。")
        QApplication.processEvents()
        report = run_project_recognition_for_paths(
            self._project_root,
            selected_paths,
            skipped_unselected_count=max(0, len(self._pre_recognition_rows) - len(selected_rows)),
        )
        self._render_report(report)
        self._render_recognition_history()
        self._set_status(f"{self.status_message()} 本次只识别已勾选的数据。")
        return report

    def refresh_report(self) -> None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。")
            return
        self._render_pre_recognition_inputs()
        self._clear_current_recognition_display()
        self._render_recognition_history()
        self._set_status("尚未开始本次识别。请选择上方数据源后点击“开始识别”。")

    def clean_old_recognition_results(self, *, skip_confirmation: bool = False) -> bool:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。")
            return False
        if not skip_confirmation:
            answer = QMessageBox.question(
                self,
                "清理旧识别结果",
                "此操作只清理旧识别结果，不会删除原始数据文件。是否继续？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                self._set_status("已取消清理旧识别结果。")
                return False
        for target in (self._project_root / "logs" / "recognition", self._project_root / "recognized_data"):
            if target.exists():
                shutil.rmtree(target)
        self._last_report = None
        self._table.setRowCount(0)
        self._counts.setPlainText("旧识别结果已清理。raw_data 中的原始导入文件未删除。")
        self._asset_summary.setPlainText("")
        self._technical_details.setPlainText("")
        self._clear_recognition_detail()
        self._render_recognition_history()
        self._set_status("旧识别结果已清理；原始数据文件未删除。请点击“重新识别”重新扫描。")
        return True

    def status_message(self) -> str:
        return self._status_label.text()

    def export_recognition_detail_report(self) -> Path | None:
        if self._project_root is None or self._selected_detail_run is None:
            self._set_status("请先查看一个识别详情，再导出报告。")
            return None
        path = export_recognition_report_markdown(self._project_root, self._selected_detail_run, self._selected_detail_file)
        self._set_status("数据识别报告已导出，可在该识别批次详情中查看。")
        return path

    def continue_to_readiness(self) -> None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。")
            return
        ok, reason = _can_continue_from_recognition(self._project_root)
        if not ok:
            self._set_status(f"不能继续：{reason} 请返回数据来源补充文件。")
            return
        self.continue_requested.emit(self._project_root)

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        header = _header("数据识别", "Developer Preview / 本地测试版", back_text="返回数据导入与检索", back_signal=self.back_requested)
        _apply_button_semantics_by_text(header, "返回数据导入与检索", "back")
        root.addWidget(header)
        pre_card, pre_layout = _card("待识别数据源")
        self._pre_recognition_empty_label = _muted("尚未选择数据。")
        pre_layout.addWidget(self._pre_recognition_empty_label)
        self._pre_recognition_table = _table(["选择", "来源类型", "名称 / 编号", "简化位置", "数据状态"])
        self._pre_recognition_table.setObjectName("preRecognitionInputList")
        self._pre_recognition_table.setMinimumHeight(88)
        self._pre_recognition_table.setMaximumHeight(150)
        self._pre_recognition_table.horizontalHeader().sectionClicked.connect(self._toggle_pre_recognition_header)
        pre_layout.addWidget(self._pre_recognition_table)
        pre_actions = QHBoxLayout()
        self._delete_selected_inputs_button = _button("删除所选", "secondaryButton", self._delete_selected_pre_recognition_sources, role="danger")
        self._delete_selected_inputs_button.setEnabled(False)
        pre_actions.addStretch(1)
        pre_actions.addWidget(self._delete_selected_inputs_button)
        pre_layout.addLayout(pre_actions)
        root.addWidget(pre_card)
        actions = QHBoxLayout()
        actions.addWidget(_button("开始识别", "primaryButton", self.run_recognition, role="primary_action"))
        actions.addWidget(_button("刷新", "secondaryButton", self.refresh_report, role="secondary"))
        actions.addStretch(1)
        root.addLayout(actions)
        root.addWidget(_muted("开始识别只处理上方勾选的数据；刷新只更新当前报告显示。"))
        self._status_label = _status_label("尚未开始本次识别。请选择上方数据源后点击“开始识别”。")
        root.addWidget(self._status_label)
        result_card, result_layout = _card("本次识别结果")
        self._current_result_hint = _muted("尚未开始本次识别。请选择上方数据源后点击“开始识别”。")
        result_layout.addWidget(self._current_result_hint)
        filter_row = QHBoxLayout()
        filter_row.addWidget(_muted("文件显示："))
        self._duplicate_filter = QComboBox()
        self._duplicate_filter.addItems(["显示全部文件", "仅显示当前有效数据来源", "隐藏疑似重复文件"])
        self._duplicate_filter.currentIndexChanged.connect(self._rerender_last_report)
        filter_row.addWidget(self._duplicate_filter)
        filter_row.addStretch(1)
        result_layout.addLayout(filter_row)
        result_layout.addWidget(_muted("本次识别结果摘要"))
        self._counts = _read_only_report_view(58)
        self._counts.setObjectName("recognitionSummaryReport")
        self._counts.setMinimumHeight(48)
        self._counts.setMaximumHeight(58)
        result_layout.addWidget(self._counts)
        next_card, next_layout = _card("下一步操作")
        next_actions = QHBoxLayout()
        self._next_action_buttons: list[QPushButton] = []
        for index in range(2):
            button = _button("", f"recognitionNextActionButton_{index}", lambda _checked=False, i=index: self._execute_next_step_action(i))
            _apply_button_semantics(button, "primary_next" if index == 0 else "secondary")
            button.setVisible(False)
            self._next_action_buttons.append(button)
            next_actions.addWidget(button)
        next_actions.addStretch(1)
        next_layout.addLayout(next_actions)
        self._next_steps_summary = _read_only_report_view(44)
        self._next_steps_summary.setObjectName("recognitionNextStepSummary")
        self._next_steps_summary.setMinimumHeight(40)
        self._next_steps_summary.setMaximumHeight(48)
        self._next_steps_summary.setPlainText("完成本次识别后，可继续进入数据准备与标准化。")
        next_layout.addWidget(self._next_steps_summary)
        result_layout.addWidget(next_card)
        self._table = _table(["文件名", "文件位置", "识别类型", "识别可信度", "文件大小", "识别理由", "提醒", "操作"])
        self._table.setObjectName("recognitionResultTable")
        self._table.setMinimumHeight(110)
        self._table.setMaximumHeight(170)
        confidence_header = self._table.horizontalHeaderItem(3)
        if confidence_header is not None:
            confidence_header.setToolTip("软件根据文件内容推断文件类型的可信程度。它不是数据质量评分，也不是科研可信度评分。")
        result_layout.addWidget(self._table)
        self._asset_summary = _read_only_report_view(150)
        self._asset_summary.setObjectName("recognitionAssetSummary")
        result_layout.addWidget(self._asset_summary)
        group_card, group_layout = _card("样本与分组预览")
        group_card.setObjectName("recognitionGroupPreviewCard")
        self._group_preview = _read_only_report_view(130)
        self._group_preview.setObjectName("recognitionGroupPreviewReport")
        group_layout.addWidget(self._group_preview)
        result_layout.addWidget(group_card)
        root.addWidget(result_card)

        history_card, history_layout = _card("历史识别记录")
        history_layout.addWidget(_muted("这里保存之前运行过的识别结果，不属于本次操作。"))
        history_summary_row = QHBoxLayout()
        self._history_summary_label = _muted("暂无历史识别记录。")
        self._history_toggle_button = _button("展开历史记录", "secondaryButton", self._toggle_history_table, role="secondary")
        self._history_summary_label.setObjectName("recognitionHistorySummary")
        self._history_toggle_button.setObjectName("recognitionHistoryToggleButton")
        self._history_toggle_button.setEnabled(False)
        history_summary_row.addWidget(self._history_summary_label)
        history_summary_row.addStretch(1)
        history_summary_row.addWidget(self._history_toggle_button)
        history_layout.addLayout(history_summary_row)
        self._history_table = _table(["时间", "批次名称", "输入数据源", "识别文件数", "内容摘要", "提醒数量", "当前状态", "操作"])
        self._history_table.setObjectName("recognitionHistoryTable")
        self._history_table.setMinimumHeight(120)
        self._history_table.setVisible(False)
        history_layout.addWidget(self._history_table)
        root.addWidget(history_card)

        detail_card, detail_layout = _card("识别详情")
        detail_layout.addWidget(_muted("只读查看本次识别文件或历史识别记录，不会修改当前识别批次。"))
        self._detail_report = _read_only_report_view(260)
        self._detail_report.setObjectName("recognitionDetailReport")
        self._detail_report.setPlainText("请选择本次识别文件或历史识别记录查看详情。")
        detail_layout.addWidget(self._detail_report)
        detail_actions = QHBoxLayout()
        self._detail_export_button = _button("导出数据识别报告", "recognitionDetailExportButton", self.export_recognition_detail_report, role="secondary")
        self._detail_export_button.setEnabled(False)
        detail_actions.addWidget(self._detail_export_button)
        detail_actions.addStretch(1)
        detail_layout.addLayout(detail_actions)
        self._detail_technical = _text_preview(180)
        self._detail_technical.setObjectName("recognitionDetailTechnical")
        self._detail_technical.setVisible(False)
        root.addWidget(detail_card)

        self._technical_details = _text_preview(180)
        self._technical_details.setVisible(False)

    def _render_report(self, report: dict[str, object]) -> None:
        self._last_report = report
        self._render_pre_recognition_inputs()
        self._current_result_hint.setVisible(False)
        annotated = _annotated_recognition_files(report, self._project_root)
        files = _filter_recognition_files(annotated, self._duplicate_filter.currentText())
        warnings = [str(item) for item in report.get("warnings", []) or []]
        duplicate_count = sum(1 for item in annotated if item.get("_duplicate"))
        self._set_status(f"已读取识别报告：{len(annotated)} 个文件，{len(warnings)} 条提醒。")
        self._fill_recognition_table(files)
        self._counts.setPlainText(_recognition_status_bar_summary(report, annotated))
        self._asset_summary.setPlainText(_recognition_asset_summary(files))
        self._render_next_steps(self._detail_run_for_current_report(report), files)
        self._group_preview.setPlainText(_group_preview_user_summary(report.get("group_preview") if isinstance(report.get("group_preview"), dict) else {}))
        self._technical_details.setPlainText(
            _json(
                {
                    "recognition_report": report,
                    "type_counts": report.get("type_counts", {}),
                    "duplicate_count": duplicate_count,
                    "backend": "app.bioinformatics.project_recognition.run_project_recognition",
                }
            )
        )

    def _rerender_last_report(self) -> None:
        if self._last_report is not None:
            self._render_report(self._last_report)

    def _clear_current_recognition_display(self) -> None:
        self._last_report = None
        self._current_result_hint.setVisible(True)
        self._table.setRowCount(0)
        self._counts.setPlainText("尚未开始本次识别。请选择上方数据源后点击“开始识别”。")
        self._asset_summary.setPlainText("")
        self._clear_next_steps()
        self._group_preview.setPlainText("")
        self._technical_details.setPlainText("")
        self._clear_recognition_detail()

    def _render_recognition_history(self) -> None:
        runs = list_recognition_runs(self._project_root) if self._project_root is not None else []
        self._history_summary_label.setText(_recognition_history_summary_text(runs))
        self._history_toggle_button.setEnabled(bool(runs))
        self._history_toggle_button.setText("收起历史记录" if self._history_expanded else "展开历史记录")
        self._history_table.setVisible(bool(runs) and self._history_expanded)
        rows = [
            [
                _format_history_time(str(run.get("generated_at") or "")),
                str(run.get("batch_name") or run.get("run_id") or "识别记录"),
                _history_input_text(run),
                str(run.get("recognized_file_count") or 0),
                _history_content_summary(run),
                str(run.get("warning_count") or 0),
                "当前使用中" if run.get("is_current") else _history_status_text(run),
                "",
            ]
            for run in runs
        ]
        _fill_table(self._history_table, rows)
        _set_table_widths(self._history_table, [150, 150, 220, 100, 260, 90, 110, 220])
        self._history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        for row_index, run in enumerate(runs):
            actions = QFrame()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(4)
            run_id = str(run.get("run_id") or "")
            view_button = _button("查看批次详情", "secondaryButton", lambda _checked=False, rid=run_id: self._view_history_run(rid), role="secondary", small=True)
            delete_button = _button("删除记录", "secondaryButton", lambda _checked=False, rid=run_id: self._delete_history_run(rid), role="danger", small=True)
            actions_layout.addWidget(view_button)
            actions_layout.addWidget(delete_button)
            self._history_table.setCellWidget(row_index, 7, actions)

    def _toggle_history_table(self) -> None:
        self._history_expanded = not self._history_expanded
        self._render_recognition_history()

    def _view_history_run(self, run_id: str) -> None:
        run = _recognition_run_by_id(self._project_root, run_id)
        if run is None:
            self._set_status("未找到该历史识别记录。")
            return
        self._render_recognition_detail(run, None)
        self._set_status("已显示历史识别详情；它不属于本次识别结果，也未修改当前识别批次。")

    def _view_current_file_detail(self, file_record: dict[str, object]) -> None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。")
            return
        report = self._last_report or {"files": [file_record]}
        self._render_recognition_detail(self._detail_run_for_current_report(report), file_record)
        self._set_status("已显示本次识别文件详情；未修改当前识别批次。")

    def _render_recognition_detail(self, run: dict[str, object], file_record: dict[str, object] | None) -> None:
        if self._project_root is None:
            return
        payload = build_recognition_detail_payload(self._project_root, run, file_record)
        self._selected_detail_run = run
        self._selected_detail_file = file_record
        self._selected_detail_payload = payload
        self._detail_report.setPlainText(format_recognition_detail_text(payload))
        self._detail_technical.setPlainText(format_recognition_detail_technical(payload))
        self._detail_export_button.setEnabled(True)

    def _render_next_steps(self, run: dict[str, object], files: list[dict[str, object]] | None) -> None:
        if self._project_root is None:
            return
        next_steps = build_recognition_next_steps(self._project_root, run, files)
        self._active_next_run = run
        self._active_next_files = [dict(item) for item in files or []]
        self._active_next_steps = next_steps
        self._next_steps_summary.setPlainText(_recognition_primary_next_step_text(next_steps))
        self._next_step_actions = [
            {"label": "继续：数据准备与标准化", "target": "continue_to_readiness"},
            {"label": "导出数据识别报告", "target": "export_recognition_report"},
        ]
        for index, button in enumerate(self._next_action_buttons):
            if index < len(self._next_step_actions):
                button.setText(str(self._next_step_actions[index].get("label") or "操作"))
                _apply_button_semantics(button, "primary_next" if index == 0 else "secondary")
                button.setVisible(True)
                button.setEnabled(True)
            else:
                button.setVisible(False)
                button.setEnabled(False)

    def _clear_next_steps(self) -> None:
        self._active_next_run = None
        self._active_next_files = []
        self._active_next_steps = None
        self._next_step_actions = []
        self._next_steps_summary.setPlainText("完成本次识别后，可继续进入数据准备与标准化。")
        for button in self._next_action_buttons:
            button.setVisible(False)
            button.setEnabled(False)

    def _execute_next_step_action(self, index: int) -> None:
        if self._project_root is None or index >= len(self._next_step_actions):
            return
        action = self._next_step_actions[index]
        target = str(action.get("target") or "")
        if target == "continue_to_readiness":
            self.continue_to_readiness()
            return
        if target == "set_current_recognition_run":
            run_id = str(action.get("run_id") or (self._active_next_run or {}).get("run_id") or "")
            self._set_history_run_current(run_id)
            run = _recognition_run_by_id(self._project_root, run_id)
            if run is not None:
                self._render_next_steps(run, None)
                self._render_recognition_detail(run, self._selected_detail_file)
            return
        if target == "detail":
            if self._active_next_run is not None:
                first_file = self._active_next_files[0] if self._active_next_files else None
                self._render_recognition_detail(self._active_next_run, first_file)
                self._set_status("已显示识别详情；未修改当前识别批次。")
            return
        if target == "export_recognition_report":
            if self._selected_detail_run is None and self._active_next_run is not None:
                self._selected_detail_run = self._active_next_run
                self._selected_detail_file = self._active_next_files[0] if self._active_next_files else None
            self.export_recognition_detail_report()
            return
        if target == "data_source":
            self.navigate_requested.emit("data_source", self._project_root)
            return
        if target in {"standardization", "analysis_tasks", "result_browser", "group_design"}:
            self.navigate_requested.emit(target, self._project_root)
            return
        self._set_status(f"下一步操作暂未接入：{action.get('label') or target}")

    def _clear_recognition_detail(self) -> None:
        self._selected_detail_run = None
        self._selected_detail_file = None
        self._selected_detail_payload = None
        self._detail_report.setPlainText("请选择本次识别文件或历史识别记录查看详情。")
        self._detail_technical.setPlainText("")
        self._detail_technical.setVisible(False)
        self._detail_export_button.setEnabled(False)

    def _detail_run_for_current_report(self, report: dict[str, object]) -> dict[str, object]:
        if self._project_root is not None:
            current = next((run for run in list_recognition_runs(self._project_root) if run.get("is_current")), None)
            if current is not None:
                return current
        return {
            "run_id": str(report.get("run_id") or "current_session"),
            "batch_name": "本次识别",
            "generated_at": report.get("generated_at"),
            "recognition_report": report,
        }

    def _set_history_run_current(self, run_id: str) -> None:
        if self._project_root is None or not set_current_recognition_run(self._project_root, run_id):
            self._set_status("设为当前结果失败。")
            return
        self._render_recognition_history()
        self._set_status("已将该识别记录设为当前标准化输入。")

    def _delete_history_run(self, run_id: str) -> None:
        run = _recognition_run_by_id(self._project_root, run_id)
        was_current = bool(run and run.get("is_current"))
        if self._project_root is None or not delete_recognition_run(self._project_root, run_id):
            self._set_status("删除历史识别记录失败。")
            return
        self._render_recognition_history()
        if was_current:
            self._set_status("当前识别结果已删除，请重新识别或选择另一条历史记录。")
        else:
            self._set_status("已删除历史识别记录。")

    def _render_pre_recognition_inputs(self) -> None:
        rows = _registered_source_rows(self._project_root)
        self._pre_recognition_rows = rows
        self._pre_recognition_checks = {}
        selection = _load_pending_recognition_selection(self._project_root)
        self._pre_recognition_empty_label.setVisible(not rows)
        _fill_table(
            self._pre_recognition_table,
            [["", row.source_type, row.source_label, row.location, row.status] for row in rows],
        )
        header_item = self._pre_recognition_table.horizontalHeaderItem(0)
        if header_item is not None:
            header_item.setText("选择")
            header_item.setCheckState(Qt.Unchecked)
        _set_table_widths(self._pre_recognition_table, [56, 130, 180, 200, 170])
        self._pre_recognition_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        for row_index, row in enumerate(rows):
            checkbox = QCheckBox()
            checkbox.setObjectName(f"preRecognitionSelect_{row.acquisition_id}")
            checkbox.setChecked(_recognition_row_selected_by_context(row, selection))
            checkbox.stateChanged.connect(lambda _state=0: self._refresh_pre_recognition_selection_state())
            self._pre_recognition_checks[row.acquisition_id] = checkbox
            self._pre_recognition_table.setCellWidget(row_index, 0, checkbox)
            item = self._pre_recognition_table.item(row_index, 3)
            if item is not None and row.location_tooltip:
                item.setToolTip(row.location_tooltip)
            for col in range(self._pre_recognition_table.columnCount()):
                cell = self._pre_recognition_table.item(row_index, col)
                if cell is not None and col in {3, 4}:
                    cell.setToolTip(row.location_tooltip or row.location)
        self._refresh_pre_recognition_selection_state()

    def _fill_recognition_table(self, files: list[dict[str, object]]) -> None:
        self._table.setRowCount(len(files))
        rows = []
        for item in files:
            warning = str(item.get("warning") or "")
            if item.get("_duplicate"):
                warning = "检测到可能重复导入的文件。" if not warning else f"{warning}；检测到可能重复导入的文件。"
            display_path, tooltip_path = _recognition_file_display_path(item)
            rows.append(
                [
                    str(item.get("file_name", "")),
                    display_path,
                    _recognition_type_text(item),
                    _format_confidence(item.get("confidence")),
                    _format_file_size(item.get("file_size")),
                    str(item.get("reason", "")),
                    warning,
                    "",
                ]
            )
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                table_item = QTableWidgetItem(value)
                source = files[row_index]
                if col_index == 1:
                    table_item.setToolTip(_recognition_file_display_path(source)[1])
                elif col_index == 2:
                    table_item.setToolTip(_recognition_roles_tooltip(source))
                elif col_index == 3:
                    table_item.setToolTip("软件根据文件内容推断文件类型的可信程度。它不是数据质量评分，也不是科研可信度评分。")
                elif col_index == 4:
                    table_item.setToolTip(f"原始 bytes：{source.get('file_size', '未记录')}")
                self._table.setItem(row_index, col_index, table_item)
            detail_button = _button("查看文件详情", "secondaryButton", lambda _checked=False, record=dict(files[row_index]): self._view_current_file_detail(record), role="secondary", small=True)
            detail_button.setObjectName(f"recognitionFileDetailButton_{row_index}")
            self._table.setCellWidget(row_index, 7, detail_button)
        self._table.resizeColumnsToContents()

    def _toggle_pre_recognition_header(self, section: int) -> None:
        if section != 0 or not self._pre_recognition_checks:
            return
        should_check = not all(checkbox.isChecked() for checkbox in self._pre_recognition_checks.values())
        for checkbox in self._pre_recognition_checks.values():
            checkbox.setChecked(should_check)
        self._refresh_pre_recognition_selection_state()

    def _selected_pre_recognition_rows(self) -> list[RegisteredSourceRow]:
        selected = []
        for row in self._pre_recognition_rows:
            checkbox = self._pre_recognition_checks.get(row.acquisition_id)
            if checkbox is not None and checkbox.isChecked():
                selected.append(row)
        return selected

    def _refresh_pre_recognition_selection_state(self) -> None:
        selected_count = len(self._selected_pre_recognition_rows())
        self._delete_selected_inputs_button.setEnabled(selected_count > 0)
        header_item = self._pre_recognition_table.horizontalHeaderItem(0)
        if header_item is not None:
            all_checked = bool(self._pre_recognition_checks) and selected_count == len(self._pre_recognition_checks)
            header_item.setCheckState(Qt.Checked if all_checked else Qt.Unchecked)

    def _delete_selected_pre_recognition_sources(self) -> None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。")
            return
        rows = self._selected_pre_recognition_rows()
        if not rows:
            self._set_status("请先选择需要移除的数据。")
            return
        removed = 0
        for row in rows:
            if _remove_acquisition_binding_by_id(self._project_root, row.acquisition_id):
                removed += 1
        self._render_pre_recognition_inputs()
        self._set_status(f"已从待识别列表移除 {removed} 个条目；未删除原始文件。")

    def _set_status(self, text: str) -> None:
        self._status_label.setText(text)


class BioinformaticsReadinessDashboardWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()

    def __init__(self, *, on_continue: Callable[[Path], None] | None = None, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self._last_artifacts: dict[str, object] = {}
        self.setObjectName("bioinformaticsReadinessDashboardPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_status()

    def run_readiness_check(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        artifacts = run_project_readiness(self._project_root)
        self._render(artifacts)
        return artifacts

    def refresh_status(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        artifacts = load_readiness_artifacts(self._project_root)
        if artifacts.get("readiness_report") is None:
            self._last_artifacts = {}
            self._status_label.setText("暂不能继续：尚未运行数据准备检查。")
            self._render_data_check_gate(set(), {}, {})
            self._recognized_inputs_label.setText("已识别到的数据：尚未检查")
            self._missing_inputs_label.setText("仍需补充的数据：尚未检查")
            self._next_step_label.setText("下一步建议：点击“重新检查”，让系统读取最新的数据识别结果。")
            self._warning_chips.setText("提示：尚未运行数据准备检查。")
            self._render_todo_items(set())
            self._matrix.setRowCount(0)
            self._details.setPlainText("")
        else:
            self._render(artifacts)

    def continue_to_standardization(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        ok, reason = _can_continue_from_readiness(self._project_root)
        if not ok:
            self._status_label.setText(f"不能继续：{reason} 请返回数据来源补充文件。")
            return
        self.continue_requested.emit(self._project_root)

    def status_message(self) -> str:
        return self._status_label.text()

    def supplement_missing_info(
        self,
        kind: str,
        *,
        mode: str = "file",
        path: str | Path | None = None,
        manual_text: str | None = None,
    ) -> bool:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return False
        normalized = _normalize_missing_input(kind)
        if normalized not in {"sample_metadata", "clinical_metadata", "expression_matrix", "comparison_config", "gmt_gene_set"}:
            self._status_label.setText("当前缺失项暂不支持在本页补充。")
            return False
        if normalized in {"expression_matrix", "gmt_gene_set"} and mode == "manual":
            self._status_label.setText(f"{_missing_input_label(normalized)}仅支持选择本地文件补充。")
            return False
        if mode == "file":
            if path is None:
                selected, _ = QFileDialog.getOpenFileName(self, "选择补充文件", str(self._project_root))
                if not selected:
                    return False
                path = selected
            source = Path(path).expanduser().resolve()
            if not source.exists():
                self._status_label.setText("补充文件不存在，请重新选择。")
                return False
            summary = register_acquisition(
                self._project_root,
                source_type=f"readiness_supplement_{normalized}",
                source_label=_missing_input_label(normalized),
                strategy="copy",
                selected_paths=[source],
                metadata={"supplement_kind": normalized, "ui_stage": "UI-07"},
            )
            self._status_label.setText(f"已补充{_missing_input_label(normalized)}：{Path(summary.copied_files[0]).name if summary.copied_files else source.name}。")
            self.save_and_rerun_readiness()
            return True
        if mode == "manual":
            text = manual_text
            if text is None:
                text, ok = QInputDialog.getMultiLineText(
                    self,
                    f"手动输入{_missing_input_label(normalized)}",
                    "请按 TSV 格式输入；第一行为字段名。",
                    _template_text_for_missing_input(normalized),
                )
                if not ok:
                    return False
            _save_manual_supplement(self._project_root, normalized, text or _template_text_for_missing_input(normalized))
            self._status_label.setText(f"已保存手动补充的{_missing_input_label(normalized)}。")
            self.save_and_rerun_readiness()
            return True
        self._status_label.setText("未知补充方式。")
        return False

    def confirm_group_preview_as_comparison(self, manual_text: str | None = None, *, skip_dialog: bool = False) -> bool:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return False
        preview = _project_group_preview(self._project_root)
        if not _group_preview_has_candidate(preview):
            self._status_label.setText("尚未检测到可确认的候选分组，请手动设置比较组。")
            return False
        text = manual_text or _comparison_config_text_from_group_preview(preview)
        if manual_text is None and not skip_dialog:
            text, ok = QInputDialog.getMultiLineText(
                self,
                "确认比较组",
                "请确认候选分组是否符合研究设计。确认后才会写入正式比较组设置。",
                text,
            )
            if not ok:
                self._status_label.setText("已取消确认比较组。")
                return False
        _save_manual_supplement(self._project_root, "comparison_config", text)
        _append_comparison_confirmation_audit(self._project_root, preview, text)
        run_project_recognition(self._project_root)
        artifacts = run_project_readiness(self._project_root)
        self._render(artifacts)
        self._status_label.setText("已确认候选分组为正式比较组，并重新检查数据准备状态。")
        return True

    def create_missing_info_template(self, kind: str) -> Path | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        normalized = _normalize_missing_input(kind)
        if normalized not in {"sample_metadata", "clinical_metadata", "comparison_config"}:
            self._status_label.setText("当前缺失项暂无模板。")
            return None
        target = self._project_root / "templates" / f"{normalized}_template.tsv"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_template_text_for_missing_input(normalized), encoding="utf-8")
        self._status_label.setText(f"已生成{_missing_input_label(normalized)}模板：{target}")
        return target

    def save_and_rerun_readiness(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        run_project_recognition(self._project_root)
        artifacts = run_project_readiness(self._project_root)
        self._render(artifacts)
        self._status_label.setText(f"{self._status_label.text()}；已重新检查。")
        return artifacts

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(
            _header(
                "Data Check & Preparation / 数据检查与准备",
                "只读展示数据检查与 preflight eligibility；不生成正式分析结果。",
                back_text="返回数据来源",
                back_signal=self.back_requested,
            )
        )
        root.addWidget(self._build_data_check_gate_card())

        status_card, status_layout = _card("数据准备概览")
        status_card.setObjectName("readinessStatusCard")
        self._status_label = _status_label("暂不能继续：尚未运行数据准备检查。")
        self._status_label.setObjectName("readinessStatusBadge")
        self._recognized_inputs_label = _muted("已识别到的数据：尚未检查")
        self._recognized_inputs_label.setObjectName("readinessRecognizedInputs")
        self._missing_inputs_label = _muted("仍需补充的数据：尚未检查")
        self._missing_inputs_label.setObjectName("readinessMissingInputs")
        self._next_step_label = _muted("下一步建议：点击“重新检查”，让系统读取最新的数据识别结果。")
        self._next_step_label.setObjectName("readinessNextStep")
        self._warning_chips = _muted("提示：尚未运行数据准备检查。")
        self._warning_chips.setObjectName("readinessWarningChips")
        status_layout.addWidget(self._status_label)
        status_layout.addWidget(self._recognized_inputs_label)
        status_layout.addWidget(self._missing_inputs_label)
        status_layout.addWidget(self._next_step_label)
        status_layout.addWidget(self._warning_chips)
        root.addWidget(status_card)

        todo_card, todo_layout = _card("待办清单")
        todo_card.setObjectName("readinessTodoCard")
        self._todo_empty_label = _muted("当前没有必须补充的信息。")
        self._todo_empty_label.setObjectName("readinessTodoEmpty")
        todo_layout.addWidget(self._todo_empty_label)
        self._todo_rows: dict[str, QFrame] = {}
        self._sample_file_button = _button("上传样本信息", "secondaryButton", lambda: self.supplement_missing_info("sample_metadata", mode="file"))
        self._sample_manual_button = _button("手动输入样本信息", "secondaryButton", lambda: self.supplement_missing_info("sample_metadata", mode="manual"))
        self._sample_template_button = _button("下载样本信息模板", "secondaryButton", lambda: self.create_missing_info_template("sample_metadata"))
        self._clinical_file_button = _button("上传临床表", "secondaryButton", lambda: self.supplement_missing_info("clinical_metadata", mode="file"))
        self._clinical_defer_button = _button("暂不做相关分析", "secondaryButton", lambda: self._defer_optional_analysis("clinical_metadata"))
        self._clinical_manual_button = _button("手动输入临床信息", "secondaryButton", lambda: self.supplement_missing_info("clinical_metadata", mode="manual"))
        self._clinical_template_button = _button("下载临床信息模板", "secondaryButton", lambda: self.create_missing_info_template("clinical_metadata"))
        self._clinical_manual_button.setVisible(False)
        self._clinical_template_button.setVisible(False)
        self._expression_file_button = _button("上传表达矩阵", "secondaryButton", lambda: self.supplement_missing_info("expression_matrix", mode="file"))
        self._comparison_preview_button = _button("使用候选分组创建比较组", "secondaryButton", self.confirm_group_preview_as_comparison)
        self._comparison_manual_button = _button("手动设置比较组", "secondaryButton", lambda: self.supplement_missing_info("comparison_config", mode="manual"))
        self._comparison_file_button = _button("导入比较组表", "secondaryButton", lambda: self.supplement_missing_info("comparison_config", mode="file"))
        self._comparison_template_button = _button("下载比较组模板", "secondaryButton", lambda: self.create_missing_info_template("comparison_config"))
        self._gmt_file_button = _button("上传 GMT 文件", "secondaryButton", lambda: self.supplement_missing_info("gmt_gene_set", mode="file"))
        self._gmt_defer_button = _button("暂不做 GSEA", "secondaryButton", lambda: self._defer_optional_analysis("gmt_gene_set"))
        todo_items = [
            ("expression_matrix", "表达矩阵", "用途：后续标准化、差异表达、富集和相关性分析的核心输入。", "当前状态：未提供。", [self._expression_file_button]),
            ("sample_metadata", "样本信息", "用途：识别样本分组、组织来源和实验条件。", "当前状态：未提供。", [self._sample_file_button, self._sample_manual_button, self._sample_template_button]),
            ("clinical_metadata", "临床信息", "用途：用于生存分析和临床变量关联。", "当前状态：未提供。", [self._clinical_file_button, self._clinical_defer_button]),
            ("comparison_config", "比较分组", "用途：用于差异表达分析，例如 control vs treatment。", "当前状态：未设置。", [self._comparison_preview_button, self._comparison_manual_button, self._comparison_file_button, self._comparison_template_button]),
            ("gmt_gene_set", "GMT 基因集", "用途：用于 GSEA。", "当前状态：未提供。", [self._gmt_file_button, self._gmt_defer_button]),
        ]
        self._todo_state_labels: dict[str, QLabel] = {}
        for key, title, purpose, state, buttons in todo_items:
            row, state_label = _readiness_todo_row(title, purpose, state, buttons)
            row.setObjectName(f"readinessTodo_{key}")
            row.setVisible(False)
            self._todo_rows[key] = row
            self._todo_state_labels[key] = state_label
            todo_layout.addWidget(row)
        root.addWidget(todo_card)

        self._matrix = _table(["分析项目", "当前状态", "还需要什么", "建议操作"])
        self._matrix.setObjectName("readinessCapabilityTable")
        self._matrix.setMinimumHeight(380)
        root.addWidget(self._matrix)

        self._details = _text_preview(130)
        self._details.setVisible(False)
        root.addWidget(_button("技术详情", "secondaryButton", lambda: _toggle_details(self._details)))
        root.addWidget(self._details)
        bottom_actions = QHBoxLayout()
        bottom_actions.addWidget(_button("重新检查", "secondaryButton", self.save_and_rerun_readiness))
        bottom_actions.addWidget(_button("继续：标准化数据", "primaryButton", self.continue_to_standardization))
        bottom_actions.addStretch(1)
        root.addLayout(bottom_actions)

    def _build_data_check_gate_card(self) -> QFrame:
        card, layout = _card("Readiness Table / 数据检查状态")
        card.setObjectName("bioinformaticsDataCheckGateCard")
        card.setProperty("formalActionEnabled", False)
        top_row = QHBoxLayout()
        self._data_check_status_chip = _status_label("blocked / 尚未检查")
        self._data_check_status_chip.setObjectName("bioinformaticsDataCheckStatusChip")
        self._data_check_status_chip.setProperty("statusSemanticKey", "analysis.status.blocked")
        self._data_check_status_chip.setProperty("formalActionEnabled", False)
        top_row.addWidget(self._data_check_status_chip)
        top_row.addStretch(1)
        layout.addLayout(top_row)
        self._data_check_readiness_table = _table(["check", "status", "gate meaning", "next action"])
        self._data_check_readiness_table.setObjectName("bioinformaticsDataCheckReadinessTable")
        self._data_check_readiness_table.setProperty("formalActionEnabled", False)
        layout.addWidget(self._data_check_readiness_table)
        self._data_check_summary = _read_only_report_view(78)
        self._data_check_summary.setObjectName("bioinformaticsDataCheckReadinessSummary")
        self._data_check_summary.setProperty("formalActionEnabled", False)
        layout.addWidget(self._data_check_summary)
        actions = QHBoxLayout()
        copy_button = _button("复制检查摘要", "secondaryButton", self._copy_data_check_summary, role="secondary")
        save_button = _button("Save Report - file picker required", "secondaryButton", lambda: None, role="secondary")
        save_button.setObjectName("bioinformaticsDataCheckSaveReportDisabledButton")
        save_button.setEnabled(False)
        save_button.setProperty("buttonBehavior", "disabled_file_picker_required")
        save_button.setProperty("formalActionEnabled", False)
        actions.addWidget(copy_button)
        actions.addWidget(save_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        notice = _muted("关键检查通过后进入 Group & Design；ready_for_preflight 只表示可做预检，不是 formal_computed_result。")
        notice.setObjectName("bioinformaticsDataCheckGateNotice")
        notice.setProperty("resultSemanticKey", "preflight_only")
        notice.setProperty("formalActionEnabled", False)
        layout.addWidget(notice)
        self._render_data_check_gate(set(), {}, {})
        return card

    def _copy_data_check_summary(self) -> None:
        QApplication.clipboard().setText(self._data_check_summary.toPlainText())
        self._status_label.setText("已复制数据检查摘要；未生成报告文件。")

    def _render_data_check_gate(
        self,
        missing: set[str],
        readiness_payload: dict[str, object],
        matrix_payload: dict[str, object],
    ) -> None:
        available = set(str(item) for item in readiness_payload.get("available_inputs", []) or [])
        warnings = [str(item) for item in readiness_payload.get("warnings", []) or [] if str(item)]
        has_expression = "expression_matrix" in available or "expression_matrix" not in missing and bool(readiness_payload)
        has_sample = "sample_metadata" in available or "sample_metadata" not in missing and bool(readiness_payload)
        has_clinical = "clinical_metadata" in available
        has_comparison = "comparison_config" in available or "comparison_config" not in missing and bool(readiness_payload)
        check_rows = [
            ("expression matrix integrity", "passed" if has_expression else "missing", "required for preflight", "Add or register expression matrix"),
            ("sample annotation completeness", "passed" if has_sample else "missing", "required for grouping", "Add sample metadata"),
            ("clinical data completeness", "passed" if has_clinical else "warning", "optional for survival/clinical association", "Add clinical table if needed"),
            ("gene annotation mapping", "warning" if warnings else "ready_for_preflight", "resolver-first check only", "Review mapping before analysis"),
            ("batch/platform consistency", "warning" if warnings else "ready_for_preflight", "preflight eligibility only", "Review platform before formal run"),
            ("missing rate check", "warning" if warnings else "ready_for_preflight", "preflight eligibility only", "Review missing values"),
            ("outlier sample detection", "blocked" if not has_sample else "warning", "diagnostic only", "Run after Data Check input exists"),
        ]
        _fill_table(self._data_check_readiness_table, [list(row) for row in check_rows])
        if has_expression and has_sample and has_comparison:
            chip_text = "ready_for_preflight / 可进入预检"
            chip_key = "analysis.status.preflight_only"
        elif missing:
            chip_text = "missing / 仍需补充"
            chip_key = "feature.status.blocked"
        else:
            chip_text = "blocked / 尚未检查"
            chip_key = "analysis.status.blocked"
        self._data_check_status_chip.setText(chip_text)
        self._data_check_status_chip.setProperty("statusSemanticKey", chip_key)
        self._data_check_summary.setPlainText(
            "\n".join(
                [
                    "Readiness summary: Data Check only evaluates preflight eligibility.",
                    f"Available inputs: {', '.join(sorted(available)) if available else 'none'}",
                    f"Missing inputs: {', '.join(sorted(missing)) if missing else 'none'}",
                    "Only preflight condition summary is shown. No fake matrix, result, plot, report, or export is generated.",
                ]
            )
        )

    def _render(self, artifacts: dict[str, object]) -> None:
        self._last_artifacts = artifacts
        readiness = artifacts.get("readiness_report") or {}
        matrix = artifacts.get("capability_matrix") or {}
        readiness_payload = readiness if isinstance(readiness, dict) else {}
        matrix_payload = matrix if isinstance(matrix, dict) else {}
        group_preview = _project_group_preview(self._project_root)
        missing = _missing_readiness_inputs(readiness_payload, matrix_payload)
        self._render_data_check_gate(missing, readiness_payload, matrix_payload)
        self._status_label.setText(_readiness_overall_summary(readiness_payload, matrix_payload, missing))
        self._recognized_inputs_label.setText(_readiness_recognized_inputs_text(readiness_payload))
        self._missing_inputs_label.setText(_readiness_missing_inputs_text(missing, group_preview))
        self._next_step_label.setText(_readiness_next_step_text(readiness_payload, matrix_payload, missing, group_preview))
        self._warning_chips.setText(_readiness_default_warning_summary(readiness_payload, matrix_payload, missing))
        self._render_todo_items(missing, group_preview)
        self._details.setPlainText(
            _json(
                {
                    "readiness_report": readiness,
                    "analysis_capability_matrix": matrix,
                    "readiness_report_path": artifacts.get("readiness_path"),
                    "capability_matrix_path": artifacts.get("matrix_path"),
                }
            )
        )
        rows = matrix.get("rows", []) if isinstance(matrix, dict) else []
        _fill_table(
            self._matrix,
            [
                [
                    str(row.get("label", "")),
                    _analysis_readiness_status_label(row),
                    _analysis_missing_text(row, group_preview),
                    _analysis_suggested_action(row, group_preview),
                ]
                for row in rows
                if isinstance(row, dict)
            ],
        )
        _set_table_widths(self._matrix, [190, 170, 240, 280])
        self._matrix.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

    def _render_todo_items(self, missing: set[str], group_preview: dict[str, object] | None = None) -> None:
        visible = {key for key in missing if key in self._todo_rows}
        self._todo_empty_label.setVisible(not visible)
        for key, row in self._todo_rows.items():
            row.setVisible(key in visible)
        comparison_state = self._todo_state_labels.get("comparison_config")
        if comparison_state is not None:
            if "comparison_config" in missing and _group_preview_has_candidate(group_preview):
                comparison_state.setText("当前状态：候选分组待确认。")
                self._comparison_preview_button.setVisible(True)
            else:
                comparison_state.setText("当前状态：未设置。")
                self._comparison_preview_button.setVisible(False)

    def _defer_optional_analysis(self, kind: str) -> None:
        label = _missing_input_label(kind)
        self._status_label.setText(f"已标记：本次暂不处理{label}。这不会改动项目数据。")


class BioinformaticsStandardizedAssetsWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()
    group_design_requested = Signal(object)

    def __init__(self, *, on_continue: Callable[[Path], None] | None = None, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self.setObjectName("bioinformaticsStandardizedAssetsPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_assets()

    def generate_assets(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        artifacts = generate_standardized_assets(self._project_root)
        self._render(artifacts)
        return artifacts

    def refresh_assets(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        artifacts = load_standardization_artifacts(self._project_root)
        if artifacts.get("registry") is None:
            self._status_label.setText("尚未生成标准化资产。")
            self._assets.setRowCount(0)
            self._selection_table.setRowCount(0)
            self._render_user_overview(artifacts)
            self._summary.setPlainText("")
            self._manifest.setPlainText(_json({"current_input": standardization_current_input_summary(self._project_root)}))
        else:
            self._render(artifacts)

    def continue_to_workflow(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        ok, reason = _can_continue_from_standardization(self._project_root)
        if not ok:
            self._status_label.setText(f"不能继续：{reason} 请返回数据来源补充文件。")
            return
        self.continue_requested.emit(self._project_root)

    def status_message(self) -> str:
        return self._status_label.text()

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("数据准备与标准化", "确认表达矩阵和样本分组，生成后续分析可用的标准化资产。", back_text="返回 Ready 检查", back_signal=self.back_requested))
        self._status_label = _status_label("尚未生成标准化资产。")
        root.addWidget(self._status_label)

        input_card, input_layout = _card("当前输入数据")
        self._current_input_summary = _read_only_report_view(100)
        self._current_input_summary.setObjectName("standardizationCurrentRecognitionInput")
        input_layout.addWidget(self._current_input_summary)
        self._input_detail = _text_preview(120)
        self._input_detail.setObjectName("standardizationInputDetail")
        self._input_detail.setVisible(False)
        input_actions = QHBoxLayout()
        input_actions.addWidget(_button("查看输入详情", "secondaryButton", lambda: _toggle_details(self._input_detail), role="secondary"))
        input_actions.addStretch(1)
        input_layout.addLayout(input_actions)
        input_layout.addWidget(self._input_detail)
        root.addWidget(input_card)

        expression_card, expression_layout = _card("表达矩阵状态")
        self._expression_status = _read_only_report_view(100)
        self._expression_status.setObjectName("standardizationExpressionStatus")
        expression_layout.addWidget(self._expression_status)
        root.addWidget(expression_card)

        group_card, group_layout = _card("分组确认")
        self._group_status = _read_only_report_view(110)
        self._group_status.setObjectName("standardizationGroupStatus")
        group_layout.addWidget(self._group_status)
        root.addWidget(group_card)

        status_card, status_layout = _card("标准化状态")
        status_grid = QGridLayout()
        status_grid.setHorizontalSpacing(SPACING["sm"])
        status_grid.setVerticalSpacing(SPACING["sm"])
        self._standardization_status_blocks: dict[str, tuple[QLabel, QLabel]] = {}
        for index, key in enumerate(("expression", "sample_metadata", "group_design", "gene_annotation", "standardized_result")):
            block = QFrame()
            block.setObjectName("bioProjectMiniStatusBlock")
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
            block_layout.setSpacing(2)
            title = QLabel("")
            title.setObjectName("bioProjectMiniStatusTitle")
            value = QLabel("")
            value.setObjectName("bioProjectMiniStatusValue")
            value.setWordWrap(True)
            block_layout.addWidget(title)
            block_layout.addWidget(value)
            self._standardization_status_blocks[key] = (title, value)
            status_grid.addWidget(block, index // 3, index % 3)
        status_layout.addLayout(status_grid)
        root.addWidget(status_card)

        main_card, main_layout = _card("主操作")
        main_actions = QHBoxLayout()
        self._confirm_group_button = _button("确认分组与比较设计", "primaryButton", self.open_group_design, role="primary_action")
        self._generate_assets_button = _button("生成标准化资产", "primaryButton", self.generate_assets, role="primary_action")
        self._continue_tasks_button = _button("继续：分析任务中心", "primaryButton", self.continue_to_workflow, role="primary_next")
        self._refresh_assets_button = _button("刷新状态", "secondaryButton", self.refresh_assets, role="secondary")
        self._export_report_button = _button("导出标准化报告 - 需文件选择器", "secondaryButton", self.export_standardization_report, role="secondary")
        self._export_report_button.setObjectName("bioinformaticsStandardizationExportReportDisabledButton")
        self._export_report_button.setEnabled(False)
        self._export_report_button.setProperty("buttonBehavior", "disabled_file_picker_required")
        self._export_report_button.setProperty("formalActionEnabled", False)
        for button in (self._confirm_group_button, self._generate_assets_button, self._continue_tasks_button, self._refresh_assets_button, self._export_report_button):
            main_actions.addWidget(button)
        main_actions.addStretch(1)
        main_layout.addLayout(main_actions)
        self._workflow_note = _muted("可进入分析任务中心不等于可以直接启动 DEG；DEG 需要表达矩阵可用，并且分组与比较设计已确认。")
        self._workflow_note.setObjectName("standardizationWorkflowGateNote")
        main_layout.addWidget(self._workflow_note)
        root.addWidget(main_card)

        diagnostic_card, diagnostic_layout = _card("标准化详情 / 开发者诊断")
        diagnostic_layout.addWidget(_muted("普通流程不需要查看这些内容；仅用于排错、审计和开发者诊断。"))
        self._diagnostic_toggle_button = _button("展开开发者诊断", "secondaryButton", self._toggle_diagnostics, role="secondary")
        diagnostic_layout.addWidget(self._diagnostic_toggle_button, alignment=Qt.AlignLeft)
        self._diagnostic_frame = QFrame()
        self._diagnostic_frame.setVisible(False)
        diagnostic_inner = QVBoxLayout(self._diagnostic_frame)
        diagnostic_inner.setContentsMargins(0, 0, 0, 0)
        self._assets = _table(["资产 ID", "资产类型", "来源文件", "样本数", "物种", "用途", "限制", "状态", "默认"])
        self._assets.setObjectName("standardizedAssetsTable")
        diagnostic_inner.addWidget(self._assets)
        self._selection_table = _table(["资产类型", "候选数", "默认资产", "状态", "说明"])
        self._selection_table.setObjectName("standardizedAssetSelectionTable")
        diagnostic_inner.addWidget(self._selection_table)
        diagnostic_actions = QHBoxLayout()
        diagnostic_actions.addWidget(_button("保存默认资产选择", "secondaryButton", self.save_asset_selection, role="secondary"))
        diagnostic_actions.addWidget(_button("打开标准化结果文件夹", "secondaryButton", lambda: _open_path(self._project_root / "standardized_data" if self._project_root else None), role="secondary"))
        diagnostic_actions.addStretch(1)
        diagnostic_inner.addLayout(diagnostic_actions)
        self._summary = _text_preview(140)
        diagnostic_inner.addWidget(self._summary)
        self._manifest = _text_preview(150)
        diagnostic_inner.addWidget(self._manifest)
        diagnostic_layout.addWidget(self._diagnostic_frame)
        root.addWidget(diagnostic_card)

    def open_group_design(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        self.group_design_requested.emit(self._project_root)

    def export_standardization_report(self) -> Path | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        self._status_label.setText("报告导出已降级：需要文件选择器与 report/export gate，当前未生成报告文件。")
        return None

    def _toggle_diagnostics(self) -> None:
        self._diagnostic_frame.setVisible(not self._diagnostic_frame.isVisible())
        self._diagnostic_toggle_button.setText("收起开发者诊断" if self._diagnostic_frame.isVisible() else "展开开发者诊断")

    def save_asset_selection(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        selections: dict[str, str] = {}
        for row in range(self._selection_table.rowCount()):
            asset_type_item = self._selection_table.item(row, 0)
            combo = self._selection_table.cellWidget(row, 2)
            if asset_type_item is None or not isinstance(combo, QComboBox):
                continue
            selected = combo.currentData()
            if selected:
                selections[asset_type_item.text()] = str(selected)
        payload = save_standardized_asset_selection(self._project_root, selections)
        self.refresh_assets()
        self._status_label.setText(f"已保存默认资产选择：{len(payload.get('asset_selections', []) or [])} 类资产。")
        return payload

    def _render(self, artifacts: dict[str, object]) -> None:
        registry = artifacts.get("registry") or {}
        manifest = artifacts.get("analysis_ready_manifest") or {}
        assets = registry.get("assets", []) if isinstance(registry, dict) else []
        warnings = registry.get("warnings", []) if isinstance(registry, dict) else []
        selection_context = build_asset_selection_context(self._project_root) if self._project_root is not None else {"groups": []}
        selection_by_type = {
            str(group.get("asset_type") or ""): group
            for group in selection_context.get("groups", []) or []
            if isinstance(group, dict)
        }
        self._status_label.setText(f"标准化资产：{len(assets)} 个，warning {len(warnings)} 条。")
        if self._project_root is not None:
            self._current_input_summary.setPlainText(standardization_current_input_summary(self._project_root))
        _fill_table(
            self._assets,
            [
                [
                    item.get("asset_id", ""),
                    item.get("asset_type", ""),
                    item.get("source_file", ""),
                    item.get("sample_count", ""),
                    item.get("species", "") or item.get("species_group", ""),
                    _asset_usage_text(item),
                    _asset_limitations_text(item),
                    item.get("validation_status", ""),
                    _asset_default_text(item, selection_by_type),
                ]
                for item in assets
                if isinstance(item, dict)
            ],
        )
        self._render_selection_table(selection_context)
        summary_text = _standardization_user_summary(registry if isinstance(registry, dict) else {}, manifest if isinstance(manifest, dict) else {})
        if self._project_root is not None:
            summary_text = f"{summary_text}\n{_asset_selection_summary_text(selection_context)}\n{design_status_summary(self._project_root)}"
        self._summary.setPlainText(summary_text)
        self._manifest.setPlainText(_json({"analysis-ready manifest": manifest, "asset_selection": selection_context, "warning": warnings}))
        self._render_user_overview(artifacts)

    def _render_user_overview(self, artifacts: dict[str, object]) -> None:
        if self._project_root is None:
            return
        registry = artifacts.get("registry") if isinstance(artifacts.get("registry"), dict) else {}
        assets = [item for item in registry.get("assets", []) or [] if isinstance(item, dict)] if registry else []
        report = load_recognition_report(self._project_root) or {}
        files = [item for item in report.get("files", []) or [] if isinstance(item, dict)]
        assets_generated = bool(registry)
        group_confirmed = has_confirmed_group_comparison_design(self._project_root)
        self._status_label.setText(_standardization_status_message(assets, assets_generated))
        self._current_input_summary.setPlainText(_standardization_current_input_user_summary(self._project_root, report))
        self._input_detail.setPlainText(_standardization_input_detail_text(self._project_root, report))
        self._expression_status.setPlainText(_standardization_expression_user_summary(report, assets))
        self._group_status.setPlainText(_standardization_group_user_summary(self._project_root, report, assets))
        status_values = _standardization_status_values(report, assets, assets_generated, group_confirmed)
        for key, title_text, value_text in status_values:
            title, value = self._standardization_status_blocks[key]
            title.setText(title_text)
            value.setText(value_text)
        self._update_main_actions(assets_generated=assets_generated, group_confirmed=group_confirmed, has_expression=_standardization_has_expression_asset(files, assets))

    def _update_main_actions(self, *, assets_generated: bool, group_confirmed: bool, has_expression: bool) -> None:
        if group_confirmed:
            self._confirm_group_button.setText("编辑分组设计")
            _apply_button_semantics(self._confirm_group_button, "secondary")
        else:
            self._confirm_group_button.setText("确认分组与比较设计")
            _apply_button_semantics(self._confirm_group_button, "primary_action")
        self._confirm_group_button.setVisible(True)

        self._generate_assets_button.setText("重新生成标准化资产" if assets_generated else "生成标准化资产")
        _apply_button_semantics(self._generate_assets_button, "secondary" if (not group_confirmed or assets_generated) else "primary_action")
        self._generate_assets_button.setVisible(True)

        self._continue_tasks_button.setVisible(assets_generated and has_expression)
        self._continue_tasks_button.setEnabled(assets_generated and has_expression)
        _apply_button_semantics(self._continue_tasks_button, "primary_next")

        self._export_report_button.setVisible(True)
        self._export_report_button.setEnabled(False)
        self._refresh_assets_button.setVisible(True)

    def _render_selection_table(self, context: dict[str, object]) -> None:
        groups = [group for group in context.get("groups", []) or [] if isinstance(group, dict)]
        self._selection_table.clearContents()
        self._selection_table.setRowCount(len(groups))
        for row, group in enumerate(groups):
            self._selection_table.setItem(row, 0, QTableWidgetItem(str(group.get("asset_type") or "")))
            self._selection_table.setItem(row, 1, QTableWidgetItem(str(group.get("candidate_count") or 0)))
            combo = QComboBox()
            for asset in group.get("candidates", []) or []:
                if not isinstance(asset, dict):
                    continue
                asset_id = str(asset.get("asset_id") or "")
                source = Path(str(asset.get("source_file") or asset.get("file_path") or "")).name
                combo.addItem(f"{asset_id} · {source}", asset_id)
            selected_id = str(group.get("selected_asset_id") or "")
            if selected_id:
                index = combo.findData(selected_id)
                if index >= 0:
                    combo.setCurrentIndex(index)
            self._selection_table.setCellWidget(row, 2, combo)
            self._selection_table.setItem(row, 3, QTableWidgetItem(str(group.get("status_label") or selection_status_label(str(group.get("selection_state") or "")))))
            self._selection_table.setItem(row, 4, QTableWidgetItem(str(group.get("reason") or "")))
        self._selection_table.resizeColumnsToContents()


class BioinformaticsGroupComparisonDesignWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()

    def __init__(self, *, on_continue: Callable[[Path], None] | None = None, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self._context: dict[str, object] = {}
        self.setObjectName("bioinformaticsGroupComparisonDesignPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_design()

    def refresh_design(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        self._context = load_group_design_context(self._project_root)
        self._render(self._context)
        return self._context

    def add_comparison_row(
        self,
        comparison_name: str = "",
        case_group: str = "",
        control_group: str = "",
        *,
        source: str = "user_confirmed",
        status: str = "待保存",
    ) -> None:
        row = self._comparison_table.rowCount()
        self._comparison_table.insertRow(row)
        for column, value in enumerate([comparison_name, case_group, control_group, source, status]):
            self._comparison_table.setItem(row, column, QTableWidgetItem(str(value)))

    def add_one_vs_control_suggestions(self) -> None:
        groups = self._group_rows_from_table()
        suggestions = build_default_comparison_rows(self._context, groups)
        self._comparison_table.setRowCount(0)
        for item in suggestions:
            self.add_comparison_row(
                str(item.get("comparison_name") or ""),
                str(item.get("case_group") or ""),
                str(item.get("control_group") or ""),
                source=str(item.get("source") or "one_vs_control_suggestion"),
                status="待保存",
            )
        self._status_label.setText(f"已生成 {len(suggestions)} 个 one-vs-control 比较建议，请检查后保存。")

    def save_design(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        groups = self._group_rows_from_table()
        comparisons = self._comparison_rows_from_table()
        warnings = validate_group_comparison_design(groups, comparisons)
        payload = save_group_comparison_design(
            self._project_root,
            groups,
            comparisons,
            imported_deg_references=[
                item
                for item in self._context.get("imported_deg_references", []) or []
                if isinstance(item, dict)
            ],
        )
        load_analysis_task_center(self._project_root)
        self._context = load_group_design_context(self._project_root)
        self._status_label.setText(
            "已保存分组与比较设计。"
            if not warnings
            else "已保存分组与比较设计，但仍需检查：" + "；".join(warnings)
        )
        self._summary.setPlainText(_group_design_context_summary(self._context))
        return payload

    def continue_to_tasks(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        self.continue_requested.emit(self._project_root)

    def status_message(self) -> str:
        return self._status_label.text()

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("Group & Design / 分组与设计", "设计分组、比较和协变量草稿；preflight-ready 不等于正式分析。", back_text="返回数据检查", back_signal=self.back_requested))
        actions = QHBoxLayout()
        refresh_button = _button("刷新分组设计", "secondaryButton", self.refresh_design, role="secondary")
        suggestion_button = _button("从对照组生成比较", "secondaryButton", self.add_one_vs_control_suggestions, role="secondary")
        save_button = _button("保存分组与比较设计", "primaryButton", self.save_design, role="secondary")
        save_button.setProperty("formalActionEnabled", False)
        save_button.setToolTip("保存 design draft / comparison draft；不启动正式分析。")
        actions.addWidget(refresh_button)
        actions.addWidget(suggestion_button)
        actions.addWidget(save_button)
        actions.addStretch(1)
        root.addLayout(actions)
        self._status_label = _status_label("尚未读取分组设计。")
        root.addWidget(self._status_label)
        root.addWidget(self._build_group_design_gate_card())
        self._summary = _read_only_report_view(145)
        self._summary.setObjectName("groupDesignSummary")
        root.addWidget(self._summary)
        self._sample_group_table = _table(["推断组", "用户组名", "组角色", "样本数", "样本 ID", "备注"])
        self._sample_group_table.setObjectName("groupDesignSampleGroupsTable")
        root.addWidget(self._sample_group_table)
        self._comparison_table = _table(["比较名称", "实验组", "对照组", "来源", "状态"])
        self._comparison_table.setObjectName("groupDesignComparisonsTable")
        root.addWidget(self._comparison_table)
        self._imported_deg_table = _table(["已有比较", "状态", "可用路径"])
        self._imported_deg_table.setObjectName("groupDesignImportedDegTable")
        root.addWidget(self._imported_deg_table)
        self._technical = _text_preview(140)
        self._technical.setObjectName("groupDesignTechnical")
        self._technical.setVisible(False)
        root.addWidget(_button("展开技术详情", "secondaryButton", lambda: _toggle_details(self._technical)))
        root.addWidget(self._technical)
        continue_button = _button("继续：分析任务中心", "primaryButton", self.continue_to_tasks, role="secondary")
        continue_button.setProperty("formalActionEnabled", False)
        continue_button.setToolTip("进入 Analysis Tasks 的 gated 任务矩阵；不启动正式分析。")
        root.addWidget(continue_button, alignment=Qt.AlignLeft)

    def _build_group_design_gate_card(self) -> QFrame:
        card, layout = _card("Design Draft / 分组设计草稿")
        card.setObjectName("bioinformaticsGroupDesignGateCard")
        card.setProperty("formalActionEnabled", False)
        self._group_design_status_chip = _status_label("preflight-ready draft / 非正式分析")
        self._group_design_status_chip.setObjectName("bioinformaticsGroupDesignStatusChip")
        self._group_design_status_chip.setProperty("statusSemanticKey", "analysis.status.preflight_only")
        self._group_design_status_chip.setProperty("resultSemanticKey", "preflight_only")
        self._group_design_status_chip.setProperty("formalActionEnabled", False)
        layout.addWidget(self._group_design_status_chip)
        self._gated_group_setup_table = _table(["group", "role", "sample count", "state"])
        self._gated_group_setup_table.setObjectName("bioinformaticsGroupSetupGatedTable")
        layout.addWidget(self._gated_group_setup_table)
        self._gated_comparison_table = _table(["comparison", "case group", "control group", "state"])
        self._gated_comparison_table.setObjectName("bioinformaticsComparisonSetupGatedTable")
        layout.addWidget(self._gated_comparison_table)
        self._covariate_table = _table(["covariate", "include draft", "gate note"])
        self._covariate_table.setObjectName("bioinformaticsCovariateSettingsTable")
        layout.addWidget(self._covariate_table)
        self._design_summary = _read_only_report_view(90)
        self._design_summary.setObjectName("bioinformaticsDesignSummary")
        self._design_summary.setProperty("resultSemanticKey", "preflight_only")
        self._design_summary.setProperty("formalActionEnabled", False)
        layout.addWidget(self._design_summary)
        actions = QHBoxLayout()
        run_preflight = _button("Run Preflight - gated preview", "secondaryButton", lambda: None, role="secondary")
        run_preflight.setObjectName("bioinformaticsRunPreflightGatedButton")
        run_preflight.setEnabled(False)
        run_preflight.setProperty("buttonBehavior", "disabled_gated_preflight_preview")
        run_preflight.setProperty("formalActionEnabled", False)
        run_preflight.setToolTip("本阶段仅显示 preflight-ready 边界，不运行模型或正式分析。")
        actions.addWidget(run_preflight)
        actions.addStretch(1)
        layout.addLayout(actions)
        self._render_group_design_gate({}, [], [])
        return card

    def _render_group_design_gate(
        self,
        context: dict[str, object],
        groups: list[dict[str, object]],
        comparisons: list[dict[str, object]],
    ) -> None:
        counts = [int(item.get("sample_count") or 0) for item in groups[:2] if isinstance(item, dict)]
        tumor_count = counts[0] if counts else 0
        normal_count = counts[1] if len(counts) > 1 else 0
        _fill_table(
            self._gated_group_setup_table,
            [
                ["Tumor", "case", tumor_count, "design draft"],
                ["Normal", "control", normal_count, "design draft"],
                ["Optional unused group", "unused", 0, "optional / ignored unless user includes"],
            ],
        )
        if comparisons:
            comparison_rows = [
                [
                    str(item.get("comparison_name") or "Tumor_vs_Normal"),
                    str(item.get("case_group") or "Tumor"),
                    str(item.get("control_group") or "Normal"),
                    "design draft / not formal analysis",
                ]
                for item in comparisons[:4]
                if isinstance(item, dict)
            ]
        else:
            comparison_rows = [["Tumor_vs_Normal", "Tumor", "Normal", "design draft / not formal analysis"]]
        _fill_table(self._gated_comparison_table, comparison_rows)
        _fill_table(
            self._covariate_table,
            [
                ["Age", "draft only", "does not start Cox or clinical model"],
                ["Gender", "draft only", "does not start Cox or clinical model"],
                ["Smoking History", "draft only", "does not start Cox or clinical model"],
                ["Stage", "draft only", "does not start Cox or clinical model"],
            ],
        )
        self._design_summary.setPlainText(
            "\n".join(
                [
                    "Design summary: group and covariate choices are drafts for preflight eligibility.",
                    f"Confirmed design exists: {bool(context.get('has_confirmed_design'))}",
                    "ready_for_preflight does not create formal_computed_result.",
                    "Report / Export gate remains disabled until a future report-ready package exists.",
                ]
            )
        )

    def _render(self, context: dict[str, object]) -> None:
        groups = build_default_group_rows(context)
        comparisons = build_default_comparison_rows(context, groups)
        imported = [item for item in context.get("imported_deg_references", []) or [] if isinstance(item, dict)]
        warnings = [str(item) for item in context.get("warnings", []) or [] if str(item)]
        self._status_label.setText(
            "状态：已确认分组设计" if context.get("has_confirmed_design") else "状态：尚未确认分组设计"
        )
        self._render_group_design_gate(context, groups, comparisons)
        self._summary.setPlainText(_group_design_context_summary(context))
        _fill_table(
            self._sample_group_table,
            [
                [
                    item.get("inferred_group_id", ""),
                    item.get("user_group_name", ""),
                    item.get("group_role", "unknown"),
                    item.get("sample_count", ""),
                    _preview_list([str(value) for value in item.get("sample_ids", []) or []], limit=6, more_label="样本"),
                    item.get("note", ""),
                ]
                for item in groups
            ],
        )
        _fill_table(
            self._comparison_table,
            [
                [
                    item.get("comparison_name", ""),
                    item.get("case_group", ""),
                    item.get("control_group", ""),
                    item.get("source", "user_confirmed"),
                    "已确认" if item.get("status") == "confirmed" else "待保存",
                ]
                for item in comparisons
            ],
        )
        _fill_table(
            self._imported_deg_table,
            [
                [
                    item.get("comparison_name", ""),
                    "完整" if item.get("is_complete") else "不完整",
                    "可直接浏览、筛选、富集输入" if item.get("is_complete") else "可查看，部分筛选功能受限",
                ]
                for item in imported
            ],
        )
        self._technical.setPlainText(_json({"context": context, "warnings": warnings}))

    def _group_rows_from_table(self) -> list[dict[str, object]]:
        original = {
            str(item.get("inferred_group_id") or ""): item
            for item in self._context.get("sample_groups", []) or []
            if isinstance(item, dict)
        }
        rows: list[dict[str, object]] = []
        for row in range(self._sample_group_table.rowCount()):
            inferred = _table_text(self._sample_group_table, row, 0)
            source = original.get(inferred, {})
            rows.append(
                {
                    "inferred_group_id": inferred,
                    "user_group_name": _table_text(self._sample_group_table, row, 1) or inferred,
                    "group_role": _table_text(self._sample_group_table, row, 2) or "unknown",
                    "sample_count": int(source.get("sample_count") or _table_text(self._sample_group_table, row, 3) or 0),
                    "sample_ids": list(source.get("sample_ids", []) or []),
                    "source_columns": list(source.get("source_columns", []) or []),
                    "note": _table_text(self._sample_group_table, row, 5),
                }
            )
        return rows

    def _comparison_rows_from_table(self) -> list[dict[str, object]]:
        groups = {str(item.get("user_group_name") or ""): item for item in self._group_rows_from_table()}
        rows: list[dict[str, object]] = []
        for row in range(self._comparison_table.rowCount()):
            case = _table_text(self._comparison_table, row, 1)
            control = _table_text(self._comparison_table, row, 2)
            rows.append(
                {
                    "comparison_name": _table_text(self._comparison_table, row, 0),
                    "case_group": case,
                    "control_group": control,
                    "case_inferred_group_id": groups.get(case, {}).get("inferred_group_id", ""),
                    "control_inferred_group_id": groups.get(control, {}).get("inferred_group_id", ""),
                    "status": "confirmed",
                    "source": _table_text(self._comparison_table, row, 3) or "user_confirmed",
                }
            )
        return rows


class BioinformaticsWorkflowStatusWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()
    navigate_requested = Signal(str)

    def __init__(self, *, on_continue: Callable[[Path], None] | None = None, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self.setObjectName("bioinformaticsWorkflowStatusPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_status()

    def run_full_workflow(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        state = run_project_workflow(self._project_root)
        self._render(state)
        return state

    def run_single_stage(self, stage_key: str | None = None) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        key = stage_key or self._stage_input.text().strip() or "recognition"
        result = run_project_stage(self._project_root, key)
        self.refresh_status()
        return result

    def refresh_status(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        state = load_workflow_state(self._project_root) or default_workflow_state(self._project_root)
        if load_workflow_state(self._project_root) is None:
            self._status_label.setText("尚未生成 workflow state。")
        self._render(state)

    def continue_to_tasks(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        ok, reason = _can_continue_from_standardization(self._project_root)
        if not ok:
            self._status_label.setText(f"不能继续：{reason} 请返回数据来源补充文件。")
            return
        self.continue_requested.emit(self._project_root)

    def status_message(self) -> str:
        return self._status_label.text()

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("生信工作流总控", "Developer Preview / 本地测试版", back_text="返回项目首页", back_signal=self.back_requested))
        actions = QHBoxLayout()
        actions.addWidget(_button("运行完整流程", "primaryButton", self.run_full_workflow))
        actions.addWidget(_button("刷新状态", "secondaryButton", self.refresh_status))
        self._stage_input = QLineEdit()
        self._stage_input.setPlaceholderText("stage key，例如 recognition")
        actions.addWidget(self._stage_input)
        actions.addWidget(_button("运行单个步骤", "secondaryButton", self.run_single_stage))
        actions.addWidget(_button("打开 workflow report", "secondaryButton", lambda: _open_path(self._project_root / "logs/workflow/project_workflow_report.md" if self._project_root else None)))
        actions.addStretch(1)
        root.addLayout(actions)
        self._status_label = _status_label("尚未生成 workflow state。")
        root.addWidget(self._status_label)
        self._steps = _table(["步骤", "状态", "输入", "输出", "warning", "下一步建议"])
        root.addWidget(self._steps)
        root.addWidget(_button("继续：分析任务中心", "primaryButton", self.continue_to_tasks), alignment=Qt.AlignLeft)

    def _render(self, state: dict[str, object]) -> None:
        self._status_label.setText(
            f"当前阶段：{state.get('current_stage', '未知')} · Ready 状态：{state.get('ready_status', '尚未生成')} · Developer Preview / 本地测试版"
        )
        rows = []
        for item in state.get("steps", []) or []:
            if not isinstance(item, dict):
                continue
            rows.append(
                [
                    item.get("label", ""),
                    item.get("status_zh") or workflow_status_zh(str(item.get("status") or "")),
                    "、".join(str(value) for value in item.get("input", []) or []),
                    "、".join(str(value) for value in item.get("output", []) or []),
                    "、".join(str(value) for value in item.get("warnings", []) or []),
                    item.get("next_step", ""),
                ]
            )
        _fill_table(self._steps, rows)


class BioinformaticsAnalysisTaskCenterWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()
    group_design_requested = Signal(object)

    def __init__(self, *, on_continue: Callable[[Path], None] | None = None, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self.setObjectName("bioinformaticsAnalysisTaskCenterPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_task_center()

    def refresh_task_center(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            state = build_analysis_center_state(None)
            self._render_gate_preview(state)
            self._render_analysis_task_gate({}, state)
            return None
        center = load_analysis_task_center(self._project_root)
        self._render(center)
        return center

    def create_task(self, task_type: str | None = None) -> object | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        selected = task_type or self._task_type_input.text().strip() or "differential_expression"
        try:
            task = create_analysis_task(self._project_root, selected)
        except ValueError as exc:
            self._status_label.setText(str(exc))
            return None
        self._status_label.setText(f"已创建任务：{task.task_id} · {task.label} · {task.status}")
        self._records.setPlainText(_json({"任务记录": [task.__dict__ | {"record_path": str(task.record_path)}]}))
        return task

    def run_geo_differential_expression_task(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        expression_assets = _geo_expression_assets_for_analysis(self._project_root)
        if not expression_assets:
            self._status_label.setText("未找到可用于差异分析的表达矩阵。请先完成数据识别和标准化资产生成。")
            return None
        summaries: list[dict[str, object]] = []
        warnings: list[str] = []
        comparison_config = load_confirmed_comparison_config(self._project_root)
        explicit_assignments = confirmed_group_assignments(comparison_config)
        for asset in expression_assets:
            file_path = Path(str(asset.get("file_path") or "")).expanduser()
            if not file_path.is_absolute():
                file_path = self._project_root / file_path
            if not file_path.is_file() and asset.get("source_file"):
                source_path = Path(str(asset.get("source_file") or "")).expanduser()
                file_path = source_path if source_path.is_absolute() else self._project_root / source_path
            if not file_path.is_file():
                warnings.append(f"表达矩阵文件不存在：{file_path}")
                continue
            dataset_id = _analysis_dataset_id(asset, file_path)
            output_dir = self._project_root / "analysis" / "geo" / "differential_expression" / dataset_id
            try:
                summary = run_geo_differential_expression(
                    file_path,
                    output_dir=output_dir,
                    dataset_id=dataset_id,
                    group_assignments=explicit_assignments or None,
                    case_label=comparison_config.case_group if comparison_config is not None else "case",
                    control_label=comparison_config.control_group if comparison_config is not None else "control",
                )
            except Exception as exc:
                warnings.append(f"{dataset_id}: {exc}")
                continue
            summaries.append(summary)
        if summaries:
            _append_geo_deg_results_to_index(self._project_root, summaries)
            load_analysis_task_center(self._project_root)
            comparison_message = f"；{comparison_summary_text(comparison_config)}" if comparison_config is not None else ""
            self._status_label.setText(f"已运行 GEO 差异分析：{len(summaries)} 个表达矩阵{comparison_message}")
            self._records.setPlainText(_json({"差异分析结果": summaries, "warnings": warnings, "comparison_config": comparison_config.to_dict() if comparison_config is not None else {}}))
            return {"summaries": summaries, "warnings": warnings}
        if comparison_config is not None:
            self._status_label.setText("差异分析未运行：已确认比较组，但表达矩阵样本 ID 未能匹配。请修正比较组或选择其他表达文件。")
        else:
            self._status_label.setText("差异分析未运行：尚未确认比较组。请先点击“设置比较组”。")
        self._records.setPlainText(_json({"warnings": warnings}))
        return {"summaries": [], "warnings": warnings}

    def configure_comparison_groups(self, manual_text: str | None = None) -> bool:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return False
        text = manual_text
        if text is None:
            text, ok = QInputDialog.getMultiLineText(
                self,
                "设置比较组",
                "请按 TSV 格式输入比较组；group_column 应对应样本信息中的分组列。",
                _template_text_for_missing_input("comparison_config"),
            )
            if not ok:
                return False
        _save_manual_supplement(self._project_root, "comparison_config", text or _template_text_for_missing_input("comparison_config"))
        run_project_recognition(self._project_root)
        run_project_readiness(self._project_root)
        self.refresh_task_center()
        self._status_label.setText("已保存比较组设置，并重新检查分析任务。")
        return True

    def configure_deg_task_plan(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        try:
            payload = save_deg_task_plan(self._project_root)
        except ValueError as exc:
            self._status_label.setText(str(exc))
            return None
        center = load_analysis_task_center(self._project_root)
        self._render(center)
        self._status_label.setText(f"已创建 DEG task plan：{len(payload.get('comparisons', []) or [])} 个比较；未执行真实 DEG。")
        self._records.setPlainText(_json({"DEG task plan": payload}))
        return payload

    def create_deg_task_run_record(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        try:
            payload = create_deg_task_run(self._project_root)
        except ValueError as exc:
            self._status_label.setText(str(exc))
            return None
        center = load_analysis_task_center(self._project_root)
        self._render(center)
        self._status_label.setText(f"已生成 DEG 任务记录：{payload.get('run_id')}；当前版本尚未执行真实差异分析。")
        self._records.setPlainText(_json({"DEG task run": payload}))
        return payload

    def generate_deg_executor_preflight(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        task_run_id = ""
        row = self._task_runs.currentRow()
        runs = list_analysis_task_runs(self._project_root, task_family="deg")
        if 0 <= row < len(runs):
            task_run_id = str(runs[row].get("run_id") or "")
        payload = run_deg_executor_preflight(self._project_root, task_run_id=task_run_id or None)
        center = load_analysis_task_center(self._project_root)
        self._render(center)
        status = str(payload.get("status") or "")
        status_text = {
            "passed": "DEG 输入校验：通过",
            "passed_with_warnings": "DEG 输入校验：通过，但有提示",
            "failed": "DEG 输入校验：未通过，请查看错误",
        }.get(status, f"DEG 输入校验：{status}")
        self._status_label.setText(f"{status_text}；当前版本尚未执行真实差异分析。")
        self._records.setPlainText(_json({"DEG executor preflight": payload}))
        return payload

    def show_selected_task_run_detail(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        row = self._task_runs.currentRow()
        runs = list_analysis_task_runs(self._project_root)
        if row < 0 or row >= len(runs):
            self._status_label.setText("请选择一条任务历史记录。")
            return None
        run = runs[row]
        self._records.setPlainText(_json({"任务运行详情": run}))
        self._status_label.setText(f"任务详情：{run.get('run_id')} · {task_run_status_label(str(run.get('status') or ''))}")
        return run

    def continue_to_results(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        records = load_task_records(self._project_root)
        if not records:
            self._status_label.setText("不能继续：尚未创建可运行任务。请返回数据来源补充文件，或先创建可运行分析任务。")
            return
        self.continue_requested.emit(self._project_root)

    def status_message(self) -> str:
        return self._status_label.text()

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("Analysis Tasks / 分析任务", "任务 gate matrix 与 DEG preflight review；不运行正式分析。", back_text="返回 Group & Design", back_signal=self.back_requested))
        self._status_label = _status_label("没有 task center 时请先运行工作流或生成任务中心。")
        root.addWidget(self._status_label)
        root.addWidget(self._build_analysis_task_gate_card())
        actions = QHBoxLayout()
        actions.addWidget(_button("刷新任务中心", "secondaryButton", self.refresh_task_center, role="secondary"))
        self._task_type_input = QLineEdit()
        self._task_type_input.setPlaceholderText("task type，例如 differential_expression")
        actions.addWidget(self._task_type_input)
        actions.addWidget(_button("去确认分组", "secondaryButton", self.open_group_design, role="secondary"))
        actions.addWidget(_button("设置比较组", "secondaryButton", self.configure_comparison_groups, role="secondary"))
        deg_plan_button = _button("配置 DEG 任务", "primaryButton", self.configure_deg_task_plan, role="secondary")
        deg_run_record_button = _button("生成 DEG 分析任务记录", "primaryButton", self.create_deg_task_run_record, role="secondary")
        deg_preflight_button = _button("生成并校验 DEG 输入", "primaryButton", self.generate_deg_executor_preflight, role="secondary")
        create_task_button = _button("创建任务", "primaryButton", self.create_task, role="secondary")
        for button, behavior in (
            (deg_plan_button, "disabled_task_plan_preview"),
            (deg_run_record_button, "disabled_task_record_preview"),
            (deg_preflight_button, "disabled_preflight_preview"),
            (create_task_button, "disabled_task_creation_preview"),
        ):
            button.setEnabled(False)
            button.setProperty("formalActionEnabled", False)
            button.setProperty("buttonBehavior", behavior)
            button.setToolTip("UI-C2e 普通页面只显示 gate/review；直接写入任务或 preflight artifact 仅保留给内部诊断方法。")
            actions.addWidget(button)
        self._geo_deg_button = _button("运行 GEO 差异分析 - 开发诊断禁用", "secondaryButton", self.run_geo_differential_expression_task)
        self._geo_deg_button.setObjectName("bioinformaticsFormalDegDisabledButton")
        self._geo_deg_button.setProperty("actionId", "developer_geo_deg_runner")
        self._geo_deg_button.setProperty("formalActionEnabled", False)
        self._geo_deg_button.setProperty("gateState", "developer_diagnostics_only")
        self._geo_deg_button.setToolTip("UI-C2b 不在普通工作流启用 GEO 差异分析 runner；如需验证旧 runner，应走单独开发诊断。")
        self._geo_deg_button.setEnabled(False)
        actions.addWidget(self._geo_deg_button)
        actions.addStretch(1)
        root.addLayout(actions)
        self._gate_actions = _table(["action_id", "state", "enabled", "button_behavior", "disabled_reason", "next_action"])
        self._gate_actions.setObjectName("bioinformaticsActionGateMatrix")
        root.addWidget(self._gate_actions)
        self._capability_summary = _read_only_report_view(150)
        self._capability_summary.setObjectName("analysisCapabilityGroupedSummary")
        root.addWidget(self._capability_summary)
        self._tasks = _table(["任务", "是否可运行", "来源与状态", "已有输入", "缺失输入", "warning", "默认参数", "preview"])
        root.addWidget(self._tasks)
        root.addWidget(_muted("任务历史记录"))
        self._task_runs = _table(["时间", "任务类型", "run id", "输入资产", "比较数量", "状态", "操作"])
        self._task_runs.setObjectName("analysisTaskRunHistoryTable")
        root.addWidget(self._task_runs)
        root.addWidget(_button("查看任务记录详情", "secondaryButton", self.show_selected_task_run_detail), alignment=Qt.AlignLeft)
        self._records = _text_preview(120)
        root.addWidget(self._records)
        root.addWidget(_button("继续：结果浏览", "primaryButton", self.continue_to_results), alignment=Qt.AlignLeft)

    def _build_analysis_task_gate_card(self) -> QFrame:
        card, layout = _card("Task Gate Matrix / 任务门控矩阵")
        card.setObjectName("bioinformaticsAnalysisTaskGateCard")
        card.setProperty("formalActionEnabled", False)
        self._analysis_task_matrix = _table(["task", "status", "dependency", "allowed action", "blocked action"])
        self._analysis_task_matrix.setObjectName("bioinformaticsAnalysisTaskGatedMatrix")
        self._analysis_task_matrix.setProperty("formalActionEnabled", False)
        layout.addWidget(self._analysis_task_matrix)
        deg_title = _muted("DEG Parameter Review / DEG 参数复核")
        deg_title.setObjectName("bioinformaticsDegParameterReviewTitle")
        layout.addWidget(deg_title)
        self._deg_parameter_table = _table(["parameter", "current review value", "gate note"])
        self._deg_parameter_table.setObjectName("bioinformaticsDegParameterReviewTable")
        self._deg_parameter_table.setProperty("resultSemanticKey", "preflight_only")
        self._deg_parameter_table.setProperty("formalActionEnabled", False)
        layout.addWidget(self._deg_parameter_table)
        self._deg_preflight_checklist = _table(["check", "state", "meaning"])
        self._deg_preflight_checklist.setObjectName("bioinformaticsDegPreflightChecklist")
        self._deg_preflight_checklist.setProperty("resultSemanticKey", "preflight_only")
        self._deg_preflight_checklist.setProperty("formalActionEnabled", False)
        layout.addWidget(self._deg_preflight_checklist)
        action_row = QHBoxLayout()
        action_specs = (
            ("Run Preflight - gated preview", "bioinformaticsRunPreflightReviewDisabledButton", "disabled_preflight_preview"),
            ("Run Formal DEG - disabled", "bioinformaticsRunFormalDegDisabledButton", "disabled_formal_executor"),
            ("Generate Plot - disabled", "bioinformaticsGeneratePlotDisabledButton", "disabled_no_result"),
            ("Add to Report - disabled", "bioinformaticsAnalysisAddToReportDisabledButton", "disabled_report_draft"),
            ("Export Result - disabled", "bioinformaticsAnalysisExportResultDisabledButton", "disabled_export_gate"),
        )
        for text, object_name, behavior in action_specs:
            button = _button(text, "secondaryButton", lambda: None, role="secondary")
            button.setObjectName(object_name)
            button.setEnabled(False)
            button.setProperty("formalActionEnabled", False)
            button.setProperty("buttonBehavior", behavior)
            button.setProperty("resultSemanticKey", "preflight_only")
            button.setProperty("exportGate", "disabled_missing_report_ready")
            action_row.addWidget(button)
        action_row.addStretch(1)
        layout.addLayout(action_row)
        self._analysis_task_gate_summary = _read_only_report_view(86)
        self._analysis_task_gate_summary.setObjectName("bioinformaticsAnalysisTaskGateSummary")
        self._analysis_task_gate_summary.setProperty("formalActionEnabled", False)
        self._analysis_task_gate_summary.setProperty("resultSemanticKey", "preflight_only")
        layout.addWidget(self._analysis_task_gate_summary)
        self._render_analysis_task_gate({}, build_analysis_center_state(None))
        return card

    def open_group_design(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        self.group_design_requested.emit(self._project_root)

    def _render(self, center: dict[str, object]) -> None:
        state = build_analysis_center_state(self._project_root)
        self._render_gate_preview(state)
        self._render_analysis_task_gate(center, state)
        tasks = [item for item in center.get("tasks", []) or [] if isinstance(item, dict)]
        self._status_label.setText(f"分析任务中心：{len(tasks)} 个任务模板。不可运行任务将显示缺失输入。")
        self._capability_summary.setPlainText(_analysis_task_group_summary(center))
        _fill_table(
            self._tasks,
            [
                [
                    item.get("label", ""),
                    "可运行" if item.get("can_run") else "不可运行",
                    _task_source_status_text(item),
                    "、".join(str(v) for v in item.get("available_inputs", []) or []),
                    "、".join(str(v) for v in item.get("missing_inputs", []) or []),
                    "、".join(str(v) for v in item.get("warnings", []) or []),
                    _json(item.get("default_parameters", {})),
                    item.get("preview_status", ""),
                ]
                for item in tasks
            ],
        )
        runs = [item for item in center.get("task_runs", []) or [] if isinstance(item, dict)]
        _fill_table(self._task_runs, [_analysis_task_run_row(item) for item in runs])
        self._records.setPlainText(_json({"已创建任务": load_task_records(self._project_root) if self._project_root else [], "任务运行记录": runs}))

    def _render_gate_preview(self, state: dict[str, object]) -> None:
        rows = [item for item in state.get("action_rows", []) or [] if isinstance(item, dict)]
        _fill_table(
            self._gate_actions,
            [
                [
                    item.get("action_id", ""),
                    label_status(str(item.get("state") or "")),
                    "enabled" if item.get("enabled") else "disabled",
                    item.get("button_behavior", ""),
                    item.get("disabled_reason", ""),
                    item.get("next_action", ""),
                ]
                for item in rows
            ],
        )
        for row_index, item in enumerate(rows):
            if bool(item.get("formal_action")):
                for column in range(self._gate_actions.columnCount()):
                    cell = self._gate_actions.item(row_index, column)
                    if cell is not None:
                        cell.setData(Qt.UserRole, {"formalActionEnabled": False, "actionId": item.get("action_id")})
        self._gate_actions.setProperty("formalActionEnabled", False)
        self._gate_actions.setProperty("schemaVersion", state.get("schema_version", ""))

    def _render_analysis_task_gate(self, center: dict[str, object], state: dict[str, object]) -> None:
        actions = {
            str(item.get("action_id") or ""): item
            for item in state.get("action_rows", []) or []
            if isinstance(item, dict)
        }
        formal_deg_state = actions.get("formal_deg", {})
        deg_preflight_state = actions.get("deg_preflight", {})
        _fill_table(
            self._analysis_task_matrix,
            [
                ["DEG", "preflight / parameter review", "expression matrix + group design", "review checklist only", "formal DEG executor"],
                ["ORA", "planned / disabled", "requires DEG result", "none", "ORA executor"],
                ["GSEA", "planned / disabled", "requires DEG result + GMT", "none", "GSEA executor"],
                ["KM / log-rank", "planned / disabled", "requires survival audit", "none", "KM/log-rank executor"],
                ["Cox", "planned / disabled", "requires clinical/survival audit", "none", "Cox executor"],
                ["Clinical Association", "audit required / disabled", "requires clinical variable audit", "none", "clinical association executor"],
            ],
        )
        comparison = self._deg_review_comparison_label()
        matrix_state = "registered / preflight-ready" if deg_preflight_state.get("enabled") else "registered / gated"
        _fill_table(
            self._deg_parameter_table,
            [
                ["comparison", comparison, "design draft; not formal run"],
                ["input matrix state", matrix_state, "dependency snapshot preview only"],
                ["method policy", "Welch preview; planned DESeq2 / limma policy", "planned executor, not enabled"],
                ["FDR threshold", "0.05", "parameter review only"],
                ["log2FC threshold", "1.0", "parameter review only"],
                ["low-expression filter", "planned filter: CPM/count threshold", "not executed"],
                ["normalization", "review required", "no normalization is run here"],
                ["missing value handling", "review required", "no imputation is run here"],
                ["batch handling", "review required", "no batch correction is run here"],
                ["dependency snapshot", str(formal_deg_state.get("disabled_reason") or "formal action disabled"), "does not prove executor readiness"],
            ],
        )
        checklist_rows = [
            ["input matrix exists", "passed" if deg_preflight_state.get("enabled") else "blocked", "preflight only"],
            ["sample metadata complete", "passed" if deg_preflight_state.get("enabled") else "blocked", "preflight only"],
            ["group design valid", "passed" if deg_preflight_state.get("enabled") else "blocked", "preflight only"],
            ["comparison valid", "passed" if deg_preflight_state.get("enabled") else "warning", "preflight only"],
            ["sample name matching", "passed / warning", "manual review remains required"],
            ["minimal group size", "warning", "does not block review page"],
            ["dependency status", "disabled formal executor", "formal DEG not enabled"],
            ["output plan / result schema", "not generated", "no formal result artifact"],
        ]
        _fill_table(self._deg_preflight_checklist, checklist_rows)
        self._analysis_task_gate_summary.setPlainText(
            "\n".join(
                [
                    "Analysis Tasks gate summary: all formal run actions remain disabled.",
                    "Preflight passed/warning states are not formal_computed_result.",
                    "No DEG result table, volcano plot, heatmap, enrichment plot, survival plot, report, or export is generated.",
                ]
            )
        )

    def _deg_review_comparison_label(self) -> str:
        if self._project_root is None:
            return "Tumor_vs_Normal"
        context = load_group_design_context(self._project_root)
        groups = build_default_group_rows(context)
        comparisons = build_default_comparison_rows(context, groups)
        if comparisons:
            return str(comparisons[0].get("comparison_name") or "Tumor_vs_Normal")
        return "Tumor_vs_Normal"


class BioinformaticsResultsBrowserWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()

    def __init__(self, *, on_continue: Callable[[Path], None] | None = None, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self.setObjectName("bioinformaticsResultsBrowserPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_results()

    def refresh_results(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            self._render_result_gate_preview(build_analysis_center_state(None))
            return None
        payload = load_result_index(self._project_root)
        self._render(payload)
        return payload

    def continue_to_report(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        payload = load_result_index(self._project_root)
        entries = [item for item in payload.get("entries", []) or [] if isinstance(item, dict)]
        if not entries:
            self._status_label.setText("不能继续：暂无可用于报告的结果。请返回数据来源补充文件，完成分析并生成结果后再进入报告。")
            return
        self.continue_requested.emit(self._project_root)

    def status_message(self) -> str:
        return self._status_label.text()

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("结果浏览", "Developer Preview / 本地测试版", back_text="返回分析任务中心", back_signal=self.back_requested))
        self._status_label = _status_label("暂无结果，请先在分析任务中心创建并运行分析任务。")
        root.addWidget(self._status_label)
        actions = QHBoxLayout()
        actions.addWidget(_button("刷新结果", "secondaryButton", self.refresh_results))
        actions.addWidget(_button("打开结果文件夹", "secondaryButton", lambda: _open_path(self._project_root / "results" if self._project_root else None)))
        actions.addWidget(_button("打开参数 JSON", "secondaryButton", lambda: _open_path(self._project_root / "manifests/result_manager.json" if self._project_root else None)))
        self._add_to_report_button = _button("加入报告 - disabled", "secondaryButton", lambda: self._status_label.setText("加入报告：UI-C2b 禁用。"))
        self._add_to_report_button.setObjectName("bioinformaticsAddToReportDisabledButton")
        self._add_to_report_button.setProperty("formalActionEnabled", False)
        self._add_to_report_button.setProperty("reportStatusKey", "report.status.draft")
        self._add_to_report_button.setToolTip("UI-C2b 只显示 result/report gate preview，不生成或追加正式报告内容。")
        self._add_to_report_button.setEnabled(False)
        actions.addWidget(self._add_to_report_button)
        actions.addStretch(1)
        root.addLayout(actions)
        self._result_gate_preview = _read_only_report_view(96)
        self._result_gate_preview.setObjectName("bioinformaticsResultGatePreview")
        root.addWidget(self._result_gate_preview)
        comparison_row = QHBoxLayout()
        comparison_row.addWidget(_muted("已有 DEG 比较："))
        self._imported_deg_selector = QComboBox()
        self._imported_deg_selector.setObjectName("importedDegComparisonSelector")
        self._imported_deg_selector.currentIndexChanged.connect(self._render_selected_imported_deg)
        comparison_row.addWidget(self._imported_deg_selector)
        comparison_row.addStretch(1)
        root.addLayout(comparison_row)
        self._imported_deg_summary = _read_only_report_view(120)
        self._imported_deg_summary.setObjectName("importedDegSummary")
        root.addWidget(self._imported_deg_summary)
        self._results = _table(["结果名称", "分析类型", "文件类型", "创建时间", "路径", "状态", "warning"])
        root.addWidget(self._results)
        self._deg_preview = _table(["gene_id", "gene_name", "log2FC", "p value", "adjusted p value", "gene_biotype", "gene_description"])
        self._deg_preview.setObjectName("importedDegPreviewTable")
        root.addWidget(self._deg_preview)
        self._details = _text_preview(130)
        root.addWidget(self._details)
        root.addWidget(_button("继续：报告查看", "primaryButton", self.continue_to_report), alignment=Qt.AlignLeft)

    def _render(self, payload: dict[str, object]) -> None:
        self._render_result_gate_preview(build_analysis_center_state(self._project_root))
        entries = [item for item in payload.get("entries", []) or [] if isinstance(item, dict)]
        warnings = [str(item) for item in payload.get("warnings", []) or []]
        if not entries:
            self._status_label.setText("暂无结果，请先在分析任务中心创建并运行分析任务。")
        else:
            self._status_label.setText(f"已读取结果索引：{len(entries)} 个结果，{len(warnings)} 条 warning。")
        _fill_table(
            self._results,
            [
                [
                    item.get("result_name") or item.get("name", "未命名结果"),
                    item.get("analysis_type", "未知"),
                    item.get("file_type", "未知"),
                    item.get("created_at", "未记录"),
                    item.get("path") or item.get("file_path", ""),
                    item.get("status", "未知"),
                    item.get("warning", ""),
                ]
                for item in entries
            ],
        )
        self._details.setPlainText(_json({"结果详情": entries[:1], "warnings": warnings}))
        self._render_imported_deg_selector()

    def _render_result_gate_preview(self, state: dict[str, object]) -> None:
        result_gate = state.get("result_gate", {}) if isinstance(state.get("result_gate"), dict) else {}
        report_gate = state.get("report_gate", {}) if isinstance(state.get("report_gate"), dict) else {}
        export_gate = state.get("export_gate", {}) if isinstance(state.get("export_gate"), dict) else {}
        self._result_gate_preview.setPlainText(
            _json(
                {
                    "result_gate": result_gate,
                    "report_gate": report_gate,
                    "export_gate": export_gate,
                    "boundary": "read_only_gate_preview_no_fake_result_no_fake_plot_no_report_ready_package",
                }
            )
        )
        self._result_gate_preview.setProperty("resultSemanticKey", result_gate.get("result_semantic_key", "result.semantic.testing_summary_only"))
        self._result_gate_preview.setProperty("reportStatusKey", report_gate.get("report_status_key", "report.status.draft"))
        self._result_gate_preview.setProperty("exportGate", export_gate.get("export_gate", "disabled_missing_report_ready"))
        self._result_gate_preview.setProperty("formalActionEnabled", False)

    def _render_imported_deg_selector(self) -> None:
        self._imported_deg_selector.blockSignals(True)
        self._imported_deg_selector.clear()
        comparisons = load_imported_deg_comparisons(self._project_root) if self._project_root is not None else []
        for item in comparisons:
            label = str(item.get("comparison_name") or "未命名比较")
            source = str(item.get("source_file_name") or Path(str(item.get("source_file") or "")).name)
            self._imported_deg_selector.addItem(f"{label} · {source}", item)
        first_complete = next((index for index, item in enumerate(comparisons) if item.get("is_complete")), 0)
        if comparisons:
            self._imported_deg_selector.setCurrentIndex(first_complete)
        self._imported_deg_selector.blockSignals(False)
        self._render_selected_imported_deg()

    def _render_selected_imported_deg(self) -> None:
        if self._project_root is None or self._imported_deg_selector.count() == 0:
            self._deg_preview.setRowCount(0)
            if self._project_root is None:
                self._imported_deg_summary.setPlainText("")
            else:
                view = build_imported_deg_view(self._project_root)
                warnings = [str(item) for item in view.get("warnings", []) or [] if str(item)]
                self._imported_deg_summary.setPlainText("；".join(warnings) if warnings else "")
            return
        item = self._imported_deg_selector.currentData()
        if not isinstance(item, dict):
            return
        view = build_imported_deg_view(
            self._project_root,
            source_asset_id=str(item.get("source_asset_id") or ""),
            comparison_name=str(item.get("comparison_name") or ""),
        )
        rows = [row for row in view.get("rows", []) or [] if isinstance(row, dict)]
        _fill_table(
            self._deg_preview,
            [
                [
                    row.get("gene_id", ""),
                    row.get("gene_name", ""),
                    row.get("log2FC", ""),
                    row.get("p value", ""),
                    row.get("adjusted p value", ""),
                    row.get("gene_biotype", ""),
                    row.get("gene_description", ""),
                ]
                for row in rows[:100]
            ],
        )
        self._imported_deg_summary.setPlainText(_imported_deg_user_summary(view, comparison_count=self._imported_deg_selector.count()))
        self._details.setPlainText(_json({"imported_deg_view": {key: value for key, value in view.items() if key != "rows"}, "preview_row_count": min(len(rows), 100)}))


class BioinformaticsReportViewerWidget(QWidget):
    back_requested = Signal()

    def __init__(self, *, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self.setObjectName("bioinformaticsReportViewerPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_back is not None:
            self.back_requested.connect(on_back)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_report()

    def generate_report(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        payload = generate_project_report(self._project_root)
        self._render(payload)
        return payload

    def refresh_report(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            self._render_export_gate_preview(build_analysis_center_state(None))
            return None
        payload = load_project_report(self._project_root)
        self._render(payload)
        return payload

    def status_message(self) -> str:
        return self._status_label.text()

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("项目报告", "Developer Preview / 本地测试版", back_text="返回结果浏览", back_signal=self.back_requested))
        actions = QHBoxLayout()
        self._generate_report_button = _button("生成 / 刷新项目报告 - disabled", "secondaryButton", self.generate_report)
        self._generate_report_button.setObjectName("bioinformaticsGenerateReportDisabledButton")
        self._generate_report_button.setProperty("formalActionEnabled", False)
        self._generate_report_button.setProperty("reportReadyPackageAllowed", False)
        self._generate_report_button.setProperty("gateState", "disabled_missing_report_ready")
        self._generate_report_button.setToolTip("UI-C2b 只显示报告草稿边界，不生成正式报告或 report-ready package。")
        self._generate_report_button.setEnabled(False)
        actions.addWidget(self._generate_report_button)
        actions.addWidget(_button("打开报告文件", "secondaryButton", lambda: _open_path(self._project_root / "reports/project_analysis_report.md" if self._project_root else None)))
        actions.addWidget(_button("打开报告文件夹", "secondaryButton", lambda: _open_path(self._project_root / "reports" if self._project_root else None)))
        self._docx_export_button = _button("导出 DOCX - disabled", "secondaryButton", lambda: self._status_label.setText("DOCX 导出：UI-C2b 禁用。"))
        self._html_export_button = _button("导出 HTML - disabled", "secondaryButton", lambda: self._status_label.setText("HTML 导出：UI-C2b 禁用。"))
        for button, fmt in ((self._docx_export_button, "export.format.docx"), (self._html_export_button, "export.format.html")):
            button.setObjectName("bioinformaticsReportExportDisabledButton")
            button.setProperty("exportFormatKey", fmt)
            button.setProperty("exportGate", "disabled_missing_report_ready")
            button.setProperty("reportStatusKey", "report.status.draft")
            button.setProperty("formalActionEnabled", False)
            button.setProperty("reportReadyPackageAllowed", False)
            button.setToolTip("Export requires report-ready gate and file picker; disabled in UI-C2b.")
            button.setEnabled(False)
            actions.addWidget(button)
        actions.addStretch(1)
        root.addLayout(actions)
        self._status_label = _status_label("报告草稿与导出 gate preview；正式报告生成和导出在 UI-C2b 禁用。")
        root.addWidget(self._status_label)
        self._export_gate_preview = _read_only_report_view(110)
        self._export_gate_preview.setObjectName("bioinformaticsReportExportGatePreview")
        root.addWidget(self._export_gate_preview)
        root.addWidget(_muted("可纳入报告的内容"))
        self._reportable_content = _read_only_report_view(100)
        self._reportable_content.setObjectName("reportableContentSummary")
        root.addWidget(self._reportable_content)
        self._markdown = _text_preview(320)
        root.addWidget(self._markdown)
        self._manifest = _text_preview(140)
        root.addWidget(self._manifest)

    def _render(self, payload: dict[str, object]) -> None:
        self._render_export_gate_preview(build_analysis_center_state(self._project_root))
        markdown = str(payload.get("markdown") or "")
        manifest = payload.get("manifest")
        if self._project_root is not None:
            self._reportable_content.setPlainText(_reportable_content_summary(load_result_index(self._project_root)))
        if not markdown:
            self._status_label.setText("尚未生成项目报告。PDF 当前未正式支持。")
            self._markdown.setPlainText("")
        else:
            self._status_label.setText("已读取项目级 Markdown 报告。PDF 当前只能显示 placeholder，未正式支持。")
            self._markdown.setPlainText(markdown)
        self._manifest.setPlainText(_json(manifest or {"PDF": "未正式支持", "DOCX": "testing placeholder"}))

    def _render_export_gate_preview(self, state: dict[str, object]) -> None:
        export_gate = state.get("export_gate", {}) if isinstance(state.get("export_gate"), dict) else {}
        report_gate = state.get("report_gate", {}) if isinstance(state.get("report_gate"), dict) else {}
        self._export_gate_preview.setPlainText(
            _json(
                {
                    "report_gate": report_gate,
                    "export_gate": export_gate,
                    "disabled_actions": ["report_ready_package", "export_package", "export_pdf", "export_docx", "export_html"],
                    "boundary": "draft_preview_only_no_report_ready_package_no_export",
                }
            )
        )
        self._export_gate_preview.setProperty("exportGate", export_gate.get("export_gate", "disabled_missing_report_ready"))
        self._export_gate_preview.setProperty("reportStatusKey", export_gate.get("report_status_key", "report.status.draft"))
        self._export_gate_preview.setProperty("formalActionEnabled", False)
        self._export_gate_preview.setProperty("reportReadyPackageAllowed", False)


class BioinformaticsSettingsAndLocalAIWidget(QWidget):
    back_requested = Signal()

    def __init__(self, *, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("bioinformaticsSettingsLocalAIPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_back is not None:
            self.back_requested.connect(on_back)

    def generate_placeholder_terms(self) -> str:
        text = self._question_input.text().strip()
        if not text:
            self._preview.setPlainText("请输入中文研究问题。")
            return ""
        result = BioinformaticsSourceRouter().search(text, online_enabled=False, limit=20)
        terms = _query_draft_output_text(result)
        self._preview.setPlainText(terms)
        return terms

    def save_local_ai_settings(self) -> str:
        enabled = self._local_ai_enabled.isChecked()
        config = desktop_local_ollama_config(
            enabled=enabled,
            base_url=self._ollama_base_url_input.text().strip() or DEFAULT_OLLAMA_BASE_URL,
            default_model=self._ollama_model_input.text().strip() or DEFAULT_OLLAMA_MODEL,
            timeout_seconds=20,
        )
        save_ai_gateway_config(config)
        self._refresh_ai_status(config)
        message = "本地 AI 已启用，仅允许本机 Ollama，经 AI Gateway 调用。" if enabled else "本地 AI 已关闭，已恢复安全默认配置。"
        self._ai_status.setText(message)
        return message

    def test_local_ai_connection(self) -> str:
        config = desktop_local_ollama_config(
            enabled=self._local_ai_enabled.isChecked(),
            base_url=self._ollama_base_url_input.text().strip() or DEFAULT_OLLAMA_BASE_URL,
            default_model=self._ollama_model_input.text().strip() or DEFAULT_OLLAMA_MODEL,
            timeout_seconds=20,
        )
        provider = OllamaProvider.from_provider_config(config.provider_configs.get("ollama", {}))
        status = provider.detect_ollama_status()
        label = _ai_provider_status_label(status)
        self._connection_status.setText(f"连接状态：{label}")
        self._refresh_ai_status(config, detected_status=status)
        return status.value

    def run_geo_legacy_environment_check(self) -> str:
        result = run_geo_environment_check()
        lines = [
            "GEO legacy 环境检查",
            f"命令：{' '.join(geo_check_command())}",
            f"退出码：{result.returncode}",
        ]
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if stdout:
            lines.extend(["stdout:", stdout[-2400:]])
        if stderr:
            lines.extend(["stderr:", stderr[-1600:]])
        if result.returncode == 0:
            lines.append("状态：可用。该检查只验证 legacy GEO 工具环境，不下载数据。")
        else:
            lines.append("状态：未通过。请根据错误信息检查依赖或本地环境。")
        text = "\n".join(lines)
        self._geo_check_preview.setPlainText(text)
        self._geo_check_status.setText("GEO legacy 环境检查已完成。" if result.returncode == 0 else "GEO legacy 环境检查未通过。")
        return text

    def status_message(self) -> str:
        return self._ai_status.text()

    def _refresh_ai_status(self, config: object | None = None, *, detected_status: AIProviderStatus | None = None) -> None:
        config = config or load_ai_gateway_config()
        if not getattr(config, "allow_network", False) or getattr(config, "default_provider", "disabled") != "ollama":
            self._ai_mode.setText("当前 AI 模式：关闭")
            self._connection_status.setText("连接状态：未启用")
            return
        provider_config = getattr(config, "provider_configs", {}).get("ollama", {})
        enabled = isinstance(provider_config, dict) and provider_config.get("enabled") is True
        if not enabled:
            self._ai_mode.setText("当前 AI 模式：fallback")
            self._connection_status.setText("连接状态：未启用")
            return
        self._ai_mode.setText("当前 AI 模式：本地 Ollama")
        if detected_status is not None:
            self._connection_status.setText(f"连接状态：{_ai_provider_status_label(detected_status)}")

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("设置与本地 AI 助手", "Developer Preview / 本地测试版", back_text="返回项目首页", back_signal=self.back_requested))
        env_card, env_layout = _card("本地环境状态")
        python_path = shutil.which("python3") or shutil.which("python") or "未知"
        env_layout.addWidget(_muted(f"当前 Python：{python_path}"))
        env_layout.addWidget(_muted("是否 project-local .venv：占位检测"))
        env_layout.addWidget(_muted("核心依赖状态：随测试环境预检；缺失时由测试或打包流程提示。"))
        env_layout.addWidget(_muted("package manifest 状态：占位"))
        root.addWidget(env_card)

        geo_card, geo_layout = _card("GEO legacy 环境检查")
        self._geo_check_status = _status_label("尚未运行 GEO legacy 环境检查。")
        geo_layout.addWidget(self._geo_check_status)
        geo_layout.addWidget(_muted("该检查只读取本地 legacy GEO 工具环境，不下载 GEO 数据，不运行数据处理。"))
        geo_layout.addWidget(_button("运行 GEO 环境检查", "secondaryButton", self.run_geo_legacy_environment_check), alignment=Qt.AlignLeft)
        self._geo_check_preview = _text_preview(170)
        self._geo_check_preview.setPlainText("检查结果将在这里显示。")
        geo_layout.addWidget(self._geo_check_preview)
        root.addWidget(geo_card)

        defaults_card, defaults_layout = _card("默认项目设置")
        defaults_layout.addWidget(_muted("默认数据策略：copy / reference"))
        defaults_layout.addWidget(_muted("默认图像格式：PNG / PDF / SVG，占位"))
        defaults_layout.addWidget(_muted("默认报告格式：Markdown / HTML / DOCX testing"))
        defaults_layout.addWidget(_muted("默认重复基因处理策略：max / median / min / remove，占位"))
        root.addWidget(defaults_card)

        ai_card, ai_layout = _card("本地 AI 检索助手")
        config = load_ai_gateway_config()
        provider_config = config.provider_configs.get("ollama", {})
        self._ai_status = _status_label("AI 默认关闭；启用本地 AI 前请确认不会上传敏感数据。")
        ai_layout.addWidget(self._ai_status)
        self._ai_mode = _status_label("当前 AI 模式：关闭")
        self._connection_status = _status_label("连接状态：未启用")
        ai_layout.addWidget(self._ai_mode)
        self._local_ai_enabled = QCheckBox("启用本地 AI")
        self._local_ai_enabled.setChecked(config.default_provider == "ollama" and config.allow_network and isinstance(provider_config, dict) and provider_config.get("enabled") is True)
        ai_layout.addWidget(self._local_ai_enabled)
        self._ollama_base_url_input = QLineEdit(str(provider_config.get("base_url") or DEFAULT_OLLAMA_BASE_URL) if isinstance(provider_config, dict) else DEFAULT_OLLAMA_BASE_URL)
        self._ollama_base_url_input.setPlaceholderText("Ollama 地址")
        self._ollama_model_input = QLineEdit(str(provider_config.get("default_model") or DEFAULT_OLLAMA_MODEL) if isinstance(provider_config, dict) else DEFAULT_OLLAMA_MODEL)
        self._ollama_model_input.setPlaceholderText("默认模型名称")
        ai_layout.addWidget(_muted("Ollama 地址"))
        ai_layout.addWidget(self._ollama_base_url_input)
        ai_layout.addWidget(_muted("默认模型名称"))
        ai_layout.addWidget(self._ollama_model_input)
        ai_layout.addWidget(self._connection_status)
        settings_row = QHBoxLayout()
        settings_row.addWidget(_button("保存 AI 设置", "secondaryButton", self.save_local_ai_settings))
        settings_row.addWidget(_button("测试连接", "secondaryButton", self.test_local_ai_connection))
        settings_row.addStretch(1)
        ai_layout.addLayout(settings_row)
        ai_layout.addWidget(_muted("隐私：AI 默认关闭；启用外部模型前请确认不会上传敏感数据。本版本外部 API 仅为后续版本预留，不提供 API Key 输入。"))
        self._question_input = QLineEdit()
        self._question_input.setPlaceholderText("输入中文研究问题")
        ai_layout.addWidget(self._question_input)
        row = QHBoxLayout()
        row.addWidget(_button("生成本地词库草稿", "secondaryButton", self.generate_placeholder_terms))
        row.addStretch(1)
        ai_layout.addLayout(row)
        self._preview = _text_preview(120)
        self._preview.setPlainText("本地 AI 仅用于翻译、关键词扩展和检索辅助；不参与统计分析，不生成科研结论，不替代人工判断。")
        ai_layout.addWidget(self._preview)
        self._refresh_ai_status(config)
        root.addWidget(ai_card)


def _scroll_root(page: QWidget, *, max_width: int | None = None) -> QVBoxLayout:
    outer = QVBoxLayout(page)
    outer.setContentsMargins(0, 0, 0, 0)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
    content = QWidget()
    content.setObjectName("bioWorkflowScrollContent")
    if max_width is not None:
        content.setMaximumWidth(max_width)
    layout = QVBoxLayout(content)
    layout.setContentsMargins(32, 24, 32, 40)
    layout.setSpacing(SPACING["md"])
    scroll.setWidget(content)
    outer.addWidget(scroll)
    return layout


def _header(title: str, subtitle: str, *, back_text: str, back_signal: Signal) -> QFrame:
    frame = QFrame()
    frame.setObjectName("bioProjectHeader")
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
    text_col = QVBoxLayout()
    title_label = QLabel(title)
    title_label.setObjectName("bioProjectTitle")
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("bioProjectSubtitle")
    subtitle_label.setWordWrap(True)
    preview = QLabel("0.1.0-internal-beta · Developer Preview / 本地测试版")
    preview.setObjectName("bioProjectPreviewBadge")
    text_col.addWidget(title_label)
    text_col.addWidget(subtitle_label)
    text_col.addWidget(preview, alignment=Qt.AlignLeft)
    layout.addLayout(text_col, 1)
    button = QPushButton(back_text)
    button.setObjectName("secondaryButton")
    button.clicked.connect(back_signal.emit)
    layout.addWidget(button)
    return frame


def _card(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("bioProjectCard")
    frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
    layout.setSpacing(SPACING["sm"])
    label = QLabel(title)
    label.setObjectName("bioProjectCardTitle")
    layout.addWidget(label)
    return frame, layout


def _readiness_todo_row(title: str, purpose: str, state: str, buttons: list[QPushButton]) -> tuple[QFrame, QLabel]:
    frame = QFrame()
    frame.setObjectName("readinessTodoRow")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
    layout.setSpacing(SPACING["xs"])
    title_label = QLabel(title)
    title_label.setObjectName("bioProjectCardTitle")
    layout.addWidget(title_label)
    layout.addWidget(_muted(purpose))
    state_label = _muted(state)
    layout.addWidget(state_label)
    actions = QHBoxLayout()
    for button in buttons:
        actions.addWidget(button)
    actions.addStretch(1)
    layout.addLayout(actions)
    return frame, state_label


def _button(text: str, object_name: str, callback: Callable[..., Any], *, role: str | None = None, small: bool = False) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName(object_name)
    if role is not None or small:
        _apply_button_semantics(button, role or "secondary", small=small)
    button.clicked.connect(callback)
    return button


def _apply_button_semantics(button: QPushButton, role: str, *, small: bool = False) -> QPushButton:
    button.setProperty("buttonRole", role)
    if small:
        button.setProperty("buttonSize", "small")
    elif button.property("buttonSize") == "small":
        button.setProperty("buttonSize", "")
    button.style().unpolish(button)
    button.style().polish(button)
    button.update()
    return button


def _apply_button_semantics_by_text(parent: QWidget, text: str, role: str, *, small: bool = False) -> None:
    for button in parent.findChildren(QPushButton):
        if button.text() == text:
            _apply_button_semantics(button, role, small=small)


def _muted(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("bioProjectMutedLabel")
    label.setWordWrap(True)
    return label


def _status_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("bioProjectStatusLabel")
    label.setWordWrap(True)
    return label


def _text_preview(height: int = 220) -> QPlainTextEdit:
    edit = QPlainTextEdit()
    edit.setReadOnly(True)
    edit.setMinimumHeight(min(height, 180))
    edit.setMaximumHeight(max(height, 120))
    edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return edit


def _read_only_report_view(height: int = 150) -> QTextEdit:
    edit = QTextEdit()
    edit.setReadOnly(True)
    edit.setAcceptRichText(False)
    edit.setMinimumHeight(min(height, 180))
    edit.setMaximumHeight(max(height, 120))
    edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return edit


def _table(headers: list[str]) -> QTableWidget:
    table = QTableWidget()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setMinimumHeight(190)
    table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    table.verticalHeader().setDefaultSectionSize(34)
    table.horizontalHeader().setMinimumHeight(36)
    return table


def _fill_table(table: QTableWidget, rows: list[list[object]]) -> None:
    table.clearContents()
    table.setRowCount(len(rows))
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            table.setItem(row_index, col_index, item)
    table.resizeColumnsToContents()


def _table_text(table: QTableWidget, row: int, column: int) -> str:
    item = table.item(row, column)
    return item.text().strip() if item is not None else ""


def _clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


def _set_table_widths(table: QTableWidget, widths: list[int]) -> None:
    for index, width in enumerate(widths[: table.columnCount()]):
        table.setColumnWidth(index, width)


def _configure_history_cache_table(table: QTableWidget) -> None:
    header = table.horizontalHeader()
    header.setStretchLastSection(False)
    header.setSectionResizeMode(0, QHeaderView.Fixed)
    header.setSectionResizeMode(1, QHeaderView.Stretch)
    header.setSectionResizeMode(2, QHeaderView.Fixed)
    table.setColumnWidth(0, 140)
    table.setColumnWidth(2, 260)


def _table_column_index(table: QTableWidget, header: str) -> int:
    for index in range(table.columnCount()):
        item = table.horizontalHeaderItem(index)
        if item is not None and item.text() == header:
            return index
    return max(0, table.columnCount() - 1)


def _registered_source_action_widget(row: RegisteredSourceRow) -> QWidget:
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    view_button = QPushButton("查看")
    view_button.setObjectName(f"registeredSourceViewButton_{row.acquisition_id}")
    remove_button = QPushButton("移除")
    remove_button.setObjectName(f"registeredSourceRemoveButton_{row.acquisition_id}")
    remove_button.setEnabled(False)
    layout.addWidget(view_button)
    layout.addWidget(remove_button)
    layout.addStretch(1)
    return widget


def _project_root(summary: BioinformaticsProjectSummary | Path | str | None) -> Path | None:
    if isinstance(summary, BioinformaticsProjectSummary):
        return summary.project_root
    if isinstance(summary, (str, Path)):
        return Path(summary).expanduser().resolve()
    return None


def _project_header_text(summary: BioinformaticsProjectSummary | Path | None) -> str:
    if isinstance(summary, BioinformaticsProjectSummary):
        return f"当前项目：{summary.project_name} · {summary.project_root}"
    root = _project_root(summary)
    return f"当前项目路径：{root}" if root else "请先创建或打开生信分析项目。"


def _strategy_from_combo(combo: QComboBox) -> AcquisitionStrategy:
    return "copy" if combo.currentText().startswith("复制") else "reference"


def _summary_to_dict(summary: AcquisitionSummary | None) -> dict[str, object] | str:
    if summary is None:
        return "尚未生成数据获取记录"
    return {
        "source_type": summary.source_type,
        "source_label": summary.source_label,
        "strategy": summary.strategy,
        "created_at": summary.created_at,
        "status": summary.status,
        "registered_files": list(summary.registered_files),
        "copied_files": list(summary.copied_files),
        "referenced_paths": list(summary.referenced_paths),
        "warnings": list(summary.warnings),
    }


GEO_SOURCE_TYPES = {"geo_gse", "geo_accession", "geo_search_candidate", "chinese_geo_gse"}


def _registered_source_rows(project_root: Path | None) -> list[RegisteredSourceRow]:
    if project_root is None:
        return []
    records_dir = project_root / "acquisition" / "records"
    if not records_dir.exists():
        return []
    rows_by_key: dict[tuple[str, str], RegisteredSourceRow] = {}
    seen: set[str] = set()
    for path in sorted(records_dir.glob("*.json")):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        acquisition_id = str(payload.get("acquisition_id") or path.stem)
        if acquisition_id in seen:
            continue
        seen.add(acquisition_id)
        source_type = str(payload.get("source_type") or "unknown")
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        source_label = _registered_source_display_name(payload, metadata)  # type: ignore[arg-type]
        row = RegisteredSourceRow(
            acquisition_id=acquisition_id,
            source_type_key=source_type,
            source_type=_source_type_label(source_type),
            source_label=source_label,
            location=_registered_source_location(payload, metadata),  # type: ignore[arg-type]
            status=_registered_status_text(payload),
            created_at=str(payload.get("created_at") or ""),
            strategy=str(payload.get("strategy") or ""),
            location_tooltip=_registered_source_full_location(payload, metadata),  # type: ignore[arg-type]
        )
        key = (row.source_type_key, row.source_label)
        previous = rows_by_key.get(key)
        if previous is None or _registered_row_rank(row) >= _registered_row_rank(previous):
            rows_by_key[key] = row
    return sorted(rows_by_key.values(), key=lambda row: row.created_at)


def _current_project_dataset_entries(project_root: Path | None, *, geo_only: bool = False) -> list[DatasetListEntry]:
    if project_root is None:
        return []
    notes = _load_user_dataset_notes(project_root)
    grouped: dict[str, DatasetListEntry] = {}
    ranks: dict[str, tuple[int, str]] = {}
    records_dir = project_root / "acquisition" / "records"
    if not records_dir.exists():
        return []
    for path in sorted(records_dir.glob("*.json")):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict):
            metadata = {}
        source_type = str(payload.get("source_type") or "unknown")
        if geo_only and not _is_geo_record(payload, metadata):
            continue
        row = RegisteredSourceRow(
            acquisition_id=str(payload.get("acquisition_id") or path.stem),
            source_type_key=source_type,
            source_type=_source_type_label(source_type),
            source_label=_registered_source_display_name(payload, metadata),
            location=_registered_source_location(payload, metadata),
            status=_registered_status_text(payload),
            created_at=str(payload.get("created_at") or ""),
            strategy=str(payload.get("strategy") or ""),
            location_tooltip=_registered_source_full_location(payload, metadata),
        )
        entry = _dataset_entry_from_record(project_root, row, payload, metadata, notes)
        rank = _dataset_entry_rank(entry, row.created_at)
        previous = grouped.get(entry.key)
        if previous is None:
            grouped[entry.key] = entry
            ranks[entry.key] = rank
            continue
        acquisition_ids = tuple(dict.fromkeys([*previous.acquisition_ids, *entry.acquisition_ids]))
        if rank >= ranks[entry.key]:
            grouped[entry.key] = DatasetListEntry(**{**entry.__dict__, "acquisition_ids": acquisition_ids})
            ranks[entry.key] = rank
        else:
            grouped[entry.key] = DatasetListEntry(**{**previous.__dict__, "acquisition_ids": acquisition_ids})
    return sorted(grouped.values(), key=lambda entry: (_dataset_source_order(entry.source_type_key), entry.name))


def _dataset_entry_from_record(
    project_root: Path,
    row: RegisteredSourceRow,
    payload: dict[str, object],
    metadata: dict[str, object],
    notes: dict[str, str],
) -> DatasetListEntry:
    key = _dataset_entry_key(row, metadata)
    title = _dataset_title_from_record(row, payload, metadata)
    abstract = _dataset_abstract_from_record(payload, metadata)
    status = _dataset_status_text(row, payload, metadata)
    available = _dataset_available_content(row, status, metadata)
    missing = _dataset_missing_content(row, status, metadata)
    accession = _geo_accession_from_record(payload, metadata) if _is_geo_record(payload, metadata) else ""
    return DatasetListEntry(
        key=key,
        source=_dataset_source_label(row, metadata),
        name=row.source_label,
        status=status,
        available_content=available,
        missing_content=missing,
        note=notes.get(key, ""),
        title=title,
        abstract=abstract,
        keywords=_dataset_keywords(metadata),
        technical_info=_dataset_technical_info(project_root, row, payload, metadata),
        ready_for_recognition=_record_ready_for_recognition(payload, metadata),
        downloadable=_dataset_is_downloadable(row, payload, metadata),
        removable=True,
        source_type_key=row.source_type_key,
        accession=accession,
        acquisition_ids=(row.acquisition_id,),
    )


def _dataset_entry_key(row: RegisteredSourceRow, metadata: dict[str, object]) -> str:
    if row.source_type_key in GEO_SOURCE_TYPES or str(metadata.get("source") or "") == "geo":
        accession = row.source_label.upper()
        return f"geo:{accession}"
    if "tcga" in row.source_type_key or str(metadata.get("source") or "") == "tcga_gdc":
        return f"tcga:{row.source_label.upper()}"
    if "gtex" in row.source_type_key or str(metadata.get("source") or "") == "gtex":
        return f"gtex:{row.source_label.upper()}"
    return f"local:{row.acquisition_id}"


def _dataset_source_label(row: RegisteredSourceRow, metadata: dict[str, object]) -> str:
    ui_source = str(metadata.get("ui_source") or "")
    if row.source_type_key == "local_import":
        return "本地导入"
    if ui_source == "chinese_research_question_search":
        return "中文检索"
    if row.source_type_key in GEO_SOURCE_TYPES:
        return "GSE 编号检索"
    if "tcga" in row.source_type_key:
        return "中文检索"
    if "gtex" in row.source_type_key:
        return "中文检索"
    return "当前项目"

def _dataset_status_text(row: RegisteredSourceRow, payload: dict[str, object], metadata: dict[str, object]) -> str:
    if row.source_type_key in GEO_SOURCE_TYPES or str(metadata.get("source") or "") == "geo":
        asset_summary = metadata.get("asset_manifest_summary")
        if isinstance(asset_summary, dict):
            expression_status = str(asset_summary.get("expression_matrix_status") or "")
            if expression_status == "downloaded":
                return "已下载"
            if asset_summary.get("metadata_downloaded"):
                return "元数据已下载"
            if payload.get("strategy") == "plan_only":
                return "未下载"
    if _record_ready_for_recognition(payload, metadata):
        if row.source_type_key == "local_import":
            return "已导入"
        if "已下载" in row.status or "可进入识别" in row.status:
            return "已下载"
        return "待识别"
    if payload.get("strategy") == "plan_only":
        if row.source_type_key in GEO_SOURCE_TYPES:
            return "未下载"
        return "未下载"
    if row.status and row.status not in {"已登记", "已登记，需确认"}:
        return row.status.replace("已登记", "已添加")
    return "需要补充信息" if row.status.endswith("需确认") else "待识别"


def _dataset_available_content(row: RegisteredSourceRow, status: str, metadata: dict[str, object]) -> str:
    if row.source_type_key == "local_import":
        return "待识别"
    assets: list[str] = []
    raw_status = row.status
    if "表达矩阵已下载" in raw_status:
        assets.append("表达矩阵")
    if "metadata" in raw_status or "元数据" in raw_status:
        assets.append("样本信息")
    if "平台" in raw_status or metadata.get("platform_accessions"):
        assets.append("平台注释")
    if "tcga" in row.source_type_key:
        return "表达矩阵、临床信息"
    if "gtex" in row.source_type_key:
        return "表达矩阵"
    return "、".join(dict.fromkeys(assets)) if assets else "待确认"


def _dataset_missing_content(row: RegisteredSourceRow, status: str, metadata: dict[str, object]) -> str:
    if row.source_type_key == "local_import":
        return "无" if status in {"已导入", "待识别"} else "待识别确认"
    raw_status = row.status
    missing: list[str] = []
    if "表达矩阵待确认" in raw_status or "表达矩阵待下载" in raw_status or status == "未下载":
        missing.append("表达矩阵")
    if "平台" not in raw_status and not metadata.get("platform_accessions") and row.source_type_key in GEO_SOURCE_TYPES:
        missing.append("平台注释")
    if "tcga" in row.source_type_key or "gtex" in row.source_type_key:
        return "数据文件"
    return "、".join(dict.fromkeys(missing)) if missing else "无"


def _dataset_title_from_record(row: RegisteredSourceRow, payload: dict[str, object], metadata: dict[str, object]) -> str:
    for key in ("title_zh", "display_title_zh", "title", "display_title", "title_en", "source_name"):
        value = str(metadata.get(key) or "").strip()
        if value:
            return value
    return row.source_label or "暂无标题"


def _dataset_abstract_from_record(payload: dict[str, object], metadata: dict[str, object]) -> str:
    for key in ("summary_zh", "brief_zh", "abstract_zh", "summary", "summary_en", "overall_design_en", "abstract"):
        value = str(metadata.get(key) or "").strip()
        if value:
            return value
    return "暂无摘要"


def _dataset_keywords(metadata: dict[str, object]) -> str:
    values: list[str] = []
    for key in ("disease", "tissue", "organism", "data_modality", "query_used"):
        value = str(metadata.get(key) or "").strip()
        if value:
            values.append(value)
    platforms = metadata.get("platform_accessions")
    if isinstance(platforms, list):
        values.extend(str(item) for item in platforms if str(item).strip())
    return "、".join(dict.fromkeys(values)) if values else "暂无关键词"


def _dataset_technical_info(project_root: Path, row: RegisteredSourceRow, payload: dict[str, object], metadata: dict[str, object]) -> str:
    return _json(
        {
            "数据来源": row.source_type,
            "GSE 编号或本地路径": row.location_tooltip or row.location,
            "当前项目绑定状态": payload.get("status", "未记录"),
            "下载状态": metadata.get("download_status", "未记录"),
            "已发现内容": _dataset_available_content(row, row.status, metadata),
            "缺失内容": _dataset_missing_content(row, row.status, metadata),
            "最近更新时间": payload.get("created_at", "未记录"),
            "日志或错误摘要": payload.get("warnings", []),
            "project_root": str(project_root),
        }
    )


def _dataset_is_downloadable(row: RegisteredSourceRow, payload: dict[str, object], metadata: dict[str, object]) -> bool:
    if row.source_type_key in GEO_SOURCE_TYPES:
        return payload.get("strategy") == "plan_only" or "表达矩阵待确认" in row.status or "表达矩阵待下载" in row.status or "已发现补充文件" in row.status
    return False


def _dataset_entry_rank(entry: DatasetListEntry, created_at: str) -> tuple[int, str]:
    score = 0
    if entry.status in {"识别完成", "已导入", "已下载"} or entry.ready_for_recognition:
        score = 3
    elif entry.status == "待识别":
        score = 2
    elif entry.status == "未下载":
        score = 1
    return score, created_at


def _dataset_source_order(source_type_key: str) -> int:
    if source_type_key == "local_import":
        return 0
    if source_type_key in GEO_SOURCE_TYPES:
        return 1
    if "tcga" in source_type_key:
        return 2
    if "gtex" in source_type_key:
        return 3
    return 9


def _dataset_entry_tooltip(entry: DatasetListEntry, column: int) -> str:
    if column == 2:
        return entry.title
    if column == 6:
        return entry.note
    return entry.technical_info if column in {3, 4, 5} else ""


def _dataset_detail_summary(entry: DatasetListEntry) -> str:
    return "\n".join(
        [
            f"数据集编号或文件名：{entry.name}",
            f"标题：{entry.title or '暂无标题'}",
            f"摘要：{entry.abstract or '暂无摘要'}",
            f"关键词 / 疾病 / 组织 / 平台：{entry.keywords or '暂无关键词'}",
        ]
    )


def _compact_note(note: str) -> str:
    cleaned = " ".join(note.split())
    if not cleaned:
        return ""
    return cleaned if len(cleaned) <= 42 else cleaned[:39] + "..."


def _user_dataset_notes_path(project_root: Path) -> Path:
    return project_root / "manifests" / "user_dataset_notes.json"


def _load_user_dataset_notes(project_root: Path) -> dict[str, str]:
    path = _user_dataset_notes_path(project_root)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    notes = payload.get("notes") if isinstance(payload, dict) else {}
    if not isinstance(notes, dict):
        return {}
    result: dict[str, str] = {}
    for key, item in notes.items():
        if isinstance(item, dict):
            result[str(key)] = str(item.get("note") or "")
        else:
            result[str(key)] = str(item or "")
    return result


def _save_user_dataset_note(project_root: Path, key: str, note: str) -> None:
    path = _user_dataset_notes_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        payload = {}
    notes = payload.get("notes") if isinstance(payload, dict) else {}
    if not isinstance(notes, dict):
        notes = {}
    if note:
        notes[key] = {"note": note, "updated_at": _utc_now_iso()}
    else:
        notes.pop(key, None)
    payload = {
        "schema_version": "biomedpilot.user_dataset_notes.v1",
        "updated_at": _utc_now_iso(),
        "notes": notes,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _historical_cache_entries(project_root: Path | None) -> list[dict[str, str]]:
    if project_root is None:
        return []
    selected = {entry.key for entry in _current_project_dataset_entries(project_root)}
    bound_paths = _current_project_bound_paths(project_root)
    entries: list[dict[str, str]] = []
    geo_root = project_root / "raw_data" / "geo"
    if geo_root.exists():
        for child in sorted(geo_root.iterdir()):
            if child.name.startswith("."):
                continue
            key = f"geo:{child.name.upper()}"
            child_path = str(child.resolve()) if child.exists() else str(child)
            if key not in selected and not _path_matches_any_bound_path(child, bound_paths):
                entries.append({"name": child.name, "path": str(child)})
    return entries


def _delete_historical_cache_path(project_root: Path, target: Path, name: str = "") -> tuple[bool, str]:
    root = project_root.expanduser().resolve()
    geo_cache_root = (root / "raw_data" / "geo").resolve()
    try:
        resolved = target.expanduser().resolve()
    except OSError as exc:
        return False, f"缓存删除失败：{exc}"
    if not _is_path_inside(resolved, geo_cache_root) or resolved == geo_cache_root:
        return False, "缓存删除失败：路径不在允许删除的缓存目录内。"
    expected_key = f"geo:{(name or resolved.name).upper()}"
    selected = {entry.key for entry in _current_project_dataset_entries(root)}
    if expected_key in selected or _path_matches_any_bound_path(resolved, _current_project_bound_paths(root)):
        return False, "该数据已加入当前项目，不能作为历史缓存删除。如需移除，请在待处理数据集中删除所选。"
    if not resolved.exists():
        return True, "缓存文件已不存在，已从列表移除。"
    try:
        if resolved.is_dir():
            shutil.rmtree(resolved)
        else:
            resolved.unlink()
    except OSError as exc:
        return False, f"缓存删除失败：{exc}"
    return True, "缓存已删除。"


def _path_matches_any_bound_path(path: Path, bound_paths: set[str]) -> bool:
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        resolved = path.expanduser()
    for raw in bound_paths:
        try:
            bound = Path(raw).expanduser().resolve()
        except OSError:
            bound = Path(raw).expanduser()
        if resolved == bound or _is_path_inside(bound, resolved) or _is_path_inside(resolved, bound):
            return True
    return False


def _is_path_inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _current_project_bound_paths(project_root: Path) -> set[str]:
    records_dir = project_root / "acquisition" / "records"
    if not records_dir.exists():
        return set()
    paths: set[str] = set()
    for path in records_dir.glob("*.json"):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for key in ("registered_files", "copied_files", "referenced_paths"):
            values = payload.get(key)
            if not isinstance(values, list):
                continue
            for raw in values:
                candidate = Path(str(raw)).expanduser()
                paths.add(str(candidate.resolve()) if candidate.exists() else str(candidate))
    return paths


def _pending_recognition_selection_path(project_root: Path) -> Path:
    return project_root / "manifests" / "pending_recognition_selection.json"


def _save_pending_recognition_selection(project_root: Path, entries: list[DatasetListEntry]) -> None:
    path = _pending_recognition_selection_path(project_root)
    payload = {
        "schema_version": "biomedpilot.pending_recognition_selection.v1",
        "updated_at": _utc_now_iso(),
        "selected_keys": [entry.key for entry in entries],
        "selected_acquisition_ids": sorted({acquisition_id for entry in entries for acquisition_id in entry.acquisition_ids}),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_pending_recognition_selection(project_root: Path | None) -> dict[str, set[str]]:
    if project_root is None:
        return {"selected_keys": set(), "selected_acquisition_ids": set()}
    path = _pending_recognition_selection_path(project_root)
    if not path.exists():
        return {"selected_keys": set(), "selected_acquisition_ids": set()}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"selected_keys": set(), "selected_acquisition_ids": set()}
    return {
        "selected_keys": {str(item) for item in payload.get("selected_keys", []) or []},
        "selected_acquisition_ids": {str(item) for item in payload.get("selected_acquisition_ids", []) or []},
    }


def _recognition_row_selected_by_context(row: RegisteredSourceRow, selection: dict[str, set[str]]) -> bool:
    return row.acquisition_id in selection.get("selected_acquisition_ids", set()) or _recognition_row_key(row) in selection.get("selected_keys", set())


def _recognition_row_key(row: RegisteredSourceRow) -> str:
    if row.source_type_key in GEO_SOURCE_TYPES:
        return f"geo:{row.source_label.upper()}"
    if "tcga" in row.source_type_key:
        return f"tcga:{row.source_label.upper()}"
    if "gtex" in row.source_type_key:
        return f"gtex:{row.source_label.upper()}"
    return f"local:{row.acquisition_id}"


def _recognition_paths_for_rows(project_root: Path, rows: list[RegisteredSourceRow]) -> list[str]:
    paths: list[str] = []
    for row in rows:
        payload = _acquisition_payload_by_id(project_root, row.acquisition_id)
        if not payload:
            continue
        for key in ("copied_files", "referenced_paths", "registered_files"):
            values = payload.get(key)
            if isinstance(values, list):
                paths.extend(str(value) for value in values if str(value).strip())
    return list(dict.fromkeys(paths))


def _acquisition_payload_by_id(project_root: Path, acquisition_id: str) -> dict[str, object] | None:
    path = project_root / "acquisition" / "records" / f"{acquisition_id}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _remove_acquisition_binding_by_id(project_root: Path, acquisition_id: str) -> bool:
    removed = False
    latest_ids = _latest_acquisition_ids(project_root)
    for folder in ("records", "plans", "handoffs"):
        target = project_root / "acquisition" / folder / f"{acquisition_id}.json"
        if target.exists():
            try:
                target.unlink()
                removed = True
            except OSError:
                pass
    if acquisition_id in latest_ids:
        for target in (
            project_root / "acquisition" / "records" / LATEST_RECORD,
            project_root / "acquisition" / "plans" / LATEST_PLAN,
            project_root / "acquisition" / "handoffs" / LATEST_HANDOFF,
        ):
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
    return removed


def _remove_dataset_project_binding(project_root: Path, entry: DatasetListEntry) -> bool:
    if entry.accession:
        return _remove_geo_download_entry(project_root, entry.accession)
    removed = False
    latest_ids = _latest_acquisition_ids(project_root)
    for acquisition_id in entry.acquisition_ids:
        for folder in ("records", "plans", "handoffs"):
            target = project_root / "acquisition" / folder / f"{acquisition_id}.json"
            if target.exists():
                try:
                    target.unlink()
                    removed = True
                except OSError:
                    pass
        if acquisition_id in latest_ids:
            for target in (
                project_root / "acquisition" / "records" / LATEST_RECORD,
                project_root / "acquisition" / "plans" / LATEST_PLAN,
                project_root / "acquisition" / "handoffs" / LATEST_HANDOFF,
            ):
                try:
                    target.unlink(missing_ok=True)
                except OSError:
                    pass
    return removed


def _latest_acquisition_ids(project_root: Path) -> set[str]:
    latest_ids: set[str] = set()
    for target in (
        project_root / "acquisition" / "records" / LATEST_RECORD,
        project_root / "acquisition" / "plans" / LATEST_PLAN,
        project_root / "acquisition" / "handoffs" / LATEST_HANDOFF,
    ):
        if not target.exists():
            continue
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        latest_ids.add(str(payload.get("acquisition_id") or ""))
    return latest_ids


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _geo_download_list_entries(project_root: Path | None) -> list[dict[str, str]]:
    if project_root is None:
        return []
    records_dir = project_root / "acquisition" / "records"
    if not records_dir.exists():
        return []
    entries: dict[str, dict[str, str]] = {}
    ranks: dict[str, tuple[int, str]] = {}
    for path in sorted(records_dir.glob("*.json")):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict) or not _is_geo_record(payload, metadata):
            continue
        accession = _geo_accession_from_record(payload, metadata)
        if not accession:
            continue
        status = _geo_download_status_text(payload, metadata)
        entry = {
            "accession": accession,
            "title": _geo_record_title(payload, metadata),
            "source": _geo_record_source_label(payload, metadata),
            "status": status,
            "assets": _geo_download_assets_text(status),
            "missing": _geo_download_missing_text(status),
            "next_step": _geo_download_next_step_text(project_root, accession, status),
            "ready": "yes" if "可进入识别" in status else "no",
            "pending_assets": "yes" if _candidate_has_pending_geo_assets(project_root, accession) else "no",
        }
        rank = _geo_download_entry_rank(status), str(payload.get("created_at") or "")
        if accession not in entries or rank >= ranks[accession]:
            entries[accession] = entry
            ranks[accession] = rank
    return [entries[key] for key in sorted(entries)]


def _is_geo_record(payload: dict[str, object], metadata: dict[str, object]) -> bool:
    source_type = str(payload.get("source_type") or "")
    return source_type in GEO_SOURCE_TYPES or str(metadata.get("source") or "") == "geo"


def _geo_accession_from_record(payload: dict[str, object], metadata: dict[str, object]) -> str:
    for key in ("accession_or_project", "accession", "gse_id", "source_id"):
        value = str(metadata.get(key) or "").strip().upper()
        if value.startswith("GSE"):
            return value
    label = str(payload.get("source_label") or "").strip().upper()
    return label if label.startswith("GSE") else ""


def _geo_record_title(payload: dict[str, object], metadata: dict[str, object]) -> str:
    for key in ("title", "display_title", "source_name"):
        value = str(metadata.get(key) or "").strip()
        if value:
            return value
    return str(payload.get("source_label") or "GEO 数据集")


def _geo_record_source_label(payload: dict[str, object], metadata: dict[str, object]) -> str:
    ui_source = str(metadata.get("ui_source") or "")
    if ui_source == "chinese_research_question_search":
        return "中文检索"
    if ui_source == "gse_accession_search" or payload.get("source_type") == "geo_gse":
        return "GSE 编号检索"
    return "GEO"


def _geo_download_status_text(payload: dict[str, object], metadata: dict[str, object]) -> str:
    status = _registered_status_text(payload)
    if status in {"已登记", "已添加", "待下载"} and str(payload.get("strategy") or "") == "plan_only":
        return "元数据待下载"
    return status


def _geo_download_entry_rank(status: str) -> int:
    if "补充文件已下载" in status or "表达矩阵已下载" in status:
        return 4
    if "可进入识别" in status:
        return 3
    if "元数据已下载" in status:
        return 2
    if "元数据待下载" in status:
        return 1
    return 0


def _geo_download_assets_text(status: str) -> str:
    assets: list[str] = []
    if "元数据已下载" in status:
        assets.append("metadata")
    if "表达矩阵已下载" in status:
        assets.append("表达矩阵")
    if "补充文件已下载" in status:
        assets.append("补充文件")
    return "、".join(assets) if assets else "待下载"


def _geo_download_missing_text(status: str) -> str:
    if "可进入识别" in status and "表达矩阵待确认" not in status and "表达矩阵待下载" not in status:
        return "无明确缺失"
    if "表达矩阵待确认" in status or "表达矩阵待下载" in status or "已发现补充文件" in status:
        return "表达矩阵/补充文件"
    if "元数据待下载" in status or "待下载" in status:
        return "元数据、表达矩阵"
    return "待确认"


def _geo_download_next_step_text(project_root: Path | None, accession: str, status: str) -> str:
    if _candidate_has_pending_geo_assets(project_root, accession):
        return "下载推荐文件"
    if "可进入识别" in status:
        return "进入识别"
    if "元数据已下载" in status:
        return "发现文件"
    return "下载元数据"


def _is_geo_saved_to_download_list(project_root: Path | None, accession: str) -> bool:
    normalized = accession.strip().upper()
    return any(entry["accession"] == normalized for entry in _geo_download_list_entries(project_root))


def _geo_candidate_from_download_entry(project_root: Path | None, accession: str) -> UnifiedDatasetCandidate | None:
    normalized = accession.strip().upper()
    if project_root is None:
        return None
    records_dir = project_root / "acquisition" / "records"
    if not records_dir.exists():
        return None
    for path in sorted(records_dir.glob("*.json"), reverse=True):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict) or not _is_geo_record(payload, metadata):
            continue
        if _geo_accession_from_record(payload, metadata) != normalized:
            continue
        title = _geo_record_title(payload, metadata)
        source_metadata = metadata.get("source_specific_metadata") if isinstance(metadata.get("source_specific_metadata"), dict) else {}
        candidate_metadata = {
            **dict(source_metadata or {}),
            "title_en": title,
            "platform_accessions": metadata.get("platform_accessions") or dict(source_metadata or {}).get("platform_accessions", []),
            "geo_url": metadata.get("geo_url") or f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={normalized}",
            "query_used": metadata.get("query_used") or normalized,
            "match_reason": metadata.get("match_reason") or "待处理数据集记录",
        }
        if metadata.get("organism"):
            candidate_metadata.setdefault("organism", metadata.get("organism"))
        candidate_metadata.setdefault("organism_display_name", get_organism_display_name(candidate_metadata.get("organism") or metadata.get("organism")))
        return UnifiedDatasetCandidate(
            source="geo",
            accession_or_project=normalized,
            display_title=title,
            organism=str(candidate_metadata.get("organism") or metadata.get("organism") or "未记录"),
            disease="",
            tissue="",
            data_modality=str(candidate_metadata.get("experiment_type") or metadata.get("data_modality") or "GEO dataset"),
            sample_count=candidate_metadata.get("sample_count") or metadata.get("sample_count") or "待确认",
            has_expression_matrix=False,
            has_sample_metadata=False,
            has_clinical_metadata=False,
            has_platform_annotation=bool(candidate_metadata.get("platform_accessions") or metadata.get("platform_accessions")),
            recommended_analyses=("data_recognition",),
            download_plan_available=True,
            score=55,
            warnings=tuple(str(item) for item in metadata.get("warnings", []) or []) if isinstance(metadata.get("warnings"), list) else (),
            source_specific_metadata=candidate_metadata,
        )
    return None


def _remove_geo_download_entry(project_root: Path | None, accession: str) -> bool:
    if project_root is None:
        return False
    normalized = accession.strip().upper()
    records_dir = project_root / "acquisition" / "records"
    if not records_dir.exists():
        return False
    removed = False
    latest_ids: set[str] = set()
    for latest in (records_dir / LATEST_RECORD, project_root / "acquisition" / "plans" / LATEST_PLAN, project_root / "acquisition" / "handoffs" / LATEST_HANDOFF):
        if latest.exists():
            try:
                payload = json.loads(latest.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                payload = {}
            latest_ids.add(str(payload.get("acquisition_id") or ""))
    for path in list(records_dir.glob("*.json")):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict) or not _is_geo_record(payload, metadata):
            continue
        if _geo_accession_from_record(payload, metadata) != normalized:
            continue
        acquisition_id = str(payload.get("acquisition_id") or path.stem)
        for folder in ("records", "plans", "handoffs"):
            target = project_root / "acquisition" / folder / f"{acquisition_id}.json"
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
        if acquisition_id in latest_ids:
            for target in (
                project_root / "acquisition" / "records" / LATEST_RECORD,
                project_root / "acquisition" / "plans" / LATEST_PLAN,
                project_root / "acquisition" / "handoffs" / LATEST_HANDOFF,
            ):
                try:
                    target.unlink(missing_ok=True)
                except OSError:
                    pass
        removed = True
    return removed


def _ready_registered_source_count(project_root: Path | None) -> int:
    if project_root is None:
        return 0
    records_dir = project_root / "acquisition" / "records"
    if not records_dir.exists():
        return 0
    ready_ids: set[str] = set()
    for path in records_dir.glob("*.json"):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict):
            metadata = {}
        if not _record_ready_for_recognition(payload, metadata):
            continue
        ready_ids.add(str(payload.get("acquisition_id") or path.stem))
    return len(ready_ids)


def _ready_chinese_source_count(project_root: Path | None) -> int:
    if project_root is None:
        return 0
    records_dir = project_root / "acquisition" / "records"
    if not records_dir.exists():
        return 0
    ready_keys: set[tuple[str, str]] = set()
    for path in records_dir.glob("*.json"):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict) or metadata.get("ui_source") != "chinese_research_question_search":
            continue
        if not _record_ready_for_recognition(payload, metadata):
            continue
        key = (str(metadata.get("source") or payload.get("source_type") or ""), str(metadata.get("accession_or_project") or payload.get("source_label") or ""))
        ready_keys.add(key)
    return len(ready_keys)


def _candidate_record_status_text(project_root: Path | None, source: str, accession_or_project: str) -> str:
    if project_root is None:
        return ""
    if source == "geo":
        manifest = _candidate_geo_asset_manifest(project_root, accession_or_project)
        if manifest:
            status = _geo_asset_status_text({"asset_manifest_summary": manifest.get("summary", {})})
            if status:
                return status
    records_dir = project_root / "acquisition" / "records"
    if not records_dir.exists():
        return ""
    latest_text = ""
    for path in sorted(records_dir.glob("*.json")):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict) or metadata.get("ui_source") != "chinese_research_question_search":
            continue
        key = (str(metadata.get("source") or ""), str(metadata.get("accession_or_project") or payload.get("source_label") or ""))
        if key != (source, accession_or_project):
            continue
        latest_text = _geo_asset_status_text(metadata) if source == "geo" else _registered_status_text(payload)
    return latest_text


def _candidate_has_pending_geo_assets(project_root: Path | None, accession_or_project: str) -> bool:
    manifest = _candidate_geo_asset_manifest(project_root, accession_or_project)
    if not manifest:
        return False
    for asset in manifest.get("assets", []) or []:
        if not isinstance(asset, dict):
            continue
        if asset.get("asset_type") not in {"series_matrix", "supplementary_file"}:
            continue
        if asset.get("status") != "downloaded" and asset.get("remote_url"):
            return True
    return False


def _candidate_has_download_manifest(project_root: Path | None, source: str, accession_or_project: str) -> bool:
    if project_root is None:
        return False
    records_dir = project_root / "acquisition" / "records"
    if not records_dir.exists():
        return False
    for path in sorted(records_dir.glob("*.json"), reverse=True):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict) or metadata.get("ui_source") != "chinese_research_question_search":
            continue
        key = (str(metadata.get("source") or ""), str(metadata.get("accession_or_project") or payload.get("source_label") or ""))
        if key != (source, accession_or_project):
            continue
        manifest_path = Path(str(metadata.get("download_manifest_path") or ""))
        if manifest_path.is_file():
            return True
        if str(metadata.get("download_status") or "") in {"tcga_gdc_download_manifest_created", "tcga_gdc_download_manifest_pending_file_selection", "gtex_download_manifest_created"}:
            return True
    return False


def _candidate_geo_asset_manifest(project_root: Path | None, accession_or_project: str) -> dict[str, object] | None:
    if project_root is None:
        return None
    accession = str(accession_or_project).strip().upper()
    records_dir = project_root / "acquisition" / "records"
    candidates: list[Path] = []
    if records_dir.exists():
        for path in sorted(records_dir.glob("*.json"), reverse=True):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            metadata = payload.get("metadata")
            if not isinstance(metadata, dict):
                continue
            if str(metadata.get("source") or "") != "geo":
                continue
            record_accession = str(metadata.get("accession_or_project") or payload.get("source_label") or "").upper()
            if record_accession != accession:
                continue
            manifest_path = Path(str(metadata.get("asset_manifest_path") or ""))
            if manifest_path.is_file():
                candidates.append(manifest_path)
    fallback = project_root / "raw_data" / "geo" / accession / f"{accession}_asset_manifest.json"
    if fallback.is_file():
        candidates.append(fallback)
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            return payload
    return None


def _registered_source_display_name(payload: dict[str, object], metadata: dict[str, object]) -> str:
    source_type = str(payload.get("source_type") or "")
    if source_type == "local_import":
        values = payload.get("registered_files") or payload.get("referenced_paths") or payload.get("copied_files")
        if isinstance(values, list) and values:
            return Path(str(values[0])).name
    if source_type in GEO_SOURCE_TYPES:
        return str(metadata.get("gse_id") or payload.get("source_label") or metadata.get("accession_or_project") or "未知 GSE")
    if source_type in {"tcga_project", "chinese_tcga_gdc_project"}:
        return str(metadata.get("project_id") or payload.get("source_label") or metadata.get("accession_or_project") or "未知 TCGA 项目")
    if source_type in {"gtex_tissue", "chinese_gtex_tissue"}:
        return str(metadata.get("tissue_name") or payload.get("source_label") or metadata.get("accession_or_project") or "未知 GTEx 组织")
    return str(payload.get("source_label") or metadata.get("accession_or_project") or "未知数据源")


def _registered_source_location(payload: dict[str, object], metadata: dict[str, object]) -> str:
    for key in ("registered_files", "referenced_paths", "copied_files"):
        values = payload.get(key)
        if isinstance(values, list) and values:
            return _compact_path(str(values[0]), max_chars=36)
    source = str(metadata.get("source") or "")
    if source == "geo" or payload.get("source_type") in {"geo_gse", "geo_accession"}:
        return "GEO"
    if source == "tcga_gdc" or "tcga" in str(payload.get("source_type") or ""):
        return "GDC / TCGA"
    if source == "gtex" or "gtex" in str(payload.get("source_type") or ""):
        return "GTEx"
    return "项目记录"


def _registered_source_full_location(payload: dict[str, object], metadata: dict[str, object]) -> str:
    for key in ("registered_files", "referenced_paths", "copied_files"):
        values = payload.get(key)
        if isinstance(values, list) and values:
            return str(values[0])
    return _registered_source_location(payload, metadata)


def _registered_status_text(payload: dict[str, object]) -> str:
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    if isinstance(metadata, dict):
        download_status = str(metadata.get("download_status") or "")
        ready = str(metadata.get("ready_for_recognition") or "")
        if str(metadata.get("source") or "") == "geo" or payload.get("source_type") in GEO_SOURCE_TYPES:
            asset_status = _geo_asset_status_text(metadata)
            if asset_status:
                return asset_status
        if download_status in {"tcga_gdc_download_manifest_created", "tcga_gdc_download_manifest_pending_file_selection"}:
            return "GDC 文件清单已创建，待下载数据文件"
        if download_status == "gtex_download_manifest_created":
            return "GTEx 下载清单已创建，待下载表达矩阵"
        if ready == "ready" and download_status == "geo_metadata_downloaded":
            return "元数据已下载 / 表达矩阵待下载 / 可进入识别"
        if ready == "ready" or download_status == "downloaded":
            return "已下载，待识别"
        if download_status.startswith("registered_pending") or ready.startswith("pending") or metadata.get("registration_status") == "registered_as_planned_source":
            return "待下载"
    warnings = payload.get("warnings")
    if isinstance(warnings, list) and warnings:
        return "已添加，需确认"
    return "已添加"


def _geo_asset_status_text(metadata: dict[str, object]) -> str:
    summary = metadata.get("asset_manifest_summary")
    if not isinstance(summary, dict):
        return ""
    parts: list[str] = []
    if summary.get("metadata_downloaded"):
        parts.append("元数据已下载")
    if summary.get("expression_matrix_status") == "downloaded":
        parts.append("表达矩阵已下载")
    elif summary.get("series_matrix_discovered") or summary.get("expression_candidate_count"):
        parts.append("表达矩阵待下载")
    elif summary.get("download_status") == "downloaded":
        parts.append("表达矩阵待确认")
    elif summary:
        parts.append("表达矩阵待确认")
    if summary.get("supplementary_files_downloaded"):
        parts.append("补充文件已下载")
    elif summary.get("supplementary_files_discovered"):
        parts.append("已发现补充文件")
    if summary.get("recognition_ready") or metadata.get("ready_for_recognition") == "ready":
        parts.append("可进入识别")
    return " / ".join(dict.fromkeys(parts))


def _record_ready_for_recognition(payload: dict[str, object], metadata: dict[str, object]) -> bool:
    if metadata.get("ready_for_recognition") == "ready" or metadata.get("download_status") == "downloaded":
        return True
    if payload.get("strategy") != "plan_only":
        return True
    return False


def _source_type_label(source_type: str) -> str:
    return {
        "local_import": "本地数据导入",
        "geo_series_matrix": "GEO Series Matrix",
        "tcga_local_folder": "TCGA 本地数据",
        "gtex_local_folder": "GTEx 本地数据",
        "tcga_gtex_tcga_folder": "TCGA + GTEx / TCGA 来源",
        "tcga_gtex_gtex_folder": "TCGA + GTEx / GTEx 来源",
        "geo_gse": "GSE 编号检索",
        "geo_accession": "GEO/GSE 数据来源",
        "chinese_geo_gse": "GSE 编号检索",
        "chinese_tcga_gdc_project": "TCGA/GDC 项目",
        "chinese_gtex_tissue": "GTEx 正常组织参考",
        "geo_search_candidate": "GEO/GSE 候选数据集",
        "tcga_project": "TCGA/GDC 项目",
        "gtex_tissue": "GTEx 正常组织参考",
    }.get(source_type, source_type)


def _selected_kind_from_paths(paths: list[Path]) -> str:
    if not paths:
        return "accession"
    return "folder" if paths[0].is_dir() else "file"


def _display_name_for_paths(paths: list[Path], fallback: str) -> str:
    if not paths:
        return fallback
    if len(paths) == 1:
        return paths[0].name or str(paths[0])
    return f"{len(paths)} 个文件：{paths[0].name}"


def _storage_policy_text(policy: str) -> str:
    return {
        "copy": "已复制到项目文件夹",
        "reference": "引用原始位置",
        "plan_only": "已添加编号，等待数据获取",
    }.get(policy, policy)


def _acquisition_status_text(summary: AcquisitionSummary) -> str:
    parts = []
    parts.append("数据获取计划：已生成" if summary.plan_path.exists() else "数据获取计划：未生成")
    parts.append("数据记录：已生成" if summary.record_path.exists() else "数据记录：未生成")
    parts.append("下一步交接清单：已生成" if summary.handoff_path.exists() else "下一步交接清单：未生成")
    return " / ".join(parts)


def _kind_label(summary: SelectedSourceSummary) -> str:
    if summary.selected_kind == "accession":
        return "当前 GSE 编号"
    if summary.source_type == "tcga_gtex_tcga_folder":
        return "TCGA 来源"
    if summary.source_type == "tcga_gtex_gtex_folder":
        return "GTEx 来源"
    if summary.source_type == "tcga_local_folder":
        return "已选择 TCGA 文件夹"
    if summary.source_type == "gtex_local_folder":
        return "已选择 GTEx 文件夹"
    if summary.selected_kind == "folder":
        return "已选择文件夹"
    return "已选择文件"


def _compact_path(path: str, *, max_chars: int = 74) -> str:
    if not path:
        return "未记录来源位置"
    if len(path) <= max_chars:
        return path
    suffix = path[-(max_chars - 3) :]
    slash = suffix.find("/")
    if slash > 0:
        suffix = suffix[slash:]
    return f"...{suffix}"


def _normalize_gse_id(value: str) -> str:
    cleaned = value.strip().upper().replace(" ", "")
    if not cleaned:
        return ""
    if cleaned.isdigit():
        return f"GSE{cleaned}"
    return cleaned


def _infer_local_data_type(paths: list[Path], *, source_type: str = "local_import") -> str:
    if source_type != "local_import":
        return _source_type_label(source_type)
    text = " ".join(str(path).lower() for path in paths)
    names = " ".join(path.name.lower() for path in paths)
    if "series_matrix" in text or "series matrix" in text:
        return "GEO Series Matrix"
    if "tcga" in text or "gdc" in text:
        return "TCGA 本地数据"
    if "gtex" in text:
        return "GTEx 本地数据"
    if any(token in names for token in ("expression", "expr", "matrix", "count", "counts", "tpm", "fpkm")):
        return "本地表达矩阵"
    if len(paths) == 1 and paths[0].suffix.lower() == ".xlsx":
        kind, _reason, confidence = classify_file(paths[0])
        if confidence >= 0.6 and kind in TYPE_LABELS:
            return TYPE_LABELS[kind]
    if any(token in names for token in ("sample", "metadata", "pheno", "phenotype")):
        return "样本注释"
    if "clinical" in names or "clinic" in names:
        return "临床表"
    if ("gene" in names and "annotation" in names) or "gene_annotation" in names:
        return "基因注释"
    if any(token in names for token in ("comparison", "group", "contrast")):
        return "分组配置"
    if paths:
        return "本地数据，待数据识别确认"
    return "未知本地数据"


def _selected_source_summary_text(summary: SelectedSourceSummary, *, compact: bool) -> str:
    path = _compact_path(summary.absolute_path) if compact else (summary.absolute_path or "未记录来源位置")
    registration_state = "需要补充数据" if summary.storage_policy == "plan_only" else "已完成"
    next_step = "可以点击“继续：数据识别”。" if summary.storage_policy != "plan_only" else "请导入已下载的 Series Matrix 文件，或等待后续版本接入自动下载。"
    lines = [
        f"当前数据：{summary.source_label}",
        f"来源内容：{summary.display_name}",
        f"{_kind_label(summary)}：{summary.display_name}",
        f"来源位置：{path}",
        f"保存方式：{_storage_policy_text(summary.storage_policy)}",
        f"数据状态：{registration_state}",
        summary.acquisition_status,
        f"最近更新时间：{summary.created_at or '未记录'}",
        f"下一步建议：{next_step}",
    ]
    if summary.source_type in {"tcga_gtex_tcga_folder", "tcga_gtex_gtex_folder"}:
        lines.append("警告：当前未进行正式 batch correction，后续分析需谨慎解释。")
    if summary.warnings:
        lines.append(f"warning：{'；'.join(summary.warnings)}")
    return "\n".join(lines)


def _source_card_status_text(summary: SelectedSourceSummary) -> str:
    if summary.source_type == "geo_gse" or summary.selected_kind == "accession":
        return f"已添加 GSE 数据集：{summary.display_name}"
    if summary.source_type == "local_import":
        return f"已选择本地数据：{_compact_path(summary.display_name, max_chars=58)}"
    if summary.storage_policy == "plan_only":
        return f"{summary.source_label}待添加确认。"
    return f"已选择本地数据：{_compact_path(summary.display_name, max_chars=58)}"


def _chinese_search_entry_status(rows: list[RegisteredSourceRow]) -> str:
    chinese_rows = [row for row in rows if _is_chinese_topic_source_type(row.source_type_key)]
    if not chinese_rows:
        return "尚未进行中文检索。"
    return f"最近中文检索：已选择 {len(chinese_rows)} 个候选数据集。"


def _is_chinese_topic_source_type(source_type: str) -> bool:
    return source_type.startswith("chinese_") or source_type in {"geo_accession", "geo_search_candidate", "tcga_project", "gtex_tissue"}


def _legacy_geo_tool_paths() -> None:
    legacy_root = Path(__file__).resolve().parent / "legacy"
    geo_tool_root = legacy_root / "geo_tool"
    for path in (str(geo_tool_root), str(legacy_root)):
        if path not in sys.path:
            sys.path.insert(0, path)


def _geo_fetcher_class() -> type[Any] | None:
    try:
        _legacy_geo_tool_paths()
        from app.bioinformatics.legacy.geo_tool.geo_info_fetcher import GeoInfoFetcher

        return GeoInfoFetcher
    except Exception:
        return None


def _fetch_geo_accession_metadata(gse_id: str, project_root: Path | None = None) -> str:
    try:
        detail = GeoDetailEnrichmentService(timeout=12).enrich(gse_id, project_root=project_root)
        if detail.summary or detail.overall_design or detail.sample_preview:
            return _geo_accession_metadata_text_from_detail(detail.to_candidate_metadata())
    except Exception:
        pass
    fetcher_cls = _geo_fetcher_class()
    if fetcher_cls is None:
        return (
            f"当前 GSE 编号：{gse_id}\n"
            "处理状态：已添加到项目。\n"
            "当前版本尚未接入可用的 GEO 元数据检索组件；也不会自动联网下载数据。\n"
            "下一步建议：请导入已下载的 Series Matrix 文件，或等待后续版本中使用自动下载。"
        )
    try:
        result = fetcher_cls(timeout=8).search_series(gse_id, max_results=3, page_size=3)
    except Exception as exc:
        return (
            f"当前 GSE 编号：{gse_id}\n"
            "处理状态：已添加到项目；本次联网元数据检索未完成。\n"
            f"检索提示：{exc}\n"
            "当前不会自动下载数据。请导入已下载的 Series Matrix 文件，或等待后续版本中使用自动下载。"
        )
    matched = [item for item in result.results if item.gse_id.upper() == gse_id.upper()] or result.results[:1]
    if not matched:
        return (
            f"当前 GSE 编号：{gse_id}\n"
            "处理状态：已添加到项目；GEO 元数据检索未返回匹配数据集。\n"
            "当前不会自动下载数据。请确认编号，或导入已下载的 Series Matrix 文件。"
        )
    info = matched[0]
    try:
        detail = build_geo_detail_metadata(
            info.gse_id,
            existing_metadata={
                "title_en": info.title_en,
                "summary_en": info.summary_en,
                "overall_design_en": info.overall_design_en,
                "organism": info.organism,
                "experiment_type": info.experiment_type,
                "sample_count": info.sample_count,
                "platform_accessions": [item.strip() for item in str(info.platform or "").replace(";", ",").split(",") if item.strip().startswith("GPL")],
                "platform_titles": [info.platform] if info.platform and not str(info.platform).strip().startswith("GPL") else [],
                "pmid": info.pubmed_id,
            },
        )
        if detail.summary or detail.overall_design:
            return _geo_accession_metadata_text_from_detail(detail.to_candidate_metadata())
    except Exception:
        pass
    return "\n".join(
        [
            f"当前 GSE 编号：{info.gse_id}",
            "处理状态：已获取 GEO 元数据并添加到项目；当前不会自动下载数据。",
            f"数据集标题：{info.title_en or '未记录'}",
            f"样本数：{info.sample_count or '未记录'}",
            f"平台信息：{info.platform or '未记录'}",
            f"物种：{info.organism or '未记录'}",
            f"可用文件：请在 GEO 页面或已下载 Series Matrix 中确认。",
            "下一步建议：导入已下载的 Series Matrix 文件后继续数据识别。",
        ]
    )


def _geo_accession_metadata_text_from_detail(metadata: dict[str, object]) -> str:
    accession = str(metadata.get("accession") or metadata.get("gse_id") or metadata.get("query_used") or "")
    platforms = metadata.get("platforms")
    platform_text = _geo_platform_summary(metadata)
    supplementary = metadata.get("supplementary_files")
    raw_files = []
    if isinstance(supplementary, list):
        raw_files = [str(item.get("file_name") or "") for item in supplementary if isinstance(item, dict) and str(item.get("file_name") or "").strip()]
    return "\n".join(
        [
            f"当前 GSE 编号：{accession}",
            "处理状态：已获取 GEO 详情元数据；当前不会自动下载数据。",
            f"数据集标题：{metadata.get('title_en') or '未记录'}",
            f"样本数：{metadata.get('sample_count') or '未记录'}",
            f"平台信息：{platform_text or '未记录'}",
            f"物种：{metadata.get('organism') or '未记录'}",
            f"实验类型：{metadata.get('experiment_type') or '未记录'}",
            f"公开日期：{metadata.get('public_date') or '未记录'}",
            f"PMID：{metadata.get('pmid') or '未记录'}",
            f"BioProject：{metadata.get('bioproject') or '未记录'}",
            f"SuperSeries：{metadata.get('superseries') or '未记录'}",
            f"可用文件：{', '.join(raw_files) if raw_files else '请在 GEO 页面或已下载 Series Matrix 中确认。'}",
            "下一步建议：查看样本标题和 characteristics 后确认分组，再下载或导入数据。",
            "GEO detail metadata JSON：" + json.dumps(metadata, ensure_ascii=False, separators=(",", ":")),
        ]
    )


def _gse_preview_from_metadata(gse_id: str, metadata_text: str) -> GseDatasetPreview:
    values: dict[str, str] = {}
    detail_metadata: dict[str, object] | None = None
    for line in metadata_text.splitlines():
        if "：" not in line:
            continue
        key, value = line.split("：", 1)
        values[key.strip()] = value.strip() or "未记录"
        if key.strip() == "GEO detail metadata JSON":
            try:
                payload = json.loads(value)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                detail_metadata = payload
    return GseDatasetPreview(
        gse_id=values.get("当前 GSE 编号", gse_id),
        title=values.get("数据集标题", "未记录"),
        platform=values.get("平台信息", "未记录"),
        sample_count=values.get("样本数", "未记录"),
        organism=values.get("物种", "未记录"),
        status="尚未添加",
        detail_metadata=detail_metadata,
    )


def _geo_candidate_from_gse_preview(preview: GseDatasetPreview) -> UnifiedDatasetCandidate:
    platform = preview.platform if preview.platform != "未记录" else ""
    platforms = [item.strip() for item in platform.replace(";", ",").split(",") if item.strip()]
    detail_metadata = dict(preview.detail_metadata or {})
    if detail_metadata:
        raw_platforms = detail_metadata.get("platform_accessions")
        platforms = [str(item) for item in raw_platforms if str(item).strip()] if isinstance(raw_platforms, list) else platforms
    display_title = str(detail_metadata.get("title_en") or preview.title)
    organism = str(detail_metadata.get("organism") or ("" if preview.organism == "未记录" else preview.organism))
    experiment_type = str(detail_metadata.get("experiment_type") or "GEO dataset")
    sample_count = detail_metadata.get("sample_count") or preview.sample_count
    metadata = {
        "title_en": display_title,
        "platform_accessions": platforms,
        "geo_url": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={preview.gse_id}",
        "match_reason": "GSE 编号精确匹配",
        "query_used": preview.gse_id,
    }
    metadata.update(detail_metadata)
    metadata.setdefault("organism_display_name", get_organism_display_name(organism))
    return UnifiedDatasetCandidate(
        source="geo",
        accession_or_project=preview.gse_id,
        display_title=display_title,
        organism=organism,
        disease="",
        tissue="",
        data_modality=experiment_type,
        sample_count=sample_count,
        has_expression_matrix=False,
        has_sample_metadata=False,
        has_clinical_metadata=False,
        has_platform_annotation=bool(platforms),
        recommended_analyses=("data_recognition",),
        download_plan_available=True,
        score=55,
        warnings=(),
        source_specific_metadata=metadata,
    )


def _research_topic_search_text(text: str) -> str:
    english_terms, geo_query = _rule_based_research_keywords(text)
    base_lines = [
        f"中文主题：{text}",
        f"英文医学词建议：{english_terms}",
        f"GEO 检索关键词：{geo_query}",
        "使用边界：检索词和候选数据集发现仅辅助选题；不参与统计分析，不生成科研结论。",
    ]
    fetcher_cls = _geo_fetcher_class()
    if fetcher_cls is None:
        return "\n".join(
            [
                *base_lines,
                "当前为检索词生成模式，尚未接入真实数据集在线检索。",
            ]
        )
    try:
        result = fetcher_cls(timeout=8).search_series(geo_query, max_results=5, page_size=5)
    except Exception as exc:
        return "\n".join(
            [
                *base_lines,
                "当前为检索词生成模式；本次在线检索未完成。",
                f"检索提示：{exc}",
            ]
        )
    if not result.results:
        return "\n".join([*base_lines, "在线检索已完成，但未返回候选 GSE 数据集。"])
    candidate_lines = [
        f"{item.gse_id}｜{item.title_en or '未记录标题'}｜样本数：{item.sample_count or '未记录'}｜平台：{item.platform or '未记录'}"
        for item in result.results[:5]
    ]
    return "\n".join([*base_lines, "候选 GSE 数据集：", *candidate_lines])


def _rule_based_research_keywords(text: str) -> tuple[str, str]:
    replacements = {
        "低分化": "poorly differentiated",
        "未分化": "anaplastic",
        "甲状腺癌": "thyroid cancer",
        "甲状腺乳头状癌": "papillary thyroid carcinoma",
        "PTC": "papillary thyroid carcinoma",
        "淋巴结转移": "lymph node metastasis",
        "转移": "metastasis",
        "胆固醇代谢": "cholesterol metabolism",
        "代谢": "metabolism",
        "肿瘤": "cancer",
        "癌": "cancer",
        "表达": "expression",
    }
    terms: list[str] = []
    lowered = text.lower()
    for zh, en in replacements.items():
        if zh.lower() in lowered and en not in terms:
            terms.append(en)
    ascii_tokens = [token for token in text.replace("与", " ").replace("和", " ").replace("、", " ").split() if token.isascii()]
    for token in ascii_tokens:
        if token not in terms:
            terms.append(token)
    if not terms:
        terms = [text]
    english_terms = "; ".join(terms)
    geo_query = f"({' AND '.join(terms)}) AND expression profiling"
    return english_terms, geo_query


def _candidate_source_type(candidate: UnifiedDatasetCandidate) -> str:
    if candidate.source == "geo":
        return "geo_accession"
    if candidate.source == "tcga_gdc":
        return "tcga_project"
    if candidate.source == "gtex":
        return "gtex_tissue"
    return f"topic_search_{candidate.source}"


def _candidate_registration_metadata(
    candidate: UnifiedDatasetCandidate,
    result: BioinformaticsSearchCenterResult | None,
    original_topic: str,
) -> dict[str, object]:
    source_type = _candidate_source_type(candidate)
    generated = _candidate_generated_query_or_mapping(candidate, result)
    metadata: dict[str, object] = {
        "ui_source": "chinese_research_question_search",
        "query_source": "chinese_topic_search",
        "source": candidate.source,
        "source_type": source_type,
        "source_name": candidate.display_title,
        "source_id": candidate.accession_or_project,
        "source_origin": "online_search" if candidate.source == "geo" else "local_mapping",
        "accession_or_project": candidate.accession_or_project,
        "display_title": candidate.display_title,
        "original_chinese_topic": original_topic,
        "generated_query_or_mapping": generated,
        "registration_status": "registered_as_planned_source",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_specific_metadata": candidate.source_specific_metadata,
        "warnings": list(candidate.warnings),
    }
    if candidate.source == "geo":
        source_result = result.source_results.get("geo") if result is not None else None
        registered_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        metadata.update(
            {
                "source_type": "geo_accession",
                "gse_id": candidate.accession_or_project,
                "accession": candidate.accession_or_project,
                "title": candidate.display_title,
                "organism": candidate.organism,
                "sample_count": candidate.sample_count,
                "platform_accessions": list(candidate.source_specific_metadata.get("platform_accessions", [])),
                "geo_url": candidate.source_specific_metadata.get("geo_url", ""),
                "query": generated,
                "query_used": generated,
                "search_time": getattr(source_result, "search_time", "") or candidate.source_specific_metadata.get("search_time", ""),
                "source_database": "NCBI GEO",
                "download_plan_available": candidate.download_plan_available,
                "ready_for_recognition": "pending",
                "registration_handoff": "data_recognition_pending_source_acquisition",
                "audit": {
                    "event_type": "geo_source_registered",
                    "accession": candidate.accession_or_project,
                    "query_used": generated,
                    "registered_at": registered_at,
                    "user_action": "register_geo_search_result_as_source",
                },
            }
        )
    elif candidate.source == "tcga_gdc":
        metadata.update(
            {
                "project_id": candidate.accession_or_project,
                "project_name": candidate.display_title,
            }
        )
    elif candidate.source == "gtex":
        metadata.update(
            {
                "tissue_name": candidate.tissue or candidate.source_specific_metadata.get("tissue_name") or candidate.accession_or_project,
            }
        )
    return metadata


def _candidate_generated_query_or_mapping(
    candidate: UnifiedDatasetCandidate,
    result: BioinformaticsSearchCenterResult | None,
) -> str:
    metadata = candidate.source_specific_metadata
    if candidate.source == "geo":
        query = metadata.get("query_used") or metadata.get("executed_query")
        if query:
            return str(query)
        if result is not None and result.query.geo_query_candidates:
            return result.query.geo_query_candidates[0]
        return candidate.accession_or_project
    if candidate.source == "tcga_gdc":
        return str(metadata.get("project_id") or candidate.accession_or_project)
    if candidate.source == "gtex":
        return str(metadata.get("tissue_name") or candidate.tissue or candidate.accession_or_project)
    return candidate.accession_or_project


def _geo_draft_summary_text(query: object) -> str:
    diseases = ", ".join(getattr(query, "disease_terms_en", ()) or ()) or "未识别疾病"
    data_types = ", ".join(getattr(query, "data_modalities", ()) or getattr(query, "data_type_terms_en", ()) or ()) or "表达谱/RNA-seq/芯片"
    species = ", ".join(getattr(query, "species", ()) or ()) or "Homo sapiens"
    return f"GEO：{diseases} · {data_types} · {species}"


def _topic_summary_text(query: object) -> str:
    diseases_zh = ", ".join(getattr(query, "disease_terms_zh", ()) or ()) or "未识别中文疾病"
    diseases_en = ", ".join(getattr(query, "disease_terms_en", ()) or ()) or "未生成英文疾病词"
    tcga = ", ".join(getattr(query, "tcga_project_ids", ()) or ()) or "无 TCGA 项目草稿"
    gtex = ", ".join(getattr(query, "gtex_tissues", ()) or ()) or "无 GTEx 组织草稿"
    return f"主题识别：{diseases_zh} → {diseases_en}；TCGA：{tcga}；GTEx：{gtex}"


def _candidate_source_bucket(source: str) -> str:
    if source == "tcga_gdc":
        return "tcga_gdc"
    if source == "gtex":
        return "gtex"
    return "geo"


def _registered_source_bucket(row: RegisteredSourceRow) -> str:
    source_type = row.source_type_key
    if "tcga" in source_type:
        return "tcga_gdc"
    if "gtex" in source_type:
        return "gtex"
    return "geo"


def _candidate_modality_label(candidate: UnifiedDatasetCandidate) -> str:
    metadata = candidate.source_specific_metadata
    platform = metadata.get("platform_accessions") or metadata.get("platform_titles")
    if isinstance(platform, list) and platform:
        return f"{candidate.data_modality} / {', '.join(str(item) for item in platform[:2])}"
    if platform:
        return f"{candidate.data_modality} / {platform}"
    return candidate.data_modality or "待确认"


def _candidate_match_reason(candidate: UnifiedDatasetCandidate) -> str:
    metadata = candidate.source_specific_metadata
    for key in ("match_reason", "mapping_status", "recommended_usage"):
        value = metadata.get(key)
        if value:
            return str(value)
    if candidate.source == "tcga_gdc":
        return "疾病词映射到 TCGA/GDC 项目"
    if candidate.source == "gtex":
        return "组织词映射到 GTEx 正常组织参考"
    return "与当前检索词匹配"


def _geo_detail_basic_rows(candidate: UnifiedDatasetCandidate) -> list[list[object]]:
    metadata = candidate.source_specific_metadata
    platforms = _geo_platform_summary(metadata) or "未记录"
    organism_display = str(metadata.get("organism_display_name") or get_organism_display_name(candidate.organism))
    return [
        ["GSE 编号", candidate.accession_or_project],
        ["英文标题", candidate.display_title or "未记录"],
        ["数据来源", "GEO"],
        ["物种", organism_display],
        ["样本数", candidate.sample_count or "待确认"],
        ["平台", platforms],
        ["数据类型", _geo_data_type_display(metadata.get("experiment_type") or candidate.data_modality)],
        ["公开日期", metadata.get("public_date") or metadata.get("status") or "未记录"],
        ["匹配原因", _candidate_match_reason(candidate)],
        ["分析潜力", _geo_candidate_potential_text(None, candidate)],
        ["GEO 链接", metadata.get("geo_url") or f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={candidate.accession_or_project}"],
    ]


def _geo_detail_english_text(candidate: UnifiedDatasetCandidate) -> str:
    metadata = candidate.source_specific_metadata
    summary = str(metadata.get("summary_en") or "").strip()
    design = str(metadata.get("overall_design_en") or metadata.get("sample_summary") or "").strip()
    contributors = metadata.get("contributors")
    if isinstance(contributors, list):
        contributor_text = ", ".join(str(item) for item in contributors[:8] if str(item).strip()) or "未记录"
    else:
        contributor_text = str(contributors or "未记录")
    lines = [
        f"English title：{metadata.get('title_en') or candidate.display_title or '未记录'}",
        f"Summary：{summary or '未记录'}",
        f"Overall design：{design or '未记录'}",
        f"样本数量：{candidate.sample_count or '待确认'}",
        f"平台信息：{_geo_platform_summary(metadata) or '未记录'}",
        f"实验类型：{metadata.get('experiment_type') or candidate.data_modality or '待确认'}",
        f"Contributors：{contributor_text}",
        f"Citation：{metadata.get('citation') or '未记录'}",
        f"PMID：{metadata.get('pmid') or metadata.get('pubmed_id') or '未记录'}",
        f"BioProject：{metadata.get('bioproject') or '未记录'}",
        f"SuperSeries：{metadata.get('superseries') or '未记录'}",
        f"原始关键词：{metadata.get('query_used') or metadata.get('executed_query') or '未记录'}",
        f"GEO link：{metadata.get('geo_url') or '未记录'}",
    ]
    return "\n".join(lines)


def _geo_platform_summary(metadata: dict[str, object]) -> str:
    platforms = metadata.get("platforms")
    if isinstance(platforms, list) and platforms:
        rows: list[str] = []
        for item in platforms:
            if not isinstance(item, dict):
                continue
            accession = str(item.get("accession") or "").strip()
            title = str(item.get("title") or "").strip()
            if accession and title:
                rows.append(f"{accession}，{title}")
            elif accession:
                rows.append(accession)
            elif title:
                rows.append(title)
        if rows:
            return "；".join(rows)
    accessions = metadata.get("platform_accessions")
    titles = metadata.get("platform_titles")
    if isinstance(accessions, list):
        rows = []
        for index, accession in enumerate(accessions):
            title = str(titles[index]) if isinstance(titles, list) and index < len(titles) else ""
            rows.append(f"{accession}，{title}" if title else str(accession))
        return "；".join(row for row in rows if row.strip())
    if isinstance(titles, list):
        return "；".join(str(item) for item in titles if str(item).strip())
    return str(accessions or titles or "").strip()


def _geo_data_type_display(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "待确认"
    lowered = text.lower()
    if "array" in lowered or "microarray" in lowered:
        return f"芯片表达谱（{text}）"
    if "rna-seq" in lowered or "sequencing" in lowered:
        return f"测序表达谱（{text}）"
    if "single-cell" in lowered or "single cell" in lowered:
        return f"单细胞数据（{text}）"
    return text


def _geo_candidate_potential_text(project_root: Path | None, candidate: UnifiedDatasetCandidate) -> str:
    try:
        profile = _build_geo_detail_profile(project_root, candidate, None)
    except Exception:
        return _candidate_recommendation(candidate)
    summary = profile.sample_structure_preview.get("sample_types") if isinstance(profile.sample_structure_preview, dict) else {}
    if isinstance(summary, dict) and summary:
        groups = " / ".join(f"{key} {value}" for key, value in summary.items())
        return f"{profile.analysis_potential_level} · {groups}"
    return profile.analysis_potential_level


def _build_geo_detail_profile(
    project_root: Path | None,
    candidate: UnifiedDatasetCandidate,
    summary_payload: dict[str, object] | None = None,
) -> GeoDatasetProfile:
    recognition_report = _geo_recognition_report_for_accession(project_root, candidate.accession_or_project)
    return GeoDatasetProfileService().build_profile(
        accession=candidate.accession_or_project,
        candidate_metadata={
            **dict(candidate.source_specific_metadata),
            "display_title": candidate.display_title,
            "organism": candidate.organism,
            "data_type": candidate.data_modality,
            "sample_count": candidate.sample_count,
        },
        project_root=project_root,
        summary_payload=dict(summary_payload or {}),
        recognition_report=recognition_report,
    )


def _geo_recognition_report_for_accession(project_root: Path | None, accession: str) -> dict[str, object] | None:
    if project_root is None:
        return None
    report = load_recognition_report(project_root)
    if not isinstance(report, dict):
        return None
    accession_key = str(accession or "").upper()
    files = report.get("files")
    if not isinstance(files, list) or not files:
        return None
    for record in files:
        if not isinstance(record, dict):
            continue
        path_text = " ".join(str(record.get(key) or "") for key in ("original_path", "route_path", "file_name")).upper()
        if accession_key and accession_key in path_text:
            return report
    return None


def _geo_profile_user_display(profile: GeoDatasetProfile, candidate: UnifiedDatasetCandidate | None = None) -> str:
    lines = [
        f"分析潜力：{profile.analysis_potential_level}",
        f"判断依据：{profile.analysis_potential_reason or '结构化元数据不足，需人工判断。'}",
    ]
    preview = profile.sample_structure_preview
    geo_count = preview.get("geo_sample_count") or profile.geo_sample_count or "待确认"
    metadata_count = preview.get("metadata_sample_count") or profile.metadata_sample_count or 0
    if profile.analysis_availability_status:
        lines.append(
            "样本数："
            f"GEO {geo_count}；元数据 {metadata_count}；表达矩阵 {profile.expression_sample_count}；匹配 {profile.matched_sample_count}。"
        )
        lines.append(f"下载后可用性：{profile.analysis_availability_status}")
    else:
        lines.append(f"样本数：GEO {geo_count}；元数据 {metadata_count}。")
    sample_types = preview.get("sample_types") if isinstance(preview, dict) else {}
    if isinstance(sample_types, dict) and sample_types:
        group_text = "，".join(f"{group_label_zh(str(key))} {value} 个" for key, value in sample_types.items())
        lines.append(f"样本结构预览：可能包括 {group_text}。")
    else:
        lines.append("样本结构预览：尚未识别明确分组。")
    if profile.candidate_comparisons:
        lines.append("候选比较组：")
        for comparison in profile.candidate_comparisons[:3]:
            case_label = group_label_zh(comparison.case_group)
            control_label = group_label_zh(comparison.control_group)
            groups = "，".join(f"{group_label_zh(str(key))} {value} 个" for key, value in comparison.group_sizes.items())
            evidence_field = _geo_comparison_evidence_field(comparison)
            lines.append(f"- 候选比较组：{case_label} vs {control_label}")
            lines.append(f"  样本数：{groups}")
            lines.append(f"  置信度：{_confidence_zh(comparison.confidence)}；需用户确认")
            lines.append(f"  判断依据：样本注释中的{evidence_field_label_zh(evidence_field)}")
            for assignment in comparison.sample_assignments[:5]:
                lines.append(
                    f"  · {assignment.sample_accession} → {group_label_zh(assignment.assigned_group)}"
                    f"（证据详情：{evidence_field_label_zh(assignment.evidence_field)} = {assignment.evidence_text[:80]}）"
                )
    else:
        lines.append("候选比较组：未识别到明确候选比较组。")
    if candidate is not None:
        lines.extend(_geo_detail_sample_platform_download_lines(candidate))
    lines.extend(_geo_download_recommendation_lines(profile))
    if profile.supplementary_file_preview:
        lines.append("补充文件预览：")
        for item in profile.supplementary_file_preview[:5]:
            size = _format_file_size(item.file_size) if item.file_size else "大小未知"
            lines.append(f"- {item.file_name}：{item.predicted_type}；风险：{item.risk_level}；{size}；{item.recommendation}")
    if profile.chinese_brief:
        lines.append(f"中文提炼：{profile.chinese_brief}")
    if profile.consistency_review.get("status") == "needs_review":
        lines.append("复核提示：GEO 页面描述与下载文件识别结果不完全一致，请人工确认比较组。")
    elif profile.consistency_review.get("status") == "consistent":
        lines.append("页面与文件识别：当前未发现明显冲突。")
    warnings = [warning for warning in profile.warnings if warning]
    if warnings:
        lines.append("提示：" + "；".join(warnings[:3]))
    return "\n".join(lines)


def _geo_detail_sample_platform_download_lines(candidate: UnifiedDatasetCandidate) -> list[str]:
    metadata = candidate.source_specific_metadata
    lines: list[str] = []
    platforms = _geo_platform_summary(metadata)
    if platforms:
        lines.append(f"平台：{platforms}")
    sample_preview = metadata.get("sample_preview")
    if isinstance(sample_preview, list) and sample_preview:
        lines.append("样本预览：")
        for item in sample_preview[:20]:
            if not isinstance(item, dict):
                continue
            accession = str(item.get("accession") or "")
            title = str(item.get("title") or "")
            chars = item.get("characteristics")
            char_text = ""
            if isinstance(chars, list) and chars:
                char_text = "；" + "；".join(str(value) for value in chars[:2] if str(value).strip())
            lines.append(f"- {accession}：{title}{char_text}".rstrip("："))
        if len(sample_preview) > 20:
            lines.append(f"- 另有 {len(sample_preview) - 20} 个样本。")
    supplementary = metadata.get("supplementary_files")
    if isinstance(supplementary, list) and supplementary:
        lines.append("下载文件：")
        for item in supplementary[:8]:
            if not isinstance(item, dict):
                continue
            name = str(item.get("file_name") or "")
            size = str(item.get("file_size") or "")
            file_type = str(item.get("file_type") or "")
            detail = "，".join(value for value in (file_type, size) if value)
            lines.append(f"- {name}：{detail or 'GEO supplementary file'}")
    download_links = metadata.get("download_links")
    if isinstance(download_links, list) and download_links:
        labels = [str(item.get("label") or "") for item in download_links if isinstance(item, dict) and str(item.get("label") or "").strip()]
        if labels:
            lines.append("处理数据：可查看 " + " / ".join(dict.fromkeys(labels)))
    title_and_design = " ".join(str(metadata.get(key) or "") for key in ("title_en", "summary_en", "overall_design_en")).lower()
    if "cd4" in title_and_design and ("anti-cd3" in title_and_design or "activation" in title_and_design):
        lines.append("分析建议：该数据包含 CD4+ T 细胞静息和多种刺激条件；后续分组识别需要读取 GSM title/characteristics，不能只凭 GSE 标题判断。")
    return lines


def _geo_sample_overview_for_summary(metadata: dict[str, object]) -> str:
    sample_preview = metadata.get("sample_preview")
    if not isinstance(sample_preview, list):
        return ""
    lines: list[str] = []
    for item in sample_preview[:20]:
        if not isinstance(item, dict):
            continue
        accession = str(item.get("accession") or "")
        title = str(item.get("title") or "")
        characteristics = item.get("characteristics")
        chars = ""
        if isinstance(characteristics, list) and characteristics:
            chars = "; ".join(str(value) for value in characteristics[:3] if str(value).strip())
        line = " | ".join(value for value in (accession, title, chars) if value)
        if line:
            lines.append(line)
    return "\n".join(lines)


def _geo_comparison_evidence_field(comparison: object) -> str:
    assignments = list(getattr(comparison, "sample_assignments", ()) or ())
    if assignments:
        return str(getattr(assignments[0], "evidence_field", "") or "")
    comparison_id = str(getattr(comparison, "comparison_id", "") or "")
    return comparison_id.split(":", 1)[0]


def _geo_download_recommendation_lines(profile: GeoDatasetProfile) -> list[str]:
    buckets = {
        "推荐下载：元数据/样本注释": [],
        "可能用于分析：表达矩阵或标准化表达文件": [],
        "不建议默认下载：raw/CEL/大文件/SRA 原始数据": [],
    }
    for item in profile.supplementary_file_preview:
        name = item.file_name
        if not name:
            continue
        label = name
        if item.asset_type == "series_matrix":
            label = f"{name}（可能包含表达矩阵或样本注释，需下载后确认）"
        elif item.predicted_type == "expression_matrix":
            label = f"{name}（可能包含表达矩阵，需下载后确认）"
        elif item.predicted_type in {"metadata_container", "sample_metadata", "clinical_metadata", "platform_annotation"}:
            label = f"{name}（{item.recommendation}）"
        elif item.predicted_type == "raw_data" or item.risk_level in {"中", "高"}:
            label = f"{name}（{item.recommendation}）"
        if item.predicted_type == "raw_data" or item.risk_level in {"中", "高"}:
            buckets["不建议默认下载：raw/CEL/大文件/SRA 原始数据"].append(label)
        elif item.predicted_type in {"metadata_container", "sample_metadata", "clinical_metadata", "platform_annotation"} and item.asset_type != "series_matrix":
            buckets["推荐下载：元数据/样本注释"].append(label)
        elif item.predicted_type == "expression_matrix" or item.asset_type == "series_matrix":
            buckets["可能用于分析：表达矩阵或标准化表达文件"].append(label)
        elif item.predicted_type != "unknown":
            buckets["推荐下载：元数据/样本注释"].append(label)
    lines = ["建议下载文件："]
    any_item = False
    for title, values in buckets.items():
        if values:
            any_item = True
            lines.append(f"- {title}：" + "；".join(values[:5]))
    if not any_item:
        lines.append("- 尚未发现明确表达矩阵文件，建议先下载/查看元数据。")
    return lines


def _confidence_zh(value: str) -> str:
    return {"high": "高", "medium": "中", "low": "低"}.get(str(value), str(value) or "待确认")


def _format_file_size(size: object) -> str:
    try:
        value = int(size)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "大小未知"
    if value >= 1024 * 1024 * 1024:
        return f"{value / (1024 * 1024 * 1024):.1f} GB"
    if value >= 1024 * 1024:
        return f"{value / (1024 * 1024):.1f} MB"
    if value >= 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value} B"


def _slug_text(value: object) -> str:
    return re.sub(r"_+", "_", "".join(character.lower() if character.isalnum() else "_" for character in str(value))).strip("_") or "comparison"


def _comparison_config_text_from_geo_profile(profile: GeoDatasetProfile) -> str:
    if not profile.candidate_comparisons:
        return _template_text_for_missing_input("comparison_config")
    return build_geo_comparison_config_text(profile)


def _geo_comparison_confirmation_prompt(profile: GeoDatasetProfile) -> str:
    if not profile.candidate_comparisons:
        return "请手动填写比较组设置。"
    comparison = profile.candidate_comparisons[0]
    case_label = group_label_zh(comparison.case_group)
    control_label = group_label_zh(comparison.control_group)
    lines = [
        "请确认候选分组是否符合研究设计。确认后才会写入正式比较组设置。",
        "",
        f"候选比较组：{case_label} vs {control_label}",
        f"对照组：{control_label}（{comparison.control_group}）",
        f"实验组：{case_label}（{comparison.case_group}）",
        "每组样本数：" + "，".join(f"{group_label_zh(key)} {value}" for key, value in comparison.group_sizes.items()),
        "样本分配证据：",
    ]
    for assignment in comparison.sample_assignments[:12]:
        lines.append(
            f"- {assignment.sample_accession}: {group_label_zh(assignment.assigned_group)}；"
            f"{evidence_field_label_zh(assignment.evidence_field)} = {assignment.evidence_text[:120]}"
        )
    if len(comparison.sample_assignments) > 12:
        lines.append(f"- 其余 {len(comparison.sample_assignments) - 12} 个样本略。")
    lines.extend(["", "下方 TSV 可编辑。可以调整 case/control、移除样本或修改个别样本分组；确认后才会写入正式比较组。"])
    return "\n".join(lines)


def _save_geo_profile_comparison_with_confirmation(
    parent: QWidget,
    project_root: Path | None,
    candidate: UnifiedDatasetCandidate,
    summary_payload: dict[str, object] | None,
    *,
    manual_text: str | None = None,
    comparison_index: int = 0,
    case_group: str | None = None,
    control_group: str | None = None,
    included_sample_ids: Iterable[str] | None = None,
    assignment_overrides: dict[str, str] | None = None,
    skip_dialog: bool = False,
) -> tuple[bool, str]:
    if project_root is None:
        return False, "请先创建或打开生信分析项目。"
    profile = _build_geo_detail_profile(project_root, candidate, summary_payload)
    if manual_text is None and not profile.candidate_comparisons:
        return False, "该 GEO 数据集尚未检测到可确认的候选分组，请手动设置比较组。"
    text = manual_text or build_geo_comparison_config_text(
        profile,
        comparison_index=comparison_index,
        case_group=case_group,
        control_group=control_group,
        included_sample_ids=included_sample_ids,
        assignment_overrides=assignment_overrides,
    )
    if manual_text is None and not skip_dialog:
        text, ok = QInputDialog.getMultiLineText(
            parent,
            "确认比较组",
            _geo_comparison_confirmation_prompt(profile),
            text,
        )
        if not ok:
            return False, "已取消确认比较组。"
    _save_manual_supplement(project_root, "comparison_config", text)
    _append_geo_profile_confirmation_audit(project_root, profile, text)
    run_project_recognition(project_root)
    run_project_readiness(project_root)
    return True, "已确认候选分组为正式比较组。"


def _append_geo_profile_confirmation_audit(project_root: Path, profile: GeoDatasetProfile, comparison_text: str) -> Path:
    path = project_root / "logs" / "readiness" / "comparison_group_confirmation_log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": _utc_now_iso(),
        "action": "confirm_geo_page_profile_comparison",
        "accession": profile.accession,
        "candidate_comparisons": [item.to_dict() for item in profile.candidate_comparisons],
        "comparison_text": comparison_text,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
    return path


def _geo_asset_detail_text(project_root: Path | None, accession: str) -> str:
    manifest = _candidate_geo_asset_manifest(project_root, accession)
    if not manifest:
        return "\n".join(
            [
                "family SOFT：未发现",
                "Series Matrix：未发现",
                "supplementary files：未发现",
                "表达矩阵：未确认",
                "样本注释：未确认",
                "平台注释：未确认",
                "当前可分析性：元数据待下载",
            ]
        )
    assets = [asset for asset in manifest.get("assets", []) or [] if isinstance(asset, dict)]
    summary = manifest.get("summary", {}) if isinstance(manifest.get("summary"), dict) else {}
    family_status = _asset_type_status(assets, "family_soft")
    matrix_status = _asset_type_status(assets, "series_matrix")
    supplementary = [asset for asset in assets if asset.get("asset_type") == "supplementary_file"]
    downloaded_supplementary = [asset for asset in supplementary if asset.get("status") == "downloaded"]
    if downloaded_supplementary:
        supplementary_text = f"已下载 {len(downloaded_supplementary)} 个"
    elif supplementary:
        supplementary_text = f"已发现 {len(supplementary)} 个"
    else:
        supplementary_text = "未发现"
    expression_status = "已识别" if summary.get("expression_matrix_status") == "downloaded" else ("待下载" if summary.get("series_matrix_discovered") or summary.get("expression_candidate_count") else "未确认")
    sample_status = "已识别" if summary.get("metadata_downloaded") else "未确认"
    platform_status = "已识别" if summary.get("metadata_downloaded") else "未确认"
    current = _geo_asset_status_text({"asset_manifest_summary": summary}) or "仅元数据"
    return "\n".join(
        [
            f"family SOFT：{family_status}",
            f"Series Matrix：{matrix_status}",
            f"supplementary files：{supplementary_text}",
            f"表达矩阵：{expression_status}",
            f"样本注释：{sample_status}",
            f"平台注释：{platform_status}",
            f"当前可分析性：{current}",
        ]
    )


def _asset_type_status(assets: list[dict[str, object]], asset_type: str) -> str:
    matches = [asset for asset in assets if asset.get("asset_type") == asset_type]
    if any(asset.get("status") == "downloaded" for asset in matches):
        return "已下载"
    if matches:
        return "已发现"
    return "未发现"


def _geo_text_summary_user_display(candidate: UnifiedDatasetCandidate, summary: dict[str, object]) -> str:
    status = str(summary.get("status") or "")
    warnings = [str(item) for item in summary.get("quality_warnings", []) or []] if isinstance(summary.get("quality_warnings"), list) else list(summary.get("quality_warnings", ()) or ())
    lines = [
        "AI 草稿：中文翻译与提炼，需人工确认。",
        f"中文标题：{summary.get('title_zh') or '未生成'}",
        f"中文摘要：{summary.get('summary_zh') or '未生成'}",
        f"一句话介绍：{summary.get('brief_zh') or '未生成'}",
    ]
    if status != "completed" or warnings or summary.get("error_message"):
        lines.append(f"提示：{summary.get('error_message') or '；'.join(warnings) or 'AI 不可用，已生成 fallback 文案。'}")
    return "\n".join(lines)


def _desktop_local_model_config() -> LocalModelConfig:
    config = load_ai_gateway_config()
    provider_config = config.provider_configs.get("ollama", {})
    enabled = (
        config.default_provider == "ollama"
        and config.allow_network
        and isinstance(provider_config, dict)
        and provider_config.get("enabled") is True
    )
    return LocalModelConfig(
        enabled=enabled,
        provider="ollama",
        base_url=str(provider_config.get("base_url") or ""),
        medical_model=str(provider_config.get("default_model") or DEFAULT_OLLAMA_MODEL),
        translator_model=str(provider_config.get("default_model") or DEFAULT_OLLAMA_MODEL),
        timeout_seconds=int(provider_config.get("timeout_seconds") or 20) if isinstance(provider_config.get("timeout_seconds") or 20, int) else 20,
    )


def _query_draft_output_text(result: BioinformaticsSearchCenterResult) -> str:
    query = result.query
    return "\n".join(
        [
            "识别到的中文概念：" + ("、".join(query.disease_terms_zh) or "未识别"),
            "英文候选词：" + ("; ".join([*query.disease_terms_en, *query.synonyms, *query.data_modalities]) or "未生成"),
            "GEO query draft：" + ("\n".join(query.geo_query_candidates) or "未生成"),
            "TCGA project hint：" + (", ".join(query.tcga_project_ids) or "未生成"),
            "GTEx tissue hint：" + (", ".join(query.gtex_tissues) or "未生成"),
        ]
    )


def _query_draft_summary(result: BioinformaticsSearchCenterResult, *, editable_output: str = "") -> dict[str, object]:
    query = result.query
    summary: dict[str, object] = {
        "recognized_zh_concepts": list(query.disease_terms_zh),
        "english_candidate_terms": list(dict.fromkeys([*query.disease_terms_en, *query.synonyms, *query.data_modalities])),
        "geo_query_draft": list(query.geo_query_candidates),
        "tcga_project_hint": list(query.tcga_project_ids),
        "gtex_tissue_hint": list(query.gtex_tissues),
        "confirmed_draft_text_hash_only": bool(editable_output),
        "search_executed": False,
    }
    return summary


def _geo_text_summary_draft_record(text: GeoStudyTextInput, payload: dict[str, object]) -> AIDraftRecord:
    output_text = "\n".join(
        [
            str(payload.get("title_zh") or ""),
            str(payload.get("summary_zh") or ""),
            str(payload.get("brief_zh") or ""),
        ]
    )
    input_text = "\n".join([text.title_en, text.summary_en, text.overall_design_en, text.sample_overview_en])
    status = "suggested" if payload.get("status") == "completed" else "suggested"
    return create_ai_draft_record(
        module="bioinformatics",
        task_type="bio_translate_dataset_detail",
        provider="ollama" if payload.get("status") == "completed" else "disabled",
        model=" / ".join(str(payload.get(key) or "") for key in ("translate_model", "brief_model")).strip(" / "),
        input_text=input_text,
        output_text=output_text,
        warnings=tuple(str(item) for item in payload.get("quality_warnings", ()) or ()),
        summary={
            "accession": text.accession,
            "status": str(payload.get("status") or ""),
            "title_zh": str(payload.get("title_zh") or ""),
            "summary_zh": str(payload.get("summary_zh") or ""),
            "brief_zh": str(payload.get("brief_zh") or ""),
        },
        status=status,
    )


def _ai_provider_status_label(status: AIProviderStatus) -> str:
    if status == AIProviderStatus.AVAILABLE:
        return "可用"
    if status == AIProviderStatus.DISABLED:
        return "未启用"
    if status == AIProviderStatus.ERROR:
        return "错误"
    return "不可用"


def _geo_topic_match_label(summary: dict[str, object], *, status: str, warnings: list[str]) -> str:
    for key in (
        "topic_match_status",
        "entity_consistency_status",
        "medical_entity_consistency",
        "entity_consistency",
        "consistency",
        "search_topic_match",
        "topic_match",
    ):
        value = summary.get(key)
        if value is None or value == "":
            continue
        normalized = str(value).strip().lower()
        if normalized in {"passed", "pass", "true", "consistent", "yes", "matched"}:
            return "是"
        if normalized in {"warning", "partial", "uncertain", "maybe", "possible"}:
            return "可能相关"
        if normalized in {"failed", "fail", "false", "inconsistent", "no", "mismatch"}:
            return "不明确"
        if normalized in {"missing", "unknown", "none", "not_checked", "not judged"}:
            return "未判断"
    if status == "completed" and not warnings:
        return "是"
    if status == "completed" and warnings:
        return "可能相关"
    return "未判断"


def _recommendation_card_title(candidate: UnifiedDatasetCandidate) -> str:
    if candidate.source == "tcga_gdc":
        return f"{candidate.accession_or_project} · {_tcga_project_zh(candidate)}"
    if candidate.source == "gtex":
        return f"{candidate.tissue or candidate.accession_or_project} · {_gtex_tissue_zh(candidate)}"
    return candidate.display_title or candidate.accession_or_project


def _recommendation_card_fields(candidate: UnifiedDatasetCandidate) -> list[tuple[str, str]]:
    if candidate.source == "tcga_gdc":
        project_id = candidate.accession_or_project
        english_name = _candidate_metadata_value(candidate, "project_name", candidate.display_title or project_id)
        return [
            ("项目代码", project_id),
            ("中文名称", _tcga_project_zh(candidate)),
            ("英文名称", english_name),
            ("数据库", "TCGA/GDC"),
            ("推荐原因", f"当前研究主题与{_tcga_project_topic_zh(candidate)}项目匹配。"),
            ("可用数据", "RNA-seq 表达、临床信息、突变数据"),
            ("适用说明", _tcga_usage_note(candidate)),
        ]
    tissue = candidate.tissue or _candidate_metadata_value(candidate, "tissue_name", candidate.accession_or_project)
    return [
        ("组织名称", tissue),
        ("中文名称", _gtex_tissue_zh(candidate)),
        ("英文名称", tissue),
        ("数据库", "GTEx"),
        ("推荐原因", f"当前研究主题涉及{_gtex_tissue_topic_zh(candidate)}，匹配 GTEx {tissue} 正常组织。"),
        ("可用数据", "正常组织 RNA 表达"),
        ("适用说明", "GTEx 是正常组织表达参考，不是肿瘤样本数据库。"),
    ]


def _tcga_project_zh(candidate: UnifiedDatasetCandidate) -> str:
    mapping = {
        "TCGA-GBM": "胶质母细胞瘤队列",
        "TCGA-LGG": "低级别胶质瘤队列",
        "TCGA-THCA": "甲状腺癌队列",
        "TCGA-ESCA": "食管癌队列",
        "TCGA-LUAD": "肺腺癌队列",
        "TCGA-LUSC": "肺鳞癌队列",
        "TCGA-LIHC": "肝细胞癌队列",
        "TCGA-BRCA": "乳腺癌队列",
        "TCGA-PRAD": "前列腺癌队列",
        "TCGA-OV": "卵巢癌队列",
        "TCGA-CESC": "宫颈癌队列",
        "TCGA-UCEC": "子宫内膜癌队列",
        "TCGA-KIRC": "肾透明细胞癌队列",
        "TCGA-BLCA": "膀胱癌队列",
        "TCGA-SKCM": "黑色素瘤队列",
        "TCGA-STAD": "胃癌队列",
        "TCGA-COAD": "结肠癌队列",
        "TCGA-READ": "直肠癌队列",
        "TCGA-PAAD": "胰腺癌队列",
    }
    return mapping.get(candidate.accession_or_project, f"{_candidate_metadata_value(candidate, 'project_name', candidate.display_title or candidate.accession_or_project)} 队列")


def _tcga_project_topic_zh(candidate: UnifiedDatasetCandidate) -> str:
    zh = _tcga_project_zh(candidate)
    return zh[:-2] if zh.endswith("队列") else zh


def _tcga_usage_note(candidate: UnifiedDatasetCandidate) -> str:
    tissue = _candidate_metadata_value(candidate, "primary_site", candidate.tissue)
    if tissue:
        return f"适合肿瘤样本分析；如需正常组织对照，可结合 GTEx {tissue}。"
    return "适合肿瘤样本分析；如需正常组织对照，可结合 GTEx 正常组织参考。"


def _gtex_tissue_zh(candidate: UnifiedDatasetCandidate) -> str:
    tissue = str(candidate.tissue or candidate.source_specific_metadata.get("tissue_name") or candidate.accession_or_project)
    mapping = {
        "Thyroid": "甲状腺组织",
        "Brain": "脑组织",
        "Liver": "肝脏组织",
        "Lung": "肺组织",
        "Esophagus": "食管组织",
        "Breast": "乳腺组织",
        "Prostate": "前列腺组织",
        "Ovary": "卵巢组织",
        "Kidney": "肾组织",
        "Colon": "结肠组织",
        "Stomach": "胃组织",
        "Pancreas": "胰腺组织",
        "Skin": "皮肤组织",
    }
    return mapping.get(tissue, f"{tissue} 组织")


def _gtex_tissue_topic_zh(candidate: UnifiedDatasetCandidate) -> str:
    zh = _gtex_tissue_zh(candidate)
    return zh[:-2] if zh.endswith("组织") else zh


def _candidate_detail_text(candidate: UnifiedDatasetCandidate, project_root: Path | None, brief: dict[str, object] | None = None) -> str:
    metadata = candidate.source_specific_metadata
    status = _candidate_record_status_text(project_root, candidate.source, candidate.accession_or_project) or "未选择"
    lines = [
        f"编号/项目/组织：{candidate.accession_or_project}",
        f"完整标题：{candidate.display_title or '未记录'}",
        f"英文标题：{metadata.get('title_en') or candidate.display_title or '未记录'}",
        f"中文简介：{(brief or {}).get('brief_zh') or '未生成'}",
        f"匹配原因：{_candidate_match_reason(candidate)}",
        f"推荐等级：{_candidate_recommendation(candidate)}",
        f"样本数：{candidate.sample_count or '待确认'}",
        f"数据类型：{candidate.data_modality or '待确认'}",
        f"资产状态：{status}",
            f"下载/添加建议：{_candidate_next_action_text(candidate, status)}",
        f"风险提示：{_candidate_risk_text(candidate, status)}",
    ]
    if candidate.source == "geo":
        manifest = _candidate_geo_asset_manifest(project_root, candidate.accession_or_project)
        summary = manifest.get("summary", {}) if isinstance(manifest, dict) else {}
        lines.extend(
            [
                f"是否仅有 metadata：{'是' if '元数据已下载' in status and '表达矩阵已下载' not in status else '待确认'}",
                f"是否发现表达矩阵：{'是' if summary.get('series_matrix_discovered') or summary.get('expression_candidate_count') or summary.get('expression_matrix_status') == 'downloaded' else '否'}",
                f"是否发现 supplementary files：{'是' if summary.get('supplementary_files_discovered') or summary.get('supplementary_files_downloaded') else '否'}",
            ]
        )
    return "\n".join(lines)


def _candidate_next_action_text(candidate: UnifiedDatasetCandidate, status: str) -> str:
    if "可进入识别" in status and "待确认" not in status and "待下载" not in status:
        return "可进入数据识别。"
    if candidate.source == "geo":
        if "已发现补充文件" in status or "表达矩阵待确认" in status or "表达矩阵待下载" in status:
            return "下载补充文件或 Series Matrix 后再进入数据识别。"
        return "先下载并添加 GEO 元数据。"
    if candidate.source in {"tcga_gdc", "gtex"}:
        return "当前先生成计划来源，后续接入真实下载。"
    return "选择后进入后续数据处理。"


def _candidate_risk_text(candidate: UnifiedDatasetCandidate, status: str) -> str:
    if candidate.source == "geo" and ("表达矩阵待确认" in status or "表达矩阵待下载" in status):
        return "当前可能只有 family SOFT metadata，仍需确认表达矩阵或补充文件。"
    if candidate.source in {"tcga_gdc", "gtex"}:
        return "本地映射仅表示候选项目/组织匹配，不代表数据文件已下载。"
    return "需在数据识别页确认文件内容和资产角色。"


def _candidate_metadata_value(candidate: UnifiedDatasetCandidate, key: str, fallback: object = "") -> str:
    value = candidate.source_specific_metadata.get(key)
    if value is None or value == "":
        value = fallback
    return str(value or "")


def _candidate_recommendation(candidate: UnifiedDatasetCandidate) -> str:
    if candidate.score >= 80:
        return "高"
    if candidate.score >= 55:
        return "中"
    return "低"


def _registered_row_rank(row: RegisteredSourceRow) -> tuple[int, str]:
    status = row.status
    score = 0
    if "可进入识别" in status or "已下载" in status:
        score = 3
    elif "元数据已下载" in status:
        score = 2
    elif "待下载" in status or "已登记" in status or "已添加" in status:
        score = 1
    return score, row.created_at


def _current_registered_row_status(project_root: Path | None, row: RegisteredSourceRow) -> str:
    if row.source_type_key in {"geo_accession", "geo_search_candidate", "chinese_geo_gse"}:
        status = _candidate_record_status_text(project_root, "geo", row.source_label)
        if status:
            return status
    return row.status


def _registered_existing_assets(row: RegisteredSourceRow, status: str | None = None) -> str:
    status = status or row.status
    assets: list[str] = []
    if "元数据已下载" in status:
        assets.append("metadata")
    if "表达矩阵已下载" in status:
        assets.append("表达矩阵")
    if "补充文件已下载" in status:
        assets.append("补充文件")
    if not assets and row.strategy != "plan_only":
        assets.append("本地文件")
    return "、".join(assets) if assets else "待下载"


def _registered_missing_assets(row: RegisteredSourceRow, status: str | None = None) -> str:
    status = status or row.status
    if "可进入识别" in status and "待确认" not in status and "待下载" not in status:
        return "无明确缺失"
    if "表达矩阵待确认" in status or "表达矩阵待下载" in status:
        return "表达矩阵"
    if "待下载" in status:
        return "数据文件"
    return "待识别确认"


def _registered_next_step(row: RegisteredSourceRow, status: str | None = None) -> str:
    status = status or row.status
    if "可进入识别" in status and "表达矩阵待下载" not in status and "表达矩阵待确认" not in status:
        return "进入数据识别"
    if "表达矩阵待确认" in status or "表达矩阵待下载" in status or "已发现补充文件" in status:
        return "下载补充文件"
    if "待下载" in status:
        return "补全数据文件"
    return "查看详情"


def _geo_empty_state_text(source_result: object | None, *, searched: bool) -> str:
    status = str(getattr(source_result, "search_status", "") or "")
    if status == "disease_terms_missing":
        return "未生成 GEO/GSE 检索草稿，请补充明确疾病或组织主题。"
    if not searched:
        return "已生成 GEO/GSE 检索草稿，尚未执行在线检索。"
    if status == "search_failed":
        return "GEO/GSE 在线检索失败，请检查网络或稍后重试。"
    if status in {"draft_only", "disease_terms_missing", ""}:
        return "已生成 GEO/GSE 检索草稿，尚未执行在线检索。"
    return "未检索到符合条件的 GEO/GSE 数据集。"


def _merge_source_search_result(
    base: BioinformaticsSearchCenterResult,
    source: str,
    source_result: SourceSearchResult,
    *,
    online_enabled: bool,
) -> BioinformaticsSearchCenterResult:
    source_results = dict(base.source_results)
    source_results[source] = source_result
    candidates = tuple(
        [
            *[candidate for candidate in base.candidates if candidate.source != source],
            *source_result.candidates,
        ]
    )
    warnings = tuple(dict.fromkeys([*base.warnings, *source_result.warnings]))
    return BioinformaticsSearchCenterResult(
        query=base.query,
        source_results=source_results,
        candidates=candidates,
        online_enabled=online_enabled,
        search_time=source_result.search_time or base.search_time,
        warnings=warnings,
    )


def _mapping_log_text(result: BioinformaticsSearchCenterResult) -> str:
    query = result.query
    return _json(
        {
            "中文概念识别": list(query.disease_terms_zh),
            "英文医学术语映射": list(query.disease_terms_en),
            "同义词扩展": list(query.synonyms),
            "词库命中": query.metadata.get("search_translation_draft"),
            "GEO query 构建过程": list(query.geo_query_candidates),
            "TCGA query 构建过程": list(query.tcga_project_ids),
            "GTEx query 构建过程": list(query.gtex_tissues),
            "本地模型输出": {
                "local_model_status": query.metadata.get("local_model_status"),
                "local_model_used": query.metadata.get("local_model_used"),
            },
            "错误和警告": list(result.warnings),
        }
    )


def _geo_text_summary_display(candidate: UnifiedDatasetCandidate, summary: dict[str, object]) -> str:
    metadata = candidate.source_specific_metadata
    model_status = summary.get("model_status") if isinstance(summary.get("model_status"), dict) else {}
    warnings = summary.get("quality_warnings") if isinstance(summary.get("quality_warnings"), (list, tuple)) else ()
    return "\n".join(
        [
            f"GSE：{candidate.accession_or_project}",
            f"英文标题：{metadata.get('title_en') or candidate.display_title or '未记录'}",
            f"英文摘要：{metadata.get('summary_en') or '未记录'}",
            f"中文标题：{summary.get('title_zh') or '未生成'}",
            f"中文摘要：{summary.get('summary_zh') or '未生成'}",
            f"中文一句话简介：{summary.get('brief_zh') or '未生成'}",
            f"翻译模型：{summary.get('translate_model') or model_status.get('translate_model') or '未配置'}（{model_status.get('translate_model_status') or '未检查'}）",
            f"医学提炼模型：{summary.get('brief_model') or model_status.get('brief_model') or '未配置'}（{model_status.get('brief_model_status') or '未检查'}）",
            f"质量提示：{'；'.join(str(item) for item in warnings) if warnings else '无'}",
            f"处理状态：{summary.get('status') or 'unknown'}",
            f"提示：{summary.get('error_message') or '无'}",
        ]
    )


def _global_source_summary_text(summary: SelectedSourceSummary) -> str:
    if summary.selected_kind == "accession":
        return (
            f"最近添加的数据：GSE 编号检索；来源内容：{summary.display_name}；"
            f"保存方式：{_storage_policy_text(summary.storage_policy)}；数据状态：需要补充数据；"
            "下一步：导入已下载的 Series Matrix 文件，或等待后续版本接入自动下载。"
        )
    return (
        f"最近添加的数据：{summary.source_label}；来源内容：{summary.display_name}；"
        f"来源位置：{_compact_path(summary.absolute_path)}；保存方式：{_storage_policy_text(summary.storage_policy)}；数据状态：已完成。"
    )


def _selected_source_technical_details(summary: SelectedSourceSummary) -> str:
    return _json(
        {
            "source_type": summary.source_type,
            "source_label": summary.source_label,
            "selected_kind": summary.selected_kind,
            "source_path": summary.absolute_path or "未记录来源位置",
            "storage_policy": summary.storage_policy,
            "acquisition_plan_path": summary.acquisition_plan_path,
            "acquisition_record_path": summary.acquisition_record_path,
            "handoff_path": summary.handoff_path,
            "raw_data_path": str(Path(summary.acquisition_plan_path).parents[2] / "raw_data") if summary.acquisition_plan_path else "未记录",
            "warnings": list(summary.warnings),
            "manifest_registration": "UI-04 registration summary only; acquisition contract unchanged.",
        }
    )


def _acquisition_user_summary(summary: AcquisitionSummary | None, artifacts: dict[str, object], project_root: Path) -> str:
    if summary is None:
        return "尚未生成数据获取记录。\n下一步建议：返回数据来源选择页，选择本地文件/文件夹或生成获取计划。"
    plan = artifacts.get("plan")
    record = artifacts.get("record")
    handoff = artifacts.get("handoff")
    file_count = len(summary.registered_files) + len(summary.copied_files) + len(summary.referenced_paths)
    next_step = "可以继续进入数据识别。" if summary.strategy != "plan_only" and file_count else "当前只是获取计划或缺少实际文件，请补充本地文件后再继续。"
    warnings = "；".join(summary.warnings) if summary.warnings else "无"
    return "\n".join(
        [
            f"数据来源：{summary.source_type} / {summary.source_label}",
            f"策略：{summary.strategy}",
            f"状态：{summary.status}",
            f"文件数量：{file_count} 个",
            f"acquisition plan：{'已生成' if plan else '不存在'}",
            f"standardization handoff：{'已生成' if handoff else '不存在'}",
            f"acquisition record：{'已生成' if record else '不存在'}",
            f"原始数据位置：{project_root / 'raw_data'}",
            f"warning：{warnings}",
            f"下一步建议：{next_step}",
        ]
    )


def _readiness_user_summary(readiness: dict[str, object], matrix: dict[str, object]) -> str:
    status = str(readiness.get("overall_status") or "unavailable")
    available = [str(item) for item in readiness.get("available_inputs", []) or []]
    warnings = [str(item) for item in readiness.get("warnings", []) or []]
    rows = [row for row in matrix.get("rows", []) or [] if isinstance(row, dict)]
    runnable = [str(row.get("label")) for row in rows if row.get("can_run")]
    blocked = [str(row.get("label")) for row in rows if not row.get("can_run")]
    return "\n".join(
        [
            f"总体状态：{readiness_status_zh(status)}",
            f"核心输入：{'已识别' if readiness.get('has_core_input') else '未识别'}",
            f"已存在数据：{'、'.join(available) if available else '无'}",
            f"可运行分析：{'、'.join(runnable) if runnable else '暂无'}",
            f"暂不可运行：{'、'.join(blocked) if blocked else '无'}",
            f"关键警告：{'；'.join(warnings) if warnings else '无'}",
        ]
    )


def _readiness_warning_chips(readiness: dict[str, object], matrix: dict[str, object]) -> str:
    return _readiness_default_warning_summary(readiness, matrix, _missing_readiness_inputs(readiness, matrix))


def _supplement_hint_text(readiness: dict[str, object], matrix: dict[str, object]) -> str:
    missing = [_missing_input_label(item) for item in _missing_readiness_inputs(readiness, matrix)]
    if not missing:
        return "当前没有必须补充的信息。可以继续生成标准化数据。"
    return "检测到缺失信息：" + "、".join(missing) + "。请在待办清单中处理后点击“重新检查”。"


def _readiness_overall_summary(readiness: dict[str, object], matrix: dict[str, object], missing: set[str]) -> str:
    has_core_input = bool(readiness.get("has_core_input"))
    rows = [row for row in matrix.get("rows", []) or [] if isinstance(row, dict)]
    runnable = [row for row in rows if row.get("can_run") and row.get("analysis_type") != "reporting"]
    if not has_core_input:
        return "暂不能继续：还没有可用的表达矩阵。"
    if runnable and not missing:
        return "可以继续：关键输入已基本满足。"
    if runnable:
        return "基本可继续，但有信息需要补充。"
    return "暂不能继续：关键输入还不完整。"


def _readiness_recognized_inputs_text(readiness: dict[str, object]) -> str:
    available = {str(item) for item in readiness.get("available_inputs", []) or []}
    labels = []
    for key in ("expression_matrix", "sample_metadata", "clinical_metadata", "platform_annotation", "gene_annotation", "comparison_config", "gmt_gene_set"):
        if key == "expression_matrix" and available & {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix"}:
            labels.append("表达矩阵")
        elif key in available:
            labels.append(_missing_input_label(key))
    return "已识别到的数据：" + ("、".join(dict.fromkeys(labels)) if labels else "尚未识别到关键数据")


def _readiness_missing_inputs_text(missing: set[str], group_preview: dict[str, object] | None = None) -> str:
    if not missing:
        return "仍需补充的数据：无"
    labels = []
    for key in _ordered_missing_inputs(missing):
        if key == "comparison_config" and _group_preview_has_candidate(group_preview):
            labels.append("比较分组（候选分组待确认）")
        else:
            labels.append(_missing_input_label(key))
    return "仍需补充的数据：" + "、".join(labels)


def _readiness_next_step_text(
    readiness: dict[str, object],
    matrix: dict[str, object],
    missing: set[str],
    group_preview: dict[str, object] | None = None,
) -> str:
    has_core_input = bool(readiness.get("has_core_input"))
    available = {str(item) for item in readiness.get("available_inputs", []) or []}
    comparison_status = str(readiness.get("comparison_group_status") or "")
    if comparison_status == "confirmed_missing_expression":
        summary = str(readiness.get("comparison_group_summary_zh") or "比较组已确认。")
        return f"下一步建议：{summary}但缺少表达矩阵，请补充表达矩阵。"
    if comparison_status == "confirmed_sample_mismatch":
        return "下一步建议：比较组已确认，但表达矩阵样本 ID 不匹配。请修正比较组或选择其他表达文件。"
    if comparison_status == "confirmed_ready":
        summary = str(readiness.get("comparison_group_summary_zh") or "比较组已确认。")
        return f"下一步建议：{summary}可以进入标准化，并在分析中心运行差异表达分析。"
    if "expression_matrix" in missing or not has_core_input:
        return "下一步建议：请返回数据导入页面补充表达矩阵文件。"
    if "comparison_config" in missing and _group_preview_has_candidate(group_preview):
        return "下一步建议：已检测到候选分组，请确认比较组；也可以先进入标准化，之后再确认。"
    if "comparison_config" in missing and "sample_metadata" not in missing:
        return "下一步建议：建议先设置比较组，以便进行差异表达分析；也可以先进入标准化，之后再补充分组信息。"
    if "sample_metadata" in missing:
        return "下一步建议：请补充样本信息；如果暂时只做表达矩阵清洗，也可以先进入标准化。"
    if missing == {"gmt_gene_set"}:
        return "下一步建议：GSEA 需要 GMT 基因集文件；不做 GSEA 时可暂时忽略。"
    if "clinical_metadata" in missing and missing <= {"clinical_metadata", "gmt_gene_set"}:
        return "下一步建议：临床信息只影响生存分析和临床变量关联；不做这些分析时可以先进入标准化。"
    if available:
        return "下一步建议：可以先进入标准化数据；后续再按分析目标补充待办项。"
    return "下一步建议：请先补充关键数据文件。"


def _readiness_default_warning_summary(readiness: dict[str, object], matrix: dict[str, object], missing: set[str]) -> str:
    warnings = [str(item) for item in readiness.get("warnings", []) or []]
    technical_warnings = [
        warning
        for warning in warnings
        if any(token in warning.lower() for token in ("numeric density", "sample-like", "payload", "asset_manifest", "manifest.json", "too few columns"))
    ]
    blocking = [label for label in (_missing_input_label(item) for item in _ordered_missing_inputs(missing)) if label]
    if technical_warnings and readiness.get("has_core_input"):
        return f"提示：有 {len(technical_warnings)} 条文件识别提示已放入技术详情。当前已找到可用表达矩阵时，这类提示通常不影响继续。"
    if blocking:
        return "提示：会影响部分分析的待办项：" + "、".join(blocking) + "。"
    if warnings:
        return f"提示：有 {len(warnings)} 条需注意信息，详情可在“技术详情”中查看。"
    return "提示：默认区域未发现需要处理的警告。"


def _ordered_missing_inputs(missing: set[str]) -> list[str]:
    order = ["expression_matrix", "sample_metadata", "comparison_config", "gmt_gene_set", "clinical_metadata"]
    return [key for key in order if key in missing] + sorted(key for key in missing if key not in order)


def _analysis_readiness_status_label(row: dict[str, object]) -> str:
    if row.get("can_run"):
        return "可继续，但需注意" if row.get("warnings") else "可继续"
    warnings = [str(item) for item in row.get("warnings", []) or []]
    if any("样本 ID 不匹配" in item for item in warnings):
        return "需要修正样本匹配"
    if any("比较组已确认，但缺少表达矩阵" in item for item in warnings):
        return "缺少表达矩阵"
    missing = [str(item) for item in row.get("missing_inputs", []) or []]
    if missing:
        return "需要补充信息"
    if row.get("analysis_type") == "reporting":
        return "暂不可用"
    return "暂不建议"


def _analysis_missing_text(row: dict[str, object], group_preview: dict[str, object] | None = None) -> str:
    warnings = [str(item) for item in row.get("warnings", []) or []]
    if any("样本 ID 不匹配" in item for item in warnings):
        return "样本 ID 不匹配"
    if any("比较组已确认，但缺少表达矩阵" in item for item in warnings):
        return "表达矩阵"
    missing = []
    for item in row.get("missing_inputs", []) or []:
        normalized = _normalize_missing_input(str(item))
        if normalized == "comparison_config" and _group_preview_has_candidate(group_preview):
            missing.append("候选分组待确认")
        else:
            missing.append(_missing_input_label(str(item)))
    return "、".join(dict.fromkeys(missing)) if missing else "无"


def _analysis_suggested_action(row: dict[str, object], group_preview: dict[str, object] | None = None) -> str:
    warnings = [str(item) for item in row.get("warnings", []) or []]
    if any("样本 ID 不匹配" in item for item in warnings):
        return "修正比较组或选择其他表达文件"
    if any("比较组已确认，但缺少表达矩阵" in item for item in warnings):
        return "补充表达矩阵"
    missing = {_normalize_missing_input(str(item)) for item in row.get("missing_inputs", []) or []}
    if "expression_matrix" in missing:
        return "返回数据导入页面补充表达矩阵"
    if "sample_metadata" in missing:
        return "上传样本信息"
    if "comparison_config" in missing and _group_preview_has_candidate(group_preview):
        return "确认比较组"
    if "comparison_config" in missing:
        return "设置比较组"
    if "gmt_gene_set" in missing:
        return "上传 GMT 文件，或暂不做 GSEA"
    if "clinical_metadata" in missing:
        return "上传临床信息，或暂不做相关分析"
    if row.get("can_run"):
        return "可直接继续"
    if row.get("analysis_type") == "reporting":
        return "先生成分析结果"
    return "查看说明"


def _project_group_preview(project_root: Path | None) -> dict[str, object]:
    if project_root is None:
        return {}
    report = load_recognition_report(project_root)
    if not isinstance(report, dict):
        return {}
    preview = report.get("group_preview")
    return preview if isinstance(preview, dict) else {}


def _group_preview_has_candidate(preview: dict[str, object] | None) -> bool:
    if not isinstance(preview, dict):
        return False
    return str(preview.get("status") or "") == "preview_only" and int(preview.get("group_count") or 0) >= 2 and bool(preview.get("selected_preview_field"))


def _group_preview_user_summary(preview: dict[str, object]) -> str:
    if not preview:
        return "\n".join(
            [
                "样本数：0",
                "候选分组：未识别",
                "分组数量：0",
                "分组置信度：低",
                "建议：可以继续进入标准化；不能直接进入差异分析，需在标准化阶段确认分组。",
            ]
        )
    status = str(preview.get("status") or "")
    if status == "confirmed_comparison_exists":
        advice = "建议：已存在正式比较组设置，可在标准化后继续分析。"
    elif _group_preview_has_candidate(preview):
        advice = "建议：已生成候选分组；进入标准化后请确认正式比较组。"
    else:
        reason = str(preview.get("missing_group_reason") or "未识别到明确分组，请在下一步手动设置比较组。")
        return "\n".join(
            [
                f"样本数：{int(preview.get('sample_count') or 0)}",
                "候选分组：未识别",
                "分组数量：0 组",
                "分组置信度：低",
                f"建议：可以继续进入标准化；不能直接进入差异分析，需在标准化阶段确认分组。{reason}",
            ]
        )
    group_sizes = preview.get("group_sizes") if isinstance(preview.get("group_sizes"), dict) else {}
    size_text = "，".join(f"{key} {value}" for key, value in group_sizes.items()) if group_sizes else "未统计"
    fields = "、".join(str(item) for item in preview.get("candidate_group_fields", []) or []) or "未识别"
    return "\n".join(
        [
            f"样本数：{int(preview.get('sample_count') or 0)}",
            f"候选分组：{fields}",
            f"分组数量：{int(preview.get('group_count') or 0)} 组",
            f"每组样本数：{size_text}",
            f"分组置信度：{_group_preview_confidence_zh(str(preview.get('confidence') or 'low'))}",
            advice,
        ]
    )


def _group_preview_confidence_zh(value: str) -> str:
    return {"high": "高", "medium": "中", "low": "低"}.get(value, "低")


def _comparison_config_text_from_group_preview(preview: dict[str, object]) -> str:
    field = str(preview.get("selected_preview_field") or "group")
    group_sizes = preview.get("group_sizes") if isinstance(preview.get("group_sizes"), dict) else {}
    groups = [str(key) for key in group_sizes]
    control = next((group for group in groups if any(token in group.lower() for token in ("control", "normal", "vehicle", "untreated"))), groups[0] if groups else "control")
    case = next((group for group in groups if group != control), groups[1] if len(groups) > 1 else "case")
    return f"comparison_id\tgroup_column\tcase_group\tcontrol_group\ncase_vs_control\t{field}\t{case}\t{control}\n"


def _append_comparison_confirmation_audit(project_root: Path, preview: dict[str, object], comparison_text: str) -> Path:
    path = project_root / "logs" / "readiness" / "comparison_group_confirmation_log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": _utc_now_iso(),
        "action": "confirm_group_preview_as_comparison",
        "selected_preview_field": preview.get("selected_preview_field"),
        "group_sizes": preview.get("group_sizes"),
        "source_file": preview.get("source_file"),
        "comparison_text": comparison_text,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
    return path


def _missing_readiness_inputs(readiness: dict[str, object], matrix: dict[str, object]) -> set[str]:
    missing: set[str] = set()
    if not readiness.get("has_core_input"):
        missing.add("expression_matrix")
    rows = [row for row in matrix.get("rows", []) or [] if isinstance(row, dict)]
    for row in rows:
        for item in row.get("missing_inputs", []) or []:
            normalized = _normalize_missing_input(str(item))
            if normalized in {"sample_metadata", "clinical_metadata", "expression_matrix", "comparison_config", "gmt_gene_set"}:
                missing.add(normalized)
    for warning in readiness.get("warnings", []) or []:
        text = str(warning)
        if "表达矩阵" in text:
            missing.add("expression_matrix")
        if "样本信息" in text:
            missing.add("sample_metadata")
        if "临床信息" in text:
            missing.add("clinical_metadata")
    return missing


def _normalize_missing_input(value: str) -> str:
    text = str(value).strip().lower()
    mapping = {
        "sample": "sample_metadata",
        "sample_metadata": "sample_metadata",
        "样本信息": "sample_metadata",
        "样本注释": "sample_metadata",
        "clinical": "clinical_metadata",
        "clinical_metadata": "clinical_metadata",
        "临床信息": "clinical_metadata",
        "临床表": "clinical_metadata",
        "expression": "expression_matrix",
        "expression_matrix": "expression_matrix",
        "raw_count_matrix": "expression_matrix",
        "normalized_expression_matrix": "expression_matrix",
        "表达矩阵": "expression_matrix",
        "基因表达数据": "expression_matrix",
        "gmt": "gmt_gene_set",
        "gmt_gene_set": "gmt_gene_set",
        "gmt 基因集": "gmt_gene_set",
        "基因集": "gmt_gene_set",
        "comparison": "comparison_config",
        "comparison_config": "comparison_config",
        "contrast": "comparison_config",
        "比较组": "comparison_config",
        "分组比较": "comparison_config",
    }
    return mapping.get(text, text)


def _missing_input_label(value: str) -> str:
    normalized = _normalize_missing_input(value)
    return {
        "sample_metadata": "样本信息",
        "clinical_metadata": "临床信息",
        "expression_matrix": "表达矩阵",
        "comparison_config": "比较分组",
        "gmt_gene_set": "GMT 基因集",
        "platform_annotation": "平台注释",
        "gene_annotation": "基因注释",
    }.get(normalized, "其他缺失资产")


def _friendly_readiness_text(text: str) -> str:
    return (
        text.replace("无表达矩阵。", "缺少表达矩阵")
        .replace("样本信息缺失。", "缺少样本信息")
        .replace("临床信息缺失。", "缺少临床信息")
        .replace("comparison_config", "比较分组")
        .replace("gmt_gene_set", "GMT 基因集")
        .replace("。", "")
    )


def _template_text_for_missing_input(kind: str) -> str:
    normalized = _normalize_missing_input(kind)
    if normalized == "sample_metadata":
        return "sample_id\tgroup\nsample_1\tcase\nsample_2\tcontrol\n"
    if normalized == "clinical_metadata":
        return "sample_id\tsurvival_time\tsurvival_status\tage\nsample_1\t未记录\t未记录\t未记录\n"
    if normalized == "comparison_config":
        return "comparison_id\tgroup_column\tcase_group\tcontrol_group\ncomparison_1\tgroup\tcase\tcontrol\n"
    return "gene\tsample_1\tsample_2\nTP53\t1\t2\n"


def _save_manual_supplement(project_root: Path, normalized: str, text: str) -> Path:
    supplement_dir = project_root / "raw_data" / "local_import" / "manual_supplements"
    supplement_dir.mkdir(parents=True, exist_ok=True)
    target = supplement_dir / f"{normalized}_manual.tsv"
    target.write_text((text or _template_text_for_missing_input(normalized)).strip() + "\n", encoding="utf-8")
    register_acquisition(
        project_root,
        source_type=f"manual_supplement_{normalized}",
        source_label=f"手动补充{_missing_input_label(normalized)}",
        strategy="reference",
        selected_paths=[target],
        metadata={"supplement_kind": normalized, "ui_stage": "UI-07", "manual_input": True},
    )
    return target


def _standardization_status_message(assets: list[dict[str, object]], assets_generated: bool) -> str:
    if not assets_generated:
        return "尚未生成标准化资产。请确认输入与分组状态后生成。"
    reminder_count = sum(1 for item in assets if str(item.get("warning") or "").strip())
    return f"标准化结果已生成：{len(assets)} 项；提醒 {reminder_count} 条。"


def _standardization_current_input_user_summary(project_root: Path, report: dict[str, object]) -> str:
    files = [item for item in report.get("files", []) or [] if isinstance(item, dict)]
    if not files:
        return "尚未选择当前识别结果。\n请先完成数据识别。"
    current_run = next((run for run in list_recognition_runs(project_root) if run.get("is_current")), {})
    generated_at = _format_history_time(str(current_run.get("generated_at") or report.get("generated_at") or ""))
    names = [str(item.get("file_name") or Path(str(item.get("original_path") or "")).name or "未命名文件") for item in files]
    shown = "、".join(names[:3])
    if len(names) > 3:
        shown += f"；另有 {len(names) - 3} 个文件"
    return "\n".join(
        [
            "已选择识别结果",
            f"输入文件数量：{len(files)}",
            f"输入文件：{shown}",
            f"识别批次时间：{generated_at or '未记录'}",
            f"内容摘要：{_standardization_content_summary(files)}",
        ]
    )


def _standardization_input_detail_text(project_root: Path, report: dict[str, object]) -> str:
    files = [item for item in report.get("files", []) or [] if isinstance(item, dict)]
    if not files:
        return "暂无输入详情。"
    lines = ["输入文件详情"]
    for item in files:
        path = str(item.get("original_path") or item.get("source_file") or item.get("file_name") or "")
        lines.append(f"- {item.get('file_name') or Path(path).name or '未命名文件'}：{_compact_path(path, max_chars=72)}")
    lines.append(f"项目位置：{_compact_path(str(project_root), max_chars=72)}")
    return "\n".join(lines)


def _standardization_content_summary(files: list[dict[str, object]]) -> str:
    labels: list[str] = []
    for item in files:
        blocks = _content_blocks_by_type(item)
        if "count_expression_matrix" in blocks:
            labels.append("count 矩阵")
        if "fpkm_expression_matrix" in blocks:
            labels.append("FPKM")
        if "tpm_expression_matrix" in blocks:
            labels.append("TPM")
        if "deg_comparisons" in blocks:
            labels.append("差异结果")
        if "gene_annotation" in blocks:
            labels.append("基因注释")
        if not blocks:
            labels.append(_recognition_type_text(item))
    return "、".join(dict.fromkeys(label for label in labels if label)) or "未识别明确内容"


def _standardization_expression_user_summary(report: dict[str, object], assets: list[dict[str, object]]) -> str:
    files = [item for item in report.get("files", []) or [] if isinstance(item, dict)]
    expression_assets = [item for item in assets if str(item.get("asset_type") or "") in {"count_matrix", "expression_matrix", "raw_count_matrix", "normalized_expression_matrix"}]
    expression_available = bool(expression_assets) or _recognition_has_expression_asset(files)
    if not expression_available:
        return "表达矩阵：缺失\n请返回数据识别或数据来源页补充表达矩阵。"
    matrix_types = _standardization_matrix_type_text(files, expression_assets)
    primary = expression_assets[0] if expression_assets else _first_expression_record(files)
    gene_id = str(primary.get("gene_id_type") or _standardization_profile_value(primary, "gene_id_type") or "")
    species = str(primary.get("species") or _standardization_profile_value(primary, "species") or "未识别")
    sample_count = _standardization_sample_count(files, expression_assets)
    gene_count = int(primary.get("gene_count") or primary.get("feature_count") or 0)
    gene_text = str(gene_count) if gene_count else "未记录"
    return "\n".join(
        [
            "表达矩阵：可用",
            f"矩阵类型：{matrix_types}",
            f"基因 ID 类型：{_gene_id_type_label(gene_id)}",
            f"物种：{species}",
            f"数据规模：基因数 {gene_text}；样本数 {sample_count if sample_count else '未记录'}",
        ]
    )


def _standardization_matrix_type_text(files: list[dict[str, object]], assets: list[dict[str, object]]) -> str:
    labels: list[str] = []
    for asset in assets:
        value_type = str(asset.get("value_type") or "")
        asset_type = str(asset.get("asset_type") or "")
        if value_type:
            labels.append(value_type.upper() if value_type != "count" else "count")
        elif asset_type == "count_matrix":
            labels.append("count")
        elif asset_type == "normalized_expression_matrix":
            labels.append("FPKM/TPM")
        elif asset_type in {"expression_matrix", "raw_count_matrix"}:
            labels.append("表达矩阵")
    for item in files:
        blocks = _content_blocks_by_type(item)
        if "count_expression_matrix" in blocks:
            labels.append("count")
        if "fpkm_expression_matrix" in blocks:
            labels.append("FPKM")
        if "tpm_expression_matrix" in blocks:
            labels.append("TPM")
    return " / ".join(dict.fromkeys(label for label in labels if label)) or "表达矩阵"


def _first_expression_record(files: list[dict[str, object]]) -> dict[str, object]:
    return next((item for item in files if _recognition_has_expression_asset([item])), files[0] if files else {})


def _standardization_profile_value(item: dict[str, object], key: str) -> object:
    profile = item.get("content_profile") if isinstance(item.get("content_profile"), dict) else {}
    return profile.get(key)


def _standardization_sample_count(files: list[dict[str, object]], assets: list[dict[str, object]]) -> int:
    values = [int(item.get("sample_count") or 0) for item in assets if int(item.get("sample_count") or 0) > 0]
    for item in files:
        for block in _content_blocks_by_type(item).values():
            if str(block.get("block_type") or "") in {"count_expression_matrix", "fpkm_expression_matrix", "tpm_expression_matrix"}:
                count = int(block.get("sample_count") or len(block.get("sample_columns", []) or []))
                if count:
                    values.append(count)
    return max(values) if values else 0


def _standardization_group_user_summary(project_root: Path, report: dict[str, object], assets: list[dict[str, object]]) -> str:
    preview = report.get("group_preview") if isinstance(report.get("group_preview"), dict) else {}
    confirmed = has_confirmed_group_comparison_design(project_root)
    context = load_group_design_context(project_root) if assets else {}
    groups = [item for item in context.get("sample_groups", []) or [] if isinstance(item, dict)] if context else []
    sample_count = sum(int(item.get("sample_count") or 0) for item in groups) or int(preview.get("sample_count") or 0) or _standardization_sample_count([item for item in report.get("files", []) or [] if isinstance(item, dict)], assets)
    group_sizes = {str(item.get("inferred_group_id") or item.get("user_group_name") or ""): int(item.get("sample_count") or 0) for item in groups if item.get("inferred_group_id") or item.get("user_group_name")}
    if not group_sizes and isinstance(preview.get("group_sizes"), dict):
        group_sizes = {str(key): int(value) for key, value in preview.get("group_sizes", {}).items()}
    group_count = len(group_sizes) or int(preview.get("group_count") or 0)
    group_text = "、".join(f"{key} {value}" for key, value in group_sizes.items()) if group_sizes else "未识别"
    confidence = _group_preview_confidence_zh(str(preview.get("confidence") or "low"))
    source = "人工确认" if confirmed else ("系统推断" if group_count else "未识别")
    lines = [
        f"样本数：{sample_count if sample_count else '未记录'}",
        f"分组数量：{group_count if group_count else 0}",
        f"每组样本数：{group_text}",
        f"分组来源：{source}",
        f"分组置信度：{confidence}",
        f"是否人工确认：{'是' if confirmed else '否'}",
    ]
    if not confirmed:
        lines.append("分组信息未确认，可以进入分析任务中心查看任务，但不能直接启动 DEG 分析。请先确认分组与比较设计。")
    return "\n".join(lines)


def _standardization_status_values(
    report: dict[str, object],
    assets: list[dict[str, object]],
    assets_generated: bool,
    group_confirmed: bool,
) -> list[tuple[str, str, str]]:
    files = [item for item in report.get("files", []) or [] if isinstance(item, dict)]
    has_expression = _standardization_has_expression_asset(files, assets)
    has_sample = any(str(asset.get("asset_type") or "") in {"sample_metadata", "phenotype_metadata"} for asset in assets) or any(
        "sample_metadata" in [str(role) for role in item.get("recognized_roles", []) or []] for item in files
    )
    has_annotation = any(str(asset.get("asset_type") or "") == "gene_annotation" for asset in assets) or any("gene_annotation" in _content_blocks_by_type(item) for item in files)
    return [
        ("expression", "表达矩阵", "可用" if has_expression else "缺失"),
        ("sample_metadata", "样本信息表", "可用" if has_sample else "需补充"),
        ("group_design", "分组设计", "已确认" if group_confirmed else "未确认"),
        ("gene_annotation", "基因注释", "已识别" if has_annotation else "需确认"),
        ("standardized_result", "标准化结果", "已生成" if assets_generated else "未生成"),
    ]


def _standardization_has_expression_asset(files: list[dict[str, object]], assets: list[dict[str, object]]) -> bool:
    if any(str(asset.get("asset_type") or "") in {"count_matrix", "expression_matrix", "raw_count_matrix", "normalized_expression_matrix"} for asset in assets):
        return True
    return _recognition_has_expression_asset(files)


def _standardization_user_summary(registry: dict[str, object], manifest: dict[str, object]) -> str:
    assets = [item for item in registry.get("assets", []) or [] if isinstance(item, dict)]
    ready_assets = [item for item in assets if item.get("analysis_ready")]
    warnings = [str(item) for item in registry.get("warnings", []) or []] + [str(item) for item in manifest.get("warnings", []) or []]
    usable = [str(item) for item in manifest.get("usable_analyses", []) or []]
    missing = [str(item) for item in manifest.get("missing_assets", []) or []]
    asset_types = {str(item.get("asset_type") or "") for item in assets}
    lines: list[str] = []
    if {"count_matrix", "normalized_expression_matrix", "deg_result_table", "gene_annotation"} <= asset_types:
        lines.extend(
            [
                "检测到一个综合 RNA-seq 表。",
                "系统已拆分为 count 矩阵、FPKM 矩阵、差异分析结果和基因注释。",
                "标准化资产：count matrix、FPKM / normalized expression matrix、imported DEG result table、gene annotation、gene identifier metadata",
                "提示：重新差异分析建议使用 count；表达展示、热图和相关性可使用 FPKM。",
            ]
        )
    lines.extend(
        [
            f"注册资产：{len(assets)} 个",
            f"analysis-ready 资产：{len(ready_assets)} 个",
            f"可用于分析：{'、'.join(usable) if usable else '暂无'}",
            f"缺失关键资产：{'、'.join(missing) if missing else '无'}",
            f"warning：{'；'.join(dict.fromkeys(warnings)) if warnings else '无'}",
            "说明：当前为资产注册和轻量校验，不等于正式 biological normalization。",
        ]
    )
    return "\n".join(lines)


def _asset_usage_text(asset: dict[str, object]) -> str:
    recommended = [str(item) for item in asset.get("recommended_for", []) or [] if str(item)]
    if recommended:
        return "、".join(recommended)
    return "后续分析输入" if asset.get("analysis_ready") else "待确认"


def _asset_limitations_text(asset: dict[str, object]) -> str:
    limitations = [str(item) for item in asset.get("limitations", []) or [] if str(item)]
    return "；".join(limitations) if limitations else str(asset.get("warning") or "")


def _asset_default_text(asset: dict[str, object], selection_by_type: dict[str, dict[str, object]]) -> str:
    asset_id = str(asset.get("asset_id") or "")
    group = selection_by_type.get(str(asset.get("asset_type") or ""), {})
    if asset_id and asset_id == str(group.get("selected_asset_id") or ""):
        return str(group.get("status_label") or selection_status_label(str(group.get("selection_state") or "")))
    if group.get("selection_state") == "needs_selection":
        return "候选"
    return ""


def _asset_selection_summary_text(context: dict[str, object]) -> str:
    groups = [group for group in context.get("groups", []) or [] if isinstance(group, dict)]
    if not groups:
        return "默认资产选择：暂无可选择资产"
    counts: dict[str, int] = {}
    for group in groups:
        state = str(group.get("selection_state") or "")
        counts[state] = counts.get(state, 0) + 1
    parts = []
    for state in ("confirmed", "recommended_default", "needs_selection", "invalid"):
        if counts.get(state):
            parts.append(f"{selection_status_label(state)} {counts[state]} 类")
    return "默认资产选择：" + "，".join(parts)


def _group_design_context_summary(context: dict[str, object]) -> str:
    has_count = bool(context.get("has_count_matrix"))
    has_normalized = bool(context.get("has_normalized_expression_matrix"))
    group_count = int(context.get("group_count") or 0)
    imported_count = int(context.get("imported_deg_count") or 0)
    warnings = [str(item) for item in context.get("warnings", []) or [] if str(item)]
    matrix_text = "count matrix" if has_count else ("FPKM/TPM matrix" if has_normalized else "未检测到")
    match = context.get("count_fpkm_sample_match")
    match_text = ""
    if match is True:
        match_text = "Count 与 FPKM 样本匹配"
    elif match is False:
        match_text = "Count 与 FPKM 样本不完全一致，请检查。"
    status = "已确认分组设计" if context.get("has_confirmed_design") else "尚未确认分组设计"
    lines = [
        f"当前数据来源：{'综合 RNA-seq 表' if (has_count and imported_count) else '当前标准化资产'}",
        f"表达矩阵：{matrix_text}",
        f"推断分组：{group_count} 组",
        f"已有 DEG comparisons：{imported_count} 个",
        f"物种：{context.get('species') or 'unknown'}",
        f"状态：{status}",
    ]
    if match_text:
        lines.append(match_text)
    if has_count and not context.get("has_confirmed_design"):
        lines.append("重新差异分析前，请先确认分组。")
    if not has_count and has_normalized:
        lines.append("当前仅检测到 FPKM/TPM 表达矩阵。可用于表达展示、热图和相关性；如需重新差异分析，请提供 count matrix 或确认适用方法。")
    if not has_count and not has_normalized:
        lines.append("未检测到可用于分组设计的表达矩阵。")
    if imported_count:
        lines.append("已有导入差异结果可直接用于结果浏览和富集分析；如需重新计算，请保存上方分组和比较设计。")
    if warnings:
        lines.append("提醒：" + "；".join(dict.fromkeys(warnings)))
    return "\n".join(lines)


def _format_confidence(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "未记录"
    return f"{numeric * 100:.0f}%"


def _recognition_type_text(item: dict[str, object]) -> str:
    primary = str(item.get("recognized_type") or "unknown")
    primary_label = str(item.get("recognized_type_zh") or TYPE_LABELS.get(primary, "未知文件"))
    semantic_label = str(item.get("semantic_type_zh") or "")
    if semantic_label:
        return semantic_label
    roles = [str(role) for role in item.get("recognized_roles", []) or [] if str(role) and str(role) != primary]
    if not roles:
        return primary_label
    role_labels = [TYPE_LABELS.get(role, role) for role in roles if role != "unknown"]
    return f"{primary_label}（含：{'、'.join(role_labels)}）" if role_labels else primary_label


def _recognition_asset_summary(files: list[dict[str, object]]) -> str:
    if not files:
        return ""
    summaries = []
    for item in files:
        if item.get("semantic_type") == "rna_seq_integrated_result_table":
            summaries.append(_integrated_rnaseq_asset_summary(item))
        else:
            label = _recognition_type_text(item)
            name = str(item.get("file_name") or "未命名文件")
            summaries.append(f"文件：{name}\n文件类型：{label}")
    return "\n\n".join(summaries)


def _integrated_rnaseq_asset_summary(item: dict[str, object]) -> str:
    blocks = _content_blocks_by_type(item)
    gene_block = blocks.get("gene_identifier", {})
    count_block = blocks.get("count_expression_matrix", {})
    fpkm_block = blocks.get("fpkm_expression_matrix", {})
    deg_block = blocks.get("deg_comparisons", {})
    annotation_block = blocks.get("gene_annotation", {})
    count_sample_count = int(count_block.get("sample_count") or len(count_block.get("sample_columns", []) or []))
    fpkm_sample_count = int(fpkm_block.get("sample_count") or len(fpkm_block.get("sample_columns", []) or []))
    comparison_count = int(deg_block.get("complete_comparison_count") or deg_block.get("comparison_count") or len(deg_block.get("comparisons", []) or []))
    gene_id_type = str(item.get("gene_id_type") or gene_block.get("gene_id_type") or "")
    gene_prefix = _gene_id_prefix(gene_id_type, gene_block)
    comparison_names = [str(comparison.get("comparison_name") or "") for comparison in deg_block.get("comparisons", []) or [] if isinstance(comparison, dict) and str(comparison.get("comparison_name") or "")]
    annotation_fields = [str(field) for field in annotation_block.get("annotation_fields", []) or [] if str(field)]
    group_text = _expression_group_summary(count_block)
    comparison_preview = _preview_list(comparison_names, limit=4, more_label="比较")
    annotation_preview = _preview_list(_preferred_annotation_fields(annotation_fields), limit=3, more_label="字段")
    lines = [
        "文件类型：RNA-seq 综合表达结果表",
        "包含 count、FPKM、差异分析结果和基因注释。",
        f"物种：{item.get('species') or gene_block.get('species') or '未识别'}",
        f"基因 ID：{_gene_id_type_label(gene_id_type)}",
        f"表达数据：count 矩阵 {count_sample_count} 列；FPKM 矩阵 {fpkm_sample_count} 列",
        f"差异比较：{comparison_count} 个完整比较",
        f"基因注释：{'已包含' if annotation_fields else '未识别'}",
        "状态：可进入标准化",
        "数据内容：",
        f"基因标识：{gene_prefix} / {_gene_id_type_label(gene_id_type)}",
        f"Count 矩阵：{count_sample_count} 列{group_text}",
        f"FPKM 矩阵：{fpkm_sample_count} 列{_fpkm_match_text(fpkm_block)}",
        f"差异比较：{comparison_preview or '未识别'}",
        f"注释字段：{annotation_preview or '未识别'}",
        "提醒：",
        "检测到 count 与 FPKM。差异分析建议使用 count；表达展示可使用 FPKM。",
    ]
    if comparison_count:
        lines.append("文件已包含差异分析结果，可用于结果浏览和富集分析；如需重新计算差异分析，请确认分组配置。")
    if str(item.get("species_group") or gene_block.get("species_group") or "") == "mouse":
        lines.append("该数据集为小鼠数据，适合动物模型分析、机制探索和方法验证，不应直接按人类临床队列解释。")
    return "\n".join(lines)


def _content_blocks_by_type(item: dict[str, object]) -> dict[str, dict[str, object]]:
    blocks = item.get("content_blocks")
    if not isinstance(blocks, list):
        profile = item.get("content_profile")
        blocks = profile.get("content_blocks") if isinstance(profile, dict) else []
    result: dict[str, dict[str, object]] = {}
    for block in blocks or []:
        if isinstance(block, dict):
            result[str(block.get("block_type") or "")] = block
    return result


def _gene_id_type_label(value: str) -> str:
    return {
        "ensembl_mouse_gene_id": "Ensembl mouse gene ID",
        "ensembl_human_gene_id": "Ensembl human gene ID",
        "ensembl_mouse_transcript_id": "Ensembl mouse transcript ID",
        "ensembl_id": "Ensembl ID",
    }.get(value, value or "未识别")


def _gene_id_prefix(gene_id_type: str, gene_block: dict[str, object]) -> str:
    examples = [str(value) for value in gene_block.get("example_values", []) or [] if str(value)]
    if examples:
        match = re.match(r"([A-Z]+)", examples[0])
        if match:
            return match.group(1)
    return {
        "ensembl_mouse_gene_id": "ENSMUSG",
        "ensembl_human_gene_id": "ENSG",
        "ensembl_mouse_transcript_id": "ENSMUST",
    }.get(gene_id_type, "gene_id")


def _expression_group_summary(block: dict[str, object]) -> str:
    groups = [str(group) for group in block.get("inferred_groups", []) or [] if str(group)]
    replicate_counts = block.get("replicate_count_by_group") if isinstance(block.get("replicate_count_by_group"), dict) else {}
    if not groups:
        return ""
    counts = [int(value) for value in replicate_counts.values() if isinstance(value, (int, float))]
    replicate_text = f"，每组约 {round(sum(counts) / len(counts))} 个重复" if counts else ""
    return f"，{len(groups)} 组{replicate_text}"


def _fpkm_match_text(block: dict[str, object]) -> str:
    if block.get("matches_count_sample_ids") is True:
        return "，与 count 样本匹配"
    if block.get("matches_count_sample_ids") is False:
        return "，与 count 样本不完全匹配"
    return ""


def _preview_list(values: list[str], *, limit: int, more_label: str) -> str:
    clean = [value for value in values if value]
    if not clean:
        return ""
    shown = "、".join(clean[:limit])
    remaining = len(clean) - limit
    return f"{shown}；另有 {remaining} 个{more_label}" if remaining > 0 else shown


def _preferred_annotation_fields(fields: list[str]) -> list[str]:
    preferred = ["gene_name", "gene_biotype", "gene_description", "tf_family"]
    result = [field for field in preferred if field in fields]
    result.extend(field for field in fields if field not in result)
    return result


def _analysis_task_group_summary(center: dict[str, object]) -> str:
    capabilities = [item for item in center.get("capabilities", []) or [] if isinstance(item, dict)]
    available = {
        str(item.get("task_id") or ""): item
        for item in capabilities
        if item.get("status") in {"available", "ready_with_group_confirmation", "ready_with_threshold_selection", "configured_not_run", "skipped_dry_run"}
    }
    lines: list[str] = []
    count_status = available.get("differential_expression_recompute", {}).get("status")
    if count_status == "ready_with_group_confirmation":
        count_group_title = "需要确认分组后运行"
    elif count_status == "configured_not_run":
        count_group_title = "DEG 任务已配置未运行"
    elif count_status == "skipped_dry_run":
        count_group_title = "DEG 任务记录已生成"
    else:
        count_group_title = "已确认分组后可运行"
    groups = [
        ("可直接使用已有结果", [("deg_result_browse", "查看差异基因结果"), ("deg_filtering", "DEG 筛选"), ("volcano_plot", "火山图"), ("enrichment_from_deg", "富集分析输入")]),
        (count_group_title, [("differential_expression_recompute", "重新差异表达分析"), ("qc", "样本 QC"), ("normalization", "count 矩阵标准化")]),
        ("表达数据探索", [("heatmap", "表达热图"), ("correlation", "样本相关性"), ("gene_expression_browse", "候选基因表达查看")]),
        ("注释与报告", [("gene_annotation_display", "gene annotation 浏览"), ("protein_coding_filter", "protein-coding 筛选"), ("report_annotation", "报告注释")]),
    ]
    for title, tasks in groups:
        labels = [label for task_id, label in tasks if task_id in available]
        if labels:
            lines.append(f"{title}：{'、'.join(labels)}")
    count_capability = available.get("differential_expression_recompute")
    if count_capability and count_capability.get("status") in {"ready_with_group_confirmation", "configured_not_run"}:
        lines.append(str(count_capability.get("reason") or "检测到推断分组，请确认实验分组后重新差异分析。"))
    mouse_capability = next((item for item in capabilities if item.get("task_id") == "human_cohort_integration" and item.get("status") == "not_available"), None)
    if mouse_capability:
        lines.append("小鼠数据：适合动物模型分析、机制探索和方法验证；不推荐人类队列整合。")
    return "\n".join(lines) if lines else "尚未生成可用分析任务。"


def _task_source_status_text(item: dict[str, object]) -> str:
    source = str(item.get("source_asset_type") or "")
    status = str(item.get("capability_status") or "")
    source_label = {
        "deg_result_table": "导入表格中的 DEG comparison",
        "count_matrix": "count matrix",
        "normalized_expression_matrix": "FPKM matrix",
        "gene_annotation": "gene annotation",
    }.get(source, source or "未识别来源资产")
    status_label = {
        "available": "可直接使用",
        "ready_with_group_confirmation": "需要确认分组",
        "ready_with_threshold_selection": "可用；需选择阈值",
        "needs_asset_selection": "需要选择默认资产",
        "configured_not_run": "已配置未运行",
        "skipped_dry_run": "当前版本仅生成任务记录",
        "planned": "已规划",
        "not_available": "不可用",
    }.get(status, status or "未知状态")
    reason = "；".join(str(value) for value in item.get("warnings", []) or [] if str(value))
    if reason:
        return f"来源：{source_label}；状态：{status_label}；{reason}"
    return f"来源：{source_label}；状态：{status_label}"


def _analysis_task_run_row(run: dict[str, object]) -> list[object]:
    source_assets = [item for item in run.get("source_assets", []) or [] if isinstance(item, dict)]
    asset_text = "、".join(str(item.get("asset_id") or item.get("asset_type") or "") for item in source_assets if item)
    comparisons = [item for item in run.get("comparisons", []) or [] if isinstance(item, dict)]
    return [
        run.get("created_at", ""),
        run.get("task_type", ""),
        run.get("run_id", ""),
        asset_text,
        len(comparisons),
        task_run_status_label(str(run.get("status") or "")),
        "查看详情",
    ]


def _reportable_content_summary(result_index: dict[str, object]) -> str:
    items = [item for item in result_index.get("items", []) or [] if isinstance(item, dict)]
    if not items:
        return "暂无可纳入报告的结果内容。尚未完成的 dry-run 任务不会被写成真实结果。"
    imported = [item for item in items if item.get("item_type") == "imported_deg_result"]
    task_runs = [item for item in items if item.get("item_type") == "analysis_task_run"]
    completed = [item for item in items if item.get("item_type") == "completed_result"]
    lines = ["可纳入报告的内容："]
    if imported:
        lines.append(f"- 导入表格中的已有差异分析结果：{len(imported)} 项")
    if completed:
        lines.append(f"- 已完成分析结果：{len(completed)} 项")
    if task_runs:
        dry_count = sum(1 for item in task_runs if item.get("status") == "skipped_dry_run")
        suffix = f"，其中 {dry_count} 项为 dry-run 任务记录" if dry_count else ""
        lines.append(f"- 尚未完成的任务记录：{len(task_runs)} 项{suffix}")
        lines.append("  任务记录只保存输入、比较设计和参数，不代表 DEG 已完成。")
    return "\n".join(lines)


def _imported_deg_user_summary(view: dict[str, object], *, comparison_count: int = 0) -> str:
    stats = view.get("statistics") if isinstance(view.get("statistics"), dict) else {}
    thresholds = view.get("selected_thresholds") if isinstance(view.get("selected_thresholds"), dict) else {}
    gene_lists = view.get("gene_lists") if isinstance(view.get("gene_lists"), dict) else {}
    enrichment_species = str(view.get("enrichment_species") or "unknown")
    species = str(view.get("species") or "")
    species_text = f"{enrichment_species} / {species}" if species and species != enrichment_species else enrichment_species
    lines = [
        "当前结果来源：导入表格中的已有差异分析结果",
        f"比较数量：{comparison_count}",
        f"物种：{species or enrichment_species or 'unknown'}",
        "可用于：DEG 浏览、筛选、火山图输入、富集分析输入",
        "差异结果来源：导入表格中的已有结果",
        f"当前比较：{view.get('comparison_name') or '未选择'}",
        f"筛选阈值：padj < {thresholds.get('padj', 0.05)}；abs(log2FC) > {thresholds.get('abs_log2fc', 1.0)}",
        f"统计：total genes {stats.get('total_genes', 0)}；significant genes {stats.get('significant_genes', 0)}；upregulated {stats.get('upregulated', 0)}；downregulated {stats.get('downregulated', 0)}",
        f"富集物种：{species_text}",
        f"Gene list：up genes {len(gene_lists.get('up_genes', []) or [])}；down genes {len(gene_lists.get('down_genes', []) or [])}；all significant genes {len(gene_lists.get('all_significant_genes', []) or [])}。优先使用 gene_name / gene symbol。",
    ]
    warnings = [str(item) for item in view.get("warnings", []) or [] if str(item)]
    if warnings:
        lines.append("提醒：" + "；".join(warnings))
    if view.get("gene_id_type") and not any(gene_lists.get(key) for key in ("up_genes", "down_genes", "all_significant_genes")):
        lines.append("若仅有 Ensembl ID，需要先做 ID 转换再进入富集分析。")
    return "\n".join(lines)


def _recognition_roles_tooltip(item: dict[str, object]) -> str:
    roles = [str(role) for role in item.get("recognized_roles", []) or [] if str(role)]
    assets = [asset for asset in item.get("detected_assets", []) or [] if isinstance(asset, dict)]
    lines = [f"主类型：{item.get('recognized_type_zh') or TYPE_LABELS.get(str(item.get('recognized_type') or 'unknown'), '未知文件')}"]
    if roles:
        lines.append("可用角色：" + "、".join(TYPE_LABELS.get(role, role) for role in roles))
    for asset in assets:
        label = str(asset.get("label_zh") or TYPE_LABELS.get(str(asset.get("asset_type") or ""), ""))
        reason = str(asset.get("reason") or "")
        if label or reason:
            lines.append(f"{label}：{reason}".strip("："))
    return "\n".join(lines)


def _format_file_size(value: object) -> str:
    try:
        size = float(value)
    except (TypeError, ValueError):
        return "未记录"
    units = ("bytes", "KB", "MB", "GB", "TB")
    index = 0
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    if index == 0:
        return f"{int(size)} bytes"
    return f"{size:.1f} {units[index]}"


def _annotated_recognition_files(report: dict[str, object], project_root: Path | None) -> list[dict[str, object]]:
    files = [dict(item) for item in report.get("files", []) or [] if isinstance(item, dict)]
    effective_paths = _current_effective_source_paths(project_root)
    groups: dict[tuple[str, str], list[int]] = {}
    for index, item in enumerate(files):
        key = (str(item.get("file_name") or ""), str(item.get("file_size") or ""))
        groups.setdefault(key, []).append(index)
        original_path = Path(str(item.get("original_path") or "")).expanduser()
        resolved = str(original_path.resolve()) if original_path.exists() else str(original_path)
        item["_effective_source"] = not effective_paths or resolved in effective_paths or any(resolved.startswith(path + "/") for path in effective_paths)
    for indexes in groups.values():
        if len(indexes) <= 1:
            continue
        sorted_indexes = sorted(indexes, key=lambda i: ("/acq-" in str(files[i].get("original_path", "")), str(files[i].get("original_path", ""))))
        for duplicate_index in sorted_indexes[1:]:
            files[duplicate_index]["_duplicate"] = True
        files[sorted_indexes[0]]["_duplicate_primary"] = True
    return files


def _current_effective_source_paths(project_root: Path | None) -> set[str]:
    if project_root is None:
        return set()
    summary = load_latest_acquisition_summary(project_root)
    if summary is None or summary.strategy == "plan_only":
        return set()
    paths = set()
    for raw in [*summary.copied_files, *summary.referenced_paths, *summary.registered_files]:
        if not str(raw).strip():
            continue
        path = Path(str(raw)).expanduser()
        paths.add(str(path.resolve()) if path.exists() else str(path))
    return paths


def _filter_recognition_files(files: list[dict[str, object]], mode: str) -> list[dict[str, object]]:
    if mode == "隐藏疑似重复文件":
        return [item for item in files if not item.get("_duplicate")]
    if mode == "仅显示当前有效数据来源":
        effective = [item for item in files if item.get("_effective_source")]
        return effective or files
    return files


def _recognition_file_display_path(item: dict[str, object]) -> tuple[str, str]:
    source_path = str(item.get("original_path") or item.get("input_path") or item.get("source_path") or "").strip()
    if source_path:
        return _compact_path(source_path, max_chars=54), source_path
    file_name = str(item.get("file_name") or "未记录")
    return file_name, file_name


def _recognition_status_bar_summary(report: dict[str, object], files: list[dict[str, object]]) -> str:
    file_count = len(files)
    type_text = _recognition_type_brief(files)
    expression_text = "表达矩阵已识别" if _recognition_has_expression_asset(files) else "表达矩阵未识别"
    preview = report.get("group_preview") if isinstance(report.get("group_preview"), dict) else {}
    if _group_preview_has_candidate(preview) or str(preview.get("status") or "") == "confirmed_comparison_exists":
        group_text = "分组信息已生成候选，需在标准化阶段确认。"
    else:
        group_text = "分组信息未识别，需在标准化阶段确认后才能做 DEG 分析。"
    return f"已识别 {file_count} 个文件：{type_text}；{expression_text}；{group_text}"


def _recognition_type_brief(files: list[dict[str, object]]) -> str:
    labels = []
    for item in files:
        label = _recognition_type_text(item)
        if label and label not in labels:
            labels.append(label)
        if len(labels) >= 3:
            break
    if not labels:
        return "暂无可识别类型"
    remaining = len(files) - len(labels)
    suffix = f"等 {len(files)} 类/文件" if remaining > 0 else ""
    return "、".join(labels) + suffix


def _recognition_has_expression_asset(files: list[dict[str, object]]) -> bool:
    expression_types = {"expression_matrix", "raw_count_matrix", "normalized_expression_matrix"}
    expression_blocks = {"count_expression_matrix", "fpkm_expression_matrix", "tpm_expression_matrix"}
    for item in files:
        if str(item.get("recognized_type") or "") in expression_types:
            return True
        roles = {str(role) for role in item.get("recognized_roles", []) or []}
        if roles & expression_types:
            return True
        for block in _content_blocks_by_type(item):
            if block in expression_blocks:
                return True
        if str(item.get("semantic_type") or "") == "rna_seq_integrated_result_table":
            return True
    return False


def _recognition_primary_next_step_text(next_steps: dict[str, object]) -> str:
    confirm = [str(item) for item in next_steps.get("needs_confirmation", []) or [] if str(item)]
    if confirm:
        return "可以继续进入数据准备与标准化；做 DEG 分析前，需要确认分组信息。"
    return "可以继续进入数据准备与标准化。"


def _recognition_user_summary(report: dict[str, object], files: list[dict[str, object]], warnings: list[str], project_root: Path | None) -> str:
    counts = report.get("type_counts", {}) if isinstance(report.get("type_counts"), dict) else {}
    duplicate_count = sum(1 for item in files if item.get("_duplicate"))
    effective_count = sum(1 for item in files if item.get("_effective_source"))
    type_lines = []
    for key, label in TYPE_LABELS.items():
        count = int(counts.get(key, 0) or 0)
        if count:
            type_lines.append(f"{label}：{count}")
    if project_root is not None and not _current_effective_source_paths(project_root):
        source_note = "本次识别结果仅来自本次选择的数据源。"
    else:
        source_note = f"当前有效数据来源文件：{effective_count} 个。"
    next_step = "如果已识别到表达矩阵或原始计数矩阵，可以继续数据准备检查；否则请返回数据来源补充文件。"
    return "\n".join(
        [
            f"识别文件总数：{len(files)}",
            f"warning 数量：{len(warnings)}",
            f"类型统计：{'；'.join(type_lines) if type_lines else '暂无可识别类型'}",
            f"疑似重复文件：{duplicate_count} 个",
            source_note,
            f"下一步建议：{next_step}",
        ]
    )


def _format_history_time(value: str) -> str:
    if not value:
        return "未记录"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def _history_input_text(run: dict[str, object]) -> str:
    values = run.get("input_data")
    if not isinstance(values, list) or not values:
        return "未记录"
    names = [Path(str(value)).name for value in values if str(value).strip()]
    if not names:
        return "未记录"
    return names[0] if len(names) == 1 else f"{len(names)} 个输入：{names[0]}"


def _history_status_text(run: dict[str, object]) -> str:
    if run.get("legacy"):
        return "由旧版项目结构导入"
    status = str(run.get("status") or "completed")
    return {
        "completed": "已完成",
        "completed_with_warnings": "完成但有警告",
        "failed": "识别失败",
        "history": "历史记录",
    }.get(status, status or "历史记录")


def _history_content_summary(run: dict[str, object]) -> str:
    report = _history_report_payload(run)
    files = [item for item in report.get("files", []) or [] if isinstance(item, dict)] if isinstance(report, dict) else []
    if not files:
        return "无有效识别文件"
    semantic_count = sum(1 for item in files if item.get("semantic_type") == "rna_seq_integrated_result_table")
    if semantic_count:
        return f"RNA-seq 综合表达结果表：{semantic_count}"
    labels = []
    for item in files[:3]:
        label = str(item.get("semantic_type_zh") or item.get("recognized_type_zh") or TYPE_LABELS.get(str(item.get("recognized_type") or "unknown"), "未知文件"))
        if label:
            labels.append(label)
    remaining = len(files) - len(labels)
    suffix = f"；另有 {remaining} 个文件" if remaining > 0 else ""
    legacy = "；由旧版项目结构导入" if run.get("legacy") else ""
    return f"{'、'.join(labels) if labels else '未知文件'}{suffix}{legacy}"


def _recognition_history_summary_text(runs: list[dict[str, object]]) -> str:
    if not runs:
        return "暂无历史识别记录。"
    current_count = sum(1 for run in runs if run.get("is_current"))
    warning_count = sum(int(run.get("warning_count") or 0) for run in runs)
    latest = _format_history_time(str(runs[0].get("generated_at") or ""))
    parts = [f"共 {len(runs)} 条历史记录", f"最近：{latest}"]
    if current_count:
        parts.append("包含当前标准化输入")
    if warning_count:
        parts.append(f"提醒 {warning_count} 条")
    return "；".join(parts)


def _history_run_detail_text(run: dict[str, object]) -> str:
    report = _history_report_payload(run)
    files = [item for item in report.get("files", []) or [] if isinstance(item, dict)] if isinstance(report, dict) else []
    warnings = [str(item) for item in report.get("warnings", []) or []] if isinstance(report, dict) else []
    lines = [
        f"批次名称：{run.get('batch_name') or run.get('run_id') or '识别记录'}",
        f"当前状态：{'当前使用中' if run.get('is_current') else _history_status_text(run)}",
        f"识别报告路径：{run.get('recognition_report_path') or '未记录'}",
        f"内容摘要：{_history_content_summary(run)}",
    ]
    if run.get("legacy"):
        lines.append("来源：由旧版项目结构导入")
    if files:
        lines.append("文件摘要：")
        lines.append(_recognition_asset_summary(files))
    if warnings:
        lines.append("Warning：" + "；".join(warnings[:5]))
    lines.append("技术详情：")
    lines.append(_json({"history_recognition_run": run, "recognition_report": report}))
    return "\n".join(lines)


def _history_report_payload(run: dict[str, object]) -> dict[str, object]:
    path = Path(str(run.get("recognition_report_path") or ""))
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _recognition_run_by_id(project_root: Path | None, run_id: str) -> dict[str, object] | None:
    if project_root is None or not run_id:
        return None
    for run in list_recognition_runs(project_root):
        if str(run.get("run_id") or "") == run_id:
            return run
    return None


def _can_continue_from_acquisition(project_root: Path) -> tuple[bool, str]:
    summary = load_latest_acquisition_summary(project_root)
    if summary is None:
        return False, "尚未生成数据获取记录。"
    if summary.strategy == "plan_only":
        return False, "当前数据来源为 plan_only，只生成获取计划，没有实际可识别文件。"
    candidate_paths = [Path(path) for path in [*summary.copied_files, *summary.referenced_paths, *summary.registered_files] if str(path).strip()]
    if not any(path.exists() for path in candidate_paths):
        return False, "未找到实际存在的原始数据文件。"
    return True, ""


def _can_continue_from_recognition(project_root: Path) -> tuple[bool, str]:
    report = load_recognition_report(project_root)
    if not isinstance(report, dict):
        return False, "尚未生成数据识别报告。"
    files = [item for item in report.get("files", []) or [] if isinstance(item, dict)]
    if not files:
        return False, "识别报告中没有任何文件。"
    has_core = any(
        str(item.get("recognized_type")) in {"expression_matrix", "raw_count_matrix"}
        or any(str(role) in {"expression_matrix", "raw_count_matrix"} for role in item.get("recognized_roles", []) or [])
        for item in files
    )
    if not has_core:
        return False, "未识别到表达矩阵或原始计数矩阵。"
    return True, ""


def _can_continue_from_readiness(project_root: Path) -> tuple[bool, str]:
    artifacts = load_readiness_artifacts(project_root)
    readiness = artifacts.get("readiness_report")
    if not isinstance(readiness, dict):
        return False, "尚未运行数据准备检查。"
    status = str(readiness.get("overall_status") or "unavailable")
    if status in {"not_ready", "unavailable"} or not readiness.get("has_core_input"):
        return False, f"当前数据准备状态为“{readiness_status_zh(status)}”。"
    return True, ""


def _can_continue_from_standardization(project_root: Path) -> tuple[bool, str]:
    artifacts = load_standardization_artifacts(project_root)
    registry = artifacts.get("registry")
    if not isinstance(registry, dict):
        return False, "尚未生成标准化资产。"
    assets = [item for item in registry.get("assets", []) or [] if isinstance(item, dict)]
    has_ready_core = any(item.get("analysis_ready") and str(item.get("asset_type")) in {"expression_matrix", "raw_count_matrix", "count_matrix", "normalized_expression_matrix"} for item in assets)
    if not has_ready_core:
        return False, "没有可用于分析的表达矩阵。"
    return True, ""


def _geo_expression_assets_for_analysis(project_root: Path) -> list[dict[str, object]]:
    artifacts = load_standardization_artifacts(project_root)
    registry = artifacts.get("registry")
    if not isinstance(registry, dict):
        return []
    assets = [item for item in registry.get("assets", []) or [] if isinstance(item, dict)]
    expression_assets: list[dict[str, object]] = []
    for asset in assets:
        asset_type = str(asset.get("asset_type") or "")
        if asset_type not in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix"}:
            continue
        if not asset.get("analysis_ready"):
            continue
        path_text = str(asset.get("file_path") or "")
        if not path_text:
            continue
        expression_assets.append(asset)
    return expression_assets


def _analysis_dataset_id(asset: dict[str, object], file_path: Path) -> str:
    for value in (asset.get("source_file"), asset.get("file_path"), file_path.name):
        match = re.search(r"GSE\d+", str(value), flags=re.I)
        if match:
            return match.group(0).upper()
    return file_path.stem


def _append_geo_deg_results_to_index(project_root: Path, summaries: list[dict[str, object]]) -> None:
    existing = load_result_index(project_root)
    entries = [dict(item) for item in existing.get("entries", []) or [] if isinstance(item, dict)]
    seen_paths = {str(item.get("path") or item.get("file_path") or "") for item in entries}
    for summary in summaries:
        result_path = str(summary.get("result_path") or "")
        if not result_path or result_path in seen_paths:
            continue
        dataset_id = str(summary.get("dataset_id") or Path(result_path).parent.name)
        entries.append(
            {
                "result_name": f"{dataset_id} 差异表达结果",
                "analysis_type": "differential_expression",
                "file_type": "csv",
                "created_at": str(summary.get("generated_at") or _utc_now_iso()),
                "path": result_path,
                "status": "generated",
                "summary_path": str(summary.get("summary_path") or ""),
                "dataset_id": dataset_id,
                "warning": "、".join(str(item) for item in summary.get("warnings", []) or []),
            }
        )
        seen_paths.add(result_path)
    write_result_index(project_root, entries)


def _toggle_details(edit: QPlainTextEdit) -> None:
    edit.setVisible(not edit.isVisible())


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _placeholder_terms(text: str) -> str:
    compact = " ".join(part for part in text.replace("与", " ").replace("和", " ").split() if part)
    return (
        f"English medical terms (placeholder): {compact}; disease; biomarker; prognosis\n"
        f"GEO keywords (placeholder): ({compact}) AND expression profiling AND Homo sapiens\n"
        "说明：当前为规则型占位输出，不调用外部网络，不写入正式分析结果。"
    )


def _open_path(path: Path | None) -> None:
    if path is None:
        return
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def _refresh_style(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)
