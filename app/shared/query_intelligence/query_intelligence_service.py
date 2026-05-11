from __future__ import annotations

from app.shared.ai_gateway import AIGateway
from app.shared.query_intelligence.local_model_bridge import (
    describe_local_model_components,
    generate_search_translation_candidates,
)
from app.shared.query_intelligence.medical_terms import lookup_medical_terms
from app.shared.query_intelligence.medical_question_parser import (
    detect_language,
    normalize_question,
    parse_medical_question,
)
from app.shared.query_intelligence.query_intelligence_models import (
    LocalModelConfig,
    QueryIntelligenceInput,
    QueryIntelligenceResult,
    SearchTranslationDraft,
)


def analyze_medical_question(payload: QueryIntelligenceInput | str, **kwargs: object) -> QueryIntelligenceResult:
    request = payload if isinstance(payload, QueryIntelligenceInput) else QueryIntelligenceInput(str(payload), **kwargs)
    normalized = normalize_question(request.original_question)
    language = detect_language(normalized, request.language_hint)
    concepts, domain, intent, analysis_type, confidence = parse_medical_question(
        normalized,
        target_context=request.target_context,
        optional_domain=request.optional_domain,
    )
    model_status = describe_local_model_components()
    warnings: list[str] = []
    if not concepts:
        warnings.append("本地词库没有识别到明确医学概念，已保留原始问题供人工调整。")
    if model_status["status"] == "fallback_registry_only":
        warnings.append("Ollama/Translator/Media 不可用或未接入，本次仅使用本地词库和规则。")
    return QueryIntelligenceResult(
        original_question=request.original_question,
        detected_language=language,
        normalized_question=normalized,
        detected_domain=domain,
        detected_intent=intent,
        detected_review_or_analysis_type=request.optional_review_type or analysis_type,
        concepts=concepts,
        warnings=tuple(warnings),
        confidence=confidence,
        local_model_status=model_status["status"],
        metadata={"local_model_components": model_status, "target_context": request.target_context},
    )


