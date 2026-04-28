from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app_meta.core.project_state import MetaProjectState
from app_meta.ui.components import (
    AnalysisSettingsWidget,
    ForestPlotWidget,
    GradeSummaryWidget,
    MetricCard,
    PrismaFlowWidget,
    RecentOutputsWidget,
    RiskOfBiasTableWidget,
    SectionCard,
)


class DashboardPage(QWidget):
    def __init__(self, project_state: MetaProjectState, on_action) -> None:
        super().__init__()
        self._project_state = project_state
        self._on_action = on_action
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        root.addLayout(self._header())
        root.addLayout(self._metrics())

        main = QHBoxLayout()
        main.setSpacing(16)
        root.addLayout(main, 1)
        main.addLayout(self._left_column(), 1)
        main.addLayout(self._right_column())

    def _header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        title = QLabel("Meta 分析项目总览")
        title.setObjectName("pageTitle")
        subtitle = QLabel(f"{self._project_state.project_name} · 主要结局：{self._project_state.current_outcome}")
        subtitle.setObjectName("muted")
        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _metrics(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        metrics = self._metric_cards()
        for index, metric in enumerate(metrics):
            grid.addWidget(
                MetricCard(metric.title, metric.value, metric.detail, metric.icon),
                0,
                index,
            )
        return grid

    def _left_column(self) -> QVBoxLayout:
        column = QVBoxLayout()
        column.setSpacing(16)
        column.addWidget(self._forest_plot_card(), 3)

        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        bottom.addWidget(self._risk_of_bias_card(), 2)
        bottom.addWidget(RecentOutputsWidget(self._project_state.recent_outputs, on_action=self._on_action), 1)
        column.addLayout(bottom, 1)
        return column

    def _right_column(self) -> QVBoxLayout:
        column = QVBoxLayout()
        column.setSpacing(16)
        column.addWidget(PrismaFlowWidget(self._project_state.prisma_flow, on_action=self._on_action))
        column.addWidget(AnalysisSettingsWidget(self._project_state.analysis_settings, on_action=self._on_action))
        column.addWidget(GradeSummaryWidget(self._project_state.grade), 1)
        return column

    def _forest_plot_card(self) -> SectionCard:
        studies, summary = self._project_state.forest_plot
        card = SectionCard()
        header = QHBoxLayout()
        copy = QVBoxLayout()
        title = QLabel(f"主要结局：{self._project_state.current_outcome}")
        title.setObjectName("sectionTitle")
        subtitle = QLabel(f"{summary.model_label} · {self._project_state.current_effect_size}")
        subtitle.setObjectName("smallMuted")
        copy.addWidget(title)
        copy.addWidget(subtitle)
        header.addLayout(copy, 1)

        for options in ((summary.model_label, "随机效应模型"), (summary.outcome_type, "连续性结局")):
            combo = QComboBox()
            combo.addItems(list(options))
            combo.setFixedWidth(210 if "固定" in options[0] else 130)
            header.addWidget(combo)

        for label in ("⛶", "导出", "⋯"):
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, name=label: self._on_action(name))
            header.addWidget(button)

        card.layout.addLayout(header)
        card.layout.addWidget(ForestPlotWidget(studies, summary), 1)
        return card

    def _risk_of_bias_card(self) -> SectionCard:
        card = SectionCard("风险偏倚（RoB 2.0）概览")
        card.layout.addWidget(RiskOfBiasTableWidget(self._project_state.risk_of_bias), 1)
        button = QPushButton("查看全部")
        button.clicked.connect(lambda: self._on_action("查看全部风险偏倚"))
        card.layout.addWidget(button)
        return card

    def _metric_cards(self) -> tuple[object, ...]:
        metric_state = self._project_state.metrics
        return (
            _MetricCardData(
                "检索文献数",
                metric_state.retrieved_literature_count,
                metric_state.retrieved_literature_trend,
                "literature_import",
            ),
            _MetricCardData(
                "纳入研究数",
                metric_state.included_studies_count,
                metric_state.included_studies_trend,
                "screening",
            ),
            _MetricCardData("当前结局", self._project_state.current_outcome, metric_state.current_outcome_subtitle, "pico"),
            _MetricCardData("异质性 I²", metric_state.heterogeneity_i2, metric_state.heterogeneity_subtitle, "forest_plot"),
        )


class _MetricCardData:
    def __init__(self, title: str, value: str, detail: str, icon: str) -> None:
        self.title = title
        self.value = value
        self.detail = detail
        self.icon = icon
