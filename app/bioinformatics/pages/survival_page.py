from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.bioinformatics.services.survival_service import SurvivalPreflightResult, SurvivalService
from app.shared.feature_availability import get_feature
from app.ui_style_tokens import SPACING, bioinformatics_project_home_stylesheet


@dataclass(frozen=True)
class SurvivalPageState:
    title: str
    description: str
    status_label: str
    last_result: SurvivalPreflightResult | None = None


def initial_survival_state() -> SurvivalPageState:
    feature = get_feature("bio-survival")
    return SurvivalPageState(
        title="生存分析",
        description="读取数据清洗计划并检查临床/生存字段。本阶段不计算 Kaplan-Meier、log-rank 或 Cox 模型。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtCore import Signal
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    Signal = None
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class SurvivalPage(QWidget):
        back_requested = Signal()

        def __init__(
            self,
            *,
            project_id: str = "manual-testing-project",
            service: SurvivalService | None = None,
            on_back: Callable[[], None] | None = None,
        ) -> None:
            super().__init__()
            self.setObjectName("bioinformaticsSurvivalPage")
            self.setStyleSheet(bioinformatics_project_home_stylesheet())
            self._project_id = project_id
            self._service = service or SurvivalService()
            self._state = initial_survival_state()
            if on_back is not None:
                self.back_requested.connect(on_back)

            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            root.setSpacing(SPACING["md"])
            back_button = QPushButton("返回分析任务中心")
            back_button.setObjectName("survivalBackButton")
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
            self._project_label.setObjectName("survivalProjectLabel")
            root.addWidget(self._project_label)
            status_chip = QLabel(f"功能状态：{self._state.status_label}")
            status_chip.setObjectName("survivalFeatureStatus")
            root.addWidget(status_chip)

            row = QHBoxLayout()
            self._path_input = QLineEdit()
            self._path_input.setObjectName("survivalPreflightPathInput")
            self._path_input.setPlaceholderText("选择或粘贴数据清洗计划 JSON 文件路径")
            choose_button = QPushButton("选择清洗计划")
            choose_button.setObjectName("chooseSurvivalCleaningPlanButton")
            choose_button.setProperty("buttonRole", "secondary")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("运行生存分析预检")
            run_button.setObjectName("runSurvivalPreflightButton")
            run_button.setProperty("buttonRole", "primary_action")
            run_button.clicked.connect(self._create_preflight)
            root.addWidget(run_button)

            self._status_label = QLabel("生存分析状态：等待数据清洗计划")
            self._status_label.setObjectName("survivalRunStatus")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setObjectName("bioProjectCard")
            summary_card.setMinimumHeight(144)
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            summary_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
            self._summary_label = QLabel("生存分析预检摘要会显示在这里。")
            self._summary_label.setObjectName("survivalSummary")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setObjectName("survivalError")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：报告导出")
            next_button.setObjectName("survivalReportExportDisabledButton")
            next_button.setEnabled(False)
            next_button.setToolTip("disabled：KM/Cox/log-rank、risk score 和 clinical report-ready 不属于当前 Bio C1b 接线范围。")
            root.addWidget(next_button)
            root.addStretch(1)

        def refresh_project(self, summary: object | None) -> None:
            self._project_id = _project_id_from_summary(summary, fallback=self._project_id)
            self._project_label.setText(f"项目：{self._project_id}")

        def run_preflight_from_path(self, path: str | Path) -> SurvivalPreflightResult:
            self._path_input.setText(str(path))
            return self._create_preflight()

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择数据清洗计划", "", "Cleaning plan (*.json)")
            if path:
                self._path_input.setText(path)

        def _create_preflight(self) -> SurvivalPreflightResult:
            result = self._service.create_preflight(project_id=self._project_id, cleaning_plan_path=self._path_input.text())
            if result.success:
                self._status_label.setText("生存分析状态：预检已生成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"数据集：{result.dataset_count}\n"
                    f"具备前置条件：{result.ready_for_survival_count}\n"
                    f"生存分析：未执行\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("生存分析状态：失败")
                self._summary_label.setText("没有生成生存分析预检。")
                self._error_label.setText(result.message)
            return result

else:

    class SurvivalPage:  # type: ignore[no-redef]
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
