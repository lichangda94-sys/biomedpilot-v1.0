from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.bioinformatics.retrieval.geo_search_service import GeoDatasetSearchItem, search_geo_datasets_for_queries

from .models import SourceSearchResult, StructuredBioinformaticsQuery, UnifiedDatasetCandidate


class GeoSearchAdapter:
    source = "geo"
    database_source = "NCBI GEO"

    def search(
        self,
        query: StructuredBioinformaticsQuery,
        *,
        online_enabled: bool,
        limit: int = 20,
        start: int = 0,
        timeout: int = 8,
        fetcher_cls: type[Any] | None | object = ...,
        confirmed_queries: tuple[str, ...] | list[str] | None = None,
        allow_broad_geo_query: bool = False,
    ) -> SourceSearchResult:
        queries = tuple(_clean_query_label(value) for value in (confirmed_queries or query.geo_query_candidates) if _clean_query_label(value))
        search_time = _now()
        if query.search_execution_status == "disease_terms_missing" and not allow_broad_geo_query:
            return SourceSearchResult(
                source=self.source,
                search_status="disease_terms_missing",
                executed_query=" | ".join(queries),
                total_found=None,
                returned_count=0,
                displayed_count=0,
                candidates=(),
                warnings=("未识别出明确疾病词，当前 query 为宽泛表达谱检索，结果可能过宽。", "宽泛 GEO 检索需要用户二次确认。"),
                database_source=self.database_source,
                search_time=search_time,
                start=start,
                query_payload={"geo_query_candidates": list(queries), "broad_query_guard": True},
            )
        if not online_enabled:
            return SourceSearchResult(
                source=self.source,
                search_status="draft_only",
                executed_query=" | ".join(queries),
                total_found=None,
                returned_count=0,
                displayed_count=0,
                candidates=(),
                warnings=("仅生成检索词，未执行在线检索。",),
                database_source=self.database_source,
                search_time=search_time,
                start=start,
                query_payload={"geo_query_candidates": list(queries)},
            )
        response = search_geo_datasets_for_queries(
            list(queries),
            max_results_per_query=limit,
            timeout=timeout,
            start=start,
            fetcher_cls=fetcher_cls,
        )
        candidates = tuple(_candidate_from_geo_item(item, query) for item in response.results)
        return SourceSearchResult(
            source=self.source,
            search_status=response.search_status,
            executed_query=response.executed_query,
            total_found=response.total_found,
            returned_count=len(response.results),
            displayed_count=len(candidates),
            candidates=candidates,
            warnings=response.warnings,
            error_message=response.error_message,
            database_source=self.database_source,
            search_time=search_time,
            start=response.start,
            next_start=response.next_start,
            fetched_all=response.fetched_all,
            query_payload={"geo_query_candidates": list(queries)},
        )


def _candidate_from_geo_item(item: GeoDatasetSearchItem, query: StructuredBioinformaticsQuery) -> UnifiedDatasetCandidate:
    metadata = {
        "gse_accession": item.accession,
        "geo_url": item.geo_url,
        "title_en": item.title,
        "summary_en": item.summary,
        "overall_design_en": "",
        "platform_accessions": list(item.platform_accessions),
        "platform_titles": list(item.platform_titles),
        "publication_date": item.publication_date,
        "update_date": item.update_date,
        "query_used": item.query_used,
        "has_series_matrix": getattr(item, "has_series_matrix", bool(item.accession)),
        "has_supplementary_files": getattr(item, "has_supplementary_files", False),
        "has_group_hint": getattr(item, "has_group_hint", _has_group_hint(item)),
    }
    warnings = tuple(getattr(item, "warnings", ()) or _geo_warnings(metadata))
    recommended = tuple(getattr(item, "recommended_analyses", ()) or _recommended_geo_analyses(item, metadata))
    return UnifiedDatasetCandidate(
        source="geo",
        accession_or_project=item.accession,
        display_title=item.title,
        organism=item.organism or "Homo sapiens",
        disease=", ".join(query.disease_terms_en),
        tissue=", ".join(query.tissue_terms),
        data_modality=item.data_type,
        sample_count=item.sample_count,
        has_expression_matrix=bool(metadata["has_series_matrix"] or metadata["has_supplementary_files"]),
        has_sample_metadata=bool(item.sample_count),
        has_clinical_metadata=False,
        has_platform_annotation=bool(item.platform_accessions),
        recommended_analyses=recommended,
        download_plan_available=bool(item.accession),
        score=int(item.relevance_score or 0),
        warnings=warnings,
        source_specific_metadata=metadata,
    )


def _has_group_hint(item: GeoDatasetSearchItem) -> bool:
    text = " ".join([item.title, item.summary, " ".join(item.tissue_disease_keywords)]).lower()
    return any(token in text for token in ("normal", "tumor", "control", "case", "metastasis"))


def _recommended_geo_analyses(item: GeoDatasetSearchItem, metadata: dict[str, object]) -> tuple[str, ...]:
    analyses = ["data_recognition"]
    if "expression" in item.data_type.lower() or "rna" in item.data_type.lower() or "microarray" in item.data_type.lower():
        analyses.append("differential_expression")
    if metadata.get("has_group_hint"):
        analyses.append("group_comparison")
    return tuple(dict.fromkeys(analyses))


def _geo_warnings(metadata: dict[str, object]) -> tuple[str, ...]:
    warnings: list[str] = []
    if not metadata.get("has_series_matrix"):
        warnings.append("需确认 Series Matrix 或补充文件是否可下载。")
    if not metadata.get("has_group_hint"):
        warnings.append("未从 metadata 中识别到明确分组线索，需人工确认样本分组。")
    return tuple(warnings)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_query_label(value: str) -> str:
    text = str(value).strip()
    if "｜" in text and text.startswith("宽泛补充检索"):
        return text.split("｜", 1)[1].strip()
    return text
