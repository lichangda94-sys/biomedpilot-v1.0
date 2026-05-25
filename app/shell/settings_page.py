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
            title="Settings / 设置中心",
            subtitle="用户偏好、外部能力状态与本地资源概览。检测优先；安装、更新、云端配置和执行能力保持关闭。",
            module_key=ModuleKey.SETTINGS.value,
            page_key="settings",
            status_widgets=[make_status_chip("Developer Preview / detect-first", status_key="developer_preview")],
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
    root.addWidget(
        make_key_value_panel(
            title="通用偏好",
            items=[
                KeyValueItem("default_project_path", "默认项目路径", profile.default_project_path, status_key="shell_only", semantic_state="shell_only"),
                KeyValueItem("language", "语言", profile.language, status_key="shell_only", semantic_state="shell_only"),
                KeyValueItem("chart_style", "图表样式", profile.chart_style, status_key="draft", semantic_state="draft"),
                KeyValueItem("export_format", "导出格式", profile.export_format, status_key="export_disabled", semantic_state="export_disabled"),
                KeyValueItem("cache_cleanup", "缓存清理", profile.cache_cleanup, status_key="planned", semantic_state="planned"),
            ],
            object_name="settingsGeneralPreferencesPanel",
        )
    )
    root.addWidget(
        make_info_banner(
            "Settings 首屏只呈现用户可理解的偏好和状态；开发者诊断已移入单独页签并默认折叠。",
            title="UI-D2 boundary",
            severity="info",
            semantic_state="shell_only",
        )
    )
    root.addStretch(1)
    return page


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
