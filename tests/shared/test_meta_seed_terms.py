from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from app.shared.query_intelligence.meta_seed_terms import (
    bind_outcome_effect_candidates,
    build_pubmed_query_blocks,
    classify_research_intent,
    extract_evidence_candidates,
    load_emtree_mappings,
    load_mesh_mappings,
    load_pubmed_free_text_mappings,
    load_seed_terms,
    match_chinese_question_to_pico,
    split_sections,
    validate_seed_terms,
)


ROOT = Path(__file__).resolve().parents[2]
META_TERMS = ROOT / "data" / "medical_terms" / "meta_analysis"


def test_meta_seed_terms_schema_and_category_coverage() -> None:
    schema = json.loads((META_TERMS / "meta_seed_terms_schema.json").read_text(encoding="utf-8"))
    seeds = load_seed_terms()
    by_type = Counter(seed.concept_type for seed in seeds)

    assert 170 <= len(seeds) <= 220
    assert len({seed.concept_id for seed in seeds}) == len(seeds)
    assert validate_seed_terms() == []
    assert set(schema["items"]["required"]) <= set(seeds[0].__dict__)
    assert {
        "disease",
        "exposure",
        "intervention",
        "outcome",
        "effect_measure",
        "study_design",
        "research_intent",
    } <= set(by_type)
    assert 45 <= by_type["disease"] <= 55
    assert 30 <= by_type["exposure"] <= 40
    assert 25 <= by_type["intervention"] <= 35
    assert 32 <= by_type["outcome"] <= 42
    assert 12 <= by_type["effect_measure"] <= 18
    assert 10 <= by_type["study_design"] <= 15
    assert 10 <= by_type["research_intent"] <= 15
    assert _seed(seeds, "meta_disease:heart_failure").review_status == "seed_batch_2_curated"
    assert _seed(seeds, "meta_exposure:mediterranean_diet").review_status == "seed_batch_2_curated"
    assert _seed(seeds, "meta_intervention:sglt2_inhibitor").review_status == "seed_batch_2_curated"
    assert _seed(seeds, "meta_outcome:objective_response_rate").review_status == "seed_batch_2_curated"


def test_query_guards_block_intent_and_effect_topic_expansion() -> None:
    seeds = load_seed_terms()
    intent_or_effect = [seed for seed in seeds if seed.concept_type in {"research_intent", "effect_measure"}]
    outcomes = [seed for seed in seeds if seed.concept_type == "outcome"]
    study_designs = [seed for seed in seeds if seed.concept_type == "study_design"]

    assert all(seed.query_expansion_allowed is False for seed in intent_or_effect)
    assert all(seed.standalone_search_allowed is False for seed in intent_or_effect)
    assert all(seed.filter_only or seed.pdf_extraction_target for seed in intent_or_effect)
    assert all(seed.query_expansion_allowed == "conditional" for seed in outcomes)
    assert all(seed.standalone_search_allowed is False for seed in outcomes)
    assert all("population_or_disease" in seed.requires_pairing_with for seed in outcomes)
    assert all(seed.filter_only is True for seed in study_designs)
    assert all(seed.query_expansion_allowed is False for seed in study_designs)
    assert all(seed.standalone_search_allowed is False for seed in study_designs)

    blocks = build_pubmed_query_blocks(["meta_research_intent:risk_factor", "meta_effect:hazard_ratio"])

    assert blocks == []
    assert build_pubmed_query_blocks(["meta_study_design:meta_analysis"]) == []


def test_pubmed_query_blocks_use_manual_mesh_and_free_text_mappings() -> None:
    blocks = build_pubmed_query_blocks(
        [
            "meta_disease:thyroid_cancer",
            "meta_exposure:prediabetes",
            "meta_intervention:metformin",
            "meta_outcome:recurrence",
        ]
    )
    text = " ".join(blocks)

    assert '"Thyroid Neoplasms"[MeSH Terms]' in text
    assert '"thyroid cancer"[Title/Abstract]' in text
    assert '"Prediabetic State"[MeSH Terms]' in text
    assert '"metformin"[Title/Abstract]' in text
    assert '"Recurrence"[MeSH Terms]' in text
    assert "hazard ratio" not in text.lower()
    assert "risk factor" not in text.lower()

    batch_2_blocks = build_pubmed_query_blocks(
        [
            "meta_disease:heart_failure",
            "meta_exposure:mediterranean_diet",
            "meta_intervention:sglt2_inhibitor",
            "meta_outcome:objective_response_rate",
        ]
    )
    batch_2_text = " ".join(batch_2_blocks)

    assert '"Heart Failure"[MeSH Terms]' in batch_2_text
    assert '"Mediterranean diet"[Title/Abstract]' in batch_2_text
    assert '"SGLT2 inhibitor"[Title/Abstract]' in batch_2_text
    assert '"objective response rate"[Title/Abstract]' in batch_2_text


