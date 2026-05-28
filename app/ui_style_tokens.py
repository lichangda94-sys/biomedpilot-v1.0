from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class StatusVisualToken:
    key: str
    label: str
    background: str
    border: str
    text: str
    icon_hint: str = ""


@dataclass(frozen=True)
class ButtonVisualToken:
    role: str
    background: str
    border: str
    text: str
    hover_background: str


class UIStatusKey(StrEnum):
    DEVELOPER_PREVIEW = "developer_preview"
    TESTING = "testing"
    PLANNED = "planned"
    SHELL_ONLY = "shell_only"
    PREFLIGHT_ONLY = "preflight_only"
    BLOCKED = "blocked"
    DISABLED = "disabled"
    AVAILABLE = "available"
    NOT_CONFIGURED = "not_configured"
    MISSING = "missing"
    FAILED = "failed"
    DRAFT = "draft"
    ADAPTER_NEEDED = "adapter_needed"
    REPORT_DISABLED = "report_disabled"
    EXPORT_DISABLED = "export_disabled"
    REPORT_READY = "report_ready"


COLORS: dict[str, str] = {
    "background": "#F5F7F9",
    "dashboard_bg": "#F4F7FB",
    "dashboard_panel": "#FFFFFF",
    "dashboard_card": "#FFFFFF",
    "dashboard_border": "#DCE6F2",
    "dashboard_text_soft": "#6B7A90",
    "app_bg": "#F5F7F9",
    "surface": "#FFFFFF",
    "surface_muted": "#F1F5F9",
    "border": "#DDE5F0",
    "divider": "#E5EAF2",
    "text": "#0F172A",
    "text_secondary": "#334155",
    "muted": "#64748B",
    "bio": "#12324A",
    "bio_soft": "#EAF2FF",
    "bio_accent": "#1BAE9F",
    "bio_green": "#20A66A",
    "bio_green_soft": "#EAF8F0",
    "meta": "#12324A",
    "meta_soft": "#F5F7F9",
    "meta_accent": "#1BAE9F",
    "labtools": "#1E88E5",
    "labtools_soft": "#EAF6FF",
    "focus": "#2563EB",
    "warning_soft": "#FFF7E6",
    "warning": "#D99A00",
    "warning_border": "#F5D899",
    "success": "#22A66B",
    "success_soft": "#E7F7F5",
    "success_border": "#BCE7E2",
    "danger": "#D43832",
    "danger_soft": "#FFF1F0",
    "danger_border": "#FFD0CC",
}

COLORS.setdefault("deep_navy", "#12324A")
COLORS.setdefault("teal", "#1BAE9F")
COLORS.setdefault("light_gray", "#F5F7F9")
COLORS.setdefault("white", COLORS["surface"])

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}

CONTROL_HEIGHT = {
    "field": 38,
    "button": 38,
    "primary": 42,
}

BUTTON_TOKENS: dict[str, ButtonVisualToken] = {
    "primary": ButtonVisualToken("primary", COLORS["bio"], COLORS["bio"], "#FFFFFF", "#0D273B"),
    "primary_action": ButtonVisualToken("primary_action", COLORS["bio_accent"], COLORS["bio_accent"], "#FFFFFF", "#138F83"),
    "secondary": ButtonVisualToken("secondary", COLORS["bio_soft"], "#D6E2EA", COLORS["bio"], "#F4F8FB"),
    "ghost": ButtonVisualToken("ghost", "transparent", "transparent", COLORS["bio"], COLORS["surface_muted"]),
    "danger": ButtonVisualToken("danger", "#FFFFFF", COLORS["danger_border"], COLORS["danger"], "#FFF7F7"),
}


RADIUS = {
    "sm": 6,
    "md": 8,
    "lg": 14,
    "control": 6,
    "card": 14,
    "panel": 14,
}

FONT_SIZE = {
    "app_title": 24,
    "page_title": 30,
    "card_title": 16,
    "body": 13,
    "secondary": 12,
    "caption": 11,
    "hero": 30,
}

THEME_PALETTE = {
    "window": COLORS["background"],
    "window_text": COLORS["text"],
    "base": COLORS["surface"],
    "alternate_base": COLORS["surface_muted"],
    "tooltip_base": COLORS["surface"],
    "tooltip_text": COLORS["text"],
    "text": COLORS["text"],
    "button": COLORS["surface"],
    "button_text": COLORS["text"],
    "bright_text": "#FFFFFF",
    "highlight": COLORS["focus"],
    "highlighted_text": "#FFFFFF",
    "disabled_text": "#94A3B8",
    "selection_background": "#DBEAFE",
}

