from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from html import escape

from app.ui_style_tokens import (
    BUTTON_TOKENS,
    CONTROL_HEIGHT,
    COLORS,
    FONT_SIZE,
    RADIUS,
    SPACING,
    UIStatusKey,
    button_stylesheet,
    card_stylesheet,
    get_status_token,
    status_chip_stylesheet,
)
from app.shared.semantic_keys import AnalysisStatusKey, FeatureStatusKey, ReportStatusKey, ResourceStatusKey
from app.app_identity import APP_ICON_PNG_PATH, MODULE_ICON_PATHS, STATUS_ICON_PATHS, load_app_icon, load_module_icon, load_status_pixmap, load_ui02_module_selection_icon


SEMANTIC_STATE_KEYS: tuple[str, ...] = (
    "available",
    "disabled",
    "blocked",
    "planned",
    "testing",
    "shell_only",
    "preflight_only",
    "draft",
    "adapter_needed",
    "report_disabled",
    "export_disabled",
)


@dataclass(frozen=True)
class AppSidebarItem:
    key: str
    label: str
    semantic_key: str
    icon_key: str = ""
    usability_role: str = "primary_navigation"
    tooltip: str = ""


STATUS_SEMANTIC_KEYS: dict[str, str] = {
    UIStatusKey.DEVELOPER_PREVIEW.value: FeatureStatusKey.DEVELOPER_PREVIEW.value,
    UIStatusKey.TESTING.value: FeatureStatusKey.TESTING.value,
    UIStatusKey.PLANNED.value: FeatureStatusKey.PLANNED.value,
    UIStatusKey.SHELL_ONLY.value: FeatureStatusKey.SHELL_ONLY.value,
    UIStatusKey.PREFLIGHT_ONLY.value: AnalysisStatusKey.PREFLIGHT_ONLY.value,
    UIStatusKey.BLOCKED.value: FeatureStatusKey.BLOCKED.value,
    UIStatusKey.DISABLED.value: FeatureStatusKey.BLOCKED.value,
    UIStatusKey.AVAILABLE.value: ResourceStatusKey.AVAILABLE.value,
    UIStatusKey.NOT_CONFIGURED.value: ResourceStatusKey.NOT_CONFIGURED.value,
    UIStatusKey.MISSING.value: ResourceStatusKey.NOT_CONFIGURED.value,
    UIStatusKey.FAILED.value: ResourceStatusKey.FAILED.value,
    UIStatusKey.DRAFT.value: ReportStatusKey.DRAFT.value,
    UIStatusKey.ADAPTER_NEEDED.value: ResourceStatusKey.NOT_CONFIGURED.value,
    UIStatusKey.REPORT_DISABLED.value: ReportStatusKey.DRAFT.value,
    UIStatusKey.EXPORT_DISABLED.value: FeatureStatusKey.BLOCKED.value,
    UIStatusKey.REPORT_READY.value: ReportStatusKey.REPORT_READY_FUTURE.value,
}

STATUS_TOOLTIPS: dict[str, str] = {
    FeatureStatusKey.TESTING.value: "Testing-level only; not a formal or production-ready capability.",
    FeatureStatusKey.PLANNED.value: "Planned only; not runnable and not currently available.",
    FeatureStatusKey.SHELL_ONLY.value: "UI shell only; no business implementation is implied.",
    FeatureStatusKey.DEVELOPER_PREVIEW.value: "Developer preview only; ordinary user production capability is not implied.",
    FeatureStatusKey.BLOCKED.value: "Blocked by missing input, resolver, dependency, or precondition; action remains unavailable.",
    ResourceStatusKey.AVAILABLE.value: "Detected resource available only; the icon does not install, configure, or enable a resource.",
    ResourceStatusKey.NOT_CONFIGURED.value: "Resource is not configured; install, update, or cloud setup remains user-triggered and gated.",
    ResourceStatusKey.FAILED.value: "Detection or resource check failed; this does not imply formal analysis failure.",
    AnalysisStatusKey.PREFLIGHT_ONLY.value: "Preflight-only analysis surface; no formal DEG, GSEA, survival, clinical, or report-ready result.",
    ReportStatusKey.DRAFT.value: "Draft report only; not report-ready and not a formal export package.",
}


