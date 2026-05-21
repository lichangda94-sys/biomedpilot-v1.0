from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from app.shared.semantic_keys import (
    AnalysisStatusKey,
    FeatureStatusKey,
    ModuleKey,
    PageKey,
    ResourceStatusKey,
    ResultSemanticKey,
)


APP_NAME = "BioMedPilot / 医研智析"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ICON_DIR = PROJECT_ROOT / "assets" / "icons" / "app"
MODULE_ICON_DIR = PROJECT_ROOT / "assets" / "icons" / "modules"
LABTOOLS_ICON_DIR = PROJECT_ROOT / "assets" / "icons" / "labtools"
BIOINFORMATICS_PAGE_ICON_DIR = PROJECT_ROOT / "assets" / "icons" / "bioinformatics" / "pages"
META_PAGE_ICON_DIR = PROJECT_ROOT / "assets" / "icons" / "meta" / "pages"
SETTINGS_RESOURCE_ICON_DIR = PROJECT_ROOT / "assets" / "icons" / "settings" / "resources"
RESULT_REPORT_EXPORT_ICON_DIR = PROJECT_ROOT / "assets" / "icons" / "result_report_export"
EMPTY_STATE_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "empty_states"
UI01_LOGIN_ICON_DIR = PROJECT_ROOT / "assets" / "icons" / "ui01_login"
UI02_MODULE_SELECTION_ICON_DIR = PROJECT_ROOT / "assets" / "icons" / "ui02_module_selection"
UI03_PROJECT_HOME_ICON_DIR = PROJECT_ROOT / "assets" / "icons" / "ui03_project_home"
APP_ICON_PNG_PATH = APP_ICON_DIR / "biomedpilot_app_icon.png"
APP_ICON_ICNS_PATH = APP_ICON_DIR / "biomedpilot_app_icon.icns"
BIOINFORMATICS_MODULE_ICON_PATH = MODULE_ICON_DIR / "module_bioinformatics.svg"
META_ANALYSIS_MODULE_ICON_PATH = MODULE_ICON_DIR / "module_meta_analysis.svg"
LABTOOLS_MODULE_ICON_PATH = MODULE_ICON_DIR / "module_labtools.svg"
SETTINGS_MODULE_ICON_PATH = MODULE_ICON_DIR / "module_settings.svg"
MODULE_ICON_PATHS = {
    ModuleKey.BIOINFORMATICS.value: BIOINFORMATICS_MODULE_ICON_PATH,
    ModuleKey.META_ANALYSIS.value: META_ANALYSIS_MODULE_ICON_PATH,
    ModuleKey.LABTOOLS.value: LABTOOLS_MODULE_ICON_PATH,
    ModuleKey.SETTINGS.value: SETTINGS_MODULE_ICON_PATH,
    "bioinformatics": BIOINFORMATICS_MODULE_ICON_PATH,
    "meta_analysis": META_ANALYSIS_MODULE_ICON_PATH,
    "labtools": LABTOOLS_MODULE_ICON_PATH,
    "settings": SETTINGS_MODULE_ICON_PATH,
}
LABTOOLS_ICON_PATHS = {
    PageKey.LABTOOLS_GENERAL_CALCULATORS.value: LABTOOLS_ICON_DIR / "labtools_general_calculator.svg",
    PageKey.LABTOOLS_REAGENT_PREPARATION.value: LABTOOLS_ICON_DIR / "labtools_reagent_preparation.svg",
    PageKey.LABTOOLS_EXPERIMENT_MODULES.value: LABTOOLS_ICON_DIR / "labtools_experiment_modules.svg",
    PageKey.LABTOOLS_CELL_EXPERIMENTS.value: LABTOOLS_ICON_DIR / "labtools_cell_experiments.svg",
    PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value: LABTOOLS_ICON_DIR / "labtools_protein_experiments.svg",
    PageKey.LABTOOLS_NUCLEIC_ACID_EXPERIMENTS.value: LABTOOLS_ICON_DIR / "labtools_nucleic_acid_experiments.svg",
    PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value: LABTOOLS_ICON_DIR / "labtools_immuno_absorbance.svg",
    PageKey.LABTOOLS_IHC.value: LABTOOLS_ICON_DIR / "labtools_ihc.svg",
}
BIOINFORMATICS_PAGE_ICON_PATHS = {
    PageKey.BIO_PROJECT_HOME.value: BIOINFORMATICS_PAGE_ICON_DIR / "bio_page_project_home.svg",
    PageKey.BIO_DATA_SOURCE.value: BIOINFORMATICS_PAGE_ICON_DIR / "bio_page_data_source.svg",
    PageKey.BIO_DATA_CHECK_PREPARATION.value: BIOINFORMATICS_PAGE_ICON_DIR / "bio_page_data_check_preparation.svg",
    PageKey.BIO_GROUP_DESIGN.value: BIOINFORMATICS_PAGE_ICON_DIR / "bio_page_group_design.svg",
    PageKey.BIO_ANALYSIS_TASKS.value: BIOINFORMATICS_PAGE_ICON_DIR / "bio_page_analysis_tasks.svg",
    PageKey.BIO_RESULT_REPORT.value: BIOINFORMATICS_PAGE_ICON_DIR / "bio_page_result_report.svg",
    PageKey.BIO_REPORT_EXPORT.value: BIOINFORMATICS_PAGE_ICON_DIR / "bio_page_report_export.svg",
    PageKey.BIO_SETTINGS_RESOURCES.value: BIOINFORMATICS_PAGE_ICON_DIR / "bio_page_settings_resources.svg",
    PageKey.BIO_PROJECT_LOGS_TECHNICAL_DETAILS.value: BIOINFORMATICS_PAGE_ICON_DIR / "bio_page_project_logs.svg",
}
META_PAGE_ICON_PATHS = {
    PageKey.META_PROJECT_HOME.value: META_PAGE_ICON_DIR / "meta_page_project_home.svg",
    PageKey.META_QUESTION_TYPE.value: META_PAGE_ICON_DIR / "meta_page_question_meta_type.svg",
    PageKey.META_SEARCH_STRATEGY.value: META_PAGE_ICON_DIR / "meta_page_search_strategy.svg",
    PageKey.META_IMPORT_DEDUP.value: META_PAGE_ICON_DIR / "meta_page_import_deduplication.svg",
    PageKey.META_SCREENING.value: META_PAGE_ICON_DIR / "meta_page_screening.svg",
    PageKey.META_FULLTEXT_EXTRACTION.value: META_PAGE_ICON_DIR / "meta_page_fulltext_extraction.svg",
    PageKey.META_QUALITY_ASSESSMENT.value: META_PAGE_ICON_DIR / "meta_page_quality_assessment.svg",
    PageKey.META_ANALYSIS_TASKS.value: META_PAGE_ICON_DIR / "meta_page_analysis_tasks.svg",
    PageKey.META_RESULT_REPORT.value: META_PAGE_ICON_DIR / "meta_page_result_report.svg",
    PageKey.META_REPORT_EXPORT.value: META_PAGE_ICON_DIR / "meta_page_report_export.svg",
}
SETTINGS_RESOURCE_ICON_PATHS = {
    "resource_external_engine": SETTINGS_RESOURCE_ICON_DIR / "resource_external_engine.svg",
    "resource_image_analysis_engine": SETTINGS_RESOURCE_ICON_DIR / "resource_image_analysis_engine.svg",
    "resource_imagej_fiji": SETTINGS_RESOURCE_ICON_DIR / "resource_imagej_fiji.svg",
    "resource_pdf_ocr": SETTINGS_RESOURCE_ICON_DIR / "resource_pdf_ocr.svg",
    "resource_local_model": SETTINGS_RESOURCE_ICON_DIR / "resource_local_model.svg",
    "resource_cloud_ai": SETTINGS_RESOURCE_ICON_DIR / "resource_cloud_ai.svg",
    "resource_python": SETTINGS_RESOURCE_ICON_DIR / "resource_python.svg",
    "resource_r": SETTINGS_RESOURCE_ICON_DIR / "resource_r.svg",
    "resource_go": SETTINGS_RESOURCE_ICON_DIR / "resource_go.svg",
    "resource_kegg": SETTINGS_RESOURCE_ICON_DIR / "resource_kegg.svg",
    "resource_analysis_package": SETTINGS_RESOURCE_ICON_DIR / "resource_analysis_package.svg",
    "resource_plotting_package": SETTINGS_RESOURCE_ICON_DIR / "resource_plotting_package.svg",
    "resource_developer_diagnostics": SETTINGS_RESOURCE_ICON_DIR / "resource_developer_diagnostics.svg",
}
EMPTY_STATE_IMAGE_PATHS = {
    "empty_project": EMPTY_STATE_IMAGE_DIR / "empty_project.svg",
    "empty_result": EMPTY_STATE_IMAGE_DIR / "empty_result.svg",
    "empty_missing_resource": EMPTY_STATE_IMAGE_DIR / "empty_missing_resource.svg",
    "empty_blocked": EMPTY_STATE_IMAGE_DIR / "empty_blocked.svg",
    "empty_shell_only": EMPTY_STATE_IMAGE_DIR / "empty_shell_only.svg",
    "empty_preflight_only": EMPTY_STATE_IMAGE_DIR / "empty_preflight_only.svg",
}
EMPTY_STATE_SEMANTIC_IMAGE_KEYS = {
    PageKey.BIO_PROJECT_HOME.value: "empty_project",
    ResultSemanticKey.TESTING_SUMMARY_ONLY.value: "empty_result",
    ResourceStatusKey.NOT_CONFIGURED.value: "empty_missing_resource",
    FeatureStatusKey.BLOCKED.value: "empty_blocked",
    FeatureStatusKey.SHELL_ONLY.value: "empty_shell_only",
    AnalysisStatusKey.PREFLIGHT_ONLY.value: "empty_preflight_only",
}
RESULT_REPORT_EXPORT_ICON_PATHS = {
    "result_overview": RESULT_REPORT_EXPORT_ICON_DIR / "result_overview.svg",
    "result_table": RESULT_REPORT_EXPORT_ICON_DIR / "result_table.svg",
    "result_summary": RESULT_REPORT_EXPORT_ICON_DIR / "result_summary.svg",
    "report_template": RESULT_REPORT_EXPORT_ICON_DIR / "report_template.svg",
    "result_clear": RESULT_REPORT_EXPORT_ICON_DIR / "result_clear.svg",
}
UI01_LOGIN_ICON_SHEET_PATH = UI01_LOGIN_ICON_DIR / "ui01_login_icon_sheet.png"
UI01_LOGIN_ICON_PATHS = {
    "brand": UI01_LOGIN_ICON_DIR / "brand.png",
    "user": UI01_LOGIN_ICON_DIR / "user.png",
    "security": UI01_LOGIN_ICON_DIR / "security.png",
    "login": UI01_LOGIN_ICON_DIR / "login.png",
    "register": UI01_LOGIN_ICON_DIR / "register.png",
    "forgot": UI01_LOGIN_ICON_DIR / "forgot.png",
    "subscription": UI01_LOGIN_ICON_DIR / "subscription.png",
    "vip": UI01_LOGIN_ICON_DIR / "vip.png",
    "license": UI01_LOGIN_ICON_DIR / "license.png",
    "preview": UI01_LOGIN_ICON_DIR / "preview.png",
}
UI02_MODULE_SELECTION_ICON_SHEET_PATH = UI02_MODULE_SELECTION_ICON_DIR / "ui02_module_selection_icon_sheet.png"
UI02_MODULE_SELECTION_ICON_PATHS = {
    "dashboard": UI02_MODULE_SELECTION_ICON_DIR / "dashboard.png",
    "settings": UI02_MODULE_SELECTION_ICON_DIR / "settings.png",
    "developer_preview": UI02_MODULE_SELECTION_ICON_DIR / "developer_preview.png",
    "recent_projects": UI02_MODULE_SELECTION_ICON_DIR / "recent_projects.png",
    "local_environment": UI02_MODULE_SELECTION_ICON_DIR / "local_environment.png",
    "current_user": UI02_MODULE_SELECTION_ICON_DIR / "current_user.png",
    "version": UI02_MODULE_SELECTION_ICON_DIR / "version.png",
    "logout": UI02_MODULE_SELECTION_ICON_DIR / "logout.png",
    "workspace": UI02_MODULE_SELECTION_ICON_DIR / "workspace.png",
    "project_entry": UI02_MODULE_SELECTION_ICON_DIR / "project_entry.png",
}
UI03_PROJECT_HOME_ICON_SHEET_PATH = UI03_PROJECT_HOME_ICON_DIR / "ui03_project_home_icon_sheet.png"
UI03_PROJECT_HOME_ICON_PATHS = {
    "create_project": UI03_PROJECT_HOME_ICON_DIR / "create_project.png",
    "open_existing_project": UI03_PROJECT_HOME_ICON_DIR / "open_existing_project.png",
    "project_name": UI03_PROJECT_HOME_ICON_DIR / "project_name.png",
    "save_location": UI03_PROJECT_HOME_ICON_DIR / "save_location.png",
    "folder_picker": UI03_PROJECT_HOME_ICON_DIR / "folder_picker.png",
    "validation_status": UI03_PROJECT_HOME_ICON_DIR / "validation_status.png",
    "project_manifest": UI03_PROJECT_HOME_ICON_DIR / "project_manifest.png",
    "project_config": UI03_PROJECT_HOME_ICON_DIR / "project_config.png",
    "current_project_summary": UI03_PROJECT_HOME_ICON_DIR / "current_project_summary.png",
    "continue_next_step": UI03_PROJECT_HOME_ICON_DIR / "continue_next_step.png",
    "project_folder_structure": UI03_PROJECT_HOME_ICON_DIR / "project_folder_structure.png",
    "project_warning": UI03_PROJECT_HOME_ICON_DIR / "project_warning.png",
}


