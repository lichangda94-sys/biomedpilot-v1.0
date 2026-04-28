from __future__ import annotations

import math
from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app_meta.core.project_state import MetaProjectState
from app_meta.ui.components import ForestPlotWidget, SectionCard
from app_meta.ui.theme import Theme


FUNNEL_POINTS = (
    (0.52, 0.21),
    (0.57, 0.19),
    (0.45, 0.27),
    (0.58, 0.18),
    (0.57, 0.24),
    (0.70, 0.22),
    (0.93, 0.31),
    (0.49, 0.28),
    (0.62, 0.17),
    (0.76, 0.26),
)


class ForestPlotPage(QWidget):
    def __init__(self, project_state: MetaProjectState, on_action: Callable[[str], None]) -> None:
        super().__init__()
        self._project_state = project_state
        self._on_action = on_action

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        root.addLayout(self._header())
        root.addWidget(self._controls_card())

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._plot_card(), 1)
        body.addWidget(self._heterogeneity_card())
        root.addLayout(body, 1)

    def _header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        title = QLabel("Forest Plot")
        title.setObjectName("pageTitle")
        subtitle = QLabel(f"{self._project_state.project_name} · {self._project_state.current_outcome}")
        subtitle.setObjectName("muted")
        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _controls_card(self) -> SectionCard:
        studies, summary = self._project_state.forest_plot
        card = SectionCard("Analysis controls")
        row = QHBoxLayout()
        for label, values in (
            ("Outcome", (self._project_state.current_outcome, "临床治愈率", "Adverse events")),
            ("Effect size", (self._project_state.current_effect_size, "Risk Ratio", "Risk Difference")),
            ("Model", (summary.model_label, "随机效应模型（DerSimonian-Laird）")),
        ):
            row.addWidget(QLabel(label))
            combo = QComboBox()
            combo.addItems(values)
            combo.setMinimumWidth(190)
            row.addWidget(combo)
        row.addStretch(1)
        for index, label in enumerate(("Export PNG", "Export PDF placeholder")):
            button = QPushButton(label)
            if index == 0:
                button.setObjectName("primaryButton")
            button.clicked.connect(lambda checked=False, name=label: self._on_action(name))
            row.addWidget(button)
        card.layout.addLayout(row)
        return card

    def _plot_card(self) -> SectionCard:
        studies, summary = self._project_state.forest_plot
        card = SectionCard(f"主要结局：{self._project_state.current_outcome}")
        plot = ForestPlotWidget(studies, summary)
        plot.setMinimumHeight(560)
        card.layout.addWidget(plot, 1)
        return card

    def _heterogeneity_card(self) -> SectionCard:
        _studies, summary = self._project_state.forest_plot
        card = SectionCard("Heterogeneity summary")
        card.setFixedWidth(340)
        rows = (
            ("Model", summary.model_label),
            ("Outcome type", summary.outcome_type),
            ("Pooled effect", f"{summary.pooled_effect_size:.2f} [{summary.ci_low:.2f}, {summary.ci_high:.2f}]"),
            ("Heterogeneity", summary.heterogeneity_text),
            ("Overall effect", summary.overall_effect_text),
        )
        for label, value in rows:
            item = QLabel(f"{label}: {value}")
            item.setWordWrap(True)
            item.setObjectName("smallMuted")
            card.layout.addWidget(item)
        card.layout.addStretch(1)
        return card


