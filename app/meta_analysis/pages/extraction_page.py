from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.services.extraction_service import ExtractionPoolResult, ExtractionService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class ExtractionPageState:
    title: str
    description: str
    status_label: str
    last_result: ExtractionPoolResult | None = None


def initial_extraction_state() -> ExtractionPageState:
    feature = get_feature("meta-extraction")
    return ExtractionPageState(
        title="Extraction / 数据提取",
        description="读取 Screening 队列并为 included 文献生成数据提取池。本阶段不开放正式人工提取表单。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class ExtractionPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: ExtractionService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or ExtractionService()
            self._state = initial_extraction_state()

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
            self._path_input.setPlaceholderText("选择或粘贴 Screening 队列 JSON 文件路径")
            choose_button = QPushButton("选择 Screening 队列")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("生成数据提取池")
            run_button.clicked.connect(self._create_pool)
            root.addWidget(run_button)

            self._status_label = QLabel("提取状态：等待 Screening 队列")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("提取池摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：Analysis")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择 Screening 队列", "", "Screening queue (*.json)")
            if path:
                self._path_input.setText(path)

        def _create_pool(self) -> None:
            result = self._service.create_pool(project_id=self._project_id, screening_queue_path=self._path_input.text())
            if result.success:
                self._status_label.setText("提取状态：提取池已生成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"筛选记录：{result.total_screening_records}\n"
                    f"Included：{result.included_records}\n"
                    f"提取记录：{result.extraction_records}\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("提取状态：失败")
                self._summary_label.setText("没有生成提取池。")
                self._error_label.setText(result.message)

else:

    class ExtractionPage:  # type: ignore[no-redef]
        pass
