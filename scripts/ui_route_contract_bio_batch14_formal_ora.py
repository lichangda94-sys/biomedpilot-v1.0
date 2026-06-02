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

import app.bioinformatics.pages.enrichment_page as enrichment_page_module
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QPlainTextEdit, QPushButton

from app.bioinformatics.deg_task_plan import DEG_PREFLIGHT_MANIFEST
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.services.enrichment_service import EnrichmentService
from app.shared.data_center.service import DataCenter
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets
from app.shared.task_center.service import TaskCenter


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH14_FORMAL_ORA.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH14_FORMAL_ORA.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_bio_batch14_formal_ora"


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
    batch: str = "Batch 14: Bioinformatics Formal ORA Positive Runtime"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    screenshots: list[dict[str, str]] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_bio_batch14_formal_ora_") as temp_name:
            audit_root = Path(temp_name)
            project = create_bioinformatics_project("Bio Batch 14 Formal ORA", audit_root / "project")
            source_path, gmt_path = _write_formal_ora_inputs(project.project_root)
            page = enrichment_page_module.EnrichmentPage(
                project_id=project.project_root.name,
                service=EnrichmentService(
                    task_center=TaskCenter(audit_root / "formal_ora_tasks.json"),
                    data_center=DataCenter(audit_root / "formal_ora_assets.json"),
                    storage_root=audit_root,
                ),
            )
            page.refresh_project(project)
            page.resize(1280, 1000)
            page.show()
            app.processEvents()
            QTest.qWait(120)
            screenshots.append(_capture(page, args.screenshot_dir, "01_formal_ora_inputs_ready"))
            rows.extend(_live_click_formal_ora(page, project.project_root, source_path, gmt_path, audit_root, failures))
            screenshots.append(_capture(page, args.screenshot_dir, "02_formal_ora_result_review"))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_bio_batch14_formal_ora.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Bioinformatics formal ORA positive runtime path from mature Enrichment page: DEG preflight selection, GMT selection, local ORA execution, result review, artifact registry, and GSEA/report gates.",
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
    parser = argparse.ArgumentParser(description="Run Bio Batch 14 formal ORA route-contract audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _write_formal_ora_inputs(project_root: Path) -> tuple[Path, Path]:
    deg_path = project_root / "analysis" / "deg" / "results" / "GSE6004_deg.csv"
    deg_path.parent.mkdir(parents=True, exist_ok=True)
    deg_path.write_text(
        "gene,log2FoldChange,padj\n"
        "TP53,2.8,0.001\n"
        "EGFR,-2.1,0.003\n"
        "MYC,1.7,0.02\n"
        "BRCA1,0.2,0.4\n"
        "PTEN,-0.3,0.5\n",
        encoding="utf-8",
    )
    source_path = project_root / DEG_PREFLIGHT_MANIFEST
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        json.dumps(
            {
                "project_id": project_root.name,
                "formal_deg_executed": True,
                "network_used": False,
                "preflight_items": [
                    {
                        "accession": "GSE6004",
                        "deg_result_files": ["analysis/deg/results/GSE6004_deg.csv"],
                        "upregulated_gene_count": 2,
                        "downregulated_gene_count": 1,
                        "status": "ready_for_enrichment_runner",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    gmt_path = project_root / "user_data" / "bioinformatics" / "gene_sets" / "batch14_pathways.gmt"
    gmt_path.parent.mkdir(parents=True, exist_ok=True)
    gmt_path.write_text(
        "DNA_DAMAGE\tlocal audit\tTP53\tBRCA1\tPTEN\n"
        "GROWTH_SIGNALING\tlocal audit\tEGFR\tMYC\n"
        "BACKGROUND_ONLY\tlocal audit\tBRCA1\tPTEN\n",
        encoding="utf-8",
    )
    return source_path, gmt_path


def _live_click_formal_ora(
    page: object,
    project_root: Path,
    source_path: Path,
    gmt_path: Path,
    audit_root: Path,
    failures: list[str],
) -> list[ContractRow]:
    rows: list[ContractRow] = []
    path_input = _find_line_edit(page, "enrichmentPreflightPathInput")
    choose_preflight = _find_button(page, "chooseEnrichmentPreflightButton")
    original_picker = enrichment_page_module.QFileDialog.getOpenFileName
    try:
        enrichment_page_module.QFileDialog.getOpenFileName = staticmethod(lambda *_args, **_kwargs: (str(source_path), "Differential expression preflight (*.json)"))
        choose_preflight.click()
    finally:
        enrichment_page_module.QFileDialog.getOpenFileName = original_picker
    choose_preflight_ok = path_input.text() == str(source_path)
    rows.append(
        _button_row(
            "BIO-FORMAL-ORA-CHOOSE-DEG-PREFLIGHT",
            choose_preflight,
            runtime_effect="selects DEG preflight JSON for formal ORA",
            artifact_evidence=str(source_path),
            status="connected" if choose_preflight_ok else "broken",
            observed=f"path_input={path_input.text()}",
        )
    )
    if not choose_preflight_ok:
        failures.append("BIO-FORMAL-ORA-CHOOSE-DEG-PREFLIGHT: file picker selection did not update preflight input")

    gene_set_input = _find_line_edit(page, "formalOraGeneSetPathInput")
    choose_gene_set = _find_button(page, "chooseFormalOraGeneSetButton")
    try:
        enrichment_page_module.QFileDialog.getOpenFileName = staticmethod(lambda *_args, **_kwargs: (str(gmt_path), "Gene set matrix transposed (*.gmt)"))
        choose_gene_set.click()
    finally:
        enrichment_page_module.QFileDialog.getOpenFileName = original_picker
    choose_gene_set_ok = gene_set_input.text() == str(gmt_path)
    rows.append(
        _button_row(
            "BIO-FORMAL-ORA-CHOOSE-GMT",
            choose_gene_set,
            runtime_effect="selects local GMT gene set file for formal ORA",
            artifact_evidence=str(gmt_path),
            status="connected" if choose_gene_set_ok else "broken",
            observed=f"gene_set_input={gene_set_input.text()}",
        )
    )
    if not choose_gene_set_ok:
        failures.append("BIO-FORMAL-ORA-CHOOSE-GMT: file picker selection did not update GMT input")

    run_button = _find_button(page, "runFormalOraButton")
    run_button.click()
    review_text = _find_plain_text(page, "formalOraResultReviewText").toPlainText()
    outputs = sorted((project_root / "results" / "enrichment").glob("formal-ora-*.json"))
    tables = sorted((project_root / "results" / "enrichment").glob("formal-ora-*.csv"))
    result_index = project_root / "results" / "summaries" / "result_index.json"
    result_payload = _read_json(outputs[0]) if outputs else {}
    run_ok = (
        bool(outputs)
        and bool(tables)
        and result_index.is_file()
        and result_payload.get("formal_ora_executed") is True
        and result_payload.get("formal_gsea_executed") is False
        and result_payload.get("network_used") is False
        and result_payload.get("database_download_executed") is False
    )
    rows.append(
        _button_row(
            "BIO-FORMAL-ORA-RUN",
            run_button,
            runtime_effect="calls EnrichmentService.run_formal_ora and writes JSON/CSV plus result index",
            artifact_evidence=f"json={outputs[0] if outputs else 'missing'}; csv={tables[0] if tables else 'missing'}; result_index={result_index}",
            status="connected" if run_ok else "broken",
            observed=f"formal_ora_executed={result_payload.get('formal_ora_executed')}; term_count={result_payload.get('term_count')}",
        )
    )
    if not run_ok:
        failures.append("BIO-FORMAL-ORA-RUN: expected formal ORA artifacts/result index were not generated")

    tasks = _read_json(audit_root / "formal_ora_tasks.json")
    assets = _read_json(audit_root / "formal_ora_assets.json")
    registry_ok = (
        (tasks.get("tasks") or [{}])[0].get("title") == "Formal ORA"
        and (assets.get("data_assets") or [{}])[0].get("data_type") == "formal_ora_result"
        and "formal_ora_executed=True" in review_text
    )
    rows.append(
        ContractRow(
            contract_id="BIO-FORMAL-ORA-REVIEW-AND-REGISTRY",
            surface="Enrichment",
            current_file="app/bioinformatics/pages/enrichment_page.py",
            object_name="formalOraResultReviewText",
            label="Formal ORA result review",
            enabled=True,
            button_behavior="renders_formal_ora_result_review_after_run",
            formal_action_enabled=False,
            runtime_effect="renders ORA result summary and proves TaskCenter/DataCenter registry writes",
            artifact_evidence=f"tasks={audit_root / 'formal_ora_tasks.json'}; assets={audit_root / 'formal_ora_assets.json'}",
            live_click_test="observed_after_run_click",
            status="connected" if registry_ok else "broken",
            observed=review_text.splitlines()[0] if review_text.splitlines() else "",
        )
    )
    if not registry_ok:
        failures.append("BIO-FORMAL-ORA-REVIEW-AND-REGISTRY: review text or registry records missing")

    disabled_expectations = {
        "runFormalOraGseaDisabledButton": (
            "BIO-FORMAL-GSEA-RUN-GATE",
            "formal_ora_gsea_executor_not_connected",
        ),
        "oraGseaPlotReportDisabledButton": (
            "BIO-FORMAL-ORA-PLOT-REPORT-GATE",
            "ora_gsea_plot_and_report_ready_gate_not_enabled",
        ),
        "enrichmentNextDisabledButton": (
            "BIO-FORMAL-ORA-CORRELATION-NEXT-GATE",
            "formal_ora_gsea_execution_and_correlation_gate_not_enabled",
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
        surface="Enrichment",
        current_file="app/bioinformatics/pages/enrichment_page.py",
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
        surface="Enrichment",
        current_file="app/bioinformatics/pages/enrichment_page.py",
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


def _capture(page: object, screenshot_dir: Path, name: str) -> dict[str, str]:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = screenshot_dir / f"{name}.png"
    page.grab().save(str(path))
    try:
        display_path = str(path.relative_to(REPO_ROOT))
    except ValueError:
        display_path = str(path)
    return {"page": name, "path": display_path}


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract: Bio Batch 14 Formal ORA",
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


def _git(*args: str) -> str:
    import subprocess

    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
