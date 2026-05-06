from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path

from app.shared.feature_availability import FeatureAvailability, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability
from app.shared.storage import default_storage_root
from app.version import APP_VERSION

from app.meta_analysis.ui_text import INTERNAL_BETA_STATUS_ZH


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
    status_label_zh: str = "内部测试"


@dataclass(frozen=True)
class MetaWorkspaceLayoutState:
    title: str
    status_label: str
    description: str
    navigation_items: tuple[MetaWorkspaceNavigationItem, ...]
    default_page_key: str
    testing_notice: str
    version_status_label: str = ""
    entry_title: str = "Meta 分析模块"
    developer_info_label: str = "开发者信息"


def meta_workspace_layout_state() -> MetaWorkspaceLayoutState:
    version_status = f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}"
    return MetaWorkspaceLayoutState(
        title="Meta 分析模块",
        status_label=version_status,
        description="用中文组织 Meta 分析主流程入口：查看当前步骤、下一步建议、需要复核的问题和内部测试限制。",
        navigation_items=(
            MetaWorkspaceNavigationItem("workflow_dashboard", "流程总控 Workflow Dashboard", "查看项目全流程状态、需要复核的问题和下一步建议。", "workflow_dashboard"),
            MetaWorkspaceNavigationItem("protocol", "研究问题 / PICO-PICOS", "记录研究问题、PICO/PICOS 和检索策略草稿。", "protocol"),
            MetaWorkspaceNavigationItem("literature_import", "文献导入 Literature Import", "导入 RIS / NBIB / CSV 并查看导入诊断。", "literature_import"),
            MetaWorkspaceNavigationItem("import_quality", "导入质量 Import Quality", "查看最近导入批次和导入质量摘要。", "import_quality"),
            MetaWorkspaceNavigationItem("literature_library", "文献库 Literature Library", "查看文献表、重复风险和流程状态标签。", "literature_library"),
            MetaWorkspaceNavigationItem("prepare_screening", "筛选准备 Prepare Screening", "生成筛选准备数据并保留旧链路兼容入口。", "prepare_screening"),
            MetaWorkspaceNavigationItem("duplicate_review", "去重审核 Duplicate Review", "查看重复候选组、合并预览和决策入口。", "duplicate_review"),
            MetaWorkspaceNavigationItem("criteria", "纳入与排除标准 Criteria", "维护纳入标准和排除标准。", "criteria"),
            MetaWorkspaceNavigationItem("screening", "标题摘要筛选 Screening", "执行 title/abstract screening。", "screening"),
            MetaWorkspaceNavigationItem("attachment", "全文 / 附件管理 Full-text", "管理附件、缺失全文和 link/copy 状态。", "attachment"),
            MetaWorkspaceNavigationItem("fulltext_eligibility", "全文筛选 Full-text Screening", "完成全文资格审查和最终纳入清单。", "fulltext_eligibility"),
            MetaWorkspaceNavigationItem("extraction", "数据提取 Data Extraction", "录入结构化提取数据、草稿和完整性检查。", "extraction"),
            MetaWorkspaceNavigationItem("extraction_schema", "提取 Schema Registry", "查看 M12 提取 schema、字段、校验规则和 testing 边界。", "extraction_schema"),
            MetaWorkspaceNavigationItem("manual_extraction", "人工提取 Effect Rows", "测试 M13 逐篇文献、study unit、effect row 和 evidence 草稿工作区。", "manual_extraction"),
            MetaWorkspaceNavigationItem("quality", "质量评价 Quality Assessment", "填写质量评价并导出 quality table。", "quality"),
            MetaWorkspaceNavigationItem("analysis", "统计分析 Meta-analysis", "构建 dataset、运行 testing meta-analysis 并查看 warnings。", "analysis"),
            MetaWorkspaceNavigationItem("reporting", "结果报告 Reporting", "生成 PRISMA、报告、导出和复现包。", "reporting"),
            MetaWorkspaceNavigationItem("ai_suggestions", "AI 建议审核队列", "查看 AI/model suggestion 必须人工 accept / reject / edit 的治理入口。", "ai_suggestions"),
            MetaWorkspaceNavigationItem("audit", "审计日志 Audit", "查看 audit log 和 review log 导出状态。", "audit"),
        ),
        default_page_key="workflow_dashboard",
        testing_notice="当前 Meta 分析模块仍为内部测试版；所有结果需要人工复核，不能作为正式临床、投稿或 production 结论。",
        version_status_label=version_status,
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
    from app.meta_analysis.pages.extraction_page import manual_extraction_effect_row_state_from_project
    from app.meta_analysis.pages.quality_page import initial_quality_state
    from app.meta_analysis.pages.analysis_page import AnalysisPage
    from app.meta_analysis.pages.reporting_page import ReportingPage
    from app.meta_analysis.pages.attachment_page import AttachmentPage
    from app.meta_analysis.pages.fulltext_eligibility_page import FullTextEligibilityPage
    from app.meta_analysis.pages.audit_log_page import AuditLogPage
    from app.meta_analysis.pages.ai_suggestions_page import AISuggestionsPage
    from app.meta_analysis.pages.protocol_page import ProtocolPage
    from app.meta_analysis.pages.workflow_dashboard_page import WorkflowDashboardPage
    from app.meta_analysis.services.extraction_schema_registry_v1_service import ExtractionSchemaRegistryV1Service

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
            "extraction_schema": _extraction_schema_registry_panel(),
            "manual_extraction": _manual_extraction_effect_row_panel(),
            "quality": _quality_page_panel(),
            "analysis": AnalysisPage(),
            "reporting": ReportingPage(),
            "ai_suggestions": AISuggestionsPage(),
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


    def _extraction_schema_registry_panel() -> QFrame:
        service = ExtractionSchemaRegistryV1Service()
        schemas = service.default_schemas()
        frame = QFrame()
        frame.setObjectName("metaExtractionSchemaRegistryPanel")
        frame.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        title = QLabel("提取 Schema Registry · M12")
        title.setStyleSheet("font-weight: 700; font-size: 16px;")
        layout.addWidget(title)
        description = QLabel(
            "按 Meta 类型展示 required fields、effect-size mapping、analysis defaults 和 quality tool recommendation。"
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        safety = QLabel("边界：Schema 只生成表单模板和校验规则，不写最终提取值，不创建 analysis-ready dataset，不推进 PRISMA。")
        safety.setWordWrap(True)
        layout.addWidget(safety)
        layout.addWidget(QLabel(f"Schema 数量：{len(schemas)}"))
        for schema in schemas:
            detail = QLabel(
                "\n".join(
                    [
                        f"{schema.display_name} / {schema.meta_type}",
                        f"Required: {', '.join(schema.required_fields)}",
                        f"Effect mapping: {schema.effect_size_mapping}",
                        f"Quality tools: {', '.join(schema.quality_tool_recommendation)}",
                    ]
                )
            )
            detail.setWordWrap(True)
            layout.addWidget(detail)
        layout.addStretch(1)
        return frame


    def _manual_extraction_effect_row_panel() -> QFrame:
        # Use a default local project path for display only; this panel is a UI testing entry and does not run analysis.
        project_dir = default_storage_root() / "projects" / "manual-meta-ui-test" / "meta_analysis"
        state = manual_extraction_effect_row_state_from_project(project_dir)
        frame = QFrame()
        frame.setObjectName("metaManualExtractionEffectRowPanel")
        frame.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        title = QLabel(f"{state.title} · M13")
        title.setStyleSheet("font-weight: 700; font-size: 16px;")
        layout.addWidget(title)
        overview = QLabel(
            "\n".join(
                [
                    f"当前 Meta 类型：{state.overview.current_meta_type}",
                    f"当前 schema：{state.overview.current_extraction_schema}",
                    f"纳入文献数：{state.overview.included_literature_count}",
                    f"study unit 数：{state.overview.study_unit_count}",
                    f"effect row 数：{state.overview.effect_row_count}",
                    f"缺失关键字段数：{state.overview.missing_required_fields_count}",
                    f"analysis candidate rows：{state.overview.analysis_candidate_row_count}",
                ]
            )
        )
        overview.setWordWrap(True)
        layout.addWidget(overview)
        layout.addWidget(QLabel("布局：顶部概览 / 左侧文献列表 / 中间 effect rows / 右侧编辑面板"))
        layout.addWidget(QLabel(f"Study unit 字段：{', '.join(state.editor.study_unit_fields)}"))
        layout.addWidget(QLabel(f"Comparison / outcome 字段：{', '.join(state.editor.comparison_outcome_fields)}"))
        layout.addWidget(QLabel(f"动态数据字段：{', '.join(state.editor.dynamic_data_fields)}"))
        layout.addWidget(QLabel(f"Source evidence 字段：{', '.join(state.editor.source_evidence_fields)}"))
        actions = QLabel(f"主操作：{' / '.join(state.primary_actions)}")
        actions.setWordWrap(True)
        layout.addWidget(actions)
        csv_actions = QLabel(f"CSV：{' / '.join(state.csv_actions)}")
        csv_actions.setWordWrap(True)
        layout.addWidget(csv_actions)
        safety = QLabel("边界：completed_by_user 不等于 analysis-ready；不运行统计，不创建 analysis-ready dataset，不推进 PRISMA。")
        safety.setWordWrap(True)
        layout.addWidget(safety)
        if state.warnings:
            warnings = QLabel("Warnings: " + "；".join(state.warnings))
            warnings.setWordWrap(True)
            layout.addWidget(warnings)
        layout.addStretch(1)
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
