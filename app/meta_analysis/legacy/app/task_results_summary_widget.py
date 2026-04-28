from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.task_models import (
    ArtifactPreviewRecord,
    TaskResultArtifactDiagnostic,
    TaskResultDetailRecord,
    TaskResultRecord,
)


class TaskResultsSummaryWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._results_section_label = QLabel("Task result registry")
        self._results_section_label.setObjectName("taskResultsSectionLabel")
        self._status_label = QLabel("Task results: 0")
        self._status_label.setObjectName("taskResultsStatusLabel")
        self._diagnostics_section_label = QLabel("Diagnostics")
        self._diagnostics_section_label.setObjectName("taskDiagnosticsSectionLabel")
        self._artifact_status_label = QLabel(
            "Artifacts: present 0, missing 0, not applicable 0"
        )
        self._artifact_status_label.setObjectName("taskResultArtifactStatusLabel")
        self._readiness_section_label = QLabel("Readiness")
        self._readiness_section_label.setObjectName("taskReadinessSectionLabel")
        self._plan_status_label = QLabel(
            "Task plans: total 0, draft 0, ready 0, disabled 0, archived 0"
        )
        self._plan_status_label.setObjectName("taskPlanStatusLabel")
        self._plan_readiness_label = QLabel(
            "Task plan materialization readiness: total 0, materializable 0, blocked 0, ready 0, draft 0, disabled 0, archived 0, missing context 0"
        )
        self._plan_readiness_label.setObjectName("taskPlanMaterializationReadinessLabel")
        self._execution_contract_readiness_label = QLabel(
            "Task execution contract readiness: total 0, ready 0, blocked 0, validation failed 0, missing context 0"
        )
        self._execution_contract_readiness_label.setObjectName(
            "taskExecutionContractReadinessLabel"
        )
        self._execution_log_summary_label = QLabel(
            "Execution logs: total 0, dry-run 0, real-run 0, success/accepted 0, failed/rejected 0, with result 0"
        )
        self._execution_log_summary_label.setObjectName(
            "taskExecutionLogSummaryLabel"
        )
        self._retry_task_summary_label = QLabel(
            "Retry tasks: total 0, pending 0, completed 0, failed 0"
        )
        self._retry_task_summary_label.setObjectName("retryTaskSummaryLabel")
        self._analysis_preflight_summary_label = QLabel(
            "Analysis preflight summaries: total 0"
        )
        self._analysis_preflight_summary_label.setObjectName(
            "analysisPreflightSummaryLabel"
        )
        self._real_dataset_readiness_label = QLabel(
            "Real dataset readiness: no report loaded"
        )
        self._real_dataset_readiness_label.setObjectName(
            "realDatasetReadinessSummaryLabel"
        )
        self._mock_runner_diagnostics_label = QLabel(
            "Mock runner diagnostics: total checks 0, accepted dry-run outcomes 0, rejected outcomes 0, validation failed outcomes 0"
        )
        self._mock_runner_diagnostics_label.setObjectName(
            "mockRunnerDiagnosticsLabel"
        )
        self._runner_adapter_registry_label = QLabel(
            "Runner adapter registry: total adapters 0, adapter types none, supported task types none, no-op adapters 0"
        )
        self._runner_adapter_registry_label.setObjectName(
            "runnerAdapterRegistryLabel"
        )
        self._artifact_preview_section_label = QLabel("Artifact preview")
        self._artifact_preview_section_label.setObjectName(
            "artifactPreviewSectionLabel"
        )
        self._artifact_preview_status_label = QLabel(
            "Artifact preview: no result selected"
        )
        self._artifact_preview_status_label.setObjectName(
            "artifactPreviewStatusLabel"
        )
        self._artifact_preview_text_label = QLabel("")
        self._artifact_preview_text_label.setObjectName("artifactPreviewTextLabel")
        self._result_detail_section_label = QLabel("Result detail")
        self._result_detail_section_label.setObjectName("resultDetailSectionLabel")
        self._result_detail_label = QLabel("Result detail: no result selected")
        self._result_detail_label.setObjectName("resultDetailLabel")
        for label in (
            self._status_label,
            self._artifact_status_label,
            self._plan_status_label,
            self._plan_readiness_label,
            self._execution_contract_readiness_label,
            self._execution_log_summary_label,
            self._retry_task_summary_label,
            self._analysis_preflight_summary_label,
            self._real_dataset_readiness_label,
            self._mock_runner_diagnostics_label,
            self._runner_adapter_registry_label,
            self._artifact_preview_status_label,
            self._artifact_preview_text_label,
            self._result_detail_label,
        ):
            label.setWordWrap(True)

        self._table = QTableWidget(0, 8)
        self._table.setObjectName("taskResultsSummaryTable")
        self._table.setHorizontalHeaderLabels(
            [
                "Result ID",
                "Type",
                "State",
                "Title",
                "Analysis ID",
                "Profile",
                "Artifact",
                "Artifact Status",
            ]
        )
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)

        layout = QVBoxLayout(self)
        layout.addWidget(self._results_section_label)
        layout.addWidget(self._status_label)
        layout.addWidget(self._diagnostics_section_label)
        layout.addWidget(self._artifact_status_label)
        layout.addWidget(self._readiness_section_label)
        layout.addWidget(self._plan_status_label)
        layout.addWidget(self._plan_readiness_label)
        layout.addWidget(self._execution_contract_readiness_label)
        layout.addWidget(self._execution_log_summary_label)
        layout.addWidget(self._retry_task_summary_label)
        layout.addWidget(self._analysis_preflight_summary_label)
        layout.addWidget(self._real_dataset_readiness_label)
        layout.addWidget(self._mock_runner_diagnostics_label)
        layout.addWidget(self._runner_adapter_registry_label)
        layout.addWidget(self._artifact_preview_section_label)
        layout.addWidget(self._artifact_preview_status_label)
        layout.addWidget(self._artifact_preview_text_label)
        layout.addWidget(self._result_detail_section_label)
        layout.addWidget(self._result_detail_label)
        layout.addWidget(self._table)

    def set_task_results(
        self,
        results: list[TaskResultRecord],
        *,
        artifact_summary: dict[str, int] | None = None,
        artifact_diagnostics: list[TaskResultArtifactDiagnostic] | None = None,
        task_plan_summary: dict[str, int] | None = None,
        task_plan_materialization_readiness: dict[str, int] | None = None,
        task_execution_contract_readiness: dict[str, int] | None = None,
        task_execution_log_summary: dict[str, int] | None = None,
        retry_task_summary: dict[str, int] | None = None,
        analysis_preflight_results: list[TaskResultRecord] | None = None,
        real_dataset_readiness_summary: dict[str, object] | None = None,
        mock_runner_diagnostics: dict[str, int] | None = None,
        runner_adapter_registry_summary: dict[str, object] | None = None,
    ) -> None:
        self._table.setRowCount(len(results))
        self._status_label.setText(f"Task results: {len(results)}")
        self._artifact_status_label.setText(self._artifact_summary_text(artifact_summary))
        self._plan_status_label.setText(self._task_plan_summary_text(task_plan_summary))
        self._plan_readiness_label.setText(
            self._task_plan_materialization_readiness_text(
                task_plan_materialization_readiness
            )
        )
        self._execution_contract_readiness_label.setText(
            self._task_execution_contract_readiness_text(
                task_execution_contract_readiness
            )
        )
        self._execution_log_summary_label.setText(
            self._task_execution_log_summary_text(task_execution_log_summary)
        )
        self._retry_task_summary_label.setText(
            self._retry_task_summary_text(retry_task_summary)
        )
        self._analysis_preflight_summary_label.setText(
            self._analysis_preflight_summary_text(analysis_preflight_results)
        )
        self._real_dataset_readiness_label.setText(
            self._real_dataset_readiness_text(real_dataset_readiness_summary)
        )
        self._mock_runner_diagnostics_label.setText(
            self._mock_runner_diagnostics_text(mock_runner_diagnostics)
        )
        self._runner_adapter_registry_label.setText(
            self._runner_adapter_registry_text(runner_adapter_registry_summary)
        )
        diagnostics_by_result_id = {
            item.result_id: item
            for item in artifact_diagnostics or []
        }
        for row_index, result in enumerate(results):
            metadata = result.metadata
            diagnostic = diagnostics_by_result_id.get(result.result_id)
            values = [
                result.result_id,
                result.result_type,
                result.state.value,
                result.title,
                str(metadata.get("analysis_id", "")),
                self._profile_text(metadata),
                result.artifact_path,
                diagnostic.artifact_status.value if diagnostic else "",
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row_index, column_index, item)

    def set_artifact_preview(self, preview: ArtifactPreviewRecord | None) -> None:
        if preview is None:
            self._artifact_preview_status_label.setText(
                "Artifact preview: no result selected"
            )
            self._artifact_preview_text_label.setText("")
            return
        status = "available" if preview.preview_available else preview.error_code or "unavailable"
        self._artifact_preview_status_label.setText(
            "Artifact preview: "
            f"path {preview.artifact_path or 'none'}, "
            f"status {status}, "
            f"exists {self._yes_no(preview.exists)}, "
            f"type {preview.file_extension or 'none'}, "
            f"size {preview.size_bytes} bytes, "
            f"message {preview.message or 'none'}"
        )
        self._artifact_preview_text_label.setText(preview.preview_text)

    def set_result_detail(self, detail: TaskResultDetailRecord | None) -> None:
        if detail is None:
            self._result_detail_label.setText("Result detail: no result selected")
            return
        if detail.error_code:
            self._result_detail_label.setText(
                "Result detail: "
                f"result {detail.result_id or 'none'}, "
                f"status {detail.error_code}, "
                f"message {detail.message or 'none'}"
            )
            return
        metadata_text = self._metadata_summary_text(detail.metadata)
        state = detail.state.value if detail.state is not None else "none"
        self._result_detail_label.setText(
            "Result detail: "
            f"result {detail.result_id}, "
            f"type {detail.result_type}, "
            f"state {state}, "
            f"title {detail.title or 'none'}, "
            f"task {detail.task_id or 'none'}, "
            f"source task {detail.source_task_id or 'none'}, "
            f"analysis {detail.analysis_id or 'none'}, "
            f"profile {detail.analysis_profile_id or 'none'}, "
            f"project {detail.project_id or 'none'}, "
            f"artifact {detail.artifact_path or 'none'}, "
            f"artifact status {detail.artifact_status.value}, "
            f"metadata {metadata_text}"
        )

    def status_text(self) -> str:
        return self._status_label.text()

    def artifact_status_text(self) -> str:
        return self._artifact_status_label.text()

    def task_plan_status_text(self) -> str:
        return self._plan_status_label.text()

    def task_plan_materialization_readiness_text(self) -> str:
        return self._plan_readiness_label.text()

    def task_execution_contract_readiness_text(self) -> str:
        return self._execution_contract_readiness_label.text()

    def task_execution_log_summary_text(self) -> str:
        return self._execution_log_summary_label.text()

    def retry_task_summary_text(self) -> str:
        return self._retry_task_summary_label.text()

    def analysis_preflight_summary_text(self) -> str:
        return self._analysis_preflight_summary_label.text()

    def real_dataset_readiness_summary_text(self) -> str:
        return self._real_dataset_readiness_label.text()

    def mock_runner_diagnostics_text(self) -> str:
        return self._mock_runner_diagnostics_label.text()

    def runner_adapter_registry_text(self) -> str:
        return self._runner_adapter_registry_label.text()

    def artifact_preview_status_text(self) -> str:
        return self._artifact_preview_status_label.text()

    def artifact_preview_text(self) -> str:
        return self._artifact_preview_text_label.text()

    def result_detail_text(self) -> str:
        return self._result_detail_label.text()

    def result_cell_text(self, row: int, column: int) -> str:
        item = self._table.item(row, column)
        return item.text() if item is not None else ""

    def result_cell_is_editable(self, row: int, column: int) -> bool:
        item = self._table.item(row, column)
        if item is None:
            return False
        return bool(item.flags() & Qt.ItemFlag.ItemIsEditable)

    def summary_labels_wrap_text(self) -> bool:
        return all(
            label.wordWrap()
            for label in (
                self._status_label,
                self._artifact_status_label,
                self._plan_status_label,
                self._plan_readiness_label,
                self._execution_contract_readiness_label,
                self._execution_log_summary_label,
                self._retry_task_summary_label,
                self._analysis_preflight_summary_label,
                self._real_dataset_readiness_label,
                self._mock_runner_diagnostics_label,
                self._runner_adapter_registry_label,
                self._artifact_preview_status_label,
                self._artifact_preview_text_label,
                self._result_detail_label,
            )
        )

    def _yes_no(self, value: bool) -> str:
        return "yes" if value else "no"

    def _artifact_summary_text(self, summary: dict[str, int] | None) -> str:
        values = summary or {}
        return (
            f"Artifacts: present {values.get('present_artifacts', 0)}, "
            f"missing {values.get('missing_artifacts', 0)}, "
            f"not applicable {values.get('not_applicable_artifacts', 0)}"
        )

    def _task_plan_summary_text(self, summary: dict[str, int] | None) -> str:
        values = summary or {}
        return (
            f"Task plans: total {values.get('total_plans', 0)}, "
            f"draft {values.get('draft_plans', 0)}, "
            f"ready {values.get('ready_plans', 0)}, "
            f"disabled {values.get('disabled_plans', 0)}, "
            f"archived {values.get('archived_plans', 0)}"
        )

    def _task_plan_materialization_readiness_text(
        self,
        summary: dict[str, int] | None,
    ) -> str:
        values = summary or {}
        return (
            "Task plan materialization readiness: "
            f"total {values.get('total_plans', 0)}, "
            f"materializable {values.get('materializable_plans', 0)}, "
            f"blocked {values.get('blocked_plans', 0)}, "
            f"ready {values.get('ready_plans', 0)}, "
            f"draft {values.get('draft_plans', 0)}, "
            f"disabled {values.get('disabled_plans', 0)}, "
            f"archived {values.get('archived_plans', 0)}, "
            f"missing context {values.get('missing_context_plans', 0)}"
        )

    def _task_execution_contract_readiness_text(
        self,
        summary: dict[str, int] | None,
    ) -> str:
        values = summary or {}
        return (
            "Task execution contract readiness: "
            f"total {values.get('total_tasks', 0)}, "
            f"ready {values.get('ready_tasks', 0)}, "
            f"blocked {values.get('blocked_tasks', 0)}, "
            f"validation failed {values.get('validation_failed_tasks', 0)}, "
            f"missing context {values.get('missing_context_tasks', 0)}"
        )

    def _task_execution_log_summary_text(
        self,
        summary: dict[str, int] | None,
    ) -> str:
        values = summary or {}
        return (
            "Execution logs: "
            f"total {values.get('total_logs', 0)}, "
            f"dry-run {values.get('dry_run_logs', 0)}, "
            f"real-run {values.get('real_run_logs', 0)}, "
            f"success/accepted {values.get('success_accepted_logs', 0)}, "
            f"failed/rejected {values.get('failed_rejected_logs', 0)}, "
            f"with result {values.get('logs_with_result_id', 0)}"
        )

    def _retry_task_summary_text(
        self,
        summary: dict[str, int] | None,
    ) -> str:
        values = summary or {}
        return (
            "Retry tasks: "
            f"total {values.get('total_retry_tasks', 0)}, "
            f"pending {values.get('retry_tasks_pending', 0)}, "
            f"completed {values.get('retry_tasks_completed', 0)}, "
            f"failed {values.get('retry_tasks_failed', 0)}"
        )

    def _analysis_preflight_summary_text(
        self,
        results: list[TaskResultRecord] | None,
    ) -> str:
        records = list(results or [])
        if not records:
            return "Analysis preflight summaries: total 0"
        latest = records[-1]
        metadata = latest.metadata
        runnable = "yes" if bool(metadata.get("runnable")) else "no"
        return (
            "Analysis preflight summaries: "
            f"total {len(records)}, "
            f"latest result {latest.result_id}, "
            f"dataset {metadata.get('dataset_id', 'none') or 'none'}, "
            f"profile {metadata.get('profile_id', 'none') or 'none'}, "
            f"runnable {runnable}, "
            f"blocking errors {metadata.get('blocking_error_count', 0)}, "
            f"warnings {metadata.get('warning_count', 0)}, "
            "recommended action "
            f"{metadata.get('recommended_action', 'none') or 'none'}"
        )

    def _real_dataset_readiness_text(
        self,
        summary: dict[str, object] | None,
    ) -> str:
        values = summary or {}
        if not values:
            return "Real dataset readiness: no report loaded"
        detected_groups = self._summary_items(values.get("detected_groups"))
        excluded_groups = self._summary_items(values.get("excluded_groups"))
        blocking_gaps = self._summary_items(values.get("blocking_gaps"))
        warnings = self._summary_items(values.get("warnings"))
        return (
            "Real dataset readiness: "
            f"dataset {values.get('dataset_id', 'none') or 'none'}, "
            "recommended action "
            f"{values.get('recommended_action', 'none') or 'none'}, "
            f"gaps {self._summary_int(values.get('gap_count'))}, "
            "preflight runnable "
            f"{self._yes_no(bool(values.get('preflight_runnable')))}, "
            f"features {self._summary_int(values.get('feature_count'))}, "
            f"samples {self._summary_int(values.get('sample_count'))}, "
            "mapping success rate "
            f"{values.get('mapping_success_rate', 0)}, "
            "detected groups "
            f"{', '.join(detected_groups) if detected_groups else 'none'}, "
            "excluded groups "
            f"{', '.join(excluded_groups) if excluded_groups else 'none'}, "
            "blocking gaps "
            f"{', '.join(blocking_gaps) if blocking_gaps else 'none'}, "
            f"warnings {len(warnings)}"
        )

    def _mock_runner_diagnostics_text(
        self,
        summary: dict[str, int] | None,
    ) -> str:
        values = summary or {}
        return (
            "Mock runner diagnostics: "
            f"total checks {values.get('total_checks', 0)}, "
            "accepted dry-run outcomes "
            f"{values.get('accepted_dry_run_outcomes', 0)}, "
            f"rejected outcomes {values.get('rejected_outcomes', 0)}, "
            "validation failed outcomes "
            f"{values.get('validation_failed_outcomes', 0)}"
        )

    def _runner_adapter_registry_text(
        self,
        summary: dict[str, object] | None,
    ) -> str:
        values = summary or {}
        adapter_types = self._summary_items(values.get("adapter_types"))
        supported_task_types = self._summary_items(
            values.get("supported_task_types")
        )
        return (
            "Runner adapter registry: "
            f"total adapters {self._summary_int(values.get('total_adapters'))}, "
            "adapter types "
            f"{', '.join(adapter_types) if adapter_types else 'none'}, "
            "supported task types "
            f"{', '.join(supported_task_types) if supported_task_types else 'none'}, "
            f"no-op adapters {self._summary_int(values.get('no_op_adapters'))}"
        )

    def _summary_items(self, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            return (value,) if value else ()
        if isinstance(value, tuple | list):
            return tuple(str(item) for item in value if str(item))
        return ()

    def _summary_int(self, value: object) -> int:
        return value if isinstance(value, int) else 0

    def _metadata_summary_text(self, metadata: dict[str, object]) -> str:
        if not metadata:
            return "none"
        return ", ".join(f"{key}={metadata[key]}" for key in sorted(metadata))

    def _profile_text(self, metadata: dict[str, object]) -> str:
        profile_id = metadata.get("analysis_profile_id")
        profile_name = str(metadata.get("analysis_profile_name", ""))
        if profile_id is None:
            return ""
        if profile_name:
            return f"{profile_name} ({profile_id})"
        return str(profile_id)
