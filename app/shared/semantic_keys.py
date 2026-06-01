from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SemanticKeyGroup(StrEnum):
    BRAND = "brand"
    NAV = "nav"
    MODULE = "module"
    PAGE = "page"
    STATUS = "status"
    REPORT = "report"
    EXPORT = "export"


class BrandKey(StrEnum):
    PRIMARY = "brand.primary"
    SECONDARY = "brand.secondary"


class NavKey(StrEnum):
    DASHBOARD = "nav.dashboard"
    BIOINFORMATICS = "nav.bioinformatics"
    META_ANALYSIS = "nav.meta_analysis"
    LABTOOLS = "nav.labtools"
    CENTERS = "nav.centers"
    SETTINGS = "nav.settings"
    TEST_FEEDBACK = "nav.test_feedback"
    ABOUT = "nav.about"


class ModuleKey(StrEnum):
    BIOINFORMATICS = "module.bioinformatics"
    META_ANALYSIS = "module.meta_analysis"
    LABTOOLS = "module.labtools"
    SETTINGS = "module.settings"


class PageKey(StrEnum):
    BIO_PROJECT_HOME = "bio.page.project_home"
    BIO_DATA_SOURCE = "bio.page.data_source"
    BIO_DATA_CHECK_PREPARATION = "bio.page.data_check_preparation"
    BIO_GROUP_DESIGN = "bio.page.group_design"
    BIO_ANALYSIS_TASKS = "bio.page.analysis_tasks"
    BIO_RESULT_REPORT = "bio.page.result_report"
    BIO_REPORT_EXPORT = "bio.page.report_export"
    BIO_SETTINGS_RESOURCES = "bio.page.settings_resources"
    BIO_PROJECT_LOGS_TECHNICAL_DETAILS = "bio.page.project_logs_technical_details"
    META_PROJECT_HOME = "meta.page.project_home"
    META_QUESTION_TYPE = "meta.page.question_meta_type"
    META_SEARCH_STRATEGY = "meta.page.search_strategy"
    META_IMPORT_DEDUP = "meta.page.import_dedup"
    META_SCREENING = "meta.page.screening"
    META_FULLTEXT_EXTRACTION = "meta.page.fulltext_extraction"
    META_QUALITY_ASSESSMENT = "meta.page.quality_assessment"
    META_ANALYSIS_TASKS = "meta.page.analysis_tasks"
    META_RESULT_REPORT = "meta.page.result_report"
    META_REPORT_EXPORT = "meta.page.report_export"
    META_SETTINGS = "meta.page.meta_settings"
    LABTOOLS_HOME = "labtools.page.home"
    LABTOOLS_GENERAL_CALCULATORS = "labtools.page.general_calculators"
    LABTOOLS_REAGENT_PREPARATION = "labtools.page.reagent_preparation"
    LABTOOLS_EXPERIMENT_MODULES = "labtools.page.experiment_modules"
    LABTOOLS_CELL_EXPERIMENTS = "labtools.page.cell_experiments"
    LABTOOLS_PROTEIN_EXPERIMENTS = "labtools.page.protein_experiments"
    LABTOOLS_NUCLEIC_ACID_EXPERIMENTS = "labtools.page.nucleic_acid_experiments"
    LABTOOLS_IMMUNO_ABSORBANCE = "labtools.page.immuno_absorbance"
    LABTOOLS_IHC = "labtools.page.ihc"
    SETTINGS_GENERAL = "settings.page.general"
    SETTINGS_EXTERNAL_CAPABILITIES = "settings.page.external_capabilities"
    SETTINGS_ANALYSIS_RESOURCES = "settings.page.analysis_resources"
    SETTINGS_MODEL_ENGINE = "settings.page.model_engine"
    SETTINGS_DEVELOPER_DIAGNOSTICS = "settings.page.developer_diagnostics"


class FeatureStatusKey(StrEnum):
    TESTING = "feature.status.testing"
    PLANNED = "feature.status.planned"
    SHELL_ONLY = "feature.status.shell_only"
    DEVELOPER_PREVIEW = "feature.status.developer_preview"
    BLOCKED = "feature.status.blocked"


class ResourceStatusKey(StrEnum):
    AVAILABLE = "resource.status.available"
    NOT_CONFIGURED = "resource.status.not_configured"
    PLANNED = "resource.status.planned"
    FAILED = "resource.status.failed"


class AnalysisStatusKey(StrEnum):
    PREFLIGHT_ONLY = "analysis.status.preflight_only"
    TESTING_LEVEL = "analysis.status.testing_level"
    BLOCKED = "analysis.status.blocked"


