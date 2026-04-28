from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app_meta.core.project_state import (
    AnalysisSettings,
    ForestPlotStudyRow,
    ForestPlotSummary,
    GradeSummary,
    MetaProjectState,
    PrismaFlowState,
    RecentOutputItem,
    RiskOfBiasRow,
)
from app_meta.ui.theme import Theme
from app_meta.ui.icon_registry import meta_icon


def add_shadow(widget: QWidget) -> None:
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(22)
    shadow.setOffset(0, 8)
    shadow.setColor(QColor(15, 23, 42, 24))
    widget.setGraphicsEffect(shadow)


class SectionCard(QFrame):
    def __init__(self, title: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        add_shadow(self)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 16)
        self.layout.setSpacing(12)
        if title:
            label = QLabel(title)
            label.setObjectName("sectionTitle")
            self.layout.addWidget(label)


Card = SectionCard


class SidebarItem(QPushButton):
    def __init__(self, text: str, icon_name: str | None = None) -> None:
        super().__init__(text)
        self.setObjectName("sidebarButton")
        self.setCheckable(True)
        if icon_name:
            self.setIcon(meta_icon(icon_name))
            self.setIconSize(QSize(20, 20))


class IconBadge(QLabel):
    def __init__(self, icon_name: str, color: str = Theme.primary, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(36, 36)
        pixmap = meta_icon(icon_name).pixmap(QSize(22, 22))
        if pixmap.isNull():
            self.setText(_icon_text(icon_name))
        else:
            self.setPixmap(pixmap)
        self.setStyleSheet(
            f"background: {Theme.primary_soft}; color: {color}; border-radius: 18px; font-weight: 700;"
        )


class MetricCard(SectionCard):
    def __init__(self, title: str, value: str, detail: str, icon: str) -> None:
        super().__init__()
        row = QHBoxLayout()
        copy = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("smallMuted")
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 24px; font-weight: 750;")
        detail_label = QLabel(detail)
        detail_label.setObjectName("smallMuted")
        copy.addWidget(title_label)
        copy.addWidget(value_label)
        copy.addWidget(detail_label)
        row.addLayout(copy, 1)
        row.addWidget(IconBadge(_icon_text(icon)))
        self.layout.addLayout(row)


class StatusPill(QLabel):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        colors = {
            "低风险": (Theme.success, Theme.success_soft),
            "某些担忧": (Theme.warning, Theme.warning_soft),
            "高风险": (Theme.danger, Theme.danger_soft),
        }
        fg, bg = colors.get(text, (Theme.muted, "#F2F4F7"))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"color: {fg}; background: {bg}; border-radius: 9px; padding: 4px 8px; font-size: 12px;"
        )


