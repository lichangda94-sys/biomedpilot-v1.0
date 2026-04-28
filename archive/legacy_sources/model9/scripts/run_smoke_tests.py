from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from extraction.rule_store import (
    format_rule_bundle_diagnostics_summary,
    inspect_rule_bundles,
)
from analysis.analysis_preflight import (
    build_fake_analysis_preflight_smoke_fixture,
    format_analysis_preflight_summary,
    summarize_analysis_preflight_summaries,
)
from core.task_management import (
    TaskManagementService,
    format_lifecycle_guard_diagnostics_summary,
    format_lifecycle_runner_wrapper_diagnostics_summary,
    format_manual_runner_wrapper_diagnostics_summary,
    format_mock_runner_diagnostics_summary,
    format_profile_reporting_result_summary,
    format_real_run_preflight_diagnostics_summary,
    format_retry_task_summary,
    format_task_execution_contract_readiness_summary,
    format_task_execution_log_summary,
    format_task_plan_materialization_readiness_summary,
    format_task_plan_summary,
    format_task_result_artifact_diagnostics_summary,
)
from core.task_runner_adapters import (
    REPORTING_SUMMARY_TASK_TYPE,
    RunnerAdapterRegistry,
    format_runner_adapter_registry_summary,
    format_reporting_runner_dry_run_summary,
    summarize_reporting_runner_dry_run,
)


def build_smoke_summary(root_dir: Path) -> list[str]:
    rule_diagnostics = inspect_rule_bundles(root_dir)
    task_service = TaskManagementService.from_state_dir(root_dir / "state")
    artifact_summary = task_service.summarize_task_result_artifacts()
    task_plan_summary = task_service.summarize_task_plans()
    materialization_readiness = (
        task_service.summarize_task_plan_materialization_readiness()
    )
    execution_contract_readiness = (
        task_service.summarize_task_execution_contract_readiness()
    )
    execution_log_summary = task_service.summarize_task_execution_logs()
    retry_task_summary = task_service.summarize_retry_tasks()
    mock_runner_diagnostics = task_service.summarize_mock_runner_diagnostics()
    profile_reporting_results = task_service.summarize_profile_reporting_results()
    runner_registry = RunnerAdapterRegistry()
    runner_adapter_summary = runner_registry.summarize_adapters()
    manual_runner_wrapper = (
        task_service.summarize_manual_runner_wrapper_diagnostics(runner_registry)
    )
    lifecycle_runner_wrapper = (
        task_service.summarize_lifecycle_runner_wrapper_diagnostics(runner_registry)
    )
    lifecycle_guard_diagnostics = task_service.summarize_lifecycle_guard_diagnostics()
    real_run_preflight = (
        task_service.summarize_real_run_preflight_diagnostics(runner_registry)
    )
    analysis_preflight_summary = summarize_analysis_preflight_summaries(
        build_fake_analysis_preflight_smoke_fixture()
    )
    reporting_runner_requests = [
        task_service.build_task_execution_request(task.task_id, dry_run=True)
        for task in task_service.list_tasks()
        if task.task_type == REPORTING_SUMMARY_TASK_TYPE
    ]
    reporting_runner_dry_run = summarize_reporting_runner_dry_run(
        reporting_runner_requests
    )
    return [
        "Model9 smoke checks:",
        "- package imports: ok",
        *format_rule_bundle_diagnostics_summary(rule_diagnostics),
        *format_task_result_artifact_diagnostics_summary(artifact_summary),
        *format_task_plan_summary(task_plan_summary),
        *format_task_plan_materialization_readiness_summary(
            materialization_readiness
        ),
        *format_task_execution_contract_readiness_summary(
            execution_contract_readiness
        ),
        *format_task_execution_log_summary(execution_log_summary),
        *format_retry_task_summary(retry_task_summary),
        *format_mock_runner_diagnostics_summary(mock_runner_diagnostics),
        *format_manual_runner_wrapper_diagnostics_summary(manual_runner_wrapper),
        *format_lifecycle_runner_wrapper_diagnostics_summary(
            lifecycle_runner_wrapper
        ),
        *format_lifecycle_guard_diagnostics_summary(lifecycle_guard_diagnostics),
        *format_real_run_preflight_diagnostics_summary(real_run_preflight),
        *format_analysis_preflight_summary(analysis_preflight_summary),
        *format_profile_reporting_result_summary(profile_reporting_results),
        *format_runner_adapter_registry_summary(runner_adapter_summary),
        *format_reporting_runner_dry_run_summary(reporting_runner_dry_run),
    ]


def main() -> int:
    root_dir = Path.cwd()
    for line in build_smoke_summary(root_dir):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
