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
    if normalized in {"cad", "chd", "mi", "ph", "af", "vt", "vf", "pe", "ldl", "hdl", "crp", "bnp", "ef"}:
        warnings.append("检测到高歧义心血管缩写；仅按精确缩写和当前上下文解释。")
    if target_context == "meta_analysis" and normalized in {"pr", "sd", "pd"}:
        warnings.append("检测到高歧义 Meta 缩写；需要结合结局、受体或疾病上下文解释。")
    suppress_exact_meta_short_token = target_context == "bioinformatics" and _is_exact_meta_short_token(query)
    if suppress_exact_meta_short_token:
        warnings.append("短 Meta 分析缩写未在 Bioinformatics context 中作为主结果输出。")
    matched_zh_terms: list[str] = []
    disease_terms: list[str] = []
    synonyms: list[str] = []
    abbreviations: list[str] = []
    mesh_terms: list[str] = []
    tissue_terms: list[str] = []
    tcga_projects: list[str] = []
    tcga_primary_sites: list[str] = []
    gtex_tissues: list[str] = []
    data_modalities: list[str] = []
    assay_terms: list[str] = []
    platform_candidates: list[str] = []
    modifier_terms: list[str] = []
    exposure_terms: list[str] = []
    intervention_terms: list[str] = []
    outcome_terms: list[str] = []
    study_design_terms: list[str] = []
    publication_type_terms: list[str] = []
    pico_terms: list[str] = []
    effect_measures: list[str] = []
    diagnostic_accuracy_terms: list[str] = []
    exclusion_type_terms: list[str] = []
    quality_assessment_terms: list[str] = []
    pubmed_query_terms: list[str] = []
    concept_ids: list[str] = []
    term_sources: list[str] = []
    confidences: list[float] = []

    overrides = [] if suppress_exact_meta_short_token else _matched_overrides(normalized, query, target_context)
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
        _extend_unique(tcga_primary_sites, override.tcga_primary_site_candidates)
        _extend_unique(gtex_tissues, override.gtex_tissue_candidates)
        _extend_unique(data_modalities, override.data_modality_terms)
        _extend_unique(assay_terms, override.assay_terms)
        _extend_unique(platform_candidates, override.platform_candidates)
        _extend_unique(modifier_terms, override.modifier_terms_en)
        _extend_unique(exposure_terms, override.exposure_terms)
        _extend_unique(intervention_terms, override.intervention_terms)
        _extend_unique(outcome_terms, override.outcome_terms)
        _extend_unique(study_design_terms, override.study_design_terms)
        _extend_unique(publication_type_terms, override.publication_type_terms)
        _extend_unique(pico_terms, override.pico_terms)
        _extend_unique(effect_measures, override.effect_measures)
        _extend_unique(diagnostic_accuracy_terms, override.diagnostic_accuracy_terms)
        _extend_unique(exclusion_type_terms, override.exclusion_type_terms)
        _extend_unique(quality_assessment_terms, override.quality_assessment_terms)
        _extend_unique(pubmed_query_terms, override.pubmed_query_terms)
        if override.confidence:
            confidences.append(override.confidence)

    index_matches, index_source = ([], "") if suppress_exact_meta_short_token else _matched_runtime_index_concepts(normalized, query, target_context)
    if index_matches:
        _append_unique(term_sources, index_source)
    specific_index_modalities = [
        concept for concept in index_matches if concept.concept_type == "data_modality" and concept.concept_id != "mini:data_modality_core"
    ]
    for concept in index_matches:
        if concept.concept_id == "mini:data_modality_core" and specific_index_modalities:
            continue
        if concept.concept_id in _BROAD_META_CORE_CONCEPT_IDS and _has_specific_meta_match(index_matches):
            continue
        if _should_skip_contextual_false_positive_concept(concept, normalized):
            continue
        _append_unique(concept_ids, concept.concept_id)
        if concept.concept_type == "disease":
            _append_unique(disease_terms, concept.preferred_label_en)
            _extend_unique(disease_terms, concept.exact_synonyms_en)
            _extend_unique(synonyms, concept.synonyms_en)
            _extend_unique(synonyms, concept.related_synonyms_en)
        elif concept.concept_type == "exposure":
            _append_unique(exposure_terms, concept.preferred_label_en)
            _extend_unique(exposure_terms, concept.exposure_terms or concept.synonyms_en)
        elif concept.concept_type in {"intervention", "treatment"}:
            _append_unique(intervention_terms, concept.preferred_label_en)
            _extend_unique(intervention_terms, concept.intervention_terms or concept.synonyms_en)
        elif concept.concept_type in {"biomarker", "hormone", "laboratory_marker", "phenotype"}:
            _append_unique(exposure_terms, concept.preferred_label_en)
            _extend_unique(exposure_terms, concept.synonyms_en)
        elif concept.concept_type == "outcome":
            _append_unique(outcome_terms, concept.preferred_label_en)
            _extend_unique(outcome_terms, concept.outcome_terms or concept.synonyms_en)
            _extend_unique(outcome_terms, concept.pubmed_query_terms)
        elif concept.concept_type == "study_design":
            _append_unique(study_design_terms, concept.preferred_label_en)
            _extend_unique(study_design_terms, concept.study_design_terms or concept.synonyms_en)
            _extend_unique(study_design_terms, concept.pubmed_query_terms)
        elif concept.concept_type == "publication_type":
            _append_unique(publication_type_terms, concept.preferred_label_en)
            _extend_unique(publication_type_terms, concept.publication_type_terms or concept.synonyms_en)
            _extend_unique(publication_type_terms, concept.pubmed_query_terms)
        elif concept.concept_type == "pico_term":
            _append_unique(pico_terms, concept.preferred_label_en)
            _extend_unique(pico_terms, concept.pico_terms or concept.synonyms_en)
        elif concept.concept_type == "effect_measure":
            _append_unique(effect_measures, concept.preferred_label_en)
            _extend_unique(effect_measures, concept.effect_measures or concept.synonyms_en)
        elif concept.concept_type == "diagnostic_accuracy":
            _append_unique(diagnostic_accuracy_terms, concept.preferred_label_en)
            _extend_unique(diagnostic_accuracy_terms, concept.diagnostic_accuracy_terms or concept.synonyms_en)
        elif concept.concept_type == "exclusion_type":
            _append_unique(exclusion_type_terms, concept.preferred_label_en)
            _extend_unique(exclusion_type_terms, concept.exclusion_type_terms or concept.synonyms_en)
            _append_unique(publication_type_terms, concept.preferred_label_en)
            _extend_unique(publication_type_terms, concept.exclusion_type_terms or concept.synonyms_en)
        elif concept.concept_type == "quality_assessment":
            _append_unique(quality_assessment_terms, concept.preferred_label_en)
            _extend_unique(quality_assessment_terms, concept.quality_assessment_terms or concept.synonyms_en)
        elif concept.concept_type == "tissue":
            _append_unique(tissue_terms, concept.preferred_label_en)
            _extend_unique(tissue_terms, concept.synonyms_en)
        elif concept.concept_type == "data_modality":
            _append_unique(data_modalities, concept.preferred_label_en)
            _extend_unique(data_modalities, concept.synonyms_en)
            _append_unique(assay_terms, concept.preferred_label_en)
            _extend_unique(assay_terms, concept.assay_terms)
            _extend_unique(platform_candidates, concept.platform_candidates)
        _extend_unique(tissue_terms, concept.tissue_terms)
        _extend_unique(tcga_primary_sites, concept.tcga_primary_site_candidates)
        _extend_unique(data_modalities, concept.data_modality_terms)
        _extend_unique(assay_terms, concept.assay_terms)
        _extend_unique(platform_candidates, concept.platform_candidates)
        _extend_unique(modifier_terms, concept.modifier_terms_en)
        _extend_unique(exposure_terms, concept.exposure_terms)
        _extend_unique(intervention_terms, concept.intervention_terms)
        _extend_unique(outcome_terms, concept.outcome_terms)
        _extend_unique(study_design_terms, concept.study_design_terms)
        _extend_unique(publication_type_terms, concept.publication_type_terms)
        _extend_unique(pico_terms, concept.pico_terms)
        _extend_unique(effect_measures, concept.effect_measures)
        _extend_unique(diagnostic_accuracy_terms, concept.diagnostic_accuracy_terms)
        _extend_unique(exclusion_type_terms, concept.exclusion_type_terms)
        _extend_unique(quality_assessment_terms, concept.quality_assessment_terms)
        _extend_unique(pubmed_query_terms, concept.pubmed_query_terms)
        _extend_unique(abbreviations, concept.abbreviations)
        _extend_unique(mesh_terms, concept.mesh_terms)
        _extend_unique(tcga_projects, concept.cross_refs.get("tcga", ()))
        _extend_unique(tcga_primary_sites, concept.cross_refs.get("tcga_primary_site", ()))
        _extend_unique(gtex_tissues, concept.cross_refs.get("gtex", ()))

    registry_matches = [] if suppress_exact_meta_short_token else match_registry_concepts(query, target_context=target_context)
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
        elif concept.semantic_group == "dataset" and not data_modalities:
            _extend_unique(data_modalities, [term for term in concept.en_terms if term not in {"dataset", "GEO", "GSE"}])

    if not overrides and not index_matches and not registry_matches:
        warnings.append("未在医学词库索引中匹配到明确术语。")

    if not disease_terms and exposure_terms:
        warnings.append("识别到暴露、表型或生物标志物，未识别到明确疾病词。")
    elif not disease_terms and tissue_terms:
        warnings.append("仅识别到组织词，未识别到明确疾病词。")
    if not disease_terms and not tissue_terms and data_modalities:
        warnings.append("识别到数据类型，但未识别到明确疾病概念。")
    if target_context == "meta_analysis":
        tcga_projects = []
        tcga_primary_sites = []
        gtex_tissues = []
        platform_candidates = []
    elif target_context == "bioinformatics":
        pico_terms = []
        effect_measures = []
        diagnostic_accuracy_terms = []
        exclusion_type_terms = []
        quality_assessment_terms = []
        pubmed_query_terms = []

    return TermLookupResult(
        original_term=query,
        normalized_term=normalized,
        matched=bool(
            matched_zh_terms
            or disease_terms
            or tissue_terms
            or data_modalities
            or assay_terms
            or platform_candidates
            or modifier_terms
            or exposure_terms
            or intervention_terms
            or outcome_terms
            or study_design_terms
            or publication_type_terms
            or pico_terms
            or effect_measures
            or diagnostic_accuracy_terms
            or exclusion_type_terms
            or quality_assessment_terms
            or pubmed_query_terms
        ),
        matched_zh_terms=matched_zh_terms,
        disease_terms_en=disease_terms,
        synonyms_en=synonyms,
        abbreviations=abbreviations,
        mesh_terms=mesh_terms,
        tissue_terms=tissue_terms,
        tcga_project_candidates=tcga_projects,
        tcga_primary_site_candidates=tcga_primary_sites,
        gtex_tissue_candidates=gtex_tissues,
        data_modality_terms=data_modalities,
        assay_terms=assay_terms,
        platform_candidates=platform_candidates,
        modifier_terms_en=modifier_terms,
        exposure_terms=exposure_terms,
        intervention_terms=intervention_terms,
        outcome_terms=outcome_terms,
        study_design_terms=study_design_terms,
        publication_type_terms=publication_type_terms,
        pico_terms=pico_terms,
        effect_measures=effect_measures,
        diagnostic_accuracy_terms=diagnostic_accuracy_terms,
        exclusion_type_terms=exclusion_type_terms,
        quality_assessment_terms=quality_assessment_terms,
        pubmed_query_terms=pubmed_query_terms,
        concept_ids=concept_ids,
        term_sources=term_sources,
        confidence=max(confidences) if confidences else (0.75 if registry_matches else 0.0),
        warnings=warnings,
    )


