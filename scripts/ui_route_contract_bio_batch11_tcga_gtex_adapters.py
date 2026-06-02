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
from typing import Callable


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.workflow_pages import BioinformaticsDataSourceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH11_TCGA_GTEX_ADAPTERS.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH11_TCGA_GTEX_ADAPTERS.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_bio_batch11_tcga_gtex_adapters"


@dataclass
class ContractRow:
    contract_id: str
    source: str
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
    batch: str = "Batch 11: Bioinformatics TCGA/GTEx visible adapters"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    screenshots: list[dict[str, str]] = []
    failures: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_bio_batch11_tcga_gtex_") as temp_name:
            project = create_bioinformatics_project("Bio Batch 11 TCGA GTEx Adapters", Path(temp_name) / "project")
            widget = BioinformaticsDataSourceWidget()
            widget.resize(1600, 1200)
            widget.show()
            widget.refresh_project(project)
            _settle(app, 120)
            rows.extend(_audit_tcga(app, widget, project.project_root, args.screenshot_dir, screenshots, failures))
            rows.extend(_audit_gtex(app, widget, project.project_root, args.screenshot_dir, screenshots, failures))
            widget.close()
            widget.deleteLater()
            _settle(app, 40)
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_bio_batch11_tcga_gtex_adapters.v1",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": (
            "Bioinformatics mature Data Source visible TCGA/GTEx adapters: "
            "source request, metadata preview, download-plan artifact, and explicit disabled gates for download/build."
        ),
        "gate_policy": {
            "light_validation_mode": os.environ.get("BIOINF_LIGHT_VALIDATION_MODE", ""),
            "download_buttons": "disabled unless BIOINF_LIGHT_VALIDATION_MODE=1 and a plan exists",
            "formal_analysis": "not opened by this batch",
        },
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
    parser = argparse.ArgumentParser(description="Audit Bio C1 visible TCGA/GTEx Data Source adapters.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _audit_tcga(
    app: QApplication,
    widget: BioinformaticsDataSourceWidget,
    project_root: Path,
    screenshot_dir: Path,
    screenshots: list[dict[str, str]],
    failures: list[str],
) -> list[ContractRow]:
    rows: list[ContractRow] = []
    source_button = _source_button(widget, "tcga")
    source_button.click()
    _settle(app, 120)
    _shot(widget, "01_tcga_adapter_ready", screenshot_dir, screenshots)
    rows.append(
        _connected_or_broken(
            "BIO-B11-TCGA-SOURCE-REQUEST",
            "TCGA",
            "data_source",
            source_button,
            "app.bioinformatics.data_source_requests.create_data_source_request",
            "creates visible TCGA Data Source request draft and opens TCGA/GTEx adapter panel",
            lambda: _latest_request_evidence(project_root, "tcga"),
            failures,
        )
    )
    rows.append(
        _click_or_disabled(
            "BIO-B11-TCGA-METADATA-PREVIEW",
            "TCGA",
            widget,
            "bioinformaticsTcgaPreviewButton",
            "app.bioinformatics.data_sources.tcga_preview.TCGAMetadataPreviewService.build_preview",
            "calls GDC metadata preview and renders case/sample/file counts",
            lambda: _text_evidence(widget, "bioinformaticsExternalDataAdapterStatus", required=("TCGA preview",)),
            failures,
            settle_ms=900,
        )
    )
    _shot(widget, "02_tcga_metadata_preview", screenshot_dir, screenshots)
    rows.append(
        _click_or_disabled(
            "BIO-B11-TCGA-DOWNLOAD-PLAN",
            "TCGA",
            widget,
            "bioinformaticsTcgaCreatePlanButton",
            "app.bioinformatics.data_sources.tcga_preview.write_tcga_download_plan_draft",
            "writes TCGA download plan draft and plan-only acquisition record",
            lambda: _glob_evidence(project_root, "acquisition/tcga_download_plans/*.json"),
            failures,
            settle_ms=180,
        )
    )
    _shot(widget, "03_tcga_download_plan", screenshot_dir, screenshots)
    rows.append(
        _click_or_disabled(
            "BIO-B11-TCGA-LIGHT-DOWNLOAD-GATE",
            "TCGA",
            widget,
            "bioinformaticsTcgaDownloadRawButton",
            "app.bioinformatics.data_sources.tcga_download_executor.TCGADownloadPlanExecutor.execute_plan",
            "executes only when light validation gate is explicitly opened",
            lambda: _glob_evidence(project_root, "acquisition/download_receipts/tcga-dl-*.json"),
            failures,
            settle_ms=240,
            allow_disabled=True,
        )
    )
    rows.append(
        _click_or_disabled(
            "BIO-B11-TCGA-EXPRESSION-BUILD-GATE",
            "TCGA",
            widget,
            "bioinformaticsTcgaBuildExpressionButton",
            "app.bioinformatics.data_sources.tcga_expression_builder.TCGAExpressionQuantificationBuilder.build_from_record",
            "builds expression matrix only after a raw download receipt exists",
            lambda: _glob_evidence(project_root, "standardized_data/tcga/**/tcga_expression_build_manifest.json"),
            failures,
            settle_ms=240,
            allow_disabled=True,
        )
    )
    return rows


