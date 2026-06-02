from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.bioinformatics.deg_task_plan import DEG_PREFLIGHT_MANIFEST
from app.bioinformatics.services.enrichment_service import EnrichmentPreflightResult, EnrichmentService, FormalOraResult
from app.shared.feature_availability import get_feature
from app.ui_style_tokens import SPACING, bioinformatics_project_home_stylesheet


@dataclass(frozen=True)
class EnrichmentPageState:
    title: str
    description: str
    status_label: str
    last_result: EnrichmentPreflightResult | None = None


def initial_enrichment_state() -> EnrichmentPageState:
    feature = get_feature("bio-enrichment")
    return EnrichmentPageState(
        title="富集分析",
        description="读取差异表达分析预检并检查富集分析前置条件。正式 ORA 支持本地 DEG 表 + GMT gene set；GSEA 仍保持 release gate。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtCore import Signal
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    Signal = None
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPlainTextEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class EnrichmentPage(QWidget):
        back_requested = Signal()

        def __init__(
            self,
            *,
            project_id: str = "manual-testing-project",
            service: EnrichmentService | None = None,
            on_back: Callable[[], None] | None = None,
        ) -> None:
            super().__init__()
            self.setObjectName("bioinformaticsEnrichmentPage")
            self.setStyleSheet(bioinformatics_project_home_stylesheet())
            self._project_id = project_id
            self._project_root: Path | None = None
            self._service = service or EnrichmentService()
            self._state = initial_enrichment_state()
            if on_back is not None:
                self.back_requested.connect(on_back)

            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            root.setSpacing(SPACING["md"])
            back_button = QPushButton("返回分析任务中心")
            back_button.setObjectName("enrichmentBackButton")
            back_button.setProperty("buttonRole", "back")
            back_button.setProperty("buttonBehavior", "navigates_back_to_analysis_tasks")
            back_button.setProperty("formalActionEnabled", False)
            back_button.clicked.connect(self.back_requested.emit)
            root.addWidget(back_button)
            title = QLabel(self._state.title)
            title.setObjectName("bioProjectTitle")
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description)
            description.setObjectName("bioProjectSubtitle")
            description.setWordWrap(True)
            root.addWidget(description)
            self._project_label = QLabel(f"项目：{self._project_id}")
            self._project_label.setObjectName("enrichmentProjectLabel")
            root.addWidget(self._project_label)
            self._source_status_label = QLabel("项目 artifact：尚未检查 DEG preflight manifest。")
            self._source_status_label.setObjectName("enrichmentProjectArtifactStatus")
            self._source_status_label.setWordWrap(True)
            root.addWidget(self._source_status_label)
            status_chip = QLabel(f"功能状态：{self._state.status_label}")
            status_chip.setObjectName("enrichmentFeatureStatus")
            root.addWidget(status_chip)

            row = QHBoxLayout()
            self._path_input = QLineEdit()
            self._path_input.setObjectName("enrichmentPreflightPathInput")
            self._path_input.setPlaceholderText("选择或粘贴差异表达分析预检 JSON 文件路径")
            choose_button = QPushButton("选择差异分析预检")
            choose_button.setObjectName("chooseEnrichmentPreflightButton")
            choose_button.setProperty("buttonRole", "secondary")
            choose_button.setProperty("buttonBehavior", "selects_deg_preflight_manifest_json")
            choose_button.setProperty("formalActionEnabled", False)
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            gene_set_row = QHBoxLayout()
            self._gene_set_input = QLineEdit()
            self._gene_set_input.setObjectName("formalOraGeneSetPathInput")
            self._gene_set_input.setPlaceholderText("选择或粘贴 GMT gene set 文件路径")
            choose_gene_set_button = QPushButton("选择 GMT 基因集")
            choose_gene_set_button.setObjectName("chooseFormalOraGeneSetButton")
            choose_gene_set_button.setProperty("buttonRole", "secondary")
            choose_gene_set_button.setProperty("buttonBehavior", "selects_local_gmt_gene_set_for_formal_ora")
            choose_gene_set_button.setProperty("formalActionEnabled", False)
            choose_gene_set_button.setProperty("downloadAllowed", False)
            choose_gene_set_button.clicked.connect(self._choose_gene_set_file)
            gene_set_row.addWidget(self._gene_set_input, 1)
            gene_set_row.addWidget(choose_gene_set_button)
            root.addLayout(gene_set_row)

            run_button = QPushButton("运行富集分析预检")
            run_button.setObjectName("runEnrichmentPreflightButton")
            run_button.setProperty("buttonRole", "primary_action")
            run_button.setProperty("buttonBehavior", "calls_enrichment_service_create_preflight_artifact")
            run_button.setProperty("formalActionEnabled", False)
            run_button.clicked.connect(self._create_preflight)
            root.addWidget(run_button)

            self._status_label = QLabel("富集状态：等待差异表达分析预检")
            self._status_label.setObjectName("enrichmentRunStatus")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setObjectName("bioProjectCard")
            summary_card.setMinimumHeight(144)
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            summary_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
            self._summary_label = QLabel("富集分析预检摘要会显示在这里。")
            self._summary_label.setObjectName("enrichmentSummary")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setObjectName("enrichmentError")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)

            backend_button = QPushButton("检测 R 富集后端")
            backend_button.setObjectName("detectBioEnrichmentRBackendButton")
            backend_button.setProperty("buttonRole", "secondary")
            backend_button.setProperty("buttonBehavior", "calls_enrichment_service_detect_r_backend")
            backend_button.setProperty("formalActionEnabled", False)
            backend_button.setProperty("detectOnly", True)
            backend_button.setProperty("installAllowed", False)
            backend_button.setProperty("downloadAllowed", False)
            backend_button.setProperty("engineExecutionAllowed", False)
            backend_button.clicked.connect(self._detect_r_backend)
            root.addWidget(backend_button)

            self._backend_detection_text = QPlainTextEdit()
            self._backend_detection_text.setObjectName("bioEnrichmentRBackendDetectionText")
            self._backend_detection_text.setReadOnly(True)
            self._backend_detection_text.setMinimumHeight(118)
            self._backend_detection_text.setPlainText(
                "状态：尚未检测 R 富集后端。\n"
                "必需包：ReactomePA、msigdbr；可选 GSEA 包：fgsea、clusterProfiler。\n"
                "策略：R backend detect-only，不安装、不下载数据库；本地 GMT ORA 由 Python adapter 执行。"
            )
            root.addWidget(self._backend_detection_text)

            run_ora_button = QPushButton("运行正式 ORA（本地 GMT）")
            run_ora_button.setObjectName("runFormalOraButton")
            run_ora_button.setProperty("buttonRole", "primary_action")
            run_ora_button.setProperty("buttonBehavior", "calls_enrichment_service_run_formal_ora_with_local_gmt")
            run_ora_button.setProperty("formalActionEnabled", True)
            run_ora_button.setProperty("engineExecutionAllowed", True)
            run_ora_button.setProperty("downloadAllowed", False)
            run_ora_button.setProperty("databaseDownloadAllowed", False)
            run_ora_button.clicked.connect(self._run_formal_ora)
            root.addWidget(run_ora_button)

            self._formal_ora_review_text = QPlainTextEdit()
            self._formal_ora_review_text.setObjectName("formalOraResultReviewText")
            self._formal_ora_review_text.setReadOnly(True)
            self._formal_ora_review_text.setMinimumHeight(132)
            self._formal_ora_review_text.setPlainText(
                "正式 ORA 结果审阅：等待 DEG preflight 和 GMT gene set。\n"
                "执行策略：本地 hypergeometric ORA，写入 JSON/CSV artifact；GSEA/report-ready gate 不自动打开。"
            )
            root.addWidget(self._formal_ora_review_text)

            confirm_button = QPushButton("确认 ORA/GSEA 参数")
            confirm_button.setObjectName("confirmOraGseaParametersDisabledButton")
            confirm_button.setEnabled(False)
            confirm_button.setProperty("buttonBehavior", "disabled_ora_gsea_parameter_confirmation_not_ready")
            confirm_button.setProperty("disabledReason", "formal_ora_gsea_parameter_confirmation_requires_backend_and_result_schema")
            confirm_button.setProperty("formalActionEnabled", False)
            confirm_button.setToolTip("disabled：需要通过 R 后端检测、输入 schema、基因集资源和结果 schema gate 后才能确认正式 ORA/GSEA 参数。")
            root.addWidget(confirm_button)

            run_formal_button = QPushButton("运行正式 ORA/GSEA")
            run_formal_button.setObjectName("runFormalOraGseaDisabledButton")
            run_formal_button.setEnabled(False)
            run_formal_button.setProperty("buttonBehavior", "disabled_formal_ora_gsea_executor_not_connected")
            run_formal_button.setProperty("disabledReason", "formal_ora_gsea_executor_not_connected")
            run_formal_button.setProperty("formalActionEnabled", False)
            run_formal_button.setToolTip("disabled：当前只生成 ORA/GSEA preflight artifact，正式 ORA/GSEA executor 尚未纳入 release gate。")
            root.addWidget(run_formal_button)

            review_button = QPushButton("审阅 ORA/GSEA 结果")
            review_button.setObjectName("reviewOraGseaResultsDisabledButton")
            review_button.setEnabled(False)
            review_button.setProperty("buttonBehavior", "disabled_ora_gsea_result_review_without_result_index")
            review_button.setProperty("disabledReason", "ora_gsea_result_index_not_available")
            review_button.setProperty("formalActionEnabled", False)
            review_button.setToolTip("disabled：没有 ORA/GSEA result index 或 manifest，不能进入结果审阅。")
            root.addWidget(review_button)

            plot_report_button = QPushButton("生成富集图表 / report-ready")
            plot_report_button.setObjectName("oraGseaPlotReportDisabledButton")
            plot_report_button.setEnabled(False)
            plot_report_button.setProperty("buttonBehavior", "disabled_ora_gsea_plot_report_gate_not_enabled")
            plot_report_button.setProperty("disabledReason", "ora_gsea_plot_and_report_ready_gate_not_enabled")
            plot_report_button.setProperty("formalActionEnabled", False)
            plot_report_button.setToolTip("disabled：正式 ORA/GSEA plot、report-ready package 和导出 gate 尚未接入。")
            root.addWidget(plot_report_button)

            next_button = QPushButton("下一步：相关性分析")
            next_button.setObjectName("enrichmentNextDisabledButton")
            next_button.setEnabled(False)
            next_button.setProperty("buttonBehavior", "disabled_correlation_and_formal_gsea_not_connected")
            next_button.setProperty("disabledReason", "formal_ora_gsea_execution_and_correlation_gate_not_enabled")
            next_button.setProperty("formalActionEnabled", False)
            next_button.setToolTip("disabled：相关性分析和正式 GSEA 执行不属于当前 Bio C1b 接线范围。")
            root.addWidget(next_button)
            root.addStretch(1)

        def refresh_project(self, summary: object | None) -> None:
            self._project_id = _project_id_from_summary(summary, fallback=self._project_id)
            self._project_root = _project_root_from_summary(summary)
            self._project_label.setText(f"项目：{self._project_id}")
            self._auto_select_project_artifact()

        def run_preflight_from_path(self, path: str | Path) -> EnrichmentPreflightResult:
            self._path_input.setText(str(path))
            return self._create_preflight()

        def run_formal_ora_from_paths(self, differential_expression_path: str | Path, gene_set_path: str | Path) -> FormalOraResult:
            self._path_input.setText(str(differential_expression_path))
            self._gene_set_input.setText(str(gene_set_path))
            return self._run_formal_ora()

        def selected_preflight_path(self) -> str:
            return self._path_input.text()

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择差异表达分析预检", "", "Differential expression preflight (*.json)")
            if path:
                self._path_input.setText(path)

        def _choose_gene_set_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择 GMT 基因集", "", "Gene set matrix transposed (*.gmt)")
            if path:
                self._gene_set_input.setText(path)

        def _create_preflight(self) -> EnrichmentPreflightResult:
            if not self._path_input.text().strip():
                self._auto_select_project_artifact()
            result = self._service.create_preflight(project_id=self._project_id, differential_expression_path=self._path_input.text())
            if result.success:
                self._status_label.setText("富集状态：预检已生成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"数据集：{result.dataset_count}\n"
                    f"具备前置条件：{result.ready_for_enrichment_count}\n"
                    f"富集分析：未执行\n"
                    f"数据库下载：未执行\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("富集状态：失败")
                self._summary_label.setText("没有生成富集分析预检。")
                self._error_label.setText(result.message)
            return result

        def _run_formal_ora(self) -> FormalOraResult:
            if not self._path_input.text().strip():
                self._auto_select_project_artifact()
            result = self._service.run_formal_ora(
                project_id=self._project_id,
                differential_expression_path=self._path_input.text(),
                gene_set_path=self._gene_set_input.text(),
            )
            if result.success:
                top_terms = "\n".join(
                    f"- {row.get('term')} | overlap={row.get('overlap_count')} | padj={float(row.get('adjusted_p_value', 1.0)):.4g}"
                    for row in result.top_terms[:5]
                ) or "- no_terms"
                self._status_label.setText("富集状态：正式 ORA 已完成")
                self._error_label.setText("")
                self._formal_ora_review_text.setPlainText(
                    f"result_id={result.result_id}\n"
                    f"significant_genes={result.significant_gene_count}\n"
                    f"universe_genes={result.universe_gene_count}\n"
                    f"terms_tested={result.term_count}\n"
                    f"formal_ora_executed=True\n"
                    f"formal_gsea_executed=False\n"
                    f"network_used=False\n"
                    f"database_download_executed=False\n"
                    f"json={result.output_path}\n"
                    f"csv={result.csv_path}\n"
                    f"result_index={result.result_index_path or 'not_inferred'}\n"
                    f"top_terms:\n{top_terms}"
                )
            else:
                self._status_label.setText("富集状态：正式 ORA 失败")
                self._error_label.setText(result.message)
                self._formal_ora_review_text.setPlainText(
                    f"formal_ora_executed=False\n"
                    f"formal_gsea_executed=False\n"
                    f"message={result.message}\n"
                    f"details={result.details}"
                )
            return result

        def _detect_r_backend(self) -> None:
            detection = self._service.detect_r_backend()
            lines = [
                f"status={detection.status}",
                f"rscript={detection.rscript}",
                "install_action=none_detect_first_only",
                "database_download=none_detect_first_only",
                "formal_ora_python_adapter=enabled_with_local_gmt",
                "formal_ora_gsea_execution=disabled",
                detection.message,
            ]
            for package_name in ("ReactomePA", "msigdbr", "fgsea", "clusterProfiler"):
                row = detection.packages.get(package_name, {})
                lines.append(
                    f"{package_name}: available={row.get('available')} "
                    f"version={row.get('version') or '-'} "
                    f"disabled_reason={row.get('missing_reason') or 'none'}"
                )
            for key, available in detection.capabilities.items():
                lines.append(f"{key}={available}")
            if detection.blockers:
                lines.append("blockers=" + ", ".join(str(item.get("code") or "unknown") for item in detection.blockers))
            else:
                lines.append("blockers=none")
            self._backend_detection_text.setPlainText("\n".join(lines))

        def _auto_select_project_artifact(self) -> None:
            if self._project_root is None:
                self._source_status_label.setText("项目 artifact：没有当前项目，无法自动定位 DEG preflight manifest。")
                return
            candidate = self._project_root / DEG_PREFLIGHT_MANIFEST
            if candidate.is_file():
                self._path_input.setText(str(candidate))
                self._source_status_label.setText(f"项目 artifact：已自动选择 DEG preflight manifest：{candidate}")
            else:
                self._source_status_label.setText(
                    "项目 artifact：未找到 analysis/deg/preflight/deg_preflight_manifest.json；"
                    "请先在 DEG 配置页生成 preflight，或手动选择 JSON。"
                )

else:

    class EnrichmentPage:  # type: ignore[no-redef]
        pass


def _project_id_from_summary(summary: object | None, *, fallback: str) -> str:
    if summary is None:
        return fallback
    project_root = getattr(summary, "project_root", None)
    if project_root is not None:
        return Path(project_root).name
    try:
        return Path(str(summary)).expanduser().name or fallback
    except Exception:
        return fallback


def _project_root_from_summary(summary: object | None) -> Path | None:
    if summary is None:
        return None
    project_root = getattr(summary, "project_root", None)
    if project_root is not None:
        return Path(project_root).expanduser().resolve()
    try:
        path = Path(str(summary)).expanduser().resolve()
    except Exception:
        return None
    return path if path.exists() else None
