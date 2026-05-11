from __future__ import annotations

from collections.abc import Iterable

from .term_index_models import TermLookupResult
from .term_normalizer import normalize_zh_term
from .vocabulary_provider import MedicalVocabularyProvider, VocabularyProviderMatch, default_vocabulary_providers


def lookup_medical_terms(
    query: str,
    target_context: str = "bioinformatics",
    *,
    providers: Iterable[MedicalVocabularyProvider] | None = None,
) -> TermLookupResult:
    normalized = normalize_zh_term(query)
    warnings: list[str] = []
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

    provider_matches = tuple(
        provider.lookup(query, normalized, target_context)
        for provider in (tuple(providers) if providers is not None else default_vocabulary_providers())
    )
    registry_matched = any(match.registry_concepts for match in provider_matches)
    for match in provider_matches:
        if match.matched:
            _append_unique(term_sources, match.source)
        _apply_provider_match(
            match,
            matched_zh_terms=matched_zh_terms,
            disease_terms=disease_terms,
            synonyms=synonyms,
            abbreviations=abbreviations,
            mesh_terms=mesh_terms,
            tissue_terms=tissue_terms,
            tcga_projects=tcga_projects,
            gtex_tissues=gtex_tissues,
            data_modalities=data_modalities,
            modifier_terms=modifier_terms,
            exposure_terms=exposure_terms,
            intervention_terms=intervention_terms,
            outcome_terms=outcome_terms,
            study_design_terms=study_design_terms,
            publication_type_terms=publication_type_terms,
            concept_ids=concept_ids,
            confidences=confidences,
        )

    if not any(match.matched for match in provider_matches):
        warnings.append("未在医学词库索引中匹配到明确术语。")

    if not disease_terms and tissue_terms:
        warnings.append("仅识别到组织词，未识别到明确疾病词。")
    if target_context == "meta_analysis":
        tcga_projects = []
        gtex_tissues = []

    return TermLookupResult(
        original_term=query,
        normalized_term=normalized,
        matched=bool(matched_zh_terms or disease_terms or tissue_terms or data_modalities or modifier_terms),
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
        confidence=max(confidences) if confidences else (0.75 if registry_matched else 0.0),
        warnings=warnings,
    )


def _apply_provider_match(match: VocabularyProviderMatch, **targets: list[str] | list[float]) -> None:
    matched_zh_terms = targets["matched_zh_terms"]
    disease_terms = targets["disease_terms"]
    synonyms = targets["synonyms"]
    abbreviations = targets["abbreviations"]
    mesh_terms = targets["mesh_terms"]
    tissue_terms = targets["tissue_terms"]
    tcga_projects = targets["tcga_projects"]
    gtex_tissues = targets["gtex_tissues"]
    data_modalities = targets["data_modalities"]
    modifier_terms = targets["modifier_terms"]
    exposure_terms = targets["exposure_terms"]
    intervention_terms = targets["intervention_terms"]
    outcome_terms = targets["outcome_terms"]
    study_design_terms = targets["study_design_terms"]
    publication_type_terms = targets["publication_type_terms"]
    concept_ids = targets["concept_ids"]
    confidences = targets["confidences"]

    for override in match.overrides:
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
            confidences.append(override.confidence)  # type: ignore[union-attr]

    for concept in match.index_concepts:
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

    for concept in match.registry_concepts:
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


def _extend_unique(items: list[str], values: object) -> None:
    for value in values:  # type: ignore[union-attr]
        _append_unique(items, str(value))


def _append_unique(items: list[str], value: str) -> None:
    text = value.strip()
    key = text.lower()
    if text and key not in {item.lower() for item in items}:
        items.append(text)
