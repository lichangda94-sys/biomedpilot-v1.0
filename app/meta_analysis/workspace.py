from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path

from app.shared.feature_availability import FeatureAvailability, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability
from app.shared.storage import default_storage_root


def meta_analysis_features() -> list[FeatureItem]:
    return [feature_item_from_availability(feature) for feature in meta_analysis_step_features()]


def meta_analysis_step_features() -> list[FeatureAvailability]:
    step_ids = {
        "meta-literature-import",
        "meta-dedup-prep",
        "meta-duplicate-review",
        "meta-screening",
        "meta-extraction",
        "meta-analysis",
        "meta-reporting",
    }
    return [feature for feature in list_features("meta_analysis") if feature.feature_id in step_ids]


@dataclass(frozen=True)
class ImportBatchQualitySummary:
    batch_id: str
    project_id: str
    source_database: str
    source_format: str
    status: str
    created_at: str
    raw_record_count: int
    parsed_record_count: int
    normalized_record_count: int
    failed_record_count: int
    warning_count: int
    duplicate_candidate_count: int
    linked_literature_record_count: int
    diagnostics_path: str
    diagnostics_summary: str = ""


@dataclass(frozen=True)
class LiteratureImportQualityDashboardState:
    title: str
    status_label: str
    description: str
    empty_state: str
    batch_count: int
    batches: tuple[ImportBatchQualitySummary, ...]


@dataclass(frozen=True)
class MetaWorkspaceNavigationItem:
    step_id: str
    label: str
    description: str
    page_key: str
    status_label: str = "Testing / Developer Preview"


@dataclass(frozen=True)
class MetaWorkspaceLayoutState:
    title: str
    status_label: str
    description: str
    navigation_items: tuple[MetaWorkspaceNavigationItem, ...]
    default_page_key: str
    testing_notice: str


def meta_workspace_layout_state() -> MetaWorkspaceLayoutState:
    return MetaWorkspaceLayoutState(
        title="Meta Analysis / 医学 Meta 分析工作台",
        status_label="Developer Preview / testing",
        description="按 Meta 项目流程组织页面入口；每个页面只调用 service/page-state，不在 UI 中写核心业务逻辑。",
        navigation_items=(
            MetaWorkspaceNavigationItem("workflow_dashboard", "总控 Workflow", "查看项目全流程状态、warning 和下一步。", "workflow_dashboard"),
            MetaWorkspaceNavigationItem("protocol", "Protocol / PICO", "记录研究问题、PICO/PICOS 和检索策略草稿。", "protocol"),
            MetaWorkspaceNavigationItem("literature_import", "Literature Import", "导入 RIS / NBIB / CSV 并查看 diagnostics。", "literature_import"),
            MetaWorkspaceNavigationItem("import_quality", "Import Quality", "查看 recent import batches 和导入质量摘要。", "import_quality"),
            MetaWorkspaceNavigationItem("literature_library", "Literature Library", "查看文献表、duplicate risk 和状态标签。", "literature_library"),
            MetaWorkspaceNavigationItem("prepare_screening", "Prepare Screening", "生成筛选准备数据和旧链路兼容入口。", "prepare_screening"),
            MetaWorkspaceNavigationItem("duplicate_review", "Duplicate Review", "查看 duplicate groups、merge preview 和决策入口。", "duplicate_review"),
            MetaWorkspaceNavigationItem("criteria", "Criteria", "维护 inclusion / exclusion criteria。", "criteria"),
            MetaWorkspaceNavigationItem("screening", "Screening", "执行 title/abstract screening。", "screening"),
            MetaWorkspaceNavigationItem("attachment", "Full-text / Attachment", "管理附件、missing full-text 和 link/copy 状态。", "attachment"),
            MetaWorkspaceNavigationItem("fulltext_eligibility", "Full-text Eligibility", "完成全文资格审查和最终纳入清单。", "fulltext_eligibility"),
            MetaWorkspaceNavigationItem("extraction", "Extraction", "录入结构化提取数据、草稿和完整性检查。", "extraction"),
            MetaWorkspaceNavigationItem("quality", "Quality", "填写质量评价并导出 quality table。", "quality"),
            MetaWorkspaceNavigationItem("analysis", "Analysis", "构建 dataset、运行 testing meta-analysis 并查看 warnings。", "analysis"),
            MetaWorkspaceNavigationItem("reporting", "Reporting", "生成 PRISMA、报告、导出和复现包。", "reporting"),
            MetaWorkspaceNavigationItem("audit", "Audit", "查看 audit log 和 review log 导出状态。", "audit"),
        ),
        default_page_key="workflow_dashboard",
        testing_notice="当前 Meta Analysis 仍为 Developer Preview / testing；所有结果需要人工复核，不能作为 production 结论。",
    )


