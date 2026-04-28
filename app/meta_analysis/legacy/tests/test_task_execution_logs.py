import tempfile
import unittest
from pathlib import Path

from core.task_management import (
    TaskManagementService,
    format_task_execution_log_summary,
)
from core.task_runner_adapters import REPORTING_SUMMARY_TASK_TYPE


class TaskExecutionLogTests(unittest.TestCase):
    def test_empty_store_lists_no_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))

            logs = service.list_task_execution_logs()

        self.assertEqual(logs, [])

    def test_append_log_records_execution_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            task = service.create_task(
                REPORTING_SUMMARY_TASK_TYPE,
                "Profile reporting summary",
                metadata={"source_plan_id": "plan-1"},
            )

            log = service.append_task_execution_log(
                task.task_id,
                source_plan_id="plan-1",
                runner_type="reporting_summary_runner",
                task_type=REPORTING_SUMMARY_TASK_TYPE,
                dry_run=True,
                outcome_status="skipped",
                message="Dry-run accepted.",
                metadata={"operator": "tester"},
            )
            logs = service.list_task_execution_logs()

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].log_id, log.log_id)
        self.assertEqual(logs[0].task_id, task.task_id)
        self.assertEqual(logs[0].source_plan_id, "plan-1")
        self.assertEqual(logs[0].runner_type, "reporting_summary_runner")
        self.assertEqual(logs[0].task_type, REPORTING_SUMMARY_TASK_TYPE)
        self.assertTrue(logs[0].dry_run)
        self.assertEqual(logs[0].outcome_status, "skipped")
        self.assertEqual(logs[0].message, "Dry-run accepted.")
        self.assertEqual(logs[0].metadata["operator"], "tester")

    def test_list_logs_can_filter_by_task_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            first = service.create_task("profile_reporting_summary", "First")
            second = service.create_task("profile_reporting_summary", "Second")
            first_log = service.append_task_execution_log(
                first.task_id,
                task_type=first.task_type,
                outcome_status="skipped",
            )
            service.append_task_execution_log(
                second.task_id,
                task_type=second.task_type,
                outcome_status="rejected",
            )

            logs = service.list_task_execution_logs_for_task(first.task_id)

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].log_id, first_log.log_id)
        self.assertEqual(logs[0].task_id, first.task_id)

    def test_logs_persist_in_json_store(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(state_dir)
            task = service.create_task("profile_reporting_summary", "Persisted")
            service.append_task_execution_log(
                task.task_id,
                task_type=task.task_type,
                dry_run=False,
                outcome_status="accepted",
                result_id="tres-1",
            )

            reloaded = TaskManagementService.from_state_dir(state_dir)
            logs = reloaded.list_task_execution_logs()

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].task_id, task.task_id)
        self.assertFalse(logs[0].dry_run)
        self.assertEqual(logs[0].outcome_status, "accepted")
        self.assertEqual(logs[0].result_id, "tres-1")

    def test_append_log_does_not_change_task_state_or_create_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root / "state")
            task = service.create_task("profile_reporting_summary", "No side effects")

            service.append_task_execution_log(
                task.task_id,
                task_type=task.task_type,
                dry_run=True,
                outcome_status="skipped",
                error_code="",
                result_id=None,
            )
            reloaded = service.list_tasks()[0]
            results = service.list_results()

        self.assertEqual(reloaded.state.value, "pending")
        self.assertEqual(results, [])
        self.assertFalse((root / "output").exists())

    def test_empty_execution_log_summary_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))

            summary = service.summarize_task_execution_logs()
            lines = format_task_execution_log_summary(summary)

        self.assertEqual(
            summary,
            {
                "total_logs": 0,
                "dry_run_logs": 0,
                "real_run_logs": 0,
                "success_accepted_logs": 0,
                "failed_rejected_logs": 0,
                "logs_with_result_id": 0,
            },
        )
        self.assertIn("Execution log summary:", lines)
        self.assertIn("- total logs: 0", lines)
        self.assertIn("- dry run logs: 0", lines)
        self.assertIn("- real run logs: 0", lines)
        self.assertIn("- success accepted logs: 0", lines)
        self.assertIn("- failed rejected logs: 0", lines)
        self.assertIn("- logs with result id: 0", lines)

    def test_execution_log_summary_counts_outcomes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            task = service.create_task("profile_reporting_summary", "Summarized")
            service.append_task_execution_log(
                task.task_id,
                task_type=task.task_type,
                dry_run=True,
                outcome_status="skipped",
            )
            service.append_task_execution_log(
                task.task_id,
                task_type=task.task_type,
                dry_run=False,
                outcome_status="accepted",
                result_id="tres-1",
            )
            service.append_task_execution_log(
                task.task_id,
                task_type=task.task_type,
                dry_run=False,
                outcome_status="rejected",
                error_code="adapter_missing",
            )

            summary = service.summarize_task_execution_logs()

        self.assertEqual(summary["total_logs"], 3)
        self.assertEqual(summary["dry_run_logs"], 1)
        self.assertEqual(summary["real_run_logs"], 2)
        self.assertEqual(summary["success_accepted_logs"], 2)
        self.assertEqual(summary["failed_rejected_logs"], 1)
        self.assertEqual(summary["logs_with_result_id"], 1)


if __name__ == "__main__":
    unittest.main()
