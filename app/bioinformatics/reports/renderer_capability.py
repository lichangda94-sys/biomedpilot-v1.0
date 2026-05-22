from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def build_report_renderer_capability_snapshot(
    *,
    environment: str = "",
    commands: tuple[str, ...] = DEFAULT_RENDERER_COMMANDS,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    capabilities = {command: detect_renderer_dependency(command) for command in commands}
    blockers = _snapshot_blockers(capabilities)
    snapshot = {
        "schema_version": REPORT_RENDERER_CAPABILITY_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "passed",
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
        "checks": {
            "detect_first_no_install_action": True,
            "no_renderer_invoked": True,
            "no_report_export_enabled": True,
            "snapshot_generated": True,
        },
        "blockers": blockers,
        "warnings": ["renderer_detection_only_pdf_docx_activation_remains_disabled"],
    }
    if output_path is not None:
        _write_json(Path(output_path), snapshot)
    return snapshot


def detect_renderer_dependency(command: str) -> dict[str, Any]:
    executable = shutil.which(command)
    payload = {
        "command": command,
        "capability_key": CAPABILITY_KEYS.get(command, f"renderer.{command}.available"),
        "available": bool(executable),
        "path": executable or "",
        "version": "",
        "missing_reason": "" if executable else f"{command}_not_found_on_path",
        "packaging_impact": PACKAGING_IMPACT.get(command, "external_renderer_binary_not_bundled"),
    }
    if executable:
        payload["version"] = renderer_dependency_version(executable)
    return payload


def renderer_dependency_version(executable: str) -> str:
    try:
        completed = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except Exception:
        return "version_unavailable"
    text = (completed.stdout or completed.stderr or "").splitlines()
    return text[0].strip() if text else "version_unavailable"


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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