def build_search_translation_draft(
    original_question: str,
    target_context: str = "bioinformatics",
    target_database: str = "geo",
    use_local_model: bool = False,
    allow_network: bool = False,
    config: LocalModelConfig | None = None,
    gateway_module: str = "",
    gateway_task_type: str = "",
    ai_gateway: AIGateway | None = None,
) -> SearchTranslationDraft:
    resolved_config = config or LocalModelConfig()
    intelligence = analyze_medical_question(
        QueryIntelligenceInput(original_question, language_hint="auto", target_context=target_context)
    )
    registry = _registry_translation_seed(intelligence)
    term_lookup = lookup_medical_terms(original_question, target_context=target_context)
    if term_lookup.matched:
        registry["main_concepts_zh"] = _unique([*registry["main_concepts_zh"], *term_lookup.matched_zh_terms])
        registry["main_concepts_en"] = _unique(
            [*term_lookup.disease_terms_en, *term_lookup.synonyms_en, *registry["main_concepts_en"]]
        )
        registry["modifier_terms_en"] = _unique([*registry["modifier_terms_en"], *term_lookup.modifier_terms_en])
        registry["data_type_terms_en"] = _unique([*term_lookup.data_modality_terms, *registry["data_type_terms_en"]])
    term_lookup_audit = _term_lookup_audit_for_context(term_lookup.to_dict(), target_context)
    audit: dict[str, object] = {
        "registry_concepts": [concept.to_dict() for concept in intelligence.concepts],
        "allow_network": allow_network,
        "term_lookup": term_lookup_audit,
        "term_sources": term_lookup.term_sources,
        "medical_terms_index_scope": "BioMedPilot shared medical vocabulary",
        "context_output_policy": _context_output_policy(target_context),
        "tcga_project_candidates": term_lookup.tcga_project_candidates if target_context == "bioinformatics" else [],
        "tcga_primary_site_candidates": term_lookup.tcga_primary_site_candidates if target_context == "bioinformatics" else [],
        "gtex_tissue_candidates": term_lookup.gtex_tissue_candidates if target_context == "bioinformatics" else [],
        "tissue_terms": term_lookup.tissue_terms if target_context == "bioinformatics" else [],
    }
    warnings = list(intelligence.warnings)
    warnings.extend(term_lookup.warnings)
    rejected_terms: list[str] = []
    candidate_terms: list[str] = []
    local_model_status = "fallback_registry_only"
    local_model_used = False
    model_translation = None

    if not use_local_model:
        local_model_status = intelligence.local_model_status
        warnings.append("本地模型未调用，本次仅使用本地词库生成检索词草稿。")
    elif not resolved_config.enabled:
        local_model_status = "disabled_by_config"
        warnings.append("本地模型调用被配置关闭，本次仅使用本地词库生成检索词草稿。")
    else:
        model_translation = generate_search_translation_candidates(
            original_question,
            target_context,
            target_database,
            resolved_config,
            gateway_module=gateway_module,
            gateway_task_type=gateway_task_type,
            ai_gateway=ai_gateway,
        )
        local_model_status = (
            "fallback_registry_only"
            if model_translation.status in {"unavailable", "missing_gateway_context_fallback_registry"}
            else model_translation.status
        )
        local_model_used = model_translation.status == "called_success"
        audit["local_model"] = {
            "model_name": model_translation.model_name,
            "provider_name": model_translation.provider_name or resolved_config.provider,
            "status": model_translation.status,
            "resolved_status": local_model_status,
            "gateway_status": model_translation.gateway_status,
            "fallback_used": model_translation.fallback_used,
            "output_char_count": model_translation.output_char_count,
            "output_sha256": model_translation.output_sha256,
            "warnings": list(model_translation.warnings),
        }
        warnings.extend(model_translation.warnings)
        if model_translation.status == "called_success":
            if _has_authoritative_vocabulary_match(term_lookup):
                registry["main_concepts_zh"] = _unique([*registry["main_concepts_zh"], *model_translation.parsed_json.get("main_concepts_zh", [])])
                registry["main_concepts_en"] = _unique([*registry["main_concepts_en"], *model_translation.parsed_json.get("main_concepts_en", [])])
                registry["modifier_terms_zh"] = _unique([*registry["modifier_terms_zh"], *model_translation.parsed_json.get("modifier_terms_zh", [])])
                registry["modifier_terms_en"] = _unique([*registry["modifier_terms_en"], *model_translation.parsed_json.get("modifier_terms_en", [])])
                registry["data_type_terms_en"] = _unique([*registry["data_type_terms_en"], *model_translation.parsed_json.get("data_type_terms_en", [])])
                registry["pubmed_query_candidates"] = _unique([*registry["pubmed_query_candidates"], *model_translation.candidate_pubmed_queries])
                registry["geo_query_candidates"] = _unique([*registry["geo_query_candidates"], *model_translation.candidate_geo_queries])
            else:
                candidate_terms = _validated_model_candidate_terms(
                    original_question,
                    [
                        *model_translation.parsed_json.get("main_concepts_en", []),
                        *model_translation.parsed_json.get("candidate_terms", []),
                    ],
                    target_context,
                )
                audit["local_model"]["candidate_terms"] = candidate_terms
                audit["local_model"]["candidate_policy"] = "unknown_term_candidates_only_not_final_query"
                warnings.append("本地模型仅生成未知词候选；候选未直接写入最终检索式。")

    registry = _suppress_bound_modifier_disease_terms(original_question, registry, term_lookup.modifier_terms_en)

    if not registry["pubmed_query_candidates"]:
        registry["pubmed_query_candidates"] = _build_pubmed_query_candidates(
            registry["main_concepts_en"], registry["modifier_terms_en"]
        )
    if not registry["geo_query_candidates"]:
        registry["geo_query_candidates"] = _build_geo_query_candidates(
            registry["main_concepts_en"], registry["modifier_terms_en"], registry["data_type_terms_en"]
        )

    guarded = _apply_disease_guard(original_question, registry)
    rejected_terms.extend(guarded["rejected_terms"])
    if rejected_terms:
        warnings.append("Disease guard 已过滤与原始问题不匹配的串病种词。")
    audit["rejected_terms"] = [
        {"term": term, "reason": _rejection_reason(original_question, term)}
        for term in rejected_terms
    ]
    disease_terms_zh = _unique([*_terms_by_semantic_group(intelligence, "disease", "zh"), *term_lookup.matched_zh_terms])
    disease_terms_en = _suppress_values(
        _unique([*_terms_by_semantic_group(intelligence, "disease", "en"), *term_lookup.disease_terms_en]),
        _bound_modifier_disease_terms(original_question, term_lookup.modifier_terms_en),
    )
    mesh_terms = _unique([*intelligence.mesh_terms, *term_lookup.mesh_terms])
    database_terms = _database_terms_for_context(intelligence, term_lookup, target_context)
    pubmed_query_candidates = list(guarded["pubmed_query_candidates"])
    geo_query_candidates = list(guarded["geo_query_candidates"])
    if target_context == "bioinformatics":
        pubmed_query_candidates = []
    elif target_context == "meta_analysis":
        geo_query_candidates = []
        pubmed_query_candidates = _build_pubmed_query_candidates_with_mesh(
            mesh_terms,
            guarded["main_concepts_en"],
            guarded["modifier_terms_en"],
        )
    return SearchTranslationDraft(
        original_question=original_question,
        detected_language=intelligence.detected_language,
        target_context=target_context,
        target_database=target_database,
        normalized_question=intelligence.normalized_question,
        review_or_analysis_intent=intelligence.detected_review_or_analysis_type,
        main_concepts_zh=guarded["main_concepts_zh"],
        main_concepts_en=guarded["main_concepts_en"],
        disease_terms_zh=disease_terms_zh,
        disease_terms_en=disease_terms_en,
        exposure_terms_zh=_terms_by_semantic_group(intelligence, "exposure", "zh"),
        exposure_terms_en=_unique([*_terms_by_semantic_group(intelligence, "exposure", "en"), *term_lookup.exposure_terms]),
        outcome_terms_zh=_terms_by_semantic_group(intelligence, "outcome", "zh"),
        outcome_terms_en=_unique([*_terms_by_semantic_group(intelligence, "outcome", "en"), *term_lookup.outcome_terms]),
        modifier_terms_zh=guarded["modifier_terms_zh"],
        modifier_terms_en=guarded["modifier_terms_en"],
        data_type_terms_en=guarded["data_type_terms_en"],
        mesh_terms=mesh_terms,
        database_terms=database_terms,
        pubmed_query_candidates=pubmed_query_candidates,
        geo_query_candidates=geo_query_candidates,
        rejected_terms=rejected_terms,
        warnings=_unique(warnings),
        confidence=intelligence.confidence,
        local_model_status=local_model_status,
        local_model_used=local_model_used,
        search_execution_status="draft_only",
        audit=audit,
        candidate_terms=candidate_terms,
    )


