from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox, QPushButton, QTableWidget, QWidget

from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH10_GEO_ONLINE_RETRIEVAL.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH10_GEO_ONLINE_RETRIEVAL.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_bio_batch10_geo_online_retrieval"
DEFAULT_ACCESSIONS = ("GSE6004", "GSE153659")


@dataclass
class ContractRow:
    contract_id: str
    accession: str
    page_key: str
    object_name: str
    label: str
    backend_capability: str
    source_file: str
    runtime_effect: str
    artifact_evidence: str
    live_click_test: str
    status: str
    observed: str
    disabled_reason: str = ""
    batch: str = "Batch 10: Bioinformatics GEO online retrieval adapter"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    screenshots: list[dict[str, str]] = []
    failures: list[str] = []
    try:
        for accession in args.accessions:
            rows.extend(_audit_accession(app, accession, args.screenshot_dir, screenshots, failures))
    finally:
        cleanup_qt_top_level_widgets(app)
    payload = {
        "schema_version": "ui_route_contract_bio_batch10_geo_online_retrieval.v1",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Bioinformatics Data Source visible GEO adapter: GSE metadata search, project registration, online metadata download, online asset download, recognition, and readiness.",
        "accessions": list(args.accessions),
        "screenshots": screenshots,
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
    print(f"json={args.json_out}")
    print(f"markdown={args.markdown_out}")
    print(f"screenshot_dir={args.screenshot_dir}")
    print(f"rows={len(rows)}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit visible Bio Data Source GEO online retrieval adapters.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    parser.add_argument("--accessions", nargs="+", default=DEFAULT_ACCESSIONS)
    return parser.parse_args(argv)


def _audit_accession(
    app: QApplication,
    accession: str,
    screenshot_dir: Path,
    screenshots: list[dict[str, str]],
    failures: list[str],
) -> list[ContractRow]:
    rows: list[ContractRow] = []
    with tempfile.TemporaryDirectory(prefix=f"biomedpilot_bio_batch10_{accession.lower()}_") as temp_name:
        project = create_bioinformatics_project(f"Bio Batch 10 {accession}", Path(temp_name) / "project")
        window = BioinformaticsWorkspaceWidget()
        window.resize(1600, 1200)
        window.show()
        window._current_project = project
        window.show_target_ia_page("data_source")
        _settle(app, 200)

        source_button = _source_button(window, "geo")
        source_button.click()
        _settle(app, 160)
        rows.append(
            _row(
                "CONFIGURE-GEO-SOURCE",
                accession,
                "data_source",
                source_button,
                "app.bioinformatics.data_source_requests.create_data_source_request",
                "app/bioinformatics/workflow_pages.py",
                "creates visible Data Source request draft and opens GEO adapter panel",
                _existing(project.project_root / "manifests" / "data_source_requests.json", failures, accession, "data_source_request"),
                "button.click()",
            )
        )

        input_widget = _widget(window, "bioinformaticsGeoAccessionInput")
        input_widget.setText(accession)
        _settle(app, 80)
        _shot(window, f"{accession}_01_geo_adapter_ready", screenshot_dir, screenshots)

        search_button = _button(window, "bioinformaticsGeoSearchMetadataButton")
        search_button.click()
        _settle(app, 320)
        rows.append(
            _row(
                "SEARCH-GEO-METADATA",
                accession,
                "data_source",
                search_button,
                "app.bioinformatics.legacy.geo_tool.geo_info_fetcher.GeoInfoFetcher.search_series",
                "app/bioinformatics/workflow_pages.py",
                "queries GEO metadata for exact GSE accession and renders candidate preview",
                _status_text(window, "bioinformaticsGeoRetrievalStatus"),
                "button.click()",
            )
        )

        add_button = _button(window, "bioinformaticsGeoAddToProjectButton")
        add_button.click()
        _settle(app, 160)
        rows.append(
            _row(
                "ADD-GEO-ACCESSION",
                accession,
                "data_source",
                add_button,
                "app.bioinformatics.project_workspace_binding.register_acquisition",
                "app/bioinformatics/workflow_pages.py",
                "registers GEO accession as plan-only pending source",
                _existing_any(
                    project.project_root,
                    ("acquisition/plans", "acquisition/records", "acquisition/handoffs"),
                    failures,
                    accession,
                    "geo_accession_registration",
                ),
                "button.click()",
            )
        )

        metadata_button = _button(window, "bioinformaticsGeoDownloadMetadataButton")
        metadata_button.click()
        _settle(app, 420)
        _shot(window, f"{accession}_02_geo_metadata_downloaded", screenshot_dir, screenshots)
        rows.append(
            _row(
                "DOWNLOAD-GEO-METADATA",
                accession,
                "data_source",
                metadata_button,
                "app.bioinformatics.download.DatasetDownloadService.create_candidate_download_task",
                "app/bioinformatics/download/dataset_download_service.py",
                "downloads GEO family SOFT metadata, writes receipt, asset manifest, and acquisition record",
                _metadata_download_evidence(project.project_root, accession, failures),
                "button.click()",
            )
        )

        asset_button = _button(window, "bioinformaticsGeoDownloadAssetsButton")
        asset_button.click()
        _settle(app, 420)
        _shot(window, f"{accession}_03_geo_assets_downloaded", screenshot_dir, screenshots)
        rows.append(
            _row(
                "DOWNLOAD-GEO-ASSETS",
                accession,
                "data_source",
                asset_button,
                "app.bioinformatics.download.DatasetDownloadService.download_geo_manifest_assets",
                "app/bioinformatics/download/dataset_download_service.py",
                "downloads selected GEO Series Matrix/supplementary assets and registers downloaded files for recognition",
                _asset_download_evidence(project.project_root, accession, failures),
                "button.click()",
            )
        )

        continue_button = _button(window, "bioinformaticsGeoContinueRecognitionButton")
        continue_button.click()
        _settle(app, 180)
        rows.append(
            _row(
                "CONTINUE-TO-RECOGNITION",
                accession,
                "data_source",
                continue_button,
                "app.bioinformatics.workspace.BioinformaticsWorkspaceWidget.show_recognition",
                "app/bioinformatics/workspace.py",
                "opens Data Check & Preparation recognition route after downloaded GEO files are ready",
                _route_evidence(window, "recognition", failures, accession),
                "button.click()",
            )
        )

        _select_first_recognition_input(window)
        _settle(app, 100)
        recognition_button = _button(window, "bioinformaticsRunRecognitionButton")
        recognition_button.click()
        _settle(app, 260)
        _shot(window, f"{accession}_04_recognition_complete", screenshot_dir, screenshots)
        rows.append(
            _row(
                "RUN-RECOGNITION",
                accession,
                "data_check_preparation",
                recognition_button,
                "app.bioinformatics.project_recognition.run_project_recognition_for_paths",
                "app/bioinformatics/project_recognition.py",
                "writes recognition report, current recognized data, and group preview artifacts",
                _existing_many(
                    project.project_root,
                    (
                        "logs/recognition/recognition_report.json",
                        "recognized_data/current.json",
                        "logs/recognition/group_preview_report.json",
                    ),
                    failures,
                    accession,
                    "recognition",
                ),
                "button.click()",
            )
        )

        readiness_continue_button = _button(window, "bioinformaticsRecognitionContinueReadinessButton")
        readiness_continue_button.click()
        _settle(app, 180)
        rows.append(
            _row(
                "CONTINUE-TO-READINESS",
                accession,
                "data_check_preparation",
                readiness_continue_button,
                "app.bioinformatics.workspace.BioinformaticsWorkspaceWidget.show_readiness",
                "app/bioinformatics/workspace.py",
                "opens readiness dashboard after recognition artifact gate passes",
                _route_evidence(window, "readiness", failures, accession),
                "button.click()",
            )
        )

        readiness_button = _button(window, "bioinformaticsRunDataCheckButton")
        readiness_button.click()
        _settle(app, 260)
        _shot(window, f"{accession}_05_readiness_complete", screenshot_dir, screenshots)
        rows.append(
            _row(
                "RUN-READINESS",
                accession,
                "data_check_preparation",
                readiness_button,
                "app.bioinformatics.project_readiness.run_project_readiness",
                "app/bioinformatics/project_readiness.py",
                "writes readiness report and analysis capability matrix",
                _existing_many(
                    project.project_root,
                    (
                        "logs/readiness/readiness_report.json",
                        "manifests/analysis_capability_matrix.json",
                    ),
                    failures,
                    accession,
                    "readiness",
                ),
                "button.click()",
            )
        )
        window.close()
        window.deleteLater()
        _settle(app, 80)
    return rows


def _row(
    suffix: str,
    accession: str,
    page_key: str,
    button: QPushButton,
    backend_capability: str,
    source_file: str,
    runtime_effect: str,
    artifact_evidence: str,
    live_click_test: str,
) -> ContractRow:
    status = "connected" if artifact_evidence and "missing:" not in artifact_evidence else "broken"
    return ContractRow(
        contract_id=f"BIO-B10-{accession}-{suffix}",
        accession=accession,
        page_key=page_key,
        object_name=button.objectName(),
        label=button.text().replace("\n", " / "),
        backend_capability=backend_capability,
        source_file=source_file,
        runtime_effect=runtime_effect,
        artifact_evidence=artifact_evidence,
        live_click_test=live_click_test,
        status=status,
        observed=f"enabled={button.isEnabled()}; disabledReason={button.property('disabledReason') or ''}",
        disabled_reason=str(button.property("disabledReason") or ""),
    )


def _metadata_download_evidence(project_root: Path, accession: str, failures: list[str]) -> str:
    target = project_root / "raw_data" / "geo" / accession / f"{accession}_family.soft.gz"
    manifest = _latest_geo_manifest(project_root, accession)
    receipts = sorted((project_root / "acquisition" / "download_receipts").glob("*.json"))
    evidence = _existing(target, failures, accession, "geo_family_soft")
    if manifest is None:
        failures.append(f"{accession}: missing geo asset manifest after metadata download")
        evidence += "; missing:geo_asset_manifest"
    else:
        evidence += f"; {manifest.relative_to(project_root)}"
    if receipts:
        evidence += f"; {receipts[-1].relative_to(project_root)}"
    return evidence


def _asset_download_evidence(project_root: Path, accession: str, failures: list[str]) -> str:
    manifest = _latest_geo_manifest(project_root, accession)
    if manifest is None:
        failures.append(f"{accession}: missing geo asset manifest after asset download")
        return "missing:geo_asset_manifest"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assets = [item for item in payload.get("assets", []) or [] if isinstance(item, dict)]
    downloaded = [
        Path(str(item.get("local_path") or ""))
        for item in assets
        if item.get("status") == "downloaded" and str(item.get("local_path") or "")
    ]
    existing = [path for path in downloaded if path.is_file()]
    if not existing:
        failures.append(f"{accession}: no downloaded GEO assets after asset download")
        return "missing:downloaded_geo_assets"
    return "; ".join(str(path.relative_to(project_root)) for path in existing[:4])


def _latest_geo_manifest(project_root: Path, accession: str) -> Path | None:
    matches = sorted((project_root / "raw_data" / "geo" / accession).glob("*_asset_manifest.json"))
    if matches:
        return matches[-1]
    matches = sorted((project_root / "raw_data" / "geo" / accession).rglob("*_asset_manifest.json"))
    return matches[-1] if matches else None


def _route_evidence(window: QWidget, expected_route: str, failures: list[str], accession: str) -> str:
    route = str(getattr(window, "_current_route_key", "") or "")
    if route != expected_route:
        failures.append(f"{accession}: expected route {expected_route}, got {route}")
        return f"missing:route:{expected_route}; observed={route}"
    return f"route={route}"


def _existing(path: Path, failures: list[str], accession: str, label: str) -> str:
    if not path.exists():
        failures.append(f"{accession}: missing {label}: {path}")
        return f"missing:{path}"
    return str(path.relative_to(path.parents[3] if "raw_data" in path.parts else path.parent.parent.parent))


def _existing_any(project_root: Path, dirs: tuple[str, ...], failures: list[str], accession: str, label: str) -> str:
    found: list[Path] = []
    for dirname in dirs:
        directory = project_root / dirname
        found.extend(path for path in directory.glob("*.json") if path.is_file())
    if not found:
        failures.append(f"{accession}: missing {label} artifacts under {dirs}")
        return f"missing:{label}"
    return "; ".join(str(path.relative_to(project_root)) for path in sorted(found)[-6:])


def _existing_many(project_root: Path, relatives: tuple[str, ...], failures: list[str], accession: str, label: str) -> str:
    missing: list[str] = []
    existing: list[str] = []
    for relative in relatives:
        path = project_root / relative
        if path.exists():
            existing.append(relative)
        else:
            missing.append(relative)
    if missing:
        failures.append(f"{accession}: missing {label} artifacts: {missing}")
        return "missing:" + ",".join(missing)
    return "; ".join(existing)


def _source_button(window: QWidget, source_key: str) -> QPushButton:
    for button in window.findChildren(QPushButton):
        if button.objectName() == "bioinformaticsDataSourceSelectPreviewButton" and button.property("sourceKey") == source_key:
            return button
    raise LookupError(f"source button not found: {source_key}")


def _button(window: QWidget, object_name: str) -> QPushButton:
    button = window.findChild(QPushButton, object_name)
    if button is None:
        raise LookupError(f"button not found: {object_name}")
    return button


def _widget(window: QWidget, object_name: str) -> Any:
    widget = window.findChild(QWidget, object_name)
    if widget is None:
        raise LookupError(f"widget not found: {object_name}")
    return widget


def _status_text(window: QWidget, object_name: str) -> str:
    widget = _widget(window, object_name)
    if hasattr(widget, "toPlainText"):
        return str(widget.toPlainText())
    if hasattr(widget, "text"):
        return str(widget.text())
    return object_name


def _select_first_recognition_input(window: QWidget) -> None:
    checks = [
        checkbox
        for checkbox in window.findChildren(QCheckBox)
        if checkbox.objectName().startswith("preRecognitionSelect_")
    ]
    if not checks:
        raise LookupError("pre-recognition input checkbox not found")
    checks[0].setChecked(True)


def _shot(window: QWidget, stem: str, screenshot_dir: Path, screenshots: list[dict[str, str]]) -> None:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = screenshot_dir / f"{stem}.png"
    window.grab().save(str(path))
    screenshots.append({"page": stem, "path": str(path.relative_to(REPO_ROOT))})


def _settle(app: QApplication, ms: int = 120) -> None:
    app.processEvents()
    QTest.qWait(ms)
    app.processEvents()


def _render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Bioinformatics Batch 10 GEO Online Retrieval Route Contract",
        "",
        f"- branch: `{payload['branch']}`",
        f"- head: `{payload['head']}`",
        f"- accessions: `{', '.join(payload['accessions'])}`",
        f"- row_count: `{summary['row_count']}`",
        f"- connected: `{summary['connected']}`",
        f"- disabled: `{summary['disabled']}`",
        f"- broken: `{summary['broken']}`",
        "",
        "## Rows",
        "",
        "| contract | accession | page | object | label | status | backend capability | evidence |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| `{}` | `{}` | `{}` | `{}` | {} | `{}` | `{}` | {} |".format(
                row["contract_id"],
                row["accession"],
                row["page_key"],
                row["object_name"],
                row["label"],
                row["status"],
                row["backend_capability"],
                row["artifact_evidence"],
            )
        )
    lines.extend(["", "## Screenshots", ""])
    for item in payload["screenshots"]:
        lines.append(f"- `{item['page']}`: `{item['path']}`")
    if summary["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in summary["failures"]:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def _git(*args: str) -> str:
    import subprocess

    return subprocess.check_output(("git", *args), cwd=REPO_ROOT, text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
