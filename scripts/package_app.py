from __future__ import annotations

import argparse
import json
import os
import plistlib
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.version import APP_BUNDLE_VERSION, APP_CHANNEL, APP_VERSION, BUILD_INFO_FILENAME

DEFAULT_APP_NAME = "BioMedPilot"
COPY_DIRS = ("app", "assets", "config", "docs", "examples", "reporting", "scripts")
COPY_FILES = ("README.md", "pyproject.toml", "requirements.txt")
PACKAGE_RESOURCE_FILES = (
    "data/medical_terms/mini_medical_terms_index.json",
    "data/medical_terms/zh_term_overrides.json",
    "data/medical_terms/source_metadata.json",
    "data/medical_terms/license_attribution.md",
)
PACKAGE_RESOURCE_DIRS = ("data/medical_terms/reference_checklists",)
STORAGE_DIRS = ("projects", "data", "tasks", "reports", "test_feedback")
IGNORE_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
}


@dataclass(frozen=True)
class PackagingOptions:
    repo_root: Path
    output_dir: Path
    app_name: str = DEFAULT_APP_NAME
    python_executable: str = sys.executable
    clean: bool = True


@dataclass(frozen=True)
class PackagingResult:
    app_path: Path
    launcher_path: Path
    resource_root: Path
    build_info_path: Path
    mode: str
    python_executable: str
    app_version: str
    git_head: str
    code_signed: bool


