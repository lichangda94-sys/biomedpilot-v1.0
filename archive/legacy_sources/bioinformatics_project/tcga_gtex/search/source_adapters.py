"""Shared concept-to-source adaptation helpers for TCGA/GDC, GTEx, and GEO."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from tcga_gtex.lexicon import CONCEPT_SOURCE_MAPPINGS_CSV


def _load_source_mappings() -> list[dict[str, str]]:
    with Path(CONCEPT_SOURCE_MAPPINGS_CSV).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _map_concept(concept_id: str, source: str) -> list[dict[str, str]]:
    return [
        row
        for row in _load_source_mappings()
        if row["concept_id"] == concept_id and row["source"] == source and row["is_active"] == "true"
    ]


def map_concept_to_tcga_filters(concept_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Map one shared concept to TCGA/GDC structured field filters."""
    rows = _map_concept(concept_id, "tcga_gdc")
    filters: dict[str, list[str]] = {}
    linked_terms: list[str] = []
    for row in rows:
        if row["target_field"] and row["target_value"]:
            filters.setdefault(row["target_field"], []).append(row["target_value"])
        if row["target_term_id"]:
            linked_terms.append(row["target_term_id"])
    return {
        "source": "tcga_gdc",
        "concept_id": concept_id,
        "context": context or {},
        "filters": filters,
        "linked_term_ids": linked_terms,
        "mapping_rows": rows,
    }


def map_concept_to_gtex_filters(concept_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Map one shared concept to GTEx tissue/resource-style filters."""
    rows = _map_concept(concept_id, "gtex")
    filters: dict[str, list[str]] = {}
    linked_terms: list[str] = []
    for row in rows:
        if row["target_field"] and row["target_value"]:
            filters.setdefault(row["target_field"], []).append(row["target_value"])
        if row["target_term_id"]:
            linked_terms.append(row["target_term_id"])
    return {
        "source": "gtex",
        "concept_id": concept_id,
        "context": context or {},
        "filters": filters,
        "linked_term_ids": linked_terms,
        "mapping_rows": rows,
    }


def map_concept_to_geo_query_terms(concept_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Reserve a GEO query-expansion entry point without implementing GEO search logic yet."""
    rows = _map_concept(concept_id, "geo")
    query_terms = [row["target_value"] for row in rows if row["target_value"]]
    return {
        "source": "geo",
        "concept_id": concept_id,
        "context": context or {},
        "query_terms": query_terms,
        "ranking_hints": [],
        "mapping_rows": rows,
        "status": "reserved_for_future_geo_adapter",
    }
