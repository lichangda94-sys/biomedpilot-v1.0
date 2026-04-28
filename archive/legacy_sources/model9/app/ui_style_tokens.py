from __future__ import annotations


COLORS = {
    "background": "#F5F7F9",
    "surface": "#FFFFFF",
    "surface_muted": "#F8FAFC",
    "border": "#DDE3EA",
    "text": "#1F2933",
    "muted": "#6B7280",
    "bio": "#12324A",
    "bio_soft": "#EAF2F8",
    "bio_accent": "#1BAE9F",
    "meta": "#6B4FD8",
    "meta_soft": "#F0EDFF",
    "warning_soft": "#FFF7E6",
    "warning": "#D99A00",
    "success": "#22A66B",
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
}

ICON_SIZE = {
    "status": 12,
    "button": 14,
    "toolbar": 16,
    "nav": 18,
    "stat": 32,
    "empty": 80,
}

CONTROL_HEIGHT = {
    "field": 38,
    "button": 38,
    "primary": 42,
}

RADIUS = {
    "sm": 8,
    "md": 14,
    "lg": 20,
}

FONT_SIZE = {
    "app_title": 24,
    "page_title": 18,
    "card_title": 16,
    "body": 13,
    "secondary": 12,
    "caption": 11,
    "small": 12,
    "title": 18,
    "hero": 24,
}


