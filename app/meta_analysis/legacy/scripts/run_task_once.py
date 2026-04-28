from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.task_management import TaskManagementService
from core.task_models import TaskExecutionOutcome, TaskRecord
from core.task_runner_adapters import (
    ReportingSummaryRunnerAdapter,
    RunnerAdapterRegistry,
)
from reporting.service import ReportingService


def build_runner_registry(
    *,
    root_dir: Path,
    task_service: TaskManagementService,
) -> RunnerAdapterRegistry:
    registry = RunnerAdapterRegistry()
    registry.register(
        ReportingSummaryRunnerAdapter(
            reporting_service=ReportingService.from_root_dir(root_dir),
            task_service=task_service,
        )
    )
    return registry


def format_task_once_summary(
    outcome: TaskExecutionOutcome,
    *,
    dry_run: bool,
) -> list[str]:
    return [
        "Task runner outcome:",
        f"- task_id: {outcome.task_id}",
        f"- dry_run: {'true' if dry_run else 'false'}",
        f"- accepted: {'true' if outcome.accepted else 'false'}",
        f"- status: {outcome.status.value}",
        f"- message: {outcome.message}",
        f"- result_id: {outcome.result_id or ''}",
        f"- error_code: {outcome.error_code or ''}",
    ]


def find_task(
    task_service: TaskManagementService,
    task_id: str,
) -> TaskRecord | None:
    for task in task_service.list_tasks():
        if task.task_id == task_id:
            return task
    return None


def append_cli_execution_log(
    task_service: TaskManagementService,
    registry: RunnerAdapterRegistry,
    outcome: TaskExecutionOutcome,
    *,
    task: TaskRecord | None,
    dry_run: bool,
) -> None:
    task_type = task.task_type if task is not None else ""
    adapter = registry.get_for_task_type(task_type) if task_type else None
    metadata = {"source": "run_task_once"}
    task_service.append_task_execution_log(
        outcome.task_id,
        source_plan_id=(
            str(task.metadata["source_plan_id"])
            if task is not None and task.metadata.get("source_plan_id") is not None
            else None
        ),
        runner_type=adapter.runner_type if adapter is not None else "",
        task_type=task_type,
        dry_run=dry_run,
        outcome_status=outcome.status.value,
        message=outcome.message,
        error_code=outcome.error_code,
        result_id=outcome.result_id,
        metadata=metadata,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one task through the manual lifecycle runner wrapper. "
            "Defaults to dry-run and never scans for tasks."
        )
    )
    parser.add_argument(
        "--task-id",
        required=True,
        help="Task id to run exactly once.",
    )
    parser.add_argument(
        "--state-dir",
        required=True,
        help="Path to the task state directory.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="Validate and route the task without executing it. This is the default.",
    )
    mode.add_argument(
        "--real-run",
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Explicitly execute the selected task through the registered adapter.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    state_dir = Path(args.state_dir)
    task_service = TaskManagementService.from_state_dir(state_dir)
    registry = build_runner_registry(
        root_dir=state_dir.parent,
        task_service=task_service,
    )
    task = find_task(task_service, args.task_id)
    outcome = task_service.execute_task_with_lifecycle(
        args.task_id,
        registry,
        dry_run=args.dry_run,
    )
    append_cli_execution_log(
        task_service,
        registry,
        outcome,
        task=task,
        dry_run=args.dry_run,
    )
    for line in format_task_once_summary(outcome, dry_run=args.dry_run):
        print(line)
    return 0 if outcome.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
