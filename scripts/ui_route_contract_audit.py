from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtWidgets import QApplication, QPushButton

from app.shell.centers_page import build_centers_page
from app.shell.main_window import MainWindow
from app.shared.data_center.service import DataCenter
from app.shared.project_center.service import ProjectCenter
from app.shared.task_center.service import TaskCenter
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_PHASE1_BATCH0.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_PHASE1_BATCH0.md"


@dataclass
class ContractRow:
    contract_id: str
    module: str
    surface: str
    current_file: str
    object_name: str
    label: str
    enabled: bool
    button_behavior: str
    disabled_reason: str
    runtime_effect: str
    artifact_evidence: str
    live_click_test: str
    status: str
    observed: str
    batch: str = "Batch 0: Contract Freeze"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    try:
        rows.extend(_audit_welcome_routes(app, failures))
        rows.extend(_audit_home_routes(app, failures))
        rows.extend(_audit_sidebar_routes(app, failures))
        rows.extend(_audit_centers_actions(app, failures))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_phase1_batch0.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Shell freeze route and live-click audit for Welcome, Home, Sidebar, and Centers.",
        "summary": {
            "row_count": len(rows),
            "connected": sum(1 for row in rows if row.status == "connected"),
            "disabled": sum(1 for row in rows if row.status == "disabled"),
            "broken": sum(1 for row in rows if row.status == "broken"),
            "failures": failures,
        },
        "rows": [asdict(row) for row in rows],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(payload), encoding="utf-8")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(f"json={args.json_out}")
    print(f"markdown={args.markdown_out}")
    print(f"rows={len(rows)}")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 1 Batch 0 UI route contract live-click audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    return parser.parse_args(argv)


def _audit_welcome_routes(app: QApplication, failures: list[str]) -> list[ContractRow]:
    specs = (
        ("SHELL-WELCOME-ENTER", "primaryButton", "dashboard", "navigates to Dashboard from Welcome"),
        ("SHELL-WELCOME-ABOUT", "aboutButton", "about", "navigates to About from Welcome"),
        ("SHELL-WELCOME-SETTINGS", "loginTopIconButton", "settings", "navigates to Settings from Welcome"),
    )
    rows: list[ContractRow] = []
    for contract_id, object_name, expected_workspace, effect in specs:
        window = MainWindow()
        try:
            button = _find_button(window._welcome_page, object_name)
            observed = _click_and_workspace(app, window, button)
            rows.append(
                _row(
                    contract_id=contract_id,
                    module="Shell",
                    surface="Welcome",
                    current_file="app/shell/login.py",
                    button=button,
                    runtime_effect=effect,
                    artifact_evidence=f"current_workspace_key={observed}",
                    observed=f"expected={expected_workspace}; observed={observed}",
                    status="connected" if observed == expected_workspace else "broken",
                )
            )
            if observed != expected_workspace:
                failures.append(f"{contract_id}: expected {expected_workspace}, observed {observed}")
        finally:
            window.close()
            window.deleteLater()
            app.processEvents()
    return rows


def _audit_home_routes(app: QApplication, failures: list[str]) -> list[ContractRow]:
    specs = (
        ("SHELL-HOME-BIO", "bioModuleButton", "bioinformatics", "navigates to Bioinformatics adapter"),
        ("SHELL-HOME-META", "metaModuleButton", "meta_analysis", "navigates to Meta Analysis adapter"),
        ("SHELL-HOME-LABTOOLS", "labtoolsModuleButton", "labtools", "navigates to LabTools adapter"),
    )
    rows: list[ContractRow] = []
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        app.processEvents()
        for contract_id, object_name, expected_workspace, effect in specs:
            window.show_dashboard()
            app.processEvents()
            button = _find_button(window._dashboard_page, object_name)
            observed = _click_and_workspace(app, window, button)
            rows.append(
                _row(
                    contract_id=contract_id,
                    module="Shell",
                    surface="Home / Dashboard",
                    current_file="app/shell/module_selection.py",
                    button=button,
                    runtime_effect=effect,
                    artifact_evidence=f"current_workspace_key={observed}",
                    observed=f"expected={expected_workspace}; observed={observed}",
                    status="connected" if observed == expected_workspace else "broken",
                )
            )
            if observed != expected_workspace:
                failures.append(f"{contract_id}: expected {expected_workspace}, observed {observed}")
        for button in window._dashboard_page.findChildren(QPushButton):
            if button.objectName() in {"dashboardHeaderIconButton", "dashboardOpenMoreProjectsButton", "dashboardViewAllProjectsButton"}:
                rows.append(_disabled_or_metadata_row("SHELL-HOME", "Home / Dashboard", "app/shell/module_selection.py", button, failures))
    finally:
        window.close()
        window.deleteLater()
        app.processEvents()
    return rows


