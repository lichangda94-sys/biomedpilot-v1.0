from __future__ import annotations

import re

from app.shared.query_intelligence.biomedical_term_registry import match_registry_concepts
from app.shared.query_intelligence.query_intelligence_models import MedicalConcept


def detect_language(question: str, hint: str = "auto") -> str:
    normalized = hint.strip().lower()
    if normalized in {"zh", "en"}:
        return normalized
    return "zh" if re.search(r"[\u4e00-\u9fff]", question) else "en"


def normalize_question(question: str) -> str:
    return " ".join(question.strip().split())


def parse_medical_question(question: str, *, target_context: str = "", optional_domain: str = "") -> tuple[tuple[MedicalConcept, ...], str, str, str, float]:
    concepts = match_registry_concepts(question, target_context=target_context)
    domain = _detect_domain(question, concepts, optional_domain)
    intent = _detect_intent(question, concepts, target_context)
    analysis_type = _detect_review_or_analysis_type(intent, target_context)
    confidence = min(0.95, 0.35 + len(concepts) * 0.12)
    return concepts, domain, intent, analysis_type, confidence


def _detect_domain(question: str, concepts: tuple[MedicalConcept, ...], optional_domain: str) -> str:
    if optional_domain:
        return optional_domain
    if any("thyroid" in " ".join(concept.en_terms).lower() or "甲状腺" in " ".join(concept.zh_terms) for concept in concepts):
        return "thyroid cancer"
    if "肿瘤" in question or "癌" in question:
        return "oncology"
    if "代谢" in question or "肥胖" in question:
        return "metabolism"
    return "general biomedical"


def _detect_intent(question: str, concepts: tuple[MedicalConcept, ...], target_context: str) -> str:
    ids = {concept.concept_id for concept in concepts}
    if target_context == "bioinformatics" or any(token in question for token in ("数据集", "GEO", "GSE", "表达谱", "转录组")):
        return "dataset_search"
    if "treatment" in ids or any(token in question for token in ("治疗", "药物", "化疗", "抑制剂")):
        return "treatment_effect"
    if "survival" in ids:
        return "prognosis_survival"
    if "incidence_risk" in ids or any(token in question for token in ("发病", "风险", "发生", "关系")):
        return "exposure_disease_risk"
    return "concept_search"


def _detect_review_or_analysis_type(intent: str, target_context: str) -> str:
    if target_context == "meta_analysis":
        if intent == "exposure_disease_risk":
            return "exposure_disease_risk_meta"
        if intent == "treatment_effect":
            return "treatment_effect_meta"
        return "general_meta_search"
    if target_context == "bioinformatics":
        return "dataset_query_generation"
    return intent
