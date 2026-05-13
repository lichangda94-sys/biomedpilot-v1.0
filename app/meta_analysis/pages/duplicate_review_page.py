from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.models.dedup import DedupDecision, DedupResult, DuplicateGroup, MergePreview
from app.meta_analysis.pages.warning_severity import WarningSeverityItem, classify_warning_severity, warning_severity_counts
from app.meta_analysis.services.dedup_decision_service import DedupDecisionService
from app.meta_analysis.services.dedup_review_v2_service import (
    RISK_GRAY,
    RISK_GREEN,
    RISK_RED,
    RISK_YELLOW,
    DedupReviewV2Service,
)
from app.meta_analysis.services.duplicate_review_service import DuplicateReviewResult, DuplicateReviewService
from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
from app.meta_analysis.ui_text import (
    DEVELOPER_INFO_TITLE_ZH,
    DUPLICATE_DECISION_ZH,
    DUPLICATE_FIELD_ZH,
    DUPLICATE_GROUP_TYPE_ZH,
    DUPLICATE_REVIEW_DESCRIPTION_ZH,
    DUPLICATE_REVIEW_TITLE_ZH,
    INTERNAL_BETA_STATUS_ZH,
)
from app.shared.feature_availability import get_feature
from app.ui_style_tokens import meta_card_stylesheet, meta_error_text_style, meta_title_style
from app.version import APP_VERSION


@dataclass(frozen=True)
class DuplicateRecordSummary:
    record_id: str
    title: str
    authors_text: str
    year: str
    journal: str
    doi: str
    pmid: str


@dataclass(frozen=True)
class DuplicateFieldDifference:
    field_name: str
    values_by_record_id: tuple[tuple[str, str], ...]
    field_name_zh: str = ""


@dataclass(frozen=True)
class DuplicateFieldConflictSummary:
    field_name: str
    values_by_record_id: tuple[tuple[str, str], ...]
    selected_record_id: str
    field_name_zh: str = ""


@dataclass(frozen=True)
class MergePreviewSummary:
    available: bool
    group_id: str = ""
    merged_from_record_ids: tuple[str, ...] = ()
    field_sources: tuple[tuple[str, str], ...] = ()
    provenance_sources: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class DuplicateGroupSummary:
    group_id: str
    record_ids: tuple[str, ...]
    duplicate_type: str
    duplicate_type_zh: str
    reason: str
    confidence: float
    master_candidate_id: str
    merge_preview_available: bool
    status: str
    risk_level: str = ""
    risk_label: str = ""


@dataclass(frozen=True)
class DuplicateReviewPageState:
    title: str
    description: str
    status_label: str
    input_summary: str
    output_summary: str
    next_step: str
    empty_state: str
    warning_summary: str
    original_record_count: int = 0
    duplicate_group_count: int = 0
    resolved_group_count: int = 0
    current_group: DuplicateGroup | None = None
    current_group_fields: tuple[str, ...] = ("title", "authors", "year", "journal", "doi", "pmid")
    decision_options: tuple[str, ...] = ("keep_first", "keep_second", "merge", "mark_not_duplicate", "skip")
    decision_note: str = ""
    last_result: DuplicateReviewResult | None = None
    last_decision: DedupDecision | None = None
    last_dedup_result: DedupResult | None = None
    merge_preview: MergePreview | None = None
    canonical_candidate_id: str = ""
    match_reasons: tuple[str, ...] = ()
    field_conflicts: tuple[str, ...] = ()
    exact_duplicate_group_count: int = 0
    suspected_duplicate_group_count: int = 0
    group_summaries: tuple[DuplicateGroupSummary, ...] = ()
    duplicate_review_queue_export_path: str = ""
    current_group_records: tuple[DuplicateRecordSummary, ...] = ()
    field_differences: tuple[DuplicateFieldDifference, ...] = ()
    field_conflict_summary: tuple[DuplicateFieldConflictSummary, ...] = ()
    merge_preview_summary: MergePreviewSummary = MergePreviewSummary(False)
    interactive_decision_options: tuple[str, ...] = ("keep_both", "mark_not_duplicate", "exclude_duplicate", "merge")
    interaction_warning: str = "Merge 决策必须先生成 merge preview；当前不会执行批量合并。"
    panel_help: tuple[str, ...] = ()
    testing_limitations: tuple[str, ...] = ()
    warning_severity_items: tuple[WarningSeverityItem, ...] = ()
    warning_severity_counts: dict[str, int] | None = None
    risk_level_counts: dict[str, int] | None = None
    v2_review_queue_path: str = ""
    v2_schema_version: str = ""
    auto_delete_enabled: bool = False
    auto_merge_enabled: bool = False
    title_zh: str = DUPLICATE_REVIEW_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = DUPLICATE_REVIEW_DESCRIPTION_ZH
    input_summary_zh: str = "输入：筛选准备记录或重复候选组 JSON。"
    output_summary_zh: str = "输出：重复候选摘要、合并预览、人工去重决策和审计记录。"
    next_step_zh: str = "下一步：确认重复文献后进入纳入与排除标准。"
    empty_state_zh: str = "没有重复候选组时，可进入纳入与排除标准和标题摘要筛选。"
    warning_summary_zh: str = "字段冲突、低置信度或缺少合并预览时需要 reviewer 人工复核。"
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH
    decision_option_labels_zh: tuple[str, ...] = ()


