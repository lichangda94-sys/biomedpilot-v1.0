from __future__ import annotations

import json
import gzip
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

from app.bioinformatics.project_analysis_tasks import create_analysis_task, load_analysis_task_center
from app.bioinformatics.geo_family_soft_parser import parse_geo_family_soft
from app.bioinformatics.geo_series_matrix_parser import parse_geo_series_matrix
from app.bioinformatics.group_preview import GROUP_PREVIEW_REPORT
from app.bioinformatics.project_readiness import load_readiness_artifacts, run_project_readiness
from app.bioinformatics.project_recognition import TYPE_LABELS, load_recognition_report, run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets, load_standardization_artifacts
from app.bioinformatics.standardization_confirmation import (
    collect_standardization_candidates,
    confirm_group_design_from_preview,
    load_standardization_confirmation,
    save_standardization_confirmation,
)
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
    return _write_xlsx_rows(path, rows)


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
                "#ID = Probe ID",
                "#Gene Symbol = Gene Symbol",
                "!platform_table_begin",
                "ID\tGene Symbol",
                "1007_s_at\tDDR1",
                "!platform_table_end",
                "^SAMPLE = GSM139002",
                "!Sample_title = PC10: Normal thyroid paired with tumor",
                "!Sample_source_name_ch1 = thyroid",
                "!Sample_organism_ch1 = Homo sapiens",
                "!Sample_characteristics_ch1 = tissue: normal thyroid",
                "!Sample_characteristics_ch1 = gender: male",
                "!Sample_characteristics_ch1 = age: 71",
                "#ID_REF = Probe ID",
                "#VALUE = RMA Gene Expression Estimates",
                "!sample_table_begin",
                "ID_REF\tVALUE",
                "1007_s_at\t8.4",
                "!sample_table_end",
                "^SAMPLE = GSM139003",
                "!Sample_title = PC11: Papillary thyroid cancer invasive front",
                "!Sample_source_name_ch1 = thyroid cancer",
                "!Sample_organism_ch1 = Homo sapiens",
                "!Sample_characteristics_ch1 = tissue: tumor",
                "!Sample_characteristics_ch1 = gender: female",
                "!Sample_characteristics_ch1 = age: 55",
                "#ID_REF = Probe ID",
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


