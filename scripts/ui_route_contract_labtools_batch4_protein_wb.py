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

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QPushButton, QScrollArea, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit

import app.labtools.ui.western_blot_widgets as wb_page_module
import app.labtools.western_blot.widgets as wb_loading_module
from app.labtools.image_analysis import ImageAnalysisTaskStore
from app.labtools.ui.western_blot_widgets import LabToolsWesternBlotWidget
from app.labtools.western_blot import WBWorkflowRecordStore
from app.labtools.western_blot.store import WBLoadingRecordStore
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets


DEFAULT_JSON = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_LABTOOLS_BATCH4_PROTEIN_WB.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "project-control" / "UI_ROUTE_CONTRACT_LABTOOLS_BATCH4_PROTEIN_WB.md"
DEFAULT_SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260602_labtools_batch4_protein_wb"


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
    batch: str = "Batch 4: LabTools Protein / Western Blot Deep Contract"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication.instance() or QApplication([])
    rows: list[ContractRow] = []
    screenshots: list[dict[str, str]] = []
    failures: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="biomedpilot_labtools_batch4_wb_") as temp_name:
            audit_root = Path(temp_name)
            page = LabToolsWesternBlotWidget()
            _redirect_stores(page, audit_root)
            with _patched_dialogs(audit_root):
                rows.extend(_audit_tab_entry_buttons(page, failures))
                rows.extend(_audit_protein_loading(page, audit_root, failures))
                rows.extend(_audit_bca(page, failures))
                rows.extend(_audit_sds_page(page, audit_root, failures))
                rows.extend(_audit_workflow_records(page, failures))
                rows.extend(_audit_wb_roi(page, audit_root, failures))
                _sanitize_audit_root(rows, audit_root)
                screenshots.extend(_capture_screenshots(app, page, args.screenshot_dir))
            page.close()
            page.deleteLater()
    finally:
        cleanup_qt_top_level_widgets(app)

    payload = {
        "schema_version": "ui_route_contract_labtools_batch4_protein_wb.v1",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": "LabTools Protein / Western Blot deep live-click contract for BCA, protein loading, SDS-PAGE, workflow records, and WB ROI/result gates.",
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
    broken_contracts = [row.contract_id for row in rows if row.status == "broken"]
    if broken_contracts:
        failures.extend(f"{contract_id}: broken route contract row" for contract_id in broken_contracts)
        payload["summary"]["failures"] = failures
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
    parser = argparse.ArgumentParser(description="Run LabTools Protein / Western Blot deep route contract live-click audit.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR)
    return parser.parse_args(argv)


def _redirect_stores(page: LabToolsWesternBlotWidget, audit_root: Path) -> None:
    page._workflow_record_store = WBWorkflowRecordStore(audit_root / "wb_workflow_records.json")
    page._loading_widget._record_store = WBLoadingRecordStore(audit_root / "wb_loading_records.json")
    roi_page = _roi_page(page)
    roi_page._task_store = ImageAnalysisTaskStore(audit_root / "wb_roi_tasks")


class _patched_dialogs:
    def __init__(self, audit_root: Path) -> None:
        self.audit_root = audit_root
        self._originals: list[tuple[object, str, object]] = []

    def __enter__(self) -> "_patched_dialogs":
        self._patch(wb_page_module.QFileDialog, "getSaveFileName", self._save_file_name)
        self._patch(wb_page_module.QFileDialog, "getOpenFileName", self._open_file_name)
        self._patch(wb_loading_module.QFileDialog, "getSaveFileName", self._save_file_name)
        self._patch(wb_loading_module.QMessageBox, "question", self._confirm_yes)
        return self

    def __exit__(self, *_exc: object) -> None:
        for owner, name, original in reversed(self._originals):
            setattr(owner, name, original)

    def _patch(self, owner: object, name: str, replacement: object) -> None:
        self._originals.append((owner, name, getattr(owner, name)))
        setattr(owner, name, replacement)

    def _save_file_name(self, _parent=None, title: str = "", *_args, **_kwargs):
        lower = title.lower()
        if "markdown" in lower:
            path = self.audit_root / "exports" / "wb_loading_record.md"
        elif "csv" in lower:
            path = self.audit_root / "exports" / "wb_loading_record.csv"
        elif "xlsx" in lower:
            path = self.audit_root / "exports" / "sds_page_calculation.xlsx"
        else:
            path = self.audit_root / "exports" / "sds_page_template.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return (str(path), "")

    def _open_file_name(self, *_args, **_kwargs):
        return (str(self.audit_root / "exports" / "sds_page_template.json"), "")

    def _confirm_yes(self, *_args, **_kwargs):
        return wb_loading_module.QMessageBox.Yes


def _audit_tab_entry_buttons(page: LabToolsWesternBlotWidget, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    for object_name, expected_tab in (
        ("openBcaAssayToolButton", "BCA 蛋白浓度测定"),
        ("openProteinLoadingToolButton", "蛋白上样计算"),
        ("openSdsPageGelToolButton", "配胶与 Lane 布局"),
    ):
        button = _find_button(page, object_name)
        button.click()
        tabs = _tabs(page)
        ok = tabs.tabText(tabs.currentIndex()) == expected_tab
        rows.append(_row(f"LABTOOLS-WB-TAB-{object_name}", "Protein / Western Blot", "app/labtools/ui/western_blot_widgets.py", button, "opens expected Western Blot tab", f"current_tab={tabs.tabText(tabs.currentIndex())}", ok))
        if not ok:
            failures.append(f"{object_name}: did not open {expected_tab}")
    return rows


def _audit_protein_loading(page: LabToolsWesternBlotWidget, audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    _select_tab(page, "蛋白上样计算")
    table = _find_child(page, QTableWidget, "proteinLoadingSampleTable")
    before_rows = table.rowCount()
    add_button = _find_button(page, "proteinLoadingAddSampleRowButton")
    add_button.click()
    rows.append(_row("LABTOOLS-WB-LOADING-ADD-SAMPLE", "Protein Loading", "app/labtools/western_blot/widgets.py", add_button, "adds sample row", f"row_count={table.rowCount()}", table.rowCount() == before_rows + 1))
    table.setItem(0, 0, QTableWidgetItem("S1"))
    table.setItem(0, 1, QTableWidgetItem("2"))
    table.setItem(1, 0, QTableWidgetItem("S2"))
    table.setItem(1, 1, QTableWidgetItem("4"))
    calculate = _find_button(page, "proteinLoadingCalculateButton")
    calculate.click()
    result_text = _find_child(page, QTextEdit, "proteinLoadingResultPanel").toPlainText()
    copy_result = _find_button(page, "proteinLoadingCopyResultButton")
    ok = "总 loading buffer 体积" in result_text and copy_result.isEnabled()
    rows.append(_row("LABTOOLS-WB-LOADING-CALCULATE", "Protein Loading", "app/labtools/western_blot/widgets.py", calculate, "calculates protein loading plan", "proteinLoadingResultPanel; copy_enabled=" + str(copy_result.isEnabled()), ok))
    if not ok:
        failures.append("protein loading calculation did not produce expected output")
    for object_name, evidence_check in (
        ("proteinLoadingCopyResultButton", lambda: QApplication.clipboard().text()),
        ("wbLoadingSaveRecordButton", lambda: _find_child(page, QTableWidget, "wbLoadingRecordHistoryTable").rowCount()),
        ("wbLoadingCopyMarkdownButton", lambda: QApplication.clipboard().text()),
        ("wbLoadingExportMarkdownButton", lambda: (audit_root / "exports" / "wb_loading_record.md").exists()),
        ("wbLoadingExportCsvButton", lambda: (audit_root / "exports" / "wb_loading_record.csv").exists()),
        ("wbLoadingRefreshRecordHistoryButton", lambda: _find_child(page, QTableWidget, "wbLoadingRecordHistoryTable").rowCount()),
    ):
        button = _find_button(page, object_name)
        button.click()
        evidence = evidence_check()
        ok = bool(evidence)
        rows.append(_row(f"LABTOOLS-WB-LOADING-{object_name}", "Protein Loading", "app/labtools/western_blot/widgets.py", button, "click produces record/export/clipboard/history effect", str(evidence), ok))
        if not ok:
            failures.append(f"{object_name}: missing expected protein loading effect")
    history = _find_child(page, QTableWidget, "wbLoadingRecordHistoryTable")
    history.selectRow(0)
    for object_name, expected_text in (
        ("wbLoadingViewRecordButton", "已载入记录"),
        ("wbLoadingDeleteRecordButton", "记录已删除"),
    ):
        button = _find_button(page, object_name)
        button.click()
        status = _find_child(page, QLabel, "wbLoadingRecordStatusLabel").text()
        ok = expected_text in status
        rows.append(_row(f"LABTOOLS-WB-LOADING-{object_name}", "Protein Loading", "app/labtools/western_blot/widgets.py", button, "history action updates selected record state", status, ok))
        if not ok:
            failures.append(f"{object_name}: expected status {expected_text}")
    return rows


def _audit_bca(page: LabToolsWesternBlotWidget, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    _select_tab(page, "BCA 蛋白浓度测定")
    _find_child(page, QTextEdit, "bcaOdMatrixPasteArea").setText(_bca_matrix_text())
    parse = _find_button(page, "bcaParseOdMatrixButton")
    parse.click()
    raw = _find_child(page, QTextEdit, "bcaRawDataPanel").toPlainText()
    rows.append(_row("LABTOOLS-WB-BCA-PARSE-MATRIX", "BCA", "app/labtools/ui/western_blot_widgets.py", parse, "parses OD matrix", raw, "OD 矩阵已解析" in raw))
    type_combo = _find_child(page, QComboBox, "bcaWellTypeCombo")
    start = _find_child(page, QLineEdit, "bcaBatchStartWellField")
    end = _find_child(page, QLineEdit, "bcaBatchEndWellField")
    name = _find_child(page, QLineEdit, "bcaAnnotationNameField")
    concentration = _find_child(page, QLineEdit, "bcaStandardConcentrationField")
    dilution = _find_child(page, QLineEdit, "bcaDilutionFactorField")
    apply = _find_button(page, "bcaApplyBatchAnnotationButton")
    for range_index, (start_well, end_well, conc, well_type) in enumerate((("A1", "A2", "0", "Standard"), ("A3", "A4", "100", "Standard"), ("A5", "A6", "200", "Standard"), ("A7", "A8", "", "Sample"))):
        type_combo.setCurrentText(well_type)
        start.setText(start_well)
        end.setText(end_well)
        name.setText("Sample 1" if well_type == "Sample" else "BSA")
        concentration.setText(conc)
        dilution.setText("2" if well_type == "Sample" else "1")
        apply.click()
        raw = _find_child(page, QTextEdit, "bcaRawDataPanel").toPlainText()
        ok = "已批量标注选区" in raw
        rows.append(_row(f"LABTOOLS-WB-BCA-APPLY-RANGE-{range_index}", "BCA", "app/labtools/ui/western_blot_widgets.py", apply, "applies BCA range annotation", raw, ok))
    plate = _find_child(page, QTableWidget, "bcaPlateTable")
    plate.setCurrentCell(0, 0)
    for object_name, expected in (("bcaSetBlankButton", "Blank"), ("bcaSetStandardButton", "Standard"), ("bcaSetSampleButton", "Sample"), ("bcaSetUnusedButton", "Unused"), ("bcaApplySelectedAnnotationButton", "Unused")):
        button = _find_button(page, object_name)
        button.click()
        raw = _find_child(page, QTextEdit, "bcaRawDataPanel").toPlainText()
        ok = "已标注孔位" in raw
        rows.append(_row(f"LABTOOLS-WB-BCA-{object_name}", "BCA", "app/labtools/ui/western_blot_widgets.py", button, f"marks selected well as {expected}", raw, ok))
    calculate = _find_button(page, "bcaCalculateButton")
    calculate.click()
    sample_text = _find_child(page, QTextEdit, "bcaSampleResultsPanel").toPlainText()
    copy = _find_button(page, "bcaCopyResultButton")
    ok = "Sample 1" in sample_text and copy.isEnabled()
    rows.append(_row("LABTOOLS-WB-BCA-CALCULATE", "BCA", "app/labtools/ui/western_blot_widgets.py", calculate, "calculates BCA results", sample_text, ok))
    if not ok:
        failures.append("BCA calculation missing expected sample result")
    copy.click()
    copied_text = QApplication.clipboard().text()
    rows.append(_row("LABTOOLS-WB-BCA-COPY", "BCA", "app/labtools/ui/western_blot_widgets.py", copy, "copies BCA results", copied_text, "BCA" in copied_text and "Sample 1" in copied_text))
    return rows


def _audit_sds_page(page: LabToolsWesternBlotWidget, audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    _select_tab(page, "配胶与 Lane 布局")
    blank = _find_button(page, "refreshBlankLaneLayoutButton")
    blank.click()
    lane_table = _find_child(page, QTableWidget, "gelLaneLayoutTable")
    rows.append(_row("LABTOOLS-WB-SDS-BLANK-LANE-LAYOUT", "SDS-PAGE", "app/labtools/ui/western_blot_widgets.py", blank, "generates blank lane layout", f"lane_rows={lane_table.rowCount()}", lane_table.rowCount() >= 10))
    import_lanes = _find_button(page, "importLoadingLaneLayoutButton")
    import_lanes.click()
    lane_evidence = ";".join((lane_table.item(row, 1).text() if lane_table.item(row, 1) else "") for row in range(min(3, lane_table.rowCount())))
    rows.append(_row("LABTOOLS-WB-SDS-IMPORT-LOADING-LANES", "SDS-PAGE", "app/labtools/ui/western_blot_widgets.py", import_lanes, "imports loading lane layout", lane_evidence, "S1" in lane_evidence or "Protein Marker" in lane_evidence))
    _fill_sds_template(page)
    calculate = _find_button(page, "primaryButton")
    calculate.click()
    result_text = _find_child(page, QTextEdit, "sdsPageGelResultPanel").toPlainText()
    ok = "总量含余量" in result_text and _find_button(page, "sdsPageTemplateJsonExportButton").isEnabled() and _find_button(page, "sdsPageXlsxExportButton").isEnabled()
    rows.append(_row("LABTOOLS-WB-SDS-CALCULATE", "SDS-PAGE", "app/labtools/ui/western_blot_widgets.py", calculate, "calculates SDS-PAGE gel batch", result_text, ok))
    if not ok:
        failures.append("SDS-PAGE calculation did not enable exports")
    for object_name, artifact in (
        ("sdsPageTemplateJsonExportButton", audit_root / "exports" / "sds_page_template.json"),
        ("sdsPageXlsxExportButton", audit_root / "exports" / "sds_page_calculation.xlsx"),
    ):
        button = _find_button(page, object_name)
        button.click()
        rows.append(_row(f"LABTOOLS-WB-SDS-{object_name}", "SDS-PAGE", "app/labtools/ui/western_blot_widgets.py", button, "exports SDS-PAGE artifact", str(artifact), artifact.exists()))
    import_json = _find_button(page, "sdsPageTemplateJsonImportButton")
    import_json.click()
    result_text = _find_child(page, QTextEdit, "sdsPageGelResultPanel").toPlainText()
    rows.append(_row("LABTOOLS-WB-SDS-IMPORT-JSON", "SDS-PAGE", "app/labtools/ui/western_blot_widgets.py", import_json, "imports SDS-PAGE template JSON", result_text, "导入" in result_text or "检测到同名" in result_text))
    return rows


def _audit_workflow_records(page: LabToolsWesternBlotWidget, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    step_ids = ("sample_preparation", "electrophoresis", "transfer", "blocking", "primary_antibody", "primary_wash", "secondary_antibody", "secondary_wash", "imaging")
    for step_id in step_ids:
        _select_tab_by_prefix(page, f"wbRecordSaveButton_{step_id}")
        _find_child(page, QLineEdit, f"wbRecordField_{step_id}_0").setText(f"{step_id} value")
        _find_child(page, QTextEdit, f"wbRecordSopText_{step_id}").setText(f"{step_id} SOP")
        _find_child(page, QTextEdit, f"wbRecordFreeText_{step_id}").setText(f"{step_id} note")
        for object_name, expected in (
            (f"wbRecordSaveButton_{step_id}", "已保存"),
            (f"wbRecordSaveSopTemplateButton_{step_id}", "已保存"),
            (f"wbRecordLoadLastButton_{step_id}", "已载入"),
            (f"wbRecordExportTextButton_{step_id}", "已导出文本"),
        ):
            button = _find_button(page, object_name)
            button.click()
            status = _find_child(page, QLabel, f"wbRecordStatus_{step_id}").text()
            ok = expected in status
            rows.append(_row(f"LABTOOLS-WB-RECORD-{step_id}-{object_name}", "WB Workflow Records", "app/labtools/ui/western_blot_widgets.py", button, "persists/loads/exports workflow record", status, ok))
            if not ok:
                failures.append(f"{object_name}: expected {expected}")
    return rows


def _audit_wb_roi(page: LabToolsWesternBlotWidget, audit_root: Path, failures: list[str]) -> list[ContractRow]:
    rows: list[ContractRow] = []
    _select_tab(page, "结果与灰度分析")
    roi = _roi_page(page)
    image_path = audit_root / "wb_preview.png"
    _write_png(image_path)
    _find_child(roi, QLineEdit, "wbImagePathInput").setText(str(image_path))
    import_image = _find_button(roi, "wbImageImportButton")
    import_image.click()
    info = _find_child(roi, QLabel, "wbImageImportInfo").text()
    rows.append(_row("LABTOOLS-WB-ROI-IMPORT-IMAGE", "WB ROI Analysis", "app/labtools/ui/western_blot_roi_widgets.py", import_image, "loads WB image path", info, "是否可读取：已记录" in info))
    preprocess = _find_button(roi, "wbPreprocessButton")
    rows.append(_disabled_row("LABTOOLS-WB-ROI-PREPROCESS-GATE", "WB ROI Analysis", "app/labtools/ui/western_blot_roi_widgets.py", preprocess))
    _find_child(roi, QLineEdit, "wbImagePathInput").setText(str(image_path))
    for object_name, ok_check in (
        ("wbCreateRoiButton", lambda: _find_child(roi, QTableWidget, "wbRoiTable").rowCount() == 1),
        ("wbSetFixedRoiSizeButton", lambda: "x" in _find_child(roi, QLabel, "wbFixedRoiSizeLabel").text()),
        ("wbCopyRoiNextLaneButton", lambda: _find_child(roi, QTableWidget, "wbRoiTable").rowCount() >= 2),
        ("wbCopyRoiAllLanesButton", lambda: _find_child(roi, QTableWidget, "wbRoiTable").rowCount() >= 2),
        ("wbUnifyRoiSizeButton", lambda: _find_child(roi, QTableWidget, "wbRoiTable").rowCount() >= 1),
    ):
        if object_name == "wbCreateRoiButton":
            _find_child(roi, QLineEdit, "wbImagePathInput").setText(str(image_path))
        button = _find_button(roi, object_name)
        if object_name == "wbCreateRoiButton":
            roi._roi_x.setValue(10)
            roi._roi_y.setValue(20)
            roi._roi_w.setValue(30)
            roi._roi_h.setValue(12)
            roi._roi_label.setText("Target Lane 1")
        button.click()
        ok = ok_check()
        rows.append(_row(f"LABTOOLS-WB-ROI-{object_name}", "WB ROI Analysis", "app/labtools/ui/western_blot_roi_widgets.py", button, "updates manual ROI workspace", f"roi_rows={_find_child(roi, QTableWidget, 'wbRoiTable').rowCount()}", ok))
    before_delete_rows = _find_child(roi, QTableWidget, "wbRoiTable").rowCount()
    for object_name, ok_check in (
        ("wbDeleteSelectedRoiButton", lambda row_count: row_count == max(0, before_delete_rows - 1)),
        ("wbClearRoiButton", lambda row_count: row_count == 0),
    ):
        button = _find_button(roi, object_name)
        button.click()
        row_count = _find_child(roi, QTableWidget, "wbRoiTable").rowCount()
        rows.append(_row(f"LABTOOLS-WB-ROI-{object_name}", "WB ROI Analysis", "app/labtools/ui/western_blot_roi_widgets.py", button, "removes manual ROI entries", f"roi_rows={row_count}", ok_check(row_count)))
    _seed_roi(roi, image_path)
    for object_name, artifact in (
        ("wbSaveRoiButton", audit_root / "wb_roi_tasks" / "manual_wb_rois" / "wb_rois.csv"),
        ("wbExportRoiButton", audit_root / "wb_roi_tasks" / "manual_wb_rois" / "wb_rois.csv"),
    ):
        button = _find_button(roi, object_name)
        button.click()
        rows.append(_row(f"LABTOOLS-WB-ROI-{object_name}", "WB ROI Analysis", "app/labtools/ui/western_blot_roi_widgets.py", button, "exports ROI coordinate artifacts", str(artifact), artifact.exists()))
    measure = _find_button(roi, "wbMeasureRoiButton")
    measure.click()
    workspace = roi.latest_workspace()
    ok = bool(workspace and workspace.run_request_path.exists() and (workspace.task_dir / "rois" / "wb_rois.csv").exists())
    rows.append(_row("LABTOOLS-WB-ROI-MEASURE-RUN-REQUEST", "WB ROI Analysis", "app/labtools/ui/western_blot_roi_widgets.py", measure, "creates WB ROI run request", "run_request_exists=" + str(ok), ok))
    if not ok:
        failures.append("WB ROI run request missing")
    measurement_csv = audit_root / "wb_measurements.csv"
    measurement_csv.write_text(_measurement_csv(str(image_path)), encoding="utf-8")
    _find_child(roi, QLineEdit, "wbMeasurementCsvPathInput").setText(str(measurement_csv))
    load = _find_button(roi, "wbLoadMeasurementCsvButton")
    load.click()
    rows.append(_row("LABTOOLS-WB-ROI-LOAD-MEASUREMENT-CSV", "WB ROI Analysis", "app/labtools/ui/western_blot_roi_widgets.py", load, "loads external measurement CSV", f"measurement_rows={_find_child(roi, QTableWidget, 'wbMeasurementTable').rowCount()}", _find_child(roi, QTableWidget, "wbMeasurementTable").rowCount() == 3))
    for object_name in ("wbCalculateTargetControlButton", "wbCalculateTargetTotalButton"):
        button = _find_button(roi, object_name)
        button.click()
        rows.append(_row(f"LABTOOLS-WB-ROI-{object_name}", "WB ROI Analysis", "app/labtools/ui/western_blot_roi_widgets.py", button, "calculates WB normalized ratios", f"normalized_rows={_find_child(roi, QTableWidget, 'wbNormalizationTable').rowCount()}", _find_child(roi, QTableWidget, "wbNormalizationTable").rowCount() >= 1))
    export = _find_button(roi, "wbExportNormalizedResultsButton")
    export.click()
    normalized = audit_root / "wb_roi_tasks" / "manual_wb_rois" / "wb_normalized_results.csv"
    rows.append(_row("LABTOOLS-WB-ROI-EXPORT-NORMALIZED", "WB ROI Analysis", "app/labtools/ui/western_blot_roi_widgets.py", export, "exports normalized WB results CSV", str(normalized), normalized.exists()))
    return rows


def _capture_screenshots(app: QApplication, page: LabToolsWesternBlotWidget, screenshot_dir: Path) -> list[dict[str, str]]:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    shots: list[dict[str, str]] = []
    for name, tab in (
        ("01_protein_wb_overview", "流程工作台"),
        ("02_bca_results", "BCA 蛋白浓度测定"),
        ("03_protein_loading_records", "蛋白上样计算"),
        ("04_sds_page_lane_layout", "配胶与 Lane 布局"),
        ("05_workflow_record", "电泳记录"),
        ("06_wb_roi_analysis", "结果与灰度分析"),
    ):
        _select_tab(page, tab)
        app.processEvents()
        scroll = page.findChild(QScrollArea, "labToolsWesternBlotScroll")
        if scroll is not None:
            scroll.verticalScrollBar().setValue(0)
        path = screenshot_dir / f"{name}.png"
        page.resize(1500, 950)
        page.grab().save(str(path))
        shots.append({"name": name, "path": str(path)})
    return shots


def _sanitize_audit_root(rows: list[ContractRow], audit_root: Path) -> None:
    needle = str(audit_root)
    for row in rows:
        row.artifact_evidence = row.artifact_evidence.replace(needle, "<audit_root>")


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


def _tabs(page: LabToolsWesternBlotWidget) -> QTabWidget:
    return _find_child(page, QTabWidget, "westernBlotTabs")


def _select_tab(page: LabToolsWesternBlotWidget, label: str) -> None:
    tabs = _tabs(page)
    for index in range(tabs.count()):
        if tabs.tabText(index) == label:
            tabs.setCurrentIndex(index)
            return
    raise AssertionError(f"Missing Western Blot tab {label}")


def _select_tab_by_prefix(page: LabToolsWesternBlotWidget, object_name: str) -> None:
    tabs = _tabs(page)
    for index in range(tabs.count()):
        tabs.setCurrentIndex(index)
        if page.findChild(QPushButton, object_name) is not None:
            return
    raise AssertionError(f"Missing Western Blot button {object_name}")


def _roi_page(page: LabToolsWesternBlotWidget):
    _select_tab(page, "结果与灰度分析")
    return _tabs(page).currentWidget()


def _bca_matrix_text() -> str:
    values = [[0.10 for _ in range(12)] for _ in range(8)]
    for index, value in enumerate((0.10, 0.10, 0.30, 0.30, 0.50, 0.50, 0.40, 0.40)):
        values[0][index] = value
    return "\n".join("\t".join(f"{value:.3f}" for value in row) for row in values)


def _fill_sds_template(page: LabToolsWesternBlotWidget) -> None:
    _find_child(page, QLineEdit, "sdsPageTemplateNameField").setText("Audit 10% gel")
    _find_child(page, QLineEdit, "sdsPageGelConcentrationField").setText("10%")
    _find_child(page, QComboBox, "sdsPageGelThicknessCombo").setCurrentText("1.0 mm")
    _find_child(page, QComboBox, "sdsPageWellCountCombo").setCurrentText("10 wells")
    _find_child(page, QLineEdit, "sdsPageGelCountField").setText("2")
    _find_child(page, QLineEdit, "sdsPageOveragePercentField").setText("3")
    _find_child(page, QLineEdit, "sdsPageResolvingComponentNameField").setText("Acrylamide mix")
    _find_child(page, QLineEdit, "sdsPageResolvingAmountField").setText("2.5")
    _find_child(page, QComboBox, "sdsPageResolvingUnitCombo").setCurrentText("mL")
    _find_child(page, QLineEdit, "sdsPageStackingComponentNameField").setText("Stacking buffer")
    _find_child(page, QLineEdit, "sdsPageStackingAmountField").setText("1")
    _find_child(page, QComboBox, "sdsPageStackingUnitCombo").setCurrentText("mL")


def _write_png(path: Path) -> None:
    image = QImage(160, 100, QImage.Format_RGB32)
    image.fill(QColor("#D9E7F7"))
    image.save(str(path), "PNG")


def _seed_roi(roi, image_path: Path) -> None:
    _find_child(roi, QLineEdit, "wbImagePathInput").setText(str(image_path))
    _find_button(roi, "wbImageImportButton").click()
    roi._roi_x.setValue(10)
    roi._roi_y.setValue(20)
    roi._roi_w.setValue(30)
    roi._roi_h.setValue(12)
    roi._roi_label.setText("Target Lane 1")
    _find_button(roi, "wbCreateRoiButton").click()


def _measurement_csv(image_path: str) -> str:
    return "\n".join(
        (
            "roi_id,image_id,image_path,roi_type,label,lane_index,sample_name,x,y,width,height,area,mean_gray_value,integrated_density,raw_integrated_density,background_roi_id,notes",
            f"target1,img,{image_path},target_band,Target,1,S1,10,20,30,12,360,80,28800,30000,bg1,",
            f"control1,img,{image_path},control_band,Control,1,S1,10,40,30,12,360,40,14400,15000,bg1,",
            f"bg1,img,{image_path},background,Background,1,S1,10,60,30,12,360,5,1800,2000,,",
            "",
        )
    )


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# UI Route Contract LabTools Batch 4: Protein / Western Blot",
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
