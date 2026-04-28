from __future__ import annotations

from dataclasses import dataclass

from app.bioinformatics.services.sample_grouping_service import SampleGroupingPlanResult, SampleGroupingService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class SampleGroupingPageState:
    title: str
    description: str
    status_label: str
    last_result: SampleGroupingPlanResult | None = None


def initial_sample_grouping_state() -> SampleGroupingPageState:
    feature = get_feature("bio-sample-groups")
    return SampleGroupingPageState(
        title="样本分组",
        description="读取数据清洗计划并生成样本分组预检。本阶段不自动推断病例/对照分组。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class SampleGroupingPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: SampleGroupingService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or SampleGroupingService()
            self._state = initial_sample_grouping_state()

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
            self._path_input.setPlaceholderText("选择或粘贴数据清洗计划 JSON 文件路径")
            choose_button = QPushButton("选择清洗计划")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("生成样本分组计划")
            run_button.clicked.connect(self._create_plan)
            root.addWidget(run_button)

            self._status_label = QLabel("分组状态：等待清洗计划")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("样本分组计划摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：差异表达分析")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择清洗计划", "", "Cleaning plan (*.json)")
            if path:
                self._path_input.setText(path)

        def _create_plan(self) -> None:
            result = self._service.create_grouping_plan(project_id=self._project_id, cleaning_plan_path=self._path_input.text())
            if result.success:
                self._status_label.setText("分组状态：计划已生成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"数据集：{result.dataset_count}\n"
                    f"可人工分组：{result.ready_for_grouping_count}\n"
                    f"自动分组：未执行\n"
                    f"差异分析：未执行\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("分组状态：失败")
                self._summary_label.setText("没有生成样本分组计划。")
                self._error_label.setText(result.message)

else:

    class SampleGroupingPage:  # type: ignore[no-redef]
        pass
