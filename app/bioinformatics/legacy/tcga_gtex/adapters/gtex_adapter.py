"""Concept-driven local GTEx search adapter."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from tcga_gtex.config_rules import get_default_rule_service
from tcga_gtex.models import FileRecord, QueryMapping, StudyRecord
from tcga_gtex.search import map_concept_to_gtex_filters

from ._search_support import (
    build_explanation,
    dedupe_preserve_order,
    ensure_query_mapping,
    serialize_file_records,
    serialize_study_records,
)


_RULE_SERVICE = get_default_rule_service()
_RESOURCE_RULES = _RULE_SERVICE.load_tcga_gtex_resource_rules()

DEFAULT_GTEX_RESOURCES = _RESOURCE_RULES["default_gtex_resources"]
GTEX_FILE_TEMPLATES = {
    key: tuple(value)
    for key, value in _RESOURCE_RULES["gtex_file_templates"].items()
}


def _slugify(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in value.upper()).strip("-")


def _build_tissue_record(
    tissue: str,
    resources: list[str],
    access_level: str,
    merged_filters: dict[str, list[str]],
    query_mapping: QueryMapping,
) -> StudyRecord:
    return StudyRecord(
        source="gtex",
        study_id=f"GTEX-{_slugify(tissue)}",
        title_en=f"GTEx {tissue}",
        tissue=tissue,
        access_level=access_level,
        available_data_types=resources or DEFAULT_GTEX_RESOURCES,
        metadata={
            "selected_filters": dict(merged_filters),
            "matched_concepts": query_mapping.concept_ids,
            "matched_terms_zh": query_mapping.matched_terms_zh,
        },
    )


def _build_resource_record(
    resource: str,
    access_level: str,
    merged_filters: dict[str, list[str]],
    query_mapping: QueryMapping,
) -> StudyRecord:
    return StudyRecord(
        source="gtex",
        study_id=f"GTEX-{_slugify(resource)}",
        title_en=f"GTEx {resource}",
        access_level=access_level,
        available_data_types=[resource],
        metadata={
            "selected_filters": dict(merged_filters),
            "matched_concepts": query_mapping.concept_ids,
            "matched_terms_zh": query_mapping.matched_terms_zh,
        },
    )


def search(query: str | QueryMapping, context: dict[str, Any] | None = None) -> dict[str, Any]:
    query_mapping = ensure_query_mapping(query)
    context = context or {}

    selected_source_mappings: list[dict[str, str]] = []
    merged_filters: dict[str, list[str]] = defaultdict(list)
    for concept_id in query_mapping.concept_ids:
        result = map_concept_to_gtex_filters(concept_id, context=context)
        for row in result["mapping_rows"]:
            if row not in selected_source_mappings:
                selected_source_mappings.append(row)
        for field, values in result["filters"].items():
            merged_filters[field] = dedupe_preserve_order(merged_filters[field] + values)

    requested_tissues = merged_filters.get("tissue", [])
    requested_resources = dedupe_preserve_order(
        merged_filters.get("resource_name", []) + merged_filters.get("expression_unit", [])
    )
    access_values = merged_filters.get("access", [])
    access_level = access_values[0] if access_values else "open access"

    records: list[StudyRecord] = []
    if requested_tissues:
        for tissue in requested_tissues:
            records.append(
                _build_tissue_record(
                    tissue=tissue,
                    resources=requested_resources,
                    access_level=access_level,
                    merged_filters=dict(merged_filters),
                    query_mapping=query_mapping,
                )
            )
    elif requested_resources:
        for resource in requested_resources:
            records.append(
                _build_resource_record(
                    resource=resource,
                    access_level=access_level,
                    merged_filters=dict(merged_filters),
                    query_mapping=query_mapping,
                )
            )

    warnings: list[str] = []
    if not records:
        warnings.append("No GTEx tissues or resources matched the current concept-to-filter selection.")

    return {
        "source": "gtex",
        "query_mapping": query_mapping.to_dict(),
        "results": serialize_study_records(records),
        "explanation": build_explanation(
            source="gtex",
            query_mapping=query_mapping,
            selected_source_mappings=selected_source_mappings,
            warnings=warnings,
        ),
    }


def _ensure_study_records(query: str | QueryMapping | StudyRecord | list[StudyRecord]) -> list[StudyRecord]:
    if isinstance(query, StudyRecord):
        return [query]
    if isinstance(query, list):
        return query
    result = search(query)
    return [StudyRecord(**record) for record in result["results"]]


def resolve_files(
    query: str | QueryMapping | StudyRecord | list[StudyRecord],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    study_records = _ensure_study_records(query)
    file_records: list[FileRecord] = []

    for study in study_records:
        resources = study.available_data_types or DEFAULT_GTEX_RESOURCES
        for resource in resources:
            guessed_role, file_name, file_type = GTEX_FILE_TEMPLATES.get(
                resource,
                ("data", f"{resource.lower().replace(' ', '_')}.dat", "dat"),
            )
            prefix = study.study_id.lower().replace("gtex-", "gtex_")
            file_records.append(
                FileRecord(
                    source="gtex",
                    study_id=study.study_id,
                    file_id=f"{study.study_id}:{guessed_role}",
                    file_name=f"{prefix}_{file_name}",
                    file_type=file_type,
                    guessed_role=guessed_role,
                    access_level=study.access_level,
                    metadata={
                        "resource_name": resource,
                        "selected_filters": study.metadata.get("selected_filters", {}),
                        "resolver": "concept_driven_gtex_file_resolution",
                    },
                )
            )

    warnings: list[str] = []
    if not file_records:
        warnings.append("No GTEx files could be resolved from the selected study records.")

    matched_terms_zh = dedupe_preserve_order(
        [term for study in study_records for term in study.metadata.get("matched_terms_zh", [])]
    )
    matched_concepts = dedupe_preserve_order(
        [concept for study in study_records for concept in study.metadata.get("matched_concepts", [])]
    )

    return {
        "source": "gtex",
        "results": serialize_file_records(file_records),
        "explanation": {
            "source": "gtex",
            "matched_terms_zh": matched_terms_zh,
            "matched_concepts": matched_concepts,
            "selected_studies": [study.study_id for study in study_records],
            "resolved_file_roles": dedupe_preserve_order([record.guessed_role for record in file_records]),
            "ambiguity_notes": [],
            "warnings": warnings,
        },
    }
