from __future__ import annotations

import json

from app.meta_analysis.project_workspace import create_meta_analysis_project
from app.meta_analysis.search_config_draft import (
    build_meta_seed_search_config_draft,
    save_meta_seed_search_config_draft,
)


def test_meta_seed_search_config_draft_handles_four_chinese_examples() -> None:
    cases = {
        "糖尿病前期与甲状腺癌风险的关系": {
            "intent": "exposure_disease_risk_meta",
            "concepts": {"meta_disease:thyroid_cancer", "meta_exposure:prediabetes"},
            "query_terms": {"Thyroid Neoplasms", "Prediabetic State"},
        },
        "二甲双胍治疗2型糖尿病的疗效": {
            "intent": "treatment_effect_meta",
            "concepts": {
                "meta_disease:type_2_diabetes_mellitus",
                "meta_intervention:metformin",
                "meta_research_intent:efficacy",
            },
            "query_terms": {"Diabetes Mellitus, Type 2", "metformin"},
        },
        "放射性碘治疗甲状腺癌复发的影响": {
            "intent": "association_meta",
            "concepts": {
                "meta_disease:thyroid_cancer",
                "meta_intervention:radioactive_iodine_therapy",
                "meta_outcome:recurrence",
            },
            "query_terms": {"Thyroid Neoplasms", "Radioisotopes", "Recurrence"},
        },
        "肥胖与乳腺癌风险的Meta分析": {
            "intent": "exposure_disease_risk_meta",
            "concepts": {
                "meta_disease:breast_cancer",
                "meta_exposure:obesity",
                "meta_research_intent:risk",
                "meta_study_design:meta_analysis",
            },
            "query_terms": {"Breast Neoplasms", "Obesity"},
        },
    }

    for question, expected in cases.items():
        draft = build_meta_seed_search_config_draft(question)
        concept_ids = {concept.concept_id for concept in draft.detected_concepts}
        query = draft.pubmed_query_draft

        assert draft.detected_intent == expected["intent"]
        assert expected["concepts"] <= concept_ids
        assert draft.draft_status == "draft_needs_user_confirmation"
        assert draft.user_confirmation_required is True
        assert draft.search_execution_status == "not_executed"
        assert draft.online_retrieval_executed is False
        assert draft.formal_search_completed is False
        assert "no_online_pubmed_embase_wos_retrieval" in draft.unsupported_features
        for term in expected["query_terms"]:
            assert term in query


def test_meta_seed_search_config_query_guards_are_visible_and_enforced() -> None:
    draft = build_meta_seed_search_config_draft("肥胖与乳腺癌风险的Meta分析，报告HR和95%CI")
    guards = {guard.concept_id: guard for guard in draft.detected_concepts}

    assert guards["meta_disease:breast_cancer"].included_in_pubmed_topic_query is True
    assert guards["meta_exposure:obesity"].included_in_pubmed_topic_query is True
    assert guards["meta_research_intent:risk"].query_expansion_allowed is False
    assert guards["meta_research_intent:risk"].included_in_pubmed_topic_query is False
    assert guards["meta_effect:hazard_ratio"].pdf_extraction_target is True
    assert guards["meta_effect:hazard_ratio"].included_in_pubmed_topic_query is False
    assert guards["meta_study_design:meta_analysis"].filter_only is True
    assert guards["meta_study_design:meta_analysis"].included_in_pubmed_topic_query is False
    assert "hazard ratio" not in draft.pubmed_query_draft.lower()
    assert "risk factor" not in draft.pubmed_query_draft.lower()
    assert "meta-analysis" not in draft.pubmed_query_draft.lower()


def test_meta_seed_search_config_outcome_guard_requires_population_pairing() -> None:
    paired = build_meta_seed_search_config_draft("放射性碘治疗甲状腺癌复发的影响")
    paired_guards = {guard.concept_id: guard for guard in paired.detected_concepts}
    recurrence = paired_guards["meta_outcome:recurrence"]

    assert recurrence.query_expansion_allowed == "conditional"
    assert "population_or_disease" in recurrence.requires_pairing_with
    assert recurrence.included_in_pubmed_topic_query is True
    assert "Recurrence" in paired.pubmed_query_draft

    unpaired = build_meta_seed_search_config_draft("复发风险Meta分析")
    unpaired_guards = {guard.concept_id: guard for guard in unpaired.detected_concepts}

    assert unpaired_guards["meta_outcome:recurrence"].included_in_pubmed_topic_query is False
    assert "Recurrence" not in unpaired.pubmed_query_draft
    assert any("Outcome terms were detected without a disease/population pair" in item for item in unpaired.warnings)


def test_meta_seed_search_config_save_stays_draft_only(tmp_path) -> None:
    project = create_meta_analysis_project("Seed Config Draft", tmp_path)
    draft = build_meta_seed_search_config_draft("二甲双胍治疗2型糖尿病的疗效")

    draft_path = save_meta_seed_search_config_draft(project.project_root, draft)
    payload = json.loads(draft_path.read_text(encoding="utf-8"))
    config = json.loads((project.project_root / "meta_project_config.json").read_text(encoding="utf-8"))

    assert draft_path.name == "meta_seed_search_config_draft.json"
    assert draft_path.parent.name == "search_strategy"
    assert payload["search_execution_status"] == "not_executed"
    assert payload["online_retrieval_executed"] is False
    assert payload["formal_search_completed"] is False
    assert payload["unsupported_features"] == [
        "no_online_pubmed_embase_wos_retrieval",
        "no_chinese_database_search",
        "no_chinese_pdf_extraction",
        "no_english_pdf_extraction_ui",
        "no_final_extraction_table_write",
    ]
    assert config["search_config_draft"]["search_execution_status"] == "not_executed"
    assert config["search_config_draft"]["formal_search_completed"] is False