def _audit_gtex(
    app: QApplication,
    widget: BioinformaticsDataSourceWidget,
    project_root: Path,
    screenshot_dir: Path,
    screenshots: list[dict[str, str]],
    failures: list[str],
) -> list[ContractRow]:
    rows: list[ContractRow] = []
    source_button = _source_button(widget, "gtex")
    source_button.click()
    _settle(app, 120)
    _shot(widget, "04_gtex_adapter_ready", screenshot_dir, screenshots)
    rows.append(
        _connected_or_broken(
            "BIO-B11-GTEX-SOURCE-REQUEST",
            "GTEx",
            "data_source",
            source_button,
            "app.bioinformatics.data_source_requests.create_data_source_request",
            "creates visible GTEx Data Source request draft and opens TCGA/GTEx adapter panel",
            lambda: _latest_request_evidence(project_root, "gtex"),
            failures,
        )
    )
    rows.append(
        _click_or_disabled(
            "BIO-B11-GTEX-METADATA-PREVIEW",
            "GTEx",
            widget,
            "bioinformaticsGtexPreviewButton",
            "app.bioinformatics.data_sources.gtex_preview.GTExMetadataPreviewService.build_preview",
            "calls GTEx tissue metadata preview and renders donor/sample/file counts",
            lambda: _text_evidence(widget, "bioinformaticsExternalDataAdapterStatus", required=("GTEx preview",)),
            failures,
            settle_ms=900,
        )
    )
    _shot(widget, "05_gtex_metadata_preview", screenshot_dir, screenshots)
    rows.append(
        _click_or_disabled(
            "BIO-B11-GTEX-DOWNLOAD-PLAN",
            "GTEx",
            widget,
            "bioinformaticsGtexCreatePlanButton",
            "app.bioinformatics.data_sources.gtex_preview.write_gtex_download_plan_draft",
            "writes GTEx download plan draft and plan-only acquisition record",
            lambda: _glob_evidence(project_root, "acquisition/gtex_download_plans/*.json"),
            failures,
            settle_ms=180,
        )
    )
    _shot(widget, "06_gtex_download_plan", screenshot_dir, screenshots)
    rows.append(
        _click_or_disabled(
            "BIO-B11-GTEX-LIGHT-DOWNLOAD-GATE",
            "GTEx",
            widget,
            "bioinformaticsGtexDownloadRawButton",
            "app.bioinformatics.data_sources.gtex_download_executor.GTExDownloadPlanExecutor.execute_plan",
            "executes only when light validation gate is explicitly opened",
            lambda: _glob_evidence(project_root, "acquisition/download_receipts/gtex-dl-*.json"),
            failures,
            settle_ms=240,
            allow_disabled=True,
        )
    )
    rows.append(
        _click_or_disabled(
            "BIO-B11-GTEX-EXPRESSION-BUILD-GATE",
            "GTEx",
            widget,
            "bioinformaticsGtexBuildExpressionButton",
            "app.bioinformatics.data_sources.gtex_expression_builder.GTExExpressionMatrixBuilder.build_from_record",
            "builds expression matrix only after a raw download receipt exists",
            lambda: _glob_evidence(project_root, "standardized_data/gtex/**/gtex_expression_build_manifest.json"),
            failures,
            settle_ms=240,
            allow_disabled=True,
        )
    )
    return rows


def _click_or_disabled(
    contract_id: str,
    source: str,
    root: QWidget,
    object_name: str,
    backend_capability: str,
    runtime_effect: str,
    evidence: Callable[[], str],
    failures: list[str],
    *,
    settle_ms: int,
    allow_disabled: bool = False,
) -> ContractRow:
    button = _button(root, object_name)
    if not button.isEnabled():
        reason = str(button.property("disabledReason") or button.toolTip() or "disabled_without_reason")
        if not reason:
            reason = "disabled_without_reason"
        if not allow_disabled:
            failures.append(f"{contract_id}: disabled unexpectedly: {reason}")
        return _row(
            contract_id,
            source,
            "data_source",
            button,
            backend_capability,
            runtime_effect,
            reason,
            "button disabled",
            "disabled" if reason != "disabled_without_reason" else "broken",
            reason,
        )
    button.click()
    _settle(QApplication.instance(), settle_ms)
    observed = evidence()
    status = "connected" if observed else "broken"
    if status == "broken":
        failures.append(f"{contract_id}: click did not produce expected evidence")
        observed = "missing expected artifact/effect"
    return _row(contract_id, source, "data_source", button, backend_capability, runtime_effect, observed, "button.click()", status)


