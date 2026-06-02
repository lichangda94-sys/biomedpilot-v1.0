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

from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QPushButton, QScrollArea, QTabWidget

from app.labtools.cell_experiments import (
    CELL_EXPERIMENT_RECORD_TYPES,
    RECORD_TEMPLATE_FIELDS,
    CellExperimentRecordStore,
    CellProfileStore,
    FreezingInventoryStore,
)
import app.labtools.cell_experiments.records as cell_experiment_records_module
from app.labtools.image_analysis import ImageAnalysisTaskStore
from app.labtools.ui.cell_experiment_widgets import LabToolsCellExperimentPage
from app.labtools.ui.image_analysis_widgets import ImageAnalysisWorkbenchWidget
from app.labtools.workspace import LabToolsWorkspaceWidget
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_LABTOOLS_BATCH3_CELL_EXPERIMENTS.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_LABTOOLS_BATCH3_CELL_EXPERIMENTS.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_labtools_batch3_cell_experiments"


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
    batch: str = "Batch 3: LabTools Cell Experiments Deep Contract"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    screenshots: list[dict[str, str]] = []
    failures: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_labtools_batch3_") as temp_name:
            audit_root = Path(temp_name)
            original_cell_root = cell_experiment_records_module.default_cell_experiment_root
            cell_experiment_records_module.default_cell_experiment_root = lambda: audit_root / "cell_experiment_default_root"
            try:
                profile_store = CellProfileStore(audit_root / "cell_profiles.json")
                inventory_store = FreezingInventoryStore(audit_root / "cell_inventory.json")
                record_store = CellExperimentRecordStore(
                    audit_root / "cell_records.json",
                    profile_store=profile_store,
                    inventory_store=inventory_store,
                )
                page = LabToolsCellExperimentPage(
                    profile_store=profile_store,
                    inventory_store=inventory_store,
                    record_store=record_store,
                )
                rows.extend(_audit_workspace_visual_gates(app, failures))
                rows.extend(_audit_profile_and_inventory(page, profile_store, inventory_store, failures))
                rows.extend(_audit_record_templates(page, profile_store, inventory_store, record_store, failures))
                rows.extend(_audit_image_analysis_tabs(page, audit_root, failures))
                screenshots.extend(_capture_screenshots(app, page, args.screenshot_dir))
            finally:
                cell_experiment_records_module.default_cell_experiment_root = original_cell_root
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_labtools_batch3_cell_experiments.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "LabTools Cell Experiments deep live-click contract for profile, inventory, record templates, and cell image-analysis run-request gates.",
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
    parser = argparse.ArgumentParser(description="Run LabTools Cell Experiments deep route contract live-click audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _audit_workspace_visual_gates(app: QApplication, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    widget = LabToolsWorkspaceWidget()
    try:
        widget.show_cell_experiments()
        app.processEvents()
        page = widget.current_page_widget()
        for object_name, surface in (
            ("cellExperimentCreateFromLastDisabledButton", "Cell Experiments Visual Summary"),
            ("cellExperimentSettingsRouteDisabledButton", "Cell Image Analysis Visual Summary"),
            ("cellExperimentRunImageAnalysisDisabledButton", "Cell Image Analysis Visual Summary"),
        ):
            button = _find_button(page, object_name)
            rows.append(_disabled_gate_row(f"LABTOOLS-CELL-VISUAL-{object_name}", surface, button))
            if button.isEnabled() or not button.property("disabledReason"):
                failures.append(f"LABTOOLS-CELL-VISUAL-{object_name}: expected disabled reason")
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()
    return rows


def _audit_profile_and_inventory(
    page: LabToolsCellExperimentPage,
    profile_store: CellProfileStore,
    inventory_store: FreezingInventoryStore,
    failures: list[str],
) -> list[ContractRow]:
    rows: list[ContractRow] = []
    _set_text(page, "cellProfileField_cell_name", "A549")
    _set_text(page, "cellProfileField_current_passage", "P8")
    _set_text(page, "cellProfileField_basal_medium", "DMEM")
    _set_text(page, "cellProfileField_serum_type", "FBS")

    save_profile = _find_button(page, "cellProfileSaveButton")
    save_profile.click()
    profile_count = len(profile_store.load())
    rows.append(
        _row(
            contract_id="LABTOOLS-CELL-PROFILE-SAVE",
            surface="Cell Profile",
            current_file="app/labtools/ui/cell_experiment_widgets.py",
            button=save_profile,
            runtime_effect="upserts CellProfileStore JSON",
            artifact_evidence=f"{profile_store.resolved_path().name}; profile_count={profile_count}",
            observed="profile_saved" if profile_count == 1 else "profile_save_failed",
            status="connected" if profile_count == 1 else "broken",
        )
    )
    if profile_count != 1:
        failures.append("LABTOOLS-CELL-PROFILE-SAVE: profile_count is not 1")

    copy_profile = _find_button(page, "cellProfileCopyButton")
    copy_profile.click()
    copied_count = len(profile_store.load())
    rows.append(
        _row(
            contract_id="LABTOOLS-CELL-PROFILE-COPY",
            surface="Cell Profile",
            current_file="app/labtools/ui/cell_experiment_widgets.py",
            button=copy_profile,
            runtime_effect="copies selected cell profile into CellProfileStore",
            artifact_evidence=f"{profile_store.resolved_path().name}; profile_count={copied_count}",
            observed="profile_copied" if copied_count == 2 else "profile_copy_failed",
            status="connected" if copied_count == 2 else "broken",
        )
    )
    if copied_count != 2:
        failures.append("LABTOOLS-CELL-PROFILE-COPY: copied profile missing")

    export_profile = _find_button(page, "cellProfileExportButton")
    export_profile.click()
    status_text = _find_label(page, "cellProfileStatusLabel").text()
    export_ok = "已导出" in status_text
    rows.append(
        _row(
            contract_id="LABTOOLS-CELL-PROFILE-EXPORT",
            surface="Cell Profile",
            current_file="app/labtools/ui/cell_experiment_widgets.py",
            button=export_profile,
            runtime_effect="exports selected cell profile TXT",
            artifact_evidence=f"profile_export_status_present={export_ok}",
            observed="profile_exported" if export_ok else "profile_export_missing",
            status="connected" if export_ok else "broken",
        )
    )
    if not export_ok:
        failures.append("LABTOOLS-CELL-PROFILE-EXPORT: export status missing")

    new_profile = _find_button(page, "cellProfileNewButton")
    new_profile.click()
    cleared = _find_line_edit(page, "cellProfileField_cell_name").text() == ""
    rows.append(
        _row(
            contract_id="LABTOOLS-CELL-PROFILE-NEW",
            surface="Cell Profile",
            current_file="app/labtools/ui/cell_experiment_widgets.py",
            button=new_profile,
            runtime_effect="clears cell profile form without deleting store",
            artifact_evidence=f"cell_name_field_empty={cleared}; profile_count={len(profile_store.load())}",
            observed="profile_form_cleared" if cleared else "profile_form_not_cleared",
            status="connected" if cleared else "broken",
        )
    )
    if not cleared:
        failures.append("LABTOOLS-CELL-PROFILE-NEW: form was not cleared")

    _set_text(page, "cellProfileField_cell_name", "A549")
    _set_text(page, "cellProfileField_current_passage", "P8")
    save_profile.click()
    _set_text(page, "freezingBatchCodeInput", "A549-FZ")
    _set_text(page, "cryovialTankInput", "LN2-1")
    _set_text(page, "cryovialRackInput", "R1")
    _set_text(page, "cryovialBoxInput", "B1")
    create_batch = _find_button(page, "freezingBatchCreateButton")
    create_batch.click()
    _batches, cryovials = inventory_store.load()
    rows.append(
        _row(
            contract_id="LABTOOLS-CELL-FREEZING-BATCH-CREATE",
            surface="Cell Freezing Inventory",
            current_file="app/labtools/ui/cell_experiment_widgets.py",
            button=create_batch,
            runtime_effect="creates freezing batch and generated cryovials",
            artifact_evidence=f"{inventory_store.resolved_path().name}; cryovial_count={len(cryovials)}",
            observed="cryovials_created" if len(cryovials) >= 2 else "cryovials_missing",
            status="connected" if len(cryovials) >= 2 else "broken",
        )
    )
    if len(cryovials) < 2:
        failures.append("LABTOOLS-CELL-FREEZING-BATCH-CREATE: cryovials missing")

    first_vial_id = cryovials[0].cryovial_id
    _set_text(page, "cryovialEditIdInput", first_vial_id)
    _set_text(page, "cryovialPositionEditInput", "A2")
    status_combo = _find_child(page, QComboBox, "cryovialStatusEditInput")
    status_combo.setCurrentText("已转移")
    update_cryovial = _find_button(page, "cryovialUpdateButton")
    update_cryovial.click()
    updated = next(vial for vial in inventory_store.list_cryovials() if vial.cryovial_id == first_vial_id)
    update_ok = updated.status == "已转移" and updated.box_position == "A2"
    rows.append(
        _row(
            contract_id="LABTOOLS-CELL-CRYOVIAL-UPDATE",
            surface="Cell Freezing Inventory",
            current_file="app/labtools/ui/cell_experiment_widgets.py",
            button=update_cryovial,
            runtime_effect="updates cryovial location and status",
            artifact_evidence=f"status={updated.status}; box_position={updated.box_position}",
            observed="cryovial_updated" if update_ok else "cryovial_update_failed",
            status="connected" if update_ok else "broken",
        )
    )
    if not update_ok:
        failures.append("LABTOOLS-CELL-CRYOVIAL-UPDATE: cryovial not updated")
    return rows


def _audit_record_templates(
    page: LabToolsCellExperimentPage,
    profile_store: CellProfileStore,
    inventory_store: FreezingInventoryStore,
    record_store: CellExperimentRecordStore,
    failures: list[str],
) -> list[ContractRow]:
    rows: list[ContractRow] = []
    record_tabs = _find_child(page, QTabWidget, "cellExperimentRecordTabs")
    for tab_index, (record_type, label) in enumerate(CELL_EXPERIMENT_RECORD_TYPES[1:], start=1):
        record_tabs.setCurrentIndex(tab_index)
        current_tab = record_tabs.currentWidget()
        refresh_profiles = getattr(current_tab, "refresh_profiles", None)
        if callable(refresh_profiles):
            refresh_profiles()
        profile_combo = _find_child(current_tab, QComboBox, f"cellRecordProfileSelector_{record_type}")
        if profile_combo.count() > 0:
            profile_combo.setCurrentIndex(profile_combo.count() - 1)
        _fill_record_fields(page, record_type)
        save_button = _find_button(page, f"cellRecordSaveButton_{record_type}")
        before = len(record_store.load())
        save_button.click()
        after = len(record_store.load())
        latest = record_store.latest_for_type(record_type)
        save_ok = after == before + 1 and latest is not None
        if record_type == "passage":
            profile = profile_store.get(latest.cell_profile_id) if latest else None
            save_ok = save_ok and profile is not None and profile.current_passage == "P9"
        if record_type == "thaw" and latest is not None and latest.fields.get("cryovial_id"):
            vial = next(vial for vial in inventory_store.list_cryovials() if vial.cryovial_id == latest.fields["cryovial_id"])
            save_ok = save_ok and vial.status == "已复苏"
        rows.append(
            _row(
                contract_id=f"LABTOOLS-CELL-RECORD-{record_type.upper()}-SAVE",
                surface=f"Cell Record Template / {label}",
                current_file="app/labtools/ui/cell_experiment_widgets.py",
                button=save_button,
                runtime_effect="saves cell experiment record and applies record side effects",
                artifact_evidence=f"{record_store.resolved_path().name}; before={before}; after={after}",
                observed="record_saved" if save_ok else "record_save_failed",
                status="connected" if save_ok else "broken",
            )
        )
        if not save_ok:
            failures.append(f"LABTOOLS-CELL-RECORD-{record_type.upper()}-SAVE: record save failed")

        export_button = _find_button(page, f"cellRecordExportButton_{record_type}")
        export_button.click()
        export_text = _find_label(page, f"cellRecordStatus_{record_type}").text()
        export_ok = "已导出" in export_text
        rows.append(
            _row(
                contract_id=f"LABTOOLS-CELL-RECORD-{record_type.upper()}-EXPORT",
                surface=f"Cell Record Template / {label}",
                current_file="app/labtools/ui/cell_experiment_widgets.py",
                button=export_button,
                runtime_effect="exports saved cell experiment record TXT",
                artifact_evidence=f"record_export_status_present={export_ok}",
                observed="record_exported" if export_ok else "record_export_failed",
                status="connected" if export_ok else "broken",
            )
        )
        if not export_ok:
            failures.append(f"LABTOOLS-CELL-RECORD-{record_type.upper()}-EXPORT: export failed")

        copy_button = _find_button(page, f"cellRecordCopyButton_{record_type}")
        copy_button.click()
        copy_text = _find_label(page, f"cellRecordStatus_{record_type}").text()
        copy_ok = "已复制当前记录为草稿" in copy_text
        rows.append(
            _row(
                contract_id=f"LABTOOLS-CELL-RECORD-{record_type.upper()}-COPY",
                surface=f"Cell Record Template / {label}",
                current_file="app/labtools/ui/cell_experiment_widgets.py",
                button=copy_button,
                runtime_effect="copies current saved record into an unsaved draft",
                artifact_evidence=copy_text,
                observed="record_copied_to_draft" if copy_ok else "record_copy_failed",
                status="connected" if copy_ok else "broken",
            )
        )
        if not copy_ok:
            failures.append(f"LABTOOLS-CELL-RECORD-{record_type.upper()}-COPY: copy failed")

        from_last_button = _find_button(page, f"cellRecordFromLastButton_{record_type}")
        from_last_button.click()
        from_last_text = _find_label(page, f"cellRecordStatus_{record_type}").text()
        from_last_ok = "已从上次记录创建草稿" in from_last_text
        rows.append(
            _row(
                contract_id=f"LABTOOLS-CELL-RECORD-{record_type.upper()}-FROM-LAST",
                surface=f"Cell Record Template / {label}",
                current_file="app/labtools/ui/cell_experiment_widgets.py",
                button=from_last_button,
                runtime_effect="creates draft from latest saved record of the same type",
                artifact_evidence=from_last_text,
                observed="record_from_last_draft_created" if from_last_ok else "record_from_last_failed",
                status="connected" if from_last_ok else "broken",
            )
        )
        if not from_last_ok:
            failures.append(f"LABTOOLS-CELL-RECORD-{record_type.upper()}-FROM-LAST: from-last failed")

    calculate = _find_button(page, "seedingCalculationButton")
    calculate.click()
    result_text = _find_label(page, "seedingCalculationResult").text()
    calc_ok = "需要细胞悬液体积" in result_text and "需要培养基体积" in result_text
    rows.append(
        _row(
            contract_id="LABTOOLS-CELL-SEEDING-CALCULATE",
            surface="Cell Record Template / Seeding",
            current_file="app/labtools/ui/cell_experiment_widgets.py",
            button=calculate,
            runtime_effect="calculates cell seeding preparation preview",
            artifact_evidence=result_text,
            observed="seeding_preview_generated" if calc_ok else "seeding_preview_missing",
            status="connected" if calc_ok else "broken",
        )
    )
    if not calc_ok:
        failures.append("LABTOOLS-CELL-SEEDING-CALCULATE: calculation preview missing")
    return rows


def _audit_image_analysis_tabs(page: LabToolsCellExperimentPage, audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    top_tabs = _find_child(page, QTabWidget, "cellExperimentTopTabs")
    top_tabs.setCurrentIndex(1)
    image_tabs = _find_child(page, QTabWidget, "cellExperimentImageAnalysisTabs")
    image_path = audit_root / "cells.png"
    image_path.write_bytes(b"image")
    for index in range(image_tabs.count()):
        image_tabs.setCurrentIndex(index)
        widget = image_tabs.currentWidget()
        if not isinstance(widget, ImageAnalysisWorkbenchWidget):
            failures.append(f"LABTOOLS-CELL-IMAGE-TAB-{index}: current widget is not ImageAnalysisWorkbenchWidget")
            continue
        widget._task_store = ImageAnalysisTaskStore(audit_root / f"cell_image_tasks_{widget.property('analysisType')}")  # noqa: SLF001 - scoped audit store injection
        widget.set_image_paths_for_testing((str(image_path),))
        action = widget.findChildren(QPushButton, "imageWorkbenchPrimaryActionButton")[0]
        action.click()
        workspace = widget.latest_workspace()
        ok = bool(workspace and workspace.run_request_path.exists() and workspace.task.status == "run_request_created")
        rows.append(
            _row(
                contract_id=f"LABTOOLS-CELL-IMAGE-{widget.property('analysisType')}-RUN-REQUEST",
                surface=f"Cell Image Analysis / {image_tabs.tabText(index)}",
                current_file="app/labtools/ui/image_analysis_widgets.py",
                button=action,
                runtime_effect="creates image-analysis run request without executing ImageJ/Fiji",
                artifact_evidence="run_request.json exists; task.status=run_request_created" if workspace else "missing_workspace",
                observed="image_run_request_created" if ok else "image_run_request_missing",
                status="connected" if ok else "broken",
            )
        )
        if not ok:
            failures.append(f"LABTOOLS-CELL-IMAGE-{widget.property('analysisType')}: run request missing")
        export_button = widget.findChild(QPushButton, "imageWorkbenchExportPlaceholderButton")
        if export_button is not None:
            rows.append(
                _disabled_gate_row(
                    f"LABTOOLS-CELL-IMAGE-{widget.property('analysisType')}-EXPORT-GATE",
                    f"Cell Image Analysis / {image_tabs.tabText(index)}",
                    export_button,
                    current_file="app/labtools/ui/image_analysis_widgets.py",
                )
            )
    return rows


def _fill_record_fields(page: LabToolsCellExperimentPage, record_type: str) -> None:
    _set_text(page, f"cellRecordExperimentName_{record_type}", f"{record_type} audit")
    _set_text(page, f"cellRecordOperator_{record_type}", "codex")
    for field_name in RECORD_TEMPLATE_FIELDS[record_type]:
        value = "P9" if field_name == "passage_after" else f"{field_name}_value"
        _set_text(page, f"cellRecordField_{record_type}_{field_name}", value)


def _capture_screenshots(app: QApplication, page: LabToolsCellExperimentPage, screenshot_dir: Path) -> list[dict[str, str]]:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    page.resize(1600, 1000)
    page.show()
    app.processEvents()
    shots: list[dict[str, str]] = []
    captures = (
        ("01_cell_experiments_overview", lambda: _scroll_top(page)),
        ("02_cell_record_tabs", lambda: (_find_child(page, QTabWidget, "cellExperimentTopTabs").setCurrentIndex(0), _scroll_bottom(page))),
        ("03_cell_image_analysis_tabs", lambda: (_find_child(page, QTabWidget, "cellExperimentTopTabs").setCurrentIndex(1), _scroll_bottom(page))),
        ("04_cell_record_after_save", lambda: (_find_child(page, QTabWidget, "cellExperimentTopTabs").setCurrentIndex(0), _scroll_bottom(page))),
    )
    try:
        for name, prepare in captures:
            prepare()
            app.processEvents()
            path = screenshot_dir / f"{name}.png"
            page.grab().save(str(path))
            shots.append({"name": name, "path": str(path.relative_to(REPO_ROOT))})
    finally:
        page.close()
        page.deleteLater()
        app.processEvents()
    return shots


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
        live_click_test="scripts/ui_route_contract_labtools_batch3_cell_experiments.py",
        status=status,
        observed=observed,
    )


def _disabled_gate_row(
    contract_id: str,
    surface: str,
    button: QPushButton,
    *,
    current_file: str = "app/labtools/ui/cell_experiment_widgets.py",
) -> ContractRow:
    status = "disabled" if not button.isEnabled() and button.property("disabledReason") else "broken"
    observed = "disabled_with_reason" if status == "disabled" else "disabled_gate_missing_reason"
    return _row(
        contract_id=contract_id,
        surface=surface,
        current_file=current_file,
        button=button,
        runtime_effect="disabled gate classified by disabledReason",
        artifact_evidence=str(button.property("disabledReason") or ""),
        observed=observed,
        status=status,
    )


def _find_button(widget: object, object_name: str) -> QPushButton:
    button = widget.findChild(QPushButton, object_name)
    if button is None:
        raise AssertionError(f"Missing QPushButton objectName={object_name}")
    return button


def _find_label(widget: object, object_name: str) -> QLabel:
    label = widget.findChild(QLabel, object_name)
    if label is None:
        raise AssertionError(f"Missing QLabel objectName={object_name}")
    return label


def _find_line_edit(widget: object, object_name: str) -> QLineEdit:
    line_edit = widget.findChild(QLineEdit, object_name)
    if line_edit is None:
        raise AssertionError(f"Missing QLineEdit objectName={object_name}")
    return line_edit


def _find_child(widget: object, cls: type, object_name: str):
    item = widget.findChild(cls, object_name)
    if item is None:
        raise AssertionError(f"Missing {cls.__name__} objectName={object_name}")
    return item


def _set_text(widget: object, object_name: str, value: str) -> None:
    _find_line_edit(widget, object_name).setText(value)


def _scroll_top(page: LabToolsCellExperimentPage) -> None:
    scroll = _find_child(page, QScrollArea, "cellExperimentWorkspaceScroll")
    scroll.verticalScrollBar().setValue(0)


def _scroll_bottom(page: LabToolsCellExperimentPage) -> None:
    scroll = _find_child(page, QScrollArea, "cellExperimentWorkspaceScroll")
    scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract LabTools Batch 3: Cell Experiments",
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
        lines.append(f"- `{shot['name']}`: `{shot['path']}`")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| Contract | Surface | Object | Status | Behavior | Evidence |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            "| `{}` | {} | `{}` | {} | `{}` | {} |".format(
                row["contract_id"],
                row["surface"],
                row["object_name"],
                row["status"],
                row["button_behavior"],
                str(row["artifact_evidence"]).replace("\n", " / "),
            )
        )
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
