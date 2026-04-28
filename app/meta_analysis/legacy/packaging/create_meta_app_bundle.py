from __future__ import annotations

import os
import plistlib
import shutil
import stat
from pathlib import Path


APP_NAME = "BioMedPilot Meta"
BUNDLE_ID = "com.biomedpilot.meta"
EXECUTABLE_NAME = "BioMedPilotMeta"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    dist_dir = repo_root / "dist"
    app_dir = dist_dir / f"{APP_NAME}.app"
    contents_dir = app_dir / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"

    if app_dir.exists():
        shutil.rmtree(app_dir)
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)

    icon_name = _copy_icon(repo_root, resources_dir)
    _write_info_plist(contents_dir / "Info.plist", icon_name)
    executable = macos_dir / EXECUTABLE_NAME
    executable.write_text(_launcher_script(), encoding="utf-8")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"Created {app_dir}")
    print("Launch it from Finder, or run:")
    print(f"  open {app_dir}")
    return 0


def _copy_icon(repo_root: Path, resources_dir: Path) -> str | None:
    icon_path = repo_root / "assets" / "meta_app_icon.icns"
    if not icon_path.exists():
        return None
    target = resources_dir / icon_path.name
    shutil.copy2(icon_path, target)
    return target.name


def _write_info_plist(path: Path, icon_name: str | None) -> None:
    plist = {
        "CFBundleDevelopmentRegion": "en",
        "CFBundleDisplayName": APP_NAME,
        "CFBundleExecutable": EXECUTABLE_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": APP_NAME,
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        "LSMinimumSystemVersion": "10.15",
        "NSHighResolutionCapable": True,
    }
    if icon_name:
        plist["CFBundleIconFile"] = icon_name
    with path.open("wb") as handle:
        plistlib.dump(plist, handle, sort_keys=False)


def _launcher_script() -> str:
    return """#!/bin/zsh
set -u

APP_EXECUTABLE="${0:A}"
MACOS_DIR="${APP_EXECUTABLE:h}"
PROJECT_ROOT="${MACOS_DIR:h:h:h:h}"

cd "$PROJECT_ROOT" || {
  echo "BioMedPilot Meta could not find the project root: $PROJECT_ROOT"
  echo "This local app bundle is expected to live in dist/BioMedPilot Meta.app inside the repository."
  exit 1
}

if [[ -f ".venv/bin/activate" ]]; then
  source ".venv/bin/activate"
fi

PYTHON_BIN="${PYTHON:-python3}"
if [[ -x ".venv-meta/bin/python" ]]; then
  PYTHON_BIN=".venv-meta/bin/python"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
fi

"$PYTHON_BIN" - <<'PY'
try:
    import PySide6  # noqa: F401
except ModuleNotFoundError:
    raise SystemExit(
        "PySide6 is not installed. Install dependencies first, for example:\\n"
        "  ./.venv/bin/python -m pip install PySide6\\n"
        "Then launch BioMedPilot Meta again."
    )
PY

if [[ $? -ne 0 ]]; then
  exit 1
fi

"$PYTHON_BIN" app_meta/main.py
exit_status=$?
if [[ "$exit_status" -ne 0 ]]; then
  message="BioMedPilot Meta did not start successfully. If the error mentions the Qt platform plugin cocoa, reinstall PySide6 with: ./.venv/bin/python -m pip install --force-reinstall PySide6"
  echo "$message"
  if command -v osascript >/dev/null 2>&1; then
    osascript -e "display dialog \\"$message\\" buttons {\\"OK\\"} default button \\"OK\\" with title \\"BioMedPilot Meta\\""
  fi
fi
exit "$exit_status"
"""


if __name__ == "__main__":
    raise SystemExit(main())
