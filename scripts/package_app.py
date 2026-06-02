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
APP_ICON_RESOURCE_NAME = "biomedpilot_app_icon.icns"
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
    executable_name: str


def build_launcher_app(options: PackagingOptions) -> PackagingResult:
    repo_root = options.repo_root.resolve()
    _validate_repo_root(repo_root)

    app_path = options.output_dir.resolve() / f"{options.app_name}.app"
    contents_dir = app_path / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    resource_root = resources_dir / "app"
    executable_name = _launcher_executable_name(options.app_name)
    launcher_path = macos_dir / executable_name

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
    _copy_bundle_icon(repo_root, resources_dir)
    git_head = _git_head(repo_root) or "unknown"
    build_info_path = resource_root / BUILD_INFO_FILENAME
    _write_build_info(build_info_path, repo_root=repo_root, git_head=git_head)
    _write_info_plist(
        contents_dir / "Info.plist",
        app_name=options.app_name,
        executable_name=executable_name,
        git_head=git_head,
    )
    launcher_mode = _write_launcher(launcher_path, app_name=options.app_name, python_executable=options.python_executable)
    _ad_hoc_sign_app(app_path)

    return PackagingResult(
        app_path=app_path,
        launcher_path=launcher_path,
        resource_root=resource_root,
        build_info_path=build_info_path,
        mode=launcher_mode,
        python_executable=options.python_executable,
        app_version=APP_VERSION,
        git_head=git_head,
        executable_name=executable_name,
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
    print(f"executable={result.executable_name}")
    print(f"build_info={result.build_info_path}")
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


def _copy_bundle_icon(repo_root: Path, resources_dir: Path) -> None:
    source = repo_root / "assets" / "icons" / "app" / APP_ICON_RESOURCE_NAME
    if source.exists():
        shutil.copy2(source, resources_dir / APP_ICON_RESOURCE_NAME)


def _create_project_storage(storage_root: Path) -> None:
    for dirname in STORAGE_DIRS:
        target = storage_root / dirname
        target.mkdir(parents=True, exist_ok=True)
        (target / ".gitkeep").write_text("", encoding="utf-8")


def _write_build_info(path: Path, *, repo_root: Path, git_head: str) -> None:
    payload = {
        "app_name": DEFAULT_APP_NAME,
        "version": APP_VERSION,
        "bundle_version": APP_BUNDLE_VERSION,
        "channel": APP_CHANNEL,
        "launch_mode": "packaged-local-python",
        "source_root": str(repo_root),
        "git_head": git_head,
        "built_at": datetime.now(UTC).isoformat(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _launcher_executable_name(app_name: str) -> str:
    normalized = "".join(character for character in app_name if character.isalnum() or character in {"_", "-"})
    return normalized or DEFAULT_APP_NAME


def _write_info_plist(path: Path, *, app_name: str, executable_name: str, git_head: str) -> None:
    payload = {
        "CFBundleName": app_name,
        "CFBundleDisplayName": "BioMedPilot / 医研智析",
        "CFBundleIdentifier": _bundle_identifier(app_name),
        "CFBundleVersion": APP_BUNDLE_VERSION,
        "CFBundleShortVersionString": APP_BUNDLE_VERSION,
        "CFBundlePackageType": "APPL",
        "CFBundleExecutable": executable_name,
        "CFBundleIconFile": APP_ICON_RESOURCE_NAME,
        "LSMinimumSystemVersion": "12.0",
        "NSPrincipalClass": "NSApplication",
        "NSHighResolutionCapable": True,
        "BioMedPilotVersion": APP_VERSION,
        "BioMedPilotChannel": APP_CHANNEL,
        "BioMedPilotGitHead": git_head,
    }
    with path.open("wb") as handle:
        plistlib.dump(payload, handle)


def _bundle_identifier(app_name: str) -> str:
    if app_name == DEFAULT_APP_NAME:
        return "local.biomedpilot.desktop"
    suffix = []
    previous_was_separator = False
    for character in app_name.lower():
        if character.isalnum():
            suffix.append(character)
            previous_was_separator = False
        elif not previous_was_separator:
            suffix.append("-")
            previous_was_separator = True
    normalized = "".join(suffix).strip("-")
    return f"local.biomedpilot.{normalized or 'preview'}"


def _write_launcher(path: Path, *, app_name: str, python_executable: str) -> str:
    if sys.platform == "darwin" and _write_native_launcher(path, app_name=app_name, python_executable=python_executable):
        return "local-python-native-launcher"
    _write_shell_launcher(path, app_name=app_name, python_executable=python_executable)
    return "local-python-launcher"


def _write_shell_launcher(path: Path, *, app_name: str, python_executable: str) -> None:
    script = f"""#!/bin/sh
set -eu
APP_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
RESOURCE_ROOT="$APP_DIR/Resources/app"
PYTHON_BIN="${{BIOMEDPILOT_PYTHON:-{python_executable}}}"
export BIOMEDPILOT_LAUNCH_MODE="packaged-local-python"
export PYTHONDONTWRITEBYTECODE="1"
LOG_FILE="/tmp/biomedpilot_integration_preview_launch.log"

if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3 || true)"
fi

if [ -z "$PYTHON_BIN" ]; then
  echo "{app_name}: Python 3 was not found. Set BIOMEDPILOT_PYTHON to a Python with PySide6 installed." >&2
  exit 127
fi

cd "$RESOURCE_ROOT"
case " $* " in
  *" --smoke-test "*)
    exec "$PYTHON_BIN" -m app.main "$@"
    ;;
  *)
    {{
      echo "started_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
      echo "python=$PYTHON_BIN"
      echo "resource_root=$RESOURCE_ROOT"
      echo "args=$*"
    }} > "$LOG_FILE"
    exec "$PYTHON_BIN" -m app.main "$@" >> "$LOG_FILE" 2>&1
    ;;
esac
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def _write_native_launcher(path: Path, *, app_name: str, python_executable: str) -> bool:
    clang = shutil.which("clang")
    if not clang:
        return False
    try:
        flags = _python_embed_flags(python_executable)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return False

    source_path = path.with_suffix(".launcher.c")
    source_path.write_text(_native_launcher_source(app_name), encoding="utf-8")
    command = [
        clang,
        str(source_path),
        "-o",
        str(path),
        *flags["cflags"],
        *flags["ldflags"],
    ]
    try:
        subprocess.run(command, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError:
        source_path.unlink(missing_ok=True)
        path.unlink(missing_ok=True)
        return False
    source_path.unlink(missing_ok=True)
    path.chmod(0o755)
    return True


def _python_embed_flags(python_executable: str) -> dict[str, list[str]]:
    code = """
import json
import sysconfig

include = sysconfig.get_config_var("INCLUDEPY")
libdir = sysconfig.get_config_var("LIBDIR")
libpl = sysconfig.get_config_var("LIBPL") or libdir
version = sysconfig.get_config_var("VERSION")
payload = {
    "cflags": [f"-I{include}"],
    "ldflags": [f"-L{libdir}", f"-L{libpl}", f"-lpython{version}", "-ldl", "-framework", "CoreFoundation", "-framework", "AppKit"],
}
print(json.dumps(payload))
"""
    completed = subprocess.run(
        [python_executable, "-c", code],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(completed.stdout)
    return {
        "cflags": [str(flag) for flag in payload["cflags"]],
        "ldflags": [str(flag) for flag in payload["ldflags"]],
    }


def _native_launcher_source(app_name: str) -> str:
    escaped_app_name = app_name.replace("\\", "\\\\").replace('"', '\\"')
    return f"""#include <Python.h>
#include <mach-o/dyld.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static int has_arg(int argc, char **argv, const char *target) {{
    for (int index = 1; index < argc; index++) {{
        if (strcmp(argv[index], target) == 0) {{
            return 1;
        }}
    }}
    return 0;
}}

static void parent_dir(char *path) {{
    char *slash = strrchr(path, '/');
    if (slash != NULL) {{
        *slash = '\\0';
    }}
}}

static int executable_path(char *buffer, size_t buffer_size) {{
    uint32_t size = (uint32_t)buffer_size;
    if (_NSGetExecutablePath(buffer, &size) != 0) {{
        return 0;
    }}
    char resolved[PATH_MAX];
    if (realpath(buffer, resolved) == NULL) {{
        return 0;
    }}
    snprintf(buffer, buffer_size, "%s", resolved);
    return 1;
}}

static void write_launch_header(const char *resource_root, int argc, char **argv) {{
    FILE *log_file = freopen("/tmp/biomedpilot_integration_preview_launch.log", "w", stdout);
    if (log_file != NULL) {{
        freopen("/tmp/biomedpilot_integration_preview_launch.log", "a", stderr);
    }}
    time_t now = time(NULL);
    struct tm *utc = gmtime(&now);
    char stamp[32] = "";
    if (utc != NULL) {{
        strftime(stamp, sizeof(stamp), "%Y-%m-%dT%H:%M:%SZ", utc);
    }}
    printf("started_at=%s\\n", stamp);
    printf("launcher=native-embedded-python\\n");
    printf("app={escaped_app_name}\\n");
    printf("resource_root=%s\\n", resource_root);
    printf("args=");
    for (int index = 1; index < argc; index++) {{
        printf("%s%s", index == 1 ? "" : " ", argv[index]);
    }}
    printf("\\n");
    fflush(stdout);
}}

int main(int argc, char **argv) {{
    char executable[PATH_MAX];
    if (!executable_path(executable, sizeof(executable))) {{
        fprintf(stderr, "{escaped_app_name}: unable to resolve executable path.\\n");
        return 126;
    }}

    char contents_dir[PATH_MAX];
    snprintf(contents_dir, sizeof(contents_dir), "%s", executable);
    parent_dir(contents_dir);
    parent_dir(contents_dir);

    char resource_root[PATH_MAX];
    snprintf(resource_root, sizeof(resource_root), "%s/Resources/app", contents_dir);
    if (chdir(resource_root) != 0) {{
        fprintf(stderr, "{escaped_app_name}: unable to enter resource root: %s\\n", resource_root);
        return 126;
    }}

    setenv("BIOMEDPILOT_LAUNCH_MODE", "packaged-local-python", 1);
    setenv("PYTHONDONTWRITEBYTECODE", "1", 1);
    const char *old_pythonpath = getenv("PYTHONPATH");
    char pythonpath[PATH_MAX * 2];
    if (old_pythonpath != NULL && strlen(old_pythonpath) > 0) {{
        snprintf(pythonpath, sizeof(pythonpath), "%s:%s", resource_root, old_pythonpath);
    }} else {{
        snprintf(pythonpath, sizeof(pythonpath), "%s", resource_root);
    }}
    setenv("PYTHONPATH", pythonpath, 1);

    if (!has_arg(argc, argv, "--smoke-test")) {{
        write_launch_header(resource_root, argc, argv);
    }}

    int embedded_argc = argc + 2;
    char **embedded_argv = calloc((size_t)embedded_argc + 1, sizeof(char *));
    if (embedded_argv == NULL) {{
        fprintf(stderr, "{escaped_app_name}: unable to allocate Python argv.\\n");
        return 125;
    }}
    embedded_argv[0] = argv[0];
    embedded_argv[1] = "-m";
    embedded_argv[2] = "app.main";
    for (int index = 1; index < argc; index++) {{
        embedded_argv[index + 2] = argv[index];
    }}

    int result = Py_BytesMain(embedded_argc, embedded_argv);
    free(embedded_argv);
    return result;
}}
"""


def _ad_hoc_sign_app(app_path: Path) -> None:
    if sys.platform != "darwin" or shutil.which("codesign") is None:
        return
    subprocess.run(
        ["codesign", "--force", "--sign", "-", "--timestamp=none", str(app_path)],
        check=True,
        text=True,
        capture_output=True,
    )


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