@dataclass(frozen=True)
class IconAssetSlot:
    key: str
    label: str
    category: str
    path: Path
    usages: tuple[str, ...]
    required: bool = True


@dataclass(frozen=True)
class IconAssetStatus:
    key: str
    label: str
    category: str
    path: Path
    generated: bool
    connected: bool
    usages: tuple[str, ...]
    state_label: str


ICON_ASSET_SLOTS: tuple[IconAssetSlot, ...] = (
    IconAssetSlot("app.main", "主 App 图标", "应用入口", APP_ICON_PNG_PATH, ("QApplication", "MainWindow", "macOS app/window icon")),
    IconAssetSlot("module.bioinformatics", "生信分析模块图标", "模块入口", BIOINFORMATICS_MODULE_ICON_PATH, ("UI-02 模块选择首页", "Sidebar module navigation")),
    IconAssetSlot("module.meta_analysis", "Meta 分析模块图标", "模块入口", META_ANALYSIS_MODULE_ICON_PATH, ("UI-02 模块选择首页", "Sidebar module navigation")),
    IconAssetSlot("module.labtools", "LabTools 模块图标", "模块入口", LABTOOLS_MODULE_ICON_PATH, ("UI-02 模块选择首页", "Sidebar module navigation")),
    IconAssetSlot("module.settings", "设置中心模块图标", "模块入口", SETTINGS_MODULE_ICON_PATH, ("Sidebar module navigation",)),
    IconAssetSlot("labtools.general_calculators", "LabTools 通用计算器图标", "LabTools", LABTOOLS_ICON_PATHS[PageKey.LABTOOLS_GENERAL_CALCULATORS.value], ("LabTools 首页一级入口",)),
    IconAssetSlot("labtools.reagent_preparation", "LabTools 试剂制备图标", "LabTools", LABTOOLS_ICON_PATHS[PageKey.LABTOOLS_REAGENT_PREPARATION.value], ("LabTools 首页一级入口",)),
    IconAssetSlot("labtools.experiment_modules", "LabTools 实验模块图标", "LabTools", LABTOOLS_ICON_PATHS[PageKey.LABTOOLS_EXPERIMENT_MODULES.value], ("LabTools 首页一级入口",)),
    IconAssetSlot("labtools.cell_experiments", "LabTools 细胞实验图标", "LabTools", LABTOOLS_ICON_PATHS[PageKey.LABTOOLS_CELL_EXPERIMENTS.value], ("LabTools 实验模块分类",)),
    IconAssetSlot("labtools.protein_experiments", "LabTools 蛋白实验图标", "LabTools", LABTOOLS_ICON_PATHS[PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value], ("LabTools 实验模块分类",)),
    IconAssetSlot("labtools.nucleic_acid_experiments", "LabTools 核酸实验图标", "LabTools", LABTOOLS_ICON_PATHS[PageKey.LABTOOLS_NUCLEIC_ACID_EXPERIMENTS.value], ("LabTools 实验模块分类",)),
    IconAssetSlot("labtools.immuno_absorbance", "LabTools 免疫与吸光度实验图标", "LabTools", LABTOOLS_ICON_PATHS[PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value], ("LabTools 实验模块分类",)),
    IconAssetSlot("labtools.ihc", "LabTools 免疫组化图标", "LabTools", LABTOOLS_ICON_PATHS[PageKey.LABTOOLS_IHC.value], ("LabTools 实验模块分类",)),
    IconAssetSlot("bio.page.project_home", "Bioinformatics 项目首页图标", "Bioinformatics 页面", BIOINFORMATICS_PAGE_ICON_PATHS[PageKey.BIO_PROJECT_HOME.value], ("Bioinformatics 目标 IA 导航",)),
    IconAssetSlot("bio.page.data_source", "Bioinformatics 数据来源图标", "Bioinformatics 页面", BIOINFORMATICS_PAGE_ICON_PATHS[PageKey.BIO_DATA_SOURCE.value], ("Bioinformatics 目标 IA 导航",)),
    IconAssetSlot("bio.page.data_check_preparation", "Bioinformatics 数据检查与准备图标", "Bioinformatics 页面", BIOINFORMATICS_PAGE_ICON_PATHS[PageKey.BIO_DATA_CHECK_PREPARATION.value], ("Bioinformatics 目标 IA 导航",)),
    IconAssetSlot("bio.page.group_design", "Bioinformatics 分组与设计图标", "Bioinformatics 页面", BIOINFORMATICS_PAGE_ICON_PATHS[PageKey.BIO_GROUP_DESIGN.value], ("Bioinformatics 目标 IA 导航",)),
    IconAssetSlot("bio.page.analysis_tasks", "Bioinformatics 分析任务图标", "Bioinformatics 页面", BIOINFORMATICS_PAGE_ICON_PATHS[PageKey.BIO_ANALYSIS_TASKS.value], ("Bioinformatics 目标 IA 导航",)),
    IconAssetSlot("bio.page.result_report", "Bioinformatics 结果与报告图标", "Bioinformatics 页面", BIOINFORMATICS_PAGE_ICON_PATHS[PageKey.BIO_RESULT_REPORT.value], ("Bioinformatics 目标 IA 导航",)),
    IconAssetSlot("bio.page.report_export", "Bioinformatics 报告导出图标", "Bioinformatics 页面", BIOINFORMATICS_PAGE_ICON_PATHS[PageKey.BIO_REPORT_EXPORT.value], ("Bioinformatics 目标 IA 导航",)),
    IconAssetSlot("bio.page.settings_resources", "Bioinformatics 设置与资源图标", "Bioinformatics 页面", BIOINFORMATICS_PAGE_ICON_PATHS[PageKey.BIO_SETTINGS_RESOURCES.value], ("Bioinformatics 辅助 IA 导航",)),
    IconAssetSlot("bio.page.project_logs_technical_details", "Bioinformatics 项目日志与技术详情图标", "Bioinformatics 页面", BIOINFORMATICS_PAGE_ICON_PATHS[PageKey.BIO_PROJECT_LOGS_TECHNICAL_DETAILS.value], ("Bioinformatics 辅助 IA 导航",)),
    IconAssetSlot("meta.page.project_home", "Meta Analysis 项目首页图标", "Meta Analysis 页面", META_PAGE_ICON_PATHS[PageKey.META_PROJECT_HOME.value], ("Meta Analysis 目标 IA 导航",)),
    IconAssetSlot("meta.page.question_meta_type", "Meta Analysis 研究问题与类型图标", "Meta Analysis 页面", META_PAGE_ICON_PATHS[PageKey.META_QUESTION_TYPE.value], ("Meta Analysis 目标 IA 导航",)),
    IconAssetSlot("meta.page.search_strategy", "Meta Analysis 检索策略图标", "Meta Analysis 页面", META_PAGE_ICON_PATHS[PageKey.META_SEARCH_STRATEGY.value], ("Meta Analysis 目标 IA 导航",)),
    IconAssetSlot("meta.page.import_dedup", "Meta Analysis 文献导入与去重图标", "Meta Analysis 页面", META_PAGE_ICON_PATHS[PageKey.META_IMPORT_DEDUP.value], ("Meta Analysis 目标 IA 导航",)),
    IconAssetSlot("meta.page.screening", "Meta Analysis 文献筛选图标", "Meta Analysis 页面", META_PAGE_ICON_PATHS[PageKey.META_SCREENING.value], ("Meta Analysis 目标 IA 导航",)),
    IconAssetSlot("meta.page.fulltext_extraction", "Meta Analysis 全文与数据提取图标", "Meta Analysis 页面", META_PAGE_ICON_PATHS[PageKey.META_FULLTEXT_EXTRACTION.value], ("Meta Analysis 目标 IA 导航",)),
    IconAssetSlot("meta.page.quality_assessment", "Meta Analysis 质量评价图标", "Meta Analysis 页面", META_PAGE_ICON_PATHS[PageKey.META_QUALITY_ASSESSMENT.value], ("Meta Analysis 目标 IA 导航",)),
    IconAssetSlot("meta.page.analysis_tasks", "Meta Analysis 统计分析图标", "Meta Analysis 页面", META_PAGE_ICON_PATHS[PageKey.META_ANALYSIS_TASKS.value], ("Meta Analysis 目标 IA 导航",)),
    IconAssetSlot("meta.page.result_report", "Meta Analysis 结果与报告图标", "Meta Analysis 页面", META_PAGE_ICON_PATHS[PageKey.META_RESULT_REPORT.value], ("Meta Analysis 目标 IA 导航",)),
    IconAssetSlot("meta.page.report_export", "Meta Analysis 报告导出图标", "Meta Analysis 页面", META_PAGE_ICON_PATHS[PageKey.META_REPORT_EXPORT.value], ("Meta Analysis 目标 IA 导航",)),
    IconAssetSlot("settings.resource.external_engine", "Settings 外部引擎资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_external_engine"], ("Settings 外部能力资源卡片",)),
    IconAssetSlot("settings.resource.image_analysis_engine", "Settings 图像分析引擎资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_image_analysis_engine"], ("Settings 外部能力资源卡片",)),
    IconAssetSlot("settings.resource.imagej_fiji", "Settings ImageJ/Fiji 资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_imagej_fiji"], ("Settings 外部能力资源卡片",)),
    IconAssetSlot("settings.resource.pdf_ocr", "Settings PDF/OCR 资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_pdf_ocr"], ("Settings 外部能力资源行",)),
    IconAssetSlot("settings.resource.local_model", "Settings 本地模型资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_local_model"], ("Settings 模型与引擎资源卡片",)),
    IconAssetSlot("settings.resource.cloud_ai", "Settings Cloud AI 资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_cloud_ai"], ("Settings 模型与引擎资源卡片",)),
    IconAssetSlot("settings.resource.python", "Settings Python 资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_python"], ("Settings 外部能力资源卡片",)),
    IconAssetSlot("settings.resource.r", "Settings R 资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_r"], ("Settings 外部能力资源卡片",)),
    IconAssetSlot("settings.resource.go", "Settings GO 资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_go"], ("Settings 分析资源卡片",)),
    IconAssetSlot("settings.resource.kegg", "Settings KEGG 资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_kegg"], ("Settings 分析资源卡片",)),
    IconAssetSlot("settings.resource.analysis_package", "Settings 分析包资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_analysis_package"], ("Settings 分析资源卡片",)),
    IconAssetSlot("settings.resource.plotting_package", "Settings 绘图包资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_plotting_package"], ("Settings 分析资源卡片",)),
    IconAssetSlot("settings.resource.developer_diagnostics", "Settings 开发者诊断资源图标", "Settings resource", SETTINGS_RESOURCE_ICON_PATHS["resource_developer_diagnostics"], ("Settings 开发者诊断折叠入口",)),
    IconAssetSlot("empty_state.project", "Empty project illustration", "Empty state", EMPTY_STATE_IMAGE_PATHS["empty_project"], ("Shared empty state primitive",)),
    IconAssetSlot("empty_state.result", "Empty result illustration", "Empty state", EMPTY_STATE_IMAGE_PATHS["empty_result"], ("Result / Report / Export empty preview",)),
    IconAssetSlot("empty_state.missing_resource", "Missing resource illustration", "Empty state", EMPTY_STATE_IMAGE_PATHS["empty_missing_resource"], ("Shared empty state primitive",)),
    IconAssetSlot("empty_state.blocked", "Blocked empty state illustration", "Empty state", EMPTY_STATE_IMAGE_PATHS["empty_blocked"], ("Shared empty state primitive",)),
    IconAssetSlot("empty_state.shell_only", "Shell-only empty state illustration", "Empty state", EMPTY_STATE_IMAGE_PATHS["empty_shell_only"], ("Shared empty state primitive",)),
    IconAssetSlot("empty_state.preflight_only", "Preflight-only empty state illustration", "Empty state", EMPTY_STATE_IMAGE_PATHS["empty_preflight_only"], ("Shared empty state primitive",)),
    IconAssetSlot("result_report_export.result_overview", "Result overview marker icon", "Result / Report / Export marker", RESULT_REPORT_EXPORT_ICON_PATHS["result_overview"], ("Result / Report / Export marker strip",)),
    IconAssetSlot("result_report_export.result_table", "Result table marker icon", "Result / Report / Export marker", RESULT_REPORT_EXPORT_ICON_PATHS["result_table"], ("Result / Report / Export marker strip",)),
    IconAssetSlot("result_report_export.result_summary", "Result summary marker icon", "Result / Report / Export marker", RESULT_REPORT_EXPORT_ICON_PATHS["result_summary"], ("Result / Report / Export marker strip",)),
    IconAssetSlot("result_report_export.report_template", "Report template marker icon", "Result / Report / Export marker", RESULT_REPORT_EXPORT_ICON_PATHS["report_template"], ("Report draft boundary marker",)),
    IconAssetSlot("result_report_export.result_clear", "Result clear helper marker icon", "Result / Report / Export marker", RESULT_REPORT_EXPORT_ICON_PATHS["result_clear"], ("Result / Report / Export disabled helper marker",)),
    IconAssetSlot("ui01.brand", "UI-01 Brand 图标", "UI-01 登录页", UI01_LOGIN_ICON_PATHS["brand"], ("UI-01 左侧品牌展示区",)),
    IconAssetSlot("ui01.user", "UI-01 User 图标", "UI-01 登录页", UI01_LOGIN_ICON_PATHS["user"], ("UI-01 用户名输入框",)),
    IconAssetSlot("ui01.security", "UI-01 Security 图标", "UI-01 登录页", UI01_LOGIN_ICON_PATHS["security"], ("UI-01 密码输入框",)),
    IconAssetSlot("ui01.login", "UI-01 Login 图标", "UI-01 登录页", UI01_LOGIN_ICON_PATHS["login"], ("UI-01 主按钮",)),
    IconAssetSlot("ui01.register", "UI-01 Register 图标", "UI-01 登录页", UI01_LOGIN_ICON_PATHS["register"], ("UI-01 注册账号占位",)),
    IconAssetSlot("ui01.forgot", "UI-01 Forgot 图标", "UI-01 登录页", UI01_LOGIN_ICON_PATHS["forgot"], ("UI-01 忘记密码占位",)),
    IconAssetSlot("ui01.license", "UI-01 License 图标", "UI-01 登录页", UI01_LOGIN_ICON_PATHS["license"], ("UI-01 当前账号等级", "后续 License 状态")),
    IconAssetSlot("ui01.vip", "UI-01 VIP 图标", "UI-01 登录页", UI01_LOGIN_ICON_PATHS["vip"], ("UI-01 订阅 / VIP 服务", "后续订阅页")),
    IconAssetSlot("ui01.subscription", "UI-01 Subscription 图标", "UI-01 登录页", UI01_LOGIN_ICON_PATHS["subscription"], ("后续订阅 / VIP 服务页",), required=False),
    IconAssetSlot("ui01.preview", "UI-01 Preview 图标", "UI-01 登录页", UI01_LOGIN_ICON_PATHS["preview"], ("后续 Developer Preview 标记", "设置中心图标状态页"), required=False),
    IconAssetSlot("ui02.dashboard", "UI-02 Dashboard 图标", "UI-02 模块选择首页", UI02_MODULE_SELECTION_ICON_PATHS["dashboard"], ("UI-02 页面标题",)),
    IconAssetSlot("ui02.settings", "UI-02 设置中心图标", "UI-02 模块选择首页", UI02_MODULE_SELECTION_ICON_PATHS["settings"], ("UI-02 本地测试信息", "设置入口按钮")),
    IconAssetSlot("ui02.developer_preview", "UI-02 Developer Preview / 测试模式图标", "UI-02 模块选择首页", UI02_MODULE_SELECTION_ICON_PATHS["developer_preview"], ("UI-02 Developer Preview 状态",)),
    IconAssetSlot("ui02.recent_projects", "UI-02 最近项目图标", "UI-02 模块选择首页", UI02_MODULE_SELECTION_ICON_PATHS["recent_projects"], ("UI-02 最近项目卡片",)),
    IconAssetSlot("ui02.local_environment", "UI-02 本地环境状态图标", "UI-02 模块选择首页", UI02_MODULE_SELECTION_ICON_PATHS["local_environment"], ("UI-02 本地环境状态",)),
    IconAssetSlot("ui02.current_user", "UI-02 当前用户图标", "UI-02 模块选择首页", UI02_MODULE_SELECTION_ICON_PATHS["current_user"], ("UI-02 当前用户 badge",)),
    IconAssetSlot("ui02.version", "UI-02 版本信息图标", "UI-02 模块选择首页", UI02_MODULE_SELECTION_ICON_PATHS["version"], ("UI-02 版本 badge",)),
    IconAssetSlot("ui02.logout", "UI-02 退出登录图标", "UI-02 模块选择首页", UI02_MODULE_SELECTION_ICON_PATHS["logout"], ("UI-02 退出登录按钮",)),
    IconAssetSlot("ui02.workspace", "UI-02 工作台图标", "UI-02 模块选择首页", UI02_MODULE_SELECTION_ICON_PATHS["workspace"], ("UI-02 模块进入按钮",)),
    IconAssetSlot("ui02.project_entry", "UI-02 项目入口图标", "UI-02 模块选择首页", UI02_MODULE_SELECTION_ICON_PATHS["project_entry"], ("UI-02 最近项目占位/项目入口",)),
    IconAssetSlot("ui03.create_project", "UI-03 创建项目图标", "UI-03 生信项目首页", UI03_PROJECT_HOME_ICON_PATHS["create_project"], ("UI-03 创建新项目卡片",)),
    IconAssetSlot("ui03.open_existing_project", "UI-03 打开现有项目图标", "UI-03 生信项目首页", UI03_PROJECT_HOME_ICON_PATHS["open_existing_project"], ("UI-03 打开已有项目卡片",)),
    IconAssetSlot("ui03.project_name", "UI-03 项目名称图标", "UI-03 生信项目首页", UI03_PROJECT_HOME_ICON_PATHS["project_name"], ("UI-03 项目名称字段",)),
    IconAssetSlot("ui03.save_location", "UI-03 保存位置图标", "UI-03 生信项目首页", UI03_PROJECT_HOME_ICON_PATHS["save_location"], ("UI-03 项目保存位置字段",)),
    IconAssetSlot("ui03.folder_picker", "UI-03 选择文件夹图标", "UI-03 生信项目首页", UI03_PROJECT_HOME_ICON_PATHS["folder_picker"], ("UI-03 文件夹选择按钮", "UI-03 打开项目文件夹")),
    IconAssetSlot("ui03.validation_status", "UI-03 项目验证状态图标", "UI-03 生信项目首页", UI03_PROJECT_HOME_ICON_PATHS["validation_status"], ("UI-03 项目合法性验证状态",)),
    IconAssetSlot("ui03.project_manifest", "UI-03 项目清单图标", "UI-03 生信项目首页", UI03_PROJECT_HOME_ICON_PATHS["project_manifest"], ("UI-03 project_manifest.json 摘要",)),
    IconAssetSlot("ui03.project_config", "UI-03 项目配置图标", "UI-03 生信项目首页", UI03_PROJECT_HOME_ICON_PATHS["project_config"], ("UI-03 project_config.json / 配置说明",)),
    IconAssetSlot("ui03.current_project_summary", "UI-03 当前项目摘要图标", "UI-03 生信项目首页", UI03_PROJECT_HOME_ICON_PATHS["current_project_summary"], ("UI-03 当前项目摘要卡片",)),
    IconAssetSlot("ui03.continue_next_step", "UI-03 继续下一步图标", "UI-03 生信项目首页", UI03_PROJECT_HOME_ICON_PATHS["continue_next_step"], ("UI-03 继续：数据来源选择按钮",)),
    IconAssetSlot("ui03.project_folder_structure", "UI-03 项目文件结构图标", "UI-03 生信项目首页", UI03_PROJECT_HOME_ICON_PATHS["project_folder_structure"], ("UI-03 项目目录结构说明",)),
    IconAssetSlot("ui03.project_warning", "UI-03 项目警告图标", "UI-03 生信项目首页", UI03_PROJECT_HOME_ICON_PATHS["project_warning"], ("UI-03 警告/错误状态",)),
    IconAssetSlot("ui04.data_source", "UI-04 数据来源图标组", "生信工作流", PROJECT_ROOT / "assets/icons/workflow/ui04_data_source.png", ("UI-04 本地/GEO/TCGA/GTEx/AI 数据入口",), required=False),
    IconAssetSlot("ui05.acquisition", "UI-05 数据获取状态图标", "生信工作流", PROJECT_ROOT / "assets/icons/workflow/ui05_acquisition_status.png", ("UI-05 acquisition plan / record / handoff",), required=False),
    IconAssetSlot("ui06.recognition", "UI-06 数据识别图标", "生信工作流", PROJECT_ROOT / "assets/icons/workflow/ui06_recognition.png", ("UI-06 文件识别表格",), required=False),
    IconAssetSlot("ui07.readiness", "UI-07 Ready 状态图标", "生信工作流", PROJECT_ROOT / "assets/icons/workflow/ui07_readiness.png", ("UI-07 Ready Dashboard",), required=False),
    IconAssetSlot("ui08.standardization", "UI-08 标准化资产图标", "生信工作流", PROJECT_ROOT / "assets/icons/workflow/ui08_standardization.png", ("UI-08 标准化资产页",), required=False),
    IconAssetSlot("ui09.workflow", "UI-09 工作流总控图标", "生信工作流", PROJECT_ROOT / "assets/icons/workflow/ui09_workflow.png", ("UI-09 工作流总控",), required=False),
    IconAssetSlot("ui10.tasks", "UI-10 分析任务中心图标", "生信工作流", PROJECT_ROOT / "assets/icons/workflow/ui10_tasks.png", ("UI-10 分析任务中心",), required=False),
    IconAssetSlot("ui11.results", "UI-11 结果浏览图标", "生信工作流", PROJECT_ROOT / "assets/icons/workflow/ui11_results.png", ("UI-11 结果浏览",), required=False),
    IconAssetSlot("ui12.report", "UI-12 报告查看图标", "生信工作流", PROJECT_ROOT / "assets/icons/workflow/ui12_report.png", ("UI-12 报告查看",), required=False),
    IconAssetSlot("ui13.settings_ai", "UI-13 设置与本地 AI 图标", "生信工作流", PROJECT_ROOT / "assets/icons/workflow/ui13_settings_ai.png", ("UI-13 设置与本地 AI 助手", "主设置中心"), required=False),
)