class FunnelPlotPage(QWidget):
    def __init__(self, project_state: MetaProjectState, on_action: Callable[[str], None]) -> None:
        super().__init__()
        self._project_state = project_state
        self._on_action = on_action

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        root.addLayout(self._header())
        root.addWidget(self._controls_card())

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._plot_card(), 1)
        body.addWidget(self._bias_summary_card())
        root.addLayout(body, 1)

    def _header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        title = QLabel("Funnel Plot")
        title.setObjectName("pageTitle")
        subtitle = QLabel("发表偏倚可视化与 Egger / Begg 检验占位")
        subtitle.setObjectName("muted")
        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _controls_card(self) -> SectionCard:
        card = SectionCard("Funnel plot controls")
        row = QHBoxLayout()
        row.addWidget(QLabel("Outcome"))
        outcome = QComboBox()
        outcome.addItems((self._project_state.current_outcome, "临床治愈率", "Adverse events"))
        row.addWidget(outcome)
        row.addStretch(1)
        for index, label in enumerate(("Egger test placeholder", "Begg test placeholder", "Export PNG")):
            button = QPushButton(label)
            if index == 2:
                button.setObjectName("primaryButton")
            button.clicked.connect(lambda checked=False, name=label: self._on_action(name))
            row.addWidget(button)
        card.layout.addLayout(row)
        return card

    def _plot_card(self) -> SectionCard:
        _studies, summary = self._project_state.forest_plot
        card = SectionCard("Funnel plot · Odds Ratio")
        card.layout.addWidget(FunnelPlotWidget(FUNNEL_POINTS, summary.pooled_effect_size), 1)
        return card

    def _bias_summary_card(self) -> SectionCard:
        card = SectionCard("Publication bias summary")
        card.setFixedWidth(340)
        rows = (
            ("Egger P", "0.18"),
            ("Begg test", "Placeholder"),
            ("Interpretation", "未见明显发表偏倚"),
            ("Notes", "Demo scatter points are shown for UI validation only."),
        )
        for label, value in rows:
            item = QLabel(f"{label}: {value}")
            item.setWordWrap(True)
            item.setObjectName("smallMuted")
            card.layout.addWidget(item)
        card.layout.addStretch(1)
        return card


class FunnelPlotWidget(QWidget):
    def __init__(self, points: tuple[tuple[float, float], ...], pooled_effect: float) -> None:
        super().__init__()
        self._points = points
        self._pooled_effect = pooled_effect
        self.setMinimumHeight(560)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(28, 24, -28, -36)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))

        plot_left = rect.left() + 48
        plot_right = rect.right() - 18
        plot_top = rect.top() + 18
        plot_bottom = rect.bottom() - 32

        painter.setPen(QPen(QColor(Theme.border), 1))
        painter.drawRect(QRectF(plot_left, plot_top, plot_right - plot_left, plot_bottom - plot_top))

        pooled_x = self._x_for_effect(self._pooled_effect, plot_left, plot_right)
        painter.setPen(QPen(QColor(Theme.primary), 1.6))
        painter.drawLine(QPointF(pooled_x, plot_top), QPointF(pooled_x, plot_bottom))

        painter.setPen(QPen(QColor("#94A3B8"), 1.2, Qt.PenStyle.DashLine))
        top_point = QPointF(pooled_x, plot_top)
        painter.drawLine(top_point, QPointF(self._x_for_effect(0.28, plot_left, plot_right), plot_bottom))
        painter.drawLine(top_point, QPointF(self._x_for_effect(1.22, plot_left, plot_right), plot_bottom))

        painter.setPen(QColor(Theme.text))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(plot_left, rect.top(), "Effect size")
        painter.drawText(rect.left(), plot_top + 12, "SE")

        painter.setFont(QFont("Arial", 9))
        for label in (0.2, 0.5, 1.0, 2.0):
            x = self._x_for_effect(label, plot_left, plot_right)
            painter.setPen(QPen(QColor(Theme.border), 1))
            painter.drawLine(QPointF(x, plot_bottom), QPointF(x, plot_bottom + 5))
            painter.setPen(QColor(Theme.muted))
            painter.drawText(QRectF(x - 20, plot_bottom + 8, 40, 18), Qt.AlignCenter, str(label).rstrip("0").rstrip("."))

        for effect, se in self._points:
            x = self._x_for_effect(effect, plot_left, plot_right)
            y = self._y_for_se(se, plot_top, plot_bottom)
            painter.setBrush(QColor(Theme.primary))
            painter.setPen(QPen(QColor("#1D4ED8"), 1))
            painter.drawEllipse(QPointF(x, y), 5.5, 5.5)

        painter.setPen(QColor(Theme.muted))
        painter.drawText(
            QRectF(plot_left, plot_bottom + 28, plot_right - plot_left, 22),
            Qt.AlignCenter,
            "Smaller study effects and pseudo 95% confidence boundaries",
        )

    def _x_for_effect(self, value: float, left: int, right: int) -> float:
        min_log = math.log10(0.2)
        max_log = math.log10(2.0)
        ratio = (math.log10(value) - min_log) / (max_log - min_log)
        return left + ratio * (right - left)

    def _y_for_se(self, value: float, top: int, bottom: int) -> float:
        max_se = 0.35
        return top + (value / max_se) * (bottom - top)


