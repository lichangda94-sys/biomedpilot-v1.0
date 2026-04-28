from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


REQUIRED_LOCAL_FILES = (
    "requirements.txt",
    "pyproject.toml",
    "scripts/run_smoke_tests.py",
    "scripts/check_packaging_readiness.py",
    "scripts/export_requirements.py",
    "scripts/run_task_once.py",
    "scripts/run_fake_geo_preflight.py",
    "scripts/run_real_geo_readiness_test.py",
)

RECOMMENDED_BOOTSTRAP_COMMANDS = (
    "python3 -m venv .venv",
    "source .venv/bin/activate",
    "pip install -r requirements.txt",
    "python3 scripts/run_smoke_tests.py",
    "python3 -m unittest discover -s tests",
)


@dataclass(frozen=True)
class LocalEnvironmentItem:
    path: str
    present: bool


@dataclass(frozen=True)
class LocalEnvironmentReport:
    python_version: str
    python_version_supported: bool
    required_files: tuple[LocalEnvironmentItem, ...]
    bootstrap_commands: tuple[str, ...]

    @property
    def missing_items(self) -> tuple[LocalEnvironmentItem, ...]:
        return tuple(item for item in self.required_files if not item.present)

    @property
    def is_ready(self) -> bool:
        return self.python_version_supported and not self.missing_items


def inspect_local_environment(
    root_dir: Path,
    *,
    version_info: tuple[int, int, int] | None = None,
) -> LocalEnvironmentReport:
    version = version_info or (
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
    )
    python_version = ".".join(str(part) for part in version)
    required_files = tuple(
        LocalEnvironmentItem(path=path, present=(Path(root_dir) / path).is_file())
        for path in REQUIRED_LOCAL_FILES
    )
    return LocalEnvironmentReport(
        python_version=python_version,
        python_version_supported=version >= (3, 10, 0),
        required_files=required_files,
        bootstrap_commands=RECOMMENDED_BOOTSTRAP_COMMANDS,
    )


def build_local_environment_summary(
    root_dir: Path,
    *,
    version_info: tuple[int, int, int] | None = None,
) -> list[str]:
    report = inspect_local_environment(root_dir, version_info=version_info)
    lines = [
        "Local environment readiness:",
        f"- ready: {'yes' if report.is_ready else 'no'}",
        f"- python version: {report.python_version}",
        (
            "- python version supported: "
            f"{'yes' if report.python_version_supported else 'no'}"
        ),
        "Required files:",
    ]
    lines.extend(
        f"- {item.path}: {'present' if item.present else 'missing'}"
        for item in report.required_files
    )
    lines.append("Missing items:")
    if report.missing_items:
        lines.extend(f"- {item.path}" for item in report.missing_items)
    else:
        lines.append("- none")
    lines.append("Recommended local bootstrap commands:")
    lines.extend(f"- {command}" for command in report.bootstrap_commands)
    return lines


def main() -> int:
    for line in build_local_environment_summary(Path.cwd()):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
