import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.task_management import TaskManagementService
from core.task_models import (
    TaskExecutionOutcome,
    TaskExecutionOutcomeStatus,
)
from core.task_runner_adapters import (
    REPORTING_SUMMARY_TASK_TYPE,
    RunnerAdapterRegistry,
)
from scripts.run_task_once import main


class FakeRunnerAdapter:
    def __init__(self, outcome: TaskExecutionOutcome) -> None:
        self._outcome = outcome
        self.seen_requests = []

    @property
    def runner_type(self) -> str:
        return "fake_runner"

    @property
    def supported_task_types(self) -> tuple[str, ...]:
        return (REPORTING_SUMMARY_TASK_TYPE,)

    def supports(self, task_type: str) -> bool:
        return task_type == REPORTING_SUMMARY_TASK_TYPE

    def execute(self, request):
        self.seen_requests.append(request)
        return self._outcome


def registry_with(adapter: FakeRunnerAdapter) -> RunnerAdapterRegistry:
    registry = RunnerAdapterRegistry()
    registry.register(adapter)
    return registry


class RunTaskOnceScriptTests(unittest.TestCase):
    def test_help_runs(self) -> None:
        output = io.StringIO()
        with self.assertRaises(SystemExit) as raised:
            with contextlib.redirect_stdout(output):
                main(["--help"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("Run one task", output.getvalue())

    def test_missing_task_id_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = io.StringIO()
            errors = io.StringIO()
            with self.assertRaises(SystemExit) as raised:
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    main(["--state-dir", str(Path(temp_dir) / "state")])

        self.assertNotEqual(raised.exception.code, 0)
        self.assertIn("--task-id", errors.getvalue())

    def test_dry_run_does_not_change_task_state_or_create_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state_dir = root / "state"
            service = TaskManagementService.from_state_dir(state_dir)
            task = service.create_task(
                REPORTING_SUMMARY_TASK_TYPE,
                "Profile reporting summary",
                project_id="project-1",
                metadata={
                    "analysis_id": "analysis-1",
                    "analysis_profile_id": "profile-1",
                    "project_id": "project-1",
                },
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                result = main(
                    [
                        "--task-id",
                        task.task_id,
                        "--state-dir",
                        str(state_dir),
                    ]
                )
            reloaded = service.list_tasks()[0]
            results = service.list_results()
            logs = service.list_task_execution_logs_for_task(task.task_id)

        self.assertEqual(result, 0)
        self.assertIn("- dry_run: true", output.getvalue())
        self.assertIn("- status: skipped", output.getvalue())
        self.assertEqual(reloaded.state.value, "pending")
        self.assertEqual(results, [])
        self.assertEqual(len(logs), 1)
        self.assertTrue(logs[0].dry_run)
        self.assertEqual(logs[0].outcome_status, "skipped")
        self.assertEqual(logs[0].task_type, REPORTING_SUMMARY_TASK_TYPE)
        self.assertEqual(logs[0].runner_type, "reporting_summary_runner")
        self.assertFalse((root / "output").exists())

    def test_dry_run_flag_is_explicit_and_state_neutral(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state_dir = root / "state"
            service = TaskManagementService.from_state_dir(state_dir)
            task = service.create_task(
                REPORTING_SUMMARY_TASK_TYPE,
                "Profile reporting summary",
                project_id="project-1",
                metadata={"analysis_id": "analysis-1"},
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                result = main(
                    [
                        "--task-id",
                        task.task_id,
                        "--state-dir",
                        str(state_dir),
                        "--dry-run",
                    ]
                )
            reloaded = service.list_tasks()[0]
            logs = service.list_task_execution_logs_for_task(task.task_id)

        self.assertEqual(result, 0)
        self.assertIn("- dry_run: true", output.getvalue())
        self.assertEqual(reloaded.state.value, "pending")
        self.assertEqual(len(logs), 1)
        self.assertTrue(logs[0].dry_run)

    def test_missing_task_returns_rejected_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir) / "state"
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                result = main(
                    [
                        "--task-id",
                        "missing-task",
                        "--state-dir",
                        str(state_dir),
                    ]
                )
            service = TaskManagementService.from_state_dir(state_dir)
            logs = service.list_task_execution_logs_for_task("missing-task")

        self.assertEqual(result, 1)
        self.assertIn("- accepted: false", output.getvalue())
        self.assertIn("- error_code: task_not_found", output.getvalue())
        self.assertEqual(len(logs), 1)
        self.assertTrue(logs[0].dry_run)
        self.assertEqual(logs[0].outcome_status, "rejected")
        self.assertEqual(logs[0].error_code, "task_not_found")

    def test_adapter_missing_logs_rejected_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir) / "state"
            service = TaskManagementService.from_state_dir(state_dir)
            task = service.create_task("unknown.task", "Unknown task")

            with contextlib.redirect_stdout(io.StringIO()):
                result = main(
                    [
                        "--task-id",
                        task.task_id,
                        "--state-dir",
                        str(state_dir),
                    ]
                )
            logs = service.list_task_execution_logs_for_task(task.task_id)

        self.assertEqual(result, 1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].task_type, "unknown.task")
        self.assertEqual(logs[0].error_code, "missing_runner_adapter")

    def test_validation_failure_logs_rejected_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir) / "state"
            service = TaskManagementService.from_state_dir(state_dir)
            task = service.create_task(
                REPORTING_SUMMARY_TASK_TYPE,
                "Profile reporting summary missing analysis",
            )

            with contextlib.redirect_stdout(io.StringIO()):
                result = main(
                    [
                        "--task-id",
                        task.task_id,
                        "--state-dir",
                        str(state_dir),
                    ]
                )
            logs = service.list_task_execution_logs_for_task(task.task_id)

        self.assertEqual(result, 1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].runner_type, "reporting_summary_runner")
        self.assertEqual(logs[0].error_code, "missing_analysis_id")

    def test_dry_run_does_not_execute_other_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state_dir = root / "state"
            service = TaskManagementService.from_state_dir(state_dir)
            selected = service.create_task(
                REPORTING_SUMMARY_TASK_TYPE,
                "Selected profile reporting summary",
                metadata={"analysis_id": "analysis-1"},
            )
            other = service.create_task(
                REPORTING_SUMMARY_TASK_TYPE,
                "Other profile reporting summary",
                metadata={"analysis_id": "analysis-2"},
            )

            with contextlib.redirect_stdout(io.StringIO()):
                result = main(
                    [
                        "--task-id",
                        selected.task_id,
                        "--state-dir",
                        str(state_dir),
                    ]
                )
            tasks = {task.task_id: task for task in service.list_tasks()}
            logs = service.list_task_execution_logs()

        self.assertEqual(result, 0)
        self.assertEqual(tasks[selected.task_id].state.value, "pending")
        self.assertEqual(tasks[other.task_id].state.value, "pending")
        self.assertEqual(service.list_results(), [])
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].task_id, selected.task_id)

    def test_real_run_fake_success_logs_result_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state_dir = root / "state"
            service = TaskManagementService.from_state_dir(state_dir)
            task = service.create_task(
                REPORTING_SUMMARY_TASK_TYPE,
                "Profile reporting summary",
                project_id="project-1",
                metadata={"analysis_id": "analysis-1"},
            )
            adapter = FakeRunnerAdapter(
                TaskExecutionOutcome(
                    task_id=task.task_id,
                    accepted=True,
                    status=TaskExecutionOutcomeStatus.ACCEPTED,
                    message="fake success",
                    result_id="tres-fake",
                )
            )

            with patch(
                "scripts.run_task_once.build_runner_registry",
                return_value=registry_with(adapter),
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    result = main(
                        [
                            "--task-id",
                            task.task_id,
                            "--state-dir",
                            str(state_dir),
                            "--real-run",
                        ]
                    )
            reloaded = service.list_tasks()[0]
            logs = service.list_task_execution_logs_for_task(task.task_id)

        self.assertEqual(result, 0)
        self.assertEqual(reloaded.state.value, "completed")
        self.assertEqual(len(logs), 1)
        self.assertFalse(logs[0].dry_run)
        self.assertEqual(logs[0].runner_type, "fake_runner")
        self.assertEqual(logs[0].outcome_status, "accepted")
        self.assertEqual(logs[0].result_id, "tres-fake")

    def test_real_run_fake_failure_logs_error_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state_dir = root / "state"
            service = TaskManagementService.from_state_dir(state_dir)
            task = service.create_task(
                REPORTING_SUMMARY_TASK_TYPE,
                "Profile reporting summary",
                project_id="project-1",
                metadata={"analysis_id": "analysis-1"},
            )
            adapter = FakeRunnerAdapter(
                TaskExecutionOutcome(
                    task_id=task.task_id,
                    accepted=False,
                    status=TaskExecutionOutcomeStatus.REJECTED,
                    message="fake failure",
                    error_code="fake_error",
                )
            )

            with patch(
                "scripts.run_task_once.build_runner_registry",
                return_value=registry_with(adapter),
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    result = main(
                        [
                            "--task-id",
                            task.task_id,
                            "--state-dir",
                            str(state_dir),
                            "--real-run",
                        ]
                    )
            reloaded = service.list_tasks()[0]
            logs = service.list_task_execution_logs_for_task(task.task_id)

        self.assertEqual(result, 1)
        self.assertEqual(reloaded.state.value, "failed")
        self.assertEqual(len(logs), 1)
        self.assertFalse(logs[0].dry_run)
        self.assertEqual(logs[0].outcome_status, "rejected")
        self.assertEqual(logs[0].error_code, "fake_error")
        self.assertEqual(logs[0].message, "fake failure")

    def test_execution_logs_do_not_affect_result_or_artifact_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state_dir = root / "state"
            service = TaskManagementService.from_state_dir(state_dir)
            task = service.create_task(
                REPORTING_SUMMARY_TASK_TYPE,
                "Profile reporting summary",
                metadata={"analysis_id": "analysis-1"},
            )

            with contextlib.redirect_stdout(io.StringIO()):
                main(
                    [
                        "--task-id",
                        task.task_id,
                        "--state-dir",
                        str(state_dir),
                    ]
                )
            results = service.list_results()
            diagnostics = service.inspect_result_artifacts()

        self.assertEqual(results, [])
        self.assertEqual(diagnostics, [])


if __name__ == "__main__":
    unittest.main()
