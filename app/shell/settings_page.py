from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QStackedWidget, QToolButton, QVBoxLayout, QWidget

from app.app_identity import SETTINGS_RESOURCE_ICON_PATHS, icon_asset_statuses, icon_asset_summary, load_settings_resource_pixmap
from app.shared.local_engines.external_engine_manager_page import ExternalEngineManagerPage
from app.shared.semantic_keys import ModuleKey, PageKey
from app.shared.settings import SettingsProfile
from app.shared.ui_components import (
    AuditLogEntry,
    EngineStatusItem,
    KeyValueItem,
    NavTab,
    SettingsResourceItem,
    make_action_button,
    make_audit_log_panel,
    make_external_engine_status_panel,
    make_info_banner,
    make_key_value_panel,
    make_page_header,
    make_section_title,
    make_secondary_nav_tabs,
    make_settings_resource_table,
    make_status_chip,
    make_workbench_card,
)
from app.shared.ui_components.primitives import diagnostic_disclosure_title
from app.ui_style_tokens import COLORS, FONT_SIZE, SPACING

SettingsPixmapLoader = Callable[[str, int], QPixmap]

SETTINGS_CENTER_TOKENS = {
    "surface": "#FFFFFF",
    "surface_subtle": "#FAFBFD",
    "border": "rgba(0, 0, 0, 0.07)",
    "divider": "rgba(0, 0, 0, 0.06)",
    "text": "#111827",
    "muted": "#6B7280",
    "faint": "#9CA3AF",
    "blue_soft": "#EEF3FF",
    "green_soft": "#F0FDF4",
    "yellow_soft": "#FFFBEB",
    "purple_soft": "#F5F3FF",
    "radius": 11,
}


def build_settings_page(
    *,
    profile: SettingsProfile | None = None,
    settings_resource_pixmap_loader: SettingsPixmapLoader = load_settings_resource_pixmap,
) -> QScrollArea:
    profile = profile or SettingsProfile()
    page = QScrollArea()
    page.setObjectName("settingsPage")
    page.setWidgetResizable(True)
    page.setProperty("moduleKey", ModuleKey.SETTINGS.value)
    page.setProperty("pageKey", "settings")
    page.setProperty("semanticKey", ModuleKey.SETTINGS.value)
    page.setProperty("usabilityRole", "scrollable_shell_page")
    page.setAccessibleName("Settings shell page")

    content = QWidget()
    content.setObjectName("settingsContent")
    content.setProperty("moduleKey", ModuleKey.SETTINGS.value)
    content.setProperty("pageKey", "settings")
    content.setProperty("semanticKey", ModuleKey.SETTINGS.value)
    content.setProperty("uiPrimitive", "page_shell")
    content.setProperty("layoutPolishNoOverlap", True)
    root = QVBoxLayout(content)
    root.setContentsMargins(21, 16, 21, 21)
    root.setSpacing(12)

    root.addWidget(
        make_page_header(
            title="设置中心 / Settings",
            subtitle="管理全局偏好、外部能力、分析资源与系统配置。",
            module_key=ModuleKey.SETTINGS.value,
            page_key="settings",
            status_widgets=[make_status_chip("Developer Preview / 本地测试版", status_key="developer_preview")],
        )
    )

    tabs = make_secondary_nav_tabs(
        [
            NavTab("general", "通用偏好"),
            NavTab("external_capabilities", "外部能力"),
            NavTab("analysis_resources", "分析资源"),
            NavTab("model_engine", "模型与引擎"),
            NavTab("developer_diagnostics", "开发者诊断"),
        ],
        active_key="general",
        object_name="settingsSecondaryNav",
    )
    stack = QStackedWidget()
    stack.setObjectName("settingsContentStack")
    stack.setProperty("uiPrimitive", "workbench_content_stack")
    stack.setProperty("layoutPolishNoOverlap", True)
    builders = (
        _build_settings_general_page,
        _build_settings_external_capabilities_page,
        _build_settings_analysis_resources_page,
        _build_settings_model_engine_page,
        _build_settings_developer_diagnostics_page,
    )
    for builder in builders:
        stack.addWidget(builder(profile, settings_resource_pixmap_loader))
    tabs.currentChanged.connect(stack.setCurrentIndex)

    root.addWidget(tabs)
    root.addWidget(stack, 1)
    root.addStretch(1)
    page.setWidget(content)
    return page


