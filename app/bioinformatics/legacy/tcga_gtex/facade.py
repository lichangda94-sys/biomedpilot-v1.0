"""Public facade for the pluggable TCGA/GTEx data module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .adapters.gtex_adapter import resolve_files as resolve_gtex_files
from .adapters.gtex_adapter import search as search_gtex
from .adapters.tcga_adapter import resolve_files as resolve_tcga_files
from .adapters.tcga_adapter import search as search_tcga
from .download.task_runner import download_dataset_files
from .models import ApiResponse
from .models import QueryMapping
from .processing.bundle_builder import build_local_analysis_bundle, read_local_bundle_summary
from .search import build_query_mapping_from_chinese, map_concept_to_geo_query_terms


def _build_response(
    *,
    status: str,
    message: str,
    output_dir: str | None = None,
    bundle_path: str | None = None,
    warnings: list[str] | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return ApiResponse(
        status=status,
        message=message,
        output_dir=output_dir,
        bundle_path=bundle_path,
        warnings=warnings or [],
        data=data or {},
    ).to_dict()


def _dedupe_mapping_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[tuple[str, Any], ...]] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        key = tuple(sorted(row.items()))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _merge_explanations(
    query_mapping: QueryMapping,
    tcga_result: dict[str, Any],
    gtex_result: dict[str, Any],
) -> dict[str, Any]:
    geo_rows: list[dict[str, Any]] = []
    geo_query_terms: list[str] = []
    for concept_id in query_mapping.concept_ids:
        geo_result = map_concept_to_geo_query_terms(concept_id)
        for row in geo_result["mapping_rows"]:
            if row not in geo_rows:
                geo_rows.append(row)
        for term in geo_result["query_terms"]:
            if term not in geo_query_terms:
                geo_query_terms.append(term)

    ambiguity_notes = tcga_result["explanation"]["ambiguity_notes"] + gtex_result["explanation"]["ambiguity_notes"]
    warnings = tcga_result["explanation"]["warnings"] + gtex_result["explanation"]["warnings"]
    return {
        "matched_terms_zh": query_mapping.matched_terms_zh,
        "matched_concepts": query_mapping.concept_ids,
        "selected_source_mappings": _dedupe_mapping_rows(
            tcga_result["explanation"]["selected_source_mappings"]
            + gtex_result["explanation"]["selected_source_mappings"]
        ),
        "ambiguity_notes": list(dict.fromkeys(ambiguity_notes)),
        "warnings": list(dict.fromkeys(warnings)),
        "source_explanations": {
            "tcga_gdc": tcga_result["explanation"],
            "gtex": gtex_result["explanation"],
            "geo": {
                "source": "geo",
                "matched_terms_zh": query_mapping.matched_terms_zh,
                "matched_concepts": query_mapping.concept_ids,
                "selected_source_mappings": geo_rows,
                "ambiguity_notes": [],
                "warnings": ["GEO search execution is still reserved for a future adapter."],
                "query_terms": geo_query_terms,
                "status": "reserved_for_future_geo_adapter",
            },
        },
    }


def search_tcga_gtex(query: str | QueryMapping, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    """Search TCGA/GTEx studies via the unified facade."""
    query_mapping = query if isinstance(query, QueryMapping) else build_query_mapping_from_chinese(query)
    tcga_result = search_tcga(query_mapping, context=filters)
    gtex_result = search_gtex(query_mapping, context=filters)

    combined_results = tcga_result["results"] + gtex_result["results"]
    explanation = _merge_explanations(query_mapping, tcga_result, gtex_result)
    status = "success" if combined_results else "failed"
    message = (
        f"Resolved {len(combined_results)} study records across TCGA/GDC and GTEx."
        if combined_results
        else "No TCGA/GTex study records matched the current concept-to-filter selection."
    )
    return _build_response(
        status=status,
        message=message,
        warnings=explanation["warnings"],
        data={
            "query": query_mapping.raw_query,
            "filters": filters or {},
            "results": combined_results,
            "results_by_source": {
                "tcga_gdc": tcga_result["results"],
                "gtex": gtex_result["results"],
            },
            "query_mapping": query_mapping.to_dict(),
            "explanation": explanation,
        },
    )


def resolve_tcga_gtex_files(query: str | QueryMapping, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve unified file-level candidates from a Chinese query or QueryMapping."""
    query_mapping = query if isinstance(query, QueryMapping) else build_query_mapping_from_chinese(query)
    tcga_result = resolve_tcga_files(query_mapping, context=filters)
    gtex_result = resolve_gtex_files(query_mapping, context=filters)

    combined_results = tcga_result["results"] + gtex_result["results"]
    warnings = list(dict.fromkeys(tcga_result["explanation"]["warnings"] + gtex_result["explanation"]["warnings"]))
    return _build_response(
        status="success" if combined_results else "failed",
        message=(
            f"Resolved {len(combined_results)} file-level candidates across TCGA/GDC and GTEx."
            if combined_results
            else "No TCGA/GTex file-level candidates matched the current concept-to-filter selection."
        ),
        warnings=warnings,
        data={
            "query": query_mapping.raw_query,
            "filters": filters or {},
            "results": combined_results,
            "results_by_source": {
                "tcga_gdc": tcga_result["results"],
                "gtex": gtex_result["results"],
            },
            "query_mapping": query_mapping.to_dict(),
            "explanation": {
                "matched_terms_zh": query_mapping.matched_terms_zh,
                "matched_concepts": query_mapping.concept_ids,
                "selected_studies": list(
                    dict.fromkeys(
                        tcga_result["explanation"]["selected_studies"] + gtex_result["explanation"]["selected_studies"]
                    )
                ),
                "resolved_file_roles": list(
                    dict.fromkeys(
                        tcga_result["explanation"]["resolved_file_roles"]
                        + gtex_result["explanation"]["resolved_file_roles"]
                    )
                ),
                "ambiguity_notes": [],
                "warnings": warnings,
                "source_explanations": {
                    "tcga_gdc": tcga_result["explanation"],
                    "gtex": gtex_result["explanation"],
                },
            },
        },
    )


def download_tcga_gtex_dataset(
    study_id: str,
    out_dir: str,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Download one TCGA/GTEx dataset via the unified facade."""
    result = download_dataset_files(study_id, out_dir, options=options)
    return _build_response(
        status=result["status"],
        message=result["message"],
        output_dir=result["output_dir"],
        warnings=result.get("warnings", []),
        data=result.get("data", {}),
    )


def build_tcga_gtex_bundle(local_dir: str) -> dict[str, Any]:
    """Build an analysis-ready bundle from a local TCGA/GTEx dataset directory."""
    result = build_local_analysis_bundle(local_dir)
    return _build_response(
        status=result["status"],
        message=result["message"],
        output_dir=result["output_dir"],
        bundle_path=result["bundle_path"],
        warnings=result.get("warnings", []),
        data=result.get("data", {}),
    )


def get_tcga_gtex_summary(bundle_dir: str) -> dict[str, Any]:
    """Summarize a built TCGA/GTEx analysis bundle."""
    result = read_local_bundle_summary(bundle_dir)
    return _build_response(
        status=result["status"],
        message=result["message"],
        output_dir=result["output_dir"],
        bundle_path=result["bundle_path"],
        warnings=result.get("warnings", []),
        data=result.get("data", {}),
    )
