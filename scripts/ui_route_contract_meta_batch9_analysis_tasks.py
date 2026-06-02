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


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from app.meta_analysis.project_workspace import create_meta_analysis_project
from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH9_ANALYSIS_TASKS.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH9_ANALYSIS_TASKS.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_meta_batch9_analysis_tasks"


@dataclass
class ContractRow:
    contract_id: str
    ui_page: str
    backend_capability: str
    branch_source: str
    current_file: str
    object_name: str
    label: str
    enabled: bool
    button_behavior: str
    disabled_reason: str
    expected_artifact: str
    live_click_test: str
    status: str
    observed: str
    batch: str = "Batch 9: Meta Analysis Tasks"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    screenshots: list[dict[str, str]] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_meta_batch9_") as temp_name:
            project_dir = _seed_project(Path(temp_name))
            rows.extend(_audit_analysis_tasks_ui(app, project_dir, args.screenshot_dir, screenshots, failures))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_meta_batch9_analysis_tasks.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Meta mature UIShell Analysis Tasks page: analysis plan draft, preflight/applicability artifacts, and formal executor gate.",
        "source_matrix": {
            "ui_baseline": "UIShell high-fidelity Meta target IA Analysis Tasks Workspace in app/meta_analysis/workspace.py.",
            "backend_sources": ["app/meta_analysis/services/analysis_setup_service.py", "app/meta_analysis/services/analysis_dataset_service.py", "app/meta_analysis/services/statistical_applicability_service.py"],
            "policy": "Analysis plan and preflight are connected; formal statistical execution, figures, result tables, and report-ready advancement remain disabled until valid extraction records and reviewer confirmation exist.",
        },
        "summary": {
            "row_count": len(rows),
            "connected": sum(1 for row in rows if row.status == "connected"),
            "disabled": sum(1 for row in rows if row.status == "disabled"),
            "broken": sum(1 for row in rows if row.status == "broken"),
            "failures": failures,
        },
        "screenshots": screenshots,
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
    print(f"screenshots={args.screenshot_dir}")
    print(f"rows={len(rows)}")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Meta Batch 9 analysis tasks route contract audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _seed_project(root: Path) -> Path:
    summary = create_meta_analysis_project("Meta Batch 9 Analysis Tasks", root)
    return summary.project_root


def _audit_analysis_tasks_ui(
    app: QApplication,
    project_dir: Path,
    screenshot_dir: Path,
    screenshots: list[dict[str, str]],
    failures: list[str],
) -> list[ContractRow]:
    rows: list[ContractRow] = []
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    widget = MetaAnalysisWorkspaceWidget()
    try:
        widget.resize(1600, 1000)
        widget.set_project_dir(project_dir)
        widget.show_target_ia_page("analysis_tasks")
        widget.show()
        app.processEvents()
        QTest.qWait(80)
        screenshots.append(_capture(widget, screenshot_dir / "01_analysis_tasks.png", "analysis_tasks"))

        draft = _find_button(widget, "metaBuildAnalysisPlanDraftButton")
        draft.click()
        app.processEvents()
        QTest.qWait(80)
        draft_gate = project_dir / "ui_runtime" / "meta_analysis_plan_draft_adapter.json"
        plan_path = project_dir / "analysis" / "analysis_plan.json"
        draft_payload = _load_json(draft_gate)
        draft_ok = draft_gate.exists() and plan_path.exists() and draft_payload.get("statistics_run") is False and draft_payload.get("report_ready") is False
        rows.append(
            _row(
                "META-ANALYSIS-PLAN-DRAFT",
                "Analysis Tasks",
                "AnalysisSetupService.create_plan/save_analysis_plan",
                draft,
                draft_gate,
                "connected" if draft_ok else "broken",
                _observed(draft_payload, "analysis_plan_draft_written") if draft_ok else "missing_analysis_plan_draft",
            )
        )
        if not draft_ok:
            failures.append("META-ANALYSIS-PLAN-DRAFT: analysis plan draft artifact missing or boundary leaked")

        preflight = _find_button(widget, "metaRunAnalysisPreflightButton")
        preflight.click()
        app.processEvents()
        QTest.qWait(80)
        preflight_gate = project_dir / "ui_runtime" / "meta_analysis_preflight_adapter.json"
        warnings_path = project_dir / "analysis" / "applicability_warnings.json"
        dataset_alias = project_dir / "analysis" / "analysis_ready_dataset.json"
        preflight_payload = _load_json(preflight_gate)
        preflight_ok = (
            preflight_gate.exists()
            and warnings_path.exists()
            and dataset_alias.exists()
            and preflight_payload.get("formal_statistics_run") is False
            and preflight_payload.get("analysis_result_created") is False
            and preflight_payload.get("report_ready") is False
        )
        rows.append(
            _row(
                "META-ANALYSIS-PREFLIGHT",
                "Analysis Tasks",
                "AnalysisSetupService.run_preflight",
                preflight,
                preflight_gate,
                "connected" if preflight_ok else "broken",
                _observed(preflight_payload, "analysis_preflight_artifacts_written") if preflight_ok else "missing_analysis_preflight_artifacts",
            )
        )
        if not preflight_ok:
            failures.append("META-ANALYSIS-PREFLIGHT: preflight artifacts missing or formal boundary leaked")

        formal = _find_button(widget, "metaTargetBoundaryDisabledAction")
        formal_ok = not formal.isEnabled() and bool(str(formal.property("disabledReason") or ""))
        rows.append(
            _row(
                "META-ANALYSIS-FORMAL-RUN-GATE",
                "Analysis Tasks",
                "formal statistics execution disabled reason",
                formal,
                Path(""),
                "disabled" if formal_ok else "broken",
                "disabled_with_reason" if formal_ok else "formal_run_gate_missing_disabled_reason",
            )
        )
        if not formal_ok:
            failures.append("META-ANALYSIS-FORMAL-RUN-GATE: formal run gate missing disabled reason")
        screenshots.append(_capture(widget, screenshot_dir / "02_analysis_after_preflight.png", "analysis_after_preflight"))
    finally:
        widget.close()
        widget.deleteLater()
    return rows


