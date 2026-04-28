from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.services.reporting_service import ReportExportResult, ReportingService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class ReportingPageState:
    title: str
    description: str
    status_label: str
    last_result: ReportExportResult | None = None


def initial_reporting_state() -> ReportingPageState:
    feature = get_feature("meta-reporting")
    return ReportingPageState(
        title="Reporting / 报告导出",
        description="读取 Analysis 预检输出并生成测试版 Markdown 摘要。本阶段不导出正式论文报告、森林图或图表包。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class ReportingPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: ReportingService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or ReportingService()
            self._state = initial_reporting_state()

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
            self._path_input.setPlaceholderText("选择或粘贴 Analysis 预检 JSON 文件路径")
            choose_button = QPushButton("选择 Analysis 预检")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("导出测试报告摘要")
            run_button.clicked.connect(self._export_report)
            root.addWidget(run_button)

            self._status_label = QLabel("报告状态：等待 Analysis 预检输出")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("报告导出摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择 Analysis 预检", "", "Analysis preflight (*.json)")
            if path:
                self._path_input.setText(path)

        def _export_report(self) -> None:
            result = self._service.export_preflight_report(project_id=self._project_id, analysis_preflight_path=self._path_input.text())
            if result.success:
                self._status_label.setText("报告状态：摘要已导出")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"报告类型：{result.report_type}\n"
                    f"输出：{result.report_path}\n"
                    f"正式报告：否"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("报告状态：导出失败")
                self._summary_label.setText("没有生成报告摘要。")
                self._error_label.setText(result.message)

else:

    class ReportingPage:  # type: ignore[no-redef]
        pass
