from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder, PRISMAService
from app.meta_analysis.services.reporting_service import ReportExportResult, ReportingService
from app.shared.feature_availability import get_feature
from app.shared.storage import default_storage_root


@dataclass(frozen=True)
class ReportingPageState:
    title: str
    description: str
    status_label: str
    last_result: ReportExportResult | None = None
    project_dir_placeholder: str = "选择或粘贴项目目录路径"
    prisma_summary_fields: tuple[str, ...] = (
        "records_identified",
        "records_after_deduplication",
        "records_screened",
        "studies_included",
        "full_text_workflow_incomplete",
    )
    formal_report_fields: tuple[str, ...] = (
        "formal_report_path",
        "prisma_summary_path",
        "missing_artifact_warnings",
    )


def initial_reporting_state() -> ReportingPageState:
    feature = get_feature("meta-reporting")
    return ReportingPageState(
        title="Reporting / 报告导出",
        description="读取 Analysis 预检输出并保留测试版 Markdown 摘要；支持 testing PRISMA 数字摘要和正式 Markdown 报告雏形。本阶段不导出 Word/PDF 正式论文报告。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class ReportingPage(QWidget):
        def __init__(
            self,
            *,
            project_id: str = "manual-testing-project",
            service: ReportingService | None = None,
            prisma_service: PRISMAService | None = None,
            formal_report_builder: FormalMarkdownReportBuilder | None = None,
        ) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or ReportingService()
            self._prisma_service = prisma_service or PRISMAService()
            self._formal_report_builder = formal_report_builder or FormalMarkdownReportBuilder(prisma_service=self._prisma_service)
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

            self._project_dir_input = QLineEdit()
            self._project_dir_input.setPlaceholderText(self._state.project_dir_placeholder)
            self._project_dir_input.setText(str(default_storage_root() / "projects" / self._project_id))
            root.addWidget(self._project_dir_input)

            prisma_button = QPushButton("生成 PRISMA summary")
            prisma_button.clicked.connect(self._generate_prisma_summary)
            root.addWidget(prisma_button)

            formal_button = QPushButton("生成 formal Markdown report")
            formal_button.clicked.connect(self._generate_formal_report)
            root.addWidget(formal_button)

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

        def _generate_prisma_summary(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            summary = self._prisma_service.collect_prisma_numbers(project_dir)
            json_path = self._prisma_service.save_prisma_flow_summary(project_dir, summary)
            md_path = self._prisma_service.export_prisma_flow_markdown(project_dir, summary)
            self._status_label.setText("报告状态：PRISMA summary 已生成")
            self._summary_label.setText(
                f"Records identified：{summary.records_identified}\n"
                f"Records screened：{summary.records_screened}\n"
                f"Studies included：{summary.studies_included}\n"
                f"Full-text workflow incomplete：是\n"
                f"JSON：{json_path}\n"
                f"Markdown：{md_path}"
            )
            self._error_label.setText("")

        def _generate_formal_report(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            report_path = self._formal_report_builder.build_formal_markdown_report(project_dir)
            self._status_label.setText("报告状态：Formal Markdown report 已生成")
            self._summary_label.setText(f"Formal Markdown report：{report_path}")
            self._error_label.setText("")

else:

    class ReportingPage:  # type: ignore[no-redef]
        pass
