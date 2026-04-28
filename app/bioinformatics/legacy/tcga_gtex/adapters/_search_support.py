"""Shared search-support helpers for local concept-driven TCGA/GTex adapters."""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

from tcga_gtex.lexicon import CONCEPT_SOURCE_MAPPINGS_CSV, ENGLISH_CORE_TERMS_FULL_CSV
from tcga_gtex.models import FileRecord, QueryMapping, StudyRecord
from tcga_gtex.search import build_query_mapping_from_chinese


@lru_cache(maxsize=1)
def load_full_terms() -> list[dict[str, str]]:
    with Path(ENGLISH_CORE_TERMS_FULL_CSV).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@lru_cache(maxsize=1)
def load_concept_source_mappings() -> list[dict[str, str]]:
    with Path(CONCEPT_SOURCE_MAPPINGS_CSV).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def ensure_query_mapping(query: str | QueryMapping) -> QueryMapping:
    if isinstance(query, QueryMapping):
        return query
    return build_query_mapping_from_chinese(query)


def build_explanation(
    *,
    source: str,
    query_mapping: QueryMapping,
    selected_source_mappings: list[dict[str, str]],
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    ambiguity_notes: list[str] = []
    if len(query_mapping.disease_terms) > 1:
        ambiguity_notes.append("Multiple disease concepts matched; returning the union of compatible source mappings.")
    if len(query_mapping.tissue_terms) > 1:
        ambiguity_notes.append("Multiple tissue concepts matched; returning the union of compatible tissue mappings.")
    if not query_mapping.concept_ids:
        ambiguity_notes.append("No concept matched the input query.")

    return {
        "source": source,
        "matched_terms_zh": query_mapping.matched_terms_zh,
        "matched_concepts": query_mapping.concept_ids,
        "selected_source_mappings": selected_source_mappings,
        "ambiguity_notes": ambiguity_notes,
        "warnings": warnings or [],
    }


def serialize_study_records(records: list[StudyRecord]) -> list[dict[str, Any]]:
    return [record.to_dict() for record in records]


def serialize_file_records(records: list[FileRecord]) -> list[dict[str, Any]]:
    return [record.to_dict() for record in records]


def dedupe_preserve_order(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output