def _validated_model_candidate_terms(
    original_question: str,
    candidate_terms: list[str],
    target_context: str,
) -> list[str]:
    payload = {
        "main_concepts_zh": [],
        "main_concepts_en": _unique(candidate_terms),
        "modifier_terms_zh": [],
        "modifier_terms_en": [],
        "data_type_terms_en": [],
        "pubmed_query_candidates": [],
        "geo_query_candidates": [],
    }
    guarded = _apply_disease_guard(original_question, payload)
    validated: list[str] = []
    for term in guarded["main_concepts_en"]:
        if _is_forbidden_candidate_term(term):
            continue
        lookup = lookup_medical_terms(term, target_context=target_context)
        if _has_authoritative_vocabulary_match(lookup):
            validated.append(term)
    return _unique(validated)


def _has_authoritative_vocabulary_match(term_lookup: object) -> bool:
    return bool(
        getattr(term_lookup, "matched_zh_terms", [])
        or getattr(term_lookup, "disease_terms_en", [])
        or getattr(term_lookup, "tissue_terms", [])
        or getattr(term_lookup, "mesh_terms", [])
        or getattr(term_lookup, "exposure_terms", [])
        or getattr(term_lookup, "outcome_terms", [])
        or getattr(term_lookup, "study_design_terms", [])
        or getattr(term_lookup, "publication_type_terms", [])
        or getattr(term_lookup, "concept_ids", [])
    )


def _is_forbidden_candidate_term(term: str) -> bool:
    lowered = term.lower()
    return any(token in lowered for token in ("tcga", "gtex", "geo", "gse"))


def _terms_by_semantic_group(intelligence: QueryIntelligenceResult, semantic_group: str, language: str) -> list[str]:
    terms: list[str] = []
    for concept in intelligence.concepts:
        if concept.semantic_group == semantic_group:
            terms.extend(concept.zh_terms if language == "zh" else [*concept.en_terms, *concept.synonyms])
    return _unique(terms)


