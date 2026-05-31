from __future__ import annotations

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

    from app.app_identity import load_labtools_pixmap
    from app.labtools.labtools_tool_registry import LabToolsPrimaryEntry, labtools_primary_entries
    from app.shared.semantic_keys import ModuleKey, PageKey
    from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING, button_stylesheet, status_chip_stylesheet
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    class LabToolsHomeWidget(QWidget):
        primary_requested = Signal(str)

        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsHomePage")
            self.setProperty("pageKey", "home")
            self.setProperty("semanticKey", PageKey.LABTOOLS_HOME.value)
            self.setStyleSheet(self._stylesheet())
            self._build_ui()

        def _build_ui(self) -> None:
            outer = QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)

            scroll = QScrollArea()
            scroll.setObjectName("labtoolsShellPage")
            scroll.setProperty("usabilityRole", "scrollable_shell_page")
            scroll.setAccessibleName("LabTools shell page")
            scroll.setWidgetResizable(True)

            content = QFrame()
            content.setObjectName("labtoolsShellContent")
            root = QVBoxLayout(content)
            root.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            root.setSpacing(SPACING["lg"])

            title = QLabel("实验工具 / LabTools")
            title.setObjectName("labtoolsShellTitle")
            title.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
            title.setProperty("semanticKey", PageKey.LABTOOLS_HOME.value)
            subtitle = QLabel("通用计算、试剂配制与实验流程工具集合，为生物医学实验提供可靠的计算与规划支持。")
            subtitle.setObjectName("labtoolsShellSubtitle")
            subtitle.setWordWrap(True)
            preview = QLabel("Developer Preview / 本地测试版")
            preview.setObjectName("uiStatusChip")
            preview.setProperty("statusKey", "developer_preview")
            preview.setStyleSheet(status_chip_stylesheet("developer_preview"))
            notice = QLabel("实验计算结果需由用户复核后用于台面操作。")
            notice.setObjectName("labtoolsReviewNotice")
            notice.setWordWrap(True)

            root.addWidget(title)
            root.addWidget(subtitle)
            root.addWidget(preview, alignment=Qt.AlignLeft)

            grid = QGridLayout()
            grid.setSpacing(SPACING["md"])
            for index, entry in enumerate(labtools_primary_entries()):
                grid.addWidget(self._primary_card(entry), 0, index)
            root.addLayout(grid)
            root.addWidget(notice)
            root.addWidget(self._quick_access_card())
            root.addStretch(1)

            scroll.setWidget(content)
            outer.addWidget(scroll)

        def _primary_card(self, entry: LabToolsPrimaryEntry) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labtoolsPrimaryEntryCard")
            frame.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
            frame.setProperty("pageKey", entry.page_key)
            frame.setProperty("semanticKey", entry.semantic_key)
            frame.setProperty("sourceCommits", ",".join(entry.source_commits))
            frame.setCursor(Qt.PointingHandCursor)

            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            layout.setSpacing(SPACING["md"])

            icon = QLabel()
            icon.setObjectName("labtoolsPrimaryEntryIcon")
            pixmap = load_labtools_pixmap(entry.semantic_key, 72)
            if not pixmap.isNull():
                icon.setPixmap(pixmap)
                icon.setFixedSize(76, 76)
                icon.setScaledContents(False)

            chip = QLabel(entry.status)
            chip.setObjectName("uiStatusChip")
            chip.setProperty("statusKey", entry.status_key)
            chip.setStyleSheet(status_chip_stylesheet(entry.status_key))

            title = QLabel(entry.title)
            title.setObjectName("labtoolsPrimaryEntryTitle")
            title.setProperty("pageKey", entry.page_key)
            title.setProperty("semanticKey", entry.semantic_key)

            english = QLabel(entry.english_title)
            english.setObjectName("labtoolsPrimaryEntryEnglishTitle")

            description = QLabel(entry.description)
            description.setObjectName("labtoolsEntryDetail")
            description.setWordWrap(True)

            details = QLabel("\n".join(f"- {item}" for item in entry.details))
            details.setObjectName("labtoolsEntryDetail")
            details.setWordWrap(True)

            button = QPushButton(entry.button_text)
            button.setObjectName("labtoolsEntryButton")
            button.setProperty("moduleKey", ModuleKey.LABTOOLS.value)
            button.setProperty("pageKey", entry.page_key)
            button.setProperty("semanticKey", entry.semantic_key)
            button.setProperty("toolId", entry.tool_id)
            button.setStyleSheet(button_stylesheet("primary_action" if entry.tool_id == "experiment_modules" else "secondary"))
            button.clicked.connect(lambda _checked=False, item=entry: self.primary_requested.emit(item.tool_id))

            layout.addWidget(icon, alignment=Qt.AlignLeft)
            layout.addWidget(chip, alignment=Qt.AlignLeft)
            layout.addWidget(title)
            layout.addWidget(english)
            layout.addWidget(description)
            layout.addWidget(details)
            layout.addStretch(1)
            layout.addWidget(button)
            return frame

        def _quick_access_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labtoolsQuickAccessCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            layout.setSpacing(SPACING["md"])
            title = QLabel("快速入口")
            title.setObjectName("labtoolsQuickAccessTitle")
            layout.addWidget(title)
            grid = QGridLayout()
            grid.setSpacing(SPACING["sm"])
            for index, key in enumerate(("使用指南", "常见问题", "意见反馈", "最近使用")):
                button = QPushButton(key)
                button.setObjectName("quickAccessButton")
                button.setProperty("quickAccessKey", key)
                button.setEnabled(False)
                button.setProperty("disabledReason", "LabTools quick access center is planned for UI-SHELL-CENTERS-C1.")
                button.setToolTip(button.property("disabledReason"))
                grid.addWidget(button, 0, index)
            layout.addLayout(grid)
            return frame

        def _stylesheet(self) -> str:
            return f"""
            QWidget#labToolsHomePage, QFrame#labtoolsShellContent {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QScrollArea#labtoolsShellPage {{
                border: 0;
                background: {COLORS["background"]};
            }}
            QLabel#labtoolsShellTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 800;
            }}
            QLabel#labtoolsShellSubtitle,
            QLabel#labtoolsPrimaryEntryEnglishTitle,
            QLabel#labtoolsEntryDetail {{
                color: {COLORS["muted"]};
            }}
            QFrame#labtoolsPrimaryEntryCard {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["md"]}px;
                min-height: 360px;
            }}
            QLabel#labtoolsPrimaryEntryTitle {{
                color: {COLORS["bio"]};
                font-size: 20px;
                font-weight: 780;
            }}
            QLabel#labtoolsReviewNotice {{
                color: {COLORS["text_secondary"]};
                background: {COLORS["warning_soft"]};
                border: 1px solid {COLORS["warning_border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 9px 11px;
            }}
            QFrame#labtoolsQuickAccessCard {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["md"]}px;
            }}
            QLabel#labtoolsQuickAccessTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["card_title"]}px;
                font-weight: 760;
            }}
            QPushButton#quickAccessButton:disabled {{
                color: {COLORS["muted"]};
                background: {COLORS["surface_muted"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 12px;
            }}
            """

else:  # pragma: no cover

    class LabToolsHomeWidget:  # type: ignore[no-redef]
        pass
