from __future__ import annotations

import json

import pytest

from app.meta_analysis.project_workspace import create_meta_analysis_project
from app.meta_analysis.search_config_draft import (
    build_confirmed_search_plan,
    build_meta_seed_search_config_draft,
    build_user_edited_search_plan,
    reject_meta_seed_search_config_draft,
    save_confirmed_search_plan,
    save_meta_seed_search_config_draft,
    save_rejected_search_config_draft,
)
from app.meta_analysis.search_execution_preflight import (
    build_pubmed_search_execution_plan,
    save_pubmed_search_execution_plan,
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
        assert draft.draft_status == "draft_only"
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
    assert payload["review_status"] == "draft_only"
    assert payload["search_execution_status"] == "not_executed"
    assert payload["online_retrieval_executed"] is False
    assert payload["formal_search_completed"] is False
    assert payload["confirmed_search_plan"] is None
    assert payload["auto_generated_draft"]["unsupported_features"] == [
        "no_online_pubmed_embase_wos_retrieval",
        "no_chinese_database_search",
        "no_chinese_pdf_extraction",
        "no_english_pdf_extraction_ui",
        "no_final_extraction_table_write",
    ]
    assert payload["user_edited_plan"]["review_status"] == "draft_only"
    assert config["search_config_draft"]["search_execution_status"] == "not_executed"
    assert config["search_config_draft"]["formal_search_completed"] is False
    assert config["search_config_draft"]["review_status"] == "draft_only"


def test_unconfirmed_draft_cannot_enter_confirmed_plan() -> None:
    draft = build_meta_seed_search_config_draft("糖尿病前期与甲状腺癌风险的关系")
    edited = build_user_edited_search_plan(draft)

    with pytest.raises(ValueError, match="User confirmation is required"):
        build_confirmed_search_plan(draft, edited)


def test_confirmed_plan_preserves_auto_draft_and_user_edits(tmp_path) -> None:
    project = create_meta_analysis_project("Confirmed Search", tmp_path)
    draft = build_meta_seed_search_config_draft("肥胖与乳腺癌风险的Meta分析")
    edited = build_user_edited_search_plan(
        draft,
        edited_pubmed_query_draft=f"{draft.pubmed_query_draft} AND humans[Filter]",
        user_notes="Prefer human studies only after reviewer confirmation.",
    )

    confirmed_path = save_confirmed_search_plan(project.project_root, draft, edited, user_confirmed=True)
    confirmed = json.loads(confirmed_path.read_text(encoding="utf-8"))
    review_payload = json.loads((project.project_root / "search_strategy" / "meta_seed_search_config_draft.json").read_text(encoding="utf-8"))
    config = json.loads((project.project_root / "meta_project_config.json").read_text(encoding="utf-8"))

    assert confirmed_path.name == "confirmed_search_plan.json"
    assert confirmed["review_status"] == "user_confirmed"
    assert confirmed["search_execution_status"] == "not_executed"
    assert confirmed["formal_search_completed"] is False
    assert confirmed["auto_generated_draft"]["original_question"] == "肥胖与乳腺癌风险的Meta分析"
    assert confirmed["user_edited_plan"]["review_status"] == "needs_edit"
    assert "humans[Filter]" in confirmed["confirmed_pubmed_query_draft"]
    assert "Prefer human studies" in confirmed["user_edited_plan"]["user_notes"]
    assert review_payload["confirmed_search_plan"]["review_status"] == "user_confirmed"
    assert config["search_config_draft"]["review_status"] == "user_confirmed"
    assert config["search_config_draft"]["confirmed_search_plan_path"].endswith("confirmed_search_plan.json")


def test_rejected_draft_does_not_enter_downstream_flow(tmp_path) -> None:
    project = create_meta_analysis_project("Rejected Search", tmp_path)
    draft = build_meta_seed_search_config_draft("复发风险Meta分析")

    rejected = reject_meta_seed_search_config_draft(draft, user_notes="Not enough topic context.")
    rejected_path = save_rejected_search_config_draft(project.project_root, draft, user_notes="Not enough topic context.")
    payload = json.loads(rejected_path.read_text(encoding="utf-8"))
    config = json.loads((project.project_root / "meta_project_config.json").read_text(encoding="utf-8"))

    assert rejected["review_status"] == "rejected"
    assert rejected["confirmed_search_plan"] is None
    assert payload["review_status"] == "rejected"
    assert payload["confirmed_search_plan"] is None
    assert payload["formal_search_completed"] is False
    assert payload["search_execution_status"] == "not_executed"
    assert config["search_config_draft"]["review_status"] == "rejected"
    assert config["search_config_draft"]["confirmed_search_plan_path"] == ""


def test_guard_override_records_warning_and_not_safe_by_default() -> None:
    draft = build_meta_seed_search_config_draft("肥胖与乳腺癌风险的Meta分析，报告HR")
    edited = build_user_edited_search_plan(
        draft,
        guard_overrides=[
            {
                "concept_id": "meta_effect:hazard_ratio",
                "requested_action": "include_in_pubmed_topic_query",
                "reason": "Reviewer wants to search HR explicitly.",
            }
        ],
    )
    confirmed = build_confirmed_search_plan(draft, edited, user_confirmed=True)

    assert edited.review_status == "needs_edit"
    assert edited.guard_overrides[0].concept_id == "meta_effect:hazard_ratio"
    assert "not automatically considered safe" in edited.guard_overrides[0].warning
    assert any("Guard override requested for meta_effect:hazard_ratio" in warning for warning in confirmed.warnings)
    assert "hazard ratio" not in draft.pubmed_query_draft.lower()


def test_pubmed_search_execution_preflight_generates_plan_without_retrieval(tmp_path) -> None:
    project = create_meta_analysis_project("PubMed Preflight", tmp_path)
    draft = build_meta_seed_search_config_draft("糖尿病前期与甲状腺癌风险的关系")
    edited = build_user_edited_search_plan(
        draft,
        edited_pubmed_query_draft=f"{draft.pubmed_query_draft} AND humans[Filter]",
        user_notes="Ready for preflight only.",
    )
    save_confirmed_search_plan(project.project_root, draft, edited, user_confirmed=True)

    plan_path = save_pubmed_search_execution_plan(project.project_root)
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    config = json.loads((project.project_root / "meta_project_config.json").read_text(encoding="utf-8"))

    assert plan_path.name == "search_execution_plan.json"
    assert payload["plan_status"] == "preflight_ready"
    assert payload["database"] == "PubMed"
    assert payload["execution_mode"] == "manual_preflight_only"
    assert payload["search_execution_status"] == "not_executed"
    assert payload["online_retrieval_executed"] is False
    assert "humans[Filter]" in payload["query"]
    assert payload["fields"] == ["MeSH Terms", "Title/Abstract", "Filter"]
    assert payload["limits"] == ["none_applied_by_executor"]
    assert any("PubMed was not queried" in warning for warning in payload["warnings"])
    assert config["search_execution_preflight"]["search_execution_status"] == "not_executed"


def test_pubmed_search_execution_preflight_requires_confirmed_plan_and_nonempty_query(tmp_path) -> None:
    project = create_meta_analysis_project("Invalid Preflight", tmp_path)
    draft = build_meta_seed_search_config_draft("二甲双胍治疗2型糖尿病的疗效")
    edited = build_user_edited_search_plan(draft, edited_pubmed_query_draft="")
    confirmed_path = save_confirmed_search_plan(project.project_root, draft, edited, user_confirmed=True)

    with pytest.raises(ValueError, match="Confirmed PubMed query draft is empty"):
        build_pubmed_search_execution_plan(confirmed_path)

    confirmed_payload = json.loads(confirmed_path.read_text(encoding="utf-8"))
    confirmed_payload["review_status"] = "needs_edit"
    confirmed_path.write_text(json.dumps(confirmed_payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="review_status=user_confirmed"):
        build_pubmed_search_execution_plan(confirmed_path)


def test_pubmed_search_execution_preflight_requires_guard_override_confirmation(tmp_path) -> None:
    project = create_meta_analysis_project("Override Preflight", tmp_path)
    draft = build_meta_seed_search_config_draft("肥胖与乳腺癌风险的Meta分析，报告HR")
    edited = build_user_edited_search_plan(
        draft,
        guard_overrides=[
            {
                "concept_id": "meta_effect:hazard_ratio",
                "requested_action": "include_in_pubmed_topic_query",
                "reason": "Reviewer wants HR in the manual strategy.",
            }
        ],
    )
    confirmed_path = save_confirmed_search_plan(project.project_root, draft, edited, user_confirmed=True)

    with pytest.raises(ValueError, match="Guard override warnings must be explicitly confirmed"):
        build_pubmed_search_execution_plan(confirmed_path)

    confirmed_edited = build_user_edited_search_plan(
        draft,
        guard_overrides=[
            {
                "concept_id": "meta_effect:hazard_ratio",
                "requested_action": "include_in_pubmed_topic_query",
                "reason": "Reviewer explicitly confirmed the guard warning.",
            }
        ],
        guard_override_confirmed=True,
    )
    save_confirmed_search_plan(project.project_root, draft, confirmed_edited, user_confirmed=True)
    plan = build_pubmed_search_execution_plan(project.project_root)

    assert plan.guard_override_confirmed is True
    assert any("Guard override requested for meta_effect:hazard_ratio" in warning for warning in plan.warnings)
    assert plan.online_retrieval_executed is False