def recent_import_batch_summaries(root_dir: Path | None = None, *, limit: int = 5) -> list[dict[str, object]]:
    return [
        {
            "project_id": summary.project_id,
            "batch_id": summary.batch_id,
            "source_database": summary.source_database,
            "format": summary.source_format,
            "source_format": summary.source_format,
            "status": summary.status,
            "raw_record_count": summary.raw_record_count,
            "parsed_count": summary.parsed_record_count,
            "parsed_record_count": summary.parsed_record_count,
            "normalized_record_count": summary.normalized_record_count,
            "failed_record_count": summary.failed_record_count,
            "warning_count": summary.warning_count,
            "duplicate_candidate_count": summary.duplicate_candidate_count,
            "linked_literature_record_count": summary.linked_literature_record_count,
            "diagnostics_path": summary.diagnostics_path,
            "diagnostics_summary": summary.diagnostics_summary,
            "created_at": summary.created_at,
        }
        for summary in recent_import_batch_quality_summaries(root_dir, limit=limit)
    ]


def recent_import_batch_quality_summaries(root_dir: Path | None = None, *, limit: int = 5) -> list[ImportBatchQualitySummary]:
    root = root_dir or default_storage_root()
    projects_root = root / "projects"
    summaries: list[ImportBatchQualitySummary] = []
    if projects_root.exists():
        for path in projects_root.glob("*/meta_analysis/literature_import/*_records.json"):
            payload = _load_json_object(path)
            if payload:
                summaries.append(_summary_from_unified_import(path, payload))
    summaries.extend(_legacy_import_batch_summaries(root))
    deduped = {f"{item.project_id}:{item.batch_id}:{item.created_at}": item for item in summaries}
    return sorted(deduped.values(), key=lambda item: item.created_at, reverse=True)[:limit]


def literature_import_quality_dashboard_state(root_dir: Path | None = None, *, limit: int = 5) -> LiteratureImportQualityDashboardState:
    batches = tuple(recent_import_batch_quality_summaries(root_dir, limit=limit))
    return LiteratureImportQualityDashboardState(
        title="Meta Literature Import Quality Dashboard",
        status_label="Testing / Developer Preview",
        description="只读显示最近文献导入批次的解析质量、warning 数量、failed 数量、duplicate candidate 数量和 diagnostics 路径。",
        empty_state="暂无导入批次。请先在 Literature Import 页面导入 NBIB / RIS / CSV 文件。",
        batch_count=len(batches),
        batches=batches,
    )


def _summary_from_unified_import(path: Path, payload: dict[str, object]) -> ImportBatchQualitySummary:
    records = list(payload.get("records", []))
    diagnostics_path = str(payload.get("diagnostics_path", ""))
    diagnostics = _load_json_object(Path(diagnostics_path)) if diagnostics_path else {}
    source_type = str(payload.get("source_type", ""))
    return ImportBatchQualitySummary(
        batch_id=str(payload.get("batch_id", path.stem.replace("_records", ""))),
        project_id=str(payload.get("project_id", path.parents[2].name)),
        source_database=str(payload.get("source_database") or source_type or "local_file"),
        source_format=str(payload.get("source_format") or source_type),
        status=str(payload.get("status") or "completed"),
        created_at=str(payload.get("created_at", "")),
        raw_record_count=_int_from(diagnostics, "raw_record_count", len(records)),
        parsed_record_count=_int_from(diagnostics, "parsed_record_count", len(records)),
        normalized_record_count=_int_from(diagnostics, "normalized_record_count", len(records)),
        failed_record_count=_int_from(diagnostics, "failed_record_count", 0),
        warning_count=_int_from(diagnostics, "warning_count", _int_from(payload, "warning_count", 0)),
        duplicate_candidate_count=_int_from(diagnostics, "duplicate_candidate_count", _int_from(payload, "duplicate_candidate_count", 0)),
        linked_literature_record_count=len(records),
        diagnostics_path=diagnostics_path,
        diagnostics_summary=_diagnostics_summary_text(diagnostics),
    )


