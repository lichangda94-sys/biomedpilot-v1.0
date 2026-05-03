from __future__ import annotations

from dataclasses import dataclass, field

from app.shared.query_intelligence import SearchTranslationDraft, build_search_translation_draft


DEFAULT_PLATFORM_TERMS = ("expression profiling", "transcriptome", "RNA-seq", "microarray")


@dataclass(frozen=True)
class TcgaProjectCandidate:
    project_id: str
    project_name: str
    primary_site: str
    disease_type: str
    mapping_status: str = "curated_term_mapping"


@dataclass(frozen=True)
class GtexTissueCandidate:
    tissue: str
    role: str = "normal_reference"
    mapping_status: str = "curated_term_mapping"


@dataclass(frozen=True)
class BioinformaticsQueryStrategy:
    original_question: str
    recognized_diseases_zh: tuple[str, ...]
    disease_terms: tuple[str, ...]
    platform_terms: tuple[str, ...]
    confirmed_geo_queries: tuple[str, ...]
    supplemental_geo_queries: tuple[str, ...]
    broad_query_guard_triggered: bool
    broad_query_requires_confirmation: bool
    tcga_project_candidates: tuple[TcgaProjectCandidate, ...]
    gtex_tissue_candidates: tuple[GtexTissueCandidate, ...]
    warnings: tuple[str, ...]
    translation_draft: SearchTranslationDraft
    audit: dict[str, object] = field(default_factory=dict)

    @property
    def geo_query_terms(self) -> tuple[str, ...]:
        return self.confirmed_geo_queries

    @property
    def gse_search_terms(self) -> tuple[str, ...]:
        return self.confirmed_geo_queries


def build_bioinformatics_query_strategy(question: str | SearchTranslationDraft) -> BioinformaticsQueryStrategy:
    draft = (
        question
        if isinstance(question, SearchTranslationDraft)
        else build_search_translation_draft(
            str(question),
            target_context="bioinformatics",
            target_database="geo",
            use_local_model=False,
            allow_network=False,
        )
    )
    disease_terms = _disease_terms(draft)
    platform_terms = _platform_terms(draft)
    confirmed = _disease_aware_queries(disease_terms, platform_terms)
    supplemental = _supplemental_queries(draft.geo_query_candidates, confirmed, platform_terms)
    broad_guard = not disease_terms and bool(platform_terms)
    warnings = list(draft.warnings)
    if broad_guard:
        warnings.append("未识别到明确疾病词，宽泛 GEO query 需要用户确认后再执行。")
    audit = {
        "term_sources": draft.audit.get("term_sources", []),
        "tcga_project_candidates": draft.audit.get("tcga_project_candidates", []),
        "gtex_tissue_candidates": draft.audit.get("gtex_tissue_candidates", []),
        "tissue_terms": draft.audit.get("tissue_terms", []),
        "context_output_policy": draft.audit.get("context_output_policy", {}),
        "pubmed_query_candidates_removed": draft.pubmed_query_candidates == [],
    }
    return BioinformaticsQueryStrategy(
        original_question=draft.original_question,
        recognized_diseases_zh=tuple(draft.disease_terms_zh),
        disease_terms=tuple(disease_terms),
        platform_terms=tuple(platform_terms),
        confirmed_geo_queries=tuple(confirmed),
        supplemental_geo_queries=tuple(supplemental),
        broad_query_guard_triggered=broad_guard,
        broad_query_requires_confirmation=broad_guard,
        tcga_project_candidates=tuple(_tcga_candidates(draft.audit.get("tcga_project_candidates", []))),
        gtex_tissue_candidates=tuple(_gtex_candidates(draft.audit.get("gtex_tissue_candidates", []))),
        warnings=tuple(_unique(warnings)),
        translation_draft=draft,
        audit=audit,
    )


def _disease_terms(draft: SearchTranslationDraft) -> list[str]:
    terms = [*draft.disease_terms_en, *draft.main_concepts_en]
    return _unique(term for term in terms if not _is_database_or_tissue_label(term))


def _platform_terms(draft: SearchTranslationDraft) -> list[str]:
    return _unique([*draft.data_type_terms_en, *DEFAULT_PLATFORM_TERMS])


def _disease_aware_queries(disease_terms: list[str], platform_terms: list[str]) -> list[str]:
    queries: list[str] = []
    for disease in disease_terms[:6]:
        for platform in platform_terms[:4]:
            queries.append(_and_query(disease, platform))
    return _unique(queries)


