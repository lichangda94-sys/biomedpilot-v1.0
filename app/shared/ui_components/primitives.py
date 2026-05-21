from __future__ import annotations

from app.ui_style_tokens import (
    BUTTON_TOKENS,
    COLORS,
    FONT_SIZE,
    RADIUS,
    UIStatusKey,
    button_stylesheet,
    card_stylesheet,
    get_status_token,
    status_chip_stylesheet,
)
from app.shared.semantic_keys import AnalysisStatusKey, FeatureStatusKey, ReportStatusKey, ResourceStatusKey


STATUS_SEMANTIC_KEYS: dict[str, str] = {
    UIStatusKey.DEVELOPER_PREVIEW.value: FeatureStatusKey.DEVELOPER_PREVIEW.value,
    UIStatusKey.TESTING.value: FeatureStatusKey.TESTING.value,
    UIStatusKey.PLANNED.value: FeatureStatusKey.PLANNED.value,
    UIStatusKey.SHELL_ONLY.value: FeatureStatusKey.SHELL_ONLY.value,
    UIStatusKey.PREFLIGHT_ONLY.value: AnalysisStatusKey.PREFLIGHT_ONLY.value,
    UIStatusKey.BLOCKED.value: FeatureStatusKey.BLOCKED.value,
    UIStatusKey.AVAILABLE.value: ResourceStatusKey.AVAILABLE.value,
    UIStatusKey.NOT_CONFIGURED.value: ResourceStatusKey.NOT_CONFIGURED.value,
    UIStatusKey.MISSING.value: ResourceStatusKey.NOT_CONFIGURED.value,
    UIStatusKey.FAILED.value: ResourceStatusKey.FAILED.value,
    UIStatusKey.DRAFT.value: ReportStatusKey.DRAFT.value,
    UIStatusKey.REPORT_READY.value: ReportStatusKey.REPORT_READY_FUTURE.value,
}


def make_status_chip(label: str | None = None, *, status_key: str | UIStatusKey = UIStatusKey.NOT_CONFIGURED):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel

    token = get_status_token(status_key)
    chip = QLabel(label or token.label)
    chip.setObjectName("uiStatusChip")
    chip.setProperty("uiPrimitive", "status_chip")
    chip.setProperty("statusKey", token.key)
    chip.setProperty("semanticKey", STATUS_SEMANTIC_KEYS.get(token.key, ResourceStatusKey.NOT_CONFIGURED.value))
    chip.setProperty("iconHint", token.icon_hint)
    chip.setAlignment(Qt.AlignCenter)
    chip.setWordWrap(False)
    chip.setStyleSheet(status_chip_stylesheet(token.key))
    return chip


def make_button(text: str, *, role: str = "secondary", size: str = "regular"):
    from PySide6.QtWidgets import QPushButton

    button = QPushButton(text)
    button.setObjectName(_button_object_name(role))
    button.setProperty("uiPrimitive", "button")
    button.setProperty("buttonRole", role if role in BUTTON_TOKENS else "secondary")
    button.setProperty("buttonSize", size)
    button.setStyleSheet(button_stylesheet(role))
    return button


def make_card(*, object_name: str = "uiCard"):
    from PySide6.QtWidgets import QFrame

    card = QFrame()
    card.setObjectName(object_name)
    card.setProperty("uiPrimitive", "card")
    card.setFrameShape(QFrame.StyledPanel)
    card.setStyleSheet(card_stylesheet())
    return card


def make_empty_state(
    title: str,
    body: str,
    *,
    action_text: str | None = None,
    empty_state_key: str | None = None,
    semantic_key: str | None = None,
    illustration_size: int = 72,
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel, QVBoxLayout

    from app.app_identity import empty_state_image_key_for, load_empty_state_pixmap

    frame = make_card(object_name="uiEmptyState")
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
        layout.addWidget(make_button(action_text, role="secondary"))

    frame.setProperty("emptyStateImageFallback", frame.findChild(QLabel, "uiEmptyStateIllustration") is None)
    return frame


def diagnostic_disclosure_title(title: str) -> str:
    return f"{title} / Developer diagnostics"


def _button_object_name(role: str) -> str:
    if role == "primary":
        return "primaryButton"
    if role == "primary_action":
        return "primaryActionButton"
    if role == "danger":
        return "dangerButton"
    if role == "ghost":
        return "ghostButton"
    return "secondaryButton"
