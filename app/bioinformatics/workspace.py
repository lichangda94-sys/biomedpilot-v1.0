from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.shared.feature_availability import FeatureAvailability, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability
from app.shared.result_report_export_shell import make_result_report_export_adoption_panel
from app.shared.semantic_keys import AnalysisStatusKey, ModuleKey, PageKey, ReportStatusKey, ResultSemanticKey
from app.shared.ui_components.primitives import make_status_chip


def bioinformatics_features() -> list[FeatureItem]:
    return [feature_item_from_availability(feature) for feature in bioinformatics_step_features()]


def bioinformatics_step_features() -> list[FeatureAvailability]:
    step_ids = {
        "bio-data-import",
        "bio-download",
        "bio-asset-detection",
        "bio-cleaning",
        "bio-sample-groups",
    }
    return [feature for feature in list_features("bioinformatics") if feature.feature_id in step_ids]


@dataclass(frozen=True)
class BioinformaticsIAPage:
    key: str
    label: str
    status_key: str
    semantic_key: str
    boundary: str
    page_group: str
    flow_index: int


@dataclass(frozen=True)
class BioinformaticsLegacyRoute:
    route_key: str
    widget_name: str
    target_page_key: str
    legacy_status: str
    visibility: str
    boundary: str


def bioinformatics_target_ia_pages() -> tuple[BioinformaticsIAPage, ...]:
    return (
        BioinformaticsIAPage(
            "project_home",
            "Project Home / 项目首页",
            "shell_only",
            "feature.status.shell_only",
            "项目创建、打开和项目状态汇总；不执行分析。",
            "main_flow",
            1,
        ),
        BioinformaticsIAPage(
            "data_source",
            "Data Source / 数据来源",
            "testing",
            "feature.status.testing",
            "GEO、本地导入与后续 TCGA/GTEx 入口；TCGA+GTEx 不自动合并。",
            "main_flow",
            2,
        ),
        BioinformaticsIAPage(
            "data_check_preparation",
            "Data Check & Preparation / 数据检查与准备",
            "preflight_only",
            AnalysisStatusKey.PREFLIGHT_ONLY.value,
            "resolver-first / preflight-first；未形成 standardized repository 与 analysis input package 前不开放正式分析。",
            "main_flow",
            3,
        ),
        BioinformaticsIAPage(
            "group_design",
            "Group & Design / 分组与设计",
            "preflight_only",
            AnalysisStatusKey.PREFLIGHT_ONLY.value,
            "服务 DEG、GSEA/ORA、相关性、生存与临床关联；不是 DEG 专属页面。",
            "main_flow",
            4,
        ),
        BioinformaticsIAPage(
            "analysis_tasks",
            "Analysis Tasks / 分析任务",
            "blocked",
            AnalysisStatusKey.BLOCKED.value,
            "只显示 gated 任务卡；不得把预检包装成正式 DEG/GSEA/生存分析执行。",
            "main_flow",
            5,
        ),
        BioinformaticsIAPage(
            "result_report",
            "Result & Report / 结果与报告",
            "testing",
            ResultSemanticKey.TESTING_SUMMARY_ONLY.value,
            "单次任务结果与报告草稿入口；区分 imported_external_result 与未来 formal_computed_result，不生成假结果或假图。",
            "main_flow",
            6,
        ),
        BioinformaticsIAPage(
            "report_export",
            "Report Export / 报告导出",
            "draft",
            ReportStatusKey.TESTING_SUMMARY.value,
            "仅允许测试摘要和报告草稿边界；不声明 report-ready 正式报告。",
            "main_flow",
            7,
        ),
        BioinformaticsIAPage(
            "settings_resources",
            "Bioinformatics Settings / 生信设置",
            "shell_only",
            "resource.status.not_configured",
            "GO/KEGG/MSigDB、R/Python 包和外部资源检测归 Settings 管理。",
            "auxiliary",
            1,
        ),
        BioinformaticsIAPage(
            "project_logs_technical_details",
            "Project Logs & Technical Details / 项目日志与技术详情",
            "shell_only",
            "feature.status.developer_preview",
            "旧 workflow status、manifest、technical logs 和反馈包只作为开发者诊断或项目日志入口，不作为普通主流程。",
            "auxiliary",
            2,
        ),
    )


def bioinformatics_main_flow_pages() -> tuple[BioinformaticsIAPage, ...]:
    return tuple(page for page in bioinformatics_target_ia_pages() if page.page_group == "main_flow")


def bioinformatics_auxiliary_pages() -> tuple[BioinformaticsIAPage, ...]:
    return tuple(page for page in bioinformatics_target_ia_pages() if page.page_group == "auxiliary")


_BIO_PAGE_SEMANTIC_KEYS = {
    "project_home": PageKey.BIO_PROJECT_HOME.value,
    "data_source": PageKey.BIO_DATA_SOURCE.value,
    "data_check_preparation": PageKey.BIO_DATA_CHECK_PREPARATION.value,
    "group_design": PageKey.BIO_GROUP_DESIGN.value,
    "analysis_tasks": PageKey.BIO_ANALYSIS_TASKS.value,
    "result_report": PageKey.BIO_RESULT_REPORT.value,
    "report_export": PageKey.BIO_REPORT_EXPORT.value,
    "settings_resources": PageKey.BIO_SETTINGS_RESOURCES.value,
    "project_logs_technical_details": PageKey.BIO_PROJECT_LOGS_TECHNICAL_DETAILS.value,
}