STATUS_TOKENS: dict[str, StatusVisualToken] = {
    UIStatusKey.DEVELOPER_PREVIEW.value: StatusVisualToken(UIStatusKey.DEVELOPER_PREVIEW.value, "Developer Preview", "#EEF6FF", "#BFDBFE", "#1E3A8A", "preview"),
    UIStatusKey.TESTING.value: StatusVisualToken(UIStatusKey.TESTING.value, "测试中", COLORS["success_soft"], COLORS["success_border"], "#0E6F66", "flask"),
    UIStatusKey.PLANNED.value: StatusVisualToken(UIStatusKey.PLANNED.value, "后续开放", COLORS["surface_muted"], COLORS["border"], COLORS["muted"], "calendar"),
    UIStatusKey.SHELL_ONLY.value: StatusVisualToken(UIStatusKey.SHELL_ONLY.value, "Shell only", "#F5F3FF", "#DDD6FE", "#5B21B6", "layout"),
    UIStatusKey.PREFLIGHT_ONLY.value: StatusVisualToken(UIStatusKey.PREFLIGHT_ONLY.value, "仅预检", "#EFF6FF", "#BFDBFE", "#1D4ED8", "checklist"),
    UIStatusKey.BLOCKED.value: StatusVisualToken(UIStatusKey.BLOCKED.value, "已阻塞", COLORS["warning_soft"], COLORS["warning_border"], "#92400E", "blocked"),
    UIStatusKey.DISABLED.value: StatusVisualToken(UIStatusKey.DISABLED.value, "已禁用", COLORS["surface_muted"], COLORS["border"], COLORS["muted"], "disabled"),
    UIStatusKey.AVAILABLE.value: StatusVisualToken(UIStatusKey.AVAILABLE.value, "可用", "#ECFDF3", "#BBF7D0", "#166534", "check"),
    UIStatusKey.NOT_CONFIGURED.value: StatusVisualToken(UIStatusKey.NOT_CONFIGURED.value, "未配置", COLORS["surface_muted"], COLORS["border"], COLORS["muted"], "settings"),
    UIStatusKey.MISSING.value: StatusVisualToken(UIStatusKey.MISSING.value, "缺失", COLORS["warning_soft"], COLORS["warning_border"], "#92400E", "missing"),
    UIStatusKey.FAILED.value: StatusVisualToken(UIStatusKey.FAILED.value, "失败", COLORS["danger_soft"], COLORS["danger_border"], COLORS["danger"], "alert"),
    UIStatusKey.DRAFT.value: StatusVisualToken(UIStatusKey.DRAFT.value, "草稿", "#F8FAFC", COLORS["border"], COLORS["text"], "draft"),
    UIStatusKey.ADAPTER_NEEDED.value: StatusVisualToken(UIStatusKey.ADAPTER_NEEDED.value, "需要适配器", COLORS["surface_muted"], COLORS["border"], COLORS["muted"], "adapter"),
    UIStatusKey.REPORT_DISABLED.value: StatusVisualToken(UIStatusKey.REPORT_DISABLED.value, "报告未开放", COLORS["surface_muted"], COLORS["border"], COLORS["muted"], "report-disabled"),
    UIStatusKey.EXPORT_DISABLED.value: StatusVisualToken(UIStatusKey.EXPORT_DISABLED.value, "导出未开放", COLORS["surface_muted"], COLORS["border"], COLORS["muted"], "export-disabled"),
    UIStatusKey.REPORT_READY.value: StatusVisualToken(UIStatusKey.REPORT_READY.value, "Report-ready", "#ECFDF3", "#86EFAC", "#14532D", "report"),
}

BUTTON_TOKENS: dict[str, ButtonVisualToken] = {
    "primary": ButtonVisualToken("primary", COLORS["bio"], COLORS["bio"], "#FFFFFF", "#0D273B"),
    "primary_action": ButtonVisualToken("primary_action", COLORS["bio_accent"], COLORS["bio_accent"], "#FFFFFF", "#138F83"),
    "secondary": ButtonVisualToken("secondary", COLORS["bio_soft"], "#D6E2EA", COLORS["bio"], "#F4F8FB"),
    "ghost": ButtonVisualToken("ghost", "transparent", "transparent", COLORS["bio"], COLORS["surface_muted"]),
    "file_picker": ButtonVisualToken("file_picker", "#FFFFFF", COLORS["border"], COLORS["bio"], COLORS["surface_muted"]),
    "disabled_action": ButtonVisualToken("disabled_action", COLORS["surface_muted"], COLORS["border"], COLORS["muted"], COLORS["surface_muted"]),
    "danger": ButtonVisualToken("danger", "#FFFFFF", COLORS["danger_border"], COLORS["danger"], "#FFF7F7"),
}


def get_status_token(status_key: str | UIStatusKey) -> StatusVisualToken:
    key = status_key.value if isinstance(status_key, UIStatusKey) else str(status_key)
    return STATUS_TOKENS.get(key, STATUS_TOKENS[UIStatusKey.NOT_CONFIGURED.value])


def get_button_token(role: str) -> ButtonVisualToken:
    return BUTTON_TOKENS.get(role, BUTTON_TOKENS["secondary"])


def status_chip_stylesheet(status_key: str | UIStatusKey) -> str:
    token = get_status_token(status_key)
    return (
        "QLabel {"
        f"color: {token.text};"
        f"background: {token.background};"
        f"border: 1px solid {token.border};"
        f"border-radius: {RADIUS['sm']}px;"
        "padding: 5px 9px;"
        f"font-size: {FONT_SIZE['secondary']}px;"
        "font-weight: 700;"
        "}"
    )


