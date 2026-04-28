"""Chinese concept matching helpers for the TCGA/GDC, GTEx, and future GEO concept layer."""

from __future__ import annotations

import csv
from pathlib import Path

from tcga_gtex.lexicon import CHINESE_CONCEPT_TERMS_CSV, CONCEPT_CATALOG_CSV
from tcga_gtex.models import QueryMapping
from tcga_gtex.search.source_adapters import (
    map_concept_to_geo_query_terms,
    map_concept_to_gtex_filters,
    map_concept_to_tcga_filters,
)


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def match_chinese_concepts(query: str) -> list[dict[str, str]]:
    """Return matched Chinese concept lexicon rows for a free-text query."""
    normalized = query.strip().lower()
    if not normalized:
        return []

    rows = _load_csv(Path(CHINESE_CONCEPT_TERMS_CSV))
    matches = [row for row in rows if row["is_active"] == "true" and row["term_zh"].lower() in normalized]
    matches = sorted(matches, key=lambda row: (-len(row["term_zh"]), int(row["priority"])))

    filtered_matches: list[dict[str, str]] = []
    for row in matches:
        row_term = row["term_zh"].lower()
        overshadowed = False
        for kept in filtered_matches:
            kept_term = kept["term_zh"].lower()
            if row["category_zh"] != kept["category_zh"]:
                continue
            if row["concept_id"] == kept["concept_id"]:
                continue
            if row_term in kept_term and len(kept_term) > len(row_term):
                overshadowed = True
                break
        if not overshadowed:
            filtered_matches.append(row)

    return filtered_matches


def build_query_mapping_from_chinese(query: str) -> QueryMapping:
    """Build a minimal concept-aware query mapping from Chinese concept matches."""
    concept_rows = {row["concept_id"]: row for row in _load_csv(Path(CONCEPT_CATALOG_CSV))}
    matches = match_chinese_concepts(query)
    concept_ids: list[str] = []
    concept_categories: list[str] = []
    matched_terms_zh: list[str] = []
    query_terms_en: list[str] = []
    disease_terms: list[str] = []
    tissue_terms: list[str] = []
    sample_type_terms: list[str] = []
    data_type_terms: list[str] = []

    for row in matches:
        concept_id = row["concept_id"]
        if concept_id not in concept_ids:
            concept_ids.append(concept_id)
        if row["term_zh"] not in matched_terms_zh:
            matched_terms_zh.append(row["term_zh"])

        concept = concept_rows.get(concept_id)
        if not concept:
            continue
        category = concept["concept_category"]
        if category not in concept_categories:
            concept_categories.append(category)
        concept_en = concept["concept_en"]
        if concept_en not in query_terms_en:
            query_terms_en.append(concept_en)

        if category == "disease":
            disease_terms.append(concept_en)
        elif category == "tissue":
            tissue_terms.append(concept_en)
        elif category == "sample_type":
            sample_type_terms.append(concept_en)
        elif category in {"analysis_resource", "access"}:
            data_type_terms.append(concept_en)

    return QueryMapping(
        raw_query=query,
        normalized_query=query.strip(),
        concept_ids=concept_ids,
        concept_categories=concept_categories,
        matched_terms_zh=matched_terms_zh,
        query_terms_en=query_terms_en,
        query_terms_zh=matched_terms_zh,
        disease_terms=disease_terms,
        tissue_terms=tissue_terms,
        sample_type_terms=sample_type_terms,
        data_type_terms=data_type_terms,
    )


def build_source_previews_from_chinese(query: str) -> dict[str, object]:
    """Build source-specific preview mappings from Chinese concept matches."""
    query_mapping = build_query_mapping_from_chinese(query)
    tcga_filters: dict[str, list[str]] = {}
    gtex_filters: dict[str, list[str]] = {}
    geo_query_terms: list[str] = []
    tcga_linked_term_ids: list[str] = []
    gtex_linked_term_ids: list[str] = []

    for concept_id in query_mapping.concept_ids:
        tcga_result = map_concept_to_tcga_filters(concept_id)
        for field, values in tcga_result["filters"].items():
            tcga_filters.setdefault(field, [])
            for value in values:
                if value not in tcga_filters[field]:
                    tcga_filters[field].append(value)
        for term_id in tcga_result["linked_term_ids"]:
            if term_id not in tcga_linked_term_ids:
                tcga_linked_term_ids.append(term_id)

        gtex_result = map_concept_to_gtex_filters(concept_id)
        for field, values in gtex_result["filters"].items():
            gtex_filters.setdefault(field, [])
            for value in values:
                if value not in gtex_filters[field]:
                    gtex_filters[field].append(value)
        for term_id in gtex_result["linked_term_ids"]:
            if term_id not in gtex_linked_term_ids:
                gtex_linked_term_ids.append(term_id)

        geo_result = map_concept_to_geo_query_terms(concept_id)
        for value in geo_result["query_terms"]:
            if value not in geo_query_terms:
                geo_query_terms.append(value)

    return {
        "query_mapping": query_mapping.to_dict(),
        "tcga_gdc": {
            "filters": tcga_filters,
            "linked_term_ids": tcga_linked_term_ids,
        },
        "gtex": {
            "filters": gtex_filters,
            "linked_term_ids": gtex_linked_term_ids,
        },
        "geo": {
            "query_terms": geo_query_terms,
            "status": "reserved_for_future_geo_adapter",
        },
    }
