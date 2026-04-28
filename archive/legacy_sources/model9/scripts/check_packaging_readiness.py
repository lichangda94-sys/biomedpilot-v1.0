from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REQUIRED_FILES = (
    "pyproject.toml",
    "README.md",
    "scripts/run_smoke_tests.py",
    "scripts/run_task_once.py",
    "scripts/run_fake_geo_preflight.py",
    "scripts/run_real_geo_readiness_test.py",
)

REQUIRED_CORE_PACKAGE_DIRS = (
    "core",
    "app",
    "reporting",
    "analysis",
    "extraction",
)

RECOMMENDED_VALIDATION_COMMANDS = (
    "python3 scripts/run_smoke_tests.py",
    "python3 -m unittest discover -s tests",
)


@dataclass(frozen=True)
class PackagingReadinessItem:
    name: str
    path: str
    present: bool


@dataclass(frozen=True)
class PackagingReadinessReport:
    required_files: tuple[PackagingReadinessItem, ...]
    core_package_dirs: tuple[PackagingReadinessItem, ...]
    validation_commands: tuple[str, ...]

    @property
    def missing_items(self) -> tuple[PackagingReadinessItem, ...]:
        return tuple(
            item
            for item in (*self.required_files, *self.core_package_dirs)
            if not item.present
        )

    @property
    def is_ready(self) -> bool:
        return not self.missing_items


def inspect_packaging_readiness(root_dir: Path) -> PackagingReadinessReport:
    root = Path(root_dir)
    required_files = tuple(
        PackagingReadinessItem(
            name=path,
            path=path,
            present=(root / path).is_file(),
        )
        for path in REQUIRED_FILES
    )
    core_package_dirs = tuple(
        PackagingReadinessItem(
            name=path,
            path=path,
            present=(root / path).is_dir(),
        )
        for path in REQUIRED_CORE_PACKAGE_DIRS
    )
    return PackagingReadinessReport(
        required_files=required_files,
        core_package_dirs=core_package_dirs,
        validation_commands=RECOMMENDED_VALIDATION_COMMANDS,
    )


def build_packaging_readiness_summary(root_dir: Path) -> list[str]:
    report = inspect_packaging_readiness(root_dir)
    lines = [
        "Packaging/localization readiness:",
        f"- ready: {'yes' if report.is_ready else 'no'}",
        "Required files:",
    ]
    lines.extend(
        f"- {item.path}: {'present' if item.present else 'missing'}"
        for item in report.required_files
    )
    lines.append("Core package directories:")
    lines.extend(
        f"- {item.path}: {'present' if item.present else 'missing'}"
        for item in report.core_package_dirs
    )
    lines.append("Missing items:")
    if report.missing_items:
        lines.extend(f"- {item.path}" for item in report.missing_items)
    else:
        lines.append("- none")
    lines.append("Recommended validation commands:")
    lines.extend(f"- {command}" for command in report.validation_commands)
    return lines


def main() -> int:
    for line in build_packaging_readiness_summary(Path.cwd()):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
