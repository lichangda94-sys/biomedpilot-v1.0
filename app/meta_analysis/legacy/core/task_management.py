from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from core.task_models import (
    ArtifactPreviewRecord,
    TaskExecutionContractDiagnostic,
    TaskExecutionContractReason,
    TaskExecutionLogRecord,
    TaskExecutionOutcome,
    TaskExecutionOutcomeStatus,
    TaskExecutionRequest,
    TaskPlanMaterializationDiagnostic,
    TaskPlanMaterializationReason,
    TaskPlanRecord,
    TaskPlanState,
    TaskRecord,
    TaskResultArtifactDiagnostic,
    TaskResultArtifactStatus,
    TaskResultDetailRecord,
    TaskResultRecord,
    TaskResultState,
)
from core.task_status import TaskState
from core.task_store import TaskRecordStore


TASK_RESULT_ARTIFACT_SUMMARY_KEYS = (
    "total_results",
    "present_artifacts",
    "missing_artifacts",
    "not_applicable_artifacts",
)

TASK_PLAN_SUMMARY_KEYS = (
    "total_plans",
    "draft_plans",
    "ready_plans",
    "disabled_plans",
    "archived_plans",
)

TASK_PLAN_MATERIALIZATION_READINESS_SUMMARY_KEYS = (
    "total_plans",
    "materializable_plans",
    "blocked_plans",
    "ready_plans",
    "draft_plans",
    "disabled_plans",
    "archived_plans",
    "missing_context_plans",
)

TASK_EXECUTION_CONTRACT_READINESS_SUMMARY_KEYS = (
    "total_tasks",
    "ready_tasks",
    "blocked_tasks",
    "validation_failed_tasks",
    "missing_context_tasks",
)

MOCK_RUNNER_DIAGNOSTICS_SUMMARY_KEYS = (
    "total_checks",
    "accepted_dry_run_outcomes",
    "rejected_outcomes",
    "validation_failed_outcomes",
)

MANUAL_RUNNER_WRAPPER_DIAGNOSTICS_SUMMARY_KEYS = (
    "dry_run_checks",
    "accepted_outcomes",
    "rejected_outcomes",
    "missing_adapter_outcomes",
)

LIFECYCLE_RUNNER_WRAPPER_DIAGNOSTICS_SUMMARY_KEYS = (
    "dry_run_checks",
    "accepted_outcomes",
    "rejected_outcomes",
    "state_mutations",
)

LIFECYCLE_GUARD_DIAGNOSTICS_KEYS = (
    "pending_allowed",
    "running_blocked",
    "completed_blocked",
    "failed_blocked",
    "dry_run_mutations",
)

REAL_RUN_PREFLIGHT_DIAGNOSTICS_SUMMARY_KEYS = (
    "checked_tasks",
    "eligible_tasks",
    "blocked_tasks",
    "adapter_missing",
    "state_mutations",
)

PROFILE_REPORTING_RESULT_SUMMARY_KEYS = (
    "total_results",
    "present_artifacts",
    "missing_artifacts",
    "not_applicable_artifacts",
)

TASK_EXECUTION_LOG_SUMMARY_KEYS = (
    "total_logs",
    "dry_run_logs",
    "real_run_logs",
    "success_accepted_logs",
    "failed_rejected_logs",
    "logs_with_result_id",
)

RETRY_TASK_SUMMARY_KEYS = (
    "total_retry_tasks",
    "retry_tasks_pending",
    "retry_tasks_completed",
    "retry_tasks_failed",
)

SUPPORTED_ARTIFACT_PREVIEW_EXTENSIONS = {".csv", ".json", ".txt", ".md"}


