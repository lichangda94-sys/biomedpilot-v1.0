from __future__ import annotations

from collections.abc import Callable

from app.shared.feature_availability import FeatureAvailability, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability


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


try:
    from pathlib import Path

    from PySide6.QtWidgets import QFrame, QLabel, QStackedWidget, QVBoxLayout, QWidget

    from app.bioinformatics.project_home import BioinformaticsProjectHomeWidget
    from app.bioinformatics.project_workspace import BioinformaticsProjectSummary
    from app.bioinformatics.workflow_pages import (
        BioinformaticsAcquisitionStatusWidget,
        BioinformaticsAnalysisTaskCenterWidget,
        BioinformaticsDataSourceWidget,
        BioinformaticsRecognitionWidget,
        BioinformaticsReadinessDashboardWidget,
        BioinformaticsReportViewerWidget,
        BioinformaticsResultsBrowserWidget,
        BioinformaticsSettingsAndLocalAIWidget,
        BioinformaticsStandardizedAssetsWidget,
        BioinformaticsWorkflowStatusWidget,
    )
except Exception:  # pragma: no cover - non-GUI environments import feature registry only.
    QFrame = QLabel = QStackedWidget = QVBoxLayout = QWidget = None


if QWidget is not None:

    class BioinformaticsWorkspaceWidget(QWidget):
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            self._current_project: BioinformaticsProjectSummary | Path | None = None
            self._stack = QStackedWidget()
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.addWidget(self._stack)
            self._project_home_page = BioinformaticsProjectHomeWidget(
                on_continue=self.show_data_source,
                on_back=on_back,
            )
            self._data_source_page = BioinformaticsDataSourceWidget(
                on_continue=self.show_recognition,
                on_back=self.show_project_home,
            )
            self._acquisition_status_page = BioinformaticsAcquisitionStatusWidget(
                on_continue=self.show_recognition,
                on_back=self.show_data_source,
            )
            self._recognition_page = BioinformaticsRecognitionWidget(
                on_continue=self.show_readiness,
                on_back=self.show_data_source,
            )
            self._readiness_page = BioinformaticsReadinessDashboardWidget(
                on_continue=self.show_standardization,
                on_back=self.show_recognition,
            )
            self._standardized_assets_page = BioinformaticsStandardizedAssetsWidget(
                on_continue=self.show_workflow_status,
                on_back=self.show_readiness,
            )
            self._workflow_status_page = BioinformaticsWorkflowStatusWidget(
                on_continue=self.show_analysis_tasks,
                on_back=self.show_project_home,
            )
            self._analysis_task_page = BioinformaticsAnalysisTaskCenterWidget(
                on_continue=self.show_results_browser,
                on_back=self.show_workflow_status,
            )
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
                self._acquisition_status_page,
                self._recognition_page,
                self._readiness_page,
                self._standardized_assets_page,
                self._workflow_status_page,
                self._analysis_task_page,
                self._results_browser_page,
                self._report_viewer_page,
                self._settings_page,
            ):
                self._stack.addWidget(page)
            self._stack.setCurrentWidget(self._project_home_page)

        def show_project_home(self) -> None:
            self._stack.setCurrentWidget(self._project_home_page)

        def show_data_source(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._data_source_page.refresh_project(self._current_project)
            self._stack.setCurrentWidget(self._data_source_page)

        def show_acquisition_status(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._acquisition_status_page.refresh_project(self._current_project)
            self._stack.setCurrentWidget(self._acquisition_status_page)

        def show_recognition(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._recognition_page.refresh_project(self._current_project)
            self._stack.setCurrentWidget(self._recognition_page)

        def show_readiness(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._readiness_page.refresh_project(self._current_project)
            self._stack.setCurrentWidget(self._readiness_page)

        def show_standardization(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._standardized_assets_page.refresh_project(self._current_project)
            self._stack.setCurrentWidget(self._standardized_assets_page)

        def show_workflow_status(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._workflow_status_page.refresh_project(self._current_project)
            self._stack.setCurrentWidget(self._workflow_status_page)

        def show_analysis_tasks(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._analysis_task_page.refresh_project(self._current_project)
            self._stack.setCurrentWidget(self._analysis_task_page)

        def show_results_browser(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._results_browser_page.refresh_project(self._current_project)
            self._stack.setCurrentWidget(self._results_browser_page)

        def show_report_viewer(self, summary: BioinformaticsProjectSummary | Path | None = None) -> None:
            self._set_current_project(summary)
            self._report_viewer_page.refresh_project(self._current_project)
            self._stack.setCurrentWidget(self._report_viewer_page)

        def show_settings(self) -> None:
            self._stack.setCurrentWidget(self._settings_page)

        def current_project(self) -> BioinformaticsProjectSummary | Path | None:
            return self._current_project

        def current_page_object_name(self) -> str:
            return self._stack.currentWidget().objectName()

        def _set_current_project(self, summary: BioinformaticsProjectSummary | Path | None) -> None:
            if summary is not None:
                self._current_project = summary


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

else:

    class BioinformaticsWorkspaceWidget:  # type: ignore[no-redef]
        pass
