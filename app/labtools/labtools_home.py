from __future__ import annotations

try:
    from PySide6.QtCore import Signal, Qt
    from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

    from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    class LabToolsHomeWidget(QWidget):
        calculators_requested = Signal()
        reagents_requested = Signal()
        image_quant_requested = Signal()
        templates_requested = Signal()

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
            subtitle = QLabel("基础实验计算与记录入口。")
            subtitle.setObjectName("labToolsSubtitle")
            root.addWidget(title)
            root.addWidget(subtitle)

            grid = QGridLayout()
            grid.setSpacing(SPACING["md"])
            grid.addWidget(
                self._entry_card(
                    "实验计算器",
                    "浓度、稀释、配制计算",
                    "可用",
                    "进入实验计算器",
                    self.calculators_requested.emit,
                    object_name="labToolsCalculatorEntry",
                ),
                0,
                0,
            )
            grid.addWidget(
                self._entry_card(
                    "试剂与配方",
                    "本地常用配方与体积缩放",
                    "可用",
                    "进入试剂与配方",
                    self.reagents_requested.emit,
                    object_name="labToolsRecipeEntry",
                ),
                0,
                1,
            )
            grid.addWidget(
                self._entry_card(
                    "图像定量",
                    "图片记录与任务草稿框架",
                    "可用",
                    "进入图像定量",
                    self.image_quant_requested.emit,
                    object_name="labToolsImageEntry",
                ),
                1,
                0,
            )
            grid.addWidget(self._entry_card("实验模板", "开发中", "开发中", "查看状态", self.templates_requested.emit), 1, 1)
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
            button.setObjectName("primaryButton" if status == "可用" else "secondaryButton")
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
            QFrame#labToolsCalculatorEntry, QFrame#labToolsRecipeEntry, QFrame#labToolsImageEntry, QFrame#labToolsPendingEntry {{
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