def bioinformatics_legacy_routes() -> tuple[BioinformaticsLegacyRoute, ...]:
    return (
        BioinformaticsLegacyRoute(
            "project_home",
            "bioinformaticsProjectHomePage",
            "project_home",
            "target_page",
            "primary",
            "目标 Project Home；保留项目创建、打开和状态摘要，不执行分析。",
        ),
        BioinformaticsLegacyRoute(
            "data_source",
            "bioinformaticsDataSourcePage",
            "data_source",
            "target_page",
            "primary",
            "目标 Data Source；本地/GEO/TCGA/GTEx 入口保持 testing 边界。",
        ),
        BioinformaticsLegacyRoute(
            "chinese_search",
            "bioinformaticsChineseDatasetSearchPage",
            "data_source",
            "folded_into_target",
            "secondary",
            "中文研究问题检索折叠到 Data Source；不绕过数据来源登记和预检。",
        ),
        BioinformaticsLegacyRoute(
            "acquisition_status",
            "bioinformaticsAcquisitionStatusPage",
            "data_source",
            "legacy_support",
            "developer_diagnostic",
            "旧 Acquisition Status 不作为目标一级页面；只作为数据来源登记的技术详情。",
        ),
        BioinformaticsLegacyRoute(
            "recognition",
            "bioinformaticsRecognitionPage",
            "data_check_preparation",
            "folded_into_target",
            "secondary",
            "旧 Recognition 折叠到 Data Check & Preparation；必须保持 preflight-only 语义。",
        ),
        BioinformaticsLegacyRoute(
            "readiness",
            "bioinformaticsReadinessDashboardPage",
            "data_check_preparation",
            "legacy_support",
            "developer_diagnostic",
            "旧 Readiness Dashboard 不作为普通主流程入口；保留为数据准备诊断。",
        ),
        BioinformaticsLegacyRoute(
            "standardized_assets",
            "bioinformaticsStandardizedAssetsPage",
            "data_check_preparation",
            "folded_into_target",
            "secondary",
            "标准化资产页折叠到 Data Check & Preparation；正式 resolver/input package 仍受 B8.1 门控。",
        ),
        BioinformaticsLegacyRoute(
            "group_design",
            "bioinformaticsGroupComparisonDesignPage",
            "group_design",
            "target_page",
            "primary",
            "目标 Group & Design；不是 DEG 专属页面。",
        ),
        BioinformaticsLegacyRoute(
            "workflow_status",
            "bioinformaticsWorkflowStatusPage",
            "project_logs_technical_details",
            "developer_diagnostic",
            "developer_diagnostic",
            "旧 Workflow Status 只进入项目日志与技术详情，不作为目标主流程。",
        ),
        BioinformaticsLegacyRoute(
            "analysis_tasks",
            "bioinformaticsAnalysisTaskCenterPage",
            "analysis_tasks",
            "gated_target",
            "primary_gated",
            "分析任务为 gated/preflight copy；不得启用正式分析执行器。",
        ),
        BioinformaticsLegacyRoute(
            "results_browser",
            "bioinformaticsResultsBrowserPage",
            "result_report",
            "testing_summary",
            "secondary",
            "结果浏览折叠到 Result & Report；只承载 testing summary 或 imported external result，不生成假图假结果。",
        ),
        BioinformaticsLegacyRoute(
            "report_viewer",
            "bioinformaticsReportViewerPage",
            "report_export",
            "report_draft",
            "secondary",
            "旧 Report Viewer 只作为 report draft / testing summary；不声明 report-ready。",
        ),
        BioinformaticsLegacyRoute(
            "settings",
            "bioinformaticsSettingsAndLocalAIPage",
            "settings_resources",
            "settings_redirect",
            "secondary",
            "生信设置和本地 AI 资源归 Settings 管理；模块内只保留壳层指引。",
        ),
    )


try:
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
    from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget
    from app.app_identity import BIOINFORMATICS_PAGE_ICON_PATHS, load_bioinformatics_page_icon
except Exception:  # pragma: no cover - non-GUI environments import feature registry only.
    QSize = Qt = None
    QColor = QFont = QIcon = QPainter = QPen = QPixmap = None
    QFrame = QGridLayout = QHBoxLayout = QLabel = QPushButton = QSizePolicy = QStackedWidget = QVBoxLayout = QWidget = None
    BIOINFORMATICS_PAGE_ICON_PATHS = {}
    load_bioinformatics_page_icon = None
    _WORKSPACE_IMPORT_ERROR: Exception | None = None
