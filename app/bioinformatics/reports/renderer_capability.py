from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

from .renderer_runtime_policy import build_full_integrated_renderer_runtime_packaging_policy


CommandFinder = Callable[[str], str | None]
SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


def build_report_renderer_capability_snapshot(
    *,
    commands: Iterable[str] = ("pandoc", "xelatex", "wkhtmltopdf", "quarto"),
    command_finder: CommandFinder | None = None,
    runner: SubprocessRunner = subprocess.run,
) -> dict[str, Any]:
    command_names = tuple(dict.fromkeys(str(command) for command in commands if str(command)))
    capabilities = {
        command: detect_renderer_dependency(command, command_finder=command_finder, runner=runner)
        for command in command_names
    }
    return {
        "schema_version": "biomedpilot.report_renderer_capability_snapshot.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "detection_mode": "detect_first_no_install_no_download",
        "capabilities": capabilities,
        "runtime_packaging_policy": build_full_integrated_renderer_runtime_packaging_policy(),
    }


def detect_renderer_dependency(
    command: str,
    *,
    command_finder: CommandFinder | None = None,
    runner: SubprocessRunner = subprocess.run,
) -> dict[str, Any]:
    resolved = _resolve_command(command, command_finder=command_finder)
    available = bool(resolved)
    return {
        "command": command,
        "available": available,
        "path": resolved,
        "version": _command_version(resolved, runner) if available else "",
        "missing_reason": "" if available else f"{command} not found on renderer search paths",
        "packaging_impact": "external_system_binary_required_not_bundled_in_releasebuild",
        "detection_mode": "detect_first_no_install_no_download",
    }


def _resolve_command(command: str, *, command_finder: CommandFinder | None) -> str:
    if command_finder is not None:
        return command_finder(command) or ""
    search_path = _renderer_search_path()
    return shutil.which(command, path=search_path) or ""


def _renderer_search_path() -> str:
    policy = build_full_integrated_renderer_runtime_packaging_policy()
    startup = policy.get("startup_path_policy") if isinstance(policy.get("startup_path_policy"), dict) else {}
    default_paths = [str(path) for path in startup.get("default_search_paths", []) or []]
    configured = os.environ.get(str(startup.get("environment_variable") or "BIOMEDPILOT_RENDERER_SEARCH_PATHS"), "")
    parts = [part for part in configured.split(os.pathsep) if part]
    parts.extend(default_paths)
    parts.extend(part for part in os.environ.get("PATH", "").split(os.pathsep) if part)
    return os.pathsep.join(dict.fromkeys(parts))


def _command_version(command_path: str, runner: SubprocessRunner) -> str:
    if not command_path:
        return ""
    for args in ((command_path, "--version"), (command_path, "-version")):
        try:
            completed = runner(list(args), capture_output=True, text=True, timeout=8, check=False)
        except Exception:
            continue
        output = (completed.stdout or completed.stderr or "").strip().splitlines()
        if completed.returncode == 0 and output:
            return output[0][:160]
    return "unknown_version"
