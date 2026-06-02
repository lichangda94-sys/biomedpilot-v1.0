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
from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
from app.meta_analysis.services.title_abstract_screening_v2_service import DECISION_INCLUDE, TitleAbstractScreeningV2Service
from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH7_FULLTEXT_EXTRACTION.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH7_FULLTEXT_EXTRACTION.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_meta_batch7_fulltext_extraction"


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
    batch: str = "Batch 7: Meta Full-text & Extraction"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    screenshots: list[dict[str, str]] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_meta_batch7_") as temp_name:
            project_dir = _seed_project(Path(temp_name))
            rows.extend(_audit_fulltext_extraction_ui(app, project_dir, args.screenshot_dir, screenshots, failures))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_meta_batch7_fulltext_extraction.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Meta mature UIShell Full-text & Extraction page: fulltext registry, extraction schema selection, manual extraction draft, and disabled placeholder tabs.",
        "source_matrix": {
            "ui_baseline": "UIShell high-fidelity Meta target IA Full-text & Extraction Workspace in app/meta_analysis/workspace.py.",
            "backend_sources": [
                "app/meta_analysis/services/fulltext_management_service.py",
                "app/meta_analysis/services/extraction_schema_registry_v1_service.py",
                "app/meta_analysis/services/manual_extraction_effect_row_service.py",
            ],
            "policy": "Full-text and extraction adapters write reviewer-controlled draft artifacts only; no automatic PDF retrieval, final extraction, statistics execution, or report-ready advancement.",
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
    parser = argparse.ArgumentParser(description="Run Meta Batch 7 fulltext/extraction route contract audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _seed_project(root: Path) -> Path:
    summary = create_meta_analysis_project("Meta Batch 7 Fulltext Extraction", root)
    project_dir = summary.project_root
    LiteratureLibraryService().import_records(
        project_dir,
        project_id=project_dir.name,
        source_type="pubmed_confirmed_candidates",
        source_name="PubMed",
        raw_records=[
            {
                "record_id": "batch7-a",
                "title": "Serum adiponectin and thyroid cancer risk",
                "abstract": "Eligible adult study with effect-size data pending full-text extraction.",
                "authors": ["Alice Adams"],
                "journal": "Meta Route Contract",
                "year": "2024",
                "pmid": "700001",
                "doi": "10.0000/meta-batch7-a",
            }
        ],
    )
    screening = TitleAbstractScreeningV2Service()
    queue = screening.build_queue(project_dir, project_id=project_dir.name)
    record_id = queue.records[0]["record_id"]
    screening.save_decision(
        project_dir,
        record_id=record_id,
        decision=DECISION_INCLUDE,
        actor="uishell_reviewer",
        notes="Included by route-contract seed for full-text/extraction adapter verification.",
    )
    return project_dir


def _audit_fulltext_extraction_ui(
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
        widget.show_target_ia_page("fulltext_extraction")
        widget.show()
        app.processEvents()
        QTest.qWait(80)
        screenshots.append(_capture(widget, screenshot_dir / "01_fulltext_management.png", "fulltext_management"))

        open_design = _find_button(widget, "metaOpenExtractionDesignButton")
        open_design.click()
        app.processEvents()
        QTest.qWait(80)
        fulltext_gate = project_dir / "ui_runtime" / "meta_fulltext_registry_adapter.json"
        fulltext_registry = project_dir / "fulltext" / "fulltext_management_registry_v1.json"
        rows.append(
            _row(
                "META-FULLTEXT-OPEN-DESIGN",
                "Full-text & Extraction",
                "FullTextManagementService.build_registry_from_screening",
                open_design,
                fulltext_gate,
                "connected" if fulltext_gate.exists() and fulltext_registry.exists() else "broken",
                "fulltext_registry_written" if fulltext_gate.exists() and fulltext_registry.exists() else "missing_fulltext_registry",
            )
        )
        if not fulltext_gate.exists() or not fulltext_registry.exists():
            failures.append("META-FULLTEXT-OPEN-DESIGN: fulltext registry artifact missing")
        screenshots.append(_capture(widget, screenshot_dir / "02_extraction_design.png", "extraction_design"))

        save_design = _find_button(widget, "metaSaveExtractionDesignButton")
        save_design.click()
        app.processEvents()
        QTest.qWait(80)
        extraction_gate = project_dir / "ui_runtime" / "meta_extraction_design_gate.json"
        schema_registry = project_dir / "extraction" / "schema_registry_v1.json"
        schema_selection = project_dir / "extraction" / "selected_extraction_schema_v1.json"
        rows.append(
            _row(
                "META-EXTRACTION-SAVE-DESIGN",
                "Full-text & Extraction",
                "ExtractionSchemaRegistryV1Service.save_default_registry/save_schema_selection",
                save_design,
                extraction_gate,
                "connected" if extraction_gate.exists() and schema_registry.exists() and schema_selection.exists() else "broken",
                "schema_registry_and_selection_written"
                if extraction_gate.exists() and schema_registry.exists() and schema_selection.exists()
                else "missing_schema_artifact",
            )
        )
        if not extraction_gate.exists() or not schema_registry.exists() or not schema_selection.exists():
            failures.append("META-EXTRACTION-SAVE-DESIGN: schema registry/selection artifact missing")

        confirm = _find_button(widget, "metaConfirmExtractionButton")
        confirm.click()
        app.processEvents()
        QTest.qWait(80)
        draft_gate = project_dir / "ui_runtime" / "meta_extraction_draft_adapter.json"
        effect_rows = project_dir / "extraction" / "extraction_effect_rows.json"
        manifest = project_dir / "extraction" / "extraction_manifest.json"
        rows.append(
            _row(
                "META-EXTRACTION-CONFIRM-DRAFT",
                "Full-text & Extraction",
                "ManualExtractionEffectRowService.create_study_unit/create_effect_row",
                confirm,
                draft_gate,
                "connected" if draft_gate.exists() and effect_rows.exists() and manifest.exists() else "broken",
                "draft_extraction_row_written_not_report_ready"
                if draft_gate.exists() and effect_rows.exists() and manifest.exists()
                else "missing_draft_extraction_artifact",
            )
        )
        if not draft_gate.exists() or not effect_rows.exists() or not manifest.exists():
            failures.append("META-EXTRACTION-CONFIRM-DRAFT: manual extraction draft artifact missing")

        back = _find_button(widget, "metaBackToFulltextButton")
        back.click()
        app.processEvents()
        QTest.qWait(80)
        rows.append(_row("META-EXTRACTION-BACK-FULLTEXT", "Full-text & Extraction", "UI tab navigation", back, Path(""), "connected", "returned_to_fulltext_management_tab"))
        screenshots.append(_capture(widget, screenshot_dir / "03_back_to_fulltext_management.png", "back_to_fulltext_management"))

        for button in widget.findChildren(QPushButton, "metaFulltextExtractionTab"):
            tab_key = str(button.property("tabKey") or "")
            if tab_key in {"提取完成核查", "历史记录"}:
                status = "disabled" if not button.isEnabled() and str(button.property("disabledReason") or "") else "broken"
                if status == "broken":
                    failures.append(f"META-FULLTEXT-TAB-{tab_key}: disabled reason missing")
                rows.append(
                    _row(
                        f"META-FULLTEXT-TAB-{tab_key}",
                        "Full-text & Extraction",
                        "disabled reason for future tab adapter",
                        button,
                        Path(""),
                        status,
                        "disabled_with_reason" if status == "disabled" else "disabled_reason_missing",
                    )
                )
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
        live_click_test="scripts/ui_route_contract_meta_batch7_fulltext_extraction.py",
        status=status,
        observed=observed,
    )


def _capture(widget: MetaAnalysisWorkspaceWidget, path: Path, name: str) -> dict[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(path))
    return {"name": name, "path": str(path), "page_key": widget.current_target_page_key()}


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract - Meta Batch 7 Full-text & Extraction",
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
