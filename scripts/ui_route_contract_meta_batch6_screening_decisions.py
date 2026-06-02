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
from app.meta_analysis.services.title_abstract_screening_v2_service import TitleAbstractScreeningV2Service
from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH6_SCREENING_DECISIONS.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH6_SCREENING_DECISIONS.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_meta_batch6_screening_decisions"


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
    batch: str = "Batch 6: Meta Screening Decisions"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    screenshots: list[dict[str, str]] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_meta_batch6_") as temp_name:
            project_dir = _seed_project(Path(temp_name))
            rows.extend(_audit_screening_ui(app, project_dir, args.screenshot_dir, screenshots, failures))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_meta_batch6_screening_decisions.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Meta mature UIShell Screening page: decision selection, reviewer save, compatible screening decisions, and next-step navigation.",
        "source_matrix": {
            "ui_baseline": "UIShell high-fidelity Meta target IA Screening Workspace in app/meta_analysis/workspace.py.",
            "backend_sources": ["app/meta_analysis/services/title_abstract_screening_v2_service.py"],
            "policy": "AI suggestions remain advisory only; reviewer save is explicit; no automatic screening or report-ready advancement.",
        },
        "summary": {
            "row_count": len(rows),
            "connected": sum(1 for row in rows if row.status == "connected"),
            "disabled": sum(1 for row in rows if row.status == "disabled"),
            "gap": sum(1 for row in rows if row.status == "gap"),
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
    parser = argparse.ArgumentParser(description="Run Meta Batch 6 screening decision route contract audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _seed_project(root: Path) -> Path:
    summary = create_meta_analysis_project("Meta Batch 6 Screening Decisions", root)
    project_dir = summary.project_root
    LiteratureLibraryService().import_records(
        project_dir,
        project_id=project_dir.name,
        source_type="pubmed_confirmed_candidates",
        source_name="PubMed",
        raw_records=[
            {
                "record_id": "batch6-a",
                "title": "Serum adiponectin and thyroid cancer risk",
                "abstract": "Eligible adult study.",
                "authors": ["Alice Adams"],
                "journal": "Meta Route Contract",
                "year": "2024",
                "pmid": "600001",
            },
            {
                "record_id": "batch6-b",
                "title": "Animal adiponectin model in thyroid tumor",
                "abstract": "Animal model study.",
                "authors": ["Ben Baker"],
                "journal": "Meta Route Contract",
                "year": "2023",
                "pmid": "600002",
            },
            {
                "record_id": "batch6-c",
                "title": "Unclear adiponectin thyroid carcinoma cohort",
                "abstract": "Unclear eligibility.",
                "authors": ["Carol Chen"],
                "journal": "Meta Route Contract",
                "year": "2022",
                "pmid": "600003",
            },
        ],
    )
    TitleAbstractScreeningV2Service().build_queue(project_dir, project_id=project_dir.name)
    return project_dir


def _audit_screening_ui(
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
        widget.show_target_ia_page("screening")
        widget.show()
        app.processEvents()
        QTest.qWait(80)
        screenshots.append(_capture(widget, screenshot_dir / "01_screening_decision_workspace.png", "screening_decision_workspace"))

        decision_buttons = {
            str(button.property("decisionId") or ""): button
            for button in widget.findChildren(QPushButton, "metaScreeningDecisionDraftButton")
        }
        for decision_id in ("include_draft", "exclude_draft", "uncertain", "need_full_text"):
            button = decision_buttons[decision_id]
            button.click()
            app.processEvents()
            QTest.qWait(50)
            artifact = project_dir / "ui_runtime" / "meta_screening_decision_selection_adapter.json"
            payload = _load_json(artifact)
            ok = (
                artifact.exists()
                and payload.get("selected_decision_id") == decision_id
                and payload.get("service_called") is False
                and payload.get("auto_decided") is False
            )
            rows.append(
                _row(
                    f"META-SCREENING-DECISION-SELECT-{decision_id.upper()}",
                    "Screening",
                    "reviewer decision selection state",
                    button,
                    str(artifact),
                    "connected" if ok else "broken",
                    f"selection_payload={_compact(payload)}",
                )
            )
            if not ok:
                failures.append(f"META-SCREENING-DECISION-SELECT-{decision_id}: invalid selection artifact")

        decision_buttons["include_draft"].click()
        app.processEvents()
        save_draft = _button(widget, "metaSaveDraftScreeningDecisionButton")
        save_draft.click()
        app.processEvents()
        QTest.qWait(80)
        decision_artifact = project_dir / "ui_runtime" / "meta_screening_decision_adapter.json"
        include_payload = _load_json(decision_artifact)
        include_ok = (
            decision_artifact.exists()
            and include_payload.get("service") == "TitleAbstractScreeningV2Service.save_decision"
            and include_payload.get("decision") == "include"
            and include_payload.get("auto_decided") is False
            and (project_dir / str(include_payload.get("decisions_path", ""))).exists()
            and (project_dir / str(include_payload.get("compatible_decisions_path", ""))).exists()
        )
        rows.append(
            _row(
                "META-SCREENING-SAVE-DRAFT-DECISION",
                "Screening",
                "save reviewer title/abstract decision",
                save_draft,
                str(decision_artifact),
                "connected" if include_ok else "broken",
                f"save_payload={_compact(include_payload)}",
            )
        )
        if not include_ok:
            failures.append("META-SCREENING-SAVE-DRAFT-DECISION: save decision artifact missing or invalid")

        decision_buttons["exclude_draft"].click()
        app.processEvents()
        save_next = _button(widget, "metaScreeningSaveNextButton")
        save_next.click()
        app.processEvents()
        QTest.qWait(80)
        exclude_payload = _load_json(decision_artifact)
        exclude_ok = (
            exclude_payload.get("decision") == "exclude"
            and exclude_payload.get("decision_counts", {}).get("include") == 1
            and exclude_payload.get("decision_counts", {}).get("exclude") == 1
            and exclude_payload.get("advance_requested") is True
        )
        rows.append(
            _row(
                "META-SCREENING-SAVE-NEXT-DECISION",
                "Screening",
                "save reviewer decision and move to next unscreened record",
                save_next,
                str(decision_artifact),
                "connected" if exclude_ok else "broken",
                f"save_next_payload={_compact(exclude_payload)}",
            )
        )
        if not exclude_ok:
            failures.append("META-SCREENING-SAVE-NEXT-DECISION: save next artifact missing or invalid")

        screenshots.append(_capture(widget, screenshot_dir / "02_screening_after_decision_save.png", "screening_after_decision_save"))

        next_fulltext = _button(widget, "metaScreeningNextFulltextButton")
        next_fulltext.click()
        app.processEvents()
        QTest.qWait(80)
        nav_ok = widget.current_target_page_key() == "fulltext_extraction"
        rows.append(
            _row(
                "META-SCREENING-NAV-NEXT-FULLTEXT",
                "Screening",
                "navigate to mature Full-text & Extraction page",
                next_fulltext,
                "current_target_page_key=fulltext_extraction",
                "connected" if nav_ok else "broken",
                f"current_target_page_key={widget.current_target_page_key()}",
            )
        )
        if not nav_ok:
            failures.append("META-SCREENING-NAV-NEXT-FULLTEXT: navigation target mismatch")
        screenshots.append(_capture(widget, screenshot_dir / "03_fulltext_after_next_navigation.png", "fulltext_after_next_navigation"))
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()
    return rows


def _row(
    contract_id: str,
    ui_page: str,
    backend_capability: str,
    button: QPushButton,
    expected_artifact: str,
    status: str,
    observed: str,
) -> ContractRow:
    return ContractRow(
        contract_id=contract_id,
        ui_page=ui_page,
        backend_capability=backend_capability,
        branch_source="UIShell high-fidelity Meta Screening page retained; current Integration v2 service adapter.",
        current_file="app/meta_analysis/workspace.py",
        object_name=button.objectName(),
        label=" ".join(button.text().split()),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        disabled_reason=str(button.property("disabledReason") or ""),
        expected_artifact=expected_artifact,
        live_click_test="scripts/ui_route_contract_meta_batch6_screening_decisions.py",
        status=status,
        observed=observed,
    )


def _button(widget: object, object_name: str) -> QPushButton:
    button = widget.findChild(QPushButton, object_name)
    if button is None:
        raise AssertionError(f"Missing QPushButton objectName={object_name}")
    return button


def _capture(widget: MetaAnalysisWorkspaceWidget, path: Path, name: str) -> dict[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(path))
    return {"name": name, "path": str(path), "page_key": widget.current_target_page_key()}


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _compact(payload: dict[str, object]) -> str:
    keys = (
        "service",
        "success",
        "selected_decision_id",
        "mapped_decision",
        "record_id",
        "decision",
        "decision_counts",
        "advance_requested",
        "auto_decided",
    )
    return json.dumps({key: payload.get(key) for key in keys if key in payload}, ensure_ascii=False, sort_keys=True)


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract Meta Batch 6: Screening Decisions",
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
        f"- UI gaps recorded: {summary['gap']}",
        f"- Broken: {summary['broken']}",
        "",
        "## Source Matrix",
        "",
        f"- UI baseline: {payload['source_matrix']['ui_baseline']}",
        f"- Policy: {payload['source_matrix']['policy']}",
        "",
        "## Screenshots",
        "",
    ]
    for shot in payload["screenshots"]:
        lines.extend([f"### {shot['name']}", "", f"![{shot['name']}]({shot['path']})", ""])
    lines.extend(
        [
            "## UI Page -> Backend Capability -> Branch Source -> Test",
            "",
            "| Contract | UI Page | Backend Capability | Source | Object | Status | Expected Artifact | Observed |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            "| {contract_id} | {ui_page} | {backend_capability} | {branch_source} | `{object_name}` | `{status}` | {expected_artifact} | {observed} |".format(
                contract_id=_md(row["contract_id"]),
                ui_page=_md(row["ui_page"]),
                backend_capability=_md(row["backend_capability"]),
                branch_source=_md(row["branch_source"]),
                object_name=_md(row["object_name"]),
                status=_md(row["status"]),
                expected_artifact=_md(row["expected_artifact"]),
                observed=_md(row["observed"]),
            )
        )
    failures = summary.get("failures") or []
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Decision selection writes UI state only; it does not write final screening decisions.",
            "- Save actions call `TitleAbstractScreeningV2Service.save_decision` with reviewer actor.",
            "- Exclude uses a structured exclusion reason; AI suggestion remains advisory only.",
            "- Navigation to Full-text is route-only; extraction and report gates remain separate batches.",
        ]
    )
    return "\n".join(lines) + "\n"


def _md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
