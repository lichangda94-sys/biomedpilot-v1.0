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

from PySide6.QtWidgets import QApplication, QPushButton

from app.bioinformatics.deg_engine.confirmation import CONFIRMATION_PATH
from app.bioinformatics.reports.readiness import evaluate_report_ready_gate
from app.bioinformatics.results.project_results import load_result_index
from app.bioinformatics.services.enrichment_service import EnrichmentService
from app.bioinformatics.services.survival_service import SurvivalService
from app.bioinformatics.workflow_pages import (
    BioinformaticsAnalysisTaskCenterWidget,
    BioinformaticsReportViewerWidget,
    BioinformaticsResultsBrowserWidget,
)
from app.shared.data_center.service import DataCenter
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets
from app.shared.task_center.service import TaskCenter
from scripts.ui_route_contract_bio_batch4_formal_deg import _create_formal_deg_project


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH7_REPORT_EXPORT.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH7_REPORT_EXPORT.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_bio_batch7_report_export"


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
    batch: str = "Batch 7: Bioinformatics Result & Report / Report Export"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    screenshots: list[dict[str, str]] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_bio_batch7_report_export_") as temp_name:
            audit_root = Path(temp_name)
            project = _create_formal_deg_project(audit_root)
            project_root = project.project_root
            rows.extend(_create_formal_deg_runtime(project, failures))
            rows.extend(_create_boundary_preflights(project_root, audit_root, failures))
            result_page = BioinformaticsResultsBrowserWidget()
            report_page = BioinformaticsReportViewerWidget()
            try:
                result_page.resize(1280, 980)
                report_page.resize(1280, 980)
                result_page.show()
                report_page.show()
                app.processEvents()
                rows.extend(_audit_result_page(result_page, report_page, project_root, failures))
                screenshots.extend(_capture_screenshots(app, result_page, report_page, args.screenshot_dir))
            finally:
                for widget in (result_page, report_page):
                    widget.close()
                    widget.deleteLater()
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_bio_batch7_report_export.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Bioinformatics Result & Report and Report Export cross-result gate: Formal DEG positive path, report draft, report-ready package export, and ORA/GSEA/Survival boundary proof.",
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
    parser = argparse.ArgumentParser(description="Run Bio Batch 7 Result & Report / Report Export route-contract audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _create_formal_deg_runtime(project: object, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    project_root = project.project_root
    task_page = BioinformaticsAnalysisTaskCenterWidget()
    try:
        task_page.refresh_project(project)
        confirm_button = _find_button(task_page, "analysisTaskConfirmFormalDegParametersButton")
        run_button = _find_button(task_page, "analysisTaskRunFormalControlledDegButton")
        confirm_button.click()
        confirmation_path = project_root / CONFIRMATION_PATH
        rows.append(
            _button_row(
                "BIO-REPORT-X-FORMAL-DEG-CONFIRM",
                "Analysis Tasks",
                "app/bioinformatics/workflow_pages.py",
                confirm_button,
                runtime_effect="writes formal DEG parameter confirmation before report/export audit",
                artifact_evidence=str(confirmation_path),
                status="connected" if confirmation_path.is_file() and run_button.isEnabled() else "broken",
                observed=f"confirmation_exists={confirmation_path.is_file()}; run_enabled={run_button.isEnabled()}",
            )
        )
        if not confirmation_path.is_file() or not run_button.isEnabled():
            failures.append("BIO-REPORT-X-FORMAL-DEG-CONFIRM: confirmation artifact missing or run gate locked")
        run_button.click()
        result_index = load_result_index(project_root)
        formal_entries = [entry for entry in result_index.get("entries", []) or [] if entry.get("result_semantics") == "formal_computed_result"]
        rows.append(
            _button_row(
                "BIO-REPORT-X-FORMAL-DEG-RUN",
                "Analysis Tasks",
                "app/bioinformatics/workflow_pages.py",
                run_button,
                runtime_effect="runs formal controlled DEG and writes result index entry",
                artifact_evidence=f"formal_entry_count={len(formal_entries)}",
                status="connected" if formal_entries else "broken",
                observed=f"result_ids={','.join(str(item.get('result_id') or '') for item in formal_entries)}",
            )
        )
        if not formal_entries:
            failures.append("BIO-REPORT-X-FORMAL-DEG-RUN: formal DEG result index entry missing")
    finally:
        task_page.close()
        task_page.deleteLater()
    return rows


def _create_boundary_preflights(project_root: Path, audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    enrichment_source = project_root / "analysis" / "deg" / "preflight" / "batch7_enrichment_source.json"
    enrichment_source.parent.mkdir(parents=True, exist_ok=True)
    enrichment_source.write_text(
        json.dumps(
            {
                "project_id": project_root.name,
                "formal_deg_executed": False,
                "preflight_items": [
                    {
                        "accession": "GSE6004",
                        "deg_result_files": ["results/formal_deg.csv"],
                        "upregulated_gene_count": 12,
                        "downregulated_gene_count": 9,
                        "status": "ready_for_deg_runner",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    enrichment = EnrichmentService(
        task_center=TaskCenter(audit_root / "boundary_enrichment_tasks.json"),
        data_center=DataCenter(audit_root / "boundary_enrichment_assets.json"),
        storage_root=audit_root,
    ).create_preflight(project_id=project_root.name, differential_expression_path=str(enrichment_source))
    rows.append(
        ContractRow(
            contract_id="BIO-REPORT-X-ENRICHMENT-PREFLIGHT-BOUNDARY",
            surface="Boundary Services",
            current_file="app/bioinformatics/services/enrichment_service.py",
            object_name="EnrichmentService.create_preflight",
            label="Create ORA/GSEA preflight boundary artifact",
            enabled=True,
            button_behavior="direct_service_call_boundary_fixture",
            formal_action_enabled=False,
            runtime_effect="generates enrichment preflight artifact without result index or report-ready promotion",
            artifact_evidence=enrichment.output_path,
            live_click_test="direct_service_call",
            status="connected" if enrichment.success else "broken",
            observed=f"enrichment_executed={enrichment.details.get('enrichment_executed')}; database_download_executed={enrichment.details.get('database_download_executed')}",
        )
    )
    if not enrichment.success:
        failures.append("BIO-REPORT-X-ENRICHMENT-PREFLIGHT-BOUNDARY: enrichment boundary preflight failed")

    survival_source = project_root / "analysis" / "cleaning" / "batch7_survival_cleaning_plan.json"
    survival_source.parent.mkdir(parents=True, exist_ok=True)
    survival_source.write_text(
        json.dumps(
            {
                "project_id": project_root.name,
                "cleaning_executed": False,
                "cleaning_items": [
                    {
                        "accession": "TCGA-BATCH7",
                        "expression_files": ["expression.tsv"],
                        "metadata_files": ["clinical.tsv"],
                        "survival_fields": ["os_time_days", "vital_status"],
                        "status": "ready_for_cleaning",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    survival = SurvivalService(
        task_center=TaskCenter(audit_root / "boundary_survival_tasks.json"),
        data_center=DataCenter(audit_root / "boundary_survival_assets.json"),
        storage_root=audit_root,
    ).create_preflight(project_id=project_root.name, cleaning_plan_path=str(survival_source))
    rows.append(
        ContractRow(
            contract_id="BIO-REPORT-X-SURVIVAL-PREFLIGHT-BOUNDARY",
            surface="Boundary Services",
            current_file="app/bioinformatics/services/survival_service.py",
            object_name="SurvivalService.create_preflight",
            label="Create survival preflight boundary artifact",
            enabled=True,
            button_behavior="direct_service_call_boundary_fixture",
            formal_action_enabled=False,
            runtime_effect="generates survival preflight artifact without KM/Cox/log-rank/risk score or report-ready promotion",
            artifact_evidence=survival.output_path,
            live_click_test="direct_service_call",
            status="connected" if survival.success else "broken",
            observed=f"survival_analysis_executed={survival.details.get('survival_analysis_executed')}",
        )
    )
    if not survival.success:
        failures.append("BIO-REPORT-X-SURVIVAL-PREFLIGHT-BOUNDARY: survival boundary preflight failed")
    return rows


def _audit_result_page(
    result_page: BioinformaticsResultsBrowserWidget,
    report_page: BioinformaticsReportViewerWidget,
    project_root: Path,
    failures: list[str],
) -> list[ContractRow]:
    rows: list[ContractRow] = []
    result_page.refresh_project(project_root)
    refresh_button = _find_button(result_page, "resultReportRefreshButton")
    refresh_button.click()
    result_index = load_result_index(project_root)
    entries = [entry for entry in result_index.get("entries", []) or [] if isinstance(entry, dict)]
    formal_entries = [entry for entry in entries if entry.get("result_semantics") == "formal_computed_result"]
    enrichment_entries = [entry for entry in entries if str(entry.get("analysis_type") or "") in {"enrichment", "gsea"}]
    survival_entries = [entry for entry in entries if str(entry.get("analysis_type") or "") in {"survival", "clinical_association"}]
    refresh_ok = bool(formal_entries) and not enrichment_entries and not survival_entries
    rows.append(
        _button_row(
            "BIO-RESULT-REPORT-REFRESH-CROSS-GATE",
            "Result & Report",
            "app/bioinformatics/workflow_pages.py",
            refresh_button,
            runtime_effect="loads result index and keeps ORA/GSEA/Survival preflight artifacts out of formal result rows",
            artifact_evidence=f"formal={len(formal_entries)}; enrichment={len(enrichment_entries)}; survival={len(survival_entries)}",
            status="connected" if refresh_ok else "broken",
            observed=f"entry_count={len(entries)}",
        )
    )
    if not refresh_ok:
        failures.append("BIO-RESULT-REPORT-REFRESH-CROSS-GATE: unexpected result-index promotion")

    for object_name, contract_id, pattern in (
        ("formalDegReviewExportTsvButton", "BIO-RESULT-FORMAL-DEG-REVIEW-TSV-EXPORT", "*_review.tsv"),
        ("formalDegReviewExportCsvButton", "BIO-RESULT-FORMAL-DEG-REVIEW-CSV-EXPORT", "*_review.csv"),
    ):
        button = _find_button(result_page, object_name)
        button.click()
        exports = sorted((project_root / "results" / "exports" / "formal_deg_review").glob(pattern))
        rows.append(
            _button_row(
                contract_id,
                "Result & Report",
                "app/bioinformatics/workflow_pages.py",
                button,
                runtime_effect="exports formal DEG review table without report-ready promotion",
                artifact_evidence=str(exports[-1]) if exports else f"missing_{pattern}",
                status="connected" if exports else "broken",
                observed=f"export_count={len(exports)}",
            )
        )
        if not exports:
            failures.append(f"{contract_id}: export artifact missing")

    plot_button = _find_button(result_page, "formalDegPlotButton")
    plot_enabled = plot_button.isEnabled()
    plot_button.click()
    result_page.refresh_project(project_root)
    result_index = load_result_index(project_root)
    selected = _latest_formal_entry(result_index)
    plot_artifacts = [item for item in selected.get("plot_artifacts", []) or [] if isinstance(item, dict)]
    rows.append(
        _button_row(
            "BIO-RESULT-FORMAL-DEG-PLOT-GATE",
            "Result & Report",
            "app/bioinformatics/workflow_pages.py",
            plot_button,
            runtime_effect="creates formal DEG plot artifact and keeps report-ready scope formal-only",
            artifact_evidence=f"plot_artifact_count={len(plot_artifacts)}",
            status="connected" if plot_enabled and plot_artifacts else "broken",
            observed="; ".join(str(item.get("plot_type") or item.get("plot_id") or "plot") for item in plot_artifacts),
        )
    )
    if not plot_artifacts:
        failures.append("BIO-RESULT-FORMAL-DEG-PLOT-GATE: formal DEG plot artifact missing")

    report_ready_button = _find_button(result_page, "formalDegReportReadyButton")
    report_ready_enabled = report_ready_button.isEnabled()
    report_ready_button.click()
    result_page.refresh_project(project_root)
    package_manifests = sorted((project_root / "report_package" / "formal_deg").glob("*/*/formal_deg_report_package_manifest.json"))
    latest_manifest = _read_json(package_manifests[-1]) if package_manifests else {}
    package_ok = (
        report_ready_enabled
        and latest_manifest.get("status") == "formal_deg_report_ready_package_created"
        and latest_manifest.get("section_scope") == "formal_deg_only"
        and latest_manifest.get("gsea_enabled") is False
        and latest_manifest.get("survival_enabled") is False
        and latest_manifest.get("clinical_conclusion_enabled") is False
    )
    rows.append(
        _button_row(
            "BIO-RESULT-FORMAL-DEG-REPORT-READY-PACKAGE",
            "Result & Report",
            "app/bioinformatics/workflow_pages.py",
            report_ready_button,
            runtime_effect="creates formal DEG report-ready package only after formal DEG plot/report gate passes",
            artifact_evidence=str(package_manifests[-1]) if package_manifests else "missing_formal_deg_report_package_manifest",
            status="connected" if package_ok else "broken",
            observed=f"section_scope={latest_manifest.get('section_scope')}; gsea={latest_manifest.get('gsea_enabled')}; survival={latest_manifest.get('survival_enabled')}; clinical={latest_manifest.get('clinical_conclusion_enabled')}",
        )
    )
    if not package_ok:
        failures.append("BIO-RESULT-FORMAL-DEG-REPORT-READY-PACKAGE: package scope or manifest invalid")

    continue_called = {"value": False}
    result_page.continue_requested.connect(lambda _root: continue_called.__setitem__("value", True))
    continue_button = _find_button(result_page, "resultReportContinueReportExportButton")
    continue_button.click()
    rows.append(
        _button_row(
            "BIO-RESULT-CONTINUE-REPORT-EXPORT",
            "Result & Report",
            "app/bioinformatics/workflow_pages.py",
            continue_button,
            runtime_effect="emits report export navigation only when at least one result exists",
            artifact_evidence="signal=continue_requested",
            status="connected" if continue_called["value"] else "broken",
            observed=f"continue_signal={continue_called['value']}",
        )
    )
    if not continue_called["value"]:
        failures.append("BIO-RESULT-CONTINUE-REPORT-EXPORT: continue signal missing")

    report_page.refresh_project(project_root)
    draft_button = _find_button(report_page, "reportExportRefreshDraftButton")
    draft_button.click()
    markdown_path = project_root / "reports" / "project_analysis_report.md"
    manifest_path = project_root / "reports" / "project_report_manifest.json"
    manifest = _read_json(manifest_path)
    draft_ok = markdown_path.is_file() and manifest_path.is_file()
    rows.append(
        _button_row(
            "BIO-REPORT-EXPORT-DRAFT-CROSS-GATE",
            "Report Export",
            "app/bioinformatics/workflow_pages.py",
            draft_button,
            runtime_effect="generates Markdown draft and report manifest with semantic gate snapshot",
            artifact_evidence=f"{markdown_path}; {manifest_path}",
            status="connected" if draft_ok else "broken",
            observed=f"included_result_ids={manifest.get('included_result_ids')}",
        )
    )
    if not draft_ok:
        failures.append("BIO-REPORT-EXPORT-DRAFT-CROSS-GATE: report draft or manifest missing")

    export_button = _find_button(report_page, "reportReadyExportButton")
    report_page.refresh_project(project_root)
    export_enabled = export_button.isEnabled()
    export_button.click()
    export_manifests = sorted((project_root / "report_package" / "formal_deg").glob("*/*/formal_deg_report_package_manifest.json"))
    export_manifest = _read_json(export_manifests[-1]) if export_manifests else {}
    export_ok = (
        export_enabled
        and export_manifest.get("status") == "formal_deg_report_ready_package_created"
        and export_manifest.get("section_scope") == "formal_deg_only"
        and export_manifest.get("gsea_enabled") is False
        and export_manifest.get("survival_enabled") is False
        and export_manifest.get("clinical_conclusion_enabled") is False
        and "GSEA、survival、clinical report-ready 仍保持 gate" in report_page.status_message()
    )
    rows.append(
        _button_row(
            "BIO-REPORT-EXPORT-FORMAL-DEG-PACKAGE-GATE",
            "Report Export",
            "app/bioinformatics/workflow_pages.py",
            export_button,
            runtime_effect="exports formal DEG report-ready package while preserving ORA/GSEA/Survival/clinical gates",
            artifact_evidence=str(export_manifests[-1]) if export_manifests else "missing_report_export_manifest",
            status="connected" if export_ok else "broken",
            observed=f"enabled={export_enabled}; status_message={report_page.status_message()}",
        )
    )
    if not export_ok:
        failures.append("BIO-REPORT-EXPORT-FORMAL-DEG-PACKAGE-GATE: export gate did not preserve formal-only scope")

    generic_gate = evaluate_report_ready_gate(project_root)
    generic_ok = generic_gate.get("status") == "eligible_for_internal_report" and generic_gate.get("included_result_ids") == export_manifest.get("included_result_ids")
    rows.append(
        ContractRow(
            contract_id="BIO-REPORT-EXPORT-GENERIC-GATE-SNAPSHOT",
            surface="Report Export",
            current_file="app/bioinformatics/reports/readiness.py",
            object_name="evaluate_report_ready_gate",
            label="Evaluate generic report-ready gate after formal package",
            enabled=True,
            button_behavior="direct_gate_snapshot",
            formal_action_enabled=False,
            runtime_effect="confirms only report-ready eligible formal DEG result is included in generic report-ready snapshot",
            artifact_evidence=f"status={generic_gate.get('status')}; included={generic_gate.get('included_result_ids')}",
            live_click_test="direct_gate_call",
            status="connected" if generic_ok else "broken",
            observed=f"blockers={generic_gate.get('blockers')}",
        )
    )
    if not generic_ok:
        failures.append("BIO-REPORT-EXPORT-GENERIC-GATE-SNAPSHOT: generic report-ready gate did not match formal package scope")
    return rows


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
        label=button.text(),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        formal_action_enabled=bool(button.property("formalActionEnabled")),
        runtime_effect=runtime_effect,
        artifact_evidence=artifact_evidence,
        live_click_test="clicked",
        status=status,
        observed=observed,
        disabled_reason=str(button.property("disabledReason") or ""),
    )


def _capture_screenshots(
    app: QApplication,
    result_page: BioinformaticsResultsBrowserWidget,
    report_page: BioinformaticsReportViewerWidget,
    screenshot_dir: Path,
) -> list[dict[str, str]]:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    app.processEvents()
    captures = [
        ("Result & Report", result_page, screenshot_dir / "01_result_report_cross_gate.png"),
        ("Report Export", report_page, screenshot_dir / "02_report_export_formal_only_gate.png"),
    ]
    rows: list[dict[str, str]] = []
    for label, widget, path in captures:
        widget.grab().save(str(path))
        try:
            display_path = str(path.relative_to(REPO_ROOT))
        except ValueError:
            display_path = str(path)
        rows.append({"page": label, "path": display_path})
    return rows


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract: Bio Batch 7 Result & Report / Report Export",
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


def _latest_formal_entry(result_index: dict[str, object]) -> dict[str, object]:
    entries = [entry for entry in result_index.get("entries", []) or [] if isinstance(entry, dict) and entry.get("result_semantics") == "formal_computed_result"]
    return entries[-1] if entries else {}


def _find_button(root: object, object_name: str) -> QPushButton:
    button = root.findChild(QPushButton, object_name)
    if button is None:
        raise AssertionError(f"Missing QPushButton {object_name}")
    return button


def _read_json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _git(*args: str) -> str:
    import subprocess

    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
