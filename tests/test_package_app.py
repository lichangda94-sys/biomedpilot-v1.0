from __future__ import annotations

import os
import plistlib
import subprocess
import sys
from pathlib import Path

from scripts.package_app import PackagingOptions, build_launcher_app


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_package_app_builds_local_launcher_bundle(tmp_path) -> None:
    result = build_launcher_app(
        PackagingOptions(
            repo_root=REPO_ROOT,
            output_dir=tmp_path,
            app_name="BioMedPilotTest",
            python_executable=sys.executable,
        )
    )

    assert result.mode == "local-python-launcher"
    assert result.app_path.exists()
    assert result.launcher_path.exists()
    assert os.access(result.launcher_path, os.X_OK)
    assert (result.resource_root / "app" / "main.py").exists()
    assert (result.resource_root / "project_storage" / "projects" / ".gitkeep").exists()
    assert not (result.resource_root / ".git").exists()

    with (result.app_path / "Contents" / "Info.plist").open("rb") as handle:
        info = plistlib.load(handle)
    assert info["CFBundleExecutable"] == "BioMedPilotTest"
    assert info["CFBundleName"] == "BioMedPilotTest"


def test_packaged_launcher_runs_smoke_test(tmp_path) -> None:
    result = build_launcher_app(
        PackagingOptions(
            repo_root=REPO_ROOT,
            output_dir=tmp_path,
            app_name="BioMedPilotSmoke",
            python_executable=sys.executable,
        )
    )
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    completed = subprocess.run(
        [str(result.launcher_path), "--smoke-test"],
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "BioMedPilot / 医研智析" in completed.stdout
    assert "bioinformatics_features=10" in completed.stdout
