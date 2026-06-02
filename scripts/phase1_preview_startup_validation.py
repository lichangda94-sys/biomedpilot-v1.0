from __future__ import annotations

import json
import os
import subprocess
import sys
import plistlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from app.shell.main_window import MainWindow


SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_phase1_preview_startup"
REPORT_PATH = REPO_ROOT / "docs" / "release_validation" / "20260602_phase1_preview_startup.md"
JSON_PATH = REPO_ROOT / "docs" / "release_validation" / "20260602_phase1_preview_startup.json"
PREVIEW_APP_PATH = REPO_ROOT / "dist" / "BioMedPilot Integration Preview.app"


def main() -> int:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.resize(1600, 1000)
    window.show()
    app.processEvents()
    QTest.qWait(120)

    screenshots: list[dict[str, str]] = []
    clicks: list[dict[str, Any]] = []

    def shot(name: str) -> None:
        app.processEvents()
        QTest.qWait(80)
        path = SCREENSHOT_DIR / f"{name}.png"
        window.grab().save(str(path))
        screenshots.append({"name": name, "path": str(path), "workspace": window.current_workspace_key()})

    def click_button(button: QPushButton | None, *, scope: str, expected: str) -> None:
        if button is None:
            clicks.append(
                {
                    "scope": scope,
                    "object_name": "",
                    "text": "",
                    "enabled": False,
                    "clicked": False,
                    "expected_workspace": expected,
                    "actual_workspace": window.current_workspace_key(),
                    "result": "missing_button",
                }
            )
            return
        before = window.current_workspace_key()
        if not button.isEnabled():
            clicks.append(
                _button_entry(
                    button,
                    scope,
                    before,
                    expected,
                    actual=before,
                    clicked=False,
                    result="disabled",
                )
            )
            return
        button.click()
        app.processEvents()
        QTest.qWait(80)
        actual = window.current_workspace_key()
        result = "passed" if actual == expected else "wrong_target"
        clicks.append(_button_entry(button, scope, before, expected, actual=actual, clicked=True, result=result))

    shot("01_welcome")

    click_button(window._welcome_page.findChild(QPushButton, "loginTopIconButton"), scope="welcome_settings", expected="settings")
    shot("02_settings_from_welcome")
    window.logout()
    app.processEvents()
    QTest.qWait(80)

    click_button(window._welcome_page.findChild(QPushButton, "aboutButton"), scope="welcome_about", expected="about")
    shot("03_about_from_welcome")
    window.logout()
    app.processEvents()
    QTest.qWait(80)

    click_button(window._welcome_page.findChild(QPushButton, "primaryButton"), scope="welcome_enter", expected="dashboard")
    shot("04_home_dashboard")
    shot("05_sidebar_dashboard")

    click_button(window._dashboard_page.findChild(QPushButton, "bioModuleButton"), scope="home_bio", expected="bioinformatics")
    shot("06_bio_workspace_entry")
    window.show_dashboard()
    click_button(window._dashboard_page.findChild(QPushButton, "metaModuleButton"), scope="home_meta", expected="meta_analysis")
    shot("07_meta_workspace_entry")
    window.show_dashboard()
    click_button(window._dashboard_page.findChild(QPushButton, "labtoolsModuleButton"), scope="home_labtools", expected="labtools")
    shot("08_labtools_workspace_entry")

    for key, expected in (
        ("dashboard", "dashboard"),
        ("bioinformatics", "bioinformatics"),
        ("meta_analysis", "meta_analysis"),
        ("labtools", "labtools"),
        ("centers", "centers"),
        ("settings", "settings"),
        ("test_feedback", "test_feedback"),
        ("about", "about"),
    ):
        button = getattr(window._sidebar, "_nav_buttons", {}).get(key)
        click_button(button, scope=f"sidebar_{key}", expected=expected)
        shot(f"09_sidebar_{key}")

    disabled_without_reason = _visible_disabled_without_reason(window)
    payload = {
        "schema_version": "biomedpilot.phase1.preview_startup.v1",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "branch": _git_output("branch", "--show-current"),
        "head": _git_output("rev-parse", "HEAD"),
        "packaged_app_gate": _packaged_app_gate(),
        "screenshots": screenshots,
        "clicks": clicks,
        "summary": {
            "click_count": len(clicks),
            "passed_clicks": sum(1 for item in clicks if item["result"] == "passed"),
            "failed_clicks": [item for item in clicks if item["result"] != "passed"],
            "disabled_without_reason_count": len(disabled_without_reason),
        },
        "disabled_without_reason": disabled_without_reason,
    }
    JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(_markdown_report(payload), encoding="utf-8")
    window.close()
    app.processEvents()
    print(REPORT_PATH)
    print(JSON_PATH)
    return 0 if not payload["summary"]["failed_clicks"] else 1


def _button_entry(
    button: QPushButton,
    scope: str,
    before: str,
    expected: str,
    actual: str,
    *,
    clicked: bool,
    result: str,
) -> dict[str, Any]:
    return {
        "scope": scope,
        "object_name": button.objectName(),
        "text": button.text().replace("\n", " / "),
        "enabled": button.isEnabled(),
        "button_behavior": str(button.property("buttonBehavior") or ""),
        "disabled_reason": str(button.property("disabledReason") or ""),
        "formal_action_enabled": bool(button.property("formalActionEnabled")),
        "file_write_allowed": bool(button.property("fileWriteAllowed")),
        "clicked": clicked,
        "previous_workspace": before,
        "expected_workspace": expected,
        "actual_workspace": actual,
        "result": result,
    }


