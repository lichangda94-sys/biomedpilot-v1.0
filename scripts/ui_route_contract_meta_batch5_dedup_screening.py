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
from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH5_DEDUP_SCREENING.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_META_BATCH5_DEDUP_SCREENING.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_meta_batch5_dedup_screening"


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
    batch: str = "Batch 5: Meta Dedup to Screening"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    failures: list[str] = []
    screenshots: list[dict[str, str]] = []
    rows: list[ContractRow] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_meta_batch5_") as temp_name:
            project_dir = _seed_project(Path(temp_name))
            rows.extend(_audit_ui(app, project_dir, args.screenshot_dir, screenshots, failures))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_meta_batch5_dedup_screening.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Meta mature UIShell Import & Deduplication adapter chain: literature library -> DedupReviewV2 -> deduplicated set -> TitleAbstractScreeningV2 queue.",
        "source_matrix": {
            "ui_baseline": "UIShell high-fidelity Meta target IA in app/meta_analysis/workspace.py; mature page retained.",
            "backend_sources": [
                "app/meta_analysis/services/dedup_review_v2_service.py",
                "app/meta_analysis/services/title_abstract_screening_v2_service.py",
                "app/meta_analysis/services/literature_library_service.py",
            ],
            "policy": "Old duplicate_review_page/screening_page remain backend capability references only; mature UIShell page is not replaced.",
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
    parser = argparse.ArgumentParser(description="Run Meta Batch 5 dedup-to-screening route contract audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _seed_project(root: Path) -> Path:
    summary = create_meta_analysis_project("Meta Batch 5 Dedup Screening", root)
    project_dir = summary.project_root
    LiteratureLibraryService().import_records(
        project_dir,
        project_id=project_dir.name,
        source_type="pubmed_confirmed_candidates",
        source_name="PubMed",
        raw_records=[
            {
                "record_id": "lit-b5-a",
                "title": "Serum adiponectin and thyroid cancer risk",
                "abstract": "Batch 5 route-contract abstract A.",
                "authors": ["Alice Adams"],
                "journal": "Meta Route Contract",
                "year": "2024",
                "pmid": "900001",
                "doi": "10.1000/b5a",
            },
            {
                "record_id": "lit-b5-b",
                "title": "Serum adiponectin and thyroid cancer risk",
                "abstract": "Batch 5 route-contract duplicate abstract B.",
                "authors": ["Alice Adams"],
                "journal": "Meta Route Contract",
                "year": "2024",
                "pmid": "900001",
                "doi": "10.1000/b5b",
            },
            {
                "record_id": "lit-b5-c",
                "title": "Adiponectin levels in thyroid carcinoma",
                "abstract": "Batch 5 route-contract independent abstract C.",
                "authors": ["Ben Baker"],
                "journal": "Meta Route Contract",
                "year": "2025",
                "pmid": "900002",
                "doi": "10.1000/b5c",
            },
        ],
    )
    return project_dir


def _audit_ui(
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
        widget.show_target_ia_page("import_dedup")
        widget.show()
        app.processEvents()
        QTest.qWait(80)
        screenshots.append(_capture(widget, screenshot_dir / "01_import_dedup_dedup_adapter.png", "import_dedup_dedup_adapter"))

        rows.extend(_disabled_boundary_rows(widget, failures))
        rows.append(
            _click_and_validate(
                app,
                widget,
                project_dir,
                "META-DEDUP-UI-BUILD-QUEUE",
                "Import & Deduplication",
                "build duplicate review v2 queue",
                "metaBuildDedupReviewQueueButton",
                "ui_runtime/meta_dedup_review_queue_adapter.json",
                lambda payload: (
                    payload.get("service") == "DedupReviewV2Service.build_review_queue"
                    and Path(project_dir / str(payload.get("output_path", ""))).exists()
                    and payload.get("auto_merged") is False
                    and payload.get("auto_deleted") is False
                ),
                "DedupReviewV2Service.build_review_queue",
                failures,
            )
        )
        screenshots.append(_capture(widget, screenshot_dir / "02_import_dedup_after_build_queue.png", "import_dedup_after_build_queue"))

        rows.append(
            _click_and_validate(
                app,
                widget,
                project_dir,
                "META-DEDUP-UI-GENERATE-DEDUPLICATED-SET",
                "Import & Deduplication",
                "generate deduplicated literature v2 set",
                "metaGenerateDeduplicatedSetButton",
                "ui_runtime/meta_deduplicated_set_adapter.json",
                lambda payload: (
                    payload.get("service") == "DedupReviewV2Service.generate_deduplicated_set"
                    and Path(project_dir / str(payload.get("output_path", ""))).exists()
                    and int(payload.get("active_record_count", 0) or 0) == 3
                    and payload.get("auto_screened") is False
                    and payload.get("blocker") == "unresolved_duplicate_groups_require_reviewer_decision"
                ),
                "DedupReviewV2Service.generate_deduplicated_set",
                failures,
            )
        )

        rows.append(
            _click_and_validate(
                app,
                widget,
                project_dir,
                "META-DEDUP-UI-BUILD-SCREENING-QUEUE",
                "Import & Deduplication",
                "build title/abstract screening v2 queue from deduplicated set",
                "metaBuildScreeningQueueFromDedupButton",
                "ui_runtime/meta_dedup_to_screening_queue_adapter.json",
                lambda payload: (
                    payload.get("service") == "TitleAbstractScreeningV2Service.build_queue"
                    and payload.get("source_type") == "deduplicated_literature_v2"
                    and Path(project_dir / str(payload.get("output_path", ""))).exists()
                    and int(payload.get("record_count", 0) or 0) == 3
                    and payload.get("auto_screening_enabled") is False
                    and "dupv2-lit-b5-a-lit-b5-b" in payload.get("warnings", [])
                ),
                "TitleAbstractScreeningV2Service.build_queue",
                failures,
            )
        )
        screenshots.append(_capture(widget, screenshot_dir / "03_import_dedup_after_screening_queue.png", "import_dedup_after_screening_queue"))

        widget.show_target_ia_page("screening")
        app.processEvents()
        QTest.qWait(80)
        screenshots.append(_capture(widget, screenshot_dir / "04_screening_page_after_queue.png", "screening_page_after_queue"))
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()
    return rows


def _disabled_boundary_rows(widget: MetaAnalysisWorkspaceWidget, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    for contract_id, object_name, capability in (
        ("META-DEDUP-UI-AUTO-MERGE-DISABLED", "metaAutoMergeDisabledButton", "auto merge remains disabled"),
        ("META-DEDUP-UI-AUTO-DELETE-DISABLED", "metaAutoDeleteDisabledButton", "auto delete remains disabled"),
        ("META-DEDUP-UI-DIRECT-SEND-DISABLED", "metaSendToScreeningDisabledButton", "direct send without adapter remains disabled"),
    ):
        button = _button(widget, object_name)
        ok = not button.isEnabled() and bool(button.property("disabledReason"))
        rows.append(
            _row(
                contract_id=contract_id,
                ui_page="Import & Deduplication",
                backend_capability=capability,
                object_name=object_name,
                button=button,
                expected_artifact="disabledReason",
                status="disabled" if ok else "broken",
                observed="disabled_with_reason" if ok else "missing_disabled_reason_or_enabled",
            )
        )
        if not ok:
            failures.append(f"{contract_id}: {object_name} should stay disabled with a reason")
    return rows


def _click_and_validate(
    app: QApplication,
    widget: MetaAnalysisWorkspaceWidget,
    project_dir: Path,
    contract_id: str,
    ui_page: str,
    backend_capability: str,
    object_name: str,
    relative_artifact: str,
    predicate,
    service_name: str,
    failures: list[str],
) -> ContractRow:
    button = _button(widget, object_name)
    artifact_path = project_dir / relative_artifact
    button.click()
    app.processEvents()
    QTest.qWait(80)
    payload = _load_json(artifact_path)
    ok = button.isEnabled() and artifact_path.exists() and predicate(payload)
    if not ok:
        failures.append(f"{contract_id}: artifact missing or invalid: {payload}")
    return _row(
        contract_id=contract_id,
        ui_page=ui_page,
        backend_capability=backend_capability,
        object_name=object_name,
        button=button,
        expected_artifact=str(artifact_path),
        status="connected" if ok else "broken",
        observed=f"{service_name}; artifact={artifact_path.name}; payload={_compact_payload(payload)}",
    )


def _row(
    *,
    contract_id: str,
    ui_page: str,
    backend_capability: str,
    object_name: str,
    button: QPushButton,
    expected_artifact: str,
    status: str,
    observed: str,
) -> ContractRow:
    return ContractRow(
        contract_id=contract_id,
        ui_page=ui_page,
        backend_capability=backend_capability,
        branch_source="UIShell high-fidelity Meta page retained; current Integration v2 service adapter.",
        current_file="app/meta_analysis/workspace.py",
        object_name=object_name,
        label=" ".join(button.text().split()),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        disabled_reason=str(button.property("disabledReason") or ""),
        expected_artifact=expected_artifact,
        live_click_test="scripts/ui_route_contract_meta_batch5_dedup_screening.py",
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


def _compact_payload(payload: dict[str, object]) -> str:
    keys = (
        "service",
        "success",
        "group_count",
        "active_record_count",
        "record_count",
        "source_type",
        "blocker",
        "warnings",
    )
    return json.dumps({key: payload.get(key) for key in keys if key in payload}, ensure_ascii=False, sort_keys=True)


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract Meta Batch 5: Dedup to Screening",
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
            "- Auto merge remains disabled.",
            "- Auto delete remains disabled.",
            "- Screening queue creation is explicit and reviewer-gated; queue records remain `not_screened`.",
            "- Unresolved duplicate groups are reported as warnings/blockers and are not hidden.",
        ]
    )
    return "\n".join(lines) + "\n"


def _md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
