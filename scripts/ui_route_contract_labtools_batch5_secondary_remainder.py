from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QPushButton, QTabWidget, QTextEdit

from app.labtools.workspace import LabToolsWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_LABTOOLS_BATCH5_SECONDARY_REMAINDER.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_LABTOOLS_BATCH5_SECONDARY_REMAINDER.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_labtools_batch5_secondary_remainder"


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
    batch: str = "Batch 5: LabTools Secondary Remainder"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    screenshots: list[dict[str, str]] = []
    failures: list[str] = []
    try:
        widget = LabToolsWorkspaceWidget()
        rows.extend(_audit_nucleic_acid(app, widget, failures))
        rows.extend(_audit_disabled_secondary(widget, "immuno_absorbance", "免疫与吸光度实验", failures))
        rows.extend(_audit_disabled_secondary(widget, "ihc", "免疫组化", failures))
        screenshots.extend(_capture_screenshots(app, widget, args.screenshot_dir))
        widget.close()
        widget.deleteLater()
    finally:
        cleanup_qt_top_level_widgets(app)

    broken = [row.contract_id for row in rows if row.status == "broken"]
    failures.extend(f"{contract_id}: broken route contract row" for contract_id in broken)
    payload = {
        "schema_version": "ui_route_contract_labtools_batch5_secondary_remainder.v1",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "LabTools remaining secondary modules: connect Nucleic Acid qPCR mix adapter; keep Immunoassay/Absorbance and IHC disabled with explicit reasons.",
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
    parser = argparse.ArgumentParser(description="Run LabTools secondary remainder route contract live-click audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _audit_nucleic_acid(app: QApplication, widget: LabToolsWorkspaceWidget, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget.show_experiment_modules()
    button = _secondary_button(widget, "nucleic_acid_experiments")
    button.click()
    app.processEvents()
    ok = widget.current_page_key() == "nucleic_acid_experiments"
    rows.append(_row("LABTOOLS-SECONDARY-NUCLEIC-NAV", "Nucleic Acid", "app/labtools/workspace.py", button, "navigates to Nucleic Acid secondary page", f"current_page_key={widget.current_page_key()}", ok))
    if not ok:
        failures.append("nucleic acid secondary navigation failed")
    page = widget.current_page_widget()
    tabs = _find_child(page, QTabWidget, "nucleicAcidExperimentTabs")
    rows.append(
        ContractRow(
            contract_id="LABTOOLS-NUCLEIC-QPCR-ADAPTER-PRESENT",
            module="LabTools",
            surface="Nucleic Acid",
            current_file="app/labtools/workspace.py",
            object_name=tabs.objectName(),
            label=" / ".join(tabs.tabText(index) for index in range(tabs.count())),
            enabled=True,
            button_behavior="hosts_qpcr_mix_adapter_and_disabled_remaining_gates",
            disabled_reason="",
            runtime_effect="QTabWidget exposes qPCR adapter plus remaining gates",
            artifact_evidence=f"tabs={tabs.count()}",
            live_click_test="inspected_runtime_tabs",
            status="connected" if tabs.count() == 4 else "broken",
            observed="verified" if tabs.count() == 4 else "unexpected_tab_count",
        )
    )
    _fill_qpcr_inputs(page)
    calculate = _find_button(page, "qpcrMixCalculateButton")
    calculate.click()
    result = _find_child(page, QTextEdit, "qpcrMixResultPanel").toPlainText()
    copy = _find_button(page, "qpcrMixCopyResultButton")
    ok = "qPCR 配液结果为实验辅助草稿" in result and copy.isEnabled()
    rows.append(_row("LABTOOLS-NUCLEIC-QPCR-CALCULATE", "Nucleic Acid qPCR", "app/labtools/ui/calculator_widgets.py", calculate, "calculates qPCR mix plan", result, ok))
    if not ok:
        failures.append("qPCR mix calculation did not produce expected result")
    copy.click()
    copied = QApplication.clipboard().text()
    rows.append(_row("LABTOOLS-NUCLEIC-QPCR-COPY", "Nucleic Acid qPCR", "app/labtools/ui/calculator_widgets.py", copy, "copies qPCR mix plan", copied, "qPCR 配液结果" in copied))
    for object_name, tab_index in (
        ("nucleicPrimerRegistryGateDisabledButton", 1),
        ("nucleicPcrProgramGateDisabledButton", 2),
        ("nucleicResultProcessingGateDisabledButton", 3),
    ):
        tabs.setCurrentIndex(tab_index)
        gate = _find_button(page, object_name)
        rows.append(_disabled_row(f"LABTOOLS-NUCLEIC-GATE-{object_name}", "Nucleic Acid", "app/labtools/workspace.py", gate))
    return rows


def _audit_disabled_secondary(widget: LabToolsWorkspaceWidget, page_key: str, surface: str, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget.show_experiment_modules()
    button = _secondary_button(widget, page_key)
    button.click()
    ok = widget.current_page_key() == page_key
    rows.append(_row(f"LABTOOLS-SECONDARY-{page_key.upper()}-NAV", surface, "app/labtools/workspace.py", button, f"navigates to {surface} placeholder page", f"current_page_key={widget.current_page_key()}", ok))
    if not ok:
        failures.append(f"{page_key}: secondary navigation failed")
    disabled = _find_button(widget.current_page_widget(), "labToolsC1DisabledActionButton")
    rows.append(_disabled_row(f"LABTOOLS-SECONDARY-{page_key.upper()}-DISABLED-GATE", surface, "app/labtools/workspace.py", disabled))
    return rows


def _capture_screenshots(app: QApplication, widget: LabToolsWorkspaceWidget, screenshot_dir: Path) -> list[dict[str, str]]:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    shots: list[dict[str, str]] = []
    for name, page_key in (
        ("01_nucleic_qpcr_adapter", "nucleic_acid_experiments"),
        ("02_immuno_absorbance_disabled", "immuno_absorbance"),
        ("03_ihc_disabled", "ihc"),
    ):
        widget.show_secondary(page_key)
        app.processEvents()
        if page_key == "nucleic_acid_experiments":
            tabs = widget.current_page_widget().findChild(QTabWidget, "nucleicAcidExperimentTabs")
            if tabs is not None:
                tabs.setCurrentIndex(0)
                app.processEvents()
        widget.resize(1500, 950)
        path = screenshot_dir / f"{name}.png"
        widget.grab().save(str(path))
        shots.append({"name": name, "page_key": page_key, "path": str(path)})
    return shots


def _fill_qpcr_inputs(page) -> None:
    _find_child(page, QLineEdit, "qpcrMixReactionsField").setText("10")
    _find_child(page, QLineEdit, "qpcrMixReactionVolumeField").setText("20")
    _find_child(page, QLineEdit, "qpcrMixMasterMixValueField").setText("10")
    _find_child(page, QComboBox, "qpcrMixMasterMixModeCombo").setCurrentText("体积（µL）")
    _find_child(page, QLineEdit, "qpcrMixForwardPrimerField").setText("0.4")
    _find_child(page, QLineEdit, "qpcrMixReversePrimerField").setText("0.4")
    _find_child(page, QLineEdit, "qpcrMixTemplateField").setText("2")
    _find_child(page, QLineEdit, "qpcrMixOveragePercentField").setText("10")


def _secondary_button(widget: LabToolsWorkspaceWidget, page_key: str) -> QPushButton:
    for button in widget.current_page_widget().findChildren(QPushButton, "labtoolsSecondaryEntryButton"):
        if button.property("pageKey") == page_key:
            return button
    raise AssertionError(f"Missing LabTools secondary button page_key={page_key}")


def _find_button(widget: object, object_name: str) -> QPushButton:
    button = widget.findChild(QPushButton, object_name)
    if button is None:
        raise AssertionError(f"Missing QPushButton objectName={object_name}")
    return button


def _find_child(widget: object, cls: type, object_name: str):
    child = widget.findChild(cls, object_name)
    if child is None:
        raise AssertionError(f"Missing {cls.__name__} objectName={object_name}")
    return child


def _row(contract_id: str, surface: str, current_file: str, button: QPushButton, runtime_effect: str, artifact_evidence: str, ok: bool) -> ContractRow:
    return ContractRow(
        contract_id=contract_id,
        module="LabTools",
        surface=surface,
        current_file=current_file,
        object_name=button.objectName(),
        label=button.text().replace("\n", " / "),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        disabled_reason=str(button.property("disabledReason") or ""),
        runtime_effect=runtime_effect,
        artifact_evidence=str(artifact_evidence).replace("\n", " / ")[:500],
        live_click_test="clicked_button_and_verified_runtime_state_or_artifact",
        status="connected" if ok else "broken",
        observed="verified" if ok else "missing_expected_effect",
    )


def _disabled_row(contract_id: str, surface: str, current_file: str, button: QPushButton) -> ContractRow:
    ok = (not button.isEnabled()) and bool(button.property("disabledReason"))
    return ContractRow(
        contract_id=contract_id,
        module="LabTools",
        surface=surface,
        current_file=current_file,
        object_name=button.objectName(),
        label=button.text().replace("\n", " / "),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        disabled_reason=str(button.property("disabledReason") or ""),
        runtime_effect="disabled gate classified by disabledReason",
        artifact_evidence=str(button.property("disabledReason") or ""),
        live_click_test="verified_disabled_reason",
        status="disabled" if ok else "broken",
        observed="disabled_with_reason" if ok else "missing_disabled_reason",
    )


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract LabTools Batch 5: Secondary Remainder",
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
        "## Screenshots",
        "",
    ]
    for shot in payload["screenshots"]:
        lines.append(f"- `{shot['name']}` / `{shot['page_key']}`: `{shot['path']}`")
    lines.extend(["", "## Rows", "", "| Contract | Surface | Object | Status | Behavior | Evidence |", "| --- | --- | --- | --- | --- | --- |"])
    for row in payload["rows"]:
        lines.append(f"| `{row['contract_id']}` | {row['surface']} | `{row['object_name']}` | {row['status']} | `{row['button_behavior']}` | {row['artifact_evidence']} |")
    failures = summary.get("failures") if isinstance(summary, dict) else []
    if failures:
        lines.extend(["", "## Failures", ""])
        for failure in failures:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def _git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=REPO_ROOT, text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
