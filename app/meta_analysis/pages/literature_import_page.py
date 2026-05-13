from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.services.literature_batch_import_service import (
    LiteratureBatchImportRequest,
    LiteratureBatchImportService,
    LiteratureBatchImportSummary,
)
from app.meta_analysis.services.literature_import_service import ImportResult, LiteratureImportService
from app.meta_analysis.services.multisource_literature_import_service import (
    MULTISOURCE_SUPPORTED_FORMATS,
    MultiSourceLiteratureImportResult,
    MultiSourceLiteratureImportService,
)
from app.meta_analysis.pages.warning_severity import WarningSeverityItem, classify_warning_severity, warning_severity_counts
from app.meta_analysis.ui_text import (
    DEDUP_MODE_ZH,
    DEVELOPER_INFO_TITLE_ZH,
    DIAGNOSTICS_FIELD_ZH,
    DIAGNOSTICS_WARNING_MESSAGE_ZH,
    IMPORT_SOURCE_OPTION_ZH,
    IMPORT_WIZARD_DESCRIPTION_ZH,
    IMPORT_WIZARD_STEP_ZH,
    IMPORT_WIZARD_TITLE_ZH,
    INTERNAL_BETA_STATUS_ZH,
)
from app.shared.feature_availability import get_feature
from app.ui_style_tokens import meta_card_stylesheet, meta_error_text_style, meta_text_style, meta_title_style
from app.version import APP_VERSION


_RESULT_CARD_STYLE = meta_card_stylesheet(muted=True)
_RESULT_TEXT_STYLE = meta_text_style(size=12)
_RESULT_TITLE_STYLE = meta_title_style(size=12)

WIZARD_STEPS = (
    "source_selection",
    "file_selection",
    "import_preview",
    "import_diagnostics",
    "duplicate_review_handoff",
)


@dataclass(frozen=True)
class ImportDiagnosticsCard:
    key: str
    label: str
    value: int
    label_zh: str = ""


@dataclass(frozen=True)
class ImportDiagnosticsWarningRow:
    key: str
    label: str
    count: int
    message: str
    severity: str = "info"
    label_zh: str = ""
    message_zh: str = ""


@dataclass(frozen=True)
class ImportDiagnosticsVisualSummary:
    diagnostics_path: str
    warnings_csv_path: str
    missing_diagnostics: bool
    total_warning_count: int
    summary_cards: tuple[ImportDiagnosticsCard, ...]
    warning_rows: tuple[ImportDiagnosticsWarningRow, ...]
    failed_record_examples: tuple[str, ...]
    warning_examples: tuple[str, ...]
    warning_severity_counts: dict[str, int] | None = None


@dataclass(frozen=True)
class LiteratureImportPageState:
    title: str
    description: str
    supported_formats: tuple[str, ...]
    status_label: str
    input_summary: str
    output_summary: str
    next_step: str
    empty_state: str
    warning_summary: str
    last_result: ImportResult | None = None
    diagnostics_summary: dict[str, object] | None = None
    diagnostics_cards: tuple[ImportDiagnosticsCard, ...] = ()
    warning_table: tuple[ImportDiagnosticsWarningRow, ...] = ()
    missing_diagnostics: bool = False
    total_warning_count: int = 0
    warning_list: tuple[str, ...] = ()
    failed_records_preview: tuple[str, ...] = ()
    diagnostics_export_path: str = ""
    warnings_export_path: str = ""
    recent_import_batches: tuple[dict[str, object], ...] = ()
    import_format_options: tuple[str, ...] = ("auto", "ris", "nbib", "csv", "pubmed_xml", "medline", "endnote_export", "zotero_export", "wos_plain_text", "wos_tab_delimited", "cnki_export", "embase_ris", "cochrane_ris")
    dedup_mode_options: tuple[str, ...] = ("detect_only", "manual_review", "skip")
    source_database: str = ""
    search_date: str = ""
    search_strategy: str = ""
    dedup_mode: str = "detect_only"
    last_batch_summary: LiteratureBatchImportSummary | None = None
    panel_help: tuple[str, ...] = ()
    testing_limitations: tuple[str, ...] = ()
    warning_severity_counts: dict[str, int] | None = None
    title_zh: str = "文献导入"
    status_label_zh: str = "内部测试"
    description_zh: str = "导入本地 RIS / NBIB / CSV 文献文件，并查看导入诊断。"
    input_summary_zh: str = "输入：本地文献导出文件、来源数据库、检索日期、检索式和去重模式。"
    output_summary_zh: str = "输出：文献记录、导入批次摘要、诊断文件和 warnings CSV。"
    next_step_zh: str = "下一步：进入去重审核。"
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


@dataclass(frozen=True)
class LiteratureImportUIPanelState:
    title: str
    status_label: str
    sections: tuple[str, ...]
    primary_action: str
    next_action: str
    diagnostics_fields: tuple[str, ...]
    recent_batch_fields: tuple[str, ...]
    empty_state: str
    testing_limitations: tuple[str, ...]
    title_zh: str = "文献导入面板"
    primary_action_zh: str = "导入所选 RIS / NBIB / CSV 文件"
    next_action_zh: str = "进入去重审核"


