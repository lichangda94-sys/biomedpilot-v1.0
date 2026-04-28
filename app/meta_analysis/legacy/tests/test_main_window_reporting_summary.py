import os
import tempfile
import unittest
from pathlib import Path

from analysis.models import AnalysisMetric, AnalysisModelType
from core.config import AppConfig
from core.data_dirs import DataDirectories
from core.task_models import (
    ArtifactPreviewRecord,
    TaskExecutionOutcome,
    TaskExecutionOutcomeStatus,
    TaskPlanRecord,
    TaskPlanState,
    TaskRecord,
    TaskResultArtifactDiagnostic,
    TaskResultArtifactStatus,
    TaskResultDetailRecord,
    TaskResultRecord,
    TaskResultState,
)
from core.task_status import TaskState
from reporting.models import AnalysisSummaryRow, AnalysisSummaryTable


class FakeReportingService:
    def __init__(self) -> None:
        self.requested_analysis_ids: list[str] = []

    def generate_analysis_summary_table(self, analysis_id: str) -> AnalysisSummaryTable:
        self.requested_analysis_ids.append(analysis_id)
        return AnalysisSummaryTable(
            project_id="proj-ui",
            rows=[
                AnalysisSummaryRow(
                    analysis_id=analysis_id,
                    analysis_profile_id="aprof-ui",
                    analysis_profile_name="UI profile",
                    metric=AnalysisMetric.OR,
                    model_type=AnalysisModelType.FIXED_EFFECT,
                    pooled_effect=0.72,
                    ci_lower=0.50,
                    ci_upper=0.95,
                    p_value=0.01,
                    tau2=0.0,
                    q_statistic=1.0,
                    i2=0.0,
                    study_count=2,
                )
            ],
        )