def initial_duplicate_review_state() -> DuplicateReviewPageState:
    feature = get_feature("meta-duplicate-review")
    return DuplicateReviewPageState(
        title="文献去重",
        description="读取 Prepare for Screening 输出，查看疑似重复组并保存最小人工去重决策。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
        input_summary="输入：screening_ready_records JSON。",
        output_summary="输出：duplicate_candidate_groups、deduplicated_literature 和 dedup decision task。",
        next_step="下一步：Screening。",
        empty_state="没有重复候选组时可直接生成去重后文献库并进入 Screening。",
        warning_summary="未找到重复组、决策不合法或来源路径错误时显示用户可读错误。",
        panel_help=(
            "当前面板显示 duplicate candidate groups、match reasons、canonical candidate 和 merge preview。",
            "输入来自 Prepare Screening / Duplicate Review 生成的 duplicate_groups JSON。",
            "输出为人工 dedup decision、duplicate_review_queue.csv 和后续 deduplicated_literature。",
            "warning 表示字段冲突、低置信度或 merge preview 不完整，需要 reviewer 复核。",
            "下一步建议：先查看 merge preview，再选择 keep_both、mark_not_duplicate、exclude_duplicate 或单组合并。",
        ),
        testing_limitations=(
            "Developer Preview / testing：merge preview 是辅助，不替代 reviewer 判断。",
            "当前不执行复杂批量合并 UI，也不自动删除记录。",
        ),
        title_zh=DUPLICATE_REVIEW_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=DUPLICATE_REVIEW_DESCRIPTION_ZH,
        decision_option_labels_zh=tuple(DUPLICATE_DECISION_ZH[item] for item in ("keep_both", "mark_not_duplicate", "exclude_duplicate", "merge")),
        risk_level_counts={RISK_RED: 0, RISK_YELLOW: 0, RISK_GRAY: 0, RISK_GREEN: 0},
        v2_schema_version="meta_duplicate_review_queue.v2",
    )