@dataclass(frozen=True)
class LiteratureImportWizardFilePreview:
    source_path: str
    file_name: str
    requested_format: str
    detected_format: str
    exists: bool
    supported: bool
    record_count_preview: int | None
    status: str
    message: str


@dataclass(frozen=True)
class LiteratureImportWizardState:
    title: str
    status_label: str
    description: str
    steps: tuple[str, ...]
    current_step: str
    source_options: tuple[str, ...]
    format_options: tuple[str, ...]
    dedup_mode_options: tuple[str, ...]
    file_picker_first: bool
    drag_drop_supported: bool
    multi_file_ready: bool
    input_summary: str
    output_summary: str
    next_step: str
    empty_state: str
    previews: tuple[LiteratureImportWizardFilePreview, ...] = ()
    summaries: tuple[LiteratureBatchImportSummary, ...] = ()
    diagnostics_cards: tuple[ImportDiagnosticsCard, ...] = ()
    warning_table: tuple[ImportDiagnosticsWarningRow, ...] = ()
    diagnostics_export_paths: tuple[str, ...] = ()
    warnings_export_paths: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    error_message: str = ""
    testing_limitations: tuple[str, ...] = ()
    title_zh: str = IMPORT_WIZARD_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = IMPORT_WIZARD_DESCRIPTION_ZH
    current_step_zh: str = ""
    step_labels_zh: tuple[str, ...] = ()
    source_option_labels_zh: tuple[str, ...] = ()
    dedup_mode_labels_zh: tuple[str, ...] = ()
    input_summary_zh: str = "输入：通过文件选择器选择本地 RIS / NBIB / CSV 文献导出文件。"
    output_summary_zh: str = "输出：导入批次、诊断摘要、warnings CSV 和去重审核入口。"
    next_step_zh: str = "导入成功后进入去重审核。"
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


@dataclass(frozen=True)
class LiteratureImportWizardExecutionResult:
    success: bool
    state: LiteratureImportWizardState
    summaries: tuple[LiteratureBatchImportSummary, ...]
    message: str


def initial_literature_import_state() -> LiteratureImportPageState:
    feature = get_feature("meta-literature-import")
    return LiteratureImportPageState(
        title="文献导入",
        description="支持 NBIB / RIS / CSV / PubMed XML / WOS / EndNote / Zotero / CNKI / Embase / Cochrane 文件导入，用于后续去重和筛选。",
        supported_formats=("NBIB", "RIS", "CSV", "PubMed XML", "MEDLINE", "EndNote", "Zotero", "WOS", "CNKI", "Embase RIS", "Cochrane RIS"),
        status_label=feature.status.display_label() if feature is not None else "测试中",
        input_summary="输入：本地 NBIB / RIS / CSV 文献文件路径。",
        output_summary="输出：literature_records 数据资产和 literature_import task。",
        next_step="下一步：Prepare Screening / 去重准备。",
        empty_state="未选择文件时不会运行导入，请先选择本地文献文件。",
        warning_summary="错误会显示为用户可读 message；详细解析错误保留在 details。",
        panel_help=(
            "当前面板显示本地多来源文献导入后的解析质量和 diagnostics 路径。",
            "输入来自用户选择的文献导出文件；输出写入 literature_records、import diagnostics 和 warnings CSV。",
            "warning 表示需要测试人员复核的字段质量问题，不会自动修复原始文件。",
            "下一步建议：检查 failed records 和 major/blocker warning 后进入 Duplicate Review。",
        ),
        testing_limitations=(
            "Developer Preview / testing：不是 production 导入向导。",
            "Diagnostics 是质量检查，不替代人工判断。",
        ),
        status_label_zh="内部测试",
    )


def initial_literature_import_wizard_state() -> LiteratureImportWizardState:
    feature = get_feature("meta-literature-import")
    return LiteratureImportWizardState(
        title="Literature Import Wizard",
        status_label=feature.status.display_label() if feature is not None else "测试中",
        description="Testing / Developer Preview 级文献导入向导：选择来源、选择文件、预览格式、执行导入、查看 diagnostics，然后进入 Duplicate Review。",
        steps=WIZARD_STEPS,
        current_step="source_selection",
        source_options=("local_database_export", "zotero_export", "endnote_export", "pubmed_download", "csv_or_txt"),
        format_options=("auto", *MULTISOURCE_SUPPORTED_FORMATS),
        dedup_mode_options=("detect_only", "manual_review", "skip"),
        file_picker_first=True,
        drag_drop_supported=True,
        multi_file_ready=True,
        input_summary="输入：通过文件选择器选择本地 NBIB / RIS / CSV / XML / WOS / CNKI 等文献导出文件，可多文件。",
        output_summary="输出：ImportBatch summary、diagnostics JSON、warnings CSV 和 Review duplicates 下一步提示。",
        next_step="导入成功后进入 Duplicate Review / Review duplicates。",
        empty_state="尚未选择文件。请使用文件选择器添加 NBIB / RIS / CSV / XML / WOS / CNKI 等文件。",
        testing_limitations=(
            "Developer Preview：该向导包装现有 parser 和 diagnostics，不是 production 导入系统。",
            "多文件导入按路径排序逐个执行；不会自动合并、删除或修复原始文件。",
            "拖拽是 page-state 支持能力，当前 PySide 页面仍以文件选择器为主。",
        ),
        title_zh=IMPORT_WIZARD_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=IMPORT_WIZARD_DESCRIPTION_ZH,
        current_step_zh=IMPORT_WIZARD_STEP_ZH["source_selection"],
        step_labels_zh=tuple(IMPORT_WIZARD_STEP_ZH[key] for key in WIZARD_STEPS),
        source_option_labels_zh=tuple(IMPORT_SOURCE_OPTION_ZH[key] for key in ("local_database_export", "zotero_export", "endnote_export", "pubmed_download", "csv_or_txt")),
        dedup_mode_labels_zh=tuple(DEDUP_MODE_ZH[key] for key in ("detect_only", "manual_review", "skip")),
    )


