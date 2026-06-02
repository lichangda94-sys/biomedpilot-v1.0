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


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH8_QUALITY_ASSESSMENT.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH8_QUALITY_ASSESSMENT.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_meta_batch8_quality_assessment"


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
    batch: str = "Batch 8: Meta Quality Assessment"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    screenshots: list[dict[str, str]] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_meta_batch8_") as temp_name:
            project_dir = _seed_project(Path(temp_name))
            rows.extend(_audit_quality_ui(app, project_dir, args.screenshot_dir, screenshots, failures))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_meta_batch8_quality_assessment.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Meta mature UIShell Quality Assessment page: reviewer-controlled quality draft, quality summary, and export artifacts.",
        "source_matrix": {
            "ui_baseline": "UIShell high-fidelity Meta target IA Quality Assessment Workspace in app/meta_analysis/workspace.py.",
            "backend_sources": ["app/meta_analysis/services/quality_service.py", "app/meta_analysis/quality/tool_registry.py"],
            "policy": "Quality tools are suggestion/form templates only; final RoB/GRADE judgement, analysis-ready dataset creation, statistics execution, and report-ready advancement remain disabled.",
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
    parser = argparse.ArgumentParser(description="Run Meta Batch 8 quality assessment route contract audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _seed_project(root: Path) -> Path:
    summary = create_meta_analysis_project("Meta Batch 8 Quality Assessment", root)
    return summary.project_root


def _audit_quality_ui(
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
        widget.show_target_ia_page("quality_assessment")
        widget.show()
        app.processEvents()
        QTest.qWait(80)
        screenshots.append(_capture(widget, screenshot_dir / "01_quality_assessment.png", "quality_assessment"))

        save = _find_button(widget, "metaSaveRiskOfBiasDraftButton")
        save.click()
        app.processEvents()
        QTest.qWait(80)

        gate = project_dir / "ui_runtime" / "meta_risk_of_bias_disabled_reason.json"
        records = project_dir / "quality" / "quality_assessment_records_v1.json"
        summary = project_dir / "quality" / "quality_assessment_summary_v1.json"
        export_json = project_dir / "quality" / "quality_assessment_v1_export.json"
        export_csv = project_dir / "exports" / "quality_assessment_v1.csv"
        payload = _load_json(gate)
        connected = gate.exists() and records.exists() and summary.exists()
        rows.append(
            _row(
                "META-QUALITY-SAVE-DRAFT",
                "Quality Assessment",
                "QualityAssessmentService.create_quality_assessment_draft",
                save,
                gate,
                "connected" if connected else "broken",
                _observed_quality_payload(payload, "draft_saved") if connected else "missing_quality_draft_artifacts",
            )
        )
        if not connected:
            failures.append("META-QUALITY-SAVE-DRAFT: quality draft artifacts missing")

        exported = export_json.exists() and export_csv.exists()
        rows.append(
            _row(
                "META-QUALITY-EXPORT-DRAFT-ARTIFACTS",
                "Quality Assessment",
                "QualityAssessmentService.export_quality_assessments_v1_json/export_quality_assessments_v1_csv",
                save,
                export_csv,
                "connected" if exported else "broken",
                "quality_json_and_csv_exported" if exported else "missing_quality_export_artifacts",
            )
        )
        if not exported:
            failures.append("META-QUALITY-EXPORT-DRAFT-ARTIFACTS: quality export artifacts missing")

        boundary_ok = (
            payload.get("auto_scores_final_quality") is False
            and payload.get("analysis_ready_dataset_created") is False
            and payload.get("statistics_run") is False
            and payload.get("prisma_advanced") is False
            and payload.get("report_ready") is False
        )
        rows.append(
            _row(
                "META-QUALITY-NO-FORMAL-GRADE-GATE",
                "Quality Assessment",
                "quality boundary gate",
                save,
                gate,
                "connected" if boundary_ok else "broken",
                _observed_quality_payload(payload, "formal_quality_gate_closed") if boundary_ok else "formal_quality_boundary_leaked",
            )
        )
        if not boundary_ok:
            failures.append("META-QUALITY-NO-FORMAL-GRADE-GATE: formal quality/report boundary leaked")
        screenshots.append(_capture(widget, screenshot_dir / "02_quality_after_save.png", "quality_after_save"))
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
        expected_artifact=str(artifact),
        live_click_test="scripts/ui_route_contract_meta_batch8_quality_assessment.py",
        status=status,
        observed=observed,
    )


def _observed_quality_payload(payload: dict[str, object], prefix: str) -> str:
    keys = ("assessment_id", "tool_name", "status", "assessment_count", "statistics_run", "report_ready")
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
        "# UI Route Contract - Meta Batch 8 Quality Assessment",
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
