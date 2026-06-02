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

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox, QPushButton, QTableWidget, QTableWidgetItem

from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.project_workspace_binding import register_acquisition
from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH9_DATA_PREP_ADAPTERS.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_BIO_BATCH9_DATA_PREP_ADAPTERS.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_bio_batch9_data_prep_adapters"


@dataclass
class ContractRow:
    contract_id: str
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
    batch: str = "Batch 9: Bioinformatics data-prep adapter chain"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    screenshots: list[dict[str, str]] = []
    failures: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_bio_batch9_") as temp_name:
            audit_root = Path(temp_name)
            project = create_bioinformatics_project("Bio Batch 9 Data Prep Adapters", audit_root / "project")
            source_path = _seed_integrated_rnaseq(project.project_root)
            acquisition = register_acquisition(
                project.project_root,
                source_type="local_import",
                source_label=source_path.name,
                strategy="reference",
                selected_paths=[source_path],
            )
            rows.append(
                _service_row(
                    "BIO-B9-ACQUISITION-REGISTER-LOCAL",
                    "data_source",
                    "register_acquisition",
                    "register local integrated RNA-seq file",
                    "app.bioinformatics.project_workspace_binding.register_acquisition",
                    "acquisition plan/record/handoff and source manifest",
                    project.project_root,
                    (acquisition.plan_path, acquisition.record_path, acquisition.handoff_path),
                    failures,
                )
            )

            window = BioinformaticsWorkspaceWidget()
            window.resize(1600, 1200)
            window.show()
            window._current_project = project
            app.processEvents()
            QTest.qWait(120)

            rows.extend(_audit_data_source(app, window, project.project_root, args.screenshot_dir, screenshots, failures))
            rows.extend(_audit_recognition(app, window, project.project_root, args.screenshot_dir, screenshots, failures))
            rows.extend(_audit_readiness(app, window, project.project_root, args.screenshot_dir, screenshots, failures))
            rows.extend(_audit_standardization(app, window, project.project_root, args.screenshot_dir, screenshots, failures))
            rows.extend(_audit_group_design(app, window, project.project_root, args.screenshot_dir, screenshots, failures))

            window.close()
            window.deleteLater()
            app.processEvents()
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_bio_batch9_data_prep_adapters.v1",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "Bioinformatics mature Data Source -> Data Check -> Standardization -> Group Design adapter chain with button-click artifact proof.",
        "screenshots": screenshots,
        "summary": {
            "row_count": len(rows),
            "connected": sum(1 for row in rows if row.status == "connected"),
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
    parser = argparse.ArgumentParser(description="Audit Bio C1 data-prep adapter chain with live button clicks.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _seed_integrated_rnaseq(project_root: Path) -> Path:
    source = project_root / "raw_data" / "local_import" / "integrated_rnaseq.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "gene_id,A1_count,A2_count,B1_count,B2_count,A1_fpkm,A2_fpkm,B1_fpkm,B2_fpkm,"
        "PFFvsPBS_log2FoldChange,PFFvsPBS_pvalue,PFFvsPBS_padj,gene_name,gene_biotype,gene_description\n"
        "ENSMUSG00000026193,10,12,30,32,1.1,1.2,3.0,3.2,1.5,0.01,0.04,Sox17,protein_coding,SRY-box transcription factor 17\n"
        "ENSMUSG00000064351,20,18,6,5,2.1,2.2,0.6,0.5,-1.7,0.02,0.03,mt-Nd1,protein_coding,mitochondrially encoded NADH\n",
        encoding="utf-8",
    )
    return source


def _audit_data_source(
    app: QApplication,
    window: BioinformaticsWorkspaceWidget,
    project_root: Path,
    screenshot_dir: Path,
    screenshots: list[dict[str, str]],
    failures: list[str],
) -> list[ContractRow]:
    rows: list[ContractRow] = []
    window.show_target_ia_page("data_source")
    _settle(app)
    _shot(window, "01_data_source", screenshot_dir, screenshots)
    local_button = _source_button(window, "local_file")
    local_button.click()
    _settle(app)
    rows.append(
        _button_row(
            "BIO-B9-DATA-SOURCE-LOCAL-DRAFT",
            "data_source",
            local_button,
            "app.bioinformatics.data_source_requests.create_data_source_request",
            "data source request draft and request index",
            project_root,
            (project_root / "manifests" / "data_source_requests.json",),
            failures,
            extra_check=lambda: _latest_data_source_request_ok(project_root, "local_file"),
        )
    )
    return rows


def _audit_recognition(
    app: QApplication,
    window: BioinformaticsWorkspaceWidget,
    project_root: Path,
    screenshot_dir: Path,
    screenshots: list[dict[str, str]],
    failures: list[str],
) -> list[ContractRow]:
    window.show_target_ia_page("data_check_preparation")
    _settle(app)
    _shot(window, "02_recognition_before_click", screenshot_dir, screenshots)
    _select_first_recognition_input(window)
    _settle(app)
    button = _button_by_text(window, "开始识别")
    button.click()
    _settle(app, 240)
    _shot(window, "03_recognition_after_click", screenshot_dir, screenshots)
    return [
        _button_row(
            "BIO-B9-DATA-CHECK-RUN-RECOGNITION",
            "data_check_preparation",
            button,
            "app.bioinformatics.project_recognition.run_project_recognition_for_paths",
            "recognition report/current recognition/group preview artifacts",
            project_root,
            (
                project_root / "logs" / "recognition" / "recognition_report.json",
                project_root / "recognized_data" / "current.json",
                project_root / "logs" / "recognition" / "group_preview_report.json",
            ),
            failures,
        )
    ]


def _audit_readiness(
    app: QApplication,
    window: BioinformaticsWorkspaceWidget,
    project_root: Path,
    screenshot_dir: Path,
    screenshots: list[dict[str, str]],
    failures: list[str],
) -> list[ContractRow]:
    _button_by_text(window, "继续：数据准备与标准化").click()
    _settle(app)
    _shot(window, "04_readiness", screenshot_dir, screenshots)
    button = _button_by_object(window, "bioinformaticsRunDataCheckButton")
    button.click()
    _settle(app, 220)
    return [
        _button_row(
            "BIO-B9-DATA-CHECK-RUN-READINESS",
            "data_check_preparation",
            button,
            "app.bioinformatics.project_readiness.run_project_readiness",
            "readiness report and analysis capability matrix",
            project_root,
            (
                project_root / "logs" / "readiness" / "readiness_report.json",
                project_root / "manifests" / "analysis_capability_matrix.json",
            ),
            failures,
        )
    ]


def _audit_standardization(
    app: QApplication,
    window: BioinformaticsWorkspaceWidget,
    project_root: Path,
    screenshot_dir: Path,
    screenshots: list[dict[str, str]],
    failures: list[str],
) -> list[ContractRow]:
    _button_by_text(window, "继续：标准化数据").click()
    _settle(app)
    _shot(window, "05_standardization_before_click", screenshot_dir, screenshots)
    route_ok = window.current_route_key() == "standardized_assets"
    button = _button_by_text(window, "生成标准化数据")
    button.click()
    _settle(app, 260)
    _shot(window, "06_standardization_after_click", screenshot_dir, screenshots)
    rows = [
        _button_row(
            "BIO-B9-DATA-CHECK-OPEN-STANDARDIZATION",
            "data_check_preparation",
            button,
            "app.bioinformatics.workspace.BioinformaticsWorkspaceWidget.show_standardization",
            "readiness continue opens standardized assets page before group design",
            project_root,
            (),
            failures,
            extra_check=lambda: route_ok,
            observed_override=f"current_route_key={window.current_route_key()}; current_page={window.current_page_object_name()}",
        ),
        _button_row(
            "BIO-B9-DATA-CHECK-GENERATE-STANDARDIZED-ASSETS",
            "data_check_preparation",
            button,
            "app.bioinformatics.project_standardization.generate_standardized_assets",
            "standardized asset registry, analysis-ready manifest, and repository manifest",
            project_root,
            (
                project_root / "manifests" / "standardized_assets_registry.json",
                project_root / "standardized_data" / "analysis_ready_assets" / "analysis_ready_manifest.json",
                project_root / "standardized_data" / "repositories" / "repository_manifest.json",
            ),
            failures,
        ),
    ]
    return rows


def _audit_group_design(
    app: QApplication,
    window: BioinformaticsWorkspaceWidget,
    project_root: Path,
    screenshot_dir: Path,
    screenshots: list[dict[str, str]],
    failures: list[str],
) -> list[ContractRow]:
    _button_by_text(window, "继续：分组与分析设计").click()
    _settle(app)
    _prepare_group_table(window)
    _shot(window, "07_group_design_prepared", screenshot_dir, screenshots)
    suggestion = _button_by_object(window, "bioinformaticsGroupDesignSuggestionButton")
    suggestion.click()
    _settle(app)
    save = _button_by_object(window, "bioinformaticsGroupDesignSaveButton")
    save.click()
    _settle(app)
    continue_button = _button_by_object(window, "bioinformaticsGroupDesignContinueButton")
    continue_button.click()
    _settle(app)
    rows = [
        _button_row(
            "BIO-B9-GROUP-DESIGN-SUGGEST-COMPARISON",
            "group_design",
            suggestion,
            "app.bioinformatics.group_comparison_design.build_default_comparison_rows",
            "one-vs-control suggestions preview artifact",
            project_root,
            (project_root / "analysis" / "group_design" / "one_vs_control_suggestions_preview.json",),
            failures,
            extra_check=lambda: _json_value(project_root / "analysis" / "group_design" / "one_vs_control_suggestions_preview.json", "status") == "suggestions_created",
        ),
        _button_row(
            "BIO-B9-GROUP-DESIGN-SAVE-CONFIRMED-DESIGN",
            "group_design",
            save,
            "app.bioinformatics.group_comparison_design.save_group_comparison_design",
            "confirmed group comparison design and updated task center",
            project_root,
            (
                project_root / "manifests" / "group_comparison_design.json",
                project_root / "manifests" / "analysis_task_center.json",
            ),
            failures,
            extra_check=lambda: _json_value(project_root / "manifests" / "group_comparison_design.json", "schema_version") == "bioinformatics_group_comparison_design.v1",
        ),
        _button_row(
            "BIO-B9-GROUP-DESIGN-CONTINUE-ANALYSIS-TASKS",
            "group_design",
            continue_button,
            "app.bioinformatics.workspace.BioinformaticsWorkspaceWidget.show_analysis_tasks",
            "opens Analysis Tasks after saved design gate",
            project_root,
            (),
            failures,
            extra_check=lambda: window.current_target_page_key() == "analysis_tasks",
            observed_override=f"current_target_page_key={window.current_target_page_key()}; current_page={window.current_page_object_name()}",
        ),
    ]
    return rows


def _prepare_group_table(window: BioinformaticsWorkspaceWidget) -> None:
    table = window.findChild(QTableWidget, "groupDesignSampleGroupsTable")
    if table is None:
        raise AssertionError("groupDesignSampleGroupsTable not found")
    for row in range(table.rowCount()):
        inferred = _table_text(table, row, 0)
        if inferred == "A":
            table.setItem(row, 1, QTableWidgetItem("PBS"))
            table.setItem(row, 2, QTableWidgetItem("control"))
        elif inferred == "B":
            table.setItem(row, 1, QTableWidgetItem("PFF"))
            table.setItem(row, 2, QTableWidgetItem("treatment"))


def _select_first_recognition_input(window: BioinformaticsWorkspaceWidget) -> None:
    checks = [
        checkbox
        for checkbox in window.findChildren(QCheckBox)
        if checkbox.objectName().startswith("preRecognitionSelect_")
    ]
    if not checks:
        raise AssertionError("No pre-recognition input checkbox found")
    checks[0].setChecked(True)


def _button_row(
    contract_id: str,
    page_key: str,
    button: QPushButton,
    backend_capability: str,
    runtime_effect: str,
    project_root: Path,
    artifacts: tuple[Path, ...],
    failures: list[str],
    *,
    extra_check: object | None = None,
    observed_override: str = "",
) -> ContractRow:
    ok = all(path.exists() for path in artifacts)
    if callable(extra_check):
        ok = ok and bool(extra_check())
    evidence = "; ".join(_relative(project_root, path) for path in artifacts) if artifacts else "route_state_assertion"
    observed = observed_override or ("artifacts_verified" if ok else "missing_or_invalid_artifact")
    if not ok:
        failures.append(f"{contract_id}: {observed}; evidence={evidence}")
    return ContractRow(
        contract_id=contract_id,
        page_key=page_key,
        object_name=button.objectName(),
        label=button.text(),
        backend_capability=backend_capability,
        source_file=backend_capability.rsplit(".", 1)[0].replace(".", "/") + ".py",
        runtime_effect=runtime_effect,
        artifact_evidence=evidence,
        live_click_test="clicked_visible_button",
        status="connected" if ok else "broken",
        observed=observed,
    )


def _service_row(
    contract_id: str,
    page_key: str,
    object_name: str,
    label: str,
    backend_capability: str,
    runtime_effect: str,
    project_root: Path,
    artifacts: tuple[Path, ...],
    failures: list[str],
) -> ContractRow:
    ok = all(path.exists() for path in artifacts)
    if not ok:
        failures.append(f"{contract_id}: service artifacts missing")
    return ContractRow(
        contract_id=contract_id,
        page_key=page_key,
        object_name=object_name,
        label=label,
        backend_capability=backend_capability,
        source_file="app/bioinformatics/project_workspace_binding.py",
        runtime_effect=runtime_effect,
        artifact_evidence="; ".join(_relative(project_root, path) for path in artifacts),
        live_click_test="adapter_service_seed_for_ui_click_chain",
        status="connected" if ok else "broken",
        observed="service_artifacts_verified" if ok else "service_artifacts_missing",
    )


def _source_button(window: BioinformaticsWorkspaceWidget, source_key: str) -> QPushButton:
    matches = [
        button
        for button in window.findChildren(QPushButton, "bioinformaticsDataSourceSelectPreviewButton")
        if button.isVisible() and button.property("sourceKey") == source_key
    ]
    if len(matches) != 1:
        raise AssertionError(f"Expected one source button for {source_key}, observed {len(matches)}")
    return matches[0]


def _button_by_text(window: BioinformaticsWorkspaceWidget, text: str) -> QPushButton:
    matches = [button for button in window.findChildren(QPushButton) if button.isVisible() and button.text() == text]
    if len(matches) != 1:
        raise AssertionError(f"Expected one visible button text={text!r}, observed {len(matches)}")
    return matches[0]


def _button_by_object(window: BioinformaticsWorkspaceWidget, object_name: str) -> QPushButton:
    matches = [button for button in window.findChildren(QPushButton, object_name) if button.isVisible()]
    if len(matches) != 1:
        raise AssertionError(f"Expected one visible button object={object_name!r}, observed {len(matches)}")
    return matches[0]


def _latest_data_source_request_ok(project_root: Path, source_key: str) -> bool:
    index = project_root / "manifests" / "data_source_requests.json"
    if not index.exists():
        return False
    payload = json.loads(index.read_text(encoding="utf-8"))
    requests = [item for item in payload.get("requests", []) or [] if isinstance(item, dict)]
    if not requests:
        return False
    latest = requests[-1]
    return latest.get("status") == "draft" and latest.get("internal_selection", {}).get("source_key") == source_key


def _json_value(path: Path, key: str) -> object:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get(key)


def _table_text(table: QTableWidget, row: int, col: int) -> str:
    item = table.item(row, col)
    return item.text().strip() if item is not None else ""


def _shot(window: BioinformaticsWorkspaceWidget, stem: str, screenshot_dir: Path, screenshots: list[dict[str, str]]) -> None:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = screenshot_dir / f"{stem}.png"
    pixmap = window.grab()
    pixmap.save(str(path))
    screenshots.append({"page": stem, "path": str(path.relative_to(REPO_ROOT))})


def _settle(app: QApplication, ms: int = 140) -> None:
    app.processEvents()
    QTest.qWait(ms)
    app.processEvents()


def _relative(project_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def _git(*args: str) -> str:
    import subprocess

    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# Bioinformatics Batch 9 Data-Prep Adapter Route Contract",
        "",
        f"- branch: `{payload.get('branch')}`",
        f"- head: `{payload.get('head')}`",
        f"- scope: {payload.get('scope')}",
        f"- row_count: `{summary.get('row_count')}`",
        f"- connected: `{summary.get('connected')}`",
        f"- broken: `{summary.get('broken')}`",
        "",
        "## Rows",
        "",
        "| contract | page | object | label | status | backend capability | evidence |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload.get("rows", []) or []:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| `{contract_id}` | `{page_key}` | `{object_name}` | {label} | `{status}` | `{backend_capability}` | {artifact_evidence} |".format(
                contract_id=row.get("contract_id", ""),
                page_key=row.get("page_key", ""),
                object_name=row.get("object_name", ""),
                label=str(row.get("label", "")).replace("|", "/"),
                status=row.get("status", ""),
                backend_capability=row.get("backend_capability", ""),
                artifact_evidence=str(row.get("artifact_evidence", "")).replace("|", "/"),
            )
        )
    lines.extend(["", "## Screenshots", ""])
    for item in payload.get("screenshots", []) or []:
        if isinstance(item, dict):
            lines.append(f"- `{item.get('page')}`: `{item.get('path')}`")
    failures = summary.get("failures") if isinstance(summary, dict) else []
    if failures:
        lines.extend(["", "## Failures", ""])
        for failure in failures:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