def _connected_or_broken(
    contract_id: str,
    source: str,
    page_key: str,
    button: QPushButton,
    backend_capability: str,
    runtime_effect: str,
    evidence: Callable[[], str],
    failures: list[str],
) -> ContractRow:
    observed = evidence()
    status = "connected" if observed else "broken"
    if status == "broken":
        failures.append(f"{contract_id}: missing expected source request evidence")
        observed = "missing expected artifact/effect"
    return _row(contract_id, source, page_key, button, backend_capability, runtime_effect, observed, "button.click()", status)


def _row(
    contract_id: str,
    source: str,
    page_key: str,
    button: QPushButton,
    backend_capability: str,
    runtime_effect: str,
    observed: str,
    live_click_test: str,
    status: str,
    disabled_reason: str = "",
) -> ContractRow:
    return ContractRow(
        contract_id=contract_id,
        source=source,
        page_key=page_key,
        object_name=button.objectName(),
        label=button.text().replace("\n", " / "),
        backend_capability=backend_capability,
        source_file="app/bioinformatics/workflow_pages.py",
        runtime_effect=runtime_effect,
        artifact_evidence=observed,
        live_click_test=live_click_test,
        status=status,
        observed=observed,
        disabled_reason=disabled_reason,
    )


def _source_button(root: QWidget, source_key: str) -> QPushButton:
    for button in root.findChildren(QPushButton):
        if button.objectName() == "bioinformaticsDataSourceSelectPreviewButton" and str(button.property("sourceKey") or "") == source_key:
            return button
    raise LookupError(f"source button not found: {source_key}")


def _button(root: QWidget, object_name: str) -> QPushButton:
    button = root.findChild(QPushButton, object_name)
    if button is None:
        raise LookupError(f"button not found: {object_name}")
    return button


def _text_evidence(root: QWidget, object_name: str, *, required: tuple[str, ...]) -> str:
    widget = root.findChild(QWidget, object_name)
    text = widget.toPlainText() if hasattr(widget, "toPlainText") else ""
    if all(part in text for part in required):
        return text.replace("\n", " | ")[:900]
    return ""


def _latest_request_evidence(project_root: Path, source_type: str) -> str:
    index_path = project_root / "manifests" / "data_source_requests.json"
    if not index_path.exists():
        return ""
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    requests = [item for item in payload.get("requests", []) if isinstance(item, dict)]
    matches = [item for item in requests if str(item.get("source_type") or "").lower() == source_type.lower()]
    if not matches:
        return ""
    latest = matches[-1]
    return f"{index_path}; request_id={latest.get('request_id')}; status={latest.get('status')}; source_type={latest.get('source_type')}"


def _glob_evidence(project_root: Path, pattern: str) -> str:
    paths = sorted(project_root.glob(pattern), key=lambda path: path.stat().st_mtime if path.exists() else 0)
    if not paths:
        return ""
    return "; ".join(str(path) for path in paths[-3:])


def _shot(widget: QWidget, name: str, screenshot_dir: Path, screenshots: list[dict[str, str]]) -> None:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = screenshot_dir / f"{name}.png"
    widget.grab().save(str(path))
    screenshots.append({"name": name, "path": str(path.relative_to(REPO_ROOT))})


def _settle(app: QApplication | None, ms: int = 120) -> None:
    if app is not None:
        app.processEvents()
    QTest.qWait(ms)
    if app is not None:
        app.processEvents()


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        return ""


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# Bio C1 Batch 11 TCGA/GTEx Adapter Route Contract",
        "",
        f"- branch: `{payload.get('branch')}`",
        f"- head: `{payload.get('head')}`",
        f"- scope: {payload.get('scope')}",
        f"- rows: {summary.get('row_count')}; connected: {summary.get('connected')}; disabled: {summary.get('disabled')}; broken: {summary.get('broken')}",
        "",
        "## Screenshots",
        "",
    ]
    for shot in payload.get("screenshots", []):
        if isinstance(shot, dict):
            lines.append(f"- `{shot.get('name')}`: `{shot.get('path')}`")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| contract | source | button | status | backend | evidence | disabled reason |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("contract_id", "")),
                    str(row.get("source", "")),
                    f"`{row.get('object_name', '')}`",
                    str(row.get("status", "")),
                    str(row.get("backend_capability", "")),
                    str(row.get("artifact_evidence", "")).replace("\n", " ")[:220],
                    str(row.get("disabled_reason", "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