def duplicate_review_v2_state_from_project(project_dir) -> DuplicateReviewPageState:
    from pathlib import Path

    project_dir = Path(project_dir).expanduser().resolve()
    service = DedupReviewV2Service()
    result = service.build_review_queue(project_dir)
    record_count = len(LiteratureLibraryService().list_records(project_dir))
    groups = result.groups
    current = groups[0] if groups else None
    summaries = tuple(
        DuplicateGroupSummary(
            group_id=group.group_id,
            record_ids=group.record_ids,
            duplicate_type="exact" if group.risk_level == RISK_RED else "suspected",
            duplicate_type_zh="高度重复" if group.risk_level == RISK_RED else "疑似重复",
            reason=group.match_reason,
            confidence=group.confidence,
            master_candidate_id=group.retain_candidate_id,
            merge_preview_available=bool(group.merge_preview),
            status=group.status,
            risk_level=group.risk_level,
            risk_label=group.risk_label,
        )
        for group in groups
    )
    return DuplicateReviewPageState(
        title="文献去重",
        description="基于统一 LiteratureLibraryService 的 Duplicate Review v2，只生成重复组、风险等级、merge preview 和人工决策入口。",
        status_label="测试中",
        input_summary="输入：literature/literature_records.json normalized records。",
        output_summary="输出：duplicate_groups_v2、merge preview、dedup_decisions_v2；不自动删除、不自动 merge。",
        next_step="人工确认 dedup decisions 后生成 deduplicated literature set。",
        empty_state="未发现重复候选组。",
        warning_summary="红/黄/灰风险均需 reviewer 复核；绿色仅表示未发现重复组。",
        original_record_count=record_count,
        duplicate_group_count=len(groups),
        current_group=None,
        current_group_records=tuple(_record_summary(record) for record in (current.records if current else ())),
        group_summaries=summaries,
        exact_duplicate_group_count=len([group for group in groups if group.risk_level == RISK_RED]),
        suspected_duplicate_group_count=len([group for group in groups if group.risk_level in {RISK_YELLOW, RISK_GRAY}]),
        risk_level_counts=dict(result.risk_level_counts),
        v2_review_queue_path=result.output_path,
        v2_schema_version="meta_duplicate_review_queue.v2",
        auto_delete_enabled=False,
        auto_merge_enabled=False,
        decision_options=("keep_both", "mark_not_duplicate", "merge", "set_master_record", "exclude_duplicate", "skip", "undo"),
        interactive_decision_options=("keep_both", "mark_not_duplicate", "merge", "set_master_record", "exclude_duplicate", "undo"),
        interaction_warning="Duplicate Review v2 不会自动删除或合并；merge 必须由 reviewer 确认。",
        panel_help=initial_duplicate_review_state().panel_help,
        testing_limitations=(
            "Duplicate Review v2 只生成风险分组和 merge preview。",
            "任何 merge / not duplicate / exclude decision 都必须人工确认并写 audit。",
        ),
        title_zh=DUPLICATE_REVIEW_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh="基于统一文献库的去重复核，显示红/黄/灰风险、字段差异和 merge preview。",
        decision_option_labels_zh=tuple(DUPLICATE_DECISION_ZH.get(item, item) for item in ("keep_both", "mark_not_duplicate", "exclude_duplicate", "merge")),
    )


def duplicate_review_state_from_groups(
    *,
    groups: list[DuplicateGroup],
    original_record_count: int = 0,
    current_index: int = 0,
    merge_preview: MergePreview | None = None,
    duplicate_review_queue_export_path: str = "",
) -> DuplicateReviewPageState:
    resolved_count = len([group for group in groups if group.status == "resolved"])
    current_group = groups[current_index] if groups and 0 <= current_index < len(groups) else None
    match_reasons = tuple(_split_match_reasons(current_group.match_reason if current_group else ""))
    differences = tuple(_field_differences(current_group.records if current_group else []))
    conflict_summary = tuple(_field_conflict_summary(differences, merge_preview))
    conflicts = tuple(_compatible_conflict_names(conflict_summary))
    group_summaries = tuple(_group_summary(group) for group in groups)
    severity_items = _merge_preview_warning_severity_items(
        field_conflict_count=len(conflict_summary),
        merge_preview=merge_preview,
        current_group=current_group,
    )
    return DuplicateReviewPageState(
        title="文献去重",
        description="读取 Prepare for Screening 输出，查看疑似重复组、match reasons 和 testing merge preview，并保存最小人工去重决策。",
        status_label="测试中",
        input_summary="输入：screening_ready_records JSON。",
        output_summary="输出：duplicate_candidate_groups、merge preview、deduplicated_literature 和 dedup decision task。",
        next_step="下一步：Screening。",
        empty_state="没有重复候选组时可直接生成去重后文献库并进入 Screening。",
        warning_summary="显示 canonical candidate、match reasons、field conflicts；未找到重复组、决策不合法或来源路径错误时显示用户可读错误。",
        original_record_count=original_record_count,
        duplicate_group_count=len(groups),
        resolved_group_count=resolved_count,
        current_group=current_group,
        current_group_fields=("title", "authors", "year", "journal", "doi", "pmid", "publication_type", "source"),
        decision_options=("keep_first", "keep_second", "merge", "keep_both", "mark_not_duplicate", "exclude_duplicate", "set_master_record", "skip"),
        merge_preview=merge_preview,
        canonical_candidate_id=_canonical_candidate_id(merge_preview, current_group),
        match_reasons=match_reasons,
        field_conflicts=conflicts,
        exact_duplicate_group_count=len([item for item in group_summaries if item.duplicate_type == "exact"]),
        suspected_duplicate_group_count=len([item for item in group_summaries if item.duplicate_type == "suspected"]),
        group_summaries=group_summaries,
        duplicate_review_queue_export_path=duplicate_review_queue_export_path,
        current_group_records=tuple(_record_summary(record) for record in (current_group.records if current_group else [])),
        field_differences=differences,
        field_conflict_summary=conflict_summary,
        merge_preview_summary=_merge_preview_summary(merge_preview),
        panel_help=initial_duplicate_review_state().panel_help,
        testing_limitations=initial_duplicate_review_state().testing_limitations,
        warning_severity_items=severity_items,
        warning_severity_counts=warning_severity_counts(severity_items),
        title_zh=DUPLICATE_REVIEW_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=DUPLICATE_REVIEW_DESCRIPTION_ZH,
        decision_option_labels_zh=tuple(DUPLICATE_DECISION_ZH.get(item, item) for item in ("keep_both", "mark_not_duplicate", "exclude_duplicate", "merge")),
    )