def _matched_overrides(normalized_query: str, raw_query: str, target_context: str) -> list[ChineseTermOverride]:
    candidates: list[ChineseTermOverride] = []
    for override in load_zh_overrides():
        if not _override_allowed_for_context(override, target_context):
            continue
        if not override.normalized_zh:
            continue
        exact_allowed = override.normalized_zh == normalized_query and not _is_strict_uppercase_short_token(override.zh_term)
        if exact_allowed or _term_matches_query(override.normalized_zh, normalized_query, override.zh_term, raw_query):
            candidates.append(override)
    return _rank_override_matches(candidates)


def _matched_runtime_index_concepts(normalized_query: str, raw_query: str, target_context: str) -> tuple[list[TermConcept], str]:
    full_matches = _matched_index_concepts(normalized_query, raw_query, target_context, load_full_term_index())
    if full_matches:
        return full_matches, "medical_terms_index.sqlite"
    mini_matches = _matched_index_concepts(normalized_query, raw_query, target_context, load_mini_term_index())
    if mini_matches:
        return mini_matches, "mini_medical_terms_index"
    return [], ""


def _matched_index_concepts(normalized_query: str, raw_query: str, target_context: str, concepts: tuple[TermConcept, ...]) -> list[TermConcept]:
    candidates: list[TermConcept] = []
    for concept in concepts:
        if not _concept_allowed_for_context(concept, target_context):
            continue
        terms = [concept.preferred_label_en, *concept.normalized_terms, *concept.synonyms_en, *concept.exact_synonyms_en]
        for term in terms:
            normalized = normalize_zh_term(term) if not term.isascii() else normalize_en_term(term)
            if _term_matches_query(normalized, normalized_query, term, raw_query):
                candidates.append(concept)
                break
    return _rank_concept_matches(candidates)


