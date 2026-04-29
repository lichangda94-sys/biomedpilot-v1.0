from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.models.prisma import PRISMAFlowSummary
from app.meta_analysis.pages.warning_severity import WarningSeverityItem, classify_warning_severity, warning_severity_counts
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder, PRISMAService
from app.meta_analysis.services.publication_export_service import PublicationExportService
from app.meta_analysis.services.reporting_service import ReportExportResult, ReportingService
from app.shared.feature_availability import get_feature
from app.shared.storage import default_storage_root


@dataclass(frozen=True)
class ReportingPageState:
    title: str
    description: str
    status_label: str
    input_summary: str
    output_summary: str
    next_step: str
    empty_state: str
    warning_summary: str
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
    publication_export_fields: tuple[str, ...] = (
        "html_report_path",
        "word_report_path",
        "supplementary_exports_path",
        "figure_package_path",
        "project_snapshot_path",
        "reproducibility_package_path",
        "artifact_lock_warnings",
        "pdf_placeholder_status",
    )
    prisma_trace_state: "PRISMATraceState | None" = None
    panel_help: tuple[str, ...] = ()
    testing_limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class PRISMATraceReferenceRow:
    source_type: str
    path: str
    status: str


@dataclass(frozen=True)
class PRISMATraceState:
    summary: PRISMAFlowSummary | None
    source_references: tuple[PRISMATraceReferenceRow, ...]
    source_reference_warnings: tuple[str, ...]
    audit_reference_warnings: tuple[str, ...]
    workflow_event_counts: dict[str, int]
    review_log_jsonl_path: str
    review_log_csv_path: str
    message: str
    warning_severity_items: tuple[WarningSeverityItem, ...] = ()
    warning_severity_counts: dict[str, int] | None = None


def initial_reporting_state() -> ReportingPageState:
    feature = get_feature("meta-reporting")
    return ReportingPageState(
        title="Reporting / 报告导出",
        description="读取 Analysis 预检输出并保留测试版 Markdown 摘要；支持 testing PRISMA 数字摘要、formal Markdown/HTML/DOCX 报告雏形、supplementary exports、figure package、project snapshot 和复现包。PDF 正式报告仍未开放。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
        input_summary="输入：analysis_preflight 或本地项目目录中的 PRISMA / extraction / analysis / figure artifacts。",
        output_summary="输出：test summary、formal Markdown/HTML/DOCX testing report、supplementary exports、figure package、snapshot 和 reproducibility package。",
        next_step="下一步：内部 beta 前审查缺失 artifact、PDF 策略和投稿模板差距。",
        empty_state="缺失 artifact 时报告写明 missing / not generated，不崩溃。",
        warning_summary="Reporting 区分 test summary、formal Markdown、HTML/DOCX testing report；PDF 正式报告仍未开放。",
        panel_help=(
            "当前面板显示 test summary、PRISMA source trace、formal Markdown/HTML/DOCX testing report 和导出路径。",
            "输入来自项目目录中的 import、dedup、screening、full-text、extraction、analysis、figure artifacts。",
            "输出写入 reports、exports、figures、snapshots 和 reproducibility package。",
            "warning 表示 source reference、audit reference 或 artifact 缺失，报告会继续生成并标记 missing。",
            "下一步建议：先补齐 blocker/major source warning，再把报告交给测试人员阅读。",
        ),
        testing_limitations=(
            "Developer Preview / testing：不生成正式 PRISMA diagram。",
            "正式 PDF report 未开放；当前仅保留 Markdown/HTML/DOCX testing 输出。",
        ),
    )


def reporting_prisma_trace_state_from_project(
    project_dir: Path,
    *,
    prisma_service: PRISMAService | None = None,
    audit_log: MetaAuditLogService | None = None,
) -> PRISMATraceState:
    project_dir = project_dir.expanduser().resolve()
    prisma_service = prisma_service or PRISMAService(audit_log=audit_log)
    audit_log = audit_log or MetaAuditLogService()
    summary = prisma_service.collect_prisma_numbers(project_dir)
    rows = tuple(
        PRISMATraceReferenceRow(
            source_type=str(item.get("source_type", "")),
            path=str(item.get("path", "")),
            status=str(item.get("status", "")),
        )
        for item in summary.source_references
    )
    source_warnings = tuple(
        f"Missing source reference: {row.source_type}"
        for row in rows
        if row.status == "missing"
    )
    events = audit_log.list_events(project_dir)
    event_type_counts: dict[str, int] = {}
    for event in events:
        event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
    workflow_counts = _workflow_event_counts(event_type_counts)
    audit_warnings = tuple(
        f"Missing audit events for {name}"
        for name, count in workflow_counts.items()
        if count == 0
    )
    severity_items = [
        WarningSeverityItem(
            key="missing_source_reference",
            severity=classify_warning_severity(context="prisma_trace", key="missing_source_reference"),
            message=warning,
        )
        for warning in source_warnings
    ]
    severity_items.extend(
        WarningSeverityItem(
            key="missing_audit_events",
            severity=classify_warning_severity(context="prisma_trace", key="missing_audit_events"),
            message=warning,
        )
        for warning in audit_warnings
    )
    return PRISMATraceState(
        summary=summary,
        source_references=rows,
        source_reference_warnings=source_warnings,
        audit_reference_warnings=audit_warnings,
        workflow_event_counts=workflow_counts,
        review_log_jsonl_path=str(project_dir / "reports" / "review_log.jsonl"),
        review_log_csv_path=str(project_dir / "reports" / "review_log.csv"),
        message="PRISMA source trace collected. Missing source or audit references are warnings in Developer Preview.",
        warning_severity_items=tuple(severity_items),
        warning_severity_counts=warning_severity_counts(tuple(severity_items)),
    )