def _registry_translation_seed(intelligence: QueryIntelligenceResult) -> dict[str, list[str]]:
    main_zh: list[str] = []
    main_en: list[str] = []
    modifier_zh: list[str] = []
    modifier_en: list[str] = []
    data_type_en: list[str] = []
    for concept in intelligence.concepts:
        if concept.semantic_group == "modifier":
            modifier_zh.extend(concept.zh_terms)
            modifier_en.extend(concept.en_terms)
        elif concept.semantic_group == "dataset":
            data_type_en.extend(term for term in concept.en_terms if term not in {"dataset", "GEO", "GSE"})
        elif concept.semantic_group == "disease":
            main_zh.extend(concept.zh_terms)
            main_en.extend([*concept.en_terms, *concept.synonyms])
    main_zh = _unique(main_zh)
    main_en = _unique(main_en)
    modifier_zh = _unique(modifier_zh)
    modifier_en = _unique(modifier_en)
    data_type_en = _unique(data_type_en or ["expression profiling", "transcriptome", "RNA-seq", "microarray"])
    return {
        "main_concepts_zh": main_zh,
        "main_concepts_en": main_en,
        "modifier_terms_zh": modifier_zh,
        "modifier_terms_en": modifier_en,
        "data_type_terms_en": data_type_en,
        "pubmed_query_candidates": _build_pubmed_query_candidates(main_en, modifier_en),
        "geo_query_candidates": _build_geo_query_candidates(main_en, modifier_en, data_type_en),
    }


def _build_pubmed_query_candidates(main_terms: list[str], modifier_terms: list[str]) -> list[str]:
    if not main_terms:
        return []
    modifier = modifier_terms[0] if modifier_terms else ""
    queries = [" ".join(term for term in (main_terms[0], modifier) if term)]
    for disease in main_terms[:4]:
        if modifier:
            queries.append(f'"{disease}" AND "{modifier}"' if " " in disease else f'{disease} AND "{modifier}"')
        else:
            queries.append(f'"{disease}"' if " " in disease else disease)
    return _unique(queries)


def _build_pubmed_query_candidates_with_mesh(
    mesh_terms: list[str],
    main_terms: list[str],
    modifier_terms: list[str],
) -> list[str]:
    queries: list[str] = []
    modifier = modifier_terms[0] if modifier_terms else ""
    for mesh in mesh_terms[:4]:
        base = f'"{mesh}"[Mesh]'
        queries.append(f"{base} AND \"{modifier}\"" if modifier else base)
    queries.extend(_build_pubmed_query_candidates(main_terms, modifier_terms))
    return _unique(queries)


def _build_geo_query_candidates(main_terms: list[str], modifier_terms: list[str], data_type_terms: list[str]) -> list[str]:
    if not main_terms:
        return []
    modifier = modifier_terms[0] if modifier_terms else ""
    queries: list[str] = []
    for disease in main_terms[:4]:
        if modifier:
            queries.append(f'"{modifier} {disease}"')
            queries.append(f'"{disease}" AND "{modifier}"' if " " in disease else f'{disease} AND "{modifier}"')
        for data_type in data_type_terms[:4]:
            queries.append(f'"{disease}" AND "{data_type}"' if " " in disease else f"{disease} AND {data_type}")
    return _unique(queries)


def _apply_disease_guard(original_question: str, payload: dict[str, list[str]]) -> dict[str, list[str]]:
    guarded = {key: list(value) for key, value in payload.items()}
    forbidden = _forbidden_terms_for_question(original_question)
    rejected: list[str] = []
    if not forbidden:
        guarded["rejected_terms"] = []
        return guarded
    for key in (
        "main_concepts_en",
        "modifier_terms_en",
        "data_type_terms_en",
        "pubmed_query_candidates",
        "geo_query_candidates",
    ):
        kept: list[str] = []
        for value in guarded[key]:
            matched = _matched_forbidden_terms(value, forbidden)
            if matched:
                rejected.extend(matched)
            else:
                kept.append(value)
        guarded[key] = _unique(kept)
    guarded["rejected_terms"] = _unique(rejected)
    return guarded


def _database_terms_for_context(
    intelligence: QueryIntelligenceResult,
    term_lookup: object,
    target_context: str,
) -> list[str]:
    if target_context == "bioinformatics":
        return _unique(
            [
                *intelligence.database_terms,
                *getattr(term_lookup, "tcga_project_candidates", []),
                *getattr(term_lookup, "tcga_primary_site_candidates", []),
                *getattr(term_lookup, "gtex_tissue_candidates", []),
                *getattr(term_lookup, "tissue_terms", []),
            ]
        )
    if target_context == "meta_analysis":
        forbidden = ("tcga", "gtex", "geo", "gse")
        return [
            term
            for term in _unique([*intelligence.database_terms])
            if not any(token in term.lower() for token in forbidden)
        ]
    return _unique([*intelligence.database_terms])


