import tempfile
import unittest
from pathlib import Path

from analysis.models import AnalysisMetric, AnalysisModelType
from analysis.service import AnalysisService
from analysis_profiles.models import KeywordMatchMode
from analysis_profiles.service import AnalysisProfileService
from core.task_management import (
    TaskManagementService,
    format_profile_reporting_result_summary,
    format_retry_task_summary,
    format_task_result_artifact_diagnostics_summary,
)
from core.task_models import TaskResultArtifactStatus, TaskResultState
from core.task_status import TaskState
from core.task_store import TaskRecordStore
from extraction.models import ExtractionRecord, OutcomeRecord, OutcomeType
from extraction.store import ExtractionStore
from reporting.service import ReportingService


class TaskManagementServiceTests(unittest.TestCase):
    def test_create_start_complete_task_with_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            task = service.create_task(
                "analysis.reporting",
                "Generate profile report",
                project_id="proj-task",
                source_id="analysis-1",
                metadata={"profile_id": "aprof-1"},
            )

            running = service.start_task(task.task_id, "running report")
            completed = service.complete_task(
                task.task_id,
                message="report ready",
                result_type="reporting_summary",
                title="Profile report",
                artifact_path="output/proj-task/reporting/summary.csv",
                summary="Report summary generated.",
            )
            results = service.list_results(task_id=task.task_id)

        self.assertEqual(task.state, TaskState.PENDING)
        self.assertEqual(running.state, TaskState.RUNNING)
        self.assertEqual(completed.state, TaskState.COMPLETED)
        self.assertEqual(completed.message, "report ready")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].result_type, "reporting_summary")
        self.assertEqual(results[0].state, TaskResultState.AVAILABLE)

    def test_failure_records_failed_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            task = service.create_task("analysis.run", "Run analysis")

            failed = service.fail_task(
                task.task_id,
                "analysis failed",
                summary="No eligible outcomes.",
            )
            results = service.list_results(task_id=task.task_id)

        self.assertEqual(failed.state, TaskState.FAILED)
        self.assertEqual(results[0].state, TaskResultState.FAILED)
        self.assertEqual(results[0].summary, "No eligible outcomes.")

    def test_records_persist_and_can_be_filtered(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(state_dir)
            project_task = service.create_task(
                "analysis.run",
                "Run profile analysis",
                project_id="proj-a",
            )
            service.create_task("reporting.export", "Export report", project_id="proj-b")
            service.complete_task(project_task.task_id, result_type="meta_result")

            reloaded = TaskManagementService(TaskRecordStore(state_dir))
            project_tasks = reloaded.list_tasks(project_id="proj-a")
            completed_tasks = reloaded.list_tasks(state=TaskState.COMPLETED)
            meta_results = reloaded.list_results(result_type="meta_result")

        self.assertEqual([item.task_id for item in project_tasks], [project_task.task_id])
        self.assertEqual([item.task_id for item in completed_tasks], [project_task.task_id])
        self.assertEqual([item.task_id for item in meta_results], [project_task.task_id])

    def test_unknown_task_cannot_record_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))

            with self.assertRaisesRegex(ValueError, "Task does not exist"):
                service.record_result("missing-task", "report")

    def test_register_profile_reporting_result_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            analysis_id, profile_id = self._seed_profile_analysis(root_dir)
            reporting_service = ReportingService.from_root_dir(root_dir)
            table = reporting_service.generate_analysis_summary_table(analysis_id)
            artifact = reporting_service.export_analysis_summary_csv(analysis_id)
            row = table.rows[0]
            task_service = TaskManagementService.from_state_dir(root_dir / "state")
            task = task_service.create_task(
                "reporting.summary",
                "Register profile report",
                project_id=table.project_id,
                source_id=analysis_id,
            )

            result = task_service.register_profile_reporting_result(
                task.task_id,
                analysis_id=analysis_id,
                project_id=table.project_id,
                analysis_profile_id=row.analysis_profile_id,
                analysis_profile_name=row.analysis_profile_name,
                artifact_path=str(artifact.path),
                summary="Profile report registered.",
            )

        self.assertEqual(result.result_type, "profile_reporting_summary")
        self.assertEqual(result.artifact_path, str(artifact.path))
        self.assertEqual(result.metadata["analysis_id"], analysis_id)
        self.assertEqual(result.metadata["project_id"], "proj-task-report")
        self.assertEqual(result.metadata["analysis_profile_id"], profile_id)
        self.assertEqual(result.metadata["analysis_profile_name"], "Task reporting profile")

    def test_register_analysis_preflight_result_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            task = service.create_task("analysis.preflight", "Register preflight")

            result = service.register_analysis_preflight_result(
                task.task_id,
                dataset_id="GSE-preflight",
                profile_id="profile-a",
                runnable=True,
                blocking_error_count=0,
                warning_count=2,
                recommended_action="review_warnings_before_analysis",
                summary="Preflight has warnings.",
            )
            reloaded_task = service.list_tasks()[0]

        self.assertEqual(result.result_type, "analysis_preflight_summary")
        self.assertEqual(result.metadata["dataset_id"], "GSE-preflight")
        self.assertEqual(result.metadata["profile_id"], "profile-a")
        self.assertTrue(result.metadata["runnable"])
        self.assertEqual(result.metadata["blocking_error_count"], 0)
        self.assertEqual(result.metadata["warning_count"], 2)
        self.assertEqual(
            result.metadata["recommended_action"],
            "review_warnings_before_analysis",
        )
        self.assertEqual(reloaded_task.state, TaskState.PENDING)

    def test_register_non_runnable_analysis_preflight_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            task = service.create_task("analysis.preflight", "Register failed preflight")

            result = service.register_analysis_preflight_result(
                task.task_id,
                dataset_id="GSE-blocked",
                profile_id="profile-a",
                runnable=False,
                blocking_error_count=1,
                warning_count=0,
                recommended_action="provide_expression_matrix",
            )

        self.assertEqual(result.result_type, "analysis_preflight_summary")
        self.assertFalse(result.metadata["runnable"])
        self.assertEqual(result.metadata["blocking_error_count"], 1)

    def test_analysis_preflight_result_without_artifact_is_not_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            task = service.create_task("analysis.preflight", "Register preflight")
            result = service.register_analysis_preflight_result(
                task.task_id,
                dataset_id="GSE-no-artifact",
                profile_id="profile-a",
                runnable=True,
                blocking_error_count=0,
                warning_count=0,
            )

            diagnostics = service.inspect_result_artifacts(result_type=result.result_type)

        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(
            diagnostics[0].artifact_status,
            TaskResultArtifactStatus.NOT_APPLICABLE,
        )

    def test_inspect_result_artifacts_reports_present_missing_and_not_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            existing_artifact = root_dir / "summary.csv"
            existing_artifact.write_text("analysis_id\nanalysis-1\n", encoding="utf-8")
            missing_artifact = root_dir / "missing.csv"
            service = TaskManagementService.from_state_dir(root_dir / "state")
            task = service.create_task("reporting.summary", "Inspect artifacts")
            present = service.record_result(
                task.task_id,
                "profile_reporting_summary",
                artifact_path=str(existing_artifact),
            )
            missing = service.record_result(
                task.task_id,
                "profile_reporting_summary",
                artifact_path=str(missing_artifact),
            )
            no_artifact = service.record_result(task.task_id, "note")

            diagnostics = service.inspect_result_artifacts(task_id=task.task_id)
            summary = service.summarize_task_result_artifacts(diagnostics)

        by_result_id = {item.result_id: item for item in diagnostics}
        self.assertEqual(
            by_result_id[present.result_id].artifact_status,
            TaskResultArtifactStatus.PRESENT,
        )
        self.assertEqual(
            by_result_id[missing.result_id].artifact_status,
            TaskResultArtifactStatus.MISSING,
        )
        self.assertEqual(
            by_result_id[no_artifact.result_id].artifact_status,
            TaskResultArtifactStatus.NOT_APPLICABLE,
        )
        self.assertEqual(
            summary,
            {
                "total_results": 3,
                "present_artifacts": 1,
                "missing_artifacts": 1,
                "not_applicable_artifacts": 1,
            },
        )

    def test_artifact_diagnostics_do_not_change_result_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root_dir / "state")
            task = service.create_task("analysis.run", "Run analysis")
            failed = service.record_result(
                task.task_id,
                "error",
                state=TaskResultState.FAILED,
                artifact_path=str(root_dir / "missing-error.txt"),
            )

            diagnostics = service.inspect_result_artifacts(task_id=task.task_id)
            reloaded = service.list_results(task_id=task.task_id)[0]

        self.assertEqual(diagnostics[0].artifact_status, TaskResultArtifactStatus.MISSING)
        self.assertEqual(diagnostics[0].state, TaskResultState.FAILED)
        self.assertEqual(reloaded.result_id, failed.result_id)
        self.assertEqual(reloaded.state, TaskResultState.FAILED)

    def test_artifact_diagnostics_formatter_handles_empty_summary(self) -> None:
        lines = format_task_result_artifact_diagnostics_summary(None)

        self.assertEqual(lines[0], "Task result artifact diagnostics:")
        self.assertIn("- total results: 0", lines)
        self.assertIn("- present artifacts: 0", lines)
        self.assertIn("- missing artifacts: 0", lines)
        self.assertIn("- not applicable artifacts: 0", lines)

    def test_artifact_diagnostics_formatter_reports_counts(self) -> None:
        lines = format_task_result_artifact_diagnostics_summary(
            {
                "total_results": 3,
                "present_artifacts": 1,
                "missing_artifacts": 1,
                "not_applicable_artifacts": 1,
            }
        )

        self.assertIn("- total results: 3", lines)
        self.assertIn("- present artifacts: 1", lines)
        self.assertIn("- missing artifacts: 1", lines)
        self.assertIn("- not applicable artifacts: 1", lines)

    def test_profile_reporting_result_summary_counts_only_profile_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            existing_artifact = root_dir / "profile-summary.csv"
            existing_artifact.write_text("analysis_id\nanalysis-1\n", encoding="utf-8")
            service = TaskManagementService.from_state_dir(root_dir / "state")
            task = service.create_task(
                "profile_reporting_summary",
                "Profile reporting summary",
            )
            service.record_result(
                task.task_id,
                "profile_reporting_summary",
                artifact_path=str(existing_artifact),
            )
            service.record_result(
                task.task_id,
                "profile_reporting_summary",
                artifact_path=str(root_dir / "missing-profile-summary.csv"),
            )
            service.record_result(task.task_id, "profile_reporting_summary")
            service.record_result(
                task.task_id,
                "other_result",
                artifact_path=str(root_dir / "missing-other.csv"),
            )

            summary = service.summarize_profile_reporting_results()

        self.assertEqual(
            summary,
            {
                "total_results": 3,
                "present_artifacts": 1,
                "missing_artifacts": 1,
                "not_applicable_artifacts": 1,
            },
        )

    def test_create_retry_task_from_failed_task_copies_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            original = service.create_task(
                "profile_reporting_summary",
                "Profile summary",
                project_id="proj-retry",
                source_id="analysis-retry",
                metadata={
                    "analysis_id": "analysis-retry",
                    "analysis_profile_id": "aprof-retry",
                    "project_id": "proj-retry",
                    "parameters": {"summary_format": "csv"},
                    "source_plan_id": "plan-retry",
                },
            )
            failed = service.fail_task(original.task_id, "export failed")
            result_count_before = len(service.list_results())

            retry = service.create_retry_task(failed.task_id)
            reloaded_original = next(
                task for task in service.list_tasks() if task.task_id == original.task_id
            )
            result_count_after = len(service.list_results())

            self.assertEqual(retry.state, TaskState.PENDING)
            self.assertEqual(retry.task_type, "profile_reporting_summary")
            self.assertEqual(retry.project_id, "proj-retry")
            self.assertEqual(retry.source_id, "analysis-retry")
            self.assertEqual(retry.metadata["retry_of_task_id"], original.task_id)
            self.assertEqual(retry.metadata["original_task_id"], original.task_id)
            self.assertEqual(retry.metadata["original_task_state"], "failed")
            self.assertEqual(retry.metadata["analysis_id"], "analysis-retry")
            self.assertEqual(retry.metadata["analysis_profile_id"], "aprof-retry")
            self.assertEqual(retry.metadata["parameters"], {"summary_format": "csv"})
            self.assertEqual(reloaded_original.state, TaskState.FAILED)
            self.assertEqual(result_count_after, result_count_before)

    def test_create_retry_task_requires_failed_original(self) -> None:
        blocked_states = (
            TaskState.PENDING,
            TaskState.RUNNING,
            TaskState.COMPLETED,
        )
        for state in blocked_states:
            with self.subTest(state=state):
                with tempfile.TemporaryDirectory() as temp_dir:
                    service = TaskManagementService.from_state_dir(Path(temp_dir))
                    task = service.create_task(
                        "profile_reporting_summary",
                        f"{state.value} task",
                    )
                    if state == TaskState.RUNNING:
                        service.start_task(task.task_id)
                    elif state == TaskState.COMPLETED:
                        service.complete_task(task.task_id)

                    with self.assertRaisesRegex(ValueError, "failed task"):
                        service.create_retry_task(task.task_id)
                    self.assertEqual(len(service.list_tasks()), 1)
                    self.assertEqual(len(service.list_results()), 0)

    def test_create_retry_task_does_not_execute_or_create_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            task = service.create_task("profile_reporting_summary", "Failed summary")
            service.fail_task(task.task_id, "failed")
            before_logs = service.list_task_execution_logs()

            retry = service.create_retry_task(task.task_id)
            after_logs = service.list_task_execution_logs()
            results = service.list_results()

            self.assertEqual(retry.state, TaskState.PENDING)
            self.assertEqual(after_logs, before_logs)
            self.assertTrue(all(not result.artifact_path for result in results))

    def test_retry_task_summary_counts_retry_states(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))
            first = service.create_task("profile_reporting_summary", "First")
            second = service.create_task("profile_reporting_summary", "Second")
            third = service.create_task("profile_reporting_summary", "Third")
            service.fail_task(first.task_id, "first failed")
            service.fail_task(second.task_id, "second failed")
            service.fail_task(third.task_id, "third failed")
            pending_retry = service.create_retry_task(first.task_id)
            completed_retry = service.create_retry_task(second.task_id)
            failed_retry = service.create_retry_task(third.task_id)
            service.complete_task(completed_retry.task_id)
            service.fail_task(failed_retry.task_id, "retry failed")
            service.create_task("profile_reporting_summary", "Ordinary task")

            summary = service.summarize_retry_tasks()

        self.assertEqual(
            summary,
            {
                "total_retry_tasks": 3,
                "retry_tasks_pending": 1,
                "retry_tasks_completed": 1,
                "retry_tasks_failed": 1,
            },
        )
        self.assertEqual(pending_retry.state, TaskState.PENDING)

    def test_retry_task_summary_empty_and_formatter_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir))

            summary = service.summarize_retry_tasks()
            lines = format_retry_task_summary(summary)

        self.assertEqual(
            summary,
            {
                "total_retry_tasks": 0,
                "retry_tasks_pending": 0,
                "retry_tasks_completed": 0,
                "retry_tasks_failed": 0,
            },
        )
        self.assertIn("Retry task summary:", lines)
        self.assertIn("- total retry tasks: 0", lines)
        self.assertIn("- retry tasks pending: 0", lines)
        self.assertIn("- retry tasks completed: 0", lines)
        self.assertIn("- retry tasks failed: 0", lines)

    def test_profile_reporting_result_formatter_handles_empty_summary(self) -> None:
        lines = format_profile_reporting_result_summary(None)

        self.assertEqual(lines[0], "Profile reporting summary results:")
        self.assertIn("- total results: 0", lines)
        self.assertIn("- present artifacts: 0", lines)
        self.assertIn("- missing artifacts: 0", lines)
        self.assertIn("- not applicable artifacts: 0", lines)

    def _seed_profile_analysis(self, root_dir: Path) -> tuple[str, str]:
        outcome_ids = self._seed_reporting_outcomes(root_dir)
        profile_service = AnalysisProfileService.from_root_dir(root_dir)
        gene_panel = profile_service.create_gene_panel(
            "proj-task-report",
            "Task reporting panel",
            ["EGFR", "ALK"],
        )
        comparison = profile_service.create_comparison_rule(
            "proj-task-report",
            "Treatment versus control",
            "Treatment",
            "Control",
        )
        keyword_set = profile_service.create_keyword_rule_set(
            "proj-task-report",
            "Task reporting keywords",
            ["metastatic", "advanced"],
            match_mode=KeywordMatchMode.ANY,
        )
        thresholds = profile_service.create_threshold_profile(
            "proj-task-report",
            "Task reporting thresholds",
            min_study_count=2,
            max_i2=75.0,
            alpha=0.05,
        )
        profile = profile_service.create_analysis_profile(
            "proj-task-report",
            "Task reporting profile",
            outcome_type=OutcomeType.BINARY,
            metric=AnalysisMetric.OR,
            model_type=AnalysisModelType.FIXED_EFFECT,
            comparison_rule_id=comparison.comparison_rule_id,
            threshold_profile_id=thresholds.threshold_profile_id,
            gene_panel_id=gene_panel.gene_panel_id,
            keyword_rule_set_id=keyword_set.keyword_rule_set_id,
        )
        config = profile_service.export_engine_config(profile.analysis_profile_id)
        analysis_service = AnalysisService.from_root_dir(root_dir)
        analysis = analysis_service.create_analysis_from_profile_config(config, outcome_ids)
        analysis_service.run_analysis(analysis.analysis_id)
        return analysis.analysis_id, profile.analysis_profile_id

    def _seed_reporting_outcomes(self, root_dir: Path) -> list[str]:
        extraction_store = ExtractionStore(root_dir)
        outcomes = []
        for index, events in enumerate((12, 18), start=1):
            extraction_id = f"extr-task-report-{index}"
            extraction_store.save_extraction_record(
                ExtractionRecord(
                    extraction_record_id=extraction_id,
                    project_id="proj-task-report",
                    screening_record_id=f"screen-task-report-{index}",
                    normalized_record_id=f"norm-task-report-{index}",
                    study_title=f"Task report study {index}",
                )
            )
            outcome_id = f"out-task-report-{index}"
            extraction_store.save_outcome_record(
                OutcomeRecord(
                    outcome_record_id=outcome_id,
                    extraction_record_id=extraction_id,
                    outcome_name="Response",
                    outcome_type=OutcomeType.BINARY,
                    group_a_n=100,
                    group_b_n=100,
                    events_a=events,
                    events_b=25,
                )
            )
            outcomes.append(outcome_id)
        return outcomes


if __name__ == "__main__":
    unittest.main()