def _write_geo_family_soft_metadata_only(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "^DATABASE = GeoMiame",
                "!Database_name = Gene Expression Omnibus (GEO)",
                "^SERIES = GSE6005",
                "!Series_title = Metadata-only GEO family SOFT",
                "!Series_geo_accession = GSE6005",
                "!Series_sample_id = GSM200001",
                "!Series_sample_id = GSM200002",
                "^PLATFORM = GPL570",
                "!Platform_title = [HG-U133_Plus_2] Affymetrix Human Genome U133 Plus 2.0 Array",
                "#ID = Probe ID",
                "#Gene Symbol = Gene Symbol",
                "!platform_table_begin",
                "ID\tGene Symbol",
                "1007_s_at\tDDR1",
                "!platform_table_end",
                "^SAMPLE = GSM200001",
                "!Sample_title = untreated thyroid sample",
                "!Sample_source_name_ch1 = thyroid",
                "!Sample_characteristics_ch1 = tissue: normal thyroid",
                "!Sample_characteristics_ch1 = treatment: untreated",
                "^SAMPLE = GSM200002",
                "!Sample_title = treated thyroid sample",
                "!Sample_source_name_ch1 = thyroid",
                "!Sample_characteristics_ch1 = tissue: normal thyroid",
                "!Sample_characteristics_ch1 = treatment: treated",
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
                "!Sample_organism_ch1 = Homo sapiens",
                "!Sample_organism_ch1 = Homo sapiens",
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
    manifest_path = Path(str(artifacts["record"]["metadata"]["source_manifest_path"]))  # type: ignore[index]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["summary"]["real_file_count"] == 1
    assert manifest["file_records"][0]["sha256"]
    assert manifest["file_records"][0]["status"] == "referenced"


def test_acquisition_binding_preserves_multifile_source_files(project_root: Path, tmp_path: Path) -> None:
    sources = []
    for name in ("GSE6004_family.soft", "expression_matrix.tsv", "sample_metadata.tsv", "clinical.tsv"):
        source = tmp_path / name
        source.write_text("id\tvalue\nA\t1\n", encoding="utf-8")
        sources.append(source)

    summary = register_acquisition(
        project_root,
        source_type="local_import",
        source_label="本地数据导入",
        strategy="reference",
        selected_paths=sources,
    )

    expected = tuple(str(path.resolve()) for path in sources)
    assert summary.source_files == expected
    assert summary.referenced_paths == expected
    artifacts = read_acquisition_artifacts(project_root)
    assert artifacts["record"]["source_files"] == list(expected)  # type: ignore[index]
    assert artifacts["handoff"]["source_files"] == list(expected)  # type: ignore[index]
    manifest_path = Path(str(artifacts["record"]["metadata"]["source_manifest_path"]))  # type: ignore[index]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["summary"]["real_file_count"] == 4
    assert manifest["summary"]["sha256_recorded_count"] == 4


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
    task_types = {task["task_type"] for task in standardization["data_processing_task_plan"]["tasks"]}  # type: ignore[index]
    assert {"expression_matrix_cleaning", "gene_annotation_mapping"} <= task_types


def test_recognition_classifies_xlsx_gene_count_matrix(project_root: Path) -> None:
    raw_file = project_root / "raw_data" / "local_import" / "GSE236866_Processed_data_tau_with_inhibitors.xlsx"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    _write_xlsx_count_matrix(raw_file)

    recognition = run_project_recognition(project_root)

    assert recognition["files"][0]["file_name"] == "GSE236866_Processed_data_tau_with_inhibitors.xlsx"  # type: ignore[index]
    assert recognition["files"][0]["recognized_type"] == "raw_count_matrix"  # type: ignore[index]
    assert recognition["files"][0]["recognized_type_zh"] == "原始计数矩阵"  # type: ignore[index]
    assert recognition["files"][0]["content_profile"]["possible_table_role"] == "raw_count_matrix"  # type: ignore[index]


def test_mixed_detected_expression_assets_allow_standardization_but_not_deg(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "GSE236866_Processed_data_tau_with_inhibitors.xlsx"
    source.parent.mkdir(parents=True, exist_ok=True)
    _write_xlsx_count_matrix(source)
    recognition_path = project_root / "logs" / "recognition" / "recognition_report.json"
    recognition_path.parent.mkdir(parents=True, exist_ok=True)
    recognition_path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.recognition_report.v1",
                "files": [
                    {
                        "file_name": source.name,
                        "original_path": str(source),
                        "recognized_type": "tabular_text_file",
                        "recognized_type_zh": "RNA-seq 综合表达结果表",
                        "recognized_roles": [],
                        "detected_assets": [
                            {"asset_type": "raw_count_matrix", "label_zh": "count 矩阵", "input_eligible": True},
                            {"asset_type": "normalized_expression_matrix", "label_zh": "FPKM 矩阵", "input_eligible": True},
                            {"asset_type": "differential_result_table", "label_zh": "差异分析结果", "input_eligible": False},
                            {"asset_type": "gene_annotation", "label_zh": "基因注释", "input_eligible": True},
                        ],
                        "route_path": str(source),
                    }
                ],
                "type_counts": {"tabular_text_file": 1},
                "warnings": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    readiness = run_project_readiness(project_root)
    report = readiness["readiness_report"]  # type: ignore[index]
    diff_row = next(row for row in readiness["capability_matrix"]["rows"] if row["analysis_type"] == "differential_expression")  # type: ignore[index]

    assert report["has_core_input"] is True
    assert report["standardization_ready"] is True
    assert report["deg_ready"] is False
    assert {"expression_matrix", "raw_count_matrix", "normalized_expression_matrix"} <= set(report["available_inputs"])  # type: ignore[arg-type]
    assert {"sample_metadata", "comparison_config"} <= set(diff_row["missing_inputs"])
    assert diff_row["can_run"] is False

    standardization = generate_standardized_assets(project_root)
    asset_types = {asset["asset_type"] for asset in standardization["registry"]["assets"]}  # type: ignore[index]
    assert {"raw_count_matrix", "normalized_expression_matrix", "gene_annotation"} <= asset_types


def test_count_matrix_without_group_is_standardization_ready_not_deg_ready(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "counts.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene,A1_count,A2_count,B1_count\nTP53,12,15,18\nEGFR,40,41,43\n", encoding="utf-8")

    run_project_recognition(project_root)
    readiness = run_project_readiness(project_root)
    report = readiness["readiness_report"]  # type: ignore[index]
    diff_row = next(row for row in readiness["capability_matrix"]["rows"] if row["analysis_type"] == "differential_expression")  # type: ignore[index]

    assert report["standardization_ready"] is True
    assert report["deg_ready"] is False
    assert {"expression_matrix", "raw_count_matrix"} <= set(report["available_inputs"])  # type: ignore[arg-type]
    assert "comparison_config" in diff_row["missing_inputs"]
    assert diff_row["can_run"] is False


def test_fpkm_expression_matrix_without_group_is_standardization_ready_not_deg_ready(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "fpkm_matrix.csv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene,A1_FPKM,A2_FPKM,B1_FPKM\nTP53,1.2,1.5,1.8\nEGFR,4.0,4.1,4.3\n", encoding="utf-8")

    run_project_recognition(project_root)
    readiness = run_project_readiness(project_root)
    report = readiness["readiness_report"]  # type: ignore[index]
    diff_row = next(row for row in readiness["capability_matrix"]["rows"] if row["analysis_type"] == "differential_expression")  # type: ignore[index]

    assert report["standardization_ready"] is True
    assert report["deg_ready"] is False
    assert {"expression_matrix", "normalized_expression_matrix"} <= set(report["available_inputs"])  # type: ignore[arg-type]
    assert "comparison_config" in diff_row["missing_inputs"]
    assert diff_row["can_run"] is False


def test_recognition_classifies_xlsx_tumor_control_expression_workbook(project_root: Path) -> None:
    raw_file = project_root / "raw_data" / "geo" / "GSE315375" / "supplementary" / "GSE315375_exp_tyroid_controlX5.xlsx"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    _write_xlsx_rows(
        raw_file,
        [
            ["Genes", "", "Control", "Tumor", "control+1", "tumor+1", "FC", "Log2FC"],
            ["MALAT1", "", 10.2, 16.1, 9.8, 15.9, 1.58, 0.66],
            ["GAPDH", "", 7.5, 7.7, 7.6, 7.4, 1.01, 0.01],
            ["ACTB", "", 8.3, 8.9, 8.1, 8.8, 1.07, 0.1],
        ],
    )

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]
    assets = _asset_by_role(record)  # type: ignore[arg-type]

    assert record["recognized_type"] == "normalized_expression_matrix"
    assert record["container_format"] == "xlsx_workbook"
    assert assets["normalized_expression_matrix"]["input_eligible"] is True
    assert record["content_profile"]["delimiter"] == "xlsx"  # type: ignore[index]
    assert "differential_result_table" not in record["recognized_roles"]  # type: ignore[operator]


def test_recognition_ignores_partial_download_files(project_root: Path) -> None:
    raw_root = project_root / "raw_data" / "geo" / "GSE300956"
    raw_root.mkdir(parents=True, exist_ok=True)
    (raw_root / "GSE300956_family.soft.gz.part").write_text("partial download", encoding="utf-8")
    expression = raw_root / "expression.tsv"
    expression.write_text("gene\tcontrol_1\ttreated_1\nTP53\t1.0\t2.0\n", encoding="utf-8")

    recognition = run_project_recognition(project_root)
    names = [str(record["file_name"]) for record in recognition["files"]]  # type: ignore[index]

    assert "GSE300956_family.soft.gz.part" not in names
    assert "expression.tsv" in names


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


def test_recognition_dedupes_raw_file_also_registered_by_reference(project_root: Path) -> None:
    source = project_root / "raw_data" / "geo" / "GSE1001" / "supplementary" / "expression_matrix.tsv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene\tGSM1\tGSM2\nTP53\t1.2\t1.5\nEGFR\t2.4\t2.1\n", encoding="utf-8")
    register_acquisition(
        project_root,
        source_type="geo_accession",
        source_label="GSE1001",
        strategy="reference",
        selected_paths=[source],
    )

    recognition = run_project_recognition(project_root)
    matching_records = [record for record in recognition["files"] if record["file_name"] == "expression_matrix.tsv"]  # type: ignore[index]

    assert len(matching_records) == 1
    assert matching_records[0]["original_path"] == str(source.resolve())
    assert not any("numeric density" in warning for warning in recognition["warnings"])  # type: ignore[operator]


