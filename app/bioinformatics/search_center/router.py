from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.shared.query_intelligence import LocalModelConfig

from .geo_adapter import GeoSearchAdapter
from .gtex_adapter import GtexSearchAdapter
from .models import BioinformaticsSearchCenterResult, SourceSearchResult, StructuredBioinformaticsQuery
from .normalizer import DatasetCandidateNormalizer
from .query_understanding import QueryUnderstandingLayer
from .ranker import DatasetCandidateRanker
from .tcga_gdc_adapter import TcgaGdcSearchAdapter


class BioinformaticsSourceRouter:
    def __init__(
        self,
        *,
        query_understanding: QueryUnderstandingLayer | None = None,
        geo_adapter: GeoSearchAdapter | None = None,
        tcga_adapter: TcgaGdcSearchAdapter | None = None,
        gtex_adapter: GtexSearchAdapter | None = None,
        normalizer: DatasetCandidateNormalizer | None = None,
        ranker: DatasetCandidateRanker | None = None,
    ) -> None:
        self.query_understanding = query_understanding or QueryUnderstandingLayer()
        self.geo_adapter = geo_adapter or GeoSearchAdapter()
        self.tcga_adapter = tcga_adapter or TcgaGdcSearchAdapter()
        self.gtex_adapter = gtex_adapter or GtexSearchAdapter()
        self.normalizer = normalizer or DatasetCandidateNormalizer()
        self.ranker = ranker or DatasetCandidateRanker()

    def search(
        self,
        query: str | StructuredBioinformaticsQuery,
        *,
        online_enabled: bool = False,
        limit: int = 20,
        start: int = 0,
        timeout: int = 8,
        use_local_model: bool = False,
        local_model_config: LocalModelConfig | None = None,
        gateway_module: str = "bioinformatics",
        gateway_task_type: str = "bio_generate_dataset_query_draft",
        geo_fetcher_cls: type[Any] | None | object = ...,
        confirmed_geo_queries: tuple[str, ...] | list[str] | None = None,
        allow_broad_geo_query: bool = False,
    ) -> BioinformaticsSearchCenterResult:
        structured = (
            query
            if isinstance(query, StructuredBioinformaticsQuery)
            else self.query_understanding.understand(
                str(query),
                use_local_model=use_local_model,
                local_model_config=local_model_config,
                gateway_module=gateway_module,
                gateway_task_type=gateway_task_type,
            )
        )
        source_results: dict[str, SourceSearchResult] = {}
        broad_blocked = structured.search_execution_status == "disease_terms_missing" and not allow_broad_geo_query
        source_online_enabled = online_enabled and not broad_blocked
        if "geo" in structured.allowed_sources:
            source_results["geo"] = self.geo_adapter.search(
                structured,
                online_enabled=source_online_enabled,
                limit=limit,
                start=start,
                timeout=timeout,
                fetcher_cls=geo_fetcher_cls,
                confirmed_queries=confirmed_geo_queries,
                allow_broad_geo_query=allow_broad_geo_query,
            )
        if "tcga_gdc" in structured.allowed_sources:
            source_results["tcga_gdc"] = self.tcga_adapter.search(
                structured,
                online_enabled=source_online_enabled,
                limit=limit,
                start=start,
                timeout=timeout,
            )
        if "gtex" in structured.allowed_sources:
            source_results["gtex"] = self.gtex_adapter.search(
                structured,
                online_enabled=source_online_enabled,
                limit=limit,
                start=start,
                timeout=timeout,
            )
        candidates = self.normalizer.normalize([candidate for result in source_results.values() for candidate in result.candidates])
        ranked = self.ranker.rank(candidates)
        warnings = tuple(dict.fromkeys([*structured.warnings, *[warning for result in source_results.values() for warning in result.warnings]]))
        return BioinformaticsSearchCenterResult(
            query=structured,
            source_results=source_results,
            candidates=ranked,
            online_enabled=source_online_enabled,
            search_time=datetime.now(timezone.utc).isoformat(),
            warnings=warnings,
        )
