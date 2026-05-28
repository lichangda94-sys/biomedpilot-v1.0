from __future__ import annotations

try:
    from PySide6.QtCore import Signal, Qt
    from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

    from app.labtools.labtools_tool_registry import LabToolsTool, labtools_tool_registry
    from app.shared.local_engines import ImageJFijiBridge
    from app.shared.semantic_keys import ModuleKey, PageKey
    from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    class LabToolsHomeWidget(QWidget):
        tool_requested = Signal(str)
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
            subtitle = QLabel("本地实验计算、实验记录辅助与结果整理工具。")
            subtitle.setObjectName("labToolsSubtitle")
            root.addWidget(title)
            root.addWidget(subtitle)

            grid = QGridLayout()
            grid.setSpacing(SPACING["md"])
            for index, tool in enumerate(labtools_tool_registry()):
                grid.addWidget(self._entry_card(tool), index // 2, index % 2)
            root.addLayout(grid)
            root.addStretch(1)
            scroll.setWidget(content)
            outer.addWidget(scroll)

        def _entry_card(
            self,
            tool: LabToolsTool,
        ) -> QFrame:
            frame = QFrame()
            frame.setObjectName(tool.object_name)
            frame.setCursor(Qt.PointingHandCursor)
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            layout.setSpacing(SPACING["md"])
            title_label = QLabel(tool.chinese_name)
            title_label.setObjectName("labToolsCardTitle")
            status = self._display_status(tool)
            status_label = QLabel(status)
            status_label.setObjectName("labToolsStatusLabel")
            description_label = QLabel(tool.description)
            description_label.setObjectName("labToolsDescription")
            description_label.setWordWrap(True)
            boundary_label = QLabel(tool.boundary_statement)
            boundary_label.setObjectName("labToolsDescription")
            boundary_label.setWordWrap(True)
            meta_label = QLabel(f"{tool.english_name} / {tool.category}")
            meta_label.setObjectName("labToolsMeta")
            meta_label.setWordWrap(True)
            button = QPushButton(tool.button_text)
            page_key, semantic_key = self._route_metadata(tool)
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
            entry_style = "primary" if status in active_statuses else "secondary"
            button.setObjectName("primaryButton" if entry_style == "primary" else "secondaryButton")
            button.setProperty("entryStyle", entry_style)
            button.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
            button.setProperty("pageKey", page_key)
            button.setProperty("semanticKey", semantic_key)
            button.setProperty("toolId", tool.tool_id)
            button.setProperty("statusKey", tool.status)
            button.clicked.connect(lambda _checked=False, item=tool: self._emit_tool(item))
            layout.addWidget(status_label, alignment=Qt.AlignLeft)
            layout.addWidget(title_label)
            layout.addWidget(meta_label)
            layout.addWidget(description_label)
            layout.addWidget(boundary_label)
            layout.addStretch(1)
            layout.addWidget(button, alignment=Qt.AlignLeft)
            return frame

        def _display_status(self, tool: LabToolsTool) -> str:
            return tool.status

        def _route_metadata(self, tool: LabToolsTool) -> tuple[str, str]:
            semantic_by_tool = {
                "general_reagent_calculator": PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
                "western_blot": PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
                "pcr_qpcr": PageKey.LABTOOLS_NUCLEIC_ACID_EXPERIMENTS.value,
                "elisa_absorbance": PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
                "cell_experiments": PageKey.LABTOOLS_CELL_EXPERIMENTS.value,
            }
            return tool.entry_page, semantic_by_tool.get(tool.tool_id, PageKey.LABTOOLS_HOME.value)

        def _emit_tool(self, tool: LabToolsTool) -> None:
            self.tool_requested.emit(tool.tool_id)
            if tool.tool_id == "general_reagent_calculator":
                self.general_calculators_requested.emit()
            elif tool.tool_id == "western_blot":
                self.western_blot_requested.emit()
            elif tool.tool_id == "pcr_qpcr":
                self.pcr_qpcr_requested.emit()
            elif tool.tool_id == "elisa_absorbance":
                self.elisa_absorbance_requested.emit()
            elif tool.tool_id == "cell_experiments":
                self.cell_experiments_requested.emit()

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
                border-radius: {RADIUS["md"]}px;
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
            QLabel#labToolsMeta {{
                color: {COLORS["muted"]};
                font-size: {FONT_SIZE["secondary"]}px;
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
