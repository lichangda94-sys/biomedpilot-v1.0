from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .registry import REPO_ROOT


STANDARD_R_RUNNER = REPO_ROOT / "analysis" / "runners" / "run_module.R"


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
