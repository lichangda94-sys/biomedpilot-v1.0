from __future__ import annotations

try:
    from PySide6.QtCore import Signal, Qt
    from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

    from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    class LabToolsHomeWidget(QWidget):
        general_calculators_requested = Signal()
        reagent_records_requested = Signal()
        cell_experiments_requested = Signal()
        western_blot_requested = Signal()
        pcr_qpcr_requested = Signal()
        elisa_absorbance_requested = Signal()

        # Backward-compatible aliases for older UI tests and callers.
        calculators_requested = general_calculators_requested
        reagents_requested = reagent_records_requested
        image_quant_requested = cell_experiments_requested
        templates_requested = reagent_records_requested

        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsHomePage")
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
            subtitle = QLabel("按实验场景组织的 LabTools 模块入口；具体工具开发前需先确认使用逻辑。")
            subtitle.setObjectName("labToolsSubtitle")
            root.addWidget(title)
            root.addWidget(subtitle)

            grid = QGridLayout()
            grid.setSpacing(SPACING["md"])
            grid.addWidget(
                self._entry_card(
                    "通用计算器",
                    "用于浓度、分子量、质量、体积、稀释、称量和后续 pH/酸碱度等通用试剂计算。",
                    "已开放 / 待确认使用逻辑",
                    "进入通用计算器",
                    self.general_calculators_requested.emit,
                    object_name="labToolsGeneralCalculatorEntry",
                ),
                0,
                0,
            )
            grid.addWidget(
                self._entry_card(
                    "试剂与实验记录",
                    "用于本地 recipe 草稿、实验记录草稿、模板保存和 JSON 导入导出；不等同于完整 ELN。",
                    "已开放 / 待确认使用逻辑",
                    "进入试剂与实验记录",
                    self.reagent_records_requested.emit,
                    object_name="labToolsReagentRecordsEntry",
                ),
                0,
                1,
            )
            grid.addWidget(
                self._entry_card(
                    "细胞实验",
                    "用于细胞接种、活率、Transwell、wound healing、增殖率、台盼蓝、Alamar Blue 等细胞实验工具。",
                    "规划中 / 待确认使用逻辑 / 暂未开放",
                    "查看细胞实验规划",
                    self.cell_experiments_requested.emit,
                    object_name="labToolsCellExperimentEntry",
                ),
                1,
                0,
            )
            grid.addWidget(
                self._entry_card(
                    "Western Blot",
                    "用于蛋白样品准备、蛋白浓度测定入口、上样体系、SDS-PAGE 配胶、电泳/转膜参数、抗体孵育流程和后续灰度分析。",
                    "规划中 / 待确认使用逻辑 / 暂未开放",
                    "查看 Western Blot 规划",
                    self.western_blot_requested.emit,
                    object_name="labToolsWesternBlotEntry",
                ),
                1,
                1,
            )
            grid.addWidget(
                self._entry_card(
                    "PCR / qPCR",
                    "用于 PCR/qPCR 体系计算、运行参数、plate layout、Ct / ΔCt / ΔΔCt 结果分析。",
                    "规划中 / 待确认使用逻辑 / 暂未开放",
                    "查看 PCR / qPCR 规划",
                    self.pcr_qpcr_requested.emit,
                    object_name="labToolsPcrQpcrEntry",
                ),
                2,
                0,
            )
            grid.addWidget(
                self._entry_card(
                    "ELISA / 吸光度与标准曲线",
                    "用于 OD 值、标准曲线、BCA、Bradford、NanoDrop、ELISA 样本浓度反推等。",
                    "规划中 / 待确认使用逻辑 / 暂未开放",
                    "查看 ELISA / 吸光度规划",
                    self.elisa_absorbance_requested.emit,
                    object_name="labToolsElisaAbsorbanceEntry",
                ),
                2,
                1,
            )
            root.addLayout(grid)
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
            active_statuses = {"可用", "本地辅助", "本地草稿", "manual-review MVP", "草稿中心", "已开放 / 待确认使用逻辑"}
            button.setObjectName("primaryButton" if status in active_statuses else "secondaryButton")
            button.clicked.connect(callback)
            layout.addWidget(status_label, alignment=Qt.AlignLeft)
            layout.addWidget(title_label)
            layout.addWidget(description_label)
            layout.addStretch(1)
            layout.addWidget(button, alignment=Qt.AlignLeft)
            return frame

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
            QFrame#labToolsGeneralCalculatorEntry, QFrame#labToolsReagentRecordsEntry, QFrame#labToolsCellExperimentEntry, QFrame#labToolsWesternBlotEntry, QFrame#labToolsPcrQpcrEntry, QFrame#labToolsElisaAbsorbanceEntry, QFrame#labToolsPendingEntry {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["lg"]}px;
                min-height: 150px;
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
            """

else:  # pragma: no cover

    class LabToolsHomeWidget:  # type: ignore[no-redef]
        pass