def _workflow_event_counts(event_type_counts: dict[str, int]) -> dict[str, int]:
    groups = {
        "import": ("import_batch_created", "record_parsed", "field_sanitized", "record_normalized", "record_saved", "diagnostics_generated"),
        "dedup": ("duplicate_detected", "duplicate_decision"),
        "screening": ("screening_decision",),
        "fulltext": ("fulltext_status_changed",),
        "extraction": ("extraction_updated",),
        "analysis": ("analysis_run_completed",),
        "report": ("report_exported",),
    }
    return {name: sum(event_type_counts.get(event_type, 0) for event_type in event_types) for name, event_types in groups.items()}


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
            publication_export_service: PublicationExportService | None = None,
        ) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or ReportingService()
            self._prisma_service = prisma_service or PRISMAService()
            self._formal_report_builder = formal_report_builder or FormalMarkdownReportBuilder(prisma_service=self._prisma_service)
            self._publication_export_service = publication_export_service or PublicationExportService(
                formal_report_builder=self._formal_report_builder
            )
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

            html_button = QPushButton("导出 HTML testing report")
            html_button.clicked.connect(self._export_html_report)
            root.addWidget(html_button)

            word_button = QPushButton("导出 Word testing report")
            word_button.clicked.connect(self._export_word_report)
            root.addWidget(word_button)

            supplementary_button = QPushButton("导出 supplementary tables")
            supplementary_button.clicked.connect(self._export_supplementary_exports)
            root.addWidget(supplementary_button)

            figure_package_button = QPushButton("导出 figure package")
            figure_package_button.clicked.connect(self._export_figure_package)
            root.addWidget(figure_package_button)

            snapshot_button = QPushButton("创建 project snapshot")
            snapshot_button.clicked.connect(self._create_project_snapshot)
            root.addWidget(snapshot_button)

            reproducibility_button = QPushButton("导出 reproducibility package")
            reproducibility_button.clicked.connect(self._export_reproducibility_package)
            root.addWidget(reproducibility_button)

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
            trace = reporting_prisma_trace_state_from_project(project_dir, prisma_service=self._prisma_service)
            source_refs = "\n".join(f"- {row.source_type}: {row.status} {row.path}" for row in trace.source_references) or "无"
            source_warnings = "\n".join(f"- {item}" for item in trace.source_reference_warnings) or "无"
            audit_warnings = "\n".join(f"- {item}" for item in trace.audit_reference_warnings) or "无"
            event_counts = "\n".join(f"- {key}: {value}" for key, value in sorted(trace.workflow_event_counts.items())) or "无"
            self._status_label.setText("报告状态：PRISMA summary 已生成")
            self._summary_label.setText(
                f"Records identified：{summary.records_identified}\n"
                f"Records after deduplication：{summary.records_after_deduplication}\n"
                f"Duplicates removed：{summary.duplicates_removed}\n"
                f"Records screened：{summary.records_screened}\n"
                f"Studies included：{summary.studies_included}\n"
                f"Full-text workflow incomplete：是\n"
                f"Source references：\n{source_refs}\n"
                f"Source reference warnings：\n{source_warnings}\n"
                f"Audit reference warnings：\n{audit_warnings}\n"
                f"Workflow event counts：\n{event_counts}\n"
                f"review_log.jsonl：{trace.review_log_jsonl_path}\n"
                f"review_log.csv：{trace.review_log_csv_path}\n"
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

        def _export_html_report(self) -> None:
            result = self._publication_export_service.export_html_report(Path(self._project_dir_input.text()).expanduser())
            self._status_label.setText("报告状态：HTML testing report 已导出")
            self._summary_label.setText(_publication_result_text("HTML report", result.output_path, result.warnings))
            self._error_label.setText("")

        def _export_word_report(self) -> None:
            result = self._publication_export_service.export_word_report(Path(self._project_dir_input.text()).expanduser())
            self._status_label.setText("报告状态：Word testing report 已导出")
            self._summary_label.setText(_publication_result_text("Word report", result.output_path, result.warnings))
            self._error_label.setText("")

        def _export_supplementary_exports(self) -> None:
            result = self._publication_export_service.export_supplementary_exports(Path(self._project_dir_input.text()).expanduser())
            self._status_label.setText("报告状态：Supplementary tables 已导出")
            self._summary_label.setText(f"Supplementary exports：{result.output_path}")
            self._error_label.setText("")

        def _export_figure_package(self) -> None:
            result = self._publication_export_service.export_figure_package(Path(self._project_dir_input.text()).expanduser())
            self._status_label.setText("报告状态：Figure package 已导出")
            self._summary_label.setText(_publication_result_text("Figure package", result.output_path, result.warnings))
            self._error_label.setText("")

        def _create_project_snapshot(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            snapshot = self._publication_export_service.create_project_snapshot(project_dir)
            snapshot_path = self._publication_export_service.save_project_snapshot(project_dir, snapshot)
            self._status_label.setText("报告状态：Project snapshot 已创建")
            self._summary_label.setText(f"Project snapshot：{snapshot_path}")
            self._error_label.setText("")

        def _export_reproducibility_package(self) -> None:
            result = self._publication_export_service.export_reproducibility_package(Path(self._project_dir_input.text()).expanduser())
            self._status_label.setText("报告状态：Reproducibility package 已导出")
            self._summary_label.setText(f"Reproducibility package：{result.output_path}")
            self._error_label.setText("")

else:

    class ReportingPage:  # type: ignore[no-redef]
        pass


def _publication_result_text(label: str, output_path: str, warnings: list[str]) -> str:
    warning_text = "\nWarnings：" + "\n".join(warnings) if warnings else ""
    return f"{label}：{output_path}{warning_text}"
