from __future__ import annotations

from dataclasses import dataclass

from app.bioinformatics.services.bio_report_service import BioReportExportResult, BioReportService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class BioReportPageState:
    title: str
    description: str
    status_label: str
    last_result: BioReportExportResult | None = None


def initial_bio_report_state() -> BioReportPageState:
    feature = get_feature("bio-reporting")
    return BioReportPageState(
        title="报告导出",
        description="导出 Bioinformatics 测试摘要，汇总已有预检 JSON。本阶段不生成正式分析报告或图表包。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class BioReportPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: BioReportService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or BioReportService()
            self._state = initial_bio_report_state()

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
            self._path_input.setPlaceholderText("选择或粘贴一个或多个 JSON 文件路径，用分号分隔")
            choose_button = QPushButton("选择来源 JSON")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("导出测试报告摘要")
            run_button.clicked.connect(self._export_report)
            root.addWidget(run_button)

            self._status_label = QLabel("报告状态：等待来源文件")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("报告摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择 Bioinformatics JSON", "", "Bioinformatics JSON (*.json)")
            if path:
                current = self._path_input.text().strip()
                self._path_input.setText(f"{current};{path}" if current else path)

        def _export_report(self) -> None:
            source_paths = [part.strip() for part in self._path_input.text().split(";") if part.strip()]
            result = self._service.export_summary_report(project_id=self._project_id, source_paths=source_paths)
            if result.success:
                self._status_label.setText("报告状态：测试摘要已导出")
                self._summary_label.setText(
                    f"来源文件：{result.source_count}\n"
                    f"正式报告：未生成\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("报告状态：失败")
                self._summary_label.setText("没有生成报告摘要。")
                self._error_label.setText(result.message)

else:

    class BioReportPage:  # type: ignore[no-redef]
        pass
