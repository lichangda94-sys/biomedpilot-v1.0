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
    QDialog,
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

from app.bioinformatics.project_analysis_tasks import create_analysis_task, load_analysis_task_center, load_task_records
from app.bioinformatics.comparison_config import (
    build_geo_comparison_config_text,
    comparison_sample_match_status,
    comparison_summary_text,
    evidence_field_label_zh,
    expression_samples_from_recognition_report,
    group_label_zh,
    confirmed_group_assignments,
    load_confirmed_comparison_config,
)
from app.bioinformatics.deg_task_plan import build_deg_preflight, load_deg_preflight_manifest
from app.bioinformatics.analysis_inputs import resolve_analysis_inputs
from app.bioinformatics.analysis_ui import build_analysis_center_state, build_dependency_rows
from app.bioinformatics.acquisition_adapters import (
    apply_legacy_asset_selection_to_repository_manifest,
    build_legacy_asset_selection_manifest,
    materialize_legacy_standardized_asset_candidates,
    merge_legacy_materialized_assets_into_repository_manifest,
    write_legacy_standardized_asset_candidates,
)
from app.bioinformatics.deg_engine import (
    load_deg_parameter_confirmation,
    load_r_deseq2_parameter_confirmation,
    load_r_limma_parameter_confirmation,
    run_formal_controlled_deg,
    run_r_deseq2_rscript_execution,
    run_r_limma_rscript_execution,
    save_deg_parameter_confirmation,
    save_r_deseq2_parameter_confirmation,
    save_r_limma_design_config,
    save_r_limma_parameter_confirmation,
)
from app.bioinformatics.deg_engine.result_review import build_formal_deg_result_review, export_formal_deg_review_table
from app.bioinformatics.enrichment import build_ora_result_review, export_ora_review_table, run_controlled_ora
from app.bioinformatics.gsea import build_gsea_result_review, export_gsea_review_table, run_controlled_preranked_gsea
from app.bioinformatics.plots import build_formal_deg_plot_gate, build_gsea_plot_gate, build_ora_plot_gate, create_formal_deg_plot_artifact, create_gsea_plot_artifact, create_ora_plot_artifact
from app.bioinformatics.reports.formal_deg import create_formal_deg_report_ready_package, evaluate_formal_deg_report_ready_gate
from app.bioinformatics.reports.gsea import create_gsea_report_ready_package, evaluate_gsea_report_ready_gate
from app.bioinformatics.reports.integrated import (
    build_full_integrated_report_package_plan,
    create_full_integrated_docx_rendered_export,
    create_full_integrated_report_package,
    evaluate_full_integrated_docx_preflight_gate,
    evaluate_full_integrated_report_gate,
    evaluate_full_integrated_report_renderer_gate,
)
from app.bioinformatics.reports.ora import create_ora_report_ready_package, evaluate_ora_report_ready_gate
from app.bioinformatics.reports.survival_clinical import (
    create_cox_report_ready_package,
    create_km_logrank_report_ready_package,
    evaluate_cox_report_ready_gate,
    evaluate_km_logrank_report_ready_gate,
)
from app.bioinformatics.data_source_requests import create_data_source_request
from app.bioinformatics.data_sources import (
    GTExDownloadExecutionResult,
    GTExDownloadPlanDraft,
    GTExDownloadPlanExecutor,
    GTExExpressionBuildResult,
    GTExExpressionMatrixBuilder,
    GTExMetadataPreviewService,
    GTExPreviewSummary,
    GTExWorkflowState,
    TCGADownloadPlanExecutor,
    TCGADownloadPlanDraft,
    TCGADownloadExecutionResult,
    TCGAClinicalBuildResult,
    TCGAClinicalMetadataBuilder,
    TCGAExpressionBuildResult,
    TCGAExpressionQuantificationBuilder,
    TCGAMetadataPreviewService,
    TCGAPreviewSummary,
    TCGAWorkflowState,
    build_gtex_preview_request,
    build_gtex_workflow_state,
    build_tcga_preview_request,
    build_tcga_workflow_state,
    format_bytes_zh,
    latest_gtex_download_plan_path,
    latest_gtex_raw_expression_record_path,
    latest_tcga_download_plan_path,
    latest_tcga_expression_build_manifest_path,
    latest_tcga_raw_expression_record_path,
    write_gtex_download_plan_draft,
    write_tcga_download_plan_draft,
)
from app.bioinformatics.gtex_tissue_registry import GTEX_USE_PURPOSES, get_gtex_tissue, get_gtex_use_purpose, grouped_gtex_tissues
from app.bioinformatics.imported_deg_results import imported_deg_summary, list_imported_deg_results, mark_imported_deg_report_candidates
from app.bioinformatics.immune_infiltration import (
    build_immune_infiltration_readiness,
    build_linkage_preflight,
    generate_immune_tme_report,
    load_signature_catalog,
    run_immune_scoring,
)
from app.bioinformatics.immune_infiltration.signature_models import signature_from_dict
from app.bioinformatics.project_readiness import (
    has_standardizable_expression_input,
    load_readiness_artifacts,
    readiness_status_zh,
    run_project_readiness,
)
from app.bioinformatics.project_recognition import TYPE_LABELS, classify_file, load_recognition_report, run_project_recognition, run_project_recognition_for_paths
from app.bioinformatics.project_standardization import generate_standardized_assets, load_standardization_artifacts
from app.bioinformatics.standardization_confirmation import (
    collect_standardization_candidates,
    confirm_group_design_from_preview,
    load_standardization_confirmation_artifacts,
    save_standardization_confirmation,
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
from app.bioinformatics.gse_file_download_candidates import (
    build_gse_file_download_candidates,
    load_gse_file_download_candidate_selection,
    save_gse_file_download_candidate_selection,
    selected_gse_file_download_candidates,
)
from app.bioinformatics.gene_set_resources import (
    COLLECTION_TYPES,
    GENE_ID_TYPES,
    SPECIES_VALUES,
    build_gsea_gene_set_readiness,
    download_gene_set_resource,
    get_gene_set,
    import_gmt_file,
    list_downloadable_gene_set_resources,
    list_local_gene_sets,
    refresh_downloaded_gene_set,
    remove_gene_set,
    select_gene_set,
    validate_gene_set_registry,
)
from app.bioinformatics.reports.project_report_builder import generate_project_report, load_project_report
from app.bioinformatics.results.project_results import load_result_index, write_result_index
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
from app.bioinformatics.tcga_project_registry import (
    TCGA_ANALYSIS_PURPOSES,
    TCGA_SAMPLE_SCOPES,
    get_tcga_analysis_purpose,
    get_tcga_project,
    get_tcga_sample_scope,
    grouped_tcga_projects,
)
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
    source_files: tuple[str, ...] = ()
    copied_files: tuple[str, ...] = ()
    referenced_paths: tuple[str, ...] = ()
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
    source_files: tuple[str, ...] = ()


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
    source_files: tuple[str, ...] = ()
    storage_policy: str = ""
    focused_source_file: str = ""
    batch_summary: str = ""


@dataclass(frozen=True)
class GseDatasetPreview:
    gse_id: str
    title: str = "未记录"
    platform: str = "未记录"
    sample_count: str = "未记录"
    status: str = "尚未添加"


class GeoDatasetDetailPanel(QFrame):
    save_requested = Signal(object)
    ignore_requested = Signal(object)
    remove_requested = Signal(object)
    add_to_download_list_requested = Signal(object)
    download_assets_requested = Signal(object)
    translate_requested = Signal(object)
    brief_requested = Signal(object)
    confirm_comparison_requested = Signal(object)
    manual_comparison_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._candidate: UnifiedDatasetCandidate | None = None
        self._project_root: Path | None = None
        self._download_candidate_rows: list[dict[str, object]] = []
        self._download_candidate_checks: dict[str, QCheckBox] = {}
        self.setObjectName("geoDatasetDetailView")
        self.setVisible(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        layout.setSpacing(SPACING["sm"])

        self._title = QLabel("GEO 数据集详情")
        self._title.setObjectName("bioProjectCardTitle")
        self._title.setWordWrap(True)
        layout.addWidget(self._title)
        self._saved_status = _status_label("尚未加入下载列表 / 待处理数据来源。")
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

        layout.addWidget(_muted("可下载文件候选"))
        self._download_candidate_hint = _muted("当前只是下载候选选择，不是分析结果；下载后仍需数据识别与标准化确认。")
        self._download_candidate_hint.setObjectName("geoDownloadCandidateHint")
        self._download_candidate_hint.setWordWrap(True)
        layout.addWidget(self._download_candidate_hint)
        self._download_candidate_table = _table(["选择", "文件名", "文件类型 / 预测角色", "推荐级别", "建议下载", "风险提示", "文件来源", "后续用途"])
        self._download_candidate_table.setObjectName("geoDownloadCandidateTable")
        self._download_candidate_table.setMinimumHeight(210)
        self._download_candidate_table.setMaximumHeight(320)
        layout.addWidget(self._download_candidate_table)
        self._save_download_candidates_button = _button("保存候选选择", "secondaryButton", lambda: self._save_download_candidate_selection())
        self._save_download_candidates_button.setObjectName("geoDownloadCandidateSaveButton")
        self._download_candidate_status = _muted("")
        self._download_candidate_status.setObjectName("geoDownloadCandidateStatus")
        candidate_actions = QHBoxLayout()
        candidate_actions.addWidget(self._save_download_candidates_button)
        candidate_actions.addWidget(self._download_candidate_status)
        candidate_actions.addStretch(1)
        layout.addLayout(candidate_actions)

        decision_actions = QHBoxLayout()
        self._save_button = _button("保存", "primaryButton", lambda: self._emit_save())
        self._download_list_button = _button("加入下载列表", "secondaryButton", lambda: self._emit_add_to_download_list())
        self._download_assets_button = _button("下载补充文件", "primaryButton", lambda: self._emit_download_assets())
        self._remove_button = _button("从项目列表移除", "secondaryButton", lambda: self._emit_remove())
        self._ignore_button = _button("忽略", "secondaryButton", lambda: self._emit_ignore())
        self._download_assets_button.setVisible(False)
        self._remove_button.setVisible(False)
        decision_actions.addWidget(self._save_button)
        decision_actions.addWidget(self._download_list_button)
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
        self._project_root = project_root
        self.setVisible(True)
        self._title.setText(f"{candidate.accession_or_project} · {candidate.display_title or 'GEO 数据集'}")
        _fill_table(self._basic_table, _geo_detail_basic_rows(candidate))
        self._english_text.setPlainText(_geo_detail_english_text(candidate))
        profile = _build_geo_detail_profile(project_root, candidate, summary_payload)
        self._profile_text.setPlainText(_geo_profile_user_display(profile))
        self._confirm_comparison_button.setEnabled(bool(profile.candidate_comparisons and project_root is not None))
        self._manual_comparison_button.setEnabled(project_root is not None)
        self._asset_text.setPlainText(_geo_asset_detail_text(project_root, candidate.accession_or_project))
        self._render_download_candidates(project_root, candidate)
        self.set_saved(saved)
        self.set_pending_assets(saved and _candidate_has_pending_geo_assets(project_root, candidate.accession_or_project))
        if summary_payload:
            self.render_summary(candidate, summary_payload)
        else:
            self._translation_text.setPlainText("尚未生成中文翻译。")

    def set_saved(self, saved: bool) -> None:
        self._saved_status.setText("已在下载列表 / 待处理数据来源中。" if saved else "尚未加入下载列表 / 待处理数据来源。")
        self._save_button.setText("已保存" if saved else "保存")
        self._save_button.setEnabled(not saved)
        self._download_list_button.setEnabled(not saved)
        self._download_list_button.setVisible(not saved)
        self._remove_button.setVisible(saved)

    def set_pending_assets(self, pending: bool) -> None:
        self._download_assets_button.setVisible(pending)
        self._download_assets_button.setEnabled(pending)

    def render_summary(self, candidate: UnifiedDatasetCandidate, payload: dict[str, object]) -> None:
        self._translation_text.setPlainText(_geo_text_summary_user_display(candidate, payload))

    def set_busy_text(self, text: str) -> None:
        self._translation_text.setPlainText(text)

    def _render_download_candidates(self, project_root: Path | None, candidate: UnifiedDatasetCandidate) -> None:
        self._download_candidate_checks.clear()
        self._download_candidate_rows = []
        self._download_candidate_table.clearContents()
        self._download_candidate_table.setRowCount(0)
        if project_root is None:
            self._download_candidate_hint.setText("请先创建或打开生信分析项目后再保存 GEO 下载候选。")
            self._save_download_candidates_button.setEnabled(False)
            return
        manifest = build_gse_file_download_candidates(
            project_root=project_root,
            accession=candidate.accession_or_project,
            candidate_metadata=candidate.source_specific_metadata,
        )
        rows = [row for row in manifest.get("candidates", []) if isinstance(row, dict)]
        self._download_candidate_rows = rows
        self._download_candidate_table.setRowCount(len(rows))
        self._save_download_candidates_button.setEnabled(bool(rows))
        if not rows:
            self._download_candidate_hint.setText("尚未发现可下载文件候选。请先下载/读取 GEO 元数据或 asset manifest。")
            return
        selected_count = sum(1 for row in rows if row.get("selected"))
        self._download_candidate_hint.setText(
            f"已发现 {len(rows)} 个 GEO 文件候选，默认选择 {selected_count} 个。当前只是下载候选选择，不是分析结果；后续仍需要 recognition 和 standardization confirmation。"
        )
        for row_index, row in enumerate(rows):
            candidate_id = str(row.get("candidate_id") or "")
            check = QCheckBox()
            check.setChecked(bool(row.get("selected")))
            check.setToolTip("选择后将写入 B5.14 下载 handoff manifest。")
            self._download_candidate_checks[candidate_id] = check
            self._download_candidate_table.setCellWidget(row_index, 0, check)
            values = [
                str(row.get("file_name") or ""),
                str(row.get("predicted_role") or row.get("predicted_type") or ""),
                str(row.get("download_priority") or ""),
                "是" if row.get("suggested_for_download") else "否",
                str(row.get("risk_warning") or ""),
                str(row.get("file_source") or ""),
                _geo_download_candidate_use_text(row),
            ]
            for col_index, value in enumerate(values, start=1):
                item = QTableWidgetItem(value)
                self._download_candidate_table.setItem(row_index, col_index, item)
        _set_table_widths(self._download_candidate_table, [72, 240, 170, 90, 88, 260, 140, 260])
        self._download_candidate_table.resizeRowsToContents()
        self._download_candidate_status.setText("")

    def _save_download_candidate_selection(self) -> None:
        if self._candidate is None or self._project_root is None:
            self._download_candidate_status.setText("请先创建或打开项目。")
            return
        selected_ids = tuple(
            candidate_id
            for candidate_id, check in self._download_candidate_checks.items()
            if check.isChecked()
        )
        save_gse_file_download_candidate_selection(
            project_root=self._project_root,
            accession=self._candidate.accession_or_project,
            candidate_metadata=self._candidate.source_specific_metadata,
            selected_candidate_ids=selected_ids,
        )
        self._download_candidate_status.setText(f"已保存下载候选选择：{len(selected_ids)} 个文件。")

    def _emit_save(self) -> None:
        if self._candidate is not None:
            self.save_requested.emit(self._candidate)

    def _emit_add_to_download_list(self) -> None:
        if self._candidate is not None:
            self.add_to_download_list_requested.emit(self._candidate)

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
        self._empty = _muted("尚未添加数据来源。请先从上方三类入口导入或检索。")
        layout.addWidget(self._empty)
        self._batch_summary = _muted("")
        self._batch_summary.setObjectName("datasetBatchSummaryText")
        self._batch_summary.setWordWrap(True)
        self._batch_summary.setVisible(False)
        layout.addWidget(self._batch_summary)
        self._table = _table(["选择", "来源", "数据集 / 文件名", "数据状态", "可用内容", "需要补充", "备注", "操作"])
        self._table.setObjectName("geoDownloadListTable")
        self._table.setMinimumHeight(180)
        layout.addWidget(self._table)

        batch_row = QHBoxLayout()
        self._download_selected_button = _button("下载所选", "secondaryButton", self._emit_download_selected)
        self._delete_selected_button = _button("删除所选", "secondaryButton", self._emit_delete_selected)
        self._download_selected_button.setEnabled(False)
        self._delete_selected_button.setEnabled(False)
        batch_row.addStretch(1)
        batch_row.addWidget(self._download_selected_button)
        batch_row.addWidget(self._delete_selected_button)
        layout.addLayout(batch_row)

    def refresh(self, project_root: Path | None) -> None:
        entries = _current_project_dataset_entries(project_root, geo_only=self._geo_only, expand_geo_files=not self._geo_only)
        self._entries = entries
        self._checks = {}
        self._empty.setVisible(not entries)
        summary_text = _dataset_batch_summary_text(entries)
        self._batch_summary.setText(summary_text)
        self._batch_summary.setVisible(bool(summary_text))
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

    def _emit_download_selected(self) -> None:
        keys = self.selected_keys()
        if keys:
            self.download_selected_requested.emit(keys)

    def _emit_delete_selected(self) -> None:
        keys = self.selected_keys()
        if keys:
            self.delete_selected_requested.emit(keys)

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
        self._summary = _text_preview(190)
        self._summary.setObjectName("datasetDefaultSummary")
        layout.addWidget(self._summary)

        layout.addWidget(_muted("用户备注"))
        self._note_edit = QPlainTextEdit()
        self._note_edit.setObjectName("datasetUserNoteEdit")
        self._note_edit.setPlaceholderText("可记录筛选理由、疑问或后续处理计划，备注只作为笔记保存")
        self._note_edit.setMinimumHeight(48)
        self._note_edit.setMaximumHeight(76)
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
        self._tcga_preview_service = TCGAMetadataPreviewService()
        self._tcga_download_executor = TCGADownloadPlanExecutor()
        self._tcga_expression_builder = TCGAExpressionQuantificationBuilder()
        self._tcga_clinical_builder = TCGAClinicalMetadataBuilder()
        self._tcga_preview_summary: TCGAPreviewSummary | None = None
        self._tcga_download_plan_draft: TCGADownloadPlanDraft | None = None
        self._tcga_download_result: TCGADownloadExecutionResult | None = None
        self._tcga_expression_build_result: TCGAExpressionBuildResult | None = None
        self._tcga_clinical_build_result: TCGAClinicalBuildResult | None = None
        self._tcga_workflow_state: TCGAWorkflowState | None = None
        self._gtex_preview_service = GTExMetadataPreviewService()
        self._gtex_download_executor = GTExDownloadPlanExecutor()
        self._gtex_expression_builder = GTExExpressionMatrixBuilder()
        self._gtex_preview_summary: GTExPreviewSummary | None = None
        self._gtex_download_plan_draft: GTExDownloadPlanDraft | None = None
        self._gtex_download_result: GTExDownloadExecutionResult | None = None
        self._gtex_expression_build_result: GTExExpressionBuildResult | None = None
        self._gtex_workflow_state: GTExWorkflowState | None = None
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
            self._set_status("先添加数据，下一步进入数据检查与准备。")
        self._refresh_registered_sources()
        self._refresh_geo_download_list()
        self._refresh_tcga_download_plan_state()
        self._refresh_tcga_expression_build_state()
        self._refresh_tcga_clinical_build_state()
        self._refresh_tcga_workflow_state()
        self._refresh_gtex_workflow_state()

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
        return "中文研究主题检索已移动到独立页面。"

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
                "选择数据来源",
                "请选择数据来源。软件会根据所选数据库、研究目的和样本范围自动构建数据获取与检查流程。",
                back_text="返回项目首页",
                back_signal=self.back_requested,
            )
        )
        self._project_label = _status_label("请先创建或打开生信分析项目。")
        root.addWidget(self._project_label)
        self._status_label = _status_label("先添加数据，下一步进入数据检查与准备。")
        root.addWidget(self._status_label)

        root.addWidget(self._data_source_home_card())
        root.addWidget(self._geo_database_card())
        root.addWidget(self._gse_card())
        root.addWidget(self._research_card())
        root.addWidget(self._tcga_database_card())
        root.addWidget(self._gtex_database_card())
        root.addWidget(self._local_import_card())

        self._selection_status_card = self._data_selection_status_card()
        root.addWidget(self._selection_status_card)

        self._dataset_list_panel = GeoDownloadListPanel(title="下载列表 / 待处理数据来源")
        self._dataset_list_panel.view_requested.connect(self._show_dataset_detail)
        self._dataset_list_panel.download_selected_requested.connect(self._download_selected_dataset_entries)
        self._dataset_list_panel.delete_selected_requested.connect(self._delete_selected_dataset_entries)
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
        self._registered_count_label = _status_label("已保存数据来源：0 个；待处理：0 个；可识别：0 个")
        self._next_button = _button("下一步：数据检查与准备", "primaryButton", self.continue_to_recognition)
        self._next_button.setEnabled(False)
        actions.addWidget(self._registered_count_label)
        actions.addStretch(1)
        actions.addWidget(self._next_button)
        root.addWidget(actions_frame)

    def _data_source_home_card(self) -> QFrame:
        card, layout = _card("选择数据来源")
        card.setObjectName("dataSourceEntryHomeCard")
        layout.addWidget(_muted("GEO 保留现有真实下载能力；TCGA 与 GTEx 本阶段先建立中文类目、选择流程和任务草案。"))
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(SPACING["md"])
        grid.setVerticalSpacing(SPACING["sm"])
        entries = (
            ("GEO 数据库", "GSE 编号、中文研究问题检索、本地 GEO 文件导入", "geo", "openGeoDatabaseButton"),
            ("TCGA 数据库", "按癌种选择 TCGA 项目并构建分析数据集", "tcga", "openTcgaDatabaseButton"),
            ("GTEx 数据库", "按正常组织选择 GTEx 表达数据", "gtex", "openGtexDatabaseButton"),
            ("本地数据导入", "导入已有表达矩阵、样本注释或分析结果", "local", "openLocalImportButton"),
        )
        for index, (title, description, key, object_name) in enumerate(entries):
            entry = QFrame()
            entry.setObjectName(f"dataSourceEntry_{key}")
            entry_layout = QVBoxLayout(entry)
            entry_layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
            entry_layout.setSpacing(SPACING["xs"])
            label = QLabel(title)
            label.setObjectName("bioProjectCardTitle")
            label.setWordWrap(True)
            entry_layout.addWidget(label)
            entry_layout.addWidget(_muted(description))
            button = _button("进入", "primaryButton", lambda checked=False, target=key: self._jump_to_data_source_section(target))
            button.setObjectName(object_name)
            entry_layout.addWidget(button, alignment=Qt.AlignLeft)
            grid.addWidget(entry, index // 2, index % 2)
        layout.addLayout(grid)
        return card

    def _geo_database_card(self) -> QFrame:
        card, layout = _card("GEO 数据库")
        card.setObjectName("geoDatabaseSectionCard")
        layout.addWidget(_muted("GEO 专区保留 GSE 编号检索/下载、中文研究问题检索和本地 GEO 文件导入入口。下载或导入完成后仍进入当前数据检查与准备。"))
        return card

    def _jump_to_data_source_section(self, target: str) -> None:
        labels = {
            "geo": "已进入 GEO 数据库区域；可按 GSE 编号检索，或进入中文研究问题检索。",
            "tcga": "已进入 TCGA 数据库区域；本阶段生成任务草案，不执行真实 GDC 下载。",
            "gtex": "已进入 GTEx 数据库区域；本阶段生成任务草案，不作为 TCGA 自动对照。",
            "local": "已进入本地数据导入区域。",
        }
        if target == "geo":
            self._gse_input.setFocus()
        elif target == "tcga":
            self._tcga_project_combo.setFocus()
        elif target == "gtex":
            self._gtex_tissue_combo.setFocus()
        elif target == "local":
            self._local_strategy_combo.setFocus()
        self._set_status(labels.get(target, "请选择数据来源。"))

    def _local_import_card(self) -> QFrame:
        card, layout = _card("本地数据导入")
        card.setObjectName("localImportEntryCard")
        layout.addWidget(_muted("用于导入表达矩阵、样本信息、临床表或已下载数据。"))
        self._local_strategy_combo = QComboBox()
        self._local_strategy_combo.setObjectName("localImportStrategyCombo")
        self._local_strategy_combo.addItems(["复制到项目（推荐）", "保留原位置，仅记录路径"])
        layout.addWidget(self._local_strategy_combo)
        select_button = _button("选择本地文件或文件夹", "primaryButton", self._choose_local_data)
        select_button.setMinimumHeight(44)
        actions = QHBoxLayout()
        actions.addWidget(select_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addWidget(self._source_summary_frame("local_import", "尚未选择本地数据。", detail_button_text="查看导入详情"))
        return card

    def _gse_card(self) -> QFrame:
        card, layout = _card("按 GSE 编号检索/下载")
        card.setObjectName("gseSearchEntryCard")
        layout.addWidget(_muted("已知 GEO 数据集编号时使用，可查看详情并加入项目数据来源。"))
        self._gse_input = QLineEdit()
        self._gse_input.setPlaceholderText("请输入 GSE 编号，例如 GSE60235")
        self._gse_input.setMinimumHeight(44)
        layout.addWidget(self._gse_input)
        gse_actions = QHBoxLayout()
        search_button = _button("检索", "primaryButton", self.search_gse_dataset)
        search_button.setMinimumHeight(44)
        self._register_gse_button = _button("添加到项目", "secondaryButton", self.register_gse_dataset)
        self._register_gse_button.setEnabled(False)
        self._register_gse_button.setVisible(False)
        gse_actions.addWidget(search_button)
        gse_actions.addWidget(self._register_gse_button)
        gse_actions.addStretch(1)
        layout.addLayout(gse_actions)
        self._gse_status_label = _status_label("尚未检索 GSE 数据集。")
        layout.addWidget(self._gse_status_label)
        self._gse_summary_table = _table(["GSE 编号", "数据集标题", "平台", "样本数量", "数据状态"])
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
        self._gse_geo_detail_panel.add_to_download_list_requested.connect(self._save_gse_geo_candidate)
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
        card, layout = _card("按中文研究问题检索 GEO 数据集")
        card.setObjectName("chineseResearchSearchEntryCard")
        layout.addWidget(_muted("面向 GEO 的中文研究问题检索入口；TCGA / GTEx 请选择各自数据库页面。"))
        self._chinese_query_input = QLineEdit()
        self._chinese_query_input.setObjectName("chineseResearchTopicEntry")
        self._chinese_query_input.setPlaceholderText("请输入研究方向，例如：甲状腺癌与肥胖相关基因表达数据")
        self._chinese_query_input.setMinimumHeight(44)
        layout.addWidget(self._chinese_query_input)
        self._chinese_search_status_label = _status_label("尚未进行中文检索。")
        layout.addWidget(self._chinese_search_status_label)
        button = _button("进入中文主题检索", "primaryButton", self.open_chinese_search)
        button.setMinimumHeight(44)
        layout.addWidget(button, alignment=Qt.AlignLeft)
        return card

    def _tcga_database_card(self) -> QFrame:
        card, layout = _card("TCGA 数据库")
        card.setObjectName("tcgaDatabaseEntryCard")
        layout.addWidget(_muted("请选择癌种、分析目的和样本范围。本步骤仅预览 TCGA 可下载数据，不会下载大文件。"))
        layout.addWidget(_muted("软件会根据分析目的自动选择所需数据类型；下载计划草案不会进入差异分析或 GSEA。"))
        self._tcga_project_combo = QComboBox()
        self._tcga_project_combo.setObjectName("tcgaProjectCombo")
        for group, projects in grouped_tcga_projects().items():
            for project in projects:
                self._tcga_project_combo.addItem(f"{group} / {project.chinese_name} ({project.project_id})", project.project_id)
        self._tcga_purpose_combo = QComboBox()
        self._tcga_purpose_combo.setObjectName("tcgaAnalysisPurposeCombo")
        for purpose in TCGA_ANALYSIS_PURPOSES:
            self._tcga_purpose_combo.addItem(purpose.chinese_name, purpose.purpose_id)
        self._tcga_sample_scope_combo = QComboBox()
        self._tcga_sample_scope_combo.setObjectName("tcgaSampleScopeCombo")
        for scope in TCGA_SAMPLE_SCOPES:
            self._tcga_sample_scope_combo.addItem(scope.chinese_name, scope.scope_id)
        form = QGridLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(SPACING["md"])
        form.setVerticalSpacing(SPACING["sm"])
        form.addWidget(QLabel("癌种项目"), 0, 0)
        form.addWidget(self._tcga_project_combo, 0, 1)
        form.addWidget(QLabel("分析目的"), 1, 0)
        form.addWidget(self._tcga_purpose_combo, 1, 1)
        form.addWidget(QLabel("样本范围"), 2, 0)
        form.addWidget(self._tcga_sample_scope_combo, 2, 1)
        layout.addLayout(form)
        self._tcga_preview_table = _table(["项目", "分析目的", "样本范围", "预览状态", "case", "sample", "file", "预计大小"])
        self._tcga_preview_table.setObjectName("tcgaPreviewTable")
        self._tcga_preview_table.setMaximumHeight(128)
        layout.addWidget(self._tcga_preview_table)
        self._tcga_sample_type_table = _table(["样本类型", "数量"])
        self._tcga_sample_type_table.setObjectName("tcgaSampleTypeDistributionTable")
        self._tcga_sample_type_table.setMaximumHeight(150)
        layout.addWidget(self._tcga_sample_type_table)
        self._tcga_summary_text = _text_preview(118)
        self._tcga_summary_text.setObjectName("tcgaMetadataPreviewSummary")
        self._tcga_summary_text.setPlainText("尚未预览。点击“预览可下载数据”后显示 case/sample/file 和预计下载内容。")
        layout.addWidget(self._tcga_summary_text)
        self._tcga_warning_text = _text_preview(92)
        self._tcga_warning_text.setObjectName("tcgaMetadataPreviewWarnings")
        self._tcga_warning_text.setPlainText("风险/限制提示会显示在这里。TCGA 与 GTEx 不会被自动合并。")
        layout.addWidget(self._tcga_warning_text)
        self._tcga_status_label = _status_label("当前阶段已建立 TCGA 中文类目和任务流程。可先执行真实 GDC metadata 预览。")
        layout.addWidget(self._tcga_status_label)
        layout.addWidget(_muted("TCGA 数据构建流程"))
        self._tcga_workflow_table = _table(["步骤", "状态", "摘要", "下一步"])
        self._tcga_workflow_table.setObjectName("tcgaWorkflowStepsTable")
        self._tcga_workflow_table.setMinimumHeight(190)
        self._tcga_workflow_table.setMaximumHeight(240)
        layout.addWidget(self._tcga_workflow_table)
        self._tcga_workflow_summary_text = _text_preview(92)
        self._tcga_workflow_summary_text.setObjectName("tcgaWorkflowSummary")
        self._tcga_workflow_summary_text.setPlainText("请选择 TCGA project 后按步骤预览、下载、构建表达矩阵和获取临床信息。")
        layout.addWidget(self._tcga_workflow_summary_text)
        actions = QHBoxLayout()
        preview_button = _button("预览可下载数据", "primaryButton", self.preview_tcga_downloadable_data)
        preview_button.setObjectName("previewTcgaDownloadableDataButton")
        self._tcga_preview_button = preview_button
        self._tcga_plan_button = _button("生成下载计划草案", "secondaryButton", self.create_tcga_download_plan_draft)
        self._tcga_plan_button.setObjectName("createTcgaDownloadPlanDraftButton")
        self._tcga_plan_button.setEnabled(False)
        self._tcga_download_button = _button("下载 TCGA 原始文件", "secondaryButton", self.download_tcga_raw_files)
        self._tcga_download_button.setObjectName("downloadTcgaRawFilesButton")
        self._tcga_download_button.setEnabled(False)
        self._tcga_expression_build_button = _button("构建 TCGA 表达矩阵", "secondaryButton", self.build_tcga_expression_matrix)
        self._tcga_expression_build_button.setObjectName("buildTcgaExpressionMatrixButton")
        self._tcga_expression_build_button.setEnabled(False)
        self._tcga_clinical_build_button = _button("获取 TCGA 临床信息", "secondaryButton", self.fetch_tcga_clinical_metadata)
        self._tcga_clinical_build_button.setObjectName("fetchTcgaClinicalMetadataButton")
        self._tcga_clinical_build_button.setEnabled(False)
        self._tcga_data_check_button = _button("进入数据检查与准备", "primaryButton", self.continue_to_recognition)
        self._tcga_data_check_button.setObjectName("enterTcgaDataCheckButton")
        self._tcga_data_check_button.setEnabled(False)
        self._tcga_data_check_button.setVisible(False)
        self._tcga_data_check_button.setText("进入准备")
        actions.addWidget(preview_button)
        actions.addWidget(self._tcga_plan_button)
        actions.addWidget(self._tcga_download_button)
        actions.addWidget(self._tcga_expression_build_button)
        actions.addWidget(self._tcga_clinical_build_button)
        actions.addWidget(self._tcga_data_check_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        self._tcga_download_status_text = _text_preview(88)
        self._tcga_download_status_text.setObjectName("tcgaRawDownloadStatus")
        self._tcga_download_status_text.setPlainText("尚未生成下载计划草案。")
        layout.addWidget(self._tcga_download_status_text)
        self._tcga_expression_build_status_text = _text_preview(88)
        self._tcga_expression_build_status_text.setObjectName("tcgaExpressionBuildStatus")
        self._tcga_expression_build_status_text.setPlainText("尚未获取 TCGA 原始表达文件。")
        layout.addWidget(self._tcga_expression_build_status_text)
        self._tcga_clinical_build_status_text = _text_preview(92)
        self._tcga_clinical_build_status_text.setObjectName("tcgaClinicalBuildStatus")
        self._tcga_clinical_build_status_text.setPlainText("尚未构建 TCGA clinical metadata。")
        layout.addWidget(self._tcga_clinical_build_status_text)
        developer_actions = QHBoxLayout()
        developer_actions.addWidget(_button("展开开发者诊断", "secondaryButton", lambda: _toggle_details(self._tcga_developer_details)))
        developer_actions.addStretch(1)
        layout.addLayout(developer_actions)
        self._tcga_developer_details = _text_preview(150)
        self._tcga_developer_details.setObjectName("tcgaMetadataPreviewDeveloperDiagnostics")
        self._tcga_developer_details.setVisible(False)
        layout.addWidget(self._tcga_developer_details)
        self._tcga_project_combo.currentIndexChanged.connect(lambda _: self._refresh_tcga_preview())
        self._tcga_purpose_combo.currentIndexChanged.connect(lambda _: self._refresh_tcga_preview())
        self._tcga_sample_scope_combo.currentIndexChanged.connect(lambda _: self._refresh_tcga_preview())
        self._refresh_tcga_preview()
        return card

    def _gtex_database_card(self) -> QFrame:
        card, layout = _card("GTEx 数据库")
        card.setObjectName("gtexDatabaseEntryCard")
        layout.addWidget(_muted("请选择正常组织和使用目的。GTEx 将作为独立正常组织表达资源管理，不作为 TCGA 的自动合并对照。"))
        self._gtex_tissue_combo = QComboBox()
        self._gtex_tissue_combo.setObjectName("gtexTissueCombo")
        for group, tissues in grouped_gtex_tissues().items():
            for tissue in tissues:
                self._gtex_tissue_combo.addItem(f"{group} / {tissue.chinese_name} ({tissue.tissue_site_detail})", tissue.tissue_id)
        self._gtex_purpose_combo = QComboBox()
        self._gtex_purpose_combo.setObjectName("gtexUsePurposeCombo")
        for purpose in GTEX_USE_PURPOSES:
            self._gtex_purpose_combo.addItem(purpose.chinese_name, purpose.purpose_id)
        form = QGridLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(SPACING["md"])
        form.setVerticalSpacing(SPACING["sm"])
        form.addWidget(QLabel("组织"), 0, 0)
        form.addWidget(self._gtex_tissue_combo, 0, 1)
        form.addWidget(QLabel("使用目的"), 1, 0)
        form.addWidget(self._gtex_purpose_combo, 1, 1)
        layout.addLayout(form)
        self._gtex_preview_table = _table(["组织大类", "具体组织", "使用目的", "预览状态", "sample", "file"])
        self._gtex_preview_table.setObjectName("gtexPreviewTable")
        self._gtex_preview_table.setMaximumHeight(120)
        layout.addWidget(self._gtex_preview_table)
        self._gtex_status_label = _status_label("GTEx 作为独立正常组织表达资源管理，不自动作为 TCGA normal control。")
        layout.addWidget(self._gtex_status_label)
        self._gtex_workflow_table = _table(["步骤", "状态", "摘要", "下一步"])
        self._gtex_workflow_table.setObjectName("gtexWorkflowStepsTable")
        self._gtex_workflow_table.setMinimumHeight(160)
        self._gtex_workflow_table.setMaximumHeight(220)
        layout.addWidget(self._gtex_workflow_table)
        self._gtex_workflow_summary_text = _text_preview(86)
        self._gtex_workflow_summary_text.setObjectName("gtexWorkflowSummary")
        self._gtex_workflow_summary_text.setPlainText("按步骤预览、下载并构建 GTEx 独立正常组织表达资源。")
        layout.addWidget(self._gtex_workflow_summary_text)
        gtex_actions = QHBoxLayout()
        self._gtex_preview_button = _button("预览 GTEx 可下载数据", "primaryButton", self.preview_gtex_downloadable_data)
        self._gtex_preview_button.setObjectName("previewGtexDownloadableDataButton")
        self._gtex_plan_button = _button("生成 GTEx 下载计划草案", "secondaryButton", self.create_gtex_download_plan_draft)
        self._gtex_plan_button.setObjectName("createGtexDownloadPlanDraftButton")
        self._gtex_plan_button.setEnabled(False)
        self._gtex_download_button = _button("下载 GTEx 原始文件", "secondaryButton", self.download_gtex_raw_files)
        self._gtex_download_button.setObjectName("downloadGtexRawFilesButton")
        self._gtex_download_button.setEnabled(False)
        self._gtex_expression_build_button = _button("构建 GTEx 表达矩阵", "secondaryButton", self.build_gtex_expression_matrix)
        self._gtex_expression_build_button.setObjectName("buildGtexExpressionMatrixButton")
        self._gtex_expression_build_button.setEnabled(False)
        self._gtex_data_check_button = _button("进入数据检查与准备", "primaryButton", self.continue_to_recognition)
        self._gtex_data_check_button.setObjectName("enterGtexDataCheckButton")
        self._gtex_data_check_button.setEnabled(False)
        self._gtex_data_check_button.setVisible(False)
        self._gtex_data_check_button.setText("进入准备")
        legacy_button = _button("下载并构建数据集", "secondaryButton", self.create_gtex_source_request)
        legacy_button.setObjectName("createGtexDataSourceRequestButton")
        legacy_button.setVisible(False)
        for button in (self._gtex_preview_button, self._gtex_plan_button, self._gtex_download_button, self._gtex_expression_build_button, self._gtex_data_check_button, legacy_button):
            gtex_actions.addWidget(button)
        gtex_actions.addStretch(1)
        layout.addLayout(gtex_actions)
        self._gtex_status_text = _text_preview(90)
        self._gtex_status_text.setObjectName("gtexWorkflowStatus")
        self._gtex_status_text.setPlainText("尚未预览 GTEx metadata。")
        layout.addWidget(self._gtex_status_text)
        self._gtex_developer_details = _text_preview(130)
        self._gtex_developer_details.setObjectName("gtexDeveloperDiagnostics")
        self._gtex_developer_details.setVisible(False)
        layout.addWidget(self._gtex_developer_details)
        self._gtex_tissue_combo.currentIndexChanged.connect(lambda _: self._refresh_gtex_preview())
        self._gtex_purpose_combo.currentIndexChanged.connect(lambda _: self._refresh_gtex_preview())
        self._refresh_gtex_preview()
        return card

    def _refresh_tcga_preview(self) -> None:
        if not hasattr(self, "_tcga_preview_table"):
            return
        self._tcga_preview_summary = None
        self._tcga_download_plan_draft = None
        if hasattr(self, "_tcga_plan_button"):
            self._tcga_plan_button.setEnabled(False)
        project = get_tcga_project(str(self._tcga_project_combo.currentData() or "TCGA-THCA"))
        purpose = get_tcga_analysis_purpose(str(self._tcga_purpose_combo.currentData() or "differential_expression"))
        scope = get_tcga_sample_scope(str(self._tcga_sample_scope_combo.currentData() or "tumor"))
        request = build_tcga_preview_request(project=project, purpose=purpose, scope=scope)
        _fill_table(
            self._tcga_preview_table,
            [
                [
                    f"{project.chinese_name} ({project.project_id})",
                    purpose.chinese_name,
                    scope.chinese_name,
                    "尚未预览",
                    "-",
                    "-",
                    "-",
                    "-",
                ]
            ],
        )
        _fill_table(self._tcga_sample_type_table, [[sample_type, "-"] for sample_type in request.sample_types] or [["全部可用样本", "-"]])
        expected = "、".join(_user_asset_label(asset) for asset in purpose.required_internal_assets)
        if hasattr(self, "_tcga_summary_text"):
            self._tcga_summary_text.setPlainText(
                "预计内容："
                + (expected or "项目元数据")
                + "\n本阶段仅预览可下载数据，不执行下载和矩阵构建。"
            )
        if hasattr(self, "_tcga_warning_text"):
            self._tcga_warning_text.setPlainText("尚未执行 GDC metadata 预览。下载计划草案不会进入 DEG/GSEA ready。")
        if hasattr(self, "_tcga_developer_details"):
            self._tcga_developer_details.setPlainText("")
        self._refresh_tcga_download_plan_state()
        self._refresh_tcga_workflow_state()

    def preview_tcga_downloadable_data(self) -> TCGAPreviewSummary | None:
        project = get_tcga_project(str(self._tcga_project_combo.currentData() or ""))
        purpose = get_tcga_analysis_purpose(str(self._tcga_purpose_combo.currentData() or ""))
        scope = get_tcga_sample_scope(str(self._tcga_sample_scope_combo.currentData() or ""))
        request = build_tcga_preview_request(project=project, purpose=purpose, scope=scope)
        self._tcga_status_label.setText("正在查询 GDC metadata，请稍候。")
        QApplication.processEvents()
        summary = self._tcga_preview_service.build_preview(request)
        self._tcga_preview_summary = summary
        self._tcga_download_plan_draft = None
        self._render_tcga_metadata_preview(summary)
        self._refresh_tcga_workflow_state()
        if summary.status == "failed":
            self._set_status("TCGA metadata 预览失败；请稍后重试或更换条件。", error=True)
        elif summary.status == "empty":
            self._set_status("未找到符合当前项目、分析目的和样本范围的数据。", error=True)
        else:
            self._set_status("TCGA metadata 预览已生成；如满足条件，可生成下载计划草案。")
        return summary

    def _render_tcga_metadata_preview(self, summary: TCGAPreviewSummary) -> None:
        status_text = _tcga_preview_status_text(summary)
        _fill_table(
            self._tcga_preview_table,
            [
                [
                    f"{summary.request.project_label_zh} ({summary.request.project_id})",
                    summary.request.analysis_purpose_zh,
                    summary.request.sample_scope_zh,
                    status_text,
                    str(summary.case_count),
                    str(summary.sample_count),
                    str(summary.file_count),
                    format_bytes_zh(summary.estimated_size_bytes, has_unknown=summary.size_has_unknown),
                ]
            ],
        )
        sample_rows = [[sample_type, str(count)] for sample_type, count in summary.sample_type_counts.items()]
        _fill_table(self._tcga_sample_type_table, sample_rows or [["未返回样本类型", "0"]])
        self._tcga_summary_text.setPlainText(_tcga_preview_summary_text(summary))
        self._tcga_warning_text.setPlainText("\n".join(summary.warnings) if summary.warnings else "未发现阻断性提示。")
        self._tcga_developer_details.setPlainText(_json(_tcga_preview_developer_payload(summary)))
        self._tcga_plan_button.setEnabled(summary.is_download_plan_available)
        if summary.is_download_plan_available:
            self._tcga_status_label.setText("TCGA metadata 预览完成，可生成下载计划草案；不会下载文件。")
        elif summary.status == "failed":
            self._tcga_status_label.setText("TCGA metadata 预览失败，未生成下载计划。")
        else:
            self._tcga_status_label.setText("当前预览不满足生成下载计划草案条件。")

    def _refresh_gtex_preview(self) -> None:
        if not hasattr(self, "_gtex_preview_table"):
            return
        tissue = get_gtex_tissue(str(self._gtex_tissue_combo.currentData() or "gtex_thyroid"))
        purpose = get_gtex_use_purpose(str(self._gtex_purpose_combo.currentData() or "normal_expression_view"))
        _fill_table(
            self._gtex_preview_table,
            [
                [
                    tissue.tissue_group,
                    f"{tissue.chinese_name} ({tissue.tissue_site_detail})",
                    purpose.chinese_name,
                    "尚未预览",
                    "-",
                    "-",
                ]
            ],
        )
        self._gtex_preview_summary = None
        self._gtex_download_plan_draft = None
        if hasattr(self, "_gtex_plan_button"):
            self._gtex_plan_button.setEnabled(False)
        if hasattr(self, "_gtex_status_text"):
            self._gtex_status_text.setPlainText("尚未预览 GTEx metadata。GTEx 不自动作为 TCGA normal control。")
        self._refresh_gtex_workflow_state()

    def preview_gtex_downloadable_data(self) -> GTExPreviewSummary | None:
        tissue = get_gtex_tissue(str(self._gtex_tissue_combo.currentData() or ""))
        purpose = get_gtex_use_purpose(str(self._gtex_purpose_combo.currentData() or ""))
        request = build_gtex_preview_request(tissue=tissue, purpose=purpose)
        self._gtex_status_label.setText("正在查询 GTEx metadata，请稍候。")
        QApplication.processEvents()
        summary = self._gtex_preview_service.build_preview(request)
        self._gtex_preview_summary = summary
        self._gtex_download_plan_draft = None
        self._render_gtex_preview(summary)
        self._refresh_gtex_workflow_state()
        if summary.status == "failed":
            self._set_status("GTEx metadata 预览失败；请稍后重试。", error=True)
        elif summary.status == "empty":
            self._set_status("未找到 GTEx metadata 或表达文件。", error=True)
        else:
            self._set_status("GTEx metadata 预览已生成；如有公共表达文件，可生成下载计划草案。")
        return summary

    def _render_gtex_preview(self, summary: GTExPreviewSummary) -> None:
        _fill_table(
            self._gtex_preview_table,
            [[summary.request.tissue_group, f"{summary.request.tissue_label_zh} ({summary.request.tissue_site_detail})", summary.request.use_purpose_zh, _gtex_preview_status_text(summary), str(summary.sample_count), str(summary.file_count)]],
        )
        self._gtex_plan_button.setEnabled(summary.is_download_plan_available)
        self._gtex_status_text.setPlainText(
            "\n".join(
                [
                    f"组织：{summary.request.tissue_label_zh} ({summary.request.tissue_site_detail})",
                    f"sample：{summary.sample_count}；donor：{summary.donor_count}；file：{summary.file_count}",
                    "GTEx 是独立正常组织表达资源，不自动作为 TCGA normal control，也不自动与 TCGA 合并。",
                    "提示：" + ("；".join(summary.warnings[:3]) if summary.warnings else "无"),
                ]
            )
        )
        self._gtex_developer_details.setPlainText(_json({"preview_summary": summary.to_dict()}))

    def create_tcga_source_request(self) -> AcquisitionSummary | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        project = get_tcga_project(str(self._tcga_project_combo.currentData() or ""))
        purpose = get_tcga_analysis_purpose(str(self._tcga_purpose_combo.currentData() or ""))
        scope = get_tcga_sample_scope(str(self._tcga_sample_scope_combo.currentData() or ""))
        warnings = (
            "真实 GDC 查询与下载将在下一阶段接入；本阶段不伪造 case/sample/file 数。",
            "TCGA request 处于等待下载与构建状态，不进入 DEG/GSEA ready。",
        )
        draft = create_data_source_request(
            self._project_root,
            source_type="TCGA",
            user_title=f"TCGA 数据库 - {project.chinese_name}",
            user_selection_summary=f"{project.chinese_name} / {purpose.chinese_name} / {scope.chinese_name}",
            internal_selection={
                "project_id": project.project_id,
                "short_code": project.short_code,
                "analysis_purpose": purpose.purpose_id,
                "sample_scope": scope.scope_id,
                "internal_sample_types": list(scope.internal_sample_types),
                "readiness_profile": purpose.readiness_profile,
            },
            expected_assets=purpose.required_internal_assets,
            warnings=warnings,
            status="pending_download",
        )
        summary = register_acquisition(
            self._project_root,
            source_type="tcga_project",
            source_label=project.project_id,
            strategy="plan_only",
            selected_paths=[],
            metadata={
                "source": "tcga_gdc",
                "ui_source": "tcga_database_page",
                "registration_status": "registered_as_planned_source",
                "download_status": "registered_pending_tcga_build",
                "ready_for_recognition": "pending_download",
                "data_source_request_id": draft.request.request_id,
                "data_source_request_path": str(draft.request_path),
                "project_id": project.project_id,
                "short_code": project.short_code,
                "chinese_name": project.chinese_name,
                "english_name": project.english_name,
                "organ_system": project.organ_system,
                "analysis_purpose": purpose.purpose_id,
                "analysis_purpose_zh": purpose.chinese_name,
                "sample_scope": scope.scope_id,
                "sample_scope_zh": scope.chinese_name,
                "expected_assets": list(purpose.required_internal_assets),
                "display_title_zh": f"TCGA {project.chinese_name}",
                "warnings": list(warnings),
            },
        )
        self._latest_summary = summary
        self._tcga_status_label.setText(f"已生成 TCGA 任务草案：{project.project_id}；等待下一阶段真实 GDC 查询与下载。")
        self._refresh_registered_sources()
        self._set_status("TCGA 数据源 request 草案已生成；不会执行虚假下载，也不会进入真实分析 ready。")
        return summary

    def create_tcga_download_plan_draft(self) -> AcquisitionSummary | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        summary = self._tcga_preview_summary
        if summary is None:
            self._set_status("请先点击“预览可下载数据”。", error=True)
            return None
        if not summary.is_download_plan_available:
            self._set_status("当前预览没有可用表达文件，不能生成下载计划草案。", error=True)
            return None
        draft = write_tcga_download_plan_draft(self._project_root, summary)
        self._tcga_download_plan_draft = draft
        project = get_tcga_project(summary.request.project_id)
        purpose = get_tcga_analysis_purpose(summary.request.analysis_purpose)
        scope = get_tcga_sample_scope(summary.request.sample_scope)
        warnings = tuple(dict.fromkeys((
            *summary.warnings,
            "本阶段只生成 TCGA/GDC 下载计划草案，不下载大文件。",
            "TCGA 下载计划草案不写 source_files，不进入 DEG/GSEA ready。",
        )))
        request_draft = create_data_source_request(
            self._project_root,
            source_type="TCGA",
            user_title=f"TCGA 数据库 - {project.chinese_name}",
            user_selection_summary=f"{project.chinese_name} / {purpose.chinese_name} / {scope.chinese_name}",
            internal_selection={
                "project_id": project.project_id,
                "short_code": project.short_code,
                "analysis_purpose": purpose.purpose_id,
                "sample_scope": scope.scope_id,
                "internal_sample_types": list(scope.internal_sample_types),
                "readiness_profile": purpose.readiness_profile,
                "metadata_preview": summary.to_dict(),
                "download_plan_draft_path": str(draft.plan_path),
                "download_plan_status": draft.status,
            },
            expected_assets=purpose.required_internal_assets,
            warnings=warnings,
            status="download_plan_draft",
        )
        acquisition = register_acquisition(
            self._project_root,
            source_type="tcga_project",
            source_label=project.project_id,
            strategy="plan_only",
            selected_paths=[],
            metadata={
                "source": "tcga_gdc",
                "ui_source": "tcga_database_page",
                "registration_status": "registered_as_planned_source",
                "download_status": "tcga_gdc_download_plan_draft_created",
                "ready_for_recognition": "pending_download",
                "data_source_request_id": request_draft.request.request_id,
                "data_source_request_path": str(request_draft.request_path),
                "download_plan_draft_id": draft.plan_id,
                "download_plan_draft_path": str(draft.plan_path),
                "download_plan_status": draft.status,
                "project_id": project.project_id,
                "short_code": project.short_code,
                "chinese_name": project.chinese_name,
                "english_name": project.english_name,
                "organ_system": project.organ_system,
                "analysis_purpose": purpose.purpose_id,
                "analysis_purpose_zh": purpose.chinese_name,
                "sample_scope": scope.scope_id,
                "sample_scope_zh": scope.chinese_name,
                "expected_assets": list(purpose.required_internal_assets),
                "metadata_preview_summary": summary.to_dict(),
                "tcga_preview_file_count": summary.file_count,
                "tcga_preview_case_count": summary.case_count,
                "tcga_preview_sample_count": summary.sample_count,
                "tcga_preview_estimated_size": format_bytes_zh(summary.estimated_size_bytes, has_unknown=summary.size_has_unknown),
                "display_title_zh": f"TCGA {project.chinese_name}",
                "warnings": list(warnings),
            },
        )
        self._latest_summary = acquisition
        self._tcga_status_label.setText(f"已生成 TCGA 下载计划草案：{project.project_id}；未下载文件。")
        self._refresh_tcga_download_plan_state()
        self._refresh_tcga_workflow_state()
        self._refresh_registered_sources()
        self._refresh_geo_download_list()
        self._set_status("TCGA 下载计划草案已生成；未写 source_files，也不会进入真实分析 ready。")
        return acquisition

    def download_tcga_raw_files(self) -> TCGADownloadExecutionResult | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        plan_path = latest_tcga_download_plan_path(self._project_root, project_id=self._selected_tcga_project_id())
        if plan_path is None:
            self._tcga_download_status_text.setPlainText("未找到 TCGA 下载计划草案，请先生成 B6.2 下载计划。")
            self._set_status("未找到 TCGA 下载计划草案。", error=True)
            return None
        self._tcga_download_status_text.setPlainText("正在下载 TCGA/GDC 原始文件；已存在文件会直接计为缓存命中。")
        self._tcga_status_label.setText("正在执行 TCGA 原始文件下载，请稍候。")
        QApplication.processEvents()
        try:
            result = self._tcga_download_executor.execute_plan(self._project_root, plan_path=plan_path)
        except Exception as exc:
            self._tcga_download_status_text.setPlainText(f"TCGA 下载执行失败：{exc}")
            self._set_status(f"TCGA 下载执行失败：{exc}", error=True)
            return None
        self._tcga_download_result = result
        self._render_tcga_download_result(result)
        self._refresh_registered_sources()
        self._refresh_geo_download_list()
        self._refresh_tcga_expression_build_state()
        self._refresh_tcga_workflow_state()
        self._set_status("TCGA 原始文件已获取，等待 B6.4 构建表达矩阵；当前不会进入 DEG/GSEA ready。")
        return result

    def _render_tcga_download_result(self, result: TCGADownloadExecutionResult) -> None:
        self._tcga_download_status_text.setPlainText(
            "\n".join(
                [
                    f"下载状态：{result.message}",
                    f"成功：{result.success_count}；缓存：{result.cache_hit_count}；失败：{result.failed_count}；阻断：{result.blocked_count}；跳过：{result.skipped_count}",
                    f"总大小：{format_bytes_zh(result.total_size_bytes)}",
                    f"本地缓存路径：{result.target_dir}",
                    f"receipt：{result.receipt_path}",
                ]
            )
        )
        self._tcga_status_label.setText("TCGA 原始文件已获取，等待 B6.4 构建表达矩阵。")

    def build_tcga_expression_matrix(self) -> TCGAExpressionBuildResult | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        record_path = latest_tcga_raw_expression_record_path(self._project_root, project_id=self._selected_tcga_project_id())
        if record_path is None:
            self._tcga_expression_build_status_text.setPlainText("未找到等待 B6.4 构建的 TCGA 原始文件记录。")
            self._set_status("未找到等待 B6.4 构建的 TCGA 原始文件记录。", error=True)
            return None
        self._tcga_expression_build_status_text.setPlainText("正在解析 TCGA expression quantification 文件并构建本地表达矩阵。")
        self._tcga_status_label.setText("正在构建 TCGA 表达矩阵，请稍候。")
        QApplication.processEvents()
        try:
            result = self._tcga_expression_builder.build_from_record(self._project_root, record_path=record_path)
        except Exception as exc:
            self._tcga_expression_build_status_text.setPlainText(f"TCGA 表达矩阵构建失败：{exc}")
            self._set_status(f"TCGA 表达矩阵构建失败：{exc}", error=True)
            return None
        self._tcga_expression_build_result = result
        self._render_tcga_expression_build_result(result)
        self._refresh_registered_sources()
        self._refresh_geo_download_list()
        self._refresh_tcga_expression_build_state()
        self._refresh_tcga_clinical_build_state()
        self._refresh_tcga_workflow_state()
        self._set_status("TCGA 表达矩阵已构建，等待统一数据检查与准备；仍不会直接进入 DEG/GSEA ready。")
        return result

    def _render_tcga_expression_build_result(self, result: TCGAExpressionBuildResult) -> None:
        warning_line = f"警告：{len(result.warnings)} 条" if result.warnings else "警告：无"
        self._tcga_expression_build_status_text.setPlainText(
            "\n".join(
                [
                    f"构建状态：{result.message}",
                    f"解析文件：{result.parsed_file_count}/{result.source_file_count}",
                    f"样本：{result.sample_count}；基因：{result.gene_count}",
                    f"counts 矩阵：{result.expression_matrix_path}",
                    f"sample metadata：{result.sample_metadata_path}",
                    f"sample mapping：{result.sample_mapping_path}",
                    f"build manifest：{result.build_manifest_path}",
                    warning_line,
                ]
            )
        )
        self._tcga_status_label.setText("TCGA 表达矩阵已构建，等待统一数据检查与准备。")

    def fetch_tcga_clinical_metadata(self) -> TCGAClinicalBuildResult | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        project = get_tcga_project(self._selected_tcga_project_id() or "TCGA-THCA")
        expression_manifest = latest_tcga_expression_build_manifest_path(self._project_root, project_id=project.project_id)
        if expression_manifest is not None:
            self._tcga_clinical_build_status_text.setPlainText("正在从 GDC /cases 获取 TCGA clinical metadata，并与 B6.4 表达样本映射。")
            self._tcga_status_label.setText("正在获取 TCGA clinical metadata，请稍候。")
            QApplication.processEvents()
            try:
                result = self._tcga_clinical_builder.build_for_latest_expression_build(self._project_root, project_id=project.project_id)
            except Exception as exc:
                self._tcga_clinical_build_status_text.setPlainText(f"TCGA clinical metadata 构建失败：{exc}")
                self._set_status(f"TCGA clinical metadata 构建失败：{exc}", error=True)
                return None
        else:
            self._tcga_clinical_build_status_text.setPlainText("未找到 B6.4 build；将仅按项目获取 TCGA clinical 概况，不能做表达-临床映射。")
            self._tcga_status_label.setText("正在获取项目 clinical 概况，请稍候。")
            QApplication.processEvents()
            try:
                result = self._tcga_clinical_builder.build_for_project(self._project_root, project.project_id)
            except Exception as exc:
                self._tcga_clinical_build_status_text.setPlainText(f"TCGA clinical metadata 预览失败：{exc}")
                self._set_status(f"TCGA clinical metadata 预览失败：{exc}", error=True)
                return None
        self._tcga_clinical_build_result = result
        self._render_tcga_clinical_build_result(result)
        self._refresh_registered_sources()
        self._refresh_geo_download_list()
        self._refresh_tcga_clinical_build_state()
        self._refresh_tcga_workflow_state()
        self._set_status("TCGA clinical metadata 已获取；仅进入 clinical/survival preflight readiness，不自动执行 survival、DEG 或 GSEA。")
        return result

    def _render_tcga_clinical_build_result(self, result: TCGAClinicalBuildResult) -> None:
        mode_text = "表达数据匹配" if result.mode == "expression_matched_cases" else "项目 clinical 概况预览"
        warning_line = f"警告：{len(result.warnings)} 条" if result.warnings else "警告：无"
        self._tcga_clinical_build_status_text.setPlainText(
            "\n".join(
                [
                    f"构建状态：{result.message}",
                    f"模式：{mode_text}",
                    f"case：{result.case_count}；匹配 case：{result.matched_case_count}；匹配 sample：{result.matched_sample_count}",
                    f"基础 OS 可用 case：{result.survival_case_count}；死亡事件：{result.death_event_count}",
                    f"case table：{result.case_table_path}",
                    f"mapping table：{result.mapping_table_path}",
                    f"clinical manifest：{result.clinical_manifest_path}",
                    f"receipt：{result.clinical_receipt_path}",
                    warning_line,
                    "当前不会执行 KM/Cox/log-rank，也不会生成 clinical 结论。",
                ]
            )
        )
        self._tcga_status_label.setText("TCGA clinical metadata 已获取，等待数据检查与准备。")

    def _refresh_tcga_download_plan_state(self) -> None:
        if not hasattr(self, "_tcga_download_button"):
            return
        plan_path = latest_tcga_download_plan_path(self._project_root, project_id=self._selected_tcga_project_id()) if self._project_root is not None else None
        self._tcga_download_button.setEnabled(plan_path is not None)
        if hasattr(self, "_tcga_download_status_text") and self._tcga_download_result is None:
            self._tcga_download_status_text.setPlainText(
                f"可执行下载计划：{plan_path.name}" if plan_path is not None else "尚未生成下载计划草案。"
            )

    def _refresh_tcga_expression_build_state(self) -> None:
        if not hasattr(self, "_tcga_expression_build_button"):
            return
        record_path = latest_tcga_raw_expression_record_path(self._project_root, project_id=self._selected_tcga_project_id()) if self._project_root is not None else None
        self._tcga_expression_build_button.setEnabled(record_path is not None)
        if hasattr(self, "_tcga_expression_build_status_text") and self._tcga_expression_build_result is None:
            self._tcga_expression_build_status_text.setPlainText(
                f"可构建表达矩阵：{record_path.name}" if record_path is not None else "尚未获取 TCGA 原始表达文件。"
            )

    def _refresh_tcga_clinical_build_state(self) -> None:
        if not hasattr(self, "_tcga_clinical_build_button"):
            return
        state = self._build_tcga_workflow_state()
        self._tcga_workflow_state = state
        clinical_step = state.step("clinical")
        has_project = self._project_root is not None
        self._tcga_clinical_build_button.setEnabled(has_project and clinical_step.enabled)
        if hasattr(self, "_tcga_clinical_build_status_text") and self._tcga_clinical_build_result is None:
            if not has_project:
                self._tcga_clinical_build_status_text.setPlainText("请先创建或打开项目。")
                return
            if clinical_step.enabled:
                self._tcga_clinical_build_status_text.setPlainText(clinical_step.summary)
            else:
                detail = f"\n阻断原因：{clinical_step.blocking_reason}" if clinical_step.blocking_reason else ""
                self._tcga_clinical_build_status_text.setPlainText(f"{clinical_step.summary}{detail}")

    def _build_tcga_workflow_state(self) -> TCGAWorkflowState:
        project_id = self._selected_tcga_project_id()
        analysis_purpose = str(self._tcga_purpose_combo.currentData() or "") if hasattr(self, "_tcga_purpose_combo") else ""
        sample_scope = str(self._tcga_sample_scope_combo.currentData() or "") if hasattr(self, "_tcga_sample_scope_combo") else ""
        return build_tcga_workflow_state(
            self._project_root,
            project_id=project_id,
            analysis_purpose=analysis_purpose,
            sample_scope=sample_scope,
        )

    def _selected_tcga_project_id(self) -> str:
        return str(self._tcga_project_combo.currentData() or "TCGA-THCA") if hasattr(self, "_tcga_project_combo") else ""

    def _refresh_tcga_workflow_state(self) -> None:
        if not hasattr(self, "_tcga_workflow_table"):
            return
        state = self._build_tcga_workflow_state()
        self._tcga_workflow_state = state
        _fill_table(
            self._tcga_workflow_table,
            [
                [
                    step.title,
                    _tcga_workflow_status_zh(step.status),
                    _tcga_workflow_user_summary(step),
                    step.action_label if step.enabled and step.action_label else step.blocking_reason or "-",
                ]
                for step in state.steps
            ],
        )
        warning_text = "；".join(state.warnings[:3]) if state.warnings else "无阻断性提示。"
        self._tcga_workflow_summary_text.setPlainText(
            "\n".join(
                [
                    f"当前阶段：{_tcga_workflow_stage_zh(state.current_stage)}",
                    f"下一步：{state.next_action or '暂无可执行主步骤'}",
                    "可进入数据检查与准备：" + ("是" if state.can_enter_data_check else "否"),
                    f"提示：{warning_text}",
                ]
            )
        )
        if hasattr(self, "_tcga_preview_button"):
            self._tcga_preview_button.setEnabled(state.step("preview").enabled)
        if hasattr(self, "_tcga_download_button"):
            self._tcga_download_button.setEnabled(state.step("download").enabled)
        if hasattr(self, "_tcga_expression_build_button"):
            self._tcga_expression_build_button.setEnabled(state.step("expression_build").enabled)
        if hasattr(self, "_tcga_clinical_build_button"):
            self._tcga_clinical_build_button.setEnabled(state.step("clinical").enabled)
        if hasattr(self, "_tcga_data_check_button"):
            self._tcga_data_check_button.setEnabled(state.can_enter_data_check)
            self._tcga_data_check_button.setVisible(state.can_enter_data_check)
            self._tcga_data_check_button.setText("进入数据检查与准备" if state.can_enter_data_check else "进入准备")
        if hasattr(self, "_tcga_developer_details"):
            workflow_payload = _json(
                {
                    "tcga_workflow_state": state.to_dict(),
                    "note": "GDC filters, file UUIDs, manifest/source paths and raw paths are intentionally kept in developer diagnostics.",
                }
            )
            self._tcga_developer_details.setPlainText(workflow_payload)

    def create_gtex_download_plan_draft(self) -> AcquisitionSummary | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        summary = self._gtex_preview_summary
        if summary is None:
            self._set_status("请先点击“预览 GTEx 可下载数据”。", error=True)
            return None
        if not summary.is_download_plan_available:
            self._set_status("当前 GTEx 预览没有可用下载计划。", error=True)
            return None
        draft = write_gtex_download_plan_draft(self._project_root, summary)
        self._gtex_download_plan_draft = draft
        tissue = get_gtex_tissue(summary.request.tissue_id)
        purpose = get_gtex_use_purpose(summary.request.use_purpose)
        warnings = tuple(dict.fromkeys((*summary.warnings, "GTEx 下载计划草案不写 source_files，不进入 DEG/GSEA ready。")))
        request_draft = create_data_source_request(
            self._project_root,
            source_type="GTEx",
            user_title=f"GTEx 数据库 - {tissue.chinese_name}",
            user_selection_summary=f"{tissue.tissue_group} / {tissue.chinese_name} / {purpose.chinese_name}",
            internal_selection={"tissue_id": tissue.tissue_id, "tissue_site_detail": tissue.tissue_site_detail, "use_purpose": purpose.purpose_id, "download_plan_draft_path": str(draft.plan_path), "not_tcga_auto_control": True},
            expected_assets=purpose.required_internal_assets,
            warnings=warnings,
            status="download_plan_draft",
        )
        acquisition = register_acquisition(
            self._project_root,
            source_type="gtex_tissue",
            source_label=tissue.tissue_id,
            strategy="plan_only",
            selected_paths=[],
            metadata={
                "source": "gtex",
                "ui_source": "gtex_database_page",
                "registration_status": "registered_as_planned_source",
                "download_status": "gtex_download_plan_draft_created",
                "ready_for_recognition": "pending_download",
                "data_source_request_id": request_draft.request.request_id,
                "data_source_request_path": str(request_draft.request_path),
                "download_plan_draft_id": draft.plan_id,
                "download_plan_draft_path": str(draft.plan_path),
                "tissue_id": tissue.tissue_id,
                "tissue_site_detail": tissue.tissue_site_detail,
                "use_purpose": purpose.purpose_id,
                "display_title_zh": f"GTEx {tissue.chinese_name}",
                "gtex_preview_summary": summary.to_dict(),
                "tcga_merge_status": "not_merged",
                "tcga_default_control_status": "disabled",
                "requires_explicit_joint_config": True,
                "warnings": list(warnings),
            },
        )
        self._latest_summary = acquisition
        self._refresh_gtex_workflow_state()
        self._refresh_registered_sources()
        self._refresh_geo_download_list()
        self._set_status("GTEx 下载计划草案已生成；不会作为 TCGA normal control。")
        return acquisition

    def download_gtex_raw_files(self) -> GTExDownloadExecutionResult | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        selected_tissue_id = str(self._gtex_tissue_combo.currentData() or "") if hasattr(self, "_gtex_tissue_combo") else ""
        plan_path = latest_gtex_download_plan_path(self._project_root, tissue_id=selected_tissue_id or None)
        if plan_path is None:
            self._gtex_status_text.setPlainText("未找到 GTEx 下载计划草案，请先生成 G6.1 下载计划。")
            self._set_status("未找到 GTEx 下载计划草案。", error=True)
            return None
        self._gtex_status_text.setPlainText("正在下载 GTEx 原始文件；已存在文件会计为缓存命中。")
        QApplication.processEvents()
        try:
            result = self._gtex_download_executor.execute_plan(self._project_root, plan_path=plan_path)
        except Exception as exc:
            self._gtex_status_text.setPlainText(f"GTEx 下载执行失败：{exc}")
            self._set_status(f"GTEx 下载执行失败：{exc}", error=True)
            return None
        self._gtex_download_result = result
        self._gtex_status_text.setPlainText(f"{result.message}\n成功：{result.success_count}；缓存：{result.cache_hit_count}；失败：{result.failed_count}\n本地缓存路径：{result.target_dir}\nreceipt：{result.receipt_path}")
        self._refresh_gtex_workflow_state()
        self._refresh_registered_sources()
        self._refresh_geo_download_list()
        self._set_status("GTEx 原始文件已获取，等待构建表达矩阵；不会自动与 TCGA 合并。")
        return result

    def build_gtex_expression_matrix(self) -> GTExExpressionBuildResult | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        selected_tissue_id = str(self._gtex_tissue_combo.currentData() or "") if hasattr(self, "_gtex_tissue_combo") else ""
        record_path = latest_gtex_raw_expression_record_path(self._project_root, tissue_id=selected_tissue_id or None)
        if record_path is None:
            self._gtex_status_text.setPlainText("未找到等待 G6.3 构建的 GTEx 原始文件记录。")
            self._set_status("未找到等待 G6.3 构建的 GTEx 原始文件记录。", error=True)
            return None
        self._gtex_status_text.setPlainText("正在解析 GTEx 表达矩阵并构建本地标准产物。")
        QApplication.processEvents()
        try:
            result = self._gtex_expression_builder.build_from_record(self._project_root, record_path=record_path)
        except Exception as exc:
            self._gtex_status_text.setPlainText(f"GTEx 表达矩阵构建失败：{exc}")
            self._set_status(f"GTEx 表达矩阵构建失败：{exc}", error=True)
            return None
        self._gtex_expression_build_result = result
        self._gtex_status_text.setPlainText(f"{result.message}\nsample：{result.sample_count}；donor：{result.donor_count}；gene：{result.gene_count}\nexpression matrix：{result.expression_matrix_path}\nbuild manifest：{result.build_manifest_path}\nGTEx 不自动作为 TCGA normal control。")
        self._refresh_gtex_workflow_state()
        self._refresh_registered_sources()
        self._refresh_geo_download_list()
        self._set_status("GTEx 表达矩阵已构建，等待数据检查与准备；不自动与 TCGA 合并。")
        return result

    def _build_gtex_workflow_state(self) -> GTExWorkflowState:
        tissue_id = str(self._gtex_tissue_combo.currentData() or "") if hasattr(self, "_gtex_tissue_combo") else ""
        use_purpose = str(self._gtex_purpose_combo.currentData() or "") if hasattr(self, "_gtex_purpose_combo") else ""
        return build_gtex_workflow_state(self._project_root, tissue_id=tissue_id, use_purpose=use_purpose)

    def _refresh_gtex_workflow_state(self) -> None:
        if not hasattr(self, "_gtex_workflow_table"):
            return
        state = self._build_gtex_workflow_state()
        self._gtex_workflow_state = state
        _fill_table(
            self._gtex_workflow_table,
            [[step.title, _tcga_workflow_status_zh(step.status), _tcga_workflow_user_summary(step), step.action_label if step.enabled and step.action_label else step.blocking_reason or "-"] for step in state.steps],
        )
        self._gtex_workflow_summary_text.setPlainText(
            "\n".join(
                [
                    f"当前阶段：{_gtex_workflow_stage_zh(state.current_stage)}",
                    f"下一步：{state.next_action or '暂无可执行主步骤'}",
                    "可进入数据检查与准备：" + ("是" if state.can_enter_data_check else "否"),
                    "提示：" + ("；".join(state.warnings[:3]) if state.warnings else "无"),
                ]
            )
        )
        self._gtex_preview_button.setEnabled(state.step("preview").enabled)
        self._gtex_download_button.setEnabled(state.step("download").enabled)
        self._gtex_expression_build_button.setEnabled(state.step("expression_build").enabled)
        self._gtex_data_check_button.setEnabled(state.can_enter_data_check)
        self._gtex_data_check_button.setVisible(state.can_enter_data_check)
        self._gtex_data_check_button.setText("进入数据检查与准备" if state.can_enter_data_check else "进入准备")
        if self._gtex_preview_summary is not None:
            self._gtex_plan_button.setEnabled(self._gtex_preview_summary.is_download_plan_available)
        else:
            self._gtex_plan_button.setEnabled(False)
        self._gtex_developer_details.setPlainText(_json({"gtex_workflow_state": state.to_dict()}))

    def create_gtex_source_request(self) -> AcquisitionSummary | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        tissue = get_gtex_tissue(str(self._gtex_tissue_combo.currentData() or ""))
        purpose = get_gtex_use_purpose(str(self._gtex_purpose_combo.currentData() or ""))
        warnings = (
            "真实 GTEx 查询与下载将在下一阶段接入；本阶段不伪造 sample/donor/file 数。",
            "GTEx request 不会被自动作为 TCGA normal control，也不进入 DEG/GSEA ready。",
        )
        draft = create_data_source_request(
            self._project_root,
            source_type="GTEx",
            user_title=f"GTEx 数据库 - {tissue.chinese_name}",
            user_selection_summary=f"{tissue.tissue_group} / {tissue.chinese_name} / {purpose.chinese_name}",
            internal_selection={
                "tissue_id": tissue.tissue_id,
                "tissue_site_detail": tissue.tissue_site_detail,
                "use_purpose": purpose.purpose_id,
                "version": tissue.version,
                "readiness_profile": purpose.readiness_profile,
                "not_tcga_auto_control": True,
            },
            expected_assets=purpose.required_internal_assets,
            warnings=warnings,
            status="pending_download",
        )
        summary = register_acquisition(
            self._project_root,
            source_type="gtex_tissue",
            source_label=tissue.tissue_site_detail,
            strategy="plan_only",
            selected_paths=[],
            metadata={
                "source": "gtex",
                "ui_source": "gtex_database_page",
                "registration_status": "registered_as_planned_source",
                "download_status": "registered_pending_gtex_build",
                "ready_for_recognition": "pending_download",
                "data_source_request_id": draft.request.request_id,
                "data_source_request_path": str(draft.request_path),
                "tissue_id": tissue.tissue_id,
                "tissue_name": tissue.tissue_site_detail,
                "tissue_site_detail": tissue.tissue_site_detail,
                "chinese_name": tissue.chinese_name,
                "tissue_group": tissue.tissue_group,
                "version": tissue.version,
                "use_purpose": purpose.purpose_id,
                "use_purpose_zh": purpose.chinese_name,
                "expected_assets": list(purpose.required_internal_assets),
                "display_title_zh": f"GTEx {tissue.chinese_name}",
                "not_tcga_auto_control": True,
                "warnings": list(warnings),
            },
        )
        self._latest_summary = summary
        self._gtex_status_label.setText(f"已生成 GTEx 任务草案：{tissue.chinese_name}；等待下一阶段真实 GTEx 查询与下载。")
        self._refresh_registered_sources()
        self._set_status("GTEx 数据源 request 草案已生成；不会执行虚假下载，也不会作为 TCGA 自动对照。")
        return summary

    def _data_selection_status_card(self) -> QFrame:
        card, layout = _card("当前数据选择状态")
        card.setObjectName("dataSelectionStatusSummaryCard")
        self._selection_saved_count_label = _status_label("已保存数据来源：0 个")
        self._selection_saved_count_label.setObjectName("dataSelectionSavedCount")
        self._selection_download_count_label = _status_label("下载列表 / 待处理：0 个")
        self._selection_download_count_label.setObjectName("dataSelectionDownloadCount")
        self._selection_ready_count_label = _status_label("可进入数据检查：0 个")
        self._selection_ready_count_label.setObjectName("dataSelectionReadyCount")
        self._selection_next_step_label = _muted("下一步：先导入本地数据，或检索 GSE / 中文研究主题。")
        self._selection_next_step_label.setObjectName("dataSelectionNextStep")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(SPACING["md"])
        grid.setVerticalSpacing(SPACING["xs"])
        grid.addWidget(self._selection_saved_count_label, 0, 0)
        grid.addWidget(self._selection_download_count_label, 0, 1)
        grid.addWidget(self._selection_ready_count_label, 0, 2)
        layout.addLayout(grid)
        layout.addWidget(self._selection_next_step_label)
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
            source_files=summary.source_files,
            copied_files=summary.copied_files,
            referenced_paths=summary.referenced_paths,
            warnings=tuple(summary.warnings),
        )
        self._source_summaries[key] = selected_summary
        self._update_source_summary_label(key, selected_summary)
        self._set_status("先添加数据，下一步进入数据检查与准备。")
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
            [[preview.gse_id, preview.title, preview.platform, preview.sample_count, preview.status]],
        )
        self._gse_search_details.setPlainText(
            _json(
                {
                    "GSE 编号": preview.gse_id,
                    "数据集标题": preview.title,
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
            self._set_status(f"已在下载列表 / 待处理数据来源中：{candidate.accession_or_project}")
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
        self._set_status(f"{candidate.accession_or_project} 已添加到下载列表 / 待处理数据来源。")
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
            self._set_status(f"已从下载列表 / 待处理数据来源中移除：{accession}")
        else:
            self._set_status(f"下载列表 / 待处理数据来源中未找到：{accession}", error=True)

    def _generate_gse_geo_summary(self, candidate: UnifiedDatasetCandidate) -> dict[str, object] | None:
        cached = self._geo_brief_cache.get(candidate.accession_or_project)
        if cached is not None:
            self._gse_geo_detail_panel.render_summary(candidate, cached)
            self._set_status("已显示中文简介。")
            return cached
        self._gse_geo_detail_panel.set_busy_text("正在生成中文翻译与提炼，请稍候。")
        QApplication.processEvents()
        metadata = candidate.source_specific_metadata
        text_input = GeoStudyTextInput(
            accession=candidate.accession_or_project,
            title_en=str(metadata.get("title_en") or candidate.display_title),
            summary_en=str(metadata.get("summary_en") or ""),
            overall_design_en=str(metadata.get("overall_design_en") or ""),
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
        entries = _current_project_dataset_entries(self._project_root)
        count = len(entries)
        ready_count = _ready_registered_source_count(self._project_root)
        pending_count = _pending_dataset_entry_count(entries)
        self._registered_count_label.setText(f"已保存数据来源：{count} 个；待处理：{pending_count} 个；可识别：{ready_count} 个")
        self._next_button.setEnabled(ready_count > 0 and self._project_root is not None)
        self._chinese_search_status_label.setText(_chinese_search_entry_status(rows))
        self._refresh_data_selection_status(entries, ready_count, pending_count)

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

    def _refresh_data_selection_status(self, entries: list[DatasetListEntry], ready_count: int, pending_count: int) -> None:
        count = len(entries)
        self._selection_saved_count_label.setText(f"已保存数据来源：{count} 个")
        self._selection_download_count_label.setText(f"下载列表 / 待处理：{pending_count} 个")
        self._selection_ready_count_label.setText(f"可进入数据检查：{ready_count} 个")
        message = _data_selection_next_step_text(self._project_root, count=count, ready_count=ready_count, pending_count=pending_count)
        self._selection_next_step_label.setText(message)
        if self._project_root is not None and self._status_label.property("status") != "error":
            self._status_label.setText(message)
            self._status_label.setProperty("status", "ok")
            _refresh_style(self._status_label)

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
        self._candidate_ignore_buttons: dict[tuple[str, str], QPushButton] = {}
        self._ignored_candidates: set[tuple[str, str]] = set()
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
        root.addWidget(_header("中文研究主题检索", "生成 GEO / TCGA / GTEx 数据检索草稿，用户确认后再进入候选数据选择。", back_text="返回数据来源", back_signal=self.back_requested))
        self._project_label = _status_label("请先创建或打开生信分析项目。")
        root.addWidget(self._project_label)
        input_card, input_layout = _card("中文研究主题输入")
        input_layout.addWidget(_muted("用于生成 GEO / TCGA / GTEx 数据检索草稿，确认草稿后再选择候选数据来源。"))
        self._query_input = QLineEdit()
        self._query_input.setPlaceholderText("例如：甲状腺癌 脂质代谢 免疫浸润")
        self._query_input.setMinimumHeight(44)
        input_layout.addWidget(self._query_input)
        action_row = QHBoxLayout()
        action_row.addWidget(_button("生成草稿", "primaryButton", self.generate_terms))
        action_row.addStretch(1)
        input_layout.addLayout(action_row)
        self._status_label = _status_label("未生成 query draft")
        input_layout.addWidget(self._status_label)
        self._topic_summary_label = _status_label("主题识别：尚未开始。")
        input_layout.addWidget(self._topic_summary_label)
        root.addWidget(input_card)

        draft_card, draft_layout = _card("Query draft（草稿 / 待确认）")
        draft_card.setObjectName("chineseQueryDraftOverviewCard")
        self._draft_overview_status = _status_label("草稿状态：尚未生成")
        self._draft_overview_geo = _muted("GEO：尚未生成草稿")
        self._draft_overview_tcga = _muted("TCGA：尚未生成草稿")
        self._draft_overview_gtex = _muted("GTEx：尚未生成草稿")
        draft_layout.addWidget(self._draft_overview_status)
        draft_layout.addWidget(self._draft_overview_geo)
        draft_layout.addWidget(self._draft_overview_tcga)
        draft_layout.addWidget(self._draft_overview_gtex)
        draft_actions = QHBoxLayout()
        draft_actions.addWidget(_button("展开分区草稿", "secondaryButton", self._toggle_full_drafts))
        draft_actions.addWidget(_button("确认草稿", "secondaryButton", lambda: self.confirm_query_draft()))
        draft_actions.addStretch(1)
        draft_layout.addLayout(draft_actions)
        root.addWidget(draft_card)

        status_card, status_layout = _card("检索状态")
        status_card.setObjectName("chineseSearchStatusSummaryCard")
        self._chinese_draft_status_label = _status_label("Query draft：未生成")
        self._chinese_partition_status_label = _status_label("分区候选：GEO 0 个，TCGA 0 个，GTEx 0 个")
        self._chinese_saved_count_label = _status_label("已保存候选：0 个")
        self._chinese_download_count_label = _status_label("加入下载列表：0 个")
        self._chinese_next_step_label = _muted("下一步：先输入中文研究主题并生成草稿。")
        status_grid = QGridLayout()
        status_grid.setContentsMargins(0, 0, 0, 0)
        status_grid.setHorizontalSpacing(SPACING["md"])
        status_grid.setVerticalSpacing(SPACING["xs"])
        status_grid.addWidget(self._chinese_draft_status_label, 0, 0)
        status_grid.addWidget(self._chinese_partition_status_label, 0, 1)
        status_grid.addWidget(self._chinese_saved_count_label, 1, 0)
        status_grid.addWidget(self._chinese_download_count_label, 1, 1)
        status_layout.addLayout(status_grid)
        status_layout.addWidget(self._chinese_next_step_label)
        root.addWidget(status_card)

        result_card, result_layout = _card("数据库分区结果")
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

        log_card, log_layout = _card("开发者诊断")
        self._mapping_log = _text_preview(180)
        self._mapping_log.setObjectName("chineseMappingLog")
        self._mapping_log.setVisible(False)
        log_layout.addWidget(_button("展开开发者诊断", "secondaryButton", lambda: _toggle_details(self._mapping_log)), alignment=Qt.AlignLeft)
        log_layout.addWidget(self._mapping_log)
        root.addWidget(log_card)

        bottom_frame = QFrame()
        bottom_frame.setObjectName("chineseDatasetSearchBottomActionBar")
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        self._registered_count_label = _status_label("已选 GEO 0 个，TCGA 0 个，GTEx 0 个；0 个可进入识别。")
        self._continue_button = _button("下一步：数据检查与准备", "primaryButton", self.continue_to_recognition)
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
        detail_text.setPlainText("点击候选结果的“查看详情”查看标题、摘要、匹配原因、资产状态和下载建议。")
        detail_layout.addWidget(detail_title)
        detail_layout.addWidget(detail_text)
        detail_actions = QHBoxLayout()
        select_button = _button("保存", "secondaryButton", self._select_current_candidate)
        download_button = _button("加入下载列表", "secondaryButton", self._download_current_candidate)
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
            self._geo_dataset_detail_panel.add_to_download_list_requested.connect(lambda candidate: self.generate_candidate_download_task(candidate.source, candidate.accession_or_project))
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
        self._candidate_ignore_buttons.clear()
        self._candidate_status_labels.clear()
        self._render_candidate_tables(result, searched=searched)
        self._refresh_candidate_registration_buttons()
        self._mapping_log.setPlainText(_mapping_log_text(result))
        self._refresh_query_draft_overview(result)
        self._refresh_chinese_search_status_summary()

    def _render_candidate_tables(self, result: BioinformaticsSearchCenterResult, *, searched: bool) -> None:
        grouped: dict[str, list[UnifiedDatasetCandidate]] = {"geo": [], "tcga_gdc": [], "gtex": []}
        for candidate in result.candidates:
            if candidate.source in grouped and (candidate.source, candidate.accession_or_project) not in self._ignored_candidates:
                grouped[candidate.source].append(candidate)
        self._fill_geo_candidates(grouped["geo"], result.source_results.get("geo"), searched=searched)
        self._fill_tcga_candidates(grouped["tcga_gdc"])
        self._fill_gtex_candidates(grouped["gtex"])
        self._refresh_chinese_search_status_summary()

    def _refresh_query_draft_overview(self, result: BioinformaticsSearchCenterResult) -> None:
        query = result.query
        self._draft_overview_status.setText("草稿状态：已生成，待用户确认")
        self._draft_overview_geo.setText("GEO：" + ("；".join(query.geo_query_candidates) if query.geo_query_candidates else "未生成草稿"))
        self._draft_overview_tcga.setText("TCGA：" + (", ".join(query.tcga_project_ids) if query.tcga_project_ids else "未生成草稿"))
        self._draft_overview_gtex.setText("GTEx：" + (", ".join(query.gtex_tissues) if query.gtex_tissues else "未生成草稿"))
        self._chinese_draft_status_label.setText("Query draft：已生成，待确认")

    def _refresh_chinese_search_status_summary(self) -> None:
        visible_candidates = [
            candidate
            for key, candidate in self._candidates.items()
            if key not in self._ignored_candidates
        ]
        candidate_counts = {
            "geo": sum(1 for candidate in visible_candidates if candidate.source == "geo"),
            "tcga_gdc": sum(1 for candidate in visible_candidates if candidate.source == "tcga_gdc"),
            "gtex": sum(1 for candidate in visible_candidates if candidate.source == "gtex"),
        }
        rows = self._registered_chinese_rows()
        ready_count = _ready_chinese_source_count(self._project_root)
        download_list_count = _download_list_row_count(self._project_root, rows)
        self._chinese_partition_status_label.setText(
            f"分区候选：GEO {candidate_counts['geo']} 个，TCGA {candidate_counts['tcga_gdc']} 个，GTEx {candidate_counts['gtex']} 个"
        )
        self._chinese_saved_count_label.setText(f"已保存候选：{len(rows)} 个")
        self._chinese_download_count_label.setText(f"加入下载列表：{download_list_count} 个")
        if self._last_result is None:
            self._chinese_next_step_label.setText("下一步：先输入中文研究主题并生成草稿。")
        elif not rows:
            self._chinese_next_step_label.setText("下一步：查看候选详情，保存或加入下载列表。")
        elif ready_count:
            self._chinese_next_step_label.setText("下一步：可以进入数据检查与准备；仍可继续补充候选数据来源。")
        else:
            self._chinese_next_step_label.setText("下一步：完成下载或确认数据来源后进入数据检查与准备。")

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
        _set_table_widths(self._geo_table, [300, 92, 300, 70, 160, 72, 150])

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
        for key in [key for key in self._candidate_ignore_buttons if key[0] == source_key]:
            self._candidate_ignore_buttons.pop(key, None)
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
        register_button = QPushButton("保存")
        register_button.setObjectName(f"registerCandidateButton_{candidate.source}_{candidate.accession_or_project}")
        register_button.clicked.connect(lambda checked=False, s=candidate.source, a=candidate.accession_or_project: self.register_candidate(s, a))
        detail_button = QPushButton("查看详情")
        detail_button.setObjectName(f"candidateDetailButton_{candidate.source}_{candidate.accession_or_project}")
        detail_button.clicked.connect(lambda checked=False, item=candidate: self._show_candidate_detail(item))
        ignore_button = QPushButton("忽略")
        ignore_button.setObjectName(f"ignoreCandidateButton_{candidate.source}_{candidate.accession_or_project}")
        ignore_button.clicked.connect(lambda checked=False, s=candidate.source, a=candidate.accession_or_project: self.ignore_candidate(s, a))
        download_button = QPushButton("加入下载列表")
        download_button.setObjectName(f"candidateDownloadButton_{candidate.source}_{candidate.accession_or_project}")
        download_button.clicked.connect(lambda checked=False, s=candidate.source, a=candidate.accession_or_project: self.generate_candidate_download_task(s, a))
        actions.addWidget(register_button)
        actions.addWidget(detail_button)
        actions.addWidget(ignore_button)
        actions.addWidget(download_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        key = (candidate.source, candidate.accession_or_project)
        self._candidate_register_buttons[key] = register_button
        self._candidate_download_buttons[key] = download_button
        self._candidate_ignore_buttons[key] = ignore_button
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
        prefix = f"已选 GEO {source_counts['geo']} 个，TCGA {source_counts['tcga_gdc']} 个，GTEx {source_counts['gtex']} 个；{ready_count} 个可进入数据检查。"
        if ready_count:
            self._registered_count_label.setText(f"{prefix} 当前状态：可进入数据检查。")
        elif total_count:
            self._registered_count_label.setText(f"{prefix} 当前建议操作：先补全表达矩阵。")
        else:
            self._registered_count_label.setText(f"{prefix} 当前建议操作：先选择数据源。")
        can_continue = ready_count > 0 and self._project_root is not None
        self._continue_button.setEnabled(can_continue)
        self._continue_button.setText("下一步：数据检查与准备")
        self._refresh_geo_download_list()
        self._refresh_chinese_search_status_summary()

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
        table.setColumnWidth(action_col, 300)
        for row_index, candidate in enumerate(candidates):
            key = (candidate.source, candidate.accession_or_project)
            action_widget = QWidget()
            layout = QHBoxLayout(action_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            detail_button = QPushButton("查看详情")
            detail_button.setObjectName(f"candidateDetailButton_{candidate.source}_{candidate.accession_or_project}")
            detail_button.clicked.connect(lambda checked=False, item=candidate: self._show_candidate_detail(item))
            layout.addWidget(detail_button)
            register_button = QPushButton("保存")
            register_button.setObjectName(f"registerCandidateButton_{candidate.source}_{candidate.accession_or_project}")
            register_button.clicked.connect(lambda checked=False, s=candidate.source, a=candidate.accession_or_project: self.register_candidate(s, a))
            ignore_button = QPushButton("忽略")
            ignore_button.setObjectName(f"ignoreCandidateButton_{candidate.source}_{candidate.accession_or_project}")
            ignore_button.clicked.connect(lambda checked=False, s=candidate.source, a=candidate.accession_or_project: self.ignore_candidate(s, a))
            download_button = QPushButton("加入下载列表")
            download_button.setObjectName(f"candidateDownloadButton_{candidate.source}_{candidate.accession_or_project}")
            download_button.clicked.connect(lambda checked=False, s=candidate.source, a=candidate.accession_or_project: self.generate_candidate_download_task(s, a))
            layout.addWidget(register_button)
            layout.addWidget(ignore_button)
            layout.addWidget(download_button)
            layout.addStretch(1)
            table.setCellWidget(row_index, action_col, action_widget)
            self._candidate_register_buttons[key] = register_button
            self._candidate_ignore_buttons[key] = ignore_button
            self._candidate_download_buttons[key] = download_button
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
        self._detail_download_button.setText("加入下载列表")
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
        self.ignore_candidate(candidate.source, candidate.accession_or_project)

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

    def ignore_candidate(self, source: str, accession_or_project: str) -> bool:
        key = (source, accession_or_project)
        candidate = self._candidates.get(key)
        if candidate is None:
            self._set_status("候选结果不存在。", error=True)
            return False
        self._ignored_candidates.add(key)
        if self._selected_candidate is not None and (self._selected_candidate.source, self._selected_candidate.accession_or_project) == key:
            self._selected_candidate = None
        if source == "geo":
            self._geo_dataset_detail_panel.setVisible(False)
        else:
            bucket = _candidate_source_bucket(source)
            self._source_detail_titles[bucket].setText("候选详情")
            self._source_detail_texts[bucket].setPlainText("已忽略该候选；不会删除真实数据，也不会写入项目数据来源。")
            self._source_detail_select_buttons[bucket].setEnabled(False)
            self._source_detail_download_buttons[bucket].setEnabled(False)
        if self._last_result is not None:
            self._render_candidate_tables(self._last_result, searched=self._last_render_searched)
        self._set_status(f"已忽略：{accession_or_project}。仅从当前候选展示中移除。")
        return True

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
                button.setText("已保存")
            else:
                button.setText("保存")
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
                    button.setText("补充文件已下载" if "补充文件已下载" in status_text else ("元数据已下载" if ready else "加入下载列表"))
                    button.setEnabled(not ready)
            else:
                manifest_created = _candidate_has_download_manifest(self._project_root, source, accession)
                if manifest_created:
                    button.setText("下载清单已创建")
                    button.setEnabled(False)
                else:
                    button.setText("加入下载列表")
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
            if str(metadata.get("analysis_gate_status") or "") == "waiting_b6_4_expression_matrix_build":
                state = "planned"
            elif metadata.get("ready_for_recognition") == "ready" or payload.get("strategy") != "plan_only":
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
        actions.addWidget(_button("继续：数据检查与准备", "primaryButton", self.continue_to_recognition))
        actions.addStretch(1)
        root.addLayout(actions)


class BioinformaticsRecognitionWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()

    def __init__(self, *, on_continue: Callable[[Path], None] | None = None, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self._last_report: dict[str, object] | None = None
        self._pre_recognition_rows: list[RegisteredSourceRow] = []
        self._pre_recognition_checks: dict[str, QCheckBox] = {}
        self.setObjectName("bioinformaticsRecognitionPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_report()

    def run_recognition(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。")
            return None
        selected_rows = self._selected_pre_recognition_rows()
        if not selected_rows:
            self._set_status("请先选择需要识别的数据。")
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
        self._set_status(f"{self.status_message()} 本次只识别已勾选的数据。")
        return report

    def refresh_report(self) -> None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。")
            return
        self._render_pre_recognition_inputs()
        report = load_recognition_report(self._project_root)
        if report is None:
            self._set_status("尚未生成数据识别报告。")
            self._table.setRowCount(0)
            self._counts.setPlainText("")
            self._group_preview.setPlainText("")
            self._technical_details.setPlainText("")
            return
        self._render_report(report)
        self._set_status(f"{self.status_message()} 刷新报告只重新读取当前识别报告显示，不重新扫描文件，也不改变项目文件。")

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
        self._technical_details.setPlainText("")
        self._set_status("旧识别结果已清理；原始数据文件未删除。请点击“重新识别”重新扫描。")
        return True

    def status_message(self) -> str:
        return self._status_label.text()

    def continue_to_readiness(self) -> None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。")
            return
        ok, reason = _can_continue_from_recognition(self._project_root)
        if not ok:
            self._set_status(f"不能继续：{reason} 请返回数据来源补充文件。")
            return
        self._set_status("可以继续进入数据准备与标准化；需在标准化阶段确认分组后才能进行 DEG 分析。")
        self.continue_requested.emit(self._project_root)

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("数据识别", "Developer Preview / 本地测试版", back_text="返回数据导入与检索", back_signal=self.back_requested))
        pre_card, pre_layout = _card("待识别数据源")
        self._pre_recognition_empty_label = _muted("尚未选择数据。")
        pre_layout.addWidget(self._pre_recognition_empty_label)
        self._pre_recognition_table = _table(["选择", "来源类型", "名称 / 编号", "当前位置", "数据状态"])
        self._pre_recognition_table.setObjectName("preRecognitionInputList")
        self._pre_recognition_table.setMinimumHeight(130)
        self._pre_recognition_table.horizontalHeader().sectionClicked.connect(self._toggle_pre_recognition_header)
        pre_layout.addWidget(self._pre_recognition_table)
        pre_actions = QHBoxLayout()
        self._delete_selected_inputs_button = _button("删除所选", "secondaryButton", self._delete_selected_pre_recognition_sources)
        self._delete_selected_inputs_button.setEnabled(False)
        pre_actions.addStretch(1)
        pre_actions.addWidget(self._delete_selected_inputs_button)
        pre_layout.addLayout(pre_actions)
        root.addWidget(pre_card)
        actions = QHBoxLayout()
        actions.addWidget(_button("开始识别", "primaryButton", self.run_recognition))
        actions.addWidget(_button("刷新", "secondaryButton", self.refresh_report))
        actions.addStretch(1)
        root.addLayout(actions)
        root.addWidget(_muted("开始识别只处理上方勾选的数据；刷新只更新当前报告显示。"))
        self._status_label = _status_label("尚未生成数据识别报告。")
        root.addWidget(self._status_label)
        filter_row = QHBoxLayout()
        filter_row.addWidget(_muted("文件显示："))
        self._duplicate_filter = QComboBox()
        self._duplicate_filter.addItems(["显示全部文件", "仅显示当前有效数据来源", "隐藏疑似重复文件"])
        self._duplicate_filter.currentIndexChanged.connect(self._rerender_last_report)
        filter_row.addWidget(self._duplicate_filter)
        filter_row.addStretch(1)
        root.addLayout(filter_row)
        self._table = _table(["文件名", "当前位置", "识别类型", "识别可信度", "文件大小", "标准化状态 / 识别理由", "warning"])
        self._table.setObjectName("recognitionResultTable")
        confidence_header = self._table.horizontalHeaderItem(3)
        if confidence_header is not None:
            confidence_header.setToolTip("软件根据文件内容推断文件类型的可信程度。它不是数据质量评分，也不是科研可信度评分。")
        root.addWidget(self._table)
        self._counts = _read_only_report_view(130)
        self._counts.setObjectName("recognitionSummaryReport")
        root.addWidget(self._counts)
        group_card, group_layout = _card("样本与分组预览")
        group_card.setObjectName("recognitionGroupPreviewCard")
        self._group_preview = _read_only_report_view(130)
        self._group_preview.setObjectName("recognitionGroupPreviewReport")
        group_layout.addWidget(self._group_preview)
        root.addWidget(group_card)
        self._technical_details = _text_preview(180)
        self._technical_details.setVisible(False)
        root.addWidget(_button("技术详情", "secondaryButton", lambda: _toggle_details(self._technical_details)), alignment=Qt.AlignLeft)
        root.addWidget(self._technical_details)
        tech_ops = QFrame()
        tech_ops.setObjectName("recognitionTechnicalOperations")
        tech_ops.setVisible(False)
        tech_layout = QHBoxLayout(tech_ops)
        tech_layout.setContentsMargins(0, 0, 0, 0)
        tech_layout.addWidget(_button("清理旧识别结果", "secondaryButton", self.clean_old_recognition_results))
        tech_layout.addWidget(_button("打开 recognized_data 文件夹", "secondaryButton", lambda: _open_path(self._project_root / "recognized_data" if self._project_root else None)))
        tech_layout.addStretch(1)
        root.addWidget(_button("技术操作", "secondaryButton", lambda: tech_ops.setVisible(not tech_ops.isVisible())), alignment=Qt.AlignLeft)
        root.addWidget(tech_ops)
        root.addWidget(_button("继续：数据准备与标准化", "primaryButton", self.continue_to_readiness), alignment=Qt.AlignLeft)

    def _render_report(self, report: dict[str, object]) -> None:
        self._last_report = report
        self._render_pre_recognition_inputs()
        annotated = _annotated_recognition_files(report, self._project_root)
        files = _filter_recognition_files(annotated, self._duplicate_filter.currentText())
        warnings = [str(item) for item in report.get("warnings", []) or []]
        duplicate_count = sum(1 for item in annotated if item.get("_duplicate"))
        self._set_status(f"已读取识别报告：{len(annotated)} 个文件，{len(warnings)} 条 warning。")
        self._fill_recognition_table(files)
        self._counts.setPlainText(_recognition_user_summary(report, annotated, warnings, self._project_root))
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
        _set_table_widths(self._pre_recognition_table, [56, 140, 190, 260, 210])
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
            rows.append(
                [
                    str(item.get("file_name", "")),
                    _compact_path(str(item.get("route_path") or item.get("original_path") or ""), max_chars=54),
                    _recognition_type_text(item),
                    _format_confidence(item.get("confidence")),
                    _format_file_size(item.get("file_size")),
                    _recognition_status_reason(item),
                    warning,
                ]
            )
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                table_item = QTableWidgetItem(value)
                source = files[row_index]
                if col_index == 1:
                    table_item.setToolTip(str(source.get("route_path") or source.get("original_path") or ""))
                elif col_index == 2:
                    table_item.setToolTip(_recognition_roles_tooltip(source))
                elif col_index == 3:
                    table_item.setToolTip("软件根据文件内容推断文件类型的可信程度。它不是数据质量评分，也不是科研可信度评分。")
                elif col_index == 4:
                    table_item.setToolTip(f"原始 bytes：{source.get('file_size', '未记录')}")
                elif col_index == 5:
                    table_item.setToolTip(str(source.get("next_action") or source.get("reason") or ""))
                self._table.setItem(row_index, col_index, table_item)
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


class GseaGeneSetResourceManagerDialog(QDialog):
    selection_changed = Signal()

    def __init__(self, project_root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root = Path(project_root).expanduser().resolve()
        self._resources: list[dict[str, Any]] = []
        self._downloadable_resources: list[dict[str, Any]] = []
        self.setObjectName("gseaGeneSetResourceManagerDialog")
        self.setWindowTitle("GSEA 基因集资源管理器")
        self.resize(980, 620)
        self._build_ui()
        self.refresh_resources()

    def refresh_resources(self) -> dict[str, object]:
        validation = validate_gene_set_registry(self._project_root)
        self._resources = [dict(item) for item in validation.get("resources", []) if isinstance(item, dict)]
        self._downloadable_resources = list_downloadable_gene_set_resources(self._project_root)
        self._render_resources()
        self._render_downloadable_resources()
        if self._resources:
            self._status_label.setText(f"本地 GSEA 基因集资源：{len(self._resources)} 个。")
        else:
            self._status_label.setText("暂无本地 GSEA 基因集资源。你可以导入本地 GMT，或在后续阶段配置 / 下载常用基因集资源。")
        return validation

    def import_local_gmt(self, path: str | Path | None = None, metadata: dict[str, object] | None = None) -> dict[str, object] | None:
        source_path: str | Path | None = path
        metadata_payload = dict(metadata or {})
        if source_path is None:
            selected, _ = QFileDialog.getOpenFileName(self, "导入本地 GMT", "", "GMT files (*.gmt);;Text files (*.txt *.gmt);;All files (*)")
            if not selected:
                return None
            source_path = selected
        if not metadata_payload:
            metadata_payload = self._prompt_import_metadata(Path(source_path))
            if metadata_payload is None:
                return None
        result = import_gmt_file(self._project_root, source_path, metadata_payload)
        resource = result.get("resource") if isinstance(result.get("resource"), dict) else {}
        self.refresh_resources()
        self.selection_changed.emit()
        self._status_label.setText(f"已导入 GMT：{resource.get('name') or Path(source_path).name}；状态：{resource.get('status') or 'unknown'}。")
        return result

    def select_current_resource(self) -> dict[str, object] | None:
        resource = self._current_resource()
        if resource is None:
            self._status_label.setText("请先在本地资源表中选择一条资源。")
            return None
        try:
            selected = select_gene_set(self._project_root, str(resource.get("resource_id") or ""))
        except ValueError as exc:
            self._status_label.setText(str(exc))
            return None
        self.refresh_resources()
        self.selection_changed.emit()
        self._status_label.setText(f"已选择 GSEA 基因集：{selected.get('name') or selected.get('resource_id')}。")
        return selected

    def remove_current_resource(self) -> dict[str, object] | None:
        resource = self._current_resource()
        if resource is None:
            self._status_label.setText("请先在本地资源表中选择一条资源。")
            return None
        removed = remove_gene_set(self._project_root, str(resource.get("resource_id") or ""))
        self.refresh_resources()
        self.selection_changed.emit()
        self._status_label.setText(f"已移除 GSEA 基因集资源：{resource.get('name') or resource.get('resource_id')}。")
        return removed

    def show_current_resource_detail(self) -> dict[str, object] | None:
        resource = self._current_resource()
        if resource is None:
            self._status_label.setText("请先在本地资源表中选择一条资源。")
            return None
        detail = get_gene_set(self._project_root, str(resource.get("resource_id") or "")) or resource
        self._details.setPlainText(_json(detail))
        return detail

    def download_selected_common_resource(self) -> dict[str, object] | None:
        resource = self._current_downloadable_resource()
        if resource is None:
            self._status_label.setText("请先在常用资源表中选择一条可下载资源。")
            return None
        if not resource.get("downloadable"):
            self._status_label.setText(str(resource.get("license_note") or "该资源本阶段不支持自动下载，请使用导入 GMT。"))
            if str(resource.get("resource_id") or "") in {"msigdb_hallmark_user_import", "custom_gmt_import"}:
                self.import_local_gmt()
            return None
        try:
            result = download_gene_set_resource(self._project_root, str(resource.get("resource_id") or ""))
        except Exception as exc:
            self._status_label.setText(f"下载失败：{exc}。如果已有本地缓存，可继续使用已缓存资源。")
            return None
        self.refresh_resources()
        self.selection_changed.emit()
        downloaded = result.get("resource") if isinstance(result.get("resource"), dict) else {}
        state = "已使用本地缓存" if result.get("cached") else "已下载并缓存"
        self._status_label.setText(f"{state}：{downloaded.get('name') or resource.get('name')}。")
        return result

    def refresh_selected_common_resource(self) -> dict[str, object] | None:
        resource = self._current_downloadable_resource()
        if resource is None:
            self._status_label.setText("请先在常用资源表中选择一条可更新资源。")
            return None
        if not resource.get("downloadable"):
            self._status_label.setText(str(resource.get("license_note") or "该资源本阶段不支持自动下载。"))
            return None
        try:
            result = refresh_downloaded_gene_set(self._project_root, str(resource.get("resource_id") or ""))
        except Exception as exc:
            self._status_label.setText(f"更新失败：{exc}。旧缓存和当前选择不会被破坏。")
            return None
        self.refresh_resources()
        self.selection_changed.emit()
        downloaded = result.get("resource") if isinstance(result.get("resource"), dict) else {}
        self._status_label.setText(f"已更新缓存：{downloaded.get('name') or resource.get('name')}。")
        return result

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        title = QLabel("GSEA 基因集资源管理器")
        title.setObjectName("pageTitle")
        subtitle = _muted("管理本地 GMT 资源；本阶段不内置、不静默下载 gene set。")
        root.addWidget(title)
        root.addWidget(subtitle)
        local_card, local_layout = _card("已可用的本地资源")
        local_card.setObjectName("gseaGeneSetLocalResourcesCard")
        self._status_label = _muted("")
        self._status_label.setObjectName("gseaGeneSetManagerStatus")
        local_layout.addWidget(self._status_label)
        self._table = _table(["名称", "类型", "物种", "Gene ID 类型", "来源", "版本 / 日期", "状态", "Gene set 数量", "当前选择", "操作"])
        self._table.setObjectName("gseaGeneSetResourceTable")
        self._table.setMinimumHeight(240)
        local_layout.addWidget(self._table)
        actions = QHBoxLayout()
        self._select_button = _button("选择", "primaryButton", self.select_current_resource)
        self._select_button.setObjectName("selectGseaGeneSetResourceButton")
        self._detail_button = _button("查看详情", "secondaryButton", self.show_current_resource_detail)
        self._detail_button.setObjectName("viewGseaGeneSetResourceButton")
        self._remove_button = _button("移除", "secondaryButton", self.remove_current_resource)
        self._remove_button.setObjectName("removeGseaGeneSetResourceButton")
        self._refresh_button = _button("刷新状态", "secondaryButton", self.refresh_resources)
        self._refresh_button.setObjectName("refreshGseaGeneSetResourcesButton")
        for button in (self._select_button, self._detail_button, self._remove_button, self._refresh_button):
            actions.addWidget(button)
        actions.addStretch(1)
        local_layout.addLayout(actions)
        root.addWidget(local_card)

        import_card, import_layout = _card("导入本地 GMT")
        import_card.setObjectName("gseaGeneSetImportCard")
        import_layout.addWidget(_muted("导入会复制 GMT 到项目本地 gene set repository，并写入 registry；不会修改原始文件。"))
        self._import_button = _button("导入本地 GMT", "primaryButton", self.import_local_gmt)
        self._import_button.setObjectName("importLocalGmtButton")
        import_layout.addWidget(self._import_button, alignment=Qt.AlignLeft)
        root.addWidget(import_card)

        download_card, download_layout = _card("下载 / 配置常用基因集资源")
        download_card.setObjectName("gseaGeneSetFutureSourcesCard")
        self._future_table = _table(["资源名称", "说明", "来源", "许可 / 使用提示", "本地状态", "本地版本 / 下载日期", "操作"])
        self._future_table.setObjectName("gseaGeneSetFutureResourcesTable")
        download_layout.addWidget(self._future_table)
        download_actions = QHBoxLayout()
        self._download_button = _button("下载到本地 / 在线获取并缓存", "primaryButton", self.download_selected_common_resource)
        self._download_button.setObjectName("downloadGeneSetResourceButton")
        self._refresh_download_button = _button("更新缓存", "secondaryButton", self.refresh_selected_common_resource)
        self._refresh_download_button.setObjectName("refreshDownloadedGeneSetResourceButton")
        self._import_hallmark_button = _button("导入 GMT", "secondaryButton", self.import_local_gmt)
        self._import_hallmark_button.setObjectName("importGeneSetFromFutureResourceButton")
        for button in (self._download_button, self._refresh_download_button, self._import_hallmark_button):
            download_actions.addWidget(button)
        download_actions.addStretch(1)
        download_layout.addLayout(download_actions)
        root.addWidget(download_card)

        self._details = _read_only_report_view(130)
        self._details.setObjectName("gseaGeneSetResourceDetails")
        root.addWidget(self._details)
        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_row.addWidget(_button("关闭", "secondaryButton", self.close))
        root.addLayout(close_row)

    def _render_resources(self) -> None:
        if not self._resources:
            _fill_table(
                self._table,
                [["暂无本地 GSEA 基因集资源。", "-", "-", "-", "-", "-", "empty", "0", "否", "导入本地 GMT"]],
            )
            return
        rows = []
        for resource in self._resources:
            rows.append(
                [
                    str(resource.get("name") or resource.get("resource_id") or ""),
                    str(resource.get("collection_type") or "Unknown"),
                    str(resource.get("species") or "unknown"),
                    str(resource.get("gene_id_type") or "unknown"),
                    str(resource.get("source_name") or resource.get("source_type") or ""),
                    str(resource.get("version") or resource.get("updated_at") or ""),
                    str(resource.get("status") or ""),
                    str(resource.get("gene_set_count") or 0),
                    "是" if resource.get("selected_for_gsea") else "否",
                    "选择 / 查看详情 / 移除 / 刷新状态",
                ]
            )
        _fill_table(self._table, rows)
        _set_table_widths(self._table, [150, 95, 80, 100, 130, 140, 90, 105, 90, 220])
        self._table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Stretch)

    def _render_downloadable_resources(self) -> None:
        rows = []
        for item in self._downloadable_resources:
            rows.append(
                [
                    str(item.get("name") or ""),
                    str(item.get("description") or ""),
                    str(item.get("source_name") or ""),
                    str(item.get("license_note") or ""),
                    str(item.get("local_status") or "未下载"),
                    str(item.get("local_version") or ""),
                    str(item.get("operation") or ""),
                ]
            )
        _fill_table(self._future_table, rows)
        _set_table_widths(self._future_table, [170, 220, 130, 330, 95, 140, 180])
        self._future_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

    def _current_resource(self) -> dict[str, Any] | None:
        if not self._resources:
            return None
        row = self._table.currentRow()
        if row < 0:
            row = 0
        if row >= len(self._resources):
            return None
        return self._resources[row]

    def _current_downloadable_resource(self) -> dict[str, Any] | None:
        if not self._downloadable_resources:
            return None
        row = self._future_table.currentRow()
        if row < 0:
            row = 0
        if row >= len(self._downloadable_resources):
            return None
        return self._downloadable_resources[row]

    def _prompt_import_metadata(self, path: Path) -> dict[str, object] | None:
        name, ok = QInputDialog.getText(self, "资源名称", "资源名称：", text=path.stem)
        if not ok:
            return None
        collection, ok = QInputDialog.getItem(self, "Collection type", "Collection type：", ["Custom", "GO_BP", "GO_CC", "GO_MF", "Reactome", "KEGG", "Hallmark", "Unknown"], 0, False)
        if not ok:
            return None
        species, ok = QInputDialog.getItem(self, "物种", "物种：", ["unknown", "human", "mouse", "other"], 0, False)
        if not ok:
            return None
        gene_id_type, ok = QInputDialog.getItem(self, "Gene ID 类型", "Gene ID 类型：", ["unknown", "symbol", "entrez", "ensembl"], 0, False)
        if not ok:
            return None
        source_name, _ = QInputDialog.getText(self, "来源备注", "来源备注（可选）：", text=path.name)
        license_note, _ = QInputDialog.getText(self, "License note", "License note（可选）：", text="")
        return {
            "name": name.strip() or path.stem,
            "collection_type": collection if collection in COLLECTION_TYPES else "Custom",
            "species": species if species in SPECIES_VALUES else "unknown",
            "gene_id_type": gene_id_type if gene_id_type in GENE_ID_TYPES else "unknown",
            "source_name": source_name.strip() or path.name,
            "license_note": license_note.strip(),
        }


class BioinformaticsReadinessDashboardWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()

    def __init__(self, *, on_continue: Callable[[Path], None] | None = None, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self._last_artifacts: dict[str, object] = {}
        self._gene_set_manager_dialog: GseaGeneSetResourceManagerDialog | None = None
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
        return self.save_and_rerun_readiness()

    def refresh_status(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        artifacts = load_readiness_artifacts(self._project_root)
        if artifacts.get("readiness_report") is None:
            self._last_artifacts = {}
            self._status_label.setText("暂不能继续：尚未运行数据检查。")
            self._recognized_inputs_label.setText("已识别到的数据：尚未检查")
            self._missing_inputs_label.setText("仍需补充的数据：尚未检查")
            self._next_step_label.setText("下一步建议：点击“运行数据检查”，逐文件刷新 recognition 和 ready check。")
            self._warning_chips.setText("提示：尚未运行数据检查。")
            self._render_todo_items(set())
            self._render_file_status_rows(_pending_data_check_file_statuses(self._project_root))
            self._render_dataset_readiness_summary({})
            self._render_group_recommendation({})
            self._render_gsea_gene_set_status({})
            self._update_run_check_button(False)
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
        if normalized not in {"sample_metadata", "clinical_metadata", "expression_matrix", "comparison_config"}:
            self._status_label.setText("当前缺失项暂不支持在本页补充。")
            return False
        if normalized in {"expression_matrix"} and mode == "manual":
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
        self._status_label.setText("已确认候选分组为正式比较组，并重新运行数据检查。")
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
        selected_paths = _pending_data_check_paths(self._project_root)
        if selected_paths:
            run_project_recognition_for_paths(self._project_root, selected_paths)
        else:
            run_project_recognition(self._project_root)
        artifacts = run_project_readiness(self._project_root)
        self._render(artifacts)
        self._status_label.setText(f"{self._status_label.text()}；已重新运行数据检查。")
        return artifacts

    def open_gene_set_resource_manager(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        dialog = GseaGeneSetResourceManagerDialog(self._project_root, self)
        dialog.selection_changed.connect(self._refresh_after_gene_set_resource_change)
        self._gene_set_manager_dialog = dialog
        dialog.show()
        dialog.raise_()
        validation = validate_gene_set_registry(self._project_root)
        resources = list_local_gene_sets(self._project_root)
        self._status_label.setText("已打开 GSEA 基因集资源管理器；可导入本地 GMT、选择本地资源或刷新状态。")
        return {"validation": validation, "resources": resources, "dialog": dialog}

    def _refresh_after_gene_set_resource_change(self) -> None:
        if self._project_root is None:
            return
        artifacts = run_project_readiness(self._project_root)
        self._render(artifacts)

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("数据检查与准备", "第一步检查每个文件；第二步继续标准化数据。", back_text="返回数据导入与检索", back_signal=self.back_requested))

        status_card, status_layout = _card("数据检查与准备概览")
        status_card.setObjectName("readinessStatusCard")
        self._status_label = _status_label("暂不能继续：尚未运行数据检查。")
        self._status_label.setObjectName("readinessStatusBadge")
        self._recognized_inputs_label = _muted("已识别到的数据：尚未检查")
        self._recognized_inputs_label.setObjectName("readinessRecognizedInputs")
        self._missing_inputs_label = _muted("仍需补充的数据：尚未检查")
        self._missing_inputs_label.setObjectName("readinessMissingInputs")
        self._next_step_label = _muted("下一步建议：点击“运行数据检查”，逐文件刷新 recognition 和 ready check。")
        self._next_step_label.setObjectName("readinessNextStep")
        self._warning_chips = _muted("提示：尚未运行数据检查。")
        self._warning_chips.setObjectName("readinessWarningChips")
        status_layout.addWidget(self._status_label)
        status_layout.addWidget(self._recognized_inputs_label)
        status_layout.addWidget(self._missing_inputs_label)
        status_layout.addWidget(self._next_step_label)
        status_layout.addWidget(self._warning_chips)
        root.addWidget(status_card)

        file_card, file_layout = _card("第一步：数据检查")
        file_card.setObjectName("dataCheckFileStatusCard")
        self._file_status_hint = _muted("每个待处理文件都会独立检查；灰色为未检查，绿色为通过，黄色为需确认，红色为不可作为标准化输入。")
        self._file_status_hint.setWordWrap(True)
        file_layout.addWidget(self._file_status_hint)
        self._file_status_table = _table(["文件名", "类型 / 后缀", "来源", "检查状态", "预计用途 / 待识别", "可用内容", "缺失 / 风险", "操作"])
        self._file_status_table.setObjectName("dataCheckFileStatusTable")
        self._file_status_table.setMinimumHeight(220)
        file_layout.addWidget(self._file_status_table)
        root.addWidget(file_card)

        dataset_card, dataset_layout = _card("数据集级 readiness 汇总")
        dataset_card.setObjectName("datasetReadinessSummaryCard")
        self._dataset_readiness_table = _table(["检查项", "状态", "说明"])
        self._dataset_readiness_table.setObjectName("datasetReadinessSummaryTable")
        self._dataset_readiness_table.setMinimumHeight(210)
        dataset_layout.addWidget(self._dataset_readiness_table)
        root.addWidget(dataset_card)

        group_card, group_layout = _card("推荐分组")
        group_card.setObjectName("recommendedGroupCard")
        self._group_recommendation = _read_only_report_view(150)
        self._group_recommendation.setObjectName("recommendedGroupPreview")
        group_layout.addWidget(self._group_recommendation)
        group_actions = QHBoxLayout()
        self._group_confirm_button = _button("确认推荐分组", "secondaryButton", self.confirm_group_preview_as_comparison)
        self._group_modify_button = _button("修改分组", "secondaryButton", lambda: self.supplement_missing_info("comparison_config", mode="manual"))
        self._group_reject_button = _button("拒绝推荐分组", "secondaryButton", lambda: self._defer_optional_analysis("comparison_config"))
        self._group_later_button = _button("稍后处理", "secondaryButton", lambda: self._defer_optional_analysis("comparison_config"))
        for button in (self._group_confirm_button, self._group_modify_button, self._group_reject_button, self._group_later_button):
            group_actions.addWidget(button)
        group_actions.addStretch(1)
        group_layout.addLayout(group_actions)
        root.addWidget(group_card)

        gsea_card, gsea_layout = _card("GSEA 基因集选择")
        gsea_card.setObjectName("gseaGeneSetStatusCard")
        self._gsea_status_label = _status_label("GSEA 基因集：未选择")
        self._gsea_status_label.setObjectName("gseaGeneSetStatus")
        self._gsea_status_help = _muted("GSEA 基因集用于后续 GSEA 分析，不属于当前 GEO / TCGA / GTEx 数据文件本身。未选择基因集不影响当前数据检查、标准化准备或 DEG preflight。")
        self._gsea_status_help.setWordWrap(True)
        gsea_layout.addWidget(self._gsea_status_label)
        gsea_layout.addWidget(self._gsea_status_help)
        gsea_layout.addWidget(_button("选择 GSEA 基因集", "secondaryButton", self.open_gene_set_resource_manager), alignment=Qt.AlignLeft)
        root.addWidget(gsea_card)

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
        todo_items = [
            ("expression_matrix", "表达矩阵", "用途：后续标准化、差异表达、富集和相关性分析的核心输入。", "当前状态：未提供。", [self._expression_file_button]),
            ("sample_metadata", "样本信息", "用途：识别样本分组、组织来源和实验条件。", "当前状态：未提供。", [self._sample_file_button, self._sample_manual_button, self._sample_template_button]),
            ("clinical_metadata", "临床信息", "用途：用于生存分析和临床变量关联。", "当前状态：未提供。", [self._clinical_file_button, self._clinical_defer_button]),
            ("comparison_config", "比较分组", "用途：用于差异表达分析，例如 control vs treatment。", "当前状态：未设置。", [self._comparison_preview_button, self._comparison_manual_button, self._comparison_file_button, self._comparison_template_button]),
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
        self._run_check_button = _button("运行数据检查", "primaryButton", self.save_and_rerun_readiness)
        bottom_actions.addWidget(self._run_check_button)
        bottom_actions.addWidget(_button("继续：标准化数据", "primaryButton", self.continue_to_standardization))
        bottom_actions.addStretch(1)
        root.addLayout(bottom_actions)

    def _render(self, artifacts: dict[str, object]) -> None:
        self._last_artifacts = artifacts
        readiness = artifacts.get("readiness_report") or {}
        matrix = artifacts.get("capability_matrix") or {}
        readiness_payload = readiness if isinstance(readiness, dict) else {}
        matrix_payload = matrix if isinstance(matrix, dict) else {}
        group_preview = _project_group_preview(self._project_root)
        missing = _missing_readiness_inputs(readiness_payload, matrix_payload)
        self._status_label.setText(_readiness_overall_summary(readiness_payload, matrix_payload, missing))
        self._recognized_inputs_label.setText(_readiness_recognized_inputs_text(readiness_payload))
        self._missing_inputs_label.setText(_readiness_missing_inputs_text(missing, group_preview))
        self._next_step_label.setText(_readiness_next_step_text(readiness_payload, matrix_payload, missing, group_preview))
        self._warning_chips.setText(_readiness_default_warning_summary(readiness_payload, matrix_payload, missing))
        self._render_todo_items(missing, group_preview)
        self._render_file_status_rows(readiness_payload.get("file_statuses", []) if isinstance(readiness_payload.get("file_statuses"), list) else [])
        self._render_dataset_readiness_summary(readiness_payload.get("dataset_readiness", {}) if isinstance(readiness_payload.get("dataset_readiness"), dict) else {})
        self._render_group_recommendation(group_preview)
        self._render_gsea_gene_set_status(readiness_payload.get("gsea_gene_set_status", {}) if isinstance(readiness_payload.get("gsea_gene_set_status"), dict) else {})
        self._update_run_check_button(True)
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

    def _render_file_status_rows(self, file_statuses: list[object]) -> None:
        rows = []
        for item in file_statuses:
            if not isinstance(item, dict):
                continue
            rows.append(
                [
                    str(item.get("file_name") or ""),
                    f"{item.get('recognized_type_zh') or item.get('recognized_type') or '待识别'} / {item.get('file_suffix') or '无后缀'}",
                    str(item.get("source") or ""),
                    _data_check_status_badge(item),
                    str(item.get("suggested_use") or ""),
                    str(item.get("available_content") or ""),
                    "；".join(part for part in [str(item.get("missing_content") or ""), str(item.get("risk_notes") or "")] if part and part != "无"),
                    _data_check_file_action(item),
                ]
            )
        _fill_table(self._file_status_table, rows)
        _set_table_widths(self._file_status_table, [190, 180, 100, 150, 260, 220, 280, 150])
        self._file_status_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

    def _render_dataset_readiness_summary(self, summary: dict[str, object]) -> None:
        rows = _dataset_readiness_user_rows(summary)
        _fill_table(self._dataset_readiness_table, rows)
        _set_table_widths(self._dataset_readiness_table, [220, 120, 430])
        self._dataset_readiness_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def _render_group_recommendation(self, preview: dict[str, object]) -> None:
        self._group_recommendation.setPlainText(_group_recommendation_detail_text(preview))
        has_candidate = _group_preview_has_candidate(preview)
        for button in (self._group_confirm_button, self._group_modify_button, self._group_reject_button, self._group_later_button):
            button.setEnabled(has_candidate or button is self._group_modify_button)

    def _render_gsea_gene_set_status(self, status: dict[str, object]) -> None:
        self._gsea_status_label.setText(str(status.get("label") or "GSEA 基因集：未选择"))
        self._gsea_status_help.setText(
            str(status.get("message") or "GSEA 基因集用于后续 GSEA 分析，不属于当前 GEO / TCGA / GTEx 数据文件本身。未选择基因集不影响当前数据检查、标准化准备或 DEG preflight。")
        )

    def _update_run_check_button(self, has_existing_result: bool) -> None:
        self._run_check_button.setText("重新运行数据检查" if has_existing_result else "运行数据检查")
        has_pending = bool(_pending_data_check_file_statuses(self._project_root))
        self._run_check_button.setEnabled(self._project_root is not None and (has_pending or has_existing_result))

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

    def __init__(self, *, on_continue: Callable[[Path], None] | None = None, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self._last_candidates: dict[str, object] = {}
        self._last_confirmation: dict[str, object] = {}
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
        self.refresh_confirmation_candidates()
        artifacts = generate_standardized_assets(self._project_root)
        self._render(artifacts)
        return artifacts

    def refresh_assets(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        artifacts = load_standardization_artifacts(self._project_root)
        if artifacts.get("registry") is None:
            self._status_label.setText("尚未生成标准化数据。")
            self._assets.setRowCount(0)
            self._render_user_state(artifacts)
        else:
            self._render(artifacts)

    def continue_to_workflow(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        ok, reason = _can_continue_from_standardization(self._project_root)
        if not ok:
            self._status_label.setText(f"不能继续：{reason} 请按页面提示补齐数据、标准化数据或分组设计。")
            return
        self.continue_requested.emit(self._project_root)

    def continue_to_group_design(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        self._status_label.setText("请在数据准备状态页确认分组与比较设计。")
        self.back_requested.emit()

    def status_message(self) -> str:
        return self._status_label.text()

    def refresh_confirmation_candidates(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        artifacts = load_standardization_confirmation_artifacts(self._project_root)
        self._last_candidates = artifacts.get("candidates") if isinstance(artifacts.get("candidates"), dict) else {}
        self._last_confirmation = artifacts.get("confirmation") if isinstance(artifacts.get("confirmation"), dict) else {}
        self._render_confirmation_state()
        return artifacts

    def confirm_expression_candidate(
        self,
        candidate_id: str | None = None,
        *,
        value_type: str | None = None,
        value_type_confirmed: bool = True,
    ) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        candidates = collect_standardization_candidates(self._project_root)
        expression = _standardization_candidate_list(candidates, "expression_matrix_candidates")
        selected_id = candidate_id or (str(expression[0].get("candidate_id") or "") if expression else "")
        if not selected_id:
            self._status_label.setText("没有可确认的表达矩阵候选。")
            return None
        selected = _standardization_find_candidate(candidates, selected_id) or {}
        selected_value_type = value_type or str(selected.get("expression_value_type_candidate") or "unknown")
        manifest = save_standardization_confirmation(
            self._project_root,
            selected_expression_candidate_id=selected_id,
            expression_value_type=selected_value_type,
            expression_value_type_confirmed=value_type_confirmed,
        )
        self._last_confirmation = manifest
        self._last_candidates = candidates
        self._render_confirmation_state()
        self._status_label.setText("已保存表达矩阵候选确认。当前不会运行真实差异分析。")
        return manifest

    def confirm_species_candidate(self, species: str | None = None, *, manual: bool = False) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        candidates = collect_standardization_candidates(self._project_root)
        species_candidates = _standardization_candidate_list(candidates, "species_candidates")
        selected_species = species or (str(species_candidates[0].get("species") or "") if species_candidates else "")
        if not selected_species:
            self._status_label.setText("没有物种证据，请手动输入后再确认。")
            return None
        manifest = save_standardization_confirmation(
            self._project_root,
            species=selected_species,
            species_confirmed=True,
            species_manual_confirmed=manual,
        )
        self._last_confirmation = manifest
        self._last_candidates = candidates
        self._render_confirmation_state()
        self._status_label.setText("已保存物种确认。")
        return manifest

    def confirm_gene_id_type(self, gene_id_type: str | None = None) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        candidates = collect_standardization_candidates(self._project_root)
        gene_candidates = _standardization_candidate_list(candidates, "gene_id_candidates")
        selected_type = gene_id_type or (str(gene_candidates[0].get("gene_id_type") or "") if gene_candidates else "unknown")
        manifest = save_standardization_confirmation(
            self._project_root,
            gene_id_type=selected_type,
            gene_id_type_confirmed=True,
        )
        self._last_confirmation = manifest
        self._last_candidates = candidates
        self._render_confirmation_state()
        self._status_label.setText("已保存 gene ID 类型确认；Probe ID 仍需平台注释或映射确认。")
        return manifest

    def confirm_group_candidate(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        manifest = confirm_group_design_from_preview(self._project_root)
        self._last_confirmation = manifest
        self._last_candidates = collect_standardization_candidates(self._project_root)
        self._render_confirmation_state()
        self._status_label.setText("已保存候选分组确认，可用于 DEG preflight；当前不会运行真实差异分析。")
        return manifest

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("数据标准化", "确认识别后的表达矩阵、样本信息和分组设计，生成后续分析可用的数据。", back_text="返回数据准备状态", back_signal=self.back_requested))
        actions = QHBoxLayout()
        actions.addWidget(_button("生成标准化数据", "primaryButton", self.generate_assets))
        actions.addWidget(_button("确认分组与比较设计", "secondaryButton", self.continue_to_group_design))
        actions.addWidget(_button("刷新状态", "secondaryButton", self.refresh_assets))
        actions.addStretch(1)
        root.addLayout(actions)
        self._status_label = _status_label("尚未生成标准化数据。")
        root.addWidget(self._status_label)

        input_card, input_layout = _card("当前输入数据")
        self._input_source_label = _muted("数据来源：待识别。")
        self._input_source_label.setObjectName("standardizationInputSource")
        self._input_status_label = _muted("识别状态：尚未读取。")
        self._input_status_label.setObjectName("standardizationInputStatus")
        self._input_summary_label = _muted("内容摘要：待生成识别报告。")
        self._input_summary_label.setObjectName("standardizationInputSummary")
        input_layout.addWidget(self._input_source_label)
        input_layout.addWidget(self._input_status_label)
        input_layout.addWidget(self._input_summary_label)
        root.addWidget(input_card)

        readiness_card, readiness_layout = _card("分析输入状态")
        self._expression_status_label = _muted("表达矩阵：待确认。")
        self._expression_status_label.setObjectName("standardizationExpressionStatus")
        self._sample_status_label = _muted("样本信息：待确认。")
        self._sample_status_label.setObjectName("standardizationSampleStatus")
        self._group_status_label = _muted("分组与比较设计：待确认。")
        self._group_status_label.setObjectName("standardizationGroupStatus")
        readiness_layout.addWidget(self._expression_status_label)
        readiness_layout.addWidget(self._sample_status_label)
        readiness_layout.addWidget(self._group_status_label)
        root.addWidget(readiness_card)

        confirmation_card, confirmation_layout = _card("标准化确认候选")
        self._confirmation_summary_label = _muted("识别阶段已发现候选表达矩阵，请在标准化阶段确认后再用于分析。")
        self._confirmation_summary_label.setObjectName("standardizationConfirmationSummary")
        confirmation_layout.addWidget(self._confirmation_summary_label)
        confirmation_actions = QHBoxLayout()
        confirmation_actions.addWidget(_button("刷新候选", "secondaryButton", self.refresh_confirmation_candidates))
        confirmation_actions.addWidget(_button("确认表达矩阵候选", "secondaryButton", lambda: self.confirm_expression_candidate()))
        confirmation_actions.addWidget(_button("确认物种候选", "secondaryButton", lambda: self.confirm_species_candidate()))
        confirmation_actions.addWidget(_button("确认 gene ID 类型", "secondaryButton", lambda: self.confirm_gene_id_type()))
        confirmation_actions.addWidget(_button("确认候选分组", "secondaryButton", lambda: self.confirm_group_candidate()))
        confirmation_actions.addStretch(1)
        confirmation_layout.addLayout(confirmation_actions)
        self._confirmation_candidates = _table(["候选类型", "来源文件", "来源 parser", "确认状态", "说明"])
        self._confirmation_candidates.setObjectName("standardizationConfirmationCandidateTable")
        confirmation_layout.addWidget(self._confirmation_candidates)
        _set_table_widths(self._confirmation_candidates, [150, 190, 150, 150, 380])
        self._confirmation_candidates.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        root.addWidget(confirmation_card)

        default_card, default_layout = _card("默认资产与下一步")
        self._default_asset_label = _muted("当前默认使用的数据：待生成标准化数据。")
        self._default_asset_label.setObjectName("standardizationDefaultAssets")
        self._next_step_label = _muted("下一步建议：先完成数据识别和准备状态检查。")
        self._next_step_label.setObjectName("standardizationNextStep")
        default_layout.addWidget(self._default_asset_label)
        default_layout.addWidget(self._next_step_label)
        root.addWidget(default_card)

        self._assets = _table(["数据内容", "当前状态", "用于后续分析", "说明"])
        self._assets.setObjectName("standardizationUserAssetTable")
        root.addWidget(self._assets)
        _set_table_widths(self._assets, [180, 170, 120, 320])
        self._assets.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        developer_card, developer_layout = _card("开发者诊断")
        developer_actions = QHBoxLayout()
        developer_actions.addWidget(_button("展开技术细节", "secondaryButton", lambda: _toggle_details(self._developer_details)))
        developer_actions.addWidget(_button("打开 standardized_data 文件夹", "secondaryButton", lambda: _open_path(self._project_root / "standardized_data" if self._project_root else None)))
        developer_actions.addStretch(1)
        developer_layout.addLayout(developer_actions)
        self._developer_details = _text_preview(150)
        self._developer_details.setObjectName("standardizationDeveloperDiagnostics")
        self._developer_details.setVisible(False)
        developer_layout.addWidget(self._developer_details)
        self._manifest = self._developer_details
        root.addWidget(developer_card)
        root.addWidget(_button("继续到分析任务中心", "primaryButton", self.continue_to_workflow), alignment=Qt.AlignLeft)

    def _render(self, artifacts: dict[str, object]) -> None:
        registry = artifacts.get("registry") or {}
        manifest = artifacts.get("analysis_ready_manifest") or {}
        assets = registry.get("assets", []) if isinstance(registry, dict) else []
        warnings = registry.get("warnings", []) if isinstance(registry, dict) else []
        self._status_label.setText(f"标准化数据：{len(assets)} 项；提示 {len(warnings)} 条。")
        _fill_table(
            self._assets,
            _standardization_user_asset_rows(assets if isinstance(assets, list) else []),
        )
        self._render_user_state(artifacts)

    def _render_user_state(self, artifacts: dict[str, object]) -> None:
        if self._project_root is None:
            return
        registry = artifacts.get("registry") if isinstance(artifacts.get("registry"), dict) else {}
        manifest = artifacts.get("analysis_ready_manifest") if isinstance(artifacts.get("analysis_ready_manifest"), dict) else {}
        repository_manifest = artifacts.get("repository_manifest") if isinstance(artifacts.get("repository_manifest"), dict) else {}
        validation_report = artifacts.get("validation_report") if isinstance(artifacts.get("validation_report"), dict) else {}
        assets = registry.get("assets", []) if isinstance(registry, dict) else []
        readiness = load_readiness_artifacts(self._project_root)
        readiness_report = readiness.get("readiness_report") if isinstance(readiness.get("readiness_report"), dict) else {}
        recognition = load_recognition_report(self._project_root) or {}
        confirmation_artifacts = load_standardization_confirmation_artifacts(self._project_root)
        self._last_candidates = confirmation_artifacts.get("candidates") if isinstance(confirmation_artifacts.get("candidates"), dict) else {}
        self._last_confirmation = confirmation_artifacts.get("confirmation") if isinstance(confirmation_artifacts.get("confirmation"), dict) else {}
        self._input_source_label.setText(_standardization_input_source_text(recognition if isinstance(recognition, dict) else {}))
        self._input_status_label.setText(_standardization_input_status_text(recognition if isinstance(recognition, dict) else {}))
        self._input_summary_label.setText(_standardization_input_summary_text(recognition if isinstance(recognition, dict) else {}))
        self._expression_status_label.setText(_standardization_expression_status_text(assets if isinstance(assets, list) else [], readiness_report if isinstance(readiness_report, dict) else {}))
        self._sample_status_label.setText(_standardization_sample_status_text(assets if isinstance(assets, list) else [], readiness_report if isinstance(readiness_report, dict) else {}))
        self._group_status_label.setText(_standardization_group_status_text(self._project_root, readiness_report if isinstance(readiness_report, dict) else {}))
        self._default_asset_label.setText(_standardization_default_assets_text(assets if isinstance(assets, list) else []))
        self._next_step_label.setText(_standardization_next_step_text(self._project_root, assets if isinstance(assets, list) else [], readiness_report if isinstance(readiness_report, dict) else {}))
        self._render_confirmation_state()
        self._developer_details.setPlainText(
            _json(
                {
                    "standardized_assets_registry": registry,
                    "analysis_ready_manifest": manifest,
                    "repository_manifest": repository_manifest,
                    "validation_report": validation_report,
                    "data_processing_task_plan": artifacts.get("data_processing_task_plan"),
                    "standardization_confirmation": self._last_confirmation,
                    "standardization_candidates": self._last_candidates,
                    "readiness_details": readiness,
                    "recognition_report": recognition,
                    "paths": {
                        "registry_path": artifacts.get("registry_path"),
                        "manifest_path": artifacts.get("manifest_path"),
                        "repository_manifest_path": artifacts.get("repository_manifest_path"),
                        "validation_report_path": artifacts.get("validation_report_path"),
                        "asset_lineage_path": artifacts.get("asset_lineage_path"),
                        "data_processing_task_plan_path": artifacts.get("data_processing_task_plan_path"),
                    },
                }
            )
        )

    def _render_confirmation_state(self) -> None:
        candidates = self._last_candidates if isinstance(self._last_candidates, dict) else {}
        confirmation = self._last_confirmation if isinstance(self._last_confirmation, dict) else {}
        rows = _standardization_confirmation_rows(candidates, confirmation)
        _fill_table(self._confirmation_candidates, rows)
        _set_table_widths(self._confirmation_candidates, [150, 190, 150, 150, 380])
        readiness = confirmation.get("readiness") if isinstance(confirmation.get("readiness"), dict) else {}
        expression_count = len(_standardization_candidate_list(candidates, "expression_matrix_candidates"))
        sample_count = len(_standardization_candidate_list(candidates, "sample_metadata_candidates"))
        group_count = len(_standardization_candidate_list(candidates, "group_candidates"))
        imported_count = len(_standardization_candidate_list(candidates, "imported_deg_candidates"))
        self._confirmation_summary_label.setText(
            "识别阶段已发现候选表达矩阵，请在标准化阶段确认后再用于分析。"
            f" 表达矩阵候选 {expression_count} 个，样本注释候选 {sample_count} 个，分组候选 {group_count} 个，导入 DEG 结果候选 {imported_count} 个。"
            f" DEG preflight ready：{'是' if readiness.get('deg_preflight_ready') else '否'}。当前不会运行真实差异分析。"
        )


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
    deg_config_requested = Signal(object)
    imported_deg_requested = Signal(object)
    immune_scoring_requested = Signal(object)

    def __init__(
        self,
        *,
        on_continue: Callable[[Path], None] | None = None,
        on_back: Callable[[], None] | None = None,
        on_configure_deg: Callable[[Path], None] | None = None,
        on_view_imported_deg: Callable[[Path], None] | None = None,
        on_configure_immune_scoring: Callable[[Path], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self.setObjectName("bioinformaticsAnalysisTaskCenterPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)
        if on_configure_deg is not None:
            self.deg_config_requested.connect(on_configure_deg)
        if on_view_imported_deg is not None:
            self.imported_deg_requested.connect(on_view_imported_deg)
        if on_configure_immune_scoring is not None:
            self.immune_scoring_requested.connect(on_configure_immune_scoring)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_task_center()

    def refresh_task_center(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
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
        self.refresh_task_center()
        self._status_label.setText(f"已创建配置草稿：{task.label}。当前仅保存任务记录，未执行真实分析。")
        return task

    def create_deg_task_draft(self) -> object | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        self.deg_config_requested.emit(self._project_root)
        self._status_label.setText("已打开差异分析配置页；当前只做配置和 preflight，不执行真实 DEG。")
        return {"next_page": "deg_config", "project_root": str(self._project_root)}

    def open_imported_deg_browser(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        self.imported_deg_requested.emit(self._project_root)
        self._status_label.setText("已打开导入结果浏览；该入口只查看用户导入 / 外部分析结果，不运行 DEG。")
        return {"next_page": "imported_deg", "project_root": str(self._project_root)}

    def open_immune_scoring(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        self.immune_scoring_requested.emit(self._project_root)
        self._status_label.setText("已打开免疫浸润 / TME评分页；该入口只生成探索性 bulk signature score。")
        return {"next_page": "immune_tme_scoring", "project_root": str(self._project_root)}

    def build_legacy_asset_candidates(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        result = write_legacy_standardized_asset_candidates(self._project_root)
        self.refresh_task_center()
        self._status_label.setText(
            f"已生成 legacy asset candidates：{result.get('candidate_count', 0)} 个；"
            "这是候选资产，不是 analysis input package 或 formal result。"
        )
        return result

    def materialize_legacy_asset_candidates(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        if not (self._project_root / "standardized_data/asset_candidates/legacy_acquisition_asset_candidates.json").is_file():
            self._status_label.setText("不能物化：尚未生成 legacy asset candidates。")
            return None
        result = materialize_legacy_standardized_asset_candidates(self._project_root)
        self.refresh_task_center()
        self._status_label.setText(
            f"已物化 legacy candidates：{result.get('materialized_asset_count', 0)} 个；"
            "仅写入隔离 repository 文件和 materialization manifest，不写 result index。"
        )
        return result

    def merge_legacy_assets_into_repository_manifest(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        if not (self._project_root / "standardized_data/asset_candidates/legacy_materialized_assets_manifest.json").is_file():
            self._status_label.setText("不能合并：尚未物化 legacy candidates。")
            return None
        result = merge_legacy_materialized_assets_into_repository_manifest(self._project_root)
        self.refresh_task_center()
        self._status_label.setText(
            f"已合并 legacy assets 到 standardized repository manifest：{result.get('merged_asset_count', 0)} 个；"
            "仍需 B8 resolver 和 downstream gates，未生成 formal analysis。"
        )
        return result

    def confirm_legacy_asset_selection(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        repository_manifest = _read_json_file(self._project_root / "standardized_data/repositories/repository_manifest.json")
        selection_ids, blockers = _legacy_default_selection_ids(repository_manifest)
        if blockers:
            self._status_label.setText(f"不能确认 legacy asset selection：{'；'.join(blockers)}")
            return {"status": "blocked", "blockers": blockers}
        selection = build_legacy_asset_selection_manifest(self._project_root, confirmed_by_user=True, **selection_ids)
        result = apply_legacy_asset_selection_to_repository_manifest(self._project_root, selection)
        self.refresh_task_center()
        validation = result.get("validation") if isinstance(result.get("validation"), dict) else {}
        downstream = validation.get("downstream_blockers") if isinstance(validation.get("downstream_blockers"), list) else []
        suffix = f"；downstream blockers：{'；'.join(str(item) for item in downstream)}" if downstream else ""
        self._status_label.setText(
            "已确认 legacy asset selection；仅更新 standardized repository default selection，"
            f"不写 analysis_input_repository/result_index{suffix}。"
        )
        return result

    def run_formal_controlled_deg_task(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        confirmation = load_deg_parameter_confirmation(self._project_root)
        parameter_manifest = confirmation.get("parameter_manifest") if isinstance(confirmation.get("parameter_manifest"), dict) else {}
        result = run_formal_controlled_deg(
            self._project_root,
            method=str(parameter_manifest.get("method") or "welch_t_test"),
            log2fc_threshold=float(parameter_manifest.get("log2fc_threshold") or 1.0),
            p_value_threshold=float(parameter_manifest.get("p_value_threshold") or 0.05),
            fdr_threshold=float(parameter_manifest.get("fdr_threshold") or 0.05),
            pseudocount=float(parameter_manifest.get("pseudocount") or 1e-9),
        )
        self.refresh_task_center()
        if result.get("status") == "passed":
            self._status_label.setText("已完成两组 controlled DEG MVP，并写入 result index v2。未生成 GSEA、plot、report-ready 或 survival 输出。")
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "formal DEG gate 未通过"
            self._status_label.setText(f"两组 controlled DEG 未运行：{blockers}")
        return result

    def confirm_r_limma_parameters(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        analysis_state = build_analysis_center_state(self._project_root)
        limma_gate = analysis_state.get("limma_rscript_gate") if isinstance(analysis_state.get("limma_rscript_gate"), dict) else {}
        try:
            confirmation = save_r_limma_parameter_confirmation(
                self._project_root,
                deg_ready_package=limma_gate.get("deg_ready_package", {}) if isinstance(limma_gate.get("deg_ready_package"), dict) else {},
                multi_factor_preflight=limma_gate.get("multi_factor_preflight", {}) if isinstance(limma_gate.get("multi_factor_preflight"), dict) else {},
                dependency_snapshot=limma_gate.get("dependency_snapshot", {}) if isinstance(limma_gate.get("dependency_snapshot"), dict) else {},
                log2fc_threshold=float(self._formal_deg_log2fc_input.text() or "1.0"),
                p_value_threshold=float(self._formal_deg_pvalue_input.text() or "0.05"),
                fdr_threshold=float(self._formal_deg_fdr_input.text() or "0.05"),
            )
        except ValueError:
            self._status_label.setText("limma Rscript 参数确认失败：threshold 必须是数字。")
            return None
        self.refresh_task_center()
        if confirmation.get("status") == "confirmed":
            plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
            self._status_label.setText(f"已确认 limma Rscript 参数；task-run id：{plan.get('task_run_id', '')}。仍只允许运行 limma DEG，不生成 plot/report-ready。")
        else:
            blockers = "；".join(str(item) for item in confirmation.get("blockers", []) or []) or "limma Rscript gate 未通过"
            self._status_label.setText(f"limma Rscript 参数未确认：{blockers}")
        return confirmation

    def prepare_r_limma_design_config(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        analysis_state = build_analysis_center_state(self._project_root)
        limma_gate = analysis_state.get("limma_rscript_gate") if isinstance(analysis_state.get("limma_rscript_gate"), dict) else {}
        deg_ready = limma_gate.get("deg_ready_package") if isinstance(limma_gate.get("deg_ready_package"), dict) else {}
        result = save_r_limma_design_config(self._project_root, deg_ready)
        self.refresh_task_center()
        if result.get("status") == "confirmed":
            contrast = result.get("contrast") if isinstance(result.get("contrast"), dict) else {}
            self._status_label.setText(
                f"已生成 limma design config：{contrast.get('case_level', 'case')} vs {contrast.get('control_level', 'control')}；"
                "仅写入 manifests/r_limma_design_config.json，未执行 limma。"
            )
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "limma design config gate 未通过"
            self._status_label.setText(f"limma design config 未生成 ready 状态：{blockers}")
        return result

    def run_r_limma_rscript_task(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        analysis_state = build_analysis_center_state(self._project_root)
        limma_gate = analysis_state.get("limma_rscript_gate") if isinstance(analysis_state.get("limma_rscript_gate"), dict) else {}
        confirmation = load_r_limma_parameter_confirmation(self._project_root)
        parameter_manifest = confirmation.get("parameter_manifest") if isinstance(confirmation.get("parameter_manifest"), dict) else {}
        output_plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
        result = run_r_limma_rscript_execution(
            self._project_root,
            expression_table_path=str(parameter_manifest.get("expression_table_path") or ""),
            sample_group_map=parameter_manifest.get("sample_group_map") if isinstance(parameter_manifest.get("sample_group_map"), dict) else {},
            case_group=str(parameter_manifest.get("case_group") or ""),
            control_group=str(parameter_manifest.get("control_group") or ""),
            multi_factor_preflight=limma_gate.get("multi_factor_preflight", {}) if isinstance(limma_gate.get("multi_factor_preflight"), dict) else {},
            parameters_manifest=parameter_manifest,
            external_capabilities=limma_gate.get("external_capabilities") if isinstance(limma_gate.get("external_capabilities"), dict) else None,
            dependency_snapshot=limma_gate.get("dependency_snapshot") if isinstance(limma_gate.get("dependency_snapshot"), dict) else None,
            result_id=str(output_plan.get("result_id") or ""),
            task_run_id=str(output_plan.get("task_run_id") or ""),
            input_package_id=str(parameter_manifest.get("input_package_id") or ""),
        )
        self.refresh_task_center()
        if result.get("status") == "passed":
            self._status_label.setText("已完成 limma Rscript DEG，并通过 B25 handoff 写入 result index v2。未生成 plot/report-ready/GSEA/survival。")
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "limma Rscript gate 未通过"
            self._status_label.setText(f"limma Rscript DEG 未运行：{blockers}")
        return result

    def confirm_r_deseq2_parameters(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        analysis_state = build_analysis_center_state(self._project_root)
        plans = analysis_state.get("r_count_model_plans") if isinstance(analysis_state.get("r_count_model_plans"), dict) else {}
        plan_map = plans.get("plans") if isinstance(plans.get("plans"), dict) else {}
        deseq2_plan = plan_map.get("deseq2") if isinstance(plan_map.get("deseq2"), dict) else {}
        diagnostics = analysis_state.get("developer_diagnostics") if isinstance(analysis_state.get("developer_diagnostics"), dict) else {}
        formal_state = diagnostics.get("formal_deg_gate_state") if isinstance(diagnostics.get("formal_deg_gate_state"), dict) else {}
        deg_ready_package = formal_state.get("deg_ready_package") if isinstance(formal_state.get("deg_ready_package"), dict) else {}
        try:
            confirmation = save_r_deseq2_parameter_confirmation(
                self._project_root,
                deg_ready_package=deg_ready_package,
                multi_factor_preflight=deseq2_plan.get("preflight", {}) if isinstance(deseq2_plan.get("preflight"), dict) else {},
                dependency_snapshot=(deseq2_plan.get("runtime_gate", {}) or {}).get("dependency_snapshot", {}) if isinstance(deseq2_plan.get("runtime_gate"), dict) else {},
                log2fc_threshold=float(self._formal_deg_log2fc_input.text() or "1.0"),
                p_value_threshold=float(self._formal_deg_pvalue_input.text() or "0.05"),
                fdr_threshold=float(self._formal_deg_fdr_input.text() or "0.05"),
            )
        except ValueError:
            self._status_label.setText("DESeq2 参数确认失败：threshold 必须是数字。")
            return None
        self.refresh_task_center()
        if confirmation.get("status") == "confirmed":
            plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
            self._status_label.setText(f"已确认 DESeq2 参数；task-run id：{plan.get('task_run_id', '')}。只允许运行 raw count DESeq2 DEG，不生成 plot/report-ready。")
        else:
            blockers = "；".join(str(item) for item in confirmation.get("blockers", []) or []) or "DESeq2 gate 未通过"
            self._status_label.setText(f"DESeq2 参数未确认：{blockers}")
        return confirmation

    def run_r_deseq2_rscript_task(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        analysis_state = build_analysis_center_state(self._project_root)
        plans = analysis_state.get("r_count_model_plans") if isinstance(analysis_state.get("r_count_model_plans"), dict) else {}
        plan_map = plans.get("plans") if isinstance(plans.get("plans"), dict) else {}
        deseq2_plan = plan_map.get("deseq2") if isinstance(plan_map.get("deseq2"), dict) else {}
        confirmation = load_r_deseq2_parameter_confirmation(self._project_root)
        parameter_manifest = confirmation.get("parameter_manifest") if isinstance(confirmation.get("parameter_manifest"), dict) else {}
        output_plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
        runtime_gate = deseq2_plan.get("runtime_gate") if isinstance(deseq2_plan.get("runtime_gate"), dict) else {}
        result = run_r_deseq2_rscript_execution(
            self._project_root,
            count_table_path=str(parameter_manifest.get("expression_table_path") or ""),
            sample_group_map=parameter_manifest.get("sample_group_map") if isinstance(parameter_manifest.get("sample_group_map"), dict) else {},
            case_group=str(parameter_manifest.get("case_group") or ""),
            control_group=str(parameter_manifest.get("control_group") or ""),
            multi_factor_preflight=deseq2_plan.get("preflight", {}) if isinstance(deseq2_plan.get("preflight"), dict) else {},
            parameters_manifest=parameter_manifest,
            external_capabilities=runtime_gate.get("external_capabilities") if isinstance(runtime_gate.get("external_capabilities"), dict) else None,
            dependency_snapshot=runtime_gate.get("dependency_snapshot") if isinstance(runtime_gate.get("dependency_snapshot"), dict) else None,
            rscript_path=str((runtime_gate.get("dependency_snapshot", {}) or {}).get("rscript_path") or "Rscript") if isinstance(runtime_gate.get("dependency_snapshot"), dict) else "Rscript",
            result_id=str(output_plan.get("result_id") or ""),
            task_run_id=str(output_plan.get("task_run_id") or ""),
            input_package_id=str(parameter_manifest.get("input_package_id") or ""),
            source_dataset_id=str(parameter_manifest.get("input_package_id") or ""),
            source_repository_manifest="standardized_data/repositories/repository_manifest.json",
        )
        self.refresh_task_center()
        if result.get("status") == "passed":
            self._status_label.setText("已完成 DESeq2 Rscript DEG，并写入 result index v2。未生成 plot/report-ready/GSEA/survival。")
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "DESeq2 Rscript gate 未通过"
            self._status_label.setText(f"DESeq2 Rscript DEG 未运行：{blockers}")
        return result

    def run_controlled_ora_task(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        result = run_controlled_ora(self._project_root)
        self.refresh_task_center()
        if result.get("status") == "passed":
            self._status_label.setText("已完成 controlled ORA MVP，并写入 result index v2。未生成 GSEA、plot、report-ready 或 survival 输出。")
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "ORA gate 未通过"
            self._status_label.setText(f"controlled ORA 未运行：{blockers}")
        return result

    def run_controlled_gsea_task(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        result = run_controlled_preranked_gsea(self._project_root)
        self.refresh_task_center()
        if result.get("status") == "passed":
            self._status_label.setText("已完成 controlled preranked GSEA MVP，并写入 result index v2。未生成 plot、report-ready、survival 或临床解释。")
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "GSEA gate 未通过"
            self._status_label.setText(f"controlled preranked GSEA 未运行：{blockers}")
        return result

    def confirm_formal_deg_parameters(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        try:
            confirmation = save_deg_parameter_confirmation(
                self._project_root,
                method=self._formal_deg_method_input.currentText(),
                log2fc_threshold=float(self._formal_deg_log2fc_input.text() or "1.0"),
                p_value_threshold=float(self._formal_deg_pvalue_input.text() or "0.05"),
                fdr_threshold=float(self._formal_deg_fdr_input.text() or "0.05"),
            )
        except ValueError:
            self._status_label.setText("Formal DEG 参数确认失败：threshold 必须是数字。")
            return None
        self.refresh_task_center()
        if confirmation.get("status") == "confirmed":
            plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
            self._status_label.setText(f"已确认 formal DEG 参数；task-run id：{plan.get('task_run_id', '')}。确认后仍只允许运行两组 controlled DEG MVP。")
        else:
            blockers = "；".join(str(item) for item in confirmation.get("blockers", []) or []) or "formal DEG gate 未通过"
            self._status_label.setText(f"Formal DEG 参数未确认：{blockers}")
        return confirmation

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
            self.refresh_task_center()
            self._status_label.setText(f"已生成测试级 GEO 差异分析结果：{len(summaries)} 个表达矩阵{comparison_message}。该入口用于内部测试，不等于正式 DEG 分析。")
            return {"summaries": summaries, "warnings": warnings}
        if comparison_config is not None:
            self._status_label.setText("差异分析未运行：已确认比较组，但表达矩阵样本 ID 未能匹配。请修正比较组或选择其他表达文件。")
        else:
            self._status_label.setText("差异分析未运行：尚未确认比较组。请先点击“设置比较组”。")
        self._set_developer_details({"warnings": warnings})
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
        self._status_label.setText("已保存比较组设置，并重新运行分析任务检查。")
        return True

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
        root.addWidget(_header("分析任务中心", "根据当前数据判断哪些分析可配置、哪些还需要补充信息。", back_text="返回数据标准化", back_signal=self.back_requested))
        self._status_label = _status_label("请先完成数据识别和数据标准化，再查看可配置的分析任务。")
        root.addWidget(self._status_label)

        summary_card, summary_layout = _card("当前分析条件")
        self._analysis_input_label = _muted("核心输入：待检查。")
        self._analysis_input_label.setObjectName("analysisTaskInputSummary")
        self._analysis_resolver_label = _muted("Resolver：待检查 standardized analysis input packages。")
        self._analysis_resolver_label.setObjectName("analysisInputResolverSummary")
        self._analysis_result_label = _muted("结果状态：暂无结果。")
        self._analysis_result_label.setObjectName("analysisTaskResultSummary")
        self._analysis_next_step_label = _muted("下一步建议：先返回数据标准化确认输入。")
        self._analysis_next_step_label.setObjectName("analysisTaskNextStep")
        summary_layout.addWidget(self._analysis_input_label)
        summary_layout.addWidget(self._analysis_resolver_label)
        summary_layout.addWidget(self._analysis_result_label)
        summary_layout.addWidget(self._analysis_next_step_label)
        root.addWidget(summary_card)

        actions = QHBoxLayout()
        actions.addWidget(_button("刷新任务状态", "secondaryButton", self.refresh_task_center))
        actions.addWidget(_button("确认分组与比较设计", "secondaryButton", self.configure_comparison_groups))
        actions.addWidget(_button("进入差异分析配置", "primaryButton", self.create_deg_task_draft))
        self._formal_deg_confirm_button = _button("确认 formal DEG 参数", "secondaryButton", self.confirm_formal_deg_parameters)
        self._formal_deg_confirm_button.setEnabled(False)
        actions.addWidget(self._formal_deg_confirm_button)
        self._formal_deg_button = _button("运行两组 controlled DEG", "primaryButton", self.run_formal_controlled_deg_task)
        self._formal_deg_button.setEnabled(False)
        actions.addWidget(self._formal_deg_button)
        self._limma_design_button = _button("生成 limma design config", "secondaryButton", self.prepare_r_limma_design_config)
        self._limma_design_button.setEnabled(False)
        self._limma_design_button.setObjectName("prepareRLimmaDesignConfigButton")
        actions.addWidget(self._limma_design_button)
        self._limma_confirm_button = _button("确认 limma Rscript 参数", "secondaryButton", self.confirm_r_limma_parameters)
        self._limma_confirm_button.setEnabled(False)
        self._limma_confirm_button.setObjectName("confirmRLimmaParametersButton")
        actions.addWidget(self._limma_confirm_button)
        self._limma_rscript_button = _button("运行 limma Rscript DEG", "secondaryButton", self.run_r_limma_rscript_task)
        self._limma_rscript_button.setEnabled(False)
        self._limma_rscript_button.setObjectName("runRLimmaRscriptDegButton")
        actions.addWidget(self._limma_rscript_button)
        self._deseq2_confirm_button = _button("确认 DESeq2 参数", "secondaryButton", self.confirm_r_deseq2_parameters)
        self._deseq2_confirm_button.setEnabled(False)
        self._deseq2_confirm_button.setObjectName("confirmRDeseq2ParametersButton")
        actions.addWidget(self._deseq2_confirm_button)
        self._deseq2_rscript_button = _button("运行 DESeq2 Rscript DEG", "secondaryButton", self.run_r_deseq2_rscript_task)
        self._deseq2_rscript_button.setEnabled(False)
        self._deseq2_rscript_button.setObjectName("runRDeseq2RscriptDegButton")
        actions.addWidget(self._deseq2_rscript_button)
        self._ora_button = _button("运行 controlled ORA", "secondaryButton", self.run_controlled_ora_task)
        self._ora_button.setEnabled(False)
        self._ora_button.setObjectName("runControlledOraButton")
        actions.addWidget(self._ora_button)
        self._gsea_button = _button("运行 controlled GSEA", "secondaryButton", self.run_controlled_gsea_task)
        self._gsea_button.setEnabled(False)
        self._gsea_button.setObjectName("runControlledGseaButton")
        actions.addWidget(self._gsea_button)
        actions.addWidget(_button("免疫浸润 / TME评分", "secondaryButton", self.open_immune_scoring))
        actions.addWidget(_button("查看已导入差异分析结果", "secondaryButton", self.open_imported_deg_browser))
        actions.addStretch(1)
        root.addLayout(actions)

        self._tasks = _table(["分析任务", "当前状态", "需要输入", "当前缺少", "下一步"])
        self._tasks.setObjectName("analysisTaskUserTable")
        root.addWidget(self._tasks)
        _set_table_widths(self._tasks, [160, 150, 220, 220, 300])
        self._tasks.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

        package_card, package_layout = _card("Analysis input packages")
        package_layout.addWidget(_muted("来源：B8 resolver，仅使用 standardized repository / registry / analysis_input_repository。"))
        self._package_table = _table(["Package", "状态", "Value", "Gene ID", "下游任务", "Blockers", "Warnings", "修复建议"])
        self._package_table.setObjectName("analysisPackageTable")
        package_layout.addWidget(self._package_table)
        root.addWidget(package_card)
        _set_table_widths(self._package_table, [180, 110, 110, 110, 200, 260, 260, 320])
        self._package_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)

        legacy_card, legacy_layout = _card("Legacy asset pipeline")
        legacy_layout.addWidget(_muted("B16 legacy 链路仅用于 acquisition / standardization 收敛；不能绕过 B8 resolver 或直接生成 formal result。"))
        legacy_actions = QHBoxLayout()
        self._legacy_build_candidates_button = _button("生成 legacy candidates", "secondaryButton", self.build_legacy_asset_candidates)
        self._legacy_build_candidates_button.setObjectName("legacyBuildAssetCandidatesButton")
        self._legacy_materialize_button = _button("物化 candidates", "secondaryButton", self.materialize_legacy_asset_candidates)
        self._legacy_materialize_button.setObjectName("legacyMaterializeCandidatesButton")
        self._legacy_merge_button = _button("合并 repository manifest", "secondaryButton", self.merge_legacy_assets_into_repository_manifest)
        self._legacy_merge_button.setObjectName("legacyMergeRepositoryManifestButton")
        self._legacy_select_button = _button("确认 legacy asset selection", "secondaryButton", self.confirm_legacy_asset_selection)
        self._legacy_select_button.setObjectName("legacyConfirmAssetSelectionButton")
        for button in (self._legacy_build_candidates_button, self._legacy_materialize_button, self._legacy_merge_button, self._legacy_select_button):
            legacy_actions.addWidget(button)
        legacy_actions.addStretch(1)
        legacy_layout.addLayout(legacy_actions)
        self._legacy_pipeline_table = _table(["阶段", "状态", "Artifact", "数量", "Blockers / Warnings", "下一步"])
        self._legacy_pipeline_table.setObjectName("analysisLegacyAssetPipelineTable")
        legacy_layout.addWidget(self._legacy_pipeline_table)
        root.addWidget(legacy_card)
        _set_table_widths(self._legacy_pipeline_table, [210, 150, 320, 80, 360, 340])
        self._legacy_pipeline_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

        action_card, action_layout = _card("Action matrix and disabled reasons")
        action_layout.addWidget(_muted("Formal actions stay disabled until their audited resolver, parameter, dependency and result-schema gates pass."))
        self._action_table = _table(["动作", "状态", "按钮", "Disabled reason", "下一步"])
        self._action_table.setObjectName("analysisActionGateTable")
        action_layout.addWidget(self._action_table)
        root.addWidget(action_card)
        _set_table_widths(self._action_table, [190, 150, 180, 360, 300])
        self._action_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        capability_card, capability_layout = _card("Deep analysis capability map")
        capability_layout.addWidget(_muted("B19 capability map：区分 available、blocked、planned、disabled、spec-only、design-audit；R adapter ready 或 design-ready 不等于功能已完成。"))
        self._capability_table = _table(["能力", "类别", "实现状态", "UI 状态", "Formal", "Capability keys", "原因 / 边界"])
        self._capability_table.setObjectName("analysisCapabilityMapTable")
        capability_layout.addWidget(self._capability_table)
        root.addWidget(capability_card)
        _set_table_widths(self._capability_table, [220, 120, 190, 150, 90, 300, 420])
        self._capability_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)

        dependency_card, dependency_layout = _card("Dependency status")
        dependency_layout.addWidget(_muted("Detect-first only：显示缺失依赖并阻断 formal action，不自动安装。"))
        self._dependency_table = _table(["依赖", "状态", "版本", "Blockers", "打包影响", "操作"])
        self._dependency_table.setObjectName("analysisDependencyTable")
        dependency_layout.addWidget(self._dependency_table)
        root.addWidget(dependency_card)
        _set_table_widths(self._dependency_table, [150, 130, 110, 280, 260, 220])
        self._dependency_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        confirm_card, confirm_layout = _card("Formal DEG user confirmation")
        confirm_layout.addWidget(_muted("运行正式 DEG 前，用户必须确认 comparison、method、thresholds、value type compatibility、dependency snapshot、输出位置和 task-run id。"))
        confirm_controls = QHBoxLayout()
        self._formal_deg_method_input = QComboBox()
        self._formal_deg_method_input.addItems(["welch_t_test", "mann_whitney"])
        self._formal_deg_method_input.setObjectName("formalDegMethodInput")
        self._formal_deg_log2fc_input = QLineEdit("1.0")
        self._formal_deg_log2fc_input.setObjectName("formalDegLog2fcThresholdInput")
        self._formal_deg_log2fc_input.setPlaceholderText("log2FC")
        self._formal_deg_pvalue_input = QLineEdit("0.05")
        self._formal_deg_pvalue_input.setObjectName("formalDegPvalueThresholdInput")
        self._formal_deg_pvalue_input.setPlaceholderText("p-value")
        self._formal_deg_fdr_input = QLineEdit("0.05")
        self._formal_deg_fdr_input.setObjectName("formalDegFdrThresholdInput")
        self._formal_deg_fdr_input.setPlaceholderText("FDR")
        confirm_controls.addWidget(QLabel("Method"))
        confirm_controls.addWidget(self._formal_deg_method_input)
        confirm_controls.addWidget(QLabel("log2FC"))
        confirm_controls.addWidget(self._formal_deg_log2fc_input)
        confirm_controls.addWidget(QLabel("p-value"))
        confirm_controls.addWidget(self._formal_deg_pvalue_input)
        confirm_controls.addWidget(QLabel("FDR"))
        confirm_controls.addWidget(self._formal_deg_fdr_input)
        confirm_controls.addStretch(1)
        confirm_layout.addLayout(confirm_controls)
        self._formal_deg_confirmation_table = _table(["确认项", "当前值", "状态"])
        self._formal_deg_confirmation_table.setObjectName("analysisFormalDegConfirmationTable")
        confirm_layout.addWidget(self._formal_deg_confirmation_table)
        root.addWidget(confirm_card)
        _set_table_widths(self._formal_deg_confirmation_table, [180, 520, 240])
        self._formal_deg_confirmation_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        gate_card, gate_layout = _card("Result / plot / report gate preview")
        gate_layout.addWidget(_muted("Result semantics、plot source、report-ready 和 ORA readiness gate 均来自 B8/B10 contracts；preflight/testing/imported 不会升级为 formal result。"))
        self._formal_deg_gate_table = _table(["Formal DEG gate", "状态", "依据", "Blockers", "Warnings"])
        self._formal_deg_gate_table.setObjectName("analysisFormalDegGateTable")
        gate_layout.addWidget(self._formal_deg_gate_table)
        self._gate_table = _table(["Gate", "状态", "依据", "Blockers", "Warnings"])
        self._gate_table.setObjectName("analysisGatePreviewTable")
        gate_layout.addWidget(self._gate_table)
        root.addWidget(gate_card)
        _set_table_widths(self._formal_deg_gate_table, [170, 170, 230, 320, 300])
        self._formal_deg_gate_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        _set_table_widths(self._gate_table, [170, 170, 230, 320, 300])
        self._gate_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        survival_card, survival_layout = _card("Survival / clinical")
        survival_layout.addWidget(_muted("B21 保留 KM/log-rank、single-variable Cox、multivariate Cox 的 gate；risk score/nomogram 只做设计审计，不生成风险分层、临床结论或 survival report-ready。"))
        self._survival_table = _table(["项目", "状态", "资产/字段", "Backend", "禁用原因", "Warnings"])
        self._survival_table.setObjectName("analysisSurvivalClinicalTable")
        survival_layout.addWidget(self._survival_table)
        root.addWidget(survival_card)
        _set_table_widths(self._survival_table, [190, 140, 240, 160, 320, 260])
        self._survival_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

        developer_card, developer_layout = _card("开发者诊断")
        developer_actions = QHBoxLayout()
        developer_actions.addWidget(_button("展开技术细节", "secondaryButton", lambda: _toggle_details(self._records)))
        self._task_type_input = QLineEdit()
        self._task_type_input.setPlaceholderText("task type，例如 differential_expression")
        developer_actions.addWidget(self._task_type_input)
        developer_actions.addWidget(_button("创建指定任务记录", "secondaryButton", self.create_task))
        developer_actions.addWidget(_button("生成测试级 GEO 差异结果", "secondaryButton", self.run_geo_differential_expression_task))
        developer_actions.addStretch(1)
        developer_layout.addLayout(developer_actions)
        self._records = _text_preview(120)
        self._records.setObjectName("analysisTaskDeveloperDiagnostics")
        self._records.setVisible(False)
        developer_layout.addWidget(self._records)
        root.addWidget(developer_card)
        root.addWidget(_button("继续：结果浏览", "primaryButton", self.continue_to_results), alignment=Qt.AlignLeft)

    def _render(self, center: dict[str, object]) -> None:
        tasks = [item for item in center.get("tasks", []) or [] if isinstance(item, dict)]
        records = load_task_records(self._project_root) if self._project_root else []
        result_index = load_result_index(self._project_root) if self._project_root else {}
        resolver = resolve_analysis_inputs(self._project_root) if self._project_root else None
        analysis_state = build_analysis_center_state(self._project_root) if self._project_root else {}
        entries = [item for item in result_index.get("entries", []) or [] if isinstance(item, dict)]
        imported_deg = _analysis_imported_deg_detected(self._project_root)
        configurable = sum(1 for item in tasks if item.get("can_run"))
        blocked = len(tasks) - configurable
        self._status_label.setText(f"分析任务中心：{len(tasks)} 类任务；可配置 {configurable} 类，需要补充 {blocked} 类。")
        self._analysis_input_label.setText(_analysis_task_input_summary(tasks))
        self._analysis_resolver_label.setText(_analysis_input_resolver_summary(resolver.to_dict() if resolver else {}))
        self._analysis_result_label.setText(_analysis_task_result_summary(entries, records, imported_deg))
        self._analysis_next_step_label.setText(_analysis_task_next_step(tasks, entries, records, imported_deg))
        _fill_table(self._tasks, _analysis_task_user_rows(tasks, self._project_root, entries, records))
        _fill_table(self._package_table, _analysis_ui_package_rows(analysis_state.get("package_rows", [])))
        _fill_table(self._legacy_pipeline_table, _analysis_ui_legacy_pipeline_rows(analysis_state.get("legacy_asset_pipeline", {})))
        self._sync_legacy_pipeline_buttons(analysis_state)
        _fill_table(self._action_table, _analysis_ui_action_rows(analysis_state.get("action_rows", []), normal_user_only=True))
        _fill_table(self._capability_table, _analysis_ui_capability_rows(analysis_state.get("analysis_capability_map", {})))
        formal_action = _analysis_ui_action(analysis_state.get("action_rows", []), "formal_deg")
        confirmation_action = _analysis_ui_action(analysis_state.get("action_rows", []), "formal_deg_parameter_confirmation")
        limma_design_action = _analysis_ui_action(analysis_state.get("action_rows", []), "r_limma_design_config")
        limma_confirmation_action = _analysis_ui_action(analysis_state.get("action_rows", []), "r_limma_parameter_confirmation")
        limma_action = _analysis_ui_action(analysis_state.get("action_rows", []), "formal_deg_limma_rscript")
        deseq2_confirmation_action = _analysis_ui_action(analysis_state.get("action_rows", []), "r_deseq2_parameter_confirmation")
        deseq2_action = _analysis_ui_action(analysis_state.get("action_rows", []), "formal_deg_deseq2_rscript")
        ora_action = _analysis_ui_action(analysis_state.get("action_rows", []), "run_ora_enrichment")
        gsea_action = _analysis_ui_action(analysis_state.get("action_rows", []), "formal_gsea")
        self._formal_deg_confirm_button.setEnabled(bool(confirmation_action.get("enabled")))
        self._formal_deg_confirm_button.setToolTip(str(confirmation_action.get("disabled_reason") or confirmation_action.get("next_action") or "确认 formal DEG 参数"))
        self._formal_deg_button.setEnabled(bool(formal_action.get("enabled")))
        if formal_action.get("enabled"):
            self._formal_deg_button.setToolTip("运行两组 controlled DEG MVP；只写 result index v2，不生成 GSEA/plot/report-ready/survival。")
        else:
            self._formal_deg_button.setToolTip(str(formal_action.get("disabled_reason") or "formal DEG gate 未通过"))
        self._limma_design_button.setEnabled(bool(limma_design_action.get("enabled")))
        self._limma_design_button.setToolTip(str(limma_design_action.get("next_action") or limma_design_action.get("disabled_reason") or "limma design config gate 未通过"))
        self._limma_confirm_button.setEnabled(bool(limma_confirmation_action.get("enabled")))
        self._limma_confirm_button.setToolTip(str(limma_confirmation_action.get("disabled_reason") or limma_confirmation_action.get("next_action") or "确认 limma Rscript 参数"))
        self._limma_rscript_button.setEnabled(bool(limma_action.get("enabled")))
        self._limma_rscript_button.setToolTip(str(limma_action.get("next_action") or limma_action.get("disabled_reason") or "limma Rscript gate 未通过"))
        self._deseq2_confirm_button.setEnabled(bool(deseq2_confirmation_action.get("enabled")))
        self._deseq2_confirm_button.setToolTip(str(deseq2_confirmation_action.get("disabled_reason") or deseq2_confirmation_action.get("next_action") or "确认 DESeq2 参数"))
        self._deseq2_rscript_button.setEnabled(bool(deseq2_action.get("enabled")))
        self._deseq2_rscript_button.setToolTip(str(deseq2_action.get("next_action") or deseq2_action.get("disabled_reason") or "DESeq2 Rscript gate 未通过"))
        self._ora_button.setEnabled(bool(ora_action.get("enabled")))
        self._ora_button.setToolTip(str(ora_action.get("next_action") or ora_action.get("disabled_reason") or "controlled ORA gate 未通过"))
        self._gsea_button.setEnabled(bool(gsea_action.get("enabled")))
        self._gsea_button.setToolTip(str(gsea_action.get("next_action") or gsea_action.get("disabled_reason") or "controlled GSEA gate 未通过"))
        _fill_table(self._dependency_table, _analysis_ui_dependency_rows(analysis_state.get("dependency_rows", [])))
        self._sync_confirmation_controls(analysis_state)
        _fill_table(self._formal_deg_confirmation_table, _analysis_ui_confirmation_rows(analysis_state.get("developer_diagnostics", {}).get("formal_deg_gate_state", {}) if isinstance(analysis_state.get("developer_diagnostics"), dict) else {}))
        _fill_table(self._formal_deg_gate_table, _analysis_ui_gate_rows(analysis_state.get("formal_deg_gate_rows", [])))
        _fill_table(self._gate_table, _analysis_ui_gate_rows([*(analysis_state.get("gate_rows", []) or []), *(analysis_state.get("ora_gate_rows", []) or []), *(analysis_state.get("gsea_gate_rows", []) or [])]))
        _fill_table(self._survival_table, _analysis_ui_survival_rows(analysis_state.get("survival_clinical_rows", [])))
        self._set_developer_details({"analysis_task_center": center, "task_records": records, "result_index": result_index, "analysis_input_resolver": resolver.to_dict() if resolver else {}, "analysis_center_state": analysis_state})

    def _set_developer_details(self, payload: dict[str, object]) -> None:
        self._records.setPlainText(_json(payload))

    def _sync_confirmation_controls(self, analysis_state: dict[str, object]) -> None:
        diagnostics = analysis_state.get("developer_diagnostics") if isinstance(analysis_state.get("developer_diagnostics"), dict) else {}
        formal_state = diagnostics.get("formal_deg_gate_state") if isinstance(diagnostics.get("formal_deg_gate_state"), dict) else {}
        parameter_gate = formal_state.get("parameter_gate") if isinstance(formal_state.get("parameter_gate"), dict) else {}
        method = str(parameter_gate.get("method") or "welch_t_test")
        index = self._formal_deg_method_input.findText(method)
        if index >= 0:
            self._formal_deg_method_input.setCurrentIndex(index)
        for widget, key, default in (
            (self._formal_deg_log2fc_input, "log2fc_threshold", "1.0"),
            (self._formal_deg_pvalue_input, "p_value_threshold", "0.05"),
            (self._formal_deg_fdr_input, "fdr_threshold", "0.05"),
        ):
            value = parameter_gate.get(key, default)
            if not widget.hasFocus():
                widget.setText(str(value))

    def _sync_legacy_pipeline_buttons(self, analysis_state: dict[str, object]) -> None:
        pipeline = analysis_state.get("legacy_asset_pipeline") if isinstance(analysis_state.get("legacy_asset_pipeline"), dict) else {}
        operations = {
            str(item.get("operation_id") or ""): item
            for item in pipeline.get("operations", []) or []
            if isinstance(item, dict)
        }
        for operation_id, button in (
            ("legacy_build_candidates", self._legacy_build_candidates_button),
            ("legacy_materialize_candidates", self._legacy_materialize_button),
            ("legacy_merge_repository_manifest", self._legacy_merge_button),
            ("legacy_confirm_asset_selection", self._legacy_select_button),
        ):
            operation = operations.get(operation_id, {})
            enabled = bool(operation.get("enabled"))
            button.setEnabled(enabled)
            tooltip = str(operation.get("next_action") if enabled else operation.get("disabled_reason") or "legacy pipeline operation blocked")
            button.setToolTip(tooltip)


class BioinformaticsDegConfigWidget(QWidget):
    back_requested = Signal()

    def __init__(self, *, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self.setObjectName("bioinformaticsDegConfigPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_back is not None:
            self.back_requested.connect(on_back)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_preflight_state()

    def refresh_preflight_state(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            self._set_developer_details({})
            return None
        state = _deg_config_user_state(self._project_root)
        manifest = load_deg_preflight_manifest(self._project_root)
        self._render(state, manifest)
        return {"state": state, "preflight_manifest": manifest}

    def run_preflight_check(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        try:
            result = build_deg_preflight(
                self._project_root,
                method=self._method_input.text().strip() or "DEG executor not connected",
                log2fc_threshold=float(self._log2fc_input.text().strip() or "1.0"),
                p_value_threshold=float(self._p_value_input.text().strip() or "0.05"),
                fdr_threshold=float(self._fdr_input.text().strip() or "0.05"),
            )
        except ValueError:
            self._status_label.setText("阈值格式不正确，请输入数字。")
            return None
        self.refresh_preflight_state()
        status_text = {
            "passed": "preflight 已通过",
            "warning": "preflight 已生成，但存在警告",
            "blocked": "preflight 已生成，但存在阻塞",
            "draft": "配置草稿",
        }.get(result.status, "preflight 已生成")
        self._status_label.setText(f"{status_text}；这是输入校验记录，不是 DEG 结果，也不会进入正式结果页。")
        return result.manifest

    def status_message(self) -> str:
        return self._status_label.text()

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(
            _header(
                "DEG 配置与 preflight 输入校验",
                "确认差异分析运行前输入是否齐备；本页仅配置、仅校验，未运行真实差异分析。",
                back_text="返回分析任务中心",
                back_signal=self.back_requested,
            )
        )
        self._status_label = _status_label("请先完成数据标准化，并确认分组与比较设计。")
        root.addWidget(self._status_label)

        input_card, input_layout = _card("当前分析输入")
        self._input_summary_label = _muted("表达矩阵、样本信息和分组状态待检查。")
        self._input_summary_label.setObjectName("degInputSummary")
        self._comparison_summary_label = _muted("比较设计：待确认。")
        self._comparison_summary_label.setObjectName("degComparisonSummary")
        self._boundary_label = _muted("边界：仅配置 / 仅校验 / 未运行真实差异分析。")
        self._boundary_label.setObjectName("degConfigBoundary")
        input_layout.addWidget(self._input_summary_label)
        input_layout.addWidget(self._comparison_summary_label)
        input_layout.addWidget(self._boundary_label)
        root.addWidget(input_card)

        config_card, config_layout = _card("DEG 配置草稿")
        config_layout.addWidget(_muted("方法状态：two-group Python DEG、limma、DESeq2 已走 gated execution；edgeR 仅 parameter/runtime planning。"))
        method_row = QHBoxLayout()
        self._method_input = QLineEdit("DEG executor not connected")
        self._method_input.setPlaceholderText("方法草稿，例如 DESeq2 待接入")
        self._log2fc_input = QLineEdit("1.0")
        self._log2fc_input.setPlaceholderText("log2FC")
        self._p_value_input = QLineEdit("0.05")
        self._p_value_input.setPlaceholderText("p value")
        self._fdr_input = QLineEdit("0.05")
        self._fdr_input.setPlaceholderText("FDR")
        for editor in (self._method_input, self._log2fc_input, self._p_value_input, self._fdr_input):
            method_row.addWidget(editor)
        config_layout.addLayout(method_row)
        root.addWidget(config_card)

        actions = QHBoxLayout()
        actions.addWidget(_button("生成 preflight 输入校验", "primaryButton", self.run_preflight_check))
        actions.addWidget(_button("刷新状态", "secondaryButton", self.refresh_preflight_state))
        actions.addWidget(_button("返回分析任务中心", "secondaryButton", self.back_requested.emit))
        actions.addStretch(1)
        root.addLayout(actions)

        self._checks_table = _table(["检查项", "状态", "说明"])
        self._checks_table.setObjectName("degPreflightCheckTable")
        root.addWidget(self._checks_table)
        _set_table_widths(self._checks_table, [180, 120, 520])
        self._checks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        self._next_step_label = _muted("下一步建议：先返回标准化或确认分组。")
        self._next_step_label.setObjectName("degNextStep")
        root.addWidget(self._next_step_label)

        developer_card, developer_layout = _card("开发者诊断")
        developer_actions = QHBoxLayout()
        developer_actions.addWidget(_button("展开技术细节", "secondaryButton", lambda: _toggle_details(self._developer_details)))
        developer_actions.addStretch(1)
        developer_layout.addLayout(developer_actions)
        self._developer_details = _text_preview(160)
        self._developer_details.setObjectName("degPreflightDeveloperDiagnostics")
        self._developer_details.setVisible(False)
        developer_layout.addWidget(self._developer_details)
        root.addWidget(developer_card)

    def _render(self, state: dict[str, object], manifest: dict[str, object] | None) -> None:
        self._input_summary_label.setText(str(state.get("input_summary_zh") or "当前输入状态待检查。"))
        self._comparison_summary_label.setText(str(state.get("comparison_summary_zh") or "比较设计：待确认。"))
        self._boundary_label.setText("配置草稿：仅配置 / 仅校验 / 未运行真实差异分析；preflight passed 不等于 real computed result。")
        if manifest is None:
            self._status_label.setText("DEG 配置页：尚未生成 preflight；当前是配置草稿。")
            _fill_table(
                self._checks_table,
                [
                    ["表达矩阵", str(state.get("expression_status_zh") or "待检查"), "需要 count matrix 或可用表达矩阵。"],
                    ["样本信息", str(state.get("metadata_status_zh") or "待检查"), "需要样本信息或用户确认的比较组设置。"],
                    ["分组与比较设计", str(state.get("comparison_status_zh") or "待确认"), "需要 case/control 或用户确认比较。"],
                    ["真实执行", "未运行", "本页不会运行真实 DEG，也不会生成结果图。"],
                ],
            )
        else:
            status = str(manifest.get("status_label_zh") or manifest.get("status") or "未知状态")
            self._status_label.setText(f"DEG preflight 状态：{status}；该记录不是 DEG 结果。")
            rows = []
            for check in manifest.get("checks", []) or []:
                if not isinstance(check, dict):
                    continue
                rows.append(
                    [
                        _deg_check_label(str(check.get("check_id") or "")),
                        _deg_preflight_check_status_label(str(check.get("status") or "")),
                        str(check.get("message_zh") or ""),
                    ]
                )
            _fill_table(self._checks_table, rows)
        self._next_step_label.setText(str(state.get("next_step_zh") or "下一步建议：返回分析任务中心。"))
        self._set_developer_details({"deg_config_state": state, "preflight_manifest": manifest or {}})

    def _set_developer_details(self, payload: dict[str, object]) -> None:
        self._developer_details.setPlainText(_json(payload))


class BioinformaticsImmuneInfiltrationWidget(QWidget):
    back_requested = Signal()

    def __init__(self, *, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self._readiness: dict[str, object] = {}
        self._last_result: object | None = None
        self.setObjectName("bioinformaticsImmuneInfiltrationPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_back is not None:
            self.back_requested.connect(on_back)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_state()

    def refresh_state(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        readiness = build_immune_infiltration_readiness(self._project_root)
        self._readiness = readiness
        self._render_readiness(readiness)
        return readiness

    def run_scoring(self) -> object | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        dataset = self._selected_dataset()
        if not dataset:
            self._status_label.setText("没有可用于 B7 的表达矩阵。")
            return None
        signatures = self._selected_signatures()
        if not signatures:
            self._status_label.setText("请至少选择一个 immune / TME signature。")
            return None
        readiness = build_immune_infiltration_readiness(self._project_root, dataset_id=str(dataset.get("dataset_id") or ""), signatures=signatures)
        if not readiness.get("can_run_scoring"):
            self._render_readiness(readiness)
            self._status_label.setText("当前输入未通过 B7 readiness，不能运行评分。")
            return None
        try:
            result = run_immune_scoring(
                self._project_root,
                expression_matrix_path=str(dataset.get("expression_matrix_path") or ""),
                selected_signatures=signatures,
                dataset_id=str(dataset.get("dataset_id") or ""),
                dataset_label=str(dataset.get("label") or ""),
                input_value_type=str(dataset.get("value_type") or "unknown"),
                gene_id_column=str(dataset.get("gene_id_column") or ""),
                sample_columns=[str(item) for item in dataset.get("sample_columns", []) or []],
                scoring_method=self._method_combo.currentText(),
                value_transform=self._transform_combo.currentText(),
            )
            preflight = build_linkage_preflight(
                self._project_root,
                score_matrix_path=result.score_matrix_path,
                expression_matrix_path=str(dataset.get("expression_matrix_path") or ""),
                target_gene=self._target_gene_input.text().strip(),
            )
            report = generate_immune_tme_report(self._project_root, manifest_path=result.manifest_path, linkage_preflight=preflight)
        except Exception as exc:
            self._status_label.setText(f"免疫浸润 / TME评分失败：{exc}")
            return None
        self._last_result = result
        self._render_result(result, preflight, report)
        self._status_label.setText("免疫浸润 / TME评分已完成；结果为探索性 bulk signature score，不自动进入 DEG/GSEA/KM/Cox。")
        return result

    def status_message(self) -> str:
        return self._status_label.text()

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(
            _header(
                "免疫浸润 / TME评分",
                "基于 bulk 表达矩阵计算探索性 immune / TME signature score。",
                back_text="返回分析任务中心",
                back_signal=self.back_requested,
            )
        )
        self._status_label = _status_label("请先完成数据检查与准备，并选择可用于 B7 的表达矩阵。")
        root.addWidget(self._status_label)

        input_card, input_layout = _card("输入与规则")
        self._dataset_combo = QComboBox()
        self._dataset_combo.setObjectName("immuneDatasetCombo")
        self._dataset_combo.currentIndexChanged.connect(lambda _index: self._render_dataset_detail())
        input_layout.addWidget(QLabel("表达矩阵"))
        input_layout.addWidget(self._dataset_combo)
        self._input_status_label = _muted("输入状态待检查。")
        self._input_status_label.setObjectName("immuneInputStatusCard")
        self._value_policy_label = _muted("value type policy：推荐 TPM；raw counts / unknown 默认阻断。")
        self._value_policy_label.setObjectName("immuneValueTypePolicy")
        self._limitations_label = _muted("限制：bulk signature score 不等同于真实免疫细胞比例；不执行 CIBERSORT/xCell/ESTIMATE。")
        self._limitations_label.setObjectName("immuneLimitationsLabel")
        input_layout.addWidget(self._input_status_label)
        input_layout.addWidget(self._value_policy_label)
        input_layout.addWidget(self._limitations_label)
        root.addWidget(input_card)

        config_card, config_layout = _card("Signature 与评分配置")
        self._signature_ids_input = QLineEdit("cd8_t_cell,cytolytic_activity,pdcd1_checkpoint")
        self._signature_ids_input.setObjectName("immuneSignatureIdsInput")
        self._signature_ids_input.setPlaceholderText("signature id，逗号分隔")
        config_layout.addWidget(self._signature_ids_input)
        option_row = QHBoxLayout()
        self._method_combo = QComboBox()
        self._method_combo.setObjectName("immuneScoringMethodCombo")
        self._method_combo.addItems(["mean_zscore", "mean_expression"])
        self._transform_combo = QComboBox()
        self._transform_combo.setObjectName("immuneValueTransformCombo")
        self._transform_combo.addItems(["none", "log2_x_plus_1"])
        self._target_gene_input = QLineEdit()
        self._target_gene_input.setObjectName("immuneTargetGeneInput")
        self._target_gene_input.setPlaceholderText("可选 target gene correlation preflight")
        option_row.addWidget(self._method_combo)
        option_row.addWidget(self._transform_combo)
        option_row.addWidget(self._target_gene_input)
        config_layout.addLayout(option_row)
        self._signature_table = _table(["Signature", "类别", "基因数", "说明"])
        self._signature_table.setObjectName("immuneSignatureTable")
        _set_table_widths(self._signature_table, [190, 120, 80, 420])
        self._signature_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        config_layout.addWidget(self._signature_table)
        root.addWidget(config_card)

        actions = QHBoxLayout()
        self._run_button = _button("运行免疫浸润 / TME评分", "primaryButton", self.run_scoring)
        self._run_button.setObjectName("immuneRunButton")
        actions.addWidget(self._run_button)
        actions.addWidget(_button("刷新状态", "secondaryButton", self.refresh_state))
        actions.addWidget(_button("返回分析任务中心", "secondaryButton", self.back_requested.emit))
        actions.addStretch(1)
        root.addLayout(actions)

        result_card, result_layout = _card("结果预览")
        self._run_summary_label = _muted("尚未运行评分。")
        self._run_summary_label.setObjectName("immuneRunSummary")
        result_layout.addWidget(self._run_summary_label)
        self._score_preview = _table(["signature_id", "display_name", "coverage_status"])
        self._score_preview.setObjectName("immuneScorePreviewTable")
        self._coverage_preview = _table(["signature_id", "matched_gene_count", "coverage_ratio", "status"])
        self._coverage_preview.setObjectName("immuneCoverageTable")
        result_layout.addWidget(self._score_preview)
        result_layout.addWidget(self._coverage_preview)
        root.addWidget(result_card)

        developer_card, developer_layout = _card("开发者诊断")
        developer_actions = QHBoxLayout()
        developer_actions.addWidget(_button("展开技术细节", "secondaryButton", lambda: _toggle_details(self._developer_details)))
        developer_actions.addStretch(1)
        developer_layout.addLayout(developer_actions)
        self._developer_details = _text_preview(160)
        self._developer_details.setObjectName("immuneDeveloperDiagnostics")
        self._developer_details.setVisible(False)
        developer_layout.addWidget(self._developer_details)
        root.addWidget(developer_card)

    def _render_readiness(self, readiness: dict[str, object]) -> None:
        datasets = [item for item in readiness.get("available_datasets", []) or [] if isinstance(item, dict)]
        selected_id = str((readiness.get("input_summary") or {}).get("dataset_id") if isinstance(readiness.get("input_summary"), dict) else "")
        self._dataset_combo.blockSignals(True)
        self._dataset_combo.clear()
        for dataset in datasets:
            self._dataset_combo.addItem(str(dataset.get("label") or dataset.get("dataset_id") or "未命名表达矩阵"), dataset)
            if selected_id and str(dataset.get("dataset_id") or "") == selected_id:
                self._dataset_combo.setCurrentIndex(self._dataset_combo.count() - 1)
        self._dataset_combo.blockSignals(False)
        self._render_dataset_detail()
        catalog_payload = load_signature_catalog()
        signatures = [_signature_from_catalog_item(item) for item in catalog_payload.get("signatures", []) if isinstance(item, dict)]
        _fill_table(
            self._signature_table,
            [
                [
                    signature.display_name,
                    signature.category,
                    str(len(signature.genes)),
                    signature.notes or "exploratory built-in signature",
                ]
                for signature in signatures
            ],
        )
        blockers = [str(item) for item in readiness.get("blockers", []) or []]
        warnings = [str(item) for item in readiness.get("warnings", []) or []]
        self._run_button.setEnabled(bool(readiness.get("can_run_scoring")))
        self._status_label.setText(
            "B7 readiness："
            + ("可运行。" if readiness.get("can_run_scoring") else "不可运行。")
            + (f" 阻塞：{'；'.join(blockers)}。" if blockers else "")
            + (f" 提示：{'；'.join(warnings[:3])}。" if warnings else "")
        )
        self._developer_details.setPlainText(_json({"immune_infiltration_readiness": readiness}))

    def _render_dataset_detail(self) -> None:
        dataset = self._selected_dataset()
        if not dataset:
            self._input_status_label.setText("未发现可用于 B7 的表达矩阵。")
            self._value_policy_label.setText("value type policy：无输入。")
            return
        self._input_status_label.setText(
            f"输入：{dataset.get('source')}；样本 {dataset.get('sample_count')}；基因 {dataset.get('gene_count')}；gene id {dataset.get('gene_id_type')}。"
        )
        self._value_policy_label.setText(f"value type：{dataset.get('value_type')}；推荐 TPM / normalized expression；raw counts / unknown 默认阻断。")

    def _render_result(self, result: object, preflight: dict[str, object], report: dict[str, object]) -> None:
        self._run_summary_label.setText(
            f"run：{getattr(result, 'run_id', '')}；signature {getattr(result, 'scored_signature_count', 0)}/{getattr(result, 'signature_count', 0)}；"
            f"sample {getattr(result, 'sample_count', 0)}；report 已生成。"
        )
        _fill_table(self._score_preview, _tsv_rows(getattr(result, "score_matrix_path", ""), limit=8, columns=["signature_id", "display_name", "coverage_status"]))
        _fill_table(self._coverage_preview, _tsv_rows(getattr(result, "coverage_path", ""), limit=8, columns=["signature_id", "matched_gene_count", "coverage_ratio", "status"]))
        self._developer_details.setPlainText(
            _json(
                {
                    "immune_scoring_result": result.to_dict() if hasattr(result, "to_dict") else {},
                    "linkage_preflight": preflight,
                    "report": report,
                }
            )
        )

    def _selected_dataset(self) -> dict[str, object] | None:
        data = self._dataset_combo.currentData()
        return data if isinstance(data, dict) else None

    def _selected_signatures(self) -> list[object]:
        requested = {
            item.strip()
            for item in self._signature_ids_input.text().replace("\n", ",").split(",")
            if item.strip()
        }
        catalog_payload = load_signature_catalog()
        catalog = [_signature_from_catalog_item(item) for item in catalog_payload.get("signatures", []) if isinstance(item, dict)]
        if not requested:
            return catalog
        return [signature for signature in catalog if signature.signature_id in requested or signature.display_name in requested]


class BioinformaticsImportedDegBrowserWidget(QWidget):
    back_requested = Signal()
    report_requested = Signal(object)

    def __init__(
        self,
        *,
        on_back: Callable[[], None] | None = None,
        on_report: Callable[[Path], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self.setObjectName("bioinformaticsImportedDegBrowserPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        if on_back is not None:
            self.back_requested.connect(on_back)
        if on_report is not None:
            self.report_requested.connect(on_report)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_imported_deg_results()

    def refresh_imported_deg_results(self) -> list[object]:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            self._set_developer_details({})
            return []
        results = list_imported_deg_results(self._project_root)
        self._render(results)
        return results

    def mark_report_candidates(self) -> list[dict[str, object]]:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return []
        entries = mark_imported_deg_report_candidates(self._project_root)
        self.refresh_imported_deg_results()
        self._status_label.setText("已标记导入结果为报告候选；仍必须说明为用户导入 / 外部分析结果，不是 BioMedPilot 重新计算。")
        return entries

    def continue_to_report(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        self.report_requested.emit(self._project_root)

    def status_message(self) -> str:
        return self._status_label.text()

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(
            _header(
                "导入结果浏览",
                "查看用户导入 / 外部分析得到的差异分析结果；这里不会运行 DEG，也不会生成火山图或富集结果。",
                back_text="返回结果浏览",
                back_signal=self.back_requested,
            )
        )
        self._status_label = _status_label("请先导入差异分析结果表，或返回结果浏览。")
        root.addWidget(self._status_label)

        summary_card, summary_layout = _card("当前导入 DEG 状态")
        self._summary_label = _muted("当前是否存在已导入 DEG 结果：待检查。")
        self._summary_label.setObjectName("importedDegSummary")
        self._boundary_label = _muted("这是用户导入的外部差异分析结果，不是 BioMedPilot 重新计算得到的结果。")
        self._boundary_label.setObjectName("importedDegBoundary")
        self._next_step_label = _muted("下一步建议：先确认列映射和来源标签。")
        self._next_step_label.setObjectName("importedDegNextStep")
        summary_layout.addWidget(self._summary_label)
        summary_layout.addWidget(self._boundary_label)
        summary_layout.addWidget(self._next_step_label)
        root.addWidget(summary_card)

        actions = QHBoxLayout()
        actions.addWidget(_button("刷新导入结果", "secondaryButton", self.refresh_imported_deg_results))
        actions.addWidget(_button("标记为报告候选", "primaryButton", self.mark_report_candidates))
        actions.addWidget(_button("查看报告草稿", "secondaryButton", self.continue_to_report))
        actions.addStretch(1)
        root.addLayout(actions)

        self._results = _table(["结果名称", "来源说明", "状态", "可用于报告", "主要列识别", "上调 / 下调 / 不显著", "查看详情"])
        self._results.setObjectName("importedDegUserTable")
        root.addWidget(self._results)
        _set_table_widths(self._results, [180, 190, 120, 110, 260, 180, 300])
        self._results.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)

        detail_card, detail_layout = _card("结果详情预览")
        self._detail_label = _muted("请选择或刷新导入结果后查看详情。预览限制行数，避免一次性加载大文件。")
        self._detail_label.setObjectName("importedDegDetailSummary")
        detail_layout.addWidget(self._detail_label)
        self._preview = _table(["列"] )
        self._preview.setObjectName("importedDegPreviewTable")
        detail_layout.addWidget(self._preview)
        self._note = _text_preview(90)
        self._note.setObjectName("importedDegUserNote")
        self._note.setPlainText("用户备注：仅用于人工阅读，不参与内部计算字段。")
        detail_layout.addWidget(self._note)
        root.addWidget(detail_card)

        developer_card, developer_layout = _card("开发者诊断")
        developer_actions = QHBoxLayout()
        developer_actions.addWidget(_button("展开技术细节", "secondaryButton", lambda: _toggle_details(self._developer_details)))
        developer_actions.addStretch(1)
        developer_layout.addLayout(developer_actions)
        self._developer_details = _text_preview(160)
        self._developer_details.setObjectName("importedDegDeveloperDiagnostics")
        self._developer_details.setVisible(False)
        developer_layout.addWidget(self._developer_details)
        root.addWidget(developer_card)

    def _render(self, results: list[object]) -> None:
        typed_results = [result for result in results if hasattr(result, "to_user_row")]
        if not typed_results:
            self._status_label.setText("暂无已导入差异分析结果。请先导入外部 DEG 表格，或返回分析任务中心。")
            self._summary_label.setText("当前是否存在已导入 DEG 结果：否。")
            self._next_step_label.setText("下一步建议：导入外部 DEG 表格，或继续 B2 preflight 配置。")
            _fill_table(self._results, [])
            self._render_preview(None)
            self._set_developer_details({"imported_deg_results": [], "summary": {}})
            return
        ready = sum(1 for result in typed_results if getattr(result, "status", "") == "ready")
        needs_confirmation = sum(1 for result in typed_results if getattr(result, "status", "") == "needs_confirmation")
        missing = sum(1 for result in typed_results if getattr(result, "status", "") == "missing")
        self._status_label.setText(f"导入结果浏览：{len(typed_results)} 个 imported DEG；可浏览 {ready} 个，待确认 {needs_confirmation} 个，缺少文件 {missing} 个。")
        self._summary_label.setText(f"当前是否存在已导入 DEG 结果：是，共 {len(typed_results)} 个。")
        self._boundary_label.setText("这是用户导入的外部差异分析结果，不是 BioMedPilot 重新计算得到的结果。")
        self._next_step_label.setText("下一步建议：确认列映射和来源说明后，可标记为报告候选；报告中必须保留导入标签。")
        _fill_table(self._results, [result.to_user_row() for result in typed_results])
        self._render_preview(typed_results[0])
        self._set_developer_details(
            {
                "imported_deg_results": [result.to_dict() for result in typed_results],
                "summary": imported_deg_summary(self._project_root) if self._project_root else {},
                "result_index": load_result_index(self._project_root) if self._project_root else {},
            }
        )

    def _render_preview(self, result: object | None) -> None:
        if result is None:
            self._detail_label.setText("结果详情：暂无导入 DEG。")
            self._preview.setColumnCount(1)
            self._preview.setHorizontalHeaderLabels(["预览"])
            _fill_table(self._preview, [])
            return
        headers = list(getattr(result, "preview_headers", ()) or ())
        rows = [list(row) for row in getattr(result, "preview_rows", ()) or ()]
        mapping = getattr(result, "column_mapping", {}) or {}
        counts = getattr(result, "regulation_counts", {}) or {}
        top_up = getattr(result, "top_up_genes", ()) or ()
        top_down = getattr(result, "top_down_genes", ()) or ()
        count_text = "待确认" if counts.get("status") != "computed" else f"上调 {counts.get('up')}；下调 {counts.get('down')}；不显著 {counts.get('not_significant')}"
        top_up_text = "、".join(str(item.get("gene") or "未命名") for item in list(top_up)[:5]) if top_up else "暂无"
        top_down_text = "、".join(str(item.get("gene") or "未命名") for item in list(top_down)[:5]) if top_down else "暂无"
        self._detail_label.setText(
            "详情："
            f"{getattr(result, 'name', '导入差异分析结果')}；"
            "关键列映射 "
            + ("、".join(f"{key}->{value}" for key, value in mapping.items()) if mapping else "待确认")
            + f"；阈值草稿 |log2FC| >= 1 且 p value/FDR <= 0.05；计数：{count_text}；"
            + f"Top up genes：{top_up_text}；Top down genes：{top_down_text}；"
            + "报告可用性：只能写“用户导入的外部分析结果显示”。"
        )
        self._preview.setColumnCount(max(1, len(headers)))
        self._preview.setHorizontalHeaderLabels(headers or ["预览"])
        _fill_table(self._preview, rows)

    def _set_developer_details(self, payload: dict[str, object]) -> None:
        self._developer_details.setPlainText(_json(payload))


class BioinformaticsResultsBrowserWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()
    imported_deg_requested = Signal(object)

    def __init__(
        self,
        *,
        on_continue: Callable[[Path], None] | None = None,
        on_back: Callable[[], None] | None = None,
        on_view_imported_deg: Callable[[Path], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self.setObjectName("bioinformaticsResultsBrowserPage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._formal_deg_review: dict[str, object] = {}
        self._ora_review: dict[str, object] = {}
        self._gsea_review: dict[str, object] = {}
        self._build_ui()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)
        if on_view_imported_deg is not None:
            self.imported_deg_requested.connect(on_view_imported_deg)

    def refresh_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
        self._project_root = _project_root(summary)
        self.refresh_results()

    def refresh_results(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        payload = load_result_index(self._project_root)
        self._render(payload)
        return payload

    def continue_to_report(self) -> None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return
        payload = load_result_index(self._project_root)
        entries = _result_entries_for_display(self._project_root, payload)
        if not entries:
            self._status_label.setText("不能继续：暂无可用于报告草稿的结果。请返回分析任务中心，完成配置或导入明确标记的结果。")
            return
        self.continue_requested.emit(self._project_root)

    def open_imported_deg_browser(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        self.imported_deg_requested.emit(self._project_root)
        self._status_label.setText("已打开导入结果浏览；这里只查看 imported DEG，不运行或生成 DEG。")
        return {"next_page": "imported_deg", "project_root": str(self._project_root)}

    def export_formal_deg_review_tsv(self) -> dict[str, object] | None:
        return self._export_formal_deg_review("tsv")

    def export_formal_deg_review_csv(self) -> dict[str, object] | None:
        return self._export_formal_deg_review("csv")

    def export_ora_review_tsv(self) -> dict[str, object] | None:
        return self._export_ora_review("tsv")

    def export_ora_review_csv(self) -> dict[str, object] | None:
        return self._export_ora_review("csv")

    def export_gsea_review_tsv(self) -> dict[str, object] | None:
        return self._export_gsea_review("tsv")

    def export_gsea_review_csv(self) -> dict[str, object] | None:
        return self._export_gsea_review("csv")

    def generate_gsea_plot_artifact(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        result_id = str(self._gsea_review.get("selected_result_id") or "")
        plot_type = self._gsea_plot_type.currentText() if hasattr(self, "_gsea_plot_type") else "gsea_enrichment_curve_spec"
        result = create_gsea_plot_artifact(self._project_root, result_id=result_id or None, plot_type=plot_type)
        if result.get("status") == "passed":
            self.refresh_results()
            self._status_label.setText(f"已注册 GSEA {plot_type} plot artifact/spec；未生成 PNG/SVG/PDF、完整报告、survival 或临床解释。")
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "GSEA plot gate 未通过"
            self._status_label.setText(f"GSEA plot artifact/spec 未生成：{blockers}")
            self._render_gsea_plot_gate(result)
        return result

    def generate_gsea_report_ready_package(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        result_id = str(self._gsea_review.get("selected_result_id") or "")
        allow_table_only = bool(self._gsea_table_only_report.isChecked()) if hasattr(self, "_gsea_table_only_report") else False
        result = create_gsea_report_ready_package(self._project_root, result_id=result_id or None, allow_table_only_report=allow_table_only)
        if result.get("status") in {"gsea_report_ready_package_created", "imported_derived_gsea_report_package_created"}:
            self.refresh_results()
            imported_note = "；imported-derived 来源已明确标注" if result.get("status") == "imported_derived_gsea_report_package_created" else ""
            self._status_label.setText(
                "已生成 GSEA report-ready package；"
                f"输出位置：{result.get('user_visible_package_path') or result.get('package_path') or ''}{imported_note}；"
                "仅包含 GSEA section，未生成 survival、完整综合报告或临床结论。"
            )
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "GSEA report-ready gate 未通过"
            self._status_label.setText(f"GSEA report package 未生成：{blockers}")
            self._render_gsea_report_gate(result.get("gate", {}) if isinstance(result.get("gate"), dict) else result)
        return result

    def generate_ora_plot_artifact(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        result_id = str(self._ora_review.get("selected_result_id") or "")
        plot_type = self._ora_plot_type.currentText() if hasattr(self, "_ora_plot_type") else "ora_barplot"
        result = create_ora_plot_artifact(self._project_root, result_id=result_id or None, plot_type=plot_type)
        if result.get("status") == "passed":
            self.refresh_results()
            self._status_label.setText(f"已注册 ORA {plot_type} plot artifact/spec；未生成 PNG/SVG/PDF、report-ready、GSEA 或 survival 输出。")
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "ORA plot gate 未通过"
            self._status_label.setText(f"ORA plot artifact/spec 未生成：{blockers}")
            self._render_ora_plot_gate(result)
        return result

    def generate_ora_report_ready_package(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        result_id = str(self._ora_review.get("selected_result_id") or "")
        allow_table_only = bool(self._ora_table_only_report.isChecked()) if hasattr(self, "_ora_table_only_report") else False
        result = create_ora_report_ready_package(self._project_root, result_id=result_id or None, allow_table_only_report=allow_table_only)
        if result.get("status") in {"ora_report_ready_package_created", "imported_derived_ora_report_package_created"}:
            self.refresh_results()
            imported_note = "；imported-derived 来源已明确标注" if result.get("status") == "imported_derived_ora_report_package_created" else ""
            self._status_label.setText(
                "已生成 ORA report package；"
                f"输出位置：{result.get('user_visible_package_path') or result.get('package_path') or ''}{imported_note}；"
                "仅包含 ORA section，未生成 GSEA、survival、完整综合报告或临床结论。"
            )
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "ORA report-ready gate 未通过"
            self._status_label.setText(f"ORA report package 未生成：{blockers}")
            self._render_ora_report_gate(result.get("gate", {}) if isinstance(result.get("gate"), dict) else result)
        return result

    def generate_formal_deg_plot_artifact(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        result_id = str(self._formal_deg_review.get("selected_result_id") or "")
        plot_type = self._formal_deg_plot_type.currentText() if hasattr(self, "_formal_deg_plot_type") else "volcano_plot"
        result = create_formal_deg_plot_artifact(self._project_root, result_id=result_id or None, plot_type=plot_type)
        if result.get("status") == "passed":
            self.refresh_results()
            self._status_label.setText(f"已注册 formal DEG {plot_type} plot artifact；未生成 report-ready、GSEA 或 survival 输出。")
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "formal DEG plot gate 未通过"
            self._status_label.setText(f"formal DEG plot artifact 未生成：{blockers}")
            self._render_formal_deg_plot_gate(result)
        return result

    def generate_formal_deg_report_ready_package(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        result_id = str(self._formal_deg_review.get("selected_result_id") or "")
        allow_table_only = bool(self._formal_deg_table_only_report.isChecked()) if hasattr(self, "_formal_deg_table_only_report") else False
        result = create_formal_deg_report_ready_package(self._project_root, result_id=result_id or None, allow_table_only_report=allow_table_only)
        if result.get("status") == "formal_deg_report_ready_package_created":
            self.refresh_results()
            self._status_label.setText(
                "已生成 formal DEG report-ready package；"
                f"输出位置：{result.get('user_visible_package_path') or result.get('package_path') or ''}；"
                "仅包含 formal DEG section，未生成 GSEA、survival 或临床结论。"
            )
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "formal DEG report-ready gate 未通过"
            self._status_label.setText(f"formal DEG report-ready package 未生成：{blockers}")
            self._render_formal_deg_report_gate(result.get("gate", {}) if isinstance(result.get("gate"), dict) else result)
        return result

    def generate_km_logrank_report_ready_package(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        gate = self._km_report_gate if isinstance(getattr(self, "_km_report_gate", {}), dict) else {}
        result_id = str(gate.get("selected_result_id") or "") or None
        allow_table_only = bool(self._km_table_only_report.isChecked()) if hasattr(self, "_km_table_only_report") else False
        result = create_km_logrank_report_ready_package(self._project_root, result_id=result_id, allow_table_only_report=allow_table_only)
        if result.get("status") == "survival_km_logrank_only_report_ready_package_created":
            self.refresh_results()
            self._status_label.setText(
                "已生成 KM/log-rank section package；"
                f"输出位置：{result.get('user_visible_package_path') or result.get('package_path') or ''}；"
                "仅包含 survival KM/log-rank section，未生成 full integrated report、risk score、预后或治疗建议。"
            )
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "KM/log-rank report-ready gate 未通过"
            self._status_label.setText(f"KM/log-rank section package 未生成：{blockers}")
            self._render_survival_clinical_report_gates(result.get("gate", {}) if isinstance(result.get("gate"), dict) else result, getattr(self, "_cox_report_gate", {}))
        return result

    def generate_cox_report_ready_package(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        gate = self._cox_report_gate if isinstance(getattr(self, "_cox_report_gate", {}), dict) else {}
        result_id = str(gate.get("selected_result_id") or "") or None
        allow_table_only = bool(self._cox_table_only_report.isChecked()) if hasattr(self, "_cox_table_only_report") else False
        result = create_cox_report_ready_package(self._project_root, result_id=result_id, allow_table_only_report=allow_table_only)
        if result.get("status") == "cox_univariate_only_report_ready_package_created":
            self.refresh_results()
            self._status_label.setText(
                "已生成 Cox univariate section package；"
                f"输出位置：{result.get('user_visible_package_path') or result.get('package_path') or ''}；"
                "仅包含 Cox section，未生成 full integrated report、risk score、预后或治疗建议。"
            )
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "Cox report-ready gate 未通过"
            self._status_label.setText(f"Cox section package 未生成：{blockers}")
            self._render_survival_clinical_report_gates(getattr(self, "_km_report_gate", {}), result.get("gate", {}) if isinstance(result.get("gate"), dict) else result)
        return result

    def generate_full_integrated_report_package(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        export_format = self._full_integrated_format.currentText() if hasattr(self, "_full_integrated_format") else "markdown"
        result = create_full_integrated_report_package(self._project_root, export_format=export_format)
        if result.get("status") == "full_integrated_report_package_created":
            self.refresh_results()
            self._status_label.setText(
                "已生成 markdown full integrated report package；"
                f"输出位置：{result.get('user_visible_package_path') or result.get('package_path') or ''}；"
                "仅包含已通过 gate 的统计研究 sections；PDF/DOCX 仍禁用；不包含临床诊断、预后、risk score 或治疗建议。"
            )
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "Full integrated report gate 未通过"
            self._status_label.setText(f"Full integrated report package 未生成：{blockers}")
            gate = result.get("gate", {}) if isinstance(result.get("gate"), dict) else {}
            plan = result.get("package_plan", {}) if isinstance(result.get("package_plan"), dict) else {}
            self._render_full_integrated_report_preview(gate, plan)
        return result

    def generate_full_integrated_docx_rendered_export(self) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        package_path = _latest_full_integrated_markdown_package(self._project_root)
        if package_path is None:
            gate = self._build_full_integrated_docx_rendered_export_ui_gate()
            blockers = "；".join(str(item) for item in gate.get("blockers", []) or []) or "full integrated markdown package missing"
            self._status_label.setText(f"DOCX rendered export 未生成：{blockers}")
            self._render_full_integrated_report_preview(
                evaluate_full_integrated_report_gate(self._project_root),
                build_full_integrated_report_package_plan(self._project_root, gate=evaluate_full_integrated_report_gate(self._project_root), export_format=self._full_integrated_format.currentText()),
                gate,
            )
            return gate
        result = create_full_integrated_docx_rendered_export(package_path)
        if result.get("status") == "full_integrated_docx_rendered_export_created":
            self.refresh_results()
            self._status_label.setText(
                "已生成 DOCX rendered export；"
                f"输出位置：{result.get('output_path') or ''}；"
                "这是 full integrated markdown package 的渲染副本，不写入 result index，不生成 PDF，不包含临床诊断、预后、risk score 或治疗建议。"
            )
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "DOCX renderer gate 未通过"
            self._status_label.setText(f"DOCX rendered export 未生成：{blockers}")
            gate = evaluate_full_integrated_report_gate(self._project_root)
            plan = build_full_integrated_report_package_plan(
                self._project_root,
                gate=gate,
                export_format=self._full_integrated_format.currentText() if hasattr(self, "_full_integrated_format") else "markdown",
            )
            self._render_full_integrated_report_preview(gate, plan, result.get("preflight_gate", {}) if isinstance(result.get("preflight_gate"), dict) else {})
        return result

    def _export_formal_deg_review(self, file_format: str) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        result_id = str(self._formal_deg_review.get("selected_result_id") or "")
        result = export_formal_deg_review_table(self._project_root, result_id=result_id, file_format=file_format)
        if result.get("status") == "passed":
            self._status_label.setText(f"已导出 formal DEG {file_format.upper()} 表格；未生成 report-ready、plot、GSEA 或 survival 输出。")
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "没有可导出的 formal DEG result"
            self._status_label.setText(f"formal DEG 表格未导出：{blockers}")
        return result

    def _export_ora_review(self, file_format: str) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        result_id = str(self._ora_review.get("selected_result_id") or "")
        result = export_ora_review_table(self._project_root, result_id=result_id, file_format=file_format)
        if result.get("status") == "passed":
            self._status_label.setText(f"已导出 ORA {file_format.upper()} 表格；未生成 report-ready、plot、GSEA 或 survival 输出。")
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "没有可导出的 ORA result"
            self._status_label.setText(f"ORA 表格未导出：{blockers}")
        return result

    def _export_gsea_review(self, file_format: str) -> dict[str, object] | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        result_id = str(self._gsea_review.get("selected_result_id") or "")
        result = export_gsea_review_table(self._project_root, result_id=result_id, file_format=file_format)
        if result.get("status") == "passed":
            self._status_label.setText(f"已导出 GSEA {file_format.upper()} 表格；未生成 plot、report-ready、survival 或临床解释。")
        else:
            blockers = "；".join(str(item) for item in result.get("blockers", []) or []) or "没有可导出的 controlled GSEA result"
            self._status_label.setText(f"GSEA 表格未导出：{blockers}")
        return result

    def status_message(self) -> str:
        return self._status_label.text()

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("结果浏览", "查看导入结果、测试级结果和任务记录，确认哪些内容可进入报告草稿。", back_text="返回分析任务中心", back_signal=self.back_requested))
        self._status_label = _status_label("暂无结果，请先在分析任务中心创建配置草稿，或导入明确标记的结果。")
        root.addWidget(self._status_label)

        summary_card, summary_layout = _card("当前结果状态")
        self._result_summary_label = _muted("当前结果：待检查。")
        self._result_summary_label.setObjectName("resultsSourceSummary")
        self._result_report_label = _muted("报告适用性：暂无可用于报告草稿的结果。")
        self._result_report_label.setObjectName("resultsReportReadiness")
        self._result_next_step_label = _muted("下一步建议：返回分析任务中心。")
        self._result_next_step_label.setObjectName("resultsNextStep")
        summary_layout.addWidget(self._result_summary_label)
        summary_layout.addWidget(self._result_report_label)
        summary_layout.addWidget(self._result_next_step_label)
        root.addWidget(summary_card)

        actions = QHBoxLayout()
        actions.addWidget(_button("刷新结果", "secondaryButton", self.refresh_results))
        actions.addWidget(_button("导入结果浏览", "secondaryButton", self.open_imported_deg_browser))
        actions.addWidget(_button("查看报告草稿", "primaryButton", self.continue_to_report))
        actions.addStretch(1)
        root.addLayout(actions)
        self._results = _table(["结果名称", "结果类型", "来源", "状态", "可用于报告", "生成时间", "简短说明", "查看详情"])
        self._results.setObjectName("resultsUserTable")
        root.addWidget(self._results)
        _set_table_widths(self._results, [170, 110, 170, 120, 120, 160, 280, 100])
        self._results.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)

        review_card, review_layout = _card("Formal DEG result review")
        self._formal_deg_guard_label = _muted("Formal DEG review shows statistical analysis results only. It is not a clinical conclusion or treatment recommendation.")
        self._formal_deg_guard_label.setObjectName("formalDegReviewGuard")
        review_layout.addWidget(self._formal_deg_guard_label)
        controls = QHBoxLayout()
        self._formal_deg_sort_input = QComboBox()
        self._formal_deg_sort_input.setObjectName("formalDegReviewSort")
        self._formal_deg_sort_input.addItems(["adjusted_p_value", "p_value", "log2_fold_change", "significance_label", "input_order"])
        self._formal_deg_sort_input.currentIndexChanged.connect(lambda _index: self.refresh_results())
        self._formal_deg_filter_input = QComboBox()
        self._formal_deg_filter_input.setObjectName("formalDegReviewFilter")
        self._formal_deg_filter_input.addItems(["all", "significant", "up", "down", "not_significant"])
        self._formal_deg_filter_input.currentIndexChanged.connect(lambda _index: self.refresh_results())
        controls.addWidget(QLabel("Sort"))
        controls.addWidget(self._formal_deg_sort_input)
        controls.addWidget(QLabel("Filter"))
        controls.addWidget(self._formal_deg_filter_input)
        controls.addWidget(_button("导出 DEG TSV", "secondaryButton", self.export_formal_deg_review_tsv))
        controls.addWidget(_button("导出 DEG CSV", "secondaryButton", self.export_formal_deg_review_csv))
        controls.addStretch(1)
        review_layout.addLayout(controls)
        plot_controls = QHBoxLayout()
        self._formal_deg_plot_type = QComboBox()
        self._formal_deg_plot_type.setObjectName("formalDegPlotType")
        self._formal_deg_plot_type.addItems(["volcano_plot", "deg_heatmap"])
        plot_controls.addWidget(QLabel("Plot artifact"))
        plot_controls.addWidget(self._formal_deg_plot_type)
        self._formal_deg_plot_button = _button("生成 formal DEG plot artifact", "secondaryButton", self.generate_formal_deg_plot_artifact)
        self._formal_deg_plot_button.setObjectName("formalDegPlotButton")
        plot_controls.addWidget(self._formal_deg_plot_button)
        self._formal_deg_plot_status = _muted("Formal plot artifact 只接受 formal_computed_result DEG source；不生成 report-ready。")
        self._formal_deg_plot_status.setObjectName("formalDegPlotStatus")
        plot_controls.addWidget(self._formal_deg_plot_status)
        plot_controls.addStretch(1)
        review_layout.addLayout(plot_controls)
        report_controls = QHBoxLayout()
        self._formal_deg_table_only_report = QCheckBox("允许无图 table-only report mode")
        self._formal_deg_table_only_report.setObjectName("formalDegTableOnlyReportMode")
        self._formal_deg_table_only_report.stateChanged.connect(lambda _state: self.refresh_results())
        self._formal_deg_report_button = _button("生成 formal DEG report-ready package", "secondaryButton", self.generate_formal_deg_report_ready_package)
        self._formal_deg_report_button.setObjectName("formalDegReportReadyButton")
        self._formal_deg_report_status = _muted("Formal DEG report-ready gate 需要完整 result index、未过期 confirmation、passed dependency/table validation 和 formal plot artifact；无图 table-only 模式需显式勾选，且不表示 volcano/heatmap 已生成。")
        self._formal_deg_report_status.setObjectName("formalDegReportReadyStatus")
        report_controls.addWidget(self._formal_deg_table_only_report)
        report_controls.addWidget(self._formal_deg_report_button)
        report_controls.addWidget(self._formal_deg_report_status)
        report_controls.addStretch(1)
        review_layout.addLayout(report_controls)
        self._formal_deg_summary_label = _muted("Formal DEG summary：暂无 formal computed DEG result。")
        self._formal_deg_summary_label.setObjectName("formalDegReviewSummary")
        self._formal_deg_downstream_label = _muted("Plot/report disabled：等待 B9.6 plot artifact / B9.7 report-ready gate。")
        self._formal_deg_downstream_label.setObjectName("formalDegReviewDownstream")
        review_layout.addWidget(self._formal_deg_summary_label)
        review_layout.addWidget(self._formal_deg_downstream_label)
        self._formal_deg_table = _table(["feature_id", "gene_symbol", "log2FC", "p-value", "FDR", "significance_label"])
        self._formal_deg_table.setObjectName("formalDegReviewTable")
        review_layout.addWidget(self._formal_deg_table)
        _set_table_widths(self._formal_deg_table, [160, 160, 110, 110, 110, 160])
        self._formal_deg_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._formal_deg_provenance = _table(["Provenance", "Value"])
        self._formal_deg_provenance.setObjectName("formalDegReviewProvenanceTable")
        review_layout.addWidget(self._formal_deg_provenance)
        _set_table_widths(self._formal_deg_provenance, [190, 620])
        self._formal_deg_provenance.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        root.addWidget(review_card)

        ora_card, ora_layout = _card("Controlled ORA result review")
        self._ora_guard_label = _muted("ORA is pathway over-representation analysis based on selected DEG genes; it does not prove pathway activation/inhibition and is not clinical interpretation.")
        self._ora_guard_label.setObjectName("oraReviewGuard")
        ora_layout.addWidget(self._ora_guard_label)
        ora_controls = QHBoxLayout()
        self._ora_sort_input = QComboBox()
        self._ora_sort_input.setObjectName("oraReviewSort")
        self._ora_sort_input.addItems(["adjusted_p_value", "p_value", "enrichment_ratio", "overlap_count", "significance_label", "input_order"])
        self._ora_sort_input.currentIndexChanged.connect(lambda _index: self.refresh_results())
        self._ora_filter_input = QComboBox()
        self._ora_filter_input.setObjectName("oraReviewFilter")
        self._ora_filter_input.addItems(["all", "significant", "not_significant"])
        self._ora_filter_input.currentIndexChanged.connect(lambda _index: self.refresh_results())
        ora_controls.addWidget(QLabel("Sort"))
        ora_controls.addWidget(self._ora_sort_input)
        ora_controls.addWidget(QLabel("Filter"))
        ora_controls.addWidget(self._ora_filter_input)
        ora_controls.addWidget(_button("导出 ORA TSV", "secondaryButton", self.export_ora_review_tsv))
        ora_controls.addWidget(_button("导出 ORA CSV", "secondaryButton", self.export_ora_review_csv))
        ora_controls.addStretch(1)
        ora_layout.addLayout(ora_controls)
        ora_plot_controls = QHBoxLayout()
        self._ora_plot_type = QComboBox()
        self._ora_plot_type.setObjectName("oraPlotType")
        self._ora_plot_type.addItems(["ora_barplot", "ora_dotplot"])
        ora_plot_controls.addWidget(QLabel("ORA plot spec"))
        ora_plot_controls.addWidget(self._ora_plot_type)
        self._ora_plot_button = _button("生成 ORA plot artifact/spec", "secondaryButton", self.generate_ora_plot_artifact)
        self._ora_plot_button.setObjectName("oraPlotButton")
        ora_plot_controls.addWidget(self._ora_plot_button)
        self._ora_plot_status = _muted("ORA plot artifact 当前仅生成 spec，不渲染 PNG/SVG/PDF，不进入 report-ready。")
        self._ora_plot_status.setObjectName("oraPlotStatus")
        ora_plot_controls.addWidget(self._ora_plot_status)
        ora_plot_controls.addStretch(1)
        ora_layout.addLayout(ora_plot_controls)
        ora_report_controls = QHBoxLayout()
        self._ora_table_only_report = QCheckBox("允许无图 ORA table-only report mode")
        self._ora_table_only_report.setObjectName("oraTableOnlyReportMode")
        self._ora_table_only_report.stateChanged.connect(lambda _state: self.refresh_results())
        self._ora_report_button = _button("生成 ORA report package", "secondaryButton", self.generate_ora_report_ready_package)
        self._ora_report_button.setObjectName("oraReportReadyButton")
        self._ora_report_status = _muted("ORA report-ready gate 需要完整 ORA result index、passed dependency/table/gene set/task log 和 ORA plot artifact；无图 ORA table-only 模式需显式勾选。")
        self._ora_report_status.setObjectName("oraReportReadyStatus")
        ora_report_controls.addWidget(self._ora_table_only_report)
        ora_report_controls.addWidget(self._ora_report_button)
        ora_report_controls.addWidget(self._ora_report_status)
        ora_report_controls.addStretch(1)
        ora_layout.addLayout(ora_report_controls)
        self._ora_summary_label = _muted("ORA summary：暂无 controlled ORA result。")
        self._ora_summary_label.setObjectName("oraReviewSummary")
        self._ora_downstream_label = _muted("ORA plot waits for ORA result gate；report-ready/GSEA/survival 禁用。")
        self._ora_downstream_label.setObjectName("oraReviewDownstream")
        ora_layout.addWidget(self._ora_summary_label)
        ora_layout.addWidget(self._ora_downstream_label)
        self._ora_table = _table(["term_id", "term_name", "overlap", "gene_set_size", "selected", "ratio", "p-value", "FDR", "genes", "significance"])
        self._ora_table.setObjectName("oraReviewTable")
        ora_layout.addWidget(self._ora_table)
        _set_table_widths(self._ora_table, [130, 220, 90, 110, 100, 90, 110, 110, 240, 130])
        self._ora_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)
        self._ora_provenance = _table(["Provenance", "Value"])
        self._ora_provenance.setObjectName("oraReviewProvenanceTable")
        ora_layout.addWidget(self._ora_provenance)
        _set_table_widths(self._ora_provenance, [190, 620])
        self._ora_provenance.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        root.addWidget(ora_card)

        gsea_card, gsea_layout = _card("Controlled preranked GSEA result review")
        self._gsea_guard_label = _muted("Preranked GSEA review shows statistical enrichment only from a DEG-derived rank metric and local gene sets; it is not pathway activation proof or clinical interpretation.")
        self._gsea_guard_label.setObjectName("gseaReviewGuard")
        gsea_layout.addWidget(self._gsea_guard_label)
        gsea_controls = QHBoxLayout()
        self._gsea_sort_input = QComboBox()
        self._gsea_sort_input.setObjectName("gseaReviewSort")
        self._gsea_sort_input.addItems(["adjusted_p_value", "p_value", "normalized_enrichment_score", "enrichment_score", "significance_label", "input_order"])
        self._gsea_sort_input.currentIndexChanged.connect(lambda _index: self.refresh_results())
        self._gsea_filter_input = QComboBox()
        self._gsea_filter_input.setObjectName("gseaReviewFilter")
        self._gsea_filter_input.addItems(["all", "significant", "significant_positive", "significant_negative", "not_significant"])
        self._gsea_filter_input.currentIndexChanged.connect(lambda _index: self.refresh_results())
        gsea_controls.addWidget(QLabel("Sort"))
        gsea_controls.addWidget(self._gsea_sort_input)
        gsea_controls.addWidget(QLabel("Filter"))
        gsea_controls.addWidget(self._gsea_filter_input)
        gsea_controls.addWidget(_button("导出 GSEA TSV", "secondaryButton", self.export_gsea_review_tsv))
        gsea_controls.addWidget(_button("导出 GSEA CSV", "secondaryButton", self.export_gsea_review_csv))
        gsea_controls.addStretch(1)
        gsea_layout.addLayout(gsea_controls)
        gsea_plot_controls = QHBoxLayout()
        self._gsea_plot_type = QComboBox()
        self._gsea_plot_type.setObjectName("gseaPlotType")
        self._gsea_plot_type.addItems(["gsea_enrichment_curve_spec", "gsea_nes_barplot_spec"])
        gsea_plot_controls.addWidget(QLabel("GSEA plot spec"))
        gsea_plot_controls.addWidget(self._gsea_plot_type)
        self._gsea_plot_button = _button("生成 GSEA plot artifact/spec", "secondaryButton", self.generate_gsea_plot_artifact)
        self._gsea_plot_button.setObjectName("gseaPlotButton")
        gsea_plot_controls.addWidget(self._gsea_plot_button)
        self._gsea_plot_status = _muted("GSEA plot artifact 当前仅生成 spec，不渲染 PNG/SVG/PDF，不进入完整报告。")
        self._gsea_plot_status.setObjectName("gseaPlotStatus")
        gsea_plot_controls.addWidget(self._gsea_plot_status)
        gsea_plot_controls.addStretch(1)
        gsea_layout.addLayout(gsea_plot_controls)
        gsea_report_controls = QHBoxLayout()
        self._gsea_table_only_report = QCheckBox("允许无图 GSEA table-only report mode")
        self._gsea_table_only_report.setObjectName("gseaTableOnlyReportMode")
        self._gsea_table_only_report.stateChanged.connect(lambda _state: self.refresh_results())
        self._gsea_report_button = _button("生成 GSEA report package", "secondaryButton", self.generate_gsea_report_ready_package)
        self._gsea_report_button.setObjectName("gseaReportReadyButton")
        self._gsea_report_status = _muted("GSEA report-ready gate 需要完整 GSEA result index、passed dependency/table/gene set/task log 和 GSEA plot artifact；无图 GSEA table-only 模式需显式勾选。")
        self._gsea_report_status.setObjectName("gseaReportReadyStatus")
        gsea_report_controls.addWidget(self._gsea_table_only_report)
        gsea_report_controls.addWidget(self._gsea_report_button)
        gsea_report_controls.addWidget(self._gsea_report_status)
        gsea_report_controls.addStretch(1)
        gsea_layout.addLayout(gsea_report_controls)
        self._gsea_summary_label = _muted("GSEA summary：暂无 controlled preranked GSEA result。")
        self._gsea_summary_label.setObjectName("gseaReviewSummary")
        self._gsea_downstream_label = _muted("GSEA plot/report-ready disabled：等待 B11.3 plot artifact / 后续 report gate。")
        self._gsea_downstream_label.setObjectName("gseaReviewDownstream")
        gsea_layout.addWidget(self._gsea_summary_label)
        gsea_layout.addWidget(self._gsea_downstream_label)
        self._gsea_table = _table(["term_id", "term_name", "set_size", "overlap", "ES", "NES", "p-value", "FDR", "leading edge", "rank metric", "significance"])
        self._gsea_table.setObjectName("gseaReviewTable")
        gsea_layout.addWidget(self._gsea_table)
        _set_table_widths(self._gsea_table, [130, 220, 90, 90, 90, 90, 110, 110, 240, 160, 150])
        self._gsea_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)
        self._gsea_provenance = _table(["Provenance", "Value"])
        self._gsea_provenance.setObjectName("gseaReviewProvenanceTable")
        gsea_layout.addWidget(self._gsea_provenance)
        _set_table_widths(self._gsea_provenance, [190, 620])
        self._gsea_provenance.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        root.addWidget(gsea_card)

        survival_report_card, survival_report_layout = _card("Survival / clinical section packages")
        survival_report_layout.addWidget(_muted("KM/log-rank 和 Cox 只允许生成 section-only package；这不是 full integrated report，也不包含临床诊断、预后、risk score 或治疗建议。"))
        survival_report_controls = QHBoxLayout()
        self._km_table_only_report = QCheckBox("允许无图 KM table-only section")
        self._km_table_only_report.setObjectName("kmTableOnlyReportMode")
        self._km_table_only_report.stateChanged.connect(lambda _state: self.refresh_results())
        self._km_report_button = _button("生成 KM/log-rank section package", "secondaryButton", self.generate_km_logrank_report_ready_package)
        self._km_report_button.setObjectName("kmReportReadyButton")
        self._km_report_status = _muted("KM/log-rank section gate 需要 formal KM result、passed validation/dependency、task log、结果表和 KM plot artifact；无图 table-only 模式需显式勾选。")
        self._km_report_status.setObjectName("kmReportReadyStatus")
        survival_report_controls.addWidget(self._km_table_only_report)
        survival_report_controls.addWidget(self._km_report_button)
        survival_report_controls.addWidget(self._km_report_status)
        survival_report_controls.addStretch(1)
        survival_report_layout.addLayout(survival_report_controls)
        cox_report_controls = QHBoxLayout()
        self._cox_table_only_report = QCheckBox("允许无图 Cox table-only section")
        self._cox_table_only_report.setObjectName("coxTableOnlyReportMode")
        self._cox_table_only_report.stateChanged.connect(lambda _state: self.refresh_results())
        self._cox_report_button = _button("生成 Cox section package", "secondaryButton", self.generate_cox_report_ready_package)
        self._cox_report_button.setObjectName("coxReportReadyButton")
        self._cox_report_status = _muted("Cox section gate 只接受 formal Cox univariate result；无图 table-only 模式需显式勾选。")
        self._cox_report_status.setObjectName("coxReportReadyStatus")
        cox_report_controls.addWidget(self._cox_table_only_report)
        cox_report_controls.addWidget(self._cox_report_button)
        cox_report_controls.addWidget(self._cox_report_status)
        cox_report_controls.addStretch(1)
        survival_report_layout.addLayout(cox_report_controls)
        self._survival_clinical_report_gate = _table(["Gate", "状态", "Source", "Package", "Blockers", "Warnings"])
        self._survival_clinical_report_gate.setObjectName("survivalClinicalReportGateTable")
        survival_report_layout.addWidget(self._survival_clinical_report_gate)
        _set_table_widths(self._survival_clinical_report_gate, [190, 160, 150, 170, 340, 260])
        self._survival_clinical_report_gate.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        root.addWidget(survival_report_card)

        gate_card, gate_layout = _card("Result semantics / plot / report gates")
        gate_layout.addWidget(_muted("结果浏览只展示 result index 语义和 eligibility；不会把 testing/imported/preflight 输出升级为 formal result。"))
        self._gate_preview = _table(["Gate", "状态", "依据", "Blockers", "Warnings"])
        self._gate_preview.setObjectName("resultsGatePreviewTable")
        gate_layout.addWidget(self._gate_preview)
        root.addWidget(gate_card)
        _set_table_widths(self._gate_preview, [170, 170, 230, 320, 300])
        self._gate_preview.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        integrated_card, integrated_layout = _card("Full integrated report preview")
        integrated_layout.addWidget(_muted("Full integrated report 需要 DEG、ORA、GSEA、KM 和 Cox section 全部通过 gate；当前只支持 markdown package，PDF/DOCX 保持 renderer-disabled。"))
        integrated_controls = QHBoxLayout()
        self._full_integrated_format = QComboBox()
        self._full_integrated_format.setObjectName("fullIntegratedReportFormat")
        self._full_integrated_format.addItems(["markdown", "pdf", "docx"])
        self._full_integrated_format.currentIndexChanged.connect(lambda _index: self.refresh_results())
        integrated_controls.addWidget(QLabel("Format"))
        integrated_controls.addWidget(self._full_integrated_format)
        self._full_integrated_button = _button("生成 full integrated report package", "secondaryButton", self.generate_full_integrated_report_package)
        self._full_integrated_button.setObjectName("fullIntegratedReportButton")
        integrated_controls.addWidget(self._full_integrated_button)
        self._full_integrated_docx_button = _button("生成 DOCX rendered export", "secondaryButton", self.generate_full_integrated_docx_rendered_export)
        self._full_integrated_docx_button.setObjectName("fullIntegratedDocxRenderedExportButton")
        integrated_controls.addWidget(self._full_integrated_docx_button)
        self._full_integrated_status = _muted("Full integrated report gate 尚未通过；当前显示 gate/package plan、renderer disabled reason 和 section provenance。")
        self._full_integrated_status.setObjectName("fullIntegratedReportStatus")
        integrated_controls.addWidget(self._full_integrated_status)
        integrated_controls.addStretch(1)
        integrated_layout.addLayout(integrated_controls)
        self._full_integrated_plan = _table(["Plan", "Value"])
        self._full_integrated_plan.setObjectName("fullIntegratedReportPlanTable")
        integrated_layout.addWidget(self._full_integrated_plan)
        _set_table_widths(self._full_integrated_plan, [260, 660])
        self._full_integrated_plan.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._full_integrated_sections = _table(["Section", "Result", "Semantics", "Validation", "Report gate", "Plot", "Package", "Prerequisite", "Blockers"])
        self._full_integrated_sections.setObjectName("fullIntegratedReportSectionTable")
        integrated_layout.addWidget(self._full_integrated_sections)
        _set_table_widths(self._full_integrated_sections, [150, 160, 170, 110, 150, 150, 150, 140, 340])
        self._full_integrated_sections.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)
        root.addWidget(integrated_card)

        developer_card, developer_layout = _card("开发者诊断")
        developer_actions = QHBoxLayout()
        developer_actions.addWidget(_button("展开技术细节", "secondaryButton", lambda: _toggle_details(self._details)))
        developer_actions.addWidget(_button("打开结果文件夹", "secondaryButton", lambda: _open_path(self._project_root / "results" if self._project_root else None)))
        developer_actions.addWidget(_button("打开参数 JSON", "secondaryButton", lambda: _open_path(self._project_root / "manifests/result_manager.json" if self._project_root else None)))
        developer_actions.addStretch(1)
        developer_layout.addLayout(developer_actions)
        self._details = _text_preview(130)
        self._details.setObjectName("resultsDeveloperDiagnostics")
        self._details.setVisible(False)
        developer_layout.addWidget(self._details)
        root.addWidget(developer_card)
        root.addWidget(_button("继续：报告查看", "primaryButton", self.continue_to_report), alignment=Qt.AlignLeft)

    def _render(self, payload: dict[str, object]) -> None:
        entries = _result_entries_for_display(self._project_root, payload)
        records = load_task_records(self._project_root) if self._project_root else []
        warnings = [str(item) for item in payload.get("warnings", []) or []]
        if not entries and not records:
            self._status_label.setText("暂无结果，请先在分析任务中心创建配置草稿，或导入明确标记的结果。")
        else:
            self._status_label.setText(f"结果浏览：{len(entries)} 个可查看结果，{len(records)} 个配置/流程记录，{len(warnings)} 条提示。")
        self._result_summary_label.setText(_results_page_source_summary(entries, records))
        self._result_report_label.setText(_results_page_report_summary(entries, records))
        self._result_next_step_label.setText(_results_page_next_step(entries, records))
        _fill_table(
            self._results,
            _results_user_rows(self._project_root, entries, records),
        )
        review = build_formal_deg_result_review(
            self._project_root,
            sort_by=self._formal_deg_sort_input.currentText(),
            significance_filter=self._formal_deg_filter_input.currentText(),
        ) if self._project_root else {}
        self._formal_deg_review = review
        self._render_formal_deg_review(review)
        ora_review = build_ora_result_review(
            self._project_root,
            sort_by=self._ora_sort_input.currentText(),
            significance_filter=self._ora_filter_input.currentText(),
        ) if self._project_root else {}
        self._ora_review = ora_review
        self._render_ora_review(ora_review)
        gsea_review = build_gsea_result_review(
            self._project_root,
            sort_by=self._gsea_sort_input.currentText(),
            significance_filter=self._gsea_filter_input.currentText(),
        ) if self._project_root else {}
        self._gsea_review = gsea_review
        self._render_gsea_review(gsea_review)
        gsea_plot_gate = build_gsea_plot_gate(
            self._project_root,
            result_id=str(gsea_review.get("selected_result_id") or "") or None,
            plot_type=self._gsea_plot_type.currentText(),
        ) if self._project_root else {}
        self._render_gsea_plot_gate(gsea_plot_gate)
        gsea_report_gate = evaluate_gsea_report_ready_gate(
            self._project_root,
            result_id=str(gsea_review.get("selected_result_id") or "") or None,
            allow_table_only_report=bool(self._gsea_table_only_report.isChecked()),
        ) if self._project_root else {}
        self._render_gsea_report_gate(gsea_report_gate)
        ora_plot_gate = build_ora_plot_gate(
            self._project_root,
            result_id=str(ora_review.get("selected_result_id") or "") or None,
            plot_type=self._ora_plot_type.currentText(),
        ) if self._project_root else {}
        self._render_ora_plot_gate(ora_plot_gate)
        ora_report_gate = evaluate_ora_report_ready_gate(
            self._project_root,
            result_id=str(ora_review.get("selected_result_id") or "") or None,
            allow_table_only_report=bool(self._ora_table_only_report.isChecked()),
        ) if self._project_root else {}
        self._render_ora_report_gate(ora_report_gate)
        plot_gate = build_formal_deg_plot_gate(
            self._project_root,
            result_id=str(review.get("selected_result_id") or "") or None,
            plot_type=self._formal_deg_plot_type.currentText(),
        ) if self._project_root else {}
        self._render_formal_deg_plot_gate(plot_gate)
        report_gate = evaluate_formal_deg_report_ready_gate(
            self._project_root,
            result_id=str(review.get("selected_result_id") or "") or None,
            allow_table_only_report=bool(self._formal_deg_table_only_report.isChecked()),
        ) if self._project_root else {}
        self._render_formal_deg_report_gate(report_gate)
        km_report_gate = evaluate_km_logrank_report_ready_gate(
            self._project_root,
            allow_table_only_report=bool(self._km_table_only_report.isChecked()),
        ) if self._project_root else {}
        cox_report_gate = evaluate_cox_report_ready_gate(
            self._project_root,
            allow_table_only_report=bool(self._cox_table_only_report.isChecked()),
        ) if self._project_root else {}
        self._km_report_gate = km_report_gate
        self._cox_report_gate = cox_report_gate
        self._render_survival_clinical_report_gates(km_report_gate, cox_report_gate)
        integrated_gate = evaluate_full_integrated_report_gate(self._project_root) if self._project_root else {}
        integrated_plan = build_full_integrated_report_package_plan(
            self._project_root,
            gate=integrated_gate,
            export_format=self._full_integrated_format.currentText() if hasattr(self, "_full_integrated_format") else "markdown",
        ) if self._project_root else {}
        docx_gate = self._build_full_integrated_docx_rendered_export_ui_gate()
        self._render_full_integrated_report_preview(integrated_gate, integrated_plan, docx_gate)
        analysis_state = build_analysis_center_state(self._project_root) if self._project_root else {}
        _fill_table(self._gate_preview, _analysis_ui_gate_rows([*(analysis_state.get("gate_rows", []) or []), *(analysis_state.get("ora_gate_rows", []) or []), *(analysis_state.get("gsea_gate_rows", []) or []), *(analysis_state.get("survival_clinical_report_gate_rows", []) or [])]))
        self._details.setPlainText(_json({"result_index": payload, "display_entries": entries, "task_records": records, "warnings": warnings, "analysis_center_state": analysis_state, "ora_review": ora_review, "gsea_review": gsea_review, "gsea_plot_gate": gsea_plot_gate, "gsea_report_gate": gsea_report_gate, "km_logrank_report_gate": km_report_gate, "cox_report_gate": cox_report_gate, "full_integrated_report_gate": integrated_gate, "full_integrated_report_package_plan": integrated_plan, "full_integrated_docx_rendered_export_gate": docx_gate}))

    def _render_formal_deg_review(self, review: dict[str, object]) -> None:
        summary = review.get("summary") if isinstance(review.get("summary"), dict) else {}
        provenance = review.get("provenance") if isinstance(review.get("provenance"), dict) else {}
        downstream = review.get("disabled_downstream") if isinstance(review.get("disabled_downstream"), dict) else {}
        rows = [row for row in review.get("rows", []) or [] if isinstance(row, dict)]
        if review.get("status") != "passed":
            self._formal_deg_summary_label.setText("Formal DEG summary：暂无 formal_computed_result DEG；imported/testing/exploratory/preflight 不会混入此审阅区。")
            _fill_table(self._formal_deg_table, [])
            _fill_table(self._formal_deg_provenance, [["Status", "; ".join(str(item) for item in review.get("blockers", []) or []) or "blocked"]])
            return
        thresholds = summary.get("thresholds") if isinstance(summary.get("thresholds"), dict) else {}
        sample_counts = summary.get("sample_counts") if isinstance(summary.get("sample_counts"), dict) else {}
        deps = summary.get("dependency_versions") if isinstance(summary.get("dependency_versions"), dict) else {}
        self._formal_deg_summary_label.setText(
            "Formal DEG summary："
            f"genes={summary.get('total_gene_count', 0)}；up={summary.get('significant_up_count', 0)}；down={summary.get('significant_down_count', 0)}；"
            f"method={summary.get('method', '')}；threshold log2FC={thresholds.get('log2fc_threshold', '')}, p={thresholds.get('p_value_threshold', '')}, FDR={thresholds.get('fdr_threshold', '')}；"
            f"samples case={sample_counts.get('case', 0)}, control={sample_counts.get('control', 0)}；"
            f"deps numpy={deps.get('numpy', '')}, pandas={deps.get('pandas', '')}, scipy={deps.get('scipy', '')}, statsmodels={deps.get('statsmodels', '')}."
        )
        self._formal_deg_downstream_label.setText(
            "；".join(str(value) for value in downstream.values())
            if downstream
            else "等待 B9.6 plot artifact / B9.7 report-ready gate。"
        )
        _fill_table(
            self._formal_deg_table,
            [
                [
                    row.get("feature_id", ""),
                    row.get("gene_symbol", ""),
                    row.get("log2_fold_change", ""),
                    row.get("p_value", ""),
                    row.get("adjusted_p_value", ""),
                    row.get("significance_label", ""),
                ]
                for row in rows[:200]
            ],
        )
        _fill_table(
            self._formal_deg_provenance,
            [
                ["input_package_id", provenance.get("input_package_id", "")],
                ["parameter_confirmation", provenance.get("parameter_confirmation", "")],
                ["dependency_snapshot", "present" if provenance.get("dependency_snapshot_present") else "missing"],
                ["task_run_log", provenance.get("task_run_log", "")],
                ["result_index_path", provenance.get("result_index_path", "")],
                ["result_table_path", provenance.get("result_table_path", "")],
                ["plot_artifacts", provenance.get("plot_artifacts", [])],
                ["report_artifacts", provenance.get("report_artifacts", [])],
                ["report_ready_eligible", provenance.get("report_ready_eligible", False)],
            ],
        )

    def _render_formal_deg_plot_gate(self, gate: dict[str, object]) -> None:
        if not hasattr(self, "_formal_deg_plot_status"):
            return
        blockers = [str(item) for item in gate.get("blockers", []) or []]
        warnings = [str(item) for item in gate.get("warnings", []) or []]
        if gate.get("status") == "passed":
            existing = gate.get("existing_plot_artifacts", []) if isinstance(gate.get("existing_plot_artifacts"), list) else []
            self._formal_deg_plot_button.setEnabled(True)
            self._formal_deg_plot_status.setText(
                f"Formal DEG plot gate passed；source={gate.get('selected_result_id', '')}；existing artifacts={len(existing)}；"
                "inherits formal_computed_result semantics；report-ready remains disabled."
            )
        else:
            self._formal_deg_plot_button.setEnabled(False)
            reason = "；".join(blockers) or "formal DEG plot gate 未通过"
            if warnings:
                reason = f"{reason}；warnings={'；'.join(warnings)}"
            self._formal_deg_plot_status.setText(f"Formal DEG plot disabled：{reason}")

    def _render_formal_deg_report_gate(self, gate: dict[str, object]) -> None:
        if not hasattr(self, "_formal_deg_report_status"):
            return
        blockers = [str(item) for item in gate.get("blockers", []) or []]
        warnings = [str(item) for item in gate.get("warnings", []) or []]
        if gate.get("status") == "eligible_for_formal_deg_report_ready":
            self._formal_deg_report_button.setEnabled(True)
            self._formal_deg_report_status.setText(
                f"Formal DEG report-ready gate passed；source={gate.get('selected_result_id', '')}；"
                f"confirmation={gate.get('confirmation_created_at', '')}；deps={gate.get('dependency_versions', {})}；"
                "package scope=formal DEG only；GSEA/survival/clinical conclusions disabled."
            )
        else:
            self._formal_deg_report_button.setEnabled(False)
            reason = "；".join(blockers) or "formal DEG report-ready gate 未通过"
            if warnings:
                reason = f"{reason}；warnings={'；'.join(warnings)}"
            self._formal_deg_report_status.setText(f"Formal DEG report-ready disabled：{reason}")

    def _render_survival_clinical_report_gates(self, km_gate: dict[str, object], cox_gate: dict[str, object]) -> None:
        if not hasattr(self, "_survival_clinical_report_gate"):
            return
        self._render_single_survival_clinical_report_gate(
            km_gate,
            button=self._km_report_button,
            label=self._km_report_status,
            eligible_status="eligible_for_km_logrank_report_ready",
            display_name="KM/log-rank section",
        )
        self._render_single_survival_clinical_report_gate(
            cox_gate,
            button=self._cox_report_button,
            label=self._cox_report_status,
            eligible_status="eligible_for_cox_report_ready",
            display_name="Cox section",
        )
        _fill_table(
            self._survival_clinical_report_gate,
            [
                _survival_clinical_report_gate_row("KM/log-rank section report-ready", km_gate),
                _survival_clinical_report_gate_row("Cox section report-ready", cox_gate),
            ],
        )

    def _render_single_survival_clinical_report_gate(
        self,
        gate: dict[str, object],
        *,
        button: QPushButton,
        label: QLabel,
        eligible_status: str,
        display_name: str,
    ) -> None:
        blockers = [str(item) for item in gate.get("blockers", []) or []]
        warnings = [str(item) for item in gate.get("warnings", []) or []]
        if gate.get("status") == eligible_status:
            button.setEnabled(True)
            label.setText(
                f"{display_name} gate passed；source={gate.get('selected_result_id', '')}；"
                f"table-only={gate.get('allow_table_only_report', False)}；"
                "section-only package；full integrated report / risk score / clinical conclusion remain disabled."
            )
        else:
            button.setEnabled(False)
            reason = "；".join(blockers) or f"{display_name} gate 未通过"
            if warnings:
                reason = f"{reason}；warnings={'；'.join(warnings)}"
            label.setText(f"{display_name} disabled：{reason}")

    def _render_full_integrated_report_preview(self, gate: dict[str, object], plan: dict[str, object], docx_gate: dict[str, object] | None = None) -> None:
        if not hasattr(self, "_full_integrated_status"):
            return
        docx_gate = docx_gate or self._build_full_integrated_docx_rendered_export_ui_gate()
        blockers = [str(item) for item in gate.get("blockers", []) or []]
        warnings = [str(item) for item in gate.get("warnings", []) or []]
        disabled_reasons = [str(item) for item in plan.get("disabled_reasons", []) or []]
        can_create = bool(plan.get("can_create_package"))
        self._full_integrated_button.setEnabled(gate.get("status") == "eligible_for_full_integrated_report" and can_create)
        if hasattr(self, "_full_integrated_docx_button"):
            self._full_integrated_docx_button.setEnabled(docx_gate.get("status") == "passed")
        if self._full_integrated_button.isEnabled():
            renderer_id = str(plan.get("renderer_id") or "builtin_markdown")
            self._full_integrated_status.setText(
                f"Full integrated report gate passed；renderer={renderer_id}；markdown-only package can be created；"
                f"DOCX rendered export={docx_gate.get('status', 'blocked')}；PDF/DOCX disabled unless DOCX rendered export gate passes；no clinical diagnosis/prognosis/risk score/treatment advice."
            )
        else:
            reason = "；".join(disabled_reasons or blockers) or str(plan.get("blocked_reason") or "full integrated report gate 未通过")
            if warnings:
                reason = f"{reason}；warnings={'；'.join(warnings)}"
            self._full_integrated_status.setText(f"Full integrated report disabled：{reason}")
        docx_blockers = [str(item) for item in docx_gate.get("blockers", []) or []]
        docx_warnings = [str(item) for item in docx_gate.get("warnings", []) or []]
        docx_reason = "；".join(docx_blockers) or str(docx_gate.get("disabled_reason") or "")
        if docx_warnings:
            docx_reason = f"{docx_reason}；warnings={'；'.join(docx_warnings)}" if docx_reason else f"warnings={'；'.join(docx_warnings)}"
        _fill_table(
            self._full_integrated_plan,
            [
                ["section_scope", plan.get("section_scope", gate.get("section_scope", "full_integrated_report"))],
                ["export_format", plan.get("export_format", self._full_integrated_format.currentText() if hasattr(self, "_full_integrated_format") else "markdown")],
                ["can_create_package", plan.get("can_create_package", False)],
                ["export_activation_status", gate.get("export_activation_status", "")],
                ["enabled_export_formats", ", ".join(str(item) for item in gate.get("enabled_export_formats", []) or [])],
                ["disabled_export_formats", ", ".join(str(item) for item in gate.get("disabled_export_formats", []) or [])],
                ["prerequisite_summary", gate.get("prerequisite_summary", {})],
                ["renderer_status", plan.get("renderer_status", "")],
                ["renderer_id", plan.get("renderer_id", "")],
                ["renderer_dependencies", ", ".join(str(item) for item in plan.get("renderer_dependencies", []) or [])],
                ["renderer_disabled_reason", plan.get("renderer_disabled_reason", "")],
                ["renderer_preflight_policy", plan.get("renderer_preflight_policy", {})],
                ["docx_rendered_export_status", docx_gate.get("status", "")],
                ["docx_rendered_export_source_package", docx_gate.get("source_package_path", "")],
                ["docx_rendered_export_renderer", docx_gate.get("renderer_id", "pandoc_docx")],
                ["docx_rendered_export_disabled_reason", docx_reason],
                ["docx_rendered_export_output_policy", "package artifact only; no result_index_v2 write; no formal_computed_result"],
                ["package_root_policy", plan.get("package_root_policy", "")],
                ["required_directories", ", ".join(str(item) for item in plan.get("required_directories", []) or [])],
                ["required_files", ", ".join(str(item) for item in plan.get("required_files", []) or [])],
                ["limitations", "; ".join(str(item) for item in gate.get("limitations_required", []) or [])],
                ["blocked_reason", plan.get("blocked_reason", "；".join(blockers))],
            ],
        )
        rows = gate.get("section_rows", []) if isinstance(gate.get("section_rows"), list) else []
        prerequisite_rows = {
            str(row.get("section_id") or ""): row
            for row in gate.get("prerequisite_rows", []) or []
            if isinstance(row, dict)
        }
        _fill_table(
            self._full_integrated_sections,
            [
                [
                    row.get("section_id", ""),
                    row.get("result_id", ""),
                    row.get("result_semantics", ""),
                    row.get("validation_status", ""),
                    row.get("section_report_ready_status", ""),
                    row.get("plot_artifact_status", ""),
                    (prerequisite_rows.get(str(row.get("section_id") or "")) or {}).get("section_package_validation_status", ""),
                    (prerequisite_rows.get(str(row.get("section_id") or "")) or {}).get("status", ""),
                    "; ".join(str(item) for item in row.get("blockers", []) or []),
                ]
                for row in rows
                if isinstance(row, dict)
            ],
        )

    def _build_full_integrated_docx_rendered_export_ui_gate(self) -> dict[str, object]:
        if self._project_root is None:
            return {"status": "blocked", "blockers": ["project_root_missing"], "warnings": [], "renderer_id": "pandoc_docx"}
        package_path = _latest_full_integrated_markdown_package(self._project_root)
        renderer_gate = evaluate_full_integrated_report_renderer_gate("docx", allow_docx_activation=True)
        if package_path is None:
            blockers = ["full_integrated_markdown_package_missing", *[str(item) for item in renderer_gate.get("blockers", []) or []]]
            return {
                "schema_version": "biomedpilot.full_integrated_docx_rendered_export_ui_gate.v1",
                "status": "blocked",
                "source_package_path": "",
                "renderer_id": "pandoc_docx",
                "renderer_gate": renderer_gate,
                "checks": {
                    "source_markdown_package_exists": False,
                    "pandoc_detected": bool((renderer_gate.get("detected_dependencies", {}).get("pandoc") or {}).get("available")) if isinstance(renderer_gate.get("detected_dependencies"), dict) else False,
                    "detect_first_no_install_action": True,
                    "writes_result_index_v2": False,
                },
                "blockers": list(dict.fromkeys(blockers)),
                "warnings": [],
                "disabled_reason": "；".join(dict.fromkeys(blockers)),
            }
        preflight = evaluate_full_integrated_docx_preflight_gate(
            package_path,
            renderer_gate=renderer_gate,
            include_activation_blocker=False,
        )
        blockers = [str(item) for item in preflight.get("blockers", []) or []]
        warnings = [str(item) for item in preflight.get("warnings", []) or []]
        return {
            "schema_version": "biomedpilot.full_integrated_docx_rendered_export_ui_gate.v1",
            "status": "passed" if preflight.get("status") == "passed" else "blocked",
            "source_package_path": str(package_path),
            "renderer_id": "pandoc_docx",
            "renderer_gate": renderer_gate,
            "preflight_gate": preflight,
            "checks": {
                "source_markdown_package_exists": True,
                "pandoc_detected": bool((renderer_gate.get("detected_dependencies", {}).get("pandoc") or {}).get("available")) if isinstance(renderer_gate.get("detected_dependencies"), dict) else False,
                "docx_preflight_passed": preflight.get("status") == "passed",
                "detect_first_no_install_action": True,
                "writes_result_index_v2": False,
            },
            "blockers": blockers,
            "warnings": warnings,
            "disabled_reason": "；".join(blockers),
        }

    def _render_ora_review(self, review: dict[str, object]) -> None:
        summary = review.get("summary") if isinstance(review.get("summary"), dict) else {}
        provenance = review.get("provenance") if isinstance(review.get("provenance"), dict) else {}
        downstream = review.get("disabled_downstream") if isinstance(review.get("disabled_downstream"), dict) else {}
        rows = [row for row in review.get("rows", []) or [] if isinstance(row, dict)]
        if review.get("status") != "passed":
            self._ora_summary_label.setText("ORA summary：暂无 controlled ORA result；raw/preflight/testing/exploratory 不会混入此审阅区。")
            _fill_table(self._ora_table, [])
            _fill_table(self._ora_provenance, [["Status", "; ".join(str(item) for item in review.get("blockers", []) or []) or "blocked"]])
            return
        deps = summary.get("dependency_versions") if isinstance(summary.get("dependency_versions"), dict) else {}
        self._ora_summary_label.setText(
            "ORA summary："
            f"terms={summary.get('term_total', 0)}；significant={summary.get('significant_term_count', 0)}；top={summary.get('top_term_by_fdr', '')}；"
            f"source={summary.get('source_deg_result_id', '')} / {summary.get('source_result_semantics', '')}；"
            f"gene_set={summary.get('gene_set_resource', '')}；method={summary.get('method', '')}；"
            f"selected genes={summary.get('selected_gene_count', 0)}；background={summary.get('background_size', 0)}；"
            f"deps scipy={deps.get('scipy', '')}, statsmodels={deps.get('statsmodels', '')}."
        )
        self._ora_downstream_label.setText("；".join(str(value) for value in downstream.values()) if downstream else "ORA plot/report-ready/GSEA/survival disabled.")
        _fill_table(
            self._ora_table,
            [
                [
                    row.get("term_id", ""),
                    row.get("term_name", ""),
                    row.get("overlap_count", ""),
                    row.get("gene_set_size", ""),
                    row.get("selected_gene_count", ""),
                    row.get("enrichment_ratio", ""),
                    row.get("p_value", ""),
                    row.get("adjusted_p_value", ""),
                    row.get("overlap_genes", ""),
                    row.get("significance_label", ""),
                ]
                for row in rows[:200]
            ],
        )
        _fill_table(
            self._ora_provenance,
            [
                ["ora_input_id", provenance.get("ora_input_id", "")],
                ["source_deg_result_id", provenance.get("source_deg_result_id", "")],
                ["source_result_semantics", provenance.get("source_result_semantics", "")],
                ["gene_set_resource_id", provenance.get("gene_set_resource_id", "")],
                ["dependency_snapshot", "present" if provenance.get("dependency_snapshot_present") else "missing"],
                ["task_run_log", provenance.get("task_run_log", "")],
                ["result_index_path", provenance.get("result_index_path", "")],
                ["result_table_path", provenance.get("result_table_path", "")],
                ["plot_artifacts", provenance.get("plot_artifacts", [])],
                ["report_artifacts", provenance.get("report_artifacts", [])],
                ["report_ready_eligible", provenance.get("report_ready_eligible", False)],
            ],
        )

    def _render_gsea_review(self, review: dict[str, object]) -> None:
        summary = review.get("summary") if isinstance(review.get("summary"), dict) else {}
        provenance = review.get("provenance") if isinstance(review.get("provenance"), dict) else {}
        downstream = review.get("disabled_downstream") if isinstance(review.get("disabled_downstream"), dict) else {}
        rows = [row for row in review.get("rows", []) or [] if isinstance(row, dict)]
        if review.get("status") != "passed":
            self._gsea_summary_label.setText("GSEA summary：暂无 controlled preranked GSEA result；raw/preflight/testing/exploratory 不会混入此审阅区。")
            self._gsea_downstream_label.setText("GSEA plot/report-ready disabled：等待 B11.3 plot artifact / 后续 report gate。")
            _fill_table(self._gsea_table, [])
            _fill_table(self._gsea_provenance, [["Status", "; ".join(str(item) for item in review.get("blockers", []) or []) or "blocked"]])
            return
        deps = summary.get("dependency_versions") if isinstance(summary.get("dependency_versions"), dict) else {}
        self._gsea_summary_label.setText(
            "GSEA summary："
            f"terms={summary.get('term_total', 0)}；significant={summary.get('significant_term_count', 0)}；"
            f"top+NES={summary.get('top_positive_nes_term', '')}；top-NES={summary.get('top_negative_nes_term', '')}；"
            f"source={summary.get('source_deg_result_id', '')} / {summary.get('source_result_semantics', '')}；"
            f"rank={summary.get('rank_metric', '')}；gene_set={summary.get('gene_set_resource', '')}；"
            f"permutations={summary.get('permutation_count', 0)}；seed={summary.get('random_seed', '')}；"
            f"deps numpy={deps.get('numpy', '')}, pandas={deps.get('pandas', '')}, scipy={deps.get('scipy', '')}, statsmodels={deps.get('statsmodels', '')}."
        )
        self._gsea_downstream_label.setText("；".join(str(value) for value in downstream.values()) if downstream else "GSEA plot/report-ready/survival/clinical disabled.")
        _fill_table(
            self._gsea_table,
            [
                [
                    row.get("term_id", ""),
                    row.get("term_name", ""),
                    row.get("set_size", ""),
                    row.get("overlap_size", ""),
                    row.get("enrichment_score", ""),
                    row.get("normalized_enrichment_score", ""),
                    row.get("p_value", ""),
                    row.get("adjusted_p_value", ""),
                    row.get("leading_edge_genes", ""),
                    row.get("rank_metric", ""),
                    row.get("significance_label", ""),
                ]
                for row in rows[:200]
            ],
        )
        _fill_table(
            self._gsea_provenance,
            [
                ["gsea_input_id", provenance.get("gsea_input_id", "")],
                ["source_deg_result_id", provenance.get("source_deg_result_id", "")],
                ["source_result_semantics", provenance.get("source_result_semantics", "")],
                ["gene_set_resource_id", provenance.get("gene_set_resource_id", "")],
                ["dependency_snapshot", "present" if provenance.get("dependency_snapshot_present") else "missing"],
                ["task_run_log", provenance.get("task_run_log", "")],
                ["result_index_path", provenance.get("result_index_path", "")],
                ["result_table_path", provenance.get("result_table_path", "")],
                ["plot_artifacts", provenance.get("plot_artifacts", [])],
                ["report_artifacts", provenance.get("report_artifacts", [])],
                ["report_ready_eligible", provenance.get("report_ready_eligible", False)],
            ],
        )

    def _render_gsea_plot_gate(self, gate: dict[str, object]) -> None:
        if not hasattr(self, "_gsea_plot_status"):
            return
        blockers = [str(item) for item in gate.get("blockers", []) or []]
        warnings = [str(item) for item in gate.get("warnings", []) or []]
        if gate.get("status") == "passed":
            existing = gate.get("existing_plot_artifacts", []) if isinstance(gate.get("existing_plot_artifacts"), list) else []
            self._gsea_plot_button.setEnabled(True)
            self._gsea_plot_status.setText(
                f"GSEA plot gate passed；source={gate.get('selected_result_id', '')}；existing artifacts={len(existing)}；"
                "spec_only_no_image_dependency；does not render PNG/SVG/PDF；full report remains disabled."
            )
        else:
            self._gsea_plot_button.setEnabled(False)
            reason = "；".join(blockers) or "GSEA plot gate 未通过"
            if warnings:
                reason = f"{reason}；warnings={'；'.join(warnings)}"
            self._gsea_plot_status.setText(f"GSEA plot disabled：{reason}")

    def _render_gsea_report_gate(self, gate: dict[str, object]) -> None:
        if not hasattr(self, "_gsea_report_status"):
            return
        blockers = [str(item) for item in gate.get("blockers", []) or []]
        warnings = [str(item) for item in gate.get("warnings", []) or []]
        if gate.get("status") in {"eligible_for_gsea_report_ready", "eligible_for_imported_derived_gsea_report_package"}:
            self._gsea_report_button.setEnabled(True)
            imported_note = "；imported-derived source will stay labeled" if gate.get("status") == "eligible_for_imported_derived_gsea_report_package" else ""
            self._gsea_report_status.setText(
                f"GSEA report-ready gate passed；source={gate.get('selected_result_id', '')}；"
                f"deps={gate.get('dependency_versions', {})}；table-only={gate.get('allow_table_only_report', False)}{imported_note}；"
                "package scope=GSEA only；survival/full report/clinical conclusions disabled."
            )
        else:
            self._gsea_report_button.setEnabled(False)
            reason = "；".join(blockers) or "GSEA report-ready gate 未通过"
            if warnings:
                reason = f"{reason}；warnings={'；'.join(warnings)}"
            self._gsea_report_status.setText(f"GSEA report-ready disabled：{reason}")

    def _render_ora_plot_gate(self, gate: dict[str, object]) -> None:
        if not hasattr(self, "_ora_plot_status"):
            return
        blockers = [str(item) for item in gate.get("blockers", []) or []]
        warnings = [str(item) for item in gate.get("warnings", []) or []]
        if gate.get("status") == "passed":
            existing = gate.get("existing_plot_artifacts", []) if isinstance(gate.get("existing_plot_artifacts"), list) else []
            self._ora_plot_button.setEnabled(True)
            self._ora_plot_status.setText(
                f"ORA plot gate passed；source={gate.get('selected_result_id', '')}；existing artifacts={len(existing)}；"
                "spec_only_no_image_dependency；does not render PNG/SVG/PDF；report-ready remains disabled."
            )
        else:
            self._ora_plot_button.setEnabled(False)
            reason = "；".join(blockers) or "ORA plot gate 未通过"
            if warnings:
                reason = f"{reason}；warnings={'；'.join(warnings)}"
            self._ora_plot_status.setText(f"ORA plot disabled：{reason}")

    def _render_ora_report_gate(self, gate: dict[str, object]) -> None:
        if not hasattr(self, "_ora_report_status"):
            return
        blockers = [str(item) for item in gate.get("blockers", []) or []]
        warnings = [str(item) for item in gate.get("warnings", []) or []]
        if gate.get("status") in {"eligible_for_ora_report_ready", "eligible_for_imported_derived_ora_report_package"}:
            self._ora_report_button.setEnabled(True)
            imported_note = "；imported-derived source will stay labeled" if gate.get("status") == "eligible_for_imported_derived_ora_report_package" else ""
            self._ora_report_status.setText(
                f"ORA report-ready gate passed；source={gate.get('selected_result_id', '')}；"
                f"deps={gate.get('dependency_versions', {})}；table-only={gate.get('allow_table_only_report', False)}{imported_note}；"
                "package scope=ORA only；GSEA/survival/full report/clinical conclusions disabled."
            )
        else:
            self._ora_report_button.setEnabled(False)
            reason = "；".join(blockers) or "ORA report-ready gate 未通过"
            if warnings:
                reason = f"{reason}；warnings={'；'.join(warnings)}"
            self._ora_report_status.setText(f"ORA report-ready disabled：{reason}")


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
            return None
        payload = load_project_report(self._project_root)
        self._render(payload)
        return payload

    def status_message(self) -> str:
        return self._status_label.text()

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("项目报告", "生成和查看项目报告草稿，保持导入、测试级和未运行状态的边界。", back_text="返回结果浏览", back_signal=self.back_requested))
        actions = QHBoxLayout()
        actions.addWidget(_button("刷新报告草稿", "primaryButton", self.generate_report))
        actions.addWidget(_button("打开报告文件夹", "secondaryButton", lambda: _open_path(self._project_root / "reports" if self._project_root else None)))
        actions.addWidget(_button("复制报告摘要", "secondaryButton", self.copy_report_summary))
        actions.addStretch(1)
        root.addLayout(actions)
        self._status_label = _status_label("没有报告草稿时请点击刷新报告草稿。本阶段只生成 Markdown 和 report_manifest.json。")
        root.addWidget(self._status_label)

        summary_card, summary_layout = _card("报告草稿状态")
        self._report_status_label = _muted("报告状态：尚未生成。")
        self._report_status_label.setObjectName("reportDraftStatus")
        self._report_semantics_label = _muted("结果语义：暂无结果。")
        self._report_semantics_label.setObjectName("reportResultSemantics")
        self._report_next_step_label = _muted("下一步建议：先返回结果浏览确认结果来源。")
        self._report_next_step_label.setObjectName("reportNextStep")
        summary_layout.addWidget(self._report_status_label)
        summary_layout.addWidget(self._report_semantics_label)
        summary_layout.addWidget(self._report_next_step_label)
        root.addWidget(summary_card)

        self._sections = _table(["报告部分", "当前状态", "来源说明", "注意事项"])
        self._sections.setObjectName("reportDraftSectionsTable")
        root.addWidget(self._sections)
        _set_table_widths(self._sections, [170, 150, 260, 320])
        self._sections.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        self._report_ready_gate = _table(["Gate", "状态", "依据", "Blockers", "Warnings"])
        self._report_ready_gate.setObjectName("reportReadyGateTable")
        root.addWidget(self._report_ready_gate)
        _set_table_widths(self._report_ready_gate, [170, 170, 230, 320, 300])
        self._report_ready_gate.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        self._markdown = _text_preview(220)
        self._markdown.setObjectName("reportDraftUserPreview")
        root.addWidget(self._markdown)

        developer_card, developer_layout = _card("开发者诊断")
        developer_actions = QHBoxLayout()
        developer_actions.addWidget(_button("展开技术细节", "secondaryButton", lambda: _toggle_details(self._manifest)))
        developer_actions.addWidget(_button("打开报告文件夹", "secondaryButton", lambda: _open_path(self._project_root / "reports" if self._project_root else None)))
        developer_actions.addStretch(1)
        developer_layout.addLayout(developer_actions)
        self._manifest = _text_preview(140)
        self._manifest.setObjectName("reportDeveloperDiagnostics")
        self._manifest.setVisible(False)
        developer_layout.addWidget(self._manifest)
        root.addWidget(developer_card)

    def _render(self, payload: dict[str, object]) -> None:
        markdown = str(payload.get("markdown") or "")
        manifest = payload.get("manifest")
        result_payload = load_result_index(self._project_root) if self._project_root else {}
        entries = _result_entries_for_display(self._project_root, result_payload)
        records = load_task_records(self._project_root) if self._project_root else []
        if not markdown:
            self._status_label.setText("尚未生成项目报告草稿。本阶段只生成 Markdown 和 report_manifest.json。")
        else:
            self._status_label.setText("已读取项目级 Markdown 报告草稿。本阶段不导出 Word 或 PDF。")
        self._report_status_label.setText(_report_draft_status_text(markdown, manifest))
        self._report_semantics_label.setText(_report_result_semantics_text(entries, records))
        self._report_next_step_label.setText(_report_next_step_text(markdown, entries, records))
        _fill_table(self._sections, _report_section_rows(self._project_root, entries, records, bool(markdown)))
        analysis_state = build_analysis_center_state(self._project_root) if self._project_root else {}
        _fill_table(self._report_ready_gate, _analysis_ui_gate_rows(analysis_state.get("gate_rows", [])))
        self._markdown.setPlainText(_report_user_preview_text(markdown, entries, records))
        self._manifest.setPlainText(_json({"markdown": markdown, "report_payload": payload, "report_manifest": manifest, "result_index": result_payload, "task_records": records, "analysis_center_state": analysis_state}))

    def copy_report_summary(self) -> str:
        summary = self._markdown.toPlainText().strip()
        if not summary:
            summary = "当前尚未生成报告草稿。"
        QApplication.clipboard().setText(summary)
        self._status_label.setText("已复制报告摘要。")
        return summary


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

        analysis_dep_card, analysis_dep_layout = _card("Analysis dependency detection")
        analysis_dep_layout.addWidget(_muted("Detect-first only：不自动安装 scipy/statsmodels/R/lifelines；缺失时显示 blocker 并禁用 formal analysis。"))
        self._analysis_dependency_status = _table(["依赖", "状态", "版本", "Blockers", "打包影响", "操作"])
        self._analysis_dependency_status.setObjectName("analysisDependencyStatusTable")
        analysis_dep_layout.addWidget(self._analysis_dependency_status)
        root.addWidget(analysis_dep_card)
        _set_table_widths(self._analysis_dependency_status, [150, 130, 110, 280, 260, 220])
        self._analysis_dependency_status.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        _fill_table(self._analysis_dependency_status, _analysis_ui_dependency_rows(build_dependency_rows()))

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


def _button(text: str, object_name: str, callback: Callable[..., Any]) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName(object_name)
    button.clicked.connect(callback)
    return button


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
    table.setMinimumHeight(160)
    table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return table


def _fill_table(table: QTableWidget, rows: list[list[object]]) -> None:
    table.clearContents()
    table.setRowCount(len(rows))
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            table.setItem(row_index, col_index, item)
    table.resizeColumnsToContents()


def _clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
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
        "source_files": list(summary.source_files),
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
            source_files=tuple(_recognition_source_files_from_payload(payload)),
        )
        key = (row.source_type_key, row.acquisition_id) if row.source_type_key == "local_import" else (row.source_type_key, row.source_label)
        previous = rows_by_key.get(key)
        if previous is None or _registered_row_rank(row) >= _registered_row_rank(previous):
            rows_by_key[key] = row
    return sorted(rows_by_key.values(), key=lambda row: row.created_at)


def _current_project_dataset_entries(project_root: Path | None, *, geo_only: bool = False, expand_geo_files: bool = True) -> list[DatasetListEntry]:
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
            source_files=tuple(_recognition_source_files_from_payload(payload)),
        )
        entry = _dataset_entry_from_record(project_root, row, payload, metadata, notes)
        entries = _expand_dataset_entries(entry, notes, expand_geo_files=expand_geo_files)
        for entry in entries:
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
    if expand_geo_files:
        expanded_geo_bases = {
            entry.key.split(":file:", 1)[0]
            for entry in grouped.values()
            if entry.source_type_key in GEO_SOURCE_TYPES and entry.focused_source_file and ":file:" in entry.key
        }
        for base_key in expanded_geo_bases:
            grouped.pop(base_key, None)
    return sorted(grouped.values(), key=lambda entry: (_dataset_source_order(entry.source_type_key), entry.name))


def _expand_dataset_entries(entry: DatasetListEntry, notes: dict[str, str], *, expand_geo_files: bool) -> list[DatasetListEntry]:
    local_entries = _expand_local_dataset_entries(entry, notes)
    if len(local_entries) != 1 or local_entries[0] is not entry:
        return local_entries
    if expand_geo_files:
        return _expand_geo_dataset_entries(entry, notes)
    return [entry]


def _pending_dataset_entry_count(entries: Iterable[DatasetListEntry]) -> int:
    return sum(
        1
        for entry in entries
        if entry.downloadable
        or entry.status in {"未下载", "元数据已下载", "需要补充信息"}
        or entry.missing_content not in {"无", "待识别确认"}
    )


def _data_selection_next_step_text(project_root: Path | None, *, count: int, ready_count: int, pending_count: int) -> str:
    if project_root is None:
        return "下一步：请先创建或打开项目。"
    if count == 0:
        return "下一步：先导入本地数据，或检索 GSE / 中文研究主题。"
    if ready_count > 0 and pending_count > 0:
        return "下一步：可先进入数据检查与准备；仍有待下载或待确认的数据来源可稍后补充。"
    if ready_count > 0:
        return "下一步：可以进入数据检查与准备。"
    if pending_count > 0:
        return "下一步：先完成下载或确认数据来源，再进入数据检查与准备。"
    return "下一步：请检查数据来源状态。"


def _user_asset_label(asset: str) -> str:
    return {
        "rna_seq_expression": "RNA-seq 表达矩阵",
        "sample_metadata": "样本信息",
        "clinical_metadata": "临床信息",
        "case_sample_mapping": "case/sample 映射",
        "project_metadata": "项目元数据",
        "gene_expression": "基因表达",
        "gene_level_expression": "gene-level 表达矩阵",
        "sample_annotation": "样本注释",
        "tissue_metadata": "组织元数据",
    }.get(asset, asset)


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
    source_files = tuple(_recognition_source_files_from_payload(payload))
    note = notes.get(key, "")
    return DatasetListEntry(
        key=key,
        source=_dataset_source_label(row, metadata),
        name=row.source_label,
        status=status,
        available_content=available,
        missing_content=missing,
        note=note,
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
        source_files=source_files,
        storage_policy=str(payload.get("strategy") or ""),
    )


def _expand_local_dataset_entries(entry: DatasetListEntry, notes: dict[str, str]) -> list[DatasetListEntry]:
    if entry.source_type_key != "local_import" or len(entry.source_files) <= 1:
        return [entry]
    storage = _storage_policy_text(entry.storage_policy)
    batch_summary = _local_import_batch_summary(entry.source_files, entry.storage_policy, entry.status)
    expanded: list[DatasetListEntry] = []
    for index, raw_path in enumerate(entry.source_files, start=1):
        file_key = f"{entry.key}:file:{index}"
        file_name = Path(raw_path).name
        expanded.append(
            DatasetListEntry(
                **{
                    **entry.__dict__,
                    "key": file_key,
                    "name": file_name,
                    "available_content": "待识别：1 个文件",
                    "note": notes.get(file_key, ""),
                    "title": file_name,
                    "abstract": f"本地导入批次中的第 {index} 个文件。",
                    "keywords": _local_file_type_hint(file_name),
                    "technical_info": _local_file_dataset_technical_info(entry, raw_path, index, storage),
                    "focused_source_file": raw_path,
                    "batch_summary": batch_summary,
                }
            )
        )
    return expanded


def _expand_geo_dataset_entries(entry: DatasetListEntry, notes: dict[str, str]) -> list[DatasetListEntry]:
    if entry.source_type_key not in GEO_SOURCE_TYPES or len(entry.source_files) <= 1:
        return [entry]
    batch_summary = _geo_download_batch_summary(entry.source_files, entry.accession or entry.name, entry.status)
    expanded: list[DatasetListEntry] = []
    for index, raw_path in enumerate(entry.source_files, start=1):
        file_key = f"{entry.key}:file:{index}"
        file_name = Path(raw_path).name
        expanded.append(
            DatasetListEntry(
                **{
                    **entry.__dict__,
                    "key": file_key,
                    "name": file_name,
                    "available_content": "待识别：1 个文件",
                    "missing_content": "待识别确认",
                    "note": notes.get(file_key, ""),
                    "title": file_name,
                    "abstract": f"{entry.accession or entry.name} 下载候选中的第 {index} 个文件。",
                    "keywords": _local_file_type_hint(file_name),
                    "technical_info": _geo_file_dataset_technical_info(entry, raw_path, index),
                    "focused_source_file": raw_path,
                    "batch_summary": batch_summary,
                }
            )
        )
    return expanded


def _geo_download_batch_summary(source_files: tuple[str, ...], accession: str, status: str) -> str:
    names = [Path(path).name for path in source_files]
    preview = "、".join(names[:3])
    remaining = len(names) - 3
    if remaining > 0:
        preview = f"{preview}；另有 {remaining} 个文件"
    return f"{accession} 下载文件总数：{len(source_files)} 个；状态：{status}；包含 {preview}"


def _geo_file_dataset_technical_info(entry: DatasetListEntry, focused_source_file: str, index: int) -> str:
    return _json(
        {
            "数据来源": entry.source,
            "GSE 编号": entry.accession or entry.name,
            "当前文件": focused_source_file,
            "文件序号": index,
            "下载文件总数": len(entry.source_files),
            "source_files": list(entry.source_files),
            "acquisition_ids": list(entry.acquisition_ids),
        }
    )


def _tcga_preview_status_text(summary: TCGAPreviewSummary) -> str:
    if summary.status == "failed":
        return "预览失败"
    if summary.status == "empty":
        return "未找到匹配数据"
    if summary.is_download_plan_available:
        return "可生成下载计划草案"
    return "metadata 预览完成"


def _tcga_preview_summary_text(summary: TCGAPreviewSummary) -> str:
    lines = [
        f"项目：{summary.request.project_label_zh} ({summary.request.project_id})",
        f"分析目的：{summary.request.analysis_purpose_zh}",
        f"样本范围：{summary.request.sample_scope_zh}",
        f"case 数：{summary.case_count}",
        f"sample 数：{summary.sample_count}",
        f"file 数：{summary.file_count}",
        f"预计下载大小：{format_bytes_zh(summary.estimated_size_bytes, has_unknown=summary.size_has_unknown)}",
    ]
    if summary.request.analysis_purpose == "differential_expression":
        lines.append("预计下载内容：开放 RNA-Seq STAR - Counts，用于后续表达矩阵构建和差异分析 preflight。")
    elif summary.request.analysis_purpose == "expression_clinical":
        lines.append("预计下载内容：开放 RNA-Seq STAR - Counts，并预览 clinical/sample metadata 可用性。")
    elif summary.request.analysis_purpose == "survival":
        lines.append("预计下载内容：clinical/case/sample metadata 概况；本阶段不执行生存分析。")
    else:
        lines.append("预计下载内容：项目样本 metadata 概况，不创建可分析表达数据集。")
    lines.append("本阶段仅预览和生成草案，不下载文件、不构建表达矩阵、不进入 DEG/GSEA ready。")
    if summary.access_counts:
        lines.append("访问类型分布：" + _counter_text(summary.access_counts))
    if summary.workflow_type_counts:
        lines.append("工作流摘要：" + _counter_text(summary.workflow_type_counts))
    if summary.data_format_counts:
        lines.append("文件格式摘要：" + _counter_text(summary.data_format_counts))
    return "\n".join(lines)


def _tcga_preview_developer_payload(summary: TCGAPreviewSummary) -> dict[str, object]:
    return {
        "endpoint": {
            "files": "/files",
            "cases": "/cases",
        },
        "filters": {
            "files": summary.gdc_filters,
            "cases": summary.case_filters,
        },
        "fields": {
            "files": "see app.bioinformatics.data_sources.tcga_preview.FILE_FIELDS",
            "cases": "see app.bioinformatics.data_sources.tcga_preview.CASE_FIELDS",
        },
        "pagination": {
            "files_fetched": summary.files_fetched,
            "files_total": summary.files_total,
            "cases_fetched": summary.cases_fetched,
            "cases_total": summary.cases_total,
        },
        "selected_file_ids_preview": list(summary.selected_file_ids_preview[:10]),
        "warnings": list(summary.warnings),
        "status": summary.status,
        "error_message": summary.error_message,
    }


def _tcga_workflow_status_zh(status: str) -> str:
    return {
        "not_started": "未开始",
        "available": "可执行",
        "running_or_requested": "已请求",
        "completed": "已完成",
        "failed": "失败",
        "blocked": "被阻断",
        "skipped": "已跳过",
    }.get(status, status)


def _tcga_workflow_stage_zh(stage: str) -> str:
    return {
        "preview": "预览可下载数据",
        "download": "下载 TCGA 原始文件",
        "expression_build": "构建 TCGA 表达矩阵",
        "clinical": "获取 TCGA 临床信息",
        "data_check": "进入数据检查与准备",
    }.get(stage, stage or "未开始")


def _gtex_workflow_stage_zh(stage: str) -> str:
    return {
        "preview": "预览 GTEx 可下载数据",
        "download": "下载 GTEx 原始文件",
        "expression_build": "构建 GTEx 表达矩阵",
        "data_check": "进入数据检查与准备",
        "manual_config": "后续手动配置用途",
    }.get(stage, stage or "未开始")


def _tcga_workflow_user_summary(step) -> str:
    summary = str(getattr(step, "summary", "") or "")
    warning = str(getattr(step, "warning", "") or "")
    text = summary if len(summary) <= 130 else summary[:127] + "..."
    if warning:
        text = f"{text}；提示：{warning}"
    return text


def _gtex_preview_status_text(summary: GTExPreviewSummary) -> str:
    if summary.status == "failed":
        return "预览失败"
    if summary.status == "empty":
        return "未找到匹配数据"
    if summary.is_download_plan_available:
        return "可生成下载计划草案"
    return "metadata 预览完成"


def _counter_text(values: dict[str, int]) -> str:
    return "、".join(f"{key} {count}" for key, count in values.items())


def _local_import_batch_summary(source_files: tuple[str, ...], storage_policy: str, status: str) -> str:
    if not source_files:
        return ""
    names = [Path(path).name for path in source_files]
    preview = "、".join(names[:3])
    remaining = len(names) - 3
    if remaining > 0:
        preview = f"{preview}，另有 {remaining} 个文件"
    contains = f"包含 {names[0]} 等 {len(names)} 个文件" if len(names) > 1 else f"包含 {names[0]}"
    return "；".join(
        [
            f"文件总数：{len(names)} 个",
            f"保存方式：{_storage_policy_text(storage_policy)}",
            f"来源状态：{status}",
            contains,
            f"文件预览：{preview}",
        ]
    )


def _local_file_type_hint(file_name: str) -> str:
    lowered = file_name.lower()
    if lowered.endswith(".soft") or "family.soft" in lowered:
        return "GEO SOFT"
    if "series_matrix" in lowered:
        return "GEO Series Matrix"
    if lowered.endswith((".xlsx", ".xls")):
        return "Excel 表格"
    if lowered.endswith((".csv", ".tsv", ".txt", ".txt.gz", ".tsv.gz", ".csv.gz")):
        return "文本表格"
    return "本地文件"


def _local_file_dataset_technical_info(entry: DatasetListEntry, focused_source_file: str, index: int, storage: str) -> str:
    return _json(
        {
            "数据来源": entry.source,
            "当前文件": focused_source_file,
            "文件序号": index,
            "批次文件总数": len(entry.source_files),
            "保存方式": storage,
            "source_files": list(entry.source_files),
            "acquisition_ids": list(entry.acquisition_ids),
        }
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
    if ui_source == "tcga_database_page":
        return "TCGA 数据库"
    if ui_source == "gtex_database_page":
        return "GTEx 数据库"
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
    if "tcga" in row.source_type_key and str(metadata.get("download_status") or "") == "tcga_expression_matrix_built":
        return "TCGA 表达矩阵已构建，等待数据检查与准备"
    if "tcga" in row.source_type_key and str(metadata.get("download_status") or "") == "tcga_clinical_metadata_built":
        if str(metadata.get("mode") or "") == "project_clinical_preview_only":
            return "TCGA clinical 概况已获取，等待 B6.4 表达矩阵后映射"
        return "TCGA clinical metadata 已获取，等待数据检查与准备"
    if "gtex" in row.source_type_key and str(metadata.get("download_status") or "") == "gtex_expression_matrix_built":
        return "GTEx 表达矩阵已构建，等待数据检查与准备"
    if _record_ready_for_recognition(payload, metadata):
        if row.source_type_key == "local_import":
            return "已导入"
        if "已下载" in row.status or "可进入识别" in row.status:
            return "已下载"
        return "待识别"
    if payload.get("strategy") == "plan_only":
        if row.source_type_key in GEO_SOURCE_TYPES:
            return "未下载"
        if "tcga" in row.source_type_key or "gtex" in row.source_type_key:
            return "等待下载与构建"
        return "未下载"
    if "tcga" in row.source_type_key and str(metadata.get("analysis_gate_status") or "") == "waiting_b6_4_expression_matrix_build":
        return "TCGA 原始文件已获取，等待 B6.4 构建表达矩阵"
    if "gtex" in row.source_type_key and str(metadata.get("analysis_gate_status") or "") == "waiting_gtex_expression_matrix_build":
        return "GTEx 原始文件已获取，等待构建表达矩阵"
    if row.status and row.status not in {"已登记", "已登记，需确认"}:
        return row.status.replace("已登记", "已添加")
    return "需要补充信息" if row.status.endswith("需确认") else "待识别"


def _dataset_available_content(row: RegisteredSourceRow, status: str, metadata: dict[str, object]) -> str:
    if row.source_type_key == "local_import":
        count = len(row.source_files)
        return f"待识别：{count} 个文件" if count > 1 else "待识别"
    assets: list[str] = []
    raw_status = row.status
    if "表达矩阵已下载" in raw_status:
        assets.append("表达矩阵")
    if "metadata" in raw_status or "元数据" in raw_status:
        assets.append("样本信息")
    if "平台" in raw_status or metadata.get("platform_accessions"):
        assets.append("平台注释")
    if "tcga" in row.source_type_key:
        if str(metadata.get("download_status") or "") == "tcga_clinical_metadata_built":
            summary = metadata.get("tcga_clinical_summary")
            if isinstance(summary, dict):
                cases = int(summary.get("case_count") or 0)
                matched = int(summary.get("matched_case_count") or 0)
                survival = int(summary.get("survival_case_count") or 0)
                return f"clinical metadata（{cases} case / 匹配 {matched} case / OS {survival} case）"
            return "clinical metadata、case/sample mapping"
        if str(metadata.get("download_status") or "") == "tcga_expression_matrix_built":
            summary = metadata.get("tcga_expression_build_summary")
            if isinstance(summary, dict):
                samples = int(summary.get("sample_count") or 0)
                genes = int(summary.get("gene_count") or 0)
                return f"表达矩阵、样本信息（{samples} 样本 / {genes} 基因）"
            return "表达矩阵、样本信息、sample mapping"
        if str(metadata.get("analysis_gate_status") or "") == "waiting_b6_4_expression_matrix_build":
            summary = metadata.get("tcga_download_summary")
            if isinstance(summary, dict):
                acquired = int(summary.get("acquired_count") or 0)
                return f"TCGA 原始文件：{acquired} 个"
            return "TCGA 原始文件"
        if str(metadata.get("download_status") or "") == "tcga_gdc_download_plan_draft_created":
            return "下载计划草案"
        expected = metadata.get("expected_assets")
        if isinstance(expected, list) and expected:
            return "预计：" + "、".join(_user_asset_label(str(item)) for item in expected)
        return "待下载与构建"
    if "gtex" in row.source_type_key:
        if str(metadata.get("download_status") or "") == "gtex_expression_matrix_built":
            summary = metadata.get("gtex_expression_build_summary")
            if isinstance(summary, dict):
                return f"GTEx 表达矩阵（{int(summary.get('sample_count') or 0)} 样本 / {int(summary.get('gene_count') or 0)} 基因）"
            return "GTEx 表达矩阵、sample/donor metadata"
        if str(metadata.get("analysis_gate_status") or "") == "waiting_gtex_expression_matrix_build":
            summary = metadata.get("gtex_download_summary")
            if isinstance(summary, dict):
                return f"GTEx 原始文件：{int(summary.get('acquired_count') or 0)} 个"
            return "GTEx 原始文件"
        if str(metadata.get("download_status") or "") == "gtex_download_plan_draft_created":
            return "GTEx 下载计划草案"
        expected = metadata.get("expected_assets")
        if isinstance(expected, list) and expected:
            return "预计：" + "、".join(_user_asset_label(str(item)) for item in expected)
        return "待下载与构建"
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
        if "tcga" in row.source_type_key and str(metadata.get("download_status") or "") == "tcga_clinical_metadata_built":
            if str(metadata.get("mode") or "") == "project_clinical_preview_only":
                return "B6.4 表达矩阵构建后再做表达-临床映射"
            return "统一数据检查与准备；survival 仅进入 preflight"
        if "tcga" in row.source_type_key and str(metadata.get("download_status") or "") == "tcga_expression_matrix_built":
            return "统一数据检查与准备"
        if "tcga" in row.source_type_key and str(metadata.get("analysis_gate_status") or "") == "waiting_b6_4_expression_matrix_build":
            return "B6.4 表达矩阵构建"
        if "gtex" in row.source_type_key and str(metadata.get("download_status") or "") == "gtex_expression_matrix_built":
            return "统一数据检查与准备；不会自动作为 TCGA 对照"
        if "gtex" in row.source_type_key and str(metadata.get("analysis_gate_status") or "") == "waiting_gtex_expression_matrix_build":
            return "G6.3 表达矩阵构建"
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
    source_files = _recognition_source_files_from_payload(payload)
    return _json(
        {
            "数据来源": row.source_type,
            "GSE 编号或本地路径": row.location_tooltip or row.location,
            "当前项目绑定状态": payload.get("status", "未记录"),
            "下载状态": metadata.get("download_status", "未记录"),
            "已发现内容": _dataset_available_content(row, row.status, metadata),
            "缺失内容": _dataset_missing_content(row, row.status, metadata),
            "source_files": source_files,
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
    if entry.status in {"识别完成", "已导入", "已下载"} or entry.ready_for_recognition or "表达矩阵已构建" in entry.status:
        score = 3
    elif entry.status == "待识别" or "原始文件已获取" in entry.status or "clinical" in entry.status:
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
    if entry.source_type_key == "local_import":
        return ""
    return entry.technical_info if column in {3, 4, 5} else ""


def _dataset_batch_summary_text(entries: Iterable[DatasetListEntry]) -> str:
    summaries: list[str] = []
    seen: set[tuple[str, ...]] = set()
    for entry in entries:
        if entry.source_type_key not in {"local_import", *GEO_SOURCE_TYPES} or len(entry.source_files) <= 1:
            continue
        acquisition_key = entry.acquisition_ids or (entry.key,)
        if acquisition_key in seen:
            continue
        seen.add(acquisition_key)
        if entry.source_type_key == "local_import":
            summaries.append(f"本地导入批次摘要：{entry.batch_summary or _local_import_batch_summary(entry.source_files, entry.storage_policy, entry.status)}")
        else:
            summaries.append(f"GEO 下载批次摘要：{entry.batch_summary or _geo_download_batch_summary(entry.source_files, entry.accession or entry.name, entry.status)}")
    return "\n".join(summaries)


def _dataset_detail_summary(entry: DatasetListEntry) -> str:
    lines = [
        f"数据集编号或文件名：{entry.name}",
        f"标题：{entry.title or '暂无标题'}",
        f"摘要：{entry.abstract or '暂无摘要'}",
        f"关键词 / 疾病 / 组织 / 平台：{entry.keywords or '暂无关键词'}",
    ]
    if entry.source_type_key == "local_import":
        files = list(entry.source_files)
        storage = _storage_policy_text(entry.storage_policy)
        if entry.focused_source_file:
            focused_name = Path(entry.focused_source_file).name
            lines.extend(
                [
                    f"当前查看文件：{focused_name}",
                    f"文件来源状态：{entry.status}",
                    f"保存方式：{storage}",
                    f"批次摘要：{entry.batch_summary}",
                    "批次完整文件列表：",
                ]
            )
        else:
            lines.append("批次完整文件列表：")
        lines.extend(
            [
                f"文件总数：{len(files)} 个",
                f"文件来源状态：{entry.status}",
                f"保存方式：{storage}",
            ]
        )
        for index, raw_path in enumerate(files, start=1):
            lines.append(f"{index}. {Path(raw_path).name}｜{storage}｜{raw_path}")
    elif entry.source_type_key in GEO_SOURCE_TYPES and entry.focused_source_file:
        lines.extend(
            [
                f"当前查看文件：{Path(entry.focused_source_file).name}",
                f"文件来源状态：{entry.status}",
                f"批次摘要：{entry.batch_summary}",
                "下载批次完整文件列表：",
                f"文件总数：{len(entry.source_files)} 个",
            ]
        )
        for index, raw_path in enumerate(entry.source_files, start=1):
            lines.append(f"{index}. {Path(raw_path).name}｜GEO 下载文件｜{raw_path}")
    return "\n".join(lines)


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
    selected_sources: list[dict[str, object]] = []
    seen_sources: set[tuple[str, ...] | str] = set()
    for entry in entries:
        source_key: tuple[str, ...] | str = entry.acquisition_ids or entry.key
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        display_name = entry.name
        if entry.source_type_key == "local_import" and len(entry.source_files) > 1:
            display_name = f"本地导入批次：{len(entry.source_files)} 个文件"
        selected_sources.append(
            {
                "key": entry.key,
                "display_name": display_name,
                "source_type": entry.source_type_key,
                "source_files": list(entry.source_files),
                "source_file_count": len(entry.source_files),
            }
        )
    payload = {
        "schema_version": "biomedpilot.pending_recognition_selection.v1",
        "updated_at": _utc_now_iso(),
        "selected_keys": [entry.key for entry in entries],
        "selected_acquisition_ids": sorted({acquisition_id for entry in entries for acquisition_id in entry.acquisition_ids}),
        "selected_sources": selected_sources,
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
        paths.extend(_recognition_source_files_from_payload(payload))
    return list(dict.fromkeys(paths))


def _pending_data_check_rows(project_root: Path | None) -> list[RegisteredSourceRow]:
    rows = _registered_source_rows(project_root)
    if project_root is None:
        return []
    selection = _load_pending_recognition_selection(project_root)
    selected = [row for row in rows if _recognition_row_selected_by_context(row, selection)]
    return selected or [row for row in rows if row.source_files]


def _pending_data_check_paths(project_root: Path | None) -> list[str]:
    if project_root is None:
        return []
    return _recognition_paths_for_rows(project_root, _pending_data_check_rows(project_root))


def _pending_data_check_file_statuses(project_root: Path | None) -> list[dict[str, object]]:
    statuses: list[dict[str, object]] = []
    for row in _pending_data_check_rows(project_root):
        source = "GEO 下载" if row.source_type_key in GEO_SOURCE_TYPES else "本地导入"
        for raw_path in row.source_files:
            path = Path(raw_path)
            statuses.append(
                {
                    "file_name": path.name,
                    "file_suffix": path.suffix.lower() or "无后缀",
                    "source": source,
                    "source_file": raw_path,
                    "recognized_type": "unchecked",
                    "recognized_type_zh": "待识别",
                    "suggested_use": "待识别",
                    "available_content": "未检查",
                    "missing_content": "未检查",
                    "risk_notes": "",
                    "status": "unchecked",
                    "status_zh": "未检查",
                    "status_color": "gray",
                    "can_enter_standardization": False,
                }
            )
    return statuses


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
        return UnifiedDatasetCandidate(
            source="geo",
            accession_or_project=normalized,
            display_title=title,
            organism=str(metadata.get("organism") or "Homo sapiens"),
            disease="",
            tissue="",
            data_modality=str(metadata.get("data_modality") or "GEO dataset"),
            sample_count=metadata.get("sample_count") or "待确认",
            has_expression_matrix=False,
            has_sample_metadata=False,
            has_clinical_metadata=False,
            has_platform_annotation=bool(metadata.get("platform_accessions")),
            recommended_analyses=("data_recognition",),
            download_plan_available=True,
            score=55,
            warnings=tuple(str(item) for item in metadata.get("warnings", []) or []) if isinstance(metadata.get("warnings"), list) else (),
            source_specific_metadata={
                "title_en": title,
                "platform_accessions": metadata.get("platform_accessions", []),
                "geo_url": metadata.get("geo_url") or f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={normalized}",
                "query_used": metadata.get("query_used") or normalized,
                "match_reason": metadata.get("match_reason") or "待处理数据集记录",
            },
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


def _download_list_row_count(project_root: Path | None, rows: Iterable[RegisteredSourceRow]) -> int:
    count = 0
    for row in rows:
        status = _current_registered_row_status(project_root, row)
        if row.strategy == "plan_only" or "下载" in status or "清单" in status or "待补充" in status:
            count += 1
    return count


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
    selected_file_names: set[str] | None = None
    if project_root is not None:
        selection = load_gse_file_download_candidate_selection(project_root=project_root, accession=accession_or_project)
        if selection:
            selected_file_names = {
                str(row.get("file_name") or "")
                for row in selected_gse_file_download_candidates(selection)
                if str(row.get("file_name") or "")
            }
    for asset in manifest.get("assets", []) or []:
        if not isinstance(asset, dict):
            continue
        if asset.get("asset_type") not in {"series_matrix", "supplementary_file"}:
            continue
        if selected_file_names is not None and str(asset.get("file_name") or "") not in selected_file_names:
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
        values = _local_import_declared_files(payload)
        if len(values) > 1:
            return f"本地导入批次：{len(values)} 个文件"
        if values:
            return Path(str(values[0])).name
    if source_type in GEO_SOURCE_TYPES:
        return str(metadata.get("gse_id") or payload.get("source_label") or metadata.get("accession_or_project") or "未知 GSE")
    if source_type in {"tcga_project", "chinese_tcga_gdc_project"}:
        return str(metadata.get("project_id") or payload.get("source_label") or metadata.get("accession_or_project") or "未知 TCGA 项目")
    if source_type in {"gtex_tissue", "chinese_gtex_tissue"}:
        return str(metadata.get("tissue_name") or payload.get("source_label") or metadata.get("accession_or_project") or "未知 GTEx 组织")
    return str(payload.get("source_label") or metadata.get("accession_or_project") or "未知数据源")


def _registered_source_location(payload: dict[str, object], metadata: dict[str, object]) -> str:
    if str(payload.get("source_type") or "") == "local_import":
        values = _recognition_source_files_from_payload(payload)
        if len(values) > 1:
            return f"{len(values)} 个文件"
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
    if str(payload.get("source_type") or "") == "local_import":
        values = _recognition_source_files_from_payload(payload)
        if len(values) > 1:
            return "\n".join(values)
    for key in ("registered_files", "referenced_paths", "copied_files"):
        values = payload.get(key)
        if isinstance(values, list) and values:
            return str(values[0])
    return _registered_source_location(payload, metadata)


def _payload_string_list(payload: dict[str, object], key: str) -> list[str]:
    values = payload.get(key)
    if not isinstance(values, list):
        return []
    return [str(value) for value in values if str(value).strip()]


def _local_import_declared_files(payload: dict[str, object]) -> list[str]:
    return (
        _payload_string_list(payload, "source_files")
        or _payload_string_list(payload, "registered_files")
        or _payload_string_list(payload, "referenced_paths")
        or _payload_string_list(payload, "copied_files")
    )


def _recognition_source_files_from_payload(payload: dict[str, object]) -> list[str]:
    strategy = str(payload.get("strategy") or "")
    if strategy == "copy":
        return _payload_string_list(payload, "copied_files") or _local_import_declared_files(payload)
    if strategy == "reference":
        return _payload_string_list(payload, "referenced_paths") or _local_import_declared_files(payload)
    return _payload_string_list(payload, "copied_files") or _payload_string_list(payload, "referenced_paths") or _local_import_declared_files(payload)


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
        if download_status == "tcga_gdc_download_plan_draft_created":
            return "GDC metadata 预览完成，下载计划草案已创建"
        if download_status in {"tcga_gdc_raw_files_acquired", "tcga_gdc_raw_files_acquired_with_warnings", "tcga_gdc_files_downloaded", "tcga_gdc_files_downloaded_with_warnings"}:
            return "TCGA 原始文件已获取，等待 B6.4 构建表达矩阵"
        if download_status == "tcga_expression_matrix_built":
            return "TCGA 表达矩阵已构建，等待数据检查与准备"
        if download_status == "tcga_clinical_metadata_built":
            return "TCGA clinical metadata 已获取，等待数据检查与准备"
        if download_status == "gtex_download_manifest_created":
            return "GTEx 下载清单已创建，待下载表达矩阵"
        if download_status == "gtex_download_plan_draft_created":
            return "GTEx metadata 预览完成，下载计划草案已创建"
        if download_status in {"gtex_raw_files_acquired", "gtex_raw_files_acquired_with_warnings"}:
            return "GTEx 原始文件已获取，等待构建表达矩阵"
        if download_status == "gtex_expression_matrix_built":
            return "GTEx 表达矩阵已构建，等待数据检查与准备"
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
    if str(metadata.get("analysis_gate_status") or "") == "waiting_b6_4_expression_matrix_build":
        return False
    if str(metadata.get("ready_for_recognition") or "") == "pending_expression_matrix_build":
        return False
    if str(metadata.get("download_status") or "") == "tcga_clinical_metadata_built":
        return False
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
    return f"本地导入批次：{len(paths)} 个文件"


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
    next_step = "可以点击“继续：数据检查与准备”。" if summary.storage_policy != "plan_only" else "请导入已下载的 Series Matrix 文件，或等待后续版本接入自动下载。"
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
    if summary.source_type == "local_import" and len(summary.source_files) > 1:
        lines.append(f"文件总数：{len(summary.source_files)} 个")
        if summary.storage_policy == "copy":
            lines.append("文件来源状态：已复制到项目目录；识别阶段使用复制后的项目内文件。")
        elif summary.storage_policy == "reference":
            lines.append("文件来源状态：使用原文件位置；识别阶段引用原始文件，不复制。")
        else:
            lines.append(f"文件来源状态：{_storage_policy_text(summary.storage_policy)}")
        preview_names = "、".join(Path(path).name for path in summary.source_files[:3])
        remaining = len(summary.source_files) - 3
        lines.append(f"主界面摘要：{preview_names}" + (f"，另有 {remaining} 个文件" if remaining > 0 else ""))
        for index, raw_path in enumerate(summary.source_files, start=1):
            lines.append(f"{index}. {Path(raw_path).name}｜{raw_path}")
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


def _fetch_geo_accession_metadata(gse_id: str) -> str:
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


def _gse_preview_from_metadata(gse_id: str, metadata_text: str) -> GseDatasetPreview:
    values: dict[str, str] = {}
    for line in metadata_text.splitlines():
        if "：" not in line:
            continue
        key, value = line.split("：", 1)
        values[key.strip()] = value.strip() or "未记录"
    return GseDatasetPreview(
        gse_id=values.get("当前 GSE 编号", gse_id),
        title=values.get("数据集标题", "未记录"),
        platform=values.get("平台信息", "未记录"),
        sample_count=values.get("样本数", "未记录"),
        status="尚未添加",
    )


def _geo_candidate_from_gse_preview(preview: GseDatasetPreview) -> UnifiedDatasetCandidate:
    platform = preview.platform if preview.platform != "未记录" else ""
    platforms = [item.strip() for item in platform.replace(";", ",").split(",") if item.strip()]
    return UnifiedDatasetCandidate(
        source="geo",
        accession_or_project=preview.gse_id,
        display_title=preview.title,
        organism="Homo sapiens",
        disease="",
        tissue="",
        data_modality="GEO dataset",
        sample_count=preview.sample_count,
        has_expression_matrix=False,
        has_sample_metadata=False,
        has_clinical_metadata=False,
        has_platform_annotation=bool(platforms),
        recommended_analyses=("data_recognition",),
        download_plan_available=True,
        score=55,
        warnings=(),
        source_specific_metadata={
            "title_en": preview.title,
            "platform_accessions": platforms,
            "geo_url": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={preview.gse_id}",
            "match_reason": "GSE 编号精确匹配",
            "query_used": preview.gse_id,
        },
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
    platforms = metadata.get("platform_accessions") or metadata.get("platform_titles") or "未记录"
    if isinstance(platforms, list):
        platforms = ", ".join(str(item) for item in platforms) or "未记录"
    return [
        ["GSE 编号", candidate.accession_or_project],
        ["英文标题", candidate.display_title or "未记录"],
        ["数据来源", "GEO"],
        ["物种", candidate.organism or "未记录"],
        ["样本数", candidate.sample_count or "待确认"],
        ["平台 GPL", platforms],
        ["数据类型", candidate.data_modality or "待确认"],
        ["匹配原因", _candidate_match_reason(candidate)],
        ["分析潜力", _geo_candidate_potential_text(None, candidate)],
        ["GEO 链接", metadata.get("geo_url") or f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={candidate.accession_or_project}"],
    ]


def _geo_detail_english_text(candidate: UnifiedDatasetCandidate) -> str:
    metadata = candidate.source_specific_metadata
    lines = [
        f"英文标题：{metadata.get('title_en') or candidate.display_title or '未记录'}",
        f"英文摘要：{metadata.get('summary_en') or '未记录'}",
        f"样本信息：{metadata.get('sample_summary') or metadata.get('overall_design_en') or '未记录'}",
        f"样本数量：{candidate.sample_count or '待确认'}",
        f"平台信息：{metadata.get('platform_titles') or metadata.get('platform_accessions') or '未记录'}",
        f"实验类型：{candidate.data_modality or '待确认'}",
        f"原始关键词：{metadata.get('query_used') or metadata.get('executed_query') or '未记录'}",
        f"PMID/DOI/GEO link：{metadata.get('pmid') or metadata.get('doi') or metadata.get('geo_url') or '未记录'}",
    ]
    return "\n".join(lines)


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


def _geo_profile_user_display(profile: GeoDatasetProfile) -> str:
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


def _geo_download_candidate_use_text(row: dict[str, object]) -> str:
    use = str(row.get("recognition_use") or "")
    if use == "expression_matrix_candidate":
        return "适合进入 expression/metadata recognition；需标准化确认。"
    if use == "sample_metadata_candidate":
        return "适合进入样本注释 recognition；分组仍需用户确认。"
    if use == "platform_annotation_candidate":
        return "平台注释候选；不承诺已完成 ID 映射。"
    if use == "imported_deg_candidate":
        return "外部 DEG 结果候选；不是软件计算结果。"
    if use == "raw_heavy_risk_file":
        return "RAW/heavy 风险文件；不进入默认下载。"
    if use == "geo_metadata_container":
        return "GEO 元数据容器；用于样本/平台元数据识别。"
    return "下载后需先识别，再进入标准化确认。"


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
    input_text = "\n".join([text.title_en, text.summary_en, text.overall_design_en])
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
        return "可进入数据检查。"
    if candidate.source == "geo":
        if "已发现补充文件" in status or "表达矩阵待确认" in status or "表达矩阵待下载" in status:
            return "下载补充文件或 Series Matrix 后再进入数据检查与准备。"
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
        return "可识别"
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
            "source_files": list(summary.source_files),
            "copied_files": list(summary.copied_files),
            "referenced_paths": list(summary.referenced_paths),
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
    file_count = len(summary.source_files or summary.registered_files or summary.copied_files or summary.referenced_paths)
    next_step = "可以继续进入数据检查与准备。" if summary.strategy != "plan_only" and file_count else "当前只是获取计划或缺少实际文件，请补充本地文件后再继续。"
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
    return "检测到缺失信息：" + "、".join(missing) + "。请在待办清单中处理后点击“重新运行数据检查”。"


def _readiness_overall_summary(readiness: dict[str, object], matrix: dict[str, object], missing: set[str]) -> str:
    standardization_ready = bool(readiness.get("standardization_ready") or readiness.get("has_core_input"))
    rows = [row for row in matrix.get("rows", []) or [] if isinstance(row, dict)]
    runnable = [row for row in rows if row.get("can_run") and row.get("analysis_type") != "reporting"]
    if not standardization_ready:
        return "暂不能继续：还没有可用的表达矩阵。"
    if not readiness.get("deg_ready"):
        return "可以继续进入数据准备与标准化；需在标准化阶段确认分组后才能进行 DEG 分析。"
    if runnable and not missing:
        return "可以继续：关键输入已基本满足。"
    if runnable:
        return "基本可继续，但有信息需要补充。"
    return "可以继续进入数据准备与标准化。"


def _readiness_recognized_inputs_text(readiness: dict[str, object]) -> str:
    available = {str(item) for item in readiness.get("available_inputs", []) or []}
    labels = []
    for key in ("expression_matrix", "sample_metadata", "clinical_metadata", "platform_annotation", "gene_annotation", "comparison_config"):
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
    standardization_ready = bool(readiness.get("standardization_ready") or readiness.get("has_core_input"))
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
    if "expression_matrix" in missing or not standardization_ready:
        return "下一步建议：请返回数据导入页面补充表达矩阵文件。"
    if not readiness.get("deg_ready") and "comparison_config" in missing:
        return "下一步建议：可以继续进入数据准备与标准化；需在标准化阶段确认分组后才能进行 DEG 分析。"
    if "comparison_config" in missing and _group_preview_has_candidate(group_preview):
        return "下一步建议：已检测到候选分组，请确认比较组；也可以先进入标准化，之后再确认。"
    if "comparison_config" in missing and "sample_metadata" not in missing:
        return "下一步建议：建议先设置比较组，以便进行差异表达分析；也可以先进入标准化，之后再补充分组信息。"
    if "sample_metadata" in missing:
        return "下一步建议：请补充样本信息；如果暂时只做表达矩阵清洗，也可以先进入标准化。"
    if "clinical_metadata" in missing and missing <= {"clinical_metadata"}:
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
    order = ["expression_matrix", "sample_metadata", "comparison_config", "clinical_metadata"]
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
    if "gsea_gene_set_selection" in missing:
        return "选择 GSEA 基因集；不影响当前数据检查和 DEG preflight"
    if "clinical_metadata" in missing:
        return "上传临床信息，或暂不做相关分析"
    if row.get("can_run"):
        return "可直接继续"
    if row.get("analysis_type") == "reporting":
        return "先生成分析结果"
    return "查看说明"


def _deg_config_user_state(project_root: Path) -> dict[str, object]:
    recognition = load_recognition_report(project_root) or {}
    artifacts = load_standardization_artifacts(project_root)
    registry = artifacts.get("registry")
    assets = [item for item in (registry or {}).get("assets", []) or [] if isinstance(item, dict)] if isinstance(registry, dict) else []
    expression_assets = [item for item in assets if str(item.get("asset_type") or "") in {"raw_count_matrix", "expression_matrix", "normalized_expression_matrix"}]
    metadata_assets = [item for item in assets if str(item.get("asset_type") or "") in {"sample_metadata", "phenotype_metadata"}]
    imported_deg_assets = [item for item in assets if str(item.get("asset_type") or "") == "differential_result_table"]
    imported_deg_detected = bool(imported_deg_assets or _deg_recognition_has_imported_result(recognition if isinstance(recognition, dict) else {}))
    comparison_config = load_confirmed_comparison_config(project_root)
    expression_samples = expression_samples_from_recognition_report(recognition if isinstance(recognition, dict) else {})
    comparison_match = comparison_sample_match_status(comparison_config, expression_samples)
    group_sizes = dict(getattr(comparison_config, "group_sizes", {}) or {}) if comparison_config is not None else {}
    case_group = str(getattr(comparison_config, "case_group", "") or "")
    control_group = str(getattr(comparison_config, "control_group", "") or "")
    has_count = any(str(item.get("asset_type") or "") == "raw_count_matrix" for item in expression_assets)
    has_normalized = any(str(item.get("asset_type") or "") == "normalized_expression_matrix" for item in expression_assets)
    input_parts = [
        f"表达矩阵 {len(expression_assets)} 个",
        f"count matrix {'已找到' if has_count else '未确认'}",
        f"normalized matrix {'已找到' if has_normalized else '未确认'}",
        f"样本信息 {'已找到或可构建' if metadata_assets or comparison_config is not None else '未确认'}",
    ]
    if imported_deg_detected:
        input_parts.append("检测到 imported DEG，但不作为重新计算输入")
    if expression_samples:
        input_parts.append(f"识别到样本列 {len(expression_samples)} 个")
    expression_status = "已找到可校验表达矩阵" if expression_assets else "阻塞：缺 count matrix 或可用表达矩阵"
    metadata_status = "已找到或可由分组构建" if metadata_assets or comparison_config is not None else "阻塞：缺 sample metadata"
    if comparison_config is None:
        comparison_status = "阻塞：缺分组设计"
        comparison_summary = "比较设计：尚未确认 case/control 或用户比较。"
        next_step = "下一步建议：返回标准化页，确认分组与比较设计。"
    else:
        match_label = _sample_match_user_label(str(comparison_match.get("sample_id_match_status") or "not_checked"))
        comparison_status = f"已确认：{case_group or 'case'} vs {control_group or 'control'}"
        comparison_summary = (
            f"比较设计：{comparison_summary_text(comparison_config)}"
            f"样本匹配：{match_label}；每组样本数：{_group_sizes_text(group_sizes) or '待确认'}。"
        )
        if not expression_assets:
            next_step = "下一步建议：返回数据选择或标准化，补充可用表达矩阵。"
        elif str(comparison_match.get("sample_id_match_status") or "") == "mismatch":
            next_step = "下一步建议：修正样本名或重新确认分组与比较设计。"
        else:
            next_step = "下一步建议：生成 preflight 输入校验；通过后仍需后续真实执行器接入前审计。"
    return {
        "input_summary_zh": "当前分析输入：" + "；".join(input_parts) + "。",
        "comparison_summary_zh": comparison_summary,
        "expression_status_zh": expression_status,
        "metadata_status_zh": metadata_status,
        "comparison_status_zh": comparison_status,
        "next_step_zh": next_step,
        "developer_diagnostics": {
            "standardization_artifacts": artifacts,
            "expression_asset_count": len(expression_assets),
            "metadata_asset_count": len(metadata_assets),
            "imported_deg_detected": imported_deg_detected,
            "comparison_match": comparison_match,
        },
    }


def _deg_check_label(check_id: str) -> str:
    return {
        "expression_matrix": "表达矩阵",
        "sample_columns": "样本列",
        "sample_metadata": "样本信息",
        "group_design": "分组设计",
        "comparison_design": "比较设计",
        "case_control_non_empty": "case/control 样本",
        "sample_name_match": "样本名匹配",
        "numeric_matrix": "数值矩阵",
    }.get(check_id, check_id or "检查项")


def _deg_preflight_check_status_label(status: str) -> str:
    return {
        "passed": "通过",
        "blocked": "阻塞",
        "warning": "警告",
        "draft": "草稿",
    }.get(status, status or "未知")


def _sample_match_user_label(status: str) -> str:
    return {
        "matched": "完全匹配",
        "partial": "部分匹配",
        "mismatch": "不匹配",
        "not_checked": "未完成校验",
    }.get(status, status or "未完成校验")


def _group_sizes_text(group_sizes: dict[str, object]) -> str:
    return "、".join(f"{group} {count} 个" for group, count in group_sizes.items() if str(group))


def _deg_recognition_has_imported_result(recognition: dict[str, object]) -> bool:
    for item in recognition.get("files", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("recognized_type") or "") == "differential_result_table":
            return True
        if any(str(role) == "differential_result_table" for role in item.get("recognized_roles", []) or []):
            return True
        for asset in item.get("detected_assets", []) or []:
            if isinstance(asset, dict) and str(asset.get("asset_type") or asset.get("role") or "") == "differential_result_table":
                return True
    return False


def _analysis_task_user_rows(
    tasks: list[dict[str, object]],
    project_root: Path | None,
    result_entries: list[dict[str, object]],
    task_records: list[dict[str, object]],
) -> list[list[object]]:
    imported_deg = _analysis_imported_deg_detected(project_root)
    rows: list[list[object]] = []
    for task in tasks:
        task_type = str(task.get("task_type") or "")
        label = _analysis_task_display_label(task)
        status = _analysis_task_user_status(task, task_records, result_entries, imported_deg)
        required = _analysis_required_inputs_text(task_type)
        missing = _analysis_task_missing_text(task)
        next_step = _analysis_task_next_action(task, task_records, result_entries, imported_deg)
        rows.append([label, status, required, missing, next_step])
    return rows


def _analysis_task_display_label(task: dict[str, object]) -> str:
    task_type = str(task.get("task_type") or "")
    if task_type == "reporting":
        return "结果浏览与报告"
    return str(task.get("label") or task_type or "未命名任务")


def _analysis_task_user_status(
    task: dict[str, object],
    task_records: list[dict[str, object]],
    result_entries: list[dict[str, object]],
    imported_deg: bool,
) -> str:
    task_type = str(task.get("task_type") or "")
    if task_type == "differential_expression":
        if imported_deg and not task.get("can_run"):
            return "已有导入结果"
        if _analysis_has_result(result_entries, "differential_expression"):
            return "已有测试级结果"
        if task.get("can_run"):
            return "可配置"
        missing = {_normalize_missing_input(str(item)) for item in task.get("missing_inputs", []) or []}
        if "comparison_config" in missing:
            return "需要确认分组"
        return "需要补充信息"
    if task_type == "reporting":
        if result_entries:
            return "已有结果可浏览"
        return "需要先有结果"
    if task_type == "tcga_gtex_joint":
        return "测试级 / 暂不可用"
    if task_type == "immune_tme_scoring":
        if _analysis_has_result(result_entries, "immune_tme_scoring"):
            return "已有探索性评分"
        return "可配置" if task.get("can_run") else "需要合适表达矩阵"
    if _analysis_has_task_record(task_records, task_type):
        return "已有配置草稿"
    if task.get("can_run"):
        return "可配置"
    return "暂不可用" if not task.get("missing_inputs") else "需要补充信息"


def _analysis_required_inputs_text(task_type: str) -> str:
    return {
        "differential_expression": "表达矩阵、样本信息、分组设计",
        "enrichment": "表达矩阵或差异分析结果",
        "gsea": "表达矩阵、GSEA 基因集选择",
        "immune_tme_scoring": "TPM / 标准化表达矩阵、immune / TME signatures",
        "correlation": "表达矩阵、目标基因",
        "survival": "表达矩阵、临床/生存信息",
        "clinical_association": "临床信息",
        "tcga_gtex_joint": "TCGA 数据、GTEx 数据、批次校正方案",
        "reporting": "真实结果或明确标记的导入/测试级结果",
    }.get(task_type, "按任务配置补充输入")


def _analysis_task_missing_text(task: dict[str, object]) -> str:
    missing = [str(item) for item in task.get("missing_inputs", []) or []]
    if not missing:
        return "无"
    labels = []
    for item in missing:
        if "analysis_capability_matrix" in item:
            labels.append("请先完成数据准备检查")
        else:
            labels.append(_missing_input_label(item))
    return "、".join(dict.fromkeys(labels))


def _analysis_task_next_action(
    task: dict[str, object],
    task_records: list[dict[str, object]],
    result_entries: list[dict[str, object]],
    imported_deg: bool,
) -> str:
    task_type = str(task.get("task_type") or "")
    missing = {_normalize_missing_input(str(item)) for item in task.get("missing_inputs", []) or []}
    if task_type == "differential_expression":
        if imported_deg and not task.get("can_run"):
            return "当前为导入表格中的已有差异分析结果，不是本软件重新计算；可进入结果浏览或补充表达矩阵与分组。"
        if _analysis_has_result(result_entries, "differential_expression"):
            return "进入结果浏览；这些结果需按结果状态区分测试级或导入来源。"
        if "comparison_config" in missing:
            return "请先确认分组与比较设计。"
        if "expression_matrix" in missing:
            return "请返回数据选择或数据识别补充表达矩阵。"
        if task.get("can_run"):
            return "进入差异分析配置与 preflight；当前只做配置和输入校验，未执行真实分析。"
        return "补齐缺失输入后再配置差异分析。"
    if task_type == "enrichment":
        return "需要差异分析结果或基因列表；不要生成假富集结果。"
    if task_type == "gsea":
        return "先在 GSEA 基因集资源管理器选择本地资源；未选择只阻断 GSEA preflight / execution。"
    if task_type == "immune_tme_scoring":
        if _analysis_has_result(result_entries, "immune_tme_scoring"):
            return "进入结果浏览或重新运行 B7 评分；结果仍为探索性 bulk score。"
        if task.get("can_run"):
            return "进入免疫浸润 / TME评分；不执行 CIBERSORT/xCell/ESTIMATE，也不自动进入 DEG/GSEA/KM/Cox。"
        return "请补充 TPM / 标准化表达矩阵；raw counts / unknown 默认不能评分。"
    if task_type == "correlation":
        return "确认目标基因和样本数量后再配置。"
    if task_type == "survival":
        return "补充临床/生存信息后再配置。"
    if task_type == "clinical_association":
        return "补充临床信息后再配置。"
    if task_type == "tcga_gtex_joint":
        return "当前仅测试级准备，后续需正式批次校正方案。"
    if task_type == "reporting":
        if result_entries:
            return "进入结果浏览，确认结果状态后再生成报告。"
        return "先生成或导入明确标记的结果。"
    if _analysis_has_task_record(task_records, task_type):
        return "查看任务记录或继续补充参数。"
    return "查看缺失输入并返回标准化页面补充。"


def _analysis_task_input_summary(tasks: list[dict[str, object]]) -> str:
    diff = next((item for item in tasks if item.get("task_type") == "differential_expression"), None)
    if not isinstance(diff, dict):
        return "核心输入：尚未生成分析任务中心。"
    missing = _analysis_task_missing_text(diff)
    if diff.get("can_run"):
        return "核心输入：已具备表达矩阵、样本信息和分组设计，可进入 DEG 配置与 preflight。"
    return f"核心输入：差异表达分析仍缺少 {missing}。"


def _analysis_input_resolver_summary(resolver: dict[str, object]) -> str:
    packages = [item for item in resolver.get("packages", []) or [] if isinstance(item, dict)]
    if not packages:
        blockers = resolver.get("blockers", []) or []
        if blockers:
            return "Resolver：尚未形成可用 input package；阻断项：" + "、".join(str(item) for item in blockers[:3]) + "。"
        return "Resolver：尚未发现 standardized analysis input package。"
    ready = [item for item in packages if not item.get("blockers")]
    package_types = "、".join(str(item.get("package_type") or "") for item in packages if item.get("package_type"))
    blockers = _resolver_issue_preview(packages, "blockers")
    warnings = _resolver_issue_preview(packages, "warnings")
    disabled = "；formal DEG/GSEA/Survival/Plot/Report-ready 仍按阶段 gate 禁用"
    issue_text = ""
    if blockers:
        issue_text += f"；阻断：{blockers}"
    if warnings:
        issue_text += f"；提示：{warnings}"
    return f"Resolver：发现 {len(packages)} 个 input package（可进入预检查/探索 {len(ready)} 个）：{package_types}{issue_text}{disabled}。"


def _resolver_issue_preview(packages: list[dict[str, object]], field_name: str) -> str:
    issues: list[str] = []
    for package in packages:
        package_type = str(package.get("package_type") or "package")
        for issue in package.get(field_name, []) or []:
            if len(issues) >= 4:
                break
            issues.append(f"{package_type}:{issue}")
        if len(issues) >= 4:
            break
    return "、".join(issues)


def _analysis_ui_package_rows(rows: object) -> list[list[object]]:
    return [
        [
            row.get("package_label", ""),
            row.get("status", ""),
            row.get("value_type", ""),
            row.get("gene_id_type", ""),
            row.get("allowed_downstream_tasks", ""),
            row.get("blockers", ""),
            row.get("warnings", ""),
            row.get("repair_action", ""),
        ]
        for row in rows
        if isinstance(row, dict)
    ]


def _read_json_file(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _latest_full_integrated_markdown_package(project_root: Path) -> Path | None:
    package_root = project_root / "report_package" / "integrated"
    if not package_root.is_dir():
        return None
    candidates: list[tuple[float, Path]] = []
    for manifest_path in package_root.glob("*/integrated_report_package_manifest.json"):
        manifest = _read_json_file(manifest_path)
        package_dir = manifest_path.parent
        if (
            manifest.get("status") == "full_integrated_report_package_created"
            and manifest.get("section_scope") == "full_integrated_report"
            and manifest.get("export_format") == "markdown"
            and (package_dir / "integrated_report.md").is_file()
        ):
            candidates.append((manifest_path.stat().st_mtime, package_dir))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _legacy_default_selection_ids(repository_manifest: dict[str, object]) -> tuple[dict[str, str], list[str]]:
    assets = [asset for asset in repository_manifest.get("assets", []) or [] if isinstance(asset, dict)]
    if not assets:
        return {}, ["repository_manifest_has_no_assets"]
    selection: dict[str, str] = {}
    blockers: list[str] = []
    for kwarg, role, types, required in (
        ("expression_asset_id", "expression_matrix", {"raw_count_matrix", "expression_matrix", "normalized_expression_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}, True),
        ("sample_metadata_asset_id", "sample_metadata", {"sample_metadata", "phenotype_metadata", "tcga_sample_metadata", "gtex_sample_metadata"}, False),
        ("feature_annotation_asset_id", "feature_annotation", {"feature_annotation", "platform_annotation", "gene_annotation", "platform_reference_hint"}, False),
        ("clinical_asset_id", "clinical_metadata", {"clinical_metadata", "survival_metadata", "tcga_clinical_metadata"}, False),
        ("group_design_asset_id", "group_design", {"group_design"}, False),
    ):
        candidates = [
            asset
            for asset in assets
            if str(asset.get("asset_role") or "") == role or str(asset.get("asset_type") or "") in types or str(asset.get("repository") or "") in types
        ]
        if len(candidates) > 1:
            blockers.append(f"ambiguous_{role}_asset_selection")
            continue
        if candidates:
            selection[kwarg] = str(candidates[0].get("asset_id") or "")
        elif required:
            blockers.append(f"missing_{role}_asset")
    return selection, blockers


def _analysis_ui_legacy_pipeline_rows(state: object) -> list[list[object]]:
    if not isinstance(state, dict):
        return []
    rows = state.get("rows")
    if not isinstance(rows, list):
        return []
    table_rows: list[list[object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        issues = "；".join(str(item) for item in (row.get("blockers"), row.get("warnings")) if str(item) and str(item) != "None")
        table_rows.append(
            [
                row.get("label", ""),
                row.get("status", ""),
                row.get("artifact_path", ""),
                row.get("count_summary", ""),
                issues or "None",
                row.get("next_action", ""),
            ]
        )
    if table_rows:
        table_rows.append(
            [
                "Formal boundary",
                "disabled",
                "",
                "",
                "writes_analysis_input_repository=False；writes_result_index=False；report_ready_eligible=False",
                state.get("boundary_message", ""),
            ]
        )
    return table_rows


def _analysis_ui_action_rows(rows: object, *, normal_user_only: bool = False) -> list[list[object]]:
    visible_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if normal_user_only and row.get("normal_user_visible") is False:
            continue
        visible_rows.append(
            [
                row.get("label", ""),
                row.get("state", ""),
                row.get("button_behavior", ""),
                row.get("disabled_reason", ""),
                row.get("next_action", ""),
            ]
        )
    return visible_rows


def _analysis_ui_action(rows: object, action_id: str) -> dict[str, object]:
    for row in rows:
        if isinstance(row, dict) and row.get("action_id") == action_id:
            return row
    return {}


def _analysis_ui_dependency_rows(rows: object) -> list[list[object]]:
    return [
        [
            row.get("label", ""),
            row.get("status", ""),
            row.get("version", ""),
            row.get("blockers", ""),
            row.get("packaging_impact", ""),
            row.get("action", ""),
        ]
        for row in rows
        if isinstance(row, dict)
    ]


def _analysis_ui_gate_rows(rows: object) -> list[list[object]]:
    return [
        [
            row.get("gate", ""),
            row.get("status", ""),
            row.get("basis", ""),
            row.get("blockers", ""),
            row.get("warnings", ""),
        ]
        for row in rows
        if isinstance(row, dict)
    ]


def _survival_clinical_report_gate_row(gate_label: str, gate: dict[str, object]) -> list[object]:
    return [
        gate_label,
        gate.get("status", "blocked"),
        gate.get("selected_result_id", ""),
        gate.get("section_scope", ""),
        "；".join(str(item) for item in gate.get("blockers", []) or []),
        "；".join(str(item) for item in gate.get("warnings", []) or []),
    ]


def _analysis_ui_capability_rows(capability_map: object) -> list[list[object]]:
    if not isinstance(capability_map, dict):
        return []
    rows = capability_map.get("rows", [])
    return [
        [
            row.get("label", ""),
            row.get("category", ""),
            row.get("implementation_status", ""),
            row.get("ui_state", ""),
            "enabled" if row.get("formal_execution_enabled") else "disabled",
            "; ".join(str(item) for item in row.get("dependency_capability_keys", []) or []),
            row.get("reason", "") or row.get("boundary", ""),
        ]
        for row in rows
        if isinstance(row, dict)
    ]


def _analysis_ui_confirmation_rows(formal_state: object) -> list[list[object]]:
    if not isinstance(formal_state, dict):
        return [["Confirmation", "missing formal DEG gate state", "blocked"]]
    parameter = formal_state.get("parameter_gate") if isinstance(formal_state.get("parameter_gate"), dict) else {}
    confirmation = formal_state.get("parameter_confirmation") if isinstance(formal_state.get("parameter_confirmation"), dict) else {}
    dependency = parameter.get("dependency_snapshot") if isinstance(parameter.get("dependency_snapshot"), dict) else {}
    packages = dependency.get("packages") if isinstance(dependency.get("packages"), dict) else {}
    output_plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
    confirmation_gate = formal_state.get("confirmation_gate") if isinstance(formal_state.get("confirmation_gate"), dict) else {}
    return [
        [
            "Comparison",
            f"{parameter.get('case_group', '')} ({len(parameter.get('case_samples', []) or [])}) vs {parameter.get('control_group', '')} ({len(parameter.get('control_samples', []) or [])}); case={', '.join(parameter.get('case_samples', []) or [])}; control={', '.join(parameter.get('control_samples', []) or [])}",
            parameter.get("status", "blocked"),
        ],
        ["Method", parameter.get("method", ""), parameter.get("method_family", "")],
        [
            "Thresholds",
            f"log2FC={parameter.get('log2fc_threshold', '')}; p={parameter.get('p_value_threshold', '')}; FDR={parameter.get('fdr_threshold', '')}; pseudocount={parameter.get('pseudocount', '')}",
            parameter.get("fdr_policy", ""),
        ],
        ["Value type compatibility", f"{parameter.get('value_type', '')}; {parameter.get('value_type_policy', '')}", parameter.get("gene_mapping_policy", "")],
        [
            "Dependency snapshot",
            "; ".join(f"{name}={status.get('version', '')}" for name, status in packages.items() if isinstance(status, dict) and name in {"numpy", "pandas", "scipy", "statsmodels"}),
            dependency.get("status", "blocked"),
        ],
        [
            "Output plan",
            f"task_run_id={output_plan.get('task_run_id', 'not confirmed')}; result={output_plan.get('result_table_path', 'not confirmed')}; log={output_plan.get('task_run_log_path', 'not confirmed')}",
            confirmation.get("status", "not confirmed"),
        ],
        ["Confirmation gate", "; ".join(str(item) for item in confirmation_gate.get("blockers", []) or []) if isinstance(confirmation_gate.get("blockers"), list | tuple) else "None", confirmation_gate.get("status", "blocked")],
    ]


def _analysis_ui_survival_rows(rows: object) -> list[list[object]]:
    return [
        [
            row.get("label", ""),
            row.get("status", ""),
            row.get("asset_status", ""),
            row.get("backend_status", ""),
            row.get("disabled_reason", ""),
            row.get("warnings", ""),
        ]
        for row in rows
        if isinstance(row, dict)
    ]


def _analysis_task_result_summary(entries: list[dict[str, object]], records: list[dict[str, object]], imported_deg: bool) -> str:
    if entries:
        imported_count = sum(1 for item in entries if _analysis_entry_semantics(item) == "imported result")
        testing_count = sum(1 for item in entries if _analysis_entry_semantics(item) == "testing-level")
        real_count = sum(1 for item in entries if _analysis_entry_semantics(item) == "real computed result")
        parts = [f"结果 {len(entries)} 个"]
        if imported_count:
            parts.append(f"导入结果 {imported_count} 个")
        if testing_count:
            parts.append(f"测试级结果 {testing_count} 个")
        if real_count:
            parts.append(f"真实计算结果 {real_count} 个")
        return "结果状态：" + "；".join(parts) + "。"
    if imported_deg:
        return "结果状态：识别到导入差异分析表格；这不是本软件重新计算的 DEG。"
    if records:
        return f"结果状态：已有 {len(records)} 个配置草稿，尚未产生结果。"
    return "结果状态：暂无结果。"


def _analysis_task_next_step(tasks: list[dict[str, object]], entries: list[dict[str, object]], records: list[dict[str, object]], imported_deg: bool) -> str:
    diff = next((item for item in tasks if item.get("task_type") == "differential_expression"), {})
    if entries:
        return "下一步建议：进入结果浏览，确认每个结果是导入、测试级还是真实计算。"
    if imported_deg:
        return "下一步建议：进入结果浏览或补充原始表达矩阵与分组；导入 DEG 不等于本软件计算结果。"
    if isinstance(diff, dict) and diff.get("can_run"):
        return "下一步建议：进入差异分析配置与 preflight；当前不会执行真实 DEG。"
    if records:
        return "下一步建议：继续补充任务参数或返回标准化页确认输入。"
    return "下一步建议：返回数据标准化或确认分组与比较设计。"


def _analysis_has_task_record(records: list[dict[str, object]], task_type: str) -> bool:
    return any(str(item.get("task_type") or "") == task_type for item in records)


def _analysis_has_result(entries: list[dict[str, object]], analysis_type: str) -> bool:
    return any(str(item.get("analysis_type") or "") == analysis_type for item in entries)


def _tsv_rows(path_text: str, *, limit: int = 8, columns: list[str] | None = None) -> list[list[object]]:
    import csv

    path = Path(str(path_text or "")).expanduser()
    if not path.is_file():
        return []
    rows: list[list[object]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        selected = columns or list(reader.fieldnames or [])
        for index, row in enumerate(reader):
            if index >= limit:
                break
            rows.append([str(row.get(column, "")) for column in selected])
    return rows


def _signature_from_catalog_item(item: dict[str, object]) -> object:
    return signature_from_dict(item)


def _analysis_entry_semantics(entry: dict[str, object]) -> str:
    explicit = str(entry.get("result_semantics") or entry.get("execution_level") or entry.get("status") or "").lower()
    if "dry" in explicit or "preflight" in explicit:
        return "dry-run"
    if "configured" in explicit or "not_run" in explicit or "not run" in explicit:
        return "configured-not-run"
    if "import" in explicit or "导入" in explicit:
        return "imported result"
    if "real" in explicit or "computed" in explicit and "testing" not in explicit:
        return "real computed result"
    if "testing" in explicit or "preview" in explicit or "generated" in explicit:
        return "testing-level"
    return "testing-level"


def _result_entries_for_display(project_root: Path | None, payload: dict[str, object]) -> list[dict[str, object]]:
    entries = [dict(item) for item in payload.get("entries", []) or [] if isinstance(item, dict)]
    if project_root is None:
        return entries
    seen_paths = {str(item.get("path") or item.get("file_path") or "") for item in entries if str(item.get("path") or item.get("file_path") or "")}
    recognition = load_recognition_report(project_root)
    if isinstance(recognition, dict):
        for item in recognition.get("files", []) or []:
            if not isinstance(item, dict) or str(item.get("recognized_type") or "") != "differential_result_table":
                continue
            path_text = str(item.get("original_path") or item.get("route_path") or "")
            if path_text and path_text in seen_paths:
                continue
            entries.append(
                {
                    "result_id": f"recognition-imported-deg-{len(entries) + 1}",
                    "result_name": f"导入差异分析表格：{item.get('file_name') or '未命名表格'}",
                    "result_type": "导入结果",
                    "analysis_type": "differential_expression",
                    "file_type": "table",
                    "path": path_text,
                    "source_label": "用户导入 / 外部差异分析结果",
                    "status": "imported",
                    "result_semantics": "imported result",
                    "report_candidate": True,
                    "report_usage_label": "可进入报告草稿，必须标明导入来源",
                    "generated_at": str(item.get("generated_at") or ""),
                    "short_description": "用户导入的外部 DEG 表；需要确认列映射后用于报告草稿。",
                    "display_action": "查看详情",
                    "warning": "导入表格中的已有差异分析结果，不是本软件重新计算。",
                    "_display_source": "recognition_imported_deg",
                }
            )
            if path_text:
                seen_paths.add(path_text)
    return entries


def _results_user_rows(project_root: Path | None, entries: list[dict[str, object]], records: list[dict[str, object]]) -> list[list[object]]:
    rows = [
        [
            _result_display_name(entry),
            _result_type_label(entry),
            _result_source_label(entry),
            _result_status_label(entry),
            _result_report_label(entry),
            _result_generated_at_label(entry),
            _result_short_description_label(entry),
            str(entry.get("display_action") or "查看详情"),
        ]
        for entry in entries
    ]
    for record in records:
        rows.append(
            [
                str(record.get("label") or "分析任务配置"),
                "配置草稿",
                _task_record_source_label(record),
                _task_record_status_label(record),
                "否",
                str(record.get("created_at") or ""),
                "任务已配置但尚未执行。",
                "已配置但尚未运行；请返回分析任务中心继续配置或满足执行条件。",
            ]
        )
    return rows


def _result_display_name(entry: dict[str, object]) -> str:
    return str(entry.get("result_name") or entry.get("name") or "未命名结果")


def _result_type_label(entry: dict[str, object]) -> str:
    explicit = str(entry.get("result_type") or "")
    if explicit:
        return explicit
    analysis_type = str(entry.get("analysis_type") or "")
    semantics = _analysis_entry_semantics(entry)
    if semantics == "imported result":
        return "导入结果"
    if semantics == "testing-level":
        return "测试级结果"
    if semantics == "configured-not-run":
        return "配置草稿"
    if semantics == "real computed result":
        return "真实计算结果"
    if "preflight" in analysis_type:
        return "输入检查"
    return "分析结果"


def _result_source_label(entry: dict[str, object]) -> str:
    semantics = _analysis_entry_semantics(entry)
    if semantics == "imported result":
        return "导入表格中的已有差异分析结果，不是本软件重新计算。"
    if semantics == "testing-level":
        return "测试级 / 开发者预览结果，不等于正式科研结果。"
    if semantics == "dry-run":
        return "流程记录 / dry-run，未执行真实分析。"
    if semantics == "configured-not-run":
        return "已配置，尚未运行。"
    if semantics == "real computed result":
        return "真实计算结果。"
    return "结果来源待确认。"


def _result_status_label(entry: dict[str, object]) -> str:
    semantics = _analysis_entry_semantics(entry)
    warning = str(entry.get("warning") or "")
    if "文件缺失" in warning:
        return "文件缺失"
    return {
        "imported result": "导入结果",
        "testing-level": "测试级",
        "dry-run": "dry-run / 未执行",
        "configured-not-run": "已配置未运行",
        "real computed result": "真实计算结果",
    }.get(semantics, "待确认")


def _result_openable_label(project_root: Path | None, entry: dict[str, object]) -> str:
    path_text = str(entry.get("path") or entry.get("file_path") or "")
    if not path_text:
        return "否"
    path = Path(path_text).expanduser()
    if project_root is not None and not path.is_absolute():
        path = project_root / path
    return "是" if path.exists() else "否，文件缺失"


def _result_report_label(entry: dict[str, object]) -> str:
    semantics = _analysis_entry_semantics(entry)
    if semantics == "real computed result":
        return "可"
    if semantics == "imported result":
        return "可，需标明导入"
    if semantics == "testing-level":
        return "可，需标明测试级"
    return "否"


def _result_generated_at_label(entry: dict[str, object]) -> str:
    return str(entry.get("generated_at") or entry.get("created_at") or "未记录")


def _result_short_description_label(entry: dict[str, object]) -> str:
    text = str(entry.get("short_description") or "").strip()
    if text:
        return text
    return _result_next_step_label(entry)


def _result_next_step_label(entry: dict[str, object]) -> str:
    semantics = _analysis_entry_semantics(entry)
    if semantics == "imported result":
        return "可查看或进入报告草稿，但必须标注为导入结果。"
    if semantics == "testing-level":
        return "可用于内部测试报告草稿，不可写成正式科研结论。"
    if semantics == "dry-run":
        return "请先完成配置并满足执行条件。"
    if semantics == "configured-not-run":
        return "请返回分析任务中心继续配置或运行前检查。"
    if semantics == "real computed result":
        return "可进入报告草稿；仍需人工核对。"
    return "先确认结果来源。"


def _task_record_source_label(record: dict[str, object]) -> str:
    execution = str(record.get("execution") or "")
    if execution in {"not_run", "not run", ""}:
        return "配置草稿 / 未执行真实分析。"
    if "dry" in execution:
        return "流程记录 / dry-run，未执行真实分析。"
    return "任务记录，结果状态需人工确认。"


def _task_record_status_label(record: dict[str, object]) -> str:
    execution = str(record.get("execution") or "")
    status = str(record.get("status") or "")
    if execution in {"not_run", "not run", ""} or status == "created":
        return "已配置，尚未运行"
    if "dry" in execution:
        return "dry-run / 未执行"
    return "任务记录"


def _results_page_source_summary(entries: list[dict[str, object]], records: list[dict[str, object]]) -> str:
    if not entries and not records:
        return "当前结果：暂无结果或任务记录。"
    counts = _result_semantics_counts(entries)
    parts = [f"可查看结果 {len(entries)} 个"]
    if counts.get("imported result"):
        parts.append(f"导入结果 {counts['imported result']} 个")
    if counts.get("testing-level"):
        parts.append(f"测试级结果 {counts['testing-level']} 个")
    if counts.get("dry-run"):
        parts.append(f"dry-run {counts['dry-run']} 个")
    if counts.get("real computed result"):
        parts.append(f"真实计算结果 {counts['real computed result']} 个")
    if records:
        parts.append(f"配置草稿 {len(records)} 个")
    return "当前结果：" + "；".join(parts) + "。"


def _results_page_report_summary(entries: list[dict[str, object]], records: list[dict[str, object]]) -> str:
    reportable = [entry for entry in entries if _analysis_entry_semantics(entry) in {"imported result", "testing-level", "real computed result"}]
    if reportable:
        return f"报告适用性：{len(reportable)} 个结果可进入报告草稿，但必须保留导入/测试级/真实计算标签。"
    if records:
        return "报告适用性：当前只有配置草稿或 dry-run，不适合生成结果报告。"
    return "报告适用性：暂无可用于报告草稿的结果。"


def _results_page_next_step(entries: list[dict[str, object]], records: list[dict[str, object]]) -> str:
    if entries:
        return "下一步建议：查看报告草稿，并在报告中保留每个结果的来源标签。"
    if records:
        return "下一步建议：返回分析任务中心继续配置；当前记录未产生真实结果。"
    return "下一步建议：返回分析任务中心，创建配置草稿或导入明确标记的结果。"


def _result_semantics_counts(entries: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        key = _analysis_entry_semantics(entry)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _report_draft_status_text(markdown: str, manifest: object) -> str:
    if markdown:
        return "报告状态：已生成 Markdown 报告草稿；本阶段不导出 Word 或 PDF。"
    if manifest:
        return "报告状态：找到报告 manifest，但尚未读取到 Markdown 草稿。"
    return "报告状态：尚未生成报告草稿。"


def _report_result_semantics_text(entries: list[dict[str, object]], records: list[dict[str, object]]) -> str:
    if not entries and not records:
        return "结果语义：暂无结果。"
    counts = _result_semantics_counts(entries)
    parts = []
    for key, label in (
        ("imported result", "导入结果"),
        ("testing-level", "测试级结果"),
        ("dry-run", "dry-run"),
        ("configured-not-run", "已配置未运行"),
        ("real computed result", "真实计算结果"),
    ):
        if counts.get(key):
            parts.append(f"{label} {counts[key]} 个")
    if records:
        parts.append(f"配置草稿 {len(records)} 个")
    return "结果语义：" + ("；".join(parts) if parts else "待确认") + "。"


def _report_next_step_text(markdown: str, entries: list[dict[str, object]], records: list[dict[str, object]]) -> str:
    if markdown and entries:
        return "下一步建议：人工核对报告草稿，确认导入、测试级和未运行内容没有被写成正式结论。"
    if entries:
        return "下一步建议：生成报告草稿，并保留每个结果的来源标签。"
    if records:
        return "下一步建议：当前只有配置草稿，先返回分析任务中心或结果浏览。"
    return "下一步建议：先返回结果浏览或分析任务中心。"


def _report_section_rows(project_root: Path | None, entries: list[dict[str, object]], records: list[dict[str, object]], has_markdown: bool) -> list[list[object]]:
    acquisition = load_latest_acquisition_summary(project_root) if project_root is not None else None
    recognition = load_recognition_report(project_root) if project_root is not None else {}
    readiness = load_readiness_artifacts(project_root).get("readiness_report") if project_root is not None else {}
    standardization = load_standardization_artifacts(project_root).get("analysis_ready_manifest") if project_root is not None else {}
    comparison = load_confirmed_comparison_config(project_root) if project_root is not None else None
    recognition_files = len(recognition.get("files", []) or []) if isinstance(recognition, dict) else 0
    result_summary = _report_result_semantics_text(entries, records).replace("结果语义：", "")
    return [
        ["项目信息", "可写入草稿", "当前项目元信息", "Developer Preview / internal beta；不是临床或投稿级报告。"],
        ["数据来源", "已记录" if acquisition else "缺失", acquisition.source_label if acquisition else "尚未记录数据来源", "缺失时请返回数据选择。"],
        ["数据识别", "已生成" if recognition_files else "缺失", f"识别文件 {recognition_files} 个", "识别结果只描述文件类型，不代表分析结论。"],
        ["数据标准化", "已生成" if isinstance(standardization, dict) and standardization.get("exists") else "缺失", "标准化数据状态", "当前仍是资产注册与轻量校验，不等于正式 normalization。"],
        ["分组与比较设计", "已确认" if comparison is not None else "待确认", comparison_summary_text(comparison) if comparison is not None else "尚未确认比较设计", "缺分组时不能把 DEG 写成已执行。"],
        ["分析任务状态", f"配置草稿 {len(records)} 个" if records else "暂无配置草稿", "analysis task records", "配置草稿或 dry-run 不等于真实结果。"],
        ["已有结果", f"结果 {len(entries)} 个" if entries else "暂无结果", result_summary, "导入和测试级结果必须在报告中保留标签。"],
        ["报告草稿", "已生成" if has_markdown else "尚未生成", "Markdown 报告草稿", "不得自动生成医学结论或临床建议。"],
    ]


def _report_user_preview_text(markdown: str, entries: list[dict[str, object]], records: list[dict[str, object]]) -> str:
    lines = [
        "报告草稿预览",
        _report_result_semantics_text(entries, records),
        "说明：报告草稿仅用于内部测试和人工核对，不代表 production-ready、clinical-grade 或 submission-grade 输出。",
        "报告应包含：项目信息、数据来源、数据识别、数据标准化、分组与比较设计、分析任务状态、已有结果、注意事项。",
    ]
    if not markdown:
        lines.append("当前尚未生成 Markdown 报告草稿。")
    else:
        lines.append("以下为中文 Markdown 报告草稿预览。")
        lines.append("")
        lines.append(markdown)
    if any(_analysis_entry_semantics(entry) == "imported result" for entry in entries):
        lines.append("导入结果必须写明来自外部表格，不是本软件重新计算。")
    if any(_analysis_entry_semantics(entry) == "testing-level" for entry in entries):
        lines.append("测试级结果只能作为 Developer Preview / 内部测试材料。")
    if records:
        lines.append("配置草稿或 dry-run 记录不应写成真实分析结论。")
    return "\n".join(lines)


def _analysis_imported_deg_detected(project_root: Path | None) -> bool:
    if project_root is None:
        return False
    recognition = load_recognition_report(project_root)
    if isinstance(recognition, dict):
        for item in recognition.get("files", []) or []:
            if isinstance(item, dict) and str(item.get("recognized_type") or "") == "differential_result_table":
                return True
    result_index = load_result_index(project_root)
    for entry in result_index.get("entries", []) or []:
        if isinstance(entry, dict) and str(entry.get("analysis_type") or "") == "differential_expression" and _analysis_entry_semantics(entry) == "imported result":
            return True
    return False


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
        return "尚未生成样本与分组预览。"
    status = str(preview.get("status") or "")
    if status == "confirmed_comparison_exists":
        status_line = "状态：已存在正式比较组设置。"
    elif _group_preview_has_candidate(preview):
        status_line = "状态：已生成候选分组，正式比较组需由你确认。"
    else:
        reason = str(preview.get("missing_group_reason") or "未识别到明确分组，请在下一步手动设置比较组。")
        return "\n".join(
            [
                f"样本数：{int(preview.get('sample_count') or 0)}",
                "识别到的候选分组：无",
                "分组数量：0 组",
                "置信度：低",
                f"状态说明：{reason}",
                "这是系统根据样本信息生成的分组预览，正式比较组需由你确认。",
            ]
        )
    group_sizes = preview.get("group_sizes") if isinstance(preview.get("group_sizes"), dict) else {}
    size_text = "，".join(f"{key} {value}" for key, value in group_sizes.items()) if group_sizes else "未统计"
    fields = "、".join(str(item) for item in preview.get("candidate_group_fields", []) or []) or "未识别"
    return "\n".join(
        [
            f"样本数：{int(preview.get('sample_count') or 0)}",
            f"识别到的候选分组：{fields}",
            f"分组数量：{int(preview.get('group_count') or 0)} 组",
            f"每组样本数：{size_text}",
            f"置信度：{_group_preview_confidence_zh(str(preview.get('confidence') or 'low'))}",
            status_line,
            "这是系统根据样本信息生成的分组预览，正式比较组需由你确认。",
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
            if normalized in {"sample_metadata", "clinical_metadata", "expression_matrix", "comparison_config"}:
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
        "gsea_gene_set_selection": "gsea_gene_set_selection",
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
        "gsea_gene_set_selection": "GSEA 基因集选择",
        "platform_annotation": "平台注释",
        "gene_annotation": "基因注释",
    }.get(normalized, "其他缺失资产")


def _friendly_readiness_text(text: str) -> str:
    return (
        text.replace("无表达矩阵。", "缺少表达矩阵")
        .replace("样本信息缺失。", "缺少样本信息")
        .replace("临床信息缺失。", "缺少临床信息")
        .replace("comparison_config", "比较分组")
        .replace("gmt_gene_set", "GSEA 基因集")
        .replace("gsea_gene_set_selection", "GSEA 基因集选择")
        .replace("。", "")
    )


def _data_check_status_badge(item: dict[str, object]) -> str:
    color = str(item.get("status_color") or "gray")
    label = str(item.get("status_zh") or item.get("status") or "未检查")
    prefix = {
        "gray": "灰色",
        "green": "绿色",
        "yellow": "黄色",
        "red": "红色",
    }.get(color, "灰色")
    return f"{prefix}：{label}"


def _data_check_file_action(item: dict[str, object]) -> str:
    color = str(item.get("status_color") or "gray")
    recognized = str(item.get("recognized_type") or "")
    if color == "gray":
        return "运行数据检查"
    if recognized == "differential_result_table":
        return "作为导入结果查看"
    if recognized == "raw_heavy_file" or color == "red":
        return "排除或替换"
    if color == "yellow":
        return "确认用途 / 补充信息"
    return "可进入标准化确认"


def _dataset_readiness_user_rows(summary: dict[str, object]) -> list[list[str]]:
    if not summary:
        return [
            ["表达矩阵", "未检查", "尚未运行数据检查。"],
            ["样本 metadata", "未检查", "尚未运行数据检查。"],
            ["GSEA 基因集", "未选择", "不影响当前数据检查、标准化准备或 DEG preflight。"],
        ]
    rows = [
        ["可用 expression matrix", _yes_no(summary.get("has_expression_matrix")), "标准化确认的核心输入。"],
        ["sample metadata", _yes_no(summary.get("has_sample_metadata")), "用于样本信息、分组候选和样本匹配。"],
        ["group design / 推荐分组", _group_design_dataset_status(summary), "推荐分组必须由用户确认后才能写入 group design。"],
        ["species 信息", _known_unknown(summary.get("species")), str(summary.get("species") or "unknown")],
        ["gene ID 类型", _known_unknown(summary.get("gene_id_type")), str(summary.get("gene_id_type") or "unknown")],
        ["platform annotation", _platform_annotation_dataset_status(summary), "probe_id 或 unknown ID 时需要平台注释确认映射。"],
        ["imported DEG", "存在" if summary.get("imported_deg_present") else "未检测到", str(summary.get("imported_deg_note") or "imported DEG 不作为重新计算输入。")],
        ["进入标准化确认", _yes_no(summary.get("can_enter_standardization_confirmation")), "数据检查完成后才进入标准化确认，不代表标准化已完成。"],
        ["进入 DEG preflight", _yes_no(summary.get("can_enter_deg_preflight")), "需要表达矩阵、样本信息和已确认比较组。"],
        ["GSEA 数据基础", _yes_no(summary.get("has_gsea_data_basis")), "GSEA gene set 未选择不阻断当前数据检查和 DEG preflight。"],
    ]
    tcga = summary.get("tcga_readiness") if isinstance(summary.get("tcga_readiness"), dict) else {}
    if tcga and tcga.get("has_tcga_b6_4_build"):
        rows.extend(
            [
                ["TCGA B6.4 构建产物", str(tcga.get("status") or "unknown"), f"{tcga.get('sample_count') or 0} 样本 / {tcga.get('gene_count') or 0} 基因。"],
                ["TCGA 默认分组候选", str(tcga.get("default_group_status") or "unknown"), "Primary Tumor vs Solid Tissue Normal；仍需用户确认比较组。"],
                ["TCGA DEG 值类型", str(tcga.get("deg_input_value_type") or "count"), "raw counts 用于 DEG preflight；TPM/FPKM/FPKM-UQ 仅默认展示。"],
            ]
        )
    tcga_clinical = summary.get("tcga_clinical_readiness") if isinstance(summary.get("tcga_clinical_readiness"), dict) else {}
    if tcga_clinical and tcga_clinical.get("has_tcga_clinical_build"):
        rows.extend(
            [
                ["TCGA clinical metadata", str(tcga_clinical.get("clinical_gate_status") or "clinical_unavailable"), f"{tcga_clinical.get('case_count') or 0} case；匹配 {tcga_clinical.get('matched_case_count') or 0} case。"],
                ["表达-临床映射", str(tcga_clinical.get("mode") or "unknown"), f"{tcga_clinical.get('matched_sample_count') or 0}/{tcga_clinical.get('sample_count') or 0} sample 已匹配 clinical。"],
                ["TCGA 基础 OS readiness", str(tcga_clinical.get("survival_gate_status") or "survival_unavailable"), f"OS 可用 {tcga_clinical.get('survival_case_count') or 0} case；死亡事件 {tcga_clinical.get('death_event_count') or 0}。不自动运行 survival，不生成临床结论。"],
            ]
        )
    gtex = summary.get("gtex_readiness") if isinstance(summary.get("gtex_readiness"), dict) else {}
    if gtex and gtex.get("has_gtex_expression_build"):
        rows.extend(
            [
                ["GTEx G6 构建产物", str(gtex.get("status") or "gtex_expression_matrix_built"), f"{gtex.get('sample_count') or 0} 样本 / {gtex.get('donor_count') or 0} donor / {gtex.get('gene_count') or 0} 基因。"],
                ["GTEx TCGA 边界", str(gtex.get("tcga_default_control_status") or "disabled"), "GTEx 不自动作为 TCGA normal control；TCGA+GTEx 需要显式联合配置。"],
                ["GTEx 值类型", str(gtex.get("value_type") or "expression_values"), "作为独立正常组织表达资源进入数据检查；不默认进入 TCGA DEG/GSEA 执行。"],
            ]
        )
    return rows


def _yes_no(value: object) -> str:
    return "是" if bool(value) else "否"


def _known_unknown(value: object) -> str:
    text = str(value or "").strip()
    return "已识别" if text and text != "unknown" else "待确认"


def _group_design_dataset_status(summary: dict[str, object]) -> str:
    if summary.get("has_group_design"):
        return "已确认"
    if summary.get("has_recommended_group"):
        return "有推荐，待确认"
    return "未检测到"


def _platform_annotation_dataset_status(summary: dict[str, object]) -> str:
    if not summary.get("needs_platform_annotation"):
        return "非必须"
    return "已提供" if summary.get("has_platform_annotation") else "需要确认"


def _group_recommendation_detail_text(preview: dict[str, object]) -> str:
    if not _group_preview_has_candidate(preview):
        return _group_preview_user_summary(preview)
    comparison_text = _comparison_config_text_from_group_preview(preview).strip().splitlines()
    values = comparison_text[1].split("\t") if len(comparison_text) > 1 else ["case_vs_control", "", "case", "control"]
    comparison_name = values[0] if len(values) > 0 else "case_vs_control"
    case_group = values[2] if len(values) > 2 else "case"
    control_group = values[3] if len(values) > 3 else "control"
    group_sizes = preview.get("group_sizes") if isinstance(preview.get("group_sizes"), dict) else {}
    assignments = preview.get("sample_group_assignments") if isinstance(preview.get("sample_group_assignments"), dict) else {}
    case_samples = _group_sample_preview(assignments, case_group)
    control_samples = _group_sample_preview(assignments, control_group)
    field = str(preview.get("selected_preview_field") or "")
    return "\n".join(
        [
            f"推荐分组：{case_group} vs {control_group}",
            f"推荐比较名称：{comparison_name}",
            f"Case：{case_group}，{int(group_sizes.get(case_group, 0) or 0)} 个样本",
            f"Case 样本预览：{case_samples or '未记录'}",
            f"Control：{control_group}，{int(group_sizes.get(control_group, 0) or 0)} 个样本",
            f"Control 样本预览：{control_samples or '未记录'}",
            f"依据字段：{evidence_field_label_zh(field) if field else '未记录'}",
            f"置信度：{_group_preview_confidence_zh(str(preview.get('confidence') or 'low'))}",
            "状态：需要用户确认；确认前不会写入正式 group design / standardization confirmation。",
        ]
    )


def _group_sample_preview(assignments: dict[object, object], group: str) -> str:
    samples = [str(sample) for sample, value in assignments.items() if str(value) == group]
    preview = "、".join(samples[:5])
    if len(samples) > 5:
        preview = f"{preview} 等 {len(samples)} 个样本"
    return preview


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


def _standardization_candidate_list(candidates: dict[str, object], key: str) -> list[dict[str, object]]:
    values = candidates.get(key)
    return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _standardization_find_candidate(candidates: dict[str, object], candidate_id: str) -> dict[str, object] | None:
    for key in (
        "expression_matrix_candidates",
        "sample_metadata_candidates",
        "group_candidates",
        "species_candidates",
        "gene_id_candidates",
        "platform_annotation_candidates",
        "imported_deg_candidates",
    ):
        for item in _standardization_candidate_list(candidates, key):
            if str(item.get("candidate_id") or "") == candidate_id:
                return item
    return None


def _standardization_confirmation_rows(candidates: dict[str, object], confirmation: dict[str, object]) -> list[list[object]]:
    rows: list[list[object]] = []
    selected_expression = confirmation.get("selected_expression_candidate") if isinstance(confirmation.get("selected_expression_candidate"), dict) else {}
    selected_expression_id = str(selected_expression.get("candidate_id") or "")
    selected_sample = confirmation.get("selected_sample_metadata_candidate") if isinstance(confirmation.get("selected_sample_metadata_candidate"), dict) else {}
    selected_sample_id = str(selected_sample.get("candidate_id") or "")
    selected_species = confirmation.get("species_confirmed") if isinstance(confirmation.get("species_confirmed"), dict) else {}
    selected_gene = confirmation.get("gene_id_type_confirmed") if isinstance(confirmation.get("gene_id_type_confirmed"), dict) else {}
    selected_platform = confirmation.get("platform_annotation_confirmed") if isinstance(confirmation.get("platform_annotation_confirmed"), dict) else {}
    group_design = confirmation.get("confirmed_group_design") if isinstance(confirmation.get("confirmed_group_design"), dict) else {}
    for item in _standardization_candidate_list(candidates, "expression_matrix_candidates"):
        rows.append(_standardization_candidate_row("表达矩阵候选", item, "已选择" if str(item.get("candidate_id") or "") == selected_expression_id else "待确认"))
    for item in _standardization_candidate_list(candidates, "sample_metadata_candidates"):
        rows.append(_standardization_candidate_row("样本注释候选", item, "已选择" if str(item.get("candidate_id") or "") == selected_sample_id else "待确认"))
    for item in _standardization_candidate_list(candidates, "group_candidates"):
        rows.append(_standardization_candidate_row("分组候选", item, "已确认" if group_design.get("group_confirmed") else "候选，待确认"))
    for item in _standardization_candidate_list(candidates, "species_candidates"):
        status = "已确认" if selected_species.get("confirmed") and str(item.get("species") or "") == str(selected_species.get("species") or "") else "待确认"
        rows.append(_standardization_candidate_row("物种候选", item, status))
    for item in _standardization_candidate_list(candidates, "gene_id_candidates"):
        status = "已确认" if selected_gene.get("confirmed") and str(item.get("gene_id_type") or "") == str(selected_gene.get("gene_id_type") or "") else "待确认"
        rows.append(_standardization_candidate_row("gene ID 候选", item, status))
    for item in _standardization_candidate_list(candidates, "platform_annotation_candidates"):
        status = "已确认" if selected_platform.get("confirmed") and str(item.get("candidate_id") or "") == str(selected_platform.get("candidate_id") or "") else "待确认"
        rows.append(_standardization_candidate_row("平台注释候选", item, status))
    for item in _standardization_candidate_list(candidates, "imported_deg_candidates"):
        rows.append(_standardization_candidate_row("已有 DEG 结果候选", item, "可浏览；不是重新计算结果"))
    return rows


def _standardization_candidate_row(label: str, item: dict[str, object], status: str) -> list[object]:
    warnings = [str(value) for value in item.get("warnings", []) or [] if str(value)]
    fields = []
    if item.get("expression_value_type_candidate"):
        fields.append(f"表达值类型候选：{item.get('expression_value_type_candidate')}")
    if item.get("gene_id_type_candidate") or item.get("gene_id_type"):
        fields.append(f"ID 类型候选：{item.get('gene_id_type_candidate') or item.get('gene_id_type')}")
    if item.get("species"):
        fields.append(f"物种：{item.get('species')}（{item.get('source_field') or '未记录'}）")
    if item.get("group_field"):
        fields.append(f"候选字段：{item.get('group_field')}")
    if item.get("requires_user_confirmation"):
        fields.append("需要用户确认")
    if item.get("can_enter_next_step") is False:
        fields.append("暂不可进入下一步")
    if warnings:
        fields.append("warning：" + "；".join(warnings[:2]))
    reason = str(item.get("reason") or "")
    if reason:
        fields.append(reason)
    return [
        label,
        str(item.get("source_file") or "未记录"),
        str(item.get("source_parser") or "unknown"),
        status,
        "；".join(fields) if fields else "待用户确认。",
    ]


def _standardization_user_summary(registry: dict[str, object], manifest: dict[str, object]) -> str:
    assets = [item for item in registry.get("assets", []) or [] if isinstance(item, dict)]
    ready_assets = [item for item in assets if item.get("analysis_ready")]
    warnings = [str(item) for item in registry.get("warnings", []) or []] + [str(item) for item in manifest.get("warnings", []) or []]
    usable = [str(item) for item in manifest.get("usable_analyses", []) or []]
    missing = [str(item) for item in manifest.get("missing_assets", []) or []]
    return "\n".join(
        [
            f"注册资产：{len(assets)} 个",
            f"analysis-ready 资产：{len(ready_assets)} 个",
            f"可用于分析：{'、'.join(usable) if usable else '暂无'}",
            f"缺失关键资产：{'、'.join(missing) if missing else '无'}",
            f"warning：{'；'.join(dict.fromkeys(warnings)) if warnings else '无'}",
            "说明：当前为资产注册和轻量校验，不等于正式 biological normalization。",
        ]
    )


def _standardization_input_source_text(recognition: dict[str, object]) -> str:
    files = [item for item in recognition.get("files", []) or [] if isinstance(item, dict)]
    if not files:
        return "数据来源：尚未读取到识别结果。"
    names = [str(item.get("file_name") or Path(str(item.get("original_path") or "")).name or "未命名文件") for item in files[:3]]
    suffix = f"等 {len(files)} 个文件" if len(files) > 3 else f"{len(files)} 个文件"
    return f"数据来源：{ '、'.join(names) }（{suffix}）。"


def _standardization_input_status_text(recognition: dict[str, object]) -> str:
    files = [item for item in recognition.get("files", []) or [] if isinstance(item, dict)]
    if not files:
        return "识别状态：尚未完成数据识别。"
    generated_at = str(recognition.get("generated_at") or "未记录")
    warnings = [str(item) for item in recognition.get("warnings", []) or [] if str(item)]
    warning_text = f"；提示 {len(warnings)} 条" if warnings else ""
    return f"识别状态：已识别 {len(files)} 个文件；识别时间：{generated_at}{warning_text}。"


def _standardization_input_summary_text(recognition: dict[str, object]) -> str:
    files = [item for item in recognition.get("files", []) or [] if isinstance(item, dict)]
    if not files:
        return "内容摘要：请先返回数据识别页生成识别报告。"
    counts = recognition.get("type_counts") if isinstance(recognition.get("type_counts"), dict) else {}
    labels = []
    for key, count in counts.items():
        try:
            numeric = int(count)
        except (TypeError, ValueError):
            numeric = 0
        if numeric > 0:
            labels.append(f"{TYPE_LABELS.get(str(key), str(key))} {numeric} 个")
    return f"内容摘要：{'；'.join(labels) if labels else '已完成识别，类型仍需人工确认'}。"


def _standardization_expression_status_text(assets: list[object], readiness: dict[str, object]) -> str:
    available = {str(item) for item in readiness.get("available_inputs", []) or []}
    expression_assets = [
        item
        for item in assets
        if isinstance(item, dict) and str(item.get("asset_type") or "") in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "count_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}
    ]
    if expression_assets:
        labels = "、".join(dict.fromkeys(_standardization_asset_display_name(item) for item in expression_assets))
        return f"表达矩阵：已整理为 BioMedPilot 内部标准格式 {len(expression_assets)} 项（{labels}）；未执行生物学 normalization。"
    if available & {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "count_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}:
        return "表达矩阵：数据准备检查已识别到可用输入；请生成标准化数据。"
    return "表达矩阵：未识别到可用于后续分析的矩阵，请返回数据识别或数据选择补充。"


def _standardization_sample_status_text(assets: list[object], readiness: dict[str, object]) -> str:
    available = {str(item) for item in readiness.get("available_inputs", []) or []}
    sample_assets = [
        item
        for item in assets
        if isinstance(item, dict) and str(item.get("asset_type") or "") in {"sample_metadata", "phenotype_metadata", "clinical_metadata", "survival_metadata", "tcga_sample_metadata", "gtex_sample_metadata", "tcga_clinical_metadata"}
    ]
    if sample_assets:
        labels = "、".join(dict.fromkeys(_standardization_asset_display_name(item) for item in sample_assets))
        return f"样本信息：已识别到 {len(sample_assets)} 项（{labels}）；分组线索需要用户确认。"
    if {"sample_metadata", "phenotype_metadata", "clinical_metadata", "survival_metadata", "tcga_sample_metadata", "gtex_sample_metadata", "tcga_clinical_metadata"} & available:
        return "样本信息：数据准备检查已识别到样本或临床信息；请生成标准化数据。"
    return "样本信息：未识别到明确样本表；可先确认是否只做表达矩阵预览。"


def _standardization_group_status_text(project_root: Path, readiness: dict[str, object]) -> str:
    comparison = load_confirmed_comparison_config(project_root)
    if comparison is not None:
        summary = comparison_summary_text(comparison)
        match = readiness.get("comparison_sample_match") if isinstance(readiness.get("comparison_sample_match"), dict) else {}
        matched = match.get("matched_sample_count") if isinstance(match, dict) else None
        suffix = f"；已匹配样本 {matched} 个" if matched not in (None, "") else ""
        return f"分组与比较设计：已确认，{summary}{suffix}。"
    status = str(readiness.get("comparison_group_status") or "")
    if status == "candidate_pending":
        return "分组与比较设计：已检测到候选分组，待用户确认比较设计。"
    if status == "no_group_detected":
        return "分组与比较设计：尚未检测到明确分组，请确认样本信息或手动补充分组。"
    return "分组与比较设计：待确认。"


def _standardization_default_assets_text(assets: list[object]) -> str:
    selected_assets = [item for item in assets if isinstance(item, dict) and item.get("default_selected")]
    if not selected_assets:
        ready_assets = [item for item in assets if isinstance(item, dict) and item.get("analysis_ready")]
        if not ready_assets:
            return "当前默认使用的数据：尚未生成可用于后续分析的数据。"
        return "当前默认使用的数据：存在候选资产，但多候选时需要确认默认资产后才能生成稳定分析输入。"
    labels = "、".join(dict.fromkeys(_standardization_asset_display_name(item) for item in selected_assets[:5]))
    suffix = f"等 {len(selected_assets)} 项" if len(selected_assets) > 5 else f"{len(selected_assets)} 项"
    return f"当前默认使用的数据：{labels}（{suffix}）；已记录 selection state。"


def _standardization_next_step_text(project_root: Path, assets: list[object], readiness: dict[str, object]) -> str:
    recognition = load_recognition_report(project_root)
    if not isinstance(recognition, dict) or not recognition.get("files"):
        return "下一步建议：先返回数据识别页生成识别报告。"
    if not assets:
        return "下一步建议：点击“生成标准化数据”，把识别结果登记为后续分析可用的数据。"
    available = {str(item) for item in readiness.get("available_inputs", []) or []}
    if not available & {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "count_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}:
        return "下一步建议：返回数据识别或数据选择，补充表达矩阵。"
    if load_confirmed_comparison_config(project_root) is None:
        return "下一步建议：确认分组与比较设计，再进入分析任务中心。"
    return "下一步建议：已具备核心输入，可继续到分析任务中心创建预览任务。"


def _standardization_user_asset_rows(assets: list[object]) -> list[list[object]]:
    rows: list[list[object]] = []
    for item in assets:
        if not isinstance(item, dict):
            continue
        analysis_ready = bool(item.get("analysis_ready"))
        warning = str(item.get("warning") or "")
        rows.append(
            [
                _standardization_asset_display_name(item),
                _standardization_asset_status_text(item, warning),
                "、".join(str(value) for value in item.get("consumable_by", []) or []) if analysis_ready else "否",
                "有提示，请在开发者诊断中查看。" if warning else _standardization_asset_user_hint(str(item.get("asset_type") or "")),
            ]
        )
    return rows


def _standardization_asset_display_name(asset: dict[str, object]) -> str:
    asset_type = str(asset.get("asset_type") or "")
    label = str(asset.get("label_zh") or TYPE_LABELS.get(asset_type, "") or "")
    if label:
        return label
    return {
        "normalized_expression_matrix": "标准化表达矩阵",
        "raw_count_matrix": "原始计数矩阵",
        "phenotype_metadata": "样本表型信息",
    }.get(asset_type, "其他数据")


def _standardization_asset_user_hint(asset_type: str) -> str:
    if asset_type in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}:
        return "已整理为内部标准格式；未执行生物学 normalization。"
    if asset_type in {"sample_metadata", "phenotype_metadata", "tcga_sample_metadata", "gtex_sample_metadata"}:
        return "可用于整理样本信息和分组线索。"
    if asset_type in {"clinical_metadata", "survival_metadata", "tcga_clinical_metadata"}:
        return "可用于临床变量或生存相关分析准备。"
    if asset_type == "differential_result_table":
        return "用户导入结果；可用于浏览或富集输入，不可作为重新计算 DEG 输入。"
    if asset_type == "gmt_gene_set":
        return "可用于 GSEA 或富集分析准备。"
    return "已登记为项目数据，是否用于分析仍需后续确认。"


def _standardization_asset_status_text(item: dict[str, object], warning: str) -> str:
    repository = str(item.get("repository") or "")
    validation = str(item.get("validation_status") or "registered")
    selected = "；默认资产" if item.get("default_selected") else ""
    if warning:
        return f"{repository}：{validation}{selected}"
    return f"{repository}：已登记{selected}"


def _format_confidence(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "未记录"
    return f"{numeric * 100:.0f}%"


def _recognition_status_reason(item: dict[str, object]) -> str:
    status = str(item.get("standardization_status_zh") or "")
    reason = str(item.get("reason") or "")
    if not status:
        roles = {str(role) for role in item.get("recognized_roles", []) or []}
        primary = str(item.get("recognized_type") or "")
        if primary in {"unknown", "raw_heavy_file"}:
            status = "不能用于分析"
        elif roles & {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "sample_metadata", "clinical_metadata", "tcga_expression_matrix", "gtex_expression_matrix"}:
            status = "可进入标准化"
        elif roles & {"platform_annotation", "gene_annotation", "platform_reference_hint", "gmt_gene_set"}:
            status = "仅作参考/注释"
    return f"{status}：{reason}" if status and reason else (status or reason)


def _recognition_type_text(item: dict[str, object]) -> str:
    primary = str(item.get("recognized_type") or "unknown")
    primary_label = str(item.get("recognized_type_zh") or TYPE_LABELS.get(primary, "未知文件"))
    roles = [str(role) for role in item.get("recognized_roles", []) or [] if str(role) and str(role) != primary]
    role_labels = [TYPE_LABELS.get(role, role) for role in roles if role != "unknown"]
    if primary == "geo_soft_container":
        depth = _geo_soft_parser_depth_from_item(item)
        depth_label = _geo_soft_parser_depth_label(depth)
        if role_labels:
            return f"{primary_label}（{depth_label}；含：{'、'.join(role_labels)}）"
        return f"{primary_label}（{depth_label}）"
    if primary == "geo_series_matrix_container":
        depth = _geo_series_parser_depth_from_item(item)
        depth_label = _geo_series_parser_depth_label(depth)
        sample_count = int(item.get("sample_count") or 0)
        expression_status = "表达矩阵区域已检测" if item.get("expression_matrix_presence") else "尚未确认表达矩阵区域"
        if role_labels:
            return f"{primary_label}（{depth_label}；样本 {sample_count}；{expression_status}；含：{'、'.join(role_labels)}）"
        return f"{primary_label}（{depth_label}；样本 {sample_count}；{expression_status}）"
    if not roles:
        return primary_label
    return f"{primary_label}（含：{'、'.join(role_labels)}）" if role_labels else primary_label


def _recognition_roles_tooltip(item: dict[str, object]) -> str:
    roles = [str(role) for role in item.get("recognized_roles", []) or [] if str(role)]
    assets = [asset for asset in item.get("detected_assets", []) or [] if isinstance(asset, dict)]
    lines = [f"主类型：{item.get('recognized_type_zh') or TYPE_LABELS.get(str(item.get('recognized_type') or 'unknown'), '未知文件')}"]
    if item.get("standardization_status_zh"):
        lines.append(f"标准化状态：{item.get('standardization_status_zh')}")
    if item.get("next_action"):
        lines.append(f"建议动作：{item.get('next_action')}")
    if str(item.get("recognized_type") or "") == "geo_soft_container":
        depth = _geo_soft_parser_depth_from_item(item)
        lines.append(f"SOFT 解析深度：{_geo_soft_parser_depth_label(depth)}")
        lines.append(f"样本数：{int(item.get('sample_count') or 0)}；平台数：{int(item.get('platform_count') or 0)}")
        if item.get("expression_table_presence"):
            lines.append("表达表格：检测为候选输入，进入标准化前需要用户确认。")
        else:
            lines.append("表达表格：尚未确认表达矩阵。")
        warnings = [str(warning) for warning in item.get("warnings", []) or [] if str(warning)]
        if warnings:
            lines.append("解析提示：" + "；".join(warnings[:3]))
    if str(item.get("recognized_type") or "") == "geo_series_matrix_container":
        depth = _geo_series_parser_depth_from_item(item)
        lines.append(f"Series Matrix 解析深度：{_geo_series_parser_depth_label(depth)}")
        lines.append(f"样本数量：{int(item.get('sample_count') or 0)}")
        platforms = [str(value) for value in item.get("platform_accessions", []) or [] if str(value)]
        if platforms:
            lines.append("平台 accession：" + "、".join(platforms[:5]))
        dimensions = item.get("expression_matrix_dimensions")
        if isinstance(dimensions, dict):
            lines.append(
                "表达矩阵维度："
                f"{int(dimensions.get('rows') or 0)} 行，"
                f"{int(dimensions.get('sample_columns') or 0)} 个样本列"
            )
        if item.get("expression_matrix_presence"):
            lines.append("已检测到 GEO Series Matrix 表达矩阵区域，可进入标准化阶段进一步确认。")
        else:
            lines.append("表达矩阵区域：尚未确认。")
        lines.append(f"表达值类型候选：{item.get('expression_value_type_candidate') or 'unknown'}")
        lines.append(f"ID 类型候选：{item.get('gene_id_type_candidate') or 'unknown'}")
        fields = [str(value) for value in item.get("sample_metadata_fields", []) or [] if str(value)]
        phenotype_fields = [str(value) for value in item.get("phenotype_candidate_fields", []) or [] if str(value)]
        lines.append(f"样本注释字段数量：{len(fields)}")
        if phenotype_fields:
            lines.append("表型/分组候选字段：" + "、".join(phenotype_fields[:8]) + "；需用户确认后才能进行 DEG 分析。")
        if str(item.get("gene_id_type_candidate") or "") in {"probe_id", "unknown"}:
            lines.append("ID_REF 可能为平台探针 ID，需结合平台注释确认 gene ID 映射。")
        warnings = [str(warning) for warning in item.get("warnings", []) or [] if str(warning)]
        if warnings:
            lines.append("解析提示：" + "；".join(warnings[:3]))
    if roles:
        lines.append("可用角色：" + "、".join(TYPE_LABELS.get(role, role) for role in roles))
    for asset in assets:
        label = str(asset.get("label_zh") or TYPE_LABELS.get(str(asset.get("asset_type") or ""), ""))
        reason = str(asset.get("reason") or "")
        if label or reason:
            lines.append(f"{label}：{reason}".strip("："))
    return "\n".join(lines)


def _geo_soft_parser_depth_from_item(item: dict[str, object]) -> str:
    profile = item.get("content_profile")
    if item.get("parser_depth"):
        return str(item.get("parser_depth") or "")
    if isinstance(profile, dict):
        return str(profile.get("parser_depth") or "")
    return ""


def _geo_soft_parser_depth_label(depth: str) -> str:
    return {
        "container_only": "已识别 GEO SOFT 容器",
        "metadata_parsed": "已解析样本/平台元数据",
        "table_detected": "检测到平台或表达表格",
        "table_parsed": "已解析表格结构",
    }.get(depth, "已识别 GEO SOFT 容器")


def _geo_series_parser_depth_from_item(item: dict[str, object]) -> str:
    profile = item.get("content_profile")
    if item.get("parser_depth"):
        return str(item.get("parser_depth") or "")
    if isinstance(profile, dict):
        return str(profile.get("parser_depth") or "")
    return ""


def _geo_series_parser_depth_label(depth: str) -> str:
    return {
        "container_only": "已识别 GEO Series Matrix 容器",
        "metadata_parsed": "已解析 Series/Sample metadata",
        "matrix_detected": "检测到表达矩阵区域",
        "matrix_previewed": "已解析表达矩阵结构预览",
    }.get(depth, "已识别 GEO Series Matrix 容器")


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


def _recognition_user_summary(report: dict[str, object], files: list[dict[str, object]], warnings: list[str], project_root: Path | None) -> str:
    counts = report.get("type_counts", {}) if isinstance(report.get("type_counts"), dict) else {}
    duplicate_count = sum(1 for item in files if item.get("_duplicate"))
    effective_count = sum(1 for item in files if item.get("_effective_source"))
    status_counts = {
        "可进入标准化": sum(1 for item in files if str(item.get("standardization_status") or "") == "eligible"),
        "仅作参考/注释": sum(1 for item in files if str(item.get("standardization_status") or "") == "reference_only"),
        "不能用于分析": sum(1 for item in files if str(item.get("standardization_status") or "") == "blocked"),
    }
    type_lines = []
    for key, label in TYPE_LABELS.items():
        count = int(counts.get(key, 0) or 0)
        if count:
            type_lines.append(f"{label}：{count}")
    if project_root is not None and not _current_effective_source_paths(project_root):
        source_note = "当前版本会扫描项目 raw_data 中所有已选择文件，因此历史导入副本也可能显示在识别结果中。"
    else:
        source_note = f"当前有效数据来源文件：{effective_count} 个。"
    has_core = has_standardizable_expression_input(files)
    if has_core:
        next_step = "可以继续进入数据准备与标准化；需在标准化阶段确认分组后才能进行 DEG 分析。"
    else:
        next_step = "未识别到表达矩阵或原始计数矩阵，请返回数据来源补充文件。"
    stale = report.get("stale_status") if isinstance(report.get("stale_status"), dict) else {}
    stale_line = "识别报告状态：当前。"
    if stale.get("is_stale"):
        stale_line = f"识别报告状态：已过期，{stale.get('message') or '请重新识别。'}"
    return "\n".join(
        [
            f"识别文件总数：{len(files)}",
            f"warning 数量：{len(warnings)}",
            f"类型统计：{'；'.join(type_lines) if type_lines else '暂无可识别类型'}",
            "标准化状态：" + "；".join(f"{label}：{count}" for label, count in status_counts.items()),
            f"疑似重复文件：{duplicate_count} 个",
            stale_line,
            source_note,
            f"下一步建议：{next_step}",
        ]
    )


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
    stale = report.get("stale_status") if isinstance(report.get("stale_status"), dict) else {}
    if stale.get("is_stale"):
        return False, str(stale.get("message") or "识别报告已过期，请重新识别。")
    files = [item for item in report.get("files", []) or [] if isinstance(item, dict)]
    if not files:
        return False, "识别报告中没有任何文件。"
    if not has_standardizable_expression_input(files):
        return False, "未识别到表达矩阵或原始计数矩阵。"
    readiness = run_project_readiness(project_root).get("readiness_report")
    if isinstance(readiness, dict) and not readiness.get("standardization_ready"):
        return False, "未识别到表达矩阵或原始计数矩阵。"
    return True, ""


def _can_continue_from_readiness(project_root: Path) -> tuple[bool, str]:
    artifacts = load_readiness_artifacts(project_root)
    readiness = artifacts.get("readiness_report")
    if not isinstance(readiness, dict):
        return False, "尚未运行数据准备检查。"
    status = str(readiness.get("overall_status") or "unavailable")
    if status in {"not_ready", "unavailable"} or not readiness.get("standardization_ready", readiness.get("has_core_input")):
        return False, f"当前数据准备状态为“{readiness_status_zh(status)}”。"
    return True, ""


def _can_continue_from_standardization(project_root: Path) -> tuple[bool, str]:
    artifacts = load_standardization_artifacts(project_root)
    registry = artifacts.get("registry")
    if not isinstance(registry, dict):
        return False, "尚未生成标准化资产。"
    stale = artifacts.get("repository_stale_status") if isinstance(artifacts.get("repository_stale_status"), dict) else {}
    if stale.get("is_stale"):
        return False, str(stale.get("message") or "标准化资产仓库已过期，请重新生成。")
    assets = [item for item in registry.get("assets", []) or [] if isinstance(item, dict)]
    has_ready_core = any(item.get("analysis_ready") and str(item.get("asset_type")) in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "count_matrix", "tcga_expression_matrix", "gtex_expression_matrix"} for item in assets)
    if not has_ready_core:
        return False, "没有 analysis-ready 表达矩阵资产。"
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
                "result_name": f"{dataset_id} 测试级差异表达结果",
                "analysis_type": "differential_expression",
                "file_type": "csv",
                "created_at": str(summary.get("generated_at") or _utc_now_iso()),
                "path": result_path,
                "status": "testing-level",
                "result_semantics": "testing-level",
                "execution_level": "testing-level computed preview",
                "summary_path": str(summary.get("summary_path") or ""),
                "dataset_id": dataset_id,
                "warning": "测试级结果，不等于正式 DEG 分析。" + ("；" + "、".join(str(item) for item in summary.get("warnings", []) or []) if summary.get("warnings") else ""),
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