def _group_summary(group: DuplicateGroup) -> DuplicateGroupSummary:
    duplicate_type = _duplicate_type(group.match_reason or group.reason)
    record_ids = tuple(group.record_ids or [str(record.get("record_id", "")) for record in group.records if record.get("record_id")])
    return DuplicateGroupSummary(
        group_id=group.group_id,
        record_ids=record_ids,
        duplicate_type=duplicate_type,
        duplicate_type_zh=DUPLICATE_GROUP_TYPE_ZH.get(duplicate_type, duplicate_type),
        reason=group.match_reason or group.reason,
        confidence=group.confidence,
        master_candidate_id=_canonical_candidate_id(None, group),
        merge_preview_available=len(record_ids) >= 2 or len(group.records) >= 2,
        status=group.status,
    )


def _duplicate_type(reason: str) -> str:
    normalized = reason.lower().replace("-", "_")
    exact_tokens = ("pmid_exact", "doi_exact", "clinicaltrials_exact", "clinical_trial_exact", "clinicaltrials id", "clinical trial id")
    if any(token in normalized for token in exact_tokens):
        return "exact"
    if normalized.strip() in {"pmid", "doi", "clinicaltrials", "clinical_trial"}:
        return "exact"
    return "suspected"


def _split_match_reasons(value: str) -> list[str]:
    return [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]


def _field_differences(records: list[dict[str, object]]) -> list[DuplicateFieldDifference]:
    differences: list[DuplicateFieldDifference] = []
    for field_name, aliases in (
        ("title", ("title",)),
        ("abstract", ("abstract",)),
        ("authors", ("authors", "authors_text")),
        ("creators", ("creators",)),
        ("creators/authors", ("creators", "authors", "authors_text")),
        ("year/date", ("year", "date")),
        ("journal/publication_title", ("journal", "publication_title")),
        ("doi", ("doi",)),
        ("pmid", ("pmid",)),
        ("clinical_trials_ids", ("clinical_trials_ids",)),
    ):
        values_by_record = tuple(
            (str(record.get("record_id", "")), _stable_value(_first_present_value(record, aliases)))
            for record in records
            if _first_present_value(record, aliases) not in ("", None, [])
        )
        values = {value for _record_id, value in values_by_record}
        if len(values) > 1:
            differences.append(DuplicateFieldDifference(field_name=field_name, values_by_record_id=values_by_record, field_name_zh=DUPLICATE_FIELD_ZH.get(field_name, field_name)))
    return differences


def _field_conflict_summary(
    differences: tuple[DuplicateFieldDifference, ...],
    preview: MergePreview | None,
) -> list[DuplicateFieldConflictSummary]:
    summaries: list[DuplicateFieldConflictSummary] = []
    for item in differences:
        selected = ""
        if preview is not None:
            selected = str(preview.field_sources.get(_source_field_for_conflict(item.field_name), ""))
        summaries.append(
            DuplicateFieldConflictSummary(
                field_name=item.field_name,
                values_by_record_id=item.values_by_record_id,
                selected_record_id=selected,
                field_name_zh=DUPLICATE_FIELD_ZH.get(item.field_name, item.field_name),
            )
        )
    return summaries


