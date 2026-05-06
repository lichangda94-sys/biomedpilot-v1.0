from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from app.bioinformatics.services.geo_differential_expression_runner import run_geo_differential_expression


def _write_xlsx_rows(path: Path, rows: list[list[object]]) -> Path:
    sheet_rows: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells: list[str] = []
        for column_index, value in enumerate(row):
            reference = f"{chr(ord('A') + column_index)}{row_index}"
            if isinstance(value, (int, float)):
                cells.append(f'<c r="{reference}"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{reference}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    worksheet_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        "</worksheet>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", worksheet_xml)
    return path


def test_geo_deg_runner_infers_tumor_control_xlsx_and_ignores_derived_fc_columns(tmp_path: Path) -> None:
    source = tmp_path / "GSE315375_exp_tyroid_controlX5.xlsx"
    _write_xlsx_rows(
        source,
        [
            ["Genes", "", "Control", "Tumor", "control+1", "tumor+1", "FC", "Log2FC"],
            ["CLDN16", "protein_coding", 0, 1078, 1, 1079, 1079, 10.07],
            ["RNU2-2P", "snRNA", 680, 89578, 681, 89579, 131.54, 7.03],
            ["", "", "", "", "", "", "", ""],
            ["GAPDH", "protein_coding", 100, 101, 101, 100, 1.0, 0.0],
        ],
    )

    summary = run_geo_differential_expression(source, output_dir=tmp_path / "analysis", dataset_id="GSE315375")

    assert summary["formal_deg_executed"] is True
    assert summary["statistical_engine"] in {"scipy_welch_t_test", "standard_library_permutation_or_welch_approx"}
    assert summary["case_samples"] == ["Tumor", "tumor+1"]
    assert summary["control_samples"] == ["Control", "control+1"]
    assert "FC" not in summary["case_samples"]
    result_path = Path(str(summary["result_path"]))
    rows = list(csv.DictReader(result_path.open(encoding="utf-8")))
    assert rows
    assert rows[0]["gene_id"] in {"CLDN16", "RNU2-2P"}
    assert float(rows[0]["log2_fold_change"]) > 0
    assert rows[0]["p_value"]
    assert rows[0]["adjusted_p_value"]
    payload = json.loads(Path(str(summary["summary_path"])).read_text(encoding="utf-8"))
    assert payload["dataset_id"] == "GSE315375"
    assert payload["row_count_skipped"] == 0


def test_geo_deg_runner_infers_cuet_vs_untreated_csv(tmp_path: Path) -> None:
    source = tmp_path / "GSE317461_Thy.8505C.cells.cpm.csv"
    source.write_text(
        "\n".join(
            [
                '"rowname","X8505c.CUET.4.BAM","X8505c.CUET.6.BAM","X8505c.UT.1.BAM","X8505c.UT.5.BAM","SYMBOL"',
                '"653635",11.2,14.0,9.1,11.7,"WASH7P"',
                '"102723897",4.3,3.8,5.0,4.1,"LOC102723897"',
                '"79854",1.3,2.7,2.5,3.6,"LINC00115"',
            ]
        ),
        encoding="utf-8",
    )

    summary = run_geo_differential_expression(source, output_dir=tmp_path / "analysis", dataset_id="GSE317461")

    assert summary["case_samples"] == ["X8505c.CUET.4.BAM", "X8505c.CUET.6.BAM"]
    assert summary["control_samples"] == ["X8505c.UT.1.BAM", "X8505c.UT.5.BAM"]
    assert Path(str(summary["result_path"])).exists()
