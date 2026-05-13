from __future__ import annotations

from app.shared.query_intelligence import build_search_translation_draft
from app.shared.query_intelligence.medical_terms import lookup_medical_terms


def _lookup_text(term: str) -> str:
    result = lookup_medical_terms(term)
    return " ".join(
        [
            *result.disease_terms_en,
            *result.synonyms_en,
            *result.abbreviations,
            *result.mesh_terms,
            *result.tissue_terms,
            *result.tcga_project_candidates,
            *result.gtex_tissue_candidates,
            *result.data_modality_terms,
        ]
    )


def test_glioma_coverage_maps_tcga_and_gtex_brain() -> None:
    result = lookup_medical_terms("脑胶质瘤")
    text = _lookup_text("脑胶质瘤").lower()

    assert "glioma" in text
    assert "glioblastoma" in text
    assert {"TCGA-GBM", "TCGA-LGG"} <= set(result.tcga_project_candidates)
    assert "Brain" in result.gtex_tissue_candidates


def test_escc_coverage_does_not_leak_thyroid_terms() -> None:
    text = _lookup_text("食管鳞癌")

    assert "esophageal squamous cell carcinoma" in text
    assert "ESCC" in text
    assert "thyroid" not in text.lower()
    assert "PTC" not in text


def test_papillary_thyroid_coverage_does_not_leak_escc_terms() -> None:
    result = lookup_medical_terms("乳头状甲状腺癌")
    text = _lookup_text("乳头状甲状腺癌")

    assert "papillary thyroid carcinoma" in text
    assert "PTC" in result.abbreviations
    assert "TCGA-THCA" in result.tcga_project_candidates
    assert "ESCC" not in text
    assert "esophageal" not in text.lower()


def test_luad_and_hcc_priority_acceptance_terms() -> None:
    luad = lookup_medical_terms("肺腺癌")
    hcc = lookup_medical_terms("肝细胞癌")

    assert "lung adenocarcinoma" in " ".join(luad.disease_terms_en)
    assert "LUAD" in luad.abbreviations
    assert "TCGA-LUAD" in luad.tcga_project_candidates
    assert "hepatocellular carcinoma" in " ".join(hcc.disease_terms_en)
    assert "HCC" in hcc.abbreviations
    assert "TCGA-LIHC" in hcc.tcga_project_candidates


def test_diabetes_and_obesity_meta_terms_are_available() -> None:
    diabetes = lookup_medical_terms("糖尿病", target_context="meta_analysis")
    obesity = lookup_medical_terms("肥胖", target_context="meta_analysis")
    diabetes_text = " ".join([*diabetes.disease_terms_en, *diabetes.synonyms_en, *diabetes.mesh_terms])
    obesity_text = " ".join([*obesity.disease_terms_en, *obesity.synonyms_en, *obesity.mesh_terms, *obesity.exposure_terms])

    assert "Diabetes Mellitus" in diabetes_text
    assert "diabetes" in diabetes_text.lower()
    assert "diabetic" in diabetes_text.lower()
    assert "Obesity" in obesity_text
    assert "BMI" in obesity_text
    assert "body mass index" in obesity_text.lower()


def test_fatty_liver_mini_vocabulary_terms_are_available() -> None:
    result = lookup_medical_terms("脂肪肝", target_context="meta_analysis")
    text = " ".join([*result.disease_terms_en, *result.synonyms_en, *result.abbreviations, *result.mesh_terms])

    assert "Fatty Liver Disease" in text
    assert "hepatic steatosis" in text
    assert "NAFLD" in result.abbreviations
    assert "Fatty Liver" in result.mesh_terms
    assert result.tcga_project_candidates == []
    assert result.gtex_tissue_candidates == []


def test_data_type_terms_enter_search_translation_draft() -> None:
    draft = build_search_translation_draft("肺腺癌单细胞甲基化蛋白质组circRNA空间转录组")

    assert "single-cell RNA-seq" in draft.data_type_terms_en
    assert "DNA methylation" in draft.data_type_terms_en
    assert "proteomics" in draft.data_type_terms_en
    assert "circRNA" in draft.data_type_terms_en
    assert "spatial transcriptomics" in draft.data_type_terms_en


def test_meta_outcome_terms_enter_search_translation_draft() -> None:
    draft = build_search_translation_draft(
        "肝细胞癌总生存无进展生存诊断准确性敏感性特异性 Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )
    text = " ".join(
        [
            *draft.outcome_terms_en,
            *draft.diagnostic_accuracy_terms,
            *draft.mesh_terms,
            *draft.pubmed_query_candidates,
        ]
    )

    assert "overall survival" in text
    assert "progression-free survival" in text
    assert "diagnostic accuracy" in text
    assert "sensitivity" in text
    assert "specificity" in text
    assert "TCGA-LIHC" not in text
    assert draft.geo_query_candidates == []