def _term_matches_query(normalized_term: str, normalized_query: str, raw_term: str, raw_query: str = "") -> bool:
    if not normalized_term:
        return False
    if _is_strict_uppercase_short_token(raw_term):
        return re.search(rf"(?<![A-Za-z0-9]){re.escape(raw_term)}(?![A-Za-z0-9])", raw_query) is not None
    if normalized_term == normalized_query:
        return True
    if not raw_term.isascii():
        if len(normalized_term) <= 1:
            return False
        return normalized_term in normalized_query
    if len(normalized_term) <= 4 or "-" in normalized_term or "+" in normalized_term:
        return re.search(rf"(?<![a-z0-9]){re.escape(normalized_term)}(?![a-z0-9])", normalized_query) is not None
    return normalized_term in normalized_query


def _rank_override_matches(candidates: list[ChineseTermOverride]) -> list[ChineseTermOverride]:
    priority = {"disease": 0, "phenotype": 1, "biomarker": 2, "hormone": 2, "laboratory_marker": 2, "modifier": 3, "tissue": 4, "data_modality": 5, "outcome": 6, "effect_measure": 6, "study_design": 6, "publication_type": 6, "pico_term": 6, "diagnostic_accuracy": 6, "exclusion_type": 6, "quality_assessment": 6}
    candidates.sort(key=lambda item: (priority.get(item.concept_type, 9), -len(item.normalized_zh), -item.confidence))
    disease_spans = [item.normalized_zh for item in candidates if item.concept_type == "disease"]
    has_specific_meta_override = any(
        item.concept_type in _META_CONCEPT_TYPES
        and not any(concept_id in _BROAD_META_CORE_CONCEPT_IDS for concept_id in item.mapped_concept_ids)
        for item in candidates
    )
    result: list[ChineseTermOverride] = []
    for item in candidates:
        if any(item.normalized_zh != span and item.normalized_zh in span for span in (candidate.normalized_zh for candidate in candidates)):
            continue
        if item.concept_type in {"tissue", "data_modality"} and any(item.normalized_zh != span and item.normalized_zh in span for span in disease_spans):
            continue
        if has_specific_meta_override and any(concept_id in _BROAD_META_CORE_CONCEPT_IDS for concept_id in item.mapped_concept_ids):
            continue
        result.append(item)
    return result