def make_status_chip(
    label: str | None = None,
    *,
    status_key: str | UIStatusKey = UIStatusKey.NOT_CONFIGURED,
    semantic_state: str | None = None,
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel

    token = get_status_token(status_key)
    chip = QLabel(label or token.label)
    semantic_key = STATUS_SEMANTIC_KEYS.get(token.key, ResourceStatusKey.NOT_CONFIGURED.value)
    status_icon_source = STATUS_ICON_PATHS.get(semantic_key)
    pixmap = load_status_pixmap(semantic_key, 14)
    chip.setObjectName("uiStatusChip")
    chip.setProperty("uiPrimitive", "status_chip")
    chip.setProperty("statusKey", token.key)
    chip.setProperty("semanticKey", semantic_key)
    chip.setProperty("iconHint", token.icon_hint)
    chip.setProperty("statusLabel", label or token.label)
    chip.setProperty("statusIconSemanticKey", semantic_key)
    chip.setProperty("statusIconRole", "auxiliary_status_marker")
    chip.setProperty("statusIconFallback", pixmap.isNull())
    chip.setProperty("statusIconActivePilot", not pixmap.isNull())
    chip.setProperty("statusAvailableRequiresDetectedResource", semantic_key == ResourceStatusKey.AVAILABLE.value)
    _apply_semantic_state_properties(chip, semantic_state or token.key)
    chip.setToolTip(STATUS_TOOLTIPS.get(semantic_key, "Status marker; text label and semantic key remain authoritative."))
    if status_icon_source is not None:
        chip.setProperty("statusIconSource", str(status_icon_source))
    if not pixmap.isNull() and status_icon_source is not None:
        chip.setTextFormat(Qt.RichText)
        chip.setText(
            f'<img src="{status_icon_source.as_uri()}" width="14" height="14" style="vertical-align:middle;">'
            f'&nbsp;{escape(label or token.label)}'
        )
    chip.setAlignment(Qt.AlignCenter)
    chip.setWordWrap(False)
    chip.setStyleSheet(status_chip_stylesheet(token.key))
    return chip


def make_button(
    text: str,
    *,
    role: str = "secondary",
    size: str = "regular",
    semantic_state: str | None = None,
    action_key: str = "",
    disabled_reason: str = "",
    enabled: bool | None = None,
    formal_action_enabled: bool = False,
    file_write_allowed: bool = False,
):
    from PySide6.QtWidgets import QPushButton

    normalized_role = role if role in BUTTON_TOKENS else "secondary"
    button = QPushButton(text)
    button.setObjectName(_button_object_name(normalized_role))
    button.setProperty("uiPrimitive", "button")
    button.setProperty("buttonRole", normalized_role)
    button.setProperty("buttonSize", size)
    button.setProperty("actionKey", action_key)
    button.setProperty("disabledReason", disabled_reason)
    button.setProperty("formalActionEnabled", formal_action_enabled)
    button.setProperty("fileWriteAllowed", file_write_allowed)
    button.setProperty("reportGenerationAllowed", False)
    button.setProperty("exportAllowed", False)
    _apply_semantic_state_properties(button, semantic_state or ("disabled" if enabled is False else "available"))
    if enabled is not None:
        button.setEnabled(enabled)
    if disabled_reason:
        button.setToolTip(disabled_reason)
    button.setMinimumHeight(_button_height(size))
    button.setStyleSheet(button_stylesheet(normalized_role))
    return button


def make_action_button(
    text: str,
    *,
    role: str = "secondary",
    size: str = "regular",
    semantic_state: str = "available",
    action_key: str = "",
    disabled_reason: str = "",
    enabled: bool = True,
    formal_action_enabled: bool = False,
    file_write_allowed: bool = False,
):
    return make_button(
        text,
        role=role,
        size=size,
        semantic_state=semantic_state,
        action_key=action_key,
        disabled_reason=disabled_reason,
        enabled=enabled,
        formal_action_enabled=formal_action_enabled,
        file_write_allowed=file_write_allowed,
    )


def make_card(*, object_name: str = "uiCard", semantic_state: str = "available"):
    from PySide6.QtWidgets import QFrame

    card = QFrame()
    card.setObjectName(object_name)
    card.setProperty("uiPrimitive", "card")
    _apply_semantic_state_properties(card, semantic_state)
    card.setFrameShape(QFrame.StyledPanel)
    card.setStyleSheet(card_stylesheet())
    return card


def make_workbench_card(*, object_name: str = "uiWorkbenchCard", semantic_state: str = "available"):
    card = make_card(object_name=object_name, semantic_state=semantic_state)
    card.setProperty("uiPrimitive", "workbench_card")
    return card


def make_empty_state(
    title: str,
    body: str,
    *,
    action_text: str | None = None,
    empty_state_key: str | None = None,
    semantic_key: str | None = None,
    illustration_size: int = 72,
    semantic_state: str = "disabled",
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel, QVBoxLayout

    from app.app_identity import empty_state_image_key_for, load_empty_state_pixmap

    frame = make_card(object_name="uiEmptyState", semantic_state=semantic_state)
    frame.setProperty("uiPrimitive", "empty_state")
    resolved_empty_state_key = empty_state_image_key_for(empty_state_key, semantic_key)
    frame.setProperty("emptyStateKey", resolved_empty_state_key or "")
    frame.setProperty("emptyStateSemanticKey", semantic_key or "")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(8)

    if resolved_empty_state_key:
        illustration = QLabel()
        illustration.setObjectName("uiEmptyStateIllustration")
        illustration.setProperty("emptyStateKey", resolved_empty_state_key)
        illustration.setProperty("semanticKey", semantic_key or "")
        illustration.setAlignment(Qt.AlignCenter)
        pixmap = load_empty_state_pixmap(resolved_empty_state_key, semantic_key=semantic_key, size=illustration_size)
        illustration.setProperty("imageFallback", pixmap.isNull())
        if not pixmap.isNull():
            illustration.setPixmap(pixmap)
            illustration.setFixedHeight(max(illustration_size, 56))
            layout.addWidget(illustration)
    else:
        frame.setProperty("emptyStateImageFallback", True)

    title_label = QLabel(title)
    title_label.setObjectName("uiEmptyStateTitle")
    title_label.setWordWrap(True)
    title_label.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONT_SIZE['card_title']}px; font-weight: 750;")
    layout.addWidget(title_label)

    body_label = QLabel(body)
    body_label.setObjectName("uiEmptyStateBody")
    body_label.setWordWrap(True)
    body_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['body']}px;")
    layout.addWidget(body_label)

    if action_text:
        layout.addWidget(make_button(action_text, role="secondary", semantic_state=semantic_state))

    frame.setProperty("emptyStateImageFallback", frame.findChild(QLabel, "uiEmptyStateIllustration") is None)
    return frame