def _find_button(widget: MetaAnalysisWorkspaceWidget, object_name: str) -> QPushButton:
    button = widget.findChild(QPushButton, object_name)
    if button is None:
        raise AssertionError(f"button not found: {object_name}")
    return button


def _row(
    contract_id: str,
    ui_page: str,
    backend_capability: str,
    button: QPushButton,
    artifact: Path,
    status: str,
    observed: str,
) -> ContractRow:
    return ContractRow(
        contract_id=contract_id,
        ui_page=ui_page,
        backend_capability=backend_capability,
        branch_source="UIShell high-fidelity Meta page + current Integration service adapter",
        current_file="app/meta_analysis/workspace.py",
        object_name=button.objectName(),
        label=button.text().replace("\n", " / "),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        disabled_reason=str(button.property("disabledReason") or ""),
        expected_artifact="" if artifact == Path("") else str(artifact),
        live_click_test="scripts/ui_route_contract_meta_batch9_analysis_tasks.py",
        status=status,
        observed=observed,
    )


def _observed(payload: dict[str, object], prefix: str) -> str:
    keys = ("success", "analysis_profile_type", "dataset_created", "formal_statistics_run", "analysis_result_created", "report_ready", "errors", "warnings")
    selected = {key: payload.get(key) for key in keys if key in payload}
    return f"{prefix}={json.dumps(selected, ensure_ascii=False, sort_keys=True)}"


def _capture(widget: MetaAnalysisWorkspaceWidget, path: Path, name: str) -> dict[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(path))
    return {"name": name, "path": str(path), "page_key": widget.current_target_page_key()}


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract - Meta Batch 9 Analysis Tasks",
        "",
        f"- branch: `{payload['branch']}`",
        f"- head: `{payload['head']}`",
        f"- scope: {payload['scope']}",
        f"- rows: `{summary['row_count']}`",
        f"- connected: `{summary['connected']}`",
        f"- disabled: `{summary['disabled']}`",
        f"- broken: `{summary['broken']}`",
        "",
        "## Matrix",
        "",
        "| contract | UI page | capability | object | status | observed |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['contract_id']}` | {row['ui_page']} | {row['backend_capability']} | "
            f"`{row['object_name']}` | `{row['status']}` | {row['observed']} |"
        )
    lines.extend(["", "## Screenshots", ""])
    for shot in payload["screenshots"]:
        lines.append(f"- `{shot['name']}`: `{shot['path']}`")
    lines.append("")
    return "\n".join(lines)


def _git(*args: str) -> str:
    try:
        completed = subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return ""
    return completed.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
