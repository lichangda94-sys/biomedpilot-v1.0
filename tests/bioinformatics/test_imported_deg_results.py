from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from app.bioinformatics.deg_task_plan import build_deg_preflight
from app.bioinformatics.imported_deg_results import (
    list_imported_deg_results,
    mark_imported_deg_report_candidates,
    save_imported_deg_column_mapping,
)
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.results.project_results import load_result_index, write_result_index


def _write_xlsx_rows(path: Path, rows: list[list[object]]) -> Path:
    xml_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            col = chr(ord("A") + col_index - 1)
            text = escape(str(value))
            cells.append(f'<c r="{col}{row_index}" t="inlineStr"><is><t>{text}</t></is></c>')
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    worksheet_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(xml_rows)}</sheetData>'
        "</worksheet>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", worksheet_xml)
    return path


def test_imported_deg_result_browser_profiles_columns_and_counts(tmp_path: Path) -> None:
    project_root = create_bioinformatics_project("Imported DEG Project", tmp_path).project_root
    source = project_root / "raw_data" / "local_import" / "deg_results.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "gene,logFC,P.Value,adj.P.Val\n"
        "TP53,1.2,0.01,0.02\n"
        "EGFR,-1.4,0.02,0.03\n"
        "ACTB,0.2,0.5,0.8\n",
        encoding="utf-8",
    )
    run_project_recognition(project_root)

    results = list_imported_deg_results(project_root)

    assert len(results) == 1
    result = results[0]
    assert result.status == "ready"
    assert result.source_label == "用户导入 / 外部分析结果"
    assert result.column_mapping["gene"] == "gene"
    assert result.column_mapping["logfc"] == "logFC"
    assert result.column_mapping["fdr"] == "adj.P.Val"
    assert result.regulation_counts["status"] == "computed"
    assert result.regulation_counts["up"] == 1
    assert result.regulation_counts["down"] == 1
    assert result.regulation_counts["not_significant"] == 1
    assert result.top_up_genes[0]["gene"] == "TP53"
    assert result.top_down_genes[0]["gene"] == "EGFR"
    assert "not_biomedpilot_computed" in result.to_dict()["semantic_boundary"]


def test_imported_deg_can_be_report_candidate_but_not_preflight_input(tmp_path: Path) -> None:
    project_root = create_bioinformatics_project("Imported DEG Boundary", tmp_path).project_root
    source = project_root / "raw_data" / "local_import" / "deg_results.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene,logFC,P.Value,adj.P.Val\nTP53,1.2,0.01,0.02\n", encoding="utf-8")
    run_project_recognition(project_root)

    entries = mark_imported_deg_report_candidates(project_root)
    preflight = build_deg_preflight(project_root)

    assert entries
    assert entries[0]["result_semantics"] == "imported result"
    assert entries[0]["report_candidate"] is True
    assert entries[0]["result_type"] == "导入结果"
    assert entries[0]["report_usage_label"] == "可进入报告草稿，必须标明导入来源"
    manifest_path = project_root / str(entries[0]["manifest_ref"])
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "biomedpilot.imported_deg_result_manifest.v1"
    assert manifest["semantic_boundary"] == "imported_external_deg_not_biomedpilot_computed"
    assert manifest["report_sentence_policy"] == "用户导入的外部分析结果显示"
    assert "重新计算" in entries[0]["warning"]
    assert preflight.status == "blocked"
    assert preflight.manifest["input_summary"]["imported_deg_detected"] is True  # type: ignore[index]
    assert any("导入差异结果不能作为重新计算 DEG" in item for item in preflight.manifest["warnings"])  # type: ignore[index]
    result_index = load_result_index(project_root)
    assert result_index["entries"][0]["result_semantics"] == "imported result"  # type: ignore[index]
    assert not (project_root / "results" / "tables").exists()
    assert not (project_root / "results" / "figures").exists()


def test_imported_deg_supports_xlsx_and_manual_mapping(tmp_path: Path) -> None:
    project_root = create_bioinformatics_project("Imported DEG XLSX", tmp_path).project_root
    source = project_root / "raw_data" / "local_import" / "deg_results.xlsx"
    _write_xlsx_rows(
        source,
        [
            ["symbol", "effect", "raw_p", "q_value", "stat", "baseMean"],
            ["MYC", "2.2", "0.001", "0.004", "4.1", "120"],
            ["CDKN1A", "-1.8", "0.002", "0.006", "-3.9", "80"],
            ["GAPDH", "0.1", "0.8", "0.9", "0.2", "200"],
        ],
    )
    write_result_index(
        project_root,
        [
            {
                "result_name": "Collaborator DEG workbook",
                "analysis_type": "differential_expression",
                "path": str(source),
                "status": "imported",
                "result_semantics": "imported result",
            }
        ],
    )

    first = list_imported_deg_results(project_root)[0]
    assert first.status == "needs_confirmation"
    save_imported_deg_column_mapping(
        project_root,
        result_id=first.result_id,
        column_mapping={"gene": "symbol", "logfc": "effect", "pvalue": "raw_p", "fdr": "q_value", "statistic": "stat", "base_mean": "baseMean"},
        user_note="limma output from collaborator",
    )

    result = list_imported_deg_results(project_root)[0]
    assert result.status == "ready"
    assert result.mapping_status == "user_confirmed"
    assert result.column_mapping["logfc"] == "effect"
    assert result.column_mapping["statistic"] == "stat"
    assert result.column_mapping["base_mean"] == "baseMean"
    assert result.user_note == "limma output from collaborator"
    assert result.regulation_counts["up"] == 1
    assert result.regulation_counts["down"] == 1

    entries = mark_imported_deg_report_candidates(project_root)
    assert entries[0]["report_candidate"] is True
    manifest = json.loads((project_root / str(entries[0]["manifest_ref"])).read_text(encoding="utf-8"))
    assert manifest["user_note"] == "limma output from collaborator"
    assert manifest["mapping_status"] == "user_confirmed"


def test_imported_deg_missing_columns_are_not_registered_without_confirmation(tmp_path: Path) -> None:
    project_root = create_bioinformatics_project("Imported DEG Missing Columns", tmp_path).project_root
    source = project_root / "raw_data" / "local_import" / "deg_results.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene,effect\nTP53,1.2\n", encoding="utf-8")
    write_result_index(
        project_root,
        [
            {
                "result_name": "Incomplete imported DEG",
                "analysis_type": "differential_expression",
                "path": str(source),
                "status": "imported",
                "result_semantics": "imported result",
            }
        ],
    )

    results = list_imported_deg_results(project_root)
    assert results[0].status == "needs_confirmation"
    assert results[0].regulation_counts["status"] == "unavailable"
    entries = mark_imported_deg_report_candidates(project_root)
    assert not any(item.get("report_candidate") for item in entries)
    assert not (project_root / "analysis" / "deg" / "imported" / results[0].result_id / "imported_deg_result_manifest.json").exists()
