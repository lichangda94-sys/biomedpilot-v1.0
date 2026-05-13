from __future__ import annotations


COLORS = {
    "deep_navy": "#12324A",
    "teal": "#1BAE9F",
    "light_gray": "#F5F7F9",
    "white": "#FFFFFF",
    "background": "#F5F7F9",
    "surface": "#FFFFFF",
    "surface_muted": "#F8FAFC",
    "border": "#DDE3EA",
    "text": "#1F2933",
    "muted": "#6B7280",
    "bio": "#12324A",
    "bio_soft": "#EAF2F8",
    "bio_accent": "#1BAE9F",
    "meta": "#12324A",
    "meta_soft": "#F5F7F9",
    "meta_accent": "#1BAE9F",
    "warning_soft": "#FFF7E6",
    "warning": "#D99A00",
    "success": "#22A66B",
    "danger": "#D43832",
}

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
    "hero": 24,
}


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


def login_stylesheet() -> str:
    return f"""
    QWidget#loginPage {{
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
        background: {COLORS["background"]};
        color: {COLORS["text"]};
        font-size: {FONT_SIZE["body"]}px;
    }}
    QScrollArea#moduleSelectionScrollArea {{
        border: 0;
        background: {COLORS["background"]};
    }}
    QFrame#dashboardHeader, QFrame#moduleCard, QFrame#supportCard {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["lg"]}px;
    }}
    QLabel#dashboardTitle {{
        color: {COLORS["bio"]};
        font-size: 28px;
        font-weight: 800;
        background: transparent;
    }}
    QLabel#dashboardSubtitle, QLabel#sessionMetaLabel, QLabel#moduleDescription, QLabel#supportLine {{
        color: {COLORS["muted"]};
        background: transparent;
    }}
    QLabel#sessionBadge {{
        color: {COLORS["bio"]};
        background: {COLORS["bio_soft"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
        padding: 7px 10px;
        font-weight: 600;
    }}
    QLabel#previewBadge {{
        color: #0E6F66;
        background: #E7F7F5;
        border: 1px solid #BCE7E2;
        border-radius: {RADIUS["sm"]}px;
        padding: 7px 10px;
        font-weight: 600;
    }}
    QLabel#moduleTitle {{
        color: {COLORS["bio"]};
        font-size: 22px;
        font-weight: 760;
        background: transparent;
    }}
    QLabel#moduleEnglishTitle {{
        color: {COLORS["bio_accent"]};
        font-size: {FONT_SIZE["card_title"]}px;
        font-weight: 700;
        background: transparent;
    }}
    QLabel#moduleAccentLine {{
        background: {COLORS["bio_accent"]};
        border: 0;
        border-radius: 2px;
    }}
    QLabel#moduleIcon, QLabel#ui02Icon {{
        background: transparent;
        border: 0;
    }}
    QLabel#supportTitle {{
        color: {COLORS["bio"]};
        font-size: {FONT_SIZE["card_title"]}px;
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
    QPushButton#primaryButton, QPushButton#bioModuleButton, QPushButton#metaModuleButton {{
        color: #FFFFFF;
        background: {COLORS["bio"]};
        border: 1px solid {COLORS["bio"]};
        min-height: {CONTROL_HEIGHT["primary"] - 18}px;
        font-weight: 700;
    }}
    QPushButton#bioModuleButton:hover, QPushButton#metaModuleButton:hover {{
        background: #0D273B;
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
    """
