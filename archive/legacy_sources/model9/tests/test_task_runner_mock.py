import tempfile
import unittest
from pathlib import Path

from core.task_management import (
    TaskManagementService,
    format_mock_runner_diagnostics_summary,
)
from core.task_models import (
    TaskExecutionOutcomeStatus,
    TaskExecutionRequest,
    TaskPlanState,
)
from core.task_status import TaskState


class TaskRunnerMockTests(unittest.TestCase):
    def test_valid_dry_run_request_returns_skipped_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            request = TaskExecutionRequest(
                task_id="task-1",
                task_type="analysis.run",
                dry_run=True,
            )

            outcome = service.run_task_execution_request_mock(request)

        self.assertTrue(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.SKIPPED)
        self.assertIsNone(outcome.result_id)
        self.assertEqual(outcome.metadata["dry_run"], True)

    def test_invalid_request_returns_rejected_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            request = TaskExecutionRequest(task_id="task-1", task_type="")

            outcome = service.run_task_execution_request_mock(request)

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.REJECTED)
        self.assertEqual(outcome.error_code, "contract_validation_failed")
        self.assertIn("task_type is required", outcome.message)
        self.assertIsNone(outcome.result_id)

    def test_mock_runner_does_not_create_result_change_task_or_create_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")
            plan = service.create_task_plan(
                "analysis.run",
                "Mock only",
                project_id="proj-runner",
                parameters={"artifact_path": str(root_dir / "mock-output.csv")},
            )
            service.update_task_plan_state(plan.plan_id, TaskPlanState.READY)
            task = service.materialize_task_plan(plan.plan_id)
            request = service.build_task_execution_request(task.task_id)
            artifact_path = Path(request.parameters["artifact_path"])

            outcome = service.run_task_execution_request_mock(request)
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertTrue(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.SKIPPED)
        self.assertEqual(reloaded.state, TaskState.PENDING)
        self.assertEqual(results, [])
        self.assertFalse(artifact_path.exists())

    def test_non_dry_run_request_is_accepted_but_not_executed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            task = service.create_task("analysis.run", "Mock non dry run")
            request = service.build_task_execution_request(task.task_id, dry_run=False)

            outcome = service.run_task_execution_request_mock(request)
            reloaded = service.list_tasks()[0]

        self.assertTrue(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.ACCEPTED)
        self.assertEqual(reloaded.state, TaskState.PENDING)
        self.assertEqual(service.list_results(), [])

    def test_mock_runner_diagnostics_summary_counts_valid_and_invalid_requests(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            summary = service.summarize_mock_runner_diagnostics(
                [
                    TaskExecutionRequest(
                        task_id="task-valid",
                        task_type="analysis.run",
                        dry_run=True,
                    ),
                    TaskExecutionRequest(
                        task_id="task-invalid",
                        task_type="",
                        dry_run=True,
                    ),
                ]
            )

        self.assertEqual(
            summary,
            {
                "total_checks": 2,
                "accepted_dry_run_outcomes": 1,
                "rejected_outcomes": 1,
                "validation_failed_outcomes": 1,
            },
        )

    def test_mock_runner_diagnostics_formatter_handles_empty_summary(self) -> None:
        lines = format_mock_runner_diagnostics_summary(None)

        self.assertEqual(lines[0], "Mock task runner diagnostics:")
        self.assertIn("- total checks: 0", lines)
        self.assertIn("- accepted dry run outcomes: 0", lines)
        self.assertIn("- rejected outcomes: 0", lines)
        self.assertIn("- validation failed outcomes: 0", lines)

    def test_mock_runner_diagnostics_from_tasks_does_not_create_results_or_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")
            task = service.create_task(
                "analysis.run",
                "Dry run check",
                metadata={"parameters": {"artifact_path": str(root_dir / "mock.csv")}},
            )

            summary = service.summarize_mock_runner_diagnostics()
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertEqual(summary["total_checks"], 1)
        self.assertEqual(summary["accepted_dry_run_outcomes"], 1)
        self.assertEqual(reloaded.task_id, task.task_id)
        self.assertEqual(reloaded.state, TaskState.PENDING)
        self.assertEqual(results, [])
        self.assertFalse((root_dir / "mock.csv").exists())


if __name__ == "__main__":
    unittest.main()