def literature_import_ui_panel_state() -> LiteratureImportUIPanelState:
    base = initial_literature_import_state()
    return LiteratureImportUIPanelState(
        title="Literature Import UI Panel",
        status_label=base.status_label,
        sections=(
            "file_picker",
            "import_metadata",
            "import_result_summary",
            "diagnostics_summary_cards",
            "warning_table",
            "failed_records_preview",
            "recent_import_batches",
            "next_step",
        ),
        primary_action="Import selected RIS / NBIB / CSV file",
        next_action="Review duplicates",
        diagnostics_fields=tuple(key for key, _label in _DIAGNOSTICS_CARD_FIELDS),
        recent_batch_fields=(
            "batch_id",
            "source_database",
            "source_format",
            "raw_record_count",
            "parsed_record_count",
            "normalized_record_count",
            "failed_record_count",
            "warning_count",
            "duplicate_candidate_count",
            "diagnostics_path",
        ),
        empty_state=base.empty_state,
        testing_limitations=base.testing_limitations,
        title_zh="文献导入面板",
    )


def preview_literature_import_files(
    source_paths: list[str] | tuple[str, ...],
    *,
    import_format: str = "auto",
) -> LiteratureImportWizardState:
    base = initial_literature_import_wizard_state()
    previews = tuple(_preview_file(path, requested_format=import_format) for path in _sorted_paths(source_paths))
    warnings = tuple(preview.message for preview in previews if not preview.supported or not preview.exists)
    current_step = "import_preview" if previews and not warnings else "file_selection"
    return _wizard_state(base, current_step=current_step, previews=previews, warnings=warnings, error_message="; ".join(warnings))


def execute_literature_import_wizard(
    *,
    project_id: str,
    source_paths: list[str] | tuple[str, ...],
    import_format: str = "auto",
    source_database: str = "",
    search_date: str = "",
    search_strategy: str = "",
    dedup_mode: str = "detect_only",
    service: LiteratureBatchImportService | None = None,
) -> LiteratureImportWizardExecutionResult:
    service = service or LiteratureBatchImportService()
    preview_state = preview_literature_import_files(source_paths, import_format=import_format)
    if not source_paths:
        state = LiteratureImportWizardState(
            **_wizard_state_dict(
                preview_state,
                current_step="file_selection",
                warnings=("no_files_selected",),
                error_message="请选择至少一个 RIS、NBIB 或 CSV 文件。",
            )
        )
        return LiteratureImportWizardExecutionResult(success=False, state=state, summaries=(), message=state.error_message)
    if preview_state.warnings:
        return LiteratureImportWizardExecutionResult(
            success=False,
            state=preview_state,
            summaries=(),
            message=preview_state.error_message or "导入预览存在不支持或缺失文件。",
        )

    summaries: list[LiteratureBatchImportSummary] = []
    for preview in preview_state.previews:
        summary = service.execute_import(
            LiteratureBatchImportRequest(
                project_id=project_id,
                source_path=preview.source_path,
                import_format=import_format,
                source_database=source_database,
                search_date=search_date,
                search_strategy=search_strategy,
                dedup_mode=dedup_mode,
            )
        )
        summaries.append(summary)
        if not summary.success:
            break
    diagnostics_cards: list[ImportDiagnosticsCard] = []
    warning_rows: list[ImportDiagnosticsWarningRow] = []
    diagnostics_paths: list[str] = []
    warnings_paths: list[str] = []
    for summary in summaries:
        if summary.diagnostics_path:
            visual = import_diagnostics_visual_summary(summary.diagnostics_path, warnings_path=summary.warnings_path)
            diagnostics_cards.extend(visual.summary_cards)
            warning_rows.extend(visual.warning_rows)
            diagnostics_paths.append(summary.diagnostics_path)
            warnings_paths.append(summary.warnings_path)
    success = bool(summaries) and all(summary.success for summary in summaries)
    failed = [summary for summary in summaries if not summary.success]
    state = LiteratureImportWizardState(
        **_wizard_state_dict(
            preview_state,
            current_step="duplicate_review_handoff" if success else "import_diagnostics",
            summaries=tuple(summaries),
            diagnostics_cards=tuple(diagnostics_cards),
            warning_table=tuple(warning_rows),
            diagnostics_export_paths=tuple(diagnostics_paths),
            warnings_export_paths=tuple(warnings_paths),
            warnings=tuple(summary.message for summary in failed),
            error_message=failed[0].error_message if failed else "",
            next_step="Review duplicates" if success else "Fix import error and retry.",
            next_step_zh="导入成功，请进入去重审核。" if success else "请修正导入错误后重试。",
        )
    )
    message = f"Imported {len(summaries)} file(s). Next step: Review duplicates." if success else state.error_message or "Import failed."
    return LiteratureImportWizardExecutionResult(success=success, state=state, summaries=tuple(summaries), message=message)