class FakeTaskService:
    def __init__(
        self,
        results: list[TaskResultRecord] | None = None,
        plan_summary: dict[str, int] | None = None,
        plan_readiness_summary: dict[str, int] | None = None,
        execution_contract_readiness_summary: dict[str, int] | None = None,
        execution_log_summary: dict[str, int] | None = None,
        retry_task_summary: dict[str, int] | None = None,
        real_dataset_readiness_summary: dict[str, object] | None = None,
        mock_runner_diagnostics_summary: dict[str, int] | None = None,
        manual_execute_outcome: TaskExecutionOutcome | None = None,
        real_execute_outcome: TaskExecutionOutcome | None = None,
        tasks: list[TaskRecord] | None = None,
        plans: list[TaskPlanRecord] | None = None,
    ) -> None:
        self._results = list(results or [])
        self._tasks = list(tasks or [])
        self._plans = list(plans or [])
        self._plan_summary = dict(plan_summary or {})
        self._plan_readiness_summary = dict(plan_readiness_summary or {})
        self._execution_contract_readiness_summary = dict(
            execution_contract_readiness_summary or {}
        )
        self._execution_log_summary = dict(execution_log_summary or {})
        self._retry_task_summary = dict(retry_task_summary or {})
        self._real_dataset_readiness_summary = dict(
            real_dataset_readiness_summary or {}
        )
        self._mock_runner_diagnostics_summary = dict(
            mock_runner_diagnostics_summary or {}
        )
        self._manual_execute_outcome = manual_execute_outcome or TaskExecutionOutcome(
            task_id="",
            accepted=True,
            status=TaskExecutionOutcomeStatus.SKIPPED,
            message="Dry-run accepted.",
        )
        self._real_execute_outcome = real_execute_outcome or TaskExecutionOutcome(
            task_id="",
            accepted=True,
            status=TaskExecutionOutcomeStatus.ACCEPTED,
            message="Real-run accepted.",
            result_id="result-real-run",
        )
        self.execute_calls: list[tuple[str, bool]] = []
        self.execution_logs: list[dict[str, object]] = []
        self.created_retry_tasks: list[TaskRecord] = []
        self.materialized_tasks: list[TaskRecord] = []
        self.preview_calls: list[str] = []
        self.detail_calls: list[str] = []
        self.list_results_calls = 0
        self.fail_list_results = False

    def list_results(self) -> list[TaskResultRecord]:
        self.list_results_calls += 1
        if self.fail_list_results:
            raise RuntimeError("summary refresh unavailable")
        return list(self._results)

    def list_tasks(self) -> list[TaskRecord]:
        return list(self._tasks)

    def list_task_plans(self) -> list[TaskPlanRecord]:
        return list(self._plans)

    def inspect_result_artifacts(self) -> list[TaskResultArtifactDiagnostic]:
        diagnostics = []
        for result in self._results:
            if result.artifact_path:
                artifact_status = TaskResultArtifactStatus.MISSING
            else:
                artifact_status = TaskResultArtifactStatus.NOT_APPLICABLE
            diagnostics.append(
                TaskResultArtifactDiagnostic(
                    result_id=result.result_id,
                    result_type=result.result_type,
                    state=result.state,
                    artifact_path=result.artifact_path,
                    artifact_status=artifact_status,
                )
            )
        return diagnostics

    def summarize_task_result_artifacts(
        self,
        diagnostics: list[TaskResultArtifactDiagnostic] | None = None,
    ) -> dict[str, int]:
        records = diagnostics if diagnostics is not None else self.inspect_result_artifacts()
        return {
            "total_results": len(records),
            "present_artifacts": 0,
            "missing_artifacts": sum(
                item.artifact_status == TaskResultArtifactStatus.MISSING
                for item in records
            ),
            "not_applicable_artifacts": sum(
                item.artifact_status == TaskResultArtifactStatus.NOT_APPLICABLE
                for item in records
            ),
        }

    def summarize_task_plans(self) -> dict[str, int]:
        if self._plans:
            return {
                "total_plans": len(self._plans),
                "draft_plans": sum(
                    plan.state == TaskPlanState.DRAFT for plan in self._plans
                ),
                "ready_plans": sum(
                    plan.state == TaskPlanState.READY for plan in self._plans
                ),
                "disabled_plans": sum(
                    plan.state == TaskPlanState.DISABLED for plan in self._plans
                ),
                "archived_plans": sum(
                    plan.state == TaskPlanState.ARCHIVED for plan in self._plans
                ),
            }
        return {
            "total_plans": self._plan_summary.get("total_plans", 0),
            "draft_plans": self._plan_summary.get("draft_plans", 0),
            "ready_plans": self._plan_summary.get("ready_plans", 0),
            "disabled_plans": self._plan_summary.get("disabled_plans", 0),
            "archived_plans": self._plan_summary.get("archived_plans", 0),
        }

    def summarize_task_plan_materialization_readiness(self) -> dict[str, int]:
        if self._plans:
            return {
                "total_plans": len(self._plans),
                "materializable_plans": sum(
                    plan.state == TaskPlanState.READY for plan in self._plans
                ),
                "blocked_plans": sum(
                    plan.state != TaskPlanState.READY for plan in self._plans
                ),
                "ready_plans": sum(
                    plan.state == TaskPlanState.READY for plan in self._plans
                ),
                "draft_plans": sum(
                    plan.state == TaskPlanState.DRAFT for plan in self._plans
                ),
                "disabled_plans": sum(
                    plan.state == TaskPlanState.DISABLED for plan in self._plans
                ),
                "archived_plans": sum(
                    plan.state == TaskPlanState.ARCHIVED for plan in self._plans
                ),
                "missing_context_plans": 0,
            }
        return {
            "total_plans": self._plan_readiness_summary.get("total_plans", 0),
            "materializable_plans": self._plan_readiness_summary.get("materializable_plans", 0),
            "blocked_plans": self._plan_readiness_summary.get("blocked_plans", 0),
            "ready_plans": self._plan_readiness_summary.get("ready_plans", 0),
            "draft_plans": self._plan_readiness_summary.get("draft_plans", 0),
            "disabled_plans": self._plan_readiness_summary.get("disabled_plans", 0),
            "archived_plans": self._plan_readiness_summary.get("archived_plans", 0),
            "missing_context_plans": self._plan_readiness_summary.get("missing_context_plans", 0),
        }

    def summarize_task_execution_contract_readiness(self) -> dict[str, int]:
        return {
            "total_tasks": self._execution_contract_readiness_summary.get("total_tasks", 0),
            "ready_tasks": self._execution_contract_readiness_summary.get("ready_tasks", 0),
            "blocked_tasks": self._execution_contract_readiness_summary.get("blocked_tasks", 0),
            "validation_failed_tasks": self._execution_contract_readiness_summary.get("validation_failed_tasks", 0),
            "missing_context_tasks": self._execution_contract_readiness_summary.get("missing_context_tasks", 0),
        }

    def summarize_task_execution_logs(self) -> dict[str, int]:
        if self.execution_logs:
            success_statuses = {"accepted", "skipped"}
            return {
                "total_logs": len(self.execution_logs),
                "dry_run_logs": sum(
                    bool(log["dry_run"]) for log in self.execution_logs
                ),
                "real_run_logs": sum(
                    not bool(log["dry_run"]) for log in self.execution_logs
                ),
                "success_accepted_logs": sum(
                    str(log["outcome_status"]) in success_statuses
                    for log in self.execution_logs
                ),
                "failed_rejected_logs": sum(
                    str(log["outcome_status"]) not in success_statuses
                    for log in self.execution_logs
                ),
                "logs_with_result_id": sum(
                    bool(log.get("result_id")) for log in self.execution_logs
                ),
            }
        return {
            "total_logs": self._execution_log_summary.get("total_logs", 0),
            "dry_run_logs": self._execution_log_summary.get("dry_run_logs", 0),
            "real_run_logs": self._execution_log_summary.get("real_run_logs", 0),
            "success_accepted_logs": self._execution_log_summary.get("success_accepted_logs", 0),
            "failed_rejected_logs": self._execution_log_summary.get("failed_rejected_logs", 0),
            "logs_with_result_id": self._execution_log_summary.get("logs_with_result_id", 0),
        }

    def summarize_retry_tasks(self) -> dict[str, int]:
        retry_tasks = [
            task for task in self._tasks if task.metadata.get("retry_of_task_id")
        ]
        if retry_tasks:
            return {
                "total_retry_tasks": len(retry_tasks),
                "retry_tasks_pending": sum(
                    task.state == TaskState.PENDING for task in retry_tasks
                ),
                "retry_tasks_completed": sum(
                    task.state == TaskState.COMPLETED for task in retry_tasks
                ),
                "retry_tasks_failed": sum(
                    task.state == TaskState.FAILED for task in retry_tasks
                ),
            }
        return {
            "total_retry_tasks": self._retry_task_summary.get("total_retry_tasks", 0),
            "retry_tasks_pending": self._retry_task_summary.get("retry_tasks_pending", 0),
            "retry_tasks_completed": self._retry_task_summary.get("retry_tasks_completed", 0),
            "retry_tasks_failed": self._retry_task_summary.get("retry_tasks_failed", 0),
        }

    def summarize_real_dataset_readiness_reports(self) -> dict[str, object]:
        return dict(self._real_dataset_readiness_summary)

    def summarize_mock_runner_diagnostics(self) -> dict[str, int]:
        return {
            "total_checks": self._mock_runner_diagnostics_summary.get("total_checks", 0),
            "accepted_dry_run_outcomes": self._mock_runner_diagnostics_summary.get("accepted_dry_run_outcomes", 0),
            "rejected_outcomes": self._mock_runner_diagnostics_summary.get("rejected_outcomes", 0),
            "validation_failed_outcomes": self._mock_runner_diagnostics_summary.get("validation_failed_outcomes", 0),
        }

    def execute_task_with_lifecycle(
        self,
        task_id: str,
        _adapter_registry: object,
        *,
        dry_run: bool = False,
    ) -> TaskExecutionOutcome:
        self.execute_calls.append((task_id, dry_run))
        outcome = (
            self._manual_execute_outcome if dry_run else self._real_execute_outcome
        )
        return TaskExecutionOutcome(
            task_id=task_id,
            accepted=outcome.accepted,
            status=outcome.status,
            message=outcome.message,
            result_id=outcome.result_id,
            error_code=outcome.error_code,
            metadata=dict(outcome.metadata),
        )

    def create_retry_task(self, original_task_id: str) -> TaskRecord:
        original = next(
            (task for task in self._tasks if task.task_id == original_task_id),
            None,
        )
        if original is None:
            raise ValueError(f"Task does not exist: {original_task_id}")
        if original.state != TaskState.FAILED:
            raise ValueError(
                "Retry task can only be created from a failed task; "
                f"current state is {original.state.value}."
            )
        metadata = dict(original.metadata)
        metadata["retry_of_task_id"] = original.task_id
        metadata["original_task_id"] = original.task_id
        metadata["original_task_state"] = original.state.value
        retry = TaskRecord(
            task_id=f"retry-{original.task_id}",
            task_type=original.task_type,
            title=f"Retry: {original.title}",
            state=TaskState.PENDING,
            project_id=original.project_id,
            source_id=original.source_id,
            metadata=metadata,
        )
        self._tasks.append(retry)
        self.created_retry_tasks.append(retry)
        return retry

    def materialize_task_plan(self, plan_id: str) -> TaskRecord:
        plan = next((record for record in self._plans if record.plan_id == plan_id), None)
        if plan is None:
            raise ValueError(f"Task plan does not exist: {plan_id}")
        if plan.state != TaskPlanState.READY:
            raise ValueError(f"Task plan must be ready to materialize: {plan.plan_id}")
        task = TaskRecord(
            task_id=f"task-{plan.plan_id}",
            task_type=plan.plan_type,
            title=plan.title,
            state=TaskState.PENDING,
            project_id=plan.project_id,
            source_id=plan.plan_id,
            metadata={
                "source_plan_id": plan.plan_id,
                "plan_type": plan.plan_type,
                "analysis_id": plan.analysis_id,
                "analysis_profile_id": plan.analysis_profile_id,
                "project_id": plan.project_id,
                "requested_by": plan.requested_by,
                "parameters": dict(plan.parameters),
                "notes": plan.notes,
            },
        )
        self._tasks.append(task)
        self.materialized_tasks.append(task)
        return task

    def append_task_execution_log(
        self,
        task_id: str,
        *,
        source_plan_id: str | None = None,
        runner_type: str = "",
        task_type: str = "",
        dry_run: bool = True,
        outcome_status: str = "",
        message: str = "",
        error_code: str = "",
        result_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> object:
        log = {
            "task_id": task_id,
            "source_plan_id": source_plan_id,
            "runner_type": runner_type,
            "task_type": task_type,
            "dry_run": dry_run,
            "outcome_status": outcome_status,
            "message": message,
            "error_code": error_code,
            "result_id": result_id,
            "metadata": dict(metadata or {}),
        }
        self.execution_logs.append(log)
        return log

    def preview_result_artifact(self, result_id: str) -> ArtifactPreviewRecord:
        self.preview_calls.append(result_id)
        for result in self._results:
            if result.result_id == result_id:
                if result.artifact_path.endswith(".png"):
                    return ArtifactPreviewRecord(
                        artifact_path=result.artifact_path,
                        exists=True,
                        file_name=Path(result.artifact_path).name,
                        file_extension=".png",
                        size_bytes=10,
                        preview_available=False,
                        message="Artifact preview is not supported for .png files.",
                        error_code="unsupported",
                    )
                return ArtifactPreviewRecord(
                    artifact_path=result.artifact_path,
                    exists=not result.artifact_path.endswith("missing.csv"),
                    file_name=Path(result.artifact_path).name,
                    file_extension=Path(result.artifact_path).suffix,
                    size_bytes=24,
                    preview_available=not result.artifact_path.endswith("missing.csv"),
                    preview_text="analysis_id,value\nanalysis-ui,42"
                    if not result.artifact_path.endswith("missing.csv")
                    else "",
                    message=(
                        "Artifact preview available."
                        if not result.artifact_path.endswith("missing.csv")
                        else "Artifact file is missing."
                    ),
                    error_code="" if not result.artifact_path.endswith("missing.csv") else "missing",
                )
        return ArtifactPreviewRecord(
            artifact_path="",
            exists=False,
            preview_available=False,
            message=f"Task result does not exist: {result_id}",
            error_code="result_not_found",
        )

    def get_task_result_detail(self, result_id: str) -> TaskResultDetailRecord:
        self.detail_calls.append(result_id)
        for result in self._results:
            if result.result_id == result_id:
                metadata = dict(result.metadata)
                return TaskResultDetailRecord(
                    result_id=result.result_id,
                    result_type=result.result_type,
                    state=result.state,
                    title=result.title,
                    task_id=result.task_id,
                    source_task_id=str(metadata.get("source_task_id", result.task_id)),
                    analysis_id=str(metadata.get("analysis_id", "")),
                    analysis_profile_id=str(metadata.get("analysis_profile_id", "")),
                    project_id=str(metadata.get("project_id", "")),
                    artifact_path=result.artifact_path,
                    artifact_status=(
                        TaskResultArtifactStatus.MISSING
                        if result.artifact_path
                        else TaskResultArtifactStatus.NOT_APPLICABLE
                    ),
                    summary=result.summary,
                    metadata=metadata,
                    created_at=result.created_at,
                    updated_at=result.created_at,
                    message="Task result detail available.",
                )
        return TaskResultDetailRecord(
            result_id=result_id,
            result_type="",
            state=None,
            message=f"Task result does not exist: {result_id}",
            error_code="result_not_found",
        )


class MainWindowReportingSummaryTests(unittest.TestCase):
    def test_load_analysis_summary_uses_reporting_service_output(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_service = FakeReportingService()
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=fake_service,  # type: ignore[arg-type]
                task_service=FakeTaskService(),  # type: ignore[arg-type]
            )

            window.load_analysis_summary("analysis-ui")

        self.assertEqual(fake_service.requested_analysis_ids, ["analysis-ui"])
        self.assertEqual(window.reporting_profile_source_text(), "Profile: UI profile (aprof-ui)")
        app.processEvents()

    def test_load_selected_analysis_summary_uses_entered_analysis_id(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_service = FakeReportingService()
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=fake_service,  # type: ignore[arg-type]
                task_service=FakeTaskService(),  # type: ignore[arg-type]
            )

            window.set_selected_analysis_id(" analysis-selected ")
            window.load_selected_analysis_summary()

        self.assertEqual(fake_service.requested_analysis_ids, ["analysis-selected"])
        self.assertEqual(window.reporting_profile_source_text(), "Profile: UI profile (aprof-ui)")
        app.processEvents()

    def test_empty_selected_analysis_id_does_not_load_summary(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_service = FakeReportingService()
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=fake_service,  # type: ignore[arg-type]
                task_service=FakeTaskService(),  # type: ignore[arg-type]
            )

            window.set_selected_analysis_id("  ")
            window.load_selected_analysis_summary()

        self.assertEqual(fake_service.requested_analysis_ids, [])
        self.assertEqual(window.reporting_profile_source_text(), "Profile: Not linked")
        app.processEvents()

    def test_displays_registered_task_results_summary(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=FakeTaskService(
                    [
                        TaskResultRecord(
                            result_id="tres-ui",
                            task_id="task-ui",
                            result_type="profile_reporting_summary",
                            title="Profile reporting summary",
                            artifact_path="output/proj-ui/reporting/summary.csv",
                            metadata={
                                "analysis_id": "analysis-ui",
                                "analysis_profile_id": "aprof-ui",
                                "analysis_profile_name": "UI profile",
                            },
                        )
                    ],
                    plan_summary={
                        "total_plans": 4,
                        "draft_plans": 1,
                        "ready_plans": 1,
                        "disabled_plans": 1,
                        "archived_plans": 1,
                    },
                    plan_readiness_summary={
                        "total_plans": 4,
                        "materializable_plans": 1,
                        "blocked_plans": 3,
                        "ready_plans": 1,
                        "draft_plans": 1,
                        "disabled_plans": 1,
                        "archived_plans": 1,
                        "missing_context_plans": 0,
                    },
                    execution_contract_readiness_summary={
                        "total_tasks": 3,
                        "ready_tasks": 2,
                        "blocked_tasks": 1,
                        "validation_failed_tasks": 0,
                        "missing_context_tasks": 1,
                    },
                    execution_log_summary={
                        "total_logs": 5,
                        "dry_run_logs": 2,
                        "real_run_logs": 3,
                        "success_accepted_logs": 4,
                        "failed_rejected_logs": 1,
                        "logs_with_result_id": 2,
                    },
                    retry_task_summary={
                        "total_retry_tasks": 3,
                        "retry_tasks_pending": 1,
                        "retry_tasks_completed": 1,
                        "retry_tasks_failed": 1,
                    },
                    real_dataset_readiness_summary={
                        "dataset_id": "GSE33630",
                        "recommended_action": "ready_for_manual_review",
                        "gap_count": 0,
                        "preflight_runnable": True,
                        "feature_count": 54675,
                        "sample_count": 105,
                        "mapping_success_rate": 0.8373,
                        "detected_groups": ("ptc", "normal"),
                        "excluded_groups": ("atc",),
                        "blocking_gaps": (),
                        "warnings": ("manual_review",),
                    },
                    mock_runner_diagnostics_summary={
                        "total_checks": 3,
                        "accepted_dry_run_outcomes": 2,
                        "rejected_outcomes": 1,
                        "validation_failed_outcomes": 1,
                    },
                ),  # type: ignore[arg-type]
            )

        self.assertEqual(window.task_results_status_text(), "Task results: 1")
        self.assertEqual(window.task_result_artifact_status_text(), "Artifacts: present 0, missing 1, not applicable 0")
        self.assertEqual(window.task_plan_status_text(), "Task plans: total 4, draft 1, ready 1, disabled 1, archived 1")
        self.assertEqual(window.task_plan_materialization_readiness_text(), "Task plan materialization readiness: total 4, materializable 1, blocked 3, ready 1, draft 1, disabled 1, archived 1, missing context 0")
        self.assertEqual(window.task_execution_contract_readiness_text(), "Task execution contract readiness: total 3, ready 2, blocked 1, validation failed 0, missing context 1")
        self.assertEqual(window.task_execution_log_summary_text(), "Execution logs: total 5, dry-run 2, real-run 3, success/accepted 4, failed/rejected 1, with result 2")
        self.assertEqual(window.retry_task_summary_text(), "Retry tasks: total 3, pending 1, completed 1, failed 1")
        self.assertEqual(window.real_dataset_readiness_summary_text(), "Real dataset readiness: dataset GSE33630, recommended action ready_for_manual_review, gaps 0, preflight runnable yes, features 54675, samples 105, mapping success rate 0.8373, detected groups ptc, normal, excluded groups atc, blocking gaps none, warnings 1")
        self.assertEqual(window.mock_runner_diagnostics_text(), "Mock runner diagnostics: total checks 3, accepted dry-run outcomes 2, rejected outcomes 1, validation failed outcomes 1")
        self.assertEqual(window.runner_adapter_registry_text(), "Runner adapter registry: total adapters 0, adapter types none, supported task types none, no-op adapters 0")
        self.assertEqual(window.task_result_cell_text(0, 1), "profile_reporting_summary")
        self.assertEqual(window.task_result_cell_text(0, 4), "analysis-ui")
        self.assertEqual(window.task_result_cell_text(0, 5), "UI profile (aprof-ui)")
        self.assertEqual(window.task_result_cell_text(0, 7), "missing")
        app.processEvents()

    def test_empty_task_results_summary_shows_zero_artifact_counts(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=FakeTaskService(),  # type: ignore[arg-type]
            )

        self.assertEqual(window.task_results_status_text(), "Task results: 0")
        self.assertEqual(window.task_result_artifact_status_text(), "Artifacts: present 0, missing 0, not applicable 0")
        self.assertEqual(window.task_plan_status_text(), "Task plans: total 0, draft 0, ready 0, disabled 0, archived 0")
        self.assertEqual(window.task_plan_materialization_readiness_text(), "Task plan materialization readiness: total 0, materializable 0, blocked 0, ready 0, draft 0, disabled 0, archived 0, missing context 0")
        self.assertEqual(window.task_execution_contract_readiness_text(), "Task execution contract readiness: total 0, ready 0, blocked 0, validation failed 0, missing context 0")
        self.assertEqual(window.task_execution_log_summary_text(), "Execution logs: total 0, dry-run 0, real-run 0, success/accepted 0, failed/rejected 0, with result 0")
        self.assertEqual(window.retry_task_summary_text(), "Retry tasks: total 0, pending 0, completed 0, failed 0")
        self.assertEqual(window.analysis_preflight_summary_text(), "Analysis preflight summaries: total 0")
        self.assertEqual(window.real_dataset_readiness_summary_text(), "Real dataset readiness: no report loaded")
        self.assertEqual(window.mock_runner_diagnostics_text(), "Mock runner diagnostics: total checks 0, accepted dry-run outcomes 0, rejected outcomes 0, validation failed outcomes 0")
        self.assertEqual(window.runner_adapter_registry_text(), "Runner adapter registry: total adapters 0, adapter types none, supported task types none, no-op adapters 0")
        app.processEvents()

    def test_displays_real_dataset_readiness_summary_read_only(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            task_service = FakeTaskService(
                real_dataset_readiness_summary={
                    "dataset_id": "GSE27155",
                    "recommended_action": "resolve_platform_mapping",
                    "gap_count": 1,
                    "preflight_runnable": False,
                    "feature_count": 123,
                    "sample_count": 12,
                    "mapping_success_rate": 0.62,
                    "detected_groups": ("ptc",),
                    "excluded_groups": ("other",),
                    "blocking_gaps": ("gene_mapping_gap",),
                    "warnings": ("platform annotation incomplete",),
                }
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

        self.assertEqual(
            window.real_dataset_readiness_summary_text(),
            "Real dataset readiness: dataset GSE27155, recommended action resolve_platform_mapping, gaps 1, preflight runnable no, features 123, samples 12, mapping success rate 0.62, detected groups ptc, excluded groups other, blocking gaps gene_mapping_gap, warnings 1",
        )
        self.assertEqual(task_service.execute_calls, [])
        self.assertEqual(task_service.execution_logs, [])
        self.assertEqual(task_service.list_results_calls, 1)
        app.processEvents()

    def test_displays_analysis_preflight_summary_read_only(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            task_service = FakeTaskService(
                [
                    TaskResultRecord(
                        result_id="tres-preflight",
                        task_id="task-preflight",
                        result_type="analysis_preflight_summary",
                        title="Analysis preflight summary",
                        metadata={
                            "dataset_id": "GSE-preflight",
                            "profile_id": "profile-a",
                            "runnable": False,
                            "blocking_error_count": 1,
                            "warning_count": 3,
                            "recommended_action": "provide_expression_matrix",
                        },
                    )
                ]
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

        self.assertEqual(
            window.analysis_preflight_summary_text(),
            "Analysis preflight summaries: total 1, latest result tres-preflight, dataset GSE-preflight, profile profile-a, runnable no, blocking errors 1, warnings 3, recommended action provide_expression_matrix",
        )
        self.assertEqual(task_service.execute_calls, [])
        self.assertEqual(task_service.execution_logs, [])
        app.processEvents()

    def test_artifact_preview_displays_csv_preview(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService(
                [
                    TaskResultRecord(
                        result_id="result-csv",
                        task_id="task-ui",
                        result_type="profile_reporting_summary",
                        artifact_path="/tmp/summary.csv",
                    )
                ]
            )
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_result_id("result-csv")
            window.preview_selected_result_artifact()

        self.assertEqual(task_service.preview_calls, ["result-csv"])
        self.assertIn("status available", window.artifact_preview_status_text())
        self.assertIn("analysis-ui,42", window.artifact_preview_text())
        self.assertEqual(task_service.execute_calls, [])
        self.assertEqual(task_service.execution_logs, [])
        app.processEvents()

    def test_artifact_preview_displays_missing_and_unsupported(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService(
                [
                    TaskResultRecord(
                        result_id="result-missing",
                        task_id="task-ui",
                        result_type="profile_reporting_summary",
                        artifact_path="/tmp/missing.csv",
                    ),
                    TaskResultRecord(
                        result_id="result-png",
                        task_id="task-ui",
                        result_type="plot",
                        artifact_path="/tmp/plot.png",
                    ),
                ]
            )
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_result_id("result-missing")
            window.preview_selected_result_artifact()
            missing_status = window.artifact_preview_status_text()
            window.set_selected_result_id("result-png")
            window.preview_selected_result_artifact()

        self.assertIn("status missing", missing_status)
        self.assertIn("status unsupported", window.artifact_preview_status_text())
        self.assertEqual(window.artifact_preview_text(), "")
        self.assertEqual(task_service.execute_calls, [])
        app.processEvents()

    def test_empty_result_id_preview_is_stable(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService()
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_result_id("  ")
            window.preview_selected_result_artifact()

        self.assertEqual(window.artifact_preview_status_text(), "Artifact preview: no result selected")
        self.assertEqual(window.artifact_preview_text(), "")
        self.assertEqual(task_service.preview_calls, [])
        app.processEvents()

    def test_result_detail_viewer_displays_metadata_and_artifact_status(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService(
                [
                    TaskResultRecord(
                        result_id="result-detail",
                        task_id="task-ui",
                        result_type="profile_reporting_summary",
                        state=TaskResultState.AVAILABLE,
                        title="Profile reporting summary",
                        artifact_path="/tmp/summary.csv",
                        metadata={
                            "source_task_id": "task-ui",
                            "analysis_id": "analysis-ui",
                            "analysis_profile_id": "profile-ui",
                            "project_id": "project-ui",
                        },
                    )
                ]
            )
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_result_id("result-detail")
            window.load_selected_result_detail()

        self.assertEqual(task_service.detail_calls, ["result-detail"])
        self.assertIn("result result-detail", window.result_detail_text())
        self.assertIn("analysis analysis-ui", window.result_detail_text())
        self.assertIn("profile profile-ui", window.result_detail_text())
        self.assertIn("project project-ui", window.result_detail_text())
        self.assertIn("artifact status missing", window.result_detail_text())
        self.assertEqual(task_service.execute_calls, [])
        self.assertEqual(task_service.execution_logs, [])
        app.processEvents()

    def test_result_detail_viewer_handles_missing_and_empty_result(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService()
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_result_id("missing-result")
            window.load_selected_result_detail()
            missing_text = window.result_detail_text()
            window.set_selected_result_id("  ")
            window.load_selected_result_detail()

        self.assertIn("status result_not_found", missing_text)
        self.assertEqual(window.result_detail_text(), "Result detail: no result selected")
        self.assertEqual(task_service.detail_calls, ["missing-result"])
        self.assertEqual(task_service.execute_calls, [])
        app.processEvents()

    def test_manual_dry_run_execute_uses_selected_task_id_and_refreshes(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService()
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            initial_refresh_calls = task_service.list_results_calls
            window.set_selected_task_id(" task-dry-run ")
            window.click_dry_run_task_button()

        self.assertEqual(task_service.execute_calls, [("task-dry-run", True)])
        self.assertGreater(task_service.list_results_calls, initial_refresh_calls)
        self.assertEqual(
            window.manual_execute_status_text(),
            "Manual execute outcome: dry_run true, status skipped, message Dry-run accepted., error none, result none",
        )
        self.assertEqual(window.task_results_status_text(), "Task results: 0")
        self.assertEqual(window.task_result_artifact_status_text(), "Artifacts: present 0, missing 0, not applicable 0")
        app.processEvents()

    def test_manual_dry_run_without_selected_task_is_stable(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService()
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_task_id("  ")
            window.click_dry_run_task_button()

        self.assertEqual(task_service.execute_calls, [])
        self.assertEqual(
            window.manual_execute_status_text(),
            "Manual execute outcome: no task selected",
        )
        app.processEvents()

    def test_manual_dry_run_displays_blocked_outcome(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService(
                manual_execute_outcome=TaskExecutionOutcome(
                    task_id="task-completed",
                    accepted=False,
                    status=TaskExecutionOutcomeStatus.REJECTED,
                    message="Task is not pending.",
                    error_code="task_not_pending",
                )
            )
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_task_id("task-completed")
            window.click_dry_run_task_button()

        self.assertEqual(task_service.execute_calls, [("task-completed", True)])
        self.assertEqual(
            window.manual_execute_status_text(),
            "Manual execute outcome: dry_run true, status rejected, message Task is not pending., error task_not_pending, result none",
        )
        app.processEvents()

    def test_manual_dry_run_displays_result_id_when_outcome_has_one(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService(
                manual_execute_outcome=TaskExecutionOutcome(
                    task_id="task-dry-run",
                    accepted=True,
                    status=TaskExecutionOutcomeStatus.ACCEPTED,
                    message="Dry-run request accepted.",
                    result_id="result-preview",
                )
            )
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_task_id("task-dry-run")
            window.click_dry_run_task_button()

        self.assertEqual(task_service.execute_calls, [("task-dry-run", True)])
        self.assertEqual(
            window.manual_execute_status_text(),
            "Manual execute outcome: dry_run true, status accepted, message Dry-run request accepted., error none, result result-preview",
        )
        app.processEvents()

    def test_real_run_preflight_displays_pending_task_as_eligible(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService(
                tasks=[
                    TaskRecord(
                        task_id="task-pending",
                        task_type="profile_reporting_summary",
                        title="Pending report",
                        state=TaskState.PENDING,
                    )
                ]
            )
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )
            initial_refresh_calls = task_service.list_results_calls

            window.set_selected_task_id("task-pending")

        self.assertEqual(task_service.execute_calls, [])
        self.assertEqual(task_service.list_results_calls, initial_refresh_calls)
        self.assertFalse(window.real_run_button_enabled())
        self.assertEqual(
            window.real_run_preflight_status_text(),
            "Real-run preflight: selected task task-pending, task exists yes, task state pending, pending eligible yes, adapter available yes, dry-run recommended yes, real-run available in UI no, blocked reason dry_run_required",
        )
        app.processEvents()

    def test_real_run_preflight_displays_missing_task_as_blocked(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService()
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_task_id("missing-task")

        self.assertEqual(task_service.execute_calls, [])
        self.assertEqual(
            window.real_run_preflight_status_text(),
            "Real-run preflight: selected task missing-task, task exists no, task state missing, pending eligible no, adapter available no, dry-run recommended yes, real-run available in UI no, blocked reason task_missing",
        )
        app.processEvents()

    def test_real_run_preflight_blocks_non_pending_tasks(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        for state in (TaskState.RUNNING, TaskState.COMPLETED, TaskState.FAILED):
            with self.subTest(state=state.value), tempfile.TemporaryDirectory() as temp_dir:
                task_service = FakeTaskService(
                    tasks=[
                        TaskRecord(
                            task_id=f"task-{state.value}",
                            task_type="profile_reporting_summary",
                            title=f"{state.value} report",
                            state=state,
                        )
                    ]
                )
                data_dirs = DataDirectories(
                    root_dir=Path(temp_dir),
                    config_dir=Path(temp_dir) / "config",
                    logs_dir=Path(temp_dir) / "logs",
                    state_dir=Path(temp_dir) / "state",
                    cache_dir=Path(temp_dir) / "cache",
                )
                window = MainWindow(
                    config=AppConfig(app_name="model9-test"),
                    data_dirs=data_dirs,
                    reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                    task_service=task_service,  # type: ignore[arg-type]
                )

                window.set_selected_task_id(f"task-{state.value}")

            self.assertEqual(task_service.execute_calls, [])
            self.assertEqual(
                window.real_run_preflight_status_text(),
                f"Real-run preflight: selected task task-{state.value}, task exists yes, task state {state.value}, pending eligible no, adapter available yes, dry-run recommended yes, real-run available in UI no, blocked reason task_not_pending",
            )
        app.processEvents()

    def test_real_run_preflight_displays_adapter_unavailable(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService(
                tasks=[
                    TaskRecord(
                        task_id="task-unknown",
                        task_type="unknown.task",
                        title="Unknown task",
                        state=TaskState.PENDING,
                    )
                ]
            )
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_task_id("task-unknown")

        self.assertEqual(task_service.execute_calls, [])
        self.assertEqual(
            window.real_run_preflight_status_text(),
            "Real-run preflight: selected task task-unknown, task exists yes, task state pending, pending eligible yes, adapter available no, dry-run recommended yes, real-run available in UI no, blocked reason adapter_unavailable",
        )
        app.processEvents()

    def test_real_run_button_requires_same_task_dry_run_and_confirmation(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService(
                tasks=[
                    TaskRecord(
                        task_id="task-ready",
                        task_type="profile_reporting_summary",
                        title="Ready report",
                        state=TaskState.PENDING,
                    )
                ],
                real_execute_outcome=TaskExecutionOutcome(
                    task_id="task-ready",
                    accepted=True,
                    status=TaskExecutionOutcomeStatus.ACCEPTED,
                    message="Real-run completed.",
                    result_id="result-real",
                ),
            )
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )
            initial_refresh_calls = task_service.list_results_calls

            window.set_selected_task_id("task-ready")
            window.set_real_run_confirmation_text("REAL-RUN task-ready")
            window.click_real_run_task_button()
            window.click_dry_run_task_button()
            window.set_real_run_confirmation_text("REAL-RUN task-ready")
            self.assertTrue(window.real_run_button_enabled())
            window.click_real_run_task_button()

        self.assertEqual(
            task_service.execute_calls,
            [("task-ready", True), ("task-ready", False)],
        )
        self.assertEqual(
            task_service.execution_logs,
            [
                {
                    "task_id": "task-ready",
                    "source_plan_id": None,
                    "runner_type": "reporting_summary_runner",
                    "task_type": "profile_reporting_summary",
                    "dry_run": False,
                    "outcome_status": "accepted",
                    "message": "Real-run completed.",
                    "error_code": "",
                    "result_id": "result-real",
                    "metadata": {"source": "main_window"},
                }
            ],
        )
        self.assertGreater(task_service.list_results_calls, initial_refresh_calls)
        self.assertEqual(
            window.manual_execute_status_text(),
            "Manual execute outcome: dry_run false, status accepted, message Real-run completed., error none, result result-real",
        )
        self.assertEqual(
            window.task_execution_log_summary_text(),
            "Execution logs: total 1, dry-run 0, real-run 1, success/accepted 1, failed/rejected 0, with result 1",
        )
        self.assertFalse(window.real_run_button_enabled())
        app.processEvents()

    def test_real_run_button_requires_task_bound_confirmation_text(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService(
                tasks=[
                    TaskRecord(
                        task_id="task-ready",
                        task_type="profile_reporting_summary",
                        title="Ready report",
                        state=TaskState.PENDING,
                    )
                ]
            )
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_task_id("task-ready")
            window.click_dry_run_task_button()
            initial_refresh_calls = task_service.list_results_calls
            window.set_real_run_confirmation_text("REAL-RUN")
            window.execute_selected_task_real_run()

        self.assertEqual(task_service.execute_calls, [("task-ready", True)])
        self.assertEqual(task_service.execution_logs, [])
        self.assertGreater(task_service.list_results_calls, initial_refresh_calls)
        self.assertFalse(window.real_run_button_enabled())
        self.assertIn(
            "blocked reason confirmation_required",
            window.real_run_preflight_status_text(),
        )
        app.processEvents()

    def test_real_run_button_blocks_without_same_task_dry_run(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService(
                tasks=[
                    TaskRecord(
                        task_id="task-a",
                        task_type="profile_reporting_summary",
                        title="Task A",
                        state=TaskState.PENDING,
                    ),
                    TaskRecord(
                        task_id="task-b",
                        task_type="profile_reporting_summary",
                        title="Task B",
                        state=TaskState.PENDING,
                    ),
                ]
            )
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_task_id("task-a")
            window.click_dry_run_task_button()
            window.set_selected_task_id("task-b")
            initial_refresh_calls = task_service.list_results_calls
            window.set_real_run_confirmation_text("REAL-RUN task-b")
            window.execute_selected_task_real_run()

        self.assertEqual(task_service.execute_calls, [("task-a", True)])
        self.assertEqual(task_service.execution_logs, [])
        self.assertGreater(task_service.list_results_calls, initial_refresh_calls)
        self.assertFalse(window.real_run_button_enabled())
        self.assertEqual(
            window.manual_execute_status_text(),
            "Manual execute outcome: real_run blocked, status rejected, message Real-run preflight is not satisfied., error real_run_preflight_blocked, result none",
        )
        self.assertIn("blocked reason dry_run_required", window.real_run_preflight_status_text())
        app.processEvents()

    def test_real_run_refresh_failure_has_stable_status(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            task_service = FakeTaskService(
                tasks=[
                    TaskRecord(
                        task_id="task-ready",
                        task_type="profile_reporting_summary",
                        title="Ready report",
                        state=TaskState.PENDING,
                    )
                ],
                real_execute_outcome=TaskExecutionOutcome(
                    task_id="task-ready",
                    accepted=True,
                    status=TaskExecutionOutcomeStatus.ACCEPTED,
                    message="Real-run completed.",
                    result_id="result-real",
                ),
            )
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_task_id("task-ready")
            window.click_dry_run_task_button()
            window.set_real_run_confirmation_text("REAL-RUN task-ready")
            task_service.fail_list_results = True
            window.click_real_run_task_button()

        self.assertEqual(
            task_service.execute_calls,
            [("task-ready", True), ("task-ready", False)],
        )
        self.assertIn(
            "Manual execute outcome: dry_run false, status accepted",
            window.manual_execute_status_text(),
        )
        self.assertIn(
            "refresh failed: summary refresh unavailable",
            window.manual_execute_status_text(),
        )
        app.processEvents()

    def test_retry_creation_from_failed_task_creates_pending_retry(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            failed_task = TaskRecord(
                task_id="task-failed",
                task_type="profile_reporting_summary",
                title="Failed report",
                state=TaskState.FAILED,
                project_id="project-ui",
                source_id="analysis-ui",
                metadata={
                    "analysis_id": "analysis-ui",
                    "analysis_profile_id": "profile-ui",
                    "project_id": "project-ui",
                },
            )
            task_service = FakeTaskService(tasks=[failed_task])
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_task_id("task-failed")
            window.set_retry_confirmation_text("CREATE RETRY task-failed")
            window.click_create_retry_task_button()

        self.assertEqual(task_service.execute_calls, [])
        self.assertEqual(task_service.execution_logs, [])
        self.assertEqual(len(task_service.created_retry_tasks), 1)
        retry = task_service.created_retry_tasks[0]
        self.assertEqual(retry.task_id, "retry-task-failed")
        self.assertEqual(retry.state, TaskState.PENDING)
        self.assertEqual(retry.metadata["retry_of_task_id"], "task-failed")
        self.assertEqual(retry.metadata["analysis_id"], "analysis-ui")
        self.assertEqual(failed_task.state, TaskState.FAILED)
        self.assertEqual(task_service.list_results(), [])
        self.assertEqual(
            window.manual_execute_status_text(),
            "Retry creation outcome: status accepted, message Retry task created., error none, retry task retry-task-failed",
        )
        self.assertEqual(
            window.retry_task_summary_text(),
            "Retry tasks: total 1, pending 1, completed 0, failed 0",
        )
        app.processEvents()

    def test_retry_creation_rejects_non_failed_tasks(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        for state in (TaskState.PENDING, TaskState.RUNNING, TaskState.COMPLETED):
            with self.subTest(state=state.value), tempfile.TemporaryDirectory() as temp_dir:
                task = TaskRecord(
                    task_id=f"task-{state.value}",
                    task_type="profile_reporting_summary",
                    title=f"{state.value} report",
                    state=state,
                )
                task_service = FakeTaskService(tasks=[task])
                data_dirs = DataDirectories(
                    root_dir=Path(temp_dir),
                    config_dir=Path(temp_dir) / "config",
                    logs_dir=Path(temp_dir) / "logs",
                    state_dir=Path(temp_dir) / "state",
                    cache_dir=Path(temp_dir) / "cache",
                )
                window = MainWindow(
                    config=AppConfig(app_name="model9-test"),
                    data_dirs=data_dirs,
                    reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                    task_service=task_service,  # type: ignore[arg-type]
                )

                window.set_selected_task_id(f"task-{state.value}")
                window.set_retry_confirmation_text(f"CREATE RETRY task-{state.value}")
                window.click_create_retry_task_button()

                self.assertEqual(task_service.created_retry_tasks, [])
                self.assertEqual(task_service.execute_calls, [])
                self.assertEqual(task_service.execution_logs, [])
                self.assertEqual(task.state, state)
                self.assertIn(
                    f"current state is {state.value}",
                    window.manual_execute_status_text(),
                )
                self.assertEqual(
                    window.retry_task_summary_text(),
                    "Retry tasks: total 0, pending 0, completed 0, failed 0",
                )
        app.processEvents()

    def test_retry_creation_rejects_missing_task_and_missing_confirmation(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            failed_task = TaskRecord(
                task_id="task-failed",
                task_type="profile_reporting_summary",
                title="Failed report",
                state=TaskState.FAILED,
            )
            task_service = FakeTaskService(tasks=[failed_task])
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_task_id("task-failed")
            window.click_create_retry_task_button()
            confirmation_status = window.manual_execute_status_text()
            window.set_selected_task_id("missing-task")
            window.set_retry_confirmation_text("CREATE RETRY missing-task")
            window.click_create_retry_task_button()

        self.assertEqual(task_service.created_retry_tasks, [])
        self.assertEqual(task_service.execute_calls, [])
        self.assertEqual(task_service.execution_logs, [])
        self.assertIn("retry_confirmation_required", confirmation_status)
        self.assertIn("Task does not exist: missing-task", window.manual_execute_status_text())
        self.assertEqual(task_service.list_results(), [])
        app.processEvents()

    def test_task_plan_materialize_ready_plan_creates_pending_task(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            ready_plan = TaskPlanRecord(
                plan_id="plan-ready",
                title="Ready reporting plan",
                plan_type="profile_reporting_summary",
                state=TaskPlanState.READY,
                analysis_id="analysis-ui",
                analysis_profile_id="profile-ui",
                project_id="project-ui",
                requested_by="tester",
                parameters={"summary_format": "csv"},
                notes="materialize in UI",
            )
            task_service = FakeTaskService(plans=[ready_plan])
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_plan_id("plan-ready")
            window.set_plan_materialization_confirmation_text(
                "MATERIALIZE PLAN plan-ready"
            )
            window.click_materialize_task_plan_button()

        self.assertEqual(task_service.execute_calls, [])
        self.assertEqual(task_service.execution_logs, [])
        self.assertEqual(task_service.list_results(), [])
        self.assertEqual(len(task_service.materialized_tasks), 1)
        task = task_service.materialized_tasks[0]
        self.assertEqual(task.task_id, "task-plan-ready")
        self.assertEqual(task.state, TaskState.PENDING)
        self.assertEqual(task.metadata["source_plan_id"], "plan-ready")
        self.assertEqual(task.metadata["analysis_id"], "analysis-ui")
        self.assertEqual(task.metadata["analysis_profile_id"], "profile-ui")
        self.assertEqual(task.metadata["project_id"], "project-ui")
        self.assertEqual(task.metadata["parameters"], {"summary_format": "csv"})
        self.assertEqual(ready_plan.state, TaskPlanState.READY)
        self.assertEqual(
            window.manual_execute_status_text(),
            "Task plan materialization outcome: status accepted, message Task plan materialized., error none, task task-plan-ready",
        )
        self.assertEqual(
            window.task_plan_status_text(),
            "Task plans: total 1, draft 0, ready 1, disabled 0, archived 0",
        )
        self.assertEqual(
            window.task_plan_materialization_readiness_text(),
            "Task plan materialization readiness: total 1, materializable 1, blocked 0, ready 1, draft 0, disabled 0, archived 0, missing context 0",
        )
        app.processEvents()

    def test_task_plan_materialize_rejects_non_ready_plans(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        for state in (
            TaskPlanState.DRAFT,
            TaskPlanState.DISABLED,
            TaskPlanState.ARCHIVED,
        ):
            with self.subTest(state=state.value), tempfile.TemporaryDirectory() as temp_dir:
                plan = TaskPlanRecord(
                    plan_id=f"plan-{state.value}",
                    title=f"{state.value} plan",
                    plan_type="profile_reporting_summary",
                    state=state,
                )
                task_service = FakeTaskService(plans=[plan])
                data_dirs = DataDirectories(
                    root_dir=Path(temp_dir),
                    config_dir=Path(temp_dir) / "config",
                    logs_dir=Path(temp_dir) / "logs",
                    state_dir=Path(temp_dir) / "state",
                    cache_dir=Path(temp_dir) / "cache",
                )
                window = MainWindow(
                    config=AppConfig(app_name="model9-test"),
                    data_dirs=data_dirs,
                    reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                    task_service=task_service,  # type: ignore[arg-type]
                )

                window.set_selected_plan_id(f"plan-{state.value}")
                window.set_plan_materialization_confirmation_text(
                    f"MATERIALIZE PLAN plan-{state.value}"
                )
                window.click_materialize_task_plan_button()

                self.assertEqual(task_service.materialized_tasks, [])
                self.assertEqual(task_service.execute_calls, [])
                self.assertEqual(task_service.execution_logs, [])
                self.assertEqual(task_service.list_results(), [])
                self.assertEqual(plan.state, state)
                self.assertIn(
                    f"Task plan must be ready to materialize: plan-{state.value}",
                    window.manual_execute_status_text(),
                )
        app.processEvents()

    def test_task_plan_materialize_rejects_missing_plan_and_missing_confirmation(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            ready_plan = TaskPlanRecord(
                plan_id="plan-ready",
                title="Ready reporting plan",
                plan_type="profile_reporting_summary",
                state=TaskPlanState.READY,
            )
            task_service = FakeTaskService(plans=[ready_plan])
            data_dirs = DataDirectories(
                root_dir=Path(temp_dir),
                config_dir=Path(temp_dir) / "config",
                logs_dir=Path(temp_dir) / "logs",
                state_dir=Path(temp_dir) / "state",
                cache_dir=Path(temp_dir) / "cache",
            )
            window = MainWindow(
                config=AppConfig(app_name="model9-test"),
                data_dirs=data_dirs,
                reporting_service=FakeReportingService(),  # type: ignore[arg-type]
                task_service=task_service,  # type: ignore[arg-type]
            )

            window.set_selected_plan_id("plan-ready")
            window.click_materialize_task_plan_button()
            confirmation_status = window.manual_execute_status_text()
            window.set_selected_plan_id("missing-plan")
            window.set_plan_materialization_confirmation_text(
                "MATERIALIZE PLAN missing-plan"
            )
            window.click_materialize_task_plan_button()

        self.assertEqual(task_service.materialized_tasks, [])
        self.assertEqual(task_service.execute_calls, [])
        self.assertEqual(task_service.execution_logs, [])
        self.assertEqual(task_service.list_results(), [])
        self.assertIn("plan_materialization_confirmation_required", confirmation_status)
        self.assertIn(
            "Task plan does not exist: missing-plan",
            window.manual_execute_status_text(),
        )
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
