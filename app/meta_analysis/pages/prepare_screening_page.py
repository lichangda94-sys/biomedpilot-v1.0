from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.services.prepare_screening_service import PrepareScreeningResult, PrepareScreeningService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class PrepareScreeningPageState:
    title: str
    description: str
    status_label: str
    input_summary: str
    output_summary: str
    next_step: str
    empty_state: str
    warning_summary: str
    last_result: PrepareScreeningResult | None = None


def initial_prepare_screening_state() -> PrepareScreeningPageState:
    feature = get_feature("meta-dedup-prep")
    return PrepareScreeningPageState(
        title="去重准备 / Prepare for Screening",
        description="读取 Literature Import 输出，生成标准化文献记录，用于后续 Duplicate Review 和 Screening。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
        input_summary="输入：Literature Import 生成的 literature_records JSON。",
        output_summary="输出：screening_ready_records 数据资产和 prepare_screening task。",
        next_step="下一步：Duplicate Review。",
        empty_state="没有导入结果时无法准备筛选记录，请先完成 Literature Import。",
        warning_summary="输入路径不存在或格式不符时显示用户可读错误。",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class PrepareScreeningPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: PrepareScreeningService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or PrepareScreeningService()
            self._state = initial_prepare_screening_state()

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
            self._path_input.setPlaceholderText("选择或粘贴 Literature Import 生成的 JSON 文件路径")
            choose_button = QPushButton("选择导入结果")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            prepare_button = QPushButton("准备筛选记录")
            prepare_button.clicked.connect(self._run_prepare)
            root.addWidget(prepare_button)

            self._status_label = QLabel("准备状态：等待导入结果")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("准备结果摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：Duplicate Review")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择导入结果", "", "Import output (*.json)")
            if path:
                self._path_input.setText(path)

        def _run_prepare(self) -> None:
            result = self._service.prepare(project_id=self._project_id, import_output_path=self._path_input.text())
            if result.success:
                self._status_label.setText("准备状态：完成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"总记录：{result.total_records}\n"
                    f"已准备：{result.prepared_records}\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("准备状态：失败")
                self._summary_label.setText("没有生成筛选准备结果。")
                self._error_label.setText(result.message)

else:

    class PrepareScreeningPage:  # type: ignore[no-redef]
        pass