def _base_page(*, object_name: str, page_key: str, semantic_key: str) -> QWidget:
    page = QWidget()
    page.setObjectName(object_name)
    page.setProperty("moduleKey", ModuleKey.SETTINGS.value)
    page.setProperty("pageKey", page_key)
    page.setProperty("semanticKey", semantic_key)
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(SPACING["md"])
    return page


def _build_settings_general_page(profile: SettingsProfile, _pixmap_loader: SettingsPixmapLoader) -> QWidget:
    page = _base_page(object_name="settingsGeneralPage", page_key="general", semantic_key=PageKey.SETTINGS_GENERAL.value)
    root = page.layout()
    root.setSpacing(14)
    content_row = QHBoxLayout()
    content_row.setContentsMargins(0, 0, 0, 0)
    content_row.setSpacing(14)
    left_col = QVBoxLayout()
    left_col.setContentsMargins(0, 0, 0, 0)
    left_col.setSpacing(14)
    left_col.addWidget(_settings_preferences_card(profile))
    left_col.addWidget(_settings_system_info_card(profile))
    left_col.addStretch(1)
    content_row.addLayout(left_col, 0)
    content_row.addWidget(_settings_external_capability_overview_card(), 1)
    root.addLayout(content_row)
    root.addWidget(_settings_quick_actions_panel())
    root.addStretch(1)
    return page


def _settings_preferences_card(profile: SettingsProfile) -> QFrame:
    card = _settings_center_panel("settingsGeneralPreferencesPanel", width=360)
    card.setProperty("uiPrimitive", "settings_preferences_card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(_settings_panel_header("通用偏好", "General"))
    for title, body, value, icon_text, status_key in (
        ("界面与语言", "设置界面语言、主题和字体大小", f"{profile.language}   浅色主题", "A", "available"),
        ("数据与存储", "设置默认路径、缓存与临时文件", "管理路径", "D", "testing"),
        ("行为与启动", "设置启动行为、更新与通知偏好", "", "B", "planned"),
        ("隐私与安全", "日志级别、数据匿名化与隐私选项", "日志级别：信息", "S", "available"),
    ):
        layout.addWidget(_settings_row(title, body, value, icon_text=icon_text, status_key=status_key))
    return card


def _settings_row(title: str, body: str, value: str, *, icon_text: str, status_key: str) -> QFrame:
    row = QFrame()
    row.setObjectName("settingsPreferenceRow")
    row.setProperty("uiPrimitive", "settings_row")
    row.setProperty("statusKey", status_key)
    row.setStyleSheet(
        f"QFrame#settingsPreferenceRow {{ background: transparent; border-bottom: 1px solid {SETTINGS_CENTER_TOKENS['divider']}; }}"
    )
    layout = QHBoxLayout(row)
    layout.setContentsMargins(14, 10, 14, 10)
    layout.setSpacing(10)
    icon = QLabel(icon_text)
    icon.setObjectName("settingsRowIcon")
    icon.setFixedSize(28, 28)
    icon.setAlignment(Qt.AlignCenter)
    icon.setStyleSheet(
        f"background: {SETTINGS_CENTER_TOKENS['blue_soft']}; color: {COLORS['bio']}; border-radius: 8px; font-size: 11px; font-weight: 800;"
    )
    layout.addWidget(icon)
    text_col = QVBoxLayout()
    text_col.setSpacing(1)
    title_label = QLabel(title)
    title_label.setObjectName("settingsRowTitle")
    title_label.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['text']}; font-size: 13px; font-weight: 750;")
    body_label = QLabel(body)
    body_label.setObjectName("settingsRowDescription")
    body_label.setWordWrap(True)
    body_label.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['muted']}; font-size: 11px;")
    text_col.addWidget(title_label)
    text_col.addWidget(body_label)
    layout.addLayout(text_col, 1)
    if value:
        value_label = QLabel(value)
        value_label.setObjectName("settingsRowValue")
        value_label.setWordWrap(False)
        value_label.setStyleSheet(
            f"color: {SETTINGS_CENTER_TOKENS['text']}; background: {SETTINGS_CENTER_TOKENS['surface_subtle']}; "
            f"border: 1px solid {SETTINGS_CENTER_TOKENS['divider']}; border-radius: 8px; padding: 3px 8px; font-size: 11px;"
        )
        layout.addWidget(value_label, 0)
    chevron = QLabel(">")
    chevron.setObjectName("settingsRowChevron")
    chevron.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['faint']}; font-size: 14px;")
    layout.addWidget(chevron, 0)
    return row


