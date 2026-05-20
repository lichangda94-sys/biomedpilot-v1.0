from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SemanticKeyGroup(StrEnum):
    BRAND = "brand"
    NAV = "nav"
    MODULE = "module"
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
    SETTINGS = "nav.settings"
    TEST_FEEDBACK = "nav.test_feedback"
    ABOUT = "nav.about"


class ModuleKey(StrEnum):
    BIOINFORMATICS = "module.bioinformatics"
    META_ANALYSIS = "module.meta_analysis"
    LABTOOLS = "module.labtools"
    SETTINGS = "module.settings"


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
    _entry(NavKey.SETTINGS, SemanticKeyGroup.NAV, "Settings / 设置中心", "Settings navigation entry."),
    _entry(NavKey.TEST_FEEDBACK, SemanticKeyGroup.NAV, "Test Feedback / 测试反馈", "Test feedback navigation entry."),
    _entry(NavKey.ABOUT, SemanticKeyGroup.NAV, "About / 关于", "About navigation entry."),
    _entry(ModuleKey.BIOINFORMATICS, SemanticKeyGroup.MODULE, "Bioinformatics / 生信分析", "Bioinformatics module identity."),
    _entry(ModuleKey.META_ANALYSIS, SemanticKeyGroup.MODULE, "Meta Analysis / Meta 分析", "Meta Analysis module identity."),
    _entry(ModuleKey.LABTOOLS, SemanticKeyGroup.MODULE, "LabTools / 实验工具", "LabTools module identity."),
    _entry(ModuleKey.SETTINGS, SemanticKeyGroup.MODULE, "Settings / 设置中心", "Settings module identity."),
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