def make_page_shell(
    *,
    object_name: str = "uiPageShell",
    module_key: str = "",
    page_key: str = "",
    content_widgets: Sequence[object] = (),
    scrollable: bool = False,
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

    shell = QFrame()
    shell.setObjectName(object_name)
    shell.setProperty("uiPrimitive", "page_shell")
    shell.setProperty("moduleKey", module_key)
    shell.setProperty("pageKey", page_key)
    shell.setProperty("layoutPolishNoOverlap", True)
    shell.setFrameShape(QFrame.NoFrame)
    shell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    shell.setStyleSheet(
        f"""
        QFrame#{object_name} {{
            background: {COLORS["background"]};
            border: 0;
        }}
        """
    )

    root = QVBoxLayout(shell)
    root.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
    root.setSpacing(SPACING["lg"])

    if scrollable:
        scroll = QScrollArea()
        scroll.setObjectName(f"{object_name}ScrollArea")
        scroll.setProperty("uiPrimitive", "page_shell_scroll_area")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName(f"{object_name}Content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(SPACING["lg"])
        for widget in content_widgets:
            content_layout.addWidget(widget)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)
    else:
        for widget in content_widgets:
            root.addWidget(widget)
        root.addStretch(1)
    return shell


def make_page_header(
    *,
    title: str,
    subtitle: str = "",
    object_name: str = "uiPageHeader",
    module_key: str = "",
    page_key: str = "",
    status_widgets: Sequence[object] = (),
    action_widgets: Sequence[object] = (),
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

    header = QFrame()
    header.setObjectName(object_name)
    header.setProperty("uiPrimitive", "page_header")
    header.setProperty("moduleKey", module_key)
    header.setProperty("pageKey", page_key)
    header.setFrameShape(QFrame.NoFrame)

    layout = QHBoxLayout(header)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(SPACING["lg"])

    title_block = QWidget()
    title_layout = QVBoxLayout(title_block)
    title_layout.setContentsMargins(0, 0, 0, 0)
    title_layout.setSpacing(SPACING["sm"])

    title_label = QLabel(title)
    title_label.setObjectName("uiPageHeaderTitle")
    title_label.setProperty("uiPrimitive", "page_header_title")
    title_label.setWordWrap(True)
    title_label.setStyleSheet(
        f"color: {COLORS['text']}; font-size: {FONT_SIZE['page_title']}px; font-weight: 800;"
    )
    title_layout.addWidget(title_label)

    if subtitle:
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("uiPageHeaderSubtitle")
        subtitle_label.setProperty("uiPrimitive", "page_header_subtitle")
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['body']}px;")
        title_layout.addWidget(subtitle_label)

    if status_widgets:
        status_row = QFrame()
        status_row.setObjectName("uiPageHeaderStatusRow")
        status_row.setProperty("uiPrimitive", "page_header_status_row")
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(SPACING["sm"])
        for widget in status_widgets:
            status_layout.addWidget(widget)
        status_layout.addStretch(1)
        title_layout.addWidget(status_row)

    layout.addWidget(title_block, 1)
    for widget in action_widgets:
        layout.addWidget(widget, 0, Qt.AlignTop)
    return header


def make_section_title(
    title: str,
    subtitle: str = "",
    *,
    object_name: str = "uiSectionTitle",
):
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

    frame = QFrame()
    frame.setObjectName(object_name)
    frame.setProperty("uiPrimitive", "section_title")
    frame.setFrameShape(QFrame.NoFrame)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(SPACING["xs"])

    title_label = QLabel(title)
    title_label.setObjectName("uiSectionTitleText")
    title_label.setWordWrap(True)
    title_label.setStyleSheet(
        f"color: {COLORS['text']}; font-size: {FONT_SIZE['card_title']}px; font-weight: 800;"
    )
    layout.addWidget(title_label)

    if subtitle:
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("uiSectionTitleSubtitle")
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['secondary']}px;")
        layout.addWidget(subtitle_label)
    return frame


