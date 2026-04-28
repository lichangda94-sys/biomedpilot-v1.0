from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.models.dedup import DedupDecision, DedupResult, DuplicateGroup
from app.meta_analysis.services.dedup_decision_service import DedupDecisionService
from app.meta_analysis.services.duplicate_review_service import DuplicateReviewResult, DuplicateReviewService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class DuplicateReviewPageState:
    title: str
    description: str
    status_label: str
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


def initial_duplicate_review_state() -> DuplicateReviewPageState:
    feature = get_feature("meta-duplicate-review")
    return DuplicateReviewPageState(
        title="文献去重",
        description="读取 Prepare for Screening 输出，查看疑似重复组并保存最小人工去重决策。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


def duplicate_review_state_from_groups(
    *,
    groups: list[DuplicateGroup],
    original_record_count: int = 0,
    current_index: int = 0,
) -> DuplicateReviewPageState:
    resolved_count = len([group for group in groups if group.status == "resolved"])
    current_group = groups[current_index] if groups and 0 <= current_index < len(groups) else None
    return DuplicateReviewPageState(
        title="文献去重",
        description="读取 Prepare for Screening 输出，查看疑似重复组并保存最小人工去重决策。",
        status_label="测试中",
        original_record_count=original_record_count,
        duplicate_group_count=len(groups),
        resolved_group_count=resolved_count,
        current_group=current_group,
    )


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
                ("合并记录", "merge"),
                ("不是重复", "mark_not_duplicate"),
                ("跳过", "skip"),
            ):
                button = QPushButton(label)
                button.clicked.connect(lambda _checked=False, value=decision: self._save_decision(value))
                decision_row.addWidget(button)
            root.addLayout(decision_row)
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
                self._current_group_index = 0
                self._render_groups()
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
                saved = self._dedup_service.save_decision(
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

        def _render_groups(self) -> None:
            if not self._groups:
                self._group_label.setText("未发现重复候选组。")
                return
            group = self._groups[self._current_group_index]
            lines = [
                f"当前重复组：{group.group_id}",
                f"匹配原因：{group.match_reason}",
                f"置信度：{group.confidence}",
                f"状态：{group.status}",
            ]
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
