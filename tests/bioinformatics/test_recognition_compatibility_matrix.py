from __future__ import annotations

from pathlib import Path

import pytest

from app.bioinformatics.project_analysis_tasks import load_analysis_task_center
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_standardization import generate_standardized_assets
from app.bioinformatics.results.project_results import build_imported_deg_view


POLLUTING_COLUMNS = {
    "gene_start",
    "gene_end",
    "gene_length",
    "gene_chr",
    "gene_strand",
    "gene_biotype",
    "gene_description",
    "log2FoldChange",
    "pvalue",
    "padj",
    "adj.P.Val",
    "P.Value",
}


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    from app.bioinformatics.project_workspace import create_bioinformatics_project

    return create_bioinformatics_project("Recognition Compatibility Matrix", tmp_path).project_root


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _raw(project_root: Path, name: str) -> Path:
    return project_root / "raw_data" / "local_import" / name


def _record(project_root: Path, name: str) -> dict[str, object]:
    report = run_project_recognition(project_root)
    return next(item for item in report["files"] if item["file_name"] == name)  # type: ignore[index]


def _blocks(record: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(block.get("block_type")): block for block in record.get("content_blocks", []) if isinstance(block, dict)}


def _sample_columns(record: dict[str, object]) -> set[str]:
    profile = record.get("content_profile")
    return set(profile.get("sample_columns", []) if isinstance(profile, dict) else [])


def _assert_no_sample_column_pollution(record: dict[str, object]) -> None:
    columns = _sample_columns(record)
    assert not (columns & POLLUTING_COLUMNS)
    assert not any(column.endswith(("_log2FoldChange", "_pvalue", "_padj")) for column in columns)


def _assets_by_type(project_root: Path) -> dict[str, list[dict[str, object]]]:
    standardization = generate_standardized_assets(project_root)
    assets = [asset for asset in standardization["registry"]["assets"] if isinstance(asset, dict)]  # type: ignore[index]
    result: dict[str, list[dict[str, object]]] = {}
    for asset in assets:
        result.setdefault(str(asset.get("asset_type")), []).append(asset)
    return result


def test_integrated_rnaseq_result_table_matrix(project_root: Path) -> None:
    path = _raw(project_root, "integrated_rnaseq_results.csv")
    _write(
        path,
        "gene_id,A1_count,A2_count,B1_count,B2_count,A1_fpkm,A2_fpkm,B1_fpkm,B2_fpkm,"
        "PFFvsPBS_log2FoldChange,PFFvsPBS_pvalue,PFFvsPBS_padj,gene_name,gene_start,gene_end,gene_biotype,gene_description\n"
        "ENSMUSG00000026193,10,12,20,22,1.1,1.2,2.1,2.2,1.5,0.01,0.04,Sox17,4490931,4497354,protein_coding,SRY-box transcription factor 17\n"
        "ENSMUSG00000064351,30,31,18,17,3.1,3.2,1.8,1.7,-1.6,0.02,0.03,mt-Nd1,2751,3707,protein_coding,mitochondrially encoded NADH\n",
    )

    record = _record(project_root, path.name)
    blocks = _blocks(record)

    assert record["semantic_type"] == "rna_seq_integrated_result_table"
    assert record["species"] == "Mus musculus"
    assert record["gene_id_type"] == "ensembl_mouse_gene_id"
    assert {"gene_identifier", "count_expression_matrix", "fpkm_expression_matrix", "deg_comparisons", "gene_annotation"} <= set(blocks)
    assert blocks["count_expression_matrix"]["value_type"] == "count"
    assert blocks["fpkm_expression_matrix"]["value_type"] == "fpkm"
    assert blocks["deg_comparisons"]["comparison_count"] == 1
    assert "gene_biotype" in blocks["gene_annotation"]["annotation_fields"]
    _assert_no_sample_column_pollution(record)


