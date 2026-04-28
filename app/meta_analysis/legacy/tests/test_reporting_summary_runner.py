import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from core.task_management import TaskManagementService
from core.task_models import (
    TaskExecutionOutcomeStatus,
    TaskExecutionRequest,
    TaskResultArtifactStatus,
)
from core.task_runner_adapters import (
    REPORTING_SUMMARY_TASK_TYPE,
    ReportingSummaryRunnerAdapter,
    RunnerAdapterRegistry,
)


@dataclass
class FakeArtifact:
    path: Path


class FakeReportingService:
    def __init__(self, artifact_path: Path, *, fail: bool = False) -> None:
        self.artifact_path = artifact_path
        self.fail = fail
        self.requested_analysis_ids: list[str] = []

    def export_analysis_summary_csv(self, analysis_id: str) -> FakeArtifact:
        self.requested_analysis_ids.append(analysis_id)
        if self.fail:
            raise ValueError("export failed")
        return FakeArtifact(path=self.artifact_path)


class ExplodingRunnerAdapter:
    @property
    def runner_type(self) -> str:
        return "exploding"

    @property
    def supported_task_types(self) -> tuple[str, ...]:
        return (REPORTING_SUMMARY_TASK_TYPE,)

    def supports(self, task_type: str) -> bool:
        return task_type == REPORTING_SUMMARY_TASK_TYPE

    def execute(self, request: TaskExecutionRequest):
        raise RuntimeError("adapter exploded")


