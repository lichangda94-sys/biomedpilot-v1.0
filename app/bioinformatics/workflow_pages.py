from __future__ import annotations

import json
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
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
    QVBoxLayout,
    QWidget,
)

from app.bioinformatics.project_analysis_tasks import create_analysis_task, load_analysis_task_center, load_task_records
from app.bioinformatics.project_readiness import load_readiness_artifacts, readiness_status_zh, run_project_readiness
from app.bioinformatics.project_recognition import TYPE_LABELS, load_recognition_report, run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets, load_standardization_artifacts
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
    LATEST_RECORD,
    generate_gse_acquisition_plan,
    load_latest_acquisition_summary,
    read_acquisition_artifacts,
    register_acquisition,
)
from app.bioinformatics.adapters.legacy_geo import geo_check_command, run_geo_environment_check
from app.bioinformatics.reports.project_report_builder import generate_project_report, load_project_report
from app.bioinformatics.results.project_results import load_result_index
from app.bioinformatics.search_center import (
    BioinformaticsSearchCenterResult,
    BioinformaticsSourceRouter,
    GeoSearchAdapter,
    SourceSearchResult,
    UnifiedDatasetCandidate,
)
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


@dataclass(frozen=True)
class GseDatasetPreview:
    gse_id: str
    title: str = "未记录"
    platform: str = "未记录"
    sample_count: str = "未记录"
    status: str = "尚未登记"


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
            self._set_status("先登记数据来源，下一步进入数据识别。")
        self._refresh_registered_sources()

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
        self._render_gse_preview(self._gse_preview)
        self._set_status("GSE 数据集摘要已生成，请确认后登记为数据源。")
        return self._gse_preview

    def register_gse_dataset(self) -> AcquisitionSummary | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        preview = self._gse_preview or self.search_gse_dataset()
        if preview is None:
            return None
        summary = generate_gse_acquisition_plan(self._project_root, preview.gse_id)
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
            status="已登记",
        )
        self._render_gse_preview(self._gse_preview)
        self._refresh_registered_sources()
        self._set_status(f"{preview.gse_id} 已登记为数据源。")
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
            summary_key=summary_key or source_type,
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

    def open_chinese_search(self) -> None:
        self.chinese_search_requested.emit()

    def continue_to_recognition(self) -> None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return
        if self._latest_summary is None:
            self._latest_summary = load_latest_acquisition_summary(self._project_root)
        if self._registered_source_count() == 0:
            self._set_status("请先生成或登记一个数据来源。", error=True)
            return
        self.continue_requested.emit(self._project_root)

    def continue_to_acquisition_status(self) -> None:
        self.continue_to_recognition()

    def _build_ui(self) -> None:
        root = _scroll_root(self, max_width=1040)
        root.addWidget(
            _header(
                "数据来源与登记",
                "先登记数据来源，下一步进入数据识别。",
                back_text="返回项目首页",
                back_signal=self.back_requested,
            )
        )
        self._project_label = _status_label("请先创建或打开生信分析项目。")
        root.addWidget(self._project_label)
        self._status_label = _status_label("先登记数据来源，下一步进入数据识别。")
        root.addWidget(self._status_label)

        root.addWidget(self._local_import_card())
        root.addWidget(self._gse_card())
        root.addWidget(self._research_card())

        summary_card, summary_layout = _card("当前已登记数据源")
        summary_card.setObjectName("registeredSourceSummaryCard")
        self._registered_empty_label = _muted("尚未登记数据源。")
        summary_layout.addWidget(self._registered_empty_label)
        self._registered_sources_table = _table(["来源类型", "名称/编号", "状态", "操作"])
        self._registered_sources_table.setObjectName("registeredSourceSummaryTable")
        self._registered_sources_table.setMinimumHeight(150)
        summary_layout.addWidget(self._registered_sources_table)
        root.addWidget(summary_card)

        self._technical_details = _text_preview(120)
        self._technical_details.setVisible(False)
        root.addWidget(self._technical_details)

        actions_frame = QFrame()
        actions_frame.setObjectName("dataSourceBottomActionBar")
        actions = QHBoxLayout(actions_frame)
        actions.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        self._registered_count_label = _status_label("已登记数据源：0 个")
        self._next_button = _button("下一步：数据识别", "primaryButton", self.continue_to_recognition)
        self._next_button.setEnabled(False)
        actions.addWidget(self._registered_count_label)
        actions.addStretch(1)
        actions.addWidget(self._next_button)
        root.addWidget(actions_frame)

    def _local_import_card(self) -> QFrame:
        card, layout = _card("本地数据导入")
        card.setObjectName("localImportEntryCard")
        layout.addWidget(_muted("导入本地表达矩阵、GEO Series Matrix、样本信息、临床表或注释文件。"))
        self._local_strategy_combo = QComboBox()
        self._local_strategy_combo.setObjectName("localImportStrategyCombo")
        self._local_strategy_combo.addItems(["复制到项目（推荐）", "保留原位置，仅记录路径"])
        layout.addWidget(self._local_strategy_combo)
        select_button = _button("选择本地数据", "primaryButton", self._choose_local_data)
        select_button.setMinimumHeight(44)
        layout.addWidget(select_button, alignment=Qt.AlignLeft)
        layout.addWidget(self._source_summary_frame("local_import", "尚未选择本地数据。", detail_button_text="查看登记详情"))
        return card

    def _gse_card(self) -> QFrame:
        card, layout = _card("GSE 编号检索")
        card.setObjectName("gseSearchEntryCard")
        layout.addWidget(_muted("已知 GEO 数据集编号时使用，例如 GSE33630。"))
        self._gse_input = QLineEdit()
        self._gse_input.setPlaceholderText("请输入 GSE 编号，例如 GSE33630")
        self._gse_input.setMinimumHeight(44)
        layout.addWidget(self._gse_input)
        gse_actions = QHBoxLayout()
        search_button = _button("检索数据集", "primaryButton", self.search_gse_dataset)
        search_button.setMinimumHeight(44)
        self._register_gse_button = _button("登记为数据源", "secondaryButton", self.register_gse_dataset)
        self._register_gse_button.setEnabled(False)
        self._register_gse_button.setVisible(False)
        gse_actions.addWidget(search_button)
        gse_actions.addWidget(self._register_gse_button)
        gse_actions.addStretch(1)
        layout.addLayout(gse_actions)
        self._gse_status_label = _status_label("尚未检索 GSE 数据集。")
        layout.addWidget(self._gse_status_label)
        self._gse_summary_table = _table(["GSE 编号", "数据集标题", "平台", "样本数量", "登记状态"])
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
        layout.addWidget(self._source_summary_frame("geo_gse", "尚未检索 GSE 数据集。", detail_button_text="查看登记详情"))
        return card

    def _research_card(self) -> QFrame:
        card, layout = _card("中文研究问题检索")
        card.setObjectName("chineseResearchSearchEntryCard")
        layout.addWidget(_muted("输入中文研究方向，生成英文检索词并推荐 GEO、TCGA、GTEx 候选数据集。"))
        self._chinese_search_status_label = _status_label("尚未进行中文检索。")
        layout.addWidget(self._chinese_search_status_label)
        button = _button("进入中文检索", "primaryButton", self.open_chinese_search)
        button.setMinimumHeight(44)
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
        self._set_status("先登记数据来源，下一步进入数据识别。")
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
        self._gse_status_label.setText(f"已登记 GSE 数据集：{preview.gse_id}" if preview.status == "已登记" else f"已检索到：{preview.gse_id}")
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
                    "登记状态": preview.status,
                }
            )
        )
        self._gse_search_detail_button.setVisible(True)
        self._register_gse_button.setVisible(preview.status != "已登记")
        self._register_gse_button.setEnabled(preview.status != "已登记")

    def _refresh_registered_sources(self) -> None:
        rows = _registered_source_rows(self._project_root)
        self._registered_empty_label.setVisible(not rows)
        _fill_table(
            self._registered_sources_table,
            [[row.source_type, row.source_label, row.status, "查看"] for row in rows],
        )
        count = len(rows)
        self._registered_count_label.setText(f"已登记数据源：{count} 个")
        self._next_button.setEnabled(count > 0 and self._project_root is not None)
        self._chinese_search_status_label.setText(_chinese_search_entry_status(rows))

    def _registered_source_count(self) -> int:
        return len(_registered_source_rows(self._project_root))

    def _toggle_source_detail(self, key: str) -> None:
        detail = self._source_detail_edits.get(key)
        if detail is not None:
            _toggle_details(detail)

    def _set_status(self, text: str, *, error: bool = False) -> None:
        self._status_label.setText(text if error else "先登记数据来源，下一步进入数据识别。")
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
        self._candidates: dict[tuple[str, str], UnifiedDatasetCandidate] = {}
        self._candidate_register_buttons: dict[tuple[str, str], QPushButton] = {}
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
        result = BioinformaticsSourceRouter().search(query, online_enabled=False, limit=20)
        self._last_result = result
        self._render_result(result, searched=False)
        self._set_status("已生成检索草稿。请确认后检索候选数据集。")
        return result

    def search_candidates(self, *, online_enabled: bool = False) -> BioinformaticsSearchCenterResult | None:
        query = self._query_input.text().strip()
        if not query:
            self._set_status("请输入中文研究主题。", error=True)
            return None
        self._set_status("检索中")
        result = BioinformaticsSourceRouter().search(query, online_enabled=online_enabled, limit=20)
        self._last_result = result
        self._render_result(result, searched=True)
        self._set_status("已完成候选数据集检索。")
        return result

    def search_geo_candidates(self) -> BioinformaticsSearchCenterResult | None:
        draft = self._ensure_draft_result()
        if draft is None:
            return None
        self._set_status("检索中")
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
            self._set_status("已检索到 GEO/GSE 候选数据集。")
        return result

    def search_tcga_candidates(self) -> BioinformaticsSearchCenterResult | None:
        result = self._ensure_draft_result()
        if result is None:
            return None
        self._render_result(result, searched=False)
        candidates = [candidate for candidate in result.candidates if candidate.source == "tcga_gdc"]
        self._set_status(
            "已根据本地词库匹配到 TCGA/GDC 项目，尚未执行在线数据获取。"
            if candidates
            else "未生成 TCGA/GDC 项目候选。"
        )
        return result

    def search_gtex_candidates(self) -> BioinformaticsSearchCenterResult | None:
        result = self._ensure_draft_result()
        if result is None:
            return None
        self._render_result(result, searched=False)
        candidates = [candidate for candidate in result.candidates if candidate.source == "gtex"]
        self._set_status(
            "已根据本地词库匹配到 GTEx 组织，尚未执行在线数据获取。"
            if candidates
            else "未生成 GTEx 组织候选。"
        )
        return result

    def register_candidate(self, source: str, accession_or_project: str) -> AcquisitionSummary | None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return None
        candidate = self._candidates.get((source, accession_or_project))
        if candidate is None:
            self._set_status("候选结果不存在。", error=True)
            return None
        if self._is_candidate_registered(source, accession_or_project):
            self._set_status(f"已登记数据源：{accession_or_project}")
            self._refresh_candidate_registration_buttons()
            return None
        summary = register_acquisition(
            self._project_root,
            source_type=_candidate_source_type(candidate),
            source_label=candidate.accession_or_project,
            strategy="plan_only",
            selected_paths=[],
            metadata={
                "ui_source": "chinese_research_question_search",
                "source": candidate.source,
                "accession_or_project": candidate.accession_or_project,
                "display_title": candidate.display_title,
                "query": self._query_input.text().strip(),
                "source_specific_metadata": candidate.source_specific_metadata,
                "warnings": list(candidate.warnings),
            },
        )
        self._refresh_registered_sources()
        self._refresh_candidate_registration_buttons()
        self.source_registered.emit(summary)
        self._set_status(f"已登记数据源：{candidate.accession_or_project}。可进入数据识别。")
        return summary

    def continue_to_recognition(self) -> None:
        if self._project_root is None:
            self._set_status("请先创建或打开生信分析项目。", error=True)
            return
        if self._registered_source_count() == 0:
            self._set_status("请先登记至少一个数据源。", error=True)
            return
        self.continue_requested.emit(self._project_root)

    def copy_query(self, source: str) -> bool:
        edit = {"geo": self._geo_query_box, "tcga": self._tcga_query_box, "gtex": self._gtex_query_box}.get(source)
        if edit is None:
            return False
        QApplication.clipboard().setText(edit.toPlainText())
        self._set_status("已复制草稿。")
        return True

    def _build_ui(self) -> None:
        root = _scroll_root(self, max_width=1080)
        root.addWidget(_header("中文研究问题检索", "中文研究主题到 GEO、TCGA、GTEx 数据源候选。", back_text="返回数据来源", back_signal=self.back_requested))
        self._project_label = _status_label("请先创建或打开生信分析项目。")
        root.addWidget(self._project_label)
        input_card, input_layout = _card("中文研究问题检索")
        self._query_input = QLineEdit()
        self._query_input.setPlaceholderText("例如：甲状腺癌、乳腺癌转移、肺癌免疫治疗耐药")
        self._query_input.setMinimumHeight(44)
        input_layout.addWidget(self._query_input)
        action_row = QHBoxLayout()
        action_row.addWidget(_button("生成检索词", "primaryButton", self.generate_terms))
        action_row.addStretch(1)
        input_layout.addLayout(action_row)
        input_layout.addWidget(_muted("选择候选数据集并登记后，可进入数据识别。"))
        self._status_label = _status_label("未生成检索词")
        input_layout.addWidget(self._status_label)
        root.addWidget(input_card)

        drafts_card, drafts_layout = _card("三源检索草稿")
        self._geo_query_box = self._query_draft_box("暂无 GEO/GSE 检索草稿")
        self._tcga_query_box = self._query_draft_box("暂无 TCGA/GDC 项目草稿")
        self._gtex_query_box = self._query_draft_box("暂无 GTEx 组织草稿")
        self._add_draft_section(
            drafts_layout,
            title="GEO/GSE 检索草稿",
            box=self._geo_query_box,
            copy_text="复制检索词",
            search_text="检索 GEO/GSE 候选数据集",
            copy_source="geo",
            search_callback=self.search_geo_candidates,
        )
        self._add_draft_section(
            drafts_layout,
            title="TCGA/GDC 项目草稿",
            box=self._tcga_query_box,
            copy_text="复制项目代码",
            search_text="检索 TCGA/GDC 项目",
            copy_source="tcga",
            search_callback=self.search_tcga_candidates,
        )
        self._add_draft_section(
            drafts_layout,
            title="GTEx 组织草稿",
            box=self._gtex_query_box,
            copy_text="复制组织关键词",
            search_text="检索 GTEx 组织",
            copy_source="gtex",
            search_callback=self.search_gtex_candidates,
        )
        root.addWidget(drafts_card)

        result_card, result_layout = _card("数据库候选结果")
        self._tabs = QTabWidget()
        self._geo_tab_page, self._geo_empty_label, self._geo_table = self._candidate_tab(["GSE 编号", "标题", "疾病/组织", "平台/数据类型", "样本数", "匹配原因", "推荐等级", "操作"])
        self._tcga_tab_page, self._tcga_empty_label, self._tcga_table = self._candidate_tab(["项目代码", "项目名称", "匹配来源", "状态", "操作"])
        self._gtex_tab_page, self._gtex_empty_label, self._gtex_table = self._candidate_tab(["组织名称", "组织类型", "匹配来源", "状态", "操作"])
        self._tabs.addTab(self._geo_tab_page, "GEO/GSE 候选数据集")
        self._tabs.addTab(self._tcga_tab_page, "TCGA/GDC 项目候选")
        self._tabs.addTab(self._gtex_tab_page, "GTEx 组织候选")
        result_layout.addWidget(self._tabs)
        root.addWidget(result_card)

        registered_card, registered_layout = _card("已选择/已登记数据源")
        self._registered_empty_label = _muted("尚未从中文检索结果登记数据源。")
        registered_layout.addWidget(self._registered_empty_label)
        self._registered_table = _table(["来源数据库", "编号/项目/组织", "名称", "登记状态", "操作"])
        self._registered_table.setObjectName("chineseRegisteredSourceTable")
        registered_layout.addWidget(self._registered_table)
        root.addWidget(registered_card)

        log_card, log_layout = _card("映射日志")
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
        self._registered_count_label = _status_label("已登记数据源：0 个")
        self._continue_button = _button("进入数据识别", "primaryButton", self.continue_to_recognition)
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
        table.setMinimumHeight(220)
        layout.addWidget(empty)
        layout.addWidget(table)
        return page, empty, table

    def _render_result(self, result: BioinformaticsSearchCenterResult, *, searched: bool) -> None:
        query = result.query
        geo_queries = tuple(query.geo_query_candidates)
        self._geo_query_box.setPlainText("\n".join(geo_queries) if geo_queries else "暂无 GEO/GSE 检索草稿")
        self._tcga_query_box.setPlainText(", ".join(query.tcga_project_ids) if query.tcga_project_ids else "暂无 TCGA/GDC 项目草稿")
        self._gtex_query_box.setPlainText(", ".join(query.gtex_tissues) if query.gtex_tissues else "暂无 GTEx 组织草稿")
        self._candidates = {(candidate.source, candidate.accession_or_project): candidate for candidate in result.candidates}
        self._candidate_register_buttons.clear()
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
                    item.accession_or_project,
                    item.display_title,
                    item.disease or item.tissue,
                    item.data_modality,
                    item.sample_count,
                    _candidate_match_reason(item),
                    _candidate_recommendation(item),
                    "",
                ]
                for item in candidates
            ],
        )
        self._install_candidate_action_buttons(self._geo_table, candidates)

    def _fill_tcga_candidates(self, candidates: list[UnifiedDatasetCandidate]) -> None:
        self._tcga_empty_label.setVisible(not candidates)
        self._tcga_table.setVisible(bool(candidates))
        self._tcga_empty_label.setText("未生成 TCGA/GDC 项目候选。")
        _fill_table(
            self._tcga_table,
            [
                [
                    item.accession_or_project,
                    item.display_title,
                    "本地词库映射",
                    "已匹配，尚未下载",
                    "",
                ]
                for item in candidates
            ],
        )
        self._install_candidate_action_buttons(self._tcga_table, candidates)

    def _fill_gtex_candidates(self, candidates: list[UnifiedDatasetCandidate]) -> None:
        self._gtex_empty_label.setVisible(not candidates)
        self._gtex_table.setVisible(bool(candidates))
        self._gtex_empty_label.setText("未生成 GTEx 组织候选。")
        _fill_table(
            self._gtex_table,
            [
                [
                    item.tissue or item.accession_or_project,
                    "正常组织参考",
                    "本地词库映射",
                    "已匹配，尚未下载",
                    "",
                ]
                for item in candidates
            ],
        )
        self._install_candidate_action_buttons(self._gtex_table, candidates)

    def _refresh_registered_sources(self) -> None:
        rows = self._registered_chinese_rows()
        self._registered_empty_label.setVisible(not rows)
        _fill_table(self._registered_table, [[row.source_type, row.source_label, row.location, row.status, ""] for row in rows])
        for row_index, row in enumerate(rows):
            self._registered_table.setCellWidget(row_index, 4, _registered_source_action_widget(row))
        count = len(rows)
        self._registered_count_label.setText(f"已登记数据源：{count} 个")
        self._continue_button.setEnabled(count > 0 and self._project_root is not None)

    def _install_candidate_action_buttons(self, table: QTableWidget, candidates: list[UnifiedDatasetCandidate]) -> None:
        action_col = table.columnCount() - 1
        for row_index, candidate in enumerate(candidates):
            key = (candidate.source, candidate.accession_or_project)
            action_widget = QWidget()
            layout = QHBoxLayout(action_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            register_button = QPushButton("登记为数据源")
            register_button.setObjectName(f"registerCandidateButton_{candidate.source}_{candidate.accession_or_project}")
            register_button.clicked.connect(lambda checked=False, s=candidate.source, a=candidate.accession_or_project: self.register_candidate(s, a))
            detail_button = QPushButton("查看详情")
            detail_button.setObjectName(f"candidateDetailButton_{candidate.source}_{candidate.accession_or_project}")
            detail_button.clicked.connect(lambda checked=False, item=candidate: self._show_candidate_detail(item))
            layout.addWidget(register_button)
            layout.addWidget(detail_button)
            layout.addStretch(1)
            table.setCellWidget(row_index, action_col, action_widget)
            self._candidate_register_buttons[key] = register_button
        self._refresh_candidate_registration_buttons()

    def _show_candidate_detail(self, candidate: UnifiedDatasetCandidate) -> None:
        self._mapping_log.setPlainText(_json(candidate.to_dict()))
        self._mapping_log.setVisible(True)
        self._set_status(f"正在查看：{candidate.accession_or_project}")

    def _refresh_candidate_registration_buttons(self) -> None:
        for (source, accession), button in self._candidate_register_buttons.items():
            registered = self._is_candidate_registered(source, accession)
            button.setText("已登记" if registered else "登记为数据源")
            button.setEnabled(not registered)

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

    def _registered_chinese_rows(self) -> list[RegisteredSourceRow]:
        return [row for row in _registered_source_rows(self._project_root) if row.source_type_key.startswith("chinese_")]

    def _registered_source_count(self) -> int:
        return len(self._registered_chinese_rows())

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
    back_requested = Signal()

    def __init__(self, *, on_continue: Callable[[Path], None] | None = None, on_back: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_root: Path | None = None
        self._last_report: dict[str, object] | None = None
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
        report = run_project_recognition(self._project_root)
        self._render_report(report)
        self._set_status(f"{self.status_message()} 重新识别已重新扫描当前项目中的数据文件；不会删除 raw_data 中的历史导入副本。")
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
        self.continue_requested.emit(self._project_root)

    def _build_ui(self) -> None:
        root = _scroll_root(self)
        root.addWidget(_header("数据识别", "Developer Preview / 本地测试版", back_text="返回数据来源与登记", back_signal=self.back_requested))
        pre_card, pre_layout = _card("待识别数据源")
        self._pre_recognition_empty_label = _muted("尚未登记数据源。")
        pre_layout.addWidget(self._pre_recognition_empty_label)
        self._pre_recognition_table = _table(["来源类型", "名称/编号", "路径/数据库", "登记状态"])
        self._pre_recognition_table.setObjectName("preRecognitionInputList")
        self._pre_recognition_table.setMinimumHeight(130)
        pre_layout.addWidget(self._pre_recognition_table)
        root.addWidget(pre_card)
        actions = QHBoxLayout()
        actions.addWidget(_button("开始数据识别", "primaryButton", self.run_recognition))
        actions.addWidget(_button("重新识别", "secondaryButton", self.run_recognition))
        actions.addWidget(_button("刷新报告", "secondaryButton", self.refresh_report))
        actions.addWidget(_button("清理旧识别结果", "secondaryButton", self.clean_old_recognition_results))
        actions.addWidget(_button("打开 recognized_data 文件夹", "secondaryButton", lambda: _open_path(self._project_root / "recognized_data" if self._project_root else None)))
        actions.addStretch(1)
        root.addLayout(actions)
        root.addWidget(
            _muted(
                "刷新报告只更新当前显示；重新识别会重新扫描当前项目数据目录；清理旧识别结果不会删除 raw_data 原始数据文件。"
            )
        )
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
        self._table = _table(["文件名", "原始位置", "识别类型", "识别可信度", "文件大小", "识别理由", "warning", "路由位置"])
        confidence_header = self._table.horizontalHeaderItem(3)
        if confidence_header is not None:
            confidence_header.setToolTip("软件根据文件内容推断文件类型的可信程度。它不是数据质量评分，也不是科研可信度评分。")
        root.addWidget(self._table)
        self._counts = _text_preview(120)
        root.addWidget(self._counts)
        self._technical_details = _text_preview(180)
        self._technical_details.setVisible(False)
        root.addWidget(_button("展开技术详情", "secondaryButton", lambda: _toggle_details(self._technical_details)), alignment=Qt.AlignLeft)
        root.addWidget(self._technical_details)
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
        self._pre_recognition_empty_label.setVisible(not rows)
        _fill_table(
            self._pre_recognition_table,
            [[row.source_type, row.source_label, row.location, row.status] for row in rows],
        )

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
                    _compact_path(str(item.get("original_path", "")), max_chars=58),
                    str(item.get("recognized_type_zh") or TYPE_LABELS.get(str(item.get("recognized_type")), "未知文件")),
                    _format_confidence(item.get("confidence")),
                    _format_file_size(item.get("file_size")),
                    str(item.get("reason", "")),
                    warning,
                    _compact_path(str(item.get("route_path", "")), max_chars=58),
                ]
            )
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                table_item = QTableWidgetItem(value)
                source = files[row_index]
                if col_index == 1:
                    table_item.setToolTip(str(source.get("original_path", "")))
                elif col_index == 3:
                    table_item.setToolTip("软件根据文件内容推断文件类型的可信程度。它不是数据质量评分，也不是科研可信度评分。")
                elif col_index == 4:
                    table_item.setToolTip(f"原始 bytes：{source.get('file_size', '未记录')}")
                elif col_index == 7:
                    table_item.setToolTip(str(source.get("route_path", "")))
                self._table.setItem(row_index, col_index, table_item)
        self._table.resizeColumnsToContents()

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
            self._status_label.setText("尚未运行 Ready 检查。")
            self._warning_chips.setText("关键警告：尚未运行")
            self._supplement_hint.setText("补充缺失信息会在运行 Ready 检查后按缺失项显示。")
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
        if normalized not in {"sample_metadata", "clinical_metadata", "expression_matrix"}:
            self._status_label.setText("当前缺失项暂不支持在本页补充。")
            return False
        if normalized == "expression_matrix" and mode == "manual":
            self._status_label.setText("表达矩阵仅支持选择本地文件补充。")
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
            supplement_dir = self._project_root / "raw_data" / "local_import" / "manual_supplements"
            supplement_dir.mkdir(parents=True, exist_ok=True)
            target = supplement_dir / f"{normalized}_manual.tsv"
            target.write_text((text or _template_text_for_missing_input(normalized)).strip() + "\n", encoding="utf-8")
            register_acquisition(
                self._project_root,
                source_type=f"manual_supplement_{normalized}",
                source_label=f"手动补充{_missing_input_label(normalized)}",
                strategy="reference",
                selected_paths=[target],
                metadata={"supplement_kind": normalized, "ui_stage": "UI-07", "manual_input": True},
            )
            self._status_label.setText(f"已保存手动补充的{_missing_input_label(normalized)}。")
            self.save_and_rerun_readiness()
            return True
        self._status_label.setText("未知补充方式。")
        return False

    def create_missing_info_template(self, kind: str) -> Path | None:
        if self._project_root is None:
            self._status_label.setText("请先创建或打开生信分析项目。")
            return None
        normalized = _normalize_missing_input(kind)
        if normalized not in {"sample_metadata", "clinical_metadata"}:
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
        root.addWidget(_header("数据准备状态", "Developer Preview / 本地测试版", back_text="返回数据识别", back_signal=self.back_requested))
        actions = QHBoxLayout()
        actions.addWidget(_button("运行 Ready 检查", "primaryButton", self.run_readiness_check))
        actions.addWidget(_button("刷新状态", "secondaryButton", self.refresh_status))
        actions.addStretch(1)
        root.addLayout(actions)

        status_bar = QFrame()
        status_bar.setObjectName("readinessCompactStatusBar")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(SPACING["lg"], SPACING["sm"], SPACING["lg"], SPACING["sm"])
        self._status_label = _status_label("尚未运行 Ready 检查。")
        self._status_label.setObjectName("readinessStatusBadge")
        self._warning_chips = QLabel("关键警告：尚未运行")
        self._warning_chips.setObjectName("readinessWarningChips")
        self._warning_chips.setWordWrap(True)
        status_layout.addWidget(self._status_label, 0)
        status_layout.addWidget(self._warning_chips, 1)
        root.addWidget(status_bar)

        supplement_card, supplement_layout = _card("补充缺失信息")
        supplement_card.setObjectName("readinessSupplementCard")
        self._supplement_hint = _muted("运行 Ready 检查后，这里会显示需要补充的样本信息、临床信息或表达矩阵。")
        supplement_layout.addWidget(self._supplement_hint)
        supplement_grid = QGridLayout()
        supplement_grid.setHorizontalSpacing(SPACING["sm"])
        supplement_grid.setVerticalSpacing(SPACING["sm"])
        self._sample_file_button = _button("选择样本信息文件", "secondaryButton", lambda: self.supplement_missing_info("sample_metadata", mode="file"))
        self._sample_manual_button = _button("手动输入样本信息", "secondaryButton", lambda: self.supplement_missing_info("sample_metadata", mode="manual"))
        self._sample_template_button = _button("下载样本信息模板", "secondaryButton", lambda: self.create_missing_info_template("sample_metadata"))
        self._clinical_file_button = _button("选择临床信息文件", "secondaryButton", lambda: self.supplement_missing_info("clinical_metadata", mode="file"))
        self._clinical_manual_button = _button("手动输入临床信息", "secondaryButton", lambda: self.supplement_missing_info("clinical_metadata", mode="manual"))
        self._clinical_template_button = _button("下载临床信息模板", "secondaryButton", lambda: self.create_missing_info_template("clinical_metadata"))
        self._expression_file_button = _button("选择表达矩阵文件", "secondaryButton", lambda: self.supplement_missing_info("expression_matrix", mode="file"))
        for index, button in enumerate(
            [
                self._sample_file_button,
                self._sample_manual_button,
                self._sample_template_button,
                self._clinical_file_button,
                self._clinical_manual_button,
                self._clinical_template_button,
                self._expression_file_button,
            ]
        ):
            supplement_grid.addWidget(button, index // 3, index % 3)
        supplement_layout.addLayout(supplement_grid)
        root.addWidget(supplement_card)

        self._matrix = _table(["分析", "是否可运行", "已有输入", "缺失输入", "警告", "下一步建议"])
        self._matrix.setObjectName("readinessCapabilityTable")
        self._matrix.setMinimumHeight(260)
        root.addWidget(self._matrix)

        self._details = _text_preview(130)
        self._details.setVisible(False)
        root.addWidget(_button("展开技术详情", "secondaryButton", lambda: _toggle_details(self._details)))
        root.addWidget(self._details)
        bottom_actions = QHBoxLayout()
        bottom_actions.addWidget(_button("保存并重新检查", "secondaryButton", self.save_and_rerun_readiness))
        bottom_actions.addWidget(_button("继续：标准化资产", "primaryButton", self.continue_to_standardization))
        bottom_actions.addStretch(1)
        root.addLayout(bottom_actions)

    def _render(self, artifacts: dict[str, object]) -> None:
        self._last_artifacts = artifacts
        readiness = artifacts.get("readiness_report") or {}
        matrix = artifacts.get("capability_matrix") or {}
        status = str(readiness.get("overall_status") or "unavailable") if isinstance(readiness, dict) else "unavailable"
        self._status_label.setText(f"当前 Ready 状态：{readiness_status_zh(status)}")
        warning_text = _readiness_warning_chips(readiness if isinstance(readiness, dict) else {}, matrix if isinstance(matrix, dict) else {})
        self._warning_chips.setText(warning_text)
        self._supplement_hint.setText(_supplement_hint_text(readiness if isinstance(readiness, dict) else {}, matrix if isinstance(matrix, dict) else {}))
        self._update_supplement_buttons(readiness if isinstance(readiness, dict) else {}, matrix if isinstance(matrix, dict) else {})
        self._details.setPlainText(_json({"readiness_report": readiness, "analysis_capability_matrix": matrix}))
        rows = matrix.get("rows", []) if isinstance(matrix, dict) else []
        _fill_table(
            self._matrix,
            [
                [
                    row.get("label", ""),
                    "可运行" if row.get("can_run") else "不可运行",
                    "、".join(str(item) for item in row.get("available_inputs", []) or []),
                    "、".join(str(item) for item in row.get("missing_inputs", []) or []) or "无",
                    "、".join(str(item) for item in row.get("warnings", []) or []),
                    row.get("next_step", ""),
                ]
                for row in rows
                if isinstance(row, dict)
            ],
        )

    def _update_supplement_buttons(self, readiness: dict[str, object], matrix: dict[str, object]) -> None:
        missing = _missing_readiness_inputs(readiness, matrix)
        self._sample_file_button.setVisible("sample_metadata" in missing)
        self._sample_manual_button.setVisible("sample_metadata" in missing)
        self._sample_template_button.setVisible("sample_metadata" in missing)
        self._clinical_file_button.setVisible("clinical_metadata" in missing)
        self._clinical_manual_button.setVisible("clinical_metadata" in missing)
        self._clinical_template_button.setVisible("clinical_metadata" in missing)
        self._expression_file_button.setVisible("expression_matrix" in missing)
        if not missing:
            for button in (
                self._sample_file_button,
                self._sample_manual_button,
                self._sample_template_button,
                self._clinical_file_button,
                self._clinical_manual_button,
                self._clinical_template_button,
                self._expression_file_button,
            ):
                button.setVisible(False)


class BioinformaticsStandardizedAssetsWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()

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
            self._summary.setPlainText("")
            self._manifest.setPlainText("")
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
        root.addWidget(_header("标准化资产", "当前为资产注册和轻量校验，不等于正式 biological normalization。", back_text="返回 Ready 检查", back_signal=self.back_requested))
        actions = QHBoxLayout()
        actions.addWidget(_button("生成标准化资产", "primaryButton", self.generate_assets))
        actions.addWidget(_button("刷新资产状态", "secondaryButton", self.refresh_assets))
        actions.addWidget(_button("打开 standardized_data 文件夹", "secondaryButton", lambda: _open_path(self._project_root / "standardized_data" if self._project_root else None)))
        actions.addStretch(1)
        root.addLayout(actions)
        self._status_label = _status_label("尚未生成标准化资产。")
        root.addWidget(self._status_label)
        self._assets = _table(["资产类型", "中文名称", "文件路径", "来源文件", "materialize 策略", "validation 状态", "warning", "analysis-ready"])
        root.addWidget(self._assets)
        self._summary = _text_preview(140)
        root.addWidget(self._summary)
        self._manifest = _text_preview(150)
        self._manifest.setVisible(False)
        root.addWidget(_button("展开技术详情", "secondaryButton", lambda: _toggle_details(self._manifest)))
        root.addWidget(self._manifest)
        root.addWidget(_button("继续：生信工作流总控", "primaryButton", self.continue_to_workflow), alignment=Qt.AlignLeft)

    def _render(self, artifacts: dict[str, object]) -> None:
        registry = artifacts.get("registry") or {}
        manifest = artifacts.get("analysis_ready_manifest") or {}
        assets = registry.get("assets", []) if isinstance(registry, dict) else []
        warnings = registry.get("warnings", []) if isinstance(registry, dict) else []
        self._status_label.setText(f"标准化资产：{len(assets)} 个，warning {len(warnings)} 条。")
        _fill_table(
            self._assets,
            [
                [
                    item.get("asset_type", ""),
                    item.get("label_zh", ""),
                    item.get("file_path", ""),
                    item.get("source_file", ""),
                    item.get("materialize_strategy", ""),
                    item.get("validation_status", ""),
                    item.get("warning", ""),
                    "是" if item.get("analysis_ready") else "否",
                ]
                for item in assets
                if isinstance(item, dict)
            ],
        )
        self._summary.setPlainText(_standardization_user_summary(registry if isinstance(registry, dict) else {}, manifest if isinstance(manifest, dict) else {}))
        self._manifest.setPlainText(_json({"analysis-ready manifest": manifest, "warning": warnings}))


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
        root.addWidget(_header("分析任务中心", "Developer Preview / 本地测试版", back_text="返回工作流总控", back_signal=self.back_requested))
        self._status_label = _status_label("没有 task center 时请先运行工作流或生成任务中心。")
        root.addWidget(self._status_label)
        actions = QHBoxLayout()
        actions.addWidget(_button("刷新任务中心", "secondaryButton", self.refresh_task_center))
        self._task_type_input = QLineEdit()
        self._task_type_input.setPlaceholderText("task type，例如 differential_expression")
        actions.addWidget(self._task_type_input)
        actions.addWidget(_button("创建任务", "primaryButton", self.create_task))
        actions.addStretch(1)
        root.addLayout(actions)
        self._tasks = _table(["任务", "是否可运行", "已有输入", "缺失输入", "warning", "默认参数", "preview"])
        root.addWidget(self._tasks)
        self._records = _text_preview(120)
        root.addWidget(self._records)
        root.addWidget(_button("继续：结果浏览", "primaryButton", self.continue_to_results), alignment=Qt.AlignLeft)

    def _render(self, center: dict[str, object]) -> None:
        tasks = [item for item in center.get("tasks", []) or [] if isinstance(item, dict)]
        self._status_label.setText(f"分析任务中心：{len(tasks)} 个任务模板。不可运行任务将显示缺失输入。")
        _fill_table(
            self._tasks,
            [
                [
                    item.get("label", ""),
                    "可运行" if item.get("can_run") else "不可运行",
                    "、".join(str(v) for v in item.get("available_inputs", []) or []),
                    "、".join(str(v) for v in item.get("missing_inputs", []) or []),
                    "、".join(str(v) for v in item.get("warnings", []) or []),
                    _json(item.get("default_parameters", {})),
                    item.get("preview_status", ""),
                ]
                for item in tasks
            ],
        )
        self._records.setPlainText(_json({"已创建任务": load_task_records(self._project_root) if self._project_root else []}))


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
        actions.addWidget(_button("加入报告", "secondaryButton", lambda: self._status_label.setText("加入报告：占位功能。")))
        actions.addStretch(1)
        root.addLayout(actions)
        self._results = _table(["结果名称", "分析类型", "文件类型", "创建时间", "路径", "状态", "warning"])
        root.addWidget(self._results)
        self._details = _text_preview(130)
        root.addWidget(self._details)
        root.addWidget(_button("继续：报告查看", "primaryButton", self.continue_to_report), alignment=Qt.AlignLeft)

    def _render(self, payload: dict[str, object]) -> None:
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
        payload = load_result_index(self._project_root)
        entries = [item for item in payload.get("entries", []) or [] if isinstance(item, dict)]
        if not entries:
            self._status_label.setText("不能生成报告：暂无可用于报告的结果。请返回数据来源补充文件，完成分析并生成结果后再生成报告。")
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
        root.addWidget(_header("项目报告", "Developer Preview / 本地测试版", back_text="返回结果浏览", back_signal=self.back_requested))
        actions = QHBoxLayout()
        actions.addWidget(_button("生成 / 刷新项目报告", "primaryButton", self.generate_report))
        actions.addWidget(_button("打开报告文件", "secondaryButton", lambda: _open_path(self._project_root / "reports/project_analysis_report.md" if self._project_root else None)))
        actions.addWidget(_button("打开报告文件夹", "secondaryButton", lambda: _open_path(self._project_root / "reports" if self._project_root else None)))
        actions.addWidget(_button("导出 DOCX", "secondaryButton", lambda: self._status_label.setText("DOCX 导出：testing placeholder，未正式支持。")))
        actions.addWidget(_button("导出 HTML", "secondaryButton", lambda: self._status_label.setText("HTML 导出：testing placeholder。")))
        actions.addStretch(1)
        root.addLayout(actions)
        self._status_label = _status_label("没有报告时请点击生成 / 刷新项目报告。PDF 当前未正式支持。")
        root.addWidget(self._status_label)
        self._markdown = _text_preview(320)
        root.addWidget(self._markdown)
        self._manifest = _text_preview(140)
        root.addWidget(self._manifest)

    def _render(self, payload: dict[str, object]) -> None:
        markdown = str(payload.get("markdown") or "")
        manifest = payload.get("manifest")
        if not markdown:
            self._status_label.setText("尚未生成项目报告。PDF 当前未正式支持。")
            self._markdown.setPlainText("")
        else:
            self._status_label.setText("已读取项目级 Markdown 报告。PDF 当前只能显示 placeholder，未正式支持。")
            self._markdown.setPlainText(markdown)
        self._manifest.setPlainText(_json(manifest or {"PDF": "未正式支持", "DOCX": "testing placeholder"}))


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
        terms = _placeholder_terms(text)
        self._preview.setPlainText(terms)
        return terms

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
        self._ai_status = _status_label(
            "未检测到本地 AI 服务，当前可使用规则占位模式。"
            if shutil.which("ollama") is None
            else "本地 AI：检测到 Ollama 命令；Translator / Media 模型状态仍为占位。"
        )
        ai_layout.addWidget(self._ai_status)
        ai_layout.addWidget(_muted("Translator 模型状态：占位。Media 模型状态：占位。"))
        self._question_input = QLineEdit()
        self._question_input.setPlaceholderText("输入中文研究问题")
        ai_layout.addWidget(self._question_input)
        row = QHBoxLayout()
        row.addWidget(_button("生成英文医学词", "secondaryButton", self.generate_placeholder_terms))
        row.addWidget(_button("生成 GEO 检索关键词", "secondaryButton", self.generate_placeholder_terms))
        row.addStretch(1)
        ai_layout.addLayout(row)
        self._preview = _text_preview(120)
        self._preview.setPlainText("本地 AI 仅用于翻译、关键词扩展和检索辅助；不参与统计分析，不生成科研结论，不替代人工判断。")
        ai_layout.addWidget(self._preview)
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


def _registered_source_rows(project_root: Path | None) -> list[RegisteredSourceRow]:
    if project_root is None:
        return []
    records_dir = project_root / "acquisition" / "records"
    if not records_dir.exists():
        return []
    rows: list[RegisteredSourceRow] = []
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
        rows.append(
            RegisteredSourceRow(
                acquisition_id=acquisition_id,
                source_type_key=source_type,
                source_type=_source_type_label(source_type),
                source_label=source_label,
                location=_registered_source_location(payload, metadata),  # type: ignore[arg-type]
                status=_registered_status_text(payload),
                created_at=str(payload.get("created_at") or ""),
                strategy=str(payload.get("strategy") or ""),
            )
        )
    return sorted(rows, key=lambda row: row.created_at)


def _registered_source_display_name(payload: dict[str, object], metadata: dict[str, object]) -> str:
    source_type = str(payload.get("source_type") or "")
    if source_type == "local_import":
        values = payload.get("registered_files") or payload.get("referenced_paths") or payload.get("copied_files")
        if isinstance(values, list) and values:
            return Path(str(values[0])).name
    return str(payload.get("source_label") or metadata.get("accession_or_project") or "未知数据源")


def _registered_source_location(payload: dict[str, object], metadata: dict[str, object]) -> str:
    for key in ("registered_files", "referenced_paths", "copied_files"):
        values = payload.get(key)
        if isinstance(values, list) and values:
            return _compact_path(str(values[0]))
    source = str(metadata.get("source") or "")
    if source == "geo" or payload.get("source_type") == "geo_gse":
        return "GEO"
    if source == "tcga_gdc" or "tcga" in str(payload.get("source_type") or ""):
        return "GDC / TCGA"
    if source == "gtex" or "gtex" in str(payload.get("source_type") or ""):
        return "GTEx"
    return "项目登记记录"


def _registered_status_text(payload: dict[str, object]) -> str:
    warnings = payload.get("warnings")
    if isinstance(warnings, list) and warnings:
        return "已登记，需确认"
    return "已登记"


def _source_type_label(source_type: str) -> str:
    return {
        "local_import": "本地数据导入",
        "geo_series_matrix": "GEO Series Matrix",
        "tcga_local_folder": "TCGA 本地数据",
        "gtex_local_folder": "GTEx 本地数据",
        "tcga_gtex_tcga_folder": "TCGA + GTEx / TCGA 来源",
        "tcga_gtex_gtex_folder": "TCGA + GTEx / GTEx 来源",
        "geo_gse": "GSE 编号检索",
        "chinese_geo_gse": "GSE 编号检索",
        "chinese_tcga_gdc_project": "TCGA/GDC 项目",
        "chinese_gtex_tissue": "GTEx 正常组织参考",
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
        "plan_only": "已登记编号，等待数据获取",
    }.get(policy, policy)


def _acquisition_status_text(summary: AcquisitionSummary) -> str:
    parts = []
    parts.append("数据获取计划：已生成" if summary.plan_path.exists() else "数据获取计划：未生成")
    parts.append("数据登记记录：已生成" if summary.record_path.exists() else "数据登记记录：未生成")
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
        f"当前数据来源：{summary.source_label}",
        f"来源内容：{summary.display_name}",
        f"{_kind_label(summary)}：{summary.display_name}",
        f"来源位置：{path}",
        f"保存方式：{_storage_policy_text(summary.storage_policy)}",
        f"登记状态：{registration_state}",
        summary.acquisition_status,
        f"最近登记时间：{summary.created_at or '未记录'}",
        f"下一步建议：{next_step}",
    ]
    if summary.source_type in {"tcga_gtex_tcga_folder", "tcga_gtex_gtex_folder"}:
        lines.append("警告：当前未进行正式 batch correction，后续分析需谨慎解释。")
    if summary.warnings:
        lines.append(f"warning：{'；'.join(summary.warnings)}")
    return "\n".join(lines)