def test_geo_family_soft_is_multirole_container(project_root: Path, tmp_path: Path) -> None:
    source = _write_geo_family_soft(tmp_path / "GSE6004_family.soft")
    parsed = parse_geo_family_soft(source)
    assert parsed["geoparse_status"] == "parsed"
    assert parsed["sample_count"] == 2
    assert parsed["sample_block_count"] == 2
    assert parsed["sample_accessions"] == ["GSM139002", "GSM139003"]
    assert parsed["sample_titles"]["GSM139002"] == "PC10: Normal thyroid paired with tumor"  # type: ignore[index]
    assert "tissue" in parsed["sample_metadata_fields"]  # type: ignore[operator]
    assert "thyroid" in parsed["source_name_ch1"]["GSM139002"]  # type: ignore[index]
    assert "tissue: normal thyroid" in parsed["characteristics_ch1"]["GSM139002"]  # type: ignore[index]
    assert parsed["platform_block_presence"] is True
    assert parsed["platform_annotation_presence"] is True
    assert parsed["expression_table_presence"] is True
    assert any("Homo sapiens" in item for item in parsed["species_evidence"])  # type: ignore[operator]
    assert any("ID_REF" in item or "Gene Symbol" in item for item in parsed["gene_id_evidence"])  # type: ignore[operator]
    assert parsed["parser_depth"] == "table_parsed"

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
    assert record["file_format"] == "SOFT"
    assert record["container_type"] == "geo_family_soft"
    assert record["parser_depth"] == "table_parsed"
    assert record["sample_count"] == 2
    assert record["sample_block_count"] == 2
    assert record["platform_count"] == 1
    assert record["platform_block_presence"] is True
    assert record["platform_annotation_presence"] is True
    assert record["expression_table_presence"] is True
    assert any("Homo sapiens" in item for item in record["species_evidence"])  # type: ignore[operator]
    assert any("ID_REF" in item or "Gene Symbol" in item for item in record["gene_id_evidence"])  # type: ignore[operator]
    assert record["can_enter_standardization"] is True
    assert set(record["recognized_roles"]) >= {"expression_matrix", "sample_metadata", "phenotype_metadata", "platform_annotation", "clinical_metadata"}
    assert {asset["asset_type"] for asset in record["detected_assets"]} >= {"expression_matrix", "sample_metadata", "phenotype_metadata", "platform_annotation", "clinical_metadata"}
    assets = _asset_by_role(record)
    assert assets["expression_matrix"]["requires_user_confirmation"] is True
    assert assets["expression_matrix"]["input_eligible"] is True
    assert "完整解析" not in record["reason"]
    assert "完整表达矩阵" not in record["reason"]
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
    task_types = {task["task_type"] for task in standardization["data_processing_task_plan"]["tasks"]}  # type: ignore[index]
    assert {"expression_matrix_cleaning", "gene_annotation_mapping", "sample_annotation_review"} <= task_types


