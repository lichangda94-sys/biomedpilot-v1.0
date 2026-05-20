from __future__ import annotations

import re

from app.shared.query_intelligence.meta_seed_terms.loader import load_seed_terms
from app.shared.query_intelligence.meta_seed_terms.models import PicoDraft, SeedTerm


INTENT_RULES: tuple[tuple[str, str], ...] = (
    ("危险因素", "exposure_disease_risk_meta"),
    ("风险", "exposure_disease_risk_meta"),
    ("预后价值", "prognostic_factor_meta"),
    ("诊断价值", "diagnostic_accuracy_meta"),
    ("疗效", "treatment_effect_meta"),
    ("安全性", "safety_outcome_meta"),
)


def classify_research_intent(question: str) -> str:
    for phrase, intent in INTENT_RULES:
        if phrase in question:
            return intent
    if "影响" in question or "关系" in question:
        return "association_meta"
    return "general_meta"


def match_chinese_question_to_pico(question: str) -> PicoDraft:
    matches = _match_seed_terms(question)
    return PicoDraft(
        population_or_disease=[term for term in matches if term.concept_type == "disease"],
        exposure=[term for term in matches if term.concept_type == "exposure"],
        intervention=[term for term in matches if term.concept_type == "intervention"],
        outcome=[term for term in matches if term.concept_type == "outcome"],
        effect=[term for term in matches if term.concept_type == "effect_measure"],
        study_design=[term for term in matches if term.concept_type == "study_design"],
        research_intent=classify_research_intent(question),
    )


def _match_seed_terms(question: str) -> list[SeedTerm]:
    matches: list[SeedTerm] = []
    for seed in load_seed_terms():
        if any(_term_matches(question, term) for term in seed.zh_terms):
            matches.append(seed)
    return matches


def _term_matches(question: str, term: str) -> bool:
    if not term:
        return False
    if _is_latin_token(term):
        return re.search(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", question, re.IGNORECASE) is not None
    return term in question


def _is_latin_token(term: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9]+", term))