def button_stylesheet(role: str) -> str:
    token = get_button_token(role)
    border = "0" if token.border == "transparent" else f"1px solid {token.border}"
    return f"""
    QPushButton {{
        color: {token.text};
        background: {token.background};
        border: {border};
        border-radius: {RADIUS["sm"]}px;
        padding: 7px 12px;
        min-height: {CONTROL_HEIGHT["button"] - 16}px;
        font-size: {FONT_SIZE["body"]}px;
        font-weight: 650;
    }}
    QPushButton:hover {{
        background: {token.hover_background};
    }}
    QPushButton:disabled {{
        color: {COLORS["muted"]};
        background: {COLORS["surface_muted"]};
        border: 1px solid {COLORS["border"]};
    }}
    """


def card_stylesheet() -> str:
    return f"""
    QFrame {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["md"]}px;
    }}
    """


def meta_card_stylesheet(*, muted: bool = False) -> str:
    background = COLORS["light_gray"] if muted else COLORS["white"]
    return f"QFrame {{ border: 1px solid {COLORS['border']}; border-radius: {RADIUS['sm']}px; background: {background}; }}"


def meta_error_text_style() -> str:
    return f"color: {COLORS['danger']};"


def meta_text_style(*, size: int = 12) -> str:
    return f"color: {COLORS['text']}; font-size: {size}px;"


def meta_title_style(*, size: int = 20) -> str:
    return f"color: {COLORS['deep_navy']}; font-size: {size}px; font-weight: 700;"


def meta_workspace_stylesheet() -> str:
    return f"""
        QWidget#metaWorkspace {{ background: {COLORS["light_gray"]}; color: {COLORS["text"]}; }}
        QFrame#metaGlobalNav, QFrame#metaWorkflowNav {{ background: {COLORS["white"]}; border-right: 1px solid {COLORS["border"]}; }}
        QFrame#metaCurrentStepWorkspace {{ background: {COLORS["light_gray"]}; }}
        QFrame#metaPageHeader, QFrame#metaCard, QFrame#metaInfoCard, QFrame#metaProjectOverviewCard,
        QFrame#metaProgressCard, QFrame#metaWarningsCard, QFrame#metaLibrarySummary,
        QFrame#metaLibraryDiagnostics, QFrame#metaImportBatchSummary, QFrame#metaQueryDraftCard,
        QFrame#metaConfirmedProtocolCard, QFrame#metaConfirmedSearchCard {{
            background: {COLORS["white"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS["sm"]}px;
        }}
        QFrame#metaDeveloperDetails {{ background: transparent; border: none; }}
        QLabel#metaSideTitle {{ color: {COLORS["deep_navy"]}; font-size: 22px; font-weight: 700; }}
        QLabel#metaPanelTitle {{ color: {COLORS["deep_navy"]}; font-size: 16px; font-weight: 700; }}
        QLabel#metaPageTitle {{ color: {COLORS["deep_navy"]}; font-size: 22px; font-weight: 700; }}
        QLabel#metaCardTitle {{ color: {COLORS["deep_navy"]}; font-size: 15px; font-weight: 700; }}
        QLabel#metaMutedText, QLabel#metaCardBody {{ color: {COLORS["muted"]}; }}
        QLabel#metaWarningText {{ color: {COLORS["warning"]}; font-weight: 600; }}
        QLabel#metaStatusBadge {{
            color: {COLORS["deep_navy"]};
            background: {COLORS["light_gray"]};
            border: 1px solid {COLORS["teal"]};
            border-radius: {RADIUS["sm"]}px;
            padding: 4px 8px;
            font-weight: 700;
        }}
        QListWidget#metaWorkflowStepList {{
            background: {COLORS["white"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS["sm"]}px;
        }}
        QPushButton#metaPrimaryButton {{
            background: {COLORS["teal"]};
            color: {COLORS["white"]};
            border: 1px solid {COLORS["teal"]};
            border-radius: {RADIUS["sm"]}px;
            padding: 8px 12px;
            font-weight: 700;
        }}
        QPushButton#metaSecondaryButton {{
            background: {COLORS["white"]};
            color: {COLORS["deep_navy"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS["sm"]}px;
            padding: 8px 12px;
        }}
        """


