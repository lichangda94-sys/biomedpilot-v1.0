from __future__ import annotations

try:
    from PySide6.QtCore import Signal, Qt
    from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

    from app.labtools.imagej_bridge import (
        ENGINE_STATUS_AVAILABLE,
        ENGINE_STATUS_CONFIGURED_UNVERIFIED,
        ENGINE_STATUS_FAILED,
        imagej_fiji_display_path,
        read_shared_imagej_fiji_status,
    )
    from app.shared.local_engines import ImageJFijiBridge
    from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    class LabToolsHomeWidget(QWidget):
        general_calculators_requested = Signal()
        reagent_records_requested = Signal()
        imagej_fiji_requested = Signal()
        cell_experiments_requested = Signal()
        western_blot_requested = Signal()
        pcr_qpcr_requested = Signal()
        elisa_absorbance_requested = Signal()

        # Backward-compatible aliases for older UI tests and callers.
        calculators_requested = general_calculators_requested
        reagents_requested = reagent_records_requested
        image_quant_requested = imagej_fiji_requested
        templates_requested = reagent_records_requested

        def __init__(self, *, imagej_bridge: ImageJFijiBridge | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsHomePage")
            self._imagej_bridge = imagej_bridge
            self.setStyleSheet(self._stylesheet())
            self._build_ui()

        def _build_ui(self) -> None:
            outer = QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setObjectName("labToolsHomeScroll")
            content = QWidget()
            content.setObjectName("labToolsHomeContent")
            root = QVBoxLayout(content)
            root.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            root.setSpacing(SPACING["lg"])

            title = QLabel("LabTools / 实验工具")
            title.setObjectName("labToolsTitle")
            subtitle = QLabel("本地实验计算、实验记录辅助、图像 workflow 配置与结果整理工具。")
            subtitle.setObjectName("labToolsSubtitle")
            root.addWidget(title)
            root.addWidget(subtitle)

            grid = QGridLayout()
            grid.setSpacing(SPACING["md"])
            grid.addWidget(
                self._entry_card(
                    "通用试剂计算器",
                    "浓度、质量、体积、摩尔量、稀释等基础实验计算。",
                    "available / 已接入",
                    "打开计算器",
                    self.general_calculators_requested.emit,
                    object_name="labToolsGeneralCalculatorEntry",
                ),
                0,
                0,
            )
            grid.addWidget(
                self._entry_card(
                    "ImageJ/Fiji 本地引擎",
                    "用于图像 workflow 的本地 ImageJ/Fiji 检测与路径配置。",
                    self._imagej_status_badge(),
                    "配置 ImageJ/Fiji",
                    self.imagej_fiji_requested.emit,
                    object_name="labToolsImageJFijiEntry",
                ),
                0,
                1,
            )
            grid.addWidget(
                self._entry_card(
                    "Western Blot 工具",
                    "WB 上样计算、条带定量 workflow 占位。",
                    "planned / 未启用",
                    "规划中",
                    self.western_blot_requested.emit,
                    object_name="labToolsWesternBlotEntry",
                ),
                1,
                0,
            )
            grid.addWidget(
                self._entry_card(
                    "PCR/qPCR 工具",
                    "PCR mix、qPCR 结果整理 workflow 占位。",
                    "planned / 未启用",
                    "规划中",
                    self.pcr_qpcr_requested.emit,
                    object_name="labToolsPcrQpcrEntry",
                ),
                1,
                1,
            )
            grid.addWidget(
                self._entry_card(
                    "ELISA/吸光度工具",
                    "标准曲线、OD 数据整理 workflow 占位。",
                    "planned / 未启用",
                    "规划中",
                    self.elisa_absorbance_requested.emit,
                    object_name="labToolsElisaAbsorbanceEntry",
                ),
                2,
                0,
            )
            grid.addWidget(
                self._entry_card(
                    "细胞实验工具",
                    "细胞接种、处理分组、实验记录 workflow 占位。",
                    "planned / 未启用",
                    "规划中",
                    self.cell_experiments_requested.emit,
                    object_name="labToolsCellExperimentEntry",
                ),
                2,
                1,
            )
            root.addLayout(grid)
            root.addWidget(
                self._notice_card(
                    "图像能力边界",
                    "当前阶段仅支持 ImageJ/Fiji 本机引擎检测和 manual-review workflow 准备；未启用 WB/gel 真实分析、agarose gel、自动 ROI、细胞计数、条带识别、pathology workflow 或生产级真实图像算法。所有图像相关结果都需要人工复核。",
                    "labToolsImageBoundaryNotice",
                )
            )
            root.addWidget(self._engine_summary_card())
            root.addStretch(1)
            scroll.setWidget(content)
            outer.addWidget(scroll)

        def _entry_card(
            self,
            title: str,
            description: str,
            status: str,
            button_text: str,
            callback,
            *,
            object_name: str = "labToolsPendingEntry",
        ) -> QFrame:
            frame = QFrame()
            frame.setObjectName(object_name)
            frame.setCursor(Qt.PointingHandCursor)
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            layout.setSpacing(SPACING["md"])
            title_label = QLabel(title)
            title_label.setObjectName("labToolsCardTitle")
            status_label = QLabel(status)
            status_label.setObjectName("labToolsStatusLabel")
            description_label = QLabel(description)
            description_label.setObjectName("labToolsDescription")
            description_label.setWordWrap(True)
            button = QPushButton(button_text)
            active_statuses = {
                "可用",
                "本地辅助",
                "本地草稿",
                "manual-review MVP",
                "草稿中心",
                "已开放 / 待确认使用逻辑",
                "available / 已接入",
                "available / configured",
                "configured / 待验证",
                "missing / manual-review",
                "fallback/manual-review",
            }
            button.setObjectName("primaryButton" if status in active_statuses else "secondaryButton")
            if status == "planned / 未启用":
                button.setEnabled(False)
            button.clicked.connect(callback)
            layout.addWidget(status_label, alignment=Qt.AlignLeft)
            layout.addWidget(title_label)
            layout.addWidget(description_label)
            layout.addStretch(1)
            layout.addWidget(button, alignment=Qt.AlignLeft)
            return frame

        def _notice_card(self, title: str, body: str, object_name: str) -> QFrame:
            frame = QFrame()
            frame.setObjectName(object_name)
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            layout.setSpacing(SPACING["sm"])
            title_label = QLabel(title)
            title_label.setObjectName("labToolsNoticeTitle")
            body_label = QLabel(body)
            body_label.setObjectName("labToolsNoticeBody")
            body_label.setWordWrap(True)
            layout.addWidget(title_label)
            layout.addWidget(body_label)
            return frame

        def _engine_summary_card(self) -> QFrame:
            status = read_shared_imagej_fiji_status(self._imagej_bridge)
            frame = QFrame()
            frame.setObjectName("labToolsImageJFijiSummary")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            layout.setSpacing(SPACING["sm"])
            title = QLabel("本地引擎状态摘要")
            title.setObjectName("labToolsNoticeTitle")
            details = QLabel(
                "\n".join(
                    (
                        f"ImageJ/Fiji 当前检测状态：{self._imagej_status_badge()}",
                        f"路径：{imagej_fiji_display_path(status.configured_path_or_endpoint)}",
                        f"版本：{status.detected_version or '未知'}",
                        f"是否已验证：{'是' if status.status == ENGINE_STATUS_AVAILABLE else '否'}",
                        status.last_error or "错误摘要：无",
                    )
                )
            )
            details.setObjectName("labToolsNoticeBody")
            details.setWordWrap(True)
            button = QPushButton("配置 ImageJ/Fiji")
            button.setObjectName("secondaryButton")
            button.clicked.connect(self.imagej_fiji_requested.emit)
            layout.addWidget(title)
            layout.addWidget(details)
            layout.addWidget(button, alignment=Qt.AlignLeft)
            return frame

        def _imagej_status_badge(self) -> str:
            status = read_shared_imagej_fiji_status(self._imagej_bridge).status
            if status == ENGINE_STATUS_AVAILABLE:
                return "available / configured"
            if status == ENGINE_STATUS_CONFIGURED_UNVERIFIED:
                return "configured / 待验证"
            if status == ENGINE_STATUS_FAILED:
                return "fallback/manual-review"
            return "missing / manual-review"

        def _stylesheet(self) -> str:
            return f"""
            QWidget#labToolsHomePage, QWidget#labToolsHomeContent {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QScrollArea#labToolsHomeScroll {{
                border: 0;
                background: {COLORS["background"]};
            }}
            QFrame#labToolsGeneralCalculatorEntry, QFrame#labToolsImageJFijiEntry, QFrame#labToolsReagentRecordsEntry, QFrame#labToolsCellExperimentEntry, QFrame#labToolsWesternBlotEntry, QFrame#labToolsPcrQpcrEntry, QFrame#labToolsElisaAbsorbanceEntry, QFrame#labToolsPendingEntry {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["md"]}px;
                min-height: 150px;
            }}
            QFrame#labToolsImageBoundaryNotice {{
                background: #FFF4F2;
                border: 1px solid #F3B4AA;
                border-radius: {RADIUS["md"]}px;
            }}
            QFrame#labToolsImageJFijiSummary {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["md"]}px;
            }}
            QLabel#labToolsTitle {{
                color: {COLORS["bio"]};
                font-size: 26px;
                font-weight: 800;
            }}
            QLabel#labToolsSubtitle, QLabel#labToolsDescription {{
                color: {COLORS["muted"]};
            }}
            QLabel#labToolsCardTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["card_title"]}px;
                font-weight: 760;
            }}
            QLabel#labToolsStatusLabel {{
                color: #0E6F66;
                background: #E7F7F5;
                border: 1px solid #BCE7E2;
                border-radius: {RADIUS["sm"]}px;
                padding: 4px 8px;
                font-weight: 700;
            }}
            QLabel#labToolsNoticeTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["card_title"]}px;
                font-weight: 760;
            }}
            QLabel#labToolsNoticeBody {{
                color: {COLORS["text"]};
            }}
            QPushButton#primaryButton {{
                color: #FFFFFF;
                background: {COLORS["bio"]};
                border: 1px solid {COLORS["bio"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 12px;
                font-weight: 700;
            }}
            QPushButton#secondaryButton {{
                color: {COLORS["bio"]};
                background: {COLORS["bio_soft"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 12px;
                font-weight: 600;
            }}
            QPushButton:disabled {{
                color: {COLORS["muted"]};
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
            }}
            """

else:  # pragma: no cover

    class LabToolsHomeWidget:  # type: ignore[no-redef]
        pass
