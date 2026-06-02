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
from typing import Callable


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("BIOINF_LIGHT_VALIDATION_MODE", "1")
os.environ.setdefault("BIOINF_TCGA_DOWNLOAD_LIMIT_FILES", "1")
os.environ.setdefault("BIOINF_GTEX_DOWNLOAD_LIMIT_FILES", "1")
os.environ.setdefault("BIOINF_GTEX_LIMIT_SAMPLES", "3")
os.environ.setdefault("BIOINF_GTEX_LIMIT_GENES", "10")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox, QPushButton, QTableWidget, QWidget

from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH13_TCGA_GTEX_DATA_CHECK.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH13_TCGA_GTEX_DATA_CHECK.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_bio_batch13_tcga_gtex_data_check"


@dataclass
class ContractRow:
    contract_id: str
    page_key: str
    object_name: str
    label: str
    backend_capability: str
    source_file: str
    runtime_effect: str
    artifact_evidence: str
    live_click_test: str
    status: str
    observed: str
    disabled_reason: str = ""
    batch: str = "Batch 13: Bioinformatics TCGA/GTEx Data Check recognition/readiness"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    screenshots: list[dict[str, str]] = []
    failures: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_bio_batch13_tcga_gtex_") as temp_name:
            project = create_bioinformatics_project("Bio Batch 13 TCGA GTEx Data Check", Path(temp_name) / "project")
            window = BioinformaticsWorkspaceWidget()
            window.resize(1600, 1200)
            window.show()
            window._current_project = project
            rows.extend(_build_tcga_gtex_sources(app, window, project.project_root, args.screenshot_dir, screenshots, failures))
            rows.extend(_audit_data_check(app, window, project.project_root, args.screenshot_dir, screenshots, failures))
            window.close()
            window.deleteLater()
            _settle(app, 40)
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_bio_batch13_tcga_gtex_data_check.v1",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": (
            "Bioinformatics TCGA/GTEx light-validation build outputs into mature Data Check page: "
            "pre-recognition selection, recognition report, readiness report, and analysis capability matrix."
        ),
        "gate_policy": {
            "light_validation_mode": os.environ.get("BIOINF_LIGHT_VALIDATION_MODE", ""),
            "formal_analysis": "not opened by this batch",
            "production_use": "recognition/readiness artifacts are preflight evidence, not report-ready production analysis",
        },
        "screenshots": screenshots,
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
    parser = argparse.ArgumentParser(description="Audit TCGA/GTEx build outputs through Bio Data Check recognition/readiness.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _build_tcga_gtex_sources(
    app: QApplication,
    window: BioinformaticsWorkspaceWidget,
    project_root: Path,
    screenshot_dir: Path,
    screenshots: list[dict[str, str]],
    failures: list[str],
) -> list[ContractRow]:
    rows: list[ContractRow] = []
    window.show_target_ia_page("data_source")
    _settle(app, 120)
    for source_key, prefix in (("tcga", "Tcga"), ("gtex", "Gtex")):
        _source_button(window, source_key).click()
        _settle(app, 160)
        for object_name in (
            f"bioinformatics{prefix}PreviewButton",
            f"bioinformatics{prefix}CreatePlanButton",
            f"bioinformatics{prefix}DownloadRawButton",
            f"bioinformatics{prefix}BuildExpressionButton",
        ):
            button = _button(window, object_name)
            if not button.isEnabled():
                failures.append(f"{object_name}: disabled during build setup: {button.property('disabledReason') or button.toolTip()}")
                rows.append(_button_row(f"BIO-B13-SETUP-{object_name}", "data_source", button, "setup", "setup click", "disabled during setup", "button disabled", "broken", str(button.property("disabledReason") or "")))
                continue
            button.click()
            _settle(app, 900 if "Preview" in object_name else 260)
        _shot(window, f"01_{source_key}_built_source_ready", screenshot_dir, screenshots)
    rows.append(
        _evidence_row(
            "BIO-B13-SETUP-TCGA-BUILD-SOURCE",
            "data_source",
            "bioinformaticsTcgaBuildExpressionButton",
            "TCGA build setup",
            "app.bioinformatics.data_sources.tcga_expression_builder.TCGAExpressionQuantificationBuilder.build_from_record",
            "TCGA expression build registered as reference source for Data Check",
            _glob_evidence(project_root, "standardized_data/tcga/**/tcga_expression_build_manifest.json"),
            failures,
        )
    )
    rows.append(
        _evidence_row(
            "BIO-B13-SETUP-GTEX-BUILD-SOURCE",
            "data_source",
            "bioinformaticsGtexBuildExpressionButton",
            "GTEx build setup",
            "app.bioinformatics.data_sources.gtex_expression_builder.GTExExpressionMatrixBuilder.build_from_record",
            "GTEx expression build registered as reference source for Data Check",
            _glob_evidence(project_root, "standardized_data/gtex/**/gtex_expression_build_manifest.json"),
            failures,
        )
    )
    return rows


