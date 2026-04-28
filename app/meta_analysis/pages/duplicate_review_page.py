from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.services.duplicate_review_service import DuplicateReviewResult, DuplicateReviewService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class DuplicateReviewPageState:
    title: str
    description: str
    status_label: str
    last_result: DuplicateReviewResult | None = None


def initial_duplicate_review_state() -> DuplicateReviewPageState:
    feature = get_feature("meta-duplicate-review")
    return DuplicateReviewPageState(
        title="Duplicate Review / 重复候选检查",
        description="读取 Prepare for Screening 输出，生成重复候选组摘要。本阶段不执行人工合并决策。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class DuplicateReviewPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: DuplicateReviewService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or DuplicateReviewService()
            self._state = initial_duplicate_review_state()

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
                self._error_label.setText("")
            else:
                self._status_label.setText("检查状态：失败")
                self._summary_label.setText("没有生成重复候选摘要。")
                self._error_label.setText(result.message)

else:

    class DuplicateReviewPage:  # type: ignore[no-redef]
        pass