def test_pure_count_matrix_with_count_suffix_is_count_asset(project_root: Path) -> None:
    path = _raw(project_root, "count_matrix.csv")
    _write(
        path,
        "gene_id,A1_count,A2_count,B1_count,B2_count\n"
        "ENSG00000141510,10,11,20,21\n"
        "ENSG00000146648,30,29,18,17\n",
    )

    record = _record(project_root, path.name)
    blocks = _blocks(record)

    assert record["recognized_type"] in {"raw_count_matrix", "tabular_text_file"}
    assert record["species"] == "Homo sapiens"
    assert record["gene_id_type"] == "ensembl_human_gene_id"
    assert blocks["count_expression_matrix"]["value_type"] == "count"
    assert set(blocks["count_expression_matrix"]["sample_columns"]) == {"A1_count", "A2_count", "B1_count", "B2_count"}
    assets = _assets_by_type(project_root)
    assert assets["count_matrix"][0]["value_type"] == "count"
    center = load_analysis_task_center(project_root)
    capabilities = {item["task_id"]: item for item in center["capabilities"]}  # type: ignore[index]
    assert capabilities["differential_expression_recompute"]["status"] == "ready_with_group_confirmation"


def test_normalized_fpkm_and_tpm_matrix_assets(project_root: Path) -> None:
    path = _raw(project_root, "normalized_expression.csv")
    _write(
        path,
        "gene_id,A1_fpkm,A2_fpkm,B1_tpm,B2_tpm\n"
        "ENSG00000141510,1.1,1.2,3.1,3.2\n"
        "ENSG00000146648,2.1,2.2,4.1,4.2\n",
    )

    record = _record(project_root, path.name)
    blocks = _blocks(record)

    assert blocks["fpkm_expression_matrix"]["value_type"] == "fpkm"
    assert blocks["tpm_expression_matrix"]["value_type"] == "tpm"
    assert record["species"] == "Homo sapiens"
    assets = _assets_by_type(project_root)
    value_types = {asset.get("value_type") for asset in assets["normalized_expression_matrix"]}
    assert {"fpkm", "tpm"} <= value_types
    assert all("DESeq2/edgeR" in " ".join(asset.get("limitations", [])) for asset in assets["normalized_expression_matrix"])


def test_single_comparison_deg_result_table_is_imported_deg_asset(project_root: Path) -> None:
    path = _raw(project_root, "single_deg_results.csv")
    _write(
        path,
        "gene_id,gene_name,log2FoldChange,pvalue,padj,gene_biotype,gene_description\n"
        "ENSMUSG00000026193,Sox17,1.5,0.01,0.04,protein_coding,SRY-box transcription factor 17\n"
        "ENSMUSG00000064351,mt-Nd1,-1.7,0.02,0.03,protein_coding,mitochondrially encoded NADH\n",
    )

    record = _record(project_root, path.name)
    blocks = _blocks(record)

    assert record["recognized_type"] == "differential_result_table"
    assert blocks["deg_comparisons"]["comparison_count"] == 1
    assert blocks["deg_comparisons"]["comparisons"][0]["comparison_name"] == "imported_deg_results"
    _assert_no_sample_column_pollution(record)
    assets = _assets_by_type(project_root)
    assert assets["deg_result_table"][0]["source_origin"] == "imported_deg_result"
    view = build_imported_deg_view(project_root, comparison_name="imported_deg_results")
    assert view["source"] == "imported_deg_result"
    assert view["enrichment_species"] == "mouse"


def test_multi_comparison_wide_deg_table_tracks_incomplete_comparisons(project_root: Path) -> None:
    path = _raw(project_root, "wide_deg_results.csv")
    _write(
        path,
        "gene_id,A_vs_B_log2FoldChange,A_vs_B_pvalue,A_vs_B_padj,C_vs_D_log2FoldChange,C_vs_D_pvalue,C_vs_D_padj,E_vs_F_log2FoldChange,E_vs_F_pvalue\n"
        "ENSMUSG00000026193,1.5,0.01,0.04,-1.2,0.02,0.03,2.0,0.01\n"
        "ENSMUSG00000064351,-1.7,0.02,0.03,1.4,0.01,0.02,-2.1,0.02\n",
    )

    record = _record(project_root, path.name)
    comparisons = _blocks(record)["deg_comparisons"]["comparisons"]

    assert _blocks(record)["deg_comparisons"]["comparison_count"] == 3
    assert _blocks(record)["deg_comparisons"]["complete_comparison_count"] == 2
    by_name = {comparison["comparison_name"]: comparison for comparison in comparisons}
    assert by_name["A_vs_B"]["is_complete"] is True
    assert by_name["E_vs_F"]["is_complete"] is False
    _assert_no_sample_column_pollution(record)


