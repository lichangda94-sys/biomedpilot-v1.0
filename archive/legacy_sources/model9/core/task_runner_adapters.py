from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.task_models import (
    TaskResultRecord,
    TaskExecutionOutcome,
    TaskExecutionOutcomeStatus,
    TaskExecutionRequest,
)


REPORTING_SUMMARY_TASK_TYPE = "profile_reporting_summary"
REPORTING_SUMMARY_FORMAT = "analysis_summary_csv"


@dataclass(frozen=True)
class ReportingSummaryRunnerValidation:
    valid: bool
    reason_code: str
    reason: str

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "valid": self.valid,
            "reason_code": self.reason_code,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ReportingRunnerDryRunSummary:
    supported_task_types: tuple[str, ...]
    dry_run_accepted: int
    rejected: int
    not_implemented: int

    def to_dict(self) -> dict[str, int | tuple[str, ...]]:
        return {
            "supported_task_types": self.supported_task_types,
            "dry_run_accepted": self.dry_run_accepted,
            "rejected": self.rejected,
            "not_implemented": self.not_implemented,
        }


class TaskRunnerAdapter(Protocol):
    @property
    def runner_type(self) -> str:
        raise NotImplementedError

    def supports(self, task_type: str) -> bool:
        raise NotImplementedError

    def execute(self, request: TaskExecutionRequest) -> TaskExecutionOutcome:
        raise NotImplementedError


@dataclass(frozen=True)
class RunnerAdapterSummary:
    total_adapters: int
    adapter_types: tuple[str, ...]
    supported_task_types: tuple[str, ...]
    no_op_adapters: int

    def to_dict(self) -> dict[str, int | tuple[str, ...]]:
        return {
            "total_adapters": self.total_adapters,
            "adapter_types": self.adapter_types,
            "supported_task_types": self.supported_task_types,
            "no_op_adapters": self.no_op_adapters,
        }


class NoOpRunnerAdapter:
    def __init__(
        self,
        supported_task_types: tuple[str, ...] | list[str] | None = None,
        *,
        runner_type: str = "no_op",
    ) -> None:
        self._supported_task_types = tuple(supported_task_types or ("*",))
        self._runner_type = runner_type

    @property
    def runner_type(self) -> str:
        return self._runner_type

    @property
    def supported_task_types(self) -> tuple[str, ...]:
        return self._supported_task_types

    def supports(self, task_type: str) -> bool:
        normalized = task_type.strip()
        return "*" in self._supported_task_types or normalized in self._supported_task_types

    def execute(self, request: TaskExecutionRequest) -> TaskExecutionOutcome:
        return TaskExecutionOutcome(
            task_id=request.task_id,
            accepted=False,
            status=TaskExecutionOutcomeStatus.REJECTED,
            message=(
                "No runner adapter is implemented for real task execution; "
                "request was not executed."
            ),
            error_code="not_implemented",
            metadata={
                "runner_type": self.runner_type,
                "task_type": request.task_type,
                "dry_run": request.dry_run,
            },
        )


