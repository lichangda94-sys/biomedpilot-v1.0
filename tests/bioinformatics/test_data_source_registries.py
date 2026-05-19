from __future__ import annotations

from app.bioinformatics.gtex_tissue_registry import get_gtex_tissue, get_gtex_use_purpose, grouped_gtex_tissues, list_gtex_tissues
from app.bioinformatics.tcga_project_registry import get_tcga_analysis_purpose, get_tcga_project, grouped_tcga_projects, list_tcga_projects


def test_tcga_registry_contains_primary_33_projects() -> None:
    projects = list_tcga_projects()

    assert len(projects) == 33
    assert get_tcga_project("TCGA-THCA").chinese_name == "甲状腺癌"
    assert get_tcga_project("TCGA-THCA").project_id == "TCGA-THCA"
    assert get_tcga_project("TCGA-LIHC").chinese_name == "肝细胞癌"
    assert get_tcga_project("TCGA-BRCA").chinese_name == "乳腺浸润癌"
    assert get_tcga_project("TCGA-LUAD").chinese_name == "肺腺癌"
    assert "内分泌/神经内分泌" in grouped_tcga_projects()


def test_tcga_analysis_purpose_maps_expected_assets() -> None:
    deg = get_tcga_analysis_purpose("differential_expression")
    clinical = get_tcga_analysis_purpose("expression_clinical")

    assert deg.chinese_name == "表达差异分析"
    assert deg.required_internal_assets == ("rna_seq_expression", "sample_metadata")
    assert "clinical_metadata" in clinical.required_internal_assets


def test_gtex_registry_contains_key_v8_tissues() -> None:
    tissues = list_gtex_tissues()
    names = {tissue.tissue_site_detail for tissue in tissues}

    assert "Thyroid" in names
    assert "Liver" in names
    assert "Lung" in names
    assert "Whole Blood" in names
    assert "Breast - Mammary Tissue" in names
    assert get_gtex_tissue("gtex_thyroid").chinese_name == "甲状腺"
    assert get_gtex_tissue("gtex_thyroid").version == "GTEx V8"
    assert "内分泌系统" in grouped_gtex_tissues()


def test_gtex_use_purpose_maps_expected_assets_and_boundary() -> None:
    reference = get_gtex_use_purpose("external_reference")

    assert reference.chinese_name == "作为外部参考数据"
    assert reference.required_internal_assets == ("gene_expression", "sample_annotation")
    assert reference.readiness_profile == "external_reference_not_tcga_control"