def test_gene_annotation_table_is_annotation_asset(project_root: Path) -> None:
    path = _raw(project_root, "gene_annotation.csv")
    _write(
        path,
        "gene_id,gene_name,gene_chr,gene_start,gene_end,gene_strand,gene_length,gene_biotype,gene_description\n"
        "ENSMUSG00000026193,Sox17,chr1,4490931,4497354,+,6424,protein_coding,SRY-box transcription factor 17\n"
        "ENSMUSG00000064351,mt-Nd1,chrM,2751,3707,+,957,protein_coding,mitochondrially encoded NADH\n",
    )

    record = _record(project_root, path.name)

    assert record["recognized_type"] == "gene_annotation"
    assert _blocks(record)["gene_annotation"]["annotation_fields"]
    _assert_no_sample_column_pollution(record)
    assets = _assets_by_type(project_root)
    assert "gene_annotation" in assets
    assert "gene_identifier_metadata" in assets


def test_sample_metadata_table_is_not_expression_matrix(project_root: Path) -> None:
    path = _raw(project_root, "sample_metadata.csv")
    _write(
        path,
        "sample_id,group,condition,batch,sex,age\n"
        "A1,A,treated,batch1,F,10\n"
        "B1,B,control,batch1,M,11\n",
    )

    record = _record(project_root, path.name)

    assert record["recognized_type"] == "sample_metadata"
    assert "sample_metadata" in record["recognized_roles"]
    assert not any(role in record["recognized_roles"] for role in ("expression_matrix", "raw_count_matrix", "normalized_expression_matrix"))


def test_comparison_config_table_is_not_expression_matrix(project_root: Path) -> None:
    path = _raw(project_root, "comparison_config.tsv")
    _write(
        path,
        "comparison_name\tcase_group\tcontrol_group\tmethod\n"
        "A_vs_B\tA\tB\tDESeq2\n",
    )

    record = _record(project_root, path.name)

    assert record["recognized_type"] == "comparison_config"
    assert "expression_matrix" not in record["recognized_roles"]


def test_geo_series_matrix_uses_geo_organism_and_keeps_blocks_separate(project_root: Path) -> None:
    path = _raw(project_root, "GSETEST_series_matrix.txt")
    _write(
        path,
        "\n".join(
            [
                "!Series_title = Mouse expression profile",
                "!Series_geo_accession = GSETEST",
                "!Series_platform_id = GPLTEST",
                "!Sample_title = treated 1",
                "!Sample_title = control 1",
                "!Sample_geo_accession = GSM1",
                "!Sample_geo_accession = GSM2",
                "!Sample_organism_ch1 = Mus musculus",
                "!Sample_characteristics_ch1 = condition: treated",
                "!Sample_characteristics_ch1 = condition: control",
                "!series_matrix_table_begin",
                '"ID_REF"\t"GSM1"\t"GSM2"',
                '"1007_s_at"\t8.1\t6.2',
                '"1053_at"\t4.4\t5.0',
                "!series_matrix_table_end",
                "",
            ]
        ),
    )

    record = _record(project_root, path.name)

    assert record["recognized_type"] == "geo_series_matrix_container"
    assert {"expression_matrix", "sample_metadata"} <= set(record["recognized_roles"])
    assert record["species"] == "Mus musculus"
    assert record["species_group"] == "mouse"
    assert record.get("species") != "Homo sapiens"


def test_unknown_table_does_not_generate_analysis_ready_asset(project_root: Path) -> None:
    path = _raw(project_root, "unknown_table.csv")
    _write(
        path,
        "id,value,note\n"
        "row1,1,alpha\n"
        "row2,2,beta\n",
    )

    report = run_project_recognition(project_root)
    record = next(item for item in report["files"] if item["file_name"] == path.name)  # type: ignore[index]

    assert record["recognized_type"] == "unknown"
    assert record["recognized_roles"] == []
    assert any("未检测到明确的基因表达、差异分析或样本注释结构" in warning for warning in report["warnings"])  # type: ignore[index]
    standardization = generate_standardized_assets(project_root)
    assert standardization["registry"]["assets"] == []  # type: ignore[index]