class ReportingSummaryRunnerTests(unittest.TestCase):
    def _service(self, root: Path) -> TaskManagementService:
        return TaskManagementService.from_state_dir(root / "state")

    def _request(
        self,
        service: TaskManagementService,
        *,
        dry_run: bool,
        project_id: str | None = "project-1",
    ):
        task = service.create_task(
            REPORTING_SUMMARY_TASK_TYPE,
            "Profile reporting summary",
            project_id=project_id,
            metadata={
                "analysis_id": "analysis-1",
                "analysis_profile_id": "profile-1",
                "project_id": project_id,
                "requested_by": "tester",
            },
        )
        return task, service.build_task_execution_request(
            task.task_id,
            dry_run=dry_run,
        )

    def test_dry_run_does_not_call_reporting_service_or_create_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, request = self._request(service, dry_run=True)
            adapter = ReportingSummaryRunnerAdapter(
                reporting_service=reporting,
                task_service=service,
            )

            outcome = adapter.execute(request)
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertTrue(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.SKIPPED)
        self.assertEqual(reporting.requested_analysis_ids, [])
        self.assertEqual(results, [])
        self.assertEqual(reloaded.task_id, task.task_id)
        self.assertEqual(reloaded.state.value, "pending")
        self.assertFalse(artifact_path.exists())

    def test_non_dry_run_exports_and_registers_profile_reporting_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, request = self._request(service, dry_run=False)
            adapter = ReportingSummaryRunnerAdapter(
                reporting_service=reporting,
                task_service=service,
            )

            outcome = adapter.execute(request)
            results = service.list_results()
            reloaded = service.list_tasks()[0]

        self.assertTrue(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.ACCEPTED)
        self.assertEqual(reporting.requested_analysis_ids, ["analysis-1"])
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(outcome.result_id, result.result_id)
        self.assertEqual(result.result_type, "profile_reporting_summary")
        self.assertEqual(result.artifact_path, str(artifact_path))
        self.assertEqual(result.metadata["analysis_id"], "analysis-1")
        self.assertEqual(result.metadata["analysis_profile_id"], "profile-1")
        self.assertEqual(result.metadata["project_id"], "project-1")
        self.assertEqual(result.metadata["source_task_id"], task.task_id)
        self.assertEqual(result.metadata["runner_type"], "reporting_summary_runner")
        self.assertEqual(reloaded.state.value, "pending")

    def test_export_failure_returns_rejected_without_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path, fail=True)
            task, request = self._request(service, dry_run=False)
            adapter = ReportingSummaryRunnerAdapter(
                reporting_service=reporting,
                task_service=service,
            )

            outcome = adapter.execute(request)
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.REJECTED)
        self.assertEqual(outcome.error_code, "reporting_export_failed")
        self.assertIn("export failed", outcome.message)
        self.assertEqual(outcome.metadata["failure_result_policy"], "no_failed_result")
        self.assertEqual(outcome.metadata["failed_result_registered"], False)
        self.assertEqual(reporting.requested_analysis_ids, ["analysis-1"])
        self.assertEqual(results, [])
        self.assertEqual(reloaded.task_id, task.task_id)
        self.assertEqual(reloaded.state.value, "pending")
        self.assertFalse(artifact_path.exists())

    def test_registration_failure_returns_rejected_without_success_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            request = TaskExecutionRequest(
                task_id="missing-task",
                task_type=REPORTING_SUMMARY_TASK_TYPE,
                analysis_id="analysis-1",
                analysis_profile_id="profile-1",
                project_id="project-1",
                dry_run=False,
            )
            adapter = ReportingSummaryRunnerAdapter(
                reporting_service=reporting,
                task_service=service,
            )

            outcome = adapter.execute(request)
            results = service.list_results()

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.REJECTED)
        self.assertEqual(outcome.error_code, "result_registration_failed")
        self.assertIn("registration failed", outcome.message)
        self.assertEqual(outcome.metadata["failure_result_policy"], "no_failed_result")
        self.assertEqual(outcome.metadata["failed_result_registered"], False)
        self.assertEqual(reporting.requested_analysis_ids, ["analysis-1"])
        self.assertEqual(results, [])

    def test_non_dry_run_without_project_id_is_rejected_without_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            _task, request = self._request(
                service,
                dry_run=False,
                project_id=None,
            )
            adapter = ReportingSummaryRunnerAdapter(
                reporting_service=reporting,
                task_service=service,
            )

            outcome = adapter.execute(request)
            results = service.list_results()

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.error_code, "missing_project_id")
        self.assertEqual(reporting.requested_analysis_ids, [])
        self.assertEqual(results, [])

    def test_runner_result_is_listed_by_task_management_service(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, request = self._request(service, dry_run=False)
            adapter = ReportingSummaryRunnerAdapter(
                reporting_service=reporting,
                task_service=service,
            )

            outcome = adapter.execute(request)
            results = service.list_results(
                task_id=task.task_id,
                result_type="profile_reporting_summary",
            )

        self.assertTrue(outcome.accepted)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].result_id, outcome.result_id)
        self.assertEqual(results[0].artifact_path, str(artifact_path))

    def test_runner_result_artifact_diagnostic_reports_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            artifact_path.write_text("analysis_id\nanalysis-1\n", encoding="utf-8")
            reporting = FakeReportingService(artifact_path)
            task, request = self._request(service, dry_run=False)
            adapter = ReportingSummaryRunnerAdapter(
                reporting_service=reporting,
                task_service=service,
            )

            adapter.execute(request)
            diagnostics = service.inspect_result_artifacts(task_id=task.task_id)
            summary = service.summarize_task_result_artifacts(diagnostics)
            reloaded = service.list_tasks()[0]

        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(
            diagnostics[0].artifact_status,
            TaskResultArtifactStatus.PRESENT,
        )
        self.assertEqual(summary["present_artifacts"], 1)
        self.assertEqual(summary["missing_artifacts"], 0)
        self.assertEqual(reloaded.state.value, "pending")

    def test_runner_result_artifact_diagnostic_reports_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "missing-summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, request = self._request(service, dry_run=False)
            adapter = ReportingSummaryRunnerAdapter(
                reporting_service=reporting,
                task_service=service,
            )

            adapter.execute(request)
            diagnostics = service.inspect_result_artifacts(task_id=task.task_id)
            summary = service.summarize_task_result_artifacts(diagnostics)
            reloaded = service.list_tasks()[0]

        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(
            diagnostics[0].artifact_status,
            TaskResultArtifactStatus.MISSING,
        )
        self.assertEqual(summary["present_artifacts"], 0)
        self.assertEqual(summary["missing_artifacts"], 1)
        self.assertEqual(reloaded.state.value, "pending")

    def test_manual_wrapper_dry_run_uses_reporting_adapter_without_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, _request = self._request(service, dry_run=True)
            registry = RunnerAdapterRegistry()
            registry.register(
                ReportingSummaryRunnerAdapter(
                    reporting_service=reporting,
                    task_service=service,
                )
            )

            outcome = service.execute_task_with_adapter(
                task.task_id,
                registry,
                dry_run=True,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertTrue(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.SKIPPED)
        self.assertEqual(reporting.requested_analysis_ids, [])
        self.assertEqual(results, [])
        self.assertEqual(reloaded.state.value, "pending")
        self.assertFalse(artifact_path.exists())

    def test_manual_wrapper_missing_adapter_returns_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            task, _request = self._request(service, dry_run=True)
            registry = RunnerAdapterRegistry()

            outcome = service.execute_task_with_adapter(
                task.task_id,
                registry,
                dry_run=True,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.REJECTED)
        self.assertEqual(outcome.error_code, "missing_runner_adapter")
        self.assertEqual(results, [])
        self.assertEqual(reloaded.state.value, "pending")

    def test_manual_wrapper_diagnostics_reports_missing_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            task, _request = self._request(service, dry_run=True)
            registry = RunnerAdapterRegistry()

            summary = service.summarize_manual_runner_wrapper_diagnostics(
                registry,
                task_ids=[task.task_id],
            )
            results = service.list_results()
            reloaded = service.list_tasks()[0]

        self.assertEqual(summary["dry_run_checks"], 1)
        self.assertEqual(summary["accepted_outcomes"], 0)
        self.assertEqual(summary["rejected_outcomes"], 1)
        self.assertEqual(summary["missing_adapter_outcomes"], 1)
        self.assertEqual(results, [])
        self.assertEqual(reloaded.state.value, "pending")

    def test_manual_wrapper_non_dry_run_creates_reporting_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, _request = self._request(service, dry_run=False)
            registry = RunnerAdapterRegistry()
            registry.register(
                ReportingSummaryRunnerAdapter(
                    reporting_service=reporting,
                    task_service=service,
                )
            )

            outcome = service.execute_task_with_adapter(
                task.task_id,
                registry,
                dry_run=False,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertTrue(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.ACCEPTED)
        self.assertEqual(reporting.requested_analysis_ids, ["analysis-1"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].result_type, "profile_reporting_summary")
        self.assertEqual(results[0].artifact_path, str(artifact_path))
        self.assertEqual(reloaded.state.value, "pending")

    def test_manual_wrapper_does_not_execute_other_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            selected_task, _request = self._request(service, dry_run=False)
            other_task = service.create_task(
                REPORTING_SUMMARY_TASK_TYPE,
                "Other profile reporting summary",
                project_id="project-2",
                metadata={
                    "analysis_id": "analysis-2",
                    "analysis_profile_id": "profile-2",
                    "project_id": "project-2",
                },
            )
            registry = RunnerAdapterRegistry()
            registry.register(
                ReportingSummaryRunnerAdapter(
                    reporting_service=reporting,
                    task_service=service,
                )
            )

            outcome = service.execute_task_with_adapter(
                selected_task.task_id,
                registry,
                dry_run=False,
            )
            results = service.list_results()
            tasks = {task.task_id: task for task in service.list_tasks()}

        self.assertTrue(outcome.accepted)
        self.assertEqual(reporting.requested_analysis_ids, ["analysis-1"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_id, selected_task.task_id)
        self.assertEqual(tasks[selected_task.task_id].state.value, "pending")
        self.assertEqual(tasks[other_task.task_id].state.value, "pending")

    def test_lifecycle_wrapper_dry_run_does_not_change_state_or_create_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, _request = self._request(service, dry_run=True)
            registry = RunnerAdapterRegistry()
            registry.register(
                ReportingSummaryRunnerAdapter(
                    reporting_service=reporting,
                    task_service=service,
                )
            )

            outcome = service.execute_task_with_lifecycle(
                task.task_id,
                registry,
                dry_run=True,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertTrue(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.SKIPPED)
        self.assertEqual(reporting.requested_analysis_ids, [])
        self.assertEqual(results, [])
        self.assertEqual(reloaded.state.value, "pending")
        self.assertFalse(artifact_path.exists())

    def test_lifecycle_wrapper_diagnostics_dry_run_does_not_mutate_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, _request = self._request(service, dry_run=True)
            registry = RunnerAdapterRegistry()
            registry.register(
                ReportingSummaryRunnerAdapter(
                    reporting_service=reporting,
                    task_service=service,
                )
            )

            summary = service.summarize_lifecycle_runner_wrapper_diagnostics(
                registry
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertEqual(summary["dry_run_checks"], 1)
        self.assertEqual(summary["accepted_outcomes"], 1)
        self.assertEqual(summary["rejected_outcomes"], 0)
        self.assertEqual(summary["state_mutations"], 0)
        self.assertEqual(reporting.requested_analysis_ids, [])
        self.assertEqual(reloaded.task_id, task.task_id)
        self.assertEqual(reloaded.state.value, "pending")
        self.assertEqual(results, [])
        self.assertFalse(artifact_path.exists())

    def test_lifecycle_wrapper_diagnostics_missing_adapter_reports_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            task, _request = self._request(service, dry_run=True)
            registry = RunnerAdapterRegistry()

            summary = service.summarize_lifecycle_runner_wrapper_diagnostics(
                registry
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertEqual(summary["dry_run_checks"], 1)
        self.assertEqual(summary["accepted_outcomes"], 0)
        self.assertEqual(summary["rejected_outcomes"], 1)
        self.assertEqual(summary["state_mutations"], 0)
        self.assertEqual(reloaded.task_id, task.task_id)
        self.assertEqual(reloaded.state.value, "pending")
        self.assertEqual(results, [])

    def test_lifecycle_guard_diagnostics_are_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            task, _request = self._request(service, dry_run=True)

            summary = service.summarize_lifecycle_guard_diagnostics()
            reloaded = service.list_tasks()[0]
            results = service.list_results()
            logs = service.list_task_execution_logs()

        self.assertEqual(summary["pending_allowed"], True)
        self.assertEqual(summary["running_blocked"], True)
        self.assertEqual(summary["completed_blocked"], True)
        self.assertEqual(summary["failed_blocked"], True)
        self.assertEqual(summary["dry_run_mutations"], 0)
        self.assertEqual(reloaded.task_id, task.task_id)
        self.assertEqual(reloaded.state.value, "pending")
        self.assertEqual(results, [])
        self.assertEqual(logs, [])

    def test_lifecycle_wrapper_non_dry_run_success_completes_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, _request = self._request(service, dry_run=False)
            registry = RunnerAdapterRegistry()
            registry.register(
                ReportingSummaryRunnerAdapter(
                    reporting_service=reporting,
                    task_service=service,
                )
            )

            outcome = service.execute_task_with_lifecycle(
                task.task_id,
                registry,
                dry_run=False,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()
            diagnostics = service.inspect_result_artifacts(task_id=task.task_id)

        self.assertTrue(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.ACCEPTED)
        self.assertEqual(reloaded.state.value, "completed")
        self.assertEqual(reloaded.message, "Lifecycle runner completed.")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].result_id, outcome.result_id)
        self.assertEqual(diagnostics[0].artifact_status, TaskResultArtifactStatus.MISSING)

    def test_lifecycle_wrapper_export_failure_marks_task_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path, fail=True)
            task, _request = self._request(service, dry_run=False)
            registry = RunnerAdapterRegistry()
            registry.register(
                ReportingSummaryRunnerAdapter(
                    reporting_service=reporting,
                    task_service=service,
                )
            )

            outcome = service.execute_task_with_lifecycle(
                task.task_id,
                registry,
                dry_run=False,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.error_code, "reporting_export_failed")
        self.assertEqual(reloaded.state.value, "failed")
        self.assertEqual(results, [])
        self.assertFalse(artifact_path.exists())

    def test_lifecycle_wrapper_missing_adapter_keeps_task_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            task, _request = self._request(service, dry_run=False)
            registry = RunnerAdapterRegistry()

            outcome = service.execute_task_with_lifecycle(
                task.task_id,
                registry,
                dry_run=False,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.error_code, "missing_runner_adapter")
        self.assertEqual(outcome.metadata["task_state_policy"], "kept_pending")
        self.assertEqual(reloaded.state.value, "pending")
        self.assertEqual(results, [])

    def test_lifecycle_wrapper_non_pending_task_does_not_execute(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, _request = self._request(service, dry_run=False)
            service.start_task(task.task_id, "already running")
            registry = RunnerAdapterRegistry()
            registry.register(
                ReportingSummaryRunnerAdapter(
                    reporting_service=reporting,
                    task_service=service,
                )
            )

            outcome = service.execute_task_with_lifecycle(
                task.task_id,
                registry,
                dry_run=False,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.error_code, "task_not_pending")
        self.assertEqual(reporting.requested_analysis_ids, [])
        self.assertEqual(reloaded.state.value, "running")
        self.assertEqual(results, [])

    def test_lifecycle_wrapper_completed_task_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, _request = self._request(service, dry_run=False)
            service.complete_task(task.task_id, message="already completed")
            registry = RunnerAdapterRegistry()
            registry.register(
                ReportingSummaryRunnerAdapter(
                    reporting_service=reporting,
                    task_service=service,
                )
            )

            outcome = service.execute_task_with_lifecycle(
                task.task_id,
                registry,
                dry_run=False,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.error_code, "task_not_pending")
        self.assertEqual(outcome.metadata["task_state"], "completed")
        self.assertEqual(outcome.metadata["task_state_policy"], "blocked_non_pending")
        self.assertEqual(reporting.requested_analysis_ids, [])
        self.assertEqual(reloaded.state.value, "completed")
        self.assertEqual(results, [])
        self.assertFalse(artifact_path.exists())

    def test_lifecycle_wrapper_failed_task_is_blocked_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, _request = self._request(service, dry_run=False)
            service.fail_task(task.task_id, "already failed")
            existing_results = service.list_results()
            registry = RunnerAdapterRegistry()
            registry.register(
                ReportingSummaryRunnerAdapter(
                    reporting_service=reporting,
                    task_service=service,
                )
            )

            outcome = service.execute_task_with_lifecycle(
                task.task_id,
                registry,
                dry_run=False,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.error_code, "task_not_pending")
        self.assertEqual(outcome.metadata["task_state"], "failed")
        self.assertEqual(outcome.metadata["task_state_policy"], "blocked_non_pending")
        self.assertEqual(reporting.requested_analysis_ids, [])
        self.assertEqual(reloaded.state.value, "failed")
        self.assertEqual(len(results), len(existing_results))
        self.assertFalse(artifact_path.exists())

    def test_lifecycle_wrapper_dry_run_blocks_non_pending_without_state_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            task, _request = self._request(service, dry_run=True)
            service.start_task(task.task_id, "already running")
            registry = RunnerAdapterRegistry()
            registry.register(
                ReportingSummaryRunnerAdapter(
                    reporting_service=reporting,
                    task_service=service,
                )
            )

            outcome = service.execute_task_with_lifecycle(
                task.task_id,
                registry,
                dry_run=True,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.error_code, "task_not_pending")
        self.assertEqual(outcome.metadata["dry_run"], True)
        self.assertEqual(outcome.metadata["task_state"], "running")
        self.assertEqual(reporting.requested_analysis_ids, [])
        self.assertEqual(reloaded.state.value, "running")
        self.assertEqual(results, [])
        self.assertFalse(artifact_path.exists())

    def test_lifecycle_wrapper_adapter_exception_marks_task_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            task, _request = self._request(service, dry_run=False)
            registry = RunnerAdapterRegistry()
            registry.register(ExplodingRunnerAdapter())

            outcome = service.execute_task_with_lifecycle(
                task.task_id,
                registry,
                dry_run=False,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.error_code, "runner_adapter_exception")
        self.assertEqual(reloaded.state.value, "failed")
        self.assertEqual(results, [])

    def test_lifecycle_wrapper_does_not_execute_other_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            artifact_path = root / "summary.csv"
            reporting = FakeReportingService(artifact_path)
            selected_task, _request = self._request(service, dry_run=False)
            other_task = service.create_task(
                REPORTING_SUMMARY_TASK_TYPE,
                "Other profile reporting summary",
                project_id="project-2",
                metadata={
                    "analysis_id": "analysis-2",
                    "analysis_profile_id": "profile-2",
                    "project_id": "project-2",
                },
            )
            registry = RunnerAdapterRegistry()
            registry.register(
                ReportingSummaryRunnerAdapter(
                    reporting_service=reporting,
                    task_service=service,
                )
            )

            outcome = service.execute_task_with_lifecycle(
                selected_task.task_id,
                registry,
                dry_run=False,
            )
            tasks = {task.task_id: task for task in service.list_tasks()}
            results = service.list_results()

        self.assertTrue(outcome.accepted)
        self.assertEqual(reporting.requested_analysis_ids, ["analysis-1"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_id, selected_task.task_id)
        self.assertEqual(tasks[selected_task.task_id].state.value, "completed")
        self.assertEqual(tasks[other_task.task_id].state.value, "pending")

    def test_real_run_preflight_reports_pending_task_as_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            task, _request = self._request(service, dry_run=False)
            registry = RunnerAdapterRegistry()
            registry.register(ReportingSummaryRunnerAdapter())

            summary = service.summarize_real_run_preflight_diagnostics(registry)
            reloaded = service.list_tasks()[0]
            results = service.list_results()
            logs = service.list_task_execution_logs()

        self.assertEqual(summary["checked_tasks"], 1)
        self.assertEqual(summary["eligible_tasks"], 1)
        self.assertEqual(summary["blocked_tasks"], 0)
        self.assertEqual(summary["adapter_missing"], 0)
        self.assertEqual(summary["state_mutations"], 0)
        self.assertEqual(reloaded.task_id, task.task_id)
        self.assertEqual(reloaded.state.value, "pending")
        self.assertEqual(results, [])
        self.assertEqual(logs, [])

    def test_real_run_preflight_reports_non_pending_and_missing_adapter_as_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = self._service(root)
            running, _request = self._request(service, dry_run=False)
            service.start_task(running.task_id)
            missing_adapter = service.create_task(
                "unknown.task",
                "Unknown task",
            )
            registry = RunnerAdapterRegistry()
            registry.register(ReportingSummaryRunnerAdapter())

            summary = service.summarize_real_run_preflight_diagnostics(registry)
            tasks = {task.task_id: task for task in service.list_tasks()}
            results = service.list_results()
            logs = service.list_task_execution_logs()

        self.assertEqual(summary["checked_tasks"], 2)
        self.assertEqual(summary["eligible_tasks"], 0)
        self.assertEqual(summary["blocked_tasks"], 2)
        self.assertEqual(summary["adapter_missing"], 1)
        self.assertEqual(summary["state_mutations"], 0)
        self.assertEqual(tasks[running.task_id].state.value, "running")
        self.assertEqual(tasks[missing_adapter.task_id].state.value, "pending")
        self.assertEqual(results, [])
        self.assertEqual(logs, [])


if __name__ == "__main__":
    unittest.main()