class ProjectProgressCard(QFrame):
    def __init__(self, project: MetaProjectState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"background: {Theme.primary_soft}; border: 1px solid {Theme.border_soft}; border-radius: {Theme.radius}px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(7)

        label = QLabel("当前项目")
        label.setStyleSheet(f"color: {Theme.primary}; font-weight: 700;")
        title = QLabel(project.project_name)
        title.setWordWrap(True)
        title.setStyleSheet("font-weight: 700;")
        meta = QLabel(
            f"ID: {project.project_id}\n创建时间: {project.created_at}\n最后更新: {project.updated_at}"
        )
        meta.setObjectName("smallMuted")
        progress_label = QLabel(f"项目进度: {project.progress_percent}%")
        progress_label.setObjectName("smallMuted")
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(project.progress_percent)
        progress.setTextVisible(False)
        settings = QPushButton("项目设置")

        layout.addWidget(label)
        layout.addWidget(title)
        layout.addWidget(meta)
        layout.addWidget(progress_label)
        layout.addWidget(progress)
        layout.addWidget(settings, alignment=Qt.AlignLeft)
        self.settings_button = settings


class ForestPlotWidget(QWidget):
    def __init__(
        self,
        studies: tuple[ForestPlotStudyRow, ...],
        summary: ForestPlotSummary,
    ) -> None:
        super().__init__()
        self._studies = studies
        self._summary = summary
        self.setMinimumHeight(440)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(6, 6, -6, -6)
        painter.fillRect(rect, QColor("#FFFFFF"))

        left = rect.left() + 16
        plot_left = rect.left() + 390
        plot_right = rect.right() - 250
        right = rect.right() - 12
        top = rect.top() + 36
        row_h = 38
        axis_y = top + row_h * (len(self._studies) + 1) + 22

        painter.setPen(QColor(Theme.text))
        painter.setFont(QFont("Arial", 11, QFont.Bold))
        painter.drawText(left, top - 12, "研究")
        painter.drawText(left + 142, top - 12, "实验组")
        painter.drawText(left + 232, top - 12, "对照组")
        painter.drawText(right - 210, top - 12, "OR (95% CI)")
        painter.drawText(right - 82, top - 12, "权重 (%)")

        x_null = self._x_for_value(1.0, plot_left, plot_right)
        painter.setPen(QPen(QColor("#94A3B8"), 1.2))
        painter.drawLine(QPointF(x_null, top - 18), QPointF(x_null, axis_y - 12))

        painter.setFont(QFont("Arial", 10))
        for i, study in enumerate(self._studies):
            y = top + i * row_h + 10
            painter.setPen(QColor(Theme.text))
            painter.drawText(left, y, study.study_name)
            painter.drawText(left + 142, y, f"{study.experimental_events}/{study.experimental_total}")
            painter.drawText(left + 232, y, f"{study.control_events}/{study.control_total}")
            painter.drawText(right - 210, y, f"{study.effect_size:.2f} [{study.ci_low:.2f}, {study.ci_high:.2f}]")
            painter.drawText(right - 70, y, f"{study.weight_percent:.1f}")

            x1 = self._x_for_value(study.ci_low, plot_left, plot_right)
            x2 = self._x_for_value(study.ci_high, plot_left, plot_right)
            x = self._x_for_value(study.effect_size, plot_left, plot_right)
            painter.setPen(QPen(QColor("#475569"), 1.4))
            painter.drawLine(QPointF(x1, y - 4), QPointF(x2, y - 4))
            size = 7 + study.weight_percent / 4
            painter.fillRect(QRectF(x - size / 2, y - 4 - size / 2, size, size), QColor(Theme.primary))

        pooled_y = top + len(self._studies) * row_h + 14
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(QColor(Theme.text))
        painter.drawText(left, pooled_y, "合计 (95% CI)")
        painter.drawText(left + 142, pooled_y, str(self._summary.total_experimental_n))
        painter.drawText(left + 232, pooled_y, str(self._summary.total_control_n))
        painter.drawText(
            right - 210,
            pooled_y,
            f"{self._summary.pooled_effect_size:.2f} [{self._summary.ci_low:.2f}, {self._summary.ci_high:.2f}]",
        )
        painter.drawText(right - 70, pooled_y, "100.0")
        diamond = [
            QPointF(self._x_for_value(self._summary.ci_low, plot_left, plot_right), pooled_y - 5),
            QPointF(self._x_for_value(self._summary.pooled_effect_size, plot_left, plot_right), pooled_y - 15),
            QPointF(self._x_for_value(self._summary.ci_high, plot_left, plot_right), pooled_y - 5),
            QPointF(self._x_for_value(self._summary.pooled_effect_size, plot_left, plot_right), pooled_y + 5),
        ]
        painter.setBrush(QColor("#111827"))
        painter.setPen(QPen(QColor("#111827"), 1))
        painter.drawPolygon(QPolygonF(diamond))

        painter.setFont(QFont("Arial", 9))
        painter.setPen(QPen(QColor(Theme.border), 1))
        painter.drawLine(QPointF(plot_left, axis_y), QPointF(plot_right, axis_y))
        for label in self._summary.x_axis_labels:
            x = self._x_for_value(label, plot_left, plot_right)
            painter.drawLine(QPointF(x, axis_y - 4), QPointF(x, axis_y + 4))
            painter.setPen(QColor(Theme.muted))
            painter.drawText(QRectF(x - 18, axis_y + 8, 36, 18), Qt.AlignCenter, str(label).rstrip("0").rstrip("."))
            painter.setPen(QPen(QColor(Theme.border), 1))

        text_y = axis_y + 48
        painter.setPen(QColor(Theme.text))
        painter.drawText(left, text_y, "总事件数")
        painter.drawText(left + 142, text_y, str(self._summary.total_experimental_events))
        painter.drawText(left + 232, text_y, str(self._summary.total_control_events))
        painter.drawText(left, text_y + 24, self._summary.heterogeneity_text)
        painter.drawText(left, text_y + 46, self._summary.overall_effect_text)

    def _x_for_value(self, value: float, left: int, right: int) -> float:
        min_log = math.log10(0.1)
        max_log = math.log10(10)
        ratio = (math.log10(value) - min_log) / (max_log - min_log)
        return left + ratio * (right - left)


class PrismaFlowWidget(SectionCard):
    def __init__(
        self,
        flow_state: PrismaFlowState,
        on_action=None,
    ) -> None:
        super().__init__("研究流程（PRISMA）")
        self._on_action = on_action or (lambda _name: None)
        steps = (
            ("搜索", flow_state.search_count),
            ("去重", flow_state.deduplicated_count),
            ("初筛", flow_state.screened_count),
            ("全文", flow_state.full_text_count),
            ("纳入", flow_state.included_count),
        )
        flow = QHBoxLayout()
        flow.setSpacing(8)
        for index, (label, count) in enumerate(steps):
            flow.addWidget(_flow_node(label, count))
            if index < len(steps) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet(f"color: {Theme.muted}; font-size: 18px;")
                flow.addWidget(arrow)
        self.layout.addLayout(flow)

        row = QHBoxLayout()
        details = QPushButton("查看详情")
        refresh = QPushButton("刷新流程")
        details.clicked.connect(lambda: self._on_action("查看详情"))
        refresh.clicked.connect(lambda: self._on_action("刷新流程"))
        row.addWidget(details)
        row.addWidget(refresh)
        row.addStretch(1)
        self.layout.addLayout(row)
        updated = QLabel(f"更新时间: {flow_state.updated_at}")
        updated.setObjectName("smallMuted")
        self.layout.addWidget(updated)


class AnalysisSettingsWidget(SectionCard):
    def __init__(self, settings: AnalysisSettings, on_action=None) -> None:
        super().__init__("分析设置")
        self._on_action = on_action or (lambda _name: None)
        rows = (
            ("效应模型", settings.effect_model),
            ("结局类型", settings.outcome_type),
            ("亚组分析", settings.subgroup_analysis),
            ("敏感性分析", settings.sensitivity_analysis),
            ("发表偏倚检验", settings.publication_bias_test),
            ("连续性校正", settings.continuity_correction),
        )
        for label_text, value_text in rows:
            line = QHBoxLayout()
            label = QLabel(label_text)
            label.setObjectName("smallMuted")
            value = QLabel(value_text)
            value.setAlignment(Qt.AlignRight)
            value.setWordWrap(True)
            line.addWidget(label)
            line.addWidget(value, 1)
            self.layout.addLayout(line)
        edit = QPushButton("编辑")
        edit.clicked.connect(lambda: self._on_action("编辑分析设置"))
        self.layout.addWidget(edit, alignment=Qt.AlignLeft)


class GradeSummaryWidget(SectionCard):
    def __init__(
        self,
        summary: GradeSummary,
    ) -> None:
        super().__init__("证据概览（GRADE）")
        top = QHBoxLayout()
        top.addWidget(QLabel(summary.outcome))
        top.addStretch(1)
        rating = QLabel(summary.evidence_quality)
        rating.setAlignment(Qt.AlignCenter)
        rating.setStyleSheet(
            f"background: {Theme.warning_soft}; color: {Theme.warning}; border-radius: 12px; padding: 5px 12px; font-weight: 700;"
        )
        top.addWidget(rating)
        self.layout.addLayout(top)

        dots = QHBoxLayout()
        rating_colors = {
            "success": Theme.success,
            "warning": Theme.warning,
            "muted": Theme.muted_light,
            "danger": Theme.danger,
        }
        for color_name in summary.rating_levels:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {rating_colors[color_name]}; font-size: 18px;")
            dots.addWidget(dot)
        dots.addStretch(1)
        self.layout.addLayout(dots)

        for domain, judgement in summary.rows:
            line = QLabel(f"{domain}: {judgement}")
            line.setObjectName("smallMuted")
            line.setWordWrap(True)
            self.layout.addWidget(line)
        conclusion = QLabel(summary.conclusion)
        conclusion.setWordWrap(True)
        conclusion.setStyleSheet(
            f"background: {Theme.primary_soft}; color: {Theme.primary}; border-radius: 10px; padding: 10px;"
        )
        self.layout.addWidget(conclusion)


class RiskOfBiasTableWidget(QTableWidget):
    def __init__(self, rows: tuple[RiskOfBiasRow, ...]) -> None:
        headers = ["研究", "随机过程", "偏离干预", "缺失结局", "测量结局", "选择性报告", "总体偏倚"]
        super().__init__(len(rows), len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        for row_index, row in enumerate(rows):
            values = [
                row.study_name,
                row.randomization,
                row.deviations,
                row.missing_outcome,
                row.outcome_measurement,
                row.selective_reporting,
                row.overall,
            ]
            for column_index, value in enumerate(values):
                if column_index == 0:
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.setItem(row_index, column_index, item)
                else:
                    self.setCellWidget(row_index, column_index, StatusPill(value))
        self.resizeColumnsToContents()


class RecentOutputsWidget(SectionCard):
    def __init__(self, outputs: tuple[RecentOutputItem, ...], on_action=None) -> None:
        super().__init__("最近输出")
        self._on_action = on_action or (lambda _name: None)
        for output in outputs:
            row = QHBoxLayout()
            icon = QLabel(output.file_type)
            icon.setAlignment(Qt.AlignCenter)
            icon.setFixedWidth(44)
            icon.setStyleSheet(
                f"background: {Theme.primary_soft}; color: {Theme.primary}; border-radius: 8px; padding: 5px; font-size: 11px; font-weight: 700;"
            )
            text = QLabel(f"{output.filename}\n{output.timestamp}")
            text.setObjectName("smallMuted")
            text.setWordWrap(True)
            row.addWidget(icon)
            row.addWidget(text, 1)
            self.layout.addLayout(row)
        button = QPushButton("打开输出文件夹")
        button.clicked.connect(lambda: self._on_action("打开输出文件夹"))
        self.layout.addWidget(button, alignment=Qt.AlignLeft)


class PlaceholderPage(QWidget):
    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)
        card = SectionCard()
        card.setMaximumWidth(620)
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        desc = QLabel(description)
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        badge = QLabel("Coming soon / 待开发")
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"background: {Theme.primary_soft}; color: {Theme.primary}; border-radius: 12px; padding: 8px 12px; font-weight: 700;"
        )
        card.layout.addWidget(title_label)
        card.layout.addWidget(desc)
        card.layout.addWidget(badge, alignment=Qt.AlignLeft)
        layout.addWidget(card, alignment=Qt.AlignCenter)
        layout.addStretch(1)


def _flow_node(label: str, count: str) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(
        f"background: {Theme.primary_soft}; border: 1px solid {Theme.border_soft}; border-radius: 14px;"
    )
    frame.setFixedWidth(82)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(8, 8, 8, 8)
    number = QLabel(count)
    number.setAlignment(Qt.AlignCenter)
    number.setStyleSheet(f"color: {Theme.primary}; font-weight: 750; font-size: 16px;")
    name = QLabel(label)
    name.setAlignment(Qt.AlignCenter)
    name.setObjectName("smallMuted")
    layout.addWidget(number)
    layout.addWidget(name)
    return frame


def _icon_text(name: str) -> str:
    return {
        "document": "D",
        "shield": "✓",
        "target": "◎",
        "wave": "∿",
    }.get(name, "•")


def secondary_button(text: str) -> QPushButton:
    return QPushButton(text)