def _rank_concept_matches(candidates: list[TermConcept]) -> list[TermConcept]:
    priority = {"disease": 0, "phenotype": 1, "biomarker": 2, "hormone": 2, "laboratory_marker": 2, "modifier": 3, "tissue": 4, "data_modality": 5, "outcome": 6, "effect_measure": 6, "study_design": 6, "publication_type": 6, "pico_term": 6, "diagnostic_accuracy": 6, "exclusion_type": 6, "quality_assessment": 6}
    unique: dict[str, TermConcept] = {candidate.concept_id: candidate for candidate in candidates}
    items = list(unique.values())
    items.sort(key=lambda item: (priority.get(item.concept_type, 9), -max((len(term) for term in item.normalized_terms), default=0)))
    return items


_META_CONCEPT_TYPES = {
    "pico_term",
    "effect_measure",
    "outcome",
    "study_design",
    "publication_type",
    "diagnostic_accuracy",
    "exclusion_type",
    "quality_assessment",
}

_BROAD_META_CORE_CONCEPT_IDS = {
    "mini:meta_outcomes_core",
    "mini:study_design_core",
    "mini:publication_exclusion_core",
    "mini:effect_size_core",
    "mini:publication_exclusion_gap_terms",
}


def _override_allowed_for_context(override: ChineseTermOverride, target_context: str) -> bool:
    if target_context == "meta_analysis":
        return True
    if override.concept_type in _META_CONCEPT_TYPES:
        return False
    if override.contexts and "meta_analysis" in override.contexts and target_context not in override.contexts:
        return False
    return True