else:
    try:
        from pathlib import Path

        from app.bioinformatics.project_home import BioinformaticsProjectHomeWidget
        from app.bioinformatics.project_workspace import BioinformaticsProjectSummary
        from app.bioinformatics.workflow_pages import (
            BioinformaticsAcquisitionStatusWidget,
            BioinformaticsAnalysisTaskCenterWidget,
            BioinformaticsChineseDatasetSearchWidget,
            BioinformaticsDataSourceWidget,
            BioinformaticsDegConfigWidget,
            BioinformaticsGroupComparisonDesignWidget,
            BioinformaticsImmuneInfiltrationWidget,
            BioinformaticsImportedDegBrowserWidget,
            BioinformaticsRecognitionWidget,
            BioinformaticsReadinessDashboardWidget,
            BioinformaticsReportViewerWidget,
            BioinformaticsResultsBrowserWidget,
            BioinformaticsSettingsAndLocalAIWidget,
            BioinformaticsStandardizedAssetsWidget,
            BioinformaticsWorkflowStatusWidget,
        )
    except Exception as exc:  # pragma: no cover - exercised when business pages are unavailable.
        _WORKSPACE_IMPORT_ERROR = exc
    else:
        _WORKSPACE_IMPORT_ERROR = None


if QWidget is not None and _WORKSPACE_IMPORT_ERROR is None:
    BIO_HOME_TOKENS = {
        "color": {
            "page_bg": "#F3F6FA",
            "card_bg": "#FFFFFF",
            "card_border": "#D8E1EC",
            "navy": "#0D2746",
            "text": "#132238",
            "muted": "#637489",
            "soft": "#F7FAFD",
            "accent": "#2F80ED",
            "accent_soft": "#EAF3FF",
            "green": "#22A06B",
            "purple": "#8B5CF6",
            "amber": "#D97706",
            "rose": "#E11D48",
        },
        "radius": {"shell": 0, "card": 16, "tile": 14, "pill": 999},
        "spacing": {"page_x": 28, "page_y": 18, "section": 16, "card": 14, "gap": 10},
        "shadow": "0 10px 24px rgba(15, 35, 60, 0.08)",
    }

    _BIO_HOME_COPY = {
        "project_home": (
            "项目首页",
            "Project Home",
            "管理项目与团队\n查看进度与关键状态",
        ),
        "data_source": (
            "数据来源",
            "Data Source",
            "连接并获取数据\n支持多种来源检索",
        ),
        "data_check_preparation": (
            "数据检查与准备",
            "Data Check & Prep",
            "完成质量检查与预处理\n构建分析数据集",
        ),
        "group_design": (
            "分组与分析设计",
            "Group & Design",
            "定义分组与比较方案\n设置协变量设计",
        ),
        "analysis_tasks": (
            "分析任务",
            "Analysis Tasks",
            "配置并提交任务\n管理队列与状态",
        ),
        "result_report": (
            "结果与报告",
            "Result & Report",
            "查看分析结果\n探索并生成报告",
        ),
        "report_export": (
            "报告导出",
            "Report Export",
            "导出报告与结果\n选择格式与模板",
        ),
        "settings_resources": (
            "生信分析设置",
            "Resources",
            "管理生信分析相关资源、参数配置、参考数据库与外部工具连接。",
        ),
        "project_logs_technical_details": (
            "项目日志与技术详情",
            "Project Logs & Details",
            "查看项目操作日志、运行记录与技术细节，支持问题排查与复现。",
        ),
    }

    _BIO_QUICK_ACCESS = (
        ("最近使用", "快速访问最近使用的项目或流程", "#2F80ED", "◷"),
        ("使用指南", "查看生信分析流程说明与示例", "#22A06B", "□"),
        ("常见问题", "查看常见问题与解决方案", "#F59E0B", "?"),
        ("意见反馈", "提出建议或报告问题", "#8B5CF6", "▱"),
    )

    _BIO_STEP_ACCENTS = {
        "project_home": ("#3B82F6", "⌂"),
        "data_source": ("#6366F1", "▤"),
        "data_check_preparation": ("#06B6D4", "✓"),
        "group_design": ("#10B981", "⋯"),
        "analysis_tasks": ("#F59E0B", "⌁"),
        "result_report": ("#8B5CF6", "▥"),
        "report_export": ("#7C3AED", "↓"),
        "settings_resources": ("#10B981", "⚙"),
        "project_logs_technical_details": ("#3B82F6", "≡"),
    }

    _BIO_FLOW_BUTTON_STYLESHEET = """
    QPushButton#bioinformaticsIANavItem {
        border: 1px solid #D8E1EC;
        border-radius: 14px;
        background: #FFFFFF;
        color: #132238;
        font-size: 12px;
        font-weight: 700;
        padding: 12px 12px;
        text-align: left;
    }
    QPushButton#bioinformaticsIANavItem:disabled {
        color: #132238;
        background: #FFFFFF;
    }
    QPushButton#bioinformaticsIANavItem[currentStep="true"] {
        border: 2px solid #2F80ED;
        background: #EAF3FF;
        color: #0D3C75;
        font-weight: 800;
    }
    QPushButton#bioinformaticsIANavItem[pageGroup="auxiliary"] {
        background: #F8FAFC;
    }
    QPushButton#bioinformaticsIANavItem[pageGroup="auxiliary"]:disabled {
        background: #F8FAFC;
    }
    QPushButton#quickAccessButton {
        border: 1px solid #E0E7EF;
        border-radius: 12px;
        background: #FFFFFF;
        color: #132238;
        font-size: 12px;
        font-weight: 700;
        padding: 10px 12px;
        text-align: left;
    }
    QPushButton#quickAccessButton:disabled {
        color: #132238;
        background: #FFFFFF;
    }
    """

    def _bio_flow_button_text(page: BioinformaticsIAPage) -> str:
        zh, en, description = _BIO_HOME_COPY[page.key]
        return f"{page.flow_index:02d}\n{zh}\n{en}\n{description}"

    def _bio_auxiliary_button_text(page: BioinformaticsIAPage) -> str:
        zh, en, description = _BIO_HOME_COPY[page.key]
        return f"{zh}\n{en}\n{description}"

    def _make_bio_target_icon(accent: str, symbol: str, *, size: int = 44, step_number: int | None = None) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        accent_color = QColor(accent)
        soft = QColor(accent)
        soft.setAlpha(32)
        painter.setBrush(soft)
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.drawRoundedRect(5, 13, size - 10, size - 10, 9, 9)
        painter.setBrush(accent_color)
        painter.drawEllipse(int(size / 2) - 11, 1, 22, 22)
        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(0, 1, size, 22, Qt.AlignCenter, str(step_number) if step_number is not None else "")
        painter.setPen(QPen(accent_color, 2))
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(0, 16, size, size - 16, Qt.AlignCenter, symbol)
        painter.end()
        icon = QIcon()
        icon.addPixmap(pixmap, QIcon.Normal)
        icon.addPixmap(pixmap, QIcon.Disabled)
        return icon

    def _apply_bio_page_icon(button: QPushButton, semantic_key: str, *, size: int, page_key: str | None = None, step_number: int | None = None) -> None:
        icon = load_bioinformatics_page_icon(semantic_key)
        if not icon.isNull():
            if page_key and page_key in _BIO_STEP_ACCENTS:
                accent, symbol = _BIO_STEP_ACCENTS[page_key]
                icon = _make_bio_target_icon(accent, symbol, size=max(42, size), step_number=step_number)
            button.setIcon(icon)
            button.setIconSize(QSize(size, size))
        button.setProperty("iconSource", str(BIOINFORMATICS_PAGE_ICON_PATHS.get(semantic_key, "")))
        button.setProperty("iconFallback", icon.isNull())

    def _refresh_dynamic_style(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _section_title(title_text: str, subtitle_text: str | None = None) -> QFrame:
        title_wrap = QFrame()
        title_wrap.setObjectName("bioinformaticsSectionTitle")
        title_wrap.setStyleSheet("QFrame#bioinformaticsSectionTitle { border: 0; background: transparent; }")
        title_layout = QHBoxLayout(title_wrap)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 15px; font-weight: 800; color: #132238;")
        title_layout.addWidget(title)
        if subtitle_text:
            subtitle = QLabel(subtitle_text)
            subtitle.setStyleSheet("font-size: 12px; font-weight: 700; color: #637489;")
            title_layout.addWidget(subtitle)
        title_layout.addStretch(1)
        return title_wrap

    class BioinformaticsWorkspaceWidget(QWidget):
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            self._current_project: BioinformaticsProjectSummary | Path | None = None
            self._legacy_routes = bioinformatics_legacy_routes()
            self._legacy_route_by_key = {route.route_key: route for route in self._legacy_routes}
            self._current_route_key = "project_home"
            self._current_target_flow_page_key = "project_home"
            self._target_ia_buttons: dict[str, QPushButton] = {}
            self._stack = QStackedWidget()
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            self._target_ia_shell = self._build_target_ia_shell()
            root.addWidget(self._target_ia_shell, 1)
            root.addWidget(self._stack, 1)
            self._project_home_page = BioinformaticsProjectHomeWidget(
                on_continue=self.show_data_source,
                on_back=on_back,
            )
            self._data_source_page = BioinformaticsDataSourceWidget(
                on_continue=self.show_readiness,
                on_back=self.show_project_home,
            )
            self._data_source_page.chinese_search_requested.connect(self.show_chinese_search)
            self._chinese_search_page = BioinformaticsChineseDatasetSearchWidget(
                on_back=self.show_data_source,
                on_continue=self.show_readiness,
                on_source_registered=lambda summary: self._data_source_page.refresh_project(self._current_project),
            )
            self._acquisition_status_page = BioinformaticsAcquisitionStatusWidget(
                on_continue=self.show_readiness,
                on_back=self.show_data_source,
            )
            self._recognition_page = BioinformaticsRecognitionWidget(
                on_continue=self.show_readiness,
                on_back=self.show_data_source,
            )
            self._readiness_page = BioinformaticsReadinessDashboardWidget(
                on_continue=self.show_standardization,
                on_back=self.show_data_source,
            )
            self._standardized_assets_page = BioinformaticsStandardizedAssetsWidget(
                on_continue=self.show_analysis_tasks,
                on_back=self.show_readiness,
            )
            self._group_design_page = BioinformaticsGroupComparisonDesignWidget(
                on_continue=self.show_analysis_tasks,
                on_back=self.show_standardization,
            )
            self._workflow_status_page = BioinformaticsWorkflowStatusWidget(
                on_continue=self.show_analysis_tasks,
                on_back=self.show_project_home,
            )
            self._analysis_task_page = BioinformaticsAnalysisTaskCenterWidget(
                on_continue=self.show_results_browser,
                on_back=self.show_standardization,
                on_configure_deg=self.show_deg_config,
                on_view_imported_deg=self.show_imported_deg_browser,
                on_configure_immune_scoring=self.show_immune_scoring,
            )
            self._deg_config_page = BioinformaticsDegConfigWidget(
                on_back=self.show_analysis_tasks,
            )
            self._immune_scoring_page = BioinformaticsImmuneInfiltrationWidget(
                on_back=self.show_analysis_tasks,
            )
            self._imported_deg_page = BioinformaticsImportedDegBrowserWidget(
                on_back=self.show_results_browser,
                on_report=self.show_report_viewer,
            )
            self._results_browser_page = BioinformaticsResultsBrowserWidget(
                on_continue=self.show_report_viewer,
                on_back=self.show_analysis_tasks,
                on_view_imported_deg=self.show_imported_deg_browser,
            )
            self._report_viewer_page = BioinformaticsReportViewerWidget(
                on_back=self.show_results_browser,
            )
            self._settings_page = BioinformaticsSettingsAndLocalAIWidget(
                on_back=self.show_project_home,
            )
            for page in (
                self._project_home_page,
                self._data_source_page,
                self._chinese_search_page,
                self._acquisition_status_page,
                self._recognition_page,
                self._readiness_page,
                self._standardized_assets_page,
                self._group_design_page,
                self._workflow_status_page,
                self._analysis_task_page,
                self._deg_config_page,
                self._immune_scoring_page,
                self._imported_deg_page,
                self._results_browser_page,
                self._report_viewer_page,
                self._settings_page,
            ):
                self._stack.addWidget(page)
            self._apply_legacy_route_properties()
            self._stack.setCurrentWidget(self._project_home_page)
            self._set_current_route("project_home")

        def target_ia_page_keys(self) -> tuple[str, ...]:
            return tuple(page.key for page in bioinformatics_target_ia_pages())

        def main_flow_page_keys(self) -> tuple[str, ...]:
            return tuple(page.key for page in bioinformatics_main_flow_pages())

        def auxiliary_page_keys(self) -> tuple[str, ...]:
            return tuple(page.key for page in bioinformatics_auxiliary_pages())

        def legacy_route_keys(self) -> tuple[str, ...]:
            return tuple(route.route_key for route in self._legacy_routes)

        def legacy_route_calibration(self) -> tuple[dict[str, str], ...]:
            return tuple(
                {
                    "route_key": route.route_key,
                    "widget_name": route.widget_name,
                    "target_page_key": route.target_page_key,
                    "legacy_status": route.legacy_status,
                    "visibility": route.visibility,
                    "boundary": route.boundary,
                }
                for route in self._legacy_routes
            )

        def _build_target_ia_shell(self) -> QFrame:
            tokens = BIO_HOME_TOKENS
            frame = QFrame()
            frame.setObjectName("bioinformaticsTargetIAShell")
            frame.setStyleSheet(
                "QFrame#bioinformaticsTargetIAShell { "
                f"border: 0; background: {tokens['color']['page_bg']};"
                "}"
            )
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(tokens["spacing"]["page_x"], tokens["spacing"]["page_y"], tokens["spacing"]["page_x"], tokens["spacing"]["page_y"])
            layout.setSpacing(tokens["spacing"]["section"])

            header = QHBoxLayout()
            header.setSpacing(14)
            title_col = QVBoxLayout()
            title_col.setSpacing(4)
            title = QLabel("生信分析 / Bioinformatics")
            title.setObjectName("bioinformaticsIATitle")
            title.setStyleSheet(f"font-size: 24px; font-weight: 850; color: {tokens['color']['navy']};")
            subtitle = QLabel("提供生信分析全流程工具，支持从数据来源到结果解读的一站式分析与可视化。")
            subtitle.setObjectName("bioinformaticsIASubtitle")
            subtitle.setWordWrap(True)
            subtitle.setStyleSheet(f"font-size: 13px; font-weight: 500; color: {tokens['color']['muted']};")
            title_col.addWidget(title)
            title_col.addWidget(subtitle)
            header.addLayout(title_col, 1)
            header.addWidget(make_status_chip("Developer Preview / 本地测试版", status_key="developer_preview"))
            layout.addLayout(header)

            main_card = QFrame()
            main_card.setObjectName("bioinformaticsWorkflowOverviewCard")
            main_card.setStyleSheet(
                "QFrame#bioinformaticsWorkflowOverviewCard { "
                f"border: 1px solid {tokens['color']['card_border']}; "
                f"border-radius: {tokens['radius']['card']}px; "
                f"background: {tokens['color']['card_bg']};"
                "}"
            )
            main_layout = QVBoxLayout(main_card)
            main_layout.setContentsMargins(18, 16, 18, 18)
            main_layout.setSpacing(14)
            title_row = QHBoxLayout()
            title_row.setContentsMargins(0, 0, 0, 0)
            title_row.addWidget(_section_title("生信分析流程概览 / Workflow Overview"), 1)
            step_count = QLabel("7 个分析步骤")
            step_count.setObjectName("bioinformaticsStepCountBadge")
            step_count.setStyleSheet(
                "QLabel#bioinformaticsStepCountBadge { "
                "border: 1px solid #D7E3F4; border-radius: 12px; "
                "background: #F0F6FF; color: #1F5FA8; font-size: 12px; "
                "font-weight: 800; padding: 5px 10px; }"
            )
            title_row.addWidget(step_count)
            main_layout.addLayout(title_row)
            flow_stepper = QFrame()
            flow_stepper.setObjectName("bioinformaticsWorkflowStepper")
            flow_stepper.setStyleSheet("QFrame#bioinformaticsWorkflowStepper { border: 0; background: transparent; }")
            flow_stepper.setProperty("uiPrimitive", "workflow_stepper")
            flow_stepper.setProperty("orientation", "vertical")
            flow_stepper.setProperty("moduleKey", ModuleKey.BIOINFORMATICS.value)
            flow_stepper.setProperty("pageGroup", "main_flow")
            flow_stepper.setProperty("formalActionEnabled", False)
            flow_grid = QGridLayout(flow_stepper)
            flow_grid.setContentsMargins(0, 0, 0, 0)
            flow_grid.setHorizontalSpacing(tokens["spacing"]["gap"])
            flow_grid.setVerticalSpacing(tokens["spacing"]["gap"])
            for index, page in enumerate(bioinformatics_main_flow_pages()):
                item = QPushButton()
                item.setObjectName("bioinformaticsIANavItem")
                item.setText(_bio_flow_button_text(page))
                item.setCheckable(True)
                item.setMinimumHeight(108)
                item.setMinimumWidth(192)
                item.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                item.setProperty("pageKey", page.key)
                item.setProperty("pageGroup", page.page_group)
                item.setProperty("flowIndex", page.flow_index)
                item.setProperty("moduleKey", ModuleKey.BIOINFORMATICS.value)
                item.setProperty("statusKey", page.status_key)
                item.setProperty("semanticKey", _BIO_PAGE_SEMANTIC_KEYS[page.key])
                item.setProperty("statusSemanticKey", page.semantic_key)
                item.setProperty("currentStep", False)
                item.setProperty("formalActionEnabled", False)
                item.setToolTip(page.label)
                item.setStyleSheet(_BIO_FLOW_BUTTON_STYLESHEET)
                _apply_bio_page_icon(item, _BIO_PAGE_SEMANTIC_KEYS[page.key], size=44, page_key=page.key, step_number=page.flow_index)
                item.setEnabled(False)
                self._target_ia_buttons[page.key] = item
                row = 0 if index < 4 else 1
                column = index if index < 4 else index - 4
                flow_grid.addWidget(item, row, column)
                flow_grid.setColumnStretch(column, 1)
            main_layout.addWidget(flow_stepper)
            layout.addWidget(main_card)

            auxiliary_card = QFrame()
            auxiliary_card.setObjectName("bioinformaticsAuxiliaryCard")
            auxiliary_card.setStyleSheet(
                "QFrame#bioinformaticsAuxiliaryCard { "
                f"border: 1px solid {tokens['color']['card_border']}; "
                f"border-radius: {tokens['radius']['card']}px; "
                f"background: {tokens['color']['card_bg']};"
                "}"
            )
            auxiliary_layout = QVBoxLayout(auxiliary_card)
            auxiliary_layout.setContentsMargins(18, 14, 18, 18)
            auxiliary_layout.setSpacing(12)
            auxiliary_layout.addWidget(_section_title("辅助功能 / Auxiliary"))
            auxiliary_row = QHBoxLayout()
            auxiliary_row.setSpacing(tokens["spacing"]["gap"])
            for page in bioinformatics_auxiliary_pages():
                item = QPushButton(_bio_auxiliary_button_text(page))
                item.setObjectName("bioinformaticsIANavItem")
                item.setCheckable(True)
                item.setMinimumHeight(96)
                item.setMinimumWidth(180)
                item.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                item.setProperty("pageKey", page.key)
                item.setProperty("pageGroup", page.page_group)
                item.setProperty("flowIndex", page.flow_index)
                item.setProperty("moduleKey", ModuleKey.BIOINFORMATICS.value)
                item.setProperty("statusKey", page.status_key)
                item.setProperty("semanticKey", _BIO_PAGE_SEMANTIC_KEYS[page.key])
                item.setProperty("statusSemanticKey", page.semantic_key)
                item.setProperty("currentStep", False)
                item.setProperty("formalActionEnabled", False)
                item.setToolTip(page.label)
                item.setStyleSheet(_BIO_FLOW_BUTTON_STYLESHEET)
                _apply_bio_page_icon(item, _BIO_PAGE_SEMANTIC_KEYS[page.key], size=44, page_key=page.key)
                item.setEnabled(False)
                self._target_ia_buttons[page.key] = item
                auxiliary_row.addWidget(item)
            auxiliary_layout.addLayout(auxiliary_row)
            layout.addWidget(auxiliary_card)

            self._result_report_panel = make_result_report_export_adoption_panel(module="bioinformatics")
            self._result_report_panel.setProperty("moduleKey", ModuleKey.BIOINFORMATICS.value)
            self._result_report_panel.setProperty("pageKey", "result_report")
            self._result_report_panel.setProperty("semanticKey", PageKey.BIO_RESULT_REPORT.value)
            layout.addWidget(self._result_report_panel)

            quick = QFrame()
            quick.setObjectName("bioinformaticsQuickAccessCard")
            quick.setStyleSheet(
                "QFrame#bioinformaticsQuickAccessCard { "
                f"border: 1px solid {tokens['color']['card_border']}; "
                f"border-radius: {tokens['radius']['card']}px; "
                f"background: {tokens['color']['card_bg']};"
                "}"
            )
            quick_layout = QVBoxLayout(quick)
            quick_layout.setContentsMargins(18, 14, 18, 18)
            quick_layout.setSpacing(12)
            quick_layout.addWidget(_section_title("快速入口"))
            quick_row = QHBoxLayout()
            quick_row.setSpacing(tokens["spacing"]["gap"])
            for text, description, accent, symbol in _BIO_QUICK_ACCESS:
                button = QPushButton(f"{text}\n{description}")
                button.setObjectName("quickAccessButton")
                button.setProperty("moduleKey", ModuleKey.BIOINFORMATICS.value)
                button.setProperty("quickAccessKey", text)
                button.setProperty("accentColor", accent)
                button.setMinimumHeight(64)
                button.setMinimumWidth(170)
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                button.setStyleSheet(_BIO_FLOW_BUTTON_STYLESHEET)
                button.setIcon(_make_bio_target_icon(accent, symbol, size=38))
                button.setIconSize(QSize(38, 38))
                button.setEnabled(False)
                quick_row.addWidget(button)
            quick_layout.addLayout(quick_row)
            layout.addWidget(quick)
            self._sync_target_flow_state()
            return frame

        def _sync_target_flow_state(self) -> None:
            if not hasattr(self, "_target_ia_buttons"):
                return
            for key, button in self._target_ia_buttons.items():
                is_current = key == self._current_target_flow_page_key
                button.setChecked(is_current)
                button.setProperty("currentStep", is_current)
                _refresh_dynamic_style(button)
                button.setMinimumHeight(108 if button.property("pageGroup") == "main_flow" else 96)
            if hasattr(self, "_result_report_panel"):
                self._result_report_panel.setVisible(self._current_target_flow_page_key == "result_report")

        def show_project_home(self) -> None:
            self._set_current_route("project_home")
            self._stack.setCurrentWidget(self._project_home_page)

        def show_data_source(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._data_source_page.refresh_project(self._current_project)
            self._set_current_route("data_source")
            self._stack.setCurrentWidget(self._data_source_page)

        def show_acquisition_status(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._acquisition_status_page.refresh_project(self._current_project)
            self._set_current_route("acquisition_status")
            self._stack.setCurrentWidget(self._acquisition_status_page)

        def show_chinese_search(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._chinese_search_page.refresh_project(self._current_project)
            pending_query = self._data_source_page.pending_chinese_query()
            if pending_query:
                self._chinese_search_page.set_query_text(pending_query)
            self._set_current_route("chinese_search")
            self._stack.setCurrentWidget(self._chinese_search_page)

        def show_recognition(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._recognition_page.refresh_project(self._current_project)
            self._set_current_route("recognition")
            self._stack.setCurrentWidget(self._recognition_page)

        def show_readiness(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._readiness_page.refresh_project(self._current_project)
            self._set_current_route("readiness")
            self._stack.setCurrentWidget(self._readiness_page)

        def show_standardization(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._standardized_assets_page.refresh_project(self._current_project)
            self._set_current_route("standardized_assets")
            self._stack.setCurrentWidget(self._standardized_assets_page)

        def show_workflow_status(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._workflow_status_page.refresh_project(self._current_project)
            self._set_current_route("workflow_status")
            self._stack.setCurrentWidget(self._workflow_status_page)

        def show_group_design(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._group_design_page.refresh_project(self._current_project)
            self._set_current_route("group_design")
            self._stack.setCurrentWidget(self._group_design_page)

        def show_analysis_tasks(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._analysis_task_page.refresh_project(self._current_project)
            self._set_current_route("analysis_tasks")
            self._stack.setCurrentWidget(self._analysis_task_page)

        def show_deg_config(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._deg_config_page.refresh_project(self._current_project)
            self._stack.setCurrentWidget(self._deg_config_page)

        def show_immune_scoring(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._immune_scoring_page.refresh_project(self._current_project)
            self._stack.setCurrentWidget(self._immune_scoring_page)

        def show_results_browser(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._results_browser_page.refresh_project(self._current_project)
            self._set_current_route("results_browser")
            self._stack.setCurrentWidget(self._results_browser_page)

        def show_imported_deg_browser(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._imported_deg_page.refresh_project(self._current_project)
            self._stack.setCurrentWidget(self._imported_deg_page)

        def show_report_viewer(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._report_viewer_page.refresh_project(self._current_project)
            self._set_current_route("report_viewer")
            self._stack.setCurrentWidget(self._report_viewer_page)

        def show_settings(self) -> None:
            self._set_current_route("settings")
            self._stack.setCurrentWidget(self._settings_page)

        def current_project(self) -> BioinformaticsProjectSummary | Path | None:
            return self._current_project

        def current_page_object_name(self) -> str:
            return self._stack.currentWidget().objectName()

        def current_route_key(self) -> str:
            return self._current_route_key

        def current_target_page_key(self) -> str:
            return str(self._stack.currentWidget().property("targetPageKey") or "")

        def current_route_status(self) -> str:
            return str(self._stack.currentWidget().property("legacyRouteStatus") or "")

        def current_route_visibility(self) -> str:
            return str(self._stack.currentWidget().property("routeVisibility") or "")

        def _set_current_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
            if summary is not None:
                self._current_project = summary

        def _apply_legacy_route_properties(self) -> None:
            route_pages = {
                "project_home": self._project_home_page,
                "data_source": self._data_source_page,
                "chinese_search": self._chinese_search_page,
                "acquisition_status": self._acquisition_status_page,
                "recognition": self._recognition_page,
                "readiness": self._readiness_page,
                "standardized_assets": self._standardized_assets_page,
                "group_design": self._group_design_page,
                "workflow_status": self._workflow_status_page,
                "analysis_tasks": self._analysis_task_page,
                "results_browser": self._results_browser_page,
                "report_viewer": self._report_viewer_page,
                "settings": self._settings_page,
            }
            for route_key, page in route_pages.items():
                route = self._legacy_route_by_key[route_key]
                page.setProperty("legacyRouteKey", route.route_key)
                page.setProperty("targetPageKey", route.target_page_key)
                page.setProperty("legacyRouteStatus", route.legacy_status)
                page.setProperty("routeVisibility", route.visibility)
                page.setProperty("developerDiagnostic", route.visibility == "developer_diagnostic")
                page.setProperty("formalActionEnabled", False)

        def _set_current_route(self, route_key: str) -> None:
            self._current_route_key = route_key
            if route_key in self._legacy_route_by_key:
                self._current_target_flow_page_key = self._legacy_route_by_key[route_key].target_page_key
            self._sync_target_flow_state()
            show_home_shell = self._current_target_flow_page_key == "project_home"
            if hasattr(self, "_target_ia_shell"):
                self._target_ia_shell.setVisible(show_home_shell)
            if hasattr(self, "_stack"):
                self._stack.setVisible(not show_home_shell)


    def _feature_row(feature: FeatureAvailability) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        title = QLabel(feature.display_label())
        title.setStyleSheet("font-weight: 700;")
        detail = QLabel(feature.description)
        detail.setWordWrap(True)
        source = QLabel(f"legacy 来源：{feature.legacy_source or '统一壳子占位'}")
        source.setWordWrap(True)
        next_step = QLabel(f"下一步：{feature.next_step}")
        next_step.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(detail)
        layout.addWidget(source)
        layout.addWidget(next_step)
        return frame

elif QWidget is not None:

    class BioinformaticsWorkspaceWidget(QWidget):  # type: ignore[no-redef]
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            self._on_back = on_back
            self.setObjectName("bioinformaticsWorkspaceUnavailable")
            root = QVBoxLayout(self)
            root.setContentsMargins(28, 24, 28, 24)
            title = QLabel("生信分析工作台暂不可用")
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            detail = QLabel(
                "当前 UIShell 分支缺少生信工作台依赖，壳子可继续实例化用于登录、导航和设置页测试。"
            )
            detail.setWordWrap(True)
            root.addWidget(detail)
            root.addStretch(1)

        def show_project_home(self) -> None:
            return None

        def show_settings(self) -> None:
            return None

        def target_ia_page_keys(self) -> tuple[str, ...]:
            return tuple(page.key for page in bioinformatics_target_ia_pages())

        def main_flow_page_keys(self) -> tuple[str, ...]:
            return tuple(page.key for page in bioinformatics_main_flow_pages())

        def auxiliary_page_keys(self) -> tuple[str, ...]:
            return tuple(page.key for page in bioinformatics_auxiliary_pages())

        def legacy_route_keys(self) -> tuple[str, ...]:
            return tuple(route.route_key for route in bioinformatics_legacy_routes())

        def legacy_route_calibration(self) -> tuple[dict[str, str], ...]:
            return tuple(
                {
                    "route_key": route.route_key,
                    "widget_name": route.widget_name,
                    "target_page_key": route.target_page_key,
                    "legacy_status": route.legacy_status,
                    "visibility": route.visibility,
                    "boundary": route.boundary,
                }
                for route in bioinformatics_legacy_routes()
            )

        def current_project(self) -> None:
            return None

        def current_page_object_name(self) -> str:
            return self.objectName()

        def current_route_key(self) -> str:
            return ""

        def current_target_page_key(self) -> str:
            return ""

        def current_route_status(self) -> str:
            return ""

        def current_route_visibility(self) -> str:
            return ""

else:

    class BioinformaticsWorkspaceWidget:  # type: ignore[no-redef]
        pass