def test_manual_mapping_files_cover_expected_seed_sets() -> None:
    seeds = load_seed_terms()
    mapped_types = {"disease", "exposure", "intervention", "outcome"}
    expected_mapped_ids = {seed.concept_id for seed in seeds if seed.concept_type in mapped_types}
    all_seed_ids = {seed.concept_id for seed in seeds}
    mesh = load_mesh_mappings()
    pubmed = load_pubmed_free_text_mappings()
    emtree = load_emtree_mappings()

    assert set(mesh) == expected_mapped_ids
    assert set(pubmed) == expected_mapped_ids
    assert set(emtree) == all_seed_ids
    assert all(row["emtree_terms"] == [] for row in emtree.values())
    assert all(row["emtree_review_status"] == "needs_review" for row in emtree.values())


def test_chinese_seed_matching_generates_pico_drafts() -> None:
    cases = {
        "糖尿病前期与甲状腺癌风险的关系": {
            "intent": "exposure_disease_risk_meta",
            "disease": "meta_disease:thyroid_cancer",
            "exposure": "meta_exposure:prediabetes",
        },
        "二甲双胍治疗2型糖尿病的疗效": {
            "intent": "treatment_effect_meta",
            "disease": "meta_disease:type_2_diabetes_mellitus",
            "intervention": "meta_intervention:metformin",
        },
        "放射性碘治疗甲状腺癌复发的影响": {
            "intent": "association_meta",
            "disease": "meta_disease:thyroid_cancer",
            "intervention": "meta_intervention:radioactive_iodine_therapy",
            "outcome": "meta_outcome:recurrence",
        },
        "肥胖与乳腺癌风险的Meta分析": {
            "intent": "exposure_disease_risk_meta",
            "disease": "meta_disease:breast_cancer",
            "exposure": "meta_exposure:obesity",
            "study_design": "meta_study_design:meta_analysis",
        },
    }

    for question, expected in cases.items():
        draft = match_chinese_question_to_pico(question)
        concept_ids = set(draft.concept_ids())

        assert draft.research_intent == expected["intent"]
        assert expected["disease"] in concept_ids
        if "exposure" in expected:
            assert expected["exposure"] in concept_ids
        if "intervention" in expected:
            assert expected["intervention"] in concept_ids
        if "outcome" in expected:
            assert expected["outcome"] in concept_ids
        if "study_design" in expected:
            assert expected["study_design"] in concept_ids


def test_research_intent_rules_are_deterministic() -> None:
    assert classify_research_intent("危险因素") == "exposure_disease_risk_meta"
    assert classify_research_intent("预后价值") == "prognostic_factor_meta"
    assert classify_research_intent("诊断价值") == "diagnostic_accuracy_meta"
    assert classify_research_intent("疗效") == "treatment_effect_meta"
    assert classify_research_intent("安全性") == "safety_outcome_meta"


def test_batch_2_chinese_terms_are_curated_seed_matches() -> None:
    draft = match_chinese_question_to_pico("SGLT2抑制剂治疗心力衰竭的安全性")
    concept_ids = set(draft.concept_ids())

    assert draft.research_intent == "safety_outcome_meta"
    assert "meta_disease:heart_failure" in concept_ids
    assert "meta_intervention:sglt2_inhibitor" in concept_ids
    assert "meta_research_intent:safety" not in concept_ids


def test_english_section_detection_excludes_references_and_extracts_regex_candidates() -> None:
    text = """
    Abstract
    We reviewed 120 patients.
    Results
    PFS was improved with HR=0.72 95% CI 0.55-0.94, P=0.01. Follow-up was 24 months.
    References
    Smith reported OS HR=9.99 P=0.99 in a cited paper.
    """
    sections = split_sections(text)
    candidates = extract_evidence_candidates(text)
    values = [candidate.value for candidate in candidates]

    assert "references" not in sections
    assert "HR=9.99" not in " ".join(values)
    assert any(candidate.evidence_type == "sample_size" and "120 patients" in candidate.value for candidate in candidates)
    assert any(candidate.evidence_type == "effect_measure" and "HR=0.72" in candidate.value for candidate in candidates)
    assert any(candidate.evidence_type == "confidence_interval" for candidate in candidates)
    assert any(candidate.evidence_type == "p_value" and "P=0.01" in candidate.value for candidate in candidates)
    assert any(candidate.evidence_type == "follow_up" for candidate in candidates)


def test_outcome_effect_binding_outputs_pending_review_only() -> None:
    text = """
    Results
    OS was associated with HR=0.80 95% CI 0.66-0.98, P=0.03.
    PFS showed OR=1.42 95% CI 1.10-1.91, P=0.02.
    References
    DFS HR=5.00 P=0.99.
    """
    bindings = bind_outcome_effect_candidates(text)
    outcomes = {binding.outcome.upper() for binding in bindings}

    assert {"OS", "PFS"} <= outcomes
    assert "DFS" not in outcomes
    assert all(binding.review_status == "pending_review" for binding in bindings)
    assert all(binding.final_extraction_allowed is False for binding in bindings)
    assert any(binding.effect_measure.upper().startswith("HR") for binding in bindings)


def _seed(seeds: tuple[object, ...], concept_id: str) -> object:
    return next(seed for seed in seeds if seed.concept_id == concept_id)