def global_app_stylesheet() -> str:
    return f"""
        QWidget {{
            background-color: {COLORS["background"]};
            color: {COLORS["text"]};
        }}
        QFrame, QGroupBox, QTabWidget::pane {{
            background-color: {COLORS["surface"]};
            color: {COLORS["text"]};
        }}
        QLabel {{
            background: transparent;
            color: {COLORS["text"]};
        }}
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox,
        QTableWidget, QTreeWidget, QListWidget {{
            background-color: {COLORS["surface"]};
            color: {COLORS["text"]};
            selection-background-color: {THEME_PALETTE["selection_background"]};
            selection-color: {COLORS["text"]};
        }}
        QPushButton {{
            background-color: {COLORS["surface"]};
            color: {COLORS["text"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS["sm"]}px;
            padding: 6px 10px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["surface_muted"]};
        }}
        QPushButton:disabled {{
            background-color: {COLORS["background"]};
            color: {THEME_PALETTE["disabled_text"]};
        }}
        QHeaderView::section {{
            background-color: {COLORS["surface_muted"]};
            color: {COLORS["text"]};
            border: 1px solid {COLORS["border"]};
            padding: 4px;
        }}
        QScrollArea, QScrollArea > QWidget > QWidget {{
            background-color: {COLORS["background"]};
        }}
        """


def login_stylesheet() -> str:
    return f"""
    QWidget#loginPage, QWidget#welcomePage {{
        background: {COLORS["background"]};
        color: {COLORS["text"]};
        font-size: {FONT_SIZE["body"]}px;
    }}
    QFrame#loginTopBar {{
        background: rgba(255, 255, 255, 0.92);
        border-bottom: 1px solid {COLORS["border"]};
    }}
    QLabel#trafficDotRed {{
        background: #EF5F56;
        border-radius: 6px;
    }}
    QLabel#trafficDotYellow {{
        background: #F4BF4F;
        border-radius: 6px;
    }}
    QLabel#trafficDotGreen {{
        background: #56C75A;
        border-radius: 6px;
    }}
    QLabel#loginTopTitle {{
        color: #0F1F38;
        font-size: 17px;
        font-weight: 800;
        background: transparent;
    }}
    QLabel#loginTopVersion {{
        color: #64748B;
        font-size: {FONT_SIZE["caption"]}px;
        background: transparent;
    }}
    QPushButton#loginTopIconButton {{
        background: transparent;
        border: 0;
        padding: 2px;
        min-height: 0;
    }}
    QWidget#loginMainContent {{
        background: {COLORS["background"]};
    }}
    QFrame#loginBrandPanel {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 #092944,
            stop: 0.45 {COLORS["bio"]},
            stop: 1 #0CA99C
        );
        border: 0;
        border-radius: 0px;
    }}
    QLabel#brandTitle {{
        color: #FFFFFF;
        font-size: 44px;
        font-weight: 800;
        background: transparent;
    }}
    QLabel#brandChineseName {{
        color: #47E6D8;
        font-size: 27px;
        font-weight: 800;
        background: transparent;
    }}
    QLabel#brandSubtitle {{
        color: #F4FAFF;
        font-size: 15px;
        font-weight: 600;
        line-height: 150%;
        background: transparent;
    }}
    QLabel#brandVersionLabel {{
        color: #D7E7EF;
        font-size: {FONT_SIZE["secondary"]}px;
        background: transparent;
    }}
    QLabel#loginBrandIcon, QLabel#loginMetaIcon {{
        background: transparent;
        border: 0;
    }}
    QLabel#capabilityTag {{
        color: #FFFFFF;
        background: rgba(255, 255, 255, 0.11);
        border: 1px solid rgba(255, 255, 255, 0.28);
        border-radius: 8px;
        padding: 12px 18px;
        font-size: 15px;
        font-weight: 700;
    }}
    QFrame#loginCard {{
        background: {COLORS["surface"]};
        border: 1px solid #D5DDE7;
        border-radius: 18px;
    }}
    QLabel#loginTitle {{
        color: {COLORS["bio"]};
        font-size: 30px;
        font-weight: 850;
        background: transparent;
    }}
    QLabel#loginHint, QLabel#loginFieldLabel, QLabel#loginMetaLabel {{
        color: {COLORS["muted"]};
        background: transparent;
    }}
    QLabel#loginFieldLabel {{
        font-size: {FONT_SIZE["secondary"]}px;
        font-weight: 600;
    }}
    QLabel#loginErrorLabel {{
        color: {COLORS["danger"]};
        background: #FFF1F0;
        border: 1px solid #FFD0CC;
        border-radius: {RADIUS["sm"]}px;
        padding: 7px 9px;
        font-size: {FONT_SIZE["secondary"]}px;
    }}
    QFrame#loginAccountPanel {{
        background: #FBFCFE;
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
    }}
    QLabel#loginAccountValue {{
        color: {COLORS["bio"]};
        background: transparent;
        font-size: 17px;
        font-weight: 800;
    }}
    QLabel#loginMetaValue {{
        color: {COLORS["bio"]};
        background: {COLORS["bio_soft"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
        padding: 7px 9px;
        font-weight: 600;
    }}
    QFrame#loginStatusTile {{
        background: #FFFFFF;
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
    }}
    QLabel#loginStatusTitle {{
        color: {COLORS["bio"]};
        background: transparent;
        font-size: {FONT_SIZE["caption"]}px;
        font-weight: 650;
    }}
    QLabel#loginStatusValue {{
        color: {COLORS["muted"]};
        background: {COLORS["surface_muted"]};
        border: 0;
        border-radius: 6px;
        padding: 2px 6px;
        font-size: 10px;
        font-weight: 650;
    }}
    QLineEdit {{
        background: {COLORS["surface"]};
        border: 1px solid #CBD5E1;
        border-radius: {RADIUS["sm"]}px;
        padding: 9px 12px;
        min-height: 30px;
        font-size: 15px;
        color: {COLORS["bio"]};
    }}
    QLineEdit:focus {{
        border: 1px solid {COLORS["bio_accent"]};
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
        color: #FFFFFF;
        background: {COLORS["bio_accent"]};
        border: 1px solid {COLORS["bio_accent"]};
        min-height: 34px;
        font-size: 15px;
        font-weight: 700;
    }}
    QPushButton#primaryButton:hover {{
        background: #129E91;
    }}
    QPushButton#linkButton {{
        color: {COLORS["bio_accent"]};
        background: transparent;
        border: 0;
        padding: 4px 0;
        text-align: left;
        font-weight: 700;
    }}
    QPushButton#linkButton:disabled {{
        color: {COLORS["bio_accent"]};
        background: transparent;
    }}
    """


