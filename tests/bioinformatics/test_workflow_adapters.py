from __future__ import annotations

import json
import gzip
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

from app.bioinformatics.project_analysis_tasks import create_analysis_task, load_analysis_task_center
from app.bioinformatics.project_readiness import load_readiness_artifacts, run_project_readiness
from app.bioinformatics.project_recognition import TYPE_LABELS, load_recognition_report, run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets, load_standardization_artifacts
from app.bioinformatics.project_workflow_orchestrator import load_workflow_state, run_project_stage, run_project_workflow
from app.bioinformatics.project_workspace import create_bioinformatics_project
from app.bioinformatics.project_workspace_binding import (
    generate_gse_acquisition_plan,
    load_latest_acquisition_summary,
    read_acquisition_artifacts,
    register_acquisition,
)
from app.bioinformatics.reports.project_report_builder import generate_project_report, load_project_report
from app.bioinformatics.results.project_results import load_result_index, write_result_index


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return create_bioinformatics_project("Workflow Adapter Project", tmp_path).project_root


def _write_xlsx_count_matrix(path: Path) -> Path:
    rows = [
        ["gene_id", "A1_count", "A2_count", "B1_count"],
        ["ENSMUSG00000026193", 195458, 215969, 197661],
        ["ENSMUSG00000064351", 160365, 142505, 129666],
    ]
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


