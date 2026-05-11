from __future__ import annotations

import re

from app.shared.query_intelligence.biomedical_term_registry import match_registry_concepts

from .term_index_loader import load_full_term_index, load_mini_term_index
from .term_index_models import ChineseTermOverride, TermConcept, TermLookupResult
from .term_normalizer import normalize_en_term, normalize_zh_term
from .zh_overrides_loader import load_zh_overrides


def lookup_medical_terms(query: str, target_context: str = "bioinformatics") -> TermLookupResult:
    normalized = normalize_en_term(query) if query.isascii() else normalize_zh_term(query)
    warnings: list[str] = []
    if normalized in {"scc", "rcc"}:
        warnings.append("检测到高歧义肿瘤缩写；需要补充部位或亚型后再做强疾病扩展。")
    matched_zh_terms: list[str] = []
    disease_terms: list[str] = []
    synonyms: list[str] = []
    abbreviations: list[str] = []
    mesh_terms: list[str] = []
    tissue_terms: list[str] = []
    tcga_projects: list[str] = []
    gtex_tissues: list[str] = []
    data_modalities: list[str] = []
    modifier_terms: list[str] = []
    exposure_terms: list[str] = []
    intervention_terms: list[str] = []
    outcome_terms: list[str] = []
    study_design_terms: list[str] = []
    publication_type_terms: list[str] = []
    concept_ids: list[str] = []
    term_sources: list[str] = []
    confidences: list[float] = []

    overrides = _matched_overrides(normalized)
    if overrides:
        _append_unique(term_sources, "zh_term_overrides")
    for override in overrides:
        _append_unique(matched_zh_terms, override.zh_term)
        _extend_unique(concept_ids, override.mapped_concept_ids)
        _extend_unique(disease_terms, override.disease_terms_en)
        _extend_unique(synonyms, override.synonyms_en)
        _extend_unique(abbreviations, override.abbreviations)
        _extend_unique(mesh_terms, override.mesh_terms)
        _extend_unique(tissue_terms, override.tissue_terms)
        _extend_unique(tcga_projects, override.tcga_project_candidates)
        _extend_unique(gtex_tissues, override.gtex_tissue_candidates)
        _extend_unique(data_modalities, override.data_modality_terms)
        _extend_unique(modifier_terms, override.modifier_terms_en)
        _extend_unique(exposure_terms, override.exposure_terms)
        _extend_unique(intervention_terms, override.intervention_terms)
        _extend_unique(outcome_terms, override.outcome_terms)
        _extend_unique(study_design_terms, override.study_design_terms)
        _extend_unique(publication_type_terms, override.publication_type_terms)
        if override.confidence:
            confidences.append(override.confidence)

    index_matches, index_source = _matched_runtime_index_concepts(normalized)
    if index_matches:
        _append_unique(term_sources, index_source)
    for concept in index_matches:
        _append_unique(concept_ids, concept.concept_id)
        if concept.concept_type == "disease":
            _append_unique(disease_terms, concept.preferred_label_en)
            _extend_unique(disease_terms, concept.exact_synonyms_en)
            _extend_unique(synonyms, concept.synonyms_en)
            _extend_unique(synonyms, concept.related_synonyms_en)
        elif concept.concept_type == "exposure":
            _append_unique(exposure_terms, concept.preferred_label_en)
            _extend_unique(exposure_terms, concept.synonyms_en)
        elif concept.concept_type in {"intervention", "treatment"}:
            _append_unique(intervention_terms, concept.preferred_label_en)
            _extend_unique(intervention_terms, concept.synonyms_en)
        elif concept.concept_type in {"biomarker", "hormone", "laboratory_marker", "phenotype"}:
            _append_unique(exposure_terms, concept.preferred_label_en)
            _extend_unique(exposure_terms, concept.synonyms_en)
        elif concept.concept_type == "outcome":
            _append_unique(outcome_terms, concept.preferred_label_en)
            _extend_unique(outcome_terms, concept.synonyms_en)
        elif concept.concept_type == "study_design":
            _append_unique(study_design_terms, concept.preferred_label_en)
            _extend_unique(study_design_terms, concept.synonyms_en)
        elif concept.concept_type == "publication_type":
            _append_unique(publication_type_terms, concept.preferred_label_en)
            _extend_unique(publication_type_terms, concept.synonyms_en)
        elif concept.concept_type == "tissue":
            _append_unique(tissue_terms, concept.preferred_label_en)
            _extend_unique(tissue_terms, concept.synonyms_en)
        elif concept.concept_type == "data_modality":
            _append_unique(data_modalities, concept.preferred_label_en)
            _extend_unique(data_modalities, concept.synonyms_en)
        _extend_unique(tissue_terms, concept.tissue_terms)
        _extend_unique(data_modalities, concept.data_modality_terms)
        _extend_unique(modifier_terms, concept.modifier_terms_en)
        _extend_unique(abbreviations, concept.abbreviations)
        _extend_unique(mesh_terms, concept.mesh_terms)
        _extend_unique(tcga_projects, concept.cross_refs.get("tcga", ()))
        _extend_unique(gtex_tissues, concept.cross_refs.get("gtex", ()))

    registry_matches = match_registry_concepts(query, target_context=target_context)
    if registry_matches:
        _append_unique(term_sources, "biomedical_term_registry")
    for concept in registry_matches:
        if _should_skip_registry_concept(concept.concept_id, normalized):
            continue
        if concept.semantic_group == "disease":
            _extend_unique(disease_terms, concept.en_terms)
            _extend_unique(synonyms, concept.synonyms)
            _extend_unique(mesh_terms, concept.mesh_terms)
            _extend_unique(tcga_projects, _tcga_from_database_terms(concept.database_terms))
            _extend_unique(gtex_tissues, _gtex_from_database_terms(concept.database_terms))
            _append_unique(concept_ids, concept.concept_id)
            _extend_unique(matched_zh_terms, concept.zh_terms)
        elif concept.semantic_group == "modifier":
            _extend_unique(modifier_terms, concept.en_terms)
            _extend_unique(matched_zh_terms, concept.zh_terms)
        elif concept.semantic_group == "dataset":
            _extend_unique(data_modalities, [term for term in concept.en_terms if term not in {"dataset", "GEO", "GSE"}])

    if not overrides and not index_matches and not registry_matches:
        warnings.append("未在医学词库索引中匹配到明确术语。")

    if not disease_terms and tissue_terms:
        warnings.append("仅识别到组织词，未识别到明确疾病词。")
    if target_context == "meta_analysis":
        tcga_projects = []
        gtex_tissues = []

    return TermLookupResult(
        original_term=query,
        normalized_term=normalized,
        matched=bool(
            matched_zh_terms
            or disease_terms
            or tissue_terms
            or data_modalities
            or modifier_terms
            or exposure_terms
            or intervention_terms
            or outcome_terms
            or study_design_terms
            or publication_type_terms
        ),
        matched_zh_terms=matched_zh_terms,
        disease_terms_en=disease_terms,
        synonyms_en=synonyms,
        abbreviations=abbreviations,
        mesh_terms=mesh_terms,
        tissue_terms=tissue_terms,
        tcga_project_candidates=tcga_projects,
        gtex_tissue_candidates=gtex_tissues,
        data_modality_terms=data_modalities,
        modifier_terms_en=modifier_terms,
        exposure_terms=exposure_terms,
        intervention_terms=intervention_terms,
        outcome_terms=outcome_terms,
        study_design_terms=study_design_terms,
        publication_type_terms=publication_type_terms,
        concept_ids=concept_ids,
        term_sources=term_sources,
        confidence=max(confidences) if confidences else (0.75 if registry_matches else 0.0),
        warnings=warnings,
    )


