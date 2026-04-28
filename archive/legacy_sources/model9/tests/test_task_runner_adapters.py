import tempfile
import unittest
from pathlib import Path

from core.task_management import TaskManagementService
from core.task_models import (
    TaskExecutionOutcomeStatus,
    TaskExecutionRequest,
)
from core.task_runner_adapters import (
    REPORTING_SUMMARY_FORMAT,
    REPORTING_SUMMARY_TASK_TYPE,
    NoOpRunnerAdapter,
    ReportingSummaryRunnerAdapter,
    RunnerAdapterRegistry,
    format_reporting_runner_dry_run_summary,
    format_runner_adapter_registry_summary,
    summarize_reporting_runner_dry_run,
    validate_reporting_summary_runner_request,
)


class RunnerAdapterRegistryTests(unittest.TestCase):
    def test_registry_registers_and_lists_adapter(self) -> None:
        registry = RunnerAdapterRegistry()
        adapter = NoOpRunnerAdapter(("profile_reporting_summary",))

        registry.register(adapter)

        self.assertEqual(registry.list_adapters(), [adapter])

    def test_registry_finds_adapter_by_task_type(self) -> None:
        registry = RunnerAdapterRegistry()
        adapter = NoOpRunnerAdapter(("profile_reporting_summary",))
        registry.register(adapter)

        found = registry.get_for_task_type("profile_reporting_summary")

        self.assertIs(found, adapter)

    def test_registry_returns_none_for_unmatched_task_type(self) -> None:
        registry = RunnerAdapterRegistry()
        registry.register(NoOpRunnerAdapter(("profile_reporting_summary",)))

        self.assertIsNone(registry.get_for_task_type("analysis.run"))

    def test_no_op_adapter_can_support_all_task_types(self) -> None:
        adapter = NoOpRunnerAdapter()

        self.assertTrue(adapter.supports("analysis.run"))
        self.assertTrue(adapter.supports("profile_reporting_summary"))

    def test_registry_summarizes_adapters(self) -> None:
        registry = RunnerAdapterRegistry()
        registry.register(NoOpRunnerAdapter(("profile_reporting_summary",)))

        summary = registry.summarize_adapters()

        self.assertEqual(summary.total_adapters, 1)
        self.assertEqual(summary.adapter_types, ("no_op",))
        self.assertEqual(summary.supported_task_types, ("profile_reporting_summary",))
        self.assertEqual(summary.no_op_adapters, 1)
        self.assertEqual(summary.to_dict()["total_adapters"], 1)

    def test_formatter_reports_empty_registry_summary(self) -> None:
        lines = format_runner_adapter_registry_summary(None)

        self.assertEqual(
            lines,
            [
                "Runner adapter registry:",
                "- total adapters: 0",
                "- adapter types: none",
                "- supported task types: none",
                "- no-op adapters: 0",
            ],
        )

    def test_formatter_reports_no_op_adapter_summary(self) -> None:
        registry = RunnerAdapterRegistry()
        registry.register(NoOpRunnerAdapter(("profile_reporting_summary",)))

        lines = format_runner_adapter_registry_summary(
            registry.summarize_adapters()
        )

        self.assertIn("Runner adapter registry:", lines)
        self.assertIn("- total adapters: 1", lines)
        self.assertIn("- adapter types: no_op", lines)
        self.assertIn("- supported task types: profile_reporting_summary", lines)
        self.assertIn("- no-op adapters: 1", lines)

    def test_no_op_adapter_execute_returns_not_implemented_outcome(self) -> None:
        adapter = NoOpRunnerAdapter(("profile_reporting_summary",))
        request = TaskExecutionRequest(
            task_id="task-1",
            task_type="profile_reporting_summary",
            analysis_id="analysis-1",
        )

        outcome = adapter.execute(request)

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.REJECTED)
        self.assertEqual(outcome.error_code, "not_implemented")
        self.assertEqual(outcome.metadata["runner_type"], "no_op")
        self.assertEqual(outcome.metadata["task_type"], "profile_reporting_summary")

    def test_registry_and_no_op_adapter_do_not_create_results_or_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_path = root / "should-not-exist.csv"
            registry = RunnerAdapterRegistry()
            adapter = NoOpRunnerAdapter(("profile_reporting_summary",))
            registry.register(adapter)
            request = TaskExecutionRequest(
                task_id="task-1",
                task_type="profile_reporting_summary",
                parameters={"artifact_path": str(artifact_path)},
            )

            found = registry.get_for_task_type(request.task_type)
            self.assertIsNotNone(found)
            assert found is not None
            outcome = found.execute(request)

        self.assertFalse(outcome.accepted)
        self.assertFalse(artifact_path.exists())

    def test_manual_wrapper_can_use_registry_no_op_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root / "state")
            task = service.create_task(
                "analysis.run",
                "Run analysis",
                metadata={"analysis_id": "analysis-1"},
            )
            registry = RunnerAdapterRegistry()
            registry.register(NoOpRunnerAdapter(("analysis.run",)))

            outcome = service.execute_task_with_adapter(
                task.task_id,
                registry,
                dry_run=True,
            )
            reloaded = service.list_tasks()[0]

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.error_code, "not_implemented")
        self.assertEqual(reloaded.state.value, "pending")

    def test_reporting_summary_runner_validation_accepts_minimal_request(self) -> None:
        request = TaskExecutionRequest(
            task_id="task-1",
            task_type=REPORTING_SUMMARY_TASK_TYPE,
            analysis_id="analysis-1",
        )

        validation = validate_reporting_summary_runner_request(request)

        self.assertTrue(validation.valid)
        self.assertEqual(validation.reason_code, "ready")
        self.assertTrue(validation.to_dict()["valid"])

    def test_reporting_summary_runner_validation_accepts_supported_format(self) -> None:
        request = TaskExecutionRequest(
            task_id="task-1",
            task_type=REPORTING_SUMMARY_TASK_TYPE,
            analysis_id="analysis-1",
            parameters={"format": REPORTING_SUMMARY_FORMAT},
        )

        validation = validate_reporting_summary_runner_request(request)

        self.assertTrue(validation.valid)

    def test_reporting_summary_runner_validation_rejects_missing_task_id(self) -> None:
        request = TaskExecutionRequest(
            task_id=" ",
            task_type=REPORTING_SUMMARY_TASK_TYPE,
            analysis_id="analysis-1",
        )

        validation = validate_reporting_summary_runner_request(request)

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason_code, "missing_task_id")

    def test_reporting_summary_runner_validation_rejects_wrong_task_type(self) -> None:
        request = TaskExecutionRequest(
            task_id="task-1",
            task_type="analysis.run",
            analysis_id="analysis-1",
        )

        validation = validate_reporting_summary_runner_request(request)

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason_code, "unsupported_task_type")

    def test_reporting_summary_runner_validation_rejects_missing_analysis_id(self) -> None:
        request = TaskExecutionRequest(
            task_id="task-1",
            task_type=REPORTING_SUMMARY_TASK_TYPE,
        )

        validation = validate_reporting_summary_runner_request(request)

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason_code, "missing_analysis_id")

    def test_reporting_summary_runner_validation_rejects_unsupported_format(self) -> None:
        request = TaskExecutionRequest(
            task_id="task-1",
            task_type=REPORTING_SUMMARY_TASK_TYPE,
            analysis_id="analysis-1",
            parameters={"format": "json"},
        )

        validation = validate_reporting_summary_runner_request(request)

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason_code, "unsupported_format")

    def test_reporting_summary_runner_validation_does_not_create_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "summary.csv"
            request = TaskExecutionRequest(
                task_id="task-1",
                task_type=REPORTING_SUMMARY_TASK_TYPE,
                analysis_id="analysis-1",
                parameters={"artifact_path": str(artifact_path)},
            )

            validation = validate_reporting_summary_runner_request(request)

            self.assertTrue(validation.valid)
            self.assertFalse(artifact_path.exists())

    def test_reporting_adapter_supports_reporting_summary_task_type(self) -> None:
        adapter = ReportingSummaryRunnerAdapter()

        self.assertTrue(adapter.supports(REPORTING_SUMMARY_TASK_TYPE))
        self.assertEqual(adapter.runner_type, "reporting_summary_runner")
        self.assertEqual(adapter.supported_task_types, (REPORTING_SUMMARY_TASK_TYPE,))

    def test_reporting_adapter_does_not_support_unknown_task_type(self) -> None:
        adapter = ReportingSummaryRunnerAdapter()

        self.assertFalse(adapter.supports("analysis.run"))

    def test_reporting_adapter_dry_run_returns_skipped_outcome(self) -> None:
        adapter = ReportingSummaryRunnerAdapter()
        request = TaskExecutionRequest(
            task_id="task-1",
            task_type=REPORTING_SUMMARY_TASK_TYPE,
            analysis_id="analysis-1",
            dry_run=True,
        )

        outcome = adapter.execute(request)

        self.assertTrue(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.SKIPPED)
        self.assertEqual(outcome.error_code, "")
        self.assertEqual(outcome.metadata["runner_type"], "reporting_summary_runner")
        self.assertEqual(outcome.metadata["dry_run"], True)

    def test_reporting_adapter_non_dry_run_without_dependencies_is_rejected(self) -> None:
        adapter = ReportingSummaryRunnerAdapter()
        request = TaskExecutionRequest(
            task_id="task-1",
            task_type=REPORTING_SUMMARY_TASK_TYPE,
            analysis_id="analysis-1",
            project_id="project-1",
            dry_run=False,
        )

        outcome = adapter.execute(request)

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.REJECTED)
        self.assertEqual(outcome.error_code, "missing_runner_dependency")
        self.assertEqual(outcome.metadata["dry_run"], False)
        self.assertEqual(outcome.metadata["failure_result_policy"], "no_failed_result")
        self.assertEqual(outcome.metadata["failed_result_registered"], False)

    def test_reporting_adapter_invalid_request_returns_rejected(self) -> None:
        adapter = ReportingSummaryRunnerAdapter()
        request = TaskExecutionRequest(
            task_id="task-1",
            task_type=REPORTING_SUMMARY_TASK_TYPE,
        )

        outcome = adapter.execute(request)

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.REJECTED)
        self.assertEqual(outcome.error_code, "missing_analysis_id")
        self.assertEqual(outcome.metadata["failure_result_policy"], "no_failed_result")
        self.assertEqual(outcome.metadata["failed_result_registered"], False)

    def test_reporting_adapter_execute_does_not_create_results_or_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "summary.csv"
            adapter = ReportingSummaryRunnerAdapter()
            request = TaskExecutionRequest(
                task_id="task-1",
                task_type=REPORTING_SUMMARY_TASK_TYPE,
                analysis_id="analysis-1",
                parameters={"artifact_path": str(artifact_path)},
            )

            outcome = adapter.execute(request)

            self.assertTrue(outcome.accepted)
            self.assertFalse(artifact_path.exists())

    def test_registry_finds_reporting_adapter_by_task_type(self) -> None:
        registry = RunnerAdapterRegistry()
        adapter = ReportingSummaryRunnerAdapter()
        registry.register(adapter)

        found = registry.get_for_task_type(REPORTING_SUMMARY_TASK_TYPE)

        self.assertIs(found, adapter)

    def test_reporting_runner_dry_run_formatter_reports_empty_summary(self) -> None:
        lines = format_reporting_runner_dry_run_summary(None)

        self.assertEqual(
            lines,
            [
                "Reporting runner dry-run:",
                "- supported task types: none",
                "- dry-run accepted: 0",
                "- rejected: 0",
                "- not implemented: 0",
            ],
        )

    def test_reporting_runner_dry_run_summary_counts_accepted_request(self) -> None:
        request = TaskExecutionRequest(
            task_id="task-1",
            task_type=REPORTING_SUMMARY_TASK_TYPE,
            analysis_id="analysis-1",
            dry_run=True,
        )

        summary = summarize_reporting_runner_dry_run([request])

        self.assertEqual(summary.supported_task_types, (REPORTING_SUMMARY_TASK_TYPE,))
        self.assertEqual(summary.dry_run_accepted, 1)
        self.assertEqual(summary.rejected, 0)
        self.assertEqual(summary.not_implemented, 0)

    def test_reporting_runner_dry_run_summary_counts_rejected_request(self) -> None:
        request = TaskExecutionRequest(
            task_id="task-1",
            task_type=REPORTING_SUMMARY_TASK_TYPE,
            dry_run=True,
        )

        summary = summarize_reporting_runner_dry_run([request])

        self.assertEqual(summary.dry_run_accepted, 0)
        self.assertEqual(summary.rejected, 1)
        self.assertEqual(summary.not_implemented, 0)

    def test_reporting_runner_dry_run_summary_counts_not_implemented_request(self) -> None:
        request = TaskExecutionRequest(
            task_id="task-1",
            task_type=REPORTING_SUMMARY_TASK_TYPE,
            analysis_id="analysis-1",
            project_id="project-1",
            dry_run=False,
        )

        summary = summarize_reporting_runner_dry_run([request])

        self.assertEqual(summary.dry_run_accepted, 0)
        self.assertEqual(summary.rejected, 0)
        self.assertEqual(summary.not_implemented, 1)

    def test_reporting_runner_dry_run_formatter_reports_counts(self) -> None:
        requests = [
            TaskExecutionRequest(
                task_id="task-1",
                task_type=REPORTING_SUMMARY_TASK_TYPE,
                analysis_id="analysis-1",
                dry_run=True,
            ),
            TaskExecutionRequest(
                task_id="task-2",
                task_type=REPORTING_SUMMARY_TASK_TYPE,
                dry_run=True,
            ),
            TaskExecutionRequest(
                task_id="task-3",
                task_type=REPORTING_SUMMARY_TASK_TYPE,
                analysis_id="analysis-3",
                project_id="project-3",
                dry_run=False,
            ),
        ]

        lines = format_reporting_runner_dry_run_summary(
            summarize_reporting_runner_dry_run(requests)
        )

        self.assertIn("- supported task types: profile_reporting_summary", lines)
        self.assertIn("- dry-run accepted: 1", lines)
        self.assertIn("- rejected: 1", lines)
        self.assertIn("- not implemented: 1", lines)

    def test_reporting_runner_dry_run_summary_does_not_create_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "summary.csv"
            request = TaskExecutionRequest(
                task_id="task-1",
                task_type=REPORTING_SUMMARY_TASK_TYPE,
                analysis_id="analysis-1",
                parameters={"artifact_path": str(artifact_path)},
                dry_run=True,
            )

            summary = summarize_reporting_runner_dry_run([request])

            self.assertEqual(summary.dry_run_accepted, 1)
            self.assertFalse(artifact_path.exists())


if __name__ == "__main__":
    unittest.main()
