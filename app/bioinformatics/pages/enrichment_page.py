from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.bioinformatics.services.enrichment_service import EnrichmentPreflightResult, EnrichmentService
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
        description="读取差异表达分析预检并检查富集分析前置条件。本阶段不下载数据库、不运行 GO / KEGG / GSEA。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtCore import Signal
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    Signal = None
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


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
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("运行富集分析预检")
            run_button.setObjectName("runEnrichmentPreflightButton")
            run_button.setProperty("buttonRole", "primary_action")
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
            next_button = QPushButton("下一步：相关性分析")
            next_button.setObjectName("enrichmentNextDisabledButton")
            next_button.setEnabled(False)
            next_button.setToolTip("disabled：相关性分析和正式 GSEA 执行不属于当前 Bio C1b 接线范围。")
            root.addWidget(next_button)
            root.addStretch(1)

        def refresh_project(self, summary: object | None) -> None:
            self._project_id = _project_id_from_summary(summary, fallback=self._project_id)
            self._project_label.setText(f"项目：{self._project_id}")

        def run_preflight_from_path(self, path: str | Path) -> EnrichmentPreflightResult:
            self._path_input.setText(str(path))
            return self._create_preflight()

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择差异表达分析预检", "", "Differential expression preflight (*.json)")
            if path:
                self._path_input.setText(path)

        def _create_preflight(self) -> EnrichmentPreflightResult:
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
