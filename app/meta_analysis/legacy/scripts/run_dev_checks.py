from __future__ import annotations

import argparse
from dataclasses import dataclass
import subprocess
import sys
from typing import Callable, Sequence


DEFAULT_CHECKS: tuple[tuple[str, ...], ...] = (
    ("python3", "scripts/check_local_environment.py"),
    ("python3", "scripts/check_packaging_readiness.py"),
    ("python3", "scripts/run_task_once.py", "--help"),
    ("python3", "scripts/run_fake_geo_preflight.py"),
    ("python3", "scripts/run_real_geo_readiness_test.py", "--help"),
    ("python3", "scripts/export_requirements.py", "--check"),
    ("python3", "scripts/run_smoke_tests.py"),
    ("python3", "-m", "unittest", "discover", "-s", "tests"),
)

QUICK_CHECKS: tuple[tuple[str, ...], ...] = (
    ("python3", "scripts/check_local_environment.py"),
    ("python3", "scripts/check_packaging_readiness.py"),
    ("python3", "scripts/run_task_once.py", "--help"),
    ("python3", "scripts/run_fake_geo_preflight.py"),
    ("python3", "scripts/run_real_geo_readiness_test.py", "--help"),
    ("python3", "scripts/run_smoke_tests.py"),
)


@dataclass(frozen=True)
class DevCheckResult:
    command: tuple[str, ...]
    returncode: int

    @property
    def passed(self) -> bool:
        return self.returncode == 0


CommandRunner = Callable[[Sequence[str]], int]


def run_command(command: Sequence[str]) -> int:
    completed = subprocess.run(command, check=False)
    return completed.returncode


def select_checks(*, quick: bool) -> tuple[tuple[str, ...], ...]:
    return QUICK_CHECKS if quick else DEFAULT_CHECKS


def run_dev_checks(
    *,
    quick: bool = False,
    runner: CommandRunner = run_command,
) -> list[DevCheckResult]:
    results: list[DevCheckResult] = []
    for command in select_checks(quick=quick):
        returncode = runner(command)
        results.append(
            DevCheckResult(command=tuple(command), returncode=returncode)
        )
        if returncode != 0:
            break
    return results


def build_dev_checks_summary(results: Sequence[DevCheckResult]) -> list[str]:
    lines = ["Developer verification checks:"]
    for result in results:
        status = "pass" if result.passed else "fail"
        lines.append(f"- {' '.join(result.command)}: {status}")
    if not results:
        lines.append("- no checks configured")
    lines.append(
        f"Overall: {'pass' if all(result.passed for result in results) else 'fail'}"
    )
    return lines


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run local developer readiness and validation checks."
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only local environment, packaging readiness, and smoke checks.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    results = run_dev_checks(quick=args.quick)
    for line in build_dev_checks_summary(results):
        print(line)
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
