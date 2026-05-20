from __future__ import annotations

import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path

from app.version import APP_CHANNEL, APP_VERSION
from scripts.package_app import PackagingOptions, build_launcher_app


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_versioned_packaged_entry_smoke_reports_metadata(tmp_path: Path) -> None:
    result = build_launcher_app(
        PackagingOptions(
            repo_root=REPO_ROOT,
            output_dir=tmp_path,
            app_name="BioMedPilotAcceptance",
            python_executable=sys.executable,
        )
    )

    build_info = json.loads(result.build_info_path.read_text(encoding="utf-8"))
    assert build_info["version"] == APP_VERSION
    assert build_info["channel"] == APP_CHANNEL
    assert build_info["launch_mode"] == "packaged-local-python"
    assert build_info["git_head"]

    with (result.app_path / "Contents" / "Info.plist").open("rb") as handle:
        info = plistlib.load(handle)
    assert info["BioMedPilotVersion"] == APP_VERSION
    assert info["BioMedPilotChannel"] == APP_CHANNEL
    assert info["BioMedPilotGitHead"] == build_info["git_head"]

    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    completed = subprocess.run(
        [str(result.launcher_path), "--smoke-test"],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )

    assert f"app_version={APP_VERSION}" in completed.stdout
    assert "launch_mode=packaged-local-python" in completed.stdout
    assert f"git_head={build_info['git_head']}" in completed.stdout
    assert f"app_root={result.resource_root}" in completed.stdout

    launchservices_completed = subprocess.run(
        [str(result.launcher_path), "--smoke-test", "-psn_0_12345"],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert f"app_version={APP_VERSION}" in launchservices_completed.stdout