def app_stylesheet() -> str:
    return f"""
    QWidget {{
        background: {COLORS["background"]};
        color: {COLORS["text"]};
        font-size: {FONT_SIZE["body"]}px;
    }}
    QLabel#heroTitle {{
        font-size: {FONT_SIZE["hero"]}px;
        font-weight: 700;
        background: transparent;
    }}
    QLabel#sectionTitle, QLabel#workspaceTitle {{
        font-size: {FONT_SIZE["page_title"]}px;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#cardTitle {{
        font-size: {FONT_SIZE["card_title"]}px;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#mutedLabel, QLabel#statusLabel {{
        font-size: {FONT_SIZE["secondary"]}px;
        color: {COLORS["muted"]};
        background: transparent;
    }}
    QLabel#friendlyStatusLabel {{
        color: {COLORS["bio"]};
        background: {COLORS["bio_soft"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
        padding: 8px 10px;
    }}
    QLabel#readinessReadyLabel {{
        font-size: {FONT_SIZE["secondary"]}px;
        color: {COLORS["success"]};
        background: transparent;
    }}
    QLabel#readinessWarningLabel {{
        font-size: {FONT_SIZE["secondary"]}px;
        color: {COLORS["warning"]};
        background: transparent;
        font-weight: 600;
    }}
    QFrame#card, QFrame#entryCard, QFrame#statCard, QFrame#sidePanel, QFrame#analysisSettingsPanel, QFrame#sidebarNavigation, QFrame#topBar, QFrame#bottomStatusBar {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["md"]}px;
    }}
    QFrame#topBar, QFrame#bottomStatusBar {{
        border-radius: {RADIUS["sm"]}px;
    }}
    QLabel#topBarTitle {{
        font-size: {FONT_SIZE["card_title"]}px;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#avatarPlaceholder {{
        color: #0B3A75;
        background: #DDEBFF;
        border-radius: 15px;
        font-size: 11px;
        font-weight: 700;
    }}
    QLabel#sidebarLogo {{
        color: #0B2F6B;
        font-size: {FONT_SIZE["card_title"]}px;
        font-weight: 700;
        background: transparent;
        padding: 4px 10px;
    }}
    QLabel#sidebarUserName {{
        color: {COLORS["text"]};
        font-size: {FONT_SIZE["body"]}px;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#sidebarAvatar {{
        color: #0B3A75;
        background: #DDEBFF;
        border-radius: 18px;
        font-weight: 700;
    }}
    QLabel#statCardIcon {{
        color: {COLORS["bio_accent"]};
        background: {COLORS["bio_soft"]};
        border: 1px solid #CFE0EA;
        border-radius: 14px;
        font-size: 26px;
        font-weight: 700;
    }}
    QLabel#statCardValue {{
        font-size: 21px;
        font-weight: 700;
        color: {COLORS["bio"]};
        background: transparent;
    }}
    QFrame#sidebarProfileCard {{
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["md"]}px;
        min-height: 126px;
    }}
    QFrame#storageUsageBar {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1976FF, stop:0.38 #1976FF, stop:0.39 #D6DEE9, stop:1 #D6DEE9);
        border: 0;
        border-radius: 3px;
    }}
    QFrame#navItemRow {{
        background: transparent;
        border: 0;
        border-radius: {RADIUS["sm"]}px;
    }}
    QFrame#navItemRow[workflowStatus="current"] {{
        background: {COLORS["bio_soft"]};
    }}
    QFrame#navItemRow[workflowStatus="locked"] QLabel#navItemTitle {{
        color: #9AA4B2;
    }}
    QFrame#navItemRow[workflowStatus="needs_attention"] QLabel#navItemTitle {{
        color: {COLORS["bio"]};
        font-weight: 600;
    }}
    QFrame#navItemAccent {{
        background: transparent;
        border: 0;
        border-radius: 2px;
    }}
    QFrame#navItemRow[workflowStatus="current"] QFrame#navItemAccent {{
        background: {COLORS["bio_accent"]};
    }}
    QLabel#navItemTitle {{
        font-size: {FONT_SIZE["body"]}px;
        color: {COLORS["text"]};
        background: transparent;
    }}
    QFrame#navItemRow[workflowStatus="current"] QLabel#navItemTitle {{
        color: {COLORS["bio"]};
        font-weight: 700;
    }}
    QLabel#navFeatureIcon, QLabel#navStatusIcon {{
        background: transparent;
    }}
    QScrollArea#mainWorkspaceScrollArea {{
        background: transparent;
        border: 0;
    }}
    QScrollArea#mainWorkspaceScrollArea QWidget {{
        background: transparent;
    }}
    QScrollArea#analysisSettingsScrollArea {{
        background: transparent;
        border: 0;
    }}
    QScrollArea#analysisSettingsScrollArea QWidget {{
        background: transparent;
    }}
    QFrame#chartPreview {{
        background: {COLORS["bio_soft"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["md"]}px;
    }}
    QFrame#heroCard {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["lg"]}px;
    }}
    QFrame#readinessChecklist {{
        background: {COLORS["surface_muted"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
    }}
    QFrame#readinessRow {{
        background: transparent;
        border: 0;
        min-height: 26px;
    }}
    QLabel#readinessItemLabel {{
        color: {COLORS["text"]};
        font-size: {FONT_SIZE["body"]}px;
        background: transparent;
    }}
    QLabel#readinessBadgeReady {{
        color: {COLORS["success"]};
        background: #EAF8F1;
        border: 1px solid #C8EFDC;
        border-radius: 8px;
        padding: 3px 7px;
        font-size: {FONT_SIZE["caption"]}px;
        font-weight: 600;
    }}
    QLabel#readinessBadgeWarning {{
        color: {COLORS["warning"]};
        background: {COLORS["warning_soft"]};
        border: 1px solid #F5D899;
        border-radius: 8px;
        padding: 3px 7px;
        font-size: {FONT_SIZE["caption"]}px;
        font-weight: 600;
    }}
    QFrame#comparisonControlChip {{
        background: #EEF6FF;
        border: 1px solid #B9D8FF;
        border-radius: {RADIUS["sm"]}px;
        min-height: 66px;
    }}
    QFrame#comparisonCaseChip {{
        background: #FFF1F0;
        border: 1px solid #FFD0CC;
        border-radius: {RADIUS["sm"]}px;
        min-height: 66px;
    }}
    QLabel#comparisonChipTitle {{
        font-size: {FONT_SIZE["body"]}px;
        font-weight: 600;
        color: {COLORS["bio"]};
        background: transparent;
    }}
    QLabel#comparisonChipDetail {{
        font-size: {FONT_SIZE["secondary"]}px;
        color: {COLORS["muted"]};
        background: transparent;
    }}
    QFrame#demoPreviewBanner {{
        background: #F0F7FA;
        border: 1px solid #CFE0EA;
        border-radius: {RADIUS["md"]}px;
    }}
    QFrame#emptyStateCard {{
        background: {COLORS["surface_muted"]};
        border: 1px dashed #C9D4E1;
        border-radius: {RADIUS["md"]}px;
    }}
    QLabel#emptyStateIcon {{
        background: transparent;
    }}
    QLabel#emptyStateTitle {{
        color: {COLORS["bio"]};
        font-size: {FONT_SIZE["body"]}px;
        font-weight: 700;
        background: transparent;
    }}
    QPushButton {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
        padding: 8px 12px;
        min-height: {CONTROL_HEIGHT["button"] - 18}px;
        font-size: {FONT_SIZE["body"]}px;
    }}
    QPushButton:hover {{
        background: {COLORS["surface_muted"]};
    }}
    QPushButton:disabled {{
        color: {COLORS["muted"]};
        background: {COLORS["surface_muted"]};
    }}
    QPushButton#primaryButton {{
        color: white;
        background: {COLORS["bio"]};
        border: 1px solid {COLORS["bio"]};
        min-height: {CONTROL_HEIGHT["primary"] - 18}px;
    }}
    QPushButton#secondaryButton, QPushButton#iconButton {{
        color: {COLORS["bio"]};
        background: {COLORS["bio_soft"]};
        border: 1px solid {COLORS["border"]};
    }}
    QPushButton#sourceSegmentButton {{
        padding: 7px 10px;
        background: {COLORS["surface"]};
    }}
    QPushButton#sourceSegmentButton:checked {{
        color: white;
        background: {COLORS["bio"]};
        border: 1px solid {COLORS["bio"]};
    }}
    QPushButton#comparisonControlCard {{
        color: {COLORS["bio"]};
        background: #EEF6FF;
        border: 1px solid #B9D8FF;
        text-align: left;
    }}
    QPushButton#comparisonCaseCard {{
        color: #D43832;
        background: #FFF1F0;
        border: 1px solid #FFD0CC;
        text-align: left;
    }}
    QPushButton#iconButton {{
        padding: 0;
        font-weight: 700;
    }}
    QPushButton#metaButton {{
        color: white;
        background: {COLORS["meta"]};
        border: 1px solid {COLORS["meta"]};
    }}
    QPushButton#navButton {{
        font-size: {FONT_SIZE["body"]}px;
        text-align: left;
        border: 0;
        background: transparent;
        padding: 9px 12px;
        min-height: 22px;
    }}
    QPushButton#navButton[workflowStatus="current"] {{
        background: {COLORS["bio_soft"]};
        color: {COLORS["bio"]};
        border-left: 3px solid {COLORS["bio_accent"]};
        font-weight: 700;
    }}
    QPushButton#navButton[workflowStatus="locked"] {{
        color: #9AA4B2;
    }}
    QPushButton#navButton[workflowStatus="needs_attention"] {{
        color: {COLORS["bio"]};
    }}
    QPushButton#topBarSearchButton, QPushButton#topBarHelpButton, QPushButton#topBarNotificationButton {{
        padding: 5px 8px;
        border-radius: {RADIUS["sm"]}px;
        background: transparent;
        border: 0;
        color: #263A59;
        min-width: 28px;
    }}
    QPushButton#navButton:checked {{
        background: {COLORS["bio_soft"]};
        color: {COLORS["bio"]};
        font-weight: 600;
    }}
    QComboBox, QLineEdit, QDoubleSpinBox {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
        padding: 7px 9px;
        min-height: {CONTROL_HEIGHT["field"] - 16}px;
        font-size: {FONT_SIZE["body"]}px;
    }}
    QPushButton#statusTaskButton {{
        text-align: left;
        color: {COLORS["muted"]};
        background: transparent;
        border: 0;
        padding: 0;
    }}
    QToolButton#advancedOptionsButton {{
        background: {COLORS["surface_muted"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
        padding: 8px 10px;
        text-align: left;
    }}
    """


def card_style(accent: str | None = None) -> str:
    border_color = accent or COLORS["border"]
    return (
        f"background: {COLORS['surface']}; "
        f"border: 1px solid {border_color}; "
        f"border-radius: {RADIUS['md']}px;"
    )
