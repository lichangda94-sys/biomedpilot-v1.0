from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QStackedWidget, QToolButton, QVBoxLayout, QWidget

from app.app_identity import SETTINGS_RESOURCE_ICON_PATHS, icon_asset_statuses, icon_asset_summary, load_settings_resource_pixmap
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
    root.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
    root.setSpacing(SPACING["lg"])

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
    grid = QGridLayout()
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(SPACING["lg"])
    grid.setVerticalSpacing(SPACING["lg"])
    grid.addWidget(_settings_preferences_card(profile), 0, 0)
    grid.addWidget(_settings_external_capability_overview_card(), 0, 1)
    grid.addWidget(_settings_system_info_card(profile), 1, 0)
    grid.setColumnStretch(0, 3)
    grid.setColumnStretch(1, 2)
    root.addLayout(grid)
    root.addWidget(_settings_quick_actions_panel())
    root.addStretch(1)
    return page


def _settings_preferences_card(profile: SettingsProfile) -> QFrame:
    card = make_workbench_card(object_name="settingsGeneralPreferencesPanel", semantic_state="available")
    card.setProperty("uiPrimitive", "settings_preferences_card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title("通用偏好", "用户可操作的全局偏好入口。"))
    for title, body, value, status_key in (
        ("界面与语言", "设置界面语言、主题和字体大小", f"{profile.language} · 浅色主题", "available"),
        ("数据与存储", "设置默认路径、缓存与临时文件", profile.default_project_path, "testing"),
        ("行为与启动", "设置启动行为、更新与通知偏好", "启动到工作台", "planned"),
        ("隐私与安全", "日志级别、数据匿名化与隐私选项", "日志级别：信息", "available"),
    ):
        layout.addWidget(_settings_row(title, body, value, status_key=status_key))
    return card


def _settings_row(title: str, body: str, value: str, *, status_key: str) -> QFrame:
    row = QFrame()
    row.setObjectName("settingsPreferenceRow")
    row.setProperty("uiPrimitive", "settings_row")
    row.setProperty("statusKey", status_key)
    row.setStyleSheet(
        f"""
        QFrame#settingsPreferenceRow {{
            background: #FBFCFE;
            border: 1px solid {COLORS["divider"]};
            border-radius: 12px;
        }}
        """
    )
    layout = QHBoxLayout(row)
    layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
    layout.setSpacing(SPACING["md"])
    icon = QLabel(title[:1])
    icon.setObjectName("settingsRowIcon")
    icon.setFixedSize(34, 34)
    icon.setAlignment(Qt.AlignCenter)
    icon.setStyleSheet(
        f"background: {COLORS['bio_soft']}; color: {COLORS['bio']}; border-radius: 10px; font-weight: 800;"
    )
    layout.addWidget(icon)
    text_col = QVBoxLayout()
    text_col.setSpacing(2)
    title_label = QLabel(title)
    title_label.setObjectName("settingsRowTitle")
    title_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 15px; font-weight: 800;")
    body_label = QLabel(body)
    body_label.setObjectName("settingsRowDescription")
    body_label.setWordWrap(True)
    body_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['secondary']}px;")
    text_col.addWidget(title_label)
    text_col.addWidget(body_label)
    layout.addLayout(text_col, 1)
    value_label = QLabel(value)
    value_label.setObjectName("settingsRowValue")
    value_label.setWordWrap(True)
    value_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONT_SIZE['secondary']}px;")
    layout.addWidget(value_label, 0)
    layout.addWidget(make_status_chip(status_key=status_key), 0)
    return row


def _settings_external_capability_overview_card() -> QFrame:
    card = make_workbench_card(object_name="settingsExternalCapabilityOverviewCard", semantic_state="testing")
    card.setProperty("uiPrimitive", "external_capability_overview")
    card.setProperty("installAllowed", False)
    card.setProperty("downloadAllowed", False)
    card.setProperty("engineExecutionAllowed", False)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    header = QHBoxLayout()
    header.addWidget(make_section_title("外部能力检测总览", "仅显示状态与配置入口，不执行安装或引擎。"), 1)
    refresh = make_action_button("重新检测", role="secondary", enabled=False, semantic_state="disabled", disabled_reason="检测动作在后续设置阶段开放。")
    refresh.setObjectName("settingsOverviewRedetectButton")
    header.addWidget(refresh)
    layout.addLayout(header)
    for name, status_key, detail in (
        ("图像分析引擎 / Image Analysis", "available", "ImageJ/Fiji 已检测到或可配置；不在此页运行图像分析。"),
        ("PDF OCR", "available", "OCR 能力作为外部资源状态展示。"),
        ("本地语言模型 / Local LLM", "not_configured", "本地模型可选配置，未配置不影响基础工作台。"),
        ("云端 AI 服务 / Cloud AI", "blocked", "云服务未配置，当前不连接云端。"),
        ("GO / KEGG 分析资源", "planned", "资源检测与下载策略后续开放。"),
        ("R / Bioconductor", "not_configured", "可选环境，检测后由用户主动配置。"),
        ("Python / 包管理器", "available", "本地 Python runtime 可用于桌面壳层。"),
    ):
        layout.addWidget(_capability_overview_row(name, status_key, detail))
    layout.addWidget(make_info_banner("绿色：可用；蓝色/灰色：可选或需配置；红色：不可用或当前关闭。", severity="info", semantic_state="testing"))
    return card


