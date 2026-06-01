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

from PySide6.QtWidgets import QApplication, QCheckBox, QLineEdit, QPushButton

import app.bioinformatics.workflow_pages as workflow_pages
from app.bioinformatics.pages.enrichment_page import EnrichmentPage
from app.bioinformatics.pages.survival_page import SurvivalPage
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.services.enrichment_service import EnrichmentService
from app.bioinformatics.services.survival_service import SurvivalService
from app.bioinformatics.workflow_pages import (
    BioinformaticsDataSourceWidget,
    BioinformaticsRecognitionWidget,
    BioinformaticsReadinessDashboardWidget,
    BioinformaticsReportViewerWidget,
    BioinformaticsResultsBrowserWidget,
    BioinformaticsStandardizedAssetsWidget,
)
from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
from app.shared.data_center.service import DataCenter
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets
from app.shared.task_center.service import TaskCenter


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH1.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH1.md"


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
    batch: str = "Batch 1: Bioinformatics Adapter Contract"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_bio_batch1_") as temp_name:
            audit_root = Path(temp_name)
            project = create_bioinformatics_project("Bio Batch 1 Contract", audit_root / "project")
            rows.extend(_audit_target_ia_routes(app, failures))
            rows.extend(_audit_data_source_requests(project, failures))
            rows.extend(_audit_data_check_artifacts(project, failures))
            rows.extend(_audit_analysis_task_gates(project, audit_root, failures))
            rows.extend(_audit_result_report_export(project, failures))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_bio_batch1.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Bioinformatics mature 7-step gated UI shell adapter and first-level runtime gate audit.",
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
    parser = argparse.ArgumentParser(description="Run Phase 1 Batch 1 Bioinformatics route contract live-click audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    return parser.parse_args(argv)


def _audit_target_ia_routes(app: QApplication, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget = BioinformaticsWorkspaceWidget()
    route_files = {
        "project_home": "app/bioinformatics/project_home.py",
        "data_source": "app/bioinformatics/workflow_pages.py",
        "data_check_preparation": "app/bioinformatics/workflow_pages.py",
        "group_design": "app/bioinformatics/workflow_pages.py",
        "analysis_tasks": "app/bioinformatics/workflow_pages.py",
        "result_report": "app/bioinformatics/workflow_pages.py",
        "report_export": "app/bioinformatics/workflow_pages.py",
        "settings_resources": "app/bioinformatics/workflow_pages.py",
        "project_logs_technical_details": "app/bioinformatics/workflow_pages.py",
    }
    try:
        by_page = {button.property("pageKey"): button for button in widget.findChildren(QPushButton, "bioinformaticsIANavItem")}
        for page_key in widget.target_ia_page_keys():
            widget.show_project_home()
            button = by_page[page_key]
            button.click()
            app.processEvents()
            observed = widget.current_target_page_key()
            ok = observed == page_key
            contract_id = f"BIO-IA-{page_key.upper().replace('-', '_')}"
            rows.append(
                _row(
                    contract_id=contract_id,
                    surface="Bioinformatics Target IA",
                    current_file=route_files.get(page_key, "app/bioinformatics/workspace.py"),
                    button=button,
                    runtime_effect=f"navigates to target IA page {page_key}",
                    artifact_evidence=f"current_target_page_key={observed}",
                    observed=f"expected={page_key}; observed={observed}",
                    status="connected" if ok else "broken",
                )
            )
            if not ok:
                failures.append(f"{contract_id}: expected target page {page_key}, observed {observed}")
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()
    return rows


def _audit_data_source_requests(project: object, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget = BioinformaticsDataSourceWidget()
    try:
        widget.refresh_project(project)
        for source_key in ("geo", "tcga", "gtex", "local_file"):
            button = _find_source_button(widget, source_key)
            button.click()
            request_path = widget.latest_data_source_request_path()
            ok = bool(request_path and request_path.exists())
            evidence = str(request_path) if request_path else "missing_data_source_request"
            if ok:
                payload = json.loads(Path(request_path).read_text(encoding="utf-8"))
                ok = payload.get("status") == "draft" and payload.get("internal_selection", {}).get("source_key") == source_key
                evidence = f"{request_path}; status={payload.get('status')}; source={payload.get('internal_selection', {}).get('source_key')}"
            contract_id = f"BIO-DATA-SOURCE-{source_key.upper()}"
            rows.append(
                _row(
                    contract_id=contract_id,
                    surface="Data Source",
                    current_file="app/bioinformatics/workflow_pages.py",
                    button=button,
                    runtime_effect="writes data_source_request draft manifest",
                    artifact_evidence=evidence,
                    observed="data_source_request_verified" if ok else "missing_or_invalid_data_source_request",
                    status="connected" if ok else "broken",
                )
            )
            if not ok:
                failures.append(f"{contract_id}: data source request artifact missing or invalid")
    finally:
        widget.close()
        widget.deleteLater()
    return rows


def _audit_data_check_artifacts(project: object, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    project_root = project.project_root
    raw_file = project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("gene\tcase_1\tcontrol_1\nTP53\t4\t1\nEGFR\t1\t3\n", encoding="utf-8")
    workflow_pages.register_acquisition(
        project_root,
        source_type="local_import",
        source_label="expression_matrix.tsv",
        strategy="reference",
        selected_paths=[raw_file],
    )

    recognition = BioinformaticsRecognitionWidget()
    readiness = BioinformaticsReadinessDashboardWidget()
    standardization = BioinformaticsStandardizedAssetsWidget()
    try:
        recognition.refresh_project(project)
        checkbox = recognition.findChild(QCheckBox)
        if checkbox is not None:
            checkbox.setChecked(True)
        recognition_button = _button_by_text(recognition, "开始识别")
        recognition_button.click()
        recognition_path = project_root / "logs" / "recognition" / "recognition_report.json"
        rows.append(
            _proof_row(
                contract_id="BIO-DATA-CHECK-RECOGNITION",
                surface="Data Check & Preparation",
                current_file="app/bioinformatics/workflow_pages.py",
                button=recognition_button,
                runtime_effect="runs recognition service for selected local asset",
                artifact_path=recognition_path,
                failures=failures,
            )
        )

        readiness.refresh_project(project)
        readiness_button = _find_button(readiness, "bioinformaticsRunDataCheckButton")
        readiness_button.click()
        readiness_path = Path(str(readiness._last_artifacts.get("readiness_path") or ""))
        rows.append(
            _proof_row(
                contract_id="BIO-DATA-CHECK-READINESS",
                surface="Data Check & Preparation",
                current_file="app/bioinformatics/workflow_pages.py",
                button=readiness_button,
                runtime_effect="runs readiness preflight and writes readiness artifact",
                artifact_path=readiness_path,
                failures=failures,
            )
        )

        standardization.refresh_project(project)
        standardization_button = _button_by_text(standardization, "生成标准化数据")
        standardization_button.click()
        registry_path = project_root / "manifests" / "standardized_assets_registry.json"
        manifest_path = project_root / "standardized_data" / "analysis_ready_assets" / "analysis_ready_manifest.json"
        repository_path = project_root / "standardized_data" / "repositories" / "repository_manifest.json"
        ok = registry_path.exists() and manifest_path.exists() and repository_path.exists()
        evidence = f"{registry_path}; {manifest_path}; {repository_path}"
        rows.append(
            _row(
                contract_id="BIO-DATA-CHECK-STANDARDIZATION",
                surface="Data Check & Preparation",
                current_file="app/bioinformatics/workflow_pages.py",
                button=standardization_button,
                runtime_effect="writes standardized asset registry, manifest, and repository manifest",
                artifact_evidence=evidence,
                observed="standardized_assets_verified" if ok else "missing_standardized_asset_artifact",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("BIO-DATA-CHECK-STANDARDIZATION: standardized asset artifacts missing")
    finally:
        for widget in (recognition, readiness, standardization):
            widget.close()
            widget.deleteLater()
    return rows


def _audit_analysis_task_gates(project: object, audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget = BioinformaticsWorkspaceWidget()
    try:
        widget.show_analysis_tasks(project)
        analysis_page = widget._analysis_task_page
        confirm_button = _find_button(analysis_page, "analysisTaskConfirmFormalDegParametersButton")
        run_button = _find_button(analysis_page, "analysisTaskRunFormalControlledDegButton")
        rows.append(_classify_gate_row("BIO-ANALYSIS-FORMAL-DEG-CONFIRM", "Analysis Tasks", confirm_button))
        rows.append(_classify_gate_row("BIO-ANALYSIS-FORMAL-DEG-RUN", "Analysis Tasks", run_button))

        enrichment_open = _find_button(analysis_page, "openEnrichmentGateButton")
        enrichment_open.click()
        rows.append(
            _row(
                contract_id="BIO-ANALYSIS-ENRICHMENT-OPEN",
                surface="Analysis Tasks",
                current_file="app/bioinformatics/workflow_pages.py",
                button=enrichment_open,
                runtime_effect="opens Enrichment preflight gate page",
                artifact_evidence=f"current_page={widget.current_page_object_name()}",
                observed=widget.current_page_object_name(),
                status="connected" if widget.current_page_object_name() == "bioinformaticsEnrichmentPage" else "broken",
            )
        )
        rows.extend(_run_enrichment_preflight(widget._enrichment_page, project, audit_root, failures))

        widget.show_analysis_tasks(project)
        survival_open = _find_button(widget._analysis_task_page, "openSurvivalClinicalGateButton")
        survival_open.click()
        rows.append(
            _row(
                contract_id="BIO-ANALYSIS-SURVIVAL-OPEN",
                surface="Analysis Tasks",
                current_file="app/bioinformatics/workflow_pages.py",
                button=survival_open,
                runtime_effect="opens Survival/Clinical preflight gate page",
                artifact_evidence=f"current_page={widget.current_page_object_name()}",
                observed=widget.current_page_object_name(),
                status="connected" if widget.current_page_object_name() == "bioinformaticsSurvivalPage" else "broken",
            )
        )
        rows.extend(_run_survival_preflight(widget._survival_page, project, audit_root, failures))
    finally:
        widget.close()
        widget.deleteLater()
    return rows


def _run_enrichment_preflight(page: EnrichmentPage, project: object, audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    disabled = _find_button(page, "enrichmentNextDisabledButton")
    rows.append(_classify_gate_row("BIO-ANALYSIS-ENRICHMENT-REPORT-GATE", "Enrichment", disabled))
    source = audit_root / "geo_differential_expression_preflight.json"
    source.write_text(
        json.dumps(
            {
                "project_id": "bio-batch1",
                "formal_deg_executed": False,
                "network_used": False,
                "preflight_items": [
                    {
                        "accession": "GSE1001",
                        "deg_result_files": ["deg.csv"],
                        "upregulated_gene_count": 12,
                        "downregulated_gene_count": 8,
                        "status": "ready_for_deg_runner",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    page._service = EnrichmentService(
        task_center=TaskCenter(audit_root / "enrichment_tasks.json"),
        data_center=DataCenter(audit_root / "enrichment_assets.json"),
        storage_root=audit_root,
    )
    path_input = page.findChild(QLineEdit, "enrichmentPreflightPathInput")
    run_button = _find_button(page, "runEnrichmentPreflightButton")
    if path_input is not None:
        path_input.setText(str(source))
    run_button.click()
    outputs = sorted((audit_root / "projects" / project.project_root.name / "bioinformatics" / "enrichment").glob("geo_enrichment_preflight_*.json"))
    ok = len(outputs) == 1
    rows.append(
        _row(
            contract_id="BIO-ANALYSIS-ENRICHMENT-RUN",
            surface="Enrichment",
            current_file="app/bioinformatics/pages/enrichment_page.py",
            button=run_button,
            runtime_effect="calls EnrichmentService and writes preflight artifact",
            artifact_evidence=str(outputs[0]) if outputs else "missing_enrichment_preflight_artifact",
            observed="enrichment_preflight_verified" if ok else "missing_enrichment_preflight_artifact",
            status="connected" if ok else "broken",
        )
    )
    if not ok:
        failures.append("BIO-ANALYSIS-ENRICHMENT-RUN: enrichment preflight artifact missing")
    return rows


def _run_survival_preflight(page: SurvivalPage, project: object, audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    disabled = _find_button(page, "survivalReportExportDisabledButton")
    rows.append(_classify_gate_row("BIO-ANALYSIS-SURVIVAL-REPORT-GATE", "Survival / Clinical", disabled))
    source = audit_root / "geo_cleaning_plan.json"
    source.write_text(
        json.dumps(
            {
                "project_id": "bio-batch1",
                "cleaning_executed": False,
                "cleaning_items": [
                    {
                        "accession": "GSE1001",
                        "expression_files": ["counts.tsv"],
                        "metadata_files": ["clinical.tsv"],
                        "survival_fields": ["os_time_days", "vital_status"],
                        "status": "ready_for_cleaning",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    page._service = SurvivalService(
        task_center=TaskCenter(audit_root / "survival_tasks.json"),
        data_center=DataCenter(audit_root / "survival_assets.json"),
        storage_root=audit_root,
    )
    path_input = page.findChild(QLineEdit, "survivalPreflightPathInput")
    run_button = _find_button(page, "runSurvivalPreflightButton")
    if path_input is not None:
        path_input.setText(str(source))
    run_button.click()
    outputs = sorted((audit_root / "projects" / project.project_root.name / "bioinformatics" / "survival").glob("geo_survival_preflight_*.json"))
    ok = len(outputs) == 1
    rows.append(
        _row(
            contract_id="BIO-ANALYSIS-SURVIVAL-RUN",
            surface="Survival / Clinical",
            current_file="app/bioinformatics/pages/survival_page.py",
            button=run_button,
            runtime_effect="calls SurvivalService and writes preflight artifact",
            artifact_evidence=str(outputs[0]) if outputs else "missing_survival_preflight_artifact",
            observed="survival_preflight_verified" if ok else "missing_survival_preflight_artifact",
            status="connected" if ok else "broken",
        )
    )
    if not ok:
        failures.append("BIO-ANALYSIS-SURVIVAL-RUN: survival preflight artifact missing")
    return rows


def _audit_result_report_export(project: object, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    results = BioinformaticsResultsBrowserWidget()
    report = BioinformaticsReportViewerWidget()
    try:
        results.refresh_project(project)
        refresh_results = _find_button(results, "resultReportRefreshButton")
        refresh_results.click()
        rows.append(
            _row(
                contract_id="BIO-RESULT-REPORT-REFRESH",
                surface="Result & Report",
                current_file="app/bioinformatics/workflow_pages.py",
                button=refresh_results,
                runtime_effect="loads result index and formal DEG gates",
                artifact_evidence=f"project_root={project.project_root}",
                observed="result_index_load_invoked",
                status="connected",
            )
        )

        report.refresh_project(project)
        draft_button = _find_button(report, "reportExportRefreshDraftButton")
        draft_button.click()
        markdown_path = project.project_root / "reports" / "project_analysis_report.md"
        manifest_path = project.project_root / "reports" / "project_report_manifest.json"
        ok = markdown_path.exists() and manifest_path.exists()
        rows.append(
            _row(
                contract_id="BIO-REPORT-EXPORT-DRAFT",
                surface="Report Export",
                current_file="app/bioinformatics/workflow_pages.py",
                button=draft_button,
                runtime_effect="generates markdown report draft and report manifest",
                artifact_evidence=f"{markdown_path}; {manifest_path}",
                observed="report_draft_verified" if ok else "missing_report_draft_or_manifest",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("BIO-REPORT-EXPORT-DRAFT: report draft artifact missing")
        export_button = _find_button(report, "reportReadyExportButton")
        rows.append(_classify_gate_row("BIO-REPORT-EXPORT-REPORT-READY-GATE", "Report Export", export_button))
    finally:
        for widget in (results, report):
            widget.close()
            widget.deleteLater()
    return rows


def _find_button(widget: object, object_name: str) -> QPushButton:
    button = widget.findChild(QPushButton, object_name)
    if button is None:
        raise AssertionError(f"Missing QPushButton objectName={object_name}")
    return button


def _find_source_button(widget: object, source_key: str) -> QPushButton:
    for button in widget.findChildren(QPushButton, "bioinformaticsDataSourceSelectPreviewButton"):
        if button.property("sourceKey") == source_key:
            return button
    raise AssertionError(f"Missing data source button sourceKey={source_key}")


def _button_by_text(widget: object, text: str) -> QPushButton:
    matches = [button for button in widget.findChildren(QPushButton) if button.text() == text]
    if len(matches) != 1:
        raise AssertionError(f"Expected one button with text={text!r}, found {len(matches)}")
    return matches[0]


def _proof_row(
    *,
    contract_id: str,
    surface: str,
    current_file: str,
    button: QPushButton,
    runtime_effect: str,
    artifact_path: Path,
    failures: list[str],
) -> ContractRow:
    ok = artifact_path.exists()
    if not ok:
        failures.append(f"{contract_id}: expected artifact missing at {artifact_path}")
    return _row(
        contract_id=contract_id,
        surface=surface,
        current_file=current_file,
        button=button,
        runtime_effect=runtime_effect,
        artifact_evidence=str(artifact_path),
        observed="artifact_verified" if ok else "missing_expected_artifact",
        status="connected" if ok else "broken",
    )


def _classify_gate_row(contract_id: str, surface: str, button: QPushButton) -> ContractRow:
    if button.isEnabled():
        status = "connected" if button.property("buttonBehavior") else "broken"
        observed = "enabled_button_has_behavior" if status == "connected" else "enabled_button_missing_behavior"
    else:
        status = "disabled" if button.property("disabledReason") else "broken"
        observed = "disabled_with_reason" if status == "disabled" else "disabled_without_reason"
    return _row(
        contract_id=contract_id,
        surface=surface,
        current_file="app/bioinformatics/workflow_pages.py",
        button=button,
        runtime_effect="formal runtime gate classified by enabled state and disabled reason",
        artifact_evidence=str(button.property("disabledReason") or "enabled"),
        observed=observed,
        status=status,
    )


def _row(
    *,
    contract_id: str,
    surface: str,
    current_file: str,
    button: QPushButton,
    runtime_effect: str,
    artifact_evidence: str,
    observed: str,
    status: str,
) -> ContractRow:
    return ContractRow(
        contract_id=contract_id,
        module="Bioinformatics",
        surface=surface,
        current_file=current_file,
        object_name=button.objectName(),
        label=" ".join(button.text().split()),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        disabled_reason=str(button.property("disabledReason") or ""),
        runtime_effect=runtime_effect,
        artifact_evidence=artifact_evidence,
        live_click_test="scripts/ui_route_contract_bio_batch1.py",
        status=status,
        observed=observed,
    )


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract Bio Batch 1",
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
        lines.append(
            "| {contract_id} | {surface} | `{object_name}` | {status} | `{button_behavior}` | {evidence} |".format(
                contract_id=_md(row["contract_id"]),
                surface=_md(row["surface"]),
                object_name=_md(row["object_name"]),
                status=_md(row["status"]),
                button_behavior=_md(row["button_behavior"]),
                evidence=_md(row["artifact_evidence"]),
            )
        )
    failures = summary.get("failures") or []
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    return "\n".join(lines) + "\n"


def _md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _git(*args: str) -> str:
    import subprocess

    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
