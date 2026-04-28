from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHeaderView,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.project_navigation_model import NavigationItem
from app.project_shell_widget import ProjectShellWidget
from app.ui_style_tokens import COLORS, CONTROL_HEIGHT, SPACING
from app.ui_icon_registry import IconFactory


class VolcanoPlotPreview(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("volcanoPlotPreview")
        self.setMinimumHeight(170)

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(18, 12, -18, -18)
        painter.fillRect(rect, QColor("#FFFFFF"))
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        painter.drawRoundedRect(QRectF(rect), 10, 10)

        plot = rect.adjusted(46, 18, -118, -34)
        axis_pen = QPen(QColor("#8AA0B5"), 1)
        painter.setPen(axis_pen)
        painter.drawLine(plot.bottomLeft(), plot.bottomRight())
        painter.drawLine(plot.bottomLeft(), plot.topLeft())
        painter.setPen(QPen(QColor("#9AA8B8"), 1, Qt.DashLine))
        for threshold in [-1.0, 1.0]:
            tx = plot.left() + ((threshold + 6.0) / 12.0) * plot.width()
            painter.drawLine(QPointF(tx, plot.top()), QPointF(tx, plot.bottom()))
        ty = plot.bottom() - (5.0 / 55.0) * plot.height()
        painter.drawLine(QPointF(plot.left(), ty), QPointF(plot.right(), ty))

        points: list[tuple[float, float, str]] = []
        for index in range(180):
            x = -5.4 + (index % 36) * 0.30
            y = 1.2 + ((index * 11) % 48) * 0.72
            category = "neutral"
            if x > 1.0 and y > 7.0:
                category = "up"
            elif x < -1.0 and y > 7.0:
                category = "down"
            points.append((x, y, category))

        for x, y, category in points:
            px = plot.left() + ((x + 6.0) / 12.0) * plot.width()
            py = plot.bottom() - min(y / 55.0, 1.0) * plot.height()
            color = {
                "up": QColor("#E53935"),
                "down": QColor("#2F80ED"),
                "neutral": QColor("#B9C1CA"),
            }[category]
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            radius = 2.2 if category != "neutral" else 1.9
            painter.drawEllipse(QPointF(px, py), radius, radius)

        painter.setPen(QColor(COLORS["muted"]))
        painter.drawText(plot.adjusted(0, 0, 0, 20), Qt.AlignCenter | Qt.AlignBottom, "log2(Fold Change)")
        painter.save()
        painter.translate(rect.left() + 16, plot.center().y() + 36)
        painter.rotate(-90)
        painter.drawText(QRectF(0, 0, 92, 18), Qt.AlignCenter, "−log10(FDR)")
        painter.restore()

        legend_x = plot.right() + 16
        legend_y = plot.top() + 44
        legend_items = [("上调", "#E53935"), ("下调", "#2F80ED"), ("不显著", "#B9C1CA")]
        for index, (label, color) in enumerate(legend_items):
            y = legend_y + index * 22
            painter.setBrush(QColor(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(legend_x, y), 4, 4)
            painter.setPen(QColor(COLORS["text"]))
            painter.drawText(QRectF(legend_x + 10, y - 8, 80, 18), Qt.AlignLeft | Qt.AlignVCenter, label)


class HeatmapPreview(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("heatmapPreview")
        self.setMinimumHeight(170)

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(18, 12, -18, -18)
        painter.fillRect(rect, QColor("#F9FBFD"))
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        painter.drawRoundedRect(QRectF(rect), 10, 10)

        plot = rect.adjusted(22, 34, -74, -34)
        rows = 10
        cols = 14
        cell_w = plot.width() / cols
        cell_h = plot.height() / rows
        palette = ["#2166AC", "#67A9CF", "#F7F7F7", "#F4A6A6", "#D73027"]
        for row in range(rows):
            for col in range(cols):
                value = (row * 3 + col * 5 + (row + col) % 4) % len(palette)
                painter.fillRect(
                    QRectF(
                        plot.left() + col * cell_w,
                        plot.top() + row * cell_h,
                        cell_w + 0.5,
                        cell_h + 0.5,
                    ),
                    QColor(palette[value]),
                )

        painter.setPen(QColor(COLORS["text"]))
        painter.drawText(rect.adjusted(22, 8, -18, 0), Qt.AlignLeft | Qt.AlignTop, "对照组")
        painter.drawText(rect.adjusted(0, 8, -20, 0), Qt.AlignRight | Qt.AlignTop, "病例组")
        painter.fillRect(QRectF(plot.left(), plot.top() - 10, cell_w * 7, 6), QColor("#2F80ED"))
        painter.fillRect(QRectF(plot.left() + cell_w * 7, plot.top() - 10, cell_w * 7, 6), QColor("#E53935"))
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        painter.drawLine(
            QPointF(plot.left() + cell_w * 7, plot.top()),
            QPointF(plot.left() + cell_w * 7, plot.bottom()),
        )
        genes = ["TP53", "MKI67", "TOP2A", "BIRC5", "CDK1", "CCNB1", "UBE2C", "NUSAP1", "DLGAP5", "AURKA"]
        painter.setFont(QFont(painter.font().family(), 8))
        painter.setPen(QColor(COLORS["text"]))
        for row, gene in enumerate(genes):
            y = plot.top() + row * cell_h + cell_h / 2 + 4
            painter.drawText(QRectF(plot.right() + 8, y - 8, 58, 16), Qt.AlignLeft | Qt.AlignVCenter, gene)
        legend = QRectF(plot.left() + plot.width() * 0.18, rect.bottom() - 18, plot.width() * 0.64, 8)
        for index, color in enumerate(["#2166AC", "#67A9CF", "#F7F7F7", "#F4A6A6", "#D73027"]):
            painter.fillRect(QRectF(legend.left() + index * legend.width() / 5, legend.top(), legend.width() / 5, legend.height()), QColor(color))
        painter.setPen(QColor(COLORS["muted"]))
        painter.drawText(QRectF(legend.left() - 12, legend.bottom(), 28, 14), Qt.AlignLeft, "-2")
        painter.drawText(QRectF(legend.center().x() - 8, legend.bottom(), 20, 14), Qt.AlignCenter, "0")
        painter.drawText(QRectF(legend.right() - 8, legend.bottom(), 28, 14), Qt.AlignRight, "2")


class AnalysisSettingsPanel(QFrame):
    def __init__(self, on_go_sample_groups: Callable[[], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._on_go_sample_groups = on_go_sample_groups
        self.setObjectName("analysisSettingsPanel")
        self.setFixedWidth(300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        header = QHBoxLayout()
        title = QLabel("分析设置")
        title.setObjectName("sectionTitle")
        reset = QPushButton("重置")
        reset.setObjectName("iconButton")
        reset.setFixedHeight(28)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(reset)
        subtitle = QLabel("选择数据、比较组和阈值后启动分析。当前需要先完成数据准备。")
        subtitle.setObjectName("mutedLabel")
        subtitle.setWordWrap(True)
        layout.addLayout(header)
        layout.addWidget(subtitle)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("analysisSettingsScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(SPACING["sm"])

        scroll_layout.addWidget(self._field_label("数据源选择"))
        source_row = QHBoxLayout()
        for text in ["GEO", "TCGA", "GTEx"]:
            button = QPushButton(text)
            button.setObjectName("sourceSegmentButton")
            button.setCheckable(True)
            button.setChecked(text == "TCGA")
            source_row.addWidget(button)
        scroll_layout.addLayout(source_row)

        for label, values in [
            ("项目 / 数据集", ["TCGA-LUAD (Lung Adenocarcinoma)", "请选择数据集", "本地表达矩阵"]),
            ("基因集", ["Homo sapiens (GRCh38)", "Hallmark", "GO BP", "KEGG"]),
            ("分析方法", ["DESeq2", "limma", "edgeR"]),
        ]:
            scroll_layout.addWidget(self._field_label(label))
            combo = QComboBox()
            combo.addItems(values)
            scroll_layout.addWidget(combo)

        scroll_layout.addWidget(self._field_label("比较组"))
        group_row = QHBoxLayout()
        group_row.setSpacing(SPACING["sm"])
        for title_text, detail_text, name in [
            ("对照组", "正常 · n=256", "comparisonControlChip"),
            ("病例组", "肿瘤 · n=256", "comparisonCaseChip"),
        ]:
            group_row.addWidget(self._comparison_chip(title_text, detail_text, name))
        scroll_layout.addLayout(group_row)

        scroll_layout.addWidget(self._field_label("log2FC 阈值"))
        log2fc = QDoubleSpinBox()
        log2fc.setRange(0.0, 10.0)
        log2fc.setSingleStep(0.1)
        log2fc.setValue(1.0)
        scroll_layout.addWidget(log2fc)

        scroll_layout.addWidget(self._field_label("FDR 阈值"))
        fdr = QDoubleSpinBox()
        fdr.setRange(0.0, 1.0)
        fdr.setSingleStep(0.01)
        fdr.setValue(0.05)
        scroll_layout.addWidget(fdr)

        checklist = QFrame()
        checklist.setObjectName("readinessChecklist")
        checklist_layout = QVBoxLayout(checklist)
        checklist_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        checklist_layout.setSpacing(SPACING["xs"])
        checklist_layout.addWidget(self._field_label("分析前检查"))
        for label, status, kind in [
            ("表达矩阵", "Ready", "ready"),
            ("样本分组", "Needs attention", "warning"),
            ("比较组", "Selected", "ready"),
            ("参数设置", "Ready", "ready"),
        ]:
            checklist_layout.addWidget(self._check_row(label, status, kind))
        scroll_layout.addWidget(checklist)

        readiness_note = QLabel("样本分组尚未完成，无法开始差异分析。请先进入样本分组页面完成分组。")
        readiness_note.setObjectName("friendlyStatusLabel")
        readiness_note.setWordWrap(True)
        scroll_layout.addWidget(readiness_note)
        go_groups = QPushButton("前往样本分组")
        go_groups.setObjectName("secondaryButton")
        if self._on_go_sample_groups is not None:
            go_groups.clicked.connect(self._on_go_sample_groups)
        scroll_layout.addWidget(go_groups)

        advanced = QToolButton()
        advanced.setObjectName("advancedOptionsButton")
        advanced.setText("高级选项")
        advanced.setCheckable(True)
        advanced.setChecked(False)
        advanced.setToolButtonStyle(Qt.ToolButtonTextOnly)
        scroll_layout.addWidget(advanced)
        scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area, 1)

        button = QPushButton("开始分析")
        button.setObjectName("primaryButton")
        button.setEnabled(False)
        button.setToolTip("样本分组尚未完成，暂不能开始分析。")
        button.setMinimumHeight(CONTROL_HEIGHT["primary"])
        layout.addWidget(button)

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-weight: 600; background: transparent;")
        return label

    def _comparison_chip(self, title_text: str, detail_text: str, name: str) -> QFrame:
        chip = QFrame()
        chip.setObjectName(name)
        chip.setMinimumHeight(70)
        layout = QVBoxLayout(chip)
        layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
        layout.setSpacing(SPACING["xs"])
        title = QLabel(title_text)
        title.setObjectName("comparisonChipTitle")
        title.setWordWrap(True)
        detail = QLabel(detail_text)
        detail.setObjectName("comparisonChipDetail")
        detail.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(detail)
        return chip

    def _check_row(self, label: str, status: str, kind: str) -> QFrame:
        row = QFrame()
        row.setObjectName("readinessRow")
        row.setMinimumHeight(28)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])
        icon_name = "completed" if kind == "ready" else "needs_attention"
        icon = QLabel()
        icon.setPixmap(IconFactory.status_icon(icon_name).pixmap(IconFactory.icon_size("status")))
        icon.setFixedSize(16, 16)
        title = QLabel(label)
        title.setObjectName("readinessItemLabel")
        title.setWordWrap(True)
        badge = QLabel(status)
        badge.setObjectName("readinessBadgeReady" if kind == "ready" else "readinessBadgeWarning")
        badge.setWordWrap(True)
        badge.setMinimumHeight(22)
        layout.addWidget(icon)
        layout.addWidget(title, 1)
        layout.addWidget(badge)
        return row


class BioinformaticsWorkspaceWidget(ProjectShellWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            project_type="bioinformatics",
            title="BioMedPilot · 生信分析",
            accent_color=COLORS["bio"],
            home_widget_factory=self._build_home_page,
            settings_panel_factory=lambda: AnalysisSettingsPanel(
                on_go_sample_groups=lambda: self.select_navigation_item("sample-groups")
            ),
            parent=parent,
        )

    def _build_placeholder_page(self, item: NavigationItem) -> QWidget:
        if item.key == "data-search":
            return self._build_data_search_page(item)
        if item.key == "data-assets":
            return self._build_data_assets_page(item)
        if item.key == "sample-groups":
            return self._build_sample_groups_page(item)
        if item.key == "deg":
            return self._build_deg_page(item)
        if item.key == "enrichment":
            return self._build_enrichment_page(item)
        if item.key == "correlation":
            return self._build_correlation_page(item)
        if item.key == "survival":
            return self._build_survival_page(item)
        if item.key == "visualization":
            return self._build_visualization_page(item)
        if item.key == "reporting":
            return self._build_reporting_page(item)
        if item.key == "tasks":
            return self._build_tasks_page(item)
        return super()._build_placeholder_page(item)

    def select_navigation_item(self, key: str) -> None:
        super().select_navigation_item(key)
        status_map = {
            "enrichment": "需要处理：请先完成差异分析后再运行富集分析。",
            "deg": "需要处理：请先完成样本分组后再进入差异分析。",
            "tasks": "需要处理：样本分组缺失",
        }
        state_text = status_map.get(key, "就绪")
        self._status_label.setText(f"{state_text} · BioMedPilot 0.1.0 · 内存 1.2 GB · CPU 8%")
        if self._bottom_status_bar is not None:
            self._bottom_status_bar.set_status(
                state_text,
                "BioMedPilot 0.1.0",
                "内存 1.2 GB · CPU 8%",
            )

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["lg"])

        demo_banner = QFrame()
        demo_banner.setObjectName("demoPreviewBanner")
        demo_layout = QHBoxLayout(demo_banner)
        demo_layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        demo_title = QLabel("示例项目预览 · Demo Preview")
        demo_title.setStyleSheet("font-weight: 700; background: transparent;")
        demo_text = QLabel("当前展示为示例数据。导入真实数据后，这里将显示你的项目结果。")
        demo_text.setObjectName("mutedLabel")
        demo_layout.addWidget(demo_title)
        demo_layout.addWidget(demo_text, 1)
        layout.addWidget(demo_banner)

        stats = QGridLayout()
        stats.setSpacing(SPACING["md"])
        cards = [
            ("数据源", "3", "GEO · TCGA · GTEx"),
            ("当前项目", "Lung Cancer Study", "TCGA-LUAD"),
            ("活跃任务", "2", "运行中"),
            ("样本数", "512", "病例 256 · 对照 256"),
        ]
        for index, (label, value, detail) in enumerate(cards):
            stats.addWidget(self._stat_card(label, value, detail), 0, index)
        layout.addLayout(stats)

        charts = QHBoxLayout()
        charts.setSpacing(SPACING["md"])
        charts.addWidget(
            self._volcano_card(
                "差异表达 · Volcano Plot",
                "上调 286 · 下调 194 · 不显著 18,420",
            )
        )
        charts.addWidget(
            self._heatmap_card(
                "差异表达 · Heatmap (Top 50)",
                "对照组 · 病例组",
            )
        )
        layout.addLayout(charts, 1)

        lower = QGridLayout()
        lower.setSpacing(SPACING["md"])
        lower.addWidget(
            self._info_card(
                "近期结果",
                [
                    "LUAD_DEG_20240520",
                    "LUAD_KEGG_20240519",
                    "LUAD_Survival_20240518",
                    "LUAD_Correlation_20240518",
                ],
            ),
            0,
            0,
        )
        lower.addWidget(
            self._workflow_card(),
            0,
            1,
        )
        lower.addWidget(
            self._info_card(
                "系统消息",
                [
                    "数据源更新：GEO 索引已同步",
                    "功能更新：热图导出入口已加入",
                    "系统维护：本地缓存状态正常",
                ],
            ),
            0,
            2,
        )
        layout.addLayout(lower)
        return page

    def _stat_card(self, label: str, value: str, detail: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("statCard")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        layout.setSpacing(SPACING["md"])
        text_layout = QVBoxLayout()
        text_layout.setSpacing(SPACING["xs"])
        label_widget = QLabel(label)
        label_widget.setObjectName("mutedLabel")
        value_widget = QLabel(value)
        value_widget.setObjectName("statCardValue")
        detail_widget = QLabel(detail)
        detail_widget.setObjectName("mutedLabel")
        detail_widget.setWordWrap(True)
        text_layout.addWidget(label_widget)
        text_layout.addWidget(value_widget)
        text_layout.addWidget(detail_widget)
        icon_map = {
            "数据源": "data_sources",
            "当前项目": "current_project",
            "活跃任务": "active_tasks",
            "样本数": "sample_count",
        }
        icon = QLabel()
        icon.setObjectName("statCardIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(IconFactory.dashboard_icon(icon_map.get(label, "data_sources")).pixmap(IconFactory.icon_size("stat")))
        icon.setFixedSize(50, 50)
        layout.addLayout(text_layout, 1)
        layout.addWidget(icon)
        return frame

    def _workflow_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["sm"])
        title_widget = QLabel("分析流程")
        title_widget.setStyleSheet("font-weight: 700; background: transparent;")
        layout.addWidget(title_widget)
        for line in [
            "数据准备：已完成",
            "差异表达分析：等待分组确认",
            "富集分析：运行中 45%",
            "可视化生成：等待中",
        ]:
            layout.addWidget(self._muted(line))
        next_step = QLabel("推荐下一步：检查样本分组")
        next_step.setObjectName("friendlyStatusLabel")
        next_step.setWordWrap(True)
        layout.addWidget(next_step)
        go_groups = QPushButton("前往样本分组")
        go_groups.setObjectName("primaryButton")
        go_groups.clicked.connect(lambda: self.select_navigation_item("sample-groups"))
        layout.addWidget(go_groups, alignment=Qt.AlignLeft)
        layout.addStretch(1)
        return frame

    def _volcano_card(self, title: str, summary: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setMinimumHeight(240)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])
        header = QHBoxLayout()
        title_widget = QLabel(title)
        title_widget.setStyleSheet("font-weight: 700; background: transparent;")
        gene_count = QLabel("总基因数：20,531")
        gene_count.setObjectName("mutedLabel")
        details = QPushButton("查看详情")
        details.setObjectName("secondaryButton")
        details.setFixedHeight(30)
        header.addWidget(title_widget)
        header.addStretch(1)
        header.addWidget(gene_count)
        header.addWidget(details)
        summary_label = QLabel(summary)
        summary_label.setObjectName("mutedLabel")
        legend = QLabel("上调：1,248 · 下调：1,076 · 不显著：18,207")
        legend.setObjectName("mutedLabel")
        plot = VolcanoPlotPreview()
        layout.addLayout(header)
        layout.addWidget(summary_label)
        layout.addWidget(plot, 1)
        layout.addWidget(legend)
        return frame

    def _heatmap_card(self, title: str, summary: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setMinimumHeight(240)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])
        header = QHBoxLayout()
        title_widget = QLabel(title)
        title_widget.setStyleSheet("font-weight: 700; background: transparent;")
        expand_button = QPushButton("⛶")
        expand_button.setObjectName("iconButton")
        expand_button.setToolTip("放大查看")
        expand_button.setFixedSize(30, 30)
        export_button = QPushButton("↓")
        export_button.setObjectName("iconButton")
        export_button.setToolTip("导出图表")
        export_button.setFixedSize(30, 30)
        header.addWidget(title_widget)
        header.addStretch(1)
        header.addWidget(expand_button)
        header.addWidget(export_button)
        summary_label = QLabel(summary)
        summary_label.setObjectName("mutedLabel")
        group_label = QLabel("对照 (n=6)                         病例 (n=6)")
        group_label.setObjectName("mutedLabel")
        group_label.setAlignment(Qt.AlignCenter)
        plot = HeatmapPreview()
        layout.addLayout(header)
        layout.addWidget(summary_label)
        layout.addWidget(group_label)
        layout.addWidget(plot, 1)
        return frame

    def _info_card(self, title: str, lines: list[str]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["sm"])
        title_widget = QLabel(title)
        title_widget.setStyleSheet("font-weight: 700; background: transparent;")
        layout.addWidget(title_widget)
        for line in lines:
            label = QLabel(line)
            label.setObjectName("mutedLabel")
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addStretch(1)
        return frame

    def _build_deg_page(self, item: NavigationItem) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])

        header = QFrame()
        header.setObjectName("card")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["lg"])
        title = QLabel(item.title)
        title.setObjectName("sectionTitle")
        description = QLabel("基于当前项目的病例组与对照组，准备差异表达分析并预览 DEG 结果结构。")
        description.setObjectName("mutedLabel")
        description.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(description)
        layout.addWidget(header)

        summary = QGridLayout()
        summary.setSpacing(SPACING["md"])
        summary.addWidget(
            self._summary_card(
                "比较组卡片",
                ["对照组：Normal", "病例组：Tumor", "样本数：病例 256 · 对照 256"],
            ),
            0,
            0,
        )
        summary.addWidget(
            self._summary_card(
                "分析参数摘要",
                ["方法：DESeq2", "|log2FC| ≥ 1.0", "FDR < 0.05"],
            ),
            0,
            1,
        )
        layout.addLayout(summary)

        middle = QHBoxLayout()
        middle.setSpacing(SPACING["md"])
        middle.addWidget(
            self._volcano_card(
                "Volcano Plot 预览",
                "上调 286 · 下调 194 · 不显著 18,420",
            ),
            1,
        )
        middle.addWidget(self._deg_table_card(), 1)
        layout.addLayout(middle, 1)

        status = QFrame()
        status.setObjectName("card")
        status_layout = QHBoxLayout(status)
        status_layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        status_text = QLabel(
            "样本分组信息缺失，无法运行差异表达分析。请先进入样本分组页面，为样本指定对照组和病例组。"
        )
        status_text.setObjectName("friendlyStatusLabel")
        status_text.setWordWrap(True)
        go_group = QPushButton("前往样本分组")
        go_group.setObjectName("secondaryButton")
        go_group.clicked.connect(lambda: self.select_navigation_item("sample-groups"))
        status_layout.addWidget(status_text, 1)
        status_layout.addWidget(go_group)
        layout.addWidget(status)

        actions = QHBoxLayout()
        start = QPushButton("开始差异分析")
        start.setObjectName("primaryButton")
        start.setEnabled(False)
        export = QPushButton("导出 DEG 表")
        export.setObjectName("secondaryButton")
        export.setEnabled(False)
        view = QPushButton("查看火山图")
        view.setObjectName("secondaryButton")
        view.setEnabled(False)
        actions.addWidget(start)
        actions.addWidget(export)
        actions.addWidget(view)
        actions.addStretch(1)
        layout.addLayout(actions)
        return page

    def _build_data_assets_page(self, item: NavigationItem) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])

        layout.addWidget(self._page_header(item.title, "识别并整理当前项目的数据文件，明确哪些资产已准备好、哪些还需要补充。"))

        overview = QGridLayout()
        overview.setSpacing(SPACING["md"])
        for index, (title, lines) in enumerate(
            [
                ("数据资产概览", ["已识别 4 类资产", "需要检查 1 项", "缺失 1 项", "不可用 1 项"]),
                ("下一步", ["先预览表达矩阵和样本注释。", "缺失临床数据时，请导入补充文件。"]),
                ("资产详情面板", ["当前选中：表达矩阵", "样本 512 · 基因 20,184", "状态：已识别"]),
            ]
        ):
            overview.addWidget(self._summary_card(title, lines), 0, index)
        layout.addLayout(overview)
        layout.addWidget(self._empty_state_card("No Data Imported", "真实项目导入前，当前资产表仅用于说明数据类型和检查路径。", "no_data"))

        table_card = QFrame()
        table_card.setObjectName("card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        table_layout.setSpacing(SPACING["md"])
        title = QLabel("资产分类表")
        title.setStyleSheet("font-weight: 700; background: transparent;")
        table = self._table(
            "dataAssetClassificationTable",
            ["资产类型", "文件 / 来源", "状态", "下一步"],
            [
                ("表达矩阵", "TCGA-LUAD_counts.tsv", "已识别", "预览"),
                ("样本注释", "sample_annotation.tsv", "已识别", "预览"),
                ("临床数据", "clinical_survival.tsv", "需要检查", "核对字段"),
                ("平台注释", "gencode.v38.annotation.gtf", "已识别", "预览"),
                ("原始补充文件", "supplementary_raw.zip", "不可用", "重新分配类型"),
                ("支持文档", "README_data_source.pdf", "缺失", "导入缺失文件"),
            ],
        )
        table_layout.addWidget(title)
        table_layout.addWidget(table, 1)
        layout.addWidget(table_card, 1)

        actions = QHBoxLayout()
        for text, name in [
            ("识别数据资产", "primaryButton"),
            ("预览", "secondaryButton"),
            ("重新分配类型", "secondaryButton"),
            ("导入缺失文件", "secondaryButton"),
        ]:
            button = QPushButton(text)
            button.setObjectName(name)
            button.setEnabled(text == "识别数据资产")
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)

        status = QLabel("请先处理“缺失”和“不可用”的资产，再进入样本分组和差异分析。")
        status.setObjectName("friendlyStatusLabel")
        status.setWordWrap(True)
        layout.addWidget(status)
        return page

    def _build_sample_groups_page(self, item: NavigationItem) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])

        layout.addWidget(self._page_header(item.title, "检查样本注释并确认最终分析分组，确保后续差异分析使用正确比较组。"))

        stats = QGridLayout()
        stats.setSpacing(SPACING["md"])
        for index, (title, lines) in enumerate(
            [
                ("分组统计卡片", ["Control 组 n=256", "Case 组 n=256", "未分组 n=12"]),
                ("分组检查提示", ["请至少设置两个分析组。", "有未分组样本，请处理后再运行差异分析。"]),
                ("下一步", ["确认最终分组。", "保存后进入差异分析页面。"]),
            ]
        ):
            stats.addWidget(self._summary_card(title, lines), 0, index)
        layout.addLayout(stats)
        layout.addWidget(self._empty_state_card("Needs attention", "仍有未分组样本。请完成最终分组后再进入差异分析。", "no_data"))

        table_card = QFrame()
        table_card.setObjectName("card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        table_layout.setSpacing(SPACING["md"])
        title = QLabel("样本表格")
        title.setStyleSheet("font-weight: 700; background: transparent;")
        table = self._table(
            "sampleGroupingTable",
            ["Sample ID", "样本标题", "来源", "自动识别分组", "最终分组", "是否纳入", "备注"],
            [
                ("TCGA-55-1592", "LUAD tumor sample", "TCGA-LUAD", "Case", "Case", "是", "肿瘤组织"),
                ("TCGA-44-2655", "LUAD normal sample", "TCGA-LUAD", "Control", "Control", "是", "邻近正常"),
                ("GTEX-11DXX", "Lung tissue", "GTEx", "Control", "Control", "是", "正常肺组织"),
                ("TCGA-50-5931", "Primary tumor", "TCGA-LUAD", "Case", "Case", "是", "病例组"),
                ("GSM3121001", "unknown phenotype", "GEO", "未识别", "未分组", "否", "需要人工确认"),
            ],
        )
        table_layout.addWidget(title)
        table_layout.addWidget(table, 1)
        layout.addWidget(table_card, 1)

        actions = QHBoxLayout()
        for text, name in [
            ("自动识别分组", "primaryButton"),
            ("手动编辑分组", "secondaryButton"),
        ]:
            button = QPushButton(text)
            button.setObjectName(name)
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)

        status = QLabel("有未分组样本时，请先手动指定最终分组或设为不纳入，再继续差异分析。")
        status.setObjectName("friendlyStatusLabel")
        status.setWordWrap(True)
        layout.addWidget(status)
        return page

    def _build_data_search_page(self, item: NavigationItem) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])
        layout.addWidget(self._page_header(item.title, "围绕研究问题检索 GEO、TCGA、GTEx 等公共数据源，筛选可用于后续分析的数据集。"))

        top = QGridLayout()
        top.setSpacing(SPACING["md"])
        top.addWidget(self._summary_card("当前状态卡片", ["Requires setup", "公共数据源检索入口已准备。", "当前展示为示例检索结果。"]), 0, 0)
        top.addWidget(self._summary_card("下一步建议", ["输入疾病或基因关键词。", "确认物种和数据源。", "选择候选数据集进入数据资产。"]), 0, 1)
        top.addWidget(self._empty_state_card("No Data Imported", "输入研究问题或关键词后开始检索公共数据集。", "no_data"), 0, 2)
        layout.addLayout(top)

        body = QHBoxLayout()
        body.setSpacing(SPACING["md"])
        input_card = QFrame()
        input_card.setObjectName("card")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        input_layout.setSpacing(SPACING["sm"])
        input_layout.addWidget(self._section_label("输入区"))
        for label, value in [
            ("研究问题输入框", "肺腺癌中 EGFR 相关表达特征"),
            ("疾病关键词", "lung adenocarcinoma"),
            ("基因关键词", "EGFR"),
        ]:
            input_layout.addWidget(self._field_label(label))
            field = QLineEdit(value)
            field.setReadOnly(True)
            input_layout.addWidget(field)
        input_layout.addWidget(self._field_label("数据源选择"))
        input_layout.addWidget(self._muted("GEO / TCGA / GTEx"))
        input_layout.addWidget(self._field_label("物种选择"))
        input_layout.addWidget(self._muted("Homo sapiens"))
        input_layout.addWidget(self._muted("空状态：输入研究问题或关键词后开始检索公共数据集。"))
        input_layout.addStretch(1)
        body.addWidget(input_card)

        output_card = QFrame()
        output_card.setObjectName("card")
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        output_layout.setSpacing(SPACING["md"])
        output_layout.addWidget(self._section_label("输出 / 预览区"))
        output_layout.addWidget(
            self._table(
                "datasetSearchResultsTable",
                ["Dataset ID", "Title", "Source", "Samples", "Platform", "Status", "Action"],
                [
                    ("GSE31210", "LUAD expression cohort", "GEO", "226", "GPL570", "Ready", "预览"),
                    ("TCGA-LUAD", "Lung Adenocarcinoma", "TCGA", "512", "RNA-seq", "Ready", "选择"),
                    ("GTEx Lung", "Normal lung tissue", "GTEx", "578", "RNA-seq", "Requires setup", "配置"),
                ],
            ),
            1,
        )
        body.addWidget(output_card, 2)
        layout.addLayout(body, 1)

        actions = QHBoxLayout()
        start = QPushButton("开始检索")
        start.setObjectName("primaryButton")
        actions.addWidget(start)
        actions.addWidget(self._muted("提示：检索结果为示例预览，连接真实数据源后可选择并导入项目。"), 1)
        layout.addLayout(actions)
        status = QLabel("状态说明：当前检索结果为示例项目预览，不会自动下载或导入真实数据。")
        status.setObjectName("friendlyStatusLabel")
        status.setWordWrap(True)
        layout.addWidget(status)
        return page

    def _build_enrichment_page(self, item: NavigationItem) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])
        layout.addWidget(self._page_header(item.title, "基于差异基因列表进行 GO、KEGG 或 GSEA 通路解释，并预览富集结果。"))

        top = QGridLayout()
        top.setSpacing(SPACING["md"])
        top.addWidget(self._summary_card("当前状态卡片", ["Locked", "请先完成差异表达分析。", "当前仅展示通路结果结构。"]), 0, 0)
        top.addWidget(self._summary_card("输入区", ["分析类型：GO / KEGG / GSEA", "基因列表：上调 DEG / 下调 DEG", "校正方法：BH"]), 0, 1)
        top.addWidget(self._summary_card("下一步建议", ["完成样本分组。", "运行差异表达分析。", "再启动富集分析。"]), 0, 2)
        layout.addLayout(top)

        body = QHBoxLayout()
        body.setSpacing(SPACING["md"])
        table_card = QFrame()
        table_card.setObjectName("card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        table_layout.setSpacing(SPACING["md"])
        table_layout.addWidget(self._section_label("输出 / 预览区"))
        table_layout.addWidget(
            self._table(
                "enrichmentResultsTable",
                ["Term", "Database", "Count", "FDR", "Status"],
                [
                    ("Cell cycle", "KEGG", "42", "0.0004", "示例"),
                    ("DNA replication", "GO BP", "35", "0.0012", "示例"),
                    ("p53 signaling pathway", "KEGG", "18", "0.0068", "示例"),
                ],
            ),
            1,
        )
        body.addWidget(table_card, 2)
        dotplot = QFrame()
        dotplot.setObjectName("card")
        dotplot_layout = QVBoxLayout(dotplot)
        dotplot_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        dotplot_layout.addWidget(self._section_label("Dotplot preview"))
        dotplot_layout.addWidget(self._muted("GO / KEGG dotplot 将在差异分析结果准备完成后生成。"))
        dotplot_layout.addWidget(self._muted("空状态：尚未获得可用于富集分析的基因列表。"))
        dotplot_layout.addWidget(self._empty_state_card("Needs data", "完成差异分析后，这里会显示 GO / KEGG / GSEA 图表预览。", "no_data"))
        dotplot_layout.addStretch(1)
        body.addWidget(dotplot)
        layout.addLayout(body, 1)

        status = QLabel("状态说明：请先完成差异表达分析。完成后，上调和下调基因列表会自动带入本页面。")
        status.setObjectName("friendlyStatusLabel")
        status.setWordWrap(True)
        layout.addWidget(status)
        action = QPushButton("运行富集分析")
        action.setObjectName("primaryButton")
        action.setEnabled(False)
        layout.addWidget(action, alignment=Qt.AlignLeft)
        return page

    def _build_correlation_page(self, item: NavigationItem) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])
        layout.addWidget(self._page_header(item.title, "探索目标基因与表型、免疫评分或其他基因表达之间的相关关系。"))

        top = QGridLayout()
        top.setSpacing(SPACING["md"])
        top.addWidget(self._summary_card("当前状态卡片", ["Ready", "可配置目标基因和相关方法。", "当前结果为示例预览。"]), 0, 0)
        top.addWidget(self._summary_card("输入区", ["目标基因输入：EGFR", "方法选择：Pearson / Spearman", "样本范围：当前项目样本"]), 0, 1)
        top.addWidget(self._summary_card("下一步建议", ["确认目标基因存在于表达矩阵。", "选择 Spearman 用于稳健探索。"]), 0, 2)
        layout.addLayout(top)

        body = QHBoxLayout()
        body.setSpacing(SPACING["md"])
        table_card = QFrame()
        table_card.setObjectName("card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        table_layout.setSpacing(SPACING["md"])
        table_layout.addWidget(self._section_label("输出 / 预览区 · 相关性结果表"))
        table_layout.addWidget(
            self._table(
                "correlationResultsTable",
                ["Target", "Variable", "Method", "r / rho", "FDR"],
                [
                    ("EGFR", "MKI67", "Spearman", "0.48", "0.004"),
                    ("EGFR", "Immune score", "Spearman", "-0.31", "0.038"),
                    ("EGFR", "Tumor purity", "Pearson", "0.27", "0.052"),
                ],
            ),
            1,
        )
        body.addWidget(table_card, 2)
        scatter = QFrame()
        scatter.setObjectName("card")
        scatter_layout = QVBoxLayout(scatter)
        scatter_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        scatter_layout.addWidget(self._section_label("Scatter preview"))
        scatter_layout.addWidget(self._muted("散点图矩阵预览：EGFR vs MKI67 / Immune score / Tumor purity"))
        scatter_layout.addWidget(self._muted("空状态：尚未选择目标基因或表型变量。"))
        scatter_layout.addWidget(self._empty_state_card("Ready", "选择目标基因和变量后，这里会展示相关散点图。", "no_data"))
        scatter_layout.addStretch(1)
        body.addWidget(scatter)
        layout.addLayout(body, 1)

        action = QPushButton("运行相关性分析")
        action.setObjectName("primaryButton")
        layout.addWidget(action, alignment=Qt.AlignLeft)
        status = QLabel("状态说明：相关性分析用于探索变量关系，示例结果不会被写入真实项目。")
        status.setObjectName("friendlyStatusLabel")
        status.setWordWrap(True)
        layout.addWidget(status)
        return page

    def _build_survival_page(self, item: NavigationItem) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])
        layout.addWidget(self._page_header(item.title, "检查临床随访字段，基于目标基因表达生成 KM 曲线和 Cox 结果预览。"))

        top = QGridLayout()
        top.setSpacing(SPACING["md"])
        top.addWidget(self._summary_card("临床数据检查", ["Needs data", "当前项目未检测到临床生存数据。", "需要 time / status 字段。"]), 0, 0)
        top.addWidget(self._summary_card("输入区", ["目标基因选择：EGFR", "分组方式：中位数切分", "结局：Overall survival"]), 0, 1)
        top.addWidget(self._summary_card("下一步建议", ["导入临床数据。", "或跳过生存分析进入可视化。"]), 0, 2)
        layout.addLayout(top)

        body = QHBoxLayout()
        body.setSpacing(SPACING["md"])
        km = QFrame()
        km.setObjectName("card")
        km_layout = QVBoxLayout(km)
        km_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        km_layout.addWidget(self._section_label("输出 / 预览区 · KM plot preview"))
        km_layout.addWidget(self._muted("Kaplan-Meier 曲线预览将在临床生存数据导入后显示。"))
        km_layout.addWidget(self._muted("空状态：当前项目未检测到临床生存数据。"))
        km_layout.addWidget(self._empty_state_card("No Data Imported", "导入临床生存数据后，这里会显示 KM 曲线。", "no_data"))
        km_layout.addStretch(1)
        body.addWidget(km)
        cox = QFrame()
        cox.setObjectName("card")
        cox_layout = QVBoxLayout(cox)
        cox_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        cox_layout.setSpacing(SPACING["md"])
        cox_layout.addWidget(self._section_label("Cox result preview"))
        cox_layout.addWidget(
            self._table(
                "coxResultPreviewTable",
                ["Variable", "HR", "95% CI", "P value", "Status"],
                [("EGFR high", "-", "-", "-", "Needs data")],
            ),
            1,
        )
        body.addWidget(cox)
        layout.addLayout(body, 1)

        warning = QLabel("状态说明：当前项目未检测到临床生存数据。请导入包含随访时间和结局状态的临床表，或跳过生存分析。")
        warning.setObjectName("friendlyStatusLabel")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        actions = QHBoxLayout()
        for text, name, enabled in [
            ("运行生存分析", "primaryButton", False),
            ("导入临床数据", "secondaryButton", True),
            ("跳过生存分析", "secondaryButton", True),
        ]:
            button = QPushButton(text)
            button.setObjectName(name)
            button.setEnabled(enabled)
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return page

    def _build_visualization_page(self, item: NavigationItem) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])
        layout.addWidget(self._page_header(item.title, "集中管理项目图表，调整样式后用于论文图、报告和结果复核。"))

        columns = QHBoxLayout()
        columns.setSpacing(SPACING["md"])
        columns.addWidget(
            self._list_card(
                "图表类型列表",
                [
                    "Volcano Plot",
                    "Heatmap",
                    "Boxplot",
                    "PCA Plot",
                    "GO Dotplot",
                    "KEGG Dotplot",
                    "GSEA Curve",
                    "Correlation Scatter",
                    "KM Curve",
                ],
            )
        )
        preview = QFrame()
        preview.setObjectName("card")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        preview_layout.setSpacing(SPACING["md"])
        preview_layout.addWidget(self._section_label("图表预览"))
        preview_layout.addWidget(VolcanoPlotPreview(), 1)
        preview_layout.addWidget(self._muted("当前预览：Volcano Plot · 上调 286 · 下调 194 · 不显著 18,420"))
        preview_layout.addWidget(self._muted("空状态：完成分析后，可在此切换真实项目图表。"))
        columns.addWidget(preview, 2)
        columns.addWidget(
            self._list_card(
                "图表设置",
                [
                    "标题：LUAD differential expression",
                    "坐标轴：log2FC / -log10(FDR)",
                    "字体大小：12 pt",
                    "图例位置：右上",
                    "图片尺寸：1800 × 1400 px",
                    "分辨率：300 dpi",
                    "加入报告：是",
                ],
            )
        )
        layout.addLayout(columns, 1)

        actions = QHBoxLayout()
        for text, name, enabled in [
            ("重新生成", "primaryButton", True),
            ("导出 PNG", "secondaryButton", False),
            ("导出 PDF", "secondaryButton", False),
            ("加入报告", "secondaryButton", True),
        ]:
            button = QPushButton(text)
            button.setObjectName(name)
            button.setEnabled(enabled)
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
        status = QLabel("导出 PNG / PDF Requires setup；重新生成仅使用当前示例结果预览，不会重新运行分析。")
        status.setObjectName("friendlyStatusLabel")
        status.setWordWrap(True)
        layout.addWidget(status)
        return page

    def _build_reporting_page(self, item: NavigationItem) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])
        layout.addWidget(self._page_header(item.title, "选择报告模板和内容范围，生成可复核的医学科研分析报告草稿。"))

        top = QGridLayout()
        top.setSpacing(SPACING["md"])
        top.addWidget(
            self._summary_card(
                "报告模板选择",
                ["模板：生信分析标准报告", "章节结构：数据、方法、结果、图表", "状态：Coming soon"],
            ),
            0,
            0,
        )
        top.addWidget(
            self._summary_card(
                "语言选择",
                ["中文", "English", "双语摘要 Coming soon"],
            ),
            0,
            1,
        )
        top.addWidget(
            self._summary_card(
                "格式选择",
                ["Word：Requires setup", "PDF：Requires setup", "图表包：Coming soon"],
            ),
            0,
            2,
        )
        layout.addLayout(top)

        middle = QHBoxLayout()
        middle.setSpacing(SPACING["md"])
        content_card = QFrame()
        content_card.setObjectName("card")
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        content_layout.setSpacing(SPACING["sm"])
        content_layout.addWidget(self._section_label("报告内容勾选"))
        for text in [
            "研究问题",
            "数据集信息",
            "数据处理流程",
            "样本分组",
            "差异分析结果",
            "富集分析结果",
            "相关性分析结果",
            "生存分析结果",
            "图表",
            "方法草稿",
        ]:
            checkbox = QCheckBox(text)
            checkbox.setChecked(text in {"研究问题", "数据集信息", "样本分组", "差异分析结果", "图表", "方法草稿"})
            content_layout.addWidget(checkbox)
        content_layout.addStretch(1)
        middle.addWidget(content_card)

        preview = QFrame()
        preview.setObjectName("card")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        preview_layout.setSpacing(SPACING["md"])
        preview_layout.addWidget(self._section_label("预览区域"))
        for line in [
            "BioMedPilot 生信分析报告草稿",
            "项目：Lung Cancer Study · TCGA-LUAD",
            "已包含：研究问题、数据集信息、样本分组、差异分析结果、图表、方法草稿",
            "Word/PDF 导出 Requires setup，当前仅展示报告结构预览。",
        ]:
            preview_layout.addWidget(self._muted(line))
        preview_layout.addWidget(self._empty_state_card("No Report", "生成报告前，这里仅展示报告结构和内容范围。", "no_report"))
        preview_layout.addStretch(1)
        middle.addWidget(preview, 2)
        layout.addLayout(middle, 1)

        actions = QHBoxLayout()
        for text, name, enabled in [
            ("生成报告", "primaryButton", True),
            ("预览报告", "secondaryButton", True),
            ("导出 Word", "secondaryButton", False),
            ("导出 PDF", "secondaryButton", False),
            ("导出图表包", "secondaryButton", False),
        ]:
            button = QPushButton(text)
            button.setObjectName(name)
            button.setEnabled(enabled)
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
        status = QLabel("导出 Word / PDF / 图表包 Coming soon；请先使用预览报告核对内容范围。")
        status.setObjectName("friendlyStatusLabel")
        status.setWordWrap(True)
        layout.addWidget(status)
        return page

    def _build_tasks_page(self, item: NavigationItem) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])
        layout.addWidget(self._page_header(item.title, "查看分析任务进度、结果入口和需要用户处理的问题。"))

        tabs = QTabWidget()
        tabs.setObjectName("taskStatusTabs")
        for title in ["Running", "Completed", "Failed", "All"]:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.setContentsMargins(SPACING["sm"], SPACING["sm"], SPACING["sm"], SPACING["sm"])
            tab_layout.addWidget(self._muted(f"{title} tasks"))
            tabs.addTab(tab, title)
        layout.addWidget(tabs)

        body = QHBoxLayout()
        body.setSpacing(SPACING["md"])
        table_card = QFrame()
        table_card.setObjectName("card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        table_layout.setSpacing(SPACING["md"])
        table_layout.addWidget(self._section_label("任务表"))
        task_table = self._table(
            "taskCenterTable",
            ["任务名称", "项目", "类型", "进度", "状态", "更新时间", "操作"],
            [
                ("差异表达分析", "Lung Cancer Study", "差异分析", "100%", "Completed", "2024-05-20 13:58", "打开结果"),
                ("富集分析", "Lung Cancer Study", "富集分析", "45%", "Running", "2024-05-20 14:20", "查看"),
                ("样本分组检查", "Lung Cancer Study", "样本分组", "-", "Needs Attention", "2024-05-20 13:40", "修复"),
                ("报告生成", "Lung Cancer Study", "报告导出", "-", "Waiting", "2024-05-19 18:02", "查看"),
                ("生存分析准备", "Lung Cancer Study", "生存分析", "-", "Failed", "2024-05-18 16:15", "查看原因"),
            ],
        )
        table_layout.addWidget(task_table, 1)
        body.addWidget(table_card, 2)

        details = QFrame()
        details.setObjectName("card")
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        details_layout.setSpacing(SPACING["md"])
        details_layout.addWidget(self._section_label("任务详情面板"))
        for line in [
            "任务名称：样本分组检查",
            "项目：Lung Cancer Study",
            "状态：Needs Attention",
            "最近更新：2024-05-20 13:40",
            "说明：样本分组信息不完整。请进入样本分组页面，为所有样本指定对照组或病例组。",
        ]:
            details_layout.addWidget(self._muted(line))
        body.addWidget(details)
        layout.addLayout(body, 1)

        error = QFrame()
        error.setObjectName("card")
        error_layout = QVBoxLayout(error)
        error_layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        error_layout.setSpacing(SPACING["sm"])
        error_layout.addWidget(self._section_label("用户友好错误区"))
        for line in [
            "发生了什么：样本分组信息缺失，无法运行差异表达分析。",
            "为什么不能继续：差异分析需要明确的对照组和病例组。",
            "用户应该去哪里修复：请先进入样本分组页面，为样本指定对照组和病例组。",
        ]:
            error_layout.addWidget(self._muted(line))
        fix = QPushButton("前往样本分组")
        fix.setObjectName("secondaryButton")
        fix.clicked.connect(lambda: self.select_navigation_item("sample-groups"))
        error_layout.addWidget(fix, alignment=Qt.AlignLeft)

        technical_toggle = QToolButton()
        technical_toggle.setObjectName("technicalDetailsToggle")
        technical_toggle.setText("Technical Details")
        technical_toggle.setCheckable(True)
        technical_toggle.setChecked(False)
        technical_toggle.setToolButtonStyle(Qt.ToolButtonTextOnly)
        error_layout.addWidget(technical_toggle)
        technical_details = QFrame()
        technical_details.setObjectName("technicalDetailsFrame")
        technical_details.setVisible(False)
        technical_layout = QVBoxLayout(technical_details)
        technical_layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
        technical_layout.addWidget(self._muted("任务代码：GROUPING_REQUIRED"))
        technical_layout.addWidget(self._muted("建议操作：确认 final_group 字段后重新运行。"))
        technical_toggle.toggled.connect(technical_details.setVisible)
        error_layout.addWidget(technical_details)
        layout.addWidget(error)
        return page

    def _page_header(self, title: str, description: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["lg"])
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        description_label = QLabel(description)
        description_label.setObjectName("mutedLabel")
        description_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        return frame

    def _list_card(self, title: str, lines: list[str]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["sm"])
        layout.addWidget(self._section_label(title))
        for line in lines:
            layout.addWidget(self._muted(line))
        layout.addStretch(1)
        return frame

    def _empty_state_card(self, title: str, message: str, icon_key: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("emptyStateCard")
        frame.setMinimumHeight(132)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        layout.setSpacing(SPACING["xs"])
        icon = QLabel()
        icon.setObjectName("emptyStateIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(IconFactory.empty_state_icon(icon_key).pixmap(IconFactory.icon_size("empty")))
        icon.setFixedSize(88, 72)
        title_label = QLabel(title)
        title_label.setObjectName("emptyStateTitle")
        title_label.setAlignment(Qt.AlignCenter)
        message_label = QLabel(message)
        message_label.setObjectName("mutedLabel")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon, alignment=Qt.AlignCenter)
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        return frame

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-weight: 700; background: transparent;")
        return label

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-weight: 600; background: transparent;")
        return label

    def _muted(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("mutedLabel")
        label.setWordWrap(True)
        return label

    def _summary_card(self, title: str, lines: list[str]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("statCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        layout.setSpacing(SPACING["xs"])
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 700; background: transparent;")
        layout.addWidget(title_label)
        for line in lines:
            label = QLabel(line)
            label.setObjectName("mutedLabel")
            layout.addWidget(label)
        layout.addStretch(1)
        return frame

    def _table(self, object_name: str, headers: list[str], rows: list[tuple[str, ...]]) -> QTableWidget:
        table = QTableWidget(len(rows), len(headers))
        table.setObjectName(object_name)
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                table.setItem(row_index, col_index, QTableWidgetItem(value))
        return table

    def _deg_table_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])
        title = QLabel("DEG table preview")
        title.setStyleSheet("font-weight: 700; background: transparent;")
        table = QTableWidget(5, 4)
        table.setObjectName("degTablePreview")
        table.setHorizontalHeaderLabels(["Gene", "log2FC", "FDR", "Regulation"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        rows = [
            ("EGFR", "2.41", "0.0008", "Up"),
            ("MKI67", "1.86", "0.0031", "Up"),
            ("ALDH2", "-1.53", "0.0074", "Down"),
            ("SFTPC", "-2.08", "0.0012", "Down"),
            ("MUC1", "1.21", "0.0210", "Up"),
        ]
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                table.setItem(row_index, col_index, QTableWidgetItem(value))
        layout.addWidget(title)
        layout.addWidget(table, 1)
        return frame