def _concept_allowed_for_context(concept: TermConcept, target_context: str) -> bool:
    if target_context == "meta_analysis":
        return True
    if concept.category == "meta_analysis_term" or concept.concept_type in _META_CONCEPT_TYPES:
        return False
    if concept.contexts and "meta_analysis" in concept.contexts and target_context not in concept.contexts:
        return False
    return True


def _has_specific_meta_match(concepts: list[TermConcept]) -> bool:
    return any(
        concept.concept_id not in _BROAD_META_CORE_CONCEPT_IDS
        and (concept.category == "meta_analysis_term" or concept.concept_type in _META_CONCEPT_TYPES)
        for concept in concepts
    )


def _is_strict_uppercase_short_token(raw_term: str) -> bool:
    return raw_term.isascii() and 1 < len(raw_term) <= 3 and raw_term.upper() == raw_term and raw_term.isalpha()


def _is_exact_meta_short_token(query: str) -> bool:
    return query.strip() in {"OS", "HR", "OR", "RR", "CI", "MD", "SMD", "SE", "PR", "CR", "SD", "PD"}


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
    if concept_id == "thyroid_cancer":
        non_cancer_thyroid_terms = {
            "甲状腺",
            "thyroid",
            "thyroid tissue",
            "thyroid gland",
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
        exact_tissue_terms = {"甲状腺", "thyroid", "thyroid tissue", "thyroid gland"}
        return normalized_query in exact_tissue_terms or any(
            term not in exact_tissue_terms and term in normalized_query for term in non_cancer_thyroid_terms
        )
    if concept_id == "esophageal_squamous_cell_carcinoma":
        esophagus_tissue_terms = {
            "食管",
            "食道",
            "食管组织",
            "食道组织",
            "食管黏膜",
            "食道黏膜",
            "食管肌层",
            "食道肌层",
            "胃食管交界",
            "食管胃交界",
            "贲门交界",
            "esophagus",
            "oesophagus",
            "esophageal tissue",
            "esophagus mucosa",
            "esophageal mucosa",
            "esophagus muscularis",
            "esophageal muscularis",
            "gastroesophageal junction",
        }
        return normalized_query in esophagus_tissue_terms
    return False


def _should_skip_contextual_false_positive_concept(concept: TermConcept, normalized_query: str) -> bool:
    if concept.concept_id == "mini:meta_analysis_recurrence" and "发表" in normalized_query:
        return True
    if concept.concept_id == "mini:meta_analysis_risk" and normalized_query in {"风险比", "危险比", "风险率"}:
        return True
    if concept.concept_id == "mini:parkinson_disease" and normalized_query == "pd":
        return True
    if concept.concept_id == "mini:hypertension" and normalized_query in {
        "pulmonary hypertension",
        "肺动脉高压",
        "肺高压",
        "pulmonary arterial hypertension",
    }:
        return True
    if concept.concept_id == "mini:cardiovascular_disease_core" and normalized_query in {
        "myocardial infarction",
        "heart attack",
        "acute myocardial infarction",
        "acute coronary syndrome",
        "hypertension",
        "pulmonary hypertension",
        "essential hypertension",
        "secondary hypertension",
        "isolated systolic hypertension",
        "atherosclerosis",
        "arteriosclerosis",
        "stroke",
        "ischemic stroke",
        "hemorrhagic stroke",
        "cerebral infarction",
        "心肌梗死",
        "心梗",
        "急性心肌梗死",
        "急性心梗",
        "急性冠脉综合征",
        "高血压",
        "肺动脉高压",
        "肺高压",
        "原发性高血压",
        "继发性高血压",
        "单纯收缩期高血压",
        "动脉粥样硬化",
        "动脉硬化",
        "脑卒中",
        "中风",
        "缺血性脑卒中",
        "脑梗死",
        "出血性脑卒中",
    }:
        return True
    return False


def _extend_unique(items: list[str], values: object) -> None:
    for value in values:  # type: ignore[union-attr]
        _append_unique(items, str(value))


def _append_unique(items: list[str], value: str) -> None:
    text = value.strip()
    key = text.lower()
    if text and key not in {item.lower() for item in items}:
        items.append(text)
