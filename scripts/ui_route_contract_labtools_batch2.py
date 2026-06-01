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

from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit

from app.labtools.cell_experiments import CellExperimentRecordStore, CellProfileStore, FreezingInventoryStore
from app.labtools.image_analysis import ImageAnalysisTaskStore
from app.labtools.labtools_tool_registry import labtools_primary_entries, labtools_secondary_entries
from app.labtools.reagent_templates import ReagentTemplateStore
from app.labtools.ui.calculator_widgets import ReagentPreparationWorkflowWidget
from app.labtools.ui.cell_experiment_widgets import LabToolsCellExperimentPage
from app.labtools.ui.image_analysis_widgets import ImageAnalysisWorkbenchWidget
from app.labtools.ui.western_blot_roi_widgets import WesternBlotROIAnalysisWidget
from app.labtools.ui.western_blot_widgets import LabToolsWesternBlotWidget
from app.labtools.western_blot import WBRectangleROI
from app.labtools.workspace import LabToolsWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_LABTOOLS_BATCH2.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_LABTOOLS_BATCH2.md"


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
    batch: str = "Batch 2: LabTools Adapter Contract"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    failures: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_labtools_batch2_") as temp_name:
            audit_root = Path(temp_name)
            rows.extend(_audit_workspace_routes(app, failures))
            rows.extend(_audit_calculator_runtime(failures))
            rows.extend(_audit_reagent_runtime(audit_root, failures))
            rows.extend(_audit_cell_runtime(audit_root, failures))
            rows.extend(_audit_western_blot_runtime(audit_root, failures))
            rows.extend(_audit_image_analysis_runtime(audit_root, failures))
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_labtools_batch2.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "LabTools approved home, second-level module list, connected calculators/reagent/cell/WB/image run-request gates.",
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
    parser = argparse.ArgumentParser(description="Run Phase 1 Batch 2 LabTools route contract live-click audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    return parser.parse_args(argv)


def _audit_workspace_routes(app: QApplication, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget = LabToolsWorkspaceWidget()
    try:
        expected_pages = (
            "home",
            "general_calculators",
            "reagent_preparation",
            "experiment_modules",
            "cell_experiments",
            "protein_experiments",
            "nucleic_acid_experiments",
            "immuno_absorbance",
            "ihc",
        )
        if widget.page_keys() != expected_pages:
            failures.append(f"LABTOOLS-PAGE-KEYS: expected {expected_pages}, observed {widget.page_keys()}")
        primary_titles = [entry.title for entry in labtools_primary_entries()]
        if primary_titles != ["通用计算器", "试剂制备", "实验模块"]:
            failures.append(f"LABTOOLS-HOME-STRUCTURE: unexpected primary titles {primary_titles}")
        secondary_titles = [entry.title for entry in labtools_secondary_entries()]
        if secondary_titles != ["细胞实验", "蛋白实验", "核酸实验", "免疫与吸光度实验", "免疫组化"]:
            failures.append(f"LABTOOLS-SECONDARY-STRUCTURE: unexpected secondary titles {secondary_titles}")

        for entry in labtools_primary_entries():
            widget.show_home()
            button = _primary_button(widget, entry.page_key)
            button.click()
            app.processEvents()
            ok = widget.current_page_key() == entry.page_key
            contract_id = f"LABTOOLS-HOME-{entry.page_key.upper()}"
            rows.append(
                _row(
                    contract_id=contract_id,
                    surface="LabTools Home",
                    current_file="app/labtools/labtools_home.py",
                    button=button,
                    runtime_effect=f"navigates to primary page {entry.page_key}",
                    artifact_evidence=f"current_page_key={widget.current_page_key()}",
                    observed=f"expected={entry.page_key}; observed={widget.current_page_key()}",
                    status="connected" if ok else "broken",
                )
            )
            if not ok:
                failures.append(f"{contract_id}: route did not reach {entry.page_key}")

        widget.show_experiment_modules()
        for entry in labtools_secondary_entries():
            button = _secondary_button(widget, entry.page_key)
            button.click()
            app.processEvents()
            ok = widget.current_page_key() == entry.page_key
            contract_id = f"LABTOOLS-SECONDARY-{entry.page_key.upper()}"
            rows.append(
                _row(
                    contract_id=contract_id,
                    surface="LabTools Experiment Modules",
                    current_file="app/labtools/workspace.py",
                    button=button,
                    runtime_effect=f"navigates to secondary page {entry.page_key}",
                    artifact_evidence=f"current_page_key={widget.current_page_key()}",
                    observed=f"expected={entry.page_key}; observed={widget.current_page_key()}",
                    status="connected" if ok else "broken",
                )
            )
            if not ok:
                failures.append(f"{contract_id}: route did not reach {entry.page_key}")
            if entry.page_key in {"nucleic_acid_experiments", "immuno_absorbance", "ihc"}:
                disabled = _find_button(widget.current_page_widget(), "labToolsC1DisabledActionButton")
                rows.append(_classify_gate_row(f"{contract_id}-DISABLED-GATE", entry.title, disabled))
            widget.show_experiment_modules()

        widget.show_cell_experiments()
        home = _find_button(widget, "labToolsHomeButton")
        home.click()
        ok = widget.current_page_key() == "home"
        rows.append(
            _row(
                contract_id="LABTOOLS-HEADER-HOME",
                surface="LabTools Header",
                current_file="app/labtools/workspace.py",
                button=home,
                runtime_effect="navigates back to LabTools home",
                artifact_evidence=f"current_page_key={widget.current_page_key()}",
                observed=f"expected=home; observed={widget.current_page_key()}",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("LABTOOLS-HEADER-HOME: route did not return home")
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()
    return rows


def _audit_calculator_runtime(failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget = LabToolsWorkspaceWidget()
    try:
        widget.show_general_calculators()
        tabs = _find_child(widget, QTabWidget, "labToolsQuickCalculatorTabs")
        dilution_index = next(index for index in range(tabs.count()) if tabs.tabText(index) == "稀释计算")
        tabs.setCurrentIndex(dilution_index)
        tab = tabs.currentWidget()
        fields = tab.findChildren(QLineEdit)
        fields[0].setText("10")
        fields[1].setText("100")
        fields[2].setText("1")
        button = _find_button(tab, "primaryButton")
        button.click()
        result = _find_child(tab, QTextEdit, "labToolsResultPanel").toPlainText()
        copy_button = next(item for item in tab.findChildren(QPushButton) if item.text() == "复制结果")
        ok = "所需 stock 体积" in result and copy_button.isEnabled()
        rows.append(
            _row(
                contract_id="LABTOOLS-CALCULATOR-DILUTION-RUN",
                surface="General Calculators",
                current_file="app/labtools/ui/calculator_widgets.py",
                button=button,
                runtime_effect="calculates dilution preview state and enables copy",
                artifact_evidence="result_panel_contains_stock_volume; copy_button_enabled=" + str(copy_button.isEnabled()),
                observed="calculator_result_verified" if ok else "missing_calculator_result",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("LABTOOLS-CALCULATOR-DILUTION-RUN: expected result state missing")
    finally:
        widget.close()
        widget.deleteLater()
    return rows


def _audit_reagent_runtime(audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    store = ReagentTemplateStore(audit_root / "reagent_templates.json")
    widget = ReagentPreparationWorkflowWidget(store)
    try:
        _save_reagent_template(widget)
        save_button = _find_button(widget, "reagentTemplateSaveButton")
        ok = store.resolved_path().exists() and len(store.load()) == 1
        rows.append(
            _row(
                contract_id="LABTOOLS-REAGENT-TEMPLATE-SAVE",
                surface="Reagent Preparation",
                current_file="app/labtools/ui/calculator_widgets.py",
                button=save_button,
                runtime_effect="upserts reagent template local JSON",
                artifact_evidence=str(store.resolved_path()),
                observed="template_json_verified" if ok else "missing_template_json",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("LABTOOLS-REAGENT-TEMPLATE-SAVE: template JSON missing")

        _find_button(widget, "preparationReloadTemplatesButton").click()
        _find_child(widget, QLineEdit, "preparationTargetVolumeField").setText("500")
        _find_child(widget, QLineEdit, "preparationOverageField").setText("10")
        calculate = _find_button(widget, "preparationCalculateButton")
        calculate.click()
        result = _find_child(widget, QTextEdit, "preparationResultPanel").toPlainText()
        ok = "PBS 1x" in result and "NaCl" in result and not (store.resolved_path().parent / "preparation_records.json").exists()
        rows.append(
            _row(
                contract_id="LABTOOLS-REAGENT-PREPARATION-CALCULATE",
                surface="Reagent Preparation",
                current_file="app/labtools/ui/calculator_widgets.py",
                button=calculate,
                runtime_effect="generates reagent preparation preview without record write",
                artifact_evidence="preview_contains_template_and_component; no preparation_records.json",
                observed="preparation_preview_verified" if ok else "missing_preparation_preview",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("LABTOOLS-REAGENT-PREPARATION-CALCULATE: expected preview state missing")
    finally:
        widget.close()
        widget.deleteLater()
    return rows


def _audit_cell_runtime(audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    profile_store = CellProfileStore(audit_root / "cell_profiles.json")
    inventory_store = FreezingInventoryStore(audit_root / "cell_inventory.json")
    record_store = CellExperimentRecordStore(audit_root / "cell_records.json", profile_store=profile_store, inventory_store=inventory_store)
    page = LabToolsCellExperimentPage(profile_store=profile_store, inventory_store=inventory_store, record_store=record_store)
    try:
        _find_child(page, QLineEdit, "cellProfileField_cell_name").setText("A549")
        _find_child(page, QLineEdit, "cellProfileField_current_passage").setText("P8")
        save_profile = _find_button(page, "cellProfileSaveButton")
        save_profile.click()
        ok = profile_store.resolved_path().exists() and len(profile_store.load()) == 1
        rows.append(
            _row(
                contract_id="LABTOOLS-CELL-PROFILE-SAVE",
                surface="Cell Experiments",
                current_file="app/labtools/ui/cell_experiment_widgets.py",
                button=save_profile,
                runtime_effect="upserts cell profile store",
                artifact_evidence=str(profile_store.resolved_path()),
                observed="cell_profile_store_verified" if ok else "missing_cell_profile_store",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("LABTOOLS-CELL-PROFILE-SAVE: profile store missing")

        _find_child(page, QLineEdit, "freezingBatchCodeInput").setText("A549-FZ")
        _find_child(page, QLineEdit, "cryovialTankInput").setText("LN2-1")
        create_batch = _find_button(page, "freezingBatchCreateButton")
        create_batch.click()
        _batches, cryovials = inventory_store.load()
        ok = inventory_store.resolved_path().exists() and len(cryovials) >= 1
        rows.append(
            _row(
                contract_id="LABTOOLS-CELL-FREEZING-BATCH-CREATE",
                surface="Cell Experiments",
                current_file="app/labtools/ui/cell_experiment_widgets.py",
                button=create_batch,
                runtime_effect="creates freezing batch and cryovial inventory",
                artifact_evidence=str(inventory_store.resolved_path()),
                observed="cryovial_inventory_verified" if ok else "missing_cryovial_inventory",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("LABTOOLS-CELL-FREEZING-BATCH-CREATE: inventory store missing")

        calculate = _find_button(page, "seedingCalculationButton")
        calculate.click()
        seeding_label = _find_child(page, QLabel, "seedingCalculationResult")
        seeding_text = seeding_label.text()
        ok = "需要细胞悬液体积" in seeding_text and "需要培养基体积" in seeding_text
        rows.append(
            _row(
                contract_id="LABTOOLS-CELL-SEEDING-CALCULATE",
                surface="Cell Experiments",
                current_file="app/labtools/ui/cell_experiment_widgets.py",
                button=calculate,
                runtime_effect="calculates cell seeding preparation preview",
                artifact_evidence="seedingCalculationResult QLabel",
                observed="cell_seeding_preview_verified" if ok else "missing_cell_seeding_preview",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("LABTOOLS-CELL-SEEDING-CALCULATE: seeding preview missing")
    finally:
        page.close()
        page.deleteLater()
    return rows


def _audit_western_blot_runtime(audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    page = LabToolsWesternBlotWidget()
    try:
        table = _find_child(page, QTableWidget, "proteinLoadingSampleTable")
        table.setItem(0, 0, QTableWidgetItem("S1"))
        table.setItem(0, 1, QTableWidgetItem("2"))
        calculate = _find_button(page, "proteinLoadingCalculateButton")
        calculate.click()
        result = _find_child(page, QTextEdit, "proteinLoadingResultPanel").toPlainText()
        copy_button = _find_button(page, "proteinLoadingCopyResultButton")
        ok = "总 loading buffer 体积" in result and copy_button.isEnabled()
        rows.append(
            _row(
                contract_id="LABTOOLS-WB-PROTEIN-LOADING-CALCULATE",
                surface="Protein / Western Blot",
                current_file="app/labtools/ui/western_blot_widgets.py",
                button=calculate,
                runtime_effect="calculates protein loading plan and enables copy",
                artifact_evidence="proteinLoadingResultPanel; copy_button_enabled=" + str(copy_button.isEnabled()),
                observed="protein_loading_result_verified" if ok else "missing_protein_loading_result",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("LABTOOLS-WB-PROTEIN-LOADING-CALCULATE: expected result state missing")
    finally:
        page.close()
        page.deleteLater()

    image_path = audit_root / "wb.png"
    image_path.write_bytes(b"image")
    roi_widget = WesternBlotROIAnalysisWidget(task_store=ImageAnalysisTaskStore(audit_root / "wb_roi_tasks"))
    try:
        roi_widget.set_image_path_for_testing(str(image_path))
        roi_widget.add_roi_for_testing(WBRectangleROI("img", str(image_path), "target_band", 10, 20, 30, 12, label="Target Lane 1"))
        measure = _find_button(roi_widget, "wbMeasureRoiButton")
        measure.click()
        workspace = roi_widget.latest_workspace()
        ok = bool(workspace and workspace.run_request_path.exists() and (workspace.task_dir / "rois" / "wb_rois.csv").exists())
        rows.append(
            _row(
                contract_id="LABTOOLS-WB-ROI-RUN-REQUEST",
                surface="Protein / Western Blot",
                current_file="app/labtools/ui/western_blot_roi_widgets.py",
                button=measure,
                runtime_effect="creates WB ROI run request without running external engine",
                artifact_evidence=str(workspace.run_request_path) if workspace else "missing_wb_roi_workspace",
                observed="wb_roi_run_request_verified" if ok else "missing_wb_roi_run_request",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("LABTOOLS-WB-ROI-RUN-REQUEST: expected run request missing")
        preprocess = _find_button(roi_widget, "wbPreprocessButton")
        rows.append(_classify_gate_row("LABTOOLS-WB-ROI-PREPROCESS-GATE", "Protein / Western Blot", preprocess))
    finally:
        roi_widget.close()
        roi_widget.deleteLater()
    return rows


def _audit_image_analysis_runtime(audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    image_path = audit_root / "cells.png"
    image_path.write_bytes(b"image")
    widget = ImageAnalysisWorkbenchWidget(
        experiment_module="cell_experiment",
        analysis_type="transwell_count",
        title="Transwell 图像分析",
        primary_actions=("识别细胞区域", "统计细胞数", "生成分析任务"),
        parameter_defaults={"分组": "A", "输出格式": "CSV"},
        task_store=ImageAnalysisTaskStore(audit_root / "cell_image_tasks"),
    )
    try:
        widget.set_image_paths_for_testing((str(image_path),))
        action = widget.findChildren(QPushButton, "imageWorkbenchPrimaryActionButton")[0]
        action.click()
        workspace = widget.latest_workspace()
        ok = bool(workspace and workspace.run_request_path.exists() and workspace.task.status == "run_request_created")
        rows.append(
            _row(
                contract_id="LABTOOLS-CELL-IMAGE-RUN-REQUEST",
                surface="Cell Image Analysis",
                current_file="app/labtools/ui/image_analysis_widgets.py",
                button=action,
                runtime_effect="creates image analysis run request without running ImageJ/Fiji",
                artifact_evidence=str(workspace.run_request_path) if workspace else "missing_image_analysis_workspace",
                observed="image_run_request_verified" if ok else "missing_image_run_request",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append("LABTOOLS-CELL-IMAGE-RUN-REQUEST: expected run request missing")
    finally:
        widget.close()
        widget.deleteLater()
    return rows


def _save_reagent_template(widget: ReagentPreparationWorkflowWidget) -> None:
    _find_child(widget, QLineEdit, "reagentTemplateNameField").setText("PBS 1x")
    _find_child(widget, QLineEdit, "reagentTemplateDefaultVolumeField").setText("100")
    _find_child(widget, QLineEdit, "reagentTemplateDefaultStrengthField").setText("1X")
    _find_child(widget, QLineEdit, "reagentComponentNameField").setText("NaCl")
    _find_child(widget, QLineEdit, "reagentComponentAmountField").setText("0.8")
    _find_child(widget, QCheckBox, "reagentComponentScaleVolumeCheck").setChecked(True)
    _find_child(widget, QCheckBox, "reagentComponentContributesVolumeCheck").setChecked(False)
    _find_button(widget, "reagentTemplateAddComponentButton").click()
    _find_button(widget, "reagentTemplateSaveButton").click()


def _primary_button(widget: LabToolsWorkspaceWidget, page_key: str) -> QPushButton:
    for button in widget.findChildren(QPushButton, "labtoolsEntryButton"):
        if button.property("pageKey") == page_key:
            return button
    raise AssertionError(f"Missing LabTools primary button for page_key={page_key}")


def _secondary_button(widget: LabToolsWorkspaceWidget, page_key: str) -> QPushButton:
    for button in widget.current_page_widget().findChildren(QPushButton, "labtoolsSecondaryEntryButton"):
        if button.property("pageKey") == page_key:
            return button
    raise AssertionError(f"Missing LabTools secondary button for page_key={page_key}")


def _find_button(widget: object, object_name: str) -> QPushButton:
    button = widget.findChild(QPushButton, object_name)
    if button is None:
        raise AssertionError(f"Missing QPushButton objectName={object_name}")
    return button


def _find_child(widget: object, cls: type, object_name: str):
    item = widget.findChild(cls, object_name)
    if item is None:
        raise AssertionError(f"Missing {cls.__name__} objectName={object_name}")
    return item


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
        current_file="app/labtools/workspace.py",
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
        module="LabTools",
        surface=surface,
        current_file=current_file,
        object_name=button.objectName(),
        label=" ".join(button.text().split()),
        enabled=button.isEnabled(),
        button_behavior=str(button.property("buttonBehavior") or ""),
        disabled_reason=str(button.property("disabledReason") or ""),
        runtime_effect=runtime_effect,
        artifact_evidence=artifact_evidence,
        live_click_test="scripts/ui_route_contract_labtools_batch2.py",
        status=status,
        observed=observed,
    )


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract LabTools Batch 2",
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
        "- Home primary entries: General Calculators, Reagent Preparation, Experiment Modules.",
        "- Experiment Modules second-level entries: Cell Experiments, Protein Experiments, Nucleic Acid Experiments, Immunoassay & Absorbance, Immunohistochemistry.",
        "- Image analysis is not a primary or second-level module entry; it is a gated workbench inside Cell Experiments and Protein / Western Blot.",
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