class ReportingSummaryRunnerAdapter:
    def __init__(
        self,
        *,
        reporting_service: object | None = None,
        task_service: object | None = None,
    ) -> None:
        self._supported_task_types = (REPORTING_SUMMARY_TASK_TYPE,)
        self._reporting_service = reporting_service
        self._task_service = task_service

    @property
    def runner_type(self) -> str:
        return "reporting_summary_runner"

    @property
    def supported_task_types(self) -> tuple[str, ...]:
        return self._supported_task_types

    def supports(self, task_type: str) -> bool:
        return task_type.strip() == REPORTING_SUMMARY_TASK_TYPE

    def execute(self, request: TaskExecutionRequest) -> TaskExecutionOutcome:
        validation = validate_reporting_summary_runner_request(request)
        metadata = {
            "runner_type": self.runner_type,
            "task_type": request.task_type,
            "dry_run": request.dry_run,
            "validation_reason": validation.reason_code,
        }
        if not validation.valid:
            return self._rejected_outcome(
                request,
                message=validation.reason,
                error_code=validation.reason_code,
                metadata=metadata,
            )
        if request.dry_run:
            return TaskExecutionOutcome(
                task_id=request.task_id,
                accepted=True,
                status=TaskExecutionOutcomeStatus.SKIPPED,
                message=(
                    "Dry-run reporting summary runner request accepted; "
                    "no reporting export executed."
                ),
                metadata=metadata,
            )
        if not (request.project_id or "").strip():
            return self._rejected_outcome(
                request,
                message=(
                    "Real reporting summary runner request requires project_id."
                ),
                error_code="missing_project_id",
                metadata=metadata,
            )
        if self._reporting_service is None or self._task_service is None:
            return self._rejected_outcome(
                request,
                message=(
                    "Real reporting summary runner dependencies are not configured; "
                    "request was not executed."
                ),
                error_code="missing_runner_dependency",
                metadata=metadata,
            )
        try:
            artifact = self._reporting_service.export_analysis_summary_csv(
                request.analysis_id or ""
            )
        except Exception as exc:
            return self._rejected_outcome(
                request,
                message=f"Reporting summary export failed: {exc}",
                error_code="reporting_export_failed",
                metadata=metadata,
            )

        artifact_path = str(getattr(artifact, "path", ""))
        if not artifact_path:
            return self._rejected_outcome(
                request,
                message="Reporting summary export did not return an artifact path.",
                error_code="reporting_export_failed",
                metadata=metadata,
            )

        try:
            result = self._register_result(request, artifact_path)
        except Exception as exc:
            return self._rejected_outcome(
                request,
                message=f"Reporting summary result registration failed: {exc}",
                error_code="result_registration_failed",
                metadata=metadata,
            )
        return TaskExecutionOutcome(
            task_id=request.task_id,
            accepted=True,
            status=TaskExecutionOutcomeStatus.ACCEPTED,
            message=(
                "Reporting summary runner exported and registered a profile reporting summary result."
            ),
            result_id=result.result_id,
            metadata={**metadata, "artifact_path": artifact_path},
        )

    def _rejected_outcome(
        self,
        request: TaskExecutionRequest,
        *,
        message: str,
        error_code: str,
        metadata: dict[str, object],
    ) -> TaskExecutionOutcome:
        return TaskExecutionOutcome(
            task_id=request.task_id,
            accepted=False,
            status=TaskExecutionOutcomeStatus.REJECTED,
            message=message,
            error_code=error_code,
            metadata={
                **metadata,
                "failure_result_policy": "no_failed_result",
                "failed_result_registered": False,
            },
        )

    def _register_result(
        self,
        request: TaskExecutionRequest,
        artifact_path: str,
    ) -> TaskResultRecord:
        return self._task_service.register_profile_reporting_result(
            request.task_id,
            analysis_id=request.analysis_id or "",
            project_id=request.project_id or "",
            analysis_profile_id=request.analysis_profile_id,
            artifact_path=artifact_path,
            metadata={
                "analysis_id": request.analysis_id,
                "analysis_profile_id": request.analysis_profile_id,
                "project_id": request.project_id,
                "source_task_id": request.task_id,
                "runner_type": self.runner_type,
                "source_plan_id": request.source_plan_id,
                "requested_by": request.requested_by,
            },
        )


class RunnerAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: list[TaskRunnerAdapter] = []

    def register(self, adapter: TaskRunnerAdapter) -> None:
        self._adapters.append(adapter)

    def get_for_task_type(self, task_type: str) -> TaskRunnerAdapter | None:
        for adapter in self._adapters:
            if adapter.supports(task_type):
                return adapter
        return None

    def list_adapters(self) -> list[TaskRunnerAdapter]:
        return list(self._adapters)

    def summarize_adapters(self) -> RunnerAdapterSummary:
        adapter_types = tuple(adapter.runner_type for adapter in self._adapters)
        supported_task_types: list[str] = []
        no_op_adapters = 0
        for adapter in self._adapters:
            if isinstance(adapter, NoOpRunnerAdapter):
                no_op_adapters += 1
                supported_task_types.extend(adapter.supported_task_types)
            else:
                task_types = getattr(adapter, "supported_task_types", ())
                if isinstance(task_types, tuple):
                    supported_task_types.extend(str(item) for item in task_types)
                elif isinstance(task_types, list):
                    supported_task_types.extend(str(item) for item in task_types)
        return RunnerAdapterSummary(
            total_adapters=len(self._adapters),
            adapter_types=adapter_types,
            supported_task_types=tuple(dict.fromkeys(supported_task_types)),
            no_op_adapters=no_op_adapters,
        )


