from __future__ import annotations

import pytest

from app.shared.query_intelligence import build_search_translation_draft
from app.shared.query_intelligence.medical_terms import lookup_medical_terms


def _lookup_text(term: str, *, target_context: str = "bioinformatics") -> str:
    result = lookup_medical_terms(term, target_context=target_context)
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
            *result.outcome_terms,
            *result.study_design_terms,
            *result.publication_type_terms,
        ]
    )


@pytest.mark.parametrize(
    ("term", "required_terms", "tcga_projects", "gtex_tissues"),
    [
        ("脑胶质瘤", ["glioma"], ["TCGA-GBM", "TCGA-LGG"], ["Brain"]),
        ("肺腺癌", ["lung adenocarcinoma"], ["TCGA-LUAD"], ["Lung"]),
        ("肺鳞癌", ["lung squamous cell carcinoma"], ["TCGA-LUSC"], ["Lung"]),
        ("结直肠癌", ["colorectal cancer"], ["TCGA-COAD", "TCGA-READ"], ["Colon"]),
        ("肝细胞癌", ["hepatocellular carcinoma"], ["TCGA-LIHC"], ["Liver"]),
        ("胰腺癌", ["pancreatic cancer"], ["TCGA-PAAD"], ["Pancreas"]),
        ("乳腺癌", ["breast cancer"], ["TCGA-BRCA"], ["Breast"]),
        ("前列腺癌", ["prostate cancer"], ["TCGA-PRAD"], ["Prostate"]),
        ("黑色素瘤", ["melanoma"], ["TCGA-SKCM"], ["Skin"]),
    ],
)
def test_systematic_tumor_tcga_and_gtex_mapping(
    term: str,
    required_terms: list[str],
    tcga_projects: list[str],
    gtex_tissues: list[str],
) -> None:
    result = lookup_medical_terms(term)
    text = _lookup_text(term).lower()

    for required in required_terms:
        assert required.lower() in text
    assert set(tcga_projects) <= set(result.tcga_project_candidates)
    assert set(gtex_tissues) <= set(result.gtex_tissue_candidates)


@pytest.mark.parametrize(
    ("term", "required_terms"),
    [
        ("2型糖尿病", ["type 2 diabetes", "Diabetes Mellitus"]),
        ("肥胖", ["Obesity", "BMI"]),
        ("高血压", ["Hypertension"]),
        ("脂肪肝", ["Fatty Liver Disease", "NAFLD"]),
        ("阿尔茨海默病", ["Alzheimer Disease"]),
        ("类风湿关节炎", ["Rheumatoid Arthritis"]),
    ],
)
def test_systematic_common_non_tumor_mapping(term: str, required_terms: list[str]) -> None:
    text = _lookup_text(term, target_context="meta_analysis").lower()

    for required in required_terms:
        assert required.lower() in text


@pytest.mark.parametrize(
    ("term", "required_term"),
    [
        ("空间转录组", "spatial transcriptomics"),
        ("甲基化", "methylation profiling"),
        ("ATAC测序", "ATAC-seq"),
        ("蛋白质组", "proteomics"),
    ],
)
def test_systematic_data_modality_mapping(term: str, required_term: str) -> None:
    result = lookup_medical_terms(term)

    assert required_term.lower() in " ".join(result.data_modality_terms).lower()


@pytest.mark.parametrize(
    ("term", "required_term", "required_abbreviation"),
    [
        ("总生存", "overall survival", "OS"),
        ("无进展生存", "progression-free survival", "PFS"),
        ("风险比", "hazard ratio", "HR"),
        ("敏感性", "sensitivity", ""),
        ("特异性", "specificity", ""),
    ],
)
def test_systematic_meta_outcome_mapping(
    term: str,
    required_term: str,
    required_abbreviation: str,
) -> None:
    result = lookup_medical_terms(term, target_context="meta_analysis")
    text = " ".join([*result.outcome_terms, *result.abbreviations])

    assert required_term in text
    if required_abbreviation:
        assert required_abbreviation in result.abbreviations


def test_systematic_study_design_and_publication_filter_terms() -> None:
    rct = lookup_medical_terms("随机对照试验", target_context="meta_analysis")
    review = lookup_medical_terms("会议摘要", target_context="meta_analysis")

    assert "randomized controlled trial" in " ".join(rct.study_design_terms)
    assert "RCT" in rct.abbreviations
    assert "conference abstract" in " ".join(review.publication_type_terms)


def test_context_filters_keep_bioinformatics_and_meta_outputs_separate() -> None:
    bio = build_search_translation_draft(
        "肺腺癌转录组",
        target_context="bioinformatics",
        target_database="geo",
    )
    meta = build_search_translation_draft(
        "肺腺癌总生存 Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert bio.pubmed_query_candidates == []
    assert bio.geo_query_candidates
    assert "TCGA-LUAD" in bio.audit.get("tcga_project_candidates", [])
    assert meta.geo_query_candidates == []
    assert not meta.audit.get("tcga_project_candidates")
    assert not meta.audit.get("gtex_tissue_candidates")
    assert "tcga" not in " ".join(meta.database_terms).lower()
    assert "gtex" not in " ".join(meta.database_terms).lower()
    assert "geo" not in " ".join(meta.database_terms).lower()


@pytest.mark.parametrize(
    ("term", "forbidden_terms"),
    [
        ("食管鳞癌", ["thyroid", "PTC"]),
        ("甲状腺癌", ["ESCC", "esophageal"]),
        ("胶质瘤", ["thyroid", "ESCC", "esophageal"]),
    ],
)
def test_systematic_forbidden_disease_leakage_guards(term: str, forbidden_terms: list[str]) -> None:
    text = _lookup_text(term)

    for forbidden in forbidden_terms:
        assert forbidden.lower() not in text.lower()
