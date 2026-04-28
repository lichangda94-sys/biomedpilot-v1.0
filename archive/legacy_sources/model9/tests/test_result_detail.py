import tempfile
import unittest
from pathlib import Path

from core.task_management import TaskManagementService
from core.task_models import TaskResultArtifactStatus, TaskResultState


class ResultDetailServiceTests(unittest.TestCase):
    def test_existing_result_detail_includes_metadata_and_artifact_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = root / "summary.csv"
            artifact.write_text("analysis_id,value\nanalysis-1,42\n", encoding="utf-8")
            service = TaskManagementService.from_state_dir(root / "state")
            task = service.create_task("profile_reporting_summary", "Report")
            result = service.record_result(
                task.task_id,
                "profile_reporting_summary",
                title="Profile reporting summary",
                artifact_path=str(artifact),
                summary="Summary ready.",
                metadata={
                    "source_task_id": task.task_id,
                    "analysis_id": "analysis-1",
                    "analysis_profile_id": "profile-1",
                    "project_id": "project-1",
                    "custom": {"nested": True},
                },
            )

            detail = service.get_task_result_detail(result.result_id)

        self.assertEqual(detail.result_id, result.result_id)
        self.assertEqual(detail.result_type, "profile_reporting_summary")
        self.assertEqual(detail.state, TaskResultState.AVAILABLE)
        self.assertEqual(detail.title, "Profile reporting summary")
        self.assertEqual(detail.task_id, task.task_id)
        self.assertEqual(detail.source_task_id, task.task_id)
        self.assertEqual(detail.analysis_id, "analysis-1")
        self.assertEqual(detail.analysis_profile_id, "profile-1")
        self.assertEqual(detail.project_id, "project-1")
        self.assertEqual(detail.artifact_path, str(artifact))
        self.assertEqual(detail.artifact_status, TaskResultArtifactStatus.PRESENT)
        self.assertEqual(detail.summary, "Summary ready.")
        self.assertEqual(detail.metadata["custom"], {"nested": True})
        self.assertEqual(detail.created_at, result.created_at)
        self.assertEqual(detail.updated_at, result.created_at)
        self.assertEqual(detail.error_code, "")

    def test_missing_result_returns_stable_error_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir) / "state")

            detail = service.get_task_result_detail("missing-result")

        self.assertEqual(detail.result_id, "missing-result")
        self.assertEqual(detail.result_type, "")
        self.assertIsNone(detail.state)
        self.assertEqual(detail.artifact_status, TaskResultArtifactStatus.NOT_APPLICABLE)
        self.assertEqual(detail.error_code, "result_not_found")
        self.assertIn("missing-result", detail.message)

    def test_artifact_missing_and_not_applicable_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root / "state")
            task = service.create_task("reporting.summary", "Report")
            missing = service.record_result(
                task.task_id,
                "profile_reporting_summary",
                artifact_path=str(root / "missing.csv"),
            )
            no_artifact = service.record_result(task.task_id, "note")

            missing_detail = service.get_task_result_detail(missing.result_id)
            no_artifact_detail = service.get_task_result_detail(no_artifact.result_id)

        self.assertEqual(missing_detail.artifact_status, TaskResultArtifactStatus.MISSING)
        self.assertEqual(
            no_artifact_detail.artifact_status,
            TaskResultArtifactStatus.NOT_APPLICABLE,
        )

    def test_detail_does_not_change_result_or_create_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = TaskManagementService.from_state_dir(root / "state")
            task = service.create_task("reporting.summary", "Report")
            result = service.record_result(
                task.task_id,
                "profile_reporting_summary",
                metadata={"analysis_id": "analysis-1"},
            )
            before_result = service.list_results()[0].to_dict()
            before_result_count = len(service.list_results())
            before_log_count = len(service.list_task_execution_logs())

            detail = service.get_task_result_detail(result.result_id)
            after_result = service.list_results()[0].to_dict()
            after_result_count = len(service.list_results())
            after_log_count = len(service.list_task_execution_logs())

            self.assertEqual(detail.analysis_id, "analysis-1")
            self.assertEqual(after_result, before_result)
            self.assertEqual(after_result_count, before_result_count)
            self.assertEqual(after_log_count, before_log_count)


if __name__ == "__main__":
    unittest.main()