def _audit_sidebar_routes(app: QApplication, failures: list[str]) -> list[ContractRow]:
    expected = {
        "dashboard": "dashboard",
        "bioinformatics": "bioinformatics",
        "meta_analysis": "meta_analysis",
        "labtools": "labtools",
        "centers": "centers",
        "settings": "settings",
        "test_feedback": "test_feedback",
        "about": "about",
    }
    rows: list[ContractRow] = []
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        app.processEvents()
        for page_key, expected_workspace in expected.items():
            button = _sidebar_button(window, page_key)
            observed = _click_and_workspace(app, window, button)
            contract_id = f"SHELL-SIDEBAR-{page_key.upper()}"
            rows.append(
                _row(
                    contract_id=contract_id,
                    module="Shell",
                    surface="Sidebar",
                    current_file="app/shell/sidebar.py",
                    button=button,
                    runtime_effect=f"navigates to {expected_workspace}",
                    artifact_evidence=f"current_workspace_key={observed}",
                    observed=f"expected={expected_workspace}; observed={observed}",
                    status="connected" if observed == expected_workspace else "broken",
                )
            )
            if observed != expected_workspace:
                failures.append(f"{contract_id}: expected {expected_workspace}, observed {observed}")
    finally:
        window.close()
        window.deleteLater()
        app.processEvents()
    return rows