def _settings_external_capability_overview_card() -> QFrame:
    card = _settings_center_panel("settingsExternalCapabilityOverviewCard")
    card.setProperty("uiPrimitive", "external_capability_overview")
    card.setProperty("installAllowed", False)
    card.setProperty("downloadAllowed", False)
    card.setProperty("engineExecutionAllowed", False)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(_settings_panel_header("外部能力检测总览", "External Capabilities"))
    for name, english, status_key, detail, icon_text in (
        ("图像分析引擎", "Image Analysis", "available", "ImageJ/Fiji 已检测到或可配置", "I"),
        ("PDF OCR", "OCR Engine", "available", "Tesseract 已检测到，版本：5.3.1", "O"),
        ("本地语言模型", "Local LLM", "not_configured", "Ollama 已检测到，未配置模型", "L"),
        ("云端 AI 服务", "Cloud AI", "not_configured", "未配置任何云服务，可配置 OpenAI / Claude 等", "C"),
        ("GO 分析服务", "Gene Ontology", "available", "连接正常，上次检查：2025-05-20", "G"),
        ("KEGG 分析服务", "KEGG", "available", "连接正常，上次检查：2025-05-20", "K"),
        ("R / Bioconductor", "R 环境", "available", "R 4.3.2，Bioconductor 3.18", "R"),
        ("Python / 包管理器", "Python Environment", "available", "Python 3.11.6，pip 可用", "P"),
    ):
        layout.addWidget(_capability_overview_row(name, english, status_key, detail, icon_text=icon_text))
    footer = QHBoxLayout()
    footer.setContentsMargins(17, 11, 17, 11)
    footer.setSpacing(14)
    for label, key in (("可用：可正常使用", "available"), ("可选：可配置使用", "not_configured"), ("不可用：未检测到", "blocked")):
        footer.addWidget(make_status_chip(label, status_key=key), 0)
    footer.addStretch(1)
    log = make_action_button("查看详细日志", role="ghost", size="small", enabled=False, semantic_state="disabled", disabled_reason="日志查看入口保留，当前不执行导出。")
    log.setObjectName("settingsOverviewLogButton")
    footer.addWidget(log, 0)
    layout.addLayout(footer)
    return card


def _capability_overview_row(name: str, english: str, status_key: str, detail: str, *, icon_text: str) -> QFrame:
    row = QFrame()
    row.setObjectName("settingsCapabilityOverviewRow")
    row.setProperty("statusKey", status_key)
    row.setStyleSheet(f"QFrame#settingsCapabilityOverviewRow {{ border-bottom: 1px solid {SETTINGS_CENTER_TOKENS['divider']}; background: transparent; }}")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(17, 9, 17, 9)
    layout.setSpacing(10)
    icon = QLabel(icon_text)
    icon.setObjectName("settingsCapabilityOverviewIcon")
    icon.setFixedSize(25, 25)
    icon.setAlignment(Qt.AlignCenter)
    icon.setStyleSheet(
        f"background: {SETTINGS_CENTER_TOKENS['surface_subtle']}; color: {COLORS['bio']}; border-radius: 7px; font-size: 10px; font-weight: 800;"
    )
    layout.addWidget(icon, 0)
    text_col = QVBoxLayout()
    text_col.setSpacing(0)
    title = QLabel(name)
    title.setObjectName("settingsCapabilityOverviewTitle")
    title.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['text']}; font-size: 12px; font-weight: 750;")
    desc = QLabel(detail)
    desc.setObjectName("settingsCapabilityOverviewDetail")
    desc.setWordWrap(True)
    desc.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['muted']}; font-size: 11px;")
    text_col.addWidget(title)
    english_label = QLabel(english)
    english_label.setObjectName("settingsCapabilityOverviewEnglish")
    english_label.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['faint']}; font-size: 10px;")
    text_col.addWidget(english_label)
    layout.addLayout(text_col, 2)
    layout.addWidget(make_status_chip(status_key=status_key), 0)
    layout.addWidget(desc, 1)
    configure = make_action_button("配置", role="ghost", size="small", enabled=False, semantic_state="disabled", disabled_reason="配置入口保留，当前不执行外部能力配置。")
    configure.setObjectName("settingsCapabilityConfigureButton")
    layout.addWidget(configure, 0)
    chevron = QLabel(">")
    chevron.setObjectName("settingsCapabilityChevron")
    chevron.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['faint']}; font-size: 12px;")
    layout.addWidget(chevron, 0)
    return row