def make_icon_label(
    text: str,
    *,
    icon_key: str = "",
    semantic_key: str = "",
    icon_size: int = 18,
    object_name: str = "uiIconLabel",
):
    from PySide6.QtCore import QSize
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

    frame = QFrame()
    frame.setObjectName(object_name)
    frame.setProperty("uiPrimitive", "icon_label")
    frame.setProperty("iconKey", icon_key)
    frame.setProperty("semanticKey", semantic_key)
    frame.setFrameShape(QFrame.NoFrame)
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(SPACING["sm"])

    icon_label = QLabel()
    icon_label.setObjectName("uiIconLabelIcon")
    icon_label.setProperty("uiPrimitive", "icon_label_icon")
    icon_label.setFixedSize(QSize(icon_size, icon_size))
    icon = load_module_icon(icon_key) if icon_key else None
    icon_fallback = True
    if icon is not None and not icon.isNull():
        icon_label.setPixmap(icon.pixmap(icon_size, icon_size))
        icon_fallback = False
    icon_label.setProperty("iconFallback", icon_fallback)
    if icon_key:
        icon_label.setProperty("iconSource", str(MODULE_ICON_PATHS.get(icon_key, "")))
    layout.addWidget(icon_label)

    text_label = QLabel(text)
    text_label.setObjectName("uiIconLabelText")
    text_label.setProperty("uiPrimitive", "icon_label_text")
    text_label.setWordWrap(True)
    text_label.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONT_SIZE['body']}px;")
    layout.addWidget(text_label, 1)
    return frame