class ResultSemanticKey(StrEnum):
    IMPORTED_EXTERNAL_RESULT = "result.semantic.imported_external_result"
    FORMAL_COMPUTED_RESULT = "result.semantic.formal_computed_result"
    TESTING_SUMMARY_ONLY = "result.semantic.testing_summary_only"


class ReportStatusKey(StrEnum):
    DRAFT = "report.status.draft"
    TESTING_SUMMARY = "report.status.testing_summary"
    REPORT_READY_FUTURE = "report.status.report_ready_future"


class ReportKey(StrEnum):
    CENTER = "report.center"
    EXPORT_PANEL = "report.export_panel"
    STATUS = "report.status"


class ExportKey(StrEnum):
    MARKDOWN = "export.format.markdown"
    HTML = "export.format.html"
    DOCX = "export.format.docx"
    CSV = "export.format.csv"
    XLSX = "export.format.xlsx"


@dataclass(frozen=True)
class SemanticKey:
    key: str
    group: SemanticKeyGroup
    default_label: str
    description: str


def _entry(key: StrEnum, group: SemanticKeyGroup, default_label: str, description: str) -> SemanticKey:
    return SemanticKey(str(key), group, default_label, description)


KEY_REGISTRY: tuple[SemanticKey, ...] = (
    _entry(BrandKey.PRIMARY, SemanticKeyGroup.BRAND, "萤火虫 / Firefly", "Primary product-facing brand display."),
    _entry(BrandKey.SECONDARY, SemanticKeyGroup.BRAND, "BioMedPilot / 医研智析", "Current app, bundle, and project identity display."),
    _entry(NavKey.DASHBOARD, SemanticKeyGroup.NAV, "Dashboard", "Global dashboard entry."),
    _entry(NavKey.BIOINFORMATICS, SemanticKeyGroup.NAV, "Bioinformatics / 生信分析", "Bioinformatics workspace navigation entry."),
    _entry(NavKey.META_ANALYSIS, SemanticKeyGroup.NAV, "Meta Analysis / Meta 分析", "Meta Analysis workspace navigation entry."),
    _entry(NavKey.LABTOOLS, SemanticKeyGroup.NAV, "LabTools / 实验工具", "LabTools workspace navigation entry."),
    _entry(NavKey.CENTERS, SemanticKeyGroup.NAV, "Centers / 管理中心", "Global Project/Data/Task/Report/Environment/Packaging center entry."),
    _entry(NavKey.SETTINGS, SemanticKeyGroup.NAV, "Settings / 设置中心", "Settings navigation entry."),
    _entry(NavKey.TEST_FEEDBACK, SemanticKeyGroup.NAV, "Test Feedback / 测试反馈", "Test feedback navigation entry."),
    _entry(NavKey.ABOUT, SemanticKeyGroup.NAV, "About / 关于", "About navigation entry."),
    _entry(ModuleKey.BIOINFORMATICS, SemanticKeyGroup.MODULE, "Bioinformatics / 生信分析", "Bioinformatics module identity."),
    _entry(ModuleKey.META_ANALYSIS, SemanticKeyGroup.MODULE, "Meta Analysis / Meta 分析", "Meta Analysis module identity."),
    _entry(ModuleKey.LABTOOLS, SemanticKeyGroup.MODULE, "LabTools / 实验工具", "LabTools module identity."),
    _entry(ModuleKey.SETTINGS, SemanticKeyGroup.MODULE, "Settings / 设置中心", "Settings module identity."),
    _entry(PageKey.BIO_PROJECT_HOME, SemanticKeyGroup.PAGE, "Bio Project Home", "Bioinformatics project home page key."),
    _entry(PageKey.BIO_DATA_SOURCE, SemanticKeyGroup.PAGE, "Bio Data Source", "Bioinformatics data source page key."),
    _entry(PageKey.BIO_DATA_CHECK_PREPARATION, SemanticKeyGroup.PAGE, "Bio Data Check & Preparation", "Bioinformatics data check and preparation page key."),
    _entry(PageKey.BIO_GROUP_DESIGN, SemanticKeyGroup.PAGE, "Bio Group & Design", "Bioinformatics group and design page key."),
    _entry(PageKey.BIO_ANALYSIS_TASKS, SemanticKeyGroup.PAGE, "Bio Analysis Tasks", "Bioinformatics analysis tasks page key."),
    _entry(PageKey.BIO_RESULT_REPORT, SemanticKeyGroup.PAGE, "Bio Result & Report", "Bioinformatics result and report page key."),
    _entry(PageKey.BIO_REPORT_EXPORT, SemanticKeyGroup.PAGE, "Bio Report Export", "Bioinformatics report export page key."),
    _entry(PageKey.BIO_SETTINGS_RESOURCES, SemanticKeyGroup.PAGE, "Bio Settings Resources", "Bioinformatics settings resources page key."),
    _entry(PageKey.BIO_PROJECT_LOGS_TECHNICAL_DETAILS, SemanticKeyGroup.PAGE, "Bio Project Logs & Technical Details", "Bioinformatics logs and technical details page key."),
    _entry(PageKey.META_PROJECT_HOME, SemanticKeyGroup.PAGE, "Meta Project Home", "Meta Analysis project home page key."),
    _entry(PageKey.META_QUESTION_TYPE, SemanticKeyGroup.PAGE, "Meta Question & Type", "Meta Analysis question and type page key."),
    _entry(PageKey.META_SEARCH_STRATEGY, SemanticKeyGroup.PAGE, "Meta Search Strategy", "Meta Analysis search strategy page key."),
    _entry(PageKey.META_IMPORT_DEDUP, SemanticKeyGroup.PAGE, "Meta Import & Dedup", "Meta Analysis import and deduplication page key."),
    _entry(PageKey.META_SCREENING, SemanticKeyGroup.PAGE, "Meta Screening", "Meta Analysis screening page key."),
    _entry(PageKey.META_FULLTEXT_EXTRACTION, SemanticKeyGroup.PAGE, "Meta Full-text & Extraction", "Meta Analysis full-text and extraction page key."),
    _entry(PageKey.META_QUALITY_ASSESSMENT, SemanticKeyGroup.PAGE, "Meta Quality Assessment", "Meta Analysis quality assessment page key."),
    _entry(PageKey.META_ANALYSIS_TASKS, SemanticKeyGroup.PAGE, "Meta Analysis Tasks", "Meta Analysis tasks page key."),
    _entry(PageKey.META_RESULT_REPORT, SemanticKeyGroup.PAGE, "Meta Result & Report", "Meta Analysis result and report page key."),
    _entry(PageKey.META_REPORT_EXPORT, SemanticKeyGroup.PAGE, "Meta Report Export", "Meta Analysis report export page key."),
    _entry(PageKey.META_SETTINGS, SemanticKeyGroup.PAGE, "Meta Settings", "Meta Analysis settings page key."),
    _entry(PageKey.LABTOOLS_HOME, SemanticKeyGroup.PAGE, "LabTools Home", "LabTools shell home page key."),
    _entry(PageKey.LABTOOLS_GENERAL_CALCULATORS, SemanticKeyGroup.PAGE, "LabTools General Calculators", "LabTools general calculators page key."),
    _entry(PageKey.LABTOOLS_REAGENT_PREPARATION, SemanticKeyGroup.PAGE, "LabTools Reagent Preparation", "LabTools reagent preparation page key."),
    _entry(PageKey.LABTOOLS_EXPERIMENT_MODULES, SemanticKeyGroup.PAGE, "LabTools Experiment Modules", "LabTools experiment modules page key."),
    _entry(PageKey.LABTOOLS_CELL_EXPERIMENTS, SemanticKeyGroup.PAGE, "LabTools Cell Experiments", "LabTools cell experiments page key."),
    _entry(PageKey.LABTOOLS_PROTEIN_EXPERIMENTS, SemanticKeyGroup.PAGE, "LabTools Protein Experiments", "LabTools protein experiments page key."),
    _entry(PageKey.LABTOOLS_NUCLEIC_ACID_EXPERIMENTS, SemanticKeyGroup.PAGE, "LabTools Nucleic Acid Experiments", "LabTools nucleic acid experiments page key."),
    _entry(PageKey.LABTOOLS_IMMUNO_ABSORBANCE, SemanticKeyGroup.PAGE, "LabTools Immuno/Absorbance", "LabTools immuno and absorbance experiments page key."),
    _entry(PageKey.LABTOOLS_IHC, SemanticKeyGroup.PAGE, "LabTools IHC", "LabTools immunohistochemistry page key."),
    _entry(PageKey.SETTINGS_GENERAL, SemanticKeyGroup.PAGE, "Settings General", "Settings general page key."),
    _entry(PageKey.SETTINGS_EXTERNAL_CAPABILITIES, SemanticKeyGroup.PAGE, "Settings External Capabilities", "Settings external capabilities page key."),
    _entry(PageKey.SETTINGS_ANALYSIS_RESOURCES, SemanticKeyGroup.PAGE, "Settings Analysis Resources", "Settings analysis resources page key."),
    _entry(PageKey.SETTINGS_MODEL_ENGINE, SemanticKeyGroup.PAGE, "Settings Model & Engine", "Settings model and engine page key."),
    _entry(PageKey.SETTINGS_DEVELOPER_DIAGNOSTICS, SemanticKeyGroup.PAGE, "Settings Developer Diagnostics", "Settings developer diagnostics page key."),
    _entry(FeatureStatusKey.TESTING, SemanticKeyGroup.STATUS, "测试中", "Feature is testable but not formal production capability."),
    _entry(FeatureStatusKey.PLANNED, SemanticKeyGroup.STATUS, "后续开放", "Feature is planned and should not appear as runnable."),
    _entry(FeatureStatusKey.SHELL_ONLY, SemanticKeyGroup.STATUS, "Shell only", "UI shell exists without business implementation."),
    _entry(FeatureStatusKey.DEVELOPER_PREVIEW, SemanticKeyGroup.STATUS, "Developer Preview", "Feature is visible for preview or developer testing."),
    _entry(FeatureStatusKey.BLOCKED, SemanticKeyGroup.STATUS, "已阻塞", "Feature is blocked by missing dependency or precondition."),
    _entry(ResourceStatusKey.AVAILABLE, SemanticKeyGroup.STATUS, "可用", "Local resource is detected and available."),
    _entry(ResourceStatusKey.NOT_CONFIGURED, SemanticKeyGroup.STATUS, "未配置", "Local resource is not configured."),
    _entry(ResourceStatusKey.PLANNED, SemanticKeyGroup.STATUS, "后续开放", "Resource integration is planned."),
    _entry(ResourceStatusKey.FAILED, SemanticKeyGroup.STATUS, "失败", "Resource detection failed."),
    _entry(AnalysisStatusKey.PREFLIGHT_ONLY, SemanticKeyGroup.STATUS, "仅预检", "Analysis surface can run preflight only."),
    _entry(AnalysisStatusKey.TESTING_LEVEL, SemanticKeyGroup.STATUS, "测试级", "Analysis output is testing-level, not formal result."),
    _entry(AnalysisStatusKey.BLOCKED, SemanticKeyGroup.STATUS, "已阻塞", "Analysis is blocked by missing resolver, input, or dependency."),
    _entry(ResultSemanticKey.IMPORTED_EXTERNAL_RESULT, SemanticKeyGroup.STATUS, "外部导入结果", "Result was imported and not recomputed by BioMedPilot."),
    _entry(ResultSemanticKey.FORMAL_COMPUTED_RESULT, SemanticKeyGroup.STATUS, "正式计算结果", "Future formal result computed by BioMedPilot-controlled workflow."),
    _entry(ResultSemanticKey.TESTING_SUMMARY_ONLY, SemanticKeyGroup.STATUS, "测试摘要", "Result is only a testing summary."),
    _entry(ReportStatusKey.DRAFT, SemanticKeyGroup.REPORT, "草稿", "Report is a draft."),
    _entry(ReportStatusKey.TESTING_SUMMARY, SemanticKeyGroup.REPORT, "测试摘要", "Report is a testing summary, not a formal report."),
    _entry(ReportStatusKey.REPORT_READY_FUTURE, SemanticKeyGroup.REPORT, "未来正式报告", "Report-ready status is reserved for future formal workflow."),
    _entry(ReportKey.CENTER, SemanticKeyGroup.REPORT, "Report Center / 报告中心", "Report center shell key."),
    _entry(ReportKey.EXPORT_PANEL, SemanticKeyGroup.REPORT, "Export / 导出", "Report export panel key."),
    _entry(ReportKey.STATUS, SemanticKeyGroup.REPORT, "Report status", "Report status namespace key."),
    _entry(ExportKey.MARKDOWN, SemanticKeyGroup.EXPORT, "Markdown", "Markdown export format key."),
    _entry(ExportKey.HTML, SemanticKeyGroup.EXPORT, "HTML", "HTML export format key."),
    _entry(ExportKey.DOCX, SemanticKeyGroup.EXPORT, "DOCX", "DOCX export format key."),
    _entry(ExportKey.CSV, SemanticKeyGroup.EXPORT, "CSV", "CSV export format key."),
    _entry(ExportKey.XLSX, SemanticKeyGroup.EXPORT, "XLSX", "XLSX export format key."),
)

_KEY_BY_VALUE = {entry.key: entry for entry in KEY_REGISTRY}


def get_semantic_key(key: str | StrEnum) -> SemanticKey:
    value = str(key)
    if value not in _KEY_BY_VALUE:
        raise KeyError(f"Unknown semantic key: {value}")
    return _KEY_BY_VALUE[value]


def keys_for_group(group: SemanticKeyGroup | str) -> tuple[SemanticKey, ...]:
    group_value = group.value if isinstance(group, SemanticKeyGroup) else str(group)
    return tuple(entry for entry in KEY_REGISTRY if entry.group.value == group_value)


def semantic_key_values() -> tuple[str, ...]:
    return tuple(entry.key for entry in KEY_REGISTRY)
