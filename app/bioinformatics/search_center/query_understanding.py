from __future__ import annotations

from app.shared.query_intelligence import LocalModelConfig, build_search_translation_draft
from app.shared.search_context import BIOINFORMATICS_SEARCH_CONTEXT, filter_search_translation_draft_by_context

from .models import BIOINFORMATICS_ALLOWED_SOURCES, StructuredBioinformaticsQuery


class QueryUnderstandingLayer:
    def understand(
        self,
        query: str,
        *,
        use_local_model: bool = False,
        local_model_config: LocalModelConfig | None = None,
        gateway_module: str = "bioinformatics",
        gateway_task_type: str = "bio_generate_dataset_query_draft",
    ) -> StructuredBioinformaticsQuery:
        cleaned = query.strip()
        draft = build_search_translation_draft(
            cleaned,
            target_context="bioinformatics",
            target_database="geo",
            use_local_model=use_local_model,
            allow_network=False,
            config=local_model_config,
            gateway_module=gateway_module if use_local_model else "",
            gateway_task_type=gateway_task_type if use_local_model else "",
        )
        draft = filter_search_translation_draft_by_context(draft, BIOINFORMATICS_SEARCH_CONTEXT)
        lookup = _lookup_payload(draft)
        disease_terms_missing = not draft.disease_terms_en and not draft.main_concepts_en
        disease_en = _unique([*draft.disease_terms_en, *draft.main_concepts_en])
        synonyms = _unique([term for term in draft.main_concepts_en if term not in disease_en])
        abbreviations = _unique([*lookup.get("abbreviations", []), *_abbreviations([*disease_en, *draft.main_concepts_en])])
        tissue_terms = _unique([*lookup.get("tissue_terms", []), *_tissue_terms(cleaned, disease_en, draft.database_terms)])
        data_modalities = _unique([*draft.data_type_terms_en, "expression profiling", "RNA-seq", "microarray", "transcriptome"])
        tcga_project_ids = _unique([*lookup.get("tcga_project_candidates", []), *_tcga_projects(cleaned, [*disease_en, *draft.database_terms])])
        gtex_tissues = _unique([*lookup.get("gtex_tissue_candidates", []), *_gtex_tissues(cleaned, [*disease_en, *tissue_terms, *draft.database_terms])])
        broad_geo_query = _build_geo_query((), data_modalities)
        geo_queries = () if disease_terms_missing else (_build_geo_query(disease_en, data_modalities),)
        search_execution_status = "disease_terms_missing" if disease_terms_missing else "draft_only"
        guard_warnings = (
            ("未识别出明确疾病词，当前 query 为宽泛表达谱检索，结果可能过宽。",)
            if disease_terms_missing
            else ()
        )
        warnings = tuple(dict.fromkeys([*draft.warnings, *guard_warnings, *_mapping_warnings(tcga_project_ids, gtex_tissues)]))
        return StructuredBioinformaticsQuery(
            original_query_zh=cleaned,
            disease_terms_zh=tuple(draft.disease_terms_zh or draft.main_concepts_zh),
            disease_terms_en=disease_en,
            synonyms=synonyms,
            abbreviations=abbreviations,
            tissue_terms=tissue_terms,
            species=("Homo sapiens",),
            data_modalities=data_modalities,
            analysis_intent=_analysis_intent(cleaned),
            allowed_sources=BIOINFORMATICS_ALLOWED_SOURCES,
            geo_query_candidates=geo_queries,
            tcga_project_ids=tcga_project_ids,
            gtex_tissues=() if disease_terms_missing else gtex_tissues,
            search_execution_status=search_execution_status,
            broad_query_guard=disease_terms_missing,
            warnings=warnings,
            metadata={
                "search_translation_draft": draft,
                "local_model_status": draft.local_model_status,
                "local_model_used": draft.local_model_used,
                "rejected_terms": draft.rejected_terms,
                "disease_terms_missing": disease_terms_missing,
                "broad_geo_query": broad_geo_query,
                "broad_geo_query_label": f"宽泛补充检索｜{broad_geo_query}",
            },
        )