def _source_card_status_text(summary: SelectedSourceSummary) -> str:
    if summary.source_type == "geo_gse" or summary.selected_kind == "accession":
        return f"已登记 GSE 数据集：{summary.display_name}"
    if summary.source_type == "local_import":
        return f"已登记本地数据：{_compact_path(summary.display_name, max_chars=58)}"
    if summary.storage_policy == "plan_only":
        return f"{summary.source_label}待登记确认。"
    return f"已登记本地数据：{_compact_path(summary.display_name, max_chars=58)}"


def _chinese_search_entry_status(rows: list[RegisteredSourceRow]) -> str:
    chinese_rows = [row for row in rows if row.source_type_key.startswith("chinese_")]
    if not chinese_rows:
        return "尚未进行中文检索。"
    return f"最近中文检索：已登记 {len(chinese_rows)} 个数据源。"


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
            "处理状态：已登记到项目。\n"
            "当前版本尚未接入可用的 GEO 元数据检索组件；也不会自动联网下载数据。\n"
            "下一步建议：请导入已下载的 Series Matrix 文件，或等待后续版本中使用自动下载。"
        )
    try:
        result = fetcher_cls(timeout=8).search_series(gse_id, max_results=3, page_size=3)
    except Exception as exc:
        return (
            f"当前 GSE 编号：{gse_id}\n"
            "处理状态：已登记到项目；本次联网元数据检索未完成。\n"
            f"检索提示：{exc}\n"
            "当前不会自动下载数据。请导入已下载的 Series Matrix 文件，或等待后续版本中使用自动下载。"
        )
    matched = [item for item in result.results if item.gse_id.upper() == gse_id.upper()] or result.results[:1]
    if not matched:
        return (
            f"当前 GSE 编号：{gse_id}\n"
            "处理状态：已登记到项目；GEO 元数据检索未返回匹配数据集。\n"
            "当前不会自动下载数据。请确认编号，或导入已下载的 Series Matrix 文件。"
        )
    info = matched[0]
    return "\n".join(
        [
            f"当前 GSE 编号：{info.gse_id}",
            "处理状态：已获取 GEO 元数据并登记到项目；当前不会自动下载数据。",
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
        status="尚未登记",
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
        return "chinese_geo_gse"
    if candidate.source == "tcga_gdc":
        return "chinese_tcga_gdc_project"
    if candidate.source == "gtex":
        return "chinese_gtex_tissue"
    return f"chinese_{candidate.source}"


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


def _candidate_recommendation(candidate: UnifiedDatasetCandidate) -> str:
    if candidate.score >= 80:
        return "高"
    if candidate.score >= 55:
        return "中"
    return "低"


def _geo_empty_state_text(source_result: object | None, *, searched: bool) -> str:
    if not searched:
        return "已生成 GEO/GSE 检索草稿，尚未执行在线检索。"
    status = str(getattr(source_result, "search_status", "") or "")
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


def _global_source_summary_text(summary: SelectedSourceSummary) -> str:
    if summary.selected_kind == "accession":
        return (
            f"最近登记的数据来源：GSE 编号检索；来源内容：{summary.display_name}；"
            f"保存方式：{_storage_policy_text(summary.storage_policy)}；登记状态：需要补充数据；"
            "下一步：导入已下载的 Series Matrix 文件，或等待后续版本接入自动下载。"
        )
    return (
        f"最近登记的数据来源：{summary.source_label}；来源内容：{summary.display_name}；"
        f"来源位置：{_compact_path(summary.absolute_path)}；保存方式：{_storage_policy_text(summary.storage_policy)}；登记状态：已完成。"
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
            f"登记文件：{file_count} 个",
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
    warnings = [_friendly_readiness_text(str(item)) for item in readiness.get("warnings", []) or []]
    missing = [_missing_input_label(item) for item in _missing_readiness_inputs(readiness, matrix)]
    chips = list(dict.fromkeys([*warnings, *[f"缺少{item}" for item in missing]]))
    if not chips:
        return "关键警告：无"
    return "关键警告：" + "  ".join(f"【{chip}】" for chip in chips[:5])


def _supplement_hint_text(readiness: dict[str, object], matrix: dict[str, object]) -> str:
    missing = [_missing_input_label(item) for item in _missing_readiness_inputs(readiness, matrix)]
    if not missing:
        return "关键输入已基本满足。可以继续生成标准化资产；如仍有警告，可先处理后再继续。"
    return "检测到缺失信息：" + "、".join(missing) + "。请补充后点击“保存并重新检查”。"


def _missing_readiness_inputs(readiness: dict[str, object], matrix: dict[str, object]) -> set[str]:
    missing: set[str] = set()
    if not readiness.get("has_core_input"):
        missing.add("expression_matrix")
    rows = [row for row in matrix.get("rows", []) or [] if isinstance(row, dict)]
    for row in rows:
        for item in row.get("missing_inputs", []) or []:
            normalized = _normalize_missing_input(str(item))
            if normalized in {"sample_metadata", "clinical_metadata", "expression_matrix"}:
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
        "表达矩阵": "expression_matrix",
        "基因表达数据": "expression_matrix",
    }
    return mapping.get(text, text)


def _missing_input_label(value: str) -> str:
    normalized = _normalize_missing_input(value)
    return {
        "sample_metadata": "样本信息",
        "clinical_metadata": "临床信息",
        "expression_matrix": "表达矩阵",
    }.get(normalized, "其他缺失资产")


def _friendly_readiness_text(text: str) -> str:
    return (
        text.replace("无表达矩阵。", "缺少表达矩阵")
        .replace("样本信息缺失。", "缺少样本信息")
        .replace("临床信息缺失。", "缺少临床信息")
        .replace("。", "")
    )


def _template_text_for_missing_input(kind: str) -> str:
    normalized = _normalize_missing_input(kind)
    if normalized == "sample_metadata":
        return "sample_id\tgroup\nsample_1\tcase\nsample_2\tcontrol\n"
    if normalized == "clinical_metadata":
        return "sample_id\tsurvival_time\tsurvival_status\tage\nsample_1\t未记录\t未记录\t未记录\n"
    return "gene\tsample_1\tsample_2\nTP53\t1\t2\n"


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


def _format_confidence(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "未记录"
    return f"{numeric * 100:.0f}%"


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
    type_lines = []
    for key, label in TYPE_LABELS.items():
        count = int(counts.get(key, 0) or 0)
        if count:
            type_lines.append(f"{label}：{count}")
    if project_root is not None and not _current_effective_source_paths(project_root):
        source_note = "当前版本会扫描项目 raw_data 中所有已登记文件，因此历史导入副本也可能显示在识别结果中。"
    else:
        source_note = f"当前有效数据来源文件：{effective_count} 个。"
    next_step = "如果已识别到表达矩阵或原始计数矩阵，可以继续 Ready 检查；否则请返回数据来源补充文件。"
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
    has_core = any(str(item.get("recognized_type")) in {"expression_matrix", "raw_count_matrix"} for item in files)
    if not has_core:
        return False, "未识别到表达矩阵或原始计数矩阵。"
    return True, ""


def _can_continue_from_readiness(project_root: Path) -> tuple[bool, str]:
    artifacts = load_readiness_artifacts(project_root)
    readiness = artifacts.get("readiness_report")
    if not isinstance(readiness, dict):
        return False, "尚未运行 Ready 检查。"
    status = str(readiness.get("overall_status") or "unavailable")
    if status in {"not_ready", "unavailable"} or not readiness.get("has_core_input"):
        return False, f"当前 Ready 状态为“{readiness_status_zh(status)}”。"
    return True, ""


def _can_continue_from_standardization(project_root: Path) -> tuple[bool, str]:
    artifacts = load_standardization_artifacts(project_root)
    registry = artifacts.get("registry")
    if not isinstance(registry, dict):
        return False, "尚未生成标准化资产。"
    assets = [item for item in registry.get("assets", []) or [] if isinstance(item, dict)]
    has_ready_core = any(item.get("analysis_ready") and str(item.get("asset_type")) in {"expression_matrix", "raw_count_matrix"} for item in assets)
    if not has_ready_core:
        return False, "没有 analysis-ready 表达矩阵资产。"
    return True, ""


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