def module_selection_stylesheet() -> str:
    return f"""
    QWidget#moduleSelectionPage, QWidget#moduleSelectionContent {{
        background: #F0F2F7;
        color: {COLORS["text"]};
        font-size: {FONT_SIZE["body"]}px;
    }}
    QScrollArea#moduleSelectionScrollArea {{
        border: 0;
        background: #F0F2F7;
    }}
    QFrame#dashboardHeader,
    QFrame#dashboardModulePanel,
    QFrame#moduleCard,
    QFrame#supportCard,
    QFrame#dashboardActivityCard {{
        background: {COLORS["dashboard_panel"]};
        border: 1px solid {COLORS["dashboard_border"]};
        border-radius: {RADIUS["lg"]}px;
    }}
    QFrame#dashboardHeader {{
        background: #FFFFFF;
        border: 0;
        border-bottom: 1px solid #E5E8EF;
        border-radius: 0;
    }}
    QLabel#dashboardHeroIcon {{
        background: #EAF2FF;
        border: 1px solid #D7E7FF;
        border-radius: 16px;
    }}
    QFrame#dashboardMetricStrip {{
        background: transparent;
        border: 0;
    }}
    QFrame#dashboardMetricCard {{
        border-radius: 14px;
    }}
    QFrame#dashboardModulePanel {{
        background: transparent;
        border: 0;
        border-radius: 0;
    }}
    QFrame#dashboardRecentProjectsCard,
    QFrame#dashboardActivityCard {{
        background: #FFFFFF;
        border-radius: 15px;
        border: 1px solid #E5E8EF;
    }}
    QFrame#moduleCard {{
        border-radius: 15px;
        padding: 0;
    }}
    QFrame#moduleCard[moduleAccent="bio"] {{
        background: #ECFAF6;
        border: 1px solid #A7E3D5;
    }}
    QFrame#moduleCard[moduleAccent="meta"] {{
        background: #F6F1FF;
        border: 1px solid #D7C8FF;
    }}
    QFrame#moduleCard[moduleAccent="labtools"] {{
        background: #EEF5FF;
        border: 1px solid #AFCBFF;
    }}
    QFrame#dashboardActivityItem {{
        background: #F8FAFC;
        border: 1px solid {COLORS["divider"]};
        border-radius: {RADIUS["md"]}px;
    }}
    QFrame#dashboardInlineEmptyState {{
        background: #F8FAFC;
        border: 1px solid {COLORS["divider"]};
        border-radius: {RADIUS["md"]}px;
    }}
    QLabel#dashboardEyebrow {{
        color: {COLORS["bio"]};
        font-size: {FONT_SIZE["caption"]}px;
        font-weight: 800;
        letter-spacing: 0px;
        background: transparent;
    }}
    QLabel#dashboardTitle {{
        color: #1A1D2E;
        font-size: 20px;
        font-weight: 800;
        background: transparent;
    }}
    QLabel#dashboardSubtitle,
    QLabel#sessionMetaLabel,
    QLabel#moduleDescription,
    QLabel#supportLine,
    QLabel#dashboardMetricCaption,
    QLabel#dashboardActivityMeta {{
        color: #9AA1B4;
        background: transparent;
    }}
    QLabel#sessionBadge {{
        color: #5A6179;
        background: #FFFFFF;
        border: 0;
        border-radius: 18px;
        padding: 7px 10px;
        font-weight: 600;
    }}
    QLabel#previewBadge {{
        color: #92600A;
        background: #FEF3CD;
        border: 1px solid #FDE68A;
        border-radius: 12px;
        padding: 5px 10px;
        font-weight: 600;
    }}
    QLabel#dashboardMetricLabel {{
        color: {COLORS["dashboard_text_soft"]};
        font-size: {FONT_SIZE["caption"]}px;
        font-weight: 700;
        background: transparent;
    }}
    QLabel#dashboardMetricValue {{
        color: {COLORS["text"]};
        font-size: 17px;
        font-weight: 800;
        background: transparent;
    }}
    QLabel#moduleTitle {{
        color: #1A1D2E;
        font-size: 20px;
        font-weight: 800;
        background: transparent;
    }}
    QLabel#moduleEnglishTitle {{
        color: #059669;
        font-size: 13px;
        font-weight: 800;
        background: transparent;
    }}
    QFrame#moduleCard[moduleAccent="bio"] QLabel#moduleEnglishTitle {{
        color: #059669;
    }}
    QFrame#moduleCard[moduleAccent="meta"] QLabel#moduleEnglishTitle {{
        color: #7C3AED;
    }}
    QFrame#moduleCard[moduleAccent="labtools"] QLabel#moduleEnglishTitle {{
        color: #2563EB;
    }}
    QLabel#moduleAccentLine {{
        background: {COLORS["bio_green"]};
        border: 0;
        border-radius: 2px;
    }}
    QFrame#moduleCard[moduleAccent="bio"] QLabel#moduleAccentLine {{
        background: {COLORS["bio_green"]};
    }}
    QFrame#moduleCard[moduleAccent="meta"] QLabel#moduleAccentLine {{
        background: {COLORS["meta"]};
    }}
    QFrame#moduleCard[moduleAccent="labtools"] QLabel#moduleAccentLine {{
        background: {COLORS["labtools"]};
    }}
    QLabel#moduleIcon, QLabel#ui02Icon {{
        background: transparent;
        border: 0;
    }}
    QLabel#moduleIcon {{
        border-radius: 14px;
    }}
    QFrame#moduleCard[moduleAccent="bio"] QLabel#moduleIcon {{
        background: #D4F5EC;
        border: 0;
    }}
    QFrame#moduleCard[moduleAccent="meta"] QLabel#moduleIcon {{
        background: #E9DDFC;
        border: 0;
    }}
    QFrame#moduleCard[moduleAccent="labtools"] QLabel#moduleIcon {{
        background: #D1E0FC;
        border: 0;
    }}
    QLabel#supportTitle {{
        color: {COLORS["bio"]};
        font-size: {FONT_SIZE["card_title"]}px;
        font-weight: 700;
        background: transparent;
    }}
    QLabel#dashboardSectionTitle {{
        color: #1A1D2E;
        font-size: 15px;
        font-weight: 800;
        background: transparent;
    }}
    QLabel#dashboardSectionSubtitle {{
        color: #8B93A5;
        font-size: 11px;
        background: transparent;
    }}
    QLabel#dashboardTestingPill {{
        color: #A16207;
        background: #FEF3CD;
        border: 1px solid #FDE68A;
        border-radius: 10px;
        padding: 3px 8px;
        font-size: 10px;
        font-weight: 700;
    }}
    QLabel#dashboardActivityTitle {{
        color: {COLORS["text"]};
        font-size: {FONT_SIZE["body"]}px;
        font-weight: 750;
        background: transparent;
    }}
    QLabel#dashboardEmptyTitle {{
        color: {COLORS["text"]};
        font-size: {FONT_SIZE["body"]}px;
        font-weight: 750;
        background: transparent;
    }}
    QLabel#dashboardEmptyBody {{
        color: {COLORS["dashboard_text_soft"]};
        font-size: {FONT_SIZE["secondary"]}px;
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
    QPushButton#dashboardHeaderIconButton {{
        color: #5A6179;
        background: #FFFFFF;
        border: 0;
        border-radius: 11px;
        padding: 0;
        font-weight: 750;
    }}
    QPushButton#primaryButton, QPushButton#bioModuleButton, QPushButton#metaModuleButton, QPushButton#labtoolsModuleButton {{
        min-height: 34px;
        font-weight: 700;
        border-radius: 12px;
    }}
    QPushButton#bioModuleButton {{
        color: #FFFFFF;
        background: #059669;
        border: 1px solid #059669;
    }}
    QPushButton#metaModuleButton {{
        color: #FFFFFF;
        background: #7C3AED;
        border: 1px solid #7C3AED;
    }}
    QPushButton#labtoolsModuleButton {{
        color: #FFFFFF;
        background: #2563EB;
        border: 1px solid #2563EB;
    }}
    QPushButton#bioModuleButton:hover {{
        background: #047857;
    }}
    QPushButton#metaModuleButton:hover {{
        background: #6D28D9;
    }}
    QPushButton#labtoolsModuleButton:hover {{
        background: #1D4ED8;
    }}
    QPushButton#dashboardOpenMoreProjectsButton {{
        color: #2563EB;
        background: #F5F8FF;
        border: 1px solid #BFCEF7;
        border-radius: 11px;
        font-weight: 700;
        min-height: 30px;
    }}
    QPushButton#dashboardOpenMoreProjectsButton:disabled,
    QPushButton#dashboardViewAllProjectsButton:disabled {{
        color: #2563EB;
        background: #F5F8FF;
        border: 1px solid #BFCEF7;
    }}
    QPushButton#dashboardViewAllProjectsButton {{
        color: #3B6FD9;
        background: transparent;
        border: 0;
        font-weight: 650;
        min-height: 28px;
    }}
    QTableWidget#dashboardRecentProjectsTable {{
        background: #FFFFFF;
        border: 0;
        gridline-color: #F5F6FA;
        color: #1A1D2E;
        font-size: 12px;
        selection-background-color: transparent;
    }}
    QTableWidget#dashboardRecentProjectsTable::item {{
        border-bottom: 1px solid #F5F6FA;
        padding: 0 8px;
    }}
    QHeaderView::section {{
        background: #FFFFFF;
        color: #9AA1B4;
        border: 0;
        border-top: 1px solid #F0F2F5;
        border-bottom: 1px solid #F0F2F5;
        padding: 9px 8px;
        font-size: 11px;
        font-weight: 800;
    }}
    QPushButton#secondaryButton {{
        color: {COLORS["bio"]};
        background: {COLORS["bio_soft"]};
        border: 1px solid {COLORS["border"]};
        font-weight: 600;
    }}
    QPushButton#logoutButton {{
        color: {COLORS["danger"]};
        background: #FFF7F7;
        border: 1px solid #FFD0CC;
        font-weight: 600;
    }}
    """