def _settings_system_info_card(profile: SettingsProfile) -> QFrame:
    card = _settings_center_panel("settingsSystemInfoCard", width=360)
    card.setProperty("uiPrimitive", "system_info_card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(_settings_panel_header("系统信息", "System Info"))
    for label, value in (
        ("应用版本", "0.1.0  Developer Preview"),
        ("运行模式", "本地模式"),
        ("操作系统", "macOS / 当前本机环境"),
        ("内存使用", "暂不可用"),
        ("磁盘使用", "暂不可用"),
    ):
        row = QHBoxLayout()
        row.setContentsMargins(14, 8, 14, 8)
        row.setSpacing(8)
        key = QLabel(label)
        key.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['muted']}; font-size: 12px;")
        val = QLabel(value)
        val.setWordWrap(True)
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['text']}; font-size: 12px; font-weight: 650;")
        row.addWidget(key)
        row.addWidget(val, 1)
        layout.addLayout(row)
    copy = make_action_button("复制系统信息", role="secondary", size="small", enabled=False, semantic_state="disabled", disabled_reason="复制动作后续开放；当前只展示系统信息布局。")
    copy.setObjectName("settingsCopySystemInfoButton")
    copy_row = QHBoxLayout()
    copy_row.setContentsMargins(14, 8, 14, 14)
    copy_row.addWidget(copy, 0)
    copy_row.addStretch(1)
    layout.addLayout(copy_row)
    return card


def _settings_quick_actions_panel() -> QFrame:
    panel = _settings_center_panel("settingsQuickActionsPanel")
    panel.setProperty("uiPrimitive", "quick_actions_panel")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(_settings_panel_header("快速操作", ""))
    row = QHBoxLayout()
    row.setContentsMargins(14, 14, 14, 14)
    row.setSpacing(10)
    for title, body, status_key, icon_text, icon_bg in (
        ("管理默认路径", "设置数据、结果与缓存路径", "testing", "P", SETTINGS_CENTER_TOKENS["blue_soft"]),
        ("检查更新", "当前已是最新版本 0.1.0", "planned", "U", SETTINGS_CENTER_TOKENS["green_soft"]),
        ("清理缓存", "释放临时文件与缓存空间", "planned", "C", SETTINGS_CENTER_TOKENS["yellow_soft"]),
        ("导出日志", "导出系统与运行日志", "planned", "L", SETTINGS_CENTER_TOKENS["purple_soft"]),
    ):
        row.addWidget(_quick_action_card(title, body, status_key=status_key, icon_text=icon_text, icon_bg=icon_bg), 1)
    layout.addLayout(row)
    return panel


def _quick_action_card(title: str, body: str, *, status_key: str, icon_text: str, icon_bg: str) -> QFrame:
    card = QFrame()
    card.setObjectName("settingsQuickActionCard")
    card.setProperty("statusKey", status_key)
    card.setProperty("actionAllowed", False)
    card.setStyleSheet(
        f"QFrame#settingsQuickActionCard {{ background: {SETTINGS_CENTER_TOKENS['surface_subtle']}; border: 1px solid rgba(0, 0, 0, 0.08); border-radius: 11px; }}"
    )
    layout = QHBoxLayout(card)
    layout.setContentsMargins(15, 13, 15, 13)
    layout.setSpacing(10)
    icon = QLabel(icon_text)
    icon.setObjectName("settingsQuickActionIcon")
    icon.setFixedSize(35, 35)
    icon.setAlignment(Qt.AlignCenter)
    icon.setStyleSheet(f"background: {icon_bg}; color: {COLORS['bio']}; border-radius: 9px; font-weight: 800;")
    layout.addWidget(icon, 0)
    text_col = QVBoxLayout()
    text_col.setSpacing(1)
    title_label = QLabel(title)
    title_label.setObjectName("settingsQuickActionTitle")
    title_label.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['text']}; font-size: 12px; font-weight: 750;")
    body_label = QLabel(body)
    body_label.setObjectName("settingsQuickActionBody")
    body_label.setWordWrap(True)
    body_label.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['muted']}; font-size: 11px;")
    text_col.addWidget(title_label)
    text_col.addWidget(body_label)
    layout.addLayout(text_col, 1)
    chevron = QLabel(">")
    chevron.setObjectName("settingsQuickActionChevron")
    chevron.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['faint']}; font-size: 14px;")
    layout.addWidget(chevron, 0)
    return card


