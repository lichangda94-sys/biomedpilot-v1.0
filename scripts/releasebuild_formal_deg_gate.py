from __future__ import annotations

import argparse
import json
import os
import plistlib
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APP = REPO_ROOT / "dist" / "BioMedPilot.app"
CONTROLLED_APP = REPO_ROOT / "dist" / "deg-runtime-validation" / "BioMedPilot.app"
DEFAULT_RUNTIME_JSON = Path("/tmp/biomedpilot_releasebuild_formal_deg_runtime_packaged.json")
CONTROLLED_RUNTIME_JSON = Path("/tmp/biomedpilot_releasebuild_formal_deg_runtime_controlled_packaged.json")
DEFAULT_CONTROLLED_PYTHON = (
    REPO_ROOT.parent / "Bioinformatics" / ".venv-b9-3b" / "bin" / "python"
)


def _run(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(command))
    merged_env = os.environ.copy()
    merged_env.setdefault("QT_QPA_PLATFORM", "offscreen")
    if env:
        merged_env.update(env)
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=merged_env,
        check=True,
        text=True,
        capture_output=True,
    )


def _run_passthrough(command: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command))
    merged_env = os.environ.copy()
    merged_env.setdefault("QT_QPA_PLATFORM", "offscreen")
    if env:
        merged_env.update(env)
    subprocess.run(command, cwd=REPO_ROOT, env=merged_env, check=True)


def _load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} did not contain a JSON object.")
    return payload


def _bundle_executable(app_path: Path) -> str:
    info_path = app_path / "Contents" / "Info.plist"
    with info_path.open("rb") as handle:
        info = plistlib.load(handle)
    executable = str(info.get("CFBundleExecutable", ""))
    if not executable:
        raise RuntimeError(f"{info_path} does not declare CFBundleExecutable.")
    return executable


def _assert_runtime_status(path: Path, *, expected_status: str) -> dict[str, object]:
    payload = _load_json(path)
    status = payload.get("status")
    if status != expected_status:
        raise RuntimeError(f"{path} status={status!r}, expected {expected_status!r}.")
    return payload


def run_gate(controlled_python: Path, *, skip_full_tests: bool = False) -> dict[str, object]:
    if not controlled_python.exists():
        raise FileNotFoundError(f"Controlled DEG Python runtime not found: {controlled_python}")

    started_at = datetime.now(UTC).isoformat(timespec="seconds")
    results: dict[str, object] = {
        "schema_version": "biomedpilot.releasebuild.formal_deg_gate.v1",
        "started_at": started_at,
        "repo_root": str(REPO_ROOT),
        "controlled_python": str(controlled_python),
        "steps": [],
    }

    steps = results["steps"]
    assert isinstance(steps, list)

    if not skip_full_tests:
        _run_passthrough([sys.executable, "scripts/run_tests.py"])
        steps.append({"name": "scripts/run_tests.py", "status": "passed"})

    source_smoke = _run([sys.executable, "-m", "app.main", "--smoke-test"])
    steps.append({"name": "source_smoke", "status": "passed", "stdout": source_smoke.stdout})

    package_smoke = _run([sys.executable, "scripts/package_app.py", "--smoke-test"])
    steps.append({"name": "package_smoke", "status": "passed", "stdout": package_smoke.stdout})

    _run(["open", "-W", "-n", str(DEFAULT_APP), "--args", "--smoke-test"])
    steps.append({"name": "open_w_smoke", "status": "passed", "app": str(DEFAULT_APP)})

    _run(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(DEFAULT_APP)])
    steps.append({"name": "codesign_default_package", "status": "passed", "app": str(DEFAULT_APP)})

    executable = _bundle_executable(DEFAULT_APP)
    if executable != "BioMedPilot":
        raise RuntimeError(f"Expected CFBundleExecutable=BioMedPilot, got {executable!r}.")
    _run([str(DEFAULT_APP / "Contents" / "MacOS" / executable), "-psn_0_12345", "--smoke-test"])
    steps.append({"name": "psn_smoke", "status": "passed", "executable": executable})

    DEFAULT_RUNTIME_JSON.unlink(missing_ok=True)
    _run(
        [
            "open",
            "-W",
            "-n",
            str(DEFAULT_APP),
            "--args",
            "--bio-formal-deg-runtime-check",
            "--bio-formal-deg-runtime-check-output",
            str(DEFAULT_RUNTIME_JSON),
        ]
    )
    default_runtime = _assert_runtime_status(DEFAULT_RUNTIME_JSON, expected_status="blocked_missing_dependency")
    steps.append(
        {
            "name": "default_gui_formal_deg_runtime_check",
            "status": "blocked_missing_dependency",
            "missing_packages": default_runtime.get("dependency_snapshot", {}).get("missing_packages", []),
            "output": str(DEFAULT_RUNTIME_JSON),
        }
    )

    controlled_package = _run(
        [
            sys.executable,
            "scripts/package_app.py",
            "--python",
            str(controlled_python),
            "--output-dir",
            "dist/deg-runtime-validation",
            "--smoke-test",
        ]
    )
    steps.append({"name": "controlled_package_smoke", "status": "passed", "stdout": controlled_package.stdout})

    _run(["open", "-W", "-n", str(CONTROLLED_APP), "--args", "--smoke-test"])
    steps.append({"name": "controlled_open_w_smoke", "status": "passed", "app": str(CONTROLLED_APP)})

    _run(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(CONTROLLED_APP)])
    steps.append({"name": "codesign_controlled_package", "status": "passed", "app": str(CONTROLLED_APP)})

    CONTROLLED_RUNTIME_JSON.unlink(missing_ok=True)
    _run(
        [
            "open",
            "-W",
            "-n",
            str(CONTROLLED_APP),
            "--args",
            "--bio-formal-deg-runtime-check",
            "--bio-formal-deg-runtime-check-output",
            str(CONTROLLED_RUNTIME_JSON),
        ]
    )
    controlled_runtime = _assert_runtime_status(CONTROLLED_RUNTIME_JSON, expected_status="passed")
    fixture = controlled_runtime.get("fixture_result", {})
    if not isinstance(fixture, dict) or fixture.get("status") != "passed":
        raise RuntimeError("Controlled DEG fixture did not pass.")
    steps.append(
        {
            "name": "controlled_deg_runtime_check",
            "status": "passed",
            "dependency_status": controlled_runtime.get("dependency_snapshot", {}).get("status"),
            "fixture_status": fixture.get("status"),
            "output": str(CONTROLLED_RUNTIME_JSON),
        }
    )

    results["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    results["status"] = "passed"
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ReleaseBuild formal DEG internal-test release gate.")
    parser.add_argument("--controlled-python", default=str(DEFAULT_CONTROLLED_PYTHON))
    parser.add_argument("--skip-full-tests", action="store_true", help="Skip scripts/run_tests.py for quick local repeats.")
    parser.add_argument("--json-output", default="")
    args = parser.parse_args(argv)

    results = run_gate(Path(args.controlled_python), skip_full_tests=args.skip_full_tests)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