def _compatible_conflict_names(conflicts: tuple[DuplicateFieldConflictSummary, ...]) -> list[str]:
    names: list[str] = []
    for item in conflicts:
        names.append(item.field_name)
        if item.field_name == "creators/authors":
            names.append("authors")
            names.append("creators")
        if item.field_name == "year/date":
            names.append("year")
            names.append("date")
        if item.field_name == "journal/publication_title":
            names.append("journal")
            names.append("publication_title")
    return list(dict.fromkeys(names))


def _merge_preview_warning_severity_items(
    *,
    field_conflict_count: int,
    merge_preview: MergePreview | None,
    current_group: DuplicateGroup | None,
) -> tuple[WarningSeverityItem, ...]:
    items: list[WarningSeverityItem] = []
    if current_group is not None and merge_preview is None:
        items.append(
            WarningSeverityItem(
                key="merge_preview_missing",
                severity=classify_warning_severity(context="merge_preview", key="merge_preview_missing"),
                message="当前重复组没有可读 merge preview。",
            )
        )
    if field_conflict_count:
        items.append(
            WarningSeverityItem(
                key="field_conflict",
                severity=classify_warning_severity(context="merge_preview", key="field_conflict", count=field_conflict_count),
                message=f"{field_conflict_count} 个关键字段存在冲突。",
            )
        )
    if current_group is not None and current_group.confidence < 0.85:
        items.append(
            WarningSeverityItem(
                key="low_confidence",
                severity=classify_warning_severity(context="merge_preview", key="low_confidence"),
                message="重复候选置信度较低，需要人工确认。",
            )
        )
    if merge_preview is not None:
        for warning in merge_preview.warnings:
            items.append(
                WarningSeverityItem(
                    key=warning,
                    severity=classify_warning_severity(context="merge_preview", key=warning),
                    message=warning,
                )
            )
    return tuple(items)


def _record_summary(record: dict[str, object]) -> DuplicateRecordSummary:
    authors = record.get("authors", "")
    authors_text = record.get("authors_text", "")
    if not authors_text:
        authors_text = ", ".join(str(item) for item in authors) if isinstance(authors, list) else str(authors)
    return DuplicateRecordSummary(
        record_id=str(record.get("record_id", "")),
        title=str(record.get("title", "")),
        authors_text=str(authors_text),
        year=str(record.get("year", "")),
        journal=str(record.get("journal", "")),
        doi=str(record.get("doi", "")),
        pmid=str(record.get("pmid", "")),
    )


def _merge_preview_summary(preview: MergePreview | None) -> MergePreviewSummary:
    if preview is None:
        return MergePreviewSummary(False)
    return MergePreviewSummary(
        available=True,
        group_id=preview.group_id,
        merged_from_record_ids=tuple(preview.merged_from_record_ids),
        field_sources=tuple(sorted((str(field), str(record_id)) for field, record_id in preview.field_sources.items())),
        provenance_sources=tuple(preview.provenance_sources),
        warnings=tuple(preview.warnings),
    )


def _stable_value(value: object) -> str:
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    return str(value)


def _first_present_value(record: dict[str, object], aliases: tuple[str, ...]) -> object:
    for alias in aliases:
        value = record.get(alias)
        if value not in ("", None, []):
            return value
    return ""


def _source_field_for_conflict(field_name: str) -> str:
    return {
        "creators/authors": "creators",
        "year/date": "year",
        "journal/publication_title": "journal",
    }.get(field_name, field_name)


def _canonical_candidate_id(preview: MergePreview | None, group: DuplicateGroup | None) -> str:
    if preview and preview.field_sources:
        return str(next(iter(preview.field_sources.values()), ""))
    if group and group.records:
        return str(group.records[0].get("record_id", ""))
    return ""


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QTextEdit = QVBoxLayout = QWidget = None