def _legacy_import_batch_summaries(root: Path) -> list[ImportBatchQualitySummary]:
    batches_path = root / "literature" / "import_batches.json"
    if not batches_path.exists():
        return []
    summaries: list[ImportBatchQualitySummary] = []
    for item in _load_json_list(batches_path):
        batch_id = str(item.get("batch_id", ""))
        diagnostics_path = root / "literature" / "import_diagnostics" / f"{batch_id}_import_diagnostics.json"
        diagnostics = _load_json_object(diagnostics_path)
        metadata = dict(item.get("metadata", {})) if isinstance(item.get("metadata"), dict) else {}
        summaries.append(
            ImportBatchQualitySummary(
                batch_id=batch_id,
                project_id=str(item.get("project_id", "")),
                source_database=str(metadata.get("source_database") or item.get("source_type", "")),
                source_format=str(item.get("format_hint", "")),
                status=str(item.get("status", "")),
                created_at=str(item.get("created_at", "")),
                raw_record_count=_int_from(item, "raw_record_count", _int_from(item, "total_records", 0)),
                parsed_record_count=_int_from(item, "parsed_record_count", _int_from(item, "imported_records", 0)),
                normalized_record_count=_int_from(item, "normalized_record_count", _int_from(item, "imported_records", 0)),
                failed_record_count=_int_from(item, "failed_records", _int_from(item, "failed_record_count", 0)),
                warning_count=_int_from(item, "warning_count", _int_from(diagnostics, "warning_count", 0)),
                duplicate_candidate_count=_int_from(item, "duplicate_candidate_count", _int_from(diagnostics, "duplicate_candidate_count", 0)),
                linked_literature_record_count=_int_from(item, "normalized_record_count", _int_from(item, "imported_records", 0)),
                diagnostics_path=str(diagnostics_path) if diagnostics_path.exists() else "",
                diagnostics_summary=_diagnostics_summary_text(diagnostics),
            )
        )
    return summaries