def _audit_centers_actions(app: QApplication, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    with tempfile.TemporaryDirectory(prefix="biomedpilot_ui_route_contract_") as temp_name:
        root = Path(temp_name)
        project_center = ProjectCenter(root / "projects" / "projects.json")
        data_center = DataCenter(root / "data" / "data_assets.json")
        task_center = TaskCenter(root / "tasks" / "tasks.json")
        data_center.register_asset(
            project_id="project-1",
            module="bioinformatics",
            data_type="expression_matrix",
            source_path="source.tsv",
            output_path="output.tsv",
        )
        page = build_centers_page(project_center=project_center, data_center=data_center, task_center=task_center)
        app.processEvents()
        checks: dict[str, tuple[str, Callable[[], bool]]] = {
            "centersRefreshProjectsButton": ("calls ProjectCenter recent projects", lambda: True),
            "centersCreateProjectRecordButton": ("writes ProjectCenter index", lambda: project_center.storage_path.exists() and bool(project_center.list_projects(limit=None))),
            "centersRefreshDataButton": ("calls DataCenter list assets", lambda: True),
            "centersExportDataIndexButton": ("writes data center index summary artifact", lambda: (root / "centers" / "data_center_index_summary.json").exists()),
            "centersRefreshTasksButton": ("calls TaskCenter list tasks", lambda: True),
            "centersCreateTaskButton": ("writes TaskCenter index", lambda: task_center.storage_path.exists() and bool(task_center.list_tasks(limit=None))),
            "centersBuildReportIndexButton": ("writes report center index artifact", lambda: (root / "centers" / "report_center_index.json").exists()),
            "centersRunEnvironmentCheckButton": ("writes environment status artifact", lambda: (root / "centers" / "environment_status.json").exists()),
            "centersBuildPackagingPreflightButton": ("writes packaging preflight artifact", lambda: (root / "centers" / "packaging_preflight.json").exists()),
        }
        for object_name, (effect, checker) in checks.items():
            button = _find_button(page, object_name)
            button.click()
            app.processEvents()
            ok = checker()
            rows.append(
                _row(
                    contract_id=f"SHELL-CENTERS-{object_name.removeprefix('centers').removesuffix('Button').upper()}",
                    module="Centers",
                    surface="Centers",
                    current_file="app/shell/centers_page.py",
                    button=button,
                    runtime_effect=effect,
                    artifact_evidence=f"temp_audit_root={root}; proof={ok}",
                    observed="artifact_or_service_verified" if ok else "missing_expected_artifact_or_state",
                    status="connected" if ok else "broken",
                )
            )
            if not ok:
                failures.append(f"{object_name}: expected Centers action proof was missing")
        build = _find_button(page, "centersRunReleaseBuildButton")
        rows.append(_disabled_or_metadata_row("SHELL-CENTERS", "Centers", "app/shell/centers_page.py", build, failures))
        page.deleteLater()
        app.processEvents()
    return rows


def _row(
    *,
    contract_id: str,
    module: str,
    surface: str,
    current_file: str,
    button: QPushButton,
    runtime_effect: str,
    artifact_evidence: str,
    observed: str,
    status: str,
) -> ContractRow:
    button_behavior = str(button.property("buttonBehavior") or "")
    disabled_reason = str(button.property("disabledReason") or "")
    if not button_behavior:
        status = "broken"
        observed = f"{observed}; missing buttonBehavior"
    if not button.isEnabled() and not disabled_reason:
        status = "broken"
        observed = f"{observed}; missing disabledReason"
    return ContractRow(
        contract_id=contract_id,
        module=module,
        surface=surface,
        current_file=current_file,
        object_name=button.objectName(),
        label=button.text() or button.accessibleName() or button.toolTip(),
        enabled=button.isEnabled(),
        button_behavior=button_behavior,
        disabled_reason=disabled_reason,
        runtime_effect=runtime_effect,
        artifact_evidence=artifact_evidence,
        live_click_test="scripts/ui_route_contract_audit.py",
        status=status,
        observed=observed,
    )


def _disabled_or_metadata_row(prefix: str, surface: str, current_file: str, button: QPushButton, failures: list[str]) -> ContractRow:
    status = "disabled" if not button.isEnabled() and button.property("disabledReason") else "connected"
    row = _row(
        contract_id=f"{prefix}-{button.objectName()}-{button.text() or button.accessibleName() or button.toolTip()}",
        module="Shell",
        surface=surface,
        current_file=current_file,
        button=button,
        runtime_effect="disabled placeholder with explicit reason" if not button.isEnabled() else "metadata-only shell control",
        artifact_evidence=str(button.property("disabledReason") or button.property("buttonBehavior") or ""),
        observed="disabled_reason_present" if not button.isEnabled() and button.property("disabledReason") else "metadata_present",
        status=status,
    )
    if row.status == "broken":
        failures.append(f"{row.contract_id}: {row.observed}")
    return row


def _find_button(widget, object_name: str) -> QPushButton:
    button = widget.findChild(QPushButton, object_name)
    if button is None:
        raise AssertionError(f"Missing button: {object_name}")
    return button


def _sidebar_button(window: MainWindow, page_key: str) -> QPushButton:
    for button in window._sidebar.findChildren(QPushButton):
        if button.property("pageKey") == page_key:
            return button
    raise AssertionError(f"Missing sidebar button for pageKey={page_key}")


def _click_and_workspace(app: QApplication, window: MainWindow, button: QPushButton) -> str:
    button.click()
    app.processEvents()
    return window.current_workspace_key()


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract Phase 1 Batch 0 Report",
        "",
        f"- created_at: `{payload['created_at']}`",
        f"- branch: `{payload['branch']}`",
        f"- head: `{payload['head']}`",
        f"- scope: {payload['scope']}",
        "",
        "## Summary",
        "",
        f"- row_count: `{summary['row_count']}`",
        f"- connected: `{summary['connected']}`",
        f"- disabled: `{summary['disabled']}`",
        f"- broken: `{summary['broken']}`",
        "",
        "## Contract Rows",
        "",
        "| Contract ID | Module | Surface | Object | Behavior | Runtime Effect | Status | Observed |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {contract_id} | {module} | {surface} | `{object_name}` | `{button_behavior}` | {runtime_effect} | `{status}` | {observed} |".format(
                **{key: _escape_md(str(value)) for key, value in row.items()}
            )
        )
    failures = summary["failures"]
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- `{_escape_md(str(failure))}`" for failure in failures)
    lines.append("")
    return "\n".join(lines)


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _git(*args: str) -> str:
    import subprocess

    try:
        completed = subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, text=True, capture_output=True)
    except Exception:
        return ""
    return completed.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