def _write_geo_family_soft(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "^DATABASE = GeoMiame",
                "!Database_name = Gene Expression Omnibus (GEO)",
                "^SERIES = GSE6004",
                "!Series_title = Gene Expression and Functional Evidence of EMT in PTC",
                "!Series_geo_accession = GSE6004",
                "!Series_type = Expression profiling by array",
                "!Series_sample_id = GSM139002",
                "!Series_sample_id = GSM139003",
                "^PLATFORM = GPL570",
                "!Platform_title = [HG-U133_Plus_2] Affymetrix Human Genome U133 Plus 2.0 Array",
                "!platform_table_begin",
                "ID\tGene Symbol",
                "1007_s_at\tDDR1",
                "!platform_table_end",
                "^SAMPLE = GSM139002",
                "!Sample_title = PC10: Normal thyroid paired with tumor",
                "!Sample_characteristics_ch1 = Tissue: normal thyroid; Gender: male; Age: 71",
                "#ID_REF =",
                "#VALUE = RMA Gene Expression Estimates",
                "!sample_table_begin",
                "ID_REF\tVALUE",
                "1007_s_at\t8.4",
                "!sample_table_end",
                "^SAMPLE = GSM139003",
                "!Sample_title = PC11: Papillary thyroid cancer invasive front",
                "!Sample_characteristics_ch1 = Tissue: tumor; Gender: female; Age: 55",
                "#ID_REF =",
                "#VALUE = RMA Gene Expression Estimates",
                "!sample_table_begin",
                "ID_REF\tVALUE",
                "1007_s_at\t9.1",
                "!sample_table_end",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_geo_series_matrix(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "!Series_title = Thyroid cancer expression profile",
                "!Series_geo_accession = GSE12345",
                "!Series_platform_id = GPL570",
                "!Sample_title = Tumor sample 1",
                "!Sample_title = Normal sample 1",
                "!Sample_geo_accession = GSM100001",
                "!Sample_geo_accession = GSM100002",
                "!Sample_characteristics_ch1 = tissue: tumor",
                "!Sample_characteristics_ch1 = tissue: normal",
                "!Sample_source_name_ch1 = thyroid cancer tissue",
                "!series_matrix_table_begin",
                '"ID_REF"\t"GSM100001"\t"GSM100002"',
                '"1007_s_at"\t8.1\t6.2',
                '"1053_at"\t4.4\t5.0',
                "!series_matrix_table_end",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _asset_by_role(record: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(asset.get("role") or asset.get("asset_type")): asset for asset in record.get("detected_assets", []) if isinstance(asset, dict)}


def test_acquisition_binding_generates_plan_record_handoff(project_root: Path, tmp_path: Path) -> None:
    source = tmp_path / "expression_matrix.tsv"
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")

    summary = register_acquisition(
        project_root,
        source_type="local_import",
        source_label="本地表达矩阵",
        strategy="reference",
        selected_paths=[source],
    )

    assert summary.strategy == "reference"
    assert summary.record_path.exists()
    assert summary.handoff_path.exists()
    assert summary.referenced_paths == (str(source.resolve()),)
    artifacts = read_acquisition_artifacts(project_root)
    assert artifacts["record"]["strategy"] == "reference"  # type: ignore[index]


def test_gse_acquisition_plan_is_plan_only(project_root: Path) -> None:
    summary = generate_gse_acquisition_plan(project_root, "GSE33630")

    assert summary.strategy == "plan_only"
    assert summary.source_type == "geo_gse"
    assert load_latest_acquisition_summary(project_root).source_label == "GSE33630"  # type: ignore[union-attr]
    assert read_acquisition_artifacts(project_root)["record"]["strategy"] == "plan_only"  # type: ignore[index]


def test_plan_only_project_is_not_ready(project_root: Path) -> None:
    generate_gse_acquisition_plan(project_root, "GSE33630")
    run_project_recognition(project_root)

    readiness = run_project_readiness(project_root)
    report = readiness["readiness_report"]  # type: ignore[index]
    matrix_rows = readiness["capability_matrix"]["rows"]  # type: ignore[index]

    assert report["overall_status"] == "not_ready"
    assert report["has_core_input"] is False
    assert not any(row["analysis_type"] == "reporting" and row["can_run"] for row in matrix_rows)


def test_recognition_readiness_standardization_chain(project_root: Path) -> None:
    raw_file = project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")

    recognition = run_project_recognition(project_root)
    assert load_recognition_report(project_root) is not None
    assert recognition["files"][0]["recognized_type"] == "expression_matrix"  # type: ignore[index]
    assert TYPE_LABELS["unknown"] == "未知文件"

    readiness = run_project_readiness(project_root)
    matrix_rows = readiness["capability_matrix"]["rows"]  # type: ignore[index]
    assert any(row["label"] == "差异表达分析" for row in matrix_rows)
    assert load_readiness_artifacts(project_root)["readiness_report"] is not None

    standardization = generate_standardized_assets(project_root)
    assert "不等于正式 biological normalization" in standardization["registry"]["warnings"][0]  # type: ignore[index]
    assert load_standardization_artifacts(project_root)["registry"] is not None


def test_recognition_classifies_xlsx_gene_count_matrix(project_root: Path) -> None:
    raw_file = project_root / "raw_data" / "local_import" / "GSE236866_Processed_data_tau_with_inhibitors.xlsx"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    _write_xlsx_count_matrix(raw_file)

    recognition = run_project_recognition(project_root)

    assert recognition["files"][0]["file_name"] == "GSE236866_Processed_data_tau_with_inhibitors.xlsx"  # type: ignore[index]
    assert recognition["files"][0]["recognized_type"] == "raw_count_matrix"  # type: ignore[index]
    assert recognition["files"][0]["recognized_type_zh"] == "原始计数矩阵"  # type: ignore[index]
    assert "count 样本列" in recognition["files"][0]["reason"]  # type: ignore[index]


def test_reference_acquisition_is_scanned_by_recognition(project_root: Path, tmp_path: Path) -> None:
    source = tmp_path / "expression_matrix.tsv"
    source.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    register_acquisition(
        project_root,
        source_type="local_import",
        source_label="本地表达矩阵",
        strategy="reference",
        selected_paths=[source],
    )

    recognition = run_project_recognition(project_root)

    assert recognition["files"][0]["original_path"] == str(source.resolve())  # type: ignore[index]
    assert recognition["files"][0]["recognized_type"] == "expression_matrix"  # type: ignore[index]


def test_geo_family_soft_is_multirole_container(project_root: Path, tmp_path: Path) -> None:
    source = _write_geo_family_soft(tmp_path / "GSE6004_family.soft")
    register_acquisition(
        project_root,
        source_type="local_import",
        source_label="GEO family SOFT",
        strategy="reference",
        selected_paths=[source],
    )

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]

    assert record["recognized_type"] == "geo_soft_container"
    assert record["recognized_type_zh"] == "GEO SOFT 容器"
    assert set(record["recognized_roles"]) >= {"expression_matrix", "sample_metadata", "platform_annotation", "clinical_metadata"}
    assert {asset["asset_type"] for asset in record["detected_assets"]} >= {"expression_matrix", "sample_metadata", "platform_annotation", "clinical_metadata"}
    assert recognition["type_counts"]["geo_soft_container"] == 1  # type: ignore[index]
    assert recognition["type_counts"]["expression_matrix"] == 1  # type: ignore[index]
    assert recognition["type_counts"]["sample_metadata"] == 1  # type: ignore[index]

    readiness = run_project_readiness(project_root)
    report = readiness["readiness_report"]  # type: ignore[index]
    assert report["has_core_input"] is True
    assert "expression_matrix" in report["available_inputs"]
    assert "sample_metadata" in report["available_inputs"]
    assert "样本信息缺失。" not in report["warnings"]

    standardization = generate_standardized_assets(project_root)
    asset_types = {asset["asset_type"] for asset in standardization["registry"]["assets"]}  # type: ignore[index]
    assert asset_types >= {"expression_matrix", "sample_metadata", "platform_annotation", "clinical_metadata"}


def test_geo_series_matrix_detects_multirole_assets(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "GSE12345-GPL570_series_matrix.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    _write_geo_series_matrix(source)

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]
    assets = _asset_by_role(record)  # type: ignore[arg-type]

    assert record["recognized_type"] == "geo_series_matrix_container"
    assert set(record["recognized_roles"]) >= {"expression_matrix", "sample_metadata", "platform_reference_hint"}  # type: ignore[arg-type]
    assert {"phenotype_metadata", "clinical_metadata"} & set(record["recognized_roles"])  # type: ignore[arg-type]
    assert assets["expression_matrix"]["input_eligible"] is True
    assert assets["expression_matrix"]["location"]["start_line"] == 11  # type: ignore[index]
    assert assets["expression_matrix"]["location"]["header_line"] == 12  # type: ignore[index]
    assert assets["expression_matrix"]["location"]["end_line"] == 15  # type: ignore[index]
    assert "ID_REF header" in assets["expression_matrix"]["evidence"]
    assert assets["sample_metadata"]["input_eligible"] is True
    assert assets["platform_reference_hint"]["input_eligible"] is False
    assert assets["platform_reference_hint"]["platform_id"] == "GPL570"


def test_csv_expression_matrix_content_profile(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "matrix.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene,A1,A2,B1\nTP53,1.2,1.5,1.8\nEGFR,4.0,4.1,4.3\n", encoding="utf-8")

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]
    assets = _asset_by_role(record)  # type: ignore[arg-type]

    assert record["recognized_type"] == "normalized_expression_matrix"
    assert "normalized_expression_matrix" in assets
    assert assets["normalized_expression_matrix"]["input_eligible"] is True
    assert record["content_profile"]["possible_table_role"] == "normalized_expression_matrix"  # type: ignore[index]
    assert "differential_result_table" not in record["recognized_roles"]  # type: ignore[operator]


