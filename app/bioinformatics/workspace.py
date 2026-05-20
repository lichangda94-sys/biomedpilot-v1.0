from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.shared.feature_availability import FeatureAvailability, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability
from app.shared.semantic_keys import AnalysisStatusKey, ReportStatusKey, ResultSemanticKey


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
        ),
        BioinformaticsIAPage(
            "data_source",
            "Data Source / 数据来源",
            "testing",
            "feature.status.testing",
            "GEO、本地导入与后续 TCGA/GTEx 入口；TCGA+GTEx 不自动合并。",
        ),
        BioinformaticsIAPage(
            "data_check_preparation",
            "Data Check & Preparation / 数据检查与准备",
            "preflight_only",
            AnalysisStatusKey.PREFLIGHT_ONLY.value,
            "resolver-first / preflight-first；未形成 standardized repository 与 analysis input package 前不开放正式分析。",
        ),
        BioinformaticsIAPage(
            "group_design",
            "Group & Design / 分组与设计",
            "preflight_only",
            AnalysisStatusKey.PREFLIGHT_ONLY.value,
            "服务 DEG、GSEA/ORA、相关性、生存与临床关联；不是 DEG 专属页面。",
        ),
        BioinformaticsIAPage(
            "analysis_tasks",
            "Analysis Tasks / 分析任务",
            "blocked",
            AnalysisStatusKey.BLOCKED.value,
            "只显示 gated 任务卡；不得把预检包装成正式 DEG/GSEA/生存分析执行。",
        ),
        BioinformaticsIAPage(
            "results",
            "Results / 结果浏览",
            "testing",
            ResultSemanticKey.TESTING_SUMMARY_ONLY.value,
            "区分 imported_external_result 与未来 formal_computed_result；不生成假结果或假图。",
        ),
        BioinformaticsIAPage(
            "report_export",
            "Report / Export / 报告导出",
            "draft",
            ReportStatusKey.TESTING_SUMMARY.value,
            "仅允许测试摘要和报告草稿边界；不声明 report-ready 正式报告。",
        ),
        BioinformaticsIAPage(
            "settings_resources",
            "Settings Resources / 生信资源设置",
            "shell_only",
            "resource.status.not_configured",
            "GO/KEGG/MSigDB、R/Python 包和外部资源检测归 Settings 管理。",
        ),
        BioinformaticsIAPage(
            "project_logs_technical_details",
            "Project Logs & Technical Details / 项目日志与技术详情",
            "shell_only",
            "feature.status.developer_preview",
            "旧 workflow status、manifest、technical logs 和反馈包只作为开发者诊断或项目日志入口，不作为普通主流程。",
        ),
    )


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
            "results",
            "testing_summary",
            "secondary",
            "结果浏览只承载 testing summary 或 imported external result；不生成假图假结果。",
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
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(8)

            title = QLabel("Bioinformatics / 生信分析目标 IA shell")
            title.setObjectName("bioinformaticsIATitle")
            title.setStyleSheet("font-weight: 750;")
            layout.addWidget(title)

            boundary = QLabel(
                "目标收束：resolver-first / preflight-first / result-schema-first。"
                "分析任务为 gated copy，不启用正式分析执行器，不生成假结果或假图。"
            )
            boundary.setObjectName("bioinformaticsIABoundary")
            boundary.setWordWrap(True)
            layout.addWidget(boundary)

            row = QHBoxLayout()
            row.setSpacing(8)
            for page in bioinformatics_target_ia_pages():
                item = QPushButton(page.label)
                item.setObjectName("bioinformaticsIANavItem")
                item.setProperty("pageKey", page.key)
                item.setProperty("statusKey", page.status_key)
                item.setProperty("semanticKey", page.semantic_key)
                item.setToolTip(page.boundary)
                item.setEnabled(False)
                row.addWidget(item)
            layout.addLayout(row)

            status_row = QHBoxLayout()
            status_row.setSpacing(8)
            for text in (
                "preflight/gated",
                "imported_external_result != formal_computed_result",
                "report draft / testing summary only",
            ):
                label = QLabel(text)
                label.setObjectName("bioinformaticsIABoundaryChip")
                label.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 6px; padding: 4px 8px; background: #FFFFFF;")
                status_row.addWidget(label)
            status_row.addStretch(1)
            layout.addLayout(status_row)

            legacy_title = QLabel("Legacy page routing calibration / 旧页面路由校准")
            legacy_title.setObjectName("bioinformaticsLegacyRouteTitle")
            legacy_title.setStyleSheet("font-weight: 700;")
            layout.addWidget(legacy_title)
            legacy_routes = list(bioinformatics_legacy_routes())
            for start in range(0, len(legacy_routes), 4):
                route_row = QHBoxLayout()
                route_row.setSpacing(8)
                for route in legacy_routes[start : start + 4]:
                    item = QPushButton(f"{route.route_key} -> {route.target_page_key}")
                    item.setObjectName("bioinformaticsLegacyRouteItem")
                    item.setProperty("routeKey", route.route_key)
                    item.setProperty("targetPageKey", route.target_page_key)
                    item.setProperty("legacyRouteStatus", route.legacy_status)
                    item.setProperty("routeVisibility", route.visibility)
                    item.setToolTip(route.boundary)
                    item.setEnabled(False)
                    route_row.addWidget(item)
                route_row.addStretch(1)
                layout.addLayout(route_row)
            return frame

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
