from __future__ import annotations

import os
import json
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
    medical_terms = result.resource_root / "data" / "medical_terms"
    assert (medical_terms / "mini_medical_terms_index.json").exists()
    assert (medical_terms / "zh_term_overrides.json").exists()
    assert (medical_terms / "source_metadata.json").exists()
    assert (medical_terms / "license_attribution.md").exists()
    assert (medical_terms / "reference_checklists").is_dir()
    assert not (medical_terms / "medical_terms_index.sqlite").exists()
    assert not (medical_terms / "raw").exists()

    build_info = json.loads(result.build_info_path.read_text(encoding="utf-8"))
    assert build_info["version"] == "0.1.0-internal-beta"
    assert build_info["launch_mode"] == "packaged-local-python"

    with (result.app_path / "Contents" / "Info.plist").open("rb") as handle:
        info = plistlib.load(handle)
    assert info["CFBundleExecutable"] == "BioMedPilotTest"
    assert info["CFBundleName"] == "BioMedPilotTest"
    assert info["BioMedPilotVersion"] == "0.1.0-internal-beta"


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
