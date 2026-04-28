import tempfile
import unittest
from pathlib import Path

from core.task_management import TaskManagementService
from core.task_models import (
    TaskExecutionContractReason,
    TaskExecutionOutcomeStatus,
    TaskExecutionRequest,
    TaskRecord,
    TaskPlanState,
)
from core.task_store import TaskRecordStore
from core.task_status import TaskState


class TaskExecutionContractTests(unittest.TestCase):
    def test_materialized_task_builds_execution_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            plan = service.create_task_plan(
                "analysis.run",
                "Run planned analysis",
                analysis_id="analysis-1",
                analysis_profile_id="aprof-1",
                project_id="proj-contract",
                requested_by="tester",
                parameters={"alpha": 0.05},
            )
            service.update_task_plan_state(plan.plan_id, TaskPlanState.READY)
            task = service.materialize_task_plan(plan.plan_id)

            request = service.build_task_execution_request(task.task_id)

        self.assertEqual(request.task_id, task.task_id)
        self.assertEqual(request.task_type, "analysis.run")
        self.assertEqual(request.source_plan_id, plan.plan_id)
        self.assertEqual(request.analysis_id, "analysis-1")
        self.assertEqual(request.analysis_profile_id, "aprof-1")
        self.assertEqual(request.project_id, "proj-contract")
        self.assertEqual(request.parameters, {"alpha": 0.05})
        self.assertEqual(request.requested_by, "tester")
        self.assertTrue(request.dry_run)

    def test_build_execution_request_does_not_mutate_task_or_create_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")
            task = service.create_task(
                "reporting.summary",
                "Build request only",
                project_id="proj-contract",
                source_id="tplan-source",
                metadata={
                    "source_plan_id": "tplan-source",
                    "analysis_id": "analysis-1",
                    "parameters": {"format": "csv"},
                },
            )
            artifact_path = root_dir / "should-not-exist.csv"

            request = service.build_task_execution_request(task.task_id)
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertEqual(request.source_plan_id, "tplan-source")
        self.assertEqual(reloaded.state, TaskState.PENDING)
        self.assertEqual(results, [])
        self.assertFalse(artifact_path.exists())

    def test_missing_task_execution_request_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))

            with self.assertRaisesRegex(ValueError, "Task does not exist"):
                service.build_task_execution_request("missing-task")

    def test_validate_execution_request_accepts_complete_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            request = TaskExecutionRequest(
                task_id="task-1",
                task_type="analysis.run",
                parameters={"alpha": 0.05},
            )

            service.validate_task_execution_request(request)

    def test_validate_execution_request_rejects_missing_task_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            request = TaskExecutionRequest(task_id="", task_type="analysis.run")

            with self.assertRaisesRegex(ValueError, "task_id is required"):
                service.validate_task_execution_request(request)

    def test_validate_execution_request_rejects_missing_task_type(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            request = TaskExecutionRequest(task_id="task-1", task_type="")

            with self.assertRaisesRegex(ValueError, "task_type is required"):
                service.validate_task_execution_request(request)

    def test_build_rejected_execution_outcome_is_contract_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))

            outcome = service.build_rejected_execution_outcome(
                "task-1",
                error_code="contract_validation_failed",
                message="Missing task_type.",
                metadata={"field": "task_type"},
            )

        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.status, TaskExecutionOutcomeStatus.REJECTED)
        self.assertEqual(outcome.error_code, "contract_validation_failed")
        self.assertEqual(outcome.metadata["field"], "task_type")

    def test_execution_contract_readiness_reports_valid_task_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            task = service.create_task("analysis.run", "Ready contract")

            diagnostics = service.inspect_task_execution_contract_readiness()

        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].task_id, task.task_id)
        self.assertTrue(diagnostics[0].can_build_request)
        self.assertTrue(diagnostics[0].contract_valid)
        self.assertEqual(diagnostics[0].reason_code, TaskExecutionContractReason.READY)

    def test_execution_contract_readiness_reports_malformed_task_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = TaskRecordStore(Path(temp_dir))
            store.save_task(TaskRecord(task_id="task-bad", task_type="", title="Bad task"))
            service = TaskManagementService(store)

            diagnostics = service.inspect_task_execution_contract_readiness()

        self.assertEqual(len(diagnostics), 1)
        self.assertFalse(diagnostics[0].can_build_request)
        self.assertFalse(diagnostics[0].contract_valid)
        self.assertEqual(
            diagnostics[0].reason_code,
            TaskExecutionContractReason.MISSING_TASK_TYPE,
        )

    def test_execution_contract_readiness_summary_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = TaskRecordStore(Path(temp_dir))
            service = TaskManagementService(store)
            service.create_task("analysis.run", "Ready contract")
            store.save_task(TaskRecord(task_id="task-bad", task_type="", title="Bad task"))

            summary = service.summarize_task_execution_contract_readiness()

        self.assertEqual(
            summary,
            {
                "total_tasks": 2,
                "ready_tasks": 1,
                "blocked_tasks": 1,
                "validation_failed_tasks": 0,
                "missing_context_tasks": 1,
            },
        )

    def test_execution_contract_readiness_does_not_create_results_or_change_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            task = service.create_task("analysis.run", "Ready contract")

            service.inspect_task_execution_contract_readiness()
            service.summarize_task_execution_contract_readiness()
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertEqual(reloaded.task_id, task.task_id)
        self.assertEqual(reloaded.state, TaskState.PENDING)
        self.assertEqual(results, [])

    def test_execution_contract_readiness_formatter_handles_empty_summary(self) -> None:
        from core.task_management import format_task_execution_contract_readiness_summary

        lines = format_task_execution_contract_readiness_summary(None)

        self.assertEqual(lines[0], "Task execution contract readiness:")
        self.assertIn("- total tasks: 0", lines)
        self.assertIn("- ready tasks: 0", lines)
        self.assertIn("- blocked tasks: 0", lines)
        self.assertIn("- validation failed tasks: 0", lines)
        self.assertIn("- missing context tasks: 0", lines)


if __name__ == "__main__":
    unittest.main()