def _audit_data_check(
    app: QApplication,
    window: BioinformaticsWorkspaceWidget,
    project_root: Path,
    screenshot_dir: Path,
    screenshots: list[dict[str, str]],
    failures: list[str],
) -> list[ContractRow]:
    rows: list[ContractRow] = []
    window.show_target_ia_page("data_check_preparation")
    _settle(app, 240)
    rows.append(
        _evidence_row(
            "BIO-B13-DATA-CHECK-PRE-INPUT-LIST",
            "data_check_preparation",
            "preRecognitionInputList",
            "pre-recognition source list",
            "app.bioinformatics.workflow_pages._pending_data_check_rows",
            "renders TCGA/GTEx expression build outputs as selectable pre-recognition inputs",
            _pre_input_evidence(window),
            failures,
        )
    )
    _select_tcga_gtex_inputs(window)
    _settle(app, 80)
    _shot(window, "02_data_check_tcga_gtex_selected", screenshot_dir, screenshots)

    start_button = _button_by_text(window, "开始识别")
    start_button.click()
    _settle(app, 320)
    _shot(window, "03_data_check_recognition_done", screenshot_dir, screenshots)
    rows.append(
        _button_row(
            "BIO-B13-DATA-CHECK-RUN-RECOGNITION-TCGA-GTEX",
            "data_check_preparation",
            start_button,
            "app.bioinformatics.project_recognition.run_project_recognition_for_paths",
            "recognizes selected TCGA/GTEx built expression assets",
            _recognition_evidence(project_root),
            "clicked_visible_button",
            "connected" if _recognition_evidence(project_root) else "broken",
        )
    )
    if not _recognition_evidence(project_root):
        failures.append("BIO-B13-DATA-CHECK-RUN-RECOGNITION-TCGA-GTEX: missing recognition evidence")

    continue_button = _button_by_text(window, "继续：数据准备与标准化")
    continue_button.click()
    _settle(app, 240)
    _shot(window, "04_readiness_before_run", screenshot_dir, screenshots)
    readiness_button = _button(window, "bioinformaticsRunDataCheckButton")
    readiness_button.click()
    _settle(app, 320)
    _shot(window, "05_readiness_after_run", screenshot_dir, screenshots)
    rows.append(
        _button_row(
            "BIO-B13-DATA-CHECK-RUN-READINESS-TCGA-GTEX",
            "data_check_preparation",
            readiness_button,
            "app.bioinformatics.project_readiness.run_project_readiness",
            "writes readiness report and analysis capability matrix for TCGA/GTEx built outputs",
            _readiness_evidence(project_root),
            "clicked_visible_button",
            "connected" if _readiness_evidence(project_root) else "broken",
        )
    )
    if not _readiness_evidence(project_root):
        failures.append("BIO-B13-DATA-CHECK-RUN-READINESS-TCGA-GTEX: missing readiness evidence")
    return rows


def _select_tcga_gtex_inputs(window: BioinformaticsWorkspaceWidget) -> None:
    selected = 0
    for checkbox in window.findChildren(QCheckBox):
        if not checkbox.objectName().startswith("preRecognitionSelect_"):
            continue
        checkbox.setChecked(True)
        selected += 1
    if selected < 2:
        raise AssertionError(f"Expected TCGA and GTEx pre-recognition checkboxes, selected={selected}")


def _pre_input_evidence(window: BioinformaticsWorkspaceWidget) -> str:
    table = window.findChild(QTableWidget, "preRecognitionInputList")
    if table is None:
        return ""
    text = " | ".join(_table_text(table, row, col) for row in range(table.rowCount()) for col in range(table.columnCount()))
    if "TCGA" in text and "GTEx" in text and table.rowCount() >= 2:
        return f"preRecognitionInputList rows={table.rowCount()}; contains TCGA and GTEx"
    return ""


def _recognition_evidence(project_root: Path) -> str:
    report_path = project_root / "logs" / "recognition" / "recognition_report.json"
    current_path = project_root / "recognized_data" / "current.json"
    group_path = project_root / "logs" / "recognition" / "group_preview_report.json"
    if not (report_path.exists() and current_path.exists() and group_path.exists()):
        return ""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    text = json.dumps(report, ensure_ascii=False)
    if "tcga" not in text.lower() or "gtex" not in text.lower():
        return ""
    return f"{_relative(project_root, report_path)}; {_relative(project_root, current_path)}; {_relative(project_root, group_path)}; selected_input_count={report.get('selected_input_count')}"