def _summary_sequence(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, tuple | list):
        return tuple(str(item) for item in value if str(item))
    return ()


def _summary_int(value: object) -> int:
    return value if isinstance(value, int) else 0


def format_runner_adapter_registry_summary(
    summary: RunnerAdapterSummary | dict[str, object] | None,
) -> list[str]:
    if isinstance(summary, RunnerAdapterSummary):
        data = summary.to_dict()
    else:
        data = summary or {}

    adapter_types = _summary_sequence(data.get("adapter_types"))
    supported_task_types = _summary_sequence(data.get("supported_task_types"))
    return [
        "Runner adapter registry:",
        f"- total adapters: {_summary_int(data.get('total_adapters'))}",
        f"- adapter types: {', '.join(adapter_types) if adapter_types else 'none'}",
        (
            "- supported task types: "
            f"{', '.join(supported_task_types) if supported_task_types else 'none'}"
        ),
        f"- no-op adapters: {_summary_int(data.get('no_op_adapters'))}",
    ]


def validate_reporting_summary_runner_request(
    request: TaskExecutionRequest,
) -> ReportingSummaryRunnerValidation:
    if not request.task_id.strip():
        return ReportingSummaryRunnerValidation(
            valid=False,
            reason_code="missing_task_id",
            reason="profile_reporting_summary runner request requires task_id",
        )
    if request.task_type != REPORTING_SUMMARY_TASK_TYPE:
        return ReportingSummaryRunnerValidation(
            valid=False,
            reason_code="unsupported_task_type",
            reason=(
                "reporting summary runner only supports profile_reporting_summary"
            ),
        )
    if not (request.analysis_id or "").strip():
        return ReportingSummaryRunnerValidation(
            valid=False,
            reason_code="missing_analysis_id",
            reason="profile_reporting_summary runner request requires analysis_id",
        )

    requested_format = str(
        request.parameters.get("format", REPORTING_SUMMARY_FORMAT)
    )
    if requested_format != REPORTING_SUMMARY_FORMAT:
        return ReportingSummaryRunnerValidation(
            valid=False,
            reason_code="unsupported_format",
            reason=(
                "profile_reporting_summary runner only supports analysis_summary_csv"
            ),
        )

    return ReportingSummaryRunnerValidation(
        valid=True,
        reason_code="ready",
        reason="profile_reporting_summary runner request is contract-ready",
    )


def summarize_reporting_runner_dry_run(
    requests: list[TaskExecutionRequest] | tuple[TaskExecutionRequest, ...] | None = None,
    adapter: ReportingSummaryRunnerAdapter | None = None,
) -> ReportingRunnerDryRunSummary:
    runner = adapter or ReportingSummaryRunnerAdapter()
    dry_run_accepted = 0
    rejected = 0
    not_implemented = 0

    for request in requests or ():
        outcome = runner.execute(request)
        if (
            outcome.accepted
            and outcome.status == TaskExecutionOutcomeStatus.SKIPPED
            and outcome.metadata.get("dry_run") is True
        ):
            dry_run_accepted += 1
        elif outcome.error_code in ("not_implemented", "missing_runner_dependency"):
            not_implemented += 1
        elif not outcome.accepted:
            rejected += 1

    return ReportingRunnerDryRunSummary(
        supported_task_types=runner.supported_task_types,
        dry_run_accepted=dry_run_accepted,
        rejected=rejected,
        not_implemented=not_implemented,
    )


def format_reporting_runner_dry_run_summary(
    summary: ReportingRunnerDryRunSummary | dict[str, object] | None,
) -> list[str]:
    if isinstance(summary, ReportingRunnerDryRunSummary):
        data = summary.to_dict()
    else:
        data = summary or {}

    supported_task_types = _summary_sequence(data.get("supported_task_types"))
    return [
        "Reporting runner dry-run:",
        (
            "- supported task types: "
            f"{', '.join(supported_task_types) if supported_task_types else 'none'}"
        ),
        f"- dry-run accepted: {_summary_int(data.get('dry_run_accepted'))}",
        f"- rejected: {_summary_int(data.get('rejected'))}",
        f"- not implemented: {_summary_int(data.get('not_implemented'))}",
    ]
