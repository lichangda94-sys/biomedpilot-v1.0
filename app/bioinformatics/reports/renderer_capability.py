from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .renderer_runtime_policy import build_full_integrated_renderer_runtime_packaging_policy


REPORT_RENDERER_CAPABILITY_SCHEMA_VERSION = "biomedpilot.report_renderer_capability_snapshot.v1"
DEFAULT_RENDERER_COMMANDS = ("pandoc", "xelatex", "wkhtmltopdf", "quarto")
CAPABILITY_KEYS = {
    "pandoc": "renderer.pandoc.available",
    "xelatex": "renderer.latex.available",
    "wkhtmltopdf": "renderer.wkhtmltopdf.available",
    "quarto": "renderer.quarto.available",
}
PACKAGING_IMPACT = {
    "pandoc": "external_binary_required_for_docx_and_pdf_activation_not_bundled",
    "xelatex": "external_binary_required_for_pandoc_pdf_backend_not_bundled",
    "wkhtmltopdf": "external_binary_alternative_pdf_backend_not_bundled",
    "quarto": "future_renderer_detect_only_not_enabled",
}
CommandFinder = Callable[[str], str | None]
SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


def build_report_renderer_capability_snapshot(
    *,
    environment: str = "",
    commands: tuple[str, ...] = DEFAULT_RENDERER_COMMANDS,
    output_path: str | Path | None = None,
    command_finder: CommandFinder | None = None,
    runner: SubprocessRunner | None = None,
) -> dict[str, Any]:
    capabilities = {command: detect_renderer_dependency(command, command_finder=command_finder, runner=runner) for command in commands}
    blockers = _snapshot_blockers(capabilities)
    runtime_policy = build_full_integrated_renderer_runtime_packaging_policy()
    snapshot = {
        "schema_version": REPORT_RENDERER_CAPABILITY_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "passed",
        "detection_mode": "detect_first_no_install_no_download",
        "environment": environment or _runtime_environment(),
        "python_executable": sys.executable,
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "platform": platform.platform(),
        },
        "capabilities": capabilities,
        "capability_keys": {command: CAPABILITY_KEYS.get(command, f"renderer.{command}.available") for command in commands},
        "packaging_impact": {command: PACKAGING_IMPACT.get(command, "external_renderer_binary_not_bundled") for command in commands},
        "runtime_packaging_policy": runtime_policy,
        "checks": {
            "detect_first_no_install_action": True,
            "no_renderer_invoked": True,
            "no_report_export_enabled": True,
            "snapshot_generated": True,
            "external_renderers_bundled": bool(runtime_policy.get("releasebuild_policy", {}).get("bundles_external_renderers")) if isinstance(runtime_policy.get("releasebuild_policy"), dict) else False,
        },
        "blockers": blockers,
        "warnings": ["renderer_detection_only_pdf_docx_activation_remains_disabled"],
    }
    if output_path is not None:
        _write_json(Path(output_path), snapshot)
    return snapshot


def detect_renderer_dependency(
    command: str,
    *,
    command_finder: CommandFinder | None = None,
    runner: SubprocessRunner | None = None,
) -> dict[str, Any]:
    executable = _resolve_command(command, command_finder=command_finder)
    payload = {
        "command": command,
        "capability_key": CAPABILITY_KEYS.get(command, f"renderer.{command}.available"),
        "available": bool(executable),
        "path": executable or "",
        "version": "",
        "missing_reason": "" if executable else f"{command}_not_found_on_renderer_search_paths",
        "packaging_impact": PACKAGING_IMPACT.get(command, "external_renderer_binary_not_bundled"),
        "detection_mode": "detect_first_no_install_no_download",
    }
    if executable:
        payload["version"] = renderer_dependency_version(executable, runner=runner)
    return payload


def renderer_dependency_version(executable: str, *, runner: SubprocessRunner | None = None) -> str:
    runner = runner or subprocess.run
    for args in ([executable, "--version"], [executable, "-version"]):
        try:
            completed = runner(
                args,
                check=False,
                capture_output=True,
                text=True,
                timeout=2,
            )
        except Exception:
            continue
        text = (completed.stdout or completed.stderr or "").splitlines()
        if completed.returncode == 0 and text:
            return text[0].strip()[:160]
    return "version_unavailable"


def _snapshot_blockers(capabilities: dict[str, dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    if not capabilities.get("pandoc", {}).get("available"):
        blockers.append("renderer_dependency_missing:pandoc")
    if not capabilities.get("xelatex", {}).get("available") and not capabilities.get("wkhtmltopdf", {}).get("available"):
        blockers.append("renderer_dependency_missing:xelatex_or_wkhtmltopdf")
    return blockers


def _runtime_environment() -> str:
    explicit = os.environ.get("BIOMEDPILOT_RENDERER_CHECK_ENV", "").strip()
    if explicit:
        return explicit
    executable = Path(sys.executable).as_posix()
    if ".app/Contents/" in executable:
        return "packaged_app"
    if "dist/BioMedPilot.app/Contents/Resources/app" in Path(__file__).as_posix():
        return "packaged_app_resource"
    return "source"


def _resolve_command(command: str, *, command_finder: CommandFinder | None) -> str:
    if command_finder is not None:
        return command_finder(command) or ""
    return shutil.which(command, path=_renderer_search_path()) or ""


def _renderer_search_path() -> str:
    policy = build_full_integrated_renderer_runtime_packaging_policy()
    startup = policy.get("startup_path_policy") if isinstance(policy.get("startup_path_policy"), dict) else {}
    env_name = str(startup.get("environment_variable") or "BIOMEDPILOT_RENDERER_SEARCH_PATHS")
    configured = [part for part in os.environ.get(env_name, "").split(os.pathsep) if part]
    defaults = [str(part) for part in startup.get("default_search_paths", []) or []]
    existing = [part for part in os.environ.get("PATH", "").split(os.pathsep) if part]
    return os.pathsep.join(dict.fromkeys([*configured, *defaults, *existing]))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
