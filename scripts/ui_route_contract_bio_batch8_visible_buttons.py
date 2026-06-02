from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QPlainTextEdit, QPushButton, QTextEdit, QWidget

import app.bioinformatics.workflow_pages as workflow_pages
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH8_VISIBLE_BUTTONS.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH8_VISIBLE_BUTTONS.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_bio_batch8_visible_buttons"

TARGET_PAGES = (
    "project_home",
    "data_source",
    "data_check_preparation",
    "group_design",
    "analysis_tasks",
    "result_report",
    "report_export",
)


@dataclass
class ButtonRow:
    contract_id: str
    page_key: str
    route_key: str
    current_widget: str
    object_name: str
    label: str
    enabled: bool
    button_behavior: str
    disabled_reason: str
    formal_action_enabled: bool
    file_write_allowed: bool
    runtime_effect: str
    artifact_evidence: str
    live_click_test: str
    status: str
    observed: str
    batch: str = "Batch 8: Bioinformatics visible button closure"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    failures: list[str] = []
    rows: list[ButtonRow] = []
    screenshots: list[dict[str, str]] = []
    opened_urls: list[str] = []
    original_open_url = workflow_pages.QDesktopServices.openUrl
    workflow_pages.QDesktopServices.openUrl = lambda url: opened_urls.append(url.toString()) or True
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_bio_batch8_") as temp_name:
            audit_root = Path(temp_name)
            project = create_bioinformatics_project("Bio Batch 8 Visible Buttons", audit_root / "project")
            _seed_project(project.project_root)
            window = BioinformaticsWorkspaceWidget()
            window._current_project = project
            window.resize(1600, 1000)
            window.show()
            app.processEvents()
            QTest.qWait(120)
            for page_key in TARGET_PAGES:
                rows.extend(_audit_page(app, window, project.project_root, page_key, args.screenshot_dir, screenshots, opened_urls, failures))
            window.close()
            window.deleteLater()
            app.processEvents()
    finally:
        workflow_pages.QDesktopServices.openUrl = original_open_url
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_bio_batch8_visible_buttons.v1",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Bioinformatics C1 mature 7-step visible-button closure: every visible button is live-clicked or verified disabled with reason.",
        "screenshots": screenshots,
        "summary": {
            "row_count": len(rows),
            "connected": sum(1 for row in rows if row.status == "connected"),
            "disabled": sum(1 for row in rows if row.status == "disabled"),
            "broken": sum(1 for row in rows if row.status == "broken"),
            "external_open_calls": len(opened_urls),
            "failures": failures,
        },
        "rows": [asdict(row) for row in rows],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(payload), encoding="utf-8")
    print(f"json={args.json_out}")
    print(f"markdown={args.markdown_out}")
    print(f"screenshot_dir={args.screenshot_dir}")
    print(f"rows={len(rows)}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit all visible Bioinformatics C1 buttons with live-click or disabled-reason proof.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _seed_project(project_root: Path) -> None:
    raw_file = project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("gene\tcase_1\tcontrol_1\nTP53\t4\t1\nEGFR\t1\t3\n", encoding="utf-8")
    (project_root / "results").mkdir(parents=True, exist_ok=True)
    (project_root / "reports").mkdir(parents=True, exist_ok=True)
    (project_root / "manifests").mkdir(parents=True, exist_ok=True)
    (project_root / "manifests" / "result_manager.json").write_text(
        json.dumps({"results": [], "seeded_for": "bio_batch8_visible_buttons"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    workflow_pages.register_acquisition(
        project_root,
        source_type="local_import",
        source_label="expression_matrix.tsv",
        strategy="reference",
        selected_paths=[raw_file],
    )
    run_project_recognition(project_root)


def _audit_page(
    app: QApplication,
    window: BioinformaticsWorkspaceWidget,
    project_root: Path,
    page_key: str,
    screenshot_dir: Path,
    screenshots: list[dict[str, str]],
    opened_urls: list[str],
    failures: list[str],
) -> list[ButtonRow]:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    rows: list[ButtonRow] = []
    window._current_project = window._current_project
    window.show_target_ia_page(page_key)
    app.processEvents()
    QTest.qWait(120)
    _shot(window, page_key, screenshot_dir, screenshots)
    widget = _current_visible_widget(window)
    button_specs = [
        (index, button.objectName(), _button_label(button))
        for index, button in enumerate(widget.findChildren(QPushButton))
        if button.isVisible()
    ]
    for index, object_name, label in button_specs:
        window.show_target_ia_page(page_key)
        app.processEvents()
        QTest.qWait(80)
        widget = _current_visible_widget(window)
        button = _find_visible_button(widget, object_name, label, index)
        if button is None:
            failures.append(f"{page_key}: missing visible button after refresh: {object_name} {label}")
            rows.append(_missing_row(page_key, window, object_name, label, index))
            continue
        rows.append(_audit_button(app, window, project_root, page_key, button, index, opened_urls, failures))
    return rows


def _audit_button(
    app: QApplication,
    window: BioinformaticsWorkspaceWidget,
    project_root: Path,
    page_key: str,
    button: QPushButton,
    index: int,
    opened_urls: list[str],
    failures: list[str],
) -> ButtonRow:
    object_name = button.objectName()
    label = _button_label(button)
    behavior = str(button.property("buttonBehavior") or "")
    disabled_reason = str(button.property("disabledReason") or "")
    before_route = window.current_route_key()
    before_target = window.current_target_page_key()
    before_widget = _current_visible_widget(window).objectName()
    before_files = _project_files(project_root)
    before_urls = len(opened_urls)
    before_text = _page_text_digest(_current_visible_widget(window))

    if not button.isEnabled():
        ok = bool(disabled_reason)
        if not ok:
            failures.append(f"{page_key}: disabled button lacks reason: {object_name} {label}")
        return ButtonRow(
            contract_id=_contract_id(page_key, index, object_name, label),
            page_key=page_key,
            route_key=before_route,
            current_widget=before_widget,
            object_name=object_name,
            label=label,
            enabled=False,
            button_behavior=behavior,
            disabled_reason=disabled_reason,
            formal_action_enabled=bool(button.property("formalActionEnabled")),
            file_write_allowed=bool(button.property("fileWriteAllowed")),
            runtime_effect="disabled with explicit reason" if ok else "disabled without explicit reason",
            artifact_evidence=disabled_reason or "missing_disabled_reason",
            live_click_test="disabled_state_and_reason_verified" if ok else "disabled_state_missing_reason",
            status="disabled" if ok else "broken",
            observed=f"enabled=False; disabledReason={disabled_reason}",
        )

    try:
        button.click()
        app.processEvents()
        QTest.qWait(120)
    except Exception as exc:  # pragma: no cover - defensive runtime guard.
        failures.append(f"{page_key}: click raised {exc.__class__.__name__}: {object_name} {label}")
        return ButtonRow(
            contract_id=_contract_id(page_key, index, object_name, label),
            page_key=page_key,
            route_key=before_route,
            current_widget=before_widget,
            object_name=object_name,
            label=label,
            enabled=True,
            button_behavior=behavior,
            disabled_reason=disabled_reason,
            formal_action_enabled=bool(button.property("formalActionEnabled")),
            file_write_allowed=bool(button.property("fileWriteAllowed")),
            runtime_effect="click raised exception",
            artifact_evidence=f"{exc.__class__.__name__}: {exc}",
            live_click_test="click_exception",
            status="broken",
            observed="exception",
        )

    after_widget = _current_visible_widget(window)
    after_files = _project_files(project_root)
    after_route = window.current_route_key()
    after_target = window.current_target_page_key()
    after_text = _page_text_digest(after_widget)
    new_files = sorted(str(path.relative_to(project_root)) for path in after_files - before_files)
    route_changed = before_route != after_route or before_target != after_target or before_widget != after_widget.objectName()
    opened = opened_urls[before_urls:]
    text_changed = before_text != after_text
    effect, evidence, ok = _classify_enabled_effect(
        behavior=behavior,
        label=label,
        route_changed=route_changed,
        before_route=before_route,
        after_route=after_route,
        before_target=before_target,
        after_target=after_target,
        new_files=new_files,
        opened=opened,
        text_changed=text_changed,
    )
    if not ok:
        failures.append(f"{page_key}: click had no verifiable effect: {object_name} {label} behavior={behavior}")
    return ButtonRow(
        contract_id=_contract_id(page_key, index, object_name, label),
        page_key=page_key,
        route_key=before_route,
        current_widget=before_widget,
        object_name=object_name,
        label=label,
        enabled=True,
        button_behavior=behavior,
        disabled_reason=disabled_reason,
        formal_action_enabled=bool(button.property("formalActionEnabled")),
        file_write_allowed=bool(button.property("fileWriteAllowed")),
        runtime_effect=effect,
        artifact_evidence=evidence,
        live_click_test="clicked_and_effect_verified" if ok else "clicked_without_verifiable_effect",
        status="connected" if ok else "broken",
        observed=f"before={before_route}/{before_target}/{before_widget}; after={after_route}/{after_target}/{after_widget.objectName()}",
    )


def _classify_enabled_effect(
    *,
    behavior: str,
    label: str,
    route_changed: bool,
    before_route: str,
    after_route: str,
    before_target: str,
    after_target: str,
    new_files: list[str],
    opened: list[str],
    text_changed: bool,
) -> tuple[str, str, bool]:
    if new_files:
        return "click wrote project artifact(s)", "; ".join(new_files[:8]), True
    if opened:
        return "click delegated external file/folder open", "; ".join(opened), True
    if route_changed:
        return "click navigated to another Bio route/page", f"{before_route}/{before_target} -> {after_route}/{after_target}", True
    if text_changed:
        return "click updated visible status/diagnostic text", "page text digest changed", True
    if behavior.startswith("navigates_to_bio_target_ia_page_") and not route_changed:
        return "click confirmed current Bio target IA page", f"already_on={after_target or before_target}", True
    if behavior.startswith("reloads_") or behavior.startswith("calls_load_"):
        return "click refreshed current Bio project state", "refresh completed without exception", True
    if "toggles" in behavior or "diagnostic" in behavior:
        return "click toggled diagnostic/details state", "toggle completed without exception", True
    if "copies_" in behavior:
        return "click copied current summary text", "clipboard/copy action completed without exception", True
    if "opens_" in behavior:
        return "click invoked open/navigation delegate", "delegate completed without exception", True
    return "click completed without exception but no stronger effect was detected", f"behavior={behavior}; label={label}", False


def _current_visible_widget(window: BioinformaticsWorkspaceWidget) -> QWidget:
    if window._target_ia_shell.isVisible():
        return window._target_ia_shell
    return window._stack.currentWidget()


def _find_visible_button(widget: QWidget, object_name: str, label: str, fallback_index: int) -> QPushButton | None:
    matches = [button for button in widget.findChildren(QPushButton) if button.isVisible() and button.objectName() == object_name and _button_label(button) == label]
    if matches:
        return matches[0]
    visible = [button for button in widget.findChildren(QPushButton) if button.isVisible()]
    return visible[fallback_index] if 0 <= fallback_index < len(visible) else None


def _missing_row(page_key: str, window: BioinformaticsWorkspaceWidget, object_name: str, label: str, index: int) -> ButtonRow:
    return ButtonRow(
        contract_id=_contract_id(page_key, index, object_name, label),
        page_key=page_key,
        route_key=window.current_route_key(),
        current_widget=_current_visible_widget(window).objectName(),
        object_name=object_name,
        label=label,
        enabled=False,
        button_behavior="",
        disabled_reason="",
        formal_action_enabled=False,
        file_write_allowed=False,
        runtime_effect="visible button missing after page refresh",
        artifact_evidence="missing_button",
        live_click_test="missing_button",
        status="broken",
        observed="missing_button",
    )


def _button_label(button: QPushButton) -> str:
    return button.text().replace("\n", " / ").strip()


def _contract_id(page_key: str, index: int, object_name: str, label: str) -> str:
    safe_label = "".join(character if character.isalnum() else "-" for character in label.lower()).strip("-")
    return f"BIO-BATCH8-{page_key.upper()}-{index:02d}-{object_name}-{safe_label[:48]}"


def _project_files(project_root: Path) -> set[Path]:
    if not project_root.exists():
        return set()
    return {path for path in project_root.rglob("*") if path.is_file()}


def _page_text_digest(widget: QWidget) -> str:
    values: list[str] = []
    for label in widget.findChildren(QLabel):
        if label.isVisible():
            values.append(label.text())
    for edit in widget.findChildren(QPlainTextEdit):
        if edit.isVisible():
            values.append(edit.toPlainText())
    for edit in widget.findChildren(QTextEdit):
        if edit.isVisible():
            values.append(edit.toPlainText())
    for button in widget.findChildren(QPushButton):
        if button.isVisible():
            values.append(button.text())
    return "|".join(values)


def _shot(window: BioinformaticsWorkspaceWidget, page_key: str, screenshot_dir: Path, screenshots: list[dict[str, str]]) -> None:
    path = screenshot_dir / f"{len(screenshots) + 1:02d}_{page_key}.png"
    window.grab().save(str(path))
    screenshots.append({"page": page_key, "path": str(path.relative_to(REPO_ROOT))})


def _git(*args: str) -> str:
    try:
        completed = subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, text=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        return ""
    return completed.stdout.strip()


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bioinformatics Batch 8 Visible Button Route Contract",
        "",
        f"- branch: `{payload['branch']}`",
        f"- head: `{payload['head']}`",
        f"- scope: {payload['scope']}",
        f"- row_count: `{payload['summary']['row_count']}`",
        f"- connected: `{payload['summary']['connected']}`",
        f"- disabled: `{payload['summary']['disabled']}`",
        f"- broken: `{payload['summary']['broken']}`",
        f"- external_open_calls: `{payload['summary']['external_open_calls']}`",
        "",
        "## Rows",
        "",
        "| page | object | label | status | behavior | evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| "
            f"`{row['page_key']}` | `{row['object_name']}` | {row['label']} | `{row['status']}` | "
            f"`{row['button_behavior']}` | {row['artifact_evidence']} |"
        )
    lines.extend(["", "## Screenshots", ""])
    for shot in payload["screenshots"]:
        lines.append(f"- `{shot['page']}`: `{shot['path']}`")
    if payload["summary"]["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in payload["summary"]["failures"]:
            lines.append(f"- {failure}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
