from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Callable, Sequence


KEY_DIRECTORIES = (
    "core",
    "analysis",
    "reporting",
    "extraction",
    "app",
    "scripts",
    "docs",
    "tests",
)

KEY_SCRIPTS = (
    "scripts/run_smoke_tests.py",
    "scripts/check_packaging_readiness.py",
    "scripts/export_requirements.py",
    "scripts/check_local_environment.py",
    "scripts/run_dev_checks.py",
)


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str = ""


@dataclass(frozen=True)
class PathStatus:
    path: str
    present: bool


@dataclass(frozen=True)
class ProjectStatusSnapshot:
    git_available: bool
    git_repo: bool
    branch: str
    head: str
    working_tree_clean: bool | None
    tags: tuple[str, ...]
    key_directories: tuple[PathStatus, ...]
    key_scripts: tuple[PathStatus, ...]


CommandRunner = Callable[[Sequence[str], Path], CommandResult]


def run_command(command: Sequence[str], cwd: Path) -> CommandResult:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return CommandResult(returncode=127, stdout="", stderr="git not found")
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _git(
    root_dir: Path,
    args: Sequence[str],
    runner: CommandRunner,
) -> CommandResult:
    return runner(("git", *args), root_dir)


def inspect_project_status(
    root_dir: Path,
    *,
    runner: CommandRunner = run_command,
) -> ProjectStatusSnapshot:
    root = Path(root_dir)
    inside_work_tree = _git(
        root,
        ("rev-parse", "--is-inside-work-tree"),
        runner,
    )
    git_available = inside_work_tree.returncode != 127
    git_repo = (
        inside_work_tree.returncode == 0
        and inside_work_tree.stdout.strip() == "true"
    )

    branch = "unavailable"
    head = "unavailable"
    working_tree_clean: bool | None = None
    tags: tuple[str, ...] = ()
    if git_repo:
        branch_result = _git(root, ("branch", "--show-current"), runner)
        if branch_result.returncode == 0 and branch_result.stdout.strip():
            branch = branch_result.stdout.strip()
        head_result = _git(root, ("rev-parse", "--short", "HEAD"), runner)
        if head_result.returncode == 0 and head_result.stdout.strip():
            head = head_result.stdout.strip()
        status_result = _git(root, ("status", "--short"), runner)
        if status_result.returncode == 0:
            working_tree_clean = status_result.stdout.strip() == ""
        tag_result = _git(root, ("tag", "--list", "v0.*"), runner)
        if tag_result.returncode == 0:
            tags = tuple(
                line.strip()
                for line in tag_result.stdout.splitlines()
                if line.strip()
            )

    key_directories = tuple(
        PathStatus(path=path, present=(root / path).is_dir())
        for path in KEY_DIRECTORIES
    )
    key_scripts = tuple(
        PathStatus(path=path, present=(root / path).is_file())
        for path in KEY_SCRIPTS
    )
    return ProjectStatusSnapshot(
        git_available=git_available,
        git_repo=git_repo,
        branch=branch,
        head=head,
        working_tree_clean=working_tree_clean,
        tags=tags,
        key_directories=key_directories,
        key_scripts=key_scripts,
    )


def build_project_status_summary(
    root_dir: Path,
    *,
    runner: CommandRunner = run_command,
) -> list[str]:
    snapshot = inspect_project_status(root_dir, runner=runner)
    clean_text = (
        "unknown"
        if snapshot.working_tree_clean is None
        else "yes"
        if snapshot.working_tree_clean
        else "no"
    )
    lines = [
        "Project status snapshot:",
        f"- git available: {'yes' if snapshot.git_available else 'no'}",
        f"- git repo: {'yes' if snapshot.git_repo else 'no'}",
        f"- branch: {snapshot.branch}",
        f"- head: {snapshot.head}",
        f"- working tree clean: {clean_text}",
        "v0 tags:",
    ]
    if snapshot.tags:
        lines.extend(f"- {tag}" for tag in snapshot.tags)
    else:
        lines.append("- none")
    lines.append("Key directories:")
    lines.extend(
        f"- {item.path}: {'present' if item.present else 'missing'}"
        for item in snapshot.key_directories
    )
    lines.append("Key scripts:")
    lines.extend(
        f"- {item.path}: {'present' if item.present else 'missing'}"
        for item in snapshot.key_scripts
    )
    return lines


def main() -> int:
    for line in build_project_status_summary(Path.cwd()):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