def load_app_icon() -> QIcon:
    for path in (APP_ICON_PNG_PATH, APP_ICON_ICNS_PATH):
        if path.exists():
            icon = QIcon(str(path))
            if not icon.isNull():
                return icon
    return QIcon()


def load_module_icon(module_key: str) -> QIcon:
    path = MODULE_ICON_PATHS.get(module_key)
    if path is None or not path.exists():
        return QIcon()
    icon = QIcon(str(path))
    return icon if not icon.isNull() else QIcon()


def load_module_pixmap(module_key: str, size: int = 72) -> QPixmap:
    icon = load_module_icon(module_key)
    return icon.pixmap(size, size) if not icon.isNull() else QPixmap()


def load_labtools_icon(semantic_key: str) -> QIcon:
    path = LABTOOLS_ICON_PATHS.get(semantic_key)
    if path is None or not path.exists():
        return QIcon()
    icon = QIcon(str(path))
    return icon if not icon.isNull() else QIcon()


def load_labtools_pixmap(semantic_key: str, size: int = 48) -> QPixmap:
    icon = load_labtools_icon(semantic_key)
    return icon.pixmap(size, size) if not icon.isNull() else QPixmap()


def load_bioinformatics_page_icon(page_key: str) -> QIcon:
    path = BIOINFORMATICS_PAGE_ICON_PATHS.get(page_key)
    if path is None or not path.exists():
        return QIcon()
    icon = QIcon(str(path))
    return icon if not icon.isNull() else QIcon()