def format_task_result_artifact_diagnostics_summary(
    summary: dict[str, int] | None,
) -> list[str]:
    values = summary or {}
    lines = ["Task result artifact diagnostics:"]
    for key in TASK_RESULT_ARTIFACT_SUMMARY_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def format_task_plan_summary(summary: dict[str, int] | None) -> list[str]:
    values = summary or {}
    lines = ["Task plan summary:"]
    for key in TASK_PLAN_SUMMARY_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def format_task_plan_materialization_readiness_summary(
    summary: dict[str, int] | None,
) -> list[str]:
    values = summary or {}
    lines = ["Task plan materialization readiness:"]
    for key in TASK_PLAN_MATERIALIZATION_READINESS_SUMMARY_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def format_task_execution_contract_readiness_summary(
    summary: dict[str, int] | None,
) -> list[str]:
    values = summary or {}
    lines = ["Task execution contract readiness:"]
    for key in TASK_EXECUTION_CONTRACT_READINESS_SUMMARY_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def format_mock_runner_diagnostics_summary(
    summary: dict[str, int] | None,
) -> list[str]:
    values = summary or {}
    lines = ["Mock task runner diagnostics:"]
    for key in MOCK_RUNNER_DIAGNOSTICS_SUMMARY_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def format_manual_runner_wrapper_diagnostics_summary(
    summary: dict[str, int] | None,
) -> list[str]:
    values = summary or {}
    lines = ["Manual runner wrapper:"]
    for key in MANUAL_RUNNER_WRAPPER_DIAGNOSTICS_SUMMARY_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def format_lifecycle_runner_wrapper_diagnostics_summary(
    summary: dict[str, int] | None,
) -> list[str]:
    values = summary or {}
    lines = ["Lifecycle runner wrapper:"]
    for key in LIFECYCLE_RUNNER_WRAPPER_DIAGNOSTICS_SUMMARY_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def format_lifecycle_guard_diagnostics_summary(
    summary: dict[str, object] | None,
) -> list[str]:
    values = summary or {}
    lines = ["Lifecycle guard diagnostics:"]
    for key in LIFECYCLE_GUARD_DIAGNOSTICS_KEYS:
        value = values.get(key, False if key != "dry_run_mutations" else 0)
        if key == "dry_run_mutations":
            value = value if isinstance(value, int) else 0
        else:
            value = "yes" if value is True else "no"
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def format_real_run_preflight_diagnostics_summary(
    summary: dict[str, int] | None,
) -> list[str]:
    values = summary or {}
    lines = ["Real-run preflight diagnostics:"]
    for key in REAL_RUN_PREFLIGHT_DIAGNOSTICS_SUMMARY_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def format_profile_reporting_result_summary(
    summary: dict[str, int] | None,
) -> list[str]:
    values = summary or {}
    lines = ["Profile reporting summary results:"]
    for key in PROFILE_REPORTING_RESULT_SUMMARY_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def format_task_execution_log_summary(
    summary: dict[str, int] | None,
) -> list[str]:
    values = summary or {}
    lines = ["Execution log summary:"]
    for key in TASK_EXECUTION_LOG_SUMMARY_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def format_retry_task_summary(summary: dict[str, int] | None) -> list[str]:
    values = summary or {}
    lines = ["Retry task summary:"]
    for key in RETRY_TASK_SUMMARY_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


