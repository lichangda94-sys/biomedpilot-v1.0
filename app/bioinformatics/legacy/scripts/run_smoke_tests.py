"""Run the repo-root smoke matrix for minimal GEO mainline viability."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "tests.test_repo_smoke",
    "tests.test_geo_detector",
    "tests.test_geo_workflow_integration",
    "tests.test_module4_rule_config",
    "tests.test_module4_mainline_bridge",
    "tests.test_literature_cli",
]


def run_command(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    run_command([sys.executable, "-m", "unittest", *TESTS])
    run_command([sys.executable, "geo_tool/run_geo_tool.py", "--check"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