def test_geo_family_soft_metadata_only_does_not_unlock_standardization(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "GSE6005_family.soft"
    source.parent.mkdir(parents=True, exist_ok=True)
    _write_geo_family_soft_metadata_only(source)

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]

    assert record["recognized_type"] == "geo_soft_container"
    assert record["parser_depth"] == "table_parsed"
    assert record["sample_count"] == 2
    assert record["platform_annotation_presence"] is True
    assert record["expression_table_presence"] is False
    assert record["can_enter_standardization"] is False
    assert "expression_matrix" not in record["recognized_roles"]  # type: ignore[operator]
    assert "sample_metadata" in record["recognized_roles"]  # type: ignore[operator]
    assert "platform_annotation" in record["recognized_roles"]  # type: ignore[operator]
    assert "尚未确认表达矩阵" in record["reason"]
    assert "完整解析" not in record["reason"]

    readiness = run_project_readiness(project_root)
    report = readiness["readiness_report"]  # type: ignore[index]
    assert report["standardization_ready"] is False
    assert report["has_core_input"] is False
    assert "expression_matrix" not in report["available_inputs"]


def test_recognition_skips_organized_geo_soft_duplicate(project_root: Path) -> None:
    source = project_root / "raw_data" / "geo" / "GSE6004" / "GSE6004_family.soft"
    duplicate = project_root / "raw_data" / "geo" / "organized" / "sample_annotation" / "GSE6004_family.soft"
    source.parent.mkdir(parents=True, exist_ok=True)
    duplicate.parent.mkdir(parents=True, exist_ok=True)
    _write_geo_family_soft(source)
    _write_geo_family_soft(duplicate)

    recognition = run_project_recognition(project_root)

    source_paths = [Path(str(item["original_path"])) for item in recognition["files"]]  # type: ignore[index]
    assert source.resolve() in source_paths
    assert duplicate.resolve() not in source_paths
    assert recognition["type_counts"]["geo_soft_container"] == 1  # type: ignore[index]

    standardization = generate_standardized_assets(project_root)
    assets = standardization["registry"]["assets"]  # type: ignore[index]
    soft_assets = [asset for asset in assets if Path(str(asset["source_file"])).name == "GSE6004_family.soft"]
    assert len([asset for asset in soft_assets if asset["asset_type"] == "expression_matrix"]) == 1
    assert len([asset for asset in soft_assets if asset["asset_type"] == "sample_metadata"]) == 1


def test_geo_family_soft_and_xlsx_results_stay_file_scoped(project_root: Path) -> None:
    soft = project_root / "raw_data" / "local_import" / "GSE6005_family.soft"
    xlsx = project_root / "raw_data" / "local_import" / "GSE236866_Processed_data_tau_with_inhibitors.xlsx"
    soft.parent.mkdir(parents=True, exist_ok=True)
    _write_geo_family_soft_metadata_only(soft)
    _write_xlsx_count_matrix(xlsx)

    recognition = run_project_recognition(project_root)
    by_name = {record["file_name"]: record for record in recognition["files"]}  # type: ignore[index]
    soft_record = by_name["GSE6005_family.soft"]
    xlsx_record = by_name["GSE236866_Processed_data_tau_with_inhibitors.xlsx"]

    assert soft_record["recognized_type"] == "geo_soft_container"
    assert soft_record["expression_table_presence"] is False
    assert "raw_count_matrix" not in soft_record["recognized_roles"]  # type: ignore[operator]
    assert "normalized_expression_matrix" not in soft_record["recognized_roles"]  # type: ignore[operator]
    assert "differential_result_table" not in soft_record["recognized_roles"]  # type: ignore[operator]
    assert xlsx_record["recognized_type"] == "raw_count_matrix"
    assert "parser_depth" not in xlsx_record
    assert "sample_count" not in xlsx_record