def load_bioinformatics_page_pixmap(page_key: str, size: int = 32) -> QPixmap:
    icon = load_bioinformatics_page_icon(page_key)
    return icon.pixmap(size, size) if not icon.isNull() else QPixmap()


def load_meta_page_icon(page_key: str) -> QIcon:
    path = META_PAGE_ICON_PATHS.get(page_key)
    if path is None or not path.exists():
        return QIcon()
    icon = QIcon(str(path))
    return icon if not icon.isNull() else QIcon()


def load_meta_page_pixmap(page_key: str, size: int = 32) -> QPixmap:
    icon = load_meta_page_icon(page_key)
    return icon.pixmap(size, size) if not icon.isNull() else QPixmap()


def load_settings_resource_icon(resource_key: str) -> QIcon:
    path = SETTINGS_RESOURCE_ICON_PATHS.get(resource_key)
    if path is None or not path.exists():
        return QIcon()
    icon = QIcon(str(path))
    return icon if not icon.isNull() else QIcon()


def load_settings_resource_pixmap(resource_key: str, size: int = 32) -> QPixmap:
    icon = load_settings_resource_icon(resource_key)
    return icon.pixmap(size, size) if not icon.isNull() else QPixmap()


def empty_state_image_key_for(empty_state_key: str | None = None, semantic_key: str | None = None) -> str | None:
    if empty_state_key in EMPTY_STATE_IMAGE_PATHS:
        return empty_state_key
    if semantic_key in EMPTY_STATE_SEMANTIC_IMAGE_KEYS:
        return EMPTY_STATE_SEMANTIC_IMAGE_KEYS[semantic_key]
    return None