def _settings_center_panel(object_name: str, *, width: int | None = None) -> QFrame:
    panel = QFrame()
    panel.setObjectName(object_name)
    panel.setProperty("uiPrimitive", "settings_center_panel")
    panel.setProperty("designReference", "Settings Center UI Design")
    panel.setStyleSheet(
        f"""
        QFrame#{object_name} {{
            background: {SETTINGS_CENTER_TOKENS['surface']};
            border: 1px solid {SETTINGS_CENTER_TOKENS['border']};
            border-radius: {SETTINGS_CENTER_TOKENS['radius']}px;
        }}
        """
    )
    if width is not None:
        panel.setFixedWidth(width)
    return panel


def _settings_panel_header(title: str, secondary: str) -> QFrame:
    header = QFrame()
    header.setObjectName("settingsPanelHeader")
    header.setStyleSheet(f"QFrame#settingsPanelHeader {{ background: transparent; border-bottom: 1px solid {SETTINGS_CENTER_TOKENS['divider']}; }}")
    layout = QHBoxLayout(header)
    layout.setContentsMargins(14, 10, 14, 10)
    title_label = QLabel(title)
    title_label.setObjectName("settingsPanelTitle")
    title_label.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['text']}; font-size: 13px; font-weight: 800;")
    layout.addWidget(title_label)
    layout.addStretch(1)
    if secondary:
        secondary_label = QLabel(secondary)
        secondary_label.setObjectName("settingsPanelSecondary")
        secondary_label.setStyleSheet(f"color: {SETTINGS_CENTER_TOKENS['faint']}; font-size: 11px;")
        layout.addWidget(secondary_label)
    return header


def _build_settings_external_capabilities_page(_profile: SettingsProfile, pixmap_loader: SettingsPixmapLoader) -> QWidget:
    page = _base_page(
        object_name="settingsExternalCapabilitiesPage",
        page_key="external_capabilities",
        semantic_key=PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    )
    root = page.layout()
    root.addWidget(make_info_banner("检测优先：仅显示本机状态；不会自动安装、下载、更新、连接云端或执行外部引擎。", title="Detect-first", severity="info"))
    root.addWidget(
        make_external_engine_status_panel(
            title="外部能力状态",
            engines=[
                EngineStatusItem("python", "Python 环境", status_key="available", semantic_state="available", detail="Python executable / package visibility"),
                EngineStatusItem("r", "R 环境", status_key="not_configured", semantic_state="adapter_needed", detail="Rscript / R packages"),
                EngineStatusItem("imagej_fiji", "ImageJ/Fiji", status_key="not_configured", semantic_state="adapter_needed", detail="LabTools 外部图像引擎，不进入主任务页"),
                EngineStatusItem("image_engine", "外部图像分析引擎", status_key="planned", semantic_state="planned", detail="Shell placeholder only"),
            ],
            object_name="settingsExternalEngineStatusPanel",
        )
    )
    root.addWidget(ExternalEngineManagerPage())
    for title, status_key, resource_keys, details in (
        (
            "Python 环境",
            "available",
            ["resource_python"],
            [("检测目标", "Python executable / package visibility"), ("后续动作", "用户触发安装或更新，当前禁用")],
        ),
        (
            "R 环境",
            "not_configured",
            ["resource_r"],
            [("检测目标", "Rscript / R packages"), ("后续动作", "检测后提示用户安装，当前禁用")],
        ),
        (
            "ImageJ/Fiji",
            "not_configured",
            ["resource_imagej_fiji"],
            [("检测目标", "本地 ImageJ/Fiji executable"), ("归属", "LabTools 外部图像引擎，不进入主任务页")],
        ),
        (
            "外部图像分析引擎",
            "planned",
            ["resource_image_analysis_engine", "resource_external_engine", "resource_pdf_ocr"],
            [("检测目标", "engine path / version / capability manifest"), ("边界", "仅壳层占位，不连接真实引擎")],
        ),
    ):
        root.addWidget(_settings_capability_card(title, status_key=status_key, resource_keys=resource_keys, details=details, pixmap_loader=pixmap_loader))
    root.addStretch(1)
    return page


