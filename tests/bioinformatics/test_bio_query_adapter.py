from __future__ import annotations

from app.bioinformatics.retrieval import build_bioinformatics_query_strategy


def test_disease_aware_geo_queries_start_with_disease_terms() -> None:
    strategy = build_bioinformatics_query_strategy("脑胶质瘤")

    assert "glioma" in strategy.disease_terms
    assert strategy.confirmed_geo_queries
    assert all(any(term.lower().strip('"') in query.lower() for term in strategy.disease_terms[:3]) for query in strategy.confirmed_geo_queries[:4])
    assert strategy.broad_query_guard_triggered is False
    assert {item.project_id for item in strategy.tcga_project_candidates} >= {"TCGA-GBM", "TCGA-LGG"}
    assert [item.tissue for item in strategy.gtex_tissue_candidates] == ["Brain"]


def test_escc_strategy_does_not_leak_thyroid_or_pubmed_terms() -> None:
    strategy = build_bioinformatics_query_strategy("食管鳞癌")
    text = " ".join([*strategy.disease_terms, *strategy.confirmed_geo_queries])

    assert "esophageal squamous cell carcinoma" in text
    assert "thyroid" not in text.lower()
    assert "PTC" not in text
    assert strategy.translation_draft.pubmed_query_candidates == []


def test_luad_and_hcc_tcga_candidates_are_specific() -> None:
    luad = build_bioinformatics_query_strategy("肺腺癌")
    hcc = build_bioinformatics_query_strategy("肝细胞癌")

    assert [item.project_id for item in luad.tcga_project_candidates] == ["TCGA-LUAD"]
    assert [item.project_id for item in hcc.tcga_project_candidates] == ["TCGA-LIHC"]
    assert "TCGA" not in [item.project_id for item in luad.tcga_project_candidates]


def test_broad_query_guard_blocks_platform_only_query() -> None:
    strategy = build_bioinformatics_query_strategy("表达谱")

    assert strategy.disease_terms == ()
    assert strategy.confirmed_geo_queries == ()
    assert strategy.supplemental_geo_queries
    assert strategy.broad_query_guard_triggered is True
    assert strategy.broad_query_requires_confirmation is True
