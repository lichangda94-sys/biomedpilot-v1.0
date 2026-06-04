from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

from .registry import REPO_ROOT


STANDARD_R_RUNNER = REPO_ROOT / "analysis" / "runners" / "run_module.R"
SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


def run_standard_r_worker(
    input_json: str | Path,
    output_dir: str | Path,
    mode: str,
    *,
    rscript_path: str | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Invoke the standard R analysis worker boundary.

    This helper is intentionally narrow: it only executes the repository-owned
    standard runner with an already materialized input manifest. It does not
    install packages, download resources, or inspect module-specific R outputs.
    """

    input_path = Path(input_json).expanduser().resolve()
    package_dir = Path(output_dir).expanduser().resolve()
    rscript = rscript_path or shutil.which("Rscript")
    if not rscript:
        return {
            "schema_version": "biomedpilot.analysis.r_worker_invocation.v1",
            "status": "blocked",
            "returncode": None,
            "command": [],
            "stdout": "",
            "stderr": "",
            "blockers": ["rscript_not_available"],
        }
    command = [rscript, str(STANDARD_R_RUNNER), str(input_path), str(package_dir), mode]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "schema_version": "biomedpilot.analysis.r_worker_invocation.v1",
            "status": "blocked",
            "returncode": None,
            "command": command,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "blockers": ["standard_r_worker_timeout"],
        }

    worker_blockers = _read_worker_blockers(package_dir / "result.json")
    status = "passed" if completed.returncode == 0 else "blocked"
    blockers = worker_blockers or ([] if completed.returncode == 0 else [f"standard_r_worker_failed:returncode={completed.returncode}"])
    return {
        "schema_version": "biomedpilot.analysis.r_worker_invocation.v1",
        "status": status,
        "returncode": completed.returncode,
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "blockers": blockers,
    }


def run_external_r_command(
    command: list[str],
    *,
    owner: str,
    timeout_seconds: int,
    failure_blocker: str,
    runner: SubprocessRunner = subprocess.run,
) -> dict[str, Any]:
    """Run an external R command through the shared analysis runtime boundary.

    This is a transition helper for controlled adapters that still build
    module-specific R scripts. It centralizes subprocess behavior and provenance
    without installing packages, downloading resources, or claiming standard
    worker migration.
    """

    if not command:
        return {
            "schema_version": "biomedpilot.analysis.external_r_command_invocation.v1",
            "status": "blocked",
            "owner": owner,
            "returncode": None,
            "command": [],
            "stdout": "",
            "stderr": "",
            "blockers": [f"{failure_blocker}:empty_command"],
            "worker_boundary": {
                "boundary_type": "analysis_runtime_external_r_command",
                "standard_worker_entrypoint": "not_used",
                "subprocess_owner": owner,
                "migration_status": "shared_subprocess_boundary_not_isolated_standard_worker",
                "task_system_invocation": "not_yet_migrated",
            },
        }
    try:
        completed = runner(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "schema_version": "biomedpilot.analysis.external_r_command_invocation.v1",
            "status": "blocked",
            "owner": owner,
            "returncode": None,
            "command": command,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "blockers": [f"{failure_blocker}:timeout"],
            "worker_boundary": {
                "boundary_type": "analysis_runtime_external_r_command",
                "standard_worker_entrypoint": "not_used",
                "subprocess_owner": owner,
                "migration_status": "shared_subprocess_boundary_not_isolated_standard_worker",
                "task_system_invocation": "not_yet_migrated",
            },
        }
    except Exception as exc:  # pragma: no cover - defensive boundary around external runtime
        return {
            "schema_version": "biomedpilot.analysis.external_r_command_invocation.v1",
            "status": "blocked",
            "owner": owner,
            "returncode": None,
            "command": command,
            "stdout": "",
            "stderr": str(exc),
            "blockers": [failure_blocker],
            "worker_boundary": {
                "boundary_type": "analysis_runtime_external_r_command",
                "standard_worker_entrypoint": "not_used",
                "subprocess_owner": owner,
                "migration_status": "shared_subprocess_boundary_not_isolated_standard_worker",
                "task_system_invocation": "not_yet_migrated",
            },
        }

    returncode = int(getattr(completed, "returncode", 1) or 0)
    return {
        "schema_version": "biomedpilot.analysis.external_r_command_invocation.v1",
        "status": "passed" if returncode == 0 else "blocked",
        "owner": owner,
        "returncode": returncode,
        "command": command,
        "stdout": str(getattr(completed, "stdout", "") or ""),
        "stderr": str(getattr(completed, "stderr", "") or ""),
        "blockers": [] if returncode == 0 else [failure_blocker],
        "worker_boundary": {
            "boundary_type": "analysis_runtime_external_r_command",
            "standard_worker_entrypoint": "not_used",
            "subprocess_owner": owner,
            "migration_status": "shared_subprocess_boundary_not_isolated_standard_worker",
            "task_system_invocation": "not_yet_migrated",
        },
    }


def _read_worker_blockers(result_json: Path) -> list[str]:
    if not result_json.is_file():
        return []
    try:
        payload = json.loads(result_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    blockers = payload.get("blockers")
    if not isinstance(blockers, list):
        return []
    return [str(item) for item in blockers]
