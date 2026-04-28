from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
import tomllib


DEFAULT_PYPROJECT_PATH = Path("pyproject.toml")
DEFAULT_REQUIREMENTS_PATH = Path("requirements.txt")
HEADER = "# Generated from pyproject.toml by scripts/export_requirements.py"


@dataclass(frozen=True)
class RequirementsExport:
    dependencies: tuple[str, ...]
    content: str


def read_project_dependencies(pyproject_path: Path) -> tuple[str, ...]:
    if not pyproject_path.is_file():
        return ()
    with pyproject_path.open("rb") as handle:
        data = tomllib.load(handle)
    dependencies = data.get("project", {}).get("dependencies", [])
    if not isinstance(dependencies, list):
        return ()
    return tuple(item for item in dependencies if isinstance(item, str))


def build_requirements_content(
    dependencies: tuple[str, ...],
    *,
    source_name: str = "pyproject.toml",
) -> str:
    lines = [HEADER.replace("pyproject.toml", source_name)]
    if dependencies:
        lines.extend(dependencies)
    else:
        lines.append("# No project dependencies declared.")
    return "\n".join(lines) + "\n"


def export_requirements(pyproject_path: Path) -> RequirementsExport:
    dependencies = read_project_dependencies(pyproject_path)
    return RequirementsExport(
        dependencies=dependencies,
        content=build_requirements_content(
            dependencies,
            source_name=pyproject_path.name,
        ),
    )


def write_requirements(requirements_path: Path, export: RequirementsExport) -> None:
    requirements_path.write_text(export.content, encoding="utf-8")


def check_requirements(requirements_path: Path, export: RequirementsExport) -> bool:
    if not requirements_path.is_file():
        return False
    return requirements_path.read_text(encoding="utf-8") == export.content


def build_requirements_summary(
    requirements_path: Path,
    export: RequirementsExport,
    *,
    check: bool,
    in_sync: bool | None = None,
) -> list[str]:
    lines = [
        "Requirements export readiness:",
        f"- dependencies exported: {len(export.dependencies)}",
        f"- requirements file: {requirements_path}",
    ]
    if check:
        lines.append(f"- check: {'ok' if in_sync else 'out of sync'}")
    else:
        lines.append("- export: written")
    if export.dependencies:
        lines.append("Dependencies:")
        lines.extend(f"- {dependency}" for dependency in export.dependencies)
    else:
        lines.append("Dependencies:")
        lines.append("- none declared")
    return lines


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export minimal requirements.txt from pyproject.toml."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check requirements.txt is in sync without writing it.",
    )
    parser.add_argument(
        "--pyproject",
        default=str(DEFAULT_PYPROJECT_PATH),
        help="Path to pyproject.toml.",
    )
    parser.add_argument(
        "--requirements",
        default=str(DEFAULT_REQUIREMENTS_PATH),
        help="Path to requirements.txt.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    pyproject_path = Path(args.pyproject)
    requirements_path = Path(args.requirements)
    export = export_requirements(pyproject_path)
    if args.check:
        in_sync = check_requirements(requirements_path, export)
        for line in build_requirements_summary(
            requirements_path,
            export,
            check=True,
            in_sync=in_sync,
        ):
            print(line)
        return 0 if in_sync else 1

    write_requirements(requirements_path, export)
    for line in build_requirements_summary(
        requirements_path,
        export,
        check=False,
    ):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