def bioinformatics_project_home_stylesheet() -> str:
    return f"""
    QWidget#bioinformaticsProjectHomePage,
    QWidget#bioProjectHomeContent,
    QWidget#bioDataSourcePlaceholderPage,
    QWidget#bioinformaticsDataSourcePage,
    QWidget#bioinformaticsAcquisitionStatusPage,
    QWidget#bioinformaticsRecognitionPage,
    QWidget#bioinformaticsReadinessDashboardPage,
    QWidget#bioinformaticsStandardizedAssetsPage,
    QWidget#bioinformaticsWorkflowStatusPage,
    QWidget#bioinformaticsAnalysisTaskCenterPage,
    QWidget#bioinformaticsResultsBrowserPage,
    QWidget#bioinformaticsReportViewerPage,
    QWidget#bioinformaticsSettingsLocalAIPage,
    QWidget#bioWorkflowScrollContent {{
        background: {COLORS["background"]};
        color: {COLORS["text"]};
        font-size: {FONT_SIZE["body"]}px;
    }}
    QScrollArea#bioProjectHomeScrollArea {{
        border: 0;
        background: {COLORS["background"]};
    }}
    QFrame#bioProjectHeader, QFrame#bioProjectCard, QFrame#bioProjectSummaryCard, QFrame#bioDataSourcePlaceholderCard,
    QFrame#readinessCompactStatusBar, QFrame#readinessSupplementCard {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["lg"]}px;
    }}
    QLabel#bioProjectIcon {{
        background: transparent;
        border: 0;
    }}
    QLabel#bioProjectTitle {{
        color: {COLORS["bio"]};
        font-size: 26px;
        font-weight: 800;
        background: transparent;
    }}
    QLabel#bioProjectSubtitle {{
        color: {COLORS["bio_accent"]};
        font-size: {FONT_SIZE["card_title"]}px;
        font-weight: 700;
        background: transparent;
    }}
    QLabel#bioProjectPreviewBadge {{
        color: #0E6F66;
        background: #E7F7F5;
        border: 1px solid #BCE7E2;
        border-radius: {RADIUS["sm"]}px;
        padding: 7px 10px;
        font-weight: 600;
    }}
    QLabel#bioProjectCardTitle {{
        color: {COLORS["bio"]};
        font-size: {FONT_SIZE["page_title"]}px;
        font-weight: 750;
        background: transparent;
    }}
    QLabel#bioProjectFieldLabel {{
        color: {COLORS["muted"]};
        font-size: {FONT_SIZE["secondary"]}px;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#bioProjectMutedLabel, QLabel#bioProjectSummaryLine, QLabel#bioProjectEmptyState {{
        color: {COLORS["muted"]};
        background: transparent;
    }}
    QLabel#bioProjectSummaryLine {{
        color: {COLORS["text"]};
        font-weight: 600;
    }}
    QLabel#bioProjectStepLabel {{
        background: {COLORS["surface_muted"]};
        color: {COLORS["muted"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
        padding: 6px 8px;
        font-size: {FONT_SIZE["secondary"]}px;
        font-weight: 650;
    }}
    QLabel#bioProjectStepLabel[state="done"] {{
        background: #E7F7F5;
        color: {COLORS["bio"]};
        border: 1px solid #BCE7E2;
    }}
    QLabel#bioProjectStepLabel[state="current"] {{
        background: {COLORS["bio"]};
        color: #FFFFFF;
        border: 1px solid {COLORS["bio"]};
    }}
    QFrame#bioProjectHealthCard {{
        background: #E7F7F5;
        border: 1px solid #BCE7E2;
        border-radius: {RADIUS["md"]}px;
    }}
    QFrame#bioProjectHealthCard[status="warning"] {{
        background: {COLORS["warning_soft"]};
        border: 1px solid #F5D899;
    }}
    QLabel#bioProjectHealthTitle {{
        color: {COLORS["bio"]};
        background: transparent;
        font-weight: 800;
    }}
    QLabel#bioProjectHealthDetail {{
        color: {COLORS["muted"]};
        background: transparent;
        font-size: {FONT_SIZE["secondary"]}px;
        font-weight: 600;
    }}
    QFrame#bioProjectMiniStatusBlock {{
        background: {COLORS["surface_muted"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["md"]}px;
    }}
    QLabel#bioProjectMiniStatusTitle {{
        color: {COLORS["muted"]};
        background: transparent;
        font-size: {FONT_SIZE["secondary"]}px;
        font-weight: 650;
    }}
    QLabel#bioProjectMiniStatusValue {{
        color: {COLORS["bio"]};
        background: transparent;
        font-weight: 800;
    }}
    QFrame#projectValidationStatusCard {{
        background: #EAF8F6;
        border: 1px solid #91D8D0;
        border-radius: {RADIUS["md"]}px;
    }}
    QLabel#bioProjectStatusLabel {{
        color: {COLORS["bio"]};
        background: {COLORS["bio_soft"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
        padding: 8px 10px;
        font-weight: 600;
    }}
    QFrame#projectValidationStatusCard QLabel#bioProjectStatusLabel {{
        color: {COLORS["bio"]};
        background: transparent;
        border: 0;
        padding: 0;
        font-weight: 750;
    }}
    QLabel#bioProjectStatusLabel[status="error"] {{
        color: {COLORS["danger"]};
        background: #FFF1F0;
        border: 1px solid #FFD0CC;
    }}
    QLabel#bioProjectStatusLabel[status="warning"] {{
        color: {COLORS["warning"]};
        background: {COLORS["warning_soft"]};
        border: 1px solid #F5D899;
    }}
    QLabel#readinessStatusBadge {{
        color: {COLORS["bio"]};
        background: #E7F7F5;
        border: 1px solid #BCE7E2;
        border-radius: {RADIUS["sm"]}px;
        padding: 7px 10px;
        font-weight: 750;
    }}
    QLabel#readinessWarningChips {{
        color: {COLORS["bio"]};
        background: transparent;
        font-weight: 600;
    }}
    QLineEdit {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
        padding: 8px 10px;
        min-height: {CONTROL_HEIGHT["field"] - 16}px;
        font-size: {FONT_SIZE["body"]}px;
    }}
    QLineEdit:focus {{
        border: 1px solid {COLORS["bio_accent"]};
    }}
    QComboBox, QPlainTextEdit, QTableWidget {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
        padding: 6px;
        color: {COLORS["text"]};
    }}
    QHeaderView::section {{
        background: {COLORS["bio_soft"]};
        color: {COLORS["bio"]};
        border: 0;
        border-right: 1px solid {COLORS["border"]};
        border-bottom: 1px solid {COLORS["border"]};
        padding: 6px;
        font-weight: 700;
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
        color: #FFFFFF;
        background: {COLORS["bio"]};
        border: 1px solid {COLORS["bio"]};
        min-height: {CONTROL_HEIGHT["primary"] - 18}px;
        font-weight: 700;
    }}
    QPushButton#secondaryButton {{
        color: {COLORS["bio"]};
        background: {COLORS["bio_soft"]};
        border: 1px solid {COLORS["border"]};
        font-weight: 600;
    }}
    QPushButton[buttonRole="primary_next"] {{
        color: #FFFFFF;
        background: {COLORS["bio"]};
        border: 1px solid {COLORS["bio"]};
        min-height: {CONTROL_HEIGHT["primary"] - 14}px;
        padding: 9px 16px;
        font-weight: 800;
    }}
    QPushButton[buttonRole="primary_action"] {{
        color: #FFFFFF;
        background: {COLORS["bio_accent"]};
        border: 1px solid {COLORS["bio_accent"]};
        min-height: {CONTROL_HEIGHT["primary"] - 16}px;
        font-weight: 750;
    }}
    QPushButton[buttonRole="back"], QPushButton[buttonRole="secondary"] {{
        color: {COLORS["bio"]};
        background: {COLORS["bio_soft"]};
        border: 1px solid #D6E2EA;
        font-weight: 650;
    }}
    QPushButton[buttonRole="danger"] {{
        color: {COLORS["danger"]};
        background: #FFFFFF;
        border: 1px solid #FFD0CC;
        font-weight: 650;
    }}
    QPushButton[buttonRole="primary_next"]:hover {{
        background: #0D273B;
        border: 1px solid #0D273B;
    }}
    QPushButton[buttonRole="primary_action"]:hover {{
        background: #138F83;
        border: 1px solid #138F83;
    }}
    QPushButton[buttonRole="back"]:hover, QPushButton[buttonRole="secondary"]:hover {{
        background: #F4F8FB;
    }}
    QPushButton[buttonRole="danger"]:hover {{
        background: #FFF7F7;
    }}
    QPushButton[buttonSize="small"] {{
        padding: 5px 9px;
        min-height: 24px;
        font-size: {FONT_SIZE["secondary"]}px;
    }}
    """