def _capability_overview_row(name: str, status_key: str, detail: str) -> QFrame:
    row = QFrame()
    row.setObjectName("settingsCapabilityOverviewRow")
    row.setProperty("statusKey", status_key)
    row.setStyleSheet(f"QFrame#settingsCapabilityOverviewRow {{ border-bottom: 1px solid {COLORS['divider']}; background: transparent; }}")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, SPACING["xs"], 0, SPACING["xs"])
    layout.setSpacing(SPACING["sm"])
    text_col = QVBoxLayout()
    title = QLabel(name)
    title.setObjectName("settingsCapabilityOverviewTitle")
    title.setStyleSheet(f"color: {COLORS['text']}; font-weight: 750;")
    desc = QLabel(detail)
    desc.setObjectName("settingsCapabilityOverviewDetail")
    desc.setWordWrap(True)
    desc.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['caption']}px;")
    text_col.addWidget(title)
    text_col.addWidget(desc)
    layout.addLayout(text_col, 1)
    layout.addWidget(make_status_chip(status_key=status_key), 0)
    configure = make_action_button("配置", role="ghost", size="small", enabled=False, semantic_state="disabled", disabled_reason="配置入口保留，当前不执行外部能力配置。")
    configure.setObjectName("settingsCapabilityConfigureButton")
    layout.addWidget(configure, 0)
    return row


def _settings_system_info_card(profile: SettingsProfile) -> QFrame:
    card = make_workbench_card(object_name="settingsSystemInfoCard", semantic_state="available")
    card.setProperty("uiPrimitive", "system_info_card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title("系统信息", "本地测试版运行环境概览。"))
    for label, value in (
        ("应用版本", "0.1.0 internal beta (Developer Preview)"),
        ("运行模式", "本地模式"),
        ("操作系统", "macOS / 当前本机环境"),
        ("内存使用", "暂不可用"),
        ("磁盘使用", "暂不可用"),
    ):
        row = QHBoxLayout()
        key = QLabel(label)
        key.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['secondary']}px;")
        val = QLabel(value)
        val.setWordWrap(True)
        val.setStyleSheet(f"color: {COLORS['text']}; font-weight: 650;")
        row.addWidget(key)
        row.addWidget(val, 1)
        layout.addLayout(row)
    copy = make_action_button("复制系统信息", role="secondary", enabled=False, semantic_state="disabled", disabled_reason="复制动作后续开放；当前只展示系统信息布局。")
    copy.setObjectName("settingsCopySystemInfoButton")
    layout.addWidget(copy, 0, Qt.AlignLeft)
    return card


def _settings_quick_actions_panel() -> QFrame:
    panel = make_workbench_card(object_name="settingsQuickActionsPanel", semantic_state="planned")
    panel.setProperty("uiPrimitive", "quick_actions_panel")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title("快速操作", "常用设置入口；未开放动作保持禁用。"))
    row = QHBoxLayout()
    row.setSpacing(SPACING["md"])
    for title, body, status_key in (
        ("管理默认路径", "设置数据、结果与缓存路径", "testing"),
        ("检查更新", "当前已是最新版本 0.1.0", "planned"),
        ("清理缓存", "释放临时文件与缓存空间", "planned"),
        ("导出日志", "导出系统与运行日志", "planned"),
    ):
        row.addWidget(_quick_action_card(title, body, status_key=status_key), 1)
    layout.addLayout(row)
    return panel


def _quick_action_card(title: str, body: str, *, status_key: str) -> QFrame:
    card = QFrame()
    card.setObjectName("settingsQuickActionCard")
    card.setProperty("statusKey", status_key)
    card.setStyleSheet(
        f"QFrame#settingsQuickActionCard {{ background: #FFFFFF; border: 1px solid {COLORS['border']}; border-radius: 12px; }}"
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
    layout.setSpacing(SPACING["xs"])
    title_label = QLabel(title)
    title_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: 800;")
    body_label = QLabel(body)
    body_label.setWordWrap(True)
    body_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['secondary']}px;")
    layout.addWidget(title_label)
    layout.addWidget(body_label)
    layout.addWidget(make_status_chip(status_key=status_key), 0, Qt.AlignLeft)
    return card


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