def test_geo_series_matrix_detects_multirole_assets(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "GSE12345-GPL570_series_matrix.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    _write_geo_series_matrix(source)

    parsed = parse_geo_series_matrix(source)
    assert parsed["series_accession"] == "GSE12345"
    assert parsed["platform_accessions"] == ["GPL570"]
    assert parsed["sample_accessions"] == ["GSM100001", "GSM100002"]
    assert parsed["sample_titles"]["GSM100001"] == "Tumor sample 1"  # type: ignore[index]
    assert parsed["sample_count"] == 2
    assert parsed["expression_matrix_presence"] is True
    assert parsed["expression_matrix_dimensions"] == {"rows": 2, "columns": 3, "sample_columns": 2}
    assert parsed["id_column"] == "ID_REF"
    assert parsed["sample_columns"] == ["GSM100001", "GSM100002"]
    assert parsed["gene_id_type_candidate"] == "probe_id"
    assert parsed["expression_value_type_candidate"] == "normalized_or_log_expression"
    assert any(item["species"] == "Homo sapiens" and item["source_field"] == "Sample_organism_ch1" for item in parsed["species_evidence"])  # type: ignore[index]

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]
    assets = _asset_by_role(record)  # type: ignore[arg-type]

    assert record["recognized_type"] == "geo_series_matrix_container"
    assert record["file_format"] == "TXT"
    assert record["container_type"] == "geo_series_matrix"
    assert record["parser_depth"] == "matrix_previewed"
    assert record["series_accession"] == "GSE12345"
    assert record["platform_accessions"] == ["GPL570"]
    assert record["sample_count"] == 2
    assert record["sample_accessions"] == ["GSM100001", "GSM100002"]
    assert record["expression_matrix_presence"] is True
    assert record["expression_matrix_dimensions"] == {"rows": 2, "columns": 3, "sample_columns": 2}
    assert record["id_column"] == "ID_REF"
    assert record["sample_columns"] == ["GSM100001", "GSM100002"]
    assert record["expression_value_type_candidate"] == "normalized_or_log_expression"
    assert record["gene_id_type_candidate"] == "probe_id"
    assert record["requires_user_confirmation"] is True
    assert record["can_enter_standardization"] is True
    assert set(record["recognized_roles"]) >= {"expression_matrix", "sample_metadata", "platform_reference_hint"}  # type: ignore[arg-type]
    assert {"phenotype_metadata", "clinical_metadata"} & set(record["recognized_roles"])  # type: ignore[arg-type]
    assert assets["expression_matrix"]["input_eligible"] is True
    assert assets["expression_matrix"]["requires_user_confirmation"] is True
    assert assets["expression_matrix"]["location"]["start_line"] == 13  # type: ignore[index]
    assert assets["expression_matrix"]["location"]["header_line"] == 14  # type: ignore[index]
    assert assets["expression_matrix"]["location"]["end_line"] == 17  # type: ignore[index]
    assert "ID_REF header" in assets["expression_matrix"]["evidence"]
    assert assets["sample_metadata"]["input_eligible"] is True
    assert assets["platform_reference_hint"]["input_eligible"] is False
    assert assets["platform_reference_hint"]["platform_id"] == "GPL570"
    assert (project_root / "logs" / "recognition" / "recognized_files.json").exists()
    assert recognition["group_preview"]["status"] == "preview_only"  # type: ignore[index]
    assert recognition["group_preview"]["selected_preview_field"] == "tissue"  # type: ignore[index]
    assert (project_root / GROUP_PREVIEW_REPORT).exists()

    readiness = run_project_readiness(project_root)
    report = readiness["readiness_report"]  # type: ignore[index]
    assert report["standardization_ready"] is True
    assert report["deg_ready"] is False


def test_geo_series_matrix_header_without_rows_is_metadata_not_expression(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "GSE304653_series_matrix.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "\n".join(
            [
                "!Series_title = RNA-seq metadata only",
                "!Series_geo_accession = GSE304653",
                "!Sample_geo_accession\tGSM1\tGSM2",
                "!Sample_characteristics_ch1\ttreatment: exercise\ttreatment: sedentary",
                "!series_matrix_table_begin",
                "ID_REF\tGSM1\tGSM2",
                "!series_matrix_table_end",
            ]
        ),
        encoding="utf-8",
    )

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]

    assert record["recognized_type"] == "geo_series_matrix_container"
    assert "sample_metadata" in record["recognized_roles"]  # type: ignore[operator]
    assert "expression_matrix" not in record["recognized_roles"]  # type: ignore[operator]
    assert record["expression_matrix_presence"] is False
    assert record["can_enter_standardization"] is False
    assert record["content_profile"]["table_data_row_count"] == 0  # type: ignore[index]

    readiness = run_project_readiness(project_root)
    assert readiness["readiness_report"]["standardization_ready"] is False  # type: ignore[index]


