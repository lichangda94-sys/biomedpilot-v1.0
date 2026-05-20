from __future__ import annotations

from app.shared.query_intelligence.medical_terms import find_terms, load_terms, resolve_legacy_concept_id
from app.shared.query_intelligence.meta_seed_terms import match_chinese_question_to_pico


def test_meta_scope_resolves_legacy_shared_concepts_to_migrated_meta_terms() -> None:
    assert resolve_legacy_concept_id("mini:meta_outcomes_core", "meta_analysis").resolved_concept_id == "meta_outcome:overall_survival"
    assert (
        resolve_legacy_concept_id("mini:meta_analysis_overall_survival", "meta_analysis").resolved_concept_id
        == "meta_outcome:overall_survival"
    )
    assert (
        resolve_legacy_concept_id("mini:study_design_core", "meta_analysis").resolved_concept_id
        == "meta_study_design:randomized_controlled_trial"
    )
    assert (
        resolve_legacy_concept_id("mini:meta_analysis_quadas_2", "meta_analysis").resolved_concept_id
        == "meta_quality_tool:quadas_2"
    )


def test_bioinformatics_scope_does_not_activate_migrated_meta_legacy_terms() -> None:
    legacy_ids = [
        "mini:meta_outcomes_core",
        "mini:meta_analysis_overall_survival",
        "mini:study_design_core",
        "mini:meta_analysis_quadas_2",
    ]

    for legacy_id in legacy_ids:
        resolution = resolve_legacy_concept_id(legacy_id, "bioinformatics")
        assert resolution is not None
        assert resolution.active is False
        assert resolution.resolved_concept_id == ""

    bio_terms = load_terms("bioinformatics")
    bio_ids = {term.concept_id for term in bio_terms}
    assert not set(legacy_ids) & bio_ids
    assert not any(term.source == "meta_migrated_from_shared_terms" for term in bio_terms)


def test_scope_find_terms_prefers_meta_migrated_terms_only_in_meta_scope() -> None:
    meta_overall = find_terms("overall survival", "meta_analysis")
    bio_overall = find_terms("overall survival", "bioinformatics")
    meta_hazard = find_terms("hazard ratio", "meta_analysis")
    bio_hazard = find_terms("hazard ratio", "bioinformatics")
    meta_rct = find_terms("randomized controlled trial", "meta_analysis")
    bio_rct = find_terms("randomized controlled trial", "bioinformatics")
    meta_quadas = find_terms("QUADAS-2", "meta_analysis")
    bio_quadas = find_terms("QUADAS-2", "bioinformatics")

    assert {term.concept_id for term in meta_overall} == {"meta_outcome:overall_survival"}
    assert not bio_overall
    assert {term.concept_id for term in meta_hazard} == {"meta_effect:hazard_ratio"}
    assert not bio_hazard
    assert {term.concept_id for term in meta_rct} == {"meta_study_design:randomized_controlled_trial"}
    assert not bio_rct
    assert {term.concept_id for term in meta_quadas} == {"meta_quality_tool:quadas_2"}
    assert not bio_quadas


def test_survival_data_and_gene_expression_scope_routing() -> None:
    meta_survival_data = find_terms("survival data", "meta_analysis")
    meta_overall = find_terms("overall survival", "meta_analysis")

    assert {term.concept_id for term in meta_survival_data} == {"meta_data_context:survival_data"}
    assert meta_survival_data[0].usage["query_expansion_allowed"] is False
    assert "survival data" not in {term.lower() for term in meta_overall[0].terms}
    assert not find_terms("gene expression profiling", "meta_analysis")
    assert find_terms("gene expression profiling", "bioinformatics")


def test_bioinformatics_scope_keeps_geo_gtex_expression_terms() -> None:
    bio_terms = load_terms("bioinformatics")
    all_terms = {value.lower() for term in bio_terms for value in (term.preferred_label_en, *term.terms)}

    assert {"tpm", "fpkm", "raw counts", "count matrix"} <= all_terms
    assert {"muscle - skeletal", "nerve - tibial", "skin", "heart", "artery"} <= all_terms
    assert {"platform annotation", "gpl annotation", "series", "sample", "dataset"} <= all_terms


def test_meta_seed_matcher_does_not_treat_bioinformatics_terms_as_pico() -> None:
    bio_text = "GSE GSM GPL TPM FPKM raw counts probe ID series matrix sample metadata TCGA barcode GTEx tissue"
    draft = match_chinese_question_to_pico(bio_text)

    assert draft.concept_ids() == []