def _build_settings_analysis_resources_page(_profile: SettingsProfile, pixmap_loader: SettingsPixmapLoader) -> QWidget:
    page = _base_page(object_name="settingsAnalysisResourcesPage", page_key="analysis_resources", semantic_key=PageKey.SETTINGS_ANALYSIS_RESOURCES.value)
    root = page.layout()
    resources = (
        (
            "GO / KEGG / MSigDB 资源",
            "planned",
            ["resource_go", "resource_kegg"],
            [("检测目标", "本地资源 manifest 与版本"), ("边界", "不自动下载数据库")],
        ),
        (
            "Bioinformatics resolver / input package",
            "preflight_only",
            ["resource_analysis_package"],
            [("检测目标", "standardized repository 与 analysis input package"), ("边界", "resolver-first，未通过预检不显示正式运行承诺")],
        ),
        (
            "Report / Export templates",
            "developer_preview",
            ["resource_plotting_package"],
            [("检测目标", "Markdown / HTML / DOCX template availability"), ("边界", "报告模板多语言化后再正式开放")],
        ),
    )
    for title, status_key, resource_keys, details in resources:
        root.addWidget(_settings_capability_card(title, status_key=status_key, resource_keys=resource_keys, details=details, pixmap_loader=pixmap_loader))
    root.addWidget(
        make_settings_resource_table(
            [
                SettingsResourceItem("go", "GO resources", "Analysis", "planned", notes="No automatic download."),
                SettingsResourceItem("kegg", "KEGG resources", "Analysis", "planned", notes="No automatic download."),
                SettingsResourceItem("analysis_package", "Resolver input package", "Bioinformatics", "preflight_only", notes="Preflight only."),
                SettingsResourceItem("plotting_package", "Report/export templates", "Report", "developer_preview", notes="Report/export disabled."),
            ]
        )
    )
    root.addStretch(1)
    return page


def _build_settings_model_engine_page(profile: SettingsProfile, pixmap_loader: SettingsPixmapLoader) -> QWidget:
    page = _base_page(object_name="settingsModelEnginePage", page_key="model_engine", semantic_key=PageKey.SETTINGS_MODEL_ENGINE.value)
    root = page.layout()
    root.addWidget(
        _settings_capability_card(
            "本地 AI 模型",
            status_key="not_configured",
            resource_keys=["resource_local_model"],
            details=[("当前配置", profile.local_ai_model), ("检测目标", "local model gateway / provider availability"), ("边界", "AI suggestion 仅为辅助建议，不自动生成结论")],
            pixmap_loader=pixmap_loader,
        )
    )
    root.addWidget(
        _settings_capability_card(
            "外部云端模型配置",
            status_key="blocked",
            resource_keys=["resource_cloud_ai"],
            details=[("当前状态", "本阶段不配置云端服务"), ("后续动作", "需要安全策略、密钥策略和用户确认流程")],
            pixmap_loader=pixmap_loader,
        )
    )
    root.addStretch(1)
    return page


def _build_settings_developer_diagnostics_page(_profile: SettingsProfile, pixmap_loader: SettingsPixmapLoader) -> QWidget:
    page = _base_page(
        object_name="settingsDeveloperDiagnosticsPage",
        page_key="developer_diagnostics",
        semantic_key=PageKey.SETTINGS_DEVELOPER_DIAGNOSTICS.value,
    )
    root = page.layout()
    toggle = QToolButton()
    toggle.setObjectName("developerDiagnosticsToggle")
    toggle.setText(diagnostic_disclosure_title("Settings resources"))
    toggle.setCheckable(True)
    toggle.setChecked(False)
    toggle.setToolButtonStyle(Qt.ToolButtonTextOnly)
    root.addWidget(toggle)

    panel = QFrame()
    panel.setObjectName("developerDiagnosticsPanel")
    panel.setProperty("uiPrimitive", "developer_diagnostics_panel")
    panel.setStyleSheet("QFrame#developerDiagnosticsPanel { background: transparent; border: 0; }")
    panel.setProperty("moduleKey", ModuleKey.SETTINGS.value)
    panel.setProperty("statusKey", "developer_preview")
    panel.setProperty("diagnosticOnly", True)
    panel.setVisible(False)
    panel_layout = QVBoxLayout(panel)
    panel_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    panel_layout.setSpacing(SPACING["md"])
    panel_layout.addWidget(make_info_banner("不会安装、下载、更新或连接云端。", title="诊断信息", severity="draft", semantic_state="developer_preview"))
    panel_layout.addWidget(
        _settings_capability_card(
            "Settings resource diagnostics",
            status_key="developer_preview",
            resource_keys=["resource_developer_diagnostics"],
            details=[("用途", "仅供开发者查看本地检测槽位、图标资源状态和壳层边界。"), ("覆盖范围", "Settings 二级导航、状态标签、检测优先 UI。")],
            pixmap_loader=pixmap_loader,
        )
    )
    panel_layout.addWidget(_icon_asset_status_panel())
    panel_layout.addWidget(make_audit_log_panel(_diagnostic_entries(), title="Settings audit log"))
    toggle.toggled.connect(panel.setVisible)
    root.addWidget(panel)
    root.addStretch(1)
    return page


