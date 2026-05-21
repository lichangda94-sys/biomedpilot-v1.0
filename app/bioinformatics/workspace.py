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
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget
except Exception:  # pragma: no cover - non-GUI environments import feature registry only.
    QFrame = QHBoxLayout = QLabel = QPushButton = QStackedWidget = QVBoxLayout = QWidget = None
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
            BioinformaticsGroupComparisonDesignWidget,
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
            root.addWidget(self._build_target_ia_shell())
            root.addWidget(self._stack)
            self._project_home_page = BioinformaticsProjectHomeWidget(
                on_continue=self.show_data_source,
                on_back=on_back,
            )
            self._data_source_page = BioinformaticsDataSourceWidget(
                on_continue=self.show_recognition,
                on_back=self.show_project_home,
            )
            self._data_source_page.chinese_search_requested.connect(self.show_chinese_search)
            self._chinese_search_page = BioinformaticsChineseDatasetSearchWidget(
                on_back=self.show_data_source,
                on_continue=self.show_recognition,
                on_source_registered=lambda summary: self._data_source_page.refresh_project(self._current_project),
            )
            self._acquisition_status_page = BioinformaticsAcquisitionStatusWidget(
                on_continue=self.show_recognition,
                on_back=self.show_data_source,
            )
            self._recognition_page = BioinformaticsRecognitionWidget(
                on_continue=self.show_readiness,
                on_back=self.show_data_source,
            )
            self._recognition_page.navigate_requested.connect(self._handle_workflow_navigation)
            self._readiness_page = BioinformaticsReadinessDashboardWidget(
                on_continue=self.show_standardization,
                on_back=self.show_recognition,
            )
            self._standardized_assets_page = BioinformaticsStandardizedAssetsWidget(
                on_continue=self.show_workflow_status,
                on_back=self.show_readiness,
            )
            self._standardized_assets_page.group_design_requested.connect(self.show_group_design)
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
                on_back=self.show_workflow_status,
            )
            self._analysis_task_page.group_design_requested.connect(self.show_group_design)
            self._results_browser_page = BioinformaticsResultsBrowserWidget(
                on_continue=self.show_report_viewer,
                on_back=self.show_analysis_tasks,
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
            frame = QFrame()
            frame.setObjectName("bioinformaticsTargetIAShell")
            frame.setStyleSheet("QFrame#bioinformaticsTargetIAShell { border-bottom: 1px solid #D8DEE9; background: #F8FAFC; }")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(18, 16, 18, 16)
            layout.setSpacing(12)

            header = QHBoxLayout()
            title_col = QVBoxLayout()
            title = QLabel("生信分析 / Bioinformatics")
            title.setObjectName("bioinformaticsIATitle")
            title.setStyleSheet("font-size: 22px; font-weight: 750;")
            subtitle = QLabel("提供生信分析全流程工具，支持从数据来源到结果解读的一站式分析与可视化。")
            subtitle.setObjectName("bioinformaticsIASubtitle")
            subtitle.setWordWrap(True)
            title_col.addWidget(title)
            title_col.addWidget(subtitle)
            header.addLayout(title_col, 1)
            header.addWidget(make_status_chip("Developer Preview / 本地测试版", status_key="developer_preview"))
            layout.addLayout(header)

            main_card = QFrame()
            main_card.setObjectName("bioinformaticsWorkflowOverviewCard")
            main_card.setStyleSheet("QFrame#bioinformaticsWorkflowOverviewCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            main_layout = QVBoxLayout(main_card)
            main_layout.setContentsMargins(14, 14, 14, 14)
            main_layout.setSpacing(12)
            main_title = QLabel("生信分析流程概览 / Workflow Overview")
            main_title.setObjectName("bioinformaticsIAMainFlowTitle")
            main_title.setStyleSheet("font-weight: 700;")
            main_layout.addWidget(main_title)
            row = QHBoxLayout()
            row.setSpacing(8)
            for page in bioinformatics_main_flow_pages():
                item = QPushButton(page.label)
                item.setObjectName("bioinformaticsIANavItem")
                item.setCheckable(True)
                item.setProperty("pageKey", page.key)
                item.setProperty("pageGroup", page.page_group)
                item.setProperty("flowIndex", page.flow_index)
                item.setProperty("moduleKey", ModuleKey.BIOINFORMATICS.value)
                item.setProperty("statusKey", page.status_key)
                item.setProperty("semanticKey", _BIO_PAGE_SEMANTIC_KEYS[page.key])
                item.setProperty("statusSemanticKey", page.semantic_key)
                item.setProperty("formalActionEnabled", False)
                item.setToolTip(page.label)
                item.setEnabled(False)
                self._target_ia_buttons[page.key] = item
                row.addWidget(item)
            main_layout.addLayout(row)
            layout.addWidget(main_card)

            auxiliary_card = QFrame()
            auxiliary_card.setObjectName("bioinformaticsAuxiliaryCard")
            auxiliary_card.setStyleSheet("QFrame#bioinformaticsAuxiliaryCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            auxiliary_layout = QVBoxLayout(auxiliary_card)
            auxiliary_layout.setContentsMargins(14, 14, 14, 14)
            auxiliary_layout.setSpacing(10)
            auxiliary_title = QLabel("辅助功能 / Auxiliary")
            auxiliary_title.setObjectName("bioinformaticsIAAuxiliaryTitle")
            auxiliary_title.setStyleSheet("font-weight: 700;")
            auxiliary_layout.addWidget(auxiliary_title)
            auxiliary_row = QHBoxLayout()
            auxiliary_row.setSpacing(10)
            for page in bioinformatics_auxiliary_pages():
                item = QPushButton(page.label)
                item.setObjectName("bioinformaticsIANavItem")
                item.setCheckable(True)
                item.setProperty("pageKey", page.key)
                item.setProperty("pageGroup", page.page_group)
                item.setProperty("flowIndex", page.flow_index)
                item.setProperty("moduleKey", ModuleKey.BIOINFORMATICS.value)
                item.setProperty("statusKey", page.status_key)
                item.setProperty("semanticKey", _BIO_PAGE_SEMANTIC_KEYS[page.key])
                item.setProperty("statusSemanticKey", page.semantic_key)
                item.setProperty("formalActionEnabled", False)
                item.setToolTip(page.label)
                item.setEnabled(False)
                self._target_ia_buttons[page.key] = item
                auxiliary_row.addWidget(item)
            auxiliary_row.addStretch(1)
            auxiliary_layout.addLayout(auxiliary_row)
            layout.addWidget(auxiliary_card)

            self._result_report_panel = make_result_report_export_adoption_panel(module="bioinformatics")
            self._result_report_panel.setProperty("moduleKey", ModuleKey.BIOINFORMATICS.value)
            self._result_report_panel.setProperty("pageKey", "result_report")
            self._result_report_panel.setProperty("semanticKey", PageKey.BIO_RESULT_REPORT.value)
            layout.addWidget(self._result_report_panel)

            quick = QFrame()
            quick.setObjectName("bioinformaticsQuickAccessCard")
            quick.setStyleSheet("QFrame#bioinformaticsQuickAccessCard { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            quick_layout = QVBoxLayout(quick)
            quick_layout.setContentsMargins(14, 12, 14, 12)
            quick_layout.setSpacing(8)
            quick_title = QLabel("快速入口")
            quick_title.setObjectName("quickAccessTitle")
            quick_title.setStyleSheet("font-weight: 700;")
            quick_layout.addWidget(quick_title)
            quick_row = QHBoxLayout()
            quick_row.setSpacing(8)
            for text in ("最近使用", "使用指南", "常见问题", "意见反馈"):
                button = QPushButton(text)
                button.setObjectName("quickAccessButton")
                button.setProperty("moduleKey", ModuleKey.BIOINFORMATICS.value)
                button.setProperty("quickAccessKey", text)
                button.setEnabled(False)
                quick_row.addWidget(button)
            quick_row.addStretch(1)
            quick_layout.addLayout(quick_row)
            layout.addWidget(quick)
            self._sync_target_flow_state()
            return frame

        def _sync_target_flow_state(self) -> None:
            if not hasattr(self, "_target_ia_buttons"):
                return
            for key, button in self._target_ia_buttons.items():
                button.setChecked(key == self._current_target_flow_page_key)
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

        def show_results_browser(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._results_browser_page.refresh_project(self._current_project)
            self._set_current_route("results_browser")
            self._stack.setCurrentWidget(self._results_browser_page)

        def show_report_viewer(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._report_viewer_page.refresh_project(self._current_project)
            self._set_current_route("report_viewer")
            self._stack.setCurrentWidget(self._report_viewer_page)

        def show_settings(self) -> None:
            self._set_current_route("settings")
            self._stack.setCurrentWidget(self._settings_page)

        def _handle_workflow_navigation(self, target: str, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            if target == "data_source":
                self.show_data_source(summary)
            elif target == "standardization":
                self.show_standardization(summary)
            elif target == "analysis_tasks":
                self.show_analysis_tasks(summary)
            elif target == "group_design":
                self.show_group_design(summary)
            elif target == "result_browser":
                self.show_results_browser(summary)

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