class TaskManagementService:
    def __init__(self, store: TaskRecordStore) -> None:
        self._store = store

    @classmethod
    def from_state_dir(cls, state_dir: Path) -> "TaskManagementService":
        return cls(TaskRecordStore(state_dir))

    def create_task(
        self,
        task_type: str,
        title: str,
        *,
        project_id: str | None = None,
        source_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> TaskRecord:
        self._require(task_type.strip(), "task_type is required.")
        self._require(title.strip(), "title is required.")
        return self._store.save_task(
            TaskRecord(
                task_id=f"task-{uuid4().hex[:12]}",
                task_type=task_type.strip(),
                title=title.strip(),
                project_id=project_id.strip() if project_id else None,
                source_id=source_id.strip() if source_id else None,
                metadata=dict(metadata or {}),
            )
        )

    def create_retry_task(self, original_task_id: str) -> TaskRecord:
        original = self._require_task(original_task_id)
        if original.state != TaskState.FAILED:
            raise ValueError(
                "Retry task can only be created from a failed task; "
                f"current state is {original.state.value}."
            )
        metadata = dict(original.metadata)
        metadata["retry_of_task_id"] = original.task_id
        metadata["original_task_id"] = original.task_id
        metadata["original_task_state"] = original.state.value
        return self.create_task(
            original.task_type,
            f"Retry: {original.title}",
            project_id=original.project_id,
            source_id=original.source_id,
            metadata=metadata,
        )

    def start_task(self, task_id: str, message: str = "started") -> TaskRecord:
        return self._transition(task_id, TaskState.RUNNING, message)

    def complete_task(
        self,
        task_id: str,
        *,
        message: str = "completed",
        result_type: str | None = None,
        title: str = "",
        artifact_path: str = "",
        summary: str = "",
        metadata: dict[str, object] | None = None,
    ) -> TaskRecord:
        task = self._transition(task_id, TaskState.COMPLETED, message)
        if result_type is not None:
            self.record_result(
                task_id,
                result_type,
                title=title,
                artifact_path=artifact_path,
                summary=summary,
                metadata=metadata,
            )
        return task

    def fail_task(
        self,
        task_id: str,
        message: str,
        *,
        result_type: str = "error",
        summary: str = "",
        metadata: dict[str, object] | None = None,
    ) -> TaskRecord:
        task = self._transition(task_id, TaskState.FAILED, message)
        self.record_result(
            task_id,
            result_type,
            state=TaskResultState.FAILED,
            title="Task failed",
            summary=summary or message,
            metadata=metadata,
        )
        return task

    def record_result(
        self,
        task_id: str,
        result_type: str,
        *,
        state: TaskResultState = TaskResultState.AVAILABLE,
        title: str = "",
        artifact_path: str = "",
        summary: str = "",
        metadata: dict[str, object] | None = None,
    ) -> TaskResultRecord:
        self._require_task(task_id)
        self._require(result_type.strip(), "result_type is required.")
        return self._store.save_result(
            TaskResultRecord(
                result_id=f"tres-{uuid4().hex[:12]}",
                task_id=task_id,
                result_type=result_type.strip(),
                state=state,
                title=title.strip(),
                artifact_path=artifact_path.strip(),
                summary=summary.strip(),
                metadata=dict(metadata or {}),
            )
        )

    def register_profile_reporting_result(
        self,
        task_id: str,
        *,
        analysis_id: str,
        project_id: str,
        analysis_profile_id: str | None = None,
        analysis_profile_name: str = "",
        artifact_path: str = "",
        summary: str = "",
        metadata: dict[str, object] | None = None,
    ) -> TaskResultRecord:
        result_metadata = {
            "analysis_id": analysis_id,
            "project_id": project_id,
            "analysis_profile_id": analysis_profile_id,
            "analysis_profile_name": analysis_profile_name,
        }
        result_metadata.update(dict(metadata or {}))
        return self.record_result(
            task_id,
            "profile_reporting_summary",
            title="Profile reporting summary",
            artifact_path=artifact_path,
            summary=summary,
            metadata=result_metadata,
        )

    def register_analysis_preflight_result(
        self,
        task_id: str,
        *,
        dataset_id: str,
        profile_id: str,
        runnable: bool,
        blocking_error_count: int,
        warning_count: int,
        artifact_path: str = "",
        recommended_action: str = "",
        summary: str = "",
        metadata: dict[str, object] | None = None,
    ) -> TaskResultRecord:
        result_metadata = {
            "dataset_id": dataset_id,
            "profile_id": profile_id,
            "runnable": runnable,
            "blocking_error_count": blocking_error_count,
            "warning_count": warning_count,
            "recommended_action": recommended_action,
        }
        result_metadata.update(dict(metadata or {}))
        return self.record_result(
            task_id,
            "analysis_preflight_summary",
            title="Analysis preflight summary",
            artifact_path=artifact_path,
            summary=summary,
            metadata=result_metadata,
        )

    def append_task_execution_log(
        self,
        task_id: str,
        *,
        source_plan_id: str | None = None,
        runner_type: str = "",
        task_type: str = "",
        dry_run: bool = True,
        outcome_status: str = "",
        message: str = "",
        error_code: str = "",
        result_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> TaskExecutionLogRecord:
        return self._store.save_execution_log(
            TaskExecutionLogRecord(
                log_id=f"texec-{uuid4().hex[:12]}",
                task_id=task_id,
                source_plan_id=source_plan_id,
                runner_type=runner_type.strip(),
                task_type=task_type.strip(),
                dry_run=dry_run,
                outcome_status=outcome_status.strip(),
                message=message.strip(),
                error_code=error_code.strip(),
                result_id=result_id,
                metadata=dict(metadata or {}),
            )
        )

    def list_task_execution_logs(self) -> list[TaskExecutionLogRecord]:
        return self._store.list_execution_logs()

    def list_task_execution_logs_for_task(
        self,
        task_id: str,
    ) -> list[TaskExecutionLogRecord]:
        return self._store.list_execution_logs(task_id=task_id)

    def summarize_task_execution_logs(
        self,
        logs: list[TaskExecutionLogRecord] | None = None,
    ) -> dict[str, int]:
        records = logs if logs is not None else self.list_task_execution_logs()
        summary = {
            "total_logs": len(records),
            "dry_run_logs": 0,
            "real_run_logs": 0,
            "success_accepted_logs": 0,
            "failed_rejected_logs": 0,
            "logs_with_result_id": 0,
        }
        success_statuses = {"accepted", "skipped"}
        for record in records:
            if record.dry_run:
                summary["dry_run_logs"] += 1
            else:
                summary["real_run_logs"] += 1
            if record.outcome_status in success_statuses:
                summary["success_accepted_logs"] += 1
            else:
                summary["failed_rejected_logs"] += 1
            if record.result_id:
                summary["logs_with_result_id"] += 1
        return summary

    def create_task_plan(
        self,
        plan_type: str,
        title: str,
        *,
        analysis_id: str | None = None,
        analysis_profile_id: str | None = None,
        project_id: str | None = None,
        requested_by: str = "",
        parameters: dict[str, object] | None = None,
        notes: str = "",
    ) -> TaskPlanRecord:
        self._require(plan_type.strip(), "plan_type is required.")
        self._require(title.strip(), "title is required.")
        return self._store.save_plan(
            TaskPlanRecord(
                plan_id=f"tplan-{uuid4().hex[:12]}",
                title=title.strip(),
                plan_type=plan_type.strip(),
                analysis_id=analysis_id.strip() if analysis_id else None,
                analysis_profile_id=analysis_profile_id.strip() if analysis_profile_id else None,
                project_id=project_id.strip() if project_id else None,
                requested_by=requested_by.strip(),
                parameters=dict(parameters or {}),
                notes=notes.strip(),
            )
        )

    def list_task_plans(
        self,
        *,
        project_id: str | None = None,
        state: TaskPlanState | None = None,
    ) -> list[TaskPlanRecord]:
        return self._store.list_plans(project_id=project_id, state=state)

    def load_task_plan(self, plan_id: str) -> TaskPlanRecord | None:
        return self._store.get_plan(plan_id)

    def update_task_plan_state(
        self,
        plan_id: str,
        state: TaskPlanState,
    ) -> TaskPlanRecord:
        plan = self._require_plan(plan_id)
        plan.transition(state)
        return self._store.save_plan(plan)

    def materialize_task_plan(self, plan_id: str) -> TaskRecord:
        plan = self._require_plan(plan_id)
        if plan.state != TaskPlanState.READY:
            raise ValueError(
                f"Task plan must be ready to materialize: {plan.plan_id}"
            )
        return self.create_task(
            plan.plan_type,
            plan.title,
            project_id=plan.project_id,
            source_id=plan.plan_id,
            metadata={
                "source_plan_id": plan.plan_id,
                "plan_type": plan.plan_type,
                "analysis_id": plan.analysis_id,
                "analysis_profile_id": plan.analysis_profile_id,
                "project_id": plan.project_id,
                "requested_by": plan.requested_by,
                "parameters": dict(plan.parameters),
                "notes": plan.notes,
            },
        )

    def summarize_task_plans(
        self,
        plans: list[TaskPlanRecord] | None = None,
    ) -> dict[str, int]:
        records = plans if plans is not None else self.list_task_plans()
        summary = {key: 0 for key in TASK_PLAN_SUMMARY_KEYS}
        summary["total_plans"] = len(records)
        for plan in records:
            if plan.state == TaskPlanState.DRAFT:
                summary["draft_plans"] += 1
            elif plan.state == TaskPlanState.READY:
                summary["ready_plans"] += 1
            elif plan.state == TaskPlanState.DISABLED:
                summary["disabled_plans"] += 1
            elif plan.state == TaskPlanState.ARCHIVED:
                summary["archived_plans"] += 1
        return summary

    def inspect_task_plan_materialization_readiness(
        self,
        plans: list[TaskPlanRecord] | None = None,
    ) -> list[TaskPlanMaterializationDiagnostic]:
        records = plans if plans is not None else self.list_task_plans()
        return [self._task_plan_materialization_diagnostic(plan) for plan in records]

    def summarize_task_plan_materialization_readiness(
        self,
        diagnostics: list[TaskPlanMaterializationDiagnostic] | None = None,
    ) -> dict[str, int]:
        records = (
            diagnostics
            if diagnostics is not None
            else self.inspect_task_plan_materialization_readiness()
        )
        summary = {
            key: 0 for key in TASK_PLAN_MATERIALIZATION_READINESS_SUMMARY_KEYS
        }
        summary["total_plans"] = len(records)
        for diagnostic in records:
            if diagnostic.can_materialize:
                summary["materializable_plans"] += 1
            else:
                summary["blocked_plans"] += 1
            if diagnostic.reason_code == TaskPlanMaterializationReason.READY:
                summary["ready_plans"] += 1
            elif diagnostic.reason_code == TaskPlanMaterializationReason.NOT_READY:
                summary["draft_plans"] += 1
            elif diagnostic.reason_code == TaskPlanMaterializationReason.DISABLED:
                summary["disabled_plans"] += 1
            elif diagnostic.reason_code == TaskPlanMaterializationReason.ARCHIVED:
                summary["archived_plans"] += 1
            elif (
                diagnostic.reason_code
                == TaskPlanMaterializationReason.MISSING_REQUIRED_CONTEXT
            ):
                summary["missing_context_plans"] += 1
        return summary

    def build_task_execution_request(
        self,
        task_id: str,
        *,
        dry_run: bool = True,
    ) -> TaskExecutionRequest:
        task = self._require_task(task_id)
        metadata = task.metadata
        parameters = metadata.get("parameters", {})
        if not isinstance(parameters, dict):
            parameters = {}
        request = TaskExecutionRequest(
            task_id=task.task_id,
            task_type=task.task_type,
            source_plan_id=self._optional_metadata_value(
                metadata.get("source_plan_id") or task.source_id
            ),
            analysis_id=self._optional_metadata_value(metadata.get("analysis_id")),
            analysis_profile_id=self._optional_metadata_value(
                metadata.get("analysis_profile_id")
            ),
            project_id=task.project_id
            or self._optional_metadata_value(metadata.get("project_id")),
            parameters=dict(parameters),
            requested_by=str(metadata.get("requested_by", "")),
            dry_run=dry_run,
        )
        self.validate_task_execution_request(request)
        return request

    def validate_task_execution_request(
        self,
        request: TaskExecutionRequest,
    ) -> None:
        self._require(request.task_id.strip(), "task_id is required.")
        self._require(request.task_type.strip(), "task_type is required.")

    def build_rejected_execution_outcome(
        self,
        task_id: str,
        *,
        error_code: str,
        message: str,
        metadata: dict[str, object] | None = None,
    ) -> TaskExecutionOutcome:
        return TaskExecutionOutcome(
            task_id=task_id,
            accepted=False,
            status=TaskExecutionOutcomeStatus.REJECTED,
            message=message,
            error_code=error_code,
            metadata=dict(metadata or {}),
        )

    def run_task_execution_request_mock(
        self,
        request: TaskExecutionRequest,
    ) -> TaskExecutionOutcome:
        try:
            self.validate_task_execution_request(request)
        except ValueError as exc:
            return self.build_rejected_execution_outcome(
                request.task_id,
                error_code="contract_validation_failed",
                message=str(exc),
                metadata={"dry_run": request.dry_run},
            )
        if request.dry_run:
            return TaskExecutionOutcome(
                task_id=request.task_id,
                accepted=True,
                status=TaskExecutionOutcomeStatus.SKIPPED,
                message="Dry-run task execution request accepted by mock runner; no task executed.",
                metadata={"dry_run": True, "task_type": request.task_type},
            )
        return TaskExecutionOutcome(
            task_id=request.task_id,
            accepted=True,
            status=TaskExecutionOutcomeStatus.ACCEPTED,
            message="Task execution request accepted by mock runner; no task executed.",
            metadata={"dry_run": False, "task_type": request.task_type},
        )

    def execute_task_with_adapter(
        self,
        task_id: str,
        adapter_registry: object,
        *,
        dry_run: bool = True,
    ) -> TaskExecutionOutcome:
        try:
            request = self.build_task_execution_request(task_id, dry_run=dry_run)
        except ValueError as exc:
            return self.build_rejected_execution_outcome(
                task_id,
                error_code="task_request_build_failed",
                message=str(exc),
                metadata={"dry_run": dry_run},
            )

        adapter = adapter_registry.get_for_task_type(request.task_type)
        if adapter is None:
            return self.build_rejected_execution_outcome(
                task_id,
                error_code="missing_runner_adapter",
                message=(
                    "No runner adapter is registered for task type: "
                    f"{request.task_type}"
                ),
                metadata={
                    "dry_run": dry_run,
                    "task_type": request.task_type,
                },
            )
        return adapter.execute(request)

    def execute_task_with_lifecycle(
        self,
        task_id: str,
        adapter_registry: object,
        *,
        dry_run: bool = False,
    ) -> TaskExecutionOutcome:
        task = self._store.get_task(task_id)
        if task is None:
            return self.build_rejected_execution_outcome(
                task_id,
                error_code="task_not_found",
                message=f"Task does not exist: {task_id}",
                metadata={"dry_run": dry_run},
            )
        if task.state != TaskState.PENDING:
            return self.build_rejected_execution_outcome(
                task_id,
                error_code="task_not_pending",
                message=(
                    "Lifecycle runner execution requires a pending task; "
                    f"current state is {task.state.value}."
                ),
                metadata={
                    "dry_run": dry_run,
                    "task_state": task.state.value,
                    "task_state_policy": "blocked_non_pending",
                },
            )
        if dry_run:
            return self.execute_task_with_adapter(
                task_id,
                adapter_registry,
                dry_run=True,
            )

        try:
            request = self.build_task_execution_request(task_id, dry_run=False)
        except ValueError as exc:
            return self.build_rejected_execution_outcome(
                task_id,
                error_code="task_request_build_failed",
                message=str(exc),
                metadata={"dry_run": False},
            )

        adapter = adapter_registry.get_for_task_type(request.task_type)
        if adapter is None:
            return self.build_rejected_execution_outcome(
                task_id,
                error_code="missing_runner_adapter",
                message=(
                    "No runner adapter is registered for task type: "
                    f"{request.task_type}"
                ),
                metadata={
                    "dry_run": False,
                    "task_type": request.task_type,
                    "task_state_policy": "kept_pending",
                },
            )

        self.start_task(task_id, "Lifecycle runner started.")
        try:
            outcome = adapter.execute(request)
        except Exception as exc:
            self._transition(
                task_id,
                TaskState.FAILED,
                "Lifecycle runner adapter raised an exception.",
            )
            return self.build_rejected_execution_outcome(
                task_id,
                error_code="runner_adapter_exception",
                message=f"Runner adapter raised an exception: {exc}",
                metadata={
                    "dry_run": False,
                    "task_type": request.task_type,
                },
            )

        if outcome.accepted and outcome.result_id:
            self.complete_task(
                task_id,
                message="Lifecycle runner completed.",
            )
            return outcome

        self._transition(
            task_id,
            TaskState.FAILED,
            "Lifecycle runner failed.",
        )
        return outcome

    def summarize_manual_runner_wrapper_diagnostics(
        self,
        adapter_registry: object,
        *,
        task_ids: list[str] | None = None,
    ) -> dict[str, int]:
        records = task_ids if task_ids is not None else [
            task.task_id for task in self.list_tasks()
        ]
        summary = {
            key: 0 for key in MANUAL_RUNNER_WRAPPER_DIAGNOSTICS_SUMMARY_KEYS
        }
        summary["dry_run_checks"] = len(records)
        for task_id in records:
            outcome = self.execute_task_with_adapter(
                task_id,
                adapter_registry,
                dry_run=True,
            )
            if outcome.accepted:
                summary["accepted_outcomes"] += 1
            else:
                summary["rejected_outcomes"] += 1
            if outcome.error_code == "missing_runner_adapter":
                summary["missing_adapter_outcomes"] += 1
        return summary

    def summarize_lifecycle_runner_wrapper_diagnostics(
        self,
        adapter_registry: object,
        *,
        task_ids: list[str] | None = None,
    ) -> dict[str, int]:
        records = task_ids if task_ids is not None else [
            task.task_id for task in self.list_tasks()
        ]
        summary = {
            key: 0 for key in LIFECYCLE_RUNNER_WRAPPER_DIAGNOSTICS_SUMMARY_KEYS
        }
        summary["dry_run_checks"] = len(records)
        for task_id in records:
            before = self._store.get_task(task_id)
            before_state = before.state if before is not None else None
            outcome = self.execute_task_with_lifecycle(
                task_id,
                adapter_registry,
                dry_run=True,
            )
            after = self._store.get_task(task_id)
            after_state = after.state if after is not None else None
            if outcome.accepted:
                summary["accepted_outcomes"] += 1
            else:
                summary["rejected_outcomes"] += 1
            if before_state != after_state:
                summary["state_mutations"] += 1
        return summary

    def summarize_lifecycle_guard_diagnostics(self) -> dict[str, object]:
        return {
            "pending_allowed": True,
            "running_blocked": True,
            "completed_blocked": True,
            "failed_blocked": True,
            "dry_run_mutations": 0,
        }

    def summarize_real_run_preflight_diagnostics(
        self,
        adapter_registry: object,
        *,
        task_ids: list[str] | None = None,
    ) -> dict[str, int]:
        records = task_ids if task_ids is not None else [
            task.task_id for task in self.list_tasks()
        ]
        summary = {
            key: 0 for key in REAL_RUN_PREFLIGHT_DIAGNOSTICS_SUMMARY_KEYS
        }
        summary["checked_tasks"] = len(records)
        for task_id in records:
            before = self._store.get_task(task_id)
            before_state = before.state if before is not None else None
            if before is None:
                summary["blocked_tasks"] += 1
                continue

            adapter = adapter_registry.get_for_task_type(before.task_type)
            if before.state == TaskState.PENDING and adapter is not None:
                summary["eligible_tasks"] += 1
            else:
                summary["blocked_tasks"] += 1
                if adapter is None:
                    summary["adapter_missing"] += 1

            after = self._store.get_task(task_id)
            after_state = after.state if after is not None else None
            if before_state != after_state:
                summary["state_mutations"] += 1
        return summary

    def summarize_mock_runner_diagnostics(
        self,
        requests: list[TaskExecutionRequest] | None = None,
    ) -> dict[str, int]:
        records = requests if requests is not None else self._build_mock_runner_requests()
        summary = {key: 0 for key in MOCK_RUNNER_DIAGNOSTICS_SUMMARY_KEYS}
        summary["total_checks"] = len(records)
        for request in records:
            outcome = self.run_task_execution_request_mock(request)
            if outcome.accepted and request.dry_run:
                summary["accepted_dry_run_outcomes"] += 1
            if not outcome.accepted:
                summary["rejected_outcomes"] += 1
            if outcome.error_code == "contract_validation_failed":
                summary["validation_failed_outcomes"] += 1
        return summary

    def inspect_task_execution_contract_readiness(
        self,
        tasks: list[TaskRecord] | None = None,
    ) -> list[TaskExecutionContractDiagnostic]:
        records = tasks if tasks is not None else self.list_tasks()
        return [self._task_execution_contract_diagnostic(task) for task in records]

    def summarize_task_execution_contract_readiness(
        self,
        diagnostics: list[TaskExecutionContractDiagnostic] | None = None,
    ) -> dict[str, int]:
        records = (
            diagnostics
            if diagnostics is not None
            else self.inspect_task_execution_contract_readiness()
        )
        summary = {key: 0 for key in TASK_EXECUTION_CONTRACT_READINESS_SUMMARY_KEYS}
        summary["total_tasks"] = len(records)
        for diagnostic in records:
            if diagnostic.contract_valid:
                summary["ready_tasks"] += 1
            else:
                summary["blocked_tasks"] += 1
            if diagnostic.reason_code == TaskExecutionContractReason.VALIDATION_FAILED:
                summary["validation_failed_tasks"] += 1
            elif diagnostic.reason_code in (
                TaskExecutionContractReason.MISSING_TASK,
                TaskExecutionContractReason.MISSING_TASK_ID,
                TaskExecutionContractReason.MISSING_TASK_TYPE,
            ):
                summary["missing_context_tasks"] += 1
        return summary

    def list_tasks(
        self,
        *,
        project_id: str | None = None,
        state: TaskState | None = None,
    ) -> list[TaskRecord]:
        return self._store.list_tasks(project_id=project_id, state=state)

    def list_results(
        self,
        *,
        task_id: str | None = None,
        result_type: str | None = None,
    ) -> list[TaskResultRecord]:
        return self._store.list_results(task_id=task_id, result_type=result_type)

    def inspect_result_artifacts(
        self,
        *,
        task_id: str | None = None,
        result_type: str | None = None,
    ) -> list[TaskResultArtifactDiagnostic]:
        diagnostics = []
        for result in self.list_results(task_id=task_id, result_type=result_type):
            artifact_path = result.artifact_path.strip()
            if not artifact_path:
                artifact_status = TaskResultArtifactStatus.NOT_APPLICABLE
            elif Path(artifact_path).exists():
                artifact_status = TaskResultArtifactStatus.PRESENT
            else:
                artifact_status = TaskResultArtifactStatus.MISSING
            diagnostics.append(
                TaskResultArtifactDiagnostic(
                    result_id=result.result_id,
                    result_type=result.result_type,
                    state=result.state,
                    artifact_path=artifact_path,
                    artifact_status=artifact_status,
                )
            )
        return diagnostics

    def summarize_task_result_artifacts(
        self,
        diagnostics: list[TaskResultArtifactDiagnostic] | None = None,
    ) -> dict[str, int]:
        records = diagnostics if diagnostics is not None else self.inspect_result_artifacts()
        summary = {
            "total_results": len(records),
            "present_artifacts": 0,
            "missing_artifacts": 0,
            "not_applicable_artifacts": 0,
        }
        for diagnostic in records:
            if diagnostic.artifact_status == TaskResultArtifactStatus.PRESENT:
                summary["present_artifacts"] += 1
            elif diagnostic.artifact_status == TaskResultArtifactStatus.MISSING:
                summary["missing_artifacts"] += 1
            elif diagnostic.artifact_status == TaskResultArtifactStatus.NOT_APPLICABLE:
                summary["not_applicable_artifacts"] += 1
        return summary

    def summarize_profile_reporting_results(self) -> dict[str, int]:
        diagnostics = self.inspect_result_artifacts(
            result_type="profile_reporting_summary"
        )
        return self.summarize_task_result_artifacts(diagnostics)

    def preview_result_artifact(
        self,
        result_id: str,
        *,
        max_chars: int = 4000,
    ) -> ArtifactPreviewRecord:
        result = self._get_result(result_id)
        if result is None:
            return ArtifactPreviewRecord(
                artifact_path="",
                exists=False,
                preview_available=False,
                message=f"Task result does not exist: {result_id}",
                error_code="result_not_found",
            )

        artifact_path = result.artifact_path.strip()
        if not artifact_path:
            return ArtifactPreviewRecord(
                artifact_path="",
                exists=False,
                preview_available=False,
                message="Task result has no artifact path.",
                error_code="not_applicable",
            )

        path = Path(artifact_path)
        file_extension = path.suffix.lower()
        record_base = {
            "artifact_path": artifact_path,
            "file_name": path.name,
            "file_extension": file_extension,
        }
        if not path.exists():
            return ArtifactPreviewRecord(
                **record_base,
                exists=False,
                preview_available=False,
                message="Artifact file is missing.",
                error_code="missing",
            )

        size_bytes = path.stat().st_size
        if file_extension not in SUPPORTED_ARTIFACT_PREVIEW_EXTENSIONS:
            return ArtifactPreviewRecord(
                **record_base,
                exists=True,
                size_bytes=size_bytes,
                preview_available=False,
                message=f"Artifact preview is not supported for {file_extension or 'unknown'} files.",
                error_code="unsupported",
            )

        char_limit = max(max_chars, 0)
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                preview_text = handle.read(char_limit)
        except OSError as exc:
            return ArtifactPreviewRecord(
                **record_base,
                exists=True,
                size_bytes=size_bytes,
                preview_available=False,
                message=f"Artifact preview failed: {exc}",
                error_code="read_failed",
            )

        return ArtifactPreviewRecord(
            **record_base,
            exists=True,
            size_bytes=size_bytes,
            preview_available=True,
            preview_text=preview_text,
            message="Artifact preview available.",
        )

    def get_task_result_detail(self, result_id: str) -> TaskResultDetailRecord:
        result = self._get_result(result_id)
        if result is None:
            return TaskResultDetailRecord(
                result_id=result_id,
                result_type="",
                state=None,
                artifact_status=TaskResultArtifactStatus.NOT_APPLICABLE,
                message=f"Task result does not exist: {result_id}",
                error_code="result_not_found",
            )

        diagnostic = next(
            (
                item
                for item in self.inspect_result_artifacts()
                if item.result_id == result.result_id
            ),
            None,
        )
        artifact_status = (
            diagnostic.artifact_status
            if diagnostic is not None
            else TaskResultArtifactStatus.NOT_APPLICABLE
        )
        metadata = dict(result.metadata)
        source_task_id = metadata.get("source_task_id", result.task_id)
        return TaskResultDetailRecord(
            result_id=result.result_id,
            result_type=result.result_type,
            state=result.state,
            title=result.title,
            task_id=result.task_id,
            source_task_id=str(source_task_id) if source_task_id is not None else "",
            analysis_id=str(metadata.get("analysis_id", "")),
            analysis_profile_id=str(metadata.get("analysis_profile_id", "")),
            project_id=str(metadata.get("project_id", "")),
            artifact_path=result.artifact_path,
            artifact_status=artifact_status,
            summary=result.summary,
            metadata=metadata,
            created_at=result.created_at,
            updated_at=result.created_at,
            message="Task result detail available.",
        )

    def summarize_retry_tasks(
        self,
        tasks: list[TaskRecord] | None = None,
    ) -> dict[str, int]:
        records = tasks if tasks is not None else self.list_tasks()
        retry_tasks = [
            task for task in records if task.metadata.get("retry_of_task_id")
        ]
        summary = {key: 0 for key in RETRY_TASK_SUMMARY_KEYS}
        summary["total_retry_tasks"] = len(retry_tasks)
        for task in retry_tasks:
            if task.state == TaskState.PENDING:
                summary["retry_tasks_pending"] += 1
            elif task.state == TaskState.COMPLETED:
                summary["retry_tasks_completed"] += 1
            elif task.state == TaskState.FAILED:
                summary["retry_tasks_failed"] += 1
        return summary

    def _transition(self, task_id: str, state: TaskState, message: str) -> TaskRecord:
        task = self._require_task(task_id)
        task.transition(state, message)
        return self._store.save_task(task)

    def _require_task(self, task_id: str) -> TaskRecord:
        task = self._store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task does not exist: {task_id}")
        return task

    def _get_result(self, result_id: str) -> TaskResultRecord | None:
        for result in self.list_results():
            if result.result_id == result_id:
                return result
        return None

    def _require_plan(self, plan_id: str) -> TaskPlanRecord:
        plan = self._store.get_plan(plan_id)
        if plan is None:
            raise ValueError(f"Task plan does not exist: {plan_id}")
        return plan

    def _optional_metadata_value(self, value: object) -> str | None:
        if value is None:
            return None
        return str(value)

    def _build_mock_runner_requests(self) -> list[TaskExecutionRequest]:
        requests = []
        for task in self.list_tasks():
            try:
                requests.append(
                    self.build_task_execution_request(task.task_id, dry_run=True)
                )
            except ValueError:
                requests.append(
                    TaskExecutionRequest(
                        task_id=task.task_id,
                        task_type=task.task_type,
                        dry_run=True,
                    )
                )
        return requests

    def _task_execution_contract_diagnostic(
        self,
        task: TaskRecord,
    ) -> TaskExecutionContractDiagnostic:
        try:
            request = self.build_task_execution_request(task.task_id)
            self.validate_task_execution_request(request)
        except ValueError as exc:
            reason = str(exc)
            reason_code = TaskExecutionContractReason.VALIDATION_FAILED
            if "Task does not exist" in reason:
                reason_code = TaskExecutionContractReason.MISSING_TASK
            elif "task_id is required" in reason:
                reason_code = TaskExecutionContractReason.MISSING_TASK_ID
            elif "task_type is required" in reason:
                reason_code = TaskExecutionContractReason.MISSING_TASK_TYPE
            return TaskExecutionContractDiagnostic(
                task_id=task.task_id,
                task_type=task.task_type,
                can_build_request=False,
                contract_valid=False,
                reason_code=reason_code,
                reason=reason,
            )
        return TaskExecutionContractDiagnostic(
            task_id=request.task_id,
            task_type=request.task_type,
            can_build_request=True,
            contract_valid=True,
            reason_code=TaskExecutionContractReason.READY,
            reason="Task can build a dry-run execution request and passes contract validation.",
        )

    def _task_plan_materialization_diagnostic(
        self,
        plan: TaskPlanRecord,
    ) -> TaskPlanMaterializationDiagnostic:
        if not plan.plan_type.strip() or not plan.title.strip():
            return TaskPlanMaterializationDiagnostic(
                plan_id=plan.plan_id,
                plan_type=plan.plan_type,
                state=plan.state,
                can_materialize=False,
                reason_code=TaskPlanMaterializationReason.MISSING_REQUIRED_CONTEXT,
                reason="Task plan is missing required title or plan_type context.",
            )
        if plan.state == TaskPlanState.READY:
            return TaskPlanMaterializationDiagnostic(
                plan_id=plan.plan_id,
                plan_type=plan.plan_type,
                state=plan.state,
                can_materialize=True,
                reason_code=TaskPlanMaterializationReason.READY,
                reason="Task plan is ready for manual materialization.",
            )
        if plan.state == TaskPlanState.DISABLED:
            return TaskPlanMaterializationDiagnostic(
                plan_id=plan.plan_id,
                plan_type=plan.plan_type,
                state=plan.state,
                can_materialize=False,
                reason_code=TaskPlanMaterializationReason.DISABLED,
                reason="Task plan is disabled.",
            )
        if plan.state == TaskPlanState.ARCHIVED:
            return TaskPlanMaterializationDiagnostic(
                plan_id=plan.plan_id,
                plan_type=plan.plan_type,
                state=plan.state,
                can_materialize=False,
                reason_code=TaskPlanMaterializationReason.ARCHIVED,
                reason="Task plan is archived.",
            )
        return TaskPlanMaterializationDiagnostic(
            plan_id=plan.plan_id,
            plan_type=plan.plan_type,
            state=plan.state,
            can_materialize=False,
            reason_code=TaskPlanMaterializationReason.NOT_READY,
            reason="Task plan is not ready.",
        )

    def _require(self, condition: object, message: str) -> None:
        if not condition:
            raise ValueError(message)