def _visible_disabled_without_reason(window: MainWindow) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for button in window.findChildren(QPushButton):
        if not button.isVisible() or button.isEnabled():
            continue
        if str(button.property("disabledReason") or ""):
            continue
        missing.append(
            {
                "object_name": button.objectName(),
                "text": button.text().replace("\n", " / "),
                "button_behavior": str(button.property("buttonBehavior") or ""),
            }
        )
    return missing


def _git_output(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return completed.stdout.strip()


def _packaged_app_gate() -> dict[str, Any]:
    gate: dict[str, Any] = {
        "app_path": str(PREVIEW_APP_PATH),
        "exists": PREVIEW_APP_PATH.exists(),
        "packaged_git_head": "",
        "cf_bundle_executable": "",
        "launcher_arch": "",
        "codesign": "not_run",
        "direct_launcher_smoke": "not_run",
        "launchservices_gui_startup_check": "not_run",
        "gui_startup_payload_path": "",
        "gui_startup_status": "",
        "gui_window_visible": None,
        "gui_window_size": {},
    }
    if not PREVIEW_APP_PATH.exists():
        return gate

    info_path = PREVIEW_APP_PATH / "Contents" / "Info.plist"
    try:
        with info_path.open("rb") as handle:
            info = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException):
        info = {}
    executable_name = str(info.get("CFBundleExecutable") or "")
    gate["packaged_git_head"] = str(info.get("BioMedPilotGitHead") or "")
    gate["cf_bundle_executable"] = executable_name
    launcher_path = PREVIEW_APP_PATH / "Contents" / "MacOS" / executable_name

    if launcher_path.exists():
        file_result = _run_command(["file", str(launcher_path)])
        gate["launcher_arch"] = file_result["stdout"].strip()
        smoke_env = os.environ.copy()
        smoke_env.setdefault("QT_QPA_PLATFORM", "offscreen")
        smoke_result = _run_command([str(launcher_path), "--smoke-test"], env=smoke_env)
        gate["direct_launcher_smoke"] = "passed" if smoke_result["returncode"] == 0 else "failed"

    codesign_result = _run_command(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(PREVIEW_APP_PATH)])
    gate["codesign"] = "valid_on_disk" if codesign_result["returncode"] == 0 else "failed"

    startup_path = Path("/tmp") / f"biomedpilot_phase1_shell_{_git_output('rev-parse', '--short', 'HEAD')}_gui_startup.json"
    open_env = os.environ.copy()
    open_env.pop("QT_QPA_PLATFORM", None)
    open_result = _run_command(
        [
            "open",
            "-W",
            "-n",
            str(PREVIEW_APP_PATH),
            "--args",
            "--gui-startup-check",
            "--gui-startup-check-output",
            str(startup_path),
        ],
        env=open_env,
        timeout=15,
    )
    gate["launchservices_gui_startup_check"] = "passed" if open_result["returncode"] == 0 else "failed"
    gate["gui_startup_payload_path"] = str(startup_path)
    if startup_path.exists():
        try:
            startup_payload = json.loads(startup_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            startup_payload = {}
        gate["gui_startup_status"] = str(startup_payload.get("status") or "")
        gate["gui_window_visible"] = startup_payload.get("window_visible")
        gate["gui_window_size"] = startup_payload.get("window_size") or {}
    return gate


def _run_command(command: list[str], *, env: dict[str, str] | None = None, timeout: int | None = None) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"returncode": 124, "stdout": "", "stderr": str(exc)}
    return {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def _markdown_report(payload: dict[str, Any]) -> str:
    package_gate = payload["packaged_app_gate"]
    lines = [
        "# Phase 1 Preview Startup Validation",
        "",
        f"- branch: `{payload['branch']}`",
        f"- head: `{payload['head']}`",
        f"- screenshot_dir: `{SCREENSHOT_DIR}`",
        f"- click_count: `{payload['summary']['click_count']}`",
        f"- passed_clicks: `{payload['summary']['passed_clicks']}`",
        f"- failed_clicks: `{len(payload['summary']['failed_clicks'])}`",
        f"- disabled_without_reason_count: `{payload['summary']['disabled_without_reason_count']}`",
        "",
        "## Packaged App Launch Gate",
        "",
        f"- app_path: `{package_gate['app_path']}`",
        f"- packaged_git_head: `{package_gate['packaged_git_head']}`",
        f"- direct_launcher_smoke: `{package_gate['direct_launcher_smoke']}`",
        f"- launchservices_gui_startup_check: `{package_gate['launchservices_gui_startup_check']}`",
        f"- gui_startup_status: `{package_gate['gui_startup_status']}`",
        f"- gui_window_visible: `{package_gate['gui_window_visible']}`",
        f"- gui_window_size: `{package_gate['gui_window_size']}`",
        f"- codesign: `{package_gate['codesign']}`",
        f"- launcher_arch: `{package_gate['launcher_arch']}`",
        f"- cf_bundle_executable: `{package_gate['cf_bundle_executable']}`",
        "",
        "## Click Results",
        "",
        "| scope | button | expected | result |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload["clicks"]:
        lines.append(
            f"| `{item['scope']}` | `{item['object_name']}` {item['text']} | "
            f"`{item['expected_workspace']}` | `{item['result']}` |"
        )
    lines.extend(["", "## Screenshots", ""])
    for shot in payload["screenshots"]:
        lines.append(f"- `{shot['name']}`: `{shot['path']}`")
    if payload["disabled_without_reason"]:
        lines.extend(["", "## Disabled Buttons Missing Reason", ""])
        for item in payload["disabled_without_reason"]:
            lines.append(f"- `{item['object_name']}` {item['text']}")
    else:
        lines.extend(["", "## Disabled Buttons Missing Reason", "", "None detected in the visible phase-1 shell scope."])
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