def _term_lookup_audit_for_context(payload: dict[str, object], target_context: str) -> dict[str, object]:
    result = dict(payload)
    if target_context == "bioinformatics":
        for key in (
            "exposure_terms",
            "intervention_terms",
            "outcome_terms",
            "study_design_terms",
            "publication_type_terms",
        ):
            result.pop(key, None)
    elif target_context == "meta_analysis":
        for key in (
            "tissue_terms",
            "tcga_project_candidates",
            "tcga_primary_site_candidates",
            "gtex_tissue_candidates",
            "data_modality_terms",
        ):
            result.pop(key, None)
    return result


def _context_output_policy(target_context: str) -> dict[str, object]:
    if target_context == "bioinformatics":
        return {
            "consumes": [
                "disease_terms_en",
                "tissue_terms",
                "data_modality_terms",
                "tcga_project_candidates",
                "tcga_primary_site_candidates",
                "gtex_tissue_candidates",
                "geo_query_terms",
            ],
            "blocks": [
                "pubmed_query_candidates",
                "web_of_science_query_candidates",
                "embase_query_candidates",
                "cnki_query_candidates",
            ],
        }
    if target_context == "meta_analysis":
        return {
            "consumes": [
                "disease_terms_en",
                "synonyms_en",
                "abbreviations",
                "mesh_terms",
                "exposure_terms",
                "intervention_terms",
                "outcome_terms",
                "study_design_terms",
                "publication_type_terms",
            ],
            "blocks": [
                "tcga_project_candidates",
                "tcga_primary_site_candidates",
                "gtex_tissue_candidates",
                "geo_query_candidates",
            ],
        }
    return {"consumes": [], "blocks": []}


def _suppress_bound_modifier_disease_terms(
    original_question: str,
    payload: dict[str, list[str]],
    modifier_terms: list[str],
) -> dict[str, list[str]]:
    forbidden = _bound_modifier_disease_terms(original_question, modifier_terms)
    if not forbidden:
        return payload
    updated = {key: list(value) for key, value in payload.items()}
    updated["main_concepts_en"] = _suppress_values(updated["main_concepts_en"], forbidden)
    return updated


def _bound_modifier_disease_terms(original_question: str, modifier_terms: list[str]) -> tuple[str, ...]:
    text = original_question.lower()
    modifiers = " ".join(modifier_terms).lower()
    if ("低分化" in original_question or "poorly differentiated" in modifiers) and ("甲状腺" in original_question or "thyroid" in text):
        return ("poorly differentiated thyroid cancer", "poorly differentiated thyroid carcinoma")
    return ()


def _suppress_values(values: list[str], forbidden: tuple[str, ...]) -> list[str]:
    if not forbidden:
        return values
    forbidden_lower = {term.lower() for term in forbidden}
    return [value for value in values if value.lower() not in forbidden_lower]


def _forbidden_terms_for_question(original_question: str) -> tuple[str, ...]:
    text = original_question.lower()
    if any(token in text for token in ("食管", "食道", "escc", "esophageal", "oesophageal")):
        return (
            "thyroid cancer",
            "thyroid carcinoma",
            "thyroid neoplasm",
            "papillary thyroid carcinoma",
            "PTC",
            "THCA",
            "TCGA-THCA",
        )
    if any(token in text for token in ("甲状腺", "ptc", "thca", "thyroid")):
        return (
            "esophageal cancer",
            "esophageal carcinoma",
            "esophageal squamous cell carcinoma",
            "oesophageal squamous cell carcinoma",
            "ESCC",
        )
    return ()


def _rejection_reason(original_question: str, term: str) -> str:
    text = original_question.lower()
    lowered = term.lower()
    if any(token in text for token in ("食管", "食道", "escc", "esophageal", "oesophageal")) and any(
        token in lowered for token in ("thyroid", "ptc", "thca", "tcga-thca")
    ):
        return "disease_guard_esophageal_question_blocks_thyroid_terms"
    if any(token in text for token in ("甲状腺", "ptc", "thca", "thyroid")) and any(
        token in lowered for token in ("escc", "esophageal", "oesophageal")
    ):
        return "disease_guard_thyroid_question_blocks_esophageal_terms"
    return "disease_guard_filtered_unmatched_disease_term"


def _matched_forbidden_terms(value: str, forbidden_terms: tuple[str, ...]) -> list[str]:
    lowered = value.lower()
    return [term for term in forbidden_terms if term.lower() in lowered]


def _unique(values: object) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:  # type: ignore[union-attr]
        text = str(value).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            items.append(text)
    return items
