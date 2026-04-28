import tempfile
import unittest
from pathlib import Path

from core.task_management import TaskManagementService
from core.task_models import TaskPlanState, TaskResultState
from scripts.run_smoke_tests import build_smoke_summary, main


class RepoSmokeTests(unittest.TestCase):
    def test_smoke_summary_surfaces_rule_bundle_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Rule bundle diagnostics:", lines)
            self.assertIn("- total bundles: 0", lines)
            self.assertIn("- missing files: 1", lines)

    def test_smoke_summary_surfaces_empty_artifact_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Task result artifact diagnostics:", lines)
            self.assertIn("- total results: 0", lines)
            self.assertIn("- present artifacts: 0", lines)
            self.assertIn("- missing artifacts: 0", lines)
            self.assertIn("- not applicable artifacts: 0", lines)

    def test_smoke_summary_surfaces_empty_task_plan_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Task plan summary:", lines)
            self.assertIn("- total plans: 0", lines)
            self.assertIn("- draft plans: 0", lines)
            self.assertIn("- ready plans: 0", lines)
            self.assertIn("- disabled plans: 0", lines)
            self.assertIn("- archived plans: 0", lines)

    def test_smoke_summary_surfaces_empty_task_plan_materialization_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Task plan materialization readiness:", lines)
            self.assertIn("- total plans: 0", lines)
            self.assertIn("- materializable plans: 0", lines)
            self.assertIn("- blocked plans: 0", lines)
            self.assertIn("- missing context plans: 0", lines)

    def test_smoke_summary_surfaces_empty_task_execution_contract_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Task execution contract readiness:", lines)
            self.assertIn("- total tasks: 0", lines)
            self.assertIn("- ready tasks: 0", lines)
            self.assertIn("- blocked tasks: 0", lines)
            self.assertIn("- validation failed tasks: 0", lines)
            self.assertIn("- missing context tasks: 0", lines)

    def test_smoke_summary_surfaces_empty_mock_runner_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Mock task runner diagnostics:", lines)
            self.assertIn("- total checks: 0", lines)
            self.assertIn("- accepted dry run outcomes: 0", lines)
            self.assertIn("- rejected outcomes: 0", lines)
            self.assertIn("- validation failed outcomes: 0", lines)

    def test_smoke_summary_surfaces_empty_manual_runner_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Manual runner wrapper:", lines)
            self.assertIn("- dry run checks: 0", lines)
            self.assertIn("- accepted outcomes: 0", lines)
            self.assertIn("- rejected outcomes: 0", lines)
            self.assertIn("- missing adapter outcomes: 0", lines)

    def test_smoke_summary_surfaces_empty_lifecycle_runner_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Lifecycle runner wrapper:", lines)
            self.assertIn("- dry run checks: 0", lines)
            self.assertIn("- accepted outcomes: 0", lines)
            self.assertIn("- rejected outcomes: 0", lines)
            self.assertIn("- state mutations: 0", lines)

    def test_smoke_summary_surfaces_lifecycle_guard_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Lifecycle guard diagnostics:", lines)
            self.assertIn("- pending allowed: yes", lines)
            self.assertIn("- running blocked: yes", lines)
            self.assertIn("- completed blocked: yes", lines)
            self.assertIn("- failed blocked: yes", lines)
            self.assertIn("- dry run mutations: 0", lines)

    def test_smoke_summary_surfaces_empty_real_run_preflight_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Real-run preflight diagnostics:", lines)
            self.assertIn("- checked tasks: 0", lines)
            self.assertIn("- eligible tasks: 0", lines)
            self.assertIn("- blocked tasks: 0", lines)
            self.assertIn("- adapter missing: 0", lines)
            self.assertIn("- state mutations: 0", lines)

    def test_smoke_summary_surfaces_empty_profile_reporting_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Profile reporting summary results:", lines)
            self.assertIn("- total results: 0", lines)
            self.assertIn("- present artifacts: 0", lines)
            self.assertIn("- missing artifacts: 0", lines)
            self.assertIn("- not applicable artifacts: 0", lines)

    def test_smoke_summary_surfaces_analysis_preflight_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")

            lines = build_smoke_summary(root_dir)

        self.assertIn("Analysis preflight readiness summary:", lines)
        self.assertIn("- total checks: 2", lines)
        self.assertIn("- runnable checks: 1", lines)
        self.assertIn("- blocked checks: 1", lines)
        self.assertIn("- warning count: 2", lines)
        self.assertIn("- blocking error count: 1", lines)
        self.assertEqual(service.list_results(), [])
        self.assertEqual(service.list_task_execution_logs(), [])

    def test_smoke_summary_surfaces_empty_execution_log_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Execution log summary:", lines)
            self.assertIn("- total logs: 0", lines)
            self.assertIn("- dry run logs: 0", lines)
            self.assertIn("- real run logs: 0", lines)
            self.assertIn("- success accepted logs: 0", lines)
            self.assertIn("- failed rejected logs: 0", lines)
            self.assertIn("- logs with result id: 0", lines)

    def test_smoke_summary_surfaces_empty_retry_task_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Retry task summary:", lines)
            self.assertIn("- total retry tasks: 0", lines)
            self.assertIn("- retry tasks pending: 0", lines)
            self.assertIn("- retry tasks completed: 0", lines)
            self.assertIn("- retry tasks failed: 0", lines)

    def test_smoke_summary_reports_retry_tasks_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")
            failed = service.create_task("profile_reporting_summary", "Failed task")
            service.fail_task(failed.task_id, "failed")
            retry = service.create_retry_task(failed.task_id)

            lines = build_smoke_summary(root_dir)
            reloaded_retry = next(
                task for task in service.list_tasks() if task.task_id == retry.task_id
            )

        self.assertIn("Retry task summary:", lines)
        self.assertIn("- total retry tasks: 1", lines)
        self.assertIn("- retry tasks pending: 1", lines)
        self.assertIn("- retry tasks completed: 0", lines)
        self.assertIn("- retry tasks failed: 0", lines)
        self.assertEqual(reloaded_retry.state.value, "pending")
        self.assertEqual(service.list_task_execution_logs(), [])

    def test_smoke_summary_surfaces_empty_runner_adapter_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Runner adapter registry:", lines)
            self.assertIn("- total adapters: 0", lines)
            self.assertIn("- adapter types: none", lines)
            self.assertIn("- supported task types: none", lines)
            self.assertIn("- no-op adapters: 0", lines)

    def test_smoke_summary_surfaces_empty_reporting_runner_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_smoke_summary(Path(temp_dir))

            self.assertIn("Reporting runner dry-run:", lines)
            self.assertIn("- supported task types: profile_reporting_summary", lines)
            self.assertIn("- dry-run accepted: 0", lines)
            self.assertIn("- rejected: 0", lines)
            self.assertIn("- not implemented: 0", lines)

    def test_smoke_summary_reports_ready_plan_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")
            plan = service.create_task_plan("analysis.run", "Ready plan")
            service.update_task_plan_state(plan.plan_id, TaskPlanState.READY)

            lines = build_smoke_summary(root_dir)
            reloaded = service.load_task_plan(plan.plan_id)

        self.assertIn("- total plans: 1", lines)
        self.assertIn("- ready plans: 1", lines)
        self.assertIn("- materializable plans: 1", lines)
        self.assertIn("- blocked plans: 0", lines)
        self.assertEqual(reloaded.state, TaskPlanState.READY)
        self.assertEqual(service.list_tasks(), [])
        self.assertEqual(service.list_results(), [])

    def test_smoke_summary_reports_ready_task_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")
            task = service.create_task("analysis.run", "Ready contract")

            lines = build_smoke_summary(root_dir)
            reloaded = service.list_tasks()[0]

        self.assertIn("- total tasks: 1", lines)
        self.assertIn("- ready tasks: 1", lines)
        self.assertIn("- blocked tasks: 0", lines)
        self.assertIn("- total checks: 1", lines)
        self.assertIn("- accepted dry run outcomes: 1", lines)
        self.assertIn("- rejected outcomes: 0", lines)
        self.assertIn("Manual runner wrapper:", lines)
        self.assertIn("- dry run checks: 1", lines)
        self.assertIn("- accepted outcomes: 0", lines)
        self.assertIn("- rejected outcomes: 1", lines)
        self.assertIn("- missing adapter outcomes: 1", lines)
        self.assertIn("Lifecycle runner wrapper:", lines)
        self.assertIn("- state mutations: 0", lines)
        self.assertIn("Runner adapter registry:", lines)
        self.assertEqual(reloaded.task_id, task.task_id)
        self.assertEqual(reloaded.state.value, "pending")
        self.assertEqual(service.list_results(), [])

    def test_smoke_summary_reports_reporting_dry_run_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")
            task = service.create_task(
                "profile_reporting_summary",
                "Reporting summary dry-run",
                metadata={"analysis_id": "analysis-1"},
            )

            lines = build_smoke_summary(root_dir)
            reloaded = service.list_tasks()[0]

        self.assertIn("Reporting runner dry-run:", lines)
        self.assertIn("- dry-run accepted: 1", lines)
        self.assertIn("- rejected: 0", lines)
        self.assertIn("- not implemented: 0", lines)
        self.assertIn("Manual runner wrapper:", lines)
        self.assertIn("- dry run checks: 1", lines)
        self.assertIn("- missing adapter outcomes: 1", lines)
        self.assertIn("Lifecycle runner wrapper:", lines)
        self.assertIn("- dry run checks: 1", lines)
        self.assertIn("- rejected outcomes: 1", lines)
        self.assertIn("- state mutations: 0", lines)
        self.assertIn("Real-run preflight diagnostics:", lines)
        self.assertIn("- checked tasks: 1", lines)
        self.assertIn("- eligible tasks: 0", lines)
        self.assertIn("- blocked tasks: 1", lines)
        self.assertIn("- adapter missing: 1", lines)
        self.assertEqual(reloaded.task_id, task.task_id)
        self.assertEqual(reloaded.state.value, "pending")
        self.assertEqual(service.list_results(), [])
        self.assertEqual(service.list_task_execution_logs(), [])

    def test_smoke_summary_reports_missing_artifact_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")
            task = service.create_task("reporting.summary", "Missing artifact")
            result = service.record_result(
                task.task_id,
                "profile_reporting_summary",
                state=TaskResultState.FAILED,
                artifact_path=str(root_dir / "missing.csv"),
            )

            lines = build_smoke_summary(root_dir)
            reloaded = service.list_results(task_id=task.task_id)[0]

        self.assertIn("- total results: 1", lines)
        self.assertIn("- missing artifacts: 1", lines)
        self.assertEqual(reloaded.result_id, result.result_id)
        self.assertEqual(reloaded.state, TaskResultState.FAILED)

    def test_smoke_summary_reports_profile_reporting_result_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")
            task = service.create_task(
                "profile_reporting_summary",
                "Profile reporting summary",
            )
            present_artifact = root_dir / "summary.csv"
            present_artifact.write_text("analysis_id\nanalysis-1\n", encoding="utf-8")
            service.record_result(
                task.task_id,
                "profile_reporting_summary",
                artifact_path=str(present_artifact),
            )
            service.record_result(
                task.task_id,
                "profile_reporting_summary",
                artifact_path=str(root_dir / "missing.csv"),
            )

            lines = build_smoke_summary(root_dir)
            reloaded = service.list_tasks()[0]

        self.assertIn("Profile reporting summary results:", lines)
        self.assertIn("- total results: 2", lines)
        self.assertIn("- present artifacts: 1", lines)
        self.assertIn("- missing artifacts: 1", lines)
        self.assertEqual(reloaded.state.value, "pending")

    def test_smoke_summary_reports_execution_logs_without_creating_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")
            task = service.create_task("profile_reporting_summary", "Logged task")
            service.append_task_execution_log(
                task.task_id,
                task_type=task.task_type,
                dry_run=False,
                outcome_status="accepted",
                result_id="tres-1",
            )

            lines = build_smoke_summary(root_dir)
            logs = service.list_task_execution_logs()
            reloaded = service.list_tasks()[0]

        self.assertIn("Execution log summary:", lines)
        self.assertIn("- total logs: 1", lines)
        self.assertIn("- real run logs: 1", lines)
        self.assertIn("- success accepted logs: 1", lines)
        self.assertIn("- logs with result id: 1", lines)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].result_id, "tres-1")
        self.assertEqual(reloaded.state.value, "pending")
        self.assertEqual(service.list_results(), [])

    def test_smoke_lifecycle_guard_diagnostics_do_not_create_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")

            lines = build_smoke_summary(root_dir)

        self.assertIn("Lifecycle guard diagnostics:", lines)
        self.assertEqual(service.list_tasks(), [])
        self.assertEqual(service.list_results(), [])
        self.assertEqual(service.list_task_execution_logs(), [])

    def test_smoke_main_does_not_fail_on_missing_rule_bundle(self) -> None:
        self.assertEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()
