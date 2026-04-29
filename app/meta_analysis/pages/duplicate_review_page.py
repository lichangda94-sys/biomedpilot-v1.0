from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.models.dedup import DedupDecision, DedupResult, DuplicateGroup, MergePreview
from app.meta_analysis.services.dedup_decision_service import DedupDecisionService
from app.meta_analysis.services.duplicate_review_service import DuplicateReviewResult, DuplicateReviewService
from app.shared.feature_availability import get_feature


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
    reason: str
    confidence: float
    master_candidate_id: str
    merge_preview_available: bool
    status: str


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
    merge_preview_summary: MergePreviewSummary = MergePreviewSummary(False)
    interactive_decision_options: tuple[str, ...] = ("keep_both", "mark_not_duplicate", "exclude_duplicate", "merge")
    interaction_warning: str = "Merge 决策必须先生成 merge preview；当前不会执行批量合并。"


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
    conflicts = tuple(item.field_name for item in differences)
    group_summaries = tuple(_group_summary(group) for group in groups)
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
        merge_preview_summary=_merge_preview_summary(merge_preview),
    )


def _group_summary(group: DuplicateGroup) -> DuplicateGroupSummary:
    duplicate_type = _duplicate_type(group.match_reason or group.reason)
    record_ids = tuple(group.record_ids or [str(record.get("record_id", "")) for record in group.records if record.get("record_id")])
    return DuplicateGroupSummary(
        group_id=group.group_id,
        record_ids=record_ids,
        duplicate_type=duplicate_type,
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
    for field_name in ("title", "abstract", "authors", "creators", "journal", "doi", "pmid", "publication_type"):
        values_by_record = tuple(
            (str(record.get("record_id", "")), _stable_value(record.get(field_name)))
            for record in records
            if record.get(field_name) not in ("", None, [])
        )
        values = {value for _record_id, value in values_by_record}
        if len(values) > 1:
            differences.append(DuplicateFieldDifference(field_name=field_name, values_by_record_id=values_by_record))
    return differences


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
            title = QLabel(self._state.title)
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{self._state.status_label}"))

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
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
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
            self._error_label.setStyleSheet("color: #B42318;")
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
                f"- {item.group_id}: {item.duplicate_type}, records={', '.join(item.record_ids)}, reason={item.reason}, confidence={item.confidence}, master={item.master_candidate_id or '待确认'}, merge_preview={'yes' if item.merge_preview_available else 'no'}"
                for item in self._state.group_summaries
            ]
            field_difference_rows = [
                f"- {item.field_name}: "
                + "; ".join(f"{record_id}={value}" for record_id, value in item.values_by_record_id)
                for item in self._state.field_differences
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