def _settings_capability_card(
    title: str,
    *,
    status_key: str,
    details: Sequence[tuple[str, str]],
    resource_keys: Sequence[str],
    pixmap_loader: SettingsPixmapLoader,
) -> QFrame:
    frame = make_workbench_card(object_name="settingsCapabilityCard", semantic_state=_semantic_state_for_status(status_key))
    frame.setProperty("moduleKey", ModuleKey.SETTINGS.value)
    frame.setProperty("statusKey", status_key)
    frame.setProperty("resourceKeys", tuple(resource_keys))
    frame.setProperty("detectOnly", True)
    frame.setProperty("installAllowed", False)
    frame.setProperty("downloadAllowed", False)
    frame.setProperty("cloudConfigAllowed", False)
    frame.setProperty("engineExecutionAllowed", False)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
    layout.setSpacing(SPACING["sm"])

    header = QHBoxLayout()
    header.setSpacing(SPACING["sm"])
    for resource_key in resource_keys:
        header.addWidget(_settings_resource_icon_label(resource_key, status_key=status_key, pixmap_loader=pixmap_loader))
    label = QLabel(title)
    label.setObjectName("settingsCardTitle")
    label.setProperty("moduleKey", ModuleKey.SETTINGS.value)
    label.setProperty("statusKey", status_key)
    label.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONT_SIZE['card_title']}px; font-weight: 800;")
    header.addWidget(label, 1)
    header.addWidget(make_status_chip(status_key=status_key))
    layout.addLayout(header)

    details_grid = QGridLayout()
    details_grid.setObjectName("settingsCapabilityDetails")
    details_grid.setHorizontalSpacing(SPACING["md"])
    details_grid.setVerticalSpacing(SPACING["sm"])
    for row, (name, value) in enumerate(details):
        key_label = QLabel(name)
        key_label.setObjectName("settingsFieldLabel")
        key_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['secondary']}px;")
        value_label = QLabel(value)
        value_label.setObjectName("settingsFieldValue")
        value_label.setWordWrap(True)
        value_label.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONT_SIZE['body']}px;")
        details_grid.addWidget(key_label, row, 0)
        details_grid.addWidget(value_label, row, 1)
    layout.addLayout(details_grid)

    actions = QHBoxLayout()
    detect_button = make_action_button("检测状态", role="secondary", action_key="detect_settings_resource", semantic_state="testing")
    detect_button.setObjectName("settingsDetectButton")
    detect_button.setProperty("moduleKey", ModuleKey.SETTINGS.value)
    detect_button.setProperty("statusKey", status_key)
    detect_button.setProperty("semanticKey", _semantic_key_for_resources(resource_keys))
    detect_button.setProperty("detectOnly", True)
    install_button = make_action_button(
        "安装 / 更新（检测后由用户触发）",
        role="ghost",
        semantic_state="disabled",
        action_key="install_settings_resource",
        enabled=False,
        disabled_reason="UI-D2 does not install, download, update, or configure resources.",
    )
    install_button.setObjectName("settingsInstallButton")
    install_button.setProperty("moduleKey", ModuleKey.SETTINGS.value)
    install_button.setProperty("statusKey", status_key)
    install_button.setProperty("semanticKey", _semantic_key_for_resources(resource_keys))
    cloud_button = make_action_button(
        "云端配置（未开放）",
        role="ghost",
        semantic_state="blocked",
        action_key="configure_cloud_resource",
        enabled=False,
        disabled_reason="Cloud configuration is disabled in this UI stage.",
    )
    cloud_button.setObjectName("settingsCloudConfigButton")
    cloud_button.setProperty("moduleKey", ModuleKey.SETTINGS.value)
    cloud_button.setProperty("statusKey", status_key)
    cloud_button.setProperty("semanticKey", PageKey.SETTINGS_MODEL_ENGINE.value)
    actions.addWidget(detect_button)
    actions.addWidget(install_button)
    actions.addWidget(cloud_button)
    actions.addStretch(1)
    layout.addLayout(actions)
    return frame


