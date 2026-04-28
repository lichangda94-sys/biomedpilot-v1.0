from __future__ import annotations

import subprocess
import sys
from pathlib import Path


LEGACY_ROOT = Path(__file__).resolve().parents[1] / "legacy"


def geo_check_command() -> list[str]:
    return [sys.executable, str(LEGACY_ROOT / "geo_tool" / "run_geo_tool.py"), "--check"]


def run_geo_environment_check() -> subprocess.CompletedProcess[str]:
    return subprocess.run(geo_check_command(), cwd=LEGACY_ROOT, text=True, capture_output=True, check=False)