def execute_multisource_literature_import(
    *,
    project_dir: Path,
    source_path: str,
    source_format: str = "auto",
    source_database: str = "",
    search_date: str = "",
    search_strategy: str = "",
    service: MultiSourceLiteratureImportService | None = None,
) -> MultiSourceLiteratureImportResult:
    service = service or MultiSourceLiteratureImportService()
    return service.import_file(
        project_dir,
        source_path=Path(source_path),
        source_format=source_format,
        source_database=source_database,
        search_date=search_date,
        search_strategy=search_strategy,
    )


def literature_import_state_from_batch_summary(
    summary: LiteratureBatchImportSummary,
    *,
    recent_import_batches: list[dict[str, object]] | None = None,
) -> LiteratureImportPageState:
    base = initial_literature_import_state()
    diagnostics = _load_diagnostics_summary(summary.diagnostics_path)
    visual_summary = import_diagnostics_visual_summary(summary.diagnostics_path, warnings_path=summary.warnings_path)
    return LiteratureImportPageState(
        title=base.title,
        description="Developer Preview / testing 文献导入入口：选择文件、设置来源信息并执行 active batch import。",
        supported_formats=base.supported_formats,
        status_label=base.status_label,
        input_summary="输入：本地 RIS / NBIB / CSV 文件、source_database、search_date、search_strategy 和 dedup_mode。",
        output_summary="输出：active ImportBatch、parsed records、import diagnostics 和下一步 Duplicate Review 提示。",
        next_step="下一步：Review duplicates。",
        empty_state=base.empty_state,
        warning_summary="导入失败会显示用户可读错误；diagnostics 展示缺字段和 warning，不自动修复。",
        diagnostics_summary=diagnostics,
        diagnostics_cards=visual_summary.summary_cards,
        warning_table=visual_summary.warning_rows,
        missing_diagnostics=visual_summary.missing_diagnostics,
        total_warning_count=visual_summary.total_warning_count,
        warning_list=visual_summary.warning_examples,
        failed_records_preview=visual_summary.failed_record_examples,
        diagnostics_export_path=summary.diagnostics_path,
        warnings_export_path=summary.warnings_path,
        recent_import_batches=tuple(recent_import_batches or ()),
        source_database=summary.source_database,
        search_date=summary.search_date,
        search_strategy=summary.search_strategy,
        dedup_mode=summary.dedup_mode,
        last_batch_summary=summary,
        panel_help=base.panel_help,
        testing_limitations=base.testing_limitations,
        warning_severity_counts=visual_summary.warning_severity_counts,
        description_zh="选择文件、设置来源信息并执行文献导入；导入后请查看诊断摘要。",
    )


def literature_import_state_from_result(
    result: ImportResult,
    *,
    recent_import_batches: list[dict[str, object]] | None = None,
) -> LiteratureImportPageState:
    base = initial_literature_import_state()
    diagnostics_path = str(result.details.get("diagnostics_path", "")) if result.details else ""
    warnings_path = str(result.details.get("warnings_path", "")) if result.details else ""
    diagnostics = _load_diagnostics_summary(diagnostics_path)
    visual_summary = import_diagnostics_visual_summary(diagnostics_path, warnings_path=warnings_path)
    return LiteratureImportPageState(
        title=base.title,
        description=base.description,
        supported_formats=base.supported_formats,
        status_label=base.status_label,
        input_summary=base.input_summary,
        output_summary="输出：literature_records、import diagnostics、warnings CSV、Data Center asset 和 literature_import task。",
        next_step=base.next_step,
        empty_state=base.empty_state,
        warning_summary="显示 diagnostics summary、warning list、failed records preview；详细解析错误保留在 details。",
        last_result=result,
        diagnostics_summary=diagnostics,
        diagnostics_cards=visual_summary.summary_cards,
        warning_table=visual_summary.warning_rows,
        missing_diagnostics=visual_summary.missing_diagnostics,
        total_warning_count=visual_summary.total_warning_count,
        warning_list=visual_summary.warning_examples,
        failed_records_preview=visual_summary.failed_record_examples,
        diagnostics_export_path=diagnostics_path,
        warnings_export_path=visual_summary.warnings_csv_path,
        recent_import_batches=tuple(recent_import_batches or ()),
        panel_help=base.panel_help,
        testing_limitations=base.testing_limitations,
        warning_severity_counts=visual_summary.warning_severity_counts,
        description_zh="导入完成后显示诊断摘要、warning 列表和失败记录预览。",
    )