if QWidget is not None:

    class DuplicateReviewPage(QWidget):
        def __init__(
            self,
            *,
            project_id: str = "manual-testing-project",
            service: DuplicateReviewService | None = None,
            dedup_service: DedupDecisionService | None = None,
        ) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or DuplicateReviewService()
            self._dedup_service = dedup_service or DedupDecisionService()
            self._state = initial_duplicate_review_state()
            self._groups: list[DuplicateGroup] = []
            self._current_group_index = 0

            root = QVBoxLayout(self)
            title = QLabel(f"{self._state.title_zh} · {self._state.status_label_zh}")
            title.setStyleSheet(meta_title_style())
            root.addWidget(title)
            description = QLabel(self._state.description_zh)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{self._state.status_label_zh} / {self._state.status_label}"))

            row = QHBoxLayout()
            self._path_input = QLineEdit()
            self._path_input.setPlaceholderText("选择或粘贴 Prepare for Screening 生成的 JSON 文件路径")
            choose_button = QPushButton("选择筛选准备结果")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            review_button = QPushButton("生成重复候选摘要")
            review_button.clicked.connect(self._run_review)
            root.addWidget(review_button)

            load_groups_button = QPushButton("载入重复候选组")
            load_groups_button.clicked.connect(self._load_groups)
            root.addWidget(load_groups_button)

            self._status_label = QLabel("检查状态：等待筛选准备结果")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet(meta_card_stylesheet())
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("重复候选摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._group_label = QLabel("当前重复组详情会显示在这里。")
            self._group_label.setWordWrap(True)
            root.addWidget(self._group_label)
            self._note_input = QTextEdit()
            self._note_input.setPlaceholderText("决策备注")
            self._note_input.setMaximumHeight(80)
            root.addWidget(self._note_input)
            decision_row = QHBoxLayout()
            for label, decision in (
                ("保留第一条", "keep_first"),
                ("保留第二条", "keep_second"),
                ("都保留", "keep_both"),
                ("合并记录", "merge"),
                ("不是重复", "mark_not_duplicate"),
                ("排除重复", "exclude_duplicate"),
                ("跳过", "skip"),
            ):
                button = QPushButton(label)
                button.clicked.connect(lambda _checked=False, value=decision: self._save_decision(value))
                decision_row.addWidget(button)
            root.addLayout(decision_row)
            navigation_row = QHBoxLayout()
            previous_button = QPushButton("上一组")
            previous_button.clicked.connect(lambda: self._move_group(-1))
            next_group_button = QPushButton("下一组")
            next_group_button.clicked.connect(lambda: self._move_group(1))
            navigation_row.addWidget(previous_button)
            navigation_row.addWidget(next_group_button)
            root.addLayout(navigation_row)
            generate_button = QPushButton("生成去重后文献库")
            generate_button.clicked.connect(self._generate_deduplicated_literature)
            root.addWidget(generate_button)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet(meta_error_text_style())
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：Screening")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择筛选准备结果", "", "Screening-ready records (*.json)")
            if path:
                self._path_input.setText(path)

        def _run_review(self) -> None:
            result = self._service.review(project_id=self._project_id, screening_ready_path=self._path_input.text())
            if result.success:
                self._status_label.setText("检查状态：完成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"总记录：{result.total_records}\n"
                    f"重复候选组：{result.duplicate_group_count}\n"
                    f"候选记录数：{result.candidate_record_count}\n"
                    f"输出：{result.output_path}"
                )
                self._path_input.setText(result.output_path)
                self._error_label.setText("")
            else:
                self._status_label.setText("检查状态：失败")
                self._summary_label.setText("没有生成重复候选摘要。")
                self._error_label.setText(result.message)

        def _load_groups(self) -> None:
            try:
                self._groups = self._dedup_service.load_groups(duplicate_review_path=self._path_input.text())
                export_path = self._dedup_service.export_duplicate_review_queue(duplicate_review_path=self._path_input.text())
                self._current_group_index = 0
                self._render_groups(duplicate_review_queue_export_path=export_path)
                self._error_label.setText("")
            except Exception as exc:
                self._error_label.setText(str(exc))

        def _save_decision(self, decision: str) -> None:
            if not self._groups:
                self._load_groups()
            if not self._groups:
                return
            group = self._groups[self._current_group_index]
            try:
                saved = self._dedup_service.save_interactive_decision(
                    duplicate_review_path=self._path_input.text(),
                    group_id=group.group_id,
                    decision=decision,
                    note=self._note_input.toPlainText(),
                )
                self._state = DuplicateReviewPageState(
                    title=self._state.title,
                    description=self._state.description,
                    status_label=self._state.status_label,
                    last_decision=saved,
                )
                self._groups = self._dedup_service.load_groups(duplicate_review_path=self._path_input.text())
                self._render_groups()
                self._error_label.setText("")
            except Exception as exc:
                self._error_label.setText(str(exc))

        def _move_group(self, step: int) -> None:
            if not self._groups:
                self._load_groups()
            if not self._groups:
                return
            self._current_group_index = max(0, min(len(self._groups) - 1, self._current_group_index + step))
            self._render_groups(duplicate_review_queue_export_path=self._state.duplicate_review_queue_export_path)

        def _generate_deduplicated_literature(self) -> None:
            result = self._dedup_service.generate_deduplicated_literature(
                project_id=self._project_id,
                duplicate_review_path=self._path_input.text(),
            )
            if result.success:
                self._status_label.setText("检查状态：去重文献库已生成")
                self._summary_label.setText(
                    f"原始文献数：{result.original_count}\n"
                    f"疑似重复组数：{result.duplicate_group_count}\n"
                    f"已处理组数：{result.resolved_group_count}\n"
                    f"去重后文献数：{result.unique_count}\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._error_label.setText(result.message)

        def _render_groups(self, *, duplicate_review_queue_export_path: str = "") -> None:
            if not self._groups:
                self._group_label.setText("未发现重复候选组。")
                return
            group = self._groups[self._current_group_index]
            preview = None
            try:
                preview = self._dedup_service.preview_merge(duplicate_review_path=self._path_input.text(), group_id=group.group_id)
            except Exception:
                preview = None
            self._state = duplicate_review_state_from_groups(
                groups=self._groups,
                original_record_count=len({str(record.get("record_id", "")) for item in self._groups for record in item.records}),
                current_index=self._current_group_index,
                merge_preview=preview,
                duplicate_review_queue_export_path=duplicate_review_queue_export_path,
            )
            group_rows = [
                f"- {item.group_id}: {item.duplicate_type_zh} ({item.duplicate_type}), records={', '.join(item.record_ids)}, reason={item.reason}, confidence={item.confidence}, master={item.master_candidate_id or '待确认'}, merge_preview={'yes' if item.merge_preview_available else 'no'}"
                for item in self._state.group_summaries
            ]
            field_difference_rows = [
                f"- {item.field_name_zh} ({item.field_name}): "
                + "; ".join(f"{record_id}={value}" for record_id, value in item.values_by_record_id)
                for item in self._state.field_differences
            ]
            field_conflict_rows = [
                f"- {item.field_name_zh} ({item.field_name}): selected={item.selected_record_id or '未指定'}; "
                + "; ".join(f"{record_id}={value}" for record_id, value in item.values_by_record_id)
                for item in self._state.field_conflict_summary
            ]
            lines = [
                f"重复候选组总数：{self._state.duplicate_group_count}",
                f"exact duplicate groups：{self._state.exact_duplicate_group_count}",
                f"suspected duplicate groups：{self._state.suspected_duplicate_group_count}",
                f"duplicate_review_queue：{self._state.duplicate_review_queue_export_path or '未导出'}",
                "全部候选组：",
                *(group_rows or ["- 无"]),
                "",
                f"当前重复组：{group.group_id}",
                f"匹配原因：{group.match_reason}",
                f"match reasons：{', '.join(self._state.match_reasons) or '无'}",
                f"置信度：{group.confidence}",
                f"状态：{group.status}",
                f"canonical candidate：{self._state.canonical_candidate_id or '待确认'}",
                f"field conflicts：{', '.join(self._state.field_conflicts) or '无'}",
                "字段冲突摘要：",
                *(field_conflict_rows or ["- 无"]),
                "字段差异：",
                *(field_difference_rows or ["- 无"]),
            ]
            if preview is not None:
                lines.extend(
                    [
                        "",
                        "Merge preview",
                        f"merged_from：{', '.join(preview.merged_from_record_ids)}",
                        f"field_sources：{preview.field_sources}",
                        f"provenance_sources：{', '.join(preview.provenance_sources)}",
                        f"warnings：{', '.join(preview.warnings) or '无'}",
                    ]
                )
            for index, record in enumerate(group.records[:2], start=1):
                authors = record.get("authors", "")
                authors_text = ", ".join(authors) if isinstance(authors, list) else str(authors)
                lines.extend(
                    [
                        "",
                        f"文献 {index}",
                        f"title: {record.get('title', '')}",
                        f"authors: {authors_text}",
                        f"year: {record.get('year', '')}",
                        f"journal: {record.get('journal', '')}",
                        f"DOI: {record.get('doi', '')}",
                        f"PMID: {record.get('pmid', '')}",
                    ]
                )
            self._group_label.setText("\n".join(lines))

else:

    class DuplicateReviewPage:  # type: ignore[no-redef]
        pass
