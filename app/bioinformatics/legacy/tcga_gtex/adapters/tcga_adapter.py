"""Concept-driven local TCGA/GDC search adapter."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from tcga_gtex.config_rules import get_default_rule_service
from tcga_gtex.models import FileRecord, QueryMapping, StudyRecord
from tcga_gtex.search import map_concept_to_tcga_filters

from ._search_support import (
    build_explanation,
    dedupe_preserve_order,
    ensure_query_mapping,
    load_full_terms,
    serialize_file_records,
    serialize_study_records,
)


_RULE_SERVICE = get_default_rule_service()
_RESOURCE_RULES = _RULE_SERVICE.load_tcga_gtex_resource_rules()

DEFAULT_TCGA_DATA_TYPES = _RESOURCE_RULES["default_tcga_data_types"]
TCGA_FILE_TEMPLATES = {
    key: tuple(value)
    for key, value in _RESOURCE_RULES["tcga_file_templates"].items()
}


def _build_project_catalog() -> dict[str, dict[str, Any]]:
    full_terms = load_full_terms()
    project_term_ids: dict[str, str] = {}
    project_titles: dict[str, str] = {}
    for row in full_terms:
        if row["field_name"] == "project.project_id" and row["term_type"] == "value":
            project_term_ids[row["field_value"]] = row["term_id"]
    for row in full_terms:
        if row["field_name"] == "project.name" and row["term_type"] == "value":
            project_code = next(
                (code for code, term_id in project_term_ids.items() if term_id == row["parent_term"]),
                "",
            )
            if project_code:
                project_titles[project_code] = row["field_value"]

    project_catalog = {
        code: {
            "study_id": code,
            "title_en": project_titles.get(code, code),
            "disease": project_titles.get(code, code),
            "access_level": "open",
        }
        for code in sorted(project_term_ids)
    }
    return project_catalog


def search(query: str | QueryMapping, context: dict[str, Any] | None = None) -> dict[str, Any]:
    query_mapping = ensure_query_mapping(query)
    context = context or {}

    selected_source_mappings: list[dict[str, str]] = []
    merged_filters: dict[str, list[str]] = defaultdict(list)
    for concept_id in query_mapping.concept_ids:
        result = map_concept_to_tcga_filters(concept_id, context=context)
        for row in result["mapping_rows"]:
            if row not in selected_source_mappings:
                selected_source_mappings.append(row)
        for field, values in result["filters"].items():
            merged_filters[field] = dedupe_preserve_order(merged_filters[field] + values)

    project_catalog = _build_project_catalog()
    requested_projects = merged_filters.get("project.project_id", [])
    requested_primary_sites = merged_filters.get("cases.primary_site", [])
    candidate_project_ids: list[str]
    if requested_projects:
        candidate_project_ids = requested_projects
    elif requested_primary_sites or merged_filters.get("project.disease_type", []):
        candidate_project_ids = []
    elif query_mapping.concept_ids:
        candidate_project_ids = list(project_catalog)
    else:
        candidate_project_ids = []

    requested_data_types = dedupe_preserve_order(
        merged_filters.get("files.data_type", [])
        + [
            "Gene Expression Quantification"
            for concept_id in query_mapping.concept_ids
            if concept_id == "analysis_resource.gene_expression"
        ]
    )
    requested_access = merged_filters.get("access", []) + merged_filters.get("files.access", [])
    access_level = requested_access[0] if requested_access else "open"

    records: list[StudyRecord] = []
    for project_id in candidate_project_ids:
        project = project_catalog.get(project_id)
        if project is None:
            continue
        available_data_types = requested_data_types or DEFAULT_TCGA_DATA_TYPES
        records.append(
            StudyRecord(
                source="tcga_gdc",
                study_id=project_id,
                title_en=project["title_en"],
                disease=project["disease"],
                tissue=", ".join(dedupe_preserve_order(merged_filters.get("cases.primary_site", []))),
                access_level=access_level,
                available_data_types=available_data_types,
                metadata={
                    "selected_filters": dict(merged_filters),
                    "matched_concepts": query_mapping.concept_ids,
                    "matched_terms_zh": query_mapping.matched_terms_zh,
                },
            )
        )

    warnings: list[str] = []
    if not requested_projects and (requested_primary_sites or merged_filters.get("project.disease_type", [])):
        warnings.append(
            "The current TCGA/GDC search only materializes study-level records when concept mappings resolve to project IDs."
        )
    if not records:
        warnings.append("No TCGA/GDC projects matched the current concept-to-filter selection.")

    return {
        "source": "tcga_gdc",
        "query_mapping": query_mapping.to_dict(),
        "results": serialize_study_records(records),
        "explanation": build_explanation(
            source="tcga_gdc",
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
        data_types = study.available_data_types or DEFAULT_TCGA_DATA_TYPES
        for data_type in data_types:
            guessed_role, file_name, file_type = TCGA_FILE_TEMPLATES.get(
                data_type,
                ("data", f"{data_type.lower().replace(' ', '_')}.dat", "dat"),
            )
            file_records.append(
                FileRecord(
                    source="tcga_gdc",
                    study_id=study.study_id,
                    file_id=f"{study.study_id}:{guessed_role}",
                    file_name=f"{study.study_id.lower()}_{file_name}",
                    file_type=file_type,
                    guessed_role=guessed_role,
                    access_level=study.access_level,
                    metadata={
                        "data_type": data_type,
                        "selected_filters": study.metadata.get("selected_filters", {}),
                        "resolver": "concept_driven_tcga_file_resolution",
                    },
                )
            )

    warnings: list[str] = []
    if not file_records:
        warnings.append("No TCGA/GDC files could be resolved from the selected study records.")

    matched_terms_zh = dedupe_preserve_order(
        [term for study in study_records for term in study.metadata.get("matched_terms_zh", [])]
    )
    matched_concepts = dedupe_preserve_order(
        [concept for study in study_records for concept in study.metadata.get("matched_concepts", [])]
    )

    return {
        "source": "tcga_gdc",
        "results": serialize_file_records(file_records),
        "explanation": {
            "source": "tcga_gdc",
            "matched_terms_zh": matched_terms_zh,
            "matched_concepts": matched_concepts,
            "selected_studies": [study.study_id for study in study_records],
            "resolved_file_roles": dedupe_preserve_order([record.guessed_role for record in file_records]),
            "ambiguity_notes": [],
            "warnings": warnings,
        },
    }