def test_csv_raw_count_matrix_content_profile(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "counts.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene,A1_count,A2_count,B1_count\nTP53,12,15,18\nEGFR,40,41,43\n", encoding="utf-8")

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]
    assets = _asset_by_role(record)  # type: ignore[arg-type]

    assert record["recognized_type"] == "raw_count_matrix"
    assert assets["raw_count_matrix"]["input_eligible"] is True


def test_csv_sample_metadata_content_profile(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "samples.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("sample_id,group,tissue,condition\nGSM1,case,thyroid,tumor\nGSM2,control,thyroid,normal\n", encoding="utf-8")

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]

    assert record["recognized_type"] == "sample_metadata"
    assert "expression_matrix" not in record["recognized_roles"]  # type: ignore[operator]


def test_csv_clinical_survival_metadata_content_profile(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "clinical.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("sample_id,age,sex,stage,OS_time,OS_status\nS1,61,F,II,12,1\nS2,55,M,I,24,0\n", encoding="utf-8")

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]

    assert record["recognized_type"] == "clinical_metadata"
    assert {"clinical_metadata", "survival_metadata"} <= set(record["recognized_roles"])  # type: ignore[arg-type]


def test_differential_result_table_not_counted_as_expression_input(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "deg_results.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene,logFC,P.Value,adj.P.Val,t\nTP53,1.2,0.01,0.05,3.1\nEGFR,-1.1,0.02,0.07,-2.8\n", encoding="utf-8")

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]
    assets = _asset_by_role(record)  # type: ignore[arg-type]

    assert record["recognized_type"] == "differential_result_table"
    assert assets["differential_result_table"]["input_eligible"] is False
    readiness = run_project_readiness(project_root)["readiness_report"]  # type: ignore[index]
    assert readiness["has_core_input"] is False
    assert "expression_matrix" not in readiness["available_inputs"]
    standardization = generate_standardized_assets(project_root)
    assert standardization["registry"]["assets"] == []  # type: ignore[index]


def test_gzip_text_expression_matrix_is_recognized(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "expression.tsv.gz"
    source.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(source, "wt", encoding="utf-8") as handle:
        handle.write("gene\tGSM1\tGSM2\tGSM3\nTP53\t1.2\t1.3\t1.4\nEGFR\t2.2\t2.3\t2.4\n")

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]

    assert record["recognized_type"] == "normalized_expression_matrix"
    assert record["container_format"] == "tabular_text"


def test_workflow_and_task_center_do_not_run_analysis(project_root: Path) -> None:
    raw_file = project_root / "raw_data" / "local_import" / "expression_matrix.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("gene\ts1\nTP53\t1\n", encoding="utf-8")
    run_project_recognition(project_root)
    run_project_readiness(project_root)

    stage = run_project_stage(project_root, "task_center")
    assert stage["status"] in {"completed", "completed_with_warnings"}

    center = load_analysis_task_center(project_root)
    assert center["tasks"]
    with pytest.raises(ValueError, match="缺失输入"):
        create_analysis_task(project_root, "differential_expression")

    state = run_project_workflow(project_root)
    assert load_workflow_state(project_root) is not None
    assert state["steps"]


def test_result_and_report_adapters(project_root: Path) -> None:
    missing_result = project_root / "results" / "tables" / "missing.tsv"
    write_result_index(
        project_root,
        [
            {
                "result_name": "Missing table",
                "analysis_type": "preview",
                "file_type": "tsv",
                "path": str(missing_result),
                "status": "created",
            }
        ],
    )
    results = load_result_index(project_root)
    assert "结果文件缺失" in results["warnings"][0]  # type: ignore[index]

    payload = generate_project_report(project_root)
    assert Path(str(payload["markdown_path"])).exists()
    report = load_project_report(project_root)
    assert "PDF" in json.dumps(report["manifest"], ensure_ascii=False)
