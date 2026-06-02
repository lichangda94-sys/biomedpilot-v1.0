from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.bioinformatics.pages.survival_page as survival_page_module
from PySide6.QtWidgets import QApplication, QLineEdit, QPlainTextEdit, QPushButton

from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.services.survival_service import SurvivalService
from app.shared.data_center.service import DataCenter
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets
from app.shared.task_center.service import TaskCenter


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH6_SURVIVAL.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH6_SURVIVAL.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_bio_batch6_survival"


@dataclass
class ContractRow:
    contract_id: str
    surface: str
    current_file: str
    object_name: str
    label: str
    enabled: bool
    button_behavior: str
    formal_action_enabled: bool
    runtime_effect: str
    artifact_evidence: str
    live_click_test: str
    status: str
    observed: str
    disabled_reason: str = ""
    batch: str = "Batch 6: Bioinformatics Survival/Clinical Gate"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    screenshots: list[dict[str, str]] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_bio_batch6_survival_") as temp_name:
            audit_root = Path(temp_name)
            project = create_bioinformatics_project("Bio Batch 6 Survival", audit_root / "project")
            source_path = _write_cleaning_plan(project.project_root)
            page = survival_page_module.SurvivalPage(
                project_id=project.project_root.name,
                service=SurvivalService(
                    task_center=TaskCenter(audit_root / "survival_tasks.json"),
                    data_center=DataCenter(audit_root / "survival_assets.json"),
                    storage_root=audit_root,
                ),
            )
            page.refresh_project(project)
            page.resize(1280, 960)
            page.show()
            app.processEvents()
            rows.extend(_audit_page_buttons(page, project.project_root, source_path, audit_root, failures))
            screenshots.extend(_capture_screenshots(app, page, args.screenshot_dir))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_bio_batch6_survival.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Bioinformatics survival/clinical input gate, backend dependency detection, KM/log-rank/Cox/risk score disabled gates, and clinical report-ready gate.",
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
    print(f"screenshot_dir={args.screenshot_dir}")
    print(f"rows={len(rows)}")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Bio Batch 6 Survival/Clinical route-contract audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _write_cleaning_plan(project_root: Path) -> Path:
    path = project_root / "analysis" / "cleaning" / "geo_cleaning_plan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "project_id": project_root.name,
                "cleaning_executed": False,
                "network_used": False,
                "cleaning_items": [
                    {
                        "accession": "TCGA-SURVIVAL-PREFLIGHT",
                        "expression_files": ["analysis/normalized/expression.tsv"],
                        "metadata_files": ["analysis/clinical/survival.tsv"],
                        "survival_fields": ["os_time_days", "vital_status", "age", "stage"],
                        "status": "ready_for_cleaning",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _audit_page_buttons(
    page: object,
    project_root: Path,
    source_path: Path,
    audit_root: Path,
    failures: list[str],
) -> list[ContractRow]:
    rows: list[ContractRow] = []

    back_called = {"value": False}
    page.back_requested.connect(lambda: back_called.__setitem__("value", True))
    back_button = _find_button(page, "survivalBackButton")
    back_button.click()
    rows.append(
        _button_row(
            "BIO-SURVIVAL-BACK",
            back_button,
            runtime_effect="emits back_requested signal to return to Analysis Tasks",
            artifact_evidence="signal=back_requested",
            status="connected" if back_called["value"] else "broken",
            observed=f"back_signal={back_called['value']}",
        )
    )
    if not back_called["value"]:
        failures.append("BIO-SURVIVAL-BACK: back_requested signal was not emitted")

    path_input = _find_line_edit(page, "survivalPreflightPathInput")
    choose_button = _find_button(page, "chooseSurvivalCleaningPlanButton")
    original_picker = survival_page_module.QFileDialog.getOpenFileName
    try:
        survival_page_module.QFileDialog.getOpenFileName = staticmethod(lambda *_args, **_kwargs: (str(source_path), "Cleaning plan (*.json)"))
        choose_button.click()
    finally:
        survival_page_module.QFileDialog.getOpenFileName = original_picker
    choose_ok = path_input.text() == str(source_path)
    rows.append(
        _button_row(
            "BIO-SURVIVAL-CHOOSE-CLEANING-PLAN",
            choose_button,
            runtime_effect="opens file picker and writes selected cleaning plan path into input",
            artifact_evidence=str(source_path),
            status="connected" if choose_ok else "broken",
            observed=f"path_input={path_input.text()}",
        )
    )
    if not choose_ok:
        failures.append("BIO-SURVIVAL-CHOOSE-CLEANING-PLAN: file picker selection did not update path input")

    run_button = _find_button(page, "runSurvivalPreflightButton")
    run_button.click()
    outputs = sorted((audit_root / "projects" / project_root.name / "bioinformatics" / "survival").glob("geo_survival_preflight_*.json"))
    output_payload = _read_json(outputs[0]) if outputs else {}
    run_ok = bool(outputs) and output_payload.get("survival_analysis_executed") is False
    rows.append(
        _button_row(
            "BIO-SURVIVAL-RUN-PREFLIGHT",
            run_button,
            runtime_effect="calls SurvivalService.create_preflight and writes geo_survival_preflight artifact",
            artifact_evidence=str(outputs[0]) if outputs else "missing_survival_preflight_artifact",
            status="connected" if run_ok else "broken",
            observed=f"survival_analysis_executed={output_payload.get('survival_analysis_executed')}",
        )
    )
    if not run_ok:
        failures.append("BIO-SURVIVAL-RUN-PREFLIGHT: expected preflight artifact was not generated")

    detect_button = _find_button(page, "detectSurvivalBackendButton")
    detect_button.click()
    detection_text = _find_plain_text(page, "survivalBackendDetectionText").toPlainText()
    detect_ok = (
        "lifelines:" in detection_text
        and "formal_survival_execution_enabled=False" in detection_text
        and "KM/log-rank/Cox/risk_score=disabled" in detection_text
        and "disabled_gate_basis=lifelines_or_r_survival_backend_required_plus_result_schema" in detection_text
    )
    rows.append(
        _button_row(
            "BIO-SURVIVAL-DETECT-BACKEND",
            detect_button,
            runtime_effect="calls SurvivalService.detect_backend_dependencies for lifelines/R survival capability snapshot",
            artifact_evidence=_compact_detection_evidence(detection_text),
            status="connected" if detect_ok else "broken",
            observed=_first_line(detection_text),
        )
    )
    if not detect_ok:
        failures.append("BIO-SURVIVAL-DETECT-BACKEND: backend detection output did not include expected survival gates")

    disabled_expectations = {
        "runKmCurveDisabledButton": (
            "BIO-SURVIVAL-KM-CURVE-GATE",
            "km_curve_executor_requires_lifelines_or_r_survival_backend_and_result_schema",
        ),
        "runLogRankDisabledButton": (
            "BIO-SURVIVAL-LOGRANK-GATE",
            "logrank_executor_requires_lifelines_or_r_survival_backend_event_schema_and_grouping_gate",
        ),
        "runCoxModelDisabledButton": (
            "BIO-SURVIVAL-COX-MODEL-GATE",
            "cox_model_executor_requires_lifelines_or_r_survival_backend_covariate_schema_and_hr_result_schema",
        ),
        "generateRiskScoreDisabledButton": (
            "BIO-SURVIVAL-RISK-SCORE-GATE",
            "risk_score_requires_validated_model_formula_training_validation_schema_and_report_gate",
        ),
        "survivalReportExportDisabledButton": (
            "BIO-SURVIVAL-CLINICAL-REPORT-READY-GATE",
            "survival_clinical_report_ready_requires_km_logrank_cox_risk_score_results_and_gate",
        ),
    }
    for object_name, (contract_id, disabled_reason) in disabled_expectations.items():
        button = _find_button(page, object_name)
        row = _disabled_button_row(contract_id, button, disabled_reason)
        rows.append(row)
        if row.status != "disabled":
            failures.append(f"{contract_id}: disabled reason mismatch or button enabled")
    return rows


def _button_row(
    contract_id: str,
    button: QPushButton,
    *,
    runtime_effect: str,
    artifact_evidence: str,
    status: str,
    observed: str,
) -> ContractRow:
    return ContractRow(
        contract_id=contract_id,
        surface="Survival / Clinical",
        current_file="app/bioinformatics/pages/survival_page.py",
        object_name=button.objectName(),
        label=button.text(),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        formal_action_enabled=bool(button.property("formalActionEnabled")),
        runtime_effect=runtime_effect,
        artifact_evidence=artifact_evidence,
        live_click_test="clicked",
        status=status,
        observed=observed,
    )


def _disabled_button_row(contract_id: str, button: QPushButton, expected_reason: str) -> ContractRow:
    actual_reason = str(button.property("disabledReason") or "")
    ok = not button.isEnabled() and actual_reason == expected_reason and bool(button.property("formalActionEnabled")) is False
    return ContractRow(
        contract_id=contract_id,
        surface="Survival / Clinical",
        current_file="app/bioinformatics/pages/survival_page.py",
        object_name=button.objectName(),
        label=button.text(),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        formal_action_enabled=bool(button.property("formalActionEnabled")),
        runtime_effect="disabled with explicit release gate reason",
        artifact_evidence=expected_reason,
        live_click_test="disabled_state_and_reason_verified",
        status="disabled" if ok else "broken",
        observed=f"enabled={button.isEnabled()}; disabledReason={actual_reason}",
        disabled_reason=actual_reason,
    )


def _capture_screenshots(app: QApplication, page: object, screenshot_dir: Path) -> list[dict[str, str]]:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    app.processEvents()
    path = screenshot_dir / "01_survival_clinical_gate.png"
    page.grab().save(str(path))
    try:
        display_path = str(path.relative_to(REPO_ROOT))
    except ValueError:
        display_path = str(path)
    return [{"page": "Bio Survival/Clinical gate", "path": display_path}]


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract: Bio Batch 6 Survival/Clinical",
        "",
        f"- branch: `{payload['branch']}`",
        f"- head: `{payload['head']}`",
        f"- scope: {payload['scope']}",
        f"- rows: {summary['row_count']}",
        f"- connected: {summary['connected']}",
        f"- disabled: {summary['disabled']}",
        f"- broken: {summary['broken']}",
        "",
        "## Screenshots",
        "",
    ]
    for screenshot in payload.get("screenshots", []):
        lines.append(f"- `{screenshot['path']}`")
    lines.extend(
        [
            "",
            "## Route Rows",
            "",
            "| Contract | Object | Status | Behavior | Evidence | Observed |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| {row['contract_id']} | `{row['object_name']}` | {row['status']} | "
            f"`{row['button_behavior']}` | {row['artifact_evidence']} | {row['observed']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _find_button(root: object, object_name: str) -> QPushButton:
    button = root.findChild(QPushButton, object_name)
    if button is None:
        raise AssertionError(f"Missing QPushButton {object_name}")
    return button


def _find_line_edit(root: object, object_name: str) -> QLineEdit:
    field = root.findChild(QLineEdit, object_name)
    if field is None:
        raise AssertionError(f"Missing QLineEdit {object_name}")
    return field


def _find_plain_text(root: object, object_name: str) -> QPlainTextEdit:
    field = root.findChild(QPlainTextEdit, object_name)
    if field is None:
        raise AssertionError(f"Missing QPlainTextEdit {object_name}")
    return field


def _read_json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _compact_detection_evidence(text: str) -> str:
    lines = [line for line in text.splitlines() if line.startswith(("status=", "lifelines:", "blockers=", "warnings="))]
    return "; ".join(lines)


def _first_line(text: str) -> str:
    return text.splitlines()[0] if text.splitlines() else ""


def _git(*args: str) -> str:
    import subprocess

    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
