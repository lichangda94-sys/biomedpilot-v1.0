from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QLabel, QLineEdit, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.app_identity import BIOINFORMATICS_WINDOW_TITLE, META_ANALYSIS_WINDOW_TITLE, load_app_icon
from app.bioinformatics_workspace_widget import BioinformaticsWorkspaceWidget
from app.meta_analysis_workspace_widget import MetaAnalysisWorkspaceWidget
from app.reporting_summary_widget import ReportingSummaryWidget
from app.task_results_summary_widget import TaskResultsSummaryWidget
from app.ui_style_tokens import app_stylesheet
from app.workbench_home_widget import WorkbenchHomeWidget
from core.config import AppConfig
from core.data_dirs import DataDirectories
from core.demo_project_loader import create_demo_meta_readiness_project
from core.profile_row_templates import (
    ProfileTemplateType,
    load_project_profile_rows,
    save_project_profile_rows,
)
from core.project_workspace import ProjectWorkspaceState, ProjectWorkspaceStore, ProjectWorkspaceType
from core.task_management import TaskManagementService
from core.task_runner_adapters import ReportingSummaryRunnerAdapter, RunnerAdapterRegistry
from reporting.service import ReportingService


class MainWindow(QMainWindow):
    def __init__(
        self,
        config: AppConfig,
        data_dirs: DataDirectories,
        reporting_service: ReportingService | None = None,
        task_service: TaskManagementService | None = None,
    ) -> None:
        super().__init__()
        self._config = config
        self._data_dirs = data_dirs
        self._reporting_service = reporting_service or ReportingService.from_root_dir(data_dirs.root_dir)
        self._task_service = task_service or TaskManagementService.from_state_dir(data_dirs.state_dir)
        self._project_store = ProjectWorkspaceStore(data_dirs.root_dir / "projects")
        self._current_project_state: ProjectWorkspaceState | None = None
        self._last_dry_run_task_id: str | None = None
        self._last_dry_run_accepted = False

        self.resize(1180, 760)
        self.setStyleSheet(app_stylesheet())
        self.setWindowIcon(load_app_icon())

        self._analysis_id_input = QLineEdit()
        self._analysis_id_input.setObjectName("analysisIdInput")
        self._analysis_id_input.setPlaceholderText("Analysis ID")
        self._load_summary_button = QPushButton("Load")
        self._load_summary_button.setObjectName("loadAnalysisSummaryButton")
        self._load_summary_button.clicked.connect(self.load_selected_analysis_summary)
        self._task_id_input = QLineEdit()
        self._task_id_input.setObjectName("taskIdInput")
        self._task_id_input.setPlaceholderText("Task ID")
        self._task_id_input.textChanged.connect(
            lambda _text: self.refresh_real_run_preflight_state()
        )
        self._plan_id_input = QLineEdit()
        self._plan_id_input.setObjectName("planIdInput")
        self._plan_id_input.setPlaceholderText("Task plan ID")
        self._result_id_input = QLineEdit()
        self._result_id_input.setObjectName("resultIdInput")
        self._result_id_input.setPlaceholderText("Result ID")
        self._preview_artifact_button = QPushButton("Preview artifact")
        self._preview_artifact_button.setObjectName("previewArtifactButton")
        self._preview_artifact_button.clicked.connect(
            self.preview_selected_result_artifact
        )
        self._load_result_detail_button = QPushButton("Load result detail")
        self._load_result_detail_button.setObjectName("loadResultDetailButton")
        self._load_result_detail_button.clicked.connect(
            self.load_selected_result_detail
        )
        self._dry_run_task_button = QPushButton("Dry-run task")
        self._dry_run_task_button.setObjectName("dryRunTaskButton")
        self._dry_run_task_button.clicked.connect(self.execute_selected_task_dry_run)
        self._retry_confirmation_input = QLineEdit()
        self._retry_confirmation_input.setObjectName("retryConfirmationInput")
        self._retry_confirmation_input.setPlaceholderText("Type CREATE RETRY <task id> to confirm")
        self._create_retry_task_button = QPushButton("Create retry task")
        self._create_retry_task_button.setObjectName("createRetryTaskButton")
        self._create_retry_task_button.clicked.connect(
            self.create_retry_task_from_selected_task
        )
        self._plan_materialization_confirmation_input = QLineEdit()
        self._plan_materialization_confirmation_input.setObjectName(
            "planMaterializationConfirmationInput"
        )
        self._plan_materialization_confirmation_input.setPlaceholderText(
            "Type MATERIALIZE PLAN <plan id> to confirm"
        )
        self._materialize_task_plan_button = QPushButton("Materialize task plan")
        self._materialize_task_plan_button.setObjectName("materializeTaskPlanButton")
        self._materialize_task_plan_button.clicked.connect(
            self.materialize_selected_task_plan
        )
        self._manual_execute_status_label = QLabel("Manual execute: idle")
        self._manual_execute_status_label.setObjectName("manualExecuteStatusLabel")
        self._manual_execute_status_label.setWordWrap(True)
        self._real_run_preflight_label = QLabel(
            "Real-run preflight: no task selected, dry-run recommended yes, real-run available in UI no"
        )
        self._real_run_preflight_label.setObjectName("realRunPreflightLabel")
        self._real_run_preflight_label.setWordWrap(True)
        self._real_run_confirmation_input = QLineEdit()
        self._real_run_confirmation_input.setObjectName("realRunConfirmationInput")
        self._real_run_confirmation_input.setPlaceholderText("Type REAL-RUN <task id> to confirm")
        self._real_run_confirmation_input.textChanged.connect(
            lambda _text: self.refresh_real_run_preflight_state()
        )
        self._real_run_task_button = QPushButton("Real-run task")
        self._real_run_task_button.setObjectName("realRunTaskButton")
        self._real_run_task_button.setEnabled(False)
        self._real_run_task_button.clicked.connect(self.execute_selected_task_real_run)

        self._reporting_summary_widget = ReportingSummaryWidget()
        self._task_results_summary_widget = TaskResultsSummaryWidget()
        self._legacy_reporting_task_widget = QWidget()
        layout = QVBoxLayout(self._legacy_reporting_task_widget)
        layout.addWidget(self._analysis_id_input)
        layout.addWidget(self._load_summary_button)
        layout.addWidget(self._task_id_input)
        layout.addWidget(self._plan_id_input)
        layout.addWidget(self._result_id_input)
        layout.addWidget(self._preview_artifact_button)
        layout.addWidget(self._load_result_detail_button)
        layout.addWidget(self._dry_run_task_button)
        layout.addWidget(self._retry_confirmation_input)
        layout.addWidget(self._create_retry_task_button)
        layout.addWidget(self._plan_materialization_confirmation_input)
        layout.addWidget(self._materialize_task_plan_button)
        layout.addWidget(self._manual_execute_status_label)
        layout.addWidget(self._real_run_preflight_label)
        layout.addWidget(self._real_run_confirmation_input)
        layout.addWidget(self._real_run_task_button)
        layout.addWidget(self._reporting_summary_widget)
        layout.addWidget(self._task_results_summary_widget)

        self._workbench_home_widget = WorkbenchHomeWidget(
            on_open_bioinformatics=self.open_bioinformatics_workspace,
            on_open_meta_analysis=self.open_meta_analysis_workspace,
            on_create_project=self.create_internal_testing_meta_project,
            on_load_demo_project=self.load_demo_profile_readiness_project,
        )
        self._bioinformatics_workspace_widget = BioinformaticsWorkspaceWidget()
        self._meta_analysis_workspace_widget = MetaAnalysisWorkspaceWidget()
        self._meta_analysis_workspace_widget.row_editor().set_profile_io_handlers(
            save_handler=self.save_current_profile_editor_rows,
            load_handler=lambda profile_type: self.load_profile_editor_rows(profile_type),
        )
        self._workspace_stack = QStackedWidget()
        self._workspace_stack.setObjectName("mainWorkbenchStack")
        self._workspace_stack.addWidget(self._workbench_home_widget)
        self._workspace_stack.addWidget(self._bioinformatics_workspace_widget)
        self._workspace_stack.addWidget(self._meta_analysis_workspace_widget)
        self.setCentralWidget(self._workspace_stack)
        self.open_bioinformatics_workspace()
        self.refresh_task_results_summary()

    def open_workbench_home(self) -> None:
        self._workspace_stack.setCurrentWidget(self._workbench_home_widget)
        self.setWindowTitle("BioMedPilot · 研究分析平台")

    def open_bioinformatics_workspace(self) -> None:
        self._workspace_stack.setCurrentWidget(self._bioinformatics_workspace_widget)
        self.setWindowTitle(BIOINFORMATICS_WINDOW_TITLE)

    def open_meta_analysis_workspace(self) -> None:
        self._workspace_stack.setCurrentWidget(self._meta_analysis_workspace_widget)
        self.setWindowTitle(META_ANALYSIS_WINDOW_TITLE)

    def current_system_title(self) -> str:
        return self.windowTitle()

    def current_workspace_key(self) -> str:
        current = self._workspace_stack.currentWidget()
        if current is self._workbench_home_widget:
            return "workbench_home"
        if current is self._bioinformatics_workspace_widget:
            return "bioinformatics"
        if current is self._meta_analysis_workspace_widget:
            return "meta_analysis"
        return "unknown"

    def current_workspace_page_title(self) -> str:
        current = self._workspace_stack.currentWidget()
        if hasattr(current, "current_page_title"):
            return current.current_page_title()
        return "统一科研分析工作台"

    def create_project_workspace(
        self,
        *,
        project_type: ProjectWorkspaceType,
        name: str,
        project_id: str | None = None,
    ) -> ProjectWorkspaceState:
        state = self._project_store.create_project(
            project_type=project_type,
            name=name,
            project_id=project_id,
        )
        self._apply_project_state(state)
        return state

    def open_project_workspace(self, project_dir: str | Path) -> ProjectWorkspaceState:
        state = self._project_store.open_project(Path(project_dir))
        self._apply_project_state(state)
        return state

    def save_current_project_workspace(self) -> ProjectWorkspaceState | None:
        if self._current_project_state is None:
            return None
        state = self._project_store.save_project(self._current_project_state)
        self._apply_project_state(state)
        return state

    def load_demo_profile_readiness_project(self) -> ProjectWorkspaceState:
        state = create_demo_meta_readiness_project(self._project_store.projects_root)
        self._apply_project_state(state)
        return state

    def current_project_state(self) -> ProjectWorkspaceState | None:
        return self._current_project_state

    def current_project_summary_text(self) -> str:
        if self._current_project_state is None:
            return "No project opened"
        state = self._current_project_state
        return f"{state.name} · {state.project_type} · {state.project_dir}"

    def create_internal_testing_meta_project(self) -> ProjectWorkspaceState:
        return self.create_project_workspace(
            project_type="meta_analysis",
            name="Internal Testing Meta Project",
            project_id="internal-testing-meta-project",
        )

    def save_current_profile_editor_rows(self) -> Path | None:
        if self._current_project_state is None:
            return None
        if self._current_project_state.project_type != "meta_analysis":
            return None
        editor = self._meta_analysis_workspace_widget.row_editor()
        decision = editor.save_decision()
        if not decision.allowed:
            raise ValueError(decision.message)
        output_path = save_project_profile_rows(
            self._current_project_state.project_dir,
            editor.profile_type(),
            editor.rows(),
        )
        editor.mark_clean()
        return output_path

    def load_profile_editor_rows(
        self,
        profile_type: ProfileTemplateType,
        *,
        discard_unsaved_changes: bool = False,
    ) -> list[dict[str, str]]:
        if self._current_project_state is None:
            return []
        if self._current_project_state.project_type != "meta_analysis":
            return []
        editor = self._meta_analysis_workspace_widget.row_editor()
        decision = editor.load_decision()
        if not decision.allowed and not discard_unsaved_changes:
            raise ValueError(decision.message)
        rows = load_project_profile_rows(
            self._current_project_state.project_dir,
            profile_type,
        )
        editor.set_profile_type(profile_type)
        editor.set_rows(rows)
        return rows

    def _apply_project_state(self, state: ProjectWorkspaceState) -> None:
        self._current_project_state = state
        self._workbench_home_widget.set_current_project_summary(
            self.current_project_summary_text()
        )
        if state.project_type == "bioinformatics":
            self._bioinformatics_workspace_widget.set_project_state(state)
            self.open_bioinformatics_workspace()
        elif state.project_type == "meta_analysis":
            self._meta_analysis_workspace_widget.set_project_state(state)
            self.open_meta_analysis_workspace()
        else:
            raise ValueError(f"Unsupported project type: {state.project_type}")

    def load_analysis_summary(self, analysis_id: str) -> None:
        table = self._reporting_service.generate_analysis_summary_table(analysis_id)
        self._reporting_summary_widget.set_analysis_summary(table)

    def load_selected_analysis_summary(self) -> None:
        analysis_id = self._analysis_id_input.text().strip()
        if not analysis_id:
            return
        self.load_analysis_summary(analysis_id)

    def set_selected_analysis_id(self, analysis_id: str) -> None:
        self._analysis_id_input.setText(analysis_id)

    def set_selected_task_id(self, task_id: str) -> None:
        self._task_id_input.setText(task_id)

    def set_selected_plan_id(self, plan_id: str) -> None:
        self._plan_id_input.setText(plan_id)

    def set_selected_result_id(self, result_id: str) -> None:
        self._result_id_input.setText(result_id)

    def preview_selected_result_artifact(self) -> None:
        result_id = self._result_id_input.text().strip()
        if not result_id:
            self._task_results_summary_widget.set_artifact_preview(None)
            return
        preview = self._task_service.preview_result_artifact(result_id)
        self._task_results_summary_widget.set_artifact_preview(preview)

    def load_selected_result_detail(self) -> None:
        result_id = self._result_id_input.text().strip()
        if not result_id:
            self._task_results_summary_widget.set_result_detail(None)
            return
        detail = self._task_service.get_task_result_detail(result_id)
        self._task_results_summary_widget.set_result_detail(detail)

    def refresh_real_run_preflight_state(self) -> None:
        if not hasattr(self, "_real_run_preflight_label"):
            return
        task_id = self._task_id_input.text().strip()
        if not task_id:
            self._real_run_preflight_label.setText(
                "Real-run preflight: no task selected, dry-run recommended yes, real-run available in UI no"
            )
            self._set_real_run_button_enabled(False)
            return

        task = next(
            (record for record in self._task_service.list_tasks() if record.task_id == task_id),
            None,
        )
        if task is None:
            self._real_run_preflight_label.setText(
                "Real-run preflight: "
                f"selected task {task_id}, task exists no, task state missing, "
                "pending eligible no, adapter available no, dry-run recommended yes, "
                "real-run available in UI no, blocked reason task_missing"
            )
            self._set_real_run_button_enabled(False)
            return

        state = getattr(getattr(task, "state", ""), "value", str(getattr(task, "state", "")))
        pending_eligible = state == "pending"
        adapter_available = (
            self._build_runner_registry().get_for_task_type(task.task_type) is not None
        )
        dry_run_ready = (
            self._last_dry_run_task_id == task.task_id
            and self._last_dry_run_accepted
        )
        confirmation_ready = (
            self._real_run_confirmation_input.text().strip()
            == self._real_run_confirmation_text(task.task_id)
        )
        real_run_available = (
            pending_eligible
            and adapter_available
            and dry_run_ready
            and confirmation_ready
        )
        if not pending_eligible:
            blocked_reason = "task_not_pending"
        elif not adapter_available:
            blocked_reason = "adapter_unavailable"
        elif not dry_run_ready:
            blocked_reason = "dry_run_required"
        elif not confirmation_ready:
            blocked_reason = "confirmation_required"
        else:
            blocked_reason = "none"

        self._real_run_preflight_label.setText(
            "Real-run preflight: "
            f"selected task {task.task_id}, "
            "task exists yes, "
            f"task state {state}, "
            f"pending eligible {self._yes_no(pending_eligible)}, "
            f"adapter available {self._yes_no(adapter_available)}, "
            "dry-run recommended yes, "
            f"real-run available in UI {self._yes_no(real_run_available)}, "
            f"blocked reason {blocked_reason}"
        )
        self._set_real_run_button_enabled(real_run_available)

    def execute_selected_task_dry_run(self) -> None:
        task_id = self._task_id_input.text().strip()
        if not task_id:
            self._manual_execute_status_label.setText(
                "Manual execute outcome: no task selected"
            )
            return
        outcome = self._task_service.execute_task_with_lifecycle(
            task_id,
            self._build_runner_registry(),
            dry_run=True,
        )
        self._last_dry_run_task_id = task_id
        self._last_dry_run_accepted = bool(outcome.accepted)
        self._manual_execute_status_label.setText(
            self._format_manual_execute_outcome(outcome, dry_run=True)
        )
        self.refresh_task_results_summary()
        self.refresh_real_run_preflight_state()

    def execute_selected_task_real_run(self) -> None:
        task_id = self._task_id_input.text().strip()
        self.refresh_real_run_preflight_state()
        if not task_id:
            self._manual_execute_status_label.setText(
                "Manual execute outcome: no task selected"
            )
            self._refresh_after_manual_execute()
            return
        if not self._real_run_task_button.isEnabled():
            self._manual_execute_status_label.setText(
                "Manual execute outcome: real_run blocked, status rejected, message Real-run preflight is not satisfied., error real_run_preflight_blocked, result none"
            )
            self._refresh_after_manual_execute()
            return

        self._real_run_task_button.setEnabled(False)
        outcome = self._task_service.execute_task_with_lifecycle(
            task_id,
            self._build_runner_registry(),
            dry_run=False,
        )
        self._append_manual_execute_log(task_id, outcome, dry_run=False)
        self._manual_execute_status_label.setText(
            self._format_manual_execute_outcome(outcome, dry_run=False)
        )
        self._last_dry_run_task_id = None
        self._last_dry_run_accepted = False
        self._real_run_confirmation_input.setText("")
        self._refresh_after_manual_execute()

    def create_retry_task_from_selected_task(self) -> None:
        task_id = self._task_id_input.text().strip()
        if not task_id:
            self._manual_execute_status_label.setText(
                "Retry creation outcome: no task selected"
            )
            self._refresh_after_manual_execute()
            return
        if (
            self._retry_confirmation_input.text().strip()
            != self._retry_confirmation_text(task_id)
        ):
            self._manual_execute_status_label.setText(
                "Retry creation outcome: status rejected, message Retry confirmation is not satisfied., error retry_confirmation_required, retry task none"
            )
            self._refresh_after_manual_execute()
            return
        try:
            retry_task = self._task_service.create_retry_task(task_id)
        except Exception as exc:
            self._manual_execute_status_label.setText(
                "Retry creation outcome: "
                f"status rejected, message {exc}, "
                "error retry_creation_rejected, retry task none"
            )
            self._refresh_after_manual_execute()
            return

        self._retry_confirmation_input.setText("")
        self._manual_execute_status_label.setText(
            "Retry creation outcome: "
            "status accepted, message Retry task created., "
            f"error none, retry task {retry_task.task_id}"
        )
        self._refresh_after_manual_execute()

    def materialize_selected_task_plan(self) -> None:
        plan_id = self._plan_id_input.text().strip()
        if not plan_id:
            self._manual_execute_status_label.setText(
                "Task plan materialization outcome: no plan selected"
            )
            self._refresh_after_manual_execute()
            return
        if (
            self._plan_materialization_confirmation_input.text().strip()
            != self._plan_materialization_confirmation_text(plan_id)
        ):
            self._manual_execute_status_label.setText(
                "Task plan materialization outcome: status rejected, message Materialization confirmation is not satisfied., error plan_materialization_confirmation_required, task none"
            )
            self._refresh_after_manual_execute()
            return
        try:
            task = self._task_service.materialize_task_plan(plan_id)
        except Exception as exc:
            self._manual_execute_status_label.setText(
                "Task plan materialization outcome: "
                f"status rejected, message {exc}, "
                "error plan_materialization_rejected, task none"
            )
            self._refresh_after_manual_execute()
            return

        self._plan_materialization_confirmation_input.setText("")
        self._manual_execute_status_label.setText(
            "Task plan materialization outcome: "
            "status accepted, message Task plan materialized., "
            f"error none, task {task.task_id}"
        )
        self._refresh_after_manual_execute()

    def _format_manual_execute_outcome(self, outcome: object, *, dry_run: bool) -> str:
        raw_status = getattr(outcome, "status", "")
        status = getattr(raw_status, "value", str(raw_status))
        message = getattr(outcome, "message", "") or "none"
        error_code = getattr(outcome, "error_code", "") or "none"
        result_id = getattr(outcome, "result_id", None) or "none"
        return (
            "Manual execute outcome: "
            f"dry_run {str(dry_run).lower()}, "
            f"status {status}, "
            f"message {message}, "
            f"error {error_code}, "
            f"result {result_id}"
        )

    def _yes_no(self, value: bool) -> str:
        return "yes" if value else "no"

    def _set_real_run_button_enabled(self, enabled: bool) -> None:
        if hasattr(self, "_real_run_task_button"):
            self._real_run_task_button.setEnabled(enabled)

    def _refresh_after_manual_execute(self) -> None:
        status = self._manual_execute_status_label.text()
        try:
            self.refresh_task_results_summary()
        except Exception as exc:  # pragma: no cover - UI stability guard
            self._manual_execute_status_label.setText(
                f"{status}; refresh failed: {exc}"
            )
            status = self._manual_execute_status_label.text()
        try:
            self.refresh_real_run_preflight_state()
        except Exception as exc:  # pragma: no cover - UI stability guard
            self._manual_execute_status_label.setText(
                f"{status}; preflight refresh failed: {exc}"
            )

    def _real_run_confirmation_text(self, task_id: str) -> str:
        return f"REAL-RUN {task_id}"

    def _retry_confirmation_text(self, task_id: str) -> str:
        return f"CREATE RETRY {task_id}"

    def _plan_materialization_confirmation_text(self, plan_id: str) -> str:
        return f"MATERIALIZE PLAN {plan_id}"

    def _append_manual_execute_log(
        self,
        task_id: str,
        outcome: object,
        *,
        dry_run: bool,
    ) -> None:
        task = next(
            (record for record in self._task_service.list_tasks() if record.task_id == task_id),
            None,
        )
        task_type = getattr(task, "task_type", "") if task is not None else ""
        adapter = self._build_runner_registry().get_for_task_type(task_type) if task_type else None
        raw_status = getattr(outcome, "status", "")
        status = getattr(raw_status, "value", str(raw_status))
        metadata = {"source": "main_window"}
        self._task_service.append_task_execution_log(
            task_id,
            source_plan_id=(
                str(task.metadata["source_plan_id"])
                if task is not None and task.metadata.get("source_plan_id") is not None
                else None
            ),
            runner_type=adapter.runner_type if adapter is not None else "",
            task_type=task_type,
            dry_run=dry_run,
            outcome_status=status,
            message=getattr(outcome, "message", ""),
            error_code=getattr(outcome, "error_code", ""),
            result_id=getattr(outcome, "result_id", None),
            metadata=metadata,
        )

    def _build_runner_registry(self) -> RunnerAdapterRegistry:
        registry = RunnerAdapterRegistry()
        registry.register(
            ReportingSummaryRunnerAdapter(
                reporting_service=self._reporting_service,
                task_service=self._task_service,
            )
        )
        return registry

    def reporting_profile_source_text(self) -> str:
        return self._reporting_summary_widget.profile_source_text()

    def refresh_task_results_summary(self) -> None:
        diagnostics = self._task_service.inspect_result_artifacts()
        results = self._task_service.list_results()
        self._task_results_summary_widget.set_task_results(
            results,
            artifact_summary=self._task_service.summarize_task_result_artifacts(diagnostics),
            artifact_diagnostics=diagnostics,
            task_plan_summary=self._task_service.summarize_task_plans(),
            task_plan_materialization_readiness=(
                self._task_service.summarize_task_plan_materialization_readiness()
            ),
            task_execution_contract_readiness=(
                self._task_service.summarize_task_execution_contract_readiness()
            ),
            task_execution_log_summary=(
                self._task_service.summarize_task_execution_logs()
            ),
            retry_task_summary=self._task_service.summarize_retry_tasks(),
            analysis_preflight_results=[
                result
                for result in results
                if result.result_type == "analysis_preflight_summary"
            ],
            real_dataset_readiness_summary=(
                self._real_dataset_readiness_summary()
            ),
            mock_runner_diagnostics=(
                self._task_service.summarize_mock_runner_diagnostics()
            ),
            runner_adapter_registry_summary=(
                RunnerAdapterRegistry().summarize_adapters().to_dict()
            ),
        )

    def task_results_status_text(self) -> str:
        return self._task_results_summary_widget.status_text()

    def task_result_artifact_status_text(self) -> str:
        return self._task_results_summary_widget.artifact_status_text()

    def task_plan_status_text(self) -> str:
        return self._task_results_summary_widget.task_plan_status_text()

    def task_plan_materialization_readiness_text(self) -> str:
        return self._task_results_summary_widget.task_plan_materialization_readiness_text()

    def task_execution_contract_readiness_text(self) -> str:
        return self._task_results_summary_widget.task_execution_contract_readiness_text()

    def task_execution_log_summary_text(self) -> str:
        return self._task_results_summary_widget.task_execution_log_summary_text()

    def retry_task_summary_text(self) -> str:
        return self._task_results_summary_widget.retry_task_summary_text()

    def analysis_preflight_summary_text(self) -> str:
        return self._task_results_summary_widget.analysis_preflight_summary_text()

    def real_dataset_readiness_summary_text(self) -> str:
        return self._task_results_summary_widget.real_dataset_readiness_summary_text()

    def artifact_preview_status_text(self) -> str:
        return self._task_results_summary_widget.artifact_preview_status_text()

    def artifact_preview_text(self) -> str:
        return self._task_results_summary_widget.artifact_preview_text()

    def result_detail_text(self) -> str:
        return self._task_results_summary_widget.result_detail_text()

    def manual_execute_status_text(self) -> str:
        return self._manual_execute_status_label.text()

    def real_run_preflight_status_text(self) -> str:
        return self._real_run_preflight_label.text()

    def click_dry_run_task_button(self) -> None:
        self._dry_run_task_button.click()

    def set_real_run_confirmation_text(self, text: str) -> None:
        self._real_run_confirmation_input.setText(text)

    def set_retry_confirmation_text(self, text: str) -> None:
        self._retry_confirmation_input.setText(text)

    def set_plan_materialization_confirmation_text(self, text: str) -> None:
        self._plan_materialization_confirmation_input.setText(text)

    def click_real_run_task_button(self) -> None:
        self._real_run_task_button.click()

    def click_create_retry_task_button(self) -> None:
        self._create_retry_task_button.click()

    def click_materialize_task_plan_button(self) -> None:
        self._materialize_task_plan_button.click()

    def real_run_button_enabled(self) -> bool:
        return self._real_run_task_button.isEnabled()

    def mock_runner_diagnostics_text(self) -> str:
        return self._task_results_summary_widget.mock_runner_diagnostics_text()

    def runner_adapter_registry_text(self) -> str:
        return self._task_results_summary_widget.runner_adapter_registry_text()

    def task_result_cell_text(self, row: int, column: int) -> str:
        return self._task_results_summary_widget.result_cell_text(row, column)

    def _real_dataset_readiness_summary(self) -> dict[str, object] | None:
        summarize = getattr(
            self._task_service,
            "summarize_real_dataset_readiness_reports",
            None,
        )
        if summarize is None:
            return None
        return summarize()


AppWindow = MainWindow