def _settings_resource_icon_label(resource_key: str, *, status_key: str, pixmap_loader: SettingsPixmapLoader, size: int = 28) -> QLabel:
    label = QLabel()
    label.setObjectName("settingsResourceIcon")
    label.setFixedSize(size + 8, size + 8)
    label.setProperty("moduleKey", ModuleKey.SETTINGS.value)
    label.setProperty("resourceKey", resource_key)
    label.setProperty("semanticKey", _SETTINGS_RESOURCE_SEMANTIC_KEYS.get(resource_key, ""))
    label.setProperty("statusKey", status_key)
    icon_source = SETTINGS_RESOURCE_ICON_PATHS.get(resource_key)
    pixmap = pixmap_loader(resource_key, size)
    if pixmap.isNull():
        label.setText("*")
        label.setAlignment(Qt.AlignCenter)
        label.setProperty("iconFallback", True)
    else:
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)
        label.setProperty("iconFallback", False)
    label.setProperty("iconSource", str(icon_source) if icon_source is not None else "")
    label.setToolTip(resource_key.replace("resource_", "").replace("_", " "))
    return label


def _icon_asset_status_panel() -> QFrame:
    summary = icon_asset_summary()
    rows = [
        SettingsResourceItem("icon_total", "图标槽位", "Diagnostics", "developer_preview", notes=str(summary["total"])),
        SettingsResourceItem("icon_generated", "已生成", "Diagnostics", "available", notes=str(summary["generated"])),
        SettingsResourceItem("icon_connected", "已接入", "Diagnostics", "available", notes=str(summary["connected"])),
        SettingsResourceItem("icon_waiting", "已生成待接入", "Diagnostics", "planned", notes=str(summary["generated_waiting"])),
        SettingsResourceItem("icon_pending", "待生成", "Diagnostics", "planned", notes=str(summary["pending"])),
    ]
    for item in icon_asset_statuses()[:8]:
        usages = "; ".join(item.usages) if item.usages else "未分配"
        rows.append(SettingsResourceItem(item.key, item.label, item.category, "developer_preview", notes=f"{item.state_label} / {usages}"))
    table = make_settings_resource_table(rows, object_name="settingsDeveloperResourceTable")
    table.setProperty("diagnosticOnly", True)
    wrapper = make_workbench_card(object_name="settingsDeveloperResourcePanel", semantic_state="developer_preview")
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(table)
    return wrapper


def _diagnostic_entries() -> tuple[AuditLogEntry, ...]:
    return (
        AuditLogEntry("UI-D2", "Settings", "INFO", "Diagnostics are collapsed by default.", "developer_preview"),
        AuditLogEntry("UI-D2", "Settings", "INFO", "Install, cloud, download, upload, and engine execution actions remain disabled.", "blocked"),
    )


def _semantic_state_for_status(status_key: str) -> str:
    return {
        "available": "available",
        "not_configured": "adapter_needed",
        "planned": "planned",
        "preflight_only": "preflight_only",
        "developer_preview": "testing",
        "blocked": "blocked",
        "shell_only": "shell_only",
        "export_disabled": "export_disabled",
    }.get(status_key, "draft")


def _semantic_key_for_resources(resource_keys: Sequence[str]) -> str:
    for resource_key in resource_keys:
        semantic_key = _SETTINGS_RESOURCE_SEMANTIC_KEYS.get(resource_key, "")
        if semantic_key:
            return semantic_key
    return ModuleKey.SETTINGS.value


_SETTINGS_RESOURCE_SEMANTIC_KEYS = {
    "resource_external_engine": PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    "resource_image_analysis_engine": PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    "resource_imagej_fiji": PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    "resource_pdf_ocr": PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    "resource_local_model": PageKey.SETTINGS_MODEL_ENGINE.value,
    "resource_cloud_ai": PageKey.SETTINGS_MODEL_ENGINE.value,
    "resource_python": PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    "resource_r": PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
    "resource_go": PageKey.SETTINGS_ANALYSIS_RESOURCES.value,
    "resource_kegg": PageKey.SETTINGS_ANALYSIS_RESOURCES.value,
    "resource_analysis_package": PageKey.SETTINGS_ANALYSIS_RESOURCES.value,
    "resource_plotting_package": PageKey.SETTINGS_ANALYSIS_RESOURCES.value,
    "resource_developer_diagnostics": PageKey.SETTINGS_DEVELOPER_DIAGNOSTICS.value,
}


__all__ = ["build_settings_page"]