def make_info_banner(
    text: str,
    *,
    title: str = "",
    severity: str = "info",
    semantic_state: str | None = None,
    object_name: str = "uiInfoBanner",
):
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

    palette = {
        "info": (COLORS["bio_soft"], "#D6E2EA", COLORS["bio"]),
        "warning": (COLORS["warning_soft"], COLORS["warning_border"], "#92400E"),
        "blocked": (COLORS["danger_soft"], COLORS["danger_border"], COLORS["danger"]),
        "success": (COLORS["success_soft"], COLORS["success_border"], "#0E6F66"),
        "draft": ("#F8FAFC", COLORS["border"], COLORS["text"]),
    }
    background, border, text_color = palette.get(severity, palette["info"])
    banner = QFrame()
    banner.setObjectName(object_name)
    banner.setProperty("uiPrimitive", "info_banner")
    banner.setProperty("severity", severity)
    _apply_semantic_state_properties(banner, semantic_state or _state_for_severity(severity))
    banner.setStyleSheet(
        f"""
        QFrame#{object_name} {{
            color: {text_color};
            background: {background};
            border: 1px solid {border};
            border-radius: {RADIUS["sm"]}px;
        }}
        QLabel {{
            color: {text_color};
            background: transparent;
        }}
        """
    )
    layout = QVBoxLayout(banner)
    layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
    layout.setSpacing(SPACING["xs"])
    if title:
        title_label = QLabel(title)
        title_label.setObjectName("uiInfoBannerTitle")
        title_label.setWordWrap(True)
        title_label.setStyleSheet(f"font-size: {FONT_SIZE['body']}px; font-weight: 800;")
        layout.addWidget(title_label)
    body_label = QLabel(text)
    body_label.setObjectName("uiInfoBannerBody")
    body_label.setWordWrap(True)
    body_label.setStyleSheet(f"font-size: {FONT_SIZE['body']}px;")
    layout.addWidget(body_label)
    return banner


def make_app_sidebar(
    *,
    items: Sequence[AppSidebarItem],
    callbacks: dict[str, Callable[[], None]],
    title: str = "萤火虫 / Firefly",
    footer: str = "Developer Preview",
    active_key: str = "",
    width: int = 200,
):
    return AppSidebar(items=items, callbacks=callbacks, title=title, footer=footer, active_key=active_key, width=width)


class AppSidebar:  # Assigned below when PySide is available.
    pass


try:
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
except Exception:  # pragma: no cover
    pass
