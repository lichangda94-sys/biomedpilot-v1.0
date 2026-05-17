from __future__ import annotations

import os
import json
import plistlib
import shutil
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
    if shutil.which("codesign"):
        assert result.signing_status == "ad_hoc_signed"
    assert result.app_version == "0.1.0-internal-beta"
    assert result.app_path.exists()
    assert result.launcher_path.exists()
    assert result.build_info_path.exists()
    assert os.access(result.launcher_path, os.X_OK)
    assert (result.resource_root / "app" / "main.py").exists()
    assert (result.resource_root / "config" / "bioinformatics" / "analysis_defaults.yaml").exists()
    assert (result.resource_root / "reporting" / "bioinformatics_standard_report.py").exists()
    assert (result.resource_root / "project_storage" / "projects" / ".gitkeep").exists()
    assert not (result.resource_root / ".git").exists()

    build_info = json.loads(result.build_info_path.read_text(encoding="utf-8"))
    assert build_info["version"] == "0.1.0-internal-beta"
    assert build_info["launch_mode"] == "packaged-local-python"

    with (result.app_path / "Contents" / "Info.plist").open("rb") as handle:
        info = plistlib.load(handle)
    assert info["CFBundleExecutable"] == "BioMedPilotTest"
    assert info["CFBundleName"] == "BioMedPilotTest"
    assert info["BioMedPilotVersion"] == "0.1.0-internal-beta"


def test_integration_preview_package_uses_stable_launcher_name(tmp_path) -> None:
    result = build_launcher_app(
        PackagingOptions(
            repo_root=REPO_ROOT,
            output_dir=tmp_path,
            app_name="BioMedPilot Integration Preview",
            executable_name="BioMedPilotIntegrationPreview",
            display_name="BioMedPilot Integration Preview / 医研智析",
            python_executable=sys.executable,
        )
    )

    assert result.app_path.name == "BioMedPilot Integration Preview.app"
    assert result.executable_name == "BioMedPilotIntegrationPreview"
    assert result.launcher_path.name == "BioMedPilotIntegrationPreview"
    assert result.launcher_path.exists()

    build_info = json.loads(result.build_info_path.read_text(encoding="utf-8"))
    assert build_info["app_name"] == "BioMedPilot Integration Preview"
    assert build_info["display_name"] == "BioMedPilot Integration Preview / 医研智析"
    assert build_info["executable_name"] == "BioMedPilotIntegrationPreview"

    with (result.app_path / "Contents" / "Info.plist").open("rb") as handle:
        info = plistlib.load(handle)
    assert info["CFBundleName"] == "BioMedPilot Integration Preview"
    assert info["CFBundleDisplayName"] == "BioMedPilot Integration Preview / 医研智析"
    assert info["CFBundleExecutable"] == "BioMedPilotIntegrationPreview"


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
    assert "app_version=0.1.0-internal-beta" in completed.stdout
    assert "launch_mode=packaged-local-python" in completed.stdout
    assert "bioinformatics_features=5" in completed.stdout
    if shutil.which("codesign"):
        subprocess.run(["codesign", "--verify", "--deep", "--strict", str(result.app_path)], check=True)


def test_packaged_launcher_ignores_launchservices_process_serial_number(tmp_path) -> None:
    result = build_launcher_app(
        PackagingOptions(
            repo_root=REPO_ROOT,
            output_dir=tmp_path,
            app_name="BioMedPilotLaunchServices",
            python_executable=sys.executable,
        )
    )
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    completed = subprocess.run(
        [str(result.launcher_path), "-psn_0_12345", "--smoke-test"],
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "launch_mode=packaged-local-python" in completed.stdout