def _readiness_evidence(project_root: Path) -> str:
    readiness_path = project_root / "logs" / "readiness" / "readiness_report.json"
    matrix_path = project_root / "manifests" / "analysis_capability_matrix.json"
    if not (readiness_path.exists() and matrix_path.exists()):
        return ""
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    text = json.dumps({"readiness": readiness, "matrix": matrix}, ensure_ascii=False).lower()
    if "tcga" not in text and "gtex" not in text:
        return ""
    return f"{_relative(project_root, readiness_path)}; {_relative(project_root, matrix_path)}; overall_status={readiness.get('overall_status')}"


def _button_row(
    contract_id: str,
    page_key: str,
    button: QPushButton,
    backend_capability: str,
    runtime_effect: str,
    artifact_evidence: str,
    live_click_test: str,
    status: str,
    disabled_reason: str = "",
) -> ContractRow:
    return ContractRow(
        contract_id=contract_id,
        page_key=page_key,
        object_name=button.objectName(),
        label=button.text().replace("\n", " / "),
        backend_capability=backend_capability,
        source_file=backend_capability.rsplit(".", 1)[0].replace(".", "/") + ".py" if "." in backend_capability else "scripts/ui_route_contract_bio_batch13_tcga_gtex_data_check.py",
        runtime_effect=runtime_effect,
        artifact_evidence=artifact_evidence,
        live_click_test=live_click_test,
        status=status,
        observed=artifact_evidence or "missing expected artifact/effect",
        disabled_reason=disabled_reason,
    )


def _evidence_row(
    contract_id: str,
    page_key: str,
    object_name: str,
    label: str,
    backend_capability: str,
    runtime_effect: str,
    artifact_evidence: str,
    failures: list[str],
) -> ContractRow:
    if not artifact_evidence:
        failures.append(f"{contract_id}: missing expected evidence")
    return ContractRow(
        contract_id=contract_id,
        page_key=page_key,
        object_name=object_name,
        label=label,
        backend_capability=backend_capability,
        source_file=backend_capability.rsplit(".", 1)[0].replace(".", "/") + ".py",
        runtime_effect=runtime_effect,
        artifact_evidence=artifact_evidence,
        live_click_test="route_state_assertion_after_visible_clicks",
        status="connected" if artifact_evidence else "broken",
        observed=artifact_evidence or "missing expected artifact/effect",
    )


def _source_button(root: QWidget, source_key: str) -> QPushButton:
    for button in root.findChildren(QPushButton):
        if button.objectName() == "bioinformaticsDataSourceSelectPreviewButton" and str(button.property("sourceKey") or "") == source_key:
            return button
    raise LookupError(f"source button not found: {source_key}")


def _button(root: QWidget, object_name: str) -> QPushButton:
    button = root.findChild(QPushButton, object_name)
    if button is None:
        raise LookupError(f"button not found: {object_name}")
    return button


def _button_by_text(root: QWidget, text: str) -> QPushButton:
    for button in root.findChildren(QPushButton):
        if text in button.text():
            return button
    raise LookupError(f"button text not found: {text}")


def _table_text(table: QTableWidget, row: int, column: int) -> str:
    item = table.item(row, column)
    return item.text() if item is not None else ""


def _glob_evidence(project_root: Path, pattern: str) -> str:
    paths = sorted(project_root.glob(pattern), key=lambda path: path.stat().st_mtime if path.exists() else 0)
    return "; ".join(_relative(project_root, path) for path in paths[-3:])


def _relative(project_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def _shot(widget: QWidget, name: str, screenshot_dir: Path, screenshots: list[dict[str, str]]) -> None:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = screenshot_dir / f"{name}.png"
    widget.grab().save(str(path))
    screenshots.append({"name": name, "path": str(path.relative_to(REPO_ROOT))})


def _settle(app: QApplication | None, ms: int = 120) -> None:
    if app is not None:
        app.processEvents()
    QTest.qWait(ms)
    if app is not None:
        app.processEvents()


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        return ""


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# Bio C1 Batch 13 TCGA/GTEx Data Check Route Contract",
        "",
        f"- branch: `{payload.get('branch')}`",
        f"- head: `{payload.get('head')}`",
        f"- scope: {payload.get('scope')}",
        f"- rows: {summary.get('row_count')}; connected: {summary.get('connected')}; disabled: {summary.get('disabled')}; broken: {summary.get('broken')}",
        "",
        "## Screenshots",
        "",
    ]
    for shot in payload.get("screenshots", []):
        if isinstance(shot, dict):
            lines.append(f"- `{shot.get('name')}`: `{shot.get('path')}`")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| contract | page | button | status | backend | evidence |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("contract_id", "")),
                    str(row.get("page_key", "")),
                    f"`{row.get('object_name', '')}`",
                    str(row.get("status", "")),
                    str(row.get("backend_capability", "")),
                    str(row.get("artifact_evidence", "")).replace("\n", " ")[:260],
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