else:

    class AppSidebar(QFrame):  # type: ignore[no-redef]
        def __init__(
            self,
            *,
            items: Sequence[AppSidebarItem],
            callbacks: dict[str, Callable[[], None]],
            title: str = "萤火虫 / Firefly",
            footer: str = "Developer Preview",
            active_key: str = "",
            width: int = 200,
        ) -> None:
            super().__init__()
            self.setObjectName("appSidebar")
            self.setProperty("uiPrimitive", "app_sidebar")
            self.setProperty("activeKey", active_key)
            self._nav_buttons: dict[str, QPushButton] = {}
            self.setFixedWidth(width)
            self.setStyleSheet(_app_sidebar_stylesheet())

            layout = QVBoxLayout(self)
            layout.setContentsMargins(7, 14, 7, 14)
            layout.setSpacing(2)

            brand = QFrame()
            brand.setObjectName("appSidebarBrand")
            brand.setProperty("uiPrimitive", "app_sidebar_brand")
            brand_layout = QHBoxLayout(brand)
            brand_layout.setContentsMargins(7, 0, 7, 14)
            brand_layout.setSpacing(9)
            brand_icon = QLabel()
            brand_icon.setObjectName("appSidebarBrandIcon")
            brand_icon.setProperty("uiPrimitive", "app_sidebar_brand_icon")
            brand_icon.setFixedSize(28, 28)
            brand_icon.setScaledContents(True)
            app_icon = load_app_icon()
            if not app_icon.isNull():
                brand_icon.setPixmap(app_icon.pixmap(28, 28))
                brand_icon.setProperty("iconSource", str(APP_ICON_PNG_PATH))
                brand_icon.setProperty("iconFallback", False)
            else:
                brand_icon.setText("F")
                brand_icon.setAlignment(Qt.AlignCenter)
                brand_icon.setProperty("iconFallback", True)
            brand_layout.addWidget(brand_icon, 0, Qt.AlignTop)

            title_lines = [line.strip() for line in title.splitlines() if line.strip()]
            title_col = QVBoxLayout()
            title_col.setContentsMargins(0, 0, 0, 0)
            title_col.setSpacing(1)
            title_label = QLabel(title_lines[0] if title_lines else title)
            title_label.setObjectName("appSidebarTitle")
            title_label.setProperty("uiPrimitive", "app_sidebar_title")
            title_label.setWordWrap(False)
            subtitle_label = QLabel(title_lines[1] if len(title_lines) > 1 else "")
            subtitle_label.setObjectName("appSidebarSubtitle")
            subtitle_label.setProperty("uiPrimitive", "app_sidebar_subtitle")
            subtitle_label.setWordWrap(False)
            title_col.addWidget(title_label)
            title_col.addWidget(subtitle_label)
            brand_layout.addLayout(title_col, 1)
            layout.addWidget(brand)

            auxiliary_started = False
            for item in items:
                if item.usability_role == "auxiliary_navigation" and not auxiliary_started:
                    layout.addStretch(1)
                    auxiliary_started = True
                button = QPushButton(_sidebar_item_text(item.label))
                button.setObjectName("appSidebarButton" if item.usability_role == "primary_navigation" else "appSidebarAuxButton")
                button.setProperty("uiPrimitive", "app_sidebar_item")
                button.setProperty("navKey", item.semantic_key)
                button.setProperty("semanticKey", item.semantic_key)
                button.setProperty("pageKey", item.key)
                button.setProperty("iconKey", item.icon_key)
                button.setProperty("moduleKey", item.icon_key if item.icon_key.startswith("module.") else "")
                button.setProperty("usabilityRole", item.usability_role)
                button.setProperty("current", item.key == active_key)
                button.setProperty("formalActionEnabled", False)
                button.setProperty("fileWriteAllowed", False)
                button.setProperty("buttonBehavior", f"navigates_to_shell_route_{item.key}")
                button.setAccessibleName(item.label)
                button.setToolTip(item.tooltip or item.label)
                button.setMinimumHeight(44)
                if item.icon_key:
                    icon = _load_sidebar_icon(item.icon_key)
                    if not icon.isNull():
                        button.setIcon(icon)
                        button.setIconSize(QSize(18, 18))
                    button.setProperty("iconSource", _sidebar_icon_source(item.icon_key))
                    button.setProperty("iconFallback", icon.isNull())
                callback = callbacks.get(item.key)
                if callback is not None:
                    button.clicked.connect(callback)
                self._nav_buttons[item.key] = button
                layout.addWidget(button)

            if not auxiliary_started:
                layout.addStretch(1)
            footer_label = QLabel(footer)
            footer_label.setObjectName("appSidebarFooter")
            footer_label.setProperty("uiPrimitive", "app_sidebar_footer")
            footer_label.setWordWrap(True)
            layout.addWidget(footer_label)

        def set_active_key(self, active_key: str) -> None:
            self.setProperty("activeKey", active_key)
            for key, button in self._nav_buttons.items():
                button.setProperty("current", key == active_key)
                button.style().unpolish(button)
                button.style().polish(button)
                button.update()


