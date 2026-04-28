import tempfile
import unittest
from pathlib import Path

from core.task_management import (
    TaskManagementService,
    format_task_plan_materialization_readiness_summary,
    format_task_plan_summary,
)
from core.task_models import TaskPlanMaterializationReason, TaskPlanState
from core.task_status import TaskState
from core.task_store import TaskRecordStore


class TaskPlanServiceTests(unittest.TestCase):
    def test_create_task_plan_defaults_to_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))

            plan = service.create_task_plan(
                "reporting.summary",
                "Prepare profile report",
                analysis_id="analysis-1",
                analysis_profile_id="aprof-1",
                project_id="proj-plan",
                requested_by="tester",
                parameters={"format": "csv"},
                notes="Review before running.",
            )

        self.assertTrue(plan.plan_id.startswith("tplan-"))
        self.assertEqual(plan.state, TaskPlanState.DRAFT)
        self.assertEqual(plan.plan_type, "reporting.summary")
        self.assertEqual(plan.analysis_id, "analysis-1")
        self.assertEqual(plan.analysis_profile_id, "aprof-1")
        self.assertEqual(plan.parameters["format"], "csv")

    def test_list_and_load_task_plans(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(state_dir)
            plan = service.create_task_plan(
                "analysis.run",
                "Plan analysis",
                project_id="proj-plan",
            )
            service.create_task_plan("reporting.export", "Other plan", project_id="other")

            reloaded = TaskManagementService(TaskRecordStore(state_dir))
            project_plans = reloaded.list_task_plans(project_id="proj-plan")
            loaded = reloaded.load_task_plan(plan.plan_id)

        self.assertEqual([item.plan_id for item in project_plans], [plan.plan_id])
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.plan_id, plan.plan_id)
        self.assertEqual(loaded.title, "Plan analysis")

    def test_update_task_plan_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            plan = service.create_task_plan("analysis.run", "Plan analysis")

            ready = service.update_task_plan_state(plan.plan_id, TaskPlanState.READY)
            disabled = service.update_task_plan_state(plan.plan_id, TaskPlanState.DISABLED)
            archived = service.update_task_plan_state(plan.plan_id, TaskPlanState.ARCHIVED)

        self.assertEqual(ready.state, TaskPlanState.READY)
        self.assertEqual(disabled.state, TaskPlanState.DISABLED)
        self.assertEqual(archived.state, TaskPlanState.ARCHIVED)

    def test_task_plan_summary_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            ready = service.create_task_plan("analysis.run", "Ready plan")
            disabled = service.create_task_plan("reporting.export", "Disabled plan")
            archived = service.create_task_plan("reporting.summary", "Archived plan")
            service.create_task_plan("analysis.run", "Draft plan")
            service.update_task_plan_state(ready.plan_id, TaskPlanState.READY)
            service.update_task_plan_state(disabled.plan_id, TaskPlanState.DISABLED)
            service.update_task_plan_state(archived.plan_id, TaskPlanState.ARCHIVED)

            summary = service.summarize_task_plans()

        self.assertEqual(
            summary,
            {
                "total_plans": 4,
                "draft_plans": 1,
                "ready_plans": 1,
                "disabled_plans": 1,
                "archived_plans": 1,
            },
        )

    def test_empty_task_plan_summary_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))

            summary = service.summarize_task_plans()

        self.assertEqual(
            summary,
            {
                "total_plans": 0,
                "draft_plans": 0,
                "ready_plans": 0,
                "disabled_plans": 0,
                "archived_plans": 0,
            },
        )

    def test_task_plan_formatter_handles_empty_summary(self) -> None:
        lines = format_task_plan_summary(None)

        self.assertEqual(lines[0], "Task plan summary:")
        self.assertIn("- total plans: 0", lines)
        self.assertIn("- draft plans: 0", lines)
        self.assertIn("- ready plans: 0", lines)
        self.assertIn("- disabled plans: 0", lines)
        self.assertIn("- archived plans: 0", lines)

    def test_task_plan_formatter_reports_counts(self) -> None:
        lines = format_task_plan_summary(
            {
                "total_plans": 4,
                "draft_plans": 1,
                "ready_plans": 1,
                "disabled_plans": 1,
                "archived_plans": 1,
            }
        )

        self.assertIn("- total plans: 4", lines)
        self.assertIn("- draft plans: 1", lines)
        self.assertIn("- ready plans: 1", lines)
        self.assertIn("- disabled plans: 1", lines)
        self.assertIn("- archived plans: 1", lines)

    def test_task_plan_summary_does_not_change_plan_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            plan = service.create_task_plan("analysis.run", "Ready plan")
            service.update_task_plan_state(plan.plan_id, TaskPlanState.READY)

            service.summarize_task_plans()
            reloaded = service.load_task_plan(plan.plan_id)

        self.assertIsNotNone(reloaded)
        assert reloaded is not None
        self.assertEqual(reloaded.state, TaskPlanState.READY)

    def test_creating_task_plan_does_not_create_tasks_or_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))

            service.create_task_plan("analysis.run", "Plan only")

            self.assertEqual(service.list_tasks(), [])
            self.assertEqual(service.list_results(), [])

    def test_ready_task_plan_materializes_task_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            plan = service.create_task_plan(
                "analysis.run",
                "Run planned analysis",
                analysis_id="analysis-1",
                analysis_profile_id="aprof-1",
                project_id="proj-plan",
                requested_by="tester",
                parameters={"alpha": 0.05},
                notes="Manual conversion only.",
            )
            service.update_task_plan_state(plan.plan_id, TaskPlanState.READY)

            task = service.materialize_task_plan(plan.plan_id)
            reloaded_plan = service.load_task_plan(plan.plan_id)

        self.assertEqual(task.task_type, "analysis.run")
        self.assertEqual(task.title, "Run planned analysis")
        self.assertEqual(task.state, TaskState.PENDING)
        self.assertEqual(task.project_id, "proj-plan")
        self.assertEqual(task.source_id, plan.plan_id)
        self.assertEqual(task.metadata["source_plan_id"], plan.plan_id)
        self.assertEqual(task.metadata["plan_type"], "analysis.run")
        self.assertEqual(task.metadata["analysis_id"], "analysis-1")
        self.assertEqual(task.metadata["analysis_profile_id"], "aprof-1")
        self.assertEqual(task.metadata["project_id"], "proj-plan")
        self.assertEqual(task.metadata["parameters"], {"alpha": 0.05})
        self.assertIsNotNone(reloaded_plan)
        assert reloaded_plan is not None
        self.assertEqual(reloaded_plan.state, TaskPlanState.READY)

    def test_non_ready_task_plans_do_not_materialize(self) -> None:
        for state in (
            TaskPlanState.DRAFT,
            TaskPlanState.DISABLED,
            TaskPlanState.ARCHIVED,
        ):
            with self.subTest(state=state):
                with tempfile.TemporaryDirectory() as temp_dir:
                    service = TaskManagementService.from_state_dir(Path(temp_dir))
                    plan = service.create_task_plan("analysis.run", f"{state.value} plan")
                    if state != TaskPlanState.DRAFT:
                        service.update_task_plan_state(plan.plan_id, state)

                    with self.assertRaisesRegex(ValueError, "must be ready"):
                        service.materialize_task_plan(plan.plan_id)

                    reloaded = service.load_task_plan(plan.plan_id)

                self.assertEqual(service.list_tasks(), [])
                self.assertEqual(service.list_results(), [])
                self.assertIsNotNone(reloaded)
                assert reloaded is not None
                self.assertEqual(reloaded.state, state)

    def test_materializing_task_plan_does_not_create_results_or_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            plan = service.create_task_plan("reporting.summary", "Prepare report")
            service.update_task_plan_state(plan.plan_id, TaskPlanState.READY)

            service.materialize_task_plan(plan.plan_id)

            tasks = service.list_tasks()
            results = service.list_results()
            diagnostics = service.inspect_result_artifacts()

        self.assertEqual(len(tasks), 1)
        self.assertEqual(results, [])
        self.assertEqual(diagnostics, [])

    def test_missing_task_plan_materialization_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))

            with self.assertRaisesRegex(ValueError, "Task plan does not exist"):
                service.materialize_task_plan("missing-plan")

            self.assertEqual(service.list_tasks(), [])
            self.assertEqual(service.list_results(), [])

    def test_task_plan_materialization_readiness_reports_state_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            ready = service.create_task_plan("analysis.run", "Ready plan")
            draft = service.create_task_plan("analysis.run", "Draft plan")
            disabled = service.create_task_plan("analysis.run", "Disabled plan")
            archived = service.create_task_plan("analysis.run", "Archived plan")
            service.update_task_plan_state(ready.plan_id, TaskPlanState.READY)
            service.update_task_plan_state(disabled.plan_id, TaskPlanState.DISABLED)
            service.update_task_plan_state(archived.plan_id, TaskPlanState.ARCHIVED)

            diagnostics = service.inspect_task_plan_materialization_readiness()

        by_plan_id = {item.plan_id: item for item in diagnostics}
        self.assertTrue(by_plan_id[ready.plan_id].can_materialize)
        self.assertEqual(
            by_plan_id[ready.plan_id].reason_code,
            TaskPlanMaterializationReason.READY,
        )
        self.assertFalse(by_plan_id[draft.plan_id].can_materialize)
        self.assertEqual(
            by_plan_id[draft.plan_id].reason_code,
            TaskPlanMaterializationReason.NOT_READY,
        )
        self.assertFalse(by_plan_id[disabled.plan_id].can_materialize)
        self.assertEqual(
            by_plan_id[disabled.plan_id].reason_code,
            TaskPlanMaterializationReason.DISABLED,
        )
        self.assertFalse(by_plan_id[archived.plan_id].can_materialize)
        self.assertEqual(
            by_plan_id[archived.plan_id].reason_code,
            TaskPlanMaterializationReason.ARCHIVED,
        )

    def test_task_plan_materialization_readiness_summary_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            ready = service.create_task_plan("analysis.run", "Ready plan")
            disabled = service.create_task_plan("analysis.run", "Disabled plan")
            archived = service.create_task_plan("analysis.run", "Archived plan")
            service.create_task_plan("analysis.run", "Draft plan")
            service.update_task_plan_state(ready.plan_id, TaskPlanState.READY)
            service.update_task_plan_state(disabled.plan_id, TaskPlanState.DISABLED)
            service.update_task_plan_state(archived.plan_id, TaskPlanState.ARCHIVED)

            summary = service.summarize_task_plan_materialization_readiness()

        self.assertEqual(
            summary,
            {
                "total_plans": 4,
                "materializable_plans": 1,
                "blocked_plans": 3,
                "ready_plans": 1,
                "draft_plans": 1,
                "disabled_plans": 1,
                "archived_plans": 1,
                "missing_context_plans": 0,
            },
        )

    def test_task_plan_materialization_readiness_does_not_create_tasks_or_change_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            plan = service.create_task_plan("analysis.run", "Ready plan")
            service.update_task_plan_state(plan.plan_id, TaskPlanState.READY)

            service.inspect_task_plan_materialization_readiness()
            service.summarize_task_plan_materialization_readiness()
            reloaded = service.load_task_plan(plan.plan_id)

        self.assertEqual(service.list_tasks(), [])
        self.assertEqual(service.list_results(), [])
        self.assertIsNotNone(reloaded)
        assert reloaded is not None
        self.assertEqual(reloaded.state, TaskPlanState.READY)

    def test_task_plan_materialization_readiness_formatter_handles_empty_summary(self) -> None:
        lines = format_task_plan_materialization_readiness_summary(None)

        self.assertEqual(lines[0], "Task plan materialization readiness:")
        self.assertIn("- total plans: 0", lines)
        self.assertIn("- materializable plans: 0", lines)
        self.assertIn("- blocked plans: 0", lines)
        self.assertIn("- ready plans: 0", lines)
        self.assertIn("- draft plans: 0", lines)
        self.assertIn("- disabled plans: 0", lines)
        self.assertIn("- archived plans: 0", lines)
        self.assertIn("- missing context plans: 0", lines)

    def test_task_plan_materialization_readiness_formatter_reports_counts(self) -> None:
        lines = format_task_plan_materialization_readiness_summary(
            {
                "total_plans": 4,
                "materializable_plans": 1,
                "blocked_plans": 3,
                "ready_plans": 1,
                "draft_plans": 1,
                "disabled_plans": 1,
                "archived_plans": 1,
                "missing_context_plans": 0,
            }
        )

        self.assertIn("- total plans: 4", lines)
        self.assertIn("- materializable plans: 1", lines)
        self.assertIn("- blocked plans: 3", lines)
        self.assertIn("- ready plans: 1", lines)
        self.assertIn("- draft plans: 1", lines)
        self.assertIn("- disabled plans: 1", lines)
        self.assertIn("- archived plans: 1", lines)
        self.assertIn("- missing context plans: 0", lines)


if __name__ == "__main__":
    unittest.main()