def test_geo_series_matrix_gzip_parser_extracts_metadata_and_matrix(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "GSE99999_series_matrix.txt.gz"
    source.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(
        [
            "!Series_title\tDemo gzipped series",
            "!Series_geo_accession\tGSE99999",
            "!Series_summary\tDemo summary",
            "!Series_overall_design\tcase control design",
            "!Series_platform_id\tGPL96",
            "!Sample_title\tcase sample\tcontrol sample",
            "!Sample_geo_accession\tGSM900001\tGSM900002",
            "!Sample_source_name_ch1\tblood case\tblood control",
            "!Sample_organism_ch1\tHomo sapiens\tHomo sapiens",
            "!Sample_characteristics_ch1\tdisease: asthma\tdisease: control",
            "!Sample_treatment_protocol_ch1\ttreated\tuntreated",
            "!series_matrix_table_begin",
            "ID_REF\tGSM900001\tGSM900002",
            "1007_s_at\t10\t12",
            "1053_at\t15\t18",
            "!series_matrix_table_end",
            "",
        ]
    )
    with gzip.open(source, "wt", encoding="utf-8") as handle:
        handle.write(content)

    parsed = parse_geo_series_matrix(source)

    assert parsed["file_format"] == "TXT.GZ"
    assert parsed["series_accession"] == "GSE99999"
    assert parsed["series_summary"] == "Demo summary"
    assert parsed["overall_design"] == "case control design"
    assert parsed["platform_accessions"] == ["GPL96"]
    assert parsed["sample_accessions"] == ["GSM900001", "GSM900002"]
    assert parsed["sample_titles"]["GSM900001"] == "case sample"  # type: ignore[index]
    assert parsed["sample_source_name_ch1"]["GSM900001"] == "blood case"  # type: ignore[index]
    assert "characteristics_ch1" in parsed["sample_metadata_fields"]  # type: ignore[operator]
    assert {"source_name_ch1", "disease", "treatment_protocol_ch1"} <= set(parsed["phenotype_candidate_fields"])  # type: ignore[arg-type]
    assert parsed["phenotype_candidate_values_preview"]["disease"] == ["asthma", "control"]  # type: ignore[index]
    assert parsed["expression_matrix_presence"] is True
    assert parsed["expression_matrix_dimensions"] == {"rows": 2, "columns": 3, "sample_columns": 2}
    assert parsed["expression_value_type_candidate"] == "count_like_candidate"
    assert parsed["gene_id_type_candidate"] == "probe_id"


def test_geo_series_matrix_species_conflict_warns(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "GSE99998_series_matrix.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "\n".join(
            [
                "!Series_geo_accession\tGSE99998",
                "!Series_platform_id\tGPL96",
                "!Sample_geo_accession\tGSM1\tGSM2",
                "!Sample_organism_ch1\tHomo sapiens\tMus musculus",
                "!series_matrix_table_begin",
                "ID_REF\tGSM1\tGSM2",
                "1007_s_at\t1.2\t2.3",
                "!series_matrix_table_end",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_geo_series_matrix(source)

    assert {item["species"] for item in parsed["species_evidence"]} >= {"Homo sapiens", "Mus musculus"}  # type: ignore[index]
    assert any("Conflicting Sample_organism_ch1" in warning for warning in parsed["warnings"])  # type: ignore[operator]


def test_geo_series_matrix_unknown_expression_values_still_standardization_ready(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "GSE99997_series_matrix.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "\n".join(
            [
                "!Series_geo_accession\tGSE99997",
                "!Series_platform_id\tGPL96",
                "!Sample_geo_accession\tGSM1\tGSM2",
                "!Sample_characteristics_ch1\tcondition: case\tcondition: control",
                "!series_matrix_table_begin",
                "ID_REF\tGSM1\tGSM2",
                "1007_s_at\tpresent\tabsent",
                "1053_at\tabsent\tpresent",
                "!series_matrix_table_end",
            ]
        ),
        encoding="utf-8",
    )

    recognition = run_project_recognition(project_root)
    record = recognition["files"][0]  # type: ignore[index]
    readiness = run_project_readiness(project_root)["readiness_report"]  # type: ignore[index]

    assert record["expression_matrix_presence"] is True
    assert record["expression_value_type_candidate"] == "unknown"
    assert record["requires_user_confirmation"] is True
    assert any("Expression value type is unknown" in warning for warning in record["warnings"])  # type: ignore[operator]
    assert readiness["standardization_ready"] is True
    assert readiness["deg_ready"] is False


def test_standardization_confirmation_candidates_and_manifest_for_series_matrix(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "GSE99999_series_matrix.txt.gz"
    source.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(
        [
            "!Series_title\tDemo gzipped series",
            "!Series_geo_accession\tGSE99999",
            "!Series_platform_id\tGPL96",
            "!Sample_title\tcase sample\tcontrol sample",
            "!Sample_geo_accession\tGSM900001\tGSM900002",
            "!Sample_organism_ch1\tHomo sapiens\tHomo sapiens",
            "!Sample_characteristics_ch1\tdisease: asthma\tdisease: control",
            "!series_matrix_table_begin",
            "ID_REF\tGSM900001\tGSM900002",
            "1007_s_at\t10\t12",
            "1053_at\t15\t18",
            "!series_matrix_table_end",
            "",
        ]
    )
    with gzip.open(source, "wt", encoding="utf-8") as handle:
        handle.write(content)

    run_project_recognition(project_root)
    candidates = collect_standardization_candidates(project_root)
    expression = candidates["expression_matrix_candidates"][0]  # type: ignore[index]
    species = candidates["species_candidates"][0]  # type: ignore[index]
    gene = candidates["gene_id_candidates"][0]  # type: ignore[index]

    assert expression["source_file"] == "GSE99999_series_matrix.txt.gz"
    assert expression["source_parser"] == "geo_series_matrix"
    assert expression["expression_value_type_candidate"] == "count_like_candidate"
    assert expression["requires_user_confirmation"] is True
    assert species["species"] == "Homo sapiens"
    assert species["source_field"] == "Sample_organism_ch1"
    assert gene["gene_id_type"] == "probe_id"
    assert gene["gene_id_type"] != "gene_symbol"

    manifest = save_standardization_confirmation(project_root, selected_expression_candidate_id=str(expression["candidate_id"]))
    assert manifest["readiness"]["deg_preflight_ready"] is False  # type: ignore[index]
    manifest = save_standardization_confirmation(
        project_root,
        expression_value_type="count_like_candidate",
        expression_value_type_confirmed=True,
        species="Homo sapiens",
        species_confirmed=True,
        gene_id_type="probe_id",
        gene_id_type_confirmed=True,
    )
    assert manifest["readiness"]["deg_preflight_ready"] is False  # type: ignore[index]
    manifest = confirm_group_design_from_preview(project_root)
    assert manifest["confirmed_group_design"]["group_confirmed"] is True  # type: ignore[index]
    assert manifest["readiness"]["deg_preflight_ready"] is True  # type: ignore[index]
    assert (project_root / "manifests" / "standardization_confirmation.json").exists()
    loaded = load_standardization_confirmation(project_root)
    assert loaded is not None
    assert loaded["readiness"]["standardization_confirmed"] is True  # type: ignore[index]


def test_standardization_confirmation_unknown_expression_value_blocks_deg_preflight(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "GSE99997_series_matrix.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "\n".join(
            [
                "!Series_geo_accession\tGSE99997",
                "!Series_platform_id\tGPL96",
                "!Sample_geo_accession\tGSM1\tGSM2",
                "!Sample_organism_ch1\tHomo sapiens\tHomo sapiens",
                "!Sample_characteristics_ch1\tcondition: case\tcondition: control",
                "!series_matrix_table_begin",
                "ID_REF\tGSM1\tGSM2",
                "1007_s_at\tpresent\tabsent",
                "1053_at\tabsent\tpresent",
                "!series_matrix_table_end",
            ]
        ),
        encoding="utf-8",
    )

    run_project_recognition(project_root)
    candidates = collect_standardization_candidates(project_root)
    expression = candidates["expression_matrix_candidates"][0]  # type: ignore[index]
    save_standardization_confirmation(
        project_root,
        selected_expression_candidate_id=str(expression["candidate_id"]),
        expression_value_type="unknown",
        expression_value_type_confirmed=True,
        species="Homo sapiens",
        species_confirmed=True,
        gene_id_type="probe_id",
        gene_id_type_confirmed=True,
    )
    manifest = confirm_group_design_from_preview(project_root)

    assert manifest["readiness"]["standardization_confirmed"] is True  # type: ignore[index]
    assert manifest["readiness"]["deg_preflight_ready"] is False  # type: ignore[index]
    assert any("unknown" in warning for warning in manifest["warnings"])  # type: ignore[operator]


def test_standardization_confirmation_filters_family_soft_and_detects_xlsx_candidates(project_root: Path) -> None:
    soft_metadata = project_root / "raw_data" / "local_import" / "GSE6005_family.soft"
    soft_expression = project_root / "raw_data" / "local_import" / "GSE6004_family.soft"
    xlsx = project_root / "raw_data" / "local_import" / "GSE236866_Processed_data_tau_with_inhibitors.xlsx"
    soft_metadata.parent.mkdir(parents=True, exist_ok=True)
    _write_geo_family_soft_metadata_only(soft_metadata)
    _write_geo_family_soft(soft_expression)
    _write_xlsx_count_matrix(xlsx)

    run_project_recognition(project_root)
    candidates = collect_standardization_candidates(project_root)
    expression_sources = {item["source_file"] for item in candidates["expression_matrix_candidates"]}  # type: ignore[index]
    by_source = {item["source_file"]: item for item in candidates["expression_matrix_candidates"]}  # type: ignore[index]

    assert "GSE6005_family.soft" not in expression_sources
    assert "GSE6004_family.soft" in expression_sources
    assert by_source["GSE6004_family.soft"]["requires_user_confirmation"] is True
    assert by_source["GSE6004_family.soft"]["source_parser"] == "geo_family_soft"
    assert "GSE236866_Processed_data_tau_with_inhibitors.xlsx" in expression_sources
    assert by_source["GSE236866_Processed_data_tau_with_inhibitors.xlsx"]["source_parser"] == "xlsx"


def test_standardization_confirmation_detects_mixed_xlsx_fpkm_and_imported_deg(project_root: Path) -> None:
    source = project_root / "raw_data" / "local_import" / "mixed.xlsx"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("placeholder", encoding="utf-8")
    recognition_path = project_root / "logs" / "recognition" / "recognition_report.json"
    recognition_path.parent.mkdir(parents=True, exist_ok=True)
    recognition_path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.recognition_report.v1",
                "files": [
                    {
                        "file_name": source.name,
                        "original_path": str(source),
                        "recognized_type": "tabular_text_file",
                        "recognized_type_zh": "RNA-seq 综合表达结果表",
                        "recognized_roles": [],
                        "detected_assets": [
                            {"asset_type": "raw_count_matrix", "label_zh": "count 矩阵", "input_eligible": True},
                            {"asset_type": "normalized_expression_matrix", "label_zh": "FPKM 矩阵", "input_eligible": True},
                            {"asset_type": "differential_result_table", "label_zh": "差异分析结果", "input_eligible": False},
                        ],
                        "route_path": str(source),
                    }
                ],
                "warnings": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    candidates = collect_standardization_candidates(project_root)
    value_types = {item["expression_value_type_candidate"] for item in candidates["expression_matrix_candidates"]}  # type: ignore[index]

    assert {"count", "FPKM"} <= value_types
    assert candidates["imported_deg_candidates"]  # type: ignore[index]
    manifest = save_standardization_confirmation(project_root)
    assert manifest["readiness"]["imported_result_ready"] is True  # type: ignore[index]


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
    assert recognition["group_preview"]["selected_preview_field"] == "group"  # type: ignore[index]


def test_group_preview_does_not_create_comparison_config(project_root: Path) -> None:
    expression = project_root / "raw_data" / "local_import" / "expression.tsv"
    sample = project_root / "raw_data" / "local_import" / "samples.tsv"
    expression.parent.mkdir(parents=True, exist_ok=True)
    expression.write_text("gene\tGSM1\tGSM2\tGSM3\tGSM4\nTP53\t1\t2\t3\t4\n", encoding="utf-8")
    sample.write_text("sample_id\tcondition\nGSM1\tcontrol\nGSM2\tcontrol\nGSM3\ttreated\nGSM4\ttreated\n", encoding="utf-8")

    recognition = run_project_recognition(project_root)
    readiness = run_project_readiness(project_root)
    diff_row = next(row for row in readiness["capability_matrix"]["rows"] if row["analysis_type"] == "differential_expression")  # type: ignore[index]

    assert recognition["group_preview"]["status"] == "preview_only"  # type: ignore[index]
    assert "comparison_config" not in readiness["readiness_report"]["available_inputs"]  # type: ignore[index]
    assert diff_row["can_run"] is False
    assert "comparison_config" in diff_row["missing_inputs"]


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
    assert readiness["standardization_ready"] is False
    assert readiness["deg_ready"] is False
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


def test_gzip_csv_expression_matrix_with_entrez_rowname_and_symbol_annotation(project_root: Path) -> None:
    source = project_root / "raw_data" / "geo" / "GSE317461" / "supplementary" / "GSE317461_Thy.8505C.cells.cpm.csv.gz"
    source.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(source, "wt", encoding="utf-8") as handle:
        handle.write('"rowname","X8505c.CUET.4.BAM","X8505c.CUET.6.BAM","X8505c.UT.1.BAM","SYMBOL"\n')
        handle.write('"653635",11.2,14.0,11.2,"WASH7P"\n')
        handle.write('"102723897",4.3,3.8,3.6,"LOC102723897"\n')
        handle.write('"79854",1.3,2.7,2.3,"LINC00115"\n')

    recognition = run_project_recognition(project_root)
    record = next(item for item in recognition["files"] if item["file_name"] == source.name)  # type: ignore[index]
    assets = _asset_by_role(record)  # type: ignore[arg-type]

    assert record["recognized_type"] == "tabular_text_file"
    assert "normalized_expression_matrix" in assets
    assert "platform_annotation" in assets
    assert record["content_profile"]["first_column_id_pattern"] == "entrez_id"  # type: ignore[index]


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