def import_diagnostics_visual_summary(diagnostics_path: str, *, warnings_path: str = "") -> ImportDiagnosticsVisualSummary:
    diagnostics = _load_diagnostics_summary(diagnostics_path)
    missing_diagnostics = bool(diagnostics_path and diagnostics.get("warning") == "diagnostics_file_missing")
    normalized_path = str(Path(diagnostics_path).expanduser()) if diagnostics_path else ""
    warnings_csv_path = warnings_path or _infer_warnings_csv_path(normalized_path)
    cards = tuple(
        ImportDiagnosticsCard(key=key, label=label, value=_int_value(diagnostics.get(key, 0)), label_zh=DIAGNOSTICS_FIELD_ZH.get(key, label))
        for key, label in _DIAGNOSTICS_CARD_FIELDS
    )
    warning_rows = _diagnostics_warning_rows(diagnostics)
    failed_examples = _string_tuple(diagnostics.get("failed_record_examples", ()), limit=5)
    warning_examples = _string_tuple(diagnostics.get("parse_warning_examples", ()), limit=10)
    total_warning_count = _int_value(diagnostics.get("warning_count", 0))
    if total_warning_count == 0:
        total_warning_count = sum(row.count for row in warning_rows)
    return ImportDiagnosticsVisualSummary(
        diagnostics_path=normalized_path,
        warnings_csv_path=warnings_csv_path,
        missing_diagnostics=missing_diagnostics,
        total_warning_count=total_warning_count,
        summary_cards=cards,
        warning_rows=warning_rows,
        failed_record_examples=failed_examples,
        warning_examples=warning_examples,
        warning_severity_counts=warning_severity_counts(
            [
                WarningSeverityItem(key=row.key, severity=row.severity, message=row.message)  # type: ignore[arg-type]
                for row in warning_rows
            ]
        ),
    )


def _load_diagnostics_summary(diagnostics_path: str) -> dict[str, object]:
    if not diagnostics_path:
        return {key: [] if key.endswith("examples") else 0 for key in _DIAGNOSTICS_SUMMARY_KEYS}
    path = Path(diagnostics_path).expanduser()
    if not path.exists():
        payload: dict[str, object] = {key: [] if key.endswith("examples") else 0 for key in _DIAGNOSTICS_SUMMARY_KEYS}
        payload.update({"warning": "diagnostics_file_missing", "path": str(path)})
        return payload
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {key: payload.get(key, [] if key.endswith("examples") else 0) for key in _DIAGNOSTICS_SUMMARY_KEYS}


_DIAGNOSTICS_SUMMARY_KEYS = (
    "raw_record_count",
    "parsed_record_count",
    "normalized_record_count",
    "failed_record_count",
    "warning_count",
    "missing_title_count",
    "missing_author_count",
    "missing_year_count",
    "missing_doi_count",
    "missing_pmid_count",
    "empty_abstract_count",
    "invalid_year_count",
    "invalid_doi_count",
    "duplicate_identifier_count",
    "parse_warning_examples",
    "failed_record_examples",
)

_DIAGNOSTICS_CARD_FIELDS = (
    ("missing_title_count", "Missing title"),
    ("missing_author_count", "Missing author"),
    ("missing_year_count", "Missing year"),
    ("missing_doi_count", "Missing DOI"),
    ("missing_pmid_count", "Missing PMID"),
    ("empty_abstract_count", "Empty abstract"),
    ("invalid_doi_count", "Invalid DOI"),
    ("invalid_year_count", "Invalid year"),
)

_WARNING_MESSAGES = {
    "missing_title_count": "Records without a title need review before screening.",
    "missing_author_count": "Author metadata is missing for some records.",
    "missing_year_count": "Publication year is missing for some records.",
    "missing_doi_count": "DOI is missing; import continues but matching may be weaker.",
    "missing_pmid_count": "PMID is missing; import continues but PubMed matching may be weaker.",
    "empty_abstract_count": "Abstract text is empty for some records.",
    "invalid_doi_count": "Some DOI values could not be normalized.",
    "invalid_year_count": "Some year values could not be parsed.",
    "duplicate_identifier_count": "Repeated DOI/PMID identifiers were detected in the import batch.",
    "failed_record_count": "Some records failed parsing or validation.",
}


def _diagnostics_warning_rows(diagnostics: dict[str, object]) -> tuple[ImportDiagnosticsWarningRow, ...]:
    rows: list[ImportDiagnosticsWarningRow] = []
    for key, label in (*_DIAGNOSTICS_CARD_FIELDS, ("duplicate_identifier_count", "Duplicate identifier"), ("failed_record_count", "Failed record")):
        count = _int_value(diagnostics.get(key, 0))
        if count <= 0:
            continue
        rows.append(
            ImportDiagnosticsWarningRow(
                key=key,
                label=label,
                count=count,
                message=_WARNING_MESSAGES.get(key, "Import diagnostics warning needs review."),
                severity=classify_warning_severity(context="import_diagnostics", key=key, count=count),
                label_zh=DIAGNOSTICS_FIELD_ZH.get(key, label),
                message_zh=DIAGNOSTICS_WARNING_MESSAGE_ZH.get(key, "导入诊断 warning 需要人工复核。"),
            )
        )
    return tuple(rows)


def _wizard_state(base: LiteratureImportWizardState, **overrides: object) -> LiteratureImportWizardState:
    return LiteratureImportWizardState(**_wizard_state_dict(base, **overrides))


