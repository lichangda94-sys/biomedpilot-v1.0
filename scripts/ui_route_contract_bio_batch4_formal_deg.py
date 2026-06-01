from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import warnings
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from app.bioinformatics.deg_engine.confirmation import CONFIRMATION_PATH
from app.bioinformatics.deg_engine.dependency_check import check_deg_backend_dependencies
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.workflow_pages import (
    BioinformaticsAnalysisTaskCenterWidget,
    BioinformaticsReportViewerWidget,
    BioinformaticsResultsBrowserWidget,
    load_result_index,
)
from app.shell.main_window import MainWindow
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH4_FORMAL_DEG.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH4_FORMAL_DEG.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260601_bio_batch4_formal_deg"


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
    batch: str = "Batch 4: Bioinformatics Formal DEG Positive Runtime"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    screenshots: list[dict[str, str]] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_bio_batch4_formal_deg_") as temp_name:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                audit_root = Path(temp_name)
                project = _create_formal_deg_project(audit_root)
                rows.extend(_run_formal_deg_positive_path(project, failures))
                screenshots.extend(_capture_screenshots(app, project, args.screenshot_dir))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_bio_batch4_formal_deg.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Bioinformatics Formal DEG positive runtime path: dependency detect, parameter confirmation, controlled run, result review, plot, report-ready package, and report export gate.",
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
    parser = argparse.ArgumentParser(description="Run Bio Batch 4 Formal DEG positive route-contract audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _create_formal_deg_project(audit_root: Path) -> object:
    project = create_bioinformatics_project("Bio Batch 4 Formal DEG", audit_root / "project")
    matrix = audit_root / "matrix.tsv"
    matrix.write_text(
        "gene\tcase1\tcase2\tctrl1\tctrl2\n"
        "TP53\t10\t12\t5\t6\n"
        "EGFR\t2\t2\t8\t9\n"
        "BRCA1\t20\t22\t19\t18\n",
        encoding="utf-8",
    )
    sample = audit_root / "sample.tsv"
    sample.write_text(
        "sample_id\tgroup\ncase1\tcase\ncase2\tcase\nctrl1\tcontrol\nctrl2\tcontrol\n",
        encoding="utf-8",
    )
    group = audit_root / "group.json"
    group.write_text(
        json.dumps(
            {
                "group_design": {
                    "sample_group_assignments": {
                        "case1": "case",
                        "case2": "case",
                        "ctrl1": "control",
                        "ctrl2": "control",
                    }
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_standardized_state(
        project.project_root,
        [
            _asset("expr", "raw_count_matrix", "expression_repository", matrix, value_type="count"),
            _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
            _asset("group", "group_design", "group_design_repository", group),
        ],
        default_expression="expr",
    )
    return project


def _run_formal_deg_positive_path(project: object, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    project_root = project.project_root
    dependency = check_deg_backend_dependencies()
    dependency_ok = dependency.get("status") == "passed"
    rows.append(
        ContractRow(
            contract_id="BIO-FORMAL-DEG-DEPENDENCY-DETECT",
            surface="Analysis Tasks",
            current_file="app/bioinformatics/deg_engine/dependency_check.py",
            object_name="check_deg_backend_dependencies",
            label="Detect formal DEG Python dependencies",
            enabled=True,
            button_behavior="detect_first_no_install",
            formal_action_enabled=False,
            runtime_effect="detects numpy/pandas/scipy/statsmodels for formal DEG activation",
            artifact_evidence=f"status={dependency.get('status')}; packages={','.join(dependency.get('packages', {}).keys())}",
            live_click_test="direct_service_call",
            status="connected" if dependency_ok else "broken",
            observed=str(dependency.get("blockers") or "passed"),
        )
    )
    if not dependency_ok:
        failures.append("BIO-FORMAL-DEG-DEPENDENCY-DETECT: dependency snapshot did not pass")

    task_page = BioinformaticsAnalysisTaskCenterWidget()
    try:
        task_page.refresh_project(project)
        confirm_button = _find_button(task_page, "analysisTaskConfirmFormalDegParametersButton")
        run_button = _find_button(task_page, "analysisTaskRunFormalControlledDegButton")

        confirm_initial = confirm_button.isEnabled()
        confirm_button.click()
        confirmation_path = project_root / CONFIRMATION_PATH
        confirmation = _read_json(confirmation_path)
        confirm_ok = confirm_initial and confirmation_path.exists() and confirmation.get("status") == "confirmed" and run_button.isEnabled()
        rows.append(
            _button_row(
                "BIO-FORMAL-DEG-PARAMETER-CONFIRM",
                "Analysis Tasks",
                "app/bioinformatics/workflow_pages.py",
                confirm_button,
                runtime_effect="writes formal DEG parameter confirmation and unlocks controlled run gate",
                artifact_evidence=str(confirmation_path),
                status="connected" if confirm_ok else "broken",
                observed=f"confirmation_status={confirmation.get('status')}; run_enabled={run_button.isEnabled()}",
            )
        )
        if not confirm_ok:
            failures.append("BIO-FORMAL-DEG-PARAMETER-CONFIRM: confirmation artifact missing or run gate not unlocked")

        run_button.click()
        result_index = load_result_index(project_root)
        formal_entries = [entry for entry in result_index.get("entries", []) or [] if entry.get("result_semantics") == "formal_computed_result"]
        result_id = str(formal_entries[0].get("result_id") or "") if formal_entries else ""
        result_table = project_root / str(formal_entries[0].get("output_artifacts", [{}])[0].get("path") or "") if formal_entries else project_root / "missing"
        run_ok = bool(formal_entries) and result_table.is_file()
        rows.append(
            _button_row(
                "BIO-FORMAL-DEG-CONTROLLED-RUN",
                "Analysis Tasks",
                "app/bioinformatics/workflow_pages.py",
                run_button,
                runtime_effect="runs controlled two-group formal DEG and writes result index v2",
                artifact_evidence=f"result_id={result_id}; result_table={result_table}; result_index={project_root / 'results' / 'summaries' / 'result_index.json'}",
                status="connected" if run_ok else "broken",
                observed=f"formal_result_count={len(formal_entries)}",
            )
        )
        if not run_ok:
            failures.append("BIO-FORMAL-DEG-CONTROLLED-RUN: formal result table or result index entry missing")
    finally:
        task_page.close()
        task_page.deleteLater()

    result_page = BioinformaticsResultsBrowserWidget()
    try:
        result_page.refresh_project(project)
        refresh_button = _find_button(result_page, "resultReportRefreshButton")
        refresh_button.click()
        rows.append(
            _button_row(
                "BIO-FORMAL-DEG-RESULT-REVIEW",
                "Result & Report",
                "app/bioinformatics/workflow_pages.py",
                refresh_button,
                runtime_effect="loads formal DEG result review table and provenance",
                artifact_evidence=f"selected_result_id={result_id}",
                status="connected" if result_id else "broken",
                observed="formal_review_loaded" if result_id else "missing_formal_result",
            )
        )

        csv_button = _find_button(result_page, "formalDegReviewExportCsvButton")
        csv_button.click()
        csv_exports = sorted((project_root / "results" / "exports" / "formal_deg_review").glob("*_review.csv"))
        rows.append(
            _button_row(
                "BIO-FORMAL-DEG-REVIEW-CSV-EXPORT",
                "Result & Report",
                "app/bioinformatics/workflow_pages.py",
                csv_button,
                runtime_effect="exports formal DEG review CSV without marking report-ready",
                artifact_evidence=str(csv_exports[0]) if csv_exports else "missing_review_csv",
                status="connected" if csv_exports else "broken",
                observed=f"csv_export_count={len(csv_exports)}",
            )
        )
        if not csv_exports:
            failures.append("BIO-FORMAL-DEG-REVIEW-CSV-EXPORT: review CSV missing")

        plot_button = _find_button(result_page, "formalDegPlotButton")
        plot_enabled_before_click = plot_button.isEnabled()
        plot_button.click()
        result_page.refresh_project(project)
        refreshed_index = load_result_index(project_root)
        refreshed_formal = next((entry for entry in refreshed_index.get("entries", []) or [] if entry.get("result_id") == result_id), {})
        plot_artifacts = [item for item in refreshed_formal.get("plot_artifacts", []) or [] if isinstance(item, dict)]
        plot_evidence = "; ".join(
            str(item.get("plot_id") or item.get("plot_type") or "plot_artifact")
            for item in plot_artifacts
        )
        rows.append(
            _button_row(
                "BIO-FORMAL-DEG-PLOT-ARTIFACT",
                "Result & Report",
                "app/bioinformatics/workflow_pages.py",
                plot_button,
                runtime_effect="creates formal DEG plot artifact from formal_computed_result",
                artifact_evidence=plot_evidence or "missing_plot_artifact",
                status="connected" if plot_enabled_before_click and plot_artifacts else "broken",
                observed=f"plot_artifact_count={len(plot_artifacts)}",
            )
        )
        if not plot_artifacts:
            failures.append("BIO-FORMAL-DEG-PLOT-ARTIFACT: plot artifact not registered")

        report_button = _find_button(result_page, "formalDegReportReadyButton")
        report_enabled_before_click = report_button.isEnabled()
        report_button.click()
        package_manifests = sorted((project_root / "report_package" / "formal_deg").glob("*/*/formal_deg_report_package_manifest.json"))
        rows.append(
            _button_row(
                "BIO-FORMAL-DEG-REPORT-READY-PACKAGE",
                "Result & Report",
                "app/bioinformatics/workflow_pages.py",
                report_button,
                runtime_effect="creates formal DEG report-ready package after plot/report gate passes",
                artifact_evidence=str(package_manifests[0]) if package_manifests else "missing_report_ready_package",
                status="connected" if report_enabled_before_click and package_manifests else "broken",
                observed=f"package_manifest_count={len(package_manifests)}",
            )
        )
        if not package_manifests:
            failures.append("BIO-FORMAL-DEG-REPORT-READY-PACKAGE: report-ready package manifest missing")
    finally:
        result_page.close()
        result_page.deleteLater()

    report_page = BioinformaticsReportViewerWidget()
    try:
        report_page.refresh_project(project)
        export_button = _find_button(report_page, "reportReadyExportButton")
        export_enabled_before_click = export_button.isEnabled()
        export_button.click()
        export_manifests = sorted((project_root / "report_package" / "formal_deg").glob("*/*/formal_deg_report_package_manifest.json"))
        rows.append(
            _button_row(
                "BIO-FORMAL-DEG-REPORT-EXPORT-GATE",
                "Report Export",
                "app/bioinformatics/workflow_pages.py",
                export_button,
                runtime_effect="exports formal DEG report-ready package only after formal gate passes",
                artifact_evidence=str(export_manifests[-1]) if export_manifests else "missing_report_export_manifest",
                status="connected" if export_enabled_before_click and export_manifests else "broken",
                observed=f"report_export_manifest_count={len(export_manifests)}",
            )
        )
        if not export_manifests:
            failures.append("BIO-FORMAL-DEG-REPORT-EXPORT-GATE: report export manifest missing")
    finally:
        report_page.close()
        report_page.deleteLater()

    return rows


def _capture_screenshots(app: QApplication, project: object, screenshot_dir: Path) -> list[dict[str, str]]:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    window = MainWindow()
    window.resize(1600, 1000)
    screenshots: list[dict[str, str]] = []
    try:
        window.show()
        app.processEvents()
        QTest.qWait(80)
        window._welcome_page.enter_workspace()
        app.processEvents()
        QTest.qWait(80)
        window.show_bioinformatics()
        window._bioinformatics_page.show_analysis_tasks(project)
        _shot(window, "01_analysis_tasks_formal_deg_ready", screenshot_dir, screenshots)

        window._bioinformatics_page.show_results_browser(project.project_root)
        _shot(window, "02_result_review_formal_deg", screenshot_dir, screenshots)

        window._bioinformatics_page._results_browser_page.refresh_project(project)
        plot_button = _find_button(window._bioinformatics_page._results_browser_page, "formalDegPlotButton")
        if plot_button.isEnabled():
            plot_button.click()
            window._bioinformatics_page._results_browser_page.refresh_project(project)
        _shot(window, "03_result_review_plot_gate", screenshot_dir, screenshots)

        window._bioinformatics_page.show_report_viewer(project.project_root)
        _shot(window, "04_report_export_formal_deg_ready", screenshot_dir, screenshots)
    finally:
        window.close()
        window.deleteLater()
    return screenshots


def _shot(window: MainWindow, name: str, screenshot_dir: Path, screenshots: list[dict[str, str]]) -> None:
    app = QApplication.instance()
    if app is not None:
        app.processEvents()
        QTest.qWait(80)
    path = screenshot_dir / f"{name}.png"
    window.grab().save(str(path))
    screenshots.append({"name": name, "path": str(path), "workspace": window.current_workspace_key()})


def _asset(asset_id: str, asset_type: str, repository: str, path: Path, *, value_type: str = "", gene_id_type: str = "symbol") -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "asset_role": "expression_matrix" if "expression" in asset_type or "count" in asset_type else asset_type,
        "repository": repository,
        "path": str(path),
        "file_path": str(path),
        "validation_status": "passed",
        "analysis_ready": True,
        "expression_value_type": value_type,
        "gene_id_type": gene_id_type,
    }


def _write_standardized_state(root: Path, assets: list[dict[str, object]], *, default_expression: str) -> None:
    selection = {"expression": {"asset_id": default_expression, "selection_state": "user_confirmed"}}
    repository_manifest = {
        "schema_version": "biomedpilot.repository_manifest.v1",
        "assets": assets,
        "default_asset_selection": selection,
    }
    registry = {
        "schema_version": "biomedpilot.standardized_assets_registry.v2",
        "assets": assets,
        "default_asset_selection": selection,
    }
    repo_path = root / "standardized_data" / "repositories" / "repository_manifest.json"
    registry_path = root / "manifests" / "standardized_assets_registry.json"
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    repo_path.write_text(json.dumps(repository_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")


def _button_row(
    contract_id: str,
    surface: str,
    current_file: str,
    button: QPushButton,
    *,
    runtime_effect: str,
    artifact_evidence: str,
    status: str,
    observed: str,
) -> ContractRow:
    return ContractRow(
        contract_id=contract_id,
        surface=surface,
        current_file=current_file,
        object_name=button.objectName(),
        label=button.text().replace("\n", " / "),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        formal_action_enabled=bool(button.property("formalActionEnabled")),
        runtime_effect=runtime_effect,
        artifact_evidence=artifact_evidence,
        live_click_test="button.click()",
        status=status,
        observed=observed,
    )


def _find_button(widget: object, object_name: str) -> QPushButton:
    button = widget.findChild(QPushButton, object_name)
    if button is None:
        raise AssertionError(f"Missing QPushButton objectName={object_name}")
    return button


def _read_json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    assert isinstance(summary, dict)
    lines = [
        "# UI Route Contract Bio Batch 4: Formal DEG",
        "",
        f"- Created: `{payload['created_at']}`",
        f"- Branch: `{payload['branch']}`",
        f"- HEAD: `{payload['head']}`",
        f"- Scope: {payload['scope']}",
        "",
        "## Summary",
        "",
        f"- Rows: {summary['row_count']}",
        f"- Connected: {summary['connected']}",
        f"- Disabled with reason: {summary['disabled']}",
        f"- Broken: {summary['broken']}",
        "",
        "## Rows",
        "",
        "| Contract | Surface | Object | Status | Behavior | Evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        assert isinstance(row, dict)
        lines.append(
            "| {contract_id} | {surface} | `{object_name}` | {status} | `{button_behavior}` | {artifact_evidence} |".format(
                contract_id=_md(row.get("contract_id", "")),
                surface=_md(row.get("surface", "")),
                object_name=_md(row.get("object_name", "")),
                status=_md(row.get("status", "")),
                button_behavior=_md(row.get("button_behavior", "")),
                artifact_evidence=_md(row.get("artifact_evidence", "")),
            )
        )
    lines.extend(["", "## Screenshots", ""])
    for shot in payload.get("screenshots", []):
        assert isinstance(shot, dict)
        lines.append(f"- `{Path(str(shot.get('path'))).name}`: {shot.get('workspace', '')}")
    return "\n".join(lines) + "\n"


def _git(*args: str) -> str:
    try:
        completed = subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, text=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return completed.stdout.strip()


def _md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " / ")


if __name__ == "__main__":
    raise SystemExit(main())
