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

from app.meta_analysis.project_workspace import create_meta_analysis_project
from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService
from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH3.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH3.md"


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
    batch: str = "Batch 3: Meta Analysis Adapter Contract"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_meta_batch3_") as temp_name:
            audit_root = Path(temp_name)
            project = create_meta_analysis_project("Meta Batch 3 Contract", audit_root / "project")
            rows.extend(_audit_target_ia_routes(app, failures))
            rows.extend(_audit_question_and_search_gates(project.project_root, failures))
            rows.extend(_audit_confirmed_search_gate(audit_root, failures))
            rows.extend(_audit_import_dedup_gates(project.project_root, failures))
            rows.extend(_audit_later_stage_gates(project.project_root, failures))
            rows.extend(_audit_report_export_gates(project.project_root))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_meta_batch3.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Meta Analysis UIShell mature target IA, adapter gates, and first-level runtime artifact audit.",
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
    parser = argparse.ArgumentParser(description="Run Phase 1 Batch 3 Meta route contract live-click audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    return parser.parse_args(argv)


def _audit_target_ia_routes(app: QApplication, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget = MetaAnalysisWorkspaceWidget()
    try:
        by_page = {button.property("pageKey"): button for button in widget.findChildren(QPushButton, "metaTargetIANavItem")}
        for page_key in widget.target_ia_page_keys():
            button = by_page[page_key]
            button.click()
            app.processEvents()
            observed = widget.current_target_page_key()
            ok = observed == page_key
            contract_id = f"META-IA-{page_key.upper()}"
            rows.append(
                _row(
                    contract_id=contract_id,
                    surface="Meta Target IA",
                    current_file="app/meta_analysis/workspace.py",
                    button=button,
                    runtime_effect=f"navigates to Meta target IA page {page_key}",
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


def _audit_question_and_search_gates(project_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget = MetaAnalysisWorkspaceWidget()
    try:
        widget.set_project_dir(project_root)
        widget.show_target_ia_page("question_meta_type")
        type_button = _type_button(widget, "exposure_disease_risk_meta")
        type_button.click()
        question_gate = project_root / "ui_runtime" / "meta_question_type_gate.json"
        pico_draft = project_root / "protocol" / "pico_workspace_draft.json"
        ok = question_gate.exists() and pico_draft.exists() and widget.selected_active_meta_type_id() == "exposure_disease_risk_meta"
        rows.append(
            _row(
                contract_id="META-QUESTION-TYPE-SELECT",
                surface="Question & Meta Type",
                current_file="app/meta_analysis/workspace.py",
                button=type_button,
                runtime_effect="selects active Meta type and writes PICO workspace gate artifact",
                artifact_evidence=f"{question_gate}; {pico_draft}",
                observed="pico_gate_verified" if ok else "missing_pico_gate",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("META-QUESTION-TYPE-SELECT: expected PICO gate artifacts missing")

        widget.show_target_ia_page("search_strategy")
        copy_button = _find_button(widget, "metaCopyQueryButton")
        copy_button.click()
        copy_manifest = project_root / "ui_runtime" / "meta_search_query_copy_manifest.json"
        ok = copy_manifest.exists()
        rows.append(
            _row(
                contract_id="META-SEARCH-COPY-QUERY",
                surface="Search Strategy",
                current_file="app/meta_analysis/workspace.py",
                button=copy_button,
                runtime_effect="copies query draft and writes copy manifest",
                artifact_evidence=str(copy_manifest),
                observed="copy_manifest_verified" if ok else "missing_copy_manifest",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("META-SEARCH-COPY-QUERY: copy manifest missing")

        save_button = _find_button(widget, "metaSaveSearchDraftButton")
        save_button.click()
        disabled_reason = project_root / "ui_runtime" / "meta_search_strategy_disabled_reason.json"
        ok = disabled_reason.exists()
        rows.append(
            _row(
                contract_id="META-SEARCH-SAVE-UNCONFIRMED-GATE",
                surface="Search Strategy",
                current_file="app/meta_analysis/workspace.py",
                button=save_button,
                runtime_effect="writes disabled reason until protocol is confirmed",
                artifact_evidence=str(disabled_reason),
                observed="unconfirmed_search_gate_verified" if ok else "missing_unconfirmed_search_gate",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("META-SEARCH-SAVE-UNCONFIRMED-GATE: disabled reason artifact missing")
    finally:
        widget.close()
        widget.deleteLater()
    return rows


def _audit_confirmed_search_gate(audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    project = create_meta_analysis_project("Meta Batch 3 Confirmed Search", audit_root / "confirmed")
    project_root = project.project_root
    service = PICOWorkspaceService()
    service.generate_draft(project_root, "肥胖暴露与甲状腺癌风险是否相关？", pico_mode="peco")
    service.edit_draft(
        project_root,
        actor="reviewer",
        updates={
            "population": "甲状腺癌人群",
            "exposure": "肥胖",
            "comparator": "非肥胖",
            "outcome": "发病风险",
            "study_design": "observational study",
        },
    )
    service.confirm_protocol(
        project_root,
        actor="reviewer",
        confirmed_meta_type="exposure_disease_risk_meta",
        overrides={
            "confirmed_pico_mode": "peco",
            "confirmed_population": "甲状腺癌人群",
            "confirmed_intervention_or_exposure": "肥胖",
            "confirmed_comparator": "非肥胖",
            "confirmed_outcomes": ("发病风险",),
            "confirmed_study_design": "observational study",
        },
    )
    widget = MetaAnalysisWorkspaceWidget()
    try:
        widget.set_project_dir(project_root)
        widget.show_target_ia_page("search_strategy")
        save_button = _find_button(widget, "metaSaveSearchDraftButton")
        save_button.click()
        gate = project_root / "ui_runtime" / "meta_search_strategy_gate.json"
        draft_set = project_root / "protocol" / "search_strategy_v2" / "search_strategy_drafts.json"
        ok = gate.exists() and draft_set.exists()
        rows.append(
            _row(
                contract_id="META-SEARCH-SAVE-CONFIRMED-STRATEGY",
                surface="Search Strategy",
                current_file="app/meta_analysis/workspace.py",
                button=save_button,
                runtime_effect="calls SearchStrategyBuilderService and writes draft strategy artifacts",
                artifact_evidence=f"{gate}; {draft_set}",
                observed="confirmed_search_strategy_verified" if ok else "missing_confirmed_search_strategy",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("META-SEARCH-SAVE-CONFIRMED-STRATEGY: search strategy artifacts missing")
    finally:
        widget.close()
        widget.deleteLater()
    return rows


def _audit_import_dedup_gates(project_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget = MetaAnalysisWorkspaceWidget()
    try:
        widget.set_project_dir(project_root)
        widget.show_target_ia_page("import_dedup")
        import_buttons = [button for button in widget.findChildren(QPushButton, "metaImportSourceButton") if button.text().startswith("Import - adapter needed")]
        if len(import_buttons) != 4:
            failures.append(f"META-IMPORT-SOURCE-GATES: expected 4 import buttons, observed {len(import_buttons)}")
        for button in import_buttons:
            source_id = str(button.property("sourceId") or "unknown").upper()
            rows.append(_classify_gate_row(f"META-IMPORT-{source_id}-GATE", "Import & Deduplication", button))
        for object_name, contract_id in (
            ("metaAutoMergeDisabledButton", "META-DEDUP-AUTO-MERGE-GATE"),
            ("metaAutoDeleteDisabledButton", "META-DEDUP-AUTO-DELETE-GATE"),
            ("metaSendToScreeningDisabledButton", "META-DEDUP-SEND-SCREENING-GATE"),
        ):
            rows.append(_classify_gate_row(contract_id, "Import & Deduplication", _find_button(widget, object_name)))
    finally:
        widget.close()
        widget.deleteLater()
    return rows


def _audit_later_stage_gates(project_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget = MetaAnalysisWorkspaceWidget()
    try:
        widget.set_project_dir(project_root)

        widget.show_target_ia_page("screening")
        screening = _find_button(widget, "metaSaveDraftScreeningDecisionButton")
        screening.click()
        screening_gate = project_root / "ui_runtime" / "meta_screening_draft_decision_gate.json"
        ok = screening_gate.exists()
        rows.append(
            _row(
                contract_id="META-SCREENING-SAVE-DRAFT-DECISION",
                surface="Screening",
                current_file="app/meta_analysis/workspace.py",
                button=screening,
                runtime_effect="calls screening queue gate or writes draft screening artifact",
                artifact_evidence=str(screening_gate),
                observed="screening_gate_verified" if ok else "missing_screening_gate",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("META-SCREENING-SAVE-DRAFT-DECISION: screening gate artifact missing")

        widget.show_target_ia_page("fulltext_extraction")
        extraction = _find_button(widget, "metaSaveExtractionDesignButton")
        extraction.click()
        extraction_gate = project_root / "ui_runtime" / "meta_extraction_design_gate.json"
        ok = extraction_gate.exists()
        rows.append(
            _row(
                contract_id="META-EXTRACTION-SAVE-DESIGN",
                surface="Full-text & Extraction",
                current_file="app/meta_analysis/workspace.py",
                button=extraction,
                runtime_effect="calls extraction schema registry and writes gate artifact",
                artifact_evidence=str(extraction_gate),
                observed="extraction_gate_verified" if ok else "missing_extraction_gate",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("META-EXTRACTION-SAVE-DESIGN: extraction gate artifact missing")

        widget.show_target_ia_page("quality_assessment")
        rob = _find_button(widget, "metaSaveRiskOfBiasDraftButton")
        rob.click()
        rob_gate = project_root / "ui_runtime" / "meta_risk_of_bias_disabled_reason.json"
        ok = rob_gate.exists()
        rows.append(
            _row(
                contract_id="META-QUALITY-ROB-DRAFT-GATE",
                surface="Quality Assessment",
                current_file="app/meta_analysis/workspace.py",
                button=rob,
                runtime_effect="writes risk-of-bias disabled reason gate artifact",
                artifact_evidence=str(rob_gate),
                observed="rob_gate_verified" if ok else "missing_rob_gate",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("META-QUALITY-ROB-DRAFT-GATE: RoB gate artifact missing")
    finally:
        widget.close()
        widget.deleteLater()
    return rows


def _audit_report_export_gates(project_root: Path) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget = MetaAnalysisWorkspaceWidget()
    try:
        widget.set_project_dir(project_root)
        widget.show_target_ia_page("analysis_tasks")
        rows.append(_classify_gate_row("META-ANALYSIS-TASKS-FORMAL-ACTION-GATE", "Meta Analysis Tasks", _find_button(widget, "metaTargetBoundaryDisabledAction")))

        widget.show_target_ia_page("result_report")
        rows.append(_classify_gate_row("META-RESULT-REPORT-GENERATE-GATE", "Result & Report", _find_button(widget, "metaGenerateReportDisabledButton")))

        widget.show_target_ia_page("report_export")
        for button in widget.findChildren(QPushButton, "metaExportFormatDisabledButton"):
            export_format = str(button.property("exportFormat") or "unknown").upper()
            rows.append(_classify_gate_row(f"META-REPORT-EXPORT-{export_format}-GATE", "Report Export", button))
    finally:
        widget.close()
        widget.deleteLater()
    return rows


def _find_button(widget: object, object_name: str) -> QPushButton:
    button = widget.findChild(QPushButton, object_name)
    if button is None:
        raise AssertionError(f"Missing QPushButton objectName={object_name}")
    return button


def _type_button(widget: MetaAnalysisWorkspaceWidget, type_id: str) -> QPushButton:
    for button in widget.findChildren(QPushButton, "metaActiveTypeSelectButton"):
        if button.property("typeId") == type_id:
            return button
    raise AssertionError(f"Missing active Meta type button type_id={type_id}")


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
        current_file="app/meta_analysis/workspace.py",
        button=button,
        runtime_effect="gate classified by enabled state and disabled reason",
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
        module="Meta Analysis",
        surface=surface,
        current_file=current_file,
        object_name=button.objectName(),
        label=" ".join(button.text().split()),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        disabled_reason=str(button.property("disabledReason") or ""),
        runtime_effect=runtime_effect,
        artifact_evidence=artifact_evidence,
        live_click_test="scripts/ui_route_contract_meta_batch3.py",
        status=status,
        observed=observed,
    )


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract Meta Batch 3",
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
        "## Approved Structure",
        "",
        "- UIShell target IA remains the final visual baseline.",
        "- Old workflow pages and services are capability sources; they do not replace the mature gated shell.",
        "- PubMed/Search/Dedup/Screening capabilities are connected only where a visible UIShell gate or adapter button proves the service/artifact path.",
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