class ReportingPage(QWidget):
    def __init__(self, project_state: MetaProjectState, on_action: Callable[[str], None]) -> None:
        super().__init__()
        self._project_state = project_state
        self._on_action = on_action

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        root.addLayout(self._header())

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._checklist_card())
        body.addWidget(self._preview_card(), 1)
        root.addLayout(body, 1)

    def _header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        title = QLabel("Reporting")
        title.setObjectName("pageTitle")
        subtitle = QLabel("生成结构化报告预览，并为 Markdown / HTML / Word / PDF 导出预留入口")
        subtitle.setObjectName("muted")
        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _checklist_card(self) -> SectionCard:
        card = SectionCard("Report component checklist")
        card.setFixedWidth(340)
        self.checks: list[QCheckBox] = []
        for item in (
            "Title",
            "Abstract",
            "PICO",
            "Search strategy",
            "PRISMA flow",
            "Included studies",
            "RoB",
            "GRADE",
            "Forest plot",
            "Funnel plot",
            "Discussion",
        ):
            check = QCheckBox(item)
            check.setChecked(True)
            self.checks.append(check)
            card.layout.addWidget(check)
        generate = QPushButton("Generate demo report preview")
        generate.setObjectName("primaryButton")
        generate.clicked.connect(self.generate_preview)
        card.layout.addWidget(generate)
        card.layout.addStretch(1)
        return card

    def _preview_card(self) -> SectionCard:
        card = SectionCard("Report preview")
        actions = QHBoxLayout()
        for index, label in enumerate(("Markdown", "HTML", "Word placeholder", "PDF placeholder")):
            button = QPushButton(label)
            if index == 0:
                button.setObjectName("primaryButton")
            button.clicked.connect(lambda checked=False, name=label: self._export_report(name))
            actions.addWidget(button)
        actions.addStretch(1)
        card.layout.addLayout(actions)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMinimumHeight(560)
        self.preview.setStyleSheet(
            f"background: {Theme.card}; border: 1px solid {Theme.border}; "
            f"border-radius: {Theme.radius_small}px; padding: 12px;"
        )
        card.layout.addWidget(self.preview, 1)
        self.generate_preview()
        return card

    def generate_preview(self) -> None:
        self.preview.setPlainText(generate_demo_report(self._project_state, self._selected_components()))
        self._on_action("Generate demo report preview")

    def _export_report(self, export_type: str) -> None:
        self._on_action(f"Export {export_type}")

    def _selected_components(self) -> tuple[str, ...]:
        return tuple(check.text() for check in self.checks if check.isChecked())


def generate_demo_report(project_state: MetaProjectState, components: tuple[str, ...] | None = None) -> str:
    selected = set(components or ())
    _studies, forest_summary = project_state.forest_plot
    lines = [
        f"# {project_state.project_name}",
        "",
        f"Project ID: {project_state.project_id}",
        f"Current outcome: {project_state.current_outcome}",
        f"Effect size: {project_state.current_effect_size}",
        "",
    ]
    sections = {
        "Title": f"## Title\n{project_state.project_name}",
        "Abstract": "## Abstract\nThis demo report summarizes a systematic review and meta-analysis workflow.",
        "PICO": "## PICO\nPopulation: adults with severe pneumonia. Intervention: systemic corticosteroids.",
        "Search strategy": "## Search strategy\nDatabases include PubMed, Embase, Web of Science, and Cochrane Library.",
        "PRISMA flow": (
            "## PRISMA flow\n"
            f"Search {project_state.prisma_flow.search_count}; included {project_state.prisma_flow.included_count}."
        ),
        "Included studies": f"## Included studies\n{project_state.metrics.included_studies_count} studies are included.",
        "RoB": "## Risk of Bias\nRoB 2.0 judgements are summarized in the dashboard.",
        "GRADE": f"## GRADE\nEvidence quality for {project_state.grade.outcome}: {project_state.grade.evidence_quality}.",
        "Forest plot": (
            "## Forest plot\n"
            f"Pooled effect {forest_summary.pooled_effect_size:.2f} "
            f"[{forest_summary.ci_low:.2f}, {forest_summary.ci_high:.2f}]."
        ),
        "Funnel plot": "## Funnel plot\nEgger P = 0.18; 未见明显发表偏倚.",
        "Discussion": "## Discussion\nThese demo findings are placeholders pending real statistical analysis binding.",
    }
    for key, text in sections.items():
        if not selected or key in selected:
            lines.extend((text, ""))
    return "\n".join(lines).strip()
