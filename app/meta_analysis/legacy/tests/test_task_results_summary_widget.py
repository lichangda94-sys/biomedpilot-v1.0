import os
import unittest

from core.task_models import (
    ArtifactPreviewRecord,
    TaskResultArtifactDiagnostic,
    TaskResultArtifactStatus,
    TaskResultDetailRecord,
    TaskResultRecord,
    TaskResultState,
)


class TaskResultsSummaryWidgetTests(unittest.TestCase):
    def test_displays_registered_task_results_read_only(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()
        result = TaskResultRecord(
            result_id="tres-1",
            task_id="task-1",
            result_type="profile_reporting_summary",
            state=TaskResultState.AVAILABLE,
            title="Profile reporting summary",
            artifact_path="output/proj/reporting/summary.csv",
            metadata={
                "analysis_id": "analysis-1",
                "analysis_profile_id": "aprof-1",
                "analysis_profile_name": "Primary profile",
            },
        )
        widget.set_task_results(
            [result],
            artifact_summary={
                "total_results": 1,
                "present_artifacts": 1,
                "missing_artifacts": 0,
                "not_applicable_artifacts": 0,
            },
            task_plan_summary={
                "total_plans": 4,
                "draft_plans": 1,
                "ready_plans": 1,
                "disabled_plans": 1,
                "archived_plans": 1,
            },
            task_plan_materialization_readiness={
                "total_plans": 4,
                "materializable_plans": 1,
                "blocked_plans": 3,
                "ready_plans": 1,
                "draft_plans": 1,
                "disabled_plans": 1,
                "archived_plans": 1,
                "missing_context_plans": 0,
            },
            task_execution_contract_readiness={
                "total_tasks": 3,
                "ready_tasks": 2,
                "blocked_tasks": 1,
                "validation_failed_tasks": 0,
                "missing_context_tasks": 1,
            },
            task_execution_log_summary={
                "total_logs": 5,
                "dry_run_logs": 2,
                "real_run_logs": 3,
                "success_accepted_logs": 4,
                "failed_rejected_logs": 1,
                "logs_with_result_id": 2,
            },
            retry_task_summary={
                "total_retry_tasks": 3,
                "retry_tasks_pending": 1,
                "retry_tasks_completed": 1,
                "retry_tasks_failed": 1,
            },
            analysis_preflight_results=[
                TaskResultRecord(
                    result_id="tres-preflight",
                    task_id="task-preflight",
                    result_type="analysis_preflight_summary",
                    state=TaskResultState.AVAILABLE,
                    title="Analysis preflight summary",
                    metadata={
                        "dataset_id": "GSE-ready",
                        "profile_id": "profile-a",
                        "runnable": True,
                        "blocking_error_count": 0,
                        "warning_count": 2,
                        "recommended_action": "review_warnings_before_analysis",
                    },
                )
            ],
            real_dataset_readiness_summary={
                "dataset_id": "GSE33630",
                "recommended_action": "ready_for_manual_review",
                "gap_count": 0,
                "preflight_runnable": True,
                "feature_count": 54675,
                "sample_count": 105,
                "mapping_success_rate": 0.8373,
                "detected_groups": ("ptc", "normal"),
                "excluded_groups": ("atc",),
                "blocking_gaps": (),
                "warnings": ("review_required",),
            },
            mock_runner_diagnostics={
                "total_checks": 3,
                "accepted_dry_run_outcomes": 2,
                "rejected_outcomes": 1,
                "validation_failed_outcomes": 1,
            },
            runner_adapter_registry_summary={
                "total_adapters": 1,
                "adapter_types": ("no_op",),
                "supported_task_types": ("reporting.summary",),
                "no_op_adapters": 1,
            },
            artifact_diagnostics=[
                TaskResultArtifactDiagnostic(
                    result_id=result.result_id,
                    result_type=result.result_type,
                    state=result.state,
                    artifact_path=result.artifact_path,
                    artifact_status=TaskResultArtifactStatus.PRESENT,
                )
            ],
        )

        self.assertEqual(widget.status_text(), "Task results: 1")
        self.assertEqual(widget.artifact_status_text(), "Artifacts: present 1, missing 0, not applicable 0")
        self.assertEqual(widget.task_plan_status_text(), "Task plans: total 4, draft 1, ready 1, disabled 1, archived 1")
        self.assertEqual(widget.task_plan_materialization_readiness_text(), "Task plan materialization readiness: total 4, materializable 1, blocked 3, ready 1, draft 1, disabled 1, archived 1, missing context 0")
        self.assertEqual(widget.task_execution_contract_readiness_text(), "Task execution contract readiness: total 3, ready 2, blocked 1, validation failed 0, missing context 1")
        self.assertEqual(widget.task_execution_log_summary_text(), "Execution logs: total 5, dry-run 2, real-run 3, success/accepted 4, failed/rejected 1, with result 2")
        self.assertEqual(widget.retry_task_summary_text(), "Retry tasks: total 3, pending 1, completed 1, failed 1")
        self.assertEqual(widget.analysis_preflight_summary_text(), "Analysis preflight summaries: total 1, latest result tres-preflight, dataset GSE-ready, profile profile-a, runnable yes, blocking errors 0, warnings 2, recommended action review_warnings_before_analysis")
        self.assertEqual(widget.real_dataset_readiness_summary_text(), "Real dataset readiness: dataset GSE33630, recommended action ready_for_manual_review, gaps 0, preflight runnable yes, features 54675, samples 105, mapping success rate 0.8373, detected groups ptc, normal, excluded groups atc, blocking gaps none, warnings 1")
        self.assertEqual(widget.mock_runner_diagnostics_text(), "Mock runner diagnostics: total checks 3, accepted dry-run outcomes 2, rejected outcomes 1, validation failed outcomes 1")
        self.assertEqual(widget.runner_adapter_registry_text(), "Runner adapter registry: total adapters 1, adapter types no_op, supported task types reporting.summary, no-op adapters 1")
        self.assertEqual(widget.result_cell_text(0, 0), "tres-1")
        self.assertEqual(widget.result_cell_text(0, 1), "profile_reporting_summary")
        self.assertEqual(widget.result_cell_text(0, 4), "analysis-1")
        self.assertEqual(widget.result_cell_text(0, 5), "Primary profile (aprof-1)")
        self.assertEqual(widget.result_cell_text(0, 7), "present")
        self.assertFalse(widget.result_cell_is_editable(0, 0))
        self.assertFalse(widget.result_cell_is_editable(0, 7))
        self.assertTrue(widget.summary_labels_wrap_text())
        app.processEvents()

    def test_displays_empty_task_plan_summary(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()

        widget.set_task_results([])

        self.assertEqual(widget.task_plan_status_text(), "Task plans: total 0, draft 0, ready 0, disabled 0, archived 0")
        self.assertEqual(widget.task_plan_materialization_readiness_text(), "Task plan materialization readiness: total 0, materializable 0, blocked 0, ready 0, draft 0, disabled 0, archived 0, missing context 0")
        self.assertEqual(widget.task_execution_contract_readiness_text(), "Task execution contract readiness: total 0, ready 0, blocked 0, validation failed 0, missing context 0")
        self.assertEqual(widget.task_execution_log_summary_text(), "Execution logs: total 0, dry-run 0, real-run 0, success/accepted 0, failed/rejected 0, with result 0")
        self.assertEqual(widget.retry_task_summary_text(), "Retry tasks: total 0, pending 0, completed 0, failed 0")
        self.assertEqual(widget.analysis_preflight_summary_text(), "Analysis preflight summaries: total 0")
        self.assertEqual(widget.real_dataset_readiness_summary_text(), "Real dataset readiness: no report loaded")
        self.assertEqual(widget.mock_runner_diagnostics_text(), "Mock runner diagnostics: total checks 0, accepted dry-run outcomes 0, rejected outcomes 0, validation failed outcomes 0")
        self.assertEqual(widget.runner_adapter_registry_text(), "Runner adapter registry: total adapters 0, adapter types none, supported task types none, no-op adapters 0")
        self.assertTrue(widget.summary_labels_wrap_text())
        app.processEvents()

    def test_displays_real_dataset_readiness_gap_summary_read_only(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()

        widget.set_task_results(
            [],
            real_dataset_readiness_summary={
                "dataset_id": "GSE60542",
                "recommended_action": "fix_group_detection",
                "gap_count": 2,
                "preflight_runnable": False,
                "feature_count": 0,
                "sample_count": 0,
                "mapping_success_rate": 0,
                "detected_groups": ("primary",),
                "excluded_groups": (),
                "blocking_gaps": (
                    "group_detection_gap",
                    "comparison_readiness_gap",
                ),
                "warnings": ("manual confirmation required", "N0/N1 ambiguous"),
            },
        )

        self.assertEqual(
            widget.real_dataset_readiness_summary_text(),
            "Real dataset readiness: dataset GSE60542, recommended action fix_group_detection, gaps 2, preflight runnable no, features 0, samples 0, mapping success rate 0, detected groups primary, excluded groups none, blocking gaps group_detection_gap, comparison_readiness_gap, warnings 2",
        )
        self.assertTrue(widget.summary_labels_wrap_text())
        app.processEvents()

    def test_displays_execution_log_summary_read_only(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()

        widget.set_task_results(
            [],
            task_execution_log_summary={
                "total_logs": 3,
                "dry_run_logs": 1,
                "real_run_logs": 2,
                "success_accepted_logs": 2,
                "failed_rejected_logs": 1,
                "logs_with_result_id": 1,
            },
        )

        self.assertEqual(widget.task_execution_log_summary_text(), "Execution logs: total 3, dry-run 1, real-run 2, success/accepted 2, failed/rejected 1, with result 1")
        self.assertTrue(widget.summary_labels_wrap_text())
        app.processEvents()

    def test_displays_retry_task_summary_read_only(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()

        widget.set_task_results(
            [],
            retry_task_summary={
                "total_retry_tasks": 4,
                "retry_tasks_pending": 2,
                "retry_tasks_completed": 1,
                "retry_tasks_failed": 1,
            },
        )

        self.assertEqual(
            widget.retry_task_summary_text(),
            "Retry tasks: total 4, pending 2, completed 1, failed 1",
        )
        self.assertTrue(widget.summary_labels_wrap_text())
        app.processEvents()

    def test_displays_runner_adapter_registry_summary_read_only(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()

        widget.set_task_results(
            [],
            runner_adapter_registry_summary={
                "total_adapters": 2,
                "adapter_types": ("no_op", "future_runner"),
                "supported_task_types": ("reporting.summary", "analysis.run"),
                "no_op_adapters": 1,
            },
        )

        self.assertEqual(widget.runner_adapter_registry_text(), "Runner adapter registry: total adapters 2, adapter types no_op, future_runner, supported task types reporting.summary, analysis.run, no-op adapters 1")
        app.processEvents()

    def test_displays_rejected_mock_runner_diagnostics(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()

        widget.set_task_results(
            [],
            mock_runner_diagnostics={
                "total_checks": 2,
                "accepted_dry_run_outcomes": 0,
                "rejected_outcomes": 2,
                "validation_failed_outcomes": 2,
            },
        )

        self.assertEqual(widget.mock_runner_diagnostics_text(), "Mock runner diagnostics: total checks 2, accepted dry-run outcomes 0, rejected outcomes 2, validation failed outcomes 2")
        app.processEvents()

    def test_displays_blocked_task_execution_contract_readiness(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()

        widget.set_task_results(
            [],
            task_execution_contract_readiness={
                "total_tasks": 2,
                "ready_tasks": 0,
                "blocked_tasks": 2,
                "validation_failed_tasks": 1,
                "missing_context_tasks": 1,
            },
        )

        self.assertEqual(widget.task_execution_contract_readiness_text(), "Task execution contract readiness: total 2, ready 0, blocked 2, validation failed 1, missing context 1")
        app.processEvents()

    def test_displays_blocked_task_plan_materialization_readiness(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()

        widget.set_task_results(
            [],
            task_plan_materialization_readiness={
                "total_plans": 2,
                "materializable_plans": 0,
                "blocked_plans": 2,
                "ready_plans": 0,
                "draft_plans": 1,
                "disabled_plans": 1,
                "archived_plans": 0,
                "missing_context_plans": 0,
            },
        )

        self.assertEqual(widget.task_plan_materialization_readiness_text(), "Task plan materialization readiness: total 2, materializable 0, blocked 2, ready 0, draft 1, disabled 1, archived 0, missing context 0")
        app.processEvents()

    def test_displays_missing_and_empty_artifact_diagnostics(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()
        missing = TaskResultRecord(
            result_id="tres-missing",
            task_id="task-1",
            result_type="profile_reporting_summary",
            artifact_path="missing.csv",
        )
        not_applicable = TaskResultRecord(
            result_id="tres-note",
            task_id="task-1",
            result_type="note",
        )

        widget.set_task_results(
            [missing, not_applicable],
            artifact_summary={
                "total_results": 2,
                "present_artifacts": 0,
                "missing_artifacts": 1,
                "not_applicable_artifacts": 1,
            },
            artifact_diagnostics=[
                TaskResultArtifactDiagnostic(
                    result_id=missing.result_id,
                    result_type=missing.result_type,
                    state=missing.state,
                    artifact_path=missing.artifact_path,
                    artifact_status=TaskResultArtifactStatus.MISSING,
                ),
                TaskResultArtifactDiagnostic(
                    result_id=not_applicable.result_id,
                    result_type=not_applicable.result_type,
                    state=not_applicable.state,
                    artifact_path=not_applicable.artifact_path,
                    artifact_status=TaskResultArtifactStatus.NOT_APPLICABLE,
                ),
            ],
        )

        self.assertEqual(widget.status_text(), "Task results: 2")
        self.assertEqual(widget.artifact_status_text(), "Artifacts: present 0, missing 1, not applicable 1")
        self.assertEqual(widget.result_cell_text(0, 7), "missing")
        self.assertEqual(widget.result_cell_text(1, 7), "not_applicable")
        app.processEvents()

    def test_displays_artifact_preview_text_read_only(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()

        widget.set_artifact_preview(
            ArtifactPreviewRecord(
                artifact_path="/tmp/summary.csv",
                exists=True,
                file_name="summary.csv",
                file_extension=".csv",
                size_bytes=32,
                preview_available=True,
                preview_text="analysis_id,value\nanalysis-1,42",
                message="Artifact preview available.",
            )
        )

        self.assertEqual(
            widget.artifact_preview_status_text(),
            "Artifact preview: path /tmp/summary.csv, status available, exists yes, type .csv, size 32 bytes, message Artifact preview available.",
        )
        self.assertIn("analysis-1", widget.artifact_preview_text())
        self.assertTrue(widget.summary_labels_wrap_text())
        app.processEvents()

    def test_displays_missing_artifact_preview_message(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()

        widget.set_artifact_preview(
            ArtifactPreviewRecord(
                artifact_path="/tmp/missing.csv",
                exists=False,
                file_name="missing.csv",
                file_extension=".csv",
                preview_available=False,
                message="Artifact file is missing.",
                error_code="missing",
            )
        )

        self.assertIn("status missing", widget.artifact_preview_status_text())
        self.assertEqual(widget.artifact_preview_text(), "")
        app.processEvents()

    def test_displays_result_detail_read_only(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()

        widget.set_result_detail(
            TaskResultDetailRecord(
                result_id="result-1",
                result_type="profile_reporting_summary",
                state=TaskResultState.AVAILABLE,
                title="Profile reporting summary",
                task_id="task-1",
                source_task_id="task-1",
                analysis_id="analysis-1",
                analysis_profile_id="profile-1",
                project_id="project-1",
                artifact_path="/tmp/summary.csv",
                artifact_status=TaskResultArtifactStatus.PRESENT,
                metadata={"analysis_id": "analysis-1", "runner_type": "reporting"},
            )
        )

        detail_text = widget.result_detail_text()
        self.assertIn("result result-1", detail_text)
        self.assertIn("type profile_reporting_summary", detail_text)
        self.assertIn("artifact status present", detail_text)
        self.assertIn("analysis_id=analysis-1", detail_text)
        self.assertIn("runner_type=reporting", detail_text)
        self.assertTrue(widget.summary_labels_wrap_text())
        app.processEvents()

    def test_displays_missing_result_detail_message(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("PySide6 is not installed.") from exc
        from app.task_results_summary_widget import TaskResultsSummaryWidget

        app = QApplication.instance() or QApplication([])
        widget = TaskResultsSummaryWidget()

        widget.set_result_detail(
            TaskResultDetailRecord(
                result_id="missing-result",
                result_type="",
                state=None,
                message="Task result does not exist: missing-result",
                error_code="result_not_found",
            )
        )

        self.assertEqual(
            widget.result_detail_text(),
            "Result detail: result missing-result, status result_not_found, message Task result does not exist: missing-result",
        )
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