def _matched_overrides(normalized_query: str) -> list[ChineseTermOverride]:
    candidates: list[ChineseTermOverride] = []
    for override in load_zh_overrides():
        if not override.normalized_zh:
            continue
        if override.normalized_zh == normalized_query or _term_matches_query(override.normalized_zh, normalized_query, override.zh_term):
            candidates.append(override)
    return _rank_override_matches(candidates)


def _matched_runtime_index_concepts(normalized_query: str) -> tuple[list[TermConcept], str]:
    full_matches = _matched_index_concepts(normalized_query, load_full_term_index())
    if full_matches:
        return full_matches, "medical_terms_index.sqlite"
    mini_matches = _matched_index_concepts(normalized_query, load_mini_term_index())
    if mini_matches:
        return mini_matches, "mini_medical_terms_index"
    return [], ""


def _matched_index_concepts(normalized_query: str, concepts: tuple[TermConcept, ...]) -> list[TermConcept]:
    candidates: list[TermConcept] = []
    for concept in concepts:
        terms = [concept.preferred_label_en, *concept.normalized_terms, *concept.synonyms_en, *concept.exact_synonyms_en]
        for term in terms:
            normalized = normalize_zh_term(term) if not term.isascii() else normalize_en_term(term)
            if _term_matches_query(normalized, normalized_query, term):
                candidates.append(concept)
                break
    return _rank_concept_matches(candidates)