def diagnostic_disclosure_title(title: str) -> str:
    return f"{title} / Developer diagnostics"


def _sidebar_item_text(label: str) -> str:
    if " / " in label:
        primary, secondary = label.split(" / ", 1)
        return f"{primary}\n{secondary}"
    return label


def _load_sidebar_icon(icon_key: str):
    if icon_key.startswith("ui02."):
        return load_ui02_module_selection_icon(icon_key.removeprefix("ui02."))
    return load_module_icon(icon_key)


def _sidebar_icon_source(icon_key: str) -> str:
    if icon_key.startswith("ui02."):
        return icon_key
    return str(MODULE_ICON_PATHS.get(icon_key, ""))


def _button_object_name(role: str) -> str:
    if role == "primary":
        return "primaryButton"
    if role == "primary_action":
        return "primaryActionButton"
    if role == "danger":
        return "dangerButton"
    if role == "ghost":
        return "ghostButton"
    if role == "file_picker":
        return "filePickerButton"
    if role == "disabled_action":
        return "disabledActionButton"
    return "secondaryButton"


def _button_height(size: str) -> int:
    if size == "small":
        return 32
    if size == "compact":
        return 34
    if size == "large":
        return CONTROL_HEIGHT["primary"]
    return CONTROL_HEIGHT["button"]


def _apply_semantic_state_properties(widget, semantic_state: str) -> None:
    state = semantic_state if semantic_state in SEMANTIC_STATE_KEYS else ""
    widget.setProperty("semanticState", state)
    for key in SEMANTIC_STATE_KEYS:
        widget.setProperty(key, key == state)


def _state_for_severity(severity: str) -> str:
    if severity == "warning":
        return "blocked"
    if severity == "blocked":
        return "blocked"
    if severity == "success":
        return "available"
    if severity == "draft":
        return "draft"
    return "testing"


def _app_sidebar_stylesheet() -> str:
    return f"""
    QFrame#appSidebar {{
        background: #FFFFFF;
        border-right: 1px solid #E5E8EF;
    }}
    QFrame#appSidebarBrand {{
        background: transparent;
        border: 0;
    }}
    QLabel#appSidebarBrandIcon {{
        background: #EEF3FF;
        border: 1px solid #D9E4FF;
        border-radius: 8px;
        color: #3B6FD9;
        font-size: 14px;
        font-weight: 800;
    }}
    QLabel#appSidebarTitle {{
        color: #1A1D2E;
        background: transparent;
        font-size: 13px;
        font-weight: 800;
        padding: 0;
    }}
    QLabel#appSidebarSubtitle {{
        color: #8B93A5;
        background: transparent;
        font-size: 10px;
        font-weight: 600;
        padding: 0;
    }}
    QLabel#appSidebarFooter {{
        color: #8B93A5;
        background: #F5F7FF;
        border: 1px solid #DDE3F5;
        border-radius: 8px;
        padding: 10px 11px;
        font-size: 10px;
    }}
    QPushButton#appSidebarButton, QPushButton#appSidebarAuxButton {{
        text-align: left;
        color: #5A6179;
        background: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 7px 10px;
        font-size: 11px;
    }}
    QPushButton#appSidebarButton:hover, QPushButton#appSidebarAuxButton:hover {{
        background: #F5F8FF;
    }}
    QPushButton#appSidebarButton[current="true"], QPushButton#appSidebarAuxButton[current="true"] {{
        color: #3B6FD9;
        background: #EEF3FE;
        border: 1px solid #EEF3FE;
        font-weight: 750;
    }}
    QPushButton#appSidebarAuxButton {{
        color: #5A6179;
    }}
    """