def load_empty_state_illustration(empty_state_key: str | None = None, *, semantic_key: str | None = None) -> QIcon:
    resolved_key = empty_state_image_key_for(empty_state_key, semantic_key)
    if resolved_key is None:
        return QIcon()
    path = EMPTY_STATE_IMAGE_PATHS.get(resolved_key)
    if path is None or not path.exists():
        return QIcon()
    icon = QIcon(str(path))
    return icon if not icon.isNull() else QIcon()


def load_empty_state_pixmap(empty_state_key: str | None = None, *, semantic_key: str | None = None, size: int = 72) -> QPixmap:
    icon = load_empty_state_illustration(empty_state_key, semantic_key=semantic_key)
    return icon.pixmap(size, size) if not icon.isNull() else QPixmap()


def load_result_report_export_icon(resource_id: str) -> QIcon:
    path = RESULT_REPORT_EXPORT_ICON_PATHS.get(resource_id)
    if path is None or not path.exists():
        return QIcon()
    icon = QIcon(str(path))
    return icon if not icon.isNull() else QIcon()


def load_result_report_export_pixmap(resource_id: str, size: int = 24) -> QPixmap:
    icon = load_result_report_export_icon(resource_id)
    return icon.pixmap(size, size) if not icon.isNull() else QPixmap()