def _term_matches_query(normalized_term: str, normalized_query: str, raw_term: str) -> bool:
    if not normalized_term:
        return False
    if normalized_term == normalized_query:
        return True
    if not raw_term.isascii():
        return normalized_term in normalized_query
    if len(normalized_term) <= 4:
        return re.search(rf"(?<![a-z0-9]){re.escape(normalized_term)}(?![a-z0-9])", normalized_query) is not None
    return normalized_term in normalized_query


def _rank_override_matches(candidates: list[ChineseTermOverride]) -> list[ChineseTermOverride]:
    priority = {"disease": 0, "phenotype": 1, "biomarker": 2, "hormone": 2, "laboratory_marker": 2, "modifier": 3, "tissue": 4, "data_modality": 5}
    candidates.sort(key=lambda item: (priority.get(item.concept_type, 9), -len(item.normalized_zh), -item.confidence))
    disease_spans = [item.normalized_zh for item in candidates if item.concept_type == "disease"]
    result: list[ChineseTermOverride] = []
    for item in candidates:
        if item.concept_type in {"tissue", "data_modality"} and any(item.normalized_zh != span and item.normalized_zh in span for span in disease_spans):
            continue
        result.append(item)
    return result


def _rank_concept_matches(candidates: list[TermConcept]) -> list[TermConcept]:
    priority = {"disease": 0, "phenotype": 1, "biomarker": 2, "hormone": 2, "laboratory_marker": 2, "modifier": 3, "tissue": 4, "data_modality": 5}
    unique: dict[str, TermConcept] = {candidate.concept_id: candidate for candidate in candidates}
    items = list(unique.values())
    items.sort(key=lambda item: (priority.get(item.concept_type, 9), -max((len(term) for term in item.normalized_terms), default=0)))
    return items


def _tcga_from_database_terms(terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if term.upper().startswith("TCGA-")]


def _gtex_from_database_terms(terms: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for term in terms:
        lowered = term.lower()
        if "thyroid" in lowered:
            _append_unique(values, "Thyroid")
        if "brain" in lowered:
            _append_unique(values, "Brain")
        if "esoph" in lowered:
            _append_unique(values, "Esophagus")
    return values


def _should_skip_registry_concept(concept_id: str, normalized_query: str) -> bool:
    if concept_id != "thyroid_cancer":
        return False
    non_cancer_thyroid_terms = {
        "甲状腺结节",
        "桥本甲状腺炎",
        "桥本病",
        "graves病",
        "格雷夫斯病",
        "甲状腺功能减退症",
        "甲减",
        "甲状腺功能亢进症",
        "甲亢",
        "自身免疫性甲状腺炎",
        "甲状腺肿",
        "甲状腺激素紊乱",
        "hypothyroidism",
        "hyperthyroidism",
        "hashimoto thyroiditis",
        "graves disease",
        "autoimmune thyroiditis",
        "thyroid nodule",
        "goiter",
        "thyroid hormone disorder",
    }
    return any(term in normalized_query for term in non_cancer_thyroid_terms)


def _extend_unique(items: list[str], values: object) -> None:
    for value in values:  # type: ignore[union-attr]
        _append_unique(items, str(value))


def _append_unique(items: list[str], value: str) -> None:
    text = value.strip()
    key = text.lower()
    if text and key not in {item.lower() for item in items}:
        items.append(text)
