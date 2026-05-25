from __future__ import annotations

import os
import json
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.package_app import PackagingOptions, _copy_ignore, build_launcher_app


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
    assert result.app_version == "0.1.0-internal-beta"
    assert result.code_signed is (sys.platform == "darwin")
    if shutil.which("codesign"):
        assert result.signing_status == "ad_hoc_signed"
    assert result.app_path.exists()
    assert result.launcher_path.exists()
    assert result.build_info_path.exists()
    assert os.access(result.launcher_path, os.X_OK)
    assert (result.resource_root / "app" / "main.py").exists()
    assert (result.resource_root / "biomedpilot_ocr_worker" / "__main__.py").exists()
    assert (result.resource_root / "config" / "bioinformatics" / "analysis_defaults.yaml").exists()
    assert (result.resource_root / "reporting" / "bioinformatics_standard_report.py").exists()
    assert (result.resource_root / "project_storage" / "projects" / ".gitkeep").exists()
    assert not (result.resource_root / ".git").exists()
    medical_terms = result.resource_root / "data" / "medical_terms"
    assert (medical_terms / "mini_medical_terms_index.json").exists()
    assert (medical_terms / "zh_term_overrides.json").exists()
    assert (medical_terms / "source_metadata.json").exists()
    assert (medical_terms / "license_attribution.md").exists()
    assert (medical_terms / "reference_checklists").is_dir()
    assert not (medical_terms / "medical_terms_index.sqlite").exists()
    assert not (medical_terms / "raw").exists()

    build_info = json.loads(result.build_info_path.read_text(encoding="utf-8"))
    assert build_info["app_name"] == "BioMedPilotTest"
    assert build_info["version"] == "0.1.0-internal-beta"
    assert build_info["launch_mode"] == "packaged-local-python"
    renderer_policy = build_info["renderer_runtime_packaging_policy"]
    assert renderer_policy["policy_id"] == "b24_3_system_path_no_bundled_renderers"
    assert renderer_policy["releasebuild_policy"]["bundles_external_renderers"] is False
    assert renderer_policy["docx"]["runtime_provider"] == "user_system_pandoc_on_search_path"
    assert "~/Library/TinyTeX/bin/universal-darwin" in renderer_policy["startup_path_policy"]["user_level_search_paths"]

    with (result.app_path / "Contents" / "Info.plist").open("rb") as handle:
        info = plistlib.load(handle)
    assert info["CFBundleExecutable"] == "BioMedPilot"
    assert info["CFBundleName"] == "BioMedPilotTest"
    assert info["CFBundleDisplayName"] == "BioMedPilotTest"
    assert info["CFBundleIdentifier"] == "local.biomedpilot.biomedpilottest"
    assert info["BioMedPilotVersion"] == "0.1.0-internal-beta"
    if sys.platform == "darwin":
        subprocess.run(["codesign", "--verify", "--deep", "--strict", str(result.app_path)], check=True)


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
    assert "workspace_entries=3" in completed.stdout
    assert "bioinformatics_features=5" in completed.stdout
    assert "labtools_features=" in completed.stdout
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


def test_package_app_ignores_local_conflict_copies_and_backups(tmp_path) -> None:
    ignored = _copy_ignore(
        str(tmp_path),
        [
            "workspace.py.pre_m0_m1_20260512.bak",
            "analysis_task_runs 2.py",
            "sample 3.csv",
            "valid_module.py",
        ],
    )

    assert "workspace.py.pre_m0_m1_20260512.bak" in ignored
    assert "analysis_task_runs 2.py" in ignored
    assert "sample 3.csv" in ignored
    assert "valid_module.py" not in ignored


def test_package_app_keeps_display_name_separate_from_executable_name(tmp_path) -> None:
    result = build_launcher_app(
        PackagingOptions(
            repo_root=REPO_ROOT,
            output_dir=tmp_path,
            app_name="BioMedPilot Integration Preview",
            python_executable=sys.executable,
        )
    )

    assert result.launcher_path.name == "BioMedPilot"
    assert result.launcher_path.exists()
    launcher_text = result.launcher_path.read_text(encoding="utf-8")
    assert "export PYTHONDONTWRITEBYTECODE=\"1\"" in launcher_text
    assert "export BIOMEDPILOT_EXTERNAL_RENDERER_POLICY=\"b24_3_system_path_no_bundled_renderers\"" in launcher_text
    assert "${HOME}/Library/TinyTeX/bin/universal-darwin" in launcher_text
    assert "export BIOMEDPILOT_RENDERER_SEARCH_PATHS=\"$RENDERER_SEARCH_PATHS\"" in launcher_text
    assert "export PATH=\"$RENDERER_SEARCH_PATHS${PATH:+:$PATH}\"" in launcher_text
    assert "PYTHON_ARCH=\"arm64\"" in launcher_text
    assert "exec arch -arm64 \"$PYTHON_BIN\" -m app.main \"$@\"" in launcher_text

    with (result.app_path / "Contents" / "Info.plist").open("rb") as handle:
        info = plistlib.load(handle)
    assert info["CFBundleExecutable"] == "BioMedPilot"
    assert info["CFBundleName"] == "BioMedPilot Integration Preview"
    assert info["CFBundleDisplayName"] == "BioMedPilot Integration Preview"
    assert info["CFBundleIdentifier"] == "local.biomedpilot.integration-preview"


def test_package_app_can_record_source_git_head(tmp_path) -> None:
    result = build_launcher_app(
        PackagingOptions(
            repo_root=REPO_ROOT,
            output_dir=tmp_path,
            app_name="BioMedPilot MainLine Preview",
            python_executable=sys.executable,
            package_git_head="83749d1",
        )
    )

    build_info = json.loads(result.build_info_path.read_text(encoding="utf-8"))
    assert result.git_head == "83749d1"
    assert build_info["git_head"] == "83749d1"

    with (result.app_path / "Contents" / "Info.plist").open("rb") as handle:
        info = plistlib.load(handle)
    assert info["BioMedPilotGitHead"] == "83749d1"