def _load_json_object(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_json_list(path: Path) -> list[dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return [dict(item) for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []


def _int_from(payload: dict[str, object], key: str, fallback: int = 0) -> int:
    try:
        return int(payload.get(key, fallback))
    except (TypeError, ValueError):
        return fallback


def _diagnostics_summary_text(diagnostics: dict[str, object]) -> str:
    if not diagnostics:
        return ""
    fields = (
        "missing_title_count",
        "missing_author_count",
        "missing_year_count",
        "missing_doi_count",
        "missing_pmid_count",
        "invalid_year_count",
        "invalid_doi_count",
    )
    return "; ".join(f"{field}={_int_from(diagnostics, field)}" for field in fields if _int_from(diagnostics, field))


try:
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QScrollArea,
        QSplitter,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt
except Exception:  # pragma: no cover
    QFrame = QHBoxLayout = QLabel = QListWidget = QListWidgetItem = QPushButton = QScrollArea = QSplitter = QStackedWidget = QVBoxLayout = QWidget = None
    Qt = None


if QWidget is not None:
    from app.meta_analysis.pages.literature_import_page import LiteratureImportPage
    from app.meta_analysis.pages.literature_library_page import LiteratureLibraryPage
    from app.meta_analysis.pages.criteria_page import CriteriaPage
    from app.meta_analysis.pages.prepare_screening_page import PrepareScreeningPage
    from app.meta_analysis.pages.duplicate_review_page import DuplicateReviewPage
    from app.meta_analysis.pages.screening_page import ScreeningPage
    from app.meta_analysis.pages.extraction_page import ExtractionPage
    from app.meta_analysis.pages.quality_page import initial_quality_state
    from app.meta_analysis.pages.analysis_page import AnalysisPage
    from app.meta_analysis.pages.reporting_page import ReportingPage
    from app.meta_analysis.pages.attachment_page import AttachmentPage
    from app.meta_analysis.pages.fulltext_eligibility_page import FullTextEligibilityPage
    from app.meta_analysis.pages.audit_log_page import AuditLogPage
    from app.meta_analysis.pages.protocol_page import ProtocolPage
    from app.meta_analysis.pages.workflow_dashboard_page import WorkflowDashboardPage

    class MetaAnalysisWorkspaceWidget(QWidget):
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            self._layout_state = meta_workspace_layout_state()
            root = QVBoxLayout(self)
            header = QHBoxLayout()
            title = QLabel(self._layout_state.title)
            title.setStyleSheet("font-size: 24px; font-weight: 700;")
            header.addWidget(title)
            header.addStretch(1)
            status = QLabel(self._layout_state.status_label)
            status.setStyleSheet("color: #8A4B00; font-weight: 600;")
            header.addWidget(status)
            back = QPushButton("返回首页")
            if on_back:
                back.clicked.connect(on_back)
            header.addWidget(back)
            root.addLayout(header)

            note = QLabel(self._layout_state.testing_notice)
            note.setWordWrap(True)
            root.addWidget(note)

            splitter = QSplitter()
            if Qt is not None:
                splitter.setOrientation(Qt.Orientation.Horizontal)
            self._navigation_list = QListWidget()
            self._navigation_list.setMinimumWidth(230)
            self._navigation_list.setMaximumWidth(320)
            self._page_stack = QStackedWidget()
            self._page_keys: list[str] = []
            pages = _workspace_pages()
            for item in self._layout_state.navigation_items:
                list_item = QListWidgetItem(item.label)
                list_item.setToolTip(f"{item.status_label}\n{item.description}")
                self._navigation_list.addItem(list_item)
                self._page_stack.addWidget(_scroll_page(pages[item.page_key]))
                self._page_keys.append(item.page_key)
            self._navigation_list.currentRowChanged.connect(self._page_stack.setCurrentIndex)
            splitter.addWidget(self._navigation_list)
            splitter.addWidget(self._page_stack)
            splitter.setSizes([260, 900])
            root.addWidget(splitter, 1)
            self._navigation_list.setCurrentRow(0)

        def page_keys(self) -> tuple[str, ...]:
            return tuple(self._page_keys)

        def current_page_key(self) -> str:
            row = self._navigation_list.currentRow()
            if row < 0 or row >= len(self._page_keys):
                return ""
            return self._page_keys[row]


    def _feature_row(feature: FeatureAvailability) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        title = QLabel(feature.display_label())
        title.setStyleSheet("font-weight: 700;")
        detail = QLabel(feature.description)
        detail.setWordWrap(True)
        source = QLabel(f"legacy 来源：{feature.legacy_source or '统一壳子占位'}")
        source.setWordWrap(True)
        next_step = QLabel(f"下一步：{feature.next_step}")
        next_step.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(detail)
        layout.addWidget(source)
        layout.addWidget(next_step)
        return frame


    def _workspace_pages() -> dict[str, QWidget]:
        return {
            "workflow_dashboard": WorkflowDashboardPage(),
            "protocol": ProtocolPage(),
            "literature_import": LiteratureImportPage(),
            "import_quality": _import_quality_dashboard(),
            "literature_library": LiteratureLibraryPage(),
            "prepare_screening": PrepareScreeningPage(),
            "duplicate_review": DuplicateReviewPage(),
            "criteria": CriteriaPage(),
            "screening": ScreeningPage(),
            "attachment": AttachmentPage(),
            "fulltext_eligibility": FullTextEligibilityPage(),
            "extraction": ExtractionPage(),
            "quality": _quality_page_panel(),
            "analysis": AnalysisPage(),
            "reporting": ReportingPage(),
            "audit": AuditLogPage(),
        }


    def _scroll_page(widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        return scroll


    def _quality_page_panel() -> QFrame:
        state = initial_quality_state()
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        title = QLabel(f"{state.title} · {state.status_label}")
        title.setStyleSheet("font-weight: 700; font-size: 16px;")
        description = QLabel(state.description)
        description.setWordWrap(True)
        tools = QLabel(f"Tools: {', '.join(state.tool_options)}")
        tools.setWordWrap(True)
        sections = QLabel(f"Form sections: {', '.join(state.form_sections)}")
        sections.setWordWrap(True)
        output = QLabel(state.output_summary)
        output.setWordWrap(True)
        next_step = QLabel(state.next_step)
        next_step.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(tools)
        layout.addWidget(sections)
        layout.addWidget(output)
        layout.addWidget(next_step)
        return frame


    def _import_quality_dashboard() -> QFrame:
        state = literature_import_quality_dashboard_state()
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        title = QLabel(f"{state.title} · {state.status_label}")
        title.setStyleSheet("font-weight: 700;")
        layout.addWidget(title)
        description = QLabel(state.description)
        description.setWordWrap(True)
        layout.addWidget(description)
        if not state.batches:
            empty = QLabel(state.empty_state)
            empty.setWordWrap(True)
            layout.addWidget(empty)
            return frame
        for batch in state.batches:
            detail = QLabel(
                "\n".join(
                    [
                        f"Batch: {batch.batch_id}",
                        f"Source: {batch.source_database} / {batch.source_format} / {batch.status}",
                        f"Created: {batch.created_at}",
                        f"Counts: raw={batch.raw_record_count}, parsed={batch.parsed_record_count}, normalized={batch.normalized_record_count}, failed={batch.failed_record_count}, warnings={batch.warning_count}",
                        f"Linked literature records: {batch.linked_literature_record_count}",
                        f"Duplicate candidates: {batch.duplicate_candidate_count}",
                        f"Diagnostics: {batch.diagnostics_path or 'not generated'}",
                        f"Summary: {batch.diagnostics_summary or 'no diagnostics warnings'}",
                    ]
                )
            )
            detail.setWordWrap(True)
            layout.addWidget(detail)
        return frame

else:

    class MetaAnalysisWorkspaceWidget:  # type: ignore[no-redef]
        pass
