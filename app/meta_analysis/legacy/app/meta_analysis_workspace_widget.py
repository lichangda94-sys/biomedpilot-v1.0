from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.meta_analysis_dashboard_model import (
    MetaAnalysisDashboardModel,
    demo_meta_dashboard_model,
)
from app.profile_row_editor_widget import ProfileRowEditorWidget
from app.profile_readiness_panel_widget import ProfileReadinessPanelWidget
from app.project_shell_widget import ProjectShellWidget
from app.ui_style_tokens import COLORS, SPACING
from core.project_workspace import ProjectWorkspaceState
from reporting.profile_readiness import ProfileReadinessDashboard, load_project_profile_readiness


class MetaAnalysisWorkspaceWidget(ProjectShellWidget):
    def __init__(
        self,
        dashboard_model: MetaAnalysisDashboardModel | None = None,
        parent: QWidget | None = None,
    ) -> None:
        self._dashboard_model = dashboard_model or demo_meta_dashboard_model()
        super().__init__(
            project_type="meta_analysis",
            title="BioMedPilot · Meta 分析",
            accent_color=COLORS["meta"],
            home_widget_factory=self._build_home_page,
            parent=parent,
        )

    def _build_home_page(self) -> QWidget:
        model = self._dashboard_model
        self._readiness_panel = ProfileReadinessPanelWidget()
        self._row_editor = ProfileRowEditorWidget("BIOMARKER_PREVALENCE_ASSOCIATION_META")

        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACING["md"])

        root.addWidget(self._build_dashboard_toolbar(model))

        body = QHBoxLayout()
        body.setSpacing(SPACING["md"])
        root.addLayout(body, 1)

        left = QVBoxLayout()
        left.setSpacing(SPACING["md"])
        left.addWidget(self._build_project_progress_card(model))
        left.addWidget(self._build_metric_card("纳入研究", str(model.included_studies), "Included studies"))
        left.addWidget(self._build_metric_card("合并效应", model.pooled_effect_label, model.heterogeneity_label))
        left.addStretch(1)
        body.addLayout(left)

        center = QVBoxLayout()
        center.setSpacing(SPACING["md"])
        center.addWidget(self._build_forest_plot_card(model), 2)
        bottom = QHBoxLayout()
        bottom.setSpacing(SPACING["md"])
        bottom.addWidget(self._build_rob_card(model))
        bottom.addWidget(self._build_outputs_card(model))
        center.addLayout(bottom)
        body.addLayout(center, 1)

        right = QVBoxLayout()
        right.setSpacing(SPACING["md"])
        right.addWidget(self._build_prisma_card(model))
        right.addWidget(self._build_analysis_settings_card())
        right.addWidget(self._build_grade_card(model))
        body.addLayout(right)

        return page

    def _build_dashboard_toolbar(self, model: MetaAnalysisDashboardModel) -> QFrame:
        frame = QFrame()
        frame.setObjectName("heroCard")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])

        title_col = QVBoxLayout()
        title = QLabel(model.project_title)
        title.setObjectName("sectionTitle")
        subtitle = QLabel(model.project_subtitle)
        subtitle.setObjectName("mutedLabel")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        layout.addLayout(title_col, 1)

        for label in ("导入文献", "运行分析", "导出报告"):
            button = QPushButton(label)
            button.setEnabled(False)
            layout.addWidget(button)
        status = QLabel(model.last_sync_label)
        status.setObjectName("mutedLabel")
        layout.addWidget(status)
        return frame

    def _build_project_progress_card(self, model: MetaAnalysisDashboardModel) -> QFrame:
        frame = self._card("当前项目进度")
        layout = frame.layout()
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(model.progress_percent)
        progress.setTextVisible(True)
        progress.setFormat(f"{model.progress_percent}%")
        progress.setStyleSheet(
            f"QProgressBar {{ background: {COLORS['surface_muted']}; border: 1px solid {COLORS['border']}; border-radius: 8px; height: 16px; }}"
            f"QProgressBar::chunk {{ background: {COLORS['meta']}; border-radius: 7px; }}"
        )
        label = QLabel(model.progress_label)
        label.setObjectName("mutedLabel")
        label.setWordWrap(True)
        layout.addWidget(progress)
        layout.addWidget(label)
        return frame

    def _build_metric_card(self, title: str, value: str, detail: str) -> QFrame:
        frame = self._card(title)
        layout = frame.layout()
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {COLORS['meta']}; background: transparent;")
        detail_label = QLabel(detail)
        detail_label.setObjectName("mutedLabel")
        detail_label.setWordWrap(True)
        layout.addWidget(value_label)
        layout.addWidget(detail_label)
        return frame

    def _build_forest_plot_card(self, model: MetaAnalysisDashboardModel) -> QFrame:
        frame = self._card("中央森林图结果区")
        layout = frame.layout()
        header = QLabel("Primary outcome · Risk Ratio · Random effects")
        header.setObjectName("mutedLabel")
        layout.addWidget(header)

        table = QTableWidget(len(model.forest_rows) + 1, 5)
        table.setObjectName("metaForestPlotTable")
        table.setHorizontalHeaderLabels(["Study", "Effect", "95% CI", "Weight", "Plot"])
        rows = list(model.forest_rows)
        for row_index, row in enumerate(rows):
            values = [
                row.study,
                f"{row.effect:.2f}",
                f"{row.ci_low:.2f}, {row.ci_high:.2f}",
                f"{row.weight:.1f}%",
                self._forest_marker(row.effect),
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_index, column_index, item)
        pooled_index = len(rows)
        for column_index, value in enumerate(
            ["Pooled effect", "0.82", "0.71, 0.95", "100%", "────◆────"]
        ):
            item = QTableWidgetItem(value)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(pooled_index, column_index, item)
        layout.addWidget(table, 1)
        return frame

    def _build_prisma_card(self, model: MetaAnalysisDashboardModel) -> QFrame:
        frame = self._card("PRISMA 流程")
        layout = frame.layout()
        for stage in model.prisma_stages:
            row = QLabel(f"{stage.label}  {stage.count} · {stage.note}")
            row.setObjectName("mutedLabel")
            row.setWordWrap(True)
            row.setStyleSheet(f"background: {COLORS['meta_soft']}; border-radius: 8px; padding: 6px 8px; color: {COLORS['text']};")
            layout.addWidget(row)
        return frame

    def _build_analysis_settings_card(self) -> QFrame:
        frame = self._card("分析设置")
        layout = frame.layout()
        for label, values in [
            ("效应量", ["Risk Ratio", "Odds Ratio", "Mean Difference"]),
            ("模型", ["Random effects", "Fixed effect"]),
            ("亚组", ["Overall", "Age group", "Region"]),
        ]:
            layout.addWidget(QLabel(label))
            combo = QComboBox()
            combo.addItems(values)
            combo.setEnabled(False)
            layout.addWidget(combo)
        run_button = QPushButton("开始分析")
        run_button.setObjectName("metaButton")
        run_button.setEnabled(False)
        layout.addWidget(run_button)
        return frame

    def _build_grade_card(self, model: MetaAnalysisDashboardModel) -> QFrame:
        frame = self._card("GRADE 概览")
        layout = frame.layout()
        for domain in model.grade_domains:
            label = QLabel(f"{domain.label}: {domain.rating} · {domain.note}")
            label.setObjectName("mutedLabel")
            label.setWordWrap(True)
            layout.addWidget(label)
        return frame

    def _build_rob_card(self, model: MetaAnalysisDashboardModel) -> QFrame:
        frame = self._card("RoB 2.0")
        layout = frame.layout()
        grid = QGridLayout()
        grid.setSpacing(SPACING["sm"])
        for row_index, domain in enumerate(model.rob_domains):
            grid.addWidget(QLabel(domain.label), row_index, 0)
            grid.addWidget(QLabel(f"Low {domain.low}"), row_index, 1)
            grid.addWidget(QLabel(f"Some {domain.some_concerns}"), row_index, 2)
            grid.addWidget(QLabel(f"High {domain.high}"), row_index, 3)
        layout.addLayout(grid)
        return frame

    def _build_outputs_card(self, model: MetaAnalysisDashboardModel) -> QFrame:
        frame = self._card("最近输出文件")
        layout = frame.layout()
        for output in model.output_files:
            label = QLabel(f"{output.name} · {output.kind} · {output.updated_at}")
            label.setObjectName("mutedLabel")
            label.setWordWrap(True)
            layout.addWidget(label)
        return frame

    def _card(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        layout.setSpacing(SPACING["sm"])
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 700; background: transparent;")
        layout.addWidget(title_label)
        return frame

    def _forest_marker(self, effect: float) -> str:
        if effect < 0.75:
            return "──■─────"
        if effect < 0.9:
            return "────■───"
        return "─────■──"

    def set_dashboard_model(self, model: MetaAnalysisDashboardModel) -> None:
        self._dashboard_model = model

    def set_project_state(self, state: ProjectWorkspaceState | None) -> None:
        super().set_project_state(state)
        if state is None:
            self._readiness_panel.set_dashboard(ProfileReadinessDashboard())
            return
        self._readiness_panel.set_dashboard(load_project_profile_readiness(state.project_dir))

    def readiness_panel(self) -> ProfileReadinessPanelWidget:
        return self._readiness_panel

    def row_editor(self) -> ProfileRowEditorWidget:
        return self._row_editor