def _supplemental_queries(existing: list[str], confirmed: list[str], platform_terms: list[str]) -> list[str]:
    confirmed_keys = {query.lower() for query in confirmed}
    supplemental = [query for query in existing if query.lower() not in confirmed_keys]
    supplemental.extend(platform_terms)
    return _unique(supplemental)


def _and_query(left: str, right: str) -> str:
    return f"{_quote_if_needed(left)} AND {_quote_if_needed(right)}"


def _quote_if_needed(value: str) -> str:
    text = value.strip().strip('"')
    return f'"{text}"' if " " in text or "-" in text else text


def _tcga_candidates(values: object) -> list[TcgaProjectCandidate]:
    return [_tcga_candidate(str(value)) for value in values]  # type: ignore[union-attr]


def _tcga_candidate(project_id: str) -> TcgaProjectCandidate:
    metadata = {
        "TCGA-GBM": ("Glioblastoma Multiforme", "Brain", "Glioblastoma"),
        "TCGA-LGG": ("Brain Lower Grade Glioma", "Brain", "Lower Grade Glioma"),
        "TCGA-THCA": ("Thyroid Carcinoma", "Thyroid", "Thyroid Carcinoma"),
        "TCGA-ESCA": ("Esophageal Carcinoma", "Esophagus", "Esophageal Carcinoma"),
        "TCGA-LUAD": ("Lung Adenocarcinoma", "Lung", "Lung Adenocarcinoma"),
        "TCGA-LUSC": ("Lung Squamous Cell Carcinoma", "Lung", "Lung Squamous Cell Carcinoma"),
        "TCGA-LIHC": ("Liver Hepatocellular Carcinoma", "Liver", "Hepatocellular Carcinoma"),
        "TCGA-STAD": ("Stomach Adenocarcinoma", "Stomach", "Stomach Adenocarcinoma"),
        "TCGA-COAD": ("Colon Adenocarcinoma", "Colon", "Colon Adenocarcinoma"),
        "TCGA-READ": ("Rectum Adenocarcinoma", "Rectum", "Rectum Adenocarcinoma"),
        "TCGA-PAAD": ("Pancreatic Adenocarcinoma", "Pancreas", "Pancreatic Adenocarcinoma"),
        "TCGA-BRCA": ("Breast Invasive Carcinoma", "Breast", "Breast Carcinoma"),
        "TCGA-PRAD": ("Prostate Adenocarcinoma", "Prostate", "Prostate Adenocarcinoma"),
        "TCGA-OV": ("Ovarian Serous Cystadenocarcinoma", "Ovary", "Ovarian Carcinoma"),
        "TCGA-CESC": ("Cervical Squamous Cell Carcinoma and Endocervical Adenocarcinoma", "Cervix", "Cervical Carcinoma"),
        "TCGA-UCEC": ("Uterine Corpus Endometrial Carcinoma", "Uterus", "Endometrial Carcinoma"),
        "TCGA-KIRC": ("Kidney Renal Clear Cell Carcinoma", "Kidney", "Renal Cell Carcinoma"),
        "TCGA-KIRP": ("Kidney Renal Papillary Cell Carcinoma", "Kidney", "Renal Cell Carcinoma"),
        "TCGA-KICH": ("Kidney Chromophobe", "Kidney", "Kidney Chromophobe"),
        "TCGA-BLCA": ("Bladder Urothelial Carcinoma", "Bladder", "Urothelial Carcinoma"),
        "TCGA-SKCM": ("Skin Cutaneous Melanoma", "Skin", "Melanoma"),
    }
    name, site, disease = metadata.get(project_id, (project_id, "", ""))
    return TcgaProjectCandidate(
        project_id=project_id,
        project_name=name,
        primary_site=site,
        disease_type=disease,
        mapping_status="curated_term_mapping" if project_id in metadata else "unverified_term_mapping",
    )


def _gtex_candidates(values: object) -> list[GtexTissueCandidate]:
    return [GtexTissueCandidate(tissue=str(value)) for value in values]  # type: ignore[union-attr]


def _is_database_or_tissue_label(term: str) -> bool:
    lowered = term.lower()
    return lowered.startswith(("tcga-", "gtex")) or lowered in {"geo", "gse", "tcga", "normal tissue", "tumor tissue"}


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