def _wizard_state_dict(base: LiteratureImportWizardState, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {**base.__dict__, **overrides}
    current_step = str(payload.get("current_step", ""))
    payload["current_step_zh"] = IMPORT_WIZARD_STEP_ZH.get(current_step, current_step)
    if "next_step_zh" not in overrides:
        next_step = str(payload.get("next_step", ""))
        payload["next_step_zh"] = "导入成功后进入去重审核。" if "Review duplicates" in next_step else "请根据提示继续。"
    return payload


def _infer_warnings_csv_path(diagnostics_path: str) -> str:
    if not diagnostics_path:
        return ""
    if diagnostics_path.endswith("_import_diagnostics.json"):
        return diagnostics_path.replace("_import_diagnostics.json", "_import_warnings.csv")
    return str(Path(diagnostics_path).with_name("import_warnings.csv"))


def _preview_file(path_text: str, *, requested_format: str) -> LiteratureImportWizardFilePreview:
    path = Path(path_text).expanduser()
    detected = _detect_preview_format(path, requested_format)
    exists = path.exists() and path.is_file()
    supported = detected in set(MULTISOURCE_SUPPORTED_FORMATS) and exists
    record_count_preview = _preview_record_count(path, detected) if supported else None
    if not exists:
        status = "missing"
        message = "导入文件不存在，请检查路径。"
    elif detected == "unknown":
        status = "unsupported"
        message = "无法识别导入格式，请选择 NBIB、RIS、CSV、XML、WOS、CNKI 等支持格式。"
    else:
        status = "ready"
        message = "File is ready for testing import preview."
    return LiteratureImportWizardFilePreview(
        source_path=str(path.resolve()) if exists else str(path),
        file_name=path.name,
        requested_format=requested_format or "auto",
        detected_format=detected,
        exists=exists,
        supported=supported,
        record_count_preview=record_count_preview,
        status=status,
        message=message,
    )


def _detect_preview_format(path: Path, requested_format: str) -> str:
    requested = (requested_format or "auto").strip().lower()
    if requested in set(MULTISOURCE_SUPPORTED_FORMATS):
        return requested
    if requested not in {"", "auto", "auto-detect", "autodetect"}:
        return "unknown"
    suffix = path.suffix.lower()
    if suffix in {".ris", ".nbib", ".csv", ".xml", ".tsv", ".tab"}:
        return {".ris": "ris", ".nbib": "nbib", ".csv": "csv", ".xml": "pubmed_xml", ".tsv": "wos_tab_delimited", ".tab": "wos_tab_delimited"}[suffix]
    if suffix in {".txt", ".ciw"} and path.exists():
        text = path.read_text(encoding="utf-8", errors="ignore")[:2000]
        if "\nER" in text and ("\nUT " in text or "\nTI " in text):
            return "wos_plain_text"
        if "题名" in text or "作者" in text or "来源" in text:
            return "cnki_export"
        if "PMID-" in text or "TI  -" in text or "AB  -" in text:
            return "medline"
        return "unknown"
    return "unknown"


def _preview_record_count(path: Path, detected_format: str) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0
    if detected_format == "ris":
        return len([line for line in text.splitlines() if line.startswith("TY  -")]) or (1 if text.strip() else 0)
    if detected_format == "nbib":
        return len([line for line in text.splitlines() if line.startswith("PMID-")]) or (1 if text.strip() else 0)
    if detected_format == "csv":
        lines = [line for line in text.splitlines() if line.strip()]
        return max(0, len(lines) - 1)
    if detected_format == "pubmed_xml":
        return text.count("<PubmedArticle>")
    if detected_format in {"wos_plain_text", "wos_tab_delimited"}:
        if detected_format == "wos_plain_text":
            return text.count("\nER")
        return max(0, len([line for line in text.splitlines() if line.strip()]) - 1)
    if detected_format == "cnki_export":
        return max(1, len([block for block in text.split("\n\n") if block.strip()])) if text.strip() else 0
    if detected_format in {"endnote_export", "zotero_export", "embase_ris", "cochrane_ris"}:
        return len([line for line in text.splitlines() if line.startswith("TY  -")]) or (1 if text.strip() else 0)
    return 0


def _sorted_paths(source_paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(str(path) for path in source_paths if str(path).strip()))


def _int_value(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _string_tuple(value: object, *, limit: int) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(str(item) for item in value[:limit])


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class LiteratureImportPage(QWidget):
        def __init__(
            self,
            *,
            project_id: str = "manual-testing-project",
            service: LiteratureImportService | None = None,
            batch_service: LiteratureBatchImportService | None = None,
        ) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or LiteratureImportService()
            self._batch_service = batch_service or LiteratureBatchImportService()
            self._state = initial_literature_import_state()

            root = QVBoxLayout(self)
            title = QLabel(f"{self._state.title_zh} · {self._state.status_label_zh}")
            title.setStyleSheet(meta_title_style())
            root.addWidget(title)
            description = QLabel(self._state.description_zh)
            description.setWordWrap(True)
            root.addWidget(description)
            status = QLabel(f"功能状态：{self._state.status_label_zh} / {self._state.status_label}")
            status.setStyleSheet("font-weight: 700;")
            root.addWidget(status)

            row = QHBoxLayout()
            self._path_input = QLineEdit()
            self._path_input.setPlaceholderText("选择或粘贴 .nbib / .ris / .csv 文件路径")
            choose_button = QPushButton("选择文件")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            self._format_input = QLineEdit()
            self._format_input.setPlaceholderText("格式：auto / ris / nbib / csv")
            self._format_input.setText("auto")
            root.addWidget(self._format_input)

            self._source_database_input = QLineEdit()
            self._source_database_input.setPlaceholderText("source_database，例如 PubMed / Embase / Zotero / EndNote")
            root.addWidget(self._source_database_input)

            self._search_date_input = QLineEdit()
            self._search_date_input.setPlaceholderText("search_date，例如 2026-04-29")
            root.addWidget(self._search_date_input)

            self._search_strategy_input = QLineEdit()
            self._search_strategy_input.setPlaceholderText("search_strategy，记录检索式或导入说明")
            root.addWidget(self._search_strategy_input)

            self._dedup_mode_input = QLineEdit()
            self._dedup_mode_input.setPlaceholderText("dedup_mode：detect_only / manual_review / skip")
            self._dedup_mode_input.setText("detect_only")
            root.addWidget(self._dedup_mode_input)

            import_button = QPushButton("导入")
            import_button.clicked.connect(self._run_batch_import)
            root.addWidget(import_button)

            self._status_label = QLabel("导入状态：等待文件")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            self._summary_card = QFrame()
            self._summary_card.setStyleSheet(_RESULT_CARD_STYLE)
            summary_layout = QVBoxLayout(self._summary_card)
            self._summary_label = QLabel("导入结果摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            self._summary_label.setStyleSheet(_RESULT_TEXT_STYLE)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(self._summary_card)

            self._diagnostics_card = _panel_frame("导入诊断摘要 Import diagnostics")
            diagnostics_layout = self._diagnostics_card.layout()
            self._diagnostics_label = QLabel("导入后显示缺标题、缺作者、缺年份、缺 DOI / PMID、DOI/年份异常等统计。")
            self._diagnostics_label.setWordWrap(True)
            self._diagnostics_label.setStyleSheet(_RESULT_TEXT_STYLE)
            diagnostics_layout.addWidget(self._diagnostics_label)
            root.addWidget(self._diagnostics_card)

            self._warning_card = _panel_frame("问题列表 Warning table")
            warning_layout = self._warning_card.layout()
            self._warning_label = QLabel("导入后显示问题级别和需要人工复核的字段质量问题。")
            self._warning_label.setWordWrap(True)
            self._warning_label.setStyleSheet(_RESULT_TEXT_STYLE)
            warning_layout.addWidget(self._warning_label)
            root.addWidget(self._warning_card)

            self._failed_card = _panel_frame("失败记录预览 Failed records")
            failed_layout = self._failed_card.layout()
            self._failed_label = QLabel("导入后显示失败记录示例；缺少 diagnostics 时显示中文 warning，不崩溃。")
            self._failed_label.setWordWrap(True)
            self._failed_label.setStyleSheet(_RESULT_TEXT_STYLE)
            failed_layout.addWidget(self._failed_label)
            root.addWidget(self._failed_card)

            self._recent_card = _panel_frame("最近导入批次 Recent Import Batches")
            recent_layout = self._recent_card.layout()
            self._recent_label = QLabel(_recent_batches_text())
            self._recent_label.setWordWrap(True)
            self._recent_label.setStyleSheet(_RESULT_TEXT_STYLE)
            recent_layout.addWidget(self._recent_label)
            root.addWidget(self._recent_card)

            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet(meta_error_text_style())
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：进入文献去重")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择文献文件", "", "Literature files (*.nbib *.ris *.csv)")
            if path:
                self._path_input.setText(path)

        def _run_import(self) -> None:
            result = self._service.import_file(project_id=self._project_id, source_path=self._path_input.text())
            if result.success:
                self._state = literature_import_state_from_result(result)
                self._status_label.setText("导入状态：完成")
                diagnostics = self._state.diagnostics_summary or {}
                cards = "\n".join(f"- {card.label}: {card.value}" for card in self._state.diagnostics_cards) or "无"
                warning_rows = (
                    "\n".join(f"- {row.label}: {row.count} ({row.message})" for row in self._state.warning_table) or "无"
                )
                warnings = "\n".join(f"- {item}" for item in self._state.warning_list) or "无"
                failed = "\n".join(f"- {item}" for item in self._state.failed_records_preview) or "无"
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"格式：{result.source_type.upper()}\n"
                    f"总记录：{result.total_records}\n"
                    f"成功导入：{result.imported_records}\n"
                    f"warning_count：{self._state.total_warning_count or diagnostics.get('warning_count', result.details.get('warning_count', 0))}\n"
                    f"failed_record_count：{diagnostics.get('failed_record_count', 0)}\n"
                    f"Diagnostics summary cards：\n{cards}\n"
                    f"Warning table：\n{warning_rows}\n"
                    f"diagnostics：{self._state.diagnostics_export_path}\n"
                    f"warnings CSV：{self._state.warnings_export_path}\n"
                    f"warning list：\n{warnings}\n"
                    f"failed records preview：\n{failed}\n"
                    f"输出：{result.output_path}"
                )
                self._render_diagnostics_panels()
                self._error_label.setText("")
            else:
                self._status_label.setText("导入状态：失败")
                self._summary_label.setText("没有生成导入结果。")
                self._error_label.setText(result.message)

        def _run_batch_import(self) -> None:
            summary = self._batch_service.execute_import(
                LiteratureBatchImportRequest(
                    project_id=self._project_id,
                    source_path=self._path_input.text(),
                    import_format=self._format_input.text() or "auto",
                    source_database=self._source_database_input.text(),
                    search_date=self._search_date_input.text(),
                    search_strategy=self._search_strategy_input.text(),
                    dedup_mode=self._dedup_mode_input.text() or "detect_only",
                )
            )
            if summary.success:
                self._state = literature_import_state_from_batch_summary(summary)
                cards = "\n".join(f"- {card.label}: {card.value}" for card in self._state.diagnostics_cards) or "无"
                warning_rows = "\n".join(f"- {row.label}: {row.count} ({row.message})" for row in self._state.warning_table) or "无"
                self._status_label.setText("导入状态：batch import 完成")
                self._summary_label.setText(
                    f"ImportBatch：{summary.batch_id}\n"
                    f"状态：{summary.status}\n"
                    f"source_database：{summary.source_database or '未填写'}\n"
                    f"search_date：{summary.search_date or '未填写'}\n"
                    f"search_strategy：{summary.search_strategy or '未填写'}\n"
                    f"格式：{summary.import_format}\n"
                    f"dedup_mode：{summary.dedup_mode}\n"
                    f"raw / parsed / normalized：{summary.raw_record_count} / {summary.parsed_record_count} / {summary.normalized_record_count}\n"
                    f"failed / warnings：{summary.failed_record_count} / {summary.warning_count}\n"
                    f"duplicate candidates：{summary.duplicate_candidate_count}\n"
                    f"records_after_dedup：{summary.records_after_dedup_count}\n"
                    f"diagnostics：{summary.diagnostics_path}\n"
                    f"warnings CSV：{summary.warnings_path}\n"
                    f"Diagnostics summary cards：\n{cards}\n"
                    f"Warning table：\n{warning_rows}\n"
                    f"下一步：{summary.next_step}"
                )
                self._render_diagnostics_panels()
                self._error_label.setText("")
            else:
                self._status_label.setText("导入状态：失败")
                self._summary_label.setText("没有生成 ImportBatch。")
                self._error_label.setText(summary.message if not summary.error_message else f"{summary.message}\n{summary.error_message}")


        def _render_diagnostics_panels(self) -> None:
            self._diagnostics_label.setText(_diagnostics_cards_text(self._state))
            self._warning_label.setText(_warning_rows_text(self._state))
            self._failed_label.setText(_failed_preview_text(self._state))
            self._recent_label.setText(_recent_batches_text(self._state))

else:

    class LiteratureImportPage:  # type: ignore[no-redef]
        pass


def _panel_frame(title: str) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(_RESULT_CARD_STYLE)
    layout = QVBoxLayout(frame)
    label = QLabel(title)
    label.setStyleSheet(_RESULT_TITLE_STYLE)
    layout.addWidget(label)
    return frame


def _diagnostics_cards_text(state: LiteratureImportPageState) -> str:
    if state.missing_diagnostics:
        return f"Diagnostics missing: {state.diagnostics_export_path or 'not generated'}"
    lines = [f"Total warnings: {state.total_warning_count}"]
    lines.extend(f"{card.label}: {card.value}" for card in state.diagnostics_cards)
    lines.append(f"Diagnostics path: {state.diagnostics_export_path or 'not generated'}")
    lines.append(f"Warnings CSV: {state.warnings_export_path or 'not generated'}")
    return "\n".join(lines)


def _warning_rows_text(state: LiteratureImportPageState) -> str:
    if not state.warning_table:
        return "No import warning rows yet."
    lines = []
    for row in state.warning_table:
        lines.append(f"[{row.severity}] {row.label}: {row.count} - {row.message}")
    if state.warning_severity_counts:
        counts = ", ".join(f"{key}={value}" for key, value in sorted(state.warning_severity_counts.items()))
        lines.append(f"Severity counts: {counts}")
    return "\n".join(lines)


def _failed_preview_text(state: LiteratureImportPageState) -> str:
    if not state.failed_records_preview and not state.warning_list:
        return "No failed records or parse warning examples yet."
    lines = []
    if state.failed_records_preview:
        lines.append("Failed records:")
        lines.extend(f"- {item}" for item in state.failed_records_preview)
    if state.warning_list:
        lines.append("Parse warnings:")
        lines.extend(f"- {item}" for item in state.warning_list)
    return "\n".join(lines)


def _recent_batches_text(state: LiteratureImportPageState | None = None) -> str:
    batches = state.recent_import_batches if state is not None and state.recent_import_batches else ()
    if not batches:
        return "No recent import batches found. Import a RIS / NBIB / CSV file to populate this panel."
    lines = []
    for batch in batches[:5]:
        lines.append(
            " | ".join(
                [
                    f"batch={batch.get('batch_id', '')}",
                    f"source={batch.get('source_database', '')}",
                    f"format={batch.get('source_format') or batch.get('format', '')}",
                    f"raw={batch.get('raw_record_count', 0)}",
                    f"parsed={batch.get('parsed_record_count') or batch.get('parsed_count', 0)}",
                    f"normalized={batch.get('normalized_record_count', 0)}",
                    f"failed={batch.get('failed_record_count', 0)}",
                    f"warnings={batch.get('warning_count', 0)}",
                    f"duplicates={batch.get('duplicate_candidate_count', 0)}",
                ]
            )
        )
    return "\n".join(lines)
