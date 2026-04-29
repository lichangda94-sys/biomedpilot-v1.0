from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


APP_VERSION = "0.1.0-internal-beta"
APP_BUNDLE_VERSION = "0.1.0"
APP_CHANNEL = "Developer Preview / testing"
BUILD_INFO_FILENAME = "BUILD_INFO.json"


@dataclass(frozen=True)
class AppVersionSummary:
    version: str
    bundle_version: str
    channel: str
    launch_mode: str
    app_root: str
    git_head: str


def app_version_summary(app_root: Path | None = None) -> AppVersionSummary:
    root = (app_root or Path.cwd()).resolve()
    build_info = _load_build_info(root / BUILD_INFO_FILENAME)
    git_head = str(build_info.get("git_head") or _git_head(root) or "unknown")
    launch_mode = str(build_info.get("launch_mode") or os.environ.get("BIOMEDPILOT_LAUNCH_MODE") or "source")
    return AppVersionSummary(
        version=str(build_info.get("version") or APP_VERSION),
        bundle_version=str(build_info.get("bundle_version") or APP_BUNDLE_VERSION),
        channel=str(build_info.get("channel") or APP_CHANNEL),
        launch_mode=launch_mode,
        app_root=str(root),
        git_head=git_head,
    )


def _load_build_info(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _git_head(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return completed.stdout.strip()