def _tcga_projects(original: str, terms: list[str]) -> tuple[str, ...]:
    text = " ".join([original, *terms]).lower()
    projects: list[str] = []
    if any(token in text for token in ("脑胶质瘤", "胶质瘤", "glioma", "glioblastoma", "gbm", "lgg")):
        projects.extend(["TCGA-GBM", "TCGA-LGG"])
    if any(token in text for token in ("甲状腺", "thyroid", "thca", "ptc")):
        projects.append("TCGA-THCA")
    if any(token in text for token in ("食管", "食道", "esophageal", "oesophageal", "escc")):
        projects.append("TCGA-ESCA")
    return _unique(projects)


def _gtex_tissues(original: str, terms: list[str]) -> tuple[str, ...]:
    text = " ".join([original, *terms]).lower()
    tissues: list[str] = []
    if any(token in text for token in ("脑胶质瘤", "胶质瘤", "glioma", "glioblastoma", "brain", "gbm", "lgg")):
        tissues.append("Brain")
    if any(token in text for token in ("甲状腺", "thyroid", "thca", "ptc")):
        tissues.append("Thyroid")
    if any(token in text for token in ("食管", "食道", "esophageal", "oesophageal", "escc")):
        tissues.append("Esophagus")
    return _unique(tissues or ["Normal tissue"])


def _tissue_terms(original: str, disease_terms: tuple[str, ...], database_terms: list[str]) -> tuple[str, ...]:
    text = " ".join([original, *disease_terms, *database_terms]).lower()
    tissues: list[str] = []
    if "brain" in text or "脑胶质瘤" in text or "胶质瘤" in text or "glioma" in text:
        tissues.extend(["brain", "brain tissue", "tumor tissue", "normal tissue"])
    if "thyroid" in text or "甲状腺" in text:
        tissues.extend(["thyroid tissue", "tumor tissue", "normal tissue"])
    if "esophageal" in text or "oesophageal" in text or "食管" in text or "食道" in text:
        tissues.extend(["esophageal tissue", "tumor tissue", "normal tissue"])
    return _unique(tissues or ["tumor tissue", "normal tissue"])


def _abbreviations(terms: list[str]) -> tuple[str, ...]:
    values = [term for term in terms if term.isupper() and 2 <= len(term) <= 12]
    if any("glioma" in term.lower() or "glioblastoma" in term.lower() for term in terms):
        values.extend(["GBM", "LGG"])
    if any("thyroid" in term.lower() for term in terms):
        values.extend(["THCA", "PTC"])
    if any("esophageal" in term.lower() or "oesophageal" in term.lower() for term in terms):
        values.append("ESCC")
    return _unique(values)


def _analysis_intent(original: str) -> str:
    text = original.lower()
    if any(token in text for token in ("生存", "survival", "预后")):
        return "survival_analysis"
    if any(token in text for token in ("差异", "表达", "deg", "expression")):
        return "differential_expression"
    return "dataset_discovery"


def _build_geo_query(disease_terms: tuple[str, ...], modalities: tuple[str, ...]) -> str:
    disease = " OR ".join(f'"{term}"' for term in disease_terms[:8])
    modality = " OR ".join(f'"{term}"' for term in modalities[:6])
    if disease:
        return f"({disease}) AND ({modality}) AND GSE[ETYP] AND Homo sapiens[Organism]"
    return f"({modality}) AND GSE[ETYP] AND Homo sapiens[Organism]"


def _mapping_warnings(tcga_projects: tuple[str, ...], gtex_tissues: tuple[str, ...]) -> tuple[str, ...]:
    warnings: list[str] = []
    if not tcga_projects:
        warnings.append("未映射到明确 TCGA 癌种项目。")
    if not gtex_tissues:
        warnings.append("未映射到明确 GTEx 正常组织。")
    return tuple(warnings)


def _unique(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        text = str(value).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            items.append(text)
    return tuple(items)


def _lookup_payload(draft: object) -> dict[str, list[str]]:
    audit = getattr(draft, "audit", {})
    payload = audit.get("term_lookup", {}) if isinstance(audit, dict) else {}
    return payload if isinstance(payload, dict) else {}
