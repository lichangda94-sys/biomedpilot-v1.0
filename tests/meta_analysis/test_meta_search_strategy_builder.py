from __future__ import annotations

from app.meta_analysis.search import MetaConceptGroupDraft, build_meta_search_strategy_draft
from app.meta_analysis.search.pubmed_query_builder import build_pubmed_query_draft


def test_meta_search_strategy_uses_shared_vocabulary_as_peco_concept_blocks() -> None:
    draft = build_meta_search_strategy_draft("肥胖与甲状腺癌发病风险 Meta 分析")

    assert draft.target_context == "meta_analysis"
    assert draft.review_framework == "PECO"
    assert draft.review_or_analysis_intent == "exposure_disease_risk_meta"
    assert draft.population.slot == "population"
    assert draft.intervention_or_exposure.label == "Exposure"
    assert "obesity" in " ".join(draft.intervention_or_exposure.terms_en).lower()
    assert "thyroid cancer" in " ".join(draft.outcome.terms_en).lower()
    assert draft.audit["shared_target_context"] == "meta_analysis"
    assert draft.audit["search_execution"] == "not_implemented_draft_only"


def test_pubmed_query_draft_supports_mesh_and_tiab_blocks() -> None:
    draft = build_meta_search_strategy_draft("肥胖与甲状腺癌发病风险 Meta 分析")

    assert '"Obesity"[Mesh]' in draft.pubmed_query_draft
    assert '"obesity"[tiab]' in draft.pubmed_query_draft
    assert '"Thyroid Neoplasms"[Mesh]' in draft.pubmed_query_draft
    assert '"thyroid cancer"[tiab]' in draft.pubmed_query_draft
    assert " AND " in draft.pubmed_query_draft


def test_pubmed_query_builder_combines_non_empty_concept_groups() -> None:
    query = build_pubmed_query_draft(
        (
            MetaConceptGroupDraft(
                slot="population",
                label="Population",
                terms_en=("thyroid cancer",),
                mesh_terms=("Thyroid Neoplasms",),
            ),
            MetaConceptGroupDraft(slot="comparator", label="Comparator"),
        )
    )

    assert query == '("Thyroid Neoplasms"[Mesh] OR "thyroid cancer"[tiab])'


def test_meta_search_strategy_has_wos_embase_cnki_placeholders() -> None:
    draft = build_meta_search_strategy_draft("肥胖与甲状腺癌发病风险 Meta 分析")

    assert draft.web_of_science_query_draft.startswith("TS=")
    assert ":ti,ab" in draft.embase_query_draft
    assert "主题=" in draft.cnki_query_draft
    assert {item.database for item in draft.query_drafts} == {"pubmed", "web_of_science", "embase", "cnki"}
    assert all(item.status == "draft_only" for item in draft.query_drafts)


def test_meta_context_does_not_output_dataset_source_terms() -> None:
    draft = build_meta_search_strategy_draft("甲状腺癌 Meta 分析")
    rendered = " ".join(
        [
            *(group_term for group in draft.concept_groups for group_term in group.all_terms),
            *(query.query for query in draft.query_drafts),
            *(str(value) for value in draft.audit.values()),
        ]
    ).lower()

    assert "geo" not in rendered
    assert "gse" not in rendered
    assert "tcga" not in rendered
    assert "gtex" not in rendered