def build_launcher_app(options: PackagingOptions) -> PackagingResult:
    repo_root = options.repo_root.resolve()
    _validate_repo_root(repo_root)

    app_path = options.output_dir.resolve() / f"{options.app_name}.app"
    contents_dir = app_path / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    resource_root = resources_dir / "app"
    launcher_path = macos_dir / options.app_name

    if app_path.exists() and options.clean:
        shutil.rmtree(app_path)

    macos_dir.mkdir(parents=True, exist_ok=True)
    resource_root.mkdir(parents=True, exist_ok=True)

    for dirname in COPY_DIRS:
        source = repo_root / dirname
        if source.exists():
            shutil.copytree(source, resource_root / dirname, ignore=_copy_ignore, dirs_exist_ok=True)

    for filename in COPY_FILES:
        source = repo_root / filename
        if source.exists():
            shutil.copy2(source, resource_root / filename)

    _copy_package_resources(repo_root, resource_root)
    _create_project_storage(resource_root / "project_storage")
    git_head = _git_head(repo_root) or "unknown"
    build_info_path = resource_root / BUILD_INFO_FILENAME
    _write_build_info(build_info_path, repo_root=repo_root, app_name=options.app_name, git_head=git_head)
    _write_info_plist(contents_dir / "Info.plist", app_name=options.app_name, git_head=git_head)
    _write_launcher(launcher_path, app_name=options.app_name, python_executable=options.python_executable)
    code_signed = _ad_hoc_codesign(app_path)

    return PackagingResult(
        app_path=app_path,
        launcher_path=launcher_path,
        resource_root=resource_root,
        build_info_path=build_info_path,
        mode="local-python-launcher",
        python_executable=options.python_executable,
        app_version=APP_VERSION,
        git_head=git_head,
        code_signed=code_signed,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local BioMedPilot macOS .app launcher without network downloads.")
    parser.add_argument("--output-dir", default="dist", help="Directory where the .app bundle will be written.")
    parser.add_argument("--app-name", default=DEFAULT_APP_NAME, help="Application bundle name.")
    parser.add_argument("--python", default=sys.executable, help="Python executable used by the launcher.")
    parser.add_argument("--no-clean", action="store_true", help="Do not remove an existing bundle before rebuilding.")
    parser.add_argument("--smoke-test", action="store_true", help="Run the generated app launcher with --smoke-test after packaging.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = build_launcher_app(
        PackagingOptions(
            repo_root=REPO_ROOT,
            output_dir=REPO_ROOT / args.output_dir,
            app_name=args.app_name,
            python_executable=args.python,
            clean=not args.no_clean,
        )
    )
    print(f"app_path={result.app_path}")
    print(f"app_version={result.app_version}")
    print(f"git_head={result.git_head}")
    print(f"mode={result.mode}")
    print(f"python={result.python_executable}")
    print(f"build_info={result.build_info_path}")
    print(f"code_signed={str(result.code_signed).lower()}")
    print("standalone=false")
    print("network_downloads=false")

    if args.smoke_test:
        env = os.environ.copy()
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
        subprocess.run([str(result.launcher_path), "--smoke-test"], env=env, check=True)
    return 0


def _validate_repo_root(repo_root: Path) -> None:
    required = [repo_root / "app" / "main.py", repo_root / "scripts" / "run_app.py"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"BioMedPilot project root is incomplete: {', '.join(missing)}")


def _copy_ignore(directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        path = Path(directory) / name
        if name in IGNORE_NAMES or name.endswith(".pyc"):
            ignored.add(name)
        elif path.is_dir() and name in {"dist", "build", ".git", ".venv", ".venv-meta"}:
            ignored.add(name)
    return ignored


def _copy_package_resources(repo_root: Path, resource_root: Path) -> None:
    for relative_name in PACKAGE_RESOURCE_FILES:
        source = repo_root / relative_name
        if source.exists():
            target = resource_root / relative_name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    for relative_name in PACKAGE_RESOURCE_DIRS:
        source = repo_root / relative_name
        if source.exists():
            shutil.copytree(source, resource_root / relative_name, ignore=_copy_ignore, dirs_exist_ok=True)


def _create_project_storage(storage_root: Path) -> None:
    for dirname in STORAGE_DIRS:
        target = storage_root / dirname
        target.mkdir(parents=True, exist_ok=True)
        (target / ".gitkeep").write_text("", encoding="utf-8")


def _write_build_info(path: Path, *, repo_root: Path, app_name: str, git_head: str) -> None:
    payload = {
        "app_name": app_name,
        "version": APP_VERSION,
        "bundle_version": APP_BUNDLE_VERSION,
        "channel": APP_CHANNEL,
        "launch_mode": "packaged-local-python",
        "source_root": str(repo_root),
        "git_head": git_head,
        "built_at": datetime.now(UTC).isoformat(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_info_plist(path: Path, *, app_name: str, git_head: str) -> None:
    payload = {
        "CFBundleName": app_name,
        "CFBundleDisplayName": app_name,
        "CFBundleIdentifier": "local.biomedpilot.desktop",
        "CFBundleVersion": APP_BUNDLE_VERSION,
        "CFBundleShortVersionString": APP_BUNDLE_VERSION,
        "CFBundlePackageType": "APPL",
        "CFBundleExecutable": app_name,
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
        "BioMedPilotVersion": APP_VERSION,
        "BioMedPilotChannel": APP_CHANNEL,
        "BioMedPilotGitHead": git_head,
    }
    with path.open("wb") as handle:
        plistlib.dump(payload, handle)


def _write_launcher(path: Path, *, app_name: str, python_executable: str) -> None:
    script = f"""#!/bin/sh
set -eu
APP_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
RESOURCE_ROOT="$APP_DIR/Resources/app"
PYTHON_BIN="${{BIOMEDPILOT_PYTHON:-{python_executable}}}"
export BIOMEDPILOT_LAUNCH_MODE="packaged-local-python"

if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3 || true)"
fi

if [ -z "$PYTHON_BIN" ]; then
  echo "{app_name}: Python 3 was not found. Set BIOMEDPILOT_PYTHON to a Python with PySide6 installed." >&2
  exit 127
fi

cd "$RESOURCE_ROOT"
exec "$PYTHON_BIN" -m app.main "$@"
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def _ad_hoc_codesign(app_path: Path) -> bool:
    if sys.platform != "darwin":
        return False
    if shutil.which("codesign") is None:
        return False
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app_path)], check=True)
    return True


def _git_head(repo_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return completed.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
