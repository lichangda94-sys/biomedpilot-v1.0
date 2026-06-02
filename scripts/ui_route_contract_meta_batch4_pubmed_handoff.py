from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtWidgets import QApplication, QPushButton

from app.meta_analysis.pages.literature_library_page import literature_library_state_from_project
from app.meta_analysis.pages.protocol_page import write_pubmed_search_execution_artifacts
from app.meta_analysis.search.pubmed_candidates_handoff_service import PubMedCandidatesHandoffService
from app.meta_analysis.search.pubmed_search_service import PubMedSearchService
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH4_PUBMED_HANDOFF.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH4_PUBMED_HANDOFF.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_meta_batch4_pubmed_handoff"


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
    batch: str = "Batch 4: Meta PubMed Search and Handoff"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    screenshots: list[dict[str, str]] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_meta_batch4_") as temp_name:
            audit_root = Path(temp_name)
            project_dir = audit_root / "meta_pubmed_handoff_project"
            project_dir.mkdir(parents=True, exist_ok=True)
            rows.extend(_audit_ui_gates(app, project_dir, args.screenshot_dir, screenshots, failures))
            rows.extend(_audit_pubmed_service_chain(project_dir, failures))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_meta_batch4_pubmed_handoff.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Meta mature UIShell PubMed/search/handoff route contract: UI gate state plus deterministic service artifact proof.",
        "source_matrix": {
            "ui_baseline": "UIShell high-fidelity Meta target IA in app/meta_analysis/workspace.py; historical source line: ui: rebuild meta analysis workbench surfaces.",
            "backend_sources": [
                "app/meta_analysis/search/pubmed_search_service.py",
                "app/meta_analysis/search/pubmed_candidates_handoff_service.py",
                "app/meta_analysis/pages/protocol_page.py",
                "app/meta_analysis/services/literature_library_service.py",
            ],
            "policy": "Old protocol page buttons are backend capability evidence only; they do not replace mature UIShell pages.",
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
    parser = argparse.ArgumentParser(description="Run Meta Batch 4 PubMed/search/handoff route contract audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _audit_ui_gates(
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
        widget.show_target_ia_page("search_strategy")
        widget.show()
        app.processEvents()
        screenshots.append(_capture(widget, screenshot_dir / "01_search_strategy_pubmed_gate.png", "search_strategy"))

        save_button = _find_button(widget, "metaSaveSearchDraftButton")
        save_button.click()
        app.processEvents()
        search_gate = project_dir / "ui_runtime" / "meta_search_strategy_disabled_reason.json"
        rows.append(
            _row_from_button(
                "META-PUBMED-UI-SEARCH-DRAFT-GATE",
                "Search Strategy",
                "SearchStrategyBuilderService gate or disabled reason",
                "UIShell Meta mature page; current Integration HEAD",
                "app/meta_analysis/workspace.py",
                save_button,
                str(search_gate),
                "connected" if search_gate.exists() else "broken",
                "draft_gate_artifact_verified" if search_gate.exists() else "missing_search_gate_artifact",
            )
        )
        if not search_gate.exists():
            failures.append("META-PUBMED-UI-SEARCH-DRAFT-GATE: expected search draft gate artifact missing")

        run_pubmed_button = widget.findChild(QPushButton, "metaRunPubMedSearchButton")
        rows.append(
            ContractRow(
                contract_id="META-PUBMED-UI-RUN-PUBMED-ACTION",
                ui_page="Search Strategy",
                backend_capability="PubMed search execution",
                branch_source="Backend service exists in current Integration; mature UIShell visible execution button not yet present.",
                current_file="app/meta_analysis/workspace.py",
                object_name="metaRunPubMedSearchButton",
                label="",
                enabled=False,
                button_behavior="missing_visible_adapter_action",
                disabled_reason="成熟 UIShell Search Strategy 页面没有显式 PubMed 执行按钮；不能把旧 ProtocolPage 按钮伪装为当前页面已接入。",
                expected_artifact="protocol/search_execution_report.json",
                live_click_test="scripts/ui_route_contract_meta_batch4_pubmed_handoff.py",
                status="gap" if run_pubmed_button is None else "connected",
                observed="missing_visible_button" if run_pubmed_button is None else "visible_button_present",
            )
        )

        widget.show_target_ia_page("import_dedup")
        app.processEvents()
        screenshots.append(_capture(widget, screenshot_dir / "02_import_dedup_pubmed_boundary.png", "import_dedup"))
        pubmed_buttons = [
            button
            for button in widget.findChildren(QPushButton, "metaImportSourceButton")
            if button.property("sourceId") == "pubmed_result_file"
        ]
        if len(pubmed_buttons) != 1:
            failures.append(f"META-PUBMED-UI-IMPORT-GATE: expected 1 PubMed import gate, observed {len(pubmed_buttons)}")
        for button in pubmed_buttons:
            status = "disabled" if not button.isEnabled() and button.property("disabledReason") else "broken"
            rows.append(
                _row_from_button(
                    "META-PUBMED-UI-IMPORT-GATE",
                    "Import & Deduplication",
                    "PubMed result/candidate handoff adapter",
                    "UIShell Meta mature page; current Integration HEAD",
                    "app/meta_analysis/workspace.py",
                    button,
                    "protocol/pubmed_candidates/*_candidates_preview.json",
                    status,
                    "disabled_with_reason" if status == "disabled" else "missing_disabled_reason",
                )
            )
            if status == "broken":
                failures.append("META-PUBMED-UI-IMPORT-GATE: PubMed import gate is missing disabled reason")
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()
    return rows


def _audit_pubmed_service_chain(project_dir: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    query = '("thyroid cancer"[Title/Abstract]) AND ("adiponectin"[Title/Abstract])'
    service = PubMedSearchService(fetcher=_fake_pubmed_fetcher)

    preview = service.preview_pubmed_count(query)
    rows.append(
        _service_row(
            "META-PUBMED-SERVICE-COUNT-PREVIEW",
            "Search Strategy",
            "PubMed count preview",
            "app/meta_analysis/search/pubmed_search_service.py",
            "PubMedSearchService.preview_pubmed_count",
            "PubMedCountPreview",
            preview.success and preview.result_count == 3,
            f"success={preview.success}; result_count={preview.result_count}; errors={preview.errors}",
        )
    )

    execution = service.search_pubmed(query, max_results=3)
    rows.append(
        _service_row(
            "META-PUBMED-SERVICE-EXECUTION",
            "Search Strategy",
            "PubMed search execution",
            "app/meta_analysis/search/pubmed_search_service.py",
            "PubMedSearchService.search_pubmed",
            "PubMedSearchExecution",
            execution.success and execution.returned_count == 3 and len(execution.records) == 3,
            f"success={execution.success}; result_count={execution.result_count}; returned_count={execution.returned_count}; pmids={list(execution.pmids)}",
        )
    )

    paths = write_pubmed_search_execution_artifacts(project_dir, query, execution)
    report_path = Path(paths["search_execution_report"])
    preview_path = Path(paths["pubmed_candidates_preview"])
    rows.append(
        _service_row(
            "META-PUBMED-ARTIFACTS-EXECUTION-AND-PREVIEW",
            "Search Strategy",
            "search execution report and candidate preview",
            "app/meta_analysis/pages/protocol_page.py",
            "write_pubmed_search_execution_artifacts",
            f"{report_path}; {preview_path}",
            report_path.exists() and preview_path.exists(),
            "execution_report_and_candidate_preview_verified" if report_path.exists() and preview_path.exists() else "missing_execution_or_preview_artifact",
        )
    )

    preview_payload = _load_json(preview_path)
    preview_id = str(preview_payload.get("preview_id") or preview_path.name.replace("_candidates_preview.json", ""))
    candidate_ids = [str(candidate["candidate_id"]) for candidate in preview_payload.get("candidates", [])]
    handoff_service = PubMedCandidatesHandoffService()
    selection = handoff_service.select_candidates(
        project_dir,
        preview_id=preview_id,
        selected_candidate_ids=tuple(candidate_ids[:2]),
        rejected_candidate_ids=tuple(candidate_ids[2:]),
        actor="route_contract",
    )
    rows.append(
        _service_row(
            "META-PUBMED-HANDOFF-SELECTION",
            "Import & Deduplication",
            "reviewer candidate selection",
            "app/meta_analysis/search/pubmed_candidates_handoff_service.py",
            "PubMedCandidatesHandoffService.select_candidates",
            selection.output_path,
            selection.success and selection.selected_count == 2 and Path(selection.output_path).exists(),
            f"success={selection.success}; selected={selection.selected_count}; rejected={selection.rejected_count}; pending={selection.pending_count}",
        )
    )

    handoff = handoff_service.import_selected_candidates(
        project_dir,
        preview_id=preview_id,
        selected_candidate_ids=tuple(candidate_ids[:2]),
        rejected_candidate_ids=tuple(candidate_ids[2:]),
        actor="route_contract",
    )
    rows.append(
        _service_row(
            "META-PUBMED-HANDOFF-IMPORT",
            "Import & Deduplication",
            "selected PubMed candidates imported to literature library",
            "app/meta_analysis/search/pubmed_candidates_handoff_service.py",
            "PubMedCandidatesHandoffService.import_selected_candidates",
            handoff.literature_records_path,
            handoff.success and handoff.imported_count == 2 and Path(handoff.literature_records_path).exists(),
            f"success={handoff.success}; imported={handoff.imported_count}; message={handoff.message}",
        )
    )

    library_state = literature_library_state_from_project(project_dir)
    rows.append(
        _service_row(
            "META-PUBMED-LITERATURE-LIBRARY-INDEX",
            "Import & Deduplication",
            "literature library read path",
            "app/meta_analysis/pages/literature_library_page.py",
            "literature_library_state_from_project",
            handoff.literature_records_path,
            library_state.total_records == 2 and all(row.source_database == "PubMed" for row in library_state.rows),
            f"total_records={library_state.total_records}; sources={[row.source_database for row in library_state.rows]}",
        )
    )

    rows.append(
        _service_row(
            "META-PUBMED-DEDUP-PREP",
            "Import & Deduplication",
            "deduplication preparation queue",
            "app/meta_analysis/search/pubmed_candidates_handoff_service.py",
            "PubMedCandidatesHandoffService._write_dedup_preparation",
            handoff.dedup_queue_path,
            Path(handoff.dedup_queue_path).exists() and _load_json(Path(handoff.dedup_queue_path)).get("status") == "pending_reviewer_decision",
            f"dedup_queue={handoff.dedup_queue_path}; auto_merged={_load_json(Path(handoff.dedup_queue_path)).get('auto_merged')}",
        )
    )

    prisma = PRISMAService().collect_prisma_numbers(project_dir)
    no_auto_screening = (
        not (project_dir / "screening").exists()
        and prisma.records_screened == 0
        and prisma.studies_included == 0
        and _load_json(Path(handoff.handoff_audit_path)).get("prisma_status") == "not_updated"
    )
    rows.append(
        _service_row(
            "META-PUBMED-NO-AUTO-SCREENING-OR-PRISMA",
            "Screening / Report",
            "boundary: no automatic screening or PRISMA advancement",
            "app/meta_analysis/search/pubmed_candidates_handoff_service.py",
            "PubMedCandidatesHandoffService.import_selected_candidates",
            handoff.handoff_audit_path,
            no_auto_screening,
            f"screening_dir_exists={(project_dir / 'screening').exists()}; records_screened={prisma.records_screened}; studies_included={prisma.studies_included}",
        )
    )

    for row in rows:
        if row.status == "broken":
            failures.append(f"{row.contract_id}: {row.observed}")
    return rows


def _capture(widget: MetaAnalysisWorkspaceWidget, path: Path, page_key: str) -> dict[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(path))
    return {"name": page_key, "path": str(path)}


def _find_button(widget: object, object_name: str) -> QPushButton:
    button = widget.findChild(QPushButton, object_name)
    if button is None:
        raise AssertionError(f"Missing QPushButton objectName={object_name}")
    return button


def _row_from_button(
    contract_id: str,
    ui_page: str,
    backend_capability: str,
    branch_source: str,
    current_file: str,
    button: QPushButton,
    expected_artifact: str,
    status: str,
    observed: str,
) -> ContractRow:
    return ContractRow(
        contract_id=contract_id,
        ui_page=ui_page,
        backend_capability=backend_capability,
        branch_source=branch_source,
        current_file=current_file,
        object_name=button.objectName(),
        label=" ".join(button.text().split()),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        disabled_reason=str(button.property("disabledReason") or ""),
        expected_artifact=expected_artifact,
        live_click_test="scripts/ui_route_contract_meta_batch4_pubmed_handoff.py",
        status=status,
        observed=observed,
    )


def _service_row(
    contract_id: str,
    ui_page: str,
    backend_capability: str,
    current_file: str,
    object_name: str,
    expected_artifact: str,
    ok: bool,
    observed: str,
) -> ContractRow:
    return ContractRow(
        contract_id=contract_id,
        ui_page=ui_page,
        backend_capability=backend_capability,
        branch_source="current Integration service; old protocol page capability source where applicable",
        current_file=current_file,
        object_name=object_name,
        label=object_name,
        enabled=True,
        button_behavior="service_or_artifact_verified",
        disabled_reason="",
        expected_artifact=expected_artifact,
        live_click_test="scripts/ui_route_contract_meta_batch4_pubmed_handoff.py",
        status="connected" if ok else "broken",
        observed=observed,
    )


def _fake_pubmed_fetcher(url: str, timeout_seconds: float) -> bytes:
    del timeout_seconds
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if parsed.path.endswith("esearch.fcgi"):
        retmax = int(query.get("retmax", ["3"])[0] or 3)
        ids = ["111", "222", "333"][:retmax] if retmax else []
        return json.dumps({"esearchresult": {"count": "3", "idlist": ids}}).encode("utf-8")
    if parsed.path.endswith("efetch.fcgi"):
        ids = ",".join(query.get("id", ["111,222,333"])).split(",")
        return _fake_pubmed_xml(ids).encode("utf-8")
    raise AssertionError(f"Unexpected PubMed URL: {url}")


def _fake_pubmed_xml(pmids: list[str]) -> str:
    records = {
        "111": ("Serum adiponectin and thyroid cancer risk", "Endocrine Evidence", "2024", "10.1000/demo111", "Alice Adams"),
        "222": ("Adiponectin levels in thyroid carcinoma", "Clinical Oncology Meta", "2025", "10.1000/demo222", "Ben Baker"),
        "333": ("ADIPOQ and thyroid neoplasm prognosis", "Cancer Biomarker Review", "2023", "10.1000/demo333", "Chen Chen"),
    }
    articles = []
    for pmid in pmids:
        title, journal, year, doi, author = records.get(pmid, records["111"])
        first, last = author.split(" ", 1)
        articles.append(
            f"""
            <PubmedArticle>
              <MedlineCitation>
                <PMID>{pmid}</PMID>
                <Article>
                  <Journal><Title>{journal}</Title><JournalIssue><PubDate><Year>{year}</Year></PubDate></JournalIssue></Journal>
                  <ArticleTitle>{title}</ArticleTitle>
                  <Abstract><AbstractText>Deterministic PubMed abstract for route-contract validation.</AbstractText></Abstract>
                  <AuthorList><Author><LastName>{last}</LastName><ForeName>{first}</ForeName></Author></AuthorList>
                </Article>
              </MedlineCitation>
              <PubmedData><ArticleIdList><ArticleId IdType="doi">{doi}</ArticleId></ArticleIdList></PubmedData>
            </PubmedArticle>
            """
        )
    return "<PubmedArticleSet>" + "\n".join(articles) + "</PubmedArticleSet>"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract Meta Batch 4: PubMed Search and Handoff",
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
            "## Next Adapter Work",
            "",
            "- Add a visually scoped PubMed execution adapter action to the mature Search Strategy page only after confirming the UIShell baseline placement.",
            "- Add reviewer candidate-selection controls to the mature Import & Deduplication page before enabling PubMed handoff from the page itself.",
            "- Keep PubMed candidate import, screening queue creation, and PRISMA count advancement separated by explicit reviewer gates.",
        ]
    )
    return "\n".join(lines) + "\n"


def _md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _git(*args: str) -> str:
    import subprocess

    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
