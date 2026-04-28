from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.services.screening_service import ScreeningQueueResult, ScreeningService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class ScreeningPageState:
    title: str
    description: str
    status_label: str
    last_result: ScreeningQueueResult | None = None


def initial_screening_state() -> ScreeningPageState:
    feature = get_feature("meta-screening")
    return ScreeningPageState(
        title="Screening / 标题摘要筛选",
        description="读取 Prepare for Screening 或 Duplicate Review 输出，生成待人工判读的标题摘要筛选队列。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class ScreeningPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: ScreeningService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or ScreeningService()
            self._state = initial_screening_state()

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
            self._path_input.setPlaceholderText("选择或粘贴 Prepare / Duplicate Review 输出 JSON 文件路径")
            choose_button = QPushButton("选择筛选来源")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("生成标题摘要筛选队列")
            run_button.clicked.connect(self._create_queue)
            root.addWidget(run_button)

            decision_card = QFrame()
            decision_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            decision_layout = QVBoxLayout(decision_card)
            decision_title = QLabel("最小人工判读")
            decision_title.setStyleSheet("font-weight: 700;")
            decision_layout.addWidget(decision_title)
            self._record_id_input = QLineEdit()
            self._record_id_input.setPlaceholderText("screening_record_id，例如 screen-xxxx")
            self._decision_input = QLineEdit()
            self._decision_input.setPlaceholderText("decision: included / excluded / maybe / pending")
            self._reason_input = QLineEdit()
            self._reason_input.setPlaceholderText("excluded 时填写排除原因")
            self._notes_input = QLineEdit()
            self._notes_input.setPlaceholderText("可选 notes")
            decision_layout.addWidget(self._record_id_input)
            decision_layout.addWidget(self._decision_input)
            decision_layout.addWidget(self._reason_input)
            decision_layout.addWidget(self._notes_input)
            save_decision_button = QPushButton("保存筛选决策")
            save_decision_button.clicked.connect(self._save_decision)
            decision_layout.addWidget(save_decision_button)
            root.addWidget(decision_card)

            self._status_label = QLabel("筛选状态：等待筛选来源")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("筛选队列摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：Extraction")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择筛选来源", "", "Screening source (*.json)")
            if path:
                self._path_input.setText(path)

        def _create_queue(self) -> None:
            result = self._service.create_queue(project_id=self._project_id, source_path=self._path_input.text())
            if result.success:
                self._status_label.setText("筛选状态：队列已生成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"总记录：{result.total_records}\n"
                    f"待筛选：{result.queued_records}\n"
                    f"Pending：{result.decision_counts.get('pending', 0)}\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("筛选状态：失败")
                self._summary_label.setText("没有生成筛选队列。")
                self._error_label.setText(result.message)

        def _save_decision(self) -> None:
            result = self._service.update_decision(
                project_id=self._project_id,
                queue_path=self._path_input.text(),
                screening_record_id=self._record_id_input.text(),
                decision=self._decision_input.text(),
                exclusion_reason_text=self._reason_input.text(),
                notes=self._notes_input.text(),
            )
            if result.success:
                self._status_label.setText("筛选状态：决策已保存")
                self._summary_label.setText(
                    f"队列：{result.queue_path}\n"
                    f"记录：{result.screening_record_id}\n"
                    f"决策：{result.decision}\n"
                    f"Included：{result.decision_counts.get('included', 0)}\n"
                    f"Excluded：{result.decision_counts.get('excluded', 0)}\n"
                    f"Maybe：{result.decision_counts.get('maybe', 0)}\n"
                    f"Pending：{result.decision_counts.get('pending', 0)}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("筛选状态：决策保存失败")
                self._error_label.setText(result.message)

else:

    class ScreeningPage:  # type: ignore[no-redef]
        pass