def load_ui01_login_icon(icon_key: str) -> QIcon:
    path = UI01_LOGIN_ICON_PATHS.get(icon_key)
    if path is None or not path.exists():
        return QIcon()
    icon = QIcon(str(path))
    return icon if not icon.isNull() else QIcon()


def load_ui01_login_pixmap(icon_key: str, size: int = 72) -> QPixmap:
    icon = load_ui01_login_icon(icon_key)
    return icon.pixmap(size, size) if not icon.isNull() else QPixmap()


def load_ui02_module_selection_icon(icon_key: str) -> QIcon:
    path = UI02_MODULE_SELECTION_ICON_PATHS.get(icon_key)
    if path is None or not path.exists():
        return QIcon()
    icon = QIcon(str(path))
    return icon if not icon.isNull() else QIcon()


def load_ui02_module_selection_pixmap(icon_key: str, size: int = 32) -> QPixmap:
    icon = load_ui02_module_selection_icon(icon_key)
    return icon.pixmap(size, size) if not icon.isNull() else QPixmap()


def load_ui03_project_home_icon(icon_key: str) -> QIcon:
    path = UI03_PROJECT_HOME_ICON_PATHS.get(icon_key)
    if path is None or not path.exists():
        return QIcon()
    icon = QIcon(str(path))
    return icon if not icon.isNull() else QIcon()


