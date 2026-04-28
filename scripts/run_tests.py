from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import os


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    subprocess.run(command, cwd=REPO_ROOT, env=env, check=True)


def main() -> int:
    run([sys.executable, "-m", "pytest", "-q"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