def load_ui03_project_home_pixmap(icon_key: str, size: int = 32) -> QPixmap:
    icon = load_ui03_project_home_icon(icon_key)
    return icon.pixmap(size, size) if not icon.isNull() else QPixmap()


def icon_asset_statuses() -> tuple[IconAssetStatus, ...]:
    statuses = []
    for slot in ICON_ASSET_SLOTS:
        generated = slot.path.exists()
        connected = bool(slot.usages) and generated and slot.required
        if generated and connected:
            state = "已生成并接入"
        elif generated:
            state = "已生成，等待接入"
        else:
            state = "待生成"
        statuses.append(
            IconAssetStatus(
                key=slot.key,
                label=slot.label,
                category=slot.category,
                path=slot.path,
                generated=generated,
                connected=connected,
                usages=slot.usages,
                state_label=state,
            )
        )
    return tuple(statuses)


def icon_asset_summary() -> dict[str, int]:
    statuses = icon_asset_statuses()
    return {
        "total": len(statuses),
        "generated": sum(1 for item in statuses if item.generated),
        "connected": sum(1 for item in statuses if item.connected),
        "pending": sum(1 for item in statuses if not item.generated),
        "generated_waiting": sum(1 for item in statuses if item.generated and not item.connected),
    }


def apply_app_identity(app: QApplication | None = None) -> QIcon:
    icon = load_app_icon()
    target = app or QApplication.instance()
    if target is not None and not icon.isNull():
        target.setWindowIcon(icon)
        target.setApplicationDisplayName(APP_NAME)
        target.setApplicationName("BioMedPilot")
    return icon
